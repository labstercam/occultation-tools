# IronPython-compatible functions to analyse Tangra light curves
# Michael Camilleri
# December 2024
#
# This module provides basic light curve analysis functions compatible with IronPython
# for use in SharpCap scripting environment.
#
# Main functions:
# - read_tangra_csv_iron() - Read Tangra CSV light curve files
# - analyse_timestamps_iron() - Extract timing statistics and camera acquisition delays
#
# Note: This version uses only Python standard library to ensure IronPython compatibility

import csv
from datetime import datetime, timedelta
import os


def read_tangra_csv_iron(file_path):
    """Read a TANGRA CSV light curve file using only standard library
    
    Compatible with IronPython for SharpCap.
    
    Args:
        file_path: Path to the TANGRA CSV file
        
    Returns:
        Dictionary with the following keys:
        - file_read_from: Local file read from
        - filename_from_tangra: The filename from the TANGRA header
        - details: Dictionary with header details from TANGRA
        - apertures: List of dictionaries with aperture information (Object, StartingX, StartingY)
        - light_curve: List of dictionaries with light curve data
        - column_names: List of column names in the light curve
        
    Note: 
        - Times do not use any date so times going over UTC midnight might cause problems
        - This version returns native Python data structures instead of pandas DataFrames
    """
    
    print('Reading TANGRA light curve from file: ' + file_path)
    
    if not os.path.exists(file_path):
        raise IOError('File not found: ' + file_path)
    
    # Read the entire file
    with open(file_path, 'rb') as f:
        lines = [line.decode('utf-8').strip() for line in f.readlines()]
    
    # Read the header (first 2 lines)
    if len(lines) < 2:
        raise ValueError('File too short - missing header')
    
    header_parts = lines[1].split(',')
    if len(header_parts) > 0:
        filename = header_parts[0]
    else:
        filename = ''
    
    # Read the details (line 7, 0-indexed line 6)
    details = {}
    video_format = ''
    if len(lines) > 6:
        # Parse the details line
        detail_reader = csv.reader([lines[6]])
        detail_row = list(detail_reader)[0]
        # Store as a simple dictionary
        details['raw_data'] = detail_row
        # Note: video_format will be extracted later from measurement parameters section
        details['video_format'] = video_format
    
    # Extract video format from measurement parameters (lines 7-8, 0-indexed 6-7)
    try:
        if len(lines) > 7:
            # Read header row (line 7, 0-indexed 6)
            params_header_reader = csv.reader([lines[6]])
            params_header = list(params_header_reader)[0]
            # Read data row (line 8, 0-indexed 7)
            params_data_reader = csv.reader([lines[7]])
            params_data = list(params_data_reader)[0]
            
            # Strip all column names for consistent matching
            params_header_stripped = [col.strip() for col in params_header]
            
            # Find Video File Format column
            for i, col_name in enumerate(params_header_stripped):
                if col_name == 'Video File Format':
                    if i < len(params_data):
                        format_value = params_data[i].strip().upper()
                        if format_value:
                            # Map Tangra format codes to report format names
                            if format_value == 'ADV' or format_value == 'ADVS':
                                video_format = 'ADVS'
                            elif 'AAV' in format_value:
                                if 'NTSC' in format_value:
                                    video_format = 'AAV-NTSC'
                                elif 'PAL' in format_value:
                                    video_format = 'AAV-PAL'
                                else:
                                    video_format = 'ADVS'  # AAV defaults to ADVS
                            elif 'PAL' in format_value or 'CCIR' in format_value:
                                video_format = 'PAL/CCIR'
                            elif 'NTSC' in format_value or 'EIA' in format_value:
                                video_format = 'NTSC/EIA'
                            elif format_value == 'SER':
                                video_format = 'SER'
                            elif format_value in ['AVI', 'MP4', 'FITS']:
                                video_format = format_value
                            else:
                                video_format = format_value  # Use as-is if not recognized
                            details['video_format'] = video_format
                    break
    except (ValueError, IndexError):
        # If parsing fails, video_format stays empty string
        pass
    
    # Find where the light curve data starts by looking for 'FrameNo' or 'BinNo'
    lc_start = -1
    for i, line in enumerate(lines):
        # Check if line starts with FrameNo or BinNo (tab-separated)
        if line.startswith('FrameNo') or line.startswith('BinNo'):
            lc_start = i
            break
        # Also check comma-separated
        parts = line.split(',')
        if len(parts) > 0 and (parts[0] == 'FrameNo' or parts[0] == 'BinNo'):
            lc_start = i
            break
    
    if lc_start < 0:
        raise ValueError('Could not find light curve data start (FrameNo/BinNo not found)')
    
    # Read aperture details (between line 8 and lc_start - 3)
    apertures = []
    if lc_start > 11:  # Make sure there's room for aperture data
        aperture_start = 8
        aperture_end = lc_start - 3
        
        # Read aperture header to find column indices
        aperture_header_reader = csv.reader([lines[aperture_start]])
        aperture_header = list(aperture_header_reader)[0]
        # Clean up header names
        aperture_header = [h.strip().replace(' ', '') for h in aperture_header]
        
        # Find indices for required columns
        try:
            obj_idx = aperture_header.index('Object')
            x_idx = aperture_header.index('StartingX')
            y_idx = aperture_header.index('StartingY')
            
            # Read aperture data rows
            for i in range(aperture_start + 1, aperture_end + 1):
                if i >= len(lines) or not lines[i].strip():
                    break
                aperture_reader = csv.reader([lines[i]])
                aperture_row = list(aperture_reader)[0]
                if len(aperture_row) > max(obj_idx, x_idx, y_idx):
                    apertures.append({
                        'Object': aperture_row[obj_idx].strip(),
                        'StartingX': float(aperture_row[x_idx]) if aperture_row[x_idx].strip() else 0.0,
                        'StartingY': float(aperture_row[y_idx]) if aperture_row[y_idx].strip() else 0.0
                    })
        except (ValueError, IndexError):
            # If we can't find the columns, skip aperture parsing
            pass
    
    # Read light curve data
    light_curve = []
    column_names = []
    
    if lc_start >= 0 and lc_start < len(lines):
        # Read header
        lc_header_reader = csv.reader([lines[lc_start]])
        column_names = list(lc_header_reader)[0]
        # Clean up column names
        column_names = [col.strip().lower()
                       .replace('binned measurment', 'signal')
                       .replace('binno', 'frameno')
                       .replace(' ', '_')
                       .replace('(', '')
                       .replace(')', '')
                       for col in column_names]
        
        # Read data rows
        for i in range(lc_start + 1, len(lines)):
            if not lines[i].strip():
                continue
            
            lc_reader = csv.reader([lines[i]])
            row_data = list(lc_reader)[0]
            
            if len(row_data) < len(column_names):
                continue
            
            # Convert row to dictionary
            row_dict = {}
            for j, col_name in enumerate(column_names):
                if j >= len(row_data):
                    row_dict[col_name] = None
                    continue
                
                value = row_data[j].strip()
                
                # Parse time specially
                if col_name == 'time_ut':
                    row_dict[col_name] = _parse_tangra_time(value)
                # Parse numeric values
                elif col_name == 'frameno':
                    try:
                        row_dict[col_name] = int(value) if value else None
                    except ValueError:
                        row_dict[col_name] = None
                else:
                    # Try to parse as float for signal values
                    try:
                        row_dict[col_name] = float(value) if value else None
                    except ValueError:
                        row_dict[col_name] = value if value else None
            
            light_curve.append(row_dict)
    
    return {
        'file_read_from': file_path,
        'filename_from_tangra': filename,
        'details': details,
        'apertures': apertures,
        'light_curve': light_curve,
        'column_names': column_names,
        'video_format': video_format
    }


def _parse_tangra_time(time_str):
    """Parse TANGRA time format [HH:MM:SS.ffffff]
    
    Args:
        time_str: Time string in format [HH:MM:SS.ffffff]
        
    Returns:
        datetime object (date component is arbitrary - 1900-01-01)
        Returns None if parsing fails
    """
    if not time_str or time_str == '':
        return None
    
    # Remove brackets
    time_str = time_str.strip().replace('[', '').replace(']', '')
    
    try:
        # Parse time
        time_obj = datetime.strptime(time_str, '%H:%M:%S.%f')
        return time_obj
    except ValueError:
        try:
            # Try without microseconds
            time_obj = datetime.strptime(time_str, '%H:%M:%S')
            return time_obj
        except ValueError:
            return None


def analyse_timestamps_iron(tangra_object, percentiles=None):
    """Analyse the timestamps from a TANGRA light curve CSV
    
    Compatible with IronPython for SharpCap.
    Checks timestamps for errors and variation.
    
    Args:
        tangra_object: A TANGRA object as read by read_tangra_csv_iron()
        percentiles: List of percentiles of timestamp delays to calculate, e.g., [1, 99]
        
    Returns:
        Dictionary with summary information including:
        - file_read_from: Source file path
        - filename_from_tangra: Original filename from TANGRA
        - start_time: Start time as string (HH:MM:SS.ffffff)
        - end_time: End time as string (HH:MM:SS.ffffff)
        - tdelta_min: Minimum time delta between frames (ms)
        - tdelta_max: Maximum time delta between frames (ms)
        - tdelta_median: Median time delta (exposure time in ms)
        - tdelta_mean: Mean time delta (ms)
        - tdelta_std: Standard deviation of time deltas (ms)
        - first_frame_no: First frame number
        - last_frame_no: Last frame number
        - frame_count: Total frame count
        - no_rows_in_csv: Number of rows in CSV
        - no_rows_missing_signal: Number of rows with missing signal data
        - exposure_from_row_count: Exposure calculated from row count (ms)
        - exposure_from_frame_no: Exposure calculated from frame numbers (ms)
        - n_late_frames: Number of frames with delays > 1.9x median
        - n_delayed_frames: Number of frames with delays > 1.1x median
        - n_repeated_frames: Number of apparent repeated frames
        - n_blank_cells: Number of rows with blank cells
        - tdelta_percentile_X: Time delta percentiles if requested
    """
    
    lc = tangra_object['light_curve']
    
    if not lc or len(lc) == 0:
        raise ValueError('Light curve data is empty')
    
    # Extract times and frame numbers
    times_list = [row['time_ut'] for row in lc if row.get('time_ut') is not None]
    frame_nos = [row['frameno'] for row in lc if row.get('frameno') is not None]
    
    if len(times_list) < 2:
        raise ValueError('Not enough valid timestamps in light curve')
    
    # Calculate time differences in milliseconds
    timediffs = []
    for i in range(1, len(times_list)):
        if times_list[i] is not None and times_list[i-1] is not None:
            delta = times_list[i] - times_list[i-1]
            # Convert to milliseconds
            delta_ms = delta.total_seconds() * 1000.0
            timediffs.append(delta_ms)
    
    if len(timediffs) == 0:
        raise ValueError('Could not calculate any time differences')
    
    # Check for repeated frames
    # Check if signal values are identical between consecutive rows
    n_repeated_frames = 0
    for i in range(1, len(lc)):
        is_repeated = True
        for key in lc[i].keys():
            if key in ['frameno', 'time_ut']:
                continue
            if lc[i].get(key) != lc[i-1].get(key):
                is_repeated = False
                break
        if is_repeated:
            n_repeated_frames += 1
    
    # Count blank cells (rows with any None values in signal columns)
    n_blank_cells = 0
    for row in lc:
        has_blank = False
        for key, value in row.items():
            if key not in ['frameno', 'time_ut'] and value is None:
                has_blank = True
                break
        if has_blank:
            n_blank_cells += 1
    
    # Count rows with missing signal_1
    no_rows_missing_signal = sum(1 for row in lc if row.get('signal_1') is None)
    
    # Calculate statistics
    tdelta_min = min(timediffs)
    tdelta_max = max(timediffs)
    tdelta_mean = sum(timediffs) / len(timediffs)
    tdelta_median = _calculate_median(timediffs)
    tdelta_std = _calculate_std(timediffs, tdelta_mean)
    
    # Frame statistics
    first_frame_no = frame_nos[0] if frame_nos else 0
    last_frame_no = frame_nos[-1] if frame_nos else 0
    frame_count = last_frame_no - first_frame_no + 1
    no_rows_in_csv = len(lc)
    
    # Calculate exposure times
    total_time_sec = (times_list[-1] - times_list[0]).total_seconds()
    exposure_from_row_count = total_time_sec / (len(times_list) - 1) * 1000.0
    exposure_from_frame_no = total_time_sec / (frame_count - 1) * 1000.0 if frame_count > 1 else 0.0
    
    # Count late and delayed frames
    n_late_frames = sum(1 for td in timediffs if td > (tdelta_median * 1.9))
    n_delayed_frames = sum(1 for td in timediffs if td > (tdelta_median * 1.1))
    
    # Format start and end times
    start_time = times_list[0].strftime('%H:%M:%S.%f')[:12] if times_list[0] else ''
    end_time = times_list[-1].strftime('%H:%M:%S.%f')[:12] if times_list[-1] else ''
    
    # Get video format from tangra_object if available
    video_format = tangra_object.get('video_format', '')
    
    # Determine exposure/integration type
    # If median exposure is consistent, it's likely single frame exposure
    # Otherwise might be integration
    exposure_integration = 'Exposure' if tdelta_std < (tdelta_median * 0.1) else 'Integration'
    
    # Build result dictionary
    result = {
        'file_read_from': tangra_object['file_read_from'],
        'filename_from_tangra': tangra_object['filename_from_tangra'],
        'start_time': start_time,
        'end_time': end_time,
        'tdelta_min': tdelta_min,
        'tdelta_max': tdelta_max,
        'tdelta_median': tdelta_median,
        'tdelta_mean': tdelta_mean,
        'tdelta_std': tdelta_std,
        'first_frame_no': first_frame_no,
        'last_frame_no': last_frame_no,
        'frame_count': frame_count,
        'no_rows_in_csv': no_rows_in_csv,
        'no_rows_missing_signal': no_rows_missing_signal,
        'exposure_from_row_count': exposure_from_row_count,
        'exposure_from_frame_no': exposure_from_frame_no,
        'n_late_frames': n_late_frames,
        'n_delayed_frames': n_delayed_frames,
        'n_repeated_frames': n_repeated_frames,
        'n_blank_cells': n_blank_cells,
        'video_format': video_format,
        'exposure_integration': exposure_integration
    }
    
    # Calculate percentiles if requested
    if percentiles is not None:
        for p in percentiles:
            percentile_value = _calculate_percentile(timediffs, p)
            result['tdelta_percentile_' + str(p)] = percentile_value - tdelta_median
    
    return result


def _calculate_median(values):
    """Calculate median of a list of numeric values
    
    Args:
        values: List of numeric values
        
    Returns:
        Median value
    """
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    if n % 2 == 0:
        # Even number of values - average the two middle values
        return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2.0
    else:
        # Odd number of values - return the middle value
        return sorted_values[n//2]


def _calculate_std(values, mean):
    """Calculate standard deviation of a list of numeric values
    
    Args:
        values: List of numeric values
        mean: Pre-calculated mean of the values
        
    Returns:
        Standard deviation
    """
    if not values or len(values) < 2:
        return 0.0
    
    variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
    return variance ** 0.5


def _calculate_percentile(values, percentile):
    """Calculate percentile of a list of numeric values
    
    Args:
        values: List of numeric values
        percentile: Percentile to calculate (0-100)
        
    Returns:
        Percentile value
    """
    if not values:
        return 0.0
    
    sorted_values = sorted(values)
    n = len(sorted_values)
    
    # Use linear interpolation between closest ranks
    k = (n - 1) * percentile / 100.0
    f = k - int(k)
    
    idx = int(k)
    
    if idx >= n - 1:
        return sorted_values[-1]
    
    return sorted_values[idx] + f * (sorted_values[idx + 1] - sorted_values[idx])


def get_observation_summary(file_path, percentiles=None):
    """Convenience function to read and analyse a Tangra CSV file in one call
    
    Args:
        file_path: Path to the TANGRA CSV file
        percentiles: Optional list of percentiles to calculate, e.g., [1, 99]
        
    Returns:
        Dictionary with analysis results including start_time, end_time, 
        exposure_time (tdelta_median), and camera acquisition delays
        
    Example:
        summary = get_observation_summary('lightcurve.csv', percentiles=[1, 99])
        print('Start:', summary['start_time'])
        print('End:', summary['end_time'])
        print('Exposure (ms):', summary['tdelta_median'])
        print('Max delay (ms):', summary['tdelta_max'])
    """
    tangra_obj = read_tangra_csv_iron(file_path)
    return analyse_timestamps_iron(tangra_obj, percentiles=percentiles)


# Example usage (for testing only - remove or comment out in production)
if __name__ == '__main__':
    # Example of how to use these functions
    print('Tangra Light Curve Analysis - IronPython Compatible Version')
    print('This module provides functions compatible with IronPython for SharpCap')
    print('')
    print('Main functions:')
    print('  - read_tangra_csv_iron(file_path)')
    print('  - analyse_timestamps_iron(tangra_object, percentiles=None)')
    print('  - get_observation_summary(file_path, percentiles=None)')
    print('')
    print('Example usage:')
    print('  summary = get_observation_summary("lightcurve.csv", percentiles=[1, 99])')
    print('  print("Start:", summary["start_time"])')
    print('  print("End:", summary["end_time"])')
    print('  print("Exposure (ms):", summary["tdelta_median"])')
