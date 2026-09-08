# Prepoint Implementation Plan for Occultation Manager

## Overview

This document provides a comprehensive plan for implementing Astrid's prepoint functionality in an Occultation Manager tool using IronPython in SharpCap. The prepoint system calculates where to point a telescope so that a target will drift into the field of view at a specific future time, which is crucial for occultation timing.

## Table of Contents
1. Core Algorithm Analysis
2. Key Components and Code Extraction
3. IronPython Implementation Strategy
4. SharpCap Integration Plan
5. Detailed Implementation Steps
6. Testing and Validation

## 1. Core Algorithm Analysis

### Prepoint Calculation Logic

The prepoint algorithm follows these steps:
1. **Input**: Target coordinates (RA/DEC) and event time
2. **Output**: Prepoint coordinates (RA/DEC) for current time
3. **Process**:
   - Convert target to AltAz coordinates at event time (with atmospheric refraction)
   - Keep same AltAz coordinates but at prepoint time (now + offset)
   - Convert back to equatorial coordinates (ICRS/J2000)

### Mathematical Foundation

The key calculation is performed in `AstCoord.prepointCoords()`:

```python
def prepointCoords(self, targetInFOVTime: datetime, prepointTime: datetime):
    # Get the coordinate of the target in JNow for the event time
    (coord, event_time) = self.__raDec360Deg('icrs', jnow = True, obsdatetime = targetInFOVTime)

    # Get the AltAz Coordinate for the target at the event time
    event_altAz = coord.transform_to(AltAz(obstime=event_time, 
                                           location=AstSite.location(),
                                           pressure=AstSite.pressure*u.pascal,
                                           temperature=AstSite.temperature*u.Celsius,
                                           relative_humidity=AstSite.rh,
                                           obswl=0.65*u.micron))

    # Use same AltAz but at prepoint time
    prepoint_altAz = SkyCoord(AltAz(obstime = prepointTime,
                                     az = event_altAz.az,
                                     alt = event_altAz.alt,
                                     location=AstSite.location(),
                                     pressure=AstSite.pressure*u.pascal,
                                     temperature=AstSite.temperature*u.Celsius,
                                     relative_humidity=AstSite.rh,
                                     obswl=0.65*u.micron))
    
    prepoint_icrs = prepoint_altAz.transform_to('icrs')
    prepoint_coords = AstCoord(prepoint_icrs)
    
    return prepoint_coords
```

### Time Offset Strategy
- **Goto-capable mounts**: 10 seconds future offset
- **Non-goto mounts**: 15 seconds future offset
- Rationale: Allows time for plate solving/sync before event

### Drift Calculations
```python
# Calculate drift in arcseconds per second
delta_time = (dte_event_time - prepointTime).total_seconds()
delta_time %= AstCoord.SIDEREAL_DAY_LENGTH * 3600.0  # Wrap around per sidereal day
angular_separation = prepoint.angular_separation(targetCoords)  # Degrees
drift_speed = angular_separation / delta_time  # Degrees per second
```

## 2. Key Components and Code Extraction

### 2.1 AstCoord Class (Coordinate System)

**Essential Methods to Implement:**

1. **`prepointCoords()`** - Core prepoint calculation
2. **`altAzRefracted()`** - Alt/Az with atmospheric refraction
3. **`angular_separation()`** - Angular distance between coordinates
4. **Coordinate conversion methods**:
   - `from360Deg()` - Create from RA/DEC in degrees
   - `raDec360Deg()` - Get RA/DEC in degrees
   - `raDec24Deg()` - Get RA/DEC in hours/degrees
   - `raDecHMSStr()` - Get RA/DEC as HMS/DMS strings

**Actual Code from Astrid - `prepointCoords()`**:
```python
def prepointCoords(self, targetInFOVTime: datetime,  prepointTime: datetime):
    print('***** targetInFOVTime', targetInFOVTime)
    # Get the coordinate of the target in JNow for the event time
    (coord, event_time) = self.__raDec360Deg('icrs', jnow = True, obsdatetime = targetInFOVTime)
    print('***** event_time', event_time)

    # Reference: https://stackoverflow.com/questions/60305302/converting-equatorial-to-alt-az-coordinates-is-very-slow
    conf.remote_timeout = 0.1
    conf.auto_download = False

    # Get the AltAz Coordinate for the target at the event time
    event_altAz = coord.transform_to(AltAz(obstime=event_time, location=AstSite.location(), pressure=AstSite.pressure*u.pascal, temperature=AstSite.temperature*u.Celsius, relative_humidity=AstSite.rh, obswl=0.65*u.micron))
    print('**** event_altAz:', event_altAz)

    prepoint_altAz = SkyCoord(AltAz(obstime = prepointTime, az = event_altAz.az, alt = event_altAz.alt, location=AstSite.location(), pressure=AstSite.pressure*u.pascal, temperature=AstSite.temperature*u.Celsius, relative_humidity=AstSite.rh, obswl=0.65*u.micron))
    prepoint_icrs = prepoint_altAz.transform_to('icrs')

    print("**** prepointTime:", prepointTime)
    print("**** prepointAltAz:", prepoint_altAz)

    # Reference: https://stackoverflow.com/questions/60305302/converting-equatorial-to-alt-az-coordinates-is-very-slow
    conf.remote_timeout = 10.0
    conf.auto_download = True

    prepoint_coords = AstCoord(prepoint_icrs)

    return prepoint_coords
```

### 2.2 AstSite Class (Site Configuration)

**Essential Properties**:
```python
class AstSite:
    lat = 0.0      # Latitude degrees
    lon = 0.0      # Longitude degrees
    alt = 0.0      # Altitude meters
    pressure = 0.0 # Pascals
    temperature = 0.0 # Celsius
    rh = 0.0       # 0 to 1.0 (relative humidity)

    @classmethod
    def set(cls, name: str, lat: float, lon: float, alt: float, 
            pressure=0.0, temperature=15.0, rh=0.5):
        cls.name = name
        cls.lat = lat
        cls.lon = lon
        cls.alt = alt
        cls.pressure = pressure
        cls.temperature = temperature
        cls.rh = rh

    @classmethod
    def location(cls):
        return EarthLocation.from_geodetic(lon=cls.lon, lat=cls.lat, height=cls.alt*u.m)
```

### 2.3 UiPanelPrepoint Class (UI Interface)

**Key UI Components**:
1. **Prepoint RA/DEC display** - Shows calculated prepoint coordinates
2. **Prepoint Time display** - Shows time when prepoint position is valid
3. **Direction Indicator** - Visual arrows showing offset after plate solve
4. **FOV Error display** - Percentage error relative to field of view
5. **Drift Time display** - Time target takes to drift through FOV
6. **Action buttons**:
   - "Goto" (for goto-capable mounts)
   - "Photo, Solve and Sync"

**Actual Code from Astrid - `calcPrepoint()`**:
```python
def calcPrepoint(self):
    self.prepointTime = datetime.utcnow() + timedelta(seconds = self.future_secs)
    #self.prepointTime = datetime(2023, 9, 13, 5, 15, 00)

    self.widgetPrepointTime.setText(self.prepointTime.strftime('%Y-%m-%dT%H:%M:%SZ'))

    if self.trackingCapable:
        event_time = self.object['start_time']
    else:
        event_time = self.object['event_time']

    dte_event_time = datetime.strptime(event_time, '%Y-%m-%dT%H:%M:%S')

    targetCoords = AstCoord.from360Deg(self.object['ra'], self.object['dec'], 'icrs')

    print('Target (ICRS): %s @ %s' % (targetCoords.raDecHMSStr('icrs'), dte_event_time.strftime('%Y-%m-dT%H:%M:%SZ')))

    prepointCoords = targetCoords.prepointCoords(targetInFOVTime = dte_event_time,  prepointTime = self.prepointTime)

    print('Prepoint Position (ICRS): %s @ %s' % (prepointCoords.raDecHMSStr('icrs'), self.prepointTime.strftime('%Y-%m-%dT%H:%M:%SZ')))

    self.prepoint = prepointCoords

    # Calculate drift in arcseconds per second
    print('Time1:', self.prepointTime)
    print('Time2:', dte_event_time)
    self.delta_time =  (dte_event_time - self.prepointTime).total_seconds()
    self.delta_time %= AstCoord.SIDEREAL_DAY_LENGTH * 3600.0			# Wrap around per sidereal day
    self.angular_separation = self.prepoint.angular_separation(targetCoords)	# Degrees
    self.drift_speed = self.angular_separation/self.delta_time
    print('angular seperation: %0.7fdeg  drift speed: %0.7fdeg/sec  delta time: %dsecs' % (self.angular_separation, self.drift_speed, self.delta_time))
    
    (ra, dec) = self.prepoint.raDecStrForSettingFormat('icrs')
    self.widgetRA.setText(ra)
    self.widgetDEC.setText(dec)
```

### 2.4 CameraModel Integration

**Essential Camera Methods**:
1. **`takePhotoSolveSync()`** - Take photo, plate solve, sync mount
2. **`gotoNoTracking()`** - Move mount without tracking enabled
3. **`syncLastPlateSolve()`** - Sync mount to plate solved position

**Code Snippet - `takePhotoSolveSync()`**:
```python
def takePhotoSolveSync(self, dialog, prepoint_coord):
    self.photoCallback = self.takePhotoSolveSync2
    self.dialogPrepoint = dialog
    self.prepoint_coord = prepoint_coord
    self.startRecording()

def takePhotoSolveSync2(self):
    self.photoCallback = None
    
    if self.settings['polar_align_test']:
        self.ui.messageBoxPrepointTestModeWarning()
        fname = '/media/pi/ASTRID/TestPlateSolveImages/midi80-qhy5Lii-FR.fit'
        self.updateDisplayOptions()
    else:
        fname = self.lastFitFile
        
        if self.filePlateSolve:
            fname = QFileDialog.getOpenFileName(self.ui, 'Open file', 
                                                 Settings.getInstance().astrid_drive, 
                                                 'FITS files (*.fit)')[0]
            if len(fname) != 0:
                print('Filename:', fname)
                self.lastFitFile = fcommon
                self.updateDisplayOptions()
            else:
                return

    self.platesolveCallbackSuccess = self.takePhotoSolveSync3
    self.platesolveCallbackFailed = self.takePhotoSolveSyncFailed
    self.solveField(fname, override_target_coord = self.prepoint_coord)

def takePhotoSolveSync3(self, position, field_size, altAz, target_position):
    self.lastSolvedPosition = position
    self.solvedTargetPixelPosition = target_position
    self.platesolveCallbackSuccess = None
    self.platesolveCallbackFailed = None
    print('Syncing solved position:', position.raDecHMSStr('icrs'))
    self.syncLastPlateSolve()
    self.dialogPrepoint.photoProcComplete(position, field_sum, altAz)
    self.updateDisplayOptions()
```

**Code Snippet - `gotoNoTracking()`**:
```python
def gotoNoTracking(self, coords, gotoButton):
    self.prepointGotoButton = gotoButton
    self.indi.telescope.tracking(False)
    self.ui.panelMount.resetUpcomingMeridianFlasher()
    if self.mountCanMove():
        self.indi.telescope.goto(coords, no_tracking = True, 
                                 slewCompleteCallback = self.gotoNoTrackingComplete)

def gotoNoTrackingComplete(self):
    self.prepointGotoButton.setEnabled(True)
```

### 2.5 AstUtils Calculations

**Essential Utility Methods**:
1. **`calculatePlateSolveTargetDelta()`** - Calculate offset between plate solved position and target

**Code Snippet**:
```python
def calculatePlateSolveTargetDelta(cls, plateSolveCoords, altAzPlateSolve, targetCoords):
    altAzTarget = targetCoords.altAzRefracted(frame='icrs')

    print('AltAzTarget:', altAzTarget)
    print('AltAzPlateSolve:', altAzPlateSolve)
    print('RaDecTarget:', targetCoords)
    print('RaDecPlateSolve:', plateSolveCoords)

    # Calculate delta
    # Az: negative is rotate anti clockwise, positive is rotate clockwise
    # Alt: negative is move down, positive is move up
    deltaAlt = altAzTarget[0] - altAzPlateSolve[0]
    deltaAz = altAzTarget[1] - altAzPlateSolve[1]

    # Calculate nearest azimuth direction if it's more than 180 degrees to target
    if deltaAz > 180.0:
        deltaAz = -(360.0 - deltaAz)
    elif deltaAz < -180.0:
        deltaAz = -(-360.0 - deltaAz)

    # Calculate Ra/Dec delta in 360deg
    plateSolveRaDec = plateSolveCoords.raDec360Deg(frame='icrs', jnow = True)
    targetRaDec = targetCoords.raDec360Deg(frame='icrs', jnow = True)
    deltaRa = targetRaDec[0] - plateSolveRaDec[0]
    deltaDec = targetRaDec[1] - plateSolveRaDec[1]

    return ((deltaAlt, deltaAz), (deltaRa, deltaDec))
```

### 2.6 Direction Indicator (UiWidgetDirection)

**Key Features**:
- Visual arrows showing Alt/Az and RA/DEC offsets
- Text display of offset values
- Support for different display modes (AltAz, RA/DEC, Both)

## 3. IronPython Implementation Strategy

### 3.1 Coordinate System Without Astropy

Since IronPython may not have access to `astropy`, we need alternative approaches:

**Option A: Simplified Calculations** (for basic prepoint)
- Use basic spherical trigonometry formulas
- Approximate refraction using simple models
- Less accurate but simpler to implement

**Option B: Python.NET with Astropy** (if available)
- Use Python.NET to call Python libraries
- Requires full Python installation alongside IronPython

**Option C: Custom Astronomy Library**
- Implement basic astronomical calculations:
  - Coordinate transformations (ICRS → AltAz)
  - Atmospheric refraction (using Saemundsson formula)
  - Precession/nutation approximations

**Recommended Formulas**:

**Altitude/Azimuth Calculation** (from RA/DEC):
```
HA = LST - RA (in radians)
alt = asin(sin(lat) * sin(dec) + cos(lat) * cos(dec) * cos(HA))
az = atan2(-sin(HA) * cos(dec), cos(lat) * sin(dec) - sin(lat) * cos(dec) * cos(HA))
```

**Atmospheric Refraction** (Saemundsson formula):
```
R = 1.02 / tan(alt + 10.3/(alt + 5.11))  # in arcminutes
Refracted altitude = alt + R/60  # Convert to degrees
```

**Sidereal Time Calculation**:
```
GMST = 18.697374558 + 24.06570982441908 * D
D = days since J2000.0
LST = GMST + longitude/15 (in hours)
```

### 3.2 Site Configuration Implementation

**IronPython Site Class**:
```python
class OccultationSite:
    def __init__(self):
        self.lat = 0.0      # Latitude in degrees
        self.lon = 0.0      # Longitude in degrees  
        self.alt = 0.0      # Altitude in meters
        self.pressure = 101325.0  # Standard pressure in Pascals
        self.temperature = 15.0   # Temperature in Celsius
        self.humidity = 0.5      # Relative humidity (0-1)
    
    def set_location(self, lat, lon, alt, pressure=101325.0, 
                     temperature=15.0, humidity=0.5):
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self.pressure = pressure
        self.temperature = temperature
        self.humidity = humidity
```

### 3.3 Prepoint Calculator Implementation

**IronPython PrepointCalculator**:
```python
class PrepointCalculator:
    SIDEREAL_DAY_LENGTH = 23.9344696  # hours
    
    def __init__(self, site):
        self.site = site
    
    def prepoint_coords(self, target_ra, target_dec, event_time, prepoint_time):
        # Convert target RA/DEC to AltAz at event time
        altaz_event = self.ra_dec_to_altaz(target_ra, target_dec, event_time)
        
        # Use same AltAz at prepoint time
        altaz_prepoint = altaz_event  # Same coordinates
        
        # Convert back to RA/DEC at prepoint time
        ra_dec_prepoint = self.altaz_to_ra_dec(altaz_prepoint[0], altaz_prepoint[1], 
                                               prepoint_time)
        
        return ra_dec_prepoint
    
    def ra_dec_to_altaz(self, ra, dec, time):
        # Implement coordinate transformation
        # Include atmospheric refraction
        
    def altaz_to_ra_dec(self, alt, az, time):
        # Implement reverse transformation
        
    def angular_separation(self, ra1, dec1, ra2, dec2):
        # Calculate angular distance between two points
        # Using cosine formula for spherical coordinates
```

## 4. User Workflow: Observer's Perspective

### 4.1 How Observers Use Astrid's Prepoint Interface

**Typical Observer Workflow in Astrid:**

1. **Event Selection**:
   - Observer selects an occultation event from the object list
   - Event details (RA/DEC, event time, star magnitude) are displayed
   - Observer clicks "Prepoint" button to initiate the prepoint process

2. **Prepoint Dialog Display**:
   - A dedicated prepoint dialog window opens
   - Shows calculated prepoint RA/DEC coordinates
   - Displays prepoint time (current time + 10-15 seconds)
   - Shows target coordinates and event time for reference

3. **Initial Calculation**:
   - System automatically calculates:
     - Prepoint position based on event time and current time
     - Angular separation between prepoint and target
     - Drift speed (how fast target will move through FOV)
   - All calculations are displayed in real-time

4. **Mount Control Options**:

   **For Goto-Capable Mounts**:
   - "Goto" button becomes available
   - Observer clicks "Goto" to send telescope to prepoint position
   - Mount moves WITHOUT tracking enabled (critical for drift alignment)
   - Button disables during slew, re-enables when complete

   **For Non-Goto Mounts**:
   - Observer manually slews telescope using hand controller
   - Uses displayed prepoint coordinates as target
   - No "Goto" button available in interface

5. **Plate Solve Verification**:
   - Observer clicks "Photo, Solve and Sync" button
   - Astrid captures an image through the camera
   - Image is automatically plate solved
   - Solved coordinates are compared with prepoint coordinates
   - Direction indicator shows visual arrows for adjustment:
     - Red/Green arrows for Altitude (Up/Down)
     - Red/Green arrows for Azimuth (Left/Right)
     - Text displays exact offset values in degrees/arcminutes

6. **Fine-Tuning and Sync**:
   - Observer uses direction indicators to manually adjust telescope
   - For small offsets: uses mount hand controller
   - For larger offsets: may use "Goto" again (if available)
   - Once aligned, system can sync mount to exact prepoint position
   - Sync ensures mount's internal coordinates match actual sky position

7. **Drift Monitoring**:
   - System calculates time until target enters field of view
   - Shows "Drift Time Through FOV" (e.g., "2.5x3.1 minutes")
   - Displays FOV error percentage based on plate solve accuracy
   - Observer monitors countdown to event time

8. **Event Readiness**:
   - Telescope remains stationary (tracking disabled)
   - Target drifts into field of view naturally
   - Observer ready to record occultation at precise event time

### 4.2 Key User Interface Elements in Astrid

**Prepoint Dialog Components**:

1. **Coordinate Displays**:
   ```
   Prepoint RA:  14h29m43.0s
   Prepoint DEC: +62°40'46"
   Prepoint Time: 2023-09-13T05:14:50Z
   ```

2. **Calculation Results**:
   ```
   Angular Separation: 0.125°
   Drift Speed: 0.0125°/sec
   Time to FOV Entry: 2m15s
   ```

3. **Direction Indicator**:
   - Visual compass-like display
   - Color-coded arrows (Red = move this direction)
   - Numerical offsets in degrees/arcminutes
   - Separate displays for Alt/Az and RA/DEC

4. **Control Buttons**:
   - **Goto**: Move mount to prepoint (goto mounts only)
   - **Photo, Solve and Sync**: Capture, solve, and align
   - **Exit Prepoint**: Close prepoint dialog

5. **Status Indicators**:
   - Mount connection status
   - Tracking enabled/disabled
   - Plate solve progress
   - Slew completion status

### 4.3 Observer Decision Points

**Critical Decisions During Prepoint**:

1. **Time Offset Selection**:
   - Default: 10 seconds (goto mounts) or 15 seconds (non-goto)
   - Observer can adjust based on:
     - Mount slew speed
     - Plate solve time required
     - Personal preference

2. **Tracking Control**:
   - **Tracking OFF during prepoint**: Essential for drift alignment
   - **Tracking ON after sync**: Optional for monitoring
   - Decision depends on mount behavior and personal workflow

3. **Plate Solve Frequency**:
   - Initial solve after goto
   - Optional additional solves for fine-tuning
   - Balance between accuracy and time consumption

4. **Manual vs Automated Adjustment**:
   - Small offsets: Manual adjustment with hand controller
   - Large offsets: New goto command
   - Decision based on offset magnitude and mount precision

### 4.4 Common Observer Scenarios

**Scenario A: Goto Mount with Plate Solving**
1. Select event → Click Prepoint
2. Review calculated coordinates
3. Click "Goto" (mount slews, tracking off)
4. Click "Photo, Solve and Sync"
5. Adjust using direction indicators
6. Sync mount to exact position
7. Monitor drift until event

**Scenario B: Non-Goto Mount**
1. Select event → Click Prepoint  
2. Review calculated coordinates
3. Manually slew to prepoint RA/DEC
4. Click "Photo, Solve and Sync"
5. Adjust manually using direction indicators
6. Monitor drift until event

**Scenario C: Quick Prepoint (No Plate Solve)**
1. Select event → Click Prepoint
2. Review coordinates
3. Goto or manually slew
4. Skip plate solve (experienced observer)
5. Directly monitor for event

### 4.5 User Experience Considerations

**What Makes Astrid's Prepoint Effective**:

1. **Visual Feedback**:
   - Clear direction indicators reduce cognitive load
   - Color coding (Red/Green) for intuitive understanding
   - Real-time coordinate updates

2. **Progressive Disclosure**:
   - Basic info first (coordinates, time)
   - Advanced info on demand (drift calculations, FOV error)
   - Direction indicators only appear after plate solve

3. **Error Prevention**:
   - Automatic tracking disable during goto
   - Coordinate validation before sending to mount
   - Clear error messages for common issues

4. **Workflow Flexibility**:
   - Supports both goto and non-goto mounts
   - Optional plate solving for accuracy
   - Adjustable time offsets for different scenarios

### 4.6 Learning Curve for New Observers

**Typical Learning Progression**:

1. **Beginner**:
   - Follows step-by-step: Select → Prepoint → Goto → Solve → Sync
   - Relies heavily on direction indicators
   - Uses default time offsets

2. **Intermediate**:
   - Understands drift calculations
   - Adjusts time offsets based on conditions
   - May skip plate solve for bright targets

3. **Advanced**:
   - Manually calculates prepoint mentally as cross-check
   - Uses multiple plate solves for maximum accuracy
   - Customizes workflow based on specific equipment

**Common Pitfalls and Solutions**:

1. **"Target not in FOV after prepoint"**:
   - Cause: Incorrect site coordinates or time
   - Solution: Verify site settings and system clock

2. **"Plate solve failed"**:
   - Cause: Poor image quality or wrong FOV
   - Solution: Adjust exposure, check focus, verify plate solve settings

3. **"Mount not moving"**:
   - Cause: Parked mount or connection issue
   - Solution: Unpark mount, check ASCOM/INDI connection

### 4.7 Integration with Overall Astrid Workflow

**Prepoint in Context of Full Observation**:

1. **Planning Phase**:
   - Load predictions → Filter events → Select target

2. **Setup Phase**:
   - Polar align → Focus camera → Set exposure

3. **Prepoint Phase** (This document's focus):
   - Calculate prepoint → Position telescope → Verify alignment

4. **Recording Phase**:
   - Start recording at appropriate time
   - Monitor event progress
   - Stop recording after event

5. **Post-Event Phase**:
   - Review recording → Extract light curve → Submit report

**Prepoint as Critical Path**:
- Most time-sensitive part of observation
- Requires careful execution for success
- Directly impacts data quality

## 5. SharpCap Integration Plan

### 4.1 SharpCap Script Architecture

**IronPython Script Structure for SharpCap**:
```python
# PrepointManager.py - Main IronPython script for SharpCap
import clr
import System
from System import DateTime
import math
import time

# ASCOM Telescope interface
clr.AddReference("ASCOM.Astrometry")
clr.AddReference("ASCOM.DriverAccess")
from ASCOM.DriverAccess import Telescope

# SharpCap API imports (if available)
# import SharpCap

class PrepointManager:
    def __init__(self):
        self.site = OccultationSite()
        self.calculator = PrepointCalculator(self.site)
        self.telescope = None
        self.connected = False
        
    def connect_telescope(self, telescope_name="ASCOM.Simulator.Telescope"):
        """Connect to ASCOM telescope"""
        try:
            self.telescope = Telescope(telescope_name)
            self.telescope.Connected = True
            self.connected = True
            return True
        except Exception as e:
            print(f"Failed to connect to telescope: {e}")
            return False
    
    def calculate_prepoint(self, target_ra, target_dec, event_time_str):
        """Calculate prepoint coordinates"""
        # Parse event time
        event_time = DateTime.Parse(event_time_str)
        
        # Calculate prepoint time (now + offset)
        prepoint_time = DateTime.UtcNow.AddSeconds(10)  # Default 10 seconds
        
        # Calculate prepoint coordinates
        prepoint_ra, prepoint_dec = self.calculator.prepoint_coords(
            target_ra, target_dec, event_time, prepoint_time
        )
        
        return {
            'prepoint_ra': prepoint_ra,
            'prepoint_dec': prepoint_dec,
            'prepoint_time': prepoint_time,
            'event_time': event_time
        }
    
    def goto_prepoint(self, ra, dec):
        """Send prepoint coordinates to telescope"""
        if not self.connected:
            return False
            
        try:
            # Convert coordinates to mount format (hours for RA)
            ra_hours = ra / 15.0  # Convert degrees to hours
            
            # Disable tracking for prepoint (like Astrid's gotoNoTracking)
            self.telescope.Tracking = False
            
            # Slew to prepoint position
            self.telescope.SlewToCoordinates(ra_hours, dec)
            return True
        except Exception as e:
            print(f"Failed to goto prepoint: {e}")
            return False
    
    def enable_tracking(self, enable=True):
        """Enable or disable tracking"""
        if self.connected:
            self.telescope.Tracking = enable
```

### 4.2 UI Components for SharpCap

**SharpCap Prepoint Dialog Requirements**:
1. **Input Fields**:
   - Target RA (hours or degrees)
   - Target DEC (degrees)
   - Event time (UTC) - date/time picker
   - Site coordinates (lat/lon/alt) - with save/load capability
   - Atmospheric conditions (pressure/temp/humidity) - optional
   - Time offset (seconds) - adjustable (default: 10s for goto, 15s for non-goto)

2. **Output Display**:
   - Prepoint RA/DEC (in both degrees and HMS/DMS)
   - Prepoint time (now + offset)
   - Drift speed (degrees/sec and arcsec/sec)
   - Angular separation from target (degrees)
   - Time to drift through FOV (minutes)
   - FOV error percentage (after plate solve)

3. **Control Elements**:
   - "Calculate Prepoint" button
   - "Connect Telescope" button
   - "Goto Prepoint" button (with "no tracking" option)
   - "Enable Tracking" toggle
   - "Take Photo & Plate Solve" button (if SharpCap supports)
   - "Sync to Prepoint" button (after plate solve)
   - Direction indicator (visual arrows for Alt/Az and RA/DEC offsets)

4. **Status Display**:
   - Connection status
   - Mount tracking status
   - Current mount coordinates
   - Plate solve results

### 4.3 Mount Control Integration

**ASCOM Telescope Interface Details**:
```python
# Complete ASCOM integration example
class TelescopeController:
    def __init__(self):
        self.telescope = None
        
    def connect(self, driver_name):
        """Connect to ASCOM telescope driver"""
        self.telescope = Telescope(driver_name)
        self.telescope.Connected = True
        
        # Check mount capabilities
        self.can_slew = self.telescope.CanSlew
        self.can_slew_async = self.telescope.CanSlewAsync
        self.can_set_tracking = self.telescope.CanSetTracking
        self.can_sync = self.telescope.CanSync
        
        return True
    
    def get_current_coordinates(self):
        """Get current telescope coordinates"""
        ra = self.telescope.RightAscension  # Hours
        dec = self.telescope.Declination    # Degrees
        return ra, dec
    
    def slew_to_prepoint(self, ra_hours, dec_degrees, no_tracking=False):
        """Slew to prepoint coordinates with optional tracking control"""
        if no_tracking and self.can_set_tracking:
            self.telescope.Tracking = False
            
        if self.can_slew_async:
            self.telescope.SlewToCoordinatesAsync(ra_hours, dec_degrees)
        else:
            self.telescope.SlewToCoordinates(ra_hours, dec_degrees)
    
    def sync_to_coordinates(self, ra_hours, dec_degrees):
        """Sync mount to specific coordinates (after plate solve)"""
        if self.can_sync:
            self.telescope.SyncToCoordinates(ra_hours, dec_degrees)
    
    def set_tracking(self, enable):
        """Enable or disable tracking"""
        if self.can_set_tracking:
            self.telescope.Tracking = enable
```

### 4.4 Plate Solve Integration with SharpCap

**SharpCap Plate Solving API Integration**:
```python
# Example of integrating with SharpCap's plate solving capabilities
class PlateSolveIntegration:
    def __init__(self, sharpcap_app):
        self.app = sharpcap_app
        
    def capture_and_solve(self):
        """Capture image and plate solve using SharpCap's built-in solver"""
        # Capture single frame
        self.app.CaptureSingleFrame()
        
        # Wait for capture to complete
        time.sleep(2)
        
        # Trigger plate solve
        # Note: Actual API calls depend on SharpCap's scripting interface
        solved_ra = self.app.PlateSolveResult.RightAscension
        solved_dec = self.app.PlateSolveResult.Declination
        field_size = self.app.PlateSolveResult.FieldSize
        
        return solved_ra, solved_dec, field_size
    
    def calculate_offsets(self, solved_ra, solved_dec, target_ra, target_dec):
        """Calculate offsets between solved position and target"""
        # Convert to degrees if needed
        solved_ra_deg = solved_ra * 15.0  # Hours to degrees
        target_ra_deg = target_ra * 15.0
        
        # Calculate RA/DEC offsets
        ra_offset = target_ra_deg - solved_ra_deg
        dec_offset = target_dec - solved_dec
        
        # Adjust for RA wrap-around
        if ra_offset > 180.0:
            ra_offset = -(360.0 - ra_offset)
        elif ra_offset < -180.0:
            ra_offset = -(-360.0 - ra_offset)
            
        return ra_offset, dec_offset
```

### 4.5 Direction Indicator Implementation

**Simple Direction Indicator for SharpCap**:
```python
class DirectionIndicator:
    def __init__(self):
        self.ra_offset = 0.0
        self.dec_offset = 0.0
        self.alt_offset = 0.0
        self.az_offset = 0.0
        
    def update_offsets(self, ra_offset, dec_offset, alt_offset=None, az_offset=None):
        """Update offset values and refresh display"""
        self.ra_offset = ra_offset
        self.dec_offset = dec_offset
        
        if alt_offset is not None:
            self.alt_offset = alt_offset
        if az_offset is not None:
            self.az_offset = az_offset
            
        self.refresh_display()
    
    def refresh_display(self):
        """Update visual display of direction arrows"""
        # Create simple text display
        display_text = f"""
        RA Offset: {self.ra_offset:+.3f}°
        DEC Offset: {self.dec_offset:+.3f}°
        """
        
        if self.alt_offset != 0.0 or self.az_offset != 0.0:
            display_text += f"""
            Alt Offset: {self.alt_offset:+.3f}°
            Az Offset: {self.az_offset:+.3f}°
            """
            
        # Add directional arrows based on offsets
        if self.ra_offset > 0:
            display_text += "\nMove WEST (RA+)"
        elif self.ra_offset < 0:
            display_text += "\nMove EAST (RA-)"
            
        if self.dec_offset > 0:
            display_text += "\nMove NORTH (DEC+)"
        elif self.dec_offset < 0:
            display_text += "\nMove SOUTH (DEC-)"
            
        return display_text
```

### 4.6 Complete Workflow Integration

**End-to-End Prepoint Workflow**:
1. **Setup Phase**:
   - Load occultation prediction data (RA/DEC, event time)
   - Configure site coordinates and atmospheric conditions
   - Connect to ASCOM telescope

2. **Calculation Phase**:
   - Calculate prepoint coordinates based on event time
   - Display prepoint RA/DEC and prepoint time
   - Calculate drift speed and angular separation

3. **Positioning Phase**:
   - Slew telescope to prepoint position (with tracking disabled)
   - Optionally: Take photo and plate solve
   - Calculate offsets between solved position and prepoint
   - Display direction indicators for manual adjustment
   - Sync mount to prepoint position (if plate solve successful)

4. **Monitoring Phase**:
   - Monitor drift until event time
   - Calculate time remaining until target enters FOV
   - Provide visual/audible alerts as event approaches

### 4.7 SharpCap Script Menu Integration

**Adding Prepoint to SharpCap Menu**:
```python
# Example of creating SharpCap menu items
def create_sharpcap_menu():
    """Create menu items in SharpCap for prepoint functionality"""
    # This would depend on SharpCap's specific scripting API
    # Typically involves creating menu items that call your functions
    
    menu_structure = {
        'Prepoint': {
            'Calculate Prepoint': calculate_prepoint_callback,
            'Goto Prepoint': goto_prepoint_callback,
            'Plate Solve and Sync': plate_solve_callback,
            'Settings': {
                'Site Configuration': site_config_callback,
                'Time Offset': time_offset_callback
            }
        }
    }
    
    return menu_structure
```

### 4.8 Error Handling and User Feedback

**Robust Error Handling**:
```python
class PrepointErrorHandler:
    @staticmethod
    def handle_telescope_error(error):
        """Handle telescope communication errors"""
        error_messages = {
            'NotConnected': 'Telescope not connected. Please connect first.',
            'Parked': 'Telescope is parked. Please unpark before moving.',
            'Slewing': 'Telescope is already slewing. Wait for completion.',
            'BelowHorizon': 'Target is below horizon.',
            'InvalidValue': 'Invalid coordinate values provided.'
        }
        
        error_type = type(error).__name__
        return error_messages.get(error_type, f'Telescope error: {str(error)}')
    
    @staticmethod
    def validate_coordinates(ra, dec):
        """Validate coordinate ranges"""
        if ra < 0 or ra >= 360:
            return False, 'RA must be between 0 and 360 degrees'
        if dec < -90 or dec > 90:
            return False, 'DEC must be between -90 and +90 degrees'
        return True, ''
```

## 5. Detailed Implementation Steps

### Step 1: Create Core Prepoint Calculator
1. Implement `PrepointCalculator` class in IronPython
2. Add basic astronomical calculations (RA/DEC ↔ AltAz)
3. Implement atmospheric refraction model
4. Test with known coordinates and times

### Step 2: Build SharpCap UI
1. Create dialog/form for prepoint calculations
2. Add input fields for target coordinates and event time
3. Add output display for prepoint results
4. Implement "Calculate" button functionality

### Step 3: Mount Control Integration
1. Integrate with ASCOM Telescope interface
2. Add "Goto Prepoint" button
3. Handle coordinate format conversion (JNow/J2000)
4. Add tracking control (enable/disable as needed)

### Step 4: Plate Solve Integration
1. Implement image capture in SharpCap
2. Add plate solve functionality (if available)
3. Calculate offsets between solved position and prepoint
4. Display direction indicators

### Step 5: Drift Calculations and FOV Analysis
1. Calculate drift speed based on angular separation and time delta
2. Compute FOV error percentage based on plate solve results
3. Calculate time target takes to drift through field of view
4. Display all calculations in UI

## 6. Testing and Validation

### Test Cases:
1. **Coordinate Transformation Tests**
   - Known RA/DEC → AltAz → RA/DEC round-trip
   - Compare with online calculators or Astrid results

2. **Prepoint Calculation Tests**
   - Test with different time offsets (10s, 15s, 30s)
   - Verify drift calculations match expectations

3. **Mount Control Tests**
   - Test goto functionality with simulator
   - Verify tracking control works correctly

4. **Integration Tests**
   - Full workflow: Calculate → Goto → Plate Solve → Sync
   - Verify offsets are calculated correctly

### Validation Strategy:
1. Cross-check calculations with Astrid results
2. Compare with online astronomical calculators
3. Test with known occultation events
4. Verify mount positioning accuracy

## Conclusion

The prepoint system from Astrid provides a robust method for positioning telescopes for occultation timing. By implementing this in IronPython for SharpCap, you can create a valuable tool for occultation observers. The key challenges are:

1. **Coordinate transformations** without astropy
2. **Atmospheric refraction** calculations
3. **Integration with SharpCap's ASCOM** interface
4. **Plate solve integration** (if available)

The implementation can be phased, starting with basic prepoint calculations and gradually adding more sophisticated features like plate solving and direction indicators.

**Next Steps**:
1. Start with the core `PrepointCalculator` class
2. Build minimal UI for calculations
3. Integrate with ASCOM mount control
4. Add plate solving if SharpCap supports it
5. Implement direction indicators for visual guidance