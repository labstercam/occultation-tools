# Line Delay Calibration Integration Plan

## Overview

This plan covers integrating GPS rolling-shutter line delay calibrations into the
Occultation Manager workflow. Implementation is broken into four development stages in
dependency order:

| Dev Stage | Description | Files |
|-----------|-------------|-------|
| **1** | Config data layer | `config.py` |
| **2** | Save calibration result from GPS Flash Calibration form | `led_line_delay_calibration.py` |
| **3** | View, label and delete stored calibrations | `line_delay_dialogs.py`, `equipment_dialogs.py` |
| **4** | Line Delay Calculator (Tools menu) | `line_delay_dialogs.py`, `main_gui.py` |

---

## Reference: Camera Parameters per Calibration Run

The following fields are extracted from the existing Excel spreadsheet and must be stored
with every calibration run. These are the camera settings that uniquely identify a "mode"
of the camera so the user can match a recording to the right calibration.

| Field             | Description / Example                                  |
|-------------------|--------------------------------------------------------|
| Camera            | Camera name, e.g. `asi462mm`                           |
| PC Name           | Computer name (from SharpCap or OS), e.g. `AstroPC`   |
| Camera Area       | Frame size (binned pixels), e.g. `816x822`             |
| Binning           | Binning factor, e.g. `1`, `2`, `2x2`                  |
| Tilt              | ROI Y offset (top of ROI in unbinned pixels), e.g. `280` |
| Pan               | ROI X offset (left of ROI in unbinned pixels), e.g. `68` |
| Colour Space      | e.g. `RAW16`, `RAW8`, `MONO16`                         |
| File Format       | e.g. `ADV`, `SER`, `FITS`                              |
| Per Line Delay    | Calibration result: ms/line (slope), e.g. `-0.040`     |
| Line 0 Delay      | Calibration result: delay at Y=0 (intercept), e.g. `17.6` ms |

> **Units:** Per Line Delay is stored and displayed in ms/line to 3 decimal places.
> Line 0 Delay is stored and displayed in ms.

Additionally, these metadata fields are stored per run:

| Field             | Description                                            |
|-------------------|--------------------------------------------------------|
| Label             | User-assigned letter (A, B, C…) identifying the settings combination |
| Run ID            | UUID (auto-generated)                                  |
| Camera ID         | Foreign key to the `cameras` config list               |
| Run DateTime (UTC)| When the calibration was recorded                      |
| Exposure (ms)     | Camera exposure during calibration                     |
| Gain              | Camera gain during calibration                         |
| Notes             | Optional free-text note                                |

---

## Dev Stage 1 — Config Data Layer (`config.py`) ✅

*Implemented. All other stages depend on this.*

Calibration runs are stored in the existing `occultation_config.json` under a new
top-level key `line_delay_calibrations` (a list of dicts). Each dict holds the fields
from the tables above. This keeps everything in the single existing config file and uses
the same `ConfigManager` helpers already in `config.py`.

### Implementation decisions recorded

- `'line_delay_calibrations': []` added to `default_config` so new installs start with
  an empty list and `load_config` will recognise the key from saved files automatically.
- Existing users without the key in their JSON file default to `[]` at runtime;
  the key is persisted on the next `save_config()` call.
- All CRUD methods use `self.config.get('line_delay_calibrations', [])` as a fallback
  in case the key is absent from an older config.
- `add_line_delay_calibration` defensively copies `run_dict` before adding the
  auto-generated `id` to avoid mutating the caller's dict.
- `update_line_delay_calibration` protects `id` and `camera_id` — those fields cannot
  be overwritten via an update call.
- `delete_line_delay_calibration` returns `False` (not an exception) if the run id is
  not found, consistent with the existing `delete_telescope` / `delete_camera` pattern.
- `get_line_delay_calibration_by_id` added (not in the original plan) — needed by Stage 2
  and Stage 3 to fetch a single run by id without iterating at the call site.

### `ConfigManager` methods added

- `get_line_delay_calibrations(camera_id=None)` — return all runs, optionally filtered by camera
- `get_line_delay_calibration_by_id(run_id)` — return a single run by UUID, or None
- `add_line_delay_calibration(run_dict)` — append and save; auto-generates id if absent
- `update_line_delay_calibration(run_id, updates)` — patch fields and save; protects id/camera_id
- `delete_line_delay_calibration(run_id)` — remove and save; returns True/False

---

## Dev Stage 2 — Save Calibration Result (`led_line_delay_calibration.py`) ✅

*Depends on Stage 1. Implement second — gets real data into the store immediately.*

**Status: Implemented.** Changes applied to both `occultation-manager/python/` and `gps-timing-analysis/python/` copies.

**Implementation decisions:**
- `SaveCalibrationDialog` added in `led_line_delay_calibration.py` (self-contained; `line_delay_dialogs.py` deferred to Stage 3)
- Config imported at module top via `try/except` into `_om_config` / `_OM_CONFIG_AVAILABLE` flag — graceful fallback when running standalone from `gps-timing-analysis`
- `_collect_calibration_settings(camera)` uses compact keys (camera_name, tilt, pan, etc.) — different from `_get_camera_settings()` which uses verbose display keys for the stability test
- `_collect_calibration_settings_from_adv(...)` populates what ADV metadata can provide; leaves tilt/pan/colour_space/gain blank for user correction in dialog
- `button_save_calibration` at `Point(440, 520), Size(150, 25)` — sits left of Close button at `Point(600, 520)`
- Button disabled on form open and at start of each new calibration run; enabled by `display_results()` on success
- `run_datetime` stored as ISO-8601 UTC: `'%Y-%m-%dT%H:%M:%SZ'`
- `tilt`/`pan` stored as `int` or `None`; `exposure_ms` as `float` or `None`; `gain` as `str`

---

## Dev Stage 3 — Calibration Manager Dialog (`line_delay_dialogs.py`, `equipment_dialogs.py`) ✅

*Depends on Stages 1 and 2. Implement third — provides a UI to inspect and manage stored runs.*

**Status: Implemented.**

**Implementation decisions:**
- `line_delay_dialogs.py` is a new file containing `LineDelayCalibrationManagerDialog`
- `DataGridView` shows all columns from the plan spec; `Label` and `Notes` columns are editable inline via `CellEndEdit` → `config.update_line_delay_calibration()`
- Runs sorted newest-first by `run_datetime`
- When `camera_id` is provided (Camera Manager entry point), a `Camera` column is omitted; when `camera_id=None` (future Tools menu entry point), a `Camera` column is prepended
- Two buttons added to `CameraManagerDialog` in `equipment_dialogs.py` on a new row below Add/Update/Delete: **"Calibrations..."** and **"Run New Calibration"**; both enabled/disabled in sync with camera selection
- `run_new_calibration` handler launches `LEDLineDelayCalibrationForm` then, on close, if `_calib_fit_result is not None and not _calib_saved`, offers to save with the selected camera pre-selected in the dialog
- `SaveCalibrationDialog` gains optional `preselect_camera_id=None` parameter — used by the "Run New Calibration" path; falls back to first camera if ID not found
- `_calib_saved` flag added to `LEDLineDelayCalibrationForm` (reset at start of each run, set to `True` when `SaveCalibrationDialog` returns `DialogResult.OK`); prevents double-save prompts
- Both copies of `led_line_delay_calibration.py` updated (`occultation-manager/python/` and `gps-timing-analysis/python/`)
- Pre-population of calibration form fields (Capture Duration, Flash Duration, Invert) from most recent run deferred — those settings are not stored in the calibration run schema

---

## Dev Stage 4 — Line Delay Calculator (`line_delay_dialogs.py`, `main_gui.py`) ✅

*Depends on Stages 1–3. Implement last.*

**Status: Implemented.**

**Implementation decisions:**
- `LineDelayCalculatorDialog` added to `line_delay_dialogs.py` (after `LineDelayCalibrationManagerDialog`)
- Modal dialog (`ShowDialog`) — no persistent window reference needed; opened fresh each time
- Camera dropdown populated from `config.get_cameras()`; change refreshes calibration dropdown
- Calibration dropdown shows `"Label — camera_area, bin binning"` for easy identification; sorted with labelled runs first (alphabetically), unlabelled last
- "No calibrations" warning shown in dark red when a camera has no stored runs; calibration combo disabled
- Y Line accepts any float (covers fractional pixels from sub-pixel aperture centroiding)
- Result displayed at 22pt bold in dark blue; formula breakdown shown in gray below: `slope × Y + intercept = result ms`; both update live on every keystroke
- Copy button writes `"{delay:.3f}"` (3 decimal places, no unit suffix) to clipboard — format matches what TANGRA expects
- "Manage Calibrations…" button opens `LineDelayCalibrationManagerDialog` for the current camera; calibration list refreshes after the manager closes
- Tools menu entry: **"Line Delay Calculator"** added after "GPS PPS Comparison" (no separator needed — it's a natural continuation of the GPS/timing tools group)
- Handler `open_line_delay_calculator_click` in `main_gui.py` uses lazy `import line_delay_dialogs` consistent with other dialog handlers

---

## Open Questions / Decisions Required

### Stage 1

1. **Units for Per Line Delay** — ✅ **ms/line, displayed to 3 decimal places** (consistent
   with the existing Excel sheet).

2. **Multiple accepted calibrations per camera** — ✅ **Keep the letter-label concept (A, B, C…)
   from the Excel sheet.** Each distinct settings combination for a camera gets a user-assigned
   letter label. Multiple labelled calibrations can coexist for the same camera. The user is
   responsible for managing the list — old or obsolete runs can be deleted manually. There is
   no automatic "accepted" flag; the user picks the appropriate labelled calibration when
   calculating a delay.

3. **Camera settings matching** — ✅ **Manual selection.** The user picks the correct labelled
   calibration (A, B, C…) from the list when generating a report. No automatic matching.

4. **Cross-platform path for GPS Calibration form** — ✅ **No additional work required.**
   The existing `LEDLineDelayCalibrationForm` already supports loading an ADV file as an
   alternative to a live camera. Users who do not have a camera connected can use that path.

5. **New dialogs file location** — ✅ **New `line_delay_dialogs.py`.**
   All new line-delay dialogs (`LineDelayCalibrationManagerDialog`, save/label prompts,
   standalone calculator) go in a new `line_delay_dialogs.py`. The `CameraManagerDialog`
   in `equipment_dialogs.py` gains the two new buttons but the dialogs they open are
   imported from `line_delay_dialogs.py`.

### Stage 2

6. **Editing Notes in the calibration table** — ✅ **Inline editing.** Notes and the letter
   label are editable directly in the table row. A **Delete** button removes the selected
   calibration run (with a confirmation prompt).

### Stage 3

7. **Y-line source** — ✅ **Manual entry for now.** The user reads the occulted star's Y pixel
   position from TANGRA and types it in. Auto-read from the Tangra CSV may be added in a
   future stage.

8. **Line delay in report output** — ✅ **No changes required.** The acquisition delay is
   already read directly from the TANGRA file during report generation.

9. **Combined timing offset display** — ✅ **No combined value.** NTP offset and camera
   acquisition delay are separate and will be displayed independently.

---

## Affected Files

| Dev Stage | File | Change |
|-----------|------|--------|
| 1 | `config.py` | New `line_delay_calibrations` key + CRUD methods |
| 2 | `led_line_delay_calibration.py` | Add "Save Result to Camera" button; expose result via return value or callback |
| 3 | `line_delay_dialogs.py` | **New file** — `LineDelayCalibrationManagerDialog`, save/label prompt |
| 3 | `equipment_dialogs.py` | Add "Calibrations…" and "Run New Calibration" buttons to `CameraManagerDialog` |
| 4 | `line_delay_dialogs.py` | Add `LineDelayCalculatorDialog` |
| 4 | `main_gui.py` | Add "Line Delay Calculator" to Tools menu |

---

*Plan version: 1.0 — all decisions resolved, ready for implementation.*
