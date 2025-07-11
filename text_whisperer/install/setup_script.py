#!/usr/bin/env python3
"""
Voice Transcription Tool - Interactive Setup Script
Handles virtual environment creation and dependency installation
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

class Colors:
    """ANSI color codes for terminal output"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_colored(text, color=Colors.ENDC):
    """Print colored text to terminal"""
    print(f"{color}{text}{Colors.ENDC}")

def print_header(text):
    """Print a header with formatting"""
    print_colored("\n" + "="*60, Colors.HEADER)
    print_colored(f"  {text}", Colors.HEADER + Colors.BOLD)
    print_colored("="*60, Colors.HEADER)

def run_command(cmd, check=True, capture_output=False):
    """Run a shell command and return result"""
    try:
        if isinstance(cmd, str):
            cmd = cmd.split()
        
        result = subprocess.run(
            cmd, 
            check=check, 
            capture_output=capture_output, 
            text=True
        )
        return result
    except subprocess.CalledProcessError as e:
        if capture_output:
            return None
        print_colored(f"Command failed: {' '.join(cmd)}", Colors.FAIL)
        print_colored(f"Error: {e}", Colors.FAIL)
        return None

def check_command_exists(command):
    """Check if a command exists in PATH"""
    return shutil.which(command) is not None

def detect_environment():
    """Detect current Python environment"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    in_conda = os.environ.get('CONDA_DEFAULT_ENV') is not None
    
    return {
        'in_venv': in_venv,
        'in_conda': in_conda,
        'python_executable': sys.executable,
        'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    }

def get_user_choice(prompt, options, default=None):
    """Get user choice from a list of options"""
    print_colored(f"\n{prompt}", Colors.OKBLUE)
    
    for i, option in enumerate(options, 1):
        default_marker = " (default)" if default and i == default else ""
        print(f"  {i}. {option}{default_marker}")
    
    while True:
        try:
            choice = input(f"\nEnter choice (1-{len(options)}): ").strip()
            
            if not choice and default:
                return default
            
            choice_num = int(choice)
            if 1 <= choice_num <= len(options):
                return choice_num
            else:
                print_colored("Invalid choice. Please try again.", Colors.WARNING)
                
        except (ValueError, KeyboardInterrupt):
            print_colored("Invalid input. Please enter a number.", Colors.WARNING)

def confirm_action(prompt, default=True):
    """Ask user for yes/no confirmation"""
    default_text = "[Y/n]" if default else "[y/N]"
    response = input(f"{prompt} {default_text}: ").strip().lower()
    
    if not response:
        return default
    
    return response in ['y', 'yes', 'true', '1']

def install_system_dependencies():
    """Install system-level dependencies"""
    system = platform.system().lower()
    
    if system == "linux":
        print_colored("\n🔧 Installing Linux system dependencies...", Colors.OKBLUE)
        
        # Detect package manager
        if check_command_exists("apt-get"):
            print("Using apt-get package manager...")
            
            commands = [
                "sudo apt-get update",
                "sudo apt-get install -y portaudio19-dev python3-dev alsa-utils",
                "sudo apt-get install -y build-essential"
            ]
            
            for cmd in commands:
                print(f"Running: {cmd}")
                result = run_command(cmd, check=False)
                if result and result.returncode != 0:
                    print_colored(f"Warning: Command failed: {cmd}", Colors.WARNING)
                    
        elif check_command_exists("yum"):
            print("Using yum package manager...")
            run_command("sudo yum install -y portaudio-devel python3-devel alsa-utils", check=False)
            
        elif check_command_exists("pacman"):
            print("Using pacman package manager...")
            run_command("sudo pacman -S --noconfirm portaudio python alsa-utils", check=False)
            
        else:
            print_colored("Could not detect package manager. Please install manually:", Colors.WARNING)
            print("- portaudio development libraries")
            print("- python development headers")
            print("- alsa-utils (for audio recording)")
            
    elif system == "darwin":  # macOS
        print_colored("\n🔧 Installing macOS system dependencies...", Colors.OKBLUE)
        
        if check_command_exists("brew"):
            print("Using Homebrew...")
            run_command("brew install portaudio", check=False)
        else:
            print_colored("Homebrew not found. Please install:", Colors.WARNING)
            print("1. Install Homebrew: /bin/bash -c \"$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\"")
            print("2. Run: brew install portaudio")
            
    elif system == "windows":
        print_colored("\n🔧 Windows detected - Python packages should work directly", Colors.OKGREEN)
        
    else:
        print_colored(f"\n⚠️  Unknown system: {system}", Colors.WARNING)
        print("You may need to install audio development libraries manually.")

def create_virtual_environment():
    """Create a virtual environment"""
    env_info = detect_environment()
    
    if env_info['in_venv'] or env_info['in_conda']:
        print_colored(f"✅ Already in virtual environment", Colors.OKGREEN)
        return True
    
    print_header("Virtual Environment Setup")
    
    if not confirm_action("Would you like to create a virtual environment?", True):
        print_colored("Continuing without virtual environment...", Colors.WARNING)
        return True
    
    # Choose environment type
    env_options = []
    if check_command_exists("python3") or check_command_exists("python"):
        env_options.append("Python venv (recommended)")
    
    if check_command_exists("conda"):
        env_options.append("Anaconda/Miniconda")
    
    if not env_options:
        print_colored("❌ No virtual environment tools found!", Colors.FAIL)
        return False
    
    choice = get_user_choice("Choose virtual environment type:", env_options, 1)
    
    env_name = input("Environment name (default: voice_transcription): ").strip() or "voice_transcription"
    
    if "venv" in env_options[choice - 1]:
        # Create Python venv
        print(f"Creating Python virtual environment: {env_name}")
        
        python_cmd = "python3" if check_command_exists("python3") else "python"
        run_command(f"{python_cmd} -m venv {env_name}")
        
        # Activation instructions
        if platform.system().lower() == "windows":
            activate_cmd = f"{env_name}\\Scripts\\activate"
        else:
            activate_cmd = f"source {env_name}/bin/activate"
            
        print_colored(f"\n✅ Virtual environment created!", Colors.OKGREEN)
        print_colored(f"To activate it manually: {activate_cmd}", Colors.OKBLUE)
        
        # Auto-activate for this session
        if platform.system().lower() != "windows":
            activate_script = Path(env_name) / "bin" / "activate"
            if activate_script.exists():
                # Update current session's python path
                venv_python = Path(env_name) / "bin" / "python"
                sys.executable = str(venv_python)
                
    else:
        # Create Conda environment
        print(f"Creating Conda environment: {env_name}")
        run_command(f"conda create -n {env_name} python=3.9 -y")
        
        print_colored(f"\n✅ Conda environment created!", Colors.OKGREEN)
        print_colored(f"To activate it manually: conda activate {env_name}", Colors.OKBLUE)
    
    return True

def get_installation_type():
    """Get user's preferred installation type"""
    print_header("Installation Type Selection")
    
    options = [
        "🚀 Full Installation (Whisper + Google Speech + PyAudio) - Recommended",
        "🎯 Local High-Quality (Whisper + PyAudio) - Best accuracy, offline",
        "⚡ Online Fast (Google Speech + PyAudio) - Fast, requires internet", 
        "💡 Minimal Installation (Google Speech + system audio) - Lightweight",
        "🔧 Custom Installation - Choose specific components"
    ]
    
    choice = get_user_choice("Select installation type:", options, 1)
    
    return {
        1: "full",
        2: "whisper", 
        3: "google",
        4: "minimal",
        5: "custom"
    }[choice]

def get_custom_components():
    """Get custom component selection"""
    print_colored("\n🔧 Custom Component Selection", Colors.OKBLUE)
    
    components = {
        'audio_pyaudio': confirm_action("Install PyAudio (better audio recording)?", True),
        'speech_whisper': confirm_action("Install Whisper (local, high-quality speech recognition)?", True),
        'speech_google': confirm_action("Install Google Speech Recognition (online, fast)?", True),
    }
    
    if not (components['speech_whisper'] or components['speech_google']):
        print_colored("⚠️  Warning: No speech recognition engine selected!", Colors.WARNING)
        if confirm_action("Add Google Speech Recognition?", True):
            components['speech_google'] = True
    
    return components

def install_dependencies(install_type):
    """Install Python dependencies based on installation type"""
    print_header("Installing Python Dependencies")
    
    # Get pip command
    pip_cmd = "pip3" if check_command_exists("pip3") else "pip"
    
    if install_type == "full":
        print_colored("📦 Installing full package set...", Colors.OKBLUE)
        run_command(f"{pip_cmd} install -r requirements-full.txt")
        
    elif install_type == "whisper":
        print_colored("📦 Installing Whisper package set...", Colors.OKBLUE)
        run_command(f"{pip_cmd} install -r requirements-base.txt")
        run_command(f"{pip_cmd} install -r requirements-audio.txt")
        run_command(f"{pip_cmd} install -r requirements-whisper.txt")
        
    elif install_type == "google":
        print_colored("📦 Installing Google Speech package set...", Colors.OKBLUE)
        run_command(f"{pip_cmd} install -r requirements-base.txt")
        run_command(f"{pip_cmd} install -r requirements-audio.txt")
        run_command(f"{pip_cmd} install -r requirements-google.txt")
        
    elif install_type == "minimal":
        print_colored("📦 Installing minimal package set...", Colors.OKBLUE)
        run_command(f"{pip_cmd} install -r requirements-minimal.txt")
        
    elif install_type == "custom":
        components = get_custom_components()
        
        print_colored("📦 Installing base components...", Colors.OKBLUE)
        run_command(f"{pip_cmd} install -r requirements-base.txt")
        
        if components['audio_pyaudio']:
            print_colored("📦 Installing PyAudio...", Colors.OKBLUE)
            result = run_command(f"{pip_cmd} install -r requirements-audio.txt", check=False)
            if result and result.returncode != 0:
                print_colored("⚠️  PyAudio installation failed. System audio tools will be used.", Colors.WARNING)
        
        if components['speech_whisper']:
            print_colored("📦 Installing Whisper...", Colors.OKBLUE)
            run_command(f"{pip_cmd} install -r requirements-whisper.txt")
            
        if components['speech_google']:
            print_colored("📦 Installing Google Speech Recognition...", Colors.OKBLUE)
            run_command(f"{pip_cmd} install -r requirements-google.txt")

def test_installation():
    """Test the installation"""
    print_header("Testing Installation")
    
    tests = []
    
    # Test basic imports
    try:
        import keyboard
        tests.append(("Keyboard library", True, "✅"))
    except ImportError:
        tests.append(("Keyboard library", False, "❌"))
    
    try:
        import pyperclip
        tests.append(("Clipboard library", True, "✅"))
    except ImportError:
        tests.append(("Clipboard library", False, "❌"))
    
    # Test audio
    try:
        import pyaudio
        tests.append(("PyAudio", True, "✅"))
    except ImportError:
        # Check for system audio tools
        if check_command_exists("arecord"):
            tests.append(("Audio recording (arecord)", True, "✅"))
        elif check_command_exists("ffmpeg"):
            tests.append(("Audio recording (ffmpeg)", True, "✅"))
        else:
            tests.append(("Audio recording", False, "❌"))
    
    # Test speech recognition
    whisper_available = False
    google_available = False
    
    try:
        import whisper
        tests.append(("Whisper speech recognition", True, "✅"))
        whisper_available = True
    except ImportError:
        tests.append(("Whisper speech recognition", False, "⚠️"))
    
    try:
        import speech_recognition
        tests.append(("Google speech recognition", True, "✅"))
        google_available = True
    except ImportError:
        tests.append(("Google speech recognition", False, "⚠️"))
    
    # Display results
    print("\n📋 Installation Test Results:")
    for name, status, icon in tests:
        color = Colors.OKGREEN if status else Colors.FAIL
        print_colored(f"  {icon} {name}", color)
    
    # Summary
    critical_failed = any(not status for name, status, _ in tests[:2])  # keyboard, pyperclip
    audio_available = any(status for name, status, _ in tests if "audio" in name.lower() or "Audio" in name)
    speech_available = whisper_available or google_available
    
    if critical_failed:
        print_colored("\n❌ Critical dependencies missing! Installation failed.", Colors.FAIL)
        return False
    elif not audio_available:
        print_colored("\n⚠️  No audio recording method available!", Colors.WARNING)
        print("Please install: sudo apt-get install alsa-utils (or ffmpeg)")
        return False
    elif not speech_available:
        print_colored("\n⚠️  No speech recognition engine available!", Colors.WARNING)
        print("Please install Whisper or Google Speech Recognition")
        return False
    else:
        print_colored("\n✅ Installation successful! All components working.", Colors.OKGREEN)
        return True

def show_next_steps():
    """Show next steps after installation"""
    print_header("Next Steps")
    
    print_colored("🎉 Setup complete! Here's how to use your voice transcription tool:\n", Colors.OKGREEN)
    
    print_colored("1. Run the application:", Colors.OKBLUE)
    print("   python voice_transcription.py\n")
    
    print_colored("2. First-time setup:", Colors.OKBLUE)
    print("   • Test recording with the '🎤 Start Recording' button")
    print("   • Enable global hotkeys with '🔥 Toggle Hotkey Mode'")
    print("   • Configure speech engine in '⚙️ Settings'\n")
    
    print_colored("3. Using global hotkeys:", Colors.OKBLUE)
    print("   • Press Ctrl+Shift+V from any application to start/stop recording")
    print("   • Use '📝 Insert at Cursor' to place transcribed text\n")
    
    print_colored("4. Troubleshooting:", Colors.OKBLUE)
    print("   • Check the setup.md file for detailed instructions")
    print("   • Verify microphone permissions if recording fails")
    print("   • Try different speech engines in settings\n")
    
    print_colored("🎤 Happy transcribing!", Colors.BOLD)

def main():
    """Main setup function"""
    print_colored("🎤 Voice Transcription Tool - Interactive Setup", Colors.HEADER + Colors.BOLD)
    print_colored("This script will help you set up the complete environment\n", Colors.OKBLUE)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print_colored("❌ Python 3.7+ required. Current version: " + sys.version, Colors.FAIL)
        sys.exit(1)
    
    print_colored(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} detected", Colors.OKGREEN)
    
    try:
        # Step 1: Virtual Environment
        if not create_virtual_environment():
            print_colored("❌ Virtual environment setup failed", Colors.FAIL)
            sys.exit(1)
        
        # Step 2: System Dependencies
        if confirm_action("Install system dependencies (audio libraries)?", True):
            install_system_dependencies()
        
        # Step 3: Installation Type
        install_type = get_installation_type()
        
        # Step 4: Install Dependencies
        install_dependencies(install_type)
        
        # Step 5: Test Installation
        if test_installation():
            show_next_steps()
        else:
            print_colored("\n❌ Installation completed with issues. Check the logs above.", Colors.WARNING)
            
    except KeyboardInterrupt:
        print_colored("\n\n❌ Setup cancelled by user", Colors.WARNING)
        sys.exit(1)
    except Exception as e:
        print_colored(f"\n❌ Setup failed with error: {e}", Colors.FAIL)
        sys.exit(1)

if __name__ == "__main__":
    main()