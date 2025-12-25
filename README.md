# occultation-tools
Tools for automating occultation observations and validating timing accuracy.

## Tools in this Repository

### 1. Occultation Manager (SharpCap Add-in)
Location: `occultation-manager/`

### 2. GPS Timing Analysis (Python Toolkit)
Location: `gps-timing-analysis/`

---

## Occultation Manager - SharpCap Add-in for Occult Watcher Cloud
SharpCap Occultation Manager for Occult Watcher is a tool for SharpCap that fully automates occultation observations. It downloads personal observations announced in Occult Watcher Cloud. It includes an Event Manager to manage events, Sequence generation to create SharpCap sequences for doing the recordings (either in the tool itself or by using the sequences directly), and configuration management.

The tool serves several purposes:
1. Enables full automation of observations from SharpCap, only requiring the use of OW Cloud to announce stations
2. Provides a much simplified work-flow for SharpCap users - other tools usually require the use of Occult Watcher Desktop or Occult 4 to generate or manage predictions, with a lot of manual work to select and run the observations, even with the OWD SharpCap addin
3. Provides a very easy and flexible way to generate SharpCap sequences to record events, with the ability for the user to edit the sequence template to their needs or edit the generate sequences

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

---

## Repository Structure

```
occultation-tools/
├── occultation-manager/      # SharpCap add-in
│   ├── python/              # Python/IronPython code
│   └── ReadMe.md           # Manager documentation
│
├── gps-timing-analysis/     # Timing validation toolkit
│   ├── light_curves.py     # Core analysis functions
│   ├── requirements.txt    # Python dependencies
│   ├── README.md          # Timing tool documentation
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
