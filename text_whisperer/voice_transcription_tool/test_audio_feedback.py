#!/usr/bin/env python3
"""
Quick test script for audio feedback functionality.
Run this to test if audio feedback is working correctly.
"""

import time
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from audio.feedback import AudioFeedback

def test_audio_feedback():
    """Test different audio feedback options."""
    print("🎵 Testing Audio Feedback System")
    print("=" * 40)
    
    # Test with default beep
    print("\n1. Testing system beep feedback...")
    feedback = AudioFeedback({
        'audio_feedback_enabled': True,
        'audio_feedback_type': 'beep',
        'audio_feedback_volume': 0.5
    })
    
    print("   Playing start sound (high beep)...")
    feedback.play_start()
    time.sleep(1)
    
    print("   Playing stop sound (low beep)...")
    feedback.play_stop()
    time.sleep(1)
    
    # Test with TTS if available
    print("\n2. Testing text-to-speech feedback...")
    feedback.set_feedback_type('tts')
    
    print("   Playing start sound (TTS)...")
    feedback.play_start()
    time.sleep(2)
    
    print("   Playing stop sound (TTS)...")
    feedback.play_stop()
    time.sleep(2)
    
    # Test volume control
    print("\n3. Testing volume control...")
    feedback.set_feedback_type('beep')
    
    print("   Playing at 100% volume...")
    feedback.set_volume(1.0)
    feedback.play_start()
    time.sleep(1)
    
    print("   Playing at 25% volume...")
    feedback.set_volume(0.25)
    feedback.play_start()
    time.sleep(1)
    
    # Test enable/disable
    print("\n4. Testing enable/disable...")
    feedback.set_enabled(False)
    print("   Feedback disabled - should hear nothing...")
    feedback.play_start()
    time.sleep(1)
    
    print("\n✅ Audio feedback test complete!")
    print("\nNotes:")
    print("- If you didn't hear any sounds, check your system audio")
    print("- TTS requires pyttsx3 to be installed")
    print("- For better audio, install pygame")

if __name__ == "__main__":
    test_audio_feedback()