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
        
        lbl_topics = Label()
        lbl_topics.Text = "Help Topics:"
        lbl_topics.Dock = DockStyle.Top
        lbl_topics.Height = int(25 * sf)
        lbl_topics.Font = Font("Microsoft Sans Serif", 9 * sf, FontStyle.Bold)
        panel.Controls.Add(lbl_topics)
        
        self.tree_topics = TreeView()
        self.tree_topics.Dock = DockStyle.Fill
        self.tree_topics.AfterSelect += self.topic_selected
        panel.Controls.Add(self.tree_topics)
        
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
        

        # Overview
        print('Overview Tag')
        overview_node = TreeNode("Overview")
        overview_node.Tag = "overview"
        self.tree_topics.Nodes.Add(overview_node)
        
        # Getting Started
        print('Getting Started Tag')
        getting_started = TreeNode("Getting Started")
        getting_started.Tag = "getting_started"
        self.add_node_with_tag(getting_started, "Initial Setup", "initial_setup")
        self.add_node_with_tag(getting_started, "Configuration", "configuration")
        self.add_node_with_tag(getting_started, "First Use", "first_use")
        self.tree_topics.Nodes.Add(getting_started)
        
        # Main Interface
        print('Main Interface Tag')
        main_interface = TreeNode("Main Interface")
        main_interface.Tag = "main_interface"
        self.add_node_with_tag(main_interface, "Menu Bar", "menu_bar")
        self.add_node_with_tag(main_interface, "Toolbar", "toolbar")
        self.add_node_with_tag(main_interface, "Events Grid", "events_grid")
        self.add_node_with_tag(main_interface, "Station Filter", "station_filter")
        self.add_node_with_tag(main_interface, "Bottom Panel", "bottom_panel")
        self.add_node_with_tag(main_interface, "Status Bar", "status_bar")
        self.tree_topics.Nodes.Add(main_interface)
        
        # Event Management
        event_mgmt = TreeNode("Event Management")
        event_mgmt.Tag = "event_management"
        self.add_node_with_tag(event_mgmt, "Downloading Events", "downloading_events")
        self.add_node_with_tag(event_mgmt, "Viewing Event Details", "event_details")
        self.add_node_with_tag(event_mgmt, "Edit Settings", "editing_exposures")
        self.add_node_with_tag(event_mgmt, "Selecting Events", "selecting_events")
        self.tree_topics.Nodes.Add(event_mgmt)
        
        # Sequence Generation
        sequences = TreeNode("Sequence Generation")
        sequences.Tag = "sequences"
        self.add_node_with_tag(sequences, "Creating Sequences", "creating_sequences")
        self.add_node_with_tag(sequences, "Template Selection", "template_selection")
        self.add_node_with_tag(sequences, "Combined Scripts", "combined_scripts")
        self.add_node_with_tag(sequences, "Running Sequences", "running_sequences")
        self.tree_topics.Nodes.Add(sequences)
        
        # Observation Preparation
        obs_prep = TreeNode("Observation Preparation")
        obs_prep.Tag = "observation_prep"
        self.add_node_with_tag(obs_prep, "Loading Events", "loading_events")
        self.add_node_with_tag(obs_prep, "GOTO & Centering", "goto_centering")
        self.add_node_with_tag(obs_prep, "Plate Solving", "plate_solving")
        self.tree_topics.Nodes.Add(obs_prep)
        
        # Report Generation
        report_gen = TreeNode("Report Generation")
        report_gen.Tag = "report_generation"
        self.add_node_with_tag(report_gen, "Report Dialog", "report_dialog")
        self.add_node_with_tag(report_gen, "File Selection", "file_selection")
        self.add_node_with_tag(report_gen, "AOTA Files", "aota_files")
        self.add_node_with_tag(report_gen, "Timing Data", "timing_data")
        self.add_node_with_tag(report_gen, "Validation", "report_validation")
        self.tree_topics.Nodes.Add(report_gen)
        
        # Advanced Features
        advanced = TreeNode("Advanced Features")
        advanced.Tag = "advanced"
        self.add_node_with_tag(advanced, "Night Mode", "night_mode")
        self.add_node_with_tag(advanced, "Tonight's Events", "tonights_events")
        self.add_node_with_tag(advanced, "Automation", "automation")
        self.tree_topics.Nodes.Add(advanced)
        
        # Troubleshooting
        troubleshooting = TreeNode("Troubleshooting")
        troubleshooting.Tag = "troubleshooting"
        self.add_node_with_tag(troubleshooting, "Common Issues", "common_issues")
        self.add_node_with_tag(troubleshooting, "Error Messages", "error_messages")
        self.add_node_with_tag(troubleshooting, "Configuration Problems", "config_problems")
        self.tree_topics.Nodes.Add(troubleshooting)
        
        # Expand top-level nodes
        for node in self.tree_topics.Nodes:
            node.Expand()
        
        # Select overview by default
        self.tree_topics.SelectedNode = overview_node
    
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
        """Load the overview content by default"""
        self.load_help_content("overview")
    
    def get_help_content(self, topic):
        """Get help content for a specific topic"""
        content_map = {
            "overview": self.get_overview_content().replace('\n','\r\n'),
            "getting_started": self.get_getting_started_content().replace('\n','\r\n'),
            "initial_setup": self.get_initial_setup_content().replace('\n','\r\n'),
            "configuration": self.get_configuration_content().replace('\n','\r\n'),
            "first_use": self.get_first_use_content().replace('\n','\r\n'),
            "main_interface": self.get_main_interface_content().replace('\n','\r\n'),
            "menu_bar": self.get_menu_bar_content().replace('\n','\r\n'),
            "toolbar": self.get_toolbar_content().replace('\n','\r\n'),
            "events_grid": self.get_events_grid_content().replace('\n','\r\n'),
            "station_filter": self.get_station_filter_content().replace('\n','\r\n'),
            "bottom_panel": self.get_bottom_panel_content().replace('\n','\r\n'),
            "status_bar": self.get_status_bar_content().replace('\n','\r\n'),
            "event_management": self.get_event_management_content().replace('\n','\r\n'),
            "downloading_events": self.get_downloading_events_content().replace('\n','\r\n'),
            "event_details": self.get_event_details_content().replace('\n','\r\n'),
            "editing_exposures": self.get_editing_exposures_content().replace('\n','\r\n'),
            "selecting_events": self.get_selecting_events_content().replace('\n','\r\n'),
            "sequences": self.get_sequences_content().replace('\n','\r\n'),
            "creating_sequences": self.get_creating_sequences_content().replace('\n','\r\n'),
            "template_selection": self.get_template_selection_content().replace('\n','\r\n'),
            "combined_scripts": self.get_combined_scripts_content().replace('\n','\r\n'),
            "running_sequences": self.get_running_sequences_content().replace('\n','\r\n'),
            "observation_prep": self.get_observation_prep_content().replace('\n','\r\n'),
            "loading_events": self.get_loading_events_content().replace('\n','\r\n'),
            "goto_centering": self.get_goto_centering_content().replace('\n','\r\n'),
            "plate_solving": self.get_plate_solving_content().replace('\n','\r\n'),
            "advanced": self.get_advanced_content().replace('\n','\r\n'),
            "night_mode": self.get_night_mode_content().replace('\n','\r\n'),
            "tonights_events": self.get_tonights_events_content().replace('\n','\r\n'),
            "automation": self.get_automation_content().replace('\n','\r\n'),
            "report_generation": self.get_report_generation_content().replace('\n','\r\n'),
            "report_dialog": self.get_report_dialog_content().replace('\n','\r\n'),
            "file_selection": self.get_file_selection_content().replace('\n','\r\n'),
            "aota_files": self.get_aota_files_content().replace('\n','\r\n'),
            "timing_data": self.get_timing_data_content().replace('\n','\r\n'),
            "report_validation": self.get_report_validation_content().replace('\n','\r\n'),
            "troubleshooting": self.get_troubleshooting_content().replace('\n','\r\n'),
            "common_issues": self.get_common_issues_content().replace('\n','\r\n'),
            "error_messages": self.get_error_messages_content().replace('\n','\r\n'),
            "config_problems": self.get_config_problems_content().replace('\n','\r\n')
        }
        
        return content_map.get(topic, "Help content not found for this topic.")
    
    def get_sequences_content(self):
            return """SEQUENCE GENERATION
===================

Creating SharpCap .scs files for automated occultation recording.

OVERVIEW
--------
Sequences automate SharpCap operations. Sequences are used rather than direct control to allow template customization and manual execution.

WORKFLOW
--------
1. Select events using checkboxes
2. Click Create Sequences button
3. Choose template from dialog
4. Application generates .scs files
5. Files saved to Sequence Path
6. Load manually in SharpCap or use Run Sequences

TEMPLATE SYSTEM
---------------
• Built-in default template for basic operations
• Custom templates: .txt files with "template" in name in File Folder
• Variable substitution for event data
• Template preview in selection dialog

TEMPLATE VARIABLES
------------------
{object_name}: Asteroid name
{event_time}: Event center time UTC
{goto_time}: GOTO start time
{start_time}: Recording start time
{recording_duration}: Total recording seconds
{exposure}: Camera exposure in seconds
{gain}: Camera gain value (0-600)
{recording_duration}: Total recording duration in seconds
{ra}, {dec}: Target coordinates
{star_mag}, {comb_mag}: Brightness values
{event_time_local}, {goto_time_local}, {start_time_local}: Local times

FILE NAMING
-----------
Format: YYYYMMDD [Event Name].scs
Example: 20241215 433 Eros - Station ABC.scs

BATCH GENERATION
----------------
• Multiple events create multiple files
• Progress shown during generation
• Summary report of success/failure

TIMING COORDINATION
-------------------
Automatic calculations:
• GOTO start time with configured lead time
• Recording start based on uncertainty
• Recording duration with base duration buffer

EXECUTION OPTIONS
-----------------
Manual: Load .scs files in SharpCap
Automated: Use Run Sequences for timed execution

Default template provides basic functionality. Create custom templates for specific equipment."""


    def get_overview_content(self):
        return """OCCULTATION MANAGER FOR SHARPCAP
Author: Michael Camilleri

OVERVIEW
========

A SharpCap integration tool for automated occultation observation management.

MAIN WORKFLOW
-------------
1. Configure OWC credentials and paths (Tools → Configuration)
2. Download assigned events from OccultWatcher Cloud
3. Filter by station and date range
4. Prepare events using interactive setup tools
5. Generate SharpCap sequence files from templates
6. Execute sequences with automated timing

KEY FEATURES
------------
• OccultWatcher Cloud event download and synchronization
• Station-based filtering and event organization
• Calculated exposure times based on star magnitudes
• Interactive telescope positioning and plate solving
• Template-based sequence generation (.scs files)
• Automated sequence execution with precise timing
• Night Mode theme for observing sessions

The tool streamlines occultation workflows from event download through automated recording."""

    def get_getting_started_content(self):
        return """GETTING STARTED
===============

Quick setup guide for new users.

PREREQUISITES
-------------
• SharpCap 4.1 or later (recent version recommended)
• OccultWatcher Cloud account with station assignments
• API Key from OWC user profile

INITIAL CONFIGURATION
---------------------
1. Open Tools → Configuration
2. Credentials tab: Enter OWC email and password
3. API Settings tab: Paste API key from OWC profile
4. File Paths tab: Set File Folder and Sequence Path
5. Recording tab: Set Base Duration, GOTO Lead Time, exposure reference
6. Click Save

FIRST EVENT WORKFLOW
--------------------
1. Click Download to retrieve assigned events
2. Use station filter to select your location
3. Select an event and click Event Details to review
4. Use Quick Filters (Today/Future/All) to show relevant events
5. Check an event checkbox and click Create Sequences
6. Select a template to generate a .scs file

The default template provides basic functions. Create custom templates for your specific equipment setup.

TESTING PREPARATION TOOLS
-------------------------
1. Select an event in the grid
2. Click Load Event in Observation Preparation panel
3. Test Setup button to configure SharpCap
4. Test GOTO button for telescope positioning
5. Use Plate Solve to verify pointing accuracy

Once configured, the tool automates event management and sequence generation."""

    def get_initial_setup_content(self):
        return """INITIAL SETUP
=============

Configuration required before first use.

CREDENTIALS
-----------
Tools → Configuration → Credentials tab:
• OWC Email: Your OccultWatcher Cloud login email
• OWC Password: Your account password

Must match active OWC account exactly.

API KEY
-------
Tools → Configuration → API Settings tab:
• Log into https://cloud.occultwatcher.net
• Navigate to User Profile → User Permissions
• Copy API key and paste into API Settings

Email must be verified in OWC before API key will work.

FILE PATHS
----------
Tools → Configuration → File Paths tab:
• File Folder: Event data and template storage location
• Sequence Path: .scs file output directory
• Days to Retain: Number of days to keep events (1-400, default 14)

Folders are created automatically if they don't exist.

RECORDING PARAMETERS
--------------------
Tools → Configuration → User Settings tab:
• Base Duration: Buffer time added to event duration (default: 60s)
• GOTO Lead Time: Seconds before event to start positioning (default: 240s)
• Magnitude Reference: Star magnitude producing 40ms exposure (default: 12.0)
• Default Gain: Camera gain for all events unless overridden (default: 450, range 0-600)

VERIFICATION
------------
Click Download to test configuration. Events should load into grid."""

    def get_configuration_content(self):
        return """CONFIGURATION
=============

Settings dialog accessed via Tools → Configuration.

The Configuration dialog has three tabs for organizing settings:

CREDENTIALS TAB
---------------
How to Get Your OWC Credentials:

1. Create an account or log in at Occult Watcher Cloud
2. Go to your User Profile page (link below)
3. Click on the 'Permissions & Settings' sub-tab
4. Find or generate your API Key in that section
5. Copy your email and API Key to the fields above

Fields:
• OWC Email: Your Occult Watcher Cloud account email address
• OWC Password: Your Occult Watcher Cloud account password
• API Host: API server hostname or URL for custom occultation data sources
• API Key: API authentication key for accessing custom occultation data sources

FILE PATHS TAB
--------------
How Download from OWC Works:

When you click 'Download Events', the application:
1. Reads your 'Upcoming Events' from OWC
2. Saves the downloaded events to 'Latest File'
3. Merges with existing 'Occultations File'
4. Retains only events no more than the configured number of days old

Fields:
• File Folder: Folder where downloaded occultation data files are stored
• Sequence Path: Folder where generated SharpCap sequence files (.scs) are saved
• Occultations File: Filename for the main occultation events data file (merged with downloads, retention period configurable)
• Latest File: Filename for storing the latest downloaded occultation events (replaced on each download)

USER SETTINGS TAB
-----------------
Understanding These Settings:

Recording Duration Formula:
  Duration = Base Duration + Event Duration (if >5 s) + 6 × Uncertainty (if >2 s)
    Example 1. Base Duration 60 s,  Event Duration 1.2 s, Uncertainty 1 s → 60s total
    Example 2. Base Duration 60 s,  Event Duration 6 s, Uncertainty 3 s  → 60 + 6 + 18 = 84s
In plain English: Start with the base duration, and add the event duration if it's more than 5 seconds, and add 6 times the uncertainty if it's more than 2 s to ensure full event coverage.

Exposure Time Formula:
  Exposure = 40 ms × 2^(CombMag + Extinction - MagRef)
  Adjusted for atmospheric extinction based on star altitude
In plain English: For every magnitude the star is dimmer than the reference magnitude, the exposure time doubles. 
MagRef: The star magnitude where you would usually use 40 ms exposure
    Example. MagRef 10.0, CombMag 12.0, Extinction 0.3 → 40 × 2^(12.0 + 0.3 - 10.0), rounded to 40 × 2^(2) = 160 ms
40 ms is the minimum exposure that will be automatically set.
Values set by doubling are 80 ms, 160 ms, 320 ms etc.
You can manually set a custom exposure per event if desired.

⚠ Sync Mount Warning:
Only enable 'Sync Mount' if you usually Sync the mount with each GOTO.
Do NOT sync if: Have a permanently aligned mount or use a refined pointing model.
Syncing could adversely affect your carefully calibrated pointing model!

Fields:
• Base Duration (s): Base recording duration in seconds. Additional time is added based on event duration and uncertainty
• GOTO Lead Time (s): How many seconds before the start of recording to begin the GOTO slew to the target position
• Mag for 40ms exp: Reference star magnitude that requires 40ms exposure. Used to calculate appropriate exposure times for stars of different magnitudes
• Sync Mount with GOTO: Enable to sync mount position after each GOTO. WARNING: Only enable if you typically sync your mount. Do NOT use with refined pointing models.
• Display UTC in Grid: Display event times in UTC (Coordinated Universal Time) in the main grid. When unchecked, times are shown in local time

All settings are validated before saving. Click Save to apply changes or Cancel to discard."""

    def get_first_use_content(self):
        return """FIRST USE
=========

Step-by-step first session workflow.

DOWNLOAD EVENTS
---------------
Click Download button to retrieve assigned events from OWC. Events appear in grid with calculated exposures and recording durations.

EXPLORE EVENTS
--------------
• Click column headers to sort
• Use station filter dropdown to filter by location
• Double-click rows for Event Details dialog
• Check event Status column for timing

TEST PREPARATION TOOLS
----------------------
1. Select an event in the grid
2. Click Load Event in Observation Preparation panel
3. Click Setup to configure SharpCap for the event
4. Test GOTO to position telescope
5. Use Plate Solve to verify pointing

CREATE TEST SEQUENCE
--------------------
1. Check one or more event checkboxes
2. Click Create Sequences button
3. Select a template from the dialog
4. Verify .scs files created in Sequence Path

VERIFY OUTPUT
-------------
Open generated .scs file in text editor to confirm coordinates, exposure, and timing are correct. Test loading in SharpCap."""

    def get_main_interface_content(self):
        return """MAIN INTERFACE
==============

Main window layout and components.

LAYOUT
------
1. Menu Bar: File, Events, Tools, Help
2. Toolbar: Single row of action buttons
3. Station Filter: Dropdown for location filtering
4. Events Grid: Sortable table of all events
5. Bottom Panel: Quick Filters and Observation Preparation
6. Status Bar: Operation status and event count

EVENTS GRID
-----------
Central display showing all event data:
• Checkboxes for batch selection
• Sortable columns (click headers)
• Double-click rows for Event Details
• Double-click Exposure column to edit

BOTTOM PANEL
------------
Quick Filters group:
• Today: Events in next 24 hours
• Future: All upcoming events
• All: Clear filters
• On/Off: Toggle selected event checkboxes
• Selection summary label

Observation Preparation group:
• Load Event: Select event from grid
• GOTO: Position telescope
• Plate Solve: Verify pointing
• Setup: Configure SharpCap
• Current event display label

Workflow follows top-to-bottom: download → filter → prepare → generate sequences."""

    def get_menu_bar_content(self):
        return """MENU BAR
========

Top-level menu access to all functions.

FILE MENU
---------
• Download Events: Retrieve assigned events from OWC
• Refresh Events: Reload from local files
• Exit: Close application

EVENTS MENU
-----------
• Event Details: Show detailed event information dialog
• Edit Exposure: Modify camera exposure time
• Select All: Check all visible events
• Select None: Clear all checkboxes

TOOLS MENU
----------
• Configuration: Open settings dialog
• Template Manager: Select sequence templates

HELP MENU
---------
• User Guide: This help system
• About: Version and license information

Most functions also available via toolbar buttons for quick access."""

    def get_toolbar_content(self):
        return """TOOLBAR
=======

Single row of action buttons below menu bar.

BUTTONS (LEFT TO RIGHT)
-----------------------
• Download: Retrieve events from OWC
• Refresh: Reload from local files
• Station Filter: Dropdown to filter by location
• Event Details: Show detailed event information
• Edit Settings: Modify exposure, gain, and recording duration
• Create Sequences: Generate .scs files from template
• Run Sequences: Execute sequences with automated timing
• Night Mode: Toggle red theme for observing

BUTTON STATES
-------------
Some buttons require event selection to be enabled:
• Event Details: Requires selected row
• Edit Settings: Requires selected row
• Create Sequences: Requires checked events
• Run Sequences: Requires checked events

Buttons arranged in typical workflow order: download → filter → review → generate → execute."""

    def get_events_grid_content(self):
        return """EVENTS GRID
===========

Central table displaying all occultation events.

COLUMNS
-------
• Selected: Checkbox for batch operations
• Event Name: Asteroid name and station identifier
• Station: Observing location
• Date/Time UTC: Event occurrence time
• Star Mag: Target star magnitude
• Comb Mag: Combined magnitude (star + asteroid)
• Mag Drop: Brightness change during occultation
• Exposure (ms): Camera exposure time (* = custom)
• Gain: Camera gain value 0-600 (* = custom)
• Recording Time (s): Total recording duration (* = custom)
• Max Duration (s): Maximum occultation length
• Alt/Az: Target altitude and azimuth at event time
• Status: Event timing status

INTERACTIONS
------------
• Click row: Select event
• Double-click row: Open Event Details dialog
• Double-click Exposure cell: Edit settings (exposure, gain, duration)
• Double-click Gain cell: Edit settings (exposure, gain, duration)
• Double-click Recording Time cell: Edit settings (exposure, gain, duration)
• Check checkbox: Select for batch operations
• Click column header: Sort by that column
• Click OWC link: Open event in browser

VISUAL INDICATORS
-----------------
• * after exposure: Custom exposure (not calculated)
• * after gain: Custom gain (not default 450)
• * after recording time: Custom duration (not calculated)
• Status values: future, past, starting soon
• Theme colors adapt for Night Mode"""

    def get_station_filter_content(self):
        return """STATION FILTER
==============

Dropdown combo box in toolbar for filtering events by observing location.

OPERATION
---------
• Dropdown populated with station names from downloaded events
• "All Stations" shows all events (default)
• Select station name to filter to that location only
• Filter applies immediately on selection
• Status bar updates to show filtered event count

FEATURES
--------
• Event checkbox selections preserved when filtering
• Works in combination with Quick Filters (Today/Future/All)
• Column sorting preserved during filtering
• Useful for observers with multiple station assignments

Select "All Stations" to clear the station filter."""

    def get_bottom_panel_content(self):
        return """BOTTOM PANEL
============

Two group boxes for quick filtering and observation preparation.

QUICK FILTERS GROUP
-------------------
Date range filtering buttons:
• Today: Show events in next 24 hours
• Future: Show all upcoming events
• All: Clear date filters (show all events)
• On/Off: Toggle checkboxes for visible events

Selection Summary label shows count of checked events.

OBSERVATION PREPARATION GROUP
-----------------------------
Interactive telescope and camera setup tools:
• Load Event: Select event from grid for preparation
• GOTO: Position telescope to event coordinates
• Plate Solve: Verify telescope pointing accuracy
• Setup: Configure SharpCap camera and capture settings

Current Event Display shows:
• Loaded event name and coordinates
• Event timing (UTC and local)
• Calculated exposure and recording duration
• Star magnitudes and other event parameters

Preparation tools allow interactive testing before generating sequences for automated execution."""

    def get_status_bar_content(self):
        return """STATUS BAR
==========

Bottom edge of window showing current operation status.

DISPLAYED INFORMATION
---------------------
Left side: Operation status messages
• "Downloading events..." during OWC retrieval
• "Downloaded X events" on completion
• "Ready" when idle
• Error messages for failed operations
• "Generating sequence..." during file creation
• "Night mode enabled/disabled" on theme toggle

Right side: Event count
• Total number of displayed events
• Updates with filters and downloads

TYPICAL MESSAGES
----------------
• "Downloading events from OW Cloud..."
• "Downloaded 15 events"
• "Loaded event for preparation: [name]"
• "Generating sequence for [name]..."
• "Night mode enabled"

Provides immediate feedback for all operations."""

    def get_downloading_events_content(self):
        return """DOWNLOADING EVENTS
==================

Retrieve assigned events from OccultWatcher Cloud.

PROCESS
-------
Click Download button:
1. Connects to OWC using configured credentials
2. Retrieves all events assigned to your stations
3. Calculates exposure times from star magnitudes
4. Calculates recording durations with uncertainty buffers
5. Saves to occultations_latest.json
6. Merges with occultations.json master file
7. Updates events grid display

DOWNLOADED DATA
---------------
• Event timing and coordinates (RA/Dec)
• Star and asteroid magnitudes
• Duration and uncertainty values
• Altitude and azimuth at event time
• OWC event page links

AUTOMATIC CALCULATIONS
----------------------
Exposure calculation:
• Based on star magnitude and reference from Configuration
• Formula: 40ms * 2.5^(star_mag - ref_mag)

Recording duration:
• max_duration + (2 * time_error) + base_duration

GOTO timing:
• event_time - goto_lead_time from Configuration

FILE MANAGEMENT
---------------
• occultations.json: Master database
• occultations_latest.json: Most recent download
• Custom exposures preserved during merge
• Events older than the configured retention period automatically removed

Download frequency: Daily or when new assignments appear in OWC."""

    def get_editing_exposures_content(self):
        return """EDIT SETTINGS
=============

Modify camera exposure, gain, and recording duration for specific events.

ACCESS
------
• Double-click Exposure column in events grid, OR
• Double-click Gain column in events grid, OR
• Double-click Recording Time column in events grid, OR
• Select event and click Edit Settings button, OR
• Events menu → Edit Settings

EDIT SETTINGS DIALOG
--------------------
Shows current values for all three parameters:
• Current Exposure (Calculated or Custom)
• Current Gain (Default or Custom)
• Current Recording Duration (Calculated or Custom)

EXPOSURE SECTION
----------------
• Text input for manual entry in milliseconds
• Quick-set buttons: 40ms, 60ms, 80ms, 120ms, 160ms, 240ms, 320ms, 480ms
• Range: 1-10000 ms
• Calculated from star magnitude using formula: 40ms * 2.5^(star_mag - ref_mag)

GAIN SECTION
------------
• Text input for manual entry (0-600)
• Quick-set buttons: 200, 300, 400, 450, 500, 550
• Range: 0-600
• Default: 450 (configurable in Tools → Configuration → User Settings)

RECORDING DURATION SECTION
--------------------------
• Text input for manual entry in seconds
• Range: 10-3600 seconds
• Calculated from: Base Duration + Event Duration (if >5s) + 6 * Uncertainty (if >2s)
• Affects GOTO time and recording start/end times

RESET BUTTON
------------
Restores all values to calculated/default:
• Exposure: Recalculates from star magnitude
• Gain: Resets to default from configuration
• Recording Duration: Recalculates from formula

CALCULATED VS CUSTOM
--------------------
Calculated values:
• Automatically determined on download
• Based on formulas and configuration settings

Custom values:
• Manually set by user
• Marked with * in events grid
• Preserved across event downloads
• Override calculated values

SMART DETECTION
---------------
If you set a value that matches the calculated/default value:
• Custom flag is NOT set
• No * indicator appears
• Value treated as calculated/default

WHEN TO CUSTOMIZE
-----------------
Exposure:
• Known camera sensitivity differs from reference
• Specific exposure needed for target star
• Site-specific lighting conditions

Gain:
• Low-light conditions requiring higher sensitivity
• Bright stars needing reduced gain
• Camera-specific optimal gain values

Recording Duration:
• Extended recording for uncertain events
• Reduced duration for well-constrained predictions
• Buffer adjustments for specific circumstances

Custom settings are saved in occultations.json and persist across sessions.

REGENERATE SEQUENCES
--------------------
After changing settings, dialog asks if you want to regenerate the sequence file.
Regeneration ensures the .scs file matches your updated settings."""

    def get_selecting_events_content(self):
        return """SELECTING EVENTS
================

Choosing events for batch operations using checkboxes.

SELECTION METHODS
-----------------
Individual:
• Click checkbox in Selected column

Bulk:
• Select All: Check all visible events
• Select None: Clear all checkboxes
• On/Off toggle: Toggle checkboxes for visible events

SELECTION BEHAVIOR
------------------
• Selections preserved when changing filters
• Hidden filtered events remain selected
• Selection summary shows count in bottom panel
• Row highlighting separate from checkbox state

BATCH OPERATIONS
----------------
Checked events used for:
• Creating sequence files (.scs generation)
• Running automated sequences with timing
• Batch statistics and reporting

WORKFLOW TIPS
-------------
• Apply Station Filter, then Select All for location-specific operations
• Use Quick Filters (Today/Future), then select for time-based operations
• Check selection summary before batch operations
• Clear selections with Select None between different tasks

Selection system supports individual and batch workflows."""

    def get_event_management_content(self):
        return """EVENT MANAGEMENT
================

Organizing and working with occultation events.

DOWNLOAD
--------
Retrieve assigned events from OWC. Events are processed with calculated exposures, recording times, and GOTO timing.

DISPLAY
-------
Events grid shows:
• Sortable columns for all event parameters
• Real-time status updates
• Custom exposure indicators (*)
• OWC links for detailed information

SELECTION
---------
Checkbox selection for batch operations:
• Individual event selection
• Select All/Select None commands
• On/Off toggle for filtered events
• Selections preserved during filtering

FILTERING
---------
• Station Filter: Show specific locations
• Quick Filters: Today/Future/All time ranges
• Column sorting: Click headers
• Combined filters for precise selection

Data management includes automatic exposure calculations, recording duration with buffers, and cleanup of old events."""

    def get_creating_sequences_content(self):
        return """CREATING SEQUENCES
==================

Generate SharpCap .scs files from selected events.

PROCESS
-------
1. Check event checkboxes in grid
2. Click Create Sequences button
3. Select template from dialog
4. Application generates .scs file for each event
5. Files saved to Sequence Path from Configuration

TEMPLATE SELECTION
------------------
Dialog shows:
• Available templates with file information
• Template content preview
• File size and modification date
• Default template if no custom templates exist

FILE GENERATION
---------------
Each event creates one .scs file:
• Filename: YYYYMMDD [Event Name].scs
• Contains SharpCap commands
• Timing, coordinates, and recording parameters
• Ready for manual or automated execution

BATCH PROCESSING
----------------
• Multiple checked events create multiple files
• Progress messages during generation
• Success/failure summary

Template variables replaced with event-specific data during generation."""

    def get_template_selection_content(self):
        return """TEMPLATE SELECTION
==================

Choose templates for sequence generation.

DIALOG
------
Template Selection dialog shows:
• Available templates with filenames
• File size and modification date
• Template content preview pane
• Selection updates preview immediately

TEMPLATE TYPES
--------------
Default Template:
• Built-in template used when no custom files exist
• Provides basic functionality

Custom Templates:
• .txt files in File Folder with "template" in filename
• Fully customizable SharpCap commands
• Variable placeholders for event data

TEMPLATE VARIABLES
------------------
Variables replaced during generation:
{object_name}: Asteroid name
{event_time}: UTC event time
{goto_time}: GOTO start time
{start_time}: Recording start time
{recording_duration}: Recording seconds
{exposure}: Camera exposure time
{ra}, {dec}: Coordinates
{star_mag}, {comb_mag}: Magnitudes
{event_time_local}, {goto_time_local}, {start_time_local}: Local times

CUSTOM TEMPLATES
----------------
To create custom template:
1. Create .txt file in File Folder
2. Include "template" in filename
3. Write SharpCap commands with variable placeholders
4. Test with sample events

Templates allow full customization for specific equipment setups."""

    def get_combined_scripts_content(self):
        return """COMBINED SCRIPTS
================

Single sequence files containing multiple events.

FEATURE NOTE
------------
Combined script generation functionality exists in the code but is not currently exposed in the user interface. Use individual sequence generation instead.

CONCEPT
-------
When available, combined scripts would:
• Merge multiple events into single .scs file
• Order events chronologically
• Provide single-file execution for multiple events
• Filename: YYYYMMDD_[StationName]_Combined_Sequences.scs

CURRENT WORKFLOW
----------------
Generate individual sequences for each event:
1. Check multiple event checkboxes
2. Click Create Sequences
3. Use Run Sequences for automated execution of multiple files

Individual sequences provide same automation with more flexibility."""

    def get_running_sequences_content(self):
        return """RUNNING SEQUENCES
=================

Execute generated sequence files with automated timing.

EXECUTION METHODS
-----------------
Manual:
• Load .scs files directly in SharpCap
• User controls timing and start

Automated:
• Check event checkboxes
• Click Run Sequences button
• Application manages timing automatically

AUTOMATED PROCESS
-----------------
1. Select events with future GOTO times
2. Click Run Sequences
3. Application waits for each event's GOTO time
4. Sequences execute automatically in chronological order
5. Status updates show progress

REQUIREMENTS
------------
• SharpCap running and accessible
• Sequence files exist for selected events (.scs in Sequence Path)
• Events must have future GOTO times
• System remains running until completion

Automated execution provides hands-off operation with precise timing while maintaining manual control option."""

    def get_troubleshooting_content(self):
        return """TROUBLESHOOTING
===============

Solutions for common problems.

EVENT DOWNLOAD ISSUES
---------------------
No events downloaded:
• Check OWC credentials in Configuration
• Verify event assignments exist in OWC
• Confirm internet connection

Authentication errors:
• Verify email confirmed in OWC
• Check API key from OWC User Profile
• Test login on OWC website

SEQUENCE PROBLEMS
-----------------
Empty or invalid sequences:
• Verify template file exists in File Folder
• Check template contains valid SharpCap commands
• Ensure template uses correct variable syntax

Template not found:
• Place .txt file with "template" in name in File Folder
• Check File Folder path in Configuration

SHARPCAP INTEGRATION
--------------------
Cannot connect:
• Ensure SharpCap 4.1+ is running
• Close other applications controlling SharpCap
• Restart both applications

GOTO problems:
• Check mount connected in SharpCap
• Test GOTO manually first
• Verify coordinates are reasonable

FILE ISSUES
-----------
Cannot save files:
• Check folder permissions
• Verify paths in Configuration
• Ensure sufficient disk space

Check Configuration settings first for most issues. Error messages provide specific guidance."""

    def get_event_details_content(self):
        return """EVENT DETAILS
=============

Detailed event information dialog.

ACCESS
------
• Double-click event row in grid, OR
• Select event and click Event Details button, OR
• Events menu → Event Details

DISPLAYED INFORMATION
---------------------
Timing:
• Event date/time (UTC)
• Local time conversion
• GOTO and recording start times
• Recording duration

Coordinates:
• RA/Dec J2000
• Altitude and azimuth at event time

Magnitudes:
• Star magnitude
• Combined magnitude (star + asteroid)
• Magnitude drop during occultation

Parameters:
• Calculated or custom exposure time
• Maximum occultation duration
• Timing uncertainty
• Station name

OWC LINK
--------
Button opens event page in OccultWatcher Cloud for additional details including finder charts and event predictions.

Dialog is read-only. Use Edit Exposure to modify camera exposure."""

    def get_observation_prep_content(self):
        return """OBSERVATION PREPARATION
=======================

Interactive tools in bottom panel for manual telescope and camera setup.

PURPOSE
-------
The Observation Preparation panel provides manual control over setup steps, allowing you to accommodate different mount configurations, test equipment, and verify setup before running automated sequences.

WORKFLOW
--------
1. Select event in events grid
2. Click Load Event button
3. Click Setup to configure SharpCap camera settings
4. Click GOTO & Center to position telescope
5. Click Plate Solve & Label to verify position and mark target star
6. Make adjustments and retry steps as needed

LOAD EVENT
----------
Loads event information into the preparation panel:
• Displays event name, coordinates, timing in panel
• Shows exposure, star magnitude, duration
• Enables the preparation tool buttons (Setup, GOTO, Plate Solve)
• Allows you to manually work through setup and testing
• Coordinates are copied to clipboard for manual GOTO if needed

SETUP BUTTON
------------
Configures SharpCap for the loaded event:
• Sets camera exposure time based on star magnitude
• Copies target coordinates (RA/Dec) to clipboard
• Sets target name in SharpCap (if supported)
• Prepares camera for target acquisition
• Use this before GOTO to ensure camera is ready

GOTO & CENTER BUTTON
--------------------
Positions telescope to target coordinates:
• Sends GOTO command to mount using event RA/Dec
• Syncs mount position first if "Sync Mount with GOTO" is enabled in Configuration
• Waits for mount to complete slew (uses async operation with blocking)
• Adds settling time after slew completes
• Does NOT automatically plate solve or recenter
• Reports completion status

If no mount is connected:
• Prompts for manual GOTO
• Coordinates are already in clipboard from Setup
• Use SharpCap's Push To Assistant or manual telescope positioning

PLATE SOLVE & LABEL BUTTON
---------------------------
Verifies position and marks target star:
• Performs plate solve on current camera frame
• Calculates actual mount position from plate solve
• Compares with target coordinates (tolerance: 0.05 degrees)
• If off by more than 0.05°: Shows position error dialog with option to retry GOTO
• If within tolerance: Labels target star with annotation
• Reports distance from target and verification status

Use this AFTER GOTO to:
• Verify mount is on target
• Check if another GOTO is needed
• Mark the target star for visual confirmation

WHY MANUAL CONTROL?
-------------------
This step-by-step approach accommodates different configurations:
• Permanently aligned mounts vs. nightly alignment
• Varying GOTO accuracy between mount types
• Different polar alignment quality
• Need to test and verify before automated runs
• Ability to make manual corrections between steps

You have full control to:
• Repeat GOTO if first attempt was inaccurate
• Adjust camera settings between steps
• Verify pointing before committing to automated sequence
• Test equipment functionality with a single event

TYPICAL SESSION
---------------
1. Load Event: Select and load test event
2. Setup: Configure camera exposure and target info
3. GOTO & Center: Position telescope (wait for completion)
4. Plate Solve & Label: Verify position
5. If off target: Click GOTO & Center again, then Plate Solve again
6. If on target: Target star is labeled, ready for observation
7. Repeat with different events to test multiple targets

Use these tools to validate your setup before running automated sequences for multiple events."""

    def get_loading_events_content(self):
        return """LOADING EVENTS
==============

Methods for getting event data into the application.

DOWNLOAD EVENTS
---------------
Primary method:
• Click Download button
• Connects to OWC with configured credentials
• Retrieves events assigned to your stations
• Processes and saves data automatically

REFRESH EVENTS
--------------
• Reloads from local occultations.json
• Updates display without network access
• Useful for previously downloaded data

DOWNLOAD PROCESS
----------------
1. Connect to OWC using email/password and API key
2. Download events for assigned stations
3. Calculate exposures from star magnitudes
4. Calculate recording durations with uncertainty buffers
5. Save to occultations_latest.json
6. Merge with occultations.json master file
7. Update events grid

FILE MANAGEMENT
---------------
• occultations.json: Master database
• occultations_latest.json: Most recent download
• Custom exposures preserved
• Events older than the retention period (configurable) removed automatically"""

    def get_goto_centering_content(self):
        return """GOTO & CENTERING
================

Automated telescope positioning via GOTO button.

PROCESS
-------
1. Uses RA/Dec coordinates from loaded event (J2000)
2. Sends GOTO command through SharpCap mount control
3. Waits for mount to complete slew
4. Reports success/failure status

REQUIREMENTS
------------
• Mount connected and active in SharpCap
• Valid coordinates loaded from event
• Mount control responsive
• Event loaded in preparation panel

INTEGRATION
-----------
• Works through SharpCap's mount control interface
• Uses coordinates directly from event data
• Provides starting point for plate solving
• Verify position before recording"""

    def get_plate_solving_content(self):
        return """PLATE SOLVING
=============

Verify telescope pointing accuracy.

PROCESS
-------
1. Click Plate Solve button in preparation panel
2. SharpCap captures current camera image
3. Plate solve engine determines exact pointing
4. Shows target information dialog
5. Verifies coordinates match event target

REQUIREMENTS
------------
• Plate solving configured in SharpCap
• Camera connected and imaging
• Sufficient stars visible in field
• Event loaded in preparation panel

RESULTS
-------
• Exact field center coordinates
• Target position verification
• Pointing accuracy measurement
• Confirmation of setup accuracy

INTEGRATION
-----------
• Uses SharpCap's built-in plate solving
• Works with current camera image
• Provides definitive position verification

Plate solving confirms accurate target positioning before automated recording."""

    def get_advanced_content(self):
        return """ADVANCED FEATURES
=================

Additional capabilities for experienced users.

NIGHT MODE
----------
• Click Night Mode button in toolbar
• Red-tinted interface for night vision preservation
• Theming across all dialogs and windows
• Toggle anytime with immediate effect
• Setting saved and restored

BATCH PROCESSING
----------------
• Select multiple events with checkboxes
• Generate multiple sequences simultaneously
• Filter and select specific subsets
• Automated execution of multiple events

TEMPLATE CUSTOMIZATION
----------------------
• Create custom .txt templates in File Folder
• Include "template" in filename
• Use variable placeholders for event data
• Full control over SharpCap commands

Advanced features provide flexibility for various observation workflows."""

    def get_tonights_events_content(self):
        return """TONIGHT'S EVENTS
================

Quick filtering for current night observations.

QUICK FILTER
------------
Use Today button in Quick Filters group to show events in next 24 hours.

WORKFLOW
--------
1. Click Today button to filter events
2. Review filtered events in grid
3. Check events to observe
4. Click Create Sequences to generate .scs files
5. Use Run Sequences for automated execution

The Today filter provides quick access to imminent events for current observing session."""

    def get_automation_content(self):
        return """AUTOMATION
==========

Automated execution capabilities for occultation observations.

AUTOMATION LEVELS
-----------------
Manual:
• Load .scs sequences in SharpCap manually
• User controls timing and execution

Semi-Automated:
• Generate sequences with Create Sequences
• Load and run manually in SharpCap

Fully Automated:
• Use Run Sequences for automatic timed execution
• Application manages timing coordination

AUTOMATED EXECUTION
-------------------
Run Sequences button:
• Executes checked events automatically
• Waits for each event's GOTO time
• Starts sequences at calculated times
• Background operation with status updates

TIMING AUTOMATION
-----------------
• Automatic GOTO time calculation with lead time
• UTC-based scheduling
• Background execution at scheduled times
• Interface remains responsive

REQUIREMENTS
------------
• SharpCap running and connected
• Sequence files generated
• Events have future GOTO times
• System stable for duration

Automation provides hands-off execution while maintaining manual control options."""

    def get_common_issues_content(self):
        return """COMMON ISSUES
=============

Frequently encountered problems and solutions.

NO EVENTS DOWNLOADED
--------------------
• Check OWC credentials in Configuration
• Verify API key is correct
• Confirm event assignments exist in OWC
• Test login on OWC website

TEMPLATE NOT FOUND
------------------
• Place .txt file with "template" in name in File Folder
• Check File Folder path in Configuration
• Verify template file contains commands
• Use Browse button to confirm folder

EMPTY SEQUENCE FILES
--------------------
• Check template uses correct variable syntax: {variable_name}
• Verify template contains valid SharpCap commands
• Test with different events

CANNOT CONNECT TO SHARPCAP
--------------------------
• Ensure SharpCap 4.1+ is running
• Close other applications controlling SharpCap
• Restart both applications

GOTO NOT WORKING
----------------
• Verify mount connected in SharpCap
• Test GOTO manually in SharpCap first
• Check mount isn't parked
• Ensure mount control is active

EVENTS GRID EMPTY
-----------------
• Click Download to get data from OWC
• Check Station Filter - select "All Stations"
• Use All quick filter
• Verify occultations.json exists in File Folder

SEQUENCES RUN AT WRONG TIMES
----------------------------
• Verify system clock is accurate
• Check GOTO Lead Time in Configuration
• Confirm UTC interpretation
• Check Windows timezone settings

Most issues resolve by checking Configuration settings."""

    def get_error_messages_content(self):
        return """ERROR MESSAGES
==============

Common error messages and solutions.

DOWNLOAD ERRORS
---------------
"HTTP Error: 401 - Unauthorized":
• Check OWC email/password in Configuration
• Verify API key is correct

"HTTP Error: 403 - Forbidden":
• Confirm email verified in OWC
• Check API key permissions

"Connection timed out":
• Check internet connection
• Retry download

FILE ERRORS
-----------
"Access Denied":
• Check folder permissions
• Run application as administrator if needed
• Verify antivirus not blocking

"File not found":
• Check File Folder path in Configuration
• Create missing folders
• Verify occultations.json exists

SHARPCAP ERRORS
---------------
"Mount not connected":
• Connect mount in SharpCap
• Check mount control is active

"Plate solve failed":
• Ensure stars visible
• Check plate solving configured
• Verify solving database installed

"Cannot start sequence":
• Check SharpCap is running
• Verify .scs file has content
• Ensure SharpCap ready to accept commands

Error messages usually indicate specific configuration or connection issues. Check Configuration first."""

    def get_config_problems_content(self):
        return """CONFIGURATION PROBLEMS
======================

Solutions for configuration issues.

CREDENTIAL ISSUES
-----------------
Cannot login to OWC:
• Verify email matches OWC account exactly
• Check password hasn't changed
• Confirm account is active
• Test login on OWC website

API Key problems:
• Get fresh API key from OWC User Profile
• Ensure email verified in OWC
• Check key wasn't truncated when copying

PATH ISSUES
-----------
Folders not found:
• Use Browse buttons to select valid folders
• Ensure folders exist and accessible
• Check folder permissions
• Avoid network paths

File access problems:
• Run as administrator if needed
• Check Windows UAC settings
• Verify antivirus not blocking
• Use local folders

PARAMETER ISSUES
----------------
Recording duration:
• Base Duration typically 30-120 seconds
• GOTO Lead Time should allow mount positioning and plate solving
• Test with conservative values first

Exposure calculation:
• Magnitude reference affects all calculations
• Adjust based on camera sensitivity
• Test with known star magnitudes
• Use custom exposures for critical events"""

    def get_report_generation_content(self):
        return """REPORT GENERATION
==================

Automated Excel report creation with timing data integration.

OVERVIEW
--------
Generates pre-filled Excel reports for IOTA (North America) and RASNZ (Trans-Tasman) formats.
Integrates timing data from AOTA and Tangra light curve analysis.

ACCESS
------
Tools → Generate Report (menu)
Right-click event in grid → Generate Report

WORKFLOW
--------
1. Select report format (North America / Trans-Tasman)
2. Choose telescope and camera from configured equipment
3. Set observation type (Positive / Negative / Unsure)
4. Select folder containing event files
5. Files auto-selected from folder (AOTA, Tangra CSV)
6. Click Generate Report
7. Excel file created in Reports subfolder

FILE ORGANIZATION
-----------------
Organize files by event in dedicated folders:
  event_folder/
    ├── event.aota.xml (or AOTA_Report.txt)
    ├── light_curve.csv
    └── video.ser

Dialog remembers last folder for faster workflow.

REPORT FORMATS
--------------
• North America: IOTA V5.6.12r standard form
• Trans-Tasman: RASNZ V4.1.2.G form

FILENAME FORMAT
---------------
YYYYMMDD_number_name_catalog_star±Observer_Station.xlsx

Example:
20251107_778_Theobalda_Gaia_DR3_12345+Smith_Observatory.xlsx

DATA SOURCES
------------
• Event data: From OWC download
• Observer info: From configuration
• Equipment: Selected telescope/camera
• Timing: AOTA files and Tangra CSV
• Location: From event station data

REPORTS LOCATION
----------------
Saved to: [File Folder]/Reports/
"""

    def get_report_dialog_content(self):
        return """REPORT DIALOG
=============

Streamlined single-dialog interface for report generation.

DIALOG SECTIONS
---------------

1. REPORT FORMAT
   Radio buttons to select:
   • North America (IOTA)
   • Trans-Tasman (RASNZ)
   
   Selection persists between sessions.

2. EQUIPMENT SELECTION
   Dropdowns populated from configuration:
   • Telescope (configured scopes)
   • Camera (configured cameras)
   
   Defaults to active equipment if set.

3. OBSERVATION TYPE
   Result of observation:
   • Positive: Occultation detected (D & R times)
   • Negative: No occultation observed
   • Unsure: Uncertain detection

4. FILE SELECTION
   Three columns for file lists:
   • AOTA XML: .aota.xml files
   • AOTA Report: AOTA_Report.txt files
   • Tangra CSV: .csv light curve files
   
   First file in each column auto-selected.
   Files displayed from current folder.

5. FOLDER SELECTION
   • Button: Select different folder
   • Label: Shows current folder path
   • Remembers last location

6. STATUS
   Displays:
   • Current selections
   • File counts
   • Validation messages
   • Generation success/error

BUTTONS
-------
• Generate Report: Creates Excel file
• Cancel: Close without generating

KEYBOARD
--------
• Enter: Generate Report
• Escape: Cancel
"""

    def get_file_selection_content(self):
        return """FILE SELECTION
==============

Three-column file selection for timing data sources.

COLUMNS
-------

1. AOTA XML
   • Lists: *.aota.xml files
   • Contains: D/R times from AOTA analysis
   • Format: XML with event timing data
   • Optional: Not required for Negative

2. AOTA REPORT  
   • Lists: *AOTA_Report.txt files
   • Contains: D/R times, uncertainties, SNR
   • Format: Plain text report
   • Alternative: Can replace AOTA XML
   • Multi-event: Prompts to select event if multiple

3. TANGRA CSV
   • Lists: *.csv files  
   • Contains: Light curve with timing
   • Format: Tangra CSV export
   • Provides: Start/end times, exposure, camera delay

AUTO-SELECTION
--------------
First file in each column automatically selected when folder opened.
Manual selection available by clicking files.

FILE DISPLAY
------------
• Filename only (not full path)
• Sorted alphabetically
• Updated when folder changes

FOLDER NAVIGATION
-----------------
• "Select Folder" button opens folder browser
• Dialog remembers last folder between sessions
• Parent folder path shown in dialog

FILE REQUIREMENTS
-----------------
Positive/Unsure: AOTA XML OR AOTA Report required
Negative: All files optional

Multiple AOTA sources: Both can be selected for cross-validation.
"""

    def get_aota_files_content(self):
        return """AOTA FILES
===========

Timing data from AOTA (Automated Occultation Timing Analysis).

FILE TYPES
----------

1. AOTA XML (.aota.xml)
   • Standard AOTA output format
   • XML structure with event elements
   • Contains D/R times with uncertainties
   • Single or multiple events per file

2. AOTA REPORT (AOTA_Report.txt)
   • Plain text report format
   • Human-readable timing data
   • Includes SNR (Signal-to-Noise Ratio)
   • Multi-event support with selection dialog

EITHER/OR LOGIC
---------------
You can provide:
• AOTA XML alone
• AOTA Report alone
• Both for cross-validation

Both NOT required - use whichever you have.

TIME COMPARISON
---------------
When both AOTA sources provided:
• Times automatically compared
• Warning if difference > 0.1 seconds
• Dialog shows both time values
• Allows verification of consistency
• AOTA Report takes priority if both present

MULTI-EVENT REPORTS
-------------------
AOTA Reports may contain multiple events:
• Dialog displays event list
• Shows D/R times for each event
• Click to select correct event
• Only selected event data used in report

DATA EXTRACTED
--------------

From AOTA XML:
• Disappearance time (H:M:S)
• Disappearance uncertainty (±seconds)
• Reappearance time (H:M:S)
• Reappearance uncertainty (±seconds)

From AOTA Report (additional):
• All timing data from XML
• Signal-to-Noise Ratio (SNR)
• Average SNR at event locations

REPORT FIELDS POPULATED
-----------------------
• D Hours, Minutes, Seconds
• D Error (±uncertainty)
• R Hours, Minutes, Seconds  
• R Error (±uncertainty)
• SNR (from AOTA Report only)

FILE LOCATION
-------------
Place in same folder as Tangra CSV and video files.
Dialog auto-selects first matching file.

VALIDATION
----------
• Required for Positive observations
• Required for Unsure observations
• Optional for Negative observations
• One of XML or Report must be present (not both required)
"""

    def get_timing_data_content(self):
        return """TIMING DATA
============

Integrated timing from AOTA and Tangra sources.

DATA SOURCES
------------

1. AOTA FILES
   D/R Event Times:
   • Disappearance time (UTC)
   • Reappearance time (UTC)
   • Uncertainties (±seconds)
   • Signal-to-Noise Ratio

2. TANGRA CSV
   Observation Times:
   • Recording start time
   • Recording end time
   • Frame exposure time
   • Camera acquisition delay

TANGRA CSV FORMAT
-----------------
Standard Tangra light curve export:
• Header with measurement parameters
• Acquisition delay in rows 7-8
• Light curve data with timestamps
• Frame time deltas for exposure calculation

EXTRACTED VALUES
----------------

From Tangra CSV:
• Start Time: First frame timestamp (HH:MM:SS.SS)
• End Time: Last frame timestamp (HH:MM:SS.SS)
• Exposure: Median frame delta (seconds, 3 decimals)
• Camera Delay: From measurement parameters (milliseconds → seconds)

From AOTA:
• D Time: Hours, Minutes, Seconds
• D Error: Uncertainty in seconds (1 decimal)
• R Time: Hours, Minutes, Seconds
• R Error: Uncertainty in seconds (1 decimal)
• SNR: Average signal-to-noise ratio (1 decimal)

REPORT PLACEHOLDERS
-------------------
Auto-populated in Excel templates:

Observation Times:
• {{STARTED_OBSERVING_HOURS}}
• {{STARTED_OBSERVING_MINUTES}}
• {{STARTED_OBSERVING_SECONDS}}
• {{STOPPED_OBSERVING_HOURS}}
• {{STOPPED_OBSERVING_MINUTES}}
• {{STOPPED_OBSERVING_SECONDS}}

Event Times:
• {{AOTA_D_HOURS}}
• {{AOTA_D_MINUTES}}
• {{AOTA_D_SECONDS}}
• {{AOTA_D_ERROR}}
• {{AOTA_R_HOURS}}
• {{AOTA_R_MINUTES}}
• {{AOTA_R_SECONDS}}
• {{AOTA_R_ERROR}}

Camera:
• {{INTEGRATION}} (exposure seconds)
• {{INTEGRATION_UNITS}} ("Seconds")
• {{CAMERA_DELAY_CORRECTION}}
• {{CORRECTIONS_APPLIED}} ("yes" when Tangra data present)
• {{SNR}} (from AOTA Report)
• {{OTHER_DETECTOR_RELATED_INFO}} (camera notes)

PRECISION
---------
• Times: Full precision from source files
• Exposure: 3 decimal places (millisecond precision)
• Uncertainties: 1 decimal place
• SNR: 1 decimal place

ERROR HANDLING
--------------
• Missing files: Placeholders remain empty
• Parse errors: Logged to console, graceful degradation
• Invalid values: Type checking with fallbacks
• Missing components: Validated before use
"""

    def get_report_validation_content(self):
        return """REPORT VALIDATION
==================

Automatic validation before report generation.

REQUIRED FIELDS
---------------

All Observation Types:
• Report format selected
• Telescope selected
• Camera selected
• Observation type selected

Positive Observations:
• AOTA XML OR AOTA Report required
• Cannot generate without timing data

Unsure Observations:
• AOTA XML OR AOTA Report required
• Same as Positive requirement

Negative Observations:
• AOTA files optional (miss report)
• Tangra CSV optional
• Can generate with event data only

FILE VALIDATION
---------------

AOTA Files:
• Must have .aota.xml OR AOTA_Report.txt
• Both allowed for cross-validation
• Parsed for timing data structure
• Multi-event reports require selection

Tangra CSV:
• Must be valid CSV format
• Header with measurement parameters
• Light curve data with timestamps
• Optional but recommended

TIME COMPARISON
---------------
When both AOTA sources present:
• D times compared (tolerance 0.1 seconds)
• R times compared (tolerance 0.1 seconds)
• Warning dialog if times differ
• Shows both time values for verification
• User acknowledges discrepancy
• Report generation continues with AOTA Report data

TOLERANCE
---------
0.1 second tolerance accounts for:
• Rounding differences
• Analysis precision variations
• Display format differences

Differences > 0.1s indicate potential issues.

VALIDATION MESSAGES
-------------------

Errors (prevent generation):
• "Report format not selected"
• "Telescope not selected"
• "Camera not selected"
• "Observation type not selected"
• "AOTA file required for Positive observations"
• "AOTA file required for Unsure observations"

Warnings (allow generation):
• "AOTA times differ by X.X seconds"
• "No Tangra CSV selected (timing data incomplete)"
• "Could not parse AOTA file (check format)"

Success:
• "Report generated: [filename]"
• "Report saved to: [path]"

FILE CHECKS
-----------
• File existence verified
• File read permissions checked
• Parse errors caught and reported
• Template file existence confirmed
• Output folder created if needed
• Output file writable confirmed

POST-GENERATION
---------------
• Excel file created in Reports folder
• Full path displayed in status
• File can be opened immediately
• Dialog remains open for additional reports
"""

    def get_night_mode_content(self):
        return """NIGHT MODE
==========

Red theme for preserving night vision during observations.

ACTIVATION
----------
Click Night Mode button in toolbar to toggle between normal and red themes.

FEATURES
--------
• Red-tinted interface across all windows
• Reduced brightness for night adaptation
• Consistent theming in all dialogs
• Immediate visual change
• Setting persists across sessions

USE CASES
---------
• Nighttime observation sessions
• Preserving dark adaptation
• Reducing eye strain
• Observatory environments

Toggle anytime without affecting functionality."""
  

    
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
Version 1.0

Author: Michael Camilleri

https://github.com/labstercam/occultation-tools


A comprehensive tool for managing asteroid occultation observations using SharpCap.

FEATURES:
• Automated event download from OccultWatcher Cloud
• Interactive observation preparation tools  
• Automated sequence generation and execution
• Excel report generation with timing integration
• AOTA Report and Tangra CSV data import
• Night vision preserving interface
• Station filtering and event management
• Template-based sequence customization

WORKFLOW:
Download → Filter → Prepare → Generate → Execute → Report

This tool streamlines the entire occultation observation process from planning through automated execution, helping observers maximize their success rate while minimizing manual intervention during critical observation periods.

For complete documentation, use Help → User Guide.

Licensed under the BSD 3-Clause License

Copyright (c) 2025, Michael Camilleri

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