#!/usr/bin/env python3
"""
Voice Transcription Tool - Root Entry Point
Delegates to the actual main.py in voice_transcription_tool/
"""

import sys
import os
from pathlib import Path

# Add voice_transcription_tool to path and run its main
sys.path.insert(0, str(Path(__file__).parent / "voice_transcription_tool"))

if __name__ == "__main__":
    from voice_transcription_tool.main import main
    sys.exit(main())
