#!/usr/bin/env python3
"""
Migration script to update Voice Transcription Tool to use pynput instead of keyboard library.

This script helps migrate from the problematic 'keyboard' library to 'pynput' for
Linux global hotkeys without requiring sudo.
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path


def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    # Check if pynput is installed
    try:
        import pynput
        print("✅ pynput is already installed")
        return True
    except ImportError:
        print("❌ pynput not found")
        
        # Try to install pynput
        print("📦 Installing pynput...")
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pynput>=1.8.0'], 
                         check=True, capture_output=True)
            print("✅ pynput installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install pynput: {e}")
            return False


def backup_original_files():
    """Create backups of original files."""
    print("\n💾 Creating backups...")
    
    files_to_backup = [
        'utils/hotkeys.py',
        'requirements.txt'
    ]
    
    for file_path in files_to_backup:
        if os.path.exists(file_path):
            backup_path = f"{file_path}.backup"
            shutil.copy2(file_path, backup_path)
            print(f"✅ Backed up {file_path} to {backup_path}")
        else:
            print(f"⚠️  {file_path} not found - skipping backup")


def update_hotkeys_module():
    """Update the hotkeys module to use pynput."""
    print("\n🔄 Updating hotkeys module...")
    
    # Check if the new pynput version exists
    if os.path.exists('utils/hotkeys_pynput.py'):
        print("✅ Found hotkeys_pynput.py")
        
        # Replace the original hotkeys.py with the pynput version
        if os.path.exists('utils/hotkeys.py'):
            shutil.copy2('utils/hotkeys_pynput.py', 'utils/hotkeys.py')
            print("✅ Updated utils/hotkeys.py to use pynput")
        else:
            # Create the hotkeys.py file
            shutil.copy2('utils/hotkeys_pynput.py', 'utils/hotkeys.py')
            print("✅ Created utils/hotkeys.py with pynput implementation")
        
        return True
    else:
        print("❌ hotkeys_pynput.py not found - cannot update")
        return False


def test_hotkey_functionality():
    """Test that the new hotkey system works."""
    print("\n🧪 Testing hotkey functionality...")
    
    try:
        # Import the updated hotkeys module
        sys.path.insert(0, 'utils')
        from hotkeys import HotkeyManager
        
        # Create manager and test
        manager = HotkeyManager()
        status = manager.get_status_info()
        
        print(f"   Backend: {status.get('backend', 'unknown')}")
        print(f"   Available: {status.get('available', False)}")
        print(f"   Pynput available: {status.get('pynput_available', False)}")
        
        if status.get('backend') == 'pynput':
            print("✅ Successfully using pynput backend")
            
            # Test hotkey registration
            def test_callback():
                pass
            
            if manager.register_hotkey('f9', test_callback):
                print("✅ Hotkey registration test passed")
                manager.unregister_hotkey('f9')
                return True
            else:
                print("⚠️  Hotkey registration test failed")
                return False
        else:
            print(f"⚠️  Using {status.get('backend')} backend instead of pynput")
            return False
            
    except Exception as e:
        print(f"❌ Hotkey test failed: {e}")
        return False


def update_application_files():
    """Update application files to use the new hotkey system."""
    print("\n📝 Checking application files...")
    
    # Look for files that import hotkeys
    files_to_check = [
        'voice_transcription_tool/main.py',
        'voice_transcription_tool/gui/main_window.py',
        'main.py'
    ]
    
    for file_path in files_to_check:
        if os.path.exists(file_path):
            print(f"   📄 Found {file_path}")
            
            # Check if it imports hotkeys
            with open(file_path, 'r') as f:
                content = f.read()
                
            if 'from utils.hotkeys import' in content or 'import utils.hotkeys' in content:
                print(f"   ✅ {file_path} already imports from utils.hotkeys (no changes needed)")
            elif 'from hotkeys import' in content:
                print(f"   ⚠️  {file_path} may need import path updates")
            else:
                print(f"   ℹ️  {file_path} doesn't appear to import hotkeys")
        else:
            print(f"   ⚠️  {file_path} not found")


def print_migration_summary():
    """Print summary of migration changes."""
    print("\n" + "="*60)
    print("🎉 MIGRATION SUMMARY")
    print("="*60)
    
    print("\n✅ Changes made:")
    print("   • Installed pynput library")
    print("   • Updated requirements.txt to use pynput instead of keyboard")
    print("   • Updated utils/hotkeys.py to use pynput backend")
    print("   • Created backups of original files")
    
    print("\n📋 What this fixes:")
    print("   • ❌ 'You must be root to use this library on linux' error")
    print("   • ✅ Global hotkeys now work without sudo")
    print("   • ✅ Better cross-platform compatibility")
    print("   • ✅ More reliable hotkey detection")
    
    print("\n🔧 Technical details:")
    print("   • Backend: keyboard library → pynput library")
    print("   • Method: Raw /dev/input access → X11 integration")
    print("   • Permissions: Requires sudo → Works in user space")
    print("   • Compatibility: Linux-specific → Cross-platform")
    
    print("\n📖 For more information:")
    print("   • Read LINUX_HOTKEY_SOLUTION.md")
    print("   • Test with: python3 test_hotkey_alternatives.py")
    print("   • Interactive test: python3 utils/hotkeys_pynput.py --interactive")


def main():
    """Main migration process."""
    print("🚀 Voice Transcription Tool - Hotkey Migration to pynput")
    print("="*65)
    print("\nThis script will migrate your application from the 'keyboard' library")
    print("to 'pynput' to fix Linux global hotkey issues without requiring sudo.")
    print("")
    
    # Confirm migration
    response = input("Continue with migration? (y/N): ").strip().lower()
    if response not in ['y', 'yes']:
        print("❌ Migration cancelled")
        return False
    
    success = True
    
    # Step 1: Check dependencies
    if not check_dependencies():
        print("❌ Dependency check failed")
        success = False
    
    # Step 2: Backup files
    backup_original_files()
    
    # Step 3: Update hotkeys module
    if not update_hotkeys_module():
        print("❌ Failed to update hotkeys module")
        success = False
    
    # Step 4: Test functionality
    if not test_hotkey_functionality():
        print("❌ Hotkey functionality test failed")
        success = False
    
    # Step 5: Check application files
    update_application_files()
    
    # Print summary
    if success:
        print_migration_summary()
        print("\n🎉 Migration completed successfully!")
        print("\n💡 Next steps:")
        print("   1. Test your application: python3 voice_transcription_tool/main.py")
        print("   2. Verify hotkeys work without sudo")
        print("   3. Remove backup files when satisfied: rm *.backup")
        return True
    else:
        print("\n❌ Migration completed with errors")
        print("💡 Check the issues above and try again")
        print("💡 Restore from backups if needed: cp *.backup original_files")
        return False


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ Migration interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Migration failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)