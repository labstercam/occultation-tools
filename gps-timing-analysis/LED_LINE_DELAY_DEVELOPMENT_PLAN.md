# GPS Timing LED Line Delay Calibration - Development Plan

**Version:** 1.0  
**Date:** February 13, 2026  
**Objective:** Add GPS timing LED calibration to measure rolling shutter line delays

---

## Executive Summary

This development plan integrates code from `Calibration_LED_2024-09-29.py` (frame capture and aperture measurement) with `light_curves.py` (GPS flash analysis and line delay calculation) to create a new LED line delay calibration tool for SharpCap.

---

## 1. Code Analysis Summary

### 1.1 Source: Calibration_LED_2024-09-29.py

**Key Components to Extract:**
- **Frame capture mechanism** (lines 107-113):
  ```python
  def framehandler(sender, args):
      if (dumpdata):
          global Mean
          cutout = args.Frame.CutROI(SharpCap.Transforms.SelectionRect)
          Stat = cutout.GetStats()
          Mean = Stat.Item1
          cutout.Release()
  ```
- **Event handler setup**:
  - `SharpCap.SelectedCamera.FrameCaptured += framehandler`
  - Uses `dumpdata` flag to control when measurements are taken
  - Uses `time.sleep(wait_time)` between measurements
  
- **GUI Form structure** (lines 460-617):
  - Uses Windows Forms with Button, CheckBox controls
  - OxyPlot for graphing (optional for our use)
  - Thread-based execution for non-blocking UI

**NOT Using:**
- GPS Calibration LED controls (SharpCap.SelectedCamera.Controls.FindByName("GPS Calibration LED"))
- Calibration Start/End Pos Adjust controls
- ROI repositioning logic specific to LED calibration
- Fermi function fitting for LED position optimization

### 1.2 Source: light_curves.py (gps-timing-analysis)

**Key Functions to Use:**
- **`analyse_gps_flash()`** (lines 219-247):
  - Input: tangra_object with 'light_curve' key
  - Analyzes light curve for GPS flash peaks
  - Returns processed light curve with peak_no, signal_flash, etc.
  
- **`calculate_delays()`** (lines 250-291):
  - Calculates delay between timestamps and GPS PPS flash
  - Uses `y` parameter for vertical position in frame
  - Uses `y_lines` parameter for total sensor lines
  - Returns time_offset for each flash peak
  
- **`line_delay_regression()`** (lines 493-508):
  - Fits linear regression model to line delays
  - Uses sklearn's RANSACRegressor for outlier rejection
  - Plots results with matplotlib
  - Returns: 'Offset of {intercept} ms plus {slope} ms per line'

### 1.3 Source: light_curves_iron.py (occultation-manager)

**Available Functions (IronPython compatible):**
- **`read_tangra_csv_iron()`**: Reads Tangra CSV format (no pandas)
- **`analyse_timestamps_iron()`**: Analyzes timing statistics
- Returns simple Python dictionaries and lists

**Data Structure Expected:**
```python
tangra_object = {
    'file_read_from': file_path,
    'filename_from_tangra': filename,
    'light_curve': [
        {'frameno': 1, 'time_ut': datetime_obj, 'signal_1': 123.4, ...},
        {'frameno': 2, 'time_ut': datetime_obj, 'signal_1': 125.2, ...},
        ...
    ],
    'column_names': ['frameno', 'time_ut', 'signal_1', 'signal_2', ...],
    'exposure_ms': 50.0,
    'acquisition_delay': None
}
```

---

## 2. Architecture & Data Flow

### 2.1 Module Structure

**New File:** `gps-timing-analysis/python/led_line_delay_calibration.py`

**Components:**
1. **Frame Capture System** (adapted from LED calibration)
   - FrameHandler class to manage frame capture events
   - Two aperture measurements (top and bottom)
   - Time series collection over configurable duration

2. **Data Collection & Format**
   - Store measurements in Tangra-compatible format
   - Two columns: signal_top, signal_bottom
   - Frame numbers and timestamps
   - Convert to tangra_object structure

3. **Analysis Pipeline** (using light_curves.py functions)
   - Import analyse_gps_flash, calculate_delays
   - Process top and bottom apertures separately
   - Calculate time offsets for each line position
   - Build dataset: y_position vs time_offset

4. **Regression & Visualization**
   - Use line_delay_regression() or create IronPython version
   - Linear fit: time_offset = intercept + slope * y_line
   - Plot with OxyPlot (IronPython compatible)
   - Display results: "Line delay: {slope:.4f} ms/line, Offset: {intercept:.2f} ms"

5. **GUI Interface** (Windows Forms)
   - Start/Stop buttons
   - Duration setting (default 30 seconds)
   - Aperture position settings (auto or manual)
   - Results display and graph

### 2.2 Data Flow Diagram

```
[SharpCap Camera] 
    |
    v (FrameCaptured event)
[Frame Handler]
    |
    +---> [Top Aperture] ---> measurements_top[]
    |
    +---> [Bottom Aperture] ---> measurements_bottom[]
    |
    v (After collection complete)
[Format as Tangra Objects]
    |---> tangra_obj_top = {light_curve: [...], ...}
    |---> tangra_obj_bottom = {light_curve: [...], ...}
    |
    v
[Analyze GPS Flashes] (light_curves.analyse_gps_flash)
    |---> lcv_top (with peak_no, signal_flash)
    |---> lcv_bottom (with peak_no, signal_flash)
    |
    v
[Calculate Delays] (light_curves.calculate_delays for each peak)
    |---> delays_top: [{peak_no, y, time_offset, ...}, ...]
    |---> delays_bottom: [{peak_no, y, time_offset, ...}, ...]
    |
    v
[Combine & Fit Linear Model]
    |---> all_delays: [(y_top, offset_top), (y_bottom, offset_bottom), ...]
    |---> Linear fit: time_offset = slope * y + intercept
    |
    v
[Display Results & Plot]
    |---> "Line delay: {slope} ms/line"
    |---> Graph with fitted line
```

---

## 3. Detailed Implementation Plan

### Phase 1: Core Frame Capture System

**File:** `led_line_delay_calibration.py`

**Step 1.1: Frame Handler Class**
```python
class FrameCaptureHandler:
    def __init__(self):
        self.capturing = False
        self.measurements_top = []
        self.measurements_bottom = []
        self.timestamps = []
        self.frame_numbers = []
        self.top_rect = None
        self.bottom_rect = None
        
    def framehandler(self, sender, args):
        """Called for each frame - measures both apertures"""
        if not self.capturing:
            return
            
        # Measure top aperture
        cutout_top = args.Frame.CutROI(self.top_rect)
        stat_top = cutout_top.GetStats()
        self.measurements_top.append(stat_top.Item1)  # Mean value
        cutout_top.Release()
        
        # Measure bottom aperture
        cutout_bottom = args.Frame.CutROI(self.bottom_rect)
        stat_bottom = cutout_bottom.GetStats()
        self.measurements_bottom.append(stat_bottom.Item1)
        cutout_bottom.Release()
        
        # Store timestamp and frame number
        # TODO: Get actual timestamp from frame metadata
        self.timestamps.append(datetime.now())
        self.frame_numbers.append(len(self.frame_numbers))
```

**Step 1.2: Aperture Setup**
- Calculate aperture positions based on frame height
- Top aperture: Y = 10% of frame height
- Bottom aperture: Y = 90% of frame height
- Width: 20% of frame width, centered
- Height: 5% of frame height (sufficient for averaging)

```python
def setup_apertures(self, frame_width, frame_height):
    """Setup top and bottom measurement apertures"""
    # Aperture dimensions
    aperture_width = int(frame_width * 0.2)
    aperture_height = int(frame_height * 0.05)
    x_center = int(frame_width * 0.5 - aperture_width * 0.5)
    
    # Top aperture (10% from top)
    y_top = int(frame_height * 0.10)
    self.top_rect = Rectangle(x_center, y_top, aperture_width, aperture_height)
    self.y_top = y_top + aperture_height // 2  # Center Y coordinate
    
    # Bottom aperture (90% from top)
    y_bottom = int(frame_height * 0.90 - aperture_height)
    self.bottom_rect = Rectangle(x_center, y_bottom, aperture_width, aperture_height)
    self.y_bottom = y_bottom + aperture_height // 2  # Center Y coordinate
```

### Phase 2: Data Format Conversion

**Step 2.1: Convert to Tangra-Compatible Format**
```python
def create_tangra_object(self, measurements, y_position, aperture_name):
    """Convert measurements to tangra_object format compatible with light_curves.py
    
    Returns:
        Dictionary matching tangra_object structure from read_tangra_csv()
    """
    light_curve = []
    
    for i, (frame_no, timestamp, signal) in enumerate(
            zip(self.frame_numbers, self.timestamps, measurements)):
        light_curve.append({
            'frameno': frame_no,
            'time_ut': timestamp,
            'signal_1': signal
        })
    
    # Calculate exposure time from timestamp differences
    if len(self.timestamps) > 1:
        time_diffs = [(self.timestamps[i+1] - self.timestamps[i]).total_seconds() * 1000 
                      for i in range(len(self.timestamps)-1)]
        exposure_ms = sum(time_diffs) / len(time_diffs)  # Average
    else:
        # Use SharpCap exposure setting as fallback
        exposure_ms = SharpCap.SelectedCamera.Controls.Exposure.ExposureMs
    
    tangra_obj = {
        'file_read_from': f'LED_Calibration_{aperture_name}',
        'filename_from_tangra': f'LED_Calibration_{aperture_name}',
        'light_curve': light_curve,
        'column_names': ['frameno', 'time_ut', 'signal_1'],
        'exposure_ms': exposure_ms,
        'acquisition_delay': None,
        'y_position': y_position,  # Store Y position for later use
        'aperture_name': aperture_name
    }
    
    return tangra_obj
```

### Phase 3: GPS Flash Analysis

**Step 3.1: Use Existing light_curves.py Functions**

**Note:** Need to import from gps-timing-analysis folder. Two options:
1. Copy necessary functions to new module (preferred for IronPython)
2. Add path and import (if IronPython allows)

```python
# Option 1: Copy essential functions (recommended)
# Copy these functions into led_line_delay_calibration.py:
# - analyse_gps_flash()
# - calculate_delays()
# Simplify to remove pandas/numpy dependencies if needed

def analyze_aperture_delays(self, tangra_obj, exposure_ms, flash_ms=100):
    """Analyze GPS flashes in the aperture light curve
    
    Args:
        tangra_obj: Tangra object with light curve data
        exposure_ms: Exposure time in milliseconds
        flash_ms: GPS flash duration in milliseconds
        
    Returns:
        List of delay measurements with y_position and time_offset
    """
    # Process light curve to find GPS flashes
    lcv = analyse_gps_flash(
        tangra_obj, 
        col='signal_1', 
        exposure_ms=exposure_ms, 
        flash_ms=flash_ms
    )
    
    # Get unique peak numbers (each peak = one GPS flash)
    peak_numbers = set(row['peak_no'] for row in lcv if row['peak_no'] > 0)
    
    # Calculate delays for each peak
    delays = []
    y_position = tangra_obj['y_position']
    frame_height = SharpCap.SelectedCamera.Height  # Or store during setup
    
    for peak_no in peak_numbers:
        delay_result = calculate_delays(
            lcv, 
            peak_no, 
            exposure_ms=exposure_ms,
            flash_ms=flash_ms,
            y=y_position,
            y_lines=frame_height
        )
        
        # Extract the time offset and add to collection
        if delay_result and len(delay_result) > 0:
            delays.append({
                'peak_no': peak_no,
                'y': y_position,
                'time_offset': delay_result[0]['time_offset'],
                'aperture': tangra_obj['aperture_name']
            })
    
    return delays
```

### Phase 4: Line Delay Regression

**Step 4.1: Linear Fit (IronPython Compatible)**
```python
def fit_line_delays(self, all_delays):
    """Fit linear model to line delays: time_offset = slope * y + intercept
    
    Args:
        all_delays: List of dicts with 'y' and 'time_offset' keys
        
    Returns:
        Dictionary with slope, intercept, and R-squared
    """
    if len(all_delays) < 2:
        return None
    
    # Extract x (y positions) and y (time offsets)
    y_positions = [d['y'] for d in all_delays]
    time_offsets = [d['time_offset'] for d in all_delays]
    
    # Simple linear regression (avoid sklearn for IronPython compatibility)
    n = len(y_positions)
    sum_x = sum(y_positions)
    sum_y = sum(time_offsets)
    sum_xx = sum(x*x for x in y_positions)
    sum_xy = sum(x*y for x, y in zip(y_positions, time_offsets))
    
    # Calculate slope and intercept
    slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x * sum_x)
    intercept = (sum_y - slope * sum_x) / n
    
    # Calculate R-squared
    mean_y = sum_y / n
    ss_tot = sum((y - mean_y)**2 for y in time_offsets)
    ss_res = sum((y - (slope * x + intercept))**2 
                 for x, y in zip(y_positions, time_offsets))
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
    
    return {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'n_measurements': n,
        'description': f'Line delay: {slope:.6f} ms/line, Offset: {intercept:.3f} ms'
    }
```

### Phase 5: Visualization

**Step 5.1: OxyPlot Graph (IronPython Compatible)**
```python
def create_line_delay_plot(self, all_delays, fit_result):
    """Create OxyPlot scatter plot with fitted line"""
    import OxyPlot
    
    # Create plot model
    plot_model = OxyPlot.PlotModel()
    plot_model.Title = 'GPS LED Line Delay Calibration'
    
    # Create scatter series for measurements
    scatter_series = OxyPlot.Series.ScatterSeries()
    scatter_series.MarkerType = OxyPlot.MarkerType.Circle
    scatter_series.MarkerSize = 5
    
    for d in all_delays:
        scatter_series.Points.Add(
            OxyPlot.Series.ScatterPoint(d['y'], d['time_offset'])
        )
    
    # Create line series for fitted line
    if fit_result:
        line_series = OxyPlot.Series.LineSeries()
        line_series.LineStyle = OxyPlot.LineStyle.Solid
        line_series.Color = OxyPlot.OxyColors.Red
        
        # Get y range for line
        y_min = min(d['y'] for d in all_delays)
        y_max = max(d['y'] for d in all_delays)
        
        # Add points for fitted line
        line_series.Points.Add(OxyPlot.DataPoint(
            y_min, 
            fit_result['slope'] * y_min + fit_result['intercept']
        ))
        line_series.Points.Add(OxyPlot.DataPoint(
            y_max,
            fit_result['slope'] * y_max + fit_result['intercept']
        ))
        
        plot_model.Series.Add(line_series)
    
    plot_model.Series.Add(scatter_series)
    
    # Set axis labels
    plot_model.Axes.Add(OxyPlot.Axes.LinearAxis(
        Position=OxyPlot.Axes.AxisPosition.Bottom,
        Title='Y Position (pixels)'
    ))
    plot_model.Axes.Add(OxyPlot.Axes.LinearAxis(
        Position=OxyPlot.Axes.AxisPosition.Left,
        Title='Time Offset (ms)'
    ))
    
    return plot_model
```

### Phase 6: GUI Interface

**Step 6.1: Windows Forms Dialog**
```python
class LEDLineDelayCalibrationForm(Form):
    def __init__(self):
        self.InitializeComponent()
        self.capture_handler = FrameCaptureHandler()
        
    def InitializeComponent(self):
        self.Text = "GPS LED Line Delay Calibration"
        self.ClientSize = Size(600, 500)
        self.TopMost = True
        
        # Duration setting
        self.label_duration = Label()
        self.label_duration.Text = "Capture Duration (seconds):"
        self.label_duration.Location = Point(20, 20)
        self.label_duration.AutoSize = True
        
        self.textbox_duration = TextBox()
        self.textbox_duration.Text = "30"
        self.textbox_duration.Location = Point(200, 18)
        self.textbox_duration.Width = 60
        
        # Flash duration setting
        self.label_flash = Label()
        self.label_flash.Text = "GPS Flash Duration (ms):"
        self.label_flash.Location = Point(280, 20)
        self.label_flash.AutoSize = True
        
        self.textbox_flash = TextBox()
        self.textbox_flash.Text = "100"
        self.textbox_flash.Location = Point(450, 18)
        self.textbox_flash.Width = 60
        
        # Start button
        self.button_start = Button()
        self.button_start.Text = "Start Calibration"
        self.button_start.Location = Point(20, 60)
        self.button_start.AutoSize = True
        self.button_start.Click += self.start_calibration
        
        # Stop button
        self.button_stop = Button()
        self.button_stop.Text = "Stop"
        self.button_stop.Location = Point(160, 60)
        self.button_stop.AutoSize = True
        self.button_stop.Enabled = False
        self.button_stop.Click += self.stop_calibration
        
        # Status label
        self.label_status = Label()
        self.label_status.Text = "Ready"
        self.label_status.Location = Point(260, 65)
        self.label_status.AutoSize = True
        
        # Results text box
        self.textbox_results = TextBox()
        self.textbox_results.Location = Point(20, 100)
        self.textbox_results.Size = Size(560, 100)
        self.textbox_results.Multiline = True
        self.textbox_results.ReadOnly = True
        
        # Plot view
        self.plot_view = OxyPlot.WindowsForms.PlotView()
        self.plot_view.Location = Point(20, 210)
        self.plot_view.Size = Size(560, 250)
        
        # Add controls
        self.Controls.Add(self.label_duration)
        self.Controls.Add(self.textbox_duration)
        self.Controls.Add(self.label_flash)
        self.Controls.Add(self.textbox_flash)
        self.Controls.Add(self.button_start)
        self.Controls.Add(self.button_stop)
        self.Controls.Add(self.label_status)
        self.Controls.Add(self.textbox_results)
        self.Controls.Add(self.plot_view)
        
    def start_calibration(self, sender, event):
        """Start LED line delay calibration"""
        # Implementation in Phase 7
        pass
        
    def stop_calibration(self, sender, event):
        """Stop ongoing calibration"""
        # Implementation in Phase 7
        pass
```

### Phase 7: Main Calibration Logic

**Step 7.1: Complete Calibration Workflow**
```python
def run_calibration(self):
    """Main calibration workflow - runs in separate thread"""
    try:
        # 1. Setup
        self.label_status.Text = "Setting up apertures..."
        camera = SharpCap.SelectedCamera
        frame_width = camera.Width
        frame_height = camera.Height
        
        self.capture_handler.setup_apertures(frame_width, frame_height)
        
        # 2. Start frame capture
        self.label_status.Text = "Capturing frames..."
        self.capture_handler.capturing = True
        camera.FrameCaptured += self.capture_handler.framehandler
        
        # 3. Wait for specified duration
        duration = float(self.textbox_duration.Text)
        time.sleep(duration)
        
        # 4. Stop frame capture
        self.capture_handler.capturing = False
        camera.FrameCaptured -= self.capture_handler.framehandler
        
        # 5. Create tangra objects
        self.label_status.Text = "Processing data..."
        tangra_top = self.capture_handler.create_tangra_object(
            self.capture_handler.measurements_top,
            self.capture_handler.y_top,
            'top'
        )
        tangra_bottom = self.capture_handler.create_tangra_object(
            self.capture_handler.measurements_bottom,
            self.capture_handler.y_bottom,
            'bottom'
        )
        
        # 6. Analyze GPS flashes
        exposure_ms = tangra_top['exposure_ms']
        flash_ms = float(self.textbox_flash.Text)
        
        delays_top = self.capture_handler.analyze_aperture_delays(
            tangra_top, exposure_ms, flash_ms
        )
        delays_bottom = self.capture_handler.analyze_aperture_delays(
            tangra_bottom, exposure_ms, flash_ms
        )
        
        # 7. Combine and fit
        self.label_status.Text = "Fitting line delays..."
        all_delays = delays_top + delays_bottom
        
        if len(all_delays) < 2:
            raise Exception("Not enough GPS flashes detected. Need at least 2.")
        
        fit_result = self.capture_handler.fit_line_delays(all_delays)
        
        # 8. Display results
        results_text = "LED Line Delay Calibration Results\n"
        results_text += "=" * 40 + "\n\n"
        results_text += f"Measurements captured: {len(all_delays)}\n"
        results_text += f"Top aperture (Y={tangra_top['y_position']}): "
        results_text += f"{len(delays_top)} flashes\n"
        results_text += f"Bottom aperture (Y={tangra_bottom['y_position']}): "
        results_text += f"{len(delays_bottom)} flashes\n\n"
        results_text += f"{fit_result['description']}\n"
        results_text += f"R-squared: {fit_result['r_squared']:.4f}\n\n"
        results_text += f"Rolling shutter time: "
        results_text += f"{fit_result['slope'] * frame_height:.3f} ms\n"
        
        self.textbox_results.Text = results_text
        
        # 9. Plot
        plot_model = self.capture_handler.create_line_delay_plot(
            all_delays, fit_result
        )
        self.plot_view.Model = plot_model
        
        self.label_status.Text = "Calibration complete"
        
    except Exception as ex:
        self.label_status.Text = "Error: " + str(ex)
        self.textbox_results.Text = "Error occurred:\n" + str(ex)
```

---

## 4. File Organization

### New Files to Create
1. **`gps-timing-analysis/python/led_line_delay_calibration.py`**
   - Main module with all classes and functions
   - Approximately 600-800 lines

### Files to Reference (Not Modify)
1. **`gps-timing-analysis/python/light_curves.py`**
   - Copy key functions: analyse_gps_flash(), calculate_delays()
   - Adapt to remove pandas/numpy for IronPython compatibility

2. **`occultation-manager/python/light_curves_iron.py`**
   - Use as reference for IronPython-compatible patterns
   - May call helper functions if needed

---

## 5. Testing Plan

### Test 1: Frame Capture
- **Goal:** Verify frame handler captures data from both apertures
- **Method:** Run for 10 seconds, check measurements_top and measurements_bottom have ~200 entries (20 fps camera)
- **Success Criteria:** Both lists populated, timestamps incrementing

### Test 2: Data Format
- **Goal:** Verify tangra_object format is correct
- **Method:** Create tangra objects and inspect structure
- **Success Criteria:** Has all required keys, light_curve is list of dicts

### Test 3: GPS Flash Detection
- **Goal:** Verify GPS flashes are detected in light curves
- **Method:** Use known GPS LED flash sequence
- **Success Criteria:** Peak_no values > 0, reasonable number of flashes detected

### Test 4: Delay Calculation
- **Goal:** Verify time offsets are calculated correctly
- **Method:** Check delays list has entries with time_offset values
- **Success Criteria:** Time offsets in reasonable range (0-50 ms for typical rolling shutter)

### Test 5: Linear Fit
- **Goal:** Verify regression gives sensible results
- **Method:** Check slope is positive and in expected range
- **Success Criteria:** 
  - Slope: 0.001 - 0.1 ms/line (typical for rolling shutter)
  - R-squared > 0.9 for good data

### Test 6: GUI
- **Goal:** Verify GUI operates correctly
- **Method:** Launch form, run calibration, view results
- **Success Criteria:** Form displays, buttons work, plot appears

---

## 6. Implementation Schedule

### Week 1: Core Functionality
- [ ] Day 1-2: Create frame capture system (Phase 1)
- [ ] Day 3: Implement data format conversion (Phase 2)
- [ ] Day 4-5: Copy and adapt GPS flash analysis functions (Phase 3)

### Week 2: Analysis & Visualization
- [ ] Day 1-2: Implement line delay regression (Phase 4)
- [ ] Day 3: Create plotting functionality (Phase 5)
- [ ] Day 4-5: Build GUI interface (Phase 6)

### Week 3: Integration & Testing
- [ ] Day 1-2: Complete calibration workflow (Phase 7)
- [ ] Day 3-4: Testing (all phases)
- [ ] Day 5: Documentation and cleanup

---

## 7. Key Design Decisions

### Decision 1: GPS LED Control (Optional)
**Chosen:** Disable by default, make optional
**Rationale:** Not all cameras have GPS LED capability, simpler for general use

### Decision 2: Aperture Positioning
**Chosen:** Automatic (10% and 90% of frame height)
**Rationale:** Maximizes Y-position separation for better line delay measurement

### Decision 3: Data Format
**Chosen:** Tangra-compatible dictionary structure
**Rationale:** Allows reuse of existing light_curves.py functions without modification

### Decision 4: Dependencies
**Chosen:** Copy and simplify functions instead of importing gps-timing-analysis
**Rationale:** IronPython compatibility, avoid path issues, easier distribution

### Decision 5: Regression Method
**Chosen:** Simple least-squares linear regression (no sklearn)
**Rationale:** IronPython compatibility, sufficient for linear relationship

---

## 8. Success Criteria

### Minimum Viable Product (MVP)
1. ✅ Captures frames from two apertures for configurable duration
2. ✅ Detects GPS flashes in both apertures
3. ✅ Calculates time offsets for top and bottom positions
4. ✅ Fits linear model to line delays
5. ✅ Displays results: slope (ms/line) and intercept
6. ✅ Shows plot of measurements with fitted line
7. ✅ GUI with Start/Stop buttons

### Enhanced Features (Post-MVP)
- Manual aperture positioning
- Save results to file (CSV)
- Multi-aperture support (more than 2)
- Real-time progress display
- Integration with main Occultation Manager GUI

---

## 9. Risks & Mitigation

### Risk 1: IronPython Compatibility
**Issue:** Functions from light_curves.py use pandas, numpy, scipy
**Mitigation:** Copy functions and adapt to use only Python standard library

### Risk 2: GPS Flash Detection
**Issue:** Flashes may not be detected if aperture positioning is poor
**Mitigation:** Use wide apertures (20% frame width), multiple measurements

### Risk 3: Insufficient Measurements
**Issue:** May not capture enough GPS flashes in duration
**Mitigation:** Default 30 seconds should give ~30 flashes at 1 PPS

### Risk 4: Frame Capture Performance
**Issue:** High frame rate may cause dropped measurements
**Mitigation:** Use simple mean calculation, efficient frame handler

---

## 10. Future Enhancements

1. **Adaptive aperture positioning** - Automatically find LED position
2. **Multiple aperture lines** - More than 2 for better fit
3. **Export calibration data** - Save to file for analysis
4. **Integration testing** - Compare with known camera specifications
5. **FITS/ADV file analysis** - Offline analysis of recorded videos
6. **Automatic camera detection** - Adjust parameters based on camera model

---

## Appendix A: Required Imports

```python
# System imports (IronPython compatible)
import time
import math
import os
from datetime import datetime, timedelta

# .NET/CLR imports for SharpCap
import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("OxyPlot")
clr.AddReference("OxyPlot.WindowsForms")

from System.Windows.Forms import *
from System.Drawing import *
import OxyPlot
import OxyPlot.WindowsForms
import OxyPlot.Series
import OxyPlot.Axes

# SharpCap - available in IronPython environment
# SharpCap.SelectedCamera
# SharpCap.Transforms
```

## Appendix B: Function Dependency Matrix

| New Function | Depends On | Source |
|---|---|---|
| FrameCaptureHandler.framehandler() | SharpCap API | LED Calibration |
| setup_apertures() | SharpCap API | New |
| create_tangra_object() | - | New, inspired by light_curves_iron |
| analyse_gps_flash() | - | light_curves.py (copy) |
| calculate_delays() | - | light_curves.py (copy) |
| fit_line_delays() | - | New (simplified regression) |
| create_line_delay_plot() | OxyPlot | New |
| run_calibration() | All above | New |

---

**End of Development Plan**
