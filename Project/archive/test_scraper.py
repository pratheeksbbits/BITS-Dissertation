#!/usr/bin/env python3
"""
Comprehensive test suite for the integrated scraper and ranking engine.
Tests all modes for multiple URLs and validates output accuracy.
"""

import os
import json
import subprocess
import sys
from typing import Dict, List, Tuple
from pathlib import Path

class ScraperTester:
    """Comprehensive test suite for the scraper framework."""

    def __init__(self):
        # Test with fewer URLs and modes for initial testing
        self.test_urls = [
            "https://www.google.com",
            "https://www.wikipedia.com"
        ]

        self.test_modes = [
            ("all", None),
            ("text", None),
            ("custom", "h1, h2, h3")
        ]

        self.results = []

    def run_command(self, cmd: List[str]) -> Tuple[int, str, str]:
        """Run a command and return exit code, stdout, stderr."""
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=os.getcwd()
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "Command timed out after 5 minutes"
        except Exception as e:
            return -2, "", f"Command execution failed: {str(e)}"

    def validate_dataset_file(self, filepath: str) -> Dict:
        """Validate the structure and content of a dataset file."""
        validation = {
            "file_exists": False,
            "is_valid_json": False,
            "has_data": False,
            "structure_valid": False,
            "total_samples": 0,
            "best_selectors": 0,
            "unique_urls": 0,
            "selector_types": set(),
            "errors": []
        }

        try:
            if not os.path.exists(filepath):
                validation["errors"].append(f"File does not exist: {filepath}")
                return validation

            validation["file_exists"] = True

            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            validation["is_valid_json"] = True

            if not isinstance(data, list) or len(data) == 0:
                validation["errors"].append("Dataset is not a non-empty list")
                return validation

            validation["has_data"] = True
            validation["total_samples"] = len(data)

            # Validate structure of first few samples
            required_fields = ["url", "tag", "text", "selector", "selector_type",
                             "features", "score", "rank", "is_best"]

            for i, sample in enumerate(data[:5]):  # Check first 5 samples
                missing_fields = []
                for field in required_fields:
                    if field not in sample:
                        missing_fields.append(field)

                if missing_fields:
                    validation["errors"].append(
                        f"Sample {i} missing fields: {missing_fields}")

                # Validate features structure
                if "features" in sample:
                    features = sample["features"]
                    if not isinstance(features, dict):
                        validation["errors"].append(f"Sample {i}: features is not a dict")
                    else:
                        # Check for key features
                        expected_features = ["match_count", "is_unique", "selector_length"]
                        for feat in expected_features:
                            if feat not in features:
                                validation["errors"].append(f"Sample {i}: missing feature '{feat}'")

                # Collect statistics
                if sample.get("is_best") == 1:
                    validation["best_selectors"] += 1

                validation["selector_types"].add(sample.get("selector_type", "unknown"))

            # Check URL consistency
            urls = set(sample.get("url", "") for sample in data)
            validation["unique_urls"] = len(urls)

            if len(urls) > 1:
                validation["errors"].append(f"Multiple URLs in dataset: {urls}")

            # Validate ranking
            best_samples = [s for s in data if s.get("is_best") == 1]
            if len(best_samples) != len(set(s.get("url", "") for s in data)):
                validation["errors"].append("Number of best selectors doesn't match number of unique URLs")

            validation["structure_valid"] = len(validation["errors"]) == 0

        except json.JSONDecodeError as e:
            validation["errors"].append(f"Invalid JSON: {str(e)}")
        except Exception as e:
            validation["errors"].append(f"Validation error: {str(e)}")

        return validation

    def test_single_url_mode(self, url: str, mode: str, custom_selector: str = None) -> Dict:
        """Test a single URL with a specific mode."""
        print(f"\n[TEST] Testing: {url}")
        print(f"   Mode: {mode}" + (f" (selector: {custom_selector})" if custom_selector else ""))

        # Build command
        cmd = ["py", "generate_dataset.py", url, mode]
        if custom_selector:
            cmd.append(custom_selector)

        # Run command
        exit_code, stdout, stderr = self.run_command(cmd)

        result = {
            "url": url,
            "mode": mode,
            "custom_selector": custom_selector,
            "exit_code": exit_code,
            "stdout": stdout,
            "stderr": stderr,
            "success": exit_code == 0,
            "dataset_file": None,
            "validation": None,
            "duration": None,
            "error_message": None
        }

        if exit_code == 0:
            # Extract dataset filename from stdout
            for line in stdout.split('\n'):
                if "Dataset ready for ML training:" in line:
                    filename = line.split(":")[-1].strip()
                    result["dataset_file"] = filename
                    break

            if result["dataset_file"]:
                result["validation"] = self.validate_dataset_file(result["dataset_file"])
            else:
                result["error_message"] = "Could not find dataset filename in output"
        else:
            # Extract error message
            error_lines = [line for line in stderr.split('\n') + stdout.split('\n')
                          if line.startswith('ERROR:') or 'Error:' in line]
            result["error_message"] = '\n'.join(error_lines) if error_lines else "Unknown error"

        return result

    def run_all_tests(self):
        """Run comprehensive tests for all URLs and modes."""
        print("🚀 Starting Comprehensive Scraper Test Suite")
        print("=" * 60)

        total_tests = len(self.test_urls) * len(self.test_modes)
        completed_tests = 0
        successful_tests = 0

        for url in self.test_urls:
            for mode, custom_selector in self.test_modes:
                result = self.test_single_url_mode(url, mode, custom_selector)
                self.results.append(result)

                completed_tests += 1
                if result["success"]:
                    successful_tests += 1

                # Print result summary
                status = "[PASS]" if result["success"] else "[FAIL]"
                print(f"{status} {completed_tests}/{total_tests} - {url} ({mode})")

                if not result["success"]:
                    print(f"   Error: {result['error_message']}")

                if result["validation"]:
                    val = result["validation"]
                    if val["structure_valid"]:
                        print(f"   [DATA] {val['total_samples']} samples, {val['best_selectors']} best selectors")
                    else:
                        print(f"   [WARN] Validation errors: {len(val['errors'])}")

        # Print final summary
        print("\n" + "=" * 60)
        print("📈 TEST SUMMARY")
        print("=" * 60)
        print(f"Total tests: {total_tests}")
        print(f"Successful: {successful_tests}")
        print(f"Failed: {total_tests - successful_tests}")
        print(".1f")

        # Analyze results
        self.analyze_results()

    def analyze_results(self):
        """Analyze test results and provide insights."""
        print("\n[ANALYSIS]")
        print("-" * 30)

        # Group by URL
        url_stats = {}
        for result in self.results:
            url = result["url"]
            if url not in url_stats:
                url_stats[url] = {"total": 0, "success": 0, "samples": []}
            url_stats[url]["total"] += 1
            if result["success"]:
                url_stats[url]["success"] += 1
            if result["validation"] and result["validation"]["total_samples"] > 0:
                url_stats[url]["samples"].append(result["validation"]["total_samples"])

        print("[BY URL]")
        for url, stats in url_stats.items():
            avg_samples = sum(stats["samples"]) / len(stats["samples"]) if stats["samples"] else 0
            print(".1f")

        # Group by mode
        mode_stats = {}
        for result in self.results:
            mode = result["mode"]
            if mode not in mode_stats:
                mode_stats[mode] = {"total": 0, "success": 0}
            mode_stats[mode]["total"] += 1
            if result["success"]:
                mode_stats[mode]["success"] += 1

        print("\n[BY MODE]")
        for mode, stats in mode_stats.items():
            print(".1f")

        # Check for common errors
        errors = [r for r in self.results if not r["success"]]
        if errors:
            print("\n[ERRORS]")
            error_types = {}
            for error in errors:
                err_msg = error.get("error_message", "Unknown")
                # Simplify error messages
                if "timed out" in err_msg.lower():
                    err_type = "Timeout"
                elif "no elements" in err_msg.lower():
                    err_type = "No elements found"
                elif "invalid" in err_msg.lower():
                    err_type = "Invalid input"
                else:
                    err_type = "Other"
                error_types[err_type] = error_types.get(err_type, 0) + 1

            for err_type, count in error_types.items():
                print(f"   {err_type}: {count} occurrences")

        # Save detailed results
        self.save_results()

    def save_results(self):
        """Save detailed test results to file."""
        output_file = "test_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)

        print(f"\n[SAVE] Detailed results saved to: {output_file}")

        # Also save summary
        summary = {
            "total_tests": len(self.results),
            "successful_tests": len([r for r in self.results if r["success"]]),
            "failed_tests": len([r for r in self.results if not r["success"]]),
            "urls_tested": len(set(r["url"] for r in self.results)),
            "modes_tested": len(set(r["mode"] for r in self.results))
        }

        summary_file = "test_summary.json"
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)

        print(f"[SAVE] Test summary saved to: {summary_file}")

def main():
    """Run the comprehensive test suite."""
    if len(sys.argv) > 1:
        print("Usage: python test_scraper.py")
        print("This script runs comprehensive tests for all URLs and modes.")
        sys.exit(1)

    tester = ScraperTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
