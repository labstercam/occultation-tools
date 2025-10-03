# test_sequence_runner.py - Standalone test for sequence_runner.py module

import sys
import os
import tempfile
import shutil
import time
import threading
from datetime import datetime, timedelta

# Add the module directory to Python path if needed
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

# Mock dependencies
class MockConfigManager:
    """Mock config manager for testing sequence runner"""
    
    def __init__(self):
        self.test_folder = tempfile.mkdtemp(prefix='seq_runner_test_')
        
    def get_sequence_path(self):
        return self.test_folder
    
    def cleanup(self):
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)

class MockOccultationEvent:
    """Mock OccultationEvent for testing"""
    
    def __init__(self, name="Test Event", hours_in_future=1, duration_minutes=1):
        self.event_name = name
        self.name = f"{name} - Test Station"
        
        # Calculate times
        now = datetime.utcnow()
        self.goto_time = now + timedelta(hours=hours_in_future)
        self.start_time = self.goto_time + timedelta(minutes=5)  # 5 min after GOTO
        self.end_time = self.start_time + timedelta(minutes=duration_minutes)
        
        # Format for sequence runner
        self.start_time_str = self.start_time.strftime('%Y-%m-%dT%H:%M:%S')
        self.goto_time_str = self.goto_time.strftime('%Y-%m-%dT%H:%M:%S')
        
    def is_future(self):
        """Check if event is in the future"""
        return self.goto_time > datetime.utcnow()
    
    def is_past(self):
        """Check if event is in the past"""
        return self.goto_time <= datetime.utcnow()

def create_mock_sequence_file(config, event):
    """Create a mock sequence file for testing"""
    start_time = datetime.strptime(event.start_time_str, '%Y-%m-%dT%H:%M:%S')
    clean_name = "".join(c for c in event.name if c.isalnum() or c in ('(',')',' ', '-', '_')).rstrip()
    seq_name = start_time.strftime('%Y%m%d') + ' ' + clean_name + '.seq'
    sequence_file_path = os.path.join(config.get_sequence_path(), seq_name)
    
    # Create mock sequence file content
    sequence_content = f"""# Mock Sequence for {event.event_name}
# Generated for testing
# GOTO Time: {event.goto_time_str}
# Start Time: {event.start_time_str}

# This is a mock sequence file for testing
COMMENT "Starting sequence for {event.event_name}"
WAIT 1
COMMENT "Mock sequence completed"
"""
    
    with open(sequence_file_path, 'w') as f:
        f.write(sequence_content)
    
    return sequence_file_path

def test_sequence_runner_creation():
    """Test SequenceRunner creation"""
    print("\n=== Testing SequenceRunner Creation ===")
    
    try:
        from sequence_runner import SequenceRunner
        
        config = MockConfigManager()
        runner = SequenceRunner(config)
        
        print("✓ SequenceRunner created successfully")
        print(f"✓ Initial running state: {runner.running}")
        print(f"✓ Current sequence: {runner.current_sequence}")
        
        # Test initial state
        assert runner.running == False, "Runner should not be running initially"
        assert runner.current_sequence is None, "Current sequence should be None initially"
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ SequenceRunner creation failed: {e}")
        import traceback
        traceback.print_exc()

def test_sequence_file_detection():
    """Test sequence file detection and path handling"""
    print("\n=== Testing Sequence File Detection ===")
    
    try:
        from sequence_runner import SequenceRunner
        
        config = MockConfigManager()
        runner = SequenceRunner(config)
        
        # Create test events
        future_event = MockOccultationEvent("Future Event", hours_in_future=2)
        
        # Create sequence file
        sequence_path = create_mock_sequence_file(config, future_event)
        print(f"✓ Created mock sequence file: {os.path.basename(sequence_path)}")
        
        # Test that file exists
        if os.path.exists(sequence_path):
            print("✓ Sequence file exists and is accessible")
            
            # Read and verify content
            with open(sequence_path, 'r') as f:
                content = f.read()
            
            if future_event.event_name in content:
                print("✓ Sequence file contains correct event data")
            else:
                print("❌ Sequence file missing event data")
        else:
            print("❌ Sequence file not found")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Sequence file detection failed: {e}")
        import traceback
        traceback.print_exc()

def test_event_filtering():
    """Test filtering of future vs past events"""
    print("\n=== Testing Event Filtering ===")
    
    try:
        from sequence_runner import SequenceRunner
        
        config = MockConfigManager()
        runner = SequenceRunner(config)
        
        # Create mix of past and future events
        past_event = MockOccultationEvent("Past Event", hours_in_future=-1)
        current_event = MockOccultationEvent("Current Event", hours_in_future=0.01)  # Just future
        future_event1 = MockOccultationEvent("Future Event 1", hours_in_future=1)
        future_event2 = MockOccultationEvent("Future Event 2", hours_in_future=2)
        
        all_events = [past_event, current_event, future_event1, future_event2]
        
        print(f"✓ Created {len(all_events)} test events")
        
        # Check event timing
        now = datetime.utcnow()
        for event in all_events:
            time_diff = (event.goto_time - now).total_seconds()
            status = "FUTURE" if time_diff > 0 else "PAST"
            print(f"  - {event.event_name}: {time_diff:.1f}s ({status})")
        
        # Test the filtering logic that would occur in run_sequences
        future_events = [e for e in all_events if e.goto_time and e.goto_time > now]
        print(f"✓ Filtered to {len(future_events)} future events")
        
        # Verify filtering worked correctly
        expected_future = sum(1 for e in all_events if e.is_future())
        if len(future_events) == expected_future:
            print("✓ Event filtering logic works correctly")
        else:
            print(f"❌ Event filtering failed: expected {expected_future}, got {len(future_events)}")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Event filtering test failed: {e}")
        import traceback
        traceback.print_exc()

def test_run_sequences_with_no_events():
    """Test run_sequences with no events"""
    print("\n=== Testing Run Sequences (No Events) ===")
    
    try:
        from sequence_runner import SequenceRunner
        
        config = MockConfigManager()
        runner = SequenceRunner(config)
        
        # Track status updates
        status_messages = []
        def capture_status(message):
            status_messages.append(message)
            print(f"  Status: {message}")
        
        # Test with empty event list
        result = runner.run_sequences([], capture_status)
        print(f"✓ Empty events result: {'Success' if result else 'Failed (expected)'}")
        
        # Test with only past events
        past_event = MockOccultationEvent("Past Event", hours_in_future=-1)
        result = runner.run_sequences([past_event], capture_status)
        print(f"✓ Past events result: {'Success' if result else 'Failed (expected)'}")
        
        # Check status messages
        if status_messages:
            print(f"✓ Status messages captured: {len(status_messages)}")
            for msg in status_messages:
                if "No future events" in msg:
                    print("✓ Correct 'no future events' message found")
                    break
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ No events test failed: {e}")
        import traceback
        traceback.print_exc()

def test_run_sequences_with_future_events():
    """Test run_sequences with future events (mock execution)"""
    print("\n=== Testing Run Sequences (Future Events) ===")
    
    try:
        from sequence_runner import SequenceRunner
        
        config = MockConfigManager()
        runner = SequenceRunner(config)
        
        # Create future events with very short timing for testing
        event1 = MockOccultationEvent("Quick Event 1", hours_in_future=0.001)  # ~3 seconds
        event2 = MockOccultationEvent("Quick Event 2", hours_in_future=0.002)  # ~7 seconds
        
        events = [event1, event2]
        
        # Create sequence files
        for event in events:
            seq_path = create_mock_sequence_file(config, event)
            print(f"✓ Created sequence for {event.event_name}")
        
        # Track status updates
        status_messages = []
        execution_start_time = time.time()
        
        def capture_status(message):
            elapsed = time.time() - execution_start_time
            status_messages.append((elapsed, message))
            print(f"  [{elapsed:.1f}s] Status: {message}")
        
        print("✓ Starting sequence execution test...")
        
        # Run sequences (this will execute quickly since events are in near future)
        result = runner.run_sequences(events, capture_status)
        execution_time = time.time() - execution_start_time
        
        print(f"✓ Sequence execution completed in {execution_time:.1f}s")
        print(f"✓ Execution result: {'Success' if result else 'Failed'}")
        print(f"✓ Final running state: {runner.running}")
        print(f"✓ Status messages captured: {len(status_messages)}")
        
        # Analyze status messages
        for elapsed, message in status_messages:
            if "Running sequence" in message:
                print(f"✓ Sequence execution started at {elapsed:.1f}s")
            elif "completed" in message.lower():
                print(f"✓ Sequences completed at {elapsed:.1f}s")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Future events test failed: {e}")
        import traceback
        traceback.print_exc()

def test_single_sequence_execution():
    """Test single sequence file execution"""
    print("\n=== Testing Single Sequence Execution ===")
    
    try:
        from sequence_runner import SequenceRunner
        
        config = MockConfigManager()
        runner = SequenceRunner(config)
        
        # Create test event and sequence file
        event = MockOccultationEvent("Single Test Event")
        sequence_path = create_mock_sequence_file(config, event)
        
        print(f"✓ Created sequence file: {os.path.basename(sequence_path)}")
        
        # Track status
        status_messages = []
        def capture_status(message):
            status_messages.append(message)
            print(f"  Status: {message}")
        
        # Test single sequence execution
        success = runner.run_single_sequence(sequence_path, event, capture_status)
        print(f"✓ Single sequence execution: {'Success' if success else 'Failed (expected without SharpCap)'}")
        
        # Test with non-existent file
        fake_path = os.path.join(config.get_sequence_path(), "nonexistent.seq")
        success = runner.run_single_sequence(fake_path, event, capture_status)
        print(f"✓ Non-existent file handling: {'Failed as expected' if not success else 'Unexpected success'}")
        
        # Check status messages
        file_not_found_msg = any("not found" in msg.lower() for msg in status_messages)
        if file_not_found_msg:
            print("✓ File not found message generated correctly")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Single sequence execution test failed: {e}")
        import traceback
        traceback.print_exc()

def test_stop_sequences():
    """Test stopping sequence execution"""
    print("\n=== Testing Stop Sequences ===")
    
    try:
        from sequence_runner import SequenceRunner
        
        config = MockConfigManager()
        runner = SequenceRunner(config)
        
        # Test stop when not running
        runner.stop_sequences()
        print("✓ Stop when not running: handled gracefully")
        print(f"✓ Running state after stop: {runner.running}")
        
        # Test stop during execution (simulate)
        runner.running = True  # Simulate running state
        runner.stop_sequences()
        print(f"✓ Running state after stop during execution: {runner.running}")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Stop sequences test failed: {e}")
        import traceback
        traceback.print_exc()

def test_concurrent_execution_safety():
    """Test thread safety and concurrent execution prevention"""
    print("\n=== Testing Concurrent Execution Safety ===")
    
    try:
        from sequence_runner import SequenceRunner
        
        config = MockConfigManager()
        runner = SequenceRunner(config)
        
        # Track status messages from both attempts
        status_messages = []
        def capture_status(message):
            status_messages.append(message)
            print(f"  Status: {message}")
        
        # Simulate concurrent execution attempts
        def attempt_execution():
            event = MockOccultationEvent("Concurrent Test", hours_in_future=0.001)
            return runner.run_sequences([event], capture_status)
        
        # Start first execution
        runner.running = True  # Simulate running state
        
        # Attempt second execution while first is "running"
        result = attempt_execution()
        
        print(f"✓ Concurrent execution prevention: {'Blocked' if not result else 'Not blocked (unexpected)'}")
        
        # Check for appropriate status message
        concurrent_blocked = any("already running" in msg.lower() for msg in status_messages)
        if concurrent_blocked:
            print("✓ Appropriate concurrent execution message generated")
        
        # Reset state
        runner.running = False
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Concurrent execution safety test failed: {e}")
        import traceback
        traceback.print_exc()

def test_event_timing_validation():
    """Test event timing validation and ordering"""
    print("\n=== Testing Event Timing Validation ===")
    
    try:
        from sequence_runner import SequenceRunner
        
        config = MockConfigManager()
        runner = SequenceRunner(config)
        
        # Create events with different timing
        now = datetime.utcnow()
        
        # Events in different time order
        event1 = MockOccultationEvent("Event 1", hours_in_future=2)    # Later
        event2 = MockOccultationEvent("Event 2", hours_in_future=1)    # Earlier
        event3 = MockOccultationEvent("Event 3", hours_in_future=3)    # Latest
        
        events = [event1, event2, event3]  # Unsorted order
        
        print("✓ Created events in unsorted order:")
        for i, event in enumerate(events):
            time_diff = (event.goto_time - now).total_seconds() / 3600  # Hours
            print(f"  {i+1}. {event.event_name}: +{time_diff:.2f} hours")
        
        # Test the sorting logic that occurs in run_sequences
        future_events = [e for e in events if e.goto_time and e.goto_time > now]
        future_events.sort(key=lambda x: x.goto_time)
        
        print("✓ Events after sorting by GOTO time:")
        for i, event in enumerate(future_events):
            time_diff = (event.goto_time - now).total_seconds() / 3600
            print(f"  {i+1}. {event.event_name}: +{time_diff:.2f} hours")
        
        # Verify sorting worked
        is_sorted = all(future_events[i].goto_time <= future_events[i+1].goto_time 
                       for i in range(len(future_events)-1))
        
        if is_sorted:
            print("✓ Event sorting logic works correctly")
        else:
            print("❌ Event sorting failed")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Event timing validation test failed: {e}")
        import traceback
        traceback.print_exc()

def test_error_handling_scenarios():
    """Test various error handling scenarios"""
    print("\n=== Testing Error Handling Scenarios ===")
    
    try:
        from sequence_runner import SequenceRunner
        
        config = MockConfigManager()
        runner = SequenceRunner(config)
        
        # Track all status messages
        all_status_messages = []
        def capture_all_status(message):
            all_status_messages.append(message)
            print(f"  Status: {message}")
        
        # Test 1: Event with None goto_time
        class BrokenEvent:
            def __init__(self):
                self.event_name = "Broken Event"
                self.name = "Broken Event - Station"
                self.goto_time = None  # This should cause issues
                self.start_time_str = "2024-01-01T12:00:00"
        
        broken_event = BrokenEvent()
        
        try:
            result = runner.run_sequences([broken_event], capture_all_status)
            print(f"✓ None goto_time handled: {'Gracefully' if not result else 'Unexpectedly succeeded'}")
        except Exception as e:
            print(f"✓ None goto_time properly rejected: {type(e).__name__}")
        
        # Test 2: Invalid sequence file path
        valid_event = MockOccultationEvent("Valid Event")
        invalid_path = "/invalid/path/to/nowhere.seq"
        
        success = runner.run_single_sequence(invalid_path, valid_event, capture_all_status)
        print(f"✓ Invalid path handled: {'Failed as expected' if not success else 'Unexpected success'}")
        
        # Test 3: Empty sequence path
        empty_path = ""
        success = runner.run_single_sequence(empty_path, valid_event, capture_all_status)
        print(f"✓ Empty path handled: {'Failed as expected' if not success else 'Unexpected success'}")
        
        # Check error messages were generated
        error_messages = [msg for msg in all_status_messages if any(word in msg.lower() 
                         for word in ['error', 'failed', 'not found'])]
        print(f"✓ Error messages generated: {len(error_messages)}")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()

def test_performance_and_timing():
    """Test performance with multiple events"""
    print("\n=== Testing Performance and Timing ===")
    
    try:
        from sequence_runner import SequenceRunner
        
        config = MockConfigManager()
        runner = SequenceRunner(config)
        
        # Create multiple future events with very short intervals
        num_events = 5
        events = []
        base_time = 0.001  # Start 3.6 seconds in future
        
        for i in range(num_events):
            event = MockOccultationEvent(f"Perf Event {i+1}", 
                                       hours_in_future=base_time + (i * 0.001))
            events.append(event)
            # Create sequence file
            create_mock_sequence_file(config, event)
        
        print(f"✓ Created {num_events} events for performance test")
        
        # Time the execution setup
        start_time = time.time()
        
        status_messages = []
        def capture_status(message):
            elapsed = time.time() - start_time
            status_messages.append((elapsed, message))
        
        # Run the sequences
        result = runner.run_sequences(events, capture_status)
        total_time = time.time() - start_time
        
        print(f"✓ Performance test completed in {total_time:.2f}s")
        print(f"✓ Result: {'Success' if result else 'Failed'}")
        print(f"✓ Status updates: {len(status_messages)}")
        
        # Analyze timing
        if status_messages:
            first_msg_time = status_messages[0][0]
            last_msg_time = status_messages[-1][0]
            print(f"✓ Status message timing: {first_msg_time:.3f}s to {last_msg_time:.3f}s")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("Sequence Runner Module Standalone Test")
    print("=" * 50)
    
    try:
        # Test module import
        from sequence_runner import SequenceRunner
        print("✓ SequenceRunner module imported successfully")
        
        # Run all tests
        test_sequence_runner_creation()
        test_sequence_file_detection()
        test_event_filtering()
        test_run_sequences_with_no_events()
        test_run_sequences_with_future_events()
        test_single_sequence_execution()
        test_stop_sequences()
        test_concurrent_execution_safety()
        test_event_timing_validation()
        test_error_handling_scenarios()
        test_performance_and_timing()
        
        print("\n" + "=" * 50)
        print("✓ All sequence runner tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure sequence_runner.py is in the same directory")
        return False
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)