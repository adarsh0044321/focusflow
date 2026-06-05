"""
FocusFlow Capture Guard
========================
Prevents the application windows from appearing in screen captures,
screen shares, and recording software on Windows 10 2004+ by applying
``WDA_EXCLUDEFROMCAPTURE`` display affinity via the Win32 API.

A background daemon thread re-applies the affinity every 500 ms to
handle newly created child windows, pop-ups, and Tkinter toplevels
that appear after initial protection.
"""

import ctypes
import ctypes.wintypes
import logging
import os
import threading
import time
from typing import Any, Optional


logger = logging.getLogger("focusflow.guard")

# ---------------------------------------------------------------------------
# Win32 constants
# ---------------------------------------------------------------------------
WDA_NONE: int = 0x00000000
WDA_EXCLUDEFROMCAPTURE: int = 0x00000011

# Callback type for EnumWindows / EnumChildWindows
_WNDENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.wintypes.BOOL,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LPARAM,
)

try:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
except AttributeError:
    # Non-Windows: provide stubs so the module can be imported for tests.
    user32 = None  # type: ignore[assignment]
    kernel32 = None  # type: ignore[assignment]


class CaptureGuard:
    """Protect application windows from screen capture on Windows.

    Usage::

        guard = CaptureGuard()
        guard.protect_window(hwnd)   # single window
        guard.protect_all_tk_windows(root)  # all Tk windows
        guard.start()                # continuous re-application thread
        ...
        guard.stop()

    The guard is safe to instantiate on non-Windows platforms — it simply
    logs a warning and becomes a no-op.
    """

    def __init__(self) -> None:
        self._hwnds: set[int] = set()
        self._running: bool = False
        self._thread: Optional[threading.Thread] = None
        self._lock = threading.Lock()
        self._pid: int = os.getpid()

        if user32 is None:
            logger.warning(
                "CaptureGuard: Win32 API unavailable — guard is disabled"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def protect_window(self, hwnd: int) -> None:
        """Register *hwnd* for capture exclusion and apply immediately."""
        with self._lock:
            self._hwnds.add(hwnd)
        self._apply_exclusion(hwnd)

    def unprotect_window(self, hwnd: int) -> None:
        """Remove *hwnd* from the protection set and reset its affinity."""
        with self._lock:
            self._hwnds.discard(hwnd)
        self._reset_affinity(hwnd)

    def start(self) -> None:
        """Start the background guard thread.

        The thread re-applies exclusion to all tracked windows every 500 ms
        and also discovers any new process-owned windows via
        ``EnumWindows``.
        """
        if self._running:
            logger.debug("Guard thread already running")
            return
        self._running = True
        self._thread = threading.Thread(
            target=self._guard_loop, name="CaptureGuard", daemon=True
        )
        self._thread.start()
        logger.info("CaptureGuard started")

    def stop(self) -> None:
        """Signal the guard thread to stop."""
        self._running = False
        if self._thread is not None:
            self._thread.join(timeout=2.0)
            self._thread = None
        logger.info("CaptureGuard stopped")

    def protect_all_tk_windows(self, root: Any) -> None:
        """Discover and protect the Tk *root* window.

        Args:
            root: A ``tkinter.Tk`` or ``tkinter.Toplevel`` instance.
        """
        if user32 is None:
            return

        hwnd = self._resolve_tk_hwnd(root)
        if hwnd:
            self.protect_window(hwnd)

        logger.info(
            "Tk window protection applied  (tracked handles: %d)",
            len(self._hwnds),
        )

    # ------------------------------------------------------------------
    # Background thread
    # ------------------------------------------------------------------

    def _guard_loop(self) -> None:
        """Continuously re-apply capture exclusion."""
        while self._running:
            try:
                # 1. Re-apply to explicitly tracked handles.
                with self._lock:
                    tracked = set(self._hwnds)

                alive = 0
                dead: list[int] = []
                for hwnd in tracked:
                    if user32.IsWindow(hwnd):
                        self._apply_exclusion(hwnd)
                        alive += 1
                    else:
                        dead.append(hwnd)

                # Prune destroyed windows.
                if dead:
                    with self._lock:
                        for h in dead:
                            self._hwnds.discard(h)
                    logger.debug(
                        "Pruned %d destroyed handle(s) from guard set", len(dead)
                    )

                # 2. Enumerate ALL top-level windows owned by this process.
                self._enum_process_windows()

                logger.debug(
                    "[Guard] Capture-exclusion applied to %d window(s)", alive
                )
            except Exception as exc:
                logger.error("Guard loop error: %s", exc)

            time.sleep(0.5)

    # ------------------------------------------------------------------
    # Win32 helpers
    # ------------------------------------------------------------------

    def _apply_exclusion(self, hwnd: int) -> bool:
        """Apply ``WDA_EXCLUDEFROMCAPTURE`` to *hwnd*.

        Returns ``True`` on success.
        """
        if user32 is None:
            return False
        try:
            if not user32.IsWindow(hwnd):
                return False
            result = user32.SetWindowDisplayAffinity(hwnd, WDA_EXCLUDEFROMCAPTURE)
            if not result:
                err = kernel32.GetLastError()
                # Error 5 (ACCESS_DENIED) is common for windows we don't own
                if err != 5:
                    logger.debug(
                        "SetWindowDisplayAffinity failed  hwnd=0x%08X  err=%d",
                        hwnd,
                        err,
                    )
                return False
            return True
        except Exception as exc:
            logger.error(
                "Exception applying display affinity to 0x%08X: %s", hwnd, exc
            )
            return False

    def _reset_affinity(self, hwnd: int) -> None:
        """Remove capture exclusion from *hwnd*."""
        if user32 is None:
            return
        try:
            user32.SetWindowDisplayAffinity(hwnd, WDA_NONE)
        except Exception as exc:
            logger.error(
                "Exception resetting display affinity on 0x%08X: %s", hwnd, exc
            )

    def _enum_process_windows(self) -> None:
        """Find all top-level windows belonging to this process and protect them.

        Uses ``EnumWindows`` with a ``GetWindowThreadProcessId`` filter.
        """
        if user32 is None:
            return

        pid = self._pid

        @_WNDENUMPROC
        def _cb(hwnd: int, _lparam: int) -> bool:
            try:
                win_pid = ctypes.wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(win_pid))
                if win_pid.value == pid:
                    self._apply_exclusion(hwnd)
                    with self._lock:
                        self._hwnds.add(hwnd)
            except Exception:
                pass
            return True  # continue enumeration

        try:
            # Keep callback reference alive during call
            self._current_callback = _cb
            user32.EnumWindows(_cb, 0)
        except Exception as exc:
            logger.debug("EnumWindows error: %s", exc)
        finally:
            self._current_callback = None

    # ------------------------------------------------------------------
    # Tk helpers
    # ------------------------------------------------------------------

    def _resolve_tk_hwnd(self, widget: Any) -> Optional[int]:
        """Resolve the true top-level HWND for a Tk widget.

        ``winfo_id()`` may return the inner frame; we walk up via
        ``GetParent`` to find the owning top-level window.
        """
        if user32 is None:
            return None
        try:
            inner = widget.winfo_id()
            hwnd = inner

            # Walk up the parent chain to find the actual top-level window.
            for _ in range(10):  # safety bound
                parent = user32.GetParent(hwnd)
                if parent == 0:
                    break
                hwnd = parent

            return hwnd
        except Exception as exc:
            logger.debug("Failed to resolve Tk HWND: %s", exc)
            return None
