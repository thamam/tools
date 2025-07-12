#!/usr/bin/env python3
"""
Compare hotkey libraries to demonstrate the solution for Linux global hotkeys.

This script shows the difference between the keyboard library (requires sudo)
and pynput library (works without sudo) for global hotkeys on Linux.
"""

import sys
import time
import os


def test_keyboard_library():
    """Test the keyboard library that requires sudo."""
    print("="*60)
    print("TESTING KEYBOARD LIBRARY (Original - Requires Sudo)")
    print("="*60)
    
    try:
        import keyboard
        print("✅ keyboard library imported successfully")
        
        # Try to register a hotkey
        print("🔧 Attempting to register F9 hotkey...")
        
        def test_callback():
            print("F9 pressed!")
        
        keyboard.add_hotkey('f9', test_callback)
        print("✅ Hotkey registered! (This means you're running as root)")
        
        # Clean up
        keyboard.unhook_all_hotkeys()
        return True
        
    except ImportError:
        print("❌ keyboard library not installed")
        print("💡 Install with: pip install keyboard")
        return False
    except Exception as e:
        print(f"❌ keyboard library failed: {e}")
        if "root" in str(e).lower():
            print("💡 This is the expected error on Linux without sudo")
            print("💡 The keyboard library requires: sudo python3 script.py")
        return False


def test_pynput_library():
    """Test the pynput library that works without sudo."""
    print("\n" + "="*60)
    print("TESTING PYNPUT LIBRARY (Solution - No Sudo Required)")
    print("="*60)
    
    try:
        from pynput import keyboard
        print("✅ pynput library imported successfully")
        
        # Try to register a hotkey
        print("🔧 Attempting to register F9 hotkey...")
        
        def test_callback():
            print("F9 pressed!")
        
        hotkeys = keyboard.GlobalHotKeys({'<f9>': test_callback})
        print("✅ GlobalHotKeys object created successfully")
        
        # Try to start the listener
        print("🔧 Attempting to start hotkey listener...")
        hotkeys.start()
        print("✅ Hotkey listener started! (No sudo required)")
        
        # Clean up immediately
        hotkeys.stop()
        print("✅ Hotkey listener stopped")
        return True
        
    except ImportError:
        print("❌ pynput library not installed")
        print("💡 Install with: pip install pynput")
        return False
    except Exception as e:
        print(f"❌ pynput library failed: {e}")
        if "display" in str(e).lower():
            print("💡 pynput requires X11 display server")
            print("💡 Make sure DISPLAY environment variable is set")
        return False


def show_system_info():
    """Show relevant system information."""
    print("\n" + "="*60)
    print("SYSTEM INFORMATION")
    print("="*60)
    
    # Check display server
    display = os.environ.get('DISPLAY', '')
    wayland_display = os.environ.get('WAYLAND_DISPLAY', '')
    xdg_session_type = os.environ.get('XDG_SESSION_TYPE', '')
    
    if wayland_display or xdg_session_type == 'wayland':
        display_server = 'Wayland'
    elif display:
        display_server = 'X11'
    else:
        display_server = 'Unknown/Headless'
    
    print(f"Display server: {display_server}")
    print(f"DISPLAY: {display}")
    print(f"WAYLAND_DISPLAY: {wayland_display}")
    print(f"XDG_SESSION_TYPE: {xdg_session_type}")
    
    # Check user groups
    try:
        import subprocess
        result = subprocess.run(['groups'], capture_output=True, text=True)
        groups = result.stdout.strip().split()
        in_input_group = 'input' in groups
        print(f"User groups: {' '.join(groups)}")
        print(f"In 'input' group: {in_input_group}")
    except:
        print("Could not determine user groups")
    
    # Check if running as root
    is_root = os.geteuid() == 0
    print(f"Running as root: {is_root}")


def show_comparison_summary(keyboard_works, pynput_works):
    """Show a summary comparison of the two libraries."""
    print("\n" + "="*60)
    print("COMPARISON SUMMARY")
    print("="*60)
    
    print("\n📊 Test Results:")
    print(f"   keyboard library: {'✅ Working' if keyboard_works else '❌ Failed'}")
    print(f"   pynput library:   {'✅ Working' if pynput_works else '❌ Failed'}")
    
    print("\n📋 Feature Comparison:")
    print("   ┌─────────────────────┬─────────────┬──────────────┐")
    print("   │ Feature             │ keyboard    │ pynput       │")
    print("   ├─────────────────────┼─────────────┼──────────────┤")
    print("   │ Sudo required       │ ✅ Yes      │ ❌ No        │")
    print("   │ Cross-platform      │ ✅ Yes      │ ✅ Yes       │")
    print("   │ X11 compatibility   │ ❌ Bypasses │ ✅ Native    │")
    print("   │ Wayland support     │ ❌ Limited  │ ⚠️ Limited   │")
    print("   │ Raw device access   │ ✅ Yes      │ ❌ No        │")
    print("   │ User-space only     │ ❌ No       │ ✅ Yes       │")
    print("   │ Security concerns   │ ⚠️ High     │ ✅ Low       │")
    print("   └─────────────────────┴─────────────┴──────────────┘")
    
    print("\n💡 Recommendations:")
    if pynput_works:
        print("   🎯 Use pynput for your application")
        print("   ✅ No sudo required")
        print("   ✅ Better security model")
        print("   ✅ Works with standard Linux desktop environments")
    elif keyboard_works:
        print("   ⚠️  keyboard library works but requires sudo")
        print("   🔒 Consider security implications of running as root")
        print("   💡 Switch to pynput when possible")
    else:
        print("   ❌ Neither library is working")
        print("   🔧 Check system configuration and dependencies")
    
    print("\n🔗 Migration Path:")
    print("   1. Install pynput: pip install pynput")
    print("   2. Replace keyboard imports with pynput")
    print("   3. Update hotkey syntax (e.g., 'f9' → '<f9>')")
    print("   4. Test without sudo")


def main():
    """Run the comparison."""
    print("🔍 Linux Global Hotkey Library Comparison")
    print("🎯 Demonstrating the solution to 'must be root' error")
    
    # Show system info first
    show_system_info()
    
    # Test both libraries
    keyboard_works = test_keyboard_library()
    pynput_works = test_pynput_library()
    
    # Show comparison
    show_comparison_summary(keyboard_works, pynput_works)
    
    print(f"\n📖 For complete solution details, see: LINUX_HOTKEY_SOLUTION.md")
    print(f"🧪 For interactive testing, run: python3 utils/hotkeys_pynput.py --interactive")


if __name__ == "__main__":
    main()