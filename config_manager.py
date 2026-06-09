"""
FocusFlow Configuration Manager
================================
JSON-based settings persistence with defaults merging, API key rotation,
and path resolution relative to the application base directory.

Settings file: data/settings.json (relative to base_dir)
"""

import json
import logging
import os
import sys
import threading
from pathlib import Path
from typing import Any, Optional


logger = logging.getLogger("focusflow.config")

DEFAULTS: dict[str, Any] = {
    # Hotkeys
    "hotkey_solve": "ctrl+shift+k",
    "hotkey_toggle": "ctrl+shift+h",
    "hotkey_clear": "ctrl+shift+z",
    "hotkey_settings": "ctrl+shift+s",
    # Capture
    "capture_mode": "region",           # "fullscreen" or "region"
    "capture_all_screens": False,
    "region_x": 0,
    "region_y": 0,
    "region_w": 800,
    "region_h": 600,
    # OCR
    "auto_run_after_hotkey": True,
    "show_ocr_preview": False,
    "save_screenshot_history": True,
    "ocr_preprocessing": True,
    "ocr_preprocess_grayscale": True,
    "ocr_preprocess_contrast": False,
    "ocr_preprocess_sharpen": False,
    "ocr_preprocess_denoise": False,
    "ocr_preprocess_threshold": False,
    # LLM (offline)
    "llm_binary": "llama.cpp-master/llm/llama-server.exe",
    "llm_cli_binary": "llama.cpp-master/llm/llama-cli.exe",
    "llm_model_path": "models/Phi-3-mini-4k-instruct-q4.gguf",
    "llm_port": 8081,
    "llm_context_length": 512,
    "llm_max_tokens": 600,
    "llm_temperature": 0.1,
    "llm_top_p": 0.9,
    "llm_threads": 2,
    "llm_gpu_layers": 0,
    "llm_timeout": 300,
    # Mode
    "mode": "combined",                 # "offline", "online", "combined"
    "combined_active": "offline",       # which sub-mode is active in combined
    # Online
    "online_api_keys": [],              # list of OpenAI API keys
    "online_model": "gpt-4o",
    "online_send_mode": "ocr",          # "ocr", "image", "both"
    "online_max_tokens": 1000,
    "online_temperature": 0.2,
    # Answer
    "answer_mode": "concise",           # "concise" or "detailed"
    "auto_copy_answer": False,
    # UI
    "first_run": True,
    "opacity": 240,
    "always_on_top": True,
    "hide_from_taskbar": False,
}


class ConfigManager:
    """Manages application settings with JSON persistence.

    Settings are stored in ``data/settings.json`` relative to the resolved
    base directory.  On load the saved values are merged over a copy of
    ``DEFAULTS`` so that newly-added keys are always present.

    Thread-safety: a reentrant lock protects all read/write access to the
    internal settings dict and the underlying file.
    """

    def __init__(self, base_dir: Optional[str] = None) -> None:
        """Initialise the config manager.

        Args:
            base_dir: Root directory of the application.  When *None* the
                directory containing this source file is used.
        """
        if base_dir is not None:
            self._base_dir = Path(base_dir).resolve()
        else:
            # Fall back to the directory that contains *this* module.
            self._base_dir = Path(__file__).resolve().parent

        self._settings_path = self._base_dir / "data" / "settings.json"
        self._lock = threading.RLock()
        self._settings: dict[str, Any] = {}
        self._api_key_index: int = 0

        self.load()
        logger.info("ConfigManager initialised  base_dir=%s", self._base_dir)

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------

    @property
    def base_dir(self) -> Path:
        """Return the resolved application base directory."""
        return self._base_dir

    def resolve_path(self, relative: str) -> Path:
        """Convert a path relative to *base_dir* into an absolute ``Path``.

        Args:
            relative: A forward- or back-slash separated relative path.

        Returns:
            The resolved absolute :class:`~pathlib.Path`.
        """
        return (self._base_dir / relative).resolve()

    # ------------------------------------------------------------------
    # Core CRUD
    # ------------------------------------------------------------------

    def get(self, key: str, default: Any = None) -> Any:
        """Return the value for *key*, falling back to *default*.

        If *default* is ``None`` and the key exists in ``DEFAULTS``, the
        global default is returned instead.
        """
        with self._lock:
            if key in self._settings:
                return self._settings[key]
            if default is not None:
                return default
            return DEFAULTS.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set *key* to *value* and persist immediately."""
        with self._lock:
            old = self._settings.get(key)
            self._settings[key] = value
            self.save()
        logger.debug("Setting changed  %s: %r -> %r", key, old, value)

    def batch_update(self, updates: dict[str, Any]) -> None:
        """Update multiple settings in a single batch and save once."""
        with self._lock:
            changed = False
            for key, value in updates.items():
                old = self._settings.get(key)
                if old != value:
                    self._settings[key] = value
                    changed = True
                    logger.debug("Setting changed (batch) %s: %r -> %r", key, old, value)
            if changed:
                self.save()

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self) -> None:
        """Write the current settings to ``data/settings.json``.

        The parent directory is created automatically if it does not exist.
        A temporary file is written first and then replaced to avoid
        corruption on power loss.
        """
        with self._lock:
            try:
                self._settings_path.parent.mkdir(parents=True, exist_ok=True)

                # Create a backup of the existing settings before overwrite
                if self._settings_path.exists():
                    bak_path = self._settings_path.with_suffix(".json.bak")
                    try:
                        import shutil
                        shutil.copy2(str(self._settings_path), str(bak_path))
                    except Exception as e:
                        logger.warning("Failed to create settings backup: %s", e)

                tmp_path = self._settings_path.with_suffix(".tmp")
                with open(tmp_path, "w", encoding="utf-8") as fh:
                    json.dump(self._settings, fh, indent=2, ensure_ascii=False)

                # Atomic replacement on Windows & Unix
                import os as _os
                _os.replace(str(tmp_path), str(self._settings_path))

                logger.debug("Settings saved  %s", self._settings_path)
            except OSError as exc:
                logger.error("Failed to save settings: %s", exc)

    def load(self) -> None:
        """Load settings from disk and merge with ``DEFAULTS``.

        Missing keys are filled from ``DEFAULTS``; unknown keys already
        present on disk are preserved.
        """
        with self._lock:
            merged: dict[str, Any] = dict(DEFAULTS)
            loaded = False

            if self._settings_path.is_file():
                try:
                    with open(self._settings_path, "r", encoding="utf-8") as fh:
                        stored = json.load(fh)
                    if isinstance(stored, dict):
                        merged.update(stored)
                        loaded = True
                        logger.info("Settings loaded  %s", self._settings_path)
                    else:
                        logger.warning(
                            "Settings file is not a JSON object – using defaults"
                        )
                except (json.JSONDecodeError, OSError) as exc:
                    logger.error(
                        "Error reading settings (%s) – trying backup settings.json.bak", exc
                    )
                    bak_path = self._settings_path.with_suffix(".json.bak")
                    if bak_path.is_file():
                        try:
                            with open(bak_path, "r", encoding="utf-8") as fh:
                                stored = json.load(fh)
                            if isinstance(stored, dict):
                                merged.update(stored)
                                loaded = True
                                logger.info("Settings loaded from backup %s", bak_path)
                            else:
                                logger.warning("Backup settings file is not a JSON object")
                        except Exception as bak_exc:
                            logger.error("Error reading backup settings (%s)", bak_exc)

            if not loaded and not self._settings_path.is_file():
                logger.info(
                    "No settings file found at %s – using defaults",
                    self._settings_path,
                )

            self._settings = merged

    # ------------------------------------------------------------------
    # API-key management
    # ------------------------------------------------------------------

    def get_api_keys(self) -> list[str]:
        """Return the current list of online API keys."""
        with self._lock:
            keys = self._settings.get("online_api_keys", [])
            return list(keys) if isinstance(keys, list) else []

    def add_api_key(self, key: str) -> None:
        """Append *key* to the API key list and save."""
        if not key or not isinstance(key, str):
            logger.warning("Attempted to add empty or invalid API key")
            return
        with self._lock:
            keys = self.get_api_keys()
            if key not in keys:
                keys.append(key)
                self._settings["online_api_keys"] = keys
                self.save()
                logger.info("API key added  (total: %d)", len(keys))
            else:
                logger.info("API key already present – skipped")

    def remove_api_key(self, index: int) -> None:
        """Remove the API key at *index* and save.

        Args:
            index: Zero-based position in the key list.
        """
        with self._lock:
            keys = self.get_api_keys()
            if 0 <= index < len(keys):
                removed = keys.pop(index)
                self._settings["online_api_keys"] = keys
                # Reset rotation counter if it's now out of range.
                if self._api_key_index >= len(keys):
                    self._api_key_index = 0
                self.save()
                logger.info(
                    "API key removed  index=%d  remaining=%d", index, len(keys)
                )
            else:
                logger.warning(
                    "remove_api_key: index %d out of range (len=%d)",
                    index,
                    len(keys),
                )

    def rotate_api_key(self) -> Optional[str]:
        """Return the next API key using round-robin rotation.

        Returns:
            The selected key, or ``None`` when no keys are configured.
        """
        with self._lock:
            keys = self.get_api_keys()
            if not keys:
                logger.warning("No API keys configured")
                return None
            key = keys[self._api_key_index % len(keys)]
            self._api_key_index = (self._api_key_index + 1) % len(keys)
            logger.debug(
                "API key rotated  index=%d/%d",
                self._api_key_index,
                len(keys),
            )
            return key
