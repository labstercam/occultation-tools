#!/usr/bin/env ipy
"""IronPython 3.4 Windows Forms tool to analyze NTP loopstats/peerstats timing accuracy.

This presents the stronger working interpretation set: D, C, E, and G.
"""

import csv
import ipaddress
import json
import math
import os
import re
import socket
import sys
import urllib.request
from datetime import date, datetime, timedelta

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
            "FormWindowState",
            "FormStartPosition",
            "Label",
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
    ComboBox = forms_module.ComboBox
    ComboBoxStyle = forms_module.ComboBoxStyle
    DialogResult = forms_module.DialogResult
    FolderBrowserDialog = forms_module.FolderBrowserDialog
    Form = forms_module.Form
    FormWindowState = forms_module.FormWindowState
    FormStartPosition = forms_module.FormStartPosition
    Label = forms_module.Label
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
    ColumnStyle = forms_module.ColumnStyle
    DockStyle = forms_module.DockStyle
    FixedPanel = forms_module.FixedPanel
else:
    Color = None
    Font = None
    FontStyle = None
    Pen = None
    Point = None
    Rectangle = None
    Size = None
    SolidBrush = None
    ColumnStyle = None
    DockStyle = None
    FixedPanel = None
    RowStyle = None
    SizeType = None
    SplitContainer = None
    TableLayoutPanel = None
    AnchorStyles = None
    Application = None
    Button = None
    BorderStyle = None
    CheckBox = None
    ComboBox = None
    ComboBoxStyle = None
    DialogResult = None
    FolderBrowserDialog = None
    Form = object
    FormWindowState = None
    FormStartPosition = None
    Label = None
    MessageBox = None
    MessageBoxButtons = None
    MessageBoxIcon = None
    PictureBox = None
    ScrollBars = None
    TextBox = None



_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _SCRIPT_DIR)
import ntp_analysis_core as ntp_core
from ntp_analysis_core import *  # noqa: F401,F403

# Color palette for server addresses (cycling through distinct colors)
SERVER_COLORS = [
    Color.FromArgb(31, 119, 180),    # blue
    Color.FromArgb(255, 127, 14),    # orange
    Color.FromArgb(44, 160, 44),     # green
    Color.FromArgb(214, 39, 40),     # red
    Color.FromArgb(148, 103, 189),   # purple
    Color.FromArgb(140, 86, 75),     # brown
    Color.FromArgb(227, 119, 194),   # pink
    Color.FromArgb(127, 127, 127),   # gray
]

def get_server_color(server_address, server_to_color):
    """Get or assign a color for a server address."""
    if server_address not in server_to_color:
        idx = len(server_to_color) % len(SERVER_COLORS)
        server_to_color[server_address] = SERVER_COLORS[idx]
    return server_to_color[server_address]


class AnalyzerForm(Form):
    def __init__(self):
        self.Text = "NTP Clock Accuracy"
        self.Size = Size(1600, 960)
        self.MinimumSize = Size(1100, 700)
        self.StartPosition = FormStartPosition.CenterScreen
        self.WindowState = FormWindowState.Maximized

        self._options_by_label = {}
        self._plot_data = {}
        self._last_loop_rows = []
        self._last_peer_rows = []
        self._last_result = None
        self._last_aggregate_report = ""
        self._current_pit_result = None
        _known_servers_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "resources", "national_utc_ntp_servers.json",
        )
        self._known_servers = load_known_servers(os.path.normpath(_known_servers_path))
        ntp_core._load_ip_location_cache(os.path.normpath(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "resources", "ip_location_cache.json",
        )))

        default_font = Font("Segoe UI", 9)
        bold_font = Font("Segoe UI", 9, FontStyle.Bold)

        split = SplitContainer()
        split.Dock = DockStyle.Fill
        split.FixedPanel = FixedPanel.Panel1
        split.SplitterWidth = 6
        self.Controls.Add(split)
        self._main_split = split
        self.Shown += self.on_form_shown
        split.Panel1.Resize += self.on_left_panel_resize

        lp = split.Panel1

        self.lbl_title = Label()
        self.lbl_title.Text = "NTP Timing Accuracy Analysis"
        self.lbl_title.Font = Font("Segoe UI", 11, FontStyle.Bold)
        self.lbl_title.Location = Point(8, 8)
        self.lbl_title.Size = Size(440, 26)
        self.lbl_title.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.lbl_title)

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
        self.txt_log_folder.Leave += self.on_scan
        lp.Controls.Add(self.txt_log_folder)

        self.btn_browse_log = Button()
        self.btn_browse_log.Text = "Browse..."
        self.btn_browse_log.Location = Point(8, 96)
        self.btn_browse_log.Size = Size(120, 28)
        self.btn_browse_log.Click += self.on_browse_log
        lp.Controls.Add(self.btn_browse_log)

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

        # ---- Analysis time filter ----
        self.lbl_time_filter = Label()
        self.lbl_time_filter.Text = "Time filter (HH:MM):"
        self.lbl_time_filter.Location = Point(8, 250)
        self.lbl_time_filter.Size = Size(120, 20)
        lp.Controls.Add(self.lbl_time_filter)

        self.txt_time_start = TextBox()
        self.txt_time_start.Text = "00:00"
        self.txt_time_start.Location = Point(134, 248)
        self.txt_time_start.Size = Size(52, 24)
        lp.Controls.Add(self.txt_time_start)

        self.lbl_time_to = Label()
        self.lbl_time_to.Text = "to"
        self.lbl_time_to.Location = Point(190, 251)
        self.lbl_time_to.Size = Size(20, 20)
        lp.Controls.Add(self.lbl_time_to)

        self.txt_time_end = TextBox()
        self.txt_time_end.Text = "24:00"
        self.txt_time_end.Location = Point(214, 248)
        self.txt_time_end.Size = Size(52, 24)
        lp.Controls.Add(self.txt_time_end)

        self.btn_reset_time = Button()
        self.btn_reset_time.Text = "Reset"
        self.btn_reset_time.Location = Point(272, 246)
        self.btn_reset_time.Size = Size(64, 28)
        self.btn_reset_time.Click += self.on_reset_time_filter
        lp.Controls.Add(self.btn_reset_time)

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

        self.chk_raw_peer_points = CheckBox()
        self.chk_raw_peer_points.Text = "Charts: raw peer points"
        self.chk_raw_peer_points.Location = Point(8, 320)
        self.chk_raw_peer_points.Size = Size(228, 24)
        self.chk_raw_peer_points.Checked = False
        self.chk_raw_peer_points.CheckedChanged += self.on_raw_peer_points_toggled
        lp.Controls.Add(self.chk_raw_peer_points)

        self.lbl_pit_time = Label()
        self.lbl_pit_time.Text = "Point-in-time (HH:MM:SS):"
        self.lbl_pit_time.Location = Point(8, 348)
        self.lbl_pit_time.Size = Size(280, 20)
        lp.Controls.Add(self.lbl_pit_time)

        self.txt_pit_time = TextBox()
        self.txt_pit_time.Text = ""
        self.txt_pit_time.Location = Point(8, 370)
        self.txt_pit_time.Size = Size(160, 24)
        lp.Controls.Add(self.txt_pit_time)

        self.btn_pit = Button()
        self.btn_pit.Text = "Calculate PIT"
        self.btn_pit.Location = Point(174, 368)
        self.btn_pit.Size = Size(112, 28)
        self.btn_pit.Click += self.on_pit_calculate
        lp.Controls.Add(self.btn_pit)

        self.lbl_pit_result = Label()
        self.lbl_pit_result.Text = "Estimated Offset and Error to use:"
        self.lbl_pit_result.Font = bold_font
        self.lbl_pit_result.Location = Point(8, 402)
        self.lbl_pit_result.Size = Size(280, 20)
        lp.Controls.Add(self.lbl_pit_result)

        self.txt_pit_result = TextBox()
        self.txt_pit_result.Text = ""
        self.txt_pit_result.ReadOnly = True
        self.txt_pit_result.Font = bold_font
        self.txt_pit_result.Location = Point(8, 424)
        self.txt_pit_result.Size = Size(280, 24)
        lp.Controls.Add(self.txt_pit_result)

        self.lbl_pit_note = Label()
        self.lbl_pit_note.Text = "Estimated accuracy accounts for distance to servers so is lower than the theoretical max error bound of delay/2"
        self.lbl_pit_note.Location = Point(8, 450)
        self.lbl_pit_note.Size = Size(280, 34)
        lp.Controls.Add(self.lbl_pit_note)

        self.lbl_observer = Label()
        self.lbl_observer.Text = "Observer location (decimal degrees):"
        self.lbl_observer.Location = Point(8, 490)
        self.lbl_observer.Size = Size(280, 20)
        lp.Controls.Add(self.lbl_observer)

        self.lbl_observer_lat = Label()
        self.lbl_observer_lat.Text = "Lat:"
        self.lbl_observer_lat.Location = Point(8, 515)
        self.lbl_observer_lat.Size = Size(28, 20)
        lp.Controls.Add(self.lbl_observer_lat)

        self.txt_observer_lat = TextBox()
        self.txt_observer_lat.Text = ""
        self.txt_observer_lat.Location = Point(36, 512)
        self.txt_observer_lat.Size = Size(80, 24)
        self.txt_observer_lat.Font = default_font
        lp.Controls.Add(self.txt_observer_lat)

        self.lbl_observer_comma = Label()
        self.lbl_observer_comma.Text = ""
        self.lbl_observer_comma.Location = Point(119, 515)
        self.lbl_observer_comma.Size = Size(4, 20)
        lp.Controls.Add(self.lbl_observer_comma)

        self.lbl_observer_lon = Label()
        self.lbl_observer_lon.Text = "Lon:"
        self.lbl_observer_lon.Location = Point(124, 515)
        self.lbl_observer_lon.Size = Size(28, 20)
        lp.Controls.Add(self.lbl_observer_lon)

        self.txt_observer_lon = TextBox()
        self.txt_observer_lon.Text = ""
        self.txt_observer_lon.Location = Point(152, 512)
        self.txt_observer_lon.Size = Size(80, 24)
        self.txt_observer_lon.Font = default_font
        lp.Controls.Add(self.txt_observer_lon)

        self.lbl_observer_note = Label()
        self.lbl_observer_note.Text = "Used to tighten asymmetry bound for known servers"
        self.lbl_observer_note.Location = Point(8, 540)
        self.lbl_observer_note.Size = Size(280, 20)
        lp.Controls.Add(self.lbl_observer_note)

        self.btn_analyze = Button()
        self.btn_analyze.Text = "Analyze"
        self.btn_analyze.Font = bold_font
        self.btn_analyze.Location = Point(342, 316)
        self.btn_analyze.Size = Size(112, 32)
        self.btn_analyze.Anchor = AnchorStyles.Top | AnchorStyles.Right
        self.btn_analyze.Click += self.on_analyze
        lp.Controls.Add(self.btn_analyze)

        self.txt_output = TextBox()
        self.txt_output.Multiline = True
        self.txt_output.ScrollBars = ScrollBars.Both
        self.txt_output.ReadOnly = True
        self.txt_output.Font = Font("Consolas", 9)
        self.txt_output.Location = Point(8, 358)
        self.txt_output.Size = Size(446, 510)
        self.txt_output.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.txt_output)

        self.lbl_status = Label()
        self.lbl_status.Text = "Ready."
        self.lbl_status.Location = Point(8, 880)
        self.lbl_status.Size = Size(446, 22)
        self.lbl_status.Anchor = AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
        lp.Controls.Add(self.lbl_status)

        tbl = TableLayoutPanel()
        tbl.Dock = DockStyle.Fill
        tbl.RowCount = 4
        tbl.ColumnCount = 1
        tbl.RowStyles.Clear()
        for _ in range(4):
            tbl.RowStyles.Add(RowStyle(SizeType.Percent, 25.0))
        tbl.ColumnStyles.Clear()
        tbl.ColumnStyles.Add(ColumnStyle(SizeType.Percent, 100.0))
        split.Panel2.Controls.Add(tbl)

        self.chart_delay = self.create_plot_panel("Delay (Peerstats selected server, loop timeline)", Point(0, 0), Size(100, 100), "delay")
        self.chart_delay.Dock = DockStyle.Fill
        tbl.Controls.Add(self.chart_delay, 0, 0)

        self.chart_offset = self.create_plot_panel("Offset (Loopstats)", Point(0, 0), Size(100, 100), "offset")
        self.chart_offset.Dock = DockStyle.Fill
        tbl.Controls.Add(self.chart_offset, 0, 1)

        self.chart_jitter = self.create_plot_panel("Jitter (Loopstats / Peerstats)", Point(0, 0), Size(100, 100), "jitter")
        self.chart_jitter.Dock = DockStyle.Fill
        tbl.Controls.Add(self.chart_jitter, 0, 2)

        self.chart_dispersion = self.create_plot_panel("Dispersion (Peerstats)", Point(0, 0), Size(100, 100), "dispersion")
        self.chart_dispersion.Dock = DockStyle.Fill
        tbl.Controls.Add(self.chart_dispersion, 0, 3)

        self.prefill_defaults()

    def set_status(self, text):
        self.lbl_status.Text = text

    def on_form_shown(self, sender, event):
        # SplitterDistance is only valid after the control has a real width.
        split = self._main_split
        available_width = split.ClientSize.Width
        if available_width <= 0:
            return

        # Compute how much width the left panel actually needs after DPI scaling.
        required_right = 0
        for ctrl in split.Panel1.Controls:
            if not ctrl.Visible:
                continue
            required_right = max(required_right, int(ctrl.Right))

        # Add breathing room so right-anchored controls (Analyze/Browse) stay visible.
        preferred = max(640, required_right + 18)

        desired_left_min = 420
        desired_right_min = 500

        # If the current width cannot satisfy both desired mins, scale them down.
        if available_width < (desired_left_min + desired_right_min):
            left_min = max(120, int(available_width * 0.35))
            right_min = max(120, available_width - left_min - 1)
            if right_min < 120:
                right_min = 120
                left_min = max(120, available_width - right_min - 1)
        else:
            left_min = desired_left_min
            right_min = desired_right_min

        split.Panel1MinSize = left_min
        split.Panel2MinSize = right_min

        min_left = split.Panel1MinSize
        max_left = available_width - split.Panel2MinSize

        # Clamp to the valid runtime range to avoid WinForms SystemError.
        if max_left < min_left:
            left_width = min_left
        else:
            left_width = max(min_left, min(preferred, max_left))

        try:
            split.SplitterDistance = left_width
        except Exception:
            # Ignore one-time layout race conditions on some WinForms runtimes.
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
        inter = 7  # ~20% more vertical separation than the previous 6 px spacing
        label_h = 22
        text_h = 24
        button_h = 34  # ~20% taller than the previous 28 px buttons
        analyze_h = 38
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

        browse_w = 120
        self.btn_browse_log.Location = Point(margin, y)
        self.btn_browse_log.Size = Size(browse_w, button_h)
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

        # Time-of-day filter row
        tf_lbl_w = 120
        tf_txt_w = 52
        tf_to_w = 20
        tf_gap = 4
        tf_reset_w = 64
        self.lbl_time_filter.Location = Point(margin, y)
        self.lbl_time_filter.Size = Size(tf_lbl_w, label_h)
        xf = margin + tf_lbl_w + tf_gap
        self.txt_time_start.Location = Point(xf, y)
        self.txt_time_start.Size = Size(tf_txt_w, text_h)
        xf += tf_txt_w + tf_gap
        self.lbl_time_to.Location = Point(xf, y + 2)
        self.lbl_time_to.Size = Size(tf_to_w, label_h)
        xf += tf_to_w + tf_gap
        self.txt_time_end.Location = Point(xf, y)
        self.txt_time_end.Size = Size(tf_txt_w, text_h)
        xf += tf_txt_w + tf_gap
        self.btn_reset_time.Location = Point(xf, y - 1)
        self.btn_reset_time.Size = Size(tf_reset_w, button_h)
        y += max(text_h, button_h) + inter

        self.chk_export.Location = Point(margin, y)
        self.chk_export.Size = Size(min(220, full_w), text_h)
        y += text_h

        analyze_w = 112
        browse_export_w = 112
        controls_gap = 6
        one_row_min = browse_export_w + analyze_w + 160 + controls_gap * 2
        two_row_min = browse_export_w + analyze_w + controls_gap

        if full_w >= one_row_min:
            export_w = max(120, full_w - browse_export_w - analyze_w - controls_gap * 2)
            self.txt_export_folder.Location = Point(margin, y)
            self.txt_export_folder.Size = Size(export_w, text_h)

            bx = margin + export_w + controls_gap
            self.btn_browse_export.Location = Point(bx, y - 1)
            self.btn_browse_export.Size = Size(browse_export_w, button_h)

            ax = bx + browse_export_w + controls_gap
            self.btn_analyze.Location = Point(ax, y - 3)
            self.btn_analyze.Size = Size(analyze_w, analyze_h)
            y += max(text_h, analyze_h) + inter
        elif full_w >= two_row_min:
            self.txt_export_folder.Location = Point(margin, y)
            self.txt_export_folder.Size = Size(full_w, text_h)
            y += text_h + 4

            self.btn_browse_export.Location = Point(margin, y)
            self.btn_browse_export.Size = Size(browse_export_w, button_h)
            self.btn_analyze.Location = Point(margin + browse_export_w + controls_gap, y - 2)
            self.btn_analyze.Size = Size(analyze_w, analyze_h)
            y += max(button_h, analyze_h) + inter
        else:
            self.txt_export_folder.Location = Point(margin, y)
            self.txt_export_folder.Size = Size(full_w, text_h)
            y += text_h + 4

            self.btn_browse_export.Location = Point(margin, y)
            self.btn_browse_export.Size = Size(browse_export_w, button_h)
            y += button_h + 4

            self.btn_analyze.Location = Point(margin, y)
            self.btn_analyze.Size = Size(analyze_w, analyze_h)
            y += analyze_h + inter

        self.chk_raw_peer_points.Location = Point(margin, y)
        self.chk_raw_peer_points.Size = Size(min(260, full_w), text_h)
        y += text_h + inter

        self.lbl_pit_time.Location = Point(margin, y)
        self.lbl_pit_time.Size = Size(full_w, label_h)
        y += label_h

        pit_btn_w = 120
        pit_gap = 6
        pit_txt_w = max(80, full_w - pit_btn_w - pit_gap)
        self.txt_pit_time.Location = Point(margin, y)
        self.txt_pit_time.Size = Size(pit_txt_w, text_h)
        self.btn_pit.Location = Point(margin + pit_txt_w + pit_gap, y - 1)
        self.btn_pit.Size = Size(pit_btn_w, button_h)
        y += max(text_h, button_h) + inter

        self.lbl_pit_result.Location = Point(margin, y)
        self.lbl_pit_result.Size = Size(full_w, label_h)
        y += label_h

        self.txt_pit_result.Location = Point(margin, y)
        self.txt_pit_result.Size = Size(full_w, text_h)
        y += text_h + 3

        self.lbl_pit_note.Location = Point(margin, y)
        self.lbl_pit_note.Size = Size(full_w, label_h * 2)
        y += label_h * 2 + inter

        self.lbl_observer.Location = Point(margin, y)
        self.lbl_observer.Size = Size(full_w, label_h)
        y += label_h

        lat_lbl_w = 28
        lat_w = 80
        gap = 8
        lon_lbl_w = 28
        lon_w = 80
        x = margin
        self.lbl_observer_lat.Location = Point(x, y + 3)
        self.lbl_observer_lat.Size = Size(lat_lbl_w, label_h)
        x += lat_lbl_w
        self.txt_observer_lat.Location = Point(x, y)
        self.txt_observer_lat.Size = Size(lat_w, text_h)
        x += lat_w + gap
        self.lbl_observer_comma.Location = Point(x, y + 3)
        self.lbl_observer_comma.Size = Size(4, label_h)
        self.lbl_observer_lon.Location = Point(x, y + 3)
        self.lbl_observer_lon.Size = Size(lon_lbl_w, label_h)
        x += lon_lbl_w
        self.txt_observer_lon.Location = Point(x, y)
        self.txt_observer_lon.Size = Size(lon_w, text_h)
        y += text_h + 2

        self.lbl_observer_note.Location = Point(margin, y)
        self.lbl_observer_note.Size = Size(full_w, label_h)
        y += label_h + inter

        content_top = y
        status_height = 24
        output_height = max(120, panel.ClientSize.Height - content_top - status_height)
        self.txt_output.Location = Point(margin, content_top)
        self.txt_output.Size = Size(full_w, output_height)
        self.lbl_status.Location = Point(margin, panel.ClientSize.Height - status_height)
        self.lbl_status.Size = Size(full_w, status_height)

    def create_plot_panel(self, title, location, size, plot_key):
        container = Label()
        container.Text = title
        container.Font = Font("Segoe UI", 9, FontStyle.Bold)
        container.Location = location
        container.Size = size
        container.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right

        header_h = 30

        if plot_key == "jitter":
            legend_y = 4
            legend_font = Font("Segoe UI", 8)
            start_x = 300
            center_y = int(header_h / 2)

            loop_swatch = Label()
            loop_swatch.BackColor = Color.FromArgb(255, 127, 14)
            loop_swatch.BorderStyle = BorderStyle.FixedSingle
            loop_swatch.Location = Point(start_x, center_y - 2)
            loop_swatch.Size = Size(18, 5)
            container.Controls.Add(loop_swatch)

            loop_label = Label()
            loop_label.Text = "Loop (Local) Jitter"
            loop_label.Font = legend_font
            loop_label.Location = Point(start_x + 22, legend_y - 1)
            loop_label.Size = Size(150, 20)
            container.Controls.Add(loop_label)

            peer_x = start_x + 210
            peer_swatch = Label()
            peer_swatch.BackColor = Color.FromArgb(44, 160, 44)
            peer_swatch.BorderStyle = BorderStyle.FixedSingle
            peer_swatch.Location = Point(peer_x, center_y - 1)
            peer_swatch.Size = Size(14, 3)
            container.Controls.Add(peer_swatch)

            peer_label = Label()
            peer_label.Text = "Peer (Network) Jitter"
            peer_label.Font = legend_font
            peer_label.Location = Point(peer_x + 18, legend_y - 1)
            peer_label.Size = Size(180, 20)
            container.Controls.Add(peer_label)
        elif plot_key == "delay":
            # Server legend for delay chart is rendered in the header container.
            self._delay_legend_controls = []

        plot_box = PictureBox()
        plot_box.Location = Point(0, header_h)
        plot_box.Size = Size(size.Width, size.Height - header_h)
        plot_box.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
        plot_box.BorderStyle = BorderStyle.FixedSingle
        plot_box.BackColor = Color.White
        plot_box.Tag = plot_key
        plot_box.Paint += self.on_plot_paint
        container.Controls.Add(plot_box)
        return container

    def update_delay_header_legend(self, server_to_color, unique_servers, server_to_km=None):
        if not hasattr(self, "chart_delay") or self.chart_delay is None:
            return

        # Remove prior dynamic delay legend controls.
        old_controls = getattr(self, "_delay_legend_controls", [])
        for ctrl in old_controls:
            try:
                self.chart_delay.Controls.Remove(ctrl)
                ctrl.Dispose()
            except Exception:
                pass
        self._delay_legend_controls = []

        if not unique_servers:
            return

        legend_font = Font("Segoe UI", 8)
        legend_y = 4
        start_x = 460
        center_y = 15
        x_pos = start_x

        for server in unique_servers:
            if x_pos > self.chart_delay.ClientSize.Width - 178:
                break

            swatch = Label()
            swatch.BackColor = server_to_color.get(server, Color.Gray)
            swatch.BorderStyle = BorderStyle.FixedSingle
            swatch.Location = Point(x_pos, center_y - 2)
            swatch.Size = Size(18, 5)
            self.chart_delay.Controls.Add(swatch)
            self._delay_legend_controls.append(swatch)

            label = Label()
            server_label_text = server if server else "Unknown"
            if server_to_km and server in server_to_km:
                server_label_text = "%s (%d km)" % (server_label_text, int(round(server_to_km[server])))
            label.Text = server_label_text
            label.Font = legend_font
            label.Location = Point(x_pos + 22, legend_y - 1)
            label.Size = Size(150, 20)
            self.chart_delay.Controls.Add(label)
            self._delay_legend_controls.append(label)

            x_pos += 178

    def _get_plot_box(self, container):
        for ctrl in container.Controls:
            if isinstance(ctrl, PictureBox):
                return ctrl
        return None

    def invalidate_plots(self):
        for container in (self.chart_delay, self.chart_offset, self.chart_jitter, self.chart_dispersion):
            plot_box = self._get_plot_box(container)
            if plot_box is not None:
                plot_box.Invalidate()

    def on_plot_paint(self, sender, event):
        plot_key = sender.Tag
        chart_data = self._plot_data.get(plot_key)
        if chart_data is None:
            self.draw_empty_plot(event.Graphics, sender.ClientRectangle)
            return
        chart_data["plot_key"] = plot_key  # Pass plot_key to draw_plot
        self.draw_plot(event.Graphics, sender.ClientRectangle, chart_data)

    def draw_empty_plot(self, graphics, bounds):
        graphics.Clear(Color.White)
        brush = SolidBrush(Color.Gray)
        try:
            graphics.DrawString("Run Analyze to draw data.", Font("Segoe UI", 9), brush, 8, 8)
        finally:
            brush.Dispose()

    def draw_plot(self, graphics, bounds, chart_data):
        graphics.Clear(Color.White)

        left = 62
        top = 8
        right = 6
        bottom = 22
        width = max(10, bounds.Width - left - right)
        height = max(10, bounds.Height - top - bottom)

        plot_rect = Rectangle(left, top, width, height)

        x_start = chart_data["x_start"]
        x_end = chart_data["x_end"]
        y_min = chart_data["y_min"]   # ms
        y_max = chart_data["y_max"]   # ms
        y_step = chart_data["y_step"] # ms
        
        plot_key = chart_data.get("plot_key", "")
        
        # For delay chart, build series from delay points with server coloring
        if plot_key == "delay":
            delay_points = chart_data.get("points", [])
            server_to_color = chart_data.get("server_to_color", {})
            unique_servers = chart_data.get("unique_servers", [])
            
            # Build series with server-colored segments
            series = [
                {
                    "name": "Delay (Server color-coded)",
                    "points": delay_points,  # (timestamp, delay, server) tuples
                    "server_to_color": server_to_color,
                    "colored": True,
                    "unique_servers": unique_servers,
                }
            ]
        else:
            series = chart_data.get("series", [])

        one_hour = timedelta(hours=1)
        h_grid_pen = Pen(Color.FromArgb(220, 220, 220))   # faint horizontal gridlines
        v_grid_pen = Pen(Color.FromArgb(228, 228, 228))   # faint vertical gridlines
        zero_pen = Pen(Color.FromArgb(150, 150, 150))     # zero reference
        axis_pen = Pen(Color.FromArgb(100, 100, 100))     # axis border
        label_brush = SolidBrush(Color.FromArgb(80, 80, 80))
        label_font = Font("Segoe UI", 7)
        try:
            # --- Filter shading (excluded time regions, drawn first) ---
            filter_shade = chart_data.get("filter_shade_intervals")
            if filter_shade:
                self._draw_filter_shading(graphics, plot_rect, filter_shade, x_start, x_end)

            # --- Raw peer scatter dots (drawn before gridlines and main series) ---
            raw_peer_points = chart_data.get("raw_peer_points", [])
            stc = chart_data.get("server_to_color") or {}
            if raw_peer_points and stc:
                dot_brushes = {}
                for _srv, _col in stc.items():
                    dot_brushes[_srv] = SolidBrush(Color.FromArgb(120, _col.R, _col.G, _col.B))
                fallback_brush = SolidBrush(Color.FromArgb(120, 128, 128, 128))
                try:
                    for _rp in raw_peer_points:
                        _px = self.map_x(_rp[0], x_start, x_end, plot_rect)
                        _py = self.map_y(_rp[1] * 1000.0, y_min, y_max, plot_rect)
                        if plot_rect.Left <= _px <= plot_rect.Right and plot_rect.Top <= _py <= plot_rect.Bottom:
                            _b = dot_brushes.get(_rp[2] if len(_rp) > 2 else "", fallback_brush)
                            graphics.FillEllipse(_b, _px - 2, _py - 2, 4, 4)
                finally:
                    for _b in dot_brushes.values():
                        _b.Dispose()
                    fallback_brush.Dispose()

            # --- Vertical x-gridlines (hourly) ---
            hour = x_start
            while hour <= x_end:
                x = self.map_x(hour, x_start, x_end, plot_rect)
                graphics.DrawLine(v_grid_pen, x, plot_rect.Top, x, plot_rect.Bottom)
                if hour.hour % 2 == 0:
                    graphics.DrawString(hour.strftime("%H:%M"), label_font, label_brush, x - 14, plot_rect.Bottom + 2)
                hour = hour + one_hour

            # --- Horizontal y-gridlines and tick labels ---
            num_ticks = int(round((y_max - y_min) / y_step)) + 1
            for i in range(num_ticks):
                y_val = y_min + i * y_step
                py = self.map_y(y_val, y_min, y_max, plot_rect)
                if plot_rect.Top <= py <= plot_rect.Bottom:
                    is_zero = abs(y_val) < y_step * 1e-4
                    if is_zero:
                        graphics.DrawLine(zero_pen, plot_rect.Left, py, plot_rect.Right, py)
                    else:
                        graphics.DrawLine(h_grid_pen, plot_rect.Left, py, plot_rect.Right, py)
                    lbl = ntp_core._format_y_label_ms(y_val, y_step)
                    lbl_y = max(plot_rect.Top, min(plot_rect.Bottom - 10, py - 6))
                    graphics.DrawString(lbl, label_font, label_brush, 2, lbl_y)

            # --- Axis border ---
            graphics.DrawRectangle(axis_pen, plot_rect)
            graphics.DrawString("UTC", label_font, label_brush, plot_rect.Right - 24, plot_rect.Bottom + 2)

            # --- Data series ---
            for item in series:
                points = item["points"]
                if len(points) < 1:
                    continue

                # Check if this is a server-colored series (for delay chart)
                if item.get("colored", False):
                    # Draw delay line with server-based color segments
                    server_to_color = item.get("server_to_color", {})
                    prev_xy = None
                    prev_server = None
                    
                    for point_data in points:
                        dt_value = point_data[0]
                        y_value = point_data[1]
                        server = point_data[2] if len(point_data) > 2 else ""
                        
                        x = self.map_x(dt_value, x_start, x_end, plot_rect)
                        y_ms = y_value * 1000.0
                        y = self.map_y(y_ms, y_min, y_max, plot_rect)
                        
                        if prev_xy is not None:
                            # Color each segment by the active source server at the
                            # previous point; color changes where source changes.
                            segment_color = server_to_color.get(prev_server, Color.Gray)
                            segment_pen = Pen(segment_color, 2)
                            try:
                                graphics.DrawLine(segment_pen, prev_xy[0], prev_xy[1], x, y)
                            finally:
                                segment_pen.Dispose()
                        prev_xy = (x, y)
                        prev_server = server
                else:
                    # Normal single-color series
                    line_pen = Pen(item["color"], item.get("width", 2))
                    try:
                        prev_xy = None
                        for dt_value, y_value in points:
                            x = self.map_x(dt_value, x_start, x_end, plot_rect)
                            y_ms = y_value * 1000.0
                            y = self.map_y(y_ms, y_min, y_max, plot_rect)
                            if prev_xy is not None:
                                graphics.DrawLine(line_pen, prev_xy[0], prev_xy[1], x, y)
                            prev_xy = (x, y)
                    finally:
                        line_pen.Dispose()

        finally:
            h_grid_pen.Dispose()
            v_grid_pen.Dispose()
            zero_pen.Dispose()
            axis_pen.Dispose()
            label_brush.Dispose()
            label_font.Dispose()

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

    def update_charts(self, loop_rows, peer_rows, use_raw_peer_points):
        x_start, x_end = compute_axis_day_bounds(loop_rows, peer_rows)
        if x_start is None or x_end is None:
            self._plot_data = {}
            self.update_delay_header_legend({}, [])
            self.invalidate_plots()
            return

        selected_peer_rows, _note = select_peer_subset(peer_rows)

        offset_points = []
        loop_jitter_points = []
        for row in sorted(loop_rows, key=lambda value: (value.mjd, value.sec_of_day)):
            stamp = to_utc_datetime(row.mjd, row.sec_of_day)
            offset_points.append((stamp, row.offset))
            loop_jitter_points.append((stamp, row.jitter))

        peer_jitter_points = []
        dispersion_points = []
        server_to_color = {}  # Server address -> Color object

        # Build selected-peer timeline from peerstats for server coloring.
        # Reduce to one active selected server per second.
        selected_timeline_rows = reduce_to_active_timeline(selected_peer_rows)
        peer_timeline = []
        for row in selected_timeline_rows:
            stamp = to_utc_datetime(row.mjd, row.sec_of_day)
            server = row.server_address if hasattr(row, "server_address") else ""
            get_server_color(server, server_to_color)
            peer_timeline.append((stamp, server))

        # Dispersion is densified later on the loop timeline (same approach
        # as selected-server delay/jitter), so do not append sparse points here.

        # Delay chart is sampled on the loopstats timeline, but value is the
        # true peerstats delay of the active selected server.
        delay_points = []  # List of (timestamp, selected_server_delay, server) tuples

        # Build per-server raw delay/jitter/dispersion streams from full peer rows.
        delays_by_server = {}
        jitters_by_server = {}
        dispersions_by_server = {}
        for row in sorted(peer_rows, key=lambda value: (value.mjd, value.sec_of_day)):
            stamp = to_utc_datetime(row.mjd, row.sec_of_day)
            server = row.server_address if hasattr(row, "server_address") else ""
            if server not in delays_by_server:
                delays_by_server[server] = []
            if server not in jitters_by_server:
                jitters_by_server[server] = []
            if server not in dispersions_by_server:
                dispersions_by_server[server] = []
            delays_by_server[server].append((stamp, row.delay))
            jitters_by_server[server].append((stamp, row.jitter))
            dispersions_by_server[server].append((stamp, row.dispersion))

        delay_index_by_server = {}
        jitter_index_by_server = {}
        dispersion_index_by_server = {}
        for server in delays_by_server.keys():
            delay_index_by_server[server] = -1
        for server in jitters_by_server.keys():
            jitter_index_by_server[server] = -1
        for server in dispersions_by_server.keys():
            dispersion_index_by_server[server] = -1

        timeline_index = 0
        active_server = ""
        if peer_timeline:
            active_server = peer_timeline[0][1]

        for row in sorted(loop_rows, key=lambda value: (value.mjd, value.sec_of_day)):
            stamp = to_utc_datetime(row.mjd, row.sec_of_day)
            while timeline_index + 1 < len(peer_timeline) and peer_timeline[timeline_index + 1][0] <= stamp:
                timeline_index += 1
                active_server = peer_timeline[timeline_index][1]

            # Carry-forward latest delay from the active selected server.
            server_delays = delays_by_server.get(active_server, [])
            if server_delays:
                idx = delay_index_by_server.get(active_server, -1)
                while idx + 1 < len(server_delays) and server_delays[idx + 1][0] <= stamp:
                    idx += 1
                delay_index_by_server[active_server] = idx
                if idx >= 0:
                    delay_points.append((stamp, server_delays[idx][1], active_server))

            # Carry-forward latest jitter from the active selected server.
            server_jitters = jitters_by_server.get(active_server, [])
            if server_jitters:
                j_idx = jitter_index_by_server.get(active_server, -1)
                while j_idx + 1 < len(server_jitters) and server_jitters[j_idx + 1][0] <= stamp:
                    j_idx += 1
                jitter_index_by_server[active_server] = j_idx
                if j_idx >= 0:
                    peer_jitter_points.append((stamp, server_jitters[j_idx][1]))

            # Carry-forward latest dispersion from the active selected server.
            server_dispersions = dispersions_by_server.get(active_server, [])
            if server_dispersions:
                d_idx = dispersion_index_by_server.get(active_server, -1)
                while d_idx + 1 < len(server_dispersions) and server_dispersions[d_idx + 1][0] <= stamp:
                    d_idx += 1
                dispersion_index_by_server[active_server] = d_idx
                if d_idx >= 0:
                    dispersion_points.append((stamp, server_dispersions[d_idx][1]))

        if not server_to_color:
            get_server_color("", server_to_color)

        # Assign a distinct colour to every server seen in peerstats (not just
        # the ones that were ever the selected/active peer).  This ensures the
        # raw-peer scatter dots are coloured and every server appears in the legend.
        for _srv in sorted(delays_by_server.keys()):
            get_server_color(_srv, server_to_color)

        def y_limits_ms(series_list):
            """Compute y_min, y_max, y_step in ms for a list of point series (values in seconds).
            Always spans zero; snapped to a nice tick interval."""
            values_ms = []
            for points in series_list:
                values_ms.extend([v * 1000.0 for _, v in points])
            if not values_ms:
                return -1.0, 1.0, 1.0
            raw_min = min(values_ms)
            raw_max = max(values_ms)
            # Always bracket zero
            lo = min(raw_min, 0.0)
            hi = max(raw_max, 0.0)
            span = hi - lo
            if span == 0.0:
                lo -= 0.5
                hi += 0.5
                span = 1.0
            step = ntp_core._choose_y_step_ms(span)
            # Snap outward to step boundaries
            y_min = math.floor(lo / step) * step
            y_max = math.ceil(hi / step) * step
            # Ensure at least 2 ticks of range
            if y_max - y_min < step * 2:
                y_max = y_min + step * 2
            return y_min, y_max, step

        # Collect raw per-server scatter points when checkbox is active
        raw_peer_delay_pts = []   # (timestamp, delay, server)
        raw_peer_jitter_pts = []  # (timestamp, jitter, server)
        raw_peer_disp_pts = []    # (timestamp, dispersion, server)
        if use_raw_peer_points:
            for server, pts in delays_by_server.items():
                for stamp, val in pts:
                    raw_peer_delay_pts.append((stamp, val, server))
            for server, pts in jitters_by_server.items():
                for stamp, val in pts:
                    raw_peer_jitter_pts.append((stamp, val, server))
            for server, pts in dispersions_by_server.items():
                for stamp, val in pts:
                    raw_peer_disp_pts.append((stamp, val, server))

        offset_min, offset_max, offset_step = y_limits_ms([offset_points])
        raw_j_flat = [(s, v) for s, v, _ in raw_peer_jitter_pts]
        jitter_min, jitter_max, jitter_step = y_limits_ms([loop_jitter_points, peer_jitter_points] + ([raw_j_flat] if raw_j_flat else []))
        raw_d_flat = [(s, v) for s, v, _ in raw_peer_disp_pts]
        disp_min, disp_max, disp_step = y_limits_ms([dispersion_points] + ([raw_d_flat] if raw_d_flat else []))
        # For delay points, extract just the values (second element of tuple)
        delay_values_only = [(dt, val) for dt, val, srv in delay_points]
        raw_dl_flat = [(s, v) for s, v, _ in raw_peer_delay_pts]
        delay_min, delay_max, delay_step = y_limits_ms([delay_values_only] + ([raw_dl_flat] if raw_dl_flat else []))

        # Build legend server list: selected (ever-active) peers first so they
        # appear at the left, then all remaining peers alphabetically.
        _selected_server_set = set([srv for _stamp, srv in peer_timeline])
        _all_server_set = set(server_to_color.keys())
        unique_servers = sorted(_selected_server_set) + sorted(_all_server_set - _selected_server_set)
        if not unique_servers and delay_points:
            unique_servers = sorted(set([srv for _stamp, _value, srv in delay_points]))
        obs_lat, obs_lon = self._get_observer_coords()
        server_to_km = {}
        for _srv in list(server_to_color.keys()):
            if _srv:
                _loc = resolve_server_location(_srv, self._known_servers, obs_lat, obs_lon)
                if _loc["geo_km"] is not None:
                    server_to_km[_srv] = _loc["geo_km"]
        self.update_delay_header_legend(server_to_color, unique_servers, server_to_km)

        self._plot_data = {
            "delay": {
                "x_start": x_start,
                "x_end": x_end,
                "y_min": delay_min,
                "y_max": delay_max,
                "y_step": delay_step,
                "points": delay_points,  # List of (timestamp, delay, server) tuples
                "server_to_color": server_to_color,
                "unique_servers": unique_servers,
                "raw_peer_points": raw_peer_delay_pts,
            },
            "offset": {
                "x_start": x_start,
                "x_end": x_end,
                "y_min": offset_min,
                "y_max": offset_max,
                "y_step": offset_step,
                "series": [
                    {"name": "Offset", "color": Color.FromArgb(31, 119, 180), "points": offset_points},
                ],
            },
            "jitter": {
                "x_start": x_start,
                "x_end": x_end,
                "y_min": jitter_min,
                "y_max": jitter_max,
                "y_step": jitter_step,
                "server_to_color": server_to_color,
                "raw_peer_points": raw_peer_jitter_pts,
                "series": [
                    {
                        "name": "Loop Jitter",
                        "color": Color.FromArgb(255, 127, 14),
                        "width": 3,
                        "points": loop_jitter_points,
                    },
                    {
                        "name": "Peer Jitter",
                        "color": Color.FromArgb(44, 160, 44),
                        "width": 2,
                        "points": peer_jitter_points,
                    },
                ],
            },
            "dispersion": {
                "x_start": x_start,
                "x_end": x_end,
                "y_min": disp_min,
                "y_max": disp_max,
                "y_step": disp_step,
                "server_to_color": server_to_color,
                "raw_peer_points": raw_peer_disp_pts,
                "series": [
                    {"name": "Dispersion", "color": Color.FromArgb(214, 39, 40), "points": dispersion_points},
                ],
            },
        }

        self.invalidate_plots()

    def _get_observer_coords(self):
        """Parse observer lat/lon text boxes. Returns (lat, lon) as floats, or (None, None) if invalid."""
        try:
            lat = float(self.txt_observer_lat.Text.strip())
            lon = float(self.txt_observer_lon.Text.strip())
        except (ValueError, AttributeError):
            return None, None
        # Detect swapped entry: latitude must be -90..90, longitude -180..180.
        lat_valid = -90.0 <= lat <= 90.0
        lon_valid = -180.0 <= lon <= 180.0
        if not lat_valid and lon_valid and -90.0 <= lon <= 90.0 and -180.0 <= lat <= 180.0:
            print("[observer] WARNING: lat=%r lon=%r looks swapped — auto-correcting to lat=%r lon=%r" % (lat, lon, lon, lat))
            lat, lon = lon, lat
        elif not lat_valid or not lon_valid:
            print("[observer] WARNING: lat=%r lon=%r out of valid range — ignored" % (lat, lon))
            return None, None
        return lat, lon

    def prefill_from_event(self, log_folder, event_dt, lat, lon):
        """Pre-populate the analyser with event context and trigger analysis.

        Parameters
        ----------
        log_folder : str   Path to the NTP stats folder.
        event_dt   : datetime  UTC event datetime.
        lat        : float  Observer latitude.
        lon        : float  Observer longitude.
        """
        try:
            if log_folder and os.path.isdir(log_folder):
                self.txt_log_folder.Text = log_folder
                if not self.txt_export_folder.Text.strip():
                    self.txt_export_folder.Text = os.path.join(log_folder, "reports")

            if lat is not None:
                self.txt_observer_lat.Text = "%.3f" % round(lat, 3)
            if lon is not None:
                self.txt_observer_lon.Text = "%.3f" % round(lon, 3)

            if event_dt is not None:
                pit = "%02d:%02d:%02d" % (event_dt.hour, event_dt.minute, event_dt.second)
                self.txt_pit_time.Text = pit

            # Scan and then try to select the dataset matching the event date.
            self.scan_options()

            if event_dt is not None:
                date_tag = event_dt.strftime("%Y%m%d")
                date_label = "%s-%s-%s" % (date_tag[:4], date_tag[4:6], date_tag[6:])
                for i in range(self.cmb_dataset.Items.Count):
                    item = self.cmb_dataset.Items[i]
                    if date_tag in item or date_label in item:
                        self.cmb_dataset.SelectedIndex = i
                        break

            # Trigger analysis automatically.
            self.on_analyze(None, None)
        except Exception:
            pass  # Best-effort; leave form open for manual use.

    def prefill_defaults(self):
        saved = load_folder_settings()
        saved_log = saved.get("log_folder", "").strip()
        saved_export = saved.get("export_folder", "").strip()

        if saved_log and os.path.isdir(saved_log):
            self.txt_log_folder.Text = saved_log
            if saved_export:
                self.txt_export_folder.Text = saved_export
            else:
                self.txt_export_folder.Text = os.path.join(saved_log, "reports")
        else:
            candidates = discover_candidate_dirs()
            if candidates:
                self.txt_log_folder.Text = candidates[0]
                self.txt_export_folder.Text = os.path.join(candidates[0], "reports")

        if not self.txt_export_folder.Text.strip() and self.txt_log_folder.Text.strip():
            self.txt_export_folder.Text = os.path.join(self.txt_log_folder.Text.strip(), "reports")
        self.txt_observer_lat.Text = saved.get("observer_lat", "").strip()
        self.txt_observer_lon.Text = saved.get("observer_lon", "").strip()
        self.on_export_toggle(None, None)
        self.scan_options()

    def show_error(self, message):
        MessageBox.Show(self, message, "NTP Analyzer", MessageBoxButtons.OK, MessageBoxIcon.Error)

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
            save_folder_settings(self.txt_log_folder.Text.strip(), self.txt_export_folder.Text.strip(),
                                  self.txt_observer_lat.Text.strip(), self.txt_observer_lon.Text.strip())
            self.scan_options()

    def on_browse_export(self, sender, event):
        chosen = self.choose_folder(self.txt_export_folder.Text.strip())
        if chosen:
            self.txt_export_folder.Text = chosen
            save_folder_settings(self.txt_log_folder.Text.strip(), self.txt_export_folder.Text.strip(),
                                  self.txt_observer_lat.Text.strip(), self.txt_observer_lon.Text.strip())

    def on_export_toggle(self, sender, event):
        enabled = self.chk_export.Checked
        self.txt_export_folder.Enabled = enabled
        self.btn_browse_export.Enabled = enabled

    def on_scan(self, sender, event):
        # When triggered by the Leave event on txt_log_folder, only re-scan if
        # the folder path has actually changed.  This prevents the selection
        # being reset to index 0 when focus simply moves away from the textbox
        # (e.g. the user clicks Analyse without editing the folder).
        current_folder = self.txt_log_folder.Text.strip().strip('"')
        if sender is self.txt_log_folder:
            if current_folder == getattr(self, '_last_scanned_folder', None):
                return
        save_folder_settings(self.txt_log_folder.Text.strip(), self.txt_export_folder.Text.strip(),
                              self.txt_observer_lat.Text.strip(), self.txt_observer_lon.Text.strip())
        self.scan_options()

    def scan_options(self):
        log_folder = self.txt_log_folder.Text.strip().strip('"')
        self._last_scanned_folder = log_folder
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
        except Exception as error:
            self.show_error("Failed to scan datasets:\n%s" % str(error))
            self.set_status("Scan failed.")
            return

        filter_text = self.txt_day_filter.Text.strip().lower()
        if filter_text:
            options = [o for o in options if filter_text in o.key.lower() or filter_text in o.label.lower()]

        if not options:
            self.set_status("No matching loopstats/peerstats datasets found.")
            return

        for option in options:
            self.cmb_dataset.Items.Add(option.label)
            self._options_by_label[option.label] = option

        self.cmb_dataset.SelectedIndex = 0
        self.set_status("Loaded %d dataset option(s)." % len(options))

    def get_selected_option(self):
        selected_label = self.cmb_dataset.Text
        if not selected_label:
            raise RuntimeError("No dataset selected.")
        option = self._options_by_label.get(selected_label)
        if option is None:
            raise RuntimeError("Dataset selection is invalid. Please rescan datasets.")
        return option

    # -----------------------------------------------------------------------
    # Time-of-day filter helpers
    # -----------------------------------------------------------------------

    def _parse_time_filter(self):
        """Parse HH:MM text boxes → (start_sec, end_sec).
        Returns (0.0, 86400.0) on invalid input or default values."""
        def _parse_hhmm(text, default_sec):
            text = text.strip()
            try:
                parts = text.split(":")
                if len(parts) == 2:
                    h = int(parts[0])
                    m = int(parts[1])
                    if 0 <= h <= 24 and 0 <= m <= 59:
                        sec = h * 3600 + m * 60
                        return 86400.0 if sec >= 86400 else float(sec)
            except (ValueError, AttributeError):
                pass
            return default_sec
        start_sec = _parse_hhmm(self.txt_time_start.Text, 0.0)
        end_sec   = _parse_hhmm(self.txt_time_end.Text,   86400.0)
        if start_sec >= end_sec:
            return 0.0, 86400.0
        return start_sec, end_sec

    def _apply_time_filter(self, loop_rows, peer_rows):
        """Filter rows to the current time-of-day window.
        Returns (filtered_loop, filtered_peer, start_sec, end_sec, is_filtered)."""
        start_sec, end_sec = self._parse_time_filter()
        is_filtered = (start_sec > 0.0 or end_sec < 86400.0)
        if not is_filtered:
            return loop_rows, peer_rows, start_sec, end_sec, False
        filtered_loop = [r for r in loop_rows if start_sec <= r.sec_of_day < end_sec]
        filtered_peer = [r for r in peer_rows if start_sec <= r.sec_of_day < end_sec]
        return filtered_loop, filtered_peer, start_sec, end_sec, True

    def _apply_filter_shading(self, start_sec, end_sec):
        """Inject filter_shade_intervals into all _plot_data entries and redraw."""
        for cd in self._plot_data.values():
            x_start = cd.get("x_start")
            x_end   = cd.get("x_end")
            if x_start is None:
                continue
            filter_base = x_start.replace(hour=0, minute=0, second=0, microsecond=0)
            shade = []
            if start_sec > 0.0:
                shade_end = filter_base + timedelta(seconds=start_sec)
                if shade_end > x_start:
                    shade.append((x_start, shade_end))
            if end_sec < 86400.0:
                shade_start = filter_base + timedelta(seconds=end_sec)
                if shade_start < x_end:
                    shade.append((shade_start, x_end))
            cd["filter_shade_intervals"] = shade
        self.invalidate_plots()

    def _draw_filter_shading(self, graphics, plot_rect, intervals, x_start, x_end):
        """Draw light-gray shading rectangles for the excluded time regions."""
        shade_brush = SolidBrush(Color.FromArgb(48, 160, 160, 160))
        try:
            for start_dt, end_dt in intervals:
                x0 = self.map_x(start_dt, x_start, x_end, plot_rect)
                x1 = self.map_x(end_dt,   x_start, x_end, plot_rect)
                x0 = max(plot_rect.Left, min(plot_rect.Right, x0))
                x1 = max(plot_rect.Left, min(plot_rect.Right, x1))
                band_w = max(1, x1 - x0)
                graphics.FillRectangle(shade_brush,
                                       x0, plot_rect.Top, band_w, plot_rect.Height)
        finally:
            shade_brush.Dispose()

    def on_raw_peer_points_toggled(self, sender, event):
        """Immediately re-render charts with or without raw peer dots."""
        if self._last_loop_rows:
            self.update_charts(self._last_loop_rows, self._last_peer_rows, self.chk_raw_peer_points.Checked)
            # Re-apply filter shading if a filter is active (it was cleared by update_charts rebuild)
            _, _, t_start_sec, t_end_sec, is_filtered = self._apply_time_filter(
                self._last_loop_rows, self._last_peer_rows)
            if is_filtered:
                self._apply_filter_shading(t_start_sec, t_end_sec)

    def on_reset_time_filter(self, sender, event):
        """Reset time filter to defaults and re-analyze if data is loaded."""
        self.txt_time_start.Text = "00:00"
        self.txt_time_end.Text = "24:00"
        if self._plot_data:
            # Re-run analysis without triggering export (Reset is not Analyze+Export)
            was_export = self.chk_export.Checked
            self.chk_export.Checked = False
            try:
                self.on_analyze(None, None)
            finally:
                self.chk_export.Checked = was_export

    # -----------------------------------------------------------------------

    def on_analyze(self, sender, event):
        try:
            option = self.get_selected_option()
            loop_rows = parse_loopstats(option.loop_path, option.target_mjd)
            peer_rows = parse_peerstats(option.peer_path, option.target_mjd)
            obs_lat, obs_lon = self._get_observer_coords()

            # Apply time-of-day filter
            filtered_loop, filtered_peer, t_start_sec, t_end_sec, is_filtered = \
                self._apply_time_filter(loop_rows, peer_rows)

            result = analyze(option, filtered_loop, filtered_peer,
                             known_servers=self._known_servers,
                             observer_lat=obs_lat, observer_lon=obs_lon)
            self._last_loop_rows = filtered_loop
            self._last_peer_rows = filtered_peer
            self._last_result = result
            self._last_aggregate_report = generate_report(result)
            if is_filtered:
                def _sec_to_hhmm(s):
                    h = int(s) // 3600
                    m = (int(s) % 3600) // 60
                    return "%02d:%02d" % (h, m)
                end_str = "24:00" if t_end_sec >= 86400.0 else _sec_to_hhmm(t_end_sec)
                self._last_aggregate_report = (
                    "Analysis time filter: %s \u2013 %s UTC\r\n\r\n" % (
                        _sec_to_hhmm(t_start_sec), end_str)
                    + self._last_aggregate_report
                )
            self.update_charts(filtered_loop, filtered_peer, self.chk_raw_peer_points.Checked)
            if is_filtered:
                self._apply_filter_shading(t_start_sec, t_end_sec)

            pit = self._compute_pit_for_display(filtered_loop, filtered_peer, result)
            self._show_combined_output(pit)

            save_folder_settings(self.txt_log_folder.Text.strip(), self.txt_export_folder.Text.strip(),
                                  self.txt_observer_lat.Text.strip(), self.txt_observer_lon.Text.strip())

            if self.chk_export.Checked:
                export_folder = self.txt_export_folder.Text.strip().strip('"')
                if not export_folder:
                    raise RuntimeError("Export folder is empty. Set an export folder or uncheck export.")
                json_path, csv_path = resolve_export_paths(export_folder, result)
                export_json(json_path, result)
                export_csv(csv_path, result)
                self.set_status("Analysis complete. Saved JSON: %s | CSV: %s" % (json_path, csv_path))
            else:
                self.set_status("Analysis complete.")

        except Exception as error:
            self.show_error(str(error))
            self.set_status("Analysis failed.")

    def _compute_pit_for_display(self, loop_rows, peer_rows, result):
        """Return pit_result using the user-entered HH:MM:SS time if valid, else the last loopstats record."""
        hms_text = self.txt_pit_time.Text.strip()
        if hms_text:
            try:
                query_sec = ntp_core._parse_pit_time_sec(hms_text)
                query_mjd = max(result.mjds) if result.mjds else max(r.mjd for r in loop_rows)
                obs_lat, obs_lon = self._get_observer_coords()
                return estimate_offset_at_time(query_mjd, query_sec, loop_rows, peer_rows,
                                               known_servers=self._known_servers,
                                               observer_lat=obs_lat, observer_lon=obs_lon)
            except Exception as err:
                self.show_error("Invalid point-in-time entry: %s\r\nUsing last loopstats record." % str(err))
        return result.pit_result

    def _update_pit_result_display(self, pit):
        """Update the read-only summary box with the best-estimate offset and error."""
        self._current_pit_result = pit
        if pit is None:
            self.txt_pit_result.Text = ""
            return
        alt_exp = pit.get("alt_u_expanded")
        primary_exp = pit["u_expanded"]
        if alt_exp is not None and alt_exp < primary_exp:
            offset_ms = pit["alt_best_offset"] * 1000.0
            error_ms = alt_exp * 1000.0
        else:
            offset_ms = pit["best_offset"] * 1000.0
            error_ms = primary_exp * 1000.0
        self.txt_pit_result.Text = "Offset: %.1f ms; Error: %.1f ms" % (offset_ms, error_ms)

    def get_pit_result(self):
        """Return the currently displayed PIT result as (offset_ms, error_ms), or None."""
        pit = self._current_pit_result
        if pit is None:
            return None
        alt_exp = pit.get("alt_u_expanded")
        primary_exp = pit["u_expanded"]
        if alt_exp is not None and alt_exp < primary_exp:
            return (pit["alt_best_offset"] * 1000.0, alt_exp * 1000.0)
        return (pit["best_offset"] * 1000.0, primary_exp * 1000.0)

    def _show_combined_output(self, pit):
        """Compose and display PIT section (top) then the aggregate report (below)."""
        if pit is not None:
            pit_text = "\r\n".join(format_pit_section(pit))
        else:
            pit_text = "(No point-in-time estimate available.)"
        separator = "\r\n" + ("=" * 80) + "\r\n\r\n"
        self.txt_output.Text = pit_text + separator + self._last_aggregate_report
        self._update_pit_result_display(pit)

    def on_pit_calculate(self, sender, event):
        try:
            if not self._last_loop_rows:
                self.show_error("Run Analyze first to load a dataset.")
                return
            hms_text = self.txt_pit_time.Text.strip()
            if not hms_text:
                self.show_error("Enter a time in HH:MM:SS format.")
                return
            query_sec = ntp_core._parse_pit_time_sec(hms_text)
            query_mjd = max(self._last_result.mjds) if self._last_result and self._last_result.mjds else max(r.mjd for r in self._last_loop_rows)
            obs_lat, obs_lon = self._get_observer_coords()
            pit = estimate_offset_at_time(query_mjd, query_sec, self._last_loop_rows, self._last_peer_rows,
                                          known_servers=self._known_servers,
                                          observer_lat=obs_lat, observer_lon=obs_lon)
            self._show_combined_output(pit)
            self._update_pit_result_display(pit)
            self.set_status("Point-in-time estimate calculated for %s." % hms_text)
        except Exception as error:
            self.show_error(str(error))
            self.set_status("Point-in-time calculation failed.")


def main():
    if clr is None:
        sys.stderr.write(
            "This script requires IronPython 3.4 on Windows (clr/System.Windows.Forms not available).\n"
        )
        return 1

    if sys.version_info[0] != 3 or sys.version_info[1] < 4:
        sys.stderr.write(
            "This script targets IronPython 3.4+. Current Python: %d.%d\n"
            % (sys.version_info[0], sys.version_info[1])
        )
        return 1

    Application.EnableVisualStyles()
    Application.Run(AnalyzerForm())
    return 0


if __name__ == "__main__":
    main()