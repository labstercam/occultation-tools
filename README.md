# occultation-tools
Tools for automating occultation observations and validating timing accuracy.

## Tools in this Repository

### 1. Occultation Manager (SharpCap Add-in)
Location: `occultation-manager/`

### 2. GPS Timing Analysis (Python Toolkit)
Location: `gps-timing-analysis/`

---

## Occultation Manager - SharpCap Add-in for Occult Watcher Cloud
SharpCap Occultation Manager automates the complete occultation observation workflow. It downloads personal observations from Occult Watcher Cloud, generates SharpCap sequences, and produces pre-filled Excel reports with integrated timing data from Tangra light curve analysis.

### Key Features

**Event Management**
- Downloads personal observations from Occult Watcher Cloud
- Manages event list with filtering and sorting
- Automatic sequence generation for SharpCap

**Report Generation**
- Streamlined single-dialog workflow combining all settings
- Integrates AOTA timing data (D/R times)
- Imports Tangra CSV light curves for observation timing and camera delay
- Supports North America (IOTA) and Trans-Tasman (RASNZ) report formats
- Auto-fills observer, telescope, and camera information
- Remembers previous settings for faster workflow

**Timing Integration**
- Extracts start/end times from Tangra CSV files
- Populates exposure time and camera acquisition delay
- Automatic HH:MM:SS.SS time formatting
- Camera delay correction from Tangra measurement parameters

**See the [occultation-manager README](occultation-manager/ReadMe.md) for full documentation.**

---

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

# Analyze Tangra light curve
tangra_data = read_tangra_csv('lightcurve.csv')
stats = analyse_timestamps(tangra_data)
print(f"Median frame time: {stats['tdelta_median']:.3f} ms")

# Calculate GPS offsets (if GPS flash present)
lcv = analyse_gps_flash(tangra_data, exposure_ms=50)
```

**See the [GPS Timing Analysis README](gps-timing-analysis/ReadMe.md) for complete documentation.**

### Integration with Occultation Manager

The tools work together seamlessly:
- **GPS Timing Analysis**: Validates camera timestamp accuracy and characterizes system timing
- **Occultation Manager**: Uses Tangra CSV files (which include timing data) to auto-populate reports

The Occultation Manager now includes `light_curves_iron.py`, an IronPython-compatible version of the timing analysis functions, allowing direct integration of Tangra light curve data into the report generation workflow.

---

## Repository Structure

```
occultation-tools/
├── occultation-manager/      # SharpCap add-in
│   ├── python/              # Python/IronPython code
│   └── ReadMe.md           # Manager documentation
│
├── gps-timing-analysis/     # Timing validation toolkit
│   ├── python/
│   │   └── light_curves.py # Core analysis functions
│   ├── requirements.txt    # Python dependencies
│   ├── ReadMe.md          # Timing tool documentation
│   └── examples/          # Example notebooks
│
└── README.md              # This file
```

## Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## License

See individual tool directories for license information.

## Author

Michael Camilleri

## Support

For issues and questions:
- Open an issue on GitHub
- Check the individual tool README files for detailed documentation
