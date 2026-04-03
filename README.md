# occultation-tools

![Version](https://img.shields.io/badge/version-0.2.0--beta.4-blue)
![License](https://img.shields.io/badge/license-BSD--3--Clause-green)

Tools for automating occultation observations and validating timing accuracy.

📋 **[View CHANGELOG](CHANGELOG.md)** for release history and version details.

## Tools in this Repository

### 1. Occultation Manager
**SharpCap add-in for automated occultation workflow**

Automates the complete occultation observation workflow: downloads personal observations from Occult Watcher Cloud, generates customizable SharpCap sequences, and produces pre-filled reports with integrated timing data from Tangra analysis.

📖 **[Read Full Documentation](occultation-manager/ReadMe.md)**  
📦 **[Download Latest Release](occultation-manager/)**  
🚀 **[Installation Instructions](occultation-manager/ReadMe.md#installation)**

**Quick Overview:**
- Downloads events from Occult Watcher Cloud
- Generates customizable SharpCap sequences for automated recording
- Observation preparation panel with GOTO, plate solve, and test recording
- Report generation with Tangra CSV integration (experimental)
- Optional NTP timing analysis step during report generation — open the full NTP Analyser or run a quick in-flow estimate, folder remembered between sessions
- Supports NA (IOTA) and TT (RASNZ) Excel outputs plus SODIS (IOTA-ES Form 2.03) text output
- Multiple telescope and camera configuration support
- **Tools menu** provides access to the NTP Timing Analyser, GPS Flash Calibration, and GPS PPS Comparison directly from the main window

### 2. GPS Timing Analysis
**Python toolkit for NTP offset monitoring, GPS PPS validation, and camera timestamp calibration**

Validates camera timestamp accuracy and NTP performance. Includes LED line delay calibration, NTP loopstats/peerstats analysis, and GPS PPS UTC error comparison.

📖 **[Read Full Documentation](gps-timing-analysis/ReadMe.md)**  
🔬 **[View Examples](gps-timing-analysis/examples/)**

**Quick Overview:**
- **NTP Timing Analysis**: loopstats/peerstats offset and jitter charting, server delay analysis, U(k=2) uncertainty estimate
- **GPS PPS Comparison**: measures internet NTP server UTC error against a GPS PPS refclock; clock drift regression; per-server uncertainty table
- **LED Line Delay Calibration**: rolling shutter line delay measurement from live GPS flash captures
- **Tangra CSV analysis**: light curve import, timestamp statistics, GPS flash detection

### Integration

The tools work together as a timing quality chain:

| Step | Tool | Purpose |
|---|---|---|
| 1 | GPS Timing + NTP installer | Set up Meinberg NTP with GPS/PPS discipline |
| 2 | NTP Timing Analyser | Verify NTP server selection and offset stability |
| 3 | GPS PPS Comparison | Quantify UTC error and clock drift against GPS ground truth |
| 4 | LED Line Delay Calibration | Characterise rolling shutter offset for the camera |
| 5 | Occultation Manager report flow | Apply NTP uncertainty to the observation report |

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
│   ├── python/              # Analysis functions + GUI tools
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
