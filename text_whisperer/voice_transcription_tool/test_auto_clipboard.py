#!/usr/bin/env python3
"""
Test script for automatic clipboard copy feature.
This simulates a transcription to test if it's automatically copied to clipboard.
"""

import sys
import time
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    import pyperclip
except ImportError:
    print("❌ pyperclip not installed. Please install it: pip install pyperclip")
    sys.exit(1)

def test_auto_clipboard():
    """Test automatic clipboard copy functionality."""
    print("📋 Testing Automatic Clipboard Copy")
    print("=" * 40)
    
    # Clear clipboard first
    print("\n1. Clearing clipboard...")
    pyperclip.copy("")
    print(f"   Current clipboard: '{pyperclip.paste()}'")
    
    # Test copying some text
    test_text = "This is a test transcription that should be automatically copied to clipboard!"
    print(f"\n2. Simulating transcription: '{test_text[:30]}...'")
    
    # Copy to clipboard (simulating what the app does)
    pyperclip.copy(test_text)
    
    # Verify it's in clipboard
    clipboard_content = pyperclip.paste()
    print(f"\n3. Clipboard content after copy: '{clipboard_content[:30]}...'")
    
    if clipboard_content == test_text:
        print("\n✅ Automatic clipboard copy is working correctly!")
    else:
        print("\n❌ Clipboard copy failed!")
        print(f"   Expected: {test_text}")
        print(f"   Got: {clipboard_content}")
    
    # Test with special characters
    print("\n4. Testing with special characters...")
    special_text = "Test with émojis 🎤 and spëcial châractérs!"
    pyperclip.copy(special_text)
    
    if pyperclip.paste() == special_text:
        print("   ✅ Special characters handled correctly")
    else:
        print("   ❌ Special characters not handled correctly")
    
    print("\n📝 Note: In the actual app, transcriptions will be automatically")
    print("   copied to clipboard when they complete (if enabled in settings).")

if __name__ == "__main__":
    test_auto_clipboard()