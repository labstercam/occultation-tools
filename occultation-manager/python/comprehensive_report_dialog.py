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
    CheckBox, Clipboard, AnchorStyles, DockStyle, Padding, DialogResult,
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

        # Timing section state
        self._calib_runs = []
        self._ntp_offset_ms = 0.0
        self._ntp_uncertainty_ms = 0.0
        self._last_cam_id = None          # guards _init_timing_section from spurious fires
        self._correction_user_set = False # True once user explicitly clicks a correction radio
        self._suppress_correction_event = False  # True during programmatic radio changes

        self.setup_ui()
        
        # Load saved preferences
        self.load_preferences()
        
        # Update button state after loading preferences
        self.update_button_state()
        
        # Apply theme
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)

        # Re-apply guidance panel highlight after theming (theme overwrites Panel BackColor)
        if hasattr(self, '_pnl_apply_guidance'):
            self._pnl_apply_guidance.BackColor = Color.LightYellow
    
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
        
        # ===== SECTION 1: EQUIPMENT =====
        grp_equipment = GroupBox()
        grp_equipment.Text = "1. Equipment"
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

        # ===== SECTION 2: REPORT FORMAT AND OBSERVATION FOLDER =====
        grp_report = GroupBox()
        grp_report.Text = "2. Report Format and Observation Folder"
        grp_report.Location = Point(10, y_pos)
        grp_report.Size = Size(940, 135)
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

        # Folder selection (right half of the §2 group)
        lbl_folder_info = Label()
        lbl_folder_info.Text = "Observation files folder:"
        lbl_folder_info.Location = Point(320, 22)
        lbl_folder_info.Size = Size(600, 20)
        grp_report.Controls.Add(lbl_folder_info)

        self.folder_textbox = TextBox()
        self.folder_textbox.Location = Point(320, 44)
        self.folder_textbox.Size = Size(500, 25)
        self.folder_textbox.ReadOnly = True
        grp_report.Controls.Add(self.folder_textbox)

        btn_browse = Button()
        btn_browse.Text = "Browse..."
        btn_browse.Location = Point(826, 42)
        btn_browse.Size = Size(100, 25)
        btn_browse.Click += self.browse_folder_click
        grp_report.Controls.Add(btn_browse)

        # File availability status indicator (updated by scan_folder)
        self._lbl_file_status = Label()
        self._lbl_file_status.Text = "No folder selected"
        self._lbl_file_status.Location = Point(320, 73)
        self._lbl_file_status.Size = Size(606, 52)
        self._lbl_file_status.ForeColor = Color.Gray
        grp_report.Controls.Add(self._lbl_file_status)

        y_pos += 145
        
        # ===== SECTION 3: TIMING =====
        grp_timing = GroupBox()
        grp_timing.Text = "3. Timing"
        grp_timing.Location = Point(10, y_pos)
        grp_timing.Size = Size(940, 475)
        main_panel.Controls.Add(grp_timing)

        lbl_timing_method = Label()
        lbl_timing_method.Text = "Timing method:"
        lbl_timing_method.Location = Point(15, 22)
        lbl_timing_method.Size = Size(115, 22)
        grp_timing.Controls.Add(lbl_timing_method)

        # Row 1: NTP and GPS flash
        self._rad_timing_ntp = RadioButton()
        self._rad_timing_ntp.Text = "NTP / GPS-disciplined clock"
        self._rad_timing_ntp.Location = Point(135, 22)
        self._rad_timing_ntp.Size = Size(215, 22)
        self._rad_timing_ntp.CheckedChanged += self._on_timing_method_changed
        grp_timing.Controls.Add(self._rad_timing_ntp)

        self._rad_timing_gps = RadioButton()
        self._rad_timing_gps.Text = "GPS flash overlay (dumb)"
        self._rad_timing_gps.Location = Point(360, 22)
        self._rad_timing_gps.Size = Size(195, 22)
        self._rad_timing_gps.CheckedChanged += self._on_timing_method_changed
        grp_timing.Controls.Add(self._rad_timing_gps)

        # Row 2: GPS-integrated CMOS, Analog video + VTI, Other
        self._rad_timing_gps_cmos = RadioButton()
        self._rad_timing_gps_cmos.Text = "GPS-integrated CMOS camera"
        self._rad_timing_gps_cmos.Location = Point(135, 47)
        self._rad_timing_gps_cmos.Size = Size(230, 22)
        self._rad_timing_gps_cmos.CheckedChanged += self._on_timing_method_changed
        grp_timing.Controls.Add(self._rad_timing_gps_cmos)

        self._rad_timing_analog_vti = RadioButton()
        self._rad_timing_analog_vti.Text = "Analog video + VTI"
        self._rad_timing_analog_vti.Location = Point(375, 47)
        self._rad_timing_analog_vti.Size = Size(185, 22)
        self._rad_timing_analog_vti.CheckedChanged += self._on_timing_method_changed
        grp_timing.Controls.Add(self._rad_timing_analog_vti)

        self._rad_timing_other = RadioButton()
        self._rad_timing_other.Text = "Other"
        self._rad_timing_other.Location = Point(570, 47)
        self._rad_timing_other.Size = Size(80, 22)
        self._rad_timing_other.Checked = True
        self._rad_timing_other.CheckedChanged += self._on_timing_method_changed
        grp_timing.Controls.Add(self._rad_timing_other)

        # --- NTP panel (visible when NTP method selected) ---
        self._pnl_timing_ntp = Panel()
        self._pnl_timing_ntp.Location = Point(8, 76)
        self._pnl_timing_ntp.Size = Size(922, 390)
        self._pnl_timing_ntp.Visible = False
        grp_timing.Controls.Add(self._pnl_timing_ntp)

        lbl_cam_section = Label()
        lbl_cam_section.Text = "Camera acquisition delay"
        lbl_cam_section.Font = Font(lbl_cam_section.Font.FontFamily, lbl_cam_section.Font.Size, FontStyle.Bold)
        lbl_cam_section.Location = Point(5, 5)
        lbl_cam_section.Size = Size(270, 18)
        self._pnl_timing_ntp.Controls.Add(lbl_cam_section)

        lbl_calib_run = Label()
        lbl_calib_run.Text = "Calibration run:"
        lbl_calib_run.Location = Point(5, 28)
        lbl_calib_run.Size = Size(110, 22)
        self._pnl_timing_ntp.Controls.Add(lbl_calib_run)

        self._combo_calib_run = ComboBox()
        self._combo_calib_run.Location = Point(118, 26)
        self._combo_calib_run.Size = Size(390, 22)
        self._combo_calib_run.DropDownStyle = ComboBoxStyle.DropDownList
        self._combo_calib_run.SelectedIndexChanged += self._on_calib_run_changed
        self._pnl_timing_ntp.Controls.Add(self._combo_calib_run)

        self._lbl_calib_match = Label()
        self._lbl_calib_match.Text = ""
        self._lbl_calib_match.Location = Point(514, 28)
        self._lbl_calib_match.Size = Size(398, 22)
        self._lbl_calib_match.ForeColor = Color.Gray
        self._pnl_timing_ntp.Controls.Add(self._lbl_calib_match)

        lbl_y_line = Label()
        lbl_y_line.Text = "Y line:"
        lbl_y_line.Location = Point(5, 54)
        lbl_y_line.Size = Size(55, 22)
        self._pnl_timing_ntp.Controls.Add(lbl_y_line)

        self._txt_y_line = TextBox()
        self._txt_y_line.Location = Point(63, 52)
        self._txt_y_line.Size = Size(70, 22)
        self._txt_y_line.Text = "0"
        self._txt_y_line.TextChanged += self._on_y_line_changed
        self._pnl_timing_ntp.Controls.Add(self._txt_y_line)

        lbl_calc_label = Label()
        lbl_calc_label.Text = "Calculated delay:"
        lbl_calc_label.Location = Point(140, 54)
        lbl_calc_label.Size = Size(128, 22)
        self._pnl_timing_ntp.Controls.Add(lbl_calc_label)

        self._lbl_calc_delay = Label()
        self._lbl_calc_delay.Text = "\u2014"
        self._lbl_calc_delay.Location = Point(272, 54)
        self._lbl_calc_delay.Size = Size(200, 22)
        self._pnl_timing_ntp.Controls.Add(self._lbl_calc_delay)

        lbl_csv_label = Label()
        lbl_csv_label.Text = "Tangra CSV:"
        lbl_csv_label.Location = Point(5, 78)
        lbl_csv_label.Size = Size(100, 20)
        lbl_csv_label.ForeColor = Color.Gray
        self._pnl_timing_ntp.Controls.Add(lbl_csv_label)

        self._lbl_csv_delay = Label()
        self._lbl_csv_delay.Text = "\u2014"
        self._lbl_csv_delay.Location = Point(108, 78)
        self._lbl_csv_delay.Size = Size(480, 20)
        self._lbl_csv_delay.ForeColor = Color.Gray
        self._pnl_timing_ntp.Controls.Add(self._lbl_csv_delay)

        self._lbl_ntp_section = Label()
        self._lbl_ntp_section.Text = "NTP correction:  \u2014"
        self._lbl_ntp_section.Font = Font(self._lbl_ntp_section.Font.FontFamily,
                                          self._lbl_ntp_section.Font.Size, FontStyle.Bold)
        self._lbl_ntp_section.Location = Point(5, 103)
        self._lbl_ntp_section.Size = Size(750, 18)
        self._pnl_timing_ntp.Controls.Add(self._lbl_ntp_section)

        self._lbl_ntp_warning = Label()
        self._lbl_ntp_warning.Text = "\u26a0  Not stored in Tangra CSV \u2014 cannot be auto-verified"
        self._lbl_ntp_warning.Location = Point(5, 122)
        self._lbl_ntp_warning.Size = Size(750, 18)
        self._lbl_ntp_warning.ForeColor = Color.DarkOrange
        self._pnl_timing_ntp.Controls.Add(self._lbl_ntp_warning)

        self._rad_corrections_applied = RadioButton()
        self._rad_corrections_applied.Text = "Applied in Tangra \u2014 corrections were entered before this observation"
        self._rad_corrections_applied.Location = Point(5, 145)
        self._rad_corrections_applied.Size = Size(890, 22)
        self._rad_corrections_applied.CheckedChanged += self._on_timing_radio_changed
        self._pnl_timing_ntp.Controls.Add(self._rad_corrections_applied)

        self._rad_corrections_not_applied = RadioButton()
        self._rad_corrections_not_applied.Text = "Not yet applied \u2014 I need to apply corrections in Tangra first"
        self._rad_corrections_not_applied.Location = Point(5, 167)
        self._rad_corrections_not_applied.Size = Size(890, 22)
        self._rad_corrections_not_applied.CheckedChanged += self._on_timing_radio_changed
        self._pnl_timing_ntp.Controls.Add(self._rad_corrections_not_applied)

        self._rad_corrections_na = RadioButton()
        self._rad_corrections_na.Text = "Not applicable / no NTP data"
        self._rad_corrections_na.Location = Point(5, 189)
        self._rad_corrections_na.Size = Size(890, 22)
        self._rad_corrections_na.CheckedChanged += self._on_timing_radio_changed
        self._pnl_timing_ntp.Controls.Add(self._rad_corrections_na)

        self._lbl_net_heading = Label()
        self._lbl_net_heading.Text = "Net correction:"
        self._lbl_net_heading.Font = Font(self._lbl_net_heading.Font.FontFamily,
                                          self._lbl_net_heading.Font.Size, FontStyle.Bold)
        self._lbl_net_heading.Location = Point(5, 220)
        self._lbl_net_heading.Size = Size(120, 18)
        self._pnl_timing_ntp.Controls.Add(self._lbl_net_heading)

        self._lbl_net_correction = Label()
        self._lbl_net_correction.Text = "\u2014"
        self._lbl_net_correction.Location = Point(130, 220)
        self._lbl_net_correction.Size = Size(780, 18)
        self._pnl_timing_ntp.Controls.Add(self._lbl_net_correction)

        self._lbl_d_preview = Label()
        self._lbl_d_preview.Text = ""
        self._lbl_d_preview.Location = Point(5, 242)
        self._lbl_d_preview.Size = Size(450, 16)
        self._lbl_d_preview.ForeColor = Color.Gray
        self._pnl_timing_ntp.Controls.Add(self._lbl_d_preview)

        self._lbl_r_preview = Label()
        self._lbl_r_preview.Text = ""
        self._lbl_r_preview.Location = Point(460, 242)
        self._lbl_r_preview.Size = Size(450, 16)
        self._lbl_r_preview.ForeColor = Color.Gray
        self._pnl_timing_ntp.Controls.Add(self._lbl_r_preview)

        # --- Step-by-step guidance panel (visible when "Not yet applied" is selected) ---
        self._pnl_apply_guidance = Panel()
        self._pnl_apply_guidance.Location = Point(0, 268)
        self._pnl_apply_guidance.Size = Size(922, 118)
        self._pnl_apply_guidance.BackColor = Color.LightYellow
        self._pnl_apply_guidance.Visible = False
        self._pnl_timing_ntp.Controls.Add(self._pnl_apply_guidance)

        lbl_g_head = Label()
        lbl_g_head.Text = "\u270e  Apply these corrections in Tangra before generating the report:"
        lbl_g_head.Font = Font(lbl_g_head.Font.FontFamily, lbl_g_head.Font.Size, FontStyle.Bold)
        lbl_g_head.Location = Point(8, 6)
        lbl_g_head.Size = Size(900, 18)
        self._pnl_apply_guidance.Controls.Add(lbl_g_head)

        lbl_g_cam = Label()
        lbl_g_cam.Text = "Camera acquisition delay:"
        lbl_g_cam.Location = Point(8, 28)
        lbl_g_cam.Size = Size(175, 22)
        self._pnl_apply_guidance.Controls.Add(lbl_g_cam)

        self._lbl_copy_cam_delay = Label()
        self._lbl_copy_cam_delay.Text = "\u2014"
        self._lbl_copy_cam_delay.Font = Font(self._lbl_copy_cam_delay.Font.FontFamily,
                                             self._lbl_copy_cam_delay.Font.Size, FontStyle.Bold)
        self._lbl_copy_cam_delay.Location = Point(186, 28)
        self._lbl_copy_cam_delay.Size = Size(130, 22)
        self._pnl_apply_guidance.Controls.Add(self._lbl_copy_cam_delay)

        self._btn_copy_cam_delay = Button()
        self._btn_copy_cam_delay.Text = "Copy"
        self._btn_copy_cam_delay.Location = Point(320, 26)
        self._btn_copy_cam_delay.Size = Size(60, 26)
        self._btn_copy_cam_delay.Click += self._on_copy_cam_delay_click
        self._pnl_apply_guidance.Controls.Add(self._btn_copy_cam_delay)

        lbl_g_ntp = Label()
        lbl_g_ntp.Text = "NTP clock offset:"
        lbl_g_ntp.Location = Point(8, 56)
        lbl_g_ntp.Size = Size(175, 22)
        self._pnl_apply_guidance.Controls.Add(lbl_g_ntp)

        self._lbl_copy_ntp_off = Label()
        self._lbl_copy_ntp_off.Text = "\u2014"
        self._lbl_copy_ntp_off.Font = Font(self._lbl_copy_ntp_off.Font.FontFamily,
                                           self._lbl_copy_ntp_off.Font.Size, FontStyle.Bold)
        self._lbl_copy_ntp_off.Location = Point(186, 56)
        self._lbl_copy_ntp_off.Size = Size(130, 22)
        self._pnl_apply_guidance.Controls.Add(self._lbl_copy_ntp_off)

        self._btn_copy_ntp_off = Button()
        self._btn_copy_ntp_off.Text = "Copy"
        self._btn_copy_ntp_off.Location = Point(320, 54)
        self._btn_copy_ntp_off.Size = Size(60, 26)
        self._btn_copy_ntp_off.Click += self._on_copy_ntp_offset_click
        self._pnl_apply_guidance.Controls.Add(self._btn_copy_ntp_off)

        lbl_g_instr = Label()
        lbl_g_instr.Text = (
            "After applying: re-run AOTA or PyOTE and save the result files to your observation folder."
        )
        lbl_g_instr.Location = Point(8, 86)
        lbl_g_instr.Size = Size(555, 20)
        lbl_g_instr.ForeColor = Color.Gray
        self._pnl_apply_guidance.Controls.Add(lbl_g_instr)

        self._btn_rescan_guidance = Button()
        self._btn_rescan_guidance.Text = "\u21bb  Rescan Folder"
        self._btn_rescan_guidance.Location = Point(575, 83)
        self._btn_rescan_guidance.Size = Size(135, 28)
        self._btn_rescan_guidance.Click += self._on_rescan_from_guidance_click
        self._pnl_apply_guidance.Controls.Add(self._btn_rescan_guidance)

        # --- GPS flash (dumb) panel ---
        self._pnl_timing_gps = Panel()
        self._pnl_timing_gps.Location = Point(8, 76)
        self._pnl_timing_gps.Size = Size(922, 60)
        self._pnl_timing_gps.Visible = False
        grp_timing.Controls.Add(self._pnl_timing_gps)

        lbl_gps_info = Label()
        lbl_gps_info.Text = (
            "\u24d8  GPS flash (Camilleri method) correction support is planned for Phase 2.\n"
            "   The flash overlay delay measurement is performed in the gps-timing-analysis tool."
        )
        lbl_gps_info.Location = Point(5, 8)
        lbl_gps_info.Size = Size(900, 40)
        lbl_gps_info.ForeColor = Color.Gray
        self._pnl_timing_gps.Controls.Add(lbl_gps_info)

        # --- GPS-integrated CMOS camera panel ---
        self._pnl_timing_gps_cmos = Panel()
        self._pnl_timing_gps_cmos.Location = Point(8, 76)
        self._pnl_timing_gps_cmos.Size = Size(922, 55)
        self._pnl_timing_gps_cmos.Visible = False
        grp_timing.Controls.Add(self._pnl_timing_gps_cmos)

        lbl_gps_cmos_info1 = Label()
        lbl_gps_cmos_info1.Text = (
            "\u24d8  GPS-integrated cameras (QHY 174GPS, ASTRID, DVTI-cam, Touptek GPS) "
            "embed accurate GPS-synchronized timestamps."
        )
        lbl_gps_cmos_info1.Location = Point(5, 5)
        lbl_gps_cmos_info1.Size = Size(910, 20)
        self._pnl_timing_gps_cmos.Controls.Add(lbl_gps_cmos_info1)

        lbl_gps_cmos_info2 = Label()
        lbl_gps_cmos_info2.Text = (
            "\u2714  No timing corrections are required. "
            "Any report form (NA, TT, SODIS) is compatible with these cameras."
        )
        lbl_gps_cmos_info2.Location = Point(5, 28)
        lbl_gps_cmos_info2.Size = Size(910, 20)
        lbl_gps_cmos_info2.ForeColor = Color.Green
        self._pnl_timing_gps_cmos.Controls.Add(lbl_gps_cmos_info2)

        # --- Analog video + VTI panel ---
        self._pnl_timing_analog_vti = Panel()
        self._pnl_timing_analog_vti.Location = Point(8, 76)
        self._pnl_timing_analog_vti.Size = Size(922, 120)
        self._pnl_timing_analog_vti.Visible = False
        grp_timing.Controls.Add(self._pnl_timing_analog_vti)

        lbl_analog_tool = Label()
        lbl_analog_tool.Text = "Analysis tool used to determine D and R times:"
        lbl_analog_tool.Location = Point(5, 5)
        lbl_analog_tool.Size = Size(360, 22)
        self._pnl_timing_analog_vti.Controls.Add(lbl_analog_tool)

        self._rad_analog_aota = RadioButton()
        self._rad_analog_aota.Text = "AOTA"
        self._rad_analog_aota.Location = Point(370, 3)
        self._rad_analog_aota.Size = Size(75, 22)
        self._rad_analog_aota.Checked = True
        self._rad_analog_aota.CheckedChanged += self._on_analog_tool_changed
        self._pnl_timing_analog_vti.Controls.Add(self._rad_analog_aota)

        self._rad_analog_pyote = RadioButton()
        self._rad_analog_pyote.Text = "PyOTE"
        self._rad_analog_pyote.Location = Point(455, 3)
        self._rad_analog_pyote.Size = Size(80, 22)
        self._rad_analog_pyote.CheckedChanged += self._on_analog_tool_changed
        self._pnl_timing_analog_vti.Controls.Add(self._rad_analog_pyote)

        # Dynamic info/warning label — updated by _update_analog_vti_warnings()
        self._lbl_vti_info = Label()
        self._lbl_vti_info.Text = ""
        self._lbl_vti_info.Location = Point(5, 32)
        self._lbl_vti_info.Size = Size(910, 82)
        self._pnl_timing_analog_vti.Controls.Add(self._lbl_vti_info)

        # --- Other panel ---
        self._pnl_timing_other = Panel()
        self._pnl_timing_other.Location = Point(8, 76)
        self._pnl_timing_other.Size = Size(922, 40)
        self._pnl_timing_other.Visible = True
        grp_timing.Controls.Add(self._pnl_timing_other)

        lbl_other_info = Label()
        lbl_other_info.Text = (
            "\u24d8  Timing corrections are not applied by OM for this method. "
            "Apply corrections in Tangra/PyOTE, PyMovie, or the NA reporting form "
            "before generating this report."
        )
        lbl_other_info.Location = Point(5, 8)
        lbl_other_info.Size = Size(900, 30)
        lbl_other_info.ForeColor = Color.Gray
        self._pnl_timing_other.Controls.Add(lbl_other_info)

        y_pos += 485

        # ===== SECTION 4: OBSERVATION FILES =====
        grp_files = GroupBox()
        grp_files.Text = "4. Observation Files"
        grp_files.Location = Point(10, y_pos)
        grp_files.Size = Size(940, 365)
        main_panel.Controls.Add(grp_files)

        # Three-column layout for file lists
        # Tangra CSV files (left)
        lbl_csv = Label()
        lbl_csv.Text = "Light Curve File:"
        lbl_csv.Location = Point(15, 25)
        lbl_csv.Size = Size(130, 20)
        grp_files.Controls.Add(lbl_csv)

        self.csv_count_label = Label()
        self.csv_count_label.Text = "No folder"
        self.csv_count_label.Location = Point(145, 25)
        self.csv_count_label.Size = Size(155, 20)
        self.csv_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.csv_count_label)

        self.csv_listbox = ListBox()
        self.csv_listbox.Location = Point(15, 48)
        self.csv_listbox.Size = Size(285, 65)
        self.csv_listbox.SelectionMode = SelectionMode.One
        self.csv_listbox.SelectedIndexChanged += self.selection_changed
        grp_files.Controls.Add(self.csv_listbox)

        self.csv_preview_label = Label()
        self.csv_preview_label.Text = "Observing times: -"
        self.csv_preview_label.Location = Point(15, 116)
        self.csv_preview_label.Size = Size(285, 40)
        self.csv_preview_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.csv_preview_label)

        # AOTA files (middle)
        lbl_aota = Label()
        lbl_aota.Text = "AOTA Files:"
        lbl_aota.Location = Point(315, 25)
        lbl_aota.Size = Size(120, 20)
        grp_files.Controls.Add(lbl_aota)

        self.aota_count_label = Label()
        self.aota_count_label.Text = "No folder"
        self.aota_count_label.Location = Point(435, 25)
        self.aota_count_label.Size = Size(165, 20)
        self.aota_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.aota_count_label)

        self.aota_listbox = ListBox()
        self.aota_listbox.Location = Point(315, 48)
        self.aota_listbox.Size = Size(285, 65)
        self.aota_listbox.SelectionMode = SelectionMode.One
        self.aota_listbox.SelectedIndexChanged += self.selection_changed
        grp_files.Controls.Add(self.aota_listbox)

        self.aota_preview_label = Label()
        self.aota_preview_label.Text = "D/R: -"
        self.aota_preview_label.Location = Point(315, 116)
        self.aota_preview_label.Size = Size(285, 40)
        self.aota_preview_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.aota_preview_label)

        # AOTA Report files (right)
        lbl_report = Label()
        lbl_report.Text = "AOTA Report:"
        lbl_report.Location = Point(615, 25)
        lbl_report.Size = Size(120, 20)
        grp_files.Controls.Add(lbl_report)

        self.report_count_label = Label()
        self.report_count_label.Text = "No folder"
        self.report_count_label.Location = Point(735, 25)
        self.report_count_label.Size = Size(185, 20)
        self.report_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.report_count_label)

        self.report_listbox = ListBox()
        self.report_listbox.Location = Point(615, 48)
        self.report_listbox.Size = Size(305, 65)
        self.report_listbox.SelectionMode = SelectionMode.One
        self.report_listbox.SelectedIndexChanged += self.selection_changed
        grp_files.Controls.Add(self.report_listbox)

        self.report_preview_label = Label()
        self.report_preview_label.Text = "D/R: -"
        self.report_preview_label.Location = Point(615, 116)
        self.report_preview_label.Size = Size(305, 40)
        self.report_preview_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.report_preview_label)

        # PyOTE Metrics row (full-width, below the three columns)
        lbl_pyote = Label()
        lbl_pyote.Text = "PyOTE Metrics:"
        lbl_pyote.Location = Point(15, 165)
        lbl_pyote.Size = Size(120, 20)
        grp_files.Controls.Add(lbl_pyote)

        self.pyote_count_label = Label()
        self.pyote_count_label.Text = "No folder"
        self.pyote_count_label.Location = Point(135, 165)
        self.pyote_count_label.Size = Size(200, 20)
        self.pyote_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.pyote_count_label)

        lbl_pyote_event = Label()
        lbl_pyote_event.Text = "Events:"
        lbl_pyote_event.Location = Point(460, 165)
        lbl_pyote_event.Size = Size(60, 20)
        grp_files.Controls.Add(lbl_pyote_event)

        self.pyote_event_count_label = Label()
        self.pyote_event_count_label.Text = "-"
        self.pyote_event_count_label.Location = Point(525, 165)
        self.pyote_event_count_label.Size = Size(210, 20)
        self.pyote_event_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.pyote_event_count_label)

        self.pyote_listbox = ListBox()
        self.pyote_listbox.Location = Point(15, 185)
        self.pyote_listbox.Size = Size(430, 55)
        self.pyote_listbox.SelectionMode = SelectionMode.One
        self.pyote_listbox.SelectedIndexChanged += self._pyote_file_selection_changed
        grp_files.Controls.Add(self.pyote_listbox)

        self.pyote_event_listbox = ListBox()
        self.pyote_event_listbox.Location = Point(460, 185)
        self.pyote_event_listbox.Size = Size(460, 55)
        self.pyote_event_listbox.SelectionMode = SelectionMode.One
        self.pyote_event_listbox.SelectedIndexChanged += self._pyote_event_selection_changed
        grp_files.Controls.Add(self.pyote_event_listbox)

        self.pyote_preview_label = Label()
        self.pyote_preview_label.Text = "D/R: -"
        self.pyote_preview_label.Location = Point(15, 244)
        self.pyote_preview_label.Size = Size(905, 22)
        self.pyote_preview_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.pyote_preview_label)

        # ===== TIMESTAMP CHECK SUBPANEL =====
        grp_ts_check = GroupBox()
        grp_ts_check.Text = "Timestamp Check"
        grp_ts_check.Location = Point(15, 271)
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

        y_pos += 365

        # ===== SECTION 5: OBSERVATION RESULT =====
        grp_obs_type = GroupBox()
        grp_obs_type.Text = "5. Observation Result"
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

        # ===== SECTION 6: CONDITIONS =====
        grp_conditions = GroupBox()
        grp_conditions.Text = "6. Conditions"
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

        # Pre-select timing method from camera config
        self._init_timing_section()
    
    def load_equipment(self):
        """Load telescopes and cameras into dropdowns"""
        # Remember current telescope/camera selections so they survive a reload
        current_tel_id = self._get_current_telescope_id()
        current_cam_id = self._get_current_camera_id()

        # Load telescopes
        self.combo_telescope.Items.Clear()
        telescopes = self.config.get_telescopes()
        active_telescope = self.config.get_active_telescope()
        active_tel_id = active_telescope.get('id') if active_telescope else None

        if not telescopes:
            self.combo_telescope.Items.Add("No telescopes configured - click Manage...")
            self.combo_telescope.SelectedIndex = 0
            self.combo_telescope.Enabled = False
        else:
            self.combo_telescope.Enabled = True
            restore_idx = 0
            for i, telescope in enumerate(telescopes):
                name = telescope.get('name', 'Unnamed')
                if telescope.get('id') == active_tel_id:
                    name = "★ " + name
                self.combo_telescope.Items.Add(name)
                tel_id = telescope.get('id')
                if current_tel_id and tel_id == current_tel_id:
                    restore_idx = i
                elif not current_tel_id and tel_id == active_tel_id:
                    restore_idx = i
            self.combo_telescope.SelectedIndex = restore_idx

        # Load cameras - show ALL cameras so the user can pick any
        self.combo_camera.Items.Clear()
        cameras = self.config.get_cameras()
        active_camera = self.config.get_active_camera()
        active_cam_id = active_camera.get('id') if active_camera else None

        if not cameras:
            self.combo_camera.Items.Add("No cameras configured - click Manage...")
            self.combo_camera.SelectedIndex = 0
            self.combo_camera.Enabled = False
        else:
            self.combo_camera.Enabled = True
            restore_idx = 0
            for i, camera in enumerate(cameras):
                name = camera.get('name', 'Unnamed')
                if camera.get('id') == active_cam_id:
                    name = "★ " + name
                self.combo_camera.Items.Add(name)
                cam_id = camera.get('id')
                if current_cam_id and cam_id == current_cam_id:
                    restore_idx = i
                elif not current_cam_id and cam_id == active_cam_id:
                    restore_idx = i
            self.combo_camera.SelectedIndex = restore_idx
    
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
        self._update_analog_vti_warnings()
        self.update_button_state()
    
    def equipment_changed(self, sender, e):
        """Handle equipment dropdown change"""
        if sender is self.combo_camera:
            new_cam_id = self._get_current_camera_id()
            if new_cam_id != self._last_cam_id:
                self._last_cam_id = new_cam_id
                self._correction_user_set = False  # fresh camera → reset user override
                self._populate_calib_runs()
                self._init_timing_section()
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

            if hasattr(self, '_combo_calib_run'):
                self._populate_calib_runs()
            self._update_file_status_labels()

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
        if sender is self.csv_listbox:
            self._populate_calib_runs()
        self.update_button_state()

    def update_extracted_time_previews(self):
        """Update preview labels with extracted times from selected files"""
        self._update_tangra_preview()
        self._update_aota_xml_preview()
        self._update_aota_report_preview()
        self._update_pyote_preview()
        self._update_timing_net_preview()

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
            # Set D/R seconds as fallback when AOTA XML did not provide them
            if self._d_time_seconds is None:
                try:
                    dh = int(summary.get('d_hours') or 0)
                    dm = int(summary.get('d_minutes') or 0)
                    ds = float(summary.get('d_seconds') or 0.0)
                    if dh or dm or ds:
                        self._d_time_seconds = dh * 3600.0 + dm * 60.0 + ds
                except Exception:
                    pass
            if self._r_time_seconds is None:
                try:
                    rh = int(summary.get('r_hours') or 0)
                    rm = int(summary.get('r_minutes') or 0)
                    rs = float(summary.get('r_seconds') or 0.0)
                    if rh or rm or rs:
                        self._r_time_seconds = rh * 3600.0 + rm * 60.0 + rs
                except Exception:
                    pass
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
        # Set D/R seconds as fallback when neither XML nor AOTA Report provided them
        if self._d_time_seconds is None and d_time and d_time != '?':
            try:
                parts = str(d_time).split(':')
                if len(parts) == 3:
                    self._d_time_seconds = int(parts[0]) * 3600.0 + int(parts[1]) * 60.0 + float(parts[2])
            except Exception:
                pass
        if self._r_time_seconds is None and r_time and r_time != '?':
            try:
                parts = str(r_time).split(':')
                if len(parts) == 3:
                    self._r_time_seconds = int(parts[0]) * 3600.0 + int(parts[1]) * 60.0 + float(parts[2])
            except Exception:
                pass
    
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
        # Use .Enabled as proxy: combo is disabled when no equipment exists for the current filter
        has_telescope = self.combo_telescope.Enabled and self.combo_telescope.SelectedIndex >= 0
        has_camera = self.combo_camera.Enabled and self.combo_camera.SelectedIndex >= 0
        
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

        # Block generate if NTP timing selected but corrections not yet applied in Tangra
        if (hasattr(self, '_rad_timing_ntp') and self._rad_timing_ntp.Checked
                and hasattr(self, '_rad_corrections_not_applied')
                and self._rad_corrections_not_applied.Checked):
            missing.append("timing corrections \u2014 apply in Tangra first (see \u00a73 guidance below)")

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
        cameras = self.config.get_cameras()

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

        # VTI safety check — may show a blocking or confirmation dialog
        if not self._check_analog_vti_before_generate():
            return

        self.DialogResult = DialogResult.OK
        self.Close()
    
    def _check_analog_vti_before_generate(self):
        """Show dialog warnings for Analog+VTI timing combinations.

        Returns True if generation can proceed, False to abort.
        Called just before DialogResult.OK is set in generate_click.
        """
        if not (hasattr(self, '_rad_timing_analog_vti') and self._rad_timing_analog_vti.Checked):
            return True
        is_aota = hasattr(self, '_rad_analog_aota') and self._rad_analog_aota.Checked
        is_pyote = hasattr(self, '_rad_analog_pyote') and self._rad_analog_pyote.Checked
        is_na = self.rb_na.Checked
        is_tt_sodis = self.rb_tt.Checked or self.rb_sodis.Checked

        if is_pyote and is_tt_sodis:
            # Genuinely incompatible — explain and block
            MessageBox.Show(
                "This combination cannot produce correctly-timed results:\n\n"
                "    \u2022  Analysis tool: PyOTE\n"
                "    \u2022  Report form: TT or SODIS\n"
                "    \u2022  Camera timing: Analog video + VTI\n\n"
                "PyOTE does NOT apply VTI timing corrections to D/R times.\n"
                "The TT and SODIS report forms do NOT apply them automatically either.\n\n"
                "To fix this, choose one of:\n"
                "    \u2022  Change the report form to IOTA NA (it applies VTI corrections automatically), OR\n"
                "    \u2022  Re-analyse the light curve using AOTA instead of PyOTE.",
                "Incompatible Combination \u2014 Cannot Generate",
                MessageBoxButtons.OK,
                MessageBoxIcon.Stop
            )
            return False

        if is_aota and is_na:
            # Dangerous — require explicit confirmation via custom dialog
            dlg = VTIDoubleCorrectConfirmDialog(self.theme_manager)
            result = dlg.ShowDialog(self)
            return dlg.confirmed

        return True

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

    def get_timing_data(self):
        """Return timing_data dict from §3 Timing inputs, or None if method needs no OM correction."""
        if not hasattr(self, '_rad_timing_ntp'):
            return None
        if self._rad_timing_ntp.Checked:
            method = 'NTP'
        elif self._rad_timing_gps.Checked:
            method = 'GPS_dumb'
        elif self._rad_timing_gps_cmos.Checked:
            return None  # Already GPS-corrected, no OM adjustment needed
        elif self._rad_timing_analog_vti.Checked:
            return None  # Corrections handled by AOTA or NA form
        else:
            return None  # Other method: no OM timing correction
        from timing_utils import build_timing_data
        if method == 'GPS_dumb':
            return build_timing_data('GPS_dumb')
        # NTP method
        camera_delay_ms = self._calculate_camera_delay() or 0.0
        calib_run_id = None
        if self._calib_runs and self._combo_calib_run.SelectedIndex >= 0:
            idx = self._combo_calib_run.SelectedIndex
            if idx < len(self._calib_runs):
                calib_run_id = self._calib_runs[idx].get('id')
        try:
            y_line = int(float(self._txt_y_line.Text.strip() or '0'))
        except (ValueError, TypeError):
            y_line = 0
        if self._rad_corrections_applied.Checked:
            camera_delay_applied = True
            ntp_applied = True
        elif self._rad_corrections_not_applied.Checked:
            # User will apply corrections in Tangra; no internal D/R correction applied by OM
            camera_delay_applied = None
            ntp_applied = None
        elif self._rad_corrections_na.Checked:
            camera_delay_applied = None
            ntp_applied = True  # No corrections to apply
        else:
            camera_delay_applied = None
            ntp_applied = None
        ntp_offset_ms = 0.0 if self._rad_corrections_na.Checked else self._ntp_offset_ms
        return build_timing_data(
            timing_method='NTP',
            camera_delay_ms=camera_delay_ms,
            camera_delay_y_line=y_line,
            calib_run_id=calib_run_id,
            ntp_offset_ms=ntp_offset_ms,
            camera_delay_applied=camera_delay_applied,
            ntp_applied=ntp_applied,
        )

    # ------------------------------------------------------------------
    # Timing section helpers
    # ------------------------------------------------------------------

    def _get_current_camera_id(self):
        """Return the camera ID currently selected in §1, or None."""
        idx = self.combo_camera.SelectedIndex
        if idx < 0:
            return None
        cameras = self.config.get_cameras()
        if 0 <= idx < len(cameras):
            return cameras[idx].get('id')
        return None

    def _get_current_telescope_id(self):
        """Return the telescope ID currently selected in §1, or None."""
        idx = self.combo_telescope.SelectedIndex
        if idx < 0:
            return None
        telescopes = self.config.get_telescopes()
        if 0 <= idx < len(telescopes):
            return telescopes[idx].get('id')
        return None

    def _init_timing_section(self):
        """Pre-select timing method from the selected camera's config field."""
        if not hasattr(self, '_rad_timing_ntp'):
            return
        cam_id = self._get_current_camera_id()
        timing_str = ''
        occult4_method = ''
        detector = ''
        name = ''
        if cam_id:
            for cam in self.config.get_cameras():
                if cam.get('id') == cam_id:
                    timing_str = cam.get('timing', '') or ''
                    occult4_method = cam.get('occult4_method', '') or ''
                    detector = cam.get('detector', '') or ''
                    name = cam.get('name', '') or ''
                    break
        timing_lower = timing_str.lower()
        # GPS-integrated CMOS cameras (QHY 174GPS, ASTRID, DVTI-cam, Touptek GPS)
        gps_cmos_keywords = ['174gps', 'astrid', 'dvti', 'touptek gps', 'qhy gps']
        is_gps_cmos = any(k in d.lower() for k in gps_cmos_keywords for d in (detector, name))
        # Analog video + VTI
        vti_timings = ['iota-vti', 'gps - time inserted', 'gps - other linking', 'gps - kiwi']
        is_analog = 'analogue' in occult4_method.lower()
        is_vti = any(v.lower() in timing_lower for v in vti_timings)
        is_analog_vti = is_analog and is_vti
        if is_gps_cmos:
            self._rad_timing_gps_cmos.Checked = True
        elif is_analog_vti:
            self._rad_timing_analog_vti.Checked = True
            self._update_analog_vti_warnings()
        elif 'ntp' in timing_lower:
            self._rad_timing_ntp.Checked = True
        else:
            self._rad_timing_other.Checked = True
        self._populate_ntp_offset_label()

    def _populate_ntp_offset_label(self):
        """Fill the NTP correction label from event.ntp_analysis_result."""
        if not hasattr(self, '_lbl_ntp_section'):
            return
        ntp_result = getattr(self.event, 'ntp_analysis_result', None)
        if ntp_result:
            self._ntp_offset_ms = float(ntp_result.get('best_offset', 0.0)) * 1000.0
            self._ntp_uncertainty_ms = float(ntp_result.get('u_expanded', 0.0)) * 1000.0
            self._lbl_ntp_section.Text = "NTP correction:  {0:+.1f} ms  (\u00b1{1:.1f} ms, 95%)".format(
                self._ntp_offset_ms, self._ntp_uncertainty_ms)
            self._lbl_ntp_warning.Text = "\u26a0  Not stored in Tangra CSV \u2014 cannot be auto-verified"
            self._lbl_ntp_warning.ForeColor = Color.DarkOrange
        else:
            self._ntp_offset_ms = 0.0
            self._ntp_uncertainty_ms = 0.0
            self._lbl_ntp_section.Text = "NTP correction:  no analysis data available"
            self._lbl_ntp_warning.Text = ""
            self._rad_corrections_na.Checked = True
        self._update_guidance_values()

    def _on_timing_method_changed(self, sender, e):
        """Show/hide timing sub-panels when method radio changes."""
        if not sender.Checked:
            return
        is_ntp = self._rad_timing_ntp.Checked
        is_gps = self._rad_timing_gps.Checked
        is_gps_cmos = self._rad_timing_gps_cmos.Checked
        is_analog_vti = self._rad_timing_analog_vti.Checked
        self._pnl_timing_ntp.Visible = is_ntp
        self._pnl_timing_gps.Visible = is_gps
        self._pnl_timing_gps_cmos.Visible = is_gps_cmos
        self._pnl_timing_analog_vti.Visible = is_analog_vti
        self._pnl_timing_other.Visible = not (is_ntp or is_gps or is_gps_cmos or is_analog_vti)
        if is_ntp:
            self._populate_calib_runs()
        if is_analog_vti:
            self._update_analog_vti_warnings()
        self.update_button_state()

    def _on_analog_tool_changed(self, sender, e):
        """Handle AOTA/PyOTE radio change in the Analog+VTI timing panel."""
        if not sender.Checked:
            return
        self._update_analog_vti_warnings()
        self.update_button_state()

    def _update_analog_vti_warnings(self):
        """Update the Analog+VTI info panel based on report format and analysis tool."""
        if not hasattr(self, '_lbl_vti_info') or not hasattr(self, '_rad_timing_analog_vti'):
            return
        if not self._rad_timing_analog_vti.Checked:
            return
        is_aota = self._rad_analog_aota.Checked
        is_na = self.rb_na.Checked
        is_tt_sodis = self.rb_tt.Checked or self.rb_sodis.Checked
        if is_aota and is_na:
            self._lbl_vti_info.Text = (
                "\u26a0  WARNING: The NA form automatically applies VTI corrections to D/R times. "
                "Do NOT apply corrections inside AOTA \u2014 the times will be double-corrected."
            )
            self._lbl_vti_info.ForeColor = Color.OrangeRed
        elif is_aota and is_tt_sodis:
            self._lbl_vti_info.Text = (
                "\u24d8  TT and SODIS forms do not automatically apply VTI corrections. "
                "Ensure VTI corrections (camera + VTI delay) are applied inside AOTA."
            )
            self._lbl_vti_info.ForeColor = Color.DarkOrange
        elif not is_aota and is_na:
            self._lbl_vti_info.Text = (
                "\u2714  NA report form will automatically apply VTI corrections to D/R times."
            )
            self._lbl_vti_info.ForeColor = Color.Green
        elif not is_aota and is_tt_sodis:
            self._lbl_vti_info.Text = (
                "\u26d4  INCOMPATIBLE: PyOTE does not apply VTI corrections, and TT/SODIS forms "
                "do not apply them automatically. D/R times will be uncorrected.\n"
                "Use the NA report form, or use AOTA to analyse the light curve."
            )
            self._lbl_vti_info.ForeColor = Color.Red
        else:
            self._lbl_vti_info.Text = "Select a report format in \u00a72 above to see guidance."
            self._lbl_vti_info.ForeColor = Color.Gray

    def _update_file_status_labels(self):
        """Update file availability status label in \u00a72 Report Format section."""
        if not hasattr(self, '_lbl_file_status'):
            return
        folder = self.current_folder
        if not folder or not os.path.isdir(folder):
            self._lbl_file_status.Text = "No folder selected"
            self._lbl_file_status.ForeColor = Color.Gray
            return
        cs_path = self._find_sharpCap_settings_file(folder)
        cs_sym = '\u2714' if cs_path else '\u2014'
        n_csv = len(self.csv_files)
        n_aota = len(self.aota_files)
        n_report = len(self.aota_report_files)
        n_pyote = len(self.pyote_files)
        parts = [
            "CameraSettings: {0}".format(cs_sym),
            "CSV: {0}".format(n_csv),
            "AOTA: {0}".format(n_aota),
            "AOTA Report: {0}".format(n_report),
            "PyOTE: {0}".format(n_pyote),
        ]
        self._lbl_file_status.Text = "  |  ".join(parts)
        self._lbl_file_status.ForeColor = Color.Green if (n_csv > 0 or n_aota > 0) else Color.Gray

    def _update_guidance_values(self):
        """Refresh the copy-value labels in the NTP step-by-step guidance panel."""
        if not hasattr(self, '_lbl_copy_cam_delay'):
            return
        delay_ms = self._calculate_camera_delay()
        ntp_ms = getattr(self, '_ntp_offset_ms', 0.0)
        if delay_ms is not None:
            self._lbl_copy_cam_delay.Text = '{0:.1f} ms'.format(delay_ms)
            self._copy_cam_delay_value = '{0:.1f}'.format(delay_ms)
        else:
            self._lbl_copy_cam_delay.Text = '\u2014 (enter Y line above)'
            self._copy_cam_delay_value = None
        ntp_copy = '{0:.1f}'.format(ntp_ms)
        self._lbl_copy_ntp_off.Text = ntp_copy + ' ms'
        self._copy_ntp_off_value = ntp_copy
        # Toggle guidance panel visibility
        not_yet = (hasattr(self, '_rad_corrections_not_applied')
                   and self._rad_corrections_not_applied.Checked)
        if hasattr(self, '_pnl_apply_guidance'):
            self._pnl_apply_guidance.Visible = not_yet

    def _on_copy_cam_delay_click(self, sender, e):
        """Copy calculated camera delay value to clipboard."""
        val = getattr(self, '_copy_cam_delay_value', None)
        if val is not None:
            Clipboard.SetText(val)
        else:
            MessageBox.Show(
                "No camera delay calculated yet.\nEnter a Y line value in \u00a73 above.",
                "Nothing to Copy",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )

    def _on_copy_ntp_offset_click(self, sender, e):
        """Copy NTP offset value to clipboard."""
        val = getattr(self, '_copy_ntp_off_value', None)
        if val is not None:
            Clipboard.SetText(val)
        else:
            MessageBox.Show(
                "No NTP offset available.",
                "Nothing to Copy",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )

    def _on_rescan_from_guidance_click(self, sender, e):
        """Re-scan the observation folder after applying corrections in Tangra."""
        if self.current_folder and os.path.isdir(self.current_folder):
            self.scan_folder(self.current_folder)
            MessageBox.Show(
                "Folder rescanned.\n\n"
                "If your corrected AOTA or PyOTE files are now visible in the \u00a74 file lists,\n"
                "select 'Applied in Tangra' in \u00a73 above to confirm and enable report generation.",
                "Rescan Complete",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
        else:
            MessageBox.Show(
                "No observation folder selected.\nBrowse to your folder in \u00a72 first.",
                "No Folder Selected",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )

    def _parse_sharpCap_settings(self, filepath):
        """Parse a SharpCap .CameraSettings file.

        Returns (camera_model_str, fields_dict).  Both may be None/'empty' on error.
        """
        camera_model = None
        fields = {}
        try:
            with open(filepath, 'r') as fh:
                for line in fh:
                    line = line.rstrip('\n').rstrip('\r').strip()
                    if line.startswith('[') and line.endswith(']'):
                        camera_model = line[1:-1]
                    elif '=' in line:
                        key, _, value = line.partition('=')
                        fields[key.strip()] = value.strip()
        except Exception:
            pass
        return camera_model, fields

    def _find_sharpCap_settings_file(self, folder):
        """Return the path of the best-matching .CameraSettings file in folder, or None.

        Picks the file whose StartCapture timestamp is closest to the selected
        Tangra CSV recording start time.  Falls back to most-recently-modified
        when start time is unavailable.
        """
        if not folder or not os.path.isdir(folder):
            return None
        candidates = []
        try:
            for f in os.listdir(folder):
                if f.lower().endswith('.camerasettings'):
                    candidates.append(os.path.join(folder, f))
        except Exception:
            return None
        if not candidates:
            return None
        if len(candidates) == 1:
            return candidates[0]
        # Try to match by StartCapture vs Tangra CSV start time
        tangra_sec = None
        if self._ts_summary:
            start_str = self._ts_summary.get('start_time') or ''
            if start_str and isinstance(start_str, str):
                try:
                    parts = str(start_str).split(':')
                    tangra_sec = int(parts[0]) * 3600.0 + int(parts[1]) * 60.0 + float(parts[2])
                except Exception:
                    pass
        if tangra_sec is not None:
            best = None
            best_diff = None
            for path in candidates:
                _, fields = self._parse_sharpCap_settings(path)
                sc_start = fields.get('StartCapture', '')
                if sc_start:
                    try:
                        time_part = sc_start.split('T')[1].rstrip('Z')
                        t_parts = time_part.split(':')
                        sc_sec = int(t_parts[0]) * 3600.0 + int(t_parts[1]) * 60.0 + float(t_parts[2])
                        diff = abs(sc_sec - tangra_sec)
                        if best_diff is None or diff < best_diff:
                            best_diff = diff
                            best = path
                    except Exception:
                        pass
            if best:
                return best
        # Fall back: most recently modified
        try:
            return max(candidates, key=os.path.getmtime)
        except Exception:
            return candidates[0]

    def _populate_calib_runs(self):
        """Load calibration runs for the selected camera, auto-matching from SharpCap settings."""
        if not hasattr(self, '_combo_calib_run'):
            return
        self._combo_calib_run.Items.Clear()
        self._calib_runs = []
        self._lbl_calib_match.Text = ''
        cam_id = self._get_current_camera_id()
        if not cam_id:
            self._lbl_calib_match.Text = 'No camera selected'
            self._lbl_calib_match.ForeColor = Color.Gray
            return
        all_runs = self.config.get_line_delay_calibrations(camera_id=cam_id)
        if not all_runs:
            self._lbl_calib_match.Text = 'No calibration runs \u2014 run LED calibration first'
            self._lbl_calib_match.ForeColor = Color.OrangeRed
            return
        # Try to read SharpCap settings from the current observation folder
        sc_area = sc_binning = sc_colour = None
        sc_tilt = sc_pan = None
        sc_file_found = False
        folder = self.current_folder
        if folder:
            sc_path = self._find_sharpCap_settings_file(folder)
            if sc_path:
                sc_file_found = True
                _, fields = self._parse_sharpCap_settings(sc_path)
                sc_area = (fields.get('Capture Area')
                           or fields.get('CaptureArea'))
                sc_binning = (fields.get('Binning')
                              or fields.get('Bin'))
                sc_colour = (fields.get('Colour Space')
                             or fields.get('Color Space')
                             or fields.get('ColourSpace')
                             or fields.get('ColorSpace'))
                if 'Tilt' in fields:
                    try:
                        sc_tilt = int(fields['Tilt'])
                    except (ValueError, TypeError):
                        pass
                if 'Pan' in fields:
                    try:
                        sc_pan = int(fields['Pan'])
                    except (ValueError, TypeError):
                        pass
        # Sort all runs by run_datetime descending
        def _run_key(r):
            return r.get('run_datetime', '') or ''
        all_runs_sorted = sorted(all_runs, key=_run_key, reverse=True)

        def _norm_binning(v):
            """Normalise binning to plain integer string: '1x1'→'1', '2x2'→'2', '1'→'1'."""
            s = str(v).strip().lower()
            if 'x' in s:
                s = s.split('x')[0]
            return s

        def _norm_int(v):
            """Convert a stored tilt/pan value (may be int, float string, or '') to int, or None."""
            try:
                return int(str(v).strip().split('.')[0])
            except (ValueError, TypeError, AttributeError):
                return None

        matched_runs = []
        if sc_area or sc_binning:  # attempt match with whatever fields were found
            for run in all_runs_sorted:
                checks = []
                if sc_area:
                    checks.append(
                        str(run.get('camera_area', '')).strip() == str(sc_area).strip())
                if sc_binning:
                    checks.append(
                        _norm_binning(run.get('binning', '')) == _norm_binning(sc_binning))
                if sc_colour:
                    checks.append(
                        str(run.get('colour_space', '')).strip().lower()
                        == str(sc_colour).strip().lower())
                if sc_tilt is not None:
                    run_tilt = _norm_int(run.get('tilt', ''))
                    checks.append(run_tilt is not None and run_tilt == sc_tilt)
                if sc_pan is not None:
                    run_pan = _norm_int(run.get('pan', ''))
                    checks.append(run_pan is not None and run_pan == sc_pan)
                if checks and all(checks):
                    matched_runs.append(run)
        display_runs = matched_runs if matched_runs else all_runs_sorted
        self._calib_runs = display_runs
        for run in display_runs:
            area = run.get('camera_area', '?')
            binning = run.get('binning', '?')
            colour = run.get('colour_space', '?')
            label = run.get('label', '')
            dt = (run.get('run_datetime', '') or '')[:10]
            text = '{0} / {1}x / {2} \u2014 {3}'.format(area, binning, colour, dt)
            if label:
                text += ' ({0})'.format(label)
            self._combo_calib_run.Items.Add(text)
        if display_runs:
            self._combo_calib_run.SelectedIndex = 0
        if matched_runs:
            match_detail = '{0} / {1}x / {2}'.format(sc_area, sc_binning, sc_colour)
            if sc_tilt is not None:
                match_detail += ' / tilt {0}'.format(sc_tilt)
            if sc_pan is not None:
                match_detail += ' / pan {0}'.format(sc_pan)
            self._lbl_calib_match.Text = '\u2714 Auto-matched from SharpCap settings ({0})'.format(match_detail)
            self._lbl_calib_match.ForeColor = Color.Green
        elif sc_area or sc_binning:
            no_match_detail = '{0}/{1}x/{2}'.format(sc_area or '?', sc_binning or '?', sc_colour or '?')
            if sc_tilt is not None:
                no_match_detail += '/tilt {0}'.format(sc_tilt)
            if sc_pan is not None:
                no_match_detail += '/pan {0}'.format(sc_pan)
            self._lbl_calib_match.Text = '\u26a0 No match for {0} \u2014 showing all runs'.format(no_match_detail)
            self._lbl_calib_match.ForeColor = Color.OrangeRed
        elif sc_file_found:
            self._lbl_calib_match.Text = '\u26a0 SharpCap settings found but fields unreadable \u2014 showing all runs'
            self._lbl_calib_match.ForeColor = Color.OrangeRed
        elif folder:
            self._lbl_calib_match.Text = 'No SharpCap settings file found \u2014 showing all runs'
            self._lbl_calib_match.ForeColor = Color.Gray
        else:
            self._lbl_calib_match.Text = 'Browse a folder for auto-match'
            self._lbl_calib_match.ForeColor = Color.Gray

        # Always refresh the delay label unconditionally — SelectedIndexChanged may
        # not fire when SelectedIndex is already 0 before the clear/repopulate cycle.
        if hasattr(self, '_lbl_calc_delay'):
            self._refresh_delay_label()

    def _on_calib_run_changed(self, sender, e):
        self._refresh_delay_label()

    def _on_y_line_changed(self, sender, e):
        self._refresh_delay_label()

    def _on_timing_radio_changed(self, sender, e):
        if not sender.Checked:
            return
        if not self._suppress_correction_event:
            self._correction_user_set = True
        self._update_timing_net_preview()
        self.update_button_state()

    def _get_y_line_max(self):
        """Return the max valid Y pixel from the selected calibration's camera_area, or None."""
        if not self._calib_runs:
            return None
        idx = self._combo_calib_run.SelectedIndex
        if idx < 0 or idx >= len(self._calib_runs):
            return None
        area = str(self._calib_runs[idx].get('camera_area', '') or '')
        try:
            parts = area.lower().split('x')
            if len(parts) >= 2:
                return int(parts[1])
        except (ValueError, IndexError):
            pass
        return None

    def _refresh_delay_label(self):
        """Validate Y-line text, compute delay, update the calc delay label."""
        normal_color = self.theme_manager.get_current_theme()['text_foreground']
        text = self._txt_y_line.Text.strip()
        if not text:
            self._lbl_calc_delay.Text = '\u2014'
            self._lbl_calc_delay.ForeColor = normal_color
            self._auto_detect_camera_delay(None)
            self._update_timing_net_preview()
            return
        try:
            y = float(text)
        except ValueError:
            self._lbl_calc_delay.Text = '\u2014 (not a valid number)'
            self._lbl_calc_delay.ForeColor = Color.OrangeRed
            self._auto_detect_camera_delay(None)
            self._update_timing_net_preview()
            return
        y_max = self._get_y_line_max()
        if y < 0 or (y_max is not None and y > y_max):
            if y_max is not None:
                self._lbl_calc_delay.Text = '\u2014 (must be 0\u2013{0})'.format(y_max)
            else:
                self._lbl_calc_delay.Text = '\u2014 (must be \u22650)'
            self._lbl_calc_delay.ForeColor = Color.OrangeRed
            self._auto_detect_camera_delay(None)
            self._update_timing_net_preview()
            return
        delay_ms = self._calculate_camera_delay()
        if delay_ms is not None:
            self._lbl_calc_delay.Text = '{0:.1f} ms'.format(delay_ms)
        else:
            self._lbl_calc_delay.Text = '\u2014'
        self._lbl_calc_delay.ForeColor = normal_color
        self._auto_detect_camera_delay(delay_ms)
        self._update_timing_net_preview()

    def _calculate_camera_delay(self):
        """Return camera_delay_ms from selected calibration run + Y line, or None."""
        if not self._calib_runs:
            return None
        idx = self._combo_calib_run.SelectedIndex
        if idx < 0 or idx >= len(self._calib_runs):
            return None
        run = self._calib_runs[idx]
        try:
            per_line = float(run.get('per_line_delay', 0.0) or 0.0)
            intercept = float(run.get('line_0_delay', 0.0) or 0.0)
            y = float(self._txt_y_line.Text.strip())
            return per_line * y + intercept
        except Exception:
            return None

    def _auto_detect_camera_delay(self, calculated_ms):
        """Compare Tangra CSV acquisition_delay with calculated_ms, auto-select camera radio."""
        if not hasattr(self, '_lbl_csv_delay'):
            return
        if self._ts_summary is None:
            self._lbl_csv_delay.Text = '\u2014'
            self._lbl_csv_delay.ForeColor = Color.Gray
            return
        csv_delay = self._ts_summary.get('acquisition_delay')  # ms, float or None
        if csv_delay is None:
            self._lbl_csv_delay.Text = 'not present in CSV'
            self._lbl_csv_delay.ForeColor = Color.Gray
            if calculated_ms is not None:
                if not (self._rad_corrections_applied.Checked
                        or self._rad_corrections_not_applied.Checked
                        or self._rad_corrections_na.Checked):
                    self._rad_corrections_not_applied.Checked = True
            return
        csv_val = float(csv_delay)
        if calculated_ms is not None:
            diff = abs(csv_val - calculated_ms)
            if csv_val < 0.1:
                self._lbl_csv_delay.Text = '{0:.1f} ms (zero \u2014 not applied in Tangra)'.format(csv_val)
                self._lbl_csv_delay.ForeColor = Color.Gray
                if not self._correction_user_set:
                    self._suppress_correction_event = True
                    self._rad_corrections_not_applied.Checked = True
                    self._suppress_correction_event = False
            elif diff <= 5.0:
                self._lbl_csv_delay.Text = '{0:.1f} ms \u2714 close match \u2014 delay was applied'.format(csv_val)
                self._lbl_csv_delay.ForeColor = Color.Green
                if not self._correction_user_set:
                    self._suppress_correction_event = True
                    self._rad_corrections_applied.Checked = True
                    self._suppress_correction_event = False
            else:
                self._lbl_csv_delay.Text = (
                    '{0:.1f} ms  \u26a0 differs from calculated by {1:.1f} ms \u2014 verify'.format(
                        csv_val, diff))
                self._lbl_csv_delay.ForeColor = Color.OrangeRed
        else:
            self._lbl_csv_delay.Text = '{0:.1f} ms'.format(csv_val)
            self._lbl_csv_delay.ForeColor = Color.Gray

    def _update_timing_net_preview(self):
        """Recompute net correction and update the D/R preview labels in \u00a75 Timing."""
        if not hasattr(self, '_lbl_net_correction'):
            return
        if not self._rad_timing_ntp.Checked:
            self._lbl_net_correction.Text = '\u2014'
            self._lbl_d_preview.Text = ''
            self._lbl_r_preview.Text = ''
            return
        not_yet = self._rad_corrections_not_applied.Checked
        delay_ms = self._calculate_camera_delay()
        if not_yet:
            cam_ms = delay_ms if delay_ms is not None else 0.0
            ntp_ms = self._ntp_offset_ms
        elif self._rad_corrections_applied.Checked or self._rad_corrections_na.Checked:
            cam_ms = 0.0
            ntp_ms = 0.0
        else:
            cam_ms = None
            ntp_ms = None
        if cam_ms is None or ntp_ms is None:
            self._lbl_net_correction.Text = '(select a correction option above)'
            self._lbl_net_correction.ForeColor = Color.Gray
            self._lbl_d_preview.Text = ''
            self._lbl_r_preview.Text = ''
            self._update_guidance_values()
            return
        net_ms = cam_ms + ntp_ms
        preview_color = Color.SteelBlue if not_yet else Color.DarkOrange
        if abs(net_ms) < 0.05:
            self._lbl_net_correction.Text = '0.0 ms (no correction needed)' if not_yet else '0.0 ms (all corrections already applied)'
            self._lbl_net_correction.ForeColor = Color.Gray
        else:
            if not_yet:
                self._lbl_net_correction.Text = '{0:+.1f} ms to apply in Tangra (reference)'.format(net_ms)
            else:
                self._lbl_net_correction.Text = '{0:+.1f} ms applied to D/R times'.format(net_ms)
            self._lbl_net_correction.ForeColor = preview_color
        # D/R preview
        from timing_utils import seconds_to_hms
        net_s = net_ms / 1000.0
        if self._d_time_seconds is not None:
            dh, dm, ds = seconds_to_hms(self._d_time_seconds)
            if abs(net_ms) >= 0.05:
                ndh, ndm, nds = seconds_to_hms(self._d_time_seconds + net_s)
                self._lbl_d_preview.Text = 'D  {0}:{1:02d}:{2:06.3f}  \u2192  {3}:{4:02d}:{5:06.3f}'.format(
                    dh, dm, ds, ndh, ndm, nds)
                self._lbl_d_preview.ForeColor = preview_color
            else:
                self._lbl_d_preview.Text = 'D  {0}:{1:02d}:{2:06.3f}'.format(dh, dm, ds)
                self._lbl_d_preview.ForeColor = Color.Gray
        else:
            self._lbl_d_preview.Text = ''
        if self._r_time_seconds is not None:
            rh, rm, rs = seconds_to_hms(self._r_time_seconds)
            if abs(net_ms) >= 0.05:
                nrh, nrm, nrs = seconds_to_hms(self._r_time_seconds + net_s)
                self._lbl_r_preview.Text = 'R  {0}:{1:02d}:{2:06.3f}  \u2192  {3}:{4:02d}:{5:06.3f}'.format(
                    rh, rm, rs, nrh, nrm, nrs)
                self._lbl_r_preview.ForeColor = preview_color
            else:
                self._lbl_r_preview.Text = 'R  {0}:{1:02d}:{2:06.3f}'.format(rh, rm, rs)
                self._lbl_r_preview.ForeColor = Color.Gray
        else:
            self._lbl_r_preview.Text = ''
        self._update_guidance_values()


class VTIDoubleCorrectConfirmDialog(Form):
    """Confirmation dialog for the dangerous Analog+VTI + AOTA + NA combination.

    The IOTA NA form applies VTI corrections automatically.  If the user also
    applied corrections inside AOTA, the D/R times will be double-corrected.
    This dialog requires three explicit acknowledgements before proceeding.
    """

    def __init__(self, theme_manager=None):
        Form.__init__(self)
        self.confirmed = False
        self.Text = "VTI Correction Risk \u2014 Action Required"
        self.Size = Size(600, 390)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        self._setup_ui()
        if theme_manager:
            apply_theme_to_control(self, theme_manager.get_current_theme())

    def _setup_ui(self):
        y = 15

        lbl_heading = Label()
        lbl_heading.Text = "\u26a0  Double-Correction Risk"
        lbl_heading.Font = Font(lbl_heading.Font.FontFamily, 13, FontStyle.Bold)
        lbl_heading.ForeColor = Color.DarkRed
        lbl_heading.Location = Point(20, y)
        lbl_heading.Size = Size(560, 28)
        self.Controls.Add(lbl_heading)
        y += 38

        lbl_combo = Label()
        lbl_combo.Text = (
            "Selected combination:  "
            "Analog video + VTI  \u2022  AOTA analysis  \u2022  IOTA North America report"
        )
        lbl_combo.Location = Point(20, y)
        lbl_combo.Size = Size(560, 20)
        self.Controls.Add(lbl_combo)
        y += 30

        lbl_explain = Label()
        lbl_explain.Text = (
            "The IOTA North America form AUTOMATICALLY applies VTI corrections\n"
            "to your D/R times during report generation.\n\n"
            "If VTI or camera-delay corrections were also applied inside AOTA,\n"
            "your times will be DOUBLE-CORRECTED and the timing will be WRONG."
        )
        lbl_explain.ForeColor = Color.DarkRed
        lbl_explain.Location = Point(20, y)
        lbl_explain.Size = Size(560, 90)
        self.Controls.Add(lbl_explain)
        y += 100

        lbl_confirm = Label()
        lbl_confirm.Text = "Confirm ALL of the following before continuing:"
        lbl_confirm.Font = Font(lbl_confirm.Font.FontFamily, lbl_confirm.Font.Size, FontStyle.Bold)
        lbl_confirm.Location = Point(20, y)
        lbl_confirm.Size = Size(560, 20)
        self.Controls.Add(lbl_confirm)
        y += 28

        self._cb1 = CheckBox()
        self._cb1.Text = "I did NOT enter a camera delay correction in AOTA"
        self._cb1.Location = Point(30, y)
        self._cb1.Size = Size(545, 22)
        self._cb1.CheckedChanged += self._on_check_changed
        self.Controls.Add(self._cb1)
        y += 28

        self._cb2 = CheckBox()
        self._cb2.Text = "I did NOT apply VTI delay corrections inside AOTA"
        self._cb2.Location = Point(30, y)
        self._cb2.Size = Size(545, 22)
        self._cb2.CheckedChanged += self._on_check_changed
        self.Controls.Add(self._cb2)
        y += 28

        self._cb3 = CheckBox()
        self._cb3.Text = "The D/R times in my AOTA file are raw, uncorrected times"
        self._cb3.Location = Point(30, y)
        self._cb3.Size = Size(545, 22)
        self._cb3.CheckedChanged += self._on_check_changed
        self.Controls.Add(self._cb3)
        y += 42

        self._btn_ok = Button()
        self._btn_ok.Text = "Continue"
        self._btn_ok.Location = Point(395, y)
        self._btn_ok.Size = Size(90, 30)
        self._btn_ok.Enabled = False
        self._btn_ok.Click += self._on_ok
        self.Controls.Add(self._btn_ok)
        self.AcceptButton = self._btn_ok

        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(495, y)
        btn_cancel.Size = Size(90, 30)
        btn_cancel.Click += self._on_cancel
        self.Controls.Add(btn_cancel)
        self.CancelButton = btn_cancel

    def _on_check_changed(self, sender, e):
        self._btn_ok.Enabled = (
            self._cb1.Checked and self._cb2.Checked and self._cb3.Checked
        )

    def _on_ok(self, sender, e):
        self.confirmed = True
        self.DialogResult = DialogResult.OK
        self.Close()

    def _on_cancel(self, sender, e):
        self.confirmed = False
        self.DialogResult = DialogResult.Cancel
        self.Close()


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

