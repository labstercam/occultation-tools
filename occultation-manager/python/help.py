import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Point, Size, Font, FontStyle
from System.Windows.Forms import *
from theme import apply_theme_to_control

class HelpDialog(Form):
    """Interactive help dialog for the Occultation Manager"""
    
    def __init__(self, theme_manager):
        Form.__init__(self)
        self.theme_manager = theme_manager
        self.setup_ui()
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup the help dialog UI"""
        self.Text = "Occultation Manager - Help & User Guide"
        self.Size = Size(900, 700)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = FormBorderStyle.Sizable
        self.MaximizeBox = True
        self.MinimizeBox = True
        
        # Create main split container
        main_split = SplitContainer()
        main_split.Dock = DockStyle.Fill
        main_split.SplitterDistance = 200
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
        btn_close.Height = 30
        self.Controls.Add(btn_close)
        
        self.AcceptButton = btn_close
    
    def setup_help_topics(self, panel):
        """Setup the help topics tree view"""
        lbl_topics = Label()
        lbl_topics.Text = "Help Topics:"
        lbl_topics.Dock = DockStyle.Top
        lbl_topics.Height = 25
        lbl_topics.Font = Font("Microsoft Sans Serif", 9, FontStyle.Bold)
        panel.Controls.Add(lbl_topics)
        
        self.tree_topics = TreeView()
        self.tree_topics.Dock = DockStyle.Fill
        self.tree_topics.AfterSelect += self.topic_selected
        panel.Controls.Add(self.tree_topics)
        
        # Populate help topics
        self.populate_help_topics()
    
    def setup_help_content(self, panel):
        """Setup the help content display"""
        self.txt_help_content = TextBox()
        self.txt_help_content.Multiline = True
        self.txt_help_content.ReadOnly = True
        self.txt_help_content.ScrollBars = ScrollBars.Vertical
        self.txt_help_content.WordWrap = True
        self.txt_help_content.Font = Font("Microsoft Sans Serif", 10)
        self.txt_help_content.Dock = DockStyle.Fill
        panel.Controls.Add(self.txt_help_content)
    
    def populate_help_topics(self):
        """Populate the help topics tree"""
        # Overview
        overview_node = TreeNode("Overview")
        overview_node.Tag = "overview"
        self.tree_topics.Nodes.Add(overview_node)
        
        # Getting Started
        getting_started = TreeNode("Getting Started")
        getting_started.Tag = "getting_started"
        getting_started.Nodes.Add(TreeNode("Initial Setup")).Tag = "initial_setup"
        getting_started.Nodes.Add(TreeNode("Configuration")).Tag = "configuration"
        getting_started.Nodes.Add(TreeNode("First Use")).Tag = "first_use"
        self.tree_topics.Nodes.Add(getting_started)
        
        # Main Interface
        main_interface = TreeNode("Main Interface")
        main_interface.Tag = "main_interface"
        main_interface.Nodes.Add(TreeNode("Menu Bar")).Tag = "menu_bar"
        main_interface.Nodes.Add(TreeNode("Toolbar")).Tag = "toolbar"
        main_interface.Nodes.Add(TreeNode("Events Grid")).Tag = "events_grid"
        main_interface.Nodes.Add(TreeNode("Station Filter")).Tag = "station_filter"
        main_interface.Nodes.Add(TreeNode("Bottom Panel")).Tag = "bottom_panel"
        main_interface.Nodes.Add(TreeNode("Status Bar")).Tag = "status_bar"
        self.tree_topics.Nodes.Add(main_interface)
        
        # Event Management
        event_mgmt = TreeNode("Event Management")
        event_mgmt.Tag = "event_management"
        event_mgmt.Nodes.Add(TreeNode("Downloading Events")).Tag = "downloading_events"
        event_mgmt.Nodes.Add(TreeNode("Viewing Event Details")).Tag = "event_details"
        event_mgmt.Nodes.Add(TreeNode("Editing Exposures")).Tag = "editing_exposures"
        event_mgmt.Nodes.Add(TreeNode("Selecting Events")).Tag = "selecting_events"
        self.tree_topics.Nodes.Add(event_mgmt)
        
        # Sequence Generation
        sequences = TreeNode("Sequence Generation")
        sequences.Tag = "sequences"
        sequences.Nodes.Add(TreeNode("Creating Sequences")).Tag = "creating_sequences"
        sequences.Nodes.Add(TreeNode("Template Selection")).Tag = "template_selection"
        sequences.Nodes.Add(TreeNode("Combined Scripts")).Tag = "combined_scripts"
        sequences.Nodes.Add(TreeNode("Running Sequences")).Tag = "running_sequences"
        self.tree_topics.Nodes.Add(sequences)
        
        # Observation Preparation
        obs_prep = TreeNode("Observation Preparation")
        obs_prep.Tag = "observation_prep"
        obs_prep.Nodes.Add(TreeNode("Loading Events")).Tag = "loading_events"
        obs_prep.Nodes.Add(TreeNode("GOTO & Centering")).Tag = "goto_centering"
        obs_prep.Nodes.Add(TreeNode("Plate Solving")).Tag = "plate_solving"
        self.tree_topics.Nodes.Add(obs_prep)
        
        # Advanced Features
        advanced = TreeNode("Advanced Features")
        advanced.Tag = "advanced"
        advanced.Nodes.Add(TreeNode("Night Mode")).Tag = "night_mode"
        advanced.Nodes.Add(TreeNode("Tonight's Events")).Tag = "tonights_events"
        advanced.Nodes.Add(TreeNode("Automation")).Tag = "automation"
        self.tree_topics.Nodes.Add(advanced)
        
        # Troubleshooting
        troubleshooting = TreeNode("Troubleshooting")
        troubleshooting.Tag = "troubleshooting"
        troubleshooting.Nodes.Add(TreeNode("Common Issues")).Tag = "common_issues"
        troubleshooting.Nodes.Add(TreeNode("Error Messages")).Tag = "error_messages"
        troubleshooting.Nodes.Add(TreeNode("Configuration Problems")).Tag = "config_problems"
        self.tree_topics.Nodes.Add(troubleshooting)
        
        # Expand top-level nodes
        for node in self.tree_topics.Nodes:
            node.Expand()
        
        # Select overview by default
        self.tree_topics.SelectedNode = overview_node
    
    def topic_selected(self, sender, e):
        """Handle topic selection"""
        if e.Node and e.Node.Tag:
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
            "overview": self.get_overview_content(),
            "getting_started": self.get_getting_started_content(),
            "initial_setup": self.get_initial_setup_content(),
            "configuration": self.get_configuration_content(),
            "first_use": self.get_first_use_content(),
            "main_interface": self.get_main_interface_content(),
            "menu_bar": self.get_menu_bar_content(),
            "toolbar": self.get_toolbar_content(),
            "events_grid": self.get_events_grid_content(),
            "station_filter": self.get_station_filter_content(),
            "bottom_panel": self.get_bottom_panel_content(),
            "status_bar": self.get_status_bar_content(),
            "event_management": self.get_event_management_content(),
            "downloading_events": self.get_downloading_events_content(),
            "event_details": self.get_event_details_content(),
            "editing_exposures": self.get_editing_exposures_content(),
            "selecting_events": self.get_selecting_events_content(),
            "sequences": self.get_sequences_content(),
            "creating_sequences": self.get_creating_sequences_content(),
            "template_selection": self.get_template_selection_content(),
            "combined_scripts": self.get_combined_scripts_content(),
            "running_sequences": self.get_running_sequences_content(),
            "observation_prep": self.get_observation_prep_content(),
            "loading_events": self.get_loading_events_content(),
            "goto_centering": self.get_goto_centering_content(),
            "plate_solving": self.get_plate_solving_content(),
            "advanced": self.get_advanced_content(),
            "night_mode": self.get_night_mode_content(),
            "tonights_events": self.get_tonights_events_content(),
            "automation": self.get_automation_content(),
            "troubleshooting": self.get_troubleshooting_content(),
            "common_issues": self.get_common_issues_content(),
            "error_messages": self.get_error_messages_content(),
            "config_problems": self.get_config_problems_content()
        }
        
        return content_map.get(topic, "Help content not found for this topic.")
    
    def get_overview_content(self):
        return """OCCULTATION MANAGER FOR SHARPCAP
Author: Michael Camilleri

OVERVIEW
========

The Occultation Manager is a comprehensive tool designed to automate the planning, preparation, and execution of asteroid occultation observations using SharpCap.

PURPOSE
-------
This tool streamlines the entire occultation observation workflow by:
• Automatically downloading occultation events from OccultWatcher Cloud
• Managing and filtering events by station and timing
• Generating automated SharpCap sequences for recording
• Providing interactive observation preparation tools
• Supporting both manual and automated observation workflows

MAIN WORKFLOW
-------------
1. SETUP: Configure your OWC credentials and file paths
2. DOWNLOAD: Retrieve your assigned occultation events from OWC
3. FILTER: View and filter events by station, date, or other criteria
4. PREPARE: Use interactive tools to setup, GOTO, and verify targets
5. GENERATE: Create SharpCap sequence files for automated recording
6. EXECUTE: Run sequences manually or automatically at event times

KEY FEATURES
------------
• Real-time event synchronization with OccultWatcher Cloud
• Enhanced event grid with detailed astronomical data
• Custom exposure calculation and editing
• Interactive observation preparation tools
• Automated sequence generation from templates
• Night vision preserving red theme
• Station-based filtering and organization
• Combined script generation for multiple events
• Tonight's events automation for hands-off operation

The tool is designed to work seamlessly with SharpCap, providing a complete solution for asteroid occultation observers from planning through execution."""

    def get_getting_started_content(self):
        return """GETTING STARTED
===============

Welcome to the Occultation Manager! This section will guide you through the initial setup and first use of the application.

PREREQUISITES
-------------
• SharpCap 4.1 or later installed
• OccultWatcher Cloud account with API access
• Active occultation event assignments in OWC
• Basic familiarity with SharpCap operation

FIRST TIME SETUP CHECKLIST
---------------------------
1. Configure your OWC credentials (email/password)
2. Set up file and sequence paths
3. Configure recording parameters
4. Download your first set of events
5. Test the basic workflow

RECOMMENDED WORKFLOW FOR NEW USERS
-----------------------------------
1. Start with the Configuration dialog (Tools → Configuration)
2. Test downloading a few events first
3. Practice with the observation preparation tools
4. Create a test sequence before your first real observation
5. Use Night Mode during actual observations

The application saves all settings automatically, so you only need to configure it once. Most users can be up and running within 5 minutes of initial setup."""

    def get_initial_setup_content(self):
        return """INITIAL SETUP
=============

STEP 1: OWC CREDENTIALS
-----------------------
You must have valid OccultWatcher Cloud credentials:
• Go to Tools → Configuration → Credentials tab
• Enter your OWC email address
• Enter your OWC password
• Ensure you have event assignments in OWC

STEP 2: API KEY SETUP
---------------------
• Log into https://cloud.occultwatcher.net
• Go to User Profile → User Permissions
• Verify your email address if not already done
• Copy your API key
• Paste it in Tools → Configuration → API Settings tab

STEP 3: FILE PATHS
------------------
Configure where files will be stored:
• File Folder: Where event data is stored (default: Documents/SharpCap)
• Sequence Path: Where .seq files are generated (usually same as above)
• These folders will be created automatically if they don't exist

STEP 4: RECORDING PARAMETERS
----------------------------
Set your recording preferences:
• Base Duration: Minimum recording time (default: 60 seconds)
• GOTO Lead Time: How early to start GOTO (default: 240 seconds)
• Magnitude Reference: Star magnitude for 40ms exposure (default: 12.0)

STEP 5: TEMPLATE FILES
----------------------
Place your SharpCap sequence template in the File Folder:
• Name it with "template" in the filename
• Use .txt extension
• Include placeholder variables like {object_name}, {exposure}, etc.

VERIFICATION
------------
Test your setup by:
1. Clicking "Download Events" - should retrieve your OWC events
2. Selecting an event and viewing details
3. Creating a test sequence file
4. Checking that files appear in your configured folders"""

    def get_configuration_content(self):
        return """CONFIGURATION
=============

Access the configuration dialog via Tools → Configuration or by clicking the configuration button.

CREDENTIALS TAB
---------------
OWC Email: Your OccultWatcher Cloud login email
OWC Password: Your OWC account password
• These are stored locally and used for API authentication
• Must match your active OWC account exactly

FILE PATHS TAB
--------------
File Folder: Primary storage location for:
• occultations.json (master event list)
• occultations_latest.json (latest download)
• Template files
• Configuration file

Sequence Path: Where generated .seq files are saved
• Can be same as File Folder
• Should be accessible to SharpCap
• Will be created automatically if it doesn't exist

Occultations File: Master event database filename
Latest File: Temporary download filename

RECORDING TAB
-------------
Base Duration: Minimum recording time in seconds
• Added to calculated event duration
• Accounts for timing uncertainties
• Typical range: 30-120 seconds

GOTO Lead Time: Seconds before recording to start GOTO
• Allows time for mount movement and settling
• Should account for your mount's slew speed
• Typical range: 120-300 seconds

Magnitude for 40ms Exposure: Reference star magnitude
• Used for automatic exposure calculation
• Adjust based on your camera sensitivity
• Typical range: 11.0-13.0

API SETTINGS TAB
----------------
API Host: OWC server URL (normally don't change)
API Key: Your personal OWC API key
• Get from OWC User Profile → User Permissions
• Must verify email address first
• Keep this key secure

SAVING SETTINGS
---------------
• Click Save to store all changes
• Settings are automatically validated
• Invalid settings will show error messages
• Use Reset to Defaults to restore original values"""

    def get_first_use_content(self):
        return """FIRST USE
=========

STEP 1: DOWNLOAD YOUR EVENTS
-----------------------------
• Click "Download Events" button or use File → Download Events
• This retrieves all your assigned events from OWC
• Events are automatically filtered to show only your stations
• Download may take 10-30 seconds depending on number of events

STEP 2: EXPLORE THE EVENT LIST
------------------------------
• Events appear in the main grid with key information
• Each row shows: event name, date/time, magnitudes, exposure, etc.
• Click column headers to sort by different criteria
• Use the Station Filter to show only specific observing sites

STEP 3: VIEW EVENT DETAILS
---------------------------
• Select an event and click "Event Details" or double-click
• Review all astronomical and timing information
• Check coordinates, magnitudes, and uncertainty values
• Note the OWC link for web-based event information

STEP 4: TEST OBSERVATION PREPARATION
-------------------------------------
• Select an event and use the Observation Preparation panel
• Click "Load Event" to load it for preparation
• Try the "Setup for Event" to configure SharpCap parameters
• Use "Event Details" to see all technical information

STEP 5: CREATE YOUR FIRST SEQUENCE
-----------------------------------
• Select one or more events
• Click "Create Sequences"
• Choose a template (or use the default)
• Check that .seq files are created in your sequence folder
• Open a .seq file in a text editor to see the generated commands

STEP 6: VERIFY EVERYTHING WORKS
--------------------------------
• Check that all files are in the expected locations
• Verify sequence files contain correct parameters
• Test loading a sequence file in SharpCap
• Make sure GOTO coordinates match the event data

COMMON FIRST-TIME ISSUES
-------------------------
• No events downloaded: Check OWC credentials and assignments
• Empty sequence files: Verify template file exists and has correct format
• File path errors: Ensure folders exist and are writable
• API errors: Verify email is confirmed and API key is correct"""

    def get_main_interface_content(self):
        return """MAIN INTERFACE
==============

The main window is organized into five key areas for efficient workflow management.

LAYOUT OVERVIEW
---------------
1. Menu Bar (top): Access to all major functions
2. Toolbar (below menu): Quick access to common operations
3. Station Filter (below toolbar): Filter events by observing station
4. Events Grid (center): Main event display and selection
5. Bottom Panel: Configuration, preparation tools, and filters
6. Status Bar (bottom): Current status and event count

WORKFLOW ORGANIZATION
---------------------
The interface follows a logical top-to-bottom workflow:
• Download and manage events (top controls)
• Filter and select events (middle area)
• Prepare and configure observations (bottom area)
• Monitor status and progress (status bar)

KEY INTERACTION AREAS
---------------------
Selection Area: Events grid with checkboxes for selecting events
Action Area: Toolbar buttons for performing operations on selected events
Configuration Area: Bottom panel for paths and settings
Information Area: Status bar and selection summary

RESPONSIVE DESIGN
-----------------
• All panels resize appropriately when window is resized
• Events grid expands to show more events as needed
• Bottom panel remains accessible but compact
• Status information always visible

KEYBOARD SHORTCUTS
------------------
• ESC: Close dialogs
• Enter: Accept dialog selections
• F1: Show this help (when implemented in menu)
• Ctrl+A: Select all events
• Del: Deselect events

The interface is designed for both quick single-event operations and batch processing of multiple events."""

    def get_menu_bar_content(self):
        return """MENU BAR
========

FILE MENU
---------
Download Events: Retrieve latest events from OWC
Refresh Events: Reload events from local files
Download & Run Tonight's Events: Automated workflow for current night
Exit: Close the application

EVENTS MENU
-----------
Event Details: Show detailed information for selected event
Edit Exposure: Modify exposure time for selected event
Select All: Mark all visible events as selected
Select None: Clear all event selections

SEQUENCES MENU
--------------
Create Sequences: Generate .seq files for selected events
Generate Combined Script: Create single sequence file with all selected events
Run Selected Sequences: Execute sequences in SharpCap (automated mode)

TOOLS MENU
----------
Configuration: Open settings dialog
Template Manager: Select and preview sequence templates

HELP MENU
---------
User Guide: This comprehensive help system
About: Application information and version details

MENU BEHAVIOR
-------------
• Menu items are context-sensitive (enabled/disabled based on selections)
• Keyboard shortcuts are shown where available
• Some operations require event selection to be enabled
• Configuration and help are always available

QUICK ACCESS
------------
Most frequently used functions are also available in the toolbar for faster access. The menu provides complete access to all features plus some advanced options not shown in the toolbar."""

    def get_toolbar_content(self):
        return """TOOLBAR
=======

The toolbar provides quick access to the most commonly used functions, organized in two rows.

TOP ROW - EVENT MANAGEMENT
---------------------------
Download Events: Get latest events from OWC
Refresh: Reload from local files
Tonight's Events: Automated workflow for current night
Select All: Mark all events as selected
Select None: Clear selections
Event Details: Show detailed event information
Edit Exposure: Modify exposure settings
Test GOTO & Solve: Quick navigation test for selected event
Night Mode: Toggle between day/night display themes

BOTTOM ROW - SEQUENCE OPERATIONS
---------------------------------
Create Sequences: Generate .seq files for selected events
Run Sequences: Execute sequences automatically
Combined Script: Create single multi-event sequence file

BUTTON STATES
-------------
• Disabled (grayed): Function not available (no selection, etc.)
• Enabled: Ready to use
• Some buttons require event selection to be active

WORKFLOW OPTIMIZATION
---------------------
Buttons are arranged in typical workflow order:
1. Download/refresh events (left side)
2. Select and manage events (center)
3. Generate and run sequences (right side)

VISUAL INDICATORS
-----------------
• Night Mode button text changes to reflect current mode
• Status updates appear in the status bar when buttons are clicked
• Some operations show progress indicators

EFFICIENCY TIPS
---------------
• Use keyboard shortcuts where available
• Night Mode is particularly useful during actual observations
• Tonight's Events button automates the entire workflow for current night
• Test GOTO & Solve helps verify setup before critical observations"""

    def get_events_grid_content(self):
        return """EVENTS GRID
===========

The events grid is the heart of the interface, displaying all your occultation events with detailed information.

COLUMNS EXPLAINED
-----------------
Selected: Checkbox to mark events for batch operations
Event Name: Asteroid name and observing station
Station: Your observing station identifier
Date/Time UTC: When the occultation occurs
Star Mag: Brightness of the target star
Comb Mag: Combined magnitude (star + asteroid)
Mag Drop: Expected brightness drop during occultation
Exposure (ms): Calculated or custom exposure time (* indicates custom)
Recording Time (s): Total recording duration
Max Duration (s): Maximum possible occultation duration
Time Error (s): Timing uncertainty
Alt/Az: Target altitude and azimuth at event time
Coordinates: RA/Dec coordinates (J2000)
OWC: Link to view event on OccultWatcher Cloud
Status: Event status (future, past, starting soon, etc.)

INTERACTION METHODS
-------------------
Single Click: Select row
Double Click: Open Event Details dialog
Double Click Exposure: Edit exposure time
Click OWC Link: Open event in web browser
Checkbox: Select/deselect for batch operations
Column Headers: Sort by that column

SELECTION METHODS
-----------------
Individual: Click checkbox for specific events
Range: Select multiple rows and use toolbar buttons
All: Use "Select All" button
None: Use "Select None" button
Filtered: Selections work with filtered views

VISUAL INDICATORS
-----------------
* after exposure: Custom exposure (not calculated)
Past events: Different status indicator
High priority: Events starting soon
Color coding: Varies by theme (day/night mode)

SORTING AND FILTERING
---------------------
• Click any column header to sort by that field
• Use Station Filter to show only specific stations
• Use Quick Filters (Today, Upcoming, All) in bottom panel
• Sort persists through filter changes

EFFICIENCY FEATURES
-------------------
• Grid remembers selections during filtering
• Fast loading for large event lists
• Automatic refresh when events are downloaded
• Real-time status updates"""

    def get_station_filter_content(self):
        return """STATION FILTER
==============

The Station Filter allows you to focus on events for specific observing locations.

LOCATION
--------
• Located just below the toolbar
• Always visible and easily accessible
• Dropdown shows all available stations from your events

HOW IT WORKS
------------
• Dropdown automatically populates with all station names from your events
• "All Stations" shows everything (default)
• Selecting a specific station shows only events for that location
• Filter applies immediately when selection changes
• Event count updates to show filtered results

CLEARING THE FILTER
--------------------
• Select "All Stations" from dropdown, OR
• Click "Clear Filter" button
• Returns to showing all events

INTERACTION WITH SELECTIONS
---------------------------
• Event selections are preserved when filtering
• You can select events from one station, then filter to another
• Batch operations work on currently visible (filtered) events
• Selection summary shows filtered selection counts

PRACTICAL USES
--------------
Multiple Stations: If you have events at different locations
Organization: Focus on events for tonight's observing session
Planning: Review events by geographic location
Verification: Check that all stations have appropriate events

AUTOMATION INTEGRATION
----------------------
• Tonight's Events feature respects current filter
• Sequence generation works with filtered events
• Station-specific workflows are easier to manage

PERFORMANCE
-----------
• Filtering is instant, even with large event lists
• No need to re-download events when changing filters
• Grid updates immediately with filtered results

The Station Filter is particularly useful for observers who participate in occultations from multiple locations or who want to focus on events for a specific observing session."""

    def get_bottom_panel_content(self):
        return """BOTTOM PANEL
============

The bottom panel contains three key areas for configuration, observation preparation, and quick filtering.

CONFIGURATION SECTION
----------------------
Sequence Path: Where generated .seq files are saved
• Text box shows current path
• Browse button to select different folder
• Path is remembered and used for all sequence generation

OBSERVATION PREPARATION SECTION
-------------------------------
This interactive section helps prepare for observations:

Load Event: Select an event from the grid for preparation
Setup for Event: Configure SharpCap with event parameters
GOTO & Center: Execute mount GOTO and verify positioning
Plate Solve & Label: Plate solve and mark target location
Clear Labels: Remove overlay markers

Event Display: Shows currently loaded event details
• Event name, coordinates, timing information
• Exposure settings and recording duration
• Key astronomical parameters

QUICK FILTERS SECTION
----------------------
Today: Show only events occurring today
Upcoming: Show only future events
All: Show all events (clear filters)

SELECTION SUMMARY
-----------------
Shows statistics about currently selected events:
• Number of events selected
• Number of future events (can be run)
• Station information for selections

WORKFLOW INTEGRATION
--------------------
The bottom panel supports different observation workflows:
• Quick Setup: Use filters to find tonight's events
• Preparation: Load and configure individual events  
• Batch Processing: Configure paths for multiple sequences
• Status Monitoring: Track selections and progress

PREPARATION WORKFLOW
--------------------
1. Select event in main grid
2. Click "Load Event" to load for preparation
3. Use "Setup for Event" to configure SharpCap
4. Use "GOTO & Center" for telescope positioning
5. Use "Plate Solve & Label" to verify target
6. Proceed with manual or automated recording

The preparation tools are designed for interactive use during observation sessions, while the filters and configuration support both planning and automated operations."""

    def get_status_bar_content(self):
        return """STATUS BAR
==========

The status bar at the bottom of the window provides real-time feedback about application operations and current state.

INFORMATION DISPLAYED
---------------------
Left Side - Current Status:
• Operation in progress (e.g., "Downloading events...")
• Completion messages (e.g., "Downloaded 15 events")
• Error messages (e.g., "Failed to connect to OWC")
• Ready state when no operation is active

Right Side - Event Count:
• Total number of events currently displayed
• Updates when filtering or downloading new events
• Reflects current filter state, not total events

STATUS MESSAGES
---------------
Download Operations:
• "Downloading events from OW Cloud..."
• "Downloaded X events" (success)
• "No events downloaded" or "Error downloading events" (failure)

File Operations:
• "Loading events..."
• "Events loaded successfully"
• "Generating sequence for [event name]..."
• "Sequence generated successfully"

Preparation Operations:
• "Loaded event for preparation: [event name]"
• "Setting up SharpCap for [event name]..."
• "GOTO/Platesolve started for [event name]"

Configuration Changes:
• "Night mode enabled/disabled"
• "Configuration saved successfully"

REAL-TIME UPDATES
-----------------
• Status updates immediately when operations begin
• Progress is shown for multi-step operations
• Error messages appear immediately when problems occur
• Success confirmations appear when operations complete

MONITORING LONG OPERATIONS
--------------------------
For operations that take time (downloading, sequence generation):
• Status shows operation in progress
• Additional details may appear for batch operations
• Final status shows completion or error state

The status bar is your primary feedback mechanism for understanding what the application is doing and whether operations completed successfully."""

    def get_downloading_events_content(self):
        return """DOWNLOADING EVENTS
==================

AUTOMATIC DOWNLOAD
------------------
Click "Download Events" button or use File → Download Events menu.

The download process:
1. Connects to OccultWatcher Cloud using your credentials
2. Retrieves all events assigned to your stations
3. Processes event data and calculates recording parameters
4. Saves events to local files for offline access
5. Merges with existing events, keeping recent data

WHAT GETS DOWNLOADED
--------------------
• All events assigned to your OWC stations
• Events within the configured retention period (14 days)
• Complete astronomical and timing data
• Station-specific predictions and uncertainties
• Links to detailed OWC event pages

DATA PROCESSING
---------------
During download, the application:
• Calculates optimal exposure times based on star magnitudes
• Determines recording durations including uncertainty buffers
• Computes GOTO times with appropriate lead time
• Processes coordinate and timing information
• Formats data for easy viewing and sequence generation

FILE MANAGEMENT
---------------
Events are saved to two files:
• occultations_latest.json: Most recent download
• occultations.json: Master database with retention management

Old events (>14 days) are automatically removed to keep files manageable.

TROUBLESHOOTING DOWNLOAD ISSUES
-------------------------------
No Events Downloaded:
• Verify OWC credentials in Configuration
• Check that you have event assignments in OWC
• Ensure internet connection is working

Authentication Errors:
• Confirm email and password are correct
• Check API key in Configuration → API Settings
• Verify email address is confirmed in OWC

Connection Problems:
• Check firewall/proxy settings
• Verify OWC service is available
• Try again later if service is temporarily unavailable

DOWNLOAD FREQUENCY
------------------
• Download when events are first assigned
• Re-download if event details change
• Daily downloads recommended during active observing periods
• Events are automatically merged to prevent duplicates"""

def get_event_details_content(self):
        return """EVENT DETAILS
=============

Access event details by selecting an event and clicking "Event Details" or double-clicking any event row.

INFORMATION SECTIONS
--------------------
Event Information:
• Event name (asteroid + station)
• Asteroid designation and proper name
• Target star identification
• Observing station details
• Data source (OWCloud)
• Link to view on OWC website

Timing Information:
• Event time (predicted center time)
• GOTO time (when to start slewing)
• Recording start and end times
• Maximum duration and timing uncertainty
• All times shown in UTC

Recording Settings:
• Calculated or custom exposure time
• Total recording duration
• Pre-calculated exposure from OWC data
• Indication of custom vs. calculated settings

Photometry Information:
• Star magnitude (unoccluded brightness)
• Combined magnitude (star + asteroid)
• Expected magnitude drop during occultation
• Useful for planning recording settings

Position Information:
• Right Ascension and Declination (J2000)
• Altitude and azimuth at event time
• Target coordinates for GOTO operations

Observer Location:
• Station latitude and longitude
• Used for local predictions and timing

Technical Information:
• Internal event identifiers
• OWCloud event ID for reference
• Object catalog number

USING EVENT DETAILS
-------------------
• Review all parameters before observation
• Verify coordinates match your planning
• Check timing uncertainty for recording duration
• Note altitude for observability planning
• Use OWC link for additional event information

The details dialog provides comprehensive information for planning and verification of occultation observations."""

    def get_editing_exposures_content(self):
        return """EDITING EXPOSURES
=================

The application automatically calculates exposure times, but you can customize them for specific events.

ACCESSING EXPOSURE EDITOR
-------------------------
• Select an event and click "Edit Exposure", OR
• Double-click the Exposure column in the events grid

AUTOMATIC CALCULATION
---------------------
Default exposures are calculated based on:
• Target star magnitude
• Your configured reference magnitude
• Camera sensitivity settings
• Typical range: 10ms to 1000ms

CUSTOM EXPOSURE SETTING
-----------------------
The exposure editor provides:
• Current exposure display (calculated or custom)
• Text input for manual entry
• Quick-set buttons for common values (10ms, 20ms, 40ms, etc.)
• Reset button to return to calculated value

EXPOSURE VALIDATION
-------------------
• Values must be between 1ms and 10000ms
• Invalid entries show warning messages
• Dialog stays open until valid value entered
• Changes are applied immediately when OK is clicked

VISUAL INDICATORS
-----------------
• Custom exposures show "*" in the events grid
• Calculated exposures show no indicator
• Custom setting overrides automatic calculation
• Reset returns to automatic calculation

PRACTICAL CONSIDERATIONS
------------------------
Shorter Exposures (10-40ms):
• Bright stars (magnitude < 10)
• Fast-moving targets
• Reduced noise at cost of photon collection

Longer Exposures (100-1000ms):
• Faint stars (magnitude > 12)
• Better photon collection
• Risk of trailing or saturation

SEQUENCE REGENERATION
---------------------
After changing exposure:
• Application offers to regenerate sequence file
• New exposure is used in updated sequence
• Previous sequence file is overwritten
• Custom exposure is preserved for future use

WORKFLOW TIPS
-------------
• Test different exposures with your camera first
• Consider star magnitude and local conditions
• Shorter exposures reduce timing uncertainty
• Custom exposures are remembered across sessions"""

    def get_selecting_events_content(self):
        return """SELECTING EVENTS
================

Event selection is used for batch operations like sequence generation and automated execution.

SELECTION METHODS
-----------------
Individual Selection:
• Click checkbox in "Selected" column for specific events
• Checkbox toggles selection state

Bulk Selection:
• "Select All" button: Marks all visible events
• "Select None" button: Clears all selections
• Selections respect current filter settings

Grid-Based Selection:
• Click row to highlight (different from selection)
• Highlighting is for single-event operations
• Selection checkboxes are for batch operations

SELECTION BEHAVIOR
------------------
Persistent Across Filters:
• Selections remain when changing station filters
• Hidden events stay selected but don't appear in operations
• Clearing filter shows all selections again

Visual Feedback:
• Checked boxes indicate selected events
• Selection summary in bottom panel shows counts
• Status updates reflect selected event operations

PRACTICAL WORKFLOW
------------------
Station-Specific Selection:
1. Apply station filter to show desired events
2. Use "Select All" to mark all events for that station
3. Perform batch operations on selected events

Time-Based Selection:
1. Use "Today" or "Upcoming" filters
2. Manually select specific events from filtered view
3. Generate sequences for selected timeframe

Quality-Based Selection:
• Review event details before selection
• Select only events with good observing conditions
• Consider timing conflicts when selecting multiple events

BATCH OPERATIONS
----------------
Selected events are used for:
• Creating multiple sequence files
• Generating combined scripts
• Running automated sequences
• Statistical summaries and reporting

SELECTION TIPS
--------------
• Select before filtering for broad operations
• Filter then select for targeted operations
• Check selection summary before batch operations
• Clear selections to start fresh workflow
• Use station filter to organize selections by location

The selection system is designed to support both quick single-event workflows and complex multi-event batch processing."""

    def get_creating_sequences_content(self):
        return """CREATING SEQUENCES
==================

Sequence generation creates SharpCap .seq files for automated occultation recording.

SEQUENCE CREATION PROCESS
-------------------------
1. Select events using checkboxes in the events grid
2. Click "Create Sequences" button
3. Choose a template from the Template Selection dialog
4. Application generates .seq files for each selected event
5. Files are saved to your configured Sequence Path

TEMPLATE SYSTEM
---------------
Templates contain SharpCap commands with placeholder variables:
• {object_name}: Asteroid name
• {event_time}: Occultation time (UTC)
• {start_time}: Recording start time
• {goto_time}: GOTO start time
• {recording_duration}: Total recording seconds
• {exposure}: Exposure time in seconds
• {ra}, {dec}: Target coordinates
• {star_mag}, {comb_mag}: Brightness values

SEQUENCE FILE NAMING
--------------------
Files are automatically named with format:
YYYYMMDD [Event Name].seq

Examples:
• 20241215 433 Eros - Station ABC.seq
• 20241216 Asteroid 2024AB - Observatory XYZ.seq

GENERATED CONTENT
-----------------
Each sequence file contains:
• Event header with timing and coordinates
• GOTO commands for telescope positioning
• Camera setup with calculated exposure
• Recording start/stop commands timed to event
• Safety delays and error handling

TEMPLATE SELECTION
------------------
Default Template: Uses built-in template if no custom template found
Custom Templates: Choose from available .txt files in your file folder
Template Preview: View template content before selection
Template Variables: Automatically replaced with event data

BATCH PROCESSING
----------------
• Multiple events create multiple sequence files
• Each file is independent and can be run separately
• Progress shown during generation
• Success/failure count reported at completion

TROUBLESHOOTING
---------------
No Template Found:
• Place template file in configured File Folder
• Ensure filename contains "template"
• Use .txt extension
• Check file permissions

Empty Sequences:
• Verify template contains valid SharpCap commands
• Check template variable syntax: {variable_name}
• Ensure template file is not corrupted

File Creation Errors:
• Check Sequence Path exists and is writable
• Ensure sufficient disk space
• Verify no other application has files open

SEQUENCE TESTING
----------------
• Generate test sequences with sample events
• Open .seq files in text editor to verify content
• Load sequences in SharpCap to test commands
• Verify timing and coordinate accuracy before observations"""

    def get_template_selection_content(self):
        return """TEMPLATE SELECTION
==================

Templates define the SharpCap commands used in generated sequence files.

TEMPLATE DIALOG
---------------
The Template Selection dialog shows:
• List of available templates with file information
• Template preview with full content display
• File size and modification date for each template
• Scrollable preview with proper formatting

TEMPLATE TYPES
--------------
Default Template: Built-in template used when no custom templates exist
Custom Templates: User-created .txt files in the File Folder
• Must contain "template" in filename
• Must use .txt extension
• Should contain valid SharpCap sequence commands

TEMPLATE STRUCTURE
------------------
A typical template includes:
#Occultation sequence for {object_name}
#Event time: {event_time} UTC
GOTO {ra} {dec}
WAIT UNTIL {goto_time_local}
SET EXPOSURE {exposure}
START RECORDING
WAIT {recording_duration}
STOP RECORDING

TEMPLATE VARIABLES
------------------
Available placeholders that get replaced with event data:
• {object_name}: Asteroid name
• {event_time}: Event center time (UTC)
• {start_time}: Recording start (UTC)  
• {goto_time}: GOTO start time (UTC)
• {event_time_local}: Event time (local HH:MM:SS)
• {start_time_local}: Start time (local HH:MM:SS)
• {goto_time_local}: GOTO time (local HH:MM:SS)
• {recording_duration}: Recording seconds
• {exposure}: Exposure time in seconds
• {ra}: Right Ascension (hours)
• {dec}: Declination (degrees)
• {star_mag}: Star magnitude
• {comb_mag}: Combined magnitude
• {mag_drop}: Magnitude drop

CREATING CUSTOM TEMPLATES
--------------------------
1. Create new .txt file in your File Folder
2. Name it with "template" in the filename
3. Write SharpCap commands using template variables
4. Test with sample sequence generation
5. Refine based on your specific needs

TEMPLATE PREVIEW
----------------
• Shows complete template content
• Uses monospace font for proper formatting
• Supports horizontal and vertical scrolling
• Updates immediately when selection changes

BEST PRACTICES
--------------
• Start with the default template and modify
• Include comments for clarity
• Test templates with non-critical events first
• Keep backup copies of working templates
• Document any custom variables or special commands

TEMPLATE MANAGEMENT
-------------------
• Templates are automatically detected in File Folder
• Refresh by reopening Template Selection dialog
• File information helps identify most recent versions
• Preview helps verify template content before use"""

    def get_combined_scripts_content(self):
        return """COMBINED SCRIPTS
================

Combined scripts merge multiple events into a single sequence file for automated multi-event sessions.

PURPOSE
-------
Instead of individual .seq files for each event, create one file containing:
• All selected events in chronological order
• Automatic transitions between events
• Complete timing coordination
• Simplified execution workflow

WHEN TO USE COMBINED SCRIPTS
----------------------------
• Multiple events in one observing session
• Automated all-night observations
• Events from the same observing station
• When manual intervention between events isn't needed

CREATION PROCESS
----------------
1. Select multiple events (same station recommended)
2. Click "Combined Script" button
3. Choose template for sequence generation
4. Application creates single .seq file with all events

COMBINED FILE STRUCTURE
-----------------------
• Header with event summary and schedule
• Individual event sections with separators
• Chronological ordering by GOTO time
• Complete timing coordination between events
• Comments identifying each event section

FILE NAMING
-----------
Format: YYYYMMDD_[StationName]_Combined_Sequences.seq

Examples:
• 20241215_StationABC_Combined_Sequences.seq
• 20241216_MultiStation_Combined_Sequences.seq

MULTI-STATION HANDLING
----------------------
If events from different stations are selected:
• Warning dialog asks for confirmation
• File created but may need manual coordination
• Consider separate combined files per station

TIMING COORDINATION
-------------------
• Events ordered by GOTO time (earliest first)
• Automatic gaps calculated between events
• No overlap protection (user responsibility)
• Each event section clearly marked with timing

CONTENT ORGANIZATION
--------------------
File Header:
• Generation timestamp
• Total number of events
• Station information
• Complete event schedule

Event Sections:
• Event identification and timing
• Complete sequence commands from template
• Separator lines between events
• Error handling for each event

EXECUTION BENEFITS
------------------
• Single file to load in SharpCap
• Automatic progression through events
• Reduced manual intervention
• Complete audit trail in one file

LIMITATIONS
-----------
• All events must use same template
• No dynamic adjustments during execution
• Station coordination required for multi-station files
• Limited error recovery between events

BEST PRACTICES
--------------
• Use for same-station events when possible
• Review combined file before critical observations
• Test with non-critical events first
• Keep individual sequences as backup
• Monitor execution for any timing issues"""

    def get_running_sequences_content(self):
        return """RUNNING SEQUENCES
=================

The application can automatically execute SharpCap sequences at the appropriate times.

SEQUENCE EXECUTION MODES
-------------------------
Manual Execution:
• Load .seq files directly in SharpCap
• Start sequences manually at appropriate times
• Full control over timing and execution

Automated Execution:
• Click "Run Sequences" for selected events
• Application manages timing and execution
• Sequences start automatically at GOTO times

AUTOMATED EXECUTION PROCESS
---------------------------
1. Select events with future GOTO times
2. Click "Run Sequences" button
3. Confirm execution dialog
4. Application waits for each event's GOTO time
5. Sequences execute automatically in chronological order

TIMING MANAGEMENT
-----------------
• Only future events can be executed automatically
• Events sorted by GOTO time
• Each sequence starts at its scheduled GOTO time
• Past events are skipped with notification

EXECUTION MONITORING
--------------------
• Status updates show current operation
• Progress through multiple events displayed
• Individual sequence success/failure reported
• Background execution doesn't block interface

REQUIREMENTS FOR AUTOMATION
----------------------------
• SharpCap must be running and accessible
• Sequence files must exist for selected events
• Events must have future GOTO times
• System must remain running until completion

ERROR HANDLING
--------------
• Failed sequences reported but don't stop others
• Individual event errors logged
• Execution continues with remaining events
• Complete status summary at finish

SAFETY CONSIDERATIONS
---------------------
• Test automated execution with non-critical events
• Monitor first few automated runs
• Ensure system stability for long sessions
• Have manual backup plans ready

TONIGHT'S EVENTS AUTOMATION
---------------------------
Special "Tonight's Events" button provides complete automation:
1. Downloads latest events from OWC
2. Filters events for next 24 hours
3. Creates sequences for tonight's events
4. Immediately starts automated execution
5. Hands-off operation for entire night

THREADING AND PERFORMANCE
-------------------------
• Sequence execution runs in background threads
• SharpCap interface remains responsive
• Status updates are thread-safe
• Multiple sequences can be queued safely

STOPPING EXECUTION
------------------
• Close application to stop waiting sequences
• Individual sequences continue once started
• Use SharpCap controls to stop active sequences
• Status shows if execution was interrupted

BEST PRACTICES
--------------
• Test automation with sample events first
• Verify all sequences before automated runs
• Monitor system during first automated sessions
• Keep manual controls available as backup
• Review execution logs after sessions"""

    def get_observation_prep_content(self):
        return """OBSERVATION PREPARATION
=======================

The Observation Preparation panel provides interactive tools for setting up and testing occultation observations.

PREPARATION WORKFLOW
--------------------
1. Select event in main grid
2. Load event for preparation
3. Setup SharpCap parameters
4. Execute GOTO and centering
5. Verify target with plate solving
6. Proceed with observation

LOADING EVENTS FOR PREPARATION
-------------------------------
Load Event Button:
• Takes the first selected event from the main grid
• Loads complete event data for interactive preparation
• Displays event details in preparation panel
• Enables all preparation tools

Event Information Display:
• Event name and timing
• Target coordinates
• Exposure and duration settings
• Key astronomical parameters

PREPARATION TOOLS
-----------------
Setup for Event:
• Configures SharpCap camera settings
• Sets exposure time from event data
• Applies target information
• Prepares interface for observation

GOTO & Center:
• Executes telescope GOTO to target coordinates
• Waits for mount settling
• Performs basic position verification
• Reports success/failure status

Plate Solve & Label:
• Initiates plate solving process
• Verifies target is in field of view
• Provides coordinate confirmation
• Shows target information dialog

Clear Labels:
• Removes any overlay markers
• Cleans up display elements
• Resets view for fresh preparation

INTEGRATION WITH SHARPCAP
-------------------------
The preparation tools work directly with SharpCap:
• Camera control integration
• Mount control for GOTO operations
• Plate solving interface
• Overlay management

INTERACTIVE SETUP PROCESS
-------------------------
1. Load Event: Get event data ready for preparation
2. Setup: Configure SharpCap with event parameters
3. GOTO: Move telescope to target position
4. Verify: Confirm position with plate solving
5. Record: Use manual or automated recording

ERROR HANDLING
--------------
• Missing event data shows warning messages
• SharpCap connection issues reported
• GOTO failures handled gracefully
• Plate solving errors provide fallback options

PREPARATION vs AUTOMATION
-------------------------
Preparation Tools: Interactive, manual control
• Good for testing and verification
• Allows step-by-step validation
• User maintains full control

Automated Sequences: Hands-off operation
• Good for reliable, tested workflows
• Minimal user intervention required
• Suitable for multiple events

BEST PRACTICES
--------------
• Use preparation tools for unfamiliar events
• Test GOTO accuracy before critical observations
• Verify plate solving works with your setup
• Practice preparation workflow during non-critical times
• Keep manual controls available as backup

The preparation tools bridge the gap between planning and automated execution, providing confidence in your observation setup."""

    def get_night_mode_content(self):
        return """NIGHT MODE
==========

Night Mode provides a red-tinted interface designed to preserve night vision during observations.

ACTIVATING NIGHT MODE
---------------------
• Click "Night Mode" button in toolbar
• Button text changes to "Day Mode" when active
• Setting is automatically saved and restored

VISUAL CHANGES
--------------
Color Scheme:
• Background: Very dark red tones
• Text: Light red/pink for readability
• Controls: Red-tinted buttons and interfaces
• Grids: Dark red backgrounds with light red text

Compatibility:
• Designed to match SharpCap's red theme
• Maintains readability while preserving night vision
• All interface elements consistently themed

NIGHT VISION PRESERVATION
-------------------------
Red light wavelengths:
• Minimize impact on dark-adapted vision
• Allow continued use of telescope eyepieces
• Maintain star visibility with naked eye
• Reduce glare in dark observing environments

WHEN TO USE NIGHT MODE
----------------------
• During all nighttime observations
• In dark sky locations
• When switching between computer and telescope
• For extended observing sessions

INTERFACE BEHAVIOR
------------------
• All dialogs and windows use night theme
• New windows automatically themed
• Theme persists across application restarts
• No functionality changes, only visual appearance

SWITCHING BETWEEN MODES
-----------------------
• Toggle anytime during operation
• Immediate visual change
• No restart required
• Theme preference saved automatically

ASTRONOMY BEST PRACTICES
------------------------
• Activate before going to observing site
• Use during all telescope operations
• Combine with red flashlight for complete setup
• Switch back to day mode for post-observation analysis

TECHNICAL CONSIDERATIONS
-----------------------
• Slightly reduced contrast in some situations
• May affect color perception of star charts
• Screen brightness should still be minimized
• Works with all Windows display settings

COMPLEMENTARY MEASURES
---------------------
For complete night vision preservation:
• Reduce screen brightness to minimum usable level
• Use red filter on any white light sources
• Allow eyes to dark-adapt before observations
• Avoid white light for at least 30 minutes

Night Mode is an essential tool for serious astronomical observations, helping maintain the dark adaptation critical for visual astronomy while providing full access to the application's features."""

    def get_tonights_events_content(self):
        return """TONIGHT'S EVENTS
================

The "Tonight's Events" feature provides complete automation for current-night occultation sessions.

WHAT IT DOES
------------
Single-click automation that:
1. Downloads latest events from OWC
2. Filters events for the next 24 hours
3. Automatically selects tonight's events
4. Creates sequence files for all events
5. Immediately starts automated execution
6. Runs completely hands-off until completion

WHEN TO USE
-----------
• Beginning of observing sessions
• When you want minimal manual intervention
• For reliable, tested observing setups
• When multiple events are scheduled for one night

ACTIVATION PROCESS
------------------
1. Click "Tonight's Events" button
2. Confirm automation dialog
3. Application downloads and processes events
4. Sequences created and execution begins automatically
5. Monitor status for progress updates

AUTOMATIC EVENT FILTERING
-------------------------
Events included if they occur:
• Between now and 24 hours from now
• At your configured stations
• With valid timing and coordinate data
• With future GOTO times

HANDS-OFF OPERATION
-------------------
Once started, the system:
• Waits for each event's GOTO time
• Executes sequences in chronological order
• Continues through all events automatically
• Provides status updates throughout the night
• Completes without user intervention

REQUIREMENTS
------------
Before using Tonight's Events:
• Valid OWC credentials configured
• Template files available
• SharpCap running and responsive
• Mount and camera properly connected
• System stable for extended operation

MONITORING
----------
• Status bar shows current operation
• Event count updates as events are processed
• Execution progress displayed
• Error messages shown if problems occur

SAFETY CONSIDERATIONS
---------------------
• Test with sample events first
• Verify all equipment works properly
• Ensure system won't sleep or shut down
• Have manual backup procedures ready
• Monitor first few automated sessions

RECOVERY FROM ISSUES
--------------------
If problems occur:
• Individual event failures don't stop others
• Application continues with remaining events
• Manual intervention possible at any time
• Sequences can be run manually as backup

CUSTOMIZATION
-------------
Tonight's Events uses:
• Current configuration settings
• Default or selected template files
• Existing station filters
• Standard sequence generation process

TYPICAL WORKFLOW
----------------
Evening Setup:
1. Arrive at observing site
2. Setup telescope and SharpCap
3. Test basic operations
4. Click "Tonight's Events"
5. Monitor first event for verification
6. Allow system to run automatically

POST-OBSERVATION:
• Review generated sequence files
• Check status messages for any issues
• Analyze recorded data as normal
• Note any improvements for future sessions

Tonight's Events is designed for experienced users with tested setups who want to maximize observing efficiency while minimizing manual intervention during critical observation periods."""

    def get_automation_content(self):
        return """AUTOMATION
==========

The Occultation Manager provides several levels of automation to suit different observing workflows and experience levels.

AUTOMATION LEVELS
-----------------
Manual Control:
• User manages all operations
• Step-by-step workflow execution
• Maximum control and flexibility
• Good for learning and testing

Semi-Automated:
• Batch sequence generation
• Manual execution of sequences
• User-controlled timing
• Balance of control and efficiency

Fully Automated:
• Complete hands-off operation
• Automatic timing and execution
• Minimal user intervention
• Maximum efficiency for routine operations

AUTOMATED COMPONENTS
--------------------
Event Management:
• Automatic download from OWC
• Event filtering and organization
• Data validation and processing
• File management and retention

Sequence Generation:
• Batch creation of .seq files
• Template-based customization
• Parameter calculation and formatting
• Error handling and validation

Sequence Execution:
• Automatic timing coordination
• Background execution management
• Status monitoring and reporting
• Error recovery and continuation

TIMING AUTOMATION
-----------------
The system handles:
• GOTO lead time calculations
• Recording start/stop timing
• Event coordination and scheduling
• Timezone and local time conversion

SAFETY FEATURES
---------------
Validation Checks:
• Event data completeness
• Timing reasonableness
• Coordinate validation
• Template syntax verification

Error Recovery:
• Individual event failure isolation
• Automatic retry capabilities
• Manual intervention options
• Comprehensive error reporting

Monitoring:
• Real-time status updates
• Progress tracking
• Performance logging
• Alert notifications

CUSTOMIZATION OPTIONS
---------------------
Users can configure:
• Automation trigger conditions
• Error handling behavior
• Notification preferences
• Safety check parameters

INTEGRATION REQUIREMENTS
------------------------
For full automation:
• SharpCap properly configured
• Mount control operational
• Camera settings optimized
• Network connectivity stable

RECOMMENDED AUTOMATION WORKFLOW
-------------------------------
New Users:
1. Start with manual operations
2. Graduate to semi-automated sequence generation
3. Test automated execution with non-critical events
4. Move to full automation for routine observations

Experienced Users:
• Use Tonight's Events for complete automation
• Customize templates for specific needs
• Implement site-specific safety checks
• Develop backup procedures

TROUBLESHOOTING AUTOMATION
--------------------------
Common Issues:
• Timing synchronization problems
• SharpCap communication errors
• Mount control failures
• Network connectivity issues

Prevention:
• Test automation with sample data first
• Verify all components work manually
• Use stable, tested configurations
• Maintain backup manual procedures

PERFORMANCE OPTIMIZATION
------------------------
• Minimize background processes during automation
• Ensure adequate system resources
• Use reliable network connections
• Test automation before critical observations

Automation is most effective when combined with thorough testing and reliable backup procedures. Start with simple automation and gradually increase complexity as you gain confidence in the system."""
        
    def get_troubleshooting_content(self):
        return """TROUBLESHOOTING
===============

Common issues and solutions for the Occultation Manager.

EVENT DOWNLOAD PROBLEMS
-----------------------
No Events Downloaded:
• Check OWC email/password in Configuration
• Verify you have event assignments in OWC
• Confirm internet connection is working
• Check API key is correctly entered

Authentication Errors:
• Ensure email address is confirmed in OWC
• Verify API key from OWC User Profile
• Check for typos in credentials
• Try logging into OWC website manually

Connection Timeouts:
• Check firewall/proxy settings
• Verify OWC service availability
• Try downloading at different times
• Check network connectivity

SEQUENCE GENERATION ISSUES
--------------------------
Empty Sequence Files:
• Verify template file exists in File Folder
• Check template file isn't corrupted
• Ensure template contains valid variables
• Test with default template first

Template Not Found:
• Place template .txt file in configured File Folder
• Ensure filename contains "template"
• Check file permissions are readable
• Use Browse button to verify File Folder location

Variable Substitution Errors:
• Check template variable syntax: {variable_name}
• Ensure all variables are spelled correctly
• Test template with simple events first
• Review generated files for correct substitution

FILE AND PATH PROBLEMS
----------------------
Cannot Save Files:
• Check folder permissions are writable
• Ensure sufficient disk space available
• Verify paths don't contain invalid characters
• Try using different folder locations

Configuration Not Saved:
• Check application has write permissions
• Verify config folder is accessible
• Look for Windows UAC permission issues
• Try running as administrator if needed

Sequence Files Not Found:
• Verify Sequence Path setting in Configuration
• Check files aren't being saved to unexpected location
• Use Browse button to confirm folder location
• Look for files in default Documents folder

SHARPCAP INTEGRATION ISSUES
---------------------------
Cannot Connect to SharpCap:
• Verify SharpCap is running
• Check SharpCap version compatibility (4.1+)
• Ensure no other applications are controlling SharpCap
• Try restarting both applications

GOTO Commands Fail:
• Check mount is connected in SharpCap
• Verify mount control is working manually
• Ensure coordinates are in correct format
• Test GOTO with known good coordinates

Camera Control Problems:
• Verify camera is connected and working in SharpCap
• Check camera settings are not locked
• Ensure exposure settings are within camera limits
• Test camera control manually first

INTERFACE AND DISPLAY ISSUES
----------------------------
Grid Not Updating:
• Try Refresh button to reload events
• Check if events were downloaded successfully
• Verify station filter isn't hiding events
• Look for error messages in status bar

Theme/Display Problems:
• Try toggling Night Mode on/off
• Check Windows display scaling settings
• Verify graphics drivers are current
• Try resizing window to refresh display

Dialog Boxes Not Appearing:
• Check for dialogs opening off-screen
• Try Alt+Tab to find hidden windows
• Reset window positions by restarting application
• Check multiple monitor configuration

PERFORMANCE ISSUES
------------------
Slow Loading:
• Check available system memory
• Close unnecessary background applications
• Verify disk space isn't critically low
• Try smaller event datasets for testing

Application Freezing:
• Allow more time for network operations
• Check for Windows updates or antivirus interference
• Monitor system resources during operation
• Try restarting application if unresponsive

GETTING HELP
------------
If problems persist:
• Check status bar messages for specific errors
• Review Windows Event Viewer for system errors
• Test with minimal configuration first
• Document exact steps that cause problems
• Contact support with specific error messages and system details

Remember: Most issues are configuration-related and can be resolved by carefully reviewing the setup steps and verifying all required components are properly configured."""

    def get_common_issues_content(self):
        return """COMMON ISSUES
=============

Frequently encountered problems and their solutions.

"NO EVENTS DOWNLOADED"
----------------------
Cause: Usually authentication or assignment issues
Solutions:
1. Verify OWC credentials in Tools → Configuration
2. Check you have event assignments in OWC
3. Confirm email address is verified in OWC
4. Test API key from OWC User Profile

"TEMPLATE NOT FOUND"
-------------------
Cause: Template file missing or incorrectly named
Solutions:
1. Place .txt file in File Folder with "template" in name
2. Check File Folder path in Configuration
3. Verify file permissions allow reading
4. Try using default template first

"SEQUENCE FILES EMPTY"
---------------------
Cause: Template formatting or variable issues
Solutions:
1. Check template uses correct variable syntax: {variable_name}
2. Verify template contains valid SharpCap commands
3. Open template file to check for corruption
4. Test with known good template

"CANNOT CONNECT TO SHARPCAP"
---------------------------
Cause: SharpCap not running or version incompatibility
Solutions:
1. Ensure SharpCap 4.1+ is running
2. Close other astronomy applications
3. Restart both applications
4. Check Windows firewall isn't blocking connection

"GOTO COMMANDS NOT WORKING"
---------------------------
Cause: Mount not connected or coordinate issues
Solutions:
1. Verify mount control works in SharpCap manually
2. Check mount is properly connected and initialized
3. Test coordinates with known good target
4. Ensure mount isn't parked or locked

"EVENTS GRID IS EMPTY"
---------------------
Cause: Events not downloaded or filter hiding them
Solutions:
1. Click Download Events to get data from OWC
2. Check Station Filter isn't hiding events
3. Use "All" filter to show all events
4. Verify events exist for your stations in OWC

"NIGHT MODE NOT WORKING"
-----------------------
Cause: Theme application issues
Solutions:
1. Try toggling Night Mode off and on
2. Restart application to reset theme
3. Check Windows high contrast mode isn't interfering
4. Verify graphics drivers are current

"CONFIGURATION WON'T SAVE"
-------------------------
Cause: File permissions or path issues
Solutions:
1. Check folder permissions allow writing
2. Run application as administrator
3. Verify config folder path is accessible
4. Check Windows UAC isn't blocking file access

"APPLICATION FREEZES DURING DOWNLOAD"
------------------------------------
Cause: Network issues or large datasets
Solutions:
1. Check internet connection stability
2. Try downloading at different times
3. Verify firewall isn't blocking application
4. Allow more time for large event lists

"EXPOSURES NOT CALCULATING CORRECTLY"
------------------------------------
Cause: Configuration or star magnitude issues
Solutions:
1. Check "Mag for 40ms exposure" setting in Configuration
2. Verify star magnitudes in event data are reasonable
3. Test with known good events
4. Use custom exposure override if needed

"SEQUENCES RUN AT WRONG TIMES"
-----------------------------
Cause: Timezone or timing configuration issues
Solutions:
1. Verify system clock is correct
2. Check timezone settings in Windows
3. Confirm event times are in UTC
4. Review GOTO lead time configuration

PREVENTION TIPS
---------------
• Test configuration with sample data first
• Verify all setup steps before critical observations
• Keep backup copies of working templates
• Document configuration settings that work
• Test automation before relying on it

WHEN TO SEEK ADDITIONAL HELP
----------------------------
• Issues persist after trying common solutions
• Error messages are unclear or undocumented
• System-specific problems with hardware integration
• Need custom template development assistance

Most common issues are resolved by carefully reviewing the configuration and ensuring all prerequisites are met."""

def get_error_messages_content(self):
        return """ERROR MESSAGES
==============

Explanation of common error messages and how to resolve them.

DOWNLOAD ERRORS
---------------
"HTTP Error: 401 - Unauthorized"
• Invalid OWC credentials
• Check email/password in Configuration
• Verify API key is correct

"HTTP Error: 403 - Forbidden"  
• Account access issues
• Check email is verified in OWC
• Confirm API key permissions

"HTTP Error: 404 - Not Found"
• API endpoint issues
• Check API host setting in Configuration
• Verify OWC service is available

"Connection timed out"
• Network connectivity issues
• Check internet connection
• Try again later if OWC is busy

FILE OPERATION ERRORS
---------------------
"Permission denied"
• File/folder access issues
• Check folder permissions
• Try running as administrator
• Verify antivirus isn't blocking

"File not found"
• Incorrect path configuration
• Check File Folder and Sequence Path settings
• Verify folders exist

"Disk full"
• Insufficient storage space
• Free up disk space
• Choose different storage location

CONFIGURATION ERRORS
--------------------
"Invalid numeric value"
• Non-numeric entry in numeric field
• Enter valid numbers only
• Check decimal separator (use period)

"Cannot access/create folder"
• Path doesn't exist or no permissions
• Choose accessible folder location
• Check folder path spelling

"Configuration validation errors"
• Multiple setup issues detected
• Review all configuration tabs
• Fix each listed error

SEQUENCE GENERATION ERRORS
--------------------------
"Template not found or empty"
• Missing template file
• Place template.txt in File Folder
• Check template file isn't empty

"Error creating sequence"
• File write permission issues
• Check Sequence Path is writable
• Verify disk space available

"Could not parse datetime"
• Invalid event time format
• Re-download events from OWC
• Check for data corruption

SHARPCAP INTEGRATION ERRORS
---------------------------
"SharpCap not found"
• SharpCap not running or wrong version
• Start SharpCap 4.1 or later
• Check installation path

"Camera not available"
• No camera selected in SharpCap
• Connect and select camera in SharpCap
• Verify camera is working

"Mount control error"
• Mount not connected or responding
• Check mount connection in SharpCap
• Verify mount is initialized

AUTOMATION ERRORS
-----------------
"No future events to run"
• All selected events are in the past
• Select events with future times
• Check system clock is correct

"Sequence file not found"
• Generated sequence missing
• Re-generate sequences
• Check Sequence Path setting

"Sequence runner already running"
• Multiple automation attempts
• Wait for current operation to finish
• Restart application if stuck

UNDERSTANDING ERROR CONTEXT
---------------------------
Error messages include:
• Specific operation that failed
• Affected event or file names
• Suggested corrective actions
• Technical details for troubleshooting

Most errors provide enough information to identify and resolve the underlying issue. When in doubt, check the configuration settings and verify all prerequisites are met."""

    def get_config_problems_content(self):
        return """CONFIGURATION PROBLEMS
======================

Solutions for configuration-related issues.

CREDENTIAL ISSUES
-----------------
Cannot Login to OWC:
• Verify email address exactly matches OWC account
• Check password hasn't changed
• Confirm account is active and not suspended
• Test login on OWC website directly

API Key Problems:
• Get fresh API key from OWC User Profile
• Ensure email address is verified in OWC
• Check key wasn't truncated when copying
• Verify key has proper permissions

PATH CONFIGURATION ISSUES
-------------------------
Folders Not Found:
• Use Browse buttons to select valid folders
• Ensure folders exist and are accessible
• Check folder permissions allow reading/writing
• Avoid network paths that might disconnect

File Access Problems:
• Run application as administrator if needed
• Check Windows UAC isn't blocking access
• Verify antivirus isn't quarantining files
• Use local folders rather than network locations

PARAMETER CONFIGURATION
-----------------------
Recording Duration Issues:
• Base Duration should be 30-120 seconds typically
• GOTO Lead Time should match your mount's speed
• Consider site-specific timing requirements
• Test with conservative values first

Exposure Calculation Problems:
• Magnitude reference affects all exposure calculations
• Adjust based on your camera sensitivity
• Test with known star magnitudes
• Use custom exposures for critical events

TEMPLATE CONFIGURATION
---------------------
Template Not Working:
• Check template file encoding (use plain text)
• Ensure template variables use correct syntax: {variable_name}
• Test template with simple SharpCap commands first
• Verify template produces valid sequence files

NETWORK CONFIGURATION
--------------------
Connection Problems:
• Check Windows Firewall isn't blocking application
• Verify proxy settings if using corporate network
• Ensure DNS can resolve occultwatcher.net
• Test with different network if possible

TROUBLESHOOTING STEPS
---------------------
1. Reset to Defaults:
   • Use "Reset to Defaults" in Configuration dialog
   • Reconfigure only essential settings
   • Test basic functionality before adding customizations

2. Validate Each Setting:
   • Test credentials by downloading events
   • Verify paths by browsing to folders
   • Check parameters with sample calculations
   • Confirm templates with test sequence generation

3. Incremental Configuration:
   • Configure one section at a time
   • Test after each change
   • Don't change multiple settings simultaneously
   • Document working configurations

BACKUP AND RECOVERY
-------------------
• Configuration file is saved in your File Folder
• Keep backup copies of working configurations
• Note working parameter values
• Document any custom template modifications

GETTING CONFIGURATION RIGHT
---------------------------
• Start with default settings and modify gradually
• Test each configuration change
• Use sample data for testing when possible
• Verify configuration works before critical observations

Most configuration problems are resolved by careful attention to detail and systematic testing of each setting."""

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
Version 2.0

Author: Michael Camilleri

A comprehensive tool for managing asteroid occultation observations using SharpCap.

FEATURES:
• Automated event download from OccultWatcher Cloud
• Interactive observation preparation tools  
• Automated sequence generation and execution
• Night vision preserving interface
• Station filtering and event management
• Template-based sequence customization

WORKFLOW:
Download → Filter → Prepare → Generate → Execute

This tool streamlines the entire occultation observation process from planning through automated execution, helping observers maximize their success rate while minimizing manual intervention during critical observation periods.

For complete documentation, use Help → User Guide.

© 2024 Michael Camilleri. All rights reserved."""

        MessageBox.Show(about_text, "About Occultation Manager", 
                       MessageBoxButtons.OK, MessageBoxIcon.Information)