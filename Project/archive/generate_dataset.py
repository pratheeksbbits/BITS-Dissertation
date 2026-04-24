#!/usr/bin/env python3
"""
End-to-end scraper and ranking engine workflow.
Provide a URL and get a training dataset for ML model training.
"""

import sys
import json
from datetime import datetime
from scraper_analyzed import extract_elements
from selector_ranking_engine import rank_selectors_for_elements, DatasetBuilder

def generate_training_dataset(url: str, mode: str = "all", custom_selector: str = None) -> str:
    """
    Generate training dataset from URL input.

    Args:
        url: Target URL to scrape
        mode: Extraction mode ("interactive", "text", "all", or "custom")
        custom_selector: Custom CSS selector (only used if mode="custom")

    Returns:
        Path to generated dataset file
    """
    print(f"[TARGET] Starting end-to-end workflow for: {url}")
    print(f"[MODE] Mode: {mode}")

    # Step 1: Extract elements
    print("\n[1/5] Extracting elements from webpage...")
    elements = extract_elements(url, mode=mode, custom_selector=custom_selector)

    if not elements:
        raise ValueError("No elements could be extracted from the URL")

    print(f"   [OK] Extracted {len(elements)} elements")

    # Step 2: Rank selectors
    print("\n[2/5] Ranking selectors with advanced scoring engine...")
    ranked_elements = rank_selectors_for_elements(url, elements)

    if not ranked_elements:
        raise ValueError("Failed to rank selectors")

    print(f"   [OK] Ranked selectors for {len(ranked_elements)} elements")

    # Step 3: Build training dataset
    print("\n[3/5] Building ML training dataset...")
    builder = DatasetBuilder()
    dataset = builder.build_dataset(url, ranked_elements)

    if not dataset:
        raise ValueError("Failed to build training dataset")

    print(f"   [OK] Generated {len(dataset)} training samples")

    # Step 4: Save dataset
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"training_dataset_{timestamp}.json"

    print(f"\n[4/5] Saving dataset to: {filename}")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    # Step 5: Show summary
    best_selectors = [row for row in dataset if row['is_best'] == 1]
    print("\n[5/5] Dataset Summary:")
    print(f"   • Total training samples: {len(dataset)}")
    print(f"   • Best selectors identified: {len(best_selectors)}")
    print(f"   • Elements processed: {len(ranked_elements)}")
    print(f"   • Average selectors per element: {len(dataset) / len(ranked_elements):.1f}")

    # Show top 3 best selectors
    print("\n[TOP] Top 3 Best Selectors:")
    for i, row in enumerate(best_selectors[:3], 1):
        print(f"   {i}. {row['selector']} (score: {row['score']:.1f}) - {row['tag']} element")

    print(f"\n[SUCCESS] Workflow completed! Dataset ready for ML training: {filename}")
    return filename

def main():
    """Command line interface for the integrated scraper."""
    if len(sys.argv) < 2:
        print("ERROR: Missing required URL argument")
        print("\nUsage: python generate_dataset.py <URL> [mode] [custom_selector]")
        print("\nModes:")
        print("  interactive - Buttons, inputs, links")
        print("  text        - Headings, labels, paragraphs")
        print("  all         - Both interactive and text elements")
        print("  custom      - Use custom CSS selector (requires custom_selector argument)")
        print("\nExamples:")
        print("  python generate_dataset.py https://example.com")
        print("  python generate_dataset.py https://example.com text")
        print("  python generate_dataset.py https://example.com custom .my-class")
        sys.exit(1)

    url = sys.argv[1]

    # Validate URL format
    if not url.startswith(('http://', 'https://')):
        print("ERROR: URL must start with http:// or https://")
        sys.exit(1)

    # Parse mode
    mode = sys.argv[2] if len(sys.argv) > 2 else "all"
    valid_modes = ["interactive", "text", "all", "custom"]

    if mode not in valid_modes:
        print(f"ERROR: Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}")
        sys.exit(1)

    # Handle custom selector requirement
    custom_selector = None
    if mode == "custom":
        if len(sys.argv) < 4:
            print("ERROR: Custom mode requires a CSS selector as the third argument")
            print("Example: python generate_dataset.py https://example.com custom .my-class")
            sys.exit(1)
        custom_selector = sys.argv[3]
        if not custom_selector.strip():
            print("ERROR: Custom selector cannot be empty")
            sys.exit(1)
    elif len(sys.argv) > 3:
        print(f"WARNING: Extra argument '{sys.argv[3]}' ignored (mode '{mode}' doesn't use custom selector)")

    # Validate custom selector if provided
    if custom_selector:
        dangerous_patterns = ['<', 'javascript:', 'onerror=', 'onclick=', 'onload=']
        for pattern in dangerous_patterns:
            if pattern in custom_selector.lower():
                print(f"ERROR: Custom selector contains potentially dangerous pattern: '{pattern}'")
                sys.exit(1)

    try:
        dataset_file = generate_training_dataset(url, mode, custom_selector)
        print(f"\nSUCCESS: Training dataset saved to: {dataset_file}")
    except KeyboardInterrupt:
        print("\n\nCANCELLED: Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nERROR: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()