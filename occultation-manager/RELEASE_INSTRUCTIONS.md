# Release Package Instructions - v0.2.0-beta.1

## Creating a GitHub Release for Occultation Manager

### Using the Automated Release Script

The easiest way to create the release ZIP is to use the PowerShell script:

```powershell
cd occultation-manager
.\create_release_zip.ps1
```

This script automatically:
- Creates the correct folder structure with `files/`, `sequences/`, and `files/Reports/`
- Copies all necessary files
- Distributes README files to appropriate folders
- Copies template files to both main folder and `files/` folder
- Generates `occultation-manager-v0.2.0-beta.1.zip`

### Manual File List (if needed)

If you need to create the package manually, include these files from `occultation-manager/`:

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

**SharpCap Sequence Templates:**
- python\SharpCap Minimal Local Time template.txt
- python\SharpCap Just Record template.txt
- python\SharpCap Sequence Local Time template.txt
- python\SharpCap Sequence UTC template.txt
- python\SharpCap Test Recording template.txt

**Countdown Reference File:**
- python\countdown python for sequencer.scs

**Report Templates (Excel files):**
- python\NorthAmerica_AstReportForm_V5.6.12r_Template.xlsx
- python\RASNZ_AstReporttForm_V4.1.2.G_Template.xlsx

**Documentation:**
- python\ReadMe.md
- ReadMe.md (from occultation-manager/)
- RELEASE_NOTES.md

**Folder README Files:**
- README_files_folder.txt
- README_sequences_folder.txt
- README_reports_folder.txt

**Assets:**
- python\moon_icon_178489.ico

### ZIP Structure

The release ZIP should have this structure:

```
occultation-manager/
├── main.py                                        <-- SharpCap startup script
├── files/                                         <-- Data folder (pre-created)
│   ├── README.txt                                <-- Explains folder purpose
│   ├── SharpCap Minimal Local Time template.txt  <-- Working copies
│   ├── SharpCap Just Record template.txt
│   ├── SharpCap Sequence Local Time template.txt
│   ├── SharpCap Sequence UTC template.txt
│   ├── SharpCap Test Recording template.txt
│   └── Reports/                                  <-- Report output folder
│       └── README.txt
├── sequences/                                     <-- Sequence output folder (pre-created)
│   └── README.txt
├── SharpCap Minimal Local Time template.txt      <-- Original reference copies
├── SharpCap Just Record template.txt
├── SharpCap Sequence Local Time template.txt
├── SharpCap Sequence UTC template.txt
├── SharpCap Test Recording template.txt
├── countdown python for sequencer.scs
├── NorthAmerica_AstReportForm_V5.6.12r_Template.xlsx
├── RASNZ_AstReporttForm_V4.1.2.G_Template.xlsx
├── moon_icon_178489.ico
├── ReadMe.md                                      <-- User documentation
├── RELEASE_NOTES.md                               <-- Version 0.2.0-beta.1 features
└── [all .py files from python/ folder]
```

### Creating the Release on GitHub

1. **Navigate to repository:**
   - Go to: https://github.com/labstercam/occultation-tools

2. **Create new release:**
   - Click "Releases" (right sidebar)
   - Click "Create a new release"

3. **Tag and title:**
   - Tag: `v0.2.0-beta.1`
   - Target: `main` branch
   - Release title: `Occultation Manager v0.2.0-beta.1 - First Public Beta`

4. **Write release notes:**
   
   Copy the content from [RELEASE_NOTES.md](RELEASE_NOTES.md) or use this summary:

   ```markdown
   # Occultation Manager v0.2.0-beta.1 - First Public Beta
   
   **First public beta release** of Occultation Manager for SharpCap.
   
   SharpCap automation tool for asteroid occultation observations with Occult Watcher Cloud integration.
   
   ## 📦 Installation
   
   **Download:** [occultation-manager-v0.2.0-beta.1.zip](link-will-be-auto-generated)
   
   ### Quick Start:
   1. Download and extract the ZIP file to a location with read/write access
      - ⚠️ **Avoid Program Files** - Windows may restrict write access
      - ✅ **Recommended**: `Documents\SharpCap\occultation-manager`
   2. Start SharpCap
   3. Go to **File → SharpCap Settings → Startup Scripts**
   4. Browse to the extracted folder and select `main.py`
   5. Restart SharpCap
   6. Click the "Occultations" button in SharpCap toolbar
   
   **First Startup - Automatic Configuration:**
   - Automatically detects installation directory
   - Creates folder structure: `files/`, `sequences/`, `files/Reports/`
   - Sets default paths to installation directory
   - Copies template files for customization
   
   **Initial Configuration:**
   - Configure OWC credentials in **Tools → Configuration → Credentials**
   - Get API key from https://cloud.occultwatcher.net/user-profile
   - All other settings are pre-configured and optional
   
   See [ReadMe.md](https://github.com/labstercam/occultation-tools/blob/main/occultation-manager/ReadMe.md) for complete documentation.
   
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
   ⚠️ **CRITICAL WARNING**: Report generation has **NOT** been approved by North America (IOTA) or Trans-Tasman (RASNZ) reporting coordinators. Verify all data before submission.
   
   - North America (IOTA) and Trans-Tasman (RASNZ) Excel formats
   - AOTA timing data integration (D/R times)
   - Tangra CSV light curve analysis (fully integrated)
   - Automatic video format and exposure detection
   - GPS flash timing analysis (not yet integrated - available as standalone tool)
   
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
   - Report generation not approved - use with caution
   
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
   - Run `create_release_zip.ps1` to generate `occultation-manager-v0.2.0-beta.1.zip`
   - Drag and drop ZIP to "Attach binaries" section in GitHub release

6. **Set release options:**
   - ✅ Check "Set as a pre-release" (this is a beta version)
   - ✅ Check "Set as the latest release"
   - Click "Publish release"

### After Publishing

The release will be available at:
- Direct link: `https://github.com/labstercam/occultation-tools/releases/tag/v0.2.0-beta.1`
- Latest release: `https://github.com/labstercam/occultation-tools/releases/latest`

## Version Control Best Practices

### Before Creating Release

1. **Update version numbers** in all files:
   - `RELEASE_NOTES.md` - Version header
   - `create_release_zip.ps1` - `$version` variable
   - This file (`RELEASE_INSTRUCTIONS.md`)

2. **Test the release ZIP**:
   - Run `create_release_zip.ps1`
   - Extract to test location
   - Install in SharpCap
   - Verify automatic folder creation
   - Test basic functionality

3. **Commit all changes**:
   ```bash
   git add .
   git commit -m "Release v0.2.0-beta.1"
   git push
   ```

4. **Create and push tag**:
   ```bash
   git tag v0.2.0-beta.1
   git push origin v0.2.0-beta.1
   ```

### After Release

1. **Verify download link** works in release notes
2. **Test installation** from GitHub release ZIP
3. **Update documentation** if any installation issues found
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
- [ ] Default paths set to installation directory
- [ ] Configuration saved to files/occultation_config.json
- [ ] Custom paths persist across restarts
- [ ] README files present in files/, sequences/, Reports/ folders
- [ ] Template files copied to both locations

### Sequence Execution (New in v0.2.0-beta.1)
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
- [ ] README.md up to date with v0.2.0-beta.1 features
- [ ] RELEASE_NOTES.md reflects current functionality
- [ ] Installation instructions clear and accurate
- [ ] Configuration steps documented
- [ ] Automatic folder setup documented

### Known Issues Documented
- [ ] Report generation warning included in docs
- [ ] Known limitations listed
- [ ] WAIT UNTIL LOCALTIME risks explained
