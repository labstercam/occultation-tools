# Occultation Manager - Architecture Documentation

## Overview

Occultation Manager is a Windows desktop application that automates the workflow for observing asteroid occultations using SharpCap. It downloads event predictions, generates observation sequences, manages equipment configurations, executes automated observations, and generates standardized reports.

**Key Technologies:**
- Python 3.x with IronPython/Pythonnet for .NET interop
- Windows Forms for GUI
- SharpCap COM automation for camera and telescope control
- OccultWatcher Cloud (OWCloud) REST API for event data
- Excel/XML for report generation

**Total Code Size:** ~14,950 lines of Python across 23 modules

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                         MAIN APPLICATION WINDOW                                 │
│                      OccultationManagerGUI (Form)                               │
│                          main_gui.py (3,286 lines)                              │
│                                                                                 │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │ MenuStrip: File | View | Tools | Help                                     │  │
│  ├───────────────────────────────────────────────────────────────────────────┤  │
│  │ Toolbar: [Download] [Generate] [Run] [Test] [Stop]                        │  │
│  ├───────────────────────────────────────────────────────────────────────────┤  │
│  │ EventsDataGrid (gui_components.py)                                        │  │
│  │   Columns: [ ] Event | Station | Date/Time | Mag | Exp | Gain | Status    │  │
│  ├───────────────────────────────────────────────────────────────────────────┤  │
│  │ Quick Actions | Observation Prep | Status Bar                             │  │
│  └───────────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────────────────────────┘
                              │
      ┌───────────────────────┼───────────────────────┬───────────────────────┐
      │                       │                       │                       │
      ▼                       ▼                       ▼                       ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│ EVENT MGMT      │  │ SEQUENCE FLOW   │  │ REPORT FLOW     │  │ CONFIGURATION   │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘


═══════════════════════════════════════════════════════════════════════════════════
EVENT MANAGEMENT DIALOGS (gui_dialogs.py - 1,856 lines)
═══════════════════════════════════════════════════════════════════════════════════

Download Events
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LocationConfirmDialog                                              │
│  - Latitude/longitude input                                         │
│  - Elevation & location name                                        │
│  - Radius & date range                                              │
│                                                                     │
│  Purpose: Confirm/edit observer location before downloading events  │
└─────────────────────────────────────────────────────────────────────┘
      │
      ▼
   [Download from OWCloud API] → Events displayed in grid


Edit Event Settings
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ExposureEditDialog                                                 │
│  - Custom exposure (ms)                                             │
│  - Custom gain                                                      │
│  - Custom recording duration                                        │
│  - Reset to calculated defaults                                     │
│                                                                     │
│  Purpose: Edit camera settings for event (double-click columns)     │
└─────────────────────────────────────────────────────────────────────┘


View Event Details
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  EventDetailsDialog                                                 │
│  - Object & star information                                        │
│  - Coordinates & timing                                             │
│  - Observation parameters                                           │
│  - OWCloud link                                                     │
│                                                                     │
│  Purpose: Display complete event info (double-click event name)     │
└─────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════════
SEQUENCE GENERATION WORKFLOW
═══════════════════════════════════════════════════════════════════════════════════

Generate Sequences (for selected events)
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  TemplateSelectionDialog (gui_dialogs.py)                           │
│  - Simple notification                                              │
│  - UTC with countdown                                               │
│  - Local time with countdown                                        │
│  - Browse custom templates                                          │
│                                                                     │
│  Purpose: Choose sequence template type and countdown format        │
└─────────────────────────────────────────────────────────────────────┘
      │
      ▼
[Generate .scs files] → Sequences saved to sequences/ folder


═══════════════════════════════════════════════════════════════════════════════════
REPORT GENERATION WORKFLOW
═══════════════════════════════════════════════════════════════════════════════════

Generate Report (for single event)
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  LocationConfirmDialog (gui_dialogs.py)                             │
│  - Latitude/longitude input                                         │
│  - Elevation & location name                                        │
│  - Same as download dialog                                          │
│                                                                     │
│  Purpose: Confirm/edit observation location for report              │
└─────────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│  ComprehensiveReportDialog (comprehensive_report_dialog.py - 686 lines)         │
│  ┌───────────────────────────────────────────────────────────────────────────┐  │
│  │ 1. Report Format Selection                                                │  │
│  │    ○ IOTA North America (V5.6.12r)                                        │  │
│  │    ○ Trans-Tasman / RASNZ (V4.1.2.G)                                      │  │
│  ├───────────────────────────────────────────────────────────────────────────┤  │
│  │ 2. Equipment Selection                                                    │  │
│  │    Telescope: [dropdown] [Manage...] ─────────┐                           │  │
│  │    Camera:    [dropdown] [Manage...] ─────────┤                           │  │
│  ├───────────────────────────────────────────────┼───────────────────────────┤  │
│  │ 3. Observation Type                           │                           │  │
│  │    ○ Positive   ○ Negative   ○ Unsure         │                           │  │
│  ├───────────────────────────────────────────────┼───────────────────────────┤  │
│  │ 4. Data Import (Optional)                     │                           │  │
│  │    Folder: [Browse...]                        │                           │  │
│  │    ┌──────────────────────────────────────┐   │                           │  │
│  │    │ AOTA XML Files        [0 files]      │   │                           │  │
│  │    │ [listbox]                            │   │                           │  │
│  │    ├──────────────────────────────────────┤   │                           │  │
│  │    │ Tangra CSV Files      [0 files]      │   │                           │  │
│  │    │ [listbox]                            │   │                           │  │
│  │    ├──────────────────────────────────────┤   │                           │  │
│  │    │ AOTA Report Files     [0 files]      │   │                           │  │
│  │    │ [listbox]                            │   │                           │  │
│  │    └──────────────────────────────────────┘   │                           │  │
│  └───────────────────────────────────────────────┘                           │  │
│                                                                                │  │
│                     If AOTA XML selected & multiple eve──────────┐            │  │
│              │  AOTAEventSelectionDialog (aota_dialogs.py)       │            │  │
│              │  - List of events from AOTA file                  │            │  │
│              │  - Select which event to use                      │            │  │
│              └───────────────────────────────────────────────────┘            │  │
│                                                                                │  │
│         [Manage Telescope...] ───────────────────┐                            │  │
│                                                  │                            │  │
│                                                  ▼                            │  │
│              ┌───────────────────────────────────────────────────┐            │  │
│              │  TelescopeManagerDialog (equipment_dialogs.py)    │            │  │
│              │  - Add/Edit/Delete telescopes                     │            │  │
│              │  - Name, Aperture, Focal Ratio, Type              │            │  │
│              └───────────────────────────────────────────────────┘            │  │
│                                                                                │  │
│         [Manage Camera...] ──────────────────────┐                            │  │
│                                                  │                            │  │
│                                                  ▼                            │  │
│              ┌───────────────────────────────────────────────────┐            │  │
│              │  CameraManagerDialog (equipment_dialogs.py)       │            │  │
│              │  - Add/Edit/Delete cameras                        │            │  │
│              │  - Detector, Timing, Report Type, Occult4 codes   │            │  │
│              └───────────────────────────────────────────────────┘            │  │
│                                                                                │  │
│  [Generate Report]                                                             │  │
└────────────────────────────────────────────────────────────────────────────────┘
      │
      ▼
[Report saved & opened in Excel]


═══════════════════════════════════════════════════════════════════════════════════
CONFIGURATION DIALOGS
═══════════════════════════════════════════════════════════════════════════════════

Tools Menu → Settings
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  ConfigurationDialog (gui_dialogs.py)                               │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │ Tabs: Paths | Recording | Observer | API                     │  │
│  │                                                               │  │
│  │ Paths Tab:                                                    │  │
│  │   - Data folder, sequences folder                            │  │
│  │   - Events files, report templates                           │  │
│  │                                                               │  │
│  │ Recording Tab:                                                │  │
│  │   - Base duration, GOTO lead time                            │  │
│  │   - Magnitude/exposure reference                             │  │
│  │   - Default gain, sync mount                                 │  │
│  │   - Display UTC/Local preference                             │  │
│  │                                                               │  │
│  │ Observer Tab:                                                 │  │
│  │   - Name, email, address, phone, fax                         │  │
│  │   - For populating report forms                              │  │
│  │                                                               │  │
│  │ API Tab:                                                      │  │
│  │   - OWCloud email & password                                 │  │
│  └───────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘


Equipment Menu → Manage Equipment
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  EquipmentSelectionDialog (equipment_dialogs.py)                    │
│  - Active telescope dropdown                                        │
│  - Active camera dropdown                                           │
│  - [Manage Telescopes...] → TelescopeManagerDialog                 │
│  - [Manage Cameras...] → CameraManagerDialog                       │
└─────────────────────────────────────────────────────────────────────┘


Help Menu → Help Topics
      │
      ▼
┌─────────────────────────────────────────────────────────────────────┐
│  HelpDialog (help.py - 911 lines)                                   │
│  - Quick Start Guide                                                │
│  - Troubleshooting                                                  │
│  - FAQ                                                               │
│  - Rich text formatting with links                                  │
└─────────────────────────────────────────────────────────────────────┘


═══════════════════════════════════════════════════════════════════════════════════
BACKEND ARCHITECTURE
═══════════════════════════════════════════════════════════════════════════════════

┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│   Events     │  │   Config     │  │  Sequences   │  │   Reports    │
│   Manager    │  │   Manager    │  │   Runner     │  │  Generators  │
│ (events.py)  │  │ (config.py)  │  │(sequence_    │  │ (na_report   │
│  968 lines   │  │  611 lines   │  │ runner.py)   │  │  tt_report   │
│              │  │              │  │  119 lines   │  │  occult4)    │
└──────┬───────┘  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘
       │                 │                 │                 │
       │                 │                 │                 │
       ▼                 ▼                 ▼                 ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│  OWCloud     │  │    JSON      │  │  .scs Files  │  │ .xlsx Report │
│  REST API    │  │   Config     │  │  Templates   │  │  XML Export  │
│   (HTTP)     │  │   Storage    │  │  (SharpCap)  │  │  (Occult4)   │
└──────────────┘  └──────────────┘  └──────────────┘  └──────────────┘
```

---

## Core Components

### 1. Main Entry Point (`main.py` - 120 lines)
**Responsibilities:**
- Application bootstrap and initialization
- Single instance check (prevents multiple windows)
- Version compatibility check (requires SharpCap 4.1.13+)
- Creates and wires up configuration, theme, and GUI instances

**Key Functions:**
- `main()` - Entry point, creates singleton GUI instance

**Dependencies:** config.py, theme.py, main_gui.py

---

### 2. GUI Layer

#### Main GUI (`main_gui.py` - 3,286 lines)
**Responsibilities:**
- Primary application window with event grid, controls, and menus
- Event selection and display
- Sequence generation coordination
- Equipment management UI
- Report generation workflow
- SharpCap integration for test recording and sequence execution
- DPI scaling support for high-resolution displays

**Key Classes:**
- `OccultationManagerGUI(Form)` - Main window

**Key Methods:**
- `setup_ui()` - Creates all UI controls and layout
- `load_initial_data()` - Loads events from cache on startup
- `download_events_click()` - Downloads events from OWCloud
- `generate_sequences_click()` - Creates .scs files for selected events
- `run_sequences_click()` - Executes sequences via SharpCap
- `test_recording_click()` - Test camera with settings preservation
- `generate_report_click()` - Launches report generation dialog

**UI Structure:**
```
MenuStrip (File, View, Tools, Help)
    │
Toolbar (Download, Generate, Run, Test, Stop buttons)
    │
Event Grid (DataGridView with checkboxes, event details)
    │
Bottom Panel
    ├─ Quick Actions Group (buttons for common tasks)
    ├─ Observation Preparation Group (equipment selection)
    └─ Status Bar (progress messages)
```

**Threading Model:**
- GUI runs on main thread
- SharpCap sequence monitoring runs on background thread
- Async execution using Python threading module
- Invoke() pattern for cross-thread UI updates

#### Dialog Windows (`gui_dialogs.py` - 1,856 lines)
**Key Dialogs:**
- `ExposureEditDialog` - Edit exposure/duration settings for events
- `EventDetailsDialog` - View full event details
- `ConfigurationDialog` - Application settings and paths
- `TemplateSelectionDialog` - Choose sequence countdown template
- `LocationConfirmDialog` - Confirm observation location on download

#### Equipment Dialogs (`equipment_dialogs.py` - 1,164 lines)
**Key Dialogs:**
- `TelescopeManagerDialog` - Add/edit telescope configurations
- `CameraManagerDialog` - Add/edit camera configurations  
- `EquipmentSelectionDialog` - Select active telescope and camera

#### GUI Components (`gui_components.py` - 280 lines)
**Key Components:**
- `EventsDataGrid(DataGridView)` - Custom data grid for events with checkbox column

---

### 3. Event Management

#### Events Module (`events.py` - 968 lines)
**Responsibilities:**
- OWCloud API integration for downloading event predictions
- Event data processing and caching
- Event merging and deduplication
- Event selection and filtering management

**Key Classes:**

**`EventProcessor`** - Static utility methods for event operations
- `load_occultations()` - Load events from JSON cache
- `save_occultations()` - Save events to JSON cache
- `merge_occultation_lists()` - Merge and deduplicate event lists
- `get_owc_events()` - HTTP request to OWCloud API with auth
- `update_ow_cloud_events()` - Fetch user's announced events

**`OccultationEvent`** - Data model for a single occultation event
- Stores all event data from OWCloud (coordinates, timing, magnitudes)
- Computes local time strings and datetime objects from UTC times
- Manages custom exposure/gain/duration overrides
- Methods: `get_asteroid_display_name()`, `get_coordinates_string()`, `get_status_info()`, `set_custom_exposure()`, `has_custom_exposure()`, etc.

**`OccultationManager`** - High-level event management interface
- `download_events_from_cloud()` - Download from OWCloud and merge with cache
- `load_events_from_files()` - Load events from JSON cache
- `get_filtered_events()` - Get events filtered by station name
- `set_station_filter()` - Apply station name filter
- `select_all_events()` / `select_no_events()` - Event selection management
- `sort_events()` - Sort events by event time

**OWCloud API Integration:**
```python
# Endpoint: https://www.occultwatcher.net:443/api2/v1/events/details-list
# Authentication: Basic Auth (email:password)
# Parameters: lat, lon, radius_km, days_ahead, min_alt, max_sun_alt
# Returns: JSON array of event predictions
```

**Data Flow:**
```
OWCloud API → download_events() → OccultationEvent objects → 
    → merge with cached events → save to JSON → display in grid
```

---

### 4. Configuration Management

#### Config Module (`config.py` - 611 lines)
**Responsibilities:**
- Persistent configuration storage (JSON)
- File path management
- Equipment configurations (telescopes, cameras)
- Observer information
- API credentials and settings
- First-run setup with folder structure creation

**Key Class:**
**`ConfigManager`** - Central configuration management

**Configuration Categories:**
1. **User Credentials**
   - OWCloud email/password for API access

2. **File Paths**
   - `my_file_folder` - Data storage location (auto-detected)
   - `sequence_path` - Where .scs sequence files are stored
   - `my_occultations_file` - Main event cache
   - `my_latest_occultations_file` - Recent downloads

3. **Recording Parameters**
   - `base_duration` - Recording duration (seconds)
   - `goto_lead_time` - Time before event to start (seconds)
   - `mag_for_40ms_exposure` - Magnitude reference for exposure calculation
   - `default_gain` - Default camera gain
   - `sync_mount` - Whether to sync telescope mount
   - `display_utc` - Show UTC vs local time

4. **Equipment Definitions**
   - `telescopes` - List of telescope configurations
   - `cameras` - List of camera configurations
   - `active_telescope_id` / `active_camera_id` - Currently selected equipment

5. **Observer Information** (for reports)
   - Name, email, address, phone
   - Used to populate report forms

**Storage:**
- Location: `{install_dir}/files/occultation_config.json`
- Format: JSON with nested dictionaries
- Auto-created on first startup
- Preserves custom paths across updates

**Key Methods:**
- `load_config()` - Read from JSON file
- `save_config()` - Write to JSON file
- `get_full_file_path()` - Resolve relative paths
- `add_telescope()` / `get_telescope()` - Equipment management
- `add_camera()` / `get_camera()` - Camera management
- `get_observer_name()` / `get_observer_email()` - Report data access

**Path Detection:**
```python
# Installation directory auto-detection (first-run):
1. Try __file__ (script location)
2. Try sys.argv[0] (executable path)  
3. Fallback to os.getcwd() (current directory)

# Folder structure created automatically:
{install_dir}/
    ├── files/                    # Data storage
    │   ├── occultation_config.json
    │   ├── occultations.json
    │   ├── Reports/             # Generated reports
    │   └── *.txt templates      # Working copies
    └── sequences/               # Generated .scs files
```

---

### 5. Sequence Generation

#### Sequence Runner (`sequence_runner.py` - 119 lines)
**Responsibilities:**
- Generate SharpCap sequence (.scs) files from events and templates
- Execute sequences via SharpCap COM API
- Multi-sequence orchestration

**Key Class:**
**`SequenceRunner`** - Sequence execution manager

**Key Methods:**
- `run_sequences()` - Run multiple sequences in chronological order
- `run_single_sequence()` - Execute one sequence file via SharpCap

**Sequence Execution Flow:**
```
1. Filter events for future GOTO times
2. Sort events by GOTO time (chronological)
3. For each event:
   a. Build sequence filename (date + object name)
   b. Resolve .scs file path
   c. Call SharpCap.Sequencer.RunSequenceFile()
   d. Monitor completion status
4. Report completion/errors
```

#### Templates Module (`templates.py` - 45 lines)
**Responsibilities:**
- Template file management
- Data tag replacement in sequence files

**Template System:**
```
Template files contain data tags in format {{tag_name}}
Available tags:
  {{goto_time}}       - UTC time to start GOTO
  {{goto_time_local}} - Local time for GOTO
  {{start_time}}      - UTC recording start time
  {{start_time_local}}- Local recording start time
  {{duration}}        - Recording duration (seconds)
  {{object_name}}     - Asteroid/object name
  {{star_name}}       - Target star identifier
```

**Template Types:**
1. **Simple Notification** - Basic WAIT UNTIL with notification
2. **UTC Notification Countdown** - Auto-updating countdown display
3. **UTC Dialog Countdown** - Windows dialog with stop button

**Generated .scs Files:**
```
Stored in: {install_dir}/sequences/
Filename format: YYYYMMDD (12345) ObjectName.scs
Example: 20251223 (165690) 2001 PA3.scs
```

---

### 6. Report Generation

#### Report Generators
Three specialized report generators create Excel-based observation reports by filling standardized templates.

**Base Class (`report_generator_base.py` - 94 lines):**
- `ReportGeneratorBase` - Common functionality for all report types
- XML placeholder replacement in Excel workbooks
- Star catalog parsing and mapping
- Filename generation

**North America Reports (`na_report.py` - 647 lines):**
- `NAReportGenerator` - IOTA North American report format
- Template: `NorthAmerica_AstReportForm_V5.6.12r_Template.xlsx`
- Fields: Observation type, event details, equipment, timing, SNR

**Trans-Tasman Reports (`tt_report.py` - 679 lines):**
- `TTReportGenerator` - RASNZ (Royal Astronomical Society NZ) format  
- Template: `RASNZ_AstReporttForm_V4.1.2.G_Template.xlsx`
- Fields: Similar to NA with regional differences

**Occult 4 XML Export (`occult4_export.py` - 949 lines):**
- `Occult4Exporter` - Occult 4 XML format (Version 2.15)
- Output: XML file for Occult 4 software analysis
- Fields: Event details, observer info, timing, equipment
- Note: EventFits section omitted (added by IOTA post-processing)

**Report Generation Flow:**
```
1. User selects event in grid
2. Click "Generate Report"
3. Comprehensive Report Dialog opens:
   a. Select report type (NA or TT)
   b. Select equipment (telescope + camera)
   c. Choose observation type (Positive/Negative/Unsure)
   d. Optional: Import Tangra light curve data
   e. Optional: Import AOTA timing/SNR data
4. Generator builds placeholder replacements
5. Unzips Excel template (.xlsx is a ZIP file)
6. Replaces placeholders in sheet1.xml
7. Rezips and saves to Reports/ folder
8. Opens report in Excel
```

**Data Sources:**
- Event data: From OccultationEvent object
- Equipment: From ConfigManager telescope/camera configs
- Observer info: From ConfigManager observer fields
- Timing/SNR: From AOTA Report Parser (optional)
- Light curve: From Tangra files (optional)

#### Comprehensive Report Dialog (`comprehensive_report_dialog.py` - 686 lines)
- Unified dialog for all report types
- Equipment selection dropdowns
- Observation type radio buttons
- File import for analysis data
- Validation and report generation coordination

#### AOTA Integration (`aota_dialogs.py` - 475 lines, `aota_parser.py` - 312 lines)
- Parse AOTA (Asteroidal Occultation Timing Analysis) XML files
- Extract timing, SNR, and light curve data
- Map AOTA events to OWCloud events
- Import analysis results into reports

---

### 7. SharpCap Integration

**Integration Pattern:**
- COM Automation via Python clr module
- Direct object references passed from SharpCap to Python
- Asynchronous sequence execution with monitoring

**Key SharpCap Objects Used:**
```python
SharpCap.Sequencer.RunSequenceFile(path)  # Execute sequence
SharpCap.Sequencer.Status                  # Running/Completed/Failed
SharpCap.Sequencer.FailingStep            # Error information
SharpCap.Sequencer.IsRunning              # Execution state
SharpCap.SelectedCamera                    # Active camera
SharpCap.Settings                          # Camera settings
```

**Async Execution Pattern:**
```python
# Save camera settings
saved_settings = self._save_camera_settings()

# Start sequence in background thread
def run_sequence_async():
    SharpCap.Sequencer.RunAsync(sequence_file_path)
    
    # Monitor completion
    while SharpCap.Sequencer.IsRunning:
        time.sleep(0.5)
    
    # Check status
    if SharpCap.Sequencer.Status == "Failed":
        # Handle error
    
    # Restore settings
    self._restore_camera_settings(saved_settings)
    
    # Update UI (cross-thread)
    self.Invoke(lambda: self.update_status("Complete"))

thread = threading.Thread(target=run_sequence_async)
thread.start()
```

**Settings Preservation:**
- Binning, exposure, gain, resolution saved before test
- Background thread restores after 2× exposure stabilization delay
- Display levels (stretch settings) preserved

---

### 8. Supporting Modules

#### Theme Management (`theme.py` - 208 lines)
- `ThemeManager` - Light/night mode themes
- Color schemes for panels, grids, buttons
- `apply_theme_to_control()` - Recursive theme application

#### Utilities (`utils.py` - 241 lines)
- File operations
- Geocoding (elevation, location names)
- Coordinate conversions
- Date/time formatting

#### Help System (`help.py` - 911 lines)
- `HelpManager` - Rich text help documents
- Quick Start Guide, troubleshooting, FAQ
- Displayed in dialog with styled text

---

## Data Flow Diagrams

### Event Download Flow
```
User → Download Button → gui_dialogs.LocationConfirmDialog
    → user enters lat/lon/radius
    → events.OccultationManager.download_events()
    → events.EventProcessor.get_owc_events() [HTTP to OWCloud API]
    → events.EventProcessor.merge_occultation_lists()
    → events.EventProcessor.save_occultations() [JSON cache]
    → main_gui.populate_event_table() [display in grid]
```

### Sequence Generation Flow
```
User → Selects events (checkboxes) → Generate Sequences Button
    → gui_dialogs.TemplateSelectionDialog [choose countdown type]
    → For each selected event:
        - templates.TemplateManager.load_template()
        - Replace data tags: {{goto_time}}, {{start_time}}, {{duration}}
        - Save .scs file to sequences/ folder
    → Update status bar with count
```

### Sequence Execution Flow
```
User → Run Sequences Button → main_gui.run_sequences_click_async()
    → Background thread starts
    → _save_camera_settings() [preserve SharpCap config]
    → For each sequence (in chronological order):
        - SharpCap.Sequencer.RunAsync(sequence_file_path)
        - Monitor SharpCap.Sequencer.Status
        - If failed: log error, continue to next
        - If success: record completion
    → _restore_camera_settings() [after stabilization delay]
    → Show summary MessageBox with results
    → Log to sequence_errors.log if any failures
```

### Report Generation Flow
```
User → Selects event → Generate Report Button
    → comprehensive_report_dialog.ComprehensiveReportDialog opens
    → User selects:
        - Report type (NA or TT)
        - Telescope and Camera
        - Observation type
        - Optional: Import AOTA or Tangra data
    → ReportGenerator.generate_report(event, equipment, data)
    → Build placeholder dictionary from event + config
    → Unzip Excel template → Replace placeholders in XML
    → Rezip → Save to Reports/ folder
    → Open in Excel
```

---

## Key Design Decisions

### 1. **Persistent JSON Configuration**
- Simple, human-readable format
- Preserves custom paths across updates
- Auto-detection on first run
- No database dependency

### 2. **COM Automation for SharpCap**
- Direct object references avoid version coupling
- Async execution keeps SharpCap responsive
- Background monitoring thread for long-running sequences

### 3. **Excel Report Templates**
- Industry-standard format for astronomy community
- Placeholder replacement avoids XML namespace issues
- Works with locked/protected Excel files

### 4. **Event Caching and Merging**
- Reduces API calls to OWCloud
- 14-day retention prevents stale data accumulation
- Unique ID deduplication handles updates

### 5. **Equipment Configuration System**
- Multiple telescope/camera support
- Active selection model (one active at a time)
- Used for report generation and exposure calculations

### 6. **Folder Structure Auto-Creation**
- First-run experience requires no manual setup
- README files guide users
- Template files distributed to working location

### 7. **Threading Model**
- GUI on main thread (Windows Forms requirement)
- SharpCap interactions on background threads
- Invoke() pattern for cross-thread UI updates
- Prevents UI freezing during long operations

---

## External Dependencies

### Python Modules
- **clr** (pythonnet) - .NET interop
- **System.Windows.Forms** - GUI
- **System.Drawing** - Graphics
- **System.Threading** - Background tasks
- **datetime, json, os, sys** - Standard library

### External APIs
- **OccultWatcher Cloud REST API**
  - Endpoint: `https://www.occultwatcher.net:443/api2/v1/events/details-list`
  - Auth: Basic Auth
  - Returns: JSON event predictions

### External Applications
- **SharpCap 4.1.13+** (required)
  - COM automation interface
  - Sequencer API for .scs file execution
  - Camera control and settings

- **Microsoft Excel** (for reports)
  - Opens generated .xlsx report files
  - No automation, just file format compatibility

---

## Error Handling Strategy

### Graceful Degradation
- Missing config file: Create defaults
- API unavailable: Use cached events
- Invalid event data: Skip and log
- SharpCap errors: Display, continue to next sequence

### User Feedback
- Status bar for progress updates
- MessageBox for errors and completions
- Console logging for debugging
- Error log files for sequence failures

### Validation
- SharpCap version check on startup
- Configuration validation
- File path existence checks
- API response validation

---

## Performance Considerations

### Scalability
- Designed for 10-100 events per session
- Event grid supports sorting, filtering
- Background thread for non-blocking operations
- Efficient JSON serialization for caching

### Memory Management
- Windows Forms lifetime management
- Background thread cleanup
- Dispose pattern for dialogs
- No long-lived event listeners

---

## Future Enhancement Opportunities

1. **Database Backend** - SQLite for larger event sets
2. **Cloud Sync** - Multiple observer coordination
3. **Real-time Monitoring** - Live camera feedback during observations
4. **Automated Analysis** - Integration with light curve analysis tools
5. **Mobile Companion** - Remote monitoring of observation sessions
6. **Weather Integration** - Cloud cover forecasts for event planning

---

## Development Environment

**Requirements:**
- Windows 10/11
- Python 3.8+ with pythonnet
- SharpCap 4.1.13 or later
- .NET Framework 4.7.2+

**Build Process:**
- No compilation required (pure Python)
- Package as ZIP with folder structure
- Include template files (.xlsx, .txt)

**Testing:**
- Manual testing with SharpCap
- Event download testing with OWCloud
- Report generation validation

---

## Version History Context

Current version: **0.2.0-beta.1** (First Public Beta - January 2026)

Key capabilities implemented:
- Automatic folder structure creation
- Smart path detection
- Multi-sequence execution
- Comprehensive error tracking
- Report generation for NA and TT formats
- Equipment management
- AOTA/Tangra integration

---

*Last Updated: January 2026*
*For API reference and reusable components, see API.md*
