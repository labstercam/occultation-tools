# Occultation-manager Python code modules
## Excel Report Generation

The Occultation Manager includes Excel report generation functionality using a custom pure-Python Excel library called `simple_xlsx.py`.

### Why simple_xlsx?

IronPython (the Python implementation used by SharpCap) cannot load C extensions compiled for CPython. The popular `openpyxl` library has dependencies on C extensions (lxml, numpy) that cause IronPython to crash. Rather than requiring users to install separate Python environments, we created a minimal pure-Python Excel library.

### simple_xlsx Implementation

**File**: `simple_xlsx.py` (364 lines)

**Core Design**:
- Uses only Python standard library: `zipfile` and `xml.etree.ElementTree`
- No external dependencies, no C extensions
- Implements just enough Excel functionality for report generation

**How .xlsx Files Work**:
- `.xlsx` files are ZIP archives containing XML files
- Main components:
  - `xl/workbook.xml` - Workbook structure and sheet list
  - `xl/_rels/workbook.xml.rels` - Relationships between files
  - `xl/worksheets/sheet1.xml` - Individual worksheet data
  - `xl/sharedStrings.xml` - Shared string table

**Classes**:

1. **SimpleWorkbook** - Manages the .xlsx ZIP file
   - `load_workbook(filepath)` - Opens and parses the Excel file
   - `get_sheet_by_name(name)` - Accesses a worksheet by name
   - `save(filepath)` - Saves modified workbook to disk

2. **SimpleWorksheet** - Handles individual worksheets
   - `__getitem__(cell_ref)` - Read cell values: `ws['A1']`
   - `__setitem__(cell_ref, value)` - Write cell values: `ws['A1'] = 'value'`
   - Supports cell references like 'A1', 'B5', 'AA100'

3. **SimpleCell** - Cell value wrapper
   - `.value` property for getting/setting cell contents

**Supported Operations**:
- ✅ Load .xlsx template files
- ✅ Read cell values
- ✅ Write cell values (strings, numbers, dates)
- ✅ Save modified workbooks
- ❌ Formulas (preserved but not calculated)
- ❌ Formatting (preserved from template)
- ❌ Charts, images, or complex features

### Usage Example

```python
from simple_xlsx import load_workbook

# Load a template
wb = load_workbook('template.xlsx')
ws = wb.get_sheet_by_name('Sheet1')

# Read a cell
title = ws['A1'].value

# Write cells
ws['B2'] = 'Observer Name'
ws['C3'] = 42
ws['D4'] = datetime.now()

# Save
wb.save('output.xlsx')
```

### NA Report Generator

**File**: `na_report.py`

Uses `simple_xlsx` to fill in the North American Occultation Report Form template (`NorthAmerica_AstReportForm_V5.6.12r.xlsx`).

**Process**:
1. Load template from local file
2. Access 'DATA' worksheet
3. Write event data to 47 mapped cells
4. Write observer/telescope configuration
5. Write recording times and metadata
6. Generate IOTA-standard filename
7. Save completed report

**Filename Format**:
```
YYYYMMDD_asteroidnumber_asteroidname_starcatalog_starnumber-surname_station.xlsx
Example: 20251213_46854_1998_QY42_UCAC4_485_038369-Camilleri_M_Home.xlsx
```

### Benefits

- ✅ Works natively in IronPython (no external Python installation needed)
- ✅ No C extension compatibility issues
- ✅ Simple, maintainable code (364 lines vs thousands in openpyxl)
- ✅ Fast initialization (no heavy dependencies)
- ✅ Reliable for template-based report generation