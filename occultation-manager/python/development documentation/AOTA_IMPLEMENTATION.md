# AOTA Import Feature Implementation

## Overview
This feature allows users to import timing data from AOTA (Asteroid Occultation Timing Analysis) XML files and include the analyzed D (disappearance) and R (reappearance) times in their occultation reports.

## Files Created

### 1. aota_parser.py
**Purpose**: Core AOTA XML parsing functionality

**Key Classes**:
- `AOTAEvent`: Represents a single event with D/R times and uncertainties
  - Parses time strings in format "HH MM SS.S ± E.E"
  - Stores separate components: hours, minutes, seconds, error
  - **Preserves original string precision** (d_seconds_str, d_error_str, etc.)
  - Validates event data
  - Filters out non-events (IsNonEvent=true)

- `AOTACameraResult`: Stores camera and measurement metadata
  - Camera type, measuring tool, video system
  - Frame integration settings
  - Timing configuration

- `AOTAResult`: Complete AOTA analysis results
  - Contains list of events
  - Filters valid events (IsNonEvent=false)
  - Handles single vs. multiple event scenarios

**Key Functions**:
- `parse_aota_file(file_path)`: Main parsing function
- `format_aota_time_component()`: Formats time values for Excel
- `format_aota_error()`: Formats error/uncertainty values

### 2. aota_dialogs.py
**Purpose**: User interface dialogs for AOTA import

**Key Classes**:
- `ObservationTypeDialog`: Select observation type
  - Three options: Positive, Negative, Unsure
  - Determines if AOTA import is needed
  - Affects filename and WAS_MISS field

- `AOTAFilePickerDialog`: File selection dialog
  - Filters for *.aota.xml files
  - Event context display
  - File validation
  - Only shown for Positive/Unsure observations

- `AOTAEventSelectionDialog`: Multi-event selection
  - Displays all valid events with timing details
  - Shows D/R times and duration
  - Allows user to select correct event
  - AOTA version and camera info display

## Files Modified

### 1. NA_PLACEHOLDERS.txt
**Added 8 new placeholders**:
```
{{AOTA_D_HOURS}}      - Disappearance hours
{{AOTA_D_MINUTES}}    - Disappearance minutes  
{{AOTA_D_SECONDS}}    - Disappearance seconds
{{AOTA_D_ERROR}}      - Disappearance uncertainty
{{AOTA_R_HOURS}}      - Reappearance hours
{{AOTA_R_MINUTES}}    - Reappearance minutes
{{AOTA_R_SECONDS}}    - Reappearance seconds
{{AOTA_R_ERROR}}      - Reappearance uncertainty
```

**Suggested Cell Mappings**:
- N31, P31, R31, T31 for D times and error
- N37, P37, R37, T37 for R times and error

### 2. TT_PLACEHOLDERS.txt
**Added same 8 AOTA placeholders**

**Suggested Cell Mappings**:
- G31, I31, K31, M31 for D times and error
- G37, I37, K37, M37 for R times and error

### 3. na_report.py (North American Report Generator)
**Added**:
- `observation_type` parameter to `generate_report()` method
- **WAS_MISS field logic**: Inverse of observation type
  - Positive → "no" (saw occultation = NOT a miss)
  - Negative → "yes" (missed occultation)  
  - Unsure → "maybe"
- **Filename formatting**: Uses POS/NEG suffix
  - Format: `YYYYMMDD_###_Asteroid_Surname_POS.xlsx`
  - POS for Positive observations, NEG otherwise
- AOTA placeholders **NOT initialized** in `_build_replacements()`
  - Placeholders remain as `{{AOTA_D_HOURS}}` etc. in Excel
  - Allows post-processing to find and replace them
- `import_aota_data(aota_event, replacements)` method
  - Preserves decimal precision using string representations
  - Handles missing data gracefully

### 4. tt_report.py (Trans-Tasman Report Generator)
**Added**:
- `observation_type` parameter to `generate_report()` method
- **WAS_MISS field logic**: Inverse of observation type
  - Positive → "no" (saw occultation = NOT a miss)
  - Negative → "yes" (missed occultation)
  - Unsure → "maybe"
- **Filename formatting**: Uses +/- prefix before surname
  - Format: `YYYYMMDD_###_Asteroid_Catalog_Number+Surname.xlsx`
  - '+' for Positive observations, '-' for Negative/Unsure
- AOTA placeholders **NOT initialized** in `_build_replacements()`
  - Excluded from `all_placeholders` validation list
  - Allows post-processing to replace them
- `import_aota_data(aota_event, replacements)` method
  - Preserves decimal precision using string representations
  - Same functionality as NA version

### 5. main_gui.py (Main GUI)
**Modified `generate_report_click()` method**:

**New Workflow**:
1. User selects event and report type
2. Equipment selection dialog
3. Location confirmation dialog
4. **NEW**: Observation type selection
   - Positive, Negative, or Unsure
   - Determines filename format and WAS_MISS value
5. **NEW**: AOTA import (only for Positive/Unsure)
   - Shows file picker dialog
   - Parses AOTA file
   - If multiple valid events: Shows event selector
   - If single event: Uses automatically
   - **Skipped for Negative observations**
6. Generates report with standard data
7. **NEW**: Adds AOTA data to generated report (if imported)

**Added `_add_aota_to_existing_report()` method**:
- Post-processes generated Excel file
- Replaces AOTA placeholders in worksheet XML
- Handles shared strings
- Preserves all other report content
- **Debug logging**: Prints which placeholders are replaced
- Uses string representations to preserve decimal precision

### 6. gui_dialogs.py
**Modified**:
- `LocationConfirmDialog` button text changed from "Confirm & Generate Report" to "Next - event D/R"

## User Workflow

### Generating a Report with AOTA Data

1. **Select Event**: Choose a past event from the event list
2. **Click "Generate Report"**
3. **Select Report Type**: Choose North America or Trans-Tasman
4. **Select Equipment**: Choose telescope and camera
5. **Confirm Location**: Verify/edit observation location, click "Next - event D/R"
6. **Select Observation Type**: Choose result of observation
   - **Positive**: Saw the occultation (asteroid blocked the star)
   - **Negative**: Did not see occultation (missed or wasn't in path)
   - **Unsure**: Uncertain about detection
   
7. **AOTA Import** (Positive/Unsure only):
   - File picker opens automatically for Positive or Unsure observations
   - Browse to your *.aota.xml file
   - Click OK (or Cancel to skip AOTA import)
   - **Note**: Negative observations skip this step entirely

8. **Select Event** (if multiple in AOTA file):
   - Dialog shows all valid events with timing details
   - Format: "D: HH:MM:SS.S (±Es) | R: HH:MM:SS.S (±Es) | Duration: Xs"
   - Select the event corresponding to your observation
   - Click "Use Selected Event"

9. **Report Generation**:
   - Report generates with observation type and filename:
     - **NA format**: `YYYYMMDD_###_Asteroid_Surname_POS.xlsx` (or NEG)
     - **TT format**: `YYYYMMDD_###_Asteroid_Catalog_Number+Surname.xlsx` (or -)
   - AOTA timing data automatically filled (if imported)
   - WAS_MISS field set based on observation type
   - Success message shows file location

### Observation Type Effects

| Type | Filename (NA) | Filename (TT) | WAS_MISS | AOTA Import |
|------|---------------|---------------|----------|-------------|
| Positive | `..._POS.xlsx` | `...+Surname.xlsx` | no | Yes - prompted |
| Negative | `..._NEG.xlsx` | `...-Surname.xlsx` | yes | No - skipped |
| Unsure | `..._NEG.xlsx` | `...-Surname.xlsx` | maybe | Yes - prompted |

## AOTA File Format

### Example Structure
```xml
<?xml version="1.0"?>
<AotaReturnValue>
  <AOTAVersion>AOTA v4.2025.8.23</AOTAVersion>
  <CameraResult>
    <CameraType>ADVS - corrected</CameraType>
    <MeasuringTool>Tangra</MeasuringTool>
    <VideoSystem>ADVS or AAV</VideoSystem>
    <FramesIntegrated>0</FramesIntegrated>
  </CameraResult>
  <EventResults>
    <EventResults>
      <IsNonEvent>false</IsNonEvent>
      <D_UTC>10 44 45.2 ± 0.4</D_UTC>
      <R_UTC>10 44 47.2 ± 0.5</R_UTC>
      <D_Frame>63</D_Frame>
      <R_Frame>67</R_Frame>
    </EventResults>
    <EventResults>
      <IsNonEvent>true</IsNonEvent>
      <!-- Non-events are filtered out -->
    </EventResults>
  </EventResults>
</AotaReturnValue>
```

### Parsing Rules
1. Only events with `<IsNonEvent>false</IsNonEvent>` are valid
2. D_UTC and R_UTC format: "HH MM SS.S ± E.E"
3. Multiple valid events require user selection
4. Camera metadata is extracted for context

## Template Updates Required

To use this feature, report templates must include the new placeholders in the appropriate cells.

### North American Template
Add to `NorthAmerica_AstReportForm_V5.6.12r_Template.xlsx`:

**Timing Section** (rows 31-37):
- Cell N31: `{{AOTA_D_HOURS}}`
- Cell P31: `{{AOTA_D_MINUTES}}`
- Cell R31: `{{AOTA_D_SECONDS}}`
- Cell T31: `{{AOTA_D_ERROR}}`
- Cell N37: `{{AOTA_R_HOURS}}`
- Cell P37: `{{AOTA_R_MINUTES}}`
- Cell R37: `{{AOTA_R_SECONDS}}`
- Cell T37: `{{AOTA_R_ERROR}}`

### Trans-Tasman Template
Add to `RASNZ_AstReporttForm_V4.1.2.G_locked.xlsx`:

**Timing Section** (rows 31-37):
- Cell G31: `{{AOTA_D_HOURS}}`
- Cell I31: `{{AOTA_D_MINUTES}}`
- Cell K31: `{{AOTA_D_SECONDS}}`
- Cell M31: `{{AOTA_D_ERROR}}`
- Cell G37: `{{AOTA_R_HOURS}}`
- Cell I37: `{{AOTA_R_MINUTES}}`
- Cell K37: `{{AOTA_R_SECONDS}}`
- Cell M37: `{{AOTA_R_ERROR}}`

## Error Handling

The implementation includes comprehensive error handling:

### Observation Type Selection
- Required step - cannot be skipped
- Default to Positive if dialog fails
- Clear labels for each option

### File Selection
- Only shown for Positive/Unsure observations
- Validates file exists
- Checks file extension
- Handles cancellation (report continues without AOTA)

### Parsing
- XML parse errors caught and reported
- Invalid time formats handled gracefully
- Missing data doesn't break report generation
- Non-events (IsNonEvent=true) filtered automatically
- **Preserves decimal precision** from AOTA file

### Event Selection
- No valid events: Warning message, report continues without AOTA data
- Single event: Automatic selection
- Multiple events: User selection dialog
- User cancellation: Report continues without AOTA data

### Report Integration
- AOTA import failure: Warning shown but report still saved
- Post-processing error: Report usable, AOTA data not added
- All errors logged to SharpCap console for debugging
- **Debug logging**: Shows which placeholders are being replaced
- Negative observations: AOTA placeholders remain unreplaced in template

## Benefits

1. **Automation**: No manual transcription of timing data
2. **Accuracy**: Direct import eliminates transcription errors
3. **Precision**: Preserves original decimal places from AOTA analysis
4. **Flexibility**: 
   - Optional AOTA import for Positive/Unsure observations
   - Automatic skip for Negative observations
   - Works with or without AOTA data
5. **User-Friendly**: 
   - Clear dialogs guide through process
   - Observation type affects workflow automatically
   - Descriptive filenames indicate result type
6. **Robust**: 
   - Handles multiple events and various error conditions
   - Filters non-events automatically
7. **Non-Breaking**: If AOTA import fails, report still generates
8. **Smart Defaults**: WAS_MISS field automatically set based on observation type
9. **Logging**: Debug output to SharpCap console for troubleshooting

## Testing Checklist

- [x] Parse valid AOTA file with single event
- [x] Parse AOTA file with multiple events
- [x] Parse AOTA file with only non-events
- [x] Handle invalid/corrupted AOTA file
- [x] Test file selection cancellation
- [x] Test event selection cancellation  
- [x] Test observation type selection (Positive/Negative/Unsure)
- [x] Verify AOTA import skipped for Negative observations
- [x] Verify AOTA import prompted for Positive/Unsure
- [x] Verify North American report with AOTA data
- [x] Verify Trans-Tasman report with AOTA data
- [x] Check placeholder replacement in Excel (post-processing)
- [x] Verify WAS_MISS field logic (inverse of observation type)
- [x] Verify NA filename format (POS/NEG suffix)
- [x] Verify TT filename format (+/- prefix)
- [x] Test with missing D or R times
- [x] Verify decimal precision preservation (0 vs 2 dp)
- [x] Verify error messages are clear
- [x] Check console logging output
- [x] Test that AOTA placeholders remain in template when not imported

## Future Enhancements

Possible improvements:
1. Display camera metadata from AOTA in report comments
2. Add SNR and other AOTA metrics
3. Support for multiple observers/stations from single AOTA file
4. Automatic AOTA file discovery based on event name/date
5. AOTA data preview before import
6. Export timing data to other formats
