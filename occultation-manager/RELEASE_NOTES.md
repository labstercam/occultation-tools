# Occultation Manager - Release Notes

## Version 0.2.0-beta.1 (January 2026)

### Major Features: Async Sequence Execution

#### Non-Blocking Sequence Execution
- **Run Sequences** button for direct multi-sequence execution from Occultation Manager
- **Test Recording** with automatic camera settings preservation and restoration
- SharpCap remains fully responsive during all sequence operations
- No more UI freezing or complete application lock-ups

#### Safe Stop Capability
- **Stop button** in Observation Preparation panel
- Confirmation dialog prevents accidental stops
- Automatic camera settings restoration after stop
- Works with both Test Recording and Run Sequences
- Comprehensive cleanup on stop or error

#### Technical Improvements
- Implemented using SharpCap's `RunAsync()` API for asynchronous operation
- Proper thread marshaling to UI thread (STA requirement) for all sequence operations
- Background monitoring threads track sequence execution status
- All sequence steps now work correctly:
  - Display stretch and auto-stretch operations
  - Show notification commands
  - Camera control UI updates
  - All other UI-touching sequence operations
- Fixed critical STA (Single Threaded Apartment) threading issue
- Comprehensive state management with race condition prevention
- Robust error handling with automatic cleanup in all code paths

#### Camera Settings Management
- Automatic save before sequence execution
- Non-blocking restoration with stabilization period
- Preserves: binning, exposure, gain, resolution, display levels
- Background thread for camera stabilization (2× exposure time)
- Safe for all camera types and configurations

### Workflow Enhancements

#### Run Sequences (New Feature)
- Select multiple events with checkboxes
- Click Run Sequences button for automated execution
- Sequences run in chronological order automatically
- Real-time progress updates ("Running sequence 2/5: Event Name")
- Eliminates manual .scs file loading in SharpCap Sequencer
- Perfect for multi-event observation sessions

#### Test Recording (Enhanced)
- Now fully non-blocking - SharpCap remains responsive
- Stop button available during test
- All camera settings automatically saved and restored
- Display levels preserved (stretch settings)
- Safe testing without disrupting your configuration

### Bug Fixes
- **Fixed**: Test Recording menu item referenced non-existent method
- **Fixed**: STA threading error when sequences use display operations
- **Fixed**: Duplicate context clearing in completion handler
- **Fixed**: Missing context cleanup in error paths
- **Fixed**: Race conditions in stop button handling
- **Fixed**: Lambda closure captures in background threads
- **Fixed**: Sequences menu was commented out (inaccessible)
- **Removed**: Dangerous blocking `RunSequenceFile()` dead code

### Documentation
- New comprehensive [RunAsync Implementation](python/development documentation/RunAsync_Implementation.md) document
- Updated Help → User Guide with async execution workflow
- Updated all README files with Run Sequences and Stop button information
- Added technical details about threading requirements
- Documented camera settings preservation workflow
- **NEW**: Added countdown and notification options documentation
- **NEW**: Created `countdown python for sequencer.scs` reference file with ready-to-use code snippets
- **NEW**: Documented WAIT UNTIL LOCALTIME risks and limitations
- **NEW**: Explained sequence execution methods (SharpCap vs Occultation Manager)

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
- Run from Occultation Manager's Run Sequences button
- More complex with additional monitoring layer
- Provides Stop button control
- **Suitable for attended multi-event sessions**
- **Not recommended for unattended operation**
- Additional complexity may reduce reliability

**Files:**
- `countdown python for sequencer.scs` - Ready-to-copy countdown code snippets
- Complete implementation notes and examples included

### API Changes
- All sequence execution now uses `RunAsync()` instead of blocking `RunSequenceFile()`
- Proper thread marshaling via `Invoke()` for all UI operations
- Background monitoring using Python `threading.Thread` (not .NET threads)

### Migration Notes
- **No user action required** - all changes are internal improvements
- Existing sequence files (.scs) work without modification
- Templates continue to work as before
- All sequence operations now more reliable and safe

### Known Limitations
- Cannot pause sequences (stop and restart only)
- No step-level stop granularity (completes current step before stopping)
- Single sequence execution at a time (no parallel sequences)

### Technical Details

**Threading Architecture:**
- UI Thread (STA): All `RunAsync()` calls, UI updates, SharpCap API calls
- Monitor Thread (MTA): Background status polling, doesn't touch UI directly
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

## Version 0.1.0 (December 2025)

### Initial Release

#### Core Features
- Event download from Occult Watcher Cloud
- Event list management with filtering and sorting
- Configurable event retention period (1-400 days)
- SharpCap sequence generation with customizable templates
- Equipment management (telescopes and cameras)
- Observation preparation panel with manual GOTO, plate solve, setup

#### Templates Provided
- SharpCap Sequence UTC Template (recommended)
- SharpCap Sequence Local Time Template
- SharpCap Minimal Local Time Template
- SharpCap Just Record Template
- SharpCap Test Recording Template

#### Report Generation (Under Development - Not Approved)
⚠️ **CRITICAL**: Report generation is still under development and has NOT been approved by North America or Trans-Tasman reporting coordinators. All generated reports must be carefully verified before submission.

- North America (IOTA) report format
- Trans-Tasman (RASNZ) report format
- AOTA timing data integration
- Tangra CSV light curve analysis (integrated)
- GPS flash timing analysis (not yet integrated - available as standalone tool for experts)
- Automatic video format detection
- Dynamic exposure/integration detection

#### Configuration
- OWC credentials management
- File path configuration
- User settings (exposure calculation, gain defaults)
- Station filtering
- Theme support (normal and night mode)

---

## Upgrade Path

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
