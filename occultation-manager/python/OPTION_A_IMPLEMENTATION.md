# Option A Implementation - Separate Camera Lists

## Overview
Converted from Option B (split timing fields) to Option A (separate camera lists with report_type selector) to simplify the camera configuration interface.

## Changes Summary

### Option B (Removed - "Too Messy")
- **4 timing fields per camera:**
  - `timing_na` + `timing_device_na` (North America)
  - `timing_tt` + `timing_device_tt` (Trans-Tasman)
- Separate dropdown lists for each report type
- ~160 lines of UI code for timing fields
- Complex field management in dialogs

### Option A (Implemented)
- **3 fields per camera:**
  - `report_type`: Dropdown with "NA", "TT", or "Both"
  - `timing`: Single timing field (8 options)
  - `timing_device`: Single timing device field (13 options)
- Simplified UI (~80 lines of code)
- Cameras filtered by report type during report generation

## Modified Files

### 1. equipment_dialogs.py
**UI Field Changes (Lines 425-535):**
- Removed: `combo_timing_na`, `combo_timing_device_na`, `combo_timing_tt`, `combo_timing_device_tt`
- Added: `combo_report_type` (DropDownList: "NA", "TT", "Both", default="Both")
- Added: `combo_timing` (8 options: "GPS - time inserted", "GPS - other linking", etc.)
- Added: `combo_timing_device` (13 options: "ADVS", "AFT or OFT Flash Tag", etc.)

**Method Updates:**
- `camera_selected()`: Loads `report_type`, `timing`, `timing_device` from camera data
- `clear_fields()`: Clears new field structure
- `add_camera()`: Reads 3 fields instead of 4, passes to config
- `update_camera()`: Reads 3 fields instead of 4, passes to config

### 2. config.py
**Method Signature Changes:**
- `add_camera()`: Changed from `(timing_na, timing_device_na, timing_tt, timing_device_tt)` to `(report_type, timing, timing_device)`
- `update_camera()`: Changed from `(timing_na, timing_device_na, timing_tt, timing_device_tt)` to `(report_type, timing, timing_device)`

**Camera Dictionary Structure:**
```python
{
    'id': str(uuid.uuid4()),
    'name': name,
    'detector': detector,
    'report_type': report_type,     # NEW: "NA", "TT", or "Both"
    'timing': timing,               # Single field
    'timing_device': timing_device, # Single field
    'other_info': other_info,
    'video_format': video_format,
    'exposure_integration': exposure_integration
}
```

### 3. na_report.py
**Field Access (Line ~304-305):**
- Changed from: `camera.get('timing_na', camera.get('timing', ...))`
- Changed to: `camera.get('timing', 'GPS - other linking')`
- Changed from: `camera.get('timing_device_na', camera.get('timing_device', ...))`
- Changed to: `camera.get('timing_device', 'SharpCap')`

### 4. tt_report.py
**Field Access (Line ~278, 282):**
- Changed from: `camera.get('timing_tt', camera.get('timing', ...))`
- Changed to: `camera.get('timing', 'GPS - other linking')`
- Changed from: `camera.get('timing_device_tt', camera.get('timing_device', ...))`
- Changed to: `camera.get('timing_device', 'SharpCap')`

## Implementation Details

### Report Type Options
- **"NA"**: Camera available only for North America reports
- **"TT"**: Camera available only for Trans-Tasman reports
- **"Both"**: Camera available for both report types (default)

### Timing Options (8 total)
1. GPS - time inserted
2. GPS - other linking
3. GPS - KIWI
4. IOTA-VTI
5. WWV
6. Visual
7. Other
8. Unknown

### Timing Device Options (13 total)
1. ADVS
2. AFT or OFT Flash Tag
3. IOTA-VTI
4. KIWI OSD
5. Drift Method
6. Astro Audio Time Sync Box
7. SharpCap
8. Other software
9. Other
10. Unknown
11. (blank)
12. GPS - time inserted
13. GPS - other linking

## Backward Compatibility
The camera_selected() method in equipment_dialogs.py still supports the old field names:
- Falls back to `timing` if `timing_na` or `timing_tt` not found
- Falls back to `timing_device` if `timing_device_na` or `timing_device_tt` not found

## UI Improvements
- Net reduction: ~30 lines of code
- UI height reduction: 80 pixels (2 fewer field rows)
- Complexity reduction: 4 timing fields → 3 fields total
- Simpler user experience: One set of timing options instead of two

## Future Enhancement
Report generators (na_report.py and tt_report.py) could be enhanced to filter cameras by `report_type`:
- NA reports: Show only cameras where `report_type` in ['NA', 'Both']
- TT reports: Show only cameras where `report_type` in ['TT', 'Both']

This would provide separate camera lists per report type as originally intended in Option A.

## Testing Recommendations
1. Create new camera with report_type="Both"
2. Verify timing and timing_device fields save correctly
3. Generate NA report - verify timing/timing_device used
4. Generate TT report - verify timing/timing_device used
5. Test existing cameras with old field names (backward compatibility)
6. Verify camera list display shows all cameras regardless of report_type

## Migration Notes
Existing cameras with old field names (`timing_na`, `timing_device_na`, `timing_tt`, `timing_device_tt`) will continue to work:
- The dialog loads with fallback logic
- On first update, they will be converted to new field structure
- No data migration script needed
