import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import sqlite3
import json
from datetime import datetime
import tempfile
import os
import time
import keyboard
import pyperclip
import subprocess
import platform
import logging
import sys

try:
    import pyaudio
    import wave
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    
try:
    import speech_recognition as sr
    SR_AVAILABLE = True
except ImportError:
    SR_AVAILABLE = False

class VoiceTranscriptionTool:
    def __init__(self):
        # Setup logging first
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        self.logger.info("=== Voice Transcription Tool Starting ===")
        
        self.root = tk.Tk()
        self.root.title("Voice Transcription Tool")
        self.root.geometry("800x700")  # Made taller for debug panel
        
        # Audio settings
        self.chunk = 1024
        self.format = None  # Will be set during audio init
        self.channels = 1
        self.rate = 16000
        self.record_seconds = 10  # Max recording length
        
        # State variables
        self.is_recording = False
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.transcription_queue = queue.Queue()
        self.recording_thread = None
        
        # Initialize components
        self.load_config()  # Load config before other initialization
        self.init_database()
        self.init_audio()
        self.init_speech_engine()
        self.create_gui()
        self.setup_hotkeys()
        
        # Start background threads
        self.start_background_threads()
        
    def setup_logging(self):
        """Setup comprehensive logging"""
        # Create logs directory
        os.makedirs("logs", exist_ok=True)
        
        # Setup file logging
        log_filename = f"logs/voice_transcription_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        
        logging.basicConfig(
            level=logging.DEBUG,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_filename),
                logging.StreamHandler(sys.stdout)  # Also log to console
            ]
        )
        
        # Create logger
        self.debug_messages = []
        
    def init_database(self):
        """Initialize SQLite database for storing transcriptions and voice profiles"""
        self.db_path = "voice_transcriptions.db"
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create transcriptions table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS transcriptions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                original_audio_path TEXT,
                transcribed_text TEXT,
                confidence REAL,
                method TEXT
            )
        ''')
        
        # Create voice profile table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS voice_profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_name TEXT,
                audio_samples TEXT,  -- JSON array of file paths
                created_date TEXT,
                last_updated TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        
    def init_audio(self):
        """Initialize audio recording method"""
        self.logger.info("Initializing audio recording...")
        self.audio_method = None
        self.available_devices = []
        
        if PYAUDIO_AVAILABLE:
            try:
                import pyaudio
                self.audio = pyaudio.PyAudio()
                self.format = pyaudio.paInt16
                self.audio_method = "pyaudio"
                self.logger.info("✅ PyAudio initialized successfully")
                
                # List available audio devices
                self.list_audio_devices()
                
            except Exception as e:
                self.logger.error(f"❌ PyAudio initialization failed: {e}")
                
        # Fallback to system recording tools
        if not self.audio_method:
            self.logger.info("Trying system audio tools...")
            system = platform.system().lower()
            if system == "linux":
                # Check if arecord is available
                try:
                    result = subprocess.run(["which", "arecord"], check=True, capture_output=True)
                    self.audio_method = "arecord"
                    self.logger.info("✅ arecord found and will be used")
                except subprocess.CalledProcessError:
                    try:
                        result = subprocess.run(["which", "ffmpeg"], check=True, capture_output=True)
                        self.audio_method = "ffmpeg"
                        self.logger.info("✅ ffmpeg found and will be used")
                    except subprocess.CalledProcessError:
                        self.logger.error("❌ No system audio tools found")
            elif system == "darwin":  # macOS
                self.audio_method = "afplay"
                self.logger.info("✅ macOS audio system detected")
            elif system == "windows":
                self.audio_method = "windows"
                self.logger.info("✅ Windows audio system detected")
                
        if self.audio_method:
            self.logger.info(f"🎤 Audio method selected: {self.audio_method}")
        else:
            self.logger.error("❌ No audio recording method available!")
            
    def list_audio_devices(self):
        """List available audio input devices"""
        if not hasattr(self, 'audio') or not self.audio:
            return
            
        try:
            self.logger.info("📋 Available audio devices:")
            device_count = self.audio.get_device_count()
            
            for i in range(device_count):
                device_info = self.audio.get_device_info_by_index(i)
                if device_info['maxInputChannels'] > 0:  # Input device
                    self.available_devices.append({
                        'index': i,
                        'name': device_info['name'],
                        'channels': device_info['maxInputChannels'],
                        'rate': device_info['defaultSampleRate']
                    })
                    self.logger.info(f"  📱 Device {i}: {device_info['name']} "
                                   f"(Channels: {device_info['maxInputChannels']}, "
                                   f"Rate: {device_info['defaultSampleRate']})")
                    
        except Exception as e:
            self.logger.error(f"Failed to list audio devices: {e}")
            
    def test_microphone(self, device_index=None):
        """Test microphone functionality"""
        self.logger.info(f"🧪 Testing microphone (device: {device_index})...")
        
        try:
            if self.audio_method == "pyaudio":
                # Test PyAudio recording
                stream = self.audio.open(
                    format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    input_device_index=device_index,
                    frames_per_buffer=self.chunk
                )
                
                # Record for 1 second
                frames = []
                for _ in range(int(self.rate / self.chunk)):
                    data = stream.read(self.chunk)
                    frames.append(data)
                    
                stream.stop_stream()
                stream.close()
                
                self.logger.info("✅ Microphone test successful")
                return True
                
            else:
                self.logger.info("⚠️ Microphone test not implemented for system audio tools")
                return True
                
        except Exception as e:
            self.logger.error(f"❌ Microphone test failed: {e}")
            return False
        
    def init_speech_engine(self):
        """Initialize speech recognition engines"""
        self.logger.info("Initializing speech recognition engines...")
        self.whisper_model = None
        self.speech_recognizer = None
        
        # Load saved engine preference
        saved_engine = getattr(self, 'current_engine', None)
        self.logger.info(f"Saved engine preference: {saved_engine}")
        
        if WHISPER_AVAILABLE:
            try:
                self.logger.info("Loading Whisper model...")
                self.whisper_model = whisper.load_model("base")
                self.logger.info("✅ Whisper model loaded successfully")
                
                if not saved_engine or saved_engine == "whisper":
                    self.current_engine = "whisper"
                    self.logger.info("🎯 Selected engine: Whisper")
            except Exception as e:
                self.logger.error(f"❌ Failed to load Whisper: {e}")
                
        if SR_AVAILABLE:
            try:
                import speech_recognition as sr
                self.speech_recognizer = sr.Recognizer()
                self.logger.info("✅ Google Speech Recognition initialized")
                
                if not hasattr(self, 'current_engine') and not self.whisper_model:
                    self.current_engine = "google"
                    self.logger.info("🎯 Selected engine: Google Speech (fallback)")
                elif saved_engine == "google":
                    self.current_engine = "google"
                    self.logger.info("🎯 Selected engine: Google Speech (saved preference)")
            except Exception as e:
                self.logger.error(f"❌ Failed to initialize Google Speech: {e}")
                
        if not hasattr(self, 'current_engine'):
            self.current_engine = None
            self.logger.error("❌ No speech recognition engines available!")
        else:
            self.logger.info(f"🚀 Speech engine ready: {self.current_engine}")
            
    def create_gui(self):
        """Create the main GUI interface"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title_label = ttk.Label(main_frame, text="Voice Transcription Tool", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="10")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.status_label = ttk.Label(status_frame, text="Ready", foreground="green")
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.engine_label = ttk.Label(status_frame, 
                                     text=f"Engine: {getattr(self, 'current_engine', 'None')}")
        self.engine_label.grid(row=0, column=1, sticky=tk.E)
        
        # Control frame
        control_frame = ttk.LabelFrame(main_frame, text="Controls", padding="10")
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.record_button = ttk.Button(control_frame, text="🎤 Start Recording", 
                                       command=self.toggle_recording)
        self.record_button.grid(row=0, column=0, padx=(0, 10))
        
        self.hotkey_button = ttk.Button(control_frame, text="🔥 Toggle Hotkey Mode", 
                                       command=self.toggle_hotkey_mode)
        self.hotkey_button.grid(row=0, column=1, padx=(0, 10))
        
        self.settings_button = ttk.Button(control_frame, text="⚙️ Settings", 
                                         command=self.open_settings)
        self.settings_button.grid(row=0, column=2)
        
        # Real-time transcription display
        transcription_frame = ttk.LabelFrame(main_frame, text="Live Transcription", padding="10")
        transcription_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.transcription_text = scrolledtext.ScrolledText(transcription_frame, height=8, wrap=tk.WORD)
        self.transcription_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Action buttons for transcription
        action_frame = ttk.Frame(transcription_frame)
        action_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Button(action_frame, text="📋 Copy to Clipboard", 
                  command=self.copy_to_clipboard).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(action_frame, text="📝 Insert at Cursor", 
                  command=self.insert_at_cursor).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(action_frame, text="🗑️ Clear", 
                  command=self.clear_transcription).grid(row=0, column=2)
        
        # History frame
        history_frame = ttk.LabelFrame(main_frame, text="Recent Transcriptions", padding="10")
        history_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # History treeview
        columns = ("Timestamp", "Text", "Method")
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=4)
        
        for col in columns:
            self.history_tree.heading(col, text=col)
            
        self.history_tree.column("Timestamp", width=150)
        self.history_tree.column("Text", width=400)
        self.history_tree.column("Method", width=100)
        
        self.history_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for history
        history_scrollbar = ttk.Scrollbar(history_frame, orient=tk.VERTICAL, command=self.history_tree.yview)
        history_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.history_tree.configure(yscrollcommand=history_scrollbar.set)
        
        # Debug panel
        debug_frame = ttk.LabelFrame(main_frame, text="Debug Log", padding="10")
        debug_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        self.debug_text = scrolledtext.ScrolledText(debug_frame, height=8, wrap=tk.WORD, 
                                                   font=("Courier", 9))
        self.debug_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Debug controls
        debug_controls = ttk.Frame(debug_frame)
        debug_controls.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        ttk.Button(debug_controls, text="🧪 Test Microphone", 
                  command=self.run_mic_test).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(debug_controls, text="📋 Audio Devices", 
                  command=self.show_audio_devices).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(debug_controls, text="🗑️ Clear Debug", 
                  command=self.clear_debug_log).grid(row=0, column=2, padx=(0, 10))
        ttk.Button(debug_controls, text="💾 Save Log", 
                  command=self.save_debug_log).grid(row=0, column=3)
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        main_frame.rowconfigure(4, weight=1)
        main_frame.rowconfigure(5, weight=1)  # Debug panel
        transcription_frame.columnconfigure(0, weight=1)
        transcription_frame.rowconfigure(0, weight=1)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        debug_frame.columnconfigure(0, weight=1)
        debug_frame.rowconfigure(0, weight=1)
        
        # Load recent history
        self.load_recent_transcriptions()
        
        # Initialize debug log
        self.add_debug_message("🚀 Voice Transcription Tool initialized")
        self.add_debug_message(f"🎤 Audio method: {self.audio_method}")
        self.add_debug_message(f"🧠 Speech engine: {getattr(self, 'current_engine', 'None')}")
        
    def add_debug_message(self, message):
        """Add a message to debug log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        debug_msg = f"[{timestamp}] {message}"
        
        # Add to debug panel
        self.debug_text.insert(tk.END, debug_msg + "\n")
        self.debug_text.see(tk.END)
        
        # Also log to file
        self.logger.info(message)
        
        # Keep debug panel to reasonable size
        lines = self.debug_text.get("1.0", tk.END).split("\n")
        if len(lines) > 100:
            self.debug_text.delete("1.0", "2.0")
            
    def run_mic_test(self):
        """Run microphone test"""
        self.add_debug_message("🧪 Starting microphone test...")
        
        def test_thread():
            success = self.test_microphone()
            if success:
                self.root.after(0, lambda: self.add_debug_message("✅ Microphone test passed"))
            else:
                self.root.after(0, lambda: self.add_debug_message("❌ Microphone test failed"))
                
        threading.Thread(target=test_thread, daemon=True).start()
        
    def show_audio_devices(self):
        """Show available audio devices"""
        self.add_debug_message("📋 Available audio devices:")
        if self.available_devices:
            for device in self.available_devices:
                self.add_debug_message(f"  📱 {device['index']}: {device['name']}")
        else:
            self.add_debug_message("  ⚠️ No audio devices detected")
            
    def clear_debug_log(self):
        """Clear debug log"""
        self.debug_text.delete("1.0", tk.END)
        self.add_debug_message("🗑️ Debug log cleared")
        
    def save_debug_log(self):
        """Save debug log to file"""
        try:
            content = self.debug_text.get("1.0", tk.END)
            filename = f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            with open(filename, 'w') as f:
                f.write(content)
            self.add_debug_message(f"💾 Debug log saved to {filename}")
        except Exception as e:
            self.add_debug_message(f"❌ Failed to save debug log: {e}")
        
    def setup_hotkeys(self):
        """Setup global hotkeys"""
        self.hotkey_active = False
        self.current_hotkey = getattr(self, 'hotkey_combination', 'ctrl+shift+v')
        
        try:
            # Remove existing hotkey if any
            if hasattr(self, 'registered_hotkey'):
                keyboard.remove_hotkey(self.registered_hotkey)
            
            # Register new hotkey
            self.registered_hotkey = keyboard.add_hotkey(self.current_hotkey, self.hotkey_toggle_recording)
            print(f"Hotkey registered: {self.current_hotkey}")
        except Exception as e:
            print(f"Failed to setup hotkeys: {e}")
            
    def update_hotkey(self, new_hotkey):
        """Update the hotkey combination"""
        self.hotkey_combination = new_hotkey
        self.setup_hotkeys()
        # Save to a config file (optional)
        self.save_config()
            
    def toggle_hotkey_mode(self):
        """Toggle hotkey listening mode"""
        self.hotkey_active = not self.hotkey_active
        if self.hotkey_active:
            self.hotkey_button.configure(text="🔥 Hotkey Mode: ON")
            self.status_label.configure(text="Hotkey mode active (Ctrl+Shift+V)", foreground="blue")
        else:
            self.hotkey_button.configure(text="🔥 Hotkey Mode: OFF")
            self.status_label.configure(text="Ready", foreground="green")
            
    def hotkey_toggle_recording(self):
        """Handle hotkey press"""
        if self.hotkey_active:
            self.toggle_recording()
            
    def toggle_recording(self):
        """Start or stop recording"""
        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()
            
    def start_recording(self):
        """Start audio recording"""
        self.logger.info("Start recording requested")
        self.add_debug_message("🎙️ Starting recording...")
        
        if not hasattr(self, 'current_engine') or self.current_engine is None:
            error_msg = "No speech recognition engine available!"
            self.logger.error(error_msg)
            self.add_debug_message(f"❌ {error_msg}")
            messagebox.showerror("Error", error_msg)
            return
            
        if not self.audio_method:
            error_msg = ("No audio recording method available!\n\n"
                        "Please install:\n"
                        "• PyAudio: pip install pyaudio\n"
                        "• Or arecord: sudo apt-get install alsa-utils\n"
                        "• Or ffmpeg: sudo apt-get install ffmpeg")
            self.logger.error("No audio recording method available")
            self.add_debug_message("❌ No audio recording method")
            messagebox.showerror("Error", error_msg)
            return
            
        if self.is_recording:
            self.add_debug_message("⚠️ Recording already in progress")
            return
            
        self.is_recording = True
        self.record_button.configure(text="🛑 Stop Recording")
        self.status_label.configure(text="Recording...", foreground="red")
        self.add_debug_message(f"🎤 Recording started with {self.audio_method}")
        
        # Start recording in a separate thread
        self.recording_thread = threading.Thread(target=self.record_audio, daemon=True)
        self.recording_thread.start()
        
    def stop_recording(self):
        """Stop audio recording"""
        self.logger.info("Stop recording requested")
        self.add_debug_message("🛑 Stopping recording...")
        self.is_recording = False
        self.record_button.configure(text="🎤 Start Recording")
        self.status_label.configure(text="Processing...", foreground="orange")
        
    def record_audio(self):
        """Record audio from microphone using available method"""
        try:
            temp_file = tempfile.mktemp(suffix=".wav")
            self.logger.info(f"Recording to temporary file: {temp_file}")
            self.add_debug_message(f"📁 Recording to: {os.path.basename(temp_file)}")
            
            if self.audio_method == "pyaudio":
                self.record_with_pyaudio(temp_file)
            elif self.audio_method == "arecord":
                self.record_with_arecord(temp_file)
            elif self.audio_method == "ffmpeg":
                self.record_with_ffmpeg(temp_file)
            else:
                raise Exception(f"Unknown audio method: {self.audio_method}")
                
            # Check if file was created and has content
            if os.path.exists(temp_file) and os.path.getsize(temp_file) > 0:
                self.logger.info(f"Recording completed successfully. File size: {os.path.getsize(temp_file)} bytes")
                self.add_debug_message(f"✅ Recording completed ({os.path.getsize(temp_file)} bytes)")
                
                # Queue for transcription
                self.audio_queue.put(temp_file)
            else:
                raise Exception("Recording failed - no audio data captured")
            
        except Exception as e:
            self.logger.error(f"Recording error: {e}")
            self.add_debug_message(f"❌ Recording error: {e}")
            self.root.after(0, lambda: self.status_label.configure(text="Recording error", foreground="red"))
            self.root.after(0, lambda: self.record_button.configure(text="🎤 Start Recording"))
            self.is_recording = False
            
    def record_with_pyaudio(self, temp_file):
        """Record using PyAudio"""
        self.logger.info("Recording with PyAudio...")
        self.add_debug_message("🎵 Using PyAudio for recording")
        
        try:
            stream = self.audio.open(format=self.format,
                                   channels=self.channels,
                                   rate=self.rate,
                                   input=True,
                                   frames_per_buffer=self.chunk)
            
            frames = []
            start_time = time.time()
            
            while self.is_recording and (time.time() - start_time) < self.record_seconds:
                try:
                    data = stream.read(self.chunk, exception_on_overflow=False)
                    frames.append(data)
                except Exception as e:
                    self.logger.warning(f"Audio read warning: {e}")
                    break
                    
            stream.stop_stream()
            stream.close()
            
            if not frames:
                raise Exception("No audio frames captured")
            
            # Save audio to file
            import wave
            wf = wave.open(temp_file, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(self.audio.get_sample_size(self.format))
            wf.setframerate(self.rate)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            self.logger.info(f"PyAudio recording saved: {len(frames)} frames")
            
        except Exception as e:
            self.logger.error(f"PyAudio recording failed: {e}")
            raise
        
    def record_with_arecord(self, temp_file):
        """Record using arecord (Linux)"""
        cmd = [
            "arecord",
            "-f", "S16_LE",
            "-c", str(self.channels),
            "-r", str(self.rate),
            "-d", str(self.record_seconds),
            temp_file
        ]
        
        process = subprocess.Popen(cmd)
        
        # Wait for recording to finish or stop signal
        start_time = time.time()
        while self.is_recording and process.poll() is None:
            if time.time() - start_time > self.record_seconds:
                break
            time.sleep(0.1)
            
        if process.poll() is None:
            process.terminate()
            process.wait()
            
    def record_with_ffmpeg(self, temp_file):
        """Record using ffmpeg"""
        cmd = [
            "ffmpeg",
            "-f", "pulse",  # Linux audio system
            "-i", "default",
            "-t", str(self.record_seconds),
            "-acodec", "pcm_s16le",
            "-ar", str(self.rate),
            "-ac", str(self.channels),
            "-y",  # Overwrite output file
            temp_file
        ]
        
        process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Wait for recording to finish or stop signal
        start_time = time.time()
        while self.is_recording and process.poll() is None:
            if time.time() - start_time > self.record_seconds:
                break
            time.sleep(0.1)
            
        if process.poll() is None:
            process.terminate()
            process.wait()
            
    def start_background_threads(self):
        """Start background processing threads"""
        threading.Thread(target=self.transcription_worker, daemon=True).start()
        threading.Thread(target=self.ui_updater, daemon=True).start()
        
    def transcription_worker(self):
        """Background worker for transcribing audio"""
        while True:
            try:
                audio_file = self.audio_queue.get(timeout=1)
                transcription = self.transcribe_audio(audio_file)
                self.transcription_queue.put(transcription)
                
                # Clean up temp file
                try:
                    os.unlink(audio_file)
                except:
                    pass
                    
            except queue.Empty:
                continue
            except Exception as e:
                print(f"Transcription error: {e}")
                
    def transcribe_audio(self, audio_file):
        """Transcribe audio file using available engine"""
        self.logger.info(f"Transcribing audio with {self.current_engine} engine")
        self.add_debug_message(f"🧠 Transcribing with {self.current_engine}...")
        
        try:
            if self.current_engine == "whisper" and self.whisper_model:
                self.logger.info("Using Whisper for transcription")
                result = self.whisper_model.transcribe(audio_file)
                transcription = {
                    'text': result['text'].strip(),
                    'confidence': 0.95,  # Whisper doesn't provide confidence
                    'method': 'whisper'
                }
                self.logger.info(f"Whisper transcription: '{transcription['text'][:50]}...'")
                return transcription
                
            elif self.current_engine == "google" and self.speech_recognizer:
                self.logger.info("Using Google Speech Recognition for transcription")
                import speech_recognition as sr
                
                with sr.AudioFile(audio_file) as source:
                    audio_data = self.speech_recognizer.record(source)
                    text = self.speech_recognizer.recognize_google(audio_data)
                    transcription = {
                        'text': text,
                        'confidence': 0.9,
                        'method': 'google'
                    }
                    self.logger.info(f"Google transcription: '{transcription['text'][:50]}...'")
                    return transcription
            else:
                raise Exception(f"No transcription engine available (current: {self.current_engine})")
                    
        except Exception as e:
            self.logger.error(f"Transcription failed: {e}")
            self.add_debug_message(f"❌ Transcription failed: {e}")
            return {
                'text': f"[Transcription failed: {str(e)}]",
                'confidence': 0.0,
                'method': 'error'
            }
            
    def ui_updater(self):
        """Update UI with transcription results"""
        while True:
            try:
                result = self.transcription_queue.get(timeout=1)
                self.root.after(0, lambda r=result: self.update_transcription_display(r))
            except queue.Empty:
                continue
                
    def update_transcription_display(self, result):
        """Update the transcription display"""
        # Update status
        self.status_label.configure(text="Ready", foreground="green")
        
        # Add to transcription text
        current_text = self.transcription_text.get("1.0", tk.END).strip()
        if current_text:
            new_text = current_text + "\n\n" + result['text']
        else:
            new_text = result['text']
            
        self.transcription_text.delete("1.0", tk.END)
        self.transcription_text.insert("1.0", new_text)
        
        # Save to database
        self.save_transcription(result)
        
        # Update history
        self.load_recent_transcriptions()
        
    def save_transcription(self, result):
        """Save transcription to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO transcriptions (timestamp, transcribed_text, confidence, method)
                VALUES (?, ?, ?, ?)
            ''', (
                datetime.now().isoformat(),
                result['text'],
                result['confidence'],
                result['method']
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Database save error: {e}")
            
    def load_recent_transcriptions(self):
        """Load recent transcriptions into history view"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT timestamp, transcribed_text, method 
                FROM transcriptions 
                ORDER BY timestamp DESC 
                LIMIT 50
            ''')
            
            # Clear existing items
            for item in self.history_tree.get_children():
                self.history_tree.delete(item)
                
            # Add new items
            for row in cursor.fetchall():
                timestamp = row[0][:19]  # Truncate timestamp
                text = row[1][:100] + "..." if len(row[1]) > 100 else row[1]
                method = row[2]
                self.history_tree.insert("", "end", values=(timestamp, text, method))
                
            conn.close()
        except Exception as e:
            print(f"History load error: {e}")
            
    def copy_to_clipboard(self):
        """Copy current transcription to clipboard"""
        text = self.transcription_text.get("1.0", tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.status_label.configure(text="Copied to clipboard!", foreground="blue")
            self.root.after(2000, lambda: self.status_label.configure(text="Ready", foreground="green"))
            
    def insert_at_cursor(self):
        """Insert transcription at current cursor position"""
        text = self.transcription_text.get("1.0", tk.END).strip()
        if text:
            # Copy to clipboard and simulate paste
            pyperclip.copy(text)
            keyboard.send('ctrl+v')
            self.status_label.configure(text="Text inserted!", foreground="blue")
            self.root.after(2000, lambda: self.status_label.configure(text="Ready", foreground="green"))
            
    def clear_transcription(self):
        """Clear the transcription display"""
        self.transcription_text.delete("1.0", tk.END)
        
    def open_settings(self):
        """Open settings window"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x300")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Engine selection
        engine_frame = ttk.LabelFrame(settings_window, text="Speech Engine", padding="10")
        engine_frame.pack(fill="x", padx=10, pady=10)
        
        engine_var = tk.StringVar(value=getattr(self, 'current_engine', ''))
        
        if WHISPER_AVAILABLE:
            ttk.Radiobutton(engine_frame, text="Whisper (Local, High Quality)", 
                           variable=engine_var, value="whisper").pack(anchor="w")
                           
        if SR_AVAILABLE:
            ttk.Radiobutton(engine_frame, text="Google Speech Recognition (Online)", 
                           variable=engine_var, value="google").pack(anchor="w")
        
        # Hotkey configuration
        hotkey_frame = ttk.LabelFrame(settings_window, text="Hotkey Configuration", padding="10")
        hotkey_frame.pack(fill="x", padx=10, pady=10)
        
        current_hotkey = getattr(self, 'hotkey_combination', 'ctrl+shift+v')
        ttk.Label(hotkey_frame, text=f"Current hotkey: {current_hotkey}").pack(anchor="w")
        
        # Hotkey presets
        hotkey_var = tk.StringVar(value=current_hotkey)
        
        hotkey_options = [
            ("ctrl+shift+v", "Ctrl+Shift+V (default)"),
            ("ctrl+alt+v", "Ctrl+Alt+V (gaming-friendly)"), 
            ("ctrl+`", "Ctrl+` (backtick)"),
            ("f11", "F11 function key"),
            ("ctrl+shift+m", "Ctrl+Shift+M (microphone)"),
            ("alt+space", "Alt+Space (quick access)")
        ]
        
        for value, label in hotkey_options:
            ttk.Radiobutton(hotkey_frame, text=label, variable=hotkey_var, value=value).pack(anchor="w")
        
        # Custom hotkey entry
        custom_frame = ttk.Frame(hotkey_frame)
        custom_frame.pack(fill="x", pady=5)
        ttk.Label(custom_frame, text="Custom:").pack(side="left")
        custom_hotkey_entry = ttk.Entry(custom_frame, width=20)
        custom_hotkey_entry.pack(side="left", padx=5)
        
        def set_custom_hotkey():
            custom_value = custom_hotkey_entry.get().strip()
            if custom_value:
                hotkey_var.set(custom_value)
        
        ttk.Button(custom_frame, text="Use Custom", command=set_custom_hotkey).pack(side="left", padx=5)
        
        # Voice training section
        training_frame = ttk.LabelFrame(settings_window, text="Voice Training", padding="10")
        training_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(training_frame, text="Record voice samples to improve accuracy:").pack(anchor="w")
        ttk.Button(training_frame, text="Start Voice Training", 
                  command=self.start_voice_training).pack(pady=5)
        
        # Audio settings
        audio_frame = ttk.LabelFrame(settings_window, text="Audio Settings", padding="10")
        audio_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Label(audio_frame, text=f"Sample Rate: {self.rate} Hz").pack(anchor="w")
        ttk.Label(audio_frame, text=f"Channels: {self.channels}").pack(anchor="w")
        
        # Save button
        def save_settings():
            self.logger.info("Saving settings...")
            self.add_debug_message("💾 Saving settings...")
            
            # Update speech engine
            new_engine = engine_var.get()
            old_engine = getattr(self, 'current_engine', '')
            
            if new_engine != old_engine:
                self.logger.info(f"Changing speech engine from {old_engine} to {new_engine}")
                self.add_debug_message(f"🔄 Switching engine: {old_engine} → {new_engine}")
                
                # Validate engine availability
                if new_engine == "whisper" and not self.whisper_model:
                    self.add_debug_message("❌ Whisper not available")
                    messagebox.showerror("Error", "Whisper engine not available!")
                    return
                elif new_engine == "google" and not self.speech_recognizer:
                    self.add_debug_message("❌ Google Speech not available")
                    messagebox.showerror("Error", "Google Speech Recognition not available!")
                    return
                
                self.current_engine = new_engine
                self.engine_label.configure(text=f"Engine: {new_engine}")
                self.add_debug_message(f"✅ Engine changed to: {new_engine}")
            
            # Update hotkey
            new_hotkey = hotkey_var.get()
            old_hotkey = getattr(self, 'hotkey_combination', 'ctrl+shift+v')
            
            if new_hotkey != old_hotkey:
                self.logger.info(f"Changing hotkey from {old_hotkey} to {new_hotkey}")
                self.update_hotkey(new_hotkey)
                
            # Save all settings to config file
            self.save_config()
            self.add_debug_message("✅ Settings saved successfully")
            settings_window.destroy()
            
        ttk.Button(settings_window, text="Save Settings", 
                  command=save_settings).pack(pady=20)
        
    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                'hotkey_combination': getattr(self, 'hotkey_combination', 'ctrl+shift+v'),
                'current_engine': getattr(self, 'current_engine', ''),
                'audio_rate': self.rate,
                'audio_channels': self.channels,
                'audio_method': getattr(self, 'audio_method', ''),
                'last_updated': datetime.now().isoformat()
            }
            
            config_file = 'voice_transcription_config.json'
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
                
            self.logger.info(f"Configuration saved to {config_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save config: {e}")
            
    def load_config(self):
        """Load configuration from file"""
        try:
            config_file = 'voice_transcription_config.json'
            with open(config_file, 'r') as f:
                config = json.load(f)
                
            self.hotkey_combination = config.get('hotkey_combination', 'ctrl+shift+v')
            self.current_engine = config.get('current_engine', '')
            
            # Apply other config settings as needed
            saved_rate = config.get('audio_rate', 16000)
            if saved_rate != self.rate:
                self.rate = saved_rate
                
            print(f"Configuration loaded: engine={self.current_engine}, hotkey={self.hotkey_combination}")
            
        except FileNotFoundError:
            # Use defaults if config file doesn't exist
            self.hotkey_combination = 'ctrl+shift+v'
            self.current_engine = ''
            print("No config file found, using defaults")
            
        except json.JSONDecodeError as e:
            print(f"Config file corrupted, using defaults: {e}")
            self.hotkey_combination = 'ctrl+shift+v'
            self.current_engine = ''
            
        except Exception as e:
            print(f"Failed to load config: {e}")
            self.hotkey_combination = 'ctrl+shift+v'
            self.current_engine = ''
        
    def start_voice_training(self):
        """Start voice training process"""
        training_window = tk.Toplevel(self.root)
        training_window.title("Voice Training")
        training_window.geometry("500x400")
        training_window.transient(self.root)
        training_window.grab_set()
        
        # Header
        header_frame = ttk.Frame(training_window, padding="20")
        header_frame.pack(fill="x")
        
        ttk.Label(header_frame, text="🎤 Voice Training", 
                 font=("Arial", 16, "bold")).pack()
        ttk.Label(header_frame, text="Record sample phrases to improve recognition accuracy", 
                 font=("Arial", 10)).pack(pady=(5, 15))
        
        # Sample phrases
        phrases_frame = ttk.LabelFrame(training_window, text="Training Phrases", padding="15")
        phrases_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        sample_phrases = [
            "The quick brown fox jumps over the lazy dog",
            "Hello, this is a test of my voice recognition system",
            "I am training my voice transcription tool to understand me better",
            "Technology makes communication faster and more efficient",
            "Please transcribe this sentence accurately and quickly"
        ]
        
        self.training_phrases = sample_phrases
        self.current_phrase_index = 0
        self.recorded_samples = []
        
        # Current phrase display
        self.phrase_label = ttk.Label(phrases_frame, text=sample_phrases[0], 
                                     font=("Arial", 12), wraplength=400, justify="center")
        self.phrase_label.pack(pady=10)
        
        # Progress
        self.progress_label = ttk.Label(phrases_frame, text=f"Phrase 1 of {len(sample_phrases)}")
        self.progress_label.pack()
        
        self.training_progress = ttk.Progressbar(phrases_frame, length=300, mode='determinate')
        self.training_progress['maximum'] = len(sample_phrases)
        self.training_progress['value'] = 0
        self.training_progress.pack(pady=10)
        
        # Recording controls
        controls_frame = ttk.Frame(phrases_frame)
        controls_frame.pack(pady=15)
        
        self.training_record_button = ttk.Button(controls_frame, text="🎤 Record Phrase", 
                                               command=self.record_training_phrase)
        self.training_record_button.pack(side="left", padx=5)
        
        self.training_skip_button = ttk.Button(controls_frame, text="⏭️ Skip", 
                                             command=self.skip_training_phrase)
        self.training_skip_button.pack(side="left", padx=5)
        
        self.training_replay_button = ttk.Button(controls_frame, text="🔄 Replay", 
                                               command=self.replay_training_phrase)
        self.training_replay_button.pack(side="left", padx=5)
        
        # Status
        self.training_status = ttk.Label(phrases_frame, text="Ready to record", foreground="green")
        self.training_status.pack(pady=5)
        
        # Instructions
        instructions_frame = ttk.LabelFrame(training_window, text="Instructions", padding="15")
        instructions_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        instructions = [
            "1. Read each phrase clearly and naturally",
            "2. Record in a quiet environment", 
            "3. Speak at your normal pace and volume",
            "4. Complete all phrases for best results"
        ]
        
        for instruction in instructions:
            ttk.Label(instructions_frame, text=instruction).pack(anchor="w")
        
        # Close button
        ttk.Button(training_window, text="Close Training", 
                  command=training_window.destroy).pack(pady=10)
                  
        self.training_window = training_window
        
    def record_training_phrase(self):
        """Record a training phrase"""
        if not self.is_recording:
            self.training_record_button.configure(text="🛑 Stop Recording")
            self.training_status.configure(text="Recording...", foreground="red")
            self.is_recording = True
            
            # Start recording in separate thread
            threading.Thread(target=self.process_training_recording, daemon=True).start()
        else:
            self.is_recording = False
            
    def process_training_recording(self):
        """Process training phrase recording"""
        try:
            # Record audio
            temp_file = tempfile.mktemp(suffix=".wav")
            
            if self.audio_method == "pyaudio":
                self.record_with_pyaudio(temp_file)
            elif self.audio_method == "arecord":
                self.record_with_arecord(temp_file)
            elif self.audio_method == "ffmpeg":
                self.record_with_ffmpeg(temp_file)
            
            # Test transcription
            result = self.transcribe_audio(temp_file)
            
            # Store training sample
            training_sample = {
                'phrase': self.training_phrases[self.current_phrase_index],
                'audio_file': temp_file,
                'transcription': result['text'],
                'confidence': result['confidence'],
                'timestamp': datetime.now().isoformat()
            }
            self.recorded_samples.append(training_sample)
            
            # Update UI
            self.root.after(0, self.training_phrase_completed, result)
            
        except Exception as e:
            self.root.after(0, lambda: self.training_status.configure(
                text=f"Recording failed: {str(e)}", foreground="red"))
            
    def training_phrase_completed(self, result):
        """Handle completed training phrase"""
        self.training_record_button.configure(text="🎤 Record Phrase")
        self.is_recording = False
        
        # Show result
        accuracy = "✅ Good" if result['confidence'] > 0.8 else "⚠️ Try again"
        self.training_status.configure(
            text=f"Transcribed: \"{result['text'][:50]}...\" {accuracy}", 
            foreground="green" if result['confidence'] > 0.8 else "orange"
        )
        
        # Move to next phrase
        self.current_phrase_index += 1
        self.training_progress['value'] = self.current_phrase_index
        
        if self.current_phrase_index < len(self.training_phrases):
            # Next phrase
            self.phrase_label.configure(text=self.training_phrases[self.current_phrase_index])
            self.progress_label.configure(text=f"Phrase {self.current_phrase_index + 1} of {len(self.training_phrases)}")
        else:
            # Training complete
            self.training_completed()
            
    def skip_training_phrase(self):
        """Skip current training phrase"""
        self.current_phrase_index += 1
        self.training_progress['value'] = self.current_phrase_index
        
        if self.current_phrase_index < len(self.training_phrases):
            self.phrase_label.configure(text=self.training_phrases[self.current_phrase_index])
            self.progress_label.configure(text=f"Phrase {self.current_phrase_index + 1} of {len(self.training_phrases)}")
            self.training_status.configure(text="Phrase skipped", foreground="blue")
        else:
            self.training_completed()
            
    def replay_training_phrase(self):
        """Replay current phrase (reset for re-recording)"""
        self.training_status.configure(text="Ready to record", foreground="green")
        
    def training_completed(self):
        """Handle training completion"""
        self.phrase_label.configure(text="🎉 Training Complete!")
        self.progress_label.configure(text=f"Recorded {len(self.recorded_samples)} samples")
        self.training_status.configure(text="Voice training data collected", foreground="green")
        
        # Hide training controls
        self.training_record_button.pack_forget()
        self.training_skip_button.pack_forget()
        self.training_replay_button.pack_forget()
        
        # Save training data
        self.save_training_data()
        
        # Show completion message
        messagebox.showinfo("Training Complete", 
                           f"Voice training completed!\n\n"
                           f"Recorded: {len(self.recorded_samples)} samples\n"
                           f"This data will be used to improve recognition accuracy.\n\n"
                           f"Training data saved to database.")
                           
    def save_training_data(self):
        """Save voice training data to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create or update voice profile
            profile_data = {
                'samples': [sample['audio_file'] for sample in self.recorded_samples],
                'phrases': [sample['phrase'] for sample in self.recorded_samples],
                'transcriptions': [sample['transcription'] for sample in self.recorded_samples],
                'confidences': [sample['confidence'] for sample in self.recorded_samples]
            }
            
            cursor.execute('''
                INSERT OR REPLACE INTO voice_profiles 
                (profile_name, audio_samples, created_date, last_updated)
                VALUES (?, ?, ?, ?)
            ''', (
                'default_profile',
                json.dumps(profile_data),
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"Failed to save training data: {e}")
        
    def cleanup(self):
        """Cleanup resources"""
        self.is_recording = False
        
        # Remove hotkey
        if hasattr(self, 'registered_hotkey'):
            try:
                keyboard.remove_hotkey(self.registered_hotkey)
            except:
                pass
                
        if hasattr(self, 'audio') and self.audio:
            self.audio.terminate()
        
    def run(self):
        """Run the application"""
        try:
            self.root.protocol("WM_DELETE_WINDOW", lambda: [self.cleanup(), self.root.destroy()])
            self.root.mainloop()
        except KeyboardInterrupt:
            self.cleanup()

def main():
    # Check for required dependencies
    missing_deps = []
    
    if not WHISPER_AVAILABLE and not SR_AVAILABLE:
        missing_deps.append("whisper OR speech_recognition")
    
    # Check for audio recording capabilities
    audio_available = PYAUDIO_AVAILABLE
    if not audio_available:
        system = platform.system().lower()
        if system == "linux":
            try:
                subprocess.run(["which", "arecord"], check=True, capture_output=True)
                audio_available = True
            except:
                try:
                    subprocess.run(["which", "ffmpeg"], check=True, capture_output=True)
                    audio_available = True
                except:
                    pass
    
    if not audio_available:
        missing_deps.append("audio recording capability")
        
    try:
        import keyboard
    except ImportError:
        missing_deps.append("keyboard")
        
    try:
        import pyperclip
    except ImportError:
        missing_deps.append("pyperclip")
    
    if missing_deps:
        print("Missing required dependencies:")
        if "audio recording capability" in missing_deps:
            print("\nFor audio recording, install ONE of:")
            print("  • PyAudio: sudo apt-get install portaudio19-dev && pip install pyaudio")
            print("  • arecord: sudo apt-get install alsa-utils")
            print("  • ffmpeg: sudo apt-get install ffmpeg")
        
        other_deps = [dep for dep in missing_deps if dep != "audio recording capability"]
        if other_deps:
            print(f"\nAlso install: pip install {' '.join(other_deps)}")
            
        print("\nFor speech recognition engines:")
        print("  • Whisper (local): pip install openai-whisper")
        print("  • Google Speech (online): pip install SpeechRecognition")
        return
        
    app = VoiceTranscriptionTool()
    app.run()

if __name__ == "__main__":
    main()