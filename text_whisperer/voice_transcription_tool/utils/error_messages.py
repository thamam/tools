"""
utils/error_messages.py - User-friendly error message templates.

Provides centralized, actionable error messages with recovery suggestions.
"""

from typing import Dict, Optional


class ErrorMessages:
    """Centralized error message templates with recovery guidance."""

    # Audio Device Errors
    AUDIO_NO_METHOD = {
        'title': 'Audio System Not Available',
        'message': 'No audio recording method is available on your system.',
        'details': 'PyAudio is required for audio recording.',
        'action': 'Please install PyAudio:\n  • Ubuntu/Debian: sudo apt install python3-pyaudio\n  • Or: pip install pyaudio'
    }

    AUDIO_DEVICE_ERROR = {
        'title': 'Audio Device Error',
        'message': 'Could not access your microphone.',
        'details': 'The selected audio device is not available or in use by another application.',
        'action': 'Try:\n  • Close other audio applications\n  • Check microphone permissions\n  • Select a different device in Settings'
    }

    AUDIO_RECORDING_FAILED = {
        'title': 'Recording Failed',
        'message': 'Could not complete the audio recording.',
        'details': 'An error occurred during recording.',
        'action': 'Try:\n  • Check microphone connection\n  • Test microphone in system settings\n  • Restart the application'
    }

    AUDIO_NO_FRAMES = {
        'title': 'No Audio Captured',
        'message': 'No audio was recorded.',
        'details': 'The microphone may not be receiving input or the volume is too low.',
        'action': 'Try:\n  • Speak louder or move closer to the microphone\n  • Check microphone is not muted\n  • Increase microphone volume in system settings'
    }

    AUDIO_SILENT = {
        'title': 'Silent Audio Detected',
        'message': 'The recorded audio appears to be silent.',
        'details': 'No speech was detected in the recording.',
        'action': 'Please ensure:\n  • Microphone is not muted\n  • Volume level is adequate (look for green audio meter)\n  • You are speaking into the correct microphone'
    }

    # Speech Engine Errors
    ENGINE_NOT_AVAILABLE = {
        'title': 'Speech Engine Not Available',
        'message': 'The selected speech recognition engine is not installed.',
        'details': 'At least one speech engine (Whisper, faster-whisper, or Google) is required.',
        'action': 'Install a speech engine:\n  • pip install openai-whisper  (GPU-accelerated, high quality)\n  • pip install faster-whisper  (4x faster, GPU-accelerated)\n  • pip install SpeechRecognition  (cloud-based, requires internet)'
    }

    ENGINE_MODEL_LOAD_FAILED = {
        'title': 'Model Loading Failed',
        'message': 'Could not load the speech recognition model.',
        'details': 'The model file may be corrupted or insufficient memory available.',
        'action': 'Try:\n  • Select a smaller model (tiny/base instead of large)\n  • Close other applications to free memory\n  • Re-download the model by clearing cache'
    }

    ENGINE_GPU_FAILED = {
        'title': 'GPU Initialization Failed',
        'message': 'Could not initialize GPU acceleration.',
        'details': 'CUDA or GPU drivers may not be properly installed.',
        'action': 'Options:\n  • Enable "Force CPU Mode" in Settings\n  • Install CUDA toolkit and cuDNN libraries\n  • Update GPU drivers\n  • The application will automatically use CPU mode'
    }

    ENGINE_TRANSCRIPTION_FAILED = {
        'title': 'Transcription Failed',
        'message': 'Could not transcribe the audio.',
        'details': 'The speech recognition engine encountered an error.',
        'action': 'Try:\n  • Record again with clearer speech\n  • Try a different speech engine in Settings\n  • Check internet connection (for Google Speech)'
    }

    ENGINE_ALL_FAILED = {
        'title': 'All Engines Failed',
        'message': 'Could not transcribe using any available speech engine.',
        'details': 'All configured speech engines failed to process the audio.',
        'action': 'Please:\n  • Check audio quality (should be clear speech)\n  • Verify at least one engine is properly installed\n  • Try recording in a quieter environment\n  • Check application logs for detailed errors'
    }

    # System & Dependency Errors
    DEPENDENCY_MISSING = {
        'title': 'Dependency Missing',
        'message': 'A required system dependency is not installed.',
        'details': 'Some features require additional system packages.',
        'action': 'Install missing dependencies:\n  • FFmpeg: sudo apt install ffmpeg\n  • xclip: sudo apt install xclip\n  • xdotool: sudo apt install xdotool'
    }

    MEMORY_ERROR = {
        'title': 'Insufficient Memory',
        'message': 'Not enough memory to complete this operation.',
        'details': 'The selected model or operation requires more RAM than available.',
        'action': 'Try:\n  • Close other applications\n  • Select a smaller model size (tiny/base)\n  • Enable CPU mode if using GPU\n  • Restart the application'
    }

    # Configuration Errors
    CONFIG_LOAD_FAILED = {
        'title': 'Configuration Load Failed',
        'message': 'Could not load application settings.',
        'details': 'The configuration file may be corrupted.',
        'action': 'The application will use default settings.\nTo reset: Delete voice_transcription_config.json and restart.'
    }

    CONFIG_SAVE_FAILED = {
        'title': 'Configuration Save Failed',
        'message': 'Could not save application settings.',
        'details': 'Check file permissions in the application directory.',
        'action': 'Your settings will not persist after closing the application.\nCheck write permissions for the config file.'
    }

    # Hotkey Errors
    HOTKEY_REGISTER_FAILED = {
        'title': 'Hotkey Registration Failed',
        'message': 'Could not register the global hotkey.',
        'details': 'The hotkey combination may already be in use by another application.',
        'action': 'Try:\n  • Choose a different hotkey in Settings\n  • Close applications that might use the same hotkey\n  • The recording button will still work'
    }

    # Auto-paste Errors
    AUTOPASTE_FAILED = {
        'title': 'Auto-Paste Failed',
        'message': 'Could not automatically paste the transcribed text.',
        'details': 'xdotool may not be installed or window focus was lost.',
        'action': 'The text has been copied to clipboard.\nYou can paste manually with Ctrl+V.\n\nTo fix auto-paste:\n  • Install xdotool: sudo apt install xdotool\n  • Ensure the target window is focused'
    }

    # Generic Errors
    UNKNOWN_ERROR = {
        'title': 'Unexpected Error',
        'message': 'An unexpected error occurred.',
        'details': 'Please check the application logs for more information.',
        'action': 'Try:\n  • Restart the application\n  • Report this issue with the log file if it persists\n  • Logs are located in: logs/voice_transcription_*.log'
    }

    @classmethod
    def format_error(cls, error_template: Dict[str, str], **kwargs) -> str:
        """
        Format an error message with optional custom details.

        Args:
            error_template: Error template dictionary with title, message, details, action
            **kwargs: Optional overrides for template fields or additional context

        Returns:
            Formatted error message string
        """
        # Merge template with custom kwargs
        error_data = {**error_template, **kwargs}

        # Build formatted message
        parts = []

        if 'message' in error_data:
            parts.append(error_data['message'])

        if 'details' in error_data and error_data['details']:
            parts.append(f"\nDetails: {error_data['details']}")

        if 'action' in error_data and error_data['action']:
            parts.append(f"\n\n{error_data['action']}")

        return '\n'.join(parts)

    @classmethod
    def get_title(cls, error_template: Dict[str, str]) -> str:
        """Get the error title/heading."""
        return error_template.get('title', 'Error')

    @classmethod
    def create_custom_error(cls, title: str, message: str,
                           details: Optional[str] = None,
                           action: Optional[str] = None) -> Dict[str, str]:
        """
        Create a custom error template.

        Args:
            title: Error dialog title
            message: Main error message
            details: Optional detailed explanation
            action: Optional recovery action guidance

        Returns:
            Error template dictionary
        """
        error = {
            'title': title,
            'message': message
        }

        if details:
            error['details'] = details

        if action:
            error['action'] = action

        return error


# Convenience functions for common patterns
def format_audio_error(error_type: str, exception: Optional[Exception] = None) -> tuple:
    """Format audio-related errors with optional exception details."""
    error_map = {
        'no_method': ErrorMessages.AUDIO_NO_METHOD,
        'device': ErrorMessages.AUDIO_DEVICE_ERROR,
        'recording': ErrorMessages.AUDIO_RECORDING_FAILED,
        'no_frames': ErrorMessages.AUDIO_NO_FRAMES,
        'silent': ErrorMessages.AUDIO_SILENT
    }

    template = error_map.get(error_type, ErrorMessages.UNKNOWN_ERROR)
    details = template.get('details', '')

    if exception:
        details = f"{details}\n\nTechnical details: {str(exception)}"

    title = ErrorMessages.get_title(template)
    message = ErrorMessages.format_error(template, details=details)

    return title, message


def format_engine_error(error_type: str, engine_name: Optional[str] = None,
                       exception: Optional[Exception] = None) -> tuple:
    """Format speech engine errors with optional exception details."""
    error_map = {
        'not_available': ErrorMessages.ENGINE_NOT_AVAILABLE,
        'model_load': ErrorMessages.ENGINE_MODEL_LOAD_FAILED,
        'gpu_failed': ErrorMessages.ENGINE_GPU_FAILED,
        'transcription': ErrorMessages.ENGINE_TRANSCRIPTION_FAILED,
        'all_failed': ErrorMessages.ENGINE_ALL_FAILED
    }

    template = error_map.get(error_type, ErrorMessages.UNKNOWN_ERROR)
    details = template.get('details', '')

    if engine_name:
        details = f"Engine: {engine_name}\n{details}"

    if exception:
        details = f"{details}\n\nTechnical details: {str(exception)}"

    title = ErrorMessages.get_title(template)
    message = ErrorMessages.format_error(template, details=details)

    return title, message


def format_system_error(error_type: str, exception: Optional[Exception] = None) -> tuple:
    """Format system-related errors."""
    error_map = {
        'dependency': ErrorMessages.DEPENDENCY_MISSING,
        'memory': ErrorMessages.MEMORY_ERROR,
        'config_load': ErrorMessages.CONFIG_LOAD_FAILED,
        'config_save': ErrorMessages.CONFIG_SAVE_FAILED
    }

    template = error_map.get(error_type, ErrorMessages.UNKNOWN_ERROR)
    details = template.get('details', '')

    if exception:
        details = f"{details}\n\nTechnical details: {str(exception)}"

    title = ErrorMessages.get_title(template)
    message = ErrorMessages.format_error(template, details=details)

    return title, message
