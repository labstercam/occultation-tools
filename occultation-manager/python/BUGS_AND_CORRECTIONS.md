# Bugs and Issues Found in Occelmnt Data Handling

## Date: December 31, 2025

## Summary
Analysis of the Occelmnt data extraction and field mapping revealed several bugs and a critical field mapping error.

---

## 1. ⚠️ CRITICAL: Star Tag Field Count Error (CORRECTED)

### Issue
The mapping document incorrectly listed the Star tag as having 16 fields, when it actually has 14 fields.

### Incorrect Mapping (Before)
- Indices 11-15 were listed as:
  - 11: MdropV - Magnitude drop in V
  - 12: MdropR - Magnitude drop in R
  - 13: Mag drops adjusted flag
  - 14: Number of bright nearby stars
  - 15: Number of all nearby stars

### Correct Mapping (After)
- Indices 11-13 are actually:
  - 11: MagDropsAdjusted_NearbyStars (0=not adjusted, 1=adjusted)
  - 12: BrightNearbyCount (count or -1)
  - 13: TotalNearbyCount (count or -1)

### Root Cause
Misreading of the Occelmnt specification. The XML format spec shows:
```
<Star> Identifier, RA, Dec, Mb, Mv, Mr, dia, double star code, K2 flag, Apparent RA, Apparent Dec,MagDropsAdjusted_NearbyStars,BrightNearbyCount, TotalNearbyCount</Star>
```

This is 14 comma-separated fields, not 16.

### Impact
- **HIGH**: Any code using indices 11+ for Star tag would access wrong data
- **FIXED**: Mapping document has been corrected
- **ACTION NEEDED**: Review any implementation code that accesses star[11] or higher indices

---

## 2. 🐛 Missing Error Handling in events.py

### Location
`events.py`, lines 221-228 in `process_owc_events()` method

### Current Code
```python
if eventOccelmnt:
    elements = eventOccelmnt['Occultations']['Event']['Elements'].split(',')
    star = eventOccelmnt['Occultations']['Event']['Star'].split(',')
    object_data = eventOccelmnt['Occultations']['Event']['Object'].split(',')
    owcloudurl = 'https://cloud.occultwatcher.net' + eventOccelmnt['Occultations']['Event']['OWC']
    object_no = object_data[0]
else:
    object_no = ""
    owcloudurl = ""
```

### Issues

#### 2a. KeyError Risk
**Problem:** Code assumes all XML tags exist without checking
- `eventOccelmnt['Occultations']['Event']['Elements']`
- `eventOccelmnt['Occultations']['Event']['Star']`
- `eventOccelmnt['Occultations']['Event']['Object']`  
- `eventOccelmnt['Occultations']['Event']['OWC']`

**Impact:** If any tag is missing, will raise KeyError and crash event processing

**Severity:** MEDIUM - Occelmnt structure should be consistent, but defensive coding is better

#### 2b. IndexError Risk
**Problem:** `object_no = object_data[0]` assumes Object CSV has at least one field

**Impact:** If Object CSV is empty or malformed, will raise IndexError

**Severity:** LOW - Object should always have number field, but defensive coding recommended

### Recommended Fix
```python
if eventOccelmnt:
    try:
        elements = eventOccelmnt['Occultations']['Event']['Elements'].split(',')
        star = eventOccelmnt['Occultations']['Event']['Star'].split(',')
        object_data = eventOccelmnt['Occultations']['Event']['Object'].split(',')
        owcloudurl = 'https://cloud.occultwatcher.net' + eventOccelmnt['Occultations']['Event']['OWC']
        object_no = object_data[0] if len(object_data) > 0 else ""
    except (KeyError, IndexError, AttributeError) as e:
        print(f"Warning: Error parsing Occelmnt data for event {eventId}: {e}")
        object_no = ""
        owcloudurl = ""
else:
    object_no = ""
    owcloudurl = ""
```

---

## 3. ℹ️ Unused Variables

### Location
`events.py`, lines 221-224

### Issue
Variables `elements`, `star`, `object_data` are extracted but only `object_data[0]` is used.

**Current behavior:**
```python
elements = eventOccelmnt['Occultations']['Event']['Elements'].split(',')  # Not used
star = eventOccelmnt['Occultations']['Event']['Star'].split(',')  # Not used
object_data = eventOccelmnt['Occultations']['Event']['Object'].split(',')  # Only [0] used
```

### Analysis
- **NOT A BUG**: The full `eventOccelmnt` structure is stored in the occultation dictionary at line 279
- The extracted variables were likely from early development and can be simplified
- All Occelmnt data is accessible via `event.original_data['occelmnt']`

### Recommendation
**Option 1 (Simplify):** Remove unused extractions
```python
if eventOccelmnt:
    try:
        # Extract only what's needed immediately
        object_data = eventOccelmnt['Occultations']['Event']['Object'].split(',')
        object_no = object_data[0] if len(object_data) > 0 else ""
        owcloudurl = 'https://cloud.occultwatcher.net' + eventOccelmnt['Occultations']['Event']['OWC']
    except (KeyError, IndexError, AttributeError) as e:
        print(f"Warning: Error parsing Occelmnt data: {e}")
        object_no = ""
        owcloudurl = ""
```

**Option 2 (Extract more):** Extract commonly-used fields into the occultation dictionary for easier access
```python
if eventOccelmnt:
    try:
        elements = eventOccelmnt['Occultations']['Event']['Elements'].split(',')
        star = eventOccelmnt['Occultations']['Event']['Star'].split(',')
        object_data = eventOccelmnt['Occultations']['Event']['Object'].split(',')
        
        # Store extracted values for easier access
        occultation['object_no'] = object_data[0] if len(object_data) > 0 else ""
        occultation['ra_j2000_precise'] = float(star[1]) if len(star) > 1 else ra
        occultation['dec_j2000_precise'] = float(star[2]) if len(star) > 2 else dec
        occultation['ra_apparent'] = float(star[9]) if len(star) > 9 else ra
        occultation['dec_apparent'] = float(star[10]) if len(star) > 10 else dec
        occultation['stellar_diameter_mas'] = float(star[6]) if len(star) > 6 else 0
        
        owcloudurl = 'https://cloud.occultwatcher.net' + eventOccelmnt['Occultations']['Event']['OWC']
    except (KeyError, IndexError, ValueError, AttributeError) as e:
        print(f"Warning: Error parsing Occelmnt data: {e}")
        # Values will use OWC fallbacks
```

---

## 4. ✅ Data Storage - Working Correctly

### Confirmation
The full Occelmnt structure IS being stored correctly:

**Line 279 in events.py:**
```python
occultation = {
    # ... other fields ...
    'occelmnt': eventOccelmnt, 'source': 'OWCloud',
    # ... other fields ...
}
```

This means all Occelmnt data is accessible in code via:
```python
if event.original_data.get('occelmnt'):
    occelmnt = event.original_data['occelmnt']
    elements = occelmnt['Occultations']['Event']['Elements'].split(',')
    star = occelmnt['Occultations']['Event']['Star'].split(',')
    obj = occelmnt['Occultations']['Event']['Object'].split(',')
    errors = occelmnt['Occultations']['Event']['Errors'].split(',')
```

---

## 5. 📋 Field Mapping Verification

### Verified Correct Mappings

#### Elements Tag (14 fields)
- ✅ Indices 0-13 correctly mapped
- ✅ Motion coefficients at indices 8-13 (dX, dY, d2X, d2Y, d3X, d3Y)

#### Star Tag (14 fields) - CORRECTED
- ✅ Indices 0-13 correctly mapped after correction
- ⚠️ Previous mapping had wrong field count (16 instead of 14)
- ✅ Apparent coordinates at indices 9-10
- ✅ Magnitudes at indices 3-5
- ✅ Stellar diameter at index 6

#### Object Tag (14 fields)
- ✅ Indices 0-13 correctly mapped
- ✅ Diameter at index 3
- ✅ Diameter uncertainty at index 10
- ✅ Asteroid magnitudes at indices 12-13

#### Errors Tag (10 fields)
- ✅ Indices 0-9 correctly mapped
- ✅ Quality flags at indices 6-9
- ✅ Position uncertainties at indices 1-4

---

## Action Items

### High Priority
1. ✅ **DONE**: Correct Star tag field mapping in documentation
2. 🔴 **TODO**: Add error handling to Occelmnt parsing in events.py
3. 🔴 **TODO**: Add bounds checking for CSV array access

### Medium Priority
4. 🟡 **CONSIDER**: Extract commonly-used Occelmnt fields into occultation dictionary
5. 🟡 **CONSIDER**: Add Occelmnt data validation logging

### Low Priority  
6. 🟢 **OPTIONAL**: Remove unused variable extractions for code clarity
7. 🟢 **OPTIONAL**: Add unit tests for Occelmnt parsing

---

## Testing Recommendations

### Test Cases Needed
1. **Normal case**: Valid Occelmnt with all tags present
2. **Missing tags**: Occelmnt missing optional tags (Earth, Orbit, Errors)
3. **Malformed CSV**: Empty or truncated CSV strings
4. **No Occelmnt**: eventOccelmnt = None case
5. **Invalid data types**: Non-numeric values in numeric fields

### Test Data
- Use `owc_downloaded_events.json` as real-world test data
- Create synthetic test cases for edge cases

---

## Conclusion

### Critical Issues
- ✅ Star tag field mapping error - **CORRECTED**

### Important Issues
- 🔴 Missing error handling in Occelmnt parsing - **NEEDS FIX**

### Code Quality
- 🟡 Unused variables - **CONSIDER CLEANUP**
- ✅ Data storage working correctly - **NO CHANGES NEEDED**

The mapping document has been corrected and is now accurate. The code should be updated to add defensive error handling before being used in production.
