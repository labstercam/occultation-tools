# GPS Timing Analysis - Python Module

## light_curves.py

Core Python module for analyzing Tangra CSV light curve files and GPS timing validation. Uses pandas, numpy, and scipy for comprehensive statistical analysis.

### Main Functions

#### read_tangra_csv(file_path)
Reads Tangra CSV light curve files with complete metadata extraction.

**Returns Dictionary**:
- `file_read_from`: Path to CSV file
- `filename_from_tangra`: Original video filename
- `details`: Header information (camera, video format, observer)
- `apertures`: DataFrame with aperture definitions
- `light_curve`: DataFrame with timestamps and photometry
- `column_names`: Light curve column headers
- `acquisition_delay`: Camera acquisition delay (ms) from measurement parameters table
- `video_format`: Video format from measurement parameters (ADVS, SER, AAV-NTSC, etc.)

**Tangra CSV Structure**:
- **Rows 1-2**: Header with filename and details
- **Rows 7-8**: Measurement parameters table (header and data)
  - Includes "Acquisition Delay (ms)" column
  - Includes "Video File Format" column (handles leading spaces)
- **Row 9+**: Aperture definitions
- **Remaining rows**: Light curve data with timestamps

**Video Format Mapping**:
- ADV/ADVS → ADVS
- AAV-NTSC → AAV-NTSC
- AAV-PAL → AAV-PAL
- PAL/CCIR → PAL/CCIR
- NTSC/EIA → NTSC/EIA
- SER, AVI, MP4, FITS → as-is

#### analyse_timestamps(light_curve_data, percentiles=[1, 99])
Statistical analysis of frame timing.

**Returns Dictionary**:
- `start_time`: First frame datetime
- `end_time`: Last frame datetime
- `tdelta_median`: Median frame time (exposure) in milliseconds
- `tdelta_mean`: Mean frame time
- `tdelta_std`: Standard deviation
- `tdelta_min`, `tdelta_max`: Timing range
- `tdelta_percentiles`: Distribution analysis
- `num_frames`: Total frame count
- `video_format`: Video format from input data
- `exposure_integration`: 'Exposure' or 'Integration' based on timing consistency (std < 10% of median)

#### analyse_gps_flash(tangra_data, exposure_ms, gps_y=None, aperture_name=None)
Analyzes GPS 1PPS flashes to calculate camera timestamp offsets.

**Parameters**:
- `tangra_data`: Output from read_tangra_csv()
- `exposure_ms`: Camera exposure time
- `gps_y`: Y-coordinate of GPS flash (optional)
- `aperture_name`: Aperture containing GPS data (optional)

**Returns**: Light curve with GPS timing analysis

### Usage Example

```python
from light_curves import read_tangra_csv, analyse_timestamps

# Read Tangra CSV
data = read_tangra_csv('event_light_curve.csv')

# Get timing statistics
stats = analyse_timestamps(data)
print(f"Observation: {stats['start_time']} to {stats['end_time']}")
print(f"Exposure: {stats['tdelta_median']:.3f} ms")
print(f"Acquisition delay: {data['acquisition_delay']:.3f} ms")

# Check timing consistency
if stats['tdelta_std'] > 1.0:
    print("WARNING: High frame time variation detected")
```

### IronPython Compatibility

For SharpCap integration, see `light_curves_iron.py` in the occultation-manager package. This version uses only Python standard library (no pandas/numpy) for IronPython compatibility.
