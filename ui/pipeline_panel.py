"""
FocusFlow — Pipeline Status Panel
Left-side Tkinter frame displaying OCR/LLM readiness indicators
and a scrollable, timestamped log output area.
"""

import logging
import tkinter as tk
from datetime import datetime
from tkinter import scrolledtext
from typing import Optional
from PIL import Image, ImageTk

logger = logging.getLogger("focusflow.ui.pipeline_panel")

# ---------------------------------------------------------------------------
# Theme constants
# ---------------------------------------------------------------------------
BG_DARK = "#1a1a2e"
BG_PANEL = "#16213e"
BG_INPUT = "#0f3460"
FG_GREEN = "#00ff88"
FG_GOLD = "#ffd700"
FG_RED = "#ff6b6b"
FG_TEXT = "#e0e0e0"
FG_DIM = "#888888"
ACCENT_PURPLE = "#7b2ff7"
FONT_MAIN = ("Consolas", 10)
FONT_TITLE = ("Consolas", 12, "bold")
FONT_SMALL = ("Consolas", 9)

# Dot colors for macOS-style traffic lights
_DOT_RED = "#ff5f56"
_DOT_YELLOW = "#ffbd2e"
_DOT_GREEN = "#27c93f"

_STARTUP_MESSAGE = (
    "FocusFlow is running!\n\n"
    "Press Ctrl+Shift+K to solve any screen.\n"
    "Panels hide in 3s — press Ctrl+Shift+H to toggle."
)


class PipelinePanel(tk.Frame):
    """Left-side panel showing pipeline readiness and log output."""

    def __init__(self, parent: tk.Misc, **kwargs) -> None:
        super().__init__(parent, bg=BG_DARK, **kwargs)
        self._build_ui()
        # Write the startup message into the log
        self.log(_STARTUP_MESSAGE)
        logger.debug("PipelinePanel initialized")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble every sub-widget inside the frame."""
        # ---- Title bar ------------------------------------------------
        title_bar = tk.Frame(self, bg=BG_PANEL, pady=6, padx=10)
        title_bar.pack(fill=tk.X)

        # Traffic-light dots (canvas circles)
        dot_canvas = tk.Canvas(
            title_bar,
            width=52,
            height=14,
            bg=BG_PANEL,
            highlightthickness=0,
        )
        dot_canvas.pack(side=tk.LEFT, padx=(0, 8))
        dot_canvas.create_oval(2, 2, 12, 12, fill=_DOT_RED, outline="")
        dot_canvas.create_oval(18, 2, 28, 12, fill=_DOT_YELLOW, outline="")
        dot_canvas.create_oval(34, 2, 44, 12, fill=_DOT_GREEN, outline="")

        title_label = tk.Label(
            title_bar,
            text="● Pipeline Status",
            font=FONT_TITLE,
            fg=FG_GREEN,
            bg=BG_PANEL,
        )
        title_label.pack(side=tk.LEFT)

        # --- Drag bindings to move the borderless Toplevel window -----
        self._drag_data = {"x": 0, "y": 0}
        for widget in (title_bar, title_label, dot_canvas):
            widget.bind("<Button-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_motion)

        # ---- Status section -------------------------------------------
        status_frame = tk.Frame(self, bg=BG_DARK, padx=12, pady=6)
        status_frame.pack(fill=tk.X)

        # OCR status row
        ocr_row = tk.Frame(status_frame, bg=BG_DARK)
        ocr_row.pack(fill=tk.X, pady=(2, 1))

        self._ocr_dot = tk.Label(
            ocr_row, text="●", font=FONT_MAIN, fg=FG_GREEN, bg=BG_DARK,
        )
        self._ocr_dot.pack(side=tk.LEFT)

        self._ocr_label = tk.Label(
            ocr_row,
            text="  OCR: Ready",
            font=FONT_MAIN,
            fg=FG_TEXT,
            bg=BG_DARK,
            anchor=tk.W,
        )
        self._ocr_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # LLM status row
        llm_row = tk.Frame(status_frame, bg=BG_DARK)
        llm_row.pack(fill=tk.X, pady=(1, 2))

        self._llm_dot = tk.Label(
            llm_row, text="●", font=FONT_MAIN, fg=FG_GOLD, bg=BG_DARK,
        )
        self._llm_dot.pack(side=tk.LEFT)

        self._llm_label = tk.Label(
            llm_row,
            text="  LLM: Loading model...",
            font=FONT_MAIN,
            fg=FG_TEXT,
            bg=BG_DARK,
            anchor=tk.W,
        )
        self._llm_label.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Image Preview Thumbnail
        self._preview_frame = tk.Frame(self, bg=BG_DARK, padx=12, pady=2)
        self._preview_frame.pack(fill=tk.X)
        self._preview_label = tk.Label(
            self._preview_frame,
            text="[No image captured]",
            font=FONT_SMALL,
            fg=FG_DIM,
            bg=BG_PANEL,
            relief=tk.FLAT,
            height=6,
        )
        self._preview_label.pack(fill=tk.X)

        # ---- Separator -----------------------------------------------
        sep = tk.Frame(self, bg=ACCENT_PURPLE, height=1)
        sep.pack(fill=tk.X, padx=10, pady=4)

        # ---- Log area -------------------------------------------------
        self._log_area = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            font=FONT_SMALL,
            bg=BG_INPUT,
            fg=FG_GREEN,
            insertbackground=FG_GREEN,
            selectbackground=ACCENT_PURPLE,
            selectforeground=FG_TEXT,
            relief=tk.FLAT,
            borderwidth=0,
            padx=8,
            pady=6,
            state=tk.DISABLED,
            cursor="arrow",
        )
        self._log_area.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 6))

        # Tag for timestamp styling
        self._log_area.tag_configure("timestamp", foreground=FG_DIM, font=FONT_SMALL)
        self._log_area.tag_configure("message", foreground=FG_GREEN, font=FONT_SMALL)

    def _on_drag_start(self, event: tk.Event) -> None:
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event: tk.Event) -> None:
        top = self.winfo_toplevel()
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = top.winfo_x() + dx
        y = top.winfo_y() + dy
        top.geometry(f"+{x}+{y}")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_ocr_status(self, message: str, ready: bool = True) -> None:
        """Update the OCR status indicator and text.

        Args:
            message: Human-readable status string, e.g. ``"Ready"`` or
                     ``"Not Found"``.
            ready:   ``True`` → green dot, ``False`` → red dot.
        """
        color = FG_GREEN if ready else FG_RED
        self._ocr_dot.configure(fg=color)
        self._ocr_label.configure(text=f"  OCR: {message}")
        logger.debug("OCR status -> %s (ready=%s)", message, ready)

    def set_llm_status(self, message: str, ready: bool = True) -> None:
        """Update the LLM status indicator and text.

        Args:
            message: Human-readable status string, e.g. ``"Ready"``,
                     ``"Loading..."``, or ``"Error"``.
            ready:   ``True`` -> green dot, ``False`` -> red dot.
                     When *message* contains ``"load"`` (case-insensitive) and
                     *ready* is ``False``, an amber dot is shown instead.
        """
        if not ready and "load" in message.lower():
            color = FG_GOLD  # amber while loading
        elif ready:
            color = FG_GREEN
        else:
            color = FG_RED
        self._llm_dot.configure(fg=color)
        self._llm_label.configure(text=f"  LLM: {message}")
        logger.debug("LLM status -> %s (ready=%s)", message, ready)

    def log(self, message: str) -> None:
        """Append a timestamped message to the log area and auto-scroll.

        Args:
            message: The text to append.  A newline is added automatically.
        """
        timestamp = datetime.now().strftime("[%H:%M:%S] ")
        self._log_area.configure(state=tk.NORMAL)
        self._log_area.insert(tk.END, timestamp, "timestamp")
        self._log_area.insert(tk.END, f"{message}\n", "message")

        # Trim oldest lines when log exceeds 200 lines
        try:
            content = self._log_area.get("1.0", "end-1c")
            lines = content.split("\n")
            if len(lines) > 200:
                num_to_delete = len(lines) - 200
                self._log_area.delete("1.0", f"{num_to_delete + 1}.0")
        except Exception as exc:
            logger.debug(f"Log trim error: {exc}")

        self._log_area.configure(state=tk.DISABLED)
        self._log_area.see(tk.END)

    def clear_log(self) -> None:
        """Remove all text from the log area."""
        self._log_area.configure(state=tk.NORMAL)
        self._log_area.delete("1.0", tk.END)
        self._log_area.configure(state=tk.DISABLED)
        logger.debug("Pipeline log cleared")

    def update_thumbnail(self, image: Optional[Image.Image]) -> None:
        """Render a scaled thumbnail of the captured image."""
        if image is None:
            self._preview_label.configure(image="", text="[No image captured]")
            self._preview_image = None
            return
            
        try:
            # Scale image to fit panel width (max width ~380, max height ~110)
            w, h = image.size
            max_w, max_h = 380, 110
            ratio = min(max_w / w, max_h / h)
            new_w = max(10, int(w * ratio))
            new_h = max(10, int(h * ratio))
            
            try:
                resampler = Image.Resampling.LANCZOS
            except AttributeError:
                try:
                    resampler = Image.LANCZOS
                except AttributeError:
                    resampler = Image.ANTIALIAS
                    
            thumb = image.resize((new_w, new_h), resampler)
            photo = ImageTk.PhotoImage(thumb)
            
            self._preview_label.configure(image=photo, text="")
            self._preview_image = photo  # keep reference
        except Exception as exc:
            logger.error(f"Failed to update thumbnail: {exc}")
            self._preview_label.configure(image="", text="[Preview Error]")
