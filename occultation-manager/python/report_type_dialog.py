"""
Dialog for selecting which regional report format to generate
"""

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Windows.Forms import (Form, Button, RadioButton, Label, DialogResult,
                                  FormBorderStyle, FormStartPosition, MessageBox, 
                                  MessageBoxButtons, MessageBoxIcon, GroupBox)
from System.Drawing import Point, Size, Font, FontStyle, Color


def apply_theme_to_control(control, theme_manager):
    """Apply theme colors to a control and its children"""
    if not theme_manager:
        return
        
    theme = theme_manager.get_current_theme()
    control.BackColor = theme['background']
    control.ForeColor = theme['text_foreground']
    
    if hasattr(control, 'Controls'):
        for child in control.Controls:
            apply_theme_to_control(child, theme_manager)


class ReportTypeSelectionDialog(Form):
    """Dialog for selecting which report format to use"""
    
    def __init__(self, theme_manager=None, event=None):
        self.theme_manager = theme_manager
        self.event = event
        self.selected_report_type = None
        
        # Setup form
        self.Text = "Select Report Format"
        self.Size = Size(500, 320)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterParent
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        self.setup_ui()
        
        if theme_manager:
            apply_theme_to_control(self, theme_manager)
    
    def setup_ui(self):
        """Setup the UI controls"""
        sf = 1.0  # Scale factor
        
        # Event info label (if provided)
        y_pos = 10
        if self.event:
            lbl_event = Label()
            event_name = self.event.get_asteroid_display_name() if hasattr(self.event, 'get_asteroid_display_name') else self.event.get('asteroid_name', 'Unknown')
            lbl_event.Text = "Event: {}".format(event_name)
            lbl_event.Location = Point(int(20 * sf), int(y_pos * sf))
            lbl_event.Size = Size(int(450 * sf), int(20 * sf))
            lbl_event.Font = Font(lbl_event.Font, FontStyle.Bold)
            self.Controls.Add(lbl_event)
            y_pos += 30
        
        # Info label
        lbl_info = Label()
        lbl_info.Text = "Select the report format to generate:"
        lbl_info.Location = Point(int(20 * sf), int(y_pos * sf))
        lbl_info.Size = Size(int(450 * sf), int(20 * sf))
        self.Controls.Add(lbl_info)
        y_pos += 30
        
        # Radio buttons group
        group = GroupBox()
        group.Text = "Report Format"
        group.Location = Point(int(20 * sf), int(y_pos * sf))
        group.Size = Size(int(450 * sf), int(140 * sf))
        self.Controls.Add(group)
        
        # North America radio button
        self.radio_na = RadioButton()
        self.radio_na.Text = "IOTA North America (V5.6.12r)"
        self.radio_na.Location = Point(int(15 * sf), int(25 * sf))
        self.radio_na.Size = Size(int(420 * sf), int(20 * sf))
        self.radio_na.Checked = True  # Default selection
        group.Controls.Add(self.radio_na)
        
        # Trans-Tasman radio button
        self.radio_tt = RadioButton()
        self.radio_tt.Text = "Trans-Tasman / RASNZ (V4.1.2.G)"
        self.radio_tt.Location = Point(int(15 * sf), int(50 * sf))
        self.radio_tt.Size = Size(int(420 * sf), int(20 * sf))
        group.Controls.Add(self.radio_tt)
        
        # SODIS Europe radio button (not yet implemented)
        self.radio_sodis = RadioButton()
        self.radio_sodis.Text = "SODIS Europe (Not yet implemented)"
        self.radio_sodis.Location = Point(int(15 * sf), int(75 * sf))
        self.radio_sodis.Size = Size(int(420 * sf), int(20 * sf))
        self.radio_sodis.Enabled = False
        self.radio_sodis.ForeColor = Color.Gray
        group.Controls.Add(self.radio_sodis)
        
        # IOTA-EA radio button (not yet implemented)
        self.radio_iota_ea = RadioButton()
        self.radio_iota_ea.Text = "IOTA East Asia (Not yet implemented)"
        self.radio_iota_ea.Location = Point(int(15 * sf), int(100 * sf))
        self.radio_iota_ea.Size = Size(int(420 * sf), int(20 * sf))
        self.radio_iota_ea.Enabled = False
        self.radio_iota_ea.ForeColor = Color.Gray
        group.Controls.Add(self.radio_iota_ea)
        
        y_pos += 150
        
        # Buttons
        btn_ok = Button()
        btn_ok.Text = "Continue"
        btn_ok.Location = Point(int(200 * sf), int(y_pos * sf))
        btn_ok.Size = Size(int(120 * sf), int(30 * sf))
        btn_ok.Click += self.ok_click
        self.Controls.Add(btn_ok)
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(int(330 * sf), int(y_pos * sf))
        btn_cancel.Size = Size(int(100 * sf), int(30 * sf))
        btn_cancel.Click += self.cancel_click
        self.Controls.Add(btn_cancel)
    
    def ok_click(self, sender, e):
        """Handle OK button click"""
        # Determine which report type was selected
        if self.radio_na.Checked:
            self.selected_report_type = 'north_america'
        elif self.radio_tt.Checked:
            self.selected_report_type = 'trans_tasman'
        elif self.radio_sodis.Checked:
            self.selected_report_type = 'sodis'
        elif self.radio_iota_ea.Checked:
            self.selected_report_type = 'iota_ea'
        else:
            MessageBox.Show("Please select a report format.", 
                          "No Selection", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        self.DialogResult = DialogResult.OK
        self.Close()
    
    def cancel_click(self, sender, e):
        """Handle Cancel button click"""
        self.DialogResult = DialogResult.Cancel
        self.Close()
    
    def get_selected_report_type(self):
        """Get the selected report type"""
        return self.selected_report_type
