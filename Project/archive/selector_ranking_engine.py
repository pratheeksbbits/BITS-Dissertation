import json
import logging
import re
from typing import Dict, List, Optional, Tuple
from playwright.sync_api import sync_playwright, Page, Browser, Playwright
from urllib.parse import urlparse

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class SelectorFeatureExtractor:
    """
    Extracts features for a given selector using Playwright page validation.
    """

    def __init__(self, page: Page):
        self.page = page

    def extract_features(self, selector: str, selector_type: str, element_attrs: Dict, xpath: Optional[str] = None) -> Dict:
        """
        Extract comprehensive features for a selector.

        Args:
            selector: The selector string
            selector_type: Type of selector (css, xpath, id, etc.)
            element_attrs: Element attributes dict
            xpath: XPath string for DOM depth calculation

        Returns:
            Dict of features
        """
        features = {}

        # Prepare selector for Playwright validation
        playwright_selector = self._prepare_selector_for_playwright(selector, selector_type)

        # Core Features
        try:
            count = self.page.locator(playwright_selector).count()
            features['match_count'] = count
            features['is_unique'] = 1 if count == 1 else 0
        except Exception as e:
            logging.warning(f"Error validating selector '{selector}' (type: {selector_type}): {e}")
            features['match_count'] = 0
            features['is_unique'] = 0

        features['selector_length'] = len(selector)

        # Selector Type Features (one-hot encoding)
        selector_types = ["css", "xpath", "id", "name", "data-testid", "aria-label", "text", "class"]
        for t in selector_types:
            features[f'is_{t}'] = 1 if selector_type == t else 0

        # Stability Features
        features['has_dynamic_pattern'] = self._has_dynamic_pattern(selector)
        features['has_unstable_attr'] = self._has_unstable_attr(selector)

        # DOM Features
        features['dom_depth'] = self._get_dom_depth(xpath) if xpath else 0
        features['sibling_count'] = self._get_sibling_count(xpath) if xpath else 0
        features['attribute_count'] = len(element_attrs)

        return features

    def _prepare_selector_for_playwright(self, selector: str, selector_type: str) -> str:
        """
        Prepare selector string for Playwright locator based on type.
        """
        if selector_type == "xpath":
            return f"xpath={selector}"
        # For other types (css, id, class, etc.), use as-is
        # text selectors are already in "text=\"...\"" format
        return selector

    def _has_dynamic_pattern(self, selector: str) -> int:
        """
        Detect dynamic patterns: random strings, numbers > 3 digits, hashes.
        """
        # Numbers with 4+ digits
        if re.search(r'\d{4,}', selector):
            return 1
        # Hex hashes (6+ chars)
        if re.search(r'[a-fA-F0-9]{6,}', selector):
            return 1
        # Mixed alphanumeric strings that look random (heuristic)
        if re.search(r'\b[a-zA-Z0-9]{8,}\b', selector) and re.search(r'[a-z]', selector) and re.search(r'[0-9]', selector):
            return 1
        return 0

    def _has_unstable_attr(self, selector: str) -> int:
        """
        Detect unstable attributes in selector.
        """
        unstable_attrs = ['style', 'onclick', 'onload', 'onerror', 'javascript', 'onmouseover', 'onmouseout']
        for attr in unstable_attrs:
            if attr in selector.lower():
                return 1
        return 0

    def _get_dom_depth(self, xpath: str) -> int:
        """
        Calculate DOM depth from XPath.
        """
        if not xpath:
            return 0
        # Count path segments (subtract 1 for leading /)
        return max(0, xpath.count('/') - 1)

    def _get_sibling_count(self, xpath: str) -> int:
        """
        Approximate sibling count from XPath position.
        """
        if not xpath:
            return 0
        # Look for [n] at the end
        match = re.search(r'\[(\d+)\]$', xpath)
        if match:
            position = int(match.group(1))
            return max(0, position - 1)  # siblings before this element
        return 0


class SelectorScorer:
    """
    Scores selectors based on features using deterministic rules.
    """

    SELECTOR_TYPE_SCORES = {
        "data-testid": 1.0,
        "id": 0.9,
        "name": 0.8,
        "aria-label": 0.7,
        "css": 0.6,
        "text": 0.5,
        "xpath": 0.3,
        "class": 0.2
    }

    def score_selector(self, features: Dict, selector_type: str) -> float:
        """
        Calculate score for a selector based on features.

        Args:
            features: Dict of features
            selector_type: Type of selector

        Returns:
            Score as float
        """
        if features['match_count'] == 0:
            return -100.0

        score = 0.0
        score += 50 * features['is_unique']
        score += 30 * self.SELECTOR_TYPE_SCORES.get(selector_type, 0.0)

        # Length penalty: -1 per 10 characters
        length_penalty = features['selector_length'] // 10
        score -= 10 * length_penalty

        score -= 20 * features['has_dynamic_pattern']
        score -= 15 * features['has_unstable_attr']

        if features['match_count'] > 1:
            score -= 40

        return score


class SelectorRanker:
    """
    Ranks selectors by score within an element.
    """

    def rank_selectors(self, selector_data: List[Dict]) -> List[Dict]:
        """
        Rank selectors by score (descending).

        Args:
            selector_data: List of dicts with selector info

        Returns:
            Ranked list with rank and is_best added
        """
        # Sort by score descending
        ranked = sorted(selector_data, key=lambda x: x['score'], reverse=True)

        for i, item in enumerate(ranked, 1):
            item['rank'] = i
            item['is_best'] = 1 if i == 1 else 0

        return ranked


class DatasetBuilder:
    """
    Builds training-ready dataset from ranked selector data.
    """

    def build_dataset(self, url: str, ranked_elements: List[Dict]) -> List[Dict]:
        """
        Transform ranked elements into flattened dataset rows.

        Args:
            url: The source URL
            ranked_elements: Elements with ranked_selectors

        Returns:
            List of dataset rows
        """
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
            logging.info(f"Loading page: {url}")
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
            xpath = element['selectors'].get('xpath')  # For DOM features

            for sel_type, selector in element['selectors'].items():
                # Skip empty selectors
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

            if selector_data:  # Only rank if we have selectors
                ranked = ranker.rank_selectors(selector_data)
                element_copy = element.copy()
                element_copy['ranked_selectors'] = ranked
                ranked_elements.append(element_copy)

        browser.close()
        logging.info(f"Processed {len(ranked_elements)} elements")
        return ranked_elements


# Example usage
if __name__ == "__main__":
    # Load sample data
    try:
        with open('selectors_www_wikipedia_com_text_20260424_040950.json', 'r', encoding='utf-8') as f:
            elements = json.load(f)
    except FileNotFoundError:
        logging.error("Sample data file not found. Please provide the JSON file.")
        exit(1)

    # Extract URL from filename or set manually
    url = "https://www.wikipedia.com"

    # Rank selectors
    ranked_elements = rank_selectors_for_elements(url, elements)

    if not ranked_elements:
        logging.error("No elements were processed successfully.")
        exit(1)

    # Build dataset
    builder = DatasetBuilder()
    dataset = builder.build_dataset(url, ranked_elements)

    # Print best selector for first element
    first_element = ranked_elements[0]
    best_selector = first_element['ranked_selectors'][0]
    print(f"\nBest selector for first element:")
    print(f"  Tag: {first_element['tag']}")
    print(f"  Text: {first_element['text']}")
    print(f"  Selector: {best_selector['selector']}")
    print(f"  Type: {best_selector['selector_type']}")
    print(f"  Score: {best_selector['score']}")
    print(f"  Features: {best_selector['features']}")

    # Save dataset
    output_file = 'training_dataset.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"\nDataset saved to {output_file} with {len(dataset)} rows")