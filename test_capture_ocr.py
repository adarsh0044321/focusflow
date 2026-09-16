import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from config_manager import ConfigManager
from ocr_engine import OCREngine
from screen_capture import ScreenCapture


class TestCaptureOCR(unittest.TestCase):
    """Test suite for screen capture and OCR integration."""

    def setUp(self):
        self.cfg = ConfigManager()
        self.ocr = OCREngine(self.cfg)
        self.cap = ScreenCapture(self.cfg)

    @patch("screen_capture.mss.MSS")
    def test_screen_capture_fullscreen_mocked(self, mock_mss):
        mock_instance = MagicMock()
        mock_mss.return_value.__enter__.return_value = mock_instance
        mock_instance.monitors = [{"left": 0, "top": 0, "width": 100, "height": 100},
                                  {"left": 0, "top": 0, "width": 100, "height": 100}]

        fake_raw = MagicMock()
        fake_raw.size = (10, 10)
        fake_raw.bgra = b"\x00" * (10 * 10 * 4)
        mock_instance.grab.return_value = fake_raw

        img = self.cap.capture_fullscreen(1)
        self.assertIsInstance(img, Image.Image)
        self.assertEqual(img.size, (10, 10))

    def test_ocr_extract_text_empty_image(self):
        blank = Image.new("RGB", (100, 100), color=(255, 255, 255))
        # OCR on blank image should succeed and return empty or string, without crashing
        text, err = self.ocr.extract_text(blank)
        self.assertIsInstance(text, str)
        self.assertIsNone(err)


if __name__ == "__main__":
    import mss
    print("Running standalone diagnostic capture with mss...")
    try:
        with mss.mss() as sct:
            raw = sct.grab(sct.monitors[1])
            img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
            img.save("test_screen_capture.png")
            print(f"Captured size: {img.size}")

        cfg = ConfigManager()
        ocr = OCREngine(cfg)
        text, err = ocr.extract_text(img)
        print(f"Error: {err}")
        print(f"Text detected: {len(text)} chars")
    except Exception as exc:
        print(f"Diagnostic run failed: {exc}")

