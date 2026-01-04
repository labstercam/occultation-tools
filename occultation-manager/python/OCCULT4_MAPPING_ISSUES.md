# Occult4 Mapping Issues and Errors

## Critical Issues Found

### **ISSUE 1: Time Source Always Defaults to GPS (Code 'a')**

**Severity:** ⚠️ **HIGH** - Causes incorrect reporting

**Current Code (lines 709-711):**
```python
# Time source
time_source = 'a'  # GPS (default)
if observer_data:
    time_source = observer_data.get('time_source', time_source)
```

**Problem:**
- The code expects `observer_data` to contain a field called `time_source` with single-letter codes ('a', 'b', 'c', etc.)
- **This field does not exist** in the camera configuration or observer data
- Camera configuration has a `timing` field with values like:
  - "GPS - other linking"
  - "GPS - Video Time Inserter"
  - "GPS - KIWI"
  - "WWV"
  - "Visual"
  - "Audio"
  - "Other"
- **Result:** Time source is ALWAYS reported as 'a' (GPS), even if user selected WWV, Visual, or Audio

**Impact:**
- If observer uses WWV radio timing → Incorrectly reported as GPS
- If observer uses Visual timing → Incorrectly reported as GPS
- If observer uses Audio timing → Incorrectly reported as GPS
- **100% of non-GPS timing methods are miscategorized**

**Required Fix:**
Add mapping logic from camera `timing` field to Occult4 time source codes:
```python
timing_to_code = {
    'GPS - other linking': 'a',
    'GPS - Video Time Inserter': 'a',
    'GPS - KIWI': 'a',
    'WWV': 'd',  # Radio time signal
    'Visual': 'f',  # Visual timing (should this be 'f' for stopwatch?)
    'Audio': 'g',  # Other
    'Other': 'g'
}
```

**Question:** Visual timing maps to code 'f' which is "Stopwatch" in Occult4. Is this correct, or should Visual timing be coded differently?

---

### **ISSUE 2: Camera Type Field Does Not Exist**

**Severity:** ⚠️ **MEDIUM** - Causes all observations to default to one method

**Current Code (lines 696-706):**
```python
# Observing method
observing_method = 'b'  # Digital SLR-camera video (default)
camera_data = self._get_camera_data(camera_id)
if camera_data:
    # Try to determine method from camera type
    camera_type = camera_data.get('type', '').lower()
    if 'video' in camera_type:
        observing_method = 'b'
    elif 'photometer' in camera_type:
        observing_method = 'c'
    elif 'dslr' in camera_type or 'sequential' in camera_type:
        observing_method = 'd'
```

**Problem:**
- The code looks for camera_data['type'] field
- **Camera configuration does NOT have a 'type' field**
- Camera configuration fields are:
  - `name` - Camera name (e.g., "ZWO ASI178MM")
  - `detector` - Detector type (free text)
  - `timing` - Timing method (e.g., "GPS - other linking")
  - `timing_device` - Device name (e.g., "SharpCap")
  - `video_format` - Video format (SER, AVI, FITS, etc.)
  - `exposure_integration` - Integration method
  - `other_info` - Additional info
- **Result:** `camera_type` is always empty string, so observing_method always defaults to 'b' (Digital SLR-camera video)

**Impact:**
- Photometer observations → Incorrectly reported as 'b' (Digital SLR video) instead of 'c'
- Sequential/DSLR images → Incorrectly reported as 'b' instead of 'd'
- Visual observations → Incorrectly reported as 'b' instead of 'f'
- Drift scan observations → Incorrectly reported as 'b' instead of 'e'
- **100% of non-video observations are miscategorized**

**Possible Solutions:**

**Option 1:** Try to infer from camera `name` field
- Look for keywords like "photometer", "DSLR", etc. in camera name
- **Risk:** Unreliable - camera names vary widely (e.g., "ZWO ASI178MM" doesn't indicate method)

**Option 2:** Try to infer from `detector` field
- Similar to Option 1
- **Risk:** Same unreliability issue

**Option 3:** Add a new field to camera configuration
- Add `observation_type` or `camera_category` field with options:
  - "Video Camera"
  - "Photometer"
  - "DSLR/Sequential Images"
  - "Drift Scan"
  - "Visual"
  - "Other"
- **Benefit:** Explicit, reliable mapping
- **Drawback:** Requires UI changes and config migration

**Option 4:** Use `detector` or `video_format` as hints
- If video_format is empty → might be photometer
- If exposure_integration indicates stacking → might be sequential
- **Risk:** Indirect inference, still unreliable

**Recommendation:** Option 3 (add explicit field) is most reliable

---

### **ISSUE 3: Observing Method Code Order Can Cause Misclassification**

**Severity:** ⚠️ **LOW** - Only affects edge cases

**Current Code:**
```python
if 'video' in camera_type:
    observing_method = 'b'
elif 'photometer' in camera_type:
    observing_method = 'c'
elif 'dslr' in camera_type or 'sequential' in camera_type:
    observing_method = 'd'
```

**Problem:**
- If camera type contains both keywords (e.g., "video photometer"), it will match first check
- Example: "video photometer" → Returns 'b' (video) instead of 'c' (photometer)
- More specific terms should be checked first

**Better Ordering:**
```python
# Check most specific first
if 'photometer' in camera_type:
    observing_method = 'c'
elif 'dslr' in camera_type or 'sequential' in camera_type:
    observing_method = 'd'
elif 'video' in camera_type:
    observing_method = 'b'  # Most generic
```

**Impact:**
- Currently theoretical since `type` field doesn't exist
- Would become relevant if field is added

---

### **ISSUE 4: Missing Observing Method Codes**

**Severity:** ℹ️ **INFO** - Incomplete coverage

**Occult4 codes not handled:**
- **Code 'a'** - Analogue & digital video (generic)
  - Never mapped
  - Should this be the default instead of 'b'?
  
- **Code 'e'** - Drift scan
  - Never mapped
  - Drift scan observations would be miscategorized
  
- **Code 'f'** - Visual
  - Never mapped
  - Visual observations would be miscategorized
  
- **Code 'g'** - Other
  - Never used as fallback
  - Unknown observation types have no catch-all

**Question:** 
- Should default be 'a' (generic video) instead of 'b' (Digital SLR-camera video)?
- How should code 'a' vs 'b' be distinguished?

**Recommendation:**
Add all codes with appropriate mapping logic:
```python
if 'drift' in camera_type or 'scan' in camera_type:
    observing_method = 'e'
elif 'visual' in camera_type:
    observing_method = 'f'
elif 'photometer' in camera_type:
    observing_method = 'c'
elif 'dslr' in camera_type or 'sequential' in camera_type:
    observing_method = 'd'
elif 'video' in camera_type:
    observing_method = 'b'
else:
    observing_method = 'g'  # Other (fallback)
```

---

## Summary of Miscategorizations

### Current State:

| Actual Method | Should Be | Currently Reports | Error? |
|---------------|-----------|-------------------|--------|
| Video camera | 'b' | 'b' | ✅ Correct |
| Photometer | 'c' | 'b' | ❌ **WRONG** |
| DSLR/Sequential | 'd' | 'b' | ❌ **WRONG** |
| Drift scan | 'e' | 'b' | ❌ **WRONG** |
| Visual | 'f' | 'b' | ❌ **WRONG** |
| GPS timing | 'a' | 'a' | ✅ Correct |
| WWV timing | 'd' | 'a' | ❌ **WRONG** |
| Visual timing | 'f'? | 'a' | ❌ **WRONG** |
| Audio timing | 'g' | 'a' | ❌ **WRONG** |

**Error Rate:**
- Observing Method: **83% error rate** (5 out of 6 non-video methods wrong)
- Time Source: **75% error rate** (3 out of 4 non-GPS methods wrong)

---

## Recommended Fixes

### Priority 1: Fix Time Source Mapping (CRITICAL)

Add function to map camera timing strings to Occult4 codes:

```python
def _map_timing_to_time_source(self, camera_data):
    """Map camera timing field to Occult4 time source code"""
    if not camera_data:
        return 'a'  # Default GPS
    
    timing = camera_data.get('timing', '').lower()
    
    # Map timing strings to codes
    if 'gps' in timing:
        return 'a'
    elif 'wwv' in timing:
        return 'd'  # Radio time signal
    elif 'visual' in timing:
        return 'f'  # Stopwatch (?)
    elif 'audio' in timing:
        return 'g'  # Other
    elif 'ntp' in timing:
        return 'b'  # NTP
    else:
        return 'a'  # Default GPS
```

### Priority 2: Add Camera Category Field (HIGH)

Modify equipment dialog to include observation method:

**New Field in Camera Configuration:**
- Name: `observation_method` or `camera_category`
- Type: Dropdown
- Options:
  - "Analogue/Digital Video" → 'a'
  - "Digital SLR-camera Video" → 'b'
  - "Photometer" → 'c'
  - "Sequential Images (DSLR/CCD)" → 'd'
  - "Drift Scan" → 'e'
  - "Visual" → 'f'
  - "Other" → 'g'

**Migration Strategy:**
- Existing cameras default to 'b' (Digital SLR-camera video)
- User can update configuration as needed

### Priority 3: Improve Fallback Logic (MEDIUM)

If camera category field is not added, improve inference:

```python
def _infer_observing_method(self, camera_data):
    """Infer observing method from available camera data"""
    if not camera_data:
        return 'b'  # Default
    
    # Check detector field
    detector = camera_data.get('detector', '').lower()
    name = camera_data.get('name', '').lower()
    
    # Try to infer from keywords
    if 'photometer' in detector or 'photometer' in name:
        return 'c'
    elif 'dslr' in detector or 'dslr' in name:
        return 'd'
    
    # Default to video
    return 'b'
```

**Note:** This is still unreliable but better than always defaulting to 'b'

---

## Testing Recommendations

### Test Cases to Verify Fixes:

1. **GPS Timing:**
   - Camera with "GPS - other linking" → Should report 'a' ✓

2. **WWV Timing:**
   - Camera with "WWV" timing → Should report 'd' (not 'a')

3. **Visual Timing:**
   - Camera with "Visual" timing → Should report 'f' (not 'a')

4. **Photometer:**
   - Camera configured as photometer → Should report 'c' (not 'b')

5. **Sequential Images:**
   - DSLR camera with sequential mode → Should report 'd' (not 'b')

6. **Mixed Keywords:**
   - Camera named "Video Photometer" → Should report 'c' (photometer takes priority)

---

## Impact Assessment

### Who is Affected:

**Currently affected users:**
- ❌ Anyone using photometer → Reports show wrong observation method
- ❌ Anyone using WWV timing → Reports show wrong time source
- ❌ Anyone using visual timing → Reports show wrong time source
- ❌ Anyone using DSLR sequential images → Reports show wrong observation method
- ❌ Anyone doing drift scan → Reports show wrong observation method

**Not affected:**
- ✅ Users with video cameras and GPS timing (most common setup)

**Estimated Impact:**
- If 80% of users use video+GPS: 20% of reports have errors
- If photometers are 5% of observations: 5% have critical errors
- **All non-GPS timing methods are incorrectly reported**

### Urgency:

**HIGH** - This should be fixed before widespread use:
1. Time source mapping is completely broken (always GPS)
2. Non-video observations are all miscategorized
3. Errors are silent - users won't notice unless checking XML details
4. Incorrect data goes into permanent IOTA database

---

## Questions for User

1. **Visual Timing:** Should "Visual" timing method map to:
   - Code 'f' (Stopwatch) - if observer uses stopwatch
   - Code 'g' (Other) - if "visual" means something else
   - Code 'f' (Visual observation method) - is this a timing or observation method?

2. **Camera Categories:** Should we add explicit camera category field to configuration?
   - Pros: Reliable, explicit, user-controlled
   - Cons: Requires UI changes, config migration, extra user input

3. **Default Observing Method:** Should default be:
   - Code 'a' (Analogue/digital video - generic)
   - Code 'b' (Digital SLR-camera video - specific)

4. **Inference vs Explicit:** Should we:
   - Try to infer from existing fields (risky but no UI changes)
   - Add new field for explicit categorization (reliable but requires changes)

5. **Migration:** For existing camera configurations:
   - Default all to 'b' (Digital SLR-camera video)?
   - Try to infer from camera name?
   - Prompt user to categorize?
