"""
Test different cell access patterns with Openize SDK
"""

import sys
import os

# Add lib folder to path
script_dir = os.path.dirname(os.path.abspath(__file__))
lib_path = os.path.join(os.path.dirname(script_dir), '..', 'lib')
sys.path.insert(0, lib_path)

import clr
clr.AddReference('Openize.OpenXMLSDK')
clr.AddReference('DocumentFormat.OpenXml')

from Openize.Cells import Workbook

# Path to template (now in python folder)
template_path = os.path.join(script_dir, '..', 'RASNZ_AstReporttForm_V4.1.2.G.xlsx')

print("Loading template...")
workbook = Workbook(template_path)
worksheet = workbook.Worksheets[0]

print(f"\nWorksheet name: {worksheet.Name if hasattr(worksheet, 'Name') else 'Unknown'}")

# Test different cell access patterns
print("\n=== Testing Cell Access Patterns ===\n")

# Pattern 1: Direct indexing with string
print("1. Testing: worksheet.Cells['A2']")
try:
    cell = worksheet.Cells['A2']
    print(f"   Cell object: {type(cell)}")
    print(f"   Current value: {cell.Value if hasattr(cell, 'Value') else 'No Value attribute'}")
except Exception as ex:
    print(f"   FAILED: {ex}")

# Pattern 2: Using Get method
print("\n2. Testing: worksheet.Cells.Get('A2')")
try:
    cell = worksheet.Cells.Get('A2')
    print(f"   Cell object: {type(cell)}")
    print(f"   Current value: {cell.Value if hasattr(cell, 'Value') else 'No Value attribute'}")
except Exception as ex:
    print(f"   FAILED: {ex}")

# Pattern 3: Using row/column indices (0-based)
print("\n3. Testing: worksheet.Cells[1, 0]")
try:
    cell = worksheet.Cells[1, 0]  # Row 2, Column A (0-based)
    print(f"   Cell object: {type(cell)}")
    print(f"   Current value: {cell.Value if hasattr(cell, 'Value') else 'No Value attribute'}")
except Exception as ex:
    print(f"   FAILED: {ex}")

# Pattern 4: Using GetCell method
print("\n4. Testing: worksheet.Cells.GetCell('A2')")
try:
    cell = worksheet.Cells.GetCell('A2')
    print(f"   Cell object: {type(cell)}")
    print(f"   Current value: {cell.Value if hasattr(cell, 'Value') else 'No Value attribute'}")
except Exception as ex:
    print(f"   FAILED: {ex}")

# Check what methods are available on Cells
print("\n=== Available Cells methods ===")
try:
    cells_type = type(worksheet.Cells)
    print(f"Cells type: {cells_type}")
    
    # Get methods
    methods = [m for m in dir(worksheet.Cells) if not m.startswith('_')]
    print(f"\nMethods/Properties: {', '.join(methods[:20])}")
except Exception as ex:
    print(f"Could not inspect Cells: {ex}")

print("\n\n=== Now testing PutValue (correct pattern) ===\n")

# Try setting a value using the verified working pattern
print("5. Testing: worksheet.Cells['A2'].PutValue('TEST')")
try:
    # Use the working pattern: direct chain, no str() conversion
    worksheet.Cells['A2'].PutValue('TEST VALUE')
    print(f"   PutValue executed")
    
    # Set some more test values with different types
    worksheet.Cells['D5'].PutValue(2023)  # Integer
    worksheet.Cells['K5'].PutValue('March')  # String
    worksheet.Cells['P5'].PutValue(1)  # Integer
    print(f"   Multiple values set")
    
    # Try saving to a test file
    test_output = os.path.join(script_dir, 'test_cell_write.xlsx')
    workbook.Save(test_output)
    print(f"\n   Saved to: {test_output}")
    print(f"   Please check:")
    print(f"   - A2 should contain 'TEST VALUE'")
    print(f"   - D5 should contain 2023")
    print(f"   - K5 should contain 'March'")
    print(f"   - P5 should contain 1")
    
except Exception as ex:
    print(f"   FAILED: {ex}")
    import traceback
    traceback.print_exc()

print("\n=== Test Complete ===")
