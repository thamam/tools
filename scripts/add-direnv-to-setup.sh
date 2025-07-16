#!/bin/bash
# add-direnv.sh - Add direnv auto-switching to existing multi-git setup

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_prompt() { echo -e "${BLUE}[?]${NC} $1"; }

echo_info "Adding direnv to your existing multi-git setup..."

# Check if direnv is installed
if ! command -v direnv &> /dev/null; then
    echo_warn "direnv is not installed"
    echo_prompt "Would you like to install it? (y/n)"
    read -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew install direnv
        else
            sudo apt-get update && sudo apt-get install -y direnv
        fi
    else
        echo_error "direnv is required. Please install it manually."
        exit 1
    fi
fi

# Add direnv hook to bashrc if not already there
if ! grep -q "direnv hook bash" ~/.bashrc; then
    echo_info "Adding direnv hook to .bashrc..."
    echo 'eval "$(direnv hook bash)"' >> ~/.bashrc
fi

# Create .envrc files
echo_info "Creating .envrc files..."

# Personal .envrc
cat > ~/personal/.envrc << 'EOF'
# Auto-switch to personal context when entering personal directory
echo "[direnv] Switching to personal context..."

# Check if our bash functions exist
if type use-personal &>/dev/null; then
    # Use our existing function (this will load all credentials)
    use-personal true  # true for quiet mode
else
    # Fallback: Load credentials directly
    if [ -f ~/.env-personal ]; then
        set -a  # automatically export all variables
        source ~/.env-personal
        set +a
        
        # Set git config
        git config --global user.name "$GIT_USER_NAME"
        git config --global user.email "$GIT_USER_EMAIL"
        git config --global credential.https://github.com.username "$GIT_CREDENTIAL_USERNAME"
        export GIT_CONTEXT="personal"
    fi
fi

# Optional: Project-specific overrides can go here
# export PROJECT_SPECIFIC_VAR="value"
EOF

# Work .envrc
cat > ~/work/.envrc << 'EOF'
# Auto-switch to work context when entering work directory
echo "[direnv] Switching to work context..."

# Check if our bash functions exist
if type use-work &>/dev/null; then
    # Use our existing function (this will load all credentials)
    use-work true  # true for quiet mode
else
    # Fallback: Load credentials directly
    if [ -f ~/.env-work ]; then
        set -a  # automatically export all variables
        source ~/.env-work
        set +a
        
        # Set git config
        git config --global user.name "$GIT_USER_NAME"
        git config --global user.email "$GIT_USER_EMAIL"
        git config --global credential.https://github.com.username "$GIT_CREDENTIAL_USERNAME"
        export GIT_CONTEXT="work"
    fi
fi

# Work-specific additions (Imagry paths are already in .env-work)
# export ADDITIONAL_WORK_VAR="value"
EOF

# Create directories if they don't exist
mkdir -p ~/personal ~/work

# Allow direnv in these directories
echo_info "Allowing direnv in personal and work directories..."
cd ~/personal && direnv allow
cd ~/work && direnv allow

# Optional: Remove auto-switching from bashrc to avoid conflicts
echo_prompt "Remove bash auto-switching to use direnv exclusively? (y/n)"
read -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo_info "Removing bash auto-switching..."
    # Create backup
    cp ~/.bashrc ~/.bashrc.backup.$(date +%Y%m%d_%H%M%S)
    
    # Remove auto-switch function and its calls
    sed -i '/auto-switch-git-context/d' ~/.bashrc
    sed -i '/^cd() {/,/^}/d' ~/.bashrc
    
    echo_info "Bash auto-switching removed (backup created)"
fi

# Create example project-specific .envrc
echo_info "Creating example project .envrc..."
mkdir -p ~/work/example-project
cat > ~/work/example-project/.envrc << 'EOF'
# Inherit all work environment settings
source_up

# Project-specific overrides
export NODE_ENV=development
export DATABASE_URL="postgresql://localhost/myproject"

# Optional: Use specific tool versions
# use node 16.14.0
# layout python3
EOF

echo
echo_info "direnv setup complete!"
echo
echo "Next steps:"
echo "1. Restart your shell or run: source ~/.bashrc"
echo "2. Test by entering directories:"
echo "   cd ~/personal  # Should show [direnv] message"
echo "   cd ~/work      # Should show [direnv] message"
echo
echo "To add project-specific configs:"
echo "1. Create .envrc in any project directory"
echo "2. Run 'direnv allow' in that directory"
echo
echo_info "Your existing credentials and SSH keys remain unchanged!"