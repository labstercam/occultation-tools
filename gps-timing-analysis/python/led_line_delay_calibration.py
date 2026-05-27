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
import sys
from datetime import datetime, timedelta

# Add script directory to sys.path for imports (needed when using execfile())
# This allows importing adv_helper.py from the same directory
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # __file__ not defined (happens with execfile() in IronPython)
    # Use current working directory as fallback
    script_dir = os.path.abspath(os.getcwd())

if script_dir not in sys.path:
    sys.path.insert(0, script_dir)
    print("Added to Python path: " + script_dir)

# .NET/CLR imports for SharpCap
import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("System.IO.Compression")
clr.AddReference("OxyPlot")
clr.AddReference("OxyPlot.WindowsForms")

from System.Windows.Forms import *
from System.Drawing import *
from System.Threading import Thread, ApartmentState, ParameterizedThreadStart
import System.Drawing.Imaging
import System.IO
import System.IO.Compression
import System.Text
import OxyPlot
import OxyPlot.WindowsForms
import OxyPlot.Series
import OxyPlot.Axes

# ADV file support (optional)
try:
    import adv_helper
    ADV_AVAILABLE = adv_helper.is_advlib_available()
    if ADV_AVAILABLE:
        print("ADV support is AVAILABLE - ADV file replay mode enabled")
    else:
        print("ADV support not available - AdvLib DLLs could not be loaded")
        print("  Check SharpCap log for AdvLib loading errors from adv_helper.py")
except Exception as e:
    ADV_AVAILABLE = False
    print("ADV support not available - could not import adv_helper.py")
    print("  Error: " + str(e))
    print("  Script directory: " + script_dir)
    import traceback
    traceback.print_exc()

# Config import for Occultation Manager integration (graceful fallback when not available)
try:
    import config as _om_config
    _OM_CONFIG_AVAILABLE = True
    print("Occultation Manager config available - Save to Camera feature enabled")
except Exception:
    _om_config = None
    _OM_CONFIG_AVAILABLE = False

# SharpCap global — provided by SharpCap's IronPython console; None when run standalone
try:
    _ = SharpCap
except NameError:
    SharpCap = None



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
        # Validate frame dimensions
        if frame_width < aperture_size or frame_height < aperture_size:
            raise Exception(
                "Frame too small for aperture.\n" +
                "Frame: {0}x{1}, Aperture: {2}x{2}".format(
                    frame_width, frame_height, aperture_size))
        
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
    
    def setup_single_aperture(self, frame_width, frame_height, y_center, aperture_size=10):
        """Setup a single measurement aperture at specified Y position
        
        Used for long-term stability testing with single aperture.
        
        Args:
            frame_width: Width of camera frame in pixels
            frame_height: Height of camera frame in pixels
            y_center: Y center position for aperture
            aperture_size: Size of square aperture in pixels (default 10x10)
        
        Sets:
            self.apertures: List with single (y_center, Rectangle) tuple
            self.measurements: Initialized dictionary for the aperture
        """
        self.frame_width = frame_width
        self.frame_height = frame_height
        self.apertures = []
        self.measurements = {}
        
        # Center horizontal position
        x_center = int(frame_width * 0.5 - aperture_size * 0.5)
        y_top = int(y_center - aperture_size * 0.5)
        
        # Create single aperture
        rect = Rectangle(x_center, y_top, aperture_size, aperture_size)
        self.apertures.append((y_center, rect))
        self.measurements[y_center] = []
        
        print("Single aperture configured:")
        print("  Frame: {0}x{1} pixels".format(frame_width, frame_height))
        print("  Aperture: {0}x{1} at ({2}, {3})".format(
            aperture_size, aperture_size, x_center, y_center))
    
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


def save_tangra_csv(aperture_measurements, timestamps, frame_numbers, 
                   aperture_y_positions, exposure_ms, filename, camera_info):
    """Save aperture measurements in TANGRA CSV format
    
    Generates a CSV file compatible with TANGRA photometry software format.
    Exports 4 apertures: top 2 and bottom 2 from the aperture list.
    Background values are set to 0 (not used for GPS timing analysis).
    
    Args:
        aperture_measurements: Dictionary {y_position: [measurements]} for all apertures
        timestamps: List of datetime objects for each frame
        frame_numbers: List of frame numbers
        aperture_y_positions: List of Y positions for all apertures (sorted top to bottom)
        exposure_ms: Exposure time in milliseconds
        filename: Output CSV filename (e.g., 'LED_Calibration_2024-01-15.csv')
        camera_info: Dictionary with camera info (name, resolution, adv_filename (optional))
        
    Returns:
        Full path to saved CSV file
    """
    import os
    from datetime import datetime as dt
    
    # Get measurements for top 2 and bottom 2 apertures
    top1_y = aperture_y_positions[0]
    top2_y = aperture_y_positions[1] if len(aperture_y_positions) > 1 else aperture_y_positions[0]
    bottom2_y = aperture_y_positions[-2] if len(aperture_y_positions) > 1 else aperture_y_positions[-1]
    bottom1_y = aperture_y_positions[-1]
    
    top1_measurements = aperture_measurements[top1_y]
    top2_measurements = aperture_measurements[top2_y]
    bottom2_measurements = aperture_measurements[bottom2_y]
    bottom1_measurements = aperture_measurements[bottom1_y]
    
    # Parse camera info
    resolution_str = camera_info.get('resolution', '640x480')
    width, height = resolution_str.split('x')
    frame_width = camera_info.get('width', int(width))
    frame_height = int(height)
    camera_name = camera_info.get('name', 'Camera')
    
    # Measurement aperture size (10x10 rectangle)
    aperture_size = 10
    aperture_half = aperture_size / 2.0
    
    # Calculate centered X coordinate
    x_center = frame_width * 0.5
    
    # Build CSV content as list of lines (comma-separated for TANGRA format)
    csv_lines = []
    
    # ===== TOP FILE HEADER (Lines 1-4) =====
    # Line 1: Tangra version
    csv_lines.append("Tangra v3.7.0.5")
    
    # Line 2: Measurement count
    csv_lines.append("Measurments of 4 objects")
    
    # Line 3: Original filename
    if camera_info.get('adv_filename'):
        # Use actual ADV filename if available
        original_filename = camera_info.get('adv_filename')
    else:
        # Generate filename for live capture
        timestamp_str = dt.utcnow().strftime("%Y-%m-%d")
        time_str = dt.utcnow().strftime("%H_%M_%SZ")
        original_filename = "D:\\SharpCap Captures\\LED_Calibration\\{0}\\Light\\{1}_.adv".format(timestamp_str, time_str)
    csv_lines.append(original_filename)
    
    # Line 4: Video format info
    csv_lines.append("Asteroidal Video (ADV2.16), Time: Timestamp Saving During Recording")
    
    # Lines 5-6: Empty
    csv_lines.append("")
    csv_lines.append("")
    
    # ===== CAMERA/RECORDING BLOCK (Lines 7-8) =====
    # Line 7: Camera/recording parameters header (comma + space separator)
    camera_header = "Reversed Gamma, Colour, Measured Band, Integration, Digital Filter, Signal Method, Background Method, Instrumental Delay Corrections, Camera, AAV Integration, First Frame, Last Frame, Reversed Camera Response, Video File Format, Acquisition Delay (ms)"
    csv_lines.append(camera_header)
    
    # Line 8: Camera/recording parameters data (comma separator, no spaces)
    first_frame = frame_numbers[0] if frame_numbers else 1
    last_frame = frame_numbers[-1] if frame_numbers else len(frame_numbers)
    camera_data = "1.00,no,Red,no,NoFilter,AperturePhotometry,AverageBackground,Not Required,{0},,{1},{2},,ADV,0.0".format(
        camera_name, first_frame, last_frame)
    csv_lines.append(camera_data)
    csv_lines.append("")  # Line 9: Empty
    
    # ===== OBJECT/APERTURES BLOCK (Lines 10-14) =====
    # Line 10: Aperture details header (comma + space separator)
    aperture_header = "Object, Type, Aperture, Tolerance, FWHM, Measured, StartingX, StartingY, Fixed"
    csv_lines.append(aperture_header)
    
    # Lines 11-14: 4 apertures (comma separator, no spaces)
    # For GPS flash, use the center of the measurement rectangle as the aperture position
    # Aperture value is half the measurement rectangle size (5.0 for 10x10 rectangle)
    # FWHM is also half the measurement rectangle size
    # Starting X/Y is the center of the rectangle
    # All apertures are along the vertical center line
    
    # Aperture 1: Top aperture (first)
    csv_lines.append("1,GPSFlash,{0:.2f},,{1:.2f},yes,{2:.1f},{3:.1f},yes".format(
        aperture_half, aperture_half, x_center, float(top1_y)))
    
    # Aperture 2: Second from top
    csv_lines.append("2,GPSFlash,{0:.2f},,{1:.2f},yes,{2:.1f},{3:.1f},yes".format(
        aperture_half, aperture_half, x_center, float(top2_y)))
    
    # Aperture 3: Second from bottom
    csv_lines.append("3,GPSFlash,{0:.2f},,{1:.2f},yes,{2:.1f},{3:.1f},yes".format(
        aperture_half, aperture_half, x_center, float(bottom2_y)))
    
    # Aperture 4: Bottom aperture (last)
    csv_lines.append("4,GPSFlash,{0:.2f},,{1:.2f},yes,{2:.1f},{3:.1f},yes".format(
        aperture_half, aperture_half, x_center, float(bottom1_y)))
    
    # Lines 15-16: Blank
    csv_lines.append("")
    csv_lines.append("")
    
    # ===== DATA BLOCK (Lines 17+) =====
    # Line 17: Data header (comma separator, space before " Background")
    data_header = "FrameNo,Time (UT),Signal (1), Background (1),Signal (2), Background (2),Signal (3), Background (3),Signal (4), Background (4)"
    csv_lines.append(data_header)
    
    # Lines 18+: Light curve data (comma separator, no spaces)
    for i, (frame_no, timestamp) in enumerate(zip(frame_numbers, timestamps)):
        time_str = "[{0}]".format(timestamp.strftime("%H:%M:%S.%f")[:-3])  # Truncate to 3 decimal places
        
        # Get signals for all 4 apertures (integers, 0 dp)
        signal1 = int(round(top1_measurements[i]))
        signal2 = int(round(top2_measurements[i]))
        signal3 = int(round(bottom2_measurements[i]))
        signal4 = int(round(bottom1_measurements[i]))
        
        # Background set to 0 (not used for GPS timing analysis)
        bg1 = 0
        bg2 = 0
        bg3 = 0
        bg4 = 0
        
        # Format data line (comma-separated)
        data_line = "{0},{1},{2},{3},{4},{5},{6},{7},{8},{9}".format(
            frame_no, time_str,
            signal1, bg1, signal2, bg2, signal3, bg3, signal4, bg4
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

def invert_measurements(measurements, auto_detect_max=True, max_value=None):
    """Invert signal measurements for inverted GPS PPS patterns
    
    Converts 100ms OFF, 900ms ON pattern to 100ms ON, 900ms OFF pattern
    by subtracting all values from the maximum.
    
    Args:
        measurements: Dictionary {y_position: [measurement_list]}
        auto_detect_max: If True, find max from data; if False, use max_value
        max_value: Explicit max value to use for inversion
        
    Returns:
        Dictionary with inverted measurements (same structure)
    """
    inverted = {}
    
    # Determine max value for inversion
    if auto_detect_max or max_value is None:
        # Find maximum across all apertures
        all_values = []
        for y_pos in measurements:
            all_values.extend(measurements[y_pos])
        max_val = max(all_values)
    else:
        max_val = max_value
    
    print("Inverting signals using max value: {0:.1f}".format(max_val))
    
    # Invert each aperture's measurements
    for y_pos in measurements:
        inverted[y_pos] = [max_val - val for val in measurements[y_pos]]
    
    return inverted


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
                              min_offset=-500, max_offset=500):
    """Filter out poor quality GPS flash measurements
    
    Removes transition frames where the flash is mostly in one frame (too dim or too bright),
    which can lead to inaccurate timing measurements. Based on analysis methods from
    Jupyter notebook examples.
    
    Args:
        all_delays: List of delay measurement dicts
        min_frac_flux: Minimum fraction of flux in first frame (default 0.1)
        max_frac_flux: Maximum fraction of flux in first frame (default 0.9)
        min_offset: Minimum acceptable time offset in ms (default -500)
        max_offset: Maximum acceptable time offset in ms (default 500)
        
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
    
    # Add subtitle with equation and quality assessment if fit_result available
    if fit_result:
        slope = fit_result['slope']
        intercept = fit_result['intercept']
        r_squared = fit_result['r_squared']
        # Format: "Line delay of intercept + slope x Y ms, R² = value" (3 sig figs)
        sign = '+' if slope >= 0 else '-'
        subtitle = 'Line delay of {0:.3g} {1} {2:.3g} x Y ms, R\u00b2 = {3:.3f}'.format(
            intercept, sign, abs(slope), r_squared)
        
        # Add quality indicator to subtitle
        if r_squared >= 0.98:
            subtitle += ' - Excellent'
            plot_model.SubtitleColor = OxyPlot.OxyColors.Green
        elif r_squared >= 0.96:
            subtitle += ' - Good'
            plot_model.SubtitleColor = OxyPlot.OxyColors.Green
        elif r_squared >= 0.9:
            subtitle += ' - Poor - REDO'
            plot_model.SubtitleColor = OxyPlot.OxyColors.Red
        else:
            subtitle += ' - Failed - REDO'
            plot_model.SubtitleColor = OxyPlot.OxyColors.Red
        
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
# XLSX WRITER (Stability Test output)
# =============================================================================

class SimpleXlsxWriter:
    """Minimal XLSX writer using System.IO.Compression (IronPython compatible).

    Creates a workbook with multiple sheets containing string or numeric cells.
    Usage:
        SimpleXlsxWriter().save(filepath, [('Sheet1', rows1), ('Sheet2', rows2)])
    where rows is a list of lists: [[val, val, ...], ...]
    Values may be str, int, float, or None.
    """

    def _col_letter(self, col_idx):
        """Convert 0-based column index to Excel column letter (A, B, ..., Z, AA ...)"""
        result = ''
        n = col_idx
        while True:
            result = chr(ord('A') + (n % 26)) + result
            n = n // 26 - 1
            if n < 0:
                break
        return result

    def _cell_ref(self, col_idx, row_num):
        """Return Excel cell reference like 'A1' (row_num is 1-based)"""
        return self._col_letter(col_idx) + str(row_num)

    def _escape(self, text):
        """Escape XML special characters"""
        s = str(text) if text is not None else ''
        s = s.replace('&', '&amp;')
        s = s.replace('<', '&lt;')
        s = s.replace('>', '&gt;')
        s = s.replace('"', '&quot;')
        return s

    def _build_worksheet(self, rows):
        """Build worksheet XML from a list of rows (list of lists)"""
        rows_xml = []
        for row_num, row_data in enumerate(rows, start=1):
            cells = []
            for col_idx, value in enumerate(row_data):
                ref = self._cell_ref(col_idx, row_num)
                if value is None:
                    cells.append('<c r="{0}" t="inlineStr"><is><t></t></is></c>'.format(ref))
                elif isinstance(value, bool):
                    cells.append('<c r="{0}" t="inlineStr"><is><t>{1}</t></is></c>'.format(
                        ref, self._escape(str(value))))
                elif isinstance(value, (int, float)):
                    if value != value:  # NaN check
                        cells.append('<c r="{0}" t="inlineStr"><is><t>NaN</t></is></c>'.format(ref))
                    else:
                        cells.append('<c r="{0}"><v>{1}</v></c>'.format(ref, value))
                else:
                    cells.append('<c r="{0}" t="inlineStr"><is><t>{1}</t></is></c>'.format(
                        ref, self._escape(str(value))))
            if cells:
                rows_xml.append('<row r="{0}">{1}</row>'.format(row_num, ''.join(cells)))
        return (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<sheetData>'
            + ''.join(rows_xml) +
            '</sheetData>'
            '</worksheet>'
        )

    def _write_entry(self, archive, path, content):
        """Write a UTF-8 string as an entry in the ZIP archive"""
        entry = archive.CreateEntry(path)
        entry_stream = entry.Open()
        try:
            data = System.Text.Encoding.UTF8.GetBytes(content)
            entry_stream.Write(data, 0, data.Length)
        finally:
            entry_stream.Close()

    def save(self, filepath, sheets):
        """Write an XLSX file.

        filepath: full path to .xlsx file to create
        sheets:   list of (sheet_name, rows) tuples
        """
        num_sheets = len(sheets)

        # [Content_Types].xml
        ws_overrides = ''.join(
            '<Override PartName="/xl/worksheets/sheet{0}.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'.format(i + 1)
            for i in range(num_sheets)
        )
        content_types_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            + ws_overrides +
            '<Override PartName="/xl/styles.xml"'
            ' ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
            '</Types>'
        )

        # _rels/.rels
        root_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument"'
            ' Target="xl/workbook.xml"/>'
            '</Relationships>'
        )

        # xl/workbook.xml
        sheet_tags = ''.join(
            '<sheet name="{0}" sheetId="{1}" r:id="rId{1}"/>'.format(self._escape(name), i + 1)
            for i, (name, _) in enumerate(sheets)
        )
        workbook_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
            ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets>' + sheet_tags + '</sheets>'
            '</workbook>'
        )

        # xl/_rels/workbook.xml.rels
        ws_rels = ''.join(
            '<Relationship Id="rId{0}"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet"'
            ' Target="worksheets/sheet{0}.xml"/>'.format(i + 1)
            for i in range(num_sheets)
        )
        styles_rel_id = num_sheets + 1
        wb_rels_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            + ws_rels +
            '<Relationship Id="rId{0}"'
            ' Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles"'
            ' Target="styles.xml"/>'.format(styles_rel_id) +
            '</Relationships>'
        )

        # xl/styles.xml (minimal valid)
        styles_xml = (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
            '<fonts count="1"><font><name val="Calibri"/><sz val="11"/></font></fonts>'
            '<fills count="2">'
            '<fill><patternFill patternType="none"/></fill>'
            '<fill><patternFill patternType="gray125"/></fill>'
            '</fills>'
            '<borders count="1"><border><left/><right/><top/><bottom/><diagonal/></border></borders>'
            '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
            '<cellXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/></cellXfs>'
            '</styleSheet>'
        )

        file_stream = System.IO.File.Create(filepath)
        try:
            archive = System.IO.Compression.ZipArchive(
                file_stream, System.IO.Compression.ZipArchiveMode.Create, True)
            try:
                self._write_entry(archive, '[Content_Types].xml', content_types_xml)
                self._write_entry(archive, '_rels/.rels', root_rels_xml)
                self._write_entry(archive, 'xl/workbook.xml', workbook_xml)
                self._write_entry(archive, 'xl/_rels/workbook.xml.rels', wb_rels_xml)
                self._write_entry(archive, 'xl/styles.xml', styles_xml)
                for i, (name, rows) in enumerate(sheets):
                    ws_xml = self._build_worksheet(rows)
                    self._write_entry(archive, 'xl/worksheets/sheet{0}.xml'.format(i + 1), ws_xml)
            finally:
                archive.Dispose()
        finally:
            file_stream.Close()


# =============================================================================
# PHASE 6 & 7: GUI INTERFACE AND MAIN CALIBRATION LOGIC
# =============================================================================

class _MinDelayDialog(Form):
    """Simple modal dialog prompting the user to enter a minimum line delay value."""

    def __init__(self, hint_text=''):
        self.min_delay_ms = None
        self.Text = "Enter Minimum Delay"
        self.ClientSize = Size(420, 160)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.StartPosition = FormStartPosition.CenterParent
        self.TopMost = True

        lbl = Label()
        lbl.Text = "Minimum delay (ms):"
        lbl.Location = Point(20, 20)
        lbl.AutoSize = True
        self.Controls.Add(lbl)

        self._txt = TextBox()
        self._txt.Text = "2.0"
        self._txt.Location = Point(160, 17)
        self._txt.Width = 80
        self.Controls.Add(self._txt)

        hint = Label()
        hint.Text = hint_text
        hint.Location = Point(20, 55)
        hint.Size = Size(380, 40)
        hint.ForeColor = Color.Gray
        self.Controls.Add(hint)

        btn_ok = Button()
        btn_ok.Text = "OK"
        btn_ok.Location = Point(230, 110)
        btn_ok.Size = Size(75, 27)
        btn_ok.Click += self._ok_click
        self.Controls.Add(btn_ok)
        self.AcceptButton = btn_ok

        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(320, 110)
        btn_cancel.Size = Size(75, 27)
        btn_cancel.Click += self._cancel_click
        self.Controls.Add(btn_cancel)
        self.CancelButton = btn_cancel

    def _ok_click(self, sender, event):
        try:
            self.min_delay_ms = float(self._txt.Text)
        except ValueError:
            MessageBox.Show("Please enter a numeric value.", "Invalid Input",
                            MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        self.DialogResult = DialogResult.OK

    def _cancel_click(self, sender, event):
        self.DialogResult = DialogResult.Cancel


class SaveCalibrationDialog(Form):
    """Dialog to save a line delay calibration result to Occultation Manager config."""

    def __init__(self, fit_result, capture_settings, preselect_camera_id=None, config=None):
        self._fit_result = fit_result
        self._capture_settings = dict(capture_settings) if capture_settings else {}
        self._config = config   # may be None; _load_cameras creates one if so
        self._camera_ids = []
        self._preselect_camera_id = preselect_camera_id
        self.InitializeComponent()
        self._load_cameras()

    def InitializeComponent(self):
        self.Text = "Save Calibration to Camera"
        self.ClientSize = Size(480, 425)
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        self.TopMost = True

        s  = self._fit_result
        cs = self._capture_settings
        slope     = s.get('slope', 0.0)
        intercept = s.get('intercept', 0.0)
        r2        = s.get('r_squared', 0.0)
        rowh = 28

        # --- Calibration Result section ---
        lbl_title = Label()
        lbl_title.Text = "Calibration Result"
        lbl_title.Font = Font(lbl_title.Font.FontFamily, 9, FontStyle.Bold)
        lbl_title.Location = Point(20, 12)
        lbl_title.AutoSize = True

        lbl_result = Label()
        r2_str = "{0:.4f}".format(r2) if r2 is not None else "N/A"
        lbl_result.Text = "Per Line Delay: {0:.3f} ms/line    Line 0 Delay: {1:.3f} ms    R\u00b2 = {2}".format(
            slope, intercept, r2_str)
        lbl_result.Location = Point(20, 35)
        lbl_result.Size = Size(440, 18)
        lbl_result.ForeColor = Color.DarkBlue

        # --- Camera & Label section ---
        y = 68
        lbl_cam = Label()
        lbl_cam.Text = "Camera:"
        lbl_cam.Location = Point(20, y + 3)
        lbl_cam.AutoSize = True

        self._combo_camera = ComboBox()
        self._combo_camera.Location = Point(130, y)
        self._combo_camera.Size = Size(310, 22)
        self._combo_camera.DropDownStyle = ComboBoxStyle.DropDownList

        y += rowh
        lbl_label = Label()
        lbl_label.Text = "Label:"
        lbl_label.Location = Point(20, y + 3)
        lbl_label.AutoSize = True

        self._txt_label = TextBox()
        self._txt_label.Location = Point(130, y)
        self._txt_label.Size = Size(50, 22)

        lbl_label_hint = Label()
        lbl_label_hint.Text = "(e.g. A, B, C\u2026)"
        lbl_label_hint.Location = Point(188, y + 3)
        lbl_label_hint.AutoSize = True
        lbl_label_hint.ForeColor = Color.Gray

        # --- Camera Settings section ---
        y += rowh + 4
        lbl_settings_title = Label()
        lbl_settings_title.Text = "Camera Settings (auto-populated; edit if needed)"
        lbl_settings_title.Location = Point(20, y)
        lbl_settings_title.Size = Size(440, 16)
        lbl_settings_title.ForeColor = Color.DimGray

        y += 22
        lbl_cam_name = Label()
        lbl_cam_name.Text = "Camera Name:"
        lbl_cam_name.Location = Point(20, y + 3)
        lbl_cam_name.AutoSize = True

        self._txt_camera_name = TextBox()
        self._txt_camera_name.Location = Point(130, y)
        self._txt_camera_name.Size = Size(320, 22)
        self._txt_camera_name.Text = str(cs.get('camera_name', ''))

        y += rowh
        lbl_pc = Label()
        lbl_pc.Text = "PC Name:"
        lbl_pc.Location = Point(20, y + 3)
        lbl_pc.AutoSize = True

        self._txt_pc_name = TextBox()
        self._txt_pc_name.Location = Point(130, y)
        self._txt_pc_name.Size = Size(320, 22)
        self._txt_pc_name.Text = str(cs.get('pc_name', ''))

        y += rowh
        lbl_area = Label()
        lbl_area.Text = "Camera Area:"
        lbl_area.Location = Point(20, y + 3)
        lbl_area.AutoSize = True

        self._txt_camera_area = TextBox()
        self._txt_camera_area.Location = Point(130, y)
        self._txt_camera_area.Size = Size(100, 22)
        self._txt_camera_area.Text = str(cs.get('camera_area', ''))

        lbl_bin = Label()
        lbl_bin.Text = "Binning:"
        lbl_bin.Location = Point(240, y + 3)
        lbl_bin.AutoSize = True

        self._txt_binning = TextBox()
        self._txt_binning.Location = Point(300, y)
        self._txt_binning.Size = Size(80, 22)
        self._txt_binning.Text = str(cs.get('binning', ''))

        y += rowh
        lbl_tilt = Label()
        lbl_tilt.Text = "Tilt (ROI Y):"
        lbl_tilt.Location = Point(20, y + 3)
        lbl_tilt.AutoSize = True

        self._txt_tilt = TextBox()
        self._txt_tilt.Location = Point(130, y)
        self._txt_tilt.Size = Size(80, 22)
        self._txt_tilt.Text = str(cs.get('tilt', ''))

        lbl_pan = Label()
        lbl_pan.Text = "Pan (ROI X):"
        lbl_pan.Location = Point(220, y + 3)
        lbl_pan.AutoSize = True

        self._txt_pan = TextBox()
        self._txt_pan.Location = Point(310, y)
        self._txt_pan.Size = Size(80, 22)
        self._txt_pan.Text = str(cs.get('pan', ''))

        y += rowh
        lbl_cs = Label()
        lbl_cs.Text = "Colour Space:"
        lbl_cs.Location = Point(20, y + 3)
        lbl_cs.AutoSize = True

        self._txt_colour_space = TextBox()
        self._txt_colour_space.Location = Point(130, y)
        self._txt_colour_space.Size = Size(100, 22)
        self._txt_colour_space.Text = str(cs.get('colour_space', ''))

        lbl_ff = Label()
        lbl_ff.Text = "File Format:"
        lbl_ff.Location = Point(240, y + 3)
        lbl_ff.AutoSize = True

        self._txt_file_format = TextBox()
        self._txt_file_format.Location = Point(310, y)
        self._txt_file_format.Size = Size(80, 22)
        self._txt_file_format.Text = str(cs.get('file_format', ''))

        y += rowh
        lbl_exp = Label()
        lbl_exp.Text = "Exposure (ms):"
        lbl_exp.Location = Point(20, y + 3)
        lbl_exp.AutoSize = True

        self._txt_exposure = TextBox()
        self._txt_exposure.Location = Point(130, y)
        self._txt_exposure.Size = Size(80, 22)
        self._txt_exposure.Text = str(cs.get('exposure_ms', ''))

        lbl_gain = Label()
        lbl_gain.Text = "Gain:"
        lbl_gain.Location = Point(220, y + 3)
        lbl_gain.AutoSize = True

        self._txt_gain = TextBox()
        self._txt_gain.Location = Point(265, y)
        self._txt_gain.Size = Size(90, 22)
        self._txt_gain.Text = str(cs.get('gain', ''))

        y += rowh + 4
        lbl_notes = Label()
        lbl_notes.Text = "Notes:"
        lbl_notes.Location = Point(20, y + 3)
        lbl_notes.AutoSize = True

        self._txt_notes = TextBox()
        self._txt_notes.Location = Point(130, y)
        self._txt_notes.Size = Size(320, 50)
        self._txt_notes.Multiline = True
        self._txt_notes.ScrollBars = ScrollBars.Vertical

        y += 58
        self._btn_save = Button()
        self._btn_save.Text = "Save"
        self._btn_save.Location = Point(270, y)
        self._btn_save.Size = Size(85, 27)
        self._btn_save.Click += self._save_click

        btn_cancel = Button()
        btn_cancel.Text = "Cancel"
        btn_cancel.Location = Point(368, y)
        btn_cancel.Size = Size(85, 27)
        btn_cancel.Click += self._cancel_click

        for ctrl in [
            lbl_title, lbl_result,
            lbl_cam, self._combo_camera,
            lbl_label, self._txt_label, lbl_label_hint,
            lbl_settings_title,
            lbl_cam_name, self._txt_camera_name,
            lbl_pc, self._txt_pc_name,
            lbl_area, self._txt_camera_area,
            lbl_bin, self._txt_binning,
            lbl_tilt, self._txt_tilt,
            lbl_pan, self._txt_pan,
            lbl_cs, self._txt_colour_space,
            lbl_ff, self._txt_file_format,
            lbl_exp, self._txt_exposure,
            lbl_gain, self._txt_gain,
            lbl_notes, self._txt_notes,
            self._btn_save, btn_cancel,
        ]:
            self.Controls.Add(ctrl)

    def _load_cameras(self):
        """Populate the camera dropdown from Occultation Manager config."""
        self._combo_camera.Items.Clear()
        if not _OM_CONFIG_AVAILABLE:
            self._combo_camera.Items.Add(
                '(Config not available \u2014 run from Occultation Manager)')
            self._combo_camera.SelectedIndex = 0
            self._combo_camera.Enabled = False
            self._btn_save.Enabled = False
            return
        try:
            if self._config is None:
                self._config = _om_config.ConfigManager()
            cameras = self._config.get_cameras()
            if not cameras:
                self._combo_camera.Items.Add(
                    '(No cameras configured \u2014 add a camera in Occultation Manager first)')
                self._combo_camera.SelectedIndex = 0
                self._combo_camera.Enabled = False
                self._btn_save.Enabled = False
            else:
                self._camera_ids = [cam['id'] for cam in cameras]
                for cam in cameras:
                    self._combo_camera.Items.Add(cam['name'])
                if self._preselect_camera_id:
                    try:
                        idx = self._camera_ids.index(self._preselect_camera_id)
                        self._combo_camera.SelectedIndex = idx
                    except ValueError:
                        self._combo_camera.SelectedIndex = 0
                else:
                    self._combo_camera.SelectedIndex = 0
        except Exception as ex:
            self._combo_camera.Items.Add('(Config error: ' + str(ex) + ')')
            self._combo_camera.SelectedIndex = 0
            self._combo_camera.Enabled = False
            self._btn_save.Enabled = False
            self._config = None

    def _save_click(self, sender, event):
        """Validate inputs and write the calibration run to config."""
        if self._config is None:
            MessageBox.Show(
                "Occultation Manager config is not available.",
                "Save Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            return

        label = self._txt_label.Text.strip()
        if not label:
            MessageBox.Show(
                "Please enter a label (e.g. A, B, C).",
                "Label Required",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            self._txt_label.Focus()
            return

        idx = self._combo_camera.SelectedIndex
        if idx < 0 or idx >= len(self._camera_ids):
            MessageBox.Show(
                "Please select a camera.",
                "Camera Required",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return
        camera_id = self._camera_ids[idx]

        def try_int(text):
            try:
                return int(text.strip())
            except Exception:
                return None

        def try_float(text):
            try:
                return float(text.strip())
            except Exception:
                return None

        from datetime import datetime as _dt
        run_dict = {
            'camera_id':      camera_id,
            'label':          label,
            'run_datetime':   _dt.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ'),
            'camera_name':    self._txt_camera_name.Text.strip(),
            'pc_name':        self._txt_pc_name.Text.strip(),
            'camera_area':    self._txt_camera_area.Text.strip(),
            'binning':        self._txt_binning.Text.strip(),
            'tilt':           try_int(self._txt_tilt.Text),
            'pan':            try_int(self._txt_pan.Text),
            'colour_space':   self._txt_colour_space.Text.strip(),
            'file_format':    self._txt_file_format.Text.strip(),
            'exposure_ms':    try_float(self._txt_exposure.Text),
            'gain':           self._txt_gain.Text.strip(),
            'per_line_delay': round(self._fit_result['slope'], 6),
            'line_0_delay':   round(self._fit_result['intercept'], 6),
            'notes':          self._txt_notes.Text.strip(),
        }
        try:
            self._config.add_line_delay_calibration(run_dict)
            self.DialogResult = DialogResult.OK
            self.Close()
        except Exception as ex:
            MessageBox.Show(
                "Save failed:\n" + str(ex),
                "Save Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )

    def _cancel_click(self, sender, event):
        self.DialogResult = DialogResult.Cancel
        self.Close()


class LEDLineDelayCalibrationForm(Form):
    """Windows Forms GUI for LED line delay calibration"""
    
    def __init__(self, sharpcap=None, config=None, theme_manager=None):
        """Initialize the calibration form"""
        self._sharpcap = sharpcap
        self._config = config
        self.capture_handler = FrameCaptureHandler()
        self.stop_requested = False
        # Stability test result storage (for save / re-save)
        self._stab_run_start = None
        self._stab_delays = []
        self._stab_timestamps = []
        self._stab_camera_settings = {}
        self._stab_stats_text = ''
        self._stab_last_save_folder = None
        # Calibration tab result storage (for Save Result to Camera)
        self._calib_fit_result = None
        self._calib_capture_settings = {}
        self._calib_saved = False
        self._active_shutter_type = None
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
    
    def set_and_refresh_plot(self, plot_view, plot_model):
        """Set plot model and force refresh"""
        plot_view.Model = plot_model
        plot_view.InvalidatePlot(True)
        
    def InitializeComponent(self):
        """Setup GUI components"""
        self.Text = "Camera Delay Calibration"
        self.ClientSize = Size(720, 930)
        self.TopMost = True
        self.FormBorderStyle = FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        
        # Create tab control
        self.tab_control = TabControl()
        self.tab_control.Location = Point(10, 10)
        self.tab_control.Size = Size(700, 860)
        
        # Create tabs
        self.tab_calibration = TabPage()
        self.tab_calibration.Text = "Line Delay Calibration"
        self.tab_calibration.Size = Size(692, 534)
        
        self.tab_stability = TabPage()
        self.tab_stability.Text = "Long Term Timing Stability"
        self.tab_stability.Size = Size(692, 534)
        
        self.tab_control.TabPages.Add(self.tab_calibration)
        self.tab_control.TabPages.Add(self.tab_stability)
        self.Controls.Add(self.tab_control)
        
        # === LINE DELAY CALIBRATION TAB ===
        
        # Capture mode selection (moved to top)
        self.label_mode = Label()
        self.label_mode.Text = "Calibration Mode:"
        self.label_mode.Location = Point(20, 20)
        self.label_mode.AutoSize = True

        self.panel_mode_group = Panel()
        self.panel_mode_group.Location = Point(155, 16)
        self.panel_mode_group.Size = Size(260, 24)
        
        self.radio_live = RadioButton()
        self.radio_live.Text = "Live Capture"
        self.radio_live.Location = Point(0, 2)
        self.radio_live.AutoSize = True
        self.radio_live.Checked = True
        self.radio_live.CheckedChanged += self.on_mode_changed
        
        self.radio_adv = RadioButton()
        self.radio_adv.Text = "Use ADV File"
        self.radio_adv.Location = Point(120, 2)
        self.radio_adv.AutoSize = True
        self.radio_adv.Enabled = ADV_AVAILABLE
        self.radio_adv.CheckedChanged += self.on_mode_changed
        if not ADV_AVAILABLE:
            self.radio_adv.Text = "Use ADV File (not available)"

        self.panel_mode_group.Controls.Add(self.radio_live)
        self.panel_mode_group.Controls.Add(self.radio_adv)

        # Shutter type selection (own row)
        self.label_shutter_type = Label()
        self.label_shutter_type.Text = "Shutter Type:"
        self.label_shutter_type.Location = Point(20, 52)
        self.label_shutter_type.AutoSize = True

        self.panel_shutter_group = Panel()
        self.panel_shutter_group.Location = Point(155, 48)
        self.panel_shutter_group.Size = Size(180, 24)

        self.radio_shutter_rolling = RadioButton()
        self.radio_shutter_rolling.Text = "Rolling"
        self.radio_shutter_rolling.Location = Point(0, 2)
        self.radio_shutter_rolling.AutoSize = True
        self.radio_shutter_rolling.Checked = True

        self.radio_shutter_global = RadioButton()
        self.radio_shutter_global.Text = "Global"
        self.radio_shutter_global.Location = Point(80, 2)
        self.radio_shutter_global.AutoSize = True

        self.panel_shutter_group.Controls.Add(self.radio_shutter_rolling)
        self.panel_shutter_group.Controls.Add(self.radio_shutter_global)

        self.button_shutter_info = Button()
        self.button_shutter_info.Text = "i"
        self.button_shutter_info.Location = Point(376, 48)
        self.button_shutter_info.Size = Size(22, 22)
        self.button_shutter_info.Font = Font(self.button_shutter_info.Font.FontFamily, 8, FontStyle.Bold)
        self.button_shutter_info.Click += self.show_shutter_type_info
        
        # Duration setting
        self.label_duration = Label()
        self.label_duration.Text = "Capture Duration (seconds):"
        self.label_duration.Location = Point(20, 82)
        self.label_duration.AutoSize = True
        
        self.textbox_duration = TextBox()
        self.textbox_duration.Text = "30"
        self.textbox_duration.Location = Point(210, 80)
        self.textbox_duration.Width = 60
        
        # Flash duration setting
        self.label_flash = Label()
        self.label_flash.Text = "GPS Flash Duration (ms):"
        self.label_flash.Location = Point(300, 82)
        self.label_flash.AutoSize = True
        
        self.textbox_flash = TextBox()
        self.textbox_flash.Text = "100"
        self.textbox_flash.Location = Point(480, 80)
        self.textbox_flash.Width = 60
        
        # Invert signal checkbox
        self.checkbox_invert = CheckBox()
        self.checkbox_invert.Text = "Invert Signal (for inverted PPS)"
        self.checkbox_invert.Location = Point(560, 80)
        self.checkbox_invert.Width = 120
        self.checkbox_invert.AutoSize = True
        self.checkbox_invert.CheckedChanged += self.on_invert_changed
        
        # Start button
        self.button_start = Button()
        self.button_start.Text = "Start Calibration"
        self.button_start.Location = Point(20, 112)
        self.button_start.Size = Size(120, 30)
        self.button_start.Click += self.start_calibration
        
        # Stop button
        self.button_stop = Button()
        self.button_stop.Text = "Stop"
        self.button_stop.Location = Point(160, 112)
        self.button_stop.Size = Size(80, 30)
        self.button_stop.Enabled = False
        self.button_stop.Click += self.stop_calibration
        
        # Status label
        self.label_status = Label()
        self.label_status.Text = "Ready"
        self.label_status.Location = Point(260, 120)
        self.label_status.AutoSize = True
        self.label_status.Font = Font(self.label_status.Font.FontFamily, 9, FontStyle.Bold)
        
        # Results text box
        self.label_results = Label()
        self.label_results.Text = "Results:"
        self.label_results.Location = Point(20, 152)
        self.label_results.AutoSize = True
        
        self.textbox_results = TextBox()
        self.textbox_results.Location = Point(20, 172)
        self.textbox_results.Size = Size(660, 100)
        self.textbox_results.Multiline = True
        self.textbox_results.ReadOnly = True
        self.textbox_results.ScrollBars = ScrollBars.Vertical
        
        # Plot view
        self.plot_view = OxyPlot.WindowsForms.PlotView()
        self.plot_view.Location = Point(20, 282)
        self.plot_view.Size = Size(660, 260)
        
        # Close button
        self.button_close = Button()
        self.button_close.Text = "Close"
        self.button_close.Location = Point(600, 602)
        self.button_close.Size = Size(80, 25)
        self.button_close.Click += self.close_form

        # Save Result to Camera button (enabled only after a successful calibration)
        self.button_save_calibration = Button()
        self.button_save_calibration.Text = "Save Result to Camera..."
        self.button_save_calibration.Location = Point(440, 602)
        self.button_save_calibration.Size = Size(150, 25)
        self.button_save_calibration.Enabled = False
        self.button_save_calibration.Click += self.save_calibration_click

        # Approximate Delays button (no GPS flasher required)
        self.label_approx_delays = Label()
        self.label_approx_delays.Text = "Alternative if no GPS flasher available"
        self.label_approx_delays.Location = Point(20, 582)
        self.label_approx_delays.AutoSize = True
        self.label_approx_delays.ForeColor = Color.Black
        self.label_approx_delays.Font = Font(self.label_approx_delays.Font.FontFamily,
                                             self.label_approx_delays.Font.Size, FontStyle.Bold)

        self.button_approx_delays = Button()
        self.button_approx_delays.Text = "Approximate Delays"
        self.button_approx_delays.Location = Point(20, 602)
        self.button_approx_delays.Size = Size(175, 25)
        self.button_approx_delays.Click += self.approximate_delays_click

        # Add controls to calibration tab
        self.tab_calibration.Controls.Add(self.label_duration)
        self.tab_calibration.Controls.Add(self.textbox_duration)
        self.tab_calibration.Controls.Add(self.label_flash)
        self.tab_calibration.Controls.Add(self.textbox_flash)
        self.tab_calibration.Controls.Add(self.checkbox_invert)
        self.tab_calibration.Controls.Add(self.label_mode)
        self.tab_calibration.Controls.Add(self.panel_mode_group)
        self.tab_calibration.Controls.Add(self.label_shutter_type)
        self.tab_calibration.Controls.Add(self.panel_shutter_group)
        self.tab_calibration.Controls.Add(self.button_shutter_info)
        self.tab_calibration.Controls.Add(self.button_start)
        self.tab_calibration.Controls.Add(self.button_stop)
        self.tab_calibration.Controls.Add(self.label_status)
        self.tab_calibration.Controls.Add(self.label_results)
        self.tab_calibration.Controls.Add(self.textbox_results)
        self.tab_calibration.Controls.Add(self.plot_view)
        self.tab_calibration.Controls.Add(self.button_save_calibration)
        self.tab_calibration.Controls.Add(self.button_approx_delays)
        self.tab_calibration.Controls.Add(self.label_approx_delays)
        self.tab_calibration.Controls.Add(self.button_close)
        
        # === LONG TERM TIMING STABILITY TAB ===
        
        # Capture Duration
        self.label_stab_duration = Label()
        self.label_stab_duration.Text = "Capture Duration (seconds):"
        self.label_stab_duration.Location = Point(20, 20)
        self.label_stab_duration.AutoSize = True
        
        self.textbox_stab_duration = TextBox()
        self.textbox_stab_duration.Text = "30"
        self.textbox_stab_duration.Location = Point(210, 18)
        self.textbox_stab_duration.Width = 60
        
        # Test Duration
        self.label_test_duration = Label()
        self.label_test_duration.Text = "Test Duration (HH:MM):"
        self.label_test_duration.Location = Point(300, 20)
        self.label_test_duration.AutoSize = True
        
        self.textbox_test_duration = TextBox()
        self.textbox_test_duration.Text = "01:00"
        self.textbox_test_duration.Location = Point(460, 18)
        self.textbox_test_duration.Width = 60
        
        # GPS Flash Duration
        self.label_stab_flash = Label()
        self.label_stab_flash.Text = "GPS Flash Duration (ms):"
        self.label_stab_flash.Location = Point(20, 50)
        self.label_stab_flash.AutoSize = True
        
        self.textbox_stab_flash = TextBox()
        self.textbox_stab_flash.Text = "100"
        self.textbox_stab_flash.Location = Point(210, 48)
        self.textbox_stab_flash.Width = 60
        
        # Invert checkbox
        self.checkbox_stab_invert = CheckBox()
        self.checkbox_stab_invert.Text = "Invert Signal (for inverted PPS)"
        self.checkbox_stab_invert.Location = Point(300, 48)
        self.checkbox_stab_invert.AutoSize = True
        self.checkbox_stab_invert.CheckedChanged += self.on_stab_invert_changed
        
        # Start button
        self.button_stab_start = Button()
        self.button_stab_start.Text = "Start Stability Test"
        self.button_stab_start.Location = Point(20, 80)
        self.button_stab_start.Size = Size(140, 30)
        self.button_stab_start.Click += self.start_stability_test
        
        # Stop button
        self.button_stab_stop = Button()
        self.button_stab_stop.Text = "Stop"
        self.button_stab_stop.Location = Point(180, 80)
        self.button_stab_stop.Size = Size(80, 30)
        self.button_stab_stop.Enabled = False
        self.button_stab_stop.Click += self.stop_stability_test

        # Save Results button
        self.button_stab_save = Button()
        self.button_stab_save.Text = "Save Results"
        self.button_stab_save.Location = Point(540, 80)
        self.button_stab_save.Size = Size(135, 30)
        self.button_stab_save.Enabled = False
        self.button_stab_save.Click += self.save_stability_results_click

        # Save path label (same Y as Statistics: label) and Open Folder button
        self.label_stab_saved_path = Label()
        self.label_stab_saved_path.Location = Point(100, 122)
        self.label_stab_saved_path.Size = Size(430, 18)
        self.label_stab_saved_path.AutoEllipsis = True
        self.label_stab_saved_path.Text = ''

        self.button_stab_open_folder = Button()
        self.button_stab_open_folder.Text = "Open Output Folder"
        self.button_stab_open_folder.Location = Point(538, 115)
        self.button_stab_open_folder.Size = Size(140, 28)
        self.button_stab_open_folder.Enabled = False
        self.button_stab_open_folder.Click += self.open_save_folder_click

        # Status label
        self.label_stab_status = Label()
        self.label_stab_status.Text = "Ready"
        self.label_stab_status.Location = Point(280, 88)
        self.label_stab_status.AutoSize = True
        self.label_stab_status.Font = Font(self.label_stab_status.Font.FontFamily, 9, FontStyle.Bold)
        
        # Statistics text box
        self.label_stab_stats = Label()
        self.label_stab_stats.Text = "Statistics:"
        self.label_stab_stats.Location = Point(20, 120)
        self.label_stab_stats.AutoSize = True
        
        self.textbox_stab_stats = TextBox()
        self.textbox_stab_stats.Location = Point(20, 140)
        self.textbox_stab_stats.Size = Size(660, 80)
        self.textbox_stab_stats.Multiline = True
        self.textbox_stab_stats.ReadOnly = True
        self.textbox_stab_stats.ScrollBars = ScrollBars.Vertical
        
        # Time series plot
        self.plot_stab_timeseries = OxyPlot.WindowsForms.PlotView()
        self.plot_stab_timeseries.Location = Point(20, 230)
        self.plot_stab_timeseries.Size = Size(660, 200)
        
        # Histogram plot
        self.plot_stab_histogram = OxyPlot.WindowsForms.PlotView()
        self.plot_stab_histogram.Location = Point(20, 440)
        self.plot_stab_histogram.Size = Size(660, 380)
        
        # Add controls to stability tab
        self.tab_stability.Controls.Add(self.label_stab_duration)
        self.tab_stability.Controls.Add(self.textbox_stab_duration)
        self.tab_stability.Controls.Add(self.label_test_duration)
        self.tab_stability.Controls.Add(self.textbox_test_duration)
        self.tab_stability.Controls.Add(self.label_stab_flash)
        self.tab_stability.Controls.Add(self.textbox_stab_flash)
        self.tab_stability.Controls.Add(self.checkbox_stab_invert)
        self.tab_stability.Controls.Add(self.button_stab_start)
        self.tab_stability.Controls.Add(self.button_stab_stop)
        self.tab_stability.Controls.Add(self.label_stab_status)
        self.tab_stability.Controls.Add(self.label_stab_stats)
        self.tab_stability.Controls.Add(self.textbox_stab_stats)
        self.tab_stability.Controls.Add(self.plot_stab_timeseries)
        self.tab_stability.Controls.Add(self.plot_stab_histogram)
        self.tab_stability.Controls.Add(self.button_stab_save)
        self.tab_stability.Controls.Add(self.label_stab_saved_path)
        self.tab_stability.Controls.Add(self.button_stab_open_folder)
    
    def on_mode_changed(self, sender, event):
        """Handle mode selection change - update UI based on selected mode"""
        if self.radio_adv.Checked:
            # ADV mode selected
            self.button_start.Text = "Load ADV File"
            self.textbox_duration.Enabled = False
            self.label_duration.Enabled = False
            # Note: Stop button not functional in ADV mode (file processing can't be interrupted)
        else:
            # Live capture mode selected
            self.button_start.Text = "Start Calibration"
            self.textbox_duration.Enabled = True
            self.label_duration.Enabled = True

    def show_shutter_type_info(self, sender, event):
        """Show help text describing rolling vs global shutter cameras."""
        info_text = (
            "Global Shutter exposes all sensor lines at the same time.\n\n"
            "Rolling Shutter exposure each line at a slightly later time.\n\n"
            "Most cameras are Rolling Shutter, all Sony STARVIS and STARVIS II series cameras are rolling shutter.\n\n"
            "Global Shutter cameras are more expensive and are often sold as suitable for Solar imaging. "
            "Global shutter sensors include IMX 174, 428, 429, 432 sensors. "
            "All Sony PREGIUS sensors are global shutter."
        )
        MessageBox.Show(
            info_text,
            "Shutter Type Information",
            MessageBoxButtons.OK,
            MessageBoxIcon.Information
        )
    
    def on_invert_changed(self, sender, event):
        """Handle invert checkbox change - show warning when enabled"""
        if self.checkbox_invert.Checked:
            # Show warning message
            result = MessageBox.Show(
                "Invert can be used for an LED that is ON for 900 ms and OFF for 100 ms. "
                "The built in LED on an Arduino module does this, as do some GPS receivers. "
                "It is better to use a proper GPS flasher, but acceptable calibration is "
                "possible with an inverted flash.",
                "Inverted PPS Signal Warning",
                MessageBoxButtons.OKCancel,
                MessageBoxIcon.Warning
            )
            
            # If user cancels, uncheck the box
            if result == DialogResult.Cancel:
                self.checkbox_invert.Checked = False
        
    def start_calibration(self, sender, event):
        """Start LED line delay calibration in separate thread"""
        # Check camera connection (only required for Live Capture mode)
        use_adv = self.radio_adv.Checked
        if not use_adv and (self._sharpcap is None or self._sharpcap.SelectedCamera is None):
            MessageBox.Show(
                "No camera is connected.\n\nPlease connect a camera before running Live Capture calibration.",
                "Camera Connection Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            return
        
        # Reset previous calibration result and disable Save button for new run
        self._calib_fit_result = None
        self._calib_saved = False
        if hasattr(self, 'button_save_calibration'):
            self.button_save_calibration.Enabled = False

        # Disable start button, enable stop (though stop doesn't work for ADV processing)
        self.button_start.Enabled = False
        self.button_stop.Enabled = True
        self.label_status.Text = "Starting..."
        self.label_status.ForeColor = Color.Orange
        
        # Capture shutter type on UI thread before handing off to background thread
        self._active_shutter_type = self._get_selected_shutter_type()
        # Run calibration in separate thread to avoid blocking UI
        thread = Thread(ParameterizedThreadStart(self.run_calibration_thread))
        thread.SetApartmentState(ApartmentState.STA)
        thread.Start(self)
        
    def run_calibration_thread(self, form):
        """Main calibration workflow - runs in separate thread"""
        try:
            # Get parameters with validation
            try:
                duration = float(form.textbox_duration.Text)
                flash_ms = float(form.textbox_flash.Text)
            except ValueError:
                raise Exception("Invalid input: Duration and Flash Duration must be numeric values")
            
            # Validate parameter ranges
            if flash_ms <= 0 or flash_ms > 1000:
                raise Exception("GPS Flash Duration must be between 0 and 1000 ms")
            
            use_adv = form.radio_adv.Checked
            
            # Branch based on capture mode
            if use_adv:
                # ADV file loading workflow (camera not required, duration not used)
                form.run_adv_workflow(flash_ms, None)
            else:
                # Live capture workflow (requires camera and duration)
                if duration <= 0 or duration > 300:
                    raise Exception("Capture Duration must be between 0 and 300 seconds")
                camera = form._sharpcap.SelectedCamera if form._sharpcap else None
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
            
            # Apply signal inversion if requested
            if self.checkbox_invert.Checked:
                print("\nApplying signal inversion...")
                self.capture_handler.measurements = invert_measurements(
                    self.capture_handler.measurements,
                    auto_detect_max=True
                )
            
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
                'width': roi.Width,
                'roi_x': roi.X,
                'roi_y': roi.Y
            }
            
            # Save CSV with top 2 and bottom 2 aperture data
            csv_path = None
            try:
                csv_path = save_tangra_csv(
                    self.capture_handler.measurements,
                    self.capture_handler.timestamps,
                    self.capture_handler.frame_numbers,
                    aperture_y_positions,
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
            fit_result = self._apply_shutter_type_to_fit_result(fit_result, all_delays_filtered)

            # Store calibration result for "Save Result to Camera" feature
            self._calib_fit_result = fit_result
            capture_settings = self._collect_calibration_settings(camera)
            capture_settings['shutter_type'] = fit_result.get('shutter_type', 'Rolling')
            capture_settings['measurement_method'] = 'GPS'
            self._calib_capture_settings = capture_settings

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
    
    def run_adv_workflow(self, flash_ms, camera):
        """Run calibration using ADV file loading and replay
        
        Args:
            flash_ms: GPS flash duration in milliseconds
            camera: Camera object (not used, kept for signature consistency)
        """
        import adv_helper
        
        # Go straight to file selection dialog (skip the informational prompt)
        self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Select ADV file...'))
        
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
            # User cancelled file selection - exit gracefully
            print("ADV file selection cancelled by user")
            self.SafeInvoke(lambda: setattr(self.label_status, 'Text', 'Cancelled'))
            self.SafeInvoke(lambda: setattr(self.label_status, 'ForeColor', Color.Gray))
            return  # Exit gracefully without error
        
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
        
        # Apply signal inversion if requested
        if self.checkbox_invert.Checked:
            print("\nApplying signal inversion...")
            self.capture_handler.measurements = invert_measurements(
                self.capture_handler.measurements,
                auto_detect_max=True
            )
        
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
            'resolution': '{0}x{1}'.format(frame_width, frame_height),
            'width': frame_width
        }
        
        # Save CSV
        csv_path = None
        try:
            csv_path = save_tangra_csv(
                self.capture_handler.measurements,
                self.capture_handler.timestamps,
                self.capture_handler.frame_numbers,
                aperture_y_positions,
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
        
        if not fit_result:
            raise Exception("Linear fit failed. Please check data and try again.")
        fit_result = self._apply_shutter_type_to_fit_result(fit_result, all_delays_filtered)

        # Store calibration result for "Save Result to Camera" feature
        self._calib_fit_result = fit_result
        capture_settings = self._collect_calibration_settings_from_adv(
            adv_file_name, frame_width, frame_height, exposure_ms)
        capture_settings['shutter_type'] = fit_result.get('shutter_type', 'Rolling')
        capture_settings['measurement_method'] = 'GPS'
        self._calib_capture_settings = capture_settings

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
        results_text += "Line delay of {0:.3g} {1} {2:.3g} x Y ms, R\u00b2 = {3:.3f}\r\n".format(
            intercept, sign, abs(slope), r_squared)
        
        # Add quality assessment based on R²
        if r_squared >= 0.98:
            results_text += "Excellent calibration fit.\r\n\r\n"
        elif r_squared >= 0.96:
            results_text += "Good calibration fit, but could be better. Check the flash brightness is not too high or low and is evenly illuminated.\r\n\r\n"
        elif r_squared >= 0.9:
            results_text += "Poor calibration fit. Please redo with better flash illumination.\r\n\r\n"
        else:
            results_text += "Very poor or failed calibration. Please redo with better flash illumination.\r\n\r\n"
        
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

        # Enable the Save button now that a valid result is available
        if hasattr(self, 'button_save_calibration'):
            self.button_save_calibration.Enabled = True

    def stop_calibration(self, sender, event):
        """Stop ongoing calibration"""
        try:
            if self.capture_handler.capturing:
                camera = self._sharpcap.SelectedCamera if self._sharpcap else None
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
                camera = self._sharpcap.SelectedCamera if self._sharpcap else None
                if camera:
                    self.capture_handler.stop_capture(camera)
            
            self.Close()
        except Exception as ex:
            print("Error in close_form: " + str(ex))
            self.Close()  # Close anyway

    def _get_selected_shutter_type(self):
        """Return selected shutter type string for storage and fit behaviour."""
        if hasattr(self, 'radio_shutter_global') and self.radio_shutter_global.Checked:
            return 'Global'
        return 'Rolling'

    def _apply_shutter_type_to_fit_result(self, fit_result, all_delays):
        """Force global shutter calibrations to slope=0 and fixed-delay intercept."""
        shutter_type = self._active_shutter_type or self._get_selected_shutter_type()
        fit_result['shutter_type'] = shutter_type
        if shutter_type != 'Global':
            return fit_result

        offsets = []
        for d in all_delays:
            try:
                offsets.append(float(d.get('time_offset', 0.0)))
            except Exception:
                pass

        if offsets:
            intercept = sum(offsets) / float(len(offsets))
            ss_tot = sum((y - intercept) ** 2 for y in offsets)
            ss_res = sum((y - intercept) ** 2 for y in offsets)
            r_squared = 1.0 - (ss_res / ss_tot) if abs(ss_tot) > 1e-10 else 1.0
            fit_result['intercept'] = intercept
            fit_result['r_squared'] = r_squared

        fit_result['slope'] = 0.0
        fit_result['description'] = 'Global shutter fixed delay: {0:.3f} ms'.format(
            float(fit_result.get('intercept', 0.0)))
        return fit_result

    def approximate_delays_click(self, sender, event):
        """Start the approximate delays measurement in a background thread."""
        if self._sharpcap is None or self._sharpcap.SelectedCamera is None:
            MessageBox.Show(
                "No camera is connected.\n\nPlease connect a camera before using Approximate Delays.",
                "Camera Not Connected",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return
        self.button_approx_delays.Enabled = False
        self.button_start.Enabled = False
        self._active_shutter_type = self._get_selected_shutter_type()
        thread = Thread(ParameterizedThreadStart(self._run_approximate_delays_thread))
        thread.SetApartmentState(ApartmentState.STA)
        thread.Start(self)

    def _run_approximate_delays_thread(self, form):
        """Background thread: measure frame rate then compute approximate line delays."""
        try:
            camera = form._sharpcap.SelectedCamera
            if camera is None:
                form.SafeInvoke(lambda: MessageBox.Show(
                    "Camera disconnected.",
                    "Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                ))
                return

            # Save current exposure and set to 1 ms
            try:
                original_exposure = camera.Controls.Exposure.ExposureMs
            except Exception:
                original_exposure = None
            measurements = []
            try:
                try:
                    camera.Controls.Exposure.ExposureMs = 1.0
                except Exception as ex:
                    form.SafeInvoke(lambda: MessageBox.Show(
                        "Could not set exposure to 1 ms:\n" + str(ex),
                        "Warning",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Warning
                    ))

                # Wait 10 s for frame rate to stabilise
                for i in range(10, 0, -1):
                    msg = "Waiting for camera to stabilise: {0}s...".format(i)
                    form.SafeInvoke(lambda m=msg: setattr(form.label_status, 'Text', m))
                    form.SafeInvoke(lambda: setattr(form.label_status, 'ForeColor', Color.Orange))
                    time.sleep(1)

                # Take 10 frame-rate measurements, one per second
                for i in range(1, 11):
                    msg = "Measuring frame rate: {0}/10...".format(i)
                    form.SafeInvoke(lambda m=msg: setattr(form.label_status, 'Text', m))
                    try:
                        fps = float(camera.CurrentFrameRate)
                        if fps > 0:
                            measurements.append(fps)
                    except Exception:
                        pass
                    time.sleep(1)
            finally:
                # Always restore original exposure after measurements
                if original_exposure is not None:
                    try:
                        camera.Controls.Exposure.ExposureMs = original_exposure
                    except Exception:
                        pass

            if not measurements:
                form.SafeInvoke(lambda: MessageBox.Show(
                    "Could not obtain any frame rate readings from the camera.",
                    "Measurement Failed",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                ))
                return

            avg_fps = sum(measurements) / len(measurements)

            # Collect ROI height for line 0 delay calculation
            try:
                roi_height = int(camera.ROI.Height)
            except Exception:
                roi_height = 0

            shutter_type = form._active_shutter_type or 'Rolling'

            # Per line delay: time per frame divided by number of lines (negative = rolling shutter)
            if roi_height > 0:
                per_line_delay = -(1.0 / avg_fps) / roi_height * 1000.0
            else:
                per_line_delay = 0.0

            # Global shutter: all lines expose simultaneously — slope is zero
            if shutter_type == 'Global':
                per_line_delay = 0.0

            result_text = (
                "Frame rate measurements: " + ", ".join("{0:.2f}".format(f) for f in measurements) + "\r\n"
                "Average frame rate: {0:.3f} fps\r\n"
                "Per line delay: {1:.6f} ms/line\r\n"
                "ROI height: {2} lines\r\n"
                "Shutter type: {3}\r\n"
            ).format(avg_fps, per_line_delay, roi_height, shutter_type)
            form.SafeInvoke(lambda: setattr(form.textbox_results, 'Text', result_text))
            form.SafeInvoke(lambda: setattr(form.label_status, 'Text', 'Enter minimum delay...'))

            # Prompt for minimum delay on UI thread
            min_delay_holder = [None]
            def ask_min_delay():
                hint = (
                    "2 ms is reasonable for a small ROI (< 1000\u00d71000) "
                    "with a mono planetary camera."
                )
                dlg = _MinDelayDialog(hint)
                dlg.StartPosition = FormStartPosition.CenterParent
                if dlg.ShowDialog(form) == DialogResult.OK:
                    min_delay_holder[0] = dlg.min_delay_ms
            form.SafeInvoke(ask_min_delay)

            min_delay = min_delay_holder[0]
            if min_delay is None:
                form.SafeInvoke(lambda: setattr(form.label_status, 'Text', 'Cancelled'))
                form.SafeInvoke(lambda: setattr(form.label_status, 'ForeColor', Color.Gray))
                return

            # For rolling shutter: line_0_delay accounts for the full-frame readout time.
            # For global shutter: all lines expose simultaneously; the fixed delay is one
            # full frame period (1/fps in ms) plus the user-entered additional hardware delay.
            if shutter_type == 'Global':
                line_0_delay = (1000.0 / avg_fps) + min_delay
            else:
                line_0_delay = min_delay + roi_height * (-1.0) * per_line_delay

            if shutter_type == 'Global':
                description = 'Approximate (Global): fixed delay {0:.3f} ms (avg {1:.2f} fps, {2} samples)'.format(
                    line_0_delay, avg_fps, len(measurements))
            else:
                description = (
                    'Approximate: {0:.6f} ms/line, Offset: {1:.3f} ms '
                    '(avg {2:.2f} fps, {3} samples)'
                ).format(per_line_delay, line_0_delay, avg_fps, len(measurements))

            # Build a synthetic fit_result matching the existing schema
            fit_result = {
                'slope': per_line_delay,
                'intercept': line_0_delay,
                'r_squared': None,
                'n_measurements': len(measurements),
                'shutter_type': shutter_type,
                'measurement_method': 'FPS',
                'description': description,
            }

            capture_settings = form._collect_calibration_settings(camera)
            capture_settings['shutter_type'] = shutter_type
            capture_settings['measurement_method'] = 'FPS'

            form._calib_fit_result = fit_result
            form._calib_capture_settings = capture_settings
            form._calib_saved = False

            summary = result_text + (
                "Min delay entered: {0:.3f} ms\r\n"
                "Line 0 delay: {1:.3f} ms\r\n"
            ).format(min_delay, line_0_delay)
            form.SafeInvoke(lambda: setattr(form.textbox_results, 'Text', summary))
            form.SafeInvoke(lambda: setattr(form.label_status, 'Text', 'Approximate delays ready'))
            form.SafeInvoke(lambda: setattr(form.label_status, 'ForeColor', Color.Green))
            if hasattr(form, 'button_save_calibration'):
                form.SafeInvoke(lambda: setattr(form.button_save_calibration, 'Enabled', True))

        except Exception as ex:
            err = str(ex)
            form.SafeInvoke(lambda: setattr(form.label_status, 'Text', 'Error'))
            form.SafeInvoke(lambda: setattr(form.label_status, 'ForeColor', Color.Red))
            form.SafeInvoke(lambda: MessageBox.Show(
                "Approximate delays failed:\n" + err,
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            ))
        finally:
            form.SafeInvoke(lambda: setattr(form.button_approx_delays, 'Enabled', True))
            form.SafeInvoke(lambda: setattr(form.button_start, 'Enabled', True))

    def save_calibration_click(self, sender, event):
        """Open the Save Result to Camera dialog."""
        if self._calib_fit_result is None:
            MessageBox.Show(
                "No calibration result to save.\n\nRun a calibration first.",
                "No Result",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            return
        dlg = SaveCalibrationDialog(self._calib_fit_result, self._calib_capture_settings,
                                    config=self._config)
        dlg.StartPosition = FormStartPosition.CenterParent
        if dlg.ShowDialog(self) == DialogResult.OK:
            self._calib_saved = True
            MessageBox.Show(
                "Calibration result saved successfully.",
                "Saved",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )

    # === LONG TERM TIMING STABILITY METHODS ===
    
    def on_stab_invert_changed(self, sender, event):
        """Handle stability invert checkbox change - show warning when enabled"""
        if self.checkbox_stab_invert.Checked:
            # Show warning message
            result = MessageBox.Show(
                "Invert can be used for an LED that is ON for 900 ms and OFF for 100 ms. "
                "The built in LED on an Arduino module does this, as do some GPS receivers. "
                "It is better to use a proper GPS flasher, but acceptable calibration is "
                "possible with an inverted flash.",
                "Inverted PPS Signal Warning",
                MessageBoxButtons.OKCancel,
                MessageBoxIcon.Warning
            )
            
            # If user cancels, uncheck the box
            if result == DialogResult.Cancel:
                self.checkbox_stab_invert.Checked = False
    
    def start_stability_test(self, sender, event):
        """Start long-term timing stability test"""
        # Check camera connection
        if self._sharpcap is None or self._sharpcap.SelectedCamera is None:
            MessageBox.Show(
                "No camera is connected.\n\nPlease connect a camera before running the stability test.",
                "Camera Connection Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            return
        
        # Validate test duration format
        test_duration_str = self.textbox_test_duration.Text.strip()
        try:
            parts = test_duration_str.split(':')
            if len(parts) != 2:
                raise ValueError("Invalid format")
            hours = int(parts[0])
            minutes = int(parts[1])
            if hours < 0 or minutes < 0 or minutes >= 60:
                raise ValueError("Invalid time values")
        except:
            MessageBox.Show(
                "Invalid Test Duration format.\n\nPlease use HH:MM format (e.g., 01:30 for 1 hour 30 minutes).",
                "Input Validation Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            return
        
        # Disable start button, enable stop
        self.button_stab_start.Enabled = False
        self.button_stab_stop.Enabled = True
        
        # Start test in background thread
        import threading
        test_thread = threading.Thread(target=self.run_stability_test_thread)
        test_thread.daemon = True
        test_thread.start()
    
    def stop_stability_test(self, sender, event):
        """Stop the stability test"""
        try:
            self.stop_requested = True
            self.SafeInvoke(lambda: setattr(self.label_stab_status, 'Text', 'Stopping...'))
        except Exception as ex:
            print("Error in stop_stability_test: " + str(ex))
    
    def run_stability_test_thread(self):
        """Background thread for long-term stability testing"""
        # Declare accumulators before try so finally can always reference them
        all_delays = []
        all_timestamps = []
        start_time = datetime.utcnow()
        camera_settings = {}

        try:
            camera = self._sharpcap.SelectedCamera if self._sharpcap else None
            if camera is None:
                self.SafeInvoke(lambda: MessageBox.Show(
                    "Camera disconnected during test.",
                    "Error",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Error
                ))
                return

            # Collect camera settings while camera is definitely available
            camera_settings = self._get_camera_settings(camera)

            # Get test parameters
            capture_duration = float(self.textbox_stab_duration.Text)
            flash_ms = float(self.textbox_stab_flash.Text)
            test_duration_str = self.textbox_test_duration.Text.strip()
            parts = test_duration_str.split(':')
            test_duration_seconds = int(parts[0]) * 3600 + int(parts[1]) * 60
            do_invert = self.checkbox_stab_invert.Checked

            self.stop_requested = False

            elapsed_time = 0
            cycle_count = 0
            
            self.SafeInvoke(lambda: setattr(self.label_stab_status, 'Text', 
                'Starting stability test...'))
            
            while elapsed_time < test_duration_seconds and not self.stop_requested:
                cycle_count += 1
                remaining_time = test_duration_seconds - elapsed_time
                remaining_str = "{0:02d}:{1:02d}:{2:02d}".format(
                    int(remaining_time // 3600),
                    int((remaining_time % 3600) // 60),
                    int(remaining_time % 60)
                )
                
                self.SafeInvoke(lambda rs=remaining_str: setattr(self.label_stab_status, 'Text',
                    'Cycle {0} - Remaining: {1}'.format(cycle_count, rs)))
                
                # Perform one capture cycle (returns list of (delay, pps_time) tuples)
                cycle_results = self.do_stability_capture_cycle(
                    camera, capture_duration, flash_ms, do_invert)
                
                if cycle_results:
                    # Add delays and their actual UTC timestamps
                    for delay, pps_time in cycle_results:
                        all_delays.append(delay)
                        all_timestamps.append(pps_time)
                    
                    # Update plots and statistics
                    self.update_stability_display(all_delays, all_timestamps, start_time)
                
                # Update elapsed time
                elapsed_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Test complete
            self.SafeInvoke(lambda: setattr(self.label_stab_status, 'Text',
                'Test complete - {0} flashes recorded'.format(len(all_delays))))
            
        except Exception as ex:
            error_msg = "Stability test error: " + str(ex)
            print(error_msg)
            import traceback
            traceback.print_exc()
            self.SafeInvoke(lambda msg=error_msg: setattr(self.label_stab_status, 'Text', msg))
        
        finally:
            # Re-enable start button, disable stop
            self.SafeInvoke(lambda: setattr(self.button_stab_start, 'Enabled', True))
            self.SafeInvoke(lambda: setattr(self.button_stab_stop, 'Enabled', False))

            # Store results and trigger save (even if test was stopped mid-run)
            if all_delays:
                self._stab_run_start = start_time
                self._stab_delays = all_delays[:]
                self._stab_timestamps = all_timestamps[:]
                self._stab_camera_settings = camera_settings
                # _stab_stats_text is already updated live by update_stability_display
                self.SafeInvoke(lambda: setattr(self.button_stab_save, 'Enabled', True))

                # Auto-save to disk
                self.save_stability_results(
                    start_time, camera_settings, all_delays, all_timestamps,
                    self._stab_stats_text,
                )
    
    def do_stability_capture_cycle(self, camera, duration, flash_ms, do_invert):
        """Perform one capture cycle and return valid flash delays with timestamps
        
        Returns:
            List of (time_offset, pps_actual_time) tuples for valid GPS flashes
        """
        try:
            # Get camera parameters
            roi = camera.ROI
            exposure_ms = camera.Controls.Exposure.ExposureMs
            
            # Setup single aperture in middle of frame
            self.capture_handler = FrameCaptureHandler()
            frame_width = roi.Width
            frame_height = roi.Height
            
            print("Stability test parameters:")
            print("  Exposure: {0} ms".format(exposure_ms))
            print("  Frame dimensions: {0}x{1}".format(frame_width, frame_height))
            
            # Single aperture at vertical center
            aperture_size = 10
            y_center = frame_height // 2
            self.capture_handler.setup_single_aperture(frame_width, frame_height, y_center, aperture_size)
            
            # Store exposure for timestamp conversion in frame handler (CRITICAL!)
            # Without this, framehandler defaults to 50ms which causes wrong mid-frame timestamps
            self.capture_handler.exposure_ms = exposure_ms
            
            # Start capture
            self.capture_handler.start_capture(camera)
            time.sleep(0.5)
            
            # Wait for capture duration
            time.sleep(duration)
            
            # Stop capture
            self.capture_handler.stop_capture(camera)
            
            # Apply inversion if requested
            if do_invert:
                self.capture_handler.measurements = invert_measurements(
                    self.capture_handler.measurements,
                    auto_detect_max=True
                )
            
            # Process the data
            measurements = self.capture_handler.measurements[y_center]
            timestamps = self.capture_handler.timestamps
            frame_numbers = self.capture_handler.frame_numbers
            
            if len(measurements) == 0:
                return []
            
            # Create tangra object
            tangra_obj = create_tangra_object(
                measurements, timestamps, frame_numbers,
                y_center, 'stability_aperture', exposure_ms
            )
            tangra_obj['frame_height'] = frame_height
            
            # Analyze GPS flashes
            lcv = analyse_gps_flash_iron(
                tangra_obj, col='signal_1',
                exposure_ms=exposure_ms,
                flash_ms=flash_ms,
                background=None
            )
            
            # Calculate delays for each valid flash
            results = []
            peak_numbers = set([row['peak_no'] for row in lcv if row['peak_no'] > 0])
            
            for peak_no in peak_numbers:
                result = calculate_delays_iron(
                    lcv, peak_no, exposure_ms, flash_ms,
                    y_center, frame_height
                )
                
                if result:
                    time_offset = result['time_offset']
                    n_frames = result['n_frames']
                    pps_actual_time = result['pps_actual_time']
                    frac_flux_frame1 = result['frac_flux_frame1']
                    
                    # Debug output for first flash
                    if len(results) == 0:
                        print("  First flash: offset={0:.3f}ms, UTC={1}, n_frames={2}, flux_frac={3:.3f}".format(
                            time_offset, pps_actual_time.strftime("%H:%M:%S"), n_frames, frac_flux_frame1))
                    
                    # Quality filtering like line delay calibration:
                    # - Reject transition frames (too dim or too bright)
                    # - Reject if too few/many frames or extreme offset values
                    if (2 <= n_frames <= 4 and 
                        -80 < time_offset < 80 and
                        0.1 < frac_flux_frame1 < 0.9):
                        results.append((time_offset, pps_actual_time))
            
            return results
            
        except Exception as ex:
            print("Stability cycle error: " + str(ex))
            import traceback
            traceback.print_exc()
            return []
    
    def update_stability_display(self, all_delays, all_timestamps, start_time):
        """Update plots and statistics for stability test"""
        try:
            if len(all_delays) == 0:
                return
            
            n_total = len(all_delays)
            
            # Remove outliers (3% tails = 1.5% each end) for statistics
            sorted_delays = sorted(all_delays)
            if n_total >= 20:  # Only remove outliers if we have enough data
                trim_count = max(1, int(n_total * 0.015))  # 1.5% from each end
                filtered_delays = sorted_delays[trim_count:-trim_count]
                n_filtered = len(filtered_delays)
                print("Statistics: removed {0} outliers ({1:.1f}%), using {2} measurements".format(
                    2*trim_count, 100.0*2*trim_count/n_total, n_filtered))
            else:
                filtered_delays = sorted_delays
                n_filtered = n_total
            
            # Calculate statistics on filtered data
            n = len(filtered_delays)
            mean_delay = sum(filtered_delays) / n
            median_delay = filtered_delays[n // 2] if n % 2 == 1 else (filtered_delays[n//2-1] + filtered_delays[n//2]) / 2.0
            min_delay = filtered_delays[0]
            max_delay = filtered_delays[-1]
            
            # Calculate 95% CI using sample statistics with t-distribution
            # Use sample variance (divide by n-1) for unbiased estimator
            if n > 1:
                variance = sum((x - mean_delay) ** 2 for x in filtered_delays) / (n - 1)
                std_delay = math.sqrt(variance)
                
                # Use t-distribution for sample CI (more accurate for smaller samples)
                # For large n (>30), t ≈ 1.96, but we'll use a simple approximation
                # t-critical values: n=30->2.04, n=60->2.00, n=120->1.98, n=inf->1.96
                if n >= 120:
                    t_critical = 1.98
                elif n >= 60:
                    t_critical = 2.00
                elif n >= 30:
                    t_critical = 2.04
                else:
                    t_critical = 2.09  # Conservative for smaller samples
                
                # 95% CI for the mean
                ci_95_mean = t_critical * std_delay / math.sqrt(n)
                
                # 95% prediction interval for individual measurements (±2 std for ~95%)
                prediction_interval = 2.0 * std_delay
            else:
                std_delay = 0.0
                ci_95_mean = 0.0
                prediction_interval = 0.0
            
            # Update statistics text
            if n_filtered < n_total:
                stats_text = "Total Flashes: {0} ({1} after removing {2} outliers)\r\n".format(n_total, n_filtered, n_total - n_filtered)
            else:
                stats_text = "Total Flashes: {0}\r\n".format(n)
            stats_text += "Mean: {0:.3f} ms (95% CI: ± {1:.3f} ms)\r\n".format(mean_delay, ci_95_mean)
            stats_text += "Median: {0:.3f} ms\r\n".format(median_delay)
            stats_text += "Range: {0:.3f} to {1:.3f} ms\r\n".format(min_delay, max_delay)
            stats_text += "Std Dev: {0:.3f} ms (95% of data within ± {1:.3f} ms)".format(std_delay, prediction_interval)
            
            self._stab_stats_text = stats_text  # cache for auto-save
            self.SafeInvoke(lambda txt=stats_text: setattr(self.textbox_stab_stats, 'Text', txt))
            
            # Create time series plot - show ALL measurements
            timeseries_plot = self.create_timeseries_plot(all_delays, all_timestamps, start_time)
            self.SafeInvoke(lambda p=timeseries_plot: self.set_and_refresh_plot(self.plot_stab_timeseries, p))
            
            # Create histogram - use filtered data (outliers removed)
            histogram_plot = self.create_histogram_plot(filtered_delays, mean_delay, ci_95_mean)
            self.SafeInvoke(lambda p=histogram_plot: self.set_and_refresh_plot(self.plot_stab_histogram, p))
            
        except Exception as ex:
            print("Error updating stability display: " + str(ex))
            import traceback
            traceback.print_exc()
    
    def create_timeseries_plot(self, delays, timestamps, start_time):
        """Create time series plot of GPS flash delays"""
        plot_model = OxyPlot.PlotModel()
        plot_model.Title = "GPS Flash Timing Delays Over Time"
        
        # Create scatter series
        scatter_series = OxyPlot.Series.ScatterSeries()
        scatter_series.MarkerType = OxyPlot.MarkerType.Circle
        scatter_series.MarkerSize = 3
        scatter_series.MarkerFill = OxyPlot.OxyColors.Blue
        
        # Use elapsed seconds from test start based on actual PPS time
        if timestamps:
            for i, (delay, timestamp) in enumerate(zip(delays, timestamps)):
                elapsed_seconds = (timestamp - start_time).total_seconds()
                scatter_series.Points.Add(OxyPlot.Series.ScatterPoint(elapsed_seconds, delay))
        
        plot_model.Series.Add(scatter_series)
        
        # Configure axes
        x_axis = OxyPlot.Axes.LinearAxis()
        x_axis.Position = OxyPlot.Axes.AxisPosition.Bottom
        x_axis.Title = 'Elapsed Time (seconds)'
        plot_model.Axes.Add(x_axis)
        
        y_axis = OxyPlot.Axes.LinearAxis()
        y_axis.Position = OxyPlot.Axes.AxisPosition.Left
        y_axis.Title = 'Time Offset (ms)'
        
        # Make Y-axis range 3x larger than data range for better visibility
        if delays:
            min_delay = min(delays)
            max_delay = max(delays)
            data_range = max_delay - min_delay
            if data_range > 0:
                center = (min_delay + max_delay) / 2.0
                expanded_range = data_range * 1.5  # 3x total (1.5x padding on each side)
                y_axis.Minimum = center - expanded_range
                y_axis.Maximum = center + expanded_range
            else:
                # Single value - show ±5ms range
                y_axis.Minimum = min_delay - 5.0
                y_axis.Maximum = max_delay + 5.0
        
        plot_model.Axes.Add(y_axis)
        
        return plot_model
    
    def create_histogram_plot(self, delays, mean_delay, ci_95_mean):
        """Create histogram of GPS flash delays with annotations"""
        plot_model = OxyPlot.PlotModel()
        plot_model.Title = "Distribution of GPS Flash Timing Delays (outliers removed)"
        
        # Create histogram with 1 ms bins
        bin_width = 1.0
        min_val = min(delays)
        max_val = max(delays)
        
        # Determine bin edges
        bin_start = math.floor(min_val / bin_width) * bin_width
        bin_end = math.ceil(max_val / bin_width) * bin_width
        num_bins = int((bin_end - bin_start) / bin_width)
        
        # Ensure at least 1 bin for single-value datasets
        if num_bins == 0:
            num_bins = 1
            bin_end = bin_start + bin_width
        
        # Count frequencies
        bins = [0] * num_bins
        for delay in delays:
            bin_index = int((delay - bin_start) / bin_width)
            if 0 <= bin_index < num_bins:
                bins[bin_index] += 1
        
        # Create histogram using RectangleAnnotations (ColumnSeries not available)
        max_count = max(bins) if bins else 1
        
        for i, count in enumerate(bins):
            if count > 0:  # Only draw bars with data
                bin_left = bin_start + i * bin_width
                bin_right = bin_start + (i + 1) * bin_width
                
                # Create filled rectangle for each bar
                rect = OxyPlot.Annotations.RectangleAnnotation()
                rect.MinimumX = bin_left
                rect.MaximumX = bin_right
                rect.MinimumY = 0
                rect.MaximumY = count
                rect.Fill = OxyPlot.OxyColors.SteelBlue
                rect.Stroke = OxyPlot.OxyColors.Black
                rect.StrokeThickness = 1
                
                plot_model.Annotations.Add(rect)
        
        print("Histogram: {0} bins, {1} total points, max count={2}".format(num_bins, len(delays), max_count))
        
        # Add mean line annotation
        mean_line = OxyPlot.Annotations.LineAnnotation()
        mean_line.Type = OxyPlot.Annotations.LineAnnotationType.Vertical
        mean_line.X = mean_delay
        mean_line.Color = OxyPlot.OxyColors.Red
        mean_line.LineStyle = OxyPlot.LineStyle.Dash
        mean_line.Text = "Mean: {0:.2f} ms".format(mean_delay)
        plot_model.Annotations.Add(mean_line)
        
        # Configure axes — explicit ranges derived from current data so they
        # always cover the full histogram regardless of when the chart is refreshed.
        x_axis = OxyPlot.Axes.LinearAxis()
        x_axis.Position = OxyPlot.Axes.AxisPosition.Bottom
        x_axis.Title = 'Time Offset (ms)'
        x_axis.Minimum = bin_start - bin_width * 0.5   # half-bin margin left of first bar
        x_axis.Maximum = bin_end   + bin_width * 0.5   # half-bin margin right of last bar
        plot_model.Axes.Add(x_axis)

        y_axis = OxyPlot.Axes.LinearAxis()
        y_axis.Position = OxyPlot.Axes.AxisPosition.Left
        y_axis.Title = 'Frequency'
        y_axis.Minimum = 0
        y_axis.Maximum = max_count * 1.15 + 1   # 15% headroom above tallest bar
        plot_model.Axes.Add(y_axis)
        
        # Add subtitle with 95% CI for the mean
        plot_model.Subtitle = "95% CI (mean): ± {0:.3f} ms".format(ci_95_mean)
        
        return plot_model


    # === STABILITY TEST SAVE METHODS ===

    def _get_stability_data_folder(self):
        """Return the base folder for stability test outputs (gps-timing-analysis/data/stability-test)"""
        parent = os.path.dirname(script_dir)  # one level above python/
        return os.path.join(parent, 'data', 'stability-test')

    def _get_camera_settings(self, camera):
        """Collect camera settings from the SharpCap camera object into a dict.

        Uses broad exception handling because available controls differ by camera model.
        """
        settings = {}

        def try_get(key, func):
            try:
                val = func()
                settings[key] = val if val is not None else 'N/A'
            except Exception:
                settings[key] = 'N/A'

        try_get('Camera', lambda: str(camera.DeviceName))

        try:
            roi = camera.ROI
            settings['Pan (ROI X)'] = int(roi.X)
            settings['Tilt (ROI Y)'] = int(roi.Y)
            settings['Frame Width (px)'] = int(roi.Width)
            settings['Frame Height (px)'] = int(roi.Height)
        except Exception:
            for k in ('Pan (ROI X)', 'Tilt (ROI Y)', 'Frame Width (px)', 'Frame Height (px)'):
                settings[k] = 'N/A'

        try_get('Exposure (ms)', lambda: float(camera.Controls.Exposure.ExposureMs))

        try:
            ctrl = camera.Controls.FindByName("Gain")
            settings['Gain'] = ctrl.Value if ctrl else 'N/A'
        except Exception:
            settings['Gain'] = 'N/A'

        try:
            ctrl = camera.Controls.FindByName("Binning")
            settings['Binning'] = ctrl.Value if ctrl else 'N/A'
        except Exception:
            settings['Binning'] = 'N/A'

        for name in ('ColourSpace', 'ColorSpace', 'Colour Space', 'Color Space'):
            try:
                ctrl = camera.Controls.FindByName(name)
                if ctrl is not None:
                    settings['Colour Space'] = ctrl.Value
                    break
            except Exception:
                pass
        if 'Colour Space' not in settings:
            settings['Colour Space'] = 'N/A'

        for name in ('OutputFormat', 'FileFormat', 'Output Format', 'File Format'):
            try:
                ctrl = camera.Controls.FindByName(name)
                if ctrl is not None:
                    settings['File Format'] = ctrl.Value
                    break
            except Exception:
                pass
        if 'File Format' not in settings:
            settings['File Format'] = 'N/A'

        for name in ('USBBandwidth', 'USB Bandwidth', 'USBTraffic', 'USB Traffic', 'USB Speed',
                     'USBSpeed', 'USBFS'):
            try:
                ctrl = camera.Controls.FindByName(name)
                if ctrl is not None:
                    settings['USB Bandwidth'] = ctrl.Value
                    break
            except Exception:
                pass
        if 'USB Bandwidth' not in settings:
            settings['USB Bandwidth'] = 'N/A'

        return settings

    def _collect_calibration_settings(self, camera):
        """Collect camera settings for calibration storage (compact field names for config).

        Returns a dict with keys matching the line_delay_calibrations schema.
        Uses broad exception handling because available controls differ by camera model.
        """
        settings = {}

        def try_get(func, default=''):
            try:
                val = func()
                return val if val is not None else default
            except Exception:
                return default

        settings['camera_name'] = try_get(lambda: str(camera.DeviceName))

        try:
            import System
            settings['pc_name'] = str(System.Environment.MachineName)
        except Exception:
            settings['pc_name'] = ''

        try:
            roi = camera.ROI
            settings['camera_area'] = '{0}x{1}'.format(roi.Width, roi.Height)
            settings['tilt'] = int(roi.Y)
            settings['pan'] = int(roi.X)
        except Exception:
            settings['camera_area'] = ''
            settings['tilt'] = ''
            settings['pan'] = ''

        settings['exposure_ms'] = try_get(
            lambda: round(float(camera.Controls.Exposure.ExposureMs), 3))

        try:
            ctrl = camera.Controls.FindByName('Gain')
            settings['gain'] = str(ctrl.Value) if ctrl else ''
        except Exception:
            settings['gain'] = ''

        try:
            ctrl = camera.Controls.FindByName('Binning')
            settings['binning'] = str(ctrl.Value) if ctrl else ''
        except Exception:
            settings['binning'] = ''

        for name in ('ColourSpace', 'ColorSpace', 'Colour Space', 'Color Space'):
            try:
                ctrl = camera.Controls.FindByName(name)
                if ctrl is not None:
                    settings['colour_space'] = str(ctrl.Value)
                    break
            except Exception:
                pass
        if 'colour_space' not in settings:
            settings['colour_space'] = ''

        for name in ('OutputFormat', 'FileFormat', 'Output Format', 'File Format'):
            try:
                ctrl = camera.Controls.FindByName(name)
                if ctrl is not None:
                    settings['file_format'] = str(ctrl.Value)
                    break
            except Exception:
                pass
        if 'file_format' not in settings:
            settings['file_format'] = ''

        return settings

    def _collect_calibration_settings_from_adv(self, adv_file_name, frame_width,
                                                frame_height, exposure_ms):
        """Collect calibration settings when working from an ADV file.

        Fields not available in the ADV header (tilt, pan, colour_space, gain)
        are left as empty strings so the user can fill them in the save dialog.
        """
        settings = {}
        # Camera name: best-effort from ADV filename; user can correct in the save dialog
        settings['camera_name'] = os.path.splitext(adv_file_name)[0]

        try:
            import System
            settings['pc_name'] = str(System.Environment.MachineName)
        except Exception:
            settings['pc_name'] = ''

        settings['camera_area'] = '{0}x{1}'.format(frame_width, frame_height)
        settings['binning'] = '1'   # ADV frames are always actual pixel dimensions
        settings['tilt'] = ''       # Not stored in ADV header
        settings['pan'] = ''        # Not stored in ADV header
        settings['colour_space'] = ''
        settings['file_format'] = 'ADV'
        settings['exposure_ms'] = round(float(exposure_ms), 3) if exposure_ms else ''
        settings['gain'] = ''
        return settings

    def _compute_histogram_bins(self, delays, bin_width=0.25):
        """Compute a histogram with the given bin width.

        Bins are aligned so edges are multiples of bin_width.
        Returns list of (bin_center, count) tuples for every bin from min to max.
        """
        if not delays:
            return []
        min_val = min(delays)
        max_val = max(delays)
        bin_start = math.floor(min_val / bin_width) * bin_width
        bin_end   = math.ceil(max_val / bin_width) * bin_width
        num_bins  = int(round((bin_end - bin_start) / bin_width))
        if num_bins == 0:
            num_bins = 1
        counts = [0] * num_bins
        for d in delays:
            idx = int((d - bin_start) / bin_width)
            if idx < 0:
                idx = 0
            elif idx >= num_bins:
                idx = num_bins - 1
            counts[idx] += 1
        result = []
        for i in range(num_bins):
            center = round(bin_start + (i + 0.5) * bin_width, 6)
            result.append((center, counts[i]))
        return result

    def _save_chart_png_sync(self, plot_view, filepath):
        """Render a PlotView to a PNG file.  Must be called on the UI thread."""
        try:
            width  = plot_view.Width  if plot_view.Width  > 0 else 660
            height = plot_view.Height if plot_view.Height > 0 else 250
            bmp = Bitmap(width, height)
            plot_view.DrawToBitmap(bmp, Rectangle(0, 0, width, height))
            bmp.Save(filepath, System.Drawing.Imaging.ImageFormat.Png)
            bmp.Dispose()
            print("Saved chart PNG: " + filepath)
        except Exception as ex:
            print("PNG save error ({0}): {1}".format(filepath, str(ex)))

    def _save_stability_excel(self, filepath, run_start_time, camera_settings,
                              stats_text, all_delays, all_timestamps):
        """Write stability test results to a 3-sheet XLSX file."""

        # --- Sheet 1: Summary ---
        summary_rows = [
            ['GPS LED Line Delay Calibration - Long Term Timing Stability Test'],
            [],
            ['Run Started (UTC)', run_start_time.strftime('%Y-%m-%d %H:%M:%S')],
            ['Run Ended   (UTC)', datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')],
            ['Total Flashes Recorded', len(all_delays)],
            [],
            ['CAMERA SETTINGS'],
            ['Setting', 'Value'],
        ]
        for key, value in camera_settings.items():
            summary_rows.append([key, value])
        summary_rows.append([])
        summary_rows.append(['TEST STATISTICS'])
        for line in stats_text.replace('\r\n', '\n').replace('\r', '\n').split('\n'):
            line = line.strip()
            if line:
                summary_rows.append([line])

        # --- Sheet 2: Histogram (0.25 ms bins, centered on mid-bin) ---
        bin_data = self._compute_histogram_bins(all_delays, bin_width=0.25)
        histogram_rows = [['Bin Center (ms)', 'Count']]
        for center, count in bin_data:
            histogram_rows.append([center, count])

        # --- Sheet 3: Time Series ---
        ts_rows = [['Measurement #', 'UTC Timestamp', 'Measured Delay (ms)']]
        for i, (delay, ts) in enumerate(zip(all_delays, all_timestamps), start=1):
            ts_str = ts.strftime('%Y-%m-%d %H:%M:%S.%f') if ts else ''
            ts_rows.append([i, ts_str, round(delay, 6)])

        writer = SimpleXlsxWriter()
        writer.save(filepath, [
            ('Summary',     summary_rows),
            ('Histogram',   histogram_rows),
            ('Time Series', ts_rows),
        ])
        print("Saved Excel: " + filepath)

    def save_stability_results(self, run_start_time, camera_settings,
                               all_delays, all_timestamps, stats_text):
        """Save PNGs and Excel for a completed stability test run.

        Creates a timestamped sub-folder under gps-timing-analysis/data/stability-test/.
        Returns the folder path on success, or None on failure.
        """
        try:
            base_folder = self._get_stability_data_folder()
            run_folder = os.path.join(base_folder, run_start_time.strftime('%Y%m%d_%H%M%S'))
            if not os.path.exists(run_folder):
                os.makedirs(run_folder)

            print("Saving stability results to: " + run_folder)

            # Chart PNGs must be rendered on the UI thread
            ts_png   = os.path.join(run_folder, 'timeseries.png')
            hist_png = os.path.join(run_folder, 'histogram.png')
            self.SafeInvoke(lambda p=self.plot_stab_timeseries, f=ts_png:
                            self._save_chart_png_sync(p, f))
            self.SafeInvoke(lambda p=self.plot_stab_histogram, f=hist_png:
                            self._save_chart_png_sync(p, f))

            # Excel workbook
            excel_path = os.path.join(run_folder, 'stability_results.xlsx')
            self._save_stability_excel(excel_path, run_start_time, camera_settings,
                                       stats_text, all_delays, all_timestamps)

            msg = 'Saved to: ' + run_folder
            print(msg)
            self._stab_last_save_folder = run_folder
            self.SafeInvoke(lambda m=msg: setattr(self.label_stab_saved_path, 'Text', m))
            self.SafeInvoke(lambda: setattr(self.button_stab_open_folder, 'Enabled', True))
            return run_folder

        except Exception as ex:
            err = 'Save error: ' + str(ex)
            print(err)
            import traceback
            traceback.print_exc()
            self.SafeInvoke(lambda e=err: setattr(self.label_stab_saved_path, 'Text', e))
            return None

    def save_stability_results_click(self, sender, event):
        """Handle Save Results button click — re-saves the most recent run."""
        if not self._stab_delays:
            MessageBox.Show(
                "No stability test results to save.\n\nRun a stability test first.",
                "No Results",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            return
        import threading
        t = threading.Thread(target=lambda: self.save_stability_results(
            self._stab_run_start,
            self._stab_camera_settings,
            self._stab_delays[:],
            self._stab_timestamps[:],
            self._stab_stats_text,
        ))
        t.daemon = True
        t.start()

    def open_save_folder_click(self, sender, event):
        """Open the last stability test output folder in Windows Explorer."""
        folder = self._stab_last_save_folder
        if not folder or not os.path.exists(folder):
            MessageBox.Show(
                "Output folder not found.\n\n" + (folder or '(none)'),
                "Folder Not Found",
                MessageBoxButtons.OK,
                MessageBoxIcon.Warning
            )
            return
        try:
            import System.Diagnostics
            System.Diagnostics.Process.Start("explorer.exe", folder)
        except Exception as ex:
            MessageBox.Show(
                "Could not open folder:\n" + str(ex),
                "Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )


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
