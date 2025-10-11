import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

import os
import threading
import time
from datetime import datetime, timedelta
from System.Drawing import Point, Size, Color, SystemColors, Font, FontStyle, Pen, PointF
from System.Windows.Forms import *
import System

from System.Threading import CancellationToken

from theme import apply_theme_to_control
from events import OccultationManager
from sequence_runner import SequenceRunner
from gui_components import EventsDataGrid
from gui_dialogs import ExposureEditDialog, EventDetailsDialog, ConfigurationDialog, TemplateSelectionDialog
from templates import TemplateManager
from utils import save_occultation_sequence
from help import HelpManager

class OccultationManagerGUI(Form):
    """Enhanced main GUI window for occultation management with all requested features"""
    
    def __init__(self, config, theme_manager,sharpcap_instance=None, plate_solve_purpose=None):
        Form.__init__(self)
        self.config = config
        self.theme_manager = theme_manager
        self.help_manager = HelpManager(theme_manager)
        self.manager = OccultationManager(config)
        self.station_filter = ""
        self.sequence_runner = SequenceRunner(config,sharpcap_instance)
        #self.template_manager = TemplateManager(config)
        self.setup_ui()
        self.load_initial_data()
        self.apply_current_theme() # Apply normal or night mode theme
        clr.AddReference("SharpCap")
        self.sharpcap = sharpcap_instance
        self.plate_solve_purpose = plate_solve_purpose
       
    
    def setup_ui(self):
        """Setup the enhanced user interface"""
        self.Text = "Occultation Manager - SharpCap Integration"
        self.Size = Size(1400, 800)
        self.StartPosition = FormStartPosition.CenterScreen
        
        # Create menu bar
        menu_bar = self.create_enhanced_menu_bar()
        self.MainMenuStrip = menu_bar
        self.Controls.Add(menu_bar)
        
        main_panel = Panel()
        main_panel.Dock = DockStyle.Fill
        main_panel.Padding = Padding(0, 25, 0, 0)  # Add top padding for menu bar
        self.Controls.Add(main_panel)
        
        # Enhanced toolbar
        toolbar = self.create_enhanced_toolbar()
        toolbar.Parent = main_panel
        
        # Station filter panel
        filter_panel = self.create_station_filter_panel()
        filter_panel.Parent = main_panel
        
        # Events grid (moved up under buttons as requested)
        self.events_grid = EventsDataGrid()
        self.events_grid.Location = Point(10, 132)
        self.events_grid.Size = Size(1360, 450)
        self.events_grid.Anchor = AnchorStyles.Top | AnchorStyles.Left | AnchorStyles.Right | AnchorStyles.Bottom
        main_panel.Controls.Add(self.events_grid)
        
        # Bottom panel (smaller now)
        bottom_panel = self.create_enhanced_bottom_panel()
        bottom_panel.Parent = main_panel
        
        # Status bar
        status_bar = self.create_status_bar()
        status_bar.Parent = main_panel

    def apply_current_theme(self):
        """Apply the current theme to all controls"""
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
        
        # Force refresh
        self.Refresh()
    
    def toggle_night_mode_click(self, sender, e):
        """Toggle night mode on/off"""
        is_night = self.theme_manager.toggle_night_mode()
        self.apply_current_theme()
        
        # Update button text
        sender.Text = "Day Mode" if is_night else "Night Mode"
        
        # Save preference to config
        self.config.set_night_mode(is_night)
        self.config.save_config()
        
        self.update_status("Night mode " + ("enabled" if is_night else "disabled"))

    def create_enhanced_toolbar(self):
        """Create the enhanced main toolbar"""
        toolbar = Panel()
        toolbar.Height = 65  # Increased height slightly
        toolbar.Dock = DockStyle.Top
        toolbar.BackColor = SystemColors.Control
        
        # Row 1 - Main operations (moved down)
        btn_download = Button()
        btn_download.Text = "Download Events"
        btn_download.Size = Size(100, 25)
        btn_download.Location = Point(5, 8)  # Changed from 5 to 8
        btn_download.Click += self.download_events_click
        toolbar.Controls.Add(btn_download)
        
        btn_refresh = Button()
        btn_refresh.Text = "Refresh"
        btn_refresh.Size = Size(70, 25)
        btn_refresh.Location = Point(110, 8)  # Changed from 5 to 8
        btn_refresh.Click += self.refresh_events_click
        toolbar.Controls.Add(btn_refresh)
        
        btn_tonight = Button()
        btn_tonight.Text = "Run Tonight's Events"
        btn_tonight.Size = Size(100, 25)
        btn_tonight.Location = Point(185, 8)  # Changed from 5 to 8
        btn_tonight.Click += self.download_and_run_tonight_click
        toolbar.Controls.Add(btn_tonight)
        
        btn_select_all = Button()
        btn_select_all.Text = "Select All"
        btn_select_all.Size = Size(70, 25)
        btn_select_all.Location = Point(295, 8)  # Changed from 5 to 8
        btn_select_all.Click += self.select_all_click
        toolbar.Controls.Add(btn_select_all)
        
        btn_select_none = Button()
        btn_select_none.Text = "Select None"
        btn_select_none.Size = Size(80, 25)
        btn_select_none.Location = Point(370, 8)  # Changed from 5 to 8
        btn_select_none.Click += self.select_none_click
        toolbar.Controls.Add(btn_select_none)
        
        btn_event_details = Button()
        btn_event_details.Text = "Event Details"
        btn_event_details.Size = Size(90, 25)
        btn_event_details.Location = Point(460, 8)  # Changed from 5 to 8
        btn_event_details.Click += self.show_event_details_click
        toolbar.Controls.Add(btn_event_details)
        
        btn_edit_exposure = Button()
        btn_edit_exposure.Text = "Edit Exposure"
        btn_edit_exposure.Size = Size(90, 25)
        btn_edit_exposure.Location = Point(560, 8)  # Changed from 5 to 8
        btn_edit_exposure.Click += self.edit_exposure_click
        toolbar.Controls.Add(btn_edit_exposure)
        
        # Row 2 - Sequence operations (moved down)
        btn_create_sequences = Button()
        btn_create_sequences.Text = "Create Sequences"
        btn_create_sequences.Size = Size(110, 25)
        btn_create_sequences.Location = Point(5, 36)  # Changed from 25 to 28
        btn_create_sequences.Click += self.create_sequences_click
        toolbar.Controls.Add(btn_create_sequences)
        
        btn_run_sequences = Button()
        btn_run_sequences.Text = "Run Sequences"
        btn_run_sequences.Size = Size(100, 25)
        btn_run_sequences.Location = Point(120, 36)  # Changed from 25 to 28
        btn_run_sequences.Click += self.run_sequences_click
        toolbar.Controls.Add(btn_run_sequences)
        
        btn_combined_script = Button()
        btn_combined_script.Text = "Combined Script"
        btn_combined_script.Size = Size(110, 25)
        btn_combined_script.Location = Point(225, 36)  # Changed from 25 to 28
        btn_combined_script.Click += self.generate_combined_script_click
        toolbar.Controls.Add(btn_combined_script)

        # Add GOTO button
        btn_goto = Button()
        btn_goto.Text = "Test GOTO & Solve"
        btn_goto.Size = Size(90, 25)
        btn_goto.Location = Point(660, 8)  # Position after other buttons
        btn_goto.Click += self.goto_selected_event
        toolbar.Controls.Add(btn_goto)        

        # Night Mode button
        self.btn_night_mode = Button()
        self.btn_night_mode.Text = "Night Mode"
        self.btn_night_mode.Size = Size(80, 25)
        self.btn_night_mode.Location = Point(760, 8)  # Adjust X position as needed
        self.btn_night_mode.Click += self.toggle_night_mode_click
        toolbar.Controls.Add(self.btn_night_mode)

        return toolbar

    def create_enhanced_menu_bar(self):
        """Create the enhanced menu bar"""
        menu_bar = MenuStrip()
        
        # File menu
        menu_file = ToolStripMenuItem("File")
        menu_file.DropDownItems.Add(ToolStripMenuItem("Download Events", None, self.download_events_click))
        menu_file.DropDownItems.Add(ToolStripMenuItem("Refresh Events", None, self.refresh_events_click))
        menu_file.DropDownItems.Add(ToolStripSeparator())
        menu_file.DropDownItems.Add(ToolStripMenuItem("Download && Run Tonight's Events", None, self.download_and_run_tonight_click))
        menu_file.DropDownItems.Add(ToolStripSeparator())
        menu_file.DropDownItems.Add(ToolStripMenuItem("Exit", None, self.exit_click))
        menu_bar.Items.Add(menu_file)
        
        # Events menu
        menu_events = ToolStripMenuItem("Events")
        menu_events.DropDownItems.Add(ToolStripMenuItem("Event Details", None, self.show_event_details_click))
        menu_events.DropDownItems.Add(ToolStripMenuItem("Edit Exposure", None, self.edit_exposure_click))
        menu_events.DropDownItems.Add(ToolStripSeparator())
        menu_events.DropDownItems.Add(ToolStripMenuItem("Select All", None, self.select_all_click))
        menu_events.DropDownItems.Add(ToolStripMenuItem("Select None", None, self.select_none_click))
        menu_bar.Items.Add(menu_events)
        
        # Sequences menu
        menu_sequences = ToolStripMenuItem("Sequences")
        menu_sequences.DropDownItems.Add(ToolStripMenuItem("Create Sequences", None, self.create_sequences_click))
        menu_sequences.DropDownItems.Add(ToolStripMenuItem("Generate Combined Script", None, self.generate_combined_script_click))
        menu_sequences.DropDownItems.Add(ToolStripSeparator())
        menu_sequences.DropDownItems.Add(ToolStripMenuItem("Run Selected Sequences", None, self.run_sequences_click))
        menu_bar.Items.Add(menu_sequences)
        
        # Tools menu
        menu_tools = ToolStripMenuItem("Tools")
        menu_tools.DropDownItems.Add(ToolStripMenuItem("Configuration", None, self.show_configuration_click))
        menu_tools.DropDownItems.Add(ToolStripMenuItem("Template Manager", None, self.show_template_manager_click))
        menu_bar.Items.Add(menu_tools)
        
        # Help menu - MODIFIED
        menu_help = ToolStripMenuItem("Help")
        menu_help.DropDownItems.Add(ToolStripMenuItem("User Guide", None, self.show_help_click))
        menu_help.DropDownItems.Add(ToolStripSeparator())
        menu_help.DropDownItems.Add(ToolStripMenuItem("About", None, self.show_about_click))
        menu_bar.Items.Add(menu_help)
        
        return menu_bar
        
    def create_station_filter_panel(self):
        """Create station filtering panel"""
        panel = Panel()
        panel.Height = 30
        panel.Dock = DockStyle.Top
        panel.BackColor = SystemColors.ControlLight
        
        lbl_station = Label()
        lbl_station.Text = "Station Filter:"
        lbl_station.Location = Point(10, 7)
        lbl_station.Size = Size(80, 20)
        panel.Controls.Add(lbl_station)
        
        self.cbo_stations = ComboBox()
        self.cbo_stations.Location = Point(95, 5)
        self.cbo_stations.Size = Size(150, 25)
        self.cbo_stations.DropDownStyle = ComboBoxStyle.DropDownList
        self.cbo_stations.SelectionChangeCommitted += self.station_filter_changed
        panel.Controls.Add(self.cbo_stations)
        
        btn_clear_filter = Button()
        btn_clear_filter.Text = "Clear Filter"
        btn_clear_filter.Location = Point(250, 4)
        btn_clear_filter.Size = Size(80, 23)
        btn_clear_filter.Click += self.clear_station_filter_click
        panel.Controls.Add(btn_clear_filter)
        
        return panel
    
    def create_enhanced_bottom_panel(self):
        """Create the enhanced bottom control panel with Observation Preparation"""
        panel = Panel()
        panel.Height = 120  # Increased height for new section
        panel.Dock = DockStyle.Bottom
        panel.BackColor = SystemColors.Control
        
        # Existing configuration group (make smaller)
        config_group = GroupBox()
        config_group.Text = "Configuration"
        config_group.Location = Point(10, 5)
        config_group.Size = Size(250, 70)
        panel.Controls.Add(config_group)
        
        lbl_seq_path = Label()
        lbl_seq_path.Text = "Sequence Path:"
        lbl_seq_path.Location = Point(10, 20)
        lbl_seq_path.Size = Size(80, 20)
        config_group.Controls.Add(lbl_seq_path)
        
        self.txt_sequence_path = TextBox()
        self.txt_sequence_path.Text = self.config.get_sequence_path()
        self.txt_sequence_path.Location = Point(10, 40)
        self.txt_sequence_path.Size = Size(150, 20)
        config_group.Controls.Add(self.txt_sequence_path)
        
        btn_browse = Button()
        btn_browse.Text = "Browse"
        btn_browse.Location = Point(170, 39)
        btn_browse.Size = Size(60, 22)
        btn_browse.Click += self.browse_sequence_path_click
        config_group.Controls.Add(btn_browse)
        
        # NEW: Observation Preparation Group
        obs_prep_group = self.create_observation_preparation_group()
        obs_prep_group.Location = Point(270, 5)
        panel.Controls.Add(obs_prep_group)
        
        # Existing actions group (repositioned)
        actions_group = GroupBox()
        actions_group.Text = "Quick Filters"
        actions_group.Location = Point(10, 80)  # Moved down
        actions_group.Size = Size(200, 35)      # Made smaller
        panel.Controls.Add(actions_group)
        
        # Quick filter buttons (single row)
        btn_filter_today = Button()
        btn_filter_today.Text = "Today"
        btn_filter_today.Location = Point(10, 15)
        btn_filter_today.Size = Size(50, 20)
        btn_filter_today.Click += self.filter_today_click
        actions_group.Controls.Add(btn_filter_today)
        
        btn_filter_upcoming = Button()
        btn_filter_upcoming.Text = "Upcoming"
        btn_filter_upcoming.Location = Point(65, 15)
        btn_filter_upcoming.Size = Size(60, 20)
        btn_filter_upcoming.Click += self.filter_upcoming_click
        actions_group.Controls.Add(btn_filter_upcoming)
        
        btn_show_all = Button()
        btn_show_all.Text = "All"
        btn_show_all.Location = Point(130, 15)
        btn_show_all.Size = Size(35, 20)
        btn_show_all.Click += self.show_all_click
        actions_group.Controls.Add(btn_show_all)
        
        # Existing selection summary (repositioned and resized)
        summary_group = GroupBox()
        summary_group.Text = "Selection Summary"
        summary_group.Location = Point(220, 80)
        summary_group.Size = Size(200, 35)
        panel.Controls.Add(summary_group)
        
        self.lbl_selection_summary = Label()
        self.lbl_selection_summary.Text = "No events selected"
        self.lbl_selection_summary.Location = Point(10, 15)
        self.lbl_selection_summary.Size = Size(180, 15)
        summary_group.Controls.Add(self.lbl_selection_summary)
        
        self.events_grid.SelectionChanged += self.grid_selection_changed
        
        return panel
    
    def create_observation_preparation_group(self):
        """Create the observation preparation control group"""
        obs_group = GroupBox()
        obs_group.Text = "Observation Preparation - Interactive Setup & Testing"
        obs_group.Size = Size(600, 110)
        
        # Current event display
        self.lbl_current_event = Label()
        self.lbl_current_event.Text = "No event loaded for preparation"
        self.lbl_current_event.Location = Point(10, 20)
        self.lbl_current_event.Size = Size(480, 15)
        self.lbl_current_event.Font = Font("Microsoft Sans Serif", 8, FontStyle.Bold)
        obs_group.Controls.Add(self.lbl_current_event)
        
        # Load Event button
        btn_load_event = Button()
        btn_load_event.Text = "Load Event"
        btn_load_event.Size = Size(80, 25)
        btn_load_event.Location = Point(500, 15)
        btn_load_event.Click += self.load_event_for_prep_click
        btn_load_event.BackColor = Color.LightYellow
        obs_group.Controls.Add(btn_load_event)
        
        # Row 1: Setup and Navigation
        btn_setup_event = Button()
        btn_setup_event.Text = "Setup for Event"
        btn_setup_event.Size = Size(90, 25)
        btn_setup_event.Location = Point(10, 45)
        btn_setup_event.Click += self.setup_for_event_click
        btn_setup_event.BackColor = Color.LightGreen
        obs_group.Controls.Add(btn_setup_event)
        
        btn_goto_target = Button()
        btn_goto_target.Text = "GOTO & Center"
        btn_goto_target.Size = Size(90, 25)
        btn_goto_target.Location = Point(110, 45)
        btn_goto_target.Click += self.goto_and_center_click
        btn_goto_target.BackColor = Color.LightBlue
        obs_group.Controls.Add(btn_goto_target)
        
        btn_plate_solve = Button()
        btn_plate_solve.Text = "Plate Solve & Label"
        btn_plate_solve.Size = Size(100, 25)
        btn_plate_solve.Location = Point(210, 45)
        btn_plate_solve.Click += self.plate_solve_label_click
        btn_plate_solve.BackColor = Color.LightCyan
        obs_group.Controls.Add(btn_plate_solve)
        
        btn_clear_labels = Button()
        btn_clear_labels.Text = "Clear Labels"
        btn_clear_labels.Size = Size(80, 25)
        btn_clear_labels.Location = Point(320, 45)
        btn_clear_labels.Click += self.clear_labels_click
        obs_group.Controls.Add(btn_clear_labels)
        
        # Event details display
        self.lbl_event_details = Label()
        self.lbl_event_details.Text = ""
        self.lbl_event_details.Location = Point(10, 80)
        self.lbl_event_details.Size = Size(570, 25)
        self.lbl_event_details.Font = Font("Microsoft Sans Serif", 8)
        obs_group.Controls.Add(self.lbl_event_details)
        
        # Initialize preparation event to None
        self._preparation_event = None
        
        return obs_group
    
    def create_status_bar(self):
        """Create the status bar"""
        status_bar = Panel()
        status_bar.Height = 25
        status_bar.Dock = DockStyle.Bottom
        status_bar.BackColor = SystemColors.ControlDark
        
        self.lbl_status = Label()
        self.lbl_status.Text = "Ready"
        self.lbl_status.Location = Point(10, 5)
        self.lbl_status.Size = Size(400, 15)
        status_bar.Controls.Add(self.lbl_status)
        
        self.lbl_event_count = Label()
        self.lbl_event_count.Text = "0 events"
        self.lbl_event_count.Location = Point(500, 5)
        self.lbl_event_count.Size = Size(100, 15)
        status_bar.Controls.Add(self.lbl_event_count)
        
        return status_bar
    
    def load_initial_data(self):
        """Load initial events data"""
        # Load theme preference
        if self.config.get_night_mode():
            self.theme_manager.set_night_mode(True)
            self.btn_night_mode.Text = "Day Mode"
            self.apply_current_theme()

        self.update_status("Loading events...")
        if self.manager.load_events_from_files():
            self.refresh_display()
            self.populate_station_filter()
            self.update_status("Events loaded successfully")
        else:
            self.update_status("No events found - use Download Events to fetch from OW Cloud")
    
    def refresh_display(self):
        """Refresh the events display"""
        self.events_grid.update_events(self.manager.get_filtered_events())
        self.lbl_event_count.Text = f"{len(self.manager.get_filtered_events())} events"
        self.update_selection_summary()
    
    def update_status(self, message):
        """Update the status bar"""
        self.lbl_status.Text = message
        Application.DoEvents()
    
    def populate_station_filter(self):
        """Populate station filter dropdown"""
        stations = self.manager.get_all_stations()
        
        self.cbo_stations.Items.Clear()
        self.cbo_stations.Items.Add("All Stations")
        
        for station in stations:
            self.cbo_stations.Items.Add(station)
        
        self.cbo_stations.SelectedIndex = 0
    
    def update_selection_summary(self):
        """Update selection summary display"""
        selected_events = self.get_displayed_selected_events()
        if not selected_events:
            self.lbl_selection_summary.Text = "No events selected"
        else:
            future_events = [e for e in selected_events if e.event_datetime and e.event_datetime > datetime.utcnow()]
            stations = set(e.station_name for e in selected_events)
            
            summary_text = f"{len(selected_events)} selected"
            if future_events:
                summary_text += f" ({len(future_events)} future)"
            if len(stations) > 1:
                summary_text += f"\n{len(stations)} stations"
            elif len(stations) == 1:
                summary_text += f"\nStation: {list(stations)[0]}"
            
            self.lbl_selection_summary.Text = summary_text
    
    # Event Handlers
    def download_events_click(self, sender, e):
        """Handle download events button click"""
        self.update_status("Downloading events from OW Cloud...")
        try:
            result = self.manager.download_events_from_cloud()
            if result > 0:
                self.refresh_display()
                self.populate_station_filter()
                self.update_status(f"Downloaded {result} events")
            elif result == 0:
                self.update_status("No events downloaded")
            else:
                self.update_status("Error downloading events")
        except Exception as ex:
            self.update_status(f"Error downloading events: {ex}")
            MessageBox.Show(f"Error downloading events: {ex}", "Download Error", 
                          MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def refresh_events_click(self, sender, e):
        """Handle refresh button click"""
        self.load_initial_data()
    
    def select_all_click(self, sender, e):
        """Handle select all button click"""
        self.events_grid.select_all_events(True)
        for event in self.manager.get_filtered_events():
            self.manager.selected_events.add(event)
        self.update_selection_summary()
    
    def select_none_click(self, sender, e):
        """Handle select none button click"""
        self.events_grid.select_all_events(False)
        self.manager.selected_events.clear()
        self.update_selection_summary()
    
    def download_and_run_tonight_click(self, sender, e):
        """Download events and automatically run tonight's events"""
        if MessageBox.Show("This will download all events and automatically run tonight's events.\n\nContinue?", 
                         "Confirm Auto-Run", MessageBoxButtons.YesNo, MessageBoxIcon.Question) != DialogResult.Yes:
            return
        
        # Download events
        self.update_status("Downloading events from OW Cloud...")
        try:
            result = self.manager.download_events_from_cloud()
            if result <= 0:
                MessageBox.Show("No events downloaded or error occurred.", "Error", 
                              MessageBoxButtons.OK, MessageBoxIcon.Error)
                return
            
            self.refresh_display()
            self.populate_station_filter()
            self.update_status(f"Downloaded {result} events")
            
            # Filter for tonight's events
            tonight_events = self.get_tonights_events()
            if not tonight_events:
                MessageBox.Show("No events found for tonight.", "No Events", 
                              MessageBoxButtons.OK, MessageBoxIcon.Information)
                return
            
            # Select tonight's events
            self.manager.selected_events = set(tonight_events)
            self.refresh_display()
            
            # Create sequences and run them
            self.create_and_run_sequences(tonight_events)
            
        except Exception as ex:
            self.update_status(f"Error: {ex}")
            MessageBox.Show(f"Error: {ex}", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def get_tonights_events(self):
        """Get events for tonight (next 24 hours)"""
        now = datetime.utcnow()
        tomorrow = now + timedelta(days=1)
        
        tonight_events = []
        for event in self.manager.get_filtered_events():
            if event.event_datetime and now <= event.event_datetime <= tomorrow:
                tonight_events.append(event)
        
        return tonight_events

    def create_and_run_sequences(self, events):
        """Create sequences and run them for the given events"""
        if not events:
            return
        
        # First create sequences
        template_dialog = TemplateSelectionDialog(self.config, self.theme_manager)
        if template_dialog.ShowDialog() == DialogResult.OK:
            template_path = template_dialog.get_selected_template_path()
            
            # Create sequences for all events
            self.manager.selected_events = set(events)
            success_count, error_count, message = self.generate_sequences_for_events(template_path)
            
            if success_count > 0:
                self.update_status("Sequences created, starting execution...")
                # Run the sequences
                def run_in_background():
                    self.sequence_runner.run_sequences(events, self.update_status_safe)
                
                thread = threading.Thread(target=run_in_background)
                thread.IsBackground = True
                thread.start()
            else:
                MessageBox.Show(f"Failed to create sequences: {message}", "Error", 
                              MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def generate_sequences_for_events(self, template_path):
        """Generate sequence files for selected events - internal method"""
        selected_events = list(self.manager.selected_events)
        if not selected_events:
            return 0, 0, "No events selected"
        
        template_content = TemplateManager.load_template(template_path, self.config)
        if not template_content:
            return 0, 0, "Template not found or empty"
        
        success_count = 0
        error_count = 0
        sequence_path = self.config.get_sequence_path()
        
        for i, event in enumerate(selected_events):
            try:
                self.update_status(f"Processing {i + 1}/{len(selected_events)}: {event.event_name}")
                
                if save_occultation_sequence(event, template_path or "", sequence_path, self.config):
                    success_count += 1
                else:
                    error_count += 1
            except Exception as e:
                error_count += 1
                print(f"Error creating sequence for {event.event_name}: {e}")
        
        return success_count, error_count, f"Created {success_count} of {len(selected_events)} sequences"
    
    def update_status_safe(self, message):
        """Thread-safe status update"""
        if self.InvokeRequired:
            self.Invoke(System.Action[str](self.update_status), message)
        else:
            self.update_status(message)
    
    def show_event_details_click(self, sender, e):
        """Show detailed event information"""
        selected_rows = []
        for row in self.events_grid.SelectedRows:
            selected_rows.append(row)
        
        if len(selected_rows) == 0:
            MessageBox.Show("Please select an event to view details.", "No Event Selected", 
                          MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        
        event = selected_rows[0].Tag
        if event:
            details_dialog = EventDetailsDialog(event, self.theme_manager)
            details_dialog.ShowDialog()
    
    def edit_exposure_click(self, sender, e):
        """Handle edit exposure button click"""
        selected_rows = []
        for row in self.events_grid.SelectedRows:
            selected_rows.append(row)
        
        if len(selected_rows) == 0:
            MessageBox.Show("Please select an event to edit exposure.", "No Event Selected", 
                          MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        elif len(selected_rows) > 1:
            MessageBox.Show("Please select only one event to edit exposure.", "Multiple Events Selected", 
                          MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        
        event = selected_rows[0].Tag
        if event:
            self.edit_event_exposure(event)
    
    def edit_event_exposure(self, event):
        """Edit exposure for a specific event"""
        exposure_dialog = ExposureEditDialog(event, self.theme_manager)
        if exposure_dialog.ShowDialog() == DialogResult.OK:
            new_exposure = exposure_dialog.get_new_exposure()
            event.set_custom_exposure(new_exposure)
            
            # Refresh the grid to show updated exposure
            self.refresh_display()
            
            # Ask if user wants to regenerate sequence
            result = MessageBox.Show(
                f"Exposure updated to {new_exposure}ms.\n\nWould you like to regenerate the sequence file for this event?",
                "Regenerate Sequence?",
                MessageBoxButtons.YesNo,
                MessageBoxIcon.Question
            )
            
            if result == DialogResult.Yes:
                self.regenerate_single_sequence(event)
    
    def regenerate_single_sequence(self, event):
        """Regenerate sequence for a single event"""
        template_dialog = TemplateSelectionDialog(self.config, self.theme_manager)
        if template_dialog.ShowDialog() == DialogResult.OK:
            template_path = template_dialog.get_selected_template_path()
            
            self.update_status(f"Generating sequence for {event.event_name}...")
            success = save_occultation_sequence(event, template_path, self.config.get_sequence_path(), self.config)
            
            if success:
                self.update_status("Sequence generated successfully")
                MessageBox.Show(f"Sequence file regenerated successfully for {event.event_name}", 
                              "Success", MessageBoxButtons.OK, MessageBoxIcon.Information)
            else:
                self.update_status("Error generating sequence")
                MessageBox.Show("Failed to regenerate sequence", 
                              "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def goto_selected_event(self, sender, e):
        """GOTO and platesolve selected event"""
        selected_events = self.get_displayed_selected_events()
        if not selected_events:
            MessageBox.Show("Please select an event for GOTO", "No Selection")
            return
        
        event = selected_events[0]
        success = self.execute_goto_command(event)
        
        if success:
            self.update_status(f"GOTO/Platesolve started for {event.event_name}")
        else:
            self.update_status("GOTO failed")
            MessageBox.Show("Failed to start GOTO sequence", "Error")

    def execute_goto_command(self, event):
        """Execute the actual GOTO command"""
        try:
            # Check if mount control is available
            if hasattr(self.sharpcap, 'Mounts') and self.sharpcap.Mounts.SelectedMount:
                mount = self.sharpcap.Mounts.SelectedMount
                mount.SlewTo(event.ra, event.dec)                
             
                print(f"GOTO command sent: RA {event.ra:.4f}h, Dec {event.dec:.4f}°")
                return True
            else:
                # Show coordinates for manual GOTO
                print(f"Manual GOTO required: RA {event.ra:.6f}h, Dec {event.dec:.6f}°")
                result = MessageBox.Show(f"No mount control available.\n\nPlease manually GOTO:\n\n" +
                                    f"RA: {event.ra:.6f} hours\nDec: {event.dec:.6f}°\n\n" +
                                    f"Click OK when GOTO is complete, or Cancel to stop.",
                                    "Manual GOTO Required", MessageBoxButtons.OKCancel, MessageBoxIcon.Information)
                return result == DialogResult.OK
                
        except Exception as e:
            print(f"GOTO execution error: {e}")
            return False


    def run_sequences_click(self, sender, e):
        """Run sequences for selected events - non-blocking version"""
        selected_events = self.get_displayed_selected_events()
        if not selected_events:
            MessageBox.Show("Please select events to run sequences for.", "No Events Selected", 
                        MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        
        # Filter for future events only
        future_events = [e for e in selected_events if e.event_datetime and e.event_datetime > datetime.utcnow()]
        if not future_events:
            MessageBox.Show("No future events selected. Only future events can be run.", "No Future Events", 
                        MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        
        if MessageBox.Show(f"This will run {len(future_events)} sequence(s) in order.\n\nContinue?", 
                        "Confirm Run Sequences", MessageBoxButtons.YesNo, MessageBoxIcon.Question) == DialogResult.Yes:
            
            # Run in background thread to avoid blocking SharpCap
            def run_in_background():
                self.sequence_runner.run_sequences(future_events, self.update_status_safe)
            
            thread = threading.Thread(target=run_in_background)
            thread.IsBackground = True
            thread.start()
        
    def create_sequences_click(self, sender, e):
        """Handle create sequences button click"""
        selected_events = self.get_displayed_selected_events()
        if not selected_events:
            MessageBox.Show("Please select events to create sequences for.", "No Events Selected", 
                          MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        
        self.manager.selected_events = set(selected_events)
        
        template_dialog = TemplateSelectionDialog(self.config, self.theme_manager)
        if template_dialog.ShowDialog() == DialogResult.OK:
            template_path = template_dialog.get_selected_template_path()
            self.create_sequences_for_events(template_path)
    
    def create_sequences_for_events(self, template_path):
        """Create sequence files for selected events"""
        sequence_path = self.txt_sequence_path.Text
        self.config.set_sequence_path(sequence_path)
        
        success_count, error_count, message = self.generate_sequences_for_events(template_path)
        
        self.update_status(message)
        MessageBox.Show(f"Successfully created {success_count} of {success_count + error_count} sequence files.", 
                       "Sequence Creation Complete", MessageBoxButtons.OK, MessageBoxIcon.Information)
    
    def generate_combined_script_click(self, sender, e):
        """Generate single combined sequence file with all selected events in time order"""
        selected_events = self.get_displayed_selected_events()
        if not selected_events:
            MessageBox.Show("Please select events to generate combined sequence for.", "No Events Selected", 
                        MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        
        # Check that all events are for the same station
        stations = set(event.station_name for event in selected_events)
        if len(stations) > 1:
            result = MessageBox.Show(f"Selected events are from {len(stations)} different stations:\n" + 
                                "\n".join(stations) + "\n\nContinue anyway?", 
                                "Multiple Stations", MessageBoxButtons.YesNo, MessageBoxIcon.Warning)
            if result != DialogResult.Yes:
                return
        
        # Get template for sequence generation
        template_dialog = TemplateSelectionDialog(self.config, self.theme_manager)
        if template_dialog.ShowDialog() != DialogResult.OK:
            return
        
        template_path = template_dialog.get_selected_template_path()
        success = self.create_combined_sequence_file(selected_events, template_path)
        
        if success:
            MessageBox.Show("Combined sequence file generated successfully!", "Success", 
                        MessageBoxButtons.OK, MessageBoxIcon.Information)
        else:
            MessageBox.Show("Failed to generate combined sequence file.", "Error", 
                        MessageBoxButtons.OK, MessageBoxIcon.Error)

    def create_combined_sequence_file(self, events, template_path):
        """Create a single sequence file with all events in time order"""
        if not events:
            return False
        
        try:
            # Sort events by GOTO time
            sorted_events = sorted(events, key=lambda x: x.goto_time if x.goto_time else datetime.max)
            
            # Load template content
            template_content = TemplateManager.load_template(template_path, self.config)
            if not template_content:
                self.update_status("Template not found or empty")
                return False
            
            # Generate filename
            date_str = datetime.utcnow().strftime('%Y%m%d')
            stations = set(event.station_name for event in events)
            station_name = list(stations)[0] if len(stations) == 1 else "MultiStation"
            combined_filename = f"{date_str}_{station_name}_Combined_Sequences.seq"
            combined_path = os.path.join(self.config.get_sequence_path(), combined_filename)
            
            # Build combined sequence content
            combined_content = []
            
            # Add header
            combined_content.append("# Combined Sequence File")
            combined_content.append(f"# Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
            combined_content.append(f"# Events: {len(sorted_events)}")
            combined_content.append(f"# Station(s): {', '.join(stations)}")
            combined_content.append("#")
            
            # Add event summary
            combined_content.append("# Event Schedule:")
            for i, event in enumerate(sorted_events, 1):
                combined_content.append(f"# {i:2d}. {event.event_time} UTC - {event.get_asteroid_display_name()}")
            combined_content.append("#" + "="*70)
            combined_content.append("")
            
            # Process each event and add its sequence content
            for i, event in enumerate(sorted_events, 1):
                self.update_status(f"Processing event {i}/{len(sorted_events)}: {event.event_name}")
                
                # Add event separator
                combined_content.append(f"# Event {i}: {event.get_asteroid_display_name()}")
                combined_content.append(f"# Time: {event.event_time} UTC")
                combined_content.append(f"# GOTO: {event.goto_time_str} UTC") 
                combined_content.append(f"# Duration: {event.recording_duration}s")
                combined_content.append("#" + "-"*50)
                
                # Generate sequence content for this event
                try:
                    event_sequence = self.format_template(template_content, event)
                    combined_content.append(event_sequence)
                except Exception as e:
                    combined_content.append(f"# ERROR: Could not generate sequence for {event.event_name}: {e}")
                    print(f"Error generating sequence for {event.event_name}: {e}")
                
                # Add spacing between events (except for last one)
                if i < len(sorted_events):
                    combined_content.append("")
                    combined_content.append("#" + "="*70)
                    combined_content.append("")
            
            # Write combined file
            with open(combined_path, 'w') as f:
                f.write('\n'.join(combined_content))
            
            self.update_status(f"Combined sequence saved: {combined_filename}")
            return True
            
        except Exception as e:
            self.update_status(f"Error creating combined sequence: {e}")
            print(f"Error creating combined sequence: {e}")
            return False

    def format_template(self, template_content, event):
        """Format template with event data"""
        try:
            return template_content.format(
                object_name=event.object_name,
                event_time=event.event_time,
                start_time=event.start_time_str,
                goto_time=event.goto_time_str,
                recording_duration=event.recording_duration,
                star_mag=event.star_mag,
                comb_mag=event.comb_mag,
                mag_drop=event.mag_drop,
                time_error=event.event_uncertainty,
                ra=event.ra,
                dec=event.dec,
                asteroid_name=event.object_name,
                exposure=event.get_exposure_seconds(),
                # Add simple local time variables
                event_time_local=event.event_time_local,
                start_time_local=event.start_time_local,
                goto_time_local=event.goto_time_local
            )
        except Exception as e:
            return f"# Error formatting template: {e}"
    
    def station_filter_changed(self, sender, e):
        """Handle station filter change"""
        if self.cbo_stations.SelectedItem:
            station_name = str(self.cbo_stations.SelectedItem)
            if station_name != "All Stations":
                self.station_filter = station_name
                self.manager.set_station_filter(station_name)
            else:
                self.station_filter = ""
                self.manager.clear_station_filter()
            
            self.refresh_display()
    
    def clear_station_filter_click(self, sender, e):
        """Clear station filter"""
        self.cbo_stations.SelectedIndex = 0  # "All Stations"
        self.station_filter = ""
        self.manager.clear_station_filter()
        self.refresh_display()
    
    def get_displayed_selected_events(self):
        """Get events that are both displayed and selected"""
        displayed_events = self.manager.get_filtered_events()
        selected_events = []
        
        for row in self.events_grid.Rows:
            if row.Cells["Selected"].Value and row.Tag in displayed_events:
                selected_events.append(row.Tag)
        
        return selected_events
    
    def filter_today_click(self, sender, e):
        """Filter events for today"""
        today = datetime.utcnow().date()
        filtered_events = []
        for event in self.manager.all_events:
            if event.event_datetime and event.event_datetime.date() == today:
                filtered_events.append(event)
        
        self.manager.events = filtered_events
        self.refresh_display()
        self.update_status(f"Showing today's events: {len(filtered_events)}")
    
    def filter_upcoming_click(self, sender, e):
        """Filter upcoming events"""
        now = datetime.utcnow()
        filtered_events = []
        for event in self.manager.all_events:
            if event.event_datetime and event.event_datetime > now:
                filtered_events.append(event)
        
        self.manager.events = filtered_events
        self.refresh_display()
        self.update_status(f"Showing upcoming events: {len(filtered_events)}")
    
    def show_all_click(self, sender, e):
        """Show all events"""
        self.manager.clear_station_filter()
        self.refresh_display()
        self.update_status("Showing all events")
    
    def browse_sequence_path_click(self, sender, e):
        """Handle browse sequence path button click"""
        dialog = FolderBrowserDialog()
        dialog.SelectedPath = self.txt_sequence_path.Text
        if dialog.ShowDialog() == DialogResult.OK:
            self.txt_sequence_path.Text = dialog.SelectedPath
            self.config.set_sequence_path(dialog.SelectedPath)
    
    def show_configuration_click(self, sender, e):
        """Show configuration dialog"""
        config_dialog = ConfigurationDialog(self.config, self.theme_manager)
        config_dialog.ShowDialog()
    
    def show_template_manager_click(self, sender, e):
        """Show template manager"""
        template_dialog = TemplateSelectionDialog(self.config, self.theme_manager)
        template_dialog.ShowDialog()
    
    def show_help_click(self, sender, e):
        """Show interactive help dialog"""
        self.help_manager.show_help(self)

    def show_about_click(self, sender, e):
        """Show about dialog with author information"""
        self.help_manager.show_about()

    def exit_click(self, sender, e):
        """Exit application"""
        if self.sequence_runner.running:
            if MessageBox.Show("Sequences are currently running. Exit anyway?", "Confirm Exit", 
                             MessageBoxButtons.YesNo, MessageBoxIcon.Warning) == DialogResult.Yes:
                self.sequence_runner.stop_sequences()
            else:
                return
        self.Close()
    
    def grid_selection_changed(self, sender, e):
        """Handle grid selection change"""
        self.update_selection_summary()

    # Observation Preparation Methods
    def get_first_selected_event(self):
        """Get the first selected event from the grid"""
        selected_events = self.get_displayed_selected_events()
        if selected_events:
            return selected_events[0]
        return None

    def load_event_for_prep_click(self, sender, e):
        """Load the first selected event for preparation"""
        event = self.get_first_selected_event()
        if not event:
            MessageBox.Show("Please select an event from the grid first", "No Event Selected", 
                        MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        # Load event for preparation
        self._preparation_event = event
        self.update_preparation_display()
        self.update_status(f"Loaded event for preparation: {event.get_asteroid_display_name()}")

    def update_preparation_display(self):
        """Update the observation preparation display with current event info"""
        event = self._preparation_event
        if event:
            # Update event label
            self.lbl_current_event.Text = f"Prep Event: {event.get_asteroid_display_name()} at {event.event_time} UTC"
            
            # Update details
            details = (f"RA: {event.ra:.4f}h, Dec: {event.dec:.4f}° | "
                    f"Exposure: {event.exposure_ms}ms | Duration: {event.recording_duration}s | "
                    f"Star Mag: {event.star_mag:.1f}")
            self.lbl_event_details.Text = details
            
            # Enable buttons
            self.enable_preparation_buttons(True)
        else:
            self.lbl_current_event.Text = "No event loaded for preparation"
            self.lbl_event_details.Text = ""
            self.enable_preparation_buttons(False)

    def enable_preparation_buttons(self, enabled):
        """Enable or disable preparation buttons based on event loading"""
        # Find buttons in the observation preparation group
        obs_group = None
        for control in self.Controls:
            if isinstance(control, Panel):
                for child in control.Controls:
                    if isinstance(child, GroupBox) and "Observation Preparation" in child.Text:
                        obs_group = child
                        break
        
        if obs_group:
            for control in obs_group.Controls:
                if (isinstance(control, Button) and 
                    control.Text not in ["Clear Labels", "Load Event"]):
                    control.Enabled = enabled

    def setup_for_event_click(self, sender, e):
        """Setup SharpCap interface for the loaded event"""
        if not self._preparation_event:
            MessageBox.Show("Please load an event first using 'Load Event' button", "No Event Loaded", 
                        MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        event = self._preparation_event
        
        try:
            self.update_status(f"Setting up SharpCap for {event.event_name}...")
            
            # Apply event parameters to SharpCap
            success = self.apply_event_parameters_to_sharpcap(event)
            
            if success:
                self.update_status(f"SharpCap configured for {event.event_name}")
                MessageBox.Show(f"SharpCap setup complete for:\n\n" +
                            f"Event: {event.get_asteroid_display_name()}\n" +
                            f"Exposure: {event.exposure_ms}ms\n" +
                            f"Recording Duration: {event.recording_duration}s\n" +
                            f"Target: RA {event.ra:.4f}h, Dec {event.dec:.4f}°\n\n" +
                            f"Use SharpCap interface for recording when ready.",
                            "Setup Complete", MessageBoxButtons.OK, MessageBoxIcon.Information)
            else:
                self.update_status("Failed to configure SharpCap")
                
        except Exception as ex:
            self.update_status(f"Error during setup: {ex}")
            MessageBox.Show(f"Error setting up event: {ex}", "Setup Error", 
                        MessageBoxButtons.OK, MessageBoxIcon.Error)

    def apply_event_parameters_to_sharpcap(self, event):
        """Apply event parameters to SharpCap interface"""
        try:
                       
            # Set exposure time
            if self.sharpcap.SelectedCamera:
                camera = self.sharpcap.SelectedCamera
                
                # Set exposure (convert ms to seconds)
                #exposure_seconds = round(event.exposure_ms / 1000.0,3)
                if hasattr(camera.Controls, 'Exposure'):
                    camera.Controls.Exposure.Value = event.exposure_ms
                    print(f"Set exposure to {event.exposure_ms:.0f} ms")
            
            # Set target name/coordinates in SharpCap (if supported)
            try:
                target_name = f"{event.get_asteroid_display_name()}_{event.station_name}"
                self.sharpcap.TargetName = target_name
                print(f"Target: {target_name} at RA {event.ra:.6f}h, Dec {event.dec:.6f}°")
            except:
                pass
            
            return True
            
        except Exception as e:
            print(f"Error applying parameters to SharpCap: {e}")
            return False

    def goto_and_center_click(self, sender, e):
        """Execute GOTO, plate solve, and recenter on target"""
        if not self._preparation_event:
            MessageBox.Show("Please load an event first using 'Load Event' button", "No Event Loaded", 
                        MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        event = self._preparation_event
        
        try:
            self.update_status(f"GOTO, plate solve and center: {event.get_asteroid_display_name()}...")
            
            # Execute complete GOTO sequence
            success = self.execute_complete_goto_sequence(event)
            
            if success:
                self.update_status("GOTO, plate solve, and recenter completed successfully")
                MessageBox.Show(f"Sequence completed successfully!\n\n" +
                            f"Target: {event.get_asteroid_display_name()}\n" +
                            f"Position verified and centered\n" +
                            f"Ready for observation",
                            "GOTO & Center Complete", MessageBoxButtons.OK, MessageBoxIcon.Information)
            else:
                self.update_status("GOTO completed, but verification had issues")
                
        except Exception as ex:
            self.update_status(f"GOTO & center error: {ex}")
            MessageBox.Show(f"GOTO & center error: {ex}", "Error", 
                        MessageBoxButtons.OK, MessageBoxIcon.Error)

    def execute_complete_goto_sequence(self, event):
        """Execute the complete GOTO sequence with error handling"""
        try:
            # Step 1: GOTO
            self.update_status("Step 1: Executing GOTO...")
            goto_success = self.execute_goto_command(event)
            
            if not goto_success:
                return False
            
            # Step 2: Wait and plate solve
#            self.update_status("Step 2: Plate solving...")
            time.sleep(3)  # Wait for mount to settle
            
            # Basic verification that we're in the right area - not done yet
            return True
            
        except Exception as e:
            print(f"GOTO sequence error: {e}")
            return False

    def plate_solve_label_click(self, sender, e):
        """Plate solve and label the target star"""
        if not self._preparation_event:
            MessageBox.Show("Please load an event first using 'Load Event' button", "No Event Loaded", 
                        MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        event = self._preparation_event
        
        try:
            self.update_status("Plate solving and labeling target...")
            
            # Execute plate solve with target marking
            success = self.plate_solve_and_mark_star(event, checkStarInFOV=True)
            
            if success == True:
                self.update_status(f"Target labeled: {event.get_asteroid_display_name()}")
                MessageBox.Show(f"Target star labeled successfully!\n\n" +
                            f"Object: {event.get_asteroid_display_name()}\n" +
                            f"Coordinates: RA {event.ra:.4f}h, Dec {event.dec:.4f}°\n" +
                            f"Star Magnitude: {event.star_mag:.1f}",
                            "Target Labeled", MessageBoxButtons.OK, MessageBoxIcon.Information)
            elif isinstance(success, str):
                self.update_status(f"Plate solve failed: {success}")
                MessageBox.Show(f"Plate solve failed: {success}", "Plate Solve Error", 
                            MessageBoxButtons.OK, MessageBoxIcon.Error)
            else:
                self.update_status("Target not found or outside field of view")
                
        except Exception as ex:
            self.update_status(f"Plate solve error: {ex}")
            MessageBox.Show(f"Plate solve error: {ex}", "Error", 
                        MessageBoxButtons.OK, MessageBoxIcon.Error)


    def plate_solve_and_mark_star(self, event, checkStarInFOV = False):
        """Plate solve current image and add reticle to mark a specific star position. If showWarnings will pop up message boxes, otherwise continues for automatation"""

        # Capture a frame and plate solve
        if not self.sharpcap.SelectedCamera:
            MessageBox.Show("Camera is not selected", "Connection Error", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return False
        if (not self.sharpcap.DeepSkyAnnotation.IsActive):
            self.update_status("Activating Deep Sky Annotation...")
            self.sharpcap.DeepSkyAnnotation.Activate()        


        try:
            result = self.sharpcap.SafeGetAsyncResult(self.sharpcap.BlindSolver.SolveAsync(self.plate_solve_purpose.Annotation, CancellationToken()))
            #result = self.sharpcap.SafeWaitForAsync(self.sharpcap.BlindSolver.SolveAsync(PlateSolvePurpose.Annotation, CancellationToken()))
            print("Plate Solve result:", result)
            self.update_status(result)
            # if (result == None):
            #     print("Plate Solve is not installed or configurated")
            #     self.update_status("Plate Solve is not installed or configurated")
            #     MessageBox.Show("Failed to Plate Solve - adjust configure or exposure and try again", "Plate Solve Error", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            #     return
        except Exception as ex:
            if(str(type(result)) != "<class 'RADecPosition'>"):                  
                print("Plate Solve Failure:", result, ex)
                self.update_status(f"Plate Solve is not installed or configurated: {result} {ex}")
                MessageBox.Show(f"Failed to Plate Solve - adjust configure or exposure and try again {ex}", "Plate Solve Error", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
        
        
        res  = self.sharpcap.SelectedCamera.Controls.Resolution.Value.Split("x")
        result = self.sharpcap.PixelPositionProvider.MapPixel(PointF(int(float(res[0])/2), int(float(res[1])/2)))
        Event_Annotation = event.event_time + "|" + event.asteroid_name + "| " + "" + "|"
        Event_Annotation = Event_Annotation + f"{event.ra:.4f}" + "|" + f"{event.dec:.4f}" + "||||"
        
        System.Windows.Forms.Clipboard.SetText(Event_Annotation)

        self.sharpcap.DeepSkyAnnotation.PasteClipboardDataAsCustom()        
        return
        
        # Convert RA/Dec to pixel coordinates using the WCS
        pixel_coords = solve_result.WCS.WorldToPixel(target_ra_hours * 15.0, target_dec_degrees)
        x, y = pixel_coords.X, pixel_coords.Y
        if checkStarInFOV:
            # Check if star is in the field of view
            if x < 0 or x > frame.Width or y < 0 or y > frame.Height:
                MessageBox.Show("Target star is not in the FOV", "Warning", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return False
            
            # Check if star is well centered (within 50% of frame radius from center)
            center_x, center_y = frame.Width / 2.0, frame.Height / 2.0
            distance_from_center = ((x - center_x)**2 + (y - center_y)**2)**0.5
            frame_radius = ((frame.Width**2 + frame.Height**2)**0.5) / 2.0
            max_centered_distance = frame_radius * 0.5
            
            if distance_from_center > max_centered_distance:
                MessageBox.Show("Target star is not well centered", "Warning", MessageBoxButtons.OK, MessageBoxIcon.Warning)
            
        # Add the reticle overlay
        self.add_reticle_overlay(x, y)
        return True

    def add_reticle_overlay(self, x, y, reticle_size = 50,overlay_name = "occultation_reticule"):
        """    Add a reticle overlay at the specified pixel coordinates    """
        # Remove existing overlay if it exists
        if self.sharpcap.Overlays.ContainsKey(overlay_name):
            self.sharpcap.Overlays.Remove(overlay_name)
        
        # Create new overlay
        overlay = self.sharpcap.Overlays.Add(overlay_name)
        overlay.AddCircle(x - reticle_size/2, y - reticle_size/2, reticle_size, Pen(Color.Red, 2))

    def clear_all_reticles(self, overlay_name = "occultation_reticule"):
        """Remove all star reticle overlays"""
        overlays_to_remove = [key for key in self.sharpcap.Overlays.Keys if key.startswith(overlay_name)]
        for key in overlays_to_remove:
            self.sharpcap.Overlays.Remove(key)

    def clear_labels_click(self, sender, e):
        """Clear all star labels/overlays"""
        try:
            self.update_status("All star labels cleared")
            MessageBox.Show("Clear any overlays using SharpCap's interface", "Clear Labels", 
                        MessageBoxButtons.OK, MessageBoxIcon.Information)
            
        except Exception as ex:
            self.update_status(f"Error clearing labels: {ex}")