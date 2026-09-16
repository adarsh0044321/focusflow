import os
import sys
import unittest
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from config_manager import ConfigManager
from ocr_engine import OCREngine


class TestOCREngine(unittest.TestCase):
    """Unit tests for OCR engine initialization and text extraction."""

    def setUp(self):
        self.cfg = ConfigManager()
        self.ocr = OCREngine(self.cfg)

    def test_ocr_extract_text_rendered_image(self):
        img = Image.new("RGB", (400, 100), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        font = ImageFont.load_default()
        d.text((10, 10), "FOCUSFLOW", fill=(0, 0, 0), font=font)
        
        # If tesseract is ready, run extraction, else verify status message
        if self.ocr.is_ready():
            text, err = self.ocr.extract_text(img)
            self.assertIsNone(err)
            self.assertIsInstance(text, str)
        else:
            msg = self.ocr.status_message()
            self.assertIsInstance(msg, str)


if __name__ == "__main__":
    cfg = ConfigManager()
    cfg.set("ocr_preprocessing", False)
    ocr = OCREngine(cfg)
    if not ocr.is_ready():
        print("OCR is not ready!")
        print(ocr.status_message())
        sys.exit(1)

    print("Creating a test image with text...")
    img = Image.new("RGB", (400, 200), color=(255, 255, 255))
    d = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("arial.ttf", 24)
    except:
        font = ImageFont.load_default()
    d.text((20, 50), "This is a test of Tesseract OCR.\nLine 2 text.", fill=(0, 0, 0), font=font)

    print("Running OCR without preprocessing...")
    text, err = ocr.extract_text(img)
    print(f"Error: {err}")
    print(f"Extracted Text: {text!r}")

    print("\nEnabling preprocessing and testing again...")
    cfg.set("ocr_preprocessing", True)
    text2, err2 = ocr.extract_text(img)
    print(f"Error: {err2}")
    print(f"Extracted Text: {text2!r}")


