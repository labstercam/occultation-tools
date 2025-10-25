import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

import os
import webbrowser
from System.Drawing import Point, Size, Color, Font, FontStyle
from System.Windows.Forms import (
    Form, Label, TextBox, Button, MessageBox, MessageBoxButtons, MessageBoxIcon,
    DialogResult, FormStartPosition, FormBorderStyle, Panel, GroupBox, LinkLabel,
    TabControl, TabPage, ListBox, ScrollBars, SelectionMode, AnchorStyles,
    CheckBox, FolderBrowserDialog, DockStyle
)
from theme import apply_theme_to_control
from templates import TemplateManager

class ExposureEditDialog(Form):
    """Dialog for editing event exposure - FIXED VERSION"""
    
    def __init__(self, event, theme_manager):
        Form.__init__(self)
        self.event = event
        self.theme_manager = theme_manager
        self.new_exposure_ms = event.exposure_ms
        self.setup_ui()
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup exposure edit dialog UI"""
        self.Text = f"Edit Exposure - {self.event.event_name}"
        self.Size = Size(400, 300)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        # Event info
        lbl_event = Label()
        lbl_event.Text = f"Event: {self.event.event_name}"
        lbl_event.Location = Point(20, 20)
        lbl_event.Size = Size(350, 20)
        lbl_event.Font = Font("Microsoft Sans Serif", 9, FontStyle.Bold)
        self.Controls.Add(lbl_event)
        
        lbl_star = Label()
        lbl_star.Text = f"Mag: {self.event.star_mag:.1f}, Mag Drop: {self.event.mag_drop:.1f}, Max Dur: {self.event.max_duration_seconds:.1f}s"
        lbl_star.Location = Point(20, 45)
        lbl_star.Size = Size(350, 20)
        self.Controls.Add(lbl_star)
        
        lbl_current = Label()
        current_text = f"Current Exposure: {self.event.exposure_ms} ms"
        if self.event.has_custom_exposure():
            current_text += " (Custom)"
        else:
            current_text += " (Calculated)"
        lbl_current.Text = current_text
        lbl_current.Location = Point(20, 80)
        lbl_current.Size = Size(350, 20)
        self.Controls.Add(lbl_current)
        
        # Exposure input
        lbl_new_exposure = Label()
        lbl_new_exposure.Text = "New Exposure (ms):"
        lbl_new_exposure.Location = Point(20, 105)
        lbl_new_exposure.Size = Size(120, 20)
        self.Controls.Add(lbl_new_exposure)
        
        self.txt_exposure = TextBox()
        self.txt_exposure.Text = str(self.event.exposure_ms)
        self.txt_exposure.Location = Point(150, 105)
        self.txt_exposure.Size = Size(100, 20)
        self.Controls.Add(self.txt_exposure)
        
        # Quick exposure buttons
        lbl_quick = Label()
        lbl_quick.Text = "Quick Settings:"
        lbl_quick.Location = Point(20, 130)
        lbl_quick.Size = Size(100, 20)
        self.Controls.Add(lbl_quick)
        
        quick_exposures = [40, 60, 80, 120, 160, 240, 320, 480]
        x_pos = 20
        y_pos = 155
        
        for i, exp in enumerate(quick_exposures):
            btn = Button()
            btn.Text = f"{exp}"
            btn.Size = Size(45, 25)
            btn.Location = Point(x_pos, y_pos)
            btn.Tag = exp
            btn.Click += self.quick_exposure_click
            self.Controls.Add(btn)
            
            x_pos += 50
            if (i + 1) % 4 == 0:
                x_pos = 20
                y_pos += 30
        
        # Buttons
        btn_ok = Button()
        btn_ok.Text = "OK"
        btn_ok.DialogResult = DialogResult.OK
        btn_ok.Location = Point(220, 220)
        btn_ok.Size = Size(75, 25)
        btn_ok.Click += self.ok_click
        self.Controls.Add(btn_ok)
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.DialogResult = DialogResult.Cancel
        btn_cancel.Location = Point(305, 220)
        btn_cancel.Size = Size(75, 25)
        self.Controls.Add(btn_cancel)
        
        btn_reset = Button()
        btn_reset.Text = "Reset to Calculated"
        btn_reset.Location = Point(20, 220)
        btn_reset.Size = Size(120, 25)
        btn_reset.Click += self.reset_click
        self.Controls.Add(btn_reset)
        
        self.AcceptButton = btn_ok
        self.CancelButton = btn_cancel
    
    def quick_exposure_click(self, sender, e):
        """Handle quick exposure button click"""
        self.txt_exposure.Text = str(sender.Tag)
    
    def reset_click(self, sender, e):
        """Reset to calculated exposure"""
        # Temporarily clear custom exposure to get calculated value
        original_custom = self.event.custom_exposure
        self.event.custom_exposure = None
        self.event._calculate_derived_values()
        calculated_exposure = self.event.exposure_ms
        self.event.custom_exposure = original_custom
        self.event._calculate_derived_values()
        
        self.txt_exposure.Text = str(calculated_exposure)
    
    def ok_click(self, sender, e):
        """Handle OK button click - FIXED VERSION"""
        try:
            exposure_text = self.txt_exposure.Text.strip()
            if not exposure_text:
                MessageBox.Show("Please enter an exposure value", "Invalid Input", 
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            self.new_exposure_ms = int(exposure_text)
            if self.new_exposure_ms < 1 or self.new_exposure_ms > 10000:
                MessageBox.Show("Exposure must be between 1 and 10000 ms", "Invalid Exposure", 
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                # FIXED: Don't set DialogResult on invalid input - dialog stays open
                return
            
            # Only set OK result if validation passes
            self.DialogResult = DialogResult.OK
            
        except ValueError:
            MessageBox.Show("Please enter a valid number", "Invalid Input", 
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
            # FIXED: Don't set DialogResult on error - dialog stays open
            return
    
    def get_new_exposure(self):
        """Get the new exposure value"""
        return self.new_exposure_ms

class EventDetailsDialog(Form):
    """Dialog for displaying detailed event information"""
    
    def __init__(self, event, theme_manager):
        Form.__init__(self)
        self.event = event
        self.theme_manager = theme_manager
        self.setup_ui()
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup event details dialog UI"""
        self.Text = f"Event Details - {self.event.get_asteroid_display_name()}"
        self.Size = Size(600, 700)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.MaximizeBox = True
        self.MinimizeBox = True
        
        # Create main panel with scroll capability
        main_panel = Panel()
        main_panel.Dock = DockStyle.Fill
        main_panel.AutoScroll = True
        self.Controls.Add(main_panel)
        
        y_pos = 20
        
        # Event Information Group
        grp_event = GroupBox()
        grp_event.Text = "Event Information"
        grp_event.Location = Point(10, y_pos)
        grp_event.Size = Size(560, 120)
        main_panel.Controls.Add(grp_event)
        
        y_pos += 130
        
        self.add_detail_label(grp_event, "Event Name:", self.event.event_name, 10, 25)
        self.add_detail_label(grp_event, "Asteroid:", self.event.get_asteroid_display_name(), 10, 50)
        self.add_detail_label(grp_event, "Star:", f"{self.event.star_name} (ID: {self.event.star_id})", 10, 75)
        self.add_detail_label(grp_event, "Station:", self.event.station_name, 300, 25)
        self.add_detail_label(grp_event, "Source:", self.event.source, 300, 50)
        
        # Add OWC link if available
        if hasattr(self.event, 'owcloudurl') and self.event.owcloudurl:
            link_label = LinkLabel()
            link_label.Text = "View on OWC"
            link_label.Location = Point(300, 75)
            link_label.Size = Size(100, 20)
            link_label.LinkClicked += lambda s, e: webbrowser.open(self.event.owcloudurl)
            grp_event.Controls.Add(link_label)
        
        # Timing Information Group
        grp_timing = GroupBox()
        grp_timing.Text = "Timing Information"
        grp_timing.Location = Point(10, y_pos)
        grp_timing.Size = Size(560, 120)
        main_panel.Controls.Add(grp_timing)
        
        y_pos += 130

        self.add_detail_label(grp_timing, "Event Time (UTC):", self.event.event_time, 10, 25)
        self.add_detail_label(grp_timing, "GOTO Time (UTC):", self.event.goto_time_str, 10, 50)
        self.add_detail_label(grp_timing, "Start Time (UTC):", self.event.start_time_str, 10, 75)
        self.add_detail_label(grp_timing, "End Time (UTC):", self.event.end_time_str, 300, 25)
        self.add_detail_label(grp_timing, "Max Duration:", f"{self.event.max_duration_seconds:.1f} seconds", 300, 50)
        self.add_detail_label(grp_timing, "Time Error:", f"{self.event.uncertainty_seconds:.1f} seconds", 300, 75)
        
        # Recording Settings Group
        grp_recording = GroupBox()
        grp_recording.Text = "Recording Settings"
        grp_recording.Location = Point(10, y_pos)
        grp_recording.Size = Size(560, 120)
        main_panel.Controls.Add(grp_recording)
        
        y_pos += 130
        
        exposure_text = f"{self.event.exposure_ms} ms"
        if self.event.has_custom_exposure():
            exposure_text += " (Custom)"
        else:
            exposure_text += " (Calculated)"
        
        self.add_detail_label(grp_recording, "Exposure:", exposure_text, 10, 25)
        self.add_detail_label(grp_recording, "Recording Duration:", f"{self.event.recording_duration} seconds", 10, 50)
        self.add_detail_label(grp_recording, "Pre-calc Exposure:", f"{self.event.precalc_exposure:.3f} seconds", 300, 25)
        
        # Photometry Information Group
        grp_photometry = GroupBox()
        grp_photometry.Text = "Photometry Information"
        grp_photometry.Location = Point(10, y_pos)
        grp_photometry.Size = Size(560, 120)
        main_panel.Controls.Add(grp_photometry)
        
        y_pos += 130
        
        self.add_detail_label(grp_photometry, "Star Magnitude:", f"{self.event.star_mag:.1f}", 10, 25)
        self.add_detail_label(grp_photometry, "Combined Magnitude:", f"{self.event.comb_mag:.1f}", 10, 50)
        self.add_detail_label(grp_photometry, "Magnitude Drop:", f"{self.event.mag_drop:.1f}", 10, 75)
        
        # Position Information Group
        grp_position = GroupBox()
        grp_position.Text = "Position Information"
        grp_position.Location = Point(10, y_pos)
        grp_position.Size = Size(560, 120)
        main_panel.Controls.Add(grp_position)
        
        y_pos += 130
        
        self.add_detail_label(grp_position, "RA (J2000):", f"{self.event.ra:.6f} hours", 10, 25)
        self.add_detail_label(grp_position, "Dec (J2000):", f"{self.event.dec:.6f}°", 10, 50)
        self.add_detail_label(grp_position, "Altitude:", f"{self.event.star_alt:.1f}°", 300, 25)
        self.add_detail_label(grp_position, "Azimuth:", f"{self.event.star_az:.1f}°", 300, 50)
        
        # Observer Location Group
        grp_location = GroupBox()
        grp_location.Text = "Observer Location"
        grp_location.Location = Point(10, y_pos)
        grp_location.Size = Size(560, 95)
        main_panel.Controls.Add(grp_location)
        
        y_pos += 105
        
        self.add_detail_label(grp_location, "Latitude:", f"{self.event.latitude:.6f}°", 10, 25)
        self.add_detail_label(grp_location, "Longitude:", f"{self.event.longitude:.6f}°", 10, 50)
        
        # Technical Information Group
        grp_technical = GroupBox()
        grp_technical.Text = "Technical Information"
        grp_technical.Location = Point(10, y_pos)
        grp_technical.Size = Size(560, 95)
        main_panel.Controls.Add(grp_technical)
        
        y_pos += 105
        
        self.add_detail_label(grp_technical, "Event ID:", self.event.event_id, 10, 25)
        self.add_detail_label(grp_technical, "OW Event ID:", str(self.event.ow_eventid), 10, 50)
        self.add_detail_label(grp_technical, "Object Number:", self.event.object_no, 300, 25)
        
        # Close button
        btn_close = Button()
        btn_close.Text = "Close"
        btn_close.DialogResult = DialogResult.OK
        btn_close.Location = Point(500, y_pos + 20)
        btn_close.Size = Size(75, 25)
        main_panel.Controls.Add(btn_close)
        
        self.AcceptButton = btn_close
    
    def add_detail_label(self, parent, label_text, value_text, x, y):
        """Helper to add label-value pairs"""
        lbl_name = Label()
        lbl_name.Text = label_text
        lbl_name.Location = Point(x, y)
        lbl_name.Size = Size(120, 20)
        lbl_name.Font = Font("Microsoft Sans Serif", 8, FontStyle.Bold)
        parent.Controls.Add(lbl_name)
        
        lbl_value = Label()
        lbl_value.Text = str(value_text) if value_text is not None else "N/A"
        lbl_value.Location = Point(x + 125, y)
        lbl_value.Size = Size(150, 20)
        lbl_value.Font = Font("Microsoft Sans Serif", 8)
        parent.Controls.Add(lbl_value)

class ConfigurationDialog(Form):
    """Configuration dialog for GUI"""
    
    def __init__(self, config, theme_manager):
        Form.__init__(self)
        self.config = config
        self.theme_manager = theme_manager
        self.setup_ui()
        self.load_current_config()
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup configuration dialog UI"""
        self.Text = "Configuration Settings"
        self.Size = Size(600, 700)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        # Create tabs
        tab_control = TabControl()
        tab_control.Location = Point(10, 10)
        tab_control.Size = Size(560, 600)
        self.Controls.Add(tab_control)
        
        # User Credentials Tab
        tab_credentials = TabPage()
        tab_credentials.Text = "Credentials"
        self.setup_credentials_tab(tab_credentials)
        tab_control.TabPages.Add(tab_credentials)
        
        # File Paths Tab
        tab_paths = TabPage()
        tab_paths.Text = "File Paths"
        self.setup_paths_tab(tab_paths)
        tab_control.TabPages.Add(tab_paths)
        
        # Recording Settings Tab
        tab_recording = TabPage()
        tab_recording.Text = "Recording"
        self.setup_recording_tab(tab_recording)
        tab_control.TabPages.Add(tab_recording)
        
        # API Settings Tab
        tab_api = TabPage()
        tab_api.Text = "API Settings"
        self.setup_api_tab(tab_api)
        tab_control.TabPages.Add(tab_api)
        
        # Buttons
        btn_ok = Button()
        btn_ok.Text = "Save"
        btn_ok.DialogResult = DialogResult.OK
        btn_ok.Location = Point(350, 630)
        btn_ok.Size = Size(75, 25)
        btn_ok.Click += self.save_config_click
        self.Controls.Add(btn_ok)
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.DialogResult = DialogResult.Cancel
        btn_cancel.Location = Point(435, 630)
        btn_cancel.Size = Size(75, 25)
        self.Controls.Add(btn_cancel)
        
        btn_reset = Button()
        btn_reset.Text = "Reset to Defaults"
        btn_reset.Location = Point(10, 630)
        btn_reset.Size = Size(120, 25)
        btn_reset.Click += self.reset_defaults_click
        self.Controls.Add(btn_reset)
        
        self.AcceptButton = btn_ok
        self.CancelButton = btn_cancel
    
    def setup_credentials_tab(self, tab):
        """Setup credentials tab"""
        lbl_email = Label()
        lbl_email.Text = "OWC Email:"
        lbl_email.Location = Point(20, 30)
        lbl_email.Size = Size(100, 20)
        tab.Controls.Add(lbl_email)
        
        self.txt_email = TextBox()
        self.txt_email.Location = Point(130, 30)
        self.txt_email.Size = Size(300, 20)
        tab.Controls.Add(self.txt_email)
        
        lbl_password = Label()
        lbl_password.Text = "OWC Password:"
        lbl_password.Location = Point(20, 60)
        lbl_password.Size = Size(100, 20)
        tab.Controls.Add(lbl_password)
        
        self.txt_password = TextBox()
        self.txt_password.Location = Point(130, 60)
        self.txt_password.Size = Size(300, 20)
        self.txt_password.UseSystemPasswordChar = True
        tab.Controls.Add(self.txt_password)
    
    def setup_paths_tab(self, tab):
        """Setup file paths tab"""
        lbl_file_folder = Label()
        lbl_file_folder.Text = "File Folder:"
        lbl_file_folder.Location = Point(20, 30)
        lbl_file_folder.Size = Size(100, 20)
        tab.Controls.Add(lbl_file_folder)
        
        self.txt_file_folder = TextBox()
        self.txt_file_folder.Location = Point(130, 30)
        self.txt_file_folder.Size = Size(250, 20)
        tab.Controls.Add(self.txt_file_folder)
        
        btn_browse_folder = Button()
        btn_browse_folder.Text = "Browse"
        btn_browse_folder.Location = Point(390, 29)
        btn_browse_folder.Size = Size(60, 22)
        btn_browse_folder.Click += self.browse_file_folder_click
        tab.Controls.Add(btn_browse_folder)
        
        lbl_sequence_path = Label()
        lbl_sequence_path.Text = "Sequence Path:"
        lbl_sequence_path.Location = Point(20, 60)
        lbl_sequence_path.Size = Size(100, 20)
        tab.Controls.Add(lbl_sequence_path)
        
        self.txt_sequence_path = TextBox()
        self.txt_sequence_path.Location = Point(130, 60)
        self.txt_sequence_path.Size = Size(250, 20)
        tab.Controls.Add(self.txt_sequence_path)
        
        btn_browse_sequence = Button()
        btn_browse_sequence.Text = "Browse"
        btn_browse_sequence.Location = Point(390, 59)
        btn_browse_sequence.Size = Size(60, 22)
        btn_browse_sequence.Click += self.browse_sequence_path_click
        tab.Controls.Add(btn_browse_sequence)
        
        lbl_occ_file = Label()
        lbl_occ_file.Text = "Occultations File:"
        lbl_occ_file.Location = Point(20, 90)
        lbl_occ_file.Size = Size(100, 20)
        tab.Controls.Add(lbl_occ_file)
        
        self.txt_occ_file = TextBox()
        self.txt_occ_file.Location = Point(130, 90)
        self.txt_occ_file.Size = Size(300, 20)
        tab.Controls.Add(self.txt_occ_file)
        
        lbl_latest_file = Label()
        lbl_latest_file.Text = "Latest File:"
        lbl_latest_file.Location = Point(20, 120)
        lbl_latest_file.Size = Size(100, 20)
        tab.Controls.Add(lbl_latest_file)
        
        self.txt_latest_file = TextBox()
        self.txt_latest_file.Location = Point(130, 120)
        self.txt_latest_file.Size = Size(300, 20)
        tab.Controls.Add(self.txt_latest_file)
    
    def setup_recording_tab(self, tab):
        """Setup recording settings tab"""
        lbl_base_duration = Label()
        lbl_base_duration.Text = "Base Duration (s):"
        lbl_base_duration.Location = Point(20, 30)
        lbl_base_duration.Size = Size(120, 20)
        tab.Controls.Add(lbl_base_duration)
        
        self.txt_base_duration = TextBox()
        self.txt_base_duration.Location = Point(150, 30)
        self.txt_base_duration.Size = Size(100, 20)
        tab.Controls.Add(self.txt_base_duration)
        
        lbl_goto_lead = Label()
        lbl_goto_lead.Text = "GOTO Lead Time (s):"
        lbl_goto_lead.Location = Point(20, 60)
        lbl_goto_lead.Size = Size(120, 20)
        tab.Controls.Add(lbl_goto_lead)
        
        self.txt_goto_lead = TextBox()
        self.txt_goto_lead.Location = Point(150, 60)
        self.txt_goto_lead.Size = Size(100, 20)
        tab.Controls.Add(self.txt_goto_lead)
        
        lbl_mag_exposure = Label()
        lbl_mag_exposure.Text = "Mag for 40ms exp:"
        lbl_mag_exposure.Location = Point(20, 90)
        lbl_mag_exposure.Size = Size(120, 20)
        tab.Controls.Add(lbl_mag_exposure)
        
        self.txt_mag_exposure = TextBox()
        self.txt_mag_exposure.Location = Point(150, 90)
        self.txt_mag_exposure.Size = Size(100, 20)
        tab.Controls.Add(self.txt_mag_exposure)

        self.chk_sync_mount = CheckBox()
        self.chk_sync_mount.Text = "Sync Mount with GOTO"       
        self.chk_sync_mount.Location = Point(20, 120)
        self.chk_sync_mount.Size = Size(200, 20)    
        tab.Controls.Add(self.chk_sync_mount)

        self.chk_sync_mount.Checked = self.config.get_sync_mount()
        self.chk_sync_mount.CheckedChanged += self.sync_mount_checked_changed
    
    def sync_mount_checked_changed(self, sender, e):
        """Handle sync mount checkbox change"""
        self.config.set_sync_mount(self.chk_sync_mount.Checked) 


    def setup_api_tab(self, tab):
        """Setup API settings tab"""
        lbl_host = Label()
        lbl_host.Text = "API Host:"
        lbl_host.Location = Point(20, 30)
        lbl_host.Size = Size(100, 20)
        tab.Controls.Add(lbl_host)
        
        self.txt_host = TextBox()
        self.txt_host.Location = Point(130, 30)
        self.txt_host.Size = Size(300, 20)
        tab.Controls.Add(self.txt_host)
        
        lbl_api_key = Label()
        lbl_api_key.Text = "API Key:"
        lbl_api_key.Location = Point(20, 60)
        lbl_api_key.Size = Size(100, 20)
        tab.Controls.Add(lbl_api_key)
        
        self.txt_api_key = TextBox()
        self.txt_api_key.Location = Point(130, 60)
        self.txt_api_key.Size = Size(300, 20)
        tab.Controls.Add(self.txt_api_key)
    
    def load_current_config(self):
        """Load current configuration into controls"""
        self.txt_email.Text = self.config.get_owc_email()
        self.txt_password.Text = self.config.get_owc_password()
        self.txt_file_folder.Text = self.config.get_file_folder()
        self.txt_sequence_path.Text = self.config.get_sequence_path()
        self.txt_occ_file.Text = self.config.get_occultations_file()
        self.txt_latest_file.Text = self.config.get_latest_occultations_file()
        self.txt_base_duration.Text = str(self.config.get_base_duration())
        self.txt_goto_lead.Text = str(self.config.get_goto_lead_time())
        self.txt_mag_exposure.Text = str(self.config.get_mag_for_40ms_exposure())
        self.chk_sync_mount.Checked = self.config.get_sync_mount()
        self.txt_host.Text = self.config.get_host()
        self.txt_api_key.Text = self.config.get_api_key()
    
    def browse_file_folder_click(self, sender, e):
        """Browse for file folder"""
        dialog = FolderBrowserDialog()
        dialog.SelectedPath = self.txt_file_folder.Text
        if dialog.ShowDialog() == DialogResult.OK:
            self.txt_file_folder.Text = dialog.SelectedPath
    
    def browse_sequence_path_click(self, sender, e):
        """Browse for sequence path"""
        dialog = FolderBrowserDialog()
        dialog.SelectedPath = self.txt_sequence_path.Text
        if dialog.ShowDialog() == DialogResult.OK:
            self.txt_sequence_path.Text = dialog.SelectedPath
    
    def save_config_click(self, sender, e):
        """Save configuration"""
        try:
            # Update config with form values
            self.config.set_owc_email(self.txt_email.Text)
            self.config.set_owc_password(self.txt_password.Text)
            self.config.set_file_folder(self.txt_file_folder.Text)
            self.config.set_sequence_path(self.txt_sequence_path.Text)
            self.config.set_occultations_file(self.txt_occ_file.Text)
            self.config.set_latest_occultations_file(self.txt_latest_file.Text)
            self.config.set_base_duration(int(self.txt_base_duration.Text))
            self.config.set_goto_lead_time(int(self.txt_goto_lead.Text))
            self.config.set_mag_for_40ms_exposure(float(self.txt_mag_exposure.Text))
            self.config.set_sync_mount(self.chk_sync_mount.Checked)
            self.config.set_host(self.txt_host.Text)
            self.config.set_api_key(self.txt_api_key.Text)
            
            # Validate and save
            errors = self.config.validate_config()
            if errors:
                MessageBox.Show("Configuration errors:\n" + "\n".join(errors), 
                              "Configuration Error", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            if self.config.save_config():
                MessageBox.Show("Configuration saved successfully!", "Success", 
                              MessageBoxButtons.OK, MessageBoxIcon.Information)
            else:
                MessageBox.Show("Failed to save configuration!", "Error", 
                              MessageBoxButtons.OK, MessageBoxIcon.Error)
                
        except ValueError as e:
            MessageBox.Show(f"Invalid numeric value: {e}", "Input Error", 
                          MessageBoxButtons.OK, MessageBoxIcon.Error)
        except Exception as e:
            MessageBox.Show(f"Error saving configuration: {e}", "Error", 
                          MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def reset_defaults_click(self, sender, e):
        """Reset to default configuration"""
        if MessageBox.Show("Reset all settings to defaults?", "Confirm Reset", 
                         MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes:
            self.config.reset_to_defaults()
            self.load_current_config()
            MessageBox.Show("Configuration reset to defaults", "Reset Complete", 
                          MessageBoxButtons.OK, MessageBoxIcon.Information)

class TemplateSelectionDialog(Form):
    """Enhanced dialog for selecting sequence template with proper preview"""
    
    def __init__(self, config, theme_manager):
        Form.__init__(self)
        self.config = config
        self.theme_manager = theme_manager
        self.selected_template_path = ""
        #self.template_manager = TemplateManager(config)
        self.setup_ui()
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup enhanced template selection UI with proper scrolling"""
        self.Text = "Select Sequence Template"
        self.Size = Size(800, 600)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.MaximizeBox = True
        self.MinimizeBox = True
        
        # Template list
        lbl_templates = Label()
        lbl_templates.Text = "Available Templates:"
        lbl_templates.Location = Point(10, 10)
        lbl_templates.Size = Size(200, 20)
        self.Controls.Add(lbl_templates)
        
        self.lst_templates = ListBox()
        self.lst_templates.Location = Point(10, 35)
        self.lst_templates.Size = Size(760, 150)
        self.lst_templates.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        self.lst_templates.SelectionMode = SelectionMode.One
        self.Controls.Add(self.lst_templates)
        
        # Load templates
        self.load_templates()
        
        # Template preview with proper scrolling - FIXED
        lbl_preview = Label()
        lbl_preview.Text = "Template Preview:"
        lbl_preview.Location = Point(10, 200)
        lbl_preview.Size = Size(200, 20)
        self.Controls.Add(lbl_preview)
        
        self.txt_preview = TextBox()
        self.txt_preview.Multiline = True
        self.txt_preview.ReadOnly = True
        self.txt_preview.ScrollBars = ScrollBars.Both  # Both horizontal and vertical scrollbars
        self.txt_preview.WordWrap = False  # FIXED: Disable word wrap for proper horizontal scrolling
        self.txt_preview.Font = Font("Courier New", 9)  # Monospace font for better formatting
        self.txt_preview.Location = Point(10, 225)
        self.txt_preview.Size = Size(760, 300)
        self.txt_preview.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
        self.Controls.Add(self.txt_preview)
        
        # Buttons: standard OK/Cancel plus an 'Apply to All Events' checkbox
        btn_ok = Button()
        btn_ok.Text = "OK"
        btn_ok.DialogResult = DialogResult.OK
        btn_ok.Location = Point(600, 533)
        btn_ok.Size = Size(75, 25)
        btn_ok.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        self.Controls.Add(btn_ok)

        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.DialogResult = DialogResult.Cancel
        btn_cancel.Location = Point(685, 533)
        btn_cancel.Size = Size(75, 25)
        btn_cancel.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        self.Controls.Add(btn_cancel)

        # Checkbox to indicate whether the chosen template should be applied to all events
        self.chk_apply_all = CheckBox()
        self.chk_apply_all.Text = "Apply to All Events"
        self.chk_apply_all.Location = Point(350, 533)
        self.chk_apply_all.Size = Size(200, 24)
        self.chk_apply_all.Checked = False
        self.chk_apply_all.CheckedChanged += lambda s, e: setattr(self, 'apply_for_all', s.Checked)
        self.Controls.Add(self.chk_apply_all)

        # Checkbox to request a single combined sequence file instead of separate files
        self.chk_create_combined = CheckBox()
        self.chk_create_combined.Text = "Create single combined sequence"
        self.chk_create_combined.Location = Point(350, 560)
        self.chk_create_combined.Size = Size(240, 24)
        self.chk_create_combined.Checked = False
        self.chk_create_combined.CheckedChanged += lambda s, e: setattr(self, 'create_combined', s.Checked)
        self.Controls.Add(self.chk_create_combined)

        # Wire events
        self.lst_templates.SelectedIndexChanged += self.template_selected

        # Default: do not apply to all unless user checks the box
        self.apply_for_all = False

        self.AcceptButton = btn_ok
        self.CancelButton = btn_cancel
    
    def load_templates(self):
        """Load available templates into the list"""
        template_files, template_folder = TemplateManager.find_template_files(self.config.get_file_folder())
        
        # Add default option
        self.lst_templates.Items.Add("Default Template")
        
        # Add template files
        for template_file in template_files:
            template_path = os.path.join(template_folder, template_file)
            size, mtime = TemplateManager.get_template_info(template_path)
            display_text = f"{template_file} ({size} bytes, {mtime.strftime('%Y-%m-%d %H:%M')})"
            self.lst_templates.Items.Add(display_text)
        
        # Select first item
        if self.lst_templates.Items.Count > 0:
            self.lst_templates.SelectedIndex = 0
    
    def template_selected(self, sender, e):
        """Handle template selection change with proper preview"""
        if self.lst_templates.SelectedIndex >= 0:
            if self.lst_templates.SelectedIndex == 0:
                # Default template
                self.selected_template_path = ""
                template_content = TemplateManager.load_template("", self.config)
            else:
                # Specific template file
                template_files, template_folder = TemplateManager.find_template_files(self.config.get_file_folder())
                if self.lst_templates.SelectedIndex - 1 < len(template_files):
                    template_file = template_files[self.lst_templates.SelectedIndex - 1]
                    self.selected_template_path = os.path.join(template_folder, template_file)
                    template_content = TemplateManager.load_template(self.selected_template_path, self.config)
            
            # Show preview with proper line breaks - FIXED
            if template_content:
                # Don't truncate, let scrollbars handle the content
                self.txt_preview.Text = template_content.replace('\n','\r\n')
            else:
                self.txt_preview.Text = "Could not load template content"
    
    def get_selected_template_path(self):
        """Get the selected template path"""
        return self.selected_template_path
    