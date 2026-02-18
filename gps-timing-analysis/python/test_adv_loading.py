"""
Diagnostic script to test ADV library loading
Run this in SharpCap IronPython console to see detailed error messages
"""

import sys
import os

# Add script directory to path (needed for execfile() in IronPython)
try:
    script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    # __file__ not defined - try to find the script directory
    script_dir = os.path.abspath(os.getcwd())

if script_dir not in sys.path:
    sys.path.insert(0, script_dir)

print("=" * 70)
print("ADV Library Loading Diagnostic")
print("=" * 70)

# Check Python version
print("\n1. Python Environment:")
print("   Python version: " + sys.version)
print("   Platform: " + sys.platform)

# Check script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_dir = os.path.join(os.path.dirname(script_dir), 'lib')
print("\n2. Directory Paths:")
print("   Script dir: " + script_dir)
print("   Lib dir: " + lib_dir)
print("   Lib dir exists: " + str(os.path.exists(lib_dir)))

# Check for DLL files
print("\n3. DLL Files:")
dll_files = ['AdvLib.dll', 'AdvLib.Core32.dll', 'AdvLib.Core64.dll']
for dll in dll_files:
    dll_path = os.path.join(lib_dir, dll)
    exists = os.path.exists(dll_path)
    size = os.path.getsize(dll_path) if exists else 0
    print("   {0}: {1} ({2} bytes)".format(dll, "FOUND" if exists else "MISSING", size))

# Try to import CLR
print("\n4. CLR Import:")
try:
    import clr
    print("   CLR imported successfully")
    print("   CLR version: " + str(clr.GetClrType(type(clr))))
except Exception as e:
    print("   ERROR importing CLR: " + str(e))
    print("=" * 70)
    sys.exit(1)

# Add lib directory to sys.path
print("\n5. Adding lib directory to sys.path:")
if lib_dir not in sys.path:
    sys.path.append(lib_dir)
    print("   Added: " + lib_dir)
else:
    print("   Already in path")

# Try to load AdvLib.dll
print("\n6. Loading AdvLib.dll:")
advlib_path = os.path.join(lib_dir, 'AdvLib.dll')
try:
    print("   Attempting: clr.AddReferenceToFileAndPath('" + advlib_path + "')")
    clr.AddReferenceToFileAndPath(advlib_path)
    print("   SUCCESS: AdvLib.dll loaded")
except Exception as e:
    print("   ERROR loading AdvLib.dll:")
    print("   " + str(type(e).__name__) + ": " + str(e))
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 70)
    print("DIAGNOSIS: AdvLib.dll could not be loaded")
    print("This is why ADV file option is not available")
    print("=" * 70)
    sys.exit(1)

# Try to import Adv namespace
print("\n7. Importing Adv namespace:")
try:
    from Adv import AdvFile2, AdvError, AdvFrameInfo
    print("   SUCCESS: Imported AdvFile2, AdvError, AdvFrameInfo")
except Exception as e:
    print("   ERROR importing Adv namespace:")
    print("   " + str(type(e).__name__) + ": " + str(e))
    import traceback
    traceback.print_exc()
    print("\n" + "=" * 70)
    print("DIAGNOSIS: AdvLib loaded but Adv namespace not accessible")
    print("=" * 70)
    sys.exit(1)

# Try to import adv_helper
print("\n8. Importing adv_helper module:")
try:
    import adv_helper
    print("   SUCCESS: adv_helper imported")
    is_available = adv_helper.is_advlib_available()
    print("   is_advlib_available() = " + str(is_available))
except Exception as e:
    print("   ERROR importing adv_helper:")
    print("   " + str(type(e).__name__) + ": " + str(e))
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
print("FINAL RESULT: ADV library is READY")
print("=" * 70)
print("\nYou can now run led_line_delay_calibration.py")
print("The ADV file option should be available.")
