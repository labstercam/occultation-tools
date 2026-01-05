## GPS Timing Analysis - Camera Timestamp Validation

Python toolkit for analyzing GPS flash timing to validate camera timestamp accuracy. Critical for ensuring sub-millisecond timing precision in occultation observations.

### Key Features

- **Tangra Light Curve Analysis**: Import and analyze Tangra CSV files for timestamp quality
- **Video Format Extraction**: Automatic extraction of video format from Tangra measurement parameters
- **GPS Flash Detection**: Automated detection and analysis of GPS 1PPS (one pulse per second) flashes
- **Timestamp Offset Calculation**: Measure timing differences between recorded and actual GPS time
- **Rolling Shutter Characterization**: Calculate inter-line timing delays for rolling shutter cameras
- **Camera Acquisition Delay**: Extract timing corrections from Tangra measurement parameters
- **Exposure/Integration Detection**: Determine recording mode from timing consistency
- **Quality Validation**: Detect dropped frames, timing anomalies, and system issues

### Use Cases

1. **Camera Calibration**: Determine timestamp offsets and acquisition delays for new cameras
2. **System Validation**: Verify GPS receiver and timestamp accuracy before observations
3. **Rolling Shutter Analysis**: Characterize line-by-line timing for Y-position corrections
4. **Quality Assurance**: Detect timing issues in recorded videos
5. **Report Integration**: Extract timing data for automated report population

### Core Functions

#### read_tangra_csv(file_path)
Reads Tangra CSV light curve files with full pandas support.

**Returns Dictionary**:
- `file_read_from`: Path to CSV file
- `filename_from_tangra`: Original video filename
- `details`: Header information (camera, video format, observer)
- `apertures`: DataFrame with aperture definitions and coordinates
- `light_curve`: DataFrame with timestamps and photometry
- `column_names`: Light curve column headers
- `acquisition_delay`: Camera acquisition delay in milliseconds (from rows 7-8)
- `video_format`: Video format code (ADVS, SER, AAV-NTSC, AAV-PAL, PAL/CCIR, NTSC/EIA, etc.)

#### analyse_timestamps(tangra_data, percentiles=None)
Analyzes frame timing statistics from the full tangra_data dictionary.

**Parameters**:
- `tangra_data`: Full dictionary returned from `read_tangra_csv()`
- `percentiles`: Optional list of percentiles to calculate (e.g., [1, 99])

**Returns**:
- `start_time`: First frame timestamp
- `end_time`: Last frame timestamp
- `tdelta_median`: Median frame time (exposure) in milliseconds
- `tdelta_std`: Standard deviation of frame times
- `tdelta_percentiles`: Distribution analysis
- `video_format`: Video format from input data
- `exposure_integration`: 'Exposure' or 'Integration' based on timing variance

#### analyse_gps_flash(tangra_data, col='signal_1', exposure_ms=50, flash_ms=100, background=None, do_plots=False)
Calculates GPS timing offsets for system validation.

**Parameters**:
- `tangra_data`: Full dictionary from `read_tangra_csv()`
- `col`: Column name containing GPS flash signal (default: 'signal_1')
- `exposure_ms`: Camera exposure time in milliseconds
- `flash_ms`: Expected GPS flash duration
- `background`: Background level (None for auto-detect)
- `do_plots`: Whether to generate diagnostic plots

### Integration with Occultation Manager

The Occultation Manager includes `light_curves_iron.py`, an IronPython-compatible version using only Python standard library (no pandas/numpy). This enables direct integration of Tangra timing data into report generation:

- Observation start/end times (HH:MM:SS.SS)
- Exposure time in seconds
- Camera acquisition delay in seconds

**Workflow**:
1. Record occultation with GPS calibration flashes (optional)
2. Analyze in Tangra to generate CSV light curve
3. Use GPS Timing Analysis to validate camera timing (if needed)
4. Generate report in Occultation Manager with integrated timing data

