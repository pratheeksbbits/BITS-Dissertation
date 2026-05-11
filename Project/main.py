#!/usr/bin/env python3

import sys
import logging
from datetime import datetime

from src.scraper import extract_elements
from src.ranking_engine import rank_selectors_for_elements, DatasetBuilder
from src.data_cleaner import clean_dataset
from src.utils import save_json, generate_timestamped_filename, print_dataset_stats, validate_url, validate_css_selector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Builds a clean dataset for ML training from a website URL
def generate_clean_dataset(url: str, mode: str = "all", custom_selector: str = None, headless: bool = True, raw: bool = False) -> str:
    print(f"[TARGET] Starting integrated workflow for: {url}")
    print(f"[MODE] Mode: {mode}")
    print(f"[BROWSER] Headless mode: {'ON' if headless else 'OFF'}")
    print(f"[OUTPUT] Output mode: {'RAW (for ML testing)' if raw else 'CLEAN (for training)'}")

    try:
        print("\n[1/6] Extracting elements from webpage...")
        elements = extract_elements(url, mode=mode, custom_selector=custom_selector, headless=headless)
        if not elements:
            raise ValueError("No elements could be extracted from the URL")
        print(f"   [OK] Extracted {len(elements)} elements")

        print("\n[2/6] Ranking selectors with advanced scoring engine...")
        ranked_elements = rank_selectors_for_elements(url, elements)
        if not ranked_elements:
            raise ValueError("Failed to rank selectors")
        print(f"   [OK] Ranked selectors for {len(ranked_elements)} elements")

        print("\n[3/6] Building initial training dataset...")
        builder = DatasetBuilder()
        dataset = builder.build_dataset(url, ranked_elements)
        if not dataset:
            raise ValueError("Failed to build training dataset")
        print(f"   [OK] Generated {len(dataset)} training samples")

        if raw:
            output_filename = generate_timestamped_filename("raw_selectors_dataset", url)
            output_path = f"data/raw/{output_filename}"
            
            print(f"\n[4/4] Saving raw dataset to: {output_path}")
            save_json(dataset, output_path)
            
            print_dataset_stats(dataset, "Raw Dataset Summary")
            
            print(f"\n[SUCCESS] Raw dataset ready for ML model testing: {output_path}")
            print("This dataset contains ALL selectors without filtering - use with your ML model to predict stability!")
            return output_path

        print("\n[4/6] Cleaning and transforming dataset...")
        cleaned_dataset = clean_dataset(dataset)
        print(f"   [OK] Cleaned to {len(cleaned_dataset)} high-quality samples")

        output_filename = generate_timestamped_filename("cleaned_training_dataset", url)
        output_path = f"data/final/{output_filename}"

        print(f"\n[5/6] Saving cleaned dataset to: {output_path}")
        save_json(cleaned_dataset, output_path)

        print_dataset_stats(cleaned_dataset, "Final Dataset Summary")

        print(f"\n[SUCCESS] Clean dataset ready for XGBoost training: {output_path}")
        return output_path

    except Exception as e:
        print(f"\n[ERROR] Process failed: {str(e)}")
        raise

# Runs the command line interface for dataset generation
def main():
    if len(sys.argv) < 2:
        print("ERROR: Missing required URL argument")
        print("\nUsage: python main.py <URL> [mode] [custom_selector] [--headless|--no-headless] [--raw]")
        print("\nModes:")
        print("  interactive - Buttons, inputs, links")
        print("  text        - Headings, labels, paragraphs")
        print("  all         - Both interactive and text elements")
        print("  custom      - Use custom CSS selector (requires custom_selector argument)")
        print("\nOptions:")
        print("  --headless     - Run browser in headless mode (default)")
        print("  --no-headless  - Run browser in visible mode")
        print("  --raw          - Generate raw dataset without cleaning (for ML model testing)")
        print("\nExamples:")
        print("  python main.py https://example.com")
        print("  python main.py https://example.com text")
        print("  python main.py https://example.com custom .my-class")
        print("  python main.py https://example.com --no-headless")
        print("  python main.py https://example.com --raw")
        sys.exit(1)

    url = sys.argv[1]

    if not validate_url(url):
        print("ERROR: URL must start with http:// or https://")
        sys.exit(1)

    headless = True
    raw = False
    args_to_remove = []
    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--headless":
            headless = True
            args_to_remove.append(i)
        elif arg == "--no-headless":
            headless = False
            args_to_remove.append(i)
        elif arg == "--raw":
            raw = True
            args_to_remove.append(i)

    for i in reversed(args_to_remove):
        sys.argv.pop(i)

    mode = sys.argv[2] if len(sys.argv) > 2 else "all"
    valid_modes = ["interactive", "text", "all", "custom"]

    if mode not in valid_modes:
        print(f"ERROR: Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}")
        sys.exit(1)

    custom_selector = None
    if mode == "custom":
        if len(sys.argv) < 4:
            print("ERROR: Custom mode requires a CSS selector as the third argument")
            print("Example: python main.py https://example.com custom .my-class")
            sys.exit(1)
        custom_selector = sys.argv[3]
        if not validate_css_selector(custom_selector):
            print(f"ERROR: Custom selector contains potentially dangerous pattern")
            sys.exit(1)

    try:
        dataset_file = generate_clean_dataset(url, mode, custom_selector, headless, raw)
        if raw:
            print(f"\nSUCCESS: Raw selectors dataset saved to: {dataset_file}")
            print("Use this dataset with your ML model to predict selector stability!")
        else:
            print(f"\nSUCCESS: Clean training dataset saved to: {dataset_file}")
            print("Ready for XGBoost model training!")
    except KeyboardInterrupt:
        print("\n\nCANCELLED: Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()