"""
speech/training.py - Voice training functionality for the Voice Transcription Tool.

MIGRATION STEP 4B: Create this file

TO MIGRATE from voice_transcription.py, copy these methods:
- start_voice_training() → becomes VoiceTrainer.start_training_session()
- All voice training dialog methods
- training_phrase_completed() → becomes record_sample()
- save_training_data() → use DatabaseManager
- get_voice_profiles() → use DatabaseManager
- clear_voice_training() → use DatabaseManager
"""

import logging
import tempfile
import os
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime


class VoiceTrainer:
    """Handles voice training operations."""
    
    def __init__(self, db_manager):
        self.logger = logging.getLogger(__name__)
        self.db_manager = db_manager
        self.sample_phrases = [
            "The quick brown fox jumps over the lazy dog",
            "Hello, this is a test of my voice recognition system", 
            "I am training my voice transcription tool to understand me better",
            "Technology makes communication faster and more efficient",
            "Please transcribe this sentence accurately and quickly"
        ]
        
        # Training state
        self.current_phrase_index = 0
        self.recorded_samples = []
        self.is_training = False
    
    def get_sample_phrases(self) -> List[str]:
        """Get the list of training phrases."""
        return self.sample_phrases.copy()
    
    def start_training_session(self) -> Dict[str, Any]:
        """
        Start a new training session.
        
        MIGRATION: Copy logic from your start_voice_training() method here.
        """
        self.current_phrase_index = 0
        self.recorded_samples = []
        self.is_training = True
        
        self.logger.info("Voice training session started")
        
        return {
            'total_phrases': len(self.sample_phrases),
            'current_phrase': self.sample_phrases[0],
            'phrase_index': 0
        }
    
    def get_current_phrase(self) -> Optional[str]:
        """Get the current training phrase."""
        if 0 <= self.current_phrase_index < len(self.sample_phrases):
            return self.sample_phrases[self.current_phrase_index]
        return None
    
    def record_sample(self, audio_file: str, transcription: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a training sample.
        
        MIGRATION: Copy logic from your training_phrase_completed() method here.
        """
        if not self.is_training:
            return {'error': 'Training session not active'}
        
        current_phrase = self.get_current_phrase()
        if not current_phrase:
            return {'error': 'No current phrase'}
        
        # Store the sample
        sample = {
            'phrase': current_phrase,
            'audio_file': audio_file,
            'transcription': transcription['text'],
            'confidence': transcription['confidence'],
            'timestamp': datetime.now().isoformat(),
            'phrase_index': self.current_phrase_index
        }
        
        self.recorded_samples.append(sample)
        self.logger.info(f"Recorded training sample {self.current_phrase_index + 1}")
        
        # Move to next phrase
        self.current_phrase_index += 1
        
        # Check if training is complete
        if self.current_phrase_index >= len(self.sample_phrases):
            return self._complete_training()
        
        # Return next phrase info
        return {
            'phrase_completed': True,
            'next_phrase': self.sample_phrases[self.current_phrase_index],
            'phrase_index': self.current_phrase_index,
            'total_phrases': len(self.sample_phrases),
            'accuracy': self._calculate_accuracy(transcription, current_phrase)
        }
    
    def skip_phrase(self) -> Dict[str, Any]:
        """
        Skip the current phrase.
        
        MIGRATION: Copy logic from your skip_training_phrase() method here.
        """
        self.current_phrase_index += 1
        
        if self.current_phrase_index >= len(self.sample_phrases):
            return self._complete_training()
        
        return {
            'phrase_skipped': True,
            'next_phrase': self.sample_phrases[self.current_phrase_index],
            'phrase_index': self.current_phrase_index,
            'total_phrases': len(self.sample_phrases)
        }
    
    def _complete_training(self) -> Dict[str, Any]:
        """
        Complete the training session.
        
        MIGRATION: Copy logic from your training_completed() method here.
        """
        self.is_training = False
        
        # Save training data to database
        training_data = {
            'samples': len(self.recorded_samples),
            'phrases': [sample['phrase'] for sample in self.recorded_samples],
            'transcriptions': [sample['transcription'] for sample in self.recorded_samples],
            'confidences': [sample['confidence'] for sample in self.recorded_samples],
            'audio_files': [sample['audio_file'] for sample in self.recorded_samples]
        }
        
        success = self.db_manager.save_voice_profile('default_profile', training_data)
        
        self.logger.info(f"Training completed with {len(self.recorded_samples)} samples")
        
        return {
            'training_complete': True,
            'samples_recorded': len(self.recorded_samples),
            'data_saved': success,
            'overall_accuracy': self._calculate_overall_accuracy()
        }
    
    def _calculate_accuracy(self, transcription: Dict[str, Any], original_phrase: str) -> float:
        """Calculate accuracy of a single transcription."""
        transcribed_text = transcription['text'].lower().strip()
        original_text = original_phrase.lower().strip()
        
        # Simple word-based accuracy
        original_words = original_text.split()
        transcribed_words = transcribed_text.split()
        
        if not original_words:
            return 0.0
        
        # Count matching words (order independent)
        matches = sum(1 for word in original_words if word in transcribed_words)
        accuracy = matches / len(original_words)
        
        return min(accuracy, transcription.get('confidence', 0.0))
    
    def _calculate_overall_accuracy(self) -> float:
        """Calculate overall training accuracy."""
        if not self.recorded_samples:
            return 0.0
        
        total_accuracy = 0.0
        for sample in self.recorded_samples:
            accuracy = self._calculate_accuracy(
                {'text': sample['transcription'], 'confidence': sample['confidence']},
                sample['phrase']
            )
            total_accuracy += accuracy
        
        return total_accuracy / len(self.recorded_samples)
    
    def get_training_progress(self) -> Dict[str, Any]:
        """Get current training progress."""
        return {
            'is_training': self.is_training,
            'current_phrase_index': self.current_phrase_index,
            'total_phrases': len(self.sample_phrases),
            'samples_recorded': len(self.recorded_samples),
            'current_phrase': self.get_current_phrase()
        }
    
    def cancel_training(self) -> None:
        """
        Cancel the current training session.
        
        MIGRATION: Copy any cleanup logic from your training cancellation.
        """
        self.is_training = False
        self.current_phrase_index = 0
        
        # Clean up audio files
        for sample in self.recorded_samples:
            try:
                os.unlink(sample['audio_file'])
            except:
                pass
        
        self.recorded_samples = []
        self.logger.info("Training session cancelled")
    
    def get_existing_profiles(self) -> List[Dict[str, Any]]:
        """
        Get existing voice training profiles.
        
        MIGRATION: Copy logic from your get_voice_profiles() method here.
        """
        return self.db_manager.get_voice_profiles()
    
    def clear_training_data(self) -> bool:
        """
        Clear all training data.
        
        MIGRATION: Copy logic from your clear_voice_training() method here.
        """
        return self.db_manager.clear_voice_profiles()
    
    def has_training_data(self) -> bool:
        """Check if there is existing training data."""
        profiles = self.get_existing_profiles()
        return len(profiles) > 0
    
    def get_training_stats(self) -> Dict[str, Any]:
        """Get statistics about existing training data."""
        profiles = self.get_existing_profiles()
        
        if not profiles:
            return {
                'profiles_count': 0,
                'total_samples': 0,
                'last_training': None
            }
        
        total_samples = 0
        last_training = None
        
        for profile in profiles:
            if 'audio_samples' in profile and 'samples' in profile['audio_samples']:
                total_samples += profile['audio_samples']['samples']
            
            if not last_training or profile['last_updated'] > last_training:
                last_training = profile['last_updated']
        
        return {
            'profiles_count': len(profiles),
            'total_samples': total_samples,
            'last_training': last_training
        }


# MIGRATION TEST: Test this module independently
if __name__ == "__main__":
    import sys
    sys.path.append('..')
    from utils.logger import setup_logging
    from config.database import DatabaseManager
    
    setup_logging()
    
    # Test voice trainer
    db_manager = DatabaseManager("test_training_db.sqlite")
    trainer = VoiceTrainer(db_manager)
    
    phrases = trainer.get_sample_phrases()
    print(f"Sample phrases: {len(phrases)}")
    
    # Test training session start
    session_info = trainer.start_training_session()
    print(f"Training session started: {'✅' if session_info else '❌'}")
    
    # Test training data stats
    stats = trainer.get_training_stats()
    print(f"Training stats: {stats}")
    
    # Test existing profiles
    has_data = trainer.has_training_data()
    print(f"Has training data: {'✅' if has_data else '❌'}")
    
    print("✅ Voice training module test completed!")
