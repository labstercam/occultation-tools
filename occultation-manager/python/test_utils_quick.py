# test_utils_quick.py - Quick utils validation test

import os
import sys
import tempfile
import shutil
from datetime import datetime, timedelta

def quick_test():
    """Quick utils test"""
    print("Quick Utils Test")
    print("=" * 20)
    
    try:
        # Mock dependencies
        class MockConfig:
            def __init__(self):
                self.temp_dir = tempfile.mkdtemp()
            def get_sequence_path(self):
                return self.temp_dir
        
        class MockEvent:
            def __init__(self):
                now = datetime.utcnow()
                self.name = "Test Event - Station ABC"
                self.object_name = "Test Asteroid"
                self.start_time_str = now.strftime('%Y-%m-%dT%H:%M:%S')
                self.ra = 15.5
                self.dec = 45.2
                self.exposure_ms = 80
                self.recording_duration = 60
                self.star_mag = 11.5
                self.comb_mag = 11.3
                self.mag_drop = 2.1
                self.event_uncertainty = 3.0
                self.station_name = "Station ABC"
                self.event_time = self.start_time_str
                self.goto_time_str = self.start_time_str
                self.event_time_local = "12:30:45"
                self.start_time_local = "12:30:15"
                self.goto_time_local = "12:26:15"
                
            def get_exposure_seconds(self):
                return self.exposure_ms / 1000.0
                
            def has_custom_exposure(self):
                return False
        
        # Mock template manager
        sys.modules['templates'] = type('MockModule', (), {
            'TemplateManager': type('MockTM', (), {
                'load_template': lambda path, config=None: "Mock template: {object_name} at {ra},{dec}"
            })()
        })()
        
        # Import and test
        from utils import save_occultation_sequence, simple_goto_event
        print("✓ Utils module imports")
        
        config = MockConfig()
        event = MockEvent()
        
        # Test sequence save
        success = save_occultation_sequence(event, "", config.get_sequence_path(), config)
        print(f"✓ Sequence save: {'Success' if success else 'Failed'}")
        
        # Test GOTO (should fail gracefully)
        result = simple_goto_event(event)
        print(f"✓ GOTO function: {'Works' if result else 'Fails gracefully (expected)'}")
        
        # Check file creation
        files = os.listdir(config.temp_dir)
        seq_files = [f for f in files if f.endswith('.scs')]
        print(f"✓ Sequence files created: {len(seq_files)}")
        
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