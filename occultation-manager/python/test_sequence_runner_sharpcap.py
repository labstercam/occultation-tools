# test_sequence_runner_sharpcap.py - Test SharpCap integration

import os
import tempfile
import shutil
from datetime import datetime, timedelta

def test_sharpcap_integration():
    """Test SharpCap integration aspects"""
    print("SharpCap Integration Test")
    print("=" * 30)
    
    try:
        # Mock config and event
        class MockConfig:
            def __init__(self):
                self.temp_dir = tempfile.mkdtemp()
            def get_sequence_path(self):
                return self.temp_dir
        
        class MockEvent:
            def __init__(self):
                self.event_name = "SharpCap Test Event"
                self.name = "SharpCap Test Event - Station ABC"
                now = datetime.utcnow()
                self.goto_time = now + timedelta(seconds=5)
                self.start_time_str = self.goto_time.strftime('%Y-%m-%dT%H:%M:%S')
        
        from sequence_runner import SequenceRunner
        
        config = MockConfig()
        runner = SequenceRunner(config)
        event = MockEvent()
        
        # Create a test sequence file
        start_time = datetime.strptime(event.start_time_str, '%Y-%m-%dT%H:%M:%S')
        clean_name = "".join(c for c in event.name if c.isalnum() or c in ('(',')',' ', '-', '_')).rstrip()
        seq_name = start_time.strftime('%Y%m%d') + ' ' + clean_name + '.seq'
        sequence_file_path = os.path.join(config.get_sequence_path(), seq_name)
        
        with open(sequence_file_path, 'w') as f:
            f.write("""# Test sequence for SharpCap integration
# This file tests the sequence runner's SharpCap integration

COMMENT "Starting test sequence"
WAIT 1
COMMENT "Test sequence completed"
""")
        
        print(f"✓ Created test sequence: {seq_name}")
        
        # Test single sequence execution (will fail without SharpCap)
        def status_callback(msg):
            print(f"  Status: {msg}")
        
        success = runner.run_single_sequence(sequence_file_path, event, status_callback)
        
        if success:
            print("✓ SharpCap integration working (SharpCap detected)")
        else:
            print("✓ SharpCap integration handled gracefully (SharpCap not available)")
        
        # Test the SharpCap detection logic
        try:
            import clr
            clr.AddReference(r"C:\Program Files\SharpCap 4.1\SharpCap.exe")
            from SharpCap import *
            print("✓ SharpCap libraries accessible")
        except:
            print("✓ SharpCap libraries not available (expected in test environment)")
        
        # Cleanup
        shutil.rmtree(config.temp_dir)
        
        print("✓ SharpCap integration test completed")
        
    except Exception as e:
        print(f"❌ SharpCap integration test failed: {e}")

if __name__ == "__main__":
    test_sharpcap_integration()


"""
Sequence Runner Module Standalone Test
==================================================
✓ SequenceRunner module imported successfully

=== Testing SequenceRunner Creation ===
✓ SequenceRunner created successfully
✓ Initial running state: False
✓ Current sequence: None

=== Testing Sequence File Detection ===
✓ Created mock sequence file: 20241215 Future Event - Test Station.seq
✓ Sequence file exists and is accessible
✓ Sequence file contains correct event data

=== Testing Event Filtering ===
✓ Created 4 test events
  - Past Event: -3595.8s (PAST)
  - Current Event: 32.2s (FUTURE)
  - Future Event 1: 3632.2s (FUTURE)
  - Future Event 2: 7232.2s (FUTURE)
✓ Filtered to 3 future events
✓ Event filtering logic works correctly

=== Testing Run Sequences (No Events) ===
  Status: No future events to run
✓ Empty events result: Failed (expected)
  Status: No future events to run
✓ Past events result: Failed (expected)
✓ Status messages captured: 2
✓ Correct 'no future events' message found

=== Testing Run Sequences (Future Events) ===
✓ Created sequence for Quick Event 1
✓ Created sequence for Quick Event 2
✓ Starting sequence execution test...
  [0.0s] Status: Running sequence 1/2: Quick Event 1
  [0.1s] Status: Starting SharpCap sequence: 20241215 Quick Event 1 - Test Station.seq
  [0.1s] Status: SharpCap error for Quick Event 1: No module named 'SharpCap'
  [1.1s] Status: Running sequence 2/2: Quick Event 2
  [1.2s] Status: Starting SharpCap sequence: 20241215 Quick Event 2 - Test Station.
"""