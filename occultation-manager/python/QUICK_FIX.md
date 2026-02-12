# DLL Installation - Standard Setup

## Required Setup

All three DLL files must be placed directly in the `lib/` root folder:

```
lib/
├── Openize.OpenXMLSDK.dll                ✅ Required in root
├── DocumentFormat.OpenXml.dll            ✅ Required in root
├── DocumentFormat.OpenXml.Framework.dll  ✅ Required in root
└── README.md
```

## Installation Steps

1. **Copy Openize.OpenXMLSDK.dll to lib/ root:**
   - Already done if downloaded from NuGet package

2. **Copy DocumentFormat.OpenXml.dll to lib/ root:**
   ```powershell
   cd "c:\Users\AstroPC\Git\occultation-tools\occultation-manager\python"
   Copy-Item "lib\netstandard2.0\DocumentFormat.OpenXml.dll" "lib\"
   ```

3. **Copy DocumentFormat.OpenXml.Framework.dll to lib/ root:**
   ```powershell
   Copy-Item "lib\netstandard2.0\DocumentFormat.OpenXml.Framework.dll" "lib\"
   ```

   Or manually:
   - Navigate to: `lib\netstandard2.0\`
   - Copy: `DocumentFormat.OpenXml.dll` AND `DocumentFormat.OpenXml.Framework.dll`
   - Paste both into: `lib\` (root folder)

## Verification

Run the verification test in SharpCap:

```python
execfile(r"c:\Users\AstroPC\Git\occultation-tools\occultation-manager\python\verify_openize_sharpcap.py")
```

Expected output:
```
✓ SUCCESS: Openize.OpenXMLSDK loaded
✓ SUCCESS: DocumentFormat.OpenXml loaded
✓ SUCCESS: Openize.Cells namespace imported
✓ SUCCESS: Empty workbook created
```

---

**Note:** The code expects both DLLs in `lib/` root. Subfolders are not searched to keep paths predictable and avoid runtime surprises.
