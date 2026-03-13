## GPS Timing Analysis - Camera Timestamp Validation

Python toolkit for analyzing GPS flash timing to validate camera timestamp accuracy. Critical for ensuring sub-millisecond timing precision in occultation observations.

### Key Features

- **LED Line Delay Calibration**: Measure rolling shutter line delays using GPS timing LED (SharpCap add-in)
- **Tangra Light Curve Analysis**: Import and analyze Tangra CSV files for timestamp quality
- **Video Format Extraction**: Automatic extraction of video format from Tangra measurement parameters
- **GPS Flash Detection**: Automated detection and analysis of GPS 1PPS (one pulse per second) flashes
- **Timestamp Offset Calculation**: Measure timing differences between recorded and actual GPS time
- **Rolling Shutter Characterization**: Calculate inter-line timing delays for rolling shutter cameras
- **Camera Acquisition Delay**: Extract timing corrections from Tangra measurement parameters
- **Exposure/Integration Detection**: Determine recording mode from timing consistency
- **Quality Validation**: Detect dropped frames, timing anomalies, and system issues

### Tools

#### **LED Line Delay Calibration** (SharpCap Add-in)
Real-time camera calibration tool for measuring rolling shutter line delays.

**Location:** `python/led_line_delay_calibration.py`

**Features:**
- Live camera capture with GPS LED flash analysis
- ADV file replay mode for offline analysis
- Multiple aperture measurements across frame height
- Linear regression for line delay calculation
- Interactive GUI with visualization
- TANGRA CSV export

**Quick Start:**
```python
# In SharpCap IronPython Console:
execfile(r"C:\path\to\gps-timing-analysis\python\led_line_delay_calibration.py")
```

See `LED_LINE_DELAY_QUICKSTART.md` for detailed usage instructions.

**Requirements:**
- SharpCap Pro 4.0+
- GPS timing LED or GPS-equipped camera (QHY174GPS, etc.)
- ADV DLLs in `lib/` directory (⚠️ must be unblocked - see `lib/README.md`)

**Note:** Windows blocks DLLs downloaded from the web. Run `lib\unblock_dlls.ps1` before first use.

#### **GPS Timing Analysis** (Offline Analysis)
Python tools for analyzing Tangra CSV light curves.

**Location:** `python/light_curves.py`, `python/ntp_analysis.py`

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

### NTP Timing (Meinberg) Workflow

The repository now includes documentation for setting up and using Meinberg NTP, monitoring NTP offsets, and estimating camera acquisition delays in a repeatable way.

Start here:
- `docs/ntp-camera-timing-workflow.md`

Detailed guides:
- `docs/ntp-meinberg-setup.md`
- `docs/ntp-offset-monitoring.md`
- `docs/camera-acquisition-delay-estimation.md`
- `docs/automated-setup.md`

Related analysis code:
- `python/ntp_analysis.py`
- `examples/process loopstats.ipynb`

Automation assets:
- `install_ntp_timing_bootstrap.cmd` (recommended one-file installer)
- `scripts/install_ntp_timing_guided.ps1`
- `scripts/install_ntp_timing_guided.cmd`
- `scripts/setup_ntp_timing.ps1` (legacy/testing)
- `scripts/find_gps_com_port.ps1`
- `config/ntp.conf.template`
- `config/ntp-country-servers.json`
- `resources/ntp_pool_zones.json`
- `resources/national_utc_ntp_servers.json`

For most users, start with:
- `install_ntp_timing_bootstrap.cmd`

The bootstrap launcher downloads/updates required files into:
- `C:\OccultationTools\gps-timing-analysis`
then starts the guided installer automatically.

Advanced/manual entrypoint:
- `scripts/install_ntp_timing_guided.ps1`

The guided installer provides an `Install / Skip / Exit` flow for each major setup stage and writes a transcript log under `gps-timing-analysis/logs/`.
It also prompts to restart the NTP service when configuration changes are made, including if you exit early after changes.
Beginner tip: follow recommended defaults in the installer unless your hardware documentation says otherwise.
Setup behavior note: server and logging updates are applied to managed `ntp.conf` sections, while other existing `ntp.conf` settings are preserved.
Guided installer note: country/pool/national-server selection is handled directly inside `install_ntp_timing_guided.ps1`.
Guided installer note: COM port detection is built in; `scripts/find_gps_com_port.ps1` remains available as a standalone utility.
Guided installer note: `install_ntp_timing_guided.cmd` requests Administrator rights automatically (UAC prompt).

GPS/PPS note:
- after setting `PPSProviders`, restart the `NTP` service first,
- a full Windows reboot is usually not required,
- reboot only if the NTP service/provider still fails to stabilize after restart or Windows indicates pending reboot requirements.

### National UTC Server Inventory Resource

Machine-readable national UTC/NTP inventory is maintained in:
- `resources/national_utc_ntp_servers.json`

Current scope in this file:
- G20 countries
- New Zealand
- Major Europe countries
- Selected additional countries

Notes:
- `country_code` values follow internet country-domain labels (IANA TLD style).
- `UK` is intentionally used as the UK internet domain code label.
- The previous `EU` entity entry has been removed.
- Some entries include `usage_note` when public server usage has restrictions.
- Setup runtime use: when `setup_ntp_timing.ps1` is run with `-Country Other` and the ccTLD is not in `config/ntp-country-servers.json`, this inventory is used to surface national-server metadata and optional national hostnames.
- Setup runtime use: when `install_ntp_timing_guided.ps1` configures `-Country Other` and the ccTLD is not in `config/ntp-country-servers.json`, this inventory is used to surface national-server metadata and optional national hostnames.
- Field conventions for `status`, `groups`, and `usage_note` are documented in `docs/ntp-country-server-requirements.md` under `national_utc_ntp_servers.json Field Reference`.

