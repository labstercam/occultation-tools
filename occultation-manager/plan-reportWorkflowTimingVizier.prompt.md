# Plan: Report Workflow — Timestamp Adjustments & VizieR Integration

## Context

This plan extends the Report workflow to handle timestamp corrections (NTP offset, camera acquisition delay) explicitly, and integrates VizieR light curve export into the flow.

---

## How PyOTE Handles Timing Corrections (from source review)

Understanding PyOTE's model is important because OM must be consistent with it for users who use both tools.

**Camera correction (`camCorrection`):**
- PyOTE does **not** have a direct camera delay input field in its main workflow
- When generating a VizieR .dat file, the user first loads the **NA (North American) Excel Asteroid Occultation Report Form** spreadsheet into PyOTE
- PyOTE reads the camera correction from cells **L45** (D-event correction) and **L47** (R-event correction) in the spreadsheet's "Corrections Calculations" tab — these are calculated from the sensor Y line by the spreadsheet
- PyOTE averages: `camCorrection = 0.5 * (dCamCorrection + rCamCorrection)`
- This averaged correction is applied **only to the VizieR .dat Date-line start timestamp** — not to the D/R event times in PyOTE's own output
- Rolling-shutter cameras using drift scan may have different D and R corrections; PyOTE's approach of averaging is acknowledged as an approximation in the source comments

**NTP correction:**
- PyOTE has **no direct NTP offset input**
- NTP corrections are expected to be handled entirely through the NA Excel report form's "Corrections Tables" tab
- PyOTE's printed warning states: *"If you use the North American Excel Spreadsheet report, all times will be properly corrected for camera delay. For other users worldwide, use the appropriate corrections documented in the North American Spreadsheet report form."*
- There is no `ntpCorrection` or equivalent field anywhere in PyOTE's VizieR workflow

**Implication for OM:**
- OM's plan to apply `camCorrection` only to the VizieR .dat start timestamp is consistent with what PyOTE does
- PyOTE users who also use OM for reporting don't enter corrections into PyOTE itself — corrections come from the NA spreadsheet. OM will need to fill a similar role for TT/SODIS reporters who don't use the NA spreadsheet
- The NTP offset is never visible in PyOTE's VizieR output; OM's §6 acknowledgement approach (user confirms it was applied in Tangra) is the only viable path

---

## Scope: Which Workflows Need OM Timestamp Handling?

The tools in use, the correction metadata available, and the existing correction ecosystems differ significantly by report type. This determines where OM's correction workflow adds genuine value vs where it would duplicate or conflict with existing tooling.

### Tool matrix

| Light curve source | Camera delay in CSV? | NTP in CSV? | Notes |
|---|---|---|---|
| Tangra CSV | ✅ yes (stores value entered by user) | ❌ no | Primary tool for NZ/AU PC disciplined timing |
| PyMovie CSV | ❌ no (confirmed: version, source path, aperture metadata, extraction method — no delay field) | ❌ no | Used with NA Excel spreadsheet |
| LiMovie CSV | ❌ no | ❌ no | Legacy; no metadata |
| R-OTE / PyOTE metrics | ❌ no | ❌ no | D/R times only, no raw timestamps |

### Report type matrix

| Report type | Corrections handled by? | D/R analysis tool | VizieR path |
|---|---|---|---|
| **TT (Trans-Tasman)** | Nothing currently — OM gap | AOTA or PyOTE | OM VizierExportDialog (new) |
| **NA (North American)** | NA Excel spreadsheet → PyOTE reads L45/L47 | PyOTE | PyOTE built-in VizieR export |
| **SODIS** | Nothing currently — OM gap | varies | OM VizierExportDialog (new) |

> **Q3 note:** Some TT reporters also use PyOTE for D/R analysis and may have used the NA Excel Spreadsheet alongside it. If a TT reporter populated the NA spreadsheet's "Corrections Calculations" tab, their corrections are already handled via PyOTE's L45/L47 read — the same closed-loop path as NA reporters. For these users, OM's §5 Timing should display a caution: *"If you used the NA Excel Spreadsheet with PyOTE, timing corrections are already handled by that spreadsheet — do not also apply them here."*

### Scope by Timing Method

OM timestamps corrections are scoped by **recording/timing method**, not by report type. The primary supported methods are:

| Timing method | Status | §5 Timing behaviour |
|---|---|---|
| **NTP / GPS-disciplined PC clock** — CMOS camera + Tangra/AOTA | **Phase 1 primary** | Full correction UI |
| **GPS flash (dumb/Camilleri)** — Tangra/AOTA | **Phase 2 primary** | Correction UI (in development) |
| PyOTE/PyMovie + smart GPS flash or NA spreadsheet | Report generation only | Read-only note |
| Analog video / VTI | Report generation only | Read-only note |
| LiMovie | Report generation only | Read-only note |

**Decision — scope by timing method:**
- §5 Timing shows the **full correction UI** only when the camera's timing method is NTP (Phase 1) or GPS flash dumb (Phase 2)
- For all other methods, §5 shows a read-only note: *"Timing corrections are not applied by Occultation Manager for this method. Apply corrections in Tangra/PyOTE, PyMovie, or the NA reporting form before generating this report."*
- The camera config's `timing` field pre-selects the §5 method radio; the user can override it
- The **VizieR export dialog** is accessible for all report types regardless of timing method; for non-corrected recordings the user enters a manual offset or leaves it at 0
- NA reporters have a closed-loop correction path (NA Excel spreadsheet → PyOTE reads L45/L47) that OM must not disrupt. They fall into the "Report generation only" path and are directed to PyOTE's built-in VizieR export for .dat files

---

## Current Workflow (as-is)

```
Report click
  └─ LocationConfirmDialog       ← confirms lat/lon/elev, optional NTP analysis
  └─ ComprehensiveReportDialog   ← 5 sections:
        §1 Report type (NA / TT / SODIS)
        §2 Equipment (telescope + camera)
        §3 Observation result (Pos / Neg / Unsure)
        §4 Browse folder → select CSV / AOTA XML / AOTA Report / PyOTE metrics
        §5 Conditions + Timestamp Check (informational only — nothing is applied)
  └─ Report generators (na/tt/sodis) → Excel/text output
```

**Gaps:**
- NTP offset and camera acquisition delay are collected but never applied to D/R times or the report
- VizierExportDialog exists as a complete standalone dialog but is called from nowhere
- No record is kept of whether corrections were applied in external tools (Tangra/PyOTE)

---

## The Three Timestamp Correction Patterns

### Pattern A — Pre-correction in Tangra *(preferred for most users)*

User enters NTP offset and camera acquisition delay **inside Tangra** before generating the CSV. The light curve CSV is already time-correct. AOTA/PyOTE operates on corrected data. D/R times from AOTA/PyOTE are ready to use.

| Pros | Cons |
|---|---|
| Single source of truth | User must know correction values before Tangra analysis |
| VizieR .dat timestamps automatically correct | OM has no record of what was applied |
| No extra OM state to track | |

### Pattern B — Mid-pipeline via corrected CSV *(deferred — too much friction)*

OM reads the raw Tangra CSV, applies corrections, writes a corrected copy. User re-opens the corrected CSV in AOTA/PyOTE.

| Pros | Cons |
|---|---|
| OM controls and records corrections | **Two-pass workflow** — analysis friction |
| Corrected timestamps flow into VizieR .dat | Easy to forget to re-run AOTA/PyOTE on corrected file |
| | Highest risk of inconsistency if wrong CSV version used |

**Decision:** Defer Pattern B. Can be added later as "Export corrected CSV" button if demand arises.

### Pattern C+V — Post-analysis correction in OM *(fallback path)*

User runs AOTA/PyOTE on the raw CSV. OM applies correction offsets to D/R times when writing the report. VizierExportDialog receives the offset and applies it to the `.dat` Date-line start time.

| Pros | Cons |
|---|---|
| No disruption to existing AOTA/PyOTE workflow | VizieR .dat light curve timestamps are offset by ~50–150 ms |
| Minimal friction | Report D/R times differ from AOTA/PyOTE displayed values |
| OM records correction metadata | Correction must be explicitly confirmed each time |

---

## Recommended Workflow Design

Support both **Pattern A (acknowledged)** and **Pattern C+V** through the same UI section. The user's radio selection determines which path is taken.

### Revised Step Sequence

```
1. LocationConfirmDialog — EXTENDED (was: confirm location + optional NTP only)
     └─ Step 1a: Confirms lat/lon/elev  (existing)
     └─ Step 1b: NTP Analysis panel  ← NEW (NTP only; camera delay moved — see §6)
           └─ NTP Analysis: run analyser → ntp_offset_ms stored on event
     └─ Note: Camera acquisition delay is NOT calculated here.
              Y line is only known after recording — the user must view the
              recording to see where the target star fell on the sensor.
              Camera delay is entered and confirmed in §5 Timing.

2. [User records. After recording: views recording in Tangra to find star's Y line;
   notes it down for camera delay calculation in §5]

3. [For Pattern A (pre-correct in Tangra): user enters ntp_offset_ms from Step 1b
   AND calculates camera_delay_ms from Y line (using OM Delay Calculator or manually),
   enters both in Tangra, then re-runs analysis. For Pattern C+V: skip this step.]

4. [User runs Tangra / PyOTE / LiMovie, with or without corrections applied]

5. ComprehensiveReportDialog §1–§2 (existing)
     └─ Report type, telescope, camera

6. ComprehensiveReportDialog §3 Observation type (existing)

7. ComprehensiveReportDialog §4 File selection (existing)
     └─ Tangra CSV selected → shows acquisition_delay_ms from CSV header if present

8. NEW: ComprehensiveReportDialog §5 Timing
     └─ Camera config `timing` field pre-selects the method radio
     └─ If NTP: pre-filled ntp_offset_ms from Step 1b; Y line + camera_delay_ms entered here;
                user declares whether corrections applied; feeds timing_data to downstream
     └─ If GPS flash (dumb): placeholder UI — "GPS flash correction support coming in Phase 2"
     └─ If Other: read-only note — "Apply corrections in your analysis tool or NA form"

9. ComprehensiveReportDialog §6 Conditions (existing §5, renumbered)

10. Report generation (existing, receives timing_data)

11. REVISED: Post-generation dialog with VizieR export button
```

**Why separate NTP (Step 1b) from camera delay (§5 Timing)?**  
NTP analysis is time-sensitive — ideally run near the observation session start. Camera delay depends on the target star's Y line on the sensor, which is **only knowable after the recording exists** (the user must open the recording to find the aperture position). These two inputs therefore have different natural timing in the workflow:

- NTP offset: captured in LocationConfirmDialog before or just after the recording session
- Camera delay: entered in §5 Timing during the report workflow, after the user has viewed the recording

---

## Step 1b — NTP Analysis Panel (in LocationConfirmDialog)

This panel records the NTP offset for the observation session. **Camera acquisition delay is NOT collected here** — the target star's Y line position is only knowable after the recording exists. Camera delay is entered and confirmed in §5 Timing during the report workflow.

> **Q1 design correction:** The original plan positioned Step 1b as a "pre-analysis gate" where both NTP offset and camera delay would be calculated before opening Tangra. This is not feasible for camera delay because the Y line requires viewing the recording. Step 1b is therefore NTP-only. The camera delay Y line NUD and Delay Calculator button live in §5 Timing instead.

```
┌─ NTP Analysis (pre-observation) ───────────────────────────────────────────┐
│  Run before or during your recording session to measure PC clock offset.   │
│                                                                             │
│  NTP Analysis                                                               │
│    [ Run NTP Analysis... ]    Result: −12.3 ms  ✓  (run at 14:22 UTC)      │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────         │
│  ℹ  Camera acquisition delay is calculated in §5 Timing (after recording)  │
│     You will need the target star's Y line position from the recording.    │
└────────────────────────────────────────────────────────────────────────────┘
```

**Design notes:**
- Result stored on the event object: `event.ntp_analysis_result` — the full dict returned by `ntp_analysis_core.estimate_offset_at_time()`. Use `event.ntp_analysis_result['best_offset'] * 1000.0` to get `ntp_offset_ms`. Confirmed keys include: `best_offset` (s), `u_expanded` (s, 95%), `gap_before_s`, `active_server_at_T`, `mean_delay_near_T`, `server_location_note`, `note`. (camera delay NOT set here)
- Panel is shown when the camera's `timing` field = NTP, GPS PPS, or GPS NMEA (all discipline the PC clock via NTP software — identical workflow); hidden for GPS flash and other methods
- Y line NUD + Delay Calculator button appear in §5 Timing after file selection
- For Pattern A: user notes the NTP offset from this panel, views the recording to find the Y line, calculates camera delay in §5, then enters both values in Tangra before (re-)running the analysis

---

## §5 Timing Section — UI Design (in ComprehensiveReportDialog)

The camera config's `timing` field pre-selects the method radio. The correction detail panel below the radios changes based on the selection.

**What Tangra stores in the CSV:** camera acquisition delay only. The NTP offset is entered in Tangra but is NOT written to the CSV. This has two consequences:
- Camera delay: OM can **auto-verify** by comparing the CSV value against the §5 calculated value
- NTP offset: OM has **no way to detect** whether it was applied — the user must explicitly acknowledge it

```
┌─ 5. Timing ────────────────────────────────────────────────────────────────┐
│                                                                             │
│  Timing method:  ● NTP / GPS-disciplined clock  ○ GPS flash (dumb)  ○ Other │
│                                                                             │
│ ── NTP panel (shown when NTP selected) ────────────────────────────────── │
│  Camera acquisition delay                                                   │
│    Calibration run: [ 816x822 / 1×1 / RAW16 — 2026-03-12 (A)  ▼ ]        │
│    Target Y line:   [ 412  ▲▼ ]    Calculated delay: 47.3 ms               │
│    Tangra CSV reports: 47.1 ms  ✓  close match — delay was applied         │
│    Status:  ● Applied in Tangra — confirmed by CSV value    (auto-detected) │
│             ○ Not yet applied — apply to D/R times now                      │
│             ○ Not applicable                                                 │
│                                                                             │
│  NTP correction  (−12.3 ms, from pre-observation NTP run)                  │
│    ⚠  Not stored in Tangra CSV — cannot be verified automatically          │
│    Status:  ● Applied in Tangra — I entered this value before analysing     │
│             ○ Not yet applied — apply to D/R times now                      │
│             ○ No NTP data available                                          │
│                                                                             │
│  ─────────────────────────────────────────────────────────────────         │
│  Net adjustment to D/R:  +59.6 ms                                           │
│  D  10:44:45.200  →  10:44:45.260       R  10:44:47.200  →  10:44:47.260   │
│                                                                             │
│  Light curve timestamps:  ● Already corrected    ○ Not yet corrected       │
│    ⚠  VizieR .dat will apply +59.6 ms offset to the start time             │
│                                                                             │
│ ── GPS flash (dumb) panel (shown when GPS flash selected) ─────────────── │
│  ⓘ GPS flash (Camilleri method) correction support is planned for Phase 2. │
│     The flash overlay delay measurement is performed in the                 │
│     gps-timing-analysis tool. Corrections will be integrated here in a     │
│     future release.                                                         │
│                                                                             │
│ ── Other panel (shown when Other selected) ────────────────────────────── │
│  ⓘ Timing corrections are not applied by Occultation Manager for this      │
│     method. Apply corrections in Tangra/PyOTE, PyMovie, or the NA          │
│     reporting form before generating this report.                           │
└──────────────────────────────────────────────────────────────────────────── ┘
```

**Behaviour rules:**
- Method radio is pre-selected from the camera config's `timing` field; user can change it
- **NTP panel** — Camera delay auto-detection (Tangra CSV):
  - CSV value ≠ 0 and matches calculated value within 5 ms → auto-select "Applied in Tangra — confirmed"
  - CSV value = 0 or absent → auto-select "Not yet applied"
  - CSV value ≠ 0 but discrepancy > 5 ms → yellow warning, leave unselected, require manual choice
- **NTP panel** — NTP offset: always requires explicit user acknowledgement (not stored in Tangra CSV)
- If `camera_delay_applied = True` and `ntp_applied = True`, net correction = 0, D/R times unchanged
- If either is `False`, OM adjusts D/R times in the report (and .dat start time if VizieR export follows)
- VizieR .dat note only displayed when `lc_timestamps_corrected = False` and net offset ≠ 0
- Net adjustment row only shown when D/R times are available (AOTA/PyOTE file selected)
- **GPS flash (dumb) panel**: shows informational placeholder only — no correction values collected; `timing_data` records `timing_method = 'GPS_dumb'` and `net_correction_s = 0.0`
- **Other panel**: no correction values collected; `timing_data` records `timing_method = 'other'` and `net_correction_s = 0.0`; report generators make no D/R adjustments

---

## `timing_data` Dict — New Data Structure

Flows from §5 Timing into report generators and VizierExportDialog:

```python
timing_data = {
    'timing_method': 'NTP',             # 'NTP' | 'GPS_dumb' | 'other'
                                        # 'NTP' covers plain NTP, GPS PPS, and GPS NMEA —
                                        # all discipline the PC clock via NTP software; identical workflow
    'camera_delay_ms': 47.3,            # NTP only: calculated from Y line via Delay Calculator
    'camera_delay_y_line': 412,         # NTP only: sensor Y line used for calculation
    'calib_run_id': None,               # NTP only: UUID/id of the matched line_delay_calibrations run
    'ntp_offset_ms': -12.3,             # NTP only: from event.ntp_analysis_result['best_offset']*1000
    'camera_delay_applied': True,       # NTP only: True => delay already applied in Tangra CSV
    'ntp_applied': True,                # NTP only: True => NTP offset applied in Tangra before analysis
    'net_correction_s': 0.0,            # NTP: sum of unapplied corrections; GPS_dumb/other: always 0.0
    'lc_timestamps_corrected': True     # NTP: True only when BOTH applied; GPS_dumb/other: None (unknown)
}
```

**NTP path:** report generators apply `net_correction_s` to D/R times; non-zero only when at least one correction is unapplied.  
**GPS flash (dumb) and Other paths:** `net_correction_s = 0.0`; report generators make no D/R adjustments; `lc_timestamps_corrected = None` signals to VizierExportDialog that correction state is unknown.  
**VizierExportDialog:** applies `net_correction_s` to the `.dat` Date-line start time if `lc_timestamps_corrected = False`. If `None`, show the minimal timing acknowledgement panel (user declares state manually).

> **Phase 2 note:** GPS flash (dumb/Camilleri) produces a single combined overlay delay measurement (NTP offset + camera acquisition delay together). When Phase 2 is implemented, `timing_data` will be extended with `gps_flash_overlay_delay_ms` and `gps_flash_delay_applied` fields in place of the NTP-specific fields above.

---

## Camera Config Change

**No change to camera config schema is needed.** The calibration data infrastructure already exists.

`config.py` already maintains a separate `line_delay_calibrations` table (a list keyed by `camera_id`) that stores one entry per calibration run, capturing the exact camera settings under which the measurement was made:

```
line_delay_calibrations[]:
    camera_id       ← foreign key to cameras[]
    camera_area     ← ROI frame size e.g. '816x822' (binned pixels)
    binning         ← '1', '2', etc.
    tilt            ← ROI Y offset (unbinned pixels)
    pan             ← ROI X offset (unbinned pixels)
    colour_space    ← e.g. 'RAW16'
    per_line_delay  ← ms/line  ← used by the Delay Calculator
    line_0_delay    ← ms (delay at Y line 0 for this config)
    label           ← user's run label, e.g. 'A', 'B', 'C'
    run_datetime    ← ISO-8601 UTC of when the calibration was recorded
    notes           ← free text
```

This table already correctly models the fact that `per_line_delay` varies by camera settings (ROI, binning, colour space) — each calibration run captures the settings it was measured under.

**What §5 Timing's Delay Calculator must do:**

1. Identify the active camera from the event
2. Retrieve `line_delay_calibrations` for that `camera_id`
3. Match the run whose `camera_area`, `binning`, and `colour_space` match the settings used for THIS recording. These come from the **SharpCap `.CameraSettings` file** in the same folder as the Tangra CSV — filename pattern `*Z_.CameraSettings`; read `Capture Area`, `Binning`, and `Colour Space` by key name (the section header `[Camera Name]` gives the camera model). If multiple `.CameraSettings` files exist in the folder, pick the one whose `StartCapture` timestamp is closest to the Tangra CSV recording time. If no file is found, show all calibration runs for the camera and require manual selection.
4. Use the matched run's `per_line_delay` × Y_line + `line_0_delay` to compute `camera_delay_ms`

**UI for calibration run selection in §5 Timing:**

- Settings come from the SharpCap `.CameraSettings` file in the same folder as the Tangra CSV (see calibration run matching above)
- If a unique matching calibration run exists for the recording's settings → auto-select and pre-fill
- If multiple runs match (same settings, different dates) → show a dropdown ordered by `run_datetime` descending; default to most recent
- If no run matches → warn "No calibration found for these camera settings. Enter delay manually or run the LED calibration."
- If no `.CameraSettings` file found in the folder → show all runs for the camera with a note "No SharpCap settings file found — select manually"
- User can always override with a manual `camera_delay_ms` entry

**The per-event `camera_delay_ms` in `timing_data`** is freshly calculated for each event's specific Y line using the selected calibration run — it is not stored in the camera record.

---

## VizieR Export Integration Points

### Post-report (primary path)

Replace the current success/failure MessageBox with a richer dialog:

```
┌─ Report Generated ──────────────────────────────────────────────────────────┐
│  ✓ Report saved: data/reports/(165690)_20241128_TT.xlsx                     │
│                                                                             │
│  [ Open Report ]   [ Export VizieR Light Curve (.dat) ]   [ Close ]        │
└──────────────────────────────────────────────────────────────────────────────┘
```

- "Export VizieR Light Curve" launches `VizierExportDialog` with all context pre-populated
- Button is only enabled if a light curve CSV was selected in §4
- `aota_report_data` passed contains already-corrected D/R times
- `timing_data` passed so VizierExportDialog can compensate the .dat start timestamp if needed

### Standalone (secondary path)

`Tools → Export VizieR Light Curve…`

- Opens a FolderBrowserDialog first
- Scans selected folder for CSV + AOTA report / PyOTE metrics files
- Launches VizierExportDialog without a full report workflow
- No event must be pre-selected in the main grid (or if one is, it is used as context)
- **No `timing_data` is pre-populated.** VizierExportDialog shows a minimal timing acknowledgement panel:
  ```
  ┌─ Timing ────────────────────────────────────────────────────────────────┐
  │  ☐  Light curve timestamps are already corrected                        │
  │     (NTP offset + camera acquisition delay applied in source)           │
  │  Net timing offset to apply:  [  0.0  ] ms  (0 = timestamps as-is)     │
  └─────────────────────────────────────────────────────────────────────────┘
  ```
  This ensures even the standalone path records whether corrections were applied before the .dat file is generated.
- **Parameter naming note:** The offset parameter in `export_vizier_dat` should be named `timing_correction_s` (not `camera_correction_s` — the correction may combine both NTP and camera delay components).

---

## Risk Summary

| Chosen pattern | D/R times in report | VizieR .dat timestamps | Workflow friction | OM records correction |
|---|---|---|---|---|
| A + acknowledgement | ✅ correct (unchanged) | ✅ correct | Minimal (one radio click) | ✅ yes |
| C+V (OM post-corrects) | ✅ correct | ⚠ offset by ~50–150 ms | Minimal | ✅ yes |
| Nothing (current state) | ❌ uncorrected | ❌ uncorrected | None | ❌ no |

---

## Implementation Steps

1. **Camera config schema**: no changes needed — `line_delay_calibrations` table already exists in `config.py` with per-settings fields (`camera_area`, `binning`, `colour_space`, `per_line_delay`, `line_0_delay`). Ensure `equipment_dialogs.py` camera manager exposes existing calibration runs for the selected camera (read-only view; calibration runs are added by the LED calibration tool, not manually).
2. **Step 1b NTP Analysis panel**: add to `LocationConfirmDialog`; NTP analyser only; stores `event.ntp_offset_ms`; camera delay calculation moved to §5
3. **`timing_data` dict**: define structure with `camera_delay_applied` / `ntp_applied` (NOT a single `applied_in_source`) and `calib_run_id`; implement `build_timing_data()` helper in a new **`timing_utils.py`** module (not in `main_gui.py`)
4. **§5 Timing section**: add to `comprehensive_report_dialog.py` between file selection and conditions; includes Y line NUD + calibration run selector (auto-matched from `line_delay_calibrations` by camera settings) + Delay Calculator for `camera_delay_ms`; pre-fills `ntp_offset_ms` from event; produces final `timing_data` with `camera_delay_applied`, `ntp_applied`, `net_correction_s`, `lc_timestamps_corrected`
5. **Report generators**: accept `timing_data` param; apply `net_correction_s` to D/R times when `lc_timestamps_corrected = False`. **TT report only:** write `timing_data['net_correction_s']` (in seconds) to the `CAMERA_DELAY_CORRECTION` cell (currently written from `tangra_data['acquisition_delay']`) so the archived report reflects the actual net OM correction applied.
6. **Post-report dialog**: replace MessageBox with a Form that includes "Export VizieR Light Curve" button; passes full context to `VizierExportDialog`
7. **Standalone menu item**: add `Tools → Export VizieR Light Curve…` to `main_gui.py` menu; implement folder-browse then launch `VizierExportDialog` with minimal timing panel (no pre-filled `timing_data`)
8. **VizierExportDialog + `export_vizier_dat`**: accept optional `timing_data` param; apply `net_correction_s` to Date-line start time if `lc_timestamps_corrected = False`; **rename `camera_correction_s` parameter to `timing_correction_s`** in `export_vizier_dat` stub — the offset may combine NTP and camera delay components

---

## Out of Scope / Phase 2

### Phase 2 — Primary (planned)

- **GPS flash (dumb/Camilleri method):** Records a GPS flash in the same video as the target star. Tangra extracts both the target light curve and the flash signal; Python post-processing in the gps-timing-analysis module measures the overlay delay (the combined NTP offset + camera acquisition delay in a single value). Implementation adds the "GPS flash (dumb)" path to §5 Timing with: flash overlay delay entry, Applied/Not yet applied status, and `gps_flash_overlay_delay_ms` in `timing_data`. Python code already exists in the gps-timing-analysis module.

### Report generation only (no OM timing corrections)

These recording/analysis methods are supported for report generation, but **no timing corrections are applied by OM**. The user is responsible for applying corrections in their analysis tools or the NA reporting form before generting the report.

- **PyOTE/PyMovie users** (with or without smart GPS flash log analysis, or NA Excel spreadsheet): corrections belong in PyMovie/PyOTE or the NA form. Smart GPS flashers (Aart's timer, StampOfApproval, IOTA-GFT) generate independent per-frame timestamps via PyOTE's flash-log path — no OM corrections possible or needed.
- **Analog video / VTI recordings**: corrections belong in AOTA, PyOTE, or the NA reporting form.
- **LiMovie CSV**: no timing metadata available; corrections must be manual in the analysis tool.

### Deferred

- Pattern B (mid-pipeline corrected CSV export) — add later as optional button in §5 if user demand arises
