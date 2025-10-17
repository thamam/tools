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

# Import our modular components
from config.settings import ConfigManager
from audio.recorder import AudioRecorder
from audio.devices import AudioDeviceManager
from audio.feedback import AudioFeedback
from speech.engines import SpeechEngineManager
from utils.hotkeys import HotkeyManager
from utils.autopaste import AutoPasteManager
from utils.health_monitor import HealthMonitor

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False


class VoiceTranscriptionApp:
    """
    Main application class - replaces the monolithic VoiceTranscriptionTool.
    
    MIGRATION: This replaces your entire VoiceTranscriptionTool class but uses
    modular components instead of having everything in one class.
    """
    
    def __init__(self, start_minimized: bool = False):
        self.logger = logging.getLogger(__name__)
        self.logger.info("Initializing Voice Transcription App")

        # CLI options
        self.start_minimized = start_minimized

        # Initialize core components
        self.config = ConfigManager()

        # Initialize managers
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

        # Load saved engine preference
        saved_engine = self.config.get('current_engine', '')
        if saved_engine and self.speech_manager.is_engine_available(saved_engine):
            self.speech_manager.set_engine(saved_engine)

        # State variables
        self.is_recording = False
        self.recording_start_time = None
        self.shutdown_requested = False  # Flag for clean thread shutdown

        # Queues for threading
        self.audio_queue = queue.Queue()
        self.transcription_queue = queue.Queue()

        # Track background threads for clean shutdown
        self.transcription_thread = None
        self.ui_updater_thread = None

        # Initialize GUI
        self._create_gui()
        self._setup_hotkeys()
        self._start_background_threads()

        # Start health monitor (no emergency callback - just log warnings)
        self.health_monitor = HealthMonitor(
            memory_limit_mb=self.config.get('health_memory_limit', 2048),  # Whisper needs more
            cpu_limit_percent=self.config.get('health_cpu_limit', 98),
            check_interval=self.config.get('health_check_interval', 30)
            # emergency_callback removed - health monitor now only logs warnings
        )
        self.health_monitor.start()

        # Initial status log
        self.logger.info(f"Audio method: {self.audio_recorder.get_audio_method()}")
        self.logger.info(f"Speech engine: {self.speech_manager.get_current_engine()}")
        self.logger.info(f"Hotkey: {self.config.get('hotkey_combination', 'alt+d')}")
    
    def _create_gui(self):
        """Create simple single-window GUI."""
        self.root = tk.Tk()
        self.root.title("Voice Transcription Tool")
        self.root.geometry("700x500")
        self.root.minsize(600, 400)

        # Configure styling
        style = ttk.Style()
        style.theme_use('clam')

        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Title
        title_label = ttk.Label(main_frame, text="🎤 Voice Transcription",
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))

        # Status panel
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill="x", pady=(0, 15))

        self.status_label = ttk.Label(status_frame, text="Ready",
                                     font=("Arial", 11, "bold"),
                                     foreground="green")
        self.status_label.pack()

        # Recording button (large and prominent)
        self.record_button = ttk.Button(main_frame, text="🎤 Start Recording",
                                       command=self._toggle_recording)
        self.record_button.pack(pady=15, ipadx=20, ipady=10)

        # Progress bar
        self.recording_progress = ttk.Progressbar(main_frame, mode='determinate',
                                                 length=400)
        self.recording_progress.pack(pady=(0, 20))
        self.recording_progress['maximum'] = self.config.get('record_seconds', 30)

        # Transcription display
        text_label = ttk.Label(main_frame, text="Transcription:",
                              font=("Arial", 10, "bold"))
        text_label.pack(anchor="w", pady=(0, 5))

        self.transcription_text = scrolledtext.ScrolledText(main_frame,
                                                           height=12,
                                                           font=("Arial", 11),
                                                           wrap="word")
        self.transcription_text.pack(fill="both", expand=True, pady=(0, 15))

        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x")

        ttk.Button(button_frame, text="📋 Copy to Clipboard",
                  command=self._copy_to_clipboard).pack(side="left", padx=(0, 10))
        ttk.Button(button_frame, text="🗑️ Clear",
                  command=self._clear_transcription).pack(side="left")
        ttk.Button(button_frame, text="⚙️ Settings",
                  command=self._open_settings).pack(side="right")

        # Bind close event
        self.root.protocol("WM_DELETE_WINDOW", self._on_closing)
    
    def _clear_transcription(self):
        """Clear the transcription display."""
        self.transcription_text.delete("1.0", tk.END)
        self.logger.info("Transcription cleared")
    
    
    
    
    def _setup_hotkeys(self):
        """Setup global hotkeys."""
        hotkey_combination = self.config.get('hotkey_combination', 'alt+d')
        success = self.hotkey_manager.register_hotkey(hotkey_combination, self._hotkey_callback)

        if success:
            self.logger.info(f"Hotkey registered: {hotkey_combination}")
        else:
            self.logger.warning(f"Failed to register hotkey: {hotkey_combination}")
    
    def _hotkey_callback(self):
        """Handle hotkey press."""
        self.logger.info("Hotkey activated")
        self._toggle_recording()
    
    def _toggle_recording(self):
        """Start or stop recording."""
        if not self.is_recording:
            self._start_recording()
        else:
            self._stop_recording()
    
    def _start_recording(self):
        """Start audio recording."""
        if not self.speech_manager.get_current_engine():
            error_msg = "No speech recognition engine available!"
            self.logger.error(error_msg)
            messagebox.showerror("Error", error_msg)
            return

        if not self.audio_recorder.is_available():
            error_msg = "No audio recording method available!"
            self.logger.error(error_msg)
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
        self.logger.info("Recording started")

        # Play start feedback sound
        self.audio_feedback.play_start()

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
        self.logger.info("Recording stopped")

        # Play stop feedback sound
        self.audio_feedback.play_stop()

        # Stop the recorder
        self.audio_recorder.stop_recording()

    def _record_audio_thread(self, max_duration):
        """Record audio in background thread."""
        try:
            result = self.audio_recorder.start_recording(
                max_duration,
                progress_callback=self._recording_progress_callback
            )

            if result.get('success'):
                self.logger.info("Recording completed")
                self.audio_queue.put(result['audio_file'])
            else:
                # Handle recording errors with clear user feedback
                error_msg = result.get('error', 'Recording failed')
                error_type = result.get('error_type', 'unknown')

                self.logger.error(f"Recording failed ({error_type}): {error_msg}")

                # Show appropriate error message based on type
                if error_type == 'silent_audio':
                    self.root.after(0, lambda: messagebox.showwarning(
                        "No Speech Detected",
                        error_msg
                    ))
                elif error_type == 'device_error':
                    self.root.after(0, lambda: messagebox.showerror(
                        "Microphone Error",
                        error_msg
                    ))
                else:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Recording Error",
                        error_msg
                    ))

        except Exception as e:
            self.logger.error(f"Recording thread error: {e}")
            self.root.after(0, lambda: messagebox.showerror(
                "Recording Error",
                f"Unexpected error during recording:\n{str(e)}"
            ))
        finally:
            # Ensure UI is reset
            self.root.after(0, self._reset_recording_ui)
    
    def _recording_progress_callback(self, elapsed_time, audio_level=0.0):
        """
        Handle recording progress updates with audio level feedback.

        Args:
            elapsed_time: Time elapsed since recording started
            audio_level: RMS audio level for visual feedback
        """
        self.root.after(0, lambda: self._update_progress_bar(elapsed_time, audio_level))

    def _update_progress_bar(self, elapsed_time, audio_level=0.0):
        """
        Update the progress bar with audio level color-coding.

        Audio level thresholds:
        - < 500: Low/silent (yellow warning)
        - 500-5000: Good level (green)
        - > 5000: Loud/clipping (red warning)
        """
        if self.is_recording:
            self.recording_progress['value'] = elapsed_time

            max_duration = self.config.get('record_seconds', 30)
            remaining = max(0, max_duration - elapsed_time)

            # Determine audio level status
            if audio_level < 500:
                level_status = "🟡 Low volume"
                level_color = "orange"
            elif audio_level > 5000:
                level_status = "🔴 Too loud"
                level_color = "red"
            else:
                level_status = "🟢 Good"
                level_color = "green"

            # Format time display
            elapsed_str = f"{int(elapsed_time)}s"
            max_str = f"{int(max_duration)}s"

            if remaining <= 3:
                self.status_label.configure(
                    text=f"Recording: {elapsed_str}/{max_str} ({level_status}) - Finishing soon!",
                    foreground="orange"
                )
            else:
                self.status_label.configure(
                    text=f"Recording: {elapsed_str}/{max_str} ({level_status})",
                    foreground=level_color
                )
    
    def _update_recording_progress(self):
        """Update recording progress bar (fallback when no audio level available)."""
        if self.is_recording and self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            self._update_progress_bar(elapsed, audio_level=1000)  # Default "good" level

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
        self.transcription_thread = threading.Thread(target=self._transcription_worker, daemon=True)
        self.ui_updater_thread = threading.Thread(target=self._ui_updater, daemon=True)
        self.transcription_thread.start()
        self.ui_updater_thread.start()
    
    def _transcription_worker(self):
        """Background worker for transcription."""
        while not self.shutdown_requested:
            try:
                audio_file = self.audio_queue.get(timeout=1)
                if self.shutdown_requested:
                    break

                self.logger.info("Processing audio for transcription...")

                result = self.speech_manager.transcribe(audio_file)
                if not self.shutdown_requested:
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

        self.logger.info("Transcription worker thread shutting down")
    
    def _ui_updater(self):
        """Update UI with transcription results."""
        while not self.shutdown_requested:
            try:
                result = self.transcription_queue.get(timeout=1)
                if self.shutdown_requested:
                    break
                self.root.after(0, lambda r=result: self._update_transcription_display(r))
            except queue.Empty:
                continue

        self.logger.info("UI updater thread shutting down")
    
    # Add all the remaining methods like _update_transcription_display, _copy_to_clipboard, etc.
    # Continue in next artifact...
    
    def run(self):
        """Run the application."""
        try:
            # Start minimized if requested
            if self.start_minimized:
                self.logger.info("Starting minimized")
                self.root.withdraw()  # Hide the window

            self.root.mainloop()
        except KeyboardInterrupt:
            self._on_closing()
    
    def _shutdown_threads(self):
        """Shutdown all background threads gracefully."""
        self.logger.info("Shutting down background threads...")

        # Signal threads to stop
        self.shutdown_requested = True

        # Clear queues to unblock any waiting threads
        while not self.audio_queue.empty():
            try:
                self.audio_queue.get_nowait()
            except queue.Empty:
                break

        while not self.transcription_queue.empty():
            try:
                self.transcription_queue.get_nowait()
            except queue.Empty:
                break

        # Wait for threads to finish with timeout
        threads_to_wait = [
            (self.transcription_thread, "Transcription worker"),
            (self.ui_updater_thread, "UI updater")
        ]

        for thread, name in threads_to_wait:
            if thread and thread.is_alive():
                self.logger.info(f"Waiting for {name} thread to finish...")
                thread.join(timeout=2.0)
                if thread.is_alive():
                    self.logger.warning(f"{name} thread did not finish in time (daemon will be terminated)")
                else:
                    self.logger.info(f"{name} thread finished cleanly")

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

        # Shutdown threads first
        self._shutdown_threads()

        # Cleanup managers
        self.hotkey_manager.unregister_hotkey()
        self.audio_recorder.cleanup()

        if hasattr(self, 'health_monitor'):
            self.health_monitor.stop()

        self.root.destroy()
    
    def _emergency_shutdown(self):
        """Emergency shutdown for system freeze prevention."""
        try:
            self.logger.warning("🚨 Emergency shutdown initiated")

            # Shutdown threads
            try:
                self._shutdown_threads()
            except:
                pass

            # Stop all background processes
            if hasattr(self, 'hotkey_manager'):
                try:
                    self.hotkey_manager.stop_all()
                    self.logger.info("Hotkey manager stopped")
                except:
                    pass

            if hasattr(self, 'audio_recorder'):
                try:
                    self.audio_recorder.stop_recording()
                    self.audio_recorder.cleanup()
                    self.logger.info("Audio recorder stopped")
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
        """Update the transcription display."""
        # Update status
        self.status_label.configure(text="Ready", foreground="green")

        # Check if transcription succeeded
        if not result.get('success', False):
            error_msg = result.get('error', 'Transcription failed')

            # Check if both engines failed
            if result.get('fallback_failed'):
                primary = result.get('primary_engine', 'unknown')
                fallback = result.get('fallback_engine', 'unknown')
                fallback_error = result.get('fallback_error', 'Unknown error')

                detailed_error = f"Both speech engines failed:\n\n"
                detailed_error += f"Primary ({primary}): {error_msg}\n"
                detailed_error += f"Fallback ({fallback}): {fallback_error}\n\n"
                detailed_error += "Please check:\n"
                detailed_error += "• Audio quality (speak clearly, reduce background noise)\n"
                detailed_error += "• Microphone volume is adequate\n"
                detailed_error += "• Internet connection (for Google Speech)"

                messagebox.showerror("Transcription Failed", detailed_error)
            else:
                messagebox.showerror("Transcription Error", error_msg)

            self.logger.error(f"Transcription failed: {error_msg}")
            return

        # Transcription succeeded
        text = result.get('text', '').strip()

        if not text:
            self.logger.warning("Transcription returned empty text")
            messagebox.showwarning("Empty Result", "Transcription completed but no text was detected.")
            return

        # Log success with fallback info if applicable
        if result.get('fallback_success'):
            fallback_from = result.get('fallback_from', 'unknown')
            method = result.get('method', 'unknown')
            self.logger.info(f"Transcription completed with fallback: {fallback_from} → {method}")
            self.status_label.configure(text=f"Ready (used {method} fallback)", foreground="orange")
            # Show brief notification
            self.root.after(3000, lambda: self.status_label.configure(text="Ready", foreground="green"))
        else:
            method = result.get('method', 'unknown')
            self.logger.info(f"Transcription completed with {method}: '{text[:30]}...'")

        # Add to transcription text
        current_text = self.transcription_text.get("1.0", tk.END).strip()
        if current_text:
            new_text = current_text + "\n\n" + text
        else:
            new_text = text

        self.transcription_text.delete("1.0", tk.END)
        self.transcription_text.insert("1.0", new_text)

        # Log quality indicator
        if result.get('confidence', 0) > 0.8:
            self.logger.info(f"High confidence transcription ({result.get('confidence', 0):.2f})")
        else:
            self.logger.warning(f"Low confidence transcription ({result.get('confidence', 0):.2f})")

        # Automatic clipboard copy if enabled
        if self.config.get('auto_copy_to_clipboard', True) and PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(text)
                self.logger.info("Automatically copied to clipboard")

                # Auto-paste if enabled (fixed: now uses xdotool directly, no Qt threading issues)
                if self.config.get('auto_paste_mode', False):
                    if self.autopaste_manager.is_available():
                        # Use configurable delay
                        delay_ms = int(self.config.get('auto_paste_delay', 1.0) * 1000)
                        self.logger.info(f"Auto-pasting in {self.config.get('auto_paste_delay', 1.0):.1f} seconds...")
                        self.root.after(delay_ms, lambda: self._perform_auto_paste(text))
                    else:
                        self.logger.warning("Auto-paste not available - text copied to clipboard")

                # Show temporary notification (unless already showing fallback message)
                if not result.get('fallback_success'):
                    self.status_label.configure(text="Copied to clipboard!", foreground="blue")
                    self.root.after(2000, lambda: self.status_label.configure(text="Ready", foreground="green"))

            except Exception as e:
                self.logger.error(f"Auto clipboard copy failed: {e}")
    
    def _perform_auto_paste(self, text: str):
        """Perform auto-paste operation."""
        if self.autopaste_manager.auto_paste(text):
            self.logger.info("Auto-pasted successfully!")
            self.status_label.configure(text="Auto-pasted!", foreground="green")
        else:
            self.logger.warning("Auto-paste failed - use Ctrl+V to paste")
            self.status_label.configure(text="Ready to paste (Ctrl+V)", foreground="orange")
    
    def _copy_to_clipboard(self):
        """Copy current transcription to clipboard."""
        text = self.transcription_text.get("1.0", tk.END).strip()
        if text and PYPERCLIP_AVAILABLE:
            try:
                pyperclip.copy(text)
                self.status_label.configure(text="Copied to clipboard!", foreground="blue")
                self.logger.info("Text copied to clipboard")
                self.root.after(2000, lambda: self.status_label.configure(text="Ready", foreground="green"))
            except Exception as e:
                self.logger.error(f"Clipboard copy failed: {e}")
                messagebox.showerror("Error", f"Clipboard copy failed: {e}")
        elif not PYPERCLIP_AVAILABLE:
            messagebox.showerror("Error", "Pyperclip not available")
        else:
            messagebox.showwarning("Warning", "No text to copy")

    def _open_settings(self):
        """Open simplified settings dialog."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x550")
        settings_window.transient(self.root)
        settings_window.grab_set()

        # Main container
        main_frame = ttk.Frame(settings_window, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Engine selection
        engine_frame = ttk.LabelFrame(main_frame, text="Speech Engine", padding="10")
        engine_frame.pack(fill="x", pady=(0, 15))

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

        # Show engine status
        ttk.Label(engine_frame, text="\nEngine Status:", font=("Arial", 9, "bold")).pack(anchor="w", pady=(10, 5))
        engine_info = self.speech_manager.get_engine_info()
        for name, info in engine_info.items():
            status_icon = "✅" if info['available'] else "❌"
            status_text = f"{status_icon} {name.capitalize()}: {'Available' if info['available'] else 'Not available'}"
            ttk.Label(engine_frame, text=status_text, font=("Arial", 9)).pack(anchor="w")

        # Hotkey configuration
        hotkey_frame = ttk.LabelFrame(main_frame, text="Hotkey", padding="10")
        hotkey_frame.pack(fill="x", pady=(0, 15))

        current_hotkey = self.config.get('hotkey_combination', 'alt+d')
        ttk.Label(hotkey_frame, text=f"Current: {current_hotkey}").pack(anchor="w", pady=(0, 10))

        hotkey_var = tk.StringVar(value=current_hotkey)

        common_hotkeys = [
            ('alt+d', 'Alt+D (recommended)'),
            ('f9', 'F9'),
            ('ctrl+shift+v', 'Ctrl+Shift+V'),
        ]

        for value, label in common_hotkeys:
            ttk.Radiobutton(hotkey_frame, text=label, variable=hotkey_var, value=value).pack(anchor="w")

        # Auto-paste settings
        paste_frame = ttk.LabelFrame(main_frame, text="Auto-paste", padding="10")
        paste_frame.pack(fill="x", pady=(0, 15))

        auto_paste_var = tk.BooleanVar(value=self.config.get('auto_paste_mode', False))
        ttk.Checkbutton(paste_frame, text="Enable auto-paste at cursor",
                       variable=auto_paste_var).pack(anchor="w")

        # Auto-paste status
        if self.autopaste_manager.is_available():
            status_text = f"✅ Available ({self.autopaste_manager.get_method()})"
            status_color = "green"
        else:
            status_text = "⚠️ Not available (install xdotool)"
            status_color = "orange"

        ttk.Label(paste_frame, text=status_text,
                 font=("Arial", 9), foreground=status_color).pack(anchor="w", pady=(5,0))

        # Audio feedback
        audio_frame = ttk.LabelFrame(main_frame, text="Audio Feedback", padding="10")
        audio_frame.pack(fill="x", pady=(0, 15))

        feedback_enabled_var = tk.BooleanVar(value=self.config.get('audio_feedback_enabled', True))
        ttk.Checkbutton(audio_frame, text="Enable audio beeps (start/stop)",
                       variable=feedback_enabled_var).pack(anchor="w")

        # Save button
        def save_settings():
            self.logger.info("Saving settings...")

            # Update speech engine
            new_engine = engine_var.get()
            if new_engine != self.speech_manager.get_current_engine():
                if self.speech_manager.set_engine(new_engine):
                    self.logger.info(f"Engine changed to: {new_engine}")
                else:
                    messagebox.showerror("Error", f"Failed to change engine to: {new_engine}")

            # Update hotkey
            new_hotkey = hotkey_var.get()
            old_hotkey = self.config.get('hotkey_combination', 'alt+d')

            if new_hotkey != old_hotkey:
                success = self.hotkey_manager.register_hotkey(new_hotkey, self._hotkey_callback)
                if success:
                    self.config.set('hotkey_combination', new_hotkey)
                    self.logger.info(f"Hotkey changed to: {new_hotkey}")
                else:
                    hotkey_var.set(old_hotkey)
                    messagebox.showerror("Error", f"Failed to register hotkey: {new_hotkey}")

            # Save settings
            self.config.set('auto_paste_mode', auto_paste_var.get())
            self.config.set('audio_feedback_enabled', feedback_enabled_var.get())

            # Apply audio feedback setting
            self.audio_feedback.set_enabled(feedback_enabled_var.get())

            # Save all settings
            self.config.save()
            self.logger.info("Settings saved")
            settings_window.destroy()

        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(15, 0))

        ttk.Button(button_frame, text="Save",
                   command=save_settings).pack(side="right", padx=(10, 0))
        ttk.Button(button_frame, text="Cancel",
                   command=settings_window.destroy).pack(side="right")

# END OF VoiceTranscriptionApp CLASS