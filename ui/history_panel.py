"""
FocusFlow — History Viewer Panel
================================
A beautifully styled, borderless, dark-themed Toplevel window to browse
and manage the interaction history.
"""

from __future__ import annotations

import logging
import os
import tkinter as tk
from tkinter import scrolledtext, messagebox
from typing import Any, Callable, Optional
from datetime import datetime
from PIL import Image, ImageTk

logger = logging.getLogger("focusflow.ui.history_panel")

# ---------------------------------------------------------------------------
# Theme constants (matching theme.py)
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

# traffic lights
_DOT_RED = "#ff5f56"
_DOT_YELLOW = "#ffbd2e"
_DOT_GREEN = "#27c93f"


class HistoryPanel(tk.Toplevel):
    """Borderless, always-on-top History Viewer panel."""

    def __init__(
        self,
        parent: tk.Misc,
        history_manager: Any,
        config: Any,
        on_restore: Callable[[str, str], None],
        **kwargs: Any
    ) -> None:
        super().__init__(parent, **kwargs)
        self.history = history_manager
        self.config = config
        self.on_restore = on_restore
        
        self.title("FocusFlow History")
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=BG_DARK)
        self.geometry("500x550")
        
        # Load opacity from config
        opacity = self.config.get("opacity", 240)
        self.attributes("-alpha", opacity / 255.0)

        self._entries: list[dict[str, Any]] = []
        self._selected_index: Optional[int] = None
        self._screenshot_win: Optional[tk.Toplevel] = None

        # Draggable title bar data
        self._drag_data = {"x": 0, "y": 0}

        self._build_ui()
        self.refresh()
        
        logger.info("HistoryPanel created")

    # ======================================================================
    # UI construction
    # ======================================================================

    def _build_ui(self) -> None:
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
            text="● Interaction History",
            font=FONT_TITLE,
            fg=FG_GREEN,
            bg=BG_PANEL,
        )
        title_label.pack(side=tk.LEFT)

        close_btn = tk.Label(
            title_bar, text="✕", font=FONT_MAIN, fg=FG_DIM, bg=BG_PANEL, cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT, padx=4)
        close_btn.bind("<Button-1>", lambda _e: self.destroy())

        # Drag bindings to move the Toplevel window
        for widget in (title_bar, title_label, dot_canvas):
            widget.bind("<Button-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_motion)

        # ---- Body split layout -----------------------------------------
        # Left half: Listbox of history entries
        # Right half: Text display of detail
        split_frame = tk.Frame(self, bg=BG_DARK, padx=8, pady=8)
        split_frame.pack(fill=tk.BOTH, expand=True)

        left_pane = tk.Frame(split_frame, bg=BG_DARK)
        left_pane.pack(side=tk.LEFT, fill=tk.Y, width=180, padx=(0, 6))

        tk.Label(
            left_pane, text="Past Solves:", font=FONT_SMALL, fg=FG_GOLD, bg=BG_DARK, anchor="w"
        ).pack(fill=tk.X, pady=(0, 2))

        # Listbox with Scrollbar
        list_scroll = tk.Scrollbar(left_pane, orient=tk.VERTICAL)
        self._listbox = tk.Listbox(
            left_pane,
            font=FONT_SMALL,
            bg=BG_INPUT,
            fg=FG_TEXT,
            relief=tk.FLAT,
            selectbackground=ACCENT_PURPLE,
            selectforeground=FG_TEXT,
            highlightthickness=1,
            highlightbackground=FG_DIM,
            highlightcolor=FG_GREEN,
            yscrollcommand=list_scroll.set
        )
        list_scroll.config(command=self._listbox.yview)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._on_entry_selected)

        # Right half: details
        right_pane = tk.Frame(split_frame, bg=BG_DARK)
        right_pane.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        tk.Label(
            right_pane, text="Details:", font=FONT_SMALL, fg=FG_GOLD, bg=BG_DARK, anchor="w"
        ).pack(fill=tk.X, pady=(0, 2))

        # ScrolledText for QA detail
        self._detail_area = scrolledtext.ScrolledText(
            right_pane,
            wrap=tk.WORD,
            font=FONT_SMALL,
            bg=BG_INPUT,
            fg=FG_TEXT,
            relief=tk.FLAT,
            borderwidth=0,
            insertbackground=FG_TEXT,
            selectbackground=ACCENT_PURPLE,
            selectforeground=FG_TEXT,
            state=tk.DISABLED
        )
        self._detail_area.pack(fill=tk.BOTH, expand=True)
        
        self._detail_area.tag_configure("header", foreground=FG_GOLD, font=("Consolas", 9, "bold"))
        self._detail_area.tag_configure("ocr", foreground=FG_TEXT)
        self._detail_area.tag_configure("highlight", foreground=FG_GREEN, font=("Consolas", 9, "bold"))
        self._detail_area.tag_configure("system", foreground=FG_DIM, font=("Consolas", 8, "italic"))

        # ---- Button bar ------------------------------------------------
        btn_frame = tk.Frame(self, bg=BG_DARK, padx=8, pady=4)
        btn_frame.pack(fill=tk.X, side=tk.BOTTOM)

        btn_style = dict(
            font=FONT_SMALL,
            relief=tk.FLAT,
            cursor="hand2",
            padx=10,
            pady=3,
            borderwidth=0,
            activeforeground=BG_DARK
        )

        self._btn_view_ss = tk.Button(
            btn_frame,
            text="🖼 View Screenshot",
            bg=FG_GOLD,
            fg=BG_DARK,
            activebackground="#e6c200",
            state=tk.DISABLED,
            command=self._handle_view_screenshot,
            **btn_style
        )
        self._btn_view_ss.pack(side=tk.LEFT, padx=(0, 4))

        self._btn_restore = tk.Button(
            btn_frame,
            text="⟳ Restore to UI",
            bg=FG_GREEN,
            fg=BG_DARK,
            activebackground="#00cc6a",
            state=tk.DISABLED,
            command=self._handle_restore,
            **btn_style
        )
        self._btn_restore.pack(side=tk.LEFT, padx=(0, 4))

        self._btn_delete = tk.Button(
            btn_frame,
            text="✕ Delete",
            bg=FG_RED,
            fg=BG_DARK,
            activebackground="#e05555",
            state=tk.DISABLED,
            command=self._handle_delete,
            **btn_style
        )
        self._btn_delete.pack(side=tk.LEFT, padx=(0, 4))

        self._btn_clear_all = tk.Button(
            btn_frame,
            text="✕ Clear All",
            bg=FG_DIM,
            fg=BG_DARK,
            activebackground="#666666",
            command=self._handle_clear_all,
            **btn_style
        )
        self._btn_clear_all.pack(side=tk.RIGHT)

    # ======================================================================
    # Drag and Drop handlers
    # ======================================================================

    def _on_drag_start(self, event: tk.Event) -> None:
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event: tk.Event) -> None:
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        self.geometry(f"+{x}+{y}")

    # ======================================================================
    # Data management
    # ======================================================================

    def refresh(self) -> None:
        """Reload entries from the HistoryManager and rebuild the list."""
        self._listbox.delete(0, tk.END)
        self._entries = self.history.get_entries(limit=100) # list of last 100 entries, newest first
        
        for entry in self._entries:
            ts = entry.get("timestamp", "")
            # Clean timestamp to extract just time and short date
            try:
                dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                display_ts = dt.strftime("%m-%d %H:%M")
            except ValueError:
                display_ts = ts[:11]
                
            mode = entry.get("capture_mode", "region")
            ocr_snippet = entry.get("cleaned_ocr", "")[:15].replace("\n", " ").strip()
            
            self._listbox.insert(tk.END, f"{display_ts} [{mode}] {ocr_snippet}...")
            
        self._clear_detail()
        logger.debug("HistoryPanel refreshed with %d entries", len(self._entries))

    def _clear_detail(self) -> None:
        self._detail_area.configure(state=tk.NORMAL)
        self._detail_area.delete("1.0", tk.END)
        self._detail_area.configure(state=tk.DISABLED)
        self._selected_index = None
        self._btn_view_ss.configure(state=tk.DISABLED)
        self._btn_restore.configure(state=tk.DISABLED)
        self._btn_delete.configure(state=tk.DISABLED)

    def _on_entry_selected(self, _event: tk.Event) -> None:
        selection = self._listbox.curselection()
        if not selection:
            return
        
        idx = selection[0]
        self._selected_index = idx
        entry = self._entries[idx]

        # Enable action buttons
        self._btn_restore.configure(state=tk.NORMAL)
        self._btn_delete.configure(state=tk.NORMAL)
        
        ss_path = entry.get("screenshot_path", "")
        if ss_path and os.path.exists(ss_path):
            self._btn_view_ss.configure(state=tk.NORMAL)
        else:
            self._btn_view_ss.configure(state=tk.DISABLED)

        # Draw details in text area
        self._detail_area.configure(state=tk.NORMAL)
        self._detail_area.delete("1.0", tk.END)

        # Header metadata
        meta = (
            f"--- Entry Details ---\n"
            f"Timestamp: {entry.get('timestamp')}\n"
            f"Mode:      {entry.get('mode')} ({entry.get('capture_mode')})\n"
            f"Answer Mode: {entry.get('answer_mode')}\n"
            f"OCR Quality: {entry.get('ocr_quality')} "
            f"(extracted in {entry.get('ocr_duration_s', 0.0)}s)\n"
            f"LLM Solve Duration: {entry.get('llm_duration_s', 0.0)}s\n"
            f"---------------------\n\n"
        )
        self._detail_area.insert(tk.END, meta, "system")

        # Cleaned OCR
        self._detail_area.insert(tk.END, "● Question Text (Cleaned OCR):\n", "header")
        self._detail_area.insert(tk.END, entry.get("cleaned_ocr", "") + "\n\n", "ocr")

        # Answer
        self._detail_area.insert(tk.END, "● AI Answer:\n", "header")
        answer_text = entry.get("answer", "")
        for line in answer_text.splitlines(keepends=True):
            if line.lstrip().lower().startswith("answer:"):
                self._detail_area.insert(tk.END, line, "highlight")
            else:
                self._detail_area.insert(tk.END, line, "ocr")

        self._detail_area.configure(state=tk.DISABLED)

    # ======================================================================
    # Button callbacks
    # ======================================================================

    def _handle_view_screenshot(self) -> None:
        if self._selected_index is None:
            return
        entry = self._entries[self._selected_index]
        ss_path = entry.get("screenshot_path", "")
        if not ss_path or not os.path.exists(ss_path):
            messagebox.showerror("Error", "Screenshot file not found.", parent=self)
            return

        # Close existing viewer if open
        if self._screenshot_win is not None:
            try:
                self._screenshot_win.destroy()
            except Exception:
                pass

        try:
            self._screenshot_win = tk.Toplevel(self)
            self._screenshot_win.title("FocusFlow Screenshot")
            self._screenshot_win.configure(bg=BG_DARK)
            self._screenshot_win.attributes("-topmost", True)
            
            # Load and display screenshot
            img = Image.open(ss_path)
            
            # Resize image to max 800x600 for convenient viewing
            img.thumbnail((800, 600))
            photo = ImageTk.PhotoImage(img)
            
            # Label to display
            lbl = tk.Label(self._screenshot_win, image=photo, bg=BG_DARK)
            lbl.image = photo # hold reference
            lbl.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
            
            # Close button
            tk.Button(
                self._screenshot_win,
                text="Close",
                font=FONT_SMALL,
                bg=FG_DIM,
                fg=BG_DARK,
                command=self._screenshot_win.destroy,
                relief=tk.FLAT,
                cursor="hand2"
            ).pack(side=tk.BOTTOM, pady=(0, 10))

            # Protect screenshot window from capture as well!
            if hasattr(self.master, "guard"):
                self.master.guard.protect_all_tk_windows(self._screenshot_win)
                
        except Exception as e:
            logger.error("Failed to view screenshot: %s", e)
            messagebox.showerror("Error", f"Failed to load screenshot: {e}", parent=self)

    def _handle_restore(self) -> None:
        if self._selected_index is None:
            return
        entry = self._entries[self._selected_index]
        ocr = entry.get("cleaned_ocr", "")
        ans = entry.get("answer", "")
        try:
            self.on_restore(ocr, ans)
            logger.info("Restored history entry to main panel")
        except Exception as e:
            logger.error("Failed to restore history entry: %s", e)

    def _handle_delete(self) -> None:
        if self._selected_index is None:
            return
        entry = self._entries[self._selected_index]
        
        # We need to find the index of this entry in the main history manager's _entries list
        # Since self.history._entries is ordered oldest-first, and self._entries is newest-first,
        # we can search by matching timestamp and content.
        ts = entry.get("timestamp")
        
        # Remove from history manager
        with self.history._lock:
            match_idx = None
            for idx, e in enumerate(self.history._entries):
                if e.get("timestamp") == ts:
                    match_idx = idx
                    break
            
            if match_idx is not None:
                self.history._entries.pop(match_idx)
                self.history._save()
                logger.info(f"Deleted history entry with timestamp {ts}")
                
        self.refresh()

    def _handle_clear_all(self) -> None:
        if not messagebox.askyesno("Confirm Clear", "Are you sure you want to delete ALL interaction history? This cannot be undone.", parent=self):
            return
            
        self.history.clear()
        self.refresh()
        logger.info("Cleared all history entries")
