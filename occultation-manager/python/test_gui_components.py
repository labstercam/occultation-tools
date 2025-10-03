# test_gui_components.py - Standalone test for gui_components.py module

import sys
import os
import webbrowser
from datetime import datetime, timedelta

# Add the module directory to Python path if needed
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

# Import required GUI libraries
import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Point, Size, Font, FontStyle
from System.Windows.Forms import *

# Mock dependencies for testing
class MockOccultationEvent:
    """Mock OccultationEvent for testing GUI components"""
    
    def __init__(self, name="Test Event", hours_future=1, custom_exposure=False):
        self.selected = True
        self.event_name = name
        self.station_name = "Test Station ABC"
        self.object_name = "Test Asteroid"
        
        # Calculate times
        now = datetime.utcnow()
        event_time = now + timedelta(hours=hours_future)
        
        self.event_date = event_time.strftime("%Y-%m-%d")
        self.event_time_utc = event_time.strftime("%H:%M:%S")
        self.event_datetime = event_time
        
        # Magnitudes
        self.star_mag = 11.5
        self.comb_mag = 11.3
        self.mag_drop = 2.1
        
        # Exposure and recording
        self.exposure_ms = 80
        self.custom_exposure = 150 if custom_exposure else None
        self.recording_duration = 60
        self.max_duration_seconds = 15.5
        self.uncertainty_seconds = 3.2
        
        # Position
        self.star_alt = 45.8
        self.star_az = 180.3
        self.ra = 15.5
        self.dec = 45.2
        
        # URLs and status
        self.owcloudurl = f"https://cloud.occultwatcher.net/event/{name.replace(' ', '')}"
        
    def get_asteroid_display_name(self):
        """Get display name for asteroid"""
        return f"Asteroid {self.object_name}"
    
    def has_custom_exposure(self):
        """Check if has custom exposure"""
        return self.custom_exposure is not None
    
    def get_coordinates_string(self):
        """Get coordinate string"""
        return f"{self.ra:.4f}h, {self.dec:.4f}°"
    
    def get_status_info(self):
        """Get status information"""
        if not self.event_datetime:
            return "Invalid Date"
        
        now = datetime.utcnow()
        if self.event_datetime < now:
            return "Past Event"
        
        time_to_event = self.event_datetime - now
        days = time_to_event.days
        hours = time_to_event.seconds // 3600
        return f"{days}d {hours}h"

def test_events_data_grid_creation():
    """Test EventsDataGrid creation and basic setup"""
    print("\n=== Testing EventsDataGrid Creation ===")
    
    try:
        from gui_components import EventsDataGrid
        
        # Create the grid
        grid = EventsDataGrid()
        print("✓ EventsDataGrid created successfully")
        
        # Check initial properties
        print(f"✓ AutoGenerateColumns: {grid.AutoGenerateColumns}")
        print(f"✓ AllowUserToAddRows: {grid.AllowUserToAddRows}")
        print(f"✓ AllowUserToDeleteRows: {grid.AllowUserToDeleteRows}")
        print(f"✓ SelectionMode: {grid.SelectionMode}")
        print(f"✓ MultiSelect: {grid.MultiSelect}")
        
        # Verify initial state
        assert grid.AutoGenerateColumns == False, "AutoGenerateColumns should be False"
        assert grid.AllowUserToAddRows == False, "AllowUserToAddRows should be False"
        assert grid.AllowUserToDeleteRows == False, "AllowUserToDeleteRows should be False"
        
        # Check columns were created
        print(f"✓ Number of columns: {grid.Columns.Count}")
        
        expected_columns = [
            "Selected", "EventName", "StationName", "DateTime", "StarMag", 
            "CombMag", "MagDrop", "ExposureMs", "RecordingTime", "MaxDuration",
            "TimeError", "Altitude", "Azimuth", "Coordinates", "OWCLink", "Status"
        ]
        
        if grid.Columns.Count == len(expected_columns):
            print("✓ Correct number of columns created")
        else:
            print(f"❌ Expected {len(expected_columns)} columns, got {grid.Columns.Count}")
        
        # Check column names
        actual_columns = [grid.Columns[i].Name for i in range(grid.Columns.Count)]
        print("✓ Column names:")
        for i, col_name in enumerate(actual_columns):
            expected = expected_columns[i] if i < len(expected_columns) else "UNEXPECTED"
            status = "✓" if col_name == expected else "❌"
            print(f"  {status} {i+1}. {col_name} (expected: {expected})")
        
        # Check initial row count
        print(f"✓ Initial rows: {grid.Rows.Count}")
        
        # Dispose grid
        grid.Dispose()
        
    except Exception as e:
        print(f"❌ EventsDataGrid creation test failed: {e}")
        import traceback
        traceback.print_exc()

def test_events_data_grid_update():
    """Test updating EventsDataGrid with event data"""
    print("\n=== Testing EventsDataGrid Update ===")
    
    try:
        from gui_components import EventsDataGrid
        
        grid = EventsDataGrid()
        
        # Create test events
        test_events = [
            MockOccultationEvent("Event 1", hours_future=2, custom_exposure=False),
            MockOccultationEvent("Event 2", hours_future=1, custom_exposure=True),
            MockOccultationEvent("Event 3", hours_future=-1, custom_exposure=False),  # Past event
        ]
        
        print(f"✓ Created {len(test_events)} test events")
        
        # Update grid with events
        grid.update_events(test_events)
        
        print(f"✓ Grid updated with events")
        print(f"✓ Rows after update: {grid.Rows.Count}")
        
        # Verify row count matches event count
        if grid.Rows.Count == len(test_events):
            print("✓ Row count matches event count")
        else:
            print(f"❌ Expected {len(test_events)} rows, got {grid.Rows.Count}")
        
        # Check data in rows
        for i in range(min(grid.Rows.Count, len(test_events))):
            row = grid.Rows[i]
            event = test_events[i]
            
            print(f"✓ Row {i+1} data:")
            
            # Check some key columns
            selected_val = row.Cells["Selected"].Value
            event_name_val = row.Cells["EventName"].Value
            station_name_val = row.Cells["StationName"].Value
            exposure_val = row.Cells["ExposureMs"].Value
            
            print(f"  - Selected: {selected_val}")
            print(f"  - Event Name: {event_name_val}")
            print(f"  - Station: {station_name_val}")
            print(f"  - Exposure: {exposure_val}")
            
            # Verify some values
            if selected_val == event.selected:
                print("  ✓ Selected value correct")
            else:
                print(f"  ❌ Selected value wrong: expected {event.selected}, got {selected_val}")
            
            if str(event.exposure_ms) in str(exposure_val):
                print("  ✓ Exposure value contains expected data")
            else:
                print(f"  ❌ Exposure value wrong: expected {event.exposure_ms}, got {exposure_val}")
            
            # Check custom exposure indicator
            if event.has_custom_exposure() and "*" in str(exposure_val):
                print("  ✓ Custom exposure indicator (*) present")
            elif not event.has_custom_exposure() and "*" not in str(exposure_val):
                print("  ✓ No custom exposure indicator (correct)")
            else:
                print(f"  ⚠ Custom exposure indicator may be wrong")
        
        # Test get_selected_events
        selected_events = grid.get_selected_events()
        print(f"✓ Selected events: {len(selected_events)}")
        
        expected_selected = sum(1 for e in test_events if e.selected)
        if len(selected_events) == expected_selected:
            print("✓ get_selected_events returns correct count")
        else:
            print(f"❌ Expected {expected_selected} selected, got {len(selected_events)}")
        
        # Dispose grid
        grid.Dispose()
        
    except Exception as e:
        print(f"❌ EventsDataGrid update test failed: {e}")
        import traceback
        traceback.print_exc()

def test_events_data_grid_selection():
    """Test EventsDataGrid selection functionality"""
    print("\n=== Testing EventsDataGrid Selection ===")
    
    try:
        from gui_components import EventsDataGrid
        
        grid = EventsDataGrid()
        
        # Create test events (all initially selected)
        test_events = [
            MockOccultationEvent("Select Test 1"),
            MockOccultationEvent("Select Test 2"),
            MockOccultationEvent("Select Test 3"),
        ]
        
        # Make some unselected initially
        test_events[1].selected = False
        test_events[2].selected = False
        
        grid.update_events(test_events)
        print(f"✓ Updated grid with {len(test_events)} events")
        
        # Test initial selection state
        initial_selected = grid.get_selected_events()
        print(f"✓ Initial selected events: {len(initial_selected)}")
        
        # Test select_all_events
        grid.select_all_events(True)
        all_selected = grid.get_selected_events()
        print(f"✓ After select all: {len(all_selected)} events selected")
        
        if len(all_selected) == len(test_events):
            print("✓ select_all_events(True) works correctly")
        else:
            print(f"❌ select_all_events failed: expected {len(test_events)}, got {len(all_selected)}")
        
        # Test deselect all
        grid.select_all_events(False)
        none_selected = grid.get_selected_events()
        print(f"✓ After deselect all: {len(none_selected)} events selected")
        
        if len(none_selected) == 0:
            print("✓ select_all_events(False) works correctly")
        else:
            print(f"❌ Deselect all failed: expected 0, got {len(none_selected)}")
        
        # Test individual selection by toggling checkboxes
        if grid.Rows.Count > 0:
            # Select first row
            grid.Rows[0].Cells["Selected"].Value = True
            
            # Check selection
            selected_after_manual = grid.get_selected_events()
            print(f"✓ After manual selection: {len(selected_after_manual)} events selected")
            
            if len(selected_after_manual) == 1:
                print("✓ Manual selection works")
            else:
                print(f"❌ Manual selection failed: expected 1, got {len(selected_after_manual)}")
        
        # Dispose grid
        grid.Dispose()
        
    except Exception as e:
        print(f"❌ EventsDataGrid selection test failed: {e}")
        import traceback
        traceback.print_exc()

def test_events_data_grid_events():
    """Test EventsDataGrid event handling"""
    print("\n=== Testing EventsDataGrid Events ===")
    
    try:
        from gui_components import EventsDataGrid
        
        # Create a form to host the grid for event testing
        test_form = Form()
        test_form.Text = "Grid Events Test"
        test_form.Size = Size(800, 400)
        
        grid = EventsDataGrid()
        grid.Dock = DockStyle.Fill
        test_form.Controls.Add(grid)
        
        # Add mock method to form for testing
        test_form.edit_event_exposure_called = False
        def mock_edit_exposure(event):
            test_form.edit_event_exposure_called = True
            test_form.last_edited_event = event
            print(f"  ✓ edit_event_exposure called for: {event.event_name if hasattr(event, 'event_name') else 'Unknown'}")
        
        test_form.edit_event_exposure = mock_edit_exposure
        
        # Create test events
        test_events = [
            MockOccultationEvent("Event Handler Test 1"),
            MockOccultationEvent("Event Handler Test 2"),
        ]
        
        grid.update_events(test_events)
        print(f"✓ Grid populated with {len(test_events)} events")
        
        # Test double-click event on exposure column
        if grid.Rows.Count > 0:
            # Find the ExposureMs column index
            exposure_col_index = -1
            for i in range(grid.Columns.Count):
                if grid.Columns[i].Name == "ExposureMs":
                    exposure_col_index = i
                    break
            
            if exposure_col_index >= 0:
                print(f"✓ Found ExposureMs column at index {exposure_col_index}")
                
                # Create mock event args for double-click
                class MockDataGridViewCellEventArgs:
                    def __init__(self, col_index, row_index):
                        self.ColumnIndex = col_index
                        self.RowIndex = row_index
                
                mock_args = MockDataGridViewCellEventArgs(exposure_col_index, 0)
                
                try:
                    # Call the double-click handler directly
                    grid.cell_double_click(grid, mock_args)
                    
                    if test_form.edit_event_exposure_called:
                        print("✓ Double-click on exposure column triggers edit")
                    else:
                        print("❌ Double-click on exposure column did not trigger edit")
                        
                except Exception as e:
                    print(f"⚠ Double-click test error: {e}")
            else:
                print("❌ ExposureMs column not found")
        
        # Test OWC link click
        if grid.Rows.Count > 0:
            # Find OWC column
            owc_col_index = -1
            for i in range(grid.Columns.Count):
                if grid.Columns[i].Name == "OWCLink":
                    owc_col_index = i
                    break
            
            if owc_col_index >= 0:
                print(f"✓ Found OWCLink column at index {owc_col_index}")
                
                # Mock webbrowser.open to test URL opening
                original_open = webbrowser.open
                opened_urls = []
                
                def mock_open(url):
                    opened_urls.append(url)
                    print(f"  ✓ Would open URL: {url}")
                
                webbrowser.open = mock_open
                
                try:
                    mock_args = MockDataGridViewCellEventArgs(owc_col_index, 0)
                    grid.cell_content_click(grid, mock_args)
                    
                    if opened_urls:
                        print("✓ OWC link click opens URL")
                    else:
                        print("❌ OWC link click did not open URL")
                
                except Exception as e:
                    print(f"⚠ OWC link test error: {e}")
                finally:
                    webbrowser.open = original_open
            else:
                print("❌ OWCLink column not found")
        
        # Dispose form and grid
        test_form.Dispose()
        
        print("✓ Event handling tests completed")
        
    except Exception as e:
        print(f"❌ EventsDataGrid events test failed: {e}")
        import traceback
        traceback.print_exc()

def test_events_data_grid_data_formatting():
    """Test EventsDataGrid data formatting and display"""
    print("\n=== Testing EventsDataGrid Data Formatting ===")
    
    try:
        from gui_components import EventsDataGrid
        
        grid = EventsDataGrid()
        
        # Create events with various data scenarios
        test_events = [
            MockOccultationEvent("Normal Event", hours_future=2),
            MockOccultationEvent("Past Event", hours_future=-2),
            MockOccultationEvent("Soon Event", hours_future=0.1),
        ]
        
        # Modify events for specific testing
        # Event with zero/missing data
        test_events.append(MockOccultationEvent("Zero Data Event"))
        test_events[-1].star_mag = 0
        test_events[-1].comb_mag = 0
        test_events[-1].mag_drop = 0
        test_events[-1].star_alt = 0
        test_events[-1].star_az = 0
        
        # Event with custom exposure
        test_events.append(MockOccultationEvent("Custom Exposure Event"))
        test_events[-1].custom_exposure = 200  # Custom exposure
        
        grid.update_events(test_events)
        print(f"✓ Grid updated with {len(test_events)} test events")
        
        # Check data formatting in each row
        for i in range(grid.Rows.Count):
            row = grid.Rows[i]
            event = test_events[i] if i < len(test_events) else None
            
            print(f"\n✓ Row {i+1} formatting:")
            
            # Check date/time formatting
            datetime_val = row.Cells["DateTime"].Value
            print(f"  - DateTime: {datetime_val}")
            
            # Check magnitude formatting
            star_mag_val = row.Cells["StarMag"].Value
            comb_mag_val = row.Cells["CombMag"].Value
            mag_drop_val = row.Cells["MagDrop"].Value
            
            print(f"  - Star Mag: {star_mag_val}")
            print(f"  - Comb Mag: {comb_mag_val}")
            print(f"  - Mag Drop: {mag_drop_val}")
            
            # Check for "N/A" handling of zero values
            if event and event.star_mag == 0:
                if "N/A" in str(star_mag_val):
                    print("  ✓ Zero star magnitude shows as N/A")
                else:
                    print("  ❌ Zero star magnitude not handled as N/A")
            
            # Check exposure formatting
            exposure_val = row.Cells["ExposureMs"].Value
            print(f"  - Exposure: {exposure_val}")
            
            if event and event.has_custom_exposure():
                if "*" in str(exposure_val):
                    print("  ✓ Custom exposure marked with *")
                else:
                    print("  ❌ Custom exposure not marked with *")
            
            # Check coordinate formatting
            coord_val = row.Cells["Coordinates"].Value
            print(f"  - Coordinates: {coord_val}")
            
            if "h" in str(coord_val) and "°" in str(coord_val):
                print("  ✓ Coordinates properly formatted with units")
            else:
                print("  ❌ Coordinates missing proper units")
            
            # Check status formatting
            status_val = row.Cells["Status"].Value
            print(f"  - Status: {status_val}")
            
            # Check OWC link
            owc_val = row.Cells["OWCLink"].Value
            print(f"  - OWC: {owc_val}")
            
            if event and event.owcloudurl:
                if "OWC" in str(owc_val):
                    print("  ✓ OWC link displayed")
                else:
                    print("  ❌ OWC link not displayed properly")
        
        # Dispose grid
        grid.Dispose()
        
    except Exception as e:
        print(f"❌ EventsDataGrid data formatting test failed: {e}")
        import traceback
        traceback.print_exc()

def test_events_data_grid_performance():
    """Test EventsDataGrid performance with many events"""
    print("\n=== Testing EventsDataGrid Performance ===")
    
    try:
        import time
        from gui_components import EventsDataGrid
        
        grid = EventsDataGrid()
        
        # Create many test events
        num_events = 100
        print(f"✓ Creating {num_events} test events...")
        
        start_time = time.time()
        
        test_events = []
        for i in range(num_events):
            event = MockOccultationEvent(f"Performance Event {i+1}", hours_future=1+(i%24))
            test_events.append(event)
        
        creation_time = time.time() - start_time
        print(f"✓ Event creation: {creation_time:.3f}s ({creation_time/num_events*1000:.1f}ms per event)")
        
        # Test grid update performance
        start_time = time.time()
        grid.update_events(test_events)
        update_time = time.time() - start_time
        
        print(f"✓ Grid update: {update_time:.3f}s ({update_time/num_events*1000:.1f}ms per event)")
        print(f"✓ Rows created: {grid.Rows.Count}")
        
        if grid.Rows.Count == num_events:
            print("✓ All events successfully added to grid")
        else:
            print(f"❌ Expected {num_events} rows, got {grid.Rows.Count}")
        
        # Test selection performance
        start_time = time.time()
        grid.select_all_events(True)
        selection_time = time.time() - start_time
        
        print(f"✓ Select all: {selection_time:.3f}s")
        
        # Test get selected performance
        start_time = time.time()
        selected = grid.get_selected_events()
        get_selected_time = time.time() - start_time
        
        print(f"✓ Get selected: {get_selected_time:.3f}s ({len(selected)} events)")
        
        # Performance summary
        total_time = creation_time + update_time + selection_time + get_selected_time
        print(f"✓ Total performance test time: {total_time:.3f}s")
        
        if update_time < 1.0:  # Should update 100 events in under 1 second
            print("✓ Performance is acceptable")
        else:
            print("⚠ Performance may be slow for large datasets")
        
        # Dispose grid
        grid.Dispose()
        
    except Exception as e:
        print(f"❌ EventsDataGrid performance test failed: {e}")
        import traceback
        traceback.print_exc()

def test_events_data_grid_edge_cases():
    """Test EventsDataGrid with edge cases and error conditions"""
    print("\n=== Testing EventsDataGrid Edge Cases ===")
    
    try:
        from gui_components import EventsDataGrid
        
        grid = EventsDataGrid()
        
        # Test with empty event list
        print("✓ Testing empty event list...")
        grid.update_events([])
        
        if grid.Rows.Count == 0:
            print("✓ Empty event list handled correctly")
        else:
            print(f"❌ Expected 0 rows for empty list, got {grid.Rows.Count}")
        
        # Test with None event list
        try:
            grid.update_events(None)
            print("❌ None event list should raise error")
        except Exception:
            print("✓ None event list properly rejected")
        
        # Test with malformed events
        class BrokenEvent:
            def __init__(self):
                self.selected = True
                # Missing many required attributes
        
        broken_events = [BrokenEvent()]
        
        try:
            grid.update_events(broken_events)
            print("⚠ Malformed events handled gracefully")
        except Exception as e:
            print(f"✓ Malformed events properly rejected: {type(e).__name__}")
        
        # Test with events having None values
        class EventWithNones:
            def __init__(self):
                self.selected = True
                self.event_name = None
                self.station_name = None
                self.event_date = None
                self.event_time_utc = None
                self.star_mag = None
                self.comb_mag = None
                self.mag_drop = None
                self.exposure_ms = None
                self.recording_duration = None
                self.max_duration_seconds = None
                self.uncertainty_seconds = None
                self.star_alt = None
                self.star_az = None
                self.owcloudurl = None
                
            def get_asteroid_display_name(self):
                return "Unknown Asteroid"
            def has_custom_exposure(self):
                return False
            def get_coordinates_string(self):
                return "N/A"
            def get_status_info(self):
                return "Unknown Status"
        
        none_events = [EventWithNones()]
        
        try:
            grid.update_events(none_events)
            print("✓ Events with None values handled")
            
            if grid.Rows.Count == 1:
                row = grid.Rows[0]
                # Check that N/A or default values appear
                datetime_val = row.Cells["DateTime"].Value
                if "N/A" in str(datetime_val) or datetime_val is None:
                    print("✓ None datetime handled appropriately")
                
        except Exception as e:
            print(f"⚠ Events with None values caused error: {e}")
        
        # Test very long event names
        long_name_event = MockOccultationEvent("A" * 200)  # Very long name
        
        try:
            grid.update_events([long_name_event])
            print("✓ Long event names handled")
        except Exception as e:
            print(f"⚠ Long event names caused error: {e}")
        
        # Test special characters in names
        special_char_event = MockOccultationEvent("Event with special chars: !@#$%^&*()[]{}|\\:;\"'<>?,.`~")
        
        try:
            grid.update_events([special_char_event])
            print("✓ Special characters in names handled")
        except Exception as e:
            print(f"⚠ Special characters caused error: {e}")
        
        # Dispose grid
        grid.Dispose()
        
        print("✓ Edge cases testing completed")
        
    except Exception as e:
        print(f"❌ EventsDataGrid edge cases test failed: {e}")
        import traceback
        traceback.print_exc()

def visual_test_events_data_grid():
    """Visual test of EventsDataGrid - shows actual working grid"""
    print("\n=== Visual EventsDataGrid Test ===")
    print("This will show a form with the EventsDataGrid")
    
    try:
        from gui_components import EventsDataGrid
        
        class GridTestForm(Form):
            def __init__(self):
                Form.__init__(self)
                self.setup_ui()
                self.populate_grid()
            
            def setup_ui(self):
                self.Text = "EventsDataGrid Visual Test"
                self.Size = Size(1200, 600)
                self.StartPosition = FormStartPosition.CenterScreen
                
                # Create grid
                self.grid = EventsDataGrid()
                self.grid.Location = Point(10, 50)
                self.grid.Size = Size(1160, 500)
                self.Controls.Add(self.grid)
                
                # Add buttons for testing
                btn_select_all = Button()
                btn_select_all.Text = "Select All"
                btn_select_all.Location = Point(10, 10)
                btn_select_all.Size = Size(80, 25)
                btn_select_all.Click += self.select_all_click
                self.Controls.Add(btn_select_all)
                
                btn_select_none = Button()
                btn_select_none.Text = "Select None"
                btn_select_none.Location = Point(100, 10)
                btn_select_none.Size = Size(80, 25)
                btn_select_none.Click += self.select_none_click
                self.Controls.Add(btn_select_none)
                
                btn_add_events = Button()
                btn_add_events.Text = "Add More Events"
                btn_add_events.Location = Point(190, 10)
                btn_add_events.Size = Size(100, 25)
                btn_add_events.Click += self.add_events_click
                self.Controls.Add(btn_add_events)
                
                self.lbl_status = Label()
                self.lbl_status.Text = "Ready"
                self.lbl_status.Location = Point(300, 15)
                self.lbl_status.Size = Size(200, 20)
                self.Controls.Add(self.lbl_status)
                
                # Add edit exposure method for testing
                self.edit_event_exposure = self.mock_edit_exposure
            
            def populate_grid(self):
                events = [
                    MockOccultationEvent("433 Eros", hours_future=2, custom_exposure=False),
                    MockOccultationEvent("2024 AB1", hours_future=1, custom_exposure=True),
                    MockOccultationEvent("Ceres", hours_future=0.5, custom_exposure=False),
                    MockOccultationEvent("Vesta", hours_future=-1, custom_exposure=False),  # Past
                    MockOccultationEvent("Pallas", hours_future=3, custom_exposure=True),
                ]
                
                self.grid.update_events(events)
                self.update_status()
            
            def select_all_click(self, sender, e):
                self.grid.select_all_events(True)
                self.update_status()
            
            def select_none_click(self, sender, e):
                self.grid.select_all_events(False)
                self.update_status()
            
            def add_events_click(self, sender, e):
                # Add some more events
                current_events = self.grid.events[:]
                new_events = [
                    MockOccultationEvent(f"New Event {len(current_events)+1}", hours_future=4),
                    MockOccultationEvent(f"New Event {len(current_events)+2}", hours_future=5, custom_exposure=True)
                ]
                
                all_events = current_events + new_events
                self.grid.update_events(all_events)
                self.update_status()
            
            def update_status(self):
                selected = self.grid.get_selected_events()
                total = len(self.grid.events)
                self.lbl_status.Text = f"Total: {total}, Selected: {len(selected)}"
            
            def mock_edit_exposure(self, event):
                MessageBox.Show(f"Edit exposure for: {event.event_name}\nCurrent: {event.exposure_ms}ms", 
                              "Mock Edit Exposure", MessageBoxButtons.OK, MessageBoxIcon.Information)
        
        print("✓ Creating visual test form...")
        form = GridTestForm()
        
        print("✓ Showing form - test the grid functionality:")
        print("  - Click checkboxes to select/deselect events")
        print("  - Double-click exposure values to test editing")
        print("  - Click OWC links to test URL opening")
        print("  - Use buttons to test selection operations")
        print("  Close the form when done testing")
        
        Application.Run(form)
        print("✓ Visual test completed")
        
    except Exception as e:
        print(f"❌ Visual test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("GUI Components Module Standalone Test")
    print("=" * 50)
    
    try:
        # Test module import
        from gui_components import EventsDataGrid
        print("✓ GUI Components module imported successfully")
        
        # Run all tests
        test_events_data_grid_creation()
        test_events_data_grid_update()
        test_events_data_grid_selection()
        test_events_data_grid_events()
        test_events_data_grid_data_formatting()
        test_events_data_grid_performance()
        test_events_data_grid_edge_cases()
        
        # Ask user if they want to run visual test
        print("\n" + "=" * 50)
        print("✓ All automated tests completed!")
        
        print("\nWould you like to run the visual test? (shows actual grid)")
        print("Enter 'y' for yes, any other key to skip:")
        
        try:
            user_input = input().strip().lower()
            if user_input == 'y':
                visual_test_events_data_grid()
        except:
            print("Visual test skipped")
        
        print("\n" + "=" * 50)
        print("✓ All GUI Components tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure gui_components.py is in the same directory")
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