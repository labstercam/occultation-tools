# GPS LED Line Delay Calibration - Quick Start Guide

## Overview

The GPS LED Line Delay Calibration tool measures rolling shutter line delays using GPS timing LED flashes. It captures frames from multiple apertures over the height of the frame, analyzes GPS PPS flashes, and calculates the time delay per sensor line using linear regression.

## Installation

**No installation needed!** The tool is a single Python file located at:
```
gps-timing-analysis/python/led_line_delay_calibration.py
```
or it is available built in to occultation-manager

## Usage

### From SharpCap IronPython Console:

1. **Connect your camera** in SharpCap
2. **Make sure GPS LED is flashing** (visible in frame)
3. **Open IronPython Console** in SharpCap
4. **Run the script:**
   ```python
   execfile(r"C:\Users\AstroPC\Git\occultation-tools\gps-timing-analysis\python\led_line_delay_calibration.py")
   ```
5. **Calibration form will appear** with "Start Calibration" button

### Running Calibration:

1. **Set capture duration** (default 30 seconds)
2. **Set GPS flash duration** (default 100ms for most GPS units)  
3. **Click "Start Calibration"**
4. **Wait** while calibration runs (status updates shown)
5. **View results** - line delay in ms/line and plot

### Understanding Results:

The calibration will display:
- **Line delay**: Time delay per sensor line in ms/line (e.g., 0.018523 ms/line)
- **Offset**: Base timing offset at Y=0 in ms
- **R-squared**: Goodness of fit (should be >0.9 for good data)
- **Rolling shutter time**: Total time to read full frame in ms
- **Plot**: Scatter plot of measurements with fitted line

Example output:
```
Line delay: 0.018523 ms/line, Offset: -2.341 ms
R-squared: 0.9823
Rolling shutter time: 18.890 ms (for 1920x1080 frame)
```

## Parameters

### Capture Duration
- **Default:** 30 seconds
- **Range:** 10-60 seconds recommended
- **Purpose:** Longer duration = more GPS flashes = better accuracy
- **Trade-off:** Longer times require more stable conditions

### GPS Flash Duration
- **Default:** 100ms
- **Typical values:** 100ms for most GPS timing LEDs
- **Purpose:** Duration of GPS PPS LED flash pulse
- **Note:** Check your GPS unit specifications

## Requirements

### Hardware
- Camera connected to SharpCap
- GPS timing LED visible in frame (or GPS-equipped camera like QHY174GPS)
- GPS LED flashing at 1 PPS rate

### Software
- SharpCap Pro 4.0 or later
- IronPython console enabled

### Camera Settings
- Exposure time should allow LED flashes to be visible
- Frame rate: 10-30 fps typical
- LED should appear as bright spots in top and bottom 10% of frame

## ADV File Replay Mode (Optional)

The tool supports analyzing previously recorded ADV files instead of live capture.

### Prerequisites for ADV Mode

**ADV DLL files must be installed and unblocked:**

1. Download AdvLib DLLs from: http://www.hristopavlov.net/adv/AdvLib.NET.zip
2. Extract and place in `gps-timing-analysis/lib/`:
   - `AdvLib.dll`
   - `AdvLib.Core32.dll`
   - `AdvLib.Core64.dll`
3. **Unblock the DLLs** (Windows blocks files downloaded from the web)

**To unblock, use one of these methods:**

**PowerShell (recommended):**
```powershell
cd gps-timing-analysis\lib
.\unblock_dlls.ps1
```

**Or manually:** Right-click each DLL → Properties → Check "Unblock" → OK

**See detailed instructions:** `gps-timing-analysis/lib/README.md`

### Using ADV Replay Mode

1. Record video with GPS LED flashes using SharpCap (save as ADV format)
2. Run the calibration tool
3. Select "ADV File Replay" mode
4. Browse to your ADV file
5. Set GPS flash duration
6. Click "Start Analysis"

### Benefits of ADV Replay

- **Reusable data:** Analyze same recording multiple times
- **Post-processing:** Don't need camera connected
- **Experimentation:** Try different parameters on same data
- **Archival:** Keep calibration recordings for documentation

## Aperture Configuration

The tool automatically creates two measurement apertures:
- **Top aperture:** Centered at 10% from top of frame
- **Bottom aperture:** Centered at 90% from top of frame
- **Size:** 20% of frame width × 5% of frame height
- **Position:** Automatically centered horizontally

This maximizes the Y-position separation for accurate line delay measurement.

## How It Works

1. **Frame Capture:** Captures frames over specified duration
2. **Aperture Measurement:** Measures mean intensity in top and bottom apertures
3. **GPS Flash Detection:** Identifies GPS PPS flash peaks in light curves
4. **Delay Calculation:** Calculates timing offset for each flash at each Y position
5. **Linear Regression:** Fits line: time_offset = slope × Y + intercept
6. **Results:** Slope = time delay per line (ms/line)

## Troubleshooting

### "No GPS flashes detected"
- **Check LED visibility:** Ensure GPS LED is visible and flashing in frame
- **Check exposure:** May be too short to see LED flashes
- **Check GPS lock:** GPS must have lock for 1 PPS signal
- **Increase duration:** Try 60 seconds for more flashes

### "Not enough measurements"
- **Need at least 2 flashes** - increase capture duration
- **Check aperture positioning** - LED should be visible in both apertures
- **Try manual positioning** of camera to include LED in frame

### "Linear fit failed"
- **Check data quality** - may have too much variation
- **Try again** - sometimes one bad flash can affect results
- **Check camera stability** - vibration can introduce errors

### "Poor R-squared value" (< 0.9)
- **Indicates noisy data** or issues with measurements
- **Check for:** bright stars in apertures, camera vibration, focus issues
- **Try:** Increase capture duration, reposition camera, check focus

## Technical Details

### Algorithm
- Uses GPS PPS flash analysis from `gps-timing-analysis/python/light_curves.py`
- Adapted for IronPython compatibility (no pandas/numpy/scipy)
- Simple least-squares linear regression
- Outlier-robust if R-squared is good

### Data Format
- Creates Tangra-compatible data structures internally
- Light curves stored as lists of dictionaries
- Compatible with existing GPS flash analysis functions

### Performance
- Typical execution time: 30-60 seconds (mostly waiting for capture)
- Memory usage: Minimal (~1-2 MB for 30 second capture)
- CPU usage: Low (measurements done on frame events)

## Output Interpretation

### Rolling Shutter Time
**Definition:** Time to read all lines from top to bottom of sensor

**Typical values:**
- Global shutter: ~0 ms (all lines read simultaneously)
- CMOS rolling shutter: 10-30 ms (typical for 1920x1080 sensors)
- High-speed CMOS: 5-15 ms

**Example:** 
- Frame: 1920 × 1080 pixels
- Line delay: 0.018 ms/line
- Rolling shutter time: 0.018 × 1080 = 19.4 ms

### Line Readout Rate
**Definition:** Number of sensor lines read per millisecond

**Calculation:** 1 / slope (lines/ms)

**Example:**
- Slope: 0.018 ms/line  
- Line rate: 1 / 0.018 = 55.6 lines/ms
- Full frame: 1080 lines @ 55.6 lines/ms = 19.4 ms

## Use Cases

### Asteroid Occultation Timing
- **Purpose:** Correct timestamps for different Y positions in frame
- **Impact:** Can affect event timing by several milliseconds
- **Importance:** Critical for accurate occultation measurements

### Video Timing Analysis
- **Purpose:** Understand frame timing structure
- **Application:** GPS-timed video analysis
- **Benefit:** More accurate timestamp corrections

### Camera Characterization
- **Purpose:** Measure rolling shutter properties
- **Validation:** Verify manufacturer specifications
- **Research:** Study sensor readout patterns

## Advanced Configuration

### Custom Aperture Positions
The code can be modified to change aperture positions:
- Edit `setup_apertures()` call in `run_calibration_thread()`
- Parameters: `top_percent`, `bottom_percent`, `width_percent`, `height_percent`
- Default: `top_percent=0.10`, `bottom_percent=0.90`

### Multiple Apertures
For future enhancement, could add more than 2 apertures:
- Would require code modification in `FrameCaptureHandler` class
- More apertures = better line delay fit = more accuracy

## Code Structure

### Main Components
1. **FrameCaptureHandler** - Manages frame capture and aperture measurements
2. **Data Format Functions** - Convert to Tangra-compatible format
3. **GPS Flash Analysis** - Detect and analyze GPS PPS flashes
4. **Regression Functions** - Fit linear model to line delays
5. **Visualization** - OxyPlot graphs
6. **GUI** - Windows Forms interface

### Dependencies
- **IronPython** standard library only
- **System.Windows.Forms** - GUI
- **System.Drawing** - Graphics
- **OxyPlot** - Plotting (included with SharpCap)
- **SharpCap API** - Camera control and frame capture

### No External Dependencies
- Does NOT require: pandas, numpy, scipy, sklearn
- Does NOT require: gps-timing-analysis folder access
- Fully self-contained single file

## Files Created

### Main Module
- `led_line_delay_calibration.py` (990 lines)
  - All phases implemented
  - Complete GUI
  - Ready to use

### Documentation
- `LED_LINE_DELAY_DEVELOPMENT_PLAN.md` - Detailed development plan
- `LED_LINE_DELAY_QUICKSTART.md` - This file

## Testing Checklist

- [ ] Script loads without errors in IronPython Console
- [ ] GUI form appears when script is run
- [ ] Camera is connected and active
- [ ] GPS LED is visible and flashing in frame
- [ ] "Start Calibration" button works
- [ ] Capture runs for specified duration
- [ ] GPS flashes are detected (check console output)
- [ ] Results display with line delay value
- [ ] Plot shows data points and fitted line
- [ ] R-squared value is > 0.9
- [ ] "Stop" button works to abort calibration

## Support & Feedback

For issues or questions:
1. Check troubleshooting section above
2. Review console output for error messages
3. Verify all requirements are met
4. Try with longer capture duration
5. Check GPS LED is visible and flashing

## Version History

**Version 1.0.0** (February 2026)
- Initial release
- Complete implementation of all phases
- IronPython compatible
- Windows Forms GUI
- OxyPlot visualization
- Linear regression analysis

## Credits

**Development:** Michael Camilleri / Development Team  
**Based on:**
- `Calibration_LED_2024-09-29.py` by Jean-Francois (frame capture)
- `gps-timing-analysis/python/light_curves.py` by Michael Camilleri (GPS flash analysis)

**License:** Same as occultation-tools project

---

**Quick Start:**
```python
# In SharpCap IronPython Console:
execfile(r"C:\Users\AstroPC\Git\occultation-tools\gps-timing-analysis\python\led_line_delay_calibration.py")

# Click "Start Calibration" in the form that appears
# Wait 30 seconds
# View results!
```
