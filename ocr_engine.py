"""FocusFlow – Tesseract OCR engine wrapper.

Locates a bundled (or system-installed) Tesseract binary, applies a
configurable image-preprocessing pipeline, and returns extracted text.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import Any, Optional, Tuple

from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger("focusflow.ocr")


class OCREngine:
    """Thin wrapper around the Tesseract CLI.

    The engine tries to locate Tesseract in this order:

    1. Bundled path relative to the application's *base_dir*
       (``Tesseract-OCR/tesseract.exe``).
    2. The system ``PATH``.

    Image preprocessing steps are individually togglable via config flags.
    """

    # Default Tesseract sub-path inside the application directory
    _BUNDLED_EXE = "Tesseract-OCR/tesseract.exe"
    _BUNDLED_TESSDATA = "Tesseract-OCR/tessdata"

    def __init__(self, config: Any) -> None:
        self.config = config
        self.logger = logger
        self.tesseract_path: Optional[str] = None
        self.tessdata_dir: Optional[str] = None
        self._ready: bool = False
        self._find_tesseract()

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def _find_tesseract(self) -> None:
        """Locate the Tesseract binary, preferring the bundled copy."""

        # 1. Bundled path (resolved via config helper)
        try:
            bundled_exe = self.config.resolve_path(self._BUNDLED_EXE)
            if os.path.isfile(bundled_exe):
                self.tesseract_path = bundled_exe
                self.tessdata_dir = self.config.resolve_path(
                    self._BUNDLED_TESSDATA
                )
                self._ready = True
                self.logger.info("Tesseract found (bundled): %s", bundled_exe)
                return
        except Exception:
            self.logger.debug("resolve_path unavailable or failed – skipping bundled check.")

        # 2. System PATH
        system_tess = shutil.which("tesseract")
        if system_tess is not None:
            self.tesseract_path = system_tess
            self.tessdata_dir = None  # let Tesseract use its own default
            self._ready = True
            self.logger.info("Tesseract found (system): %s", system_tess)
            return

        self.logger.warning("Tesseract binary NOT found.")

    # ------------------------------------------------------------------
    # Status helpers
    # ------------------------------------------------------------------

    def is_ready(self) -> bool:
        """Return *True* if a usable Tesseract binary was found."""
        return self._ready

    def status_message(self) -> str:
        """Human-readable status string."""
        if self._ready:
            return f"OCR: Tesseract ready at {self.tesseract_path}"
        return "OCR: Tesseract NOT FOUND – install Tesseract or place it in Tesseract-OCR/"

    # ------------------------------------------------------------------
    # Preprocessing pipeline
    # ------------------------------------------------------------------

    def _preprocess(self, image: Image.Image) -> Image.Image:
        """Apply the configurable preprocessing pipeline.

        Each step is gated by a config flag (all default to *True*).
        """

        img = image.copy()

        # 1. Grayscale conversion
        if self.config.get("ocr_preprocess_grayscale", True):
            img = img.convert("L")
            self.logger.debug("Preprocessing: grayscale applied.")

        # 2. Contrast enhancement
        if self.config.get("ocr_preprocess_contrast", True):
            factor: float = self.config.get("ocr_contrast_factor", 1.5)
            if img.mode == "L":
                img = img.convert("RGB")
            img = ImageEnhance.Contrast(img).enhance(factor)
            self.logger.debug("Preprocessing: contrast (×%.2f) applied.", factor)

        # 3. Sharpening
        if self.config.get("ocr_preprocess_sharpen", True):
            img = img.filter(ImageFilter.SHARPEN)
            self.logger.debug("Preprocessing: sharpen applied.")

        # 4. Denoising (median filter)
        if self.config.get("ocr_preprocess_denoise", True):
            median_size: int = self.config.get("ocr_median_size", 3)
            img = img.filter(ImageFilter.MedianFilter(size=median_size))
            self.logger.debug(
                "Preprocessing: median denoise (size %d) applied.", median_size
            )

        # 5. Thresholding → binary
        if self.config.get("ocr_preprocess_threshold", True):
            threshold_val: int = self.config.get("ocr_threshold_value", 128)
            gray = img.convert("L")
            img = gray.point(lambda p: 255 if p > threshold_val else 0, mode="1")
            self.logger.debug(
                "Preprocessing: binary threshold (%d) applied.", threshold_val
            )

        return img

    # ------------------------------------------------------------------
    # Core OCR
    # ------------------------------------------------------------------

    def extract_text(self, image: Image.Image) -> Tuple[str, Optional[str]]:
        """Run Tesseract on a PIL *Image*.

        Returns
        -------
        tuple[str, str | None]
            ``(extracted_text, error_message)``.  *error_message* is
            ``None`` on success.
        """

        if not self._ready:
            return "", "Tesseract is not available."

        # --- ensure temp directory exists --------------------------------
        try:
            temp_dir = self.config.resolve_path("temp")
        except Exception:
            temp_dir = os.path.join(tempfile.gettempdir(), "focusflow_temp")
        os.makedirs(temp_dir, exist_ok=True)

        # --- preprocess --------------------------------------------------
        try:
            processed = self._preprocess(image)
        except Exception as exc:
            self.logger.exception("Preprocessing failed.")
            return "", f"Preprocessing error: {exc}"

        # --- save to a temporary file ------------------------------------
        run_id = uuid.uuid4().hex
        tmp_in = os.path.join(temp_dir, f"ocr_input_{run_id}.png")
        tmp_out_base = os.path.join(temp_dir, f"ocr_output_{run_id}")
        tmp_out_txt = tmp_out_base + ".txt"

        try:
            try:
                processed.save(tmp_in)
            except Exception as exc:
                self.logger.exception("Failed to save preprocessed image.")
                return "", f"Image save error: {exc}"

            # --- build command -----------------------------------------------
            cmd: list[str] = [
                str(self.tesseract_path),
                tmp_in,
                tmp_out_base,
                "--psm", "3",
                "--oem", "3",
                "-c", "preserve_interword_spaces=1",
                "-l", self.config.get("ocr_lang", "eng"),
            ]

            if self.tessdata_dir and os.path.isdir(self.tessdata_dir):
                cmd.extend(["--tessdata-dir", str(self.tessdata_dir)])

            self.logger.debug("Running: %s", " ".join(cmd))

            # --- execute Tesseract -------------------------------------------
            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=self.config.get("ocr_timeout", 30),
                    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                )
            except FileNotFoundError:
                self.logger.error("Tesseract binary not found at runtime.")
                self._ready = False
                return "", "Tesseract binary not found at runtime."
            except subprocess.TimeoutExpired:
                self.logger.error("Tesseract timed out.")
                return "", "OCR timed out."
            except Exception as exc:
                self.logger.exception("Unexpected Tesseract error.")
                return "", f"OCR error: {exc}"

            if result.returncode != 0:
                err_msg = (result.stderr or "").strip()
                self.logger.error("Tesseract exited %d: %s", result.returncode, err_msg)
                return "", f"Tesseract error (exit {result.returncode}): {err_msg}"

            # --- read output -------------------------------------------------
            try:
                with open(tmp_out_txt, "r", encoding="utf-8-sig", errors="replace") as fh:
                    text = fh.read()
            except FileNotFoundError:
                self.logger.error("Tesseract output file not found.")
                return "", "OCR output file missing."
            except Exception as exc:
                self.logger.exception("Failed to read OCR output.")
                return "", f"Read error: {exc}"

            self.logger.info(
                "OCR complete – extracted %d characters.", len(text.strip())
            )
            return text, None

        finally:
            # --- cleanup temp files (best-effort) ----------------------------
            for fp in (tmp_in, tmp_out_txt):
                try:
                    if os.path.exists(fp):
                        os.remove(fp)
                except OSError:
                    pass
