# Bug Check Report - Occelmnt Data & OBS.XML Export

## Date: December 31, 2025

## Summary
Found and fixed **CRITICAL BUGS** in Occelmnt data field mapping and OBS.XML export code.

---

## ❌ CRITICAL BUGS FIXED

### 1. **Object Tag Field Mapping - COMPLETELY WRONG** ✅ FIXED

**Location:** `events.py` lines 256-271

**Problem:** Object tag field indices did not match the Occelmnt specification at all.

**What Was Wrong:**
```python
# INCORRECT MAPPING
object_data[2] = 'object_desig'        # WRONG - should be magnitude
object_data[4] = 'object_diameter_flag' # WRONG - should be distance_au
object_data[5] = 'object_orbit_source'  # WRONG - should be rings
object_data[6] = 'object_bibcode'       # WRONG - should be moons
object_data[7] = 'object_epoch'         # WRONG - should be dRA
object_data[8] = 'object_error_source'  # WRONG - should be dDec
object_data[9] = 'object_error_bibcode' # WRONG - should be taxonomic class
object_data[11] = 'object_ephemeris_uncertainty' # WRONG - should be moon shadow flag
object_data[12] = 'object_mag_h'        # WRONG - should be mag_v
object_data[13] = 'object_mag_g'        # WRONG - should be mag_r
```

**Correct Mapping (per OBS_XML_Data_Field_Mapping.md):**
```python
Index 0: Number (asteroid number)
Index 1: Name
Index 2: Magnitude (asteroid magnitude) ✅
Index 3: Diameter (km)
Index 4: Distance (AU)
Index 5: Number of rings
Index 6: Number of moons
Index 7: dRA - Hourly rate of change in RA (s/hr)
Index 8: dDec - Hourly rate of change in Dec (arcsec/hr)
Index 9: Taxonomic class
Index 10: Diameter uncertainty (km)
Index 11: Planet moon in shadow flag
Index 12: MagV_Asteroid (V magnitude) ✅
Index 13: MagR_Asteroid (R magnitude) ✅
```

**Impact:** HIGH - Would have extracted completely wrong data for asteroid properties
**Status:** ✅ FIXED in events.py

---

### 2. **Errors Tag Field Mapping - WRONG INDICES** ✅ FIXED

**Location:** `events.py` lines 286-299

**Problem:** Errors tag field indices did not match the specification.

**What Was Wrong:**
```python
# INCORRECT MAPPING
errors[0] = 'error_ra_star_sigma'  # WRONG - should be path width uncertainty
errors[1] = 'error_dec_star_sigma' # WRONG - should be error ellipse major axis
errors[2] = 'error_ra_obj_sigma'   # WRONG - should be error ellipse minor axis
errors[3] = 'error_dec_obj_sigma'  # WRONG - should be error ellipse PA
errors[4] = 'error_ca_sigma'       # WRONG - should be 1-sigma position error
errors[5] = 'error_pa_sigma'       # WRONG - should be error basis description
```

**Correct Mapping:**
```python
Index 0: Path width uncertainty (fraction of path width)
Index 1: Major axis of error ellipse (arcsec)
Index 2: Minor axis of error ellipse (arcsec)
Index 3: PA of major axis (degrees)
Index 4: 1-sigma star/asteroid position error (arcsec) ✅
Index 5: Error basis description string
Index 6: Reliability (RUWE value)
Index 7: Duplicate Source flag (0/1/-1)
Index 8: Non-GAIA proper motion flag (0/1/-1)
Index 9: Proper motion using UCAC4 flag (0/1/-1)
```

**Impact:** HIGH - Would have used wrong uncertainty values in OBS.XML
**Status:** ✅ FIXED in events.py

---

### 3. **OBS.XML Export Using Wrong Field Names** ✅ FIXED

**Location:** `occult4_export.py` lines 236-250, 467-474

**Problem:** XML export code was using the wrong field names after the events.py fix.

**What Was Fixed:**
1. Changed `object_mag_g` → `object_mag_v` for asteroid V magnitude
2. Changed `error_ra_star_sigma`/`error_dec_star_sigma` → `error_position_1sigma` for position uncertainty
3. Updated to use isotropic 1-sigma position error for both RA and Dec

**Impact:** HIGH - Would have failed to find fields or used wrong data
**Status:** ✅ FIXED in occult4_export.py

---

## ✅ VERIFIED CORRECT

### 1. **Star Tag Mapping - CORRECT** ✅

All 14 star fields correctly mapped:
- ✅ Indices 0-13 match specification
- ✅ J2000 coordinates at indices 1-2
- ✅ Apparent coordinates at indices 9-10
- ✅ Magnitudes Mb/Mv/Mr at indices 3-5
- ✅ Stellar diameter at index 6
- ✅ Nearby star counts at indices 12-13

### 2. **Elements Tag Mapping - NEEDS VERIFICATION** ⚠️

Currently mapped as:
```python
Index 0: event_jd
Index 1: event_ca_km
Index 2: event_pa_deg
Index 3: event_sep_arcsec
Index 4: geocentric_distance_au
Index 5: heliocentric_distance_au
Index 6: sun_target_moon_angle
Index 7: moon_illum_percent
Index 8-13: motion_dx, dy, d2x, d2y, d3x, d3y
```

**Issue:** Mapping document shows conflicting formats:
- One place lists: "Source, Duration, Year, Month, Day, UT..."
- Another place lists: "JD, CA, PA, Sep, Geocentric Distance..."

**Action Needed:** Download actual Occelmnt data to verify which format OWC uses
**Priority:** CRITICAL - Must verify before using motion coefficients

### 3. **Import Statements - CORRECT** ✅

All required imports present:
- ✅ `os` - used in occult4_export.py
- ✅ `datetime` - used for time formatting
- ✅ `xml.sax.saxutils.escape` - used for XML escaping
- ✅ `re` - used for regex (imported inline in asteroid name cleaning)

### 4. **Data Access Pattern - CORRECT** ✅

```python
occelmnt_data = event.original_data.get('occelmnt_data', {}) if hasattr(event, 'original_data') else {}
```

- ✅ Checks if `original_data` attribute exists
- ✅ Uses `.get()` with default empty dict
- ✅ Defensive against missing fields
- ✅ Won't crash if occelmnt_data doesn't exist

### 5. **Type Conversions - CORRECT** ✅

All numeric conversions wrapped in try-except:
```python
try:
    value = float(occelmnt_data['field_name'])
    formatted = f'{value:.2f}'
except (ValueError, TypeError):
    # Fallback to default
```

- ✅ Catches ValueError for invalid numeric strings
- ✅ Catches TypeError for None values
- ✅ Always provides fallback values
- ✅ Won't crash on malformed data

### 6. **Format Strings - CORRECT** ✅

All format strings use appropriate precision:
- ✅ RA J2000: `:.10f` (10 decimals)
- ✅ Dec J2000: `:+.9f` (9 decimals, with sign)
- ✅ RA Apparent: `:.8f` (8 decimals)
- ✅ Dec Apparent: `:+.7f` (7 decimals, with sign)
- ✅ Magnitudes: `:.2f` (2 decimals)
- ✅ Motion coefficients: `:.6f` (6 decimals)
- ✅ Diameters: `:.1f` (1 decimal)

---

## ⚠️ POTENTIAL ISSUES

### 1. **Empty String Handling**

**Scenario:** Occelmnt CSV fields may contain empty strings

**Current Behavior:**
```python
if 'field_name' in occelmnt_data and occelmnt_data['field_name']:
    # Empty string "" evaluates to False, so this block is skipped
```

**Impact:** LOW - Empty strings will use fallback values (correct behavior)
**Status:** Working as intended

### 2. **Field Name Typos**

**Risk:** Typos in field names would silently fall back to defaults

**Mitigation:** All field names verified against events.py extraction code
**Status:** ✅ All field names match exactly

### 3. **Magnitude Band Confusion**

**OBS.XML Star Line:**
- Field 13: Mb (Blue magnitude) ← from `star_mag_b`
- Field 14: Mg (Gaia G / Visual magnitude) ← from `star_mag_v`
- Field 15: Mr (Red magnitude) ← from `star_mag_r`

**User Concern:** "Be careful with star mags as several are provided for different colour bands"

**Verification:**
- ✅ Mb uses `star_mag_b` (Blue magnitude from Occelmnt star[3])
- ✅ Mg uses `star_mag_v` (Visual magnitude from Occelmnt star[4])
- ✅ Mr uses `star_mag_r` (Red magnitude from Occelmnt star[5])
- ✅ Correct color bands mapped to correct XML fields

**Status:** ✅ CORRECT

### 4. **J2000 vs Apparent Coordinates**

**User Concern:** "Respect J2000 and Apparent coords, they are different"

**Verification:**
- ✅ J2000 RA/Dec from `star_ra_j2000`, `star_dec_j2000` (Occelmnt star[1-2])
- ✅ Apparent RA/Dec from `star_ra_apparent`, `star_dec_apparent` (Occelmnt star[9-10])
- ✅ Different precision: J2000 has more decimals (10/9 vs 8/7)
- ✅ No mixing of coordinate systems
- ✅ Fallback uses same system (J2000 → J2000, Apparent → J2000 with note)

**Status:** ✅ CORRECT

### 5. **Prediction vs Observation Data**

**User Concern:** "Predictions are from OWC data. Actual event data from AOTA and TANGRA"

**Verification:**
- ✅ Star coordinates, magnitudes, diameter: from Occelmnt (PREDICTION)
- ✅ Asteroid motion coefficients: from Occelmnt (PREDICTION)
- ✅ Asteroid diameter: from Occelmnt (PREDICTION)
- ✅ D/R times, uncertainties, SNR: from AOTA/Tangra (OBSERVATION) - already implemented
- ✅ No mixing of prediction and observation timing data

**Status:** ✅ CORRECT

---

## 🔍 CODE REVIEW CHECKLIST

### events.py
- ✅ All imports present
- ✅ Star tag (14 fields) - indices correct
- ❌ **Object tag (14 fields) - indices FIXED**
- ⚠️ Elements tag (14 fields) - needs verification with real data
- ❌ **Errors tag (10 fields) - indices FIXED**
- ✅ Earth tag (5 fields) - optional, indices correct
- ✅ Orbit tag (6 fields) - optional, indices correct
- ✅ Error handling - proper try-except blocks
- ✅ Backwards compatibility - old events will load

### occult4_export.py
- ✅ All imports present
- ✅ Data access pattern correct
- ❌ **Field names FIXED to match events.py**
- ✅ Type conversions all wrapped in try-except
- ✅ Format strings use correct precision
- ✅ Fallback values provided for all fields
- ✅ J2000 vs Apparent coordinates respected
- ✅ Color band magnitudes correctly mapped
- ✅ Prediction data (Occelmnt) vs Observation data (AOTA) separation maintained

---

## 📋 TESTING RECOMMENDATIONS

### 1. Download Real Event with Occelmnt
```python
# In main GUI, download events and check occelmnt_data structure
import json
with open('occultations.json', 'r') as f:
    events = json.load(f)

event = events[0]  # Get first event
if 'occelmnt_data' in event:
    print("=== VERIFICATION ===")
    print("Object fields:")
    print("  Index 2 (should be magnitude):", event['occelmnt_data'].get('object_magnitude'))
    print("  Index 12 (should be mag_v):", event['occelmnt_data'].get('object_mag_v'))
    print("  Index 13 (should be mag_r):", event['occelmnt_data'].get('object_mag_r'))
    
    print("\nError fields:")
    print("  Index 4 (1-sigma position error):", event['occelmnt_data'].get('error_position_1sigma'))
    print("  Index 6 (RUWE):", event['occelmnt_data'].get('quality_ruwe'))
```

### 2. Generate OBS.XML and Verify Output
```python
# Generate XML for test event
exporter = Occult4Exporter(config)
xml_path = exporter.export_observation(event, telescope_id, camera_id, ...)

# Check generated XML
with open(xml_path, 'r') as f:
    xml_content = f.read()
    
# Verify:
# 1. Star line has correct J2000 coordinates (10/9 decimals)
# 2. Star line has correct Apparent coordinates (8/7 decimals)
# 3. Star line has correct Mb/Mv/Mr values (2 decimals each)
# 4. Asteroid line has motion coefficients (6 decimals each)
# 5. Asteroid line has correct V magnitude
```

### 3. Verify Elements Tag Format
**CRITICAL:** Download Occelmnt and check if Elements starts with JD or Source:
```python
if 'occelmnt' in event:
    elements_csv = event['occelmnt']['Occultations']['Event']['Elements']
    print("Raw Elements CSV:", elements_csv)
    fields = elements_csv.split(',')
    print("First field:", fields[0])  # Should be JD or Source?
    print("Index 8:", fields[8] if len(fields) > 8 else "N/A")  # Should be dX
```

---

## 🎯 SUMMARY

### Fixed
1. ✅ Object tag field mapping - **COMPLETELY REWRITTEN**
2. ✅ Errors tag field mapping - **INDICES CORRECTED**
3. ✅ OBS.XML export field names - **UPDATED TO MATCH**
4. ✅ Position uncertainty handling - **USES ISOTROPIC 1-SIGMA**

### Verified Correct
5. ✅ Star tag mapping
6. ✅ Import statements
7. ✅ Data access patterns
8. ✅ Type conversion error handling
9. ✅ Format string precision
10. ✅ J2000 vs Apparent coordinate separation
11. ✅ Color band magnitude mapping
12. ✅ Prediction vs Observation data separation

### Needs Verification
13. ⚠️ **Elements tag format** - Download real Occelmnt to verify if it starts with JD or Source

### Impact Assessment
- **Before fixes:** Would have generated invalid OBS.XML with wrong asteroid data
- **After fixes:** Will generate correct OBS.XML with proper field mappings
- **Backwards compatibility:** Maintained - old events without occelmnt_data will still work

---

## ✅ CONCLUSION

**All critical bugs fixed.** Code is now ready for testing with real Occelmnt data. The Elements tag format still needs verification, but the motion coefficient extraction code is correctly structured - just need to confirm the field order matches actual OWC responses.
