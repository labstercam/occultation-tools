"""
Comprehensive Report Generation Dialog
Combines report type, equipment, observation type, and file selection in one dialog
"""

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("System")

import os
import System
from System import Array
from System.Drawing import Point, Size, Color, Font, FontStyle
from System.Windows.Forms import (
    Form, Button, Label, ListBox, Panel, TextBox, GroupBox, RadioButton, ComboBox,
    AnchorStyles, DockStyle, Padding, DialogResult,
    FormStartPosition, MessageBox, MessageBoxButtons, MessageBoxIcon,
    FolderBrowserDialog, SelectionMode, ComboBoxStyle
)
from theme import apply_theme_to_control


class ComprehensiveReportDialog(Form):
    """Single comprehensive dialog for all report generation settings"""
    
    def __init__(self, config, theme_manager, event):
        """Initialize the comprehensive dialog
        
        Args:
            config: ConfigManager instance
            theme_manager: Theme manager for consistent styling
            event: Event object for display
        """
        Form.__init__(self)
        self.config = config
        self.theme_manager = theme_manager
        self.event = event
        
        # Return values
        self.report_type = None
        self.telescope_id = None
        self.camera_id = None
        self.observation_type = None
        self.selected_aota_path = None
        self.selected_tangra_path = None
        self.selected_aota_report_path = None
        self.clouds = None
        self.stability = None
        self.other_conditions = None
        
        # File lists
        self.aota_files = []
        self.csv_files = []
        self.aota_report_files = []
        self.current_folder = None
        
        self.setup_ui()
        
        # Load saved preferences
        self.load_preferences()
        
        # Update button state after loading preferences
        self.update_button_state()
        
        # Apply theme
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup user interface"""
        self.Text = "Generate Report"
        self.Size = Size(1000, 820)  # Increased from 720 to 820 for Conditions section
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        # Main scroll panel
        main_panel = Panel()
        main_panel.Location = Point(10, 10)
        main_panel.Size = Size(970, 725)  # Increased from 625 to 725 for Conditions section
        main_panel.AutoScroll = True
        self.Controls.Add(main_panel)
        
        y_pos = 10
        
        # Event header
        lbl_event = Label()
        lbl_event.Text = f"Generating Report for: {self.event.get_asteroid_display_name()}"
        lbl_event.Font = Font(lbl_event.Font.FontFamily, 12, FontStyle.Bold)
        lbl_event.Location = Point(10, y_pos)
        lbl_event.Size = Size(940, 30)
        main_panel.Controls.Add(lbl_event)
        y_pos += 40
        
        # ===== SECTION 1: REPORT TYPE =====
        grp_report = GroupBox()
        grp_report.Text = "1. Report Format"
        grp_report.Location = Point(10, y_pos)
        grp_report.Size = Size(940, 90)
        main_panel.Controls.Add(grp_report)
        
        self.rb_na = RadioButton()
        self.rb_na.Text = "IOTA North America (V5.6.12r)"
        self.rb_na.Location = Point(20, 25)
        self.rb_na.Size = Size(280, 25)
        self.rb_na.CheckedChanged += self.report_type_changed
        grp_report.Controls.Add(self.rb_na)
        
        self.rb_tt = RadioButton()
        self.rb_tt.Text = "Trans-Tasman / RASNZ (V4.1.2.G)"
        self.rb_tt.Location = Point(20, 50)
        self.rb_tt.Size = Size(280, 25)
        self.rb_tt.CheckedChanged += self.report_type_changed
        grp_report.Controls.Add(self.rb_tt)
        
        y_pos += 100
        
        # ===== SECTION 2: EQUIPMENT =====
        grp_equipment = GroupBox()
        grp_equipment.Text = "2. Equipment Selection"
        grp_equipment.Location = Point(10, y_pos)
        grp_equipment.Size = Size(940, 90)
        main_panel.Controls.Add(grp_equipment)
        
        # Telescope
        lbl_telescope = Label()
        lbl_telescope.Text = "Telescope:"
        lbl_telescope.Location = Point(20, 30)
        lbl_telescope.Size = Size(100, 20)
        grp_equipment.Controls.Add(lbl_telescope)
        
        self.combo_telescope = ComboBox()
        self.combo_telescope.Location = Point(130, 28)
        self.combo_telescope.Size = Size(350, 25)
        self.combo_telescope.DropDownStyle = ComboBoxStyle.DropDownList
        self.combo_telescope.SelectedIndexChanged += self.equipment_changed
        grp_equipment.Controls.Add(self.combo_telescope)
        
        btn_manage_telescope = Button()
        btn_manage_telescope.Text = "Manage..."
        btn_manage_telescope.Location = Point(490, 26)
        btn_manage_telescope.Size = Size(100, 25)
        btn_manage_telescope.Click += self.manage_telescopes_click
        grp_equipment.Controls.Add(btn_manage_telescope)
        
        # Camera
        lbl_camera = Label()
        lbl_camera.Text = "Camera:"
        lbl_camera.Location = Point(20, 58)
        lbl_camera.Size = Size(100, 20)
        grp_equipment.Controls.Add(lbl_camera)
        
        self.combo_camera = ComboBox()
        self.combo_camera.Location = Point(130, 56)
        self.combo_camera.Size = Size(350, 25)
        self.combo_camera.DropDownStyle = ComboBoxStyle.DropDownList
        self.combo_camera.SelectedIndexChanged += self.equipment_changed
        grp_equipment.Controls.Add(self.combo_camera)
        
        btn_manage_camera = Button()
        btn_manage_camera.Text = "Manage..."
        btn_manage_camera.Location = Point(490, 54)
        btn_manage_camera.Size = Size(100, 25)
        btn_manage_camera.Click += self.manage_cameras_click
        grp_equipment.Controls.Add(btn_manage_camera)
        
        y_pos += 100
        
        # ===== SECTION 3: OBSERVATION TYPE =====
        grp_obs_type = GroupBox()
        grp_obs_type.Text = "3. Observation Result"
        grp_obs_type.Location = Point(10, y_pos)
        grp_obs_type.Size = Size(940, 120)
        main_panel.Controls.Add(grp_obs_type)
        
        self.rb_positive = RadioButton()
        self.rb_positive.Text = "Positive - Observed disappearance and reappearance (AOTA required)"
        self.rb_positive.Location = Point(20, 25)
        self.rb_positive.Size = Size(500, 25)
        self.rb_positive.Checked = True
        self.rb_positive.CheckedChanged += self.observation_type_changed
        grp_obs_type.Controls.Add(self.rb_positive)
        
        self.rb_negative = RadioButton()
        self.rb_negative.Text = "Negative - No occultation occurred (AOTA optional)"
        self.rb_negative.Location = Point(20, 50)
        self.rb_negative.Size = Size(500, 25)
        self.rb_negative.CheckedChanged += self.observation_type_changed
        grp_obs_type.Controls.Add(self.rb_negative)
        
        self.rb_unsure = RadioButton()
        self.rb_unsure.Text = "Unsure - Possible event but uncertain (AOTA required)"
        self.rb_unsure.Location = Point(20, 75)
        self.rb_unsure.Size = Size(500, 25)
        self.rb_unsure.CheckedChanged += self.observation_type_changed
        grp_obs_type.Controls.Add(self.rb_unsure)
        
        y_pos += 130
        
        # ===== SECTION 4: FILE SELECTION =====
        grp_files = GroupBox()
        grp_files.Text = "4. Observation Files"
        grp_files.Location = Point(10, y_pos)
        grp_files.Size = Size(940, 190)
        main_panel.Controls.Add(grp_files)
        
        # Folder selection
        lbl_folder = Label()
        lbl_folder.Text = "Folder containing AOTA, Tangra CSV, and AOTA Report files:"
        lbl_folder.Location = Point(15, 25)
        lbl_folder.Size = Size(900, 20)
        grp_files.Controls.Add(lbl_folder)
        
        self.folder_textbox = TextBox()
        self.folder_textbox.Location = Point(15, 48)
        self.folder_textbox.Size = Size(800, 25)
        self.folder_textbox.ReadOnly = True
        grp_files.Controls.Add(self.folder_textbox)
        
        btn_browse = Button()
        btn_browse.Text = "Browse..."
        btn_browse.Location = Point(820, 46)
        btn_browse.Size = Size(100, 25)
        btn_browse.Click += self.browse_folder_click
        grp_files.Controls.Add(btn_browse)
        
        # Three-column layout for file lists
        # AOTA files (left)
        lbl_aota = Label()
        lbl_aota.Text = "AOTA Files:"
        lbl_aota.Location = Point(15, 85)
        lbl_aota.Size = Size(120, 20)
        grp_files.Controls.Add(lbl_aota)
        
        self.aota_count_label = Label()
        self.aota_count_label.Text = "No folder"
        self.aota_count_label.Location = Point(135, 85)
        self.aota_count_label.Size = Size(165, 20)
        self.aota_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.aota_count_label)
        
        self.aota_listbox = ListBox()
        self.aota_listbox.Location = Point(15, 108)
        self.aota_listbox.Size = Size(285, 65)
        self.aota_listbox.SelectionMode = SelectionMode.One
        self.aota_listbox.SelectedIndexChanged += self.selection_changed
        grp_files.Controls.Add(self.aota_listbox)
        
        # Tangra CSV files (middle)
        lbl_csv = Label()
        lbl_csv.Text = "Tangra CSV:"
        lbl_csv.Location = Point(315, 85)
        lbl_csv.Size = Size(120, 20)
        grp_files.Controls.Add(lbl_csv)
        
        self.csv_count_label = Label()
        self.csv_count_label.Text = "No folder"
        self.csv_count_label.Location = Point(435, 85)
        self.csv_count_label.Size = Size(165, 20)
        self.csv_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.csv_count_label)
        
        self.csv_listbox = ListBox()
        self.csv_listbox.Location = Point(315, 108)
        self.csv_listbox.Size = Size(285, 65)
        self.csv_listbox.SelectionMode = SelectionMode.One
        self.csv_listbox.SelectedIndexChanged += self.selection_changed
        grp_files.Controls.Add(self.csv_listbox)
        
        # AOTA Report files (right)
        lbl_report = Label()
        lbl_report.Text = "AOTA Report:"
        lbl_report.Location = Point(615, 85)
        lbl_report.Size = Size(120, 20)
        grp_files.Controls.Add(lbl_report)
        
        self.report_count_label = Label()
        self.report_count_label.Text = "No folder"
        self.report_count_label.Location = Point(735, 85)
        self.report_count_label.Size = Size(185, 20)
        self.report_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.report_count_label)
        
        self.report_listbox = ListBox()
        self.report_listbox.Location = Point(615, 108)
        self.report_listbox.Size = Size(305, 65)
        self.report_listbox.SelectionMode = SelectionMode.One
        self.report_listbox.SelectedIndexChanged += self.selection_changed
        grp_files.Controls.Add(self.report_listbox)
        
        y_pos += 200
        
        # ===== SECTION 5: CONDITIONS =====
        grp_conditions = GroupBox()
        grp_conditions.Text = "5. Conditions"
        grp_conditions.Location = Point(10, y_pos)
        grp_conditions.Size = Size(940, 80)
        main_panel.Controls.Add(grp_conditions)
        
        # Clouds
        lbl_clouds = Label()
        lbl_clouds.Text = "Clouds:"
        lbl_clouds.Location = Point(20, 30)
        lbl_clouds.Size = Size(80, 20)
        grp_conditions.Controls.Add(lbl_clouds)
        
        self.combo_clouds = ComboBox()
        self.combo_clouds.Location = Point(110, 28)
        self.combo_clouds.Size = Size(180, 25)
        self.combo_clouds.DropDownStyle = ComboBoxStyle.DropDownList
        self.combo_clouds.Items.AddRange(Array[object](["Clear", "Fog", "Thin cloud < 2", "Thick cloud > 2", "Broken cloud", "Star faint", "Averted vision"]))
        self.combo_clouds.SelectedIndex = 0
        grp_conditions.Controls.Add(self.combo_clouds)
        
        # Stability
        lbl_stability = Label()
        lbl_stability.Text = "Stability:"
        lbl_stability.Location = Point(310, 30)
        lbl_stability.Size = Size(80, 20)
        grp_conditions.Controls.Add(lbl_stability)
        
        self.combo_stability = ComboBox()
        self.combo_stability.Location = Point(400, 28)
        self.combo_stability.Size = Size(180, 25)
        self.combo_stability.DropDownStyle = ComboBoxStyle.DropDownList
        self.combo_stability.Items.AddRange(Array[object](["Steady", "Slight flickering", "Strong flickering"]))
        self.combo_stability.SelectedIndex = 0
        grp_conditions.Controls.Add(self.combo_stability)
        
        # Other Conditions
        lbl_other = Label()
        lbl_other.Text = "Other Conditions:"
        lbl_other.Location = Point(600, 30)
        lbl_other.Size = Size(130, 20)
        grp_conditions.Controls.Add(lbl_other)
        
        self.txt_other_conditions = TextBox()
        self.txt_other_conditions.Location = Point(730, 28)
        self.txt_other_conditions.Size = Size(190, 25)
        grp_conditions.Controls.Add(self.txt_other_conditions)
        
        # ===== BOTTOM BUTTONS =====
        self.status_label = Label()
        self.status_label.Text = "Please complete all sections above"
        self.status_label.Location = Point(20, 755)  # Moved down to 755
        self.status_label.Size = Size(700, 20)
        self.status_label.ForeColor = Color.Gray
        self.Controls.Add(self.status_label)
        
        self.btn_generate = Button()
        self.btn_generate.Text = "Generate Report"
        self.btn_generate.Location = Point(750, 750)  # Moved down to 750
        self.btn_generate.Size = Size(140, 35)
        self.btn_generate.Enabled = False
        self.btn_generate.Click += self.generate_click
        self.Controls.Add(self.btn_generate)
        self.AcceptButton = self.btn_generate
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(900, 750)  # Moved down to 750
        btn_cancel.Size = Size(80, 35)
        btn_cancel.Click += self.cancel_click
        self.Controls.Add(btn_cancel)
        self.CancelButton = btn_cancel
    
    def load_preferences(self):
        """Load saved preferences and populate fields"""
        # Load report type preference
        last_report_type = self.config.get_last_report_type()
        if last_report_type == 'trans_tasman':
            self.rb_tt.Checked = True
        else:
            self.rb_na.Checked = True
        
        # Load equipment
        self.load_equipment()
        
        # Try to browse to last folder's parent
        last_folder = self.config.get_last_report_folder()
        if last_folder and os.path.exists(last_folder):
            # Don't auto-scan yet, just remember for browse dialog
            self.remembered_folder = last_folder
        else:
            self.remembered_folder = None
    
    def load_equipment(self):
        """Load telescopes and cameras into dropdowns"""
        # Load telescopes
        self.combo_telescope.Items.Clear()
        telescopes = self.config.get_telescopes()
        active_telescope = self.config.get_active_telescope()
        active_tel_id = active_telescope.get('id') if active_telescope else None
        
        if not telescopes:
            # Add placeholder when no telescopes configured
            self.combo_telescope.Items.Add("No telescopes configured - click Manage...")
            self.combo_telescope.SelectedIndex = 0
            self.combo_telescope.Enabled = False
        else:
            self.combo_telescope.Enabled = True
            selected_index = 0
            for i, telescope in enumerate(telescopes):
                name = telescope.get('name', 'Unnamed')
                if telescope.get('id') == active_tel_id:
                    name = "★ " + name
                    selected_index = i
                self.combo_telescope.Items.Add(name)
            
            self.combo_telescope.SelectedIndex = selected_index
        
        # Load cameras - FILTER BY CURRENT REPORT TYPE
        self.combo_camera.Items.Clear()
        all_cameras = self.config.get_cameras()
        
        # Determine current report type
        if self.rb_na.Checked:
            current_report_type = 'NA'
        elif self.rb_tt.Checked:
            current_report_type = 'TT'
        else:
            current_report_type = None  # No report type selected yet
        
        # Filter cameras by report_type (exact match only)
        if current_report_type:
            cameras = [c for c in all_cameras 
                      if c.get('report_type', 'NA') == current_report_type]
        else:
            cameras = all_cameras  # Show all if no report type selected
        
        active_camera = self.config.get_active_camera()
        active_cam_id = active_camera.get('id') if active_camera else None
        
        if not cameras:
            # No cameras match this report type
            msg = f"No cameras for {current_report_type} - click Manage..." if current_report_type else "No cameras configured - click Manage..."
            self.combo_camera.Items.Add(msg)
            self.combo_camera.SelectedIndex = 0
            self.combo_camera.Enabled = False
        else:
            self.combo_camera.Enabled = True
            selected_index = 0
            active_found = False
            
            for i, camera in enumerate(cameras):
                name = camera.get('name', 'Unnamed')
                if camera.get('id') == active_cam_id:
                    name = "★ " + name
                    selected_index = i
                    active_found = True
                self.combo_camera.Items.Add(name)
            
            # Only select active if it's in this filtered list
            if active_found:
                self.combo_camera.SelectedIndex = selected_index
            elif cameras:
                self.combo_camera.SelectedIndex = 0
    
    def manage_telescopes_click(self, sender, e):
        """Open telescope management dialog"""
        from equipment_dialogs import TelescopeManagerDialog
        dialog = TelescopeManagerDialog(self.config, self.theme_manager)
        dialog.ShowDialog()
        self.load_equipment()
    
    def manage_cameras_click(self, sender, e):
        """Open camera management dialog"""
        from equipment_dialogs import CameraManagerDialog
        dialog = CameraManagerDialog(self.config, self.theme_manager)
        dialog.ShowDialog()
        self.load_equipment()
    
    def report_type_changed(self, sender, e):
        """Handle report type radio button change"""
        self.load_equipment()  # Reload to filter cameras by report type
        self.update_button_state()
    
    def equipment_changed(self, sender, e):
        """Handle equipment dropdown change"""
        self.update_button_state()
    
    def observation_type_changed(self, sender, e):
        """Handle observation type radio button change"""
        self.update_button_state()
    
    def browse_folder_click(self, sender, e):
        """Handle browse folder button click"""
        dialog = FolderBrowserDialog()
        dialog.Description = "Select folder containing AOTA and Tangra CSV files"
        
        # Start in remembered folder if available
        if hasattr(self, 'remembered_folder') and self.remembered_folder and os.path.exists(self.remembered_folder):
            dialog.SelectedPath = self.remembered_folder
        else:
            # Default to Reports folder
            reports_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Reports')
            if os.path.exists(reports_folder):
                dialog.SelectedPath = reports_folder
        
        if dialog.ShowDialog() == DialogResult.OK:
            folder_path = dialog.SelectedPath
            self.current_folder = folder_path
            self.folder_textbox.Text = folder_path
            
            # Save parent folder for next time (one level up from selected folder)
            parent_folder = os.path.dirname(folder_path)
            self.config.set_last_report_folder(parent_folder)
            
            self.scan_folder(folder_path)
    
    def scan_folder(self, folder_path):
        """Scan folder for AOTA, CSV, and AOTA Report files"""
        self.aota_files = []
        self.csv_files = []
        self.aota_report_files = []
        self.aota_listbox.Items.Clear()
        self.csv_listbox.Items.Clear()
        self.report_listbox.Items.Clear()
        
        if not os.path.exists(folder_path):
            self.aota_count_label.Text = "Folder not found"
            self.csv_count_label.Text = "Folder not found"
            self.report_count_label.Text = "Folder not found"
            return
        
        try:
            for filename in os.listdir(folder_path):
                full_path = os.path.join(folder_path, filename)
                
                if filename.lower().endswith('.aota.xml'):
                    self.aota_files.append(full_path)
                    self.aota_listbox.Items.Add(filename)
                elif filename.lower().endswith('_aota_report.txt'):
                    self.aota_report_files.append(full_path)
                    self.report_listbox.Items.Add(filename)
                elif filename.lower().endswith('.csv'):
                    self.csv_files.append(full_path)
                    self.csv_listbox.Items.Add(filename)
            
            # Update count labels
            aota_count = len(self.aota_files)
            csv_count = len(self.csv_files)
            report_count = len(self.aota_report_files)
            
            if aota_count == 0:
                self.aota_count_label.Text = "No AOTA files found"
            elif aota_count == 1:
                self.aota_count_label.Text = "1 file found"
            else:
                self.aota_count_label.Text = f"{aota_count} files found"
            
            if csv_count == 0:
                self.csv_count_label.Text = "No CSV files found"
            elif csv_count == 1:
                self.csv_count_label.Text = "1 file found"
            else:
                self.csv_count_label.Text = f"{csv_count} files found"
            
            if report_count == 0:
                self.report_count_label.Text = "No Report files found"
            elif report_count == 1:
                self.report_count_label.Text = "1 file found"
            else:
                self.report_count_label.Text = f"{report_count} files found"
            
            # Auto-select first files
            if aota_count > 0:
                self.aota_listbox.SelectedIndex = 0
            if csv_count > 0:
                self.csv_listbox.SelectedIndex = 0
            if report_count > 0:
                self.report_listbox.SelectedIndex = 0
            
            self.update_button_state()
            
        except Exception as ex:
            MessageBox.Show(
                f"Error scanning folder:\n\n{str(ex)}",
                "Scan Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            self.aota_count_label.Text = "Error"
            self.csv_count_label.Text = "Error"
            self.report_count_label.Text = "Error"
    
    def selection_changed(self, sender, e):
        """Handle file selection changed"""
        self.update_button_state()
    
    def update_button_state(self):
        """Update generate button state and status message"""
        # Check all requirements
        has_report_type = self.rb_na.Checked or self.rb_tt.Checked
        
        # Check if equipment is configured (not just selected)
        telescopes = self.config.get_telescopes()
        cameras = self.config.get_cameras()
        has_telescope = len(telescopes) > 0 and self.combo_telescope.SelectedIndex >= 0
        has_camera = len(cameras) > 0 and self.combo_camera.SelectedIndex >= 0
        
        aota_selected = self.aota_listbox.SelectedIndex >= 0
        csv_selected = self.csv_listbox.SelectedIndex >= 0
        report_selected = self.report_listbox.SelectedIndex >= 0
        
        # Determine observation type
        if self.rb_positive.Checked:
            obs_type = "Positive"
        elif self.rb_negative.Checked:
            obs_type = "Negative"
        elif self.rb_unsure.Checked:
            obs_type = "Unsure"
        else:
            obs_type = None
        
        # Build status message
        missing = []
        if not has_report_type:
            missing.append("report format")
        if not has_telescope:
            missing.append("telescope")
        if not has_camera:
            missing.append("camera")
        if not csv_selected:
            missing.append("Tangra CSV file")
        
        # AOTA requirement depends on observation type - either AOTA.xml OR AOTA Report is needed
        if obs_type in ["Positive", "Unsure"] and not aota_selected and not report_selected:
            missing.append("AOTA file or AOTA Report")
        
        if missing:
            self.status_label.Text = "Missing: " + ", ".join(missing)
            self.status_label.ForeColor = Color.Red
            self.btn_generate.Enabled = False
        else:
            self.status_label.Text = "Ready to generate report"
            self.status_label.ForeColor = Color.Green
            self.btn_generate.Enabled = True
    
    def generate_click(self, sender, e):
        """Handle generate button click"""
        # Collect all selections
        
        # Report type
        if self.rb_na.Checked:
            self.report_type = 'north_america'
        elif self.rb_tt.Checked:
            self.report_type = 'trans_tasman'
        
        # Save report type preference
        self.config.set_last_report_type(self.report_type)
        
        # Equipment
        telescopes = self.config.get_telescopes()
        all_cameras = self.config.get_cameras()
        
        # Filter cameras by report type (exact match only)
        if self.report_type == 'north_america':
            cameras = [c for c in all_cameras if c.get('report_type', 'NA') == 'NA']
        elif self.report_type == 'trans_tasman':
            cameras = [c for c in all_cameras if c.get('report_type', 'NA') == 'TT']
        else:
            cameras = all_cameras
        
        if self.combo_telescope.SelectedIndex >= 0 and self.combo_telescope.SelectedIndex < len(telescopes):
            telescope = telescopes[self.combo_telescope.SelectedIndex]
            self.telescope_id = telescope.get('id')
        
        if self.combo_camera.SelectedIndex >= 0 and self.combo_camera.SelectedIndex < len(cameras):
            camera = cameras[self.combo_camera.SelectedIndex]
            self.camera_id = camera.get('id')
        
        # Observation type
        if self.rb_positive.Checked:
            self.observation_type = "Positive"
        elif self.rb_negative.Checked:
            self.observation_type = "Negative"
        elif self.rb_unsure.Checked:
            self.observation_type = "Unsure"
        
        # Files
        if self.csv_listbox.SelectedIndex >= 0:
            self.selected_tangra_path = self.csv_files[self.csv_listbox.SelectedIndex]
        else:
            MessageBox.Show(
                "Please select a Tangra CSV file.",
                "No CSV File",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return
        
        # AOTA or AOTA Report - at least one required for Positive/Unsure
        if self.aota_listbox.SelectedIndex >= 0:
            self.selected_aota_path = self.aota_files[self.aota_listbox.SelectedIndex]
        
        if self.report_listbox.SelectedIndex >= 0:
            self.selected_aota_report_path = self.aota_report_files[self.report_listbox.SelectedIndex]
        
        # For Positive/Unsure, need at least one of AOTA.xml or AOTA Report
        if self.observation_type in ["Positive", "Unsure"]:
            if not self.selected_aota_path and not self.selected_aota_report_path:
                MessageBox.Show(
                    f"Either AOTA file or AOTA Report is required for {self.observation_type} observations.",
                    "Missing AOTA Data",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                )
                return
        
        # Conditions
        if self.combo_clouds.SelectedIndex >= 0 and self.combo_clouds.SelectedItem:
            self.clouds = str(self.combo_clouds.SelectedItem)
        if self.combo_stability.SelectedIndex >= 0 and self.combo_stability.SelectedItem:
            self.stability = str(self.combo_stability.SelectedItem)
        self.other_conditions = self.txt_other_conditions.Text.strip() if self.txt_other_conditions.Text else None
        
        self.DialogResult = DialogResult.OK
        self.Close()
    
    def cancel_click(self, sender, e):
        """Handle cancel button click"""
        self.DialogResult = DialogResult.Cancel
        self.Close()
    
    # Getters for main_gui
    def get_report_type(self):
        return self.report_type
    
    def get_telescope_id(self):
        return self.telescope_id
    
    def get_camera_id(self):
        return self.camera_id
    
    def get_observation_type(self):
        return self.observation_type
    
    def get_selected_aota_path(self):
        return self.selected_aota_path
    
    def get_selected_tangra_path(self):
        return self.selected_tangra_path
    
    def get_selected_aota_report_path(self):
        return self.selected_aota_report_path
    
    def get_clouds(self):
        return self.clouds
    
    def get_stability(self):
        return self.stability
    
    def get_other_conditions(self):
        return self.other_conditions
