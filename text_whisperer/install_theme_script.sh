#!/bin/bash

# Installation script for Project Theme Setup
# This script helps you install the theme setup script globally

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Function to display header
show_header() {
    echo -e "${PURPLE}╔══════════════════════════════════════════╗${NC}"
    echo -e "${PURPLE}║     Project Theme Script Installer      ║${NC}"
    echo -e "${PURPLE}║    Make it available globally on your   ║${NC}"
    echo -e "${PURPLE}║              system                      ║${NC}"
    echo -e "${PURPLE}╚══════════════════════════════════════════╝${NC}"
    echo
}

# Function to check if script exists
check_script_exists() {
    if [ ! -f "setup_project_theme.sh" ]; then
        echo -e "${RED}Error: setup_project_theme.sh not found in current directory${NC}"
        echo -e "${YELLOW}Please make sure you're running this from the directory containing setup_project_theme.sh${NC}"
        exit 1
    fi
}

# Function to show installation options
show_installation_options() {
    echo -e "${YELLOW}Choose installation method:${NC}"
    echo -e "${BLUE}1.${NC} ${GREEN}Global installation${NC} (requires sudo, installs to /usr/local/bin)"
    echo -e "${BLUE}2.${NC} ${GREEN}User installation${NC} (installs to ~/.local/bin)"
    echo -e "${BLUE}3.${NC} ${GREEN}Custom location${NC} (specify your own path)"
    echo -e "${BLUE}4.${NC} ${GREEN}Show current script location${NC} (just display info)"
    echo
}

# Function to get user choice
get_user_choice() {
    read -p "Enter your choice (1-4): " choice
    case $choice in
        1) install_global ;;
        2) install_user ;;
        3) install_custom ;;
        4) show_info ;;
        *) 
            echo -e "${RED}Invalid choice. Please enter 1, 2, 3, or 4.${NC}"
            return 1
            ;;
    esac
}

# Function to install globally
install_global() {
    echo -e "${BLUE}Installing globally to /usr/local/bin...${NC}"
    
    if sudo cp setup_project_theme.sh /usr/local/bin/setup-project-theme; then
        sudo chmod +x /usr/local/bin/setup-project-theme
        echo -e "${GREEN}✅ Successfully installed globally!${NC}"
        echo -e "${YELLOW}You can now run:${NC} ${GREEN}setup-project-theme${NC} ${YELLOW}from any directory${NC}"
        test_installation "/usr/local/bin/setup-project-theme"
    else
        echo -e "${RED}❌ Failed to install globally. Make sure you have sudo privileges.${NC}"
    fi
}

# Function to install for user
install_user() {
    echo -e "${BLUE}Installing to ~/.local/bin...${NC}"
    
    # Create directory if it doesn't exist
    mkdir -p ~/.local/bin
    
    if cp setup_project_theme.sh ~/.local/bin/setup-project-theme; then
        chmod +x ~/.local/bin/setup-project-theme
        echo -e "${GREEN}✅ Successfully installed for user!${NC}"
        
        # Check if ~/.local/bin is in PATH
        if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
            echo -e "${YELLOW}⚠️  ~/.local/bin is not in your PATH${NC}"
            echo -e "${YELLOW}Add this to your ~/.bashrc or ~/.zshrc:${NC}"
            echo -e "${GREEN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
        else
            echo -e "${YELLOW}You can now run:${NC} ${GREEN}setup-project-theme${NC} ${YELLOW}from any directory${NC}"
        fi
        
        test_installation "$HOME/.local/bin/setup-project-theme"
    else
        echo -e "${RED}❌ Failed to install for user.${NC}"
    fi
}

# Function to install to custom location
install_custom() {
    echo -e "${BLUE}Enter the full path where you want to install the script:${NC}"
    read -p "Path: " custom_path
    
    if [ -d "$custom_path" ]; then
        target_file="$custom_path/setup-project-theme"
        if cp setup_project_theme.sh "$target_file"; then
            chmod +x "$target_file"
            echo -e "${GREEN}✅ Successfully installed to $target_file${NC}"
            echo -e "${YELLOW}You can now run:${NC} ${GREEN}$target_file${NC}"
            test_installation "$target_file"
        else
            echo -e "${RED}❌ Failed to install to $custom_path${NC}"
        fi
    else
        echo -e "${RED}❌ Directory $custom_path does not exist${NC}"
    fi
}

# Function to show current script info
show_info() {
    echo -e "${BLUE}Current script location:${NC} ${GREEN}$(pwd)/setup_project_theme.sh${NC}"
    echo -e "${BLUE}Script is executable:${NC} ${GREEN}$(test -x setup_project_theme.sh && echo "Yes" || echo "No")${NC}"
    echo -e "${BLUE}You can run it directly:${NC} ${GREEN}./setup_project_theme.sh${NC}"
    echo
    echo -e "${YELLOW}To use it from any directory, choose one of the installation options above.${NC}"
}

# Function to test installation
test_installation() {
    local installed_path="$1"
    echo
    echo -e "${BLUE}Testing installation...${NC}"
    
    if [ -f "$installed_path" ] && [ -x "$installed_path" ]; then
        echo -e "${GREEN}✅ Script is installed and executable${NC}"
        echo -e "${BLUE}Test command:${NC} ${GREEN}$(basename "$installed_path") --help${NC}"
    else
        echo -e "${RED}❌ Installation test failed${NC}"
    fi
}

# Function to show completion message
show_completion_message() {
    echo
    echo -e "${GREEN}╔══════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║         Installation Complete!          ║${NC}"
    echo -e "${GREEN}╚══════════════════════════════════════════╝${NC}"
    echo
    echo -e "${YELLOW}Next steps:${NC}"
    echo -e "1. ${CYAN}Navigate to any project directory${NC}"
    echo -e "2. ${CYAN}Run: ${GREEN}setup-project-theme${NC}"
    echo -e "3. ${CYAN}Choose your preferred theme${NC}"
    echo -e "4. ${CYAN}Reload Cursor IDE to see changes${NC}"
    echo
    echo -e "${PURPLE}Happy coding with your new project-specific themes! 🎉${NC}"
}

# Main script logic
main() {
    show_header
    check_script_exists
    
    while true; do
        show_installation_options
        if get_user_choice; then
            break
        fi
        echo
    done
    
    show_completion_message
}

# Run main function
main "$@" 