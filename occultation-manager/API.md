# Occultation Manager - API Reference

This document describes the public interfaces and reusable components for developers who want to:
- Maintain or extend the Occultation Manager
- Fork the code to add new features
- Reuse specific modules (e.g., OWCloud integration, sequence generation)

---

## Table of Contents

1. [Event Management API](#event-management-api)
2. [Configuration API](#configuration-api)
3. [Sequence Generation API](#sequence-generation-api)
4. [Report Generation API](#report-generation-api)
5. [Data Models](#data-models)
6. [Utility Functions](#utility-functions)

---

## Event Management API

Module: `events.py`

### OccultationManager

High-level interface for event operations.

```python
from events import OccultationManager

# Initialize
manager = OccultationManager(config)

# Download events from OWCloud (downloads, merges, and saves)
num_events = manager.download_events_from_cloud()
if num_events > 0:
    print(f"Downloaded {num_events} events")
elif num_events == 0:
    print("No new events found")
else:
    print("Error downloading events")

# Load events from cached JSON files
manager.load_events_from_files()

# Access events
all_events = manager.all_events  # List of all OccultationEvent objects
filtered = manager.get_filtered_events()  # Get events filtered by station

# Selection management (used by GUI)
manager.select_all_events()  # Select all
manager.select_no_events()   # Deselect all
manager.toggle_event_selection()  # Toggle selection

# Station filtering
manager.set_station_filter("station_name")
manager.clear_station_filter()

# Sort events
manager.sort_events()  # Sort by event time
```

**Returns:**
- `download_events_from_cloud()`: Integer (count of events, 0 if none, -1 on error)
- `load_events_from_files()`: Boolean (True if successful)
- `get_filtered_events()`: List of filtered events
- `select_all_events()`: Integer (count of selected events)

**Properties:**
- `all_events`: List of all OccultationEvent objects
- `events`: Currently displayed events (after filtering)
- `selected_events`: Set of selected event objects
- `station_filter`: Current station filter string

**Exceptions:**
- Exceptions are caught and logged, methods return error codes instead of raising

---

### EventProcessor

Static utility methods for low-level event operations.

```python
from events import EventProcessor

# Download raw events from OWCloud API
raw_events = EventProcessor.get_owc_events(
    url="https://www.occultwatcher.net:443/api2/v1/events/details-list",
    username="your@email.com",
    password="your_password",
    data={
        'latitude': -37.8,
        'longitude': 144.9,
        'radius': 200,
        'daysAhead': 30
    }
)

# Save events to JSON cache
EventProcessor.save_occultations(
    events_data=events,
    filename='occultations.json',
    config=config
)

# Load events from JSON cache
cached_events = EventProcessor.load_occultations(
    filename='occultations.json',
    config=config
)

# Merge two event lists (deduplication)
merged = EventProcessor.merge_occultation_lists(
    existing=cached_events,
    new=downloaded_events,
    id_key='unique_id',
    retention_days=14  # Remove events older than this
)
```

**Key Features:**
- HTTP requests with Basic Auth
- Automatic event deduplication by unique_id
- Retention policy (removes old events)
- Merges preserve newest version of each event

---

### OccultationEvent

Represents an occultation event with all associated data from OWCloud and computed values.

**Parsed Attributes (from JSON data):**
```python
{
    # Identification
    'name': str,                    # Event name
    'station_name': str,            # Station name
    'ow_eventid': str,              # OWCloud event ID
    'event_id': str,                # Alternative event ID
    
    # Object Information
    'object_name': str,             # Asteroid/object name
    'object_no': str,               # Object catalog number
    
    # Star Information
    'star_id': str,                 # Star catalog ID
    'star_mag': float,              # Star magnitude
    'mag_drop': float,              # Magnitude drop during occultation
    'comb_mag': float,              # Combined magnitude
    
    # Coordinates
    'ra': float,                    # Right ascension (degrees)
    'dec': float,                   # Declination (degrees)
    'star_alt': float,              # Star altitude (degrees)
    'star_az': float,               # Star azimuth (degrees)
    'latitude': float,              # Observer latitude
    'longitude': float,             # Observer longitude
    'elevation': float,             # Observer elevation (meters)
    'obs_location': str,            # Observer location name
    
    # Timing (strings from OWCloud)
    'event_time': str,              # Event time string
    'start_time_str': str,          # Recording start time string
    'end_time_str': str,            # Recording end time string
    'goto_time_str': str,           # Telescope goto time string
    
    # Duration and Uncertainty
    'event_duration': float,        # Expected event duration (seconds)
    'event_uncertainty': float,     # Time uncertainty (seconds)
    'recording_duration': int,      # Recording duration (seconds)
    
    # Camera Settings
    'precalc_exposure': float,      # Pre-calculated exposure from OWCloud
    
    # Source Information
    'source': str,                  # Data source
    'owcloudurl': str,              # OWCloud event URL
}
```

**Computed Attributes (calculated locally):**
```python
{
    # Parsed Datetimes
    'event_datetime': datetime,         # Event time as datetime object
    'start_time': datetime,             # Recording start as datetime
    'end_time': datetime,               # Recording end as datetime
    'goto_time': datetime,              # Goto time as datetime
    
    # Local Time Strings (for display)
    'start_time_local': str,            # Start time in local timezone
    'goto_time_local': str,             # Goto time in local timezone
    'event_time_local': str,            # Event time in local timezone
    'pre_goto_time_local': str,         # Pre-goto time in local timezone
    'event_date': str,                  # Event date (YYYY-MM-DD)
    'event_time_utc': str,              # Event time UTC (HH:MM:SS)
    
    # Camera Settings (calculated)
    'exposure_ms': int,                 # Calculated exposure (milliseconds)
    'gain_value': int,                  # Calculated gain value
    
    # Duration Values
    'duration_seconds': float,          # Event duration in seconds
    'max_duration_seconds': float,      # Maximum expected duration
    'uncertainty_seconds': float,       # Uncertainty in seconds
    
    # UI State
    'selected': bool,                   # Selection state for UI
}
```

**Custom Override Attributes:**
```python
{
    'custom_exposure': int or None,     # User-specified exposure override
    'custom_gain': int or None,         # User-specified gain override
    'custom_recording_duration': int or None,  # User-specified recording duration override
}
```

**Key Methods:**
- `get_asteroid_display_name()` - Returns formatted asteroid name
- `get_coordinates_string()` - Returns RA/Dec as formatted string
- `get_status_info()` - Returns event status information
- `set_custom_exposure(value)` - Set custom exposure override
- `set_custom_gain(value)` - Set custom gain override
- `set_custom_recording_duration(value)` - Set custom recording duration override
- `has_custom_exposure()` - Check if custom exposure is set
- `has_custom_gain()` - Check if custom gain is set
- `has_custom_recording_duration()` - Check if custom recording duration is set
- `set_elevation(elevation)` - Set observer elevation
- `get_elevation()` - Get observer elevation
- `set_obs_location(location)` - Set observer location name
- `get_obs_location()` - Get observer location name
```

**Constructor:**
```python
OccultationEvent(
    data: dict,           # Raw event data from OWCloud
    config: ConfigManager  # Configuration for settings
)
```

**Key Methods:**
- `calculate_airmass()` → float: Atmospheric extinction (1.0 = zenith)
- `calculate_sun_angle()` → float: Angular distance from sun (degrees)
- `calculate_moon_angle()` → float: Angular distance from moon (degrees)
- `calculate_sky_brightness()` → float: Combined sky brightness factor

**Data Dictionary Format (from OWCloud):**
```json
{
  "unique_id": "20251223_165690_UCAC4_361_199861",
  "object_no": 165690,
  "object_name": "(165690) 2001 PA3",
  "star_name": "UCAC4 361-199861",
  "star_mag": 11.2,
  "event_time": "2025-12-23T14:30:45",
  "altitude": 45.5,
  "azimuth": 178.3,
  "duration": 8.2,
  "probability": 0.85,
  "ra_star_deg": 182.456,
  "dec_star_deg": -15.234
}
```

---

## Configuration API

Module: `config.py`

### ConfigManager

Central configuration management with persistent JSON storage.

```python
from config import ConfigManager

# Initialize (auto-detects installation directory)
config = ConfigManager()

# Or specify custom config folder
config = ConfigManager(config_folder="/path/to/config")

# Access file paths (fixed path model)
data_root = config.get_data_root()  # Install-relative data root
events_folder = config.get_events_folder()  # Event cache JSON files
templates_folder = config.get_templates_folder()  # Working template copies
sequences_folder = config.get_sequences_folder()  # Sequence files location
reports_folder = config.get_reports_folder()  # Generated reports
full_path = config.get_full_file_path('occultations.json')

# Get configuration path
config_path = config.get_config_path()  # Path to JSON config file

# User credentials
email = config.get_owc_email()
password = config.get_owc_password()

# Recording parameters
base_duration = config.get_base_duration()  # Recording duration (seconds)
goto_lead = config.get_goto_lead_time()  # GOTO lead time (seconds)
sync_mount = config.get_sync_mount()  # Boolean
default_gain = config.get_default_gain()  # Integer

# Observer information (for reports)
name = config.get_observer_name()
email = config.get_observer_email()
address = config.get_observer_address()
city = config.get_observer_city()
phone = config.get_observer_phone()

# Equipment management
telescopes = config.get_telescopes()  # List of telescope dicts
cameras = config.get_cameras()  # List of camera dicts

# Add new telescope
telescope_id = config.add_telescope(
    name='Celestron C8',
    aperture=200,  # mm
    focal_ratio=10,  # f-ratio (not focal length!)
    tel_type='SCT including Cass and Mak'
)

# Update telescope
config.update_telescope(
    telescope_id=telescope_id,
    name='Updated Name',
    aperture=250,
    focal_ratio=12,
    tel_type='SCT'
)

# Get telescope by ID
telescope = config.get_telescope_by_id(telescope_id)

# Set active telescope
config.set_active_telescope(telescope_id)
active_telescope = config.get_active_telescope()

# Delete telescope
config.delete_telescope(telescope_id)

# Add new camera
camera_id = config.add_camera(
    name='ZWO ASI290MM',
    detector='QHY 174 GPS',
    report_type='NA',  # 'NA' or 'TT'
    timing='GPS - time inserted',
    timing_device='GPS',
    occult4_method='b',  # Optional, default='b'
    occult4_time='a',    # Optional, default='a'
    other_info='Additional notes'  # Optional
)

# Update camera
config.update_camera(
    camera_id=camera_id,
    name='Updated Name',
    detector='Updated Detector',
    report_type='TT',
    timing='GPS - other linking',
    timing_device='KIWI-OSD',
    occult4_method='c',
    occult4_time='b',
    other_info='Updated info'
)

# Get camera by ID
camera = config.get_camera_by_id(camera_id)

# Set active equipment
config.set_active_camera(camera_id)
active_camera = config.get_active_camera()

# Delete camera
config.delete_camera(camera_id)

# Save configuration (persists to JSON)
config.save_config()

# Reload from disk
config.load_config()
```

**Equipment Data Structure:**

```python
# Telescope dictionary
telescope = {
    'id': 'unique_id_string',
    'name': 'Celestron C8',
    'aperture': 200.0,  # Aperture in mm (float)
    'focal_ratio': 10.0,  # F-ratio, not focal length! (float)
    'type': 'SCT including Cass and Mak'  # Telescope type
}

# Camera dictionary
camera = {
    'id': 'unique_id_string',
    'name': 'ZWO ASI290MM',
    'detector': 'QHY 174 GPS',  # Detector type for reports
    'report_type': 'NA',  # 'NA' or 'TT' (determines available options)
    'timing': 'GPS - time inserted',  # Timing method
    'timing_device': 'GPS',  # Timing device type
    'occult4_method': 'b',  # Occult4 method code (a-d)
    'occult4_time': 'a',  # Occult4 time code (a-c)
    'other_info': 'Additional camera notes'  # Optional
}
```

**Important Notes:**
- **Telescope:** Stores `focal_ratio` (f-number), NOT focal length
- **Camera:** Designed for report generation, NOT sensor specifications
- Camera fields (detector, timing, etc.) populate IOTA/RASNZ report forms
- Report type ('NA' or 'TT') determines available dropdown options in GUI
```

**Configuration Storage:**
- File: `{install_dir}/data/config/occultation_config.json`
- Format: JSON
- Encoding: UTF-8
- Auto-created on first run

---

## Sequence Generation API

Module: `sequence_runner.py`, `templates.py`

### SequenceRunner

Manages SharpCap sequence execution.

```python
from sequence_runner import SequenceRunner

# Initialize
runner = SequenceRunner(config, sharpcap_instance)

# Run multiple sequences in chronological order
success = runner.run_sequences(
    events=selected_events,  # List of OccultationEvent objects
    status_callback=lambda msg: print(msg)  # Optional progress callback
)

# Run single sequence
success = runner.run_single_sequence(
    sequence_file_path='C:/sequences/event.scs',
    event=event_object,
    status_callback=lambda msg: print(msg)
)

# Check if currently running
if runner.running:
    print("Sequence in progress")

# Get current sequence
current = runner.current_sequence  # OccultationEvent or None
```

**Sequence Execution Behavior:**
- Filters for future events (past GOTO time events are skipped)
- Sorts by GOTO time (chronological order)
- Continues to next sequence if one fails
- Waits 1 second between sequences
- Returns overall success (True if any completed)

**Status Callback Messages:**
```
"Running sequence 2/5: (778) Theobalda"
"Starting SharpCap sequence: event.scs"
"Sequence started successfully for (778) Theobalda"
"Failed to run sequence for (778) Theobalda"
"All sequences completed"
```

---

### TemplateManager

Manages sequence template files.

```python
from templates import TemplateManager

# Initialize
templates = TemplateManager(config)

# Find template files in folder
template_files, folder_path = TemplateManager.find_template_files(
    template_folder=config.get_templates_folder()
)

# Get template file info
size, mtime = TemplateManager.get_template_info(template_path)

# Load template content
content = TemplateManager.load_template(
    template_path='C:/install/data/templates/SharpCap Sequence UTC Template.txt',
    config=config
)

# Manual tag replacement
if content:
    content = content.replace('{goto_time}', '2025-12-23T14:25:00')
    content = content.replace('{start_time}', '2025-12-23T14:30:00')
    content = content.replace('{duration}', '120')
    content = content.replace('{object_name}', '(778) Theobalda')
    
    # Save manually
    output_path = os.path.join(config.get_sequences_folder(), 'event.scs')
    with open(output_path, 'w') as f:
        f.write(content)
```

**Note:** Tag replacement is typically handled by the GUI layer (`main_gui.py`), not by TemplateManager itself.

**Available Data Tags:**

| Tag | Format | Example | Description |
|-----|--------|---------|-------------|
| `{goto_time}` | ISO 8601 UTC | `2025-12-23T14:25:00` | GOTO start time |
| `{goto_time_local}` | HH:MM:SS | `01:25:00` | GOTO local time (for WAIT UNTIL) |
| `{start_time}` | ISO 8601 UTC | `2025-12-23T14:30:00` | Recording start time |
| `{start_time_local}` | HH:MM:SS | `01:30:00` | Recording local time |
| `{duration}` | Integer | `120` | Recording duration (seconds) |
| `{object_name}` | String | `(778) Theobalda` | Asteroid name |
| `{star_name}` | String | `UCAC4 361-199861` | Target star |

**Template File Locations:**
- Master templates: `{install_dir}/resources/templates_master/sequencer/*.txt`
- Working copies: `{install_dir}/data/templates/*.txt` (user-editable)

**Template Types:**
1. **SharpCap Sequence UTC Template.txt** - UTC sequence with countdown
2. **SharpCap Sequence Local Time Template.txt** - Local-time sequence with countdown
3. **SharpCap Minimal Local Time Template.txt** - Minimal local-time sequence
4. **SharpCap Just Record Template.txt** - Recording-only sequence
5. **SharpCap Test Recording Template.txt** - Short test recording sequence

---

## Report Generation API

Modules: `na_report_openize.py`, `tt_report_openize.py`, `report_generator_base.py`, `occult4_export.py`

### Overview

Three report generators create standardized observation reports:
- **NAReportGeneratorOpenize** - IOTA North American format (.xlsx)
- **TTReportGeneratorOpenize** - RASNZ Trans-Tasman format (.xlsx)
- **Occult4Exporter** - Occult 4 XML format (.xml)

All use the same data sources and similar APIs.

---

### NAReportGeneratorOpenize

Generates IOTA North American occultation report forms using Openize.

```python
from na_report_openize import NAReportGeneratorOpenize

# Initialize
generator = NAReportGeneratorOpenize(config)

# Generate report
report_path = generator.generate_report(
    event=event_object,
    telescope_id='telescope_uuid',
    camera_id='camera_uuid',
    observation_type='Positive',  # 'Positive', 'Negative', 'Unsure'
    tangra_data={  # Optional: Tangra light curve data
        'snr': 8.5,
        'd_time': '2025-12-23 14:30:42.345',
        'r_time': '2025-12-23 14:30:50.678',
        'event_grade': 'A'
    },
    aota_report_data={  # Optional: AOTA timing/SNR data
        'snr': 9.2,
        'disappearance': '14:30:42.123',
        'reappearance': '14:30:50.456',
        'duration': 8.333
    },
    aota_xml_used=False  # True if AOTA XML file was source
)

print(f"Report saved to: {report_path}")
# Returns: C:/install/data/reports/20251223_778_Theobalda_Report.xlsx
```

**Report Output:**
- Format: Microsoft Excel (.xlsx)
- Location: `{install_dir}/data/reports/`
- Filename: `YYYYMMDD_ObjectNumber_ObjectName_Report.xlsx`
- Opens automatically in Excel after generation

---

### TTReportGeneratorOpenize

Generates RASNZ Trans-Tasman occultation report forms using Openize.

```python
from tt_report_openize import TTReportGeneratorOpenize

# Initialize
generator = TTReportGeneratorOpenize(config)

# Generate report (same API as NAReportGeneratorOpenize)
report_path = generator.generate_report(
    event=event_object,
    telescope_id='telescope_uuid',
    camera_id='camera_uuid',
    observation_type='Positive',
    tangra_data=tangra_data,  # Optional
    aota_report_data=aota_data,  # Optional
    aota_xml_used=False
)
```

**Differences from NA Reports:**
- Different Excel template (RASNZ format)
- Different field mappings
- Different star catalog formatting

---

### Occult4Exporter

Generates Occult 4 XML format files for asteroid occultation analysis.

```python
from occult4_export import Occult4Exporter

# Initialize
exporter = Occult4Exporter(config)

# Export observation to XML
xml_path = exporter.export_observation(
    event=event_object,
    telescope_id='telescope_uuid',
    camera_id='camera_uuid',
    observation_type='Positive',
    tangra_data=tangra_data,  # Optional
    aota_report_data=aota_data,  # Optional
    observer_data={'notes': 'Additional info'}  # Optional
)

# Export to specific path
xml_path = exporter.export_observation_to_path(
    output_path='C:/custom/path/observation.xml',
    event=event_object,
    telescope_id='telescope_uuid',
    camera_id='camera_uuid',
    observation_type='Positive'
)
```

**XML Output:**
- Format: Occult 4 XML Version 2.15
- Location: `{install_dir}/data/reports/` (via `get_file_folder()/Reports` compatibility path)
- Filename: `YYYYMMDD_ObjectNumber_ObjectName_StarID_Occult4.xml`
- Compatible with Occult 4 software for analysis

**Note:** EventFits section (elliptic fits, shape models) is omitted from exports and added by IOTA after processing.

---

### ReportGeneratorBase

Base class with common report functionality.

```python
from report_generator_base import ReportGeneratorBase

# Inherit for custom report types
class MyReportGenerator(ReportGeneratorBase):
    TEMPLATE_FILENAME = 'MyTemplate.xlsx'
    
    def generate_report(self, event, **kwargs):
        replacements = self._build_replacements(event)
        # ... custom logic
```

**Provided Methods:**
- `parse_star_catalog(star_name)` → (catalog, number)
  - Example: `"UCAC4 361-199861"` → `("UCAC4", "361-199861")`
- `_generate_filename(event, date_str)` → filename string
- `get_template_path()` → full path to the active report template

**Months Constant:**
```python
MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
          'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
```

---

## Data Models

### Equipment Models

```python
# Telescope configuration
{
    'id': str,              # Unique identifier (UUID)
    'name': str,            # Display name
    'aperture': float,      # Aperture in mm
    'focal_ratio': float,   # Focal ratio (f/number)
    'type': str             # Type (SCT, Refractor, Newtonian, etc.)
}

# Camera configuration (for report generation)
{
    'id': str,              # Unique identifier (UUID)
    'name': str,            # Display name
    'detector': str,        # Detector type
    'report_type': str,     # Report type for generation
    'timing': str,          # Timing source description
    'timing_device': str,   # Timing device used
    'occult4_method': str,  # Occult4 method code
    'occult4_time': str,    # Occult4 time code
    'other_info': str       # Additional information
}
```

---

## Utility Functions

Module: `utils.py`

### Geocoding Functions

```python
from utils import get_elevation_from_coordinates, get_location_name_from_coordinates

# Get elevation for coordinates
elevation_m = get_elevation_from_coordinates(
    latitude=-37.8,
    longitude=144.9
)
# Returns: float (meters above sea level) or None if unavailable

# Get location name from coordinates
location_name = get_location_name_from_coordinates(
    latitude=-37.8,
    longitude=144.9
)
# Returns: str ("Melbourne, Victoria, Australia") or None
```

**API Usage:**
- Uses public geocoding APIs
- Cached results to avoid repeated requests
- Returns None on API failures (graceful degradation)

---

### File Operations

```python
from utils import save_occultation_sequence

# Save sequence file with error handling
success = save_occultation_sequence(
    content="SHOW NOTIFICATION ...",
    filename="20251223_event.scs",
    folder_path="C:/sequences"
)
# Returns: bool (True on success)
```

---

## SharpCap COM API Reference

The application interacts with SharpCap through COM automation. These are the key SharpCap objects used:

### Sequencer API

```python
# Access sequencer
sequencer = SharpCap.Sequencer

# Run sequence file
sequencer.RunSequenceFile("C:/sequences/event.scs")

# Run sequence asynchronously (non-blocking)
sequencer.RunAsync("C:/sequences/event.scs")

# Check status
status = sequencer.Status  # "Running", "Completed", "Failed", "Stopped"
is_running = sequencer.IsRunning  # Boolean

# On failure
failing_step = sequencer.FailingStep  # Which step failed
failure_reason = sequencer.FailureReason  # Error message

# Stop sequence
sequencer.Stop()
```

### Camera API

```python
# Access camera
camera = SharpCap.SelectedCamera

# Camera settings
settings = camera.Settings
exposure = settings.Exposure.Value  # Microseconds
gain = settings.Gain.Value
binning = settings.Binning.Value  # e.g., "2x2"

# Set settings
settings.Exposure.Value = 40000  # 40ms
settings.Gain.Value = 450

# Resolution
width = camera.Width
height = camera.Height
```

**Important Notes:**
- COM objects must be accessed from correct thread
- Settings changes may take time to apply (stabilization delay)
- Always save and restore settings for test recordings

---

## Code Examples

### Example 1: Download and Display Events

```python
from config import ConfigManager
from events import OccultationManager

# Initialize
config = ConfigManager()
manager = OccultationManager(config)

# Download events from OWCloud
num_events = manager.download_events_from_cloud()
print(f"Downloaded {num_events} events")

# Or load from cache
manager.load_events_from_files()

# Access all events
for event in manager.all_events:
    print(f"{event.display_goto_time}: {event.object_name}")
    print(f"  Star: {event.star_name} (mag {event.star_mag:.1f})")
    print(f"  Duration: {event.duration:.1f}s")
    print(f"  Altitude: {event.display_altitude}")
    print(f"  Probability: {event.probability*100:.0f}%")
    print()
```

### Example 2: Generate Sequence Files

```python
from config import ConfigManager
from events import OccultationManager
from templates import TemplateManager
import os

# Setup
config = ConfigManager()
manager = OccultationManager(config)
templates = TemplateManager(config)

# Load events
manager.load_events_from_files()

# Load template
template_path = os.path.join(config.get_templates_folder(), 'SharpCap Sequence UTC Template.txt')
template_content = TemplateManager.load_template(template_path, config)

# Generate sequences for each event
for event in manager.all_events[:5]:  # First 5 events
    # Build replacement dictionary
    content = template_content
    content = content.replace('{goto_time}', event.goto_time.strftime('%Y-%m-%dT%H:%M:%S'))
    content = content.replace('{start_time}', event.start_time.strftime('%Y-%m-%dT%H:%M:%S'))
    content = content.replace('{duration}', str(event.recording_duration))
    content = content.replace('{object_name}', event.name)
    
    # Save
    filename = f"{event.event_datetime.strftime('%Y%m%d')} {event.name}.scs"
    output_path = os.path.join(config.get_sequences_folder(), filename)
    with open(output_path, 'w') as f:
        f.write(content)
    
    print(f"Generated: {filename}")
```

### Example 3: Generate Report

```python
from config import ConfigManager
from events import OccultationManager
from na_report_openize import NAReportGeneratorOpenize

# Setup
config = ConfigManager()
manager = OccultationManager(config)
generator = NAReportGeneratorOpenize(config)

# Load events
manager.load_events_from_files()

# Get first event
event = manager.all_events[0]

# Optional: Add analysis data
tangra_data = {
    'snr': 8.5,
    'd_time': '2025-12-23 14:30:42.345',
    'r_time': '2025-12-23 14:30:50.678',
    'event_grade': 'A'
}

# Generate
report_path = generator.generate_report(
    event=event,
    telescope_id=config.get_active_telescope()['id'],
    camera_id=config.get_active_camera()['id'],
    observation_type='Positive',
    tangra_data=tangra_data
)

print(f"Report: {report_path}")
```

### Example 4: Custom Event Filter

```python
from events import OccultationManager
from datetime import datetime, timedelta

config = ConfigManager()
manager = OccultationManager(config)
manager.load_events_from_files()

# Filter for high-probability, bright events tonight
tonight_start = datetime.utcnow().replace(hour=20, minute=0, second=0)
tonight_end = tonight_start + timedelta(hours=8)

filtered = [
    e for e in manager.all_events
    if e.probability > 0.5
    and e.star_mag < 12.0
    and tonight_start < e.event_datetime < tonight_end
    and e.altitude > 30
]

print(f"Found {len(filtered)} high-quality events tonight")
```

---

## Best Practices

### Error Handling

```python
try:
    events = manager.download_events(...)
except ConnectionError:
    print("OWCloud API unavailable - using cached events")
    events = EventProcessor.load_occultations('occultations.json', config)
except Exception as ex:
    print(f"Unexpected error: {ex}")
    import traceback
    traceback.print_exc()
```

### Configuration Management

```python
# Always save after changes
config.add_telescope(telescope_data)
config.save_config()

# Load fresh data if needed
config.load_config()
```

### Thread Safety (Windows Forms)

```python
# Update UI from background thread
def background_task():
    result = long_running_operation()
    
    # Use Invoke to update UI
    form.Invoke(lambda: form.update_status(f"Complete: {result}"))

thread = threading.Thread(target=background_task)
thread.start()
```

### SharpCap Integration

```python
# Always check if running
if not SharpCap.Sequencer.IsRunning:
    SharpCap.Sequencer.RunSequenceFile(path)
else:
    print("Sequencer already running")

# Monitor status
while SharpCap.Sequencer.IsRunning:
    time.sleep(0.5)

# Check result
if SharpCap.Sequencer.Status == "Failed":
    print(f"Failed: {SharpCap.Sequencer.FailureReason}")
```

---

## Extension Points

### Adding a New Report Format

1. Create new module inheriting from `ReportGeneratorBase`
2. Implement `generate_report()` method
3. Map required report fields to workbook cells (Openize pattern)
4. Add to comprehensive report dialog

```python
from report_generator_base import ReportGeneratorBase

class MyReportGenerator(ReportGeneratorBase):
    TEMPLATE_FILENAME = 'MyTemplate.xlsx'
    
    def generate_report(self, event, **kwargs):
        # Build data model and write values to target worksheet cells
        # using direct Openize cell access
        
        # Generate
        template = self.get_template_path()
        output = os.path.join(self.config.get_reports_folder(), filename)
        # Open workbook with Openize, write mapped cells, and save to output
        return output
```

### Adding a New Countdown Template

1. Create .txt file with SharpCap sequence commands
2. Use data tags: `{goto_time}`, `{start_time}`, `{duration}`
3. Place in `data/templates/` folder
4. Add to template selection dialog

```plaintext
# My Custom Countdown Template
SHOW NOTIFICATION "Starting in 5 minutes" COLOUR Blue DURATION 5000
WAIT UNTIL LOCALTIME "{goto_time_local}"
CLEAR NOTIFICATION
SHOW NOTIFICATION "Recording {object_name}" COLOUR Green DURATION 10000
CAPTURE {duration} FRAMES
CLEAR NOTIFICATION
```

### Adding a New Event Data Source

1. Extend `EventProcessor` with new download method
2. Convert to `OccultationEvent` objects
3. Merge with existing events using `merge_occultation_lists()`

```python
@staticmethod
def download_from_custom_source(api_url, params):
    # Fetch data
    response = urllib.request.urlopen(api_url)
    data = json.loads(response.read())
    
    # Convert to standard format
    events = []
    for item in data:
        event_dict = {
            'unique_id': item['id'],
            'object_name': item['asteroid'],
            'event_time': item['datetime'],
            # ... map other fields
        }
        events.append(OccultationEvent(event_dict, config))
    
    return events
```

---

## Troubleshooting

### Common Issues

**Events not downloading:**
- Check OWCloud credentials in configuration
- Verify internet connection
- Check API endpoint URL
- Review console for error messages

**Sequences not generating:**
- Verify template files exist in `data/templates/` folder
- Check sequence folder path in configuration
- Ensure events have valid datetime values

**Reports not generating:**
- Check template .xlsx files are present
- Verify telescope/camera IDs are valid
- Ensure event has all required fields
- Check `data/reports/` exists and is writable

**SharpCap integration errors:**
- Verify SharpCap version is 4.1.13+
- Ensure camera is connected
- Check sequencer is not already running
- Review SharpCap logs for COM errors

---

## Further Reading

- **ARCHITECTURE.md** - System design and component relationships
- **README.md** - User installation and usage guide
- **RELEASE_NOTES.md** - Version history and changes

---

*Last Updated: January 2026*
*For architecture overview, see ARCHITECTURE.md*
