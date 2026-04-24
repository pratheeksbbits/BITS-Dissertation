#!/usr/bin/env python3
"""
Integrated Playwright Selector Ranking and Dataset Generation Framework
Single entry point for end-to-end workflow: URL + mode → Clean ML Training Dataset

Usage: python integrated_framework.py <URL> [mode] [custom_selector]

Modes:
  interactive - Buttons, inputs, links
  text        - Headings, labels, paragraphs
  all         - Both interactive and text elements
  custom      - Use custom CSS selector (requires custom_selector argument)

Output: cleaned_training_dataset_[timestamp].json (ready for XGBoost training)
"""

import sys
import json
import logging
import re
import math
from datetime import datetime
from collections import Counter
from typing import Dict, List, Optional, Tuple
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Constants
IMPORTANT_TAGS = ["button", "input", "textarea", "select", "a"]
TEXT_CONTENT_TAGS = ["h1", "h2", "h3", "h4", "h5", "h6", "p", "label", "span", "strong", "em", "div"]

MODE_SELECTORS = {
    "interactive": 'button, input, select, textarea, a, [role="button"], [role="link"], [role="textbox"]',
    "text": 'h1, h2, h3, h4, h5, h6, label, p[role="heading"], span[role="heading"], strong, em, div[role="heading"]',
    "all": 'button, input, select, textarea, a, [role="button"], [role="link"], [role="textbox"], h1, h2, h3, h4, h5, h6, label, p, span, strong, em, div[role="article"]'
}

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def calculate_entropy(s: str) -> float:
    """Calculate Shannon entropy of a string."""
    if not s:
        return 0.0
    entropy = 0.0
    for count in Counter(s).values():
        p = count / len(s)
        entropy -= p * math.log2(p)
    return entropy

def has_dynamic_pattern_new(selector: str) -> int:
    """Improved dynamic pattern detection."""
    tokens = re.split(r'[-_]', selector)
    for token in tokens:
        token = token.strip()
        if not token:
            continue
        if re.match(r'^[a-z0-9]{5,}$', token, re.IGNORECASE):
            return 1
        if calculate_entropy(token) > 3.5:
            return 1
        if re.match(r'^default-ltr-.*', token) or re.match(r'^e[0-9a-z]{6,}$', token, re.IGNORECASE):
            return 1
    return 0

def new_label(row) -> int:
    """Compute new label based on improved criteria."""
    features = row['features']
    match_count = features.get('match_count', 0)
    has_dynamic = features.get('has_dynamic_pattern', 0)
    sel_len = features.get('selector_length', 0)
    sel_type = row['selector_type']

    label = 1 if (
        match_count == 1
        and has_dynamic == 0
        and sel_len < 50
        and sel_type not in ['xpath']
    ) else 0

    if sel_type == 'xpath':
        label = 0
    if sel_type == 'class' and has_dynamic == 1:
        label = 0

    return label

def add_new_features(row) -> dict:
    """Add new features to the features dict."""
    features = row['features'].copy()
    selector = row['selector']
    text = row['text']

    features['is_probably_generated_class'] = (
        1 if row['selector_type'] == 'class' and (len(selector) > 10 or bool(re.search(r'\d', selector))) else 0
    )

    tokens = [t for t in re.split(r'[.\s#]', selector) if t]
    features['selector_token_count'] = len(tokens)

    token_lengths = [len(t) for t in tokens]
    features['avg_token_length'] = sum(token_lengths) / len(token_lengths) if token_lengths else 0

    features['has_numeric_token'] = 1 if any(re.search(r'\d', t) for t in tokens) else 0

    features['text_length'] = len(text)
    features['is_text_short'] = 1 if len(text) < 20 else 0
    features['is_xpath_absolute'] = 1 if row['selector_type'] == 'xpath' and selector.startswith('/') else 0

    return features

# =============================================================================
# SCRAPER FUNCTIONS
# =============================================================================

def generate_css_selector(element_handle):
    try:
        return element_handle.evaluate('''el => {
            if (el.id) return '#' + el.id;
            if (el.className) return '.' + el.className.split(' ')[0];
            return el.tagName.toLowerCase();
        }''')
    except:
        return None

def generate_xpath(element_handle):
    try:
        return element_handle.evaluate('''el => {
            let path = [];
            while (el && el.nodeType === 1) {
                let name = el.tagName.toLowerCase();
                let sib = el, pos = 1;
                while (sib = sib.previousElementSibling) {
                    if (sib.tagName.toLowerCase() === name) pos++;
                }
                path.unshift(name + (pos > 1 ? '[' + pos + ']' : ''));
                el = el.parentElement;
            }
            return '/' + path.join('/');
        }''')
    except:
        return None

def get_role_based_locator(element_handle):
    try:
        role = element_handle.get_attribute('role') or ''
        name = element_handle.get_attribute('aria-label') or element_handle.inner_text().strip()[:50] or ''
        if role and name:
            return f"getByRole('{role}', {{ name: '{name}' }})"
        return None
    except:
        return None

def get_test_id_locator(element_handle):
    test_id = element_handle.get_attribute('data-testid') or element_handle.get_attribute('data-test') or ''
    if test_id:
        return f"getByTestId('{test_id}')"
    return None

def get_text_based_locator(element_handle):
    try:
        text = element_handle.inner_text(timeout=2000).strip()[:50]
        if text:
            return f"getByText('{text}')"
    except:
        pass
    return None

def extract_elements(url, mode="all", custom_selector=None):
    """Extract elements from a webpage."""
    if custom_selector:
        selector = custom_selector
    elif mode not in MODE_SELECTORS:
        raise ValueError(f"Invalid mode. Choose from: {', '.join(MODE_SELECTORS.keys())}")
    else:
        selector = MODE_SELECTORS[mode]

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(3000)
            except PlaywrightTimeoutError:
                raise ValueError("Page load timeout. The website took too long to load.")
            except Exception as e:
                raise ValueError(f"Failed to navigate to {url}: {e}")

            try:
                elements = page.eval_on_selector_all(selector, '''els => {
                    return Array.from(els).map(el => ({
                        tag: el.tagName.toLowerCase(),
                        text: (el.innerText || el.value || el.alt || '').trim().slice(0, 50),
                        attributes: Object.fromEntries(Array.from(el.attributes).map(a => [a.name, a.value])),
                    }));
                }''')
            except Exception as e:
                raise ValueError(f"Invalid CSS selector or selector not found: {selector}")

            elements_data = []
            for idx, elem in enumerate(elements):
                try:
                    handles = page.query_selector_all(selector)
                    if idx >= len(handles):
                        continue
                    handle = handles[idx]

                    selectors = {}
                    selectors['css'] = generate_css_selector(handle)
                    selectors['xpath'] = generate_xpath(handle)
                    selectors['role_based'] = get_role_based_locator(handle)
                    selectors['test_id'] = get_test_id_locator(handle)
                    selectors['text_based'] = get_text_based_locator(handle)

                    attrs = elem['attributes']
                    if attrs.get("data-testid"):
                        selectors["data-testid"] = f'[data-testid="{attrs["data-testid"]}"]'
                    if attrs.get("id"):
                        selectors["id"] = f'#{attrs["id"]}'
                    if attrs.get("name"):
                        selectors["name"] = f'[name="{attrs["name"]}"]'
                    if attrs.get("aria-label"):
                        selectors["aria-label"] = f'[aria-label="{attrs["aria-label"]}"]'
                    if attrs.get("placeholder"):
                        selectors["placeholder"] = f'[placeholder="{attrs["placeholder"]}"]'
                    text = elem['text']
                    if text:
                        selectors["text"] = f'text="{text}"'
                    if attrs.get("class"):
                        class_selector = "." + ".".join(attrs["class"].split())
                        selectors["class"] = class_selector

                    element_data = {
                        'tag': elem['tag'],
                        'text': elem['text'],
                        'attributes': elem['attributes'],
                        'selectors': selectors
                    }
                    elements_data.append(element_data)

                except Exception as e:
                    logging.warning(f"Error processing element {idx}: {e}")
                    continue

            browser.close()
            return elements_data

    except Exception as e:
        raise ValueError(f"Critical error during extraction: {e}")

# =============================================================================
# RANKING ENGINE FUNCTIONS
# =============================================================================

class SelectorFeatureExtractor:
    def __init__(self, page):
        self.page = page

    def extract_features(self, selector: str, selector_type: str, element_attrs: Dict, xpath: Optional[str] = None) -> Dict:
        features = {}
        playwright_selector = self._prepare_selector_for_playwright(selector, selector_type)

        try:
            count = self.page.locator(playwright_selector).count()
            features['match_count'] = count
            features['is_unique'] = 1 if count == 1 else 0
        except Exception as e:
            logging.warning(f"Error validating selector '{selector}': {e}")
            features['match_count'] = 0
            features['is_unique'] = 0

        features['selector_length'] = len(selector)
        selector_types = ["css", "xpath", "id", "name", "data-testid", "aria-label", "text", "class"]
        for t in selector_types:
            features[f'is_{t}'] = 1 if selector_type == t else 0

        features['has_dynamic_pattern'] = has_dynamic_pattern_new(selector)
        features['has_unstable_attr'] = self._has_unstable_attr(selector)
        features['dom_depth'] = self._get_dom_depth(xpath) if xpath else 0
        features['sibling_count'] = self._get_sibling_count(xpath) if xpath else 0
        features['attribute_count'] = len(element_attrs)

        return features

    def _prepare_selector_for_playwright(self, selector: str, selector_type: str) -> str:
        if selector_type == "xpath":
            return f"xpath={selector}"
        return selector

    def _has_unstable_attr(self, selector: str) -> int:
        unstable_attrs = ['style', 'onclick', 'onload', 'onerror', 'javascript', 'onmouseover', 'onmouseout']
        for attr in unstable_attrs:
            if attr in selector.lower():
                return 1
        return 0

    def _get_dom_depth(self, xpath: str) -> int:
        if not xpath:
            return 0
        return max(0, xpath.count('/') - 1)

    def _get_sibling_count(self, xpath: str) -> int:
        if not xpath:
            return 0
        match = re.search(r'\[(\d+)\]$', xpath)
        if match:
            position = int(match.group(1))
            return max(0, position - 1)
        return 0

class SelectorScorer:
    SELECTOR_TYPE_SCORES = {
        "data-testid": 1.0, "id": 0.9, "name": 0.8, "aria-label": 0.7,
        "css": 0.6, "text": 0.5, "xpath": 0.3, "class": 0.2
    }

    def score_selector(self, features: Dict, selector_type: str) -> float:
        if features['match_count'] == 0:
            return -100.0

        score = 0.0
        score += 50 * features['is_unique']
        score += 30 * self.SELECTOR_TYPE_SCORES.get(selector_type, 0.0)
        length_penalty = features['selector_length'] // 10
        score -= 10 * length_penalty
        score -= 20 * features['has_dynamic_pattern']
        score -= 15 * features['has_unstable_attr']

        if features['match_count'] > 1:
            score -= 40

        return score

class SelectorRanker:
    def rank_selectors(self, selector_data: List[Dict]) -> List[Dict]:
        ranked = sorted(selector_data, key=lambda x: x['score'], reverse=True)
        for i, item in enumerate(ranked, 1):
            item['rank'] = i
            item['is_best'] = 1 if i == 1 else 0
        return ranked

class DatasetBuilder:
    def build_dataset(self, url: str, ranked_elements: List[Dict]) -> List[Dict]:
        dataset = []
        for element in ranked_elements:
            for sel_data in element['ranked_selectors']:
                row = {
                    "url": url,
                    "tag": element['tag'],
                    "text": element['text'],
                    "selector": sel_data['selector'],
                    "selector_type": sel_data['selector_type'],
                    "features": sel_data['features'],
                    "score": sel_data['score'],
                    "rank": sel_data['rank'],
                    "is_best": sel_data['is_best']
                }
                dataset.append(row)
        return dataset

def rank_selectors_for_elements(url: str, elements: List[Dict]) -> List[Dict]:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        try:
            page.goto(url, wait_until="networkidle", timeout=30000)
        except Exception as e:
            logging.error(f"Failed to load {url}: {e}")
            browser.close()
            return []

        extractor = SelectorFeatureExtractor(page)
        scorer = SelectorScorer()
        ranker = SelectorRanker()

        ranked_elements = []

        for element in elements:
            selector_data = []
            xpath = element['selectors'].get('xpath')

            for sel_type, selector in element['selectors'].items():
                if not selector or not selector.strip():
                    continue

                features = extractor.extract_features(selector, sel_type, element['attributes'], xpath)
                score = scorer.score_selector(features, sel_type)

                selector_data.append({
                    'selector': selector,
                    'selector_type': sel_type,
                    'features': features,
                    'score': score
                })

            if selector_data:
                ranked = ranker.rank_selectors(selector_data)
                element_copy = element.copy()
                element_copy['ranked_selectors'] = ranked
                ranked_elements.append(element_copy)

        browser.close()
        return ranked_elements

# =============================================================================
# DATA CLEANING FUNCTIONS
# =============================================================================

def clean_dataset(data: List[Dict]) -> List[Dict]:
    """Clean and transform the dataset."""
    import pandas as pd

    df = pd.DataFrame(data)

    # Step 1: Fix has_dynamic_pattern
    df['features'] = df.apply(
        lambda row: {**row['features'], 'has_dynamic_pattern': has_dynamic_pattern_new(row['selector'])},
        axis=1
    )

    # Step 2: Remove invalid data
    df = df[~((df['features'].apply(lambda x: x.get('match_count', 0) == 0) & (df['selector_type'] != 'text')))]
    df = df[~df['selector'].str.contains(r'#.*:.*:')]
    df = df[df['selector'].str.strip() != '']
    df = df.drop_duplicates(subset=['selector', 'url', 'tag', 'text'])

    # Step 3: Fix label
    df['label'] = df.apply(new_label, axis=1)

    # Step 4: Normalize text
    df['text'] = df['text'].str.replace(r'\n', ' ', regex=True).str.replace(r'\s+', ' ', regex=True).str.strip()
    text_mask = df['selector_type'] == 'text'
    df.loc[text_mask, 'selector'] = 'text="' + df.loc[text_mask, 'text'] + '"'

    # Step 5: Add new features
    df['features'] = df.apply(add_new_features, axis=1)

    # Step 6: Remove low-signal data
    df = df[~((df['text'] == '') & (df['selector_type'] == 'text'))]
    df = df[df['features'].apply(lambda x: x.get('match_count', 0) <= 5)]
    df = df[df['features'].apply(lambda x: x.get('selector_length', 0) <= 100)]

    # Step 7: Balance dataset
    pos = df[df['label'] == 1]
    neg = df[df['label'] == 0]

    if len(neg) > len(pos):
        neg_balanced = neg.sample(len(pos), random_state=42)
        df = pd.concat([pos, neg_balanced])
    elif len(pos) > len(neg):
        pos_balanced = pos.sample(len(neg), random_state=42)
        df = pd.concat([pos_balanced, neg])

    # Step 8: Final output
    return df[['selector', 'selector_type', 'features', 'label']].to_dict('records')

# =============================================================================
# MAIN WORKFLOW
# =============================================================================

def generate_clean_dataset(url: str, mode: str = "all", custom_selector: str = None) -> str:
    """Generate clean ML training dataset from URL input."""
    print(f"[TARGET] Starting integrated workflow for: {url}")
    print(f"[MODE] Mode: {mode}")

    # Step 1: Extract elements
    print("\n[1/6] Extracting elements from webpage...")
    elements = extract_elements(url, mode=mode, custom_selector=custom_selector)
    if not elements:
        raise ValueError("No elements could be extracted from the URL")
    print(f"   [OK] Extracted {len(elements)} elements")

    # Step 2: Rank selectors
    print("\n[2/6] Ranking selectors with advanced scoring engine...")
    ranked_elements = rank_selectors_for_elements(url, elements)
    if not ranked_elements:
        raise ValueError("Failed to rank selectors")
    print(f"   [OK] Ranked selectors for {len(ranked_elements)} elements")

    # Step 3: Build initial dataset
    print("\n[3/6] Building initial training dataset...")
    builder = DatasetBuilder()
    dataset = builder.build_dataset(url, ranked_elements)
    if not dataset:
        raise ValueError("Failed to build training dataset")
    print(f"   [OK] Generated {len(dataset)} training samples")

    # Step 4: Clean dataset
    print("\n[4/6] Cleaning and transforming dataset...")
    cleaned_dataset = clean_dataset(dataset)
    print(f"   [OK] Cleaned to {len(cleaned_dataset)} high-quality samples")

    # Step 5: Save cleaned dataset
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"cleaned_training_dataset_{timestamp}.json"

    print(f"\n[5/6] Saving cleaned dataset to: {filename}")
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(cleaned_dataset, f, indent=2, ensure_ascii=False)

    # Step 6: Show summary
    labels = [row['label'] for row in cleaned_dataset]
    pos_count = sum(labels)
    neg_count = len(labels) - pos_count

    print("\n[6/6] Final Dataset Summary:")
    print(f"   • Total training samples: {len(cleaned_dataset)}")
    print(f"   • Positive labels (stable selectors): {pos_count}")
    print(f"   • Negative labels (unstable selectors): {neg_count}")
    print(f"   • Balanced ratio: {pos_count}/{neg_count}")

    selector_types = {}
    for row in cleaned_dataset:
        st = row['selector_type']
        selector_types[st] = selector_types.get(st, 0) + 1
    print(f"   • Selector types: {selector_types}")

    print(f"\n[SUCCESS] Clean dataset ready for XGBoost training: {filename}")
    return filename

def main():
    """Command line interface."""
    if len(sys.argv) < 2:
        print("ERROR: Missing required URL argument")
        print("\nUsage: python integrated_framework.py <URL> [mode] [custom_selector]")
        print("\nModes:")
        print("  interactive - Buttons, inputs, links")
        print("  text        - Headings, labels, paragraphs")
        print("  all         - Both interactive and text elements")
        print("  custom      - Use custom CSS selector (requires custom_selector argument)")
        print("\nExamples:")
        print("  python integrated_framework.py https://example.com")
        print("  python integrated_framework.py https://example.com text")
        print("  python integrated_framework.py https://example.com custom .my-class")
        sys.exit(1)

    url = sys.argv[1]

    if not url.startswith(('http://', 'https://')):
        print("ERROR: URL must start with http:// or https://")
        sys.exit(1)

    mode = sys.argv[2] if len(sys.argv) > 2 else "all"
    valid_modes = ["interactive", "text", "all", "custom"]

    if mode not in valid_modes:
        print(f"ERROR: Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}")
        sys.exit(1)

    custom_selector = None
    if mode == "custom":
        if len(sys.argv) < 4:
            print("ERROR: Custom mode requires a CSS selector as the third argument")
            print("Example: python integrated_framework.py https://example.com custom .my-class")
            sys.exit(1)
        custom_selector = sys.argv[3]
        dangerous_patterns = ['<', 'javascript:', 'onerror=', 'onclick=', 'onload=']
        for pattern in dangerous_patterns:
            if pattern in custom_selector.lower():
                print(f"ERROR: Custom selector contains potentially dangerous pattern: '{pattern}'")
                sys.exit(1)

    try:
        dataset_file = generate_clean_dataset(url, mode, custom_selector)
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