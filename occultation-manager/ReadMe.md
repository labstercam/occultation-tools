# Occultation Manager

**Version 0.2.0-beta.7** - SharpCap add-in for automated occultation observations

SharpCap Occultation Manager streamlines your occultation observation workflow by automating event management and generating customizable SharpCap sequences. It downloads your announced observations from Occult Watcher Cloud and creates sequences tailored to your equipment and recording preferences. Sequences can be run interactively or unattended for fully automated recordings for an entire nights observations. The sequences can be run on remote PCs without internet connection for multiple station deployments.

Occultation Manager generates reports for NA, TT and SODIS and Occult 4 XML, populating all event details, event D/R, and manages telescope, camera, station location and condition information from within the tool. No more copying and pasting from multiple different applications.

The workflow can be as simple as announce stations in Occult Watcher Cloud, open Sharpcap Occultation Manager, press Download, then Create Sequences, then Run Sequences and an entire nights observations are set up and running!

## Workflow

1. **Download Events**: Sync with Occult Watcher Cloud to download your stations announced in OW Cloud or via OW Desktop
<img width="1063" height="321" alt="image" src="https://github.com/user-attachments/assets/2630915b-d967-4a5c-910a-5b4bb6ef3b08" />

2. **Prepare for Observation (optional)**: Use the Observation Preparation panel to set up for your event for either live or automated recording
   - **Load Event**: Select an event from the grid to prepare
   - **GOTO**: Automatically slew your mount to the event coordinates
   - **Plate Solve**: Verify pointing and label the target star
   - **Setup**: Configure and SharpCap camera settings (exposure, coordinates)
   - **Test Recording**: Make a short test recording to verify setup without disrupting your settings
3. **Customize Settings (optional)**: Override calculated exposure, gain, or recording duration if needed
4. **Generate Sequences**: Create customized SharpCap sequences for automated recording of single events or multiple events
<img width="391" height="248" alt="image" src="https://github.com/user-attachments/assets/f503a43f-d610-46d1-a69a-a4895ca93c05" />

6. **Run Sequences**: Run the sequence(s) to record the occultation from occultation-manager, or use the SharpCap Sequencer separately
7. **Generate Reports**: Confirm observer location, optionally run NTP analysis, then load Tangra/AOTA analysis and generate reports for North America, Australasia or SODIS reporting systems (working prototypes)
<img width="494" height="407" alt="image" src="https://github.com/user-attachments/assets/6720113f-5cf5-4e08-a689-7588f370cdeb" />
  
8. **Validate Timing (optional)**: Use **Tools → NTP Clock Accuracy** or **Tools → GPS vs NTP Testing** for independent UTC accuracy verification
  

## 📦 Installation

### Quick Start

1. **Download**: Get the latest release `occultation-manager-v0.2.0-beta.7.zip` [https://github.com/labstercam/occultation-tools/releases/download/v0.2.0-beta.7/occultation-manager-v0.2.0-beta.7.zip](https://github.com/labstercam/occultation-tools/releases/download/v0.2.0-beta.7/occultation-manager-v0.2.0-beta.7.zip)
2. **Extract**: Unzip to a location with read/write access (e.g., `Documents\SharpCap`)
   - ⚠️ **Avoid Program Files** - Windows may restrict write access
   - ✅ **Recommended**: `Documents\SharpCap`
3. **Load in SharpCap**:
   - Open SharpCap
   - Go to **File → SharpCap Settings → Startup Scripts**
   - Browse to the extracted `app` folder
   - Select the `app/main.py` script
   - Click OK and restart SharpCap

<img width="666" height="155" alt="SharpCap Settings" src="https://github.com/user-attachments/assets/42a9d9c9-4273-4a88-8d0a-428cca649afe" />

4. **Launch**: Click the new **Occultations** button in the SharpCap toolbar

<img width="117" height="28" alt="Occultations Button" src="https://github.com/user-attachments/assets/6dbdf7af-aea5-4637-a39a-ff8a435dce55" />

### First Startup - Automatic Setup

On first launch, the Occultation Manager automatically:
- **Detects installation location** and uses fixed folders
- **Creates folder structure**:
   - `data/config/` - Configuration file storage
   - `data/events/` - Event JSON files
   - `data/templates/` - Working template copies (user-editable)
   - `data/sequences/` - SharpCap sequence files (.scs)
   - `data/reports/` - Generated Excel reports
- **Saves configuration** to `data/config/occultation_config.json`

**Template files** are sourced from:
- `resources/templates_master/` - Master templates (distributed)
- `data/templates/` - Working copies used by sequence generation

### Configuration

After installation, configure the application:

1. **Credentials** (Required):
   - Go to **Tools → Configuration → Credentials**
   - Enter your Occult Watcher Cloud email and API key
   - Set **Days to Retain** for event history (default 14, range 1-400)
   - Get your API key at: https://cloud.occultwatcher.net/user-profile

2. **File Paths Tab**:
   - Paths are fixed to the installation folder structure
   - Use built-in buttons to open Explorer for:
     - `data/config/`
     - `data/events/`
     - `data/reports/`
     - `data/sequences/`
     - `data/templates/`

3. **Observer Settings**:
   - **User Settings**: Observer name, location, telescope details
   - **Equipment**: Add telescopes and cameras with specifications
   - **Report Info**: Contact information for report generation

4. **Save Configuration**: Click Save to store all settings

### Folder Structure

After extraction and first run:
```
occultation-manager/
├── app/                             # SharpCap startup and Python modules
│   ├── main.py                      # SharpCap startup script
│   ├── *.py
│   └── lib/                         # Openize SDK DLLs
├── resources/
│   └── templates_master/            # Distributed master templates
│       ├── sequencer/
│       └── reports/
└── data/                            # User data (auto-created)
   ├── config/occultation_config.json
   ├── events/occultations.json
   ├── templates/                   # Working template copies
   ├── sequences/                   # Generated .scs files
   └── reports/                     # Generated report files
```

## Key Features

**Event Management**
- Downloads personal observations from Occult Watcher Cloud
- Manages event list with filtering by date, location, and probability
- Configurable event retention period (1-400 days, default 14)
- Automatic SharpCap sequence generation with customizable templates
- Customizable per-event settings (exposure, gain, recording duration)
- **Generate Dummy Events**: Create realistic test events for practice and testing
  - Configure event timing, location, and spacing
  - Events visible from your observatory location
  - Easy deletion when no longer needed
- **Observation Preparation Panel**: Integrated workflow for setting up events
  - Load event for preparation with summary display
  - GOTO mount control with automatic slewing
  - Plate solve verification and target labeling
  - Camera setup with exposure and coordinate configuration
  - Test recording with automatic settings preservation and restoration

**SharpCap Sequence Generation**
- Full control over recording workflow through customizable templates
- Automated mount control, camera configuration, and recording
- Flexible templates for any equipment setup or recording style
- Support for unattended multi-event observation sessions
- Built-in templates: Full automation, minimal setup, and test recording
- Sequences use calculated or custom exposure, gain, and duration values

**Report Generation (Under Development)**
- ⚠️ **Not Approved**: Report generation is still under development and has not been approved by the NA, TT, or SODIS reporting coordinators
- ⚠️ Only TANGRA and AOTA outputs are currently supported
- Single comprehensive dialog for workflow efficiency
- Report flow now includes **Confirm Observer Location** with optional **Step 2 NTP timing analysis**
- Optional NTP actions:
   - **Open NTP Analyser** (non-blocking, separate analyzer window)
   - **Analyze NTP** (quick in-flow offset/uncertainty estimate)
- NTP quick analysis uses a single NTP stats folder input, auto-selects loopstats/peerstats for the event date/time, and remembers the last selected folder
- Shared NTP resources are loaded from `gps-timing-analysis/resources/` (including `national_utc_ntp_servers.json` and `ip_location_cache.json`)
- Supports Tangra, R-OTE, and Limovie CSV light curve formats; format is auto-detected from file content
- Integrates AOTA timing data from AOTA XML, AOTA Report files, or PyOTE `fit_metrics.txt`
- **PyOTE fit_metrics.txt**: auto-detected from the observation folder by file content; select aperture/event then import D/R times directly into the report
- Camera timing calibration is now integrated: use **Tools → Camera Delay Calibration** to calibrate, save results to the camera profile via **Save Calibration to Camera**, and calculate per-event acquisition delays via **Tools → Camera Delay Calculator**
- GPS timestamp offset and advanced timing analysis remain available as standalone tools in `gps-timing-analysis`
- Uses Openize SDK for direct Excel cell manipulation (NA/TT)
- Supports SODIS/IOTA-ES plain-text report generation (Form 2.03)
- Preserves Excel data validation and formulas
- Automatic Occult 4 XML export with matching filename
- Observing conditions capture (clouds, stability, other notes)
- Supports North America (IOTA), Trans-Tasman (RASNZ), and SODIS (IOTA-ES) formats
- Use with caution and verify all generated data before submission

**Tools Menu**
- **Camera Delay Calibration**: LED line delay calibration for rolling-shutter cameras (requires SharpCap live capture or ADV replay); results can be saved directly to the camera profile. An "Approximate Delays" option is available when no GPS flasher is available.
- **Camera Delay Calculator**: Calculate the rolling-shutter acquisition delay for a given star Y pixel position using stored line delay calibrations; one-click copy to clipboard in TANGRA format
- **NTP Clock Accuracy**: Full loopstats/peerstats offset, jitter, and delay charting with uncertainty estimate; launched as a separate non-blocking window
- **GPS vs NTP Testing**: Measures UTC error of each internet NTP server relative to a GPS PPS refclock using the same NTP dataset; produces per-server uncertainty table, clock drift regression, and three charts (delay, UTC error, selected peer + trend)

**Equipment Management**
- Multiple telescope and camera configurations
- Active equipment selection
- Equipment details automatically populate reports
- **Line delay calibration management**: view, label (A, B, C…), edit notes, and delete stored calibration runs per camera via **Calibrations...** button in Camera Manager
- **Run New Calibration** from Camera Manager to launch the Camera Delay Calibration form with the selected camera pre-selected

## Benefits

1. **Complete Control**: SharpCap sequences give you full flexibility over your recording workflow
2. **Customizable Automation**: Automate as little or as much as needed for your setup
3. **Equipment Flexibility**: Templates can be adapted to any telescope, mount, and camera combination
4. **Simplified Event Management**: No need for Occult Watcher Desktop for predictions
5. **Multi-Event Sessions**: Generate sequences for entire night's observations
6. **Safe Testing**: Test recordings preserve your camera settings automatically

## SharpCap Sequences - Your Recording Workflow

The Occultation Manager generates SharpCap Sequences that give you complete control over your recording workflow. By using sequences, you can customize the automation to match your equipment, observing style, and comfort level.

**Why Use Sequences?**
**Why Use Sequences?**
- **Complete Control**: You decide what gets automated and what stays manual
- **Equipment Specific**: Adapt to your exact telescope, mount, camera, and accessories
- **Safety First**: Control mount movements, pointing, and post-observation positioning
- **Multi-Event Capable**: Generate sequences for entire night's observations
- **Reliable**: Test and refine your templates before relying on them

### Template Variables
Templates use Python string formatting with the following variables from each event:
- **{exposure}**: Exposure time in seconds (calculated or custom override)
- **{gain}**: Camera gain 0-600 (default 450 or custom override)
- **{recording_duration}**: Total recording duration in seconds (calculated or custom override)
- Additional variables: start/end times, coordinates, event details

### Provided Templates

Five templates are included demonstrating different automation levels and timing approaches:

**⭐ SharpCap Sequence UTC Template** (RECOMMENDED - Full Automation with UTC Timing):
- **Best and safest template** with proper UTC-based countdown system
- Handles times safely regardless of when started (late start, next day, after midnight)
- User can safely stop and restart countdown without missing events
- Fully configures mount and camera for each observation
- Sets binning, ROI, file format, exposure, gain, and recording settings
- Automated GOTO, plate solve, and safe finish positioning
- Parks mount in safe position after each observation
- Suitable for unattended multi-night operation
- Uses Python code for accurate UTC countdown calculations

**SharpCap Sequence Local Time Template** (Full Automation with Local Time):
- ⚠️ **Less safe**: Has problems with times after local midnight
- ⚠️ **Cannot handle next day events**: Only works for current night observations
- Fully configures mount and camera like UTC template
- Requires manual "WAIT UNTIL" statements to prevent premature start
- Risk of missing events if local time crosses midnight
- Must add 86400 second delays for each day's wait, or use UTC template instead

**SharpCap Minimal Local Time Template** (Basic Automation):
- ⚠️ **Same local time risks** as above (midnight issues, current night only)
- Assumes you've manually configured most camera recording settings
- Automated GOTO and plate solve
- Only adjusts exposure and gain for each event
- Minimal automation for those wanting more manual control

**SharpCap Just Record Template** (Manual Setup):
- Bare bones recording only - no GOTO, no plate solve, no camera setup
- Uses local time for recording start (same midnight risks)
- Assumes user has already pointed telescope and configured camera
- Intended for ad-hoc interactive use
- Only sets target name and triggers recording at event time

**SharpCap Test Recording Template** (Verification):
- Immediate short recording for pre-event testing (no waiting)
- Used automatically by the **Test Recording** button
- Verifies focus, framing, and camera settings
- Automatically restores camera settings after test
- Configures binning, ROI, format, exposure, and gain for test

### Critical: Test and Customize

⚠️ **You MUST test and adapt these templates to your specific setup before using them for observations.** The provided templates are examples only.

**Before relying on any template:**
- Test extensively during daytime with your actual equipment
- Verify all mount movements are safe and correct
- Check that camera settings match your requirements
- Ensure file paths and formats work with your system
- Test unattended operation thoroughly before trusting it
- Consider cable management and equipment safety
- Plan for post-sunrise mount positioning

**Safety Considerations:**
- Risk of equipment damage from cable snags or incorrect pointing
- Risk of sun exposure if sequence runs past sunrise
- Risk of failed observations due to untested settings
- Unattended operation requires extensive testing and safety planning

## Event Customization

The Occultation Manager automatically calculates optimal exposure times and recording durations for each event based on the predicted magnitude drop and event duration. However, you can override these defaults for specific events:

### Edit Settings Dialog
Double-click on an event's Exposure, Gain, or Recording Time column (or use the **Edit Settings** toolbar button) to customize:

**Exposure Time (1-10000 ms)**
- Calculated from predicted magnitude drop (brighter drops = shorter exposure)
- Override for specific camera sensitivity or event characteristics
- Quick buttons: 40, 80, 120, 160, 200, 240, 320, 480 ms

**Gain (0-600)**
- Default value configurable in Tools → Configuration → User Settings
- Standard default: 450
- Override for specific camera or event requirements
- Quick buttons: 200, 250, 300, 350, 450, 550

**Recording Duration (10-3600 seconds)**
- Calculated as: (uncertainty × 8) + (max_duration × 2)
- Override for specific event timing requirements
- Quick buttons: 30, 60, 90, 120, 180, 300 seconds

### Custom Value Indicators
The event grid displays an asterisk (*) next to values that have been customized:
- **Exposure (ms)*** - Custom exposure time
- **Gain*** - Custom gain value
- **Recording Time (s)*** - Custom recording duration

### Reset to Defaults
Use the Reset button in the Edit Settings dialog to restore calculated values. The system intelligently detects when custom values match calculated defaults and removes the custom flag automatically.

## Observation Preparation

The Observation Preparation panel provides an integrated workflow for setting up and testing your observation before the actual event. Select exactly one event from the grid to use these features:

### Load Event
Loads the selected event into the preparation panel, displaying key information:
- Asteroid name and event time (UTC)
- Altitude and azimuth coordinates
- Exposure time (calculated or custom)
- Maximum event duration
- Star magnitude

### GOTO
Automatically slews your telescope mount to the event coordinates. Requires SharpCap integration with your mount software (ASCOM, etc.).

### Plate Solve
Performs plate solving to:
- Verify mount pointing accuracy
- Calculate offset from target coordinates
- Label the target star in the field of view

Use this after GOTO to confirm your telescope is correctly positioned.

### Setup
Configures SharpCap camera settings for the event:
- Sets the exposure time to the calculated/custom value
- Copies event coordinates (RA/Dec) to clipboard for manual entry if needed
- Prepares camera for the observation

### Test Recording
Makes a short test recording to verify your setup without disrupting your carefully configured camera settings. The test recording:

**What it does:**
1. Saves your current camera settings (binning, exposure, gain, resolution, display levels)
2. Runs a short recording sequence using the "SharpCap Test Recording Template.txt"
3. **Non-blocking execution** - SharpCap remains fully responsive
4. **Stop button available** - Cancel recording safely if needed
5. Automatically restores all camera settings after recording completes
6. Waits for camera stabilization (2× exposure time)
7. Restores display stretch levels to match your pre-test view

**Why use it:**
- Verify focus and framing before the event
- SharpCap UI remains responsive during test (can adjust settings if needed)
- Test your camera setup without manual adjustment afterwards
- Ensure recording settings work correctly
- Check field of view and target visibility
- Confirm no issues with the sequence template

**Settings Preserved:**
- Camera binning
- Exposure time
- Gain value
- Resolution/ROI
- Display black/mid/white levels (stretch)

**Template Required:**
The test recording feature requires a template file named "SharpCap Test Recording Template.txt" in your configured templates folder. This template should define a brief recording sequence (typically 10-30 seconds) suitable for testing purposes.

### Run Sequences (Direct Execution)

Execute multiple sequences directly from Occultation Manager without manually loading them in SharpCap Sequencer:

**What it does:**
1. Select multiple events and check their checkboxes
2. Click **Run Sequences** button (toolbar) or **Sequences → Run Selected Sequences** (menu)
3. Saves current camera settings automatically
4. Executes each sequence in time order (earliest first)
5. **Non-blocking execution** - SharpCap remains fully responsive
6. **Stop button available** - Cancel safely with confirmation dialog
7. Automatically restores all camera settings after completion
8. Shows progress status ("Running sequence 1/3: Event Name")

**Benefits:**
- No need to manually load .scs files in SharpCap Sequencer
- Automatic multi-sequence sessions for entire night's observations
- SharpCap UI remains responsive (can monitor, adjust, or cancel)
- Safe cancellation at any time with automatic cleanup
- All sequence operations work correctly (display stretch, notifications, camera controls)
- Camera settings preserved and restored automatically

**Stop Button:**
- Located in Observation Preparation panel
- Only enabled when sequences are running
- Click to request stop with confirmation dialog
- Sequences complete current step before stopping
- Camera settings automatically restored after stop
- Works for both Test Recording and Run Sequences

**Technical Details:**
- Uses SharpCap's `RunAsync()` API for non-blocking execution
- All UI operations marshaled to correct thread (STA requirement)

### Sequence Execution Methods - Which To Use?

There are two ways to execute your generated sequences:

**METHOD 1: SharpCap Sequencer (RECOMMENDED - Safest)**
- Load your .scs file directly in SharpCap's Sequencer
- Click Play to start the sequence
- SharpCap manages all timing and execution
- **Simplest and most reliable method**
- **Recommended for unattended operation**
- **Recommended for remote operation**
- Fewest points of failure

**METHOD 2: Occultation Manager Run Sequences (Alternative)**
- Note: It is safer to run sequences directly from SharpCap.
- Note: Combined Sequences can only be run directly from SharpCap.
- Select events and click Run Sequences button
- Manager executes sequences via RunAsync API
- Provides Stop button control during execution
- More complex with additional monitoring layer
- **Suitable for attended multi-event sessions**
- **Not recommended for unattended operation**
- Additional complexity may reduce reliability

**Recommendation:** For the most reliable operation, especially for unattended or 
remote recording, load your sequences directly in SharpCap Sequencer and use 
Method 1. Method 2 is useful for attended sessions where you want Stop button 
control, but adds complexity that may not be desirable for critical observations.

### Countdown and Notification Options

⚠️ **CRITICAL TIMING SAFETY INFORMATION**

**WAIT UNTIL LOCALTIME PROBLEMS:**

SharpCap's built-in `WAIT UNTIL LOCALTIME` and `WAIT UNTIL AFTER LOCALTIME` 
commands have serious limitations that can cause you to **MISS EVENTS**:

1. **NO DATE AWARENESS**: SharpCap only knows the TIME, not the DATE
   - If started after midnight, it may wait 24 hours until "tomorrow"
   - Events after local midnight will be missed or start immediately

2. **NEXT-DAY EVENT FAILURE:**
   - Event at 01:00:00 (after midnight) started at 23:00:00 (before midnight)
   - Sequencer sees 01:00:00 < 23:00:00 and waits until NEXT day's 01:00:00
   - **You MISS the event entirely!**

3. **DAYLIGHT SAVING TIME:**
   - Clock changes can cause unexpected behavior
   - 1-hour timing errors during DST transitions

**RECOMMENDED APPROACH - USE UTC WITH PYTHON COUNTDOWN:**

For reliable, safe timing use UTC-based countdown functions. These handle all edge 
cases correctly including events after midnight, late starts, next-day events, and 
daylight saving time.

**THREE COUNTDOWN OPTIONS:**

**Option 1: Notification Without Countdown (Simplest, Most Risky)**

Uses only SharpCap native commands:
```
SHOW NOTIFICATION "Waiting until {goto_time}_local" COLOUR Green DURATION 10000
WAIT UNTIL LOCALTIME "{goto_time_local}"
CLEAR NOTIFICATION
```

✓ Simple, no Python code  
✗ Subject to ALL local time problems  
✗ Can miss events  
⚠️ **NOT RECOMMENDED** for critical observations

**Option 2: UTC Notification Countdown (RECOMMENDED)**

Auto-updating notification with formatted countdown in Days HH:MM:SS format.

**Setup** - Add these at the start of your sequence:
```
RUN PYTHON CODE "import datetime as dt; import time; import clr; clr.AddReference('System'); from System import Action"
RUN PYTHON CODE "def format_time(seconds): days = seconds // 86400; hours = (seconds % 86400) // 3600; mins = (seconds % 3600) // 60; secs = seconds % 60; return (str(days) + ' Days ' if days > 0 else '') + str(hours).zfill(2) + ':' + str(mins).zfill(2) + ':' + str(secs).zfill(2)"
RUN PYTHON CODE "def countdown_utc(date_string, message, target_dt=None, is_first=True): target_dt = dt.datetime.strptime(date_string,'%Y-%m-%dT%H:%M:%S') if is_first else target_dt; remaining = int((target_dt - dt.datetime.utcnow()).total_seconds()); status = 0; formatted = format_time(remaining); alert = ' ⚠️ LESS THAN 5 MIN!' if remaining < 300 and remaining >= 60 else (' 🔴 LESS THAN 1 MIN!' if remaining < 60 else ''); (SharpCap.ShowNotification(message + ': ' + formatted + ' remaining' + alert, status, False, 2, None, None, None) if remaining > 0 else None); (time.sleep(1) if remaining > 0 and SharpCap.Sequencer.IsRunning else None); (countdown_utc(date_string, message, target_dt, False) if remaining > 1 and SharpCap.Sequencer.IsRunning else None)"
```

**Usage** - Then use in your sequence with UTC time tags:
```
RUN PYTHON CODE "countdown_utc('{goto_time}', 'Waiting for GOTO')"
```

**Advantages:**
✓ UTC-based - no timezone/midnight issues  
✓ Accurate countdown display  
✓ Adaptive update rate: 1-minute when >5 min, 1-second when ≤5 min  
✓ Safe for 24+ hour countdowns  
✓ Color-coded warnings (<5 min, <1 min)  
✓ Stoppable (may take up to 60s to respond when >5 min remaining)  
✓ **RECOMMENDED**

**Option 3: UTC Dialog Countdown (Most Complex)**

Windows dialog with large countdown display and stop button.

**Setup** - Add these at the start of your sequence:
```
RUN PYTHON CODE "import datetime as dt; import time; import clr; clr.AddReference('System.Windows.Forms'); clr.AddReference('System.Drawing'); from System.Windows.Forms import Form, Label, Button, FormStartPosition, DockStyle, FormBorderStyle, Application; from System.Drawing import Size, Font, FontStyle, ContentAlignment"
RUN PYTHON CODE "def format_time(seconds): days = seconds // 86400; hours = (seconds % 86400) // 3600; mins = (seconds % 3600) // 60; secs = seconds % 60; return (str(days) + ' Days ' if days > 0 else '') + str(hours).zfill(2) + ':' + str(mins).zfill(2) + ':' + str(secs).zfill(2)"
RUN PYTHON CODE "def update_countdown(form, label, target_dt, message, stopped): remaining = int((target_dt - dt.datetime.utcnow()).total_seconds()); (label.__setattr__('Text', message + '\\n\\n' + format_time(remaining) + '\\nremaining') if remaining > 0 else None); Application.DoEvents(); (time.sleep(0.1) if remaining > 0 and not stopped[0] and SharpCap.Sequencer.IsRunning else None); (update_countdown(form, label, target_dt, message, stopped) if remaining > 0 and not stopped[0] and SharpCap.Sequencer.IsRunning else form.Close())"
RUN PYTHON CODE "def countdown_dialog(date_string, message): target_dt = dt.datetime.strptime(date_string,'%Y-%m-%dT%H:%M:%S'); form = Form(); form.Text = message; form.Size = Size(400, 150); form.FormBorderStyle = FormBorderStyle.FixedDialog; form.StartPosition = FormStartPosition.CenterScreen; form.MaximizeBox = False; form.MinimizeBox = False; form.TopMost = True; label = Label(); label.Font = Font('Arial', 16, FontStyle.Bold); label.Dock = DockStyle.Fill; label.TextAlign = ContentAlignment.MiddleCenter; button = Button(); button.Text = 'Stop Countdown'; button.Dock = DockStyle.Bottom; button.Height = 40; stopped = [False]; button.Click += lambda s, e: (stopped.__setitem__(0, True), form.Close()); form.Controls.Add(label); form.Controls.Add(button); form.Show(); update_countdown(form, label, target_dt, message, stopped)"
```

**Usage** - Then use in your sequence with UTC time tags:
```
RUN PYTHON CODE "countdown_dialog('{goto_time}', 'Waiting for GOTO')"
```

**Advantages:**
✓ Large visible countdown  
✓ Dedicated stop button  

**Disadvantages:**
✗ Most complex implementation  
✗ Additional failure points (Windows forms)  
✗ Stop button may take up to 60 seconds to respond when >5 min remaining  
⚠️ Use only if you need large visible countdown

**Ready-to-Use Code:**
See `countdown python for sequencer.scs` in the application folder for complete 
code snippets you can copy directly into your sequences.

**ALWAYS TEST countdown functions before using for real observations!**
- Background monitoring thread tracks sequence status
- Proper thread synchronization prevents race conditions
- Comprehensive error handling with automatic cleanup

This provides the best of both worlds: automated multi-sequence execution with full UI control and safe cancellation.

## Report Generation (Under Development - Not Approved)

⚠️ **CRITICAL WARNING**: Report generation is still under development and **has NOT been approved** by the NA, TT, or SODIS reporting coordinators. Only TANGRA and AOTA outputs are currently supported. All generated reports must be carefully verified before submission to any reporting organization. Use with extreme caution.

Reports are generated using a streamlined single-dialog workflow that combines:
- Report format selection (North America / Trans-Tasman / SODIS)
- Telescope and camera selection
- Observation type (Positive / Negative / Unsure)
- Observing conditions (clouds, stability, other notes)
- AOTA file selection (.aota.xml OR .txt for D/R times and SNR)
- Tangra CSV file selection (light curve with timing data)

**Technical Implementation**:
- Uses Openize.OpenXML-SDK for direct Excel cell access via IronPython
- Preserves Excel data validation, formulas, and formatting
- Automatic Occult 4 XML export with conditions mapped to standard codes
- Templates stored directly in python/ folder (no placeholder files needed)

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
- Camera acquisition delay in seconds — 4 decimal places (from measurement parameters table)

**GPS Flash Timing Analysis Status**:
⚠️ **Not Yet Integrated**: GPS flash timing analysis functions are available in the `gps-timing-analysis` toolkit but are not yet integrated into Occultation Manager. These advanced functions (GPS 1PPS flash detection, timestamp offset calculation, rolling shutter characterization) are currently available as standalone tools for expert users who can write custom Python code. Plans exist to integrate these capabilities into the report generation workflow in a future release.

### Workflow Improvements
- **Settings Persistence**: Remembers last report type and folder location
- **Auto-Selection**: Automatically selects first available AOTA and Tangra files; AOTA Report events are listed first in the D/R event combo
- **Smart Validation**: AOTA file (XML or Report) required for Positive/Unsure observations, optional for Negative
- **Flexible Timing**: Accepts either AOTA.xml OR AOTA_Report.txt (or both for validation)
- **Time Verification**: Compares D/R times when both AOTA sources provided
- **Multi-Event Support**: Select specific event from AOTA Reports with multiple events
- **One-Click Generation**: Single dialog replaces 5 separate dialogs
- **NTP Uncertainty Note**: When the NTP uncertainty checkbox is ticked, the note is written to the Additional Comments section of the TT report (cell D44), separate from Other Conditions

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
