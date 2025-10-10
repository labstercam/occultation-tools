import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Color, SystemColors
from System.Windows.Forms import *

class ThemeManager:
    """Manages day/night mode themes with SharpCap-compatible colors"""
    
    def __init__(self):
        self.is_night_mode = False
        self.setup_themes()
    
    def setup_themes(self):
        """Define SharpCap-compatible color schemes"""
        # Day mode (default Windows colors)
        self.day_theme = {
            'background': SystemColors.Control,
            'panel_background': SystemColors.Window,
            'text_foreground': SystemColors.ControlText,
            'grid_background': SystemColors.Window,
            'grid_foreground': SystemColors.WindowText,
            'grid_selection': SystemColors.Highlight,
            'button_background': SystemColors.ButtonFace,
            'button_text': SystemColors.ControlText,
            'status_background': SystemColors.ControlDark,
            'status_text': SystemColors.ControlText,
            'groupbox_background': SystemColors.Control,
            'textbox_background': SystemColors.Window
        }
        
        # Night mode (SharpCap orange/black theme for night vision preservation)
        # Based on SharpCap 3.2+ night mode color scheme
        # Reference: https://www.sharpcap.co.uk/sharpcap/whats-new-in-sharpcap-3-2
        # "The use of an orange colour for text and controls instead of the more 
        # traditional red makes text legibility much better without adding 
        # significantly to the screen brightness."
        self.night_theme = {
            'background': Color.FromArgb(25, 20, 15),          # Very dark (almost black)
            'panel_background': Color.FromArgb(40, 30, 20),    # Dark brown-black
            'text_foreground': Color.FromArgb(255, 180, 80),   # Orange text (SharpCap style)
            'grid_background': Color.FromArgb(30, 25, 18),     # Dark background
            'grid_foreground': Color.FromArgb(255, 170, 70),   # Orange text
            'grid_selection': Color.FromArgb(150, 90, 30),     # Dark orange selection
            'button_background': Color.FromArgb(60, 45, 25),   # Medium dark button
            'button_text': Color.FromArgb(255, 190, 90),       # Bright orange text
            'status_background': Color.FromArgb(20, 15, 10),   # Nearly black
            'status_text': Color.FromArgb(255, 160, 60),       # Orange
            'groupbox_background': Color.FromArgb(35, 28, 20), # Dark for groupboxes
            'textbox_background': Color.FromArgb(50, 38, 25)   # Input fields dark
        }
    
    def get_current_theme(self):
        """Get current theme colors"""
        return self.night_theme if self.is_night_mode else self.day_theme
    
    def toggle_night_mode(self):
        """Toggle between day and night mode"""
        self.is_night_mode = not self.is_night_mode
        return self.is_night_mode
    
    def set_night_mode(self, enabled):
        """Set night mode on/off"""
        self.is_night_mode = enabled

# Global functions to use with GUI element classes
def apply_theme_to_control(control, theme_colors):
    """Recursively apply theme to a control and all its children"""
    try:
        # Apply colors based on control type
        if hasattr(control, 'BackColor'):
            if isinstance(control, (Form, Panel, TabControl, TabPage)):
                control.BackColor = theme_colors['background']
            elif isinstance(control, GroupBox):
                control.BackColor = theme_colors['groupbox_background']
            elif isinstance(control, (TextBox, ComboBox, ListBox)):
                control.BackColor = theme_colors['textbox_background']
            elif isinstance(control, Button):
                control.BackColor = theme_colors['button_background']
                control.ForeColor = theme_colors['button_text']
                control.FlatStyle = FlatStyle.Flat  # Better appearance in night mode
            elif isinstance(control, DataGridView):
                apply_datagrid_theme(control, theme_colors)
        
        if hasattr(control, 'ForeColor'):
            if not isinstance(control, (Button, DataGridView)):  # Buttons handled above
                control.ForeColor = theme_colors['text_foreground']
        
        # Recursively apply to child controls
        if hasattr(control, 'Controls'):
            for child in control.Controls:
                apply_theme_to_control(child, theme_colors)
                
    except Exception as e:
        print(f"Error applying theme to {type(control)}: {e}")

def apply_datagrid_theme(grid, theme_colors):
    """Apply theme specifically to DataGridView"""
    try:
        grid.BackgroundColor = theme_colors['grid_background']
        grid.ForeColor = theme_colors['grid_foreground']
        grid.DefaultCellStyle.BackColor = theme_colors['grid_background']
        grid.DefaultCellStyle.ForeColor = theme_colors['grid_foreground']
        grid.DefaultCellStyle.SelectionBackColor = theme_colors['grid_selection']
        grid.DefaultCellStyle.SelectionForeColor = theme_colors['text_foreground']
        grid.ColumnHeadersDefaultCellStyle.BackColor = theme_colors['button_background']
        grid.ColumnHeadersDefaultCellStyle.ForeColor = theme_colors['button_text']
        grid.EnableHeadersVisualStyles = False  # Required for custom header colors
        grid.GridColor = theme_colors['text_foreground']
    except Exception as e:
        print(f"Error applying DataGrid theme: {e}")
