#!/usr/bin/env python3
"""
Test script for wake word detection functionality.
"""

import time
import logging
from utils.wake_word import WakeWordDetector, SimpleWakeWordDetector

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def on_wake_word_detected(wake_word, score):
    """Callback when wake word is detected."""
    print(f"\n🎯 WAKE WORD DETECTED: '{wake_word}' (score: {score:.2f})")
    print("=" * 50)

def test_wake_word_detection():
    """Test wake word detection."""
    print("🎤 Wake Word Detection Test")
    print("=" * 50)
    
    # Try full detector first
    detector = WakeWordDetector(
        callback=on_wake_word_detected,
        wake_words=["hey computer"],
        threshold=0.5
    )
    
    if not detector.is_available():
        print("⚠️  OpenWakeWord not available, using simple detector...")
        detector = SimpleWakeWordDetector(
            callback=on_wake_word_detected,
            wake_phrase="hey computer"
        )
    
    print(f"✅ Detector initialized: {detector.__class__.__name__}")
    print(f"🎯 Wake words: {detector.wake_words if hasattr(detector, 'wake_words') else 'energy-based detection'}")
    
    # Test microphone
    print("\n🧪 Testing microphone...")
    if detector.test_microphone(duration=2.0):
        print("✅ Microphone test passed")
    else:
        print("❌ Microphone test failed")
        return
    
    # Start listening
    print("\n🎧 Starting wake word detection...")
    if detector.start_listening():
        print("✅ Listening started")
        print(f"🗣️  Say 'hey computer' to trigger detection")
        print("⏰ Will listen for 20 seconds...")
        print("Press Ctrl+C to stop early\n")
        
        try:
            # Listen for 20 seconds
            for i in range(20):
                time.sleep(1)
                print(f"\r⏱️  Time remaining: {20-i} seconds", end="", flush=True)
        except KeyboardInterrupt:
            print("\n\n⚠️  Interrupted by user")
        
        # Stop listening
        print("\n\n🛑 Stopping wake word detection...")
        detector.stop_listening()
        print("✅ Detection stopped")
    else:
        print("❌ Failed to start listening")
    
    # Show status
    print("\n📊 Final Status:")
    status = detector.get_status()
    for key, value in status.items():
        print(f"  {key}: {value}")

if __name__ == "__main__":
    test_wake_word_detection()