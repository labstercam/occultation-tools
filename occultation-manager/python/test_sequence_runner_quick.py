# test_sequence_runner_quick.py - Quick sequence runner test

import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta

def quick_test():
    """Quick sequence runner test"""
    print("Quick Sequence Runner Test")
    print("=" * 30)
    
    try:
        # Mock config
        class MockConfig:
            def __init__(self):
                self.temp_dir = tempfile.mkdtemp()
            def get_sequence_path(self):
                return self.temp_dir
        
        # Mock event
        class MockEvent:
            def __init__(self, future_hours=1):
                self.event_name = "Test Event"
                self.name = "Test Event - Station ABC"
                now = datetime.utcnow()
                self.goto_time = now + timedelta(hours=future_hours)
                self.start_time_str = self.goto_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Import and test
        from sequence_runner import SequenceRunner
        print("✓ SequenceRunner module imports")
        
        config = MockConfig()
        runner = SequenceRunner(config)
        print("✓ SequenceRunner creates successfully")
        
        # Test basic properties
        assert runner.running == False, "Should not be running initially"
        assert runner.current_sequence is None, "No current sequence initially"
        print("✓ Initial state correct")
        
        # Test with no events
        result = runner.run_sequences([], lambda msg: None)
        assert result == False, "Should fail with no events"
        print("✓ Empty events handled correctly")
        
        # Test with past event
        past_event = MockEvent(future_hours=-1)
        result = runner.run_sequences([past_event], lambda msg: None)
        assert result == False, "Should fail with past events"
        print("✓ Past events handled correctly")
        
        # Test stop function
        runner.stop_sequences()
        assert runner.running == False, "Should not be running after stop"
        print("✓ Stop function works")
        
        # Cleanup
        shutil.rmtree(config.temp_dir)
        
        print("✓ Quick test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)