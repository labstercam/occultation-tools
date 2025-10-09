# test_utils.py - Standalone test for utils.py module

import sys
import os
import tempfile
import shutil
from datetime import datetime, timedelta

# Add the module directory to Python path if needed
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

# Mock dependencies
class MockConfigManager:
    """Mock config manager for testing utils module"""
    
    def __init__(self):
        self.test_folder = tempfile.mkdtemp(prefix='utils_test_')
        
    def get_sequence_path(self):
        return self.test_folder
    
    def get_file_folder(self):
        return self.test_folder
    
    def get_full_file_path(self, filename):
        return os.path.join(self.test_folder, filename)

class MockOccultationEvent:
    """Mock OccultationEvent for testing"""
    
    def __init__(self, event_data=None):
        if event_data is None:
            event_data = self.create_default_event_data()
        
        # Parse event data
        self.name = event_data.get('name', 'Test Event')
        self.object_name = event_data.get('object_name', 'Test Asteroid')
        self.event_time = event_data.get('event_time', '')
        self.start_time_str = event_data.get('start_time', '')
        self.end_time_str = event_data.get('end_time', '')
        self.goto_time_str = event_data.get('goto_time', '')
        self.recording_duration = event_data.get('recording_duration', 60)
        self.star_mag = event_data.get('star_mag', 11.5)
        self.comb_mag = event_data.get('comb_mag', 11.3)
        self.mag_drop = event_data.get('mag_drop', 2.1)
        self.event_uncertainty = event_data.get('event_uncertainty', 3.0)
        self.ra = event_data.get('ra', 15.5)
        self.dec = event_data.get('dec', 45.2)
        self.station_name = event_data.get('station_name', 'Test Station')
        self.exposure_ms = event_data.get('exposure_ms', 80)
        self.custom_exposure = None
        
        # Calculate local times (simplified)
        self.event_time_local = event_data.get('event_time_local', '12:30:45')
        self.start_time_local = event_data.get('start_time_local', '12:30:15')
        self.goto_time_local = event_data.get('goto_time_local', '12:26:15')
    
    def create_default_event_data(self):
        """Create default event data"""
        now = datetime.utcnow()
        event_time = now + timedelta(hours=2)
        start_time = event_time - timedelta(seconds=30)
        end_time = event_time + timedelta(seconds=30)
        goto_time = event_time - timedelta(seconds=300)
        
        return {
            'name': 'Test Asteroid - Test Station',
            'object_name': 'Test Asteroid',
            'event_time': event_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'start_time': start_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'end_time': end_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'goto_time': goto_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'recording_duration': 60,
            'star_mag': 11.5,
            'comb_mag': 11.3,
            'mag_drop': 2.1,
            'event_uncertainty': 3.0,
            'ra': 15.5,
            'dec': 45.2,
            'station_name': 'Test Station',
            'exposure_ms': 80
        }
    
    def get_exposure_seconds(self):
        """Get exposure in seconds"""
        return self.exposure_ms / 1000.0
    
    def has_custom_exposure(self):
        """Check if has custom exposure"""
        return self.custom_exposure is not None

class MockTemplateManager:
    """Mock TemplateManager for testing"""
    
    @staticmethod
    def load_template(template_path, config=None):
        """Return a mock template"""
        if template_path and 'error' in template_path.lower():
            return None  # Simulate template not found
        
        return """# Mock Template for {object_name}
# Event time: {event_time} UTC
# GOTO time: {goto_time} UTC
# Local GOTO time: {goto_time_local}

GOTO {ra} {dec}
WAIT UNTIL {goto_time_local}
SET EXPOSURE {exposure}
START RECORDING {recording_duration}
STOP RECORDING

# Event details:
# Star magnitude: {star_mag}
# Combined magnitude: {comb_mag}
# Magnitude drop: {mag_drop}
# Time error: {time_error} seconds
# Station: {station_name}
"""

def test_save_occultation_sequence_with_event_object():
    """Test save_occultation_sequence with OccultationEvent object"""
    print("\n=== Testing save_occultation_sequence (Event Object) ===")
    
    try:
        # Mock the templates module
        sys.modules['templates'] = type('MockModule', (), {
            'TemplateManager': MockTemplateManager
        })()
        
        from utils import save_occultation_sequence
        
        config = MockConfigManager()
        event = MockOccultationEvent()
        
        # Test with default template
        success = save_occultation_sequence(event, "", config.get_sequence_path(), config)
        print(f"✓ Save with event object: {'Success' if success else 'Failed'}")
        
        if success:
            # Check if file was created
            start_time = datetime.strptime(event.start_time_str, '%Y-%m-%dT%H:%M:%S')
            clean_name = "".join(c for c in event.name if c.isalnum() or c in ('(',')',' ', '-', '_')).rstrip()
            expected_filename = start_time.strftime('%Y%m%d') + ' ' + clean_name + '.scs'
            expected_path = os.path.join(config.get_sequence_path(), expected_filename)
            
            if os.path.exists(expected_path):
                print(f"✓ Sequence file created: {expected_filename}")
                
                # Check file contents
                with open(expected_path, 'r') as f:
                    content = f.read()
                
                print(f"✓ File size: {len(content)} characters")
                
                # Check template substitution
                checks = [
                    (event.object_name, 'object name'),
                    (str(event.ra), 'RA coordinate'),
                    (str(event.dec), 'Dec coordinate'),
                    (str(event.get_exposure_seconds()), 'exposure'),
                    (str(event.recording_duration), 'recording duration'),
                    (event.goto_time_local, 'local GOTO time')
                ]
                
                for value, description in checks:
                    if value in content:
                        print(f"✓ Template substitution - {description}: {value}")
                    else:
                        print(f"❌ Template substitution - {description}: '{value}' not found")
                
            else:
                print(f"❌ Sequence file not found: {expected_path}")
        
        # Cleanup
        shutil.rmtree(config.test_folder)
        
    except Exception as e:
        print(f"❌ Event object test failed: {e}")
        import traceback
        traceback.print_exc()

def test_save_occultation_sequence_with_dict():
    """Test save_occultation_sequence with dictionary object"""
    print("\n=== Testing save_occultation_sequence (Dictionary) ===")
    
    try:
        # Mock the templates module
        sys.modules['templates'] = type('MockModule', (), {
            'TemplateManager': MockTemplateManager
        })()
        
        from utils import save_occultation_sequence
        
        config = MockConfigManager()
        
        # Create dictionary event data (legacy format)
        now = datetime.utcnow()
        future_time = now + timedelta(hours=1)
        
        event_dict = {
            'name': 'Dictionary Asteroid - Station XYZ',
            'object_name': 'Dictionary Asteroid',
            'event_time': future_time.strftime('%Y-%m-%dT%H:%M:%S'),
            'start_time': (future_time - timedelta(seconds=30)).strftime('%Y-%m-%dT%H:%M:%S'),
            'goto_time': (future_time - timedelta(seconds=300)).strftime('%Y-%m-%dT%H:%M:%S'),
            'recording_duration': 90,
            'star_mag': 12.1,
            'comb_mag': 11.9,
            'mag_drop': 1.8,
            'event_uncertainty': 2.5,
            'ra': 16.25,
            'dec': 35.8,
            'exposure': 0.1,  # 100ms
            'station_name': 'Station XYZ',
            # Missing local time fields (should be handled)
        }
        
        # Test with dictionary
        success = save_occultation_sequence(event_dict, "", config.get_sequence_path(), config)
        print(f"✓ Save with dictionary: {'Success' if success else 'Failed'}")
        
        if success:
            # Check if file was created
            start_time = datetime.strptime(event_dict['start_time'], '%Y-%m-%dT%H:%M:%S')
            clean_name = "".join(c for c in event_dict['name'] if c.isalnum() or c in ('(',')',' ', '-', '_')).rstrip()
            expected_filename = start_time.strftime('%Y%m%d') + ' ' + clean_name + '.scs'
            expected_path = os.path.join(config.get_sequence_path(), expected_filename)
            
            if os.path.exists(expected_path):
                print(f"✓ Dictionary sequence file created: {expected_filename}")
                
                # Check contents
                with open(expected_path, 'r') as f:
                    content = f.read()
                
                # Check for empty local time handling
                if 'event_time_local' in content and 'start_time_local' in content:
                    print("✓ Local time fields handled (may be empty)")
                
            else:
                print(f"❌ Dictionary sequence file not found: {expected_path}")
        
        # Cleanup
        shutil.rmtree(config.test_folder)
        
    except Exception as e:
        print(f"❌ Dictionary test failed: {e}")
        import traceback
        traceback.print_exc()

def test_simple_goto_event():
    """Test simple_goto_event function"""
    print("\n=== Testing simple_goto_event ===")
    
    try:
        from utils import simple_goto_event
        
        event = MockOccultationEvent()
        
        # Test GOTO function (should fail gracefully without SharpCap)
        result = simple_goto_event(event)
        print(f"✓ GOTO function called: {'Success' if result else 'Failed (expected without SharpCap)'}")
        
        # The function should return False when SharpCap is not available
        if not result:
            print("✓ Graceful failure when SharpCap not available")
        else:
            print("⚠ Unexpected success - SharpCap may be running")
        
    except Exception as e:
        print(f"❌ GOTO test failed: {e}")
        import traceback
        traceback.print_exc()

def test_template_error_handling():
    """Test error handling scenarios"""
    print("\n=== Testing Error Handling ===")
    
    try:
        # Mock the templates module
        sys.modules['templates'] = type('MockModule', (), {
            'TemplateManager': MockTemplateManager
        })()
        
        from utils import save_occultation_sequence
        
        config = MockConfigManager()
        event = MockOccultationEvent()
        
        # Test with missing template
        success = save_occultation_sequence(event, "error_template.txt", config.get_sequence_path(), config)
        print(f"✓ Missing template handled: {'Failed as expected' if not success else 'Unexpected success'}")
        
        # Test with invalid directory
        invalid_path = "/this/path/should/not/exist/12345"
        success = save_occultation_sequence(event, "", invalid_path, config)
        print(f"✓ Invalid path handled: {'Failed as expected' if not success else 'Unexpected success'}")
        
        # Test with invalid event data
        try:
            invalid_event = {}  # Empty dictionary
            success = save_occultation_sequence(invalid_event, "", config.get_sequence_path(), config)
            print(f"✓ Invalid event data handled: {'Failed as expected' if not success else 'Handled gracefully'}")
        except Exception as e:
            print(f"✓ Invalid event data properly rejected: {type(e).__name__}")
        
        # Cleanup
        shutil.rmtree(config.test_folder)
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()

def test_filename_generation():
    """Test sequence filename generation"""
    print("\n=== Testing Filename Generation ===")
    
    try:
        from utils import save_occultation_sequence
        
        # Mock the templates module
        sys.modules['templates'] = type('MockModule', (), {
            'TemplateManager': MockTemplateManager
        })()
        
        config = MockConfigManager()
        
        # Test various event names for filename generation
        test_cases = [
            ('Normal Asteroid - Station ABC', 'Normal event name'),
            ('(433) Eros - Observatory XYZ', 'Numbered asteroid'),
            ('2024 AB1 - Site-123', 'Designation with special chars'),
            ('Test/Event\\With:Bad*Chars - Station', 'Special characters'),
            ('   Asteroid With Spaces   - Station   ', 'Extra spaces'),
        ]
        
        for event_name, description in test_cases:
            try:
                # Create event with specific name
                event_data = MockOccultationEvent().create_default_event_data()
                event_data['name'] = event_name
                event = MockOccultationEvent(event_data)
                
                success = save_occultation_sequence(event, "", config.get_sequence_path(), config)
                
                if success:
                    # Check what filename was created
                    files = [f for f in os.listdir(config.get_sequence_path()) if f.endswith('.scs')]
                    if files:
                        latest_file = max(files, key=lambda f: os.path.getctime(os.path.join(config.get_sequence_path(), f)))
                        print(f"✓ {description}: '{event_name}' → '{latest_file}'")
                    else:
                        print(f"❌ {description}: No file created")
                else:
                    print(f"❌ {description}: Save failed")
                    
            except Exception as e:
                print(f"❌ {description}: Error - {e}")
        
        # Cleanup
        shutil.rmtree(config.test_folder)
        
    except Exception as e:
        print(f"❌ Filename generation test failed: {e}")
        import traceback
        traceback.print_exc()

def test_custom_template_path():
    """Test with custom template path"""
    print("\n=== Testing Custom Template Path ===")
    
    try:
        # Create a real template file for testing
        config = MockConfigManager()
        template_path = os.path.join(config.get_sequence_path(), 'custom_template.txt')
        
        custom_template_content = """# Custom Template for {object_name}
# Custom event time: {event_time}
# Custom coordinates: RA={ra}h, Dec={dec}°

CUSTOM_GOTO {ra} {dec}
CUSTOM_WAIT {goto_time_local}
CUSTOM_EXPOSE {exposure}
CUSTOM_RECORD {recording_duration}

# Custom parameters:
# Star: {star_mag} mag
# Drop: {mag_drop} mag
# Station: {station_name}
"""
        
        with open(template_path, 'w') as f:
            f.write(custom_template_content)
        
        print(f"✓ Custom template created: {os.path.basename(template_path)}")
        
        # Mock TemplateManager to use real file
        class RealTemplateManager:
            @staticmethod
            def load_template(template_path, config=None):
                try:
                    if template_path and os.path.exists(template_path):
                        with open(template_path, 'r') as f:
                            return f.read()
                    return None
                except:
                    return None
        
        sys.modules['templates'] = type('MockModule', (), {
            'TemplateManager': RealTemplateManager
        })()
        
        from utils import save_occultation_sequence
        
        event = MockOccultationEvent()
        success = save_occultation_sequence(event, template_path, config.get_sequence_path(), config)
        
        print(f"✓ Custom template usage: {'Success' if success else 'Failed'}")
        
        if success:
            # Find and check the generated file
            files = [f for f in os.listdir(config.get_sequence_path()) if f.endswith('.scs')]
            if files:
                seq_file = files[0]
                seq_path = os.path.join(config.get_sequence_path(), seq_file)
                
                with open(seq_path, 'r') as f:
                    content = f.read()
                
                # Check for custom template markers
                custom_markers = ['CUSTOM_GOTO', 'CUSTOM_WAIT', 'CUSTOM_EXPOSE', 'CUSTOM_RECORD']
                found_markers = [marker for marker in custom_markers if marker in content]
                
                print(f"✓ Custom template markers found: {len(found_markers)}/{len(custom_markers)}")
                for marker in found_markers:
                    print(f"  - {marker}")
        
        # Cleanup
        shutil.rmtree(config.test_folder)
        
    except Exception as e:
        print(f"❌ Custom template test failed: {e}")
        import traceback
        traceback.print_exc()

def test_performance():
    """Test performance of sequence generation"""
    print("\n=== Testing Performance ===")
    
    try:
        import time
        
        # Mock the templates module
        sys.modules['templates'] = type('MockModule', (), {
            'TemplateManager': MockTemplateManager
        })()
        
        from utils import save_occultation_sequence
        
        config = MockConfigManager()
        
        # Test multiple sequence generation
        num_sequences = 10
        events = []
        
        for i in range(num_sequences):
            event_data = MockOccultationEvent().create_default_event_data()
            event_data['name'] = f'Performance Test Event {i+1} - Station {i%3+1}'
            event_data['object_name'] = f'Test Asteroid {i+1}'
            events.append(MockOccultationEvent(event_data))
        
        # Time the generation
        start_time = time.time()
        
        success_count = 0
        for event in events:
            if save_occultation_sequence(event, "", config.get_sequence_path(), config):
                success_count += 1
        
        total_time = time.time() - start_time
        avg_time = total_time / num_sequences
        
        print(f"✓ Generated {success_count}/{num_sequences} sequences")
        print(f"✓ Total time: {total_time:.3f} seconds")
        print(f"✓ Average time per sequence: {avg_time:.3f} seconds")
        
        # Check files were created
        files = [f for f in os.listdir(config.get_sequence_path()) if f.endswith('.scs')]
        print(f"✓ Files created: {len(files)}")
        
        # Cleanup
        shutil.rmtree(config.test_folder)
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("Utils Module Standalone Test")
    print("=" * 40)
    
    try:
        # Test module import
        from utils import save_occultation_sequence, simple_goto_event
        print("✓ Utils module imported successfully")
        
        # Run all tests
        test_save_occultation_sequence_with_event_object()
        test_save_occultation_sequence_with_dict()
        test_simple_goto_event()
        test_template_error_handling()
        test_filename_generation()
        test_custom_template_path()
        test_performance()
        
        print("\n" + "=" * 40)
        print("✓ All utils tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure utils.py is in the same directory")
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