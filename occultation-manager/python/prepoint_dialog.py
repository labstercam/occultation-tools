"""
Prepoint Dialog for Occultation Manager
Simple UI for prepoint calculations and mount control
"""

import clr
import math
import threading
from datetime import datetime, timedelta
from System.Windows.Forms import (
    Form, Label, Button, GroupBox, TextBox, ComboBox, CheckBox,
    DialogResult, MessageBox, MessageBoxButtons, MessageBoxIcon,
    DockStyle, AnchorStyles, FormBorderStyle, FormStartPosition
)
from System.Drawing import Point, Size, Color, Font, FontStyle, SystemColors
from System.Threading import CancellationToken
from theme import apply_theme_to_control


class PrepointDialog(Form):
    """Dialog for prepoint calculations and telescope control"""
    
    def __init__(self, config, theme_manager=None, sharpcap=None, event=None):
        """
        Initialize prepoint dialog
        
        Args:
            config: ConfigManager instance
            theme_manager: ThemeManager instance
            sharpcap: SharpCap instance (if available)
            event: OccultationEvent instance
        """
        self.config = config
        self.theme_manager = theme_manager
        self.sharpcap = sharpcap
        self.event = event
        
        # Initialize prepoint calculator with site coordinates
        # Get latitude/longitude from event or fail
        if event:
            self.latitude = getattr(event, 'latitude', 0.0)
            self.longitude = getattr(event, 'longitude', 0.0)
            # Fail if coordinates are zero (missing)
            if self.latitude == 0.0 or self.longitude == 0.0:
                MessageBox.Show("Event missing latitude/longitude coordinates. Cannot calculate prepoint.", 
                              "Missing Coordinates", MessageBoxButtons.OK, MessageBoxIcon.Error)
                self.latitude = None
                self.longitude = None
                self.calculator = None
                return
        else:
            # No event provided
            MessageBox.Show("No event selected. Cannot calculate prepoint.", 
                          "No Event", MessageBoxButtons.OK, MessageBoxIcon.Error)
            self.latitude = None
            self.longitude = None
            self.calculator = None
            return
        
        self.calculator = None
        self.mount_controller = None
        self._plate_solve_purpose = None
        
        # Store the plate_solve_purpose from sharpcap if available
        if sharpcap:
            self.mount_controller = PrepointMountController(sharpcap)
            if hasattr(sharpcap, 'PlateSolvePurpose'):
                self._plate_solve_purpose = sharpcap.PlateSolvePurpose
        
        self._init_ui()
        
        # Apply theme if available
        if self.theme_manager:
            theme_colors = self.theme_manager.get_current_theme()
            apply_theme_to_control(self, theme_colors)
    
    def _init_ui(self):
        """Initialize the UI"""
        self.Text = "Prepoint Calculator"
        self.Size = Size(500, 520)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.StartPosition = FormStartPosition.CenterParent
        
        # Calculate scale factor
        sf = 1.0
        if self.theme_manager and hasattr(self.theme_manager, 'scale_factor'):
            sf = self.theme_manager.scale_factor
        
        y_pos = 20
        
        # Target coordinates display
        lbl_target = Label()
        lbl_target.Text = "Target Coordinates:"
        lbl_target.Location = Point(20, y_pos)
        lbl_target.Size = Size(150, 20)
        self.Controls.Add(lbl_target)
        
        self.txt_target_coords = TextBox()
        self.txt_target_coords.Location = Point(180, y_pos)
        self.txt_target_coords.Size = Size(200, 20)
        self.txt_target_coords.ReadOnly = True
        self.txt_target_coords.BackColor = Color.LightGray
        self.Controls.Add(self.txt_target_coords)
        
        y_pos += 30
        
        # Prepoint coordinates display
        lbl_prepoint = Label()
        lbl_prepoint.Text = "Prepoint Coordinates:"
        lbl_prepoint.Location = Point(20, y_pos)
        lbl_prepoint.Size = Size(150, 20)
        self.Controls.Add(lbl_prepoint)
        
        self.txt_prepoint_coords = TextBox()
        self.txt_prepoint_coords.Location = Point(180, y_pos)
        self.txt_prepoint_coords.Size = Size(200, 20)
        self.txt_prepoint_coords.ReadOnly = True
        self.txt_prepoint_coords.BackColor = Color.LightGray
        self.Controls.Add(self.txt_prepoint_coords)
        
        y_pos += 30
        
        # Alt/Az display
        lbl_altaz = Label()
        lbl_altaz.Text = "Prepoint Alt/Az (Slew Position):"
        lbl_altaz.Location = Point(20, y_pos)
        lbl_altaz.Size = Size(150, 20)
        self.Controls.Add(lbl_altaz)
        
        self.txt_target_altaz = TextBox()
        self.txt_target_altaz.Location = Point(180, y_pos)
        self.txt_target_altaz.Size = Size(200, 20)
        self.txt_target_altaz.ReadOnly = True
        self.txt_target_altaz.BackColor = Color.LightGray
        self.Controls.Add(self.txt_target_altaz)
        
        y_pos += 30
        
        # Drift information group
        drift_group = GroupBox()
        drift_group.Text = "Drift Information"
        drift_group.Location = Point(20, y_pos)
        drift_group.Size = Size(460, 120)
        self.Controls.Add(drift_group)
        
        y_pos_in_group = 25
        
        lbl_drift_time = Label()
        lbl_drift_time.Text = "Time to drift through FOV:"
        lbl_drift_time.Location = Point(10, y_pos_in_group)
        lbl_drift_time.Size = Size(150, 20)
        drift_group.Controls.Add(lbl_drift_time)
        
        self.txt_drift_time = TextBox()
        self.txt_drift_time.Location = Point(170, y_pos_in_group)
        self.txt_drift_time.Size = Size(100, 20)
        self.txt_drift_time.ReadOnly = True
        self.txt_drift_time.BackColor = Color.LightGray
        drift_group.Controls.Add(self.txt_drift_time)
        
        y_pos_in_group += 30
        
        lbl_alt_rate = Label()
        lbl_alt_rate.Text = "Altitude drift rate:"
        lbl_alt_rate.Location = Point(10, y_pos_in_group)
        lbl_alt_rate.Size = Size(150, 20)
        drift_group.Controls.Add(lbl_alt_rate)
        
        self.txt_alt_rate = TextBox()
        self.txt_alt_rate.Location = Point(170, y_pos_in_group)
        self.txt_alt_rate.Size = Size(100, 20)
        self.txt_alt_rate.ReadOnly = True
        self.txt_alt_rate.BackColor = Color.LightGray
        drift_group.Controls.Add(self.txt_alt_rate)
        
        lbl_az_rate = Label()
        lbl_az_rate.Text = "Azimuth drift rate:"
        lbl_az_rate.Location = Point(280, y_pos_in_group)
        lbl_az_rate.Size = Size(150, 20)
        drift_group.Controls.Add(lbl_az_rate)
        
        self.txt_az_rate = TextBox()
        self.txt_az_rate.Location = Point(440, y_pos_in_group)
        self.txt_az_rate.Size = Size(100, 20)
        self.txt_az_rate.ReadOnly = True
        self.txt_az_rate.BackColor = Color.LightGray
        drift_group.Controls.Add(self.txt_az_rate)
        
        y_pos_in_group += 30
        
        lbl_time_to_event = Label()
        lbl_time_to_event.Text = "Time to event:"
        lbl_time_to_event.Location = Point(10, y_pos_in_group)
        lbl_time_to_event.Size = Size(150, 20)
        drift_group.Controls.Add(lbl_time_to_event)
        
        self.txt_time_to_event = TextBox()
        self.txt_time_to_event.Location = Point(170, y_pos_in_group)
        self.txt_time_to_event.Size = Size(100, 20)
        self.txt_time_to_event.ReadOnly = True
        self.txt_time_to_event.BackColor = Color.LightGray
        drift_group.Controls.Add(self.txt_time_to_event)
        
        y_pos += 130
        
        # Mount control buttons
        btn_calculate = Button()
        btn_calculate.Text = "Calculate Prepoint"
        btn_calculate.Location = Point(20, y_pos)
        btn_calculate.Size = Size(120, 30)
        btn_calculate.Click += self.calculate_prepoint
        self.Controls.Add(btn_calculate)
        
        btn_goto = Button()
        btn_goto.Text = "Goto Prepoint"
        btn_goto.Location = Point(160, y_pos)
        btn_goto.Size = Size(120, 30)
        btn_goto.Click += self.goto_prepoint
        btn_goto.BackColor = Color.LightBlue
        self.Controls.Add(btn_goto)
        
        btn_refine_prepoint = Button()
        btn_refine_prepoint.Text = "Refine Pre-Point"
        btn_refine_prepoint.Location = Point(300, y_pos)
        btn_refine_prepoint.Size = Size(120, 30)
        btn_refine_prepoint.Click += self.refine_prepoint
        btn_refine_prepoint.BackColor = Color.LightGreen
        self.Controls.Add(btn_refine_prepoint)
        
        y_pos += 40
        
        # Prepoint offset input
        lbl_offset = Label()
        lbl_offset.Text = "Prepoint Offset (seconds):"
        lbl_offset.Location = Point(20, y_pos)
        lbl_offset.Size = Size(150, 20)
        self.Controls.Add(lbl_offset)
        
        self.txt_offset = TextBox()
        self.txt_offset.Location = Point(180, y_pos)
        self.txt_offset.Size = Size(50, 20)
        self.txt_offset.Text = "10"
        self.Controls.Add(self.txt_offset)
        
        y_pos += 30
        
        # Mount status
        lbl_mount_status = Label()
        lbl_mount_status.Text = "Mount Status:"
        lbl_mount_status.Location = Point(20, y_pos)
        lbl_mount_status.Size = Size(150, 20)
        self.Controls.Add(lbl_mount_status)
        
        self.txt_mount_status = Label()
        self.txt_mount_status.Location = Point(180, y_pos)
        self.txt_mount_status.Size = Size(200, 20)
        if self.mount_controller and self.mount_controller.is_mount_available():
            self.txt_mount_status.Text = "Mount Connected"
            self.txt_mount_status.ForeColor = Color.Green
        else:
            self.txt_mount_status.Text = "No Mount Connected"
            self.txt_mount_status.ForeColor = Color.Red
        self.Controls.Add(self.txt_mount_status)
        
        y_pos += 30
        
        # Refine status (distance to prepoint target)
        lbl_refine_status = Label()
        lbl_refine_status.Text = "Distance to Prepoint:"
        lbl_refine_status.Location = Point(20, y_pos)
        lbl_refine_status.Size = Size(150, 20)
        self.Controls.Add(lbl_refine_status)
        
        self.txt_refine_status = Label()
        self.txt_refine_status.Location = Point(180, y_pos)
        self.txt_refine_status.Size = Size(280, 20)
        self.txt_refine_status.Text = "Not yet refined"
        self.txt_refine_status.ForeColor = Color.Blue
        self.Controls.Add(self.txt_refine_status)
        
        y_pos += 30
        
        # Direction indicator - Alt/Az movement
        lbl_direction_altaz = Label()
        lbl_direction_altaz.Text = "Alt/Az Move:"
        lbl_direction_altaz.Location = Point(20, y_pos)
        lbl_direction_altaz.Size = Size(150, 20)
        self.Controls.Add(lbl_direction_altaz)
        
        self.txt_direction_altaz = Label()
        self.txt_direction_altaz.Location = Point(180, y_pos)
        self.txt_direction_altaz.Size = Size(280, 20)
        self.txt_direction_altaz.Text = "Calculate prepoint, then Refine"
        self.txt_direction_altaz.ForeColor = Color.Blue
        self.Controls.Add(self.txt_direction_altaz)
        
        y_pos += 24
        
        # Direction indicator - Ra/Dec movement
        lbl_direction_radec = Label()
        lbl_direction_radec.Text = "RA/Dec Move:"
        lbl_direction_radec.Location = Point(20, y_pos)
        lbl_direction_radec.Size = Size(150, 20)
        self.Controls.Add(lbl_direction_radec)
        
        self.txt_direction_radec = Label()
        self.txt_direction_radec.Location = Point(180, y_pos)
        self.txt_direction_radec.Size = Size(280, 20)
        self.txt_direction_radec.Text = "Calculate prepoint, then Refine"
        self.txt_direction_radec.ForeColor = Color.Blue
        self.Controls.Add(self.txt_direction_radec)
        
        y_pos += 40
        
        # OK/Cancel buttons
        btn_ok = Button()
        btn_ok.Text = "OK"
        btn_ok.Location = Point(200, y_pos)
        btn_ok.Size = Size(80, 30)
        btn_ok.Click += self.close_dialog
        self.Controls.Add(btn_ok)
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(300, y_pos)
        btn_cancel.Size = Size(80, 30)
        btn_cancel.Click += self.close_dialog
        self.Controls.Add(btn_cancel)
        
        # Initialize calculator
        if self.latitude and self.longitude:
            self.calculator = PrepointCalculator(self.latitude, self.longitude)
        
        # Populate initial data if event is provided
        if self.event:
            self.update_target_coordinates()
    
    def update_target_coordinates(self):
        """Update target coordinates display"""
        if self.event and self.calculator:
            target_ra = self.event.ra
            target_dec = self.event.dec
            
            # Format RA/DEC
            ra_str = "{:.4f}h".format(target_ra)
            dec_str = "{:.4f}°".format(target_dec)
            self.txt_target_coords.Text = "RA: {}, DEC: {}".format(ra_str, dec_str)
            
            # Don't calculate Alt/Az yet - will be calculated after prepoint calculation
            # Alt/Az at event time will be replaced with Alt/Az at prepoint time after calculation
            self.txt_target_altaz.Text = "Calculate prepoint first"
            
            # Debug: Compare with event grid Alt/Az if available
            event_alt = getattr(self.event, 'star_alt', None)
            event_az = getattr(self.event, 'star_az', None)
            if event_alt and event_az:
                # Calculate Alt/Az at event time for debugging
                event_time = datetime.strptime(self.event.event_time, "%Y-%m-%dT%H:%M:%S")
                alt, az = self.calculator.ra_dec_to_altaz(target_ra, target_dec, event_time)
                print("[Alt/Az Debug] Event grid Alt/Az: Alt={:.1f}°, Az={:.1f}°".format(event_alt, event_az))
                print("[Alt/Az Debug] Calculated Alt/Az: Alt={:.1f}°, Az={:.1f}°".format(alt, az))
                print("[Alt/Az Debug] Difference: Alt diff={:.1f}°, Az diff={:.1f}°".format(alt - event_alt, az - event_az))
                print("[Alt/Az Debug] Site coordinates: lat={:.4f}°, lon={:.4f}°".format(self.latitude, self.longitude))
    
    def calculate_prepoint(self, sender, e):
        """Calculate prepoint coordinates"""
        if not self.event or not self.calculator:
            MessageBox.Show("No event selected or calculator not initialized", 
                          "Prepoint Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            return
        
        try:
            offset_seconds = int(self.txt_offset.Text)
            if offset_seconds <= 0:
                MessageBox.Show("Offset must be positive seconds", 
                              "Invalid Input", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            target_ra = self.event.ra
            target_dec = self.event.dec
            event_time = datetime.strptime(self.event.event_time, "%Y-%m-%dT%H:%M:%S")
            
            # Get event Alt/Az if available
            event_alt = getattr(self.event, 'star_alt', None)
            event_az = getattr(self.event, 'star_az', None)
            
            # Calculate prepoint coordinates
            prepoint_ra, prepoint_dec, prepoint_time = self.calculator.calculate_prepoint(
                target_ra, target_dec, event_time, offset_seconds, event_alt, event_az
            )
            
            # Format prepoint coordinates
            ra_str = "{:.4f}h".format(prepoint_ra)
            dec_str = "{:.4f}°".format(prepoint_dec)
            time_str = prepoint_time.strftime("%H:%M:%S")
            self.txt_prepoint_coords.Text = "RA: {}, DEC: {} at {}".format(ra_str, dec_str, time_str)
            
            # Calculate drift information
            drift_info = self.calculator.calculate_drift_info(
                target_ra, target_dec, event_time, fov_width_deg=1.0, fov_height_deg=1.0, prepoint_offset_seconds=offset_seconds
            )
            
            self.txt_drift_time.Text = "{:.1f} min".format(drift_info['drift_time_minutes'])
            self.txt_alt_rate.Text = "{:.3f}°/s".format(drift_info['alt_rate_deg_per_sec'])
            self.txt_az_rate.Text = "{:.3f}°/s".format(drift_info['az_rate_deg_per_sec'])
            self.txt_time_to_event.Text = "{:.0f} s".format(drift_info['time_to_event_seconds'])
            
            # Store calculated prepoint for later use
            self.prepoint_ra = prepoint_ra
            self.prepoint_dec = prepoint_dec
            self.prepoint_alt, self.prepoint_az = self.calculator.ra_dec_to_altaz(prepoint_ra, prepoint_dec, prepoint_time)
            
            # Update Alt/Az display with prepoint Alt/Az (what mount will slew to)
            self.txt_target_altaz.Text = "Alt: {:.1f}°, Az: {:.1f}°".format(self.prepoint_alt, self.prepoint_az)
            
            # Update mount status
            if self.mount_controller and self.mount_controller.is_mount_available():
                current_alt, current_az = self.mount_controller.get_current_altaz()
                if current_alt and current_az:
                    alt_diff = self.prepoint_alt - current_alt
                    az_diff = self.prepoint_az - current_az
                    direction_text = "Move {:.2f}° Alt, {:.2f}° Az".format(alt_diff, az_diff)
                    self.txt_direction_altaz.Text = direction_text
            
        except Exception as ex:
            MessageBox.Show("Error calculating prepoint: {}".format(ex), 
                          "Calculation Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def goto_prepoint(self, sender, e):
        """Goto prepoint coordinates"""
        if not self.mount_controller or not self.mount_controller.is_mount_available():
            MessageBox.Show("No mount connected or mount doesn't support GOTO", 
                          "Mount Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            return
        
        if not hasattr(self, 'prepoint_alt') or not hasattr(self, 'prepoint_az'):
            MessageBox.Show("Calculate prepoint first", 
                          "Missing Coordinates", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        try:
            # Use RA/Dec for mount slew (more reliable than Alt/Az)
            success = self.mount_controller.goto_prepoint(
                self.prepoint_alt, self.prepoint_az, self.prepoint_ra, self.prepoint_dec
            )
            if success:
                MessageBox.Show("Mount slewing to Alt: {:.1f}°, Az: {:.1f}°".format(self.prepoint_alt, self.prepoint_az), 
                              "GOTO Started", MessageBoxButtons.OK, MessageBoxIcon.Information)
            else:
                MessageBox.Show("Failed to slew mount", 
                              "GOTO Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
        except Exception as ex:
            MessageBox.Show("GOTO failed: {}".format(ex), 
                          "GOTO Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def refine_prepoint(self, sender, e):
        """
        Plate solve the current image and retrieve coordinates of the actual image.
        Does NOT sync the mount - only reads the solved position.
        Then calculates:
        1. Alt-Az of the solved position
        2. Total angular distance to prepoint target
        3. Direction to move in Alt-Az and RA/Dec (E/W, N/S)
        """
        if not self.sharpcap or not self.sharpcap.SelectedCamera:
            MessageBox.Show("No camera connected", 
                          "Camera Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            return
        
        if not hasattr(self, 'prepoint_ra') or not hasattr(self, 'prepoint_dec'):
            MessageBox.Show("Calculate prepoint coordinates first before refining", 
                          "Prepoint Required", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        # Update status to show we're working
        self.txt_refine_status.Text = "Plate solving..."
        self.txt_refine_status.ForeColor = Color.Orange
        
        # Run plate solve in background thread to avoid blocking UI
        try:
            # Check if plate solving is available
            if not hasattr(self.sharpcap, 'BlindSolver') or self.sharpcap.BlindSolver is None:
                MessageBox.Show("Plate solving is not available on this system.\n\n"
                              "SharpCap's plate solver needs to be configured first.",
                              "Plate Solve Unavailable", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                self.txt_refine_status.Text = "Plate solve unavailable"
                self.txt_refine_status.ForeColor = Color.Red
                return
            
            # Determine plate solve purpose
            solve_purpose = self._plate_solve_purpose
            if solve_purpose is None:
                # Try to get it from the main SharpCap object
                try:
                    solve_purpose = self.sharpcap.PlateSolvePurpose.Annotation
                except:
                    # Fallback to a default value
                    solve_purpose = 0  # PlateSolvePurpose.Annotation
            
            # Perform plate solve - this is a blocking call that will
            # capture a frame and solve it
            # Use SafeGetAsyncResult to avoid locking issues
            result = self.sharpcap.SafeGetAsyncResult(
                self.sharpcap.BlindSolver.SolveAsync(solve_purpose, CancellationToken())
            )
            
            if result is None:
                self.txt_refine_status.Text = "Plate solve failed - no result"
                self.txt_refine_status.ForeColor = Color.Red
                return
            
            # Extract solved coordinates (RA in hours, Dec in degrees)
            solved_ra = result.RightAscension   # hours
            solved_dec = result.Declination     # degrees
            
            print("[Refine Pre-Point] Solved position: RA={:.4f}h, Dec={:.4f}°".format(solved_ra, solved_dec))
            
            # Debug: Compare with prepoint target position
            # (the prepoint position is the star's RA/Dec corrected for time till event and refraction)
            print("[Refine Pre-Point] Prepoint target: RA={:.4f}h, Dec={:.4f}°".format(self.prepoint_ra, self.prepoint_dec))
            print("[Refine Pre-Point] Plate solve: RA={:.4f}h, Dec={:.4f}°".format(solved_ra, solved_dec))
            print("[Refine Pre-Point] RA difference: {:.4f}h ({:.2f}°), Dec difference: {:.4f}°".format(
                solved_ra - self.prepoint_ra, (solved_ra - self.prepoint_ra) * 15.0, solved_dec - self.prepoint_dec))
            
            # Calculate angular distance to prepoint target in RA/Dec space
            angular_distance_radec = self._calculate_angular_distance(solved_ra, solved_dec, self.prepoint_ra, self.prepoint_dec)
            print("[Refine Pre-Point] Angular distance to prepoint (RA/Dec): {:.2f}°".format(angular_distance_radec))
            
            # Debug: Check if this is the expected difference due to Earth's rotation
            # Earth rotates 15° per hour = 1 hour RA per hour of time
            
            # Calculate prepoint_time if not already stored (needed for time difference calculation)
            if not hasattr(self, 'prepoint_time'):
                # If prepoint_time not stored, calculate it from event
                event_time = datetime.strptime(self.event.event_time, "%Y-%m-%dT%H:%M:%S")
                offset_seconds = int(self.txt_offset.Text) if hasattr(self, 'txt_offset') and self.txt_offset.Text else 10
                self.prepoint_time = event_time - timedelta(seconds=offset_seconds)
            
            current_time = datetime.utcnow()
            time_diff_hours = (self.prepoint_time - current_time).total_seconds() / 3600.0
            expected_ra_diff_hours = time_diff_hours * (15.0 / 15.0)  # 1 hour RA per hour of time
            
            # Debug: Show all times
            print("[Refine Pre-Point] Current time: {}".format(current_time.strftime("%H:%M:%S")))
            print("[Refine Pre-Point] Prepoint time: {}".format(self.prepoint_time.strftime("%H:%M:%S")))
            print("[Refine Pre-Point] Event time: {}".format(self.event.event_time))
            print("[Refine Pre-Point] Time to prepoint: {:.2f} hours".format(time_diff_hours))
            print("[Refine Pre-Point] Expected RA difference due to Earth rotation: {:.4f}h".format(expected_ra_diff_hours))
            print("[Refine Pre-Point] Actual RA difference: {:.4f}h".format(solved_ra - self.prepoint_ra))
            print("[Refine Pre-Point] Difference from expected: {:.4f}h".format((solved_ra - self.prepoint_ra) - expected_ra_diff_hours))
            
            # Check if prepoint calculation might be wrong
            # Calculate what the RA difference SHOULD be based on Earth's rotation
            # Star moves WEST (RA decreases?) Actually, RA increases EAST...
            # For a star at event RA, current RA should be: event_ra - (time_to_event * sidereal_rate)
            # Where sidereal_rate = 1.0027379 (sidereal days per solar day)
            sidereal_rate = 1.0027379  # Sidereal days per solar day
            time_to_event_hours = time_diff_hours  # Positive if prepoint is before event
            expected_current_ra = self.prepoint_ra - (time_to_event_hours * sidereal_rate / 24.0)
            print("[Refine Pre-Point] Expected current RA (if pointing at star): {:.4f}h".format(expected_current_ra))
            print("[Refine Pre-Point] Plate solve RA: {:.4f}h".format(solved_ra))
            print("[Refine Pre-Point] Should telescope be at prepoint RA or current star RA?")
            
            # Calculate Alt/Az of the solved position at CURRENT time
            current_time = datetime.utcnow()
            solved_alt_current, solved_az_current = self.calculator.ra_dec_to_altaz(solved_ra, solved_dec, current_time)
            
            print("[Refine Pre-Point] Solved Alt/Az at current time {}: Alt={:.2f}°, Az={:.2f}°".format(
                current_time.strftime("%H:%M:%S"), solved_alt_current, solved_az_current))
            
            # Also calculate at prepoint time for comparison
            # Calculate prepoint_time if not already stored
            if not hasattr(self, 'prepoint_time'):
                # If prepoint_time not stored, calculate it from event
                event_time = datetime.strptime(self.event.event_time, "%Y-%m-%dT%H:%M:%S")
                offset_seconds = int(self.txt_offset.Text) if hasattr(self, 'txt_offset') and self.txt_offset.Text else 10
                self.prepoint_time = event_time - timedelta(seconds=offset_seconds)
            
            solved_alt_prepoint, solved_az_prepoint = self.calculator.ra_dec_to_altaz(solved_ra, solved_dec, self.prepoint_time)
            
            print("[Refine Pre-Point] Solved Alt/Az at prepoint time {}: Alt={:.2f}°, Az={:.2f}°".format(
                self.prepoint_time.strftime("%H:%M:%S"), solved_alt_prepoint, solved_az_prepoint))
            
            # For Refine Pre-Point, compare CURRENT telescope position to the PREPOINT TARGET position
            # (where the telescope should be pointing for the star to be centered at event time)
            
            # 1. Calculate prepoint target Alt/Az at CURRENT time
            current_time = datetime.utcnow()
            target_alt_current, target_az_current = self.calculator.ra_dec_to_altaz(
                self.prepoint_ra, self.prepoint_dec, current_time
            )
            
            print("[Refine Pre-Point] Prepoint target Alt/Az at current time {}: Alt={:.2f}°, Az={:.2f}°".format(
                current_time.strftime("%H:%M:%S"), target_alt_current, target_az_current))
            
            # 2. Current telescope position (from plate solve at current time)
            # Use solved_alt_current, solved_az_current (already calculated)
            
            # 3. Try to get mount's current coordinates for comparison
            # If mount is connected and knows its position, compare to that instead
            mount_ra = None
            mount_dec = None
            mount_alt = None
            mount_az = None
            
            if self.mount_controller and self.mount_controller.mount:
                try:
                    mount_ra = self.mount_controller.mount.RightAscension
                    mount_dec = self.mount_controller.mount.Declination
                    print("[Refine Pre-Point] Mount reports: RA={:.4f}h, Dec={:.4f}°".format(mount_ra, mount_dec))
                    
                    # Calculate mount Alt/Az at current time
                    mount_alt, mount_az = self.calculator.ra_dec_to_altaz(mount_ra, mount_dec, current_time)
                    print("[Refine Pre-Point] Mount Alt/Az: Alt={:.2f}°, Az={:.2f}°".format(mount_alt, mount_az))
                    
                except Exception as e:
                    print("[Refine Pre-Point] Could not get mount coordinates: {}".format(e))
            
            # Decide what to compare against:
            # 1. If mount coordinates available, compare plate solve to mount position (after GOTO)
            # 2. Otherwise, compare plate solve to prepoint target
            if mount_ra is not None and mount_dec is not None:
                # Compare to mount position (where telescope thinks it's pointing after GOTO)
                compare_ra = mount_ra
                compare_dec = mount_dec
                compare_alt = mount_alt
                compare_az = mount_az
                compare_label = "mount position"
                print("[Refine Pre-Point] Comparing to MOUNT position (after GOTO)")
            else:
                # Compare to prepoint target (where telescope should be pointing)
                compare_ra = self.prepoint_ra
                compare_dec = self.prepoint_dec
                compare_alt = target_alt_current
                compare_az = target_az_current
                compare_label = "prepoint target"
                print("[Refine Pre-Point] Comparing to PREPOINT target (no mount info)")
            
            # 4. Calculate angular distance using Haversine formula on RA/Dec coordinates
            # This gives the true angular separation on the celestial sphere
            angular_distance = self._calculate_angular_distance(
                solved_ra, solved_dec, compare_ra, compare_dec
            )
            
            # 5. Calculate Alt/Az differences for direction display (both at CURRENT time)
            alt_diff = compare_alt - solved_alt_current
            az_diff = compare_az - solved_az_current
            # Normalize azimuth difference to shortest path (-180° to +180°)
            if az_diff > 180.0:
                az_diff -= 360.0
            elif az_diff < -180.0:
                az_diff += 360.0
            
            # Debug output for Alt/Az comparison
            print("[Refine Pre-Point] Telescope Alt/Az: Alt={:.2f}°, Az={:.2f}°".format(solved_alt_current, solved_az_current))
            print("[Refine Pre-Point] Target Alt/Az: Alt={:.2f}°, Az={:.2f}°".format(compare_alt, compare_az))
            print("[Refine Pre-Point] Alt diff: {:.2f}°, Az diff: {:.2f}°".format(alt_diff, az_diff))
            
            self.txt_refine_status.Text = "{:.2f}° from {}".format(angular_distance, compare_label)
            if angular_distance < 1.0:
                self.txt_refine_status.ForeColor = Color.Green
            elif angular_distance < 5.0:
                self.txt_refine_status.ForeColor = Color.Orange
            else:
                self.txt_refine_status.ForeColor = Color.Red
            
            # Format Alt/Az direction
            alt_dir = "Up" if alt_diff > 0 else "Down" if alt_diff < 0 else " - "
            az_dir = "Right" if az_diff > 0 else "Left" if az_diff < 0 else " - "
            altaz_text = "Alt: {:.2f}° ({})  Az: {:.2f}° ({})".format(
                abs(alt_diff), alt_dir, abs(az_diff), az_dir
            )
            self.txt_direction_altaz.Text = altaz_text
            
            # Calculate RA/Dec direction offsets (compare to appropriate target)
            ra_diff_hours = compare_ra - solved_ra
            # Normalize RA difference to shortest path (-12 to +12 hours)
            if ra_diff_hours > 12.0:
                ra_diff_hours -= 24.0
            elif ra_diff_hours < -12.0:
                ra_diff_hours += 24.0
            ra_diff_deg = ra_diff_hours * 15.0  # Convert to degrees (at equator)
            
            dec_diff = compare_dec - solved_dec
            
            # Determine RA direction (E/W)
            # In the sky, RA increases Eastward
            ra_dir = "East" if ra_diff_hours > 0 else "West" if ra_diff_hours < 0 else " - "
            dec_dir = "North" if dec_diff > 0 else "South" if dec_diff < 0 else " - "
            
            radec_text = "RA: {:.2f}h ({})  Dec: {:.2f}° ({})".format(
                abs(ra_diff_hours), ra_dir, abs(dec_diff), dec_dir
            )
            self.txt_direction_radec.Text = radec_text
            
            # Store solved coordinates for later use
            self.solved_ra = solved_ra
            self.solved_dec = solved_dec
            self.solved_alt_current = solved_alt_current
            self.solved_az_current = solved_az_current
            self.solved_alt_prepoint = solved_alt_prepoint
            self.solved_az_prepoint = solved_az_prepoint
            
            print("[Refine Pre-Point] Complete: {:.2f}° from target".format(angular_distance))
            
        except Exception as ex:
            error_msg = str(ex)
            print("[Refine Pre-Point] Error: {}".format(error_msg))
            self.txt_refine_status.Text = "Plate solve failed"
            self.txt_refine_status.ForeColor = Color.Red
            MessageBox.Show("Plate solve failed: {}\n\nCheck camera exposure and focus.".format(error_msg),
                          "Plate Solve Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def _calculate_angular_distance(self, ra1_hours, dec1_deg, ra2_hours, dec2_deg):
        """
        Calculate angular distance between two points on the celestial sphere
        using the spherical law of cosines (haversine formula).
        
        Args:
            ra1_hours: RA of point 1 in hours
            dec1_deg: Dec of point 1 in degrees
            ra2_hours: RA of point 2 in hours
            dec2_deg: Dec of point 2 in degrees
            
        Returns:
            Angular distance in degrees
        """
        # Convert to radians
        ra1_rad = math.radians(ra1_hours * 15.0)
        dec1_rad = math.radians(dec1_deg)
        ra2_rad = math.radians(ra2_hours * 15.0)
        dec2_rad = math.radians(dec2_deg)
        
        # Haversine formula
        d_ra = ra2_rad - ra1_rad
        d_dec = dec2_rad - dec1_rad
        
        a = math.sin(d_dec / 2.0) ** 2 + \
            math.cos(dec1_rad) * math.cos(dec2_rad) * math.sin(d_ra / 2.0) ** 2
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        
        return math.degrees(c)
    
    def close_dialog(self, sender, e):
        """Close dialog"""
        if sender.Text == "OK":
            self.DialogResult = DialogResult.OK
        else:
            self.DialogResult = DialogResult.Cancel
        self.Close()


# Import PrepointCalculator and PrepointMountController from prepoint_manager
try:
    from prepoint_manager import PrepointCalculator, PrepointMountController
except ImportError:
    # Define fallback classes if import fails
    class PrepointCalculator:
        def __init__(self, lat, lon, elev=0):
            self.lat = lat
            self.lon = lon
            self.elev = elev
        
        def calculate_prepoint(self, target_ra_hours, target_dec_degrees, event_time_utc, prepoint_offset_seconds=10):
            return 0, 0, datetime.utcnow()
    
    class PrepointMountController:
        def __init__(self, sharpcap=None):
            self.sharpcap = sharpcap
            self.mount = None
        
        def is_mount_available(self):
            return False
        
        def goto_prepoint(self, alt_deg, az_deg):
            return False