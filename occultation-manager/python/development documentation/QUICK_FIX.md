# DLL Installation - Standard Setup

## Status Note (2026-03)

This quick fix reflects the current Openize DLL layout expected by runtime loading.

## Required Setup

All three DLL files must be placed directly in the `python/lib/` root folder:

```
python/lib/
├── Openize.OpenXMLSDK.dll                ✓ Required in root
├── DocumentFormat.OpenXml.dll            ✓ Required in root
├── DocumentFormat.OpenXml.Framework.dll  ✓ Required in root
└── README.md
```

## Installation Steps

1. From `occultation-manager/python`, copy the OpenXML dependencies into `lib/` root:

```powershell
Copy-Item "lib\netstandard2.0\DocumentFormat.OpenXml.dll" "lib\" -Force
Copy-Item "lib\netstandard2.0\DocumentFormat.OpenXml.Framework.dll" "lib\" -Force
```

2. Ensure `Openize.OpenXMLSDK.dll` is present in `lib/` root.

## Verification

Run the verification test in SharpCap (update the path to your local checkout):

```python
execfile(r"<repo>\occultation-manager\python\verify_openize_sharpcap.py")
```

Expected output includes:
```
✓ SUCCESS: Openize.OpenXMLSDK loaded
✓ SUCCESS: DocumentFormat.OpenXml loaded
✓ SUCCESS: Openize.Cells namespace imported
✓ SUCCESS: Empty workbook created
```

---

**Note:** Runtime loading expects these assemblies in `python/lib/` root for predictable behavior.
