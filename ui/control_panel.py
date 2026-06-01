"""
FocusFlow Control Panel
========================
Central command surface for FocusFlow.  A borderless, always-on-top
Toplevel window with draggable title bar, hotkey reference, mode
tabs, mode selector, region info, and a manual question input.

All business-logic callbacks are injected via ``set_on_*`` methods
so the panel stays fully decoupled from the rest of the application.
"""

from __future__ import annotations

import logging
import tkinter as tk
from typing import Any, Callable, Optional

logger = logging.getLogger("focusflow.control_panel")

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


class ControlPanel(tk.Toplevel):
    """Borderless, always-on-top control surface for FocusFlow."""

    def __init__(self, parent: tk.Misc, config: Any, **kwargs: Any) -> None:
        super().__init__(parent, **kwargs)
        self.config = config

        # --- Window chrome --------------------------------------------------
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(bg=BG_DARK)

        # --- Callbacks (set later via public helpers) -----------------------
        self._on_solve: Optional[Callable[[], None]] = None
        self._on_region: Optional[Callable[[], None]] = None
        self._on_history: Optional[Callable[[], None]] = None
        self._on_settings: Optional[Callable[[], None]] = None
        self._on_manual_send: Optional[Callable[[str], None]] = None
        self._on_mode_change: Optional[Callable[[str, Optional[str]], None]] = None

        # --- Tk variables ---------------------------------------------------
        self._mode_var = tk.StringVar(value=self.config.get("mode", "offline"))
        self._send_mode_var = tk.StringVar(
            value=self.config.get("online_send_mode", "ocr")
        )
        self._region_text_var = tk.StringVar(value="Mode: Region (800×600)")

        # --- Build UI -------------------------------------------------------
        self._build_title_bar()
        self._build_hotkey_reference()
        self._build_mode_tabs()
        self._build_mode_selector()
        self._build_region_info()
        self._build_online_options()
        self._build_manual_input()

        # --- Initialise from config -----------------------------------------
        self._sync_from_config()

        logger.info("ControlPanel created")

    # ======================================================================
    # Title bar (draggable)
    # ======================================================================

    def _build_title_bar(self) -> None:
        bar = tk.Frame(self, bg=BG_PANEL, padx=6, pady=4)
        bar.pack(fill=tk.X)

        # Traffic-light dots
        dots_frame = tk.Frame(bar, bg=BG_PANEL)
        dots_frame.pack(side=tk.LEFT)
        for colour in (FG_RED, FG_GOLD, FG_GREEN):
            dot = tk.Canvas(
                dots_frame, width=12, height=12, bg=BG_PANEL, highlightthickness=0
            )
            dot.create_oval(2, 2, 11, 11, fill=colour, outline=colour)
            dot.pack(side=tk.LEFT, padx=2)

        # Title text
        title_label = tk.Label(
            bar,
            text="● FocusFlow Controls",
            font=FONT_TITLE,
            fg=FG_GREEN,
            bg=BG_PANEL,
        )
        title_label.pack(side=tk.LEFT, padx=8)

        # Close button (subtle)
        close_btn = tk.Label(
            bar, text="✕", font=FONT_MAIN, fg=FG_DIM, bg=BG_PANEL, cursor="hand2"
        )
        close_btn.pack(side=tk.RIGHT, padx=4)
        close_btn.bind("<Button-1>", lambda _e: self.withdraw())

        # --- Drag bindings --------------------------------------------------
        self._drag_data: dict[str, int] = {"x": 0, "y": 0}
        for widget in (bar, title_label):
            widget.bind("<Button-1>", self._on_drag_start)
            widget.bind("<B1-Motion>", self._on_drag_motion)

    def _on_drag_start(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag_motion(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        dx = event.x - self._drag_data["x"]
        dy = event.y - self._drag_data["y"]
        x = self.winfo_x() + dx
        y = self.winfo_y() + dy
        self.geometry(f"+{x}+{y}")

    # ======================================================================
    # Hotkey reference
    # ======================================================================

    def _build_hotkey_reference(self) -> None:
        frame = tk.Frame(self, bg=BG_DARK, padx=10, pady=4)
        frame.pack(fill=tk.X)

        header = tk.Label(
            frame,
            text="Hotkey Reference",
            font=FONT_MAIN,
            fg=FG_GOLD,
            bg=BG_DARK,
            anchor="w",
        )
        header.pack(fill=tk.X)

        sep = tk.Frame(frame, bg=FG_DIM, height=1)
        sep.pack(fill=tk.X, pady=(2, 4))

        hotkeys: list[tuple[str, str]] = [
            ("Solve Screen (Full)", "Ctrl + Shift + K"),
            ("Toggle Panels", "Ctrl + Shift + H"),
            ("Clear Answer", "Ctrl + Shift + Z"),
            ("Open Settings", "Ctrl + Shift + S"),
            ("Opacity +/−", "Ctrl + .  /  Ctrl + ,"),
        ]
        for action, shortcut in hotkeys:
            row = tk.Frame(frame, bg=BG_DARK)
            row.pack(fill=tk.X)
            tk.Label(
                row, text=f"  {action}", font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK, anchor="w"
            ).pack(side=tk.LEFT)
            tk.Label(
                row, text=shortcut, font=FONT_SMALL, fg=FG_GOLD, bg=BG_DARK, anchor="e"
            ).pack(side=tk.RIGHT)

    # ======================================================================
    # Mode tabs (AI Solve / Region Active / Settings)
    # ======================================================================

    def _build_mode_tabs(self) -> None:
        frame = tk.Frame(self, bg=BG_DARK, padx=10, pady=6)
        frame.pack(fill=tk.X)

        tab_defs: list[tuple[str, str, str, Callable[[], None]]] = [
            ("AI Solve", FG_GOLD, BG_DARK, self._handle_solve),
            ("Region Active", FG_GREEN, BG_DARK, self._handle_region),
            ("History", ACCENT_PURPLE, BG_DARK, self._handle_history),
            ("Settings", "#20b2aa", BG_DARK, self._handle_settings),
        ]

        for text, fg_colour, bg_colour, handler in tab_defs:
            btn = tk.Button(
                frame,
                text=text,
                font=FONT_MAIN,
                fg=BG_DARK,
                bg=fg_colour,
                activebackground=fg_colour,
                activeforeground=BG_DARK,
                relief=tk.FLAT,
                padx=12,
                pady=3,
                cursor="hand2",
                command=handler,
            )
            btn.pack(side=tk.LEFT, padx=3)

    # ======================================================================
    # Mode selector (Offline / Online / Combined)
    # ======================================================================

    def _build_mode_selector(self) -> None:
        frame = tk.Frame(self, bg=BG_DARK, padx=10, pady=4)
        frame.pack(fill=tk.X)

        tk.Label(
            frame, text="Mode:", font=FONT_MAIN, fg=FG_TEXT, bg=BG_DARK
        ).pack(side=tk.LEFT)

        for mode_value, label in [
            ("offline", "Offline"),
            ("online", "Online"),
            ("combined", "Combined"),
        ]:
            rb = tk.Radiobutton(
                frame,
                text=label,
                variable=self._mode_var,
                value=mode_value,
                font=FONT_MAIN,
                fg=FG_TEXT,
                bg=BG_DARK,
                selectcolor=BG_INPUT,
                activebackground=BG_DARK,
                activeforeground=FG_GREEN,
                indicatoron=True,
                command=self._handle_mode_change,
                cursor="hand2",
            )
            rb.pack(side=tk.LEFT, padx=6)

    # ======================================================================
    # Region info line
    # ======================================================================

    def _build_region_info(self) -> None:
        frame = tk.Frame(self, bg=BG_DARK, padx=10, pady=2)
        frame.pack(fill=tk.X)

        self._region_label = tk.Label(
            frame,
            textvariable=self._region_text_var,
            font=FONT_SMALL,
            fg=FG_DIM,
            bg=BG_DARK,
            anchor="w",
        )
        self._region_label.pack(fill=tk.X)

    # ======================================================================
    # Online sub-options (send mode)
    # ======================================================================

    def _build_online_options(self) -> None:
        self._online_frame = tk.Frame(self, bg=BG_DARK, padx=10, pady=4)
        # Visibility is toggled in _sync_from_config / update_mode_display.

        tk.Label(
            self._online_frame,
            text="Send mode:",
            font=FONT_MAIN,
            fg=FG_TEXT,
            bg=BG_DARK,
        ).pack(side=tk.LEFT)

        for val, label in [("ocr", "OCR"), ("image", "Image"), ("both", "Both")]:
            rb = tk.Radiobutton(
                self._online_frame,
                text=label,
                variable=self._send_mode_var,
                value=val,
                font=FONT_MAIN,
                fg=FG_TEXT,
                bg=BG_DARK,
                selectcolor=BG_INPUT,
                activebackground=BG_DARK,
                activeforeground=FG_GREEN,
                indicatoron=True,
                cursor="hand2",
            )
            rb.pack(side=tk.LEFT, padx=6)

    # ======================================================================
    # Manual question input
    # ======================================================================

    def _build_manual_input(self) -> None:
        frame = tk.Frame(self, bg=BG_DARK, padx=10, pady=6)
        frame.pack(fill=tk.X)

        tk.Label(
            frame,
            text="Manual Question:",
            font=FONT_SMALL,
            fg=FG_TEXT,
            bg=BG_DARK,
            anchor="w",
        ).pack(fill=tk.X)

        input_row = tk.Frame(frame, bg=BG_DARK)
        input_row.pack(fill=tk.X, pady=(2, 0))

        self._manual_entry = tk.Entry(
            input_row,
            font=FONT_MAIN,
            fg=FG_TEXT,
            bg=BG_INPUT,
            insertbackground=FG_GREEN,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=FG_DIM,
            highlightcolor=FG_GREEN,
        )
        self._manual_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, ipady=3)
        self._manual_entry.bind("<Return>", lambda _e: self._handle_manual_send())

        send_btn = tk.Button(
            input_row,
            text="Send",
            font=FONT_MAIN,
            fg=BG_DARK,
            bg=FG_GREEN,
            activebackground=FG_GREEN,
            activeforeground=BG_DARK,
            relief=tk.FLAT,
            padx=10,
            cursor="hand2",
            command=self._handle_manual_send,
        )
        send_btn.pack(side=tk.LEFT, padx=(6, 0))

    # ======================================================================
    # Internal handlers
    # ======================================================================

    def _handle_solve(self) -> None:
        if self._on_solve:
            try:
                self._on_solve()
            except Exception:
                logger.exception("Error in solve callback")

    def _handle_region(self) -> None:
        if self._on_region:
            try:
                self._on_region()
            except Exception:
                logger.exception("Error in region callback")

    def _handle_settings(self) -> None:
        if self._on_settings:
            try:
                self._on_settings()
            except Exception:
                logger.exception("Error in settings callback")

    def _handle_history(self) -> None:
        if self._on_history:
            try:
                self._on_history()
            except Exception:
                logger.exception("Error in history callback")

    def _handle_manual_send(self) -> None:
        text = self.get_manual_text()
        if not text:
            return
        if self._on_manual_send:
            try:
                self._on_manual_send(text)
            except Exception:
                logger.exception("Error in manual-send callback")

    def _handle_mode_change(self) -> None:
        new_mode = self._mode_var.get()
        self._toggle_online_options(new_mode)
        if self._on_mode_change:
            try:
                combined_active = None
                if new_mode == "combined":
                    combined_active = self.config.get("combined_active", "offline")
                self._on_mode_change(new_mode, combined_active)
            except Exception:
                logger.exception("Error in mode-change callback")

    def _toggle_online_options(self, mode: str) -> None:
        """Show or hide the online sub-options frame."""
        if mode in ("online", "combined"):
            self._online_frame.pack(fill=tk.X, after=self._region_label.master)
        else:
            self._online_frame.pack_forget()

    def _sync_from_config(self) -> None:
        """Pull current config values into the UI widgets."""
        mode = self.config.get("mode", "offline")
        self._mode_var.set(mode)
        self._toggle_online_options(mode)

        w = self.config.get("region_w", 800)
        h = self.config.get("region_h", 600)
        self.update_region_display(w, h)

        self._send_mode_var.set(self.config.get("online_send_mode", "ocr"))

    # ======================================================================
    # Public API
    # ======================================================================

    def set_on_solve(self, callback: Callable[[], None]) -> None:
        """Register a callback for the AI Solve button."""
        self._on_solve = callback

    def set_on_region(self, callback: Callable[[], None]) -> None:
        """Register a callback for the Region Active button."""
        self._on_region = callback

    def set_on_settings(self, callback: Callable[[], None]) -> None:
        """Register a callback for the Settings button."""
        self._on_settings = callback

    def set_on_history(self, callback: Callable[[], None]) -> None:
        """Register a callback for the History button."""
        self._on_history = callback

    def set_on_manual_send(
        self,
        callback: Callable[[str], None],
        get_text_func: Optional[Callable[[], str]] = None,
    ) -> None:
        """Register a callback and optional text-getter for manual send.

        If *get_text_func* is ``None`` the built-in
        :meth:`get_manual_text` is used.
        """
        self._on_manual_send = callback
        # get_text_func is accepted for interface parity but the panel
        # always reads from its own Entry widget.

    def set_mode_callback(self, callback: Callable[[str, Optional[str]], None]) -> None:
        """Register a callback invoked when the mode radio buttons change."""
        self._on_mode_change = callback

    def update_mode_display(
        self, mode: str, combined_active: Optional[str] = None
    ) -> None:
        """Programmatically update the mode indicator."""
        self._mode_var.set(mode)
        self._toggle_online_options(mode)

    def update_region_display(self, w: int, h: int) -> None:
        """Update the region dimensions text."""
        self._region_text_var.set(f"Mode: Region ({w}×{h})")

    def get_manual_text(self) -> str:
        """Return the current text from the manual question input."""
        return self._manual_entry.get().strip()

    def clear_manual_text(self) -> None:
        """Clear the manual question input."""
        self._manual_entry.delete(0, tk.END)
