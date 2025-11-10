"""
gui/main_window.py - Main application window for the Voice Transcription Tool.

Implements the main Tkinter GUI with modular integration of audio, speech,
hotkey, and configuration managers.
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
from utils.tray_manager import TrayManager
from utils.error_messages import format_audio_error, format_system_error

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False


class VoiceTranscriptionApp:
    """
    Main application class coordinating all modular components.

    Integrates audio recording, speech recognition, hotkeys, auto-paste,
    and health monitoring through a clean manager-based architecture.
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
        self.speech_manager = SpeechEngineManager(config=self.config.get_all())
        self.hotkey_manager = HotkeyManager()

        # Initialize audio feedback
        self.audio_feedback = AudioFeedback(self.config.get_all())

        # Initialize auto-paste manager
        self.autopaste_manager = AutoPasteManager()

        # Initialize tray manager (must be after GUI is created)
        self.tray_manager = None

        # Load saved engine preference
        saved_engine = self.config.get('current_engine', '')
        if saved_engine and self.speech_manager.is_engine_available(saved_engine):
            self.speech_manager.set_engine(saved_engine)

        # State variables
        self.is_recording = False
        self.recording_start_time = None
        self.shutdown_requested = False  # Flag for clean thread shutdown
        self.banner_pulse_state = False  # For pulsing recording banner animation
        self._is_hiding_to_tray = False  # Flag to prevent recursion when hiding to tray

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

        # Initialize tray manager after GUI is created
        self.tray_manager = TrayManager(self)
        self.tray_manager.start()

        # Initial status log
        self.logger.info(f"Audio method: {self.audio_recorder.get_audio_method()}")
        self.logger.info(f"Speech engine: {self.speech_manager.get_current_engine()}")
        self.logger.info(f"Hotkey: {self.config.get('hotkey_combination', 'alt+d')}")
    
    def _create_gui(self):
        """Create simple single-window GUI."""
        self.root = tk.Tk()
        self.root.title("Voice Transcription Tool")
        self.root.geometry("750x600")  # Increased to show all buttons
        self.root.minsize(650, 550)  # Ensure buttons always visible

        # Configure styling
        style = ttk.Style()
        style.theme_use('clam')

        # Main container
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Recording banner (hidden by default)
        self.recording_banner = tk.Label(
            main_frame,
            text="● RECORDING",
            font=("Arial", 14, "bold"),
            background="#FF0000",
            foreground="white",
            pady=8
        )
        # Don't pack yet - will be shown during recording

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

        # Progress bar (time elapsed)
        self.recording_progress = ttk.Progressbar(main_frame, mode='determinate',
                                                 length=400)
        self.recording_progress.pack(pady=(0, 10))
        self.recording_progress['maximum'] = self.config.get('record_seconds', 30)

        # Audio level meter frame
        meter_frame = ttk.Frame(main_frame)
        meter_frame.pack(fill="x", pady=(0, 10))

        ttk.Label(meter_frame, text="Audio Level:", font=("Arial", 9)).pack(anchor="w")

        # Audio level meter canvas (visual meter with color zones)
        self.audio_level_canvas = tk.Canvas(
            meter_frame,
            height=20,
            background="#E0E0E0",
            highlightthickness=1,
            highlightbackground="#999999"
        )
        self.audio_level_canvas.pack(fill="x", pady=(2, 0))

        # Draw zone markers (low/good/loud thresholds)
        self._draw_audio_meter_zones()

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

        # Keyboard shortcuts hint
        shortcuts_hint = ttk.Label(
            main_frame,
            text="Shortcuts: Ctrl+R (record) | Ctrl+C (copy) | Ctrl+Q (quit) | Esc (stop)",
            font=("Arial", 8),
            foreground="gray"
        )
        shortcuts_hint.pack(pady=(10, 0))

        # Bind close event (hides to tray if available, otherwise quits)
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close_button)

        # Bind minimize event to hide to tray (if tray available)
        self.root.bind('<Unmap>', self._on_window_state_changed)

        # Setup keyboard shortcuts
        self._setup_keyboard_shortcuts()

    def _draw_audio_meter_zones(self):
        """Draw background color zones for audio level meter."""
        # Color zones: low (yellow), good (green), loud (red)
        # RMS thresholds: 0-500 (yellow), 500-5000 (green), 5000+ (red)
        width = 400  # Approximate canvas width
        height = 20

        # Zone boundaries (normalized to 0-10000 RMS scale)
        low_threshold = 0.05  # 500/10000
        good_threshold = 0.5  # 5000/10000

        # Draw zones
        low_x = int(width * low_threshold)
        good_x = int(width * good_threshold)

        self.audio_level_canvas.create_rectangle(
            0, 0, low_x, height,
            fill="#FFD700", outline="", tags="zone"
        )  # Yellow zone
        self.audio_level_canvas.create_rectangle(
            low_x, 0, good_x, height,
            fill="#90EE90", outline="", tags="zone"
        )  # Green zone
        self.audio_level_canvas.create_rectangle(
            good_x, 0, width, height,
            fill="#FFB6C1", outline="", tags="zone"
        )  # Light red zone
    
    def _clear_transcription(self):
        """Clear the transcription display."""
        self.transcription_text.delete("1.0", tk.END)
        self.logger.info("Transcription cleared")
    
    
    
    
    def _setup_keyboard_shortcuts(self):
        """Setup GUI keyboard shortcuts."""
        # Ctrl+R - Toggle recording
        self.root.bind('<Control-r>', lambda e: self._toggle_recording())
        self.root.bind('<Control-R>', lambda e: self._toggle_recording())

        # Ctrl+C - Copy to clipboard (in transcription text area)
        # Note: This is default behavior in ScrolledText, but we add our own too
        self.root.bind('<Control-c>', lambda e: self._copy_to_clipboard() if self.transcription_text.tag_ranges(tk.SEL) == () else None)
        self.root.bind('<Control-C>', lambda e: self._copy_to_clipboard() if self.transcription_text.tag_ranges(tk.SEL) == () else None)

        # Ctrl+Q - Quit application
        self.root.bind('<Control-q>', lambda e: self._on_closing())
        self.root.bind('<Control-Q>', lambda e: self._on_closing())

        # Escape - Stop recording (if active)
        self.root.bind('<Escape>', lambda e: self._stop_recording() if self.is_recording else None)

        self.logger.info("Keyboard shortcuts enabled: Ctrl+R (record), Ctrl+C (copy), Ctrl+Q (quit), Esc (stop)")

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
            # Use format_engine_error for speech engine not available
            from utils.error_messages import format_engine_error
            error_title, error_msg = format_engine_error('not_available')
            self.logger.error("No speech recognition engine available")
            messagebox.showerror(error_title, error_msg)
            return

        if not self.audio_recorder.is_available():
            # Use format_audio_error for audio method not available
            error_title, error_msg = format_audio_error('no_method')
            self.logger.error("No audio recording method available")
            messagebox.showerror(error_title, error_msg)
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

        # Show recording banner
        self.recording_banner.pack(fill="x", pady=(0, 10), before=self.status_label.master)
        self._pulse_recording_banner()

        # Update tray icon and show notification
        if self.tray_manager:
            self.tray_manager.set_recording_state(True)
            self.tray_manager.notify_recording_started()

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

        # Hide recording banner
        self.recording_banner.pack_forget()

        # Update tray icon and show notification
        if self.tray_manager:
            self.tray_manager.set_recording_state(False)
            self.tray_manager.notify_recording_stopped()

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

                # Map error type to formatted error message
                error_type_map = {
                    'silent_audio': 'silent',
                    'device_error': 'device',
                    'no_frames': 'no_frames'
                }
                audio_error_type = error_type_map.get(error_type, 'recording')
                error_title, formatted_msg = format_audio_error(audio_error_type)

                # Show appropriate error message (warning for silent audio, error for others)
                if error_type == 'silent_audio':
                    self.root.after(0, lambda: messagebox.showwarning(error_title, formatted_msg))
                else:
                    self.root.after(0, lambda: messagebox.showerror(error_title, formatted_msg))

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

            # Update audio level meter
            self._update_audio_meter(audio_level)

            # Update tray notifications with audio level
            if self.tray_manager:
                self.tray_manager.update_recording_progress(elapsed_time, audio_level)
    
    def _update_recording_progress(self):
        """Update recording progress bar (fallback when no audio level available)."""
        if self.is_recording and self.recording_start_time:
            elapsed = time.time() - self.recording_start_time
            self._update_progress_bar(elapsed, audio_level=1000)  # Default "good" level

            # Schedule next update
            self.root.after(100, self._update_recording_progress)
    
    def _pulse_recording_banner(self):
        """Animate the recording banner with pulsing effect."""
        if not self.is_recording:
            return

        # Toggle between bright and dark red
        if self.banner_pulse_state:
            self.recording_banner.configure(background="#CC0000")  # Dark red
        else:
            self.recording_banner.configure(background="#FF0000")  # Bright red

        self.banner_pulse_state = not self.banner_pulse_state

        # Schedule next pulse (500ms cycle = 1Hz pulsing)
        self.root.after(500, self._pulse_recording_banner)

    def _update_audio_meter(self, audio_level):
        """Update the visual audio level meter bar."""
        # Clear previous meter bar
        self.audio_level_canvas.delete("meter")

        # Normalize audio level to canvas width (0-10000 RMS → 0-400px)
        canvas_width = self.audio_level_canvas.winfo_width()
        if canvas_width <= 1:  # Canvas not yet rendered
            canvas_width = 400

        # Clamp and scale
        max_rms = 10000
        normalized_level = min(audio_level / max_rms, 1.0)
        bar_width = int(canvas_width * normalized_level)

        # Color code the meter bar
        if audio_level < 500:
            bar_color = "#FFA500"  # Orange (low)
        elif audio_level > 5000:
            bar_color = "#FF0000"  # Red (too loud)
        else:
            bar_color = "#00CC00"  # Green (good)

        # Draw meter bar
        if bar_width > 0:
            self.audio_level_canvas.create_rectangle(
                0, 0, bar_width, 20,
                fill=bar_color, outline="", tags="meter"
            )

    def _reset_recording_ui(self):
        """Reset recording UI state."""
        self.is_recording = False
        self.recording_start_time = None
        self.record_button.configure(text="🎤 Start Recording")
        self.recording_progress['value'] = 0

        # Hide banner and clear audio meter
        self.recording_banner.pack_forget()
        self.audio_level_canvas.delete("meter")
    
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

    def restore_window(self):
        """
        Restore window from minimized/withdrawn state.

        This method properly restores the window by:
        1. Deiconifying (un-minimizing) the window
        2. Lifting it to the top of the window stack
        3. Forcing focus to ensure it's active

        Called by tray icon's "Show Window" action.
        """
        try:
            self.root.deiconify()  # Restore from minimized/withdrawn state
            self.root.lift()  # Bring window to front
            self.root.focus_force()  # Force focus to window
            self.logger.debug("Window restored from tray")
        except Exception as e:
            self.logger.error(f"Error restoring window: {e}")

    def hide_to_tray(self):
        """
        Hide window to system tray.

        Completely withdraws the window (not just minimize to taskbar).
        This is the proper system tray behavior like Dropbox/NoMachine.

        Called when:
        - User clicks [X] close button (if tray mode enabled)
        - User clicks minimize button (if tray mode enabled)
        - User selects "Hide Window" from tray menu
        """
        try:
            self._is_hiding_to_tray = True
            self.root.withdraw()  # Completely hide window
            self.logger.debug("Window hidden to tray")
        except Exception as e:
            self.logger.error(f"Error hiding window to tray: {e}")
        finally:
            # Reset flag after a short delay
            self.root.after(100, lambda: setattr(self, '_is_hiding_to_tray', False))

    def _on_window_close_button(self):
        """
        Handle window close button ([X]) click.

        Behavior depends on tray availability:
        - If tray available: Hide to tray (like Dropbox/NoMachine)
        - If no tray: Quit application normally

        This enables true system tray behavior where [X] doesn't quit.
        """
        if self.tray_manager and self.tray_manager.is_available():
            # Tray mode: hide window instead of quitting
            self.logger.info("Close button clicked - hiding to tray")
            self.hide_to_tray()
        else:
            # Normal mode: quit application
            self.logger.info("Close button clicked - quitting application")
            self._on_closing()

    def _on_window_state_changed(self, event=None):
        """
        Handle window state changes (iconify/minimize).

        If window is minimized and tray is available, hide to tray instead.
        Uses a short delay to avoid race conditions with the iconify event.
        """
        if not self._is_hiding_to_tray and self.tray_manager and self.tray_manager.is_available():
            # Check state after a short delay to avoid race conditions
            self.root.after(10, self._check_and_hide_if_iconified)

    def _check_and_hide_if_iconified(self):
        """
        Check if window is iconified (minimized) and hide to tray if so.

        This is called after a delay from _on_window_state_changed to ensure
        the window state has stabilized.
        """
        try:
            if not self._is_hiding_to_tray and self.root.state() == 'iconic':
                self.logger.info("Window minimized - hiding to tray")
                self.hide_to_tray()
        except Exception as e:
            # Ignore errors (window might be destroyed)
            pass

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

        # Stop tray icon
        if hasattr(self, 'tray_manager') and self.tray_manager:
            self.tray_manager.stop()

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
            # Get user-friendly formatted error message
            error_title, error_message = self.speech_manager.format_transcription_error(result)

            # Display error to user
            messagebox.showerror(error_title, error_message)

            # Show tray notification for failure
            if self.tray_manager and self.tray_manager.is_available():
                self.tray_manager.notify_transcription_complete("", success=False)

            # Log technical error details
            error_msg = result.get('error', 'Transcription failed')
            self.logger.error(f"Transcription failed: {error_msg}")
            return

        # Transcription succeeded
        text = result.get('text', '').strip()

        if not text:
            self.logger.warning("Transcription returned empty text")
            messagebox.showwarning("Empty Result", "Transcription completed but no text was detected.")
            return

        # Show tray notification with transcribed text
        if self.tray_manager and self.tray_manager.is_available():
            self.tray_manager.notify_transcription_complete(text, success=True)

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
        """Perform auto-paste operation with clear feedback."""
        result = self.autopaste_manager.auto_paste(text)

        if result.get('success'):
            # Paste succeeded
            method = result.get('method', 'unknown')
            window = result.get('window', '')

            if window:
                self.logger.info(f"Auto-pasted successfully to: {window}")
                # Show brief confirmation
                self.status_label.configure(text=f"✓ Pasted to {window[:30]}...", foreground="green")
            else:
                self.logger.info(f"Auto-pasted successfully using {method}")
                self.status_label.configure(text=f"✓ Text pasted", foreground="green")

            # Reset status after 2 seconds
            self.root.after(2000, lambda: self.status_label.configure(text="Ready", foreground="green"))
        else:
            # Paste failed
            error_msg = result.get('error', 'Auto-paste failed')
            method = result.get('method', 'unknown')

            self.logger.warning(f"Auto-paste failed ({method}): {error_msg}")

            # Show error with manual paste instruction
            self.status_label.configure(
                text="⚠ Auto-paste failed - Press Ctrl+V to paste",
                foreground="orange"
            )

            # Reset status after 4 seconds (longer for error)
            self.root.after(4000, lambda: self.status_label.configure(text="Ready", foreground="green"))
    
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
        """Open simplified settings dialog with auto-save."""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x600")
        settings_window.transient(self.root)
        settings_window.grab_set()

        # Main container
        main_frame = ttk.Frame(settings_window, padding="20")
        main_frame.pack(fill="both", expand=True)

        # Status label at the top for feedback
        status_label = ttk.Label(main_frame, text="", font=("Arial", 9))
        status_label.pack(anchor="w", pady=(0, 10))

        # Helper function to show status messages
        def show_status(message, color="green"):
            """Display status message for 2 seconds then clear."""
            status_label.configure(text=message, foreground=color)
            settings_window.after(2000, lambda: status_label.configure(text=""))

        # Auto-save helper functions
        def _change_engine():
            """Auto-save engine selection."""
            new_engine = engine_var.get()
            if new_engine != self.speech_manager.get_current_engine():
                if self.speech_manager.set_engine(new_engine):
                    self.config.set('current_engine', new_engine)
                    self.config.save()
                    self.logger.info(f"Engine changed to: {new_engine}")
                    show_status(f"✓ Engine changed to {new_engine.capitalize()}")
                else:
                    self.logger.error(f"Failed to change engine to: {new_engine}")
                    show_status(f"✗ Failed to change engine", "red")

        def _change_hotkey():
            """Auto-save hotkey change."""
            new_hotkey = hotkey_var.get()
            old_hotkey = self.config.get('hotkey_combination', 'alt+d')

            if new_hotkey != old_hotkey:
                success = self.hotkey_manager.register_hotkey(new_hotkey, self._hotkey_callback)
                if success:
                    self.config.set('hotkey_combination', new_hotkey)
                    self.config.save()
                    self.logger.info(f"Hotkey changed to: {new_hotkey}")
                    show_status(f"✓ Hotkey changed to {new_hotkey}")
                else:
                    hotkey_var.set(old_hotkey)
                    self.logger.error(f"Failed to register hotkey: {new_hotkey}")
                    show_status(f"✗ Failed to register hotkey", "red")

        def _toggle_autopaste():
            """Auto-save auto-paste toggle."""
            enabled = auto_paste_var.get()
            self.config.set('auto_paste_mode', enabled)
            self.config.save()
            self.logger.info(f"Auto-paste {'enabled' if enabled else 'disabled'}")
            show_status(f"✓ Auto-paste {'enabled' if enabled else 'disabled'}")

        def _toggle_audio_feedback():
            """Auto-save audio feedback toggle."""
            enabled = feedback_enabled_var.get()
            self.config.set('audio_feedback_enabled', enabled)
            self.audio_feedback.set_enabled(enabled)
            self.config.save()
            self.logger.info(f"Audio feedback {'enabled' if enabled else 'disabled'}")
            show_status(f"✓ Audio feedback {'enabled' if enabled else 'disabled'}")

        def _reset_to_defaults():
            """Reset all settings to defaults with confirmation."""
            if messagebox.askyesno("Reset Settings",
                                   "Reset all settings to defaults?\n\n" +
                                   "• Engine: Whisper\n" +
                                   "• Hotkey: Alt+D\n" +
                                   "• Auto-paste: Disabled\n" +
                                   "• Audio feedback: Enabled"):
                # Reset engine
                engine_var.set("whisper")
                _change_engine()

                # Reset hotkey
                hotkey_var.set("alt+d")
                _change_hotkey()

                # Reset auto-paste
                auto_paste_var.set(False)
                _toggle_autopaste()

                # Reset audio feedback
                feedback_enabled_var.set(True)
                _toggle_audio_feedback()

                show_status("✓ All settings reset to defaults")

        # Engine selection
        engine_frame = ttk.LabelFrame(main_frame, text="Speech Engine", padding="10")
        engine_frame.pack(fill="x", pady=(0, 15))

        current_engine = self.speech_manager.get_current_engine() or ''
        engine_var = tk.StringVar(value=current_engine)

        available_engines = self.speech_manager.get_available_engines()

        for engine in available_engines:
            if engine == 'faster-whisper':
                ttk.Radiobutton(engine_frame, text="Faster-Whisper (Local, GPU-Accelerated)",
                                variable=engine_var, value="faster-whisper",
                                command=_change_engine).pack(anchor="w")
            elif engine == 'whisper':
                ttk.Radiobutton(engine_frame, text="Whisper (Local, HQ Mode)",
                                variable=engine_var, value="whisper",
                                command=_change_engine).pack(anchor="w")
            elif engine == 'google':
                ttk.Radiobutton(engine_frame, text="Google Speech Recognition (Online)",
                                variable=engine_var, value="google",
                                command=_change_engine).pack(anchor="w")

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

        # Model size selector (for Whisper engines)
        model_frame = ttk.LabelFrame(main_frame, text="Whisper Model Size", padding="10")
        model_frame.pack(fill="x", pady=(0, 15))

        def _change_model_size():
            """Auto-save model size change and reload model."""
            new_model_size = model_var.get()
            old_model_size = self.config.get('whisper_model_size', 'base')

            if new_model_size != old_model_size:
                # Show loading dialog
                loading_dialog = tk.Toplevel(settings_window)
                loading_dialog.title("Loading Model")
                loading_dialog.geometry("400x150")
                loading_dialog.transient(settings_window)
                loading_dialog.grab_set()

                loading_frame = ttk.Frame(loading_dialog, padding="20")
                loading_frame.pack(fill="both", expand=True)

                ttk.Label(loading_frame, 
                         text=f"Loading {new_model_size} model...",
                         font=("Arial", 11)).pack(pady=(10, 20))
                
                progress_bar = ttk.Progressbar(loading_frame, mode='indeterminate', length=300)
                progress_bar.pack(pady=10)
                progress_bar.start(10)

                status_var = tk.StringVar(value="Initializing...")
                status_lbl = ttk.Label(loading_frame, textvariable=status_var, 
                                      font=("Arial", 9), foreground="gray")
                status_lbl.pack(pady=5)

                def reload_model():
                    """Reload models in background thread."""
                    try:
                        status_var.set("Saving configuration...")
                        self.config.set('whisper_model_size', new_model_size)
                        self.config.save()

                        status_var.set(f"Loading {new_model_size} model...")
                        # Reinitialize speech manager with new model size
                        self.speech_manager = SpeechEngineManager(config=self.config.get_all())
                        
                        self.logger.info(f"Model size changed to: {new_model_size}")
                        
                        # Close loading dialog on main thread
                        self.root.after(0, loading_dialog.destroy)
                        self.root.after(0, lambda: show_status(f"✓ Model changed to {new_model_size}"))
                    except Exception as e:
                        self.logger.error(f"Failed to reload model: {e}")
                        self.root.after(0, loading_dialog.destroy)
                        self.root.after(0, lambda: show_status(f"✗ Failed to reload model", "red"))
                        # Revert to old model size
                        self.root.after(0, lambda: model_var.set(old_model_size))

                # Start reload in background thread
                import threading
                threading.Thread(target=reload_model, daemon=True).start()

        current_model = self.config.get('whisper_model_size', 'base')
        model_var = tk.StringVar(value=current_model)

        ttk.Label(model_frame, text="Choose model size (speed vs accuracy trade-off):",
                 font=("Arial", 9)).pack(anchor="w", pady=(0, 10))

        model_options = [
            ('tiny', 'Tiny - Fastest, lowest quality (~1-2s for 30s audio)'),
            ('base', 'Base - Balanced, recommended (~3-5s for 30s audio)'),
            ('small', 'Small - Better quality (~8-12s for 30s audio)'),
            ('medium', 'Medium - High quality (~25-35s for 30s audio)'),
            ('large', 'Large - Best quality (~60-90s for 30s audio)')
        ]

        for value, label in model_options:
            ttk.Radiobutton(model_frame, text=label, variable=model_var, value=value,
                           command=_change_model_size).pack(anchor="w")

        # Note about GPU acceleration
        current_engine = engine_var.get()
        if current_engine in ['whisper', 'faster-whisper']:
            gpu_note = "\n💡 With GPU: Times are 3-5x faster"
        else:
            gpu_note = "\n⚠️ Model size applies to Whisper engines only"
        
        ttk.Label(model_frame, text=gpu_note,
                 font=("Arial", 8), foreground="gray").pack(anchor="w", pady=(5, 0))

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
            ttk.Radiobutton(hotkey_frame, text=label, variable=hotkey_var, value=value,
                           command=_change_hotkey).pack(anchor="w")

        # Auto-paste settings
        paste_frame = ttk.LabelFrame(main_frame, text="Auto-paste", padding="10")
        paste_frame.pack(fill="x", pady=(0, 15))

        auto_paste_var = tk.BooleanVar(value=self.config.get('auto_paste_mode', False))
        ttk.Checkbutton(paste_frame, text="Enable auto-paste at cursor",
                       variable=auto_paste_var,
                       command=_toggle_autopaste).pack(anchor="w")

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
                       variable=feedback_enabled_var,
                       command=_toggle_audio_feedback).pack(anchor="w")

        # Bottom buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill="x", pady=(15, 0))

        ttk.Button(button_frame, text="Reset to Defaults",
                   command=_reset_to_defaults).pack(side="left")
        ttk.Button(button_frame, text="Close",
                   command=settings_window.destroy).pack(side="right")

# END OF VoiceTranscriptionApp CLASS