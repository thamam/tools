#!/bin/bash
# Cursor Chat History Cleanup Script
# Removes accumulated chat history that causes Cursor 1.2.x freezing issues

set -e  # Exit on any error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Cursor Chat History Cleanup Script ===${NC}"
echo

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to format file sizes
format_size() {
    local size=$1
    if [ $size -gt 1073741824 ]; then
        echo "$(($size / 1073741824))GB"
    elif [ $size -gt 1048576 ]; then
        echo "$(($size / 1048576))MB"
    elif [ $size -gt 1024 ]; then
        echo "$(($size / 1024))KB"
    else
        echo "${size}B"
    fi
}

# Check if Cursor config directory exists
CURSOR_CONFIG="$HOME/.config/Cursor"
if [ ! -d "$CURSOR_CONFIG" ]; then
    print_error "Cursor configuration directory not found at $CURSOR_CONFIG"
    echo "Have you run Cursor at least once?"
    exit 1
fi

# Check if Cursor is currently running
if pgrep -f "cursor.*--no-sandbox" > /dev/null || pgrep -f "cursor" > /dev/null; then
    print_error "Cursor is currently running. Please close it before running this cleanup."
    echo "Use: pkill -f cursor"
    exit 1
fi

# Show current sizes
echo -e "${YELLOW}Current Cursor configuration sizes:${NC}"
cursor_size=$(du -sb "$CURSOR_CONFIG" 2>/dev/null | cut -f1 || echo 0)
workspace_size=$(du -sb "$CURSOR_CONFIG/User/workspaceStorage" 2>/dev/null | cut -f1 || echo 0)
logs_size=$(du -sb "$CURSOR_CONFIG/logs" 2>/dev/null | cut -f1 || echo 0)

echo "  Total Cursor config: $(format_size $cursor_size)"
echo "  Workspace storage:   $(format_size $workspace_size)"
echo "  Logs:               $(format_size $logs_size)"
echo

# Show workspace storage breakdown
if [ -d "$CURSOR_CONFIG/User/workspaceStorage" ] && [ "$(ls -A "$CURSOR_CONFIG/User/workspaceStorage" 2>/dev/null)" ]; then
    print_status "Top 10 largest workspace directories:"
    du -sh "$CURSOR_CONFIG/User/workspaceStorage"/*/ 2>/dev/null | sort -hr | head -10 | while read size dir; do
        echo "  $size - $(basename "$dir")"
    done
    echo
fi

# Warning about what will be removed
echo -e "${YELLOW}This script will remove:${NC}"
echo "  ✗ All chat history and AI conversations"
echo "  ✗ Workspace-specific settings and cache"
echo "  ✗ Old log files (older than 7 days)"
echo
echo -e "${GREEN}This script will preserve:${NC}"
echo "  ✓ User settings and preferences"
echo "  ✓ Installed extensions"
echo "  ✓ Keybindings and themes"
echo "  ✓ Recent log files (last 7 days)"
echo

# Confirmation prompt
read -p "Do you want to proceed with the cleanup? (y/N): " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cleanup cancelled."
    exit 0
fi

# Create backup
BACKUP_DIR="$CURSOR_CONFIG/../Cursor_backup_$(date +%Y%m%d_%H%M%S)"
print_status "Creating backup at $BACKUP_DIR..."
cp -r "$CURSOR_CONFIG" "$BACKUP_DIR"
backup_size=$(du -sb "$BACKUP_DIR" 2>/dev/null | cut -f1 || echo 0)
print_status "Backup created: $(format_size $backup_size)"

# Track space saved
space_saved=0

# Clean workspace storage
if [ -d "$CURSOR_CONFIG/User/workspaceStorage" ]; then
    print_status "Removing workspace storage (chat history)..."
    workspace_before=$(du -sb "$CURSOR_CONFIG/User/workspaceStorage" 2>/dev/null | cut -f1 || echo 0)
    rm -rf "$CURSOR_CONFIG/User/workspaceStorage"/*
    workspace_after=$(du -sb "$CURSOR_CONFIG/User/workspaceStorage" 2>/dev/null | cut -f1 || echo 0)
    workspace_saved=$((workspace_before - workspace_after))
    space_saved=$((space_saved + workspace_saved))
    print_status "Workspace storage cleared: $(format_size $workspace_saved) freed"
fi

# Clean workspace storage backups
if [ -d "$CURSOR_CONFIG/User" ]; then
    workspace_backups=$(find "$CURSOR_CONFIG/User" -name "workspaceStorage_backup_*" -type d 2>/dev/null)
    if [ -n "$workspace_backups" ]; then
        print_status "Removing workspace storage backups..."
        backup_before=0
        echo "$workspace_backups" | while read backup_dir; do
            if [ -d "$backup_dir" ]; then
                backup_size=$(du -sb "$backup_dir" 2>/dev/null | cut -f1 || echo 0)
                backup_before=$((backup_before + backup_size))
                rm -rf "$backup_dir"
            fi
        done
        print_status "Workspace backups removed"
    fi
fi

# Clean old logs (keep last 7 days)
if [ -d "$CURSOR_CONFIG/logs" ]; then
    print_status "Cleaning old log files (older than 7 days)..."
    logs_before=$(du -sb "$CURSOR_CONFIG/logs" 2>/dev/null | cut -f1 || echo 0)
    find "$CURSOR_CONFIG/logs" -type d -mtime +7 -exec rm -rf {} + 2>/dev/null || true
    logs_after=$(du -sb "$CURSOR_CONFIG/logs" 2>/dev/null | cut -f1 || echo 0)
    logs_saved=$((logs_before - logs_after))
    space_saved=$((space_saved + logs_saved))
    if [ $logs_saved -gt 0 ]; then
        print_status "Old logs removed: $(format_size $logs_saved) freed"
    else
        print_status "No old logs to remove"
    fi
fi

# Clean any orphaned extension host logs
if [ -d "$CURSOR_CONFIG/logs" ]; then
    find "$CURSOR_CONFIG/logs" -name "exthost" -type d -exec find {} -name "*.log" -size +10M -delete \; 2>/dev/null || true
fi

# Show results
echo
cursor_size_after=$(du -sb "$CURSOR_CONFIG" 2>/dev/null | cut -f1 || echo 0)
total_saved=$((cursor_size - cursor_size_after))

echo -e "${GREEN}=== Cleanup Complete! ===${NC}"
print_status "Total space freed: $(format_size $total_saved)"
print_status "Cursor config size: $(format_size $cursor_size_after) (was $(format_size $cursor_size))"
print_status "Backup location: $BACKUP_DIR"

echo
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Launch Cursor to test if freezing issues are resolved"
echo "2. If everything works well, you can remove the backup:"
echo "   rm -rf \"$BACKUP_DIR\""
echo "3. If issues persist, restore from backup:"
echo "   rm -rf \"$CURSOR_CONFIG\" && mv \"$BACKUP_DIR\" \"$CURSOR_CONFIG\""

echo
print_status "Cleanup completed successfully!"
echo "You can now launch Cursor. It should be much faster and stable."