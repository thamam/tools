"""
gui/main_window.py - Main application window for the Voice Transcription Tool.

MIGRATION STEP 6A: Create this file - THE BIG ONE!

TO MIGRATE from voice_transcription.py, copy these methods:
- create_gui() → becomes _create_gui()
- All GUI creation methods (create_title, create_status_panel, etc.)
- All event handlers (toggle_recording, copy_to_clipboard, etc.)
- All UI update methods (update_transcription_display, etc.)
- Background thread management
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
import logging
import os
from datetime import datetime
from typing import Optional, Dict, Any

# Import our modular components
from config.settings import ConfigManager
from audio.recorder import AudioRecorder
from audio.devices import AudioDeviceManager
from audio.feedback import AudioFeedback
from speech.engines import SpeechEngineManager
from utils.hotkeys import HotkeyManager
from utils.logger import DebugMessageHandler
from utils.autopaste import AutoPasteManager
from utils.system_tray import SystemTrayManager
from utils.health_monitor import HealthMonitor

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

try:
    import pynput
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False


class VoiceTranscriptionApp:
    """
    Main application class - replaces the monolithic VoiceTranscriptionTool.
    
    MIGRATION: This replaces your entire VoiceTranscriptionTool class but uses
    modular components instead of having everything in one class.
    """
    
    def __init__(self, start_minimized: bool = False, enable_tray: bool = True):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Voice Transcription App")
        
        # CLI options
        self.start_minimized = start_minimized
        self.enable_tray = enable_tray
        
        # Initialize core components (modular!)
        self.config = ConfigManager()
        self.debug_handler = DebugMessageHandler()

        # Initialize managers (each handles one responsibility)
        self.audio_recorder = AudioRecorder(
            sample_rate=self.config.get('audio_rate', 16000),
            channels=self.config.get('audio_channels', 1)
        )
        self.device_manager = AudioDeviceManager()
        self.speech_manager = SpeechEngineManager()
        self.hotkey_manager = HotkeyManager()
        
        # Initialize audio feedback
        self.audio_feedback = AudioFeedback(self.config.get_all())
        
        # Initialize auto-paste manager
        self.autopaste_manager = AutoPasteManager()
        
        # Initialize system tray manager
        self.system_tray = SystemTrayManager(self)
        
        # Load saved engine preference
        saved_engine = self.config.get('current_engine', '')
        if saved_engine and self.speech_manager.is_engine_available(saved_engine):
            self.speech_manager.set_engine(saved_engine)
        
        # State variables
        self.is_recording = False
        self.recording_start_time = None
        
        # Queues for threading
        self.audio_queue = queue.Queue()
        self.transcription_queue = queue.Queue()
        
        # Initialize GUI
        self._create_gui()
        self._setup_hotkeys()
        self._start_background_threads()
        
        # Initialize debug handler callback
        self.debug_handler.add_callback(self._update_debug_display)
        
        # Initialize system tray
        self._setup_system_tray()

        # Start health monitor
        self.health_monitor = HealthMonitor(
            memory_limit_mb=self.config.get('health_memory_limit', 1024),
            cpu_limit_percent=self.config.get('health_cpu_limit', 95),
            check_interval=self.config.get('health_check_interval', 30),
            emergency_callback=self._emergency_shutdown
        )
        self.health_monitor.start()
        
        # Initial setup
        self._add_debug_message("🚀 Voice Transcription Tool initialized")
        self._add_debug_message(f"🎤 Audio method: {self.audio_recorder.get_audio_method()}")
        self._add_debug_message(f"🧠 Speech engine: {self.speech_manager.get_current_engine()}")
        self._add_debug_message(f"🔥 Hotkey: {self.config.get('hotkey_combination', 'f9')}")
        
        # System tray status
        if self.system_tray.is_available():
            self._add_debug_message("🖥️ System tray enabled")
        else:
            self._add_debug_message("⚠️ System tray not available")
    
    def _create_gui(self):
        """Create the modern GUI with tabbed interface."""
        self.root = tk.Tk()
        self.root.title("Voice Transcription Tool")
        
        # Set window size from config (reduced default)
        width = self.config.get('window_width', 800)
        height = self.config.get('window_height', 600)
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(700, 500)
        
        # Configure modern styling
        style = ttk.Style()
        style.theme_use('clam')  # More modern theme
        
        # Create main container
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Create top toolbar
        self._create_toolbar(main_container)
        
        # Create notebook for tabs
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill="both", expand=True, pady=(10, 0))
        
        # Create tabs
        self._create_main_tab()
        self._create_history_tab()
        self._create_advanced_tab()
        
        # Advanced mode state
        self.advanced_mode = self.config.get('advanced_mode', False)
        self._update_advanced_visibility()
        
        # Load initial data
        self._load_recent_transcriptions()
        
        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _create_toolbar(self, parent):
        """Create modern toolbar with essential controls."""
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill="x", pady=(0, 5))
        
        # Left side - main controls
        left_frame = ttk.Frame(toolbar)
        left_frame.pack(side="left")
        
        # Record button (large, prominent)
        self.record_button = ttk.Button(left_frame, text="🎤 Start Recording", 
                                       command=self._toggle_recording,
                                       style="Accent.TButton")
        self.record_button.pack(side="left", padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(left_frame, text="Ready", 
                                     font=("Arial", 10, "bold"))
        self.status_label.pack(side="left", padx=(10, 0))
        
        # Right side - mode and settings
        right_frame = ttk.Frame(toolbar)
        right_frame.pack(side="right")
        
        # Advanced mode toggle
        self.advanced_toggle = ttk.Checkbutton(right_frame, text="Advanced Mode",
                                              command=self._toggle_advanced_mode)
        self.advanced_toggle.pack(side="right", padx=(10, 0))
        
        # Settings button
        ttk.Button(right_frame, text="⚙️ Settings", 
                  command=self._open_settings).pack(side="right", padx=(10, 0))
        
        # Minimize to tray button
        if self.system_tray.is_available():
            ttk.Button(right_frame, text="📱 Minimize", 
                      command=self._hide_to_tray).pack(side="right", padx=(10, 0))
    
    def _create_main_tab(self):
        """Create the main transcription tab."""
        main_tab = ttk.Frame(self.notebook)
        self.notebook.add(main_tab, text="🎤 Transcription")
        
        # Create main content areas
        content_frame = ttk.Frame(main_tab)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top section - quick controls
        control_frame = ttk.LabelFrame(content_frame, text="Quick Controls", padding="10")
        control_frame.pack(fill="x", pady=(0, 10))
        
        controls_row = ttk.Frame(control_frame)
        controls_row.pack(fill="x")
        
        # Progress bar
        self.recording_progress = ttk.Progressbar(controls_row, mode='indeterminate')
        self.recording_progress.pack(fill="x", pady=(0, 10))
        
        # Engine selection
        engine_frame = ttk.Frame(controls_row)
        engine_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Label(engine_frame, text="Engine:").pack(side="left")
        self.engine_var = tk.StringVar(value=self.speech_manager.get_current_engine())
        engine_combo = ttk.Combobox(engine_frame, textvariable=self.engine_var,
                                   values=self.speech_manager.get_available_engines(),
                                   state="readonly")
        engine_combo.pack(side="left", padx=(5, 10))
        engine_combo.bind('<<ComboboxSelected>>', self._on_engine_change)
        
        # Copy button
        ttk.Button(controls_row, text="📋 Copy to Clipboard",
                  command=self._copy_to_clipboard).pack(side="right")
        
        # Main transcription area
        text_frame = ttk.LabelFrame(content_frame, text="Transcription", padding="10")
        text_frame.pack(fill="both", expand=True)
        
        # Create text widget with scrollbar
        text_container = ttk.Frame(text_frame)
        text_container.pack(fill="both", expand=True)
        
        self.transcription_text = scrolledtext.ScrolledText(text_container, 
                                                          height=15, 
                                                          font=("Arial", 11),
                                                          wrap="word")
        self.transcription_text.pack(fill="both", expand=True)
    
    def _create_history_tab(self):
        """Create the transcription history tab."""
        history_tab = ttk.Frame(self.notebook)
        self.notebook.add(history_tab, text="📜 History")
        
        content_frame = ttk.Frame(history_tab)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Controls
        control_frame = ttk.Frame(content_frame)
        control_frame.pack(fill="x", pady=(0, 10))
        
        ttk.Button(control_frame, text="🔄 Refresh",
                  command=self._load_recent_transcriptions).pack(side="left")
        ttk.Button(control_frame, text="🗑️ Clear History",
                  command=self._clear_history).pack(side="left", padx=(10, 0))
        
        # History list
        list_frame = ttk.LabelFrame(content_frame, text="Recent Transcriptions", padding="10")
        list_frame.pack(fill="both", expand=True)
        
        # Create treeview for history
        columns = ("Time", "Text", "Confidence")
        self.history_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=10)
        
        # Configure columns
        self.history_tree.heading("Time", text="Time")
        self.history_tree.heading("Text", text="Transcription")
        self.history_tree.heading("Confidence", text="Confidence")
        
        self.history_tree.column("Time", width=150)
        self.history_tree.column("Text", width=400)
        self.history_tree.column("Confidence", width=100)
        
        # Scrollbar for history
        history_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.history_tree.yview)
        self.history_tree.configure(yscrollcommand=history_scroll.set)
        
        self.history_tree.pack(side="left", fill="both", expand=True)
        history_scroll.pack(side="right", fill="y")
        
        # Bind double-click
        self.history_tree.bind("<Double-1>", self._on_history_select)
    
    def _create_advanced_tab(self):
        """Create the advanced features tab."""
        advanced_tab = ttk.Frame(self.notebook)
        self.notebook.add(advanced_tab, text="🔧 Advanced")
        self.advanced_tab = advanced_tab
        
        content_frame = ttk.Frame(advanced_tab)
        content_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # Debug panel
        debug_frame = ttk.LabelFrame(content_frame, text="Debug Messages", padding="10")
        debug_frame.pack(fill="both", expand=True)
        
        self.debug_text = scrolledtext.ScrolledText(debug_frame, height=10, 
                                                   font=("Consolas", 9))
        self.debug_text.pack(fill="both", expand=True)
    
    def _toggle_advanced_mode(self):
        """Toggle advanced mode visibility."""
        self.advanced_mode = not self.advanced_mode
        self.config.set('advanced_mode', self.advanced_mode)
        self._update_advanced_visibility()
    
    def _update_advanced_visibility(self):
        """Update visibility of advanced features."""
        if hasattr(self, 'advanced_tab'):
            if self.advanced_mode:
                self.notebook.add(self.advanced_tab, text="🔧 Advanced")
                self.advanced_toggle.state(['selected'])
            else:
                try:
                    self.notebook.forget(self.advanced_tab)
                except:
                    pass
                self.advanced_toggle.state(['!selected'])
    
    def _on_engine_change(self, event=None):
        """Handle speech engine change."""
        new_engine = self.engine_var.get()
        if self.speech_manager.set_engine(new_engine):
            self.config.set('current_engine', new_engine)
            self._add_debug_message(f"🧠 Switched to {new_engine} engine")
        else:
            self._add_debug_message(f"❌ Failed to switch to {new_engine}")
            # Reset to current engine
            self.engine_var.set(self.speech_manager.get_current_engine())
    
    def _on_history_select(self, event):
        """Handle history item selection - show full text and copy option."""
        selection = self.history_tree.selection()
        if selection:
            item_id = selection[0]
            
            # Try to get full text first, fallback to displayed text
            try:
                full_text = self.history_tree.set(item_id, "full_text")
                if not full_text:  # Fallback for older entries
                    full_text = self.history_tree.item(item_id)['values'][1]
            except:
                full_text = self.history_tree.item(item_id)['values'][1]
            
            # Show full text in a popup window
            self._show_full_transcription(full_text)
            
            self._add_debug_message("📋 Full transcription displayed")
    
    def _show_full_transcription(self, text: str):
        """Show full transcription text in a popup window."""
        popup = tk.Toplevel(self.root)
        popup.title("Full Transcription")
        popup.geometry("600x400")
        popup.resizable(True, True)
        
        # Create text widget with scrollbars
        frame = tk.Frame(popup)
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(frame, wrap=tk.WORD, width=70, height=20)
        scrollbar = tk.Scrollbar(frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Insert text and make it read-only
        text_widget.insert("1.0", text)
        text_widget.config(state=tk.DISABLED)
        
        # Button frame
        button_frame = tk.Frame(popup)
        button_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # Copy to clipboard button
        def copy_to_clipboard():
            popup.clipboard_clear()
            popup.clipboard_append(text)
            self._add_debug_message("📋 Text copied to clipboard")
        
        # Insert to current transcription button
        def insert_to_current():
            current_text = self.transcription_text.get("1.0", tk.END).strip()
            if current_text:
                new_text = current_text + "\n\n" + text
            else:
                new_text = text
            
            self.transcription_text.delete("1.0", tk.END)
            self.transcription_text.insert("1.0", new_text)
            popup.destroy()
            self._add_debug_message("📋 Text inserted to current transcription")
        
        tk.Button(button_frame, text="Copy to Clipboard", command=copy_to_clipboard).pack(side=tk.LEFT, padx=(0, 5))
        tk.Button(button_frame, text="Insert to Current", command=insert_to_current).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=popup.destroy).pack(side=tk.RIGHT)
        
        # Center the popup
        popup.transient(self.root)
        popup.grab_set()
    
    def _clear_history(self):
        """Clear transcription history."""
        if messagebox.askyesno("Clear History", 
                              "Are you sure you want to clear all transcription history?"):
            # Clear from database
            try:
                with sqlite3.connect(self.db_manager.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM transcriptions")
                    conn.commit()
                
                # Clear from UI
                for item in self.history_tree.get_children():
                    self.history_tree.delete(item)
                
                self._add_debug_message("🗑️ Transcription history cleared")
                
            except Exception as e:
                self.logger.error(f"Failed to clear history: {e}")
                messagebox.showerror("Error", f"Failed to clear history: {e}")
    
    def _create_status_panel(self, parent):
        """Create status panel."""
        status_frame = ttk.LabelFrame(parent, text="Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Ready", foreground="green")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        engine_name = self.speech_manager.get_current_engine() or 'None'
        self.engine_label = ttk.Label(status_frame, text=f"Engine: {engine_name}")
        self.engine_label.grid(row=0, column=1, sticky=tk.E)
        
        # Recording progress
        self.recording_progress = ttk.Progressbar(status_frame, length=200, mode='determinate')
        self.recording_progress.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        self.recording_progress['maximum'] = self.config.get('record_seconds', 30)
    
    def _create_controls(self, parent):
        """Create control buttons."""
        control_frame = ttk.LabelFrame(parent, text="Controls", padding="10")
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.record_button = ttk.Button(control_frame, text="🎤 Start Recording", 
                                       command=self._toggle_recording)
        self.record_button.grid(row=0, column=0, padx=(0, 10))
        
        self.hotkey_button = ttk.Button(control_frame, text="🔥 Toggle Hotkey Mode", 
                                       command=self._toggle_hotkey_mode)
        self.hotkey_button.grid(row=0, column=1, padx=(0, 10))
        
        self.settings_button = ttk.Button(control_frame, text="⚙️ Settings",
                                         command=self._open_settings)
        self.settings_button.grid(row=0, column=2)
    
    def _create_transcription_panel(self, parent):
        """Create transcription display panel."""
        transcription_frame = ttk.LabelFrame(parent, text="Live Transcription", padding="10")
        transcription_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.transcription_text = scrolledtext.ScrolledText(transcription_frame, height=8, wrap=tk.WORD)
        self.transcription_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Action buttons
        action_frame = ttk.Frame(transcription_frame)
        action_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(action_frame, text="📋 Copy to Clipboard", 
                  command=self._copy_to_clipboard).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(action_frame, text="📝 Insert at Cursor", 
                  command=self._insert_at_cursor).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(action_frame, text="🗑️ Clear", 
                  command=self._clear_transcription).grid(row=0, column=2)
        
        transcription_frame.columnconfigure(0, weight=1)
        transcription_frame.rowconfigure(0, weight=1)
    
    def _create_history_panel(self, parent):
        """Create history panel."""
        history_frame = ttk.LabelFrame(parent, text="Recent Transcriptions", padding="10")
        history_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        columns = ("Timestamp", "Text", "Method")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=4)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
        
        self.history_tree.column("Timestamp", width=150)
        self.history_tree.column("Text", width=400) 
        self.history_tree.column("Method", width=100)
        
        self.history_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        history_scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, 
                                         command=self.history_tree.yview)
        history_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
    
    def _create_debug_panel(self, parent):
        """Create debug panel."""
        debug_frame = ttk.LabelFrame(parent, text="Debug Log", padding="10")
        debug_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.debug_text = scrolledtext.ScrolledText(debug_frame, height=8, wrap=tk.WORD, 
                                                   font=("Courier", 9))
        self.debug_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Debug controls
        debug_controls = ttk.Frame(debug_frame)
        debug_controls.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(debug_controls, text="🧪 Test Microphone", 
                  command=self._test_microphone).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(debug_controls, text="📋 Audio Devices", 
                  command=self._show_audio_devices).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(debug_controls, text="🗑️ Clear Debug", 
                  command=self._clear_debug_log).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(debug_controls, text="💾 Save Log", 
                  command=self._save_debug_log).grid(row=0, column=3)
        
        debug_frame.columnconfigure(0, weight=1)
        debug_frame.rowconfigure(0, weight=1)
    
    def _setup_hotkeys(self):
        """Setup global hotkeys."""
        # Define multiple hotkeys
        hotkey_map = {
            self.config.get('hotkey_combination', 'alt+d'): self._hotkey_callback,  # Record/Stop
            'alt+s': self._hotkey_settings,  # Open Settings
        }
        
        # Register all hotkeys
        results = self.hotkey_manager.register_multiple_hotkeys(hotkey_map)
        
        # Report results
        for combination, success in results.items():
            if success:
                self._add_debug_message(f"🔥 Hotkey registered: {combination}")
            else:
                self._add_debug_message(f"❌ Failed to register hotkey: {combination}")
        
        # Log summary
        successful_hotkeys = [combo for combo, success in results.items() if success]
        if successful_hotkeys:
            self._add_debug_message(f"✅ Active hotkeys: {', '.join(successful_hotkeys)}")
        else:
            self._add_debug_message("⚠️ No hotkeys registered - run with sudo for global hotkeys")
    
    def _hotkey_settings(self):
        """Hotkey callback for opening settings."""
        if hasattr(self, 'root'):
            self.root.after(0, self._open_settings)
            self._add_debug_message("⚙️ Settings opened via hotkey")

    def _hotkey_callback(self):
        """Handle hotkey press."""
        if self.hotkey_manager.is_hotkey_active():
            self._add_debug_message(f"🔥 Hotkey activated: {self.hotkey_manager.get_current_combination()}")
            self._toggle_recording()
        else:
            self._add_debug_message("⚠️ Hotkey pressed but mode not enabled")
    
    def _setup_system_tray(self):
        """Setup system tray functionality."""
        if not self.system_tray.is_available():
            self.logger.warning("System tray not available")
            return
        
        # Set up callbacks
        self.system_tray.set_show_callback(self._show_from_tray)
        self.system_tray.set_hide_callback(self._hide_to_tray)
        self.system_tray.set_quit_callback(self._on_closing)
        self.system_tray.set_record_callback(self._toggle_recording)
        
        # Start system tray (if enabled)
        if self.enable_tray and self.system_tray.start():
            self.logger.info("System tray started successfully")
            
            # Add minimize to tray option
            self._add_tray_options_to_gui()
        elif self.enable_tray:
            self.logger.warning("Failed to start system tray")
        else:
            self.logger.info("System tray disabled via CLI option")
    
    def _add_tray_options_to_gui(self):
        """Add system tray options to the GUI."""
        # Add a minimize to tray button to the control frame if tray is available
        if hasattr(self, 'control_frame') and self.system_tray.is_available():
            tray_button = ttk.Button(
                self.control_frame, 
                text="📱 Minimize to Tray",
                command=self._hide_to_tray
            )
            tray_button.pack(side="left", padx=5)
    
    def _show_from_tray(self):
        """Show main window from system tray."""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self._add_debug_message("📱 Restored from system tray")
    
    def _hide_to_tray(self):
        """Hide main window to system tray."""
        if self.system_tray.is_available():
            self.root.withdraw()
            self.system_tray.show_notification(
                "Voice Transcription Tool",
                "Minimized to system tray. Right-click icon for options."
            )
            self._add_debug_message("📱 Minimized to system tray")
        else:
            self._add_debug_message("❌ System tray not available")
    
    def _toggle_hotkey_mode(self):
        """Toggle hotkey listening mode."""
        current_state = self.hotkey_manager.is_hotkey_active()
        new_state = not current_state
        
        self.hotkey_manager.set_active(new_state)
        
        if new_state:
            self.hotkey_button.configure(text="🔥 Hotkey Mode: ON")
            self.status_label.configure(text="Hotkey mode active", foreground="blue")
            self._add_debug_message("🔥 Hotkey mode activated")
        else:
            self.hotkey_button.configure(text="🔥 Hotkey Mode: OFF")
            self.status_label.configure(text="Ready", foreground="green")
            self._add_debug_message("🔥 Hotkey mode deactivated")
    
    def _toggle_recording(self):
        """Start or stop recording."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """
        Start audio recording.
        
        MIGRATION: Copy logic from your start_recording() method here.
        Use self.audio_recorder instead of direct audio calls.
        """
        if not self.speech_manager.get_current_engine():
            error_msg = "No speech recognition engine available!"
            self._add_debug_message(f"❌ {error_msg}")
            messagebox.showerror("Error", error_msg)
            return
            
        if not self.audio_recorder.is_available():
            error_msg = "No audio recording method available!"
            self._add_debug_message(f"❌ {error_msg}")
            messagebox.showerror("Error", error_msg)
            return
        
        # Capture active window for auto-paste (before changing focus)
        if self.config.get('auto_paste_mode', False):
            self.autopaste_manager.capture_active_window()

        self.is_recording = True
        self.recording_start_time = time.time()
        self.record_button.configure(text="🛑 Stop Recording")
        self.status_label.configure(text="Recording...", foreground="red")
        self.recording_progress['value'] = 0
        self._add_debug_message("🎤 Recording started")
        
        # Play start feedback sound
        self.audio_feedback.play_start()
        
        # Update system tray icon to show recording
        if hasattr(self, 'system_tray') and self.system_tray:
            self.system_tray.start_recording_animation()
        
        # Start recording in a separate thread
        max_duration = self.config.get('record_seconds', 30)
        threading.Thread(target=self._record_audio_thread, args=(max_duration,), daemon=True).start()
        
        # Start progress updater
        self._update_recording_progress()
    
    def _stop_recording(self):
        """Stop audio recording."""
        self.is_recording = False
        self.recording_start_time = None
        self.record_button.configure(text="🎤 Start Recording")
        self.status_label.configure(text="Processing...", foreground="orange")
        self.recording_progress['value'] = 0
        self._add_debug_message("🛑 Recording stopped")
        
        # Play stop feedback sound
        self.audio_feedback.play_stop()
        
        # Update system tray icon to stop recording animation
        if hasattr(self, 'system_tray') and self.system_tray:
            self.system_tray.stop_recording_animation()
        
        # Stop the recorder
        self.audio_recorder.stop_recording()

    def _record_audio_thread(self, max_duration):
        """Record audio in background thread."""
        try:
            audio_file = self.audio_recorder.start_recording(
                max_duration, 
                progress_callback=self._recording_progress_callback
            )
            
            if audio_file:
                self._add_debug_message(f"✅ Recording completed")
                self.audio_queue.put(audio_file)
            else:
                self._add_debug_message("❌ Recording failed")

        except Exception as e:
            self.logger.error(f"Recording thread error: {e}")
            self._add_debug_message(f"❌ Recording error: {e}")
        finally:
            # Ensure UI is reset
            self.root.after(0, self._reset_recording_ui)
    
    def _recording_progress_callback(self, elapsed_time):
        """Handle recording progress updates."""
        self.root.after(0, lambda: self._update_progress_bar(elapsed_time))
    
    def _update_progress_bar(self, elapsed_time):
        """Update the progress bar and system tray timer."""
        if self.is_recording:
            self.recording_progress['value'] = elapsed_time
            
            max_duration = self.config.get('record_seconds', 30)
            remaining = max(0, max_duration - elapsed_time)
            
            # Update system tray icon with timer
            if hasattr(self, 'system_tray') and self.system_tray:
                self.system_tray.update_timer(int(remaining))
            
            if remaining <= 3:
                self.status_label.configure(
                    text=f"Recording... {remaining:.1f}s left (finishing soon)", 
                    foreground="orange"
                )
            else:
                self.status_label.configure(
                    text=f"Recording... {remaining:.1f}s left", 
                    foreground="red"
                )
    
    def _update_recording_progress(self):
        """Update recording progress bar."""
        if self.is_recording and self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            self._update_progress_bar(elapsed)
            
            # Schedule next update
            self.root.after(100, self._update_recording_progress)
    
    def _reset_recording_ui(self):
        """Reset recording UI state."""
        self.is_recording = False
        self.recording_start_time = None
        self.record_button.configure(text="🎤 Start Recording")
        self.recording_progress['value'] = 0
    
    # Continue in next part... (methods like _start_background_threads, _transcription_worker, etc.)
    
    def _start_background_threads(self):
        """Start background processing threads."""
        threading.Thread(target=self._transcription_worker, daemon=True).start()
        threading.Thread(target=self._ui_updater, daemon=True).start()
    
    def _transcription_worker(self):
        """Background worker for transcription."""
        while True:
            try:
                audio_file = self.audio_queue.get(timeout=1)
                self._add_debug_message("🔄 Processing audio for transcription...")
                
                result = self.speech_manager.transcribe(audio_file)
                self.transcription_queue.put(result)
                
                # Clean up temp file
                try:
                    os.unlink(audio_file)
                except:
                    pass
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Transcription worker error: {e}")
    
    def _ui_updater(self):
        """Update UI with transcription results."""
        while True:
            try:
                result = self.transcription_queue.get(timeout=1)
                self.root.after(0, lambda r=result: self._update_transcription_display(r))
            except queue.Empty:
                continue
    
    # Add all the remaining methods like _update_transcription_display, _copy_to_clipboard, etc.
    # Continue in next artifact...
    
    def run(self):
        """Run the application."""
        try:
            # Start minimized if requested
            if self.start_minimized:
                self.logger.info("Starting minimized to system tray")
                self.root.withdraw()  # Hide the window
                if hasattr(self, 'system_tray') and self.system_tray:
                    self._add_debug_message("🔵 Started minimized - check system tray!")
            
            self.root.mainloop()
        except KeyboardInterrupt:
            self._on_closing()
    
    def _on_closing(self):
        """Handle application closing."""
        self.logger.info("Application closing...")
        
        # Save current window size
        geometry = self.root.geometry()
        if 'x' in geometry and '+' in geometry:
            width, height = geometry.split('+')[0].split('x')
            self.config.update({
                'window_width': int(width),
                'window_height': int(height)
            })
        
        # Save current engine
        current_engine = self.speech_manager.get_current_engine()
        if current_engine:
            self.config.set('current_engine', current_engine)
        
        # Save config
        self.config.save()
        
        # Cleanup
        self.hotkey_manager.unregister_hotkey()
        self.audio_recorder.cleanup()

        # Stop system tray
        if self.system_tray.is_available():
            self.system_tray.stop()

        if hasattr(self, 'health_monitor'):
            self.health_monitor.stop()

        self.root.destroy()
    
    def _emergency_shutdown(self):
        """Emergency shutdown for system freeze prevention."""
        try:
            self.logger.warning("🚨 Emergency shutdown initiated")
            
            # Stop all background processes first
            if hasattr(self, 'hotkey_manager'):
                try:
                    self.hotkey_manager.stop_all()
                    self.logger.info("Hotkey manager stopped")
                except:
                    pass

            if hasattr(self, 'audio_recorder'):
                try:
                    self.audio_recorder.stop_recording()
                    self.logger.info("Audio recorder stopped")
                except:
                    pass
            
            if hasattr(self, 'system_tray'):
                try:
                    self.system_tray.stop()
                    self.logger.info("System tray stopped")
                except:
                    pass

            if hasattr(self, 'health_monitor'):
                try:
                    self.health_monitor.stop()
                except:
                    pass
            
            # Force close GUI
            if hasattr(self, 'root'):
                try:
                    self.root.quit()
                    self.root.destroy()
                except:
                    pass
                    
        except Exception as e:
            # Last resort - don't let exceptions stop emergency shutdown
            pass

    def _update_transcription_display(self, result):
        """
        Update the transcription display.
        
        MIGRATION: Copy logic from your update_transcription_display() method here.
        """
        # Update status
        self.status_label.configure(text="Ready", foreground="green")
        self._add_debug_message(f"✅ Transcription completed: '{result['text'][:30]}...'")
        
        # Add to transcription text
        current_text = self.transcription_text.get("1.0", tk.END).strip()
        if current_text:
            new_text = current_text + "\n\n" + result['text']
        else:
            new_text = result['text']
            
        self.transcription_text.delete("1.0", tk.END)
        self.transcription_text.insert("1.0", new_text)
        
        # Save to database
        self.db_manager.save_transcription(
            result['text'], 
            result['confidence'], 
            result['method']
        )
        
        # Update history
        self._load_recent_transcriptions()
        
        # Show quality indicator
        if result['confidence'] > 0.8:
            self._add_debug_message(f"🎯 High confidence transcription ({result['confidence']:.2f})")
        else:
            self._add_debug_message(f"⚠️ Low confidence transcription ({result['confidence']:.2f})")
        
        # Automatic clipboard copy if enabled
        if self.config.get('auto_copy_to_clipboard', True) and PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(result['text'])
                self._add_debug_message("📋 Automatically copied to clipboard")
                
                # Auto-paste if enabled
                if self.config.get('auto_paste_mode', False):
                    if self.autopaste_manager.is_available():
                        # Use configurable delay
                        delay_ms = int(self.config.get('auto_paste_delay', 1.0) * 1000)
                        self._add_debug_message(f"⏳ Auto-pasting in {self.config.get('auto_paste_delay', 1.0):.1f} seconds...")
                        self.root.after(delay_ms, lambda: self._perform_auto_paste(result['text']))
                    else:
                        self._add_debug_message("⚠️ Auto-paste not available - text copied to clipboard")
                        self._add_debug_message(f"💡 {self.autopaste_manager.install_instructions().split(chr(10))[0]}")
                
                # Show temporary notification
                self.status_label.configure(text="Copied to clipboard!", foreground="blue")
                self.root.after(2000, lambda: self.status_label.configure(text="Ready", foreground="green"))
                
                # System tray notification
                if self.system_tray.is_available():
                    self.system_tray.show_notification(
                        "Voice Transcription Complete",
                        f"'{result['text'][:50]}{'...' if len(result['text']) > 50 else ''}'"
                    )

            except Exception as e:
                self.logger.error(f"Auto clipboard copy failed: {e}")
    
    def _perform_auto_paste(self, text: str):
        """Perform auto-paste operation."""
        if self.autopaste_manager.auto_paste(text):
            self._add_debug_message("✅ Auto-pasted successfully!")
            self.status_label.configure(text="Auto-pasted!", foreground="green")
        else:
            self._add_debug_message("⚠️ Auto-paste failed - use Ctrl+V to paste")
            self.status_label.configure(text="Ready to paste (Ctrl+V)", foreground="orange")
    
    def _copy_to_clipboard(self):
        """
        Copy current transcription to clipboard.
        
        MIGRATION: Copy logic from your copy_to_clipboard() method here.
        """
        text = self.transcription_text.get("1.0", tk.END).strip()
        if text and PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(text)
                self.status_label.configure(text="Copied to clipboard!", foreground="blue")
                self._add_debug_message("📋 Text copied to clipboard")
                self.root.after(2000, lambda: self.status_label.configure(text="Ready", foreground="green"))
            except Exception as e:
                self._add_debug_message(f"❌ Clipboard copy failed: {e}")
        elif not PYPERCLIP_AVAILABLE:
            self._add_debug_message("❌ Pyperclip not available")
        else:
            self._add_debug_message("⚠️ No text to copy")

    def _insert_at_cursor(self):
        """
        Insert transcription at current cursor position.
        
        MIGRATION: Copy logic from your insert_at_cursor() method here.
        """
        text = self.transcription_text.get("1.0", tk.END).strip()
        if text:
            if PYPERCLIP_AVAILABLE and KEYBOARD_AVAILABLE:
                try:
                    # Copy to clipboard and simulate paste
                    pyperclip.copy(text)
                    keyboard.send('ctrl+v')
                    self.status_label.configure(text="Text inserted!", foreground="blue")
                    self._add_debug_message("📝 Text inserted at cursor")
                    self.root.after(2000, lambda: self.status_label.configure(text="Ready", foreground="green"))
                except Exception as e:
                    self._add_debug_message(f"❌ Text insertion failed: {e}")
            else:
                self._add_debug_message("❌ Text insertion requires pyperclip and keyboard libraries")
        else:
            self._add_debug_message("⚠️ No text to insert")

    def _clear_transcription(self):
        """Clear the transcription display."""
        self.transcription_text.delete("1.0", tk.END)
        self._add_debug_message("🗑️ Transcription cleared")

    def _load_recent_transcriptions(self):
        """Load recent transcriptions into history view."""
        try:
            # Only load if history tree exists (GUI is initialized)
            if not hasattr(self, 'history_tree'):
                return
                
            transcriptions = self.db_manager.get_recent_transcriptions(50)
            
            # Clear existing items
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
                
            # Add new items
            for trans in transcriptions:
                # Format timestamp
                try:
                    if isinstance(trans['timestamp'], str):
                        dt = datetime.fromisoformat(trans['timestamp'].replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M')
                    else:
                        formatted_time = str(trans['timestamp'])[:16]
                except:
                    formatted_time = str(trans['timestamp'])[:16]
                
                # Store full text and create display text
                full_text = trans['text']
                display_text = full_text
                if len(display_text) > 120:  # Increased from 80 to 120 characters
                    display_text = display_text[:120] + "..."
                
                # Get confidence or method
                confidence = trans.get('confidence', 'N/A')
                if isinstance(confidence, (int, float)):
                    confidence = f"{confidence:.0%}"
                
                # Store full text in the tree item for later retrieval
                item_id = self.history_tree.insert("", "end", values=(formatted_time, display_text, confidence))
                # Store full text as a tag so we can retrieve it later
                self.history_tree.set(item_id, "full_text", full_text)
                
        except Exception as e:
            self.logger.error(f"History load error: {e}")
            self._add_debug_message(f"❌ Failed to load history: {e}")

    def _test_microphone(self):
        """
        Run microphone test.
        
        MIGRATION: Copy logic from your run_mic_test() method here.
        """
        self._add_debug_message("🧪 Starting microphone test...")
        
        def test_thread():
            success = self.audio_recorder.test_recording(1.0)
            if success:
                self.root.after(0, lambda: self._add_debug_message("✅ Microphone test passed"))
            else:
                self.root.after(0, lambda: self._add_debug_message("❌ Microphone test failed"))
                
        threading.Thread(target=test_thread, daemon=True).start()

    def _show_audio_devices(self):
        """
        Show available audio devices.
        
        MIGRATION: Copy logic from your show_audio_devices() method here.
        """
        self._add_debug_message("📋 Available audio devices:")
        device_info = self.device_manager.get_devices_info()
        for info in device_info:
            self._add_debug_message(f"  {info}")

    def _clear_debug_log(self):
        """Clear debug log."""
        self.debug_text.delete("1.0", tk.END)
        self.debug_handler.clear_messages()
        self._add_debug_message("🗑️ Debug log cleared")

    def _save_debug_log(self):
        """Save debug log to file."""
        try:
            content = self.debug_text.get("1.0", tk.END)
            from datetime import datetime
            filename = f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(content)
            self._add_debug_message(f"💾 Debug log saved to {filename}")
        except Exception as e:
            self._add_debug_message(f"❌ Failed to save debug log: {e}")

    def _add_debug_message(self, message: str):
        """Add a debug message."""
        self.debug_handler.add_message(message)
        self.logger.info(message)

    def _update_debug_display(self, message: str):
        """Update debug display with new message."""
        self.debug_text.insert(tk.END, message + "\n")
        self.debug_text.see(tk.END)
        
        # Keep reasonable size
        lines = self.debug_text.get("1.0", tk.END).split("\n")
        if len(lines) > 100:
            self.debug_text.delete("1.0", "2.0")

    def _open_settings(self):
        """
        Open settings window with scrollable content.
        
        MIGRATION: Copy logic from your open_settings() method here.
        This creates the settings dialog with engine selection, hotkeys, etc.
        """
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Voice Transcription Tool - Settings")
        settings_window.geometry("600x800")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Button frame at bottom (create first so it doesn't get pushed down)
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(side="bottom", fill="x", padx=10, pady=10)
        
        # Create main frame with scrollbar
        main_frame = ttk.Frame(settings_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=(10, 0))
        
        # Create canvas and scrollbar
        canvas = tk.Canvas(main_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        # Configure scrolling
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Enable mouse wheel scrolling (cross-platform)
        def _on_mousewheel(event):
            if event.delta:
                # Windows
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            else:
                # Linux
                if event.num == 4:
                    canvas.yview_scroll(-1, "units")
                elif event.num == 5:
                    canvas.yview_scroll(1, "units")
        
        # Bind mouse wheel events
        canvas.bind_all("<MouseWheel>", _on_mousewheel)  # Windows
        canvas.bind_all("<Button-4>", _on_mousewheel)     # Linux
        canvas.bind_all("<Button-5>", _on_mousewheel)     # Linux
        
        # Use scrollable_frame as parent for all settings
        parent = scrollable_frame
        
        # Engine selection
        engine_frame = ttk.LabelFrame(parent, text="Speech Engine", padding="10")
        engine_frame.pack(fill="x", pady=(0, 10))
        
        current_engine = self.speech_manager.get_current_engine() or ''
        engine_var = tk.StringVar(value=current_engine)
        
        available_engines = self.speech_manager.get_available_engines()
        
        for engine in available_engines:
            if engine == 'whisper':
                ttk.Radiobutton(engine_frame, text="Whisper (Local, High Quality)", 
                                variable=engine_var, value="whisper").pack(anchor="w")
            elif engine == 'google':
                ttk.Radiobutton(engine_frame, text="Google Speech Recognition (Online)", 
                                variable=engine_var, value="google").pack(anchor="w")
        
        if not available_engines:
            ttk.Label(engine_frame, text="⚠️ No speech engines available", 
                        foreground="orange").pack(anchor="w")
        
        # Hotkey configuration
        hotkey_frame = ttk.LabelFrame(parent, text="Hotkey Configuration", padding="10")
        hotkey_frame.pack(fill="x", pady=(0, 10))
        
        current_hotkey = self.config.get('hotkey_combination', 'f9')
        ttk.Label(hotkey_frame, text=f"Current hotkey: {current_hotkey}").pack(anchor="w")
        
        hotkey_var = tk.StringVar(value=current_hotkey)
        
        # One-handed options
        ttk.Label(hotkey_frame, text="One-handed options (recommended):", 
                    font=("Arial", 9, "bold")).pack(anchor="w", pady=(10,0))
        
        one_handed_options = self.hotkey_manager.get_one_handed_combinations()
        for value, label in one_handed_options:
            ttk.Radiobutton(hotkey_frame, text=label, variable=hotkey_var, value=value).pack(anchor="w")
        
        # Two-handed options
        ttk.Label(hotkey_frame, text="Two-handed options:", 
                    font=("Arial", 9, "bold")).pack(anchor="w", pady=(10,0))
        
        two_handed_options = self.hotkey_manager.get_two_handed_combinations()
        for value, label in two_handed_options:
            ttk.Radiobutton(hotkey_frame, text=label, variable=hotkey_var, value=value).pack(anchor="w")

        # Clipboard settings
        clipboard_frame = ttk.LabelFrame(parent, text="Clipboard Settings", padding="10")
        clipboard_frame.pack(fill="x", pady=(0, 10))
        
        # Auto copy to clipboard
        auto_copy_var = tk.BooleanVar(value=self.config.get('auto_copy_to_clipboard', True))
        ttk.Checkbutton(clipboard_frame, text="Automatically copy transcriptions to clipboard", 
                       variable=auto_copy_var).pack(anchor="w")
        
        ttk.Label(clipboard_frame, text="When enabled, every transcription will be automatically\ncopied to your clipboard for easy pasting.", 
                 font=("Arial", 9), foreground="gray").pack(anchor="w", pady=(5,0))
        
        # Auto-paste mode
        auto_paste_var = tk.BooleanVar(value=self.config.get('auto_paste_mode', False))
        ttk.Checkbutton(clipboard_frame, text="Auto-paste mode (paste at cursor position)", 
                       variable=auto_paste_var).pack(anchor="w", pady=(10,0))
        
        # Auto-paste status
        if self.autopaste_manager.is_available():
            status_text = f"✅ Auto-paste available using: {self.autopaste_manager.get_method()}"
            status_color = "green"
        else:
            status_text = "⚠️ Auto-paste not available - install xdotool"
            status_color = "orange"
        
        ttk.Label(clipboard_frame, text=status_text, 
                 font=("Arial", 9), foreground=status_color).pack(anchor="w", pady=(5,0))
        
        if not self.autopaste_manager.is_available():
            ttk.Label(clipboard_frame, text="To enable: sudo apt-get install xdotool", 
                     font=("Arial", 8), foreground="gray").pack(anchor="w")
        
        # Auto-paste delay setting
        delay_frame = ttk.Frame(clipboard_frame)
        delay_frame.pack(fill="x", pady=(10,0))
        ttk.Label(delay_frame, text="Auto-paste delay:").pack(side="left")
        
        auto_paste_delay_var = tk.DoubleVar(value=self.config.get('auto_paste_delay', 1.0))
        delay_scale = ttk.Scale(delay_frame, from_=0.5, to=3.0, 
                               variable=auto_paste_delay_var, orient="horizontal", length=150)
        delay_scale.pack(side="left", padx=(10,0))
        
        delay_label = ttk.Label(delay_frame, text=f"{auto_paste_delay_var.get():.1f}s")
        delay_label.pack(side="left", padx=(10,0))
        
        def update_delay_label(*args):
            delay_label.config(text=f"{auto_paste_delay_var.get():.1f}s")
        auto_paste_delay_var.trace_add("write", update_delay_label)
        
        # System tray settings
        tray_frame = ttk.LabelFrame(parent, text="System Tray", padding="10")
        tray_frame.pack(fill="x", pady=(0, 10))
        
        # System tray status
        if self.system_tray.is_available():
            tray_status_text = "✅ System tray available"
            tray_status_color = "green"
        else:
            tray_status_text = "⚠️ System tray not available - install pystray pillow"
            tray_status_color = "orange"
        
        ttk.Label(tray_frame, text=tray_status_text, 
                 font=("Arial", 9), foreground=tray_status_color).pack(anchor="w")
        
        if self.system_tray.is_available():
            ttk.Label(tray_frame, text="• Right-click tray icon for quick actions\n• Use 'Minimize to Tray' to run in background", 
                     font=("Arial", 8), foreground="gray").pack(anchor="w", pady=(5,0))
        else:
            ttk.Label(tray_frame, text="To enable: pip install pystray pillow", 
                     font=("Arial", 8), foreground="gray").pack(anchor="w")
        
        # Audio feedback settings
        audio_frame = ttk.LabelFrame(parent, text="Audio Feedback", padding="10")
        audio_frame.pack(fill="x", pady=(0, 10))
        
        # Enable/disable audio feedback
        feedback_enabled_var = tk.BooleanVar(value=self.config.get('audio_feedback_enabled', True))
        ttk.Checkbutton(audio_frame, text="Enable audio feedback", 
                       variable=feedback_enabled_var).pack(anchor="w")
        
        # Feedback type selection
        feedback_type_var = tk.StringVar(value=self.config.get('audio_feedback_type', 'beep'))
        ttk.Label(audio_frame, text="Feedback type:").pack(anchor="w", pady=(10,0))
        ttk.Radiobutton(audio_frame, text="System beep", 
                       variable=feedback_type_var, value="beep").pack(anchor="w", padx=(20,0))
        ttk.Radiobutton(audio_frame, text="Text-to-speech", 
                       variable=feedback_type_var, value="tts").pack(anchor="w", padx=(20,0))
        
        # Volume control
        volume_frame = ttk.Frame(audio_frame)
        volume_frame.pack(fill="x", pady=(10,0))
        ttk.Label(volume_frame, text="Volume:").pack(side="left")
        
        volume_var = tk.DoubleVar(value=self.config.get('audio_feedback_volume', 0.5))
        volume_scale = ttk.Scale(volume_frame, from_=0.0, to=1.0, 
                                variable=volume_var, orient="horizontal", length=200)
        volume_scale.pack(side="left", padx=(10,0))
        
        volume_label = ttk.Label(volume_frame, text=f"{int(volume_var.get()*100)}%")
        volume_label.pack(side="left", padx=(10,0))
        
        def update_volume_label(*args):
            volume_label.config(text=f"{int(volume_var.get()*100)}%")
        volume_var.trace_add("write", update_volume_label)
        
        # Test button
        def test_audio_feedback():
            # Temporarily apply settings
            self.audio_feedback.set_enabled(feedback_enabled_var.get())
            self.audio_feedback.set_feedback_type(feedback_type_var.get())
            self.audio_feedback.set_volume(volume_var.get())
            
            # Play test sounds
            self.audio_feedback.play_start()
            self.root.after(1000, self.audio_feedback.play_stop)
            
        ttk.Button(audio_frame, text="🔊 Test Feedback", 
                  command=test_audio_feedback).pack(pady=(10,0))
        
        # Window size configuration
        window_frame = ttk.LabelFrame(parent, text="Window Settings", padding="10")
        window_frame.pack(fill="x", pady=(0, 10))
        
        current_geometry = self.root.geometry()
        if 'x' in current_geometry and '+' in current_geometry:
            width, height = current_geometry.split('+')[0].split('x')
        else:
            width, height = "900", "800"
        
        size_frame = ttk.Frame(window_frame)
        size_frame.pack(fill="x")
        
        ttk.Label(size_frame, text="Window Size:").pack(side="left")
        
        width_var = tk.StringVar(value=width)
        height_var = tk.StringVar(value=height)
        
        ttk.Label(size_frame, text="Width:").pack(side="left", padx=(10, 0))
        width_entry = ttk.Entry(size_frame, textvariable=width_var, width=8)
        width_entry.pack(side="left", padx=5)
        
        ttk.Label(size_frame, text="Height:").pack(side="left", padx=(10, 0))
        height_entry = ttk.Entry(size_frame, textvariable=height_var, width=8)
        height_entry.pack(side="left", padx=5)
        
        def apply_window_size():
            try:
                new_width = int(width_var.get())
                new_height = int(height_var.get())
                
                if new_width < 800 or new_height < 600:
                    messagebox.showwarning("Invalid Size", "Minimum size is 800x600")
                    return
                    
                self.root.geometry(f"{new_width}x{new_height}")
                self._add_debug_message(f"🖼️ Window resized to {new_width}x{new_height}")
                
            except ValueError:
                messagebox.showerror("Invalid Input", "Please enter valid numbers")
        
        ttk.Button(size_frame, text="Apply Size", command=apply_window_size).pack(side="left", padx=10)

        # Save button
        def save_settings():
            self._add_debug_message("💾 Saving settings...")
            
            # Update speech engine
            new_engine = engine_var.get()
            if new_engine != self.speech_manager.get_current_engine():
                if self.speech_manager.set_engine(new_engine):
                    # Update engine label if it exists (in main window)
                    if hasattr(self, 'engine_label'):
                        self.engine_label.configure(text=f"Engine: {new_engine}")
                    self._add_debug_message(f"✅ Engine changed to: {new_engine}")
                else:
                    self._add_debug_message(f"❌ Failed to change engine to: {new_engine}")
            
            # Update hotkey
            new_hotkey = hotkey_var.get()
            old_hotkey = self.config.get('hotkey_combination', 'alt+d')
            
            if new_hotkey != old_hotkey:
                # Try to register the new hotkey
                success = self.hotkey_manager.register_hotkey(new_hotkey, self._hotkey_callback)
                if success:
                    self.config.set('hotkey_combination', new_hotkey)
                    self._add_debug_message(f"✅ Hotkey changed to: {new_hotkey}")
                else:
                    # Keep the old hotkey setting if registration fails
                    hotkey_var.set(old_hotkey)
                    self._add_debug_message(f"❌ Failed to change hotkey to: {new_hotkey}")
                    self._add_debug_message("💡 Tip: Run with sudo for global hotkeys")
            
            # Save clipboard settings
            self.config.set('auto_copy_to_clipboard', auto_copy_var.get())
            self.config.set('auto_paste_mode', auto_paste_var.get())
            self.config.set('auto_paste_delay', auto_paste_delay_var.get())
            
            # Save audio feedback settings
            self.config.update({
                'audio_feedback_enabled': feedback_enabled_var.get(),
                'audio_feedback_type': feedback_type_var.get(),
                'audio_feedback_volume': volume_var.get()
            })
            
            # Apply audio feedback settings
            self.audio_feedback.set_enabled(feedback_enabled_var.get())
            self.audio_feedback.set_feedback_type(feedback_type_var.get())
            self.audio_feedback.set_volume(volume_var.get())
            
            # Save window size
            self.config.update({
                'window_width': int(width_var.get()),
                'window_height': int(height_var.get())
            })

            # Save all settings
            self.config.save()
            self._add_debug_message("✅ All settings saved")
            settings_window.destroy()
            
        # Add buttons to the button frame created at the top
        ttk.Button(button_frame, text="Save Settings",
                   command=save_settings).pack(side="right", padx=(10, 0))
        ttk.Button(button_frame, text="Cancel",
                   command=settings_window.destroy).pack(side="right")


# END OF VoiceTranscriptionApp CLASS