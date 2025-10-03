# test_main_gui.py - Standalone test for main_gui.py module

import sys
import os
import tempfile
import shutil
import threading
import time
from datetime import datetime, timedelta

# Add the module directory to Python path if needed
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

# Import required GUI libraries
import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Point, Size, Color, SystemColors, Font, FontStyle
from System.Windows.Forms import *
import System

# Mock all dependencies
class MockThemeManager:
    """Mock theme manager for testing"""
    
    def __init__(self):
        self.is_night_mode = False
    
    def get_current_theme(self):
        return {
            'background': SystemColors.Control,
            'text_foreground': SystemColors.ControlText,
            'button_background': SystemColors.ButtonFace,
            'button_text': SystemColors.ButtonText,
            'textbox_background': SystemColors.Window,
            'groupbox_background': SystemColors.Control,
            'grid_background': SystemColors.Window,
            'grid_foreground': SystemColors.WindowText,
            'grid_selection': SystemColors.Highlight
        }
    
    def toggle_night_mode(self):
        self.is_night_mode = not self.is_night_mode
        return self.is_night_mode
    
    def set_night_mode(self, enabled):
        self.is_night_mode = enabled

class MockConfigManager:
    """Mock config manager for testing"""
    
    def __init__(self):
        self.test_folder = tempfile.mkdtemp(prefix='main_gui_test_')
        self.night_mode = False
    
    def get_sequence_path(self):
        return self.test_folder
    
    def set_sequence_path(self, path):
        pass
    
    def get_night_mode(self):
        return self.night_mode
    
    def set_night_mode(self, enabled):
        self.night_mode = enabled
    
    def save_config(self):
        return True
    
    def cleanup(self):
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)

class MockOccultationEvent:
    """Mock OccultationEvent for testing"""
    
    def __init__(self, name="Mock Event", hours_future=1):
        self.event_name = name
        self.object_name = "Mock Asteroid"
        self.station_name = "Mock Station"
        self.selected = True
        self.exposure_ms = 80
        self.custom_exposure = None
        
        # Times
        now = datetime.utcnow()
        self.event_datetime = now + timedelta(hours=hours_future)
        self.goto_time = self.event_datetime - timedelta(minutes=5)
        
        # Other attributes
        self.ra = 15.5
        self.dec = 45.2
        self.star_mag = 11.5
        self.recording_duration = 60
    
    def get_asteroid_display_name(self):
        return self.object_name
    
    def has_custom_exposure(self):
        return self.custom_exposure is not None
    
    def set_custom_exposure(self, ms):
        self.custom_exposure = ms / 1000.0
        self.exposure_ms = ms
    
    def get_exposure_seconds(self):
        return self.exposure_ms / 1000.0

class MockOccultationManager:
    """Mock OccultationManager for testing"""
    
    def __init__(self, config):
        self.config = config
        self.events = []
        self.all_events = []
        self.selected_events = set()
    
    def load_events_from_files(self):
        # Create some mock events
        self.all_events = [
            MockOccultationEvent("Mock Event 1", 1),
            MockOccultationEvent("Mock Event 2", 2),
            MockOccultationEvent("Past Event", -1),
        ]
        self.events = self.all_events[:]
        return True
    
    def download_events_from_cloud(self):
        return 3
    
    def get_filtered_events(self):
        return self.events
    
    def get_all_stations(self):
        return ["Mock Station", "Test Station"]
    
    def set_station_filter(self, filter_text):
        pass
    
    def clear_station_filter(self):
        self.events = self.all_events[:]

class MockSequenceRunner:
    """Mock SequenceRunner for testing"""
    
    def __init__(self, config):
        self.config = config
        self.running = False
    
    def run_sequences(self, events, callback):
        callback("Mock sequence execution started")
        time.sleep(0.1)  # Brief pause
        callback("Mock sequence execution completed")
        return True

class MockEventsDataGrid:
    """Mock EventsDataGrid for testing"""
    
    def __init__(self):
        self.events = []
        self.Rows = type('MockRows', (), {'Count': 0})()
        self.SelectedRows = []
        self.SelectionChanged = None
    
    def update_events(self, events):
        self.events = events
        self.Rows.Count = len(events)
    
    def get_selected_events(self):
        return [e for e in self.events if e.selected]
    
    def select_all_events(self, select):
        for event in self.events:
            event.selected = select
    
    def __setattr__(self, name, value):
        # Allow setting event handlers
        super(MockEventsDataGrid, self).__setattr__(name, value)

class MockTemplateManager:
    """Mock TemplateManager for testing"""
    
    def __init__(self, config):
        self.config = config
    
    @staticmethod
    def load_template(template_path, config=None):
        return "# Mock template content\nGOTO {ra} {dec}\nEXPOSE {exposure}"

# Mock all the imported modules
def setup_mocks():
    """Setup all required mocks"""
    # Mock theme
    def mock_apply_theme(control, theme):
        pass
    
    sys.modules['theme'] = type('MockModule', (), {
        'apply_theme_to_control': mock_apply_theme
    })()
    
    # Mock events
    sys.modules['events'] = type('MockModule', (), {
        'OccultationManager': MockOccultationManager
    })()
    
    # Mock sequence_runner
    sys.modules['sequence_runner'] = type('MockModule', (), {
        'SequenceRunner': MockSequenceRunner
    })()
    
    # Mock gui_components
    sys.modules['gui_components'] = type('MockModule', (), {
        'EventsDataGrid': MockEventsDataGrid
    })()
    
    # Mock gui_dialogs
    class MockDialog:
        def __init__(self, *args):
            self.ShowDialog = lambda: DialogResult.OK
            self.Dispose = lambda: None
            self.get_selected_template_path = lambda: ""
            self.get_new_exposure = lambda: 150
    
    sys.modules['gui_dialogs'] = type('MockModule', (), {
        'ExposureEditDialog': MockDialog,
        'EventDetailsDialog': MockDialog,
        'ConfigurationDialog': MockDialog,
        'TemplateSelectionDialog': MockDialog
    })()
    
    # Mock templates
    sys.modules['templates'] = type('MockModule', (), {
        'TemplateManager': MockTemplateManager
    })()
    
    # Mock utils
    def mock_save_sequence(event, template_path, sequence_path, config):
        return True
    
    def mock_simple_goto(event):
        return True
    
    sys.modules['utils'] = type('MockModule', (), {
        'save_occultation_sequence': mock_save_sequence,
        'simple_goto_event': mock_simple_goto
    })()

def test_main_gui_creation():
    """Test OccultationManagerGUI creation and basic setup"""
    print("\n=== Testing OccultationManagerGUI Creation ===")
    
    try:
        setup_mocks()
        
        from main_gui import OccultationManagerGUI
        
        config = MockConfigManager()
        theme_manager = MockThemeManager()
        
        print("✓ Creating OccultationManagerGUI...")
        gui = OccultationManagerGUI(config, theme_manager)
        
        print(f"✓ Main GUI created: {gui.Text}")
        print(f"✓ Window size: {gui.Size}")
        print(f"✓ Start position: {gui.StartPosition}")
        
        # Check that key components were created
        has_menu = gui.MainMenuStrip is not None
        print(f"✓ Menu bar created: {has_menu}")
        
        # Count controls
        control_count = 0
        for control in gui.Controls:
            control_count += 1
        
        print(f"✓ Main controls created: {control_count}")
        
        # Check for key attributes
        if hasattr(gui, 'manager'):
            print("✓ Manager component initialized")
        
        if hasattr(gui, 'sequence_runner'):
            print("✓ Sequence runner component initialized")
        
        if hasattr(gui, 'events_grid'):
            print("✓ Events grid component initialized")
        
        # Dispose GUI
        gui.Dispose()
        config.cleanup()
        
        print("✓ OccultationManagerGUI creation test completed")
        
    except Exception as e:
        print(f"❌ OccultationManagerGUI creation test failed: {e}")
        import traceback
        traceback.print_exc()

def test_main_gui_menu_creation():
    """Test menu bar creation and structure"""
    print("\n=== Testing Menu Bar Creation ===")
    
    try:
        setup_mocks()
        
        from main_gui import OccultationManagerGUI
        
        config = MockConfigManager()
        theme_manager = MockThemeManager()
        
        gui = OccultationManagerGUI(config, theme_manager)
        
        menu_bar = gui.MainMenuStrip
        if menu_bar:
            print(f"✓ Menu bar created with {menu_bar.Items.Count} items")
            
            menu_names = []
            for i in range(menu_bar.Items.Count):
                menu_item = menu_bar.Items[i]
                menu_names.append(menu_item.Text)
            
            print("✓ Menu items:")
            for menu in menu_names:
                print(f"  - {menu}")
            
            expected_menus = ["File", "Events", "Sequences", "Tools", "Help"]
            if all(menu in menu_names for menu in expected_menus):
                print("✓ All expected menus present")
            else:
                missing = [menu for menu in expected_menus if menu not in menu_names]
                print(f"❌ Missing menus: {missing}")
            
            # Check Help menu specifically
            help_menu = None
            for i in range(menu_bar.Items.Count):
                if menu_bar.Items[i].Text == "Help":
                    help_menu = menu_bar.Items[i]
                    break
            
            if help_menu and hasattr(help_menu, 'DropDownItems'):
                help_items = []
                for j in range(help_menu.DropDownItems.Count):
                    help_items.append(help_menu.DropDownItems[j].Text)
                
                print(f"✓ Help menu items: {help_items}")
                
                if "User Guide" in help_items:
                    print("✓ User Guide menu item present")
                else:
                    print("❌ User Guide menu item missing")
        else:
            print("❌ Menu bar not created")
        
        gui.Dispose()
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Menu bar creation test failed: {e}")
        import traceback
        traceback.print_exc()

def test_main_gui_event_handlers():
    """Test main GUI event handler methods"""
    print("\n=== Testing Main GUI Event Handlers ===")
    
    try:
        setup_mocks()
        
        from main_gui import OccultationManagerGUI
        
        config = MockConfigManager()
        theme_manager = MockThemeManager()
        
        gui = OccultationManagerGUI(config, theme_manager)
        
        # Test status update
        gui.update_status("Test status message")
        if hasattr(gui, 'lbl_status') and gui.lbl_status.Text == "Test status message":
            print("✓ update_status method works")
        else:
            print("⚠ update_status method may not be working properly")
        
        # Test refresh display
        try:
            gui.refresh_display()
            print("✓ refresh_display method executed without error")
        except Exception as e:
            print(f"⚠ refresh_display error: {e}")
        
        # Test get_displayed_selected_events
        try:
            selected = gui.get_displayed_selected_events()
            print(f"✓ get_displayed_selected_events returned {len(selected)} events")
        except Exception as e:
            print(f"⚠ get_displayed_selected_events error: {e}")
        
        # Test theme toggle
        try:
            original_mode = theme_manager.is_night_mode
            gui.toggle_night_mode_click(None, None)
            new_mode = theme_manager.is_night_mode
            
            if new_mode != original_mode:
                print("✓ Night mode toggle works")
            else:
                print("❌ Night mode toggle failed")
        except Exception as e:
            print(f"⚠ Night mode toggle error: {e}")
        
        gui.Dispose()
        config.cleanup()
        
        print("✓ Event handlers test completed")
        
    except Exception as e:
        print(f"❌ Main GUI event handlers test failed: {e}")
        import traceback
        traceback.print_exc()

def test_main_gui_preparation_methods():
    """Test observation preparation methods"""
    print("\n=== Testing Observation Preparation Methods ===")
    
    try:
        setup_mocks()
        
        from main_gui import OccultationManagerGUI
        
        config = MockConfigManager()
        theme_manager = MockThemeManager()
        
        gui = OccultationManagerGUI(config, theme_manager)
        
        # Test get_first_selected_event
        try:
            first_event = gui.get_first_selected_event()
            print(f"✓ get_first_selected_event returned: {type(first_event).__name__ if first_event else 'None'}")
        except Exception as e:
            print(f"⚠ get_first_selected_event error: {e}")
        
        # Test loading event for preparation
        if hasattr(gui.manager, 'all_events') and gui.manager.all_events:
            test_event = gui.manager.all_events[0]
            gui._preparation_event = test_event
            
            try:
                gui.update_preparation_display()
                print("✓ update_preparation_display executed without error")
                
                if hasattr(gui, 'lbl_current_event'):
                    current_text = gui.lbl_current_event.Text
                    if test_event.object_name in current_text:
                        print("✓ Preparation display shows event information")
                    else:
                        print("⚠ Preparation display may not be updating correctly")
                
            except Exception as e:
                print(f"⚠ update_preparation_display error: {e}")
        
        # Test button enabling/disabling
        try:
            gui.enable_preparation_buttons(True)
            gui.enable_preparation_buttons(False)
            print("✓ enable_preparation_buttons executed without error")
        except Exception as e:
            print(f"⚠ enable_preparation_buttons error: {e}")
        
        gui.Dispose()
        config.cleanup()
        
        print("✓ Preparation methods test completed")
        
    except Exception as e:
        print(f"❌ Preparation methods test failed: {e}")
        import traceback
        traceback.print_exc()

def test_main_gui_sequence_methods():
    """Test sequence-related methods"""
    print("\n=== Testing Sequence Methods ===")
    
    try:
        setup_mocks()
        
        from main_gui import OccultationManagerGUI
        
        config = MockConfigManager()
        theme_manager = MockThemeManager()
        
        gui = OccultationManagerGUI(config, theme_manager)
        
        # Test generate_sequences_for_events
        try:
            success, error, message = gui.generate_sequences_for_events("")
            print(f"✓ generate_sequences_for_events: {success} success, {error} errors")
            print(f"  Message: {message}")
        except Exception as e:
            print(f"⚠ generate_sequences_for_events error: {e}")
        
        # Test format_template
        try:
            template_content = "Event: {object_name}, RA: {ra}, Dec: {dec}, Exposure: {exposure}"
            test_event = MockOccultationEvent("Template Test Event")
            
            formatted = gui.format_template(template_content, test_event)
            print(f"✓ format_template result: {formatted[:50]}...")
            
            # Check that variables were substituted
            if test_event.object_name in formatted:
                print("✓ Template variable substitution works")
            else:
                print("❌ Template variable substitution failed")
                
        except Exception as e:
            print(f"⚠ format_template error: {e}")
        
        # Test get_tonights_events
        try:
            tonight_events = gui.get_tonights_events()
            print(f"✓ get_tonights_events returned {len(tonight_events)} events")
        except Exception as e:
            print(f"⚠ get_tonights_events error: {e}")
        
        gui.Dispose()
        config.cleanup()
        
        print("✓ Sequence methods test completed")
        
    except Exception as e:
        print(f"❌ Sequence methods test failed: {e}")
        import traceback
        traceback.print_exc()

def test_main_gui_threading():
    """Test threading functionality"""
    print("\n=== Testing Threading Functionality ===")
    
    try:
        setup_mocks()
        
        from main_gui import OccultationManagerGUI
        
        config = MockConfigManager()
        theme_manager = MockThemeManager()
        
        gui = OccultationManagerGUI(config, theme_manager)
        
        # Test thread-safe status update
        status_messages = []
        
        # Override update_status to capture messages
        original_update_status = gui.update_status
        def capture_update_status(message):
            status_messages.append(message)
            original_update_status(message)
        gui.update_status = capture_update_status
        
        # Test thread-safe update
        try:
            gui.update_status_safe("Thread-safe test message")
            print("✓ update_status_safe executed without error")
            
            if "Thread-safe test message" in status_messages:
                print("✓ Thread-safe status message captured")
            else:
                print("⚠ Thread-safe status message not captured")
                
        except Exception as e:
            print(f"⚠ update_status_safe error: {e}")
        
        # Test background sequence execution setup (don't actually run)
        try:
            # This tests the threading setup without actually running sequences
            future_events = [e for e in gui.manager.all_events 
                           if hasattr(e, 'event_datetime') and e.event_datetime > datetime.utcnow()]
            
            if future_events:
                print(f"✓ Found {len(future_events)} future events for threading test")
                
                # Test that threading function can be created (don't execute)
                def test_background_function():
                    gui.sequence_runner.run_sequences(future_events, gui.update_status_safe)
                
                thread = threading.Thread(target=test_background_function)
                thread.IsBackground = True
                print("✓ Background thread created successfully")
                
                # Don't actually start the thread in test
            else:
                print("✓ No future events for threading test (expected)")
                
        except Exception as e:
            print(f"⚠ Threading setup error: {e}")
        
        gui.Dispose()
        config.cleanup()
        
        print("✓ Threading functionality test completed")
        
    except Exception as e:
        print(f"❌ Threading functionality test failed: {e}")
        import traceback
        traceback.print_exc()

def visual_test_main_gui():
    """Visual test of main GUI - shows actual working interface"""
    print("\n=== Visual Main GUI Test ===")
    print("This will show the actual main GUI interface")
    
    try:
        setup_mocks()
        
        from main_gui import OccultationManagerGUI
        
        config = MockConfigManager()
        theme_manager = MockThemeManager()
        
        print("✓ Creating main GUI for visual test...")
        
        # Create GUI
        gui = OccultationManagerGUI(config, theme_manager)
        
        print("✓ Main GUI created successfully")
        print("✓ Showing GUI - test the following features:")
        print("  - Menu bar items (File, Events, Sequences, Tools, Help)")
        print("  - Toolbar buttons")
        print("  - Station filter dropdown")
        print("  - Events grid (should show mock events)")
        print("  - Bottom panel controls")
        print("  - Night mode toggle")
        print("  - Status bar")
        print("  - Close the window when done testing")
        
        # Show the GUI
        Application.Run(gui)
        
        config.cleanup()
        print("✓ Visual main GUI test completed")
        
    except Exception as e:
        print(f"❌ Visual main GUI test failed: {e}")
        import traceback
        traceback.print_exc()

def quick_test_main_gui():
    """Quick validation test for main GUI"""
    print("\n=== Quick Main GUI Test ===")
    
    try:
        setup_mocks()
        
        from main_gui import OccultationManagerGUI
        
        config = MockConfigManager()
        theme_manager = MockThemeManager()
        
        # Test creation without showing
        gui = OccultationManagerGUI(config, theme_manager)
        print("✓ Main GUI creates without errors")
        
        # Test basic properties
        assert gui.Text == "Occultation Manager - SharpCap Integration", "Window title incorrect"
        assert gui.Size.Width == 1400 and gui.Size.Height == 800, "Window size incorrect"
        print("✓ Basic properties correct")
        
        # Test that components exist
        components = ['manager', 'sequence_runner', 'events_grid', 'theme_manager', 'config']
        for component in components:
            if hasattr(gui, component):
                print(f"✓ {component} component exists")
            else:
                print(f"❌ {component} component missing")
        
        # Test a simple method call
        try:
            gui.update_status("Quick test status")
            print("✓ Basic method call works")
        except Exception as e:
            print(f"⚠ Basic method call error: {e}")
        
        gui.Dispose()
        config.cleanup()
        
        print("✓ Quick main GUI test completed")
        
    except Exception as e:
        print(f"❌ Quick main GUI test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("Main GUI Module Standalone Test")
    print("=" * 50)
    
    try:
        print("✓ Setting up mocks...")
        setup_mocks()
        
        # Test module import
        from main_gui import OccultationManagerGUI
        print("✓ Main GUI module imported successfully")
        
        # Run automated tests
        test_main_gui_creation()
        test_main_gui_menu_creation()
        test_main_gui_event_handlers()
        test_main_gui_preparation_methods()
        test_main_gui_sequence_methods()
        test_main_gui_threading()
        quick_test_main_gui()
        
        print("\n" + "=" * 50)
        print("✓ All automated main GUI tests completed!")
        
        # Ask user if they want to run visual test
        print("\nWould you like to run the visual test? (shows actual main GUI)")
        print("Enter 'y' for yes, any other key to skip:")
        
        try:
            user_input = input().strip().lower()
            if user_input == 'y':
                visual_test_main_gui()
        except:
            print("Visual test skipped")
        
        print("\n" + "=" * 50)
        print("✓ All Main GUI tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure main_gui.py and all dependencies are in the same directory")
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