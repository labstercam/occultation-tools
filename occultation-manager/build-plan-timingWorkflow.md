# Build Plan: Timing Corrections & VizieR Integration

**Design reference:** `plan-reportWorkflowTimingVizier.prompt.md`  
**Branch:** `vizier-light-curves`  
**Done when:** End-to-end run on a real event matches manual processing.

---

## What Already Exists (Do Not Re-Build)

| Item | Location | Notes |
|---|---|---|
| `LineDelayCalculatorDialog` | `line_delay_dialogs.py:277` | Standalone dialog: camera + calibration run dropdown + Y line input → `_current_delay` float |
| `line_delay_calibrations` table | `config.py:700` | Per-settings calibration runs keyed by `camera_id`; fields: `camera_area`, `binning`, `colour_space`, `per_line_delay`, `line_0_delay`, `tilt`, `pan`, `run_datetime`, `label` |
| NTP analysis in `LocationConfirmDialog` | `gui_dialogs.py:1748` | Already runs analysis; result stored via `get_ntp_analysis_result()` |
| `event.ntp_analysis_result` | `main_gui.py:1992` | Already populated from location dialog |
| `acquisition_delay` in Tangra CSV | `light_curves_iron.py:92` | Already parsed and present in `tangra_data['acquisition_delay']` (ms, float or None) |
| `_d_time_seconds` / `_r_time_seconds` | `comprehensive_report_dialog.py:64` | Already populated from AOTA/AOTA Report/PyOTE at file selection (§4) |
| `VizierExportDialog` | `vizier_export_dialog.py:56` | Complete; accepts `lc_path`, `event`, `config`, `theme_manager`, `observation_folder`, `aota_report_data` |
| `export_vizier_dat` | `vizier_export.py:549` | Complete; has `camera_correction_s` param (to be renamed) |
| Report generators (NA, TT, SODIS) | `na/tt/sodis_report_*.py` | Generate reports; currently receive `tangra_data` and `aota_report_data` |
| Section numbers in dialog | `comprehensive_report_dialog.py:438` | Visual labels only — `grp_conditions.Text = "5. Conditions"` — safe to change |

---

## Phase 1 — NTP Timing Corrections + VizieR Wiring

**Scope:** NTP / GPS-disciplined PC clock recordings using Tangra + AOTA.  
**Not in Phase 1:** GPS flash dumb corrections (placeholder only), report-generation-only paths need no changes.

### Task 1 — Define `timing_data` dict and helper function

**File:** `timing_utils.py` (new file in `occultation-manager/python/`)  
**Depends on:** nothing  
**Deliverable:** A single function `build_timing_data(...)` that constructs the dict. Start simple — will be populated by Task 3.

```python
timing_data = {
    'timing_method': 'NTP',        # 'NTP' | 'GPS_dumb' | 'other'
    'camera_delay_ms': 0.0,        # from §5 Timing: per_line_delay × Y + line_0_delay
    'camera_delay_y_line': None,   # int Y line entered in §5
    'calib_run_id': None,          # UUID of matched line_delay_calibrations run
    'ntp_offset_ms': 0.0,          # from event.ntp_analysis_result['offset_ms'], or 0.0
    'camera_delay_applied': None,  # True/False/None — set by user in §5
    'ntp_applied': None,           # True/False/None — set by user in §5
    'net_correction_s': 0.0,       # sum of unapplied corrections in seconds (negative = shift earlier)
    'lc_timestamps_corrected': None  # True when both applied; False when either unapplied; None if other
}
```

**Notes:**
- `net_correction_s` is computed: sum of `camera_delay_ms` where not applied + `ntp_offset_ms` where not applied, converted to seconds
- `lc_timestamps_corrected = True` only when `camera_delay_applied = True` AND `ntp_applied = True`
- For `'GPS_dumb'` and `'other'`, all correction fields are None/0; `lc_timestamps_corrected = None`

---

### Task 2 — Extract NTP offset from existing `event.ntp_analysis_result`

**File:** `main_gui.py` (`generate_report_click`)  
**Depends on:** Task 1  
**Change:** After ComprehensiveReportDialog closes (line ~2010), read the NTP offset:

```python
ntp_offset_ms = 0.0
ntp_uncertainty_ms = 0.0
if event.ntp_analysis_result:
    ntp_offset_ms = float(event.ntp_analysis_result.get('best_offset', 0.0)) * 1000.0
    ntp_uncertainty_ms = float(event.ntp_analysis_result.get('u_expanded', 0.0)) * 1000.0
```

**Confirmed keys** (from `ntp_analysis_core.py:estimate_offset_at_time` docstring):

| Key | Type | Description |
|---|---|---|
| `best_offset` | float (s) | **The offset to use** — interpolated or extrapolated from loopstats |
| `u_expanded` | float (s) | Expanded uncertainty ~95% |
| `u_combined` | float (s) | Combined standard uncertainty k=1 |
| `gap_before_s` | float (s) | Age of closest loopstats record before event |
| `active_server_at_T` | str \| None | NTP server address active at event time |
| `mean_delay_near_T` | float (s) | Mean RTT of nearby peer records |
| `server_location_note` | str | How server location was resolved |
| `note` | str | Human-readable summary |

Note: the existing UI code already extracts and displays `best_offset × 1000` as ms (`gui_dialogs.py:2361`). The §5 Timing panel should show the same value with uncertainty.

---

### Task 3 — Add §5 Timing section to `ComprehensiveReportDialog`

**File:** `comprehensive_report_dialog.py`  
**Depends on:** Task 1  
**Section rename:** `grp_conditions.Text` changes from `"5. Conditions"` to `"6. Conditions"`.

**New GroupBox** inserted between §4 File Selection and §6 Conditions (currently §5):

```
┌─ 5. Timing ────────────────────────────────────────────────────────────────┐
│  Timing method:  ● NTP / GPS-disciplined  ○ GPS flash (dumb)  ○ Other     │
│                                                                             │
│ [NTP panel — shown when NTP selected]                                      │
│  Camera acquisition delay                                                   │
│    Calibration run: [ ComboBox — camera_area / binning / colour_space ▼ ] │
│    Target Y line:   [ NUD 0–4096 ]    Calculated delay: 47.3 ms            │
│    Tangra CSV:      47.1 ms  ✓  (auto-detected)                            │
│    Status:  ◉ Applied in Tangra — confirmed by CSV   ○ Not yet applied     │
│             ○ Not applicable                                                │
│                                                                             │
│  NTP correction  (−12.3 ms from NTP analysis)                              │
│    ⚠ Not stored in Tangra CSV                                              │
│    Status:  ◉ Applied in Tangra — I entered this value  ○ Not yet applied  │
│             ○ No NTP data                                                   │
│                                                                             │
│  Net adjustment to D/R:  +59.6 ms                                          │
│  D  10:44:45.200  →  10:44:45.260    R  10:44:47.200  →  10:44:47.260     │
│                                                                             │
│ [GPS flash (dumb) panel — shown when GPS flash selected]                   │
│  GPS flash correction is planned for Phase 2.                              │
│                                                                             │
│ [Other panel — shown when Other selected]                                  │
│  Apply corrections in your analysis tool before generating this report.   │
└────────────────────────────────────────────────────────────────────────────┘
```

**Implementation details:**

**Method radio pre-selection:**
- Read `camera_id` from the already-selected camera in §2
- Load camera config; read `timing` field
- Map `timing` value → radio: NTP/GPS PPS/GPS NMEA → NTP radio; otherwise → Other radio

**Calibration run ComboBox (NTP panel only):**
- On CSV selection change (fires `_update_tangra_preview`), also scan for a SharpCap `.CameraSettings` file in the same folder
- File pattern: `*Z_.CameraSettings` (timestamp prefix varies; there may be one file or several — pick the one whose `StartCapture` timestamp is closest to the Tangra CSV recording time)
- Parse as INI / key=value; section `[Camera Name]` gives the camera model; read fields by name (not position-dependent — different cameras may have different fields):
  - `Capture Area` → `camera_area` string (e.g. `"816x822"`)
  - `Binning` → integer
  - `Colour Space` → string (e.g. `"MONO16"`)
- Use these three values to filter `config.get_line_delay_calibrations(camera_id=...)` list
- Display matching runs as `"{camera_area} / {binning}× / {colour_space} — {run_datetime[:10]} ({label})"`
- If multiple matches: show all; pre-select the most recent
- If no match: show all runs for camera with `"⚠ No auto-match — select manually"` label
- If no `.CameraSettings` file found at all: show all runs with a note `"No SharpCap settings file found in this folder"`
- On calibration run selection change: recalculate delay if Y line is set

**Y line NUD:**
- Range 0–4096, integer; `ValueChanged` event recalculates delay
- Formula: `delay_ms = run['per_line_delay'] * y_line + run['line_0_delay']`
- Display result inline next to NUD

**Camera delay auto-detection (fires when §4 CSV selection changes):**
- Read `tangra_data['acquisition_delay']` (ms, already in `_update_tangra_preview`)
- Compare with calculated delay:
  - CSV value present and `abs(csv_val - calculated) <= 5.0` → auto-select "Applied in Tangra"
  - CSV value is 0 or None → auto-select "Not yet applied"
  - CSV value present but `abs(csv_val - calculated) > 5.0` → highlight warning text, leave unselected

**NTP row:**
- Pre-fill displayed `ntp_offset_ms` value from `event.ntp_analysis_result` if present; otherwise show "No NTP data available" and pre-select "No NTP data" radio
- No auto-detection — always requires explicit user choice

**Net adjustment display:**
- Recalculates whenever any radio changes
- Applies only when corresponding `_applied` flag is False
- Shows adjusted D/R times using `_d_time_seconds` / `_r_time_seconds` (already available in dialog)
- Net row hidden if both corrections are applied (net = 0) or if D/R times are not available

**New getter methods to add:**
```python
def get_timing_data(self):
    """Returns the fully-populated timing_data dict, or None if timing method is 'other'."""
```

---

### Task 4 — Pass `timing_data` through `generate_report_click`

**File:** `main_gui.py`  
**Depends on:** Tasks 2 and 3  

After `comprehensive_dialog.ShowDialog()` returns OK (around line 2010):

```python
timing_data = comprehensive_dialog.get_timing_data()
ntp_offset_ms = timing_data['ntp_offset_ms'] if timing_data else 0.0
```

Pass `timing_data` to `report_generator.generate_report(...)` — add as a new optional keyword argument: `timing_data=timing_data`.

---

### Task 5 — Apply `net_correction_s` in report generators

**Files:** `tt_report_openize.py`, `na_report_openize.py`, `sodis_report_text.py`  
**Depends on:** Task 4  

Each `generate_report(...)` method gains a `timing_data=None` keyword argument.

When `timing_data` is present and `timing_data['net_correction_s'] != 0.0`:
- Add `net_correction_s` to `d_seconds` and `r_seconds` before writing to report cells
- Clamp seconds to `[0.0, 60.0)` and carry over to minutes if needed

**TT report `CAMERA_DELAY_CORRECTION` cell:** When `timing_data` is passed, write `timing_data['net_correction_s']` (in seconds) to this cell instead of `tangra_data['acquisition_delay']`. This reflects the actual net correction OM applied, which is what matters for archival purposes.

---

### Task 6 — Rename `camera_correction_s` → `timing_correction_s` in `vizier_export.py`

**File:** `vizier_export.py`  
**Depends on:** nothing (safe standalone rename)  

- Rename parameter at line 564: `camera_correction_s=0.0` → `timing_correction_s=0.0`
- Update the two internal uses at lines 596–597 and 675
- Update the docstring at line 586
- Search for any callers of `export_vizier_dat` in the codebase and update their keyword arg names

```bash
# Find all callers:
grep -rn "camera_correction_s" occultation-manager/python/
```

---

### Task 7 — Wire `timing_data` into `VizierExportDialog`

**File:** `vizier_export_dialog.py`  
**Depends on:** Tasks 3 and 6  

Add `timing_data=None` to `__init__` signature:

```python
def __init__(self, lc_path, event, config, theme_manager,
             observation_folder, aota_report_data=None, timing_data=None):
```

In `_export_dat` (or wherever `export_vizier_dat` is called):
```python
correction_s = 0.0
if timing_data and timing_data.get('lc_timestamps_corrected') is False:
    correction_s = timing_data['net_correction_s']
elif timing_data is None or timing_data.get('lc_timestamps_corrected') is None:
    # standalone path: user entered manual offset — use self._manual_offset_ms / 1000.0
    correction_s = self._manual_offset_ms / 1000.0

export_vizier_dat(..., timing_correction_s=correction_s)
```

**Standalone path** (no `timing_data`): show a minimal panel in the dialog:
```
┌─ Timing ──────────────────────────────────────────────────────────────┐
│  ☐  Light curve timestamps are already corrected                      │
│     (NTP offset + camera delay applied in source)                     │
│  Additional offset:  [  0.0  ] ms     (positive = shift timestamps later) │
└───────────────────────────────────────────────────────────────────────┘
```
This panel shows when `timing_data is None`. When `timing_data` is passed from the report workflow, the panel is hidden and `net_correction_s` is used directly.

---

### Task 8 — Wire VizieR export into post-report dialog

**File:** `main_gui.py`  
**Depends on:** Task 7  

Replace the current `MessageBox.Show(success_msg, ...)` (around line 2420) with a WinForms `Form` containing three buttons:

```
┌─ Report Generated ───────────────────────────────────────────────┐
│  ✓ (165690)_20241128_TT.xlsx saved                               │
│                                                                  │
│  [ Open Report ]  [ Export VizieR .dat ]  [ Close ]             │
└──────────────────────────────────────────────────────────────────┘
```

- "Open Report" → `os.startfile(output_path)`
- "Export VizieR .dat" → `VizierExportDialog(lc_path=tangra_csv_path, ..., timing_data=timing_data).ShowDialog()`
  - Button only enabled when `tangra_csv_path is not None`
- "Close" → `dialog.Close()`

**Pass to VizierExportDialog:** `lc_path`, `event`, `config`, `theme_manager`, `observation_folder=selected_obs_folder`, `aota_report_data`, `timing_data`

---

### Task 9 — Add standalone `Tools → Export VizieR Light Curve…` menu item

**File:** `main_gui.py`  
**Depends on:** Task 7  

Add to the Tools menu (after "Camera Delay Calculator"):

```python
menu_tools.DropDownItems.Add(
    ToolStripMenuItem("Export VizieR Light Curve\u2026", None, self.open_vizier_export_click)
)
```

Handler `open_vizier_export_click`:
1. If an event is selected in the grid, use it; otherwise show file browser
2. Open `FolderBrowserDialog` — user selects the observation folder
3. Scan folder for CSV files (reuse `csv_files` scan logic from `comprehensive_report_dialog.py:663`)
4. If multiple CSVs found: show a simple ListBox picker
5. Launch `VizierExportDialog(lc_path=..., event=event, ..., timing_data=None)` — standalone path, shows manual timing panel

---

## Phase 1 — Task Summary and Dependencies

```
Task 1  build_timing_data() helper dict definition         ─────────────────────────────┐
Task 2  extract ntp_offset_ms from event.ntp_analysis_result  ──────────────┐           │
Task 3  §5 Timing section in ComprehensiveReportDialog          depends: 1   │           │
Task 4  pass timing_data through generate_report_click          depends: 2,3 │           │
Task 5  apply net_correction_s in report generators             depends: 4   │           │
Task 6  rename camera_correction_s → timing_correction_s    ─────────────────────────── │ ─┐
Task 7  timing_data in VizierExportDialog                       depends: 3,6             │  │
Task 8  post-report dialog with VizieR button                   depends: 4,7             │  │
Task 9  standalone Tools menu item                              depends: 7               │  │
```

Recommended build order: **1 → 2 → 6 → 3 → 4 → 5 → 7 → 8 → 9**

---

## Phase 1 — Exit Criteria

Phase 1 is complete when all of the following pass on a real NTP-timed CMOS recording:

1. **Pattern A (pre-corrected in Tangra):**
   - §5 Timing auto-detects camera delay from CSV → "Applied in Tangra" pre-selected
   - User confirms NTP was applied → "Applied in Tangra" selected
   - Net correction = 0; report D/R times match AOTA output unchanged
   - VizierExportDialog opens with `timing_correction_s = 0`; generated `.dat` timestamps match light curve

2. **Pattern C+V (corrections not applied in Tangra):**
   - §5 Timing auto-detects CSV delay = 0 → "Not yet applied" pre-selected
   - User confirms NTP not applied
   - Report D/R times are adjusted by net correction; values match manual calculation
   - VizierExportDialog applies same net offset to `.dat` start time

3. **Other timing method (e.g. PyOTE user):**
   - Camera `timing` field maps to Other radio
   - §5 shows read-only note; no correction values collected
   - Report D/R times pass through unchanged

4. **VizieR standalone path:**
   - `Tools → Export VizieR Light Curve…` opens dialog from any folder
   - Manual offset panel visible; entering a value shifts `.dat` start time
   - Leaving offset at 0 produces `.dat` matching light curve start exactly

---

## Phase 2 — GPS Flash Dumb (Camilleri Method)

**Prerequisite:** Phase 1 complete and validated.

### Overview

The dumb GPS flasher records a GPS flash event in the same video as the target star. The overlay delay (NTP offset + camera acquisition delay combined) is measured from the flash waveform using the Python processing code in `gps-timing-analysis`. Phase 2 replaces the Phase 1 placeholder panel with a functional workflow.

### Phase 2 Tasks (outline — detail to be expanded when Phase 1 is done)

| # | Task | File(s) |
|---|---|---|
| 2.1 | §5 GPS flash panel: flash overlay delay entry field, Applied/Not applied status | `comprehensive_report_dialog.py` |
| 2.2 | Extend `timing_data` with `gps_flash_overlay_delay_ms` + `gps_flash_delay_applied` | `main_gui.py` |
| 2.3 | Report generators: apply GPS flash net correction (same path as NTP `net_correction_s`) | `tt/na/sodis_report_*.py` |
| 2.4 | Link to `gps-timing-analysis` results: read overlay delay from a saved analysis file, or launch the analysis tool | TBD |
| 2.5 | VizieR export: GPS flash delay path (same `net_correction_s` mechanism as NTP) | `vizier_export_dialog.py` |

---

## Open Questions — Resolved

| # | Question | Resolution |
|---|---|---|
| OQ1 | Keys in `event.ntp_analysis_result`? | **`best_offset`** (float, seconds) is the offset; `u_expanded` is 95% uncertainty. See full key table in Task 2. |
| OQ2 | TT `CAMERA_DELAY_CORRECTION` cell: Tangra CSV value or net OM correction? | **Net OM correction** (`timing_data['net_correction_s']` in seconds). |
| OQ3 | `build_timing_data()` in `main_gui.py` or separate module? | **New `timing_utils.py`** in `occultation-manager/python/`. |
| OQ4 | How to match calibration run? CSV header? | **SharpCap `.CameraSettings` file** in same folder as the Tangra CSV. Read `Capture Area`, `Binning`, `Colour Space` by key name. Section header `[Camera Name]` gives camera model. See detail in Task 3. |
