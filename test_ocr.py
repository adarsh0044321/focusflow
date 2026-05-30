import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Ensure we import from current directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
from config_manager import ConfigManager
from ocr_engine import OCREngine

cfg = ConfigManager()
# Disable preprocessing for the first test
cfg.set("ocr_preprocessing", False)

ocr = OCREngine(cfg)

if not ocr.is_ready():
    print("OCR is not ready!")
    print(ocr.status_message())
    sys.exit(1)

print("Creating a test image with text...")
img = Image.new('RGB', (400, 200), color=(255, 255, 255))
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

