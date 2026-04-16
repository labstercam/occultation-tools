"""
Line Delay Calibration Dialogs for Occultation Manager.

Contains:
    LineDelayCalibrationManagerDialog  -- view, label, edit, delete, and manually add calibration runs
    ManualCalibrationEntryDialog       -- form for manually entering a calibration run
    LineDelayCalculatorDialog          -- calculate acquisition delay from stored calibrations
"""

import clr
clr.AddReference('System.Windows.Forms')
clr.AddReference('System.Drawing')

from System.Windows.Forms import (
    Form, Label, Button, TextBox, ComboBox, ComboBoxStyle, Clipboard,
    DataGridView, DataGridViewTextBoxColumn, DataGridViewSelectionMode,
    AnchorStyles,
    DialogResult, MessageBox, MessageBoxButtons, MessageBoxIcon,
    FormBorderStyle, FormStartPosition,
)
from System.Drawing import Point, Size, Color, Font, FontStyle

try:
    from theme import apply_theme_to_control
    _THEME_AVAILABLE = True
except ImportError:
    _THEME_AVAILABLE = False


class LineDelayCalibrationManagerDialog(Form):
    """Shows stored line delay calibration runs for a camera (or all cameras).

    Label and Notes cells are editable inline; changes are saved immediately to
    config. All other columns are read-only.

    Access points:
        Camera Manager → "Calibrations…" (filtered to selected camera)
        Tools menu → "Line Delay Calibrations…" (all cameras, camera_id=None)
    """

    def __init__(self, config, camera_id=None, camera_name=None, theme_manager=None):
        """
        config      : ConfigManager instance
        camera_id   : if provided, show only runs for this camera; None = all
        camera_name : display name for the title bar (optional)
        """
        self._config = config
        self._camera_id = camera_id
        self._camera_name = camera_name or 'All Cameras'
        self._theme_manager = theme_manager
        self._run_ids = []   # parallel list to DataGridView rows
        self.InitializeComponent()
        self._load_data()
        if theme_manager is not None and _THEME_AVAILABLE:
            apply_theme_to_control(self, theme_manager.get_current_theme())

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def InitializeComponent(self):
        self.Text = 'Calibration Runs \u2014 ' + self._camera_name
        self.Size = Size(1050, 570)
        self.MinimumSize = Size(800, 440)
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.StartPosition = FormStartPosition.CenterParent
        self.MaximizeBox = True
        self.MinimizeBox = False

        # Hint label at the top
        self._lbl_hint = Label()
        self._lbl_hint.Text = (
            'Click the Label or Notes cell in a row to edit it inline. '
            'Changes are saved automatically. '
            'Per Line Delay is in ms/line; Line 0 Delay is in ms.'
        )
        self._lbl_hint.Location = Point(10, 10)
        self._lbl_hint.Size = Size(1000, 18)
        self._lbl_hint.ForeColor = Color.DimGray
        self._lbl_hint.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right

        # DataGridView
        self._grid = DataGridView()
        self._grid.Location = Point(10, 34)
        self._grid.Size = Size(1020, 432)
        self._grid.Anchor = (
            AnchorStyles.Top | AnchorStyles.Bottom |
            AnchorStyles.Left | AnchorStyles.Right
        )
        self._grid.AllowUserToAddRows = False
        self._grid.AllowUserToDeleteRows = False
        self._grid.SelectionMode = DataGridViewSelectionMode.FullRowSelect
        self._grid.MultiSelect = False
        self._grid.RowHeadersVisible = False
        # EditMode defaults to EditOnKeystrokeOrF2 which is fine for inline editing
        self._grid.CellEndEdit += self._cell_end_edit

        # Column definitions: (field_key, header_text, width, read_only)
        col_defs = [
            ('run_datetime',   'Date/Time (UTC)',  140, True),
            ('label',          'Label',             45, False),   # editable
            ('camera_name',    'Camera Name',      130, True),
            ('camera_area',    'Camera Area',        80, True),
            ('binning',        'Binning',             55, True),
            ('tilt',           'Tilt',                45, True),
            ('pan',            'Pan',                 45, True),
            ('colour_space',   'Colour Space',        70, True),
            ('file_format',    'File Format',         70, True),
            ('exposure_ms',    'Exposure (ms)',        80, True),
            ('gain',           'Gain',                45, True),
            ('per_line_delay', 'Per Line (ms)',        90, True),
            ('line_0_delay',   'Line 0 (ms)',          80, True),
            ('notes',          'Notes',              160, False),   # editable
        ]
        # Prepend Camera column when showing all cameras
        if self._camera_id is None:
            col_defs.insert(0, ('camera_name', 'Camera', 110, True))

        self._col_keys = []
        for key, header, width, readonly in col_defs:
            col = DataGridViewTextBoxColumn()
            col.HeaderText = header
            col.Width = width
            col.ReadOnly = readonly
            col.Name = key
            col.SortMode = col.SortMode   # keep default (Automatic for text columns)
            self._grid.Columns.Add(col)
            self._col_keys.append(key)

        # Delete button — bottom-left
        self._btn_delete = Button()
        self._btn_delete.Text = 'Delete Selected'
        self._btn_delete.Location = Point(10, 476)
        self._btn_delete.Size = Size(130, 30)
        self._btn_delete.Anchor = AnchorStyles.Bottom | AnchorStyles.Left
        self._btn_delete.Click += self._delete_click

        # Add Manual Entry button — bottom-left (next to Delete)
        self._btn_add_manual = Button()
        self._btn_add_manual.Text = 'Add Manual Entry\u2026'
        self._btn_add_manual.Location = Point(148, 476)
        self._btn_add_manual.Size = Size(155, 30)
        self._btn_add_manual.Anchor = AnchorStyles.Bottom | AnchorStyles.Left
        # Only enabled when a specific camera is selected (not the all-cameras view)
        self._btn_add_manual.Enabled = (self._camera_id is not None)
        self._btn_add_manual.Click += self._add_manual_click

        # Row count label — bottom centre-left
        self._lbl_count = Label()
        self._lbl_count.Location = Point(312, 483)
        self._lbl_count.Size = Size(300, 18)
        self._lbl_count.Anchor = AnchorStyles.Bottom | AnchorStyles.Left
        self._lbl_count.ForeColor = Color.DimGray

        # Close button — bottom-right
        self._btn_close = Button()
        self._btn_close.Text = 'Close'
        self._btn_close.Location = Point(910, 476)
        self._btn_close.Size = Size(110, 30)
        self._btn_close.Anchor = AnchorStyles.Bottom | AnchorStyles.Right
        self._btn_close.Click += self._close_click

        for ctrl in [
            self._lbl_hint,
            self._grid,
            self._btn_delete,
            self._btn_add_manual,
            self._lbl_count,
            self._btn_close,
        ]:
            self.Controls.Add(ctrl)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_data(self):
        """Load calibration runs into the grid."""
        self._grid.Rows.Clear()
        self._run_ids = []

        runs = self._config.get_line_delay_calibrations(self._camera_id)
        # Sort newest first
        runs = sorted(runs, key=lambda r: r.get('run_datetime', ''), reverse=True)

        for run in runs:
            row_idx = self._grid.Rows.Add()
            for col_idx, key in enumerate(self._col_keys):
                val = run.get(key, '')
                if val is None:
                    val = ''
                if key == 'per_line_delay':
                    try:
                        display = '{:.4f}'.format(float(val))
                    except (ValueError, TypeError):
                        display = str(val)
                elif key == 'line_0_delay':
                    try:
                        display = '{:.2f}'.format(float(val))
                    except (ValueError, TypeError):
                        display = str(val)
                else:
                    display = str(val)
                self._grid.Rows[row_idx].Cells[col_idx].Value = display
            self._run_ids.append(run.get('id', ''))

        count = len(runs)
        self._lbl_count.Text = '{0} run{1}'.format(count, '' if count == 1 else 's')

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _cell_end_edit(self, sender, event):
        """Save inline edits to Label or Notes immediately to config."""
        row_idx = event.RowIndex
        col_idx = event.ColumnIndex
        if row_idx < 0 or row_idx >= len(self._run_ids):
            return
        key = self._col_keys[col_idx]
        if key not in ('label', 'notes'):
            return
        run_id = self._run_ids[row_idx]
        cell_val = self._grid.Rows[row_idx].Cells[col_idx].Value
        new_val = str(cell_val).strip() if cell_val is not None else ''
        try:
            self._config.update_line_delay_calibration(run_id, {key: new_val})
        except Exception as ex:
            MessageBox.Show(
                'Could not save change:\n' + str(ex),
                'Save Error',
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )

    def _delete_click(self, sender, event):
        """Delete the currently selected calibration run after confirmation."""
        current = self._grid.CurrentRow
        if current is None:
            MessageBox.Show(
                'Select a row to delete.',
                'No Selection',
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            return
        idx = current.Index
        if idx < 0 or idx >= len(self._run_ids):
            return
        result = MessageBox.Show(
            'Delete this calibration run?\n\nThis cannot be undone.',
            'Confirm Delete',
            MessageBoxButtons.YesNo,
            MessageBoxIcon.Warning
        )
        if result == DialogResult.Yes:
            run_id = self._run_ids[idx]
            self._config.delete_line_delay_calibration(run_id)
            self._load_data()

    def _close_click(self, sender, event):
        self.DialogResult = DialogResult.OK
        self.Close()

    def _add_manual_click(self, sender, event):
        """Open the manual calibration entry dialog; reload grid on save."""
        dlg = ManualCalibrationEntryDialog(
            self._config,
            self._camera_id,
            self._camera_name,
            theme_manager=self._theme_manager,
        )
        if dlg.ShowDialog(self) == DialogResult.OK:
            self._load_data()


class LineDelayCalculatorDialog(Form):
    """Calculator for rolling-shutter line delay.

    Formula:  Delay (ms) = per_line_delay (ms/line) × Y + line_0_delay (ms)

    Where Y is the occulted star's vertical pixel position on the sensor.
    The result can be copied to the clipboard and pasted into TANGRA.
    """

    def __init__(self, config, theme_manager=None):
        self._config = config
        self._theme_manager = theme_manager
        self._calib_data = []   # run dicts for the selected camera
        self._camera_ids = []
        self._current_delay = None   # float or None
        self.InitializeComponent()
        self._load_cameras()
        if theme_manager is not None and _THEME_AVAILABLE:
            apply_theme_to_control(self, theme_manager.get_current_theme())

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def InitializeComponent(self):
        self.Text = 'Camera Delay Calculator'
        self.ClientSize = Size(460, 362)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.StartPosition = FormStartPosition.CenterParent

        y = 15

        # --- Camera row ---
        lbl_cam = Label()
        lbl_cam.Text = 'Camera:'
        lbl_cam.Location = Point(15, y + 3)
        lbl_cam.AutoSize = True

        self._combo_camera = ComboBox()
        self._combo_camera.Location = Point(145, y)
        self._combo_camera.Size = Size(295, 22)
        self._combo_camera.DropDownStyle = ComboBoxStyle.DropDownList
        self._combo_camera.SelectedIndexChanged += self._camera_changed

        y += 34

        # --- Calibration row ---
        lbl_calib = Label()
        lbl_calib.Text = 'Calibration:'
        lbl_calib.Location = Point(15, y + 3)
        lbl_calib.AutoSize = True

        self._combo_calib = ComboBox()
        self._combo_calib.Location = Point(145, y)
        self._combo_calib.Size = Size(295, 22)
        self._combo_calib.DropDownStyle = ComboBoxStyle.DropDownList
        self._combo_calib.SelectedIndexChanged += self._update_result

        y += 26

        # No-calibrations hint (hidden when calibrations exist)
        self._lbl_no_calib = Label()
        self._lbl_no_calib.Text = (
            'No calibrations stored for this camera \u2014 '
            'run a GPS Flash Calibration first.'
        )
        self._lbl_no_calib.Location = Point(145, y)
        self._lbl_no_calib.Size = Size(295, 32)
        self._lbl_no_calib.ForeColor = Color.DarkRed
        self._lbl_no_calib.Visible = False

        y += 36

        # --- Y line row ---
        lbl_y = Label()
        lbl_y.Text = 'Occulted Star Y Line:'
        lbl_y.Location = Point(15, y + 3)
        lbl_y.AutoSize = True

        self._txt_y = TextBox()
        self._txt_y.Location = Point(175, y)
        self._txt_y.Size = Size(80, 22)
        self._txt_y.TextChanged += self._update_result

        lbl_px = Label()
        lbl_px.Text = 'pixels'
        lbl_px.Location = Point(263, y + 3)
        lbl_px.AutoSize = True
        lbl_px.ForeColor = Color.DimGray

        y += 42

        # --- Result section ---
        lbl_result_title = Label()
        lbl_result_title.Text = 'Calculated Acquisition Delay'
        lbl_result_title.Location = Point(15, y)
        lbl_result_title.AutoSize = True
        lbl_result_title.ForeColor = Color.DimGray

        y += 22

        self._lbl_result = Label()
        self._lbl_result.Text = '\u2014'
        self._lbl_result.Location = Point(15, y)
        self._lbl_result.Size = Size(430, 42)
        self._lbl_result.Font = Font(
            self._lbl_result.Font.FontFamily, 22, FontStyle.Bold)
        self._lbl_result.ForeColor = Color.DarkBlue

        y += 48

        self._lbl_formula = Label()
        self._lbl_formula.Text = 'Per Line Delay \u00d7 Y + Line 0 Delay'
        self._lbl_formula.Location = Point(15, y)
        self._lbl_formula.AutoSize = True
        self._lbl_formula.ForeColor = Color.DimGray

        y += 22

        self._lbl_formula_vals = Label()
        self._lbl_formula_vals.Text = ''
        self._lbl_formula_vals.Location = Point(15, y)
        self._lbl_formula_vals.Size = Size(430, 17)
        self._lbl_formula_vals.ForeColor = Color.DimGray

        y += 34

        # --- Buttons ---
        btn_manage = Button()
        btn_manage.Text = 'Manage Calibrations\u2026'
        btn_manage.Location = Point(15, y)
        btn_manage.Size = Size(173, 28)
        btn_manage.Click += self._manage_click

        self._btn_copy = Button()
        self._btn_copy.Text = 'Copy'
        self._btn_copy.Location = Point(245, y)
        self._btn_copy.Size = Size(90, 28)
        self._btn_copy.Enabled = False
        self._btn_copy.Click += self._copy_click

        btn_close = Button()
        btn_close.Text = 'Close'
        btn_close.Location = Point(345, y)
        btn_close.Size = Size(100, 28)
        btn_close.Click += self._close_click

        for ctrl in [
            lbl_cam, self._combo_camera,
            lbl_calib, self._combo_calib, self._lbl_no_calib,
            lbl_y, self._txt_y, lbl_px,
            lbl_result_title, self._lbl_result,
            self._lbl_formula, self._lbl_formula_vals,
            btn_manage, self._btn_copy, btn_close,
        ]:
            self.Controls.Add(ctrl)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_cameras(self):
        self._combo_camera.Items.Clear()
        self._camera_ids = []
        cameras = self._config.get_cameras()
        if not cameras:
            self._combo_camera.Items.Add('(No cameras configured)')
            self._combo_camera.SelectedIndex = 0
            self._combo_camera.Enabled = False
            return
        for cam in cameras:
            self._combo_camera.Items.Add(cam.get('name', ''))
            self._camera_ids.append(cam['id'])
        self._combo_camera.SelectedIndex = 0   # triggers _camera_changed

    def _reload_calibrations(self):
        self._combo_calib.Items.Clear()
        self._calib_data = []
        idx = self._combo_camera.SelectedIndex
        if idx < 0 or idx >= len(self._camera_ids):
            self._combo_calib.Enabled = False
            self._lbl_no_calib.Visible = False
            return
        cam_id = self._camera_ids[idx]
        runs = self._config.get_line_delay_calibrations(cam_id)
        # Sort: labelled runs first (alphabetically), then unlabelled
        runs = sorted(runs, key=lambda r: (r.get('label', '') == '', r.get('label', ''), r.get('run_datetime', '')))
        self._calib_data = runs
        if not runs:
            self._combo_calib.Enabled = False
            self._lbl_no_calib.Visible = True
            return
        self._combo_calib.Enabled = True
        self._lbl_no_calib.Visible = False
        for run in runs:
            label = run.get('label', '?')
            parts = []
            area = run.get('camera_area', '')
            binning = run.get('binning', '')
            if area:
                parts.append(area)
            if binning:
                parts.append('bin ' + str(binning))
            display = label
            if parts:
                display += ' \u2014 ' + ', '.join(parts)
            self._combo_calib.Items.Add(display)
        self._combo_calib.SelectedIndex = 0

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _camera_changed(self, sender, event):
        self._reload_calibrations()
        self._update_result(None, None)

    def _update_result(self, sender, event):
        self._lbl_result.Text = '\u2014'
        self._lbl_formula_vals.Text = ''
        self._btn_copy.Enabled = False
        self._current_delay = None

        # Need a calibration selected
        idx = self._combo_calib.SelectedIndex
        if idx < 0 or idx >= len(self._calib_data):
            return
        run = self._calib_data[idx]

        slope = run.get('per_line_delay')
        intercept = run.get('line_0_delay')
        if slope is None or intercept is None:
            self._lbl_formula_vals.Text = 'Calibration data incomplete (missing slope or intercept).'
            return
        try:
            slope = float(slope)
            intercept = float(intercept)
        except (ValueError, TypeError):
            self._lbl_formula_vals.Text = 'Calibration data could not be parsed.'
            return

        # Parse Y line
        y_text = self._txt_y.Text.strip()
        if not y_text:
            self._lbl_formula_vals.Text = 'Enter a Y line value above.'
            return
        try:
            y_val = float(y_text)
        except ValueError:
            self._lbl_formula_vals.Text = 'Y line must be a number.'
            return

        # Range validation using camera_area from the calibration run (e.g. "440x411")
        area = str(run.get('camera_area', '') or '')
        y_max = None
        try:
            parts = area.lower().split('x')
            if len(parts) >= 2:
                y_max = int(parts[1])
        except (ValueError, IndexError):
            pass

        if y_val < 0 or (y_max is not None and y_val > y_max):
            if y_max is not None:
                self._lbl_formula_vals.Text = (
                    'Y must be 0\u2013{0} (camera area: {1}).'.format(y_max, area))
            else:
                self._lbl_formula_vals.Text = 'Y line must be \u22650.'
            return

        delay = slope * y_val + intercept
        self._current_delay = delay
        self._lbl_result.Text = '{0:.3f} ms'.format(delay)
        self._lbl_formula_vals.Text = '{0:.6g} \u00d7 {1} + {2:.6g} = {3:.3f} ms'.format(
            slope, y_text, intercept, delay)
        self._btn_copy.Enabled = True

    def _copy_click(self, sender, event):
        if self._current_delay is None:
            return
        text = '{0:.3f}'.format(self._current_delay)
        try:
            Clipboard.SetText(text)
        except Exception as ex:
            MessageBox.Show(
                'Could not copy to clipboard:\n' + str(ex),
                'Copy Error',
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )

    def _manage_click(self, sender, event):
        cam_idx = self._combo_camera.SelectedIndex
        cam_id = (self._camera_ids[cam_idx]
                  if 0 <= cam_idx < len(self._camera_ids) else None)
        cam_name = (self._combo_camera.Text
                    if cam_id else 'All Cameras')
        dlg = LineDelayCalibrationManagerDialog(
            self._config,
            camera_id=cam_id,
            camera_name=cam_name,
            theme_manager=self._theme_manager,
        )
        dlg.ShowDialog(self)
        # Refresh calibrations in case the user deleted or edited entries
        self._reload_calibrations()
        self._update_result(None, None)

    def _close_click(self, sender, event):
        self.Close()


class ManualCalibrationEntryDialog(Form):
    """Form for manually entering a line delay calibration run.

    Useful when calibration values are known from an external source (another
    tool, a published measurement, an older spreadsheet) and need to be stored
    against a camera without running the GPS Flash Calibration capture.

    Per Line Delay and Line 0 Delay are required; all other fields are optional.
    """

    def __init__(self, config, camera_id, camera_name, theme_manager=None):
        self._config = config
        self._camera_id = camera_id
        self._camera_name = camera_name
        self._theme_manager = theme_manager
        self.InitializeComponent()
        if theme_manager is not None and _THEME_AVAILABLE:
            apply_theme_to_control(self, theme_manager.get_current_theme())

    # ------------------------------------------------------------------
    # UI setup
    # ------------------------------------------------------------------

    def InitializeComponent(self):
        self.Text = 'Add Manual Calibration \u2014 ' + self._camera_name
        self.ClientSize = Size(450, 440)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.StartPosition = FormStartPosition.CenterParent

        LX = 15    # label column x
        TX = 175   # textbox column x
        TW = 255   # standard textbox width
        RH = 28    # row height
        y = 12

        # Camera indicator
        lbl_cam = Label()
        lbl_cam.Text = 'Camera: ' + self._camera_name
        lbl_cam.Location = Point(LX, y)
        lbl_cam.AutoSize = True
        lbl_cam.ForeColor = Color.DimGray
        y += RH

        # --- Calibration Results (required) ---
        lbl_req_hdr = Label()
        lbl_req_hdr.Text = 'Calibration Results  (required)'
        lbl_req_hdr.Location = Point(LX, y)
        lbl_req_hdr.AutoSize = True
        lbl_req_hdr.Font = Font(
            lbl_req_hdr.Font.FontFamily, lbl_req_hdr.Font.Size, FontStyle.Bold)
        y += 22

        lbl_pld = Label()
        lbl_pld.Text = 'Per Line Delay (ms/line):'
        lbl_pld.Location = Point(LX, y + 3)
        lbl_pld.AutoSize = True
        self._txt_per_line = TextBox()
        self._txt_per_line.Location = Point(TX, y)
        self._txt_per_line.Size = Size(120, 22)
        y += RH

        lbl_l0 = Label()
        lbl_l0.Text = 'Line 0 Delay (ms):'
        lbl_l0.Location = Point(LX, y + 3)
        lbl_l0.AutoSize = True
        self._txt_line0 = TextBox()
        self._txt_line0.Location = Point(TX, y)
        self._txt_line0.Size = Size(120, 22)
        y += RH + 8

        # --- Camera Settings (optional) ---
        lbl_cam_hdr = Label()
        lbl_cam_hdr.Text = 'Camera Settings  (optional)'
        lbl_cam_hdr.Location = Point(LX, y)
        lbl_cam_hdr.AutoSize = True
        lbl_cam_hdr.Font = Font(
            lbl_cam_hdr.Font.FontFamily, lbl_cam_hdr.Font.Size, FontStyle.Bold)
        y += 22

        lbl_area = Label()
        lbl_area.Text = 'Camera Area:'
        lbl_area.Location = Point(LX, y + 3)
        lbl_area.AutoSize = True
        self._txt_area = TextBox()
        self._txt_area.Location = Point(TX, y)
        self._txt_area.Size = Size(TW, 22)
        y += RH

        lbl_bin = Label()
        lbl_bin.Text = 'Binning:'
        lbl_bin.Location = Point(LX, y + 3)
        lbl_bin.AutoSize = True
        self._txt_binning = TextBox()
        self._txt_binning.Location = Point(TX, y)
        self._txt_binning.Size = Size(60, 22)
        y += RH

        # Tilt and Pan on the same row
        lbl_tilt = Label()
        lbl_tilt.Text = 'Tilt:'
        lbl_tilt.Location = Point(LX, y + 3)
        lbl_tilt.AutoSize = True
        self._txt_tilt = TextBox()
        self._txt_tilt.Location = Point(TX, y)
        self._txt_tilt.Size = Size(60, 22)
        lbl_pan = Label()
        lbl_pan.Text = 'Pan:'
        lbl_pan.Location = Point(TX + 70, y + 3)
        lbl_pan.AutoSize = True
        self._txt_pan = TextBox()
        self._txt_pan.Location = Point(TX + 100, y)
        self._txt_pan.Size = Size(60, 22)
        y += RH

        lbl_cs = Label()
        lbl_cs.Text = 'Colour Space:'
        lbl_cs.Location = Point(LX, y + 3)
        lbl_cs.AutoSize = True
        self._txt_colour_space = TextBox()
        self._txt_colour_space.Location = Point(TX, y)
        self._txt_colour_space.Size = Size(TW, 22)
        y += RH

        lbl_ff = Label()
        lbl_ff.Text = 'File Format:'
        lbl_ff.Location = Point(LX, y + 3)
        lbl_ff.AutoSize = True
        self._txt_file_format = TextBox()
        self._txt_file_format.Location = Point(TX, y)
        self._txt_file_format.Size = Size(TW, 22)
        y += RH

        # Exposure and Gain on the same row
        lbl_exp = Label()
        lbl_exp.Text = 'Exposure (ms):'
        lbl_exp.Location = Point(LX, y + 3)
        lbl_exp.AutoSize = True
        self._txt_exp = TextBox()
        self._txt_exp.Location = Point(TX, y)
        self._txt_exp.Size = Size(80, 22)
        lbl_gain = Label()
        lbl_gain.Text = 'Gain:'
        lbl_gain.Location = Point(TX + 90, y + 3)
        lbl_gain.AutoSize = True
        self._txt_gain = TextBox()
        self._txt_gain.Location = Point(TX + 120, y)
        self._txt_gain.Size = Size(80, 22)
        y += RH + 8

        # --- Label and Notes ---
        lbl_lbl = Label()
        lbl_lbl.Text = 'Label (A, B, C\u2026):'
        lbl_lbl.Location = Point(LX, y + 3)
        lbl_lbl.AutoSize = True
        self._txt_label = TextBox()
        self._txt_label.Location = Point(TX, y)
        self._txt_label.Size = Size(60, 22)
        y += RH

        lbl_notes = Label()
        lbl_notes.Text = 'Notes:'
        lbl_notes.Location = Point(LX, y + 3)
        lbl_notes.AutoSize = True
        self._txt_notes = TextBox()
        self._txt_notes.Location = Point(TX, y)
        self._txt_notes.Size = Size(TW, 22)
        y += RH + 10

        # --- Buttons ---
        btn_save = Button()
        btn_save.Text = 'Save'
        btn_save.Location = Point(TX, y)
        btn_save.Size = Size(110, 30)
        btn_save.Click += self._save_click

        btn_cancel = Button()
        btn_cancel.Text = 'Cancel'
        btn_cancel.Location = Point(TX + 120, y)
        btn_cancel.Size = Size(110, 30)
        btn_cancel.Click += self._cancel_click

        for ctrl in [
            lbl_cam,
            lbl_req_hdr, lbl_pld, self._txt_per_line, lbl_l0, self._txt_line0,
            lbl_cam_hdr,
            lbl_area, self._txt_area,
            lbl_bin, self._txt_binning,
            lbl_tilt, self._txt_tilt, lbl_pan, self._txt_pan,
            lbl_cs, self._txt_colour_space,
            lbl_ff, self._txt_file_format,
            lbl_exp, self._txt_exp, lbl_gain, self._txt_gain,
            lbl_lbl, self._txt_label,
            lbl_notes, self._txt_notes,
            btn_save, btn_cancel,
        ]:
            self.Controls.Add(ctrl)

    # ------------------------------------------------------------------
    # Event handlers
    # ------------------------------------------------------------------

    def _save_click(self, sender, event):
        """Validate inputs then save the manual calibration run to config."""
        per_line_text = self._txt_per_line.Text.strip()
        line0_text = self._txt_line0.Text.strip()

        if not per_line_text:
            MessageBox.Show(
                'Per Line Delay is required.',
                'Validation Error',
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return
        if not line0_text:
            MessageBox.Show(
                'Line 0 Delay is required.',
                'Validation Error',
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return

        try:
            per_line_delay = float(per_line_text)
        except ValueError:
            MessageBox.Show(
                'Per Line Delay must be a number (e.g. -0.040).',
                'Validation Error',
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return

        try:
            line_0_delay = float(line0_text)
        except ValueError:
            MessageBox.Show(
                'Line 0 Delay must be a number.',
                'Validation Error',
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return

        # Optional numeric fields
        tilt_text = self._txt_tilt.Text.strip()
        pan_text = self._txt_pan.Text.strip()
        exp_text = self._txt_exp.Text.strip()

        tilt = None
        if tilt_text:
            try:
                tilt = int(tilt_text)
            except ValueError:
                MessageBox.Show(
                    'Tilt must be an integer.',
                    'Validation Error',
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                )
                return

        pan = None
        if pan_text:
            try:
                pan = int(pan_text)
            except ValueError:
                MessageBox.Show(
                    'Pan must be an integer.',
                    'Validation Error',
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                )
                return

        exposure_ms = None
        if exp_text:
            try:
                exposure_ms = float(exp_text)
            except ValueError:
                MessageBox.Show(
                    'Exposure must be a number.',
                    'Validation Error',
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Warning
                )
                return

        import datetime
        run_dict = {
            'camera_id':      self._camera_id,
            'run_datetime':   datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'per_line_delay': per_line_delay,
            'line_0_delay':   line_0_delay,
            'camera_area':    self._txt_area.Text.strip() or None,
            'binning':        self._txt_binning.Text.strip() or None,
            'tilt':           tilt,
            'pan':            pan,
            'colour_space':   self._txt_colour_space.Text.strip() or None,
            'file_format':    self._txt_file_format.Text.strip() or None,
            'exposure_ms':    exposure_ms,
            'gain':           self._txt_gain.Text.strip() or None,
            'label':          self._txt_label.Text.strip(),
            'notes':          self._txt_notes.Text.strip(),
        }
        try:
            self._config.add_line_delay_calibration(run_dict)
            self.DialogResult = DialogResult.OK
            self.Close()
        except Exception as ex:
            MessageBox.Show(
                'Could not save calibration:\n' + str(ex),
                'Save Error',
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )

    def _cancel_click(self, sender, event):
        self.DialogResult = DialogResult.Cancel
        self.Close()
