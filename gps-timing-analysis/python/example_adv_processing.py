# Example script showing proper path handling for ADV GPS timing analysis
# Compatible with IronPython 3.4 in SharpCap
# Michael Camilleri - February 2026

import sys
import os

# Add the lib directory to Python path for AdvLib DLLs
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(os.path.dirname(script_dir), 'lib')
sys.path.append(lib_dir)

# Import the ADV processing module
import adv_processing_iron

print('='*70)
print('ADV GPS Timing Analysis - Example Script')
print('='*70)
print('')

# ============================================================================
# CONFIGURATION - Update these paths for your system
# ============================================================================

# Method 1: Using raw strings (recommended for Windows)
# The 'r' prefix prevents Python from interpreting backslashes as escape codes
FILE_PATH = r'C:\Users\AstroPC\Documents\GPS_Timing'
FILE_NAME = '02_51_03Z.adv'

# Method 2: Using forward slashes (also works on Windows)
# FILE_PATH = 'C:/Users/AstroPC/Documents/GPS_Timing'
# FILE_NAME = 'gps_test.adv'

# Method 3: Using os.path.join (most portable)
# FILE_PATH = os.path.join('C:', 'Users', 'AstroPC', 'Documents', 'GPS_Timing')
# FILE_NAME = 'gps_test.adv'

# Method 4: Using user's Documents folder (portable across users)
# FILE_PATH = os.path.join(os.path.expanduser('~'), 'Documents', 'GPS_Timing')
# FILE_NAME = 'gps_test.adv'

# Method 5: Relative to script location
# FILE_PATH = os.path.join(script_dir, '..', 'test_data')
# FILE_NAME = 'gps_test.adv'

# Processing parameters
FRAME_START = 0          # First frame to process (0 = first frame)
FRAME_END = None         # Last frame to process (None = all frames)
AGG_ROWS = 10            # Aggregate every N rows (10 = good for most cameras)
                         # Use -1 for global shutter (entire frame)
EXPOSURE_MS = None       # Exposure time in ms (e.g., 40.0)
                         # Set to None for auto-estimate (uses frame interval)
                         # NOTE: Auto-estimate calculates frame interval, NOT exposure!
                         # Frame interval = exposure + readout time
                         # Specify exact value if you know the actual exposure time
FLASH_MS = 100           # GPS PPS flash duration in ms (typically 100)
IGNORE_HEADER = 0        # Rows to ignore at top (for OSD overlay)
IGNORE_FOOTER = 0        # Rows to ignore at bottom (for OSD overlay)
QUALITY_FILTER = True    # Enable quality filtering of measurements
MIN_FRAC_FLUX = 0.1      # Minimum fraction of flash in first frame
MAX_FRAC_FLUX = 0.9      # Maximum fraction of flash in first frame
VERBOSE = True           # Print detailed progress

# ============================================================================
# PATH VALIDATION
# ============================================================================

print('Configuration:')
print('-'*70)
print('File path: ' + FILE_PATH)
print('File name: ' + FILE_NAME)
print('')

# Construct full path
full_path = os.path.join(FILE_PATH, FILE_NAME)
print('Full path: ' + full_path)
print('Normalized path: ' + os.path.normpath(full_path))
print('')

# Check if file exists
if not os.path.exists(full_path):
    print('[ERROR] ADV file not found!')
    print('')
    print('Please check:')
    print('1. File path is correct: ' + FILE_PATH)
    print('2. File name is correct: ' + FILE_NAME)
    print('3. File actually exists at: ' + full_path)
    print('')
    print('To fix:')
    print('  - Update FILE_PATH and FILE_NAME at the top of this script')
    print('  - Use raw strings r"C:\\path" or forward slashes "C:/path"')
    print('  - Check Windows Explorer to verify the exact path')
    sys.exit(1)

print('[OK] ADV file found')
print('')

# Check if output directory is writable
print('Checking output directory...')
if os.access(FILE_PATH, os.W_OK):
    print('[OK] Output directory is writable')
else:
    print('[WARNING] Output directory may not be writable')
    print('  CSV export may fail')
print('')

# ============================================================================
# PROCESS ADV FILE
# ============================================================================

print('='*70)
print('Starting ADV processing...')
print('='*70)
print('')

try:
    # Process the ADV file for GPS timing
    result = adv_processing_iron.process_adv_for_gps_timing(
        file_path=FILE_PATH,
        file_name=FILE_NAME,
        frame_start=FRAME_START,
        frame_end=FRAME_END,
        agg_rows=AGG_ROWS,
        exposure_ms=EXPOSURE_MS,
        flash_ms=FLASH_MS,
        ignore_header_lines=IGNORE_HEADER,
        ignore_footer_lines=IGNORE_FOOTER,
        quality_filter=QUALITY_FILTER,
        min_frac_flux=MIN_FRAC_FLUX,
        max_frac_flux=MAX_FRAC_FLUX,
        verbose=VERBOSE
    )
    
    # ========================================================================
    # DISPLAY RESULTS
    # ========================================================================
    
    print('')
    print('='*70)
    print('RESULTS')
    print('='*70)
    print('')
    
    print('File Information:')
    print('  Filename: ' + result['file'])
    print('  Image size: ' + str(result['width']) + ' x ' + str(result['height']))
    print('  Frames processed: ' + str(result['n_frames']))
    print('  Exposure: ' + '{:.2f}'.format(result['exposure_ms']) + ' ms')
    print('')
    
    print('GPS Flash Detection:')
    print('  Total measurements: ' + str(len(result['flash_data'])))
    print('  Quality filter: ' + ('Enabled' if QUALITY_FILTER else 'Disabled'))
    print('')
    
    if result['regression'] and len(result['flash_data']) >= 5:
        reg = result['regression']
        print('Line Delay Calibration:')
        print('  Equation: Time = {:.1f} + {:.5f} * Y ms'.format(
            reg['intercept_ms'], reg['slope_ms_per_line']))
        print('  Intercept: {:.1f} ms'.format(reg['intercept_ms']))
        print('  Line delay: {:.5f} ms/line'.format(reg['slope_ms_per_line']))
        print('  Line delay: {:.2f} us/line'.format(reg['slope_ms_per_line'] * 1000))
        print('  Points used: ' + str(reg['n_inliers']) + '/' + str(reg['n_points']))
        print('  Outliers rejected: ' + str(reg['n_outliers']))
        print('')
    elif len(result['flash_data']) > 0:
        print('[WARNING] Not enough measurements for regression fit')
        print('  Need at least 5 measurements, found: ' + str(len(result['flash_data'])))
        print('')
    else:
        print('[ERROR] No GPS flashes detected!')
        print('  Possible issues:')
        print('    - GPS not flashing during recording')
        print('    - Flash too dim or too bright')
        print('    - Wrong exposure time or flash duration')
        print('')
    
    # ========================================================================
    # EXPORT RESULTS
    # ========================================================================
    
    if len(result['flash_data']) > 0:
        # Construct output filename
        output_filename = FILE_NAME.replace('.adv', '_gps_timing.csv')
        output_path = os.path.join(FILE_PATH, output_filename)
        
        print('Exporting results...')
        adv_processing_iron.export_flash_data_csv(result['flash_data'], output_path)
        print('')
        
        print('Output files:')
        print('  CSV: ' + output_path)
        print('')
    
    # ========================================================================
    # MEASUREMENT QUALITY STATISTICS
    # ========================================================================
    
    if len(result['flash_data']) > 0:
        print('Measurement Quality:')
        
        # Calculate statistics on frac_flux_frame1
        fracs = [d['frac_flux_frame1'] for d in result['flash_data']]
        min_frac = min(fracs)
        max_frac = max(fracs)
        avg_frac = sum(fracs) / len(fracs)
        
        print('  First frame flux fraction:')
        print('    Min: {:.3f}'.format(min_frac))
        print('    Max: {:.3f}'.format(max_frac))
        print('    Average: {:.3f}'.format(avg_frac))
        print('    Target range: {:.1f} - {:.1f}'.format(MIN_FRAC_FLUX, MAX_FRAC_FLUX))
        
        # Count measurements by row
        rows = set([d['y'] for d in result['flash_data']])
        print('  Row groups with measurements: ' + str(len(rows)))
        print('')
    
    print('='*70)
    print('Processing complete!')
    print('='*70)
    
except Exception as e:
    print('')
    print('='*70)
    print('[ERROR] Processing failed!')
    print('='*70)
    print('')
    print('Error message: ' + str(e))
    print('')
    print('Troubleshooting:')
    print('  1. Check that ADV file is valid (try opening in TANGRA)')
    print('  2. Verify AdvLib DLLs are in: ' + lib_dir)
    print('  3. Check that file path uses proper format (raw strings or forward slashes)')
    print('  4. Ensure GPS was flashing during recording')
    print('  5. Try adjusting exposure_ms or flash_ms parameters')
    print('')
    
    # Print full traceback for debugging
    import traceback
    print('Full error traceback:')
    traceback.print_exc()
