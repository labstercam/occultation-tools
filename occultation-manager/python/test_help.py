# test_help.py - Standalone test for help.py module

import sys
import os

# Add the module directory to Python path if needed
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

# Import required GUI libraries
import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Windows.Forms import *
from System.Drawing import *

# Mock the theme manager for testing
class MockThemeManager:
    """Mock theme manager for testing help system"""
    
    def __init__(self):
        self.is_night_mode = False
    
    def get_current_theme(self):
        """Return simple theme for testing"""
        if self.is_night_mode:
            return {
                'background': Color.FromArgb(40, 0, 0),
                'text_foreground': Color.FromArgb(255, 200, 200),
                'button_background': Color.FromArgb(80, 20, 20),
                'button_text': Color.FromArgb(255, 200, 200)
            }
        else:
            return {
                'background': SystemColors.Control,
                'text_foreground': SystemColors.ControlText,
                'button_background': SystemColors.ButtonFace,
                'button_text': SystemColors.ControlText
            }
    
    def toggle_night_mode(self):
        """Toggle night mode for testing"""
        self.is_night_mode = not self.is_night_mode
        return self.is_night_mode

# Simple theme application function for testing
def apply_theme_to_control(control, theme_colors):
    """Simplified theme application for testing"""
    try:
        if hasattr(control, 'BackColor'):
            control.BackColor = theme_colors.get('background', SystemColors.Control)
        if hasattr(control, 'ForeColor'):
            control.ForeColor = theme_colors.get('text_foreground', SystemColors.ControlText)
        
        # Apply to child controls
        if hasattr(control, 'Controls'):
            for child in control.Controls:
                apply_theme_to_control(child, theme_colors)
    except Exception as e:
        print(f"Theme application error: {e}")

# Import the help system (will need the above mocks)
try:
    from help import HelpDialog, HelpManager
    print("✓ Help module imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

class HelpTestForm(Form):
    """Test form for help system"""
    
    def __init__(self):
        Form.__init__(self)
        self.theme_manager = MockThemeManager()
        self.help_manager = HelpManager(self.theme_manager)
        self.setup_ui()
    
    def setup_ui(self):
        """Setup test form UI"""
        self.Text = "Help System Test"
        self.Size = Size(400, 300)
        self.StartPosition = FormStartPosition.CenterScreen
        
        # Test buttons
        btn_show_help = Button()
        btn_show_help.Text = "Show Help Dialog"
        btn_show_help.Size = Size(150, 30)
        btn_show_help.Location = Point(50, 50)
        btn_show_help.Click += self.show_help_click
        self.Controls.Add(btn_show_help)
        
        btn_show_about = Button()
        btn_show_about.Text = "Show About Dialog"
        btn_show_about.Size = Size(150, 30)
        btn_show_about.Location = Point(50, 100)
        btn_show_about.Click += self.show_about_click
        self.Controls.Add(btn_show_about)
        
        btn_toggle_theme = Button()
        btn_toggle_theme.Text = "Toggle Night Mode"
        btn_toggle_theme.Size = Size(150, 30)
        btn_toggle_theme.Location = Point(50, 150)
        btn_toggle_theme.Click += self.toggle_theme_click
        self.Controls.Add(btn_toggle_theme)
        
        btn_test_direct = Button()
        btn_test_direct.Text = "Test Help Direct"
        btn_test_direct.Size = Size(150, 30)
        btn_test_direct.Location = Point(50, 200)
        btn_test_direct.Click += self.test_direct_click
        self.Controls.Add(btn_test_direct)
        
        # Status label
        self.lbl_status = Label()
        self.lbl_status.Text = "Ready to test help system"
        self.lbl_status.Location = Point(50, 250)
        self.lbl_status.Size = Size(300, 20)
        self.Controls.Add(self.lbl_status)
    
    def show_help_click(self, sender, e):
        """Test help dialog via HelpManager"""
        try:
            self.lbl_status.Text = "Opening help dialog..."
            self.help_manager.show_help(self)
            self.lbl_status.Text = "Help dialog closed"
        except Exception as ex:
            self.lbl_status.Text = f"Help error: {ex}"
            print(f"Help dialog error: {ex}")
    
    def show_about_click(self, sender, e):
        """Test about dialog"""
        try:
            self.lbl_status.Text = "Opening about dialog..."
            self.help_manager.show_about()
            self.lbl_status.Text = "About dialog closed"
        except Exception as ex:
            self.lbl_status.Text = f"About error: {ex}"
            print(f"About dialog error: {ex}")
    
    def toggle_theme_click(self, sender, e):
        """Test theme toggling"""
        try:
            is_night = self.theme_manager.toggle_night_mode()
            theme_colors = self.theme_manager.get_current_theme()
            apply_theme_to_control(self, theme_colors)
            self.lbl_status.Text = f"Theme: {'Night' if is_night else 'Day'}"
            self.Refresh()
        except Exception as ex:
            self.lbl_status.Text = f"Theme error: {ex}"
            print(f"Theme toggle error: {ex}")
    
    def test_direct_click(self, sender, e):
        """Test help dialog directly"""
        try:
            self.lbl_status.Text = "Opening help dialog directly..."
            help_dialog = HelpDialog(self.theme_manager)
            help_dialog.ShowDialog()
            self.lbl_status.Text = "Direct help dialog closed"
        except Exception as ex:
            self.lbl_status.Text = f"Direct help error: {ex}"
            print(f"Direct help dialog error: {ex}")

def test_help_content():
    """Test help content generation without GUI"""
    print("\n=== Testing Help Content Generation ===")
    
    try:
        # Create theme manager
        theme_manager = MockThemeManager()
        
        # Create help dialog
        help_dialog = HelpDialog(theme_manager)
        
        # Test content methods
        test_topics = [
            'overview',
            'getting_started', 
            'configuration',
            'main_interface',
            'troubleshooting'
        ]
        
        for topic in test_topics:
            try:
                print(topic)
                content = help_dialog.get_help_content(topic)
                print(f"✓ {topic}: {len(content)} characters")
                
                # Check for author mention
                if 'Michael Camilleri' in content:
                    print(f"  ✓ Author attribution found in {topic}")
                    
            except Exception as e:
                print(f"❌ {topic}: Error - {e}")
        
        print("✓ Content generation test completed")
        
    except Exception as e:
        print(f"❌ Content generation test failed: {e}")

def run_gui_test():
    """Run the GUI test"""
    print("\n=== Starting GUI Test ===")
    
    try:
        Application.EnableVisualStyles()
        test_form = HelpTestForm()
        print("✓ Test form created")
        
        print("✓ GUI test ready - showing form")
        print("Use the buttons to test different aspects of the help system")
        
        Application.Run(test_form)
        print("✓ GUI test completed")
        
    except Exception as e:
        print(f"❌ GUI test failed: {e}")

def main():
    """Main test function"""
    print("Help System Standalone Test")
    print("=" * 40)
    
    # Test 1: Content generation
    test_help_content()
    
    # Test 2: GUI functionality
    print("\nStarting GUI test...")
    print("Close the test window when done testing.")
    run_gui_test()
    
    print("\nAll tests completed!")

if __name__ == "__main__":
    main()