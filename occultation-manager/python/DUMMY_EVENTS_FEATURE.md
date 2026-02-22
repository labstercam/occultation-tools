# Dummy Event Generator Feature

## Overview
The Dummy Event Generator creates realistic test occultation events for testing the occultation-manager without requiring OccultWatcher Cloud access. Generated events are added directly to your main occultations files and can be easily deleted when no longer needed.

## Quick Start

**Generate Test Events:**
1. Click **"Generate Dummy Events"** in the toolbar
2. Enter number of events, start time, and location
3. Click Generate
4. Events appear immediately in your event grid

**Remove Test Events:**
1. Select the dummy events (they have IDs like "TEST-1001", "TEST-1002")
2. Click **"Delete"** in Quick Filters
3. Confirm deletion
4. Events are removed from your local files

## Features

### User Interface
- **Button**: "Generate Dummy Events" button in the main toolbar (after "Refresh")
- **Dialog**: Comprehensive configuration dialog for event generation

### Configuration Options

1. **Number of Events**
   - Range: 1-100 events
   - Default: 5

2. **Start Time**
   - **Option A**: UTC Start Time (YYYY-MM-DD HH:MM:SS format)
   - **Option B**: Minutes from now (default: 30 minutes)

3. **Interval Between Events**
   - Spacing in minutes between consecutive events
   - Default: 15 minutes

4. **Observer Location**
   - Latitude (degrees, -90 to 90)
   - Longitude (degrees, -180 to 180)
   - Station Name (text)
   - Default: Melbourne, Australia area

## Intelligent Event Generation

### Visibility Calculation
Events are generated with proper sky visibility at the observer's location:
- **Sidereal Time**: Calculates LST at event time based on observer longitude
- **RA Selection**: Places objects within ±3 hours of LST (near meridian)
- **DEC Range**: Uses declinations between -20° and +20° (near celestial equator)
- **Result**: Events are actually observable from the given location at the specified time

### Realistic Parameters
All event parameters are randomly generated within sensible ranges:

- **Star Magnitude**: 8.0 - 13.0
- **Magnitude Drop**: 1.5 - 6.0 magnitudes
- **Event Duration**: 5 - 25 seconds
- **Event Uncertainty**: 1 - 5 seconds
- **Star Altitude**: 30° - 70° (well-placed)
- **Exposure**: Automatically calculated based on star magnitude
  - Mag ≤ 10.0: 20ms
  - Mag ≤ 12.0: 40ms
  - Mag ≤ 13.0: 80ms
  - Mag > 13.0: 160ms

### Naming Convention
- **Asteroid Names**: "Test 1", "Test 2", "Test 3", etc.
- **Asteroid Numbers**: "(1)", "(2)", "(3)", etc.
- **Event IDs**: "TEST-1001", "TEST-1002", etc.
- **Star Catalog**: Random UCAC4 identifiers

### Generated Fields
Each event includes all required fields:
- Event times (UTC and local)
- Coordinates (RA/DEC, Alt/Az)
- Station information (name, lat, lon, elevation)
- Camera settings (exposure, gain)
- Star identification
- OccultWatcher Cloud URL (test URL)

## Usage Workflow

1. Click **"Generate Dummy Events"** button in toolbar
2. Configure generation parameters in dialog
3. Click **"Generate"**
4. Events are:
   - Generated with realistic parameters
   - Appended to occultations.json and occultations_latest.json
   - Automatically loaded into the event grid
5. Success message shows number of events created
6. When done testing, select dummy events and click **"Delete"** button to remove them

## Technical Implementation

### Files
- **dummy_event_generator.py**: Complete implementation
  - `DummyEventGeneratorDialog`: Configuration UI
  - `DummyEventGenerator`: Event generation logic

### Integration
- **main_gui.py**: 
  - Import module
  - Add "Generate Dummy Events" toolbar button
  - Implement click handler
  - Reload events from files after generation

### Storage
- Generated events are appended to **occultations.json** (main event file)
- Also appended to **occultations_latest.json** for consistency
- Events persist alongside real OccultWatcher Cloud events
- No separate test file - all events in one place

### Sidereal Time Algorithm
Uses standard astronomical calculations:
1. Convert UTC time to Julian Date
2. Calculate days since J2000.0
3. Calculate Greenwich Mean Sidereal Time (GMST)
4. Convert to Local Sidereal Time (LST) using longitude

### Event Structure
Generated events match the exact structure of OccultWatcher events, including:
- All timing fields (event, start, end, goto, pre-goto)
- Coordinate data (RA, DEC, Alt, Az)
- Photometry (magnitudes, drops)
- Station location (lat, lon, elevation)
- Camera settings (exposure, gain)
- Metadata (IDs, URLs, names)

Events are stored in occultations.json with unique IDs starting at TEST-1001, TEST-1002, etc.

## Benefits

1. **No Cloud Dependency**: Test without OccultWatcher access
2. **Custom Scenarios**: Create specific test cases
3. **Location-Aware**: Events visible from your observatory
4. **Realistic Data**: Proper ranges for all parameters
5. **Flexible Timing**: Test past, present, or future events
6. **Batch Creation**: Generate multiple events at once
7. **Easy Cleanup**: Use Delete button to remove when done
8. **Integrated Storage**: Events mixed with real events - test realistic workflows

## Error Handling

- Input validation for all fields
- Range checking (latitude, longitude, counts)
- Date/time format validation
- File I/O error handling
- User-friendly error messages

## Deleting Dummy Events

Generated dummy events can be removed using the **Delete** button in Quick Filters:

1. Select the dummy events in the event grid
2. Click **"Delete"** button
3. Confirm deletion in the dialog
4. Events are removed from both occultations.json and occultations_latest.json
5. Grid refreshes automatically

**Note**: Dummy events have IDs like "TEST-1001", "TEST-1002", making them easy to identify and select for deletion. The deletion is permanent on your local PC but won't affect OccultWatcher Cloud.
