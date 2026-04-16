"""
VizieR Light Curve Export Dialog.

Presents a WinForms dialog pre-populated from the current event record for
configuring and writing VizieR .dat light curve files from a loaded
occultation observation.

Constructor:
    VizierExportDialog(lc_path, event, config, theme_manager,
                       observation_folder, aota_report_data=None, timing_data=None)

IronPython 3.4 compatible (no pathlib, no typing, no numpy).
"""

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("System")

# Chart uses GDI+ (PictureBox + Paint event) — no DataVisualization dependency.

import os
import System
from System.Drawing import Point, Size, Color, Font, FontStyle, Pen, SolidBrush, Rectangle
from System.Windows.Forms import (
    Form, Button, Label, TextBox, GroupBox, NumericUpDown, CheckBox,
    MessageBox, MessageBoxButtons, MessageBoxIcon,
    FormStartPosition, PictureBox, BorderStyle,
)
from theme import apply_theme_to_control
import light_curve_reader as lcr
from vizier_export import (
    parse_star_id,
    compute_median_step,
    insert_dropped_readings,
    compute_trim_window,
    to_seconds,
    export_all_copies,
)
from vizier_export import _is_neg_zero


class VizierExportDialog(Form):
    """WinForms dialog for exporting a light curve to VizieR .dat format."""

    def __init__(self, lc_path, event, config, theme_manager,
                 observation_folder, aota_report_data=None, timing_data=None):
        """Initialise the dialog and load the light curve.

        Args:
            lc_path:            str path to the light curve CSV file.
            event:              OccultationEvent with object_no, object_name,
                                star_id, latitude, longitude, elevation,
                                event_date, get_asteroid_display_name().
            config:             ConfigManager with get_observer_name(),
                                get_reports_folder().
            theme_manager:      Theme manager for consistent styling.
            observation_folder: str path to the folder containing the light curve.
            aota_report_data:   Optional dict with d_hours/d_minutes/d_seconds
                                and r_hours/r_minutes/r_seconds for auto-trim.
            timing_data:        Optional dict from ComprehensiveReportDialog.get_timing_data().
        """
        Form.__init__(self)
        self._lc_path = lc_path
        self._event = event
        self._config = config
        self._theme_manager = theme_manager
        self._observation_folder = observation_folder or ''
        self._aota_report_data = aota_report_data or {}
        self._timing_data = timing_data

        # Standalone timing panel controls (only created when timing_data is None)
        self._chk_already_corrected = None
        self._nud_manual_offset = None

        # Expanded light curve (set in _load_and_prepare)
        self._exp_frames = []
        self._exp_times = []
        self._exp_values = []
        self._time_step_s = None
        self._d_time_s = None   # disappearance seconds-from-midnight
        self._r_time_s = None   # reappearance seconds-from-midnight

        # Chart PictureBox (set in _setup_ui)
        self._chart = None

        # Reentrancy guard for NUD ValueChanged
        self._trim_updating = False

        self._setup_ui()
        self._load_and_prepare()

        if theme_manager:
            theme_colors = theme_manager.get_current_theme()
            apply_theme_to_control(self, theme_colors)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _setup_ui(self):
        self.Text = "Export VizieR Light Curve"
        self.Size = Size(920, 930 if self._timing_data is None else 840)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False

        y = 10

        # ---- Header --------------------------------------------------
        lbl_title = Label()
        lbl_title.Text = "VizieR Light Curve Export"
        if self._event:
            try:
                lbl_title.Text = "VizieR Export \u2014 " + self._event.get_asteroid_display_name()
            except Exception:
                pass
        lbl_title.Font = Font(lbl_title.Font.FontFamily, 11, FontStyle.Bold)
        lbl_title.Location = Point(12, y)
        lbl_title.Size = Size(884, 26)
        self.Controls.Add(lbl_title)
        y += 28

        lbl_path = Label()
        lbl_path.Text = "File: " + os.path.basename(self._lc_path)
        lbl_path.ForeColor = Color.Gray
        lbl_path.Location = Point(14, y)
        lbl_path.Size = Size(884, 18)
        self.Controls.Add(lbl_path)
        y += 24

        # ---- 1. Star Catalog Identifiers -----------------------------
        grp_star = GroupBox()
        grp_star.Text = "1. Star Catalog Identifiers"
        grp_star.Location = Point(10, y)
        grp_star.Size = Size(884, 110)
        self.Controls.Add(grp_star)

        lbl_note = Label()
        lbl_note.Text = "Pre-filled from event star ID. Edit if needed, or leave blank if not in catalog."
        lbl_note.ForeColor = Color.Gray
        lbl_note.Location = Point(12, 20)
        lbl_note.Size = Size(860, 16)
        grp_star.Controls.Add(lbl_note)

        # Parse star ID
        star_ids = {}
        if self._event:
            raw_star_id = getattr(self._event, 'star_id', '') or ''
            if raw_star_id:
                star_ids = parse_star_id(raw_star_id)

        # UCAC4
        lbl_ucac4 = Label()
        lbl_ucac4.Text = "UCAC4:"
        lbl_ucac4.Location = Point(12, 44)
        lbl_ucac4.Size = Size(58, 20)
        grp_star.Controls.Add(lbl_ucac4)

        self.txt_ucac4 = TextBox()
        self.txt_ucac4.Location = Point(73, 41)
        self.txt_ucac4.Size = Size(180, 22)
        self.txt_ucac4.Text = star_ids.get('ucac4', '')
        grp_star.Controls.Add(self.txt_ucac4)

        # Tycho2
        lbl_tycho2 = Label()
        lbl_tycho2.Text = "Tycho2:"
        lbl_tycho2.Location = Point(275, 44)
        lbl_tycho2.Size = Size(60, 20)
        grp_star.Controls.Add(lbl_tycho2)

        self.txt_tycho2 = TextBox()
        self.txt_tycho2.Location = Point(338, 41)
        self.txt_tycho2.Size = Size(180, 22)
        self.txt_tycho2.Text = star_ids.get('tycho2', '')
        grp_star.Controls.Add(self.txt_tycho2)

        # Hipparcos
        lbl_hip = Label()
        lbl_hip.Text = "Hipparcos:"
        lbl_hip.Location = Point(540, 44)
        lbl_hip.Size = Size(80, 20)
        grp_star.Controls.Add(lbl_hip)

        self.txt_hip = TextBox()
        self.txt_hip.Location = Point(623, 41)
        self.txt_hip.Size = Size(180, 22)
        self.txt_hip.Text = star_ids.get('hipparcos', '')
        grp_star.Controls.Add(self.txt_hip)

        # Format hint
        lbl_fmt = Label()
        lbl_fmt.Text = "Formats:  UCAC4 = 361-199861   |   Tycho2 = 1234-5678-1   |   Hipparcos = 12345"
        lbl_fmt.ForeColor = Color.DarkGray
        lbl_fmt.Location = Point(12, 70)
        lbl_fmt.Size = Size(860, 16)
        grp_star.Controls.Add(lbl_fmt)

        # Warning if star ID couldn't be parsed
        self.lbl_star_warn = Label()
        self.lbl_star_warn.Text = ""
        self.lbl_star_warn.ForeColor = Color.OrangeRed
        self.lbl_star_warn.Location = Point(12, 88)
        self.lbl_star_warn.Size = Size(860, 16)
        grp_star.Controls.Add(self.lbl_star_warn)

        if self._event:
            raw = getattr(self._event, 'star_id', '') or ''
            if raw and not any(star_ids.values()):
                self.lbl_star_warn.Text = (
                    "Could not parse '%s' — please enter catalog IDs manually." % raw
                )

        y += 120

        # ---- 2. Observer & Object ------------------------------------
        grp_obs = GroupBox()
        grp_obs.Text = "2. Observer & Object"
        grp_obs.Location = Point(10, y)
        grp_obs.Size = Size(884, 78)
        self.Controls.Add(grp_obs)

        observer_name = ''
        if self._config:
            try:
                observer_name = self._config.get_observer_name() or ''
            except Exception:
                pass

        lat = float(getattr(self._event, 'latitude', 0.0) or 0.0) if self._event else 0.0
        lon = float(getattr(self._event, 'longitude', 0.0) or 0.0) if self._event else 0.0
        elev = int(getattr(self._event, 'elevation', 0) or 0) if self._event else 0

        lbl_obs1 = Label()
        lbl_obs1.Text = "Observer: %s    Lat: %.5f\u00b0    Lon: %.5f\u00b0    Elevation: %d m" % (
            observer_name, lat, lon, elev)
        lbl_obs1.Location = Point(12, 22)
        lbl_obs1.Size = Size(860, 20)
        grp_obs.Controls.Add(lbl_obs1)

        obj_no = str(getattr(self._event, 'object_no', '') or '') if self._event else ''
        obj_name = str(getattr(self._event, 'object_name', '') or '') if self._event else ''
        star_display = str(getattr(self._event, 'star_id', '') or '') if self._event else ''

        lbl_obs2 = Label()
        lbl_obs2.Text = "Asteroid: (%s) %s    Star ID: %s" % (obj_no, obj_name, star_display)
        lbl_obs2.Location = Point(12, 46)
        lbl_obs2.Size = Size(860, 20)
        grp_obs.Controls.Add(lbl_obs2)

        y += 88

        # ---- 3. Trim Window ------------------------------------------
        grp_trim = GroupBox()
        grp_trim.Text = "3. Trim Window"
        grp_trim.Location = Point(10, y)
        grp_trim.Size = Size(884, 76)
        self.Controls.Add(grp_trim)

        # NUDs store 0-based indices into _exp_frames/_exp_values.  The small
        # grey labels below each NUD show the corresponding actual frame number
        # so the user can cross-reference against the chart X-axis.
        lbl_first = Label()
        lbl_first.Text = "First index:"
        lbl_first.Location = Point(12, 27)
        lbl_first.Size = Size(80, 20)
        grp_trim.Controls.Add(lbl_first)

        self.nud_first = NumericUpDown()
        self.nud_first.Location = Point(95, 24)
        self.nud_first.Size = Size(90, 22)
        self.nud_first.Minimum = System.Decimal(0)
        self.nud_first.Maximum = System.Decimal(999999)
        self.nud_first.ValueChanged += self._trim_changed
        grp_trim.Controls.Add(self.nud_first)

        self.lbl_first_frame = Label()
        self.lbl_first_frame.Text = ""
        self.lbl_first_frame.ForeColor = Color.DimGray
        self.lbl_first_frame.Location = Point(95, 48)
        self.lbl_first_frame.Size = Size(130, 16)
        grp_trim.Controls.Add(self.lbl_first_frame)

        lbl_last = Label()
        lbl_last.Text = "Last index:"
        lbl_last.Location = Point(240, 27)
        lbl_last.Size = Size(75, 20)
        grp_trim.Controls.Add(lbl_last)

        self.nud_last = NumericUpDown()
        self.nud_last.Location = Point(318, 24)
        self.nud_last.Size = Size(90, 22)
        self.nud_last.Minimum = System.Decimal(0)
        self.nud_last.Maximum = System.Decimal(999999)
        self.nud_last.ValueChanged += self._trim_changed
        grp_trim.Controls.Add(self.nud_last)

        self.lbl_last_frame = Label()
        self.lbl_last_frame.Text = ""
        self.lbl_last_frame.ForeColor = Color.DimGray
        self.lbl_last_frame.Location = Point(318, 48)
        self.lbl_last_frame.Size = Size(130, 16)
        grp_trim.Controls.Add(self.lbl_last_frame)

        btn_auto_trim = Button()
        btn_auto_trim.Text = "Auto Trim"
        btn_auto_trim.Location = Point(422, 22)
        btn_auto_trim.Size = Size(88, 26)
        btn_auto_trim.Click += self._auto_trim_click
        grp_trim.Controls.Add(btn_auto_trim)

        self.lbl_trim_info = Label()
        self.lbl_trim_info.Text = "Duration: \u2014"
        self.lbl_trim_info.ForeColor = Color.DimGray
        self.lbl_trim_info.Location = Point(522, 28)
        self.lbl_trim_info.Size = Size(350, 18)
        grp_trim.Controls.Add(self.lbl_trim_info)

        y += 86

        # ---- 4. Light Curve Preview -----------------------------------
        grp_chart = GroupBox()
        grp_chart.Text = "4. Light Curve Preview"
        grp_chart.Location = Point(10, y)
        grp_chart.Size = Size(884, 380)
        self.Controls.Add(grp_chart)

        self._chart = PictureBox()
        self._chart.Location = Point(8, 18)
        self._chart.Size = Size(864, 354)
        self._chart.BackColor = Color.White
        self._chart.BorderStyle = BorderStyle.FixedSingle
        self._chart.Paint += self._chart_paint
        grp_chart.Controls.Add(self._chart)

        y += 390

        # ---- 5. Timing (standalone mode only) -----------------------
        # Shown when no timing_data is provided from the report workflow.
        # Allows the user to declare whether the light curve is already
        # corrected, or enter a manual additional offset.
        if self._timing_data is None:
            grp_timing = GroupBox()
            grp_timing.Text = "5. Timing Correction"
            grp_timing.Location = Point(10, y)
            grp_timing.Size = Size(884, 72)
            self.Controls.Add(grp_timing)

            self._chk_already_corrected = CheckBox()
            self._chk_already_corrected.Text = (
                "Light curve timestamps are already corrected "
                "(NTP offset + camera delay applied in source)"
            )
            self._chk_already_corrected.Location = Point(12, 18)
            self._chk_already_corrected.Size = Size(858, 20)
            self._chk_already_corrected.CheckedChanged += self._on_standalone_timing_changed
            grp_timing.Controls.Add(self._chk_already_corrected)

            lbl_offset = Label()
            lbl_offset.Text = "Additional offset:"
            lbl_offset.Location = Point(12, 46)
            lbl_offset.Size = Size(118, 20)
            grp_timing.Controls.Add(lbl_offset)

            self._nud_manual_offset = NumericUpDown()
            self._nud_manual_offset.Location = Point(133, 43)
            self._nud_manual_offset.Size = Size(90, 22)
            self._nud_manual_offset.Minimum = System.Decimal(-99999)
            self._nud_manual_offset.Maximum = System.Decimal(99999)
            self._nud_manual_offset.DecimalPlaces = 1
            self._nud_manual_offset.Value = System.Decimal(0)
            grp_timing.Controls.Add(self._nud_manual_offset)

            lbl_ms = Label()
            lbl_ms.Text = "ms   (positive = shift timestamps later)"
            lbl_ms.ForeColor = Color.DimGray
            lbl_ms.Location = Point(226, 46)
            lbl_ms.Size = Size(320, 20)
            grp_timing.Controls.Add(lbl_ms)

            y += 82

        # ---- Status label -------------------------------------------
        self.lbl_status = Label()
        self.lbl_status.Text = "Loading light curve\u2026"
        self.lbl_status.ForeColor = Color.Gray
        self.lbl_status.Location = Point(12, y + 12)
        self.lbl_status.Size = Size(680, 20)
        self.Controls.Add(self.lbl_status)

        # ---- Bottom buttons -----------------------------------------
        self.btn_export = Button()
        self.btn_export.Text = "Export"
        self.btn_export.Location = Point(706, y + 6)
        self.btn_export.Size = Size(96, 32)
        self.btn_export.Enabled = False
        self.btn_export.Click += self._export_click
        self.Controls.Add(self.btn_export)
        self.AcceptButton = self.btn_export

        btn_close = Button()
        btn_close.Text = "Close"
        btn_close.Location = Point(814, y + 6)
        btn_close.Size = Size(80, 32)
        btn_close.Click += self._close_click
        self.Controls.Add(btn_close)
        self.CancelButton = btn_close

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def _load_and_prepare(self):
        """Load light curve, insert dropped readings, compute default trim."""
        try:
            frames, times, values = lcr.read_light_curve(self._lc_path)
        except Exception as ex:
            self.lbl_status.Text = "Error loading light curve: %s" % ex
            return

        if not frames:
            self.lbl_status.Text = "Light curve file contains no readable data."
            return

        # Median time step — get_observation_summary returns tdelta_median in ms
        try:
            summary = lcr.get_observation_summary(self._lc_path)
            tdelta_ms = summary.get('tdelta_median') if summary else None
            self._time_step_s = (
                tdelta_ms / 1000.0 if tdelta_ms else compute_median_step(times)
            )
        except Exception:
            self._time_step_s = compute_median_step(times)

        # Expand dropped readings
        self._exp_frames, self._exp_times, self._exp_values = (
            insert_dropped_readings(frames, times, values, self._time_step_s)
        )

        n_original = len(frames)
        n_expanded = len(self._exp_frames)
        n_inserted = n_expanded - n_original

        # D/R times from aota_report_data (used for trim and chart markers)
        self._d_time_s, self._r_time_s = self._extract_dr_times()

        # Auto-trim
        event_dur_s = 0.0
        if self._d_time_s is not None and self._r_time_s is not None:
            event_dur_s = max(0.0, self._r_time_s - self._d_time_s)

        left_idx, right_idx = compute_trim_window(
            self._exp_times,
            d_time_s=self._d_time_s,
            r_time_s=self._r_time_s,
            event_duration_s=event_dur_s,
        )

        # Configure NUDs (values are 0-based indices into _exp_frames)
        if n_expanded > 0:
            self.nud_first.Maximum = System.Decimal(n_expanded - 1)
            self.nud_last.Maximum = System.Decimal(n_expanded - 1)
            self._trim_updating = True
            try:
                self.nud_first.Value = System.Decimal(left_idx)
                self.nud_last.Value = System.Decimal(right_idx)
            finally:
                self._trim_updating = False
            self._update_frame_labels()

        self._draw_chart()
        self._update_trim_info()

        self.btn_export.Enabled = (n_expanded > 0)
        self.lbl_status.Text = (
            "%d frames loaded (%d original + %d inserted for gaps)."
            % (n_expanded, n_original, n_inserted)
        )

    def _extract_dr_times(self):
        """Return (d_time_s, r_time_s) from aota_report_data, or (None, None)."""
        data = self._aota_report_data
        if not data:
            return None, None
        d_time_s = None
        r_time_s = None
        try:
            d_h = int(data.get('d_hours') or 0)
            d_m = int(data.get('d_minutes') or 0)
            d_s = float(data.get('d_seconds') or 0.0)
            d_time_s = d_h * 3600.0 + d_m * 60.0 + d_s
        except (TypeError, ValueError):
            pass
        try:
            r_h = int(data.get('r_hours') or 0)
            r_m = int(data.get('r_minutes') or 0)
            r_s = float(data.get('r_seconds') or 0.0)
            r_time_s = r_h * 3600.0 + r_m * 60.0 + r_s
        except (TypeError, ValueError):
            pass
        return d_time_s, r_time_s

    # ------------------------------------------------------------------
    # Chart
    # ------------------------------------------------------------------

    def _draw_chart(self):
        """Invalidate the PictureBox to trigger a GDI+ repaint."""
        if self._chart is None:
            return
        self._chart.Invalidate()

    def _nearest_frame_to_time(self, time_s):
        """Return the frame number whose timestamp is closest to time_s."""
        best_frame = None
        best_diff = None
        for f, t in zip(self._exp_frames, self._exp_times):
            if t is None:
                continue
            diff = abs(to_seconds(t) - time_s)
            if best_diff is None or diff < best_diff:
                best_diff = diff
                best_frame = f
        return best_frame

    def _update_trim_strips(self):
        """Redraw the chart to reflect the current trim window."""
        if self._chart is not None:
            self._chart.Invalidate()

    def _chart_paint(self, sender, e):
        """GDI+ Paint handler — draws the light curve on the PictureBox."""
        g = e.Graphics
        g.Clear(Color.White)

        if not self._exp_frames or not self._exp_values:
            br = SolidBrush(Color.Gray)
            try:
                g.DrawString("No data loaded.", Font("Segoe UI", 9), br, 8.0, 8.0)
            finally:
                br.Dispose()
            return

        valid_vals = [v for v in self._exp_values
                      if v is not None and not _is_neg_zero(v)]
        if not valid_vals:
            return

        w = sender.ClientSize.Width
        h = sender.ClientSize.Height
        pad_l, pad_r, pad_t, pad_b = 5, 5, 5, 5
        pw = max(1, w - pad_l - pad_r)
        ph = max(1, h - pad_t - pad_b)

        x_min = float(self._exp_frames[0])
        x_max = float(self._exp_frames[-1])
        x_range = x_max - x_min if x_max > x_min else 1.0

        y_min_v = float(min(valid_vals))
        y_max_v = float(max(valid_vals))
        y_margin = (y_max_v - y_min_v) * 0.05 if y_max_v > y_min_v else 1.0
        y_lo = y_min_v - y_margin
        y_hi = y_max_v + y_margin
        y_range = y_hi - y_lo if y_hi > y_lo else 1.0

        drop_y_px = pad_t + ph - 4   # dropped markers near bottom edge

        def fx(frame):
            return int(pad_l + (float(frame) - x_min) / x_range * pw)

        def fy(val):
            return int(pad_t + (1.0 - (float(val) - y_lo) / y_range) * ph)

        # --- Trim shading (grey outside the selected window) ---
        n = len(self._exp_frames)
        first_idx = int(self.nud_first.Value)
        last_idx = int(self.nud_last.Value)
        if first_idx < n and last_idx < n:
            x_first = fx(self._exp_frames[first_idx])
            x_last = fx(self._exp_frames[last_idx])
            shade = SolidBrush(Color.FromArgb(45, 100, 100, 100))
            try:
                left_w = x_first - pad_l
                if left_w > 0:
                    g.FillRectangle(shade, pad_l, pad_t, left_w, ph)
                right_x = x_last
                right_w = (pad_l + pw) - right_x
                if right_w > 0:
                    g.FillRectangle(shade, right_x, pad_t, right_w, ph)
            finally:
                shade.Dispose()

        # --- D/R reference lines ---
        if self._d_time_s is not None:
            d_frame = self._nearest_frame_to_time(self._d_time_s)
            if d_frame is not None:
                dx = fx(d_frame)
                d_pen = Pen(Color.OrangeRed, 2)
                try:
                    g.DrawLine(d_pen, dx, pad_t, dx, pad_t + ph)
                finally:
                    d_pen.Dispose()

        if self._r_time_s is not None:
            r_frame = self._nearest_frame_to_time(self._r_time_s)
            if r_frame is not None:
                rx = fx(r_frame)
                r_pen = Pen(Color.CornflowerBlue, 2)
                try:
                    g.DrawLine(r_pen, rx, pad_t, rx, pad_t + ph)
                finally:
                    r_pen.Dispose()

        # --- Signal polyline + dropped-frame markers ---
        sig_pen = Pen(Color.CornflowerBlue, 1)
        drop_pen = Pen(Color.Red, 1)
        prev_pt = None
        try:
            for f, v in zip(self._exp_frames, self._exp_values):
                px = fx(f)
                if v is None or _is_neg_zero(v):
                    sz = 3
                    g.DrawLine(drop_pen, px - sz, drop_y_px - sz, px + sz, drop_y_px + sz)
                    g.DrawLine(drop_pen, px + sz, drop_y_px - sz, px - sz, drop_y_px + sz)
                    prev_pt = None
                else:
                    py = fy(v)
                    if prev_pt is not None:
                        g.DrawLine(sig_pen, prev_pt[0], prev_pt[1], px, py)
                    prev_pt = (px, py)
        finally:
            sig_pen.Dispose()
            drop_pen.Dispose()

    # ------------------------------------------------------------------
    # Trim window handlers
    # ------------------------------------------------------------------

    def _update_frame_labels(self):
        """Update the 'frame XXXX' labels below the NUDs."""
        n = len(self._exp_frames)
        if n == 0:
            self.lbl_first_frame.Text = ''
            self.lbl_last_frame.Text = ''
            return
        first_idx = int(self.nud_first.Value)
        last_idx = int(self.nud_last.Value)
        if 0 <= first_idx < n:
            self.lbl_first_frame.Text = 'frame %d' % self._exp_frames[first_idx]
        if 0 <= last_idx < n:
            self.lbl_last_frame.Text = 'frame %d' % self._exp_frames[last_idx]

    def _update_trim_info(self):
        """Refresh the duration / frame-count label."""
        first_idx = int(self.nud_first.Value)
        last_idx = int(self.nud_last.Value)
        n = len(self._exp_frames)
        if n == 0 or first_idx >= n or last_idx >= n or last_idx < first_idx:
            self.lbl_trim_info.Text = "Duration: \u2014"
            return

        t_first = self._exp_times[first_idx]
        t_last = self._exp_times[last_idx]
        if t_first is not None and t_last is not None:
            duration_s = (t_last - t_first).total_seconds()
        elif self._time_step_s:
            duration_s = (last_idx - first_idx) * self._time_step_s
        else:
            duration_s = 0.0

        count = last_idx - first_idx + 1
        self.lbl_trim_info.Text = "Duration: %.2f s  (%d frames)" % (duration_s, count)

    def _trim_changed(self, sender, e):
        """Handle first/last frame NUD change — clamp range and refresh UI."""
        if self._trim_updating:
            return
        n = len(self._exp_frames)
        if n == 0:
            return

        first_idx = int(self.nud_first.Value)
        last_idx = int(self.nud_last.Value)

        # Clamp so first <= last
        if last_idx < first_idx:
            self._trim_updating = True
            try:
                if sender is self.nud_last:
                    self.nud_last.Value = self.nud_first.Value
                else:
                    self.nud_first.Value = self.nud_last.Value
            finally:
                self._trim_updating = False

        self._update_frame_labels()
        self._update_trim_strips()
        self._update_trim_info()

    def _auto_trim_click(self, sender, e):
        """Re-apply the automatic trim window centred on the event."""
        if not self._exp_times:
            return
        event_dur_s = 0.0
        if self._d_time_s is not None and self._r_time_s is not None:
            event_dur_s = max(0.0, self._r_time_s - self._d_time_s)
        left_idx, right_idx = compute_trim_window(
            self._exp_times,
            d_time_s=self._d_time_s,
            r_time_s=self._r_time_s,
            event_duration_s=event_dur_s,
        )
        self._trim_updating = True
        try:
            self.nud_first.Value = System.Decimal(left_idx)
            self.nud_last.Value = System.Decimal(right_idx)
        finally:
            self._trim_updating = False
        self._update_frame_labels()
        self._update_trim_strips()
        self._update_trim_info()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_click(self, sender, e):
        """Validate inputs, build lines, and write .dat to all destinations."""
        first_idx = int(self.nud_first.Value)
        last_idx = int(self.nud_last.Value)
        n = len(self._exp_frames)

        if n == 0 or first_idx >= n or last_idx >= n or last_idx < first_idx:
            MessageBox.Show(
                "Invalid trim window. Please select a valid frame range.",
                "Export Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning,
            )
            return

        trimmed_values = self._exp_values[first_idx:last_idx + 1]
        trimmed_times = self._exp_times[first_idx:last_idx + 1]

        initial_time_dt = trimmed_times[0]
        last_time_dt = trimmed_times[-1]
        if initial_time_dt is None or last_time_dt is None:
            MessageBox.Show(
                "Cannot export: first or last trimmed frame has no timestamp.",
                "Export Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning,
            )
            return

        delta_time_s = (last_time_dt - initial_time_dt).total_seconds()

        # Event date
        event_date = ''
        if self._event:
            event_date = str(getattr(self._event, 'event_date', '') or '')
        if not event_date:
            event_date = '1900-01-01'

        # Asteroid number and name (strip '(number) ' prefix from object_name)
        obj_no = str(getattr(self._event, 'object_no', '') or '') if self._event else ''
        raw_name = str(getattr(self._event, 'object_name', '') or '') if self._event else ''
        if raw_name.startswith('(') and ') ' in raw_name:
            raw_name = raw_name[raw_name.index(') ') + 2:]

        # Observer info from config
        observer_name = ''
        reports_folder = ''
        if self._config:
            try:
                observer_name = self._config.get_observer_name() or ''
            except Exception:
                pass
            try:
                reports_folder = self._config.get_reports_folder() or ''
            except Exception:
                pass

        lat = float(getattr(self._event, 'latitude', 0.0) or 0.0) if self._event else 0.0
        lon = float(getattr(self._event, 'longitude', 0.0) or 0.0) if self._event else 0.0
        elev = float(getattr(self._event, 'elevation', 0) or 0) if self._event else 0.0

        # Star catalog IDs (from user-editable TextBoxes)
        ucac4 = self.txt_ucac4.Text.strip()
        tycho2 = self.txt_tycho2.Text.strip()
        hipparcos = self.txt_hip.Text.strip()

        try:
            # Compute timing correction
            timing_correction_s = 0.0
            if self._timing_data is None:
                # Standalone path: read from manual panel
                if (self._chk_already_corrected is None
                        or not self._chk_already_corrected.Checked):
                    if self._nud_manual_offset is not None:
                        timing_correction_s = (
                            float(self._nud_manual_offset.Value) / 1000.0
                        )
            elif self._timing_data.get('lc_timestamps_corrected') is False:
                timing_correction_s = float(
                    self._timing_data.get('net_correction_s') or 0.0
                )

            written = export_all_copies(
                event_date=event_date,
                initial_time_dt=initial_time_dt,
                delta_time_s=delta_time_s,
                num_readings=len(trimmed_values),
                ucac4=ucac4,
                tycho2=tycho2,
                hipparcos=hipparcos,
                lat_decimal=lat,
                lon_decimal=lon,
                altitude_m=elev,
                observer_name=observer_name,
                asteroid_number=obj_no,
                asteroid_name=raw_name,
                expanded_values=trimmed_values,
                reports_folder=reports_folder,
                observation_folder=self._observation_folder,
                timing_correction_s=timing_correction_s,
            )
        except Exception as ex:
            MessageBox.Show(
                "Export failed:\n\n%s" % ex,
                "Export Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error,
            )
            return

        paths_text = '\n'.join(written)
        MessageBox.Show(
            "VizieR .dat file written to %d location(s):\n\n%s" % (len(written), paths_text),
            "Export Complete",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information,
        )
        self.lbl_status.Text = "Exported %d cop%s." % (
            len(written), 'y' if len(written) == 1 else 'ies')

    def _on_standalone_timing_changed(self, sender, e):
        """Disable the manual offset NUD when 'already corrected' is checked."""
        if self._nud_manual_offset is not None and self._chk_already_corrected is not None:
            self._nud_manual_offset.Enabled = not self._chk_already_corrected.Checked

    def _close_click(self, sender, e):
        self.Close()
