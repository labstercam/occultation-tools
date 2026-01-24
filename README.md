# occultation-tools

![Version](https://img.shields.io/badge/version-0.2.0--beta.1-blue)
![License](https://img.shields.io/badge/license-BSD--3--Clause-green)

Tools for automating occultation observations and validating timing accuracy.

📋 **[View CHANGELOG](CHANGELOG.md)** for release history and version details.

## Tools in this Repository

### 1. Occultation Manager
**SharpCap add-in for automated occultation workflow**

Automates the complete occultation observation workflow: downloads personal observations from Occult Watcher Cloud, generates customizable SharpCap sequences, and produces pre-filled Excel reports with integrated timing data from Tangra analysis.

📖 **[Read Full Documentation](occultation-manager/ReadMe.md)**  
📦 **[Download Latest Release](occultation-manager/)**  
🚀 **[Installation Instructions](occultation-manager/ReadMe.md#installation)**

**Quick Overview:**
- Downloads events from Occult Watcher Cloud
- Generates customizable SharpCap sequences for automated recording
- Observation preparation panel with GOTO, plate solve, and test recording
- Report generation with Tangra CSV integration (experimental)
- Multiple telescope and camera configuration support

### 2. GPS Timing Analysis
**Python toolkit for camera timestamp validation**

Validates camera timestamp accuracy using GPS flash timing analysis. Essential for ensuring sub-millisecond timing precision in occultation observations.

📖 **[Read Full Documentation](gps-timing-analysis/ReadMe.md)**  
🔬 **[View Examples](gps-timing-analysis/examples/)**

**Quick Overview:**
- Tangra CSV light curve analysis
- GPS flash detection and timing offset calculation
- Rolling shutter characterization
- Camera calibration and quality assurance

### Integration

The tools work together:
- **GPS Timing Analysis**: Validates camera timestamp accuracy
- **Occultation Manager**: Uses Tangra CSV files to auto-populate reports with timing data

---

## Repository Structure

```
occultation-tools/
├── occultation-manager/      # SharpCap add-in
│   ├── python/               # Application code
│   ├── ReadMe.md            # Full documentation
│   └── RELEASE_NOTES.md     # Version history
│
├── gps-timing-analysis/      # Timing validation toolkit
│   ├── python/              # Analysis functions
│   ├── examples/            # Jupyter notebooks
│   ├── requirements.txt     # Dependencies
│   └── ReadMe.md           # Full documentation
│
├── CHANGELOG.md             # Release history
└── README.md               # This file
```

## License

BSD 3-Clause License. See individual tool directories for details.

## Author

Michael Camilleri

## Support

- 📖 Read the documentation in each tool's ReadMe.md
- 🐛 [Open an issue](https://github.com/labstercam/occultation-tools/issues) on GitHub
- 💬 Check existing issues for solutions
