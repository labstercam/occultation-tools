# GPS Timing Analysis - Examples

Example notebooks and scripts demonstrating GPS timing validation and Tangra light curve analysis.

## Available Examples

### process loopstats.ipynb
Comprehensive notebook demonstrating:
- Reading Tangra CSV light curve files
- Timestamp statistical analysis
- Frame timing validation
- GPS offset calculation
- Rolling shutter characterization

**Key Demonstrations**:
- Load and parse Tangra CSV structure
- Extract observation start/end times
- Calculate median exposure and frame time statistics
- Identify timing anomalies and dropped frames
- Extract camera acquisition delay from measurement parameters

### Sample Data

The `sample_data/` directory contains example files for testing:
- Tangra CSV light curves with GPS timing data
- Example measurement parameter tables showing acquisition delay

## Running the Examples

1. **Install dependencies**:
```bash
cd ../
pip install -r requirements.txt
```

2. **Launch Jupyter**:
```bash
jupyter notebook
```

3. **Open and run notebooks**:
   - Navigate to `process loopstats.ipynb`
   - Execute cells to see timing analysis workflow

## Practical Applications

**Pre-Observation Validation**:
- Test camera timestamp accuracy with GPS flashes
- Verify acquisition delay values
- Check for timing drift or anomalies

**Post-Observation Analysis**:
- Validate recorded event timing
- Extract timing data for report generation
- Identify any recording issues

**System Characterization**:
- Measure camera acquisition delays
- Characterize rolling shutter timing
- Establish baseline timing accuracy

## Integration with Occultation Manager

These examples show the analysis workflow used by the Occultation Manager's `light_curves_iron.py` module. The same timing data extraction is used to auto-populate Excel reports with:
- Observation start/end times
- Exposure duration
- Camera acquisition delay corrections

## New NTP and Camera Timing Documentation

For end-to-end operational guidance, see:
- `../docs/ntp-camera-timing-workflow.md`
- `../docs/ntp-meinberg-setup.md`
- `../docs/ntp-offset-monitoring.md`
- `../docs/camera-acquisition-delay-estimation.md`
