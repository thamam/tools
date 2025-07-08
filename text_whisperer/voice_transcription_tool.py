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
        self.root = tk.Tk()
        self.root.title("Voice Transcription Tool")
        self.root.geometry("800x600")
        
        # Audio settings
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.record_seconds = 10  # Max recording length
        
        # State variables
        self.is_recording = False
        self.is_listening = False
        self.audio_queue = queue.Queue()
        self.transcription_queue = queue.Queue()
        
        # Initialize components
        self.init_database()
        self.init_audio()
        self.init_speech_engine()
        self.create_gui()
        self.setup_hotkeys()
        
        # Start background threads
        self.start_background_threads()
        
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
        self.audio_method = None
        
        if PYAUDIO_AVAILABLE:
            try:
                self.audio = pyaudio.PyAudio()
                self.audio_method = "pyaudio"
            except Exception as e:
                print(f"PyAudio initialization failed: {e}")
                
        # Fallback to system recording tools
        if not self.audio_method:
            system = platform.system().lower()
            if system == "linux":
                # Check if arecord is available
                try:
                    subprocess.run(["which", "arecord"], check=True, capture_output=True)
                    self.audio_method = "arecord"
                except:
                    try:
                        subprocess.run(["which", "ffmpeg"], check=True, capture_output=True)
                        self.audio_method = "ffmpeg"
                    except:
                        pass
            elif system == "darwin":  # macOS
                self.audio_method = "afplay"
            elif system == "windows":
                self.audio_method = "windows"
        
    def init_speech_engine(self):
        """Initialize speech recognition engines"""
        self.whisper_model = None
        self.speech_recognizer = None
        
        if WHISPER_AVAILABLE:
            try:
                self.whisper_model = whisper.load_model("base")
                self.current_engine = "whisper"
            except Exception as e:
                print(f"Failed to load Whisper: {e}")
                
        if SR_AVAILABLE and not self.whisper_model:
            self.speech_recognizer = sr.Recognizer()
            self.current_engine = "google"
            
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
        self.history_tree = ttk.Treeview(history_frame, columns=columns, show="headings", height=6)
        
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
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
        main_frame.rowconfigure(4, weight=1)
        transcription_frame.columnconfigure(0, weight=1)
        transcription_frame.rowconfigure(0, weight=1)
        history_frame.columnconfigure(0, weight=1)
        history_frame.rowconfigure(0, weight=1)
        
        # Load recent history
        self.load_recent_transcriptions()
        
    def setup_hotkeys(self):
        """Setup global hotkeys"""
        self.hotkey_active = False
        try:
            # Ctrl+Shift+V to start/stop recording
            keyboard.add_hotkey('ctrl+shift+v', self.hotkey_toggle_recording)
        except Exception as e:
            print(f"Failed to setup hotkeys: {e}")
            
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
        if not hasattr(self, 'current_engine') or self.current_engine is None:
            messagebox.showerror("Error", "No speech recognition engine available!")
            return
            
        if not self.audio_method:
            messagebox.showerror("Error", "No audio recording method available!\n\n"
                               "Please install:\n"
                               "• PyAudio: pip install pyaudio\n"
                               "• Or arecord: sudo apt-get install alsa-utils\n"
                               "• Or ffmpeg: sudo apt-get install ffmpeg")
            return
            
        self.is_recording = True
        self.record_button.configure(text="🛑 Stop Recording")
        self.status_label.configure(text="Recording...", foreground="red")
        
        # Start recording in a separate thread
        threading.Thread(target=self.record_audio, daemon=True).start()
        
    def stop_recording(self):
        """Stop audio recording"""
        self.is_recording = False
        self.record_button.configure(text="🎤 Start Recording")
        self.status_label.configure(text="Processing...", foreground="orange")
        
    def record_audio(self):
        """Record audio from microphone using available method"""
        try:
            temp_file = tempfile.mktemp(suffix=".wav")
            
            if self.audio_method == "pyaudio":
                self.record_with_pyaudio(temp_file)
            elif self.audio_method == "arecord":
                self.record_with_arecord(temp_file)
            elif self.audio_method == "ffmpeg":
                self.record_with_ffmpeg(temp_file)
            else:
                raise Exception("No audio recording method available")
                
            # Queue for transcription
            self.audio_queue.put(temp_file)
            
        except Exception as e:
            print(f"Recording error: {e}")
            self.root.after(0, lambda: self.status_label.configure(text="Recording error", foreground="red"))
            
    def record_with_pyaudio(self, temp_file):
        """Record using PyAudio"""
        stream = self.audio.open(format=self.format,
                               channels=self.channels,
                               rate=self.rate,
                               input=True,
                               frames_per_buffer=self.chunk)
        
        frames = []
        start_time = time.time()
        
        while self.is_recording and (time.time() - start_time) < self.record_seconds:
            data = stream.read(self.chunk)
            frames.append(data)
            
        stream.stop_stream()
        stream.close()
        
        # Save audio to file
        wf = wave.open(temp_file, 'wb')
        wf.setnchannels(self.channels)
        wf.setsampwidth(self.audio.get_sample_size(self.format))
        wf.setframerate(self.rate)
        wf.writeframes(b''.join(frames))
        wf.close()
        
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
        try:
            if self.current_engine == "whisper" and self.whisper_model:
                result = self.whisper_model.transcribe(audio_file)
                return {
                    'text': result['text'].strip(),
                    'confidence': 0.95,  # Whisper doesn't provide confidence
                    'method': 'whisper'
                }
                
            elif self.current_engine == "google" and self.speech_recognizer:
                with sr.AudioFile(audio_file) as source:
                    audio_data = self.speech_recognizer.record(source)
                    text = self.speech_recognizer.recognize_google(audio_data)
                    return {
                        'text': text,
                        'confidence': 0.9,
                        'method': 'google'
                    }
                    
        except Exception as e:
            print(f"Transcription failed: {e}")
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
            new_engine = engine_var.get()
            if new_engine != getattr(self, 'current_engine', ''):
                self.current_engine = new_engine
                self.engine_label.configure(text=f"Engine: {new_engine}")
            settings_window.destroy()
            
        ttk.Button(settings_window, text="Save Settings", 
                  command=save_settings).pack(pady=20)
        
    def start_voice_training(self):
        """Start voice training process"""
        messagebox.showinfo("Voice Training", 
                           "Voice training will be implemented in the next version. "
                           "This will allow recording custom voice samples to improve "
                           "recognition accuracy for your specific voice patterns.")
        
    def cleanup(self):
        """Cleanup resources"""
        self.is_recording = False
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