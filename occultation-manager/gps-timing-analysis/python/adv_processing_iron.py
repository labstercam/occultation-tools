# IronPython-compatible ADV file processing for GPS timing analysis
# Designed for SharpCap/IronPython 3.4 environment
# Michael Camilleri & GitHub Copilot
# February 2026
#
# This version uses .NET AdvLib for ADV file reading and replaces
# NumPy, Pandas, SciPy, and Astropy with pure Python/.NET code
#
# Requires: AdvLib.dll and supporting DLLs (AdvLib.Core32.dll, AdvLib.Core64.dll)
# Place DLLs in: gps-timing-analysis/lib/ directory

import clr
import sys

# Add reference to AdvLib .NET assembly
# DLLs should be in ../lib/ directory relative to this script
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(os.path.dirname(script_dir), 'lib')

# Add lib directory to path for DLL loading
if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# Load AdvLib with full path
try:
    advlib_path = os.path.join(lib_dir, 'AdvLib.dll')
    clr.AddReferenceToFileAndPath(advlib_path)
    from Adv import AdvFile2, AdvError, AdvFrameInfo
    import System  # For reflection calls
    print("AdvLib loaded successfully from: " + lib_dir)
except Exception as e:
    print("ERROR: Could not load AdvLib: " + str(e))
    print("Please ensure the following DLLs are in: " + lib_dir)
    print("  - AdvLib.dll")
    print("  - AdvLib.Core32.dll")
    print("  - AdvLib.Core64.dll")
    print("\nDownload from: http://www.hristopavlov.net/adv/AdvLib.NET.zip")

from datetime import datetime, timedelta
from pathlib import Path
import random

# ============================================================================
# Helper Functions (NumPy/SciPy/Pandas replacements)
# ============================================================================

def calculate_mean(values):
    """Calculate mean of a list of numbers"""
    if not values:
        return 0.0
    return sum(values) / float(len(values))

def calculate_median(values):
    """Calculate median of a list of numbers"""
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    if n % 2 == 0:
        return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2.0
    else:
        return sorted_values[n//2]

def calculate_std(values):
    """Calculate standard deviation of a list of numbers"""
    if len(values) < 2:
        return 0.0
    mean = calculate_mean(values)
    variance = sum((x - mean) ** 2 for x in values) / float(len(values) - 1)
    return variance ** 0.5

def calculate_percentile(values, percentile):
    """
    Calculate percentile of a list of numbers (0-100).
    Uses linear interpolation between nearest ranks.
    """
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    k = (n - 1) * percentile / 100.0
    f = int(k)
    c = k - f
    if f + 1 < n:
        return sorted_values[f] * (1.0 - c) + sorted_values[f + 1] * c
    else:
        return sorted_values[f]

def trim_mean(values, proportiontocut=0.05):
    """
    Calculate trimmed mean (remove top/bottom proportion).
    Equivalent to scipy.stats.trim_mean
    """
    if not values:
        return 0.0
    sorted_values = sorted(values)
    n = len(sorted_values)
    cut_count = int(n * proportiontocut)
    if cut_count * 2 >= n:
        return calculate_mean(values)
    trimmed = sorted_values[cut_count:n-cut_count]
    return calculate_mean(trimmed)

def linear_regression_ransac(x_values, y_values, threshold=10.0, max_iterations=100):
    """
    RANSAC robust linear regression: y = mx + c
    Removes outliers beyond threshold distance from fitted line.
    
    Args:
        x_values: List of x coordinates
        y_values: List of y coordinates  
        threshold: Maximum distance for inlier (default 10.0)
        max_iterations: RANSAC iterations
    
    Returns:
        (slope, intercept, inliers_mask) where inliers_mask is list of bool
    """
    if len(x_values) != len(y_values) or len(x_values) < 2:
        return 0.0, 0.0, [True] * len(x_values)
    
    n = len(x_values)
    best_slope = 0.0
    best_intercept = 0.0
    best_inliers = [True] * n
    max_inlier_count = 0
    
    # RANSAC iterations
    iterations = min(max_iterations, n * (n-1) // 2)
    
    for iteration in range(iterations):
        # Sample 2 random points
        if n < 2:
            break
        indices = random.sample(range(n), 2)
        x1, y1 = x_values[indices[0]], y_values[indices[0]]
        x2, y2 = x_values[indices[1]], y_values[indices[1]]
        
        # Calculate line through these two points
        if abs(x2 - x1) < 1e-10:
            continue
        
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1
        
        # Count inliers
        inliers = []
        for i in range(n):
            predicted = slope * x_values[i] + intercept
            residual = abs(y_values[i] - predicted)
            inliers.append(residual < threshold)
        
        inlier_count = sum(inliers)
        
        # Keep best model
        if inlier_count > max_inlier_count:
            max_inlier_count = inlier_count
            best_inliers = inliers
            
            # Refit using all inliers (least squares)
            inlier_x = [x_values[i] for i in range(n) if inliers[i]]
            inlier_y = [y_values[i] for i in range(n) if inliers[i]]
            
            if len(inlier_x) >= 2:
                # Least squares fit
                x_mean = calculate_mean(inlier_x)
                y_mean = calculate_mean(inlier_y)
                
                numerator = sum((inlier_x[i] - x_mean) * (inlier_y[i] - y_mean) 
                               for i in range(len(inlier_x)))
                denominator = sum((inlier_x[i] - x_mean) ** 2 
                                 for i in range(len(inlier_x)))
                
                if denominator != 0:
                    best_slope = numerator / denominator
                    best_intercept = y_mean - best_slope * x_mean
    
    return best_slope, best_intercept, best_inliers

# ============================================================================
# ADV File Reading Functions (using .NET AdvLib)
# ============================================================================

def open_adv(file_path, file_name, verbose=False):
    """
    Open an ADV file using .NET AdvLib.
    
    Args:
        file_path: Directory path to the file
        file_name: Name of the ADV file
        verbose: If True, print file information
    
    Returns:
        AdvFile2 object (must call .Close() when done)
    
    Example:
        adv = open_adv("C:/Videos/", "gps_test.adv", verbose=True)
        # ... process file ...
        adv.Close()
    """
    try:
        full_path = str(Path(file_path) / file_name)
        adv_file = AdvFile2(full_path)
        
        if verbose:
            print('Opened ADV file: ' + full_path)
            print('  Frames: ' + str(adv_file.MainSteamInfo.FrameCount))
            print('  Size: ' + str(adv_file.Width) + ' x ' + str(adv_file.Height))
            print('  BPP: ' + str(adv_file.DataBpp))
        
        return adv_file
    
    except Exception as e:
        print('ERROR opening ADV file: ' + str(e))
        raise

def read_adv_frame(adv_file, frame_number):
    """
    Read a single frame from ADV file WITH timestamp information.
    
    Args:
        adv_file: AdvFile2 object from open_adv()
        frame_number: Frame number to read (0-indexed)
    
    Returns:
        tuple: (pixels, frame_info) where frame_info contains UTC timestamps
                Returns (pixels, None) if frameInfo not available
    
    Note:
        Uses AdvLib.GetFramePixels directly because AdvFrameInfo has internal constructor.
        IronPython handles .NET out parameters by returning them as additional return values.
    """
    from Adv import AdvLib
    
    try:
        # Call AdvLib.GetFramePixels directly - it creates AdvFrameInfo internally
        # Signature: GetFramePixels(streamId, frameNo, width, height, out frameInfo, out pixels)
        # IronPython returns: (errorCode, frameInfo, pixels)
        
        result = AdvLib.GetFramePixels(
            0,  # streamId (0 = main stream)
            frame_number,
            adv_file.Width,
            adv_file.Height
        )
        
        # IronPython should return tuple: (errorCode, frameInfo, pixels)
        if isinstance(result, tuple) and len(result) == 3:
            error_code, frame_info, pixels = result
            
            # Check error code
            if error_code == 0:  # S_OK
                return (pixels, frame_info)
            else:
                print('ERROR: AdvLib.GetFramePixels returned error code ' + str(error_code))
                return (None, None)
        else:
            # Unexpected return format
            print('WARNING: AdvLib.GetFramePixels returned unexpected format: ' + str(type(result)))
            return (None, None)
            
    except Exception as e:
        print('ERROR reading frame ' + str(frame_number) + ': ' + str(e))
        import traceback
        traceback.print_exc()
        
        # Try fallback: use AdvFile2's simple method (no frame_info)
        try:
            pixels = adv_file.GetMainFramePixels(frame_number)
            return (pixels, None)
        except:
            return (None, None)

def get_frame_timestamp(frame_info, exposure_ms=None):
    """
    Extract UTC mid-exposure timestamp from AdvFrameInfo.
    
    Args:
        frame_info: AdvFrameInfo object from read_adv_frame()
        exposure_ms: Exposure time in milliseconds (optional, for fallback)
    
    Returns:
        datetime: Mid-exposure timestamp (UTC)
    
    Note:
        .NET AdvLib provides these DateTime properties:
        - UtcMidExposureTime: Direct mid-exposure timestamp
        - UtcStartExposureTimeStamp: Start of exposure
        - UtcExposureMilliseconds: Exposure duration
        
        This is more accurate than ElapsedTicks from MainIndex.
    """
    if frame_info is None:
        return None
    
    try:
        # Check if UTC timestamp is available
        if hasattr(frame_info, 'HasUtcTimeStamp') and frame_info.HasUtcTimeStamp:
            # Try UtcMidExposureTime first (most direct)
            if hasattr(frame_info, 'UtcMidExposureTime'):
                net_dt = frame_info.UtcMidExposureTime
                return datetime(
                    net_dt.Year, net_dt.Month, net_dt.Day,
                    net_dt.Hour, net_dt.Minute, net_dt.Second,
                    net_dt.Millisecond * 1000  # Convert to microseconds
                )
            
            # Fallback: Calculate from start + exposure/2
            if hasattr(frame_info, 'UtcStartExposureTimeStamp'):
                net_dt = frame_info.UtcStartExposureTimeStamp
                timestamp = datetime(
                    net_dt.Year, net_dt.Month, net_dt.Day,
                    net_dt.Hour, net_dt.Minute, net_dt.Second,
                    net_dt.Millisecond * 1000
                )
                
                # Add half exposure to get mid-frame
                if hasattr(frame_info, 'UtcExposureMilliseconds'):
                    timestamp += timedelta(milliseconds=frame_info.UtcExposureMilliseconds / 2.0)
                elif exposure_ms:
                    timestamp += timedelta(milliseconds=exposure_ms / 2.0)
                
                return timestamp
        
        print('Warning: frame_info has no UTC timestamp')
        return None
        
    except Exception as e:
        print('ERROR extracting timestamp from frame_info: ' + str(e))
        import traceback
        traceback.print_exc()
        return None

def pixels_to_2d_list(pixels, width, height):
    """
    Convert flat .NET uint[] pixel array to 2D Python list.
    
    Args:
        pixels: .NET uint[] array from ADV file (length = width * height)
        width: Image width
        height: Image height
    
    Returns:
        2D list: image[row][col] with pixel values
    """
    image = []
    for y in range(height):
        row = []
        for x in range(width):
            row.append(int(pixels[y * width + x]))
        image.append(row)
    return image

def calculate_row_means_trimmed(image_2d, proportiontocut=0.05):
    """
    Calculate trimmed mean for each row of the image.
    Removes outliers (hot pixels, stars) for better background measurement.
    
    Args:
        image_2d: 2D list of pixel values [row][col]
        proportiontocut: Proportion to trim from each end (0.05 = 5%)
    
    Returns:
        List of row means (one value per row)
    """
    row_means = []
    for row in image_2d:
        if row:
            row_mean = trim_mean(row, proportiontocut)
            row_means.append(row_mean)
    return row_means

# ============================================================================
# GPS Flash Analysis Functions
# ============================================================================

def analyse_gps_flash(light_curve_data, exposure_ms=50, flash_ms=100, background=None):
    """
    Analyze a single light curve for GPS flashes and tag each peak.
    
    Args:
        light_curve_data: Dict with keys:
            - 'frameno': List of frame numbers
            - 'time_ut': List of datetime objects (timestamps)
            - 'signal': List of signal values (flux)
        exposure_ms: Nominal exposure time in ms
        flash_ms: GPS flash duration in ms (typically 100 ms)
        background: Background level (auto-calculated if None)
    
    Returns:
        Enhanced dict with original data plus:
            - 'peak_no': Peak sequence number for each frame (0 = background)
            - 'signal_flash': Flash signal with background removed
            - 'avg_background': Calculated average background level
    """
    signals = light_curve_data['signal']
    
    # Auto-calculate background if not provided
    if background is None:
        # Estimate percentage of frames that should be background
        # Based on exposure time vs flash duration and 1 PPS frequency
        background_percentile = 100.0 - (exposure_ms/flash_ms + 1.0)/(1000.0/flash_ms)*100.0
        background = calculate_percentile(signals, background_percentile)
    
    # Flag background frames
    background_flags = [1.0 if s <= background else 0.0 for s in signals]
    
    # Calculate average background level
    background_values = [signals[i] for i in range(len(signals)) if background_flags[i] == 1.0]
    avg_background = calculate_mean(background_values) if background_values else background
    
    # Extract flash signals (background subtracted, only for flash frames)
    signal_flash = []
    for i in range(len(signals)):
        if background_flags[i] == 0.0:  # Flash frame
            signal_flash.append(signals[i] - avg_background)
        else:  # Background frame
            signal_flash.append(0.0)
    
    # Label each flash peak with unique sequence number
    peaks = [1.0 if s > 0 else 0.0 for s in signal_flash]
    
    # Find transitions (edges of flashes)
    transitions = [0.0]
    for i in range(1, len(peaks)):
        transitions.append(abs(peaks[i] - peaks[i-1]))
    
    # Assign cumulative peak numbers
    peak_no = [0.0]
    cumsum = 0.0
    for i in range(1, len(transitions)):
        cumsum += transitions[i]
        peak_no.append(cumsum * peaks[i])
    
    # Return enhanced light curve
    result = dict(light_curve_data)  # Copy original data
    result['peak_no'] = peak_no
    result['signal_flash'] = signal_flash
    result['avg_background'] = avg_background
    
    return result

def calculate_delays(light_curve_data, peak_no, exposure_ms, flash_ms, y=0, y_lines=0):
    """
    Calculate time delay between frame timestamp and actual GPS PPS for one flash peak.
    
    This determines when the GPS flash actually occurred relative to the frame timestamp.
    
    Args:
        light_curve_data: Enhanced light curve dict from analyse_gps_flash()
        peak_no: Which peak number to analyze (from peak_no field)
        exposure_ms: Frame exposure time in ms
        flash_ms: GPS flash duration in ms
        y: Y position (sensor row number) for rolling shutter correction
        y_lines: Total lines in frame (0 or -1 for global shutter)
    
    Returns:
        Dict with timing analysis results:
            - 'time_offset': Timestamp error in ms (positive = timestamp late)
            - 'frac_flux_frame1': Fraction of flash in first frame
            - 'pps_actual_time': Calculated actual GPS PPS time
            - plus other diagnostic values
        
        Returns None if peak not found or insufficient data.
    """
    # Extract frames belonging to this peak
    peak_indices = [i for i in range(len(light_curve_data['peak_no'])) 
                   if light_curve_data['peak_no'][i] == peak_no]
    
    if not peak_indices:
        return None
    
    # Calculate frame time differences
    times = light_curve_data['time_ut']
    time_diffs = [exposure_ms]  # First frame has no previous
    for i in range(1, len(times)):
        diff_ms = (times[i] - times[i-1]).total_seconds() * 1000.0
        time_diffs.append(diff_ms)
    
    # Get first frame of this peak
    first_idx = peak_indices[0]
    
    # Total flux in entire flash and flux in first frame
    total_flux = sum(light_curve_data['signal_flash'][i] for i in peak_indices)
    flux1 = light_curve_data['signal_flash'][first_idx]
    
    if total_flux == 0:
        return None
    
    # Fraction of flash that occurred in first frame
    frac_flux_frame1 = flux1 / total_flux
    
    # How many ms of the 100ms flash were in first frame
    pps_ms_in_frame1 = frac_flux_frame1 * flash_ms
    
    # Calculate actual end time of first frame
    # Timestamps are mid-exposure, so add half exposure to get end
    rolling_shutter_offset = exposure_ms / 2.0
    
    frame1_mid = times[first_idx]
    frame1_end = frame1_mid + timedelta(milliseconds=rolling_shutter_offset)
    
    # Find actual GPS PPS time (round to nearest second)
    # GPS PPS occurs at exact second boundaries
    total_seconds = (frame1_end - datetime(1900, 1, 1)).total_seconds()
    pps_seconds = round(total_seconds)
    pps_actual = datetime(1900, 1, 1) + timedelta(seconds=pps_seconds)
    
    # Actual end time of first frame relative to PPS
    frame1_end_actual = pps_actual + timedelta(milliseconds=pps_ms_in_frame1)
    
    # Time offset: difference between timestamp and actual
    # Positive means timestamp is LATE (later than actual)
    time_offset = (frame1_end - frame1_end_actual).total_seconds() * 1000.0
    
    return {
        'peak_no': int(peak_no),
        'n_frames': len(peak_indices),
        'y': y,
        'y_lines': y_lines,
        'y_time_offset': rolling_shutter_offset,
        'total_flux': total_flux,
        'flux1': flux1,
        'frac_flux_frame1': frac_flux_frame1,
        'pps_ms_in_frame1': pps_ms_in_frame1,
        'frame1_mid': frame1_mid,
        'frame1_end': frame1_end,
        'pps_actual_time': pps_actual,
        'frame1_end_actual': frame1_end_actual,
        'time_offset': time_offset,
        'frame1_timestamp_ms': time_diffs[first_idx]
    }

# ============================================================================
# Main ADV Processing Function
# ============================================================================

def process_adv_for_gps_timing(file_path, file_name, 
                                frame_start=0, frame_end=None,
                                agg_rows=10, 
                                exposure_ms=None,
                                flash_ms=100,
                                ignore_header_lines=0,
                                ignore_footer_lines=0,
                                quality_filter=True,
                                min_frac_flux=0.1,
                                max_frac_flux=0.9,
                                verbose=False):
    """
    Process ADV file to extract GPS flash timing measurements from row fluxes.
    
    This is the main function for GPS timing analysis. It:
    1. Opens ADV file and reads frames
    2. Calculates row-averaged flux for each frame
    3. Aggregates rows together (for rolling shutter analysis)
    4. Detects GPS flashes in each row group
    5. Calculates timing offsets for each flash
    6. Fits line-delay model (for rolling shutter cameras)
    
    Args:
        file_path: Directory containing ADV file
        file_name: ADV filename (e.g., "gps_test.adv")
        frame_start: First frame to process (default 0)
        frame_end: Last frame to process (None = all frames)
        agg_rows: Number of rows to aggregate together (10 = every 10 rows)
                  Set to -1 for entire frame (global shutter)
        exposure_ms: Frame exposure time in ms (IMPORTANT: specify if known!)
                     If None, estimates from frame interval (less accurate)
                     Frame interval = exposure + readout, so may overestimate
        flash_ms: GPS PPS flash duration in ms (default 100)
        ignore_header_lines: Skip N rows at top of frame (for OSD)
        ignore_footer_lines: Skip N rows at bottom of frame (for OSD)
        quality_filter: Filter out poor-quality measurements
        min_frac_flux: Minimum fraction of flux in first frame (quality filter)
        max_frac_flux: Maximum fraction of flux in first frame (quality filter)
        verbose: Print progress information
    
    Returns:
        Dict containing:
            'file': Filename
            'file_path': File path
            'width': Image width
            'height': Image height
            'n_frames': Number of frames processed
            'exposure_ms': Exposure time in ms
            'flash_ms': Flash duration in ms
            'light_curves': Dict of light curves by row group
            'flash_data': List of GPS flash timing measurements
            'regression': Fitted line-delay model (if enough data)
                - 'intercept_ms': Offset in ms
                - 'slope_ms_per_line': Delay per sensor line in ms
                - 'n_inliers': Number of points used in fit
                - 'n_outliers': Number of outliers rejected
    """
    
    print('\n' + '='*60)
    print('GPS Timing Analysis from ADV File')
    print('='*60)
    print('File: ' + file_name)
    
    # Open ADV file
    adv_file = open_adv(file_path, file_name, verbose=verbose)
    
    try:
        width = adv_file.Width
        height = adv_file.Height
        n_frames = adv_file.MainSteamInfo.FrameCount
        
        # Validate frame range
        if frame_start < 0:
            frame_start = 0
        if frame_end is None or frame_end >= n_frames:
            frame_end = n_frames - 1
        if frame_start > frame_end:
            raise ValueError('frame_start (' + str(frame_start) + ') must be <= frame_end (' + str(frame_end) + ')')
        
        print('Processing frames ' + str(frame_start) + ' to ' + str(frame_end))
        print('Image size: ' + str(width) + ' x ' + str(height))
        
        # Get exposure time
        if exposure_ms is None:
            # WARNING: This estimates FRAME INTERVAL, not actual exposure!
            # Frame interval = exposure + readout time
            # Always specify exposure_ms if you know the actual value
            
            # Skip first few frames which may have anomalous timing
            # Use frames 5 and 6 for stable interval measurement
            sample_frame = min(5, frame_end - 1)
            _, frame_info0 = read_adv_frame(adv_file, sample_frame)
            _, frame_info1 = read_adv_frame(adv_file, sample_frame + 1)
            ts0 = get_frame_timestamp(frame_info0)
            ts1 = get_frame_timestamp(frame_info1)
            if ts0 and ts1:
                frame_interval_ms = (ts1 - ts0).total_seconds() * 1000
                exposure_ms = frame_interval_ms
                print('WARNING: Using frame interval as exposure estimate: ' + '{:.1f}'.format(exposure_ms) + ' ms')
                print('  (Calculated from frames ' + str(sample_frame) + '-' + str(sample_frame + 1) + ')')
                print('  (Frame interval = exposure + readout time)')
                print('  Specify exposure_ms parameter for accurate results')
            else:
                # Default fallback
                exposure_ms = 40.0
                print('WARNING: Could not estimate exposure, using default: ' + '{:.1f}'.format(exposure_ms) + ' ms')
        else:
            print('Using specified exposure: ' + '{:.1f}'.format(exposure_ms) + ' ms')
        
        # Calculate effective frame height after cropping
        effective_height = height - ignore_header_lines - ignore_footer_lines
        
        # Storage for all frames' data
        all_row_means = []  # List of lists: all_row_means[frame][row]
        all_timestamps = []
        all_frame_numbers = []
        
        # Process each frame
        print('Reading frames...')
        for frame_no in range(frame_start, frame_end + 1):
            if verbose and (frame_no - frame_start) % 100 == 0:
                print('  Frame ' + str(frame_no - frame_start), end=',')
            
            # Read frame with timestamp info
            pixels, frame_info = read_adv_frame(adv_file, frame_no)
            if pixels is None:
                continue
            
            # Convert to 2D array
            image_2d = pixels_to_2d_list(pixels, width, height)
            
            # Crop header/footer if requested
            if ignore_header_lines > 0 or ignore_footer_lines > 0:
                image_2d = image_2d[ignore_header_lines:height - ignore_footer_lines]
            
            # Calculate trimmed mean for each row (removes hot pixels/stars)
            row_means = calculate_row_means_trimmed(image_2d, proportiontocut=0.05)
            all_row_means.append(row_means)
            
            # Get timestamp (mid-exposure) from frame_info
            timestamp = get_frame_timestamp(frame_info, exposure_ms)
            all_timestamps.append(timestamp)
            all_frame_numbers.append(frame_no)
        
        print('')
        print('Processed ' + str(len(all_frame_numbers)) + ' frames')
        
        # Transpose data: [frame][row] -> [row][frame]
        n_rows = len(all_row_means[0]) if all_row_means else 0
        n_frames_read = len(all_row_means)
        
        row_timeseries = []
        for row_idx in range(n_rows):
            row_ts = [all_row_means[frame_idx][row_idx] 
                     for frame_idx in range(n_frames_read)]
            row_timeseries.append(row_ts)
        
        # Aggregate rows together
        print('Aggregating rows...')
        if agg_rows == -1:
            # Global shutter or whole-frame mode
            print('  Mode: Global shutter (entire frame)')
            aggregated = {
                -1: [calculate_mean([row_timeseries[r][t] for r in range(n_rows)]) 
                     for t in range(len(all_timestamps))]
            }
        else:
            # Rolling shutter mode - group rows
            print('  Mode: Rolling shutter (every ' + str(agg_rows) + ' rows)')
            temp_groups = {}
            for row_idx in range(n_rows):
                group_key = (row_idx // agg_rows) * agg_rows
                if group_key not in temp_groups:
                    temp_groups[group_key] = []
                temp_groups[group_key].append(row_timeseries[row_idx])
            
            # Average within each group
            aggregated = {}
            for group_key, group_rows in temp_groups.items():
                n_times = len(group_rows[0])
                aggregated[group_key] = [
                    calculate_mean([group_rows[r][t] for r in range(len(group_rows))]) 
                    for t in range(n_times)
                ]
        
        print('Created ' + str(len(aggregated)) + ' aggregated light curves')
        
        # Analyze GPS flashes for each row group
        print('Analyzing GPS flashes...')
        light_curves = {}
        flash_data = []
        
        for row_group in sorted(aggregated.keys()):
            signal_values = aggregated[row_group]
            
            if verbose:
                print('  Row group ' + str(row_group), end=',')
            
            # Create light curve dictionary
            lc_data = {
                'frameno': all_frame_numbers[:],
                'time_ut': all_timestamps[:],
                'signal': signal_values[:]
            }
            
            # Analyze for GPS flashes
            lc_enhanced = analyse_gps_flash(lc_data, exposure_ms, flash_ms)
            light_curves[row_group] = lc_enhanced
            
            # Find unique peaks (each peak = one GPS flash)
            unique_peaks = list(set([p for p in lc_enhanced['peak_no'] if p > 0]))
            
            # Calculate timing delays for each peak
            for peak in unique_peaks:
                delay_result = calculate_delays(
                    lc_enhanced, peak, exposure_ms, flash_ms,
                    y=row_group, y_lines=effective_height
                )
                
                if delay_result is not None:
                    # Quality filtering
                    accept = True
                    if quality_filter:
                        frac = delay_result['frac_flux_frame1']
                        if frac < min_frac_flux or frac > max_frac_flux:
                            accept = False
                    
                    if accept:
                        delay_result['row_group'] = row_group
                        delay_result['file'] = file_name
                        flash_data.append(delay_result)
        
        print('')
        print('Found ' + str(len(flash_data)) + ' GPS flash measurements')
        
        # Fit regression model (line delay calibration)
        regression_result = None
        if len(flash_data) >= 5:
            print('Fitting line-delay model...')
            
            y_values = [float(d['y']) for d in flash_data]
            offset_values = [float(d['time_offset']) for d in flash_data]
            
            slope, intercept, inliers = linear_regression_ransac(
                y_values, offset_values, 
                threshold=10.0, max_iterations=100
            )
            
            n_inliers = sum(inliers)
            n_outliers = len(inliers) - n_inliers
            
            regression_result = {
                'slope': slope,
                'intercept': intercept,
                'slope_ms_per_line': slope,
                'intercept_ms': intercept,
                'n_points': len(flash_data),
                'n_inliers': n_inliers,
                'n_outliers': n_outliers
            }
            
            print('')
            print('Line Delay Calibration:')
            print('  Offset: ' + '{:.1f}'.format(intercept) + ' ms')
            print('  Line delay: ' + '{:.4f}'.format(slope) + ' ms/line')
            print('  Points used: ' + str(n_inliers) + '/' + str(len(flash_data)))
            print('  Outliers: ' + str(n_outliers))
        
        return {
            'file': file_name,
            'file_path': file_path,
            'width': width,
            'height': height,
            'n_frames': len(all_frame_numbers),
            'exposure_ms': exposure_ms,
            'flash_ms': flash_ms,
            'light_curves': light_curves,
            'flash_data': flash_data,
            'regression': regression_result
        }
    
    finally:
        # Always close the ADV file
        adv_file.Close()
        print('Closed ADV file')

# ============================================================================
# Export Functions
# ============================================================================

def export_flash_data_csv(flash_data, output_file):
    """
    Export GPS flash timing data to CSV file (TANGRA-compatible format).
    
    Args:
        flash_data: List of flash measurement dicts from process_adv_for_gps_timing()
        output_file: Path to output CSV file
    """
    if not flash_data:
        print('No flash data to export')
        return
    
    # Get all keys from first measurement
    keys = list(flash_data[0].keys())
    
    # Write CSV file
    try:
        with open(output_file, 'w') as f:
            # Header row
            f.write(','.join(keys) + '\n')
            
            # Data rows
            for measurement in flash_data:
                values = []
                for key in keys:
                    value = measurement.get(key, '')
                    
                    # Format datetime objects
                    if isinstance(value, datetime):
                        value = value.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                    
                    values.append(str(value))
                
                f.write(','.join(values) + '\n')
        
        print('Exported ' + str(len(flash_data)) + ' measurements to: ' + output_file)
    
    except Exception as e:
        print('ERROR exporting CSV: ' + str(e))

# ============================================================================
# Example Usage (for testing)
# ============================================================================

if __name__ == '__main__':
    # Example: Process an ADV file for GPS timing analysis
    
    print('ADV GPS Timing Analysis (IronPython version)')
    print('Requires AdvLib.dll and supporting DLLs in ../lib/')
    print('')
    
    # Configuration - adjust these paths for your system
    file_path = r'C:\Users\AstroPC\Documents\GPS_Timing'
    file_name = 'gps_test.adv'
    
    # Check if file exists
    full_path = str(Path(file_path) / file_name)
    if not os.path.exists(full_path):
        print('ERROR: ADV file not found: ' + full_path)
        print('\nPlease update the file_path and file_name variables.')
    else:
        try:
            # Process the ADV file
            result = process_adv_for_gps_timing(
                file_path=file_path,
                file_name=file_name,
                frame_start=0,
                frame_end=None,        # Process all frames
                agg_rows=10,           # Aggregate every 10 rows
                exposure_ms=None,      # Auto-detect
                flash_ms=100,          # 100ms GPS flash
                ignore_header_lines=0, # No OSD cropping
                ignore_footer_lines=0,
                quality_filter=True,   # Filter poor measurements
                min_frac_flux=0.1,
                max_frac_flux=0.9,
                verbose=True
            )
            
            print('')
            print('='*60)
            print('Analysis Complete!')
            print('='*60)
            print('Frames processed: ' + str(result['n_frames']))
            print('Flash measurements: ' + str(len(result['flash_data'])))
            
            if result['regression']:
                reg = result['regression']
                print('')
                print('Line Delay Calibration:')
                print('  Equation: Time = {:.1f} + {:.4f} * Y ms'.format(
                    reg['intercept_ms'], reg['slope_ms_per_line']))
                print('  Quality: ' + str(reg['n_inliers']) + '/' + 
                      str(reg['n_points']) + ' points used')
            
            # Export to CSV
            output_csv = str(Path(file_path) / file_name.replace('.adv', '_gps_timing.csv'))
            export_flash_data_csv(result['flash_data'], output_csv)
            
            print('')
            print('Done!')
        
        except Exception as e:
            print('')
            print('ERROR during processing:')
            print(str(e))
            import traceback
            traceback.print_exc()
