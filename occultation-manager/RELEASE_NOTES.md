# Occultation Manager - Release Notes

## Version 0.2.0-beta.3 (March 2026)

**Bug Fixes, User Improvements, Documentation and Release Preparation Update**

- Bugs fixes from user testing reports
- Improvements based on user feedback including better folder and file management
- Performed a brief cleanup to archive or remove out-of-date code/files.
- Updated release-facing documentation and version references for Beta.3.
- Updated release packaging/version pointers (ZIP naming and instructions).
- Release packaging now pre-seeds `data/templates` with sequencer master templates.

---

## Version 0.2.0-beta.2 (February 2026)

**Excel Report Generation Improvements**

This release improves Excel report generation with the Openize SDK for more reliable, maintainable report creation with enhanced IronPython compatibility.

### What's New in Beta.2

#### Openize SDK Implementation
- **Direct Excel Cell Manipulation**: Uses Openize.OpenXML-SDK for direct cell access via IronPython
- **No More XML Placeholders**: Eliminates manual XML string replacement approach
- **Preserves Excel Features**: Maintains data validation, formulas, and formatting
- **IronPython Compatible**: Fully tested with IronPython 3.4.2 on .NET 8.0
- **Bundled DLLs**: Required .NET assemblies included in release package

#### Enhanced Report Features
- **Conditions Section**: Added clouds and stability fields to comprehensive report dialog
- **Occult XML Integration**: Conditions automatically mapped to Occult XML transparency/stability codes
- **Improved Reliability**: More robust Excel manipulation without file corruption risks
- **Better Debugging**: Enhanced logging for troubleshooting report generation

#### Technical Improvements
- New report generators: `tt_report_openize.py` and `na_report_openize.py`
- Template files relocated from development documentation to python folder
- Simplified template management (no more _Template.xlsx placeholders)
- Comprehensive conditions mapping for Occult 4 XML export

#### Installation Requirements
- **Openize SDK DLLs** (included in release):
  - Openize.OpenXMLSDK.dll (~500-800 KB)
  - DocumentFormat.OpenXml.dll (~5-8 MB)
  - DocumentFormat.OpenXml.Framework.dll (~100-200 KB)
- DLLs located in `lib/` folder with installation guide
- No additional downloads required - all dependencies included

#### Breaking Changes
- Excel templates updated to non-placeholder versions
- Old XML-based report generators removed

### Technical Details

**Report Generator Architecture:**
- Uses Openize.Cells.Workbook for Excel file access
- Direct cell writing via row/column coordinates
- Cell references: H27 (clouds), P27 (stability), X27 (other conditions)
- SNR extraction from cell W40 for Occult XML export

**Conditions Mapping:**
- Clouds → Transparency codes: Clear=1, Some Clouds=2, Intermittent Clouds=3, Cloudy=4, Very Cloudy=5, Overcast=6, Other Conditions=7
- Stability: Excellent=1, Good=2, Poor=3
- Automatic mapping for Occult 4 XML <Conditions> line

**Documentation Updates:**
- Architecture documentation reflects Openize implementation
- Removed legacy XML placeholder references
- Updated report generator file names and line counts

---

## Version 0.2.0-beta.1 (January 2026)

**First Public Beta Release**

This is the first public beta release of Occultation Manager. Below is a summary of key features and capabilities.

### Installation & Configuration

#### Automatic Setup
- Release ZIP includes pre-created folder structure: `files/`, `sequences/`, and `files/Reports/` with README guides
- First startup automatically detects installation directory and creates folder structure
- Smart path detection uses Python `__file__`, `sys.argv[0]`, or current directory as fallbacks
- Template files distributed to both main folder (originals) and `files/` folder (working copies)
- Configuration stored in `{install_dir}/files/occultation_config.json`
- Custom paths from previous installations are preserved

#### Simple Installation
- Extract and run - no manual folder creation needed
- Default paths automatically set to installation directory
- Configuration file automatically placed in data folder
- Clear README files in each folder explaining purpose
- Template files ready to customize in files folder

### Core Features

#### Sequence Execution
- **Run Sequences** button for direct multi-sequence execution from Occultation Manager
- **Test Recording** with automatic camera settings preservation and restoration
- SharpCap remains fully responsive during all sequence operations
- Asynchronous execution using SharpCap's `RunAsync()` API

#### Safe Stop Capability
- **Stop button** in Observation Preparation panel
- Confirmation dialog prevents accidental stops
- Automatic camera settings restoration after stop
- Works with both Test Recording and Run Sequences
- Comprehensive cleanup on stop or error

#### Camera Settings Management
- Automatic save before sequence execution
- Non-blocking restoration with stabilization period
- Preserves: binning, exposure, gain, resolution, display levels
- Background thread for camera stabilization (2× exposure time)
- Safe for all camera types and configurations

### Workflow Features

#### Run Sequences
- Select multiple events with checkboxes
- Click Run Sequences button for automated execution
- Sequences run in chronological order automatically
- Real-time progress updates ("Running sequence 2/5: Event Name")
- Eliminates manual .scs file loading in SharpCap Sequencer
- Suitable for multi-event observation sessions

#### Test Recording
- Fully non-blocking - SharpCap remains responsive
- Stop button available during test
- All camera settings automatically saved and restored
- Display levels preserved (stretch settings)
- Safe testing without disrupting your configuration

### Countdown and Timing Features

#### UTC-Based Countdown Functions
Three countdown options for reliable timing in sequences:

**Option 1: Simple Notification** (not recommended - timing risks)
- Basic SharpCap notification with WAIT UNTIL LOCALTIME
- Subject to midnight and next-day event failures

**Option 2: UTC Notification Countdown** (RECOMMENDED)
- Auto-updating notification with formatted countdown
- Displays Days HH:MM:SS format
- Adaptive update rate: 1-minute intervals when >5 min remaining, 1-second when ≤5 min
- Safe for 24+ hour countdowns (no recursion limit issues)
- Color-coded warnings (<5 min amber, <1 min red)
- UTC-based: no timezone or midnight issues
- Safe for late starts and next-day events
- Stoppable via SharpCap Stop button (may take up to 60s when >5 min remaining)

**Option 3: UTC Dialog Countdown**
- Windows dialog with large countdown display
- Adaptive update rate: 1-minute intervals when >5 min remaining, 1-second when ≤5 min
- Safe for 24+ hour countdowns (no recursion limit issues)
- Dedicated Stop button in dialog (may take up to 60s to respond when >5 min remaining)
- Most complex implementation
- Use only if large visible countdown needed

#### WAIT UNTIL LOCALTIME Risks (CRITICAL)
**SharpCap's WAIT UNTIL LOCALTIME commands can cause you to MISS EVENTS:**

1. **No Date Awareness**: SharpCap only knows TIME, not DATE
   - Events after midnight may wait 24 hours
   - Late starts can miss events entirely

2. **Next-Day Event Failure**: 
   - Event at 01:00:00 started at 23:00:00 fails completely
   - Sequencer waits until next day's 01:00:00
   - **Event is missed!**

3. **Daylight Saving Time**: Clock changes cause timing errors

**Recommendation**: Use UTC-based countdown functions (Option 2) for all critical 
observations. These handle midnight, next-day events, and DST correctly.

#### Sequence Execution Methods

**Method 1: SharpCap Sequencer (RECOMMENDED - Safest)**
- Load .scs file directly in SharpCap's Sequencer
- Simplest and most reliable approach
- **Recommended for unattended operation**
- **Recommended for remote operation**
- Fewest points of failure

**Method 2: Occultation Manager Run Sequences (Alternative)**
- Note: It is safer to run sequences directly from SharpCap.
- Note: Combined Sequences can only be run directly from SharpCap.
- Run from Occultation Manager's Run Sequences button
- More complex with additional monitoring layer
- Provides Stop button control
- **Suitable for attended multi-event sessions**
- **Not recommended for unattended operation**
- Additional complexity may reduce reliability

**Reference Files:**
- `countdown python for sequencer.scs` - Ready-to-copy countdown code snippets
- Complete implementation notes and examples included

### Technical Implementation

#### Threading Architecture
- UI Thread (STA): All `RunAsync()` calls, UI updates, SharpCap API calls
- Monitor Thread (MTA): Background status polling, doesn't touch UI directly
- Proper thread marshaling via `Invoke()` for all UI operations
- Background monitoring using Python `threading.Thread`

#### API Usage
- Asynchronous execution using SharpCap's `RunAsync()` API
- Proper thread marshaling to UI thread (STA requirement) for all sequence operations
- Background monitoring threads track sequence execution status
- Comprehensive state management with race condition prevention
- Robust error handling with automatic cleanup in all code paths

### Known Limitations
- Cannot pause sequences (stop and restart only)
- No step-level stop granularity (completes current step before stopping)
- Single sequence execution at a time (no parallel sequences)

### Report Generation (Under Development - Not Approved)

⚠️ **CRITICAL WARNING**: Report generation is still under development and has **NOT** been approved by North America (IOTA) or Trans-Tasman (RASNZ) reporting coordinators. Use with extreme caution and verify all generated data before submission.

#### Current Report Capabilities
- Single comprehensive dialog for workflow efficiency
- Integrates AOTA timing data (D/R times)
- Imports Tangra CSV light curve analysis
- Automatic video format extraction from Tangra CSV files
- Dynamic exposure/integration detection based on timing consistency
- Supports North America (IOTA) and Trans-Tasman (RASNZ) formats
- Auto-fills observer, telescope, and camera information
- Remembers previous settings for faster workflow

#### Timing Integration Status
- ✅ **Tangra CSV Light Curve Analysis**: Fully integrated
  - Extracts start/end times from Tangra CSV files
  - Populates exposure time and camera acquisition delay
  - Video format sourced from Tangra measurement parameters
  - Automatic HH:MM:SS.SS time formatting
  
- ⚠️ **GPS Flash Timing Analysis**: Not yet integrated into Occultation Manager
  - Functions available in gps-timing-analysis toolkit
  - Available as standalone tool for experts with custom Python code
  - Future integration planned

**Always verify all report data independently before submission to regional coordinators.**

### Documentation

Documentation includes:
- Comprehensive user guide accessible via Help menu
- Installation and configuration instructions
- Workflow guides for all major features
- Countdown and notification options with examples
- WAIT UNTIL LOCALTIME risks and limitations explained
- Sequence execution methods comparison
- `countdown python for sequencer.scs` reference file with ready-to-use code snippets

---

## Support and Feedback

This is a beta release. Please report issues, bugs, and feedback through GitHub Issues.

### Known Issues
- None reported yet

### Reporting Issues
When reporting issues, please include:
- SharpCap version
- Camera type and connection method
- Steps to reproduce the issue
- Any error messages displayed
- Sequence file if relevant (sanitize personal info)
- All cross-thread calls marshaled via `Invoke()` to UI thread

**State Management:**
- Six instance variables track execution state
- Comprehensive cleanup in all error paths
- Race condition prevention via state checks
- Context tracking for appropriate user messages

**Performance:**
- 1-second polling interval for status monitoring
- Minimal CPU overhead
- No UI blocking or freezing
- 2-second delay between sequences in multi-sequence execution

---
---

## Version History

This is the first public beta release. Previous versions were internal development builds not released publicly.

### From 0.1.0 to 0.2.0
1. Replace Python files with updated versions
2. No configuration changes required
3. Existing sequence files continue to work
4. Test the new Run Sequences and Stop button features
5. Enjoy non-blocking operation!

---

## Support

For issues, questions, or feature requests:
- GitHub Issues: https://github.com/labstercam/occultation-tools/issues
- Documentation: See README files and Help → User Guide
- Technical Details: See [RunAsync Implementation](python/development documentation/RunAsync_Implementation.md)

---

*Release notes maintained by: Michael Camilleri*  
*Last updated: January 24, 2026*
