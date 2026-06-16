"""
FocusFlow Webview API Bridge
=============================
Bridges JavaScript commands inside the pywebview browser runtime to
native Python operations.
"""

import json
import logging
import os
import subprocess
import threading
import time
import win32api
import win32con
import win32gui
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("focusflow.bridge")

class FocusFlowAPI:
    """Methods exposed directly to window.pywebview.api in JavaScript."""

    def __init__(self, app: Any) -> None:
        self._app = app
        self._logger = logger

    # --- System Controls ---
    def minimize_window(self) -> None:
        """Minimize the main application window."""
        try:
            self._app.window.minimize()
            self._logger.info("Window minimized via JS API.")
        except Exception as e:
            self._logger.error(f"Error minimizing window: {e}")

    def close_window(self) -> None:
        """Close the application window and exit."""
        try:
            self._logger.info("Window close requested via JS API.")
            self._app.cleanup()
            self._app.window.destroy()
        except Exception as e:
            self._logger.error(f"Error closing window: {e}")

    # --- Session Controls ---
    def start_focus_session(self, goal: str, subject: str, duration_mins: int, mode: str, custom_features: Optional[Dict[str, bool]] = None) -> bool:
        """Request the python backend to lock focus and start a session."""
        try:
            self._logger.info(f"Starting focus session: {goal} ({subject}), {duration_mins} mins, Mode: {mode}, Features: {custom_features}")
            return self._app.start_focus_session(goal, subject, duration_mins, mode, custom_features)
        except Exception as e:
            self._logger.error(f"Error starting focus session: {e}")
            return False

    def stop_focus_session(self, status: str) -> bool:
        """End the current focus session and save results."""
        try:
            self._logger.info(f"Stopping focus session with status: {status} (asynchronously)")
            threading.Thread(target=self._app.stop_focus_session, args=(status,), daemon=True).start()
            return True
        except Exception as e:
            self._logger.error(f"Error stopping focus session: {e}")
            return False

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """Retrieve details of the active focus session (used for crash recovery)."""
        try:
            return self._app.get_active_session()
        except Exception as e:
            self._logger.error(f"Error getting active session: {e}")
            return None

    # --- Stats & Goals ---
    def get_stats(self) -> Dict[str, Any]:
        """Fetch compiled session metrics, streaks, and achievements."""
        try:
            return self._app.session_manager.get_stats()
        except Exception as e:
            self._logger.error(f"Error getting stats: {e}")
            return {}

    def get_daily_goals(self) -> List[Dict[str, Any]]:
        try:
            return self._app.session_manager.get_daily_goals()
        except Exception as e:
            self._logger.error(f"Error getting daily goals: {e}")
            return []

    def add_daily_goal(self, text: str) -> Dict[str, Any]:
        try:
            return self._app.session_manager.add_daily_goal(text)
        except Exception as e:
            self._logger.error(f"Error adding daily goal: {e}")
            return {}

    def toggle_daily_goal(self, goal_id: str) -> bool:
        try:
            return self._app.session_manager.toggle_daily_goal(goal_id)
        except Exception as e:
            self._logger.error(f"Error toggling daily goal: {e}")
            return False

    def delete_daily_goal(self, goal_id: str) -> bool:
        try:
            return self._app.session_manager.delete_daily_goal(goal_id)
        except Exception as e:
            self._logger.error(f"Error deleting daily goal: {e}")
            return False

    # --- AI Study Assistant ---
    def query_ai_assistant(self, query: str, tool: str, ocr_context: Optional[str] = None) -> str:
        """Query the AI Engine with highly specialized academic templates."""
        try:
            self._logger.info(f"AI Assistant query via tool: {tool}")
            
            # Format student-specific templates
            templates = {
                "doubt_solver": (
                    "You are a specialized Study AI Doubts Solver. Solve the following question step-by-step, "
                    "explaining the methodology and formulas used. Give the final answer clearly at the end.\n\n"
                    "Question:\n{query}"
                ),
                "concept_explainer": (
                    "Explain the following academic concept in simple terms, using an intuitive real-world analogy. "
                    "Provide a clear definition followed by 3 key bullet-point highlights.\n\n"
                    "Concept: {query}"
                ),
                "summarizer": (
                    "Create a structured, clean summary of the following text. Highlight key definitions, formulas, "
                    "or historical dates in bold or code blocks.\n\n"
                    "Text: {query}"
                ),
                "flashcards": (
                    "Synthesize the following text into 5 high-yield study flashcards. Format each flashcard as:\n"
                    "Q: [Question]\nA: [Answer]\n\n"
                    "Text:\n{query}"
                ),
                "notes_generator": (
                    "Convert the following text into organized, structured study and revision notes. "
                    "Use hierarchical headings (Markdown #, ##, ###), lists, and highlight key concepts.\n\n"
                    "Text:\n{query}"
                ),
                "quiz_maker": (
                    "Create a 3-question multiple-choice quiz on the following topic. Each question must have "
                    "options A, B, C, and D. List the correct answers and brief explanations at the very end.\n\n"
                    "Topic: {query}"
                ),
                "formula_explainer": (
                    "Break down the following formula. Detail what each variable means (with units), the core "
                    "physical or mathematical principle, and show a simple solved numerical example.\n\n"
                    "Formula: {query}"
                ),
                "study_planner": (
                    "Create a structured, calendar-ready study and revision schedule for the topic or exam listed below. "
                    "Identify key sub-topics, recommended daily time blocks, and a quick revision checklist.\n\n"
                    "Topic/Exam: {query}"
                )
            }
            
            # Retrieve correct template or default
            prompt_template = templates.get(tool, "Please answer the following study query:\n{query}")
            formatted_prompt = prompt_template.format(query=query)
            
            if ocr_context:
                formatted_prompt += f"\n\nContext extracted from screen capture:\n{ocr_context}"
                
            # Ensure AI engine is started (in case it is run outside of a session, or is still loading)
            threading.Thread(target=self._app.ai.start, daemon=True).start()

            # Send to unified AI engine
            result = self._app.ai.solve_manual(formatted_prompt)
            response = result.get("answer", "")
            return response
        except Exception as e:
            self._logger.error(f"Error querying AI Assistant: {e}")
            return f"Error connecting to AI engine: {e}"

    # --- Screen Capture & OCR ---
    def trigger_ocr_capture(self) -> None:
        """Trigger transparent region capture on a background thread to prevent GUI lockup."""
        try:
            self._logger.info("OCR Screen Capture requested.")
            threading.Thread(target=self._app.run_stealth_capture, daemon=True).start()
        except Exception as e:
            self._logger.error(f"Error triggering OCR capture: {e}")

    # --- Media Controller (Spotify) ---
    def spotify_action(self, action: str) -> bool:
        """Control local media playback (Spotify / fallback) using native keyboard virtual keys."""
        try:
            self._logger.info(f"Media controller action: {action}")
            vk_map = {
                "play_pause": win32con.VK_MEDIA_PLAY_PAUSE,
                "next": win32con.VK_MEDIA_NEXT_TRACK,
                "prev": win32con.VK_MEDIA_PREV_TRACK
            }
            
            if action not in vk_map:
                # Fallback: launch Spotify app if that's the command
                if action == "launch":
                    spotify_path = os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe")
                    if os.path.exists(spotify_path):
                        subprocess.Popen(spotify_path)
                        return True
                    else:
                        os.system("start spotify:") # URI scheme launch
                        return True
                return False
                
            key = vk_map[action]
            win32api.keybd_event(key, 0, 0, 0)
            win32api.keybd_event(key, 0, win32con.KEYEVENTF_KEYUP, 0)
            return True
        except Exception as e:
            self._logger.error(f"Error sending media key: {e}")
            return False

    # --- Settings Manager ---
    def get_settings(self) -> Dict[str, Any]:
        """Retrieve the compiled dictionary of application configuration parameters.

        Fetches all persistable setting key-value pairs stored in the active ConfigManager.
        """
        try:
            settings_data = self._app.config.get_all()
            self._logger.debug("Successfully read config settings count: %d", len(settings_data))
            return settings_data
        except Exception as e:
            self._logger.error(f"Error reading config: {e}", exc_info=True)
            return {}

    def save_settings(self, settings_dict: Dict[str, Any]) -> bool:
        """Save settings and apply dynamic runtime parameters."""
        try:
            self._logger.info("Saving new configuration settings...")
            for k, v in settings_dict.items():
                self._app.config.set(k, v)
            
            # Apply dynamic changes (like opacity) immediately
            opacity = settings_dict.get("opacity", 240)
            self._app.update_opacity(opacity)

            # Dynamically adjust offline engine if AI panel is active/visible
            if getattr(self._app, "ai_panel_visible", False):
                new_model = settings_dict.get("online_model")
                if new_model in ("gpt-4o", "gpt-4o-mini"):
                    # Stop offline server to free RAM
                    threading.Thread(target=self._app.ai.stop, daemon=True).start()
                elif new_model in ("offline", "combined"):
                    # Start offline server
                    threading.Thread(target=self._app.ai.start, daemon=True).start()

            return True
        except Exception as e:
            self._logger.error(f"Error saving settings: {e}")
            return False

    # --- External Windows Utilities (Strict Mode Allowed) ---
    def open_file_explorer(self) -> None:
        """Open Windows File Explorer (Safe whitelist command)."""
        try:
            subprocess.Popen("explorer.exe")
        except Exception as e:
            self._logger.error(f"Error launching file explorer: {e}")

    def open_pdf_selector(self) -> None:
        """Let the user pick a PDF and open it in their default PDF reader."""
        try:
            # We can start a thread to prevent blocking the webview
            threading.Thread(target=self._app.open_pdf_dialog, daemon=True).start()
        except Exception as e:
            self._logger.error(f"Error opening PDF selector: {e}")

    def on_ai_panel_visibility_changed(self, visible: bool) -> None:
        """Called by JS frontend when the AI panel visibility changes."""
        try:
            self._logger.info(f"AI Panel visibility changed: {visible}")
            self._app.ai_panel_visible = visible
            if visible:
                # Start the AI engine (starts llama-server if configured for offline/combined)
                threading.Thread(target=self._app.ai.start, daemon=True).start()
            else:
                # Stop the AI engine (kills llama-server to free resources)
                threading.Thread(target=self._app.ai.stop, daemon=True).start()
        except Exception as e:
            self._logger.error(f"Error handling AI panel visibility change: {e}")
