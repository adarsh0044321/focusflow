"""
FocusFlow Retrieval & OCR Cleaner Test Suite
============================================
Tests the newly improved whole-word set intersection and stop-words filtering in
KnowledgeBase, as well as math formula protection in OCRCleaner.
"""

import os
import sys

# Ensure we import from current directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from knowledge_base import KnowledgeBase, _STOP_WORDS
from ocr_cleaner import OCRCleaner

def run_tests():
    print("=== Running FocusFlow Verification Tests ===")
    
    # ----------------------------------------------------------------------
    # Test 1: Stop words filter list verification
    # ----------------------------------------------------------------------
    print("\n[Test 1] Verifying Stop Words List...")
    expected_stops = {"the", "and", "of", "to", "is", "in", "it"}
    missing = expected_stops - _STOP_WORDS
    if missing:
        print(f"FAIL: Missing expected stop words: {missing}")
        return False
    print("PASS: Stop words list contains standard English particles.")

    # ----------------------------------------------------------------------
    # Test 2: Knowledge Base word-based retrieval vs substring matching
    # ----------------------------------------------------------------------
    print("\n[Test 2] Verifying KnowledgeBase set-intersection search...")
    kb = KnowledgeBase(os.path.abspath(os.path.dirname(__file__)))
    
    # Let's verify that querying a common substring like "he" (from "chemistry" / "helium")
    # or stop word "the" does NOT retrieve false positives if they are not exact keywords.
    # Standard stop words should be stripped.
    context_stops = kb.get_context("the and of to is in it")
    if context_stops.strip():
        print(f"FAIL: Stop words query returned context:\n{context_stops}")
        return False
    print("PASS: Pure stop-words queries correctly yield zero matches.")

    # A query with "he" should NOT match organic chemistry just because of substring "chemistry"
    # unless "he" is in the document as a word (like helium).
    context_substring = kb.get_context("he")
    # Verify organic chemistry is not matched just because of substring
    if "Organic Chemistry" in context_substring:
        print("FAIL: Substring 'he' matched 'Organic Chemistry' topic.")
        return False
    print("PASS: Whole-word set intersection prevents substring containment matches (e.g. 'he' inside 'chemistry').")

    # Verify that a real query yields the correct page
    context_real = kb.get_context("Bohr radius de Broglie quantum")
    if "Atomic Structure" not in context_real:
        print(f"FAIL: Expected topic 'Atomic Structure' not matched. Context found:\n{context_real}")
        return False
    print("PASS: Relevant search terms correctly retrieve matching knowledge sheets.")

    # ----------------------------------------------------------------------
    # Test 3: OCR Cleaner math formula retention
    # ----------------------------------------------------------------------
    print("\n[Test 3] Verifying OCRCleaner math formula retention...")
    cleaner = OCRCleaner()
    
    # This formula has lots of parentheses, equals, division and spaces.
    # Original cleaner (alnum count = 7 / len 17 non-ws = 41% alnum ratio) would wipe it out.
    math_formula = "f(x) = (x^2 + 1) / (x - 1)"
    
    cleaned, quality, warnings = cleaner.clean(math_formula)
    
    if math_formula not in cleaned:
        print(f"FAIL: Mathematical formula was stripped out by OCR cleaner! Cleaned output: '{cleaned}'")
        return False
        
    print(f"PASS: OCR cleaner successfully preserved math formula: '{cleaned}'")
    print(f"      OCR quality score: {quality}")
    
    # Test a programming expression
    code_expr = "A = [1, 2; 3, 4]"
    cleaned_code, _, _ = cleaner.clean(code_expr)
    if code_expr not in cleaned_code:
        print(f"FAIL: Programming statement was stripped out! Cleaned output: '{cleaned_code}'")
        return False
    print(f"PASS: OCR cleaner successfully preserved programming statement: '{cleaned_code}'")

    print("\n=== All Tests Passed Successfully! ===")
    return True

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
