"""
GPS LED Line Delay Calibration for SharpCap
Measures rolling shutter line delays using GPS timing LED

This module captures frames from multiple 10x10 pixel apertures distributed across the
frame height, analyzes GPS PPS flashes, and calculates rolling shutter line delays with
linear regression.

Features:
- Multiple 10x10 pixel apertures distributed across frame height (every 100 pixels)
- Automatically accounts for ROI and binning settings
- Correct binning handling: camera reports unbinned ROI, frame data is binned
- GPS PPS flash detection and timing analysis
- Quality filtering to remove transition frames (outliers)
- Linear regression for line delay calculation with R-squared fit quality
- TANGRA CSV export for external analysis

Usage:
    From SharpCap IronPython Console:
    execfile(r"C:\path\to\gps-timing-analysis\python\led_line_delay_calibration.py")
    
    Then click "Start Calibration" in the GUI

Technical Implementation:
    Camera API (SharpCap):
        - camera.ROI: Returns Rectangle (X=Pan, Y=Tilt, Width/Height in binned pixels)
        - camera.Controls.Resolution.Value: May report unbinned ROI dimensions
        - camera.ROI.Width/Height: Actual binned frame data dimensions
        - Binning: camera.Controls.FindByName("Binning").Value (e.g., "2x2")
    
    Frame Timestamps:
        - Live: BufferFrame.Info.EndTimeStamp → converted to mid-frame (subtract exposure/2)
        - ADV: AdvFrameInfo.UtcMidExposureTime → already mid-frame timestamp
        - Processing: calculate_delays_iron() adds exposure/2 to get end-frame timing
        - Consistent with tested original light_curves.py algorithm
    
    ADV File Integration:
        - Uses .NET AdvLib through IronPython CLR
        - AdvFile2 class for file I/O
        - Extracts frame pixels, timestamps, and exposure metadata
        - Converts .NET DateTime to Python datetime for compatibility

Author: Michael Camilleri / Development Team
Date: February 2026
Version: 3.0.0 - Production release with ADV replay support
"""

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
from System.Threading import Thread, ApartmentState, ParameterizedThreadStart
import OxyPlot
import OxyPlot.WindowsForms
import OxyPlot.Series
import OxyPlot.Axes

# ADV file support (optional)
try:
    import adv_helper
    ADV_AVAILABLE = adv_helper.is_advlib_available()
except:
    ADV_AVAILABLE = False
    print("ADV support not available (adv_helper.py not found or AdvLib DLLs missing)")



# =============================================================================
# PHASE 1: FRAME CAPTURE SYSTEM
# =============================================================================

class FrameCaptureHandler:
    """Handles frame capture and aperture measurements for line delay calibration
    
    This class manages the frame capture event handler and records light intensity
    measurements from multiple apertures distributed across the frame height.
    """
    
    def __init__(self):
        """Initialize the frame capture handler"""
        self.capturing = False
        self.apertures = []  # List of (y_position, Rectangle) tuples
        self.measurements = {}  # Dictionary: y_position -> list of measurements
        self.timestamps = []
        self.frame_numbers = []
        self.frame_width = 0
        self.frame_height = 0
        self.unbinned_frame_height = 0  # Physical sensor lines for rolling shutter calc
        self.binning = 1
        self.frame_count = 0  # Counter to verify frames are being captured
        
    def framehandler(self, sender, args):
        """Frame capture event handler - called for each camera frame
        
        Measures mean light intensity in all apertures across the frame.
        Stores measurements, timestamps, and frame numbers.
        
        Args:
            sender: Event sender (camera)
            args: Frame event arguments containing frame data
        """
        if not self.capturing:
            return
        
        self.frame_count += 1
        
        # Print confirmation on first frame
        if self.frame_count == 1:
            print("First frame received - capture working!")
            print("  Frame dimensions: {0}x{1} pixels (from camera.ROI)".format(
                self.frame_width, self.frame_height))
            print("  Converting EndTimeStamp to mid-frame (subtracting {0} ms)".format(
                getattr(self, 'exposure_ms', 0.0) / 2.0))
        
        try:
            # Measure all apertures
            for y_pos, rect in self.apertures:
                cutout = args.Frame.CutROI(rect)
                stat = cutout.GetStats()
                mean_val = stat.Item1  # Mean value
                cutout.Release()
                
                # Store measurement for this aperture
                self.measurements[y_pos].append(mean_val)
            
            # Store timestamp - using SharpCap's frame timestamp (end of exposure)
            # Access FrameInfo via args.Frame.Info property
            net_timestamp = args.Frame.Info.EndTimeStamp
            
            # Convert .NET DateTime to Python datetime
            timestamp_end = datetime(
                net_timestamp.Year,
                net_timestamp.Month,
                net_timestamp.Day,
                net_timestamp.Hour,
                net_timestamp.Minute,
                net_timestamp.Second,
                net_timestamp.Millisecond * 1000  # Convert milliseconds to microseconds
            )
            
            # Convert end-frame timestamp to mid-frame to match ADV workflow and original light_curves.py
            # This ensures consistent behavior where calculate_delays_iron() expects mid-frame timestamps
            exposure_ms = getattr(self, 'exposure_ms', 50.0)  # Will be set before capture starts
            timestamp = timestamp_end - timedelta(milliseconds=exposure_ms / 2.0)
            self.timestamps.append(timestamp)
            
            # Print first timestamp for verification
            if self.frame_count == 1:
                print("  First frame timestamp (mid-frame): {0}".format(timestamp.strftime("%Y%m%d %H:%M:%S.%f")[:-3]))
            
            # Store frame number
            self.frame_numbers.append(len(self.frame_numbers))
            
            # Print progress every 20 frames
            if len(self.frame_numbers) % 20 == 0:
                print("Captured {0} frames...".format(len(self.frame_numbers)))
            
        except Exception as ex:
            # Log errors for debugging but don't disrupt capture
            print("Frame handler error: {0}".format(str(ex)))
            import traceback
            traceback.print_exc()
    
    def setup_apertures(self, frame_width, frame_height, aperture_size=10, spacing=100):
        """Setup multiple measurement apertures distributed across frame height
        
        Creates fixed-size square apertures at regular intervals from top to bottom of frame.
        Automatically accounts for ROI and binning via camera.Controls.Resolution.Value.
        
        Args:
            frame_width: Width of camera frame in pixels (from Controls.Resolution.Value, accounts for ROI/binning)
            frame_height: Height of camera frame in pixels (from Controls.Resolution.Value, accounts for ROI/binning)
            aperture_size: Size of square aperture in pixels (default 10x10)
            spacing: Vertical spacing between apertures in pixels (default 100)
        
        Sets:
            self.apertures: List of (y_center, Rectangle) tuples for all apertures
            self.measurements: Initialized dictionary for each aperture
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.apertures = []
        self.measurements = {}
        
        # Fixed aperture dimensions (square)
        aperture_width = aperture_size
        aperture_height = aperture_size
        
        # Center horizontal position
        x_center = int(frame_width * 0.5 - aperture_width * 0.5)
        
        # Create apertures from top to bottom at regular intervals
        # Ensure we always include top (Y=0) and bottom (Y=height-aperture_size) positions
        y_positions = []
        
        # Start at top
        y_positions.append(0)
        
        # Add middle positions at spacing intervals
        y = spacing
        while y < (frame_height - aperture_height - spacing // 2):
            y_positions.append(y)
            y += spacing
        
        # End at bottom
        y_bottom = frame_height - aperture_height
        if y_positions[-1] != y_bottom:
            y_positions.append(y_bottom)
        
        # Create Rectangle objects and initialize measurement storage
        for y_top in y_positions:
            rect = Rectangle(x_center, y_top, aperture_width, aperture_height)
            y_center = y_top + aperture_height // 2
            self.apertures.append((y_center, rect))
            self.measurements[y_center] = []
        
        print("Multiple apertures configured (ROI-aware):")
        print("  Frame: {0}x{1} pixels".format(frame_width, frame_height))
        print("  Aperture count: {0}".format(len(self.apertures)))
        print("  Aperture size: {0}x{1} pixels".format(aperture_width, aperture_height))
        print("  Y positions: {0}".format([y for y, _ in self.apertures]))
    
    def start_capture(self, camera):
        """Start capturing frames from the camera
        
        Args:
            camera: SharpCap camera object
        """
        self.capturing = True
        camera.FrameCaptured += self.framehandler
        print("Frame capture started - event handler attached")
    
    def stop_capture(self, camera):
        """Stop capturing frames from the camera
        
        Args:
            camera: SharpCap camera object
        """
        self.capturing = False
        camera.FrameCaptured -= self.framehandler
        print("Frame capture stopped - captured {0} frames".format(len(self.frame_numbers)))
    
    def reset(self):
        """Reset all captured data"""
        for y_pos in self.measurements.keys():
            self.measurements[y_pos] = []
        self.timestamps = []
        self.frame_numbers = []
        self.frame_count = 0
        print("Capture data reset")


# =============================================================================
# PHASE 2: DATA FORMAT CONVERSION
# =============================================================================

def create_tangra_object(measurements, timestamps, frame_numbers, y_position, 
                        aperture_name, exposure_ms):
    """Convert measurements to tangra_object format compatible with light_curves.py
    
    Creates a dictionary structure that matches the output of read_tangra_csv()
    so that existing GPS flash analysis functions can be used without modification.
    
    Args:
        measurements: List of mean intensity values
        timestamps: List of datetime objects for each frame
        frame_numbers: List of frame numbers
        y_position: Y coordinate of aperture center in frame
        aperture_name: Name of aperture ('top' or 'bottom')
        exposure_ms: Exposure time in milliseconds
        
    Returns:
        Dictionary matching tangra_object structure from read_tangra_csv()
    """
    light_curve = []
    
    for frame_no, timestamp, signal in zip(frame_numbers, timestamps, measurements):
        light_curve.append({
            'frameno': frame_no,
            'time_ut': timestamp,
            'signal_1': signal
        })
    
    tangra_obj = {
        'file_read_from': 'LED_Calibration_{0}'.format(aperture_name),
        'filename_from_tangra': 'LED_Calibration_{0}'.format(aperture_name),
        'light_curve': light_curve,
        'column_names': ['frameno', 'time_ut', 'signal_1'],
        'signal_1': measurements,  # Add direct access to signal data
        'timestamp': timestamps,   # Add direct access to timestamps
        'exposure_ms': exposure_ms,
        'acquisition_delay': None,
        'y_position': y_position,  # Store Y position for later use
        'aperture_name': aperture_name,
        'details': {},
        'apertures': []
    }
    
    print("Created tangra object for {0}: {1} frames, signal range {2:.1f}-{3:.1f}".format(
        aperture_name, len(light_curve), min(measurements), max(measurements)))
    return tangra_obj


def save_tangra_csv(top_measurements, bottom_measurements, timestamps, frame_numbers, 
                   top_y, bottom_y, exposure_ms, filename, camera_info):
    """Save aperture measurements in TANGRA CSV format
    
    Generates a CSV file compatible with TANGRA photometry software format.
    Top aperture is saved as Star 1, bottom aperture as Star 2.
    Background values are set to 0 (not used for GPS timing analysis).
    
    Args:
        top_measurements: List of mean intensity values from top aperture
        bottom_measurements: List of mean intensity values from bottom aperture
        timestamps: List of datetime objects for each frame
        frame_numbers: List of frame numbers
        top_y: Y coordinate of top aperture center
        bottom_y: Y coordinate of bottom aperture center
        exposure_ms: Exposure time in milliseconds
        filename: Output CSV filename (e.g., 'LED_Calibration_2024-01-15.csv')
        camera_info: Dictionary with camera info (name, resolution)
        
    Returns:
        Full path to saved CSV file
    """
    import os
    from datetime import datetime as dt
    
    # Build CSV content as list of lines
    csv_lines = []
    
    # Line 1: TANGRA header
    csv_lines.append("Tangra")
    
    # Line 2: Original filename (use camera name and timestamp)
    timestamp_str = dt.utcnow().strftime("%Y%m%d_%H%M%S")
    original_filename = "{0}_LED_Calibration_{1}.raw".format(camera_info.get('name', 'Camera'), timestamp_str)
    csv_lines.append(original_filename)
    
    # Lines 3-6: Empty
    csv_lines.append("")
    csv_lines.append("")
    csv_lines.append("")
    csv_lines.append("")
    
    # Line 7: Measurement parameters header
    csv_lines.append("Video File Format,Frame Rate,Frames in Video,Frame Width,Frame Height,Acquisition Delay (ms),Colour Channel,Binning,Tracked")
    
    # Line 8: Measurement parameters data
    resolution_str = camera_info.get('resolution', '640x480')
    width, height = resolution_str.split('x')
    params_line = "SharpCap Live,{0},{1},{2},{3},0.0,Green,1,False".format(
        round(1000.0 / exposure_ms, 2) if exposure_ms > 0 else 30.0,  # Frame rate
        len(frame_numbers),  # Total frames
        width,
        height
    )
    csv_lines.append(params_line)
    
    # Line 9: Aperture details header
    csv_lines.append("Object,Type,Aperture,StartingX,StartingY")
    
    # Line 10: Star 1 (top aperture)
    csv_lines.append("1,Fixed Aperture,Rectangle (10x10 fixed),5,{0}".format(int(top_y)))
    
    # Line 11: Star 2 (bottom aperture)
    csv_lines.append("2,Fixed Aperture,Rectangle (10x10 fixed),5,{0}".format(int(bottom_y)))
    
    # Lines 12-13: Blank
    csv_lines.append("")
    csv_lines.append("")
    
    # Line 14: Light curve header
    csv_lines.append("FrameNo,Time (UT),Signal 1,Background 1,Signal 2,Background 2")
    
    # Lines 15+: Light curve data
    for frame_no, timestamp, signal1, signal2 in zip(frame_numbers, timestamps, top_measurements, bottom_measurements):
        time_str = "[{0}]".format(timestamp.strftime("%H:%M:%S.%f"))
        data_line = "{0},{1},{2:.1f},0.0,{3:.1f},0.0".format(
            frame_no,
            time_str,
            signal1,
            signal2
        )
        csv_lines.append(data_line)
    
    # Write to file
    with open(filename, 'w') as f:
        for line in csv_lines:
            f.write(line + '\n')
    
    # Print to console
    print("\n" + "="*60)
    print("TANGRA CSV File Saved: {0}".format(filename))
    print("="*60)
    print("First 20 lines:")
    print("-"*60)
    for i, line in enumerate(csv_lines[:20]):
        print(line)
    print("-"*60)
    print("... ({0} data rows total)".format(len(frame_numbers)))
    print("="*60 + "\n")
    
    return os.path.abspath(filename)


# =============================================================================
# PHASE 3: GPS FLASH ANALYSIS FUNCTIONS
# =============================================================================
# These functions are adapted from gps-timing-analysis/python/light_curves.py
# Simplified to remove pandas/numpy dependencies for IronPython compatibility

def analyse_gps_flash_iron(tangra_object, col='signal_1', exposure_ms=50, 
                           flash_ms=100, background=None):
    """Analyze a light curve for GPS flashes and calculate time offsets
    
    This is an IronPython-compatible version of analyse_gps_flash() from light_curves.py.
    Processes the light curve to identify GPS flash peaks and prepare for delay calculation.
    
    Args:
        tangra_object: Tangra object with 'light_curve' list of dicts
        col: Name of column with signal data (default 'signal_1')
        exposure_ms: Exposure time in milliseconds
        flash_ms: GPS flash duration in milliseconds
        background: If specified, use as background level; otherwise calculated automatically
        
    Returns:
        List of dicts with GPS flash analysis results including peak_no for each frame
    """
    lcv = tangra_object['light_curve']
    
    # Safety check for empty light curve
    if not lcv or len(lcv) == 0:
        print("Error: Empty light curve provided")
        return []
    
    # Extract signal values
    signals = [row[col] for row in lcv]
    
    # Calculate background if not provided
    if background is None:
        # Use percentile based on exposure/flash ratio
        # Frames WITHOUT flashes should be most common
        sorted_signals = sorted(signals)
        percentile_index = int(len(sorted_signals) * (100.0 - (exposure_ms/flash_ms + 1.0)/(1000.0/flash_ms)*100.0) / 100.0)
        background = sorted_signals[min(percentile_index, len(sorted_signals)-1)]
    
    # Calculate average background from frames below threshold
    background_signals = [s for s in signals if s <= background]
    avg_background = sum(background_signals) / len(background_signals) if background_signals else background
    
    # Identify flash frames (signal above background)
    flash_frames = []
    for i, row in enumerate(lcv):
        signal = row[col]
        is_flash = signal > background
        signal_flash = (signal - avg_background) if is_flash else 0.0
        
        flash_frames.append({
            'frameno': row['frameno'],
            'time_ut': row['time_ut'],
            col: signal,
            'background_flag': 0.0 if is_flash else 1.0,
            'signal_flash': signal_flash,
            'avg_background': avg_background
        })
    
    # Label each GPS flash peak with a sequence number
    # A peak is a contiguous group of frames with signal above background
    peak_no = 0
    in_peak = False
    
    for row in flash_frames:
        if row['signal_flash'] > 0:
            if not in_peak:
                peak_no += 1
                in_peak = True
            row['peak_no'] = peak_no
        else:
            in_peak = False
            row['peak_no'] = 0
    
    print("Found {0} GPS flash peaks".format(peak_no))
    return flash_frames


def calculate_delays_iron(lcv, peak_no, exposure_ms, flash_ms, y, y_lines):
    """Calculate delay between timestamps and GPS PPS flash for a single peak
    
    This is an IronPython-compatible version of calculate_delays() from light_curves.py.
    Matches the original tested algorithm exactly.
    
    Args:
        lcv: Light curve list of dicts from analyse_gps_flash_iron()
        peak_no: Peak number to analyze (from peak_no field)
        exposure_ms: Exposure time in milliseconds
        flash_ms: GPS flash duration in milliseconds
        y: Y coordinate in frame (for rolling shutter calculations)
        y_lines: Total number of lines in frame
        
    Returns:
        Dictionary with time offset calculation results
    """
    # Get frames for this peak only
    peak_frames = [row for row in lcv if row['peak_no'] == peak_no]
    
    if not peak_frames:
        return None
    
    # Total flux during the signal (background already removed)
    total_flux = sum(row['signal_flash'] for row in peak_frames)
    
    if total_flux == 0:
        return None
    
    # Flux in the first frame of the signal
    flux1 = peak_frames[0]['signal_flash']
    
    # Fraction of total flux in first frame gives fraction of flash_ms time in first frame
    frac_flux_frame1 = flux1 / total_flux
    pps_ms_in_frame1 = frac_flux_frame1 * flash_ms
    
    # Get the frame timestamp - MID exposure time (matches original light_curves.py)
    # Both live capture and ADV now provide mid-frame timestamps
    frame1_mid = peak_frames[0]['time_ut']
    
    # Calculate the end time of the first frame
    # Original light_curves.py: "Just add half exposure to get end frame"
    rolling_shutter_y_offset = exposure_ms / 2.0
    frame1_end = frame1_mid + timedelta(milliseconds=rolling_shutter_y_offset)
    
    # The actual UT of the PPS flash (assumes timestamps accurate to <<1s)
    total_seconds = (frame1_end - datetime(1900, 1, 1)).total_seconds()
    pps_actual_seconds = round(total_seconds)
    pps_actual_time = datetime(1900, 1, 1) + timedelta(seconds=pps_actual_seconds)
    
    # The actual time of the end of the frame (pps_ms_in_frame1 after the PPS)
    frame1_end_actual = pps_actual_time + timedelta(milliseconds=pps_ms_in_frame1)
    
    # Time offset is the difference
    time_offset = (frame1_end - frame1_end_actual).total_seconds() * 1000.0
    
    result = {
        'peak_no': peak_no,
        'n_frames': len(peak_frames),
        'y': y,
        'y_lines': y_lines,
        'y_time_offset': rolling_shutter_y_offset,
        'total_flux': total_flux,
        'flux1': flux1,
        'frac_flux_frame1': frac_flux_frame1,
        'pps_ms_in_frame1': pps_ms_in_frame1,
        'frame1_mid': frame1_mid,
        'frame1_end': frame1_end,
        'pps_actual_time': pps_actual_time,
        'frame1_end_actual': frame1_end_actual,
        'time_offset': time_offset
    }
    
    return result


def analyze_aperture_delays(tangra_obj, exposure_ms, flash_ms=100):
    """Analyze GPS flashes in an aperture light curve and calculate all delays
    
    Args:
        tangra_obj: Tangra object with light curve data
        exposure_ms: Exposure time in milliseconds
        flash_ms: GPS flash duration in milliseconds (default 100ms)
        
    Returns:
        List of delay measurement dicts with y_position and time_offset
    """
    aperture_name = tangra_obj.get('aperture_name', 'unknown')
    print("\nAnalyzing aperture: {0}".format(aperture_name))
    
    # Process light curve to find GPS flashes
    lcv = analyse_gps_flash_iron(
        tangra_obj,
        col='signal_1',
        exposure_ms=exposure_ms,
        flash_ms=flash_ms
    )
    
    # Get unique peak numbers (each peak = one GPS PPS flash)
    peak_numbers = set(row['peak_no'] for row in lcv if row['peak_no'] > 0)
    
    if not peak_numbers:
        print("Warning: No GPS flashes detected in {0} aperture".format(tangra_obj['aperture_name']))
        return []
    
    # Calculate delays for each peak
    delays = []
    y_position = tangra_obj['y_position']
    y_lines = tangra_obj.get('frame_height', 1000)  # Default if not set
    
    print("  y_position={0}, frame_height={1}, binning={2}".format(
        y_position, y_lines, tangra_obj.get('binning', '?')))
    
    for peak_no in peak_numbers:
        delay_result = calculate_delays_iron(
            lcv,
            peak_no,
            exposure_ms=exposure_ms,
            flash_ms=flash_ms,
            y=y_position,
            y_lines=y_lines
        )
        
        if delay_result:
            delays.append({
                'peak_no': peak_no,
                'y': y_position,
                'time_offset': delay_result['time_offset'],
                'frac_flux_frame1': delay_result['frac_flux_frame1'],
                'total_flux': delay_result['total_flux'],
                'aperture': tangra_obj['aperture_name'],
                'n_frames': delay_result['n_frames']
            })
    
    print("Calculated {0} delays for {1} aperture".format(len(delays), tangra_obj['aperture_name']))
    return delays


def filter_flash_measurements(all_delays, min_frac_flux=0.1, max_frac_flux=0.9,
                              min_offset=-80, max_offset=80):
    """Filter out poor quality GPS flash measurements
    
    Removes transition frames where the flash is mostly in one frame (too dim or too bright),
    which can lead to inaccurate timing measurements. Based on analysis methods from
    Jupyter notebook examples.
    
    Args:
        all_delays: List of delay measurement dicts
        min_frac_flux: Minimum fraction of flux in first frame (default 0.1)
        max_frac_flux: Maximum fraction of flux in first frame (default 0.9)
        min_offset: Minimum acceptable time offset in ms (default -80)
        max_offset: Maximum acceptable time offset in ms (default 80)
        
    Returns:
        Filtered list of delay measurements and statistics dict
    """
    if not all_delays:
        return [], {'total': 0, 'filtered': 0, 'kept': 0}
    
    total_count = len(all_delays)
    
    # Apply filters
    filtered = []
    for d in all_delays:
        # Check fraction of flux in first frame
        frac = d.get('frac_flux_frame1', 0.5)
        if frac < min_frac_flux or frac > max_frac_flux:
            continue
        
        # Check time offset is reasonable
        offset = d.get('time_offset', 0)
        if offset < min_offset or offset > max_offset:
            continue
        
        filtered.append(d)
    
    kept_count = len(filtered)
    removed_count = total_count - kept_count
    
    stats = {
        'total': total_count,
        'filtered': removed_count,
        'kept': kept_count
    }
    
    print("Flash filtering: {0} total, {1} kept, {2} removed as outliers".format(
        total_count, kept_count, removed_count))
    
    if kept_count < 2:
        print("Warning: Only {0} measurements remain after filtering - need at least 2".format(kept_count))
    
    return filtered, stats


# =============================================================================
# PHASE 4: LINE DELAY REGRESSION
# =============================================================================

def fit_line_delays(all_delays):
    """Fit linear model to line delays: time_offset = slope * y + intercept
    
    Uses simple least-squares linear regression (IronPython compatible, no sklearn).
    
    Args:
        all_delays: List of dicts with 'y' (y position) and 'time_offset' (ms) keys
        
    Returns:
        Dictionary with:
            - slope: ms per line (should be positive for rolling shutter)
            - intercept: offset at y=0 in ms
            - r_squared: R-squared goodness of fit
            - n_measurements: number of data points
            - description: Human-readable result string
        Or None if insufficient data
    """
    if len(all_delays) < 2:
        print("Error: Need at least 2 measurements for linear fit")
        return None
    
    # Extract x (y positions) and y (time offsets)
    y_positions = [float(d['y']) for d in all_delays]
    time_offsets = [float(d['time_offset']) for d in all_delays]
    
    n = len(y_positions)
    
    # Calculate sums for linear regression
    sum_x = sum(y_positions)
    sum_y = sum(time_offsets)
    sum_xx = sum(x*x for x in y_positions)
    sum_xy = sum(x*y for x, y in zip(y_positions, time_offsets))
    
    # Calculate slope and intercept
    # slope = (n*sum_xy - sum_x*sum_y) / (n*sum_xx - sum_x*sum_x)
    # intercept = (sum_y - slope*sum_x) / n
    denominator = n * sum_xx - sum_x * sum_x
    
    if abs(denominator) < 1e-10:
        print("Error: Cannot fit line (singular matrix)")
        return None
    
    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    
    # Calculate R-squared
    mean_y = sum_y / n
    ss_tot = sum((y - mean_y)**2 for y in time_offsets)
    ss_res = sum((y - (slope * x + intercept))**2 
                 for x, y in zip(y_positions, time_offsets))
    r_squared = 1.0 - (ss_res / ss_tot) if abs(ss_tot) > 1e-10 else 0.0
    
    result = {
        'slope': slope,
        'intercept': intercept,
        'r_squared': r_squared,
        'n_measurements': n,
        'description': 'Line delay: {0:.6f} ms/line, Offset: {1:.3f} ms'.format(slope, intercept)
    }
    
    print(result['description'])
    print('R-squared: {0:.4f}'.format(r_squared))
    
    return result


# =============================================================================
# PHASE 5: VISUALIZATION
# =============================================================================

def create_line_delay_plot(all_delays, fit_result):
    """Create OxyPlot scatter plot with fitted line
    
    Args:
        all_delays: List of dicts with 'y' and 'time_offset' keys
        fit_result: Dictionary from fit_line_delays() with slope and intercept
        
    Returns:
        OxyPlot.PlotModel ready to display
    """
    # Create plot model
    plot_model = OxyPlot.PlotModel()
    plot_model.Title = 'GPS LED Line Delay Calibration'
    
    # Add subtitle with equation if fit_result available
    if fit_result:
        slope = fit_result['slope']
        intercept = fit_result['intercept']
        r_squared = fit_result['r_squared']
        # Format: "Line delay of intercept + slope x Y ms, R² = value" (3 sig figs)
        sign = '+' if slope >= 0 else '-'
        subtitle = 'Line delay of {0:.3g} {1} {2:.3g} x Y ms, R\u00b2 = {3:.3f}'.format(
            intercept, sign, abs(slope), r_squared)
        plot_model.Subtitle = subtitle
    
    # Create scatter series for measurements
    scatter_series = OxyPlot.Series.ScatterSeries()
    scatter_series.MarkerType = OxyPlot.MarkerType.Circle
    scatter_series.MarkerSize = 5
    scatter_series.MarkerFill = OxyPlot.OxyColors.Blue
    
    for d in all_delays:
        scatter_point = OxyPlot.Series.ScatterPoint(float(d['y']), float(d['time_offset']))
        scatter_series.Points.Add(scatter_point)
    
    # Create line series for fitted line
    if fit_result:
        line_series = OxyPlot.Series.LineSeries()
        line_series.LineStyle = OxyPlot.LineStyle.Solid
        line_series.Color = OxyPlot.OxyColors.Red
        line_series.StrokeThickness = 2
        
        # Get y range for line
        y_min = min(float(d['y']) for d in all_delays)
        y_max = max(float(d['y']) for d in all_delays)
        
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
    x_axis = OxyPlot.Axes.LinearAxis()
    x_axis.Position = OxyPlot.Axes.AxisPosition.Bottom
    x_axis.Title = 'Y Position (pixels)'
    plot_model.Axes.Add(x_axis)
    
    y_axis = OxyPlot.Axes.LinearAxis()
    y_axis.Position = OxyPlot.Axes.AxisPosition.Left
    y_axis.Title = 'Time Offset (ms)'
    plot_model.Axes.Add(y_axis)
    
    return plot_model


# =============================================================================
# PHASE 6 & 7: GUI INTERFACE AND MAIN CALIBRATION LOGIC
# =============================================================================

class LEDLineDelayCalibrationForm(Form):
    """Windows Forms GUI for LED line delay calibration"""
    
    def __init__(self):
        """Initialize the calibration form"""
        self.capture_handler = FrameCaptureHandler()
        self.InitializeComponent()
        # Force handle creation to avoid invoke errors from background threads
        handle = self.Handle
        
    def SafeInvoke(self, action):
        """Safely invoke action on UI thread, handling handle creation issues"""
        try:
            if self.IsHandleCreated:
                self.Invoke(action)
            else:
                # Force handle creation if needed
                handle = self.Handle
                self.Invoke(action)
        except Exception as ex:
            # Fallback: try direct execution if invoke fails
            try:
                action()
            except:
                print("Warning: Could not update UI: " + str(ex))
        
    def InitializeComponent(self):
        """Setup GUI components"""
        self.Text = "GPS LED Line Delay Calibration"
        self.ClientSize = Size(700, 550)
        self.TopMost = True
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        
        # Capture mode selection (moved to top)
        self.label_mode = Label()
        self.label_mode.Text = "Calibration Mode:"
        self.label_mode.Location = Point(20, 20)
        self.label_mode.AutoSize = True
        
        self.radio_live = RadioButton()
        self.radio_live.Text = "Live Capture"
        self.radio_live.Location = Point(140, 18)
        self.radio_live.AutoSize = True
        self.radio_live.Checked = True
        
        self.radio_adv = RadioButton()
        self.radio_adv.Text = "Use ADV File"
        self.radio_adv.Location = Point(260, 18)
        self.radio_adv.AutoSize = True
        self.radio_adv.Enabled = ADV_AVAILABLE
        if not ADV_AVAILABLE:
            self.radio_adv.Text = "Use ADV File (not available)"
        
        # Duration setting
        self.label_duration = Label()
        self.label_duration.Text = "Capture Duration (seconds):"
        self.label_duration.Location = Point(20, 50)
        self.label_duration.AutoSize = True
        
        self.textbox_duration = TextBox()
        self.textbox_duration.Text = "30"
        self.textbox_duration.Location = Point(210, 48)
        self.textbox_duration.Width = 60
        
        # Flash duration setting
        self.label_flash = Label()
        self.label_flash.Text = "GPS Flash Duration (ms):"
        self.label_flash.Location = Point(300, 50)
        self.label_flash.AutoSize = True
        
        self.textbox_flash = TextBox()
        self.textbox_flash.Text = "100"
        self.textbox_flash.Location = Point(480, 48)
        self.textbox_flash.Width = 60
        
        # Start button
        self.button_start = Button()
        self.button_start.Text = "Start Calibration"
        self.button_start.Location = Point(20, 80)
        self.button_start.Size = Size(120, 30)
        self.button_start.Click += self.start_calibration
        
        # Stop button
        self.button_stop = Button()
        self.button_stop.Text = "Stop"
        self.button_stop.Location = Point(160, 80)
        self.button_stop.Size = Size(80, 30)
        self.button_stop.Enabled = False
        self.button_stop.Click += self.stop_calibration
        
        # Status label
        self.label_status = Label()
        self.label_status.Text = "Ready"
        self.label_status.Location = Point(260, 88)
        self.label_status.AutoSize = True
        self.label_status.Font = Font(self.label_status.Font.FontFamily, 9, FontStyle.Bold)
        
        # Results text box
        self.label_results = Label()
        self.label_results.Text = "Results:"
        self.label_results.Location = Point(20, 120)
        self.label_results.AutoSize = True
        
        self.textbox_results = TextBox()
        self.textbox_results.Location = Point(20, 140)
        self.textbox_results.Size = Size(660, 100)
        self.textbox_results.Multiline = True
        self.textbox_results.ReadOnly = True
        self.textbox_results.ScrollBars = ScrollBars.Vertical
        
        # Plot view
        self.plot_view = OxyPlot.WindowsForms.PlotView()
        self.plot_view.Location = Point(20, 250)
        self.plot_view.Size = Size(660, 260)
        
        # Close button
        self.button_close = Button()
        self.button_close.Text = "Close"
        self.button_close.Location = Point(600, 520)
        self.button_close.Size = Size(80, 25)
        self.button_close.Click += self.close_form
        
        # Add controls
        self.Controls.Add(self.label_duration)
        self.Controls.Add(self.textbox_duration)
        self.Controls.Add(self.label_flash)
        self.Controls.Add(self.textbox_flash)
        self.Controls.Add(self.label_mode)
        self.Controls.Add(self.radio_live)
        self.Controls.Add(self.radio_adv)
        self.Controls.Add(self.button_start)
        self.Controls.Add(self.button_stop)
        self.Controls.Add(self.label_status)
        self.Controls.Add(self.label_results)
        self.Controls.Add(self.textbox_results)
        self.Controls.Add(self.plot_view)
        self.Controls.Add(self.button_close)
        
    def start_calibration(self, sender, event):
        """Start LED line delay calibration in separate thread"""
        # Check camera connection (only required for Live Capture mode)
        use_adv = self.radio_adv.Checked
        if not use_adv and SharpCap.SelectedCamera is None:
            MessageBox.Show(
                "No camera is connected.\n\nPlease connect a camera before running Live Capture calibration.",
                "Camera Connection Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            return
        
        # Disable start button, enable stop
        self.button_start.Enabled = False
        self.button_stop.Enabled = True
        self.label_status.Text = "Starting..."
        self.label_status.ForeColor = Color.Orange
        
        # Run calibration in separate thread to avoid blocking UI
        thread = Thread(ParameterizedThreadStart(self.run_calibration_thread))
        thread.SetApartmentState(ApartmentState.STA)
        thread.Start(self)
        
    def run_calibration_thread(self, form):
        """Main calibration workflow - runs in separate thread"""
        try:
            # Get parameters
            duration = float(form.textbox_duration.Text)
            flash_ms = float(form.textbox_flash.Text)
            use_adv = form.radio_adv.Checked
            
            # Branch based on capture mode
            if use_adv:
                # ADV file loading workflow (camera not required)
                form.run_adv_workflow(duration, flash_ms, None)
            else:
                # Live capture workflow (requires camera)
                camera = SharpCap.SelectedCamera
                form.run_live_workflow(duration, flash_ms, camera)
                
        except Exception as e:
            error_msg = "Calibration failed:\n" + str(e)
            print(error_msg)
            form.SafeInvoke(lambda: MessageBox.Show(error_msg, "Calibration Error", MessageBoxButtons.OK, MessageBoxIcon.Error))
        finally:
            # Re-enable start button
            form.SafeInvoke(lambda: setattr(form.button_start, 'Enabled', True))
            form.SafeInvoke(lambda: setattr(form.button_stop, 'Enabled', False))
            form.SafeInvoke(lambda: setattr(form.label_status, 'Text', 'Ready'))
            form.SafeInvoke(lambda: setattr(form.label_status, 'ForeColor', Color.Black))
    
    def run_live_workflow(self, duration, flash_ms, camera):
        """Run calibration using live frame capture (original method)"""
        try:
            # 1. Setup apertures
            self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Setting up apertures...'))
            
            # Get exposure and binning info
            exposure_ms = camera.Controls.Exposure.ExposureMs
            
            # Detect binning factor (for information/validation)
            binning = 1
            try:
                binning_control = camera.Controls.FindByName("Binning")
                if binning_control:
                    binning_value = binning_control.Value
                    # Parse binning value (could be "1x1", "2x2", etc.)
                    if "x" in str(binning_value):
                        binning = int(str(binning_value).split("x")[0])
                    else:
                        binning = int(binning_value)
                    print("Detected binning: {0}x{0}".format(binning))
            except:
                print("Could not detect binning, assuming 1x1")
            
            # Get actual frame dimensions from camera ROI (already in binned pixels)
            roi = camera.ROI
            estimated_width = roi.Width
            estimated_height = roi.Height
            
            print("Camera ROI dimensions: {0}x{1} pixels (binned)".format(estimated_width, estimated_height))
            print("Will verify with actual captured frame dimensions...")
            
            self.capture_handler.reset()
            # Setup apertures using estimated dimensions (will be validated below)
            self.capture_handler.setup_apertures(estimated_width, estimated_height)
            
            # Store frame dimensions in binned pixels (for rolling shutter delay calculations)
            self.capture_handler.frame_height = int(estimated_height)
            self.capture_handler.frame_width = int(estimated_width)
            self.capture_handler.binning = binning
            # Store exposure for timestamp conversion in frame handler
            self.capture_handler.exposure_ms = exposure_ms
            
            # 2. Start frame capture
            self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Capturing frames...'))
            self.capture_handler.start_capture(camera)
            
            # Give camera time to start delivering frames
            time.sleep(0.5)
            
            # Wait for first frame to verify capture is working
            max_wait = 30  # Max 30 iterations = ~3 seconds
            for i in range(max_wait):
                if self.capture_handler.frame_count > 0:
                    break
                time.sleep(0.1)
            
            if self.capture_handler.frame_count == 0:
                raise Exception("No frames captured - camera not delivering frame data")
            
            # Frame dimensions are already set correctly from camera.ROI
            # (which provides binned pixel dimensions directly)
            print("Frame capture confirmed - using ROI dimensions: {0}x{1} pixels".format(
                estimated_width, estimated_height))
            self.capture_handler.binning = binning
            
            # 3. Wait for capture duration
            self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 
                       'Capturing... ({0}s remaining)'.format(int(duration))))
            
            # Count down the duration
            for remaining in range(int(duration), 0, -1):
                if remaining % 5 == 0 or remaining <= 3:
                    self.SafeInvoke(lambda r=remaining: setattr(self.label_status, 'Text', 
                               'Capturing... ({0}s remaining)'.format(r)))
                time.sleep(1)
            
            # 4. Stop frame capture
            self.capture_handler.stop_capture(camera)
            
            # Check if we captured any frames
            n_frames = len(self.capture_handler.frame_numbers)
            print("Captured {0} frames total".format(n_frames))
            
            if n_frames == 0:
                error_msg = "No frames were captured.\n\n"
                error_msg += "Please ensure:\n"
                error_msg += "1. Camera is in Live mode (preview running)\n"
                error_msg += "2. Camera is delivering frames\n"
                error_msg += "3. Exposure time is not too long"
                raise Exception(error_msg)
            
            # 5. Create tangra objects for all apertures
            self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Processing data...'))
            
            tangra_objects = []
            aperture_y_positions = sorted(self.capture_handler.measurements.keys())
            
            for y_pos in aperture_y_positions:
                measurements = self.capture_handler.measurements[y_pos]
                aperture_name = 'aperture_y{0}'.format(y_pos)
                
                # For live capture: use actual captured frame pixel coordinates
                # y_pos and frame_height are in actual frame pixels (the pixel grid of captured frames)
                # Line delays are calculated per pixel in the frame coordinate system
                
                tangra_obj = create_tangra_object(
                    measurements,
                    self.capture_handler.timestamps,
                    self.capture_handler.frame_numbers,
                    y_pos,  # Y coordinate in frame pixels
                    aperture_name,
                    exposure_ms
                )
                # Store frame height in actual frame pixels for rolling shutter calculations
                tangra_obj['frame_height'] = self.capture_handler.frame_height
                tangra_obj['binned_y_pos'] = y_pos  # Keep position for reference
                tangra_obj['binning'] = self.capture_handler.binning  # For information only
                tangra_objects.append(tangra_obj)
            
            print("Created {0} tangra objects for {1} apertures".format(
                len(tangra_objects), len(aperture_y_positions)))
            print("  Live capture: frame_height={0} pixels, frame_width={1} pixels".format(
                self.capture_handler.frame_height, self.capture_handler.frame_width))
            print("  (Line delays calculated per pixel in actual frame coordinate system)")
            
            from datetime import datetime as dt
            import os
            
            # Use Documents folder as save location
            try:
                # Try to get Documents folder from environment
                documents_folder = os.path.expanduser("~\\Documents")
                if not os.path.exists(documents_folder):
                    # Fallback to user's home directory
                    documents_folder = os.path.expanduser("~")
            except:
                # Last resort: use temp directory
                import tempfile
                documents_folder = tempfile.gettempdir()
            
            timestamp_str = dt.utcnow().strftime("%Y%m%d_%H%M%S")
            csv_filename = os.path.join(documents_folder, "LED_Calibration_{0}.csv".format(timestamp_str))
            
            # Get camera info including ROI
            camera_info = {
                'name': camera.DeviceName if hasattr(camera, 'DeviceName') else 'Camera',
                'resolution': '{0}x{1}'.format(roi.Width, roi.Height),
                'roi_x': roi.X,
                'roi_y': roi.Y
            }
            
            # Save CSV with first and last aperture data
            csv_path = None
            try:
                first_y = aperture_y_positions[0]
                last_y = aperture_y_positions[-1]
                csv_path = save_tangra_csv(
                    self.capture_handler.measurements[first_y],
                    self.capture_handler.measurements[last_y],
                    self.capture_handler.timestamps,
                    self.capture_handler.frame_numbers,
                    first_y,
                    last_y,
                    exposure_ms,
                    csv_filename,
                    camera_info
                )
                print("TANGRA CSV saved to: {0}".format(csv_path))
            except Exception as csv_ex:
                print("Warning: Could not save TANGRA CSV file: {0}".format(str(csv_ex)))
                print("Continuing with analysis...")
            
            # 6. Analyze GPS flashes in all apertures
            self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Analyzing GPS flashes...'))
            
            all_delays = []
            aperture_flash_counts = {}
            
            for tangra_obj in tangra_objects:
                aperture_delays = analyze_aperture_delays(tangra_obj, exposure_ms, flash_ms)
                all_delays.extend(aperture_delays)
                aperture_flash_counts[tangra_obj['y_position']] = len(aperture_delays)
            
            print("Total GPS flash measurements across all apertures: {0}".format(len(all_delays)))
            for y_pos, count in sorted(aperture_flash_counts.items()):
                print("  Y={0}: {1} flashes".format(y_pos, count))
            
            # 7. Filter and fit
            self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Filtering and fitting...'))
            
            if len(all_delays) < 2:
                raise Exception(
                    "Not enough GPS flashes detected. Need at least 2.\n\n" +
                    "Total measurements: {0}\n\n".format(len(all_delays)) +
                    "Make sure GPS LED is flashing and visible in frame."
                )
            
            # Filter out poor quality measurements (transition frames)
            all_delays_filtered, filter_stats = filter_flash_measurements(all_delays)
            
            if len(all_delays_filtered) < 2:
                raise Exception(
                    "Not enough quality measurements after filtering.\\n\\n" +
                    "Total measurements: {0}\\n".format(filter_stats['total']) +
                    "Kept: {0}, Filtered out: {1}\\n\\n".format(
                        filter_stats['kept'], filter_stats['filtered']) +
                    "Try capturing for longer or check GPS LED visibility."
                )
            
            # Fit linear model
            self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Calculating line delays...'))
            fit_result = fit_line_delays(all_delays_filtered)
            
            if not fit_result:
                raise Exception("Linear fit failed. Please check data and try again.")
            
            # 8. Display results
            self.SafeInvoke(lambda: self.display_results(
                all_delays_filtered, fit_result, tangra_objects, 
                aperture_y_positions, self.capture_handler.frame_height, 
                self.capture_handler.binning, filter_stats, csv_path
            ))
            
            # 9. Success
            self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Calibration complete'))
            self.SafeInvoke(lambda: setattr(self.label_status, 'ForeColor', Color.Green))
        
        except Exception as ex:
            # Handle errors
            error_msg = "Error occurred:\n" + str(ex)
            self.SafeInvoke(lambda: setattr(self.textbox_results, 'Text', error_msg))
            self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Error'))
            self.SafeInvoke(lambda: setattr(self.label_status, 'ForeColor', Color.Red))
            print("Calibration error: " + str(ex))
        
        finally:
            # Re-enable buttons
            self.SafeInvoke(lambda: setattr(self.button_start, 'Enabled', True))
            self.SafeInvoke(lambda: setattr(self.button_stop, 'Enabled', False))
    
    def run_adv_workflow(self, duration, flash_ms, camera):
        """Run calibration using ADV file loading and replay"""
        import adv_helper
        
        # Prompt user to load ADV file
        self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Waiting to load ADV file...'))
        
        msg = "Load an ADV recording for calibration.\n\n"
        msg += "Manually record now using SharpCap to ADV or use an existing file.\n\n"
        msg += "Press OK when ready to load the file from disk."
        
        result = MessageBox.Show(msg, "Load ADV File", 
                                MessageBoxButtons.OKCancel, 
                                MessageBoxIcon.Information)
        
        if result != DialogResult.OK:
            raise Exception("ADV file loading cancelled by user")
        
        # Prompt for ADV file location
        self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Locating ADV file...'))
        
        # Prompt user to browse for ADV file
        dialog = OpenFileDialog()
        dialog.Title = "Select ADV file for calibration"
        dialog.Filter = "ADV files (*.adv)|*.adv|All files (*.*)|*.*"
        
        # Try common SharpCap capture locations as initial directory
        default_paths = [
            os.path.join(os.path.expanduser('~'), 'Documents', 'SharpCap Captures'),
            os.path.join(os.path.expanduser('~'), 'Videos', 'SharpCap'),
            os.path.join(os.path.expanduser('~'), 'Documents')
        ]
        
        for base_path in default_paths:
            if os.path.exists(base_path):
                dialog.InitialDirectory = base_path
                break
        
        adv_file_path = None
        adv_file_name = None
        
        if dialog.ShowDialog() == DialogResult.OK:
            adv_file_path = os.path.dirname(dialog.FileName)
            adv_file_name = os.path.basename(dialog.FileName)
            print("User selected: " + dialog.FileName)
        else:
            raise Exception("ADV file not selected")
        
        # Process ADV file
        self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Processing ADV file...'))
        
        try:
            adv_file = adv_helper.open_adv(adv_file_path, adv_file_name, verbose=True)
        except Exception as e:
            raise Exception("Failed to open ADV file: " + str(e))
        
        try:
            # Get file information
            frame_count = adv_file.MainSteamInfo.FrameCount
            frame_width = adv_file.Width
            frame_height = adv_file.Height
            
            print("ADV file: {0} frames, {1}x{2}".format(frame_count, frame_width, frame_height))
            print("Using ADV frame dimensions directly (no scaling applied)")
            print("ADV timestamps will be used as mid-frame (matching original light_curves.py behavior)")
            
            # Get exposure from ADV file
            exposure_ms = adv_helper.get_frame_exposure_ms(adv_file, 0)
            if exposure_ms is None:
                print("WARNING: Could not read exposure from ADV file")
                # Use a default value if exposure not available
                exposure_ms = 40.0
                print("Using default exposure: {0} ms".format(exposure_ms))
            else:
                print("ADV file exposure: {0:.2f} ms (from file metadata)".format(exposure_ms))
            
            # Setup apertures using actual ADV frame dimensions
            self.capture_handler.reset()
            self.capture_handler.setup_apertures(frame_width, frame_height)
            self.capture_handler.frame_width = frame_width
            self.capture_handler.frame_height = frame_height
            # Binning not relevant for ADV playback - dimensions are already actual frame size
            self.capture_handler.binning = 1
            
            # Process frames from ADV file
            self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 
                       'Reading {0} frames from ADV...'.format(frame_count)))
            
            for frame_no in range(frame_count):
                if frame_no % 100 == 0:
                    self.SafeInvoke(lambda fn=frame_no: setattr(self.label_status, 'Text', 
                               'Processing frame {0}/{1}...'.format(fn, frame_count)))
                
                # Read frame and get timestamp from frame info
                # This matches the original light_curves.py behavior:
                # It reads StartOfExposure timestamp and adds Shutter/2 for mid-frame
                pixels, frame_info = adv_helper.read_adv_frame(adv_file, frame_no)
                if pixels is None:
                    continue
                
                # Get timestamp from frame info (already read with pixels)
                # Use the cached frame_info to avoid reading the frame twice
                timestamp = adv_helper.get_frame_info_timestamp(adv_file, frame_no)
                
                # Measure each aperture
                for y_pos, aperture_rect in self.capture_handler.apertures:
                    mean_value = adv_helper.get_aperture_mean(pixels, frame_width, frame_height, aperture_rect)
                    self.capture_handler.measurements[y_pos].append(mean_value)
                
                # Store timestamps and frame numbers
                self.capture_handler.timestamps.append(timestamp)
                self.capture_handler.frame_numbers.append(frame_no)
            
            print("Processed {0} frames from ADV file".format(frame_count))
            
            # Verify timestamp intervals
            if len(self.capture_handler.timestamps) >= 2:
                deltas = []
                for i in range(min(10, len(self.capture_handler.timestamps) - 1)):
                    delta = (self.capture_handler.timestamps[i+1] - self.capture_handler.timestamps[i]).total_seconds() * 1000.0
                    deltas.append(delta)
                print("  Frame intervals (first 10, ms): {0}".format(["{0:.1f}".format(d) for d in deltas]))
                print("  Average frame interval: {0:.2f} ms (expected ~{1:.2f} ms)".format(
                    sum(deltas) / len(deltas), exposure_ms))
            
            if self.capture_handler.apertures:
                print("  Apertures: {0}".format(len(self.capture_handler.apertures)))
                y_pos, _ = self.capture_handler.apertures[0]
                measurements = self.capture_handler.measurements[y_pos]
                print("  Aperture Y={0} measurements:".format(y_pos))
                print("    Count: {0}".format(len(measurements)))
                if len(measurements) >= 10:
                    print("    First 10: {0}".format(["{0:.1f}".format(m) for m in measurements[:10]]))
                    print("    Min: {0:.1f}, Max: {1:.1f}, Mean: {2:.1f}".format(
                        min(measurements), max(measurements), sum(measurements) / len(measurements)))
            print("")
            
        finally:
            adv_file.Close()
        
        # Continue with analysis (same as live capture from step 5 onwards)
        self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Creating TANGRA objects...'))
        
        # Create TANGRA objects and analyze
        tangra_objects = []
        aperture_y_positions = sorted(self.capture_handler.measurements.keys())
        
        for y_pos in aperture_y_positions:
            measurements = self.capture_handler.measurements[y_pos]
            aperture_name = 'aperture_y{0}'.format(y_pos)
            
            # For ADV files: use actual frame pixel coordinates directly
            # y_pos and frame_height are in actual frame pixels (the pixel grid of the recorded frames)
            # Line delays are calculated per pixel in the frame coordinate system
            
            tangra_obj = create_tangra_object(
                measurements,
                self.capture_handler.timestamps,
                self.capture_handler.frame_numbers,
                y_pos,  # Y coordinate in frame pixels
                aperture_name,
                exposure_ms
            )
            # Store frame height in actual frame pixels for rolling shutter calculations
            tangra_obj['frame_height'] = self.capture_handler.frame_height
            tangra_obj['binned_y_pos'] = y_pos  # Keep position for reference
            tangra_obj['binning'] = self.capture_handler.binning  # For information only
            tangra_objects.append(tangra_obj)
        
        print("Created {0} tangra objects for {1} apertures".format(
            len(tangra_objects), len(aperture_y_positions)))
        print("  ADV file: frame_height={0} pixels, frame_width={1} pixels".format(
            self.capture_handler.frame_height, self.capture_handler.frame_width))
        print("  (Line delays calculated per pixel in actual frame coordinate system)")
        
        # Generate CSV filename based on ADV filename
        # Save in same directory as ADV file, or fallback to Documents
        csv_basename = adv_file_name.replace('.adv', '_line_delay.csv')
        
        # Try to save in ADV file directory first (best - keeps files together)
        csv_filename = os.path.join(adv_file_path, csv_basename)
        
        # Check if ADV directory is writable, otherwise use fallback
        try:
            # Test if directory is writable
            test_file = os.path.join(adv_file_path, '.write_test')
            with open(test_file, 'w') as f:
                f.write('test')
            os.remove(test_file)
        except:
            # ADV directory not writable, use fallback
            print("ADV directory not writable, using Documents folder for CSV")
            try:
                documents_folder = os.path.expanduser("~\\Documents")
                if not os.path.exists(documents_folder):
                    documents_folder = os.path.expanduser("~")
            except:
                import tempfile
                documents_folder = tempfile.gettempdir()
            csv_filename = os.path.join(documents_folder, csv_basename)
        
        # Camera info for CSV - extract from ADV filename if possible
        camera_info = {
            'name': adv_file_name.split('_')[0] if '_' in adv_file_name else 'Camera',
            'resolution': '{0}x{1}'.format(frame_width, frame_height)
        }
        
        # Save CSV
        csv_path = None
        try:
            first_y = aperture_y_positions[0]
            last_y = aperture_y_positions[-1]
            csv_path = save_tangra_csv(
                self.capture_handler.measurements[first_y],
                self.capture_handler.measurements[last_y],
                self.capture_handler.timestamps,
                self.capture_handler.frame_numbers,
                first_y,
                last_y,
                exposure_ms,
                csv_filename,
                camera_info
            )
            print("TANGRA CSV saved to: {0}".format(csv_path))
        except Exception as csv_ex:
            print("Warning: Could not save TANGRA CSV file: {0}".format(str(csv_ex)))
        
        # Analyze GPS flashes
        self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Analyzing GPS flashes...'))
        
        all_delays = []
        aperture_flash_counts = {}
        
        for tangra_obj in tangra_objects:
            aperture_delays = analyze_aperture_delays(tangra_obj, exposure_ms, flash_ms)
            all_delays.extend(aperture_delays)
            aperture_flash_counts[tangra_obj['y_position']] = len(aperture_delays)
        
        print("Total GPS flash measurements: {0}".format(len(all_delays)))
        for y_pos, count in sorted(aperture_flash_counts.items()):
            print("  Y={0}: {1} flashes detected".format(y_pos, count))
        
        if len(all_delays) == 0:
            error_msg = "No GPS flashes detected in any aperture.\n\n"
            error_msg += "Possible causes:\n"
            error_msg += "1. GPS LED was not enabled during recording\n"
            error_msg += "2. Flash duration setting is incorrect\n"
            error_msg += "3. Insufficient exposure time to detect flashes\n\n"
            error_msg += "Please ensure GPS LED is enabled and flashing before recording."
            raise Exception(error_msg)
        
        # Filter and fit
        self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Fitting line delay model...'))
        
        all_delays_filtered, filter_stats = filter_flash_measurements(all_delays)
        
        if len(all_delays_filtered) < 5:
            raise Exception("Insufficient measurements after filtering ({0} remaining)".format(len(all_delays_filtered)))
        
        fit_result = fit_line_delays(all_delays_filtered)
        
        # Display results
        self.SafeInvoke(lambda: self.display_results(
            all_delays_filtered, fit_result, tangra_objects, 
            aperture_y_positions, self.capture_handler.frame_height, 
            self.capture_handler.binning, filter_stats, csv_path
        ))
        
        # Success
        self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Calibration complete'))
        self.SafeInvoke(lambda: setattr(self.label_status, 'ForeColor', Color.Green))
    
    def display_results(self, all_delays, fit_result, tangra_objects,
                       aperture_y_positions, frame_height, binning, 
                       filter_stats=None, csv_path=None):
        """Display calibration results in GUI"""
        import os
        
        # Build results text (use \r\n for Windows TextBox control)
        results_text = "LED Line Delay Calibration Results\r\n"
        results_text += "=" * 50 + "\r\n\r\n"
        
        # Show line delay equation prominently at top (3 sig figs)
        slope = fit_result['slope']
        intercept = fit_result['intercept']
        r_squared = fit_result['r_squared']
        sign = '+' if slope >= 0 else '-'
        results_text += "Line delay of {0:.3g} {1} {2:.3g} x Y ms, R\u00b2 = {3:.3f}\r\n\r\n".format(
            intercept, sign, abs(slope), r_squared)
        
        # Show CSV file path if available
        if csv_path:
            results_text += "TANGRA CSV saved: {0}\r\n".format(os.path.basename(csv_path))
            results_text += "Full path: {0}\r\n\r\n".format(csv_path)
        
        results_text += "Binning: {0}x{0}\r\n".format(binning)
        results_text += "Apertures measured: {0}\r\n".format(len(aperture_y_positions))
        results_text += "  Y positions (binned): {0}\r\n".format(aperture_y_positions)
        results_text += "Measurements captured: {0}\r\n".format(
            filter_stats['total'] if filter_stats else len(all_delays))
        
        # Show filtering results if available
        if filter_stats:
            results_text += "\r\nQuality filtering:\r\n"
            results_text += "  Kept: {0} good measurements\r\n".format(filter_stats['kept'])
            results_text += "  Filtered out: {0} outliers/transition frames\r\n".format(
                filter_stats['filtered'])
        
        # Calculate rolling shutter time (time for full frame)
        # Slope is in ms per binned pixel (frame coordinates)
        rolling_shutter_time = fit_result['slope'] * frame_height
        results_text += "\r\nRolling shutter time (full frame): {0:.3g} ms\r\n".format(rolling_shutter_time)
        results_text += "  (Based on {0} frame lines at {1}x{1} binning)\r\n".format(frame_height, binning)
        
        # Calculate line rate
        if abs(fit_result['slope']) > 1e-10:
            line_rate = 1.0 / fit_result['slope']  # lines per ms
            results_text += "Line readout rate: {0:.3g} lines/ms\r\n".format(line_rate)
        
        self.textbox_results.Text = results_text
        
        # Create and display plot
        plot_model = create_line_delay_plot(all_delays, fit_result)
        self.plot_view.Model = plot_model
    
    def stop_calibration(self, sender, event):
        """Stop ongoing calibration"""
        try:
            if self.capture_handler.capturing:
                camera = SharpCap.SelectedCamera
                if camera:
                    self.capture_handler.stop_capture(camera)
            
            self.label_status.Text = "Stopped by user"
            self.label_status.ForeColor = Color.Orange
            self.button_start.Enabled = True
            self.button_stop.Enabled = False
        except Exception as ex:
            print("Error in stop_calibration: " + str(ex))
    
    def close_form(self, sender, event):
        """Close the form"""
        try:
            # Make sure capture is stopped
            if self.capture_handler.capturing:
                camera = SharpCap.SelectedCamera
                if camera:
                    self.capture_handler.stop_capture(camera)
            
            self.Close()
        except Exception as ex:
            print("Error in close_form: " + str(ex))
            self.Close()  # Close anyway


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

# Create and show the form when script is run
if __name__ == '__main__' or True:  # True ensures it runs when execfile'd
    print("")
    print("=" * 60)
    print("GPS LED Line Delay Calibration")
    print("Version 3.0.0")
    print("=" * 60)
    print("")
    
    # Check if SharpCap is available
    try:
        if SharpCap is None:
            print("ERROR: SharpCap not available.")
            print("This script must be run from SharpCap IronPython Console.")
        else:
            print("SharpCap detected: " + SharpCap.AppName)
            print("Creating calibration form...")
            
            # Create and show the form
            form = LEDLineDelayCalibrationForm()
            form.StartPosition = FormStartPosition.CenterScreen
            form.Show()
            
            print("Calibration form displayed.")
            print("Click 'Start Calibration' to begin.")
            print("")
    except:
        print("ERROR: Could not access SharpCap.")
        print("Make sure you are running this from SharpCap IronPython Console.")
