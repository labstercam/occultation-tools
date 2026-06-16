# Occultation Manager - Python Modules

## Core Components

### Dummy Event Generator

The Dummy Event Generator creates realistic test occultation events for practice and testing without requiring OccultWatcher Cloud access.

**Key Features:**
- Generates 1-100 test events with configurable timing and spacing
- Events calculated to be visible from your observer location using sidereal time
- Realistic parameters: star magnitudes, durations, coordinates, exposures
- Events added directly to occultations.json alongside real events
- Easily identifiable with TEST-#### IDs (e.g., TEST-1001, TEST-1002)
- Simple deletion using the Delete button in Quick Filters

**Usage:**
1. Click "Generate Dummy Events" in toolbar
2. Configure number of events, start time, interval, and location
3. Click Generate - events appear immediately in the event grid
4. Use for testing sequences, workflows, and equipment setup
5. Select and delete dummy events when no longer needed

See [DUMMY_EVENTS_FEATURE.md](development documentation/DUMMY_EVENTS_FEATURE.md) for complete documentation.

### Report Generation System

⚠️ **Status**: Report generation is still under development and has NOT been approved by North America, Trans-Tasman, or SODIS reporting coordinators.

The Occultation Manager includes comprehensive report generation (Excel for NA/TT and text for SODIS) with integrated Tangra light curve analysis.

**Current Integration Status**:
- ✅ **Tangra CSV light curve analysis**: Fully integrated for video format detection, exposure/integration mode, and frame timing
- ✅ **SODIS / IOTA-ES report generation**: Integrated as `IOTA-ES / SODIS (Form 2.03)` in the comprehensive report workflow
- ⚠️ **GPS flash timing analysis**: NOT YET INTEGRATED - Available in `gps-timing-analysis` toolkit as standalone tools for expert users with custom Python code
- 📅 **Future Plans**: Integration of GPS flash timing analysis (1PPS detection, timestamp offset, rolling shutter characterization) into report workflow

**Excel Report Implementation**:
- Uses Openize.OpenXML-SDK for direct Excel manipulation via .NET
- IronPython compatible through CLR interop
- Direct cell access preserves Excel data validation and formulas
- No external Python dependencies required

### Sequence Execution (Async Implementation)

The Occultation Manager implements non-blocking sequence execution using SharpCap's `RunAsync()` API.

**Key Files:**
- `main_gui.py` - Lines 2383-3046: Async sequence execution implementation
- `development documentation/RunAsync_Implementation.md` - Comprehensive technical documentation

**Architecture:**
- **Test Recording**: UI thread calls `RunAsync()`, separate monitor thread polls status
- **Run Sequences**: Background thread manages loop, marshals `RunAsync()` to UI thread
- **Stop Button**: Safe cancellation with confirmation and automatic cleanup
- **Camera Settings**: Automatic save/restore with non-blocking stabilization

**Critical Threading Requirement:**
All `RunAsync()` calls must be marshaled to the UI thread (STA apartment state) even when called from background threads. SharpCap sequence steps that manipulate UI components (display stretch, notifications, camera controls) require STA threading.

**Implementation Pattern:**
```python
# WRONG - Fails with STA error from background thread:
task = self.sharpcap.Sequencer.RunAsync()

# CORRECT - Marshal to UI thread:
self.Invoke(lambda: self.sharpcap.Sequencer.RunAsync())
```

**State Management:**
- `_sequence_running`: Master execution flag
- `_sequence_monitoring_thread`: Background monitor thread reference
- `_sequence_saved_settings`: Camera settings backup dictionary
- `_current_sequence_path`: Active sequence file path(s)
- `_sequence_stopped_by_user`: Stop request flag
- `_sequence_context`: Context tracking for appropriate messaging

**Benefits:**
- SharpCap remains fully responsive during sequence execution
- Safe stop capability with automatic cleanup
- Camera settings preservation and restoration
- All sequence operations work (display, notifications, controls)
- Robust error handling with comprehensive state cleanup

See [RunAsync_Implementation.md](development documentation/RunAsync_Implementation.md) for complete technical details.

### Countdown and Timing Functions

**countdown python for sequencer.scs** - Ready-to-use countdown code snippets

Provides three options for reliable countdown timing in SharpCap sequences.

**CRITICAL: WAIT UNTIL LOCALTIME Risks**

SharpCap's built-in `WAIT UNTIL LOCALTIME` and `WAIT UNTIL AFTER LOCALTIME` commands 
have serious limitations that can cause missed events:

1. **No Date Awareness**: Only knows TIME, not DATE
   - Late starts after midnight may wait 24 hours
   - Next-day events will fail completely

2. **Next-Day Event Failure**:
   - Event at 01:00:00 after midnight, started at 23:00:00 before midnight
   - Sequencer sees 01:00:00 < 23:00:00, waits until next day
   - **Event is missed entirely**

3. **Daylight Saving Time**: Clock changes cause 1-hour timing errors

**Three Countdown Options:**

**Option 1: Simple Notification (NOT RECOMMENDED)**
- Uses SharpCap's SHOW NOTIFICATION + WAIT UNTIL LOCALTIME
- Subject to all local time problems above
- Can miss events if started late or after midnight

**Option 2: UTC Notification Countdown (RECOMMENDED)**
- Auto-updating notification with formatted countdown (Days HH:MM:SS)
- Adaptive update rate: 1-minute intervals when >5 min remaining, 1-second when ≤5 min
- Safe for 24+ hour countdowns (no recursion limit issues)
- Color-coded warnings: ⚠️ <5 min, 🔴 <1 min
- UTC-based: handles midnight, next-day events, DST correctly
- Stoppable via SharpCap Stop button (may take up to 60s when >5 min remaining)
- Safe for late starts (continues immediately if time passed)
- Most reliable option for critical observations

**Option 3: UTC Dialog Countdown**
- Windows dialog with large countdown display
- Adaptive update rate: 1-minute intervals when >5 min remaining, 1-second when ≤5 min
- Safe for 24+ hour countdowns (no recursion limit issues)
- Dedicated Stop button in dialog (may take up to 60s to respond when >5 min remaining)
- Most complex implementation
- Additional failure points (Windows forms)
- Use only if large visible countdown needed

**Implementation Pattern:**
```python
# Define functions at start of sequence (one-line Python code):
RUN PYTHON CODE "import datetime as dt; import time; import clr; clr.AddReference('System'); from System import Action"
RUN PYTHON CODE "def format_time(seconds): ..."
RUN PYTHON CODE "def countdown_utc(date_string, message, ...): ..."

# Use in sequence with UTC time tags:
RUN PYTHON CODE "countdown_utc('{goto_time}', 'Waiting for GOTO')"
```

**Sequence Execution Methods:**

**Method 1: SharpCap Sequencer (RECOMMENDED - Safest)**
- Load .scs file directly in SharpCap's Sequencer
- Click Play to start
- Simplest and most reliable approach
- **Recommended for unattended operation**
- **Recommended for remote operation**
- Fewest points of failure

**Method 2: Occultation Manager Run Sequences (Alternative)**
- Run from Occultation Manager's Run Sequences button
- More complex with additional monitoring layer
- Provides Stop button control during execution
- **Suitable for attended multi-event sessions**
- **Not recommended for unattended operation**
- Additional complexity may reduce reliability

**Testing:**
ALWAYS test countdown functions before critical observations:
1. Create test sequence with 2-minute countdown
2. Verify countdown displays and updates correctly
3. Test stop functionality
4. Test late start (start after countdown time passed)
5. Verify sequence continues after countdown

**File Reference:**
Complete code snippets and implementation notes in `countdown python for sequencer.scs`

#### Report Generators

**na_report_openize.py** - North America (IOTA V5.6.12r, Openize)
- Uses template: `NorthAmerica_AstReportForm_V5.6.12r.xlsx`
- Openize-based cell population preserving Excel validation/formulas
- **Video format and exposure/integration** sourced from Tangra CSV analysis
- Filename format: `YYYYMMDD_asteroidnumber_asteroidname_starcatalog_starnumber-surname_station.xlsx`

**tt_report_openize.py** - Trans-Tasman (RASNZ V4.1.2.G, Openize)
- Uses template: `RASNZ_AstReporttForm_V4.1.2.G.xlsx`
- Openize-based cell population preserving Excel validation/formulas
- **Video format and exposure/integration** sourced from Tangra CSV analysis

**sodis_report_text.py** - SODIS / IOTA-ES (Form 2.03, Text)
- Uses template: `IOTA-ES_report.txt`
- Writes plain-text report with SODIS key order and naming
- Template resolved from installed resources master reports folder
- Filename format: `YYYYMMDD_asteroidNo_starCatalog_starNumber.txt`
- Positive/Unsure uses AOTA D/R timings; Negative writes `D: M` and `R: M`

**occult4_export.py** - Occult 4 XML Export (Version 2.15+)
- Generates OBS.XML files compatible with Occult 4 software
- Integrated into report workflow alongside NA, TT, and SODIS reports
- Uses data already collected from AOTA reports and Tangra analysis
- Exports single observation data in standardized XML format for IOTA

**Key Features**:
- Automatic filename generation matching observation details
- Precision coordinate handling (J2000 vs Apparent RA/Dec)
- **Dynamic data extraction** from Tangra CSV files (video format, timing parameters)
- Telescope aperture conversion (mm to cm, rounded to integer)
- Variable precision time formatting (removes trailing zeros)
- Timing accuracy from AOTA report uncertainties
- Observer location extraction from geocoded data
- Equipment type code mapping (telescope, camera, timing)

**Data Sources**:
1. AOTA Report: D/R times, uncertainties, SNR
2. Tangra CSV: Observation start/end times, exposure, camera delay
3. Event data: Star/asteroid coordinates, prediction times
4. Configuration: Observer details, telescope/camera specifications
5. Occelmnt data: Preferred source for astrometric data

**Exported Data Structure**:
- Star section: J2000 and apparent coordinates, magnitudes, uncertainties
- Asteroid section: Object details, motion vectors, ephemeris source
- Date section: Observation date in yyyy mm dd format
- Observations section: Observer ID, prediction, D/R event times with accuracies
- Conditions section: Seeing, transparency, SNR

**Format Notes**:
- Time format: `H M SS.S` (no leading zeros, variable decimal precision)
- Coordinate format: `±ddd mm ss.s` (1 decimal place for seconds)
- Telescope aperture: Integer cm (converted from mm configuration)
- Plot codes: Space character for included events
- All timing uses observed AOTA times when available, falls back to predictions

#### Timing Integration

**light_curves_iron.py** - IronPython-Compatible Timing Analysis
- Reads Tangra CSV light curve files
- Extracts observation timing statistics and video format
- Compatible with IronPython (no pandas/numpy/scipy)
- Uses only Python standard library (csv, datetime)

**Key Functions**:
```python
read_tangra_csv_iron(file_path)
# Returns: filename, header details, apertures, light curve data, video_format

analyse_timestamps_iron(light_curve_data)
# Returns: start_time, end_time, tdelta_median, tdelta_std, video_format, exposure_integration

get_observation_summary(tangra_csv_path)
# Convenience wrapper combining read and analysis
```

**Extracted Data**:
- Start time (HH:MM:SS.SS format)
- End time (HH:MM:SS.SS format)
- Exposure time (median frame delta in seconds)
- Camera acquisition delay (from measurement parameters table, rows 7-8)
- **Video format** (from measurement parameters: ADV→ADVS, AAV variants, PAL/CCIR, NTSC/EIA, SER, AVI, MP4, FITS)
- **Exposure/Integration type** (calculated from timing consistency)

**Tangra CSV Parsing**:
- **Lines 7-8 (0-indexed 6-7)**: Measurement parameters header and data
  - Extracts "Video File Format" column (handles leading spaces in column names)
  - Extracts "Acquisition Delay (ms)" column
- Maps Tangra format codes to report-standard format names

**Report Fields Populated**:
```
{{STARTED_OBSERVING_HOURS}}
{{STARTED_OBSERVING_MINUTES}}
{{STARTED_OBSERVING_SECONDS}}
{{STOPPED_OBSERVING_HOURS}}
{{STOPPED_OBSERVING_MINUTES}}
{{STOPPED_OBSERVING_SECONDS}}
{{INTEGRATION}}                    # Exposure in seconds
{{VIDEO_FORMAT}}                   # Video format from Tangra CSV
{{EXPOSURE_INTEGRATION}}           # Exposure or Integration based on timing consistency
{{CAMERA_DELAY_CORRECTION}}        # Acquisition delay in seconds
{{CORRECTIONS_APPLIED}}            # Set to "yes" when Tangra data present
```

#### AOTA Integration

**aota_parser.py** - Parse AOTA XML Files
- Extracts D/R timing events from .aota.xml files
- Preserves precision using string representations
- Handles multiple events per file

**aota_report_parser.py** - Parse AOTA Report Text Files (NEW)
- IronPython-compatible parser using only Python standard library (re module)
- Parses plain text AOTA_Report.txt files generated by AOTA software
- Extracts timing data, uncertainties, and signal-to-noise ratios

**Key Functions**:
```python
parse_aota_report(file_path)
# Returns: dict with events array, or None on error

get_event_summary(parsed_data, event_number)
# Returns: dict with d_hours/d_minutes/d_seconds/d_uncertainty,
#          r_hours/r_minutes/r_seconds/r_uncertainty, snr
```

**Extracted Data from AOTA Reports**:
- Disappearance time: Hours, Minutes, Seconds (H M S.s format)
- Disappearance uncertainty: ±error in seconds
- Reappearance time: Hours, Minutes, Seconds (H M S.s format)
- Reappearance uncertainty: ±error in seconds
- Signal-to-Noise Ratio: Average SNR at event locations

**Report Fields Populated**:
```
{{AOTA_D_HOURS}}
{{AOTA_D_MINUTES}}
{{AOTA_D_SECONDS}}
{{AOTA_D_ERROR}}                   # ±uncertainty in seconds (1 decimal place)
{{AOTA_R_HOURS}}
{{AOTA_R_MINUTES}}
{{AOTA_R_SECONDS}}
{{AOTA_R_ERROR}}                   # ±uncertainty in seconds (1 decimal place)
{{SNR}}                            # Signal-to-noise ratio (1 decimal place)
{{OTHER_DETECTOR_RELATED_INFO}}    # Camera other_info field
```

**File Format Support**:
- Accepts AOTA_Report.txt files with "Event #N" sections
- Parses "Event time in UTC" with "D: H M S.s ±error" and "R: H M S.s ±error" format
- Extracts "SN at event locations" with "Ave: value" format
- Handles multi-event files (prompts user to select specific event)

**Error Handling**:
- Returns None on file I/O errors (logged to console)
- Validates all timing components before use
- Try/except blocks for type conversions
- Graceful degradation on malformed data

### User Interface

**comprehensive_report_dialog.py** - Streamlined Report Generation
Single dialog combining:
1. Report format selection (NA/TT)
2. Equipment selection (telescope/camera)
3. Observation type (Positive/Negative/Unsure)
4. File selection (AOTA XML, AOTA Report, and Tangra CSV)

**Features**:
- Three-column file selection (AOTA XML, AOTA Report, Tangra CSV)
- Settings persistence (remembers last report type and folder)
- Auto-selection of first available files
- Flexible validation (AOTA XML OR AOTA Report required for Positive/Unsure)
- Time comparison with warning when both AOTA sources differ (>0.1s tolerance)
- Multi-event selection dialog for AOTA Reports with multiple events
- Real-time status feedback

**Other Dialogs**:
- `aota_dialogs.py` - AOTA event selection and observation type
- `equipment_dialogs.py` - Telescope and camera management
- `gui_dialogs.py` - Location confirmation and utility dialogs

### Configuration Management

**config.py** - Settings Persistence
Manages all configuration with JSON storage (`occultation_config.json`):
- Observer information
- Multiple telescopes and cameras
- Active equipment selection
- Report generation preferences (type, folder)
- OWC credentials and API settings
- Event retention period (days_to_retain_events: 1-400, default 14)
- Default camera gain (default_gain: 0-600, default 450)

**Configuration Settings**:
- `get_days_to_retain_events()` / `set_days_to_retain_events(days)` - Event retention period
- `get_default_gain()` / `set_default_gain(gain)` - Default camera gain for new events
- `validate_config()` - Validates retention days (1-400 range) and other settings

### Event Management

**events.py** - OccultationEvent Class
Core event data model with automatic calculations and customizable overrides:

**Calculated Properties**:
- `exposure_ms` - Calculated from magnitude drop (brighter = shorter exposure)
- `gain_value` - Uses default_gain from configuration (default 450)
- `recording_duration` - Calculated as (uncertainty × 8) + (max_duration × 2)
- `start_time`, `end_time`, `goto_time` - Derived from recording duration

**Custom Overrides**:
- `custom_exposure` - Override calculated exposure (1-10000 ms)
- `custom_gain` - Override default gain (0-600)
- `custom_recording_duration` - Override calculated duration (10-3600 seconds)

**Key Methods**:
- `set_custom_exposure(value_ms)` - Sets custom exposure in milliseconds
- `set_custom_gain(value)` - Sets custom gain value
- `set_custom_recording_duration(value_seconds)` - Sets custom duration and recalculates times
- `has_custom_exposure()`, `has_custom_gain()`, `has_custom_recording_duration()` - Check custom flags
- `get_exposure()` - Returns exposure in seconds for template formatting
- `get_gain()` - Returns gain value for template formatting
- `_calculate_derived_values()` - Recalculates all timing when recording duration changes

**Event Merging with Retention**:
- `merge_occultation_lists(latest, existing, retention_days)` - Merges event lists
- Uses cutoff date based on retention_days setting
- Preserves custom settings (exposure, gain, recording duration) for existing events
- Removes events older than cutoff date

**GUI Components** (`gui_components.py`, `gui_dialogs.py`):
- EventsDataGrid displays Exposure (ms), Gain, Recording Time (s) with * for custom values
- Double-click on these columns opens Edit Settings dialog
- ExposureEditDialog (Edit Settings) - Combined dialog for exposure/gain/duration customization
- Configuration Dialog includes Days to Retain Events (File Paths) and Default Gain (User Settings)
- User Settings tab has individual 'Explain' buttons for each setting showing formulas and examples

**Sequence Generation** (`utils.py`, `templates.py`):
- Generates SharpCap sequences with {exposure}, {gain}, {recording_duration} variables
- Templates use Python string.format() with event-specific values
- Calculated or custom values automatically substituted

### Utility Modules

- `aota_parser.py` - Parse AOTA XML timing files
- `aota_report_parser.py` - Parse AOTA Report text files (D/R times, uncertainties, SNR)
- `templates.py` - SharpCap sequence template management
- `theme.py` - Dark/light mode theme support
- `utils.py` - Common utility functions

## Folder Structure

**Production Files** (python/ folder root):
- 23 Python modules (.py files)
- 5 SharpCap sequence templates (.txt files)
- 2 Excel report templates (.xlsx files)
- 1 application icon (.ico file)

**Development Files** (excluded from release):
- `testing/` - Active verification scripts (`verify_openize_sharpcap.py`, `test_openize_integration.py`, `test_openize_tt_report.py`)
- `testing/` may also contain archived legacy/one-off scripts when retained for reference (not part of the active testing workflow)
- `development documentation/` - Implementation notes, bug tracking, and technical specifications