# test_gui_dialogs.py - Standalone test for gui_dialogs.py module

import sys
import os
import tempfile
import shutil
from datetime import datetime, timedelta

# Add the module directory to Python path if needed
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

# Import required GUI libraries
import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Point, Size, Color, Font, FontStyle
from System.Windows.Forms import *

# Mock dependencies for testing
class MockThemeManager:
    """Mock theme manager for testing dialogs"""
    
    def __init__(self):
        self.is_night_mode = False
    
    def get_current_theme(self):
        """Return simple theme for testing"""
        if self.is_night_mode:
            return {
                'background': Color.FromArgb(40, 0, 0),
                'text_foreground': Color.FromArgb(255, 200, 200),
                'button_background': Color.FromArgb(80, 20, 20),
                'button_text': Color.FromArgb(255, 200, 200),
                'textbox_background': Color.FromArgb(70, 10, 10),
                'groupbox_background': Color.FromArgb(45, 0, 0)
            }
        else:
            return {
                'background': SystemColors.Control,
                'text_foreground': SystemColors.ControlText,
                'button_background': SystemColors.ButtonFace,
                'button_text': SystemColors.ButtonText,
                'textbox_background': SystemColors.Window,
                'groupbox_background': SystemColors.Control
            }
    
    def toggle_night_mode(self):
        """Toggle night mode for testing"""
        self.is_night_mode = not self.is_night_mode
        return self.is_night_mode

class MockConfigManager:
    """Mock config manager for testing dialogs"""
    
    def __init__(self):
        self.test_folder = tempfile.mkdtemp(prefix='dialog_test_')
        self.config = {
            'owc_user_email': 'test@example.com',
            'owc_user_password': 'testpassword',
            'my_file_folder': self.test_folder,
            'sequence_path': self.test_folder,
            'my_occultations_file': 'test_occ.json',
            'my_latest_occultations_file': 'test_latest.json',
            'base_duration': 60,
            'goto_lead_time': 240,
            'mag_for_40ms_exposure': 12.0,
            'host': 'https://test.example.com',
            'apiKey': 'test_api_key'
        }
    
    def get_owc_email(self):
        return self.config['owc_user_email']
    def set_owc_email(self, email):
        self.config['owc_user_email'] = email
    def get_owc_password(self):
        return self.config['owc_user_password']
    def set_owc_password(self, password):
        self.config['owc_user_password'] = password
    def get_file_folder(self):
        return self.config['my_file_folder']
    def set_file_folder(self, folder):
        self.config['my_file_folder'] = folder
    def get_sequence_path(self):
        return self.config['sequence_path']
    def set_sequence_path(self, path):
        self.config['sequence_path'] = path
    def get_occultations_file(self):
        return self.config['my_occultations_file']
    def set_occultations_file(self, filename):
        self.config['my_occultations_file'] = filename
    def get_latest_occultations_file(self):
        return self.config['my_latest_occultations_file']
    def set_latest_occultations_file(self, filename):
        self.config['my_latest_occultations_file'] = filename
    def get_base_duration(self):
        return self.config['base_duration']
    def set_base_duration(self, duration):
        self.config['base_duration'] = int(duration)
    def get_goto_lead_time(self):
        return self.config['goto_lead_time']
    def set_goto_lead_time(self, time):
        self.config['goto_lead_time'] = int(time)
    def get_mag_for_40ms_exposure(self):
        return self.config['mag_for_40ms_exposure']
    def set_mag_for_40ms_exposure(self, mag):
        self.config['mag_for_40ms_exposure'] = float(mag)
    def get_host(self):
        return self.config['host']
    def set_host(self, host):
        self.config['host'] = host
    def get_api_key(self):
        return self.config['apiKey']
    def set_api_key(self, key):
        self.config['apiKey'] = key
    def validate_config(self):
        return []  # No errors for testing
    def save_config(self):
        return True
    def reset_to_defaults(self):
        return True
    def cleanup(self):
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)

class MockOccultationEvent:
    """Mock OccultationEvent for testing"""
    
    def __init__(self, name="Test Event"):
        self.event_name = name
        self.star_name = "HD 123456"
        self.star_mag = 11.5
        self.comb_mag = 11.3
        self.mag_drop = 2.1
        self.exposure_ms = 80
        self.custom_exposure = None
        self.object_name = "Test Asteroid"
        self.station_name = "Test Station"
        self.event_time = "2024-01-15T12:30:45"
        self.goto_time_str = "2024-01-15T12:26:45"
        self.start_time_str = "2024-01-15T12:30:15"
        self.end_time_str = "2024-01-15T12:30:75"
        self.recording_duration = 60
        self.max_duration_seconds = 15.5
        self.uncertainty_seconds = 3.2
        self.precalc_exposure = 0.08
        self.star_id = "HD 123456"
        self.ra = 15.5
        self.dec = 45.2
        self.star_alt = 45.8
        self.star_az = 180.3
        self.latitude = 40.123
        self.longitude = -75.456
        self.source = "OWCloud"
        self.event_id = "test_event_123"
        self.ow_eventid = 12345
        self.object_no = "2024 AB"
        self.owcloudurl = "https://cloud.occultwatcher.net/event/12345"
    
    def has_custom_exposure(self):
        return self.custom_exposure is not None
    
    def set_custom_exposure(self, exposure_ms):
        self.custom_exposure = exposure_ms / 1000.0
        self.exposure_ms = exposure_ms
    
    def get_asteroid_display_name(self):
        return f"Asteroid {self.object_name}"
    
    def _calculate_derived_values(self):
        # Simulate recalculation
        if self.custom_exposure is None:
            self.exposure_ms = 80  # Default calculated value

# Mock the theme application function
def apply_theme_to_control(control, theme_colors):
    """Simplified theme application for testing"""
    try:
        if hasattr(control, 'BackColor'):
            control.BackColor = theme_colors.get('background', SystemColors.Control)
        if hasattr(control, 'ForeColor'):
            control.ForeColor = theme_colors.get('text_foreground', SystemColors.ControlText)
    except:
        pass  # Ignore theme application errors in tests

def test_exposure_edit_dialog():
    """Test ExposureEditDialog creation and functionality"""
    print("\n=== Testing ExposureEditDialog ===")
    
    try:
        # Mock the theme module
        sys.modules['theme'] = type('MockModule', (), {
            'apply_theme_to_control': apply_theme_to_control
        })()
        
        from gui_dialogs import ExposureEditDialog
        
        theme_manager = MockThemeManager()
        event = MockOccultationEvent("Test Exposure Event")
        
        print("✓ Creating ExposureEditDialog...")
        dialog = ExposureEditDialog(event, theme_manager)
        
        print(f"✓ Dialog created: {dialog.Text}")
        print(f"✓ Dialog size: {dialog.Size}")
        print(f"✓ Initial exposure: {dialog.new_exposure_ms}ms")
        
        # Test that initial exposure matches event
        if dialog.new_exposure_ms == event.exposure_ms:
            print("✓ Initial exposure value correct")
        else:
            print(f"❌ Initial exposure wrong: expected {event.exposure_ms}, got {dialog.new_exposure_ms}")
        
        # Test validation without showing dialog
        print("✓ Testing exposure validation...")
        
        # Test valid exposure
        dialog.txt_exposure.Text = "150"
        dialog.ok_click(None, None)
        
        if dialog.DialogResult == DialogResult.OK:
            print("✓ Valid exposure accepted")
            if dialog.get_new_exposure() == 150:
                print("✓ New exposure value correct")
            else:
                print(f"❌ New exposure wrong: expected 150, got {dialog.get_new_exposure()}")
        else:
            print("❌ Valid exposure rejected")
        
        # Test invalid exposure (reset dialog result)
        dialog.DialogResult = DialogResult.None
        dialog.txt_exposure.Text = "invalid"
        dialog.ok_click(None, None)
        
        if dialog.DialogResult != DialogResult.OK:
            print("✓ Invalid exposure properly rejected")
        else:
            print("❌ Invalid exposure incorrectly accepted")
        
        # Test out of range exposure
        dialog.DialogResult = DialogResult.None
        dialog.txt_exposure.Text = "50000"  # Too high
        dialog.ok_click(None, None)
        
        if dialog.DialogResult != DialogResult.OK:
            print("✓ Out of range exposure properly rejected")
        else:
            print("❌ Out of range exposure incorrectly accepted")
        
        dialog.Dispose()
        print("✓ ExposureEditDialog test completed")
        
    except Exception as e:
        print(f"❌ ExposureEditDialog test failed: {e}")
        import traceback
        traceback.print_exc()

def test_event_details_dialog():
    """Test EventDetailsDialog creation and display"""
    print("\n=== Testing EventDetailsDialog ===")
    
    try:
        # Mock the theme module
        sys.modules['theme'] = type('MockModule', (), {
            'apply_theme_to_control': apply_theme_to_control
        })()
        
        from gui_dialogs import EventDetailsDialog
        
        theme_manager = MockThemeManager()
        event = MockOccultationEvent("Detailed Test Event")
        
        print("✓ Creating EventDetailsDialog...")
        dialog = EventDetailsDialog(event, theme_manager)
        
        print(f"✓ Dialog created: {dialog.Text}")
        print(f"✓ Dialog size: {dialog.Size}")
        print(f"✓ Dialog is sizable: {dialog.FormBorderStyle == FormBorderStyle.Sizable}")
        
        # Check that main panel was created
        main_panel = None
        for control in dialog.Controls:
            if isinstance(control, Panel) and hasattr(control, 'AutoScroll'):
                main_panel = control
                break
        
        if main_panel:
            print("✓ Main scrollable panel created")
            print(f"✓ AutoScroll enabled: {main_panel.AutoScroll}")
            
            # Count GroupBox controls (should be multiple sections)
            group_boxes = []
            for control in main_panel.Controls:
                if isinstance(control, GroupBox):
                    group_boxes.append(control.Text)
            
            print(f"✓ Found {len(group_boxes)} information sections:")
            for gb in group_boxes:
                print(f"  - {gb}")
            
            expected_sections = ["Event Information", "Timing Information", "Recording Settings", 
                               "Photometry Information", "Position Information"]
            found_expected = sum(1 for section in expected_sections 
                               if any(section in gb for gb in group_boxes))
            
            if found_expected >= 3:  # At least 3 main sections
                print("✓ Major information sections present")
            else:
                print("❌ Some major sections may be missing")
        else:
            print("❌ Main panel not found")
        
        dialog.Dispose()
        print("✓ EventDetailsDialog test completed")
        
    except Exception as e:
        print(f"❌ EventDetailsDialog test failed: {e}")
        import traceback
        traceback.print_exc()

def test_configuration_dialog():
    """Test ConfigurationDialog creation and functionality"""
    print("\n=== Testing ConfigurationDialog ===")
    
    try:
        # Mock the theme module
        sys.modules['theme'] = type('MockModule', (), {
            'apply_theme_to_control': apply_theme_to_control
        })()
        
        from gui_dialogs import ConfigurationDialog
        
        config = MockConfigManager()
        theme_manager = MockThemeManager()
        
        print("✓ Creating ConfigurationDialog...")
        dialog = ConfigurationDialog(config, theme_manager)
        
        print(f"✓ Dialog created: {dialog.Text}")
        print(f"✓ Dialog size: {dialog.Size}")
        
        # Find the TabControl
        tab_control = None
        for control in dialog.Controls:
            if isinstance(control, TabControl):
                tab_control = control
                break
        
        if tab_control:
            print(f"✓ TabControl found with {tab_control.TabPages.Count} tabs")
            
            tab_names = []
            for i in range(tab_control.TabPages.Count):
                tab_names.append(tab_control.TabPages[i].Text)
            
            print("✓ Tab pages:")
            for tab in tab_names:
                print(f"  - {tab}")
            
            expected_tabs = ["Credentials", "File Paths", "Recording", "API Settings"]
            if all(tab in tab_names for tab in expected_tabs):
                print("✓ All expected tabs present")
            else:
                missing = [tab for tab in expected_tabs if tab not in tab_names]
                print(f"❌ Missing tabs: {missing}")
        else:
            print("❌ TabControl not found")
        
        # Test that configuration values were loaded
        # Find email textbox (should be in Credentials tab)
        email_textbox = None
        def find_textbox_by_name(parent, target_name):
            for control in parent.Controls:
                if hasattr(control, 'Controls'):  # Container
                    result = find_textbox_by_name(control, target_name)
                    if result:
                        return result
                elif isinstance(control, TextBox) and hasattr(parent, 'Text') and 'Credentials' in getattr(parent, 'Text', ''):
                    # This is a textbox in the credentials tab
                    return control
            return None
        
        if tab_control and tab_control.TabPages.Count > 0:
            cred_tab = tab_control.TabPages[0]  # First tab should be credentials
            for control in cred_tab.Controls:
                if isinstance(control, TextBox):
                    if control.Text == config.get_owc_email():
                        print("✓ Email configuration loaded correctly")
                        break
        
        # Test validation and save functionality
        print("✓ Testing configuration save...")
        
        # Find and test save button
        save_button = None
        for control in dialog.Controls:
            if isinstance(control, Button) and control.Text == "Save":
                save_button = control
                break
        
        if save_button:
            print("✓ Save button found")
            
            # Test save click handler (won't actually save in test)
            try:
                dialog.save_config_click(save_button, None)
                print("✓ Save config handler executed without error")
            except Exception as e:
                print(f"⚠ Save config handler error: {e}")
        else:
            print("❌ Save button not found")
        
        dialog.Dispose()
        config.cleanup()
        print("✓ ConfigurationDialog test completed")
        
    except Exception as e:
        print(f"❌ ConfigurationDialog test failed: {e}")
        import traceback
        traceback.print_exc()

def test_template_selection_dialog():
    """Test TemplateSelectionDialog creation and functionality"""
    print("\n=== Testing TemplateSelectionDialog ===")
    
    try:
        # Mock the theme and templates modules
        sys.modules['theme'] = type('MockModule', (), {
            'apply_theme_to_control': apply_theme_to_control
        })()
        
        # Mock TemplateManager
        class MockTemplateManager:
            @staticmethod
            def find_template_files(folder):
                # Return some mock template files
                return ['template1.txt', 'advanced_template.txt', 'basic_template.txt'], folder
            
            @staticmethod
            def get_template_info(template_path):
                from datetime import datetime
                return 1234, datetime.now()  # Mock size and modification time
            
            @staticmethod
            def load_template(template_path, config=None):
                if template_path:
                    return f"# Mock template content for {os.path.basename(template_path)}\nGOTO {{ra}} {{dec}}\nEXPOSE {{exposure}}"
                else:
                    return "# Default template\nGOTO {ra} {dec}\nSTART RECORDING"
        
        sys.modules['templates'] = type('MockModule', (), {
            'TemplateManager': MockTemplateManager
        })()
        
        from gui_dialogs import TemplateSelectionDialog
        
        config = MockConfigManager()
        theme_manager = MockThemeManager()
        
        print("✓ Creating TemplateSelectionDialog...")
        dialog = TemplateSelectionDialog(config, theme_manager)
        
        print(f"✓ Dialog created: {dialog.Text}")
        print(f"✓ Dialog size: {dialog.Size}")
        print(f"✓ Dialog is sizable: {dialog.FormBorderStyle == FormBorderStyle.Sizable}")
        
        # Find the ListBox for templates
        list_box = None
        for control in dialog.Controls:
            if isinstance(control, ListBox):
                list_box = control
                break
        
        if list_box:
            print(f"✓ Template ListBox found with {list_box.Items.Count} items")
            
            if list_box.Items.Count > 0:
                print("✓ Template items:")
                for i in range(min(list_box.Items.Count, 5)):  # Show first 5
                    print(f"  - {list_box.Items[i]}")
                
                # Test selection
                list_box.SelectedIndex = 0
                print("✓ Selected first template")
                
                # Check if preview was updated
                preview_textbox = None
                for control in dialog.Controls:
                    if isinstance(control, TextBox) and control.Multiline:
                        preview_textbox = control
                        break
                
                if preview_textbox:
                    print("✓ Preview TextBox found")
                    if preview_textbox.Text:
                        print(f"✓ Preview content: {len(preview_textbox.Text)} characters")
                        if "template" in preview_textbox.Text.lower():
                            print("✓ Preview contains template content")
                    else:
                        print("⚠ Preview is empty")
                else:
                    print("❌ Preview TextBox not found")
            else:
                print("❌ No template items found")
        else:
            print("❌ Template ListBox not found")
        
        # Test get_selected_template_path
        selected_path = dialog.get_selected_template_path()
        print(f"✓ Selected template path: {selected_path if selected_path else 'Default template'}")
        
        dialog.Dispose()
        config.cleanup()
        print("✓ TemplateSelectionDialog test completed")
        
    except Exception as e:
        print(f"❌ TemplateSelectionDialog test failed: {e}")
        import traceback
        traceback.print_exc()

def test_dialog_theme_application():
    """Test theme application to dialogs"""
    print("\n=== Testing Dialog Theme Application ===")
    
    try:
        # Mock the theme module
        theme_applications = []
        
        def mock_apply_theme(control, theme_colors):
            theme_applications.append((type(control).__name__, len(theme_colors)))
            apply_theme_to_control(control, theme_colors)
        
        sys.modules['theme'] = type('MockModule', (), {
            'apply_theme_to_control': mock_apply_theme
        })()
        
        from gui_dialogs import ExposureEditDialog
        
        theme_manager = MockThemeManager()
        event = MockOccultationEvent()
        
        # Test day theme
        theme_manager.is_night_mode = False
        dialog = ExposureEditDialog(event, theme_manager)
        
        day_applications = len(theme_applications)
        print(f"✓ Day theme applied {day_applications} times")
        
        dialog.Dispose()
        
        # Test night theme
        theme_applications.clear()
        theme_manager.is_night_mode = True
        dialog = ExposureEditDialog(event, theme_manager)
        
        night_applications = len(theme_applications)
        print(f"✓ Night theme applied {night_applications} times")
        
        if day_applications > 0 and night_applications > 0:
            print("✓ Theme application working for both modes")
        else:
            print("❌ Theme application may not be working")
        
        # Test theme switching
        if theme_manager.toggle_night_mode() == False:  # Switch back to day
            print("✓ Theme switching works")
        
        dialog.Dispose()
        print("✓ Theme application test completed")
        
    except Exception as e:
        print(f"❌ Dialog theme application test failed: {e}")
        import traceback
        traceback.print_exc()

def test_dialog_error_handling():
    """Test dialog error handling scenarios"""
    print("\n=== Testing Dialog Error Handling ===")
    
    try:
        # Mock the theme module
        sys.modules['theme'] = type('MockModule', (), {
            'apply_theme_to_control': apply_theme_to_control
        })()
        
        from gui_dialogs import ExposureEditDialog, EventDetailsDialog
        
        theme_manager = MockThemeManager()
        
        # Test with None event
        try:
            dialog = ExposureEditDialog(None, theme_manager)
            print("❌ Should reject None event")
            dialog.Dispose()
        except Exception:
            print("✓ None event properly rejected")
        
        # Test with malformed event
        class BrokenEvent:
            def __init__(self):
                self.exposure_ms = "not a number"  # Invalid
                self.event_name = None
        
        try:
            dialog = ExposureEditDialog(BrokenEvent(), theme_manager)
            print("⚠ Malformed event handled gracefully")
            dialog.Dispose()
        except Exception:
            print("✓ Malformed event properly rejected")
        
        # Test EventDetailsDialog with minimal event
        class MinimalEvent:
            def __init__(self):
                self.event_name = "Minimal"
                # Missing most attributes
        
        try:
            dialog = EventDetailsDialog(MinimalEvent(), theme_manager)
            print("✓ Minimal event handled in details dialog")
            dialog.Dispose()
        except Exception as e:
            print(f"⚠ Minimal event caused error: {type(e).__name__}")
        
        print("✓ Error handling test completed")
        
    except Exception as e:
        print(f"❌ Dialog error handling test failed: {e}")
        import traceback
        traceback.print_exc()

def visual_test_dialogs():
    """Visual test of dialogs - shows actual working dialogs"""
    print("\n=== Visual Dialog Test ===")
    print("This will show actual dialogs for visual testing")
    
    try:
        # Mock required modules
        sys.modules['theme'] = type('MockModule', (), {
            'apply_theme_to_control': apply_theme_to_control
        })()
        
        class MockTemplateManager:
            @staticmethod
            def find_template_files(folder):
                return ['test_template.txt', 'advanced_template.txt'], folder
            
            @staticmethod
            def get_template_info(template_path):
                return 1234, datetime.now()
            
            @staticmethod
            def load_template(template_path, config=None):
                return f"# Visual test template\nGOTO {{ra}} {{dec}}\nEXPOSE {{exposure}}\n# Path: {template_path}"
        
        sys.modules['templates'] = type('MockModule', (), {
            'TemplateManager': MockTemplateManager
        })()
        
        from gui_dialogs import (ExposureEditDialog, EventDetailsDialog, 
                               ConfigurationDialog, TemplateSelectionDialog)
        
        theme_manager = MockThemeManager()
        config = MockConfigManager()
        event = MockOccultationEvent("Visual Test Event")
        
        class DialogTestForm(Form):
            def __init__(self):
                Form.__init__(self)
                self.theme_manager = theme_manager
                self.config = config
                self.event = event
                self.setup_ui()
            
            def setup_ui(self):
                self.Text = "Dialog Visual Test"
                self.Size = Size(400, 300)
                self.StartPosition = FormStartPosition.CenterScreen
                
                y_pos = 20
                
                # Test buttons for each dialog
                dialogs = [
                    ("Exposure Edit Dialog", self.show_exposure_dialog),
                    ("Event Details Dialog", self.show_details_dialog),
                    ("Configuration Dialog", self.show_config_dialog),
                    ("Template Selection Dialog", self.show_template_dialog),
                ]
                
                for dialog_name, handler in dialogs:
                    btn = Button()
                    btn.Text = dialog_name
                    btn.Location = Point(20, y_pos)
                    btn.Size = Size(180, 30)
                    btn.Click += handler
                    self.Controls.Add(btn)
                    y_pos += 40
                
                # Theme toggle button
                self.btn_theme = Button()
                self.btn_theme.Text = "Toggle Night Mode"
                self.btn_theme.Location = Point(220, 20)
                self.btn_theme.Size = Size(120, 30)
                self.btn_theme.Click += self.toggle_theme
                self.Controls.Add(self.btn_theme)
                
                # Status label
                self.lbl_status = Label()
                self.lbl_status.Text = "Click buttons to test dialogs"
                self.lbl_status.Location = Point(20, 200)
                self.lbl_status.Size = Size(350, 40)
                self.Controls.Add(self.lbl_status)
                
                # Close button
                btn_close = Button()
                btn_close.Text = "Close"
                btn_close.Location = Point(300, 250)
                btn_close.Size = Size(80, 30)
                btn_close.Click += lambda s, e: self.Close()
                self.Controls.Add(btn_close)
            
            def show_exposure_dialog(self, sender, e):
                dialog = ExposureEditDialog(self.event, self.theme_manager)
                result = dialog.ShowDialog()
                self.lbl_status.Text = f"Exposure dialog result: {result}"
                if result == DialogResult.OK:
                    self.lbl_status.Text += f"\nNew exposure: {dialog.get_new_exposure()}ms"
                dialog.Dispose()
            
            def show_details_dialog(self, sender, e):
                dialog = EventDetailsDialog(self.event, self.theme_manager)
                result = dialog.ShowDialog()
                self.lbl_status.Text = f"Details dialog result: {result}"
                dialog.Dispose()
            
            def show_config_dialog(self, sender, e):
                dialog = ConfigurationDialog(self.config, self.theme_manager)
                result = dialog.ShowDialog()
                self.lbl_status.Text = f"Config dialog result: {result}"
                dialog.Dispose()
            
            def show_template_dialog(self, sender, e):
                dialog = TemplateSelectionDialog(self.config, self.theme_manager)
                result = dialog.ShowDialog()
                self.lbl_status.Text = f"Template dialog result: {result}"
                if result == DialogResult.OK:
                    path = dialog.get_selected_template_path()
                    self.lbl_status.Text += f"\nSelected: {os.path.basename(path) if path else 'Default'}"
                dialog.Dispose()
            
            def toggle_theme(self, sender, e):
                is_night = self.theme_manager.toggle_night_mode()
                apply_theme_to_control(self, self.theme_manager.get_current_theme())
                self.lbl_status.Text = f"Theme: {'Night' if is_night else 'Day'} mode"
        
        print("✓ Creating visual test form...")
        form = DialogTestForm()
        
        print("✓ Showing form - click buttons to test each dialog:")
        print("  - Test all dialogs in both day and night modes")
        print("  - Verify dialog functionality and appearance")
        print("  - Close the main form when done testing")
        
        Application.Run(form)
        
        config.cleanup()
        print("✓ Visual dialog test completed")
        
    except Exception as e:
        print(f"❌ Visual dialog test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("GUI Dialogs Module Standalone Test")
    print("=" * 50)
    
    try:
        # Test module import
        print("✓ Testing module imports...")
        
        # Set up basic mocks first
        sys.modules['theme'] = type('MockModule', (), {
            'apply_theme_to_control': apply_theme_to_control
        })()
        
        from gui_dialogs import (ExposureEditDialog, EventDetailsDialog,
                               ConfigurationDialog, TemplateSelectionDialog)
        print("✓ GUI Dialogs module imported successfully")
        
        # Run all tests
        test_exposure_edit_dialog()
        test_event_details_dialog()
        test_configuration_dialog()
        test_template_selection_dialog()
        test_dialog_theme_application()
        test_dialog_error_handling()
        
        print("\n" + "=" * 50)
        print("✓ All automated dialog tests completed!")
        
        # Ask user if they want to run visual test
        print("\nWould you like to run the visual dialog test? (shows actual dialogs)")
        print("Enter 'y' for yes, any other key to skip:")
        
        try:
            user_input = input().strip().lower()
            if user_input == 'y':
                visual_test_dialogs()
        except:
            print("Visual test skipped")
        
        print("\n" + "=" * 50)
        print("✓ All GUI Dialog tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure gui_dialogs.py is in the same directory")
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