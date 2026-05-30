"""
FocusFlow System Test Script
============================
Tests all modules of FocusFlow for correct imports, instantiation, and basic functionality.
"""

import os
import sys
from PIL import Image, ImageDraw, ImageFont

# Reconfigure stdout for utf-8 on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

# Ensure we import from current directory
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from config_manager import ConfigManager
from ocr_engine import OCREngine
from ocr_cleaner import OCRCleaner
from knowledge_base import KnowledgeBase
from history_manager import HistoryManager
from ai_engine import AIEngine
from online_engine import OnlineEngine
from offline_engine import OfflineEngine

def run_tests():
    print("=== FocusFlow Integration Test ===")
    
    # 1. Config Manager
    print("\n1. Testing ConfigManager...")
    cfg = ConfigManager(os.path.abspath(os.path.dirname(__file__)))
    print(f"Base Directory: {cfg.base_dir}")
    print(f"Mode: {cfg.get('mode')}")
    print(f"llm_binary: {cfg.get('llm_binary')}")
    
    # 2. OCR Engine
    print("\n2. Testing OCREngine...")
    ocr = OCREngine(cfg)
    if not ocr.is_ready():
        print(f"FAIL: {ocr.status_message()}")
    else:
        print(f"SUCCESS: {ocr.status_message()}")
        
        # Test OCR on a generated image
        print("Generating test image...")
        img = Image.new('RGB', (500, 200), color=(255, 255, 255))
        d = ImageDraw.Draw(img)
        try:
            # Try to load a font, otherwise default
            font = ImageFont.truetype("arial.ttf", 20)
        except Exception:
            font = ImageFont.load_default()
        d.text((20, 50), "FocusFlow Test: Can you read this line?", fill=(0, 0, 0), font=font)
        d.text((20, 100), "Another line with some symbols! @#$%", fill=(0, 0, 0), font=font)
        
        text, err = ocr.extract_text(img)
        if err:
            print(f"OCR Error: {err}")
        else:
            print(f"OCR Output:\n---\n{text}\n---")
            
    # 3. OCR Cleaner
    print("\n3. Testing OCRCleaner...")
    cleaner = OCRCleaner()
    dirty_text = "FocusFlow   Test:   Can   you   read   this   line? \n\nAnother line  with some symbols! @#$%\nAsk Gemini\nNetlify UI"
    cleaned, quality, warnings = cleaner.clean(dirty_text)
    print(f"Cleaned Text:\n---\n{cleaned}\n---")
    print(f"Quality: {quality}")
    print(f"Warnings: {warnings}")
    
    # 4. Knowledge Base
    print("\n4. Testing KnowledgeBase...")
    kb = KnowledgeBase(os.path.abspath(os.path.dirname(__file__)))
    topics = kb.get_all_topics()
    print(f"Loaded {len(topics)} topics from knowledge base.")
    # Search for derivatives
    context = kb.get_context("What is the derivative of x^2?")
    print(f"Context for 'derivative':\n---\n{context}\n---")
    
    # 5. History Manager
    print("\n5. Testing HistoryManager...")
    hm = HistoryManager(os.path.abspath(os.path.dirname(__file__)), cfg)
    print(f"Loaded {len(hm.get_entries())} history entries.")
    
    # 6. AI Engine Configuration
    print("\n6. Testing AIEngine...")
    ai = AIEngine(cfg, kb)
    print("AI Engine initialized successfully.")
    
    print("\n=== Integration Test Finished ===")

if __name__ == "__main__":
    run_tests()
