"""
FocusFlow Settings Dialog
==========================
A dark-themed ``tk.Toplevel`` that exposes every configurable knob in
the application.  Sections are rendered as styled ``LabelFrame`` widgets
and the whole dialog loads its initial state from ``ConfigManager`` on
construction, writing everything back on *Save & Close*.
"""

from __future__ import annotations

import logging
import tkinter as tk
from tkinter import filedialog, ttk
from typing import Any, Optional

logger = logging.getLogger("focusflow.settings_dialog")

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

# Available online models
ONLINE_MODELS: list[str] = ["gpt-5"]


def _themed_labelframe(parent: tk.Misc, text: str) -> tk.LabelFrame:
    """Return a dark-styled ``LabelFrame``."""
    lf = tk.LabelFrame(
        parent,
        text=f"  {text}  ",
        font=FONT_MAIN,
        fg=FG_GOLD,
        bg=BG_DARK,
        bd=1,
        relief=tk.GROOVE,
        highlightbackground=FG_DIM,
        padx=10,
        pady=6,
    )
    return lf


def _mask_key(key: str) -> str:
    """Return a display-safe version of an API key (``sk-...abc``)."""
    if len(key) <= 8:
        return "****"
    return f"{key[:3]}...{key[-3:]}"


class SettingsDialog(tk.Toplevel):
    """Settings dialog for FocusFlow."""

    def __init__(
        self,
        parent: tk.Misc,
        config: Any,
        on_save: Optional[Any] = None,
        on_opacity_preview: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(parent, **kwargs)
        self.config = config
        self.on_save = on_save
        self.on_opacity_preview = on_opacity_preview
        self.title("FocusFlow Settings")
        self.configure(bg=BG_DARK)
        self.geometry("500x640")
        self.resizable(False, True)
        self.attributes("-topmost", True)

        # --- Tk variables (bound to widgets, synced to config) --------------
        self._mode_var = tk.StringVar(value=config.get("mode", "offline"))
        self._send_mode_var = tk.StringVar(
            value=config.get("online_send_mode", "ocr")
        )
        self._model_var = tk.StringVar(value=config.get("online_model", "gpt-5"))

        self._model_path_var = tk.StringVar(
            value=config.get("llm_model_path", "")
        )
        self._threads_var = tk.IntVar(value=config.get("llm_threads", 4))
        self._gpu_layers_var = tk.IntVar(value=config.get("llm_gpu_layers", 0))
        self._ctx_len_var = tk.IntVar(
            value=config.get("llm_context_length", 2048)
        )

        self._capture_mode_var = tk.StringVar(
            value=config.get("capture_mode", "region")
        )
        self._region_x_var = tk.IntVar(value=config.get("region_x", 0))
        self._region_y_var = tk.IntVar(value=config.get("region_y", 0))
        self._region_w_var = tk.IntVar(value=config.get("region_w", 800))
        self._region_h_var = tk.IntVar(value=config.get("region_h", 600))

        self._gray_var = tk.BooleanVar(
            value=config.get("ocr_preprocess_grayscale", True)
        )
        self._contrast_var = tk.BooleanVar(
            value=config.get("ocr_preprocess_contrast", False)
        )
        self._sharpen_var = tk.BooleanVar(
            value=config.get("ocr_preprocess_sharpen", False)
        )
        self._denoise_var = tk.BooleanVar(
            value=config.get("ocr_preprocess_denoise", False)
        )
        self._threshold_var = tk.BooleanVar(
            value=config.get("ocr_preprocess_threshold", False)
        )

        self._opacity_var = tk.IntVar(value=config.get("opacity", 240))
        self._answer_mode_var = tk.StringVar(
            value=config.get("answer_mode", "concise")
        )
        self._always_top_var = tk.BooleanVar(
            value=config.get("always_on_top", True)
        )

        # --- Scrollable body ------------------------------------------------
        self._canvas = tk.Canvas(self, bg=BG_DARK, highlightthickness=0)
        self._scrollbar = tk.Scrollbar(
            self, orient=tk.VERTICAL, command=self._canvas.yview
        )
        self._body = tk.Frame(self._canvas, bg=BG_DARK)

        self._body.bind(
            "<Configure>",
            lambda _e: self._canvas.configure(scrollregion=self._canvas.bbox("all")),
        )
        self._canvas.create_window((0, 0), window=self._body, anchor="nw")
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        # Mousewheel scrolling
        self._canvas.bind_all(
            "<MouseWheel>",
            lambda e: self._canvas.yview_scroll(-int(e.delta / 120), "units"),
        )

        # --- Sections -------------------------------------------------------
        self._build_mode_section()
        self._build_online_section()
        self._build_offline_section()
        self._build_capture_section()
        self._build_ocr_section()
        self._build_appearance_section()
        self._build_buttons()

        logger.info("SettingsDialog opened")

    # ======================================================================
    # Section builders
    # ======================================================================

    # --- 1. Mode -----------------------------------------------------------

    def _build_mode_section(self) -> None:
        lf = _themed_labelframe(self._body, "Mode")
        lf.pack(fill=tk.X, padx=10, pady=(10, 4))

        row = tk.Frame(lf, bg=BG_DARK)
        row.pack(fill=tk.X)
        for value, label in [
            ("offline", "Offline"),
            ("online", "Online"),
            ("combined", "Combined"),
        ]:
            tk.Radiobutton(
                row,
                text=label,
                variable=self._mode_var,
                value=value,
                font=FONT_MAIN,
                fg=FG_TEXT,
                bg=BG_DARK,
                selectcolor=BG_INPUT,
                activebackground=BG_DARK,
                activeforeground=FG_GREEN,
                cursor="hand2",
            ).pack(side=tk.LEFT, padx=8)

    # --- 2. Online settings ------------------------------------------------

    def _build_online_section(self) -> None:
        lf = _themed_labelframe(self._body, "Online Settings")
        lf.pack(fill=tk.X, padx=10, pady=4)

        # --- API key input --------------------------------------------------
        key_row = tk.Frame(lf, bg=BG_DARK)
        key_row.pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            key_row, text="API Key:", font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK
        ).pack(side=tk.LEFT)

        self._api_key_entry = tk.Entry(
            key_row,
            font=FONT_MAIN,
            fg=FG_TEXT,
            bg=BG_INPUT,
            insertbackground=FG_GREEN,
            relief=tk.FLAT,
            show="*",
            highlightthickness=1,
            highlightbackground=FG_DIM,
            highlightcolor=FG_GREEN,
        )
        self._api_key_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6, ipady=2)

        tk.Button(
            key_row,
            text="Add",
            font=FONT_SMALL,
            fg=BG_DARK,
            bg=FG_GREEN,
            activebackground=FG_GREEN,
            activeforeground=BG_DARK,
            relief=tk.FLAT,
            padx=8,
            cursor="hand2",
            command=self._add_api_key,
        ).pack(side=tk.LEFT)

        # --- Key listbox ----------------------------------------------------
        self._key_listbox = tk.Listbox(
            lf,
            height=3,
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
        self._key_listbox.pack(fill=tk.X, pady=(0, 4))
        self._refresh_key_list()

        tk.Button(
            lf,
            text="Remove Selected",
            font=FONT_SMALL,
            fg=FG_TEXT,
            bg=FG_RED,
            activebackground=FG_RED,
            activeforeground=FG_TEXT,
            relief=tk.FLAT,
            padx=8,
            cursor="hand2",
            command=self._remove_api_key,
        ).pack(anchor="w", pady=(0, 6))

        # --- Model dropdown -------------------------------------------------
        model_row = tk.Frame(lf, bg=BG_DARK)
        model_row.pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            model_row, text="Model:", font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK
        ).pack(side=tk.LEFT)

        model_combo = ttk.Combobox(
            model_row,
            textvariable=self._model_var,
            values=ONLINE_MODELS,
            state="readonly",
            font=FONT_SMALL,
            width=18,
        )
        model_combo.pack(side=tk.LEFT, padx=6)

        # --- Send mode ------------------------------------------------------
        send_row = tk.Frame(lf, bg=BG_DARK)
        send_row.pack(fill=tk.X)
        tk.Label(
            send_row, text="Send mode:", font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK
        ).pack(side=tk.LEFT)
        for val, label in [("ocr", "OCR"), ("image", "Image"), ("both", "Both")]:
            tk.Radiobutton(
                send_row,
                text=label,
                variable=self._send_mode_var,
                value=val,
                font=FONT_SMALL,
                fg=FG_TEXT,
                bg=BG_DARK,
                selectcolor=BG_INPUT,
                activebackground=BG_DARK,
                activeforeground=FG_GREEN,
                cursor="hand2",
            ).pack(side=tk.LEFT, padx=4)

    # --- 3. Offline settings -----------------------------------------------

    def _build_offline_section(self) -> None:
        lf = _themed_labelframe(self._body, "Offline Settings")
        lf.pack(fill=tk.X, padx=10, pady=4)

        # Model path
        path_row = tk.Frame(lf, bg=BG_DARK)
        path_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            path_row, text="Model path:", font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK
        ).pack(side=tk.LEFT)
        tk.Entry(
            path_row,
            textvariable=self._model_path_var,
            font=FONT_SMALL,
            fg=FG_TEXT,
            bg=BG_INPUT,
            insertbackground=FG_GREEN,
            relief=tk.FLAT,
            highlightthickness=1,
            highlightbackground=FG_DIM,
            highlightcolor=FG_GREEN,
        ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=4, ipady=2)
        tk.Button(
            path_row,
            text="Browse",
            font=FONT_SMALL,
            fg=BG_DARK,
            bg=FG_GOLD,
            activebackground=FG_GOLD,
            activeforeground=BG_DARK,
            relief=tk.FLAT,
            padx=6,
            cursor="hand2",
            command=self._browse_model_path,
        ).pack(side=tk.LEFT)

        # Numeric spinboxes row
        nums_row = tk.Frame(lf, bg=BG_DARK)
        nums_row.pack(fill=tk.X)
        for label_text, var, lo, hi in [
            ("Threads:", self._threads_var, 1, 16),
            ("GPU Layers:", self._gpu_layers_var, 0, 99),
            ("Context:", self._ctx_len_var, 512, 8192),
        ]:
            col = tk.Frame(nums_row, bg=BG_DARK)
            col.pack(side=tk.LEFT, padx=(0, 12))
            tk.Label(
                col, text=label_text, font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK
            ).pack(side=tk.LEFT)
            sb = tk.Spinbox(
                col,
                from_=lo,
                to=hi,
                textvariable=var,
                width=6,
                font=FONT_SMALL,
                fg=FG_TEXT,
                bg=BG_INPUT,
                buttonbackground=BG_PANEL,
                relief=tk.FLAT,
                highlightthickness=1,
                highlightbackground=FG_DIM,
                highlightcolor=FG_GREEN,
            )
            sb.pack(side=tk.LEFT, padx=2)

    # --- 4. Capture --------------------------------------------------------

    def _build_capture_section(self) -> None:
        lf = _themed_labelframe(self._body, "Capture")
        lf.pack(fill=tk.X, padx=10, pady=4)

        mode_row = tk.Frame(lf, bg=BG_DARK)
        mode_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            mode_row, text="Mode:", font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK
        ).pack(side=tk.LEFT)
        for val, label in [("fullscreen", "Fullscreen"), ("region", "Region")]:
            tk.Radiobutton(
                mode_row,
                text=label,
                variable=self._capture_mode_var,
                value=val,
                font=FONT_SMALL,
                fg=FG_TEXT,
                bg=BG_DARK,
                selectcolor=BG_INPUT,
                activebackground=BG_DARK,
                activeforeground=FG_GREEN,
                cursor="hand2",
            ).pack(side=tk.LEFT, padx=6)

        # Region coordinate spinboxes
        coord_row = tk.Frame(lf, bg=BG_DARK)
        coord_row.pack(fill=tk.X)
        for label_text, var in [
            ("X:", self._region_x_var),
            ("Y:", self._region_y_var),
            ("W:", self._region_w_var),
            ("H:", self._region_h_var),
        ]:
            tk.Label(
                coord_row, text=label_text, font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK
            ).pack(side=tk.LEFT, padx=(4, 0))
            tk.Spinbox(
                coord_row,
                from_=0,
                to=9999,
                textvariable=var,
                width=6,
                font=FONT_SMALL,
                fg=FG_TEXT,
                bg=BG_INPUT,
                buttonbackground=BG_PANEL,
                relief=tk.FLAT,
                highlightthickness=1,
                highlightbackground=FG_DIM,
                highlightcolor=FG_GREEN,
            ).pack(side=tk.LEFT, padx=2)

    # --- 5. OCR preprocessing ----------------------------------------------

    def _build_ocr_section(self) -> None:
        lf = _themed_labelframe(self._body, "OCR Preprocessing")
        lf.pack(fill=tk.X, padx=10, pady=4)

        row = tk.Frame(lf, bg=BG_DARK)
        row.pack(fill=tk.X)
        for label, var in [
            ("Grayscale", self._gray_var),
            ("Contrast", self._contrast_var),
            ("Sharpen", self._sharpen_var),
            ("Denoise", self._denoise_var),
            ("Threshold", self._threshold_var),
        ]:
            tk.Checkbutton(
                row,
                text=label,
                variable=var,
                font=FONT_SMALL,
                fg=FG_TEXT,
                bg=BG_DARK,
                selectcolor=BG_INPUT,
                activebackground=BG_DARK,
                activeforeground=FG_GREEN,
                cursor="hand2",
            ).pack(side=tk.LEFT, padx=4)

    # --- 6. Appearance -----------------------------------------------------

    def _build_appearance_section(self) -> None:
        lf = _themed_labelframe(self._body, "Appearance")
        lf.pack(fill=tk.X, padx=10, pady=4)

        # Opacity slider
        opa_row = tk.Frame(lf, bg=BG_DARK)
        opa_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            opa_row, text="Opacity:", font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK
        ).pack(side=tk.LEFT)

        self._opacity_label = tk.Label(
            opa_row,
            text=str(self._opacity_var.get()),
            font=FONT_SMALL,
            fg=FG_GREEN,
            bg=BG_DARK,
            width=4,
        )
        self._opacity_label.pack(side=tk.RIGHT)

        def _on_scale_change(v: str) -> None:
            val = int(float(v))
            self._opacity_label.configure(text=str(val))
            if self.on_opacity_preview:
                try:
                    self.on_opacity_preview(val)
                except Exception:
                    pass

        opa_scale = tk.Scale(
            opa_row,
            from_=30,
            to=255,
            orient=tk.HORIZONTAL,
            variable=self._opacity_var,
            showvalue=False,
            font=FONT_SMALL,
            fg=FG_TEXT,
            bg=BG_DARK,
            troughcolor=BG_INPUT,
            activebackground=FG_GREEN,
            highlightthickness=0,
            command=_on_scale_change,
        )
        opa_scale.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=6)

        # Answer mode
        ans_row = tk.Frame(lf, bg=BG_DARK)
        ans_row.pack(fill=tk.X, pady=(0, 4))
        tk.Label(
            ans_row, text="Answer mode:", font=FONT_SMALL, fg=FG_TEXT, bg=BG_DARK
        ).pack(side=tk.LEFT)
        for val, label in [("concise", "Concise"), ("detailed", "Detailed")]:
            tk.Radiobutton(
                ans_row,
                text=label,
                variable=self._answer_mode_var,
                value=val,
                font=FONT_SMALL,
                fg=FG_TEXT,
                bg=BG_DARK,
                selectcolor=BG_INPUT,
                activebackground=BG_DARK,
                activeforeground=FG_GREEN,
                cursor="hand2",
            ).pack(side=tk.LEFT, padx=6)

        # Always on top
        tk.Checkbutton(
            lf,
            text="Always on top",
            variable=self._always_top_var,
            font=FONT_SMALL,
            fg=FG_TEXT,
            bg=BG_DARK,
            selectcolor=BG_INPUT,
            activebackground=BG_DARK,
            activeforeground=FG_GREEN,
            cursor="hand2",
        ).pack(anchor="w")

    # --- Buttons -----------------------------------------------------------

    def _build_buttons(self) -> None:
        btn_frame = tk.Frame(self._body, bg=BG_DARK, pady=10)
        btn_frame.pack(fill=tk.X, padx=10)

        tk.Button(
            btn_frame,
            text="Save & Close",
            font=FONT_MAIN,
            fg=BG_DARK,
            bg=FG_GREEN,
            activebackground=FG_GREEN,
            activeforeground=BG_DARK,
            relief=tk.FLAT,
            padx=16,
            pady=4,
            cursor="hand2",
            command=self._save_and_close,
        ).pack(side=tk.LEFT, padx=(0, 10))

        tk.Button(
            btn_frame,
            text="Cancel",
            font=FONT_MAIN,
            fg=FG_TEXT,
            bg=FG_DIM,
            activebackground=FG_DIM,
            activeforeground=FG_TEXT,
            relief=tk.FLAT,
            padx=16,
            pady=4,
            cursor="hand2",
            command=self.destroy,
        ).pack(side=tk.LEFT)

    # ======================================================================
    # Internal helpers
    # ======================================================================

    def _refresh_key_list(self) -> None:
        """Reload the API-key listbox from config."""
        self._key_listbox.delete(0, tk.END)
        for key in self.config.get_api_keys():
            self._key_listbox.insert(tk.END, _mask_key(key))

    def _add_api_key(self) -> None:
        key = self._api_key_entry.get().strip()
        if not key:
            return
        self.config.add_api_key(key)
        self._api_key_entry.delete(0, tk.END)
        self._refresh_key_list()
        logger.info("API key added via settings dialog")

    def _remove_api_key(self) -> None:
        selection = self._key_listbox.curselection()
        if not selection:
            return
        index: int = selection[0]
        self.config.remove_api_key(index)
        self._refresh_key_list()
        logger.info("API key removed via settings dialog  index=%d", index)

    def _browse_model_path(self) -> None:
        path = filedialog.askopenfilename(
            title="Select GGUF Model",
            filetypes=[("GGUF models", "*.gguf"), ("All files", "*.*")],
        )
        if path:
            self._model_path_var.set(path)

    # ======================================================================
    # Save / Cancel
    # ======================================================================

    def _save_and_close(self) -> None:
        """Write all widget values back to config and close."""
        try:
            updates = {
                "mode": self._mode_var.get(),
                "online_model": self._model_var.get(),
                "online_send_mode": self._send_mode_var.get(),
                "llm_model_path": self._model_path_var.get(),
                "llm_threads": self._threads_var.get(),
                "llm_gpu_layers": self._gpu_layers_var.get(),
                "llm_context_length": self._ctx_len_var.get(),
                "capture_mode": self._capture_mode_var.get(),
                "region_x": self._region_x_var.get(),
                "region_y": self._region_y_var.get(),
                "region_w": self._region_w_var.get(),
                "region_h": self._region_h_var.get(),
                "ocr_preprocess_grayscale": self._gray_var.get(),
                "ocr_preprocess_contrast": self._contrast_var.get(),
                "ocr_preprocess_sharpen": self._sharpen_var.get(),
                "ocr_preprocess_denoise": self._denoise_var.get(),
                "ocr_preprocess_threshold": self._threshold_var.get(),
                "opacity": self._opacity_var.get(),
                "answer_mode": self._answer_mode_var.get(),
                "always_on_top": self._always_top_var.get(),
            }
            self.config.batch_update(updates)
            logger.info("Settings saved via dialog batch update")
        except Exception:
            logger.exception("Error saving settings")

        if self.on_save is not None:
            try:
                self.on_save()
            except Exception as exc:
                logger.error("Error executing on_save callback: %s", exc)

        self.destroy()

    def destroy(self) -> None:
        """Clean up bindings and destroy the window."""
        try:
            self.unbind_all("<MouseWheel>")
        except Exception:
            pass
        super().destroy()
