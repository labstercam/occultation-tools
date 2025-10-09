import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Point, Size, Font, FontStyle
from System.Windows.Forms import Label, TextBox, ScrollBars, DialogResult
from System.Windows.Forms import TreeView, TreeNode, FormStartPosition, FormBorderStyle, SplitContainer, DockStyle, FixedPanel, Button, Form  # Added Form and TreeNode import
from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon
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
        self.add_node_with_tag(event_mgmt, "Editing Exposures", "editing_exposures")
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
            "troubleshooting": self.get_troubleshooting_content().replace('\n','\r\n'),
            "common_issues": self.get_common_issues_content().replace('\n','\r\n'),
            "error_messages": self.get_error_messages_content().replace('\n','\r\n'),
            "config_problems": self.get_config_problems_content().replace('\n','\r\n')
        }
        
        return content_map.get(topic, "Help content not found for this topic.")
    
    def get_sequences_content(self):
            return """SEQUENCE GENERATION
        ===================

        Automated creation of SharpCap sequence files for occultation recording.

        Sequences are used rather than direct software control by the tool as it is easier for users to create templates for their own telescope setups, and the sequences can be used manually or sent to another station.

        SEQUENCE WORKFLOW
        -----------------
        1. Select events using checkboxes in the events grid
        2. Click "Create Sequences" button in toolbar
        3. Choose template from Template Selection dialog
        4. Application generates individual .scs files for each selected event
        5. Files saved to configured Sequence Path
        6. Ready for manual loading or automated execution

        TEMPLATE SYSTEM
        ---------------
        Templates define the structure and commands used in sequences:
        • Built-in default template for standard operations
        • Custom template support (.txt files in File Folder with "template" in name)
        • Variable substitution for event-specific data
        • Template preview and selection interface

        Available Template Variables:
        • {object_name}: Asteroid name
        • {event_time}: Occultation center time (UTC)
        • {goto_time}: GOTO start time
        • {start_time}: Recording start time
        • {recording_duration}: Total recording seconds
        • {exposure}: Camera exposure time in seconds
        • {ra}, {dec}: Target coordinates
        • {star_mag}, {comb_mag}: Brightness values
        • {event_time_local}: Event time (local HH:MM:SS)
        • {goto_time_local}: GOTO time (local HH:MM:SS)
        • {start_time_local}: Start time (local HH:MM:SS)

        FILE NAMING
        -----------
        Automatic naming format: YYYYMMDD [Event Name].scs
        Example: 20241215 433 Eros - Station ABC.scs

        BATCH GENERATION
        ----------------
        • Select multiple events for simultaneous processing
        • Each event gets individual sequence file
        • Progress tracking during generation
        • Summary report of success/failure counts

        COMBINED SEQUENCES
        ------------------
        Alternative option: "Combined Script" button
        • Creates single file containing multiple events
        • Chronologically ordered execution
        • Automatic transitions between events
        • Named: YYYYMMDD_[StationName]_Combined_Sequences.scs

        TIMING COORDINATION
        -------------------
        Automatic calculations:
        • GOTO start time with configurable lead time (from Configuration)
        • Recording start based on event uncertainty
        • Recording duration including base duration buffer
        • All times coordinated for precise execution

        EXECUTION OPTIONS
        -----------------
        Manual Execution:
        • Load .scs files directly in SharpCap
        • User controls timing and start

        Automated Execution:
        • Use "Run Sequences" button for selected events
        • Application manages timing and execution automatically
        • Background processing with status updates

        The sequence generation system creates SharpCap-compatible .scs files with precise timing and complete automation commands for reliable occultation recording."""


    def get_overview_content(self):
        return """OCCULTATION MANAGER FOR SHARPCAP
        Author: Michael Camilleri

        OVERVIEW
        ========

        The Occultation Manager automates occultation observation workflows using SharpCap.

        MAIN WORKFLOW
        -------------
        1. SETUP: Configure OWC credentials and file paths in Tools → Configuration
        2. DOWNLOAD: Click "Download Events" to retrieve assigned events from OWC
        3. FILTER: Use Station Filter and Quick Filters to show desired events
        4. PREPARE: Use bottom panel tools for interactive setup and verification
        5. GENERATE: Click "Create Sequences" to generate SharpCap .scs files
        6. EXECUTE: Use "Run Sequences" for automation or "Run Tonight's Events" for complete automation

        KEY FEATURES
        ------------
        • Event download from OccultWatcher Cloud
        • Station filtering and event organization
        • Interactive preparation tools (GOTO, plate solving)
        • Automated sequence generation from templates
        • Background execution with precise timing
        • Night vision preserving red theme
        • Complete automation via "Tonight's Events" button

        The tool handles everything from event download through automated execution."""

    def get_getting_started_content(self):
        return """GETTING STARTED
        ===============

        Quick setup guide for new users.

        PREREQUISITES
        -------------
        • SharpCap 4.1 or later. Most recent version or recent version recommended
        • OccultWatcher Cloud account with event assignments
        • API Key assigned to your user in OWC

        SETUP CHECKLIST
        ---------------
        1. Go to Tools → Configuration
        2. Enter OWC email/password in Credentials tab
        3. Get API key from OWC User Profile and enter in API Settings tab
        4. Set File Folder and Sequence Path in File Paths tab
        5. Configure recording parameters in Recording tab
        6. Click Save

        FIRST USE
        ---------
        1. Click "Download Events" to get your assigned events
        2. Select an event and click "Event Details" to review
        3. Try "Create Sequences" to generate a test .scs file
        4. Use preparation tools to test GOTO and plate solving

        Note: Only basic functions are provided by the default sequence template. You will need to modify or setup your own to suit your setups

        """

    def get_initial_setup_content(self):
        return """INITIAL SETUP
        =============

        Required configuration steps before first use.

        STEP 1: OWC CREDENTIALS
        -----------------------
        Tools → Configuration → Credentials tab:
        • Enter your OccultWatcher Cloud email address
        • Enter your OWC password
        • These must match your active OWC account exactly

        STEP 2: API KEY
        ---------------
        Tools → Configuration → API Settings tab:
        • Log into https://cloud.occultwatcher.net
        • Go to User Profile → User Permissions
        • Copy your API key and paste it in the API Settings tab

        STEP 3: FILE PATHS
        ------------------
        Tools → Configuration → File Paths tab:
        • File Folder: Where event data and templates are stored
        • Sequence Path: Where .scs files are generated
        • Both folders created automatically if they don't exist

        STEP 4: RECORDING PARAMETERS
        ----------------------------
        Tools → Configuration → Recording tab:
        • Base Duration: Added to event duration (default: 60 seconds)
        • GOTO Lead Time: How early to start GOTO (default: 240 seconds)
        • Magnitude Reference: Star magnitude for 40ms exposure (default: 12.0)

        VERIFICATION
        ------------
        1. Click "Download Events" - should retrieve your assigned events
        2. Create a test sequence to verify file generation
        3. Check that files appear in configured folders"""

    def get_configuration_content(self):
        return """CONFIGURATION
        =============

        Access via Tools → Configuration.

        CREDENTIALS TAB
        ---------------
        • OWC Email: Your OccultWatcher Cloud login email
        • OWC Password: Your OWC account password
        • Must match your active OWC account exactly

        API SETTINGS TAB
        ----------------
        • API Host: OWC server URL (normally don't change)
        • API Key: Get from OWC User Profile → User Permissions
        • Email must be verified in OWC first

        FILE PATHS TAB
        --------------
        • File Folder: Storage for event data and templates
        • Sequence Path: Where .scs files are saved
        • Occultations File: Master event database filename
        • Latest File: Temporary download filename

        RECORDING TAB
        -------------
        • Base Duration: Minimum recording time added to event duration
        • GOTO Lead Time: Seconds before recording to start GOTO
        • Magnitude for 40ms Exposure: Reference for exposure calculation

        All settings are saved automatically and validated when Save is clicked."""

    def get_first_use_content(self):
        return """FIRST USE
        =========

        Step-by-step first session guide.

        STEP 1: DOWNLOAD EVENTS
        -----------------------
        • Click "Download Events" button
        • Retrieves all assigned events from OWC
        • Events appear in main grid with calculated parameters

        STEP 2: EXPLORE EVENTS
        ----------------------
        • Review events in main grid
        • Click column headers to sort
        • Use Station Filter to show specific locations
        • Double-click events for detailed information

        STEP 3: TEST PREPARATION
        ------------------------
        • Select an event and click "Load Event" in bottom panel
        • Try "Setup for Event" to configure SharpCap
        • Use "GOTO & Center" to test telescope positioning
        • Try "Plate Solve & Label" to verify position and label the target star

        STEP 4: CREATE SEQUENCES
        ------------------------
        • Select one or more events using checkboxes
        • Click "Create Sequences"
        • Choose template and generate .scs files
        • Check files are created in Sequence Path

        STEP 5: VERIFY SETUP
        --------------------
        • Open .scs file in text editor to verify content
        • Test loading sequence in SharpCap
        • Confirm coordinates and timing are correct"""

    def get_main_interface_content(self):
        return """MAIN INTERFACE
        ==============

        The main window layout and key areas.

        LAYOUT OVERVIEW
        ---------------
        1. Menu Bar: Access to all functions
        2. Toolbar: Quick access buttons in two rows
        3. Station Filter: Dropdown to filter events by location
        4. Events Grid: Main display of all events with selection checkboxes
        5. Bottom Panel: Configuration, preparation tools, and quick filters
        6. Status Bar: Current operation status and event count

        KEY AREAS
        ---------
        Events Grid: Central area showing all event information
        • Checkboxes for selecting events for batch operations
        • Sortable columns for organization
        • Double-click for event details

        Bottom Panel Sections:
        • Configuration: Sequence Path setting
        • Preparation: Interactive tools for event setup
        • Quick Filters: Today/Upcoming/All buttons
        • Selection Summary: Count of selected events

        The interface follows a logical workflow from top to bottom: download → filter → select → prepare → generate."""

    def get_menu_bar_content(self):
        return """MENU BAR
        ========

        Complete access to all application functions.

        FILE MENU
        ---------
        • Download Events: Get latest from OWC
        • Refresh Events: Reload from local files
        • Download & Run Tonight's Events: Complete automation
        • Exit: Close application

        EVENTS MENU
        -----------
        • Event Details: Show detailed event information
        • Edit Exposure: Modify exposure time
        • Select All: Mark all events currently visible in the grid (e.g. only filtered stations)
        • Select None: Clear all selections

        SEQUENCES MENU
        --------------
        • Create Sequences: Generate .scs files
        • Generate Combined Script: Single sequence for multiple events
        • Run Selected Sequences: Automated execution

        TOOLS MENU
        ----------
        • Configuration: Settings dialog
        • Template Manager: Select sequence templates

        HELP MENU
        ---------
        • User Guide: This help system
        • About: Application information

        Most functions are also available via toolbar buttons for quick access."""

    def get_toolbar_content(self):
        return """TOOLBAR
        =======

        Two rows of buttons for quick access to common functions.

        TOP ROW - EVENT MANAGEMENT
        ---------------------------
        • Download Events: Get latest from OWC
        • Refresh: Reload from local files
        • Tonight's Events: Complete automation
        • Select All: Mark all events
        • Select None: Clear selections
        • Event Details: Show detailed information
        • Edit Exposure: Modify exposure settings
        • Test GOTO & Solve: Quick positioning test
        • Night Mode: Toggle red theme

        BOTTOM ROW - SEQUENCES
        ----------------------
        • Create Sequences: Generate .scs files
        • Run Sequences: Automated execution
        • Combined Script: Multi-event sequence file

        BUTTON STATES
        -------------
        • Grayed buttons are disabled (no selection required)
        • Some buttons require event selection to be active
        • Night Mode button text changes to reflect current state

        Buttons are arranged in typical workflow order from left to right."""

    def get_events_grid_content(self):
        return """EVENTS GRID
        ===========

        Central display showing all occultation events.

        COLUMNS
        -------
        • Selected: Checkbox for batch operations
        • Event Name: Asteroid name and station
        • Station: Observing location
        • Date/Time UTC: Occultation timing
        • Star Mag/Comb Mag/Mag Drop: Brightness information
        • Exposure (ms): Calculated or custom (* indicates custom)
        • Recording Time (s): Total recording duration
        • Max Duration (s): Maximum occultation length
        • Time Error (s): Timing uncertainty
        • Alt/Az: Target position at event time
        • Coordinates: RA/Dec (J2000)
        • OWC: Link to event on OccultWatcher Cloud
        • Status: Event timing status

        INTERACTIONS
        ------------
        • Single click: Select row
        • Double-click: Open Event Details
        • Double-click Exposure: Edit exposure time
        • Checkbox: Select for batch operations
        • Column headers: Sort by that column
        • OWC link: Opens event in web browser

        VISUAL INDICATORS
        -----------------
        • * after exposure: Custom exposure (not calculated)
        • Status shows: future, past, starting soon, etc.
        • Color coding varies by day/night theme"""

    def get_station_filter_content(self):
        return """STATION FILTER
        ==============

        Dropdown filter below toolbar for showing events by observing location.

        HOW IT WORKS
        ------------
        • Dropdown automatically populated with station names from events
        • "All Stations" shows everything (default)
        • Select specific station to filter events
        • Filter applies immediately when selection changes
        • Event count updates in status bar

        FEATURES
        --------
        • Event selections preserved when filtering
        • "Clear Filter" button returns to "All Stations"
        • Works with Quick Filters and sorting
        • Useful for multi-station observers

        The Station Filter helps organize events when you have assignments at multiple observing locations."""

    def get_bottom_panel_content(self):
        return """BOTTOM PANEL
        ============

        Three main sections for configuration, preparation, and filtering.

        CONFIGURATION SECTION
        ----------------------
        • Sequence Path: Shows current path for .scs file generation
        • Browse button to select different folder
        • Path automatically used for all sequence creation

        OBSERVATION PREPARATION
        -----------------------
        Interactive tools for event setup:
        • Load Event: Select event from grid for preparation
        • Setup for Event: Configure SharpCap parameters
        • GOTO & Center: Execute telescope positioning
        • Plate Solve & Label: Verify position accuracy
        • Clear Labels: Remove overlay markers

        Event Display shows loaded event details including coordinates, timing, and exposure settings.

        QUICK FILTERS
        -------------
        • Today: Show events in next 24 hours
        • Upcoming: Show all future events
        • All: Show all events (clear filters)

        SELECTION SUMMARY
        -----------------
        Shows count of selected events and how many are future events that can be executed.

        The bottom panel integrates configuration, interactive preparation, and quick filtering for efficient workflow management."""

    def get_status_bar_content(self):
        return """STATUS BAR
        ==========

        Bottom window bar showing current status and event information.

        INFORMATION DISPLAYED
        ---------------------
        Left Side: Current operation status
        • "Downloading events..." during network operations
        • "Downloaded X events" on completion
        • "Ready" when idle
        • Error messages when problems occur

        Right Side: Event count
        • Total events currently displayed
        • Updates with filtering and downloads
        • Reflects current filter state

        TYPICAL MESSAGES
        ----------------
        • "Downloading events from OW Cloud..."
        • "Downloaded 15 events"
        • "Loaded event for preparation: [event name]"
        • "Generating sequence for [event name]..."
        • "Night mode enabled/disabled"

        The status bar provides immediate feedback on all operations and current system state."""

    def get_downloading_events_content(self):
        return """DOWNLOADING EVENTS
        ==================

        Getting event data from OccultWatcher Cloud.

        DOWNLOAD PROCESS
        ----------------
        Click "Download Events" button:
        1. Connects to OWC using configured credentials
        2. Retrieves all events assigned to your stations
        3. Calculates exposure times based on star magnitudes
        4. Determines recording durations with uncertainty buffers
        5. Saves to occultations_latest.json and merges with occultations.json
        6. Updates events grid display

        WHAT GETS DOWNLOADED
        --------------------
        • All events assigned to your OWC stations
        • Complete timing and coordinate data
        • Star magnitudes for exposure calculation
        • Uncertainty values for duration calculation
        • Links to detailed OWC event pages

        AUTOMATIC PROCESSING
        --------------------
        • Exposure calculation using magnitude reference from Configuration
        • Recording duration = max duration + base duration from Configuration
        • GOTO time = event time - lead time from Configuration
        • Automatic removal of events older than 14 days

        FILE MANAGEMENT
        ---------------
        • Events saved to File Folder as occultations.json
        • Latest download saved as occultations_latest.json
        • Custom exposure modifications preserved across downloads

        Download frequency: daily during active periods or when new events are assigned."""

    def get_editing_exposures_content(self):
        return """EDITING EXPOSURES
    =================

        Modifying camera exposure times for specific events.

        ACCESS METHODS
        --------------
        • Select event and click "Edit Exposure" button, OR
        • Double-click the Exposure column in events grid

        EXPOSURE EDITOR
        ---------------
        • Shows current exposure (calculated or custom)
        • Text input for manual entry
        • Quick-set buttons: 10ms, 20ms, 40ms, 100ms, etc.
        • Reset button to return to calculated value
        • OK/Cancel buttons

        AUTOMATIC vs CUSTOM
        -------------------
        • Default exposures calculated from star magnitude and configuration
        • Custom exposures show "*" in events grid
        • Custom settings override automatic calculation
        • Reset button returns to automatic calculation

        VALIDATION
        ----------
        • Values must be between 1ms and 10000ms
        • Invalid entries show warning messages
        • Changes applied when OK clicked

        Custom exposures are preserved across event downloads and remembered for future use."""

    def get_selecting_events_content(self):
        return """SELECTING EVENTS
        ================

        Choosing events for batch operations using checkboxes.

        SELECTION METHODS
        -----------------
        • Individual: Click checkbox in "Selected" column
        • Bulk: "Select All" or "Select None" buttons
        • Checkboxes work with current filter settings

        SELECTION BEHAVIOR
        ------------------
        • Selections preserved when changing filters
        • Hidden events stay selected but don't appear in operations
        • Selection summary shown in bottom panel
        • Grid highlighting different from checkbox selection

        BATCH OPERATIONS
        ----------------
        Selected events used for:
        • Creating sequence files
        • Generating combined scripts
        • Running automated sequences
        • Statistical summaries

        WORKFLOW TIPS
        -------------
        • Use Station Filter then Select All for location-specific operations
        • Use Quick Filters (Today/Upcoming) then select for time-based operations
        • Check selection summary before batch operations

        The selection system supports both single-event workflows and complex multi-event batch processing."""

    def get_event_management_content(self):
        return """EVENT MANAGEMENT
        ================

        Organizing and working with occultation events.

        CORE FUNCTIONS
        --------------
        Download Events:
        • Retrieves latest assignments from OWC
        • Processes and validates event data
        • Merges with existing events automatically

        Event Display:
        • Comprehensive grid with sortable columns
        • Real-time status updates
        • Visual indicators for custom settings
        • Links to detailed OWC event pages

        Event Selection:
        • Individual checkboxes and bulk selection tools
        • Selection preserved across filtering operations
        • Batch operations on selected events

        FILTERING CAPABILITIES
        ----------------------
        • Station Filter: Show events for specific locations
        • Quick Filters: Today/Upcoming/All for time-based selection
        • Column sorting: Click headers to sort by any field
        • Combined filtering for precise event selection

        DATA MANAGEMENT
        ---------------
        • Automatic exposure calculations based on star magnitudes
        • Recording duration with uncertainty buffers
        • GOTO timing with configurable lead times
        • Custom modifications preserved across downloads
        • Automatic cleanup of events older than 14 days

        The event management system handles everything from download through selection for automated operations."""

    def get_creating_sequences_content(self):
        return """CREATING SEQUENCES
        ==================

        Generating SharpCap .scs files from selected events.

        SEQUENCE CREATION
        -----------------
        1. Select events using checkboxes
        2. Click "Create Sequences" button
        3. Choose template from selection dialog
        4. Application generates individual .scs file for each event
        5. Files saved to configured Sequence Path

        TEMPLATE SYSTEM
        ---------------
        • Built-in default template if no custom template exists
        • Custom templates: .txt files with "template" in name in File Folder
        • Template preview shows content before selection
        • Variables automatically replaced with event data

        GENERATED FILES
        ---------------
        • Named: YYYYMMDD [Event Name].scs
        • Contains complete SharpCap commands for automation
        • Includes timing, coordinates, and recording parameters
        • Ready for manual loading or automated execution

        BATCH PROCESSING
        ----------------
        • Multiple events create multiple sequence files
        • Progress shown during generation
        • Success/failure count reported
        • Each file independent and self-contained

        The sequence generation system transforms event data into executable SharpCap automation files."""

    def get_template_selection_content(self):
        return """TEMPLATE SELECTION
    ==================

        Choosing templates for sequence generation.

        TEMPLATE DIALOG
        ---------------
        • Shows available templates with file information
        • Template preview displays full content
        • File size and modification date shown
        • Selection updates preview immediately

        TEMPLATE TYPES
        --------------
        • Default Template: Built-in template used when no custom files exist
        • Custom Templates: .txt files in File Folder with "template" in filename
        • Template preview shows complete content with proper formatting

        TEMPLATE VARIABLES
        ------------------
        Variables replaced with event data:
        • {object_name}: Asteroid name
        • {event_time}: Event center time (UTC)
        • {goto_time}: GOTO start time
        • {recording_duration}: Recording seconds
        • {exposure}: Exposure time
        • {ra}, {dec}: Target coordinates
        • And many others for complete customization

        CUSTOM TEMPLATES
        ----------------
        • Create .txt file in File Folder
        • Include "template" in filename
        • Use SharpCap commands with variable placeholders
        • Test with sample events before critical use

        The template system allows complete customization of generated sequence commands while providing sensible defaults."""

    def get_combined_scripts_content(self):
        return """COMBINED SCRIPTS
        ================

        Creating single sequence files containing multiple events.

        COMBINED SCRIPT CREATION
        ------------------------
        1. Select multiple events using checkboxes
        2. Click "Combined Script" button
        3. Choose template for sequence generation
        4. Application creates single .scs file with all events

        COMBINED FILE FEATURES
        ----------------------
        • Events ordered chronologically by GOTO time
        • Complete timing coordination between events
        • Single file for simplified execution
        • Named: YYYYMMDD_[StationName]_Combined_Sequences.scs

        WHEN TO USE
        -----------
        • Multiple events in one observing session
        • All-night automated observations
        • Events from same observing station
        • Minimal manual intervention desired

        MULTI-STATION HANDLING
        ----------------------
        • Warning dialog if events from different stations selected
        • File created but may need manual coordination
        • Consider separate combined files per station

        Combined scripts simplify execution by merging multiple events into one automated sequence file."""

    def get_running_sequences_content(self):
        return """RUNNING SEQUENCES
        =================

        Automated execution of generated sequence files.

        EXECUTION METHODS
        -----------------
        Manual Execution:
        • Load .scs files directly in SharpCap
        • User controls timing and start

        Automated Execution:
        • Click "Run Sequences" for selected events
        • Application manages timing automatically
        • Sequences start at calculated GOTO times

        AUTOMATED PROCESS
        -----------------
        1. Select events with future GOTO times
        2. Click "Run Sequences" button
        3. Application waits for each event's GOTO time
        4. Sequences execute automatically in chronological order
        5. Status updates show progress

        TONIGHT'S EVENTS
        ----------------
        Complete automation via "Tonight's Events" button:
        • Downloads latest events
        • Filters for next 24 hours
        • Creates sequences automatically
        • Starts execution immediately
        • Hands-off operation for entire night

        REQUIREMENTS
        ------------
        • SharpCap running and accessible
        • Sequence files exist for selected events
        • Events must have future GOTO times
        • System remains running until completion

        Automated execution provides reliable hands-off operation while maintaining manual control options when needed."""

    def get_troubleshooting_content(self):
        return """TROUBLESHOOTING
    ===============

        Solutions for common problems.

        EVENT DOWNLOAD ISSUES
        ---------------------
        No Events Downloaded:
        • Check OWC credentials in Configuration
        • Verify event assignments exist in OWC
        • Confirm internet connection

        Authentication Errors:
        • Verify email address confirmed in OWC
        • Check API key from OWC User Profile
        • Test login on OWC website

        SEQUENCE PROBLEMS
        -----------------
        Empty Sequence Files:
        • Verify template file exists in File Folder
        • Check template contains valid SharpCap commands
        • Ensure template uses correct variable syntax

        Template Not Found:
        • Place .txt file with "template" in name in File Folder
        • Check File Folder path in Configuration

        SHARPCAP INTEGRATION
        --------------------
        Cannot Connect:
        • Ensure SharpCap 4.1+ is running
        • Close other applications controlling SharpCap
        • Restart both applications

        GOTO Problems:
        • Check mount connected in SharpCap
        • Test GOTO manually first
        • Verify coordinates are reasonable

        FILE ISSUES
        -----------
        Cannot Save Files:
        • Check folder permissions
        • Run as administrator if needed
        • Verify sufficient disk space

        Most issues resolve by checking Configuration settings and ensuring prerequisites are met."""

    def get_event_details_content(self):  # (fixed indentation)
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

    def get_observation_prep_content(self):  # (generated)
        return """OBSERVATION PREPARATION
    =======================

    Interactive tools in the bottom panel for setting up occultation observations.

    PREPARATION WORKFLOW
    --------------------
    1. Select event in main grid
    2. Click "Load Event" to prepare for setup
    3. Use "Setup for Event" to configure SharpCap
    4. Click "GOTO & Center" for telescope positioning
    5. Use "Plate Solve & Label" to verify position
    6. Click "Clear Labels" to clean up display

    LOAD EVENT FUNCTION
    -------------------
    • Takes first selected event from main grid
    • Displays event details in preparation panel
    • Shows event name, coordinates, timing, exposure settings
    • Enables all preparation tool buttons

    PREPARATION TOOLS
    -----------------
    Setup for Event:
    • Configures SharpCap camera settings automatically
    • Sets exposure time from event data
    • Applies target information to SharpCap

    GOTO & Center:
    • Executes telescope GOTO to target coordinates
    • Waits for mount settling and completion
    • Reports success/failure status

    Plate Solve & Label:
    • Initiates plate solving on current field
    • Verifies target position accuracy
    • Shows target information dialog
    • Adds overlay labels marking target location

    Clear Labels:
    • Removes overlay markers and labels
    • Cleans up display for fresh preparation

    The preparation tools provide step-by-step interactive setup and verification before manual or automated recording."""

    def get_loading_events_content(self):  # (generated)
        return """LOADING EVENTS
    ==============

    Methods for getting occultation event data into the application.

    LOADING METHODS
    ---------------
    Download Events:
    • Primary method using "Download Events" button
    • Connects to OccultWatcher Cloud via configured credentials
    • Retrieves all events assigned to your stations
    • Processes and saves data automatically

    Refresh Events:
    • "Refresh Events" reloads from local occultations.json file
    • Updates display without network access
    • Useful when working with previously downloaded data

    DOWNLOAD PROCESS
    ----------------
    1. Connects to OWC using email/password and API key
    2. Downloads all events for your assigned stations
    3. Calculates exposure times based on star magnitudes
    4. Determines recording durations with uncertainty buffers
    5. Saves to occultations_latest.json and merges with occultations.json
    6. Updates events grid display

    AUTOMATIC PROCESSING
    --------------------
    • Exposure calculation using magnitude reference from Configuration
    • Recording duration = max duration + base duration + uncertainty buffer
    • GOTO time calculation with configurable lead time
    • Coordinate validation and formatting
    • Automatic removal of events older than 14 days

    FILE MANAGEMENT
    ---------------
    • Events saved to File Folder as occultations.json
    • Latest download saved as occultations_latest.json
    • Automatic merge prevents duplicates
    • Custom exposure settings preserved across downloads

    The loading system automatically handles all data processing and file management for seamless event updates."""

    def get_goto_centering_content(self):  # (generated)
        return """GOTO & CENTERING
    ================

    Automated telescope positioning using the "GOTO & Center" button in the preparation panel.

    GOTO PROCESS
    ------------
    1. Uses RA/Dec coordinates from loaded event (J2000)
    2. Sends GOTO command through SharpCap mount control
    3. Waits for mount to complete slew
    4. Reports success/failure status
    5. Provides starting point for fine centering or plate solving

    REQUIREMENTS
    ------------
    • Mount connected and working in SharpCap
    • Valid coordinates loaded from selected event
    • Mount control active and responsive
    • Event loaded in preparation panel

    INTEGRATION
    -----------
    • Works through SharpCap's mount control interface
    • Uses coordinates directly from event data
    • Integrates with preparation workflow
    • Prepares field for plate solving verification

    TYPICAL ACCURACY
    ----------------
    • Gets telescope within 1-10 arcminutes of target
    • Accuracy depends on mount alignment quality
    • Provides starting point for fine positioning
    • May require plate solving for precise positioning

    The GOTO function provides automated telescope positioning as part of the interactive preparation workflow."""

    def get_plate_solving_content(self):  # (generated)
        return """PLATE SOLVING
    =============

    Astrometric verification using the "Plate Solve & Label" button in the preparation panel.

    PLATE SOLVING PROCESS
    ---------------------
    1. Captures current camera image automatically
    2. Processes image through SharpCap's plate solving engine
    3. Determines exact field center coordinates
    4. Compares solved position with target coordinates
    5. Shows target information dialog with results
    6. Adds overlay labels marking target location

    REQUIREMENTS
    ------------
    • Camera connected and working in SharpCap
    • Sufficient stars visible in current field
    • Event loaded in preparation panel
    • SharpCap plate solving configured and working

    RESULTS PROVIDED
    ----------------
    • Exact field center coordinates
    • Target position verification
    • Pointing accuracy measurement
    • Visual overlay showing target location
    • Confirmation dialog with solving details

    INTEGRATION
    -----------
    • Uses SharpCap's built-in plate solving
    • Works with current camera image
    • Integrates with preparation workflow
    • Provides visual confirmation of setup

    CLEAR LABELS
    ------------
    • "Clear Labels" button removes overlay markers
    • Cleans up display after plate solving
    • Resets view for fresh preparation

    Plate solving provides precise position verification as part of the interactive observation preparation process."""

    def get_advanced_content(self):  # (generated)
        return """ADVANCED FEATURES
    =================

    Sophisticated tools and capabilities for experienced users.

    NIGHT MODE
    ----------
    • Click "Night Mode" button in toolbar to activate
    • Complete red-tinted interface for night vision preservation
    • Consistent theming across all dialogs and windows
    • Toggle anytime with immediate visual change
    • Setting automatically saved and restored

    TONIGHT'S EVENTS AUTOMATION
    ---------------------------
    • Single "Tonight's Events" button for complete automation
    • Downloads latest events, filters for next 24 hours
    • Automatically selects and generates sequences
    • Immediately starts automated execution
    • Hands-off operation for entire night's events

    COMBINED SCRIPT GENERATION
    --------------------------
    • "Combined Script" button creates single multi-event sequence
    • Chronological ordering of selected events
    • Automatic transitions between events
    • Single file for all-night automation
    • Named: YYYYMMDD_[StationName]_Combined_Sequences.scs

    BATCH PROCESSING
    ----------------
    • Multi-event sequence generation
    • Bulk selection tools (Select All/Select None)
    • Station-based filtering and operations
    • Persistent selections across filter changes

    AUTOMATED EXECUTION
    -------------------
    • "Run Sequences" button for hands-off execution
    • Background processing with status updates
    • Automatic timing coordination for multiple events
    • Thread-safe operation maintaining interface responsiveness

    CONFIGURATION PROFILES
    ----------------------
    • Complete configuration system via Tools → Configuration
    • Automatic saving of all settings
    • Reset to Defaults option available
    • Settings preserved across application restarts

    These advanced features provide professional-grade automation while maintaining ease of use for standard operations."""

    def get_tonights_events_content(self):  # (generated)
        return """TONIGHT'S EVENTS
    ================

    Complete automation for current-night observations via single button click.

    TONIGHT'S EVENTS BUTTON
    -----------------------
    Located in toolbar - provides one-click automation:
    1. Downloads latest events from OWC
    2. Automatically filters events for next 24 hours
    3. Selects all applicable events for your stations
    4. Generates sequence files using configured template
    5. Immediately begins automated execution
    6. Runs hands-off until completion

    AUTOMATIC FILTERING
    -------------------
    • Events occurring within next 24 hours
    • Events assigned to your configured stations
    • Events with valid timing and coordinate data
    • Events with future GOTO times only

    REQUIREMENTS
    ------------
    • Valid OWC credentials configured
    • Template file available in File Folder
    • SharpCap running and equipment connected
    • System stable for extended operation

    OPERATION
    ---------
    • Completely hands-off after initial button click
    • Background processing with status updates
    • Automatic timing coordination for all events
    • Continues through individual event failures
    • Status bar shows progress throughout night

    WHEN TO USE
    -----------
    • Beginning of observing sessions
    • Multiple events scheduled for one night
    • Reliable, tested observing setups
    • Minimal manual intervention desired

    Tonight's Events transforms the entire workflow into a single-click operation for experienced users with tested configurations."""

    def get_automation_content(self):  # (generated)
        return """AUTOMATION
    ==========

    Automated execution capabilities for reliable occultation observations.

    AUTOMATION LEVELS
    -----------------
    Manual Control:
    • Load sequences in SharpCap manually
    • User controls all timing and execution

    Semi-Automated:
    • Generate sequences with "Create Sequences"
    • Load and run manually in SharpCap

    Fully Automated:
    • Use "Run Sequences" for automatic execution
    • Use "Tonight's Events" for complete automation

    AUTOMATED SEQUENCE EXECUTION
    ----------------------------
    "Run Sequences" Button:
    • Executes selected events automatically
    • Manages timing coordination
    • Starts sequences at calculated GOTO times
    • Background operation with status updates
    • Continues through multiple events

    "Tonight's Events" Button:
    • Complete workflow automation
    • Downloads, filters, generates, and executes
    • Single-click operation for entire night

    TIMING AUTOMATION
    -----------------
    • Automatic GOTO time calculation with lead time
    • Precise UTC-based scheduling
    • Background execution at scheduled times
    • Thread-safe operation maintaining responsiveness

    BACKGROUND PROCESSING
    ---------------------
    • Sequences execute in background threads
    • Interface remains responsive during automation
    • Status updates show current operations
    • Individual event failures don't stop others

    REQUIREMENTS FOR AUTOMATION
    ---------------------------
    • SharpCap running and equipment connected
    • Valid sequence files for selected events
    • Events must have future GOTO times
    • System must remain running until completion

    Automation provides reliable hands-off operation while maintaining manual control options when needed."""

    def get_common_issues_content(self):  # (generated)
        return """COMMON ISSUES
    =============

    Frequently encountered problems and quick solutions.

    "NO EVENTS DOWNLOADED"
    ----------------------
    • Check OWC email/password in Tools → Configuration → Credentials
    • Verify API key in Tools → Configuration → API Settings
    • Confirm you have event assignments in OWC
    • Test login on OccultWatcher Cloud website

    "TEMPLATE NOT FOUND"
    -------------------
    • Place .txt file with "template" in filename in File Folder
    • Check File Folder path in Configuration is correct
    • Verify template file contains SharpCap commands
    • Use Browse button to confirm File Folder location

    "EMPTY SEQUENCE FILES"
    ---------------------
    • Check template uses correct variable syntax: {variable_name}
    • Verify template contains valid SharpCap commands
    • Ensure template file isn't corrupted
    • Test with different events

    "CANNOT CONNECT TO SHARPCAP"
    ---------------------------
    • Ensure SharpCap 4.1+ is running
    • Close other applications controlling SharpCap
    • Restart both applications
    • Check SharpCap isn't showing error dialogs

    "GOTO COMMANDS NOT WORKING"
    ---------------------------
    • Verify mount is connected in SharpCap
    • Test GOTO manually in SharpCap first
    • Check mount isn't parked or restricted
    • Ensure mount control is active

    "EVENTS GRID IS EMPTY"
    ---------------------
    • Click Download Events to get data from OWC
    • Check Station Filter - select "All Stations"
    • Use "All" quick filter to clear time filters
    • Verify File Folder contains occultations.json

    "SEQUENCES RUN AT WRONG TIMES"
    -----------------------------
    • Verify system clock is accurate
    • Check GOTO Lead Time setting in Configuration
    • Confirm events times are interpreted as UTC
    • Check timezone settings in Windows

    Most issues resolve by checking Configuration settings and ensuring all prerequisites are met."""

    def get_error_messages_content(self):  # (generated)
        return """ERROR MESSAGES
    ==============

    Common error messages and their solutions.

    DOWNLOAD ERRORS
    ---------------
    "HTTP Error: 401 - Unauthorized"
    • Check OWC email/password in Configuration
    • Verify API key is correct

    "HTTP Error: 403 - Forbidden"
    • Confirm email address is verified in OWC
    • Check API key has proper permissions

    "Connection timed out"
    • Check internet connection
    • Try downloading at different times

    FILE ERRORS
    -----------
    "Permission denied" / "Access denied"
    • Run application as administrator
    • Check folder permissions
    • Verify antivirus isn't blocking files

    "File not found" / "Path not found"
    • Check File Folder path in Configuration
    • Use Browse button to verify folder exists

    "Template not found or empty"
    • Place template.txt file in File Folder
    • Verify template contains content

    SHARPCAP ERRORS
    ---------------
    "SharpCap not found or not responding"
    • Ensure SharpCap 4.1+ is running
    • Restart both applications

    "Camera not available"
    • Connect camera in SharpCap first
    • Test camera manually in SharpCap

    "Mount not connected"
    • Connect mount in SharpCap mount panel
    • Test mount control manually

    AUTOMATION ERRORS
    -----------------
    "No future events selected"
    • Select events with future GOTO times
    • Check system clock is accurate

    "Sequence execution failed"
    • Check sequence files exist
    • Verify SharpCap is ready for automation

    Most error messages provide specific guidance for resolution. Check Configuration settings first for most issues."""

    def get_config_problems_content(self):  # (implemented)
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
    • Check key wasn't truncated when copying or had extra spaces
    
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
    • GOTO Lead Time should allow enough for your mount to plate solve and GOTO, including 1 plate solve retry
    • Consider site-specific timing requirements
    • Test with conservative values first

    Exposure Calculation Problems:
    • Magnitude reference affects all exposure calculations
    • Adjust based on your camera sensitivity
    • Test with known star magnitudes
    • Use custom exposures for critical events"""

    def get_night_mode_content(self):  # (implemented)
        return """NIGHT MODE
    ================

    Toggle Night Mode for an alternative color scheme.

    """
  

    
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
• Night vision preserving interface
• Station filtering and event management
• Template-based sequence customization

WORKFLOW:
Download → Filter → Prepare → Generate → Execute

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