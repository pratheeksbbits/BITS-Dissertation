# Test script to verify error handling
print("="*60)
print("ERROR HANDLING TEST SUITE")
print("="*60)

# Test 1: URL validation
print("\nTest 1: URL Validation")
print("-" * 60)

from scraper_analyzed import validate_url

test_urls = [
    ("https://www.google.com", True),
    ("http://localhost:3000", True),
    ("invalid-url", False),
    ("just text", False),
    ("ftp://example.com", False),
    ("", False),
    ("https://example.com/path?query=value", True),
]

for url, expected_valid in test_urls:
    is_valid, msg = validate_url(url)
    status = "✅" if is_valid == expected_valid else "❌"
    print(f"{status} URL: '{url}' - Valid: {is_valid}")
    if msg and not is_valid:
        print(f"   Error: {msg}")

# Test 2: CSS Selector validation
print("\nTest 2: CSS Selector Validation")
print("-" * 60)

from scraper_analyzed import validate_css_selector

test_selectors = [
    ("button", True),
    ("button.primary", True),
    (".class-name", True),
    ("#id-name", True),
    ("[data-testid='value']", True),
    ("div > span", True),
    ("<script>alert('test')</script>", False),
    ("{malicious}", False),
    ("", False),
]

for selector, expected_valid in test_selectors:
    is_valid, msg = validate_css_selector(selector)
    status = "✅" if is_valid == expected_valid else "❌"
    print(f"{status} Selector: '{selector}' - Valid: {is_valid}")
    if msg and not is_valid:
        print(f"   Error: {msg}")

print("\n" + "="*60)
print("ERROR HANDLING TEST COMPLETE")
print("="*60)
