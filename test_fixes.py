import unittest
from unittest.mock import MagicMock
from history_manager import HistoryManager
from config_manager import ConfigManager
from online_engine import OnlineEngine


class TestFocusFlowFixes(unittest.TestCase):

    def setUp(self):
        self.config = MagicMock(spec=ConfigManager)
        self.config.get.side_effect = lambda key, default=None: default
        self.config.get_api_keys.return_value = ["test_key"]

    def test_history_manager_template_override(self):
        """Verify that passing screenshot_path overrides the empty default template."""
        # Mock dependencies
        hm = HistoryManager(base_dir=".", config=self.config)
        hm._entries = []
        hm._save = MagicMock()

        test_entry = {
            "timestamp": "2026-06-03 12:00:00",
            "screenshot_path": "data/screenshots/screenshot_test.png",
            "raw_ocr": "What is 2+2?",
            "cleaned_ocr": "What is 2+2?",
            "answer": "Answer: 4",
        }

        hm.add_entry(test_entry)

        # Check entries
        entries = hm.get_entries(limit=1)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["screenshot_path"], "data/screenshots/screenshot_test.png")
        self.assertEqual(entries[0]["raw_ocr"], "What is 2+2?")

    def test_online_engine_fallback_when_responses_fails(self):
        """Verify that OnlineEngine._request_completion falls back to chat.completions when client.responses raises exceptions."""
        engine = OnlineEngine(self.config)

        # 1. Setup client with a broken custom responses endpoint
        mock_client = MagicMock()
        mock_client.responses.create.side_effect = Exception("Custom endpoint failed")

        # Mock the chat completions to return a valid mock response
        mock_chat_completion = MagicMock()
        mock_chat_completion.choices = [MagicMock()]
        mock_chat_completion.choices[0].message.content = "Chat Completions Answer"
        mock_client.chat.completions.create.return_value = mock_chat_completion

        # Call completion
        answer = engine._request_completion(
            client=mock_client,
            model="gpt-4o",
            messages_or_input="Test Prompt",
            max_tokens=1000,
            temperature=0.2
        )

        # Verify it fallback successfully and returned correct text
        self.assertEqual(answer, "Chat Completions Answer")
        mock_client.responses.create.assert_called_once()
        mock_client.chat.completions.create.assert_called_once()

    def test_online_engine_fallback_when_responses_missing(self):
        """Verify that OnlineEngine._request_completion falls back to chat.completions when client has no responses attribute."""
        engine = OnlineEngine(self.config)

        # Setup client without responses attribute
        mock_client = MagicMock(spec=["chat"])
        # Deliberately delete responses if mock has it due to MagicMock behavior
        if hasattr(mock_client, "responses"):
            delattr(mock_client, "responses")

        mock_chat_completion = MagicMock()
        mock_chat_completion.choices = [MagicMock()]
        mock_chat_completion.choices[0].message.content = "Chat Completions Direct Answer"
        mock_client.chat.completions.create.return_value = mock_chat_completion

        # Call completion
        answer = engine._request_completion(
            client=mock_client,
            model="gpt-4o",
            messages_or_input="Test Prompt",
            max_tokens=1000,
            temperature=0.2
        )

        self.assertEqual(answer, "Chat Completions Direct Answer")
        mock_client.chat.completions.create.assert_called_once()

    def test_control_panel_update_region_display(self):
        """Verify that ControlPanel.update_region_display respects capture_mode."""
        mock_config = MagicMock()
        
        # Test case 1: capture_mode is "region"
        mock_config.get.side_effect = lambda key, default=None: "region" if key == "capture_mode" else default
        panel = MagicMock()
        panel.config = mock_config
        panel._region_text_var = MagicMock()
        
        from ui.control_panel import ControlPanel
        ControlPanel.update_region_display(panel, 800, 600)
        panel._region_text_var.set.assert_called_once_with("Capture Area: Region (800×600)")
        
        # Test case 2: capture_mode is "fullscreen"
        panel._region_text_var.reset_mock()
        mock_config.get.side_effect = lambda key, default=None: "fullscreen" if key == "capture_mode" else default
        ControlPanel.update_region_display(panel, 800, 600)
        panel._region_text_var.set.assert_called_once_with("Capture Area: Fullscreen")

    def test_ai_engine_solve_manual_prompt_cleaning(self):
        """Verify that solve_manual in AIEngine dynamically re-indexes the prompt rules when removing OCR-specific instructions."""
        from ai_engine import AIEngine
        mock_config = MagicMock()
        mock_config.get.side_effect = lambda key, default=None: "solver" if key == "ai_persona" else ("offline" if key == "mode" else default)
        
        # Instantiate AIEngine with mocked subcomponents
        engine = AIEngine(mock_config)
        engine.offline = MagicMock()
        engine.offline.is_ready.return_value = True
        engine.offline.query.return_value = "Mocked offline response"
        engine._get_knowledge_context = MagicMock(return_value="")
        engine._effective_mode = MagicMock(return_value="offline")
        
        # Call solve_manual
        engine.solve_manual("Test manual question")
        
        # Capture the system prompt passed to the offline query
        args, kwargs = engine.offline.query.call_args
        system_prompt = kwargs.get("system_prompt") if "system_prompt" in kwargs else args[1]
        
        # Verify the prompt does not contain OCR references and is correctly numbered
        self.assertNotIn("OCR", system_prompt)
        self.assertNotIn("2. Solve the problem methodically", system_prompt)
        self.assertIn("1. Solve the problem methodically", system_prompt)
        self.assertIn("2. If options are provided", system_prompt)


if __name__ == "__main__":
    unittest.main()
