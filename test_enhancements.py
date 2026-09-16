import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import os
import tempfile
from config_manager import ConfigManager
from history_manager import HistoryManager
from app_bridge import FocusFlowAPI


class TestFocusFlowEnhancements(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.config = MagicMock(spec=ConfigManager)
        self.config.get.side_effect = lambda key, default=None: default
        self.config.get_api_keys.return_value = []
        self.config.get_all.return_value = {"theme": "dark", "llm_mode": "offline"}

    def tearDown(self):
        try:
            self.root.destroy()
        except:
            pass

    def test_focusflow_api_run_code_python(self):
        """Verify that FocusFlowAPI runs valid Python code in the sandbox."""
        mock_app = MagicMock()
        api = FocusFlowAPI(mock_app)
        res = api.run_code("python", "print('FocusFlow Test Sandbox')")
        self.assertEqual(res["exit_code"], 0)
        self.assertIn("FocusFlow Test Sandbox", res["stdout"])
        self.assertEqual(res["stderr"], "")

    def test_focusflow_api_run_code_unsupported(self):
        """Verify that FocusFlowAPI returns error for unsupported languages."""
        mock_app = MagicMock()
        api = FocusFlowAPI(mock_app)
        res = api.run_code("unsupported_lang", "test")
        self.assertEqual(res["exit_code"], -1)
        self.assertIn("Unsupported sandbox language", res["stderr"])

    def test_focusflow_api_settings_bridge(self):
        """Verify that save_settings and get_settings interact correctly with config."""
        mock_app = MagicMock()
        mock_app.config = self.config
        api = FocusFlowAPI(mock_app)
        
        # Test get_settings
        settings = api.get_settings()
        self.assertIsInstance(settings, dict)
        self.assertEqual(settings.get("theme"), "dark")

        # Test save_settings
        success = api.save_settings({"theme": "light", "focus_duration": 45})
        self.assertTrue(success)
        self.config.set.assert_any_call("theme", "light")
        self.config.set.assert_any_call("focus_duration", 45)

    def test_focusflow_api_query_ai(self):
        """Verify that query_ai_assistant formats and dispatches questions properly."""
        mock_app = MagicMock()
        mock_app.ai.solve_manual.return_value = {"answer": "Derived answer"}
        
        api = FocusFlowAPI(mock_app)
        res = api.query_ai_assistant("Solve x + 2 = 5", "doubt_solver")
        self.assertEqual(res, "Derived answer")
        mock_app.ai.solve_manual.assert_called_once()


    def test_study_guide_markdown_export(self):
        """Verify that study guide compile logic generates valid Markdown."""
        from ui.history_viewer import HistoryViewerDialog
        
        mock_history = MagicMock(spec=HistoryManager)
        mock_history.get_entries.return_value = [
            {
                "timestamp": "2026-06-10 12:00:00",
                "mode": "offline",
                "engine": "offline/llamacpp",
                "ocr_quality": "good",
                "raw_ocr": "What is 2+2?",
                "answer": "Answer: 4\nStep-by-step: 2 + 2 equals 4.",
            },
            {
                "timestamp": "2026-06-10 12:05:00",
                "mode": "online",
                "engine": "online/gpt-4o",
                "ocr_quality": "weak",
                "raw_ocr": "Solve: 5*5",
                "answer": "Answer: 25\nExplanation: 5 multiplied by 5 is 25.",
            }
        ]
        
        mock_guard = MagicMock()
        
        # Instantiate dialog
        dialog = HistoryViewerDialog(self.root, mock_history, mock_guard)
        
        # Mock messagebox and filedialog
        from tkinter import messagebox, filedialog
        
        # Create a temp file path to export to
        temp_dir = tempfile.gettempdir()
        export_path = os.path.join(temp_dir, "test_study_guide.md")
        if os.path.exists(export_path):
            os.remove(export_path)
            
        try:
            with patch.object(filedialog, "asksaveasfilename", return_value=export_path), \
                 patch.object(messagebox, "showinfo") as mock_info:
                 
                dialog._export_study_guide()
                
                # Check that showinfo was called (meaning successful export)
                mock_info.assert_called_once()
                
                # Read output file and check content
                self.assertTrue(os.path.exists(export_path))
                with open(export_path, "r", encoding="utf-8") as f:
                    content = f.read()
                    
                self.assertIn("# FocusFlow Revision & Study Guide", content)
                self.assertIn("Total Solved Questions: 2", content)
                self.assertIn("## Question 1", content)
                self.assertIn("What is 2+2?", content)
                self.assertIn("Answer: 4", content)
                self.assertIn("Solve: 5*5", content)
                self.assertIn("Answer: 25", content)
        finally:
            if os.path.exists(export_path):
                os.remove(export_path)


if __name__ == "__main__":
    unittest.main()

