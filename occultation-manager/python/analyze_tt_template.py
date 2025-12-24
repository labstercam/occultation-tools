"""
Script to analyze the Trans-Tasman RASNZ template structure
Reads the template and outputs cell mappings and requirements
"""

import os
from simple_xlsx import load_workbook

template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                             'RASNZ_AstReporttForm_V4.1.2.G.xlsx')

print("="*80)
print("TRANS-TASMAN TEMPLATE ANALYSIS")
print("="*80)

wb = load_workbook(template_path)
print("Sheets:", wb.sheetnames)
print()

# Analyze Directions sheet
print("="*80)
print("DIRECTIONS SHEET")
print("="*80)
if 'Directions' in wb.sheetnames:
    ws = wb['Directions']
    # Read first 50 rows to get directions
    for row in range(1, 51):
        row_text = []
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']:
            cell_ref = "{}{}".format(col, row)
            cell = ws[cell_ref]
            value = cell.value if hasattr(cell, 'value') else cell
            if value:
                row_text.append(str(value))
        if row_text:
            print("Row {}: {}".format(row, " | ".join(row_text)))
print()

# Analyze DATA sheet structure
print("="*80)
print("DATA SHEET - CELL MAPPING ANALYSIS")
print("="*80)
if 'DATA' in wb.sheetnames:
    ws = wb['DATA']
    
    # Sample key cells to find labels/structure
    print("\nScanning for field labels and structure...")
    print()
    
    for row in range(1, 50):
        for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 
                    'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                    'AA', 'AB', 'AC', 'AD']:
            cell_ref = "{}{}".format(col, row)
            cell = ws[cell_ref]
            value = cell.value if hasattr(cell, 'value') else cell
            if value and isinstance(value, str):
                # Look for key field names
                lower_val = value.lower()
                keywords = ['asteroid', 'object', 'observer', 'name', 'email', 'location',
                           'latitude', 'longitude', 'elevation', 'telescope', 'aperture',
                           'focal', 'camera', 'timing', 'star', 'catalog', 'date', 'time',
                           'year', 'month', 'day', 'hour', 'minute', 'second', 'phone',
                           'address', 'city', 'state', 'country', 'detector', 'video',
                           'exposure', 'integration', 'started', 'stopped', 'recording']
                
                for keyword in keywords:
                    if keyword in lower_val and len(value) < 50:  # Avoid long text blocks
                        print("{}: '{}'".format(cell_ref, value))
                        break

print()
print("="*80)
print("ANALYSIS COMPLETE")
print("="*80)
