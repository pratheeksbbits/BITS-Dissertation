"""
Test suite for the ranking engine module.
"""

import unittest
from unittest.mock import MagicMock
from src.ranking_engine import SelectorScorer, SelectorRanker

class TestRankingEngine(unittest.TestCase):

    def setUp(self):
        self.scorer = SelectorScorer()
        self.ranker = SelectorRanker()

    def test_selector_scorer_unique_id(self):
        """Test scoring of unique ID selector."""
        features = {
            'match_count': 1,
            'is_unique': 1,
            'selector_length': 5,
            'has_dynamic_pattern': 0,
            'has_unstable_attr': 0
        }
        score = self.scorer.score_selector(features, 'id')
        self.assertGreater(score, 0)

    def test_selector_scorer_no_matches(self):
        """Test scoring when no elements match."""
        features = {
            'match_count': 0,
            'is_unique': 0,
            'selector_length': 10,
            'has_dynamic_pattern': 0,
            'has_unstable_attr': 0
        }
        score = self.scorer.score_selector(features, 'css')
        self.assertEqual(score, -100.0)

    def test_selector_ranker(self):
        """Test selector ranking."""
        selector_data = [
            {'selector': 'sel1', 'score': 10.0},
            {'selector': 'sel2', 'score': 20.0},
            {'selector': 'sel3', 'score': 5.0}
        ]

        ranked = self.ranker.rank_selectors(selector_data)

        # Check ranking order (highest score first)
        self.assertEqual(ranked[0]['selector'], 'sel2')
        self.assertEqual(ranked[0]['rank'], 1)
        self.assertEqual(ranked[0]['is_best'], 1)

        self.assertEqual(ranked[1]['selector'], 'sel1')
        self.assertEqual(ranked[1]['rank'], 2)
        self.assertEqual(ranked[1]['is_best'], 0)

if __name__ == '__main__':
    unittest.main()