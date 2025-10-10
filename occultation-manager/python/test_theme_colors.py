# test_theme_colors.py - Visual test of SharpCap-compatible night mode colors

import sys
import os

# Add the module directory to Python path if needed
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Color, Font, FontStyle, Point, Size, ContentAlignment
from System.Windows.Forms import *
from theme import ThemeManager, apply_theme_to_control

class ColorTestForm(Form):
    """Form to display and test SharpCap night mode colors"""
    
    def __init__(self):
        self.theme_manager = ThemeManager()
        self.setup_form()
        
    def setup_form(self):
        """Setup the test form"""
        self.Text = "SharpCap Night Mode Color Test"
        self.Width = 900
        self.Height = 700
        self.StartPosition = FormStartPosition.CenterScreen
        
        # Main panel
        main_panel = Panel()
        main_panel.Dock = DockStyle.Fill
        main_panel.AutoScroll = True
        self.Controls.Add(main_panel)
        
        y_pos = 20
        
        # Title
        title = Label()
        title.Text = "SharpCap Orange Night Mode Color Palette"
        title.Font = Font("Arial", 16, FontStyle.Bold)
        title.AutoSize = True
        title.Location = Point(20, y_pos)
        main_panel.Controls.Add(title)
        y_pos += 50
        
        # Description
        desc = Label()
        desc.Text = "Based on SharpCap 3.2+ night mode (orange text on black background)"
        desc.AutoSize = True
        desc.Location = Point(20, y_pos)
        main_panel.Controls.Add(desc)
        y_pos += 40
        
        # Background colors section
        self.add_section_header(main_panel, "Background Colors (Dark/Black)", y_pos)
        y_pos += 30
        
        bg_colors = [
            ("Background (Very Dark)", Color.FromArgb(25, 20, 15), "#19140F"),
            ("Panel Background", Color.FromArgb(40, 30, 20), "#281E14"),
            ("Grid Background", Color.FromArgb(30, 25, 18), "#1E1912"),
            ("Button Background", Color.FromArgb(60, 45, 25), "#3C2D19"),
            ("TextBox Background", Color.FromArgb(50, 38, 25), "#322619"),
            ("GroupBox Background", Color.FromArgb(35, 28, 20), "#231C14"),
            ("Status Background", Color.FromArgb(20, 15, 10), "#140F0A"),
        ]
        
        for name, color, hex_val in bg_colors:
            y_pos = self.add_color_sample(main_panel, name, color, hex_val, y_pos)
            y_pos += 50
        
        y_pos += 20
        
        # Foreground colors section
        self.add_section_header(main_panel, "Foreground Colors (Orange - High Visibility)", y_pos)
        y_pos += 30
        
        fg_colors = [
            ("Text Foreground (Primary)", Color.FromArgb(255, 180, 80), "#FFB450"),
            ("Grid Foreground", Color.FromArgb(255, 170, 70), "#FFAA46"),
            ("Button Text", Color.FromArgb(255, 190, 90), "#FFBE5A"),
            ("Status Text", Color.FromArgb(255, 160, 60), "#FFA03C"),
            ("Grid Selection", Color.FromArgb(150, 90, 30), "#965A1E"),
        ]
        
        for name, color, hex_val in fg_colors:
            y_pos = self.add_color_sample(main_panel, name, color, hex_val, y_pos, show_text=True)
            y_pos += 50
        
        y_pos += 20
        
        # Theme toggle section
        self.add_section_header(main_panel, "Theme Toggle Test", y_pos)
        y_pos += 30
        
        toggle_panel = self.create_toggle_test_panel()
        toggle_panel.Location = Point(20, y_pos)
        main_panel.Controls.Add(toggle_panel)
        y_pos += toggle_panel.Height + 20
        
        # Live demo section
        y_pos += 20
        self.add_section_header(main_panel, "Live Component Demo", y_pos)
        y_pos += 30
        
        demo_panel = self.create_demo_panel()
        demo_panel.Location = Point(20, y_pos)
        main_panel.Controls.Add(demo_panel)
        
    def add_section_header(self, parent, text, y_pos):
        """Add a section header"""
        header = Label()
        header.Text = text
        header.Font = Font("Arial", 12, FontStyle.Bold)
        header.AutoSize = True
        header.Location = Point(20, y_pos)
        parent.Controls.Add(header)
        
    def add_color_sample(self, parent, name, color, hex_val, y_pos, show_text=False):
        """Add a color sample with name and hex value"""
        # Color box
        box = Panel()
        box.BackColor = color
        box.Size = Size(200, 30)
        box.Location = Point(20, y_pos)
        box.BorderStyle = BorderStyle.FixedSingle
        parent.Controls.Add(box)
        
        # If showing text sample
        if show_text:
            text_label = Label()
            text_label.Text = "Sample Text"
            text_label.ForeColor = color
            text_label.BackColor = Color.FromArgb(25, 20, 15)  # Dark background
            text_label.AutoSize = False
            text_label.Size = Size(150, 30)
            text_label.TextAlign = ContentAlignment.MiddleCenter
            text_label.Location = Point(230, y_pos)
            text_label.BorderStyle = BorderStyle.FixedSingle
            parent.Controls.Add(text_label)
        
        # Name label
        name_label = Label()
        name_label.Text = name
        name_label.AutoSize = True
        name_label.Location = Point(400, y_pos + 5)
        parent.Controls.Add(name_label)
        
        # Hex value label
        hex_label = Label()
        hex_label.Text = "{0} - RGB({1}, {2}, {3})".format(hex_val, color.R, color.G, color.B)
        hex_label.AutoSize = True
        hex_label.ForeColor = Color.Gray
        hex_label.Location = Point(620, y_pos + 5)
        parent.Controls.Add(hex_label)
        
        return y_pos
    
    def create_toggle_test_panel(self):
        """Create a panel to test theme toggling"""
        panel = Panel()
        panel.Size = Size(850, 150)
        panel.BorderStyle = BorderStyle.FixedSingle
        
        # Add sample controls
        label = Label()
        label.Text = "Sample Label"
        label.Location = Point(10, 10)
        label.AutoSize = True
        panel.Controls.Add(label)
        
        textbox = TextBox()
        textbox.Text = "Sample TextBox"
        textbox.Location = Point(10, 40)
        textbox.Width = 200
        panel.Controls.Add(textbox)
        
        button = Button()
        button.Text = "Sample Button"
        button.Location = Point(10, 70)
        button.Width = 150
        panel.Controls.Add(button)
        
        # Toggle button
        toggle_btn = Button()
        toggle_btn.Text = "Toggle Night Mode (F12)"
        toggle_btn.Location = Point(10, 110)
        toggle_btn.Width = 200
        toggle_btn.Click += self.on_toggle_night_mode
        panel.Controls.Add(toggle_btn)
        
        # Info label
        self.mode_label = Label()
        self.mode_label.Text = "Current Mode: Day"
        self.mode_label.Location = Point(220, 115)
        self.mode_label.AutoSize = True
        panel.Controls.Add(self.mode_label)
        
        self.toggle_panel = panel
        return panel
    
    def create_demo_panel(self):
        """Create a panel with various controls to demonstrate theme"""
        panel = Panel()
        panel.Size = Size(850, 250)
        panel.BorderStyle = BorderStyle.FixedSingle
        
        # GroupBox
        group = GroupBox()
        group.Text = "Sample GroupBox"
        group.Location = Point(10, 10)
        group.Size = Size(250, 150)
        panel.Controls.Add(group)
        
        # Controls inside groupbox
        cb = CheckBox()
        cb.Text = "Check Box Option"
        cb.Location = Point(10, 25)
        cb.AutoSize = True
        group.Controls.Add(cb)
        
        rb1 = RadioButton()
        rb1.Text = "Radio Option 1"
        rb1.Location = Point(10, 50)
        rb1.AutoSize = True
        rb1.Checked = True
        group.Controls.Add(rb1)
        
        rb2 = RadioButton()
        rb2.Text = "Radio Option 2"
        rb2.Location = Point(10, 75)
        rb2.AutoSize = True
        group.Controls.Add(rb2)
        
        combo = ComboBox()
        combo.Items.AddRange(["Option 1", "Option 2", "Option 3"])
        combo.SelectedIndex = 0
        combo.Location = Point(10, 105)
        combo.Width = 200
        group.Controls.Add(combo)
        
        # ListBox
        listbox = ListBox()
        listbox.Items.AddRange(["Item 1", "Item 2", "Item 3", "Item 4", "Item 5"])
        listbox.Location = Point(280, 10)
        listbox.Size = Size(200, 150)
        panel.Controls.Add(listbox)
        
        # DataGridView
        grid = DataGridView()
        grid.Location = Point(500, 10)
        grid.Size = Size(330, 150)
        grid.AllowUserToAddRows = False
        grid.RowHeadersVisible = False
        
        # Add columns
        grid.Columns.Add("Name", "Name")
        grid.Columns.Add("Value", "Value")
        grid.Columns.Add("Status", "Status")
        
        # Add sample data
        grid.Rows.Add("Sample 1", "Value A", "Active")
        grid.Rows.Add("Sample 2", "Value B", "Inactive")
        grid.Rows.Add("Sample 3", "Value C", "Active")
        
        panel.Controls.Add(grid)
        
        # Status label
        status = Label()
        status.Text = "Status: All systems operational"
        status.Location = Point(10, 170)
        status.AutoSize = True
        panel.Controls.Add(status)
        
        # Action buttons
        btn1 = Button()
        btn1.Text = "Action 1"
        btn1.Location = Point(10, 200)
        btn1.Width = 100
        panel.Controls.Add(btn1)
        
        btn2 = Button()
        btn2.Text = "Action 2"
        btn2.Location = Point(120, 200)
        btn2.Width = 100
        panel.Controls.Add(btn2)
        
        btn3 = Button()
        btn3.Text = "Cancel"
        btn3.Location = Point(230, 200)
        btn3.Width = 100
        panel.Controls.Add(btn3)
        
        self.demo_panel = panel
        return panel
    
    def on_toggle_night_mode(self, sender, e):
        """Toggle night mode and apply to form"""
        is_night = self.theme_manager.toggle_night_mode()
        theme_colors = self.theme_manager.get_current_theme()
        
        # Apply theme to toggle test panel
        apply_theme_to_control(self.toggle_panel, theme_colors)
        
        # Apply theme to demo panel
        apply_theme_to_control(self.demo_panel, theme_colors)
        
        # Update mode label
        self.mode_label.Text = "Current Mode: {0}".format('Night (Orange)' if is_night else 'Day')
        
        # Force refresh
        self.Refresh()

def main():
    """Main test function"""
    print("SharpCap Night Mode Color Test")
    print("=" * 50)
    print("\nThis test displays SharpCap-compatible orange night mode colors")
    print("Press F12 or click 'Toggle Night Mode' to switch themes")
    print("\nColor Scheme:")
    print("- Background: Black/Dark Brown (RGB: 20-60, 15-45, 10-25)")
    print("- Text: Orange (RGB: 255, 160-190, 60-90)")
    print("- No blue light to preserve night vision")
    print("\n" + "=" * 50 + "\n")
    
    Application.EnableVisualStyles()
    Application.SetCompatibleTextRenderingDefault(False)
    
    form = ColorTestForm()
    Application.Run(form)

if __name__ == "__main__":
    main()
