## GPS Timing Analysis - Camera Timestamp Validation

Python toolkit for analyzing GPS flash timing to validate camera timestamp accuracy. Critical for ensuring sub-millisecond timing precision in occultation observations.

**Location:** `gps-timing-analysis/`

### Key Features

- **TANGRA Light Curve Analysis**: Import and analyze TANGRA CSV files for timestamp quality
- **GPS Flash Detection**: Automated detection and analysis of GPS 1PPS (one pulse per second) flashes
- **Timestamp Offset Calculation**: Measure timing differences between recorded and actual GPS time
- **Rolling Shutter Characterization**: Calculate inter-line timing delays for rolling shutter cameras
- **ADV Video Processing**: Direct processing of ADV format astronomical videos
- **Quality Validation**: Detect dropped frames, timing anomalies, and system issues

### Use Cases

1. **Camera Calibration**: Determine timestamp offsets for new cameras and recording systems
2. **System Validation**: Verify GPS receiver and timestamp accuracy before critical observations
3. **Rolling Shutter Analysis**: Characterize line-by-line timing for accurate Y-position corrections
4. **Quality Assurance**: Detect timing issues in recorded occultation videos

### Quick Start

```bash
# Install dependencies
cd gps-timing-analysis
pip install -r requirements.txt

# Import and use
from light_curves import read_tangra_csv, analyse_timestamps, analyse_gps_flash

# Analyze TANGRA light curve
tangra_data = read_tangra_csv('lightcurve.csv')
stats = analyse_timestamps(tangra_data)
print(f"Median frame time: {stats['tdelta_median']} ms")

# Calculate GPS offsets
lcv = analyse_gps_flash(tangra_data, exposure_ms=50)
```

**See the [GPS Timing Analysis README](gps-timing-analysis/README.md) for complete documentation.**

### Integration with Occultation Manager

While these tools are currently separate, they complement each other:
- **Occultation Manager**: Automates event recording and report generation
- **GPS Timing Analysis**: Validates that your recordings have accurate timestamps

Use GPS Timing Analysis to characterize your camera system, then use those validated settings with Occultation Manager for reliable automated observations.

