# test_gui_components_minimal.py - Minimal interactive test

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Windows.Forms import *
from System.Drawing import *
from datetime import datetime, timedelta

def minimal_visual_test():
    """Minimal visual test showing basic grid functionality"""
    print("Minimal GUI Components Visual Test")
    print("=" * 35)
    
    try:
        from gui_components import EventsDataGrid
        
        # Simple mock event
        class SimpleEvent:
            def __init__(self, name):
                self.selected = True
                self.event_name = name
                self.station_name = "Station ABC"
                self.event_date = datetime.now().strftime("%Y-%m-%d")
                self.event_time_utc = datetime.now().strftime("%H:%M:%S")
                self.star_mag = 11.5
                self.comb_mag = 11.3
                self.mag_drop = 2.1
                self.exposure_ms = 80
                self.recording_duration = 60
                self.max_duration_seconds = 15.0
                self.uncertainty_seconds = 3.0
                self.star_alt = 45.0
                self.star_az = 180.0
                self.ra = 15.5
                self.dec = 45.2
                self.owcloudurl = f"https://example.com/{name.replace(' ', '')}"
                
            def get_asteroid_display_name(self):
                return f"Asteroid {self.event_name}"
            def has_custom_exposure(self):
                return False
            def get_coordinates_string(self):
                return f"{self.ra:.4f}h, {self.dec:.4f}°"
            def get_status_info(self):
                return "Future"
        
        # Create simple form
        form = Form()
        form.Text = "EventsDataGrid Minimal Test"
        form.Size = Size(900, 400)
        form.StartPosition = FormStartPosition.CenterScreen
        
        # Create grid
        grid = EventsDataGrid()
        grid.Location = Point(10, 10)
        grid.Size = Size(860, 300)
        form.Controls.Add(grid)
        
        # Add test events
        events = [
            SimpleEvent("Test Event 1"),
            SimpleEvent("Test Event 2"),
            SimpleEvent("Test Event 3"),
        ]
        
        grid.update_events(events)
        
        # Add close button
        btn_close = Button()
        btn_close.Text = "Close"
        btn_close.Location = Point(400, 320)
        btn_close.Size = Size(80, 30)
        btn_close.Click += lambda s, e: form.Close()
        form.Controls.Add(btn_close)
        
        # Add status label
        lbl_status = Label()
        lbl_status.Text = f"Showing {len(events)} events - Try selecting/deselecting checkboxes"
        lbl_status.Location = Point(10, 325)
        lbl_status.Size = Size(380, 20)
        form.Controls.Add(lbl_status)
        
        print("✓ Showing minimal test form...")
        print("  - Grid shows 3 test events")
        print("  - Try clicking checkboxes in the Selected column")
        print("  - Close the form when done")
        
        form.ShowDialog()
        print("✓ Minimal visual test completed")
        
    except Exception as e:
        print(f"❌ Minimal visual test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    minimal_visual_test()

"""

What the Tests Verify
Grid Creation: EventsDataGrid creates with correct initial properties
Column Setup: All 16 expected columns are created with correct names
Data Population: Grid correctly displays event data in proper format
Selection System: Checkbox selection and get_selected_events work
Event Handling: Double-click and cell content click events function
Data Formatting: Proper display of dates, magnitudes, coordinates, etc.
Performance: Handles 100+ events with acceptable speed
Edge Cases: Graceful handling of empty lists, None values, malformed data
Visual Verification: Interactive test shows actual working grid
Integration: Compatible with mock event objects matching real structure
This comprehensive test suite ensures the GUI components work correctly and can handle real-world usage scenarios in the main application.
GUI Components Module Standalone Test
==================================================
✓ GUI Components module imported successfully

=== Testing EventsDataGrid Creation ===
✓ EventsDataGrid created successfully
✓ AutoGenerateColumns: False
✓ AllowUserToAddRows: False
✓ AllowUserToDeleteRows: False
✓ SelectionMode: FullRowSelect
✓ MultiSelect: True
✓ Number of columns: 16
✓ Correct number of columns created
✓ Column names:
  ✓ 1. Selected (expected: Selected)
  ✓ 2. EventName (expected: EventName)
  ✓ 3. StationName (expected: StationName)
  ✓ 4. DateTime (expected: DateTime)
  ✓ 5. StarMag (expected: StarMag)
  ✓ 6. CombMag (expected: CombMag)
  ✓ 7. MagDrop (expected: MagDrop)
  ✓ 8. ExposureMs (expected: ExposureMs)
  ✓ 9. RecordingTime (expected: RecordingTime)
  ✓ 10. MaxDuration (expected: MaxDuration)
  ✓ 11. TimeError (expected: TimeError)
  ✓ 12. Altitude (expected: Altitude)
  ✓ 13. Azimuth (expected: Azimuth)
  ✓ 14. Coordinates (expected: Coordinates)
  ✓ 15. OWCLink (expected: OWCLink)
  ✓ 16. Status (expected: Status)
✓ Initial rows: 0

=== Testing EventsDataGrid Update ===
✓ Created 3 test events
✓ Grid updated with events
✓ Rows after update: 3
✓ Row count matches event count
✓ Row 1 data:
  - Selected: True
  - Event Name: Asteroid Event 1
  - Station: Test Station ABC
  - Exposure: 80
  ✓ Selected value correct
  ✓ Exposure value contains expected data
  ✓ No custom exposure indicator (correct)
✓ Row 2 data:
  - Selected: True
  - Event Name: Asteroid Event 2
  - Station: Test Station ABC
  - Exposure: 80*
  ✓ Selected value correct
  ✓ Exposure value contains expected data
  ✓ Custom exposure indicator (*) present
✓ Row 3 data:
  - Selected: True
  - Event Name: Asteroid Event 3
  - Station: Test Station ABC
  - Exposure: 80
  ✓ Selected value correct
  ✓ Exposure value contains expected data
  ✓ No custom exposure indicator (correct)
✓ Selected events: 3
✓ get_selected_events returns correct count

=== Testing EventsDataGrid Selection ===
✓ Updated grid with 3 events
✓ Initial selected events: 1
✓ After select all: 3 events selected
✓ select_all_events(True) works correctly
✓ After deselect all: 0 events selected
✓ select_all_events(False) works correctly
✓ After manual selection: 1 events selected
✓ Manual selection works

=== Testing EventsDataGrid Events ===
✓ Grid populated with 2 events
✓ Found ExposureMs column at index 7
  ✓ edit_event_exposure called for: Event Handler Test 1
✓ Double-click on exposure column triggers edit
✓ Found OWCLink column at index 14
  ✓ Would open URL: https://cloud.occultwatcher.net/event/EventHandlerTest1
✓ OWC link click opens URL
✓ Event handling tests completed

... (additional test output)

==================================================
✓ All automated tests completed!

Would you like to run the visual test? (shows actual grid)
Enter 'y' for yes, any other key to skip:

"""    