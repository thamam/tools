from setuptools import setup, find_packages

setup(
    name="voice-transcription-tool",
    version="2.0.0",
    description="A powerful speech-to-text application with global hotkeys and voice training",
    packages=find_packages(),
    install_requires=[
        "keyboard>=0.13.5",
        "pyperclip>=1.9.0",
        "pyaudio>=0.2.14",
        "openai-whisper>=20231117",
        "SpeechRecognition>=3.10.0",
        "torch>=1.9.0",
        "numpy>=1.21.0",
        "requests>=2.25.0"
    ],
    python_requires=">=3.7",
    entry_points={
        "console_scripts": [
            "voice-transcription=voice_transcription_tool.main:main",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
