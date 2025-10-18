#!/usr/bin/env python3
"""
scripts/memory_leak_test.py - Memory leak detection for Voice Transcription Tool.

This script performs sustained recording cycles while monitoring memory usage
to detect potential memory leaks. It's designed to run for extended periods
(hours) to catch slow memory accumulation.

Usage:
    python scripts/memory_leak_test.py --cycles 1000 --log-interval 100
    python scripts/memory_leak_test.py --duration 3600  # Run for 1 hour

The script will:
1. Establish a memory baseline
2. Perform recording cycles continuously
3. Log memory snapshots at regular intervals
4. Alert if memory growth exceeds threshold
5. Generate a memory leak report at the end
"""

import sys
import os
import time
import argparse
import psutil
from datetime import datetime
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'voice_transcription_tool'))

from audio.recorder import AudioRecorder
from speech.engines import SpeechEngineManager
from config.settings import ConfigManager


class MemoryLeakDetector:
    """Monitors memory usage during sustained operations to detect leaks."""

    def __init__(self, threshold=0.20, log_interval=100):
        """
        Initialize memory leak detector.

        Args:
            threshold: Maximum allowed memory growth (0.20 = 20%)
            log_interval: Log memory every N cycles
        """
        self.process = psutil.Process()
        self.threshold = threshold
        self.log_interval = log_interval
        self.baseline_memory = None
        self.memory_samples = []
        self.start_time = None

    def establish_baseline(self):
        """Establish baseline memory usage."""
        # Force garbage collection
        import gc
        gc.collect()

        time.sleep(1)  # Let things settle

        self.baseline_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        self.start_time = time.time()

        print(f"✓ Baseline memory established: {self.baseline_memory:.1f} MB")
        return self.baseline_memory

    def check_memory(self, cycle):
        """
        Check current memory and log if at interval.

        Args:
            cycle: Current cycle number

        Returns:
            dict with memory stats
        """
        current_memory = self.process.memory_info().rss / 1024 / 1024  # MB
        growth = (current_memory - self.baseline_memory) / self.baseline_memory
        elapsed = time.time() - self.start_time

        sample = {
            'cycle': cycle,
            'timestamp': datetime.now().isoformat(),
            'elapsed_seconds': round(elapsed, 2),
            'memory_mb': round(current_memory, 2),
            'baseline_mb': round(self.baseline_memory, 2),
            'growth_percent': round(growth * 100, 2)
        }

        self.memory_samples.append(sample)

        # Log at intervals
        if cycle % self.log_interval == 0:
            print(f"[Cycle {cycle:4d}] Memory: {current_memory:7.1f} MB | "
                  f"Growth: {growth*100:+5.1f}% | Elapsed: {elapsed/60:.1f}min")

        # Check threshold
        if growth > self.threshold:
            print(f"\n⚠️  WARNING: Memory leak detected!")
            print(f"   Baseline: {self.baseline_memory:.1f} MB")
            print(f"   Current:  {current_memory:.1f} MB")
            print(f"   Growth:   {growth*100:.1f}%")
            print(f"   Cycle:    {cycle}")
            return {'leak_detected': True, **sample}

        return {'leak_detected': False, **sample}

    def generate_report(self, output_file=None):
        """
        Generate memory leak detection report.

        Args:
            output_file: Optional file path to write JSON report
        """
        if not self.memory_samples:
            print("No memory samples collected")
            return

        final_sample = self.memory_samples[-1]
        max_memory = max(s['memory_mb'] for s in self.memory_samples)
        max_growth = max(s['growth_percent'] for s in self.memory_samples)

        report = {
            'test_info': {
                'start_time': self.start_time,
                'duration_seconds': final_sample['elapsed_seconds'],
                'total_cycles': len(self.memory_samples),
                'log_interval': self.log_interval,
                'threshold_percent': self.threshold * 100
            },
            'memory_stats': {
                'baseline_mb': self.baseline_memory,
                'final_mb': final_sample['memory_mb'],
                'max_mb': max_memory,
                'final_growth_percent': final_sample['growth_percent'],
                'max_growth_percent': max_growth
            },
            'verdict': {
                'leak_detected': max_growth > (self.threshold * 100),
                'passed': max_growth <= (self.threshold * 100)
            },
            'samples': self.memory_samples
        }

        # Print summary
        print("\n" + "="*60)
        print("MEMORY LEAK DETECTION REPORT")
        print("="*60)
        print(f"Test Duration:    {final_sample['elapsed_seconds']/60:.1f} minutes")
        print(f"Total Cycles:     {len(self.memory_samples)}")
        print(f"Baseline Memory:  {self.baseline_memory:.1f} MB")
        print(f"Final Memory:     {final_sample['memory_mb']:.1f} MB")
        print(f"Max Memory:       {max_memory:.1f} MB")
        print(f"Final Growth:     {final_sample['growth_percent']:+.1f}%")
        print(f"Max Growth:       {max_growth:+.1f}%")
        print(f"Threshold:        {self.threshold*100:.0f}%")
        print(f"Verdict:          {'❌ LEAK DETECTED' if report['verdict']['leak_detected'] else '✅ PASS'}")
        print("="*60)

        # Write JSON report
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2)
            print(f"\n✓ Report saved to: {output_file}")

        return report


def run_recording_cycle_test(cycles=1000, log_interval=100):
    """
    Run sustained recording cycles to detect memory leaks.

    Args:
        cycles: Number of recording cycles to perform
        log_interval: Log memory every N cycles
    """
    print("="*60)
    print("MEMORY LEAK TEST: RECORDING CYCLES")
    print("="*60)
    print(f"Cycles:       {cycles}")
    print(f"Log Interval: {log_interval}")
    print("="*60 + "\n")

    # Initialize components
    detector = MemoryLeakDetector(threshold=0.20, log_interval=log_interval)
    recorder = AudioRecorder()

    # Establish baseline
    detector.establish_baseline()

    failures = []
    start_time = time.time()

    try:
        for cycle in range(1, cycles + 1):
            try:
                # Perform recording cycle (very short for speed)
                result = recorder.start_recording(max_duration=0.1)

                if not result['success']:
                    failures.append(f"Cycle {cycle}: Recording failed - {result.get('error')}")

                # Stop recording
                recorder.is_recording = False

                # Check memory
                memory_check = detector.check_memory(cycle)

                if memory_check['leak_detected']:
                    print(f"\n🛑 Stopping test early due to memory leak detection")
                    break

            except KeyboardInterrupt:
                print(f"\n⚠️  Test interrupted by user at cycle {cycle}")
                break
            except Exception as e:
                failures.append(f"Cycle {cycle}: Exception - {str(e)}")
                print(f"❌ Cycle {cycle} error: {e}")

    finally:
        elapsed = time.time() - start_time
        print(f"\n✓ Test completed in {elapsed/60:.1f} minutes")

        if failures:
            print(f"\n⚠️  {len(failures)} cycle failures occurred:")
            for failure in failures[:10]:  # Show first 10
                print(f"   {failure}")

        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"logs/memory_leak_report_{timestamp}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        detector.generate_report(output_file=report_file)


def run_duration_test(duration_seconds=3600, check_interval=60):
    """
    Run test for a specified duration (e.g., 1 hour, 8 hours).

    Args:
        duration_seconds: How long to run the test
        check_interval: Seconds between recording cycles
    """
    print("="*60)
    print("MEMORY LEAK TEST: DURATION-BASED")
    print("="*60)
    print(f"Duration:       {duration_seconds/3600:.1f} hours")
    print(f"Check Interval: {check_interval} seconds")
    print("="*60 + "\n")

    detector = MemoryLeakDetector(threshold=0.30, log_interval=1)  # Log every check
    recorder = AudioRecorder()

    detector.establish_baseline()

    start_time = time.time()
    cycle = 0

    try:
        while (time.time() - start_time) < duration_seconds:
            cycle += 1

            # Perform recording
            result = recorder.start_recording(max_duration=1.0)
            recorder.is_recording = False

            # Check memory
            memory_check = detector.check_memory(cycle)

            if memory_check['leak_detected']:
                print(f"\n🛑 Stopping test early due to memory leak detection")
                break

            # Wait before next cycle
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print(f"\n⚠️  Test interrupted by user")

    finally:
        # Generate report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = f"logs/memory_leak_duration_report_{timestamp}.json"
        os.makedirs(os.path.dirname(report_file), exist_ok=True)
        detector.generate_report(output_file=report_file)


def main():
    """Main entry point for memory leak testing."""
    parser = argparse.ArgumentParser(
        description="Memory leak detection for Voice Transcription Tool"
    )

    parser.add_argument(
        '--cycles',
        type=int,
        default=1000,
        help='Number of recording cycles to perform (default: 1000)'
    )

    parser.add_argument(
        '--log-interval',
        type=int,
        default=100,
        help='Log memory every N cycles (default: 100)'
    )

    parser.add_argument(
        '--duration',
        type=int,
        help='Run for specified duration in seconds instead of fixed cycles'
    )

    parser.add_argument(
        '--check-interval',
        type=int,
        default=60,
        help='Seconds between checks in duration mode (default: 60)'
    )

    args = parser.parse_args()

    if args.duration:
        run_duration_test(
            duration_seconds=args.duration,
            check_interval=args.check_interval
        )
    else:
        run_recording_cycle_test(
            cycles=args.cycles,
            log_interval=args.log_interval
        )


if __name__ == "__main__":
    main()
