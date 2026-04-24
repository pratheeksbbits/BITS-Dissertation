#!/usr/bin/env python3
"""
Simple test for the integrated scraper framework
"""

import subprocess
import sys
import os

def test_single_case():
    """Test one URL with one mode"""
    url = "https://www.google.com"
    mode = "text"

    print(f"Testing: {url} with mode: {mode}")

    # Run the command
    cmd = ["py", "generate_dataset.py", url, mode]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

    print(f"Exit code: {result.returncode}")

    if result.returncode == 0:
        print("SUCCESS!")
        # Check if dataset file was created
        for line in result.stdout.split('\n'):
            if "Dataset ready for ML training:" in line:
                filename = line.split(":")[-1].strip()
                print(f"Dataset file: {filename}")
                if os.path.exists(filename):
                    print("File exists!")
                    # Check file size
                    size = os.path.getsize(filename)
                    print(f"File size: {size} bytes")
                else:
                    print("File does not exist!")
                break
    else:
        print("FAILED!")
        print("STDOUT:", result.stdout)
        print("STDERR:", result.stderr)

if __name__ == "__main__":
    test_single_case()