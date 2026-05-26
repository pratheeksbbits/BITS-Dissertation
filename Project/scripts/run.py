#!/usr/bin/env python3

import sys
import os
import json
import re
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import generate_clean_dataset
from src.scraper import extract_elements, extract_elements_from_page
from src.ranking_engine import rank_selectors_for_elements, rank_selectors_for_elements_on_page
from src.utils import generate_timestamped_filename, save_json, validate_url, extract_domain
from ml.evaluate import SelectorStabilityInference
from LLM.zeiss_gateway_client import ZeissLLMGatewayClient
import pandas as pd

DEFAULT_LLM_BASE_URL = "https://api.genai.zeiss.com/llm"
DEFAULT_LLM_MODEL = "gpt-4o"
DEFAULT_LLM_API_KEY = "827180ec60ba42d5a82503b538298779"
DEFAULT_PROMPT_FILE = "LLM/prompts/generate_helper_js_prompt.txt"
DEFAULT_DIRECT_PROMPT_FILE = "LLM/prompts/generate_helper_js_direct_prompt.txt"
DEFAULT_CDP_URL = "http://127.0.0.1:9222"

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


def _is_usable_selector(selector, selector_type):
    if not selector or not str(selector).strip():
        return False

    s = str(selector).strip()
    t = str(selector_type or "").strip().lower()

    # Reject clearly broken selectors.
    if s in {".", "#", "[]", "._", "#.", ".."}:
        return False
    if len(s) < 2:
        return False

    if t in {"id"} and not s.startswith("#"):
        return False
    if t in {"xpath"} and not (s.startswith("/") or s.startswith("(") or s.startswith("xpath=")):
        return False
    if t in {"text", "text_based"} and "text=" not in s and "getByText(" not in s:
        return False
    if t in {"placeholder", "aria-label", "name", "data-testid"} and "[" not in s and "getBy" not in s:
        return False

    return True


def _selector_priority(row):
    usable = 1 if _is_usable_selector(row.get("selector"), row.get("selector_type")) else 0
    stable = 1 if row.get("prediction") == 1 else 0
    prob = float(row.get("probability", 0))
    conf = float(row.get("confidence", 0))
    sel_len = len(str(row.get("selector", "")))

    # Strong preference order: usable > stable > high probability > confidence > shorter selector.
    return (usable, stable, prob, conf, -sel_len)


def _safe_js_string(value):
    return json.dumps(str(value), ensure_ascii=False)


def _to_method_suffix(text):
    raw = re.sub(r"[^a-zA-Z0-9]+", " ", str(text or "")).strip()
    if not raw:
        return "Generic"
    parts = [p for p in raw.split(" ") if p][:2]
    suffix = "".join(p[:1].upper() + p[1:] for p in parts)
    # Keep helper names short and readable.
    return suffix[:16] if suffix else "Generic"


def _element_type_name(tag):
    t = str(tag or "").strip().lower()
    if not t:
        return "Element"

    semantic_map = {
        "a": "Link",
        "button": "Button",
        "input": "Input",
        "textarea": "Textarea",
        "select": "Select",
        "img": "Image",
        "form": "Form",
        "div": "Div",
        "span": "Span",
        "h1": "Heading",
        "h2": "Heading",
        "h3": "Heading",
        "h4": "Heading",
        "h5": "Heading",
        "h6": "Heading",
    }
    if t in semantic_map:
        return semantic_map[t]

    cleaned = re.sub(r"[^a-zA-Z0-9]+", " ", t).strip()
    if not cleaned:
        return "Element"

    token = cleaned.split(" ")[0]
    if not token or not token[0].isalpha():
        return "Element"
    return token[:1].upper() + token[1:]


def _action_prefix(tag):
    t = str(tag or "").strip().lower()
    if t in {"button", "a"}:
        return "click"
    if t in {"input", "textarea"}:
        return "fill"
    return "waitFor"


def _build_guaranteed_helpers(predictions_payload):
    best = predictions_payload.get("best_selectors", [])
    lines = []
    lines.append("class GeneratedPageHelpers {")
    lines.append("  constructor(page) {")
    lines.append("    this.page = page;")
    lines.append("  }")
    lines.append("")

    method_names = []

    for item in best:
        eid = item.get("element_id")
        tag = str(item.get("tag", "")).lower()
        selector = str(item.get("best_selector", "")).strip()
        stable = bool(item.get("is_stable", False))

        suffix = _to_method_suffix(item.get("text") or "")
        element_type = _element_type_name(tag)
        action = _action_prefix(tag)
        method = f"{action}{element_type}{suffix}"

        if tag in {"button", "a"}:
            body = [f"await this.page.click({_safe_js_string(selector)});"]
        elif tag in {"input", "textarea"}:
            body = [f"await this.page.fill({_safe_js_string(selector)}, value);"]
        else:
            body = [f"await this.page.waitForSelector({_safe_js_string(selector)}, {{ state: 'visible' }});"]

        # Ensure unique method names.
        original = method
        i = 2
        while method in method_names:
            method = f"{original}{i}"
            i += 1
        method_names.append(method)

        lines.append(f"  // element_id={eid}, tag={tag}, stable={str(stable).lower()}")
        if tag in {"input", "textarea"}:
            lines.append(f"  async {method}(value) {{")
        else:
            lines.append(f"  async {method}() {{")
        for stmt in body:
            lines.append(f"    {stmt}")
        lines.append("  }")
        lines.append("")

    lines.append("}")
    lines.append("")
    lines.append("module.exports = GeneratedPageHelpers;")

    return "\n".join(lines), method_names


def _llm_has_all_methods(helper_js, required_methods):
    for name in required_methods:
        if re.search(rf"\b{name}\s*\(", helper_js) is None:
            return False
    return True


def _build_guaranteed_helpers_from_candidate_payload(candidate_payload):
    lines = []
    lines.append("class GeneratedPageHelpers {")
    lines.append("  constructor(page) {")
    lines.append("    this.page = page;")
    lines.append("  }")
    lines.append("")

    method_names = []
    for element in candidate_payload.get("elements", []):
        eid = element.get("element_id")
        tag = str(element.get("tag", "")).lower()
        text = element.get("text", "")
        candidates = element.get("candidate_selectors", [])
        if not candidates:
            continue

        selector = candidates[0].get("selector", "")
        action = _action_prefix(tag)
        element_type = _element_type_name(tag)
        suffix = _to_method_suffix(text)
        method = f"{action}{element_type}{suffix}"

        original = method
        i = 2
        while method in method_names:
            method = f"{original}{i}"
            i += 1
        method_names.append(method)

        lines.append(f"  // element_id={eid}, selected_by=deterministic")
        if tag in {"input", "textarea"}:
            lines.append(f"  async {method}(value) {{")
            lines.append(f"    await this.page.fill({_safe_js_string(selector)}, value);")
        elif tag in {"button", "a"}:
            lines.append(f"  async {method}() {{")
            lines.append(f"    await this.page.click({_safe_js_string(selector)});")
        else:
            lines.append(f"  async {method}() {{")
            lines.append(f"    await this.page.waitForSelector({_safe_js_string(selector)}, {{ state: 'visible' }});")
        lines.append("  }")
        lines.append("")

    lines.append("}")
    lines.append("")
    lines.append("module.exports = GeneratedPageHelpers;")

    return "\n".join(lines), method_names


def _llm_has_all_element_comments(helper_js, element_ids):
    for eid in element_ids:
        if re.search(rf"element_id\s*=\s*{eid}\b", helper_js) is None:
            return False
    return True


def _build_direct_candidate_artifacts(url, mode, ranked_elements, input_mode="raw"):
    raw_rows = _build_raw_rows_from_ranked(url, ranked_elements)
    if not raw_rows:
        raise ValueError("No selectors available for direct LLM workflow")

    os.makedirs("data/raw", exist_ok=True)
    raw_output_filename = generate_timestamped_filename("direct_llm_selectors_raw", url)
    raw_output_path = f"data/raw/{raw_output_filename}"
    save_json(raw_rows, raw_output_path)

    rows_for_llm = raw_rows if input_mode == "raw" else _clean_raw_selector_rows(raw_rows)
    if not rows_for_llm:
        rows_for_llm = raw_rows

    candidate_payload = _group_selector_candidates_for_llm(url, mode, rows_for_llm)

    os.makedirs("data/predictions", exist_ok=True)
    candidate_output_path = f"data/predictions/direct_llm_candidates_{extract_domain(url)}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    save_json(candidate_payload, candidate_output_path)

    return raw_output_path, candidate_output_path, candidate_payload


def _generate_helper_from_direct_candidates(
    url,
    mode,
    raw_output_path,
    candidate_output_path,
    candidate_payload,
    llm_api_key,
    llm_base_url,
    llm_model,
    llm_temperature,
    llm_max_tokens,
    prompt_file,
    llm_version,
):
    if not os.path.exists(prompt_file):
        raise FileNotFoundError(
            f"Prompt file not found: {prompt_file}. Create it or pass --prompt-file=<path>."
        )

    with open(prompt_file, "r", encoding="utf-8") as f:
        prompt_template = f.read()

    candidates_json = json.dumps(candidate_payload, indent=2, ensure_ascii=False)
    final_prompt = (
        prompt_template
        .replace("{{URL}}", url)
        .replace("{{MODE}}", mode)
        .replace("{{SCRAPER_CANDIDATES_JSON}}", candidates_json)
    )

    print("[DIRECT LLM 2/3] Calling ZEISS LLM endpoint...")
    effective_api_key = llm_api_key or os.getenv("ZEISS_SUB_KEY") or DEFAULT_LLM_API_KEY
    client = ZeissLLMGatewayClient(base_url=llm_base_url, api_key=effective_api_key, timeout=180)

    chat_response = client.chat_completions(
        body={
            "model": llm_model,
            "messages": [
                {
                    "role": "system",
                    "content": "You generate Playwright helper JavaScript from selector candidate JSON. Choose the best selector per element and provide one helper for each element_id.",
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

    llm_helper_js = _unwrap_js_fence(_extract_chat_content(chat_response))
    deterministic_js, _ = _build_guaranteed_helpers_from_candidate_payload(candidate_payload)
    element_ids = [e.get("element_id") for e in candidate_payload.get("elements", [])]

    if llm_helper_js and _llm_has_all_element_comments(llm_helper_js, element_ids):
        helper_js = llm_helper_js
        helper_source = "llm-direct"
    else:
        helper_js = deterministic_js
        helper_source = "deterministic-fallback"
        print("[WARN] Direct LLM output missed one or more element_id sections. Using deterministic full-coverage helper generation.")

    print("[DIRECT LLM 3/3] Saving generated helper JavaScript...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = extract_domain(url)
    os.makedirs("data/helpers", exist_ok=True)

    js_output_path = f"data/helpers/generated_helpers_{domain}_{timestamp}.js"
    metadata_output_path = f"data/helpers/generated_helpers_metadata_{domain}_{timestamp}.json"
    llm_raw_output_path = f"data/helpers/generated_helpers_llm_raw_{domain}_{timestamp}.js"

    with open(js_output_path, "w", encoding="utf-8") as f:
        f.write(helper_js)

    if llm_helper_js:
        with open(llm_raw_output_path, "w", encoding="utf-8") as f:
            f.write(llm_helper_js)

    metadata = {
        "url": url,
        "mode": mode,
        "generated_at": timestamp,
        "strategy": "direct-llm",
        "llm_base_url": llm_base_url,
        "llm_model": llm_model,
        "llm_version": llm_version,
        "prompt_file": prompt_file,
        "helper_source": helper_source,
        "raw_dataset_path": raw_output_path,
        "candidates_path": candidate_output_path,
        "helper_js_path": js_output_path,
        "llm_raw_helper_js_path": llm_raw_output_path,
    }
    save_json(metadata, metadata_output_path)

    print(f"   [OK] Helper JavaScript saved: {js_output_path}")
    print(f"   [OK] Generation metadata saved: {metadata_output_path}")
    print("\n[SUCCESS] Direct LLM helper generation workflow completed.")

    return {
        "raw_dataset_path": raw_output_path,
        "candidates_path": candidate_output_path,
        "helper_js_path": js_output_path,
        "metadata_path": metadata_output_path,
    }


def run_direct_llm_workflow(
    url,
    mode="all",
    headless=True,
    llm_api_key=None,
    llm_base_url=DEFAULT_LLM_BASE_URL,
    llm_model=DEFAULT_LLM_MODEL,
    llm_temperature=0.2,
    llm_max_tokens=3000,
    prompt_file=DEFAULT_DIRECT_PROMPT_FILE,
    llm_version="v1",
    direct_input_mode="raw",
):
    if not validate_url(url):
        raise ValueError("URL must start with http:// or https://")

    valid_modes = ["interactive", "text", "all"]
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}")

    print("\n[DIRECT LLM] Starting scraper-to-LLM workflow (XGBoost bypass)...")
    print(f"[TARGET] {url}")
    print(f"[MODE] {mode}")
    print(f"[INPUT] Selector candidate mode: {direct_input_mode}")

    print("\n[DIRECT LLM 1/3] Extracting and ranking selectors...")
    elements = extract_elements(url, mode=mode, headless=headless)
    if not elements:
        raise ValueError("No elements extracted from URL")

    ranked_elements = rank_selectors_for_elements(url, elements)
    if not ranked_elements:
        raise ValueError("No ranked selectors produced")

    raw_output_path, candidate_output_path, candidate_payload = _build_direct_candidate_artifacts(
        url,
        mode,
        ranked_elements,
        input_mode=direct_input_mode,
    )

    return _generate_helper_from_direct_candidates(
        url=url,
        mode=mode,
        raw_output_path=raw_output_path,
        candidate_output_path=candidate_output_path,
        candidate_payload=candidate_payload,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_max_tokens=llm_max_tokens,
        prompt_file=prompt_file,
        llm_version=llm_version,
    )


def run_direct_llm_workflow_from_page(
    page,
    mode="all",
    llm_api_key=None,
    llm_base_url=DEFAULT_LLM_BASE_URL,
    llm_model=DEFAULT_LLM_MODEL,
    llm_temperature=0.2,
    llm_max_tokens=3000,
    prompt_file=DEFAULT_DIRECT_PROMPT_FILE,
    llm_version="v1",
    direct_input_mode="raw",
):
    current_url = page.url
    print("\n[DIRECT LLM] Starting scraper-to-LLM workflow from live browser context (XGBoost bypass)...")
    print(f"[TARGET] {current_url}")
    print(f"[MODE] {mode}")
    print(f"[INPUT] Selector candidate mode: {direct_input_mode}")

    print("\n[DIRECT LLM 1/3] Extracting and ranking selectors from existing context...")
    elements = extract_elements_from_page(page, mode=mode)
    if not elements:
        raise ValueError("No elements extracted from current page")
    ranked_elements = rank_selectors_for_elements_on_page(page, elements)
    if not ranked_elements:
        raise ValueError("No ranked selectors produced")

    raw_output_path, candidate_output_path, candidate_payload = _build_direct_candidate_artifacts(
        current_url,
        mode,
        ranked_elements,
        input_mode=direct_input_mode,
    )

    return _generate_helper_from_direct_candidates(
        url=current_url,
        mode=mode,
        raw_output_path=raw_output_path,
        candidate_output_path=candidate_output_path,
        candidate_payload=candidate_payload,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_max_tokens=llm_max_tokens,
        prompt_file=prompt_file,
        llm_version=llm_version,
    )


def _build_raw_rows_from_ranked(url, ranked_elements):
    rows = []
    for element_id, element in enumerate(ranked_elements):
        for sel_data in element.get("ranked_selectors", []):
            rows.append(
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
    return rows


def _selector_type_priority(selector_type):
    priorities = {
        "data-testid": 10,
        "id": 9,
        "name": 8,
        "aria-label": 7,
        "placeholder": 6,
        "text": 5,
        "css": 4,
        "class": 3,
        "xpath": 2,
        "role_based": 1,
        "text_based": 1,
        "test_id": 1,
    }
    return priorities.get(str(selector_type or "").lower(), 0)


def _clean_raw_selector_rows(raw_rows):
    cleaned = []
    seen = set()
    for row in raw_rows:
        key = (row.get("element_id"), row.get("selector"), row.get("selector_type"))
        if key in seen:
            continue
        seen.add(key)

        if not _is_usable_selector(row.get("selector"), row.get("selector_type")):
            continue

        # Discard very long absolute XPaths unless no better options remain later.
        selector = str(row.get("selector", ""))
        if row.get("selector_type") == "xpath" and len(selector) > 120:
            continue

        cleaned.append(row)

    return cleaned


def _group_selector_candidates_for_llm(url, mode, selector_rows, max_candidates_per_element=8):
    grouped = {}
    for row in selector_rows:
        eid = row.get("element_id")
        grouped.setdefault(eid, []).append(row)

    payload_elements = []
    for eid in sorted(grouped.keys()):
        rows = grouped[eid]

        rows_sorted = sorted(
            rows,
            key=lambda r: (
                1 if _is_usable_selector(r.get("selector"), r.get("selector_type")) else 0,
                _selector_type_priority(r.get("selector_type")),
                float(r.get("rule_score", 0)),
                -len(str(r.get("selector", ""))),
            ),
            reverse=True,
        )

        top = rows_sorted[:max_candidates_per_element]
        head = top[0]

        payload_elements.append(
            {
                "element_id": eid,
                "tag": head.get("tag", ""),
                "text": head.get("text", ""),
                "candidate_selectors": [
                    {
                        "selector": r.get("selector", ""),
                        "selector_type": r.get("selector_type", ""),
                        "rule_score": r.get("rule_score", 0),
                        "rule_rank": r.get("rule_rank", 0),
                    }
                    for r in top
                ],
            }
        )

    return {
        "url": url,
        "mode": mode,
        "generated_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "total_elements": len(payload_elements),
        "elements": payload_elements,
    }

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
    return _finalize_prediction_outputs(url, mode, elements, ranked_elements)


# Persists prediction artifacts from extracted + ranked element data
def _finalize_prediction_outputs(url, mode, elements, ranked_elements):
    if not ranked_elements:
        raise ValueError("Failed to rank selectors")
    print(f"   [OK] Ranked selectors for {len(ranked_elements)} elements")

    raw_rows = _build_raw_rows_from_ranked(url, ranked_elements)

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

    # Pick the best selector per element with quality gating so broken selectors are not preferred.
    best_by_element = {}
    for row in enriched_rows:
        element_id = row["element_id"]
        current = best_by_element.get(element_id)
        if current is None:
            best_by_element[element_id] = row
            continue

        is_better = _selector_priority(row) > _selector_priority(current)
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


# Runs prediction workflow directly on an existing Playwright page context
def run_predict_workflow_from_page(page, mode="all"):
    current_url = page.url
    if not current_url or not current_url.startswith("http"):
        raise ValueError("Current page URL is invalid. Navigate to a valid http/https page first.")

    valid_modes = ["interactive", "text", "all"]
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}")

    print(f"[TARGET] Predict workflow for existing browser context: {current_url}")
    print(f"[MODE] Mode: {mode}")
    print("[BROWSER] Source: existing live browser context")

    print("\n[1/5] Extracting webpage elements from existing context...")
    elements = extract_elements_from_page(page, mode=mode)
    if not elements:
        raise ValueError("No elements extracted from the current browser page")
    print(f"   [OK] Extracted {len(elements)} elements")

    print("\n[2/5] Ranking selectors for each element on existing context...")
    ranked_elements = rank_selectors_for_elements_on_page(page, elements)
    return _finalize_prediction_outputs(current_url, mode, elements, ranked_elements)


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
    helper_strategy="xgboost",
    direct_input_mode="raw",
):
    if helper_strategy == "direct-llm":
        return run_direct_llm_workflow(
            url=url,
            mode=mode,
            headless=headless,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            llm_model=llm_model,
            llm_temperature=llm_temperature,
            llm_max_tokens=llm_max_tokens,
            prompt_file=prompt_file or DEFAULT_DIRECT_PROMPT_FILE,
            llm_version=llm_version,
            direct_input_mode=direct_input_mode,
        )

    print("\n[E2E] Starting end-to-end helper generation workflow...")

    raw_output_path, best_output_path = run_predict_workflow(url, mode=mode, headless=headless)
    return _generate_helper_from_predictions(
        url=url,
        mode=mode,
        raw_output_path=raw_output_path,
        best_output_path=best_output_path,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_max_tokens=llm_max_tokens,
        prompt_file=prompt_file,
        llm_version=llm_version,
    )


# Runs end-to-end helper generation from an existing Playwright page context
def run_e2e_helper_workflow_from_page(
    page,
    mode="all",
    llm_api_key=None,
    llm_base_url=DEFAULT_LLM_BASE_URL,
    llm_model=DEFAULT_LLM_MODEL,
    llm_temperature=0.2,
    llm_max_tokens=3000,
    prompt_file=DEFAULT_PROMPT_FILE,
    llm_version="v1",
    helper_strategy="xgboost",
    direct_input_mode="raw",
):
    if helper_strategy == "direct-llm":
        return run_direct_llm_workflow_from_page(
            page=page,
            mode=mode,
            llm_api_key=llm_api_key,
            llm_base_url=llm_base_url,
            llm_model=llm_model,
            llm_temperature=llm_temperature,
            llm_max_tokens=llm_max_tokens,
            prompt_file=prompt_file or DEFAULT_DIRECT_PROMPT_FILE,
            llm_version=llm_version,
            direct_input_mode=direct_input_mode,
        )

    print("\n[E2E] Starting end-to-end helper generation workflow from live browser context...")

    raw_output_path, best_output_path = run_predict_workflow_from_page(page, mode=mode)

    return _generate_helper_from_predictions(
        url=page.url,
        mode=mode,
        raw_output_path=raw_output_path,
        best_output_path=best_output_path,
        llm_api_key=llm_api_key,
        llm_base_url=llm_base_url,
        llm_model=llm_model,
        llm_temperature=llm_temperature,
        llm_max_tokens=llm_max_tokens,
        prompt_file=prompt_file,
        llm_version=llm_version,
    )


def _generate_helper_from_predictions(
    url,
    mode,
    raw_output_path,
    best_output_path,
    llm_api_key,
    llm_base_url,
    llm_model,
    llm_temperature,
    llm_max_tokens,
    prompt_file,
    llm_version,
):
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
                    "content": "You generate high-quality Playwright helper JavaScript files based on selector prediction JSON. Method names must be readable and follow Action+ElementType+Text naming without element IDs.",
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

    llm_helper_js = _unwrap_js_fence(_extract_chat_content(chat_response))

    guaranteed_helper_js, required_methods = _build_guaranteed_helpers(predictions_payload)

    if llm_helper_js and _llm_has_all_methods(llm_helper_js, required_methods):
        helper_js = llm_helper_js
        helper_source = "llm"
    else:
        helper_js = guaranteed_helper_js
        helper_source = "deterministic-fallback"
        print("[WARN] LLM output missed one or more required element helpers. Using deterministic full-coverage helper generation.")

    print("[E2E 3/3] Saving generated helper JavaScript...")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    domain = extract_domain(url)

    os.makedirs("data/helpers", exist_ok=True)
    js_output_path = f"data/helpers/generated_helpers_{domain}_{timestamp}.js"
    metadata_output_path = f"data/helpers/generated_helpers_metadata_{domain}_{timestamp}.json"
    llm_raw_output_path = f"data/helpers/generated_helpers_llm_raw_{domain}_{timestamp}.js"

    with open(js_output_path, "w", encoding="utf-8") as f:
        f.write(helper_js)

    if llm_helper_js:
        with open(llm_raw_output_path, "w", encoding="utf-8") as f:
            f.write(llm_helper_js)

    metadata = {
        "url": url,
        "mode": mode,
        "generated_at": timestamp,
        "llm_base_url": llm_base_url,
        "llm_model": llm_model,
        "llm_version": llm_version,
        "prompt_file": prompt_file,
        "helper_source": helper_source,
        "required_helper_count": len(required_methods),
        "raw_dataset_path": raw_output_path,
        "predictions_path": best_output_path,
        "helper_js_path": js_output_path,
        "llm_raw_helper_js_path": llm_raw_output_path,
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


def _pick_active_page_from_browser(browser):
    candidate_page = None

    for context in browser.contexts:
        for page in context.pages:
            if page.url and page.url != "about:blank":
                candidate_page = page

    if candidate_page is None:
        for context in browser.contexts:
            if context.pages:
                candidate_page = context.pages[-1]

    if candidate_page is None:
        raise ValueError("No open pages found in connected browser context.")

    return candidate_page


def run_context_workflow_via_cdp(
    mode,
    workflow,
    cdp_url=DEFAULT_CDP_URL,
    llm_api_key=None,
    llm_base_url=DEFAULT_LLM_BASE_URL,
    llm_model=DEFAULT_LLM_MODEL,
    llm_temperature=0.2,
    llm_max_tokens=3000,
    prompt_file=DEFAULT_PROMPT_FILE,
    llm_version="v1",
    helper_strategy="xgboost",
    direct_input_mode="raw",
):
    print(f"[CONTEXT] Connecting to live browser via CDP: {cdp_url}")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp(cdp_url)
        page = _pick_active_page_from_browser(browser)
        print(f"[CONTEXT] Using active page: {page.url}")

        if workflow == "predict":
            result = run_predict_workflow_from_page(page, mode=mode)
        elif workflow == "generate-js":
            result = run_e2e_helper_workflow_from_page(
                page=page,
                mode=mode,
                llm_api_key=llm_api_key,
                llm_base_url=llm_base_url,
                llm_model=llm_model,
                llm_temperature=llm_temperature,
                llm_max_tokens=llm_max_tokens,
                prompt_file=prompt_file,
                llm_version=llm_version,
                helper_strategy=helper_strategy,
                direct_input_mode=direct_input_mode,
            )
        else:
            raise ValueError("Invalid workflow for context mode. Use 'predict' or 'generate-js'.")

        browser.close()
        return result

if __name__ == "__main__":
    # Context workflow using live browser state:
    # python scripts/run.py context <mode> <predict|generate-js> [--cdp-url=http://127.0.0.1:9222] [llm options]
    if len(sys.argv) >= 4 and sys.argv[1].lower() == "context":
        mode = sys.argv[2]
        workflow = sys.argv[3].lower()

        cdp_url = DEFAULT_CDP_URL
        llm_api_key = None
        llm_base_url = DEFAULT_LLM_BASE_URL
        llm_model = DEFAULT_LLM_MODEL
        llm_temperature = 0.2
        llm_max_tokens = 3000
        prompt_file = DEFAULT_PROMPT_FILE
        llm_version = "v1"
        helper_strategy = "xgboost"
        direct_input_mode = "raw"

        for arg in sys.argv[4:]:
            if arg.startswith("--cdp-url="):
                cdp_url = arg.split("=", 1)[1]
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
            elif arg.startswith("--helper-strategy="):
                helper_strategy = arg.split("=", 1)[1]
                if helper_strategy not in ["xgboost", "direct-llm"]:
                    print("ERROR: --helper-strategy must be 'xgboost' or 'direct-llm'")
                    sys.exit(1)
                if helper_strategy == "direct-llm" and prompt_file == DEFAULT_PROMPT_FILE:
                    prompt_file = DEFAULT_DIRECT_PROMPT_FILE
            elif arg.startswith("--direct-input="):
                direct_input_mode = arg.split("=", 1)[1]
                if direct_input_mode not in ["raw", "cleaned"]:
                    print("ERROR: --direct-input must be 'raw' or 'cleaned'")
                    sys.exit(1)
            else:
                print(f"ERROR: Unexpected argument '{arg}'")
                sys.exit(1)

        try:
            run_context_workflow_via_cdp(
                mode=mode,
                workflow=workflow,
                cdp_url=cdp_url,
                llm_api_key=llm_api_key,
                llm_base_url=llm_base_url,
                llm_model=llm_model,
                llm_temperature=llm_temperature,
                llm_max_tokens=llm_max_tokens,
                prompt_file=prompt_file,
                llm_version=llm_version,
                helper_strategy=helper_strategy,
                direct_input_mode=direct_input_mode,
            )
            sys.exit(0)
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)

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
        helper_strategy = "xgboost"
        direct_input_mode = "raw"

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
            elif arg.startswith("--helper-strategy="):
                helper_strategy = arg.split("=", 1)[1]
                if helper_strategy not in ["xgboost", "direct-llm"]:
                    print("ERROR: --helper-strategy must be 'xgboost' or 'direct-llm'")
                    sys.exit(1)
                if helper_strategy == "direct-llm" and prompt_file == DEFAULT_PROMPT_FILE:
                    prompt_file = DEFAULT_DIRECT_PROMPT_FILE
            elif arg.startswith("--direct-input="):
                direct_input_mode = arg.split("=", 1)[1]
                if direct_input_mode not in ["raw", "cleaned"]:
                    print("ERROR: --direct-input must be 'raw' or 'cleaned'")
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
                helper_strategy=helper_strategy,
                direct_input_mode=direct_input_mode,
            )
            sys.exit(0)
        except Exception as e:
            print(f"ERROR: {e}")
            sys.exit(1)

    if len(sys.argv) < 2:
        print("Usage: python run.py <command> [args...]")
        print("       python run.py context <mode> <predict|generate-js> [--cdp-url=http://127.0.0.1:9222] [llm options]")
        print("       python run.py <url> <mode> predict [--headless|--no-headless]")
        print("       python run.py <url> <mode> generate-js [--headless|--no-headless] [--llm-model=<model>] [--prompt-file=<path>]")
        print("\nCommands:")
        print("  single <url> [mode] [selector] [--headless|--no-headless] [--raw]  - Process single URL")
        print("  batch <url1> <url2> ... [--headless|--no-headless] [--workers=N] [--raw]  - Process multiple URLs")
        print("  context <mode> <predict|generate-js> [options]  - Run workflow on existing live browser context via CDP")
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
        print("  --cdp-url=<url>            - CDP endpoint for context mode (default: http://127.0.0.1:9222)")
        print("  --helper-strategy=<name>   - xgboost or direct-llm (default: xgboost)")
        print("  --direct-input=<mode>      - raw or cleaned selector candidates for direct-llm (default: raw)")
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