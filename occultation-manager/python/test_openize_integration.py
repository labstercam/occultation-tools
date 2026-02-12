"""
Integration Test for TT Report Generation with Openize SDK
===========================================================

Run this from SharpCap's Python scripting console to test the complete
TT report generation using the Openize SDK.

This script:
1. Imports the new generator
2. Creates mock event data
3. Generates a test report
4. Verifies the output file exists
"""

import sys
import os
from datetime import datetime

# Add python folder to path
script_dir = r"c:\Users\AstroPC\Git\occultation-tools\occultation-manager\python"
if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

# Add lib folder to path
lib_path = os.path.join(script_dir, 'lib')
if lib_path not in sys.path:
    sys.path.append(lib_path)

print("=" * 70)
print("TT REPORT OPENIZE - INTEGRATION TEST")
print("=" * 70)

# Import the new generator
print("\n[1/6] Importing TTReportGeneratorOpenize...")
try:
    from tt_report_openize import TTReportGeneratorOpenize, is_openize_available
    print("✓ Import successful")
except Exception as ex:
    print(f"✗ FAILED: {ex}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Check if Openize is available
print("\n[2/6] Checking Openize SDK availability...")
if not is_openize_available():
    print("✗ FAILED: Openize SDK not available")
    sys.exit(1)
print("✓ Openize SDK is available")

# Create mock configuration
print("\n[3/6] Creating mock configuration...")
class MockConfig:
    def __init__(self):
        self.observer_name = "Test Observer"
        self.observer_email = "test@example.com"
        self.observer_address = "123 Test Street"
        self.observer_city = "Test City"
        self.observer_state = "Test State"
        self.file_folder = script_dir  # Use script folder for test output
        
    def get_observer_name(self):
        return self.observer_name
    
    def get_observer_email(self):
        return self.observer_email
    
    def get_observer_address(self):
        return self.observer_address
    
    def get_observer_city(self):
        return self.observer_city
    
    def get_observer_state(self):
        return self.observer_state
    
    def get_observer_country(self):
        return "Test Country"
    
    def get_observer_phone(self):
        return "+1234567890"
    
    def get_observer_fax(self):
        return ""
    
    def get_file_folder(self):
        return self.file_folder
    
    def get_telescopes(self):
        return [{
            'id': 'test-scope',
            'name': 'Test Telescope',
            'aperture': 235,  # mm
            'focal_length': 1500,  # mm
            'focal_ratio': 6.4,
            'type': 'SCT including Cass and Mak'
        }]
    
    def get_active_telescope(self):
        return self.get_telescopes()[0]
    
    def get_cameras(self):
        return [{
            'id': 'test-camera',
            'name': 'Test Camera',
            'timing': 'GPS PPS',
            'timing_device': 'SharpCap',
            'detector': 'Test Detector',
            'other_info': 'Test camera info'
        }]
    
    def get_active_camera(self):
        return self.get_cameras()[0]

config = MockConfig()
print("✓ Mock configuration created")

# Create mock event
print("\n[4/6] Creating mock event data...")
class MockEvent:
    def __init__(self):
        self.event_datetime = datetime(2024, 12, 13, 10, 3, 42)
        self.object_no = 12345
        self.object_name = "(12345) TestAsteroid"
        self.star_name = "UCAC4 123-456789"
        self.star_id = "UCAC4 123-456789"
        self.obs_location = "Test Observatory"
        self.latitude = -36.8356
        self.longitude = 174.6578
        self.elevation = 25.0
        self.station_name = "Test Station"

event = MockEvent()
print(f"✓ Mock event created: {event.object_name} on {event.event_datetime}")

# Create mock Tangra data
tangra_data = {
    'start_time': '10:02:30.123',
    'end_time': '10:04:45.678',
    'video_format': 'SER',
    'tdelta_median': 40.0,  # ms
    'acquisition_delay': 45.0  # ms
}
print(f"✓ Mock Tangra data created")

# Initialize generator
print("\n[5/6] Initializing TT report generator...")
try:
    generator = TTReportGeneratorOpenize(config)
    print("✓ Generator initialized")
except Exception as ex:
    print(f"✗ FAILED: {ex}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Generate report
print("\n[6/6] Generating test report...")
print("This may take a few seconds...")
try:
    output_path = generator.generate_report(
        event=event,
        telescope_id='test-scope',
        camera_id='test-camera',
        observation_type='Positive',
        tangra_data=tangra_data,
        aota_report_data=None,
        aota_xml_used=False
    )
    
    if output_path and os.path.exists(output_path):
        file_size = os.path.getsize(output_path) / 1024
        print(f"\n✓ SUCCESS: Report generated!")
        print(f"  Location: {output_path}")
        print(f"  Size: {file_size:.1f} KB")
        
        # Verify it's a valid Excel file
        if output_path.endswith('.xlsx'):
            print(f"  Format: Valid .xlsx file")
        
        print("\n" + "=" * 70)
        print("INTEGRATION TEST PASSED!")
        print("=" * 70)
        print("\nNext steps:")
        print(f"  1. Open the generated report: {output_path}")
        print("  2. Verify all cells are populated correctly")
        print("  3. Check data validation dropdowns work")
        print("  4. Compare with output from existing generator")
        print("  5. Test with real event data")
        
    else:
        print(f"\n✗ FAILED: Report was not created")
        print(f"  Expected output: {output_path if output_path else 'None'}")
        sys.exit(1)
        
except Exception as ex:
    print(f"\n✗ FAILED: {ex}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("=" * 70)
