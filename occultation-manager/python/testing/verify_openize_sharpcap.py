"""
Quick DLL Verification Script for SharpCap
===========================================

Copy and paste this script into SharpCap's Python scripting console
to verify that the Openize SDK DLLs are properly loaded.

This should be run from within SharpCap where IronPython is embedded.
"""

import clr
import sys
import os

print("=" * 70)
print("OPENIZE SDK DLL VERIFICATION")
print("=" * 70)

# Resolve project paths from this script location
try:
    current_file = __file__
except NameError:
    current_file = r"c:\Users\AstroPC\Git\occultation-tools\occultation-manager\python\testing\verify_openize_sharpcap.py"

testing_dir = os.path.dirname(os.path.abspath(current_file))
script_dir = os.path.dirname(testing_dir)  # ...\python
lib_path = os.path.join(script_dir, 'lib')

print(f"\nScript directory: {script_dir}")
print(f"Lib directory: {lib_path}")

if os.path.exists(lib_path):
    print(f"✓ Lib directory exists")
    if lib_path not in sys.path:
        sys.path.append(lib_path)
    
    # List DLL files in lib root
    print("\nDLL files found in lib/:")
    dll_found = {}
    for item in os.listdir(lib_path):
        if item.endswith('.dll'):
            dll_path = os.path.join(lib_path, item)
            size_kb = os.path.getsize(dll_path) / 1024
            print(f"  • {item} ({size_kb:.1f} KB)")
            dll_found[item] = True
    
    # Check for required DLLs
    required_dlls = [
        'Openize.OpenXMLSDK.dll',
        'DocumentFormat.OpenXml.dll',
        'DocumentFormat.OpenXml.Framework.dll'
    ]
    
    missing_dlls = [dll for dll in required_dlls if dll not in dll_found]
    if missing_dlls:
        print(f"\n✗ MISSING REQUIRED DLLs:")
        for dll in missing_dlls:
            print(f"  • {dll}")
        print(f"\nPlease copy missing DLLs from lib/netstandard2.0/ to lib/")
        sys.exit(1)
else:
    print(f"✗ Lib directory not found!")
    sys.exit(1)

# Try loading Openize SDK
print("\n" + "-" * 70)
print("LOADING OPENIZE SDK...")
print("-" * 70)

try:
    print("\nAttempting: clr.AddReference('Openize.OpenXMLSDK')")
    clr.AddReference('Openize.OpenXMLSDK')
    print("✓ SUCCESS: Openize.OpenXMLSDK loaded")
except Exception as ex:
    print(f"✗ FAILED: {ex}")
    sys.exit(1)

# Try loading DocumentFormat.OpenXml
try:
    print("\nAttempting: clr.AddReference('DocumentFormat.OpenXml')")
    clr.AddReference('DocumentFormat.OpenXml')
    print("✓ SUCCESS: DocumentFormat.OpenXml loaded")
except Exception as ex:
    print(f"✗ FAILED: {ex}")
    sys.exit(1)

# Try importing Openize namespaces
print("\n" + "-" * 70)
print("IMPORTING OPENIZE NAMESPACES...")
print("-" * 70)

try:
    print("\nAttempting: from Openize.Cells import Workbook, Worksheet")
    from Openize.Cells import Workbook, Worksheet
    print("✓ SUCCESS: Openize.Cells namespace imported")
    print(f"  • Workbook class: {Workbook}")
    print(f"  • Worksheet class: {Worksheet}")
except Exception as ex:
    print(f"✗ FAILED: {ex}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Try creating a test workbook in memory
print("\n" + "-" * 70)
print("TESTING WORKBOOK CREATION...")
print("-" * 70)

try:
    print("\nAttempting: workbook = Workbook()")
    workbook = Workbook()
    print("✓ SUCCESS: Empty workbook created")
    
    print("\nAttempting: worksheet = workbook.Worksheets[0]")
    worksheet = workbook.Worksheets[0]
    print(f"✓ SUCCESS: Got first worksheet")
    
    print("\nAttempting: worksheet.Cells['A1'].PutValue('Test')")
    worksheet.Cells['A1'].PutValue('Test')
    print("✓ SUCCESS: Set cell A1 to 'Test'")
    
    print("\nAttempting: value = worksheet.Cells['A1'].GetValue()")
    value = worksheet.Cells['A1'].GetValue()
    print(f"✓ SUCCESS: Retrieved cell A1 = '{value}'")
    
except Exception as ex:
    print(f"✗ FAILED: {ex}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Final summary
print("\n" + "=" * 70)
print("VERIFICATION COMPLETE - ALL TESTS PASSED!")
print("=" * 70)
print("\n✓ Openize SDK is properly installed and working")
print("✓ Ready to generate TT reports with tt_report_openize.py")
print("\nNext steps:")
print("  1. Test with actual event data")
print("  2. Generate a TT report")
print("  3. Compare with existing generator output")
print("  4. Verify Excel data validation works")
print("=" * 70)
