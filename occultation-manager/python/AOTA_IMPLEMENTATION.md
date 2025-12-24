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
  - Validates event data

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
- `AOTAFilePickerDialog`: File selection dialog
  - Filters for *.aota.xml files
  - Event context display
  - File validation

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
- AOTA placeholder initialization in `_build_replacements()`
- `import_aota_data(aota_event, replacements)` method
  - Populates AOTA placeholders from parsed event
  - Handles missing data gracefully

### 4. tt_report.py (Trans-Tasman Report Generator)
**Added**:
- AOTA placeholder initialization in `_build_replacements()`
- AOTA placeholders added to `all_placeholders` list
- `import_aota_data(aota_event, replacements)` method
  - Same functionality as NA version

### 5. main_gui.py (Main GUI)
**Modified `generate_report_click()` method**:

**New Workflow**:
1. User selects event and report type
2. Equipment selection dialog
3. Location confirmation dialog
4. **NEW**: AOTA import prompt
   - Yes/No dialog asking if user wants to import AOTA data
   - If Yes: Shows file picker
   - Parses AOTA file
   - If multiple valid events: Shows event selector
   - If single event: Uses automatically
5. Generates report with standard data
6. **NEW**: Adds AOTA data to generated report

**Added `_add_aota_to_existing_report()` method**:
- Post-processes generated Excel file
- Replaces AOTA placeholders in worksheet XML
- Handles shared strings
- Preserves all other report content

## User Workflow

### Generating a Report with AOTA Data

1. **Select Event**: Choose a past event from the event list
2. **Click "Generate Report"**
3. **Select Report Type**: Choose North America or Trans-Tasman
4. **Select Equipment**: Choose telescope and camera
5. **Confirm Location**: Verify/edit observation location
6. **AOTA Import Prompt**: Dialog asks "Do you want to import timing data from an AOTA analysis file?"
   - **Click No**: Report generates without AOTA data (user can fill manually)
   - **Click Yes**: Continue to import process

7. **Select AOTA File** (if Yes):
   - Browse dialog opens filtered to *.aota.xml files
   - Select your AOTA file
   - Click OK

8. **Select Event** (if multiple in file):
   - Dialog shows all valid events with timing details
   - Format: "D: HH:MM:SS.S (±Es) | R: HH:MM:SS.S (±Es) | Duration: Xs"
   - Select the event corresponding to your observation
   - Click "Use Selected Event"

9. **Report Generation**:
   - Report generates with all standard data
   - AOTA timing data automatically filled in designated cells
   - Success message shows file location

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

### File Selection
- Validates file exists
- Checks file extension
- Handles cancellation

### Parsing
- XML parse errors caught and reported
- Invalid time formats handled gracefully
- Missing data doesn't break report generation

### Event Selection
- No valid events: Warning message, report continues without AOTA data
- Single event: Automatic selection
- Multiple events: User selection dialog
- User cancellation: Report continues without AOTA data

### Report Integration
- AOTA import failure: Warning shown but report still saved
- Post-processing error: Report usable, AOTA data not added
- All errors logged to console for debugging

## Benefits

1. **Automation**: No manual transcription of timing data
2. **Accuracy**: Direct import eliminates transcription errors
3. **Flexibility**: Optional feature - works with or without AOTA
4. **User-Friendly**: Clear dialogs guide through process
5. **Robust**: Handles multiple events and various error conditions
6. **Non-Breaking**: If AOTA import fails, report still generates

## Testing Checklist

- [ ] Parse valid AOTA file with single event
- [ ] Parse AOTA file with multiple events
- [ ] Parse AOTA file with only non-events
- [ ] Handle invalid/corrupted AOTA file
- [ ] Test file selection cancellation
- [ ] Test event selection cancellation  
- [ ] Test declining AOTA import
- [ ] Verify North American report with AOTA data
- [ ] Verify Trans-Tasman report with AOTA data
- [ ] Check placeholder replacement in Excel
- [ ] Test with missing D or R times
- [ ] Verify error messages are clear
- [ ] Check console logging output

## Future Enhancements

Possible improvements:
1. Display camera metadata from AOTA in report comments
2. Add SNR and other AOTA metrics
3. Support for multiple observers/stations from single AOTA file
4. Automatic AOTA file discovery based on event name/date
5. AOTA data preview before import
6. Export timing data to other formats
