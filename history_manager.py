"""
FocusFlow History Manager
==========================
Persists a chronological log of OCR → LLM interactions as JSON, with
automatic backup, screenshot saving, and bounded retrieval.

Files (relative to base_dir):
    data/history.json          — primary history file
    data/history.backup.json   — automatic backup before each save
    data/screenshots/          — saved screenshot images
"""

import json
import logging
import os
import shutil
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

try:
    from PIL import Image
except ImportError:  # PIL is optional at import time
    Image = None  # type: ignore[assignment,misc]

from config_manager import ConfigManager

logger = logging.getLogger("focusflow.history")


class HistoryManager:
    """Manages the interaction history with JSON persistence.

    Each entry records OCR text, the generated answer, timing metrics,
    quality flags, and the mode used.  Screenshots can optionally be saved
    alongside the JSON log.

    Attributes:
        base_dir:      Resolved application root.
        history_path:  Path to ``data/history.json``.
        backup_path:   Path to ``data/history.backup.json``.
        screenshot_dir: Path to ``data/screenshots/``.
    """

    def __init__(self, base_dir: str | Path, config: ConfigManager) -> None:
        """Load (or create) the history file.

        Args:
            base_dir: Application root directory.
            config:   Active :class:`ConfigManager` instance (used to check
                whether screenshot saving is enabled, etc.).
        """
        self.base_dir: Path = Path(base_dir).resolve()
        self.config = config

        self.history_path: Path = self.base_dir / "data" / "history.json"
        self.backup_path: Path = self.base_dir / "data" / "history.backup.json"
        self.screenshot_dir: Path = self.base_dir / "data" / "screenshots"

        self._entries: list[dict[str, Any]] = []
        self._lock = threading.RLock()

        self._load()
        logger.info(
            "HistoryManager initialised  entries=%d  path=%s",
            len(self._entries),
            self.history_path,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add_entry(self, entry_dict: dict[str, Any]) -> None:
        """Append *entry_dict* to history and persist.

        Missing fields are filled with sensible defaults so callers do not
        need to supply every key.

        Args:
            entry_dict: Interaction record (see module docstring for schema).
        """
        template: dict[str, Any] = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "screenshot_path": "",
            "raw_ocr": "",
            "cleaned_ocr": "",
            "answer": "",
            "ocr_quality": "unknown",
            "ocr_warnings": [],
            "ocr_duration_s": 0.0,
            "llm_duration_s": 0.0,
            "answer_mode": self.config.get("answer_mode", "concise"),
            "capture_mode": self.config.get("capture_mode", "region"),
            "mode": self.config.get("mode", "offline"),
        }
        template.update(entry_dict)
        with self._lock:
            self._entries.append(template)
            self._save()
        logger.info(
            "History entry added  total=%d  ts=%s",
            len(self._entries),
            template["timestamp"],
        )

    def save_screenshot(
        self,
        image: Any,  # PIL.Image.Image
        timestamp: str,
    ) -> str:
        """Save a PIL Image to the screenshots directory.

        Args:
            image:     A ``PIL.Image.Image`` instance.
            timestamp: Human-readable timestamp used to build the filename.

        Returns:
            The absolute path to the saved image, or an empty string on
            failure.
        """
        if Image is None:
            logger.error("Pillow is not installed – cannot save screenshot")
            return ""

        if not isinstance(image, Image.Image):
            logger.error("save_screenshot: expected PIL.Image, got %s", type(image))
            return ""

        try:
            self.screenshot_dir.mkdir(parents=True, exist_ok=True)

            # Build a filesystem-safe filename from the timestamp.
            safe_ts = (
                timestamp.replace(":", "-").replace(" ", "_").replace("/", "-")
            )
            filename = f"screenshot_{safe_ts}.png"
            filepath = self.screenshot_dir / filename

            image.save(str(filepath), format="PNG", optimize=True)
            logger.debug("Screenshot saved  %s", filepath)
            return str(filepath)
        except Exception as exc:
            logger.error("Failed to save screenshot: %s", exc)
            return ""

    def get_entries(self, limit: int = 50) -> list[dict[str, Any]]:
        """Return the most recent *limit* history entries (newest first).

        Args:
            limit: Maximum number of entries to return.  Use ``0`` or a
                negative value to retrieve everything.

        Returns:
            A list of entry dicts ordered newest-first.
        """
        with self._lock:
            if limit <= 0:
                return list(reversed(self._entries))
            return list(reversed(self._entries[-limit:]))

    def clear(self) -> None:
        """Delete all history entries and persist the empty list."""
        with self._lock:
            count = len(self._entries)
            self._backup()
            self._entries.clear()
            self._save(skip_backup=True)
            if self.screenshot_dir.exists():
                try:
                    shutil.rmtree(self.screenshot_dir)
                except Exception as exc:
                    logger.warning("Failed to clean up screenshot directory: %s", exc)
        logger.info("History cleared  (removed %d entries)", count)

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _save(self, skip_backup: bool = False) -> None:
        """Write ``_entries`` to JSON, creating a backup first."""
        with self._lock:
            if not skip_backup:
                self._backup()
            try:
                self.history_path.parent.mkdir(parents=True, exist_ok=True)

                tmp_path = self.history_path.with_suffix(".tmp")
                with open(tmp_path, "w", encoding="utf-8") as fh:
                    json.dump(self._entries, fh, indent=2, ensure_ascii=False)

                # Atomic replacement on Windows & Unix
                import os as _os
                _os.replace(str(tmp_path), str(self.history_path))

                logger.debug("History saved  entries=%d", len(self._entries))
            except OSError as exc:
                logger.error("Failed to save history: %s", exc)

    def _backup(self) -> None:
        """Copy ``history.json`` → ``history.backup.json`` if it exists."""
        with self._lock:
            if not self.history_path.is_file():
                return
            try:
                shutil.copy2(str(self.history_path), str(self.backup_path))
                logger.debug("History backup created  %s", self.backup_path)
            except Exception as exc:
                logger.warning("Failed to create history backup: %s", exc)

    def _load(self) -> None:
        """Load entries from disk, falling back to backup then empty list."""
        with self._lock:
            self._entries = self._read_json(self.history_path)
            if self._entries is not None:
                return

            logger.warning(
                "Primary history file unreadable – trying backup at %s",
                self.backup_path,
            )
            self._entries = self._read_json(self.backup_path)
            if self._entries is not None:
                return

            logger.info("No usable history file found – starting fresh")
            self._entries = []

    def _read_json(self, path: Path) -> Optional[list[dict[str, Any]]]:
        """Attempt to read a JSON array from *path*.

        Returns:
            The parsed list, or ``None`` on any failure.
        """
        if not path.is_file():
            return None
        try:
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, list):
                return data
            logger.warning("History file is not a JSON array: %s", path)
            return None
        except (json.JSONDecodeError, OSError) as exc:
            logger.error("Error reading history file %s: %s", path, exc)
            return None
