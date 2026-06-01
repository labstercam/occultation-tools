"""PC Performance Testing tool for SharpCap.

This dialog reuses the live frame-capture pattern used by the line delay
calibration tool and focuses on timestamp stability under system load.
"""

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("System.IO.Compression")
clr.AddReference("OxyPlot")
clr.AddReference("OxyPlot.WindowsForms")

import math
import os
import sys
import time
import threading
from datetime import datetime, timedelta

try:
    _SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
except Exception:
    _SCRIPT_DIR = os.path.abspath(os.getcwd())
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

import System
import System.Drawing.Imaging
import System.IO
import System.IO.Compression
clr.AddReference("System.Management")
import System.Text
import OxyPlot
import OxyPlot.WindowsForms

from System.Drawing import *
from System.Windows.Forms import *
from System.Diagnostics import PerformanceCounter

try:
    import System.Management
    _SYSTEM_MANAGEMENT_AVAILABLE = True
except Exception:
    _SYSTEM_MANAGEMENT_AVAILABLE = False

try:
    from theme import apply_theme_to_control
    _THEME_AVAILABLE = True
except Exception:
    _THEME_AVAILABLE = False

try:
    import config as _om_config
    _OM_CONFIG_AVAILABLE = True
except Exception:
    _om_config = None
    _OM_CONFIG_AVAILABLE = False

try:
    import adv_helper
    _ADV_AVAILABLE = adv_helper.is_advlib_available()
except Exception:
    adv_helper = None
    _ADV_AVAILABLE = False

try:
    _ = SharpCap
except NameError:
    SharpCap = None


class SimpleXlsxWriter:
    """Minimal XLSX writer using System.IO.Compression."""

    def _col_letter(self, col_idx):
        result = ''
        n = col_idx
        while True:
            result = chr(ord('A') + (n % 26)) + result
            n = n // 26 - 1
            if n < 0:
                break
        return result

    def _cell_ref(self, col_idx, row_num):
        return self._col_letter(col_idx) + str(row_num)

    def _escape(self, text):
        s = str(text) if text is not None else ''
        s = s.replace('&', '&amp;')
        s = s.replace('<', '&lt;')
        s = s.replace('>', '&gt;')
        s = s.replace('"', '&quot;')
        return s

    def _build_worksheet(self, rows):
        rows_xml = []
        for row_num, row_data in enumerate(rows, start=1):
            cells = []
            for col_idx, value in enumerate(row_data):
                ref = self._cell_ref(col_idx, row_num)
                if value is None:
                    cells.append('<c r="{0}" t="inlineStr"><is><t></t></is></c>'.format(ref))
                elif isinstance(value, bool):
                    cells.append('<c r="{0}" t="inlineStr"><is><t>{1}</t></is></c>'.format(
                        ref, self._escape(str(value))))
                elif isinstance(value, (int, float)):
                    if value != value:
                        cells.append('<c r="{0}" t="inlineStr"><is><t>NaN</t></is></c>'.format(ref))
                    else:
                        cells.append('<c r="{0}"><v>{1}</v></c>'.format(ref, value))
                else:
                    cells.append('<c r="{0}" t="inlineStr"><is><t>{1}</t></is></c>'.format(
                        ref, self._escape(str(value))))
            if cells:
                rows_xml.append('<row r="{0}">{1}</row>'.format(row_num, ''.join(cells)))
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetData>' + ''.join(rows_xml) + '</sheetData>'
            '</worksheet>'
        )

    def _write_entry(self, archive, path, content):
        entry = archive.CreateEntry(path)
        entry_stream = entry.Open()
        try:
            data = System.Text.Encoding.UTF8.GetBytes(content)
            entry_stream.Write(data, 0, data.Length)
        finally:
            entry_stream.Close()

    def save(self, filepath, sheets):
        num_sheets = len(sheets)

        ws_overrides = ''.join(
            '<Override PartName="/xl/worksheets/sheet{0}.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            .format(i + 1)
            for i in range(num_sheets)
        )
        content_types_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            + ws_overrides +
            '<Override PartName="/xl/styles.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '</Types>'
        )

        root_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"'
            ' Target="xl/workbook.xml"/>'
            '</Relationships>'
        )

        sheet_tags = ''.join(
            '<sheet name="{0}" sheetId="{1}" r:id="rId{1}"/>'
            .format(self._escape(name), i + 1)
            for i, (name, _) in enumerate(sheets)
        )
        workbook_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
            ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets>' + sheet_tags + '</sheets>'
            '</workbook>'
        )

        ws_rels = ''.join(
            '<Relationship Id="rId{0}"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"'
            ' Target="worksheets/sheet{0}.xml"/>'
            .format(i + 1)
            for i in range(num_sheets)
        )
        styles_rel_id = num_sheets + 1
        wb_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + ws_rels +
            '<Relationship Id="rId{0}"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"'
            ' Target="styles.xml"/>'
            .format(styles_rel_id) +
            '</Relationships>'
        )

        styles_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="1"><font><name val="Calibri"/><sz val="11"/></font></fonts>'
            '<fills count="2">'
            '<fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill>'
            '</fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
            '</styleSheet>'
        )

        file_stream = System.IO.File.Create(filepath)
        try:
            archive = System.IO.Compression.ZipArchive(
                file_stream, System.IO.Compression.ZipArchiveMode.Create, True)
            try:
                self._write_entry(archive, '[Content_Types].xml', content_types_xml)
                self._write_entry(archive, '_rels/.rels', root_rels_xml)
                self._write_entry(archive, 'xl/workbook.xml', workbook_xml)
                self._write_entry(archive, 'xl/_rels/workbook.xml.rels', wb_rels_xml)
                self._write_entry(archive, 'xl/styles.xml', styles_xml)
                for i, (name, rows) in enumerate(sheets):
                    ws_xml = self._build_worksheet(rows)
                    self._write_entry(archive, 'xl/worksheets/sheet{0}.xml'.format(i + 1), ws_xml)
            finally:
                archive.Dispose()
        finally:
            file_stream.Close()


class PerformanceWindowDialog(Form):
    """Simple dialog for configuring the live chart window width."""

    def __init__(self, current_width_seconds):
        Form.__init__(self)
        self.Text = 'Live Window Width'
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.StartPosition = FormStartPosition.CenterParent
        self.ClientSize = Size(320, 120)
        self._value = float(current_width_seconds)

        label = Label()
        label.Text = 'Live chart window width (seconds):'
        label.AutoSize = True
        label.Location = Point(12, 14)
        self.Controls.Add(label)

        self.txt_width = TextBox()
        self.txt_width.Text = '{0:.1f}'.format(float(current_width_seconds))
        self.txt_width.Location = Point(12, 40)
        self.txt_width.Width = 120
        self.Controls.Add(self.txt_width)

        btn_ok = Button()
        btn_ok.Text = 'OK'
        btn_ok.Location = Point(132, 76)
        btn_ok.DialogResult = DialogResult.OK
        self.Controls.Add(btn_ok)
        self.AcceptButton = btn_ok

        btn_cancel = Button()
        btn_cancel.Text = 'Cancel'
        btn_cancel.Location = Point(220, 76)
        btn_cancel.DialogResult = DialogResult.Cancel
        self.Controls.Add(btn_cancel)
        self.CancelButton = btn_cancel

    def get_value(self):
        try:
            value = float(self.txt_width.Text.strip())
            if value <= 0:
                raise ValueError()
            return value
        except Exception:
            return None


class LiveFrameCaptureHandler(object):
    """Collects frame timestamps from SharpCap live capture."""

    def __init__(self, on_sample):
        self.capturing = False
        self.frame_count = 0
        self.exposure_ms = 0.0
        self._last_mid_timestamp = None
        self._on_sample = on_sample

    def framehandler(self, sender, args):
        if not self.capturing:
            return
        try:
            net_timestamp = args.Frame.Info.EndTimeStamp
            timestamp_end = datetime(
                net_timestamp.Year,
                net_timestamp.Month,
                net_timestamp.Day,
                net_timestamp.Hour,
                net_timestamp.Minute,
                net_timestamp.Second,
                net_timestamp.Millisecond * 1000,
            )
            timestamp = timestamp_end - timedelta(milliseconds=float(self.exposure_ms) / 2.0)
            self.frame_count += 1
            if self._on_sample is not None:
                self._on_sample(timestamp)
        except Exception as ex:
            print('Performance frame handler error: {0}'.format(str(ex)))


class PCPerformanceTestingForm(Form):
    """Live PC performance testing dialog."""

    def __init__(self, sharpcap=None, config=None, theme_manager=None):
        Form.__init__(self)
        self._sharpcap = sharpcap
        self._config = config
        self._theme_manager = theme_manager
        self._capture_lock = threading.Lock()
        self._capture_handler = LiveFrameCaptureHandler(self._handle_timestamp_sample)
        self._samples = []
        self._perf_samples = []
        self._capture_running = False
        self._stop_requested = False
        self._last_ui_refresh = 0.0
        self._capture_start = None
        self._last_mid_timestamp = None
        self._window_seconds = 10.0
        self._full_window_seconds = 30.0
        self._show_cumulative_delta_line = False
        self._live_y_limit = 10.0
        self._full_y_limit = 10.0
        self._recording_path = None
        self._export_folder = None
        self._run_start_utc = None
        self._summary_text = ''
        self._recording_mode = 'live'
        self._camera_settings_snapshot = {}
        self._camera_summary_text = ''
        self._full_delta_model = None
        self._full_delta_series = None
        self._full_delta_x_axis = None
        self._full_delta_y_axis = None
        self._full_cumulative_series = None
        self._full_cumulative_y_axis = None
        self._full_delta_last_index = -1
        self._full_cumulative_delta_sum = 0.0
        self._full_cumulative_min = 0.0
        self._full_cumulative_max = 0.0
        self._full_perf_model = None
        self._full_perf_x_axis = None
        self._full_perf_series = {}
        self._full_perf_last_index = -1
        self._default_output_folder = self._get_output_folder()
        self.InitializeComponent()
        self._initialize_performance_stats()
        try:
            handle = self.Handle
        except Exception:
            handle = None
        if theme_manager is not None and _THEME_AVAILABLE:
            try:
                apply_theme_to_control(self, theme_manager.get_current_theme())
            except Exception:
                pass
        self._perf_timer = Timer()
        self._perf_timer.Interval = 1000
        self._perf_timer.Tick += self._update_performance_panel
        self._perf_timer.Start()

    def InitializeComponent(self):
        self.Text = 'PC Performance Testing'
        self.ClientSize = Size(1560, 980)
        self.StartPosition = FormStartPosition.CenterScreen
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.MinimizeBox = True
        self.MaximizeBox = True

        self.main_split = SplitContainer()
        self.main_split.Dock = DockStyle.Fill
        self.main_split.Orientation = Orientation.Vertical
        self.Controls.Add(self.main_split)
        self._main_split_panel1_min = 420
        self._main_split_panel2_min = 760
        self._main_split_target_distance = 470
        self._set_splitter_distance_safe(self.main_split, self._main_split_target_distance)
        self.main_split.SizeChanged += self._on_main_split_size_changed

        self.left_panel = Panel()
        self.left_panel.Dock = DockStyle.Fill
        self.left_panel.AutoScroll = True
        self.main_split.Panel1.Controls.Add(self.left_panel)

        self.right_panel = Panel()
        self.right_panel.Dock = DockStyle.Fill
        self.main_split.Panel2.Controls.Add(self.right_panel)

        info_group = GroupBox()
        info_group.Text = 'About PC Performance Testing'
        info_group.Location = Point(12, 10)
        info_group.Size = Size(438, 244)
        info_group.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        self.left_panel.Controls.Add(info_group)

        info_label = Label()
        info_label.AutoSize = False
        info_label.Location = Point(12, 20)
        info_label.Size = Size(416, 214)
        info_label.Text = (
            'PC Performance Testing shows live frame-to-frame\r\n'
            'timestamp stability while SharpCap is acquiring\r\n'
            'video, or analyse an ADV recording.\r\n'
            '\r\n'
            'Use it to see whether the timestamp interval\r\n'
            'stays steady or changes when the PC is under\r\n'
            'load, for example from mouse movement,\r\n'
            'competing USB activity, or other Windows\r\n'
            'processes.\r\n'
            '\r\n'
            'The delta plots show frame interval minus the\r\n'
            'nominal camera exposure.\r\n'
            '\r\n'
            'Disk % is derived from Windows PhysicalDisk\r\n'
            '% Idle Time as (100 - Idle), clamped to\r\n'
            '0-100%.'
        )
        info_group.Controls.Add(info_label)

        self.lbl_duration = Label()
        self.lbl_duration.Text = 'Capture Duration (seconds):'
        self.lbl_duration.AutoSize = True
        self.lbl_duration.Location = Point(12, 268)
        self.left_panel.Controls.Add(self.lbl_duration)

        self.txt_duration = TextBox()
        self.txt_duration.Text = '30'
        self.txt_duration.Location = Point(190, 264)
        self.txt_duration.Width = 60
        self.left_panel.Controls.Add(self.txt_duration)

        self.lbl_width = Label()
        self.lbl_width.Text = 'Live Window (seconds):'
        self.lbl_width.AutoSize = True
        self.lbl_width.Location = Point(270, 268)
        self.left_panel.Controls.Add(self.lbl_width)

        self.lbl_width_value = Label()
        self.lbl_width_value.Text = '10.0'
        self.lbl_width_value.AutoSize = True
        self.lbl_width_value.Location = Point(418, 268)
        self.lbl_width_value.Anchor = AnchorStyles.Top | AnchorStyles.Right
        self.left_panel.Controls.Add(self.lbl_width_value)

        self.btn_width = Button()
        self.btn_width.Text = 'Configure...'
        self.btn_width.Location = Point(340, 296)
        self.btn_width.Size = Size(110, 28)
        self.btn_width.Anchor = AnchorStyles.Top | AnchorStyles.Right
        self.btn_width.Click += self.configure_window_width_click
        self.left_panel.Controls.Add(self.btn_width)

        self.lbl_test_desc = Label()
        self.lbl_test_desc.Text = 'Test Description:'
        self.lbl_test_desc.AutoSize = True
        self.lbl_test_desc.Location = Point(12, 340)
        self.left_panel.Controls.Add(self.lbl_test_desc)

        self.txt_test_desc = TextBox()
        self.txt_test_desc.Location = Point(120, 336)
        self.txt_test_desc.Size = Size(330, 24)
        self.txt_test_desc.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        self.left_panel.Controls.Add(self.txt_test_desc)

        self.lbl_comment = Label()
        self.lbl_comment.Text = 'Comment:'
        self.lbl_comment.AutoSize = True
        self.lbl_comment.Location = Point(12, 372)
        self.left_panel.Controls.Add(self.lbl_comment)

        self.txt_comment = TextBox()
        self.txt_comment.Location = Point(120, 368)
        self.txt_comment.Size = Size(330, 24)
        self.txt_comment.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        self.left_panel.Controls.Add(self.txt_comment)

        self.lbl_recording_mode = Label()
        self.lbl_recording_mode.Text = 'Recording Mode:'
        self.lbl_recording_mode.AutoSize = True
        self.lbl_recording_mode.Location = Point(12, 404)
        self.left_panel.Controls.Add(self.lbl_recording_mode)

        self.panel_recording_mode = Panel()
        self.panel_recording_mode.Location = Point(120, 401)
        self.panel_recording_mode.Size = Size(330, 52)
        self.panel_recording_mode.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        self.left_panel.Controls.Add(self.panel_recording_mode)

        self.radio_record_live = RadioButton()
        self.radio_record_live.Text = 'Live Mode'
        self.radio_record_live.Location = Point(0, 2)
        self.radio_record_live.AutoSize = True
        self.radio_record_live.Checked = True
        self.radio_record_live.CheckedChanged += self._on_recording_mode_changed
        self.panel_recording_mode.Controls.Add(self.radio_record_live)

        self.radio_record_adv = RadioButton()
        self.radio_record_adv.Text = 'Record to ADV File'
        self.radio_record_adv.Location = Point(0, 26)
        self.radio_record_adv.AutoSize = True
        self.radio_record_adv.Enabled = _ADV_AVAILABLE
        self.radio_record_adv.CheckedChanged += self._on_recording_mode_changed
        if not _ADV_AVAILABLE:
            self.radio_record_adv.Text = 'Record to ADV File (unavailable)'
        self.panel_recording_mode.Controls.Add(self.radio_record_adv)

        self.lbl_output = Label()
        self.lbl_output.Text = 'Mode: Live (no file recording)'
        self.lbl_output.AutoSize = False
        self.lbl_output.Location = Point(12, 460)
        self.lbl_output.Size = Size(438, 34)
        self.lbl_output.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        self.lbl_output.ForeColor = Color.DimGray
        self.left_panel.Controls.Add(self.lbl_output)

        self.actions_flow = FlowLayoutPanel()
        self.actions_flow.Location = Point(12, 500)
        self.actions_flow.Size = Size(438, 68)
        self.actions_flow.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right
        self.actions_flow.WrapContents = True
        self.actions_flow.FlowDirection = FlowDirection.LeftToRight
        self.actions_flow.AutoSize = False
        self.left_panel.Controls.Add(self.actions_flow)

        self.btn_start = Button()
        self.btn_start.Text = 'Start Test'
        self.btn_start.Size = Size(100, 30)
        self.btn_start.Margin = Padding(0, 0, 8, 8)
        self.btn_start.Click += self.start_test_click
        self.actions_flow.Controls.Add(self.btn_start)

        self.btn_stop = Button()
        self.btn_stop.Text = 'Stop'
        self.btn_stop.Size = Size(80, 30)
        self.btn_stop.Margin = Padding(0, 0, 8, 8)
        self.btn_stop.Enabled = False
        self.btn_stop.Click += self.stop_test_click
        self.actions_flow.Controls.Add(self.btn_stop)

        self.btn_save = Button()
        self.btn_save.Text = 'Save Results...'
        self.btn_save.Size = Size(120, 30)
        self.btn_save.Margin = Padding(0, 0, 8, 8)
        self.btn_save.Enabled = False
        self.btn_save.Click += self.save_results_click
        self.actions_flow.Controls.Add(self.btn_save)

        self.lbl_status = Label()
        self.lbl_status.Text = 'Ready'
        self.lbl_status.AutoSize = True
        self.lbl_status.Location = Point(12, 574)
        self.lbl_status.Font = Font(self.lbl_status.Font.FontFamily, 9, FontStyle.Bold)
        self.left_panel.Controls.Add(self.lbl_status)

        self.info_split = SplitContainer()
        self.info_split.Location = Point(12, 604)
        self.info_split.Size = Size(438, 312)
        self.info_split.Anchor = AnchorStyles.Top | AnchorStyles.Bottom | AnchorStyles.Left | AnchorStyles.Right
        self.info_split.Orientation = Orientation.Vertical
        self.left_panel.Controls.Add(self.info_split)
        self._info_split_panel1_min = 140
        self._info_split_panel2_min = 140
        self._info_split_target_distance = 220
        self._set_splitter_distance_safe(self.info_split, self._info_split_target_distance)
        self.info_split.SizeChanged += self._on_info_split_size_changed
        self.Shown += self._on_form_shown

        self.text_stats_summary = TextBox()
        self.text_stats_summary.Dock = DockStyle.Fill
        self.text_stats_summary.Multiline = True
        self.text_stats_summary.ReadOnly = True
        self.text_stats_summary.ScrollBars = ScrollBars.Vertical
        self.info_split.Panel1.Controls.Add(self.text_stats_summary)

        self.text_camera_summary = TextBox()
        self.text_camera_summary.Dock = DockStyle.Fill
        self.text_camera_summary.Multiline = True
        self.text_camera_summary.ReadOnly = True
        self.text_camera_summary.ScrollBars = ScrollBars.Vertical
        self.info_split.Panel2.Controls.Add(self.text_camera_summary)

        # Backward-compatible alias used by existing summary setter.
        self.text_summary = self.text_stats_summary

        self.grp_pc_perf = GroupBox()
        self.grp_pc_perf.Text = 'PC Performance'
        self.grp_pc_perf.Dock = DockStyle.Top
        self.grp_pc_perf.Height = 62
        self.right_panel.Controls.Add(self.grp_pc_perf)

        perf_labels = [
            ('cpu', 'CPU: --'),
            ('memory', 'Memory: --'),
            ('disk', 'Disk: --'),
            ('network', 'Network: --'),
        ]
        self._perf_value_labels = {}
        perf_flow = FlowLayoutPanel()
        perf_flow.Dock = DockStyle.Fill
        perf_flow.WrapContents = True
        perf_flow.AutoSize = False
        perf_flow.FlowDirection = FlowDirection.LeftToRight
        self.grp_pc_perf.Controls.Add(perf_flow)
        for key, text in perf_labels:
            label = Label()
            label.Text = text
            label.AutoSize = True
            label.Margin = Padding(14, 22, 14, 0)
            label.Font = Font(label.Font.FontFamily, 9, FontStyle.Bold)
            perf_flow.Controls.Add(label)
            self._perf_value_labels[key] = label

        charts_table = TableLayoutPanel()
        charts_table.Dock = DockStyle.Fill
        charts_table.ColumnCount = 1
        charts_table.RowCount = 3
        charts_table.Padding = Padding(6)
        charts_table.RowStyles.Add(RowStyle(SizeType.Percent, 46.0))
        charts_table.RowStyles.Add(RowStyle(SizeType.Percent, 27.0))
        charts_table.RowStyles.Add(RowStyle(SizeType.Percent, 27.0))
        self.right_panel.Controls.Add(charts_table)

        self.plot_live = OxyPlot.WindowsForms.PlotView()
        self.plot_live.Dock = DockStyle.Fill
        charts_table.Controls.Add(self.plot_live, 0, 0)

        self.plot_full = OxyPlot.WindowsForms.PlotView()
        self.plot_full.Dock = DockStyle.Fill
        charts_table.Controls.Add(self.plot_full, 0, 1)

        perf_chart_panel = TableLayoutPanel()
        perf_chart_panel.Dock = DockStyle.Fill
        perf_chart_panel.ColumnCount = 1
        perf_chart_panel.RowCount = 2
        perf_chart_panel.Margin = Padding(0)
        perf_chart_panel.Padding = Padding(0)
        perf_chart_panel.RowStyles.Add(RowStyle(SizeType.AutoSize))
        perf_chart_panel.RowStyles.Add(RowStyle(SizeType.Percent, 100.0))
        charts_table.Controls.Add(perf_chart_panel, 0, 2)

        perf_chart_legend = FlowLayoutPanel()
        perf_chart_legend.AutoSize = True
        perf_chart_legend.WrapContents = True
        perf_chart_legend.FlowDirection = FlowDirection.LeftToRight
        perf_chart_legend.Dock = DockStyle.Top
        perf_chart_legend.Margin = Padding(6, 0, 6, 2)
        perf_chart_legend.Padding = Padding(0)
        perf_chart_panel.Controls.Add(perf_chart_legend, 0, 0)

        for color, text in [
            (Color.IndianRed, 'CPU %'),
            (Color.DodgerBlue, 'Memory %'),
            (Color.DarkOrange, 'Disk %'),
            (Color.SeaGreen, 'Network %'),
        ]:
            legend_item = FlowLayoutPanel()
            legend_item.AutoSize = True
            legend_item.WrapContents = False
            legend_item.FlowDirection = FlowDirection.LeftToRight
            legend_item.Margin = Padding(0, 0, 14, 0)
            legend_item.Padding = Padding(0)

            line_swatch = Panel()
            line_swatch.BackColor = color
            line_swatch.Width = 18
            line_swatch.Height = 3
            line_swatch.Margin = Padding(0, 8, 5, 0)
            legend_item.Controls.Add(line_swatch)

            label = Label()
            label.Text = text
            label.AutoSize = True
            label.ForeColor = color
            label.Font = Font(label.Font.FontFamily, 8.5, FontStyle.Bold)
            label.Margin = Padding(0, 0, 0, 0)
            legend_item.Controls.Add(label)

            perf_chart_legend.Controls.Add(legend_item)

        self.plot_perf_full = OxyPlot.WindowsForms.PlotView()
        self.plot_perf_full.Dock = DockStyle.Fill
        perf_chart_panel.Controls.Add(self.plot_perf_full, 0, 1)

        self._chart_tooltip = ToolTip()
        self._chart_tooltip.SetToolTip(
            self.plot_full,
            'Full duration timestamp delta versus nominal exposure. '\
            'Cumulative delta is still calculated and exported, but the cumulative line is hidden.'
        )

        self.FormClosing += self._on_form_closing

        self._update_recording_mode_ui()
        self._update_summary_text('No test data yet.')
        self._refresh_all_plots()

    def _initialize_performance_stats(self):
        self._perf_cpu_counter = None
        self._perf_disk_counter = None
        self._perf_disk_idle_counter = None
        self._perf_memory_counter = None
        self._perf_network_counter = None
        self._perf_network_speed_bps = None
        self._perf_total_memory_mb = None

        try:
            self._perf_cpu_counter = PerformanceCounter('Processor', '% Processor Time', '_Total', True)
            self._perf_cpu_counter.NextValue()
        except Exception:
            self._perf_cpu_counter = None

        try:
            self._perf_disk_counter = PerformanceCounter('PhysicalDisk', '% Disk Time', '_Total', True)
            self._perf_disk_counter.NextValue()
        except Exception:
            self._perf_disk_counter = None

        try:
            self._perf_disk_idle_counter = PerformanceCounter('PhysicalDisk', '% Idle Time', '_Total', True)
            self._perf_disk_idle_counter.NextValue()
        except Exception:
            self._perf_disk_idle_counter = None

        try:
            self._perf_memory_counter = PerformanceCounter('Memory', 'Available MBytes', True)
        except Exception:
            self._perf_memory_counter = None

        if _SYSTEM_MANAGEMENT_AVAILABLE:
            try:
                searcher = System.Management.ManagementObjectSearcher(
                    'SELECT TotalVisibleMemorySize FROM Win32_OperatingSystem')
                for item in searcher.Get():
                    self._perf_total_memory_mb = float(item['TotalVisibleMemorySize']) / 1024.0
                    break
            except Exception:
                self._perf_total_memory_mb = None

        self._perf_network_counter, self._perf_network_speed_bps = self._find_network_counter()

    def _normalize_perf_name(self, text):
        if not text:
            return ''
        return ''.join(ch.lower() for ch in str(text) if ch.isalnum())

    def _find_network_counter(self):
        try:
            category = System.Diagnostics.PerformanceCounterCategory('Network Interface')
            instances = list(category.GetInstanceNames())
        except Exception:
            instances = []

        try:
            adapters = list(System.Net.NetworkInformation.NetworkInterface.GetAllNetworkInterfaces())
        except Exception:
            adapters = []

        for adapter in adapters:
            try:
                if adapter.OperationalStatus != System.Net.NetworkInformation.OperationalStatus.Up:
                    continue
                if adapter.NetworkInterfaceType in (
                    System.Net.NetworkInformation.NetworkInterfaceType.Loopback,
                    System.Net.NetworkInformation.NetworkInterfaceType.Tunnel,
                ):
                    continue
                if adapter.Speed <= 0:
                    continue

                candidate_names = [adapter.Name, adapter.Description]
                for candidate in candidate_names:
                    normalized_candidate = self._normalize_perf_name(candidate)
                    if not normalized_candidate:
                        continue
                    for instance_name in instances:
                        normalized_instance = self._normalize_perf_name(instance_name)
                        if not normalized_instance:
                            continue
                        if normalized_candidate == normalized_instance or normalized_candidate in normalized_instance or normalized_instance in normalized_candidate:
                            try:
                                counter = PerformanceCounter('Network Interface', 'Bytes Total/sec', instance_name, True)
                                counter.NextValue()
                                return counter, float(adapter.Speed)
                            except Exception:
                                pass
            except Exception:
                continue
        return None, None

    def _format_stat_value(self, value):
        if value is None:
            return 'N/A'
        try:
            return '{0:.1f}%'.format(float(value))
        except Exception:
            return 'N/A'

    def _clamp_percent(self, value):
        if value is None:
            return None
        try:
            numeric = float(value)
            if numeric < 0.0:
                return 0.0
            if numeric > 100.0:
                return 100.0
            return numeric
        except Exception:
            return None

    def _update_performance_panel(self, sender=None, e=None):
        cpu_val = None
        mem_val = None
        disk_val = None
        net_val = None

        try:
            if self._perf_cpu_counter is not None:
                cpu_val = float(self._perf_cpu_counter.NextValue())
        except Exception:
            cpu_val = None

        try:
            if self._perf_memory_counter is not None and self._perf_total_memory_mb and self._perf_total_memory_mb > 0:
                available_mb = float(self._perf_memory_counter.NextValue())
                used_mb = max(0.0, self._perf_total_memory_mb - available_mb)
                mem_val = (used_mb / self._perf_total_memory_mb) * 100.0
        except Exception:
            mem_val = None

        try:
            if self._perf_disk_idle_counter is not None:
                idle_val = float(self._perf_disk_idle_counter.NextValue())
                disk_val = self._clamp_percent(100.0 - idle_val)
            elif self._perf_disk_counter is not None:
                # % Disk Time can exceed 100 in some configurations; clamp for UI/plots.
                disk_val = self._clamp_percent(float(self._perf_disk_counter.NextValue()))
        except Exception:
            disk_val = None

        try:
            if self._perf_network_counter is not None and self._perf_network_speed_bps and self._perf_network_speed_bps > 0:
                bytes_per_sec = float(self._perf_network_counter.NextValue())
                net_val = (bytes_per_sec * 8.0 / self._perf_network_speed_bps) * 100.0
        except Exception:
            net_val = None

        try:
            self._perf_value_labels['cpu'].Text = 'CPU: {0}'.format(self._format_stat_value(cpu_val))
            self._perf_value_labels['memory'].Text = 'Memory: {0}'.format(self._format_stat_value(mem_val))
            self._perf_value_labels['disk'].Text = 'Disk: {0}'.format(self._format_stat_value(disk_val))
            self._perf_value_labels['network'].Text = 'Network: {0}'.format(self._format_stat_value(net_val))
        except Exception:
            pass

        if self._capture_running and self._run_start_utc is not None:
            elapsed_s = max(0.0, (datetime.utcnow() - self._run_start_utc).total_seconds())
            with self._capture_lock:
                self._perf_samples.append({
                    'elapsed_s': elapsed_s,
                    'cpu': cpu_val,
                    'memory': mem_val,
                    'disk': disk_val,
                    'network': net_val,
                })

    def SafeInvoke(self, action):
        try:
            if self.IsDisposed:
                return
            if self.InvokeRequired:
                self.BeginInvoke(System.Action(action))
            else:
                action()
        except Exception:
            try:
                action()
            except Exception:
                pass

    def _get_output_folder(self):
        if self._config is not None:
            try:
                folder = os.path.join(self._config.get_data_root(), 'pc-performance-testing')
                if not os.path.exists(folder):
                    os.makedirs(folder)
                return folder
            except Exception:
                pass
        folder = os.path.join(os.getcwd(), 'pc-performance-testing')
        if not os.path.exists(folder):
            os.makedirs(folder)
        return folder

    def _set_splitter_distance_safe(self, split_container, desired_distance):
        """Clamp splitter distance to a valid range for the current control size."""
        try:
            total_width = int(split_container.ClientSize.Width)
            splitter_width = int(split_container.SplitterWidth)
            min_distance = int(split_container.Panel1MinSize)
            max_distance = total_width - int(split_container.Panel2MinSize) - splitter_width
            if max_distance < min_distance:
                # If the control is temporarily too small, fall back to the center.
                max_distance = max(0, total_width - splitter_width)
                min_distance = 0

            clamped = max(min_distance, min(int(desired_distance), max_distance))
            split_container.SplitterDistance = clamped
        except Exception:
            # Ignore transient layout timing issues; resize handlers will retry.
            pass

    def _apply_split_constraints_safe(self, split_container, panel1_min, panel2_min, target_distance):
        """Apply min panel sizes only when current width can support them."""
        try:
            total_width = int(split_container.ClientSize.Width)
            splitter_width = int(split_container.SplitterWidth)
            required = int(panel1_min) + int(panel2_min) + splitter_width
            if total_width >= required:
                if split_container.Panel1MinSize != int(panel1_min):
                    split_container.Panel1MinSize = int(panel1_min)
                if split_container.Panel2MinSize != int(panel2_min):
                    split_container.Panel2MinSize = int(panel2_min)
            else:
                # Keep mins relaxed until container is wide enough.
                if split_container.Panel1MinSize != 0:
                    split_container.Panel1MinSize = 0
                if split_container.Panel2MinSize != 0:
                    split_container.Panel2MinSize = 0
        except Exception:
            # Ignore transient layout timing issues; resize handlers will retry.
            pass

        self._set_splitter_distance_safe(split_container, target_distance)

    def _on_form_shown(self, sender, e):
        self._on_main_split_size_changed(None, None)
        self._on_info_split_size_changed(None, None)

    def _on_main_split_size_changed(self, sender, e):
        self._apply_split_constraints_safe(
            self.main_split,
            self._main_split_panel1_min,
            self._main_split_panel2_min,
            self._main_split_target_distance,
        )

    def _on_info_split_size_changed(self, sender, e):
        self._apply_split_constraints_safe(
            self.info_split,
            self._info_split_panel1_min,
            self._info_split_panel2_min,
            self._info_split_target_distance,
        )

    def _get_camera_settings(self, camera):
        """Collect camera settings matching the Line Delay Calibration details block."""
        settings = {}

        def try_get(key, func):
            try:
                val = func()
                settings[key] = val if val is not None else 'N/A'
            except Exception:
                settings[key] = 'N/A'

        try_get('Camera', lambda: str(camera.DeviceName))

        try:
            roi = camera.ROI
            settings['Pan (ROI X)'] = int(roi.X)
            settings['Tilt (ROI Y)'] = int(roi.Y)
            settings['Frame Width (px)'] = int(roi.Width)
            settings['Frame Height (px)'] = int(roi.Height)
        except Exception:
            for key in ('Pan (ROI X)', 'Tilt (ROI Y)', 'Frame Width (px)', 'Frame Height (px)'):
                settings[key] = 'N/A'

        try_get('Exposure (ms)', lambda: round(float(camera.Controls.Exposure.ExposureMs), 6))

        try:
            ctrl = camera.Controls.FindByName('Gain')
            settings['Gain'] = ctrl.Value if ctrl else 'N/A'
        except Exception:
            settings['Gain'] = 'N/A'

        try:
            ctrl = camera.Controls.FindByName('Binning')
            settings['Binning'] = ctrl.Value if ctrl else 'N/A'
        except Exception:
            settings['Binning'] = 'N/A'

        for name in ('ColourSpace', 'ColorSpace', 'Colour Space', 'Color Space'):
            try:
                ctrl = camera.Controls.FindByName(name)
                if ctrl is not None:
                    settings['Colour Space'] = ctrl.Value
                    break
            except Exception:
                pass
        if 'Colour Space' not in settings:
            settings['Colour Space'] = 'N/A'

        for name in ('OutputFormat', 'FileFormat', 'Output Format', 'File Format'):
            try:
                ctrl = camera.Controls.FindByName(name)
                if ctrl is not None:
                    settings['File Format'] = ctrl.Value
                    break
            except Exception:
                pass
        if 'File Format' not in settings:
            settings['File Format'] = 'N/A'

        for name in ('USBBandwidth', 'USB Bandwidth', 'USBTraffic', 'USB Traffic', 'USB Speed',
                     'USBSpeed', 'USBFS'):
            try:
                ctrl = camera.Controls.FindByName(name)
                if ctrl is not None:
                    settings['USB Bandwidth'] = ctrl.Value
                    break
            except Exception:
                pass
        if 'USB Bandwidth' not in settings:
            settings['USB Bandwidth'] = 'N/A'

        return settings

    def _build_camera_summary_text(self):
        lines = []
        lines.append('Camera & Recording Settings')
        lines.append('')
        if self._camera_settings_snapshot:
            for key in (
                'Camera',
                'Pan (ROI X)',
                'Tilt (ROI Y)',
                'Frame Width (px)',
                'Frame Height (px)',
                'Exposure (ms)',
                'Gain',
                'Binning',
                'Colour Space',
                'File Format',
                'USB Bandwidth',
            ):
                value = self._camera_settings_snapshot.get(key, 'N/A')
                lines.append('{0}: {1}'.format(key, value))
        else:
            lines.append('Camera: N/A')

        lines.append('')
        lines.append('Recording Settings')
        mode_text = 'Record to ADV File' if self._recording_mode == 'adv' else 'Live Mode'
        lines.append('Recording Mode: {0}'.format(mode_text))
        lines.append('Record File: {0}'.format(self._recording_path if self._recording_path else 'N/A'))
        if self._recording_mode == 'adv' and self._samples:
            try:
                lines.append('Capture Duration (s): {0:.3f}'.format(float(self._full_window_seconds)))
            except Exception:
                lines.append('Capture Duration (s): {0}'.format(self.txt_duration.Text.strip()))
        else:
            lines.append('Capture Duration (s): {0}'.format(self.txt_duration.Text.strip()))
        lines.append('Live Window (s): {0:.1f}'.format(self._window_seconds))
        lines.append('Test Description: {0}'.format(self.txt_test_desc.Text.strip() if self.txt_test_desc.Text.strip() else ''))
        lines.append('Comment: {0}'.format(self.txt_comment.Text.strip() if self.txt_comment.Text.strip() else ''))
        return '\r\n'.join(lines)

    def _update_camera_summary_text(self):
        self._camera_summary_text = self._build_camera_summary_text()
        self.text_camera_summary.Text = self._camera_summary_text

    def _get_recording_mode(self):
        if hasattr(self, 'radio_record_adv') and self.radio_record_adv.Checked:
            return 'adv'
        return 'live'

    def _update_recording_mode_ui(self):
        mode = self._get_recording_mode()
        if mode == 'adv':
            self.lbl_output.Text = 'Manually record an ADV file, then load it for analysis.'
            self.btn_start.Text = 'Load ADV File'
            if not self._capture_running:
                self.btn_stop.Enabled = False
        else:
            self.lbl_output.Text = 'Mode: Live (no file recording)'
            self.btn_start.Text = 'Start Test'
        self._update_camera_summary_text()

    def _on_recording_mode_changed(self, sender, e):
        self._update_recording_mode_ui()

    def _load_samples_from_adv(self, adv_file_path):
        if not _ADV_AVAILABLE or adv_helper is None:
            raise Exception('ADV support is unavailable (adv_helper/AdvLib not loaded).')
        if not adv_file_path or not os.path.exists(adv_file_path):
            raise Exception('ADV recording file was not found: {0}'.format(adv_file_path if adv_file_path else 'N/A'))

        adv_file = None
        try:
            folder = os.path.dirname(adv_file_path)
            name = os.path.basename(adv_file_path)
            adv_file = adv_helper.open_adv(folder, name, verbose=False)
            frame_count = int(adv_file.MainSteamInfo.FrameCount)
            if frame_count <= 0:
                raise Exception('Recorded ADV file has no frames.')

            exposure_ms = adv_helper.get_frame_exposure_ms(adv_file, 0)
            if exposure_ms is not None:
                try:
                    self._capture_handler.exposure_ms = float(exposure_ms)
                except Exception:
                    pass

            timestamps = []
            for frame_no in range(frame_count):
                ts = adv_helper.get_frame_info_timestamp(adv_file, frame_no)
                if ts is not None:
                    timestamps.append(ts)
                if frame_no > 0 and (frame_no % 200) == 0:
                    self.SafeInvoke(lambda n=frame_no, t=frame_count: self._set_status('Processing ADV... ({0}/{1})'.format(n, t), Color.DarkBlue))

            if len(timestamps) < 2:
                raise Exception('Not enough valid timestamps were read from the ADV file.')

            start_ts = timestamps[0]
            samples = []
            last_ts = None
            for idx, ts in enumerate(timestamps):
                interval_ms = None
                delta_ms = None
                if last_ts is not None:
                    interval_ms = (ts - last_ts).total_seconds() * 1000.0
                    delta_ms = interval_ms - float(self._capture_handler.exposure_ms)

                samples.append({
                    'frame_no': idx + 1,
                    'timestamp': ts,
                    'elapsed_s': (ts - start_ts).total_seconds(),
                    'interval_ms': interval_ms,
                    'delta_ms': delta_ms,
                })
                last_ts = ts

            with self._capture_lock:
                self._samples = samples
                self._capture_start = start_ts
                self._last_mid_timestamp = last_ts
                try:
                    self._full_window_seconds = max(1.0, float(samples[-1]['elapsed_s']))
                except Exception:
                    pass

        finally:
            try:
                if adv_file is not None:
                    adv_file.Close()
            except Exception:
                pass

    def configure_window_width_click(self, sender, e):
        dlg = PerformanceWindowDialog(self._window_seconds)
        if dlg.ShowDialog(self) == DialogResult.OK:
            value = dlg.get_value()
            if value is None:
                MessageBox.Show('Enter a positive numeric window width.', 'Invalid Input', MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            self._window_seconds = value
            self.lbl_width_value.Text = '{0:.1f}'.format(value)
            self._refresh_all_plots()

    def start_test_click(self, sender, e):
        if self._capture_running:
            return

        mode = self._get_recording_mode()
        if mode == 'adv' and not _ADV_AVAILABLE:
            MessageBox.Show('ADV recording mode is unavailable.\n\nCheck AdvLib DLL availability via adv_helper.py.', 'ADV Unavailable', MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return

        duration = None
        if mode != 'adv':
            try:
                duration = float(self.txt_duration.Text.strip())
                if duration <= 0 or duration > 3600:
                    raise ValueError()
            except Exception:
                MessageBox.Show('Capture Duration must be a positive number of seconds.', 'Invalid Input', MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
        else:
            # ADV mode is file-driven, not duration-driven.
            duration = 1.0

        if mode != 'adv' and (self._sharpcap is None or getattr(self._sharpcap, 'SelectedCamera', None) is None):
            MessageBox.Show('No camera is connected.\n\nPlease connect a camera and run SharpCap live preview first.', 'Camera Missing', MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return

        selected_adv = None
        if mode == 'adv':
            dialog = OpenFileDialog()
            dialog.Title = 'Select ADV file for PC Performance analysis'
            dialog.Filter = 'ADV files (*.adv)|*.adv|All files (*.*)|*.*'
            if dialog.ShowDialog(self) != DialogResult.OK:
                self._recording_mode = mode
                self._set_status('Ready', Color.Black)
                self._update_summary_text('ADV file selection cancelled.')
                return
            selected_adv = dialog.FileName

        self._samples = []
        self._perf_samples = []
        self._capture_start = None
        self._last_mid_timestamp = None
        self._live_y_limit = 10.0
        self._full_y_limit = 10.0
        self._full_window_seconds = float(duration)
        self._reset_full_plot_state()
        self._run_start_utc = datetime.utcnow()
        self._recording_path = selected_adv if selected_adv else None
        self._stop_requested = False
        self._capture_running = True
        self._recording_mode = mode

        try:
            if mode == 'adv':
                self._camera_settings_snapshot = {}
            else:
                self._camera_settings_snapshot = self._get_camera_settings(self._sharpcap.SelectedCamera)
        except Exception:
            self._camera_settings_snapshot = {}

        self.btn_start.Enabled = False
        self.btn_stop.Enabled = (mode != 'adv')
        self.btn_save.Enabled = False
        self.radio_record_live.Enabled = False
        self.radio_record_adv.Enabled = False
        self.lbl_status.Text = 'Starting...'
        self.lbl_status.ForeColor = Color.Orange
        self._update_summary_text('Starting capture...')
        self._update_camera_summary_text()
        self.plot_full.Model = self._initialize_full_delta_plot_model()
        self.plot_perf_full.Model = self._initialize_full_perf_plot_model()
        self._sync_full_window_axes()
        self.plot_full.InvalidatePlot(True)
        self.plot_perf_full.InvalidatePlot(True)

        if mode == 'adv':
            self._set_status('Processing ADV file...', Color.DarkBlue)
            self._update_summary_text('Processing ADV file...')
            worker = threading.Thread(target=lambda p=selected_adv: self._run_adv_file_analysis(p))
        else:
            worker = threading.Thread(target=lambda: self._run_capture(duration, self._sharpcap.SelectedCamera))
        worker.daemon = True
        worker.start()

    def _run_adv_file_analysis(self, adv_file_path):
        try:
            self._load_samples_from_adv(adv_file_path)
            self.SafeInvoke(lambda: self._set_status('ADV analysis complete', Color.Green))
        except Exception as ex:
            self.SafeInvoke(lambda: self._set_status('Error', Color.Red))
            self.SafeInvoke(lambda m='Error: {0}'.format(str(ex)): self._update_summary_text(m))
            MessageBox.Show('PC Performance Testing failed:\n\n{0}'.format(str(ex)), 'Performance Test Error', MessageBoxButtons.OK, MessageBoxIcon.Error)
        finally:
            self._capture_running = False
            self.SafeInvoke(lambda: setattr(self.btn_start, 'Enabled', True))
            self.SafeInvoke(lambda: setattr(self.btn_stop, 'Enabled', False))
            self.SafeInvoke(lambda: setattr(self.radio_record_live, 'Enabled', True))
            self.SafeInvoke(lambda: setattr(self.radio_record_adv, 'Enabled', _ADV_AVAILABLE))
            self.SafeInvoke(lambda: setattr(self.btn_save, 'Enabled', len(self._samples) > 1))
            self.SafeInvoke(lambda: self._set_status('Ready', Color.Black if len(self._samples) > 1 else Color.DarkSlateGray))
            self.SafeInvoke(self._refresh_all_plots)

    def stop_test_click(self, sender, e):
        self._stop_requested = True
        self.SafeInvoke(lambda: self._set_status('Stopping...', Color.DarkOrange))

    def _set_status(self, text, color=None):
        self.lbl_status.Text = text
        if color is not None:
            self.lbl_status.ForeColor = color

    def _run_capture(self, duration_seconds, camera):
        try:
            try:
                exposure_ms = float(camera.Controls.Exposure.ExposureMs)
            except Exception:
                exposure_ms = 0.0
            self._capture_handler.exposure_ms = exposure_ms
            self._capture_handler.frame_count = 0

            self._capture_handler.capturing = True
            camera.FrameCaptured += self._capture_handler.framehandler

            # Wait briefly for the first frame so the user knows the stream is live.
            wait_seconds = 0.0
            while not self._stop_requested and self._capture_handler.frame_count == 0 and wait_seconds < 3.0:
                time.sleep(0.1)
                wait_seconds += 0.1

            if self._capture_handler.frame_count == 0:
                raise Exception('No frames captured. Make sure SharpCap live preview is running.')

            start = time.time()
            last_remaining = None
            while not self._stop_requested:
                elapsed = time.time() - start
                remaining = duration_seconds - elapsed
                if remaining <= 0:
                    break
                remaining_int = int(math.ceil(remaining))
                if remaining_int != last_remaining:
                    last_remaining = remaining_int
                    self.SafeInvoke(lambda r=remaining_int: self._set_status('Capturing... ({0}s remaining)'.format(r), Color.DarkBlue))
                time.sleep(0.1)

            self.SafeInvoke(lambda: self._set_status('Finalizing...', Color.DarkBlue))

        except Exception as ex:
            self.SafeInvoke(lambda: self._set_status('Error', Color.Red))
            self.SafeInvoke(lambda m='Error: {0}'.format(str(ex)): self._update_summary_text(m))
            MessageBox.Show('PC Performance Testing failed:\n\n{0}'.format(str(ex)), 'Performance Test Error', MessageBoxButtons.OK, MessageBoxIcon.Error)
        finally:
            try:
                camera.FrameCaptured -= self._capture_handler.framehandler
            except Exception:
                pass
            self._capture_handler.capturing = False
            self._capture_running = False
            self.SafeInvoke(lambda: setattr(self.btn_start, 'Enabled', True))
            self.SafeInvoke(lambda: setattr(self.btn_stop, 'Enabled', False))
            self.SafeInvoke(lambda: setattr(self.radio_record_live, 'Enabled', True))
            self.SafeInvoke(lambda: setattr(self.radio_record_adv, 'Enabled', _ADV_AVAILABLE))
            self.SafeInvoke(lambda: setattr(self.btn_save, 'Enabled', len(self._samples) > 1))
            self.SafeInvoke(lambda: self._set_status('Ready', Color.Black if len(self._samples) > 1 else Color.DarkSlateGray))
            self.SafeInvoke(self._refresh_all_plots)

    def _handle_timestamp_sample(self, timestamp):
        with self._capture_lock:
            if self._capture_start is None:
                self._capture_start = timestamp
                sample = {
                    'frame_no': 1,
                    'timestamp': timestamp,
                    'elapsed_s': 0.0,
                    'interval_ms': None,
                    'delta_ms': None,
                }
                self._samples.append(sample)
            else:
                interval_ms = (timestamp - self._last_mid_timestamp).total_seconds() * 1000.0 if self._last_mid_timestamp is not None else None
                delta_ms = interval_ms - float(self._capture_handler.exposure_ms) if interval_ms is not None else None
                sample = {
                    'frame_no': len(self._samples) + 1,
                    'timestamp': timestamp,
                    'elapsed_s': (timestamp - self._capture_start).total_seconds(),
                    'interval_ms': interval_ms,
                    'delta_ms': delta_ms,
                }
                self._samples.append(sample)
            self._last_mid_timestamp = timestamp

        now = time.time()
        if (now - self._last_ui_refresh) >= 0.5 or len(self._samples) <= 3:
            self._last_ui_refresh = now
            self.SafeInvoke(self._refresh_all_plots)

    def _refresh_all_plots(self):
        with self._capture_lock:
            samples = list(self._samples)
            perf_samples = list(self._perf_samples)
            exposure_ms = float(self._capture_handler.exposure_ms)
            window_seconds = float(self._window_seconds)

        self._sync_full_window_axes()

        valid = [s for s in samples if s.get('delta_ms') is not None]
        if not valid:
            self.plot_live.Model = self._build_empty_plot('Live interval delta (waiting for data)', 'Elapsed seconds', 'Delta from nominal exposure (ms)')
            if self._full_delta_model is None:
                self.plot_full.Model = self._initialize_full_delta_plot_model()
            self._update_summary_text('Waiting for samples...')
        else:
            self.plot_live.Model = self._build_timeseries_plot(valid, exposure_ms, window_seconds, live=True)
            self.plot_full.Model = self._initialize_full_delta_plot_model()
            self._append_full_delta_points(valid)
            self._update_summary_text(self._build_summary_text(valid, exposure_ms))

        if perf_samples:
            self.plot_perf_full.Model = self._initialize_full_perf_plot_model()
            self._append_full_perf_points(perf_samples)
        else:
            self.plot_perf_full.Model = self._initialize_full_perf_plot_model()
            self._clear_full_perf_points()

        self.plot_live.InvalidatePlot(True)
        self.plot_full.InvalidatePlot(True)
        self.plot_perf_full.InvalidatePlot(True)

    def _reset_full_plot_state(self):
        self._full_delta_model = None
        self._full_delta_series = None
        self._full_delta_x_axis = None
        self._full_delta_y_axis = None
        self._full_cumulative_series = None
        self._full_cumulative_y_axis = None
        self._full_delta_last_index = -1
        self._full_cumulative_delta_sum = 0.0
        self._full_cumulative_min = 0.0
        self._full_cumulative_max = 0.0
        self._full_perf_model = None
        self._full_perf_x_axis = None
        self._full_perf_series = {}
        self._full_perf_last_index = -1

    def _initialize_full_delta_plot_model(self):
        if self._full_delta_model is not None:
            return self._full_delta_model

        model = OxyPlot.PlotModel()
        model.Title = 'Full Duration Timestamp Delta'
        model.TitleFontSize = 16
        model.PlotAreaBorderColor = OxyPlot.OxyColors.LightGray
        model.Background = OxyPlot.OxyColors.White

        series = OxyPlot.Series.LineSeries()
        series.Title = 'Delta (ms)'
        series.Color = OxyPlot.OxyColors.DodgerBlue
        series.StrokeThickness = 1.5
        series.TrackerFormatString = 'Delta\nTime: {2:0.###}s\nValue: {4:0.###} ms'
        series.YAxisKey = 'deltaAxis'
        model.Series.Add(series)

        cumulative_series = OxyPlot.Series.LineSeries()
        cumulative_series.Title = 'Cumulative Delta (ms)'
        cumulative_series.Color = OxyPlot.OxyColors.MediumVioletRed
        cumulative_series.StrokeThickness = 2.0
        cumulative_series.TrackerFormatString = (
            'Cumulative Delta\nTime: {2:0.###}s\nValue: {4:0.###} ms\n'
            'Large magnitude may indicate dropped frames or buffer catch-up bursts.'
        )
        cumulative_series.YAxisKey = 'cumulativeAxis'
        if self._show_cumulative_delta_line:
            model.Series.Add(cumulative_series)

        zero_line = OxyPlot.Annotations.LineAnnotation()
        zero_line.Type = OxyPlot.Annotations.LineAnnotationType.Horizontal
        zero_line.Y = 0.0
        zero_line.Color = OxyPlot.OxyColors.Gray
        zero_line.LineStyle = OxyPlot.LineStyle.Dash
        model.Annotations.Add(zero_line)

        x_axis = OxyPlot.Axes.LinearAxis()
        x_axis.Position = OxyPlot.Axes.AxisPosition.Bottom
        x_axis.Title = 'Elapsed Time (seconds)'
        x_axis.Minimum = 0.0
        x_axis.Maximum = max(1.0, float(self._full_window_seconds))
        model.Axes.Add(x_axis)

        y_axis = OxyPlot.Axes.LinearAxis()
        y_axis.Position = OxyPlot.Axes.AxisPosition.Left
        y_axis.Key = 'deltaAxis'
        y_axis.Title = 'Delta from nominal exposure (ms)'
        padding = 0.15 * self._full_y_limit
        y_axis.Minimum = -(self._full_y_limit + padding)
        y_axis.Maximum = self._full_y_limit + padding
        model.Axes.Add(y_axis)

        cumulative_axis = OxyPlot.Axes.LinearAxis()
        cumulative_axis.Position = OxyPlot.Axes.AxisPosition.Right
        cumulative_axis.Key = 'cumulativeAxis'
        cumulative_axis.Title = 'Cumulative Delta (ms)'
        cumulative_axis.Minimum = -1.0
        cumulative_axis.Maximum = 1.0
        if self._show_cumulative_delta_line:
            model.Axes.Add(cumulative_axis)

        self._full_delta_model = model
        self._full_delta_series = series
        self._full_delta_x_axis = x_axis
        self._full_delta_y_axis = y_axis
        self._full_cumulative_series = cumulative_series
        self._full_cumulative_y_axis = cumulative_axis if self._show_cumulative_delta_line else None
        return self._full_delta_model

    def _append_full_delta_points(self, valid_samples):
        model = self._initialize_full_delta_plot_model()
        if self._full_delta_series is None:
            return

        changed = False
        start_idx = self._full_delta_last_index + 1
        if start_idx < 0:
            start_idx = 0

        for idx in range(start_idx, len(valid_samples)):
            sample = valid_samples[idx]
            delta = sample.get('delta_ms')
            if delta is None:
                continue
            self._full_delta_series.Points.Add(OxyPlot.DataPoint(sample['elapsed_s'], delta))
            self._full_cumulative_delta_sum += float(delta)
            if self._full_cumulative_series is not None:
                self._full_cumulative_series.Points.Add(OxyPlot.DataPoint(sample['elapsed_s'], self._full_cumulative_delta_sum))
            if self._full_cumulative_delta_sum < self._full_cumulative_min:
                self._full_cumulative_min = self._full_cumulative_delta_sum
            if self._full_cumulative_delta_sum > self._full_cumulative_max:
                self._full_cumulative_max = self._full_cumulative_delta_sum
            abs_delta = abs(float(delta))
            if abs_delta > self._full_y_limit:
                self._full_y_limit = abs_delta
            self._full_delta_last_index = idx
            changed = True

        if changed and self._full_delta_y_axis is not None:
            padding = 0.15 * self._full_y_limit
            self._full_delta_y_axis.Minimum = -(self._full_y_limit + padding)
            self._full_delta_y_axis.Maximum = self._full_y_limit + padding
            if self._full_cumulative_y_axis is not None:
                span = max(abs(self._full_cumulative_min), abs(self._full_cumulative_max), 1.0)
                cum_padding = 0.15 * span
                self._full_cumulative_y_axis.Minimum = self._full_cumulative_min - cum_padding
                self._full_cumulative_y_axis.Maximum = self._full_cumulative_max + cum_padding

    def _initialize_full_perf_plot_model(self):
        if self._full_perf_model is not None:
            return self._full_perf_model

        model = OxyPlot.PlotModel()
        model.Title = 'PC Load (Full Duration)'
        model.TitleFontSize = 16
        model.PlotAreaBorderColor = OxyPlot.OxyColors.LightGray
        model.Background = OxyPlot.OxyColors.White

        specs = [
            ('cpu', 'CPU %', OxyPlot.OxyColors.IndianRed),
            ('memory', 'Memory %', OxyPlot.OxyColors.DodgerBlue),
            ('disk', 'Disk %', OxyPlot.OxyColors.DarkOrange),
            ('network', 'Network %', OxyPlot.OxyColors.SeaGreen),
        ]
        series_map = {}
        for key, title, color in specs:
            series = OxyPlot.Series.LineSeries()
            series.Title = title
            series.Color = color
            series.StrokeThickness = 2
            model.Series.Add(series)
            series_map[key] = series

        x_axis = OxyPlot.Axes.LinearAxis()
        x_axis.Position = OxyPlot.Axes.AxisPosition.Bottom
        x_axis.Title = 'Elapsed Time (seconds)'
        x_axis.Minimum = 0.0
        x_axis.Maximum = max(1.0, float(self._full_window_seconds))
        model.Axes.Add(x_axis)

        y_axis = OxyPlot.Axes.LinearAxis()
        y_axis.Position = OxyPlot.Axes.AxisPosition.Left
        y_axis.Title = 'Load (%)'
        y_axis.Minimum = 0.0
        y_axis.Maximum = 100.0
        model.Axes.Add(y_axis)

        self._full_perf_model = model
        self._full_perf_x_axis = x_axis
        self._full_perf_series = series_map
        return self._full_perf_model

    def _sync_full_window_axes(self):
        max_x = max(1.0, float(self._full_window_seconds))
        try:
            if self._full_delta_x_axis is not None:
                self._full_delta_x_axis.Minimum = 0.0
                self._full_delta_x_axis.Maximum = max_x
        except Exception:
            pass
        try:
            if self._full_perf_x_axis is not None:
                self._full_perf_x_axis.Minimum = 0.0
                self._full_perf_x_axis.Maximum = max_x
        except Exception:
            pass

    def _append_full_perf_points(self, perf_samples):
        self._initialize_full_perf_plot_model()
        if not self._full_perf_series:
            return

        start_idx = self._full_perf_last_index + 1
        if start_idx < 0:
            start_idx = 0

        for idx in range(start_idx, len(perf_samples)):
            sample = perf_samples[idx]
            elapsed = sample.get('elapsed_s', 0.0)
            for key, series in self._full_perf_series.items():
                value = sample.get(key)
                if value is not None:
                    try:
                        series.Points.Add(OxyPlot.DataPoint(elapsed, float(value)))
                    except Exception:
                        pass
            self._full_perf_last_index = idx

    def _clear_full_perf_points(self):
        self._initialize_full_perf_plot_model()
        for series in self._full_perf_series.values():
            try:
                series.Points.Clear()
            except Exception:
                pass
        self._full_perf_last_index = -1

    def _build_empty_plot(self, title, x_title, y_title):
        model = OxyPlot.PlotModel()
        model.Title = title
        model.TitleFontSize = 16
        model.PlotAreaBorderColor = OxyPlot.OxyColors.LightGray
        model.Background = OxyPlot.OxyColors.White
        x_axis = OxyPlot.Axes.LinearAxis()
        x_axis.Position = OxyPlot.Axes.AxisPosition.Bottom
        x_axis.Title = x_title
        model.Axes.Add(x_axis)
        y_axis = OxyPlot.Axes.LinearAxis()
        y_axis.Position = OxyPlot.Axes.AxisPosition.Left
        y_axis.Title = y_title
        model.Axes.Add(y_axis)
        return model

    def _build_timeseries_plot(self, samples, exposure_ms, window_seconds, live=False):
        model = OxyPlot.PlotModel()
        model.Title = 'Live Timestamp Delta' if live else 'Full Duration Timestamp Delta'
        model.TitleFontSize = 16
        model.PlotAreaBorderColor = OxyPlot.OxyColors.LightGray
        model.Background = OxyPlot.OxyColors.White

        series = OxyPlot.Series.LineSeries()
        series.Color = OxyPlot.OxyColors.DeepSkyBlue if live else OxyPlot.OxyColors.DodgerBlue
        series.StrokeThickness = 1.5
        series.MarkerType = OxyPlot.MarkerType.Circle
        series.MarkerSize = 2

        for sample in samples:
            series.Points.Add(OxyPlot.DataPoint(sample['elapsed_s'], sample['delta_ms']))

        model.Series.Add(series)

        zero_line = OxyPlot.Annotations.LineAnnotation()
        zero_line.Type = OxyPlot.Annotations.LineAnnotationType.Horizontal
        zero_line.Y = 0.0
        zero_line.Color = OxyPlot.OxyColors.Gray
        zero_line.LineStyle = OxyPlot.LineStyle.Dash
        model.Annotations.Add(zero_line)

        x_axis = OxyPlot.Axes.LinearAxis()
        x_axis.Position = OxyPlot.Axes.AxisPosition.Bottom
        x_axis.Title = 'Elapsed Time (seconds)'
        if live:
            end_x = samples[-1]['elapsed_s']
            start_x = end_x - float(window_seconds)
            if start_x < 0:
                start_x = 0.0
            x_axis.Minimum = start_x
            x_axis.Maximum = start_x + float(window_seconds)
        else:
            x_axis.Minimum = 0.0
            x_axis.Maximum = max(samples[-1]['elapsed_s'], float(window_seconds))
        model.Axes.Add(x_axis)

        y_axis = OxyPlot.Axes.LinearAxis()
        y_axis.Position = OxyPlot.Axes.AxisPosition.Left
        y_axis.Title = 'Delta from nominal exposure (ms)'
        deltas = [s['delta_ms'] for s in samples if s.get('delta_ms') is not None]
        if deltas:
            min_delta = min(deltas)
            max_delta = max(deltas)
            limit = max(10.0, abs(min_delta), abs(max_delta))
            if live:
                if limit > self._live_y_limit:
                    self._live_y_limit = limit
                limit = self._live_y_limit
            padding = 0.15 * limit
            y_axis.Minimum = -(limit + padding)
            y_axis.Maximum = limit + padding
        model.Axes.Add(y_axis)
        return model

    def _build_pc_stats_plot(self, perf_samples, window_seconds, live=False):
        model = OxyPlot.PlotModel()
        model.Title = 'Live PC Load Metrics' if live else 'PC Load (Full Duration)'
        model.TitleFontSize = 16
        model.PlotAreaBorderColor = OxyPlot.OxyColors.LightGray
        model.Background = OxyPlot.OxyColors.White

        metric_specs = [
            ('cpu', 'CPU %', OxyPlot.OxyColors.IndianRed),
            ('memory', 'Memory %', OxyPlot.OxyColors.DodgerBlue),
            ('disk', 'Disk %', OxyPlot.OxyColors.DarkOrange),
            ('network', 'Network %', OxyPlot.OxyColors.SeaGreen),
        ]

        max_value = 0.0
        for key, title, color in metric_specs:
            series = OxyPlot.Series.LineSeries()
            series.Title = title
            series.Color = color
            series.StrokeThickness = 2
            for sample in perf_samples:
                val = sample.get(key)
                if val is not None:
                    try:
                        numeric = float(val)
                        series.Points.Add(OxyPlot.DataPoint(sample['elapsed_s'], numeric))
                        if numeric > max_value:
                            max_value = numeric
                    except Exception:
                        pass
            model.Series.Add(series)

        x_axis = OxyPlot.Axes.LinearAxis()
        x_axis.Position = OxyPlot.Axes.AxisPosition.Bottom
        x_axis.Title = 'Elapsed Time (seconds)'
        if live:
            end_x = perf_samples[-1]['elapsed_s']
            start_x = end_x - float(window_seconds)
            if start_x < 0:
                start_x = 0.0
            x_axis.Minimum = start_x
            x_axis.Maximum = start_x + float(window_seconds)
        else:
            x_axis.Minimum = 0.0
            x_axis.Maximum = max(perf_samples[-1]['elapsed_s'], float(window_seconds))
        model.Axes.Add(x_axis)

        y_axis = OxyPlot.Axes.LinearAxis()
        y_axis.Position = OxyPlot.Axes.AxisPosition.Left
        y_axis.Title = 'Load (%)'
        y_axis.Minimum = 0.0
        y_axis.Maximum = max(100.0, max_value + 5.0)
        model.Axes.Add(y_axis)

        return model

    def _configure_legend_compat(self, model, prefer_top_outside=False, fallback_text=None):
        """Enable legend with best-effort compatibility across OxyPlot versions."""
        try:
            model.IsLegendVisible = True
        except Exception:
            pass

        placement_applied = False

        try:
            legend_position_enum = getattr(OxyPlot, 'LegendPosition', None)
            if legend_position_enum is not None:
                if prefer_top_outside and hasattr(legend_position_enum, 'TopCenter'):
                    model.LegendPosition = legend_position_enum.TopCenter
                    placement_applied = True
                elif hasattr(legend_position_enum, 'TopRight'):
                    model.LegendPosition = legend_position_enum.TopRight
        except Exception:
            pass

        try:
            legend_placement_enum = getattr(OxyPlot, 'LegendPlacement', None)
            if legend_placement_enum is not None:
                if prefer_top_outside and hasattr(legend_placement_enum, 'Outside'):
                    model.LegendPlacement = legend_placement_enum.Outside
                    placement_applied = True
                elif hasattr(legend_placement_enum, 'Inside'):
                    model.LegendPlacement = legend_placement_enum.Inside
        except Exception:
            pass

        try:
            legend_orientation_enum = getattr(OxyPlot, 'LegendOrientation', None)
            if prefer_top_outside and legend_orientation_enum is not None and hasattr(legend_orientation_enum, 'Horizontal'):
                model.LegendOrientation = legend_orientation_enum.Horizontal
        except Exception:
            pass

        if prefer_top_outside and fallback_text and not placement_applied:
            try:
                model.Subtitle = fallback_text
                model.SubtitleFontSize = 10
            except Exception:
                pass

    def _build_summary_text(self, samples, exposure_ms):
        deltas = [s['delta_ms'] for s in samples if s.get('delta_ms') is not None]
        if not deltas:
            return 'No delta data available.'
        mean_val = sum(deltas) / float(len(deltas))
        min_val = min(deltas)
        max_val = max(deltas)
        variance = 0.0
        if len(deltas) > 1:
            variance = sum((v - mean_val) ** 2 for v in deltas) / float(len(deltas) - 1)
        std_val = math.sqrt(variance) if variance > 0 else 0.0
        lines = []
        lines.append('Timestamp Statistics')
        lines.append('')
        lines.append('Exposure (ms): {0:.3f}'.format(exposure_ms))
        lines.append('Samples: {0}'.format(len(samples)))
        lines.append('Delta samples: {0}'.format(len(deltas)))
        lines.append('Mean delta (ms): {0:.3f}'.format(mean_val))
        lines.append('Min delta (ms): {0:.3f}'.format(min_val))
        lines.append('Max delta (ms): {0:.3f}'.format(max_val))
        lines.append('Std dev (ms): {0:.3f}'.format(std_val))
        lines.append('Live window (s): {0:.1f}'.format(self._window_seconds))
        mode_text = 'Record to ADV File' if self._recording_mode == 'adv' else 'Live Mode'
        lines.append('Recording mode: {0}'.format(mode_text))
        lines.append('Disk % source: PhysicalDisk % Idle Time (100 - Idle), clamped to 0-100%.')
        if self._recording_path:
            lines.append('Record file: {0}'.format(self._recording_path))
        if self.txt_test_desc.Text.strip():
            lines.append('Description: {0}'.format(self.txt_test_desc.Text.strip()))
        if self.txt_comment.Text.strip():
            lines.append('Comment: {0}'.format(self.txt_comment.Text.strip()))
        return '\r\n'.join(lines)

    def _update_summary_text(self, text):
        self._summary_text = text
        self.text_summary.Text = text
        self._update_camera_summary_text()

    def save_results_click(self, sender, e):
        if len(self._samples) < 2:
            MessageBox.Show('No capture data is available to save.', 'No Data', MessageBoxButtons.OK, MessageBoxIcon.Information)
            return

        dialog = SaveFileDialog()
        dialog.Title = 'Save PC Performance Test Results'
        dialog.Filter = 'Excel Workbook (*.xlsx)|*.xlsx|All files (*.*)|*.*'
        default_name = 'pc_performance_test_{0}.xlsx'.format(datetime.utcnow().strftime('%Y%m%d_%H%M%S'))
        dialog.InitialDirectory = self._default_output_folder
        dialog.FileName = default_name

        if dialog.ShowDialog(self) != DialogResult.OK:
            return

        output_path = dialog.FileName
        try:
            self._save_results(output_path)
            MessageBox.Show('Saved results to:\n\n{0}'.format(output_path), 'Saved', MessageBoxButtons.OK, MessageBoxIcon.Information)
        except Exception as ex:
            MessageBox.Show('Could not save results:\n\n{0}'.format(str(ex)), 'Save Error', MessageBoxButtons.OK, MessageBoxIcon.Error)

    def _save_results(self, output_path):
        folder = os.path.dirname(output_path)
        base = os.path.splitext(os.path.basename(output_path))[0]
        live_png = os.path.join(folder, base + '_live.png')
        full_png = os.path.join(folder, base + '_full.png')
        perf_full_png = os.path.join(folder, base + '_pc_full.png')

        self._save_plot_png(self.plot_live, live_png)
        self._save_plot_png(self.plot_full, full_png)
        self._save_plot_png(self.plot_perf_full, perf_full_png)

        with self._capture_lock:
            samples = list(self._samples)
            perf_samples = list(self._perf_samples)
            exposure_ms = float(self._capture_handler.exposure_ms)
            run_start = self._run_start_utc

        mode_text = 'Record to ADV File' if self._recording_mode == 'adv' else 'Live Mode'

        details_rows = [
            ['PC Performance Testing'],
            [],
            ['Run Started (UTC)', run_start.strftime('%Y-%m-%d %H:%M:%S') if run_start else ''],
            ['Run Saved (UTC)', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')],
            ['Capture Duration (s)', self.txt_duration.Text.strip()],
            ['Live Window Width (s)', '{0:.1f}'.format(self._window_seconds)],
            ['Recording Mode', mode_text],
            ['Record File', self._recording_path or ''],
            ['Exposure (ms)', '{0:.3f}'.format(exposure_ms)],
            ['Frames Captured', len(samples)],
            ['Test Description', self.txt_test_desc.Text.strip()],
            ['Comment', self.txt_comment.Text.strip()],
            [],
            ['CAMERA SETTINGS'],
            ['Setting', 'Value'],
        ]

        for key in (
            'Camera',
            'Pan (ROI X)',
            'Tilt (ROI Y)',
            'Frame Width (px)',
            'Frame Height (px)',
            'Exposure (ms)',
            'Gain',
            'Binning',
            'Colour Space',
            'File Format',
            'USB Bandwidth',
        ):
            details_rows.append([key, self._camera_settings_snapshot.get(key, 'N/A')])

        details_rows.extend([
            [],
            ['RECORDING SETTINGS'],
            ['Setting', 'Value'],
            ['Recording Mode', mode_text],
            ['Record File', self._recording_path or ''],
            ['Capture Duration (s)', self.txt_duration.Text.strip()],
            ['Live Window Width (s)', '{0:.1f}'.format(self._window_seconds)],
            ['Test Description', self.txt_test_desc.Text.strip()],
            ['Comment', self.txt_comment.Text.strip()],
            [],
            ['Chart Files'],
            ['Live Plot PNG', live_png],
            ['Full Plot PNG', full_png],
            ['PC Full Plot PNG', perf_full_png],
            ['Cumulative Delta Note', 'Cumulative delta can indicate dropped frames if it exceeds one frame exposure interval. '
             'It may later decrease as buffered frames are caught up, which can appear as short interval bursts.'],
        ])

        deltas = [s['delta_ms'] for s in samples if s.get('delta_ms') is not None]
        if deltas:
            mean_val = sum(deltas) / float(len(deltas))
            min_val = min(deltas)
            max_val = max(deltas)
            variance = sum((v - mean_val) ** 2 for v in deltas) / float(len(deltas) - 1) if len(deltas) > 1 else 0.0
            std_val = math.sqrt(variance) if variance > 0 else 0.0
            details_rows.extend([
                [],
                ['Summary Statistics'],
                ['Mean Delta (ms)', round(mean_val, 6)],
                ['Min Delta (ms)', round(min_val, 6)],
                ['Max Delta (ms)', round(max_val, 6)],
                ['Std Dev (ms)', round(std_val, 6)],
            ])

        analysis_rows = [['Frame #', 'UTC Timestamp', 'Elapsed Seconds', 'Interval Ms', 'Delta from Nominal Ms', 'Cumulative Delta Ms', 'CPU %', 'Memory %', 'Disk %', 'Network %']]
        perf_idx = -1
        cumulative_delta = 0.0
        have_cumulative = False
        for sample in samples:
            ts = sample.get('timestamp')
            elapsed_s = sample.get('elapsed_s', 0.0)

            while (perf_idx + 1) < len(perf_samples):
                next_elapsed = perf_samples[perf_idx + 1].get('elapsed_s')
                if next_elapsed is None or next_elapsed > elapsed_s:
                    break
                perf_idx += 1

            perf_sample = perf_samples[perf_idx] if perf_idx >= 0 else None
            sample_delta = sample.get('delta_ms')
            if sample_delta is not None:
                cumulative_delta += float(sample_delta)
                have_cumulative = True

            analysis_rows.append([
                sample.get('frame_no'),
                ts.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3] if ts else '',
                round(elapsed_s, 6),
                round(sample['interval_ms'], 6) if sample.get('interval_ms') is not None else '',
                round(sample_delta, 6) if sample_delta is not None else '',
                round(cumulative_delta, 6) if have_cumulative else '',
                round(perf_sample.get('cpu'), 6) if perf_sample and perf_sample.get('cpu') is not None else '',
                round(perf_sample.get('memory'), 6) if perf_sample and perf_sample.get('memory') is not None else '',
                round(perf_sample.get('disk'), 6) if perf_sample and perf_sample.get('disk') is not None else '',
                round(perf_sample.get('network'), 6) if perf_sample and perf_sample.get('network') is not None else '',
            ])

        perf_rows = [['Elapsed Seconds', 'CPU %', 'Memory %', 'Disk %', 'Network %']]
        for sample in perf_samples:
            perf_rows.append([
                round(sample.get('elapsed_s', 0.0), 6),
                round(sample.get('cpu'), 6) if sample.get('cpu') is not None else '',
                round(sample.get('memory'), 6) if sample.get('memory') is not None else '',
                round(sample.get('disk'), 6) if sample.get('disk') is not None else '',
                round(sample.get('network'), 6) if sample.get('network') is not None else '',
            ])

        writer = SimpleXlsxWriter()
        writer.save(output_path, [
            ('Details', details_rows),
            ('Full Analysis', analysis_rows),
            ('PC Stats', perf_rows),
        ])

        # Best-effort chart embedding for users who have Excel installed.
        # If Excel is unavailable, the PNG copies remain next to the workbook.
        self._embed_charts_with_excel(output_path, live_png, full_png, perf_full_png)

    def _save_plot_png(self, plot_view, filepath):
        width = plot_view.Width if plot_view.Width > 0 else 800
        height = plot_view.Height if plot_view.Height > 0 else 300
        bmp = Bitmap(width, height)
        try:
            plot_view.DrawToBitmap(bmp, Rectangle(0, 0, width, height))
            bmp.Save(filepath, System.Drawing.Imaging.ImageFormat.Png)
        finally:
            bmp.Dispose()

    def _embed_charts_with_excel(self, workbook_path, live_png, full_png, perf_full_png=None):
        try:
            excel_type = System.Type.GetTypeFromProgID('Excel.Application')
            if excel_type is None:
                return False

            excel = System.Activator.CreateInstance(excel_type)
            workbook = None
            try:
                excel.Visible = False
                excel.DisplayAlerts = False
                workbook = excel.Workbooks.Open(workbook_path)

                try:
                    existing = workbook.Worksheets['Charts']
                    existing.Delete()
                except Exception:
                    pass

                charts_sheet = workbook.Worksheets.Add()
                charts_sheet.Name = 'Charts'
                charts_sheet.Cells(1, 1).Value2 = 'Live plot'
                charts_sheet.Shapes.AddPicture(live_png, False, True, 10, 20, 920, 260)
                charts_sheet.Cells(22, 1).Value2 = 'Full duration plot'
                charts_sheet.Shapes.AddPicture(full_png, False, True, 10, 360, 920, 260)

                if perf_full_png and System.IO.File.Exists(perf_full_png):
                    charts_sheet.Cells(43, 1).Value2 = 'PC load (full duration)'
                    charts_sheet.Shapes.AddPicture(perf_full_png, False, True, 10, 700, 920, 260)

                workbook.Save()
                return True
            finally:
                try:
                    if workbook is not None:
                        workbook.Close(True)
                except Exception:
                    pass
                try:
                    excel.Quit()
                except Exception:
                    pass
        except Exception as ex:
            print('Could not embed charts in Excel workbook: {0}'.format(str(ex)))
            return False

    def _on_form_closing(self, sender, e):
        self._stop_requested = True
        try:
            if hasattr(self, '_perf_timer') and self._perf_timer is not None:
                self._perf_timer.Stop()
                self._perf_timer.Dispose()
        except Exception:
            pass


form = None

if __name__ == '__main__':
    if SharpCap is None:
        print('PC Performance Testing tool must be run from SharpCap.')
    else:
        form = PCPerformanceTestingForm(sharpcap=SharpCap, config=_om_config, theme_manager=None)
        form.Show()
