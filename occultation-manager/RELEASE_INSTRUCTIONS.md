# Release Package Instructions - v0.1.0

## Creating a GitHub Release for Occultation Manager

### Files to Include in Release ZIP

Package the following files from `occultation-manager/python/`:

**Python Files (all .py files from python/ folder):**
- aota_dialogs.py
- aota_parser.py
- aota_report_parser.py
- comprehensive_report_dialog.py
- config.py
- equipment_dialogs.py
- events.py
- file_selection_dialog.py
- gui_components.py
- gui_dialogs.py
- help.py
- light_curves_iron.py
- main.py
- main_gui.py
- na_report.py
- occult4_export.py
- report_generator_base.py
- sequence_runner.py
- tangra_dialogs.py
- templates.py
- theme.py
- tt_report.py
- utils.py

**SharpCap Sequence Templates (all .txt files):**
- Minimal Local Time template.txt
- SharpCap Just Record template.txt
- SharpCap Sequence Local Time template.txt
- SharpCap Sequence UTC template.txt
- SharpCap Test Recording template.txt

**Report Templates (Excel files):**
- NorthAmerica_AstReportForm_V5.6.12r_Template.xlsx
- RASNZ_AstReporttForm_V4.1.2.G_Template.xlsx

**Documentation:**
- ReadMe.md (from python/ folder)
- README.md (copy from parent directory)

**Assets:**
- moon_icon_178489.ico

**Note:** The testing/ and development documentation/ subfolders are not included in the release.

### ZIP Structure

```
occultation-manager/
├── ReadMe.md                                      <-- Read this first!
├── README.md
├── aota_dialogs.py
├── aota_parser.py
├── aota_report_parser.py
├── comprehensive_report_dialog.py
├── config.py
├── equipment_dialogs.py
├── events.py
├── file_selection_dialog.py
├── gui_components.py
├── gui_dialogs.py
├── help.py
├── light_curves_iron.py
├── main.py
├── main_gui.py
├── na_report.py
├── occult4_export.py
├── report_generator_base.py
├── sequence_runner.py
├── tangra_dialogs.py
├── templates.py
├── theme.py
├── tt_report.py
├── utils.py
├── Minimal Local Time template.txt
├── SharpCap Just Record template.txt
├── SharpCap Sequence Local Time template.txt
├── SharpCap Sequence UTC template.txt
├── SharpCap Test Recording template.txt
├── NorthAmerica_AstReportForm_V5.6.12r_Template.xlsx
├── RASNZ_AstReporttForm_V4.1.2.G_Template.xlsx
└── moon_icon_178489.ico
```

### Creating the Release on GitHub

1. **Navigate to repository:**
   - Go to: https://github.com/labstercam/occultation-tools

2. **Create new release:**
   - Click "Releases" (right sidebar)
   - Click "Create a new release"

3. **Tag and title:**
   - Tag: `v0.1.0` (choose appropriate version)
   - Target: `main` branch
   - Release title: `Occultation Manager v0.1.0 - Initial Release`

4. **Write release notes:**
   ```markdown
   # Occultation Manager v0.1.0 - Initial Release
   
   SharpCap automation tool for asteroid occultation observations with Occult Watcher Cloud integration.
   
   ## 🎯 Major Features in v0.1.0
   
   ### Event Management
   - ✅ **Occult Watcher Cloud integration** - Downloads personal observations from your OWC announced stations
   - ✅ **Event filtering** - Filter by date, location, and probability
   - ✅ **Configurable retention** - Events retained for 1-400 days (default 14)
   - ✅ **Custom event settings** - Override exposure, gain, and recording duration per event
   - ✅ **Event grid display** - Sortable columns with custom value indicators (asterisks)
   
   ### Observation Preparation
   - ✅ **Load Event workflow** - Select and prepare single events with summary display
   - ✅ **GOTO integration** - Automatic telescope slewing to event coordinates
   - ✅ **Plate Solve** - Verify pointing and label target star
   - ✅ **Camera Setup** - Configure SharpCap exposure and coordinates
   - ✅ **Test Recording** - Make test recordings with automatic settings preservation and restoration
     - Saves/restores: binning, exposure, gain, resolution, display levels
     - Uses dedicated "SharpCap Test Recording Template.txt"
   
   ### Sequence Generation
   - ✅ **Automated sequences** - Generate SharpCap .scs files for event recording
   - ✅ **Template system** - Customizable templates with event data substitution
   - ✅ **Combined sequences** - Single file for multiple events in time order
   - ✅ **Template variables** - Exposure, gain, recording duration, coordinates, timing
   - ✅ **Provided templates** - Local Time, UTC, and Test Recording templates included
   
   ### Report Generation
   - ✅ **Comprehensive workflow** - Single dialog for all report types and data sources
   - ✅ **North America (IOTA V5.6.12r)** - Excel format for IOTA submissions
   - ✅ **Trans-Tasman (RASNZ V4.1.2.G)** - Excel format for Australia/New Zealand
   - ✅ **Occult 4 XML Export** - OBS.XML format (Version 2.15+)
   - ✅ **AOTA timing integration** - Imports D/R times from .aota.xml or AOTA_Report.txt
   - ✅ **Tangra CSV integration** - Extracts observation times, exposure, camera delay
   - ✅ **Auto-fill equipment** - Telescope and camera details from configuration
   - ✅ **Settings persistence** - Remembers report type and folder location
   
   ### Equipment Management
   - ✅ **Multiple configurations** - Manage multiple telescopes and cameras
   - ✅ **Active equipment selection** - Choose active telescope/camera for reports
   - ✅ **Comprehensive details** - Aperture, focal length, mount type, camera specs
   
   ### User Interface
   - ✅ **Dark theme support** - Theme manager with light/dark modes
   - ✅ **DPI scaling** - Proper display on high-DPI monitors
   - ✅ **Interactive help** - Built-in help system with detailed guidance
   - ✅ **Status updates** - Real-time status bar feedback
   - ✅ **Event selection summary** - Shows count of selected/displayed events
   
   ## 📋 Installation
   
   **Download:** [occultation-manager-v0.1.0.zip](link-will-be-auto-generated)
   
   ### Quick Start:
   1. Download and extract the ZIP file to a location where you have read/write access
      - Suggested: `Documents\SharpCap\occultation-manager`
   2. Start SharpCap
   3. Go to **File → SharpCap Settings → Startup Scripts**
   4. Browse to the extracted folder and add `main.py`
   5. Close and restart SharpCap
   6. Click the "Occultations" button in SharpCap toolbar
   7. Configure OWC credentials in **Tools → Configuration → Credentials**
   
   See [ReadMe.md](https://github.com/labstercam/occultation-tools/blob/main/occultation-manager/ReadMe.md) for complete documentation.
   
   ## ⚙️ Requirements
   
   **For SharpCap Integration:**
   - SharpCap Pro 4.0+
   - Windows 10/11
   - Internet connection for OWC event downloads
   - (Optional) ASCOM-compatible mount for GOTO functionality
   
   ## 📝 Configuration
   
   ### Initial Setup
   1. **Occult Watcher Cloud** (Tools → Configuration → Credentials)
      - Enter OWC email and password
      - Get API key from https://cloud.occultwatcher.net/user-profile
   
   2. **File Paths** (Tools → Configuration → File Paths)
      - Events data folder (default: Documents\OccultationManager\Events)
      - Sequence output folder (default: Documents\OccultationManager\Sequences)
      - Report output folder (default: Documents\OccultationManager\Reports)
      - Event retention period (1-400 days, default 14)
   
   3. **User Settings** (Tools → Configuration → User Settings)
      - Observer location (latitude/longitude for altitude calculations)
      - Minimum event probability threshold
      - GOTO lead time (minutes before event)
      - Base recording duration
      - Default camera gain (0-600, default 450)
   
   4. **Equipment** (Tools menu)
      - Add telescopes (aperture, focal length, mount type)
      - Add cameras (model, pixel size, sensor dimensions)
      - Select active equipment
   
   ### Sequence Templates
   
   Customize templates for your equipment and workflow:
   - **Local Time template** - Full automation including mount/camera setup
   - **UTC template** - Basic recording with UTC timing
   - **Test Recording template** - Short test recordings
   
   Templates use Python string formatting with variables:
   - `{exposure}` - Exposure time in seconds
   - `{gain}` - Camera gain value
   - `{recording_duration}` - Total recording duration
   - `{object_name}`, `{event_time}`, `{ra}`, `{dec}` - Event details
   
   ## ⚠️ Important Notes
   
   ### Report Generation Status
   **Report generation is under development and has not been approved by NA or TT reporting coordinators. Use with caution.**
   
   Users should:
   - Carefully review generated reports before submission
   - Verify all timing data matches AOTA/Tangra analysis
   - Check equipment details are correct
   - Confirm observation type selection (Positive/Negative/Unsure)
   
   ### Camera Settings Restoration
   The Test Recording feature saves and restores:
   - Binning (as string value)
   - Exposure time (in milliseconds)
   - Gain value
   - Resolution/ROI
   - Display levels (black/mid/white points)
   
   After test recording, camera waits 2× exposure time for stabilization.
   
   ## 🐛 Known Limitations
   
   - Report generation not yet approved by reporting coordinators
   - SODIS Europe report format not yet implemented
   - Tangra CSV video format detection relies on measurement parameters table
   - Camera delay extraction depends on Tangra CSV structure
   
   ## 📚 Documentation
   - [Main README](https://github.com/labstercam/occultation-tools/blob/main/occultation-manager/ReadMe.md)
   - [Python README](https://github.com/labstercam/occultation-tools/blob/main/occultation-manager/python/ReadMe.md)
   ```

5. **Upload ZIP file:**
   - Create `occultation-manager-v0.1.0.zip` with structure above
   - Drag and drop to "Attach binaries" section

6. **Set as latest release:**
   - Check "Set as the latest release"
   - Check "Set as a pre-release" if this is a beta/testing version
   - Click "Publish release"

### After Publishing

The release will be available at:
- Direct link: `https://github.com/labstercam/occultation-tools/releases/latest`
- Download link: `https://github.com/labstercam/occultation-tools/releases/download/v0.1.0/occultation-manager-v0.1.0.zip`

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
- [ ] Location confirmation works
- [ ] Telescope/camera selection populates
- [ ] AOTA file loading (.xml and .txt) works
- [ ] Tangra CSV parsing extracts correct data
- [ ] North America Excel report generates
- [ ] Trans-Tasman Excel report generates
- [ ] Occult 4 XML export creates valid OBS.XML
- [ ] Settings persistence (report type, folder) works

### Equipment Management
- [ ] Add/edit/delete telescopes works
- [ ] Add/edit/delete cameras works
- [ ] Active equipment selection persists
- [ ] Equipment appears in reports correctly

### Theme and UI
- [ ] Light theme displays correctly
- [ ] Dark theme displays correctly
- [ ] Theme switching works without restart
- [ ] DPI scaling proper on high-DPI displays
- [ ] All buttons accessible and labeled clearly
- [ ] Status bar updates appropriately

### Help System
- [ ] Help dialog opens and displays content
- [ ] All help topics accessible
- [ ] About dialog shows correct information

### Documentation
- [ ] README.md up to date with v0.1.0 features
- [ ] python/ReadMe.md reflects current functionality
- [ ] Installation instructions clear and accurate
- [ ] Configuration steps documented
- [ ] Template customization explained

### Known Issues Documented
- [ ] Report generation warning included in docs
- [ ] Known limitations listed
- [ ] Workarounds provided where applicable
