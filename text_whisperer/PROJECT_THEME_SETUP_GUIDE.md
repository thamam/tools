# 🎨 Project Theme Setup Guide

A powerful script to set up project-specific color themes for Cursor IDE that won't affect your global settings.

## 🚀 Quick Start

### Interactive Mode (Recommended for first-time users)
```bash
./setup_project_theme.sh
```
This will show you a beautiful menu with all available themes and descriptions.

### Direct Mode (Fast for experienced users)
```bash
./setup_project_theme.sh "One Dark Pro"
./setup_project_theme.sh "Dracula"
./setup_project_theme.sh "Solarized Dark"
```

## 📋 Available Themes

| Theme Name | Description |
|------------|-------------|
| **Default Dark Modern** | Modern dark theme with balanced colors |
| **Default Light Modern** | Modern light theme with clean appearance |
| **Dark+ (default dark)** | VS Code classic dark theme |
| **Light+ (default light)** | VS Code classic light theme |
| **One Dark Pro** | Popular Atom-inspired dark theme |
| **Dracula** | Dark theme with vibrant colors |
| **Monokai** | Classic dark theme with high contrast |
| **Solarized Dark** | Easy on eyes dark theme |
| **Solarized Light** | Easy on eyes light theme |
| **Abyss** | Very dark theme for focused coding |
| **Quiet Light** | Minimal light theme |
| **Nord** | Arctic-inspired blue theme |
| **Gruvbox Dark Hard** | Retro dark theme with warm colors |
| **Material Theme** | Google Material Design inspired |
| **Tomorrow Night Blue** | Blue-tinted dark theme |

## 🛠️ Installation Options

### Option 1: Copy to Individual Projects
```bash
# Copy the script to your project directory
cp setup_project_theme.sh /path/to/your/project/
cd /path/to/your/project/
chmod +x setup_project_theme.sh
./setup_project_theme.sh
```

### Option 2: Global Installation (Recommended)
```bash
# Make it available globally
sudo cp setup_project_theme.sh /usr/local/bin/setup-project-theme
sudo chmod +x /usr/local/bin/setup-project-theme

# Now you can use it from any project directory
cd /path/to/any/project/
setup-project-theme
```

### Option 3: Add to Your Dotfiles
```bash
# Add to your ~/.local/bin (make sure it's in your PATH)
mkdir -p ~/.local/bin
cp setup_project_theme.sh ~/.local/bin/setup-project-theme
chmod +x ~/.local/bin/setup-project-theme

# Add to PATH if not already there (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"
```

## 🎯 Usage Examples

### Example 1: New Python Project
```bash
mkdir my-python-project
cd my-python-project
setup-project-theme "One Dark Pro"
```

### Example 2: Web Development Project
```bash
mkdir my-web-app
cd my-web-app
setup-project-theme "Material Theme"
```

### Example 3: Data Science Project
```bash
mkdir data-analysis
cd data-analysis
setup-project-theme "Solarized Dark"
```

## ✨ What the Script Does

1. **Creates `.vscode/settings.json`** with project-specific theme settings
2. **Backs up existing settings** to `.vscode/settings.json.backup`
3. **Enhances your coding experience** with:
   - Custom syntax highlighting colors
   - Bracket colorization
   - Semantic highlighting
   - Enhanced editor guides
   - Improved terminal theming
   - Better file icons

## 🔧 Customization

After running the script, you can edit `.vscode/settings.json` to customize:

### Change Syntax Colors
```json
"editor.tokenColorCustomizations": {
  "comments": "#YOUR_COLOR",
  "strings": "#YOUR_COLOR",
  "keywords": "#YOUR_COLOR"
}
```

### Add Custom Themes
Edit the script and add your theme to the `themes` array:
```bash
["Your Custom Theme"]="Your theme description"
```

### Modify Editor Features
```json
"editor.fontSize": 14,
"editor.fontFamily": "Fira Code",
"editor.tabSize": 4
```

## 🔄 Switching Themes

To change themes in an existing project:
```bash
# Run the script again - it will backup your current settings
./setup_project_theme.sh "New Theme Name"
```

## 🗂️ File Structure

After running the script, your project will have:
```
your-project/
├── .vscode/
│   ├── settings.json           # New theme settings
│   └── settings.json.backup    # Backup of previous settings
└── other-project-files...
```

## 🚨 Important Notes

- **Project-specific only**: These settings only affect the current project
- **Global settings preserved**: Your global Cursor IDE settings remain unchanged
- **Backup created**: Original settings are backed up before changes
- **Reload required**: Restart Cursor IDE to see changes

## 🎨 Recommended Themes by Project Type

| Project Type | Recommended Theme |
|--------------|-------------------|
| **Python/AI/ML** | One Dark Pro, Dracula |
| **Web Development** | Material Theme, Default Dark Modern |
| **Data Science** | Solarized Dark, Nord |
| **Mobile Development** | Monokai, Gruvbox Dark Hard |
| **Documentation** | Quiet Light, Default Light Modern |
| **General Programming** | Dark+ (default dark), Abyss |

## 🔧 Troubleshooting

### Theme not applying?
1. Reload Cursor IDE: `Ctrl+Shift+P` → "Developer: Reload Window"
2. Check if `.vscode/settings.json` was created
3. Verify theme name is correct (case-sensitive)

### Want to undo changes?
1. Delete `.vscode/settings.json`
2. Rename `.vscode/settings.json.backup` to `.vscode/settings.json`
3. Or simply delete the entire `.vscode` directory

### Script not executable?
```bash
chmod +x setup_project_theme.sh
```

## 📝 Script Features

- ✅ Interactive theme selection with descriptions
- ✅ Command-line argument support
- ✅ Automatic backup of existing settings
- ✅ Colorful, user-friendly output
- ✅ Input validation and error handling
- ✅ Enhanced editor features included
- ✅ Works with any project directory
- ✅ Preserves global settings

## 🤝 Contributing

Want to add more themes? Edit the `themes` array in the script:
```bash
declare -A themes=(
    ["Your Theme Name"]="Your theme description"
    # ... existing themes
)
```

---

**Happy Coding! 🎉**

*This script makes it easy to have different themes for different projects while keeping your global IDE settings intact.* 