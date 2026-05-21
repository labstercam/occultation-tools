import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

import os
import webbrowser
from datetime import date
from System.Drawing import Point, Size, Color, Font, FontStyle
from System.Windows.Forms import (
    Form, Label, TextBox, Button, MessageBox, MessageBoxButtons, MessageBoxIcon,
    DialogResult, FormStartPosition, FormBorderStyle, Panel, GroupBox, LinkLabel,
    TabControl, TabPage, ListBox, ScrollBars, SelectionMode, AnchorStyles,
    CheckBox, FolderBrowserDialog, DockStyle, ToolTip, ComboBox, ComboBoxStyle,
    RadioButton
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


def _compute_quick_gains(default_gain):
    """Compute quick-gain button values based on default gain.

    For default_gain <= 1000: linear range 0 to 2*default_gain.
    For default_gain > 1000:  logarithmic range 100 to 100000 (fixed), log-spaced.

    Returns a sorted list of distinct integers representing sensible round gain values.
    """
    import math

    if default_gain <= 0:
        return [0, 50, 100, 150, 200, 300]

    if default_gain > 1000:
        # Logarithmic / dB scale: fixed range 100 to 100000, log-spaced
        low = 100.0
        high = 100000.0
        n = 6
        log_low = math.log10(low)
        log_high = math.log10(high)

        def _round_log(v):
            if v >= 10000:
                return int(round(v / 1000.0)) * 1000
            elif v >= 2000:
                return int(round(v / 100.0)) * 100
            else:
                return int(round(v / 50.0)) * 50

        raw = [10.0 ** (log_low + i * (log_high - log_low) / (n - 1)) for i in range(n)]
        rounded = [_round_log(v) for v in raw]
    else:
        # Linear scale: cover 0 to 2*default_gain in ~6 sensible steps
        high = 2 * default_gain
        if high >= 4000:
            unit = 1000
        elif high >= 2000:
            unit = 500
        elif high >= 1000:
            unit = 100
        elif high >= 400:
            unit = 50
        else:
            unit = 10

        capped_high = int(round(float(high) / unit)) * unit
        total_steps = capped_high // unit if unit > 0 else 1
        skip = max(1, (total_steps + 4) // 5)  # ceiling division → target ~6 buttons

        rounded = list(range(0, capped_high + unit, skip * unit))
        rounded = [g for g in rounded if g <= high + unit // 2]
        if capped_high not in rounded:
            rounded.append(capped_high)

    # Deduplicate while preserving order, then sort
    seen = set()
    result = []
    for g in rounded:
        if g not in seen:
            seen.add(g)
            result.append(g)
    return sorted(result)


class ExposureEditDialog(Form):
    """Dialog for editing event exposure and gain - DPI-aware version"""
    
    def __init__(self, event, theme_manager):
        Form.__init__(self)
        self.event = event
        self.theme_manager = theme_manager
        self.new_exposure_ms = event.exposure_ms
        self.new_gain = event.gain_value
        self.new_recording_duration = event.recording_duration
        self._sf = _detect_scale_factor()
        self.setup_ui()
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup settings edit dialog UI with DPI scaling"""
        sf = self._sf
        
        self.Text = f"Edit Settings - {self.event.event_name}"
        self.Size = Size(int(450 * sf), int(550 * sf))
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
        
        # Current exposure
        lbl_current = Label()
        current_text = f"Current Exposure: {self.event.exposure_ms} ms"
        if self.event.has_custom_exposure():
            current_text += " (Custom)"
        else:
            current_text += " (Calculated)"
        lbl_current.Text = current_text
        lbl_current.Location = Point(int(20 * sf), int(75 * sf))
        lbl_current.Size = Size(int(350 * sf), int(20 * sf))
        self.Controls.Add(lbl_current)
        
        # Current gain
        lbl_current_gain = Label()
        gain_text = f"Current Gain: {self.event.gain_value}"
        if self.event.has_custom_gain():
            gain_text += " (Custom)"
        else:
            gain_text += " (Default)"
        lbl_current_gain.Text = gain_text
        lbl_current_gain.Location = Point(int(20 * sf), int(95 * sf))
        lbl_current_gain.Size = Size(int(350 * sf), int(20 * sf))
        self.Controls.Add(lbl_current_gain)
        
        # Current recording duration
        lbl_current_duration = Label()
        duration_text = f"Current Recording Duration: {self.event.recording_duration} seconds"
        if self.event.has_custom_recording_duration():
            duration_text += " (Custom)"
        else:
            duration_text += " (Calculated)"
        lbl_current_duration.Text = duration_text
        lbl_current_duration.Location = Point(int(20 * sf), int(115 * sf))
        lbl_current_duration.Size = Size(int(410 * sf), int(20 * sf))
        self.Controls.Add(lbl_current_duration)
        
        # Exposure input
        lbl_new_exposure = Label()
        lbl_new_exposure.Text = "New Exposure (ms):"
        lbl_new_exposure.Location = Point(int(20 * sf), int(145 * sf))
        lbl_new_exposure.Size = Size(int(120 * sf), int(20 * sf))
        self.Controls.Add(lbl_new_exposure)
        
        self.txt_exposure = TextBox()
        self.txt_exposure.Text = str(self.event.exposure_ms)
        self.txt_exposure.Location = Point(int(150 * sf), int(145 * sf))
        self.txt_exposure.Size = Size(int(100 * sf), int(20 * sf))
        self.Controls.Add(self.txt_exposure)
        
        # Gain input
        lbl_new_gain = Label()
        lbl_new_gain.Text = "New Gain:"
        lbl_new_gain.Location = Point(int(20 * sf), int(170 * sf))
        lbl_new_gain.Size = Size(int(120 * sf), int(20 * sf))
        self.Controls.Add(lbl_new_gain)
        
        self.txt_gain = TextBox()
        self.txt_gain.Text = str(self.event.gain_value)
        self.txt_gain.Location = Point(int(150 * sf), int(170 * sf))
        self.txt_gain.Size = Size(int(100 * sf), int(20 * sf))
        self.Controls.Add(self.txt_gain)
        
        # Recording duration input
        lbl_new_duration = Label()
        lbl_new_duration.Text = "Recording Duration (s):"
        lbl_new_duration.Location = Point(int(20 * sf), int(195 * sf))
        lbl_new_duration.Size = Size(int(130 * sf), int(20 * sf))
        self.Controls.Add(lbl_new_duration)
        
        self.txt_duration = TextBox()
        self.txt_duration.Text = str(self.event.recording_duration)
        self.txt_duration.Location = Point(int(150 * sf), int(195 * sf))
        self.txt_duration.Size = Size(int(100 * sf), int(20 * sf))
        self.Controls.Add(self.txt_duration)
        
        # Quick exposure buttons
        lbl_quick = Label()
        lbl_quick.Text = "Quick Exposure:"
        lbl_quick.Location = Point(int(20 * sf), int(225 * sf))
        lbl_quick.Size = Size(int(100 * sf), int(20 * sf))
        self.Controls.Add(lbl_quick)
        
        quick_exposures = [40, 60, 80, 120, 160, 240, 320, 480]
        x_pos = int(20 * sf)
        y_pos = int(250 * sf)
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
        
        # Quick gain buttons
        lbl_quick_gain = Label()
        lbl_quick_gain.Text = "Quick Gain:"
        lbl_quick_gain.Location = Point(int(20 * sf), y_pos + int(10 * sf))
        lbl_quick_gain.Size = Size(int(100 * sf), int(20 * sf))
        self.Controls.Add(lbl_quick_gain)
        
        from config import ConfigManager as _CM_qg
        quick_gains = _compute_quick_gains(_CM_qg().get_default_gain())
        x_pos = int(20 * sf)
        y_pos = y_pos + int(35 * sf)
        
        for i, gain in enumerate(quick_gains):
            btn = Button()
            btn.Text = f"{gain}"
            btn.Location = Point(x_pos, y_pos)
            _autosize_button(btn, sf, padding=int(12 * sf), min_width=int(45 * sf))
            btn.Tag = gain
            btn.Click += self.quick_gain_click
            self.Controls.Add(btn)
            
            x_pos += btn.Width + gap
            if (i + 1) % 3 == 0:
                x_pos = int(20 * sf)
                y_pos += int(30 * sf)
        
        # Calculate button row Y position dynamically
        button_y = y_pos + int(20 * sf)
        
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
    
    def quick_gain_click(self, sender, e):
        """Handle quick gain button click"""
        self.txt_gain.Text = str(sender.Tag)
    
    def reset_click(self, sender, e):
        """Reset to calculated exposure, default gain, and calculated recording duration"""
        from config import ConfigManager
        config = ConfigManager()
        
        # Reset exposure: temporarily clear custom exposure to get calculated value
        original_custom = self.event.custom_exposure
        self.event.custom_exposure = None
        self.event._calculate_derived_values()
        calculated_exposure = self.event.exposure_ms
        # Restore original (dialog hasn't been saved yet)
        self.event.custom_exposure = original_custom
        self.event._calculate_derived_values()
        
        self.txt_exposure.Text = str(calculated_exposure)
        
        # Reset gain to config default
        default_gain = config.get_default_gain()
        self.txt_gain.Text = str(default_gain)
        
        # Reset recording duration: temporarily clear custom to get calculated value
        original_custom_duration = self.event.custom_recording_duration
        self.event.custom_recording_duration = None
        self.event._calculate_derived_values()
        calculated_duration = self.event.recording_duration
        # Restore original (dialog hasn't been saved yet)
        self.event.custom_recording_duration = original_custom_duration
        self.event._calculate_derived_values()
        
        self.txt_duration.Text = str(calculated_duration)
    
    def ok_click(self, sender, e):
        """Handle OK button click - validate exposure, gain, and recording duration"""
        try:
            # Validate exposure
            exposure_text = self.txt_exposure.Text.strip()
            if not exposure_text:
                MessageBox.Show("Please enter an exposure value", "Invalid Input", 
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            exp_value = int(exposure_text)
            if exp_value < 1 or exp_value > 10000:
                MessageBox.Show("Exposure must be between 1 and 10000 ms", "Invalid Exposure", 
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            # Validate gain
            gain_text = self.txt_gain.Text.strip()
            if not gain_text:
                MessageBox.Show("Please enter a gain value", "Invalid Input", 
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            gain_value = int(gain_text)
            if gain_value < 0:
                MessageBox.Show("Gain must be 0 or greater", "Invalid Gain",
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            # Validate recording duration
            duration_text = self.txt_duration.Text.strip()
            if not duration_text:
                MessageBox.Show("Please enter a recording duration value", "Invalid Input", 
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            duration_value = int(duration_text)
            if duration_value < 10 or duration_value > 3600:
                MessageBox.Show("Recording duration must be between 10 and 3600 seconds", "Invalid Duration", 
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            # All values are valid
            self.new_exposure_ms = exp_value
            self.new_gain = gain_value
            self.new_recording_duration = duration_value
            self.DialogResult = DialogResult.OK
            
        except ValueError:
            MessageBox.Show("Please enter valid numbers for all settings", "Invalid Input", 
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
    
    def get_new_exposure(self):
        """Get the new exposure value"""
        return self.new_exposure_ms
    
    def get_new_gain(self):
        """Get the new gain value"""
        return self.new_gain
    
    def get_new_recording_duration(self):
        """Get the new recording duration in seconds"""
        return self.new_recording_duration

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
        
        # Station Location Group
        grp_location = GroupBox()
        grp_location.Text = "Station Location"
        grp_location.Location = Point(int(10 * sf), y_pos)
        grp_location.Size = Size(int(560 * sf), int(145 * sf))
        main_panel.Controls.Add(grp_location)
        
        y_pos += int(155 * sf)
        
        self.add_detail_label(grp_location, "Latitude:", f"{self.event.latitude:.6f}°", 10, 25)
        self.add_detail_label(grp_location, "Longitude:", f"{self.event.longitude:.6f}°", 10, 50)
        station_elevation = getattr(self.event, 'elevation', None)
        if station_elevation is not None:
            try:
                station_elevation_text = f"{float(station_elevation):.1f} m"
            except Exception:
                station_elevation_text = str(station_elevation)
        else:
            station_elevation_text = "N/A"
        self.add_detail_label(grp_location, "Elevation:", station_elevation_text, 10, 75)
        station_location_text = getattr(self.event, 'obs_location', None)
        if not station_location_text:
            station_location_text = "N/A"
        self.add_detail_label(grp_location, "Location:", station_location_text, 10, 100)
        
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
        self.tab_control = TabControl()
        self.tab_control.Location = Point(int(10 * sf), int(10 * sf))
        self.tab_control.Size = Size(int(560 * sf), int(600 * sf))
        self.Controls.Add(self.tab_control)
        
        # User Credentials Tab
        tab_credentials = TabPage()
        tab_credentials.Text = "Credentials"
        self.setup_credentials_tab(tab_credentials)
        self.tab_control.TabPages.Add(tab_credentials)
        
        # File Paths Tab
        tab_paths = TabPage()
        tab_paths.Text = "File Paths"
        self.setup_paths_tab(tab_paths)
        self.tab_control.TabPages.Add(tab_paths)
        
        # Recording Settings Tab
        tab_recording = TabPage()
        tab_recording.Text = "User Settings"
        self.setup_recording_tab(tab_recording)
        self.tab_control.TabPages.Add(tab_recording)
        
        # Observer/Telescope Tab
        tab_observer = TabPage()
        tab_observer.Text = "Observer/Telescope"
        self.setup_observer_telescope_tab(tab_observer)
        self.tab_control.TabPages.Add(tab_observer)
        
        self.setup_api_tab(tab_credentials)
        
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

        lbl_retention_days = Label()
        lbl_retention_days.Text = "Days to Retain:"
        lbl_retention_days.Location = Point(int(20 * sf), int(180 * sf))
        lbl_retention_days.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(lbl_retention_days)

        self.txt_retention_days = TextBox()
        self.txt_retention_days.Location = Point(int(130 * sf), int(180 * sf))
        self.txt_retention_days.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(self.txt_retention_days)
        self.tooltip.SetToolTip(self.txt_retention_days, "Number of days to retain events in the occultations file (1-400 days)")
        
        # Information panel
        info_panel = GroupBox()
        info_panel.Text = "How to Get Your OWC Credentials"
        info_panel.Location = Point(int(20 * sf), int(220 * sf))
        info_panel.Size = Size(int(500 * sf), int(145 * sf))
        tab.Controls.Add(info_panel)
        
        info_text = Label()
        info_text.Text = ("1. Create an account or log in at Occult Watcher Cloud\n"
                         "2. Go to your User Profile page (link below)\n"
                         "3. Click on the 'Permissions & Settings' sub-tab\n"
                         "4. Find or generate your API Key in that section\n"
                         "5. Copy your email and API Key to the fields above")
        info_text.Location = Point(int(10 * sf), int(20 * sf))
        info_text.Size = Size(int(480 * sf), int(88 * sf))
        info_text.AutoSize = False
        info_panel.Controls.Add(info_text)
        
        # Clickable link to user profile
        link_profile = LinkLabel()
        link_profile.Text = "Open OWC User Profile →"
        link_profile.Location = Point(int(10 * sf), int(112 * sf))
        link_profile.AutoSize = True
        link_profile.LinkClicked += self.open_owc_profile
        info_panel.Controls.Add(link_profile)
        self.tooltip.SetToolTip(link_profile, "Opens https://cloud.occultwatcher.net/user-profile in your browser")

        download_panel = GroupBox()
        download_panel.Text = "How Download from OWC Works"
        download_panel.Location = Point(int(20 * sf), int(375 * sf))
        download_panel.Size = Size(int(500 * sf), int(140 * sf))
        tab.Controls.Add(download_panel)

        download_text = Label()
        download_text.Text = ("When you click 'Download Events', the application:\n"
                     "1. Reads your 'Upcoming Events' from OWC (link below)\n"
                     "2. Saves the downloaded events to data/events/\n"
                     "3. Merges with existing occultation events data\n"
                     "4. Retains only events no more than the specified days old")
        download_text.Location = Point(int(10 * sf), int(20 * sf))
        download_text.Size = Size(int(480 * sf), int(80 * sf))
        download_text.AutoSize = False
        download_panel.Controls.Add(download_text)

        link_events = LinkLabel()
        link_events.Text = "Open My Events on OWC →"
        link_events.Location = Point(int(10 * sf), int(105 * sf))
        link_events.AutoSize = True
        link_events.LinkClicked += self.open_owc_events
        download_panel.Controls.Add(link_events)
        self.tooltip.SetToolTip(link_events, "Opens https://cloud.occultwatcher.net/my-events in your browser")
    
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

        lbl_folder_actions = Label()
        lbl_folder_actions.Text = "Open Data Folders in Windows Explorer"
        lbl_folder_actions.Location = Point(int(20 * sf), int(20 * sf))
        lbl_folder_actions.Size = Size(int(350 * sf), int(20 * sf))
        tab.Controls.Add(lbl_folder_actions)

        btn_open_config = Button()
        btn_open_config.Text = "Open Config Folder"
        btn_open_config.Location = Point(int(20 * sf), int(60 * sf))
        _autosize_button(btn_open_config, sf, min_width=int(160 * sf))
        btn_open_config.Click += self.open_config_folder_click
        tab.Controls.Add(btn_open_config)

        btn_open_events = Button()
        btn_open_events.Text = "Open Events Folder"
        btn_open_events.Location = Point(int(200 * sf), int(60 * sf))
        _autosize_button(btn_open_events, sf, min_width=int(160 * sf))
        btn_open_events.Click += self.open_events_folder_click
        tab.Controls.Add(btn_open_events)

        btn_open_reports = Button()
        btn_open_reports.Text = "Open Reports Folder"
        btn_open_reports.Location = Point(int(20 * sf), int(100 * sf))
        _autosize_button(btn_open_reports, sf, min_width=int(160 * sf))
        btn_open_reports.Click += self.open_reports_folder_click
        tab.Controls.Add(btn_open_reports)

        btn_open_sequences = Button()
        btn_open_sequences.Text = "Open Sequences Folder"
        btn_open_sequences.Location = Point(int(200 * sf), int(100 * sf))
        _autosize_button(btn_open_sequences, sf, min_width=int(160 * sf))
        btn_open_sequences.Click += self.open_sequences_folder_click
        tab.Controls.Add(btn_open_sequences)

        btn_open_templates = Button()
        btn_open_templates.Text = "Open Templates Folder"
        btn_open_templates.Location = Point(int(20 * sf), int(140 * sf))
        _autosize_button(btn_open_templates, sf, min_width=int(160 * sf))
        btn_open_templates.Click += self.open_templates_folder_click
        tab.Controls.Add(btn_open_templates)

        lbl_path_note = Label()
        lbl_path_note.Text = "Folders are fixed under the installation data directory."
        lbl_path_note.Location = Point(int(20 * sf), int(190 * sf))
        lbl_path_note.Size = Size(int(500 * sf), int(20 * sf))
        lbl_path_note.ForeColor = Color.Gray
        tab.Controls.Add(lbl_path_note)
    
    def open_owc_events(self, sender, e):
        """Open OWC my events page in browser"""
        try:
            webbrowser.open("https://cloud.occultwatcher.net/my-events")
        except Exception as ex:
            MessageBox.Show(f"Could not open browser: {ex}", "Error", 
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)

    def _open_folder_in_explorer(self, folder_path):
        """Open a folder in Windows Explorer"""
        try:
            if folder_path and not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
            os.startfile(folder_path)
        except Exception as ex:
            MessageBox.Show(f"Could not open folder: {ex}", "Error",
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)

    def open_config_folder_click(self, sender, e):
        self._open_folder_in_explorer(self.config.get_config_folder())

    def open_events_folder_click(self, sender, e):
        self._open_folder_in_explorer(self.config.get_events_folder())

    def open_reports_folder_click(self, sender, e):
        self._open_folder_in_explorer(self.config.get_reports_folder())

    def open_sequences_folder_click(self, sender, e):
        self._open_folder_in_explorer(self.config.get_sequences_folder())

    def open_templates_folder_click(self, sender, e):
        self._open_folder_in_explorer(self.config.get_templates_folder())

    def open_debug_logs_folder_click(self, sender, e):
        """Open folder containing debug log files."""
        try:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            self._open_folder_in_explorer(module_dir)
        except Exception as ex:
            MessageBox.Show(f"Could not open debug log folder: {ex}", "Error",
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
        
        btn_explain_base_duration = Button()
        btn_explain_base_duration.Text = "Explain"
        btn_explain_base_duration.Location = Point(int(260 * sf), int(18 * sf))
        _autosize_button(btn_explain_base_duration, sf, height=int(22 * sf), min_width=int(70 * sf))
        btn_explain_base_duration.Click += self.explain_base_duration_click
        tab.Controls.Add(btn_explain_base_duration)
        
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
        
        btn_explain_goto_lead = Button()
        btn_explain_goto_lead.Text = "Explain"
        btn_explain_goto_lead.Location = Point(int(260 * sf), int(48 * sf))
        _autosize_button(btn_explain_goto_lead, sf, height=int(22 * sf), min_width=int(70 * sf))
        btn_explain_goto_lead.Click += self.explain_goto_lead_click
        tab.Controls.Add(btn_explain_goto_lead)
        
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

        btn_explain_mag_exposure = Button()
        btn_explain_mag_exposure.Text = "Explain"
        btn_explain_mag_exposure.Location = Point(int(260 * sf), int(78 * sf))
        _autosize_button(btn_explain_mag_exposure, sf, height=int(22 * sf), min_width=int(70 * sf))
        btn_explain_mag_exposure.Click += self.explain_mag_exposure_click
        tab.Controls.Add(btn_explain_mag_exposure)

        lbl_default_gain = Label()
        lbl_default_gain.Text = "Default Gain:"
        lbl_default_gain.Location = Point(int(20 * sf), int(110 * sf))
        lbl_default_gain.Size = Size(int(120 * sf), int(20 * sf))
        tab.Controls.Add(lbl_default_gain)
        
        self.txt_default_gain = TextBox()
        self.txt_default_gain.Location = Point(int(150 * sf), int(110 * sf))
        self.txt_default_gain.Size = Size(int(100 * sf), int(20 * sf))
        tab.Controls.Add(self.txt_default_gain)
        self.tooltip.SetToolTip(self.txt_default_gain, "Default camera gain value (integer, minimum 0, no upper limit). Used for all events unless overridden per-event.")

        btn_explain_default_gain = Button()
        btn_explain_default_gain.Text = "Explain"
        btn_explain_default_gain.Location = Point(int(260 * sf), int(108 * sf))
        _autosize_button(btn_explain_default_gain, sf, height=int(22 * sf), min_width=int(70 * sf))
        btn_explain_default_gain.Click += self.explain_default_gain_click
        tab.Controls.Add(btn_explain_default_gain)

        self.chk_sync_mount = CheckBox()
        self.chk_sync_mount.Text = "Sync Mount with GOTO"       
        self.chk_sync_mount.Location = Point(int(20 * sf), int(140 * sf))
        self.chk_sync_mount.Size = Size(int(200 * sf), int(20 * sf))    
        tab.Controls.Add(self.chk_sync_mount)
        self.tooltip.SetToolTip(self.chk_sync_mount, "⚠ WARNING: Only enable if you usually SYNC your mount with every GOTO. Do NOT use with permanently aligned or precision aligned mounts!")

        self.chk_sync_mount.Checked = self.config.get_sync_mount()
        self.chk_sync_mount.CheckedChanged += self.sync_mount_checked_changed

        btn_explain_sync_mount = Button()
        btn_explain_sync_mount.Text = "Explain"
        btn_explain_sync_mount.Location = Point(int(230 * sf), int(138 * sf))
        _autosize_button(btn_explain_sync_mount, sf, height=int(22 * sf), min_width=int(70 * sf))
        btn_explain_sync_mount.Click += self.explain_sync_mount_click
        tab.Controls.Add(btn_explain_sync_mount)

        self.display_utc = CheckBox()
        self.display_utc.Text = "Display UTC in Grid"       
        self.display_utc.Location = Point(int(20 * sf), int(170 * sf))
        self.display_utc.Size = Size(int(200 * sf), int(20 * sf))    
        tab.Controls.Add(self.display_utc)
        self.tooltip.SetToolTip(self.display_utc, "Display event times in UTC (Coordinated Universal Time) in the main grid. When unchecked, times are shown in local time")

        self.display_utc.Checked = self.config.get_display_utc()
        self.display_utc.CheckedChanged += self.display_utc_checked_changed
        
        btn_explain_display_utc = Button()
        btn_explain_display_utc.Text = "Explain"
        btn_explain_display_utc.Location = Point(int(230 * sf), int(168 * sf))
        _autosize_button(btn_explain_display_utc, sf, height=int(22 * sf), min_width=int(70 * sf))
        btn_explain_display_utc.Click += self.explain_display_utc_click
        tab.Controls.Add(btn_explain_display_utc)

        self.chk_output_debug_logs = CheckBox()
        self.chk_output_debug_logs.Text = "Output Debug Logs"
        self.chk_output_debug_logs.Location = Point(int(20 * sf), int(200 * sf))
        self.chk_output_debug_logs.Size = Size(int(200 * sf), int(20 * sf))
        tab.Controls.Add(self.chk_output_debug_logs)
        self.tooltip.SetToolTip(self.chk_output_debug_logs, "Enable verbose debug console/file logging for OWC download and event parsing")

        self.chk_output_debug_logs.Checked = self.config.get_output_debug_logs()
        
        btn_open_debug_logs = Button()
        btn_open_debug_logs.Text = "Open Debug Logs Folder"
        btn_open_debug_logs.Location = Point(int(230 * sf), int(198 * sf))
        _autosize_button(btn_open_debug_logs, sf, height=int(22 * sf), min_width=int(165 * sf))
        btn_open_debug_logs.Click += self.open_debug_logs_folder_click
        tab.Controls.Add(btn_open_debug_logs)
        self.tooltip.SetToolTip(btn_open_debug_logs, "Open folder containing owc_raw_download.log and owc_data_debug.log")
    
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

    def explain_base_duration_click(self, sender, e):
        """Show explanation for Base Duration setting"""
        explanation = ("Recording Duration Formula:\n\n"
                      "Duration = Base Duration + Event Duration (if >5 s) + 6 × Uncertainty (if >2 s)\n\n"
                      "Example 1:\n"
                      "  Base Duration 60 s, Event Duration 1.2 s, Uncertainty 1 s → 60s total\n\n"
                      "Example 2:\n"
                      "  Base Duration 60 s, Event Duration 6 s, Uncertainty 3 s → 60 + 6 + 18 = 84s\n\n"
                      "In plain English:\n"
                      "Start with the base duration, and add the event duration if it's more than 5 seconds,\n"
                      "and add 6 times the uncertainty if it's more than 2 s to ensure full event coverage.")
        MessageBox.Show(explanation, "Base Duration Explanation", 
                       MessageBoxButtons.OK, MessageBoxIcon.Information)

    def explain_goto_lead_click(self, sender, e):
        """Show explanation for GOTO Lead Time setting"""
        explanation = ("GOTO Lead Time:\n\n"
                      "This setting determines how many seconds before the start of recording to begin\n"
                      "the GOTO slew to the target position.\n\n"
                      "This ensures the mount has enough time to slew to the target and settle before\n"
                      "recording needs to begin.\n\n"
                      "Example:\n"
                      "  If recording should start at 22:30:00 and GOTO Lead Time is 120 seconds,\n"
                      "  the GOTO command will be issued at 22:28:00.")
        MessageBox.Show(explanation, "GOTO Lead Time Explanation", 
                       MessageBoxButtons.OK, MessageBoxIcon.Information)

    def explain_mag_exposure_click(self, sender, e):
        """Show explanation for Mag for 40ms Exposure setting"""
        explanation = ("Exposure Time Formula:\n\n"
                      "Exposure = 40 ms × 2^(CombMag + Extinction - MagRef)\n\n"
                      "Adjusted for atmospheric extinction based on star altitude.\n\n"
                      "In plain English:\n"
                      "For every magnitude the star is dimmer than the reference magnitude,\n"
                      "the exposure time doubles.\n\n"
                      "MagRef: The star magnitude where you would usually use 40 ms exposure\n\n"
                      "Example:\n"
                      "  MagRef 10.0, CombMag 12.0, Extinction 0.3\n"
                      "  → 40 × 2^(12.0 + 0.3 - 10.0)\n"
                      "  → 40 × 2^(2) = 160 ms\n\n"
                      "40 ms is the minimum exposure that will be automatically set.\n"
                      "Values set by doubling are 80 ms, 160 ms, 320 ms etc.\n"
                      "You can manually set a custom exposure per event if desired.")
        MessageBox.Show(explanation, "Mag for 40ms Exposure Explanation", 
                       MessageBoxButtons.OK, MessageBoxIcon.Information)

    def explain_default_gain_click(self, sender, e):
        """Show explanation for Default Gain setting"""
        explanation = ("Default Gain:\n\n"
                      "This is the default camera gain value used for all events\n"
                      "unless overridden per-event. Minimum value is 0; there is no upper limit.\n\n"
                      "Higher gain values have slightly less read noise so give slightly better SNR.\n\n"
                      "Typical values:\n"
                      "  • 0-200: Low gain, low noise (very bright targets)\n"
                      "  • 350-450: Medium-high gain recommended for most occultations\n"
                      "  • 450+: High gain. Not recommended - do test recordings and reductions first\n\n"
                      "Note: Gain values above 1000 are interpreted as logarithmic (dB) gain.\n"
                      "The Edit Settings quick gain buttons will automatically adapt to the dB scale.\n\n")
        MessageBox.Show(explanation, "Default Gain Explanation", 
                       MessageBoxButtons.OK, MessageBoxIcon.Information)

    def explain_sync_mount_click(self, sender, e):
        """Show explanation for Sync Mount with GOTO setting"""
        explanation = ("⚠ Sync Mount Warning:\n\n"
                      "Only enable 'Sync Mount' if you usually Sync the mount with each GOTO.\n\n"
                      "Do NOT sync if you have:\n"
                      "  • A permanently aligned mount\n"
                      "  • A refined pointing model\n\n"
                      "Syncing could adversely affect your carefully calibrated pointing model!\n\n"
                      "When enabled, the mount will sync to the plate-solved position after each GOTO,\n"
                      "which can help with mounts that have poor pointing accuracy.")
        MessageBox.Show(explanation, "Sync Mount with GOTO Explanation", 
                       MessageBoxButtons.OK, MessageBoxIcon.Warning)

    def explain_display_utc_click(self, sender, e):
        """Show explanation for Display UTC in Grid setting"""
        explanation = ("Display UTC in Grid:\n\n"
                      "When enabled, all event times in the main grid will be displayed in\n"
                      "UTC (Coordinated Universal Time).\n\n"
                      "When disabled, times are shown in your local time zone.\n\n"
                      "UTC is the standard for astronomical observations and makes it easier to\n"
                      "coordinate with other observers around the world.\n\n"
                      "Note: Times in generated reports may still use UTC regardless of this setting,\n"
                      "as UTC is the standard for official submissions.")
        MessageBox.Show(explanation, "Display UTC in Grid Explanation", 
                       MessageBoxButtons.OK, MessageBoxIcon.Information)



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
        self.txt_host.ReadOnly = True
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
        lbl_report_note.Text = "This information will be used to auto-fill Report Forms"
        lbl_report_note.Location = Point(int(20 * sf), int(385 * sf))
        lbl_report_note.Size = Size(int(480 * sf), int(30 * sf))
        lbl_report_note.ForeColor = Color.Gray
        tab.Controls.Add(lbl_report_note)
    
    def load_current_config(self):
        """Load current configuration into controls"""
        self.txt_email.Text = self.config.get_owc_email()
        self.txt_password.Text = self.config.get_owc_password()
        self.txt_retention_days.Text = str(self.config.get_days_to_retain_events())
        self.txt_base_duration.Text = str(self.config.get_base_duration())
        self.txt_goto_lead.Text = str(self.config.get_goto_lead_time())
        self.txt_mag_exposure.Text = '{:.1f}'.format(self.config.get_mag_for_40ms_exposure())
        self.txt_default_gain.Text = str(self.config.get_default_gain())
        self.chk_sync_mount.Checked = self.config.get_sync_mount()
        self.display_utc.Checked = self.config.get_display_utc()
        self.chk_output_debug_logs.Checked = self.config.get_output_debug_logs()
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
        """Open fixed events folder"""
        self._open_folder_in_explorer(self.config.get_events_folder())
    
    def browse_sequence_path_click(self, sender, e):
        """Open fixed sequences folder"""
        self._open_folder_in_explorer(self.config.get_sequences_folder())
    
    def save_config_click(self, sender, e):
        """Save configuration"""
        try:
            # Update config with form values
            self.config.set_owc_email(self.txt_email.Text)
            self.config.set_owc_password(self.txt_password.Text)
            
            # Validate and save retention days
            retention_days = int(self.txt_retention_days.Text)
            if retention_days < 1 or retention_days > 400:
                MessageBox.Show("Days to retain events must be between 1 and 400", "Invalid Value",
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            self.config.set_days_to_retain_events(retention_days)
            
            self.config.set_base_duration(int(self.txt_base_duration.Text))
            self.config.set_goto_lead_time(int(self.txt_goto_lead.Text))
            self.config.set_mag_for_40ms_exposure(round(float(self.txt_mag_exposure.Text), 1))
            self.config.set_default_gain(int(self.txt_default_gain.Text))
            self.config.set_sync_mount(self.chk_sync_mount.Checked)
            self.config.set_display_utc(self.display_utc.Checked)
            self.config.set_output_debug_logs(self.chk_output_debug_logs.Checked)
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
        """Reset current tab settings to defaults"""
        selected_tab = None
        tab_name = ""
        try:
            selected_tab = self.tab_control.SelectedTab
            tab_name = selected_tab.Text if selected_tab else ""
        except Exception:
            tab_name = ""

        if tab_name == "File Paths":
            MessageBox.Show("File paths are fixed and have no resettable values.", "No Reset Needed",
                          MessageBoxButtons.OK, MessageBoxIcon.Information)
            return

        if not tab_name:
            tab_name = "All Tabs"

        if MessageBox.Show(f"Reset settings on '{tab_name}' tab to defaults?", "Confirm Reset",
                         MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes:
            return

        defaults = self.config.default_config

        try:
            if tab_name == "Credentials":
                self.config.set_owc_email(defaults.get('owc_user_email', ''))
                self.config.set_owc_password(defaults.get('owc_user_password', ''))
                self.config.set_days_to_retain_events(defaults.get('days_to_retain_events', 14))
                self.config.set_host(defaults.get('host', ''))
                self.config.set_api_key(defaults.get('apiKey', ''))
            elif tab_name == "User Settings":
                self.config.set_base_duration(defaults.get('base_duration', 60))
                self.config.set_goto_lead_time(defaults.get('goto_lead_time', 240))
                self.config.set_mag_for_40ms_exposure(defaults.get('mag_for_40ms_exposure', 12.0))
                self.config.set_default_gain(defaults.get('default_gain', 450))
                self.config.set_sync_mount(defaults.get('sync_mount', True))
                self.config.set_display_utc(defaults.get('display_utc', True))
                self.config.set_output_debug_logs(defaults.get('output_debug_logs', False))
            elif tab_name == "Observer/Telescope":
                self.config.set_observer_name(defaults.get('observer_name', ''))
                self.config.set_observer_email(defaults.get('observer_email', ''))
                self.config.set_observer_address(defaults.get('observer_address', ''))
                self.config.set_observer_city(defaults.get('observer_city', ''))
                self.config.set_observer_state(defaults.get('observer_state', ''))
                self.config.set_observer_country(defaults.get('observer_country', ''))
                self.config.set_observer_phone(defaults.get('observer_phone', ''))
                self.config.set_observer_fax(defaults.get('observer_fax', ''))
            else:
                # Fallback: preserve previous behavior if tab is unknown
                self.config.reset_to_defaults()

            self.config.save_config()
            self.load_current_config()

            try:
                self._orig_goto_lead = self.config.get_goto_lead_time()
                self._orig_base_duration = self.config.get_base_duration()
                self._orig_mag_ref = self.config.get_mag_for_40ms_exposure()
            except Exception:
                pass

            MessageBox.Show(f"'{tab_name}' settings reset to defaults", "Reset Complete",
                          MessageBoxButtons.OK, MessageBoxIcon.Information)
        except Exception as ex:
            MessageBox.Show(f"Error resetting defaults: {ex}", "Reset Error",
                          MessageBoxButtons.OK, MessageBoxIcon.Error)

class TemplateSelectionDialog(Form):
    """Enhanced dialog for selecting sequence template with DPI scaling"""
    
    def __init__(self, config, theme_manager, help_manager=None):
        Form.__init__(self)
        self.config = config
        self.theme_manager = theme_manager
        self.help_manager = help_manager
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
        
        # Open Templates Folder button
        btn_open_folder = Button()
        btn_open_folder.Text = "Open Templates Folder"
        btn_open_folder.Location = Point(int(620 * sf), int(8 * sf))
        _autosize_button(btn_open_folder, sf)
        btn_open_folder.Anchor = AnchorStyles.Top | AnchorStyles.Right
        btn_open_folder.Click += self.open_templates_folder
        self.Controls.Add(btn_open_folder)
        
        self.lst_templates = ListBox()
        self.lst_templates.Location = Point(int(10 * sf), int(35 * sf))
        self.lst_templates.Size = Size(int(760 * sf), int(150 * sf))
        self.lst_templates.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        self.lst_templates.SelectionMode = SelectionMode.One
        self.Controls.Add(self.lst_templates)
        
        # Load templates
        self.load_templates()
        
        # Help buttons row
        btn_utc_info = Button()
        btn_utc_info.Text = "UTC or Local Time Template?"
        btn_utc_info.Location = Point(int(10 * sf), int(190 * sf))
        _autosize_button(btn_utc_info, sf)
        btn_utc_info.Click += self.show_utc_vs_local_info
        self.Controls.Add(btn_utc_info)
        
        btn_template_help = Button()
        btn_template_help.Text = "Template Help"
        btn_template_help.Location = Point(int(250 * sf), int(190 * sf))
        _autosize_button(btn_template_help, sf)
        btn_template_help.Click += self.show_template_help
        if not self.help_manager:
            btn_template_help.Enabled = False
        self.Controls.Add(btn_template_help)
        
        # Template preview with proper scrolling
        lbl_preview = Label()
        lbl_preview.Text = "Template Preview:"
        lbl_preview.Location = Point(int(10 * sf), int(225 * sf))
        lbl_preview.Size = Size(int(200 * sf), int(20 * sf))
        self.Controls.Add(lbl_preview)
        
        self.txt_preview = TextBox()
        self.txt_preview.Multiline = True
        self.txt_preview.ReadOnly = True
        self.txt_preview.ScrollBars = ScrollBars.Both  # Both horizontal and vertical scrollbars
        self.txt_preview.WordWrap = False
        self.txt_preview.Font = Font("Courier New", 9 * sf)  # Monospace font matching dialog text size
        self.txt_preview.Location = Point(int(10 * sf), int(250 * sf))
        self.txt_preview.Size = Size(int(760 * sf), int(275 * sf))
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

        self.AcceptButton = btn_ok
        self.CancelButton = btn_cancel
    
    def load_templates(self):
        """Load available templates into the list"""
        template_files, template_folder = TemplateManager.find_template_files(self.config.get_templates_folder())
        
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
            # Get the selected template file
            template_files, template_folder = TemplateManager.find_template_files(self.config.get_templates_folder())
            if self.lst_templates.SelectedIndex < len(template_files):
                template_file = template_files[self.lst_templates.SelectedIndex]
                self.selected_template_path = os.path.join(template_folder, template_file)
                template_content = TemplateManager.load_template(self.selected_template_path, self.config)
            else:
                template_content = None
            
            # Show preview with proper line breaks
            if template_content:
                # Don't truncate, let scrollbars handle the content
                self.txt_preview.Text = template_content.replace('\n','\r\n')
            else:
                self.txt_preview.Text = "Could not load template content"
    
    def get_selected_template_path(self):
        """Get the selected template path"""
        return self.selected_template_path
    
    def open_templates_folder(self, sender, e):
        """Open the templates folder in Windows Explorer"""
        try:
            template_files, template_folder = TemplateManager.find_template_files(self.config.get_templates_folder())
            if os.path.exists(template_folder):
                os.startfile(template_folder)
            else:
                MessageBox.Show(
                    f"Templates folder not found:\n{template_folder}",
                    "Folder Not Found",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                )
        except Exception as ex:
            MessageBox.Show(
                f"Error opening templates folder:\n{str(ex)}",
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
    
    def show_utc_vs_local_info(self, sender, e):
        """Show information about UTC vs Local Time templates"""
        info_text = (
            "UTC TEMPLATES (Recommended):\n"
            "\u2022 Start at exactly the UTC times specified\n"
            "\u2022 Work correctly across midnight boundaries\n"
            "\u2022 Handle late starts gracefully\n"
            "\u2022 Include countdown options (notification banner or dialog window)\n"
            "\n"
            "LOCAL TIME TEMPLATES:\n"
            "\u2022 Do not know what the date is, only work for current day\n"
            "\u2022 Can have problems with midnight changeover\n"
            "\u2022 If a sequence step starts late, it may wait another 24 hours\n"
            "\n"
            "IMPORTANT NOTES:\n"
            "\u2022 Templates have detailed comments explaining how they work and any limitations\n"
            "\u2022 Whichever you choose, do extensive tests to understand how they work on your system with your equipment\n"
            "\n"
            "Recommendation: Use UTC templates for reliable, predictable behavior."
        )
        MessageBox.Show(
            info_text,
            "UTC vs Local Time Templates",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )
    
    def show_template_help(self, sender, e):
        """Open help dialog to Template Modification section"""
        if self.help_manager:
            self.help_manager.show_help(self, topic="template_modification")
    
    def show_utc_vs_local_info(self, sender, e):
        """Show information about UTC vs Local Time templates"""
        info_text = (
            "UTC TEMPLATES (Recommended):\n"
            "\u2022 Start at exactly the UTC times specified\n"
            "\u2022 Work correctly across midnight boundaries\n"
            "\u2022 Handle late starts gracefully\n"
            "\u2022 Include countdown options (notification banner or dialog window)\n"
            "\n"
            "LOCAL TIME TEMPLATES:\n"
            "\u2022 Do not know what the date is, only work for current day\n"
            "\u2022 Can have problems with midnight changeover\n"
            "\u2022 If a sequence step starts late, it may wait another 24 hours\n"
            "\n"
            "IMPORTANT NOTES:\n"
            "\u2022 Templates have detailed comments explaining how they work and any limitations\n"
            "\u2022 Whichever you choose, do extensive tests to understand how they work on your system with your equipment\n"
            "\n"
            "Recommendation: Use UTC templates for reliable, predictable behavior."
        )
        MessageBox.Show(
            info_text,
            "UTC vs Local Time Templates",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )
    
    def show_template_help(self, sender, e):
        """Open help dialog to Template Modification section"""
        if self.help_manager:
            self.help_manager.show_help(self, topic="template_modification")


class LocationConfirmDialog(Form):
    """Dialog to confirm observer location before generating report"""
    
    def __init__(self, event, theme_manager, config=None, ntp_context=None):
        Form.__init__(self)
        self.event = event
        self.theme_manager = theme_manager
        self.config = config
        self.ntp_context = ntp_context or {}
        self.confirmed = False
        self._sf = _detect_scale_factor()
        sf = self._sf
        
        # Form properties
        self.Text = "Confirm Observation Location"
        self.Size = Size(int(620 * sf), int(720 * sf))
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
        lbl_title.Text = "Step 1: Confirm the observation location"
        lbl_title.Location = Point(int(10 * sf), y_pos)
        lbl_title.Size = Size(int(510 * sf), int(25 * sf))
        lbl_title.Font = Font(lbl_title.Font.FontFamily, 11 * sf, FontStyle.Bold)
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
        lbl_station.Font = Font(lbl_station.Font.FontFamily, 9 * sf, FontStyle.Bold)
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
        elevation = getattr(event, 'elevation', None)  # None means lookup needed
        
        # Latitude input
        lbl_lat = Label()
        lbl_lat.Text = "Latitude (°):"
        lbl_lat.Location = Point(int(15 * sf), int(80 * sf))
        lbl_lat.Size = Size(int(100 * sf), int(20 * sf))
        station_group.Controls.Add(lbl_lat)
        
        self.txt_latitude = TextBox()
        self.txt_latitude.Location = Point(int(120 * sf), int(80 * sf))
        self.txt_latitude.Size = Size(int(120 * sf), int(20 * sf))
        self.txt_latitude.Text = f"{latitude:.6f}"
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
        self.txt_longitude.Text = f"{longitude:.6f}"
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
        if elevation is None:
            self.txt_elevation.Text = ''
        elif elevation == 0.0:
            self.txt_elevation.Text = '0'
        else:
            self.txt_elevation.Text = str(elevation)
        self._elevation_needs_lookup = (elevation is None)
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

        # ===== STEP 2: REPORT FORMAT =====
        report_format_group = GroupBox()
        report_format_group.Text = "Step 2: Report Format"
        report_format_group.Location = Point(int(10 * sf), y_pos)
        report_format_group.Size = Size(int(580 * sf), int(100 * sf))
        panel.Controls.Add(report_format_group)

        self.rb_na = RadioButton()
        self.rb_na.Text = "IOTA North America (V5.6.12r)"
        self.rb_na.Location = Point(int(20 * sf), int(22 * sf))
        self.rb_na.Size = Size(int(300 * sf), int(22 * sf))
        self.rb_na.Checked = True
        self.rb_na.CheckedChanged += self._on_report_format_changed
        report_format_group.Controls.Add(self.rb_na)

        self.rb_tt = RadioButton()
        self.rb_tt.Text = "Trans-Tasman / RASNZ (V4.1.2.G)"
        self.rb_tt.Location = Point(int(20 * sf), int(47 * sf))
        self.rb_tt.Size = Size(int(300 * sf), int(22 * sf))
        self.rb_tt.CheckedChanged += self._on_report_format_changed
        report_format_group.Controls.Add(self.rb_tt)

        self.rb_sodis = RadioButton()
        self.rb_sodis.Text = "IOTA-ES / SODIS (Form 2.03)"
        self.rb_sodis.Location = Point(int(20 * sf), int(72 * sf))
        self.rb_sodis.Size = Size(int(300 * sf), int(22 * sf))
        self.rb_sodis.CheckedChanged += self._on_report_format_changed
        report_format_group.Controls.Add(self.rb_sodis)

        # Pre-select from saved preference
        if self.config is not None:
            last_type = self.config.get_last_report_type()
            if last_type == 'trans_tasman':
                self.rb_tt.Checked = True
            elif last_type == 'sodis':
                self.rb_sodis.Checked = True
            else:
                self.rb_na.Checked = True

        y_pos += int(110 * sf)

        # ===== STEP 3: EQUIPMENT =====
        equipment_group = GroupBox()
        equipment_group.Text = "Step 3: Equipment"
        equipment_group.Location = Point(int(10 * sf), y_pos)
        equipment_group.Size = Size(int(580 * sf), int(115 * sf))
        panel.Controls.Add(equipment_group)

        lbl_telescope = Label()
        lbl_telescope.Text = "Telescope:"
        lbl_telescope.Location = Point(int(15 * sf), int(28 * sf))
        lbl_telescope.Size = Size(int(90 * sf), int(20 * sf))
        equipment_group.Controls.Add(lbl_telescope)

        self.combo_telescope = ComboBox()
        self.combo_telescope.Location = Point(int(115 * sf), int(26 * sf))
        self.combo_telescope.Size = Size(int(340 * sf), int(25 * sf))
        self.combo_telescope.DropDownStyle = ComboBoxStyle.DropDownList
        equipment_group.Controls.Add(self.combo_telescope)

        btn_manage_telescope = Button()
        btn_manage_telescope.Text = "Manage..."
        btn_manage_telescope.Location = Point(int(465 * sf), int(24 * sf))
        btn_manage_telescope.Size = Size(int(100 * sf), int(25 * sf))
        btn_manage_telescope.Click += self._manage_telescopes_click
        equipment_group.Controls.Add(btn_manage_telescope)

        lbl_camera = Label()
        lbl_camera.Text = "Camera:"
        lbl_camera.Location = Point(int(15 * sf), int(57 * sf))
        lbl_camera.Size = Size(int(90 * sf), int(20 * sf))
        equipment_group.Controls.Add(lbl_camera)

        self.combo_camera = ComboBox()
        self.combo_camera.Location = Point(int(115 * sf), int(55 * sf))
        self.combo_camera.Size = Size(int(340 * sf), int(25 * sf))
        self.combo_camera.DropDownStyle = ComboBoxStyle.DropDownList
        equipment_group.Controls.Add(self.combo_camera)

        btn_manage_camera = Button()
        btn_manage_camera.Text = "Manage..."
        btn_manage_camera.Location = Point(int(465 * sf), int(53 * sf))
        btn_manage_camera.Size = Size(int(100 * sf), int(25 * sf))
        btn_manage_camera.Click += self._manage_cameras_click
        equipment_group.Controls.Add(btn_manage_camera)

        lbl_camera_note = Label()
        lbl_camera_note.Text = "Cameras must be configured for each report format separately."
        lbl_camera_note.Location = Point(int(15 * sf), int(88 * sf))
        lbl_camera_note.Size = Size(int(550 * sf), int(18 * sf))
        lbl_camera_note.ForeColor = Color.Gray
        equipment_group.Controls.Add(lbl_camera_note)

        self._load_equipment()

        # Auto-trigger elevation lookup if elevation was not in the event data.
        if getattr(self, '_elevation_needs_lookup', False):
            self._auto_lookup_elevation(latitude, longitude)

        y_pos += int(125 * sf)

        # Buttons
        btn_panel = Panel()
        btn_panel.Height = int(40 * sf)
        btn_panel.Location = Point(0, y_pos)
        btn_panel.Width = int(600 * sf)
        panel.Controls.Add(btn_panel)

        btn_confirm = Button()
        btn_confirm.Text = "Next →"
        btn_confirm.Size = Size(int(100 * sf), int(28 * sf))
        btn_confirm.Location = Point(int(380 * sf), int(6 * sf))
        btn_confirm.Click += self.confirm_click
        btn_panel.Controls.Add(btn_confirm)

        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Size = Size(int(100 * sf), int(28 * sf))
        btn_cancel.Location = Point(int(270 * sf), int(6 * sf))
        btn_cancel.Click += self.cancel_click
        btn_panel.Controls.Add(btn_cancel)
        
        # Apply theme
        theme_colors = theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def lookup_location_click(self, sender, e):
        """Look up city/town name from coordinates using reverse geocoding"""
        original_text = sender.Text
        try:
            # Get current lat/lon values
            latitude = float(self.txt_latitude.Text)
            longitude = float(self.txt_longitude.Text)
            
            # Show working message
            sender.Text = "Looking up..."
            sender.Enabled = False
            self.Refresh()
            
            # Import location lookup function
            from utils import get_location_name_from_coordinates
            
            # Lookup location name
            location_name = get_location_name_from_coordinates(latitude, longitude, verbose=False)
            
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
        except Exception:
            MessageBox.Show("No Internet Connection or location service unavailable.", 
                          "Location Lookup Failed", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            sender.Text = original_text
            sender.Enabled = True
    
    def _auto_lookup_elevation(self, latitude, longitude):
        """Silently look up elevation on form load; populate field if successful."""
        try:
            from utils import get_elevation_from_coordinates
            elevation = get_elevation_from_coordinates(latitude, longitude, verbose=False)
            if elevation is not None:
                self.txt_elevation.Text = str(round(elevation, 1))
        except Exception:
            pass  # Leave blank; user can use the Lookup Elevation button manually.

    def lookup_elevation_click(self, sender, e):
        """Look up elevation from coordinates using online API"""
        original_text = sender.Text
        try:
            # Get current lat/lon values
            latitude = float(self.txt_latitude.Text)
            longitude = float(self.txt_longitude.Text)
            
            # Show working message
            sender.Text = "Looking up..."
            sender.Enabled = False
            self.Refresh()
            
            # Import elevation lookup function
            from utils import get_elevation_from_coordinates
            
            # Lookup elevation
            elevation = get_elevation_from_coordinates(latitude, longitude, verbose=False)
            
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
        except Exception:
            MessageBox.Show("No Internet Connection or elevation service unavailable.", 
                          "Elevation Lookup Failed", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            sender.Text = original_text
            sender.Enabled = True
    
    def confirm_click(self, sender, e):
        """User confirmed the location, equipment, and report format"""
        try:
            # Validate and store the entered values
            self.latitude = float(self.txt_latitude.Text)
            self.longitude = float(self.txt_longitude.Text)
            self.elevation = float(self.txt_elevation.Text) if self.txt_elevation.Text.strip() else None
            self.obs_location = self.txt_obs_location.Text.strip()

            # Check all required fields are present.
            missing = []
            if not self.obs_location:
                missing.append("Observing Location")
            if self.elevation is None:
                missing.append("Elevation")

            if missing:
                msg = (
                    "The following required fields are empty:\n\n"
                    + "\n".join("  \u2022 " + m for m in missing)
                    + "\n\nIf you continue without filling these in you will need to "
                    "enter them manually in a later form (not recommended).\n\n"
                    "Do you want to go back and complete the missing fields?"
                )
                result = MessageBox.Show(
                    msg,
                    "Missing Required Fields",
                    MessageBoxButtons.YesNo,
                    MessageBoxIcon.Warning,
                )
                if result == DialogResult.Yes:
                    return  # Return to form
                # User chose to continue anyway — use safe defaults
                if self.elevation is None:
                    self.elevation = 0.0
                if not self.obs_location:
                    self.obs_location = ''

            # Store equipment IDs
            self._telescope_id = self._get_selected_telescope_id()
            self._camera_id = self._get_selected_camera_id()

            # Store report type
            if self.rb_tt.Checked:
                self._report_type = 'trans_tasman'
            elif self.rb_sodis.Checked:
                self._report_type = 'sodis'
            else:
                self._report_type = 'north_america'

            # Save report type preference
            if self.config is not None:
                self.config.set_last_report_type(self._report_type)

            self.confirmed = True
            self.DialogResult = DialogResult.OK
            self.Close()
        except ValueError:
            MessageBox.Show("Please enter valid numeric values for latitude, longitude and elevation.",
                          "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning)
    
    def cancel_click(self, sender, e):
        """User cancelled"""
        self.confirmed = False
        self.DialogResult = DialogResult.Cancel
        self.Close()

    def _load_equipment(self):
        """Load telescopes and cameras into dropdowns. Cameras are filtered by selected report format."""
        if self.config is None:
            self.combo_telescope.Items.Add("No config available")
            self.combo_telescope.SelectedIndex = 0
            self.combo_telescope.Enabled = False
            self.combo_camera.Items.Add("No config available")
            self.combo_camera.SelectedIndex = 0
            self.combo_camera.Enabled = False
            return

        telescopes = self.config.get_telescopes()
        active_telescope = self.config.get_active_telescope()
        active_tel_id = active_telescope.get('id') if active_telescope else None
        if not telescopes:
            self.combo_telescope.Items.Add("No telescopes configured - click Manage...")
            self.combo_telescope.SelectedIndex = 0
            self.combo_telescope.Enabled = False
        else:
            self.combo_telescope.Enabled = True
            sel_idx = 0
            for i, t in enumerate(telescopes):
                name = t.get('name', 'Unnamed')
                if t.get('id') == active_tel_id:
                    name = "\u2605 " + name
                    sel_idx = i
                self.combo_telescope.Items.Add(name)
            self.combo_telescope.SelectedIndex = sel_idx

        # Determine current report format for camera filtering
        if hasattr(self, 'rb_tt') and self.rb_tt.Checked:
            fmt_key = 'TT'
        elif hasattr(self, 'rb_sodis') and self.rb_sodis.Checked:
            fmt_key = 'SODIS'
        else:
            fmt_key = 'NA'

        all_cameras = self.config.get_cameras()
        # Filter to cameras matching the selected report format
        self._filtered_cameras = [c for c in all_cameras if c.get('report_type', 'NA') == fmt_key]
        active_camera = self.config.get_active_camera()
        active_cam_id = active_camera.get('id') if active_camera else None
        if not self._filtered_cameras:
            self.combo_camera.Items.Add("No cameras configured for this format - click Manage...")
            self.combo_camera.SelectedIndex = 0
            self.combo_camera.Enabled = False
        else:
            self.combo_camera.Enabled = True
            sel_idx = 0
            for i, c in enumerate(self._filtered_cameras):
                name = c.get('name', 'Unnamed')
                if c.get('id') == active_cam_id:
                    name = "\u2605 " + name
                    sel_idx = i
                self.combo_camera.Items.Add(name)
            self.combo_camera.SelectedIndex = sel_idx

    def _get_selected_telescope_id(self):
        if self.config is None:
            return None
        idx = self.combo_telescope.SelectedIndex
        telescopes = self.config.get_telescopes()
        if 0 <= idx < len(telescopes):
            return telescopes[idx].get('id')
        return None

    def _get_selected_camera_id(self):
        if self.config is None:
            return None
        idx = self.combo_camera.SelectedIndex
        filtered = getattr(self, '_filtered_cameras', None)
        if filtered is not None:
            if 0 <= idx < len(filtered):
                return filtered[idx].get('id')
            return None
        # Fallback: unfiltered list (shouldn't normally be reached)
        cameras = self.config.get_cameras()
        if 0 <= idx < len(cameras):
            return cameras[idx].get('id')
        return None

    def _on_report_format_changed(self, sender, e):
        """Refresh the camera dropdown when the report format selection changes."""
        if not sender.Checked:
            return
        if not hasattr(self, 'combo_camera'):
            return
        self.combo_camera.Items.Clear()
        self._load_equipment_cameras_only()

    def _load_equipment_cameras_only(self):
        """Refresh only the camera dropdown based on the current report format."""
        if self.config is None:
            return
        if hasattr(self, 'rb_tt') and self.rb_tt.Checked:
            fmt_key = 'TT'
        elif hasattr(self, 'rb_sodis') and self.rb_sodis.Checked:
            fmt_key = 'SODIS'
        else:
            fmt_key = 'NA'

        all_cameras = self.config.get_cameras()
        self._filtered_cameras = [c for c in all_cameras if c.get('report_type', 'NA') == fmt_key]
        active_camera = self.config.get_active_camera()
        active_cam_id = active_camera.get('id') if active_camera else None
        if not self._filtered_cameras:
            self.combo_camera.Items.Add("No cameras configured for this format - click Manage...")
            self.combo_camera.SelectedIndex = 0
            self.combo_camera.Enabled = False
        else:
            self.combo_camera.Enabled = True
            sel_idx = 0
            for i, c in enumerate(self._filtered_cameras):
                name = c.get('name', 'Unnamed')
                if c.get('id') == active_cam_id:
                    name = "\u2605 " + name
                    sel_idx = i
                self.combo_camera.Items.Add(name)
            self.combo_camera.SelectedIndex = sel_idx

    def _manage_telescopes_click(self, sender, e):
        if self.config is None:
            return
        from equipment_dialogs import TelescopeManagerDialog
        dialog = TelescopeManagerDialog(self.config, self.theme_manager)
        dialog.ShowDialog()
        self.combo_telescope.Items.Clear()
        self.combo_camera.Items.Clear()
        self._load_equipment()

    def _manage_cameras_click(self, sender, e):
        if self.config is None:
            return
        from equipment_dialogs import CameraManagerDialog
        dialog = CameraManagerDialog(self.config, self.theme_manager)
        dialog.ShowDialog()
        self.combo_telescope.Items.Clear()
        self.combo_camera.Items.Clear()
        self._load_equipment()

    def get_location(self):
        """Get the entered location values"""
        return {
            'latitude': self.latitude if hasattr(self, 'latitude') else 0.0,
            'longitude': self.longitude if hasattr(self, 'longitude') else 0.0,
            'elevation': self.elevation if hasattr(self, 'elevation') else 0.0,
            'obs_location': self.obs_location if hasattr(self, 'obs_location') else ''
        }

    def get_telescope_id(self):
        return getattr(self, '_telescope_id', None)

    def get_camera_id(self):
        return getattr(self, '_camera_id', None)

    def get_report_type(self):
        return getattr(self, '_report_type', 'north_america')
    