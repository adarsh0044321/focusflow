"""FocusFlow – Screen capture module.

Uses the ``mss`` library for fast, cross-monitor screen grabs and provides
an interactive Tkinter overlay for drag-selecting a capture region.
"""

from __future__ import annotations

import logging
import tkinter as tk
from typing import Any, Callable, Optional

import mss
import mss.tools
from PIL import Image

logger = logging.getLogger("focusflow.capture")


class ScreenCapture:
    """Capture screenshots (full-screen or region) and let the user
    interactively pick a capture region via a translucent overlay."""

    def __init__(self, config: Any) -> None:
        self.config = config
        self.logger = logger

    # ------------------------------------------------------------------
    # Public capture helpers
    # ------------------------------------------------------------------

    def capture_fullscreen(self, monitor_index: int = 1) -> Image.Image:
        """Capture a full monitor.  Returns a PIL ``Image``.

        Parameters
        ----------
        monitor_index:
            1-based index into ``mss.monitors``.  Index 0 is the
            virtual screen that spans *all* monitors.
        """
        with mss.mss() as sct:
            if self.config.get("capture_all_screens"):
                raw = sct.grab(sct.monitors[0])  # all monitors combined
            else:
                idx = min(monitor_index, len(sct.monitors) - 1)
                raw = sct.grab(sct.monitors[idx])
            return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

    def capture_region(self) -> Image.Image:
        """Capture the rectangular region defined in the current config.

        Config keys used: ``region_x``, ``region_y``, ``region_w``,
        ``region_h``.
        """
        x: int = self.config.get("region_x", 0)
        y: int = self.config.get("region_y", 0)
        w: int = self.config.get("region_w", 400)
        h: int = self.config.get("region_h", 300)

        if w <= 0 or h <= 0:
            self.logger.warning(
                "Invalid region dimensions (%d×%d) – falling back to full screen.",
                w,
                h,
            )
            return self.capture_fullscreen()

        region = {"left": x, "top": y, "width": w, "height": h}
        with mss.mss() as sct:
            raw = sct.grab(region)
            return Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")

    def capture(self) -> Image.Image:
        """Capture based on the current ``capture_mode`` config value.

        * ``"region"`` – uses :pymeth:`capture_region`
        * anything else – uses :pymeth:`capture_fullscreen`
        """
        mode: str = self.config.get("capture_mode", "fullscreen")
        if mode == "region":
            return self.capture_region()
        return self.capture_fullscreen()

    # ------------------------------------------------------------------
    # Interactive region selector
    # ------------------------------------------------------------------

    def select_region_interactive(
        self,
        callback: Callable[[int, int, int, int], None],
    ) -> None:
        """Open a translucent fullscreen overlay and let the user
        click-and-drag to select a rectangular region.

        On mouse-release the overlay is destroyed and *callback* is
        invoked with ``(x, y, width, height)`` in screen coordinates.

        If the user presses **Escape** the overlay is dismissed without
        calling the callback.
        """
        self.logger.info("Opening interactive region selector …")
        _RegionSelector(callback, self.logger)


# ======================================================================
# Private overlay widget
# ======================================================================


class _RegionSelector:
    """Transparent fullscreen Tkinter overlay for drag-selecting a
    rectangular screen region."""

    # Theme colours (matching FocusFlow dark theme)
    _OVERLAY_COLOR = "#1a1a2e"
    _RECT_OUTLINE = "#00ff88"
    _RECT_WIDTH = 2

    def __init__(
        self,
        callback: Callable[[int, int, int, int], None],
        log: logging.Logger,
    ) -> None:
        self._callback = callback
        self._logger = log
        self._start_x: int = 0
        self._start_y: int = 0
        self._rect_id: Optional[int] = None

        # --- build the overlay window -----------------------------------
        self._root = tk.Tk()
        self._root.withdraw()  # hide default root

        self._overlay = tk.Toplevel(self._root)
        self._overlay.title("Select Region")
        self._overlay.attributes("-fullscreen", True)
        self._overlay.attributes("-topmost", True)

        # Semi-transparent overlay (Windows-specific alpha)
        self._overlay.attributes("-alpha", 0.30)
        self._overlay.configure(bg=self._OVERLAY_COLOR)

        self._overlay.overrideredirect(True)  # no window decorations

        # Canvas covering the whole screen
        self._canvas = tk.Canvas(
            self._overlay,
            cursor="crosshair",
            bg=self._OVERLAY_COLOR,
            highlightthickness=0,
        )
        self._canvas.pack(fill=tk.BOTH, expand=True)

        # Instruction label
        self._canvas.create_text(
            self._overlay.winfo_screenwidth() // 2,
            30,
            text="Click and drag to select a region  ·  Press Esc to cancel",
            fill="#e0e0e0",
            font=("Segoe UI", 14),
        )

        # --- bindings ---------------------------------------------------
        self._canvas.bind("<ButtonPress-1>", self._on_press)
        self._canvas.bind("<B1-Motion>", self._on_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_release)
        self._overlay.bind("<Escape>", self._on_cancel)

        self._root.mainloop()

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _on_press(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self._start_x = event.x_root
        self._start_y = event.y_root
        # Draw initial rectangle (canvas coords)
        self._rect_id = self._canvas.create_rectangle(
            event.x,
            event.y,
            event.x,
            event.y,
            outline=self._RECT_OUTLINE,
            width=self._RECT_WIDTH,
        )

    def _on_drag(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if self._rect_id is None:
            return
        # Update the rectangle to follow the cursor
        x0 = self._start_x - self._overlay.winfo_rootx()
        y0 = self._start_y - self._overlay.winfo_rooty()
        self._canvas.coords(self._rect_id, x0, y0, event.x, event.y)

    def _on_release(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        end_x = event.x_root
        end_y = event.y_root

        # Normalise so (x, y) is the top-left corner
        x = min(self._start_x, end_x)
        y = min(self._start_y, end_y)
        w = abs(end_x - self._start_x)
        h = abs(end_y - self._start_y)

        self._destroy()

        if w < 5 or h < 5:
            self._logger.warning(
                "Region too small (%d×%d) – selection ignored.", w, h
            )
            return

        self._logger.info("Region selected: x=%d y=%d w=%d h=%d", x, y, w, h)
        try:
            self._callback(x, y, w, h)
        except Exception:
            self._logger.exception("Error in region-selection callback")

    def _on_cancel(self, _event: tk.Event) -> None:  # type: ignore[type-arg]
        self._logger.info("Region selection cancelled by user.")
        self._destroy()

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _destroy(self) -> None:
        try:
            self._overlay.destroy()
        except tk.TclError:
            pass
        try:
            self._root.destroy()
        except tk.TclError:
            pass
