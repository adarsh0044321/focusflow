"""
FocusFlow — AI Answer Panel
Right-side Tkinter frame displaying AI-generated answers,
action buttons, and a system status message.
"""

import logging
import tkinter as tk
from tkinter import scrolledtext, simpledialog
from typing import Callable, Optional

logger = logging.getLogger("focusflow.ui.answer_panel")

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

_DEFAULT_SYSTEM_MSG = "[System] FocusFlow local AI ready."
_FOOTER_TEXT = "Ctrl+Shift+K = solve screen  |  Ctrl+Shift+H = toggle panels"


class AnswerPanel(tk.Frame):
    """Right-side panel showing AI answers, action buttons, and status."""

    def __init__(self, parent: tk.Misc, **kwargs) -> None:
        super().__init__(parent, bg=BG_DARK, **kwargs)

        # Callback slots (set via public helpers)
        self._on_rerun: Optional[Callable[[], None]] = None
        self._on_manual_q: Optional[Callable[[], None]] = None
        self._on_clear: Optional[Callable[[], None]] = None
        self._on_chat_send: Optional[Callable[[str], None]] = None

        self._build_ui()
        logger.debug("AnswerPanel initialized")

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Assemble every sub-widget inside the frame."""
        # ---- Title bar ------------------------------------------------
        title_bar = tk.Frame(self, bg=BG_PANEL, pady=6, padx=10)
        title_bar.pack(fill=tk.X)

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
            text="● AI Answer",
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

        # ---- Button row -----------------------------------------------
        btn_frame = tk.Frame(self, bg=BG_DARK, padx=10, pady=6)
        btn_frame.pack(fill=tk.X)

        btn_style: dict = dict(
            font=FONT_MAIN,
            relief=tk.FLAT,
            cursor="hand2",
            padx=12,
            pady=4,
            borderwidth=0,
            activeforeground=BG_DARK,
        )

        self._btn_rerun = tk.Button(
            btn_frame,
            text="⟳ Re-run LLM",
            bg=FG_GREEN,
            fg=BG_DARK,
            activebackground="#00cc6a",
            command=self._handle_rerun,
            **btn_style,
        )
        self._btn_rerun.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_manual = tk.Button(
            btn_frame,
            text="✎ Manual Q",
            bg=FG_GOLD,
            fg=BG_DARK,
            activebackground="#e6c200",
            command=self._handle_manual_q,
            **btn_style,
        )
        self._btn_manual.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_clear = tk.Button(
            btn_frame,
            text="✕ Clear",
            bg=FG_RED,
            fg=BG_DARK,
            activebackground="#e05555",
            command=self._handle_clear,
            **btn_style,
        )
        self._btn_clear.pack(side=tk.LEFT, padx=(0, 6))

        self._btn_copy = tk.Button(
            btn_frame,
            text="📋 Copy",
            bg=ACCENT_PURPLE,
            fg=FG_TEXT,
            activebackground="#611cc9",
            command=self._handle_copy,
            **btn_style,
        )
        self._btn_copy.pack(side=tk.LEFT)

        # ---- System message -------------------------------------------
        self._sys_msg_label = tk.Label(
            self,
            text=_DEFAULT_SYSTEM_MSG,
            font=FONT_SMALL,
            fg=FG_DIM,
            bg=BG_DARK,
            anchor=tk.W,
            padx=12,
            pady=2,
        )
        self._sys_msg_label.pack(fill=tk.X)

        # ---- Separator ------------------------------------------------
        sep = tk.Frame(self, bg=ACCENT_PURPLE, height=1)
        sep.pack(fill=tk.X, padx=10, pady=4)

        # ---- Answer display -------------------------------------------
        self._answer_area = scrolledtext.ScrolledText(
            self,
            wrap=tk.WORD,
            font=FONT_MAIN,
            bg=BG_INPUT,
            fg=FG_TEXT,
            insertbackground=FG_TEXT,
            selectbackground=ACCENT_PURPLE,
            selectforeground=FG_TEXT,
            relief=tk.FLAT,
            borderwidth=0,
            padx=10,
            pady=8,
            state=tk.DISABLED,
            cursor="arrow",
        )
        self._answer_area.pack(fill=tk.BOTH, expand=True, padx=6, pady=(0, 4))

        # Text tags for answer formatting
        self._answer_area.tag_configure(
            "answer", foreground=FG_TEXT, font=FONT_MAIN,
        )
        self._answer_area.tag_configure(
            "highlight", foreground=FG_GREEN, font=("Consolas", 10, "bold"),
        )

        # ---- Footer / hotkey hints ------------------------------------
        footer = tk.Label(
            self,
            text=_FOOTER_TEXT,
            font=FONT_SMALL,
            fg=FG_DIM,
            bg=BG_PANEL,
            anchor=tk.CENTER,
            padx=6,
            pady=4,
        )
        footer.pack(fill=tk.X, side=tk.BOTTOM)

        # ---- Chat Follow-up entry -------------------------------------
        self._chat_frame = tk.Frame(self, bg=BG_DARK, padx=10, pady=4)
        self._chat_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        tk.Label(
            self._chat_frame, text="💬 Chat Follow-up:", font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK
        ).pack(fill=tk.X, anchor="w", pady=(0, 2))
        
        entry_row = tk.Frame(self._chat_frame, bg=BG_DARK)
        entry_row.pack(fill=tk.X)
        
        self._chat_entry = tk.Entry(
            entry_row,
            font=FONT_MAIN,
            fg=FG_TEXT,
            bg=BG_INPUT,
            insertbackground=FG_GREEN,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=FG_DIM,
            highlightcolor=FG_GREEN,
        )
        self._chat_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self._chat_entry.bind("<Return>", lambda _e: self._handle_chat_send())
        
        self._btn_chat_send = tk.Button(
            entry_row,
            text="Send",
            font=FONT_SMALL,
            fg=BG_DARK,
            bg=FG_GREEN,
            activebackground=FG_GREEN,
            activeforeground=BG_DARK,
            relief=tk.FLAT,
            padx=10,
            cursor="hand2",
            command=self._handle_chat_send,
        )
        self._btn_chat_send.pack(side=tk.LEFT, padx=(6, 0))

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
    # Internal button handlers
    # ------------------------------------------------------------------

    def _handle_rerun(self) -> None:
        if self._on_rerun is not None:
            try:
                self._on_rerun()
            except Exception as exc:
                logger.error("Re-run callback error: %s", exc)
        else:
            logger.debug("Re-run pressed but no callback set")

    def _handle_manual_q(self) -> None:
        if self._on_manual_q is not None:
            try:
                self._on_manual_q()
            except Exception as exc:
                logger.error("Manual Q callback error: %s", exc)
        else:
            logger.debug("Manual Q pressed but no callback set")

    def _handle_clear(self) -> None:
        self.clear_answer()
        if self._on_clear is not None:
            try:
                self._on_clear()
            except Exception as exc:
                logger.error("Clear callback error: %s", exc)

    def _handle_copy(self) -> None:
        try:
            text = self._answer_area.get("1.0", tk.END).strip()
            if text:
                self.clipboard_clear()
                self.clipboard_append(text)
                self.set_system_message("[System] Copied to clipboard!")
                logger.info("Copied answer to clipboard")
            else:
                self.set_system_message("[System] No answer to copy.")
        except Exception as exc:
            logger.error("Failed to copy to clipboard: %s", exc)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def set_answer(self, text: str) -> None:
        """Display *text* in the answer area, replacing any previous content.

        Lines beginning with ``Answer:`` are highlighted in green.
        """
        self._answer_area.configure(state=tk.NORMAL)
        self._answer_area.delete("1.0", tk.END)

        for line in text.splitlines(keepends=True):
            stripped = line.lstrip()
            if stripped.lower().startswith("answer:"):
                self._answer_area.insert(tk.END, line, "highlight")
            else:
                self._answer_area.insert(tk.END, line, "answer")

        self._answer_area.configure(state=tk.DISABLED)
        self._answer_area.see("1.0")
        logger.debug("Answer displayed (%d chars)", len(text))

    def clear_answer(self) -> None:
        """Clear the answer display area."""
        self._answer_area.configure(state=tk.NORMAL)
        self._answer_area.delete("1.0", tk.END)
        self._answer_area.configure(state=tk.DISABLED)
        logger.debug("Answer area cleared")

    def set_system_message(self, msg: str) -> None:
        """Update the small system message line below the buttons.

        Args:
            msg: Status text, e.g. ``"[System] Processing..."``
        """
        self._sys_msg_label.configure(text=msg)

    def set_on_rerun(self, callback: Callable[[], None]) -> None:
        """Register a callback invoked when the **Re-run LLM** button is
        pressed."""
        self._on_rerun = callback

    def set_on_manual_q(self, callback: Callable[[], None]) -> None:
        """Register a callback invoked when the **Manual Q** button is
        pressed."""
        self._on_manual_q = callback

    def set_on_clear(self, callback: Callable[[], None]) -> None:
        """Register a callback invoked when the **Clear** button is
        pressed (after the answer area has already been cleared)."""
        self._on_clear = callback

    def get_manual_question(self) -> Optional[str]:
        """Open a simple input dialog and return the user's question.

        Returns:
            The typed question string, or ``None`` if the dialog was
            cancelled.
        """
        # The dialog inherits the dark styling from the toplevel where
        # possible.  On Windows, ``simpledialog`` always uses the system
        # chrome, but the prompt text is still readable.
        question = simpledialog.askstring(
            "FocusFlow — Manual Question",
            "Type your question:",
            parent=self,
        )
        if question and question.strip():
            logger.debug("Manual question entered (%d chars)", len(question))
            return question.strip()
        return None

    def _handle_chat_send(self) -> None:
        text = self._chat_entry.get().strip()
        if not text:
            return
        if self._on_chat_send:
            try:
                self._on_chat_send(text)
            except Exception as exc:
                logger.error("Chat send callback error: %s", exc)
        self._chat_entry.delete(0, tk.END)

    def set_on_chat_send(self, callback: Callable[[str], None]) -> None:
        """Register a callback for the follow-up chat Send action."""
        self._on_chat_send = callback

    def append_chat_message(self, text: str, is_user: bool = False) -> None:
        """Append a follow-up chat message to the answer area."""
        self._answer_area.configure(state=tk.NORMAL)
        
        # Add a visual separator if this is the start of follow-up chat
        content = self._answer_area.get("1.0", tk.END).strip()
        if content and "💬 Follow-up Chat" not in content:
            self._answer_area.insert(tk.END, "\n\n" + "─" * 40 + "\n💬 Follow-up Chat\n")
            
        if is_user:
            self._answer_area.insert(tk.END, f"\n> User: {text}\n", "highlight")
        else:
            self._answer_area.insert(tk.END, f"\nFocusFlow:\n", "highlight")
            for line in text.splitlines(keepends=True):
                stripped = line.lstrip()
                if stripped.lower().startswith("answer:"):
                    self._answer_area.insert(tk.END, line, "highlight")
                else:
                    self._answer_area.insert(tk.END, line, "answer")
                    
        self._answer_area.configure(state=tk.DISABLED)
        self._answer_area.see(tk.END)
