import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Point, Size, Font, FontStyle
from System.Windows.Forms import Label, TextBox, ScrollBars, DialogResult
from System.Windows.Forms import TreeView, TreeNode, FormStartPosition, FormBorderStyle, SplitContainer, DockStyle, FixedPanel, Button, Form  # Added Form and TreeNode import
from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon
from theme import apply_theme_to_control

def _detect_scale_factor():
    """Detect current display DPI and return scale factor.
    
    Returns:
        float: Scale factor (1.0 for 100%, 1.25 for 125%, 1.5 for 150%)
    """
    try:
        from System.Drawing import Graphics, Bitmap
        # Use a temporary form to get DPI
        temp_form = Form()
        try:
            temp_form.CreateControl()
            g = Graphics.FromHwnd(temp_form.Handle)
            try:
                dpi = float(g.DpiX)
            finally:
                g.Dispose()
        finally:
            temp_form.Dispose()
        
        return dpi / 96.0
    except Exception:
        return 1.0

class HelpDialog(Form):
    """Interactive help dialog for the Occultation Manager with DPI scaling"""
    
    def __init__(self, theme_manager, initial_topic=None):
        Form.__init__(self)
        self.theme_manager = theme_manager
        self.initial_topic = initial_topic
        self._sf = _detect_scale_factor()
        self.setup_ui()
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup the help dialog UI with DPI scaling"""
        sf = self._sf
        
        self.Text = "Occultation Manager - Help & User Guide"
        self.Size = Size(int(900 * sf), int(700 * sf))
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.MaximizeBox = True
        self.MinimizeBox = True
        
        # Create main split container
        main_split = SplitContainer()
        main_split.Dock = DockStyle.Fill
        main_split.FixedPanel = FixedPanel.Panel1
        self.Controls.Add(main_split)
        # Set AFTER Controls.Add so layout is realised before the value is applied
        main_split.SplitterDistance = int(185 * sf)  # Panel1 = topics tree width
        
        # Left panel - Help topics tree
        self.setup_help_topics(main_split.Panel1)
        
        # Right panel - Help content
        self.setup_help_content(main_split.Panel2)
        
        # Load initial content (select appropriate topic)
        if self.initial_topic == "template_modification":
            self.select_topic_by_tag("template_modification")
        else:
            self.select_topic_by_tag("quickstart")
        
        # Close button
        btn_close = Button()
        btn_close.Text = "Close"
        btn_close.DialogResult = DialogResult.OK
        btn_close.Dock = DockStyle.Bottom
        btn_close.Height = int(30 * sf)
        self.Controls.Add(btn_close)
        
        self.AcceptButton = btn_close
    
    def setup_help_topics(self, panel):
        """Setup the help topics tree view with DPI scaling"""
        sf = self._sf
        
        self.tree_topics = TreeView()
        self.tree_topics.Dock = DockStyle.Fill
        self.tree_topics.Font = Font("Segoe UI", 10 * sf)
        self.tree_topics.AfterSelect += self.topic_selected
        panel.Controls.Add(self.tree_topics)
        
        lbl_topics = Label()
        lbl_topics.Text = "Help Topics:"
        lbl_topics.Dock = DockStyle.Top
        lbl_topics.Height = int(25 * sf)
        lbl_topics.Font = Font("Segoe UI", 9 * sf, FontStyle.Bold)
        panel.Controls.Add(lbl_topics)
        
        # Apply theme colors to TreeView
        theme_colors = self.theme_manager.get_current_theme()
        self.tree_topics.BackColor = theme_colors['textbox_background']
        self.tree_topics.ForeColor = theme_colors['text_foreground']
        
        # Populate help topics
        self.populate_help_topics()
    
    def setup_help_content(self, panel):
        """Setup the help content display with DPI scaling"""
        sf = self._sf
        
        self.txt_help_content = TextBox()
        self.txt_help_content.Multiline = True
        self.txt_help_content.ReadOnly = True
        self.txt_help_content.ScrollBars = ScrollBars.Vertical
        self.txt_help_content.WordWrap = True
        self.txt_help_content.Font = Font("Segoe UI", 10 * sf)
        self.txt_help_content.Dock = DockStyle.Fill
        panel.Controls.Add(self.txt_help_content)

    def add_node_with_tag(self,parent, text, tag):
            """Helper to add a node with a tag"""
            node = TreeNode(text)
            node.Tag = tag
            parent.Nodes.Add(node)
            return node    
    
    def populate_help_topics(self):
        """Populate the help topics tree"""
        def add_node_with_tag(self,parent, text, tag):
            node = TreeNode(text)
            node.Tag = tag
            parent.Nodes.Add(node)
            return node
        
        # Quick Start
        quickstart_node = TreeNode("Quick Start")
        quickstart_node.Tag = "quickstart"
        self.tree_topics.Nodes.Add(quickstart_node)
        
        # Event Recording Workflow
        workflow_node = TreeNode("Event Recording Workflow")
        workflow_node.Tag = "workflow"
        self.tree_topics.Nodes.Add(workflow_node)
        
        # Template Modification
        template_node = TreeNode("Template Modification")
        template_node.Tag = "template_modification"
        self.tree_topics.Nodes.Add(template_node)
        
        # Timing & Calibration Tools
        timing_node = TreeNode("Timing & Calibration Tools")
        timing_node.Tag = "timing_tools"
        self.tree_topics.Nodes.Add(timing_node)

        # Report Generation
        report_gen_node = TreeNode("Report Generation")
        report_gen_node.Tag = "report_generation"
        self.tree_topics.Nodes.Add(report_gen_node)

        # Equipment Setup
        equipment_node = TreeNode("Equipment Setup")
        equipment_node.Tag = "equipment_setup"
        self.tree_topics.Nodes.Add(equipment_node)
        
        # Expand top-level nodes
        for node in self.tree_topics.Nodes:
            node.Expand()
        
        # Store reference for initial topic selection
        self.quickstart_node = quickstart_node
        self.template_node = template_node
    
    def topic_selected(self, sender, e):
        """Handle topic selection"""
        if e.Node and e.Node.Tag and e.Node.Tag != '':
            self.load_help_content(e.Node.Tag)
    
    def load_help_content(self, topic):
        """Load help content for the specified topic"""
        content = self.get_help_content(topic)
        self.txt_help_content.Text = content
        # Scroll to top
        self.txt_help_content.SelectionStart = 0
        self.txt_help_content.ScrollToCaret()
    
    def load_overview_content(self):
        """Load the quick start content by default"""
        self.load_help_content("quickstart")
    
    def select_topic_by_tag(self, tag):
        """Select and display a topic by its tag"""
        for node in self.tree_topics.Nodes:
            if node.Tag == tag:
                self.tree_topics.SelectedNode = node
                self.load_help_content(tag)
                return
        # Fallback to quickstart if not found
        self.tree_topics.SelectedNode = self.quickstart_node
        self.load_help_content("quickstart")
    
    def get_help_content(self, topic):
        """Get help content for a specific topic"""
        content_map = {
            "quickstart": self.get_quickstart_content().replace('\n','\r\n'),
            "workflow": self.get_workflow_content().replace('\n','\r\n'),
            "template_modification": self.get_template_modification_content().replace('\n','\r\n'),
            "timing_tools": self.get_timing_tools_content().replace('\n','\r\n'),
            "report_generation": self.get_report_generation_content().replace('\n','\r\n'),
            "equipment_setup": self.get_equipment_setup_content().replace('\n','\r\n')
        }
        
        return content_map.get(topic, "Help content not found for this topic.")
    
    
    def get_quickstart_content(self):
        return """QUICK START GUIDE
==================

Installation and first-time setup for Occultation Manager.

INSTALLATION
------------
1. Download occultation-manager-v0.2.0-beta.9.zip from GitHub
2. Extract to a folder with read/write access
   ⚠️ AVOID Program Files - Windows may restrict write access
   ✅ RECOMMENDED: Documents\\SharpCap
3. Start SharpCap
4. Go to File → SharpCap Settings → Startup Scripts
5. Browse to the extracted app folder and select 'app/main.py'
6. Click OK and restart SharpCap

A new "Occultations" button appears in SharpCap's main toolbar.

FIRST STARTUP - AUTOMATIC SETUP
--------------------------------
When you first launch Occultation Manager, it automatically:

• Detects your installation directory
• Creates all required data folders automatically (see Folder Structure below)
• Uses fixed install-relative paths (no path setup required)
• Seeds missing templates from resources/templates_master/sequencer/
• Saves configuration to data/config/occultation_config.json

INITIAL CONFIGURATION
---------------------
Click the Occultations button to open Occultation Manager.

Go to Tools → Configuration and set up:

CREDENTIALS TAB (Required):
• OWC Email: Your Occult Watcher Cloud login
• OWC Password: Your OWC password
• API Key: Get from https://cloud.occultwatcher.net/user-profile
  Go to User Profile → Permissions & Settings
• Days to Retain Events: How long to keep old events (default: 14)
• Includes "How Download from OWC Works" guidance panel

FILE PATHS TAB:
• Paths are fixed by installation layout and are not user-configurable
• Use buttons to open data folders in Windows Explorer (see Folder Structure below)

USER SETTINGS TAB:
• Base Duration: Extra recording time (default: 60s)
• GOTO Lead Time: Slew start before recording (default: 240s)
• Mag for 40ms exp: Reference magnitude (default: 12.0)
• Default Gain: Camera gain for new events (default: 450)
• Sync Mount with GOTO: Syncs mount to plate-solved position after each GOTO (default: off)
  ⚠ Only enable if you normally sync your mount manually with every GOTO
  Do NOT use with permanently aligned or precision pointing-model mounts
• Display UTC in Grid: Show event times in UTC instead of local time (default: off)
• Output Debug Logs: Enable verbose OWC download/parsing log files (default: off)
  Click "Open Debug Logs Folder" to access owc_raw_download.log and owc_data_debug.log

Click the 'Explain' button next to any setting for detailed help.

OBSERVER/TELESCOPE TAB:
• Fill in your personal details that will auto-fill into generated reports:
  - Name, Email, Address, City, State, Country, Phone, Fax
• Station latitude and longitude come from OWC event data (not set here)
• Click "Tools → Manage Telescopes" and "Tools → Manage Cameras" to set up
  your equipment profiles — see the "Equipment Setup" help topic for details

Click Save to apply changes.

FIRST USE
---------
1. Click Download to retrieve your assigned events from OWC
2. Review events in the grid (times, magnitudes, exposures)
3. Use Station Filter to show only your observing location
4. Select an event and explore the Observation Preparation panel
5. Check event checkboxes and click Create Sequences
6. Choose a template (recommend: SharpCap Sequence UTC Template)
7. Find generated .scs files in data/sequences/

GETTING STARTED
---------------
• Download: Syncs with OWC to get your station assignments
• Generate Dummy Events: Create realistic test events for practice
  - Configure number, timing, location, and spacing
  - Events visible from your observatory
  - Delete when done using Quick Filters Delete button
• Station Filter: Shows events for specific location
• Event Grid: All event information with sortable columns
• Quick Filters: Show Today/Future/All events, toggle all checkboxes On/Off, Delete selected
• Observation Preparation: Test GOTO, plate solve, camera setup
• Create Sequences: Generate customizable SharpCap .scs files
• Night Mode: Red theme for observing sessions

See "Event Recording Workflow" for detailed workflow steps.
See "Template Modification" for customizing sequences.

FOLDER STRUCTURE
----------------
After extraction and first run, the install folder contains:

occultation-manager/
├── app/
│   ├── main.py                      # SharpCap startup script
│   ├── *.py
│   └── lib/
├── resources/
│   └── templates_master/
│       ├── sequencer/
│       └── reports/
└── data/                            # Auto-created on first launch
    ├── config/occultation_config.json
    ├── events/occultations.json
    ├── templates/
    ├── sequences/
    └── reports/

The data/ folders are created automatically — no manual setup is needed.
Use Tools → Configuration → File Paths to open any folder in Explorer."""

    def get_workflow_content(self):
        return """EVENT RECORDING WORKFLOW
========================

Complete workflow from downloading events to recording observations.

OVERVIEW
--------
The Occultation Manager streamlines event management through SharpCap 
sequence generation. Sequences give you complete control over automation 
while handling timing and coordination automatically.

STEP 1: DOWNLOAD EVENTS
------------------------
Click Download button (or File → Download)
• Retrieves assigned events from Occult Watcher Cloud
• Calculates optimal exposure times based on star magnitudes
• Calculates recording durations with uncertainty buffers
• Events appear in the grid with all calculated parameters

STEP 2: FILTER AND REVIEW
--------------------------
• Use Station Filter to show your observing location
• Click Quick Filters: Today (next 24h), Future (all upcoming), All
• Click column headers to sort events
• Double-click rows to see Event Details
• Review: event time, star magnitude, exposure, recording duration

STEP 3: CUSTOMIZE SETTINGS (OPTIONAL)
--------------------------------------
• Double-click Exposure, Gain, or Recording Time columns to customize
• Override calculated values for specific events
• Set custom exposure for camera sensitivity
• Adjust gain for brightness conditions
• Modify recording duration for unusual uncertainties
• Custom values marked with * in grid

STEP 4: PREPARE FOR OBSERVATION (OPTIONAL - MANUAL TESTING)
------------------------------------------------------------
Use Observation Preparation panel for manual setup and testing:

• Load Event: Select event from grid
• Setup: Configure SharpCap camera (sets exposure, copies coordinates)
• GOTO: Slew telescope to target
• Plate Solve: Verify pointing and mark target star

This allows you to:
• Test equipment before the event
• Verify mount positioning accuracy
• Check field of view and framing
• Make sure everything works correctly

OR use Test Recording button:
• Makes short test recording (10-30s)
• Automatically saves and restores all camera settings
• Verifies focus, framing, and recording setup
• Safe testing without disrupting your configuration

STEP 5: GENERATE SEQUENCES (PREFERRED METHOD)
----------------------------------------------
• Check event checkboxes for events you want to record
• Click Create Sequences button
• Select template from dialog:
  
  ⭐ RECOMMENDED: SharpCap Sequence UTC Template
     - Safest template with proper countdown system
     - Handles late starts and next-day events
     - Can be safely stopped and restarted
     - Full automation: GOTO, plate solve, recording, safe finish
  
  Other templates:
  - Local Time templates (simpler but has midnight issues)
  - Minimal template (basic automation, assumes manual setup)
  - Just Record template (recording only, no GOTO/plate solve)

• .scs files created in data/sequences/
• One file per event: YYYYMMDD [Event Name].scs

STEP 6A: AUTOMATED RECORDING (RECOMMENDED)
-------------------------------------------
Load sequences in SharpCap:
• Open Sequencer in SharpCap
• Load .scs file(s) for your events
• Click Play to start sequence
• Sequence waits for proper time, then automates:
  - Countdown to GOTO time
  - GOTO and plate solve
  - Camera configuration
  - Countdown to recording start
  - Recording at precise time
  - Safe finish (park mount, etc.)

UTC Template benefits:
• Proper UTC-based countdown (no timezone issues)
• Safe to start early (waits until correct time)
• Safe to start late (records immediately if past start time)
• User can stop countdown and restart if needed
• Handles events after midnight correctly
• Suitable for multi-night unattended operation

STEP 6B: MANUAL RECORDING (ALTERNATIVE)
----------------------------------------
If you prefer complete manual control:
• Use Observation Preparation panel to set up manually
• Load Event: Select event and load
• Setup: Configure camera
• GOTO: Position telescope when ready
• Plate Solve: Verify pointing
• Start Recording manually in SharpCap at event time
• Monitor and control everything yourself

Or use Test Recording for quick tests:
• Verifies your setup without disrupting settings
• Good for testing before manual recording
• Non-blocking: SharpCap remains responsive during recording
• Stop button available to cancel if needed

STEP 6C: RUN SEQUENCES DIRECTLY (NEW ASYNC METHOD)
---------------------------------------------------
Run multiple sequences directly from Occultation Manager:

• Select multiple events and check their checkboxes
• Click Run Sequences button (or Sequences → Run Sequences)
• Sequences execute automatically in time order
• Each sequence runs to completion before starting the next
• SharpCap remains responsive throughout execution
• Stop button enables safe cancellation at any time
• Camera settings automatically saved and restored

Run Sequences benefits:
• Non-blocking operation - SharpCap UI remains responsive
• Can stop execution safely with confirmation dialog
• Automatic camera settings preservation and restoration
• Status updates show progress through sequence list
• Suitable for multi-event sessions without manual sequence loading
• All sequence steps work correctly (display stretch, notifications, etc.)

Stop Button:
• Appears in Observation Preparation panel
• Only enabled when sequence is running
• Click to safely stop current sequence
• Confirmation dialog prevents accidental stops
• Automatically restores all camera settings after stop
• Can be used with both Test Recording and Run Sequences

STEP 7: ANALYZE RESULTS
------------------------
After recording:
• Process video in Tangra or similar
• Generate light curve CSV
• Use AOTA for timing analysis (optional)

STEP 8: GENERATE REPORT (UNDER DEVELOPMENT - NOT APPROVED)
----------------------------------------------------------
⚠ CRITICAL WARNING: Report generation is still under development and 
has NOT been approved by reporting coordinators. Only TANGRA and AOTA
outputs are currently supported. All generated reports must be carefully
verified before submission.

See the dedicated "Report Generation" help topic for full details of
the Generate Report form, Timestamp Check tools, and Inspect Timestamps
chart viewer.

WORKFLOW SUMMARY
----------------
1. Download → Filter → Customize (optional)
2. EITHER:
   • Generate Sequences → Load in SharpCap → Automated recording
   OR
   • Manual Preparation → Manual recording
3. Analyze → Report (optional, verify data)

KEY POINTS
----------
• Sequences give you full control through customizable templates
• UTC Template recommended for safety and reliability
• Test Recording button for safe testing
• Observation Preparation for manual control
• Report generation is under development and NOT APPROVED - verify all data carefully
• Tangra light curve analysis is integrated; see Tools menu for camera timing and calibration tools
• Templates can be customized to match your equipment
• Automate as much or as little as you need"""

    def get_template_modification_content(self):
        return """TEMPLATE MODIFICATION
======================

Customize SharpCap sequence templates to match your equipment and workflow.

OVERVIEW
--------
Templates are text files containing SharpCap sequencer commands with 
placeholder variables that get replaced with event-specific data when 
sequences are generated.

FILE LOCATIONS
--------------
Understanding where files are read from and saved to:

TEMPLATES (read from):
• Location: data/templates/ (fixed path)
• Files: Any .txt file with "template" in the filename
• Examples: "SharpCap Sequence UTC template.txt", "MyCustom template.txt"
• The application scans data/templates/ for these files when you click 
  Create Sequences

SEQUENCES (saved to):
• Location: data/sequences/ (fixed path)
• Files: .scs files generated from templates
• Naming: YYYYMMDD [Event Name].scs
• Examples: "20260125 433 Eros - Station ABC.scs"

REPORTS (saved to):
• Location: data/reports/ (fixed path)
• Files: .xlsx Excel report files
• Naming: YYYYMMDD_number_name_catalog_star±Observer_Station.xlsx
• Examples: "20251107_778_Theobalda_Gaia_DR3_12345+Smith_Observatory.xlsx"

CREATING CUSTOM TEMPLATES
--------------------------
1. Create a new .txt file in data/templates/
2. Include "template" in the filename (e.g., "MyCustom template.txt")
3. Write SharpCap sequencer commands
4. Insert placeholder variables in curly braces: {variable_name}
5. Save the file
6. Template appears in Template Selection dialog

PLACEHOLDER SYNTAX
------------------
Use curly braces {} to insert event data into your template:

{placeholder_name}

Example:
  SET EXPOSURE TO {exposure}
  
becomes:
  SET EXPOSURE TO 0.120

AVAILABLE PLACEHOLDERS
----------------------

EVENT IDENTIFICATION:
{object_name} | Asteroid name | "433 Eros"
{name} | Full event name including station | "433 Eros - Station ABC"
{asteroid_name} | Same as object_name | "433 Eros"
{station_name} | Observing station name | "Station ABC"

TIMING (UTC):
{event_time} | Event center time UTC (ISO format) | "2026-01-25T04:32:15"
{start_time} | Recording start time UTC (ISO format) | "2026-01-25T04:30:45"
{goto_time} | GOTO slew start time UTC (ISO format) | "2026-01-25T04:26:45"
{pre_goto} | Format for UTC countdown functions (YYYYMMDD HH:MM:SS) | "20260125 04:20:00"

TIMING (LOCAL TIME):
{event_time_local} | Event center time local (HH:MM:SS only) | "20:32:15"
{start_time_local} | Recording start time local (HH:MM:SS only) | "20:30:45"
{goto_time_local} | GOTO start time local (HH:MM:SS only) | "20:26:45"
{pre_goto_time_local} | Pre-GOTO time local (HH:MM:SS only) | "20:20:00"

⚠ WARNING: Local time placeholders are TIME ONLY (no date component):
  - Do NOT include date in the output (only HH:MM:SS)
  - Times after local midnight will NOT work properly with WAIT UNTIL AFTER LOCALTIME
  - Next-day events will fail (time "01:00:00" looks earlier than "23:00:00")
  - Daylight saving time changes can cause incorrect timing
  - WAIT UNTIL AFTER LOCALTIME compares time only, not date+time
  
  STRONGLY PREFER UTC timing with {pre_goto} and custom countdown functions.
  UTC-based sequences handle all edge cases correctly.

COORDINATES:
{ra} | Right Ascension in decimal degrees | "47.235689"
{dec} | Declination in decimal degrees | "+12.456789"

CAMERA SETTINGS:
{exposure} | Camera exposure time in seconds (3 decimals) | "0.120"
{gain} | Camera gain value (integer, minimum 0, no upper limit) | "450"
{recording_duration} | Total recording duration in seconds (integer) | "180"

Notes: Exposure, gain, and recording_duration use calculated values or 
custom overrides from Edit Settings dialog.

MAGNITUDE INFORMATION:
{star_mag} | Target star magnitude (1 decimal) | "11.2"
{comb_mag} | Combined star+asteroid magnitude (1 decimal) | "11.8"
{mag_drop} | Magnitude change during occultation (1 decimal) | "0.6"

EVENT PARAMETERS:
{time_error} | Event timing uncertainty in seconds (1 decimal) | "3.5"

COUNTDOWN AND NOTIFICATION OPTIONS:
------------------------------------
⚠ CRITICAL TIMING SAFETY INFORMATION

WAIT UNTIL LOCALTIME PROBLEMS:
SharpCap's built-in WAIT UNTIL LOCALTIME and WAIT UNTIL AFTER LOCALTIME 
commands have serious limitations that can cause you to MISS EVENTS:

1. NO DATE AWARENESS: SharpCap only knows the TIME, not the DATE
   - If started after midnight, it may wait 24 hours until "tomorrow"
   - Events after local midnight will be missed or start immediately

2. NEXT-DAY EVENT FAILURE:
   - Event at 01:00:00 (after midnight) started at 23:00:00 (before midnight)
   - Sequencer sees 01:00:00 < 23:00:00 and waits until NEXT day's 01:00:00
   - You MISS the event entirely!

3. DAYLIGHT SAVING TIME:
   - Clock changes can cause unexpected behavior
   - 1-hour timing errors during DST transitions

RECOMMENDED APPROACH - USE UTC WITH PYTHON COUNTDOWN:
For reliable, safe timing use UTC-based countdown functions (see below).
These handle all edge cases correctly including:
• Events after midnight ✓
• Late starts ✓
• Next-day events ✓
• Daylight saving time ✓

SAFEST OPERATION METHOD:
The SAFEST way to run sequences is directly through SharpCap's Sequencer:
• Load your .scs file in SharpCap Sequencer
• Click Play to start the sequence
• SharpCap manages all timing and execution
• Simplest and most reliable method
• Recommended for unattended/remote operation

ALTERNATIVE - OCCULTATION-MANAGER EXECUTION:
You can also run sequences from Occultation Manager (Run Sequences button):
Note: It is safer to run sequences directly from SharpCap.
Note: Combined Sequences can only be run directly from SharpCap.
• More complex process with additional monitoring
• Provides Stop button control during execution
• Useful for attended sessions with multiple events
• Less suitable for unattended operation
• Additional layer of complexity may reduce reliability

THREE COUNTDOWN OPTIONS:
------------------------

OPTION 1: NOTIFICATION WITHOUT COUNTDOWN (Simplest, Most Risky)
Uses only SharpCap native commands - no Python code:

    SHOW NOTIFICATION "Waiting until {goto_time}_local" COLOUR Green DURATION 10000
    WAIT UNTIL LOCALTIME "{goto_time_local}"
    CLEAR NOTIFICATION

✓ Advantages: Simple, no Python code
✗ Disadvantages: Subject to ALL local time problems above
✗ Can miss events if started late or after midnight
⚠ NOT RECOMMENDED for critical observations

OPTION 2: UTC NOTIFICATION COUNTDOWN (Recommended, Most Reliable)
Displays auto-updating notification with formatted countdown:

First, define the functions (at start of sequence):
    RUN PYTHON CODE "import datetime as dt; import time; import clr; clr.AddReference('System'); from System import Action"
    RUN PYTHON CODE "def format_time(seconds): days = seconds // 86400; hours = (seconds % 86400) // 3600; mins = (seconds % 3600) // 60; secs = seconds % 60; return (str(days) + ' Days ' if days > 0 else '') + str(hours).zfill(2) + ':' + str(mins).zfill(2) + ':' + str(secs).zfill(2)"
    RUN PYTHON CODE "def countdown_utc(date_string, message, target_dt=None, is_first=True): target_dt = dt.datetime.strptime(date_string,'%Y-%m-%dT%H:%M:%S') if is_first else target_dt; remaining = int((target_dt - dt.datetime.utcnow()).total_seconds()); status = 0; formatted = format_time(remaining); alert = ' ⚠️ LESS THAN 5 MIN!' if remaining < 300 and remaining >= 60 else (' 🔴 LESS THAN 1 MIN!' if remaining < 60 else ''); (SharpCap.ShowNotification(message + ': ' + formatted + ' remaining' + alert, status, False, 2, None, None, None) if remaining > 0 else None); (time.sleep(1) if remaining > 0 and SharpCap.Sequencer.IsRunning else None); (countdown_utc(date_string, message, target_dt, False) if remaining > 1 and SharpCap.Sequencer.IsRunning else None)"

Then use in your sequence (use UTC time tags like {goto_time}):
    RUN PYTHON CODE "countdown_utc('{goto_time}', 'Waiting for GOTO')"

✓ Advantages:
  • UTC-based: No timezone or midnight issues
  • Accurate countdown display in Days HH:MM:SS format
  • Adaptive update rate: 1-minute intervals when >5 min remaining, 1-second when ≤5 min
  • Safe for 24+ hour countdowns (no recursion limit issues)
  • Color-coded warnings (<5 min, <1 min)
  • Can be stopped with SharpCap's Stop button
  • Safe if started late (continues immediately if time passed)
  • Handles events across midnight correctly
✓ RECOMMENDED for reliable timing

NOTE: SharpCap Stop button may take up to 60 seconds to respond when more
than 5 minutes from event time (due to update interval).

OPTION 3: UTC DIALOG COUNTDOWN (Most Complex, Potentially Less Reliable)
Shows Windows dialog with countdown and stop button:

First, define the functions (at start of sequence):
    RUN PYTHON CODE "import datetime as dt; import time; import clr; clr.AddReference('System.Windows.Forms'); clr.AddReference('System.Drawing'); from System.Windows.Forms import Form, Label, Button, FormStartPosition, DockStyle, FormBorderStyle, Application; from System.Drawing import Size, Font, FontStyle, ContentAlignment"
    RUN PYTHON CODE "def format_time(seconds): days = seconds // 86400; hours = (seconds % 86400) // 3600; mins = (seconds % 3600) // 60; secs = seconds % 60; return (str(days) + ' Days ' if days > 0 else '') + str(hours).zfill(2) + ':' + str(mins).zfill(2) + ':' + str(secs).zfill(2)"
    RUN PYTHON CODE "def update_countdown(form, label, target_dt, message, stopped): remaining = int((target_dt - dt.datetime.utcnow()).total_seconds()); (label.__setattr__('Text', message + '\\n\\n' + format_time(remaining) + '\\nremaining') if remaining > 0 else None); Application.DoEvents(); (time.sleep(0.1) if remaining > 0 and not stopped[0] and SharpCap.Sequencer.IsRunning else None); (update_countdown(form, label, target_dt, message, stopped) if remaining > 0 and not stopped[0] and SharpCap.Sequencer.IsRunning else form.Close())"
    RUN PYTHON CODE "def countdown_dialog(date_string, message): target_dt = dt.datetime.strptime(date_string,'%Y-%m-%dT%H:%M:%S'); form = Form(); form.Text = message; form.Size = Size(400, 150); form.FormBorderStyle = FormBorderStyle.FixedDialog; form.StartPosition = FormStartPosition.CenterScreen; form.MaximizeBox = False; form.MinimizeBox = False; form.TopMost = True; label = Label(); label.Font = Font('Arial', 16, FontStyle.Bold); label.Dock = DockStyle.Fill; label.TextAlign = ContentAlignment.MiddleCenter; button = Button(); button.Text = 'Stop Countdown'; button.Dock = DockStyle.Bottom; button.Height = 40; stopped = [False]; button.Click += lambda s, e: (stopped.__setitem__(0, True), form.Close()); form.Controls.Add(label); form.Controls.Add(button); form.Show(); update_countdown(form, label, target_dt, message, stopped)"

Then use in your sequence (use UTC time tags like {goto_time}):
    RUN PYTHON CODE "countdown_dialog('{goto_time}', 'Waiting for GOTO')"

✓ Advantages:
  • Large, easy-to-read countdown display
  • Dedicated Stop button in dialog
  • Adaptive update rate: 1-minute intervals when >5 min remaining, 1-second when ≤5 min
  • Safe for 24+ hour countdowns (no recursion limit issues)
  • UTC-based timing
  • Very visible countdown
✗ Disadvantages:
  • Most complex implementation
  • Additional Windows form may cause issues
  • More failure points than notification method
  • Stop button may take up to 60 seconds to respond when >5 min remaining
⚠ Use only if you need the large visible countdown
  • Most complex implementation
  • Additional Windows form may cause issues
  • More failure points than notification method
⚠ Use only if you need the large visible countdown

COUNTDOWN CODE REFERENCE:
See "countdown python for sequencer.scs" in the python folder for
ready-to-copy countdown code snippets and detailed implementation notes.

TESTING COUNTDOWN FUNCTIONS:
CRITICAL: Always test countdown functions before using for real events!
1. Create test sequence with countdown set to 2 minutes in future
2. Run sequence and verify countdown displays correctly
3. Test stop functionality
4. Verify sequence continues after countdown completes
5. Test starting sequence late (after countdown time has passed)

TEMPLATE EXAMPLE
----------------
Here's a simple template showing placeholder usage:

# Occultation sequence for {object_name}
# Event time: {event_time}
# Star magnitude: {star_mag}, Exposure: {exposure}s

SEQUENCE
    # Wait for GOTO time
    WAIT UNTIL LATER THAN LOCALTIME "{goto_time_local}"
    
    # Position telescope
    MOUNT GOTO "{ra} {dec}"
    MOUNT SOLVEANDSYNC
    
    # Configure camera
    TARGETNAME "{object_name}"
    SET EXPOSURE TO {exposure}
    SET GAIN TO {gain}
    
    # Wait and record
    WAIT UNTIL LATER THAN LOCALTIME "{start_time_local}"
    CAPTURE {recording_duration} SECONDS LIVE FRAMES
END SEQUENCE

USING SHARPCAP SEQUENCER TO PROTOTYPE
--------------------------------------
The SharpCap Sequencer tool is excellent for prototyping commands:

1. Open SharpCap Sequencer (Tools → Sequencer)
2. Build your sequence visually using the command palette
3. Test commands with dummy values
4. Use "View Script" to see the generated commands
5. Copy working commands into your template
6. Replace specific values with placeholders

Example workflow:
• Create GOTO command in Sequencer: MOUNT GOTO "12.5 45.3"
• Copy to template
• Replace with placeholders: MOUNT GOTO "{ra} {dec}"

This approach ensures commands are syntactically correct before 
adding placeholder variables.

TESTING TEMPLATES
-----------------
1. Create template with placeholders
2. Select an event and check its checkbox
3. Click Create Sequences
4. Choose your custom template
5. Open generated .scs file in text editor
6. Verify placeholders were replaced with correct values
7. Load .scs file in SharpCap and test execution

TEMPLATE TIPS
-------------
• Start with provided templates and modify them
• Test extensively before relying on templates
• Use comments (#) to document your template
• UTC timing is more reliable than local time
• Include error handling (IGNORE ERRORS, RETRY ERRORS)
• Define safe_finish SUBroutine for error recovery
• Consider what happens if sequence starts late
• Plan for mount parking and safe positions
• Verify all SharpCap commands are current

EXAMPLE TEMPLATES
-----------------
Five templates are provided:

1. SharpCap Sequence UTC Template (RECOMMENDED)
   - Full automation with UTC countdown
   - Safe for any start time and next-day events
   - Error handling and safe finish

2. SharpCap Sequence Local Time Template
   - Full automation with local time
   - Issues with midnight and next-day events

3. SharpCap Minimal Local Time Template
   - Basic automation, assumes manual camera setup
   - Local time limitations apply

4. SharpCap Just Record Template
   - Recording only, no GOTO or plate solve
   - For completely manual setup

5. SharpCap Test Recording Template
   - Immediate short recording for testing
   - Used by Test Recording button

Review these templates to understand different approaches and 
copy techniques for your own templates.

ADVANCED FEATURES
-----------------
• Python code execution (RUN PYTHON CODE)
• Custom countdown functions (UTC timing)
• Conditional logic (IF/END IF)
• Loops (LOOP/END LOOP)
• Subroutines (DEF SUB/END SUB)
• Error handling (IGNORE ERRORS, RETRY ERRORS)

See SharpCap Sequencer documentation for full command reference.

COMMON CUSTOMIZATIONS
---------------------
• Mount parking positions (MOUNT GOTO ALTAZ)
• Camera binning and ROI (SET RESOLUTION, SET BINNING)
• Output format (SET OUTPUT FORMAT)
• Plate solve settings (SET PLATESOLVE/FOCUS SETTINGS)
• Tracking mode (MOUNT TRACKING)
• Notifications (SHOW NOTIFICATION)

Every setup is different - customize templates to match your 
specific equipment, site conditions, and workflow preferences."""

    def get_equipment_setup_content(self):
        return """EQUIPMENT SETUP
================

Configure telescope and camera profiles used for report generation.
Access both managers via the Tools menu.

TELESCOPE MANAGER  (Tools → Manage Telescopes)
-----------------------------------------------
Maintains a list of telescope profiles.  The active telescope is
pre-selected in the Generate Report form.

Fields:
  • Name         — A label you choose (e.g. "C11 Main")
  • Aperture     — Mirror/lens diameter in mm (e.g. 280)
  • Focal Ratio  — f/ ratio (e.g. 10.0 for f/10)
  • Type         — One of:
      SCT including Cass and Mak
      Newtonian
      Refractor
      EdgeHD
      Ritchey-Chretien
      Other

Buttons:
  • Add New      — Clears fields; fill in details and click Add New to save
  • Update       — Saves edits to the currently selected telescope
  • Delete       — Permanently removes the selected telescope
  • Set as Active — Marks the selected telescope as the default for reports
    (★ shown next to active telescope in the list)

CAMERA MANAGER  (Tools → Manage Cameras)
------------------------------------------
Maintains a list of camera configurations including timing and
Occult 4 classification fields.  The active camera is pre-selected
in the Generate Report form.

Report Type MUST be selected first when adding a new camera.
The Report Type controls which timing options appear in the
Timing dropdown and which cameras are shown in the report form
for a given report format (NA/TT/SODIS).

Fields:
  • Report Type      — NA, TT, or SODIS (select this first for a new camera)
  • Name             — A label you choose (e.g. "ASI174MC GPS")
  • Detector         — Camera model; free-editable dropdown with common cameras
  • Timing           — Timing method; options depend on Report Type:
      NA/TT:  "GPS - time inserted", "NTP", "Stopwatch", etc.
      SODIS:  Occult 4 time codes used directly (a-GPS, b-NTP, etc.)
  • Timing Device    — Free text for time-stamping device name (e.g. "QHY 174 GPS")
  • Occult 4 Method  — Detection method code for Occult 4 / IOTA reporting
      Auto-populated from Detector when a known detector is selected
      Can be overridden manually
  • Occult 4 Time    — Timing method code for Occult 4 / IOTA reporting
      Auto-populated from Timing when a known timing method is selected
      Can be overridden manually
  • Other Detector Info — Free text for additional notes about the camera

Occult 4 method codes:
  a - Analogue & digital video
  b - Digital SLR-camera video
  c - Photometer
  d - Sequential images
  e - Drift scan
  f - Visual
  g - Other

Occult 4 time codes:
  a - GPS
  b - NTP
  c - Telephone (fixed or mobile)
  d - Radio time signal
  e - Internal clock of recorder
  f - Stopwatch
  g - Other

Buttons:
  • Add New             — Clears fields; select Report Type first, fill in
                          details, then click Add New to save
  • Update              — Saves edits to the currently selected camera
  • Delete              — Permanently removes the selected camera
  • Set as Active       — Marks the selected camera as the default for reports
    (★ shown next to active camera in the list)
  • Calibrations...     — Shows all saved line-delay calibration runs for this
                          camera; select a run to view its parameters
  • Run New Calibration — Launches the Camera Delay Calibration tool to record
                          a new calibration run for this camera
    (See "Timing & Calibration Tools" for the full calibration workflow)

WORKFLOW — FIRST TIME SETUP
-----------------------------
1. Open Tools → Configuration → Observer/Telescope tab
   Fill in your Name, Email, and postal address for report auto-fill

2. Open Tools → Manage Telescopes
   Click Add New, fill in Name, Aperture, Focal Ratio, and Type
   Click Add New to save, then Set as Active

3. Open Tools → Manage Cameras
   Select Report Type (NA, TT, or SODIS) for your reporting organisation
   Fill in Name, Detector, Timing, and Timing Device
   Occult 4 Method and Occult 4 Time are auto-populated — verify them
   Click Add New to save, then Set as Active

4. These profiles are now available in Section 2 of the Generate Report form"""

    def get_report_generation_content(self):
        return """REPORT GENERATION
==================

⚠ CRITICAL WARNING: Report generation is under development and has NOT
been approved by reporting coordinators. Only TANGRA and AOTA outputs
are currently supported. All generated reports must be carefully
verified before submission. Do not submit without checking.

OPENING THE FORM
----------------
Events menu → Generate Report

The form is divided into five sections. All required sections must be
complete before the Generate Report button becomes active.

SECTION 1: REPORT FORMAT
-------------------------
Choose the reporting organisation format:
  • IOTA North America (V5.6.12r)
  • Trans-Tasman / RASNZ (V4.1.2.G)
  • IOTA-ES / SODIS (Form 2.03)

The camera dropdown in Section 2 is filtered to show only cameras
configured for the selected report type.

SECTION 2: EQUIPMENT SELECTION
-------------------------------
  • Telescope: select from configured telescopes
  • Camera: select from cameras matching the chosen report type
  • Use Manage... buttons to add or edit equipment profiles

SECTION 3: OBSERVATION RESULT
------------------------------
  • Positive - Observed disappearance and reappearance (AOTA required)
  • Negative - No occultation occurred (AOTA optional)
  • Unsure   - Possible event but uncertain (AOTA required)

SECTION 4: OBSERVATION FILES
-----------------------------
Browse to the folder containing your observation files. The file
lists are populated automatically when a folder is selected.

File sources:
  1. Light-curve CSV  - Tangra, R-OTE, or Limovie CSV export
                        (format is auto-detected from the file content)
  2. AOTA XML         - AOTA prediction/analysis files (.aota.xml)
  3. AOTA Report      - AOTA report text files; listed FIRST in the
                        D/R event combo when available
  4. PyOTE metrics    - PyOTE fit_metrics.txt files (detected by content,
                        not filename); a second list lets you pick the
                        aperture/event row within the metrics file

Select one file in each column as needed. A short preview appears below
each list showing extracted times or D/R values for quick verification.

D/R event source priority:
  AOTA Report events are listed first in the event combo, followed by
  AOTA XML events and PyOTE events. The first entry in the list is
  selected by default.

The D and R uncertainty values shown in the event info label are
formatted to 1–2 significant figures (e.g. ±0.2s, ±0.04s).

TIMESTAMP CHECK SUBPANEL
-------------------------
Automatically populated when a Tangra CSV is selected. Analyses frame
timing for irregularities that could affect timing accuracy.

  Delayed frames
    Frames where the interval between consecutive frames is more than
    10% longer than the median interval. Minor timing slip — usually
    caused by brief CPU load. A small number is generally acceptable.

  Late frames
    Frames where the interval is more than 90% longer than the median.
    This almost always means one or more frames were dropped. Each late
    frame is a gap in coverage and may affect timing accuracy.

  Status
    OK               - No delayed or late frames (green)
    Check            - Some delayed frames, no late frames (orange)
    Issues detected  - One or more late frames (red)

  Deviation (min/max)
    Shows the minimum and maximum frame interval expressed as a
    deviation from the median exposure time, in milliseconds.
    e.g. "-0.5 to +42.3 ms" indicates the worst dropped-frame gap.

  Event time warning (orange/red text, right of Inspect button)
    Appears when the predicted event time from OWC falls outside the
    recording start-to-end window of the selected Tangra CSV. This
    does not prevent report generation but should be investigated —
    it may mean the wrong CSV file is selected.

  Explain... button
    Opens a message box with plain-language explanations of all
    three metrics and guidance on when to be concerned.

  Inspect Timestamps... button
    Opens the Timestamp Inspector window (see below). Only enabled
    when a Tangra CSV has been successfully loaded.

SECTION 5: TIMING METHOD
------------------------
Choose the method used to create accurate timestamps for this observation.
The selected method determines which sub-panel is shown.

Tip: most fields and buttons in this section have contextual help. Hover
over a field for a brief tooltip, or click the ? and \u24d8 buttons for a
full explanation. If the Generate Report button is disabled, click the ?
button to the left of it to see exactly what is still required.

NTP (Computer Clock)
  Used when your computer clock was synchronised to a time server during
  recording (e.g. using Meinberg NTP or Windows Time Service with a good
  upstream pool server).

  Y-line:
    The vertical pixel position (in Tangra sensor coordinates) of the star
    in the occultation video. Used to calculate the rolling-shutter
    acquisition delay for your camera model.
    You can get this from Tangra → [right-click aperture] → Properties.

  Calibration Run:
    Select the saved calibration run whose settings match the current
    recording (area, binning, gain, frame rate). OM will calculate the
    camera acquisition delay from the Y-line and calibration data.
    If no run matches, use Tools → Camera Delay Calculator to find the
    correct delay manually.

  NTP Clock Offset:
    Carried forward from the NTP timing analysis in Step 2 (Location
    Confirm dialog). If no analysis was run, enter the offset manually.
    The offset is the signed correction (ms) to add to the measured
    event time — positive means the clock was running slow.

  Correction Status:
    Choose whether timing corrections were already applied in Tangra:

    Applied in Tangra:
      Both the camera delay and NTP offset have already been entered
      in Tangra's light-curve settings. The timestamps in the exported
      CSV already include these corrections.
      You must tick both confirmation checkboxes to confirm the values
      match what you entered. If either value changes (e.g. you update
      the calibration run or Y-line), the checkboxes are automatically
      cleared and the heading turns orange — re-tick after reviewing.

    Not yet applied:
      Corrections have NOT been entered in Tangra. A step-by-step
      guidance panel is shown with the calculated values and Copy
      buttons to transfer them to Tangra. After applying, re-open
      this dialog and select "Applied in Tangra" to proceed.

    Not applicable:
      Used when the NTP system was used for clock sync but rolling-
      shutter corrections are not relevant for this event type
      (e.g. certain negative observations with short videos).

  D/R times warning:
    The corrected D and R preview times are shown below the correction
    status. Two checks run automatically:
    • D ≥ R (red, blocking): for Positive or Unsure observations, the
      reappearance cannot be before or equal to the disappearance.
      This prevents generation until corrected.
    • Net correction > 500 ms (orange, non-blocking): an unusually
      large combined correction that may warrant investigation, but
      does not prevent generation.

  Why OM does not modify the light curve CSV directly:
    OM is designed as a report assembler — it collects results from
    specialist tools (Tangra, AOTA, PyOTE) and produces the final
    report. Keeping the correction step inside Tangra means:
    • The Tangra CSV header is the authoritative record of what was
      applied. Any downstream tool (AOTA, PyOTE, R-OTE, another
      observer) can read the header and see the correction value.
    • There is no risk of double-correction if habits change between
      events (e.g. corrections entered in Tangra AND by OM).
    • OM never needs to reproduce Tangra's internal timestamp
      arithmetic, which handles edge cases (midnight wraparound,
      variable frame rates) that OM does not have visibility of.

  How to verify corrections were applied correctly:
    Camera acquisition delay:
      Open the Tangra CSV in a text editor. Row 8 (the measurement
      parameters row) contains the column 'Acquisition Delay (ms)'.
      The value must match the delay OM calculated — not 0.

    NTP clock offset:
      Tangra does not record the NTP offset in the CSV header, so
      there is no automated way to verify it from the file alone.
      Verification relies on your own record-keeping:
      • The NTP analysis log saved by the gps-timing-analysis tool
        is the authoritative source for the offset value.
      • The timing note written to the report Comments field (by OM
        at generation time) records what values were used.
      • If you are unsure, re-run the NTP analysis for the
        observation night and compare to the value you entered.

    AOTA / PyOTE output:
      AOTA and PyOTE derive D/R times from the timestamps in the
      CSV they are given. If the camera delay is shown correctly
      in the CSV header (above), and you gave AOTA/PyOTE that same
      corrected CSV, the D/R times will be correct. If you re-ran
      AOTA or PyOTE after regenerating the CSV, ensure the new
      result file is the one selected in OM's §4 Observation Files.

GPS (Reference Only — GPS_CMOS):
  For cameras with hardware GPS timestamping (e.g. IOTA-VTI in pass-
  through mode, or dedicated GPS-disciplined hardware). No software
  corrections are needed or applied by OM.

Analog VTI:
  For cameras using a video time inserter. A safety check panel is
  shown reminding you to verify the VTI was functioning correctly
  before generating the report.

Other:
  Free-text description of the timing method. No corrections are
  calculated by OM.

SECTION 6: CONDITIONS
----------------------
  • Clouds: sky transparency (Clear / Fog / Thin cloud / etc.)
  • Stability: atmospheric seeing (Steady / Flickering)
  • Other Conditions: free-text field for additional notes

INCLUDE STATION NAME IN FILENAMES
----------------------------------
A checkbox at the bottom-right of the dialog (unchecked by default).
When checked, the observer's station name is appended to the Trans-Tasman
(RASNZ) report filename:
  e.g. 20250523_778_Theobalda_Gaia_DR3_12345+Smith_HomeObservatory.xlsx

Leave unchecked to generate filenames without the station suffix — the
default behaviour and consistent with earlier releases. This checkbox has
no effect on NA or SODIS report filenames.

GENERATE REPORT BUTTON
-----------------------
Active when all required fields are complete. Click to generate the
pre-filled Excel report and save it to data/reports/.

Manually verify all data in the generated report before submitting.

AFTER REPORT GENERATION — RENAME FILES DIALOG
----------------------------------------------
After a report is successfully saved, a Rename Files dialog appears
offering to rename the observation files so they share the same stem
as the report.

Two sections are shown:
  Selected Observation Files
    The CSV, AOTA XML, AOTA Report, and PyOTE metrics files that were
    loaded in the report dialog.
  Image and Light Curve Files in Observation Folder
    Image files and .lc files discovered in the observation folder
    (.jpg, .jpeg, .png, .bmp, .tif, .tiff, .gif, .lc).

How it works:
  • Each row shows the current filename on the left and an editable
    text box with the proposed new name on the right
  • You can edit any proposed name before confirming
  • All files are checked by default; uncheck any file to skip it
  • Files already named correctly are excluded from the list
  • Click Rename to apply; collisions are skipped and reported
  • Close the dialog without clicking Rename to skip all renames

Suffix preservation:
  Files containing _AOTA in the stem keep the _AOTA_… portion.
  If the filename also contains _Bin{N} before _AOTA, that tag is
  preserved too. For example:
    event_Bin2_AOTA_Report.txt → 20250523_778_..._Bin2_AOTA_Report.txt
    event_AOTA_Event1.xml      → 20250523_778_..._AOTA_Event1.xml
    event_lightcurve.csv       → 20250523_778_....csv


TIMESTAMP INSPECTOR WINDOW
===========================

Opened via the Inspect Timestamps... button. Displays two OxyPlot
charts from the selected Tangra CSV for detailed frame-timing analysis.

CHART 1: FRAME INTERVAL DEVIATION FROM MEDIAN
----------------------------------------------
X axis: Frame number
Y axis: Deviation of each frame interval from the median exposure (ms)
  • Zero line (dashed grey) = perfect, uniform timing
  • Positive values = frame arrived later than expected
  • Negative values = frame arrived slightly early (rare)

Y-axis scaling:
  • Auto-scales to the data range
  • Always shows at least ±5 ms so small deviations remain visible
  • A slight jitter of ±0.5–2 ms is normal and acceptable

CHART 2: SIGNAL LEVEL
----------------------
X axis: Frame number (same range as Chart 1)
Y axis: Signal (ADU) of the primary aperture (signal_1)

Use this chart to visually locate the occultation event and compare
it against any timing anomalies visible in Chart 1.

VERTICAL REFERENCE LINES (both charts)
---------------------------------------
  Blue solid    - Predicted event time from OWC ("Event")
  Red dashed    - D time from AOTA file ("D")
  Green dashed  - R time from AOTA file ("R")

If no AOTA file is selected, D and R lines are not drawn.
If no event time is available, the Event line is not drawn.

STATS LINE (between the two charts)
-------------------------------------
  Median exposure: X.XX ms  |  Min deviation: ±X.XX ms  |  Max deviation: ±X.XX ms

INTERPRETING THE CHARTS
------------------------
  • Scattered points close to zero (< ±2 ms):
      Normal USB or driver jitter — no impact on timing.

  • A single large positive spike:
      One late frame or dropped frame. Check whether it falls within
      or outside the D/R event window. If outside, no impact.

  • Multiple large spikes or spikes during the event window:
      Significant timing issues. The event times may be unreliable.
      Consider noting in your report or contacting your coordinator.

  • Gradual drift (slope across the chart):
      Possible clock or driver issue. Check NTP clock accuracy logs.

  • Event line (blue) outside the D/R window:
      May indicate the wrong AOTA file or CSV was selected, or the
      event prediction was updated after the AOTA was generated."""

    def get_timing_tools_content(self):
        return """TIMING & CALIBRATION TOOLS
      ===========================

      The Tools menu groups timing-related utilities under flat headings so they are
      easy to scan:

      • Camera Delay Calibration
      • NTP / GPS Time Testing
      • PC Performance Testing

      CAMERA DELAY CALIBRATION  (Tools → Camera Delay Calibration → Open Calibration Tool)
      --------------------------------------------------------------------------------------
Measures the rolling-shutter line delay of your camera using GPS-timed LED
flashes.  This is the primary calibration tool — it captures frames from two
apertures (top and bottom of the frame), detects GPS PPS flashes, and fits a
linear model to calculate the time delay per sensor line.

Use this tool when:
• Setting up a new camera for occultation recording
• Changing ROI, binning, or frame rate significantly
• You have a GPS timing LED (e.g. IOTA GPS Timing Device)

Workflow:
1. Connect your GPS timing LED to the serial port
2. Open Tools → Camera Delay Calibration → Open Calibration Tool in SharpCap
3. Point camera at LED through two apertures (top and bottom of frame)
4. Click Start Calibration and wait for data collection to complete
5. Review the fit results (R², per-line delay, line-0 delay)
6. Click Save Calibration to Camera to store results in the camera profile

APPROXIMATE DELAYS (no GPS required):
If you do not have a GPS flasher, use the "Approximate Delays" button in the
Camera Delay Calibration window.  This method:
• Sets the camera to 1 ms exposure and measures the actual frame rate
• Asks you to enter an estimated minimum delay (2 ms is a reasonable default)
• Calculates per-line and line-0 delays from the measured frame rate and ROI height
• Stores results as a synthetic calibration (R² shown as N/A)
These values are approximate but usable when GPS timing is unavailable.

CAMERA DELAY CALCULATOR  (Tools → Camera Delay Calibration → Camera Delay Calculator)
--------------------------------------------------------------------------------------
Calculates the rolling-shutter acquisition delay for a specific star Y pixel
position using previously saved calibration data.

Use this tool when:
• Preparing a timing submission for a recorded occultation
• You need the per-event mid-line delay for Tangra or ROTE

Workflow:
1. Open Tools → Camera Delay Calibration → Camera Delay Calculator
2. Select the camera from the drop-down
3. The grid shows all saved calibration runs for that camera
4. Select the calibration run that matches your recording settings
   (area, binning, gain, exposure)
5. Enter the star's Y pixel position
6. The tool calculates and displays the acquisition delay
7. Click Copy to Clipboard (TANGRA format) to copy the delay value

NTP CLOCK ACCURACY  (Tools → NTP / GPS Time Testing → NTP Clock Accuracy)
--------------------------------------------------------------------------
Analyses NTP loopstats log files to show how accurately the computer clock
is tracking UTC.  Use this after an observing session to verify that your
clock was within acceptable limits during the recording.

Workflow:
1. Open Tools → NTP / GPS Time Testing → NTP Clock Accuracy
2. Browse to your NTP loopstats file (typically in C:\\NTP\\logs\\)
3. Set the date/time range for the recording period
4. Click Analyse to plot clock offset vs time
5. Review offset statistics; offset should stay within ±5 ms for occultation timing

GPS vs NTP TESTING  (Tools → NTP / GPS Time Testing → GPS vs NTP Testing)
---------------------------------------------------------------------------
Compares GPS PPS timestamps against the NTP-disciplined system clock to
verify that NTP is correctly locked to GPS.  Use this tool when commissioning
a new GPS/NTP timing setup or investigating timing discrepancies.

Workflow:
1. Connect your GPS device and ensure NTP is running
2. Open Tools → NTP / GPS Time Testing → GPS vs NTP Testing
3. Select the GPS serial port and log file locations
4. Click Start to begin comparison logging
5. Review the offset plot; offsets should be consistently < 1 ms

PC PERFORMANCE TESTING  (Tools → PC Performance Testing → Open PC Performance Testing)
---------------------------------------------------------------------------------------
Monitors frame-to-frame timestamp stability while SharpCap is acquiring video,
and can also analyse an ADV recording after you load it manually. Use this when
you suspect the PC, USB bus, storage, or background activity may be affecting
timestamp consistency.

Workflow:
1. Open Tools → PC Performance Testing → Open PC Performance Testing
2. Choose Live Mode to monitor timestamps during capture, or select Record to ADV File
3. In ADV mode, manually record an ADV file, then load it for analysis
4. Review the timestamp delta plots and PC load chart
5. Save the workbook if you want the plots, summary, and raw data exported

CALIBRATION DATA STORAGE
-------------------------
Calibration results are stored in the camera profile inside
data/config/occultation_config.json.  Each saved calibration records:
• Camera name and area (ROI)
• Binning, gain, and exposure at time of calibration
• Per-line delay (ms/line) and line-0 delay (ms)
• R² of fit (or N/A for approximate results)
• Date/time and optional label/notes

Multiple calibration runs can be stored per camera — the Camera Delay
Calculator lets you select which run to use for a given observation."""
    

class HelpManager:
    """Manages help system integration"""
    
    def __init__(self, theme_manager):
        self.theme_manager = theme_manager
    
    def show_help(self, parent_form=None, topic=None):
        """Show the help dialog, optionally opening to a specific topic"""
        help_dialog = HelpDialog(self.theme_manager, initial_topic=topic)
        if parent_form:
            help_dialog.Owner = parent_form
        help_dialog.ShowDialog()
    
    def show_about(self):
        """Show about dialog with author information"""
        about_text = """OCCULTATION MANAGER FOR SHARPCAP
Version 0.2.0-beta.9

Author: Michael Camilleri

https://github.com/labstercam/occultation-tools


A tool for managing asteroid occultation observations through customizable SharpCap sequences.

FEATURES:
\u2022 Automated event download from OccultWatcher Cloud
\u2022 Generate realistic test events for practice and testing
\u2022 Interactive observation preparation tools
\u2022 Customizable SharpCap sequence generation
\u2022 Full control over recording workflow automation
\u2022 Equipment-specific template customization
\u2022 Multi-event session support
\u2022 Night vision preserving interface
\u2022 Station filtering and event management
\u2022 Telescope and camera profile management
\u2022 Camera delay calibration (GPS-timed LED flash method)
\u2022 Camera delay calculator (per-event acquisition delay)
\u2022 NTP clock accuracy analysis
\u2022 GPS vs NTP timing comparison

PRIMARY WORKFLOW:
Download \u2192 Filter \u2192 Prepare \u2192 Customize \u2192 Generate Sequence \u2192 Execute

OPTIONAL FEATURES:
\u2022 Excel report generation (NA / Trans-Tasman / SODIS)
  \u26a0 Experimental - Not approved by reporting coordinators
\u2022 Tangra / R-OTE / Limovie CSV import with frame-timing analysis and Timestamp Inspector
\u2022 AOTA XML and AOTA Report file import for D/R times in reports
\u2022 PyOTE fit_metrics.txt import for D/R times in reports
\u2022 Post-report Rename Files dialog to match observation files to report stem
\u2022 Optional station name suffix in Trans-Tasman report filenames

This tool emphasizes giving you complete control through SharpCap sequences.
Customize templates to match your equipment and automate as much or as little
as you need. Test thoroughly before relying on automated sequences.

For complete documentation, use Help \u2192 User Guide.
For licence terms, use Help \u2192 Licence."""

        MessageBox.Show(about_text, "About Occultation Manager",
                       MessageBoxButtons.OK, MessageBoxIcon.Information)

    def show_licence(self, parent_form=None):
        """Show BSD 3-Clause licence in a scrollable dialog"""
        licence_text = """BSD 3-Clause License

Copyright (c) 2026, Michael Camilleri
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this
   list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice,
   this list of conditions and the following disclaimer in the documentation
   and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its
   contributors may be used to endorse or promote products derived from
   this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
AND WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
LIMITED TO THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A
PARTICULAR PURPOSE. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
POSSIBILITY OF SUCH DAMAGE."""

        sf = _detect_scale_factor()
        dlg = Form()
        dlg.Text = "Licence"
        dlg.FormBorderStyle = FormBorderStyle.FixedDialog
        dlg.MaximizeBox = False
        dlg.MinimizeBox = False
        dlg.StartPosition = FormStartPosition.CenterParent
        dlg.ClientSize = Size(int(580 * sf), int(380 * sf))

        txt = TextBox()
        txt.Multiline = True
        txt.ReadOnly = True
        txt.ScrollBars = ScrollBars.Vertical
        txt.WordWrap = True
        txt.Font = Font("Courier New", 8.5)
        txt.Text = licence_text
        txt.Location = Point(int(10 * sf), int(10 * sf))
        txt.Size = Size(int(560 * sf), int(320 * sf))
        txt.BorderStyle = 0  # None
        dlg.Controls.Add(txt)

        btn_ok = Button()
        btn_ok.Text = "Close"
        btn_ok.DialogResult = DialogResult.OK
        btn_ok.Size = Size(int(80 * sf), int(28 * sf))
        btn_ok.Location = Point(int((580 * sf - 90 * sf) // 2), int(346 * sf))
        dlg.Controls.Add(btn_ok)
        dlg.AcceptButton = btn_ok

        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(dlg, theme_colors)

        if parent_form:
            dlg.Owner = parent_form
        dlg.ShowDialog()