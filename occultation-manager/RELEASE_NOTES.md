# Occultation Manager - Release Notes

## Version 0.2.0-beta.9 (April 2026)

**Report Generation Bug Fixes and UX Improvements**

### SNR Fix — AOTA Report Parser (Bug Fix)

The SNR (Signal-to-Noise Ratio) field was not populating in the TT Excel report when an AOTA
Report text file was used as the timing source. The parser's regex was matching only `Ave:` but
some AOTA Report versions label the average as `Average:`.

- Regex updated from `r'Ave:\s*([\d.]+)'` to `r'(?:Ave|Average)\s*:\s*([\d.]+)'` with `re.IGNORECASE`
- SNR now correctly populates cell W40 in the RASNZ TT report for both label variants

### Camera Acquisition Delay — 4 Decimal Places (Bug Fix)

The camera acquisition delay written to the TT report (cell P26) was rounding to 3 or fewer
decimal places, losing precision for delays calculated from the rolling-shutter calibration.

- `total_delay_s` and `delay_sec` in `tt_report_openize.py` now rounded to 4 decimal places
- Consistent with the precision provided by Tangra's measurement parameters

### NTP Timing Comment — Correct Cell (Bug Fix)

The NTP timing uncertainty note (generated when the NTP uncertainty checkbox is ticked in the
D/R info panel) was being merged into the "Other Conditions" field and written to the wrong
cell in the TT report. It is now written to its own row in Additional Comments.

- `ntp_comment` is no longer merged into `other_conditions` in `main_gui.py`
- Passed as a separate `ntp_comment=` kwarg to all three report generators
- In the TT report: written to cell **D44** (Additional Comments, third row)
- `na_report_openize.py` and `sodis_report_text.py` accept the kwarg (unused — those formats
  handle their own comment layout)

### AOTA Report — Default First in D/R Event Combo (UX)

When AOTA Report events are available in the D/R event combo of the Phase B report dialog,
they are now listed first (before AOTA XML events and PyOTE events), making the most commonly
used source the default selection.

---

## Version 0.2.0-beta.8 (April 2026)

**NTP Timing Corrections — Observer Verification Workflow**

This release closes four safety gaps in the Option 1 (corrections applied in Tangra) NTP
timing workflow, ensuring observers can confirm, record, and verify their timing corrections
before generating a report.

### Gap 1 — Confirmation Checkboxes (New)

When "Applied in Tangra" is selected in §3 Timing, a confirmation sub-panel now expands
inline showing two checkboxes:

- **Camera acquisition delay: X.X ms** — populated from the calibrated Y-line calculation
- **NTP clock offset: ±X.X ms** — populated from the loaded NTP log

Both must be ticked before the **Generate Report** button becomes active. The panel heading
reads *"Confirm the values you entered in Tangra match:"*

### Gap 2 — Stale Correction Warning (New)

If the observer ticks the confirmation checkboxes and then changes an input (edits the Y line,
selects a different calibration run, or loads a different NTP log file), the affected checkbox
is automatically **unticked** and the panel heading changes to:

> ⚠ Values changed — please re-confirm below:   *(orange)*

Re-ticking both checkboxes restores the normal heading. Navigating away from "Applied in Tangra"
to another radio clears both checkboxes and resets the heading automatically.

### Gap 3 — D/R Plausibility Check (New)

After confirming, a new plausibility label (below the D/R preview rows) checks:

1. **D ≥ R check** *(blocking)* — for Positive/Unsure observations with "Applied in Tangra"
   selected, if the corrected disappearance time is not before the reappearance time, the label
   shows a red ⚠ warning and Generate is blocked until the discrepancy is resolved.

2. **Large correction warning** *(non-blocking)* — if the net correction (camera delay + NTP
   offset) exceeds 500 ms, an orange ⚠ warning is shown as a prompt to double-check inputs.

Both warnings are suppressed when "Not yet applied" is selected (the guidance panel occupies
the same space). The D/R check also re-runs whenever a different PyOTE event is selected.

### Gap 4 — Timing Corrections Written to Report Comments (New)

All three report generators (NA, TT, SODIS) now write a human-readable timing note to their
comments/notes section:

| State | Comment text |
|---|---|
| Applied + confirmed | *"NTP timing corrections applied in Tangra: camera acq. delay 14.3 ms, NTP offset +5.2 ms (net +19.5 ms) — confirmed by observer"* |
| Applied (not confirmed) | Same, without *"— confirmed by observer"* |
| N/A | *"NTP system used; timing corrections not applicable"* |
| Not yet applied | *"NTP timing: corrections not applied in this session"* |
| GPS (dumb) | *"GPS timing (reference only); no OM timing correction applied"* |

Implemented via `ReportGeneratorBase.build_timing_note(timing_data)`.

### Contextual Help — Tooltips and Info Buttons (New)

All key controls in §3 Timing (NTP) and §3 Observation Result now carry contextual guidance:

**Hover tooltips** on:
- Calibration run selector — match requirements (area, binning, gain, frame rate)
- Y-line field — how to read the value from Tangra
- Net correction label — definition and sign convention
- Confirmation checkboxes — what exactly to verify in Tangra
- "Not yet applied" radio — points to the guidance panel
- Observation type radios — AOTA requirement reminder per type

**Info/explain buttons** (click for a message box):
- **ⓘ What is NTP correction?** — explains camera delay, NTP offset, and the net formula
- **? (Calibration run)** — explains what a run is, what settings must match, and how to create a new one
- **? (Y-line)** — step-by-step instructions for finding the Y coordinate in Tangra
- **Why confirm?** — explains the silent-error risk and exactly where in Tangra to enter each value
- **What happened?** — appears next to the D≥R plausibility warning; lists four common causes
- **? (status bar)** — appears when Generate is blocked; shows the full blocking reason in a popup

### `get_timing_data()` — `corrections_confirmed` field (New)

`ComprehensiveReportDialog.get_timing_data()` now includes a `corrections_confirmed` boolean
in the returned dict. `True` only when "Applied in Tangra" is selected **and** both confirmation
checkboxes are ticked at the time the report is generated. Downstream code can use this field
to distinguish confirmed vs. unconfirmed correction declarations.

---

## Version 0.2.0-beta.7 (April 2026)

**Multi-Format Light Curve Support and PyOTE Metrics Integration**

### Multi-Format Light Curve Reader (New Module)

A new `light_curve_reader.py` module provides automatic format detection and unified reading for all supported light curve CSV formats:

- **Tangra** — standard IOTA CSV format
- **R-OTE / PyOTE** — CSV format used by the R-OTE and PyOTE analysis tools
- **Limovie** — CSV export from Limovie

`detect_format(filepath)` identifies the format from the first line of the file without relying on filename conventions. `read_light_curve(filepath)` returns a unified `(frames, times, values)` tuple for all supported formats.

### Timestamp Inspector Available for All Light Curve Formats

The **Inspect Timestamps...** button in the Generate Report dialog is now available for R-OTE and Limovie CSV files as well as Tangra. All formats use `light_curve_reader.read_light_curve()` for consistent timestamp analysis with the same deviation charts, statistics line, and event-time reference lines.

### PyOTE fit_metrics.txt Integration (New)

The **4. Observation Files** section of the Generate Report dialog now supports PyOTE `fit_metrics.txt` files as an additional D/R timing source alongside AOTA XML and AOTA Report files:

- **Content-based file detection**: scans all `.txt` files in the observation folder and identifies PyOTE metrics files by their `aperture name,` CSV header — no specific filename convention required
- **Event selection**: a second listbox lists all aperture/event rows within the selected metrics file; each entry shows the aperture name, D time, and R time
- **D/R preview**: a preview label shows the disappearance and reappearance times for the selected event
- **Report integration**: the selected PyOTE event provides D/R times and SNR (DNR) to all report generators (NA, TT, SODIS, Occult 4 XML) when no AOTA source is selected

New module `pyote_metrics_reader.py` provides:

- `detect_pyote_metrics(file_path)` — reads the first non-blank line and returns `True` if it starts with `aperture name,`
- `read_pyote_fit_metrics(file_path)` — full CSV read with header detection, blank-line and `Source file is` line skipping, and numeric coercion for all measurement columns
- `record_to_aota_report_data(record)` — converts a PyOTE event record to the shared `aota_report_data` dict shape consumed by all report generators
- `format_record_display(record)` — formats a one-line event summary for listbox display

### Other Improvements

- Updated release-facing documentation and version references for Beta.7.
- Updated release packaging/version pointers (ZIP naming and instructions).

---

## Version 0.2.0-beta.6 (April 2026)

**Report Enhancements & Help Documentation**

### Timestamp Check Subpanel (Generate Report form)

The Generate Report dialog now includes a Timestamp Check subpanel when a Tangra CSV is loaded:

- Colour-coded status label: **OK** / **Check** / **Issues** based on delayed/late frame counts
- Min/max deviation values (ms from median) displayed
- Event-time window warning when the OWC predicted event time falls outside the CSV time coverage
- **Explain...** button: describes what the check means and how to interpret results
- **Inspect Timestamps...** button: opens the new Timestamp Inspector window

### Timestamp Inspector Window (New)

A dedicated analysis window for visual frame timing inspection:

- **Chart 1**: Frame interval deviation from median (ms); Y-axis always spans ≥ ±5 ms
- **Chart 2**: Signal level (ADU) for the primary aperture
- **Stats line** between charts: median interval, min deviation, max deviation
- **Vertical reference lines**: blue solid = predicted event time, red dashed = D time,
  green dashed = R time

### Help Documentation Expanded

- New **Equipment Setup** topic: complete Telescope Manager and Camera Manager
  field-level documentation, including all Occult 4 codes and the first-time setup workflow
- **Quick Start** guide updated: Observer/Telescope tab fully documented; User Settings
  expanded with Sync Mount, Display UTC, and Debug Logs fields
- **Quick Filters** description updated: On/Off checkbox toggle documented
- **About dialog**: version updated to 0.2.0-beta.6, features list expanded to include
  telescope/camera management, calibration tools, Timestamp Inspector, and SODIS format support

### Other Improvements

- Updated release-facing documentation and version references for Beta.6.
- Updated release packaging/version pointers (ZIP naming and instructions).

---

## Version 0.2.0-beta.5 (April 2026)

**Line Delay Calibration Integration**

### GPS Flash Line Delay Calibration — Integrated Workflow (New)

The GPS flash line delay calibration tool is now fully integrated into the Occultation Manager
workflow. Previously available only as a standalone script from `gps-timing-analysis`, it can
now be launched, calibrated, and have results saved directly within the Occultation Manager.

**Camera Manager integration** (`Tools → Manage Cameras`):
- **Calibrations...** button: opens the Calibration Manager showing all stored calibration
  runs for the selected camera — view, label (A, B, C…), edit notes, and delete runs inline
- **Run New Calibration** button: launches the Camera Delay Calibration form with the current
  camera pre-selected; on close, if a result was produced but not saved, offers to save it
  with the camera pre-selected in the Save dialog

**Camera Delay Calibration form** (`Tools → Camera Delay Calibration`):
- New **Save Calibration to Camera** button appears after a successful calibration run
- Saves the result (per-line delay, line 0 delay) to the camera profile in
  `occultation_config.json` with full capture metadata (camera area, binning, tilt, pan,
  colour space, file format, exposure ms, gain)
- Each run carries a user-assignable letter label (A, B, C…) for identifying distinct
  camera settings combinations; multiple labelled calibrations per camera are supported
- **Approximate Delays** button: when no GPS flasher is available, measures frame rate at
  1 ms exposure and derives per-line and line-0 delays from the ROI height and a
  user-supplied minimum delay estimate

**New: Camera Delay Calculator** (`Tools → Camera Delay Calculator`):
- Select camera and labelled calibration from dropdowns
- Enter Y pixel position of the occulted star (accepts fractional pixels from TANGRA)
- Live calculation: `per_line_delay × Y + line_0_delay = acquisition delay (ms)` with
  formula breakdown shown in gray below the result
- One-click **Copy** button writes the delay (3 d.p., no unit suffix) to the clipboard
  in the format expected by TANGRA
- **Manage Calibrations…** button opens Calibration Manager for the selected camera inline

**Calibration data store:**
- All runs stored in `occultation_config.json` under `line_delay_calibrations`
- Full camera settings recorded per run for mode identification
- New CRUD methods on `ConfigManager`: `get_line_delay_calibrations(camera_id=None)`,
  `get_line_delay_calibration_by_id`, `add_line_delay_calibration`,
  `update_line_delay_calibration`, `delete_line_delay_calibration`

### Other Improvements

- Updated release-facing documentation and version references for Beta.5.
- Updated release packaging/version pointers (ZIP naming and instructions).

---

## Version 0.2.0-beta.4 (April 2026)

**NTP Timing Integration, GPS PPS Comparison Tool, and Chart Improvements**

### GPS PPS Comparison Analysis (New Tool)

A new standalone analysis form accessible from **Tools → GPS PPS Comparison** that uses the same NTP loopstats/peerstats dataset as the NTP Timing Analyser to measure how accurately each internet NTP server tracks true UTC.

The tool identifies a GPS PPS refclock (`127.127.*.*`) in the peerstats data as a UTC ground-truth reference and computes the UTC error of every internet server by interpolating the GPS offset to each server's measurement timestamp.  Analysis is restricted to strictly-noselect intervals (select code < 4) when NTP is not using the GPS as its sync source, preventing circular bias.

**Key capabilities:**
- **Preflight dialog**: scans all `127.127.*.*` candidates, shows record count, select-code distribution, and a traffic-light status indicator (green = strictly noselect, amber = mixed, red = never noselect); displays noselect interval coverage with timestamps
- **UTC Error chart**: per-server `offset − GPS PPS` offset in ms, constrained to GPS noselect windows, color-coded by server
- **Delay chart**: NTP round-trip delay for each server over the session
- **Selected Peer + Drift chart**: UTC error for the NTP-selected peer together with an OLS linear drift regression trend line
- **k=2 uncertainty box**: combined expanded uncertainty across all servers (mean, U(k=2), N)
- **Drift report**: clock drift in ms/hr and ppm with R² and record count
- **Text report**: per-server table with mean, Std, U(k=2), N; combined estimate; GPS coverage summary and warnings
- **JSON export**: full comparison result, uncertainty, and drift data
- **Observer lat/lon**: server distances shown in legend (uses shared `national_utc_ntp_servers.json` / IP geolocation cache)

**GPS PPS comparison calculation:**

For each internet server record inside a noselect interval:
```
UTC error = internet_offset − linear_interpolation(GPS PPS offset, target_time)
```
GPS measurements more than 120 s apart are rejected.  Expanded uncertainty U(k=2) = 2 × σ(UTC errors).

### NTP Timing Integration into Report Flow

The report workflow (Generate Reports → Confirm Observer Location) now includes an optional **NTP timing step** before the comprehensive report dialog:

- **Open NTP Analyser**: launches the full NTP Timing Analysis window non-blocking alongside the report dialog
- **Analyze NTP**: performs a quick in-flow NTP offset/uncertainty estimate directly in the dialog
- NTP dataset input uses a single stats folder; the closest loopstats/peerstats pair to the event date/time is auto-selected
- The selected folder is remembered between sessions
- Shared NTP resources (`national_utc_ntp_servers.json`, `ip_location_cache.json`) are loaded from the sibling `gps-timing-analysis/resources/` directory

### Chart and Axis Improvements (NTP and GPS PPS tools)

- **X-axis now visible on all charts**: data-constrained bounds (not midnight-to-midnight) with tick intervals chosen from the data span
  - ≤ 2 h span → 30 min major, 10 min minor
  - ≤ 6 h → 1 h / 30 min
  - ≤ 24 h → 2 h / 1 h
  - > 24 h → 6 h / 1 h
- **Y-axis tick density capped** at 8 intervals (9 gridlines) for all charts
- **Series clipped to plot rectangle**: out-of-range data no longer overflows axis borders
- **Legend on top chart only** (GPS PPS tools); selected-peer/drift chart has inline legend identifying the data line and the dashed OLS trend line
- Chart containers set `AutoSize = False` to prevent WinForms anchor miscalculation that was clipping axis labels

### Other Improvements

- Bugs fixes from user testing reports
- Improvements based on user feedback including better folder and file management
- Performed a brief cleanup to archive or remove out-of-date code/files.
- Updated release-facing documentation and version references for Beta.4.
- Updated release packaging/version pointers (ZIP naming and instructions).
- Release packaging now pre-seeds `data/templates` with sequencer master templates.
- Release ZIP packaging replaced `Compress-Archive` with `System.IO.Compression.ZipArchive` opened with `FileShare.ReadWrite`, eliminating "file in use" errors caused by antivirus/Windows Search Indexer scanning temp files during packaging.

---

## Version 0.2.0-beta.3 (March 2026)

**Bug Fixes, User Improvements, Documentation and Release Preparation Update**

- Bugs fixes from user testing reports
- Improvements based on user feedback including better folder and file management
- Performed a brief cleanup to archive or remove out-of-date code/files.
- Updated release-facing documentation and version references for Beta.3.
- Updated release packaging/version pointers (ZIP naming and instructions).
- Release packaging now pre-seeds `data/templates` with sequencer master templates.

### SODIS / IOTA-ES Report Support (MVP)

- Added new report format option: `IOTA-ES / SODIS (Form 2.03)` in comprehensive report dialog
- Added new report generator module: `sodis_report_text.py` (`SODISReportGeneratorText`)
- Wired SODIS generation into main report flow (`report_type == 'sodis'`)
- Added SODIS camera profile support in shared equipment dialog filtering
- SODIS output uses installed template source under `resources/templates_master/reports`
- SODIS filename format: `YYYYMMDD_asteroidNo_starCatalog_starNumber.txt`
- SODIS focal length output derived from aperture × focal ratio (cm, rounded)
- SODIS negative observations output `D: M` and `R: M`
- Updated warning text to include NA, TT, and SODIS coordinator approval status

---

## Version 0.2.0-beta.2 (February 2026)

**Excel Report Generation Improvements**

This release improves Excel report generation with the Openize SDK for more reliable, maintainable report creation with enhanced IronPython compatibility.

### What's New in Beta.2

#### Openize SDK Implementation
- **Direct Excel Cell Manipulation**: Uses Openize.OpenXML-SDK for direct cell access via IronPython
- **No More XML Placeholders**: Eliminates manual XML string replacement approach
- **Preserves Excel Features**: Maintains data validation, formulas, and formatting
- **IronPython Compatible**: Fully tested with IronPython 3.4.2 on .NET 8.0
- **Bundled DLLs**: Required .NET assemblies included in release package

#### Enhanced Report Features
- **Conditions Section**: Added clouds and stability fields to comprehensive report dialog
- **Occult XML Integration**: Conditions automatically mapped to Occult XML transparency/stability codes
- **Improved Reliability**: More robust Excel manipulation without file corruption risks
- **Better Debugging**: Enhanced logging for troubleshooting report generation

#### Technical Improvements
- New report generators: `tt_report_openize.py` and `na_report_openize.py`
- Template files relocated from development documentation to python folder
- Simplified template management (no more _Template.xlsx placeholders)
- Comprehensive conditions mapping for Occult 4 XML export

#### Installation Requirements
- **Openize SDK DLLs** (included in release):
  - Openize.OpenXMLSDK.dll (~500-800 KB)
  - DocumentFormat.OpenXml.dll (~5-8 MB)
  - DocumentFormat.OpenXml.Framework.dll (~100-200 KB)
- DLLs located in `lib/` folder with installation guide
- No additional downloads required - all dependencies included

#### Breaking Changes
- Excel templates updated to non-placeholder versions
- Old XML-based report generators removed

### Technical Details

**Report Generator Architecture:**
- Uses Openize.Cells.Workbook for Excel file access
- Direct cell writing via row/column coordinates
- Cell references: H27 (clouds), P27 (stability), X27 (other conditions)
- SNR extraction from cell W40 for Occult XML export

**Conditions Mapping:**
- Clouds → Transparency codes: Clear=1, Some Clouds=2, Intermittent Clouds=3, Cloudy=4, Very Cloudy=5, Overcast=6, Other Conditions=7
- Stability: Excellent=1, Good=2, Poor=3
- Automatic mapping for Occult 4 XML <Conditions> line

**Documentation Updates:**
- Architecture documentation reflects Openize implementation
- Removed legacy XML placeholder references
- Updated report generator file names and line counts

---

## Version 0.2.0-beta.1 (January 2026)

**First Public Beta Release**

This is the first public beta release of Occultation Manager. Below is a summary of key features and capabilities.

### Installation & Configuration

#### Automatic Setup
- Release ZIP includes pre-created folder structure: `files/`, `sequences/`, and `files/Reports/` with README guides
- First startup automatically detects installation directory and creates folder structure
- Smart path detection uses Python `__file__`, `sys.argv[0]`, or current directory as fallbacks
- Template files distributed to both main folder (originals) and `files/` folder (working copies)
- Configuration stored in `{install_dir}/files/occultation_config.json`
- Custom paths from previous installations are preserved

#### Simple Installation
- Extract and run - no manual folder creation needed
- Default paths automatically set to installation directory
- Configuration file automatically placed in data folder
- Clear README files in each folder explaining purpose
- Template files ready to customize in files folder

### Core Features

#### Sequence Execution
- **Run Sequences** button for direct multi-sequence execution from Occultation Manager
- **Test Recording** with automatic camera settings preservation and restoration
- SharpCap remains fully responsive during all sequence operations
- Asynchronous execution using SharpCap's `RunAsync()` API

#### Safe Stop Capability
- **Stop button** in Observation Preparation panel
- Confirmation dialog prevents accidental stops
- Automatic camera settings restoration after stop
- Works with both Test Recording and Run Sequences
- Comprehensive cleanup on stop or error

#### Camera Settings Management
- Automatic save before sequence execution
- Non-blocking restoration with stabilization period
- Preserves: binning, exposure, gain, resolution, display levels
- Background thread for camera stabilization (2× exposure time)
- Safe for all camera types and configurations

### Workflow Features

#### Run Sequences
- Select multiple events with checkboxes
- Click Run Sequences button for automated execution
- Sequences run in chronological order automatically
- Real-time progress updates ("Running sequence 2/5: Event Name")
- Eliminates manual .scs file loading in SharpCap Sequencer
- Suitable for multi-event observation sessions

#### Test Recording
- Fully non-blocking - SharpCap remains responsive
- Stop button available during test
- All camera settings automatically saved and restored
- Display levels preserved (stretch settings)
- Safe testing without disrupting your configuration

### Countdown and Timing Features

#### UTC-Based Countdown Functions
Three countdown options for reliable timing in sequences:

**Option 1: Simple Notification** (not recommended - timing risks)
- Basic SharpCap notification with WAIT UNTIL LOCALTIME
- Subject to midnight and next-day event failures

**Option 2: UTC Notification Countdown** (RECOMMENDED)
- Auto-updating notification with formatted countdown
- Displays Days HH:MM:SS format
- Adaptive update rate: 1-minute intervals when >5 min remaining, 1-second when ≤5 min
- Safe for 24+ hour countdowns (no recursion limit issues)
- Color-coded warnings (<5 min amber, <1 min red)
- UTC-based: no timezone or midnight issues
- Safe for late starts and next-day events
- Stoppable via SharpCap Stop button (may take up to 60s when >5 min remaining)

**Option 3: UTC Dialog Countdown**
- Windows dialog with large countdown display
- Adaptive update rate: 1-minute intervals when >5 min remaining, 1-second when ≤5 min
- Safe for 24+ hour countdowns (no recursion limit issues)
- Dedicated Stop button in dialog (may take up to 60s to respond when >5 min remaining)
- Most complex implementation
- Use only if large visible countdown needed

#### WAIT UNTIL LOCALTIME Risks (CRITICAL)
**SharpCap's WAIT UNTIL LOCALTIME commands can cause you to MISS EVENTS:**

1. **No Date Awareness**: SharpCap only knows TIME, not DATE
   - Events after midnight may wait 24 hours
   - Late starts can miss events entirely

2. **Next-Day Event Failure**: 
   - Event at 01:00:00 started at 23:00:00 fails completely
   - Sequencer waits until next day's 01:00:00
   - **Event is missed!**

3. **Daylight Saving Time**: Clock changes cause timing errors

**Recommendation**: Use UTC-based countdown functions (Option 2) for all critical 
observations. These handle midnight, next-day events, and DST correctly.

#### Sequence Execution Methods

**Method 1: SharpCap Sequencer (RECOMMENDED - Safest)**
- Load .scs file directly in SharpCap's Sequencer
- Simplest and most reliable approach
- **Recommended for unattended operation**
- **Recommended for remote operation**
- Fewest points of failure

**Method 2: Occultation Manager Run Sequences (Alternative)**
- Note: It is safer to run sequences directly from SharpCap.
- Note: Combined Sequences can only be run directly from SharpCap.
- Run from Occultation Manager's Run Sequences button
- More complex with additional monitoring layer
- Provides Stop button control
- **Suitable for attended multi-event sessions**
- **Not recommended for unattended operation**
- Additional complexity may reduce reliability

**Reference Files:**
- `countdown python for sequencer.scs` - Ready-to-copy countdown code snippets
- Complete implementation notes and examples included

### Technical Implementation

#### Threading Architecture
- UI Thread (STA): All `RunAsync()` calls, UI updates, SharpCap API calls
- Monitor Thread (MTA): Background status polling, doesn't touch UI directly
- Proper thread marshaling via `Invoke()` for all UI operations
- Background monitoring using Python `threading.Thread`

#### API Usage
- Asynchronous execution using SharpCap's `RunAsync()` API
- Proper thread marshaling to UI thread (STA requirement) for all sequence operations
- Background monitoring threads track sequence execution status
- Comprehensive state management with race condition prevention
- Robust error handling with automatic cleanup in all code paths

### Known Limitations
- Cannot pause sequences (stop and restart only)
- No step-level stop granularity (completes current step before stopping)
- Single sequence execution at a time (no parallel sequences)

### Report Generation (Under Development - Not Approved)

⚠️ **CRITICAL WARNING**: Report generation is still under development and has **NOT** been approved by the NA, TT, or SODIS reporting coordinators. Only TANGRA and AOTA outputs are currently supported. Use with extreme caution and verify all generated data before submission.

#### Current Report Capabilities
- Single comprehensive dialog for workflow efficiency
- Integrates AOTA timing data (D/R times)
- Imports Tangra CSV light curve analysis
- Automatic video format extraction from Tangra CSV files
- Dynamic exposure/integration detection based on timing consistency
- Supports North America (IOTA), Trans-Tasman (RASNZ), and SODIS (IOTA-ES) formats
- Auto-fills observer, telescope, and camera information
- Remembers previous settings for faster workflow

#### Timing Integration Status
- ✅ **Tangra CSV Light Curve Analysis**: Fully integrated
  - Extracts start/end times from Tangra CSV files
  - Populates exposure time and camera acquisition delay
  - Video format sourced from Tangra measurement parameters
  - Automatic HH:MM:SS.SS time formatting
  
- ⚠️ **GPS Flash Timing Analysis**: Not yet integrated into Occultation Manager
  - Functions available in gps-timing-analysis toolkit
  - Available as standalone tool for experts with custom Python code
  - Future integration planned

**Always verify all report data independently before submission to regional coordinators.**

### Documentation

Documentation includes:
- Comprehensive user guide accessible via Help menu
- Installation and configuration instructions
- Workflow guides for all major features
- Countdown and notification options with examples
- WAIT UNTIL LOCALTIME risks and limitations explained
- Sequence execution methods comparison
- `countdown python for sequencer.scs` reference file with ready-to-use code snippets

---

## Support and Feedback

This is a beta release. Please report issues, bugs, and feedback through GitHub Issues.

### Known Issues
- None reported yet

### Reporting Issues
When reporting issues, please include:
- SharpCap version
- Camera type and connection method
- Steps to reproduce the issue
- Any error messages displayed
- Sequence file if relevant (sanitize personal info)
- All cross-thread calls marshaled via `Invoke()` to UI thread

**State Management:**
- Six instance variables track execution state
- Comprehensive cleanup in all error paths
- Race condition prevention via state checks
- Context tracking for appropriate user messages

**Performance:**
- 1-second polling interval for status monitoring
- Minimal CPU overhead
- No UI blocking or freezing
- 2-second delay between sequences in multi-sequence execution

---
---

## Version History

This is the first public beta release. Previous versions were internal development builds not released publicly.

### From 0.1.0 to 0.2.0
1. Replace Python files with updated versions
2. No configuration changes required
3. Existing sequence files continue to work
4. Test the new Run Sequences and Stop button features
5. Enjoy non-blocking operation!

---

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/labstercam/occultation-tools/issues
- Documentation: See README files and Help → User Guide
- Technical Details: See [RunAsync Implementation](python/development documentation/RunAsync_Implementation.md)

---

*Release notes maintained by: Michael Camilleri*  
*Last updated: March 7, 2026*
