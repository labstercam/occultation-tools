# Camera Types and Timing Types - Report Format Comparison

## Status Note (2026-03)

This comparison reflects current NA/TT Openize generators and current OBS.XML export mapping.

## Individual Report Formats

### North America (IOTA) Report - `na_report_openize.py`

**Timing Options (from equipment_dialogs.py):**
- GPS - other linking
- GPS - Video Time Inserter
- GPS - KIWI
- WWV
- Visual
- Audio
- Other

**Camera/Detector Fields:**
- `timing` - Selected from timing options above
- `timing_device` - Free text field (e.g., "SharpCap")
- `detector` - Free text field (e.g., "SharpCap", camera name)
- `other_info` - Free text additional information
- `video_format` - SER, AVI, FITS, MP4, Other
- `exposure_integration` - Other, Integration, Exposure

**Default Values:**
- Timing: "GPS - other linking"
- Timing Device: "SharpCap"
- Detector: "SharpCap"
- Video Format: "SER"

---

### Trans-Tasman (RASNZ) Report - `tt_report_openize.py`

**Timing Options:**
- GPS - other linking
- GPS - Video Time Inserter
- GPS - KIWI
- WWV
- Visual
- Audio
- Other

**Camera/Detector Fields:**
- `timing` - Selected from timing options (same as NA)
- `timing_device` - Free text field
- `detector` - Free text field
- `video_format` - SER, AVI, FITS, MP4, Other
- `exposure_integration` - Other, Integration, Exposure

**Additional TT-specific Fields:**
- `timing_method` - Always set to "Video Recording"

**Default Values:**
- Timing: "GPS - other linking"
- Timing Device: "SharpCap"
- Video Format: "SER"

---

### Occult 4 OBS.XML Export - `occult4_export.py`

**Observing Method Codes (single character):**
- _(blank)_ = unspecified
- **a** = Analogue & digital video
- **b** = Digital SLR-camera video
- **c** = Photometer
- **d** = Sequential images
- **e** = Drift scan
- **f** = Visual
- **g** = Other

**Default:** `b` (Digital SLR-camera video)

**Mapping Logic:**
- If camera type contains "video" → `b`
- If camera type contains "photometer" → `c`
- If camera type contains "dslr" or "sequential" → `d`
- Otherwise → `b` (default)

**Time Source Codes (single character):**
- _(blank)_ = unspecified
- **a** = GPS
- **b** = NTP
- **c** = Telephone (fixed or mobile)
- **d** = Radio time signal
- **e** = Internal clock of recorder
- **f** = Stopwatch
- **g** = Other

**Default:** `a` (GPS)

**Note:** Occult4 uses single-letter codes, not descriptive text like NA/TT reports.

---

## Similarities

### All Three Formats Share:
1. **GPS as primary timing source** - All default to GPS timing
2. **Video format tracking** - All support SER, AVI, and other video formats
3. **Exposure/integration distinction** - All track whether timing is per-exposure or integrated
4. **Free-text device field** - All allow specifying the actual timing device used
5. **Alternative timing sources** - All support WWV, Visual, Audio, and Other options

### Common Timing Sources Across All Formats:
- GPS (most common, all formats default to this)
- WWV radio time signal
- Visual observation
- Audio timing
- Other/unspecified

---

## Differences

### 1. **Field Granularity**

**NA & TT (Verbose):**
- Separate "timing" and "timing_device" fields
- Example: 
  - Timing: "GPS - other linking"
  - Timing Device: "SharpCap"

**Occult4 (Coded):**
- Single character code for time source: `a` (GPS)
- Device details not directly stored in XML structure
- More compact representation

### 2. **Camera/Detector Representation**

**NA & TT:**
- Free-text `detector` field
- Allows detailed camera descriptions
- Can include model numbers and specifications

**Occult4:**
- Uses single-letter `observing_method` code
- More generic categorization (video, photometer, sequential, etc.)
- Less detailed but standardized

### 3. **Timing Method Options**

**NA & TT Include:**
- "GPS - other linking"
- "GPS - Video Time Inserter" (specific hardware)
- "GPS - KIWI" (specific hardware)
- WWV
- Visual
- Audio
- Other

**Occult4 Time Source:**
- GPS (generic, no hardware distinction)
- NTP (network time - NOT in NA/TT)
- Telephone (NOT in NA/TT)
- Radio time signal (equivalent to WWV)
- Internal clock (NOT explicit in NA/TT)
- Stopwatch (NOT in NA/TT)
- Other

### 4. **Observing Method**

**NA & TT:**
- No explicit "observing method" field
- Information implied through camera type and video format
- More flexible free-text description

**Occult4:**
- Required single-letter code
- Distinguishes:
  - Analogue vs digital video
  - SLR video
  - Photometer (photoelectric)
  - Sequential images (DSLR/CCD stacking)
  - Drift scan
  - Visual
  - Other

### 5. **GPS Hardware Specificity**

**NA & TT:**
- Distinguish between different GPS linking methods:
  - "other linking" (generic/SharpCap)
  - "Video Time Inserter" (IOTA-VTI hardware)
  - "KIWI" (KIWI-OSD hardware)

**Occult4:**
- Generic GPS code (`a`)
- Hardware details not preserved in standard field
- Must be documented elsewhere (comments/notes)

### 6. **Additional Timing Sources**

**Occult4 Unique:**
- **NTP** - Network Time Protocol (internet time sync)
- **Telephone** - Phone call time services
- **Internal clock** - Pre-calibrated recorder clock
- **Stopwatch** - Manual timing with stopwatch

**NA/TT Unique:**
- **GPS hardware variants** - Specific GPS overlay devices

---

## Mapping Between Formats

### GPS Timing:
- **NA/TT:** "GPS - other linking" / "GPS - Video Time Inserter" / "GPS - KIWI"
- **Occult4:** `a` (GPS)
- **Loss of information:** Specific GPS hardware type

### Radio Time:
- **NA/TT:** "WWV"
- **Occult4:** `d` (Radio time signal)
- **Equivalent**

### Visual/Manual:
- **NA/TT:** "Visual"
- **Occult4:** `f` (Visual)
- **Equivalent**

### Audio:
- **NA/TT:** "Audio"
- **Occult4:** `g` (Other)
- **Note:** Audio timing would map to "Other" in Occult4

### Other:
- **NA/TT:** "Other"
- **Occult4:** `g` (Other)
- **Equivalent**

### NTP (Network Time):
- **NA/TT:** Would use "GPS - other linking" or "Other"
- **Occult4:** `b` (NTP)
- **NA/TT has no explicit NTP option**

### Camera Types:
- **NA/TT:** Free text in `detector` field (e.g., "ZWO ASI178MM", "QHY5L-II")
- **Occult4:** Code in `observing_method`:
  - Video camera → `b`
  - Photometer → `c`
  - DSLR sequential → `d`

---

## Recommendations

### For Multi-Format Reporting:

1. **Store both verbose and coded formats** in camera configuration
2. **GPS Hardware:** Document specific GPS device in "timing_device" field for NA/TT, but accept generic GPS code for Occult4
3. **Camera Type:** Use camera configuration to map to appropriate Occult4 observing method code
4. **Default Mappings:**
   - SharpCap video → `b` (Digital SLR-camera video)
   - GPS timing → `a` (GPS)

### For Camera Configuration Dialog:

Consider adding a new field:
- **Camera Type Category:** Video / Photometer / Sequential / Drift Scan / Other
- This would allow automatic mapping to Occult4 `observing_method` codes
- While preserving detailed camera model in `detector` field for NA/TT

### Handling GPS Hardware Variants:

**Current Approach:**
- NA/TT: Use specific "GPS - Video Time Inserter" or "GPS - KIWI"
- Occult4: Map all GPS variants to code `a`
- Document actual hardware in timing_device field
- **Acceptable trade-off:** Occult4 format prioritizes standardization over hardware specifics

---

## Summary Table

| Feature | NA/TT Reports | Occult4 XML | Notes |
|---------|---------------|-------------|-------|
| **Format** | Free text | Single char codes | Occult4 more compact |
| **GPS Variants** | 3 options | 1 code | NA/TT more specific |
| **NTP Support** | No | Yes (`b`) | Occult4 has NTP |
| **Phone Time** | No | Yes (`c`) | Occult4 only |
| **Stopwatch** | No | Yes (`f`) | Occult4 only |
| **WWV Radio** | Yes | Yes (`d`) | Both support |
| **Visual** | Yes | Yes (`f`) | Both support |
| **Camera Detail** | High (free text) | Low (7 codes) | NA/TT more flexible |
| **Photometer** | Implied | Explicit (`c`) | Occult4 distinguishes |
| **Sequential** | Implied | Explicit (`d`) | Occult4 distinguishes |
| **Drift Scan** | No | Yes (`e`) | Occult4 only |
| **Video Types** | 5 formats | 2 codes (a/b) | NA/TT more granular |

---

## Current Implementation Status

✓ **Fully Implemented:**
- NA report timing/camera fields
- TT report timing/camera fields  
- Occult4 observing method mapping (video/photometer/sequential)
- Occult4 time source (defaults to GPS)

⚠ **Limited Mapping:**
- GPS hardware variants (VTI, KIWI) → Generic GPS code in Occult4
- No explicit mapping for NTP, telephone, stopwatch in NA/TT
- Camera model details not preserved in Occult4 observing method code

✓ **Acceptable Trade-offs:**
- Hardware specifics documented in free-text fields (NA/TT)
- Standardized codes provide consistency (Occult4)
- All essential timing information preserved across formats
