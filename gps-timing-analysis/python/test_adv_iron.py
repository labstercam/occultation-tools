# Test script for ADV processing with IronPython
# This script tests the AdvLib .NET library and path handling
# Run this in IronPython to verify your setup before processing ADV files

import sys
import os

print('='*70)
print('ADV IronPython Setup Test')
print('='*70)
print('')

# ============================================================================
# Step 1: Test Python version and environment
# ============================================================================
print('1. Testing Python Environment')
print('-'*70)
print('Python version: ' + sys.version)
print('Platform: ' + sys.platform)
print('Executable: ' + sys.executable)
print('')

# Check if running in IronPython
if 'IronPython' in sys.version:
    print('[OK] Running in IronPython')
else:
    print('[WARNING] Not running in IronPython - this may not work!')
print('')

# ============================================================================
# Step 2: Test CLR availability
# ============================================================================
print('2. Testing CLR (.NET) Availability')
print('-'*70)
try:
    import clr
    print('[OK] CLR module imported successfully')
    print('CLR version info:')
    try:
        from System import Environment
        print('  .NET Framework: ' + str(Environment.Version))
    except:
        print('  [INFO] Could not get .NET version')
except ImportError as e:
    print('[ERROR] Failed to import CLR: ' + str(e))
    print('  This script requires IronPython!')
    sys.exit(1)
print('')

# ============================================================================
# Step 3: Test path handling
# ============================================================================
print('3. Testing Path Handling')
print('-'*70)

# Get script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
print('Script directory: ' + script_dir)

# Get lib directory (should be ../lib relative to script)
lib_dir = os.path.join(os.path.dirname(script_dir), 'lib')
print('Lib directory: ' + lib_dir)
print('Lib exists: ' + str(os.path.exists(lib_dir)))

if not os.path.exists(lib_dir):
    print('[WARNING] Lib directory does not exist!')
    print('  Create: ' + lib_dir)
    print('  And place AdvLib DLLs there')
print('')

# Test different path representations
print('Testing path formats:')
test_paths = [
    r'C:\Users\AstroPC\Documents\test.adv',
    'C:/Users/AstroPC/Documents/test.adv',
    os.path.join('C:', 'Users', 'AstroPC', 'Documents', 'test.adv'),
]

for i, path in enumerate(test_paths):
    print('  Path ' + str(i+1) + ': ' + path)
    print('    Normalized: ' + os.path.normpath(path))
    print('    Exists: ' + str(os.path.exists(path)))
print('')

# ============================================================================
# Step 4: Test AdvLib DLL loading
# ============================================================================
print('4. Testing AdvLib DLL Loading')
print('-'*70)

# Add lib directory to path
if lib_dir not in sys.path:
    sys.path.append(lib_dir)
    print('Added to sys.path: ' + lib_dir)

# Check for required DLLs
required_dlls = ['AdvLib.dll', 'AdvLib.Core32.dll', 'AdvLib.Core64.dll']
all_dlls_found = True

print('Checking for required DLLs:')
for dll_name in required_dlls:
    dll_path = os.path.join(lib_dir, dll_name)
    exists = os.path.exists(dll_path)
    print('  ' + dll_name + ': ' + ('FOUND' if exists else 'MISSING'))
    if not exists:
        all_dlls_found = False

if not all_dlls_found:
    print('')
    print('[ERROR] Not all required DLLs found!')
    print('Download from: http://www.hristopavlov.net/adv/AdvLib.NET.zip')
    print('Extract all 3 DLLs to: ' + lib_dir)
    print('')
    print('TEST INCOMPLETE - Cannot proceed without DLLs')
    sys.exit(1)

print('')
print('Attempting to load AdvLib...')
try:
    # Load by full path (required for IronPython)
    advlib_path = os.path.join(lib_dir, 'AdvLib.dll')
    clr.AddReferenceToFileAndPath(advlib_path)
    from Adv import AdvFile2, AdvError, AdvFrameInfo
    print('[OK] AdvLib loaded successfully!')
    print('  AdvFile2 class available')
    print('  AdvError class available')
    print('  AdvFrameInfo class available')
except Exception as e:
    print('[ERROR] Failed to load AdvLib: ' + str(e))
    print('')
    print('Troubleshooting:')
    print('  1. Make sure all 3 DLLs are in: ' + lib_dir)
    print('  2. Check that DLLs are not blocked (Windows security)')
    print('     Right-click each DLL -> Properties -> Unblock')
    print('  3. Make sure you have .NET Framework 4.5+ installed')
    print('  4. Check Windows Event Viewer for DLL load failures')
    sys.exit(1)
print('')

# ============================================================================
# Step 5: Test ADV file path configuration
# ============================================================================
print('5. Testing ADV File Path Configuration')
print('-'*70)

# Example test file paths - ADJUST THESE FOR YOUR SYSTEM
test_file_paths = [
    # Example: User Documents folder
    (os.path.join(os.path.expanduser('~'), 'Documents', 'GPS_Timing'),
     'gps_test.adv'),
    
    # Example: Specific path with raw string
    (r'C:\Users\AstroPC\Documents\GPS_Timing',
     'test.adv'),
    
    # Example: Current directory
    (script_dir,
     'sample.adv'),
]

print('Testing potential ADV file locations:')
adv_file_found = None
for i, (path, filename) in enumerate(test_file_paths):
    full_path = os.path.join(path, filename)
    exists = os.path.exists(full_path)
    print('  ' + str(i+1) + '. ' + full_path)
    print('     Exists: ' + str(exists))
    if exists and adv_file_found is None:
        adv_file_found = (path, filename)

print('')

if adv_file_found:
    print('[OK] Found ADV file: ' + os.path.join(adv_file_found[0], adv_file_found[1]))
    test_file_path, test_file_name = adv_file_found
else:
    print('[INFO] No ADV test files found')
    print('To test ADV file opening, place a test .adv file in:')
    print('  ' + os.path.join(script_dir, 'sample.adv'))
    print('or update the test_file_paths list in this script')
    test_file_path = None
    test_file_name = None
print('')

# ============================================================================
# Step 6: Test ADV file opening (if file available)
# ============================================================================
if test_file_path and test_file_name:
    print('6. Testing ADV File Opening')
    print('-'*70)
    
    full_path = os.path.join(test_file_path, test_file_name)
    print('Attempting to open: ' + full_path)
    
    try:
        adv_file = AdvFile2(full_path)
        print('[OK] ADV file opened successfully!')
        print('')
        print('File information:')
        print('  Width: ' + str(adv_file.Width))
        print('  Height: ' + str(adv_file.Height))
        print('  Frames: ' + str(adv_file.MainSteamInfo.FrameCount))
        print('  Bits per pixel: ' + str(adv_file.DataBpp))
        print('  Max pixel value: ' + str(adv_file.MaxPixelValue))
        print('  Is color: ' + str(adv_file.IsColourImage))
        print('')
        
        # Test reading a single frame
        print('Testing frame reading...')
        try:
            frame_number = 0
            pixels, frame_info = adv_file.GetMainFramePixels(frame_number)
            print('[OK] Read frame ' + str(frame_number))
            print('  Pixel array type: ' + str(type(pixels)))
            print('  Pixel array length: ' + str(len(pixels)))
            print('  Expected length: ' + str(adv_file.Width * adv_file.Height))
            print('  FrameInfo type: ' + str(type(frame_info)))
            print('  Exposure (ns): ' + str(frame_info.Exposure))
            print('  Exposure (ms): ' + str(frame_info.Exposure / 1e6))
            print('')
        except Exception as e:
            print('[ERROR] Failed to read frame: ' + str(e))
            import traceback
            traceback.print_exc()
        
        # Close the file
        adv_file.Close()
        print('[OK] ADV file closed')
        print('')
        
    except Exception as e:
        print('[ERROR] Failed to open ADV file: ' + str(e))
        import traceback
        traceback.print_exc()
        print('')
else:
    print('6. Testing ADV File Opening')
    print('-'*70)
    print('[SKIPPED] No test ADV file available')
    print('')

# ============================================================================
# Step 7: Test importing main processing module
# ============================================================================
print('7. Testing Main Processing Module')
print('-'*70)

try:
    import adv_processing_iron
    print('[OK] adv_processing_iron module imported successfully')
    print('  Available functions:')
    print('    - open_adv()')
    print('    - read_adv_frame()')
    print('    - process_adv_for_gps_timing()')
    print('    - export_flash_data_csv()')
    print('')
except ImportError as e:
    print('[ERROR] Failed to import adv_processing_iron: ' + str(e))
    print('  Make sure adv_processing_iron.py is in: ' + script_dir)
    print('')

# ============================================================================
# Summary
# ============================================================================
print('='*70)
print('Test Summary')
print('='*70)
print('Environment: ' + ('IronPython' if 'IronPython' in sys.version else 'Other'))
print('CLR available: Yes')
print('AdvLib loaded: ' + ('Yes' if 'AdvFile2' in dir() else 'No'))
print('Test ADV file: ' + ('Found' if test_file_path else 'Not found'))
print('Processing module: ' + ('Available' if 'adv_processing_iron' in sys.modules else 'Not available'))
print('')

if 'AdvFile2' in dir():
    print('[SUCCESS] All core components working!')
    print('')
    print('Next steps:')
    print('1. Place your ADV files in a known location')
    print('2. Update file_path and file_name in the example code')
    print('3. Run: import adv_processing_iron')
    print('4. Call: adv_processing_iron.process_adv_for_gps_timing(...)')
    print('')
    print('Example usage:')
    print("  import adv_processing_iron")
    print("  result = adv_processing_iron.process_adv_for_gps_timing(")
    print("      file_path=r'C:\\Users\\AstroPC\\Documents\\GPS_Timing',")
    print("      file_name='my_gps_test.adv',")
    print("      agg_rows=10,")
    print("      verbose=True")
    print("  )")
else:
    print('[INCOMPLETE] Some components missing')
    print('Review the errors above and fix issues')

print('')
print('='*70)
print('Test Complete')
print('='*70)
