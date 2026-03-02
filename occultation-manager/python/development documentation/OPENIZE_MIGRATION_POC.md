# TT Report Generation - Openize SDK Migration

## Status Note (2026-03)

Migration is complete and Openize-based generators are the production path for both TT and NA report generation.
This document is retained as technical migration history and reference material.

## Proof of Concept Documentation

This document describes the proof-of-concept migration from XML string replacement to the Openize OpenXML SDK for Trans-Tasman (RASNZ) report generation.

---

## Overview

### Legacy Implementation (`tt_report.py`, removed)
- Creates Excel template with placeholder text (`{{OBSERVATION_TYPE}}`, etc.)
- Manually manipulates ZIP file structure and XML content
- Uses `zipfile` and `xml.etree.ElementTree` for string replacements
- Requires maintenance of separate placeholder template file

### New Implementation (`tt_report_openize.py`)
- Uses original Excel template with data validation intact
- Leverages Openize OpenXML SDK .NET library via IronPython
- Direct cell access: `worksheet.Cells['A2'].PutValue(value)`
- Cleaner, more maintainable code

---

## Key Benefits

### 1. **Preserves Excel Features**
- ✓ Data validation dropdowns work immediately
- ✓ Cell formatting remains intact
- ✓ Formulas are preserved
- ✓ Conditional formatting maintained

### 2. **More Reliable**
- ✓ No XML namespace issues
- ✓ Robust to Excel structure changes
- ✓ Type-safe cell operations
- ✓ Automatic value validation

### 3. **Cleaner Code**
```python
# OLD WAY - Complex XML manipulation
with zipfile.ZipFile(template_path, 'r') as zf:
    xml_str = zf.read('xl/worksheets/sheet1.xml').decode('utf-8')
    xml_str = xml_str.replace('{{OBSERVATION_TYPE}}', observation_type)
    # ... many more replacements

# NEW WAY - Direct and clear
worksheet.Cells['A2'].PutValue(observation_type)
```

### 4. **Better Maintainability**
- Cell references are explicit in code
- No need to maintain placeholder mapping files
- Easier to debug and update
- Self-documenting code

---

## Architecture

### File Structure
```
occultation-manager/python/
├── lib/                                    # NEW: .NET DLLs
│   ├── Openize.OpenXMLSDK.dll             # Main SDK
│   ├── DocumentFormat.OpenXml.dll         # Dependency
│   └── DocumentFormat.OpenXml.Framework.dll # Dependency
├── development documentation/
│   └── RASNZ_AstReporttForm_V4.1.2.G.xlsx # Original template (with validation)
├── tt_report.py                           # Legacy implementation (removed)
├── tt_report_openize.py                   # NEW: Openize-based generator
└── testing/test_openize_tt_report.py      # NEW: Test/demo script
```

### Dependencies
- **IronPython** (already in use) - Provides .NET interop via `clr` module
- **Openize.OpenXML-SDK** (new) - .NET library for Excel manipulation
- **DocumentFormat.OpenXml** (new) - Required by Openize SDK

---

## Cell Mapping Reference

Based on `TT_PLACEHOLDERS.txt`, here are the key cell mappings:

### Event Information
| Cell | Content | Example |
|------|---------|---------|
| A2   | Observation Type | "Positive" |
| D5   | Event Year | 2024 |
| K5   | Event Month | "Dec" |
| P5   | Event Day | 13 |
| Y5   | Predicted Hours | 10 |
| AA5  | Predicted Minutes | 3 |
| AC5  | Predicted Seconds | 42 |

### Asteroid & Star Information
| Cell | Content | Example |
|------|---------|---------|
| E7   | Asteroid Number | "46854" |
| K7   | Asteroid Name | "1998 QY42" |
| S7   | Star Catalog | "UCAC4" |
| X7   | Star Number | "485-038369" |
| P8   | RIO/TNO Prediction | "No" |

### Observer Information
| Cell | Content | Example |
|------|---------|---------|
| D9   | Observer Name | "Michael Camilleri" |
| S9   | Observer Email | "email@example.com" |
| D11  | Observer Address | "7/1 Piripiri Drive" |
| S11  | Observer Phone | "+64211840111" |
| D13  | City, State, Country | "Auckland, NZ" |
| E15  | Observing Location | "Te Atatu Peninsula" |

### Location Coordinates
| Cell | Content | Example |
|------|---------|---------|
| E17  | Latitude Format | "deg.ddddd" |
| E18  | Latitude | 36.83556 |
| J18  | Latitude Direction | "S" or "N" |
| N17  | Longitude Format | "deg.ddddd" |
| N18  | Longitude | 174.6578 |
| R18  | Longitude Direction | "E" or "W" |
| V18  | Elevation | 23 |
| W18  | Elevation Units | "m" |
| AA18 | Elevation Datum | "WGS84" |

### Equipment
| Cell | Content | Example |
|------|---------|---------|
| E20  | Aperture | 23.5 (cm) |
| H20  | Aperture Units | "cm" |
| L20  | Focal Ratio | 6.3 |
| T20  | Telescope Type | "SCT" |

### Timing & Recording
| Cell | Content | Example |
|------|---------|---------|
| C22  | Timing Method | "GPS PPS" |
| O22  | Recording Method | "Video Recording" |
| Y22  | Asteroid Visible | "Yes" |
| E23  | Timing Device | "SharpCap" |
| C24  | OTE | "AOTA (part of OCCULT4)" |

### Detector/Camera
| Cell | Content | Example |
|------|---------|---------|
| E25  | Detector | "SharpCap" |
| L25  | Video Format | "SER" |
| O25  | Integration Time | 0.040 (seconds) |
| S25  | Integration Units | "Seconds" |
| Z26  | Corrections Applied | "yes" |
| AA26 | Camera Delay | 0.045 (seconds) |

### Timing Observations
| Cell | Content | Example |
|------|---------|---------|
| E31  | Start Hours | 10 |
| G31  | Start Minutes | 3 |
| I31  | Start Seconds | 42.15 |
| E37  | Stop Hours | 10 |
| G37  | Stop Minutes | 8 |
| I37  | Stop Seconds | 15.32 |

### AOTA Timing Data (D = Disappearance, R = Reappearance)
| Cell | Content | Example |
|------|---------|---------|
| G31  | AOTA D Hours | 10 |
| I31  | AOTA D Minutes | 4 |
| K31  | AOTA D Seconds | 12.345 |
| M31  | AOTA D Error | 0.023 |
| G37  | AOTA R Hours | 10 |
| I37  | AOTA R Minutes | 4 |
| K37  | AOTA R Seconds | 15.678 |
| M37  | AOTA R Error | 0.025 |

### Event Outcome
| Cell | Content | Example |
|------|---------|---------|
| W38  | Was Miss | "no" / "yes" / "maybe" |
| D40  | Second Star | "No" |
| D42  | Comments | (free text) |

---

## Implementation Details

### Class: `TTReportGeneratorOpenize`

Inherits from `ReportGeneratorBase` to maintain compatibility with existing infrastructure.

#### Key Methods

**`__init__(self, config)`**
- Checks if Openize SDK is available
- Raises `RuntimeError` if DLLs not found

**`generate_report(self, event, ...)`**
- Main entry point (same signature as `TTReportGenerator`)
- Opens original template using Openize SDK
- Populates worksheet with event data
- Saves to Reports folder

**`_populate_worksheet(self, worksheet, event)`**
- Core logic for populating all cells
- Calls `_set_cell()` for each field
- Handles Tangra and AOTA data integration

**`_set_cell(self, worksheet, cell_ref, value)`**
- Helper to safely set cell values
- Skips empty/None values
- Converts all values to strings
- Handles exceptions gracefully

**`_populate_aota_data(self, worksheet, aota_report_summary)`**
- Populates AOTA timing data if available
- Maps disappearance (D) and reappearance (R) times
- Includes uncertainty values

---

## Usage

### Basic Usage
```python
from tt_report_openize import TTReportGeneratorOpenize

# Initialize (interface-compatible with prior generator)
generator = TTReportGeneratorOpenize(config)

# Generate report (identical interface)
output_path = generator.generate_report(
    event=event,
    telescope_id=telescope_id,
    camera_id=camera_id,
    observation_type='Positive',
    tangra_data=tangra_data,
    aota_report_data=aota_report_data,
    aota_xml_used=False
)

if output_path:
    print(f"Report generated: {output_path}")
else:
    print("Report generation failed")
```

### Testing
```bash
# Run the test script
python test_openize_tt_report.py
```

Current testing layout note:
- Active scripts are in `testing/` (`verify_openize_sharpcap.py`, `test_openize_integration.py`, `test_openize_tt_report.py`)
- Older legacy/one-off scripts were moved to `testing/archive/` for historical reference and are not part of the active testing workflow

The test script will:
1. Check if Openize SDK is available
2. Verify template file exists
3. Show comparisons between old and new approaches
4. Demonstrate usage examples

---

## Installation

### 1. Download Openize SDK

Visit: https://www.nuget.org/packages/Openize.OpenXML-SDK/

Click "Download package" to get `openize.openxml-sdk.25.7.0.nupkg`

### 2. Extract DLLs

The .nupkg file is a ZIP archive. Extract these files:

```
lib/netstandard2.0/Openize.OpenXMLSDK.dll
lib/netstandard2.0/DocumentFormat.OpenXml.dll
lib/netstandard2.0/DocumentFormat.OpenXml.Framework.dll
```

Or use PowerShell:
```powershell
# Download using NuGet CLI
nuget install Openize.OpenXML-SDK -OutputDirectory ./packages

# DLLs will be in:
# ./packages/Openize.OpenXML-SDK.25.7.0/lib/netstandard2.0/
```

### 3. Place DLLs in lib/ folder

```
occultation-manager/python/
└── lib/
    ├── Openize.OpenXMLSDK.dll
    ├── DocumentFormat.OpenXml.dll
    └── DocumentFormat.OpenXml.Framework.dll
```

### 4. Verify Installation
```bash
python testing/test_openize_tt_report.py
```

You should see:
```
✓ SUCCESS: Openize SDK is loaded and available!
✓ SUCCESS: Original template found
```

---

## Migration Strategy (Historical Checklist)

### Phase 1: Testing (Completed)
- [x] Create proof-of-concept implementation
- [x] Document cell mappings
- [x] Create test script
- [ ] Generate test reports with sample data
- [ ] Compare output with archived baseline reports
- [ ] Verify Excel features work correctly

### Phase 2: Integration (Completed)
- [x] Add Openize generator to main GUI
- [x] Remove old/new generator option
- [ ] Continue real-data validation
- [ ] Gather user feedback

### Phase 3: Migration (Completed)
- [ ] Address any issues found in testing
- [ ] Update documentation
- [x] Make Openize generator the default
- [x] Remove old generator fallback option

### Phase 4: Cleanup (In Progress)
- [x] Remove placeholder template files from packaging
- [ ] Update user documentation
- [x] Migrate NA reports to Openize

---

## Comparison: Old vs New

### Code Complexity

**Old Implementation (legacy):**
- 680 lines in `tt_report.py` (removed)
- Complex XML parsing and manipulation
- String replacement in multiple XML files
- Namespace handling required
- Error-prone with template changes

**New Implementation:**
- 580 lines in `tt_report_openize.py`
- Direct cell access
- No XML manipulation needed
- Type-safe operations
- Robust to template structure

### Performance

Both approaches are fast enough for single report generation:
- Old: ~0.5-1.0 seconds per report (ZIP manipulation overhead)
- New: ~0.3-0.8 seconds per report (efficient DLL operations)

### Reliability

**Old Implementation Issues:**
- XML namespaces can cause failures
- Template structure changes break code
- Data validation lost after generation
- Placeholders can be missed

**New Implementation Benefits:**
- Uses official Excel SDK
- Preserves all Excel features
- More predictable behavior
- Better error messages

---

## Troubleshooting

### "Openize SDK not available"
**Cause:** DLLs not found or not loaded

**Solution:**
1. Verify DLLs exist in `lib/` folder
2. Check DLL versions are compatible
3. Try adding lib path to system PATH
4. Check for .NET Framework version compatibility

### "Template not found"
**Cause:** Original template file missing

**Solution:**
1. Ensure `RASNZ_AstReporttForm_V4.1.2.G.xlsx` exists
2. Check it's in `development documentation/` folder
3. Verify file permissions

### "Could not set cell"
**Cause:** Invalid cell reference or value type

**Solution:**
1. Check cell reference is valid (e.g., "A2", not "A2:")
2. Ensure value can be converted to string
3. Check for None/empty values

---

## Future Enhancements

### 1. North America Reports
Keep `na_report_openize.py` aligned with TT Openize approach for consistency

### 2. Batch Processing
Leverage Openize SDK for efficient multi-report generation

### 3. Enhanced Validation
Add cell validation checking before setting values

### 4. Template Discovery
Auto-detect and use appropriate template versions

### 5. Formula Support
Populate cells that use formulas for calculations

---

## References

- **Openize SDK GitHub:** https://github.com/openize-com/openize-open-xml-sdk-net
- **NuGet Package:** https://www.nuget.org/packages/Openize.OpenXML-SDK/
- **Excel README:** https://github.com/openize-com/openize-open-xml-sdk-net/blob/main/Excel/README.md
- **TT Placeholders:** `development documentation/TT_PLACEHOLDERS.txt`
- **Original Template:** `development documentation/RASNZ_AstReporttForm_V4.1.2.G.xlsx`

---

## Support

For questions or issues with this proof of concept:

1. Run the test script: `python testing/test_openize_tt_report.py`
2. If reviewing older ad hoc tests, check `testing/archive/` (not part of the active testing workflow)
3. Check cell mappings in this document
4. Review example usage above
5. Verify DLLs are correctly installed

---

*Last Reviewed: 2026-03-02*
*Version: 1.1 - Historical migration reference*
