#!/bin/bash
# setup-multi-git.sh - Enhanced setup script with repository conversion
# Usage: 
#   ./setup-multi-git.sh              # Run full setup
#   ./setup-multi-git.sh --convert    # Convert current repo
#   ./setup-multi-git.sh --convert --personal
#   ./setup-multi-git.sh --convert --work
#   ./setup-multi-git.sh --scan       # Scan all repos in current directory tree

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Helper functions
echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }
echo_prompt() { echo -e "${BLUE}[?]${NC} $1"; }

# Function to extract GitHub username from URL
extract_github_info() {
    local url=$1
    local regex='github\.com[:/]([^/]+)/([^/]+)(\.git)?$'
    
    if [[ $url =~ $regex ]]; then
        echo "${BASH_REMATCH[1]}/${BASH_REMATCH[2]}"
    else
        echo ""
    fi
}

# Function to detect account type based on gitconfig
detect_account_type() {
    local repo_path=$1
    local git_email=$(cd "$repo_path" && git config --get user.email 2>/dev/null || echo "")
    
    # Check if we have gitconfig files to compare against
    if [ -f ~/.gitconfig-personal ] && [ -f ~/.gitconfig-work ]; then
        local personal_email=$(grep -E "^\s*email\s*=" ~/.gitconfig-personal | sed 's/.*= *//')
        local work_email=$(grep -E "^\s*email\s*=" ~/.gitconfig-work | sed 's/.*= *//')
        
        if [ "$git_email" = "$personal_email" ]; then
            echo "personal"
        elif [ "$git_email" = "$work_email" ]; then
            echo "work"
        else
            echo "unknown"
        fi
    else
        echo "unknown"
    fi
}

# Function to convert repository remote
convert_repo() {
    local repo_path=${1:-.}
    local target_type=$2
    local remote_name=${3:-origin}
    
    cd "$repo_path"
    
    # Check if it's a git repository
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        echo_error "Not a git repository: $repo_path"
        return 1
    fi
    
    # Get current remote URL
    local current_url=$(git remote get-url "$remote_name" 2>/dev/null || echo "")
    if [ -z "$current_url" ]; then
        echo_error "Remote '$remote_name' not found"
        return 1
    fi
    
    echo_info "Current URL: $current_url"
    
    # Auto-detect if not specified
    if [ -z "$target_type" ]; then
        echo_prompt "Detecting account type based on git config..."
        target_type=$(detect_account_type "$repo_path")
        
        if [ "$target_type" = "unknown" ]; then
            echo "Select account type:"
            echo "1) Personal"
            echo "2) Work"
            read -p "Choice (1-2): " choice
            case $choice in
                1) target_type="personal" ;;
                2) target_type="work" ;;
                *) echo_error "Invalid choice"; return 1 ;;
            esac
        else
            echo_info "Detected as: $target_type"
            read -p "Is this correct? (y/n): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Select account type:"
                echo "1) Personal"
                echo "2) Work"
                read -p "Choice (1-2): " choice
                case $choice in
                    1) target_type="personal" ;;
                    2) target_type="work" ;;
                    *) echo_error "Invalid choice"; return 1 ;;
                esac
            fi
        fi
    fi
    
    # Extract GitHub info
    local github_info=$(extract_github_info "$current_url")
    if [ -z "$github_info" ]; then
        echo_error "Could not parse GitHub URL"
        return 1
    fi
    
    # Determine new URL based on preference
    echo "Select protocol:"
    echo "1) SSH (recommended)"
    echo "2) HTTPS"
    read -p "Choice (1-2): " protocol_choice
    
    case $protocol_choice in
        1)
            # Convert to SSH
            local new_url="git@github.com-${target_type}:${github_info}.git"
            ;;
        2)
            # Keep as HTTPS (will use token from context)
            local new_url="https://github.com/${github_info}.git"
            echo_warn "Note: HTTPS URLs depend on active context (use-personal/use-work)"
            ;;
        *)
            echo_error "Invalid choice"
            return 1
            ;;
    esac
    
    # Update the remote
    echo_info "Updating remote to: $new_url"
    git remote set-url "$remote_name" "$new_url"
    
    # Update local git config if needed
    if [ "$target_type" = "personal" ] && [ -f ~/.gitconfig-personal ]; then
        local name=$(grep -E "^\s*name\s*=" ~/.gitconfig-personal | sed 's/.*= *//')
        local email=$(grep -E "^\s*email\s*=" ~/.gitconfig-personal | sed 's/.*= *//')
        git config user.name "$name"
        git config user.email "$email"
        echo_info "Updated local git config for personal account"
    elif [ "$target_type" = "work" ] && [ -f ~/.gitconfig-work ]; then
        local name=$(grep -E "^\s*name\s*=" ~/.gitconfig-work | sed 's/.*= *//')
        local email=$(grep -E "^\s*email\s*=" ~/.gitconfig-work | sed 's/.*= *//')
        git config user.name "$name"
        git config user.email "$email"
        echo_info "Updated local git config for work account"
    fi
    
    echo_info "Repository converted successfully!"
    echo "New remote URL:"
    git remote -v | grep "$remote_name"
}

# Function to scan and list all git repositories
scan_repos() {
    local start_dir=${1:-.}
    echo_info "Scanning for git repositories in $start_dir..."
    
    local repos=()
    while IFS= read -r -d '' repo; do
        repos+=("$(dirname "$repo")")
    done < <(find "$start_dir" -name ".git" -type d -prune -print0 2>/dev/null)
    
    if [ ${#repos[@]} -eq 0 ]; then
        echo_warn "No git repositories found"
        return
    fi
    
    echo_info "Found ${#repos[@]} repositories:"
    echo
    
    for repo in "${repos[@]}"; do
        cd "$repo"
        local origin_url=$(git remote get-url origin 2>/dev/null || echo "No origin")
        local current_email=$(git config --get user.email 2>/dev/null || echo "Not set")
        local account_type=$(detect_account_type "$repo")
        
        echo "Repository: ${BLUE}$repo${NC}"
        echo "  Origin: $origin_url"
        echo "  Email: $current_email"
        echo "  Detected type: $account_type"
        echo
    done
    
    read -p "Do you want to convert any of these repositories? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        for repo in "${repos[@]}"; do
            echo
            echo "Repository: ${BLUE}$repo${NC}"
            read -p "Convert this repository? (y/n/q to quit): " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Qq]$ ]]; then
                break
            elif [[ $REPLY =~ ^[Yy]$ ]]; then
                convert_repo "$repo"
            fi
        done
    fi
}

# Main setup function
run_setup() {
    echo_info "Starting multi-account Git setup..."
    
    # 1. Collect user information
    echo
    echo "=== Personal Account Information ==="
    read -p "Personal GitHub username: " PERSONAL_GH_USERNAME
    read -p "Personal email: " PERSONAL_EMAIL
    read -p "Personal full name: " PERSONAL_NAME
    read -s -p "Personal GitHub token (hidden): " PERSONAL_GH_TOKEN
    echo
    read -p "Personal DockerHub username (leave empty if none): " PERSONAL_DH_USERNAME
    if [ -n "$PERSONAL_DH_USERNAME" ]; then
        read -s -p "Personal DockerHub token (hidden): " PERSONAL_DH_TOKEN
        echo
    fi
    
    echo
    echo "=== Work Account Information ==="
    read -p "Work GitHub username: " WORK_GH_USERNAME
    read -p "Work email: " WORK_EMAIL
    read -p "Work full name: " WORK_NAME
    read -s -p "Work GitHub token (hidden): " WORK_GH_TOKEN
    echo
    read -p "Work DockerHub username (leave empty if none): " WORK_DH_USERNAME
    if [ -n "$WORK_DH_USERNAME" ]; then
        read -s -p "Work DockerHub token (hidden): " WORK_DH_TOKEN
        echo
    fi
    
    # AWS credentials (optional)
    echo
    read -p "Do you have work AWS credentials to add? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "AWS Access Key ID: " WORK_AWS_KEY_ID
        read -s -p "AWS Secret Access Key (hidden): " WORK_AWS_SECRET
        echo
        read -p "AWS Default Region (e.g., us-east-2): " WORK_AWS_REGION
    fi
    
    # 2. Generate SSH keys
    echo
    echo_info "Generating SSH keys..."
    
    if [ ! -f ~/.ssh/id_ed25519_personal ]; then
        ssh-keygen -t ed25519 -C "$PERSONAL_EMAIL" -f ~/.ssh/id_ed25519_personal -N ""
        echo_info "Personal SSH key generated"
    else
        echo_warn "Personal SSH key already exists, skipping..."
    fi
    
    if [ ! -f ~/.ssh/id_ed25519_work ]; then
        ssh-keygen -t ed25519 -C "$WORK_EMAIL" -f ~/.ssh/id_ed25519_work -N ""
        echo_info "Work SSH key generated"
    else
        echo_warn "Work SSH key already exists, skipping..."
    fi
    
    # 3. Create SSH config
    echo
    echo_info "Setting up SSH config..."
    
    SSH_CONFIG="$HOME/.ssh/config"
    if [ -f "$SSH_CONFIG" ]; then
        echo_warn "SSH config exists. Backing up to $SSH_CONFIG.backup"
        cp "$SSH_CONFIG" "$SSH_CONFIG.backup"
    fi
    
    # Check if entries already exist
    if ! grep -q "Host github.com-personal" "$SSH_CONFIG" 2>/dev/null; then
        cat >> "$SSH_CONFIG" << EOF

# Personal GitHub account
Host github.com-personal
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_personal
    IdentitiesOnly yes
EOF
    fi
    
    if ! grep -q "Host github.com-work" "$SSH_CONFIG" 2>/dev/null; then
        cat >> "$SSH_CONFIG" << EOF

# Work GitHub account
Host github.com-work
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_work
    IdentitiesOnly yes
EOF
    fi
    
    chmod 600 "$SSH_CONFIG"
    
    # 4. Create environment files
    echo
    echo_info "Creating environment files..."
    
    # Personal environment
    cat > ~/.env-personal << EOF
# Personal GitHub and DockerHub credentials
export GH_TOKEN="$PERSONAL_GH_TOKEN"
export DOCKERHUB_USERNAME="$PERSONAL_DH_USERNAME"
export DOCKERHUB_TOKEN="$PERSONAL_DH_TOKEN"
export GIT_USER_NAME="$PERSONAL_NAME"
export GIT_USER_EMAIL="$PERSONAL_EMAIL"
export GIT_CREDENTIAL_USERNAME="$PERSONAL_GH_USERNAME"
EOF
    
    # Work environment
    cat > ~/.env-work << EOF
# Work GitHub and DockerHub credentials
export GH_TOKEN="$WORK_GH_TOKEN"
export DOCKERHUB_USERNAME="$WORK_DH_USERNAME"
export DOCKERHUB_TOKEN="$WORK_DH_TOKEN"
export GIT_USER_NAME="$WORK_NAME"
export GIT_USER_EMAIL="$WORK_EMAIL"
export GIT_CREDENTIAL_USERNAME="$WORK_GH_USERNAME"
EOF
    
    # Add AWS credentials if provided
    if [ -n "$WORK_AWS_KEY_ID" ]; then
        cat >> ~/.env-work << EOF
export AWS_ACCESS_KEY_ID="$WORK_AWS_KEY_ID"
export AWS_SECRET_ACCESS_KEY="$WORK_AWS_SECRET"
export AWS_DEFAULT_REGION="$WORK_AWS_REGION"
EOF
    fi
    
    # Add Imagry-specific environment variables
    cat >> ~/.env-work << EOF

# Imagry-specific environment variables
export SPACENET_HOME="/opt/imagry/spacenet"
export AI_CENTERNET_PATH="/opt/imagry/centernet"
export TRAFFIC_SIGNS_CLASSIFIER_PATH="/opt/imagry/tl_classifier"
EOF
    
    chmod 600 ~/.env-personal ~/.env-work
    
    # 5. Create git-credentials-wrapper.sh
    echo
    echo_info "Creating git credentials wrapper..."
    
    cat > ~/git-credentials-wrapper.sh << 'EOF'
#!/bin/bash
# This wrapper script handles credential selection based on context

# Check which context we're in
if [ "$GIT_CONTEXT" = "work" ]; then
    # For work context, check if Imagry's script exists and use it
    if [ -f "$HOME/git-credentials.sh" ]; then
        # Use Imagry's credential script
        exec "$HOME/git-credentials.sh" "$@"
    else
        # Fallback to work credentials store
        git credential-store --file=$HOME/.git-credentials-work "$@"
    fi
elif [ "$GIT_CONTEXT" = "personal" ]; then
    # Use personal credentials store
    git credential-store --file=$HOME/.git-credentials-personal "$@"
else
    # No context set - prompt user
    echo "Error: No Git context set. Use 'use-personal' or 'use-work' first." >&2
    exit 1
fi
EOF
    
    chmod +x ~/git-credentials-wrapper.sh
    
    # 6. Update .gitconfig
    echo
    echo_info "Updating Git configuration..."
    
    # Backup existing .gitconfig
    if [ -f ~/.gitconfig ]; then
        cp ~/.gitconfig ~/.gitconfig.backup
        echo_info "Backed up existing .gitconfig to .gitconfig.backup"
    fi
    
    # Remove existing user section from .gitconfig
    if [ -f ~/.gitconfig ]; then
        sed -i.tmp '/^\[user\]/,/^$/d' ~/.gitconfig
        rm -f ~/.gitconfig.tmp
    fi
    
    # Ensure includeIf sections exist
    if ! grep -q "includeIf.*gitdir:~/personal/" ~/.gitconfig 2>/dev/null; then
        cat >> ~/.gitconfig << 'EOF'

[includeIf "gitdir:~/personal/"]
    path = ~/.gitconfig-personal

[includeIf "gitdir:~/work/"]
    path = ~/.gitconfig-work
EOF
    fi
    
    # Create personal gitconfig
    cat > ~/.gitconfig-personal << EOF
[user]
    name = $PERSONAL_NAME
    email = $PERSONAL_EMAIL
EOF
    
    # Create work gitconfig
    cat > ~/.gitconfig-work << EOF
[user]
    name = $WORK_NAME
    email = $WORK_EMAIL
EOF
    
    # 7. Add functions to .bashrc
    echo
    echo_info "Adding context switching functions to .bashrc..."
    
    # Check if functions already exist
    if ! grep -q "use-personal()" ~/.bashrc 2>/dev/null; then
        cat >> ~/.bashrc << 'EOF'

# Git/GitHub Context Switching Functions
use-personal() {
    echo "Switching to personal Git/GitHub context..."
    
    # Load personal environment variables
    if [ -f ~/.env-personal ]; then
        source ~/.env-personal
    else
        echo "Warning: ~/.env-personal not found"
        return 1
    fi
    
    # Set git config for personal use
    git config --global user.name "$GIT_USER_NAME"
    git config --global user.email "$GIT_USER_EMAIL"
    git config --global credential.https://github.com.username "$GIT_CREDENTIAL_USERNAME"
    
    # Use the wrapper script for credential helper
    git config --global credential.helper "$HOME/git-credentials-wrapper.sh"
    
    # Create/update personal credentials file
    echo "https://$GIT_CREDENTIAL_USERNAME:$GH_TOKEN@github.com" > ~/.git-credentials-personal
    chmod 600 ~/.git-credentials-personal
    
    # Export a marker variable
    export GIT_CONTEXT="personal"
    
    echo "Switched to personal context:"
    echo "  Git User: $GIT_USER_NAME <$GIT_USER_EMAIL>"
    echo "  GitHub User: $GIT_CREDENTIAL_USERNAME"
    [ -n "$DOCKERHUB_USERNAME" ] && echo "  DockerHub User: $DOCKERHUB_USERNAME"
}

use-work() {
    echo "Switching to work Git/GitHub context..."
    
    # Load work environment variables
    if [ -f ~/.env-work ]; then
        source ~/.env-work
    else
        echo "Warning: ~/.env-work not found"
        return 1
    fi
    
    # Set git config for work use
    git config --global user.name "$GIT_USER_NAME"
    git config --global user.email "$GIT_USER_EMAIL"
    git config --global credential.https://github.com.username "$GIT_CREDENTIAL_USERNAME"
    
    # Use the wrapper script for credential helper
    git config --global credential.helper "$HOME/git-credentials-wrapper.sh"
    
    # Create/update work credentials file
    echo "https://$GIT_CREDENTIAL_USERNAME:$GH_TOKEN@github.com" > ~/.git-credentials-work
    chmod 600 ~/.git-credentials-work
    
    # Export a marker variable
    export GIT_CONTEXT="work"
    
    # Check if Imagry's git-credentials.sh exists
    if [ -f "$HOME/git-credentials.sh" ]; then
        echo "  Using Imagry's git-credentials.sh"
    fi
    
    echo "Switched to work context:"
    echo "  Git User: $GIT_USER_NAME <$GIT_USER_EMAIL>"
    echo "  GitHub User: $GIT_CREDENTIAL_USERNAME"
    [ -n "$DOCKERHUB_USERNAME" ] && echo "  DockerHub User: $DOCKERHUB_USERNAME"
    [ -n "$AWS_ACCESS_KEY_ID" ] && echo "  AWS Account: Configured"
}

git-context() {
    if [ -z "$GIT_CONTEXT" ]; then
        echo "No Git context set. Use 'use-personal' or 'use-work' to set context."
    else
        echo "Current Git context: $GIT_CONTEXT"
        echo "  Git User: $(git config --global user.name) <$(git config --global user.email)>"
        echo "  GitHub User: $(git config --global credential.https://github.com.username)"
        echo "  Credential Helper: $(git config --global credential.helper)"
        [ -n "$DOCKERHUB_USERNAME" ] && echo "  DockerHub User: $DOCKERHUB_USERNAME"
        [ -n "$AWS_ACCESS_KEY_ID" ] && echo "  AWS: Configured"
    fi
}

# Auto-start SSH agent (if not already running)
if [ -z "$SSH_AUTH_SOCK" ]; then
    eval "$(ssh-agent -s)" >/dev/null 2>&1
    ssh-add ~/.ssh/id_ed25519_personal 2>/dev/null
    ssh-add ~/.ssh/id_ed25519_work 2>/dev/null
fi
EOF
        echo_info "Functions added to .bashrc"
    else
        echo_warn "Context switching functions already exist in .bashrc, skipping..."
    fi
    
    # 8. Set up global gitignore
    echo
    echo_info "Setting up global gitignore..."
    
    cat >> ~/.gitignore_global << 'EOF'
.env-personal
.env-work
.git-credentials-*
EOF
    
    git config --global core.excludesfile ~/.gitignore_global
    
    # 9. Set up Imagry symlink
    echo
    read -p "Do you want to set up the /opt/imagry symlink for Imagry repos? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        IMAGRY_DIR="$HOME/work/opt/imagry"
        echo_info "Creating directory structure at $IMAGRY_DIR"
        mkdir -p "$IMAGRY_DIR"
        
        # Remove existing symlink if it exists
        if [ -L /opt/imagry ]; then
            echo_warn "Removing existing /opt/imagry symlink"
            sudo rm /opt/imagry
        fi
        
        # Create new symlink
        sudo ln -s "$IMAGRY_DIR" /opt/imagry
        echo_info "Created symlink: /opt/imagry -> $IMAGRY_DIR"
        
        # Create required directories
        sudo mkdir -p /opt/imagry/core_dumps/
        echo_info "Created /opt/imagry/core_dumps/ directory"
    fi
    
    # 10. Display SSH public keys
    echo
    echo_info "Setup complete! Here are your SSH public keys to add to GitHub:"
    echo
    echo "=== PERSONAL SSH PUBLIC KEY ==="
    echo "Add this to your personal GitHub account:"
    cat ~/.ssh/id_ed25519_personal.pub
    echo
    echo "=== WORK SSH PUBLIC KEY ==="
    echo "Add this to your work GitHub account:"
    cat ~/.ssh/id_ed25519_work.pub
    echo
    
    # 11. Final instructions
    echo_info "Final steps:"
    echo "1. Add the SSH keys above to your respective GitHub accounts"
    echo "2. Run: source ~/.bashrc"
    echo "3. Test with: use-personal or use-work"
    echo "4. Clone repositories:"
    echo "   Personal SSH: git clone git@github.com-personal:username/repo.git"
    echo "   Work SSH: git clone git@github.com-work:organization/repo.git"
    echo "   HTTPS: git clone https://github.com/username/repo.git (depends on active context)"
    echo
    echo_info "To convert existing repositories, run: $0 --convert"
    echo_info "To scan all repositories, run: $0 --scan"
    echo
    echo_info "Setup script completed successfully!"
}

# Parse command line arguments
case "${1:-setup}" in
    --convert)
        if [ "$2" = "--personal" ]; then
            convert_repo "." "personal"
        elif [ "$2" = "--work" ]; then
            convert_repo "." "work"
        else
            convert_repo "."
        fi
        ;;
    --scan)
        scan_repos "${2:-.}"
        ;;
    --help|-h)
        echo "Usage: $0 [OPTIONS]"
        echo "Options:"
        echo "  (no args)           Run full setup"
        echo "  --convert           Convert current repository"
        echo "  --convert --personal  Convert to personal account"
        echo "  --convert --work    Convert to work account"
        echo "  --scan [DIR]        Scan directory for git repos (default: current)"
        echo "  --help              Show this help"
        ;;
    *)
        run_setup
        ;;
esac