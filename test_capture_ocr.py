import os
import sys
import mss
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from config_manager import ConfigManager
from ocr_engine import OCREngine

print("Capturing screen with mss...")
with mss.mss() as sct:
    raw = sct.grab(sct.monitors[1])
    img = Image.frombytes("RGB", raw.size, raw.bgra, "raw", "BGRX")
    img.save("test_screen_capture.png")

print(f"Captured size: {img.size}")

cfg = ConfigManager()
ocr = OCREngine(cfg)

print("Running Tesseract...")
text, err = ocr.extract_text(img)
print(f"Error: {err}")
print(f"Text detected: {len(text)} chars")
if len(text) > 0:
    print(f"Preview: {text[:200]!r}")
else:
    print("No text detected!")
