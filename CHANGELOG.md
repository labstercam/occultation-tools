# Changelog

All notable changes to the Occultation Manager project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Maintenance
- Brief cleanup pass completed to archive or remove out-of-date code/files.

### Documentation
- Documentation refreshed for current structure and release-facing guidance.

## [0.2.0-beta.2] - 2026-02

### Documentation
- Updated release-facing version references from `0.2.0-beta.1` to `0.2.0-beta.2` in user and release-prep documentation.
- Updated installation package name and GitHub release download URL in `occultation-manager/ReadMe.md`.
- Updated embedded Quick Start install package reference in `occultation-manager/python/help.py`.
- Updated current version context in `occultation-manager/ARCHITECTURE.md`.

### Release Preparation
- Consolidated development-oriented markdown docs into `occultation-manager/python/development documentation/`.
- Updated moved-doc references in `occultation-manager/python/ReadMe.md` and `occultation-manager/python/lib/README.md`.

## [0.1.0] - 2026-01-22

### Initial Release

First public release of Occultation Manager for SharpCap - a tool for managing asteroid occultation observations through customizable SharpCap sequences.

### Core Features

#### Event Management
- Automated event download from OccultWatcher Cloud (OWC)
- Station-based filtering for assigned events
- Event grid with sortable columns and detailed information
- Quick filters (Today/Future/All) for date-based filtering
- Custom exposure, gain, and recording duration settings per event
- Event details dialog with complete timing and magnitude information

#### Sequence Generation
- Template-based SharpCap sequence (.scs) file generation
- Five included templates:
  - **SharpCap Sequence UTC Template** (⭐ RECOMMENDED) - UTC-based timing, safe for all scenarios
  - SharpCap Sequence Local Time Template - Full automation with local time (midnight issues)
  - SharpCap Minimal Local Time Template - Basic automation, manual camera setup
  - SharpCap Just Record Template - Recording only, no GOTO/plate solve
  - SharpCap Test Recording Template - For testing equipment
- Custom template support (any .txt file with "template" in filename)
- 17 placeholder variables for complete event data substitution
- Customizable per-event or single template for all events

#### Observation Preparation
- Interactive telescope positioning (GOTO & Center)
- Plate solving and target verification
- Manual camera setup and configuration
- Test Recording feature with automatic settings save/restore
- Pre-observation equipment testing

#### Configuration
- Complete credential management for OWC integration
- Configurable file paths (templates, sequences, event data, reports)
- Recording parameter customization (base duration, GOTO lead time, exposure calculation)
- Equipment profiles (multiple telescopes and cameras)
- Observer information management
- Retention period for downloaded events (1-400 days)

#### User Interface
- Night Mode with red theme for observing sessions
- DPI-aware scaling for high-resolution displays
- Comprehensive help system with Quick Start, Workflow, and Template Modification guides
- Tooltips with detailed explanations throughout
- Themed dialogs consistent across application

### Experimental Features

⚠️ **WARNING**: The following features are experimental and not approved by reporting coordinators. **Always verify all data before submission.**

#### Report Generation (Experimental)
- North America (IOTA) Excel report generation (V5.6.12r)
- Trans-Tasman (RASNZ) Excel report generation (V4.1.2.G)
- AOTA timing data integration (.aota.xml and AOTA_Report.txt)
- Tangra CSV light curve data integration
- Equipment and observer data pre-population
- Reports saved to `[File Folder]/Reports/` subfolder

### Known Limitations

#### Local Time Placeholders
- Local time placeholders (`{*_time_local}`) output TIME ONLY (no date)
- Times after midnight will NOT work with `WAIT UNTIL AFTER LOCALTIME` command
- Next-day events will fail (01:00:00 appears earlier than 23:00:00 in time-only comparison)
- Daylight saving time changes can cause timing errors
- **Strongly recommend using UTC timing with {pre_goto} placeholder and custom countdown functions**

#### Report Generation
- Report generation is experimental
- Not approved by IOTA or RASNZ reporting coordinators
- Manual verification required before submission
- Excel templates must be unprotected for editing
- Some field mappings may need adjustment based on coordinator feedback

### Technical Details

#### File Locations
- **Templates** (read from): File Folder - any .txt file with "template" in filename
- **Sequences** (saved to): Sequence Path (defaults to File Folder if empty)
- **Reports** (saved to): `[File Folder]/Reports/` (automatically created)
- **Event Data**: `occultations.json` and `occultations_latest.json` in File Folder

#### System Requirements
- SharpCap 4.1 or later (recent version recommended)
- IronPython 2.7 (included with SharpCap)
- Windows operating system
- Active OccultWatcher Cloud account with API access
- Internet connection for event downloads

#### Dependencies
All dependencies are built-in to SharpCap's IronPython environment:
- System.Windows.Forms for GUI
- System.Drawing for graphics and theming
- Standard Python libraries (os, json, datetime, etc.)

### Installation

1. Download `occultation-manager.zip` from GitHub Releases
2. Extract to a folder with read/write access (recommended: Documents\SharpCap\occultation-manager)
3. Start SharpCap
4. Go to File → SharpCap Settings → Startup Scripts
5. Browse to extracted folder and select 'main' script
6. Click OK and restart SharpCap
7. "Occultations" button appears in SharpCap main toolbar

### Documentation

- **Quick Start Guide**: Help → User Guide → Quick Start
- **Event Recording Workflow**: Help → User Guide → Event Recording Workflow
- **Template Modification**: Help → User Guide → Template Modification
- **README.md**: Complete feature overview and customization guide
- **RELEASE_INSTRUCTIONS.md**: Detailed file list and release process

### License

BSD 3-Clause License - See LICENSE file for full text.

### Credits

**Author**: Michael Camilleri

**Repository**: https://github.com/labstercam/occultation-tools

---

## Future Releases

Future versions will focus on:
- User feedback and bug fixes
- Enhanced template customization options
- Additional report format support (SODIS Europe, IOTA East Asia)
- Improved error handling and validation
- Performance optimizations
- Extended help documentation with examples

---

**Note**: Version numbers follow [Semantic Versioning](https://semver.org/):
- MAJOR version for incompatible API changes
- MINOR version for added functionality in a backwards compatible manner
- PATCH version for backwards compatible bug fixes
