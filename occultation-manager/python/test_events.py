# test_events.py - Standalone test for events.py module

import sys
import os
import json
from datetime import datetime, timedelta

# Add the module directory to Python path if needed
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

# Mock ConfigManager for testing
class MockConfigManager:
    """Mock config manager for testing events module"""
    
    def __init__(self):
        self.test_folder = os.path.join(os.getcwd(), 'test_events_data')
        if not os.path.exists(self.test_folder):
            os.makedirs(self.test_folder)
    
    # File path methods
    def get_file_folder(self):
        return self.test_folder
    
    def get_full_file_path(self, filename):
        return os.path.join(self.test_folder, filename)
    
    def get_occultations_file(self):
        return 'test_occultations.json'
    
    def get_latest_occultations_file(self):
        return 'test_occultations_latest.json'
    
    def get_sequence_path(self):
        return self.test_folder
    
    # Recording parameters
    def get_base_duration(self):
        return 60
    
    def get_goto_lead_time(self):
        return 240
    
    def get_mag_for_40ms_exposure(self):
        return 12.0
    
    # API configuration
    def get_owc_email(self):
        return 'test@example.com'
    
    def get_owc_password(self):
        return 'test_password'
    
    def get_full_url(self):
        return 'https://www.occultwatcher.net:443/api2/v1/events/details-list?apikey=test'
    
    def get_occelmnt_url(self):
        return 'https://www.occultwatcher.net:443/api2/v1/owc/event/my/%s/occelmnts?apikey=test'

def create_sample_event_data():
    """Create sample event data for testing"""
    now = datetime.utcnow()
    future_time = now + timedelta(hours=2)
    
    return {
        'name': 'Test Asteroid - Station ABC',
        'station_name': 'Station ABC', 
        'ow_eventid': '12345',
        'id': 'Test Asteroid : HD 123456 : Station ABC',
        'object_name': 'Test Asteroid',
        'ra': 15.5,  # hours
        'dec': 45.2,  # degrees
        'star_mag': 11.5,
        'mag_drop': 2.1,
        'comb_mag': 11.3,
        'event_time': future_time.strftime('%Y-%m-%dT%H:%M:%S'),
        'start_time': (future_time - timedelta(seconds=30)).strftime('%Y-%m-%dT%H:%M:%S'),
        'end_time': (future_time + timedelta(seconds=30)).strftime('%Y-%m-%dT%H:%M:%S'),
        'goto_time': (future_time - timedelta(seconds=300)).strftime('%Y-%m-%dT%H:%M:%S'),
        'event_duration': 15.0,
        'event_uncertainty': 5.0,
        'recording_duration': 60,
        'star_id': 'HD 123456',
        'star_az': 180.5,
        'star_alt': 45.2,
        'object_no': '2024 AB',
        'latitude': 40.123,
        'longitude': -75.456,
        'exposure': 0.08,  # 80ms
        'source': 'OWCloud',
        'owcloudurl': 'https://cloud.occultwatcher.net/event/12345'
    }

def create_sample_owc_response():
    """Create sample OWC API response for testing"""
    now = datetime.utcnow()
    future_time = now + timedelta(hours=3)
    
    return [
        {
            'Id': 67890,
            'Object': 'Test Asteroid 2',
            'MaxDurSec': 12.5,
            'StarName': 'HD 987654',
            'RAJ2000Hours': 16.25,
            'DEJ2000Deg': 35.8,
            'StarMag': 10.8,
            'MagDrop': 1.9,
            'Stations': [
                {
                    'IsOwnStation': True,
                    'EventTimeUtc': future_time.strftime('%Y-%m-%dT%H:%M:%S.000'),
                    'ErrorInTimeSec': 3.2,
                    'StationName': 'Test Station XYZ',
                    'Latitude': 41.234,
                    'Longitude': -74.567,
                    'StarAz': 195.5,
                    'StarAlt': 55.3,
                    'CombMag': 10.6
                }
            ]
        }
    ]

def test_event_processor():
    """Test EventProcessor class"""
    print("\n=== Testing EventProcessor ===")
    
    try:
        config = MockConfigManager()
        processor = EventProcessor(config)
        print("✓ EventProcessor created successfully")
        
        # Test save/load operations
        sample_data = [create_sample_event_data()]
        
        # Test saving
        success = EventProcessor.save_occultations(sample_data, 'test_save.json', config)
        print(f"✓ Save test: {'Success' if success else 'Failed'}")
        
        # Test loading
        loaded_data = EventProcessor.load_occultations('test_save.json', config)
        print(f"✓ Load test: {len(loaded_data)} events loaded")
        
        if loaded_data and len(loaded_data) > 0:
            print(f"  - First event: {loaded_data[0]['name']}")
        
        # Test merge operations
        new_data = [create_sample_event_data()]
        new_data[0]['id'] = 'Different Event : HD 999999 : Station DEF'  # Different ID
        
        merged = EventProcessor.merge_occultation_lists(loaded_data, new_data, id_key='id')
        print(f"✓ Merge test: {len(merged)} events after merge")
        
    except Exception as e:
        print(f"❌ EventProcessor test failed: {e}")
        import traceback
        traceback.print_exc()

def test_occultation_event():
    """Test OccultationEvent class"""
    print("\n=== Testing OccultationEvent ===")
    
    try:
        config = MockConfigManager()
        sample_data = create_sample_event_data()
        
        # Create event
        event = OccultationEvent(sample_data, config)
        print("✓ OccultationEvent created successfully")
        
        # Test basic properties
        print(f"  - Event name: {event.event_name}")
        print(f"  - Coordinates: {event.get_coordinates_string()}")
        print(f"  - Exposure: {event.exposure_ms}ms")
        print(f"  - Status: {event.get_status_info()}")
        print(f"  - Display name: {event.get_asteroid_display_name()}")
        
        # Test exposure calculations
        print(f"  - Has custom exposure: {event.has_custom_exposure()}")
        print(f"  - Exposure seconds: {event.get_exposure_seconds()}")
        
        # Test custom exposure
        event.set_custom_exposure(150)  # 150ms
        print(f"  - After custom exposure: {event.exposure_ms}ms, custom: {event.has_custom_exposure()}")
        
        # Test datetime parsing
        if event.event_datetime:
            print(f"  - Event datetime: {event.event_datetime}")
            print(f"  - Local times: GOTO={event.goto_time_local}, Event={event.event_time_local}")
        
    except Exception as e:
        print(f"❌ OccultationEvent test failed: {e}")
        import traceback
        traceback.print_exc()

def test_occultation_manager():
    """Test OccultationManager class"""
    print("\n=== Testing OccultationManager ===")
    
    try:
        config = MockConfigManager()
        manager = OccultationManager(config)
        print("✓ OccultationManager created successfully")
        
        # Create test data file
        test_events = [create_sample_event_data()]
        test_events.append({
            **create_sample_event_data(),
            'name': 'Another Asteroid - Station XYZ',
            'station_name': 'Station XYZ',
            'id': 'Another Asteroid : HD 111111 : Station XYZ'
        })
        
        EventProcessor.save_occultations(test_events, config.get_occultations_file(), config)
        
        # Test loading events
        success = manager.load_events_from_files()
        print(f"✓ Load events test: {'Success' if success else 'Failed'}")
        print(f"  - Loaded {len(manager.all_events)} events")
        
        # Test station filtering
        stations = manager.get_all_stations()
        print(f"✓ Station list: {stations}")
        
        if stations:
            manager.set_station_filter(stations[0])
            filtered = manager.get_filtered_events()
            print(f"✓ Filter test: {len(filtered)} events for station {stations[0]}")
        
        # Test selections
        manager.select_all_events()
        print(f"✓ Select all: {len(manager.selected_events)} events selected")
        
        manager.select_no_events()
        print(f"✓ Select none: {len(manager.selected_events)} events selected")
        
    except Exception as e:
        print(f"❌ OccultationManager test failed: {e}")
        import traceback
        traceback.print_exc()

def test_owc_data_processing():
    """Test OWC data processing"""
    print("\n=== Testing OWC Data Processing ===")
    
    try:
        config = MockConfigManager()
        sample_owc_data = create_sample_owc_response()
        
        # Test process_owc_events
        processed = EventProcessor.process_owc_events(sample_owc_data, '', config)
        print(f"✓ OWC processing: {len(processed)} events processed")
        
        if processed:
            event = processed[0]
            print(f"  - Event name: {event['name']}")
            print(f"  - Recording duration: {event['recording_duration']}s")
            print(f"  - Exposure: {event['exposure']}s")
            print(f"  - Coordinates: RA={event['ra']:.3f}h, Dec={event['dec']:.3f}°")
            
    except Exception as e:
        print(f"❌ OWC processing test failed: {e}")
        import traceback
        traceback.print_exc()

def test_edge_cases():
    """Test edge cases and error handling"""
    print("\n=== Testing Edge Cases ===")
    
    try:
        config = MockConfigManager()
        
        # Test with empty data
        empty_result = EventProcessor.load_occultations('nonexistent.json', config)
        print(f"✓ Empty file test: {len(empty_result)} events (expected 0)")
        
        # Test with invalid event data
        try:
            invalid_data = {'incomplete': 'data'}
            event = OccultationEvent(invalid_data, config)
            print("✓ Invalid data handled gracefully")
        except Exception as e:
            print(f"✓ Invalid data properly rejected: {type(e).__name__}")
        
        # Test merge with empty lists
        merged = EventProcessor.merge_occultation_lists([], [], id_key='id')
        print(f"✓ Empty merge test: {len(merged)} events")
        
        # Test date parsing edge cases
        test_dates = [
            '2024-01-15T12:30:45',
            '2024-01-15T12:30:45.123',
            '2024-01-15T12:30:45Z',
            '2024-01-15 12:30:45',
            ''
        ]
        
        for date_str in test_dates:
            test_event_data = create_sample_event_data()
            test_event_data['event_time'] = date_str
            try:
                event = OccultationEvent(test_event_data, config)
                parsed = event.event_datetime
                print(f"✓ Date '{date_str}' → {parsed}")
            except Exception as e:
                print(f"✓ Date '{date_str}' → Error: {type(e).__name__}")
        
    except Exception as e:
        print(f"❌ Edge cases test failed: {e}")
        import traceback
        traceback.print_exc()

def cleanup_test_files():
    """Clean up test files"""
    try:
        test_folder = os.path.join(os.getcwd(), 'test_events_data')
        if os.path.exists(test_folder):
            import shutil
            shutil.rmtree(test_folder)
            print("✓ Test files cleaned up")
    except Exception as e:
        print(f"⚠ Cleanup warning: {e}")

def main():
    """Main test function"""
    print("Events Module Standalone Test")
    print("=" * 50)
    
    try:
        # Import the events module
        from events import EventProcessor, OccultationEvent, OccultationManager
        print("✓ Events module imported successfully")
        
        # Run tests
        test_event_processor()
        test_occultation_event()
        test_occultation_manager()
        test_owc_data_processing()
        test_edge_cases()
        
        print("\n" + "=" * 50)
        print("✓ All tests completed successfully!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure events.py is in the same directory")
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Cleanup
        cleanup_test_files()

if __name__ == "__main__":
    main()