"""
Test script to check if simple_xlsx can read the locked RASNZ template
Run this in SharpCap's IronPython environment
"""

import os
from simple_xlsx import load_workbook

# Test loading the locked RASNZ template
template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                             'RASNZ_AstReporttForm_V4.1.2.G.xlsx')

print("="*60)
print("Testing locked XLSX file with simple_xlsx")
print("="*60)
print("Template path:", template_path)
print("File exists:", os.path.exists(template_path))
print()

try:
    print("Loading workbook...")
    wb = load_workbook(template_path)
    print("SUCCESS: Workbook loaded")
    print()
    
    print("Available sheets:", wb.sheetnames)
    print()
    
    # Try to access each sheet
    for sheet_name in wb.sheetnames:
        try:
            ws = wb[sheet_name]
            print("  - {} sheet accessed successfully".format(sheet_name))
        except Exception as ex:
            print("  - {} sheet ERROR: {}".format(sheet_name, str(ex)))
    print()
    
    # Try to read some cells from DATA sheet
    if 'DATA' in wb.sheetnames:
        print("Reading cells from DATA sheet:")
        ws = wb['DATA']
        test_cells = ['A1', 'B1', 'C1', 'D1', 'E1']
        for cell in test_cells:
            try:
                value = ws[cell]
                print("  Cell {}: '{}'".format(cell, value))
            except Exception as ex:
                print("  Cell {} ERROR: {}".format(cell, str(ex)))
        print()
    
    # Try to read from Directions sheet
    if 'Directions' in wb.sheetnames:
        print("Reading cells from Directions sheet:")
        ws = wb['Directions']
        test_cells = ['A1', 'A2', 'A3']
        for cell in test_cells:
            try:
                value = ws[cell]
                print("  Cell {}: '{}'".format(cell, value))
            except Exception as ex:
                print("  Cell {} ERROR: {}".format(cell, str(ex)))
        print()
    
    print("="*60)
    print("CONCLUSION: The locked XLSX file CAN be read successfully!")
    print("Protection does not prevent reading the template.")
    print("="*60)
    
except Exception as ex:
    import traceback
    print("="*60)
    print("ERROR: Failed to load locked XLSX file")
    print("="*60)
    print("Error:", str(ex))
    print()
    print("Full traceback:")
    print(traceback.format_exc())
    print()
    print("="*60)
    print("CONCLUSION: The locked file CANNOT be read.")
    print("You will need to remove protection from the file.")
    print("="*60)
