# AOTA Import Feature - Quick Start Guide

## Status Note (2026-03)

This guide reflects the current report workflow using `LocationConfirmDialog` and `ComprehensiveReportDialog`.

## What is AOTA?

AOTA (Asteroid Occultation Timing Analysis) is a tool that analyzes your occultation videos and extracts precise disappearance (D) and reappearance (R) times. The analysis results are saved in XML files with the extension `.aota.xml`.

## How to Use AOTA Import

### Step 1: Generate Your AOTA File
1. Process your occultation video with AOTA
2. AOTA will create a file like: `eventname.aota.xml`
3. Save this file somewhere you can find it

### Step 2: Open Report in Occultation Manager
1. Open Occultation Manager in SharpCap
2. Select a **past event** from the event list
3. Click **"Report"** button

### Step 3: Follow the Report Generation Flow
The current flow uses a **Comprehensive Report Dialog**:

1. **Confirm Location**: Verify your observation site coordinates.
2. **Choose Report + Equipment**: Select report type, telescope, and camera.
3. **Set Observation Type**: Positive, Negative, or Unsure.
4. **Browse Data Folder**: Select one folder containing your files.
  - Tangra CSV
  - Optional AOTA XML (`*.aota.xml`)
  - Optional AOTA Report text file
5. **Select Files in Lists**: Pick the detected files in the dialog lists.

### Step 4: AOTA Data Selection Rules
- **Positive / Unsure**: At least one of AOTA XML or AOTA Report is required.
- **Negative**: AOTA inputs are optional.
- If both AOTA XML and AOTA Report are provided, AOTA Report timing is preferred in report generation.

### Step 5: Select Event (only if multiple events in file)
If your AOTA file contains multiple events:
1. A dialog shows all events with their timing details
2. Example display:
   ```
   Event 1: D: 10:44:45.2 (±0.4s) | R: 10:44:47.2 (±0.5s) | Duration: 2.0s
   Event 2: D: 10:45:12.3 (±0.3s) | R: 10:45:15.1 (±0.4s) | Duration: 2.8s
   ```
3. Select the event that matches your observation
4. Click **"Use Selected Event"**

If only one event exists, it's selected automatically.

### Step 6: Report Generated!
- Report saves with all your observation details
- AOTA timing data is filled when supplied
- Success message shows the file location

## What Data Gets Imported?

The AOTA import fills these fields in your report:

**Disappearance Time (D)**:
- Hours (HH)
- Minutes (MM)
- Seconds (SS.S)
- Error/Uncertainty (±E.E seconds)

**Reappearance Time (R)**:
- Hours (HH)
- Minutes (MM)  
- Seconds (SS.S)
- Error/Uncertainty (±E.E seconds)

These are placed in separate cells as individual components, making it easy for the report form to display them correctly.

## Example AOTA File

Your AOTA file might look like this:
```xml
<?xml version="1.0"?>
<AotaReturnValue>
  <AOTAVersion>AOTA v4.2025.8.23</AOTAVersion>
  <CameraResult>
    <CameraType>ADVS - corrected</CameraType>
    <MeasuringTool>Tangra</MeasuringTool>
  </CameraResult>
  <EventResults>
    <EventResults>
      <IsNonEvent>false</IsNonEvent>
      <D_UTC>10 44 45.2 ± 0.4</D_UTC>
      <R_UTC>10 44 47.2 ± 0.5</R_UTC>
    </EventResults>
  </EventResults>
</AotaReturnValue>
```

The parser extracts:
- D time: 10:44:45.2 with error ±0.4
- R time: 10:44:47.2 with error ±0.5

## Common Scenarios

### Scenario 1: Single Event
✓ AOTA file has one event → Automatically selected → Report generated

### Scenario 2: Multiple Events  
✓ AOTA file has 3 events → Dialog shows all 3 → You select one → Report generated

### Scenario 3: No Valid Events
⚠ AOTA file only has non-events → Warning shown → Report still generated without timing

### Scenario 4: No AOTA File
✓ Do not select AOTA XML or AOTA Report (Negative observation) → Report generated

### Scenario 5: AOTA Import Fails
⚠ Parse error → Error message → Report still generated → Fill timing manually

## Tips

1. **Keep AOTA files organized**: Name them clearly with event details
2. **One analysis per report**: Match AOTA file to the correct event
3. **Check your data**: Always review the imported times in the final report
4. **It's optional**: You can always skip AOTA import and enter times manually
5. **Re-import if needed**: Generate the report again with a different AOTA file if you made a mistake

## Troubleshooting

### "Failed to parse AOTA file"
- Check the file is a valid XML file
- Make sure it's actually from AOTA (not renamed or corrupted)
- Try opening the file in a text editor to verify it's readable

### "No valid events found"
- AOTA might have marked all events as non-events
- Check your AOTA analysis settings
- You can still complete the report and enter times manually

### "Multiple events found" but I only analyzed one
- AOTA may create placeholder entries for multiple detections
- Look at the timing details and select the event that matches your observation
- The display shows D time, R time, and duration to help identify the correct event

### Report generated but AOTA data missing
- Check the Excel file - data should be in the timing section (rows 31-37)
- Verify you selected an AOTA XML or AOTA Report file in the dialog lists
- Check console output for any error messages
- If it fails, you can still enter the data manually

## Need Help?

- Check the console output for detailed error messages
- Review `AOTA_IMPLEMENTATION.md` for technical details
