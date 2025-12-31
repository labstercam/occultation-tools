# Occultation Manager

SharpCap Occultation Manager automates the complete occultation observation workflow, from event download through report submission. It integrates with Occult Watcher Cloud, generates SharpCap sequences for automated recording, and produces pre-filled Excel reports with integrated timing data.

## Key Features

**Event Management**
- Downloads personal observations from Occult Watcher Cloud
- Manages event list with filtering by date, location, and probability
- Automatic SharpCap sequence generation

**Streamlined Report Generation**
- Single comprehensive dialog workflow (replaces 5 separate dialogs)
- Integrates AOTA timing data for D/R times
- Imports Tangra CSV light curves for observation timing and camera delay
- Supports multiple output formats:
  - North America (IOTA V5.6.12r) - Excel
  - Trans-Tasman (RASNZ V4.1.2.G) - Excel
  - Occult 4 XML Export (Version 2.15+) - OBS.XML format
- All formats generated in same workflow using shared data
- Auto-fills observer, telescope, and camera information
- Remembers report type and folder location for faster workflow

**Timing Integration**
- Extracts start/end times from Tangra CSV files (HH:MM:SS.SS format)
- Populates exposure time in seconds with 3 decimal precision
- Camera acquisition delay correction from Tangra measurement parameters
- Automatic placeholder population for all timing fields

**Equipment Management**
- Multiple telescope and camera configurations
- Active equipment selection
- Equipment details automatically populate reports

## Benefits

1. **Full Automation**: Complete workflow from event download to report generation within SharpCap
2. **Simplified Workflow**: No need for Occult Watcher Desktop or Occult 4 for predictions
3. **Flexible Sequences**: Customizable SharpCap sequence templates for any recording setup
4. **Accurate Timing**: Direct integration of Tangra timing analysis into reports
5. **Multi-Equipment**: Manage multiple telescopes, cameras, and observing sites

## Workflow

1. **Download Events**: Sync with Occult Watcher Cloud to get your announced stations
2. **Generate Sequences**: Create SharpCap sequences for automated recording
3. **Record Event**: Run the sequence to capture the occultation
4. **Analyze in Tangra**: Process video to generate light curve CSV and AOTA report
5. **Generate Reports**: One-click generation of Excel reports (NA/TT) and/or Occult 4 XML with integrated AOTA and Tangra data

## Installation
## Installation

1. Download the Python code from **occultation-manager.zip** above by right clicking and selecting 'Save As'
2. Unzip to a file location where you have read/write access. Suggest a new subfolder \Documents\SharpCap\occultation-manager
3. Alternative: clone this GitHub repository if you are a GitHub user
4. Start SharpCap
5. In "File" → "SharpCap Settings" → "Startup Scripts" → find that folder and add the 'main' script

<img width="666" height="155" alt="image" src="https://github.com/user-attachments/assets/42a9d9c9-4273-4a88-8d0a-428cca649afe" />

6. Close SharpCap (the script will be loaded at the next start)

A new button should appear in the SharpCap main toolbar. Press it to start the Occultation Manager.
<img width="117" height="28" alt="image" src="https://github.com/user-attachments/assets/6dbdf7af-aea5-4637-a39a-ff8a435dce55" />

## Configuration Setup

Press the  Occultations button in SharpCap to start the Occultation Manager.

Setup your Occult Watcher Cloud configuration. Go to the **Tools | Configuration** menu, **Credentials** Tab and follow the instructions there. You will need an OWC account and API key.

Under the **File Paths** tab you can set file paths and file names. Default values should be fine but you might want to use a different folder for your Sequences.

Under **User Settings** set it up to suit your telescope following the instructions there.

Save the configuration.

## Sequencer Templates
The Occultation Manager is used to generate SharpCap Sequences, and these sequences are used to run the events. By using SharpCap Sequences the user can customise the event recording to their system and to what they need to do. So you can do anything that a SharpCap Sequence can do and automate as little or as much as you want. You can generate a single sequence that will run an entire nights observations.

The Local Time template is a fully working example for the Authors setup. It fully configures the mount and camera for each observation (binning, ROI, file format etc) and leaves the mount in a safe position after each observation. 

The Minimal template is a minimalist example. It assumes that you have already set up your camera and recording settings for how you want to record and only adjusts the exposure.

You will need to test these templates and adapt them to your setup and to how you want to record. My advice is to use something like the Local Time Template which sets all the camera parameters as it is really easy to forget to set something manually and then mess up the observation.

You will need to extensively test your own template(s) before trusting them or before they are safe to use for unattended observations. There is the risk of failure, and the risk of damaging gear by snagging cables or leaving it pointed to the sun after sunrise.

## Report Generation

Reports are generated using a streamlined single-dialog workflow that combines:
- Report format selection (North America / Trans-Tasman)
- Telescope and camera selection
- Observation type (Positive / Negative / Unsure)
- AOTA file selection (.aota.xml OR .txt for D/R times and SNR)
- Tangra CSV file selection (light curve with timing data)

### Supported Report Formats
- **North America (IOTA V5.6.12r)**: IOTA standard report form
- **Trans-Tasman (RASNZ V4.1.2.G)**: Australia/New Zealand report form
- **SODIS Europe**: Planned for future implementation

### Timing Data Integration

**From AOTA Files (.aota.xml or AOTA_Report.txt)**:
- Disappearance (D) time with uncertainty (±error in seconds)
- Reappearance (R) time with uncertainty (±error in seconds)
- Signal-to-Noise Ratio (SNR) from AOTA Report text files
- Event quality indicators
- Either file type accepted (XML or text report)
- Automatic time comparison when both files provided (warns if times differ by >0.1s)

**From Tangra CSV Files**:
- Observation start time (HH:MM:SS.SS)
- Observation end time (HH:MM:SS.SS)
- Exposure time in seconds (3 decimal places)
- Camera acquisition delay in seconds (from measurement parameters table)

### Workflow Improvements
- **Settings Persistence**: Remembers last report type and folder location
- **Auto-Selection**: Automatically selects first available AOTA and Tangra files
- **Smart Validation**: AOTA file (XML or Report) required for Positive/Unsure observations, optional for Negative
- **Flexible Timing**: Accepts either AOTA.xml OR AOTA_Report.txt (or both for validation)
- **Time Verification**: Compares D/R times when both AOTA sources provided
- **Multi-Event Support**: Select specific event from AOTA Reports with multiple events
- **One-Click Generation**: Single dialog replaces 5 separate dialogs

### File Organization
For efficient workflow, organize files in folders by event:
```
D:\Occultations\Reported\20251107 (778) Theobalda+\
  ├── event.aota.xml          # AOTA XML timing file (optional)
  ├── event_AOTA_Report.txt   # AOTA text report with D/R times and SNR (optional)
  ├── light_curve.csv         # Tangra CSV
  └── video.ser              # Original recording
```

**Note**: You need either `event.aota.xml` OR `event_AOTA_Report.txt` (or both for cross-validation) for Positive/Unsure observations.

The dialog remembers the parent folder (e.g., `D:\Occultations\Reported\`) making it easy to switch between event folders.
