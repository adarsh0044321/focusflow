import unittest
from unittest.mock import MagicMock, patch
import tkinter as tk
import os
import tempfile
from config_manager import ConfigManager
from history_manager import HistoryManager

class TestFocusFlowEnhancements(unittest.TestCase):

    def setUp(self):
        self.root = tk.Tk()
        self.root.withdraw()
        
        self.config = MagicMock(spec=ConfigManager)
        self.config.get.side_effect = lambda key, default=None: default
        self.config.get_api_keys.return_value = []

    def tearDown(self):
        try:
            self.root.destroy()
        except:
            pass

    def test_clipboard_duplicate_detection_logic(self):
        """Verify that clipboard text matches last solved prompts or answers are ignored."""
        from main import FocusFlowApp
        
        # Instantiate a mock app with mocked Tk root, config, and panel classes
        with patch("main.PipelinePanel") as mock_pipeline_cls, \
             patch("main.ControlPanel") as mock_control_cls, \
             patch("main.AnswerPanel") as mock_answer_cls, \
             patch("main.SettingsDialog") as mock_settings_cls, \
             patch.object(FocusFlowApp, "_init_guard"), \
             patch.object(FocusFlowApp, "_register_hotkeys"), \
             patch.object(FocusFlowApp, "_init_ai"):
             
            app = FocusFlowApp()
            app.root = self.root
            app.config = self.config
            app._cleaned_up = False
            
            # Setup config mock to return clipboard monitor enabled
            self.config.get.side_effect = lambda key, default=None: True if key == "clipboard_monitor_enabled" else default
            
            # Set state indicators
            app._last_clipboard_text = "Original Clip"
            app._last_ocr_text = "Solved Prompt"
            app._last_raw_text = "Raw Prompt"
            app._last_ai_answer = "AI Answer"
            
            # Setup manual solve mock
            app._solve_manual_text = MagicMock()
            
            # 1. Test duplicate clip text
            self.root.clipboard_clear()
            self.root.clipboard_append("Original Clip")
            app.check_clipboard()
            app._solve_manual_text.assert_not_called()
            
            # 2. Test duplicate solved prompt
            self.root.clipboard_clear()
            self.root.clipboard_append("Solved Prompt")
            app.check_clipboard()
            app._solve_manual_text.assert_not_called()
            
            # 3. Test duplicate raw prompt
            self.root.clipboard_clear()
            self.root.clipboard_append("Raw Prompt")
            app.check_clipboard()
            app._solve_manual_text.assert_not_called()
            
            # 4. Test duplicate AI answer
            self.root.clipboard_clear()
            self.root.clipboard_append("AI Answer")
            app.check_clipboard()
            app._solve_manual_text.assert_not_called()
            
            # 5. Test new fresh text
            self.root.clipboard_clear()
            self.root.clipboard_append("New Question to Solve")
            app.check_clipboard()
            app._solve_manual_text.assert_called_once_with("New Question to Solve")

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

    def test_panel_hiding_during_solve(self):
        """Verify that solve triggers hide panels and schedules show panels after capture."""
        from main import FocusFlowApp
        
        with patch("main.PipelinePanel") as mock_pipeline_cls, \
             patch("main.ControlPanel") as mock_control_cls, \
             patch("main.AnswerPanel") as mock_answer_cls, \
             patch("main.SettingsDialog") as mock_settings_cls, \
             patch.object(FocusFlowApp, "_init_guard"), \
             patch.object(FocusFlowApp, "_register_hotkeys"), \
             patch.object(FocusFlowApp, "_init_ai"):

            app = FocusFlowApp()
            app.root = self.root
            app.capture = MagicMock()
            app.capture.capture.return_value = MagicMock()
            app._hide_panels = MagicMock()
            app._show_panels = MagicMock()
            
            # Setup thread run
            app._on_solve()
            
            # Verify hide panels was called immediately on main thread
            app._hide_panels.assert_called_once()
            
            # Run background thread synchronously to test show callback
            app._solve_pipeline(rerun=False)
            
            # Wait for any scheduled actions on main thread queue
            self.root.update()
            
            # Verify show panels was called (which schedules self._show_panels on main thread)
            app._show_panels.assert_called_once()


if __name__ == "__main__":
    unittest.main()
