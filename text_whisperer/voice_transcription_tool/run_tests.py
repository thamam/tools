#!/usr/bin/env python3
"""
Test runner for the Voice Transcription Tool.

This script runs the test suite and provides a summary of results.
"""

import sys
import subprocess
from pathlib import Path

def main():
    """Run the test suite."""
    print("🧪 Voice Transcription Tool Test Suite")
    print("=" * 40)
    
    # Check if pytest is available
    try:
        import pytest
    except ImportError:
        print("❌ pytest not installed")
        print("Install with: pip install pytest")
        return 1
    
    # Set up test environment
    project_root = Path(__file__).parent
    sys.path.insert(0, str(project_root))
    
    # Run tests
    print("\n🏃 Running tests...")
    
    try:
        # Run pytest with coverage if available
        cmd = [sys.executable, "-m", "pytest"]
        
        # Try to add coverage
        try:
            import coverage
            cmd.extend(["--cov=.", "--cov-report=term-missing", "--cov-report=html"])
            print("📊 Running with coverage analysis")
        except ImportError:
            print("📊 Coverage not available (install with: pip install pytest-cov)")
        
        # Add test directory
        cmd.append("tests/")
        
        result = subprocess.run(cmd, cwd=project_root)
        
        if result.returncode == 0:
            print("\n✅ All tests passed!")
            
            # Show coverage report location if available
            coverage_dir = project_root / "htmlcov"
            if coverage_dir.exists():
                print(f"📊 Coverage report: {coverage_dir / 'index.html'}")
        else:
            print("\n❌ Some tests failed!")
            
        return result.returncode
        
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())