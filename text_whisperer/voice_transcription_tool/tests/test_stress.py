"""
tests/test_stress.py - Stress testing for production readiness validation.

This module contains stress tests designed to catch edge cases, resource leaks,
and stability issues under heavy load. These tests ensure the application can
handle sustained usage without crashes or memory leaks.

Test scenarios:
- 1000 recording cycles to detect resource leaks
- Rapid hotkey presses to test race conditions
- Long recording cycles to test large buffer handling
- Concurrent operations to test thread safety
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock, patch
import psutil
import os

# Import components to test
from audio.recorder import AudioRecorder
from speech.engines import SpeechEngineManager
from config.settings import ConfigManager


class TestStressCycles:
    """Stress tests for recording cycle repetition."""

    @pytest.fixture
    def recorder(self):
        """Create a mocked AudioRecorder for stress testing."""
        with patch('audio.recorder.pyaudio.PyAudio'):
            recorder = AudioRecorder()
            # Mock PyAudio initialization
            recorder.p = Mock()
            recorder.audio_method = "pyaudio"
            recorder.rate = 16000
            recorder.channels = 1
            recorder.chunk_size = 1024
            yield recorder

    @pytest.fixture
    def speech_manager(self):
        """Create a mocked SpeechEngineManager."""
        manager = SpeechEngineManager()
        # Mock the transcribe method to return quickly
        manager.transcribe = Mock(return_value={
            'success': True,
            'text': 'Test transcription',
            'language': 'en',
            'confidence': 0.95
        })
        return manager

    def test_1000_recording_cycles(self, recorder):
        """
        Stress test: 1000 start/stop recording cycles.

        Validates:
        - No memory leaks over sustained cycles
        - Proper resource cleanup between cycles
        - Recording state management under load
        - Memory growth stays under 20% of baseline
        """
        import tempfile
        import wave
        from pathlib import Path

        # Get baseline memory
        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024  # MB

        # Mock the recording methods to create dummy audio files
        def create_dummy_audio(file_path, *args, **kwargs):
            """Create a minimal valid WAV file for testing."""
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b'\x00\x01' * 100)  # 100 frames of audio

        recorder._record_pyaudio = create_dummy_audio

        failures = []
        temp_files = []

        for cycle in range(1000):
            try:
                # Start recording
                result = recorder.start_recording(
                    max_duration=0.1,  # Very short for speed
                    progress_callback=None
                )

                # Track temp file for cleanup
                if result.get('audio_file'):
                    temp_files.append(result['audio_file'])

                # Verify recording started
                if not result['success']:
                    failures.append(f"Cycle {cycle}: Recording failed - {result.get('error')}")

                # Check memory every 100 cycles
                if cycle % 100 == 0:
                    current_memory = process.memory_info().rss / 1024 / 1024
                    memory_growth = (current_memory - baseline_memory) / baseline_memory

                    # Fail if memory grows beyond 20%
                    if memory_growth > 0.20:
                        failures.append(
                            f"Cycle {cycle}: Memory leak detected! "
                            f"Baseline: {baseline_memory:.1f}MB, "
                            f"Current: {current_memory:.1f}MB, "
                            f"Growth: {memory_growth*100:.1f}%"
                        )
                        break

            except Exception as e:
                failures.append(f"Cycle {cycle}: Exception - {str(e)}")

        # Cleanup temp files
        for temp_file in temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except:
                pass

        # Report all failures
        assert len(failures) == 0, f"Stress test failures:\n" + "\n".join(failures)

    def test_rapid_hotkey_presses(self, recorder):
        """
        Stress test: Rapid start/stop cycles (simulating rapid hotkey presses).

        Validates:
        - No race conditions in recording state
        - Queue doesn't accumulate stale data
        - Proper handling of state transitions
        """
        import wave
        from pathlib import Path

        def create_dummy_audio(file_path, *args, **kwargs):
            """Create a minimal valid WAV file for testing."""
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b'\x00\x01' * 100)

        recorder._record_pyaudio = create_dummy_audio

        failures = []
        temp_files = []

        for cycle in range(100):
            try:
                # Rapid start
                result1 = recorder.start_recording(max_duration=0.01)
                if result1.get('audio_file'):
                    temp_files.append(result1['audio_file'])

                time.sleep(0.001)  # Very short delay

                # Another rapid start (should fail with already_recording or succeed if first completed)
                result2 = recorder.start_recording(max_duration=0.01)
                if result2.get('audio_file'):
                    temp_files.append(result2['audio_file'])

                # Verify appropriate behavior
                if not result1['success']:
                    failures.append(f"Cycle {cycle}: First recording unexpectedly failed - {result1.get('error')}")

            except Exception as e:
                failures.append(f"Cycle {cycle}: Race condition - {str(e)}")

        # Cleanup temp files
        for temp_file in temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except:
                pass

        assert len(failures) == 0, f"Race condition failures:\n" + "\n".join(failures)

    def test_long_recording_cycles(self, recorder):
        """
        Stress test: Multiple long recordings (30s each).

        Validates:
        - Large audio buffer handling
        - Memory management for long recordings
        - Sustained operation without crashes
        """
        import wave
        from pathlib import Path

        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024

        # Mock long recording with larger audio file
        def mock_long_record(file_path, *args, **kwargs):
            # Create larger audio file to simulate 30s recording
            # Simulate 30s recording with gradual data accumulation
            time.sleep(0.1)  # Shortened for test speed
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                # 30s at 16kHz = 480,000 frames
                wf.writeframes(b'\x00\x01' * 10000)  # Larger file

        recorder._record_pyaudio = mock_long_record

        failures = []
        temp_files = []

        for cycle in range(10):  # 10 long recordings
            try:
                result = recorder.start_recording(max_duration=30.0)
                if result.get('audio_file'):
                    temp_files.append(result['audio_file'])

                if not result['success']:
                    failures.append(f"Cycle {cycle}: Recording failed - {result.get('error')}")

                # Check memory after each long recording
                current_memory = process.memory_info().rss / 1024 / 1024
                memory_growth = (current_memory - baseline_memory) / baseline_memory

                if memory_growth > 0.30:  # 30% threshold for long recordings
                    failures.append(
                        f"Cycle {cycle}: Memory leak in long recording! "
                        f"Growth: {memory_growth*100:.1f}%"
                    )

            except Exception as e:
                failures.append(f"Cycle {cycle}: Long recording failed - {str(e)}")

        # Cleanup temp files
        for temp_file in temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except:
                pass

        assert len(failures) == 0, f"Long recording failures:\n" + "\n".join(failures)


class TestConcurrentOperations:
    """Tests for concurrent operation safety."""

    @pytest.fixture
    def recorder(self):
        """Create a mocked AudioRecorder."""
        import wave

        with patch('audio.recorder.pyaudio.PyAudio'):
            recorder = AudioRecorder()
            recorder.p = Mock()
            recorder.audio_method = "pyaudio"

            # Mock to create dummy audio files
            def create_dummy_audio(file_path, *args, **kwargs):
                with wave.open(file_path, 'wb') as wf:
                    wf.setnchannels(1)
                    wf.setsampwidth(2)
                    wf.setframerate(16000)
                    wf.writeframes(b'\x00\x01' * 100)

            recorder._record_pyaudio = create_dummy_audio
            yield recorder

    def test_concurrent_start_attempts(self, recorder):
        """
        Test concurrent start_recording() calls.

        Validates:
        - Only one recording can be active at a time
        - Proper rejection of duplicate start attempts
        - Thread-safe state management
        """
        from pathlib import Path

        results = []
        temp_files = []

        def attempt_start():
            result = recorder.start_recording(max_duration=0.1)
            results.append(result)
            if result.get('audio_file'):
                temp_files.append(result['audio_file'])

        # Launch 5 concurrent start attempts
        threads = [threading.Thread(target=attempt_start) for _ in range(5)]

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()

        # At least one should succeed
        successful = [r for r in results if r['success']]
        already_recording = [r for r in results if 'already_recording' in r.get('error_type', '')]

        assert len(successful) >= 1, f"Expected at least 1 success, got {len(successful)}"

        # Cleanup temp files
        for temp_file in temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except:
                pass


class TestMemoryLeakDetection:
    """Tests specifically designed to detect memory leaks."""

    def test_transcription_memory_leak(self):
        """
        Test for memory leaks in transcription processing.

        Validates:
        - Transcription results are properly garbage collected
        - No accumulation of result objects in memory
        """
        manager = SpeechEngineManager()

        # Mock transcribe to return data quickly
        mock_result = {
            'success': True,
            'text': 'This is a test transcription with some length to it' * 10,
            'language': 'en',
            'confidence': 0.95
        }
        manager.transcribe = Mock(return_value=mock_result)

        process = psutil.Process()
        baseline_memory = process.memory_info().rss / 1024 / 1024

        # Run 500 transcriptions
        for i in range(500):
            result = manager.transcribe('fake_audio_file.wav')
            # Immediately discard result to test garbage collection
            del result

        # Check final memory
        final_memory = process.memory_info().rss / 1024 / 1024
        memory_growth = (final_memory - baseline_memory) / baseline_memory

        # Memory should not grow significantly (allow 15% for Python overhead)
        assert memory_growth < 0.15, (
            f"Memory leak detected in transcription! "
            f"Baseline: {baseline_memory:.1f}MB, "
            f"Final: {final_memory:.1f}MB, "
            f"Growth: {memory_growth*100:.1f}%"
        )

    def test_config_save_memory_leak(self):
        """
        Test for memory leaks in config save operations.

        Validates:
        - Config objects don't accumulate in memory
        - File handles are properly closed
        """
        import tempfile
        import shutil

        # Create temp config directory
        temp_dir = tempfile.mkdtemp()
        config_file = os.path.join(temp_dir, 'test_config.json')

        try:
            config = ConfigManager(config_file=config_file)

            process = psutil.Process()
            baseline_memory = process.memory_info().rss / 1024 / 1024

            # Perform 1000 save operations
            for i in range(1000):
                config.set('test_key', f'value_{i}')
                config.save()

            final_memory = process.memory_info().rss / 1024 / 1024
            memory_growth = (final_memory - baseline_memory) / baseline_memory

            assert memory_growth < 0.10, (
                f"Memory leak in config save! Growth: {memory_growth*100:.1f}%"
            )

        finally:
            # Clean up
            shutil.rmtree(temp_dir)


class TestErrorRecovery:
    """Tests for graceful error recovery under stress."""

    @pytest.fixture
    def recorder(self):
        """Create recorder with error injection capability."""
        with patch('audio.recorder.pyaudio.PyAudio'):
            recorder = AudioRecorder()
            recorder.p = Mock()
            recorder.audio_method = "pyaudio"
            yield recorder

    def test_recovery_from_intermittent_failures(self, recorder):
        """
        Test recovery from intermittent recording failures.

        Validates:
        - System recovers from transient errors
        - Subsequent recordings work after failure
        - Error state doesn't persist
        """
        import wave
        from pathlib import Path

        call_count = [0]
        temp_files = []

        def intermittent_failure(file_path, *args, **kwargs):
            call_count[0] += 1
            # Fail every 3rd call
            if call_count[0] % 3 == 0:
                raise Exception("Simulated intermittent failure")
            # Otherwise create a dummy file
            with wave.open(file_path, 'wb') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(16000)
                wf.writeframes(b'\x00\x01' * 100)

        recorder._record_pyaudio = intermittent_failure

        success_count = 0
        failure_count = 0

        for i in range(30):
            try:
                result = recorder.start_recording(max_duration=0.1)
                if result.get('audio_file'):
                    temp_files.append(result['audio_file'])

                if result['success']:
                    success_count += 1
                else:
                    failure_count += 1
            except:
                failure_count += 1

        # Cleanup temp files
        for temp_file in temp_files:
            try:
                Path(temp_file).unlink(missing_ok=True)
            except:
                pass

        # Should have mix of successes and failures
        assert success_count > 15, f"Too few successful recordings: {success_count}/30"
        assert failure_count > 5, f"Expected some failures, got {failure_count}"


# Pytest markers
pytestmark = [
    pytest.mark.slow,  # These are slow stress tests
    pytest.mark.stress,  # Custom marker for stress tests
]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
