"""
Phase B Dialog — Step 3 of the Generate Report flow.

Shown after ComprehensiveReportDialog (Dialog 2) once the user has confirmed
timing corrections (or declared them N/A).  Owns:
  §3  Observation Files + Timestamp Check
  §4  Per-method timing info panels (GPS-CMOS / GPS-flash / Analog-VTI / Other)
  §5  Observation Result
  §6  Conditions
  [Generate Report]
"""

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("System")

import os
import re
import System
from System import Array
from System.Drawing import Point, Size, Color, Font, FontStyle
from System.Windows.Forms import (
    Form, Button, Label, ListBox, Panel, TextBox, GroupBox, RadioButton, ComboBox,
    CheckBox, DialogResult, FormStartPosition, MessageBox,
    MessageBoxButtons, MessageBoxIcon, FolderBrowserDialog, SelectionMode,
    ComboBoxStyle, ToolTip
)
from theme import apply_theme_to_control


class PhaseBDialog(Form):
    """Dialog 3 — file selection, result, conditions, and Generate button."""

    def __init__(self, config, theme_manager, event,
                 timing_context,
                 current_folder=None):
        """
        Args:
            config:         ConfigManager
            theme_manager:  ThemeManager
            event:          Event object
            timing_context: dict with keys populated by D2:
                'is_ntp', 'is_gps', 'is_gps_cmos', 'is_analog_vti',
                'rb_na_checked', 'rb_tt_checked', 'rb_sodis_checked',
                'rad_analog_aota_checked',
                'ts_summary'  (live reference — may be updated by rescan)
            current_folder: last browsed folder from D2 (may be None)
        """
        Form.__init__(self)
        self.config = config
        self.theme_manager = theme_manager
        self.event = event
        self.timing_ctx = timing_context
        self.current_folder = current_folder

        # File lists
        self.aota_files = []
        self.csv_files = []
        self.aota_report_files = []
        self.pyote_files = []
        self.pyote_events = []
        self._dr_events = []
        self.selected_pyote_path = None
        self.selected_pyote_event_index = -1
        self.selected_aota_event_index = -1
        self.selected_aota_report_event_index = -1

        # D/R times for inspector
        self._d_time_seconds = None
        self._r_time_seconds = None
        self._ts_summary = None

        # NTP comment to include in report (set when NTP uncertainty checkbox is checked)
        self.ntp_comment = None

        # Output values
        self.selected_tangra_path = None
        self.selected_aota_path = None
        self.selected_aota_report_path = None
        self.clouds = None
        self.stability = None
        self.other_conditions = None
        self.observation_type = None
        self.include_station_name = False
        self._owc_type_user_override = False
        self._suppress_owc_combo_event = False
        self._last_submitted_owc_signature = None

        self._setup_ui()

        if current_folder and os.path.isdir(current_folder):
            self.folder_textbox.Text = current_folder
            self.scan_folder(current_folder)

        self._apply_timing_panels()
        self.update_button_state()

        theme_colors = theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self.Text = "Generate Report \u2014 Phase B"
        self.Size = Size(1000, 1000)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False

        main_panel = Panel()
        main_panel.Location = Point(10, 10)
        main_panel.Size = Size(970, 860)
        main_panel.AutoScroll = True
        self.Controls.Add(main_panel)

        y_pos = 10

        # ===== PHASE B SEPARATOR =====
        lbl_phase_b = Label()
        lbl_phase_b.Text = "\u25bc  Phase B \u2014 After saving the Tangra light curve"
        lbl_phase_b.Font = Font(lbl_phase_b.Font.FontFamily, lbl_phase_b.Font.Size, FontStyle.Bold)
        lbl_phase_b.Location = Point(10, y_pos)
        lbl_phase_b.Size = Size(600, 20)
        lbl_phase_b.ForeColor = Color.Navy

        # Only show Phase B separator when Phase A was relevant (NTP or GPS flash)
        is_ntp = self.timing_ctx.get('is_ntp', False)
        is_gps = self.timing_ctx.get('is_gps', False)
        lbl_phase_b.Visible = is_ntp or is_gps
        main_panel.Controls.Add(lbl_phase_b)
        self._lbl_phase_b_separator = lbl_phase_b
        y_pos += 28

        # ===== SECTION 3: OBSERVATION FILES & TIMESTAMP CHECK =====
        grp_files = GroupBox()
        grp_files.Text = "3. Observation Files"
        grp_files.Location = Point(10, y_pos)
        # Size set later once _grp_dr_height is known
        main_panel.Controls.Add(grp_files)

        lbl_csv = Label()
        lbl_csv.Text = "Light Curve File:"
        lbl_csv.Location = Point(15, 89)
        lbl_csv.Size = Size(130, 20)
        grp_files.Controls.Add(lbl_csv)

        self.csv_count_label = Label()
        self.csv_count_label.Text = "No folder"
        self.csv_count_label.Location = Point(145, 89)
        self.csv_count_label.Size = Size(155, 20)
        self.csv_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.csv_count_label)

        self.csv_listbox = ListBox()
        self.csv_listbox.Location = Point(15, 112)
        self.csv_listbox.Size = Size(285, 65)
        self.csv_listbox.SelectionMode = SelectionMode.One
        self.csv_listbox.SelectedIndexChanged += self.selection_changed
        grp_files.Controls.Add(self.csv_listbox)

        self.csv_preview_label = Label()
        self.csv_preview_label.Text = "Observing times: -"
        self.csv_preview_label.Location = Point(15, 180)
        self.csv_preview_label.Size = Size(285, 40)
        self.csv_preview_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.csv_preview_label)

        lbl_aota = Label()
        lbl_aota.Text = "AOTA Files:"
        lbl_aota.Location = Point(315, 89)
        lbl_aota.Size = Size(120, 20)
        grp_files.Controls.Add(lbl_aota)

        self.aota_count_label = Label()
        self.aota_count_label.Text = "No folder"
        self.aota_count_label.Location = Point(435, 89)
        self.aota_count_label.Size = Size(165, 20)
        self.aota_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.aota_count_label)

        self.aota_listbox = ListBox()
        self.aota_listbox.Location = Point(315, 112)
        self.aota_listbox.Size = Size(285, 65)
        self.aota_listbox.SelectionMode = SelectionMode.One
        self.aota_listbox.SelectedIndexChanged += self.selection_changed
        grp_files.Controls.Add(self.aota_listbox)

        self.aota_preview_label = Label()
        self.aota_preview_label.Text = "D/R: -"
        self.aota_preview_label.Location = Point(315, 180)
        self.aota_preview_label.Size = Size(285, 40)
        self.aota_preview_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.aota_preview_label)

        lbl_report = Label()
        lbl_report.Text = "AOTA Report:"
        lbl_report.Location = Point(615, 89)
        lbl_report.Size = Size(120, 20)
        grp_files.Controls.Add(lbl_report)

        self.report_count_label = Label()
        self.report_count_label.Text = "No folder"
        self.report_count_label.Location = Point(735, 89)
        self.report_count_label.Size = Size(185, 20)
        self.report_count_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.report_count_label)

        self.report_listbox = ListBox()
        self.report_listbox.Location = Point(615, 112)
        self.report_listbox.Size = Size(305, 65)
        self.report_listbox.SelectionMode = SelectionMode.One
        self.report_listbox.SelectedIndexChanged += self.selection_changed
        grp_files.Controls.Add(self.report_listbox)

        self.report_preview_label = Label()
        self.report_preview_label.Text = "D/R: -"
        self.report_preview_label.Location = Point(615, 180)
        self.report_preview_label.Size = Size(305, 40)
        self.report_preview_label.ForeColor = Color.Gray
        grp_files.Controls.Add(self.report_preview_label)

        lbl_pyote = Label()
        lbl_pyote.Text = "PyOTE Metrics:"
        lbl_pyote.Location = Point(15, 165)
        lbl_pyote.Size = Size(120, 20)
        lbl_pyote.Visible = False
        grp_files.Controls.Add(lbl_pyote)
        self._lbl_pyote_header = lbl_pyote

        self.pyote_count_label = Label()
        self.pyote_count_label.Text = "No folder"
        self.pyote_count_label.Location = Point(135, 165)
        self.pyote_count_label.Size = Size(200, 20)
        self.pyote_count_label.ForeColor = Color.Gray
        self.pyote_count_label.Visible = False
        grp_files.Controls.Add(self.pyote_count_label)

        lbl_pyote_event = Label()
        lbl_pyote_event.Text = "Events:"
        lbl_pyote_event.Location = Point(460, 165)
        lbl_pyote_event.Size = Size(60, 20)
        lbl_pyote_event.Visible = False
        grp_files.Controls.Add(lbl_pyote_event)
        self._lbl_pyote_event_header = lbl_pyote_event

        self.pyote_event_count_label = Label()
        self.pyote_event_count_label.Text = "-"
        self.pyote_event_count_label.Location = Point(525, 165)
        self.pyote_event_count_label.Size = Size(210, 20)
        self.pyote_event_count_label.ForeColor = Color.Gray
        self.pyote_event_count_label.Visible = False
        grp_files.Controls.Add(self.pyote_event_count_label)

        self.pyote_listbox = ListBox()
        self.pyote_listbox.Location = Point(15, 185)
        self.pyote_listbox.Size = Size(430, 55)
        self.pyote_listbox.SelectionMode = SelectionMode.One
        self.pyote_listbox.SelectedIndexChanged += self._pyote_file_selection_changed
        self.pyote_listbox.Visible = False
        grp_files.Controls.Add(self.pyote_listbox)

        self.pyote_event_listbox = ListBox()
        self.pyote_event_listbox.Location = Point(460, 185)
        self.pyote_event_listbox.Size = Size(460, 55)
        self.pyote_event_listbox.SelectionMode = SelectionMode.One
        self.pyote_event_listbox.SelectedIndexChanged += self._pyote_event_selection_changed
        self.pyote_event_listbox.Visible = False
        grp_files.Controls.Add(self.pyote_event_listbox)

        self.pyote_preview_label = Label()
        self.pyote_preview_label.Text = "D/R: -"
        self.pyote_preview_label.Location = Point(15, 244)
        self.pyote_preview_label.Size = Size(905, 22)
        self.pyote_preview_label.ForeColor = Color.Gray
        self.pyote_preview_label.Visible = False
        grp_files.Controls.Add(self.pyote_preview_label)

        # Timestamp Check sub-panel
        grp_ts_check = GroupBox()
        grp_ts_check.Text = "Timestamp Check"
        grp_ts_check.Location = Point(15, 231)
        grp_ts_check.Size = Size(910, 105)
        grp_files.Controls.Add(grp_ts_check)

        self.lbl_ts_delayed = Label()
        self.lbl_ts_delayed.Text = "Delayed frames: -"
        self.lbl_ts_delayed.Location = Point(15, 22)
        self.lbl_ts_delayed.Size = Size(165, 20)
        grp_ts_check.Controls.Add(self.lbl_ts_delayed)

        self.lbl_ts_late = Label()
        self.lbl_ts_late.Text = "Late frames: -"
        self.lbl_ts_late.Location = Point(190, 22)
        self.lbl_ts_late.Size = Size(140, 20)
        grp_ts_check.Controls.Add(self.lbl_ts_late)

        self.lbl_ts_status = Label()
        self.lbl_ts_status.Text = "Status: -"
        self.lbl_ts_status.Location = Point(340, 22)
        self.lbl_ts_status.Size = Size(200, 20)
        grp_ts_check.Controls.Add(self.lbl_ts_status)

        self.lbl_ts_minmax = Label()
        self.lbl_ts_minmax.Text = "Deviation: -"
        self.lbl_ts_minmax.Location = Point(550, 22)
        self.lbl_ts_minmax.Size = Size(345, 20)
        grp_ts_check.Controls.Add(self.lbl_ts_minmax)

        btn_ts_explain = Button()
        btn_ts_explain.Text = "Explain..."
        btn_ts_explain.Location = Point(15, 48)
        btn_ts_explain.Size = Size(80, 28)
        btn_ts_explain.Click += self._ts_explain_click
        grp_ts_check.Controls.Add(btn_ts_explain)

        self.btn_ts_inspect = Button()
        self.btn_ts_inspect.Text = "Inspect Timestamps..."
        self.btn_ts_inspect.Location = Point(105, 48)
        self.btn_ts_inspect.Size = Size(160, 28)
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

        self.lbl_delay_check = Label()
        self.lbl_delay_check.Text = "Tangra delay: -"
        self.lbl_delay_check.Location = Point(15, 80)
        self.lbl_delay_check.Size = Size(880, 22)
        grp_ts_check.Controls.Add(self.lbl_delay_check)

        # --- Folder picker row ---
        lbl_folder_info2 = Label()
        lbl_folder_info2.Text = "Observation files folder:"
        lbl_folder_info2.Location = Point(15, 28)
        lbl_folder_info2.Size = Size(160, 20)
        grp_files.Controls.Add(lbl_folder_info2)

        self.folder_textbox = TextBox()
        self.folder_textbox.Location = Point(180, 25)
        self.folder_textbox.Size = Size(490, 22)
        self.folder_textbox.ReadOnly = True
        grp_files.Controls.Add(self.folder_textbox)

        btn_browse = Button()
        btn_browse.Text = "Browse..."
        btn_browse.Location = Point(680, 23)
        btn_browse.Size = Size(85, 28)
        btn_browse.Click += self._browse_folder_click
        grp_files.Controls.Add(btn_browse)

        # --- Rescan row ---
        lbl_rescan = Label()
        lbl_rescan.Text = "After saving corrected files to the folder, refresh the lists:"
        lbl_rescan.Location = Point(15, 56)
        lbl_rescan.Size = Size(580, 20)
        lbl_rescan.ForeColor = Color.Gray
        grp_files.Controls.Add(lbl_rescan)

        btn_rescan = Button()
        btn_rescan.Text = "\u21bb  Rescan Folder"
        btn_rescan.Location = Point(603, 53)
        btn_rescan.Size = Size(135, 26)
        btn_rescan.Click += self._on_rescan_click
        grp_files.Controls.Add(btn_rescan)

        # --- D/R event selector sub-panel ---
        _is_ntp_timing = self.timing_ctx.get('is_ntp', False) or self.timing_ctx.get('is_gps', False)
        _grp_dr_height = 110 if _is_ntp_timing else 80

        grp_dr = GroupBox()
        grp_dr.Text = "Select Event to Report"
        grp_dr.Location = Point(15, 346)
        grp_dr.Size = Size(910, _grp_dr_height)
        grp_files.Controls.Add(grp_dr)

        lbl_dr_select = Label()
        lbl_dr_select.Text = "D/R Event:"
        lbl_dr_select.Location = Point(10, 22)
        lbl_dr_select.Size = Size(95, 20)
        grp_dr.Controls.Add(lbl_dr_select)

        self.combo_dr_event = ComboBox()
        self.combo_dr_event.Location = Point(110, 20)
        self.combo_dr_event.Size = Size(790, 25)
        self.combo_dr_event.DropDownStyle = ComboBoxStyle.DropDownList
        self.combo_dr_event.SelectedIndexChanged += self._dr_event_selected
        grp_dr.Controls.Add(self.combo_dr_event)

        self.lbl_dr_d_info = Label()
        self.lbl_dr_d_info.Text = "D: -"
        self.lbl_dr_d_info.Location = Point(10, 52)
        self.lbl_dr_d_info.Size = Size(355, 20)
        grp_dr.Controls.Add(self.lbl_dr_d_info)

        self.lbl_dr_r_info = Label()
        self.lbl_dr_r_info.Text = "R: -"
        self.lbl_dr_r_info.Location = Point(370, 52)
        self.lbl_dr_r_info.Size = Size(340, 20)
        grp_dr.Controls.Add(self.lbl_dr_r_info)

        self.lbl_dr_duration = Label()
        self.lbl_dr_duration.Text = ""
        self.lbl_dr_duration.Location = Point(716, 52)
        self.lbl_dr_duration.Size = Size(188, 20)
        self.lbl_dr_duration.ForeColor = Color.Gray
        grp_dr.Controls.Add(self.lbl_dr_duration)

        if _is_ntp_timing:
            self.chk_ntp_uncertainty = CheckBox()
            self.chk_ntp_uncertainty.Text = "Include NTP Offset Uncertainty"
            self.chk_ntp_uncertainty.Location = Point(10, 80)
            self.chk_ntp_uncertainty.Size = Size(280, 22)
            self.chk_ntp_uncertainty.CheckedChanged += self._on_ntp_uncertainty_changed
            grp_dr.Controls.Add(self.chk_ntp_uncertainty)

            self.lbl_ntp_info = Label()
            self.lbl_ntp_info.Text = "NTP: not yet analysed"
            self.lbl_ntp_info.Location = Point(300, 82)
            self.lbl_ntp_info.Size = Size(600, 20)
            self.lbl_ntp_info.ForeColor = Color.Gray
            grp_dr.Controls.Add(self.lbl_ntp_info)

        grp_files.Size = Size(940, 346 + _grp_dr_height + 10)
        y_pos += 346 + _grp_dr_height + 20

        # Compute the height consumed by the (mutually exclusive) section-4 timing info panel
        _tc = self.timing_ctx
        if _tc.get('is_gps_cmos', False):
            _timing_panel_h = 55
        elif _tc.get('is_gps', False):
            _timing_panel_h = 45
        elif _tc.get('is_analog_vti', False):
            _timing_panel_h = 120
        elif _tc.get('is_ntp', False):
            _timing_panel_h = 4  # no info panel shown for NTP; small gap only
        else:
            _timing_panel_h = 40

        # ===== SECTION 4: PER-METHOD INFO PANELS (mutually exclusive) =====
        self._pnl_timing_gps_cmos = Panel()
        self._pnl_timing_gps_cmos.Location = Point(10, y_pos)
        self._pnl_timing_gps_cmos.Size = Size(940, 55)
        self._pnl_timing_gps_cmos.Visible = False
        main_panel.Controls.Add(self._pnl_timing_gps_cmos)

        lbl_gps_cmos_info1 = Label()
        lbl_gps_cmos_info1.Text = (
            "\u24d8  GPS-integrated cameras (QHY 174GPS, ASTRID, DVTI-cam, Touptek GPS) "
            "embed accurate GPS-synchronized timestamps."
        )
        lbl_gps_cmos_info1.Location = Point(15, 5)
        lbl_gps_cmos_info1.Size = Size(910, 20)
        self._pnl_timing_gps_cmos.Controls.Add(lbl_gps_cmos_info1)

        lbl_gps_cmos_info2 = Label()
        lbl_gps_cmos_info2.Text = (
            "\u2714  No timing corrections required. "
            "Any report form (NA, TT, SODIS) is compatible."
        )
        lbl_gps_cmos_info2.Location = Point(15, 28)
        lbl_gps_cmos_info2.Size = Size(910, 20)
        lbl_gps_cmos_info2.ForeColor = Color.Green
        self._pnl_timing_gps_cmos.Controls.Add(lbl_gps_cmos_info2)

        self._pnl_timing_gps = Panel()
        self._pnl_timing_gps.Location = Point(10, y_pos)
        self._pnl_timing_gps.Size = Size(940, 45)
        self._pnl_timing_gps.Visible = False
        main_panel.Controls.Add(self._pnl_timing_gps)

        lbl_gps_info = Label()
        lbl_gps_info.Text = (
            "\u24d8  GPS flash (Camilleri method) correction support is planned for Phase 2.\n"
            "   The flash overlay delay measurement is performed in the gps-timing-analysis tool."
        )
        lbl_gps_info.Location = Point(15, 5)
        lbl_gps_info.Size = Size(900, 35)
        lbl_gps_info.ForeColor = Color.Gray
        self._pnl_timing_gps.Controls.Add(lbl_gps_info)

        self._pnl_timing_analog_vti = Panel()
        self._pnl_timing_analog_vti.Location = Point(10, y_pos)
        self._pnl_timing_analog_vti.Size = Size(940, 120)
        self._pnl_timing_analog_vti.Visible = False
        main_panel.Controls.Add(self._pnl_timing_analog_vti)

        lbl_analog_tool = Label()
        lbl_analog_tool.Text = "Analysis tool used to determine D and R times:"
        lbl_analog_tool.Location = Point(15, 5)
        lbl_analog_tool.Size = Size(360, 22)
        self._pnl_timing_analog_vti.Controls.Add(lbl_analog_tool)

        self._rad_analog_aota = RadioButton()
        self._rad_analog_aota.Text = "AOTA"
        self._rad_analog_aota.Location = Point(380, 3)
        self._rad_analog_aota.Size = Size(75, 22)
        self._rad_analog_aota.Checked = self.timing_ctx.get('rad_analog_aota_checked', True)
        self._rad_analog_aota.CheckedChanged += self._on_analog_tool_changed
        self._pnl_timing_analog_vti.Controls.Add(self._rad_analog_aota)

        self._rad_analog_pyote = RadioButton()
        self._rad_analog_pyote.Text = "PyOTE"
        self._rad_analog_pyote.Location = Point(465, 3)
        self._rad_analog_pyote.Size = Size(80, 22)
        self._rad_analog_pyote.Checked = not self.timing_ctx.get('rad_analog_aota_checked', True)
        self._rad_analog_pyote.CheckedChanged += self._on_analog_tool_changed
        self._pnl_timing_analog_vti.Controls.Add(self._rad_analog_pyote)

        self._lbl_vti_info = Label()
        self._lbl_vti_info.Text = ""
        self._lbl_vti_info.Location = Point(15, 32)
        self._lbl_vti_info.Size = Size(910, 82)
        self._pnl_timing_analog_vti.Controls.Add(self._lbl_vti_info)

        self._pnl_timing_other = Panel()
        self._pnl_timing_other.Location = Point(10, y_pos)
        self._pnl_timing_other.Size = Size(940, 40)
        self._pnl_timing_other.Visible = True
        main_panel.Controls.Add(self._pnl_timing_other)

        lbl_other_info = Label()
        lbl_other_info.Text = (
            "\u24d8  Timing corrections are not applied by OM for this method. "
            "Apply corrections in Tangra/PyOTE, PyMovie, or the NA reporting form "
            "before generating this report."
        )
        lbl_other_info.Location = Point(15, 8)
        lbl_other_info.Size = Size(900, 30)
        lbl_other_info.ForeColor = Color.Gray
        self._pnl_timing_other.Controls.Add(lbl_other_info)

        y_pos += _timing_panel_h + 10

        # ===== SECTION 5: OBSERVATION RESULT =====
        grp_obs_type = GroupBox()
        grp_obs_type.Text = "4. Observation Result"
        grp_obs_type.Location = Point(10, y_pos)
        grp_obs_type.Size = Size(940, 165)
        main_panel.Controls.Add(grp_obs_type)

        self.rb_positive = RadioButton()
        self.rb_positive.Text = "Positive - Observed occultation (D/R source required)"
        self.rb_positive.Location = Point(20, 25)
        self.rb_positive.Size = Size(480, 25)
        self.rb_positive.Checked = True
        self.rb_positive.CheckedChanged += self._obs_type_changed
        grp_obs_type.Controls.Add(self.rb_positive)

        self.rb_negative = RadioButton()
        self.rb_negative.Text = "Negative - No occultation occurred (D/R not required)"
        self.rb_negative.Location = Point(20, 50)
        self.rb_negative.Size = Size(480, 25)
        self.rb_negative.CheckedChanged += self._obs_type_changed
        grp_obs_type.Controls.Add(self.rb_negative)

        self.rb_unsure = RadioButton()
        self.rb_unsure.Text = "Unsure - Possible event but uncertain (D/R source required)"
        self.rb_unsure.Location = Point(20, 75)
        self.rb_unsure.Size = Size(480, 25)
        self.rb_unsure.CheckedChanged += self._obs_type_changed
        grp_obs_type.Controls.Add(self.rb_unsure)

        self.rb_not_observed = RadioButton()
        self.rb_not_observed.Text = "Not observed, failed or clouded out (D/R not required)"
        self.rb_not_observed.Location = Point(20, 100)
        self.rb_not_observed.Size = Size(500, 25)
        self.rb_not_observed.CheckedChanged += self._obs_type_changed
        grp_obs_type.Controls.Add(self.rb_not_observed)

        # RHS: Optional OWC report entry
        self._lbl_owc_head = Label()
        self._lbl_owc_head.Text = "Occult Watcher Cloud"
        self._lbl_owc_head.Font = Font(self._lbl_owc_head.Font.FontFamily,
                                       self._lbl_owc_head.Font.Size, FontStyle.Bold)
        self._lbl_owc_head.Location = Point(530, 20)
        self._lbl_owc_head.Size = Size(200, 20)
        grp_obs_type.Controls.Add(self._lbl_owc_head)

        lbl_owc_report = Label()
        lbl_owc_report.Text = "Report Type:"
        lbl_owc_report.Location = Point(530, 44)
        lbl_owc_report.Size = Size(84, 20)
        grp_obs_type.Controls.Add(lbl_owc_report)

        self.cmb_owc_report_type = ComboBox()
        self.cmb_owc_report_type.Location = Point(618, 42)
        self.cmb_owc_report_type.Size = Size(160, 23)
        self.cmb_owc_report_type.DropDownStyle = ComboBoxStyle.DropDownList
        self.cmb_owc_report_type.Items.AddRange(Array[object]([
            'Positive', 'Miss', 'Not Observed', 'Clouded Out', 'Failed'
        ]))
        self.cmb_owc_report_type.SelectedIndex = 0
        self.cmb_owc_report_type.SelectedIndexChanged += self._on_owc_report_type_changed
        grp_obs_type.Controls.Add(self.cmb_owc_report_type)

        self.lbl_owc_duration = Label()
        self.lbl_owc_duration.Text = "Duration (s):"
        self.lbl_owc_duration.Location = Point(530, 70)
        self.lbl_owc_duration.Size = Size(84, 20)
        grp_obs_type.Controls.Add(self.lbl_owc_duration)

        self.txt_owc_duration = TextBox()
        self.txt_owc_duration.Location = Point(618, 68)
        self.txt_owc_duration.Size = Size(85, 22)
        grp_obs_type.Controls.Add(self.txt_owc_duration)

        self.lbl_owc_comment = Label()
        self.lbl_owc_comment.Text = "Comment (max 30):"
        self.lbl_owc_comment.Location = Point(530, 96)
        self.lbl_owc_comment.Size = Size(110, 20)
        grp_obs_type.Controls.Add(self.lbl_owc_comment)

        self.txt_owc_comment = TextBox()
        self.txt_owc_comment.Location = Point(644, 94)
        self.txt_owc_comment.Size = Size(166, 22)
        self.txt_owc_comment.MaxLength = 30
        grp_obs_type.Controls.Add(self.txt_owc_comment)

        self.btn_submit_owc = Button()
        self.btn_submit_owc.Text = "Submit to OWC"
        self.btn_submit_owc.Location = Point(812, 92)
        self.btn_submit_owc.Size = Size(112, 26)
        self.btn_submit_owc.Click += self._submit_owc_click
        grp_obs_type.Controls.Add(self.btn_submit_owc)

        self.lbl_owc_status = Label()
        self.lbl_owc_status.Text = ""
        self.lbl_owc_status.Location = Point(530, 124)
        self.lbl_owc_status.Size = Size(394, 34)
        self.lbl_owc_status.ForeColor = Color.Gray
        grp_obs_type.Controls.Add(self.lbl_owc_status)

        self._sync_owc_report_type_from_observation_type(force=True)
        self._refresh_owc_duration_ui()

        y_pos += 175

        # ===== SECTION 6: CONDITIONS =====
        grp_conditions = GroupBox()
        grp_conditions.Text = "5. Conditions"
        grp_conditions.Location = Point(10, y_pos)
        grp_conditions.Size = Size(940, 80)
        main_panel.Controls.Add(grp_conditions)

        lbl_clouds = Label()
        lbl_clouds.Text = "Clouds:"
        lbl_clouds.Location = Point(20, 30)
        lbl_clouds.Size = Size(80, 20)
        grp_conditions.Controls.Add(lbl_clouds)

        self.combo_clouds = ComboBox()
        self.combo_clouds.Location = Point(110, 28)
        self.combo_clouds.Size = Size(180, 25)
        self.combo_clouds.DropDownStyle = ComboBoxStyle.DropDownList
        self.combo_clouds.Items.AddRange(Array[object]([
            "Clear", "Fog", "Thin cloud < 2", "Thick cloud > 2",
            "Broken cloud", "Star faint", "Averted vision"
        ]))
        self.combo_clouds.SelectedIndex = 0
        grp_conditions.Controls.Add(self.combo_clouds)

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

        lbl_other_cond = Label()
        lbl_other_cond.Text = "Other Conditions:"
        lbl_other_cond.Location = Point(600, 30)
        lbl_other_cond.Size = Size(130, 20)
        grp_conditions.Controls.Add(lbl_other_cond)

        self.txt_other_conditions = TextBox()
        self.txt_other_conditions.Location = Point(730, 28)
        self.txt_other_conditions.Size = Size(190, 25)
        grp_conditions.Controls.Add(self.txt_other_conditions)

        # ===== BOTTOM BUTTONS =====
        self.status_label = Label()
        self.status_label.Text = "Please complete all sections above"
        self.status_label.Location = Point(20, 880)
        self.status_label.Size = Size(475, 20)
        self.status_label.ForeColor = Color.Gray
        self.Controls.Add(self.status_label)

        self.chk_include_station = CheckBox()
        self.chk_include_station.Text = "Include Station Name in Filenames"
        self.chk_include_station.Location = Point(500, 882)
        self.chk_include_station.Size = Size(215, 20)
        self.chk_include_station.Checked = False
        self.Controls.Add(self.chk_include_station)

        self._btn_why_blocked = Button()
        self._btn_why_blocked.Text = "?"
        self._btn_why_blocked.Location = Point(723, 879)
        self._btn_why_blocked.Size = Size(24, 22)
        self._btn_why_blocked.Click += self._on_why_blocked_click
        self.Controls.Add(self._btn_why_blocked)

        self.btn_generate = Button()
        self.btn_generate.Text = "Generate Report"
        self.btn_generate.Location = Point(750, 875)
        self.btn_generate.Size = Size(140, 35)
        self.btn_generate.Enabled = False
        self.btn_generate.Click += self._generate_click
        self.Controls.Add(self.btn_generate)
        self.AcceptButton = self.btn_generate

        btn_back = Button()
        btn_back.Text = "\u2190 Back"
        btn_back.Location = Point(900, 875)
        btn_back.Size = Size(80, 35)
        btn_back.Click += self._back_click
        self.Controls.Add(btn_back)
        self.CancelButton = btn_back

        self._setup_tooltips()

    # ------------------------------------------------------------------
    # Timing panel visibility
    # ------------------------------------------------------------------

    def _apply_timing_panels(self):
        """Show the correct per-method info panel based on timing_ctx."""
        is_ntp = self.timing_ctx.get('is_ntp', False)
        is_gps = self.timing_ctx.get('is_gps', False)
        is_gps_cmos = self.timing_ctx.get('is_gps_cmos', False)
        is_analog_vti = self.timing_ctx.get('is_analog_vti', False)
        self._pnl_timing_gps.Visible = is_gps
        self._pnl_timing_gps_cmos.Visible = is_gps_cmos
        self._pnl_timing_analog_vti.Visible = is_analog_vti
        self._pnl_timing_other.Visible = not (is_ntp or is_gps or is_gps_cmos or is_analog_vti)
        self._lbl_phase_b_separator.Visible = is_ntp or is_gps
        if is_analog_vti:
            self._update_analog_vti_warnings()

    def _on_analog_tool_changed(self, sender, e):
        if not sender.Checked:
            return
        self._update_analog_vti_warnings()
        self.update_button_state()

    def _update_analog_vti_warnings(self):
        if not hasattr(self, '_lbl_vti_info'):
            return
        is_aota = self._rad_analog_aota.Checked
        is_na = self.timing_ctx.get('rb_na_checked', False)
        is_tt_sodis = self.timing_ctx.get('rb_tt_checked', False) or self.timing_ctx.get('rb_sodis_checked', False)
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
            self._lbl_vti_info.Text = "\u2714  NA report form will automatically apply VTI corrections to D/R times."
            self._lbl_vti_info.ForeColor = Color.Green
        elif not is_aota and is_tt_sodis:
            self._lbl_vti_info.Text = (
                "\u26d4  INCOMPATIBLE: PyOTE does not apply VTI corrections, and TT/SODIS forms "
                "do not apply them automatically. D/R times will be uncorrected.\n"
                "Use the NA report form, or use AOTA to analyse the light curve."
            )
            self._lbl_vti_info.ForeColor = Color.Red
        else:
            self._lbl_vti_info.Text = "Report format was selected in the previous dialog."
            self._lbl_vti_info.ForeColor = Color.Gray

    # ------------------------------------------------------------------
    # Folder / scan
    # ------------------------------------------------------------------

    def _browse_folder_click(self, sender, e):
        dialog = FolderBrowserDialog()
        dialog.Description = "Select folder containing AOTA and light curve CSV files"
        if self.current_folder and os.path.exists(self.current_folder):
            dialog.SelectedPath = self.current_folder
        if dialog.ShowDialog() == DialogResult.OK:
            folder_path = dialog.SelectedPath
            self.current_folder = folder_path
            self.folder_textbox.Text = folder_path
            parent_folder = os.path.dirname(folder_path)
            self.config.set_last_report_folder(parent_folder)
            self.scan_folder(folder_path)

    def scan_folder(self, folder_path):
        """Scan folder for AOTA, CSV, AOTA Report, and PyOTE metrics files."""
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
        self._dr_events = []
        self.combo_dr_event.Items.Clear()
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

            def _count_label(n, noun):
                if n == 0:
                    return 'No {0} found'.format(noun)
                return '{0} file{1} found'.format(n, 's' if n > 1 else '')

            self.aota_count_label.Text = _count_label(len(self.aota_files), 'AOTA files')
            self.csv_count_label.Text = _count_label(len(self.csv_files), 'CSV files')
            self.report_count_label.Text = _count_label(len(self.aota_report_files), 'Report files')
            self.pyote_count_label.Text = _count_label(len(self.pyote_files), 'PyOTE metrics')

            if self.aota_files:
                self.aota_listbox.SelectedIndex = 0
            if self.csv_files:
                self.csv_listbox.SelectedIndex = 0
            if self.aota_report_files:
                self.report_listbox.SelectedIndex = 0
            if self.pyote_files:
                self.pyote_listbox.SelectedIndex = 0

            self._update_all_previews()
            self.update_button_state()

        except Exception as ex:
            MessageBox.Show(
                "Error scanning folder:\n\n{0}".format(str(ex)),
                "Scan Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
            self.aota_count_label.Text = "Error"
            self.csv_count_label.Text = "Error"
            self.report_count_label.Text = "Error"
            self.pyote_count_label.Text = "Error"

    def _on_rescan_click(self, sender, e):
        if self.current_folder and os.path.isdir(self.current_folder):
            self.scan_folder(self.current_folder)
        else:
            self.status_label.Text = "No folder selected — browse to your folder first"
            self.status_label.ForeColor = Color.OrangeRed

    # ------------------------------------------------------------------
    # File selection / previews
    # ------------------------------------------------------------------

    def selection_changed(self, sender, e):
        self._update_all_previews()
        self.update_button_state()

    def _update_all_previews(self):
        self._update_tangra_preview()
        self._update_aota_xml_preview()
        self._update_aota_report_preview()
        self._update_pyote_preview()
        self._populate_dr_combo()

    def _format_time_value(self, value):
        if value is None:
            return "-"
        if isinstance(value, str):
            text = value.strip()
            return text if text else "-"
        try:
            if float(value).is_integer():
                return str(int(value))
            return ("{0:.3f}".format(float(value))).rstrip('0').rstrip('.')
        except Exception:
            return str(value)

    def _format_hms(self, hours, minutes, seconds):
        return "{0}:{1}:{2}".format(
            self._format_time_value(hours),
            self._format_time_value(minutes),
            self._format_time_value(seconds))

    def _count_dp(self, val):
        """Return number of decimal places in val (str or float), preserving trailing zeros in strings."""
        if val is None:
            return 2
        s = str(val).strip()
        if '.' in s:
            dec = s.split('.')[1]
            return len(dec) if dec else 0
        return 0

    @staticmethod
    def _fmt_unc(val):
        """Format an uncertainty value to 2 significant figures, stripping trailing zeros.

        Examples: 0.2000001 -> '0.2',  0.15 -> '0.15',  1.234 -> '1.2',  3.5 -> '3.5'
        """
        try:
            return '{:.2g}'.format(float(val))
        except (TypeError, ValueError):
            return str(val)

    def _update_tangra_preview(self):
        try:
            if self.csv_listbox.SelectedIndex < 0:
                self.csv_preview_label.Text = "Observing times: -"
                self._reset_timestamp_check()
                return
            tangra_path = self.csv_files[self.csv_listbox.SelectedIndex]
            import light_curve_reader as lcr
            summary = lcr.get_observation_summary(tangra_path, percentiles=[1, 99])
            self._ts_summary = summary
            if summary is None:
                self.csv_preview_label.Text = "Observing times: not found"
                self._reset_timestamp_check()
                return
            start_time = summary.get('start_time', '')
            end_time = summary.get('end_time', '')
            if start_time or end_time:
                self.csv_preview_label.Text = "Start: {0}\nEnd: {1}".format(
                    self._format_time_value(start_time),
                    self._format_time_value(end_time))
            else:
                self.csv_preview_label.Text = "Observing times: not found"
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
            self._update_delay_check(summary)
        except Exception:
            self.csv_preview_label.Text = "Observing times: unable to extract"
            self._reset_timestamp_check()

    def _update_aota_xml_preview(self):
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
            n = len(valid_events)
            evt = valid_events[0]
            d_seconds = evt.d_seconds_str if evt.d_seconds_str is not None else evt.d_seconds
            r_seconds = evt.r_seconds_str if evt.r_seconds_str is not None else evt.r_seconds
            d_time = self._format_hms(evt.d_hours, evt.d_minutes, d_seconds)
            r_time = self._format_hms(evt.r_hours, evt.r_minutes, r_seconds)
            if n == 1:
                self.aota_preview_label.Text = "D: {0}\nR: {1}".format(d_time, r_time)
            else:
                self.aota_preview_label.Text = "{0} events\nFirst: D {1}  R {2}".format(n, d_time, r_time)
        except Exception:
            self.aota_preview_label.Text = "D/R: unable to extract"

    def _update_aota_report_preview(self):
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
            self.pyote_event_count_label.Text = "{0} event{1}".format(count, 's' if count != 1 else '')
            self.pyote_event_listbox.SelectedIndex = 0
        except Exception:
            self.pyote_event_count_label.Text = "Error reading file"
            self.pyote_preview_label.Text = "D/R: unable to read"
        self._populate_dr_combo()
        self.update_button_state()

    def _pyote_event_selection_changed(self, sender, e):
        self._update_pyote_preview()
        self.update_button_state()

    def _update_pyote_preview(self):
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

    def _populate_dr_combo(self):
        """Rebuild the D/R event combo from all currently selected source files."""
        self.combo_dr_event.Items.Clear()
        self._dr_events = []

        # Events from the selected AOTA Report file (listed first — preferred source)
        if self.report_listbox.SelectedIndex >= 0:
            report_file_idx = self.report_listbox.SelectedIndex
            report_path = self.aota_report_files[report_file_idx]
            try:
                import aota_report_parser as arp
                parsed_report = arp.parse_aota_report(report_path)
                if parsed_report and parsed_report.get('events'):
                    n = len(parsed_report['events'])
                    for ev_idx in range(n):
                        summary = arp.get_event_summary(parsed_report, ev_idx)
                        if not summary:
                            continue
                        try:
                            d_time = self._format_hms(
                                summary.get('d_hours'), summary.get('d_minutes'), summary.get('d_seconds'))
                            r_time = self._format_hms(
                                summary.get('r_hours'), summary.get('r_minutes'), summary.get('r_seconds'))
                            dh = int(summary.get('d_hours') or 0)
                            dm = int(summary.get('d_minutes') or 0)
                            ds = float(summary.get('d_seconds') or 0.0)
                            d_sec = dh * 3600.0 + dm * 60.0 + ds if (dh or dm or ds) else None
                            rh = int(summary.get('r_hours') or 0)
                            rm = int(summary.get('r_minutes') or 0)
                            rs = float(summary.get('r_seconds') or 0.0)
                            r_sec = rh * 3600.0 + rm * 60.0 + rs if (rh or rm or rs) else None
                        except Exception:
                            d_time = r_time = '?'
                            d_sec = r_sec = None
                        prefix = 'AOTA Report' if n == 1 else 'AOTA Report ev.{0}'.format(ev_idx + 1)
                        d_unc_rpt = summary.get('d_uncertainty')
                        r_unc_rpt = summary.get('r_uncertainty')
                        self._dr_events.append({
                            'source': 'aota_report',
                            'report_file_idx': report_file_idx,
                            'event_idx': ev_idx,
                            'd_seconds': d_sec,
                            'r_seconds': r_sec,
                            'd_time_str': d_time,
                            'r_time_str': r_time,
                            'd_uncertainty': float(d_unc_rpt) if d_unc_rpt is not None else None,
                            'r_uncertainty': float(r_unc_rpt) if r_unc_rpt is not None else None,
                            'd_unc_dp': self._count_dp(d_unc_rpt),
                            'r_unc_dp': self._count_dp(r_unc_rpt),
                        })
                        self.combo_dr_event.Items.Add(
                            '{0}  D {1}  R {2}'.format(prefix, d_time, r_time))
            except Exception:
                pass

        # Events from the selected AOTA XML file
        if self.aota_listbox.SelectedIndex >= 0:
            aota_file_idx = self.aota_listbox.SelectedIndex
            aota_path = self.aota_files[aota_file_idx]
            try:
                from aota_parser import parse_aota_file
                aota_result = parse_aota_file(aota_path)
                if aota_result:
                    valid_events = aota_result.get_valid_events()
                    n = len(valid_events)
                    for ev_idx, evt in enumerate(valid_events):
                        try:
                            d_s = evt.d_seconds_str if evt.d_seconds_str is not None else evt.d_seconds
                            r_s = evt.r_seconds_str if evt.r_seconds_str is not None else evt.r_seconds
                            d_time = self._format_hms(evt.d_hours, evt.d_minutes, d_s)
                            r_time = self._format_hms(evt.r_hours, evt.r_minutes, r_s)
                            d_s_f = float(d_s) if d_s is not None else 0.0
                            r_s_f = float(r_s) if r_s is not None else 0.0
                            d_sec = int(evt.d_hours or 0) * 3600.0 + int(evt.d_minutes or 0) * 60.0 + d_s_f
                            r_sec = int(evt.r_hours or 0) * 3600.0 + int(evt.r_minutes or 0) * 60.0 + r_s_f
                        except Exception:
                            d_time = r_time = '?'
                            d_sec = r_sec = None
                        prefix = 'AOTA' if n == 1 else 'AOTA ev.{0}'.format(ev_idx + 1)
                        d_unc = float(evt.d_error) if evt.d_error is not None else None
                        r_unc = float(evt.r_error) if evt.r_error is not None else None
                        self._dr_events.append({
                            'source': 'aota',
                            'aota_file_idx': aota_file_idx,
                            'event_idx': ev_idx,
                            'd_seconds': d_sec,
                            'r_seconds': r_sec,
                            'd_time_str': d_time,
                            'r_time_str': r_time,
                            'd_uncertainty': d_unc,
                            'r_uncertainty': r_unc,
                            'd_unc_dp': self._count_dp(evt.d_error_str if evt.d_error_str is not None else evt.d_error),
                            'r_unc_dp': self._count_dp(evt.r_error_str if evt.r_error_str is not None else evt.r_error),
                        })
                        self.combo_dr_event.Items.Add(
                            '{0}  D {1}  R {2}'.format(prefix, d_time, r_time))
            except Exception:
                pass

        # Events from PyOTE metrics (uses already-loaded self.pyote_events)
        if self.pyote_events and self.pyote_listbox.SelectedIndex >= 0:
            pyote_file_idx = self.pyote_listbox.SelectedIndex
            for ev_idx, record in enumerate(self.pyote_events):
                d_time = record.get('D time', '?')
                r_time = record.get('R time', '?')
                uncertainty = record.get('time err +/-secs', None)
                d_sec = r_sec = None
                try:
                    parts = str(d_time).split(':')
                    if len(parts) == 3:
                        d_sec = int(parts[0]) * 3600.0 + int(parts[1]) * 60.0 + float(parts[2])
                except Exception:
                    pass
                try:
                    parts = str(r_time).split(':')
                    if len(parts) == 3:
                        r_sec = int(parts[0]) * 3600.0 + int(parts[1]) * 60.0 + float(parts[2])
                except Exception:
                    pass
                display = 'PyOTE  D {0}  R {1}'.format(d_time, r_time)
                if uncertainty is not None:
                    display += '  \u00b1{0}s'.format(uncertainty)
                unc_f = float(uncertainty) if uncertainty is not None else None
                unc_dp = self._count_dp(uncertainty)
                # Strip brackets from PyOTE bracketed time strings for display in info panel
                def _strip_brackets(t):
                    return str(t).strip().strip('[]')
                self._dr_events.append({
                    'source': 'pyote',
                    'pyote_file_idx': pyote_file_idx,
                    'pyote_event_idx': ev_idx,
                    'd_seconds': d_sec,
                    'r_seconds': r_sec,
                    'd_time_str': _strip_brackets(d_time),
                    'r_time_str': _strip_brackets(r_time),
                    'd_uncertainty': unc_f,
                    'r_uncertainty': unc_f,
                    'd_unc_dp': unc_dp,
                    'r_unc_dp': unc_dp,
                })
                self.combo_dr_event.Items.Add(display)

        if self._dr_events:
            self.combo_dr_event.SelectedIndex = 0
        else:
            self._d_time_seconds = None
            self._r_time_seconds = None
        self.update_button_state()

    def _dr_event_selected(self, sender, e):
        idx = self.combo_dr_event.SelectedIndex
        if idx < 0 or idx >= len(self._dr_events):
            self._d_time_seconds = None
            self._r_time_seconds = None
            self._update_dr_info_panel()
            self._refresh_owc_duration_ui()
            return
        rec = self._dr_events[idx]
        self._d_time_seconds = rec.get('d_seconds')
        self._r_time_seconds = rec.get('r_seconds')
        self._update_dr_info_panel()
        self._refresh_owc_duration_ui()
        self.update_button_state()

    def _on_ntp_uncertainty_changed(self, sender, e):
        self._update_dr_info_panel()

    def _update_dr_info_panel(self):
        """Refresh the D/R time display labels, optionally combining NTP uncertainty in quadrature."""
        import math

        idx = self.combo_dr_event.SelectedIndex
        if idx < 0 or idx >= len(self._dr_events):
            self.lbl_dr_d_info.Text = "D: -"
            self.lbl_dr_r_info.Text = "R: -"
            if hasattr(self, 'lbl_dr_duration'):
                self.lbl_dr_duration.Text = ""
            if hasattr(self, 'lbl_ntp_info'):
                self.lbl_ntp_info.ForeColor = Color.Gray
            self.ntp_comment = None
            return

        rec = self._dr_events[idx]
        d_time = rec.get('d_time_str') or '-'
        r_time = rec.get('r_time_str') or '-'
        d_unc = rec.get('d_uncertainty')
        r_unc = rec.get('r_uncertainty')
        d_dp = rec.get('d_unc_dp', 2)
        r_dp = rec.get('r_unc_dp', 2)

        is_ntp = self.timing_ctx.get('is_ntp', False) or self.timing_ctx.get('is_gps', False)
        ntp_off_ms = self.timing_ctx.get('ntp_offset_ms', 0.0) or 0.0
        ntp_unc_ms = self.timing_ctx.get('ntp_uncertainty_ms', 0.0) or 0.0
        use_ntp = (is_ntp and hasattr(self, 'chk_ntp_uncertainty')
                   and self.chk_ntp_uncertainty.Checked)

        if use_ntp and ntp_unc_ms > 0:
            ntp_unc_s = ntp_unc_ms / 1000.0
            d_combined = math.sqrt(d_unc ** 2 + ntp_unc_s ** 2) if d_unc is not None else ntp_unc_s
            r_combined = math.sqrt(r_unc ** 2 + ntp_unc_s ** 2) if r_unc is not None else ntp_unc_s
            self.lbl_dr_d_info.Text = "D: {0}  \u00b1{1}s".format(
                d_time, self._fmt_unc(d_combined))
            self.lbl_dr_r_info.Text = "R: {0}  \u00b1{1}s".format(
                r_time, self._fmt_unc(r_combined))
            self.ntp_comment = (
                "NTP timing: offset {0:+.1f} ms, uncertainty \u00b1{1:.1f} ms (95%). "
                "NTP offset uncertainty added in quadrature to D/R uncertainties."
            ).format(ntp_off_ms, ntp_unc_ms)
        else:
            if d_unc is not None:
                self.lbl_dr_d_info.Text = "D: {0}  \u00b1{1}s".format(
                    d_time, self._fmt_unc(d_unc))
            else:
                self.lbl_dr_d_info.Text = "D: {0}".format(d_time)
            if r_unc is not None:
                self.lbl_dr_r_info.Text = "R: {0}  \u00b1{1}s".format(
                    r_time, self._fmt_unc(r_unc))
            else:
                self.lbl_dr_r_info.Text = "R: {0}".format(r_time)
            self.ntp_comment = None

        # D/R duration
        if hasattr(self, 'lbl_dr_duration'):
            d_sec_val = rec.get('d_seconds')
            r_sec_val = rec.get('r_seconds')
            if d_sec_val is not None and r_sec_val is not None:
                dur = r_sec_val - d_sec_val
                if dur >= 0:
                    self.lbl_dr_duration.Text = "Dur: {0}s".format('{:.2g}'.format(dur))
                    self.lbl_dr_duration.ForeColor = Color.Gray
                else:
                    self.lbl_dr_duration.Text = ""
            else:
                self.lbl_dr_duration.Text = ""

        if hasattr(self, 'lbl_ntp_info'):
            if is_ntp and ntp_unc_ms > 0:
                self.lbl_ntp_info.Text = "NTP: {0:+.1f} ms  \u00b1{1:.1f} ms (95%)".format(
                    ntp_off_ms, ntp_unc_ms)
                self.lbl_ntp_info.ForeColor = Color.Gray
                self.chk_ntp_uncertainty.Enabled = True
            elif is_ntp:
                self.lbl_ntp_info.Text = "NTP: not yet analysed \u2014 run NTP analysis in the previous dialog"
                self.lbl_ntp_info.ForeColor = Color.OrangeRed
                self.chk_ntp_uncertainty.Enabled = False
                self.chk_ntp_uncertainty.Checked = False

    # ------------------------------------------------------------------
    # Timestamp check helpers
    # ------------------------------------------------------------------

    def _reset_timestamp_check(self):
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
        self.lbl_delay_check.Text = "Tangra delay: -"
        self.lbl_delay_check.ForeColor = Color.Gray

    def _check_event_in_window(self, summary):
        try:
            event_time_str = self.event.event_time if (self.event and hasattr(self.event, 'event_time')) else ''
            if not event_time_str or not summary:
                self.lbl_ts_event_warning.Visible = False
                return
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

    def _update_delay_check(self, summary):
        """Compare the Tangra CSV's recorded acquisition delay against the expected total delay from D2."""
        expected_ms = self.timing_ctx.get('total_delay_ms', None)
        if not self.timing_ctx.get('is_ntp', False) or expected_ms is None:
            self.lbl_delay_check.Text = "Tangra delay: (not applicable for this timing method)"
            self.lbl_delay_check.ForeColor = Color.Gray
            return
        actual_ms = summary.get('acquisition_delay', None) if summary else None
        if actual_ms is None:
            self.lbl_delay_check.Text = (
                "Tangra delay: NOT SET  \u2717  Expected: {0:.1f} ms"
                " \u2014 enter this in Tangra \u2192 Camera and Timing Corrections".format(expected_ms))
            self.lbl_delay_check.ForeColor = Color.Red
            return
        diff = expected_ms - actual_ms
        if abs(diff) < 1.0:
            self.lbl_delay_check.Text = (
                "Tangra delay: {0:.1f} ms  \u2713  Matches calculated total delay".format(actual_ms))
            self.lbl_delay_check.ForeColor = Color.Green
        else:
            self.lbl_delay_check.Text = (
                "Tangra delay: {0:.1f} ms  \u2717  Expected: {1:.1f} ms"
                "  (needs adjustment of {2:+.1f} ms)".format(actual_ms, expected_ms, diff))
            self.lbl_delay_check.ForeColor = Color.Red

    def _ts_explain_click(self, sender, e):
        MessageBox.Show(
            "Timestamp Check analyses recording frame timing for irregularities.\n\n"
            "Delayed frames: frames where the interval is more than 10% longer than "
            "the median (minor timing slip).\n\n"
            "Late frames: frames where the interval is more than 90% longer than the "
            "median. This typically means one or more frames were dropped.\n\n"
            "If these anomalies fall completely outside the D/R event window they have "
            "no impact on the reported event times and can be ignored.",
            "Timestamp Check Explained", MessageBoxButtons.OK, MessageBoxIcon.Information)

    def _ts_inspect_click(self, sender, e):
        if self.csv_listbox.SelectedIndex < 0:
            return
        tangra_path = self.csv_files[self.csv_listbox.SelectedIndex]
        try:
            event_secs = None
            try:
                event_time_str = self.event.event_time if (self.event and hasattr(self.event, 'event_time')) else ''
                if event_time_str:
                    t_part = event_time_str.split('T')[-1].rstrip('Z').split('.')[0]
                    p = t_part.split(':')
                    event_secs = int(p[0]) * 3600 + int(p[1]) * 60 + float(p[2])
            except Exception:
                event_secs = None
            from comprehensive_report_dialog import TimestampInspectorForm
            form = TimestampInspectorForm(tangra_path, self._d_time_seconds, self._r_time_seconds, event_secs)
            form.ShowDialog(self)
        except Exception as ex:
            MessageBox.Show(
                "Error opening Timestamp Inspector:\n\n" + str(ex),
                "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)

    # ------------------------------------------------------------------
    # Observation type
    # ------------------------------------------------------------------

    def _obs_type_changed(self, sender, e):
        self._sync_owc_report_type_from_observation_type()
        self._refresh_owc_duration_ui()
        self.update_button_state()

    def _on_owc_report_type_changed(self, sender, e):
        if not self._suppress_owc_combo_event:
            self._owc_type_user_override = True
        self._refresh_owc_duration_ui()

    def _sync_owc_report_type_from_observation_type(self, force=False):
        """Keep OWC type aligned with observation result unless user overrides."""
        if not hasattr(self, 'cmb_owc_report_type'):
            return
        if self._owc_type_user_override and not force:
            return

        obs_type = self._get_obs_type()
        target_ui = 'Positive'
        if obs_type == 'Negative':
            target_ui = 'Miss'
        elif obs_type == 'Unsure':
            # "Unsure" still indicates a potential positive with D/R timing.
            target_ui = 'Positive'
        elif obs_type == 'NotObserved':
            target_ui = 'Not Observed'

        try:
            self._suppress_owc_combo_event = True
            self.cmb_owc_report_type.SelectedItem = target_ui
        finally:
            self._suppress_owc_combo_event = False

    def _is_owc_positive_selected(self):
        if not hasattr(self, 'cmb_owc_report_type'):
            return False
        try:
            return str(self.cmb_owc_report_type.SelectedItem) == 'Positive'
        except Exception:
            return False

    def _get_selected_dr_duration(self):
        idx = self.combo_dr_event.SelectedIndex
        if idx < 0 or idx >= len(self._dr_events):
            return None
        rec = self._dr_events[idx]
        d_sec = rec.get('d_seconds')
        r_sec = rec.get('r_seconds')
        if d_sec is None or r_sec is None:
            return None
        try:
            dur = float(r_sec) - float(d_sec)
            if dur < 0:
                return None
            return dur
        except Exception:
            return None

    def _refresh_owc_duration_ui(self):
        if not hasattr(self, 'lbl_owc_duration') or not hasattr(self, 'txt_owc_duration'):
            return
        is_positive = self._is_owc_positive_selected()
        self.lbl_owc_duration.Visible = is_positive
        self.txt_owc_duration.Visible = is_positive
        if not is_positive:
            self.txt_owc_duration.Text = ''
            return

        dur = self._get_selected_dr_duration()
        if dur is None:
            self.txt_owc_duration.Text = ''
        else:
            self.txt_owc_duration.Text = ('{0:.3f}'.format(float(dur))).rstrip('0').rstrip('.')

    def _map_owc_report_type(self):
        """Map UI labels to EventProcessor.submit_owc_report observation_type."""
        try:
            ui_value = str(self.cmb_owc_report_type.SelectedItem)
        except Exception:
            ui_value = ''
        mapping = {
            'Positive': 'Positive',
            'Miss': 'Miss',
            'Not Observed': 'NotObserved',
            'Clouded Out': 'Clouded',
            'Failed': 'Failed',
        }
        return mapping.get(ui_value)

    def _validate_owc_submission_inputs(self):
        """Validate current OWC inputs and return normalized values.

        Returns:
            tuple: (obs_type, duration_s, comment, error_message)
        """
        obs_type = self._map_owc_report_type()
        if obs_type is None:
            return None, None, None, 'Select an OWC report type.'

        duration_s = None
        if obs_type == 'Positive':
            raw_duration = (self.txt_owc_duration.Text or '').strip()
            if not raw_duration:
                return None, None, None, 'Duration is required for Positive reports.'
            try:
                duration_s = float(raw_duration)
                if duration_s <= 0:
                    raise ValueError()
            except Exception:
                return None, None, None, 'Duration must be a positive number of seconds.'

        comment = (self.txt_owc_comment.Text or '').strip()
        if len(comment) > 30:
            return None, None, None, 'Comment must be 30 characters or fewer.'

        try:
            comment.encode('ascii')
        except Exception:
            return None, None, None, 'Comment must contain ASCII only.'

        allowed = re.compile(r"^[A-Za-z0-9 .,;:!?\-_'()/]*$")
        if comment and not allowed.match(comment):
            return None, None, None, 'Use letters/numbers and basic punctuation only.'

        return obs_type, duration_s, comment, None

    def _get_owc_submission_signature(self):
        """Return a stable signature for current OWC submission inputs."""
        obs_type, duration_s, comment, _ = self._validate_owc_submission_inputs()
        if not obs_type:
            return None
        duration_token = ''
        if duration_s is not None:
            duration_token = '{0:.6f}'.format(float(duration_s))
        return '{0}|{1}|{2}'.format(obs_type, duration_token, comment)

    def _submit_owc_report(self, update_status_label=True):
        """Submit to OWC using current RHS controls. Returns True on success."""
        if self.config is None:
            if update_status_label:
                self.lbl_owc_status.Text = 'Config unavailable.'
                self.lbl_owc_status.ForeColor = Color.OrangeRed
            return False

        obs_type, duration_s, comment, error_message = self._validate_owc_submission_inputs()
        if error_message:
            if update_status_label:
                self.lbl_owc_status.Text = error_message
                self.lbl_owc_status.ForeColor = Color.OrangeRed
            return False

        try:
            from events import EventProcessor

            self.btn_submit_owc.Enabled = False
            if update_status_label:
                self.lbl_owc_status.Text = 'Submitting to OWC...'
                self.lbl_owc_status.ForeColor = Color.Gray

            event_payload = {
                'ow_eventid': getattr(self.event, 'ow_eventid', None),
                'ow_api_eventid': getattr(self.event, 'ow_api_eventid', None),
                'owc_station_id': getattr(self.event, 'owc_station_id', None),
                'owcloudurl': getattr(self.event, 'owcloudurl', None),
                'latitude': getattr(self.event, 'latitude', None),
                'longitude': getattr(self.event, 'longitude', None),
                'elevation': getattr(self.event, 'elevation', None),
            }

            result = EventProcessor.submit_owc_report(
                self.config,
                event_payload,
                observation_type=obs_type,
                comment=comment,
                duration_s=duration_s,
                update_location=False,
            )

            if result.get('success'):
                persisted_ok = self._persist_owc_status(obs_type)
                self._last_submitted_owc_signature = self._get_owc_submission_signature()
                if update_status_label:
                    if persisted_ok:
                        self.lbl_owc_status.Text = 'Submitted to OWC successfully.'
                        self.lbl_owc_status.ForeColor = Color.Green
                    else:
                        self.lbl_owc_status.Text = 'Submitted to OWC. Warning: status could not be saved locally.'
                        self.lbl_owc_status.ForeColor = Color.OrangeRed
                return True

            if update_status_label:
                self.lbl_owc_status.Text = 'OWC submit failed: {0}'.format(result.get('error') or 'Unknown error')
                self.lbl_owc_status.ForeColor = Color.OrangeRed
            return False
        except Exception as ex:
            if update_status_label:
                self.lbl_owc_status.Text = 'OWC submit exception: {0}'.format(str(ex))
                self.lbl_owc_status.ForeColor = Color.OrangeRed
            return False
        finally:
            self.btn_submit_owc.Enabled = True

    def _auto_submit_owc_if_needed(self):
        """Submit OWC on Generate when never submitted or inputs changed since submit."""
        current_signature = self._get_owc_submission_signature()
        if current_signature and current_signature == self._last_submitted_owc_signature:
            return True

        ok = self._submit_owc_report(update_status_label=True)
        if not ok:
            MessageBox.Show(
                'Could not submit the OWC report.\n\n'
                'Fix the OWC values or press Submit to OWC and resolve the error before generating.',
                'OWC Submit Failed',
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return False
        return True

    def _get_owc_status_display(self, obs_type):
        """Return user-facing grid/status label for OWC report values."""
        mapping = {
            'Positive': 'Positive',
            'Miss': 'Miss',
            'Negative': 'Miss',
            'NotObserved': 'Unsure No Obs',
            'Failed': 'Failed',
            'Clouded': 'Clouded',
        }
        return mapping.get(str(obs_type or ''), str(obs_type or ''))

    def _persist_owc_status(self, obs_type):
        """Persist OWC report status to the current event and JSON event stores."""
        display_status = self._get_owc_status_display(obs_type)

        # Update in-memory event immediately so callers can refresh grid state.
        try:
            self.event.owc_report_status = obs_type
            self.event.status = display_status
            if hasattr(self.event, 'original_data') and isinstance(self.event.original_data, dict):
                self.event.original_data['owc_report_status'] = obs_type
                self.event.original_data['status'] = display_status
        except Exception:
            pass

        event_id = getattr(self.event, 'event_id', None)
        if not event_id or self.config is None:
            return False

        try:
            from events import EventProcessor
            save_succeeded = False
            for occ_file in (
                self.config.get_occultations_file(),
                self.config.get_latest_occultations_file(),
            ):
                try:
                    events_data = EventProcessor.load_occultations(occ_file, self.config)
                    if not events_data:
                        continue
                    changed = False
                    for entry in events_data:
                        if entry.get('id') == event_id:
                            entry['owc_report_status'] = obs_type
                            entry['status'] = display_status
                            changed = True
                            break
                    if changed:
                        if EventProcessor.save_occultations(events_data, occ_file, self.config):
                            save_succeeded = True
                except Exception:
                    continue
            return save_succeeded
        except Exception:
            return False

    def _submit_owc_click(self, sender, e):
        """Submit selected OWC report type from the RHS Observation Result panel."""
        self._submit_owc_report(update_status_label=True)

    def _get_obs_type(self):
        if self.rb_positive.Checked:
            return "Positive"
        if self.rb_negative.Checked:
            return "Negative"
        if self.rb_unsure.Checked:
            return "Unsure"
        if hasattr(self, 'rb_not_observed') and self.rb_not_observed.Checked:
            return "NotObserved"
        return None

    # ------------------------------------------------------------------
    # Button state
    # ------------------------------------------------------------------

    def update_button_state(self):
        csv_selected = self.csv_listbox.SelectedIndex >= 0
        dr_selected = (self.combo_dr_event.SelectedIndex >= 0 and bool(self._dr_events))
        obs_type = self._get_obs_type()

        missing = []
        if not csv_selected:
            missing.append("light curve CSV file")
        if obs_type in ("Positive", "Unsure") and not dr_selected:
            missing.append("D/R event source (select an AOTA, AOTA Report, or PyOTE file)")

        if missing:
            self.status_label.Text = "Missing: " + ", ".join(missing)
            self.status_label.ForeColor = Color.Red
            self.btn_generate.Enabled = False
            self._btn_why_blocked.Visible = True
        else:
            self.status_label.Text = "Ready to generate report"
            self.status_label.ForeColor = Color.Green
            self.btn_generate.Enabled = True
            self._btn_why_blocked.Visible = False

    # ------------------------------------------------------------------
    # Generate / Back
    # ------------------------------------------------------------------

    def _generate_click(self, sender, e):
        obs_type = self._get_obs_type()

        if self.csv_listbox.SelectedIndex >= 0:
            self.selected_tangra_path = self.csv_files[self.csv_listbox.SelectedIndex]
        else:
            MessageBox.Show("Please select a light curve CSV file.",
                            "No CSV File", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return

        self.selected_aota_path = None
        self.selected_aota_event_index = -1
        self.selected_aota_report_path = None
        self.selected_aota_report_event_index = -1
        self.selected_pyote_path = None
        self.selected_pyote_event_index = -1
        if self.combo_dr_event.SelectedIndex >= 0 and self._dr_events:
            rec = self._dr_events[self.combo_dr_event.SelectedIndex]
            src = rec.get('source')
            if src == 'aota':
                self.selected_aota_path = self.aota_files[rec['aota_file_idx']]
                self.selected_aota_event_index = rec['event_idx']
            elif src == 'aota_report':
                self.selected_aota_report_path = self.aota_report_files[rec['report_file_idx']]
                self.selected_aota_report_event_index = rec['event_idx']
            elif src == 'pyote':
                self.selected_pyote_path = self.pyote_files[rec['pyote_file_idx']]
                self.selected_pyote_event_index = rec['pyote_event_idx']

        if obs_type in ("Positive", "Unsure"):
            if not self.selected_aota_path and not self.selected_aota_report_path and not self.selected_pyote_path:
                MessageBox.Show(
                    "Either AOTA file, AOTA Report, or PyOTE Metrics is required for {0} observations.".format(obs_type),
                    "Missing Event Data", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return

        if self.combo_clouds.SelectedIndex >= 0 and self.combo_clouds.SelectedItem:
            self.clouds = str(self.combo_clouds.SelectedItem)
        if self.combo_stability.SelectedIndex >= 0 and self.combo_stability.SelectedItem:
            self.stability = str(self.combo_stability.SelectedItem)
        self.other_conditions = self.txt_other_conditions.Text.strip() or None
        # Keep report generator compatibility: use Negative for non-observed outcomes.
        self.observation_type = 'Negative' if obs_type == 'NotObserved' else obs_type
        self.include_station_name = self.chk_include_station.Checked

        if not self._auto_submit_owc_if_needed():
            return

        if not self._check_analog_vti_before_generate():
            return

        self.DialogResult = DialogResult.OK
        self.Close()

    def _check_analog_vti_before_generate(self):
        is_analog_vti = self.timing_ctx.get('is_analog_vti', False)
        if not is_analog_vti:
            return True
        is_aota = self._rad_analog_aota.Checked
        is_na = self.timing_ctx.get('rb_na_checked', False)
        is_tt_sodis = self.timing_ctx.get('rb_tt_checked', False) or self.timing_ctx.get('rb_sodis_checked', False)

        if not is_aota and is_tt_sodis:
            MessageBox.Show(
                "This combination cannot produce correctly-timed results:\n\n"
                "    \u2022  Analysis tool: PyOTE\n"
                "    \u2022  Report form: TT or SODIS\n"
                "    \u2022  Camera timing: Analog video + VTI\n\n"
                "PyOTE does NOT apply VTI timing corrections to D/R times.\n"
                "The TT and SODIS report forms do NOT apply them automatically either.\n\n"
                "To fix this, choose one of:\n"
                "    \u2022  Change the report form to IOTA NA, OR\n"
                "    \u2022  Re-analyse the light curve using AOTA instead of PyOTE.",
                "Incompatible Combination \u2014 Cannot Generate",
                MessageBoxButtons.OK, MessageBoxIcon.Stop)
            return False

        if is_aota and is_na:
            from comprehensive_report_dialog import VTIDoubleCorrectConfirmDialog
            dlg = VTIDoubleCorrectConfirmDialog(self.theme_manager)
            dlg.ShowDialog(self)
            return dlg.confirmed

        return True

    def _back_click(self, sender, e):
        self.DialogResult = DialogResult.Cancel
        self.Close()

    def _on_why_blocked_click(self, sender, e):
        text = getattr(self.status_label, 'Text', '')
        if not text or text == "Ready to generate report":
            return
        MessageBox.Show(text, "Why is Generate blocked?",
                        MessageBoxButtons.OK, MessageBoxIcon.Information)

    # ------------------------------------------------------------------
    # Tooltips
    # ------------------------------------------------------------------

    def _setup_tooltips(self):
        self._tooltip = ToolTip()
        self._tooltip.AutoPopDelay = 12000
        self._tooltip.InitialDelay = 400
        self._tooltip.ReshowDelay = 200
        self._tooltip.SetToolTip(self.rb_positive,
            "Observed both disappearance and reappearance.\nAOTA, AOTA Report, or PyOTE result required.")
        self._tooltip.SetToolTip(self.rb_negative,
            "No occultation was detected.\nAOTA is optional; a light curve CSV is still required.")
        self._tooltip.SetToolTip(self.rb_unsure,
            "A possible event occurred but the result is uncertain.\nAOTA, AOTA Report, or PyOTE result required.")
        self._tooltip.SetToolTip(self.rb_not_observed,
            "No usable observation (not observed, failed, or clouded out).\n"
            "Default OWC type is Not Observed; you can change it to Failed or Clouded Out.")
