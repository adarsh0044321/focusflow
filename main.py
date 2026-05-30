"""
FocusFlow — Main Entry Point
============================
Study tool that captures screen content, performs OCR, and uses AI
(offline llama.cpp or online OpenAI API) to solve exam questions.

Features:
- Screen capture evasion (invisible to screenshots/screen sharing)
- Region selection for targeted capture
- OCR with text cleaning
- Offline LLM (llama.cpp + Phi-3)
- Online mode (OpenAI ChatGPT API with key rotation)
- Combined mode (switch between offline/online)
- Manual question input
- Knowledge base integration
- Global hotkeys
"""

import logging
import os
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from typing import Optional

# ---------------------------------------------------------------------------
# Resolve base directory (where this script lives)
# ---------------------------------------------------------------------------
if getattr(sys, "frozen", False):
    exe_dir = Path(sys.executable).resolve().parent
    if exe_dir.name.lower() == "dist" and not (exe_dir / "Tesseract-OCR").exists() and (exe_dir.parent / "Tesseract-OCR").exists():
        BASE_DIR = exe_dir.parent
    else:
        BASE_DIR = exe_dir
else:
    BASE_DIR = Path(__file__).resolve().parent

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "focusflow.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("focusflow")

# ---------------------------------------------------------------------------
# Imports (after logging is configured)
# ---------------------------------------------------------------------------
from config_manager import ConfigManager
from screen_capture import ScreenCapture
from ocr_engine import OCREngine
from ocr_cleaner import OCRCleaner
from ai_engine import AIEngine
from guard import CaptureGuard
from history_manager import HistoryManager
from knowledge_base import KnowledgeBase

from ui.pipeline_panel import PipelinePanel
from ui.control_panel import ControlPanel
from ui.answer_panel import AnswerPanel
from ui.settings_dialog import SettingsDialog


class FocusFlowApp:
    """Main application class that wires all components together."""

    def __init__(self) -> None:
        logger.info(f"[Startup] FocusFlow — log: {LOG_FILE}")

        # ── Core components ──────────────────────────────────────────
        self.config = ConfigManager(str(BASE_DIR))
        self.kb = KnowledgeBase(str(BASE_DIR))
        self.history = HistoryManager(str(BASE_DIR), self.config)
        self.ocr = OCREngine(self.config)
        self.cleaner = OCRCleaner()
        self.capture = ScreenCapture(self.config)
        self.ai = AIEngine(self.config, self.kb)
        self.guard = CaptureGuard()

        # ── Tkinter root ─────────────────────────────────────────────
        self.root = tk.Tk()
        self.root.withdraw()  # hide root — we use Toplevel panels

        # ── Create UI panels ─────────────────────────────────────────
        self._create_panels()

        # ── Screen capture guard ─────────────────────────────────────
        self.root.after(500, self._init_guard)

        # ── Global hotkeys ───────────────────────────────────────────
        self._register_hotkeys()

        # ── Start AI engine in background ────────────────────────────
        self._init_ai_thread = threading.Thread(
            target=self._init_ai, daemon=True, name="ai-init"
        )
        self._init_ai_thread.start()

        # ── OCR status ───────────────────────────────────────────────
        if self.ocr.is_ready():
            self.pipeline.set_ocr_status("OCR: Ready", ready=True)
            self.pipeline.log(f"OCR: {self.ocr.status_message()}")
        else:
            self.pipeline.set_ocr_status("OCR: Not Found", ready=False)
            self.pipeline.log(f"OCR: {self.ocr.status_message()}")

        # ── Update region display ────────────────────────────────────
        w = self.config.get("region_w")
        h = self.config.get("region_h")
        self.controls.update_region_display(w, h)

        # ── Mode display ─────────────────────────────────────────────
        mode = self.config.get("mode")
        combined = self.config.get("combined_active")
        self.controls.update_mode_display(mode, combined)

        # ── Mark first run complete ──────────────────────────────────
        if self.config.get("first_run"):
            self.config.set("first_run", False)

        logger.info("[Startup] UI initialised — entering main loop")

    # ==================================================================
    # UI Creation
    # ==================================================================

    def _create_panels(self) -> None:
        """Create the three main panels as Toplevel windows."""
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()

        # Panel dimensions
        panel_w = 420
        panel_h = 500

        # Pipeline panel (left)
        self.pipeline = PipelinePanel(self.root)
        self.pipeline_win = tk.Toplevel(self.root)
        self.pipeline_win.overrideredirect(True)
        self.pipeline_win.attributes("-topmost", True)
        self.pipeline_win.configure(bg="#1a1a2e")
        self.pipeline_win.geometry(f"{panel_w}x{panel_h}+10+50")
        opacity = self.config.get("opacity", 240)
        self.pipeline_win.attributes("-alpha", opacity / 255.0)
        self.pipeline = PipelinePanel(self.pipeline_win)
        self.pipeline.pack(fill=tk.BOTH, expand=True)

        # Control panel (center)
        self.controls = ControlPanel(self.root, self.config)
        self.controls.geometry(f"{panel_w}x{panel_h}+{10 + panel_w + 10}+50")
        self.controls.attributes("-alpha", opacity / 255.0)

        # Answer panel (right)
        self.answer_win = tk.Toplevel(self.root)
        self.answer_win.overrideredirect(True)
        self.answer_win.attributes("-topmost", True)
        self.answer_win.configure(bg="#1a1a2e")
        self.answer_win.geometry(
            f"{panel_w}x{panel_h}+{10 + (panel_w + 10) * 2}+50"
        )
        self.answer_win.attributes("-alpha", opacity / 255.0)
        self.answer = AnswerPanel(self.answer_win)
        self.answer.pack(fill=tk.BOTH, expand=True)

        # ── Wire up callbacks ────────────────────────────────────────
        self.controls.set_on_solve(self._on_solve)
        self.controls.set_on_region(self._on_region_select)
        self.controls.set_on_settings(self._on_settings)
        self.controls.set_mode_callback(self._on_mode_change)
        self.controls.set_on_manual_send(self._on_manual_send_click)

        self.answer.set_on_rerun(self._on_solve)
        self.answer.set_on_manual_q(self._on_manual_question)
        self.answer.set_on_clear(self._on_clear)

        # Track all windows for guard and toggle
        self._windows = [self.pipeline_win, self.controls, self.answer_win]
        self._panels_visible = True

    # ==================================================================
    # Guard (Screen Capture Evasion)
    # ==================================================================

    def _init_guard(self) -> None:
        """Apply screen capture protection to all windows."""
        try:
            for win in self._windows:
                self.guard.protect_all_tk_windows(win)
            self.guard.start()
            count = len(self.guard._hwnds)
            logger.info(f"[Protection] {count} panels protected.")
        except Exception as e:
            logger.error(f"[Guard] Failed to initialise: {e}")

    # ==================================================================
    # AI Initialization
    # ==================================================================

    def _init_ai(self) -> None:
        """Start the AI engine (runs in background thread)."""
        mode = self.config.get("mode") or "combined"
        if mode == "online":
            self._update_llm_status("Online Mode Active", True)
            self.pipeline.log("LLM: Online mode active.")
            return

        self.pipeline.log("LLM: Starting AI engine...")
        self._update_llm_status("Loading model... (may take 30-60s on low-RAM PC)", False)

        self.ai.start()

        # Poll for readiness
        max_wait = int(self.config.get("llm_timeout", 300))
        elapsed = 0
        while elapsed < max_wait:
            if self.config.get("mode") == "online":
                self._update_llm_status("Online Mode Active", True)
                self.pipeline.log("LLM: Switched to online mode. Stopping loader.")
                self.ai.stop()
                return

            if self.ai.offline.is_ready():
                self._update_llm_status("LLM: Model loaded and ready!", True)
                self.pipeline.log("LLM: Model loaded and ready!")
                return
            time.sleep(2)
            elapsed += 2
            status = self.ai.offline.status_message()
            self._update_llm_status(status, False)
            self.pipeline.log(f"LLM: {status}")

        self._update_llm_status("LLM: Timeout waiting for model", False)
        self.pipeline.log("LLM: Timeout — model may not have loaded.")

    def _update_llm_status(self, message: str, ready: bool) -> None:
        """Thread-safe LLM status update."""
        try:
            self.root.after(0, lambda: self.pipeline.set_llm_status(message, ready))
        except Exception:
            pass

    # ==================================================================
    # Hotkeys
    # ==================================================================

    def _register_hotkeys(self) -> None:
        """Register global hotkeys using keyboard library."""
        try:
            import keyboard
        except ImportError:
            logger.warning(
                "[Hotkeys] 'keyboard' module not found — hotkeys disabled. "
                "Install with: pip install keyboard"
            )
            self.pipeline.log(
                "[Warning] Hotkeys disabled — install 'keyboard' module"
            )
            return

        hotkeys = [
            ("hotkey_solve", self._on_solve_hotkey),
            ("hotkey_toggle", self._on_toggle_panels_hotkey),
            ("hotkey_clear", self._on_clear_hotkey),
            ("hotkey_settings", self._on_settings_hotkey),
        ]
        
        registered_count = 0
        for name, cb in hotkeys:
            hk = self.config.get(name)
            if hk:
                try:
                    keyboard.add_hotkey(hk, cb, suppress=False)
                    registered_count += 1
                    logger.debug(f"[Hotkeys] Registered {name}: {hk}")
                except Exception as e:
                    logger.error(f"[Hotkeys] Failed to register {name} ({hk}): {e}")

        # Register opacity keys separately as fallback keys
        opacity_keys = [
            ("ctrl+.", self._on_opacity_up),
            ("ctrl+period", self._on_opacity_up),
            ("ctrl+,", self._on_opacity_down),
            ("ctrl+comma", self._on_opacity_down),
        ]
        for hk, cb in opacity_keys:
            try:
                keyboard.add_hotkey(hk, cb, suppress=False)
                logger.debug(f"[Hotkeys] Registered opacity shortcut: {hk}")
            except Exception as e:
                logger.warning(f"[Hotkeys] Failed to register opacity shortcut {hk}: {e}")

        logger.info(f"[Hotkeys] Registered {registered_count} global hotkeys")
        self.pipeline.log("Hotkeys registered. Press Ctrl+Shift+K to solve.")

    # ==================================================================
    # Actions
    # ==================================================================

    def _on_solve_hotkey(self) -> None:
        """Called from hotkey thread — schedule solve on main thread."""
        self.root.after(0, self._on_solve)

    def _on_solve(self) -> None:
        """Capture screen, OCR, and solve with AI."""
        self.pipeline.log("\n--- Solving ---")
        self.answer.set_system_message("[System] Capturing screen...")

        # Run in thread to avoid UI freeze
        threading.Thread(target=self._solve_pipeline, daemon=True).start()

    def _solve_pipeline(self) -> None:
        """Full solve pipeline (runs in background thread)."""
        t_start = time.perf_counter()

        # 1. Capture
        try:
            image = self.capture.capture()
            self.pipeline.log(f"[Capture] {image.size[0]}x{image.size[1]} captured")
        except Exception as e:
            self.pipeline.log(f"[Capture] Error: {e}")
            self._set_answer_safe(f"[Error] Screen capture failed: {e}")
            return

        # 2. Save screenshot if enabled
        if self.config.get("save_screenshot_history"):
            timestamp = time.strftime("%Y-%m-%d_%H-%M-%S")
            self.history.save_screenshot(image, timestamp)

        # 3. OCR
        t_ocr = time.perf_counter()
        raw_text, ocr_err = self.ocr.extract_text(image)
        ocr_duration = round(time.perf_counter() - t_ocr, 2)

        if ocr_err:
            self.pipeline.log(f"[OCR] Warning: {ocr_err}")
        self.pipeline.log(f"[OCR] Extracted {len(raw_text)} chars in {ocr_duration}s")

        # 4. Clean OCR
        cleaned_text, quality, warnings = self.cleaner.clean(raw_text)
        self.pipeline.log(
            f"[OCRCleaner] raw={len(raw_text)} chars -> cleaned={len(cleaned_text)} chars, quality={quality}"
        )
        for w in warnings:
            self.pipeline.log(f"[OCRCleaner] Warning: {w}")

        if not cleaned_text.strip():
            self._set_answer_safe("[No text detected] Try adjusting the capture region.")
            return

        # 5. AI Solve
        self._set_system_safe("[System] Sending to AI...")
        t_llm = time.perf_counter()

        mode = self.config.get("mode", "combined")
        send_mode = self.config.get("online_send_mode", "ocr")

        # Determine if we should send image
        send_image = None
        effective_mode = self.ai._effective_mode()
        if effective_mode == "online" and send_mode in ("image", "both"):
            send_image = image

        result = self.ai.solve(cleaned_text, image=send_image)
        llm_duration = round(time.perf_counter() - t_llm, 2)

        answer = result.get("answer", "[No answer]")
        engine = result.get("engine", "unknown")

        self.pipeline.log(f"[AI] Answer in {llm_duration}s via {engine} ({len(answer)} chars)")
        self._set_answer_safe(answer)

        # 6. Save to history
        entry = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "raw_ocr": raw_text,
            "cleaned_ocr": cleaned_text,
            "answer": answer,
            "ocr_quality": quality,
            "ocr_warnings": warnings,
            "ocr_duration_s": ocr_duration,
            "llm_duration_s": llm_duration,
            "answer_mode": self.config.get("answer_mode"),
            "capture_mode": self.config.get("capture_mode"),
            "mode": effective_mode,
        }
        self.history.add_entry(entry)

        total = round(time.perf_counter() - t_start, 2)
        self.pipeline.log(f"[Done] Total: {total}s")

    def _on_manual_question(self) -> None:
        """Handle Manual Q button on Answer Panel (shows dialog)."""
        question = self.answer.get_manual_question()
        if not question or not question.strip():
            return
        self._solve_manual_text(question)

    def _on_manual_send_click(self, text: str) -> None:
        """Handle Send button on Control Panel (takes text from entry)."""
        if not text or not text.strip():
            return
        self.controls.clear_manual_text()
        self._solve_manual_text(text)

    def _solve_manual_text(self, question: str) -> None:
        """Common helper to solve manual questions in a background thread."""
        self.pipeline.log(f"\n--- Manual Question ---\n{question[:100]}...")
        self.answer.set_system_message("[System] Processing manual question...")

        def _solve():
            result = self.ai.solve_manual(question.strip())
            answer = result.get("answer", "[No answer]")
            engine = result.get("engine", "unknown")
            duration = result.get("duration", 0)
            self.pipeline.log(f"[AI] Manual answer in {duration}s via {engine}")
            self._set_answer_safe(answer)

            # Save to history
            entry = {
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "raw_ocr": question,
                "cleaned_ocr": question,
                "answer": answer,
                "ocr_quality": "manual",
                "ocr_warnings": [],
                "ocr_duration_s": 0,
                "llm_duration_s": duration,
                "answer_mode": self.config.get("answer_mode"),
                "capture_mode": "manual",
                "mode": result.get("mode", "offline"),
            }
            self.history.add_entry(entry)

        threading.Thread(target=_solve, daemon=True).start()

    def _on_region_select(self) -> None:
        """Open region selection overlay."""
        # Hide panels during selection
        self._hide_panels()

        def on_selected(x, y, w, h):
            self.config.set("region_x", x)
            self.config.set("region_y", y)
            self.config.set("region_w", w)
            self.config.set("region_h", h)
            self.config.set("capture_mode", "region")
            self.controls.update_region_display(w, h)
            self.pipeline.log(f"[Region] Set to ({x}, {y}) {w}x{h}")
            # Show panels again
            self._show_panels()

        self.capture.select_region_interactive(on_selected)

    def _on_settings(self) -> None:
        """Open settings dialog."""
        try:
            dialog = SettingsDialog(
                self.root,
                self.config,
                on_save=self._on_settings_saved,
                on_opacity_preview=self._set_opacity
            )
            # Protect the settings window too
            self.root.after(200, lambda: self.guard.protect_all_tk_windows(dialog))
        except Exception as e:
            logger.error(f"[Settings] Error opening: {e}")

    def _on_settings_saved(self) -> None:
        """Apply newly saved settings immediately to running app."""
        # 1. Opacity
        opacity = self.config.get("opacity", 240)
        self._set_opacity(opacity)

        # 2. Always on top
        always_on_top = self.config.get("always_on_top", True)
        for win in self._windows:
            try:
                win.attributes("-topmost", always_on_top)
            except Exception:
                pass

        # 3. Capture Region / Mode
        w = self.config.get("region_w")
        h = self.config.get("region_h")
        self.controls.update_region_display(w, h)

        # 4. Mode Display
        mode = self.config.get("mode")
        combined = self.config.get("combined_active")
        self.controls.update_mode_display(mode, combined)

        # 5. Start offline engine if mode requires it
        if mode in ("offline", "combined") and not self.ai.offline.is_ready():
            threading.Thread(target=self._init_ai, daemon=True).start()

    def _on_clear(self) -> None:
        """Clear the answer panel."""
        self.answer.clear_answer()
        self.answer.set_system_message("[System] Cleared.")

    def _on_mode_change(self, mode: str, combined_active: Optional[str] = None) -> None:
        """Handle mode change from UI."""
        self.config.set("mode", mode)
        if combined_active:
            self.config.set("combined_active", combined_active)
        self.controls.update_mode_display(mode, combined_active)
        self.pipeline.log(f"[Mode] Changed to: {mode}" + (f" ({combined_active})" if combined_active else ""))

        # Start offline engine if needed and not already running
        if mode in ("offline", "combined") and not self.ai.offline.is_ready():
            threading.Thread(target=self._init_ai, daemon=True).start()

    def _on_toggle_panels(self) -> None:
        """Toggle panel visibility."""
        if self._panels_visible:
            self._hide_panels()
        else:
            self._show_panels()

    def _hide_panels(self) -> None:
        """Hide all panels."""
        for win in self._windows:
            try:
                win.withdraw()
            except Exception:
                pass
        self._panels_visible = False

    def _show_panels(self) -> None:
        """Show all panels."""
        for win in self._windows:
            try:
                win.deiconify()
            except Exception:
                pass
        self._panels_visible = True
        # Reapply guard
        self.root.after(200, self._init_guard)

    def _on_toggle_panels_hotkey(self) -> None:
        """Safe wrapper for toggle hotkey."""
        self.root.after(0, self._on_toggle_panels)

    def _on_clear_hotkey(self) -> None:
        """Safe wrapper for clear hotkey."""
        self.root.after(0, self._on_clear)

    def _on_settings_hotkey(self) -> None:
        """Safe wrapper for settings hotkey."""
        self.root.after(0, self._on_settings)

    def _on_opacity_up(self) -> None:
        """Increase opacity."""
        self.root.after(0, self._on_opacity_up_main)

    def _on_opacity_up_main(self) -> None:
        current = self.config.get("opacity", 240)
        new_val = min(255, current + 15)
        self._set_opacity(new_val)

    def _on_opacity_down(self) -> None:
        """Decrease opacity."""
        self.root.after(0, self._on_opacity_down_main)

    def _on_opacity_down_main(self) -> None:
        current = self.config.get("opacity", 240)
        new_val = max(50, current - 15)
        self._set_opacity(new_val)

    def _set_opacity(self, value: int) -> None:
        """Set opacity for all panels."""
        self.config.set("opacity", value)
        alpha = value / 255.0
        for win in self._windows:
            try:
                win.attributes("-alpha", alpha)
            except Exception:
                pass

    # ==================================================================
    # Thread-safe UI helpers
    # ==================================================================

    def _set_answer_safe(self, text: str) -> None:
        """Thread-safe answer update."""
        try:
            self.root.after(0, lambda: self.answer.set_answer(text))
        except Exception:
            pass

    def _set_system_safe(self, text: str) -> None:
        """Thread-safe system message update."""
        try:
            self.root.after(0, lambda: self.answer.set_system_message(text))
        except Exception:
            pass

    # ==================================================================
    # Run
    # ==================================================================

    def run(self) -> None:
        """Start the Tkinter main loop."""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            pass
        finally:
            self.cleanup()

    def cleanup(self) -> None:
        """Clean up resources on exit."""
        logger.info("[Shutdown] Cleaning up...")
        self.guard.stop()
        self.ai.stop()
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:
            pass
        logger.info("[Shutdown] FocusFlow stopped.")


# ==================================================================
# Entry Point
# ==================================================================

def main():
    """Application entry point."""
    # Ensure required directories exist
    for d in ["data", "data/screenshots", "temp", "logs", "knowledge_base"]:
        (BASE_DIR / d).mkdir(parents=True, exist_ok=True)

    app = FocusFlowApp()
    app.run()


if __name__ == "__main__":
    main()
