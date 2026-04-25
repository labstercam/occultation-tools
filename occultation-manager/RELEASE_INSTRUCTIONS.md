# Release Package Instructions - v0.2.0-beta.9

## Creating a GitHub Release for Occultation Manager

### Using the Automated Release Script

The easiest way to create the release ZIP is to use the PowerShell script:

```powershell
cd occultation-manager
.\create_release_zip.ps1
```

This script automatically:
- Creates the fixed folder structure with `app/`, `resources/templates_master/`, and `data/`
- Copies all necessary files including Openize SDK DLLs into `app/lib/`
- Places master templates in `resources/templates_master/{sequencer,reports}/`
- Pre-seeds `data/templates/` with working copies of the sequencer master templates
- Seeds/creates data folders under `data/{config,events,templates,sequences,reports}/`
- Generates `occultation-manager-v0.2.0-beta.9.zip`

### Manual File List (if needed)

If you need to create the package manually, include these files from `occultation-manager/`:

**Application Python Files (copied into `app/`):**
- aota_dialogs.py
- aota_parser.py
- aota_report_parser.py
- comprehensive_report_dialog.py
- config.py
- dummy_event_generator.py
- equipment_dialogs.py
- events.py
- file_selection_dialog.py
- gui_components.py
- gui_dialogs.py
- help.py
- led_line_delay_calibration.py
- light_curve_reader.py
- light_curves_iron.py
- line_delay_dialogs.py
- main.py
- main_gui.py
- na_report_openize.py
- occult4_export.py
- pyote_metrics_reader.py
- rename_files_dialog.py
- report_generator_base.py
- sequence_runner.py
- sodis_report_text.py
- tangra_dialogs.py
- templates.py
- theme.py
- timing_utils.py
- tt_report_openize.py
- utils.py
- vizier_export.py
- vizier_export_dialog.py

**Sequencer Master Templates (copied into `resources/templates_master/sequencer/`):**
- python\SharpCap Minimal Local Time template.txt
- python\SharpCap Just Record template.txt
- python\SharpCap Sequence Local Time template.txt
- python\SharpCap Sequence UTC template.txt
- python\SharpCap Test Recording template.txt

**Countdown Reference File (in sequencer masters):**
- python\countdown python for sequencer.scs

**Working Template Copies (also copied into `data/templates/`):**
- SharpCap Minimal Local Time template.txt
- SharpCap Just Record template.txt
- SharpCap Sequence Local Time template.txt
- SharpCap Sequence UTC template.txt
- SharpCap Test Recording template.txt
- countdown python for sequencer.scs

**Report Master Templates (copied into `resources/templates_master/reports/`):**
- python\NorthAmerica_AstReportForm_V5.6.12r.xlsx
- python\RASNZ_AstReporttForm_V4.1.2.G.xlsx

**Openize SDK DLLs (copied into `app/lib/`):**
- python\lib\Openize.OpenXMLSDK.dll
- python\lib\DocumentFormat.OpenXml.dll
- python\lib\DocumentFormat.OpenXml.Framework.dll
- python\lib\README.md

**Documentation (package root and app):**
- python\ReadMe.md
- ReadMe.md (from occultation-manager/)
- RELEASE_NOTES.md

**Data folder README seed files:**
- README_events_folder.txt
- README_sequences_folder.txt
- README_reports_folder.txt

**Assets:**
- python\moon_icon_178489.ico

### ZIP Structure

The release ZIP should have this structure:

```
occultation-manager/
├── app/                                           <-- SharpCap startup + Python modules
│   ├── main.py                                    <-- SharpCap startup script target
│   ├── *.py
│   ├── moon_icon_178489.ico
│   ├── ReadMe.md
│   └── lib/
│       ├── Openize.OpenXMLSDK.dll
│       ├── DocumentFormat.OpenXml.dll
│       ├── DocumentFormat.OpenXml.Framework.dll
│       └── README.md
├── resources/
│   └── templates_master/
│       ├── sequencer/                             <-- .txt/.scs master templates
│       └── reports/                               <-- .xlsx report masters
├── data/                                          <-- User data root (pre-created)
│   ├── config/
│   ├── events/
│   ├── templates/                                 <-- Pre-seeded working template copies
│   ├── sequences/
│   └── reports/
├── ReadMe.md                                      <-- User documentation
├── RELEASE_NOTES.md                               <-- Version 0.2.0-beta.9 features
└── RELEASE_INSTRUCTIONS.md
```

### Creating the Release on GitHub

1. **Navigate to repository:**
   - Go to: https://github.com/labstercam/occultation-tools

2. **Create new release:**
   - Click "Releases" (right sidebar)
   - Click "Create a new release"

3. **Tag and title:**
   - Tag: `v0.2.0-beta.9`
   - Target: `main` branch
   - Release title: `Occultation Manager v0.2.0-beta.9 - Bug Fixes, Rename Dialog, and UX Improvements`

4. **Write release notes:**
   
   Copy the content from [RELEASE_NOTES.md](RELEASE_NOTES.md) or use this summary:

   ```markdown
   # Occultation Manager v0.2.0-beta.9 - Bug Fixes, Rename Dialog, and UX Improvements
   
   **Report Generation Bug Fixes and new features** — SNR fix for AOTA Report parser, camera delay 4 d.p. in TT report, NTP comment written to correct Additional Comments cell, AOTA Report as default first entry in D/R combo, D/R uncertainty displayed to 1–2 sig fig, new Rename Files dialog, "Include Station Name in Filenames" checkbox, and layout fix for blank space in Generate Report dialog.
   
   SharpCap automation tool for asteroid occultation observations with Occult Watcher Cloud integration.

   ## 🧹 Maintenance

   - Updated release-facing documentation and version references for Beta.9.
   - Updated release packaging/version pointers (ZIP naming and instructions).
   
   ## 📦 Installation
   
   **Download:** [occultation-manager-v0.2.0-beta.9.zip](https://github.com/labstercam/occultation-tools/releases/download/v0.2.0-beta.9/occultation-manager-v0.2.0-beta.9.zip)
   
   ### Quick Start:
   1. Download and extract the ZIP file to a location with read/write access
      - ⚠️ **Avoid Program Files** - Windows may restrict write access
      - ✅ **Recommended**: `Documents\SharpCap`
   2. Start SharpCap
   3. Go to **File → SharpCap Settings → Startup Scripts**
   4. Browse to the extracted `app` folder and select `app/main.py`
   5. Restart SharpCap
   6. Click the "Occultations" button in SharpCap toolbar
   
   **First Startup - Automatic Configuration:**
   - Automatically detects installation directory
   - Uses fixed folders under `data/` and `resources/templates_master/`
   - Creates data folders: `data/config`, `data/events`, `data/templates`, `data/sequences`, `data/reports`
   - Seeds missing working templates into `data/templates`
   
   **Initial Configuration:**
   - Configure OWC credentials in **Tools → Configuration → Credentials**
   - Set **Days to Retain** in the Credentials tab (default 14)
   - Use **Tools → Configuration → File Paths** buttons to open `data/config`, `data/events`, `data/templates`, `data/sequences`, and `data/reports`
   - Get API key from https://cloud.occultwatcher.net/user-profile
   - All other settings are pre-configured and optional
   
   See [ReadMe.md](https://github.com/labstercam/occultation-tools/blob/main/occultation-manager/ReadMe.md) for complete documentation.
   
   ## ✨ What's New in Beta.9
   
   ### SNR Fix — AOTA Report Parser
   
   SNR now correctly populates the TT report when an AOTA Report text file is the timing source.
   Regex updated to match both `Ave:` and `Average:` label variants (case-insensitive).
   
   ### Camera Delay — 4 Decimal Places (TT Report)
   
   Camera acquisition delay written to cell P26 of the TT report is now rounded to 4 d.p.,
   preserving the precision provided by the rolling-shutter calibration.
   
   ### NTP Comment — Written to Correct Cell
   
   The NTP uncertainty note is now written to cell D44 (Additional Comments) in the TT report,
   not merged into the Other Conditions field.
   
   ### AOTA Report — Default First in Combo
   
   When AOTA Report events are available, they appear first in the D/R event combo.
   
   ### D/R Uncertainty — 1–2 Significant Figures
   
   Uncertainty values in the event info panel now display as `±0.2s`, `±0.04s` etc.
   instead of `±0.2000001s`.
   
   ### Rename Files Dialog (New)
   
   After report generation a new dialog offers to rename the observation files (CSV, AOTA XML,
   AOTA Report, image files, `.lc` files) so they share the same stem as the generated report.
   Filenames are editable before confirming. `_AOTA_…` and `_Bin{N}` suffixes are preserved
   automatically.
   
   ### Include Station Name in Filenames (New)
   
   A new checkbox in the Generate Report dialog (unchecked by default) appends the observer's
   station name to the TT report filename when checked.
   
   ### Generate Report Dialog — Layout Fix
   
   The large blank space below section 3 when a compact timing method is selected has been
   removed. Sections 4 and 5 now follow immediately below section 3.
   
   ## 🎯 Key Features
   
   ### Event Management
   - Downloads personal observations from Occult Watcher Cloud
   - Event list with filtering by date, location, and probability
   - Configurable event retention (1-400 days, default 14)
   - Custom per-event settings (exposure, gain, recording duration)
   
   ### Sequence Execution
   - **Run Sequences** button for direct multi-sequence execution
   - **Test Recording** with automatic camera settings preservation
   - SharpCap remains responsive during all operations
   - **Stop button** with confirmation and automatic cleanup
   - Asynchronous execution using SharpCap's RunAsync() API
   
   ### Observation Preparation
   - Load event workflow with summary display
   - GOTO integration for automatic telescope slewing
   - Plate solve verification and target labeling
   - Camera setup with exposure and coordinate configuration
   - Test recording without disrupting settings
   
   ### Sequence Generation
   - Automated SharpCap .scs file generation
   - Customizable templates with event data substitution
   - Combined sequences for multiple events
   - Five provided templates (UTC, Local Time, Minimal, Test Recording)
   - **UTC countdown functions** for reliable timing (24+ hour safe)
   
   ### Report Generation (Under Development - Not Approved)
   ⚠️ **CRITICAL WARNING**: Report generation has **NOT** been approved by North America (IOTA), Trans-Tasman (RASNZ), or SODIS reporting coordinators. Verify all data before submission.
   
   - North America (IOTA) and Trans-Tasman (RASNZ) Excel formats, plus SODIS (IOTA-ES) text format
   - AOTA timing data integration (D/R times)
   - Tangra CSV light curve analysis (fully integrated)
   - Automatic video format and exposure detection
   - GPS flash timing analysis available via Tools → Camera Delay Calibration
   
   ### Equipment Management
   - Multiple telescope and camera configurations
   - Active equipment selection
   - Comprehensive equipment details for reports
   
   ## ⚙️ Requirements
   
   - SharpCap Pro 4.0+
   - Windows 10/11
   - Internet connection for OWC event downloads
   - (Optional) ASCOM-compatible mount for GOTO functionality
   
   ## 📝 Known Limitations
   
   - Cannot pause sequences (stop and restart only)
   - Single sequence execution at a time
   - Report generation not approved — only TANGRA and AOTA outputs supported; use with caution
   
   ## 📖 Documentation
   
   - [ReadMe.md](https://github.com/labstercam/occultation-tools/blob/main/occultation-manager/ReadMe.md) - Complete user guide
   - [RELEASE_NOTES.md](https://github.com/labstercam/occultation-tools/blob/main/occultation-manager/RELEASE_NOTES.md) - Detailed feature list
   - Built-in Help menu with comprehensive guides
   - `countdown python for sequencer.scs` - Reference code for countdown functions
   
   ## 🐛 Reporting Issues
   
   This is a beta release. Please report issues through [GitHub Issues](https://github.com/labstercam/occultation-tools/issues).
   
   Include:
   - SharpCap version
   - Camera type and connection method
   - Steps to reproduce
   - Error messages
   - Sequence file (if relevant)
   ```

5. **Upload ZIP file:**
   - Run `create_release_zip.ps1` to generate `occultation-manager-v0.2.0-beta.9.zip`
   - Drag and drop ZIP to "Attach binaries" section in GitHub release
   - GitHub does **not** auto-update markdown links in release notes; paste this URL manually in the notes:
     `https://github.com/labstercam/occultation-tools/releases/download/v0.2.0-beta.9/occultation-manager-v0.2.0-beta.9.zip`

6. **Set release options:**
   - ✅ Check "Set as a pre-release" (this is a beta version)
   - ✅ Check "Set as the latest release"
   - Click "Publish release"

### After Publishing

The release will be available at:
- Direct link: `https://github.com/labstercam/occultation-tools/releases/tag/v0.2.0-beta.9`
- Latest release: `https://github.com/labstercam/occultation-tools/releases/latest`

## Version Control Best Practices

### Before Creating Release

1. **Update version numbers** in all files:
   - `RELEASE_NOTES.md` - Version header
   - `create_release_zip.ps1` - `$version` variable
   - This file (`RELEASE_INSTRUCTIONS.md`)
   - Release notes download URL (must match tag + ZIP filename)

2. **Test the release ZIP**:
   - Run `create_release_zip.ps1`
   - Extract to test location
   - Install in SharpCap
   - Verify automatic folder creation
   - Test basic functionality

3. **Commit all changes**:
   ```bash
   git add .
   git commit -m "Release v0.2.0-beta.9"
   git push
   ```

4. **Create and push tag**:
   ```bash
   git tag v0.2.0-beta.9
   git push origin v0.2.0-beta.9
   ```

### After Release

1. **Verify download link** works in release notes
2. **Test installation** from GitHub release ZIP
3. **Update documentation** if any installation issues found
- Direct link: `https://github.com/labstercam/occultation-tools/releases/latest`
- Download link: `https://github.com/labstercam/occultation-tools/releases/download/v0.2.0-beta.9/occultation-manager-v0.2.0-beta.9.zip`

Update README.md with this download link.

---

## Release Checklist for v0.1.0

Before creating the release, verify:

### Code Quality
- [ ] All Python files have proper docstrings
- [ ] No debug print statements in production code (except intentional logging)
- [ ] No hardcoded file paths (all use config)
- [ ] Error handling implemented for critical operations
- [ ] No test files included in release ZIP

### Configuration
- [ ] occultation_config.json has sensible defaults
- [ ] Template files are included and functional
- [ ] Report templates (Excel) are not corrupted
- [ ] Icon file (moonstars_99404.ico) is present

### SharpCap Integration
- [ ] main.py registers button in SharpCap toolbar correctly
- [ ] GUI launches without errors
- [ ] SharpCap remains responsive while GUI is open
- [ ] Camera controls accessible from GUI

### Event Management
- [ ] OWC download works with valid credentials
- [ ] Events display in grid correctly
- [ ] Filtering (Today, Upcoming, All) works
- [ ] Station filtering functions
- [ ] Custom exposure/gain/duration edits save correctly
- [ ] Asterisk indicators show for custom values

### Observation Preparation
- [ ] Load Event displays event information correctly
- [ ] GOTO command works (if mount available)
- [ ] Plate Solve executes (if supported)
- [ ] Setup configures camera exposure
- [ ] Test Recording saves/restores all camera settings
  - [ ] Binning
  - [ ] Exposure
  - [ ] Gain
  - [ ] Resolution
  - [ ] Display levels (black/mid/white)

### Sequence Generation
- [ ] Template selection dialog lists available templates
- [ ] Sequence files generate with correct content
- [ ] Event data substitutes into templates correctly
- [ ] Combined sequences sort events by time
- [ ] Custom settings (exposure/gain/duration) appear in sequences

### Report Generation
- [ ] Warning dialog appears before report generation
- [ ] AOTA file loading (.xml and .txt) works
- [ ] Tangra CSV parsing extracts correct data
- [ ] North America Excel report generates
- [ ] Trans-Tasman Excel report generates
- [ ] Equipment details populate correctly
- [ ] Settings persistence (report type, folder) works

### Equipment Management
- [ ] Add/edit/delete telescopes works
- [ ] Add/edit/delete cameras works
- [ ] Active equipment selection persists
- [ ] Equipment appears in reports correctly

### Configuration & Installation
- [ ] First startup creates folder structure automatically
- [ ] Fixed install-relative paths active (no path configuration required)
- [ ] Configuration saved to data/config/occultation_config.json
- [ ] README seed files present in data/events, data/sequences, data/reports
- [ ] Working templates seeded into data/templates from resources/templates_master/sequencer

### Sequence Execution (Available in v0.2.0-beta.3+)
- [ ] Run Sequences button executes multiple selected sequences
- [ ] Sequences run in chronological order
- [ ] Progress updates show current sequence
- [ ] Stop button works during sequence execution
- [ ] SharpCap remains responsive during execution
- [ ] Camera settings restored after stop

### Theme and UI
- [ ] Light theme displays correctly
- [ ] Dark theme displays correctly
- [ ] Theme switching works without restart
- [ ] All buttons accessible and labeled clearly
- [ ] Status bar updates appropriately

### Help System
- [ ] Help dialog opens and displays content
- [ ] All help topics accessible
- [ ] About dialog shows correct information

### Documentation
- [ ] README.md up to date with v0.2.0-beta.5 features
- [ ] RELEASE_NOTES.md reflects current functionality
- [ ] Installation instructions clear and accurate
- [ ] Configuration steps documented
- [ ] Automatic folder setup documented

### Known Issues Documented
- [ ] Report generation warning included in docs
- [ ] Known limitations listed
- [ ] WAIT UNTIL LOCALTIME risks explained
