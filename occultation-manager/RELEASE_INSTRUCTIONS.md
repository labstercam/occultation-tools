# Release Package Instructions - v0.3.0-alpha.2

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
- Generates `occultation-manager-v0.3.0-alpha.2.zip`

### Manual File List (if needed)

If you need to create the package manually, include these files from `occultation-manager/`:

**Application Python Files (copied into `app/`):**
- adv_helper.py
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
- pc_performance_testing.py
- phase_b_dialog.py
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
│   ├── pc_performance_testing.py                  <-- PC Performance Testing tool
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
├── RELEASE_NOTES.md                               <-- Version 0.3.0-alpha.2 features
└── RELEASE_INSTRUCTIONS.md
```

### Creating the Release on GitHub

1. **Navigate to repository:**
   - Go to: https://github.com/labstercam/occultation-tools

2. **Create new release:**
   - Click "Releases" (right sidebar)
   - Click "Create a new release"

3. **Tag and title:**
   - Tag: `v0.3.0-alpha.2`
   - Target: `alpha-release` branch
   - Release title: `Occultation Manager v0.3.0-alpha.2 — Full Reporting with PyOTE, OBS XML, and NTP Timing`

4. **Write release notes:**
   
   Copy the content from [RELEASE_NOTES.md](RELEASE_NOTES.md) or use this summary:

   ```markdown
   # Occultation Manager v0.3.0-alpha.2

   Full reporting workflow alpha: AOTA XML, AOTA Report, and PyOTE fit_metrics.txt timing
   sources; NA, TT, SODIS, and Occult 4 OBS XML output; NTP confirmation workflow; timestamp
   inspector; post-report rename, Gmail submission, and VizieR export.

   See RELEASE_NOTES.md for the full capability overview.
   ```

5. **Upload ZIP file:**
   - Run `create_release_zip.ps1` to generate `occultation-manager-v0.3.0-alpha.2.zip`
   - Drag and drop ZIP to "Attach binaries" section in GitHub release
   - Paste the download URL manually in the release notes:
     `https://github.com/labstercam/occultation-tools/releases/download/v0.3.0-alpha.2/occultation-manager-v0.3.0-alpha.2.zip`

6. **Set release options:**
   - ✅ Check "Set as a pre-release" (this is an alpha version)
   - ✅ Check "Set as the latest release"
   - Click "Publish release"

### After Publishing

The release will be available at:
- Direct link: `https://github.com/labstercam/occultation-tools/releases/tag/v0.3.0-alpha.2`
- Latest release: `https://github.com/labstercam/occultation-tools/releases/latest`

## Version Control

### Before Creating Release

1. **Update version numbers** in all files:
   - `RELEASE_NOTES.md` — version header
   - `create_release_zip.ps1` — `$version` variable
   - This file (`RELEASE_INSTRUCTIONS.md`)

2. **Test the release ZIP**:
   - Run `create_release_zip.ps1`
   - Extract to a test location
   - Install in SharpCap and verify startup
   - Verify automatic folder creation
   - Test basic event download and report generation

3. **Commit all changes**:
   ```bash
   git add .
   git commit -m "Release v0.3.0-alpha.2"
   git push
   ```

4. **Create and push tag**:
   ```bash
   git tag v0.3.0-alpha.2
   git push origin v0.3.0-alpha.2
   ```

### After Release

1. Verify download link works in release notes
2. Test clean installation from the GitHub release ZIP
3. Update ReadMe.md download link if needed

---

## Release Checklist

Before creating the release ZIP, verify:

### Code
- [ ] No debug print statements in production code (except intentional logging)
- [ ] No hardcoded file paths (all use config)
- [ ] No test or development files included in ZIP

### Assets
- [ ] Report templates (Excel) are not corrupted
- [ ] Icon file (`moon_icon_178489.ico`) is present
- [ ] Openize SDK DLLs are present in `python/lib/`

### SharpCap Integration
- [ ] `main.py` registers button in SharpCap toolbar correctly
- [ ] GUI launches without errors on a clean extract
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
- [ ] README.md up to date with v0.3.0-alpha.1 features
- [ ] RELEASE_NOTES.md reflects current functionality
- [ ] Installation instructions clear and accurate
- [ ] Configuration steps documented
- [ ] Automatic folder setup documented

### Known Issues Documented
- [ ] Report generation warning included in docs
- [ ] Known limitations listed
- [ ] WAIT UNTIL LOCALTIME risks explained
