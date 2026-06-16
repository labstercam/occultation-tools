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
from System.Drawing import Point, Size, Color, Font, FontStyle, Image
from System.Windows.Forms import (
    Form, Button, Label, ListBox, Panel, TextBox, GroupBox, RadioButton, ComboBox,
    CheckBox, Clipboard, AnchorStyles, DockStyle, Padding, DialogResult,
    FormStartPosition, MessageBox, MessageBoxButtons, MessageBoxIcon,
    FolderBrowserDialog, SelectionMode, ComboBoxStyle, ToolTip,
    PictureBox, PictureBoxSizeMode
)
from theme import apply_theme_to_control


class _ComboProxy(object):
    """Lightweight proxy that mimics a read-only ComboBox for equipment lookups."""
    def __init__(self, index, count):
        self.SelectedIndex = index
        self.Enabled = (index >= 0 and count > 0)


class _RadioProxy(object):
    """Lightweight proxy that mimics a RadioButton.Checked for report type."""
    def __init__(self, checked):
        self.Checked = checked


class ComprehensiveReportDialog(Form):
    """Single comprehensive dialog for all report generation settings"""
    
    def __init__(self, config, theme_manager, event, telescope_id=None, camera_id=None,
                 report_type=None, ntp_context=None):
        """Initialize the comprehensive dialog
        
        Args:
            config: ConfigManager instance
            theme_manager: Theme manager for consistent styling
            event: Event object for display
            telescope_id: Pre-selected telescope ID from Dialog 1
            camera_id: Pre-selected camera ID from Dialog 1
            report_type: Pre-selected report type from Dialog 1
            ntp_context: NTP module context dict passed from main_gui
        """
        Form.__init__(self)
        self.config = config
        self.theme_manager = theme_manager
        self.event = event
        self._init_telescope_id = telescope_id
        self._init_camera_id = camera_id
        self._init_report_type = report_type
        self.ntp_context = ntp_context or {}
        
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
        self._ntp_gui_form = None          # reference to open AnalyzerForm, if any
        self._last_cam_id = None          # guards _init_timing_section from spurious fires
        self._correction_user_set = False # True once user explicitly clicks a correction radio
        self._suppress_correction_event = False  # True during programmatic radio changes

        # NTP Analyser state (§2)
        self._ntp_stats_folder = None
        self._ntp_loopstats_path = None
        self._ntp_peerstats_path = None
        self._ntp_analysis_result_loc = None  # from §2 NTP Analyser panel

        self.setup_ui()

        # Build equipment + report-type proxies from values passed by Dialog 1.
        # These proxy objects let existing code (update_button_state, generate_click, etc.)
        # continue reading .SelectedIndex, .Enabled, .Checked without modification.
        self._rebuild_equipment_proxies(
            self._init_telescope_id, self._init_camera_id, self._init_report_type
        )
        
        # Load saved preferences
        self.load_preferences()
        
        # Update button state after loading preferences
        self.update_button_state()
        
        # Apply theme
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)

        # Re-apply custom timing guidance colors after theming.
        self._apply_tangra_guidance_colors()

    def _apply_tangra_guidance_colors(self):
        """Set readable Step A1-A4 colors for both day and night themes."""
        is_night = bool(getattr(self.theme_manager, 'is_night_mode', False))

        if hasattr(self, '_pnl_step_a3'):
            self._pnl_step_a3.BackColor = Color.FromArgb(26, 20, 14) if is_night else Color.LightYellow
        if hasattr(self, '_pnl_step_a4'):
            self._pnl_step_a4.BackColor = Color.FromArgb(22, 17, 12) if is_night else Color.FromArgb(240, 255, 240)
        if hasattr(self, '_pnl_gps_manual_delay'):
            self._pnl_gps_manual_delay.BackColor = Color.FromArgb(28, 22, 16) if is_night else Color.FromArgb(235, 244, 255)

        # Labels explicitly set to gray become hard to read in night mode.
        if hasattr(self, '_lbl_calib_match'):
            self._lbl_calib_match.ForeColor = Color.FromArgb(255, 214, 150) if is_night else Color.Gray
        if hasattr(self, '_lbl_gps_delay_hint'):
            self._lbl_gps_delay_hint.ForeColor = Color.FromArgb(255, 214, 150) if is_night else Color.Gray
        if hasattr(self, 'lbl_ntp_analysing'):
            self.lbl_ntp_analysing.ForeColor = Color.FromArgb(255, 214, 150) if is_night else Color.Gray
        if hasattr(self, 'lbl_ntp_offset_loc'):
            self.lbl_ntp_offset_loc.ForeColor = Color.FromArgb(255, 214, 150) if is_night else Color.Gray
        if hasattr(self, 'lbl_ntp_uncertainty_loc'):
            self.lbl_ntp_uncertainty_loc.ForeColor = Color.FromArgb(255, 214, 150) if is_night else Color.Gray
        if hasattr(self, 'lbl_ntp_age_loc'):
            self.lbl_ntp_age_loc.ForeColor = Color.FromArgb(255, 214, 150) if is_night else Color.Gray
        if hasattr(self, 'lbl_ntp_server_loc'):
            self.lbl_ntp_server_loc.ForeColor = Color.FromArgb(255, 214, 150) if is_night else Color.Gray
        if hasattr(self, '_lbl_a3_instr'):
            self._lbl_a3_instr.ForeColor = Color.FromArgb(255, 214, 150) if is_night else Color.Gray
        if hasattr(self, '_lbl_total_delay'):
            self._lbl_total_delay.ForeColor = Color.FromArgb(255, 236, 185) if is_night else Color.Gray
        if hasattr(self, '_lbl_a4_csv_prefix'):
            self._lbl_a4_csv_prefix.ForeColor = Color.FromArgb(255, 214, 150) if is_night else Color.Gray
        if hasattr(self, '_lbl_csv_delay'):
            self._lbl_csv_delay.ForeColor = Color.FromArgb(255, 214, 150) if is_night else Color.Gray

    def _status_color(self, kind):
        """Return report-flow status colors tuned for day/night readability."""
        is_night = bool(getattr(self.theme_manager, 'is_night_mode', False))
        if is_night:
            colors = {
                'muted': Color.FromArgb(255, 214, 150),
                'info': Color.FromArgb(255, 214, 150),
                'warning': Color.FromArgb(255, 190, 90),
                'success': Color.FromArgb(180, 255, 160),
                'error': Color.FromArgb(255, 170, 150),
            }
        else:
            colors = {
                'muted': Color.Gray,
                'info': Color.Gray,
                'warning': Color.Orange,
                'success': Color.Green,
                'error': Color.Red,
            }
        return colors.get(kind, colors['info'])
    
    def setup_ui(self):
        """Setup user interface"""
        self.Text = "Generate Report"
        self.Size = Size(1000, 920)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        # Main scroll panel
        main_panel = Panel()
        main_panel.Location = Point(10, 10)
        main_panel.Size = Size(970, 770)
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

        # ===== SECTION 1: OBSERVATION FILES FOLDER (picker only) =====
        grp_folder = GroupBox()
        grp_folder.Text = "1. Observation Files Folder"
        grp_folder.Location = Point(10, y_pos)
        grp_folder.Size = Size(940, 70)
        main_panel.Controls.Add(grp_folder)

        lbl_folder_info = Label()
        lbl_folder_info.Text = "Observation files folder:"
        lbl_folder_info.Location = Point(15, 22)
        lbl_folder_info.Size = Size(160, 20)
        grp_folder.Controls.Add(lbl_folder_info)

        self.folder_textbox = TextBox()
        self.folder_textbox.Location = Point(180, 20)
        self.folder_textbox.Size = Size(620, 25)
        self.folder_textbox.ReadOnly = True
        grp_folder.Controls.Add(self.folder_textbox)

        btn_browse = Button()
        btn_browse.Text = "Browse..."
        btn_browse.Location = Point(810, 18)
        btn_browse.Size = Size(100, 28)
        btn_browse.Click += self.browse_folder_click
        grp_folder.Controls.Add(btn_browse)

        self._lbl_file_status = Label()
        self._lbl_file_status.Text = "No folder selected"
        self._lbl_file_status.Location = Point(180, 47)
        self._lbl_file_status.Size = Size(730, 18)
        self._lbl_file_status.ForeColor = self._status_color('muted')
        grp_folder.Controls.Add(self._lbl_file_status)

        y_pos += 80

        # ===== SECTION 2: TIMING METHOD =====
        grp_timing_method = GroupBox()
        grp_timing_method.Text = "2. Timing Method"
        grp_timing_method.Location = Point(10, y_pos)
        grp_timing_method.Size = Size(940, 72)
        main_panel.Controls.Add(grp_timing_method)

        self._rad_timing_ntp = RadioButton()
        self._rad_timing_ntp.Text = "NTP / GPS-disciplined clock"
        self._rad_timing_ntp.Location = Point(15, 22)
        self._rad_timing_ntp.Size = Size(220, 22)
        self._rad_timing_ntp.CheckedChanged += self._on_timing_method_changed
        grp_timing_method.Controls.Add(self._rad_timing_ntp)

        self._rad_timing_gps = RadioButton()
        self._rad_timing_gps.Text = "GPS flash overlay (dumb)"
        self._rad_timing_gps.Location = Point(245, 22)
        self._rad_timing_gps.Size = Size(205, 22)
        self._rad_timing_gps.CheckedChanged += self._on_timing_method_changed
        grp_timing_method.Controls.Add(self._rad_timing_gps)

        self._rad_timing_gps_cmos = RadioButton()
        self._rad_timing_gps_cmos.Text = "GPS-integrated CMOS camera"
        self._rad_timing_gps_cmos.Location = Point(15, 47)
        self._rad_timing_gps_cmos.Size = Size(230, 22)
        self._rad_timing_gps_cmos.CheckedChanged += self._on_timing_method_changed
        grp_timing_method.Controls.Add(self._rad_timing_gps_cmos)

        self._rad_timing_analog_vti = RadioButton()
        self._rad_timing_analog_vti.Text = "Analog video + VTI"
        self._rad_timing_analog_vti.Location = Point(255, 47)
        self._rad_timing_analog_vti.Size = Size(185, 22)
        self._rad_timing_analog_vti.CheckedChanged += self._on_timing_method_changed
        grp_timing_method.Controls.Add(self._rad_timing_analog_vti)

        self._rad_timing_other = RadioButton()
        self._rad_timing_other.Text = "Other"
        self._rad_timing_other.Location = Point(450, 47)
        self._rad_timing_other.Size = Size(80, 22)
        self._rad_timing_other.Checked = True
        self._rad_timing_other.CheckedChanged += self._on_timing_method_changed
        grp_timing_method.Controls.Add(self._rad_timing_other)

        y_pos += 82

        # ===== PHASE A: PREPARE FOR TANGRA (NTP/GPS-disciplined and GPS Flash only) =====
        # This panel is shown only for timing methods that require corrections entered into Tangra.
        self._pnl_phase_a = Panel()
        self._pnl_phase_a.Location = Point(10, y_pos)
        self._pnl_phase_a.Size = Size(940, 516)
        self._pnl_phase_a.BackColor = Color.FromArgb(235, 244, 255)  # light blue tint
        self._pnl_phase_a.Visible = False
        main_panel.Controls.Add(self._pnl_phase_a)

        lbl_phase_a_head = Label()
        lbl_phase_a_head.Text = "\u25b6  Phase A \u2014 Complete these steps to calculate time corrections for TANGRA"
        lbl_phase_a_head.Font = Font(lbl_phase_a_head.Font.FontFamily, lbl_phase_a_head.Font.Size, FontStyle.Bold)
        lbl_phase_a_head.Location = Point(8, 8)
        lbl_phase_a_head.Size = Size(900, 18)
        self._pnl_phase_a.Controls.Add(lbl_phase_a_head)

        # --- Camera acquisition delay sub-section ---
        lbl_cam_section = Label()
        lbl_cam_section.Text = "Step A1 \u2014 Camera acquisition delay"
        lbl_cam_section.Font = Font(lbl_cam_section.Font.FontFamily, lbl_cam_section.Font.Size, FontStyle.Bold)
        lbl_cam_section.Location = Point(8, 34)
        lbl_cam_section.Size = Size(350, 18)
        self._pnl_phase_a.Controls.Add(lbl_cam_section)

        self._btn_ntp_info = Button()
        self._btn_ntp_info.Text = "\u24d8  Timing correction help"
        self._btn_ntp_info.Location = Point(680, 32)
        self._btn_ntp_info.Size = Size(195, 26)
        self._btn_ntp_info.Click += self._on_ntp_info_click
        self._pnl_phase_a.Controls.Add(self._btn_ntp_info)

        self._lbl_calib_run = Label()
        self._lbl_calib_run.Text = "Calibration run:"
        self._lbl_calib_run.Location = Point(8, 58)
        self._lbl_calib_run.Size = Size(110, 22)
        self._pnl_phase_a.Controls.Add(self._lbl_calib_run)

        self._combo_calib_run = ComboBox()
        self._combo_calib_run.Location = Point(120, 56)
        self._combo_calib_run.Size = Size(356, 22)
        self._combo_calib_run.DropDownStyle = ComboBoxStyle.DropDownList
        self._combo_calib_run.SelectedIndexChanged += self._on_calib_run_changed
        self._pnl_phase_a.Controls.Add(self._combo_calib_run)

        self._btn_calib_info = Button()
        self._btn_calib_info.Text = "?"
        self._btn_calib_info.Location = Point(479, 56)
        self._btn_calib_info.Size = Size(24, 26)
        self._btn_calib_info.Click += self._on_calib_info_click
        self._pnl_phase_a.Controls.Add(self._btn_calib_info)

        self._lbl_calib_match = Label()
        self._lbl_calib_match.Text = ""
        self._lbl_calib_match.Location = Point(516, 54)
        self._lbl_calib_match.Size = Size(360, 34)
        self._lbl_calib_match.AutoSize = False
        self._lbl_calib_match.ForeColor = Color.Gray
        self._pnl_phase_a.Controls.Add(self._lbl_calib_match)

        self._lbl_y_line = Label()
        self._lbl_y_line.Text = "Y line:"
        self._lbl_y_line.Location = Point(8, 84)
        self._lbl_y_line.Size = Size(55, 22)
        self._pnl_phase_a.Controls.Add(self._lbl_y_line)

        self._txt_y_line = TextBox()
        self._txt_y_line.Location = Point(66, 82)
        self._txt_y_line.Size = Size(70, 22)
        self._txt_y_line.Text = ""
        self._txt_y_line.TextChanged += self._on_y_line_changed
        self._pnl_phase_a.Controls.Add(self._txt_y_line)

        self._btn_y_line_info = Button()
        self._btn_y_line_info.Text = "?"
        self._btn_y_line_info.Location = Point(139, 82)
        self._btn_y_line_info.Size = Size(24, 26)
        self._btn_y_line_info.Click += self._on_y_line_info_click
        self._pnl_phase_a.Controls.Add(self._btn_y_line_info)

        self._lbl_calc_label = Label()
        self._lbl_calc_label.Text = "Calculated delay:"
        self._lbl_calc_label.Location = Point(167, 84)
        self._lbl_calc_label.Size = Size(128, 22)
        self._pnl_phase_a.Controls.Add(self._lbl_calc_label)

        self._lbl_calc_delay = Label()
        self._lbl_calc_delay.Text = "\u2014"
        self._lbl_calc_delay.Location = Point(299, 84)
        self._lbl_calc_delay.Size = Size(200, 22)
        self._pnl_phase_a.Controls.Add(self._lbl_calc_delay)

        # GPS flash (dumb) Step A1: manual camera delay entry panel.
        # Visible only for GPS flash method; overlays calibration/Y-line controls.
        self._pnl_gps_manual_delay = Panel()
        self._pnl_gps_manual_delay.Location = Point(0, 56)
        self._pnl_gps_manual_delay.Size = Size(930, 52)
        self._pnl_gps_manual_delay.BackColor = Color.FromArgb(235, 244, 255)
        self._pnl_gps_manual_delay.Visible = False
        self._pnl_phase_a.Controls.Add(self._pnl_gps_manual_delay)

        self._lbl_gps_delay = Label()
        self._lbl_gps_delay.Text = "Camera Acquisition Delay (ms):"
        self._lbl_gps_delay.Location = Point(8, 4)
        self._lbl_gps_delay.Size = Size(230, 22)
        self._pnl_gps_manual_delay.Controls.Add(self._lbl_gps_delay)

        self._txt_gps_delay = TextBox()
        self._txt_gps_delay.Location = Point(242, 2)
        self._txt_gps_delay.Size = Size(90, 22)
        self._txt_gps_delay.TextChanged += self._on_gps_delay_changed
        self._pnl_gps_manual_delay.Controls.Add(self._txt_gps_delay)

        self._lbl_gps_delay_hint = Label()
        self._lbl_gps_delay_hint.Text = "Enter measured camera delay to 1 decimal place (e.g., 5.3 or -5.3)"
        self._lbl_gps_delay_hint.Location = Point(8, 28)
        self._lbl_gps_delay_hint.Size = Size(700, 20)
        self._lbl_gps_delay_hint.ForeColor = Color.Gray
        self._pnl_gps_manual_delay.Controls.Add(self._lbl_gps_delay_hint)

        # --- NTP analysis sub-section (hidden for GPS Flash) ---
        self._pnl_ntp_analyse = Panel()
        self._pnl_ntp_analyse.Location = Point(0, 108)
        self._pnl_ntp_analyse.Size = Size(940, 124)
        self._pnl_ntp_analyse.Visible = True  # shown for NTP method; hidden for GPS Flash
        self._pnl_phase_a.Controls.Add(self._pnl_ntp_analyse)

        lbl_step_a2 = Label()
        lbl_step_a2.Text = "Step A2 \u2014 NTP Analysis"
        lbl_step_a2.Font = Font(lbl_step_a2.Font.FontFamily, lbl_step_a2.Font.Size, FontStyle.Bold)
        lbl_step_a2.Location = Point(8, 0)
        lbl_step_a2.Size = Size(260, 18)
        self._pnl_ntp_analyse.Controls.Add(lbl_step_a2)

        lbl_ntp_folder = Label()
        lbl_ntp_folder.Text = "NTP stats folder:"
        lbl_ntp_folder.Location = Point(8, 22)
        lbl_ntp_folder.Size = Size(155, 20)
        self._pnl_ntp_analyse.Controls.Add(lbl_ntp_folder)

        self.txt_ntp_stats_folder = TextBox()
        self.txt_ntp_stats_folder.Location = Point(163, 20)
        self.txt_ntp_stats_folder.Size = Size(280, 22)
        self._pnl_ntp_analyse.Controls.Add(self.txt_ntp_stats_folder)

        btn_ntp_folder_browse = Button()
        btn_ntp_folder_browse.Text = "Browse..."
        btn_ntp_folder_browse.Location = Point(451, 18)
        btn_ntp_folder_browse.Size = Size(100, 28)
        btn_ntp_folder_browse.Click += self._browse_ntp_folder_click
        self._pnl_ntp_analyse.Controls.Add(btn_ntp_folder_browse)

        btn_analyse_ntp = Button()
        btn_analyse_ntp.Text = "Analyse NTP"
        btn_analyse_ntp.Location = Point(8, 50)
        btn_analyse_ntp.Size = Size(115, 26)
        btn_analyse_ntp.Click += self._analyse_ntp_click
        self._pnl_ntp_analyse.Controls.Add(btn_analyse_ntp)

        self.lbl_ntp_analysing = Label()
        self.lbl_ntp_analysing.Text = ""
        self.lbl_ntp_analysing.Location = Point(132, 54)
        self.lbl_ntp_analysing.Size = Size(400, 18)
        self.lbl_ntp_analysing.ForeColor = Color.Gray
        self._pnl_ntp_analyse.Controls.Add(self.lbl_ntp_analysing)

        btn_open_ntp = Button()
        btn_open_ntp.Text = "Open NTP Analyser"
        btn_open_ntp.Location = Point(740, 50)
        btn_open_ntp.Size = Size(150, 26)
        btn_open_ntp.Click += self._on_open_ntp_analyser_location_click
        self._pnl_ntp_analyse.Controls.Add(btn_open_ntp)

        _ntp_results_font = Font("Microsoft Sans Serif", 9)

        self.lbl_ntp_offset_loc = Label()
        self.lbl_ntp_offset_loc.Text = "Offset: -"
        self.lbl_ntp_offset_loc.Location = Point(8, 78)
        self.lbl_ntp_offset_loc.Size = Size(200, 20)
        self.lbl_ntp_offset_loc.Font = _ntp_results_font
        self.lbl_ntp_offset_loc.ForeColor = Color.Gray
        self._pnl_ntp_analyse.Controls.Add(self.lbl_ntp_offset_loc)

        self.lbl_ntp_uncertainty_loc = Label()
        self.lbl_ntp_uncertainty_loc.Text = "Uncertainty: -"
        self.lbl_ntp_uncertainty_loc.Location = Point(218, 78)
        self.lbl_ntp_uncertainty_loc.Size = Size(220, 20)
        self.lbl_ntp_uncertainty_loc.Font = _ntp_results_font
        self.lbl_ntp_uncertainty_loc.ForeColor = Color.Gray
        self._pnl_ntp_analyse.Controls.Add(self.lbl_ntp_uncertainty_loc)

        self.lbl_ntp_age_loc = Label()
        self.lbl_ntp_age_loc.Text = "Data age: -"
        self.lbl_ntp_age_loc.Location = Point(448, 78)
        self.lbl_ntp_age_loc.Size = Size(200, 20)
        self.lbl_ntp_age_loc.Font = _ntp_results_font
        self.lbl_ntp_age_loc.ForeColor = Color.Gray
        self._pnl_ntp_analyse.Controls.Add(self.lbl_ntp_age_loc)

        self.lbl_ntp_server_loc = Label()
        self.lbl_ntp_server_loc.Text = "Server: -"
        self.lbl_ntp_server_loc.Location = Point(8, 100)
        self.lbl_ntp_server_loc.Size = Size(900, 20)
        self.lbl_ntp_server_loc.Font = _ntp_results_font
        self.lbl_ntp_server_loc.ForeColor = Color.Gray
        self._pnl_ntp_analyse.Controls.Add(self.lbl_ntp_server_loc)

        self._prefill_ntp_folder()

        # --- Step A3: Enter Total Delay in Tangra ---
        self._pnl_step_a3 = Panel()
        self._pnl_step_a3.Location = Point(0, 234)
        self._pnl_step_a3.Size = Size(940, 128)
        self._pnl_step_a3.BackColor = Color.LightYellow
        self._pnl_phase_a.Controls.Add(self._pnl_step_a3)

        lbl_a3_head = Label()
        lbl_a3_head.Text = "Step A3 \u2014 Enter Total Delay in Tangra"
        lbl_a3_head.Font = Font(lbl_a3_head.Font.FontFamily, lbl_a3_head.Font.Size, FontStyle.Bold)
        lbl_a3_head.Location = Point(8, 4)
        lbl_a3_head.Size = Size(500, 18)
        self._pnl_step_a3.Controls.Add(lbl_a3_head)

        self._lbl_a3_instr = Label()
        self._lbl_a3_instr.Text = (
            "\u270e  Open Tangra \u2192 Camera and Timing Corrections, enter the Total Delay "
            "in the Acquisition Delay field only. Leave Reference Time unchecked.")
        self._lbl_a3_instr.Location = Point(8, 24)
        self._lbl_a3_instr.Size = Size(920, 18)
        self._lbl_a3_instr.ForeColor = Color.Gray
        self._pnl_step_a3.Controls.Add(self._lbl_a3_instr)

        lbl_total_delay_prefix = Label()
        lbl_total_delay_prefix.Text = "Total Delay for TANGRA:"
        lbl_total_delay_prefix.Location = Point(8, 46)
        lbl_total_delay_prefix.Size = Size(198, 22)
        self._pnl_step_a3.Controls.Add(lbl_total_delay_prefix)

        self._lbl_total_delay = Label()
        self._lbl_total_delay.Text = "\u2014"
        self._lbl_total_delay.Font = Font(self._lbl_total_delay.Font.FontFamily,
                                          self._lbl_total_delay.Font.Size, FontStyle.Bold)
        self._lbl_total_delay.ForeColor = Color.Gray
        self._lbl_total_delay.Location = Point(210, 46)
        self._lbl_total_delay.Size = Size(120, 22)
        self._pnl_step_a3.Controls.Add(self._lbl_total_delay)

        _btn_total_delay_info = Button()
        _btn_total_delay_info.Text = "\u24d8  How to enter in Tangra"
        _btn_total_delay_info.Location = Point(394, 44)
        _btn_total_delay_info.Size = Size(190, 28)
        _btn_total_delay_info.Click += self._on_total_delay_info_click
        self._pnl_step_a3.Controls.Add(_btn_total_delay_info)

        _tangra_img_path = os.path.join(
            self.config.get_templates_master_root(), 'images', 'tangra_delay_entry.png')
        self._pic_tangra = PictureBox()
        self._pic_tangra.SizeMode = PictureBoxSizeMode.StretchImage
        self._pic_tangra.Location = Point(594, 40)
        self._pic_tangra.Size = Size(334, 54)
        self._pic_tangra.BackColor = Color.White
        try:
            from System.Drawing import Bitmap
            self._pic_tangra.Image = Bitmap(_tangra_img_path)
        except Exception as _img_ex:
            _lbl_img_err = Label()
            _lbl_img_err.Text = 'img: ' + _tangra_img_path
            _lbl_img_err.Location = Point(538, 44)
            _lbl_img_err.Size = Size(390, 46)
            _lbl_img_err.ForeColor = Color.OrangeRed
            self._pnl_step_a3.Controls.Add(_lbl_img_err)
        self._pnl_step_a3.Controls.Add(self._pic_tangra)

        self._btn_copy_total_delay = Button()
        self._btn_copy_total_delay.Text = "Copy"
        self._btn_copy_total_delay.Location = Point(334, 44)
        self._btn_copy_total_delay.Size = Size(55, 26)
        self._btn_copy_total_delay.Click += self._on_copy_total_delay_click
        self._pnl_step_a3.Controls.Add(self._btn_copy_total_delay)

        # Individual delay labels — shown only when total delay is negative
        self._lbl_indiv_prefix = Label()
        self._lbl_indiv_prefix.Text = 'Total < 0 \u2014 enter delays separately in Tangra:'
        self._lbl_indiv_prefix.ForeColor = Color.OrangeRed
        self._lbl_indiv_prefix.Location = Point(8, 72)
        self._lbl_indiv_prefix.Size = Size(580, 18)
        self._lbl_indiv_prefix.Visible = False
        self._pnl_step_a3.Controls.Add(self._lbl_indiv_prefix)

        self._lbl_indiv_line1 = Label()
        self._lbl_indiv_line1.Text = ''
        self._lbl_indiv_line1.ForeColor = Color.DarkGreen
        self._lbl_indiv_line1.Location = Point(8, 92)
        self._lbl_indiv_line1.Size = Size(440, 18)
        self._lbl_indiv_line1.Visible = False
        self._pnl_step_a3.Controls.Add(self._lbl_indiv_line1)

        self._lbl_indiv_line2 = Label()
        self._lbl_indiv_line2.Text = ''
        self._lbl_indiv_line2.ForeColor = Color.DarkGreen
        self._lbl_indiv_line2.Location = Point(8, 110)
        self._lbl_indiv_line2.Size = Size(440, 18)
        self._lbl_indiv_line2.Visible = False
        self._pnl_step_a3.Controls.Add(self._lbl_indiv_line2)

        # --- Step A4: Confirm TANGRA delays applied ---
        self._pnl_step_a4 = Panel()
        self._pnl_step_a4.Location = Point(0, 370)
        self._pnl_step_a4.Size = Size(940, 140)
        self._pnl_step_a4.BackColor = Color.FromArgb(240, 255, 240)  # pale green tint
        self._pnl_phase_a.Controls.Add(self._pnl_step_a4)

        lbl_a4_head = Label()
        lbl_a4_head.Text = "Step A4 \u2014 Confirm TANGRA delays applied"
        lbl_a4_head.Font = Font(lbl_a4_head.Font.FontFamily, lbl_a4_head.Font.Size, FontStyle.Bold)
        lbl_a4_head.Location = Point(8, 4)
        lbl_a4_head.Size = Size(500, 18)
        self._pnl_step_a4.Controls.Add(lbl_a4_head)

        self._lbl_a4_csv_prefix = Label()
        self._lbl_a4_csv_prefix.Text = "Tangra CSV Acquisition Delay:"
        self._lbl_a4_csv_prefix.Location = Point(8, 26)
        self._lbl_a4_csv_prefix.Size = Size(210, 20)
        self._lbl_a4_csv_prefix.ForeColor = Color.Gray
        self._pnl_step_a4.Controls.Add(self._lbl_a4_csv_prefix)

        self._lbl_csv_delay = Label()
        self._lbl_csv_delay.Text = "Rescan folder to load the Tangra CSV acquisition delay"
        self._lbl_csv_delay.Location = Point(222, 26)
        self._lbl_csv_delay.Size = Size(540, 40)
        self._lbl_csv_delay.ForeColor = Color.Gray
        self._pnl_step_a4.Controls.Add(self._lbl_csv_delay)

        self._lbl_csv_note = Label()
        self._lbl_csv_note.Text = ''
        self._lbl_csv_note.Location = Point(8, 48)
        self._lbl_csv_note.Size = Size(900, 18)
        self._lbl_csv_note.ForeColor = Color.OrangeRed
        self._lbl_csv_note.Visible = False
        self._pnl_step_a4.Controls.Add(self._lbl_csv_note)

        self._btn_rescan_guidance = Button()
        self._btn_rescan_guidance.Text = "\u21bb  Rescan Folder"
        self._btn_rescan_guidance.Location = Point(772, 22)
        self._btn_rescan_guidance.Size = Size(135, 28)
        self._btn_rescan_guidance.Click += self._on_rescan_from_guidance_click
        self._pnl_step_a4.Controls.Add(self._btn_rescan_guidance)

        self._rad_corrections_applied = RadioButton()
        self._rad_corrections_applied.Text = "Applied \u2014 I have entered the delays into Tangra\u2019s Acquisition Delay field"
        self._rad_corrections_applied.Location = Point(8, 70)
        self._rad_corrections_applied.Size = Size(910, 22)
        self._rad_corrections_applied.CheckedChanged += self._on_timing_radio_changed
        self._rad_corrections_applied.Enabled = False
        self._pnl_step_a4.Controls.Add(self._rad_corrections_applied)

        self._pnl_applied_confirm = Panel()
        self._pnl_applied_confirm.Location = Point(28, 92)
        self._pnl_applied_confirm.Size = Size(900, 22)
        self._pnl_applied_confirm.Visible = True
        self._pnl_step_a4.Controls.Add(self._pnl_applied_confirm)

        self._chk_confirm_total_delay = CheckBox()
        self._chk_confirm_total_delay.Text = "Total Delay for TANGRA: \u2014  (tick to confirm value is correctly entered)"
        self._chk_confirm_total_delay.Location = Point(0, 0)
        self._chk_confirm_total_delay.Size = Size(880, 20)
        self._chk_confirm_total_delay.CheckedChanged += self._on_confirm_check_changed
        self._pnl_applied_confirm.Controls.Add(self._chk_confirm_total_delay)

        self._rad_corrections_not_applied = RadioButton()
        self._rad_corrections_not_applied.Text = "Not yet applied \u2014 I need to enter the delays in Tangra before generating the light curve"
        self._rad_corrections_not_applied.Location = Point(8, 114)
        self._rad_corrections_not_applied.Size = Size(910, 22)
        self._rad_corrections_not_applied.Checked = True
        self._rad_corrections_not_applied.CheckedChanged += self._on_timing_radio_changed
        self._pnl_step_a4.Controls.Add(self._rad_corrections_not_applied)

        y_pos += 526  # Phase A height (516) + 10px gap

        # ===== BOTTOM BUTTONS (D2 — "Next →") =====
        self.status_label = Label()
        self.status_label.Text = "Please complete all sections above"
        self.status_label.Location = Point(20, 790)
        self.status_label.Size = Size(700, 20)
        self.status_label.ForeColor = self._status_color('muted')
        self.Controls.Add(self.status_label)

        self._btn_why_blocked = Button()
        self._btn_why_blocked.Text = "?"
        self._btn_why_blocked.Location = Point(723, 789)
        self._btn_why_blocked.Size = Size(24, 26)
        self._btn_why_blocked.Click += self._on_why_blocked_click
        self.Controls.Add(self._btn_why_blocked)

        self._btn_next = Button()
        self._btn_next.Text = "Next  \u2192"
        self._btn_next.Location = Point(750, 785)
        self._btn_next.Size = Size(140, 35)
        self._btn_next.Enabled = False
        self._btn_next.Click += self._next_click
        self.Controls.Add(self._btn_next)
        self.AcceptButton = self._btn_next

        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(900, 785)
        btn_cancel.Size = Size(80, 35)
        btn_cancel.Click += self.cancel_click
        self.Controls.Add(btn_cancel)
        self.CancelButton = btn_cancel

        self._setup_tooltips()

    def load_preferences(self):
        """Load saved preferences and populate fields.
        Equipment and report type come pre-selected from Dialog 1; only load folder."""
        # Try to browse to last folder's parent
        last_folder = self.config.get_last_report_folder()
        if last_folder and os.path.exists(last_folder):
            # Don't auto-scan yet, just remember for browse dialog
            self.remembered_folder = last_folder
        else:
            self.remembered_folder = None

        # Pre-select timing method from camera config
        self._init_timing_section()
    
    def _rebuild_equipment_proxies(self, telescope_id, camera_id, report_type):
        """Build proxy objects from pre-selected Dialog 1 values.
        Allows existing code referencing combo_telescope/camera/rb_na/tt/sodis to continue working."""
        telescopes = self.config.get_telescopes()
        cameras = self.config.get_cameras()

        # Find index of selected telescope
        tel_idx = -1
        for i, t in enumerate(telescopes):
            if t.get('id') == telescope_id:
                tel_idx = i
                break
        if tel_idx < 0 and telescopes:
            # Fall back to active telescope
            active = self.config.get_active_telescope()
            active_id = active.get('id') if active else None
            for i, t in enumerate(telescopes):
                if t.get('id') == active_id:
                    tel_idx = i
                    break
            if tel_idx < 0:
                tel_idx = 0

        # Find index of selected camera
        cam_idx = -1
        for i, c in enumerate(cameras):
            if c.get('id') == camera_id:
                cam_idx = i
                break
        if cam_idx < 0 and cameras:
            active = self.config.get_active_camera()
            active_id = active.get('id') if active else None
            for i, c in enumerate(cameras):
                if c.get('id') == active_id:
                    cam_idx = i
                    break
            if cam_idx < 0:
                cam_idx = 0

        self.combo_telescope = _ComboProxy(tel_idx, len(telescopes))
        self.combo_camera = _ComboProxy(cam_idx, len(cameras))

        rt = report_type or 'north_america'
        self.rb_na = _RadioProxy(rt == 'north_america')
        self.rb_tt = _RadioProxy(rt == 'trans_tasman')
        self.rb_sodis = _RadioProxy(rt == 'sodis')

        # Cache camera id for _init_timing_section
        if 0 <= cam_idx < len(cameras):
            self._last_cam_id = cameras[cam_idx].get('id')

    def load_equipment(self):
        """No-op: equipment was selected in Dialog 1."""
        pass

    def manage_telescopes_click(self, sender, e):
        """No-op: equipment is managed from the Settings dialog."""
        pass

    def manage_cameras_click(self, sender, e):
        """No-op: equipment is managed from the Settings dialog."""
        pass

    def report_type_changed(self, sender, e):
        """No-op: report type was selected in Dialog 1."""
        pass

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
            
            # Store folder; D3 (PhaseBDialog) will scan it when opened via _next_click
            self._update_file_status_labels()
            self.update_button_state()

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
                self.lbl_ts_delayed.ForeColor = self._status_color('error')
                self.lbl_ts_late.ForeColor = self._status_color('error')
                self.lbl_ts_status.Text = "Status: Issues detected"
                self.lbl_ts_status.ForeColor = self._status_color('error')
            elif n_delayed > 0:
                self.lbl_ts_delayed.ForeColor = self._status_color('warning')
                self.lbl_ts_late.ForeColor = self._status_color('muted')
                self.lbl_ts_status.Text = "Status: Check"
                self.lbl_ts_status.ForeColor = self._status_color('warning')
            else:
                self.lbl_ts_delayed.ForeColor = self._status_color('muted')
                self.lbl_ts_late.ForeColor = self._status_color('muted')
                self.lbl_ts_status.Text = "Status: OK"
                self.lbl_ts_status.ForeColor = self._status_color('success')
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
            self.lbl_ts_minmax.ForeColor = self._status_color('muted')
            self._check_event_in_window(summary)
            delay_ms = self._calculate_camera_delay()
            self._auto_detect_camera_delay(delay_ms)
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
        if hasattr(self, '_rad_corrections_applied'):
            self._rad_corrections_applied.Enabled = False
        if hasattr(self, '_lbl_csv_delay'):
            self._lbl_csv_delay.Text = 'Rescan folder to load the Tangra CSV acquisition delay'
            self._lbl_csv_delay.ForeColor = Color.Gray
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
            form = TimestampInspectorForm(
                tangra_path,
                self._d_time_seconds,
                self._r_time_seconds,
                event_secs,
                theme_manager=self.theme_manager,
            )
            form.ShowDialog(self)
        except Exception as ex:
            MessageBox.Show(
                "Error opening Timestamp Inspector:\n\n" + str(ex),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )

    def update_button_state(self):
        """Update Next button state — blocks until timing is confirmed (or N/A)."""
        has_report_type = self.rb_na.Checked or self.rb_tt.Checked or self.rb_sodis.Checked

        has_telescope = self.combo_telescope.Enabled and self.combo_telescope.SelectedIndex >= 0
        has_camera = self.combo_camera.Enabled and self.combo_camera.SelectedIndex >= 0

        missing = []
        if not has_report_type:
            missing.append("report format")
        if not has_telescope:
            missing.append("telescope")
        if not has_camera:
            missing.append("camera")

        # Block if Tangra-correction methods are selected but corrections not yet applied in Tangra
        timing_requires_tangra = (
            (hasattr(self, '_rad_timing_ntp') and self._rad_timing_ntp.Checked)
            or (hasattr(self, '_rad_timing_gps') and self._rad_timing_gps.Checked)
        )
        if (timing_requires_tangra
                and hasattr(self, '_rad_corrections_not_applied')
                and self._rad_corrections_not_applied.Checked):
            missing.append("timing corrections \u2014 apply in Tangra first (see Phase A guidance)")

        # Block if Applied selected but confirmation checkbox not ticked
        if (timing_requires_tangra
                and hasattr(self, '_rad_corrections_applied')
                and self._rad_corrections_applied.Checked):
            confirmed = hasattr(self, '_chk_confirm_total_delay') and self._chk_confirm_total_delay.Checked
            if not confirmed:
                missing.append("confirmation that the Total Delay was entered in Tangra (tick the checkbox in Step A4)")

        if missing:
            self.status_label.Text = "Missing: " + ", ".join(missing)
            self.status_label.ForeColor = self._status_color('error')
            self._btn_next.Enabled = False
            if hasattr(self, '_btn_why_blocked'):
                self._btn_why_blocked.Visible = True
        else:
            self.status_label.Text = "Ready \u2014 click Next to select observation files"
            self.status_label.ForeColor = self._status_color('success')
            self._btn_next.Enabled = True
            if hasattr(self, '_btn_why_blocked'):
                self._btn_why_blocked.Visible = False
    
    def _next_click(self, sender, e):
        """Collect D2 selections, build timing_context, open PhaseBDialog (D3)."""
        # Report type
        if self.rb_na.Checked:
            self.report_type = 'north_america'
        elif self.rb_tt.Checked:
            self.report_type = 'trans_tasman'
        elif self.rb_sodis.Checked:
            self.report_type = 'sodis'
        self.config.set_last_report_type(self.report_type)

        # Equipment IDs
        telescopes = self.config.get_telescopes()
        cameras = self.config.get_cameras()
        if self.combo_telescope.SelectedIndex >= 0 and self.combo_telescope.SelectedIndex < len(telescopes):
            self.telescope_id = telescopes[self.combo_telescope.SelectedIndex].get('id')
        if self.combo_camera.SelectedIndex >= 0 and self.combo_camera.SelectedIndex < len(cameras):
            self.camera_id = cameras[self.combo_camera.SelectedIndex].get('id')

        # Build timing context to pass to D3
        is_ntp = hasattr(self, '_rad_timing_ntp') and self._rad_timing_ntp.Checked
        is_gps = hasattr(self, '_rad_timing_gps') and self._rad_timing_gps.Checked
        is_gps_cmos = hasattr(self, '_rad_timing_gps_cmos') and self._rad_timing_gps_cmos.Checked
        is_analog_vti = hasattr(self, '_rad_timing_analog_vti') and self._rad_timing_analog_vti.Checked
        rb_na_checked = hasattr(self, 'rb_na') and self.rb_na.Checked
        rb_tt_checked = hasattr(self, 'rb_tt') and self.rb_tt.Checked
        rb_sodis_checked = hasattr(self, 'rb_sodis') and self.rb_sodis.Checked

        total_delay_str = getattr(self, '_copy_total_delay_value', None)
        total_delay_ms = float(total_delay_str) if total_delay_str else None

        timing_context = {
            'is_ntp': is_ntp,
            'is_gps': is_gps,
            'is_gps_cmos': is_gps_cmos,
            'is_analog_vti': is_analog_vti,
            'rb_na_checked': rb_na_checked,
            'rb_tt_checked': rb_tt_checked,
            'rb_sodis_checked': rb_sodis_checked,
            'total_delay_ms': total_delay_ms,
            'ntp_offset_ms': self._ntp_offset_ms if is_ntp else 0.0,
            'ntp_uncertainty_ms': self._ntp_uncertainty_ms if is_ntp else 0.0,
            # rad_analog_aota_checked intentionally omitted — D3 defaults to AOTA (True)
        }

        from phase_b_dialog import PhaseBDialog
        self._dlg3 = PhaseBDialog(
            self.config,
            self.theme_manager,
            self.event,
            timing_context=timing_context,
            current_folder=getattr(self, 'current_folder', None),
        )
        if self._dlg3.ShowDialog(self) == DialogResult.OK:
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
    
    # ------------------------------------------------------------------
    # Phase B delegation getters — data lives in D3 after _next_click
    # ------------------------------------------------------------------

    def _d3(self):
        """Return the PhaseBDialog instance, or None if not yet opened."""
        return getattr(self, '_dlg3', None)

    def get_observation_type(self):
        d3 = self._d3()
        return d3.observation_type if d3 else None

    def get_selected_aota_path(self):
        d3 = self._d3()
        return d3.selected_aota_path if d3 else None

    def get_selected_tangra_path(self):
        d3 = self._d3()
        return d3.selected_tangra_path if d3 else None

    def get_selected_aota_report_path(self):
        d3 = self._d3()
        return d3.selected_aota_report_path if d3 else None

    def get_clouds(self):
        d3 = self._d3()
        return d3.clouds if d3 else None

    def get_stability(self):
        d3 = self._d3()
        return d3.stability if d3 else None

    def get_other_conditions(self):
        d3 = self._d3()
        return d3.other_conditions if d3 else None

    def get_selected_folder(self):
        d3 = self._d3()
        return d3.current_folder if d3 else getattr(self, 'current_folder', None)

    def get_selected_pyote_path(self):
        d3 = self._d3()
        return d3.selected_pyote_path if d3 else None

    def get_selected_pyote_event_index(self):
        d3 = self._d3()
        return d3.selected_pyote_event_index if d3 else -1

    def get_selected_aota_event_index(self):
        d3 = self._d3()
        return d3.selected_aota_event_index if d3 else -1

    def get_selected_aota_report_event_index(self):
        d3 = self._d3()
        return d3.selected_aota_report_event_index if d3 else -1

    def get_ntp_comment(self):
        d3 = self._d3()
        return d3.ntp_comment if d3 else None

    def get_observation_comment(self):
        d3 = self._d3()
        return d3.observation_comment if d3 else None

    def get_include_station_name(self):
        d3 = self._d3()
        return d3.include_station_name if d3 else False

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
        corrections_confirmed = False
        if self._rad_corrections_applied.Checked:
            camera_delay_applied = True
            ntp_applied = True
            confirmed = hasattr(self, '_chk_confirm_total_delay') and self._chk_confirm_total_delay.Checked
            corrections_confirmed = confirmed
        elif self._rad_corrections_not_applied.Checked:
            # User will apply corrections in Tangra; no internal D/R correction applied by OM
            camera_delay_applied = None
            ntp_applied = None
        else:
            camera_delay_applied = None
            ntp_applied = None
        ntp_offset_ms = self._ntp_offset_ms
        result = build_timing_data(
            timing_method='NTP',
            camera_delay_ms=camera_delay_ms,
            camera_delay_y_line=y_line,
            calib_run_id=calib_run_id,
            ntp_offset_ms=ntp_offset_ms,
            camera_delay_applied=camera_delay_applied,
            ntp_applied=ntp_applied,
        )
        result['corrections_confirmed'] = corrections_confirmed
        return result

    # ------------------------------------------------------------------
    # Timing section helpers
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # NTP Analyser (§1) helpers -- counterpart of LocationConfirmDialog NTP methods
    # ------------------------------------------------------------------

    def _prefill_ntp_folder(self):
        """Prefill NTP stats folder from saved settings, else discover candidates."""
        ntp_module = self.ntp_context.get('module')
        if ntp_module is None:
            return
        try:
            settings = ntp_module.load_folder_settings()
            saved_folder = (settings.get('log_folder') or '').strip()
            if saved_folder and os.path.isdir(saved_folder):
                self.txt_ntp_stats_folder.Text = saved_folder
                self._ntp_stats_folder = saved_folder
                return
            candidates = ntp_module.discover_candidate_dirs()
            for folder in candidates:
                options = ntp_module.build_day_options(folder)
                if options:
                    self.txt_ntp_stats_folder.Text = folder
                    self._ntp_stats_folder = folder
                    return
        except Exception:
            pass

    def _save_ntp_folder_setting(self, folder_path):
        ntp_module = self.ntp_context.get('module')
        if ntp_module is None:
            return
        try:
            settings = ntp_module.load_folder_settings()
            export_folder = settings.get('export_folder', '')
            observer_lat = settings.get('observer_lat', '')
            observer_lon = settings.get('observer_lon', '')
            ntp_module.save_folder_settings(folder_path, export_folder, observer_lat, observer_lon)
        except Exception:
            pass

    def _browse_ntp_folder_click(self, sender, e):
        dialog = FolderBrowserDialog()
        current = (self.txt_ntp_stats_folder.Text or '').strip()
        if current and os.path.isdir(current):
            dialog.SelectedPath = current
        if dialog.ShowDialog() == DialogResult.OK:
            self.txt_ntp_stats_folder.Text = dialog.SelectedPath
            self._ntp_stats_folder = dialog.SelectedPath
            self._save_ntp_folder_setting(dialog.SelectedPath)

    def _pick_ntp_dataset_for_event(self, ntp_module, stats_folder, event_dt):
        from datetime import date as _date
        options = ntp_module.build_day_options(stats_folder)
        if not options:
            raise RuntimeError("No loopstats/peerstats dataset found in selected folder.")
        event_mjd = (event_dt.date() - _date(1858, 11, 17)).days
        event_sec = (event_dt.hour * 3600.0 + event_dt.minute * 60.0
                     + event_dt.second + event_dt.microsecond / 1000000.0)
        best_option = None
        best_gap = None
        for option in options:
            try:
                loop_rows = ntp_module.parse_loopstats(option.loop_path, option.target_mjd)
            except Exception:
                continue
            day_rows = [r for r in loop_rows if r.mjd == event_mjd]
            if not day_rows:
                continue
            gap = min(abs(r.sec_of_day - event_sec) for r in day_rows)
            if best_gap is None or gap < best_gap:
                best_gap = gap
                best_option = option
        if best_option is not None:
            return best_option, best_gap
        for option in options:
            if option.target_mjd == event_mjd:
                return option, None
        return options[0], None

    def _analyse_ntp_click(self, sender, e):
        from datetime import date as _date
        ntp_module = self.ntp_context.get('module')
        if ntp_module is None:
            import_err = self.ntp_context.get('import_error') or 'ntp_analysis_core import failed.'
            MessageBox.Show(
                "NTP analysis core is not available.\n\n{0}".format(import_err),
                "NTP Module Not Available", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        stats_folder = (self.txt_ntp_stats_folder.Text or '').strip()
        if not stats_folder or not os.path.isdir(stats_folder):
            MessageBox.Show("Please select a valid NTP stats folder.", "Missing NTP Folder",
                            MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        event_dt = getattr(self.event, 'event_datetime', None)
        if event_dt is None:
            MessageBox.Show("Selected event does not have a UTC event time.", "Missing Event Time",
                            MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        self.lbl_ntp_analysing.Text = "Analysing - please wait up to ~30s"
        self.Refresh()
        try:
            option, sec_gap = self._pick_ntp_dataset_for_event(ntp_module, stats_folder, event_dt)
            mjd = (event_dt.date() - _date(1858, 11, 17)).days
            sec = (event_dt.hour * 3600.0 + event_dt.minute * 60.0
                   + event_dt.second + event_dt.microsecond / 1000000.0)
            loop_rows = ntp_module.parse_loopstats(option.loop_path, option.target_mjd)
            peer_rows = ntp_module.parse_peerstats(option.peer_path, option.target_mjd)
            if not loop_rows:
                raise RuntimeError("No loopstats rows available for event day in selected folder.")
            if not peer_rows:
                raise RuntimeError("No peerstats rows available for event day in selected folder.")
            known_servers = self.ntp_context.get('known_servers')
            result = ntp_module.estimate_offset_at_time(
                mjd, sec, loop_rows, peer_rows, known_servers=known_servers)
            self._ntp_stats_folder = stats_folder
            self._ntp_loopstats_path = option.loop_path
            self._ntp_peerstats_path = option.peer_path
            self._ntp_analysis_result_loc = result
            self._save_ntp_folder_setting(stats_folder)
            loop_name = os.path.basename(option.loop_path)
            peer_name = os.path.basename(option.peer_path)
            dataset_note = option.label if sec_gap is None else "{0} (closest: {1:.0f}s)".format(option.label, sec_gap)
            offset_ms = float(result.get('best_offset', 0.0)) * 1000.0
            uncertainty_ms = float(result.get('u_expanded', 0.0)) * 1000.0
            age_minutes = int(round(float(result.get('gap_before_s', 0.0)) / 60.0))
            server = result.get('active_server_at_T') or 'unknown'
            delay_ms = float(result.get('mean_delay_near_T', 0.0)) * 1000.0
            location_note = result.get('server_location_note') or ''
            self.lbl_ntp_offset_loc.Text = "Offset: {0:+.1f} ms".format(offset_ms)
            self.lbl_ntp_uncertainty_loc.Text = "Uncertainty: +/- {0:.1f} ms (95%)".format(uncertainty_ms)
            self.lbl_ntp_age_loc.Text = "Data age: {0} min".format(age_minutes)
            if location_note:
                self.lbl_ntp_server_loc.Text = "Server: {0}  |  {1:.1f} ms  ({2})".format(server, delay_ms, location_note)
            else:
                self.lbl_ntp_server_loc.Text = "Server: {0}  |  {1:.1f} ms".format(server, delay_ms)
            theme_colors = self.theme_manager.get_current_theme()
            text_fg = theme_colors['text_foreground']
            for lbl in (self.lbl_ntp_offset_loc, self.lbl_ntp_uncertainty_loc,
                        self.lbl_ntp_age_loc, self.lbl_ntp_server_loc):
                lbl.ForeColor = text_fg
            self.lbl_ntp_analysing.Text = ""
            # Forward result to event so §3 NTP correction panel can read it
            self.event.ntp_loopstats_path = option.loop_path
            self.event.ntp_peerstats_path = option.peer_path
            self.event.ntp_analysis_result = result
            self._populate_ntp_offset_label()
        except Exception as ex:
            self._ntp_analysis_result_loc = None
            for lbl in (self.lbl_ntp_offset_loc, self.lbl_ntp_uncertainty_loc,
                        self.lbl_ntp_age_loc, self.lbl_ntp_server_loc):
                lbl.Text = lbl.Text.split(':')[0] + ': -'
                lbl.ForeColor = Color.Red
            self.lbl_ntp_analysing.Text = ""
            MessageBox.Show("NTP analysis failed:\n\n{0}".format(str(ex)),
                            "NTP Analysis Error", MessageBoxButtons.OK, MessageBoxIcon.Error)

    def _on_open_ntp_analyser_location_click(self, sender, e):
        """Open the NTP analyser window from the §1 NTP Analyser panel."""
        ntp_module = self.ntp_context.get('module')
        import_error = self.ntp_context.get('import_error')
        if ntp_module is None and import_error:
            MessageBox.Show("NTP analysis core was not loaded:\n\n{0}".format(import_error),
                            "NTP Module Not Available", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        try:
            if getattr(self, '_ntp_gui_form', None) is not None:
                try:
                    if not self._ntp_gui_form.IsDisposed:
                        self._ntp_gui_form.BringToFront()
                        self._ntp_gui_form.Activate()
                        self._ntp_gui_form.TopMost = True
                        self._ntp_gui_form.TopMost = False
                        return
                except Exception:
                    pass
            import analyze_ntp_timing_accuracy as ntp_gui
            self._ntp_gui_form = ntp_gui.AnalyzerForm()
            self._ntp_gui_form.FormClosed += self._on_ntp_analyser_form_closed
            try:
                self._ntp_gui_form.Show(self)
            except Exception:
                self._ntp_gui_form.Show()
            self._ntp_gui_form.BringToFront()
            self._ntp_gui_form.Activate()
            self._ntp_gui_form.TopMost = True
            self._ntp_gui_form.TopMost = False
            stats_folder = (self.txt_ntp_stats_folder.Text or '').strip() or None
            event_dt = getattr(self.event, 'event_datetime', None)
            self._ntp_gui_form.prefill_from_event(stats_folder, event_dt, None, None)
        except Exception as ex:
            MessageBox.Show("Unable to open NTP analyser:\n\n{0}".format(str(ex)),
                            "Open NTP Analyser Error", MessageBoxButtons.OK, MessageBoxIcon.Error)

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
        """Load NTP offset state from event.ntp_analysis_result."""
        ntp_result = getattr(self.event, 'ntp_analysis_result', None)
        if ntp_result:
            self._ntp_offset_ms = float(ntp_result.get('best_offset', 0.0)) * 1000.0
            self._ntp_uncertainty_ms = float(ntp_result.get('u_expanded', 0.0)) * 1000.0
        else:
            self._ntp_offset_ms = 0.0
            self._ntp_uncertainty_ms = 0.0
            if hasattr(self, '_rad_corrections_not_applied'):
                self._rad_corrections_not_applied.Checked = True
        self._update_guidance_values()

    def _on_timing_method_changed(self, sender, e):
        """Show/hide Phase A and timing sub-panels when method radio changes."""
        if not sender.Checked:
            return
        is_ntp = self._rad_timing_ntp.Checked
        is_gps = self._rad_timing_gps.Checked
        is_gps_cmos = self._rad_timing_gps_cmos.Checked
        is_analog_vti = self._rad_timing_analog_vti.Checked

        # Phase A is only relevant for methods that need corrections entered into Tangra
        phase_a_visible = is_ntp or is_gps
        self._pnl_phase_a.Visible = phase_a_visible

        # Inside Phase A: only show the NTP analysis sub-section for the NTP method, not GPS flash
        if hasattr(self, '_pnl_ntp_analyse'):
            self._pnl_ntp_analyse.Visible = is_ntp

        # Step A1 input mode: NTP uses calibration/y-line; GPS flash uses manual delay entry.
        if hasattr(self, '_pnl_gps_manual_delay'):
            self._pnl_gps_manual_delay.Visible = is_gps
            if is_gps:
                self._pnl_gps_manual_delay.BringToFront()

        # Legacy Step A1 controls are hidden for GPS flash manual-entry workflow.
        for ctrl_name in (
                '_lbl_calib_run', '_combo_calib_run', '_btn_calib_info', '_lbl_calib_match',
                '_lbl_y_line', '_txt_y_line', '_btn_y_line_info',
                '_lbl_calc_label', '_lbl_calc_delay'):
            if hasattr(self, ctrl_name):
                getattr(self, ctrl_name).Visible = not is_gps

        if hasattr(self, '_btn_ntp_info'):
            if is_gps:
                self._btn_ntp_info.Text = "\u24d8  GPS flash timing help"
            else:
                self._btn_ntp_info.Text = "\u24d8  Timing correction help"

        if is_ntp:
            self._populate_calib_runs()
        elif is_gps:
            self._refresh_delay_label()
        self._update_guidance_values()
        self.update_button_state()

    def _on_gps_delay_changed(self, sender, e):
        """Handle GPS flash (dumb) manual camera delay entry."""
        is_gps = hasattr(self, '_rad_timing_gps') and self._rad_timing_gps.Checked
        if not is_gps:
            return
        self._refresh_delay_label()

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
            self._lbl_vti_info.ForeColor = self._status_color('error')
        elif is_aota and is_tt_sodis:
            self._lbl_vti_info.Text = (
                "\u24d8  TT and SODIS forms do not automatically apply VTI corrections. "
                "Ensure VTI corrections (camera + VTI delay) are applied inside AOTA."
            )
            self._lbl_vti_info.ForeColor = self._status_color('warning')
        elif not is_aota and is_na:
            self._lbl_vti_info.Text = (
                "\u2714  NA report form will automatically apply VTI corrections to D/R times."
            )
            self._lbl_vti_info.ForeColor = self._status_color('success')
        elif not is_aota and is_tt_sodis:
            self._lbl_vti_info.Text = (
                "\u26d4  INCOMPATIBLE: PyOTE does not apply VTI corrections, and TT/SODIS forms "
                "do not apply them automatically. D/R times will be uncorrected.\n"
                "Use the NA report form, or use AOTA to analyse the light curve."
            )
            self._lbl_vti_info.ForeColor = self._status_color('error')
        else:
            self._lbl_vti_info.Text = "Report format was selected in Step 3 of the previous dialog."
            self._lbl_vti_info.ForeColor = self._status_color('muted')

    def _update_file_status_labels(self):
        """Update folder status label in §1 Folder section."""
        if not hasattr(self, '_lbl_file_status'):
            return
        folder = self.current_folder
        if not folder or not os.path.isdir(folder):
            self._lbl_file_status.Text = "No folder selected"
            self._lbl_file_status.ForeColor = self._status_color('muted')
            return
        self._lbl_file_status.Text = "Folder selected \u2014 files will be loaded in the next step"
        self._lbl_file_status.ForeColor = self._status_color('success')

    def _update_guidance_values(self):
        """Refresh the Total Delay label and copy controls in Phase A."""
        if not hasattr(self, '_lbl_total_delay'):
            return
        is_ntp = hasattr(self, '_rad_timing_ntp') and self._rad_timing_ntp.Checked
        is_gps = hasattr(self, '_rad_timing_gps') and self._rad_timing_gps.Checked
        delay_ms = self._calculate_camera_delay()
        ntp_ms = getattr(self, '_ntp_offset_ms', 0.0) if is_ntp else 0.0
        if delay_ms is not None:
            self._copy_cam_delay_value = '{0:.1f}'.format(delay_ms)
        else:
            self._copy_cam_delay_value = None
        ntp_copy = '{0:.1f}'.format(ntp_ms if is_ntp else 0.0)
        self._copy_ntp_off_value = ntp_copy

        # Total Delay = camera_delay - ntp_offset:
        # positive camera delay shifts Tangra timestamps earlier (subtract);
        # positive NTP offset shifts Tangra timestamps later (subtract less).
        indiv_visible = False
        if delay_ms is not None:
            total_ms = (delay_ms - ntp_ms) if is_ntp else delay_ms
            if total_ms >= 0:
                self._lbl_total_delay.Text = '{0:.1f} ms'.format(total_ms)
                self._lbl_total_delay.ForeColor = Color.DarkGreen
                self._copy_total_delay_value = '{0:.1f}'.format(total_ms)
                if hasattr(self, '_lbl_a3_instr'):
                    if is_ntp:
                        self._lbl_a3_instr.Text = (
                            "\u270e  Open Tangra \u2192 Camera and Timing Corrections, enter the Total Delay "
                            "in the Acquisition Delay field only. Leave Reference Time unchecked.")
                    elif is_gps:
                        self._lbl_a3_instr.Text = (
                            "\u270e  Open Tangra \u2192 Camera and Timing Corrections, enter Camera Delay "
                            "in Acquisition Delay. Leave Reference Time unchecked.")
            else:
                # Negative delay — Tangra cannot accept negative Acquisition Delay values.
                self._lbl_total_delay.Text = '{0:.1f} ms'.format(total_ms)
                self._lbl_total_delay.ForeColor = Color.OrangeRed
                self._copy_total_delay_value = None
                indiv_visible = True
                if hasattr(self, '_lbl_a3_instr'):
                    if is_ntp:
                        self._lbl_a3_instr.Text = (
                            "\u270e  Total Delay is negative. Enter camera delay in Acquisition Delay "
                            "and NTP Offset in (Reference Time \u2212 UTC).")
                    elif is_gps:
                        self._lbl_a3_instr.Text = (
                            "\u270e  Camera delay is negative. Enter Acquisition Delay = 0 and put "
                            "the positive value into (Reference Time \u2212 UTC).")
        else:
            total_ms = None
            self._lbl_total_delay.Text = '\u2014'
            self._lbl_total_delay.ForeColor = Color.Gray
            self._copy_total_delay_value = None
        if hasattr(self, '_btn_copy_total_delay'):
            self._btn_copy_total_delay.Enabled = (self._copy_total_delay_value is not None)
        if hasattr(self, '_lbl_indiv_prefix'):
            self._lbl_indiv_prefix.Visible = indiv_visible
            if indiv_visible:
                if is_gps:
                    self._lbl_indiv_prefix.Text = 'Camera delay < 0 \u2014 enter values separately in Tangra:'
                    self._lbl_indiv_line1.Text = 'Acquisition Delay: 0.0 ms'
                    self._lbl_indiv_line2.Text = '(Reference Time \u2212 UTC): {0:.1f} ms'.format(abs(delay_ms))
                else:
                    self._lbl_indiv_prefix.Text = 'Total < 0 \u2014 enter delays separately in Tangra:'
                    self._lbl_indiv_line1.Text = 'Acquisition Delay: {0:.1f} ms'.format(delay_ms)
                    self._lbl_indiv_line2.Text = '(Reference Time \u2212 UTC): {0:.1f} ms'.format(ntp_ms)
            self._lbl_indiv_line1.Visible = indiv_visible
            self._lbl_indiv_line2.Visible = indiv_visible
        # Update confirmation checkbox with current total delay value;
        # uncheck if the value has changed since it was last confirmed.
        if hasattr(self, '_chk_confirm_total_delay'):
            if total_ms is not None and total_ms < 0:
                if is_gps:
                    new_chk_text = (
                        'For TANGRA enter Acquisition Delay = 0.0 ms and (Reference Time \u2212 UTC) = {0:.1f} ms '
                        '\u2014 tick to confirm values were entered correctly'.format(abs(delay_ms)))
                else:
                    new_chk_text = (
                        'Camera Delay for TANGRA: {0:.1f} ms  \u2014 tick to confirm delays are correctly entered separately'
                        .format(delay_ms))
            else:
                new_chk_text = (
                    'Total Delay for TANGRA: {0:.1f} ms  \u2014 tick to confirm value is correctly entered'
                    .format(total_ms) if total_ms is not None
                    else 'Total Delay for TANGRA: \u2014  (tick to confirm value is correctly entered)')
            if self._chk_confirm_total_delay.Text != new_chk_text:
                self._chk_confirm_total_delay.Checked = False
                self._chk_confirm_total_delay.Text = new_chk_text
            if hasattr(self, '_tooltip'):
                if is_gps and total_ms is not None and total_ms < 0:
                    self._tooltip.SetToolTip(
                        self._chk_confirm_total_delay,
                        "Confirm you entered Acquisition Delay=0.0 ms and (Reference Time \u2212 UTC)\n"
                        "as the positive absolute camera-delay value in Tangra."
                    )
                else:
                    self._tooltip.SetToolTip(
                        self._chk_confirm_total_delay,
                        "Confirm this is the exact Total Delay value you entered in Tangra\u2019s\n"
                        "Camera and Timing Corrections dialog, Acquisition Delay field."
                    )
        if hasattr(self, '_rad_corrections_applied'):
            if is_gps and total_ms is not None and total_ms < 0:
                applied_text = (
                    'Applied \u2014 I have entered Acquisition Delay = 0.0 ms and '
                    '(Reference Time \u2212 UTC) in Tangra'
                )
            else:
                applied_text = (
                    'Applied \u2014 I have entered the delays into Tangra\u2019s '
                    'Acquisition Delay field'
                )
            self._rad_corrections_applied.Text = applied_text
        if hasattr(self, '_lbl_csv_note'):
            if is_gps and total_ms is not None and total_ms < 0:
                self._lbl_csv_note.Text = (
                    'CSV can only verify Acquisition Delay = 0.0 ms; '
                    '(Reference Time \u2212 UTC) must be confirmed manually.'
                )
                self._lbl_csv_note.Visible = True
                if hasattr(self, '_lbl_csv_delay'):
                    self._lbl_csv_delay.Size = Size(540, 20)
            else:
                self._lbl_csv_note.Text = ''
                self._lbl_csv_note.Visible = False
                if hasattr(self, '_lbl_csv_delay'):
                    self._lbl_csv_delay.Size = Size(540, 40)

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

    def _on_total_delay_info_click(self, sender, e):
        """Show information about entering the Total Delay into Tangra."""
        is_gps = hasattr(self, '_rad_timing_gps') and self._rad_timing_gps.Checked
        if is_gps:
            delay_ms = self._calculate_camera_delay()
            neg_note = ''
            if delay_ms is not None and delay_ms < 0:
                neg_note = (
                    '\n\nFor negative camera delay (example -5.3 ms):\n'
                    '  \u2022 Acquisition Delay = 0.0 ms\n'
                    '  \u2022 (Reference Time \u2212 UTC) Offset = +5.3 ms\n'
                    'Tangra accepts only positive Acquisition Delay values.'
                )
            MessageBox.Show(
                'For GPS flash overlay (dumb), use the camera delay from Step A1.\n\n'
                'If delay is positive, enter it in Acquisition Delay and leave '
                '(Reference Time \u2212 UTC) unchecked.' + neg_note,
                'Tangra GPS Flash Timing Entry',
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            return

        MessageBox.Show(
            'Copy the Total Delay into the Tangra "Camera and Timing Corrections" dialog.\n\n'
            'Enter it in the Acquisition Delay field only.\n'
            'Leave the Reference Time unchecked \u2014 the Total Delay is the combined '
            'NTP offset and camera acquisition delay.\n\n'
            'If the Total Delay is negative, they must instead be entered separately:\n'
            'enter the camera Acquisition Delay in Tangra\u2019s Acquisition Delay field\n'
            'and the NTP Offset in the Reference Time (UTC Correction) field.',
            'Tangra Acquisition Delay Entry',
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )

    def _on_copy_total_delay_click(self, sender, e):
        """Copy the combined Total Delay (cam delay + NTP offset) to clipboard."""
        val = getattr(self, '_copy_total_delay_value', None)
        if val is not None:
            Clipboard.SetText(val)
        else:
            MessageBox.Show(
                'Total Delay not yet calculated.\nEnter a Y line value in Step A1 above.',
                'Nothing to Copy',
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )

    def _on_rescan_from_guidance_click(self, sender, e):
        """Read the first Tangra CSV in the folder and update the Step A4 acquisition delay label."""
        folder = self.current_folder
        if not folder or not os.path.isdir(folder):
            self._lbl_csv_delay.Text = 'No folder selected'
            self._lbl_csv_delay.ForeColor = Color.Gray
            return
        try:
            csv_path = None
            for filename in sorted(os.listdir(folder)):
                if filename.lower().endswith('.csv'):
                    csv_path = os.path.join(folder, filename)
                    break
            if csv_path is None:
                self._ts_summary = None
                self._lbl_csv_delay.Text = 'No CSV found in folder'
                self._lbl_csv_delay.ForeColor = Color.Gray
                return
            import light_curve_reader as lcr
            summary = lcr.get_observation_summary(csv_path, percentiles=[1, 99])
            self._ts_summary = summary
            delay_ms = self._calculate_camera_delay()
            self._auto_detect_camera_delay(delay_ms)
        except Exception as ex:
            self._lbl_csv_delay.Text = 'Error reading CSV'
            self._lbl_csv_delay.ForeColor = Color.OrangeRed

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
            print("[CameraSettings] folder invalid or missing:", repr(folder))
            return None
        candidates = []
        try:
            all_files = os.listdir(folder)
            for f in all_files:
                fl = f.lower()
                if fl.endswith('.camerasettings') or fl.endswith('.camerasettings.txt'):
                    candidates.append(os.path.join(folder, f))
        except Exception as ex:
            print("[CameraSettings] ERROR listing folder:", ex)
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

        def _apply_binning_to_area(area_str, binning_str):
            """Divide unbinned WxH area string by binning factor. Returns binned 'WxH' or None."""
            try:
                b = int(_norm_binning(binning_str))
                if b < 2:
                    return area_str
                parts = str(area_str).strip().lower().split('x')
                if len(parts) == 2:
                    w = int(round(int(parts[0]) / b))
                    h = int(round(int(parts[1]) / b))
                    return '{0}x{1}'.format(w, h)
            except (ValueError, TypeError, AttributeError):
                pass
            return area_str

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
                    # CameraSettings stores unbinned pixels; calibration run stores binned pixels
                    binning_for_area = sc_binning or run.get('binning', '1')
                    sc_area_binned = _apply_binning_to_area(sc_area, binning_for_area)
                    checks.append(
                        str(run.get('camera_area', '')).strip().lower() == sc_area_binned.lower())
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
            sc_area_binned = _apply_binning_to_area(sc_area, sc_binning) if sc_area and sc_binning else sc_area
            match_detail = '{0} / {1}x / {2}'.format(sc_area_binned, sc_binning, sc_colour)
            if sc_tilt is not None:
                match_detail += ' / tilt {0}'.format(sc_tilt)
            if sc_pan is not None:
                match_detail += ' / pan {0}'.format(sc_pan)
            self._lbl_calib_match.Text = '\u2714 Auto-matched from SharpCap settings'
            self._lbl_calib_match.ForeColor = Color.Green
        elif sc_area or sc_binning:
            # Show both what the file has (binned) and what the stored run has, for easy comparison
            stored = all_runs_sorted[0] if all_runs_sorted else {}
            binning_for_area = sc_binning or stored.get('binning', '1')
            sc_area_binned = _apply_binning_to_area(sc_area, binning_for_area) if sc_area else '?'
            file_detail = 'file: {0}(/{1}binned={2})/{3}x/{4}'.format(
                sc_area or '?', _norm_binning(binning_for_area), sc_area_binned,
                _norm_binning(sc_binning) if sc_binning else '?', sc_colour or '?')
            run_detail = 'run: {0}/{1}x/{2}'.format(
                stored.get('camera_area', '?'), stored.get('binning', '?'), stored.get('colour_space', '?'))
            if sc_tilt is not None:
                file_detail += '/tilt {0}'.format(sc_tilt)
                run_detail += '/tilt {0}'.format(stored.get('tilt', '?'))
            if sc_pan is not None:
                file_detail += '/pan {0}'.format(sc_pan)
                run_detail += '/pan {0}'.format(stored.get('pan', '?'))
            self._lbl_calib_match.Text = '\u26a0 No match \u2014 {0}  vs  {1} \u2014 showing all runs'.format(file_detail, run_detail)
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
        applied = (hasattr(self, '_rad_corrections_applied')
                   and self._rad_corrections_applied.Checked)
        if hasattr(self, '_chk_confirm_total_delay'):
            self._chk_confirm_total_delay.Enabled = applied
            if not applied:
                self._chk_confirm_total_delay.Checked = False
        self.update_button_state()

    def _on_confirm_check_changed(self, sender, e):
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

        # GPS flash (dumb): camera delay is entered manually (no line-delay calculation here).
        if hasattr(self, '_rad_timing_gps') and self._rad_timing_gps.Checked:
            delay_ms = self._calculate_camera_delay()
            if delay_ms is None:
                self._lbl_calc_delay.Text = '\u2014 (enter camera delay)'
                self._lbl_calc_delay.ForeColor = Color.Gray
            else:
                self._lbl_calc_delay.Text = '{0:.1f} ms'.format(delay_ms)
                self._lbl_calc_delay.ForeColor = normal_color
            self._auto_detect_camera_delay(delay_ms)
            self._update_guidance_values()
            return

        text = self._txt_y_line.Text.strip()
        if not text:
            self._lbl_calc_delay.Text = '\u2014'
            self._lbl_calc_delay.ForeColor = normal_color
            self._auto_detect_camera_delay(None)
            self._update_guidance_values()
            return
        try:
            y = float(text)
        except ValueError:
            self._lbl_calc_delay.Text = '\u2014 (not a valid number)'
            self._lbl_calc_delay.ForeColor = Color.OrangeRed
            self._auto_detect_camera_delay(None)
            self._update_guidance_values()
            return
        y_max = self._get_y_line_max()
        if y < 0 or (y_max is not None and y > y_max):
            if y_max is not None:
                self._lbl_calc_delay.Text = '\u2014 (must be 0\u2013{0})'.format(y_max)
            else:
                self._lbl_calc_delay.Text = '\u2014 (must be \u22650)'
            self._lbl_calc_delay.ForeColor = Color.OrangeRed
            self._auto_detect_camera_delay(None)
            self._update_guidance_values()
            return
        delay_ms = self._calculate_camera_delay()
        if delay_ms is not None:
            self._lbl_calc_delay.Text = '{0:.1f} ms'.format(delay_ms)
        else:
            self._lbl_calc_delay.Text = '\u2014'
        self._lbl_calc_delay.ForeColor = normal_color
        self._auto_detect_camera_delay(delay_ms)
        self._update_guidance_values()

    def _calculate_camera_delay(self):
        """Return camera_delay_ms from selected calibration run + Y line, or None."""
        # GPS flash (dumb): user enters measured camera acquisition delay directly.
        if hasattr(self, '_rad_timing_gps') and self._rad_timing_gps.Checked:
            if not hasattr(self, '_txt_gps_delay'):
                return None
            text = self._txt_gps_delay.Text.strip()
            if not text:
                return None
            try:
                return round(float(text), 1)
            except ValueError:
                return None

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
        """Compare Tangra CSV acquisition_delay with Total Delay (cam - NTP), auto-select radio."""
        if not hasattr(self, '_lbl_csv_delay'):
            return
        if self._ts_summary is None:
            self._lbl_csv_delay.Text = 'Rescan folder to load the Tangra CSV acquisition delay'
            self._lbl_csv_delay.ForeColor = Color.Gray
            if hasattr(self, '_rad_corrections_applied'):
                self._rad_corrections_applied.Enabled = False
            return
        # CSV loaded — enable the Applied radio now that we have data to compare against
        if hasattr(self, '_rad_corrections_applied'):
            self._rad_corrections_applied.Enabled = True
        csv_delay = self._ts_summary.get('acquisition_delay')  # ms, float or None
        is_ntp = hasattr(self, '_rad_timing_ntp') and self._rad_timing_ntp.Checked
        is_gps = hasattr(self, '_rad_timing_gps') and self._rad_timing_gps.Checked

        if is_ntp:
            # When total delay (cam - ntp) is negative, Tangra requires separate entries;
            # compare CSV only against camera delay in that case.
            ntp_ms = getattr(self, '_ntp_offset_ms', 0.0)
            total_is_negative = (calculated_ms is not None and (calculated_ms - ntp_ms) < 0)
            if total_is_negative:
                compare_ms = calculated_ms  # check camera delay only
            else:
                compare_ms = (calculated_ms - ntp_ms) if calculated_ms is not None else None
            guidance_note = (
                '\n\u26a0 Ensure you have applied the NTP Offset in TANGRA'
                ' \u2014 this cannot be checked automatically'
            ) if total_is_negative else ''
            ref_label = 'camera delay' if total_is_negative else 'Total Delay'
        else:
            # GPS flash (dumb): no NTP analyser offset. If camera delay is negative,
            # Tangra requires Acquisition Delay=0 and positive (Reference Time-UTC).
            total_is_negative = (calculated_ms is not None and calculated_ms < 0)
            compare_ms = 0.0 if total_is_negative else calculated_ms
            guidance_note = ''
            ref_label = 'Acquisition Delay'
        if csv_delay is None:
            self._lbl_csv_delay.Text = 'not present in CSV'
            self._lbl_csv_delay.ForeColor = Color.Gray
            if compare_ms is not None:
                if not (self._rad_corrections_applied.Checked
                        or self._rad_corrections_not_applied.Checked):
                    self._rad_corrections_not_applied.Checked = True
            return
        csv_val = float(csv_delay)
        if compare_ms is not None:
            diff = abs(csv_val - compare_ms)
            if csv_val < 0.1 and not (is_gps and total_is_negative):
                self._lbl_csv_delay.Text = '{0:.1f} ms (zero \u2014 not applied in Tangra)'.format(csv_val)
                self._lbl_csv_delay.ForeColor = Color.Gray
                if not self._correction_user_set:
                    self._suppress_correction_event = True
                    self._rad_corrections_not_applied.Checked = True
                    self._suppress_correction_event = False
            elif diff <= 1.0:
                self._lbl_csv_delay.Text = (
                    '{0:.1f} ms \u2714 close match \u2014 delay was applied{1}'.format(csv_val, guidance_note))
                self._lbl_csv_delay.ForeColor = Color.Green
                if not self._correction_user_set:
                    self._suppress_correction_event = True
                    self._rad_corrections_applied.Checked = True
                    self._suppress_correction_event = False
            else:
                self._lbl_csv_delay.Text = (
                    '{0:.1f} ms  \u26a0 differs from {1} by {2:.1f} ms \u2014 verify{3}'.format(
                        csv_val, ref_label, diff, guidance_note))
                self._lbl_csv_delay.ForeColor = Color.OrangeRed
        else:
            self._lbl_csv_delay.Text = '{0:.1f} ms'.format(csv_val)
            self._lbl_csv_delay.ForeColor = Color.Gray

    def _setup_tooltips(self):
        """Configure hover tooltips for NTP panel controls and observation type radios."""
        self._tooltip = ToolTip()
        self._tooltip.AutoPopDelay = 12000
        self._tooltip.InitialDelay = 400
        self._tooltip.ReshowDelay = 200
        if hasattr(self, '_combo_calib_run'):
            self._tooltip.SetToolTip(
                self._combo_calib_run,
                "Select the run whose area, binning, gain, and frame rate match\n"
                "your occultation recording. If none match, use Tools \u2192 Camera Delay Calculator."
            )
        if hasattr(self, '_txt_y_line'):
            self._tooltip.SetToolTip(
                self._txt_y_line,
                "The vertical pixel position of the star on the sensor in Tangra.\n"
                "Right-click the aperture \u2192 Properties to read it."
            )
        if hasattr(self, '_txt_gps_delay'):
            self._tooltip.SetToolTip(
                self._txt_gps_delay,
                "GPS flash (dumb): enter the measured camera acquisition delay in ms.\n"
                "Use one decimal place; negative values are allowed."
            )
        if hasattr(self, '_chk_confirm_total_delay'):
            self._tooltip.SetToolTip(
                self._chk_confirm_total_delay,
                "Confirm this is the exact Total Delay value you entered in Tangra\u2019s\n"
                "Camera and Timing Corrections dialog, Acquisition Delay field."
            )
        if hasattr(self, '_rad_corrections_not_applied'):
            self._tooltip.SetToolTip(
                self._rad_corrections_not_applied,
                "Choose this if you still need to enter the corrections in Tangra.\n"
                "The guidance panel below shows the exact steps."
            )
        if hasattr(self, 'rb_positive'):
            self._tooltip.SetToolTip(
                self.rb_positive,
                "Observed both disappearance and reappearance.\n"
                "AOTA or PyOTE result required."
            )
        if hasattr(self, 'rb_negative'):
            self._tooltip.SetToolTip(
                self.rb_negative,
                "No occultation was detected.\n"
                "AOTA is optional; a light curve CSV is still required."
            )
        if hasattr(self, 'rb_unsure'):
            self._tooltip.SetToolTip(
                self.rb_unsure,
                "A possible event occurred but the result is uncertain.\n"
                "AOTA or PyOTE result required."
            )

    def _on_open_ntp_analyser_click(self, sender, e):
        """Open the standalone NTP Analyser window from within the Generate Report dialog."""
        try:
            if getattr(self, '_ntp_gui_form', None) is not None:
                try:
                    if not self._ntp_gui_form.IsDisposed:
                        self._ntp_gui_form.BringToFront()
                        self._ntp_gui_form.Activate()
                        self._ntp_gui_form.TopMost = True
                        self._ntp_gui_form.TopMost = False
                        return
                except Exception:
                    pass

            import analyze_ntp_timing_accuracy as ntp_gui
            self._ntp_gui_form = ntp_gui.AnalyzerForm()
            self._ntp_gui_form.FormClosed += self._on_ntp_analyser_form_closed
            try:
                self._ntp_gui_form.Show(self)
            except Exception:
                self._ntp_gui_form.Show()
            self._ntp_gui_form.BringToFront()
            self._ntp_gui_form.Activate()
            self._ntp_gui_form.TopMost = True
            self._ntp_gui_form.TopMost = False

            # Pre-populate with event context
            stats_folder = None
            loopstats_path = getattr(self.event, 'ntp_loopstats_path', None)
            if loopstats_path:
                stats_folder = os.path.dirname(loopstats_path)
            event_dt = getattr(self.event, 'event_datetime', None)
            obs_lat = getattr(self.event, 'latitude', None)
            obs_lon = getattr(self.event, 'longitude', None)
            self._ntp_gui_form.prefill_from_event(stats_folder, event_dt, obs_lat, obs_lon)
        except Exception as ex:
            MessageBox.Show(
                "Unable to open NTP analyser:\n\n{0}".format(str(ex)),
                "Open NTP Analyser Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error,
            )

    def _on_ntp_analyser_form_closed(self, sender, e):
        """Handle NTP analyser form close — offer to apply PIT values to §3."""
        self._ntp_gui_form = None
        try:
            pit_vals = sender.get_pit_result()
            if pit_vals is None:
                return
            offset_ms, error_ms, raw_pit = pit_vals
            answer = MessageBox.Show(
                "Use the NTP PIT values calculated in the analyser?\n\n"
                "  Offset:       {0:+.1f} ms\n"
                "  Uncertainty:  \u00b1{1:.1f} ms  (95%)\n\n"
                "Clicking Yes will update the NTP correction in \u00a73.".format(
                    offset_ms, error_ms),
                "Use NTP PIT Values?",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Question,
            )
            if answer == DialogResult.Yes:
                self._apply_ntp_pit_result(offset_ms, error_ms, raw_pit)
        except Exception:
            pass

    def _apply_ntp_pit_result(self, offset_ms, error_ms, raw_pit=None):
        """Apply NTP PIT values from the analyser and refresh the Step A2 panel labels."""
        self._ntp_offset_ms = offset_ms
        self._ntp_uncertainty_ms = error_ms
        if hasattr(self, 'lbl_ntp_offset_loc'):
            theme_colors = self.theme_manager.get_current_theme()
            text_fg = theme_colors['text_foreground']
            self.lbl_ntp_offset_loc.Text = 'Offset: {0:+.1f} ms'.format(offset_ms)
            self.lbl_ntp_offset_loc.ForeColor = text_fg
            self.lbl_ntp_uncertainty_loc.Text = 'Uncertainty: +/- {0:.1f} ms (95%)'.format(error_ms)
            self.lbl_ntp_uncertainty_loc.ForeColor = text_fg
            if raw_pit is not None:
                age_minutes = int(round(float(raw_pit.get('gap_before_s', 0.0)) / 60.0))
                server = raw_pit.get('active_server_at_T') or 'unknown'
                delay_ms_val = float(raw_pit.get('mean_delay_near_T', 0.0)) * 1000.0
                location_note = raw_pit.get('server_location_note') or ''
                self.lbl_ntp_age_loc.Text = 'Data age: {0} min'.format(age_minutes)
                if location_note:
                    self.lbl_ntp_server_loc.Text = 'Server: {0}  |  {1:.1f} ms  ({2})'.format(
                        server, delay_ms_val, location_note)
                else:
                    self.lbl_ntp_server_loc.Text = 'Server: {0}  |  {1:.1f} ms'.format(
                        server, delay_ms_val)
                self.lbl_ntp_age_loc.ForeColor = text_fg
                self.lbl_ntp_server_loc.ForeColor = text_fg
        self._update_guidance_values()
        self.update_button_state()

    def _on_ntp_info_click(self, sender, e):
        is_gps = hasattr(self, '_rad_timing_gps') and self._rad_timing_gps.Checked
        if is_gps:
            MessageBox.Show(
                "GPS flash overlay (dumb) timing uses camera acquisition delay only.\n\n"
                "There is no NTP analyser offset in this method.\n\n"
                "If Camera Delay is positive:\n"
                "  enter it in Tangra Acquisition Delay and leave Reference unchecked.\n\n"
                "If Camera Delay is negative:\n"
                "  Tangra cannot accept negative Acquisition Delay, so enter:\n"
                "    Acquisition Delay = 0.0 ms\n"
                "    (Reference Time \u2212 UTC) = abs(camera delay) as a positive value.",
                "About GPS Flash Timing Corrections",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            return

        MessageBox.Show(
            "NTP timing corrections account for two sources of error in event timestamps:\n\n"
            "1.  Camera acquisition delay\n"
            "    Rolling-shutter cameras do not capture all pixel rows at the same instant.\n"
            "    The delay depends on which Y-line the star falls on, the frame rate,\n"
            "    and the sensor readout speed. It is measured using LED flash calibration runs.\n\n"
            "2.  NTP clock offset\n"
            "    The computer clock may drift slightly from UTC. NTP corrects this\n"
            "    continuously, but a small residual offset usually remains.\n\n"
            "Both values are entered in Tangra\u2019s Video File Properties \u2192 Timing Correction\n"
            "before exporting the timing CSV. The Total Delay to enter is:\n"
            "    total = camera_delay_ms \u2212 ntp_offset_ms\n\n"
            "In Tangra, a positive camera delay shifts event times earlier.\n"
            "In Tangra, a positive NTP offset shifts event times later.\n"
            "Entering (camera_delay \u2212 ntp_offset) in Tangra's Acquisition Delay field\n"
            "combines both corrections in a single entry.",
            "About NTP Timing Corrections",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )

    def _on_calib_info_click(self, sender, e):
        MessageBox.Show(
            "A calibration run is a short video of LED flashes recorded before or\n"
            "after your occultation session, using the same camera settings.\n\n"
            "The flash timing determines the camera acquisition delay for each\n"
            "Y-line position. For a valid match, the run must use the same:\n"
            "  \u2022  Area / crop / region of interest\n"
            "  \u2022  Binning\n"
            "  \u2022  Gain\n"
            "  \u2022  Frame rate\n\n"
            "If no matching run is listed, use:\n"
            "  Tools \u2192 Camera Delay Calculator\u2026\n"
            "to process a new LED flash video and create a calibration run.",
            "About Calibration Runs",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )

    def _on_y_line_info_click(self, sender, e):
        MessageBox.Show(
            "The Y-line is the vertical pixel position of the target star on the sensor,\n"
            "as shown in Tangra.\n\n"
            "To find it in Tangra:\n"
            "  1.  Open the occultation video in Tangra\n"
            "  2.  Right-click the tracking aperture on the target star\n"
            "  3.  Select Properties\n"
            "  4.  Note the Y coordinate shown\n\n"
            "Use the aperture position from your actual occultation recording,\n"
            "not from the calibration run.\n\n"
            "The Y-line determines where in the rolling-shutter readout cycle the star\n"
            "was captured. A larger Y-line means a larger delay on bottom-read sensors.",
            "Finding the Y-line in Tangra",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )

    def _on_why_confirm_click(self, sender, e):
        is_gps = hasattr(self, '_rad_timing_gps') and self._rad_timing_gps.Checked
        if is_gps:
            MessageBox.Show(
                "OM calculates camera-delay guidance, but cannot verify whether\n"
                "you actually entered the values in Tangra.\n\n"
                "For GPS flash overlay (dumb), if camera delay is negative then Tangra\n"
                "cannot accept it in Acquisition Delay. You must enter:\n"
                "  \u2022  Acquisition Delay = 0.0 ms\n"
                "  \u2022  (Reference Time \u2212 UTC) Offset = abs(camera delay)\n\n"
                "If these are not entered correctly, exported times can be wrong.\n\n"
                "HOW TO VERIFY\n"
                "Open the Tangra CSV and check row 8.\n"
                "For negative-delay workflow, \u2018Acquisition Delay (ms)\u2019 should be 0.0 ms.\n"
                "CSV does not record the (Reference Time \u2212 UTC) value, so confirm it\n"
                "from your Tangra entry notes.",
                "Why is Confirmation Required?",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            return

        MessageBox.Show(
            "OM calculates what the corrections should be, but cannot verify whether\n"
            "you actually entered them in Tangra.\n\n"
            "If the corrections were not entered but you select \u2018Applied in Tangra\u2019,\n"
            "the exported D/R times will be uncorrected while the report states they\n"
            "were corrected. This is a silent error that affects timing accuracy.\n\n"
            "By ticking both boxes you confirm that:\n"
            "  \u2022  The camera acquisition delay shown was entered in Tangra\u2019s\n"
            "     Video File Properties \u2192 Timing Correction\n"
            "  \u2022  The NTP clock offset was entered in the same section\n\n"
            "If either value changes (e.g. you update the Y-line or calibration run),\n"
            "the boxes are cleared automatically and the heading turns orange \u2014\n"
            "re-confirm after reviewing the new values.\n\n"
            "HOW TO VERIFY THE CORRECTIONS WERE APPLIED\n"
            "Open the Tangra CSV in a text editor and check row 8 (the measurement\n"
            "parameters row). The column \u2018Acquisition Delay (ms)\u2019 must show the camera\n"
            "delay value, not 0. Because Tangra does not record the NTP offset in the\n"
            "CSV header, verification of the NTP value relies on your own record-keeping\n"
            "(the NTP analysis log from Step 2 is the authoritative source).",
            "Why is Confirmation Required?",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )

    def _on_why_blocked_click(self, sender, e):
        text = getattr(self.status_label, 'Text', '')
        if not text or text.startswith("Ready"):
            return
        MessageBox.Show(
            text,
            "Why is Generate blocked?",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )


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

    def __init__(self, tangra_path, d_time_seconds=None, r_time_seconds=None, event_time_seconds=None, theme_manager=None):
        Form.__init__(self)
        self.tangra_path = tangra_path
        self.d_time_seconds = d_time_seconds
        self.r_time_seconds = r_time_seconds
        self.event_time_seconds = event_time_seconds
        self._theme_manager = theme_manager
        self._setup_ui()
        self._apply_dialog_theme_non_chart()
        self._build_charts()

    def _apply_dialog_theme_non_chart(self):
        """Apply night/day theme to dialog controls without changing chart colors."""
        if self._theme_manager is None:
            return

        try:
            theme_colors = self._theme_manager.get_current_theme()
            # Style the form and all non-plot controls. Keep PlotView controls
            # untouched so chart background/series colors remain unchanged.
            self.BackColor = theme_colors['background']
            self.ForeColor = theme_colors['text_foreground']
            for child in self.Controls:
                if child == self._plot_interval or child == self._plot_signal:
                    continue
                apply_theme_to_control(child, theme_colors)
        except Exception:
            pass

    def _setup_ui(self):
        self.Text = "Timestamp Inspector"
        self.Size = Size(900, 780)
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
        self._lbl_info.Size = Size(770, 68)
        self._lbl_info.Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
        self._lbl_info.Text = (
            "Delayed frames: deviation > +10% of median.  Late frames: deviation > +90% of median (dropped frame likely).\n"
            "Anomalies outside the D/R window have no impact on reported event times.\n"
            "Many anomalies may indicate frame rate too high. Recommended: record at \u22641/3 of camera max frame rate."
        )
        self.Controls.Add(self._lbl_info)

        btn_close = Button()
        btn_close.Text = "Close"
        btn_close.Location = Point(793, 620)
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
                "Median exposure: {0:.0f} ms   |   "
                "Min deviation: {1:+.0f} ms   |   "
                "Max deviation: {2:+.0f} ms"
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
            model1.PlotMargins = OxyPlot.OxyThickness(75.0, 10.0, 20.0, 30.0)

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
            ya2.StringFormat = "0.00E+0"
            model2.Axes.Add(ya2)
            model2.PlotMargins = OxyPlot.OxyThickness(75.0, 10.0, 20.0, 30.0)

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
        if event_frame is not None and not (d_frame is not None or r_frame is not None):
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
            ann.TextHorizontalAlignment = OxyPlot.HorizontalAlignment.Right
            ann.TextOrientation = OxyAnn.AnnotationTextOrientation.Horizontal
            model.Annotations.Add(ann)
        if r_frame is not None:
            ann = OxyAnn.LineAnnotation()
            ann.Type = OxyAnn.LineAnnotationType.Vertical
            ann.X = float(r_frame)
            ann.Color = OxyPlot.OxyColors.Green
            ann.LineStyle = OxyPlot.LineStyle.Dash
            ann.Text = "R"
            ann.TextOrientation = OxyAnn.AnnotationTextOrientation.Horizontal
            model.Annotations.Add(ann)

