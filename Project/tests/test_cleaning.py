"""
Test suite for the data cleaner module.
"""

import unittest
from src.data_cleaner import has_dynamic_pattern_new, new_label, calculate_entropy

class TestDataCleaner(unittest.TestCase):

    def test_calculate_entropy(self):
        """Test entropy calculation."""
        # Uniform distribution should have high entropy
        entropy = calculate_entropy("abcd")
        self.assertGreater(entropy, 1.0)

        # Single character should have zero entropy
        entropy = calculate_entropy("aaaa")
        self.assertEqual(entropy, 0.0)

    def test_has_dynamic_pattern_new(self):
        """Test dynamic pattern detection."""
        # Should detect long alphanumeric strings
        self.assertEqual(has_dynamic_pattern_new("abc123def"), 1)

        # Should detect CSS-in-JS patterns
        self.assertEqual(has_dynamic_pattern_new("default-ltr-cache-123"), 1)

        # Should not flag normal selectors
        self.assertEqual(has_dynamic_pattern_new("button"), 0)
        self.assertEqual(has_dynamic_pattern_new("#my-id"), 0)

    def test_new_label_logic(self):
        """Test label assignment logic."""
        # Good selector: unique, no dynamic pattern, short length, not xpath
        good_row = {
            'features': {
                'match_count': 1,
                'has_dynamic_pattern': 0,
                'selector_length': 10
            },
            'selector_type': 'id'
        }
        self.assertEqual(new_label(good_row), 1)

        # Bad selector: xpath
        xpath_row = {
            'features': {
                'match_count': 1,
                'has_dynamic_pattern': 0,
                'selector_length': 10
            },
            'selector_type': 'xpath'
        }
        self.assertEqual(new_label(xpath_row), 0)

        # Bad selector: multiple matches
        multi_row = {
            'features': {
                'match_count': 2,
                'has_dynamic_pattern': 0,
                'selector_length': 10
            },
            'selector_type': 'css'
        }
        self.assertEqual(new_label(multi_row), 0)

if __name__ == '__main__':
    unittest.main()