# Plan: VizieR Light Curve .dat Export

## TL;DR
Add VizieR .dat light curve export to Occultation Manager. PyOTE does not query Vizier — it *exports* processed light curves in a 5-line text format for submission to the VizieR archive. We implement the same format in two new IronPython-compatible modules: `vizier_export.py` (pure processing) and `vizier_export_dialog.py` (WinForms dialog with embedded chart).

---

## Key Research Findings

**PyOTE .dat file format (5 lines):**
```
Date: {year}-{month}-{day} {HH:MM:SS.ss}: {deltaTime:.2f}: {numReadings}
Star: {hipparcos}: 0: 0: 0: {Tycho2}: {UCAC4}
Observer: {+/-longDeg}:{longMin}:{longSec}: {+/-latDeg}:{latMin}:{latSec}: {altitude}: {observer_name}
Object: Asteroid: {asteroidNumber}: {asteroidName}
Values:{v1}:{v2}: :{v3}:...
```
- Values scaled so max = 9524; dropped readings encoded as `": "` (empty field between colons)
- Filename: `({num})_{yyyymmdd}_{HH}{MM}{SS}_{FF}.dat`

**Data sources in OM — all available:**

| Field | Source |
|---|---|
| Timestamps + values | `light_curve_reader.read_light_curve()` — datetime objects + floats |
| Median frame interval | `get_observation_summary()` → `tdelta_median` |
| Asteroid number/name | `event.object_no`, `event.object_name` |
| Observer lat/lon/elevation | `event.latitude`, `event.longitude`, `event.elevation` (decimal degrees, meters) |
| Observer name | `config.get_observer_name()` |
| Star catalog IDs | `event.star_id` (e.g. `UCAC4 361-199861`) — parseable |
| D/R times | `aota_report_data` dict (optional, for auto-trim) |

**IronPython adaptation needed:**
- No `numpy` → pure Python list operations + sort-based median
- No `matplotlib` → WinForms `System.Windows.Forms.DataVisualization.Charting`
- `-0.0` sentinel works natively; `math.copysign` available in IronPython 3.4

---

## Implementation Steps

### Phase 1 — `vizier_export.py` (pure processing, independently testable)

1. `parse_star_id(star_id)` → `{'ucac4', 'tycho2', 'hipparcos'}` — parses OWCloud star name strings like `UCAC4 361-199861`, `TYC 1234-5678-1`, `HIP 12345`
2. `decimal_degrees_to_dms(d)` → `(deg_str, min_str, sec_str)` — with `+/-` sign prefix on degrees
3. `to_seconds(dt)` — datetime → float seconds-from-midnight
4. `compute_median_step(times)` — pure Python sort-based median of inter-frame deltas; no numpy
5. `is_neg_zero(v)` — `math.copysign(1, v) < 0 and v == 0.0`
6. `insert_dropped_readings(frames, times, values, time_step_s)` → expanded lists with `-0.0` sentinels; gaps > 1.8× step → synthetic frames; **depends on step 4**
7. `compute_trim_window(times, d_time_s, r_time_s, event_time_s, event_duration_s)` → `(left_idx, right_idx)` — half-window = `max(15, event_duration + 20)` seconds each side; **depends on step 6** (operates on expanded times)
8. `build_date_line`, `build_star_line`, `build_location_line`, `build_object_line`, `build_values_line` — string formatters
9. `generate_dat_filename(...)` → filename string
10. `export_vizier_dat(output_path, ...)` — writes the 5-line file; includes `camera_correction_s=0.0` parameter stub for future use
11. `get_output_paths(...)` → list of 3 destination paths: `%USERPROFILE%\Documents\VizieR_lightcurves\`, OM `data/reports/`, observation source folder

### Phase 2 — `vizier_export_dialog.py` (WinForms dialog) *(depends on Phase 1)*

12. `VizierExportDialog(Form)` constructor: `(lc_path, event, config, observation_folder, aota_report_data=None)`
13. `_load_and_prepare()` — calls `read_light_curve()` → `insert_dropped_readings()` → `compute_trim_window()` → initial chart draw
14. GroupBox "Star Catalog Identifiers" — UCAC4, Tycho2, Hipparcos TextBoxes pre-filled from `parse_star_id(event.star_id)`; user-editable; validated at export
15. GroupBox "Observer Info" — read-only labels from `event` + `config`
16. GroupBox "Trim" — NumericUpDown first/last frame; "Auto Trim" button; label showing selected duration
17. WinForms Chart — embedded in dialog; scaled ADU values; dropped readings in red; vertical reference lines for D/R times and predicted event time
18. `_export_click()` — validates star fields, calls `export_vizier_dat()` for each destination path, shows success/failure

### Phase 3 — Packaging *(depends on Phase 1+2)*

19. Add `vizier_export.py` and `vizier_export_dialog.py` to `create_release_zip.ps1`

---

## Relevant Files

- `occultation-manager/python/vizier_export.py` — **create** (new)
- `occultation-manager/python/vizier_export_dialog.py` — **create** (new)
- `occultation-manager/create_release_zip.ps1` — add both files (step 19)
- Reference: `light_curve_reader.py` — `read_light_curve()`, `get_observation_summary()`
- Reference: `pyote_metrics_reader.py` — analogous module structure pattern
- Reference: `comprehensive_report_dialog.py` — source of `lc_path` and `observation_folder` for launch args

---

## Decisions Made

| Decision | Choice |
|---|---|
| Camera correction | NOT applied initially; `camera_correction_s=0.0` stub in API for future |
| Output destinations | 3 copies: VizieR_lightcurves folder, OM reports/, observation source folder |
| Trim default | Centred on D/R midpoint or predicted event time; half-window = max(15s, event_duration+20s) each side |
| Plot preview | Embedded WinForms Chart in export dialog |
| Zip archive | Later phase |

---

## Verification Checklist

1. `insert_dropped_readings` unit-test: 3-frame gap at 120ms cadence → exactly 2 `-0.0` sentinels inserted
2. `compute_trim_window`: D=14:30:42, R=14:30:50, 8s duration, 120ms cadence → ≥ 292 frames each side (≥ 35s each side)
3. `build_values_line`: max ADU 48000 → scale factor = 9524/48000 = 0.1984; verify colon encoding for dropped readings
4. `parse_star_id`: `UCAC4 361-199861` → `ucac4='361-199861'`; `TYC 1234-5678-1` → `tycho2='1234-5678-1'`; `HIP 12345` → `hipparcos='12345'`; Gaia string → all empty
5. Full pipeline: generate .dat from a real Tangra/R-OTE CSV + event object; check all 5 lines match format
6. Open generated `.dat` in PyOTE to verify acceptance
7. Confirm all 3 destination copies are written
8. Dialog chart: dropped readings render in red; trim adjusts chart range correctly

---

## Further Considerations

1. **`star_id` format ambiguity** — OWCloud `StarName` values vary by event. `parse_star_id` should handle known patterns and silently leave fields blank for unrecognised formats (e.g. Gaia DR3 IDs must NOT be placed in Hipparcos field), prompting the user to fill in manually.
2. **GUI integration point** — TBD by user. The dialog is designed as a self-contained form with 5 constructor args so it can be launched from any button or menu item without modification.
3. **Camera correction** — noted as future work; the `export_vizier_dat` signature includes `camera_correction_s=0.0` so the initial timestamp can be adjusted later without API changes.
