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
        self.pyote_files = []
        self.pyote_events = []       # list of dicts from current pyote file
        self.selected_pyote_path = None
        self.selected_pyote_event_index = -1
        self.current_folder = None
        
        # Timestamp check state
        self._ts_summary = None
        self._d_time_seconds = None
        self._r_time_seconds = None
        
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
        self.Size = Size(1000, 1071)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        # Main scroll panel
        main_panel = Panel()
        main_panel.Location = Point(10, 10)
        main_panel.Size = Size(970, 940)
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
        grp_report.Size = Size(940, 115)
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

        self.rb_sodis = RadioButton()
        self.rb_sodis.Text = "IOTA-ES / SODIS (Form 2.03)"
        self.rb_sodis.Location = Point(20, 75)
        self.rb_sodis.Size = Size(280, 25)
        self.rb_sodis.CheckedChanged += self.report_type_changed
        grp_report.Controls.Add(self.rb_sodis)
        
        y_pos += 125
        
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
        grp_files.Size = Size(940, 415)
        main_panel.Controls.Add(grp_files)
        
        # Folder selection
        lbl_folder = Label()
        lbl_folder.Text = "Folder containing AOTA, light curve CSV, and AOTA Report files:"
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
        # Tangra CSV files (left)
        lbl_csv = Label()
        lbl_csv.Text = "Light Curve File:"
        lbl_csv.Location = Point(15, 85)
        lbl_csv.Size = Size(130, 20)
        grp_files.Controls.Add(lbl_csv)
        
        self.csv_count_label = Label()
        self.csv_count_label.Text = "No folder"
        self.csv_count_label.Location = Point(145, 85)
        self.csv_count_label.Size = Size(155, 20)
        self.csv_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.csv_count_label)
        
        self.csv_listbox = ListBox()
        self.csv_listbox.Location = Point(15, 108)
        self.csv_listbox.Size = Size(285, 65)
        self.csv_listbox.SelectionMode = SelectionMode.One
        self.csv_listbox.SelectedIndexChanged += self.selection_changed
        grp_files.Controls.Add(self.csv_listbox)

        self.csv_preview_label = Label()
        self.csv_preview_label.Text = "Observing times: -"
        self.csv_preview_label.Location = Point(15, 176)
        self.csv_preview_label.Size = Size(285, 40)
        self.csv_preview_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.csv_preview_label)
        
        # AOTA files (middle)
        lbl_aota = Label()
        lbl_aota.Text = "AOTA Files:"
        lbl_aota.Location = Point(315, 85)
        lbl_aota.Size = Size(120, 20)
        grp_files.Controls.Add(lbl_aota)
        
        self.aota_count_label = Label()
        self.aota_count_label.Text = "No folder"
        self.aota_count_label.Location = Point(435, 85)
        self.aota_count_label.Size = Size(165, 20)
        self.aota_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.aota_count_label)
        
        self.aota_listbox = ListBox()
        self.aota_listbox.Location = Point(315, 108)
        self.aota_listbox.Size = Size(285, 65)
        self.aota_listbox.SelectionMode = SelectionMode.One
        self.aota_listbox.SelectedIndexChanged += self.selection_changed
        grp_files.Controls.Add(self.aota_listbox)

        self.aota_preview_label = Label()
        self.aota_preview_label.Text = "D/R: -"
        self.aota_preview_label.Location = Point(315, 176)
        self.aota_preview_label.Size = Size(285, 40)
        self.aota_preview_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.aota_preview_label)
        
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

        self.report_preview_label = Label()
        self.report_preview_label.Text = "D/R: -"
        self.report_preview_label.Location = Point(615, 176)
        self.report_preview_label.Size = Size(305, 40)
        self.report_preview_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.report_preview_label)

        # PyOTE Metrics row (full-width, below the three columns)
        lbl_pyote = Label()
        lbl_pyote.Text = "PyOTE Metrics:"
        lbl_pyote.Location = Point(15, 225)
        lbl_pyote.Size = Size(120, 20)
        grp_files.Controls.Add(lbl_pyote)

        self.pyote_count_label = Label()
        self.pyote_count_label.Text = "No folder"
        self.pyote_count_label.Location = Point(135, 225)
        self.pyote_count_label.Size = Size(200, 20)
        self.pyote_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.pyote_count_label)

        lbl_pyote_event = Label()
        lbl_pyote_event.Text = "Events:"
        lbl_pyote_event.Location = Point(460, 225)
        lbl_pyote_event.Size = Size(60, 20)
        grp_files.Controls.Add(lbl_pyote_event)

        self.pyote_event_count_label = Label()
        self.pyote_event_count_label.Text = "-"
        self.pyote_event_count_label.Location = Point(525, 225)
        self.pyote_event_count_label.Size = Size(210, 20)
        self.pyote_event_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.pyote_event_count_label)

        self.pyote_listbox = ListBox()
        self.pyote_listbox.Location = Point(15, 245)
        self.pyote_listbox.Size = Size(430, 55)
        self.pyote_listbox.SelectionMode = SelectionMode.One
        self.pyote_listbox.SelectedIndexChanged += self._pyote_file_selection_changed
        grp_files.Controls.Add(self.pyote_listbox)

        self.pyote_event_listbox = ListBox()
        self.pyote_event_listbox.Location = Point(460, 245)
        self.pyote_event_listbox.Size = Size(460, 55)
        self.pyote_event_listbox.SelectionMode = SelectionMode.One
        self.pyote_event_listbox.SelectedIndexChanged += self._pyote_event_selection_changed
        grp_files.Controls.Add(self.pyote_event_listbox)

        self.pyote_preview_label = Label()
        self.pyote_preview_label.Text = "D/R: -"
        self.pyote_preview_label.Location = Point(15, 304)
        self.pyote_preview_label.Size = Size(905, 22)
        self.pyote_preview_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.pyote_preview_label)

        # ===== TIMESTAMP CHECK SUBPANEL =====
        grp_ts_check = GroupBox()
        grp_ts_check.Text = "Timestamp Check"
        grp_ts_check.Location = Point(15, 331)
        grp_ts_check.Size = Size(910, 80)
        grp_files.Controls.Add(grp_ts_check)

        self.lbl_ts_delayed = Label()
        self.lbl_ts_delayed.Text = "Delayed frames: -"
        self.lbl_ts_delayed.Location = Point(15, 22)
        self.lbl_ts_delayed.Size = Size(165, 20)
        self.lbl_ts_delayed.ForeColor = Color.Gray
        grp_ts_check.Controls.Add(self.lbl_ts_delayed)

        self.lbl_ts_late = Label()
        self.lbl_ts_late.Text = "Late frames: -"
        self.lbl_ts_late.Location = Point(190, 22)
        self.lbl_ts_late.Size = Size(140, 20)
        self.lbl_ts_late.ForeColor = Color.Gray
        grp_ts_check.Controls.Add(self.lbl_ts_late)

        self.lbl_ts_status = Label()
        self.lbl_ts_status.Text = "Status: -"
        self.lbl_ts_status.Location = Point(340, 22)
        self.lbl_ts_status.Size = Size(200, 20)
        self.lbl_ts_status.ForeColor = Color.Gray
        grp_ts_check.Controls.Add(self.lbl_ts_status)

        self.lbl_ts_minmax = Label()
        self.lbl_ts_minmax.Text = "Deviation: -"
        self.lbl_ts_minmax.Location = Point(550, 22)
        self.lbl_ts_minmax.Size = Size(345, 20)
        self.lbl_ts_minmax.ForeColor = Color.Gray
        grp_ts_check.Controls.Add(self.lbl_ts_minmax)

        btn_ts_explain = Button()
        btn_ts_explain.Text = "Explain..."
        btn_ts_explain.Location = Point(15, 48)
        btn_ts_explain.Size = Size(80, 25)
        btn_ts_explain.Click += self._ts_explain_click
        grp_ts_check.Controls.Add(btn_ts_explain)

        self.btn_ts_inspect = Button()
        self.btn_ts_inspect.Text = "Inspect Timestamps..."
        self.btn_ts_inspect.Location = Point(105, 48)
        self.btn_ts_inspect.Size = Size(160, 25)
        self.btn_ts_inspect.Enabled = False
        self.btn_ts_inspect.Click += self._ts_inspect_click
        grp_ts_check.Controls.Add(self.btn_ts_inspect)

        self.lbl_ts_event_warning = Label()
        self.lbl_ts_event_warning.Text = ""
        self.lbl_ts_event_warning.Location = Point(275, 52)
        self.lbl_ts_event_warning.Size = Size(620, 20)
        self.lbl_ts_event_warning.ForeColor = Color.OrangeRed
        self.lbl_ts_event_warning.Visible = False
        grp_ts_check.Controls.Add(self.lbl_ts_event_warning)

        y_pos += 425
        
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
        self.status_label.Location = Point(20, 976)
        self.status_label.Size = Size(700, 20)
        self.status_label.ForeColor = Color.Gray
        self.Controls.Add(self.status_label)
        
        self.btn_generate = Button()
        self.btn_generate.Text = "Generate Report"
        self.btn_generate.Location = Point(750, 971)
        self.btn_generate.Size = Size(140, 35)
        self.btn_generate.Enabled = False
        self.btn_generate.Click += self.generate_click
        self.Controls.Add(self.btn_generate)
        self.AcceptButton = self.btn_generate
        
        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(900, 971)
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
        elif last_report_type == 'sodis':
            self.rb_sodis.Checked = True
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
        elif self.rb_sodis.Checked:
            current_report_type = 'SODIS'
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
        dialog.Description = "Select folder containing AOTA and light curve CSV files"
        
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
        """Scan folder for AOTA, CSV, AOTA Report, and PyOTE metrics files"""
        self.aota_files = []
        self.csv_files = []
        self.aota_report_files = []
        self.pyote_files = []
        self.pyote_events = []
        self.aota_listbox.Items.Clear()
        self.csv_listbox.Items.Clear()
        self.report_listbox.Items.Clear()
        self.pyote_listbox.Items.Clear()
        self.pyote_event_listbox.Items.Clear()
        self.aota_preview_label.Text = "D/R: -"
        self.csv_preview_label.Text = "Observing times: -"
        self.report_preview_label.Text = "D/R: -"
        self.pyote_preview_label.Text = "D/R: -"
        self.pyote_count_label.Text = "No folder"
        self.pyote_event_count_label.Text = "-"
        self._d_time_seconds = None
        self._r_time_seconds = None
        self._reset_timestamp_check()
        
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
                elif filename.lower().endswith('.txt') and not filename.lower().endswith('_aota_report.txt'):
                    try:
                        import pyote_metrics_reader as pmr
                        if pmr.detect_pyote_metrics(full_path):
                            self.pyote_files.append(full_path)
                            self.pyote_listbox.Items.Add(filename)
                    except Exception:
                        pass
                elif filename.lower().endswith('.csv'):
                    self.csv_files.append(full_path)
                    try:
                        import light_curve_reader as lcr
                        fmt = lcr.detect_format(full_path)
                    except Exception:
                        fmt = '?'
                    self.csv_listbox.Items.Add(filename + '  [' + fmt + ']')
            
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

            pyote_count = len(self.pyote_files)
            if pyote_count == 0:
                self.pyote_count_label.Text = "No PyOTE metrics found"
            elif pyote_count == 1:
                self.pyote_count_label.Text = "1 file found"
            else:
                self.pyote_count_label.Text = f"{pyote_count} files found"
            
            # Auto-select first files
            if aota_count > 0:
                self.aota_listbox.SelectedIndex = 0
            if csv_count > 0:
                self.csv_listbox.SelectedIndex = 0
            if report_count > 0:
                self.report_listbox.SelectedIndex = 0
            if pyote_count > 0:
                self.pyote_listbox.SelectedIndex = 0

            self.update_extracted_time_previews()
            
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
            self.pyote_count_label.Text = "Error"
    
    def selection_changed(self, sender, e):
        """Handle file selection changed"""
        self.update_extracted_time_previews()
        self.update_button_state()

    def update_extracted_time_previews(self):
        """Update preview labels with extracted times from selected files"""
        self._update_tangra_preview()
        self._update_aota_xml_preview()
        self._update_aota_report_preview()
        self._update_pyote_preview()

    def _format_time_value(self, value):
        """Format time value for preview with sensible precision"""
        if value is None:
            return "-"

        if isinstance(value, str):
            text = value.strip()
            return text if text else "-"

        try:
            # Keep integers compact; round fractional values to sensible precision
            if float(value).is_integer():
                return str(int(value))
            return ("{0:.3f}".format(float(value))).rstrip('0').rstrip('.')
        except Exception:
            return str(value)

    def _format_hms(self, hours, minutes, seconds):
        """Format H:M:S triplet for preview"""
        return "{0}:{1}:{2}".format(
            self._format_time_value(hours),
            self._format_time_value(minutes),
            self._format_time_value(seconds)
        )

    def _update_tangra_preview(self):
        """Update Tangra CSV observing time preview"""
        try:
            if self.csv_listbox.SelectedIndex < 0:
                self.csv_preview_label.Text = "Observing times: -"
                self._reset_timestamp_check()
                return

            tangra_path = self.csv_files[self.csv_listbox.SelectedIndex]
            import light_curve_reader as lcr
            summary = lcr.get_observation_summary(tangra_path, percentiles=[1, 99])
            self._ts_summary = summary

            start_time = summary.get('start_time', '') if summary else ''
            end_time = summary.get('end_time', '') if summary else ''

            if start_time or end_time:
                self.csv_preview_label.Text = "Start: {0}\nEnd: {1}".format(
                    self._format_time_value(start_time),
                    self._format_time_value(end_time)
                )
            else:
                self.csv_preview_label.Text = "Observing times: not found"

            # Update timestamp check labels
            n_delayed = int(summary.get('n_delayed_frames', 0) or 0)
            n_late = int(summary.get('n_late_frames', 0) or 0)
            self.lbl_ts_delayed.Text = "Delayed frames: {0}".format(n_delayed)
            self.lbl_ts_late.Text = "Late frames: {0}".format(n_late)
            if n_late > 0:
                self.lbl_ts_delayed.ForeColor = Color.OrangeRed
                self.lbl_ts_late.ForeColor = Color.OrangeRed
                self.lbl_ts_status.Text = "Status: Issues detected"
                self.lbl_ts_status.ForeColor = Color.OrangeRed
            elif n_delayed > 0:
                self.lbl_ts_delayed.ForeColor = Color.Orange
                self.lbl_ts_late.ForeColor = Color.Gray
                self.lbl_ts_status.Text = "Status: Check"
                self.lbl_ts_status.ForeColor = Color.Orange
            else:
                self.lbl_ts_delayed.ForeColor = Color.Gray
                self.lbl_ts_late.ForeColor = Color.Gray
                self.lbl_ts_status.Text = "Status: OK"
                self.lbl_ts_status.ForeColor = Color.Green
            self.btn_ts_inspect.Enabled = True
            # Min/max deviation from median
            tdelta_min = summary.get('tdelta_min', None)
            tdelta_max = summary.get('tdelta_max', None)
            tdelta_median = summary.get('tdelta_median', None)
            if tdelta_min is not None and tdelta_max is not None and tdelta_median:
                min_dev = tdelta_min - tdelta_median
                max_dev = tdelta_max - tdelta_median
                self.lbl_ts_minmax.Text = "Deviation: {0:+.1f} to {1:+.1f} ms".format(min_dev, max_dev)
            else:
                self.lbl_ts_minmax.Text = "Deviation: -"
            self.lbl_ts_minmax.ForeColor = Color.Gray
            self._check_event_in_window(summary)
        except Exception:
            self.csv_preview_label.Text = "Observing times: unable to extract"
            self._reset_timestamp_check()

    def _update_aota_xml_preview(self):
        """Update AOTA XML D/R preview"""
        # Always clear stale D/R values at the start; only set on successful parse
        self._d_time_seconds = None
        self._r_time_seconds = None
        try:
            if self.aota_listbox.SelectedIndex < 0:
                self.aota_preview_label.Text = "D/R: -"
                return

            aota_path = self.aota_files[self.aota_listbox.SelectedIndex]
            from aota_parser import parse_aota_file
            aota_result = parse_aota_file(aota_path)

            if not aota_result:
                self.aota_preview_label.Text = "D/R: unable to extract"
                return

            valid_events = aota_result.get_valid_events()
            if not valid_events:
                self.aota_preview_label.Text = "D/R: not found"
                return

            evt = valid_events[0]
            d_seconds = evt.d_seconds_str if evt.d_seconds_str is not None else evt.d_seconds
            r_seconds = evt.r_seconds_str if evt.r_seconds_str is not None else evt.r_seconds
            d_time = self._format_hms(evt.d_hours, evt.d_minutes, d_seconds)
            r_time = self._format_hms(evt.r_hours, evt.r_minutes, r_seconds)
            self.aota_preview_label.Text = "D: {0}\nR: {1}".format(d_time, r_time)

            # Store D/R times as seconds-from-midnight for the inspector form
            try:
                d_h = int(evt.d_hours or 0)
                d_m = int(evt.d_minutes or 0)
                d_s = float(d_seconds) if d_seconds is not None else 0.0
                self._d_time_seconds = d_h * 3600.0 + d_m * 60.0 + d_s
                r_h = int(evt.r_hours or 0)
                r_m = int(evt.r_minutes or 0)
                r_s = float(r_seconds) if r_seconds is not None else 0.0
                self._r_time_seconds = r_h * 3600.0 + r_m * 60.0 + r_s
            except Exception:
                self._d_time_seconds = None
                self._r_time_seconds = None
        except Exception:
            self.aota_preview_label.Text = "D/R: unable to extract"

    def _update_aota_report_preview(self):
        """Update AOTA Report D/R preview"""
        try:
            if self.report_listbox.SelectedIndex < 0:
                self.report_preview_label.Text = "D/R: -"
                return

            report_path = self.aota_report_files[self.report_listbox.SelectedIndex]
            import aota_report_parser as arp
            parsed_report = arp.parse_aota_report(report_path)

            if not parsed_report or not parsed_report.get('events'):
                self.report_preview_label.Text = "D/R: not found"
                return

            summary = arp.get_event_summary(parsed_report, 0)
            if not summary:
                self.report_preview_label.Text = "D/R: not found"
                return

            d_time = self._format_hms(summary.get('d_hours'), summary.get('d_minutes'), summary.get('d_seconds'))
            r_time = self._format_hms(summary.get('r_hours'), summary.get('r_minutes'), summary.get('r_seconds'))
            self.report_preview_label.Text = "D: {0}\nR: {1}".format(d_time, r_time)
        except Exception:
            self.report_preview_label.Text = "D/R: unable to extract"

    def _pyote_file_selection_changed(self, sender, e):
        """Handle PyOTE file listbox selection change - load events from selected file"""
        self.pyote_events = []
        self.pyote_event_listbox.Items.Clear()
        self.pyote_preview_label.Text = "D/R: -"
        self.pyote_event_count_label.Text = "-"

        if self.pyote_listbox.SelectedIndex < 0:
            self.update_button_state()
            return

        pyote_path = self.pyote_files[self.pyote_listbox.SelectedIndex]
        try:
            import pyote_metrics_reader as pmr
            self.pyote_events = pmr.read_pyote_fit_metrics(pyote_path)
            if not self.pyote_events:
                self.pyote_event_count_label.Text = "No events found"
                self.update_button_state()
                return

            for record in self.pyote_events:
                self.pyote_event_listbox.Items.Add(pmr.format_record_display(record))

            count = len(self.pyote_events)
            if count == 1:
                self.pyote_event_count_label.Text = "1 event"
            else:
                self.pyote_event_count_label.Text = f"{count} events"

            self.pyote_event_listbox.SelectedIndex = 0
        except Exception:
            self.pyote_event_count_label.Text = "Error reading file"
            self.pyote_preview_label.Text = "D/R: unable to read"

        self.update_button_state()

    def _pyote_event_selection_changed(self, sender, e):
        """Handle PyOTE event listbox selection change - update D/R preview"""
        self._update_pyote_preview()
        self.update_button_state()

    def _update_pyote_preview(self):
        """Update PyOTE metrics D/R preview for the selected event"""
        if self.pyote_event_listbox.SelectedIndex < 0 or not self.pyote_events:
            self.pyote_preview_label.Text = "D/R: -"
            return

        idx = self.pyote_event_listbox.SelectedIndex
        if idx >= len(self.pyote_events):
            self.pyote_preview_label.Text = "D/R: -"
            return

        record = self.pyote_events[idx]
        d_time = record.get('D time', '?')
        r_time = record.get('R time', '?')
        uncertainty = record.get('time err +/-secs', None)
        snr = record.get('DNR', None)

        preview = "D: {0}  R: {1}".format(d_time, r_time)
        if uncertainty is not None:
            preview += "  \u00b1{0}s".format(uncertainty)
        if snr is not None:
            preview += "  SNR(DNR):{0}".format(snr)
        self.pyote_preview_label.Text = preview
    
    def _reset_timestamp_check(self):
        """Reset timestamp check labels and state"""
        self._ts_summary = None
        self.lbl_ts_delayed.Text = "Delayed frames: -"
        self.lbl_ts_delayed.ForeColor = Color.Gray
        self.lbl_ts_late.Text = "Late frames: -"
        self.lbl_ts_late.ForeColor = Color.Gray
        self.lbl_ts_status.Text = "Status: -"
        self.lbl_ts_status.ForeColor = Color.Gray
        self.btn_ts_inspect.Enabled = False
        self.lbl_ts_minmax.Text = "Deviation: -"
        self.lbl_ts_minmax.ForeColor = Color.Gray
        self.lbl_ts_event_warning.Visible = False

    def _check_event_in_window(self, summary):
        """Check if the predicted event time falls within the CSV recording window"""
        try:
            event_time_str = self.event.event_time if (self.event and hasattr(self.event, 'event_time')) else ''
            if not event_time_str or not summary:
                self.lbl_ts_event_warning.Visible = False
                return

            # Parse HH:MM:SS from ISO datetime "YYYY-MM-DDTHH:MM:SS..."
            t_part = event_time_str.split('T')[-1].rstrip('Z').split('.')[0]
            parts = t_part.split(':')
            event_secs = int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])

            start_str = summary.get('start_time', '')
            end_str = summary.get('end_time', '')
            if not start_str or not end_str:
                self.lbl_ts_event_warning.Visible = False
                return

            def hms_to_secs(s):
                p = s.split(':')
                return int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])

            if hms_to_secs(start_str) <= event_secs <= hms_to_secs(end_str):
                self.lbl_ts_event_warning.Visible = False
            else:
                self.lbl_ts_event_warning.Text = "Warning: predicted event time not within recording window"
                self.lbl_ts_event_warning.Visible = True
        except Exception:
            self.lbl_ts_event_warning.Visible = False

    def _ts_explain_click(self, sender, e):
        """Show explanation of timestamp check metrics"""
        MessageBox.Show(
            "Timestamp Check analyses recording frame timing for irregularities.\n\n"
            "Delayed frames: frames where the interval is more than 10% longer than "
            "the median (minor timing slip).\n\n"
            "Late frames: frames where the interval is more than 90% longer than the "
            "median. This typically means one or more frames were dropped.\n\n"
            "If these anomalies fall completely outside the D/R event window they have "
            "no impact on the reported event times and can be ignored.\n\n"
            "If many frames are affected the recording frame rate may have been too high "
            "for the camera and computer. It is recommended to record at no more than "
            "1/3 of the camera's maximum frame rate.",
            "Timestamp Check Explained",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )

    def _ts_inspect_click(self, sender, e):
        """Open the Timestamp Inspector form"""
        if self.csv_listbox.SelectedIndex < 0:
            return
        tangra_path = self.csv_files[self.csv_listbox.SelectedIndex]
        try:
            # Derive predicted event time as seconds-from-midnight
            event_secs = None
            try:
                event_time_str = self.event.event_time if (self.event and hasattr(self.event, 'event_time')) else ''
                if event_time_str:
                    t_part = event_time_str.split('T')[-1].rstrip('Z').split('.')[0]
                    p = t_part.split(':')
                    event_secs = int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])
            except Exception:
                event_secs = None
            form = TimestampInspectorForm(tangra_path, self._d_time_seconds, self._r_time_seconds, event_secs)
            form.ShowDialog(self)
        except Exception as ex:
            MessageBox.Show(
                "Error opening Timestamp Inspector:\n\n" + str(ex),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )

    def update_button_state(self):
        """Update generate button state and status message"""
        # Check all requirements
        has_report_type = self.rb_na.Checked or self.rb_tt.Checked or self.rb_sodis.Checked
        
        # Check if equipment is configured (not just selected)
        telescopes = self.config.get_telescopes()
        cameras = self.config.get_cameras()
        has_telescope = len(telescopes) > 0 and self.combo_telescope.SelectedIndex >= 0
        has_camera = len(cameras) > 0 and self.combo_camera.SelectedIndex >= 0
        
        aota_selected = self.aota_listbox.SelectedIndex >= 0
        csv_selected = self.csv_listbox.SelectedIndex >= 0
        report_selected = self.report_listbox.SelectedIndex >= 0
        pyote_selected = (self.pyote_listbox.SelectedIndex >= 0
                          and self.pyote_event_listbox.SelectedIndex >= 0
                          and bool(self.pyote_events))
        
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
            missing.append("light curve CSV file")
        
        # AOTA requirement depends on observation type - either AOTA.xml, AOTA Report, or PyOTE Metrics is needed
        if obs_type in ["Positive", "Unsure"] and not aota_selected and not report_selected and not pyote_selected:
            missing.append("AOTA file, AOTA Report, or PyOTE Metrics")
        
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
        elif self.rb_sodis.Checked:
            self.report_type = 'sodis'
        
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
        elif self.report_type == 'sodis':
            cameras = [c for c in all_cameras if c.get('report_type', 'NA') == 'SODIS']
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
                "Please select a light curve CSV file.",
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

        # PyOTE metrics
        self.selected_pyote_path = None
        self.selected_pyote_event_index = -1
        if self.pyote_listbox.SelectedIndex >= 0:
            self.selected_pyote_path = self.pyote_files[self.pyote_listbox.SelectedIndex]
            self.selected_pyote_event_index = self.pyote_event_listbox.SelectedIndex

        # For Positive/Unsure, need at least one of AOTA.xml, AOTA Report, or PyOTE Metrics
        if self.observation_type in ["Positive", "Unsure"]:
            if not self.selected_aota_path and not self.selected_aota_report_path and not self.selected_pyote_path:
                MessageBox.Show(
                    f"Either AOTA file, AOTA Report, or PyOTE Metrics is required for {self.observation_type} observations.",
                    "Missing Event Data",
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

    def get_selected_folder(self):
        return self.current_folder

    def get_selected_pyote_path(self):
        return self.selected_pyote_path

    def get_selected_pyote_event_index(self):
        return self.selected_pyote_event_index


class TimestampInspectorForm(Form):
    """Form for inspecting frame timing from a Tangra CSV file with OxyPlot charts"""

    def __init__(self, tangra_path, d_time_seconds=None, r_time_seconds=None, event_time_seconds=None):
        Form.__init__(self)
        self.tangra_path = tangra_path
        self.d_time_seconds = d_time_seconds
        self.r_time_seconds = r_time_seconds
        self.event_time_seconds = event_time_seconds
        self._setup_ui()
        self._build_charts()

    def _setup_ui(self):
        self.Text = "Timestamp Inspector"
        self.Size = Size(900, 720)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedSingle
        self.MaximizeBox = False
        self.MinimizeBox = False

        clr.AddReference("OxyPlot")
        clr.AddReference("OxyPlot.WindowsForms")
        import OxyPlot.WindowsForms as OxyWF

        self._plot_interval = OxyWF.PlotView()
        self._plot_interval.Location = Point(10, 10)
        self._plot_interval.Size = Size(865, 250)
        self._plot_interval.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        self.Controls.Add(self._plot_interval)

        self._lbl_stats = Label()
        self._lbl_stats.Location = Point(10, 264)
        self._lbl_stats.Size = Size(865, 18)
        self._lbl_stats.Text = ""
        self.Controls.Add(self._lbl_stats)

        self._plot_signal = OxyWF.PlotView()
        self._plot_signal.Location = Point(10, 286)
        self._plot_signal.Size = Size(865, 252)
        self._plot_signal.Anchor = (AnchorStyles.Top | AnchorStyles.Left |
                                    AnchorStyles.Right | AnchorStyles.Bottom)
        self.Controls.Add(self._plot_signal)

        self._lbl_info = Label()
        self._lbl_info.Location = Point(10, 545)
        self._lbl_info.Size = Size(770, 52)
        self._lbl_info.Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
        self._lbl_info.Text = (
            "Delayed frames: deviation > +10% of median.  Late frames: deviation > +90% of median (dropped frame likely).\n"
            "Anomalies outside the D/R window have no impact on reported event times.\n"
            "Many anomalies may indicate frame rate too high. Recommended: record at \u22641/3 of camera max frame rate."
        )
        self.Controls.Add(self._lbl_info)

        btn_close = Button()
        btn_close.Text = "Close"
        btn_close.Location = Point(793, 603)
        btn_close.Size = Size(85, 28)
        btn_close.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        btn_close.Click += self._close_click
        self.Controls.Add(btn_close)

    def _close_click(self, sender, e):
        self.Close()

    def _build_charts(self):
        try:
            import OxyPlot
            import OxyPlot.Series as OxySeries
            import OxyPlot.Axes as OxyAxes
            import OxyPlot.Annotations as OxyAnn
            import light_curve_reader as lcr

            all_frames, all_times, all_values = lcr.read_light_curve(self.tangra_path)

            if not all_frames or len(all_frames) < 2:
                self._lbl_info.Text = "Not enough data to display charts."
                return

            valid = [(f, t, v) for f, t, v in zip(all_frames, all_times, all_values) if t is not None]
            if len(valid) < 2:
                self._lbl_info.Text = "Not enough valid timestamps to display charts."
                return
            frame_nos = [r[0] for r in valid]
            times = [r[1] for r in valid]
            signals = [r[2] if r[2] is not None else 0 for r in valid]
            # Cache for use in _add_dr_annotations
            self._cached_times = times
            self._cached_frame_nos = frame_nos

            # Compute timediffs in ms and deviations from median
            timediffs = []
            diff_frames = []
            for i in range(1, len(times)):
                delta_ms = (times[i] - times[i - 1]).total_seconds() * 1000.0
                timediffs.append(delta_ms)
                diff_frames.append(frame_nos[i])

            if not timediffs:
                self._lbl_info.Text = "Could not compute frame intervals."
                return

            # Median
            sorted_td = sorted(timediffs)
            n = len(sorted_td)
            median_ms = (sorted_td[n // 2 - 1] + sorted_td[n // 2]) / 2.0 if n % 2 == 0 else sorted_td[n // 2]

            # Deviations from median
            deviations = [td - median_ms for td in timediffs]
            min_dev = min(deviations)
            max_dev = max(deviations)

            # Populate stats label
            self._lbl_stats.Text = (
                "Median exposure: {0:.2f} ms   |   "
                "Min deviation: {1:+.2f} ms   |   "
                "Max deviation: {2:+.2f} ms"
            ).format(median_ms, min_dev, max_dev)

            # Find D/R frame numbers by closest timestamp
            d_frame = self._nearest_frame(times, frame_nos, self.d_time_seconds)
            r_frame = self._nearest_frame(times, frame_nos, self.r_time_seconds)

            # --- Chart 1: interval deviation from median ---
            model1 = OxyPlot.PlotModel()
            model1.Title = "Frame Interval Deviation from Median"
            model1.TitleFontSize = 12.0

            xa1 = OxyAxes.LinearAxis()
            xa1.Position = OxyAxes.AxisPosition.Bottom
            xa1.Title = "Frame number"
            model1.Axes.Add(xa1)

            # Y axis: autoscale to data but enforce minimum ±5 ms range
            y_pad = max(abs(min_dev), abs(max_dev)) * 0.1 + 0.5
            y_min_axis = min(min_dev - y_pad, -5.0)
            y_max_axis = max(max_dev + y_pad, 5.0)

            ya1 = OxyAxes.LinearAxis()
            ya1.Position = OxyAxes.AxisPosition.Left
            ya1.Title = "Deviation from median (ms)"
            ya1.Minimum = y_min_axis
            ya1.Maximum = y_max_axis
            model1.Axes.Add(ya1)

            s1 = OxySeries.LineSeries()
            s1.Title = "Deviation"
            s1.Color = OxyPlot.OxyColors.SteelBlue
            for fn, dv in zip(diff_frames, deviations):
                s1.Points.Add(OxyPlot.DataPoint(float(fn), dv))
            model1.Series.Add(s1)

            zero_ann = OxyAnn.LineAnnotation()
            zero_ann.Type = OxyAnn.LineAnnotationType.Horizontal
            zero_ann.Y = 0.0
            zero_ann.Color = OxyPlot.OxyColors.Gray
            zero_ann.LineStyle = OxyPlot.LineStyle.Dash
            zero_ann.Text = "0 (median)"
            model1.Annotations.Add(zero_ann)

            self._add_dr_annotations(model1, d_frame, r_frame, OxyAnn, OxyPlot)
            self._plot_interval.Model = model1

            # --- Chart 2: signal level ---
            model2 = OxyPlot.PlotModel()
            model2.Title = "Signal Level"
            model2.TitleFontSize = 12.0

            xa2 = OxyAxes.LinearAxis()
            xa2.Position = OxyAxes.AxisPosition.Bottom
            xa2.Title = "Frame number"
            model2.Axes.Add(xa2)

            ya2 = OxyAxes.LinearAxis()
            ya2.Position = OxyAxes.AxisPosition.Left
            ya2.Title = "Signal"
            model2.Axes.Add(ya2)

            s2 = OxySeries.LineSeries()
            s2.Title = "Signal"
            s2.Color = OxyPlot.OxyColors.DarkGreen
            for fn, sig in zip(frame_nos, signals):
                s2.Points.Add(OxyPlot.DataPoint(float(fn), float(sig)))
            model2.Series.Add(s2)

            self._add_dr_annotations(model2, d_frame, r_frame, OxyAnn, OxyPlot)
            self._plot_signal.Model = model2

        except Exception as ex:
            self._lbl_info.Text = "Error building charts: " + str(ex)

    def _nearest_frame(self, times, frame_nos, target_seconds):
        """Return the frame number whose timestamp is closest to target_seconds from midnight"""
        if target_seconds is None:
            return None
        best_diff = None
        best_frame = None
        for t, fn in zip(times, frame_nos):
            if t is None:
                continue
            t_sec = t.hour * 3600.0 + t.minute * 60.0 + t.second + t.microsecond / 1e6
            diff = abs(t_sec - target_seconds)
            if best_diff is None or diff < best_diff:
                best_diff = diff
                best_frame = fn
        return best_frame

    def _add_dr_annotations(self, model, d_frame, r_frame, OxyAnn, OxyPlot):
        """Add vertical D/R and predicted-event annotations to a plot model"""
        event_frame = self._nearest_frame(
            self._cached_times, self._cached_frame_nos, self.event_time_seconds
        ) if hasattr(self, '_cached_times') else None
        if event_frame is not None:
            ann = OxyAnn.LineAnnotation()
            ann.Type = OxyAnn.LineAnnotationType.Vertical
            ann.X = float(event_frame)
            ann.Color = OxyPlot.OxyColors.DodgerBlue
            ann.LineStyle = OxyPlot.LineStyle.Solid
            ann.StrokeThickness = 1.5
            ann.Text = "Event"
            model.Annotations.Add(ann)
        if d_frame is not None:
            ann = OxyAnn.LineAnnotation()
            ann.Type = OxyAnn.LineAnnotationType.Vertical
            ann.X = float(d_frame)
            ann.Color = OxyPlot.OxyColors.Red
            ann.LineStyle = OxyPlot.LineStyle.Dash
            ann.Text = "D"
            model.Annotations.Add(ann)
        if r_frame is not None:
            ann = OxyAnn.LineAnnotation()
            ann.Type = OxyAnn.LineAnnotationType.Vertical
            ann.X = float(r_frame)
            ann.Color = OxyPlot.OxyColors.Green
            ann.LineStyle = OxyPlot.LineStyle.Dash
            ann.Text = "R"
            model.Annotations.Add(ann)

