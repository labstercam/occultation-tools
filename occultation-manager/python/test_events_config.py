# test_events_config.py - Test config dependencies

import os
import sys

# Mock the config module
class MockConfig:
    def __init__(self):
        self.test_folder = os.path.join(os.getcwd(), 'temp_test')
        if not os.path.exists(self.test_folder):
            os.makedirs(self.test_folder)
    
    def get_file_folder(self):
        return self.test_folder
    
    def get_full_file_path(self, filename):
        return os.path.join(self.test_folder, filename)
    
    def get_base_duration(self):
        return 60
    
    def get_goto_lead_time(self):
        return 240
    
    def get_mag_for_40ms_exposure(self):
        return 12.0

# Test imports
try:
    # Add current directory to path
    sys.path.insert(0, os.getcwd())
    
    # Try importing events module
    from events import EventProcessor, OccultationEvent
    print("✓ Events module imports successfully")
    
    # Test basic functionality
    config = MockConfig()
    processor = EventProcessor(config)
    print("✓ EventProcessor creates successfully")
    
    # Test with minimal event data
    minimal_event = {
        'name': 'Test Event',
        'station_name': 'Test Station',
        'event_time': '2024-01-15T12:00:00',
        'start_time': '2024-01-15T11:59:30',
        'end_time': '2024-01-15T12:00:30',
        'goto_time': '2024-01-15T11:55:00',
        'ra': 12.5,
        'dec': 45.0,
        'star_mag': 11.0,
        'comb_mag': 10.8,
        'mag_drop': 1.2,
        'event_duration': 10.0,
        'event_uncertainty': 2.0,
        'recording_duration': 60,
        'exposure': 0.05
    }
    
    event = OccultationEvent(minimal_event, config)
    print("✓ OccultationEvent creates successfully")
    print(f"  Event name: {event.event_name}")
    print(f"  Exposure: {event.exposure_ms}ms")
    
    # Cleanup
    import shutil
    if os.path.exists(config.test_folder):
        shutil.rmtree(config.test_folder)
    
    print("✓ Basic functionality test passed!")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Check that events.py exists and has correct imports")
except Exception as e:
    print(f"❌ Runtime error: {e}")
    import traceback
    traceback.print_exc()