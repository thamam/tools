#!/bin/bash
#
# BMAD Dashboard Installation Script
# Installs the complete BMAD dashboard system
#

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${BLUE}🚀 BMAD Dashboard Installation${NC}"
echo ""
echo "Installing from: $SCRIPT_DIR"
echo ""

# Create directory structure
echo -e "${YELLOW}📁 Creating directory structure...${NC}"
mkdir -p ~/.config/claude-code/tools
mkdir -p ~/.config/claude-code/apps
mkdir -p ~/.config/claude-code/hooks
mkdir -p ~/.claude/commands

# Copy tools
echo -e "${YELLOW}🔧 Installing state reader tool...${NC}"
cp "$SCRIPT_DIR/tools/bmad-state-reader.py" ~/.config/claude-code/tools/
chmod +x ~/.config/claude-code/tools/bmad-state-reader.py

# Copy apps
echo -e "${YELLOW}📊 Installing dashboard application...${NC}"
cp "$SCRIPT_DIR/apps/bmad-dashboard.py" ~/.config/claude-code/apps/
chmod +x ~/.config/claude-code/apps/bmad-dashboard.py

echo -e "${YELLOW}🚀 Installing launcher script...${NC}"
cp "$SCRIPT_DIR/apps/launch-dashboard.sh" ~/.config/claude-code/apps/
chmod +x ~/.config/claude-code/apps/launch-dashboard.sh

# Copy hooks
echo -e "${YELLOW}🪝 Installing auto-refresh hook...${NC}"
cp "$SCRIPT_DIR/hooks/tool-result.sh" ~/.config/claude-code/hooks/
chmod +x ~/.config/claude-code/hooks/tool-result.sh

# Copy commands
echo -e "${YELLOW}⌨️  Installing dashboard command...${NC}"
cp "$SCRIPT_DIR/commands/bmad-dashboard.md" ~/.claude/commands/

# Copy documentation
if [ -f "$SCRIPT_DIR/README.md" ]; then
    echo -e "${YELLOW}📚 Installing documentation...${NC}"
    cp "$SCRIPT_DIR/README.md" ~/.config/claude-code/BMAD-DASHBOARD-README.md
fi

echo ""
echo -e "${GREEN}✅ Installation complete!${NC}"
echo ""
echo -e "${BLUE}📍 Files installed:${NC}"
echo "   • ~/.config/claude-code/tools/bmad-state-reader.py"
echo "   • ~/.config/claude-code/apps/bmad-dashboard.py"
echo "   • ~/.config/claude-code/apps/launch-dashboard.sh"
echo "   • ~/.config/claude-code/hooks/tool-result.sh"
echo "   • ~/.claude/commands/bmad-dashboard.md"
echo "   • ~/.config/claude-code/BMAD-DASHBOARD-README.md"
echo ""

# Check dependencies
echo -e "${BLUE}🔍 Checking dependencies...${NC}"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "   ${GREEN}✅${NC} Python: $PYTHON_VERSION"
else
    echo -e "   ${RED}❌${NC} Python 3 not found"
    echo ""
    echo -e "${RED}Please install Python 3.8 or higher${NC}"
    exit 1
fi

# Check rich library
if python3 -c "from rich.console import Console" 2>/dev/null; then
    echo -e "   ${GREEN}✅${NC} Rich library: installed"
else
    echo -e "   ${YELLOW}⚠️${NC}  Rich library: NOT installed"
    echo ""
    echo -e "${YELLOW}📦 Installing rich library...${NC}"

    # Check if pip is installed
    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        echo -e "   ${RED}❌${NC} pip not found. Please install pip."
        echo "   For example, you can use: sudo apt-get install python3-pip"
        echo "   Or on other systems: sudo yum install python3-pip"
        exit 1
    fi

    if pip install rich 2>/dev/null || pip3 install rich 2>/dev/null || pip install --user rich 2>/dev/null; then
        echo -e "   ${GREEN}✅${NC} Rich library installed successfully"
    else
        echo -e "   ${RED}❌${NC} Failed to install rich library"
        echo ""
        echo "Please install manually:"
        echo "  pip install rich"
        echo "  # or"
        echo "  pip3 install rich"
        echo "  # or"
        echo "  pip install --user rich"
        exit 1
    fi
fi

echo ""
echo -e "${GREEN}🎉 BMAD Dashboard is ready to use!${NC}"
echo ""
echo -e "${BLUE}📖 Quick Start:${NC}"
echo "   1. Navigate to a BMAD project"
echo "   2. Run: ~/.config/claude-code/apps/bmad-dashboard.py"
echo "   3. Or use: /bmad-dashboard command in Claude Code"
echo ""
echo -e "${BLUE}📄 Documentation:${NC}"
echo "   • Full guide: ~/.config/claude-code/BMAD-DASHBOARD-README.md"
echo "   • Or read: $SCRIPT_DIR/README.md"
echo ""
echo -e "${BLUE}🧪 Test the installation:${NC}"
echo "   cd /path/to/bmad/project"
echo "   ~/.config/claude-code/apps/bmad-dashboard.py --summary"
echo ""
