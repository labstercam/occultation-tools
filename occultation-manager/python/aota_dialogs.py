"""
AOTA Event Selection Dialog

Provides UI for selecting observation type and AOTA file, and choosing which event 
to use when multiple valid events are present.
"""

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Windows.Forms import (
    Form, Label, Button, ListBox, MessageBox, MessageBoxButtons, MessageBoxIcon,
    DialogResult, FormStartPosition, FormBorderStyle, SelectionMode, Panel,
    DockStyle, OpenFileDialog, GroupBox, RadioButton
)
from System.Drawing import Point, Size, Font, FontStyle, Color
from gui_dialogs import _detect_scale_factor, _autosize_button
from theme import apply_theme_to_control


class ObservationTypeDialog(Form):
    """Dialog for selecting observation type (Positive, Negative, Unsure)"""
    
    def __init__(self, theme_manager, event_name=None):
        Form.__init__(self)
        self.theme_manager = theme_manager
        self.event_name = event_name
        self.selected_type = None
        self._sf = _detect_scale_factor()
        
        self.setup_ui()
        
        # Apply theme
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup observation type selection UI"""
        sf = self._sf
        
        self.Text = "Observation Type"
        self.Size = Size(int(550 * sf), int(400 * sf))
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        # Main panel
        panel = Panel()
        panel.Dock = DockStyle.Fill
        from System.Windows.Forms import Padding as PaddingClass
        panel.Padding = PaddingClass(int(20 * sf), int(20 * sf), int(20 * sf), int(20 * sf))
        self.Controls.Add(panel)
        
        y_pos = 10
        
        # Event info if provided
        if self.event_name:
            lbl_event = Label()
            lbl_event.Text = f"Generating report for: {self.event_name}"
            lbl_event.Location = Point(int(10 * sf), y_pos)
            lbl_event.Size = Size(int(490 * sf), int(25 * sf))
            lbl_event.Font = Font(lbl_event.Font.FontFamily, 10, FontStyle.Bold)
            panel.Controls.Add(lbl_event)
            y_pos += int(35 * sf)
        
        # Title
        lbl_title = Label()
        lbl_title.Text = "What was the result of your observation?"
        lbl_title.Location = Point(int(10 * sf), y_pos)
        lbl_title.Size = Size(int(490 * sf), int(25 * sf))
        lbl_title.Font = Font(lbl_title.Font.FontFamily, 10, FontStyle.Bold)
        panel.Controls.Add(lbl_title)
        y_pos += int(35 * sf)
        
        # Options group
        grp_type = GroupBox()
        grp_type.Text = "Observation Type"
        grp_type.Location = Point(int(10 * sf), y_pos)
        grp_type.Size = Size(int(490 * sf), int(180 * sf))
        panel.Controls.Add(grp_type)
        
        # Radio buttons
        self.rb_positive = RadioButton()
        self.rb_positive.Text = "Positive - I observed a disappearance and reappearance"
        self.rb_positive.Location = Point(int(15 * sf), int(30 * sf))
        self.rb_positive.Size = Size(int(460 * sf), int(25 * sf))
        self.rb_positive.Checked = True  # Default selection
        grp_type.Controls.Add(self.rb_positive)
        
        lbl_positive_desc = Label()
        lbl_positive_desc.Text = "You will be prompted to import AOTA timing data (D and R times)"
        lbl_positive_desc.Location = Point(int(35 * sf), int(55 * sf))
        lbl_positive_desc.Size = Size(int(440 * sf), int(20 * sf))
        lbl_positive_desc.ForeColor = Color.Gray
        grp_type.Controls.Add(lbl_positive_desc)
        
        self.rb_negative = RadioButton()
        self.rb_negative.Text = "Negative - No occultation occurred (miss or cloud)"
        self.rb_negative.Location = Point(int(15 * sf), int(85 * sf))
        self.rb_negative.Size = Size(int(460 * sf), int(25 * sf))
        grp_type.Controls.Add(self.rb_negative)
        
        lbl_negative_desc = Label()
        lbl_negative_desc.Text = "Report will be generated without D/R timing data"
        lbl_negative_desc.Location = Point(int(35 * sf), int(110 * sf))
        lbl_negative_desc.Size = Size(int(440 * sf), int(20 * sf))
        lbl_negative_desc.ForeColor = Color.Gray
        grp_type.Controls.Add(lbl_negative_desc)
        
        self.rb_unsure = RadioButton()
        self.rb_unsure.Text = "Unsure - Possible event but uncertain"
        self.rb_unsure.Location = Point(int(15 * sf), int(140 * sf))
        self.rb_unsure.Size = Size(int(460 * sf), int(25 * sf))
        grp_type.Controls.Add(self.rb_unsure)
        
        lbl_unsure_desc = Label()
        lbl_unsure_desc.Text = "You will be prompted to import AOTA timing data if available"
        lbl_unsure_desc.Location = Point(int(35 * sf), int(165 * sf))
        lbl_unsure_desc.Size = Size(int(440 * sf), int(20 * sf))
        lbl_unsure_desc.ForeColor = Color.Gray
        grp_type.Controls.Add(lbl_unsure_desc)
        
        y_pos += int(190 * sf)
        
        # Info label
        lbl_info = Label()
        lbl_info.Text = ("Note: This selection will be recorded in the report.\n" +
                        "You can change other details manually in the Excel file after generation.")
        lbl_info.Location = Point(int(10 * sf), y_pos)
        lbl_info.Size = Size(int(490 * sf), int(40 * sf))
        lbl_info.ForeColor = Color.Gray
        panel.Controls.Add(lbl_info)
        y_pos += int(50 * sf)
        
        # Buttons
        btn_ok = Button()
        btn_ok.Text = "Next"
        btn_ok.Location = Point(int(390 * sf), y_pos)
        btn_ok.Size = Size(int(100 * sf), int(28 * sf))
        btn_ok.Click += self.ok_click
        panel.Controls.Add(btn_ok)
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.DialogResult = DialogResult.Cancel
        btn_cancel.Location = Point(int(280 * sf), y_pos)
        _autosize_button(btn_cancel, sf)
        panel.Controls.Add(btn_cancel)
        
        self.AcceptButton = btn_ok
        self.CancelButton = btn_cancel
    
    def ok_click(self, sender, e):
        """Handle OK button click"""
        if self.rb_positive.Checked:
            self.selected_type = "Positive"
        elif self.rb_negative.Checked:
            self.selected_type = "Negative"
        elif self.rb_unsure.Checked:
            self.selected_type = "Unsure"
        else:
            MessageBox.Show("Please select an observation type.", "No Selection",
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        self.DialogResult = DialogResult.OK
    
    def get_selected_type(self):
        """Get the selected observation type"""
        return self.selected_type


class AOTAFilePickerDialog(Form):
    """Dialog for selecting an AOTA XML file"""
    
    def __init__(self, theme_manager, event_name=None):
        Form.__init__(self)
        self.theme_manager = theme_manager
        self.event_name = event_name
        self.selected_file_path = None
        self._sf = _detect_scale_factor()
        
        self.setup_ui()
        
        # Apply theme
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup file picker UI"""
        sf = self._sf
        
        self.Text = "Import AOTA Analysis"
        self.Size = Size(int(600 * sf), int(300 * sf))
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        # Main panel
        panel = Panel()
        panel.Dock = DockStyle.Fill
        from System.Windows.Forms import Padding as PaddingClass
        panel.Padding = PaddingClass(int(20 * sf), int(20 * sf), int(20 * sf), int(20 * sf))
        self.Controls.Add(panel)
        
        y_pos = 10
        
        # Event info if provided
        if self.event_name:
            lbl_event = Label()
            lbl_event.Text = f"Importing AOTA data for: {self.event_name}"
            lbl_event.Location = Point(int(10 * sf), y_pos)
            lbl_event.Size = Size(int(540 * sf), int(25 * sf))
            lbl_event.Font = Font(lbl_event.Font.FontFamily, 10, FontStyle.Bold)
            panel.Controls.Add(lbl_event)
            y_pos += int(35 * sf)
        
        # Instructions
        lbl_instructions = Label()
        lbl_instructions.Text = ("AOTA (Asteroid Occultation Timing Analysis) files contain timing data\n" +
                                "from video analysis. Select your AOTA XML file below.")
        lbl_instructions.Location = Point(int(10 * sf), y_pos)
        lbl_instructions.Size = Size(int(540 * sf), int(40 * sf))
        panel.Controls.Add(lbl_instructions)
        y_pos += int(50 * sf)
        
        # File selection group
        grp_file = GroupBox()
        grp_file.Text = "AOTA File Selection"
        grp_file.Location = Point(int(10 * sf), y_pos)
        grp_file.Size = Size(int(540 * sf), int(90 * sf))
        panel.Controls.Add(grp_file)
        
        # File path label
        lbl_file = Label()
        lbl_file.Text = "Selected File:"
        lbl_file.Location = Point(int(15 * sf), int(25 * sf))
        lbl_file.Size = Size(int(90 * sf), int(20 * sf))
        grp_file.Controls.Add(lbl_file)
        
        # File path display
        self.lbl_file_path = Label()
        self.lbl_file_path.Text = "(No file selected)"
        self.lbl_file_path.Location = Point(int(110 * sf), int(25 * sf))
        self.lbl_file_path.Size = Size(int(410 * sf), int(20 * sf))
        self.lbl_file_path.AutoEllipsis = True
        grp_file.Controls.Add(self.lbl_file_path)
        
        # Browse button
        btn_browse = Button()
        btn_browse.Text = "Browse for AOTA File..."
        btn_browse.Location = Point(int(15 * sf), int(55 * sf))
        btn_browse.Size = Size(int(180 * sf), int(28 * sf))
        btn_browse.Click += self.browse_click
        grp_file.Controls.Add(btn_browse)
        
        y_pos += int(100 * sf)
        
        # Info about file format
        lbl_info = Label()
        lbl_info.Text = "AOTA files have extension: *.aota.xml"
        lbl_info.Location = Point(int(10 * sf), y_pos)
        lbl_info.Size = Size(int(540 * sf), int(20 * sf))
        from System.Drawing import Color
        lbl_info.ForeColor = Color.Gray
        panel.Controls.Add(lbl_info)
        y_pos += int(30 * sf)
        
        # Buttons
        btn_ok = Button()
        btn_ok.Text = "OK"
        btn_ok.Location = Point(int(390 * sf), y_pos)
        btn_ok.Click += self.ok_click
        _autosize_button(btn_ok, sf)
        panel.Controls.Add(btn_ok)
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.DialogResult = DialogResult.Cancel
        btn_cancel.Location = Point(int(475 * sf), y_pos)
        _autosize_button(btn_cancel, sf)
        panel.Controls.Add(btn_cancel)
        
        self.AcceptButton = btn_ok
        self.CancelButton = btn_cancel
    
    def browse_click(self, sender, e):
        """Handle browse button click"""
        dialog = OpenFileDialog()
        dialog.Title = "Select AOTA XML File"
        dialog.Filter = "AOTA XML Files (*.aota.xml)|*.aota.xml|XML Files (*.xml)|*.xml|All Files (*.*)|*.*"
        dialog.FilterIndex = 1
        
        if dialog.ShowDialog() == DialogResult.OK:
            self.selected_file_path = dialog.FileName
            self.lbl_file_path.Text = self.selected_file_path
    
    def ok_click(self, sender, e):
        """Handle OK button click"""
        if not self.selected_file_path:
            MessageBox.Show("Please select an AOTA file.", "No File Selected",
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        # Check file exists
        import os
        if not os.path.exists(self.selected_file_path):
            MessageBox.Show(f"File not found:\n{self.selected_file_path}", 
                          "File Not Found",
                          MessageBoxButtons.OK, MessageBoxIcon.Error)
            return
        
        self.DialogResult = DialogResult.OK
    
    def get_selected_file_path(self):
        """Get the selected file path"""
        return self.selected_file_path


class AOTAEventSelectionDialog(Form):
    """Dialog for selecting which AOTA event to use when multiple events are found"""
    
    def __init__(self, theme_manager, aota_result, event_name=None):
        Form.__init__(self)
        self.theme_manager = theme_manager
        self.aota_result = aota_result
        self.event_name = event_name
        self.selected_event = None
        self._sf = _detect_scale_factor()
        
        self.setup_ui()
        
        # Apply theme
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup event selection UI"""
        sf = self._sf
        
        self.Text = "Select AOTA Event"
        self.Size = Size(int(700 * sf), int(500 * sf))
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        # Main panel
        panel = Panel()
        panel.Dock = DockStyle.Fill
        from System.Windows.Forms import Padding as PaddingClass
        panel.Padding = PaddingClass(int(20 * sf), int(20 * sf), int(20 * sf), int(20 * sf))
        self.Controls.Add(panel)
        
        y_pos = 10
        
        # Title
        lbl_title = Label()
        lbl_title.Text = "Multiple Events Found in AOTA File"
        lbl_title.Location = Point(int(10 * sf), y_pos)
        lbl_title.Size = Size(int(640 * sf), int(25 * sf))
        lbl_title.Font = Font(lbl_title.Font.FontFamily, 11, FontStyle.Bold)
        panel.Controls.Add(lbl_title)
        y_pos += int(35 * sf)
        
        # Event info if provided
        if self.event_name:
            lbl_event = Label()
            lbl_event.Text = f"Generating report for: {self.event_name}"
            lbl_event.Location = Point(int(10 * sf), y_pos)
            lbl_event.Size = Size(int(640 * sf), int(20 * sf))
            panel.Controls.Add(lbl_event)
            y_pos += int(30 * sf)
        
        # Instructions
        lbl_instructions = Label()
        lbl_instructions.Text = "Please select which event timing to use for the report:"
        lbl_instructions.Location = Point(int(10 * sf), y_pos)
        lbl_instructions.Size = Size(int(640 * sf), int(20 * sf))
        panel.Controls.Add(lbl_instructions)
        y_pos += int(30 * sf)
        
        # AOTA info
        lbl_aota_info = Label()
        info_parts = []
        if self.aota_result.aota_version:
            info_parts.append(f"AOTA Version: {self.aota_result.aota_version}")
        if self.aota_result.camera_result.camera_type:
            info_parts.append(f"Camera: {self.aota_result.camera_result.camera_type}")
        if self.aota_result.camera_result.measuring_tool:
            info_parts.append(f"Tool: {self.aota_result.camera_result.measuring_tool}")
        lbl_aota_info.Text = " | ".join(info_parts) if info_parts else "AOTA File Information"
        lbl_aota_info.Location = Point(int(10 * sf), y_pos)
        lbl_aota_info.Size = Size(int(640 * sf), int(20 * sf))
        from System.Drawing import Color
        lbl_aota_info.ForeColor = Color.DarkBlue
        panel.Controls.Add(lbl_aota_info)
        y_pos += int(30 * sf)
        
        # Event list
        lbl_events = Label()
        lbl_events.Text = "Available Events:"
        lbl_events.Location = Point(int(10 * sf), y_pos)
        lbl_events.Size = Size(int(200 * sf), int(20 * sf))
        panel.Controls.Add(lbl_events)
        y_pos += int(25 * sf)
        
        # ListBox for events
        self.lst_events = ListBox()
        self.lst_events.Location = Point(int(10 * sf), y_pos)
        self.lst_events.Size = Size(int(640 * sf), int(200 * sf))
        self.lst_events.SelectionMode = SelectionMode.One
        self.lst_events.Font = Font("Courier New", 9 * sf)  # Monospace for alignment
        panel.Controls.Add(self.lst_events)
        
        # Populate list with valid events only
        valid_events = self.aota_result.get_valid_events()
        for i, event in enumerate(valid_events):
            display_text = f"Event {i+1}: {str(event)}"
            self.lst_events.Items.Add(display_text)
        
        # Select first event by default
        if self.lst_events.Items.Count > 0:
            self.lst_events.SelectedIndex = 0
        
        y_pos += int(210 * sf)
        
        # Additional info
        lbl_info = Label()
        lbl_info.Text = ("D = Disappearance | R = Reappearance\n" +
                        "Times shown as HH:MM:SS.S with uncertainty in seconds\n" +
                        "Select the event that corresponds to your observation")
        lbl_info.Location = Point(int(10 * sf), y_pos)
        lbl_info.Size = Size(int(640 * sf), int(60 * sf))
        lbl_info.ForeColor = Color.Gray
        panel.Controls.Add(lbl_info)
        y_pos += int(70 * sf)
        
        # Buttons
        btn_ok = Button()
        btn_ok.Text = "Use Selected Event"
        btn_ok.Location = Point(int(470 * sf), y_pos)
        btn_ok.Size = Size(int(160 * sf), int(28 * sf))
        btn_ok.Click += self.ok_click
        panel.Controls.Add(btn_ok)
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.DialogResult = DialogResult.Cancel
        btn_cancel.Location = Point(int(350 * sf), y_pos)
        _autosize_button(btn_cancel, sf)
        panel.Controls.Add(btn_cancel)
        
        self.AcceptButton = btn_ok
        self.CancelButton = btn_cancel
    
    def ok_click(self, sender, e):
        """Handle OK button click"""
        if self.lst_events.SelectedIndex < 0:
            MessageBox.Show("Please select an event.", "No Event Selected",
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        # Get the selected event from valid events list
        valid_events = self.aota_result.get_valid_events()
        self.selected_event = valid_events[self.lst_events.SelectedIndex]
        
        self.DialogResult = DialogResult.OK
    
    def get_selected_event(self):
        """Get the selected AOTA event"""
        return self.selected_event
