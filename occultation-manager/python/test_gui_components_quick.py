# test_gui_components_quick.py - Quick GUI components validation test

import os
import sys
from datetime import datetime, timedelta


# Import GUI libraries
import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Windows.Forms import *
from System.Drawing import Size

def quick_test():
    """Quick GUI components test"""
    print("Quick GUI Components Test")
    print("=" * 30)
    
    try:
        
        # Mock event for testing
        class MockEvent:
            def __init__(self):
                self.selected = True
                self.event_name = "Test Event"
                self.station_name = "Test Station"
                self.event_date = "2024-01-15"
                self.event_time_utc = "12:30:45"
                self.star_mag = 11.5
                self.comb_mag = 11.3
                self.mag_drop = 2.1
                self.exposure_ms = 80
                self.recording_duration = 60
                self.max_duration_seconds = 15.5
                self.uncertainty_seconds = 3.2
                self.star_alt = 45.0
                self.star_az = 180.0
                self.ra = 15.5
                self.dec = 45.2
                self.owcloudurl = "https://example.com"
                
            def get_asteroid_display_name(self):
                return "Test Asteroid"
            def has_custom_exposure(self):
                return False
            def get_coordinates_string(self):
                return "15.5000h, 45.2000°"
            def get_status_info(self):
                return "Future Event"
        
        # Import and test
        from gui_components import EventsDataGrid
        print("✓ GUI Components module imports")
        
        # Create grid
        grid = EventsDataGrid()
        print("✓ EventsDataGrid created")
        
        # Test basic properties
        assert grid.AutoGenerateColumns == False, "AutoGenerateColumns should be False"
        assert grid.Columns.Count > 0, "Should have columns"
        print("✓ Grid properties correct")
        
        # Test with events
        test_events = [MockEvent(), MockEvent()]
        test_events[1].event_name = "Test Event 2"
        
        grid.update_events(test_events)
        assert grid.Rows.Count == 2, f"Expected 2 rows, got {grid.Rows.Count}"
        print("✓ Grid updates with events")
        
        # Test selection
        selected = grid.get_selected_events()
        assert len(selected) == 2, f"Expected 2 selected, got {len(selected)}"
        print("✓ Selection works")
        
        # Test select all/none
        grid.select_all_events(False)
        selected = grid.get_selected_events()
        assert len(selected) == 0, f"Expected 0 selected after deselect all, got {len(selected)}"
        print("✓ Deselect all works")
        
        grid.select_all_events(True)
        selected = grid.get_selected_events()
        assert len(selected) == 2, f"Expected 2 selected after select all, got {len(selected)}"
        print("✓ Select all works")
        
        # Dispose grid
        grid.Dispose()
        
        print("✓ Quick test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)