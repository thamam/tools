"""
config/database.py - Database operations for the Voice Transcription Tool.

MIGRATION STEP 2C: Create this file third (only depends on sqlite3)

TO MIGRATE: Copy these methods from your original voice_transcription.py:
- init_database()
- save_transcription() 
- load_recent_transcriptions()
- save_voice_profile()
- get_voice_profiles()
- clear_voice_profiles()
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional


class DatabaseManager:
    """Manages SQLite database operations."""
    
    def __init__(self, db_path: str = "voice_transcriptions.db"):
        self.db_path = Path(db_path)
        self.logger = logging.getLogger(__name__)
        self.init_database()
    
    def init_database(self) -> None:
        """Initialize database tables."""
        try:
            with sqlite3.connect(self.db_path) as conn:
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
                
                # Create voice profiles table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS voice_profiles (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        profile_name TEXT,
                        audio_samples TEXT,
                        created_date TEXT,
                        last_updated TEXT
                    )
                ''')
                
                conn.commit()
                self.logger.info("Database initialized successfully")
                
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
    
    def save_transcription(self, text: str, confidence: float, method: str, 
                          audio_path: Optional[str] = None) -> bool:
        """Save a transcription to the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO transcriptions (timestamp, original_audio_path, 
                                              transcribed_text, confidence, method)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    datetime.now().isoformat(),
                    audio_path,
                    text,
                    confidence,
                    method
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save transcription: {e}")
            return False
    
    def get_recent_transcriptions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent transcriptions."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT timestamp, transcribed_text, method, confidence
                    FROM transcriptions 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                ''', (limit,))
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'timestamp': row[0],
                        'text': row[1],
                        'method': row[2],
                        'confidence': row[3]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to get recent transcriptions: {e}")
            return []
    
    def save_voice_profile(self, profile_name: str, training_data: Dict[str, Any]) -> bool:
        """Save voice training profile."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT OR REPLACE INTO voice_profiles 
                    (profile_name, audio_samples, created_date, last_updated)
                    VALUES (?, ?, ?, ?)
                ''', (
                    profile_name,
                    json.dumps(training_data),
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save voice profile: {e}")
            return False
    
    def get_voice_profiles(self) -> List[Dict[str, Any]]:
        """Get all voice training profiles."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM voice_profiles ORDER BY last_updated DESC')
                
                results = []
                for row in cursor.fetchall():
                    results.append({
                        'id': row[0],
                        'profile_name': row[1],
                        'audio_samples': json.loads(row[2]) if row[2] else {},
                        'created_date': row[3],
                        'last_updated': row[4]
                    })
                
                return results
                
        except Exception as e:
            self.logger.error(f"Failed to get voice profiles: {e}")
            return []
    
    def clear_voice_profiles(self) -> bool:
        """Clear all voice training data."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM voice_profiles')
                conn.commit()
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to clear voice profiles: {e}")
            return False


# MIGRATION TEST: Test this module independently
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from utils.logger import setup_logging
    
    setup_logging()
    
    # Test database operations
    db = DatabaseManager("test_db.sqlite")
    
    # Test transcription save/load
    success = db.save_transcription("Test transcription", 0.95, "test")
    print(f"Save transcription: {'✅' if success else '❌'}")
    
    transcriptions = db.get_recent_transcriptions(5)
    print(f"Load transcriptions: {'✅' if transcriptions else '❌'}")
    
    # Test voice profile save/load
    test_profile = {"samples": ["test1.wav", "test2.wav"]}
    success = db.save_voice_profile("test_profile", test_profile)
    print(f"Save voice profile: {'✅' if success else '❌'}")
    
    profiles = db.get_voice_profiles()
    print(f"Load voice profiles: {'✅' if profiles else '❌'}")
    
    print("✅ Database module test completed!")
