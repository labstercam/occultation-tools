"""
Detailed cell mapping for Trans-Tasman template
This will identify the exact cells where data should be entered
"""

import os
from simple_xlsx import load_workbook

template_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 
                             'RASNZ_AstReporttForm_V4.1.2.G.xlsx')

wb = load_workbook(template_path)
ws = wb['DATA']

print("="*80)
print("TRANS-TASMAN CELL MAPPING")
print("="*80)
print()

# Define regions to scan for data entry cells
# Based on labels, data cells are typically to the right or below labels

print("EVENT INFORMATION (Rows 1-7):")
for row in range(1, 8):
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 
                'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                'AA', 'AB', 'AC', 'AD', 'AE', 'AF']:
        cell_ref = "{}{}".format(col, row)
        cell = ws[cell_ref]
        value = cell.value if hasattr(cell, 'value') else cell
        if value:
            print("  {}: '{}'".format(cell_ref, value))
print()

print("OBSERVER INFORMATION (Rows 8-15):")
for row in range(8, 16):
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 
                'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y']:
        cell_ref = "{}{}".format(col, row)
        cell = ws[cell_ref]
        value = cell.value if hasattr(cell, 'value') else cell
        if value:
            print("  {}: '{}'".format(cell_ref, value))
print()

print("LOCATION INFORMATION (Rows 16-19):")
for row in range(16, 20):
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 
                'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z',
                'AA', 'AB', 'AC']:
        cell_ref = "{}{}".format(col, row)
        cell = ws[cell_ref]
        value = cell.value if hasattr(cell, 'value') else cell
        if value:
            print("  {}: '{}'".format(cell_ref, value))
print()

print("TELESCOPE/CAMERA (Rows 20-27):")
for row in range(20, 28):
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 
                'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
        cell_ref = "{}{}".format(col, row)
        cell = ws[cell_ref]
        value = cell.value if hasattr(cell, 'value') else cell
        if value:
            print("  {}: '{}'".format(cell_ref, value))
print()

print("TIMING INFORMATION (Rows 28-38):")
for row in range(28, 39):
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 
                'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
        cell_ref = "{}{}".format(col, row)
        cell = ws[cell_ref]
        value = cell.value if hasattr(cell, 'value') else cell
        if value:
            print("  {}: '{}'".format(cell_ref, value))
print()

print("COMMENTS/NOTES (Rows 39-45):")
for row in range(39, 46):
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 
                'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V']:
        cell_ref = "{}{}".format(col, row)
        cell = ws[cell_ref]
        value = cell.value if hasattr(cell, 'value') else cell
        if value:
            print("  {}: '{}'".format(cell_ref, value))
print()

print("="*80)
print("MAPPING COMPLETE")
print("="*80)
