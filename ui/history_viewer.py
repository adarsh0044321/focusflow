"""
FocusFlow — Interactive History Viewer
Sleek dark-themed Toplevel window that displays past capture history,
detailed OCR/AI metrics, text search filters, and screenshot overlays.
"""

import logging
import os
import tkinter as tk
from tkinter import scrolledtext, ttk
from typing import Any, Optional
from PIL import Image, ImageTk

logger = logging.getLogger("focusflow.ui.history_viewer")

# --- Theme constants -------------------------------------------------------
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


class HistoryViewerDialog(tk.Toplevel):
    """Sleek HUD panel to browse, search, and inspect capture history."""

    def __init__(self, parent: tk.Misc, history_manager: Any, guard: Any, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.history = history_manager
        self.guard = guard
        
        self.title("FocusFlow Learning Journal")
        self.geometry("860x600")
        self.configure(bg=BG_DARK)
        self.resizable(True, True)
        self.attributes("-topmost", True)
        
        # Apply screen capture exclusion
        self.update_idletasks()
        self.guard.protect_all_tk_windows(self)

        self._entries: list[dict[str, Any]] = []
        self._filtered_entries: list[dict[str, Any]] = []
        
        self._build_ui()
        self.reload_history()

    def _build_ui(self) -> None:
        """Create the split-pane search and detail layout."""
        # --- Top Search Bar ---
        search_frame = tk.Frame(self, bg=BG_PANEL, padx=12, pady=8)
        search_frame.pack(fill=tk.X, side=tk.TOP)

        tk.Label(
            search_frame, text="🔍 Search History:", font=FONT_MAIN, fg=FG_GOLD, bg=BG_PANEL
        ).pack(side=tk.LEFT, padx=(0, 8))

        self._search_var = tk.StringVar()
        self._search_var.trace_add("write", lambda *args: self._on_search_change())
        
        self._search_entry = tk.Entry(
            search_frame,
            textvariable=self._search_var,
            font=FONT_MAIN,
            fg=FG_TEXT,
            bg=BG_INPUT,
            insertbackground=FG_GREEN,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=FG_DIM,
            highlightcolor=FG_GREEN,
        )
        self._search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)

        tk.Button(
            search_frame,
            text="Reload",
            font=FONT_SMALL,
            fg=BG_DARK,
            bg=FG_GREEN,
            activebackground=FG_GREEN,
            activeforeground=BG_DARK,
            relief=tk.FLAT,
            padx=10,
            cursor="hand2",
            command=self.reload_history,
        ).pack(side=tk.RIGHT, padx=(8, 0))

        # --- Main Split Panes ---
        main_pane = tk.PanedWindow(self, orient=tk.HORIZONTAL, bg=BG_DARK, bd=0, sashwidth=4, sashrelief=tk.FLAT)
        main_pane.pack(fill=tk.BOTH, expand=True, padx=6, pady=6)

        # Left pane: Chronological list
        left_frame = tk.Frame(main_pane, bg=BG_DARK)
        main_pane.add(left_frame, width=280)

        tk.Label(
            left_frame, text="Capture Logs:", font=FONT_MAIN, fg=FG_TEXT, bg=BG_DARK, anchor="w"
        ).pack(fill=tk.X, pady=(0, 4))

        list_scroll = tk.Scrollbar(left_frame, orient=tk.VERTICAL)
        self._listbox = tk.Listbox(
            left_frame,
            yscrollcommand=list_scroll.set,
            font=FONT_SMALL,
            fg=FG_TEXT,
            bg=BG_INPUT,
            selectbackground=ACCENT_PURPLE,
            selectforeground=FG_TEXT,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=FG_DIM,
            highlightcolor=FG_GREEN,
        )
        list_scroll.config(command=self._listbox.yview)
        list_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self._listbox.pack(fill=tk.BOTH, expand=True)
        self._listbox.bind("<<ListboxSelect>>", self._on_item_select)

        # Right pane: Detail View
        self._right_frame = tk.Frame(main_pane, bg=BG_DARK, padx=8)
        main_pane.add(self._right_frame)

        # Detail Header Metrics
        self._metrics_label = tk.Label(
            self._right_frame,
            text="Select an entry to view details.",
            font=FONT_SMALL,
            fg=FG_GOLD,
            bg=BG_DARK,
            justify=tk.LEFT,
            anchor="w",
        )
        self._metrics_label.pack(fill=tk.X, pady=(0, 6))

        # Action row
        self._actions_frame = tk.Frame(self._right_frame, bg=BG_DARK)
        self._actions_frame.pack(fill=tk.X, pady=(0, 4))

        self._btn_screenshot = tk.Button(
            self._actions_frame,
            text="🖼️ View Screenshot",
            font=FONT_SMALL,
            fg=BG_DARK,
            bg=FG_GREEN,
            activebackground=FG_GREEN,
            activeforeground=BG_DARK,
            relief=tk.FLAT,
            padx=10,
            cursor="hand2",
            state=tk.DISABLED,
            command=self._show_screenshot_popup,
        )
        self._btn_screenshot.pack(side=tk.LEFT)

        # Tabs or split-text area for OCR text and Answer
        text_pane = tk.PanedWindow(self._right_frame, orient=tk.VERTICAL, bg=BG_DARK, bd=0, sashwidth=4, sashrelief=tk.FLAT)
        text_pane.pack(fill=tk.BOTH, expand=True, pady=4)

        # Upper: Question / OCR
        ocr_frame = tk.Frame(text_pane, bg=BG_DARK)
        text_pane.add(ocr_frame, height=180)
        tk.Label(ocr_frame, text="Captured Question / OCR:", font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK, anchor="w").pack(fill=tk.X)
        self._ocr_area = scrolledtext.ScrolledText(ocr_frame, wrap=tk.WORD, font=FONT_MAIN, bg=BG_INPUT, fg=FG_TEXT, relief=tk.FLAT, state=tk.DISABLED)
        self._ocr_area.pack(fill=tk.BOTH, expand=True)

        # Lower: Answer
        ans_frame = tk.Frame(text_pane, bg=BG_DARK)
        text_pane.add(ans_frame)
        tk.Label(ans_frame, text="AI Step-by-Step Solution:", font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK, anchor="w").pack(fill=tk.X)
        self._ans_area = scrolledtext.ScrolledText(ans_frame, wrap=tk.WORD, font=FONT_MAIN, bg=BG_INPUT, fg=FG_TEXT, relief=tk.FLAT, state=tk.DISABLED)
        self._ans_area.pack(fill=tk.BOTH, expand=True)

        self._ans_area.tag_configure("highlight", foreground=FG_GREEN, font=("Consolas", 10, "bold"))
        self._ans_area.tag_configure("normal", foreground=FG_TEXT)

    # ------------------------------------------------------------------
    # Data Loading
    # ------------------------------------------------------------------

    def reload_history(self) -> None:
        """Fetch chronological entries from history manager."""
        self._entries = self.history.get_entries(limit=0)  # load all
        self._filter_and_populate()

    def _filter_and_populate(self) -> None:
        """Apply search filter and refresh the Listbox."""
        query = self._search_var.get().strip().lower()
        self._listbox.delete(0, tk.END)
        self._filtered_entries = []

        for entry in self._entries:
            # Match search against timestamp, raw text, or answer
            text_match = (
                query in entry.get("timestamp", "").lower()
                or query in entry.get("raw_ocr", "").lower()
                or query in entry.get("answer", "").lower()
            )
            if not query or text_match:
                self._filtered_entries.append(entry)
                
                # Format list item
                ts = entry.get("timestamp", "N/A")
                mode = entry.get("mode", "offline").upper()
                snippet = entry.get("raw_ocr", "")[:30].strip().replace("\n", " ")
                if len(entry.get("raw_ocr", "")) > 30:
                    snippet += "..."
                
                self._listbox.insert(tk.END, f"{ts} [{mode}] {snippet}")

    def _on_search_change(self) -> None:
        self._filter_and_populate()

    # ------------------------------------------------------------------
    # Event Handlers
    # ------------------------------------------------------------------

    def _on_item_select(self, event: tk.Event) -> None:
        """Display details when a history item is selected."""
        selection = self._listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index >= len(self._filtered_entries):
            return
        
        entry = self._filtered_entries[index]
        
        # Display Metrics
        ts = entry.get("timestamp", "N/A")
        mode = entry.get("mode", "offline").upper()
        engine = entry.get("engine", "unknown")
        ocr_dur = entry.get("ocr_duration_s", 0.0)
        llm_dur = entry.get("llm_duration_s", 0.0)
        quality = entry.get("ocr_quality", "unknown").upper()
        
        metrics = (
            f"Timestamp: {ts}  |  Mode: {mode} ({engine})\n"
            f"OCR Duration: {ocr_dur}s  |  LLM Solving: {llm_dur}s  |  Quality: {quality}"
        )
        self._metrics_label.config(text=metrics)

        # Show raw OCR
        self._ocr_area.configure(state=tk.NORMAL)
        self._ocr_area.delete("1.0", tk.END)
        self._ocr_area.insert(tk.END, entry.get("raw_ocr", ""))
        self._ocr_area.configure(state=tk.DISABLED)

        # Show Answer (with styling)
        self._ans_area.configure(state=tk.NORMAL)
        self._ans_area.delete("1.0", tk.END)
        
        answer_text = entry.get("answer", "")
        for line in answer_text.splitlines(keepends=True):
            if line.lstrip().lower().startswith("answer:"):
                self._ans_area.insert(tk.END, line, "highlight")
            else:
                self._ans_area.insert(tk.END, line, "normal")
        self._ans_area.configure(state=tk.DISABLED)

        # Toggle screenshot button state
        scr_path = entry.get("screenshot_path", "")
        if scr_path and os.path.exists(scr_path):
            self._btn_screenshot.config(state=tk.NORMAL)
            self._selected_screenshot_path = scr_path
        else:
            self._btn_screenshot.config(state=tk.DISABLED)
            self._selected_screenshot_path = ""

    # ------------------------------------------------------------------
    # Screenshot Preview Popup
    # ------------------------------------------------------------------

    def _show_screenshot_popup(self) -> None:
        """Open a translucent glassmorphic window to show the PNG capture."""
        path = getattr(self, "_selected_screenshot_path", "")
        if not path or not os.path.exists(path):
            return

        try:
            # Create sub Toplevel popup
            popup = tk.Toplevel(self)
            popup.title("Screenshot Capture Preview")
            popup.configure(bg=BG_DARK)
            
            # Protect popup
            popup.update_idletasks()
            self.guard.protect_all_tk_windows(popup)
            
            # Open and scale image to fit screen dimensions nicely
            img = Image.open(path)
            w, h = img.size
            
            # Target width/height bounds
            max_w = min(1200, self.winfo_screenwidth() - 200)
            max_h = min(800, self.winfo_screenheight() - 200)
            
            if w > max_w or h > max_h:
                ratio = min(max_w / w, max_h / h)
                w = int(w * ratio)
                h = int(h * ratio)
                try:
                    resampler = Image.Resampling.LANCZOS
                except AttributeError:
                    resampler = Image.LANCZOS
                img = img.resize((w, h), resampler)
                
            popup.geometry(f"{w}x{h}+100+100")
            
            photo = ImageTk.PhotoImage(img)
            label = tk.Label(popup, image=photo, bg=BG_DARK)
            label.image = photo  # keep reference
            label.pack(fill=tk.BOTH, expand=True)
            
            # Add escape close binding
            popup.bind("<Escape>", lambda e: popup.destroy())
            
            # Top-most preview
            popup.attributes("-topmost", True)
            popup.focus_force()
        except Exception as exc:
            logger.error("Failed to open screenshot popup: %s", exc)
