"""
Test script for Occult 4 XML export
Validates the XML structure and format
"""

import sys
from datetime import datetime
from occult4_export import Occult4Exporter


class MockConfig:
    """Mock configuration for testing"""
    def get_file_folder(self):
        return '.'
    
    def get_observer_name(self):
        return 'Test Observer'
    
    def get_iota_region(self):
        return 'US'
    
    def get_telescopes(self):
        return [{'id': 'test1', 'aperture': '20', 'type': 'SCT'}]
    
    def get_cameras(self):
        return [{'id': 'cam1', 'type': 'video'}]


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


def test_export():
    """Test the export functionality"""
    print("Testing Occult 4 XML Export...")
    
    config = MockConfig()
    exporter = Occult4Exporter(config)
    event = MockEvent()
    
    # Test export
    output_path = exporter.export_observation(
        event,
        telescope_id='test1',
        camera_id='cam1',
        observation_type='Positive'
    )
    
    if output_path:
        print(f"\nSuccess! File created: {output_path}")
        print("\nValidating XML structure...")
        
        # Read and display the file
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print("\n" + "="*80)
            print("GENERATED XML:")
            print("="*80)
            print(content)
            print("="*80)
        
        # Basic validation
        errors = []
        
        # Check XML declaration
        if not content.startswith('<?xml version="1.0"'):
            errors.append("Missing XML declaration")
        
        # Check required tags
        required_tags = [
            '<AsteroidOccultations>',
            '<FileVersion>',
            '<Event>',
            '<Date>',
            '<Details>',
            '<Star>',
            '<StarIssues>',
            '<Asteroid>',
            '<EventFits>',
            '<SolveFlags>',
            '<EllipticFit>',
            '<EllipseUncertainty>',
            '<Observations>',
            '<Prediction>',
            '<Observer>',
            '<ID>',
            '<Conditions>',
            '<D>',
            '<R>',
            '<Added>',
            '<LastEdited>',
            '</Event>',
            '</AsteroidOccultations>'
        ]
        
        for tag in required_tags:
            if tag not in content:
                errors.append(f"Missing tag: {tag}")
        
        # Check pipe separators in data lines
        if '|' not in content:
            errors.append("Missing pipe separators in data")
        
        # Check time format in D/R lines
        import re
        d_line_match = re.search(r'<D>(\d{2} \d{2} \d{2}\.\d{2})\|', content)
        if not d_line_match:
            errors.append("D line time format incorrect (should be 'hh mm ss.ss|')")
        else:
            print(f"\n✓ D line time format correct: {d_line_match.group(1)}")
        
        r_line_match = re.search(r'<R>(\d{2} \d{2} \d{2}\.\d{2})\|', content)
        if not r_line_match:
            errors.append("R line time format incorrect (should be 'hh mm ss.ss|')")
        else:
            print(f"✓ R line time format correct: {r_line_match.group(1)}")
        
        # Check Prediction time format
        pred_match = re.search(r'<Prediction>[^|]+\|[^|]+\|[^|]+\|(\d+)\|(\d+)\|(\d+\.\d)\|', content)
        if not pred_match:
            errors.append("Prediction time format incorrect (should be 'hr|min|s.s|')")
        else:
            print(f"✓ Prediction time format correct: {pred_match.group(1)}|{pred_match.group(2)}|{pred_match.group(3)}")
        
        # Check coordinate format
        coord_match = re.search(r'([+-]\d{2,3} \d{2} \d{2}\.\d)', content)
        if not coord_match:
            errors.append("Coordinate format incorrect (should be '±ddd mm ss.s' or '±dd mm ss.s')")
        else:
            print(f"✓ Coordinate format correct: {coord_match.group(1)}")
        
        # Report results
        if errors:
            print("\n❌ VALIDATION ERRORS:")
            for error in errors:
                print(f"  - {error}")
            return False
        else:
            print("\n✓ All validation checks passed!")
            return True
    else:
        print("❌ Export failed!")
        return False


if __name__ == '__main__':
    success = test_export()
    sys.exit(0 if success else 1)
