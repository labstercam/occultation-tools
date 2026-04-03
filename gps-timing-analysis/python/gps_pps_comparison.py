#!/usr/bin/env ipy
"""GPS PPS Comparison Analysis tool — IronPython 3.4 Windows Forms.

Provides:
  GPSPPSPreflightDialog  — modal dialog to confirm the GPS PPS server and
                           validate its noselect state before running comparison.
  GPSPPSComparisonForm   — main comparison form with 3 plots (Phase 3).
"""

import os
import sys

try:
    import clr  # type: ignore
except ImportError:
    clr = None

if clr is not None:
    clr.AddReference("System")
    clr.AddReference("System.Drawing")
    clr.AddReference("System.Windows.Forms")

    drawing_module = __import__(
        "System.Drawing",
        fromlist=["Color", "Font", "FontStyle", "Pen", "Point", "Rectangle", "Size", "SolidBrush"],
    )
    forms_module = __import__(
        "System.Windows.Forms",
        fromlist=[
            "AnchorStyles",
            "Application",
            "Button",
            "BorderStyle",
            "CheckBox",
            "ColumnStyle",
            "ComboBox",
            "ComboBoxStyle",
            "DialogResult",
            "DockStyle",
            "FixedPanel",
            "FolderBrowserDialog",
            "Form",
            "FormBorderStyle",
            "FormWindowState",
            "FormStartPosition",
            "Label",
            "ListBox",
            "MessageBox",
            "MessageBoxButtons",
            "MessageBoxIcon",
            "PictureBox",
            "RowStyle",
            "ScrollBars",
            "SizeType",
            "SplitContainer",
            "TableLayoutPanel",
            "TextBox",
        ],
    )

    Color = drawing_module.Color
    Font = drawing_module.Font
    FontStyle = drawing_module.FontStyle
    Pen = drawing_module.Pen
    Point = drawing_module.Point
    Rectangle = drawing_module.Rectangle
    Size = drawing_module.Size
    SolidBrush = drawing_module.SolidBrush

    AnchorStyles = forms_module.AnchorStyles
    Application = forms_module.Application
    Button = forms_module.Button
    BorderStyle = forms_module.BorderStyle
    CheckBox = forms_module.CheckBox
    ColumnStyle = forms_module.ColumnStyle
    ComboBox = forms_module.ComboBox
    ComboBoxStyle = forms_module.ComboBoxStyle
    DialogResult = forms_module.DialogResult
    DockStyle = forms_module.DockStyle
    FixedPanel = forms_module.FixedPanel
    FolderBrowserDialog = forms_module.FolderBrowserDialog
    Form = forms_module.Form
    FormBorderStyle = forms_module.FormBorderStyle
    FormWindowState = forms_module.FormWindowState
    FormStartPosition = forms_module.FormStartPosition
    Label = forms_module.Label
    ListBox = forms_module.ListBox
    MessageBox = forms_module.MessageBox
    MessageBoxButtons = forms_module.MessageBoxButtons
    MessageBoxIcon = forms_module.MessageBoxIcon
    PictureBox = forms_module.PictureBox
    RowStyle = forms_module.RowStyle
    ScrollBars = forms_module.ScrollBars
    SizeType = forms_module.SizeType
    SplitContainer = forms_module.SplitContainer
    TableLayoutPanel = forms_module.TableLayoutPanel
    TextBox = forms_module.TextBox

else:
    Color = None
    Font = None
    FontStyle = None
    Pen = None
    Point = None
    Rectangle = None
    Size = None
    SolidBrush = None
    AnchorStyles = None
    Application = None
    Button = None
    BorderStyle = None
    CheckBox = None
    ColumnStyle = None
    ComboBox = None
    ComboBoxStyle = None
    DialogResult = None
    DockStyle = None
    FixedPanel = None
    FolderBrowserDialog = None
    Form = object
    FormBorderStyle = None
    FormWindowState = None
    FormStartPosition = None
    Label = None
    ListBox = None
    MessageBox = None
    MessageBoxButtons = None
    MessageBoxIcon = None
    PictureBox = None
    RowStyle = None
    ScrollBars = None
    SizeType = None
    SplitContainer = None
    TableLayoutPanel = None
    TextBox = None


_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
import ntp_analysis_core as ntp_core
from ntp_analysis_core import *  # noqa: F401,F403

# Color palette for server addresses — identical to analyze_ntp_timing_accuracy.py
# so both tools assign the same color to the same server when both are open.
SERVER_COLORS = [
    Color.FromArgb(31, 119, 180),   # blue
    Color.FromArgb(255, 127, 14),   # orange
    Color.FromArgb(44, 160, 44),    # green
    Color.FromArgb(214, 39, 40),    # red
    Color.FromArgb(148, 103, 189),  # purple
    Color.FromArgb(140, 86, 75),    # brown
    Color.FromArgb(227, 119, 194),  # pink
    Color.FromArgb(127, 127, 127),  # gray
]


def get_server_color(server_address, server_to_color):
    """Get or assign a color for a server address."""
    if server_address not in server_to_color:
        idx = len(server_to_color) % len(SERVER_COLORS)
        server_to_color[server_address] = SERVER_COLORS[idx]
    return server_to_color[server_address]


# ---------------------------------------------------------------------------
# GPSPPSPreflightDialog
# ---------------------------------------------------------------------------

class GPSPPSPreflightDialog(Form):
    """Modal dialog to confirm the GPS PPS reference server before running comparison.

    The caller passes all peerstats rows for the selected dataset.  The dialog
    scans for any 127.127.*.* NTP refclock address, shows each one with its
    record count and observed select codes, and provides a traffic-light
    indicator of whether the server was held in the noselect state.

    After ShowDialog() returns DialogResult.OK, read the output properties:
        .selected_gps_addr  : str                       confirmed GPS PPS address
        .noselect_intervals : list[(datetime, datetime)] valid analysis windows
        .noselect_status    : dict                       from check_gps_pps_noselect_status()

    Traffic-light colour logic
    --------------------------
    Green  : all records in noselect state (is_strictly_noselect == True)
    Amber  : >= 90% of records in noselect state
    Red    : < 90% of records in noselect state

    In all cases OK is enabled once a server is selected; the caller may then
    choose to abort based on the reported status.
    """

    _TRAFFIC_GREEN = Color.FromArgb(46, 160, 73)
    _TRAFFIC_AMBER = Color.FromArgb(200, 148, 0)
    _TRAFFIC_RED   = Color.FromArgb(185, 50,  50)
    _TRAFFIC_NONE  = Color.FromArgb(210, 210, 210)

    def __init__(self, peer_rows):
        # -------------------------------------------------------------------
        # Output properties — set when user confirms with OK.
        # -------------------------------------------------------------------
        self.selected_gps_addr = None     # str
        self.noselect_intervals = []      # list[(datetime, datetime)]
        self.noselect_status = {}         # dict from check_gps_pps_noselect_status()

        # -------------------------------------------------------------------
        # Internal state
        # -------------------------------------------------------------------
        self._peer_rows = peer_rows
        # list[(addr, record_count)] sorted by count descending
        self._candidates = find_gps_pps_candidates(peer_rows)
        # Cached results from the most recently selected server
        self._cached_status = {}
        self._cached_intervals = []

        # -------------------------------------------------------------------
        # Form chrome
        # -------------------------------------------------------------------
        self.Text = "Select GPS PPS Reference Server"
        self.Size = Size(550, 520)
        self.MinimumSize = Size(480, 478)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False

        default_font = Font("Segoe UI", 9)
        bold_font    = Font("Segoe UI", 9, FontStyle.Bold)
        small_font   = Font("Segoe UI", 8)
        mono_font    = Font("Consolas", 9)

        m = 14       # left/right margin
        w = 498      # control width

        # --- Instruction label ---
        lbl_instruction = Label()
        lbl_instruction.Font = default_font
        lbl_instruction.Text = (
            "The following NTP refclock servers (127.127.*.*) were found in the "
            "selected dataset. Select the GPS or PPS server to use as the UTC "
            "ground-truth reference. It must be configured with the noselect "
            "option in ntp.conf."
        )
        lbl_instruction.Location = Point(m, 12)
        lbl_instruction.Size = Size(w, 60)
        self.Controls.Add(lbl_instruction)

        # --- Servers list header ---
        lbl_list_header = Label()
        lbl_list_header.Font = bold_font
        lbl_list_header.Text = "Refclock servers found in this dataset:"
        lbl_list_header.Location = Point(m, 80)
        lbl_list_header.Size = Size(w, 20)
        self.Controls.Add(lbl_list_header)

        # --- ListBox of candidates ---
        self.lst_servers = ListBox()
        self.lst_servers.Font = mono_font
        self.lst_servers.Location = Point(m, 104)
        self.lst_servers.Size = Size(w, 110)
        self.lst_servers.SelectedIndexChanged += self._on_server_selected
        self.Controls.Add(self.lst_servers)

        # --- Status section ---
        lbl_status_header = Label()
        lbl_status_header.Font = bold_font
        lbl_status_header.Text = "Server noselect status:"
        lbl_status_header.Location = Point(m, 228)
        lbl_status_header.Size = Size(w, 20)
        self.Controls.Add(lbl_status_header)

        # Traffic-light label — BackColor driven by noselect status
        self.lbl_status_light = Label()
        self.lbl_status_light.Font = default_font
        self.lbl_status_light.Text = "Select a server above to see its noselect status."
        self.lbl_status_light.Location = Point(m, 252)
        self.lbl_status_light.Size = Size(w, 28)
        self.lbl_status_light.BackColor = self._TRAFFIC_NONE
        self.Controls.Add(self.lbl_status_light)

        # Coverage summary (multiline — shows interval count and time span)
        self.lbl_coverage = Label()
        self.lbl_coverage.Font = default_font
        self.lbl_coverage.Text = ""
        self.lbl_coverage.Location = Point(m, 288)
        self.lbl_coverage.Size = Size(w, 62)
        self.Controls.Add(self.lbl_coverage)

        # Warning label (amber text) — shown when non-noselect records exist
        self.lbl_warning = Label()
        self.lbl_warning.Font = small_font
        self.lbl_warning.ForeColor = Color.FromArgb(160, 80, 0)
        self.lbl_warning.Text = ""
        self.lbl_warning.Location = Point(m, 358)
        self.lbl_warning.Size = Size(w, 52)
        self.Controls.Add(self.lbl_warning)

        # --- Buttons (right-aligned) ---
        # btn_ok  right edge: m + w = 512;  btn_ok left: 512 - 90 - 4 - 90 = 328
        # btn_cancel right edge: 512;  btn_cancel left: 512 - 90 = 422
        self.btn_ok = Button()
        self.btn_ok.Text = "OK"
        self.btn_ok.Size = Size(90, 28)
        self.btn_ok.Location = Point(m + w - 190, 426)
        self.btn_ok.Enabled = False
        self.btn_ok.Click += self._on_ok
        self.Controls.Add(self.btn_ok)

        self.btn_cancel = Button()
        self.btn_cancel.Text = "Cancel"
        self.btn_cancel.Size = Size(90, 28)
        self.btn_cancel.Location = Point(m + w - 96, 426)
        self.btn_cancel.Click += self._on_cancel
        self.Controls.Add(self.btn_cancel)

        self.AcceptButton = self.btn_ok
        self.CancelButton = self.btn_cancel

        # Populate list and pre-select single candidate
        self._populate_list()

    # -----------------------------------------------------------------------
    # List population
    # -----------------------------------------------------------------------

    def _populate_list(self):
        self.lst_servers.Items.Clear()
        if not self._candidates:
            self.lst_servers.Items.Add(
                "No GPS/PPS refclock (127.127.*.*) found in this dataset."
            )
            return

        for addr, count in self._candidates:
            # Show observed select codes alongside record count.
            # check_gps_pps_noselect_status returns select_code_counts with int keys.
            s = check_gps_pps_noselect_status(self._peer_rows, addr)
            codes = sorted(k for k in s.get("select_code_counts", {}).keys() if k >= 0)
            codes_str = ",".join(str(c) for c in codes) if codes else "?"
            self.lst_servers.Items.Add(
                "%-24s  %6d records   select codes seen: %s" % (addr, count, codes_str)
            )

        # Auto-select when there is exactly one candidate so the user sees
        # its status immediately without having to click.
        if len(self._candidates) == 1:
            self.lst_servers.SelectedIndex = 0

    # -----------------------------------------------------------------------
    # Event handlers
    # -----------------------------------------------------------------------

    def _on_server_selected(self, sender, event):
        idx = self.lst_servers.SelectedIndex
        if idx < 0 or not self._candidates or idx >= len(self._candidates):
            self._reset_status_display()
            self.btn_ok.Enabled = False
            return
        addr = self._candidates[idx][0]
        self._refresh_status(addr)

    def _on_ok(self, sender, event):
        idx = self.lst_servers.SelectedIndex
        if idx < 0 or not self._candidates or idx >= len(self._candidates):
            return
        # Publish output properties from the cached computation done
        # by _refresh_status so we don't recompute on OK click.
        self.selected_gps_addr = self._candidates[idx][0]
        self.noselect_status = self._cached_status
        self.noselect_intervals = self._cached_intervals
        self.DialogResult = DialogResult.OK
        self.Close()

    def _on_cancel(self, sender, event):
        self.DialogResult = DialogResult.Cancel
        self.Close()

    # -----------------------------------------------------------------------
    # Status display helpers
    # -----------------------------------------------------------------------

    def _reset_status_display(self):
        self.lbl_status_light.Text = "Select a server above to see its noselect status."
        self.lbl_status_light.BackColor = self._TRAFFIC_NONE
        self.lbl_status_light.ForeColor = Color.Black
        self.lbl_coverage.Text = ""
        self.lbl_warning.Text = ""

    def _refresh_status(self, addr):
        """Compute and display noselect status for *addr*; cache results."""
        # Phase 1 integration: check_gps_pps_noselect_status and
        # get_gps_pps_noselect_intervals are imported via 'from ntp_analysis_core import *'
        self._cached_status = check_gps_pps_noselect_status(self._peer_rows, addr)
        self._cached_intervals = get_gps_pps_noselect_intervals(self._peer_rows, addr)

        fraction = self._cached_status.get("noselect_fraction", 0.0)

        # --- Traffic-light colour and message ---
        if self._cached_status.get("is_strictly_noselect"):
            bg   = self._TRAFFIC_GREEN
            fg   = Color.White
            text = "All records in noselect state — clean GPS reference."
        elif fraction >= 0.90:
            bg   = self._TRAFFIC_AMBER
            fg   = Color.White
            text = (
                "Mostly noselect (%.1f%%) — analysis restricted to clean intervals."
                % (fraction * 100.0)
            )
        else:
            bg   = self._TRAFFIC_RED
            fg   = Color.White
            text = (
                "Significant selected periods — only %.1f%% of records in noselect state."
                % (fraction * 100.0)
            )

        self.lbl_status_light.BackColor = bg
        self.lbl_status_light.ForeColor = fg
        self.lbl_status_light.Text = text

        # --- Coverage summary ---
        intervals = self._cached_intervals
        coverage_hours = sum(
            (end - start).total_seconds() / 3600.0 for start, end in intervals
        )
        n = len(intervals)
        if n == 0:
            coverage_text = "No valid noselect intervals found in this dataset."
        else:
            lines = [
                "Noselect coverage: %.2f hrs across %d interval(s)" % (coverage_hours, n)
            ]
            for start, end in intervals[:3]:
                same_day = start.date() == end.date()
                end_str = (
                    end.strftime("%H:%M:%S")
                    if same_day
                    else end.strftime("%Y-%m-%d %H:%M")
                )
                lines.append(
                    "  %s  \u2013  %s" % (start.strftime("%Y-%m-%d %H:%M"), end_str)
                )
            if n > 3:
                lines.append("  ... and %d more interval(s)" % (n - 3))
            coverage_text = "\r\n".join(lines)

        self.lbl_coverage.Text = coverage_text

        # --- Warnings ---
        warnings = self._cached_status.get("warnings", [])
        self.lbl_warning.Text = "\r\n".join(warnings) if warnings else ""

        # Enable OK in all cases — user can see the status and decide whether
        # to proceed.  Red status is a warning, not a hard block.
        self.btn_ok.Enabled = True


# ---------------------------------------------------------------------------
# GPSPPSComparisonForm  (Phase 3)
# ---------------------------------------------------------------------------

class GPSPPSComparisonForm(Form):
    """Main GPS PPS comparison analysis window.

    Reads the same loopstats/peerstats files as AnalyzerForm, launches the
    GPSPPSPreflightDialog to confirm the GPS PPS reference server, then plots:
      Row 0 — NTP Server Delays          (per server, color-coded)
      Row 1 — UTC Error per Server       (offset − GPS PPS, per server, grey band)
      Row 2 — Selected Peer UTC Error    (single series, grey band, drift trend)

    The text report summarises per-server k=2 uncertainty and clock drift.
    """

    def __init__(self):
        # -------------------------------------------------------------------
        # Output / state
        # -------------------------------------------------------------------
        self._options_by_label = {}
        self._plot_data = {}
        self._last_loop_rows = []
        self._last_peer_rows = []
        self._comparison_result = None
        self._uncertainty_result = None
        self._drift_result = None
        # legend control lists – rebuilt after each analysis run
        self._delays_legend_controls = []
        self._offset_diffs_legend_controls = []

        # Known NTP servers for distance lookup (shared resource dir)
        _res = os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "resources"
        ))
        _known_path = os.path.join(_res, "national_utc_ntp_servers.json")
        self._known_servers = load_known_servers(_known_path)
        ntp_core._load_ip_location_cache(os.path.join(_res, "ip_location_cache.json"))

        # -------------------------------------------------------------------
        # Form chrome
        # -------------------------------------------------------------------
        self.Text = "GPS vs NTP Testing"
        self.Size = Size(1600, 960)
        self.MinimumSize = Size(1100, 700)
        self.StartPosition = FormStartPosition.CenterScreen
        self.WindowState = FormWindowState.Maximized

        default_font = Font("Segoe UI", 9)
        bold_font    = Font("Segoe UI", 9, FontStyle.Bold)

        split = SplitContainer()
        split.Dock = DockStyle.Fill
        split.FixedPanel = FixedPanel.Panel1
        split.SplitterWidth = 6
        self.Controls.Add(split)
        self._main_split = split
        self.Shown += self.on_form_shown
        split.Panel1.Resize += self.on_left_panel_resize

        lp = split.Panel1

        # ---- Title ----
        self.lbl_title = Label()
        self.lbl_title.Text = "GPS PPS Comparison Analysis"
        self.lbl_title.Font = Font("Segoe UI", 11, FontStyle.Bold)
        self.lbl_title.Location = Point(8, 8)
        self.lbl_title.Size = Size(440, 26)
        self.lbl_title.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.lbl_title)

        # ---- Log folder ----
        self.lbl_log = Label()
        self.lbl_log.Text = "NTP log folder:"
        self.lbl_log.Font = bold_font
        self.lbl_log.Location = Point(8, 44)
        self.lbl_log.Size = Size(200, 20)
        lp.Controls.Add(self.lbl_log)

        self.txt_log_folder = TextBox()
        self.txt_log_folder.Font = default_font
        self.txt_log_folder.Location = Point(8, 66)
        self.txt_log_folder.Size = Size(446, 24)
        self.txt_log_folder.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.txt_log_folder)

        self.btn_browse_log = Button()
        self.btn_browse_log.Text = "Browse..."
        self.btn_browse_log.Location = Point(8, 96)
        self.btn_browse_log.Size = Size(100, 28)
        self.btn_browse_log.Click += self.on_browse_log
        lp.Controls.Add(self.btn_browse_log)

        self.btn_scan = Button()
        self.btn_scan.Text = "Scan Datasets"
        self.btn_scan.Location = Point(114, 96)
        self.btn_scan.Size = Size(120, 28)
        self.btn_scan.Click += self.on_scan
        lp.Controls.Add(self.btn_scan)

        # ---- Day filter ----
        self.lbl_filter = Label()
        self.lbl_filter.Text = "Day filter (optional text / MJD / YYYYMMDD):"
        self.lbl_filter.Location = Point(8, 136)
        self.lbl_filter.Size = Size(440, 20)
        lp.Controls.Add(self.lbl_filter)

        self.txt_day_filter = TextBox()
        self.txt_day_filter.Location = Point(8, 158)
        self.txt_day_filter.Size = Size(328, 24)
        self.txt_day_filter.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.txt_day_filter)

        self.btn_apply_filter = Button()
        self.btn_apply_filter.Text = "Apply Filter"
        self.btn_apply_filter.Location = Point(342, 156)
        self.btn_apply_filter.Size = Size(112, 28)
        self.btn_apply_filter.Anchor = AnchorStyles.Top | AnchorStyles.Right
        self.btn_apply_filter.Click += self.on_scan
        lp.Controls.Add(self.btn_apply_filter)

        # ---- Dataset selector ----
        self.lbl_dataset = Label()
        self.lbl_dataset.Text = "Dataset:"
        self.lbl_dataset.Font = bold_font
        self.lbl_dataset.Location = Point(8, 198)
        self.lbl_dataset.Size = Size(200, 20)
        lp.Controls.Add(self.lbl_dataset)

        self.cmb_dataset = ComboBox()
        self.cmb_dataset.DropDownStyle = ComboBoxStyle.DropDownList
        self.cmb_dataset.Location = Point(8, 220)
        self.cmb_dataset.Size = Size(446, 24)
        self.cmb_dataset.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.cmb_dataset)

        # ---- Export ----
        self.chk_export = CheckBox()
        self.chk_export.Text = "Export JSON + CSV"
        self.chk_export.Location = Point(8, 258)
        self.chk_export.Size = Size(160, 24)
        self.chk_export.Checked = True
        self.chk_export.CheckedChanged += self.on_export_toggle
        lp.Controls.Add(self.chk_export)

        self.txt_export_folder = TextBox()
        self.txt_export_folder.Location = Point(8, 284)
        self.txt_export_folder.Size = Size(328, 24)
        self.txt_export_folder.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.txt_export_folder)

        self.btn_browse_export = Button()
        self.btn_browse_export.Text = "Browse..."
        self.btn_browse_export.Location = Point(342, 282)
        self.btn_browse_export.Size = Size(112, 28)
        self.btn_browse_export.Anchor = AnchorStyles.Top | AnchorStyles.Right
        self.btn_browse_export.Click += self.on_browse_export
        lp.Controls.Add(self.btn_browse_export)

        # ---- Observer coordinates ----
        self.lbl_observer = Label()
        self.lbl_observer.Text = "Observer location (decimal degrees):"
        self.lbl_observer.Location = Point(8, 322)
        self.lbl_observer.Size = Size(280, 20)
        lp.Controls.Add(self.lbl_observer)

        self.lbl_observer_lat = Label()
        self.lbl_observer_lat.Text = "Lat:"
        self.lbl_observer_lat.Location = Point(8, 347)
        self.lbl_observer_lat.Size = Size(28, 20)
        lp.Controls.Add(self.lbl_observer_lat)

        self.txt_observer_lat = TextBox()
        self.txt_observer_lat.Text = ""
        self.txt_observer_lat.Location = Point(36, 344)
        self.txt_observer_lat.Size = Size(80, 24)
        self.txt_observer_lat.Font = default_font
        lp.Controls.Add(self.txt_observer_lat)

        self.lbl_observer_lon = Label()
        self.lbl_observer_lon.Text = "Lon:"
        self.lbl_observer_lon.Location = Point(126, 347)
        self.lbl_observer_lon.Size = Size(28, 20)
        lp.Controls.Add(self.lbl_observer_lon)

        self.txt_observer_lon = TextBox()
        self.txt_observer_lon.Text = ""
        self.txt_observer_lon.Location = Point(154, 344)
        self.txt_observer_lon.Size = Size(80, 24)
        self.txt_observer_lon.Font = default_font
        lp.Controls.Add(self.txt_observer_lon)

        self.lbl_observer_note = Label()
        self.lbl_observer_note.Text = "Used to compute server distance for delay correction"
        self.lbl_observer_note.Location = Point(8, 372)
        self.lbl_observer_note.Size = Size(360, 20)
        lp.Controls.Add(self.lbl_observer_note)

        # ---- Run Comparison button (prominent) ----
        self.btn_run = Button()
        self.btn_run.Text = "Run Comparison"
        self.btn_run.Font = bold_font
        self.btn_run.Location = Point(8, 400)
        self.btn_run.Size = Size(180, 36)
        self.btn_run.Click += self.on_run_comparison
        lp.Controls.Add(self.btn_run)

        # ---- GPS info / status labels (populated after run) ----
        self.lbl_gps_info = Label()
        self.lbl_gps_info.Text = "GPS PPS server: (run comparison to detect)"
        self.lbl_gps_info.Font = default_font
        self.lbl_gps_info.Location = Point(8, 446)
        self.lbl_gps_info.Size = Size(440, 20)
        self.lbl_gps_info.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.lbl_gps_info)

        self.lbl_noselect_info = Label()
        self.lbl_noselect_info.Text = "Noselect coverage: —"
        self.lbl_noselect_info.Font = default_font
        self.lbl_noselect_info.Location = Point(8, 468)
        self.lbl_noselect_info.Size = Size(440, 20)
        self.lbl_noselect_info.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.lbl_noselect_info)

        # ---- One-line results summaries ----
        self.lbl_uncertainty_hdr = Label()
        self.lbl_uncertainty_hdr.Text = "UTC Error (k=2, combined):"
        self.lbl_uncertainty_hdr.Font = bold_font
        self.lbl_uncertainty_hdr.Location = Point(8, 496)
        self.lbl_uncertainty_hdr.Size = Size(220, 20)
        lp.Controls.Add(self.lbl_uncertainty_hdr)

        self.txt_uncertainty = TextBox()
        self.txt_uncertainty.Text = ""
        self.txt_uncertainty.ReadOnly = True
        self.txt_uncertainty.Font = bold_font
        self.txt_uncertainty.Location = Point(8, 518)
        self.txt_uncertainty.Size = Size(440, 24)
        self.txt_uncertainty.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.txt_uncertainty)

        self.lbl_drift_hdr = Label()
        self.lbl_drift_hdr.Text = "Clock drift (over GPS period):"
        self.lbl_drift_hdr.Font = bold_font
        self.lbl_drift_hdr.Location = Point(8, 548)
        self.lbl_drift_hdr.Size = Size(220, 20)
        lp.Controls.Add(self.lbl_drift_hdr)

        self.txt_drift = TextBox()
        self.txt_drift.Text = ""
        self.txt_drift.ReadOnly = True
        self.txt_drift.Font = bold_font
        self.txt_drift.Location = Point(8, 570)
        self.txt_drift.Size = Size(440, 24)
        self.txt_drift.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.txt_drift)

        # ---- Full text report (expands to fill remaining height) ----
        self.txt_output = TextBox()
        self.txt_output.Multiline = True
        self.txt_output.ScrollBars = ScrollBars.Both
        self.txt_output.ReadOnly = True
        self.txt_output.Font = Font("Consolas", 9)
        self.txt_output.Location = Point(8, 602)
        self.txt_output.Size = Size(446, 250)
        self.txt_output.Anchor = (AnchorStyles.Top | AnchorStyles.Bottom |
                                   AnchorStyles.Left | AnchorStyles.Right)
        lp.Controls.Add(self.txt_output)

        # ---- Status bar ----
        self.lbl_status = Label()
        self.lbl_status.Text = "Ready."
        self.lbl_status.Location = Point(8, 860)
        self.lbl_status.Size = Size(446, 22)
        self.lbl_status.Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.lbl_status)

        # ---- Right panel: 3-row table ----
        tbl = TableLayoutPanel()
        tbl.Dock = DockStyle.Fill
        tbl.RowCount = 3
        tbl.ColumnCount = 1
        tbl.RowStyles.Clear()
        for _ in range(3):
            tbl.RowStyles.Add(RowStyle(SizeType.Percent, 33.334))
        tbl.ColumnStyles.Clear()
        tbl.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        split.Panel2.Controls.Add(tbl)

        self.chart_delays = self.create_plot_panel(
            "Delay (NTP servers, color-coded)", "delays")
        self.chart_delays.Dock = DockStyle.Fill
        tbl.Controls.Add(self.chart_delays, 0, 0)

        self.chart_offset_diffs = self.create_plot_panel(
            "UTC Error per Server  (offset \u2212 GPS PPS)", "offset_diffs")
        self.chart_offset_diffs.Dock = DockStyle.Fill
        tbl.Controls.Add(self.chart_offset_diffs, 0, 1)

        self.chart_selected_diff = self.create_plot_panel(
            "Selected Peer UTC Error + Clock Drift", "selected_diff")
        self.chart_selected_diff.Dock = DockStyle.Fill
        tbl.Controls.Add(self.chart_selected_diff, 0, 2)

        self.prefill_defaults()

    # -----------------------------------------------------------------------
    # Layout management
    # -----------------------------------------------------------------------

    def on_form_shown(self, sender, event):
        split = self._main_split
        available_width = split.ClientSize.Width
        if available_width <= 0:
            return
        required_right = 0
        for ctrl in split.Panel1.Controls:
            right = ctrl.Location.X + ctrl.Size.Width
            if right > required_right:
                required_right = right
        left_min = max(required_right + 8, 380)
        try:
            split.SplitterDistance = left_min
        except Exception:
            pass
        self.adjust_left_panel_layout()

    def on_left_panel_resize(self, sender, event):
        self.adjust_left_panel_layout()

    def adjust_left_panel_layout(self):
        panel = self._main_split.Panel1
        panel_width = panel.ClientSize.Width
        if panel_width <= 0:
            return

        margin = 8
        inter = 7
        label_h = 22
        text_h = 24
        button_h = 34
        run_h = 38
        full_w = max(120, panel_width - (margin * 2))

        y = 8
        self.lbl_title.Location = Point(margin, y)
        self.lbl_title.Size = Size(full_w, 28)
        y += 28 + inter

        self.lbl_log.Location = Point(margin, y)
        self.lbl_log.Size = Size(full_w, label_h)
        y += label_h

        self.txt_log_folder.Location = Point(margin, y)
        self.txt_log_folder.Size = Size(full_w, text_h)
        y += text_h + inter

        browse_w = 100
        scan_w = 120
        btn_gap = 6
        self.btn_browse_log.Location = Point(margin, y)
        self.btn_browse_log.Size = Size(browse_w, button_h)
        self.btn_scan.Location = Point(margin + browse_w + btn_gap, y)
        self.btn_scan.Size = Size(scan_w, button_h)
        y += button_h + inter

        self.lbl_filter.Location = Point(margin, y)
        self.lbl_filter.Size = Size(full_w, label_h)
        y += label_h

        apply_w = 112
        filter_gap = 6
        if full_w >= (apply_w + 150 + filter_gap):
            filter_w = max(120, full_w - apply_w - filter_gap)
            self.txt_day_filter.Location = Point(margin, y)
            self.txt_day_filter.Size = Size(filter_w, text_h)
            self.btn_apply_filter.Location = Point(margin + filter_w + filter_gap, y - 1)
            self.btn_apply_filter.Size = Size(apply_w, button_h)
            y += max(text_h, button_h) + inter
        else:
            self.txt_day_filter.Location = Point(margin, y)
            self.txt_day_filter.Size = Size(full_w, text_h)
            y += text_h + 4
            self.btn_apply_filter.Location = Point(margin, y)
            self.btn_apply_filter.Size = Size(apply_w, button_h)
            y += button_h + inter

        self.lbl_dataset.Location = Point(margin, y)
        self.lbl_dataset.Size = Size(full_w, label_h)
        y += label_h

        self.cmb_dataset.Location = Point(margin, y)
        self.cmb_dataset.Size = Size(full_w, text_h)
        y += text_h + inter

        # Export row: checkbox on its own sub-row, then folder + browse
        self.chk_export.Location = Point(margin, y)
        self.chk_export.Size = Size(min(220, full_w), text_h)
        y += text_h

        browse_exp_w = 112
        export_gap = 6
        if full_w >= (browse_exp_w + 120 + export_gap):
            export_w = max(80, full_w - browse_exp_w - export_gap)
            self.txt_export_folder.Location = Point(margin, y)
            self.txt_export_folder.Size = Size(export_w, text_h)
            self.btn_browse_export.Location = Point(margin + export_w + export_gap, y - 1)
            self.btn_browse_export.Size = Size(browse_exp_w, button_h)
            y += max(text_h, button_h) + inter
        else:
            self.txt_export_folder.Location = Point(margin, y)
            self.txt_export_folder.Size = Size(full_w, text_h)
            y += text_h + 4
            self.btn_browse_export.Location = Point(margin, y)
            self.btn_browse_export.Size = Size(browse_exp_w, button_h)
            y += button_h + inter

        # Observer coordinates
        self.lbl_observer.Location = Point(margin, y)
        self.lbl_observer.Size = Size(full_w, label_h)
        y += label_h

        lat_lbl_w = 28
        lat_w = 80
        lon_lbl_w = 28
        lon_w = 80
        coords_gap = 10
        x = margin
        self.lbl_observer_lat.Location = Point(x, y + 3)
        self.lbl_observer_lat.Size = Size(lat_lbl_w, label_h)
        x += lat_lbl_w
        self.txt_observer_lat.Location = Point(x, y)
        self.txt_observer_lat.Size = Size(lat_w, text_h)
        x += lat_w + coords_gap
        self.lbl_observer_lon.Location = Point(x, y + 3)
        self.lbl_observer_lon.Size = Size(lon_lbl_w, label_h)
        x += lon_lbl_w
        self.txt_observer_lon.Location = Point(x, y)
        self.txt_observer_lon.Size = Size(lon_w, text_h)
        y += text_h + 2

        self.lbl_observer_note.Location = Point(margin, y)
        self.lbl_observer_note.Size = Size(full_w, label_h)
        y += label_h + inter

        # "Run Comparison" button — full width at smaller sizes, fixed width when wide
        run_w = min(full_w, 200)
        self.btn_run.Location = Point(margin, y)
        self.btn_run.Size = Size(run_w, run_h)
        y += run_h + inter

        # GPS info labels
        self.lbl_gps_info.Location = Point(margin, y)
        self.lbl_gps_info.Size = Size(full_w, label_h)
        y += label_h + 2

        self.lbl_noselect_info.Location = Point(margin, y)
        self.lbl_noselect_info.Size = Size(full_w, label_h)
        y += label_h + inter

        # One-line summary boxes
        self.lbl_uncertainty_hdr.Location = Point(margin, y)
        self.lbl_uncertainty_hdr.Size = Size(full_w, label_h)
        y += label_h

        self.txt_uncertainty.Location = Point(margin, y)
        self.txt_uncertainty.Size = Size(full_w, text_h)
        y += text_h + inter

        self.lbl_drift_hdr.Location = Point(margin, y)
        self.lbl_drift_hdr.Size = Size(full_w, label_h)
        y += label_h

        self.txt_drift.Location = Point(margin, y)
        self.txt_drift.Size = Size(full_w, text_h)
        y += text_h + inter

        # txt_output fills the rest; status bar is always at the very bottom
        status_h = 24
        output_top = y
        output_h = max(60, panel.ClientSize.Height - output_top - status_h - 2)
        self.txt_output.Location = Point(margin, output_top)
        self.txt_output.Size = Size(full_w, output_h)

        self.lbl_status.Location = Point(margin, panel.ClientSize.Height - status_h)
        self.lbl_status.Size = Size(full_w, status_h)

    # -----------------------------------------------------------------------
    # Chart / plot panel construction
    # -----------------------------------------------------------------------

    def create_plot_panel(self, title, plot_key):
        """Create a Label container + PictureBox for one chart row."""
        container = Label()
        container.Text = title
        container.Font = Font("Segoe UI", 9, FontStyle.Bold)
        # AutoSize must be False so WinForms anchoring on the child PictureBox
        # resolves correctly; otherwise the container auto-sizes to text height
        # and the PictureBox overflows, causing its bottom portion to be clipped.
        container.AutoSize = False
        container.Size = Size(100, 100)
        container.Anchor = (AnchorStyles.Top | AnchorStyles.Bottom |
                             AnchorStyles.Left | AnchorStyles.Right)

        _legend_font = Font("Segoe UI", 8)
        _center_y = 15
        _legend_y = 4

        if plot_key == "delays":
            self._delays_legend_controls = []
        elif plot_key == "offset_diffs":
            self._offset_diffs_legend_controls = []
        elif plot_key == "selected_diff":
            # Inline legend: selected-peer diff line + OLS trend line
            _sw1 = Label()
            _sw1.BackColor = Color.FromArgb(31, 119, 180)
            _sw1.BorderStyle = BorderStyle.FixedSingle
            _sw1.Location = Point(300, _center_y - 2)
            _sw1.Size = Size(18, 5)
            container.Controls.Add(_sw1)
            _lb1 = Label()
            _lb1.Text = u"UTC Error (offset \u2212 GPS)"
            _lb1.Font = _legend_font
            _lb1.Location = Point(322, _legend_y - 1)
            _lb1.Size = Size(155, 20)
            container.Controls.Add(_lb1)
            _sw2 = Label()
            _sw2.BackColor = Color.FromArgb(200, 60, 20)
            _sw2.BorderStyle = BorderStyle.FixedSingle
            _sw2.Location = Point(485, _center_y - 1)
            _sw2.Size = Size(18, 3)
            container.Controls.Add(_sw2)
            _lb2 = Label()
            _lb2.Text = "OLS drift (dashed)"
            _lb2.Font = _legend_font
            _lb2.Location = Point(507, _legend_y - 1)
            _lb2.Size = Size(130, 20)
            container.Controls.Add(_lb2)

        plot_box = PictureBox()
        plot_box.Location = Point(0, 30)
        # Initial height = container height - header = 100 - 30 = 70.
        # dist_bottom anchor = container.Height - plot_box.Bottom = 100 - 100 = 0.
        # After Dock/resize the PictureBox fills the container correctly.
        plot_box.Size = Size(100, 70)
        plot_box.Anchor = (AnchorStyles.Top | AnchorStyles.Bottom |
                            AnchorStyles.Left | AnchorStyles.Right)
        plot_box.BorderStyle = BorderStyle.FixedSingle
        plot_box.BackColor = Color.White
        plot_box.Tag = plot_key
        plot_box.Paint += self.on_plot_paint
        container.Controls.Add(plot_box)
        return container

    def _rebuild_server_legend(self, container, legend_store, server_to_color,
                                unique_servers, server_to_km=None):
        """Rebuild color-swatch + label controls in a chart header for server legend."""
        for ctrl in legend_store[:]:
            try:
                container.Controls.Remove(ctrl)
                ctrl.Dispose()
            except Exception:
                pass
        del legend_store[:]

        if not unique_servers:
            return

        legend_font = Font("Segoe UI", 8)
        x_pos = 460
        center_y = 15
        legend_y = 4

        for server in unique_servers:
            if x_pos > max(container.ClientSize.Width - 178, 460):
                break

            swatch = Label()
            swatch.BackColor = server_to_color.get(server, Color.Gray)
            swatch.BorderStyle = BorderStyle.FixedSingle
            swatch.Location = Point(x_pos, center_y - 2)
            swatch.Size = Size(18, 5)
            container.Controls.Add(swatch)
            legend_store.append(swatch)

            lbl = Label()
            text = server if server else "Unknown"
            if server_to_km and server in server_to_km and server_to_km[server] is not None:
                text = "%s (%d km)" % (text, int(round(server_to_km[server])))
            lbl.Text = text
            lbl.Font = legend_font
            lbl.Location = Point(x_pos + 22, legend_y - 1)
            lbl.Size = Size(150, 20)
            container.Controls.Add(lbl)
            legend_store.append(lbl)

            x_pos += 178

    def _get_plot_box(self, container):
        for ctrl in container.Controls:
            if isinstance(ctrl, PictureBox):
                return ctrl
        return None

    def invalidate_plots(self):
        for container in (self.chart_delays, self.chart_offset_diffs, self.chart_selected_diff):
            pb = self._get_plot_box(container)
            if pb is not None:
                pb.Invalidate()

    # -----------------------------------------------------------------------
    # Drawing
    # -----------------------------------------------------------------------

    def on_plot_paint(self, sender, event):
        plot_key = sender.Tag
        chart_data = self._plot_data.get(plot_key)
        if chart_data is None:
            self.draw_empty_plot(event.Graphics, sender.ClientRectangle)
            return
        chart_data["plot_key"] = plot_key
        self.draw_plot(event.Graphics, sender.ClientRectangle, chart_data)

    def draw_empty_plot(self, graphics, bounds):
        graphics.Clear(Color.White)
        brush = SolidBrush(Color.Gray)
        try:
            graphics.DrawString("Run Comparison to draw data.",
                                 Font("Segoe UI", 9), brush, 8, 8)
        finally:
            brush.Dispose()

    def draw_plot(self, graphics, bounds, chart_data):
        import math as _math
        graphics.Clear(Color.White)

        left   = 62
        top    = 8
        right  = 6
        bottom = 28
        width  = max(10, bounds.Width  - left - right)
        height = max(10, bounds.Height - top  - bottom)
        plot_rect = Rectangle(left, top, width, height)

        x_start = chart_data["x_start"]
        x_end   = chart_data["x_end"]
        y_min   = chart_data["y_min"]   # ms
        y_max   = chart_data["y_max"]   # ms
        y_step  = chart_data["y_step"]  # ms

        h_grid_pen     = Pen(Color.FromArgb(220, 220, 220))
        v_grid_pen     = Pen(Color.FromArgb(228, 228, 228))
        zero_pen       = Pen(Color.FromArgb(150, 150, 150))
        axis_pen       = Pen(Color.FromArgb(100, 100, 100))
        label_brush    = SolidBrush(Color.FromArgb(80, 80, 80))
        label_font     = Font("Segoe UI", 7)
        try:
            # --- Coverage bands (behind everything) ---
            coverage_intervals = chart_data.get("coverage_intervals")
            if coverage_intervals:
                self._draw_coverage_bands(graphics, plot_rect, coverage_intervals,
                                          x_start, x_end)

            # --- Vertical x-gridlines: minor (thin) + major (labelled) ---
            major_minutes = chart_data.get("x_major_minutes", 60)
            minor_minutes = chart_data.get("x_minor_minutes", 30)
            minor_td = timedelta(minutes=minor_minutes)
            v_minor_pen = Pen(Color.FromArgb(240, 240, 240))
            try:
                t = x_start
                while t <= x_end:
                    total_min = t.hour * 60 + t.minute
                    is_major = (total_min % major_minutes == 0) and t.second == 0
                    x = self.map_x(t, x_start, x_end, plot_rect)
                    if plot_rect.Left <= x <= plot_rect.Right:
                        graphics.DrawLine(v_grid_pen if is_major else v_minor_pen,
                                          x, plot_rect.Top, x, plot_rect.Bottom)
                        if is_major:
                            lbl = t.strftime("%H:%M")
                            lbl_x = int(x - len(lbl) * 3.5)
                            graphics.DrawString(lbl, label_font, label_brush,
                                                lbl_x, plot_rect.Bottom + 4)
                    t = t + minor_td
            finally:
                v_minor_pen.Dispose()

            # --- Horizontal y-gridlines + tick labels ---
            num_ticks = int(round((y_max - y_min) / y_step)) + 1
            for i in range(num_ticks):
                y_val = y_min + i * y_step
                py = self.map_y(y_val, y_min, y_max, plot_rect)
                if plot_rect.Top <= py <= plot_rect.Bottom:
                    is_zero = abs(y_val) < y_step * 1e-4
                    graphics.DrawLine(zero_pen if is_zero else h_grid_pen,
                                      plot_rect.Left, py, plot_rect.Right, py)
                    lbl = ntp_core._format_y_label_ms(y_val, y_step)
                    lbl_y = max(plot_rect.Top, min(plot_rect.Bottom - 10, py - 6))
                    graphics.DrawString(lbl, label_font, label_brush, 2, lbl_y)

            # --- Axis border ---
            graphics.DrawRectangle(axis_pen, plot_rect)
            graphics.DrawString("UTC", label_font, label_brush,
                                 plot_rect.Right - 24, plot_rect.Bottom + 2)

            # --- Data series + trend line clipped to the plot area ---
            graphics.SetClip(plot_rect)
            try:
                for item in chart_data.get("series", []):
                    pts = item["points"]
                    if not pts:
                        continue
                    line_pen = Pen(item["color"], item.get("width", 2))
                    try:
                        prev_xy = None
                        for entry in pts:
                            dt_value = entry[0]
                            y_value  = entry[1]
                            x = self.map_x(dt_value, x_start, x_end, plot_rect)
                            y = self.map_y(y_value * 1000.0, y_min, y_max, plot_rect)
                            if prev_xy is not None:
                                graphics.DrawLine(line_pen, prev_xy[0], prev_xy[1], x, y)
                            prev_xy = (x, y)
                    finally:
                        line_pen.Dispose()

                # --- Trend line overlay (drawn on top of series for visibility) ---
                trend_data = chart_data.get("trend_line")
                if trend_data and trend_data.get("drift_ms_per_hour") is not None:
                    self._draw_trend_line(graphics, plot_rect, trend_data,
                                          x_start, x_end, y_min, y_max)
            finally:
                graphics.ResetClip()

        finally:
            h_grid_pen.Dispose()
            v_grid_pen.Dispose()
            zero_pen.Dispose()
            axis_pen.Dispose()
            label_brush.Dispose()
            label_font.Dispose()

    def _draw_coverage_bands(self, graphics, plot_rect, intervals, x_start, x_end):
        """Fill semi-transparent grey rectangles for the GPS PPS noselect intervals."""
        band_brush = SolidBrush(Color.FromArgb(28, 100, 140, 100))  # faint green-grey
        try:
            for start_dt, end_dt in intervals:
                x0 = self.map_x(start_dt, x_start, x_end, plot_rect)
                x1 = self.map_x(end_dt,   x_start, x_end, plot_rect)
                # Clamp to plot area
                x0 = max(plot_rect.Left,  min(plot_rect.Right,  x0))
                x1 = max(plot_rect.Left,  min(plot_rect.Right,  x1))
                band_w = max(1, x1 - x0)
                graphics.FillRectangle(band_brush,
                                       x0, plot_rect.Top, band_w, plot_rect.Height)
        finally:
            band_brush.Dispose()

    def _draw_trend_line(self, graphics, plot_rect, drift_result,
                          x_start, x_end, y_min, y_max):
        """Draw a dashed trend line representing the linear drift regression."""
        # drift_ms_per_hour is the OLS slope; start_offset_ms is the Y-intercept
        # estimate (mean of first 10%).  We calculate the line value at x_start
        # and x_end using the full window start/end offsets from drift_result.
        coverage_hours = drift_result.get("coverage_hours", 0.0)
        if coverage_hours <= 0:
            return

        # The regression covers [start_dt, end_dt] — we stored start_offset_ms
        # and end_offset_ms so we can draw a segment between those two points.
        # Use coverage_hours to find the actual start/end datetimes approximately
        # (they were built from noselect_intervals in on_run_comparison).
        trend_start_dt = drift_result.get("_trend_start_dt")
        trend_end_dt   = drift_result.get("_trend_end_dt")
        if trend_start_dt is None or trend_end_dt is None:
            return

        y0_ms = drift_result.get("start_offset_ms", 0.0)
        y1_ms = drift_result.get("end_offset_ms",   0.0)

        x0 = self.map_x(trend_start_dt, x_start, x_end, plot_rect)
        x1 = self.map_x(trend_end_dt,   x_start, x_end, plot_rect)
        py0 = self.map_y(y0_ms, y_min, y_max, plot_rect)
        py1 = self.map_y(y1_ms, y_min, y_max, plot_rect)

        trend_pen = Pen(Color.FromArgb(180, 200, 60, 20), 2)
        try:
            try:
                # DashPattern: float array [dash_len, gap_len] in pen-width units.
                # IronPython converts a Python list of floats automatically.
                trend_pen.DashPattern = [8.0, 4.0]
            except Exception:
                pass  # fall back to solid line if DashPattern unsupported
            graphics.DrawLine(trend_pen, x0, py0, x1, py1)
        finally:
            trend_pen.Dispose()

    def map_x(self, dt_value, x_start, x_end, rect):
        total = (x_end - x_start).total_seconds()
        if total <= 0:
            return rect.Left
        offset = (dt_value - x_start).total_seconds()
        return int(rect.Left + (float(offset) / float(total)) * rect.Width)

    def map_y(self, value, y_min, y_max, rect):
        span = y_max - y_min
        if span <= 0:
            return rect.Top + int(rect.Height / 2)
        ratio = (float(value) - float(y_min)) / float(span)
        return int(rect.Bottom - ratio * rect.Height)

    # -----------------------------------------------------------------------
    # Chart data preparation
    # -----------------------------------------------------------------------

    def update_charts(self, loop_rows, peer_rows, comparison, drift_result):
        """Build _plot_data for all three chart panels and trigger redraw."""
        import math as _math

        # Collect all data datetimes for tight x-axis bounds
        _all_dts = []
        for _ps in (comparison.get("per_server_delay", {}), comparison.get("per_server_diff", {})):
            for _pts in _ps.values():
                _all_dts.extend(_dt for _dt, _ in _pts)
        _all_dts.extend(_dt for _dt, _ in comparison.get("selected_peer_diff", []))

        if _all_dts:
            _data_min = min(_all_dts)
            _data_max = max(_all_dts)
            _span_s   = (_data_max - _data_min).total_seconds()
            if _span_s <= 7200.0:       # <= 2 h
                x_major_minutes, x_minor_minutes = 30, 10
            elif _span_s <= 21600.0:    # <= 6 h
                x_major_minutes, x_minor_minutes = 60, 30
            elif _span_s <= 86400.0:    # <= 24 h
                x_major_minutes, x_minor_minutes = 120, 60
            else:
                x_major_minutes, x_minor_minutes = 360, 60
            # Floor start to nearest prior major-tick boundary
            _sm = _data_min.hour * 60 + _data_min.minute
            _sf = (_sm // x_major_minutes) * x_major_minutes
            x_start = _data_min.replace(hour=_sf // 60, minute=_sf % 60,
                                        second=0, microsecond=0)
            # Ceil end to nearest next major-tick boundary
            _em = _data_max.hour * 60 + _data_max.minute + (
                1 if (_data_max.second or _data_max.microsecond) else 0)
            _ec = int(_math.ceil(float(_em) / x_major_minutes)) * x_major_minutes
            if _ec >= 1440:
                x_end = _data_max.replace(hour=0, minute=0, second=0, microsecond=0) \
                        + timedelta(days=1)
            else:
                x_end = _data_max.replace(hour=_ec // 60, minute=_ec % 60,
                                          second=0, microsecond=0)
            # Enforce minimum 1-hour span
            if (x_end - x_start).total_seconds() < 3600.0:
                x_end = x_start + timedelta(hours=1)
        else:
            x_start, x_end = compute_axis_day_bounds(loop_rows, peer_rows)
            x_major_minutes, x_minor_minutes = 60, 30

        if x_start is None or x_end is None:
            self._plot_data = {}
            self.invalidate_plots()
            return

        server_to_color = {}
        server_to_km    = comparison.get("server_to_km", {})
        noselect_ivs    = comparison.get("noselect_intervals", [])

        # Assign colors to all internet servers in a stable order
        all_servers = sorted(comparison.get("per_server_delay", {}).keys())
        for addr in all_servers:
            get_server_color(addr, server_to_color)

        def _y_limits(series_list):
            """y_min, y_max, y_step (ms) from a collection of (dt, val_s) point lists.
            Always brackets zero; snapped to a nice tick step with ≤9 ticks."""
            vals_ms = []
            for pts in series_list:
                vals_ms.extend(v * 1000.0 for _, v in pts)
            if not vals_ms:
                return -1.0, 1.0, 1.0
            lo = min(min(vals_ms), 0.0)
            hi = max(max(vals_ms), 0.0)
            span = hi - lo if hi != lo else 1.0
            step = ntp_core._choose_y_step_ms(span)
            y_min = _math.floor(lo / step) * step
            y_max = _math.ceil(hi  / step) * step
            # Ensure minimum 2-step span, but recalculate step from the
            # extended span so the total tick count stays ≤ 9.
            if y_max - y_min < step * 2:
                y_max = y_min + step * 2
                step = ntp_core._choose_y_step_ms(y_max - y_min)
                y_min = _math.floor(lo / step) * step
                y_max = _math.ceil(hi  / step) * step
                if y_max - y_min < step * 2:
                    y_max = y_min + step * 2
            return y_min, y_max, step

        # ---- Chart 0: delays (one series per server) ----
        delay_series = []
        for addr in all_servers:
            pts = sorted(comparison["per_server_delay"].get(addr, []),
                         key=lambda p: p[0])
            delay_series.append({
                "name":   addr,
                "color":  server_to_color.get(addr, Color.Gray),
                "points": pts,
                "width":  2,
            })
        all_delay_pts = [pt for s in delay_series for pt in s["points"]]
        d_min, d_max, d_step = _y_limits([all_delay_pts])

        # ---- Chart 1: offset diffs per server ----
        diff_series = []
        for addr in all_servers:
            pts = sorted(comparison["per_server_diff"].get(addr, []),
                         key=lambda p: p[0])
            diff_series.append({
                "name":   addr,
                "color":  server_to_color.get(addr, Color.Gray),
                "points": pts,
                "width":  2,
            })
        all_diff_pts = [pt for s in diff_series for pt in s["points"]]
        od_min, od_max, od_step = _y_limits([all_diff_pts])

        # ---- Chart 2: selected peer diff + trend ----
        sel_pts = sorted(comparison.get("selected_peer_diff", []),
                         key=lambda p: p[0])
        sel_series = [{
            "name":   "Selected peer",
            "color":  Color.FromArgb(31, 119, 180),
            "points": sel_pts,
            "width":  2,
        }]
        sd_min, sd_max, sd_step = _y_limits([sel_pts])

        # Rebase the trend line onto the offset-diff chart.
        # estimate_drift_linear_regression returns start/end_offset_ms in raw peer
        # offset units, but the chart plots (peer_offset - gps_offset).  We keep
        # the correct OLS slope and recompute the intercept from sel_pts so the
        # trend line passes through the actual data.
        drift_for_plot = drift_result
        if (drift_result and drift_result.get("drift_ms_per_hour") is not None
                and len(sel_pts) >= 2):
            _slope_ms_s = drift_result["drift_ms_per_hour"] / 3600.0
            _t0 = sel_pts[0][0]
            _intercepts = [
                v * 1000.0 - _slope_ms_s * (dt - _t0).total_seconds()
                for dt, v in sel_pts
            ]
            _icept = sum(_intercepts) / len(_intercepts)
            _ts = drift_result.get("_trend_start_dt")
            _te = drift_result.get("_trend_end_dt")
            if _ts is not None and _te is not None:
                drift_for_plot = dict(drift_result)
                drift_for_plot["start_offset_ms"] = (
                    _icept + _slope_ms_s * (_ts - _t0).total_seconds())
                drift_for_plot["end_offset_ms"] = (
                    _icept + _slope_ms_s * (_te - _t0).total_seconds())

        # Extend y range to include rebased trend line endpoints
        if drift_for_plot and drift_for_plot.get("drift_ms_per_hour") is not None:
            for v in (drift_for_plot.get("start_offset_ms", 0.0),
                      drift_for_plot.get("end_offset_ms",   0.0)):
                if v is not None:
                    if v < sd_min:
                        sd_min = _math.floor(v / sd_step) * sd_step
                    if v > sd_max:
                        sd_max = _math.ceil(v  / sd_step) * sd_step

        self._plot_data = {
            "delays": {
                "x_start":         x_start,
                "x_end":           x_end,
                "x_major_minutes": x_major_minutes,
                "x_minor_minutes": x_minor_minutes,
                "y_min":           d_min,
                "y_max":           d_max,
                "y_step":          d_step,
                "series":          delay_series,
            },
            "offset_diffs": {
                "x_start":            x_start,
                "x_end":              x_end,
                "x_major_minutes":    x_major_minutes,
                "x_minor_minutes":    x_minor_minutes,
                "y_min":              od_min,
                "y_max":              od_max,
                "y_step":             od_step,
                "series":             diff_series,
                "coverage_intervals": noselect_ivs,
            },
            "selected_diff": {
                "x_start":            x_start,
                "x_end":              x_end,
                "x_major_minutes":    x_major_minutes,
                "x_minor_minutes":    x_minor_minutes,
                "y_min":              sd_min,
                "y_max":              sd_max,
                "y_step":             sd_step,
                "series":             sel_series,
                "coverage_intervals": noselect_ivs,
                "trend_line":         drift_for_plot,
            },
        }

        # Legend only on the top chart; clear any stale items from the other panels
        unique_servers = all_servers
        self._rebuild_server_legend(self.chart_delays, self._delays_legend_controls,
                                    server_to_color, unique_servers, server_to_km)
        for _ctrl in self._offset_diffs_legend_controls[:]:
            try:
                self.chart_offset_diffs.Controls.Remove(_ctrl)
                _ctrl.Dispose()
            except Exception:
                pass
        del self._offset_diffs_legend_controls[:]
        self.invalidate_plots()

    # -----------------------------------------------------------------------
    # Observer coordinates helper
    # -----------------------------------------------------------------------

    def _get_observer_coords(self):
        """Parse lat/lon text boxes. Returns (lat, lon) floats or (None, None)."""
        try:
            lat = float(self.txt_observer_lat.Text.strip())
            lon = float(self.txt_observer_lon.Text.strip())
        except (ValueError, AttributeError):
            return None, None
        lat_ok = -90.0  <= lat <= 90.0
        lon_ok = -180.0 <= lon <= 180.0
        # Auto-correct obviously swapped entry
        if not lat_ok and lon_ok and -90.0 <= lon <= 90.0 and -180.0 <= lat <= 180.0:
            lat, lon = lon, lat
        elif not lat_ok or not lon_ok:
            return None, None
        return lat, lon

    # -----------------------------------------------------------------------
    # Settings / folder management
    # -----------------------------------------------------------------------

    def prefill_defaults(self):
        saved = load_folder_settings()
        saved_log    = saved.get("log_folder",    "").strip()
        saved_export = saved.get("export_folder", "").strip()

        if saved_log and os.path.isdir(saved_log):
            self.txt_log_folder.Text = saved_log
            self.txt_export_folder.Text = (
                saved_export if saved_export
                else os.path.join(saved_log, "reports")
            )
        else:
            candidates = discover_candidate_dirs()
            if candidates:
                self.txt_log_folder.Text = candidates[0]
                self.txt_export_folder.Text = os.path.join(candidates[0], "reports")

        if not self.txt_export_folder.Text.strip() and self.txt_log_folder.Text.strip():
            self.txt_export_folder.Text = os.path.join(
                self.txt_log_folder.Text.strip(), "reports")

        self.txt_observer_lat.Text = saved.get("observer_lat", "").strip()
        self.txt_observer_lon.Text = saved.get("observer_lon", "").strip()
        self.on_export_toggle(None, None)
        self.scan_options()

    def show_error(self, message):
        MessageBox.Show(self, message, "GPS PPS Comparison",
                        MessageBoxButtons.OK, MessageBoxIcon.Error)

    def choose_folder(self, current_path):
        dialog = FolderBrowserDialog()
        if current_path and os.path.isdir(current_path):
            dialog.SelectedPath = current_path
        if dialog.ShowDialog(self) == DialogResult.OK:
            return dialog.SelectedPath
        return None

    def on_browse_log(self, sender, event):
        chosen = self.choose_folder(self.txt_log_folder.Text.strip())
        if chosen:
            self.txt_log_folder.Text = chosen
            if not self.txt_export_folder.Text.strip():
                self.txt_export_folder.Text = os.path.join(chosen, "reports")
            save_folder_settings(self.txt_log_folder.Text.strip(),
                                  self.txt_export_folder.Text.strip(),
                                  self.txt_observer_lat.Text.strip(),
                                  self.txt_observer_lon.Text.strip())
            self.scan_options()

    def on_browse_export(self, sender, event):
        chosen = self.choose_folder(self.txt_export_folder.Text.strip())
        if chosen:
            self.txt_export_folder.Text = chosen
            save_folder_settings(self.txt_log_folder.Text.strip(),
                                  self.txt_export_folder.Text.strip(),
                                  self.txt_observer_lat.Text.strip(),
                                  self.txt_observer_lon.Text.strip())

    def on_export_toggle(self, sender, event):
        enabled = self.chk_export.Checked
        self.txt_export_folder.Enabled = enabled
        self.btn_browse_export.Enabled = enabled

    def on_scan(self, sender, event):
        save_folder_settings(self.txt_log_folder.Text.strip(),
                              self.txt_export_folder.Text.strip(),
                              self.txt_observer_lat.Text.strip(),
                              self.txt_observer_lon.Text.strip())
        self.scan_options()

    def scan_options(self):
        log_folder = self.txt_log_folder.Text.strip().strip('"')
        self.cmb_dataset.Items.Clear()
        self._options_by_label = {}

        if not log_folder:
            self.set_status("Set an NTP log folder, then scan datasets.")
            return
        if not os.path.isdir(log_folder):
            self.set_status("Log folder does not exist.")
            return

        try:
            options = build_day_options(log_folder)
        except Exception as err:
            self.show_error("Failed to scan datasets:\n%s" % str(err))
            self.set_status("Scan failed.")
            return

        filter_text = self.txt_day_filter.Text.strip().lower()
        if filter_text:
            options = [o for o in options
                       if filter_text in o.key.lower() or filter_text in o.label.lower()]

        if not options:
            self.set_status("No matching loopstats/peerstats datasets found.")
            return

        for option in options:
            self.cmb_dataset.Items.Add(option.label)
            self._options_by_label[option.label] = option

        self.cmb_dataset.SelectedIndex = 0
        self.set_status("Loaded %d dataset option(s)." % len(options))

    def get_selected_option(self):
        label = self.cmb_dataset.Text
        if not label:
            raise RuntimeError("No dataset selected.")
        option = self._options_by_label.get(label)
        if option is None:
            raise RuntimeError("Dataset selection is invalid.  Please rescan datasets.")
        return option

    # -----------------------------------------------------------------------
    # Main analysis flow
    # -----------------------------------------------------------------------

    def on_run_comparison(self, sender, event):
        try:
            option = self.get_selected_option()
            self.set_status("Loading data...")

            loop_rows = parse_loopstats(option.loop_path, option.target_mjd)
            peer_rows = parse_peerstats(option.peer_path, option.target_mjd)

            if not peer_rows:
                raise RuntimeError("No peerstats rows found for the selected dataset.")

            # Check that at least one GPS/PPS refclock exists
            candidates = find_gps_pps_candidates(peer_rows)
            if not candidates:
                raise RuntimeError(
                    "No NTP refclock (127.127.*.*) addresses were found in the "
                    "peerstats data for this dataset.\n\n"
                    "Make sure your ntp.conf has a GPS or PPS refclock configured "
                    "and that the correct dataset day is selected."
                )

            # --- Pre-flight dialog ---
            self.set_status("Waiting for GPS PPS server confirmation...")
            preflight = GPSPPSPreflightDialog(peer_rows)
            result = preflight.ShowDialog(self)
            if result != DialogResult.OK:
                self.set_status("Comparison cancelled.")
                return

            gps_addr          = preflight.selected_gps_addr
            noselect_intervals = preflight.noselect_intervals
            noselect_status    = preflight.noselect_status

            if not noselect_intervals:
                raise RuntimeError(
                    "No valid noselect intervals were found for %s.\n\n"
                    "The analysis requires the GPS PPS server to appear in "
                    "peerstats with select code < 4 (noselect state) for at "
                    "least some of the dataset period." % gps_addr
                )

            self.set_status("Running GPS PPS comparison...")

            obs_lat, obs_lon = self._get_observer_coords()

            # --- Phase 1: core comparison ---
            comparison = compute_gps_pps_comparison(
                peer_rows, gps_addr, noselect_intervals,
                observer_lat=obs_lat, observer_lon=obs_lon,
                known_servers=self._known_servers,
            )

            uncertainty = estimate_comparison_uncertainty(
                comparison["per_server_diff"]
            )

            # Drift regression over the full noselect coverage window
            if noselect_intervals:
                drift_start = noselect_intervals[0][0]
                drift_end   = noselect_intervals[-1][1]
            else:
                drift_start = drift_end = None

            if drift_start is not None:
                drift = estimate_drift_linear_regression(
                    peer_rows, drift_start, drift_end
                )
                # Attach datetime anchors so _draw_trend_line can use them
                drift["_trend_start_dt"] = drift_start
                drift["_trend_end_dt"]   = drift_end
            else:
                drift = {"drift_ms_per_hour": None, "r_squared": None,
                          "n_points": 0, "coverage_hours": 0.0,
                          "warning": "No noselect intervals available."}

            # Cache for potential re-use
            self._last_loop_rows   = loop_rows
            self._last_peer_rows   = peer_rows
            self._comparison_result = comparison
            self._uncertainty_result = uncertainty
            self._drift_result      = drift

            # --- Update summary labels ---
            self.lbl_gps_info.Text = "GPS PPS: %s" % gps_addr
            coverage_hours = comparison.get("coverage_hours", 0.0)
            n_intervals = len(comparison.get("noselect_intervals", []))
            self.lbl_noselect_info.Text = (
                "Noselect coverage: %.2f hrs (%d interval(s))" % (coverage_hours, n_intervals)
            )

            combined = uncertainty.get("combined", {})
            if combined.get("u_expanded_k2_ms") is not None:
                self.txt_uncertainty.Text = (
                    "Mean: %.3f ms   U(k=2): \u00b1%.3f ms   N=%d%s"
                    % (
                        combined["mean_ms"],
                        combined["u_expanded_k2_ms"],
                        combined["n"],
                        "  *low N" if combined.get("low_n_warning") else "",
                    )
                )
            else:
                self.txt_uncertainty.Text = "Insufficient data."

            if drift.get("drift_ms_per_hour") is not None:
                self.txt_drift.Text = (
                    "%.4f ms/hr  (%.4f ppm)   r\u00b2=%.3f   N=%d"
                    % (
                        drift["drift_ms_per_hour"],
                        drift["drift_ppm"],
                        drift["r_squared"],
                        drift["n_points"],
                    )
                )
                if drift.get("warning"):
                    self.txt_drift.Text += "  *"
            else:
                self.txt_drift.Text = drift.get("warning", "Insufficient data.")

            # --- Full text report ---
            report_text = generate_gps_comparison_report(
                comparison, uncertainty, drift, noselect_status
            )
            self.txt_output.Text = report_text

            # --- Charts ---
            self.update_charts(loop_rows, peer_rows, comparison, drift)

            # --- Optional export ---
            save_folder_settings(
                self.txt_log_folder.Text.strip(),
                self.txt_export_folder.Text.strip(),
                self.txt_observer_lat.Text.strip(),
                self.txt_observer_lon.Text.strip(),
            )

            if self.chk_export.Checked:
                export_folder = self.txt_export_folder.Text.strip().strip('"')
                if not export_folder:
                    raise RuntimeError(
                        "Export folder is empty.  Set an export folder or uncheck export."
                    )
                if not os.path.isdir(export_folder):
                    os.makedirs(export_folder)
                stamp  = __import__("datetime").datetime.now().strftime("%Y%m%d_%H%M%S")
                base   = os.path.join(export_folder, "gps_pps_comparison_%s" % stamp)
                _json_path = base + ".json"
                _handle = open(_json_path, "w", encoding="utf-8")
                try:
                    import json as _json
                    _json.dump({
                        "generated_at":      __import__("datetime").datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                        "dataset":           option.label,
                        "gps_pps_addr":      gps_addr,
                        "coverage_hours":    coverage_hours,
                        "uncertainty":       {
                            k: {kk: (vv if not isinstance(vv, float) or vv == vv else None)
                                for kk, vv in v.items()}
                            for k, v in uncertainty.get("per_server", {}).items()
                        },
                        "combined_uncertainty": combined,
                        "drift": {k: v for k, v in drift.items()
                                  if not k.startswith("_")},
                    }, _handle, indent=2, default=str)
                finally:
                    _handle.close()
                self.set_status("Comparison complete.  Saved: %s" % _json_path)
            else:
                self.set_status(
                    "Comparison complete.  GPS PPS: %s  Coverage: %.2f hrs"
                    % (gps_addr, coverage_hours)
                )

        except Exception as err:
            self.show_error(str(err))
            self.set_status("Comparison failed.")

    # -----------------------------------------------------------------------
    # Status bar
    # -----------------------------------------------------------------------

    def set_status(self, text):
        self.lbl_status.Text = text


# ---------------------------------------------------------------------------
# Standalone entry point
# ---------------------------------------------------------------------------

def main():
    if clr is None:
        sys.stderr.write(
            "This script requires IronPython 3.4 on Windows "
            "(clr / System.Windows.Forms not available).\n"
        )
        return 1
    Application.EnableVisualStyles()
    Application.Run(GPSPPSComparisonForm())
    return 0


if __name__ == "__main__":
    main()
