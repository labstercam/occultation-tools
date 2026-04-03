# GPS PPS Comparison Analysis — Development Plan

## Overview

Add a new **GPS PPS Comparison Analysis** tool that reads the same `loopstats` and `peerstats` files as the existing NTP accuracy analysis tool, identifies the GPS PPS refclock server in the data, and plots the deviation of each internet NTP server from GPS PPS time as the true UTC error.

The GPS PPS source is assumed accurate to <<1 ms. The difference between a GPS PPS offset measurement and an internet NTP server offset measurement is therefore the error in the internet NTP server.

---

## Architecture Decision

**New separate form** — not a mode toggle or optional elements added to the existing NTP analysis form.

**Rationale:**
- The GPS comparison has a unique preflight validation workflow (confirm GPS server, verify noselect state) that does not fit in the existing form's flow
- Its 3 plots serve a different analytical purpose than the 4 existing diagnostic plots
- Both windows can be open simultaneously for cross-reference
- Zero risk of breaking existing NTP accuracy analysis functionality

**Rejected alternative:** "Mode toggle / optional elements" approach — swapping the chart panel between two modes on the same form would make the UI confusing and make the pre-flight step awkward to trigger and re-run.

---

## Decisions Record

| Question | Decision |
|---|---|
| GPS PPS address detection | Scan for any `127.127.*.*` (any NTP refclock); user chooses which one in the preflight dialog |
| noselect validation strictness | Warn and restrict analysis to strictly-noselect periods only (select code < 4) |
| Time alignment method | Linear interpolate GPS PPS offset to internet server timestamps; reject gaps > 120 s |
| Clock drift estimation source | Linear regression on selected peer offset slope over the GPS coverage window |
| New form vs existing form modification | New separate form |
| Uncertainty report | Per-server table then combined k=2 estimate |

---

## Phase 1 — Core Analysis Functions in `ntp_analysis_core.py`

Add after the helper cluster near line 1237, before `analyze()`.
All new functions are pure Python with no GUI imports — safe to test in CPython.

### 1.1 `find_gps_pps_candidates(peer_rows)`
- Input: `list[PeerRecord]`
- Output: `list[(addr: str, record_count: int)]` sorted by record count descending
- Logic: collect unique `server_address` values that start with `"127.127."`, count records per address

### 1.2 `check_gps_pps_noselect_status(peer_rows, gps_pps_addr)`
- Output: `dict` with keys:
  - `is_strictly_noselect` (bool) — True if all records have select code < 4
  - `select_code_counts` (dict[int, int]) — count per select code observed
  - `noselect_fraction` (float) — fraction of records with select code < 4
  - `warnings` (list[str]) — human-readable warnings if non-noselect records found
- Notes: select codes 0–3 = noselect/reject/falsetick/excess; 4+ = candidate or better (noselect was not in effect)

### 1.3 `get_gps_pps_noselect_intervals(peer_rows, gps_pps_addr, gap_threshold_s=300)`
- Output: `list[(start_dt: datetime, end_dt: datetime)]`
- Logic: filter to GPS PPS records with select code < 4, sorted by timestamp; group into contiguous runs where consecutive records are ≤ `gap_threshold_s` apart

### 1.4 `interpolate_gps_pps_offset(gps_records_sorted, target_dt, max_gap_s=120)`
- Output: `float | None`
- Logic: find the two GPS PPS records that bracket `target_dt`; linearly interpolate; return `None` if the gap between them exceeds `max_gap_s` or no bracketing records exist

### 1.5 `compute_gps_pps_comparison(peer_rows, gps_pps_addr, noselect_intervals, observer_lat, observer_lon)`
- Output: dict with keys:
  - `per_server_delay` — `dict[addr, list[(datetime, delay_s)]]` for all internet servers
  - `per_server_diff` — `dict[addr, list[(datetime, offset_diff_s)]]`
    - `offset_diff = internet_offset - interpolated_gps_pps_offset`
    - Only timestamps within `noselect_intervals` are included
  - `selected_peer_diff` — `list[(datetime, offset_diff_s)]` using `reduce_to_active_timeline()` output paired with GPS PPS interpolation
  - `server_to_km` — `dict[addr, float | None]` from `resolve_server_location()`
  - `gps_pps_addr`, `noselect_intervals`, `coverage_hours`

### 1.6 `estimate_comparison_uncertainty(per_server_diff)`
- Output: dict with keys:
  - `per_server` — `dict[addr, {mean_ms, stdev_ms, u_expanded_k2_ms, n}]`
  - `combined` — `{mean_ms, stdev_ms, u_expanded_k2_ms, n}` (all server diff values pooled)
- Formula: u_expanded (k=2) = 2 × stdev(diff values)
- Flag when `n < 30` for any server or combined

### 1.7 `estimate_drift_linear_regression(peer_rows, selected_peer_addr, start_dt, end_dt)`
- Output: dict with keys:
  - `drift_ppm` — slope in ppm (s/s × 1e6)
  - `drift_ms_per_hour` — slope in ms/hour
  - `r_squared` — goodness-of-fit
  - `n_points`, `coverage_hours`
  - `start_offset_ms`, `end_offset_ms`
- Logic: filter selected-peer records to `[start_dt, end_dt]`; ordinary least squares regression of `offset_s` vs `t_s` (seconds since start_dt); no external libraries — implement OLS directly using sums

### 1.8 `generate_gps_comparison_report(comparison_result, uncertainty_result, drift_result)`
- Output: `str`
- Formats: GPS server confirmed, noselect coverage period, per-server deviation table (mean ± k=2), combined k=2 estimate, clock drift narrative

---

## Phase 2 — Preflight Dialog

**File:** `gps-timing-analysis/python/gps_pps_comparison.py` (new file)  
**Class:** `GPSPPSPreflightDialog(Form)` — modal ~480 × 400 px

### Controls

| Control | Purpose |
|---|---|
| Instruction label | "Select the GPS/PPS refclock server to use as the reference" |
| `ListBox` | One row per `127.127.*.*` candidate: `"127.127.20.0   (1842 records)"` |
| Status panel / `Label` | Traffic-light background colour + summary text |
| noselect summary `Label` | e.g. `"Noselect period: 10.2 hrs (96% of records)"` |
| Warning `Label` | Shown in amber if non-noselect records were found |
| OK / Cancel buttons | OK disabled until a server is selected |

### Traffic-light logic

| Condition | Colour | Meaning |
|---|---|---|
| All records noselect | Green | `"All records in noselect state — clean reference"` |
| ≥ 90% records noselect | Yellow/Amber | `"Mostly noselect — analysis restricted to clean intervals"` |
| < 90% records noselect | Red | `"Significant selected periods — review before proceeding"` |

### Output properties
- `selected_gps_addr` (str) — the chosen address
- `noselect_intervals` (list) — from `get_gps_pps_noselect_intervals()`
- `noselect_status` (dict) — from `check_gps_pps_noselect_status()`

---

## Phase 3 — Main Comparison Form

**File:** `gps-timing-analysis/python/gps_pps_comparison.py`  
**Class:** `GPSPPSComparisonForm(Form)` — non-modal, 1600 × 900, min 1100 × 700

### Left Panel Controls

| Control | Purpose |
|---|---|
| Title label | "GPS PPS Comparison Analysis" |
| Log folder `TextBox` + Browse button | NTP log folder (shares same settings key as existing form) |
| Scan button + Dataset `ComboBox` | Reuses `build_day_options()` |
| Observer lat/lon `TextBox` × 2 | Decimal degrees; shared with existing form settings |
| "Run Comparison" button (bold) | Opens preflight dialog, then runs analysis |
| GPS PPS server confirmed `Label` | Populated after preflight e.g. `"GPS PPS: 127.127.20.0"` |
| noselect period `Label` | e.g. `"Noselect coverage: 10.2 hrs"` |
| k=2 uncertainty `TextBox` (readonly) | e.g. `"Combined UTC error (k=2): ±2.8 ms"` |
| Drift estimate `TextBox` (readonly) | e.g. `"Clock drift: +0.42 ms/hr (r²=0.91)"` |
| Full report `TextBox` (Consolas 9, multiline readonly) | Per-server table + combined + drift narrative |
| Export checkbox + export folder `TextBox` + Browse | Optional JSON/CSV export |
| Status `Label` (bottom-anchored) | Status bar |

### Right Panel — 3-Row TableLayoutPanel (33% each)

| Row | Chart title | Series | Special drawing |
|---|---|---|---|
| 0 | "NTP Server Delays" | Each internet server, color-coded by `SERVER_COLORS` | Legend swatches with IP + km (same pattern as existing delay chart) |
| 1 | "UTC Error per Server (Offset − GPS PPS)" | Each internet server's diff, color-coded | Semi-transparent grey `FillRectangle` band = GPS PPS noselect window; zero line |
| 2 | "Selected Peer UTC Error + Clock Drift" | Single series | Grey band + dashed linear trend overlay |

### GDI+ Drawing Additions

Reuse `map_x`, `map_y`, `draw_empty_plot`, `draw_plot` patterns from `analyze_ntp_timing_accuracy.py`.

New helpers:
- **`draw_coverage_band(graphics, bounds, intervals, x_start, x_end)`** — draws semi-transparent grey `FillRectangle` for GPS coverage periods before series lines in plots 1 and 2
- **`draw_trend_line(graphics, bounds, regression_result, x_start, x_end, y_min, y_max)`** — dashed `Pen` overlay for linear drift trend in plot 2

### Instance State

| Field | Purpose |
|---|---|
| `_options_by_label` | Dataset options dict, from `scan_options()` |
| `_gps_pps_addr` | Confirmed GPS address from preflight |
| `_noselect_intervals` | list of `(start_dt, end_dt)` |
| `_last_peer_rows` | Cached `list[PeerRecord]` |
| `_last_loop_rows` | Cached `list[LoopRecord]` |
| `_comparison_result` | Full result from `compute_gps_pps_comparison()` |
| `_uncertainty_result` | From `estimate_comparison_uncertainty()` |
| `_drift_result` | From `estimate_drift_linear_regression()` |
| `_plot_data` | `dict` keyed `"delays"`, `"offset_diffs"`, `"selected_diff"` |

---

## Phase 4 — Integration

### 4.1 `occultation-manager/python/main_gui.py`
- Add `"GPS PPS Comparison"` `ToolStripMenuItem` to Tools menu (after `"GPS Flash Calibration"`)
- Handler: `open_gps_pps_comparison_click` — uses `imp.load_source` fallback for `gps_pps_comparison.py`
- State attribute: `self._gps_pps_comp_form = None`

### 4.2 `occultation-manager/create_release_zip.ps1`
- Add `gps_pps_comparison.py` to `$gpsPythonFiles` list

### 4.3 `gps-timing-analysis/python/analyze_ntp_timing_accuracy.py` *(optional / deferred)*
- Add `"GPS PPS Comparison…"` button at the bottom of the left panel
- Pre-fills log folder and observer coords from the current form into the new form

---

## Key Formulas

```
# Offset difference (UTC error of internet server)
offset_diff(t) = internet_offset(t) - interpolate_gps_pps_offset(t)

# Per-server uncertainty (k=2, coverage factor 2)
mean_D   = mean(offset_diff values for server)
u_k2     = 2 × stdev(offset_diff values for server)
interval = mean_D ± u_k2

# Combined uncertainty (all servers pooled)
u_k2_combined = 2 × stdev(all offset_diff values)

# Clock drift from linear regression
slope (s/s) = OLS slope of selected_peer_offset vs time in seconds
drift_ppm  = slope × 1e6
drift_ms_hr = slope × 3600 × 1000
```

---

## noselect Identification Logic

GPS PPS records in `peerstats` use the NTP status word select bits (bits 8–10):

| Select code | Meaning | noselect active? |
|---|---|---|
| 0 | reject | Yes |
| 1 | falsetick | Yes |
| 2 | excess | Yes |
| 3 | outlier | Yes |
| 4 | candidate | **No** |
| 5 | backup | **No** |
| 6 | sys.peer | **No** |
| 7 | pps.peer | **No** |

Analysis is restricted to contiguous intervals where select code < 4 (gap tolerance: 5 minutes).

---

## Verification Steps

1. **Unit test (CPython):** call `find_gps_pps_candidates()` on a peerstats file with a `127.127.20.0` entry — confirm it returns that address
2. **Unit test:** call `check_gps_pps_noselect_status()` with mixed select codes — confirm `is_strictly_noselect=False` and warnings populated
3. **Unit test:** call `compute_gps_pps_comparison()` with GPS and internet server having identical offsets — confirm all diffs ≈ 0
4. **GUI test:** open `GPSPPSComparisonForm` in SharpCap, scan a dataset, click Run Comparison — confirm preflight dialog appears, all 3 plots render, report text appears
5. **Visual check:** grey GPS coverage band visually aligns with `noselect_intervals` on plots 1 and 2
6. **Packaging check:** run `create_release_zip.ps1` and confirm `gps_pps_comparison.py` is in the ZIP

---

## Further Considerations

1. **Export** — The comparison result should be exportable to JSON/CSV matching the existing export pattern; add export controls to the left panel in Phase 3.
2. **Minimum n warning** — Flag in the report when `n < 30` per-server diff points; the k=2 estimate is statistically weak with few records.
3. **loopstats freq field** — Although peer offset regression was chosen for drift, the loopstats `freq` field (NTP's own frequency correction) is a cleaner signal. Display it alongside the regression estimate as a sanity check.
4. **Shared settings** — Both forms write to the same `ntp_analyzer_settings.json`; coordinate so one form's Save does not overwrite the other's in-flight changes.

---

## Implementation Order

```
Phase 1  →  ntp_analysis_core.py   (8 new functions, pure Python, testable)
Phase 2  →  gps_pps_comparison.py  (GPSPPSPreflightDialog)
Phase 3  →  gps_pps_comparison.py  (GPSPPSComparisonForm + 3 plots)
Phase 4a →  main_gui.py            (Tools menu item)
Phase 4b →  create_release_zip.ps1 (packaging)
Phase 4c →  analyze_ntp_timing_accuracy.py  (optional launch button, deferred)
```
