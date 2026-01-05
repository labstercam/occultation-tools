# SNR Export Fix - January 5, 2026

## Issue: SNR Not Populated in OBS.XML

**Problem:** SNR (Signal-to-Noise Ratio) was available in AOTA Report but not being exported to the OBS.XML `<Conditions>` line.

**Reported by User:** "The SNR is not being populated in the OBS.XML. It is available in the AOTA report but not in the AOTA XML. If the AOTA xml is being used as the source for D/R times, add in the SNR from the AOTA report if it is available"

---

## Root Cause

The `_build_conditions_line()` method in [occult4_export.py](occult4_export.py) only accepted `observer_data` parameter. The AOTA Report data containing SNR (`aota_report_data`) was never passed to this method, so the SNR field remained blank in generated OBS.XML files.

**Data Flow Before Fix:**
```
AOTA Report (contains SNR)
    ↓
aota_report_parser.py extracts SNR
    ↓
aota_report_data dict (contains 'snr' key)
    ↓
passed to export_observation()
    ↓
passed to _build_observer_section()
    ↓
❌ NOT passed to _build_conditions_line()
    ↓
SNR field blank in OBS.XML
```

---

## Fix Applied

### Files Modified
- **[occult4_export.py](occult4_export.py)** - lines 596-770

### Changes Made

#### 1. Updated `_build_observer_section()` method (line 603)
```python
# Before:
lines.append(self._build_conditions_line(observer_data))

# After:
lines.append(self._build_conditions_line(aota_report_data, observer_data))
```

#### 2. Updated `_build_conditions_line()` signature and logic (lines 739-770)

**Before:**
```python
def _build_conditions_line(self, observer_data):
    """Build the Conditions line with observing conditions"""
    # Default values
    sn = ''  # Signal-to-noise ratio
    
    # Override with observer_data if provided
    if observer_data:
        sn = observer_data.get('sn', sn)
    
    # ... rest of method
```

**After:**
```python
def _build_conditions_line(self, aota_report_data, observer_data):
    """Build the Conditions line with observing conditions"""
    # Default values
    sn = ''  # Signal-to-noise ratio
    
    # Get SNR from AOTA report data if available
    if aota_report_data and 'snr' in aota_report_data:
        snr_value = aota_report_data.get('snr')
        if snr_value is not None:
            # Format to 1 decimal place
            sn = f"{snr_value:.1f}"
    
    # Override with observer_data if provided (observer_data takes precedence)
    if observer_data:
        # ... other fields ...
        # Only override SNR if explicitly provided in observer_data
        if 'sn' in observer_data:
            sn = observer_data.get('sn', sn)
    
    # ... rest of method
```

---

## Data Flow After Fix

```
AOTA Report (contains SNR)
    ↓
aota_report_parser.py extracts SNR
    ↓
aota_report_data dict (contains 'snr': 4.5)
    ↓
passed to export_observation()
    ↓
passed to _build_observer_section()
    ↓
✅ NOW passed to _build_conditions_line(aota_report_data, observer_data)
    ↓
SNR extracted: sn = f"{4.5:.1f}" → "4.5"
    ↓
SNR populated in OBS.XML: <Conditions>_|_|4.5|0|</Conditions>
```

---

## OBS.XML Format

The `<Conditions>` line uses pipe-delimited format:

```xml
<Conditions>stability|transparency|sn|time_adjustment|comment</Conditions>
```

**Example with SNR:**
```xml
<Conditions>_|_|4.5|0|</Conditions>
```

Where:
- `_` = unstated stability
- `_` = unstated transparency
- `4.5` = SNR (Signal-to-Noise Ratio) - **now populated!**
- `0` = time adjustment (±s.ss)
- (empty) = comment

---

## Priority & Override Logic

1. **First priority:** Extract SNR from `aota_report_data` (AOTA Report)
2. **Second priority:** Override with `observer_data['sn']` if explicitly provided
3. **Default:** Empty string if neither source has SNR

This ensures:
- ✅ AOTA Report SNR is automatically used when available
- ✅ Manual override still possible via `observer_data`
- ✅ Blank SNR remains valid when no data available

---

## Testing

Created comprehensive test: **[test_snr_export.py](test_snr_export.py)**

### Test Case 1: With AOTA Report Data
```python
aota_report_data = {
    'd_hours': '10', 'd_minutes': '23', 'd_seconds': '45.12',
    'r_hours': '10', 'r_minutes': '23', 'r_seconds': '50.34',
    'snr': 4.5  # SNR value to test
}

# Expected result in OBS.XML:
# <Conditions>_|_|4.5|0|</Conditions>
```

**Result:** ✅ SNR correctly exported as "4.5"

### Test Case 2: Without AOTA Report Data
```python
# No aota_report_data parameter provided

# Expected result in OBS.XML:
# <Conditions>_|_||0|</Conditions>
```

**Result:** ✅ SNR correctly blank (empty string)

---

## Impact Assessment

### Before Fix
- ❌ SNR was **always blank** in OBS.XML
- ❌ Valuable AOTA Report data was ignored
- ❌ Manual entry required even when data was available

### After Fix
- ✅ SNR **automatically populated** from AOTA Report
- ✅ Formatted to 1 decimal place (per Occult 4 spec)
- ✅ Still allows manual override via `observer_data`
- ✅ Backwards compatible (works with or without AOTA data)

### Backwards Compatibility
- Old code calling without `aota_report_data`: Still works (SNR blank)
- Old code with `observer_data['sn']`: Still works (manual override)
- New AOTA workflow: SNR automatically populated ✨

---

## Related Code

### AOTA Report Parser
**[aota_report_parser.py](aota_report_parser.py)** already extracts SNR:

```python
def get_event_summary(aota_report_data, event_index=0):
    """Get timing and SNR data for a specific event."""
    # ... extract D/R times ...
    return {
        'd_hours': d_time['hours'],
        'd_minutes': d_time['minutes'],
        'd_seconds': d_time['seconds'],
        'd_uncertainty': event.get('d_uncertainty'),
        'r_hours': r_time['hours'],
        'r_minutes': r_time['minutes'],
        'r_seconds': r_time['seconds'],
        'r_uncertainty': event.get('r_uncertainty'),
        'snr': event.get('snr_ave')  # ← SNR extracted here
    }
```

The SNR comes from the "SN at event locations" section of AOTA Report:
```
SN at event locations D(1,2):(4.46,4.55) R(1,2):(4.46,4.55)  Ave:4.5
                                                             ↑
                                                     This value is extracted
```

---

## Conclusion

✅ **Fix Verified and Complete**

- SNR now correctly flows from AOTA Report → OBS.XML
- Maintains all existing functionality
- Adds automated data population where previously required manual entry
- Test coverage demonstrates correct behavior

**Status:** Ready for production use with AOTA Report workflow.
