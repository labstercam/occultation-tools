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
    
    def __init__(self, theme_manager):
        Form.__init__(self)
        self.theme_manager = theme_manager
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
        main_split.SplitterDistance = int(600 * sf)  # 3x wider for better topic visibility
        main_split.FixedPanel = FixedPanel.Panel1
        self.Controls.Add(main_split)
        
        # Left panel - Help topics tree
        self.setup_help_topics(main_split.Panel1)
        
        # Right panel - Help content
        self.setup_help_content(main_split.Panel2)
        
        # Load initial content
        self.load_overview_content()
        
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
        self.tree_topics.AfterSelect += self.topic_selected
        panel.Controls.Add(self.tree_topics)
        
        lbl_topics = Label()
        lbl_topics.Text = "Help Topics:"
        lbl_topics.Dock = DockStyle.Top
        lbl_topics.Height = int(25 * sf)
        lbl_topics.Font = Font("Microsoft Sans Serif", 9 * sf, FontStyle.Bold)
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
        self.txt_help_content.Font = Font("Microsoft Sans Serif", 10 * sf)
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
        
        # Expand top-level nodes
        for node in self.tree_topics.Nodes:
            node.Expand()
        
        # Select Quick Start by default
        self.tree_topics.SelectedNode = quickstart_node
    
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
    
    def get_help_content(self, topic):
        """Get help content for a specific topic"""
        content_map = {
            "quickstart": self.get_quickstart_content().replace('\n','\r\n'),
            "workflow": self.get_workflow_content().replace('\n','\r\n'),
            "template_modification": self.get_template_modification_content().replace('\n','\r\n')
        }
        
        return content_map.get(topic, "Help content not found for this topic.")
    
    
    def get_quickstart_content(self):
        return """QUICK START GUIDE
==================

Installation and first-time setup for Occultation Manager.

INSTALLATION
------------
1. Download occultation-manager.zip from GitHub
2. Extract to a folder with read/write access
   Recommended: Documents\\SharpCap\\occultation-manager
3. Start SharpCap
4. Go to File → SharpCap Settings → Startup Scripts
5. Browse to the extracted folder and select the 'main' script
6. Click OK and restart SharpCap

A new "Occultations" button appears in SharpCap's main toolbar.

INITIAL CONFIGURATION
---------------------
Click the Occultations button to open Occultation Manager.

Go to Tools → Configuration and set up:

CREDENTIALS TAB:
• OWC Email: Your Occult Watcher Cloud login
• OWC Password: Your OWC password
• API Key: Get from OWC User Profile → Permissions & Settings

FILE PATHS TAB:
• File Folder: Where events are stored, templates are read from, and 
  Reports are saved
  - Templates: Any .txt file with "template" in the filename
  - Reports: Saved to [File Folder]/Reports/ subfolder (auto-created)
  - Event data: occultations.json and occultations_latest.json

• Sequence Path: Where .scs sequence files are saved (defaults to File 
  Folder if left empty)
  - Can be set to different location for organizational purposes
  - Sequence files: YYYYMMDD [Event Name].scs format

• Days to Retain Events: How long to keep old events (default: 14)

USER SETTINGS TAB:
• Base Duration: Extra recording time (default: 60s)
• GOTO Lead Time: Slew start before recording (default: 240s)
• Mag for 40ms exp: Reference magnitude (default: 12.0)
• Default Gain: Camera gain for new events (default: 450)

Click the 'Explain' button next to any setting for detailed help.

Click Save to apply changes.

FIRST USE
---------
1. Click Download to retrieve your assigned events from OWC
2. Review events in the grid (times, magnitudes, exposures)
3. Use Station Filter to show only your observing location
4. Select an event and explore the Observation Preparation panel
5. Check event checkboxes and click Create Sequences
6. Choose a template (recommend: SharpCap Sequence UTC Template)
7. Find generated .scs files in your Sequence Path folder

GETTING STARTED
---------------
• Download Events: Syncs with OWC to get your station assignments
• Station Filter: Shows events for specific location
• Event Grid: All event information with sortable columns
• Quick Filters: Show Today/Future/All events
• Observation Preparation: Test GOTO, plate solve, camera setup
• Create Sequences: Generate customizable SharpCap .scs files
• Night Mode: Red theme for observing sessions

See "Event Recording Workflow" for detailed workflow steps.
See "Template Modification" for customizing sequences."""

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
Click Download button (or File → Download Events)
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
• GOTO & Center: Slew telescope to target
• Plate Solve & Label: Verify pointing and mark target star

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

• .scs files created in your Sequence Path folder
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
• GOTO & Center: Position telescope when ready
• Plate Solve & Label: Verify pointing
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
• Click Run Sequences button (or Sequences → Run Selected Sequences)
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

STEP 8: GENERATE REPORT (OPTIONAL - EXPERIMENTAL)
--------------------------------------------------
⚠ WARNING: Report generation is experimental and not approved by 
reporting coordinators. Verify all data before submission.

Tools → Generate Report:
• Select report format (North America / Trans-Tasman)
• Choose equipment (telescope/camera)
• Set observation type (Positive/Negative/Unsure)
• Select folder with AOTA and Tangra CSV files
• Generate pre-filled Excel report
• MANUALLY VERIFY all data before submitting

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
• Report generation is experimental - verify before submission
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
• Location: File Folder (configured in Tools → Configuration)
• Files: Any .txt file with "template" in the filename
• Examples: "SharpCap Sequence UTC template.txt", "MyCustom template.txt"
• The application scans File Folder for these files when you click 
  Create Sequences

SEQUENCES (saved to):
• Location: Sequence Path (configured in Tools → Configuration)
• Files: .scs files generated from templates
• Naming: YYYYMMDD [Event Name].scs
• Examples: "20260125 433 Eros - Station ABC.scs"
• If Sequence Path is empty, sequences are saved to File Folder

REPORTS (saved to):
• Location: [File Folder]/Reports/ subfolder (auto-created)
• Files: .xlsx Excel report files
• Naming: YYYYMMDD_number_name_catalog_star±Observer_Station.xlsx
• Examples: "20251107_778_Theobalda_Gaia_DR3_12345+Smith_Observatory.xlsx"

CREATING CUSTOM TEMPLATES
--------------------------
1. Create a new .txt file in your File Folder
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
{gain} | Camera gain value (0-600) | "450"
{recording_duration} | Total recording duration in seconds (integer) | "180"

Notes: Exposure, gain, and recording_duration use calculated values or 
custom overrides from Edit Settings dialog.

MAGNITUDE INFORMATION:
{star_mag} | Target star magnitude (1 decimal) | "11.2"
{comb_mag} | Combined star+asteroid magnitude (1 decimal) | "11.8"
{mag_drop} | Magnitude change during occultation (1 decimal) | "0.6"

EVENT PARAMETERS:
{time_error} | Event timing uncertainty in seconds (1 decimal) | "3.5"

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
    

class HelpManager:
    """Manages help system integration"""
    
    def __init__(self, theme_manager):
        self.theme_manager = theme_manager
    
    def show_help(self, parent_form=None):
        """Show the help dialog"""
        help_dialog = HelpDialog(self.theme_manager)
        if parent_form:
            help_dialog.Owner = parent_form
        help_dialog.ShowDialog()
    
    def show_about(self):
        """Show about dialog with author information"""
        about_text = """OCCULTATION MANAGER FOR SHARPCAP
Version 0.1.0

Author: Michael Camilleri

https://github.com/labstercam/occultation-tools


A tool for managing asteroid occultation observations through customizable SharpCap sequences.

FEATURES:
• Automated event download from OccultWatcher Cloud
• Interactive observation preparation tools  
• Customizable SharpCap sequence generation
• Full control over recording workflow automation
• Equipment-specific template customization
• Multi-event session support
• Night vision preserving interface
• Station filtering and event management

PRIMARY WORKFLOW:
Download → Filter → Prepare → Customize → Generate Sequence → Execute

OPTIONAL FEATURES:
• Excel report generation (North America / Trans-Tasman)
  ⚠ Experimental - Not approved by reporting coordinators
• AOTA Report and Tangra CSV data import for reports

This tool emphasizes giving you complete control through SharpCap sequences. 
Customize templates to match your equipment and automate as much or as little 
as you need. Test thoroughly before relying on automated sequences.

For complete documentation, use Help → User Guide.

Licensed under the BSD 3-Clause License

Copyright (c) 2026, Michael Camilleri

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
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."""

        MessageBox.Show(about_text, "About Occultation Manager", 
                       MessageBoxButtons.OK, MessageBoxIcon.Information)