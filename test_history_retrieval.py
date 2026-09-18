"""
FocusFlow Retrieval & OCR Cleaner Test Suite
============================================
Tests the newly improved whole-word set intersection and stop-words filtering in
KnowledgeBase, as well as math formula protection in OCRCleaner.
"""

import os
import sys
import unittest

# Ensure we import from current directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from knowledge_base import KnowledgeBase, _STOP_WORDS
from ocr_cleaner import OCRCleaner


class TestHistoryRetrieval(unittest.TestCase):
    """Verifies whole-word set intersection search, stop-words filtering, and OCR formula preservation."""

    def test_stop_words_list(self) -> None:
        expected_stops = {"the", "and", "of", "to", "is", "in", "it"}
        missing = expected_stops - _STOP_WORDS
        self.assertFalse(missing, f"Missing expected stop words: {missing}")

    def test_knowledge_base_word_retrieval(self) -> None:
        kb = KnowledgeBase(os.path.abspath(os.path.dirname(__file__)))

        # Standard stop words should be stripped, yielding zero matches
        context_stops = kb.get_context("the and of to is in it")
        self.assertFalse(context_stops.strip(), f"Stop words query returned context: {context_stops}")

        # A query with "he" should NOT match organic chemistry due to substring
        context_substring = kb.get_context("he")
        self.assertNotIn("Organic Chemistry", context_substring, "Substring 'he' matched 'Organic Chemistry'")

        # Real query should yield relevant topic
        context_real = kb.get_context("Bohr radius de Broglie quantum")
        self.assertIn("Atomic Structure", context_real, f"Expected topic 'Atomic Structure' not matched in: {context_real}")

    def test_ocr_cleaner_math_formula_retention(self) -> None:
        cleaner = OCRCleaner()

        # Complex math formula with operators and symbols
        math_formula = "f(x) = (x^2 + 1) / (x - 1)"
        cleaned, quality, warnings = cleaner.clean(math_formula)
        self.assertIn(math_formula, cleaned, f"Mathematical formula was stripped: {cleaned}")
        self.assertIn(quality, ("good", "weak"))

        # Programming expression
        code_expr = "A = [1, 2; 3, 4]"
        cleaned_code, _, _ = cleaner.clean(code_expr)
        self.assertIn(code_expr, cleaned_code, f"Programming statement was stripped: {cleaned_code}")


if __name__ == "__main__":
    unittest.main()

