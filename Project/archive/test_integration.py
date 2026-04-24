#!/usr/bin/env python3
"""
Test script for integrated scraper and ranking engine
"""

import json
from scraper_analyzed import extract_elements
from selector_ranking_engine import rank_selectors_for_elements, DatasetBuilder

def test_integration():
    # Test URL
    url = "https://www.wikipedia.com"
    mode = "text"  # Test with text mode

    print("Testing integrated scraper and ranking engine...")
    print(f"URL: {url}")
    print(f"Mode: {mode}")

    # Step 1: Extract elements using scraper
    print("\n1. Extracting elements...")
    elements = extract_elements(url, mode=mode)

    if not elements:
        print("ERROR: No elements extracted")
        return

    print(f"   Extracted {len(elements)} elements")

    # Step 2: Rank selectors using ranking engine
    print("\n2. Ranking selectors...")
    ranked_elements = rank_selectors_for_elements(url, elements)

    if not ranked_elements:
        print("ERROR: No elements ranked")
        return

    print(f"   Ranked {len(ranked_elements)} elements")

    # Step 3: Build training dataset
    print("\n3. Building training dataset...")
    builder = DatasetBuilder()
    dataset = builder.build_dataset(url, ranked_elements)

    if not dataset:
        print("ERROR: No dataset generated")
        return

    print(f"   Generated {len(dataset)} training samples")

    # Step 4: Save and show results
    output_file = "integrated_test_dataset.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"\n4. Dataset saved to {output_file}")

    # Show sample results
    print("\n5. Sample results:")
    if dataset:
        sample = dataset[0]
        print(f"   URL: {sample['url']}")
        print(f"   Tag: {sample['tag']}")
        print(f"   Text: {sample['text'][:50]}...")
        print(f"   Selector: {sample['selector']}")
        print(f"   Type: {sample['selector_type']}")
        print(f"   Score: {sample['score']}")
        print(f"   Rank: {sample['rank']}")
        print(f"   Is Best: {sample['is_best']}")

    # Count best selectors
    best_count = sum(1 for row in dataset if row['is_best'] == 1)
    print(f"\n   Total best selectors: {best_count}")

    print("\nIntegration test completed successfully!")

if __name__ == "__main__":
    test_integration()