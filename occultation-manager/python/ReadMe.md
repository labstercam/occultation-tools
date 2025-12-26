# Occultation Manager - Python Modules

## Core Components

### Report Generation System

The Occultation Manager includes comprehensive Excel report generation with integrated timing analysis.

#### simple_xlsx.py - Pure Python Excel Library

**Why simple_xlsx?**
IronPython (used by SharpCap) cannot load C extensions. Popular libraries like `openpyxl` depend on lxml and numpy (C extensions), causing IronPython crashes. `simple_xlsx` provides Excel functionality using only Python standard library.

**Implementation** (364 lines):
- Uses only `zipfile` and `xml.etree.ElementTree`
- No external dependencies or C extensions
- Implements essential Excel operations for report generation

**Core Classes**:
- `SimpleWorkbook` - Manages .xlsx ZIP files
- `SimpleWorksheet` - Handles individual worksheets
- `SimpleCell` - Cell value wrapper

**Supported Operations**:
- ✅ Load .xlsx templates
- ✅ Read/write cell values (strings, numbers, dates)
- ✅ Save modified workbooks
- ❌ Formulas (preserved but not calculated)
- ❌ Formatting (preserved from template)

#### Report Generators

**na_report.py** - North America (IOTA V5.6.12r)
- Uses template: `NorthAmerica_AstReportForm_V5.6.12r.xlsx`
- Populates 47 mapped cells with event and timing data
- Filename format: `YYYYMMDD_asteroidnumber_asteroidname_starcatalog_starnumber-surname_station.xlsx`

**tt_report.py** - Trans-Tasman (RASNZ V4.1.2.G)
- Uses template: `TransTasman_AstReportForm_V4.1.2.G.xlsx`
- Similar structure with regional-specific fields

#### Timing Integration

**light_curves_iron.py** - IronPython-Compatible Timing Analysis
- Reads Tangra CSV light curve files
- Extracts observation timing statistics
- Compatible with IronPython (no pandas/numpy/scipy)
- Uses only Python standard library (csv, datetime)

**Key Functions**:
```python
read_tangra_csv_iron(file_path)
# Returns: filename, header details, apertures, light curve data

analyse_timestamps_iron(light_curve_data)
# Returns: start_time, end_time, tdelta_median, tdelta_std

get_observation_summary(tangra_csv_path)
# Convenience wrapper combining read and analysis
```

**Extracted Data**:
- Start time (HH:MM:SS.SS format)
- End time (HH:MM:SS.SS format)
- Exposure time (median frame delta in seconds)
- Camera acquisition delay (from measurement parameters table, rows 7-8)

**Report Placeholders Populated**:
```
{{STARTED_OBSERVING_HOURS}}
{{STARTED_OBSERVING_MINUTES}}
{{STARTED_OBSERVING_SECONDS}}
{{STOPPED_OBSERVING_HOURS}}
{{STOPPED_OBSERVING_MINUTES}}
{{STOPPED_OBSERVING_SECONDS}}
{{INTEGRATION}}                    # Exposure in seconds
{{CAMERA_DELAY_CORRECTION}}        # Acquisition delay in seconds
{{CORRECTIONS_APPLIED}}            # Set to "yes" when Tangra data present
```

### User Interface

**comprehensive_report_dialog.py** - Streamlined Report Generation
Single dialog combining:
1. Report format selection (NA/TT)
2. Equipment selection (telescope/camera)
3. Observation type (Positive/Negative/Unsure)
4. File selection (AOTA and Tangra CSV)

**Features**:
- Settings persistence (remembers last report type and folder)
- Auto-selection of first available files
- Smart validation (AOTA required for Positive/Unsure)
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

### Utility Modules

- `aota_parser.py` - Parse AOTA XML timing files
- `templates.py` - SharpCap sequence template management
- `theme.py` - Dark/light mode theme support
- `utils.py` - Common utility functions