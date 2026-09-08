"""ADV File Helper Functions for LED Line Delay Calibration

IronPython-compatible ADV file reading using .NET AdvLib for SharpCap.

This module provides ADV file reading capabilities for the LED Line Delay Calibration tool.
It interfaces with the .NET AdvLib assembly to read ADV format video files recorded by
SharpCap and extract frame data, timestamps, and exposure information.

Requirements:
    - AdvLib.dll and supporting DLLs (AdvLib.Core32.dll or AdvLib.Core64.dll)
    - DLLs must be placed in: gps-timing-analysis/lib/ directory

Key Functions:
    - open_adv(): Open an ADV filefor reading
    - read_adv_frame(): Read a frame with pixel data and metadata
    - get_frame_info_timestamp(): Extract mid-frame UTC timestamp
    - get_frame_exposure_ms(): Get exposure time from file metadata
    - get_aperture_mean(): Calculate mean pixel value in aperture region

Author: Michael Camilleri / Development Team
Date: February 2026
Version: 1.0.0 - Production release
"""

import clr
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add reference to AdvLib .NET assembly
# DLLs should be in ../lib/ directory relative to this script
# Handle both normal execution and SharpCap execfile() scenarios
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # __file__ not defined (can happen with execfile() in some environments)
    # Fall back to current working directory
    script_dir = os.path.abspath(os.getcwd())
    print("WARNING: __file__ not defined, using current directory: " + script_dir)

lib_dir = os.path.join(os.path.dirname(script_dir), 'lib')

# Verify lib_dir exists, if not try alternate relative paths
if not os.path.exists(lib_dir):
    # Try looking for gps-timing-analysis/lib from various relative locations
    alt_paths = [
        os.path.join(script_dir, '..', 'lib'),
        os.path.join(os.getcwd(), '..', 'lib')
    ]
    for alt_path in alt_paths:
        alt_path = os.path.abspath(alt_path)
        if os.path.exists(alt_path):
            lib_dir = alt_path
            print("Found lib directory at: " + lib_dir)
            break
    
print("ADV Helper: Using lib directory: " + lib_dir)
print("  Exists: " + str(os.path.exists(lib_dir)))

# Add lib directory to path for DLL loading
if lib_dir not in sys.path:
    sys.path.append(lib_dir)

# Try to load AdvLib (optional dependency)
ADVLIB_AVAILABLE = False
try:
    advlib_path = os.path.join(lib_dir, 'AdvLib.dll')
    print("Checking for AdvLib.dll at: " + advlib_path)
    
    if os.path.exists(advlib_path):
        print("  AdvLib.dll found, attempting to load...")
        clr.AddReferenceToFileAndPath(advlib_path)
        from Adv import AdvFile2, AdvError, AdvFrameInfo
        ADVLIB_AVAILABLE = True
        print("  SUCCESS: AdvLib loaded and Adv namespace imported")
    else:
        print("  ERROR: AdvLib.dll not found at expected location")
        print("  Please download and place DLLs in: " + lib_dir)
        print("  Required files: AdvLib.dll, AdvLib.Core32.dll, AdvLib.Core64.dll")
except Exception as e:
    print("ERROR loading AdvLib:")
    print("  " + str(type(e).__name__) + ": " + str(e))
    print("  DLL location checked: " + advlib_path)
    print("  To enable ADV file support:")
    print("    1. Download AdvLib from: http://www.hristopavlov.net/adv/AdvLib.NET.zip")
    print("    2. Extract DLLs to: " + lib_dir)
    print("    3. Unblock DLLs (right-click > Properties > Unblock)")
    import traceback
    traceback.print_exc()

# ============================================================================
# ADV File Reading Functions
# ============================================================================

def is_advlib_available():
    """Check if AdvLib is available for ADV file operations"""
    return ADVLIB_AVAILABLE

def open_adv(file_path, file_name, verbose=False):
    """
    Open an ADV file using .NET AdvLib.
    
    Args:
        file_path: Directory path to the file
        file_name: Name of the ADV file
        verbose: If True, print file information
    
    Returns:
        AdvFile2 object (must call .Close() when done)
    """
    if not ADVLIB_AVAILABLE:
        raise Exception("AdvLib is not available. Cannot open ADV files.")
    
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
    Read a single frame from ADV file.
    
    Args:
        adv_file: AdvFile2 object from open_adv()
        frame_number: Frame number to read (0-indexed)
    
    Returns:
        tuple: (pixels_array, frame_info)
            pixels_array: .NET uint[] flat array (width * height length)
            frame_info: AdvFrameInfo object with timestamp and exposure metadata
    
    Returns (None, None) if error occurs.
    """
    try:
        # AdvFile2 has TWO overloads of GetMainFramePixels:
        # 1. GetMainFramePixels(uint frameNo) -> returns uint[]
        # 2. GetMainFramePixels(uint frameNo, out AdvFrameInfo) -> returns uint[] + out param
        #
        # To call overload #2 from IronPython, use clr.Reference to force the out parameter
        from Adv import AdvFrameInfo
        
        # Create a reference for the out parameter
        frame_info_ref = clr.Reference[AdvFrameInfo]()
        
        # Call the overload with out parameter
        pixels = adv_file.GetMainFramePixels(frame_number, frame_info_ref)
        
        # Extract the value from the reference
        frame_info = frame_info_ref.Value
        
        return (pixels, frame_info)
            
    except Exception as e:
        print('ERROR reading frame ' + str(frame_number) + ': ' + str(e))
        import traceback
        traceback.print_exc()
        return (None, None)

def get_frame_timestamp(adv_file, frame_number):
    """
    Get timestamp information for a frame from the ADV MainIndex.
    
    Args:
        adv_file: AdvFile2 object from open_adv()
        frame_number: Frame number (0-indexed)
    
    Returns:
        datetime: Frame timestamp (UTC)
    
    Note:
        ADV files store UTC timestamps in the MainIndex as ElapsedTicks
        measured from the ADV epoch (2010-01-01 00:00:00 UTC).
        Ticks are in 10MHz units (100 nanoseconds per tick).
        
        The exact meaning of the timestamp (start, mid, or end of frame) depends
        on the recording software and camera. This function returns the raw
        timestamp without adjustment. Caller should handle any necessary
        conversion based on their specific use case.
    """
    try:
        # Access the frame index entry
        index_entry = adv_file.MainIndex[frame_number]
        
        # ElapsedTicks is in 10MHz units (100 nanoseconds per tick)
        elapsed_ticks = index_entry.ElapsedTicks
        
        # Convert to microseconds (ticks / 10)
        elapsed_microseconds = elapsed_ticks / 10.0
        
        # ADV epoch: 2010-01-01 00:00:00 UTC
        adv_epoch = datetime(2010, 1, 1, 0, 0, 0)
        
        # Add elapsed time to get UTC timestamp
        timestamp = adv_epoch + timedelta(microseconds=elapsed_microseconds)
        
        return timestamp
    except Exception as e:
        print('ERROR getting timestamp for frame ' + str(frame_number) + ': ' + str(e))
        return None

def get_frame_info_timestamp(adv_file, frame_number):
    """
    Get mid-frame timestamp from ADV file frame info (matches original light_curves.py exactly).
    
    Args:
        adv_file: AdvFile2 object from open_adv()
        frame_number: Frame number (0-indexed)
    
    Returns:
        datetime: Mid-frame timestamp (UTC) as Python datetime object
    
    Note:
        .NET AdvLib AdvFrameInfo properties:
        - UtcStartExposureTimeStamp: DateTime object for start of exposure
        - UtcMidExposureTime: DateTime object for mid-frame (already adjusted)
        - UtcExposureMilliseconds: Exposure duration in milliseconds
        - HasUtcTimeStamp: Boolean indicating if UTC timestamp is available
    """
    try:
        # Get frame info by reading the frame
        pixels, frame_info = read_adv_frame(adv_file, frame_number)
        
        if frame_info is None:
            print('ERROR: Could not get frame info for frame ' + str(frame_number))
            return None
        
        # Try to read timestamp from FrameInfo properties
        try:
            # .NET AdvLib has UtcMidExposureTime which is already the mid-frame timestamp!
            if hasattr(frame_info, 'HasUtcTimeStamp') and frame_info.HasUtcTimeStamp:
                if hasattr(frame_info, 'UtcMidExposureTime'):
                    # Use the mid-exposure time directly (already calculated by AdvLib)
                    # Convert .NET DateTime to Python datetime
                    net_datetime = frame_info.UtcMidExposureTime
                    py_datetime = datetime(
                        net_datetime.Year,
                        net_datetime.Month,
                        net_datetime.Day,
                        net_datetime.Hour,
                        net_datetime.Minute,
                        net_datetime.Second,
                        net_datetime.Millisecond * 1000  # Convert milliseconds to microseconds
                    )
                    return py_datetime
                elif hasattr(frame_info, 'UtcStartExposureTimeStamp') and hasattr(frame_info, 'UtcExposureMilliseconds'):
                    # Fallback: calculate mid-frame from start + exposure/2
                    net_start = frame_info.UtcStartExposureTimeStamp
                    py_start = datetime(
                        net_start.Year,
                        net_start.Month,
                        net_start.Day,
                        net_start.Hour,
                        net_start.Minute,
                        net_start.Second,
                        net_start.Millisecond * 1000
                    )
                    exposure_ms = frame_info.UtcExposureMilliseconds
                    mid_frame_timestamp = py_start + timedelta(milliseconds=exposure_ms / 2.0)
                    return mid_frame_timestamp
                else:
                    raise AttributeError('Missing UtcMidExposureTime or UtcStartExposureTimeStamp properties')
            else:
                raise AttributeError('No UTC timestamp available (HasUtcTimeStamp is False)')
                
        except Exception as e:
            print('ERROR reading timestamp from FrameInfo: {0}'.format(str(e)))
            print('Falling back to MainIndex.ElapsedTicks method...')
            
            # Fallback: Use MainIndex method (less accurate)
            index_entry = adv_file.MainIndex[frame_number]
            elapsed_ticks = index_entry.ElapsedTicks
            elapsed_microseconds = elapsed_ticks / 10.0
            adv_epoch = datetime(2010, 1, 1, 0, 0, 0)
            base_timestamp = adv_epoch + timedelta(microseconds=elapsed_microseconds)
            
            # Try to get exposure from frame_info if available
            try:
                exposure_ms = float(frame_info.Exposure) / 1e6
            except:
                # Last resort - use estimation
                print('  WARNING: Could not get exposure time, using 50ms default')
                exposure_ms = 50.0
            
            # Add half exposure to approximate mid-frame
            mid_frame_timestamp = base_timestamp + timedelta(milliseconds=exposure_ms / 2.0)
            
            return mid_frame_timestamp
            
    except Exception as e:
        print('ERROR getting frame info timestamp for frame ' + str(frame_number) + ': ' + str(e))
        import traceback
        traceback.print_exc()
        return None

def get_frame_exposure_ms(adv_file, frame_number=0):
    """
    Get exposure time in milliseconds from ADV file frame info.
    
    Args:
        adv_file: AdvFile2 object from open_adv()
        frame_number: Frame number to read (default 0, exposure usually constant)
    
    Returns:
        float: Exposure time in milliseconds
    
    Note:
        Reads actual exposure from ADV file metadata.
        Assumes all frames have same exposure (reads from first frame by default).
    """
    try:
        # Get frame info by reading the frame
        pixels, frame_info = read_adv_frame(adv_file, frame_number)
        
        if frame_info is None:
            return None
        
        # Try UtcExposureMilliseconds first (direct value)
        if hasattr(frame_info, 'UtcExposureMilliseconds'):
            return float(frame_info.UtcExposureMilliseconds)
        
        # Fallback: Exposure is stored in nanoseconds, convert to milliseconds
        if hasattr(frame_info, 'Exposure'):
            exposure_ms = float(frame_info.Exposure) / 1e6
            return exposure_ms
        
        return None
    except Exception as e:
        print('ERROR getting exposure for frame ' + str(frame_number) + ': ' + str(e))
        return None

def get_aperture_mean(pixels, width, height, aperture_rect):
    """
    Calculate mean pixel value in an aperture region.
    
    Args:
        pixels: .NET uint[] array from ADV file
        width: Frame width
        height: Frame height
        aperture_rect: System.Drawing.Rectangle defining aperture (X, Y, Width, Height)
    
    Returns:
        float: Mean pixel value in the aperture region
    """
    x = aperture_rect.X
    y = aperture_rect.Y
    w = aperture_rect.Width
    h = aperture_rect.Height
    
    total = 0.0
    count = 0
    
    for row in range(y, min(y + h, height)):
        for col in range(x, min(x + w, width)):
            pixel_index = row * width + col
            if pixel_index < len(pixels):
                total += int(pixels[pixel_index])
                count += 1
    
    if count > 0:
        return total / float(count)
    else:
        return 0.0
