# test_theme_visual.py - Visual theme test (shows actual form)

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Windows.Forms import *
from System.Drawing import *

def visual_test():
    """Visual theme test - shows actual themed form"""
    print("Visual Theme Test")
    print("=" * 20)
    print("This will show a form to visually test themes")
    
    try:
        from theme import ThemeManager, apply_theme_to_control
        
        class ThemeTestForm(Form):
            def __init__(self):
                Form.__init__(self)
                self.theme_manager = ThemeManager()
                self.setup_ui()
                self.apply_current_theme()
            
            def setup_ui(self):
                self.Text = "Theme Visual Test"
                self.Size = Size(500, 400)
                self.StartPosition = FormStartPosition.CenterScreen
                
                # Toggle button
                self.btn_toggle = Button()
                self.btn_toggle.Text = "Toggle Night Mode"
                self.btn_toggle.Location = Point(10, 10)
                self.btn_toggle.Size = Size(120, 30)
                self.btn_toggle.Click += self.toggle_theme
                self.Controls.Add(self.btn_toggle)
                
                # Status label
                self.lbl_status = Label()
                self.lbl_status.Text = "Day Mode Active"
                self.lbl_status.Location = Point(140, 15)
                self.lbl_status.Size = Size(200, 20)
                self.Controls.Add(self.lbl_status)
                
                # GroupBox with controls
                group = GroupBox()
                group.Text = "Sample Controls"
                group.Location = Point(10, 50)
                group.Size = Size(460, 150)
                self.Controls.Add(group)
                
                # Button in group
                btn_sample = Button()
                btn_sample.Text = "Sample Button"
                btn_sample.Location = Point(10, 30)
                btn_sample.Size = Size(100, 25)
                group.Controls.Add(btn_sample)
                
                # TextBox
                txt_sample = TextBox()
                txt_sample.Text = "Sample text"
                txt_sample.Location = Point(120, 30)
                txt_sample.Size = Size(100, 25)
                group.Controls.Add(txt_sample)
                
                # Label
                lbl_sample = Label()
                lbl_sample.Text = "Sample Label"
                lbl_sample.Location = Point(10, 65)
                lbl_sample.Size = Size(100, 20)
                group.Controls.Add(lbl_sample)
                
                # DataGridView
                grid = DataGridView()
                grid.Location = Point(10, 210)
                grid.Size = Size(460, 150)
                grid.Columns.Add("Col1", "Column 1")
                grid.Columns.Add("Col2", "Column 2")
                grid.Rows.Add("Data 1", "Value 1")
                grid.Rows.Add("Data 2", "Value 2")
                self.Controls.Add(grid)
                self.grid = grid
            
            def toggle_theme(self, sender, e):
                is_night = self.theme_manager.toggle_night_mode()
                self.apply_current_theme()
                
                if is_night:
                    self.lbl_status.Text = "Night Mode Active"
                else:
                    self.lbl_status.Text = "Day Mode Active"
            
            def apply_current_theme(self):
                theme = self.theme_manager.get_current_theme()
                apply_theme_to_control(self, theme)
                
                # Apply to grid specifically
                from theme import apply_datagrid_theme
                apply_datagrid_theme(self.grid, theme)
        
        print("✓ Creating visual test form...")
        form = ThemeTestForm()
        
        print("✓ Showing form - click 'Toggle Night Mode' to test themes")
        print("  Close the form when done testing")
        
        Application.Run(form)
        print("✓ Visual test completed")
        
    except Exception as e:
        print(f"❌ Visual test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    visual_test()

"""
Theme Module Standalone Test
========================================
✓ Theme module imported successfully

=== Testing ThemeManager Creation ===
✓ ThemeManager created successfully
✓ Initial night mode: False
✓ Starts in day mode (correct)
✓ Day and night themes initialized

=== Testing Theme Definitions ===
✓ Day theme colors:
  - background: Color [Control]
  - panel_background: Color [Window]
  - text_foreground: Color [ControlText]
  - grid_background: Color [Window]
  - grid_foreground: Color [WindowText]
  - grid_selection: Color [Highlight]
  - button_background: Color [ButtonFace]
  - button_text: Color [ButtonText]
  - status_background: Color [ControlDark]
  - status_text: Color [ControlText]
  - groupbox_background: Color [Control]
  - textbox_background: Color [Window]
✓ Day theme has 12 color definitions
✓ Night theme colors:
  - background: Color [A=255, R=40, G=0, B=0] (✓ Red-tinted)
  - panel_background: Color [A=255, R=60, G=0, B=0] (✓ Red-tinted)
  - text_foreground: Color [A=255, R=255, G=200, B=200] (✓ Red-tinted)
✓ Night theme has 12 color definitions
✓ Day and night themes have matching color keys

=== Testing Theme Switching ===
✓ Initial state: Night mode = False
✓ After toggle: Night mode = True
✓ Toggle changed the state
✓ Theme changed after toggle
✓ Background color changed
✓ After second toggle: Night mode = False
✓ Second toggle returned to initial state
✓ set_night_mode(True) works
✓ set_night_mode(False) works

=== Testing Color Properties ===
✓ Testing Day theme colors:
  - background: Color [Control] (System color)
  - panel_background: Color [Window] (System color)
  - text_foreground: Color [ControlText] (System color)
  ... (additional colors)
✓ Day theme validation completed
✓ Testing Night theme colors:
  - background: RGB(40, 0, 0)
  - panel_backgroun
"""    