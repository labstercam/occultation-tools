"""
Equipment Management Dialogs for Telescopes and Cameras
"""

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

from System.Windows.Forms import (
    Form, Label, TextBox, ComboBox, Button, ListBox, GroupBox,
    DialogResult, MessageBox, MessageBoxButtons, MessageBoxIcon,
    ComboBoxStyle, SelectionMode, FormBorderStyle, FormStartPosition
)
from System.Drawing import Point, Size, Color, Font, FontStyle
from theme import apply_theme_to_control

class TelescopeManagerDialog(Form):
    """Dialog for managing multiple telescope configurations"""
    
    def __init__(self, config, theme_manager=None):
        self.config = config
        self.theme_manager = theme_manager
        self.selected_telescope_id = None
        self.telescope_map = {}  # Map list index to telescope dict
        
        # Setup form
        self.Text = "Telescope Manager"
        self.Size = Size(700, 500)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterParent
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        self.setup_ui()
        self.load_telescopes()
        
        if theme_manager:
            theme_colors = theme_manager.get_current_theme()
            apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup the UI controls"""
        sf = 1.0  # Scale factor
        
        # List of telescopes
        lbl_list = Label()
        lbl_list.Text = "Telescopes:"
        lbl_list.Location = Point(int(20 * sf), int(20 * sf))
        lbl_list.Size = Size(int(200 * sf), int(20 * sf))
        self.Controls.Add(lbl_list)
        
        self.lst_telescopes = ListBox()
        self.lst_telescopes.Location = Point(int(20 * sf), int(45 * sf))
        self.lst_telescopes.Size = Size(int(250 * sf), int(300 * sf))
        self.lst_telescopes.SelectionMode = SelectionMode.One
        self.lst_telescopes.SelectedIndexChanged += self.telescope_selected
        self.Controls.Add(self.lst_telescopes)
        
        # Telescope details group
        details_group = GroupBox()
        details_group.Text = "Telescope Details"
        details_group.Location = Point(int(290 * sf), int(20 * sf))
        details_group.Size = Size(int(380 * sf), int(325 * sf))
        self.Controls.Add(details_group)
        
        # Name
        lbl_name = Label()
        lbl_name.Text = "Name:"
        lbl_name.Location = Point(int(15 * sf), int(30 * sf))
        lbl_name.Size = Size(int(100 * sf), int(20 * sf))
        details_group.Controls.Add(lbl_name)
        
        self.txt_name = TextBox()
        self.txt_name.Location = Point(int(120 * sf), int(30 * sf))
        self.txt_name.Size = Size(int(240 * sf), int(20 * sf))
        details_group.Controls.Add(self.txt_name)
        
        # Aperture
        lbl_aperture = Label()
        lbl_aperture.Text = "Aperture (mm):"
        lbl_aperture.Location = Point(int(15 * sf), int(65 * sf))
        lbl_aperture.Size = Size(int(100 * sf), int(20 * sf))
        details_group.Controls.Add(lbl_aperture)
        
        self.txt_aperture = TextBox()
        self.txt_aperture.Location = Point(int(120 * sf), int(65 * sf))
        self.txt_aperture.Size = Size(int(100 * sf), int(20 * sf))
        details_group.Controls.Add(self.txt_aperture)
        
        # Focal Ratio
        lbl_focal = Label()
        lbl_focal.Text = "Focal Ratio (f/):" 
        lbl_focal.Location = Point(int(15 * sf), int(100 * sf))
        lbl_focal.Size = Size(int(100 * sf), int(20 * sf))
        details_group.Controls.Add(lbl_focal)
        
        self.txt_focal_ratio = TextBox()
        self.txt_focal_ratio.Location = Point(int(120 * sf), int(100 * sf))
        self.txt_focal_ratio.Size = Size(int(100 * sf), int(20 * sf))
        details_group.Controls.Add(self.txt_focal_ratio)
        
        # Type
        lbl_type = Label()
        lbl_type.Text = "Type:"
        lbl_type.Location = Point(int(15 * sf), int(135 * sf))
        lbl_type.Size = Size(int(100 * sf), int(20 * sf))
        details_group.Controls.Add(lbl_type)
        
        self.combo_type = ComboBox()
        self.combo_type.Location = Point(int(120 * sf), int(135 * sf))
        self.combo_type.Size = Size(int(240 * sf), int(20 * sf))
        self.combo_type.DropDownStyle = ComboBoxStyle.DropDownList
        telescope_types = [
            "SCT including Cass and Mak",
            "Newtonian",
            "Refractor",
            "EdgeHD",
            "Ritchey-Chretien",
            "Other"
        ]
        for tel_type in telescope_types:
            self.combo_type.Items.Add(tel_type)
        self.combo_type.SelectedIndex = 0
        details_group.Controls.Add(self.combo_type)
        
        # Buttons inside details group
        self.btn_add = Button()
        self.btn_add.Text = "Add New"
        self.btn_add.Location = Point(int(15 * sf), int(250 * sf))
        self.btn_add.Size = Size(int(110 * sf), int(30 * sf))
        self.btn_add.Click += self.add_telescope
        details_group.Controls.Add(self.btn_add)
        
        self.btn_update = Button()
        self.btn_update.Text = "Update"
        self.btn_update.Location = Point(int(135 * sf), int(250 * sf))
        self.btn_update.Size = Size(int(110 * sf), int(30 * sf))
        self.btn_update.Click += self.update_telescope
        self.btn_update.Enabled = False
        details_group.Controls.Add(self.btn_update)
        
        self.btn_delete = Button()
        self.btn_delete.Text = "Delete"
        self.btn_delete.Location = Point(int(255 * sf), int(250 * sf))
        self.btn_delete.Size = Size(int(110 * sf), int(30 * sf))
        self.btn_delete.Click += self.delete_telescope
        self.btn_delete.Enabled = False
        details_group.Controls.Add(self.btn_delete)
        
        # Active indicator
        self.lbl_active = Label()
        self.lbl_active.Text = "★ Active"
        self.lbl_active.Location = Point(int(15 * sf), int(200 * sf))
        self.lbl_active.Size = Size(int(100 * sf), int(20 * sf))
        self.lbl_active.ForeColor = Color.Green
        self.lbl_active.Font = Font(self.lbl_active.Font.FontFamily, 10, FontStyle.Bold)
        self.lbl_active.Visible = False
        details_group.Controls.Add(self.lbl_active)
        
        self.btn_set_active = Button()
        self.btn_set_active.Text = "Set as Active"
        self.btn_set_active.Location = Point(int(120 * sf), int(195 * sf))
        self.btn_set_active.Size = Size(int(125 * sf), int(30 * sf))
        self.btn_set_active.Click += self.set_active_telescope
        self.btn_set_active.Enabled = False
        details_group.Controls.Add(self.btn_set_active)
        
        # Close button
        btn_close = Button()
        btn_close.Text = "Close"
        btn_close.Location = Point(int(560 * sf), int(420 * sf))
        btn_close.Size = Size(int(100 * sf), int(30 * sf))
        btn_close.Click += self.close_dialog
        self.Controls.Add(btn_close)
    
    def load_telescopes(self):
        """Load telescopes into the list"""
        self.lst_telescopes.Items.Clear()
        self.telescope_map.clear()
        telescopes = self.config.get_telescopes()
        active_telescope = self.config.get_active_telescope()
        active_id = active_telescope.get('id') if active_telescope else None
        
        for telescope in telescopes:
            name = telescope.get('name', 'Unnamed')
            if telescope.get('id') == active_id:
                name = "★ " + name
            # Store telescope dict as Tag and display formatted name
            self.lst_telescopes.Items.Add(name)
            # Store the telescope dict for later retrieval
            self.telescope_map[self.lst_telescopes.Items.Count - 1] = telescope
    
    def telescope_selected(self, sender, e):
        """Handle telescope selection"""
        if self.lst_telescopes.SelectedIndex >= 0:
            telescope = self.telescope_map.get(self.lst_telescopes.SelectedIndex)
            if not telescope:
                return
                
            self.selected_telescope_id = telescope.get('id')
            
            # Load telescope details
            self.txt_name.Text = telescope.get('name', '')
            self.txt_aperture.Text = str(telescope.get('aperture', ''))
            
            # Handle backward compatibility: convert old focal_length to focal_ratio
            focal_ratio = telescope.get('focal_ratio', 0)
            if focal_ratio == 0 and telescope.get('focal_length', 0) > 0:
                aperture_val = telescope.get('aperture', 0)
                if aperture_val > 0:
                    focal_ratio = telescope.get('focal_length') / aperture_val
            self.txt_focal_ratio.Text = '{:.2f}'.format(focal_ratio) if focal_ratio > 0 else ''
            
            # Set type
            tel_type = telescope.get('type', 'SCT including Cass and Mak')
            for i in range(self.combo_type.Items.Count):
                if self.combo_type.Items[i] == tel_type:
                    self.combo_type.SelectedIndex = i
                    break
            
            # Enable buttons
            self.btn_update.Enabled = True
            self.btn_delete.Enabled = True
            self.btn_set_active.Enabled = True
            
            # Show active indicator
            active_telescope = self.config.get_active_telescope()
            active_id = active_telescope.get('id') if active_telescope else None
            is_active = (self.selected_telescope_id == active_id)
            self.lbl_active.Visible = is_active
            self.btn_set_active.Enabled = not is_active
        else:
            self.clear_fields()
    
    def clear_fields(self):
        """Clear all input fields"""
        self.txt_name.Text = ""
        self.txt_aperture.Text = ""
        self.txt_focal_ratio.Text = ""
        self.combo_type.SelectedIndex = 0
        self.btn_update.Enabled = False
        self.btn_delete.Enabled = False
        self.btn_set_active.Enabled = False
        self.lbl_active.Visible = False
        self.selected_telescope_id = None
    
    def add_telescope(self, sender, e):
        """Add a new telescope"""
        try:
            name = self.txt_name.Text.strip()
            aperture = float(self.txt_aperture.Text)
            focal_ratio = float(self.txt_focal_ratio.Text)
            tel_type = self.combo_type.Text if self.combo_type.SelectedIndex >= 0 else "SCT including Cass and Mak"
            
            if not name:
                MessageBox.Show("Please enter a telescope name.", "Validation Error",
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            if aperture <= 0 or focal_ratio <= 0:
                MessageBox.Show("Aperture and focal ratio must be positive numbers.", "Validation Error",
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            self.config.add_telescope(name, aperture, focal_ratio, tel_type)
            self.config.save_config()
            self.load_telescopes()
            self.clear_fields()
            
            MessageBox.Show("Telescope added successfully.", "Success",
                          MessageBoxButtons.OK, MessageBoxIcon.Information)
        except ValueError:
            MessageBox.Show("Please enter valid numbers for aperture and focal ratio.", "Input Error",
                          MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def update_telescope(self, sender, e):
        """Update the selected telescope"""
        if not self.selected_telescope_id:
            return
        
        try:
            name = self.txt_name.Text.strip()
            aperture = float(self.txt_aperture.Text)
            focal_ratio = float(self.txt_focal_ratio.Text)
            tel_type = self.combo_type.Text if self.combo_type.SelectedIndex >= 0 else "SCT including Cass and Mak"
            
            if not name:
                MessageBox.Show("Please enter a telescope name.", "Validation Error",
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            if aperture <= 0 or focal_ratio <= 0:
                MessageBox.Show("Aperture and focal ratio must be positive numbers.", "Validation Error",
                              MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            self.config.update_telescope(self.selected_telescope_id, name, aperture, focal_ratio, tel_type)
            self.config.save_config()
            self.load_telescopes()
            
            # Re-select the same telescope
            for i, telescope in self.telescope_map.items():
                if telescope.get('id') == self.selected_telescope_id:
                    self.lst_telescopes.SelectedIndex = i
                    break
            
            MessageBox.Show("Telescope updated successfully.", "Success",
                          MessageBoxButtons.OK, MessageBoxIcon.Information)
        except ValueError:
            MessageBox.Show("Please enter valid numbers for aperture and focal length.", "Input Error",
                          MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def delete_telescope(self, sender, e):
        """Delete the selected telescope"""
        if not self.selected_telescope_id:
            return
        
        result = MessageBox.Show("Are you sure you want to delete this telescope?", "Confirm Delete",
                               MessageBoxButtons.YesNo, MessageBoxIcon.Question)
        
        if result == DialogResult.Yes:
            self.config.delete_telescope(self.selected_telescope_id)
            self.config.save_config()
            self.load_telescopes()
            self.clear_fields()
    
    def set_active_telescope(self, sender, e):
        """Set the selected telescope as active"""
        if not self.selected_telescope_id:
            return
        
        self.config.set_active_telescope(self.selected_telescope_id)
        self.config.save_config()
        self.load_telescopes()
        
        # Re-select the same telescope
        for i, telescope in self.telescope_map.items():
            if telescope.get('id') == self.selected_telescope_id:
                self.lst_telescopes.SelectedIndex = i
                break
    
    def close_dialog(self, sender, e):
        """Close the dialog"""
        self.DialogResult = DialogResult.OK
        self.Close()


class CameraManagerDialog(Form):
    """Dialog for managing multiple camera configurations"""
    
    def __init__(self, config, theme_manager=None):
        self.config = config
        self.theme_manager = theme_manager
        self.selected_camera_id = None
        self.camera_map = {}  # Map list index to camera dict
        
        # Setup form
        self.Text = "Camera Manager"
        self.Size = Size(750, 600)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterParent
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        self.setup_ui()
        self.load_cameras()
        
        if theme_manager:
            theme_colors = theme_manager.get_current_theme()
            apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup the UI controls"""
        sf = 1.0  # Scale factor
        
        # List of cameras
        lbl_list = Label()
        lbl_list.Text = "Cameras:"
        lbl_list.Location = Point(int(20 * sf), int(20 * sf))
        lbl_list.Size = Size(int(200 * sf), int(20 * sf))
        self.Controls.Add(lbl_list)
        
        self.lst_cameras = ListBox()
        self.lst_cameras.Location = Point(int(20 * sf), int(45 * sf))
        self.lst_cameras.Size = Size(int(250 * sf), int(400 * sf))
        self.lst_cameras.SelectionMode = SelectionMode.One
        self.lst_cameras.SelectedIndexChanged += self.camera_selected
        self.Controls.Add(self.lst_cameras)
        
        # Camera details group
        details_group = GroupBox()
        details_group.Text = "Camera Details"
        details_group.Location = Point(int(290 * sf), int(20 * sf))
        details_group.Size = Size(int(430 * sf), int(505 * sf))
        self.Controls.Add(details_group)
        
        y_pos = 30
        
        # Name
        lbl_name = Label()
        lbl_name.Text = "Name:"
        lbl_name.Location = Point(int(15 * sf), int(y_pos * sf))
        lbl_name.Size = Size(int(130 * sf), int(20 * sf))
        details_group.Controls.Add(lbl_name)
        
        self.txt_name = TextBox()
        self.txt_name.Location = Point(int(150 * sf), int(y_pos * sf))
        self.txt_name.Size = Size(int(260 * sf), int(20 * sf))
        details_group.Controls.Add(self.txt_name)
        
        y_pos += 40
        
        # Detector
        lbl_detector = Label()
        lbl_detector.Text = "Detector:"
        lbl_detector.Location = Point(int(15 * sf), int(y_pos * sf))
        lbl_detector.Size = Size(int(130 * sf), int(20 * sf))
        details_group.Controls.Add(lbl_detector)
        
        self.combo_detector = ComboBox()
        self.combo_detector.Location = Point(int(150 * sf), int(y_pos * sf))
        self.combo_detector.Size = Size(int(260 * sf), int(20 * sf))
        self.combo_detector.DropDownStyle = ComboBoxStyle.DropDown
        details_group.Controls.Add(self.combo_detector)
        
        y_pos += 40
        
        # Report Type
        lbl_report_type = Label()
        lbl_report_type.Text = "Report Type:"
        lbl_report_type.Location = Point(int(15 * sf), int(y_pos * sf))
        lbl_report_type.Size = Size(int(130 * sf), int(20 * sf))
        details_group.Controls.Add(lbl_report_type)
        
        self.combo_report_type = ComboBox()
        self.combo_report_type.Location = Point(int(150 * sf), int(y_pos * sf))
        self.combo_report_type.Size = Size(int(260 * sf), int(20 * sf))
        self.combo_report_type.DropDownStyle = ComboBoxStyle.DropDownList
        report_types = ["NA", "TT"]
        for rt in report_types:
            self.combo_report_type.Items.Add(rt)
        self.combo_report_type.Text = "NA"
        self.combo_report_type.SelectedIndexChanged += self.report_type_changed
        details_group.Controls.Add(self.combo_report_type)
        
        y_pos += 40
        
        # Timing
        lbl_timing = Label()
        lbl_timing.Text = "Timing:"
        lbl_timing.Location = Point(int(15 * sf), int(y_pos * sf))
        lbl_timing.Size = Size(int(130 * sf), int(20 * sf))
        details_group.Controls.Add(lbl_timing)
        
        self.combo_timing = ComboBox()
        self.combo_timing.Location = Point(int(150 * sf), int(y_pos * sf))
        self.combo_timing.Size = Size(int(260 * sf), int(20 * sf))
        self.combo_timing.DropDownStyle = ComboBoxStyle.DropDown
        details_group.Controls.Add(self.combo_timing)
        
        y_pos += 40
        
        # Timing Device
        lbl_timing_device = Label()
        lbl_timing_device.Text = "Timing Device:"
        lbl_timing_device.Location = Point(int(15 * sf), int(y_pos * sf))
        lbl_timing_device.Size = Size(int(130 * sf), int(20 * sf))
        details_group.Controls.Add(lbl_timing_device)
        
        self.combo_timing_device = ComboBox()
        self.combo_timing_device.Location = Point(int(150 * sf), int(y_pos * sf))
        self.combo_timing_device.Size = Size(int(260 * sf), int(20 * sf))
        self.combo_timing_device.DropDownStyle = ComboBoxStyle.DropDown
        details_group.Controls.Add(self.combo_timing_device)
        
        y_pos += 40
        
        # Video Format
        lbl_video_format = Label()
        lbl_video_format.Text = "Video Format:"
        lbl_video_format.Location = Point(int(15 * sf), int(y_pos * sf))
        lbl_video_format.Size = Size(int(130 * sf), int(20 * sf))
        details_group.Controls.Add(lbl_video_format)
        
        self.combo_video_format = ComboBox()
        self.combo_video_format.Location = Point(int(150 * sf), int(y_pos * sf))
        self.combo_video_format.Size = Size(int(260 * sf), int(20 * sf))
        self.combo_video_format.DropDownStyle = ComboBoxStyle.DropDown
        details_group.Controls.Add(self.combo_video_format)
        
        # Initialize timing options for default report type (after all combos are created)
        self.update_timing_options()
        
        y_pos += 40
        
        # Exposure/Integration
        lbl_exposure = Label()
        lbl_exposure.Text = "Exposure/Integration:"
        lbl_exposure.Location = Point(int(15 * sf), int(y_pos * sf))
        lbl_exposure.Size = Size(int(130 * sf), int(20 * sf))
        details_group.Controls.Add(lbl_exposure)
        
        self.combo_exposure = ComboBox()
        self.combo_exposure.Location = Point(int(150 * sf), int(y_pos * sf))
        self.combo_exposure.Size = Size(int(260 * sf), int(20 * sf))
        self.combo_exposure.DropDownStyle = ComboBoxStyle.DropDown
        exposure_options = ["Other", "Integration", "Exposure"]
        for opt in exposure_options:
            self.combo_exposure.Items.Add(opt)
        self.combo_exposure.Text = "Other"
        details_group.Controls.Add(self.combo_exposure)
        
        y_pos += 40
        
        # Other Detector Info
        lbl_other = Label()
        lbl_other.Text = "Other Detector Info:"
        lbl_other.Location = Point(int(15 * sf), int(y_pos * sf))
        lbl_other.Size = Size(int(130 * sf), int(20 * sf))
        details_group.Controls.Add(lbl_other)
        
        self.txt_other_info = TextBox()
        self.txt_other_info.Location = Point(int(150 * sf), int(y_pos * sf))
        self.txt_other_info.Size = Size(int(260 * sf), int(40 * sf))
        self.txt_other_info.Multiline = True
        details_group.Controls.Add(self.txt_other_info)
        
        y_pos += 60
        
        # Active indicator
        self.lbl_active = Label()
        self.lbl_active.Text = "★ Active"
        self.lbl_active.Location = Point(int(15 * sf), int(y_pos * sf))
        self.lbl_active.Size = Size(int(100 * sf), int(20 * sf))
        self.lbl_active.ForeColor = Color.Green
        self.lbl_active.Font = Font(self.lbl_active.Font.FontFamily, 10, FontStyle.Bold)
        self.lbl_active.Visible = False
        details_group.Controls.Add(self.lbl_active)
        
        self.btn_set_active = Button()
        self.btn_set_active.Text = "Set as Active"
        self.btn_set_active.Location = Point(int(150 * sf), int((y_pos - 5) * sf))
        self.btn_set_active.Size = Size(int(125 * sf), int(30 * sf))
        self.btn_set_active.Click += self.set_active_camera
        self.btn_set_active.Enabled = False
        details_group.Controls.Add(self.btn_set_active)
        
        y_pos += 40
        
        # Buttons
        self.btn_add = Button()
        self.btn_add.Text = "Add New"
        self.btn_add.Location = Point(int(15 * sf), int(y_pos * sf))
        self.btn_add.Size = Size(int(130 * sf), int(30 * sf))
        self.btn_add.Click += self.add_camera
        details_group.Controls.Add(self.btn_add)
        
        self.btn_update = Button()
        self.btn_update.Text = "Update"
        self.btn_update.Location = Point(int(150 * sf), int(y_pos * sf))
        self.btn_update.Size = Size(int(130 * sf), int(30 * sf))
        self.btn_update.Click += self.update_camera
        self.btn_update.Enabled = False
        details_group.Controls.Add(self.btn_update)
        
        self.btn_delete = Button()
        self.btn_delete.Text = "Delete"
        self.btn_delete.Location = Point(int(285 * sf), int(y_pos * sf))
        self.btn_delete.Size = Size(int(130 * sf), int(30 * sf))
        self.btn_delete.Click += self.delete_camera
        self.btn_delete.Enabled = False
        details_group.Controls.Add(self.btn_delete)
        
        # Close button (positioned under camera list)
        btn_close = Button()
        btn_close.Text = "Close"
        btn_close.Location = Point(int(85 * sf), int(460 * sf))
        btn_close.Size = Size(int(100 * sf), int(30 * sf))
        btn_close.Click += self.close_dialog
        self.Controls.Add(btn_close)
    
    def load_cameras(self):
        """Load cameras into the list"""
        self.lst_cameras.Items.Clear()
        self.camera_map.clear()
        cameras = self.config.get_cameras()
        active_camera = self.config.get_active_camera()
        active_id = active_camera.get('id') if active_camera else None
        
        for camera in cameras:
            name = camera.get('name', 'Unnamed')
            if camera.get('id') == active_id:
                name = "★ " + name
            # Store camera dict as Tag and display formatted name
            self.lst_cameras.Items.Add(name)
            # Store the camera dict for later retrieval
            self.camera_map[self.lst_cameras.Items.Count - 1] = camera
    
    def report_type_changed(self, sender, e):
        """Handle report type change - update timing options"""
        self.update_timing_options()
    
    def update_timing_options(self):
        """Update timing, timing device, detector, and video format options based on selected report type"""
        report_type = self.combo_report_type.Text
        current_timing = self.combo_timing.Text
        current_device = self.combo_timing_device.Text
        current_detector = self.combo_detector.Text
        current_video_format = self.combo_video_format.Text
        
        # Clear current options
        self.combo_timing.Items.Clear()
        self.combo_timing_device.Items.Clear()
        self.combo_detector.Items.Clear()
        self.combo_video_format.Items.Clear()
        
        if report_type == "NA":
            # NA timing options
            timing_options = [
                "GPS - time inserted",
                "GPS - other linking",
                "GPS - KIWI",
                "IOTA-VTI",
                "WWV",
                "Visual",
                "Other",
                "Unknown"
            ]
            # NA timing device options
            timing_device_options = [
                "ADVS",
                "AFT or OFT Flash Tag",
                "ASTRID",
                "Beeperbox",
                "Cellphone",
                "Computer NTP",
                "GPS",
                "GPS-ABC",
                "IOTA-VTI",
                "KIWI-OSD",
                "Stopwatch",
                "WWV Radio Time",
                "Other - Specify in Comments"
            ]
            # NA detector options
            detector_options = [
                "CCD Drift Scan",
                "ASTRID",
                "Flea 3-03S1 with ADVS",
                "Flea 3-03S3 with ADVS",
                "Flea 3-28S4M with ADVS",
                "Grasshopper Express with ADVS",
                "G-Star",
                "KPC-350BH",
                "LN-300-11673",
                "Mallincam",
                "Mintron 12v1C-EX",
                "PC164C",
                "PC164C-EX",
                "PC165-DNR",
                "Photometer",
                "QHY 174 GPS",
                "RunCam Night Eagle",
                "RunCam Night Eagle Astro",
                "Samsung SBC-2000",
                "Visual",
                "Watec 120N",
                "Watec 120N+",
                "Watec 902H",
                "Watec 910BD",
                "Watec 910HX",
                "Other - List in Comments"
            ]
            # NA video format options
            video_format_options = [
                "AAV-NTSC",
                "AAV-PAL",
                "ADVS",
                "CCD Drift",
                "FITS Images",
                "NTSC/EIA",
                "PAL/CCIR"
            ]
        else:  # TT
            # TT timing options
            timing_options = [
                "GPS - time inserted",
                "GPS - other linking",
                "Video + audio time signal",
                "Tape Recorder + time signal",
                "Eye-Ear + time signal",
                "Stopwatch",
                "Radio broadcast - calibrated",
                "other"
            ]
            # TT timing device options
            timing_device_options = [
                "Stopwatch",
                "WWV Radio Time",
                "Beeperbox",
                "GPS",
                "Computer NTP",
                "KIWI-OSD",
                "IOTA-VTI",
                "GPS-ABC",
                "ADVS",
                "Cellphone",
                "Other - Specify in Comments"
            ]
            # TT detector options
            detector_options = [
                "Visual",
                "Photometer",
                "PC165-DNR",
                "PC164C",
                "PC164C-EX",
                "Watec 120N",
                "Watec 120N+",
                "Watec 910HX",
                "Watec 910BD",
                "Watec 902H",
                "Mintron 12v1C-EX",
                "Mallincam",
                "CCD",
                "Samsung SBC-2000",
                "KPC-350BH",
                "LN-300-11673",
                "Flea 3-03S1 with ADVS",
                "Flea 3-03S3 with ADVS",
                "Flea 3-28S4M with ADVS",
                "Grasshopper Express with ADVS",
                "G-Star",
                "QHY 174GPS",
                "Other - List in Comments"
            ]
            # TT video format options
            video_format_options = [
                "NTSC/EIA",
                "PAL/CCIR",
                "CCD Drift",
                "ADVS",
                "AAV-NTSC",
                "FITS",
                "AAV-PAL"
            ]
        
        # Populate timing options
        for opt in timing_options:
            self.combo_timing.Items.Add(opt)
        
        # Populate timing device options
        for opt in timing_device_options:
            self.combo_timing_device.Items.Add(opt)
        
        # Populate detector options
        for opt in detector_options:
            self.combo_detector.Items.Add(opt)
        
        # Populate video format options
        for opt in video_format_options:
            self.combo_video_format.Items.Add(opt)
        
        # Restore previous values if they exist in new list
        if current_timing in timing_options:
            self.combo_timing.Text = current_timing
        else:
            self.combo_timing.Text = "GPS - other linking" if "GPS - other linking" in timing_options else timing_options[0] if timing_options else ""
        
        if current_device in timing_device_options:
            self.combo_timing_device.Text = current_device
        else:
            self.combo_timing_device.Text = ""
        
        if current_detector in detector_options:
            self.combo_detector.Text = current_detector
        else:
            self.combo_detector.Text = ""
        
        if current_video_format in video_format_options:
            self.combo_video_format.Text = current_video_format
        else:
            self.combo_video_format.Text = ""
    
    def camera_selected(self, sender, e):
        """Handle camera selection"""
        if self.lst_cameras.SelectedIndex >= 0:
            camera = self.camera_map.get(self.lst_cameras.SelectedIndex)
            if not camera:
                return
                
            self.selected_camera_id = camera.get('id')
            
            # Load camera details
            self.txt_name.Text = camera.get('name', '')
            self.combo_detector.Text = camera.get('detector', '')
            
            # Set report type first
            report_type = camera.get('report_type', 'NA')
            # Migrate old 'Both' to 'NA'
            if report_type == 'Both':
                report_type = 'NA'
            self.combo_report_type.Text = report_type
            
            # Manually update timing options (setting Text doesn't trigger event)
            self.update_timing_options()
            
            # Now load timing values (after options are updated)
            self.combo_timing.Text = camera.get('timing', 'GPS - other linking')
            self.combo_timing_device.Text = camera.get('timing_device', '')
            self.combo_video_format.Text = camera.get('video_format', 'SER')
            self.combo_exposure.Text = camera.get('exposure_integration', 'Other')
            self.txt_other_info.Text = camera.get('other_info', '')
            
            # Enable buttons
            self.btn_update.Enabled = True
            self.btn_delete.Enabled = True
            self.btn_set_active.Enabled = True
            
            # Show active indicator
            active_camera = self.config.get_active_camera()
            active_id = active_camera.get('id') if active_camera else None
            is_active = (self.selected_camera_id == active_id)
            self.lbl_active.Visible = is_active
            self.btn_set_active.Enabled = not is_active
        else:
            self.clear_fields()
    
    def clear_fields(self):
        """Clear all input fields"""
        self.txt_name.Text = ""
        self.combo_detector.Text = ""
        self.combo_report_type.Text = "NA"
        self.combo_timing.Text = "GPS - other linking"
        self.combo_timing_device.Text = ""
        self.combo_video_format.Text = ""
        self.combo_exposure.Text = "Other"
        self.txt_other_info.Text = ""
        self.btn_update.Enabled = False
        self.btn_delete.Enabled = False
        self.btn_set_active.Enabled = False
        self.lbl_active.Visible = False
        self.selected_camera_id = None
    
    def add_camera(self, sender, e):
        """Add a new camera"""
        name = self.txt_name.Text.strip()
        detector = self.combo_detector.Text.strip()
        report_type = self.combo_report_type.Text
        timing = self.combo_timing.Text
        timing_device = self.combo_timing_device.Text
        video_format = self.combo_video_format.Text
        exposure_integration = self.combo_exposure.Text
        other_info = self.txt_other_info.Text.strip()
        
        if not name:
            MessageBox.Show("Please enter a camera name.", "Validation Error",
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        if not detector:
            MessageBox.Show("Please enter a detector name.", "Validation Error",
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        self.config.add_camera(name, detector, report_type, timing, timing_device,
                              other_info, video_format, exposure_integration)
        self.config.save_config()
        self.load_cameras()
        self.clear_fields()
        
        MessageBox.Show("Camera added successfully.", "Success",
                      MessageBoxButtons.OK, MessageBoxIcon.Information)
    
    def update_camera(self, sender, e):
        """Update the selected camera"""
        if not self.selected_camera_id:
            return
        
        name = self.txt_name.Text.strip()
        detector = self.combo_detector.Text.strip()
        report_type = self.combo_report_type.Text
        timing = self.combo_timing.Text
        timing_device = self.combo_timing_device.Text
        video_format = self.combo_video_format.Text
        exposure_integration = self.combo_exposure.Text
        other_info = self.txt_other_info.Text.strip()
        
        if not name:
            MessageBox.Show("Please enter a camera name.", "Validation Error",
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        if not detector:
            MessageBox.Show("Please enter a detector name.", "Validation Error",
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        self.config.update_camera(self.selected_camera_id, name, detector, report_type, timing, timing_device,
                                 other_info, video_format, exposure_integration)
        self.config.save_config()
        self.load_cameras()
        
        # Re-select the same camera
        for i, camera in self.camera_map.items():
            if camera.get('id') == self.selected_camera_id:
                self.lst_cameras.SelectedIndex = i
                break
        
        MessageBox.Show("Camera updated successfully.", "Success",
                      MessageBoxButtons.OK, MessageBoxIcon.Information)
    
    def delete_camera(self, sender, e):
        """Delete the selected camera"""
        if not self.selected_camera_id:
            return
        
        result = MessageBox.Show("Are you sure you want to delete this camera?", "Confirm Delete",
                               MessageBoxButtons.YesNo, MessageBoxIcon.Question)
        
        if result == DialogResult.Yes:
            self.config.delete_camera(self.selected_camera_id)
            self.config.save_config()
            self.load_cameras()
            self.clear_fields()
    
    def set_active_camera(self, sender, e):
        """Set the selected camera as active"""
        if not self.selected_camera_id:
            return
        
        self.config.set_active_camera(self.selected_camera_id)
        self.config.save_config()
        self.load_cameras()
        
        # Re-select the same camera
        for i, camera in self.camera_map.items():
            if camera.get('id') == self.selected_camera_id:
                self.lst_cameras.SelectedIndex = i
                break
    
    def close_dialog(self, sender, e):
        """Close the dialog"""
        self.DialogResult = DialogResult.OK
        self.Close()


class EquipmentSelectionDialog(Form):
    """Dialog for selecting telescope and camera for a report"""
    
    def __init__(self, config, theme_manager=None, event=None):
        self.config = config
        self.theme_manager = theme_manager
        self.event = event
        self.selected_telescope_id = None
        self.selected_camera_id = None
        
        # Get active equipment
        active_telescope = config.get_active_telescope()
        active_camera = config.get_active_camera()
        
        self.selected_telescope_id = active_telescope.get('id') if active_telescope else None
        self.selected_camera_id = active_camera.get('id') if active_camera else None
        
        # Setup form
        self.Text = "Select Equipment for Report"
        self.Size = Size(500, 360)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.StartPosition = FormStartPosition.CenterParent
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        self.setup_ui()
        
        if theme_manager:
            theme_colors = theme_manager.get_current_theme()
            apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup the UI controls"""
        sf = 1.0  # Scale factor
        
        # Event info label
        if self.event:
            lbl_event = Label()
            event_name = self.event.get_asteroid_display_name() if hasattr(self.event, 'get_asteroid_display_name') else self.event.get('asteroid_name', 'Unknown')
            station_name = self.event.station_name if hasattr(self.event, 'station_name') else ''
            lbl_event.Text = "Event: {}    Station: {}".format(event_name, station_name)
            lbl_event.Location = Point(int(20 * sf), int(10 * sf))
            lbl_event.Size = Size(int(450 * sf), int(20 * sf))
            lbl_event.Font = Font(lbl_event.Font, FontStyle.Bold)
            self.Controls.Add(lbl_event)
        
        # Info label
        lbl_info = Label()
        lbl_info.Text = "Select the telescope and camera to use for this report:"
        lbl_info.Location = Point(int(20 * sf), int(40 * sf))
        lbl_info.Size = Size(int(450 * sf), int(20 * sf))
        self.Controls.Add(lbl_info)
        
        # Telescope selection
        lbl_telescope = Label()
        lbl_telescope.Text = "Telescope:"
        lbl_telescope.Location = Point(int(20 * sf), int(80 * sf))
        lbl_telescope.Size = Size(int(100 * sf), int(20 * sf))
        self.Controls.Add(lbl_telescope)
        
        self.combo_telescope = ComboBox()
        self.combo_telescope.Location = Point(int(120 * sf), int(80 * sf))
        self.combo_telescope.Size = Size(int(330 * sf), int(20 * sf))
        self.combo_telescope.DropDownStyle = ComboBoxStyle.DropDownList
        self.Controls.Add(self.combo_telescope)
        
        # Load telescopes
        telescopes = self.config.get_telescopes()
        active_telescope = self.config.get_active_telescope()
        active_telescope_id = active_telescope.get('id') if active_telescope else None
        
        selected_index = -1
        for i, telescope in enumerate(telescopes):
            name = telescope.get('name', 'Unnamed')
            if telescope.get('id') == active_telescope_id:
                name = "★ " + name  # Mark active with star
                selected_index = i
            self.combo_telescope.Items.Add(name)
            
        if selected_index >= 0:
            self.combo_telescope.SelectedIndex = selected_index
        elif self.combo_telescope.Items.Count > 0:
            self.combo_telescope.SelectedIndex = 0
        
        # Camera selection
        lbl_camera = Label()
        lbl_camera.Text = "Camera:"
        lbl_camera.Location = Point(int(20 * sf), int(125 * sf))
        lbl_camera.Size = Size(int(100 * sf), int(20 * sf))
        self.Controls.Add(lbl_camera)
        
        self.combo_camera = ComboBox()
        self.combo_camera.Location = Point(int(120 * sf), int(125 * sf))
        self.combo_camera.Size = Size(int(330 * sf), int(20 * sf))
        self.combo_camera.DropDownStyle = ComboBoxStyle.DropDownList
        self.Controls.Add(self.combo_camera)
        
        # Load cameras
        cameras = self.config.get_cameras()
        active_camera = self.config.get_active_camera()
        active_camera_id = active_camera.get('id') if active_camera else None
        
        selected_index = -1
        for i, camera in enumerate(cameras):
            name = camera.get('name', 'Unnamed')
            # Show report type
            report_type = camera.get('report_type', 'NA')
            # Migrate old 'Both' to display as 'NA'
            if report_type == 'Both':
                report_type = 'NA'
            name = f"{name} ({report_type})"
            if camera.get('id') == active_camera_id:
                name = "★ " + name  # Mark active with star
                selected_index = i
            self.combo_camera.Items.Add(name)
            
        if selected_index >= 0:
            self.combo_camera.SelectedIndex = selected_index
        elif self.combo_camera.Items.Count > 0:
            self.combo_camera.SelectedIndex = 0
        
        # Note
        lbl_note = Label()
        lbl_note.Text = "★ indicates the currently active equipment.\nThis selection is only for this report and will not change your active equipment."
        lbl_note.Location = Point(int(20 * sf), int(170 * sf))
        lbl_note.Size = Size(int(450 * sf), int(40 * sf))
        lbl_note.ForeColor = Color.Gray
        self.Controls.Add(lbl_note)
        
        # Buttons
        btn_ok = Button()
        btn_ok.Text = "Generate Report"
        btn_ok.Location = Point(int(180 * sf), int(280 * sf))
        btn_ok.Size = Size(int(130 * sf), int(30 * sf))
        btn_ok.Click += self.ok_click
        self.Controls.Add(btn_ok)
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(int(320 * sf), int(280 * sf))
        btn_cancel.Size = Size(int(100 * sf), int(30 * sf))
        btn_cancel.Click += self.cancel_click
        self.Controls.Add(btn_cancel)
    
    def ok_click(self, sender, e):
        """Handle OK button click"""
        # Check if equipment is selected
        if self.combo_telescope.Items.Count == 0:
            MessageBox.Show("No telescopes configured. Please add a telescope first via Tools → Manage Telescopes.", 
                          "No Telescopes", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            self.DialogResult = DialogResult.Cancel
            self.Close()
            return
        
        if self.combo_camera.Items.Count == 0:
            MessageBox.Show("No cameras configured. Please add a camera first via Tools → Manage Cameras.", 
                          "No Cameras", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            self.DialogResult = DialogResult.Cancel
            self.Close()
            return
        
        # Get selected telescope
        if self.combo_telescope.SelectedIndex >= 0:
            telescopes = self.config.get_telescopes()
            if self.combo_telescope.SelectedIndex < len(telescopes):
                telescope = telescopes[self.combo_telescope.SelectedIndex]
                self.selected_telescope_id = telescope.get('id')
                print("EquipmentSelectionDialog: Selected telescope ID = {}".format(self.selected_telescope_id))
                print("EquipmentSelectionDialog: Selected telescope name = {}".format(telescope.get('name')))
        
        # Get selected camera
        if self.combo_camera.SelectedIndex >= 0:
            cameras = self.config.get_cameras()
            if self.combo_camera.SelectedIndex < len(cameras):
                camera = cameras[self.combo_camera.SelectedIndex]
                self.selected_camera_id = camera.get('id')
                print("EquipmentSelectionDialog: Selected camera ID = {}".format(self.selected_camera_id))
                print("EquipmentSelectionDialog: Selected camera model = {}".format(camera.get('model')))
        
        self.DialogResult = DialogResult.OK
        self.Close()
    
    def cancel_click(self, sender, e):
        """Handle Cancel button click"""
        self.DialogResult = DialogResult.Cancel
        self.Close()
    
    def get_selected_telescope_id(self):
        """Get the selected telescope ID"""
        return self.selected_telescope_id
    
    def get_selected_camera_id(self):
        """Get the selected camera ID"""
        return self.selected_camera_id
