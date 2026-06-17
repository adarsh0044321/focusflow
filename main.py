"""
FocusFlow — Main Entry Point
============================
Redesigned study-focused desktop application that hosts a webview-based
SaaS dashboard, locks distractions with native hooks, calculates study
analytics, and provides academic AI assistance.
"""

import atexit
import logging
import logging.handlers
import os
os.environ["WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS"] = "--disable-renderer-accessibility"
import sys
import winreg
import subprocess
import threading
import time
import ctypes
import ctypes.wintypes
import tkinter as tk
from pathlib import Path
from typing import Optional, Dict, Any, List
import http.server
import socketserver

# --- Initialize DPI awareness on Windows ---
# DPI (Dots Per Inch) awareness is configured on Windows to prevent the Webview2
# frame and overlay graphics from being blurry or incorrectly scaled on high-DPI monitors.
if sys.platform == "win32":
    try:
        import ctypes
        # SetProcessDpiAwareness(1) corresponds to PROCESS_SYSTEM_DPI_AWARE
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        try:
            # Fallback to SetProcessDPIAware for older Windows OS versions
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass

# --- Resolve base directory ---
if getattr(sys, "frozen", False):
    exe_dir = Path(sys.executable).resolve().parent
    if exe_dir.name.lower() == "dist" and not (exe_dir / "Tesseract-OCR").exists() and (exe_dir.parent / "Tesseract-OCR").exists():
        BASE_DIR = exe_dir.parent
    else:
        BASE_DIR = exe_dir
else:
    BASE_DIR = Path(__file__).resolve().parent

# --- Logging setup ---
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "focusflow.log"

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)-7s %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.handlers.RotatingFileHandler(
            LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
        ),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("focusflow")

# --- Native Win32 API / keyboard imports ---
import webview
import keyboard
import win32api
import win32con
import win32gui
import win32process

# --- Legacy imports ---
from config_manager import ConfigManager
from screen_capture import ScreenCapture
from ocr_engine import OCREngine
from ocr_cleaner import OCRCleaner
from ai_engine import AIEngine
from guard import CaptureGuard
from session_manager import SessionManager
from app_bridge import FocusFlowAPI

class ThreadedHTTPServer:
    """Simple HTTP server to serve the static Next.js export in a background thread."""

    def __init__(self, host: str, port: int, directory: str) -> None:
        self.host = host
        self.port = port
        self.directory = directory
        self.server = None
        self.thread = None

    def start(self) -> None:
        dir_path = self.directory
        
        class SafeHTTPHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, directory=dir_path, **kwargs)
                
            def log_message(self, format, *args):
                # Mute logging output
                pass

        class MyTCPServer(socketserver.TCPServer):
            allow_reuse_address = True

        self.server = MyTCPServer((self.host, self.port), SafeHTTPHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        logger.info(f"Local static server started at http://{self.host}:{self.port} serving {self.directory}")

    def stop(self) -> None:
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info("Local static server stopped.")

class FocusLock:
    """Manages low-level Windows keyboard locks during focus sessions."""

    def __init__(self) -> None:
        self.locked = False
        self.hotkeys: List[Any] = []

    def lock(self) -> None:
        if self.locked:
            return
        self.locked = True
        logger.info("Applying global keyboard locks.")
        
        try:
            # Block Windows keys globally
            keyboard.block_key('left windows')
            keyboard.block_key('right windows')
            
            # Intercept and suppress Alt+Tab, Alt+F4, and task views
            hk_alt_tab = keyboard.add_hotkey('alt+tab', lambda: None, suppress=True)
            hk_win_tab = keyboard.add_hotkey('win+tab', lambda: None, suppress=True)
            hk_alt_f4 = keyboard.add_hotkey('alt+f4', lambda: None, suppress=True)
            hk_ctrl_esc = keyboard.add_hotkey('ctrl+esc', lambda: None, suppress=True)
            hk_ctrl_shift_esc = keyboard.add_hotkey('ctrl+shift+esc', lambda: None, suppress=True)
            
            # Additional touchpad-emulated hotkeys (virtual desktops and minimization)
            hk_win_d = keyboard.add_hotkey('win+d', lambda: None, suppress=True)
            hk_ctrl_win_left = keyboard.add_hotkey('ctrl+win+left', lambda: None, suppress=True)
            hk_ctrl_win_right = keyboard.add_hotkey('ctrl+win+right', lambda: None, suppress=True)
            hk_ctrl_win_d = keyboard.add_hotkey('ctrl+win+d', lambda: None, suppress=True)
            hk_ctrl_win_f4 = keyboard.add_hotkey('ctrl+win+f4', lambda: None, suppress=True)
            
            self.hotkeys = [
                hk_alt_tab, hk_win_tab, hk_alt_f4, hk_ctrl_esc, hk_ctrl_shift_esc,
                hk_win_d, hk_ctrl_win_left, hk_ctrl_win_right, hk_ctrl_win_d, hk_ctrl_win_f4
            ]
        except Exception as e:
            logger.error(f"Failed to register keyboard locks: {e}")

    def unlock(self) -> None:
        if not self.locked:
            return
        self.locked = False
        logger.info("Releasing global keyboard locks.")
        
        try:
            keyboard.unblock_key('left windows')
            keyboard.unblock_key('right windows')
        except Exception:
            pass
            
        for hk in self.hotkeys:
            try:
                keyboard.remove_hotkey(hk)
            except Exception:
                pass
        self.hotkeys = []
        try:
            keyboard.unhook_all()
        except Exception:
            pass

class TouchpadLock:
    """Manages low-level Windows Precision Touchpad gesture settings."""

    def __init__(self) -> None:
        self.registry_path = r"Software\Microsoft\Windows\CurrentVersion\PrecisionTouchPad"
        self.saved_settings = {}
        self.keys_to_block = {
            "ThreeFingerPressAction": 0,
            "ThreeFingerTapAction": 0,
            "ThreeFingerSlideEnabled": 0,
            "ThreeFingerHorizSlideAction": 0,
            "ThreeFingerVertSlideAction": 0,
            "FourFingerPressAction": 0,
            "FourFingerTapAction": 0,
            "FourFingerSlideEnabled": 0,
            "FourFingerHorizSlideAction": 0,
            "FourFingerVertSlideAction": 0,
            "ZoomEnabled": 0,
            "TwoFingerTapEnabled": 0,
            "PanEnabled": 0,
            "EnableEdgy": 0,
        }

    def lock(self) -> None:
        logger.info("Applying touchpad gesture locks.")
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_ALL_ACCESS)
        except Exception as e:
            logger.error(f"Failed to open PrecisionTouchPad registry key: {e}")
            return

        self.saved_settings = {}
        for name, block_value in self.keys_to_block.items():
            try:
                val, val_type = winreg.QueryValueEx(key, name)
                self.saved_settings[name] = (val, val_type)
            except FileNotFoundError:
                self.saved_settings[name] = None
            except Exception as e:
                logger.error(f"Failed to query {name}: {e}")
                
            try:
                winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, block_value)
            except Exception as e:
                logger.error(f"Failed to set {name} to {block_value}: {e}")

        winreg.CloseKey(key)
        self._notify_system()

    def unlock(self) -> None:
        if not self.saved_settings:
            return
        logger.info("Restoring touchpad gesture settings.")
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, self.registry_path, 0, winreg.KEY_ALL_ACCESS)
        except Exception as e:
            logger.error(f"Failed to open PrecisionTouchPad registry key: {e}")
            return

        for name, saved in self.saved_settings.items():
            try:
                if saved is None:
                    try:
                        winreg.DeleteValue(key, name)
                    except FileNotFoundError:
                        pass
                else:
                    winreg.SetValueEx(key, name, 0, saved[1], saved[0])
            except Exception as e:
                logger.error(f"Failed to restore {name}: {e}")

        winreg.CloseKey(key)
        self.saved_settings = {}
        self._notify_system()

    def _notify_system(self) -> None:
        try:
            win32gui.SendMessageTimeout(
                win32con.HWND_BROADCAST,
                win32con.WM_SETTINGCHANGE,
                0,
                "PrecisionTouchPad",
                win32con.SMTO_ABORTIFHUNG,
                100
            )
            logger.info("System notified of PrecisionTouchPad registry change.")
        except Exception as e:
            logger.error(f"Failed to send WM_SETTINGCHANGE: {e}")

class FocusFlowApp:
    """Redesigned main application controller."""

    def __init__(self, run_mode: str = "combined") -> None:
        logger.info(f"[Startup] FocusFlow — log: {LOG_FILE}")

        # --- Core managers ---
        self.config = ConfigManager(str(BASE_DIR))
        self.run_mode = run_mode
        self.session_manager = SessionManager(str(BASE_DIR))
        self.ocr = OCREngine(self.config)
        self.cleaner = OCRCleaner()
        self.capture = ScreenCapture(self.config)
        self.ai = AIEngine(self.config, None, run_mode=self.run_mode)
        self.guard = CaptureGuard()

        # --- State variables ---
        self.session_active = False
        self.session_goal = ""
        self.session_subject = ""
        self.session_target_mins = 0
        self.session_mode = "light"
        self.session_features = {}
        self.session_start_time = ""
        self.webview_hwnd = None
        self.ocr_text = ""
        self._cleaned_up = False
        self.ai_panel_visible = False

        # --- Window recovery path ---
        self.recovery_path = BASE_DIR / "data" / "active_session.json"

        # --- Focus Guard Locks ---
        self.focus_lock = FocusLock()
        self.touchpad_lock = TouchpadLock()
        self.locks_applied = False
        self.guard_thread: Optional[threading.Thread] = None

        # --- Start local HTTP server ---
        static_dir = BASE_DIR / "landing" / "out"
        self.server = ThreadedHTTPServer("127.0.0.1", 5000, str(static_dir))
        self.server.start()

        # --- Register cleanup ---
        atexit.register(self.cleanup)

    def run(self) -> None:
        """Create and start the pywebview window."""
        self.window = webview.create_window(
            title='FocusFlow 🪐',
            url='http://127.0.0.1:5000/dashboard/',
            frameless=True,
            fullscreen=True,
            easy_drag=False,
            background_color='#000000',
            js_api=FocusFlowAPI(self)
        )
        
        # Apply window display affinity on shown
        webview.start(self._on_window_shown)

    def _on_window_shown(self) -> None:
        """Callback fired when the WebView2 window has loaded."""
        time.sleep(0.5)  # Wait for window handle creation
        self.webview_hwnd = win32gui.FindWindow(None, 'FocusFlow 🪐')
        if self.webview_hwnd:
            # Evasion: Exclude window from screenshots and screen shares
            self.guard.protect_window(self.webview_hwnd)
            self.guard.start()
            
            # Apply initial opacity from settings
            opacity = self.config.get("opacity", 240)
            self.update_opacity(opacity)
            logger.info(f"Capture Evasion applied to Webview HWND: {hex(self.webview_hwnd)}")

            # Block WebView2 new window requests (ad clicks, target="_blank" links) to prevent focus theft/popups
            try:
                form = self.window.native
                if form:
                    import clr
                    clr.AddReference("System.Windows.Forms")
                    from System import Action
                    
                    def register_wv2_handlers():
                        try:
                            webview_ctrl = form.browser.webview
                            
                            def handle_new_window(sender, args):
                                logger.info(f"[WebView2] Blocked new window request for URI: {args.Uri}")
                                args.Handled = True
                                
                            def on_initialization_completed(sender, args):
                                try:
                                    core_wv2 = webview_ctrl.CoreWebView2
                                    if core_wv2:
                                        core_wv2.NewWindowRequested += handle_new_window
                                        logger.info("[WebView2] NewWindowRequested registered inside initialization completion handler.")
                                except Exception as ex:
                                    logger.error(f"Error inside WebView2 initialization completed: {ex}")
                                    
                            if webview_ctrl.CoreWebView2 is not None:
                                webview_ctrl.CoreWebView2.NewWindowRequested += handle_new_window
                                logger.info("[WebView2] NewWindowRequested registered directly.")
                            else:
                                webview_ctrl.CoreWebView2InitializationCompleted += on_initialization_completed
                                logger.info("[WebView2] CoreWebView2InitializationCompleted registered.")
                        except Exception as ex:
                            logger.error(f"Error registering WebView2 handlers on UI thread: {ex}")
                            
                    form.Invoke(Action(register_wv2_handlers))
            except Exception as e:
                logger.error(f"Failed to setup WebView2 window interceptor: {e}")
        else:
            logger.error("Could not find window HWND for display protection!")

    def update_opacity(self, opacity_value: int) -> None:
        """Apply transparent layering directly to Webview window handle."""
        # Disabled to prevent cross-thread Win32 window style modification deadlocks with WebView2
        return

    # --- Focus Session Actions ---
    def start_focus_session(self, goal: str, subject: str, duration_mins: int, mode: str, custom_features: Optional[Dict[str, bool]] = None) -> bool:
        """Log active session details, enable Win32 locks, and spawn active guard loop."""
        self.session_active = True
        self.session_goal = goal
        self.session_subject = subject
        self.session_target_mins = duration_mins
        self.session_mode = mode
        self.session_start_time = time.strftime("%Y-%m-%d %H:%M:%S")

        # Resolve features with default fallback sets
        self.session_features = {
            "keyboard_lock": False,
            "touchpad_lock": False,
            "app_sweeper": False,
            "foreground_guard": False,
            "fullscreen": False,
            "capture_protection": True
        }
        
        # Apply defaults based on mode
        if mode == "moderate":
            self.session_features["keyboard_lock"] = True
            self.session_features["foreground_guard"] = True
        elif mode == "strict":
            self.session_features["keyboard_lock"] = True
            self.session_features["touchpad_lock"] = True
            self.session_features["app_sweeper"] = True
            self.session_features["foreground_guard"] = True
            self.session_features["capture_protection"] = True
        elif mode == "very_strict":
            self.session_features["keyboard_lock"] = True
            self.session_features["touchpad_lock"] = True
            self.session_features["app_sweeper"] = True
            self.session_features["foreground_guard"] = True
            self.session_features["fullscreen"] = True
            self.session_features["capture_protection"] = True

        # Override with user customized settings if provided
        if custom_features:
            for k, v in custom_features.items():
                self.session_features[k] = bool(v)

        # Save session config to file for crash recovery
        recovery_data = {
            "goal": goal,
            "subject": subject,
            "target_duration_mins": duration_mins,
            "mode": mode,
            "start_time": self.session_start_time,
            "custom_features": self.session_features
        }
        import json
        try:
            with open(self.recovery_path, "w", encoding="utf-8") as f:
                json.dump(recovery_data, f)
        except Exception as e:
            logger.error(f"Failed to save recovery file: {e}")

        # Apply all session locks and start background processes
        self._apply_session_locks_and_features()

        return True

    def _apply_session_locks_and_features(self) -> None:
        """Apply Win32 locks, guards, and backend processes based on self.session_features."""
        if getattr(self, "locks_applied", False):
            logger.info("Locks and features are already applied, skipping duplicate activation.")
            return
        self.locks_applied = True

        # Activate keyboard locks
        if self.session_features.get("keyboard_lock"):
            self.focus_lock.lock()

        # Activate touchpad gesture locks
        if self.session_features.get("touchpad_lock"):
            self.touchpad_lock.lock()

        # Proactively close unallowed applications in a background thread to prevent UI freezing
        if self.session_features.get("app_sweeper"):
            threading.Thread(target=self._close_unallowed_apps, daemon=True).start()

        # Activate fullscreen mode
        if self.session_features.get("fullscreen"):
            try:
                self.window.fullscreen = True
                logger.info("Entered Fullscreen mode.")
            except Exception as e:
                logger.error(f"Failed to enter fullscreen: {e}")

        # Dynamic Capture Protection Exclusion
        if self.webview_hwnd:
            if self.session_features.get("capture_protection"):
                self.guard.protect_window(self.webview_hwnd)
                self.guard.start()
            else:
                self.guard.unprotect_window(self.webview_hwnd)
                self.guard.stop()

        # Create desktop shortcut for Strict mode
        if self.session_mode == "strict":
            self._manage_desktop_shortcut(True)

        # Register safety backdoor hook (Ctrl+Shift+Alt+Escape)
        try:
            self.backdoor_hk = keyboard.add_hotkey(
                'ctrl+shift+alt+esc', 
                lambda: threading.Thread(target=self.stop_focus_session, args=("interrupted",), daemon=True).start(), 
                suppress=True
            )
            logger.info("Safety backdoor hotkey registered.")
        except Exception as e:
            logger.error(f"Failed to register safety backdoor: {e}")

        # Spawn foreground guard thread
        if self.session_features.get("foreground_guard"):
            self.guard_thread = threading.Thread(target=self._focus_guard_loop, daemon=True)
            self.guard_thread.start()

    def stop_focus_session(self, status: str) -> bool:
        """Disable Win32 locks, prune active sessions, and log metrics."""
        time.sleep(0.2)  # Cooldown delay to allow active hook thread execution to safely return
        self.session_active = False
        self.locks_applied = False
        
        # Stop hooks and locks
        self.focus_lock.unlock()
        self.touchpad_lock.unlock()

        # Remove backdoor hook
        if hasattr(self, "backdoor_hk") and self.backdoor_hk:
            try:
                keyboard.remove_hotkey(self.backdoor_hk)
            except Exception:
                pass
            self.backdoor_hk = None

        # Exit fullscreen mode if active
        if self.session_features.get("fullscreen") or getattr(self.window, "fullscreen", False):
            try:
                self.window.fullscreen = False
                logger.info("Exited Fullscreen mode.")
            except Exception as e:
                logger.error(f"Failed to exit fullscreen: {e}")

        # Restore default capture protection on session exit
        if self.webview_hwnd:
            self.guard.protect_window(self.webview_hwnd)
            self.guard.start()

        # Remove desktop shortcut if was strict
        if self.session_mode == "strict":
            self._manage_desktop_shortcut(False)

        # Delete crash recovery file
        if self.recovery_path.exists():
            try:
                self.recovery_path.unlink()
            except Exception as e:
                logger.error(f"Failed to clear recovery file: {e}")

        # Compute elapsed time in minutes
        if self.session_start_time:
            start_dt = time.strptime(self.session_start_time, "%Y-%m-%d %H:%M:%S")
            start_secs = time.mktime(start_dt)
            elapsed_mins = int((time.time() - start_secs) / 60)
            elapsed_mins = max(1, min(self.session_target_mins, elapsed_mins))
        else:
            elapsed_mins = self.session_target_mins

        # Log session status database
        is_interrupted = (status == "interrupted")
        self.session_manager.add_session(
            goal=self.session_goal,
            subject=self.session_subject,
            duration_mins=elapsed_mins,
            target_duration_mins=self.session_target_mins,
            mode=self.session_mode,
            status=status,
            is_interrupted=is_interrupted
        )

        # Reset states
        old_mode = self.session_mode
        self.session_goal = ""
        self.session_subject = ""
        self.session_start_time = ""

        # Notify JS frontend that session has ended
        try:
            self.window.evaluate_js(f"if(window.stopSessionFromPython) window.stopSessionFromPython('{status}');")
        except Exception as e:
            logger.error(f"Failed to notify JS of session stop: {e}")

        return True

    def get_active_session(self) -> Optional[Dict[str, Any]]:
        """Used on launch to check if a crash occurred during an active session."""
        if self.recovery_path.exists():
            try:
                with open(self.recovery_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Check if session has already expired in natural time
                start_dt = time.strptime(data["start_time"], "%Y-%m-%d %H:%M:%S")
                start_secs = time.mktime(start_dt)
                total_duration = data["target_duration_mins"] * 60
                
                if time.time() < start_secs + total_duration:
                    self.session_active = True
                    self.session_goal = data.get("goal", "")
                    self.session_subject = data.get("subject", "")
                    self.session_target_mins = data.get("target_duration_mins", 0)
                    self.session_mode = data.get("mode", "light")
                    self.session_start_time = data.get("start_time", "")
                    self.session_features = data.get("custom_features", {})
                    
                    # Apply session locks and start background processes on recovery
                    logger.info("Crash Recovery: Resuming active focus session natively.")
                    self._apply_session_locks_and_features()
                    
                    return data
                else:
                    # Session naturally completed/expired in background while app was closed
                    self.recovery_path.unlink()
                    logger.info("Pruned naturally expired recovery session.")
            except Exception as e:
                logger.error(f"Error reading recovery file: {e}")
        return None

    # --- Focus Guard Loop ---
    def _focus_guard_loop(self) -> None:
        """Monitors active windows and enforces whitelists during lock modes."""
        logger.info("Focus Guard Loop Active.")
        last_full_scan = time.time()
        while self.session_active:
            try:
                now = time.time()
                if self.session_features.get("app_sweeper") and (now - last_full_scan >= 10.0):
                    last_full_scan = now
                    threading.Thread(target=self._close_unallowed_apps, daemon=True).start()

                if self.session_features.get("foreground_guard"):
                    hwnd = win32gui.GetForegroundWindow()
                    if hwnd and hwnd != self.webview_hwnd:
                        _, pid = win32process.GetWindowThreadProcessId(hwnd)
                        if pid == os.getpid():
                            is_allowed = True
                            proc_name = "FocusFlow (Internal)"
                        else:
                            proc_name = self._get_process_name_by_hwnd(hwnd)
                            is_allowed = False

                            # 1. Very Strict Mode
                            if self.session_mode == "very_strict":
                                is_allowed = False

                            # 2. Strict Mode
                            elif self.session_mode == "strict":
                                allowed_apps = self.config.get("strict_allowed_apps") or [
                                    "Spotify.exe", "Acrobat.exe", "SumatraPDF.exe", "explorer.exe"
                                ]
                                if proc_name in allowed_apps:
                                    is_allowed = True

                            # 3. Moderate / Custom / Light with foreground guard
                            else:
                                allowed_apps = self.config.get("moderate_allowed_apps") or [
                                    "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "Spotify.exe"
                                ]
                                proc_lower = proc_name.lower() if proc_name else ""
                                allowed_apps_lower = [app.lower() for app in allowed_apps]
                                
                                if proc_lower in allowed_apps_lower:
                                    browsers = ["chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "opera.exe", "iexplore.exe"]
                                    if proc_lower in browsers:
                                        title = win32gui.GetWindowText(hwnd).lower()
                                        allowed_sites = self.config.get("moderate_allowed_websites") or [
                                            "youtube.com", "physicswallah.com", "unacademy.com", "notion.so"
                                        ]
                                        if any(site.lower() in title for site in allowed_sites):
                                            is_allowed = True
                                    else:
                                        # Non-browser whitelisted app is allowed directly
                                        is_allowed = True

                        if not is_allowed:
                            logger.info(f"Blocked foreground activity: {proc_name} ({hex(hwnd)})")
                            if self.session_features.get("app_sweeper"):
                                class_name = win32gui.GetClassName(hwnd)
                                if class_name not in ("Progman", "Shell_TrayWnd", "Button", "InputIndicator") and (proc_name or "").lower() != "explorer.exe":
                                    _, pid = win32process.GetWindowThreadProcessId(hwnd)
                                    if pid != os.getpid():
                                        logger.info(f"[Proctoring] Terminating popped process: {proc_name} (PID: {pid})")
                                        try:
                                            startupinfo = subprocess.STARTUPINFO()
                                            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                                            subprocess.Popen(
                                                ["taskkill", "/F", "/PID", str(pid)],
                                                startupinfo=startupinfo,
                                                stdout=subprocess.DEVNULL,
                                                stderr=subprocess.DEVNULL
                                            )
                                        except Exception as e:
                                            logger.debug(f"Failed to taskkill PID {pid}: {e}")
                            else:
                                win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                            
                            if self.webview_hwnd:
                                win32gui.SetForegroundWindow(self.webview_hwnd)
                                escaped_proc = (proc_name or "Unknown").replace("'", "\\'")
                                self.window.evaluate_js(f"window.showBlockedAlert('{escaped_proc}')")
            except Exception as e:
                logger.error(f"Error in guard loop: {e}")
            time.sleep(0.3)
        logger.info("Focus Guard Loop Stopped.")

    def _get_process_name_by_hwnd(self, hwnd: int) -> Optional[str]:
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            h_proc = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
            if h_proc:
                try:
                    name = win32process.GetModuleFileNameEx(h_proc, 0)
                    return os.path.basename(name)
                finally:
                    win32api.CloseHandle(h_proc)
        except Exception:
            pass
        return None

    def _close_unallowed_apps(self) -> None:
        """Enumerate all running processes natively and kill user applications that are not allowed."""
        if not self.session_features.get("app_sweeper"):
            return
            
        logger.info(f"[Proctoring] Scanning and terminating unallowed applications for {self.session_mode} mode.")
        
        # Determine allowed apps based on mode
        allowed_apps = []
        if self.session_mode == "strict":
            allowed_apps = self.config.get("strict_allowed_apps") or [
                "Spotify.exe", "Acrobat.exe", "SumatraPDF.exe", "explorer.exe"
            ]
        elif self.session_mode == "very_strict":
            allowed_apps = ["explorer.exe"]
        else: # Moderate/custom
            allowed_apps = self.config.get("moderate_allowed_apps") or [
                "chrome.exe", "msedge.exe", "firefox.exe", "brave.exe", "Spotify.exe"
            ]
            
        allowed_apps_lower = {app.lower() for app in allowed_apps}
        
        # Hardcoded additional whitelist fallback for safety
        system_whitelist = {
            "explorer.exe", "taskmgr.exe", "cmd.exe", "powershell.exe", 
            "conhost.exe", "tasklist.exe", "taskkill.exe", "wmic.exe"
        }
        
        try:
            # Enumerate all process IDs
            pids = win32process.EnumProcesses()
        except Exception as e:
            logger.error(f"Failed to enumerate processes via Win32: {e}")
            return
            
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        system_root = (os.environ.get("SystemRoot") or "C:\\Windows").lower()
        
        for pid in pids:
            if pid in (0, 4) or pid == os.getpid():
                continue
                
            h_proc = None
            try:
                # Open process with query and read rights
                h_proc = win32api.OpenProcess(win32con.PROCESS_QUERY_INFORMATION | win32con.PROCESS_VM_READ, False, pid)
                if h_proc:
                    path = win32process.GetModuleFileNameEx(h_proc, 0)
                    path_lower = path.lower()
                    name = os.path.basename(path)
                    name_lower = name.lower()
                    
                    # 1. Automatic system directory whitelist:
                    # Whitelist everything running out of Windows system directory (drivers, services, shell hosts)
                    if path_lower.startswith(system_root):
                        continue
                        
                    # 2. Application essentials whitelist:
                    # Protect ourselves, our WebView2 renderer/helper processes, and the OCR/LLM engines
                    if any(x in name_lower for x in ("focusflow", "msedgewebview2", "tesseract", "llama-server", "python")):
                        continue
                        
                    # 3. User allowed apps & basic system shell tools
                    if name_lower in allowed_apps_lower or name_lower in system_whitelist:
                        continue
                        
                    # If it passed all filters, it is an unauthorized user app. Terminate it.
                    logger.info(f"[Proctoring] Terminating unallowed process: {name} (PID: {pid})")
                    try:
                        subprocess.Popen(
                            ["taskkill", "/F", "/PID", str(pid)],
                            startupinfo=startupinfo,
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL
                        )
                    except Exception as kill_err:
                        logger.debug(f"Failed to trigger taskkill for {name} (PID {pid}): {kill_err}")
            except Exception:
                # Ignore processes we cannot open (e.g. secure system services running as SYSTEM/NT Service, which we shouldn't kill anyway)
                pass
            finally:
                if h_proc:
                    try:
                        win32api.CloseHandle(h_proc)
                    except Exception:
                        pass

    # --- Screen Capture & OCR Pipeline ---
    def run_stealth_capture(self) -> None:
        """Minimizes main app, starts Tkinter drag overlay, runs Tesseract OCR, restores app."""
        try:
            # 1. Minimize main webview window
            self.window.minimize()
            time.sleep(0.4) # Wait for animation
            
            self.ocr_text = ""
            
            # Run interactive transparent overlay in background thread
            def select_thread():
                root = tk.Tk()
                root.withdraw()
                
                def on_select(x, y, w, h):
                    self.config.set("region_x", x)
                    self.config.set("region_y", y)
                    self.config.set("region_w", w)
                    self.config.set("region_h", h)
                    
                    # Capture screen region
                    img = self.capture.capture_region()
                    
                    # Run OCR
                    raw_text, ocr_err = self.ocr.extract_text(img)
                    cleaned, _, _ = self.cleaner.clean(raw_text)
                    self.ocr_text = cleaned
                    root.destroy()
                    
                def on_cancel():
                    root.destroy()
                    
                self.capture.select_region_interactive(on_select, on_cancel=on_cancel, root=root)
                root.mainloop()
                
            t = threading.Thread(target=select_thread)
            t.start()
            t.join() # Wait for selector window exit
            
            # 2. Restore main webview window
            self.window.restore()
            time.sleep(0.1)
            
            # 3. Paste OCR text into JS
            if self.ocr_text:
                escaped = self.ocr_text.replace("'", "\\'").replace("\n", "\\n").replace("\r", "")
                self.window.evaluate_js(f"window.setOcrResult('{escaped}')")
                logger.info(f"Successfully processed OCR and sent to JS: {len(self.ocr_text)} chars")
            else:
                logger.warning("OCR capture was empty or cancelled.")
        except Exception as e:
            logger.error(f"Failed to execute OCR capture: {e}")
            if self.window:
                self.window.restore()

    def open_pdf_dialog(self) -> None:
        """Trigger native Open File dialog to pick study PDF and copy to serve inside WebView."""
        try:
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            
            from tkinter import filedialog
            file_path = filedialog.askopenfilename(
                parent=root,
                title="Select Study PDF",
                filetypes=[("PDF files", "*.pdf")]
            )
            root.destroy()
            
            if file_path:
                import shutil
                # Create destination directory inside Next.js static files
                temp_pdf_dir = BASE_DIR / "landing" / "out" / "temp_pdf"
                temp_pdf_dir.mkdir(parents=True, exist_ok=True)
                
                dest_path = temp_pdf_dir / "selected.pdf"
                shutil.copy2(file_path, dest_path)
                logger.info(f"Copied study PDF to static path: {dest_path}")
                
                # Evaluate JS to load PDF inside webview
                self.window.evaluate_js("if (window.loadPdfInApp) window.loadPdfInApp('/temp_pdf/selected.pdf');")
        except Exception as e:
            logger.error(f"Error opening study PDF: {e}")

    def _manage_desktop_shortcut(self, create: bool) -> None:
        """Create or remove the Student Tools link on the desktop."""
        try:
            desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")
            shortcut_path = os.path.join(desktop_dir, "Student Tools.url")
            if create:
                with open(shortcut_path, "w", encoding="utf-8") as f:
                    f.write("[InternetShortcut]\n")
                    f.write("URL=https://student-tools-seven.vercel.app/\n")
                logger.info(f"Created Student Tools shortcut on desktop: {shortcut_path}")
            else:
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    logger.info("Deleted Student Tools shortcut from desktop.")
        except Exception as e:
            logger.error(f"Failed to manage desktop shortcut: {e}")

    # --- Cleanup ---
    def cleanup(self) -> None:
        """Gracefully release Win32 locks, stop background server, and shutdown AI processes."""
        if self._cleaned_up:
            return
        self._cleaned_up = True
        logger.info("[Cleanup] Finalizing FocusFlow...")
        
        # Unlock keyboard hooks
        try:
            self.focus_lock.unlock()
        except Exception:
            pass
            
        try:
            self.touchpad_lock.unlock()
        except Exception:
            pass
            
        try:
            keyboard.unhook_all()
        except Exception:
            pass
            
        # Stop HTTP server
        try:
            self.server.stop()
        except Exception:
            pass
            
        # Stop AI Engine
        try:
            self.ai.stop()
        except Exception:
            pass
            
        # Stop CaptureGuard
        try:
            self.guard.stop()
        except Exception:
            pass
        logger.info("[Cleanup] Done.")
        os._exit(0)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="FocusFlow Immersive Study App")
    parser.add_argument(
        "--mode",
        choices=["online", "offline", "combined"],
        default="combined",
        help="Run mode for the application (default: combined)"
    )
    args, unknown = parser.parse_known_args()
    
    app = FocusFlowApp(run_mode=args.mode)
    app.run()
