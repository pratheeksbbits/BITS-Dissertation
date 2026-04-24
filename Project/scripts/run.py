#!/usr/bin/env python3
"""
Alternative script runner for the framework.
Can be used for batch processing or different entry points.
"""

import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add src and project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from main import generate_clean_dataset

def run_batch(urls, mode="all", headless=True, max_workers=None):
    """Run the framework on multiple URLs with optional parallelism."""
    if max_workers is None:
        max_workers = min(len(urls), 4)  # Default to 4 workers max, or number of URLs if less

    print(f"Starting batch processing with {max_workers} parallel workers...")
    print(f"Headless mode: {'ON' if headless else 'OFF'}")
    print(f"Processing {len(urls)} URLs: {', '.join(urls[:3])}{'...' if len(urls) > 3 else ''}")
    print()

    results = []

    def process_url(url):
        """Process a single URL and return result."""
        try:
            print(f"[{urls.index(url)+1}/{len(urls)}] Processing: {url}")
            dataset_file = generate_clean_dataset(url, mode, headless=headless)
            print(f"[{urls.index(url)+1}/{len(urls)}] ✓ Completed: {url} -> {dataset_file}")
            return (url, dataset_file, "SUCCESS")
        except Exception as e:
            print(f"[{urls.index(url)+1}/{len(urls)}] ✗ Failed: {url} -> {e}")
            return (url, None, str(e))

    # Use ThreadPoolExecutor for parallelism
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_url = {executor.submit(process_url, url): url for url in urls}

        # Collect results as they complete
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

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python run.py <command> [args...]")
        print("\nCommands:")
        print("  single <url> [mode] [selector] [--headless|--no-headless]  - Process single URL")
        print("  batch <url1> <url2> ... [--headless|--no-headless] [--workers=N]  - Process multiple URLs")
        print("\nOptions:")
        print("  --headless     - Run browser in headless mode (default)")
        print("  --no-headless  - Run browser in visible mode")
        print("  --workers=N    - Number of parallel workers for batch processing (default: 4)")
        sys.exit(1)

    command = sys.argv[1]

    if command == "single":
        # Parse flags and separate arguments
        url = None
        mode = "all"
        custom_selector = None
        headless = True
        
        i = 2
        while i < len(sys.argv):
            arg = sys.argv[i]
            if arg in ["--headless", "--no-headless"]:
                headless = (arg == "--headless")
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
        
        generate_clean_dataset(url, mode, custom_selector, headless)

    elif command == "batch":
        # Parse flags and separate URLs
        urls = []
        headless = True
        max_workers = None
        
        for arg in sys.argv[2:]:
            if arg == "--headless":
                headless = True
            elif arg == "--no-headless":
                headless = False
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
        
        run_batch(urls, headless=headless, max_workers=max_workers)

    else:
        print(f"ERROR: Unknown command '{command}'")
        sys.exit(1)