#!/usr/bin/env python3

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import generate_clean_dataset
from src.scraper import extract_elements
from src.ranking_engine import rank_selectors_for_elements
from src.utils import generate_timestamped_filename, save_json, validate_url, extract_domain
from ml.evaluate import SelectorStabilityInference
from LLM.zeiss_gateway_client import ZeissLLMGatewayClient
import pandas as pd

DEFAULT_LLM_BASE_URL = "https://api.genai.zeiss.com/llm"
DEFAULT_LLM_MODEL = "gpt-4o"
DEFAULT_LLM_API_KEY = "827180ec60ba42d5a82503b538298779"
DEFAULT_PROMPT_FILE = "LLM/prompts/generate_helper_js_prompt.txt"

# Processes multiple URLs in parallel for dataset generation
def run_batch(urls, mode="all", headless=True, max_workers=None, raw=False):
    if max_workers is None:
        max_workers = min(len(urls), 4)

    print(f"Starting batch processing with {max_workers} parallel workers...")
    print(f"Headless mode: {'ON' if headless else 'OFF'}")
    print(f"Processing {len(urls)} URLs: {', '.join(urls[:3])}{'...' if len(urls) > 3 else ''}")
    print()

    results = []

    # Handles processing of a single URL in batch mode
    def process_url(url):
        try:
            print(f"[{urls.index(url)+1}/{len(urls)}] Processing: {url}")
            dataset_file = generate_clean_dataset(url, mode, headless=headless, raw=raw)
            print(f"[{urls.index(url)+1}/{len(urls)}] ✓ Completed: {url} -> {dataset_file}")
            return (url, dataset_file, "SUCCESS")
        except Exception as e:
            print(f"[{urls.index(url)+1}/{len(urls)}] ✗ Failed: {url} -> {e}")
            return (url, None, str(e))

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_url = {executor.submit(process_url, url): url for url in urls}

        for future in as_completed(future_to_url):
            result = future.result()
            results.append(result)

    print(f"\n{'='*60}")
    print("BATCH PROCESSING SUMMARY")
    print('='*60)
    for url, file, status in results:
        print(f"{url}: {status}")
        if file:
            print(f"  → {file}")

# Finds the most recent trained selector stability model
def _find_latest_model_path(model_dir="ml/models"):
    model_files = sorted(
        Path(model_dir).glob("selector_stability_model_*.joblib"),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not model_files:
        raise FileNotFoundError(
            "No trained model found in ml/models. Train or copy a model first."
        )
    return str(model_files[0])

# Adds missing model features for raw selector datasets
def _add_missing_features(X, rows, expected_features):
    missing_features = expected_features - set(X.columns)
    if not missing_features:
        return X

    for feature in missing_features:
        if feature == "is_probably_generated_class":
            X[feature] = [
                1 if (r["selector_type"] == "class" and (len(r["selector"]) > 10 or any(c.isdigit() for c in r["selector"]))) else 0
                for r in rows
            ]
        elif feature == "selector_token_count":
            X[feature] = [
                len([t for t in re.split(r"[.\s#\[\]]", r["selector"]) if t])
                for r in rows
            ]
        elif feature == "avg_token_length":
            values = []
            for r in rows:
                tokens = [t for t in re.split(r"[.\s#\[\]]", r["selector"]) if t]
                values.append(sum(len(t) for t in tokens) / len(tokens) if tokens else 0)
            X[feature] = values
        elif feature == "has_numeric_token":
            X[feature] = [
                1 if any(any(c.isdigit() for c in token) for token in re.split(r"[.\s#\[\]]", r["selector"]) if token) else 0
                for r in rows
            ]
        elif feature == "text_length":
            X[feature] = [len(r.get("text", "") or "") for r in rows]
        elif feature == "is_text_short":
            X[feature] = [1 if len(r.get("text", "") or "") < 20 else 0 for r in rows]
        elif feature == "is_xpath_absolute":
            X[feature] = [
                1 if (r["selector_type"] == "xpath" and str(r["selector"]).startswith("/")) else 0
                for r in rows
            ]
        else:
            X[feature] = 0

    return X

# Runs URL -> raw selectors -> ML prediction -> best selectors JSON workflow
def run_predict_workflow(url, mode="all", headless=True):
    if not validate_url(url):
        raise ValueError("URL must start with http:// or https://")

    valid_modes = ["interactive", "text", "all"]
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}")

    print(f"[TARGET] Predict workflow for: {url}")
    print(f"[MODE] Mode: {mode}")
    print(f"[BROWSER] Headless mode: {'ON' if headless else 'OFF'}")

    print("\n[1/5] Extracting webpage elements...")
    elements = extract_elements(url, mode=mode, headless=headless)
    if not elements:
        raise ValueError("No elements extracted from the URL")
    print(f"   [OK] Extracted {len(elements)} elements")

    print("\n[2/5] Ranking selectors for each element...")
    ranked_elements = rank_selectors_for_elements(url, elements)
    if not ranked_elements:
        raise ValueError("Failed to rank selectors")
    print(f"   [OK] Ranked selectors for {len(ranked_elements)} elements")

    raw_rows = []
    for element_id, element in enumerate(ranked_elements):
        for sel_data in element.get("ranked_selectors", []):
            raw_rows.append(
                {
                    "element_id": element_id,
                    "url": url,
                    "tag": element.get("tag", ""),
                    "text": element.get("text", ""),
                    "selector": sel_data.get("selector", ""),
                    "selector_type": sel_data.get("selector_type", ""),
                    "features": sel_data.get("features", {}),
                    "rule_score": sel_data.get("score", 0),
                    "rule_rank": sel_data.get("rank", 0),
                    "is_rule_best": sel_data.get("is_best", 0),
                }
            )

    if not raw_rows:
        raise ValueError("No selectors available for prediction")

    print("\n[3/5] Saving raw selector dataset...")
    raw_output_filename = generate_timestamped_filename("raw_selectors_dataset", url)
    raw_output_path = f"data/raw/{raw_output_filename}"
    save_json(raw_rows, raw_output_path)
    print(f"   [OK] Raw selector dataset saved: {raw_output_path}")

    print("\n[4/5] Running model predictions for all selectors...")
    model_path = _find_latest_model_path()
    inference = SelectorStabilityInference(model_path)

    X = pd.DataFrame([row["features"] for row in raw_rows])
    expected_features = set(inference.feature_names) if inference.feature_names else set(X.columns)
    X = _add_missing_features(X, raw_rows, expected_features)
    if inference.feature_names:
        X = X[inference.feature_names]

    predictions = inference.predict_batch(X)

    enriched_rows = []
    for i, row in enumerate(raw_rows):
        enriched = row.copy()
        enriched["prediction"] = int(predictions.iloc[i]["prediction"])
        enriched["probability"] = float(predictions.iloc[i]["probability"])
        enriched["confidence"] = float(predictions.iloc[i]["confidence"])
        enriched["is_stable"] = bool(predictions.iloc[i]["is_stable"])
        enriched_rows.append(enriched)

    # Pick the best selector per element based on model probability, then confidence, then shortest selector.
    best_by_element = {}
    for row in enriched_rows:
        element_id = row["element_id"]
        current = best_by_element.get(element_id)
        if current is None:
            best_by_element[element_id] = row
            continue

        is_better = (
            row["probability"] > current["probability"]
            or (
                row["probability"] == current["probability"]
                and row["confidence"] > current["confidence"]
            )
            or (
                row["probability"] == current["probability"]
                and row["confidence"] == current["confidence"]
                and len(row["selector"]) < len(current["selector"])
            )
        )
        if is_better:
            best_by_element[element_id] = row

    best_selectors = []
    for element_id in sorted(best_by_element.keys()):
        row = best_by_element[element_id]
        best_selectors.append(
            {
                "element_id": row["element_id"],
                "tag": row["tag"],
                "text": row["text"],
                "best_selector": row["selector"],
                "selector_type": row["selector_type"],
                "prediction": row["prediction"],
                "probability": round(row["probability"], 6),
                "confidence": round(row["confidence"], 6),
                "is_stable": row["is_stable"],
            }
        )

    print("\n[5/5] Saving final best-selector JSON output...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("data/predictions", exist_ok=True)
    best_output_path = f"data/predictions/best_selectors_predictions_{timestamp}.json"
    final_payload = {
        "url": url,
        "mode": mode,
        "generated_at": timestamp,
        "model_path": model_path,
        "raw_dataset_path": raw_output_path,
        "total_elements": len(best_selectors),
        "total_selectors_scored": len(enriched_rows),
        "best_selectors": best_selectors,
    }
    save_json(final_payload, best_output_path)
    print(f"   [OK] Best selectors JSON saved: {best_output_path}")
    print("\n[SUCCESS] Predict workflow completed.")

    return raw_output_path, best_output_path


# Extracts text content from OpenAI-compatible chat response payload
def _extract_chat_content(response_json):
    choices = response_json.get("choices", [])
    if not choices:
        return ""

    message = choices[0].get("message", {})
    content = message.get("content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                parts.append(item.get("text", ""))
            elif isinstance(item, str):
                parts.append(item)
        return "\n".join([p for p in parts if p])

    return str(content)


# If the model returns a fenced code block, unwrap it to raw JavaScript
def _unwrap_js_fence(text):
    match = re.search(r"```(?:javascript|js)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()


# Runs full workflow: URL -> selector predictions -> LLM helper generation JS file
def run_e2e_helper_workflow(
    url,
    mode="all",
    headless=True,
    llm_api_key=None,
    llm_base_url=DEFAULT_LLM_BASE_URL,
    llm_model=DEFAULT_LLM_MODEL,
    llm_temperature=0.2,
    llm_max_tokens=3000,
    prompt_file=DEFAULT_PROMPT_FILE,
    llm_version="v1",
):
    print("\n[E2E] Starting end-to-end helper generation workflow...")

    raw_output_path, best_output_path = run_predict_workflow(url, mode=mode, headless=headless)

    print("\n[E2E 1/3] Loading predictions and prompt template...")
    with open(best_output_path, "r", encoding="utf-8") as f:
        predictions_payload = json.load(f)

    if not os.path.exists(prompt_file):
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_file}. Create it or pass --prompt-file=<path>."
        )

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    predictions_json = json.dumps(predictions_payload, indent=2, ensure_ascii=False)
    final_prompt = (
        prompt_template
        .replace("{{URL}}", url)
        .replace("{{MODE}}", mode)
        .replace("{{PREDICTIONS_JSON}}", predictions_json)
    )

    print("[E2E 2/3] Calling ZEISS LLM endpoint...")
    effective_api_key = llm_api_key or os.getenv("ZEISS_SUB_KEY") or DEFAULT_LLM_API_KEY

    client = ZeissLLMGatewayClient(
        base_url=llm_base_url,
        api_key=effective_api_key,
        timeout=180,
    )

    chat_response = client.chat_completions(
        body={
            "model": llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You generate high-quality Playwright helper JavaScript files based on selector prediction JSON.",
                },
                {
                    "role": "user",
                    "content": final_prompt,
                },
            ],
            "temperature": llm_temperature,
            "max_tokens": llm_max_tokens,
        },
        version=llm_version,
    )

    helper_js = _unwrap_js_fence(_extract_chat_content(chat_response))
    if not helper_js:
        raise ValueError("LLM response did not contain helper JavaScript content")

    print("[E2E 3/3] Saving generated helper JavaScript...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = extract_domain(url)

    os.makedirs("data/helpers", exist_ok=True)
    js_output_path = f"data/helpers/generated_helpers_{domain}_{timestamp}.js"
    metadata_output_path = f"data/helpers/generated_helpers_metadata_{domain}_{timestamp}.json"

    with open(js_output_path, "w", encoding="utf-8") as f:
        f.write(helper_js)

    metadata = {
        "url": url,
        "mode": mode,
        "generated_at": timestamp,
        "llm_base_url": llm_base_url,
        "llm_model": llm_model,
        "llm_version": llm_version,
        "prompt_file": prompt_file,
        "raw_dataset_path": raw_output_path,
        "predictions_path": best_output_path,
        "helper_js_path": js_output_path,
    }
    save_json(metadata, metadata_output_path)

    print(f"   [OK] Helper JavaScript saved: {js_output_path}")
    print(f"   [OK] Generation metadata saved: {metadata_output_path}")
    print("\n[SUCCESS] End-to-end helper generation workflow completed.")

    return {
        "raw_dataset_path": raw_output_path,
        "predictions_path": best_output_path,
        "helper_js_path": js_output_path,
        "metadata_path": metadata_output_path,
    }

if __name__ == "__main__":
    # Shortcut workflow: python scripts/run.py <url> <mode> predict [--headless|--no-headless]
    if len(sys.argv) >= 4 and sys.argv[3].lower() == "predict" and sys.argv[1] not in ["single", "batch"]:
        url = sys.argv[1]
        mode = sys.argv[2]
        headless = True

        for arg in sys.argv[4:]:
            if arg == "--headless":
                headless = True
            elif arg == "--no-headless":
                headless = False
            else:
                print(f"ERROR: Unexpected argument '{arg}'")
                sys.exit(1)

        try:
            run_predict_workflow(url, mode=mode, headless=headless)
            sys.exit(0)
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    # End-to-end workflow:
    # python scripts/run.py <url> <mode> generate-js [options]
    if len(sys.argv) >= 4 and sys.argv[3].lower() == "generate-js" and sys.argv[1] not in ["single", "batch"]:
        url = sys.argv[1]
        mode = sys.argv[2]

        headless = True
        llm_api_key = None
        llm_base_url = DEFAULT_LLM_BASE_URL
        llm_model = DEFAULT_LLM_MODEL
        llm_temperature = 0.2
        llm_max_tokens = 3000
        prompt_file = DEFAULT_PROMPT_FILE
        llm_version = "v1"

        for arg in sys.argv[4:]:
            if arg == "--headless":
                headless = True
            elif arg == "--no-headless":
                headless = False
            elif arg.startswith("--llm-api-key="):
                llm_api_key = arg.split("=", 1)[1]
            elif arg.startswith("--llm-base-url="):
                llm_base_url = arg.split("=", 1)[1]
            elif arg.startswith("--llm-model="):
                llm_model = arg.split("=", 1)[1]
            elif arg.startswith("--llm-temperature="):
                try:
                    llm_temperature = float(arg.split("=", 1)[1])
                except ValueError:
                    print(f"ERROR: Invalid float value in '{arg}'")
                    sys.exit(1)
            elif arg.startswith("--llm-max-tokens="):
                try:
                    llm_max_tokens = int(arg.split("=", 1)[1])
                except ValueError:
                    print(f"ERROR: Invalid integer value in '{arg}'")
                    sys.exit(1)
            elif arg.startswith("--prompt-file="):
                prompt_file = arg.split("=", 1)[1]
            elif arg.startswith("--llm-version="):
                llm_version = arg.split("=", 1)[1]
                if llm_version not in ["plain", "v1"]:
                    print("ERROR: --llm-version must be 'plain' or 'v1'")
                    sys.exit(1)
            else:
                print(f"ERROR: Unexpected argument '{arg}'")
                sys.exit(1)

        try:
            run_e2e_helper_workflow(
                url=url,
                mode=mode,
                headless=headless,
                llm_api_key=llm_api_key,
                llm_base_url=llm_base_url,
                llm_model=llm_model,
                llm_temperature=llm_temperature,
                llm_max_tokens=llm_max_tokens,
                prompt_file=prompt_file,
                llm_version=llm_version,
            )
            sys.exit(0)
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python run.py <command> [args...]")
        print("       python run.py <url> <mode> predict [--headless|--no-headless]")
        print("       python run.py <url> <mode> generate-js [--headless|--no-headless] [--llm-model=<model>] [--prompt-file=<path>]")
        print("\nCommands:")
        print("  single <url> [mode] [selector] [--headless|--no-headless] [--raw]  - Process single URL")
        print("  batch <url1> <url2> ... [--headless|--no-headless] [--workers=N] [--raw]  - Process multiple URLs")
        print("  <url> <mode> predict [--headless|--no-headless]  - One-line end-to-end prediction workflow")
        print("  <url> <mode> generate-js [options]  - Predict selectors and generate Playwright helper JS via ZEISS LLM")
        print("\nOptions:")
        print("  --headless     - Run browser in headless mode (default)")
        print("  --no-headless  - Run browser in visible mode")
        print("  --raw          - Generate raw dataset without cleaning (for ML model testing)")
        print("  --workers=N    - Number of parallel workers for batch processing (default: 4)")
        print("  --llm-model=<name>         - LLM model for helper generation (default: gpt-4o)")
        print("  --llm-api-key=<key>        - ZEISS API key (else ZEISS_SUB_KEY env var, then built-in test key)")
        print("  --llm-base-url=<url>       - ZEISS LLM gateway base URL")
        print("  --llm-version=<plain|v1>   - Chat endpoint variant (default: v1)")
        print("  --llm-temperature=<float>  - LLM temperature (default: 0.2)")
        print("  --llm-max-tokens=<int>     - Max output tokens (default: 3000)")
        print("  --prompt-file=<path>       - Prompt template path (default: LLM/prompts/generate_helper_js_prompt.txt)")
        sys.exit(1)

    command = sys.argv[1]

    if command == "single":
        # Parse flags and separate arguments
        url = None
        mode = "all"
        custom_selector = None
        headless = True
        raw = False
        
        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg in ["--headless", "--no-headless"]:
                headless = (arg == "--headless")
                i += 1
            elif arg == "--raw":
                raw = True
                i += 1
            elif url is None:
                url = arg
                i += 1
            elif mode == "all":  # mode not set yet
                mode = arg
                i += 1
            elif custom_selector is None:
                custom_selector = arg
                i += 1
            else:
                print(f"ERROR: Unexpected argument '{arg}'")
                sys.exit(1)
        
        if not url:
            print("ERROR: single command requires URL")
            print("Example: python run.py single https://example.com --no-headless")
            sys.exit(1)
        
        generate_clean_dataset(url, mode, custom_selector, headless, raw)

    elif command == "batch":
        # Parse flags and separate URLs
        urls = []
        headless = True
        max_workers = None
        raw = False
        
        for arg in sys.argv[2:]:
            if arg == "--headless":
                headless = True
            elif arg == "--no-headless":
                headless = False
            elif arg == "--raw":
                raw = True
            elif arg.startswith("--workers="):
                try:
                    max_workers = int(arg.split("=")[1])
                except ValueError:
                    print(f"ERROR: Invalid workers value in '{arg}'")
                    sys.exit(1)
            else:
                urls.append(arg)
        
        if len(urls) < 2:
            print("ERROR: batch command requires at least 2 URLs")
            print("Example: python run.py batch https://site1.com https://site2.com --workers=2")
            sys.exit(1)
        
        run_batch(urls, headless=headless, max_workers=max_workers, raw=raw)

    else:
        print(f"ERROR: Unknown command '{command}'")
        sys.exit(1)