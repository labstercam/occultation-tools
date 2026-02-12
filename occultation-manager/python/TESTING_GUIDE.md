# Testing Openize SDK in SharpCap

## Quick Start Guide

Since this project uses **IronPython embedded in SharpCap**, you'll need to test from within SharpCap's scripting environment.

---

## Step 1: Verify DLL Loading

1. **Open SharpCap**
2. **Open the Python Scripting console** (Tools → Scripting Console or File → Python Scripts)
3. **Load and run the verification script:**

```python
# In SharpCap's Python console, type:
execfile(r"c:\Users\AstroPC\Git\occultation-tools\occultation-manager\python\verify_openize_sharpcap.py")
```

**Expected output:**
```
OPENIZE SDK DLL VERIFICATION
================================
✓ Lib directory exists
✓ SUCCESS: Openize.OpenXMLSDK loaded
✓ SUCCESS: DocumentFormat.OpenXml loaded
✓ SUCCESS: Openize.Cells namespace imported
✓ SUCCESS: Empty workbook created
✓ SUCCESS: Set cell A1 to 'Test'

VERIFICATION COMPLETE - ALL TESTS PASSED!
```

---

## Step 2: Test Report Generation

If Step 1 passed, test the full report generation:

```python
# In SharpCap's Python console, type:
execfile(r"c:\Users\AstroPC\Git\occultation-tools\occultation-manager\python\test_openize_integration.py")
```

**Expected output:**
```
TT REPORT OPENIZE - INTEGRATION TEST
=====================================
[1/6] Importing TTReportGeneratorOpenize...
✓ Import successful
[2/6] Checking Openize SDK availability...
✓ Openize SDK is available
[3/6] Creating mock configuration...
✓ Mock configuration created
[4/6] Creating mock event data...
✓ Mock event created: (12345) TestAsteroid on 2024-12-13 10:03:42
[5/6] Initializing TT report generator...
✓ Generator initialized
[6/6] Generating test report...
✓ SUCCESS: Report generated!
  Location: c:\Users\...\Reports\20241213_12345_TestAsteroid_UCAC4_123_456789+Observer_Test_Station.xlsx

INTEGRATION TEST PASSED!
```

---

## Step 3: Verify the Generated Report

1. **Navigate to the Reports folder:**
   ```
   c:\Users\AstroPC\Git\occultation-tools\occultation-manager\python\Reports\
   ```

2. **Open the generated .xlsx file in Excel**

3. **Check that:**
   - ✅ All cells are populated with test data
   - ✅ Data validation dropdowns work (try clicking cells with dropdowns)
   - ✅ Formulas are intact (if any)
   - ✅ Formatting is preserved
   - ✅ No error cells or #REF! errors

---

## Alternative: Run from Occultation Manager

If you're running the Occultation Manager main application (which also uses IronPython):

```python
# From Occultation Manager's scripting context:
import sys
sys.path.append(r"c:\Users\AstroPC\Git\occultation-tools\occultation-manager\python")

# Then run either verification script
execfile(r"c:\Users\AstroPC\Git\occultation-tools\occultation-manager\python\verify_openize_sharpcap.py")
```

---

## Troubleshooting

### "Could not load file or assembly 'Openize.OpenXMLSDK'"

**Check:**
1. DLL file exists: `lib\Openize.OpenXMLSDK.dll`
2. File is not blocked (right-click → Properties → Unblock)
3. File size is ~500-800 KB (not empty or corrupted)

### "Could not load file or assembly 'DocumentFormat.OpenXml'"

**Check:**
1. DLL exists in: `lib\netstandard2.0\DocumentFormat.OpenXml.dll` or `lib\net462\`
2. File is not blocked
3. File size is ~5-8 MB

### "No module named tt_report_openize"

**Fix:**
```python
import sys
sys.path.insert(0, r"c:\Users\AstroPC\Git\occultation-tools\occultation-manager\python")
```

### "Template not found"

**Check:**
```
c:\Users\AstroPC\Git\occultation-tools\occultation-manager\python\development documentation\RASNZ_AstReporttForm_V4.1.2.G.xlsx
```

Must exist (original template with data validation, NOT the placeholder version).

---

## What Gets Tested

### verify_openize_sharpcap.py
- ✓ DLL files present in lib folder
- ✓ CLR can load both assemblies
- ✓ Namespaces can be imported
- ✓ Can create empty workbook
- ✓ Can set and get cell values

### test_openize_integration.py
- ✓ All of the above, plus:
- ✓ Can load template file
- ✓ Can populate all 50+ cells
- ✓ Can save modified workbook
- ✓ Output file is valid .xlsx format

---

## Next Steps After Successful Tests

1. **Compare with existing generator:**
   - Generate same report with `tt_report.py` (old)
   - Generate same report with `tt_report_openize.py` (new)
   - Compare cell values
   - Verify data validation only works in new version

2. **Test with real data:**
   - Use actual event from OccultWatcher
   - Include real Tangra CSV files
   - Include real AOTA data
   - Verify timing accuracy

3. **Plan integration:**
   - Add option to main GUI
   - Allow user to choose generator
   - Run parallel testing
   - Collect feedback

4. **Consider NA reports:**
   - Apply same approach to `na_report.py`
   - Create `na_report_openize.py`
   - Unified Excel manipulation strategy

---

## Quick Reference: File Locations

```
occultation-manager/python/
├── lib/
│   ├── Openize.OpenXMLSDK.dll           ← Main DLL
│   ├── netstandard2.0/
│   │   └── DocumentFormat.OpenXml.dll   ← Dependency
│   └── net462/
│       └── DocumentFormat.OpenXml.dll   ← Alternative
│
├── development documentation/
│   └── RASNZ_AstReporttForm_V4.1.2.G.xlsx  ← Original template
│
├── tt_report_openize.py                  ← New generator
├── verify_openize_sharpcap.py            ← DLL verification
├── test_openize_integration.py           ← Full integration test
├── OPENIZE_MIGRATION_POC.md              ← Full documentation
└── OPENIZE_POC_SUMMARY.md                ← Quick summary
```

---

## Support

If tests fail or you encounter issues:
1. Check all file locations above
2. Review error messages carefully
3. Try unblocking DLL files in Windows
4. Verify .NET Framework 4.6.2+ is installed
5. Check OPENIZE_MIGRATION_POC.md troubleshooting section

---

*Happy Testing!* 🚀
