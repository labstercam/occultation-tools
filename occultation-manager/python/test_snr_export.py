"""
Test script to verify SNR is properly exported to OBS.XML from AOTA report data
"""

import sys
import os
import tempfile
from datetime import datetime
from occult4_export import Occult4Exporter


class MockConfig:
    """Mock configuration for testing"""
    def __init__(self):
        # Use temp directory to avoid permission issues
        self.temp_dir = tempfile.mkdtemp()
    
    def get_file_folder(self):
        return self.temp_dir
    
    def get_observer_name(self):
        return 'Test Observer'
    
    def get_observer_state(self):
        return 'CA'
    
    def get_iota_region(self):
        return 'US'
    
    def get_telescopes(self):
        return [{'id': 'test1', 'aperture': '20', 'type': 'SCT'}]
    
    def get_cameras(self):
        return [{'id': 'cam1', 'type': 'video', 'occult4_method': 'b', 'occult4_time': 'a'}]


class MockEvent:
    """Mock event for testing"""
    def __init__(self):
        self.event_datetime = datetime(2025, 12, 30, 10, 23, 45, 123456)
        self.object_no = '778'
        self.object_name = '(778) Theobalda'
        self.star_id = 'Gaia DR3 4691443935057297792'
        self.star_mag = 12.5
        self.ra_hours = 10.123456789
        self.dec_degrees = -23.456789012
        self.longitude = -122.5
        self.latitude = 37.75
        self.elevation = 100
        self.obs_location = 'Test City'
        self.event_duration = 5.2


def test_snr_export():
    """Test SNR export from AOTA report data"""
    print("Testing SNR export to OBS.XML...")
    
    config = MockConfig()
    print(f"Using temp directory: {config.get_file_folder()}")
    exporter = Occult4Exporter(config)
    event = MockEvent()
    
    # Create AOTA report data with SNR
    aota_report_data = {
        'd_hours': '10',
        'd_minutes': '23',
        'd_seconds': '45.12',
        'd_uncertainty': 0.05,
        'r_hours': '10',
        'r_minutes': '23',
        'r_seconds': '50.34',
        'r_uncertainty': 0.05,
        'snr': 4.5  # This is the SNR value we want to see in the XML
    }
    
    print(f"\nAOTA Report Data:")
    print(f"  D Time: {aota_report_data['d_hours']}:{aota_report_data['d_minutes']}:{aota_report_data['d_seconds']}")
    print(f"  R Time: {aota_report_data['r_hours']}:{aota_report_data['r_minutes']}:{aota_report_data['r_seconds']}")
    print(f"  SNR: {aota_report_data['snr']}")
    
    # Test export with AOTA data
    output_path = exporter.export_observation(
        event,
        telescope_id='test1',
        camera_id='cam1',
        observation_type='Positive',
        aota_report_data=aota_report_data
    )
    
    if output_path:
        print(f"\nSuccess! File created: {output_path}")
        
        # Read and check for SNR
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print("\nSearching for SNR in Conditions line...")
        
        # Extract Conditions line
        import re
        conditions_match = re.search(r'<Conditions>([^<]+)</Conditions>', content)
        
        if conditions_match:
            conditions_content = conditions_match.group(1)
            print(f"Conditions line: {conditions_content}")
            
            # Parse the pipe-delimited values
            parts = conditions_content.split('|')
            if len(parts) >= 3:
                stability = parts[0]
                transparency = parts[1]
                snr = parts[2]
                
                print(f"\nParsed Conditions:")
                print(f"  Stability: '{stability}'")
                print(f"  Transparency: '{transparency}'")
                print(f"  SNR: '{snr}'")
                
                # Check if SNR is populated
                if snr and snr.strip():
                    expected_snr = "4.5"
                    if snr.strip() == expected_snr:
                        print(f"\n✓ SUCCESS! SNR correctly populated: {snr}")
                        return True
                    else:
                        print(f"\n⚠ WARNING! SNR value mismatch. Expected: {expected_snr}, Got: {snr}")
                        return False
                else:
                    print(f"\n❌ FAILED! SNR is empty or blank")
                    return False
            else:
                print(f"\n❌ FAILED! Conditions line doesn't have enough fields (expected 5+, got {len(parts)})")
                return False
        else:
            print("\n❌ FAILED! Could not find Conditions line in XML")
            return False
    else:
        print("❌ Export failed!")
        return False


def test_snr_without_aota_data():
    """Test that export works without AOTA data (SNR should be blank)"""
    print("\n" + "="*80)
    print("Testing export WITHOUT AOTA data (SNR should be blank)...")
    
    config = MockConfig()
    print(f"Using temp directory: {config.get_file_folder()}")
    exporter = Occult4Exporter(config)
    event = MockEvent()
    
    # Test export without AOTA data
    output_path = exporter.export_observation(
        event,
        telescope_id='test1',
        camera_id='cam1',
        observation_type='Positive'
        # No aota_report_data parameter
    )
    
    if output_path:
        print(f"File created: {output_path}")
        
        # Read and check for SNR
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import re
        conditions_match = re.search(r'<Conditions>([^<]+)</Conditions>', content)
        
        if conditions_match:
            conditions_content = conditions_match.group(1)
            parts = conditions_content.split('|')
            if len(parts) >= 3:
                snr = parts[2]
                if snr.strip() == '':
                    print(f"✓ SUCCESS! SNR correctly blank when no AOTA data: '{snr}'")
                    return True
                else:
                    print(f"⚠ WARNING! SNR should be blank but got: '{snr}'")
                    return False
        
        print("❌ Could not parse Conditions line")
        return False
    else:
        print("❌ Export failed!")
        return False


def test_snr_max_value():
    """Test that SNR is capped at maximum value of 20.0"""
    print("\n" + "="*80)
    print("Testing SNR maximum value (should cap at 20.0)...")
    
    config = MockConfig()
    print(f"Using temp directory: {config.get_file_folder()}")
    exporter = Occult4Exporter(config)
    event = MockEvent()
    
    # Create AOTA report data with SNR > 20.0
    aota_report_data = {
        'd_hours': '10',
        'd_minutes': '23',
        'd_seconds': '45.12',
        'r_hours': '10',
        'r_minutes': '23',
        'r_seconds': '50.34',
        'snr': 35.7  # This should be capped to 20.0
    }
    
    print(f"Input SNR: {aota_report_data['snr']} (should be capped to 20.0)")
    
    # Test export
    output_path = exporter.export_observation(
        event,
        telescope_id='test1',
        camera_id='cam1',
        observation_type='Positive',
        aota_report_data=aota_report_data
    )
    
    if output_path:
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        import re
        conditions_match = re.search(r'<Conditions>([^<]+)</Conditions>', content)
        
        if conditions_match:
            conditions_content = conditions_match.group(1)
            parts = conditions_content.split('|')
            if len(parts) >= 3:
                snr = parts[2]
                expected_snr = "20.0"
                if snr.strip() == expected_snr:
                    print(f"✓ SUCCESS! SNR correctly capped at maximum: {snr}")
                    return True
                else:
                    print(f"❌ FAILED! Expected SNR: {expected_snr}, Got: {snr}")
                    return False
        
        print("❌ Could not parse Conditions line")
        return False
    else:
        print("❌ Export failed!")
        return False


if __name__ == '__main__':
    print("="*80)
    print("SNR EXPORT TEST SUITE")
    print("="*80)
    
    # Test 1: With AOTA data
    test1_passed = test_snr_export()
    
    # Test 2: Without AOTA data
    test2_passed = test_snr_without_aota_data()
    
    # Test 3: SNR max value
    test3_passed = test_snr_max_value()
    
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(f"Test 1 (SNR from AOTA data): {'✓ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Test 2 (No AOTA data): {'✓ PASSED' if test2_passed else '❌ FAILED'}")
    print(f"Test 3 (SNR max value cap): {'✓ PASSED' if test3_passed else '❌ FAILED'}")
    
    all_passed = test1_passed and test2_passed and test3_passed
    print(f"\nOverall: {'✓ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")
    print("="*80)
    
    sys.exit(0 if all_passed else 1)
