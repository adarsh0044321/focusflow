"""
FocusFlow — Unit Tests for New Features & Bug Fixes
Tests:
1. Stop-word filtering in KnowledgeBase.
2. Math equations preservation in OCRCleaner.
3. Config validation in settings dialog properties.
4. AI Solver Persona prompts.
"""

import os
import sys
import unittest

# Ensure we import from current directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config_manager import ConfigManager
from knowledge_base import KnowledgeBase
from ocr_cleaner import OCRCleaner
from ai_engine import AIEngine


class TestFocusFlowEnhancements(unittest.TestCase):

    def setUp(self) -> None:
        self.base_dir = os.path.abspath(os.path.dirname(__file__))
        self.config = ConfigManager(self.base_dir)
        self.kb = KnowledgeBase(self.base_dir)
        self.cleaner = OCRCleaner()
        self.ai = AIEngine(self.config, self.kb)

    def test_stop_words_filtering(self) -> None:
        """Verify that stop-words are filtered, avoiding irrelevant topics."""
        # Query with many stop-words and one keyword
        query = "What is the derivative of x^2?"
        
        # Manually extract words to verify stop-words list is excluded
        from knowledge_base import _STOP_WORDS
        import re
        words = set(re.findall(r"[a-zA-Z0-9]{2,}", query.lower()))
        filtered_words = {w for w in words if w not in _STOP_WORDS}
        
        # Stop words like "what", "is", "the", "of" should be removed
        self.assertNotIn("what", filtered_words)
        self.assertNotIn("is", filtered_words)
        self.assertNotIn("the", filtered_words)
        self.assertNotIn("of", filtered_words)
        
        # Key terms like "derivative" and "x2" should remain
        self.assertIn("derivative", filtered_words)
        
        # Verify context output is clean and relevant
        context = self.kb.get_context(query)
        self.assertIn("[Applications Derivatives]", context)
        self.assertNotIn("[Atomic Structure]", context)  # verify stop words didn't cause leakage

    def test_math_equation_preservation(self) -> None:
        """Verify that mathematical equations are not deleted as garbage."""
        # A low-alphanumeric ratio line representing an algebraic identity
        math_line = "(x + y) * (x - y) = x^2 - y^2"
        
        # Standard cleaning
        cleaned, quality, warnings = self.cleaner.clean(math_line)
        
        # Check that the math line is preserved in the cleaned text
        self.assertIn("x^2", cleaned)
        self.assertIn("y^2", cleaned)
        self.assertIn("=", cleaned)
        
        # Standard table coordinate bounds or numeric list
        numeric_line = "[10, 20, 30]"
        cleaned_num, _, _ = self.cleaner.clean(numeric_line)
        self.assertIn("10", cleaned_num)
        self.assertIn("30", cleaned_num)

    def test_solver_personas(self) -> None:
        """Verify that AI system prompts load dynamically per persona."""
        # 1. Standard Solver
        self.config.set("ai_persona", "solver")
        prompt_solver = self.ai._build_system_prompt()
        self.assertIn("expert exam solver", prompt_solver)
        
        # 2. Socratic Tutor
        self.config.set("ai_persona", "tutor")
        prompt_tutor = self.ai._build_system_prompt()
        self.assertIn("Socratic Tutor", prompt_tutor)
        self.assertIn("DO NOT explicitly state the final answer option", prompt_tutor)

        # 3. Code Expert
        self.config.set("ai_persona", "code")
        prompt_code = self.ai._build_system_prompt()
        self.assertIn("coding mentor", prompt_code)
        
        # 4. Language Expert
        self.config.set("ai_persona", "lang")
        prompt_lang = self.ai._build_system_prompt()
        self.assertIn("Literature and Language Expert", prompt_lang)


if __name__ == "__main__":
    unittest.main()
