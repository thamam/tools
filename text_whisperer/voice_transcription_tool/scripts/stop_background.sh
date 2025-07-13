#!/bin/bash

echo "Stopping Voice Transcription Tool background service..."
systemctl --user stop voice-transcription-tool.service
systemctl --user disable voice-transcription-tool.service
echo "Service stopped and disabled from auto-start."
