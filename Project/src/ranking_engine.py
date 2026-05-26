import logging
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse

class SelectorFeatureExtractor:

    # Initializes the feature extractor with a page
    def __init__(self, page):
        self.page = page

    # Extracts features for a selector to assess its stability
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

        features['has_dynamic_pattern'] = self._has_dynamic_pattern(selector)
        features['has_unstable_attr'] = self._has_unstable_attr(selector)
        features['dom_depth'] = self._get_dom_depth(xpath) if xpath else 0
        features['sibling_count'] = self._get_sibling_count(xpath) if xpath else 0
        features['attribute_count'] = len(element_attrs)

        return features

    # Prepares a selector for Playwright locator
    def _prepare_selector_for_playwright(self, selector: str, selector_type: str) -> str:
        if selector_type == "xpath":
            return f"xpath={selector}"
        return selector

    # Checks if selector has dynamic patterns that make it unstable
    def _has_dynamic_pattern(self, selector: str) -> int:
        unstable_attrs = ['style', 'onclick', 'onload', 'onerror', 'javascript', 'onmouseover', 'onmouseout']
        for attr in unstable_attrs:
            if attr in selector.lower():
                return 1
        return 0

    # Checks if selector uses unstable attributes
    def _has_unstable_attr(self, selector: str) -> int:
        unstable_attrs = ['style', 'onclick', 'onload', 'onerror', 'javascript', 'onmouseover', 'onmouseout']
        for attr in unstable_attrs:
            if attr in selector.lower():
                return 1
        return 0

    # Calculates the DOM depth from XPath
    def _get_dom_depth(self, xpath: str) -> int:
        if not xpath:
            return 0
        return max(0, xpath.count('/') - 1)

    # Gets the sibling count from XPath position
    def _get_sibling_count(self, xpath: str) -> int:
        if not xpath:
            return 0
        import re
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

    # Calculates a stability score for a selector based on its features
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

    # Ranks selectors by their stability score in descending order
    def rank_selectors(self, selector_data: List[Dict]) -> List[Dict]:
        ranked = sorted(selector_data, key=lambda x: x['score'], reverse=True)
        for i, item in enumerate(ranked, 1):
            item['rank'] = i
            item['is_best'] = 1 if i == 1 else 0
        return ranked

class DatasetBuilder:

    # Builds a dataset from ranked elements for ML training
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

# Ranks selectors for all elements on a webpage
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

        ranked_elements = rank_selectors_for_elements_on_page(page, elements)

        browser.close()
        return ranked_elements


# Ranks selectors for all elements using an existing Playwright page context
def rank_selectors_for_elements_on_page(page, elements: List[Dict]) -> List[Dict]:
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

    return ranked_elements