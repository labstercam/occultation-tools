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
    CheckBox, FolderBrowserDialog, DockStyle, ToolTip, ComboBox, ComboBoxStyle
)
from theme import apply_theme_to_control
from templates import TemplateManager

def _detect_scale_factor():
    """Detect current display DPI and return scale factor.
    
    Returns:
        float: Scale factor (1.0 for 100%, 1.25 for 125%, 1.5 for 150%)
    """
    try:
        from System.Drawing import Graphics, Bitmap
        # Use a temporary form to get DPI
        temp_form = Form()
        try:
            temp_form.CreateControl()
            g = Graphics.FromHwnd(temp_form.Handle)
            try:
                dpi = float(g.DpiX)
            finally:
                g.Dispose()
        finally:
            temp_form.Dispose()
        
        return dpi / 96.0
    except Exception:
        return 1.0

def _autosize_button(btn, sf, padding=None, min_width=None, height=None):
    """Auto-size button to fit text content with DPI scaling.
    
    Args:
        btn: Button control to size
        sf: Scale factor
        padding: Horizontal padding (default: 20 * sf)
        min_width: Minimum width (default: 60 * sf)
        height: Button height (default: 25 * sf)
    """
    try:
        from System.Drawing import Bitmap, Graphics
        
        if padding is None:
            padding = int(round(20 * sf))
        if min_width is None:
            min_width = int(round(60 * sf))
        if height is None:
            height = int(round(25 * sf))
        
        # Measure text width
        bmp = Bitmap(1, 1)
        g = Graphics.FromImage(bmp)
        try:
            sizef = g.MeasureString(btn.Text or "", btn.Font)
            measured = int(sizef.Width)
        finally:
            g.Dispose()
            bmp.Dispose()
        
        width = max(measured + padding, min_width)
        btn.Size = Size(width, height)
    except Exception:
        # Fallback to scaled default if measurement fails
        btn.Size = Size(int(round(75 * sf)), int(round(25 * sf)))

class ExposureEditDialog(Form):
    """Dialog for editing event exposure - DPI-aware version"""
    
    def __init__(self, event, theme_manager):
        Form.__init__(self)
        self.event = event
        self.theme_manager = theme_manager
        self.new_exposure_ms = event.exposure_ms
        self._sf = _detect_scale_factor()
        self.setup_ui()
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup exposure edit dialog UI with DPI scaling"""
        sf = self._sf
        
        self.Text = f"Edit Exposure - {self.event.event_name}"
        self.Size = Size(int(450 * sf), int(330 * sf))
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        # Event info
        lbl_event = Label()
        lbl_event.Text = f"Event: {self.event.event_name}"
        lbl_event.Location = Point(int(20 * sf), int(20 * sf))
        lbl_event.Size = Size(int(350 * sf), int(20 * sf))
        lbl_event.Font = Font("Microsoft Sans Serif", 9 * sf, FontStyle.Bold)
        self.Controls.Add(lbl_event)
        
        lbl_star = Label()
        lbl_star.Text = f"Mag: {self.event.star_mag:.1f}, Mag Drop: {self.event.mag_drop:.1f}, Max Dur: {self.event.max_duration_seconds:.1f}s"
        lbl_star.Location = Point(int(20 * sf), int(45 * sf))
        lbl_star.Size = Size(int(350 * sf), int(20 * sf))
        self.Controls.Add(lbl_star)
        
        lbl_current = Label()
        current_text = f"Current Exposure: {self.event.exposure_ms} ms"
        if self.event.has_custom_exposure():
            current_text += " (Custom)"
        else:
            current_text += " (Calculated)"
        lbl_current.Text = current_text
        lbl_current.Location = Point(int(20 * sf), int(80 * sf))
        lbl_current.Size = Size(int(350 * sf), int(20 * sf))
        self.Controls.Add(lbl_current)
        
        # Exposure input
        lbl_new_exposure = Label()
        lbl_new_exposure.Text = "New Exposure (ms):"
        lbl_new_exposure.Location = Point(int(20 * sf), int(105 * sf))
        lbl_new_exposure.Size = Size(int(120 * sf), int(20 * sf))
        self.Controls.Add(lbl_new_exposure)
        
        self.txt_exposure = TextBox()
        self.txt_exposure.Text = str(self.event.exposure_ms)
        self.txt_exposure.Location = Point(int(150 * sf), int(105 * sf))
        self.txt_exposure.Size = Size(int(100 * sf), int(20 * sf))
        self.Controls.Add(self.txt_exposure)
        
        # Quick exposure buttons
        lbl_quick = Label()
        lbl_quick.Text = "Quick Settings:"
        lbl_quick.Location = Point(int(20 * sf), int(130 * sf))
        lbl_quick.Size = Size(int(100 * sf), int(20 * sf))
        self.Controls.Add(lbl_quick)
        
        quick_exposures = [40, 60, 80, 120, 160, 240, 320, 480]
        x_pos = int(20 * sf)
        y_pos = int(155 * sf)
        gap = int(6 * sf)
        
        for i, exp in enumerate(quick_exposures):
            btn = Button()
            btn.Text = f"{exp}"
            btn.Location = Point(x_pos, y_pos)
            _autosize_button(btn, sf, padding=int(12 * sf), min_width=int(45 * sf))
            btn.Tag = exp
            btn.Click += self.quick_exposure_click
            self.Controls.Add(btn)
            
            x_pos += btn.Width + gap
            if (i + 1) % 4 == 0:
                x_pos = int(20 * sf)
                y_pos += int(30 * sf)
        
        # Calculate button row Y position dynamically
        button_y = y_pos + int(15 * sf)
        
        # Buttons - position them relative to form width
        btn_reset = Button()
        btn_reset.Text = "Reset to Calculated"
        _autosize_button(btn_reset, sf, min_width=int(120 * sf))
        btn_reset.Location = Point(int(20 * sf), button_y)
        btn_reset.Click += self.reset_click
        self.Controls.Add(btn_reset)
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.DialogResult = DialogResult.Cancel
        _autosize_button(btn_cancel, sf, min_width=int(60 * sf))
        # Position from right edge
        btn_cancel.Location = Point(int(self.ClientSize.Width - btn_cancel.Width - 20 * sf), button_y)
        self.Controls.Add(btn_cancel)
        
        btn_ok = Button()
        btn_ok.Text = "OK"
        btn_ok.DialogResult = DialogResult.OK
        _autosize_button(btn_ok, sf, min_width=int(60 * sf))
        # Position to left of Cancel button
        btn_ok.Location = Point(int(btn_cancel.Location.X - btn_ok.Width - 10 * sf), button_y)
        btn_ok.Click += self.ok_click
        self.Controls.Add(btn_ok)
        
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
    """Dialog for displaying detailed event information with DPI scaling"""
    
    def __init__(self, event, theme_manager):
        Form.__init__(self)
        self.event = event
        self.theme_manager = theme_manager
        self._sf = _detect_scale_factor()
        self.setup_ui()
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup event details dialog UI with DPI scaling"""
        sf = self._sf
        
        self.Text = f"Event Details - {self.event.get_asteroid_display_name()}"
        self.Size = Size(int(650 * sf), int(700 * sf))
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.MaximizeBox = True
        self.MinimizeBox = True
        
        # Create main panel with scroll capability
        main_panel = Panel()
        main_panel.Dock = DockStyle.Fill
        main_panel.AutoScroll = True
        self.Controls.Add(main_panel)
        
        y_pos = int(20 * sf)
        
        # Event Information Group
        grp_event = GroupBox()
        grp_event.Text = "Event Information"
        grp_event.Location = Point(int(10 * sf), y_pos)
        grp_event.Size = Size(int(560 * sf), int(120 * sf))
        main_panel.Controls.Add(grp_event)
        
        y_pos += int(130 * sf)
        
        self.add_detail_label(grp_event, "Event Name:", self.event.event_name, 10, 25)
        self.add_detail_label(grp_event, "Asteroid:", self.event.get_asteroid_display_name(), 10, 50)
        self.add_detail_label(grp_event, "Star:", f"{self.event.star_name} (ID: {self.event.star_id})", 10, 75)
        self.add_detail_label(grp_event, "Station:", self.event.station_name, 300, 25)
        self.add_detail_label(grp_event, "Source:", self.event.source, 300, 50)
        
        # Add OWC link if available
        if hasattr(self.event, 'owcloudurl') and self.event.owcloudurl:
            link_label = LinkLabel()
            link_label.Text = "View on OWC"
            link_label.Location = Point(int(300 * sf), int(75 * sf))
            link_label.Size = Size(int(100 * sf), int(20 * sf))
            link_label.LinkClicked += lambda s, e: webbrowser.open(self.event.owcloudurl)
            grp_event.Controls.Add(link_label)
        
        # Timing Information Group
        grp_timing = GroupBox()
        grp_timing.Text = "Timing Information"
        grp_timing.Location = Point(int(10 * sf), y_pos)
        grp_timing.Size = Size(int(560 * sf), int(120 * sf))
        main_panel.Controls.Add(grp_timing)
        
        y_pos += int(130 * sf)

        self.add_detail_label(grp_timing, "Event Time (UTC):", self.event.event_time, 10, 25)
        self.add_detail_label(grp_timing, "GOTO Time (UTC):", self.event.goto_time_str, 10, 50)
        self.add_detail_label(grp_timing, "Start Time (UTC):", self.event.start_time_str, 10, 75)
        self.add_detail_label(grp_timing, "End Time (UTC):", self.event.end_time_str, 300, 25)
        self.add_detail_label(grp_timing, "Max Duration:", f"{self.event.max_duration_seconds:.1f} seconds", 300, 50)
        self.add_detail_label(grp_timing, "Time Error:", f"{self.event.uncertainty_seconds:.1f} seconds", 300, 75)
        
        # Recording Settings Group
        grp_recording = GroupBox()
        grp_recording.Text = "Recording Settings"
        grp_recording.Location = Point(int(10 * sf), y_pos)
        grp_recording.Size = Size(int(560 * sf), int(120 * sf))
        main_panel.Controls.Add(grp_recording)
        
        y_pos += int(130 * sf)
        
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
        grp_photometry.Location = Point(int(10 * sf), y_pos)
        grp_photometry.Size = Size(int(560 * sf), int(120 * sf))
        main_panel.Controls.Add(grp_photometry)
        
        y_pos += int(130 * sf)
        
        self.add_detail_label(grp_photometry, "Star Magnitude:", f"{self.event.star_mag:.1f}", 10, 25)
        self.add_detail_label(grp_photometry, "Combined Magnitude:", f"{self.event.comb_mag:.1f}", 10, 50)
        self.add_detail_label(grp_photometry, "Magnitude Drop:", f"{self.event.mag_drop:.1f}", 10, 75)
        
        # Position Information Group
        grp_position = GroupBox()
        grp_position.Text = "Position Information"
        grp_position.Location = Point(int(10 * sf), y_pos)
        grp_position.Size = Size(int(560 * sf), int(120 * sf))
        main_panel.Controls.Add(grp_position)
        
        y_pos += int(130 * sf)
        
        self.add_detail_label(grp_position, "RA (J2000):", f"{self.event.ra:.6f} hours", 10, 25)
        self.add_detail_label(grp_position, "Dec (J2000):", f"{self.event.dec:.6f}°", 10, 50)
        self.add_detail_label(grp_position, "Altitude:", f"{self.event.star_alt:.1f}°", 300, 25)
        self.add_detail_label(grp_position, "Azimuth:", f"{self.event.star_az:.1f}°", 300, 50)
        
        # Observer Location Group
        grp_location = GroupBox()
        grp_location.Text = "Observer Location"
        grp_location.Location = Point(int(10 * sf), y_pos)
        grp_location.Size = Size(int(560 * sf), int(95 * sf))
        main_panel.Controls.Add(grp_location)
        
        y_pos += int(105 * sf)
        
        self.add_detail_label(grp_location, "Latitude:", f"{self.event.latitude:.6f}°", 10, 25)
        self.add_detail_label(grp_location, "Longitude:", f"{self.event.longitude:.6f}°", 10, 50)
        
        # Technical Information Group
        grp_technical = GroupBox()
        grp_technical.Text = "Technical Information"
        grp_technical.Location = Point(int(10 * sf), y_pos)
        grp_technical.Size = Size(int(560 * sf), int(95 * sf))
        main_panel.Controls.Add(grp_technical)
        
        y_pos += int(105 * sf)
        
        self.add_detail_label(grp_technical, "Event ID:", self.event.event_id, 10, 25)
        self.add_detail_label(grp_technical, "OW Event ID:", str(self.event.ow_eventid), 10, 50)
        self.add_detail_label(grp_technical, "Object Number:", self.event.object_no, 300, 25)
        
        # Close button
        btn_close = Button()
        btn_close.Text = "Close"
        btn_close.DialogResult = DialogResult.OK
        btn_close.Location = Point(int(500 * sf), y_pos + int(20 * sf))
        _autosize_button(btn_close, sf)
        main_panel.Controls.Add(btn_close)
        
        self.AcceptButton = btn_close
    
    def add_detail_label(self, parent, label_text, value_text, x, y):
        """Helper to add label-value pairs with DPI scaling"""
        sf = self._sf
        lbl_name = Label()
        lbl_name.Text = label_text
        lbl_name.Location = Point(int(x * sf), int(y * sf))
        lbl_name.Size = Size(int(120 * sf), int(20 * sf))
        lbl_name.Font = Font("Microsoft Sans Serif", 8 * sf, FontStyle.Bold)
        parent.Controls.Add(lbl_name)
        
        lbl_value = Label()
        lbl_value.Text = str(value_text) if value_text is not None else "N/A"
        lbl_value.Location = Point(int((x + 125) * sf), int(y * sf))
        lbl_value.Size = Size(int(150 * sf), int(20 * sf))
        lbl_value.Font = Font("Microsoft Sans Serif", 8 * sf)
        parent.Controls.Add(lbl_value)

class ConfigurationDialog(Form):
    """Configuration dialog for GUI with DPI scaling"""
    
    def __init__(self, config, theme_manager):
        Form.__init__(self)
        self.config = config
        self.theme_manager = theme_manager
        self._sf = _detect_scale_factor()
        
        # Create ToolTip component for the entire dialog
        self.tooltip = ToolTip()
        self.tooltip.AutoPopDelay = 5000
        self.tooltip.InitialDelay = 500
        self.tooltip.ReshowDelay = 200
        self.tooltip.ShowAlways = True
        
        self.setup_ui()
        self.load_current_config()
        # Snapshot key config values so we can detect changes that
        # require re-processing of OWC events (goto lead, base duration,
        # and mag reference for 40ms exposure).
        try:
            self._orig_goto_lead = self.config.get_goto_lead_time()
        except Exception:
            self._orig_goto_lead = None
        try:
            self._orig_base_duration = self.config.get_base_duration()
        except Exception:
            self._orig_base_duration = None
        try:
            self._orig_mag_ref = self.config.get_mag_for_40ms_exposure()
        except Exception:
            self._orig_mag_ref = None
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup configuration dialog UI with DPI scaling"""
        sf = self._sf
        
        self.Text = "Configuration Settings"
        self.Size = Size(int(600 * sf), int(700 * sf))
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        # Create tabs
        tab_control = TabControl()
        tab_control.Location = Point(int(10 * sf), int(10 * sf))
        tab_control.Size = Size(int(560 * sf), int(600 * sf))
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
        tab_recording.Text = "User Settings"
        self.setup_recording_tab(tab_recording)
        tab_control.TabPages.Add(tab_recording)
        
        # Observer/Telescope Tab
        tab_observer = TabPage()
        tab_observer.Text = "Observer/Telescope"
        self.setup_observer_telescope_tab(tab_observer)
        tab_control.TabPages.Add(tab_observer)
        
        # API Settings Tab
        tab_api = TabPage()
        tab_api.Text = "API Settings"
        #self.setup_api_tab(tab_api)
        self.setup_api_tab(tab_credentials)
        
        #tab_control.TabPages.Add(tab_api)
        
        # Buttons
        btn_ok = Button()
        btn_ok.Text = "Save"
        btn_ok.DialogResult = DialogResult.OK
        btn_ok.Location = Point(int(350 * sf), int(630 * sf))
        _autosize_button(btn_ok, sf)
        btn_ok.Click += self.save_config_click
        self.Controls.Add(btn_ok)
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.DialogResult = DialogResult.Cancel
        btn_cancel.Location = Point(int(435 * sf), int(630 * sf))
        _autosize_button(btn_cancel, sf)
        self.Controls.Add(btn_cancel)
        
        btn_reset = Button()
        btn_reset.Text = "Reset to Defaults"
        btn_reset.Location = Point(int(10 * sf), int(630 * sf))
        _autosize_button(btn_reset, sf, min_width=int(140 * sf))
        btn_reset.Click += self.reset_defaults_click
        self.Controls.Add(btn_reset)
        
        self.AcceptButton = btn_ok
        self.CancelButton = btn_cancel
    
    def setup_credentials_tab(self, tab):
        """Setup credentials tab with DPI scaling"""
        sf = self._sf
        
        # Credentials fields at top with even spacing
        lbl_email = Label()
        lbl_email.Text = "OWC Email:"
        lbl_email.Location = Point(int(20 * sf), int(20 * sf))
        lbl_email.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(lbl_email)
        
        self.txt_email = TextBox()
        self.txt_email.Location = Point(int(130 * sf), int(20 * sf))
        self.txt_email.Size = Size(int(300 * sf), int(20 * sf))
        tab.Controls.Add(self.txt_email)
        self.tooltip.SetToolTip(self.txt_email, "Your Occult Watcher Cloud account email address")
        
        lbl_password = Label()
        lbl_password.Text = "OWC Password:"
        lbl_password.Location = Point(int(20 * sf), int(60 * sf))
        lbl_password.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(lbl_password)
        
        self.txt_password = TextBox()
        self.txt_password.Location = Point(int(130 * sf), int(60 * sf))
        self.txt_password.Size = Size(int(300 * sf), int(20 * sf))
        self.txt_password.UseSystemPasswordChar = True
        tab.Controls.Add(self.txt_password)
        self.tooltip.SetToolTip(self.txt_password, "Your Occult Watcher Cloud account password")
        
        # Information Panel at bottom (after API fields are added)
        info_panel = GroupBox()
        info_panel.Text = "How to Get Your OWC Credentials"
        info_panel.Location = Point(int(20 * sf), int(190 * sf))
        info_panel.Size = Size(int(500 * sf), int(140 * sf))
        tab.Controls.Add(info_panel)
        
        info_text = Label()
        info_text.Text = ("1. Create an account or log in at Occult Watcher Cloud\n"
                         "2. Go to your User Profile page (link below)\n"
                         "3. Click on the 'Permissions & Settings' sub-tab\n"
                         "4. Find or generate your API Key in that section\n"
                         "5. Copy your email and API Key to the fields above")
        info_text.Location = Point(int(10 * sf), int(20 * sf))
        info_text.Size = Size(int(480 * sf), int(80 * sf))
        info_text.AutoSize = False
        info_panel.Controls.Add(info_text)
        
        # Clickable link to user profile
        link_profile = LinkLabel()
        link_profile.Text = "Open OWC User Profile →"
        link_profile.Location = Point(int(10 * sf), int(105 * sf))
        link_profile.AutoSize = True
        link_profile.LinkClicked += self.open_owc_profile
        info_panel.Controls.Add(link_profile)
        self.tooltip.SetToolTip(link_profile, "Opens https://cloud.occultwatcher.net/user-profile in your browser")
    
    def open_owc_profile(self, sender, e):
        """Open OWC user profile page in browser"""
        try:
            webbrowser.open("https://cloud.occultwatcher.net/user-profile")
        except Exception as ex:
            MessageBox.Show(f"Could not open browser: {ex}", "Error", 
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
    
    def setup_paths_tab(self, tab):
        """Setup file paths tab with DPI scaling"""
        sf = self._sf
        
        # All file paths fields at top with even spacing
        lbl_file_folder = Label()
        lbl_file_folder.Text = "File Folder:"
        lbl_file_folder.Location = Point(int(20 * sf), int(20 * sf))
        lbl_file_folder.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(lbl_file_folder)
        
        self.txt_file_folder = TextBox()
        self.txt_file_folder.Location = Point(int(130 * sf), int(20 * sf))
        self.txt_file_folder.Size = Size(int(250 * sf), int(20 * sf))
        tab.Controls.Add(self.txt_file_folder)
        self.tooltip.SetToolTip(self.txt_file_folder, "Folder where downloaded occultation data files are stored")
        
        btn_browse_folder = Button()
        btn_browse_folder.Text = "Browse"
        btn_browse_folder.Location = Point(int(390 * sf), int(19 * sf))
        _autosize_button(btn_browse_folder, sf, height=int(22 * sf))
        btn_browse_folder.Click += self.browse_file_folder_click
        tab.Controls.Add(btn_browse_folder)
        self.tooltip.SetToolTip(btn_browse_folder, "Browse for file folder location")
        
        lbl_sequence_path = Label()
        lbl_sequence_path.Text = "Sequence Path:"
        lbl_sequence_path.Location = Point(int(20 * sf), int(60 * sf))
        lbl_sequence_path.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(lbl_sequence_path)
        
        self.txt_sequence_path = TextBox()
        self.txt_sequence_path.Location = Point(int(130 * sf), int(60 * sf))
        self.txt_sequence_path.Size = Size(int(250 * sf), int(20 * sf))
        tab.Controls.Add(self.txt_sequence_path)
        self.tooltip.SetToolTip(self.txt_sequence_path, "Folder where generated SharpCap sequence files (.scs) are saved")
        
        btn_browse_sequence = Button()
        btn_browse_sequence.Text = "Browse"
        btn_browse_sequence.Location = Point(int(390 * sf), int(59 * sf))
        _autosize_button(btn_browse_sequence, sf, height=int(22 * sf))
        btn_browse_sequence.Click += self.browse_sequence_path_click
        tab.Controls.Add(btn_browse_sequence)
        self.tooltip.SetToolTip(btn_browse_sequence, "Browse for sequence file location")
        
        lbl_occ_file = Label()
        lbl_occ_file.Text = "Occultations File:"
        lbl_occ_file.Location = Point(int(20 * sf), int(100 * sf))
        lbl_occ_file.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(lbl_occ_file)
        
        self.txt_occ_file = TextBox()
        self.txt_occ_file.Location = Point(int(130 * sf), int(100 * sf))
        self.txt_occ_file.Size = Size(int(300 * sf), int(20 * sf))
        tab.Controls.Add(self.txt_occ_file)
        self.tooltip.SetToolTip(self.txt_occ_file, "Filename for the main occultation events data file (merged with downloads, 14-day retention)")
        
        lbl_latest_file = Label()
        lbl_latest_file.Text = "Latest File:"
        lbl_latest_file.Location = Point(int(20 * sf), int(140 * sf))
        lbl_latest_file.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(lbl_latest_file)
        
        self.txt_latest_file = TextBox()
        self.txt_latest_file.Location = Point(int(130 * sf), int(140 * sf))
        self.txt_latest_file.Size = Size(int(300 * sf), int(20 * sf))
        tab.Controls.Add(self.txt_latest_file)
        self.tooltip.SetToolTip(self.txt_latest_file, "Filename for storing the latest downloaded occultation events (replaced on each download)")
        
        # Information Panel at bottom
        info_panel = GroupBox()
        info_panel.Text = "How Download from OWC Works"
        info_panel.Location = Point(int(20 * sf), int(190 * sf))
        info_panel.Size = Size(int(500 * sf), int(140 * sf))
        tab.Controls.Add(info_panel)
        
        info_text = Label()
        info_text.Text = ("When you click 'Download Events', the application:\n"
                         "1. Reads your 'Upcoming Events' from OWC (link below)\n"
                         "2. Saves the downloaded events to 'Latest File'\n"
                         "3. Merges with existing 'Occultations File'\n"
                         "4. Retains only events no more than 14 days old")
        info_text.Location = Point(int(10 * sf), int(20 * sf))
        info_text.Size = Size(int(480 * sf), int(80 * sf))
        info_text.AutoSize = False
        info_panel.Controls.Add(info_text)
        
        # Clickable link to my events
        link_events = LinkLabel()
        link_events.Text = "Open My Events on OWC →"
        link_events.Location = Point(int(10 * sf), int(105 * sf))
        link_events.AutoSize = True
        link_events.LinkClicked += self.open_owc_events
        info_panel.Controls.Add(link_events)
        self.tooltip.SetToolTip(link_events, "Opens https://cloud.occultwatcher.net/my-events in your browser")
    
    def open_owc_events(self, sender, e):
        """Open OWC my events page in browser"""
        try:
            webbrowser.open("https://cloud.occultwatcher.net/my-events")
        except Exception as ex:
            MessageBox.Show(f"Could not open browser: {ex}", "Error", 
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
    
    def setup_recording_tab(self, tab):
        """Setup recording settings tab with DPI scaling"""
        sf = self._sf
        
        # Settings fields at top
        lbl_base_duration = Label()
        lbl_base_duration.Text = "Base Duration (s):"
        lbl_base_duration.Location = Point(int(20 * sf), int(20 * sf))
        lbl_base_duration.Size = Size(int(120 * sf), int(20 * sf))
        tab.Controls.Add(lbl_base_duration)
        
        self.txt_base_duration = TextBox()
        self.txt_base_duration.Location = Point(int(150 * sf), int(20 * sf))
        self.txt_base_duration.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(self.txt_base_duration)
        self.tooltip.SetToolTip(self.txt_base_duration, "Base recording duration in seconds. Additional time is added based on event duration and uncertainty")
        
        lbl_goto_lead = Label()
        lbl_goto_lead.Text = "GOTO Lead Time (s):"
        lbl_goto_lead.Location = Point(int(20 * sf), int(50 * sf))
        lbl_goto_lead.Size = Size(int(120 * sf), int(20 * sf))
        tab.Controls.Add(lbl_goto_lead)
        
        self.txt_goto_lead = TextBox()
        self.txt_goto_lead.Location = Point(int(150 * sf), int(50 * sf))
        self.txt_goto_lead.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(self.txt_goto_lead)
        self.tooltip.SetToolTip(self.txt_goto_lead, "How many seconds before the start of recording to begin the GOTO slew to the target position")
        
        lbl_mag_exposure = Label()
        lbl_mag_exposure.Text = "Mag for 40 ms exp:"
        lbl_mag_exposure.Location = Point(int(20 * sf), int(80 * sf))
        lbl_mag_exposure.Size = Size(int(120 * sf), int(20 * sf))
        tab.Controls.Add(lbl_mag_exposure)
        
        self.txt_mag_exposure = TextBox()
        self.txt_mag_exposure.Location = Point(int(150 * sf), int(80 * sf))
        self.txt_mag_exposure.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(self.txt_mag_exposure)
        self.tooltip.SetToolTip(self.txt_mag_exposure, "Reference star magnitude that requires 40 ms exposure. Used to calculate appropriate exposure times for stars of different magnitudes")

        self.chk_sync_mount = CheckBox()
        self.chk_sync_mount.Text = "Sync Mount with GOTO"       
        self.chk_sync_mount.Location = Point(int(20 * sf), int(110 * sf))
        self.chk_sync_mount.Size = Size(int(200 * sf), int(20 * sf))    
        tab.Controls.Add(self.chk_sync_mount)
        self.tooltip.SetToolTip(self.chk_sync_mount, "⚠ WARNING: Only enable if you usually SYNC your mount with every GOTO. Do NOT use with permanently aligned or precision aligned mounts!")

        self.chk_sync_mount.Checked = self.config.get_sync_mount()
        self.chk_sync_mount.CheckedChanged += self.sync_mount_checked_changed

        self.display_utc = CheckBox()
        self.display_utc.Text = "Display UTC in Grid"       
        self.display_utc.Location = Point(int(20 * sf), int(140 * sf))
        self.display_utc.Size = Size(int(200 * sf), int(20 * sf))    
        tab.Controls.Add(self.display_utc)
        self.tooltip.SetToolTip(self.display_utc, "Display event times in UTC (Coordinated Universal Time) in the main grid. When unchecked, times are shown in local time")

        self.display_utc.Checked = self.config.get_display_utc()
        self.display_utc.CheckedChanged += self.display_utc_checked_changed
        
        # Information Panel at bottom
        info_panel = GroupBox()
        info_panel.Text = "Understanding These Settings"
        info_panel.Location = Point(int(20 * sf), int(180 * sf))
        info_panel.Size = Size(int(500 * sf), int(400 * sf))
        tab.Controls.Add(info_panel)
        
        info_text = Label()
        info_text.Text = ("Recording Duration Formula:\n"
                         "  Duration = Base Duration + Event Duration (if >5 s) + 6 × Uncertainty (if >2 s)\n"
                         "    Example 1. Base Duration 60 s,  Event Duration 1.2 s, Uncertainty 1 s → 60s total\n"
                         "    Example 2. Base Duration 60 s,  Event Duration 6 s, Uncertainty 3 s  → 60 + 6 + 18 = 84s\n"
                         "In plain English: Start with the base duration,\n"
                         "and add the event duration if it's more than 5 seconds,\n"
                         "and add 6 times the uncertainty if it's more than 2 s to ensure full event coverage.\n\n"
                         "Exposure Time Formula:\n"
                         "  Exposure = 40 ms × 2^(CombMag + Extinction - MagRef)\n"
                         "  Adjusted for atmospheric extinction based on star altitude\n"
                         " In plain English: For every magnitude the star is dimmer than the reference magnitude,\n"
                         " the exposure time doubles. \n"
                         " MagRef: The star magnitude where you would usually use 40 ms exposure\n"
                         "    Example. MagRef 10.0, CombMag 12.0, Extinction 0.3 → 40 × 2^(12.0 + 0.3 - 10.0), rounded to 40 × 2^(2) = 160 ms\n"
                         "40 ms is the minimum exposure that will be automatically set.\n"
                         "Values set by doubling are 80 ms, 160 ms, 320 ms etc.\n"
                         "You can manually set a custom exposure per event if desired.\n\n"
                         "⚠ Sync Mount Warning:\n"
                         "Only enable 'Sync Mount' if you usually Sync the mount with each GOTO.\n"
                         "Do NOT sync if: Have a permanently aligned mount or use a refined pointing model.\n"
                         "Syncing could adversely affect your carefully calibrated pointing model!")
        info_text.Location = Point(int(10 * sf), int(20 * sf))
        info_text.Size = Size(int(480 * sf), int(370 * sf))
        info_text.AutoSize = False
        info_panel.Controls.Add(info_text)
    
    def sync_mount_checked_changed(self, sender, e):
        """Handle sync mount checkbox change"""
        self.config.set_sync_mount(self.chk_sync_mount.Checked) 

    def display_utc_checked_changed(self, sender, e):
        """Handle UTC diplay checkbox change"""
        self.config.set_display_utc(self.display_utc.Checked)
        # If this dialog was opened with an owner (main GUI), refresh the
        # events display immediately so the grid updates to UTC/local view.
        try:
            owner = getattr(self, 'Owner', None)
            if owner and hasattr(owner, 'refresh_display'):
                owner.refresh_display()
        except Exception:
            # Defensive: do not raise from UI handler
            pass


    def setup_api_tab(self, tab):
        """Setup API settings tab with DPI scaling"""
        sf = self._sf
        
        lbl_host = Label()
        lbl_host.Text = "API Host:"
        lbl_host.Location = Point(int(20 * sf), int(100 * sf))
        lbl_host.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(lbl_host)
        
        self.txt_host = TextBox()
        self.txt_host.Location = Point(int(130 * sf), int(100 * sf))
        self.txt_host.Size = Size(int(300 * sf), int(20 * sf))
        tab.Controls.Add(self.txt_host)
        self.tooltip.SetToolTip(self.txt_host, "API server hostname or URL for custom occultation data sources")
        
        lbl_api_key = Label()
        lbl_api_key.Text = "API Key:"
        lbl_api_key.Location = Point(int(20 * sf), int(140 * sf))
        lbl_api_key.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(lbl_api_key)
        
        self.txt_api_key = TextBox()
        self.txt_api_key.Location = Point(int(130 * sf), int(140 * sf))
        self.txt_api_key.Size = Size(int(300 * sf), int(20 * sf))
        tab.Controls.Add(self.txt_api_key)
        self.tooltip.SetToolTip(self.txt_api_key, "API authentication key for accessing custom occultation data sources")
    
    def setup_observer_telescope_tab(self, tab):
        """Setup observer and telescope configuration tab with DPI scaling"""
        sf = self._sf
        
        # Observer Section
        observer_group = GroupBox()
        observer_group.Text = "Observer Information"
        observer_group.Location = Point(int(20 * sf), int(10 * sf))
        observer_group.Size = Size(int(500 * sf), int(290 * sf))
        tab.Controls.Add(observer_group)
        
        lbl_observer_name = Label()
        lbl_observer_name.Text = "Name:"
        lbl_observer_name.Location = Point(int(20 * sf), int(30 * sf))
        lbl_observer_name.Size = Size(int(100 * sf), int(20 * sf))
        observer_group.Controls.Add(lbl_observer_name)
        
        self.txt_observer_name = TextBox()
        self.txt_observer_name.Location = Point(int(130 * sf), int(30 * sf))
        self.txt_observer_name.Size = Size(int(340 * sf), int(20 * sf))
        observer_group.Controls.Add(self.txt_observer_name)
        self.tooltip.SetToolTip(self.txt_observer_name, "Your full name as it will appear on reports")
        
        lbl_observer_email = Label()
        lbl_observer_email.Text = "Email:"
        lbl_observer_email.Location = Point(int(20 * sf), int(60 * sf))
        lbl_observer_email.Size = Size(int(100 * sf), int(20 * sf))
        observer_group.Controls.Add(lbl_observer_email)
        
        self.txt_observer_email = TextBox()
        self.txt_observer_email.Location = Point(int(130 * sf), int(60 * sf))
        self.txt_observer_email.Size = Size(int(340 * sf), int(20 * sf))
        observer_group.Controls.Add(self.txt_observer_email)
        self.tooltip.SetToolTip(self.txt_observer_email, "Your email address for report correspondence")
        
        lbl_observer_address = Label()
        lbl_observer_address.Text = "Address:"
        lbl_observer_address.Location = Point(int(20 * sf), int(90 * sf))
        lbl_observer_address.Size = Size(int(100 * sf), int(20 * sf))
        observer_group.Controls.Add(lbl_observer_address)
        
        self.txt_observer_address = TextBox()
        self.txt_observer_address.Location = Point(int(130 * sf), int(90 * sf))
        self.txt_observer_address.Size = Size(int(340 * sf), int(20 * sf))
        observer_group.Controls.Add(self.txt_observer_address)
        self.tooltip.SetToolTip(self.txt_observer_address, "Street address")
        
        lbl_observer_city = Label()
        lbl_observer_city.Text = "City:"
        lbl_observer_city.Location = Point(int(20 * sf), int(120 * sf))
        lbl_observer_city.Size = Size(int(100 * sf), int(20 * sf))
        observer_group.Controls.Add(lbl_observer_city)
        
        self.txt_observer_city = TextBox()
        self.txt_observer_city.Location = Point(int(130 * sf), int(120 * sf))
        self.txt_observer_city.Size = Size(int(150 * sf), int(20 * sf))
        observer_group.Controls.Add(self.txt_observer_city)
        
        lbl_observer_state = Label()
        lbl_observer_state.Text = "State:"
        lbl_observer_state.Location = Point(int(290 * sf), int(120 * sf))
        lbl_observer_state.Size = Size(int(40 * sf), int(20 * sf))
        observer_group.Controls.Add(lbl_observer_state)
        
        self.txt_observer_state = TextBox()
        self.txt_observer_state.Location = Point(int(335 * sf), int(120 * sf))
        self.txt_observer_state.Size = Size(int(135 * sf), int(20 * sf))
        observer_group.Controls.Add(self.txt_observer_state)
        self.tooltip.SetToolTip(self.txt_observer_state, "e.g., GA, NSW")
        
        lbl_observer_country = Label()
        lbl_observer_country.Text = "Country:"
        lbl_observer_country.Location = Point(int(20 * sf), int(150 * sf))
        lbl_observer_country.Size = Size(int(100 * sf), int(20 * sf))
        observer_group.Controls.Add(lbl_observer_country)
        
        self.txt_observer_country = TextBox()
        self.txt_observer_country.Location = Point(int(130 * sf), int(150 * sf))
        self.txt_observer_country.Size = Size(int(150 * sf), int(20 * sf))
        observer_group.Controls.Add(self.txt_observer_country)
        
        lbl_observer_phone = Label()
        lbl_observer_phone.Text = "Phone:"
        lbl_observer_phone.Location = Point(int(20 * sf), int(180 * sf))
        lbl_observer_phone.Size = Size(int(100 * sf), int(20 * sf))
        observer_group.Controls.Add(lbl_observer_phone)
        
        self.txt_observer_phone = TextBox()
        self.txt_observer_phone.Location = Point(int(130 * sf), int(180 * sf))
        self.txt_observer_phone.Size = Size(int(200 * sf), int(20 * sf))
        observer_group.Controls.Add(self.txt_observer_phone)
        self.tooltip.SetToolTip(self.txt_observer_phone, "+1-404-555-1234")
        
        lbl_observer_fax = Label()
        lbl_observer_fax.Text = "Fax:"
        lbl_observer_fax.Location = Point(int(20 * sf), int(210 * sf))
        lbl_observer_fax.Size = Size(int(100 * sf), int(20 * sf))
        observer_group.Controls.Add(lbl_observer_fax)
        
        self.txt_observer_fax = TextBox()
        self.txt_observer_fax.Location = Point(int(130 * sf), int(210 * sf))
        self.txt_observer_fax.Size = Size(int(200 * sf), int(20 * sf))
        observer_group.Controls.Add(self.txt_observer_fax)
        self.tooltip.SetToolTip(self.txt_observer_fax, "Optional")
        
        lbl_note = Label()
        lbl_note.Text = "Location lat/lon will be requested from event station when generating reports"
        lbl_note.Location = Point(int(20 * sf), int(245 * sf))
        lbl_note.Size = Size(int(460 * sf), int(30 * sf))
        lbl_note.ForeColor = Color.Gray
        observer_group.Controls.Add(lbl_note)
        
        # Note about telescope management
        lbl_telescope_note = Label()
        lbl_telescope_note.Text = "Telescope and Camera information can be managed via the Tools menu:"
        lbl_telescope_note.Location = Point(int(20 * sf), int(310 * sf))
        lbl_telescope_note.Size = Size(int(480 * sf), int(20 * sf))
        tab.Controls.Add(lbl_telescope_note)
        
        lbl_telescope_menu = Label()
        lbl_telescope_menu.Text = "• Tools → Manage Telescopes\n• Tools → Manage Cameras"
        lbl_telescope_menu.Location = Point(int(40 * sf), int(335 * sf))
        lbl_telescope_menu.Size = Size(int(480 * sf), int(40 * sf))
        lbl_telescope_menu.ForeColor = Color.Gray
        tab.Controls.Add(lbl_telescope_menu)
        
        lbl_report_note = Label()
        lbl_report_note.Text = "This information will be used to auto-fill North American Occultation Report Forms"
        lbl_report_note.Location = Point(int(20 * sf), int(385 * sf))
        lbl_report_note.Size = Size(int(480 * sf), int(30 * sf))
        lbl_report_note.ForeColor = Color.Gray
        tab.Controls.Add(lbl_report_note)
    
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
        self.display_utc.Checked = self.config.get_display_utc()
        self.txt_host.Text = self.config.get_host()
        self.txt_api_key.Text = self.config.get_api_key()
        
        # Observer fields
        self.txt_observer_name.Text = self.config.get_observer_name()
        self.txt_observer_email.Text = self.config.get_observer_email()
        self.txt_observer_address.Text = self.config.get_observer_address()
        self.txt_observer_city.Text = self.config.get_observer_city()
        self.txt_observer_state.Text = self.config.get_observer_state()
        self.txt_observer_country.Text = self.config.get_observer_country()
        self.txt_observer_phone.Text = self.config.get_observer_phone()
        self.txt_observer_fax.Text = self.config.get_observer_fax()
    
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
            self.config.set_display_utc(self.display_utc.Checked)
            self.config.set_host(self.txt_host.Text)
            self.config.set_api_key(self.txt_api_key.Text)
            
            # Observer fields
            self.config.set_observer_name(self.txt_observer_name.Text)
            self.config.set_observer_email(self.txt_observer_email.Text)
            self.config.set_observer_address(self.txt_observer_address.Text)
            self.config.set_observer_city(self.txt_observer_city.Text)
            self.config.set_observer_state(self.txt_observer_state.Text)
            self.config.set_observer_country(self.txt_observer_country.Text)
            self.config.set_observer_phone(self.txt_observer_phone.Text)
            self.config.set_observer_fax(self.txt_observer_fax.Text)
            
            # Validate and save
            errors = self.config.validate_config()
            if errors:
                MessageBox.Show("Configuration errors:\n" + "\n".join(errors), 
                              "Configuration Error", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            if self.config.save_config():
                MessageBox.Show("Configuration saved successfully!", "Success", 
                              MessageBoxButtons.OK, MessageBoxIcon.Information)
                # Refresh owner UI immediately so changes (e.g., Display UTC)
                # take effect without closing the dialog.
                try:
                    owner = getattr(self, 'Owner', None)
                    if owner and hasattr(owner, 'refresh_display'):
                        owner.refresh_display()
                except Exception:
                    pass
                # If certain config values changed, reprocess the loaded OWC
                # events so recording duration, goto times and exposure are
                # recalculated according to the new settings.
                try:
                    new_goto = self.config.get_goto_lead_time()
                    new_base = self.config.get_base_duration()
                    new_mag = self.config.get_mag_for_40ms_exposure()
                    changed = (
                        (self._orig_goto_lead is not None and new_goto != self._orig_goto_lead) or
                        (self._orig_base_duration is not None and new_base != self._orig_base_duration) or
                        (self._orig_mag_ref is not None and new_mag != self._orig_mag_ref)
                    )
                except Exception:
                    changed = False

                if changed:
                    try:
                        owner = getattr(self, 'Owner', None)
                        if owner and hasattr(owner, 'manager') and hasattr(owner, 'update_status'):
                            owner.update_status("Reprocessing events with new configuration...")
                            # Recalculate derived values for each in-memory event so
                            # recording duration, goto times and exposure are updated
                            # according to the new configuration. Preserve any
                            # user-set custom exposure values.
                            try:
                                for ev in owner.manager.all_events:
                                    # Use the public helper to recompute timing/exposure
                                    # so we don't duplicate logic here.
                                    try:
                                        if hasattr(ev, 'recompute_timing'):
                                            ev.recompute_timing()
                                        else:
                                            # Backwards compatible fallback
                                            ev._calculate_derived_values()
                                    except Exception:
                                        # Don't stop on single-event failure
                                        pass
                                # Keep the same filtered/active event list but ensure
                                # sorting and display are refreshed.
                                try:
                                    owner.manager.sort_events()
                                except Exception:
                                    pass
                                owner.refresh_display()
                                owner.update_status("Reprocessing complete")
                            except Exception:
                                # Fall back to reloading from files if in-memory
                                # reprocessing fails for some reason.
                                try:
                                    owner.manager.load_events_from_files()
                                    owner.refresh_display()
                                    owner.update_status("Reprocessing complete")
                                except Exception:
                                    owner.update_status("Reprocessing failed")
                    except Exception:
                        # Don't propagate UI errors
                        pass

                # Update our snapshot so further saves compare correctly
                try:
                    self._orig_goto_lead = self.config.get_goto_lead_time()
                    self._orig_base_duration = self.config.get_base_duration()
                    self._orig_mag_ref = self.config.get_mag_for_40ms_exposure()
                except Exception:
                    pass
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
    """Enhanced dialog for selecting sequence template with DPI scaling"""
    
    def __init__(self, config, theme_manager):
        Form.__init__(self)
        self.config = config
        self.theme_manager = theme_manager
        self.selected_template_path = ""
        self._sf = _detect_scale_factor()
        self.setup_ui()
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup enhanced template selection UI with DPI scaling"""
        sf = self._sf
        
        self.Text = "Select Sequence Template"
        self.Size = Size(int(800 * sf), int(600 * sf))
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.MaximizeBox = True
        self.MinimizeBox = True
        
        # Template list
        lbl_templates = Label()
        lbl_templates.Text = "Available Templates:"
        lbl_templates.Location = Point(int(10 * sf), int(10 * sf))
        lbl_templates.Size = Size(int(200 * sf), int(20 * sf))
        self.Controls.Add(lbl_templates)
        
        self.lst_templates = ListBox()
        self.lst_templates.Location = Point(int(10 * sf), int(35 * sf))
        self.lst_templates.Size = Size(int(760 * sf), int(150 * sf))
        self.lst_templates.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        self.lst_templates.SelectionMode = SelectionMode.One
        self.Controls.Add(self.lst_templates)
        
        # Load templates
        self.load_templates()
        
        # Template preview with proper scrolling - FIXED
        lbl_preview = Label()
        lbl_preview.Text = "Template Preview:"
        lbl_preview.Location = Point(int(10 * sf), int(200 * sf))
        lbl_preview.Size = Size(int(200 * sf), int(20 * sf))
        self.Controls.Add(lbl_preview)
        
        self.txt_preview = TextBox()
        self.txt_preview.Multiline = True
        self.txt_preview.ReadOnly = True
        self.txt_preview.ScrollBars = ScrollBars.Both  # Both horizontal and vertical scrollbars
        self.txt_preview.WordWrap = False  # FIXED: Disable word wrap for proper horizontal scrolling
        self.txt_preview.Font = Font("Courier New", 9 * sf)  # Monospace font with scaling
        self.txt_preview.Location = Point(int(10 * sf), int(225 * sf))
        self.txt_preview.Size = Size(int(760 * sf), int(300 * sf))
        self.txt_preview.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
        self.Controls.Add(self.txt_preview)
        
        # Buttons: standard OK/Cancel plus an 'Apply to All Events' checkbox
        btn_ok = Button()
        btn_ok.Text = "OK"
        btn_ok.DialogResult = DialogResult.OK
        btn_ok.Location = Point(int(600 * sf), int(533 * sf))
        _autosize_button(btn_ok, sf)
        btn_ok.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        self.Controls.Add(btn_ok)

        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.DialogResult = DialogResult.Cancel
        btn_cancel.Location = Point(int(685 * sf), int(533 * sf))
        _autosize_button(btn_cancel, sf)
        btn_cancel.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        self.Controls.Add(btn_cancel)

        # Checkbox to indicate whether the chosen template should be applied to all events
        self.chk_apply_all = CheckBox()
        self.chk_apply_all.Text = "Apply to All Events"
        self.chk_apply_all.Location = Point(int(350 * sf), int(533 * sf))
        self.chk_apply_all.Size = Size(int(200 * sf), int(24 * sf))
        self.chk_apply_all.Anchor = AnchorStyles.Bottom | AnchorStyles.Right

        # Default: do not apply to all unless the user explicitly checks the box
        self.chk_apply_all.Checked = False
        # Keep the attribute in sync with the checkbox state even if the user
        # never toggles it (avoid relying solely on CheckedChanged firing).
        self.apply_for_all = self.chk_apply_all.Checked
        self.chk_apply_all.CheckedChanged += lambda s, e: setattr(self, 'apply_for_all', s.Checked)
        self.Controls.Add(self.chk_apply_all)

        # Checkbox to request a single combined sequence file instead of separate files
        self.chk_create_combined = CheckBox()
        self.chk_create_combined.Text = "Create single combined sequence"
        self.chk_create_combined.Location = Point(int(10 * sf), int(533 * sf))
        self.chk_create_combined.Size = Size(int(240 * sf), int(24 * sf))
        self.chk_create_combined.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        self.chk_create_combined.Checked = False
        self.chk_create_combined.CheckedChanged += lambda s, e: setattr(self, 'create_combined', s.Checked)
        self.Controls.Add(self.chk_create_combined)

        # Wire events
        self.lst_templates.SelectedIndexChanged += self.template_selected

        # `apply_for_all` is initialized from the checkbox above so no-op here

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


class LocationConfirmDialog(Form):
    """Dialog to confirm observer location before generating report"""
    
    def __init__(self, event, theme_manager):
        Form.__init__(self)
        self.event = event
        self.theme_manager = theme_manager
        self.confirmed = False
        
        # Detect scale factor
        sf = _detect_scale_factor()
        
        # Form properties
        self.Text = "Confirm Observation Location"
        self.Size = Size(int(550 * sf), int(560 * sf))
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterParent
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.TopMost = True  # Ensure dialog appears on top
        
        # Main panel
        panel = Panel()
        panel.Dock = DockStyle.Fill
        from System.Windows.Forms import Padding as PaddingClass
        panel.Padding = PaddingClass(int(15 * sf), int(15 * sf), int(15 * sf), int(15 * sf))
        self.Controls.Add(panel)
        
        y_pos = 10
        
        # Title
        lbl_title = Label()
        lbl_title.Text = "Please confirm the observation location"
        lbl_title.Location = Point(int(10 * sf), y_pos)
        lbl_title.Size = Size(int(510 * sf), int(25 * sf))
        lbl_title.Font = Font(lbl_title.Font.FontFamily, 11, FontStyle.Bold)
        panel.Controls.Add(lbl_title)
        y_pos += int(35 * sf)
        
        # Event details
        lbl_event = Label()
        event_name = getattr(event, 'event_name', 'Unknown Event')
        event_date = ''
        if hasattr(event, 'event_datetime') and event.event_datetime:
            event_date = event.event_datetime.strftime('%Y-%m-%d %H:%M UTC')
        lbl_event.Text = f"Event: {event_name}\nDate: {event_date}"
        lbl_event.Location = Point(int(10 * sf), y_pos)
        lbl_event.Size = Size(int(510 * sf), int(40 * sf))
        panel.Controls.Add(lbl_event)
        y_pos += int(50 * sf)
        
        # Station info group
        station_group = GroupBox()
        station_group.Text = "Observation Location (editable)"
        station_group.Location = Point(int(10 * sf), y_pos)
        station_group.Size = Size(int(510 * sf), int(280 * sf))
        panel.Controls.Add(station_group)
        
        # Station name
        lbl_station = Label()
        station_name = getattr(event, 'station_name', 'Unknown Station')
        lbl_station.Text = f"Station: {station_name}"
        lbl_station.Location = Point(int(15 * sf), int(25 * sf))
        lbl_station.Size = Size(int(480 * sf), int(20 * sf))
        lbl_station.Font = Font(lbl_station.Font.FontFamily, 9, FontStyle.Bold)
        station_group.Controls.Add(lbl_station)
        
        # Observing Location (City, State/Country)
        lbl_obs_loc = Label()
        lbl_obs_loc.Text = "Observing Location:"
        lbl_obs_loc.Location = Point(int(15 * sf), int(50 * sf))
        lbl_obs_loc.Size = Size(int(140 * sf), int(20 * sf))
        station_group.Controls.Add(lbl_obs_loc)
        
        self.txt_obs_location = TextBox()
        self.txt_obs_location.Location = Point(int(160 * sf), int(50 * sf))
        self.txt_obs_location.Size = Size(int(200 * sf), int(20 * sf))
        # Prepopulate with stored value from event download
        obs_location_stored = getattr(event, 'obs_location', '')
        self.txt_obs_location.Text = obs_location_stored if obs_location_stored else ""
        station_group.Controls.Add(self.txt_obs_location)
        
        btn_lookup_loc = Button()
        btn_lookup_loc.Text = "Lookup"
        btn_lookup_loc.Location = Point(int(370 * sf), int(48 * sf))
        btn_lookup_loc.Size = Size(int(100 * sf), int(25 * sf))
        btn_lookup_loc.Click += self.lookup_location_click
        station_group.Controls.Add(btn_lookup_loc)
        
        # Get coordinates - prepopulate with stored values
        latitude = getattr(event, 'latitude', 0.0)
        longitude = getattr(event, 'longitude', 0.0)
        elevation = getattr(event, 'elevation', 0.0)
        
        # Latitude input
        lbl_lat = Label()
        lbl_lat.Text = "Latitude (°):"
        lbl_lat.Location = Point(int(15 * sf), int(80 * sf))
        lbl_lat.Size = Size(int(100 * sf), int(20 * sf))
        station_group.Controls.Add(lbl_lat)
        
        self.txt_latitude = TextBox()
        self.txt_latitude.Location = Point(int(120 * sf), int(80 * sf))
        self.txt_latitude.Size = Size(int(120 * sf), int(20 * sf))
        self.txt_latitude.Text = f"{latitude:.5f}"
        station_group.Controls.Add(self.txt_latitude)
        
        # Longitude input
        lbl_lon = Label()
        lbl_lon.Text = "Longitude (°):"
        lbl_lon.Location = Point(int(260 * sf), int(80 * sf))
        lbl_lon.Size = Size(int(100 * sf), int(20 * sf))
        station_group.Controls.Add(lbl_lon)
        
        self.txt_longitude = TextBox()
        self.txt_longitude.Location = Point(int(365 * sf), int(80 * sf))
        self.txt_longitude.Size = Size(int(120 * sf), int(20 * sf))
        self.txt_longitude.Text = f"{longitude:.5f}"
        station_group.Controls.Add(self.txt_longitude)
        
        # Elevation input
        lbl_elev = Label()
        lbl_elev.Text = "Elevation (m):"
        lbl_elev.Location = Point(int(15 * sf), int(110 * sf))
        lbl_elev.Size = Size(int(100 * sf), int(20 * sf))
        station_group.Controls.Add(lbl_elev)
        
        self.txt_elevation = TextBox()
        self.txt_elevation.Location = Point(int(120 * sf), int(110 * sf))
        self.txt_elevation.Size = Size(int(120 * sf), int(20 * sf))
        self.txt_elevation.Text = str(elevation) if elevation != 0.0 else ''
        station_group.Controls.Add(self.txt_elevation)
        
        # Google Maps link
        lbl_maps_text = Label()
        lbl_maps_text.Text = "View on map:"
        lbl_maps_text.Location = Point(int(15 * sf), int(145 * sf))
        lbl_maps_text.Size = Size(int(100 * sf), int(20 * sf))
        station_group.Controls.Add(lbl_maps_text)
        
        link_maps = LinkLabel()
        maps_url = f"https://www.google.com/maps?q={latitude},{longitude}"
        link_maps.Text = "Open Google Maps"
        link_maps.Location = Point(int(120 * sf), int(145 * sf))
        link_maps.Size = Size(int(150 * sf), int(20 * sf))
        link_maps.LinkClicked += lambda s, e: webbrowser.open(maps_url)
        station_group.Controls.Add(link_maps)
        
        # Lookup Elevation button
        btn_lookup_elev = Button()
        btn_lookup_elev.Text = "Lookup Elevation"
        btn_lookup_elev.Location = Point(int(285 * sf), int(142 * sf))
        btn_lookup_elev.Size = Size(int(130 * sf), int(25 * sf))
        btn_lookup_elev.Click += self.lookup_elevation_click
        station_group.Controls.Add(btn_lookup_elev)
        
        # Info label
        lbl_info = Label()
        lbl_info.Text = "Enter/verify observation location and coordinates.\nUse 'Lookup' to find city/town name from coordinates.\nUse 'Lookup Elevation' to get elevation (WGS84 datum)."
        lbl_info.Location = Point(int(15 * sf), int(180 * sf))
        lbl_info.Size = Size(int(480 * sf), int(80 * sf))
        lbl_info.ForeColor = Color.Gray
        station_group.Controls.Add(lbl_info)
        
        y_pos += int(290 * sf)
        
        # Buttons
        btn_panel = Panel()
        btn_panel.Height = int(40 * sf)
        btn_panel.Location = Point(0, y_pos)
        btn_panel.Width = int(520 * sf)
        panel.Controls.Add(btn_panel)
        
        btn_confirm = Button()
        btn_confirm.Text = "Next - event D/R"
        btn_confirm.Size = Size(int(180 * sf), int(28 * sf))
        btn_confirm.Location = Point(int(240 * sf), int(6 * sf))
        btn_confirm.Click += self.confirm_click
        btn_panel.Controls.Add(btn_confirm)
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Size = Size(int(100 * sf), int(28 * sf))
        btn_cancel.Location = Point(int(130 * sf), int(6 * sf))
        btn_cancel.Click += self.cancel_click
        btn_panel.Controls.Add(btn_cancel)
        
        # Apply theme
        apply_theme_to_control(self, theme_manager)
    
    def lookup_location_click(self, sender, e):
        """Look up city/town name from coordinates using reverse geocoding"""
        try:
            # Get current lat/lon values
            latitude = float(self.txt_latitude.Text)
            longitude = float(self.txt_longitude.Text)
            
            # Show working message
            original_text = sender.Text
            sender.Text = "Looking up..."
            sender.Enabled = False
            self.Refresh()
            
            # Import location lookup function
            from utils import get_location_name_from_coordinates
            
            # Lookup location name
            location_name = get_location_name_from_coordinates(latitude, longitude)
            
            # Restore button
            sender.Text = original_text
            sender.Enabled = True
            
            if location_name:
                self.txt_obs_location.Text = location_name
            else:
                MessageBox.Show("Could not retrieve location name from the service.\nPlease check your internet connection or enter location manually.", 
                              "Location Lookup Failed", MessageBoxButtons.OK, MessageBoxIcon.Warning)
        
        except ValueError:
            MessageBox.Show("Please enter valid latitude and longitude values first.", 
                          "Invalid Coordinates", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            sender.Text = original_text
            sender.Enabled = True
        except Exception as ex:
            MessageBox.Show(f"Error during location lookup: {ex}", 
                          "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            sender.Text = original_text
            sender.Enabled = True
    
    def lookup_elevation_click(self, sender, e):
        """Look up elevation from coordinates using online API"""
        try:
            # Get current lat/lon values
            latitude = float(self.txt_latitude.Text)
            longitude = float(self.txt_longitude.Text)
            
            # Show working message
            original_text = sender.Text
            sender.Text = "Looking up..."
            sender.Enabled = False
            self.Refresh()
            
            # Import elevation lookup function
            from utils import get_elevation_from_coordinates
            
            # Lookup elevation
            elevation = get_elevation_from_coordinates(latitude, longitude)
            
            # Restore button
            sender.Text = original_text
            sender.Enabled = True
            
            if elevation is not None:
                self.txt_elevation.Text = str(round(elevation, 1))
            else:
                MessageBox.Show("Could not retrieve elevation data from the service.\nPlease check your internet connection or enter elevation manually.", 
                              "Elevation Lookup Failed", MessageBoxButtons.OK, MessageBoxIcon.Warning)
        
        except ValueError:
            MessageBox.Show("Please enter valid latitude and longitude values first.", 
                          "Invalid Coordinates", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            sender.Text = original_text
            sender.Enabled = True
        except Exception as ex:
            MessageBox.Show(f"Error during elevation lookup: {ex}", 
                          "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            sender.Text = original_text
            sender.Enabled = True
    
    def confirm_click(self, sender, e):
        """User confirmed the location"""
        try:
            # Validate and store the entered values
            self.latitude = float(self.txt_latitude.Text)
            self.longitude = float(self.txt_longitude.Text)
            self.elevation = float(self.txt_elevation.Text) if self.txt_elevation.Text.strip() else 0.0
            self.obs_location = self.txt_obs_location.Text.strip()
            
            # Validate observing location is filled
            if not self.obs_location:
                MessageBox.Show("Please enter an observing location (use the Lookup button or enter manually).", 
                              "Missing Location", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            self.confirmed = True
            self.DialogResult = DialogResult.OK
            self.Close()
        except ValueError:
            MessageBox.Show("Please enter valid numeric values for latitude and longitude.", 
                          "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning)
    
    def cancel_click(self, sender, e):
        """User cancelled"""
        self.confirmed = False
        self.DialogResult = DialogResult.Cancel
        self.Close()
    
    def get_location(self):
        """Get the entered location values"""
        return {
            'latitude': self.latitude if hasattr(self, 'latitude') else 0.0,
            'longitude': self.longitude if hasattr(self, 'longitude') else 0.0,
            'elevation': self.elevation if hasattr(self, 'elevation') else 0.0,
            'obs_location': self.obs_location if hasattr(self, 'obs_location') else ''
        }
    