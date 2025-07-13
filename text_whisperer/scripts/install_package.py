#!/usr/bin/env python3
"""
Desktop Package Installer for Voice Transcription Tool

This script creates a complete desktop application package with:
- Desktop entry file
- Application icon
- Launch scripts with proper permissions
- Menu integration
- Auto-start options
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def create_app_icon():
    """Create a simple SVG icon for the application."""
    icon_svg = """<?xml version="1.0" encoding="UTF-8"?>
<svg width="64" height="64" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <!-- Microphone body -->
  <rect x="26" y="16" width="12" height="20" rx="6" fill="#2563eb" stroke="#1d4ed8" stroke-width="2"/>
  
  <!-- Microphone grille -->
  <line x1="28" y1="20" x2="36" y2="20" stroke="#e5e7eb" stroke-width="1"/>
  <line x1="28" y1="24" x2="36" y2="24" stroke="#e5e7eb" stroke-width="1"/>
  <line x1="28" y1="28" x2="36" y2="28" stroke="#e5e7eb" stroke-width="1"/>
  <line x1="28" y1="32" x2="36" y2="32" stroke="#e5e7eb" stroke-width="1"/>
  
  <!-- Microphone stand -->
  <path d="M32 36 L32 44" stroke="#374151" stroke-width="3"/>
  <path d="M24 44 L40 44" stroke="#374151" stroke-width="3"/>
  
  <!-- Sound waves -->
  <path d="M44 24 Q48 28 48 32 Q48 36 44 40" stroke="#10b981" stroke-width="2" fill="none"/>
  <path d="M48 20 Q54 26 54 32 Q54 38 48 44" stroke="#10b981" stroke-width="2" fill="none"/>
  
  <!-- Recording indicator -->
  <circle cx="18" cy="18" r="4" fill="#ef4444"/>
  <circle cx="18" cy="18" r="2" fill="#fca5a5" opacity="0.8"/>
</svg>"""
    
    icon_path = Path("voice-transcription.svg")
    with open(icon_path, 'w') as f:
        f.write(icon_svg)
    
    return icon_path.absolute()

def create_desktop_entry(install_dir, icon_path):
    """Create desktop entry file."""
    desktop_content = f"""[Desktop Entry]
Name=Voice Transcription Tool
Comment=AI-powered voice transcription with wake word detection
Exec={install_dir}/launch-gui.sh
Icon={icon_path}
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Utility;
StartupNotify=true
Keywords=voice;transcription;speech;text;ai;whisper;
MimeType=audio/wav;audio/mp3;audio/ogg;
"""
    
    desktop_path = Path("voice-transcription.desktop")
    with open(desktop_path, 'w') as f:
        f.write(desktop_content)
    
    return desktop_path.absolute()

def create_launch_scripts(install_dir):
    """Create launch scripts with proper permissions."""
    
    # Main launch script (with sudo for hotkeys)
    launch_script = f"""#!/bin/bash
# Voice Transcription Tool Launcher
# This script launches the application with proper permissions

cd "{install_dir}"

# Check if running with sudo for hotkeys
if [ "$EUID" -eq 0 ]; then
    echo "Running with root privileges (hotkeys enabled)"
    python3 main.py "$@"
else
    echo "Running without root (hotkeys disabled - use GUI buttons)"
    python3 main.py "$@"
fi
"""
    
    # GUI launcher (with PolicyKit for password prompt)
    gui_launch_script = f"""#!/bin/bash
# Voice Transcription Tool GUI Launcher
# This script launches with a GUI password prompt for hotkeys

cd "{install_dir}"

# Try to get sudo with GUI prompt
if command -v pkexec >/dev/null 2>&1; then
    # Use PolicyKit for GUI password prompt
    pkexec env DISPLAY=$DISPLAY XAUTHORITY=$XAUTHORITY python3 "{install_dir}/main.py" "$@"
elif command -v gksudo >/dev/null 2>&1; then
    # Fallback to gksudo
    gksudo python3 "{install_dir}/main.py" "$@"
else
    # No GUI sudo available, run normally
    python3 "{install_dir}/main.py" "$@"
fi
"""
    
    # No-sudo launcher
    user_launch_script = f"""#!/bin/bash
# Voice Transcription Tool User Launcher
# This script launches without sudo (hotkeys disabled)

cd "{install_dir}"
python3 main.py "$@"
"""
    
    scripts = {
        "launch.sh": launch_script,
        "launch-gui.sh": gui_launch_script,
        "launch-user.sh": user_launch_script
    }
    
    script_paths = {}
    for name, content in scripts.items():
        script_path = Path(name)
        with open(script_path, 'w') as f:
            f.write(content)
        
        # Make executable
        os.chmod(script_path, 0o755)
        script_paths[name] = script_path.absolute()
    
    return script_paths

def install_desktop_package():
    """Install the complete desktop package."""
    print("🚀 Installing Voice Transcription Tool as Desktop Application")
    print("=" * 60)
    
    # Get current directory
    current_dir = Path.cwd()
    install_dir = current_dir
    
    print(f"📁 Installation directory: {install_dir}")
    
    # Create icon
    print("🎨 Creating application icon...")
    icon_path = create_app_icon()
    print(f"✅ Icon created: {icon_path}")
    
    # Create launch scripts
    print("📜 Creating launch scripts...")
    script_paths = create_launch_scripts(install_dir)
    for name, path in script_paths.items():
        print(f"✅ Created: {path}")
    
    # Create desktop entry
    print("🖥️ Creating desktop entry...")
    desktop_path = create_desktop_entry(install_dir, icon_path)
    print(f"✅ Desktop entry created: {desktop_path}")
    
    # Install desktop entry
    home_dir = Path.home()
    desktop_dir = home_dir / ".local" / "share" / "applications"
    desktop_dir.mkdir(parents=True, exist_ok=True)
    
    target_desktop = desktop_dir / "voice-transcription.desktop"
    shutil.copy2(desktop_path, target_desktop)
    os.chmod(target_desktop, 0o755)
    print(f"✅ Desktop entry installed: {target_desktop}")
    
    # Install icon
    icon_dir = home_dir / ".local" / "share" / "icons"
    icon_dir.mkdir(parents=True, exist_ok=True)
    
    target_icon = icon_dir / "voice-transcription.svg"
    shutil.copy2(icon_path, target_icon)
    print(f"✅ Icon installed: {target_icon}")
    
    # Update desktop database
    try:
        subprocess.run(["update-desktop-database", str(desktop_dir)], 
                      check=False, capture_output=True)
        print("✅ Desktop database updated")
    except:
        print("⚠️ Could not update desktop database (optional)")
    
    # Create symbolic links in PATH (optional)
    bin_dir = home_dir / ".local" / "bin"
    bin_dir.mkdir(parents=True, exist_ok=True)
    
    for script_name in ["launch.sh", "launch-gui.sh", "launch-user.sh"]:
        source = install_dir / script_name
        if script_name == "launch-gui.sh":
            target = bin_dir / "voice-transcription"
        else:
            target = bin_dir / f"voice-transcription-{script_name[:-3]}"
        
        try:
            if target.exists():
                target.unlink()
            target.symlink_to(source)
            print(f"✅ Command available: {target.name}")
        except Exception as e:
            print(f"⚠️ Could not create command link {target.name}: {e}")
    
    print("\n🎉 Installation Complete!")
    print("\nHow to use:")
    print("1. 🖱️  Launch from Applications menu: 'Voice Transcription Tool'")
    print("2. 💻 Command line:")
    print(f"   - voice-transcription (GUI with hotkeys)")
    print(f"   - voice-transcription-launch (terminal with hotkeys)")
    print(f"   - voice-transcription-user (no hotkeys needed)")
    print(f"3. 📂 Direct: {install_dir}/launch-gui.sh")
    
    print("\n📋 Features:")
    print("✅ Modern tabbed interface")
    print("✅ Speech recognition (Whisper, Google)")
    print("✅ Wake word detection")
    print("✅ Voice training")
    print("✅ Auto-paste to any application")
    print("✅ System tray support")
    print("✅ Global hotkeys (requires root/sudo)")
    
    return True

def uninstall_desktop_package():
    """Uninstall the desktop package."""
    print("🗑️ Uninstalling Voice Transcription Tool Desktop Package")
    print("=" * 60)
    
    home_dir = Path.home()
    
    # Remove desktop entry
    desktop_file = home_dir / ".local" / "share" / "applications" / "voice-transcription.desktop"
    if desktop_file.exists():
        desktop_file.unlink()
        print(f"✅ Removed: {desktop_file}")
    
    # Remove icon
    icon_file = home_dir / ".local" / "share" / "icons" / "voice-transcription.svg"
    if icon_file.exists():
        icon_file.unlink()
        print(f"✅ Removed: {icon_file}")
    
    # Remove command links
    bin_dir = home_dir / ".local" / "bin"
    for cmd in ["voice-transcription", "voice-transcription-launch", "voice-transcription-user"]:
        cmd_file = bin_dir / cmd
        if cmd_file.exists():
            cmd_file.unlink()
            print(f"✅ Removed: {cmd_file}")
    
    print("✅ Uninstallation complete!")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "uninstall":
        uninstall_desktop_package()
    else:
        install_desktop_package()