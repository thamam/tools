#!/usr/bin/env python3
"""
GUI Functionality Test Script

This script tests all button functionality and UI components to ensure they work correctly.
"""

import sys
import os
import time
import threading
import tkinter as tk
from unittest.mock import Mock, patch

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gui_functionality():
    """Test all GUI components and button functionality."""
    print("🧪 Starting GUI functionality tests...")
    
    try:
        # Import after path setup
        from gui.main_window import VoiceTranscriptionApp
        
        print("✅ Successfully imported VoiceTranscriptionApp")
        
        # Create app instance
        app = VoiceTranscriptionApp()
        print("✅ Successfully created app instance")
        
        # Test that GUI was created
        assert hasattr(app, 'root'), "Root window not created"
        assert hasattr(app, 'notebook'), "Notebook widget not created"
        assert hasattr(app, 'record_button'), "Record button not created"
        assert hasattr(app, 'status_label'), "Status label not created"
        print("✅ Basic GUI components created")
        
        # Test toolbar components
        assert hasattr(app, 'advanced_toggle'), "Advanced toggle not created"
        print("✅ Toolbar components created")
        
        # Test tab structure
        tab_count = app.notebook.index("end")
        print(f"✅ Created {tab_count} tabs")
        
        # Test advanced mode toggle
        initial_mode = app.advanced_mode
        app._toggle_advanced_mode()
        assert app.advanced_mode != initial_mode, "Advanced mode toggle not working"
        app._toggle_advanced_mode()  # Reset
        print("✅ Advanced mode toggle working")
        
        # Test engine selection
        if hasattr(app, 'engine_var'):
            available_engines = app.speech_manager.get_available_engines()
            if available_engines:
                print(f"✅ Engine selection available: {available_engines}")
            else:
                print("⚠️ No speech engines available for testing")
        
        # Test button states
        button_tests = []
        
        # Record button
        if hasattr(app, 'record_button'):
            button_tests.append(("Record Button", app.record_button, app._toggle_recording))
        
        # Settings button - find in toolbar
        settings_button = None
        for widget in app.root.winfo_children():
            if isinstance(widget, tk.Frame):
                for child in widget.winfo_children():
                    if isinstance(child, tk.Frame):
                        for grandchild in child.winfo_children():
                            if (isinstance(grandchild, tk.Button) and 
                                "Settings" in str(grandchild.cget('text'))):
                                settings_button = grandchild
                                break
        
        if settings_button:
            button_tests.append(("Settings Button", settings_button, app._open_settings))
        
        print(f"✅ Found {len(button_tests)} testable buttons")
        
        # Test button callbacks exist
        for name, button, callback in button_tests:
            assert callable(callback), f"{name} callback not callable"
            print(f"✅ {name} callback is callable")
        
        # Test history functionality
        if hasattr(app, 'history_tree'):
            # Test loading history
            app._load_recent_transcriptions()
            print("✅ History loading works")
            
            # Test clear history (mock the confirmation)
            with patch('tkinter.messagebox.askyesno', return_value=True):
                app._clear_history()
                print("✅ Clear history works")
        
        # Test debug functionality
        if hasattr(app, 'debug_text'):
            app._add_debug_message("Test debug message")
            print("✅ Debug messaging works")
        
        # Test transcription display
        if hasattr(app, 'transcription_text'):
            app.transcription_text.insert("1.0", "Test transcription")
            content = app.transcription_text.get("1.0", tk.END).strip()
            assert content == "Test transcription", "Transcription display not working"
            print("✅ Transcription display works")
        
        # Test copy functionality
        app._copy_to_clipboard()
        print("✅ Copy to clipboard works")
        
        # Test voice training availability
        if hasattr(app, 'voice_trainer'):
            phrases = app.voice_trainer.get_sample_phrases()
            assert len(phrases) > 0, "No training phrases available"
            print(f"✅ Voice training available with {len(phrases)} phrases")
        
        # Test wake word detector
        if hasattr(app, 'wake_word_detector') and app.wake_word_detector:
            status = app.wake_word_detector.get_status()
            print(f"✅ Wake word detector status: {status['is_available']}")
        
        # Test configuration
        app.config.set('test_setting', True)
        assert app.config.get('test_setting') == True, "Config not working"
        print("✅ Configuration system works")
        
        # Test window sizing
        width = app.root.winfo_reqwidth()
        height = app.root.winfo_reqheight()
        print(f"✅ Window size: {width}x{height}")
        
        print("\n🎉 All GUI functionality tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Clean up
        try:
            if 'app' in locals() and hasattr(app, 'root'):
                app.root.quit()
                app.root.destroy()
        except:
            pass

def test_individual_components():
    """Test individual components without full GUI."""
    print("\n🔬 Testing individual components...")
    
    try:
        # Test imports
        from config.settings import ConfigManager
        from config.database import DatabaseManager
        from speech.engines import SpeechEngineManager
        from speech.training import VoiceTrainer
        from audio.recorder import AudioRecorder
        from utils.wake_word import SimpleWakeWordDetector
        
        print("✅ All imports successful")
        
        # Test config manager
        config = ConfigManager()
        config.set('test_key', 'test_value')
        assert config.get('test_key') == 'test_value'
        print("✅ ConfigManager works")
        
        # Test database
        db = DatabaseManager(':memory:')
        profiles = db.get_voice_profiles()
        print("✅ DatabaseManager works")
        
        # Test speech engines
        speech_mgr = SpeechEngineManager()
        engines = speech_mgr.get_available_engines()
        print(f"✅ SpeechEngineManager works, engines: {engines}")
        
        # Test voice trainer
        trainer = VoiceTrainer(db)
        phrases = trainer.get_sample_phrases()
        print(f"✅ VoiceTrainer works, {len(phrases)} phrases")
        
        # Test audio recorder
        recorder = AudioRecorder()
        available = recorder.is_available()
        print(f"✅ AudioRecorder available: {available}")
        
        # Test simple wake word detector
        detector = SimpleWakeWordDetector()
        detector_available = detector.is_available()
        print(f"✅ SimpleWakeWordDetector available: {detector_available}")
        
        print("🎉 All component tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Component test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Voice Transcription Tool - GUI Functionality Test")
    print("=" * 60)
    
    # Test components first
    component_success = test_individual_components()
    
    # Only test GUI if components work
    if component_success:
        gui_success = test_gui_functionality()
        
        if gui_success:
            print("\n✅ ALL TESTS PASSED - Application is ready for use!")
            sys.exit(0)
        else:
            print("\n❌ GUI tests failed")
            sys.exit(1)
    else:
        print("\n❌ Component tests failed")
        sys.exit(1)