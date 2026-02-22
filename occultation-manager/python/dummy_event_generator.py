"""
Dummy Event Generator for Testing
Generates realistic test occultation events
"""

import json
import os
import random
from datetime import datetime, timedelta
from System.Windows.Forms import (
    Form, Label, TextBox, Button, ComboBox, RadioButton, GroupBox,
    DialogResult, MessageBox, MessageBoxButtons, MessageBoxIcon,
    DockStyle, AnchorStyles, FormBorderStyle, FormStartPosition
)
from System.Drawing import Point, Size, SystemColors
from theme import apply_theme_to_control

class DummyEventGeneratorDialog(Form):
    """Dialog for configuring dummy event generation"""
    
    def __init__(self, config, theme_manager=None):
        self.config = config
        self.theme_manager = theme_manager
        self.result_params = None
        
        # Get scale factor
        self.sf = 1.0
        if theme_manager and hasattr(theme_manager, 'scale_factor'):
            self.sf = theme_manager.scale_factor
        
        self._init_ui()
        
        # Apply theme if available
        if self.theme_manager:
            theme_colors = self.theme_manager.get_current_theme()
            apply_theme_to_control(self, theme_colors)
    
    def _init_ui(self):
        """Initialize the UI"""
        sf = self.sf
        
        self.Text = "Generate Dummy Events"
        self.Size = Size(int(500 * sf), int(450 * sf))
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.StartPosition = FormStartPosition.CenterParent
        
        y_pos = int(20 * sf)
        
        # Number of events
        lbl_count = Label()
        lbl_count.Text = "Number of events:"
        lbl_count.Location = Point(int(20 * sf), y_pos)
        lbl_count.Size = Size(int(150 * sf), int(20 * sf))
        self.Controls.Add(lbl_count)
        
        self.txt_count = TextBox()
        self.txt_count.Location = Point(int(180 * sf), y_pos)
        self.txt_count.Size = Size(int(100 * sf), int(20 * sf))
        self.txt_count.Text = "5"
        self.Controls.Add(self.txt_count)
        
        y_pos += int(35 * sf)
        
        # Start time option group
        grp_start = GroupBox()
        grp_start.Text = "Start Time"
        grp_start.Location = Point(int(20 * sf), y_pos)
        grp_start.Size = Size(int(440 * sf), int(120 * sf))
        self.Controls.Add(grp_start)
        
        # Radio button for UTC time
        self.rb_utc = RadioButton()
        self.rb_utc.Text = "UTC Start Time:"
        self.rb_utc.Location = Point(int(10 * sf), int(25 * sf))
        self.rb_utc.Size = Size(int(150 * sf), int(20 * sf))
        self.rb_utc.Checked = False
        self.rb_utc.CheckedChanged += self._on_start_option_changed
        grp_start.Controls.Add(self.rb_utc)
        
        self.txt_utc = TextBox()
        self.txt_utc.Location = Point(int(170 * sf), int(23 * sf))
        self.txt_utc.Size = Size(int(240 * sf), int(20 * sf))
        self.txt_utc.Text = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        self.txt_utc.Enabled = False
        grp_start.Controls.Add(self.txt_utc)
        
        # Radio button for minutes from now
        self.rb_minutes = RadioButton()
        self.rb_minutes.Text = "Minutes from now:"
        self.rb_minutes.Location = Point(int(10 * sf), int(60 * sf))
        self.rb_minutes.Size = Size(int(150 * sf), int(20 * sf))
        self.rb_minutes.Checked = True
        self.rb_minutes.CheckedChanged += self._on_start_option_changed
        grp_start.Controls.Add(self.rb_minutes)
        
        self.txt_minutes = TextBox()
        self.txt_minutes.Location = Point(int(170 * sf), int(58 * sf))
        self.txt_minutes.Size = Size(int(100 * sf), int(20 * sf))
        self.txt_minutes.Text = "30"
        self.txt_minutes.Enabled = True
        grp_start.Controls.Add(self.txt_minutes)
        
        lbl_minutes_help = Label()
        lbl_minutes_help.Text = "(time until first event)"
        lbl_minutes_help.Location = Point(int(280 * sf), int(60 * sf))
        lbl_minutes_help.Size = Size(int(150 * sf), int(20 * sf))
        grp_start.Controls.Add(lbl_minutes_help)
        
        y_pos += int(135 * sf)
        
        # Interval between events
        lbl_interval = Label()
        lbl_interval.Text = "Interval (minutes):"
        lbl_interval.Location = Point(int(20 * sf), y_pos)
        lbl_interval.Size = Size(int(150 * sf), int(20 * sf))
        self.Controls.Add(lbl_interval)
        
        self.txt_interval = TextBox()
        self.txt_interval.Location = Point(int(180 * sf), y_pos)
        self.txt_interval.Size = Size(int(100 * sf), int(20 * sf))
        self.txt_interval.Text = "15"
        self.Controls.Add(self.txt_interval)
        
        y_pos += int(35 * sf)
        
        # Location group
        grp_location = GroupBox()
        grp_location.Text = "Observer Location"
        grp_location.Location = Point(int(20 * sf), y_pos)
        grp_location.Size = Size(int(440 * sf), int(120 * sf))
        self.Controls.Add(grp_location)
        
        lbl_lat = Label()
        lbl_lat.Text = "Latitude (deg):"
        lbl_lat.Location = Point(int(10 * sf), int(25 * sf))
        lbl_lat.Size = Size(int(100 * sf), int(20 * sf))
        grp_location.Controls.Add(lbl_lat)
        
        self.txt_latitude = TextBox()
        self.txt_latitude.Location = Point(int(120 * sf), int(23 * sf))
        self.txt_latitude.Size = Size(int(100 * sf), int(20 * sf))
        self.txt_latitude.Text = "-37.8136"
        grp_location.Controls.Add(self.txt_latitude)
        
        lbl_lon = Label()
        lbl_lon.Text = "Longitude (deg):"
        lbl_lon.Location = Point(int(10 * sf), int(55 * sf))
        lbl_lon.Size = Size(int(100 * sf), int(20 * sf))
        grp_location.Controls.Add(lbl_lon)
        
        self.txt_longitude = TextBox()
        self.txt_longitude.Location = Point(int(120 * sf), int(53 * sf))
        self.txt_longitude.Size = Size(int(100 * sf), int(20 * sf))
        self.txt_longitude.Text = "144.9631"
        grp_location.Controls.Add(self.txt_longitude)
        
        lbl_station = Label()
        lbl_station.Text = "Station Name:"
        lbl_station.Location = Point(int(10 * sf), int(85 * sf))
        lbl_station.Size = Size(int(100 * sf), int(20 * sf))
        grp_location.Controls.Add(lbl_station)
        
        self.txt_station = TextBox()
        self.txt_station.Location = Point(int(120 * sf), int(83 * sf))
        self.txt_station.Size = Size(int(300 * sf), int(20 * sf))
        self.txt_station.Text = "Test Station"
        grp_location.Controls.Add(self.txt_station)
        
        y_pos += int(135 * sf)
        
        # Buttons
        btn_generate = Button()
        btn_generate.Text = "Generate"
        btn_generate.Location = Point(int(200 * sf), y_pos)
        btn_generate.Size = Size(int(100 * sf), int(30 * sf))
        btn_generate.Click += self._on_generate_click
        self.Controls.Add(btn_generate)
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(int(320 * sf), y_pos)
        btn_cancel.Size = Size(int(100 * sf), int(30 * sf))
        btn_cancel.Click += self._on_cancel_click
        self.Controls.Add(btn_cancel)
        
        self.AcceptButton = btn_generate
        self.CancelButton = btn_cancel
    
    def _on_start_option_changed(self, sender, e):
        """Handle start option radio button changes"""
        self.txt_utc.Enabled = self.rb_utc.Checked
        self.txt_minutes.Enabled = self.rb_minutes.Checked
    
    def _on_generate_click(self, sender, e):
        """Handle Generate button click"""
        try:
            # Validate inputs
            count = int(self.txt_count.Text)
            if count < 1 or count > 100:
                MessageBox.Show("Number of events must be between 1 and 100", 
                              "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            interval = int(self.txt_interval.Text)
            if interval < 1:
                MessageBox.Show("Interval must be at least 1 minute", 
                              "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            latitude = float(self.txt_latitude.Text)
            if latitude < -90 or latitude > 90:
                MessageBox.Show("Latitude must be between -90 and 90", 
                              "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            longitude = float(self.txt_longitude.Text)
            if longitude < -180 or longitude > 180:
                MessageBox.Show("Longitude must be between -180 and 180", 
                              "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            station_name = self.txt_station.Text.strip()
            if not station_name:
                MessageBox.Show("Station name is required", 
                              "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            # Determine start time
            if self.rb_utc.Checked:
                try:
                    start_time = datetime.strptime(self.txt_utc.Text.strip(), "%Y-%m-%d %H:%M:%S")
                except:
                    MessageBox.Show("Invalid UTC time format. Use YYYY-MM-DD HH:MM:SS", 
                                  "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                    return
            else:
                minutes = int(self.txt_minutes.Text)
                if minutes < 0:
                    MessageBox.Show("Minutes from now must be positive", 
                                  "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                    return
                start_time = datetime.utcnow() + timedelta(minutes=minutes)
            
            # Store parameters
            self.result_params = {
                'count': count,
                'start_time': start_time,
                'interval': interval,
                'latitude': latitude,
                'longitude': longitude,
                'station_name': station_name
            }
            
            self.DialogResult = DialogResult.OK
            self.Close()
            
        except ValueError as ex:
            MessageBox.Show(f"Invalid input: {ex}", "Invalid Input", 
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
    
    def _on_cancel_click(self, sender, e):
        """Handle Cancel button click"""
        self.DialogResult = DialogResult.Cancel
        self.Close()


class DummyEventGenerator:
    """Generates realistic dummy occultation events"""
    
    @staticmethod
    def calculate_sidereal_time(utc_time, longitude):
        """
        Calculate Local Sidereal Time (LST) in hours
        
        Args:
            utc_time: datetime object in UTC
            longitude: observer longitude in degrees (East positive)
        
        Returns:
            LST in hours (0-24)
        """
        # Julian Date
        a = (14 - utc_time.month) // 12
        y = utc_time.year + 4800 - a
        m = utc_time.month + 12 * a - 3
        jd = utc_time.day + (153 * m + 2) // 5 + 365 * y + y // 4 - y // 100 + y // 400 - 32045
        jd += (utc_time.hour - 12) / 24.0 + utc_time.minute / 1440.0 + utc_time.second / 86400.0
        
        # Days since J2000.0
        d = jd - 2451545.0
        
        # Greenwich Mean Sidereal Time (GMST) in hours
        gmst = 18.697374558 + 24.06570982441908 * d
        gmst = gmst % 24
        
        # Local Sidereal Time (LST)
        lst = gmst + longitude / 15.0
        lst = lst % 24
        
        return lst
    
    @staticmethod
    def generate_events(params, config):
        """
        Generate dummy events
        
        Args:
            params: Dictionary with generation parameters
            config: ConfigManager instance
        
        Returns:
            List of event dictionaries
        """
        events = []
        current_time = params['start_time']
        
        for i in range(params['count']):
            event_num = i + 1
            
            # Calculate LST at event time
            lst = DummyEventGenerator.calculate_sidereal_time(current_time, params['longitude'])
            
            # Generate RA near LST (within ±3 hours for good visibility)
            # This ensures the object is near meridian and well-placed
            ra_offset = random.uniform(-3.0, 3.0)
            ra = (lst + ra_offset) % 24
            
            # Use DEC near zero as requested (±20 degrees)
            dec = random.uniform(-20.0, 20.0)
            
            # Generate other random but sensible values
            star_mag = random.uniform(8.0, 13.0)
            mag_drop = random.uniform(1.5, 6.0)
            comb_mag = star_mag + 0.5  # Combined magnitude slightly fainter
            
            event_duration = random.uniform(5.0, 25.0)
            event_uncertainty = random.uniform(1.0, 5.0)
            
            # Calculate recording duration (base + uncertainty)
            recording_duration = int(config.config.get('base_duration', 60) + event_uncertainty * 2)
            
            # Calculate star altitude (rough estimate)
            # For simplicity, assume objects near meridian have good altitude
            star_alt = random.uniform(30.0, 70.0)
            star_az = random.uniform(0.0, 360.0)
            
            # Calculate exposure based on magnitude
            mag_for_40ms = float(config.config.get('mag_for_40ms_exposure', 12.0))
            if star_mag <= mag_for_40ms - 2:
                exposure = 0.02  # 20ms for bright stars
            elif star_mag <= mag_for_40ms:
                exposure = 0.04  # 40ms
            elif star_mag <= mag_for_40ms + 1:
                exposure = 0.08  # 80ms
            else:
                exposure = 0.16  # 160ms for faint stars
            
            exposure_ms = int(exposure * 1000)
            
            # Calculate derived times
            start_time = current_time - timedelta(seconds=recording_duration / 2)
            end_time = current_time + timedelta(seconds=recording_duration / 2)
            goto_time = start_time - timedelta(seconds=60)  # 1 minute before recording
            pre_goto_time = goto_time - timedelta(seconds=60)
            
            # Format times
            event_time_str = current_time.strftime("%Y-%m-%dT%H:%M:%S")
            start_time_str = start_time.strftime("%Y-%m-%dT%H:%M:%S")
            end_time_str = end_time.strftime("%Y-%m-%dT%H:%M:%S")
            goto_time_str = goto_time.strftime("%Y-%m-%dT%H:%M:%S")
            
            # Local times (same as UTC for simplicity in test events)
            event_time_local = current_time.strftime("%Y-%m-%d %H:%M:%S")
            start_time_local = start_time.strftime("%Y-%m-%d %H:%M:%S")
            goto_time_local = goto_time.strftime("%Y-%m-%d %H:%M:%S")
            pre_goto_time_local = pre_goto_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Generate star catalog ID
            ucac_zone = random.randint(100, 800)
            ucac_num = random.randint(100000, 999999)
            star_id = f"UCAC4-{ucac_zone}-{ucac_num}"
            
            # Create event dictionary
            event = {
                "id": f"TEST-{1000 + event_num}",
                "unique_id": f"test_{1000 + event_num}",
                "name": f"{current_time.strftime('%Y%m%d')} ({event_num}) Test{event_num} - {params['station_name']}",
                "object_name": f"({event_num}) Test{event_num}",
                "object_no": str(event_num),
                "event_time": event_time_str,
                "event_time_local": event_time_local,
                "start_time_str": start_time_str,
                "start_time_local": start_time_local,
                "end_time_str": end_time_str,
                "goto_time_str": goto_time_str,
                "goto_time_local": goto_time_local,
                "pre_goto_time_local": pre_goto_time_local,
                "recording_duration": recording_duration,
                "event_uncertainty": round(event_uncertainty, 1),
                "event_duration": round(event_duration, 1),
                "star_id": star_id,
                "star_mag": round(star_mag, 1),
                "comb_mag": round(comb_mag, 1),
                "mag_drop": round(mag_drop, 1),
                "star_alt": round(star_alt, 1),
                "star_az": round(star_az, 1),
                "ra": round(ra, 4),
                "dec": round(dec, 4),
                "station_name": params['station_name'],
                "latitude": params['latitude'],
                "longitude": params['longitude'],
                "elevation": 50,  # Default elevation
                "exposure": round(exposure, 3),
                "exposure_ms": exposure_ms,
                "gain_value": config.config.get('default_gain', 450),
                "owcloudurl": f"https://cloud.occultwatcher.net/event/TEST-{1000 + event_num}",
                "occelmnt_data": {}
            }
            
            events.append(event)
            
            # Increment time for next event
            current_time += timedelta(minutes=params['interval'])
        
        return events
    
    @staticmethod
    def save_events(events, config):
        """
        Append events to occultations.json and occultations_latest.json
        
        Args:
            events: List of event dictionaries
            config: ConfigManager instance
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Append to occultations.json (main file)
            occultations_file = config.get_occultations_file()
            occultations_path = config.get_full_file_path(occultations_file)
            
            existing_events = []
            if os.path.exists(occultations_path):
                with open(occultations_path, 'r', encoding='utf-8') as f:
                    existing_events = json.load(f)
            
            combined_events = existing_events + events
            
            with open(occultations_path, 'w', encoding='utf-8') as f:
                json.dump(combined_events, f, indent=2, ensure_ascii=False)
            
            # Append to occultations_latest.json
            latest_file = config.get_latest_occultations_file()
            latest_path = config.get_full_file_path(latest_file)
            
            existing_latest = []
            if os.path.exists(latest_path):
                with open(latest_path, 'r', encoding='utf-8') as f:
                    existing_latest = json.load(f)
            
            combined_latest = existing_latest + events
            
            with open(latest_path, 'w', encoding='utf-8') as f:
                json.dump(combined_latest, f, indent=2, ensure_ascii=False)
            
            return True
        
        except Exception as ex:
            print("Error saving events: {}".format(ex))
            return False
