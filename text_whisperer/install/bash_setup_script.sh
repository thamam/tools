#!/bin/bash

# Voice Transcription Tool - Quick Setup Script
# Alternative bash version for users who prefer shell scripts

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Helper functions
print_header() {
    echo -e "\n${PURPLE}${BOLD}================================================${NC}"
    echo -e "${PURPLE}${BOLD}  $1${NC}"
    echo -e "${PURPLE}${BOLD}================================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Ask user for yes/no input
ask_yes_no() {
    local prompt="$1"
    local default="${2:-y}"
    
    if [ "$default" = "y" ]; then
        prompt="$prompt [Y/n]: "
    else
        prompt="$prompt [y/N]: "
    fi
    
    while true; do
        read -p "$prompt" response
        case ${response:-$default} in
            [Yy]* ) return 0;;
            [Nn]* ) return 1;;
            * ) echo "Please answer yes or no.";;
        esac
    done
}

# Get user choice from options
get_choice() {
    local prompt="$1"
    shift
    local options=("$@")
    
    echo -e "${BLUE}$prompt${NC}"
    for i in "${!options[@]}"; do
        echo "  $((i+1)). ${options[$i]}"
    done
    
    while true; do
        read -p "Enter choice (1-${#options[@]}): " choice
        if [[ "$choice" =~ ^[1-9][0-9]*$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#options[@]}" ]; then
            return $((choice-1))
        else
            print_warning "Invalid choice. Please try again."
        fi
    done
}

# Install system dependencies
install_system_deps() {
    print_header "Installing System Dependencies"
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_info "Detected Linux system"
        
        if command_exists apt-get; then
            echo "Using apt-get package manager..."
            sudo apt-get update
            sudo apt-get install -y portaudio19-dev python3-dev alsa-utils build-essential
            print_success "Linux dependencies installed"
        elif command_exists yum; then
            echo "Using yum package manager..."
            sudo yum install -y portaudio-devel python3-devel alsa-utils
        elif command_exists pacman; then
            echo "Using pacman package manager..."
            sudo pacman -S --noconfirm portaudio python alsa-utils
        else
            print_warning "Could not detect package manager. Please install manually:"
            echo "- portaudio development libraries"
            echo "- python development headers" 
            echo "- alsa-utils"
        fi
        
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        print_info "Detected macOS system"
        
        if command_exists brew; then
            echo "Installing dependencies with Homebrew..."
            brew install portaudio
            print_success "macOS dependencies installed"
        else
            print_warning "Homebrew not found. Please install it first:"
            echo '/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"'
            echo "Then run: brew install portaudio"
        fi
        
    elif [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
        print_info "Detected Windows system - Python packages should work directly"
    else
        print_warning "Unknown system type: $OSTYPE"
        echo "You may need to install audio development libraries manually"
    fi
}

# Create virtual environment
setup_virtual_env() {
    print_header "Virtual Environment Setup"
    
    # Check if already in virtual environment
    if [[ -n "$VIRTUAL_ENV" ]] || [[ -n "$CONDA_DEFAULT_ENV" ]]; then
        print_success "Already in virtual environment: ${VIRTUAL_ENV:-$CONDA_DEFAULT_ENV}"
        return 0
    fi
    
    if ! ask_yes_no "Create virtual environment?"; then
        print_warning "Continuing without virtual environment"
        return 0
    fi
    
    # Choose environment type
    env_options=()
    if command_exists python3 || command_exists python; then
        env_options+=("Python venv (recommended)")
    fi
    if command_exists conda; then
        env_options+=("Anaconda/Miniconda")
    fi
    
    if [ ${#env_options[@]} -eq 0 ]; then
        print_error "No virtual environment tools found!"
        return 1
    fi
    
    get_choice "Choose virtual environment type:" "${env_options[@]}"
    local env_choice=$?
    
    read -p "Environment name (default: voice_transcription): " env_name
    env_name=${env_name:-voice_transcription}
    
    if [[ "${env_options[$env_choice]}" == *"venv"* ]]; then
        # Create Python venv
        print_info "Creating Python virtual environment: $env_name"
        
        if command_exists python3; then
            python3 -m venv "$env_name"
        else
            python -m venv "$env_name"
        fi
        
        # Activation instructions
        if [[ "$OSTYPE" == "cygwin" ]] || [[ "$OSTYPE" == "msys" ]]; then
            activate_cmd="$env_name/Scripts/activate"
        else
            activate_cmd="source $env_name/bin/activate"
        fi
        
        print_success "Virtual environment created!"
        print_info "To activate: $activate_cmd"
        
    else
        # Create Conda environment
        print_info "Creating Conda environment: $env_name"
        conda create -n "$env_name" python=3.9 -y
        
        print_success "Conda environment created!"
        print_info "To activate: conda activate $env_name"
    fi
}

# Install Python dependencies
install_python_deps() {
    print_header "Installing Python Dependencies"
    
    # Installation type options
    local install_options=(
        "🚀 Full Installation (Whisper + Google Speech + PyAudio)"
        "🎯 Local High-Quality (Whisper + PyAudio)" 
        "⚡ Online Fast (Google Speech + PyAudio)"
        "💡 Minimal Installation (Google Speech + system audio)"
    )
    
    get_choice "Select installation type:" "${install_options[@]}"
    local install_choice=$?
    
    # Determine pip command
    local pip_cmd="pip"
    if command_exists pip3; then
        pip_cmd="pip3"
    fi
    
    case $install_choice in
        0) # Full
            print_info "Installing full package set..."
            $pip_cmd install -r requirements-full.txt
            ;;
        1) # Whisper
            print_info "Installing Whisper package set..."
            $pip_cmd install -r requirements-base.txt
            $pip_cmd install -r requirements-audio.txt
            $pip_cmd install -r requirements-whisper.txt
            ;;
        2) # Google
            print_info "Installing Google Speech package set..."
            $pip_cmd install -r requirements-base.txt
            $pip_cmd install -r requirements-audio.txt  
            $pip_cmd install -r requirements-google.txt
            ;;
        3) # Minimal
            print_info "Installing minimal package set..."
            $pip_cmd install -r requirements-minimal.txt
            ;;
    esac
    
    print_success "Python dependencies installed"
}

# Test installation
test_installation() {
    print_header "Testing Installation"
    
    local python_cmd="python"
    if command_exists python3; then
        python_cmd="python3"
    fi
    
    echo "Testing imports..."
    
    # Test basic libraries
    if $python_cmd -c "import keyboard" 2>/dev/null; then
        print_success "Keyboard library"
    else
        print_error "Keyboard library missing"
    fi
    
    if $python_cmd -c "import pyperclip" 2>/dev/null; then
        print_success "Clipboard library"
    else
        print_error "Clipboard library missing"
    fi
    
    # Test audio
    if $python_cmd -c "import pyaudio" 2>/dev/null; then
        print_success "PyAudio"
    elif command_exists arecord; then
        print_success "Audio recording (arecord)"
    elif command_exists ffmpeg; then
        print_success "Audio recording (ffmpeg)"
    else
        print_warning "No audio recording method found"
    fi
    
    # Test speech recognition
    if $python_cmd -c "import whisper" 2>/dev/null; then
        print_success "Whisper speech recognition"
    else
        print_warning "Whisper not available"
    fi
    
    if $python_cmd -c "import speech_recognition" 2>/dev/null; then
        print_success "Google speech recognition"
    else
        print_warning "Google speech recognition not available"
    fi
}

# Show completion message
show_completion() {
    print_header "Setup Complete!"
    
    echo -e "${GREEN}🎉 Voice Transcription Tool is ready!${NC}\n"
    
    echo -e "${BLUE}Next steps:${NC}"
    echo "1. Run the application: python voice_transcription.py"
    echo "2. Test recording with the microphone button"
    echo "3. Enable global hotkeys (Ctrl+Shift+V)"
    echo "4. Configure speech engine in settings"
    echo ""
    echo -e "${CYAN}For detailed usage instructions, see setup.md${NC}"
    echo -e "${CYAN}🎤 Happy transcribing!${NC}"
}

# Main execution
main() {
    echo -e "${PURPLE}${BOLD}🎤 Voice Transcription Tool - Quick Setup${NC}"
    echo -e "${BLUE}This script will set up your complete environment${NC}\n"
    
    # Check Python version
    if ! command_exists python3 && ! command_exists python; then
        print_error "Python not found! Please install Python 3.7+"
        exit 1
    fi
    
    local python_cmd="python"
    if command_exists python3; then
        python_cmd="python3"
    fi
    
    local python_version=$($python_cmd -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    print_success "Python $python_version detected"
    
    # Check for requirements files
    if [ ! -f "requirements-base.txt" ]; then
        print_error "Requirements files not found! Please run this script in the project directory."
        exit 1
    fi
    
    # Main setup steps
    if ask_yes_no "Install system dependencies?"; then
        install_system_deps
    fi
    
    setup_virtual_env
    install_python_deps
    test_installation
    show_completion
}

# Run main function
main "$@"