"""
Selector Ranking Engine Module
Handles feature extraction, scoring, ranking, and dataset building.
"""

import logging
from typing import Dict, List, Optional
from playwright.sync_api import sync_playwright
from urllib.parse import urlparse

class SelectorFeatureExtractor:
    """Extracts features for selector validation."""

    def __init__(self, page):
        self.page = page

    def extract_features(self, selector: str, selector_type: str, element_attrs: Dict, xpath: Optional[str] = None) -> Dict:
        """Extract comprehensive features for a selector."""
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

    def _prepare_selector_for_playwright(self, selector: str, selector_type: str) -> str:
        if selector_type == "xpath":
            return f"xpath={selector}"
        return selector

    def _has_dynamic_pattern(self, selector: str) -> int:
        unstable_attrs = ['style', 'onclick', 'onload', 'onerror', 'javascript', 'onmouseover', 'onmouseout']
        for attr in unstable_attrs:
            if attr in selector.lower():
                return 1
        return 0

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
        import re
        match = re.search(r'\[(\d+)\]$', xpath)
        if match:
            position = int(match.group(1))
            return max(0, position - 1)
        return 0

class SelectorScorer:
    """Scores selectors based on features."""

    SELECTOR_TYPE_SCORES = {
        "data-testid": 1.0, "id": 0.9, "name": 0.8, "aria-label": 0.7,
        "css": 0.6, "text": 0.5, "xpath": 0.3, "class": 0.2
    }

    def score_selector(self, features: Dict, selector_type: str) -> float:
        """Calculate score for a selector."""
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
    """Ranks selectors by score."""

    def rank_selectors(self, selector_data: List[Dict]) -> List[Dict]:
        """Rank selectors by score (descending)."""
        ranked = sorted(selector_data, key=lambda x: x['score'], reverse=True)
        for i, item in enumerate(ranked, 1):
            item['rank'] = i
            item['is_best'] = 1 if i == 1 else 0
        return ranked

class DatasetBuilder:
    """Builds training-ready dataset."""

    def build_dataset(self, url: str, ranked_elements: List[Dict]) -> List[Dict]:
        """Transform ranked elements into dataset rows."""
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
    """
    Main function to rank selectors for all elements on a page.

    Args:
        url: Target URL
        elements: List of element dicts from DOM extraction

    Returns:
        Elements with ranked_selectors added
    """
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