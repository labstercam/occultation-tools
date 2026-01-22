import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("System")

import os
import sys
import threading
import time
import webbrowser

from datetime import datetime, timedelta
from System.Drawing import Point, Size, Color, SystemColors, Font, FontStyle, Pen, PointF
from System.Windows.Forms import (
    Form, Panel, MenuStrip, Button, Label, ComboBox, ComboBoxStyle,
    ToolStripMenuItem, ToolStripSeparator, FolderBrowserDialog, GroupBox,
    TextBox, DataGridView, AnchorStyles, DockStyle, Padding, Application,
    MessageBox, MessageBoxButtons, MessageBoxIcon, DialogResult, FormStartPosition, Clipboard,
    LinkLabel
)
from System.Diagnostics import Process
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
# na_report import moved to lazy load in generate_report_click() to avoid crashes

class OccultationManagerGUI(Form):
    """Enhanced main GUI window for occultation management with all requested features"""
    
    def __init__(self, config, theme_manager,sharpcap_instance=None, plate_solve_purpose=None,coordinateParser = None):
        Form.__init__(self)
        self.config = config
        self.theme_manager = theme_manager
        
        # Disable automatic DPI scaling since we handle it manually
        # Use integer value 0 instead of AutoScaleMode.None (which conflicts with Python's None keyword)
        from System.Windows.Forms import AutoScaleMode
        self.AutoScaleMode = 0  # AutoScaleMode.None = 0
        
        # Ensure a control handle exists early so we can reliably detect DPI
        try:
            # CreateControl is harmless if handle already exists; it helps Graphics.FromHwnd succeed
            self.CreateControl()
        except Exception:
            pass

        # Detect current scale factor and category (100/125/150)
        self._scale_factor, self._scale_category = self._detect_scale()

        # Centralized size constants — use these in later layout changes so all values
        # are derived from a single source of truth. Values are base (100%) pixels
        # multiplied by detected scale factor.
        try:
            sf = float(self._scale_factor)
        except Exception:
            sf = 1.0

        self.size_constants = {
            # Heights
            'toolbar_height': int(round(44 * sf)),
            'bottom_reserved_height': int(round(90 * sf)),
            'status_height': int(round(25 * sf)),
            'button_height': int(round(25 * sf)),

            # Widths
            'quick_group_width': int(round(310 * sf)),
            'obs_group_width': int(round(1150 * sf)),

            # Layout - now scaled
            'gap': int(round(4 * sf)),
            'start_x': int(round(10 * sf)),
            'toolbar_start_x': int(round(6 * sf)),
            # Move toolbar buttons down a couple of pixels to avoid crowding the menu
            'toolbar_start_y': int(round(18 * sf)),
            # Fixed pixel nudge (not scaled) to ensure toolbar buttons sit below
            # the MenuStrip regardless of font metrics. Adjust if overlap occurs.
            # Increased per user request from 6 -> 8 px for a stronger nudge.
            'toolbar_fixed_nudge': 8,
            # Extra button height (px) to avoid clipped button borders at high DPI
            'toolbar_button_extra': int(round(4 * sf)),
        }
        self.help_manager = HelpManager(theme_manager)
        self.manager = OccultationManager(config)
        self.station_filter = ""
        self.sequence_runner = SequenceRunner(config,sharpcap_instance)
        #self.template_manager = TemplateManager(config)
        self.report_generator = None  # Lazy load when needed to avoid import issues
        self.setup_ui()
        self.load_initial_data()
        self.apply_current_theme() # Apply normal or night mode theme
        clr.AddReference("SharpCap")
        self.sharpcap = sharpcap_instance
        self.plate_solve_purpose = plate_solve_purpose
        self.CoordinateParser = coordinateParser
       
    
    def OnLoad(self, e):
        """Override OnLoad to ensure proper DPI detection and window sizing after form is created"""
        Form.OnLoad(self, e)
        # Re-detect scale factor now that handle is definitely created
        self._scale_factor, self._scale_category = self._detect_scale()
        
        # Calculate form size based on event grid column widths
        try:
            # Sum up all column widths from the events grid
            total_grid_width = 0
            for col in self.events_grid.Columns:
                total_grid_width += col.Width
            
            # Add padding for scrollbar, borders, and margins
            sf = getattr(self, '_scale_factor', 1.0)
            scrollbar_width = int(round(20 * sf))
            border_padding = int(round(40 * sf))
            
            # Calculate minimum width needed for the grid
            min_form_width = total_grid_width + scrollbar_width + border_padding
            
            # Set a reasonable minimum and maximum
            min_width = int(round(800 * sf))
            max_width = int(round(2400 * sf))
            
            form_width = max(min_width, min(min_form_width, max_width))
            
            # Calculate height based on UI components
            toolbar_h = int(self.size_constants.get('toolbar_height', int(round(44 * sf))))
            bottom_panel_h = int(self.size_constants.get('bottom_reserved_height', int(round(90 * sf))))
            status_h = int(self.size_constants.get('status_height', int(round(25 * sf))))
            menu_h = int(round(24 * sf))
            
            # Default grid height for reasonable number of rows
            grid_height = int(round(300 * sf))
            
            form_height = menu_h + toolbar_h + bottom_panel_h + grid_height + status_h
            
            # Apply the calculated size
            self.Size = Size(form_width, form_height)
        except Exception:
            # Fallback to fixed size if calculation fails
            sf = getattr(self, '_scale_factor', 1.0)
            self.Size = Size(int(1600 * sf), int(445 * sf))
    
    def setup_ui(self):
        """Setup the enhanced user interface"""
        self.Text = "Occultation Manager - SharpCap Integration"
        # Scale window size with DPI
        sf = getattr(self, '_scale_factor', 1.0)
        self.Size = Size(int(1600 * sf), int(445 * sf))
        self.StartPosition = FormStartPosition.CenterScreen
        
        # Create menu bar
        menu_bar = self.create_enhanced_menu_bar()
        # Dock the menu bar to the top so it occupies its own space
        try:
            menu_bar.Dock = DockStyle.Top
        except Exception:
            pass
        self.MainMenuStrip = menu_bar
        # Keep the MenuStrip flush with the Windows title bar. Instead, nudge
        # the toolbar downward by about half the font height so its buttons are
        # not overlapped by the menu at high DPI.
        self.Controls.Add(menu_bar)
        
        main_panel = Panel()
        main_panel.Dock = DockStyle.Fill
        # Small manual top padding needed when MenuStrip is docked to Top
        main_panel.Padding = Padding(0, 10, 0, 0)
        self.Controls.Add(main_panel)
        
        # Enhanced toolbar
        # Compute a small vertical nudge (half the font height) and add it to
        # the central size_constants so the toolbar's internal layout places
        # its row below the MenuStrip without moving the MenuStrip itself.
        try:
            # Use a small scaled nudge so the toolbar moves down slightly at
            # higher DPI instead of a fixed pixel amount. Add 2 extra pixels
            # for a bit more separation (per request).
            sf = getattr(self, '_scale_factor', 1.0)
            base_nudge = int(self.size_constants.get('toolbar_fixed_nudge', 6))
            scaled = int(round(sf * base_nudge)) + 2
            self.size_constants['toolbar_start_y'] = int(self.size_constants.get('toolbar_start_y', 18)) + scaled
        except Exception:
            pass

        toolbar = self.create_enhanced_toolbar()
        
        # Events grid (moved up under buttons as requested)
        self.events_grid = EventsDataGrid()
        # Dock the events grid to fill remaining space under top-docked controls
        self.events_grid.Dock = DockStyle.Fill
        
        # Bottom panel (smaller now)
        bottom_panel = self.create_enhanced_bottom_panel()
        # Add controls so toolbar sits above bottom_panel and events_grid fills remaining area.
        # For DockStyle.Top controls, the control added later is placed closer to the top,
        # so add bottom_panel first, then toolbar, then events_grid last (Fill).
        main_panel.Controls.Add(bottom_panel)
        main_panel.Controls.Add(toolbar)
        main_panel.Controls.Add(self.events_grid)
        # Ensure the events grid is visible and filling the remaining space
        try:
            self.events_grid.Visible = True
            self.events_grid.BringToFront()
        except Exception:
            pass

        # Status bar
        status_bar = self.create_status_bar()
        status_bar.Parent = main_panel

    def apply_current_theme(self):
        """Apply the current theme to all controls"""
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
        
        # Force refresh
        self.Refresh()

    def _layout_row(self, parent, controls, start_x=10, y=15, gap=4):
        """Helper to lay out a row of controls with a fixed pixel gap.

        parent: control whose coordinate space we use
        controls: iterable of controls (must have .Size.Width set)
        start_x, y: starting coordinates
        gap: pixel gap between controls
        """
        x = start_x
        for ctrl in controls:
            try:
                # If this is a button or label, auto-size it based on its label so widths
                # are consistent with content. This uses a small off-screen
                # bitmap to measure the rendered string in the control's font.
                try:
                    from System.Windows.Forms import Button, Label
                    if isinstance(ctrl, Button) or isinstance(ctrl, Label) :
                        self._autosize_button(ctrl)
                except Exception:
                    # ignore if Button isn't available/import fails
                    pass

                ctrl.Location = Point(x, y)
            except Exception:
                # If Location assignment fails, skip
                pass
            x += (ctrl.Size.Width if hasattr(ctrl, 'Size') else 0) + gap

    def _autosize_button(self, btn, padding=None, min_width=None, height=None):
        """Set button width to fit its text plus padding (DPI-aware).

        Uses Graphics.MeasureString on a tiny bitmap so this works even when
        controls haven't been shown/created with a window handle yet.
        Padding/min_width/height default to values derived from
        self._scale_factor / self.size_constants when available.
        """
        try:
            sf = getattr(self, '_scale_factor', 1.0)
            # Derive sensible defaults from the central size_constants if present
            try:
                default_btn_h = int(round(self.size_constants.get('button_height', int(round(25 * sf)))))
            except Exception:
                default_btn_h = int(round(25 * sf))

            if padding is None:
                padding = int(round(14 * sf))
            if min_width is None:
                min_width = int(round(40 * sf))
            if height is None:
                height = default_btn_h

            from System.Drawing import Bitmap, Graphics
            # Create a tiny bitmap and measure the text with the button's font
            bmp = Bitmap(1, 1)
            g = Graphics.FromImage(bmp)
            try:
                sizef = g.MeasureString(btn.Text or "", btn.Font)
                measured = int(sizef.Width)
            finally:
                g.Dispose()
                bmp.Dispose()

            width = measured + padding
            if width < min_width:
                width = min_width

            # If the control already has a non-default height, preserve it; otherwise set scaled height
            try:
                current_h = btn.Size.Height
                if current_h == 23:
                    new_h = height
                else:
                    new_h = current_h
            except Exception:
                new_h = height

            btn.Size = Size(width, new_h)
        except Exception:
            # Non-fatal: leave existing size if measuring fails
            pass
    
    def _detect_scale(self):
        """Detect the current display DPI and return (scale_factor, category).

        scale_factor: float (e.g. 1.0, 1.25, 1.5)
        category: int (100, 125, 150)

        Uses Graphics.FromHwnd(self.Handle) when available and falls back to 96 DPI.
        """
        try:
            # Try to get DPI from Graphics if handle is available
            dpi = 96.0
            try:
                if hasattr(self, 'Handle') and self.Handle:
                    from System.Drawing import Graphics
                    g = Graphics.FromHwnd(self.Handle)
                    try:
                        dpi = float(g.DpiX)
                    finally:
                        g.Dispose()
                else:
                    # If no handle yet, try to create it
                    if not getattr(self, 'IsHandleCreated', False):
                        try:
                            self.CreateControl()
                            from System.Drawing import Graphics
                            g = Graphics.FromHwnd(self.Handle)
                            try:
                                dpi = float(g.DpiX)
                            finally:
                                g.Dispose()
                        except Exception:
                            pass
            except Exception:
                # Final fallback - try using DeviceContext or default to 96 DPI
                try:
                    from System.Drawing import Graphics
                    # Get DPI from a temporary graphics context
                    g = Graphics.FromHwnd(System.IntPtr.Zero)
                    try:
                        dpi = float(g.DpiX)
                    finally:
                        g.Dispose()
                except Exception:
                    # Ultimate fallback to classic 96 DPI
                    dpi = 96.0

            sf = dpi / 96.0
            if dpi < 110:
                cat = 100
            elif dpi < 140:
                cat = 125
            else:
                cat = 150

            return (sf, cat)
        except Exception:
            return (1.0, 100)
    
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
        # Use central size constant for toolbar height (DPI-aware)
        try:
            toolbar.Height = int(self.size_constants.get('toolbar_height', 40))
        except Exception:
            toolbar.Height = 40
        toolbar.Dock = DockStyle.Top
        toolbar.BackColor = SystemColors.Control
        sf = getattr(self, '_scale_factor', 1.0)
        btn_h = int(round(self.size_constants.get('button_height', int(round(25 * sf)))))
        # Add a small extra to button height to avoid clipped borders at high DPI
        extra_h = int(self.size_constants.get('toolbar_button_extra', 4))
        gap = int(self.size_constants.get('gap', 4))
        start_x = int(self.size_constants.get('toolbar_start_x', 6))
        start_y = int(self.size_constants.get('toolbar_start_y', 7))
        # Row 1 - Primary workflow (left-to-right)
        btn_download = Button()
        btn_download.Text = "Download"
        btn_download.Click += self.download_events_click
        toolbar.Controls.Add(btn_download)
        try:
            self._autosize_button(btn_download, height=btn_h + extra_h)
        except Exception:
            pass
        btn_refresh = Button()
        btn_refresh.Text = "Refresh"
        btn_refresh.Click += self.refresh_events_click
        toolbar.Controls.Add(btn_refresh)
        try:
            self._autosize_button(btn_refresh, height=btn_h + extra_h)
        except Exception:
            pass

        self.cbo_stations = ComboBox()
        try:
            cbo_w = int(round(150 * sf))
            # Make combobox a bit taller to align with increased button height
            self.cbo_stations.Size = Size(cbo_w, btn_h + extra_h)
        except Exception:
            self.cbo_stations.Size = Size(150, 25 + extra_h)
        self.cbo_stations.DropDownStyle = ComboBoxStyle.DropDownList
        self.cbo_stations.SelectionChangeCommitted += self.station_filter_changed
        toolbar.Controls.Add(self.cbo_stations)

        btn_event_details = Button()
        btn_event_details.Text = "Event Details"
        btn_event_details.Click += self.show_event_details_click
        toolbar.Controls.Add(btn_event_details)
        try:
            self._autosize_button(btn_event_details, height=btn_h + extra_h)
        except Exception:
            pass

        btn_edit_exposure = Button()
        btn_edit_exposure.Text = "Edit Settings"
        btn_edit_exposure.Click += self.edit_exposure_click
        toolbar.Controls.Add(btn_edit_exposure)
        try:
            self._autosize_button(btn_edit_exposure, height=btn_h + extra_h)
        except Exception:
            pass

        # Sequence operations
        btn_create_sequences = Button()
        btn_create_sequences.Text = "Create Sequences"
        btn_create_sequences.Click += self.create_sequences_click
        toolbar.Controls.Add(btn_create_sequences)
        try:
            self._autosize_button(btn_create_sequences, height=btn_h + extra_h)
        except Exception:
            pass

        btn_run_sequences = Button()
        btn_run_sequences.Text = "Run Sequences"
        btn_run_sequences.Click += self.run_sequences_click
        toolbar.Controls.Add(btn_run_sequences)
        try:
            self._autosize_button(btn_run_sequences, height=btn_h + extra_h)
        except Exception:
            pass
        
        btn_generate_report = Button()
        btn_generate_report.Text = "Generate Report"
        btn_generate_report.Click += self.generate_report_click
        toolbar.Controls.Add(btn_generate_report)
        try:
            self._autosize_button(btn_generate_report, height=btn_h + extra_h)
        except Exception:
            pass


        # Night Mode (global)
        self.btn_night_mode = Button()
        self.btn_night_mode.Text = "Night Mode"
        self.btn_night_mode.Click += self.toggle_night_mode_click
        toolbar.Controls.Add(self.btn_night_mode)
        try:
            self._autosize_button(self.btn_night_mode, height=btn_h + extra_h)
        except Exception:
            pass

        # Layout the toolbar buttons with a fixed 4px gap
        try:
            self._layout_row(toolbar, [btn_download, btn_refresh, self.cbo_stations, btn_event_details, btn_edit_exposure, btn_create_sequences, btn_run_sequences, btn_generate_report, self.btn_night_mode], start_x=start_x, y=start_y, gap=gap)
        except Exception:
            pass

        # Ensure the toolbar height is sufficient to show the buttons fully
        try:
            min_needed = start_y + (btn_h + extra_h) + 6
            if toolbar.Height < min_needed:
                toolbar.Height = int(min_needed)
        except Exception:
            pass

        return toolbar

    def create_enhanced_menu_bar(self):
        """Create the enhanced menu bar"""
        menu_bar = MenuStrip()
        
        # File menu
        menu_file = ToolStripMenuItem("File")
        menu_file.DropDownItems.Add(ToolStripMenuItem("Download Events", None, self.download_events_click))
        menu_file.DropDownItems.Add(ToolStripMenuItem("Refresh Events", None, self.refresh_events_click))
        menu_file.DropDownItems.Add(ToolStripSeparator())
        menu_file.DropDownItems.Add(ToolStripMenuItem("Exit", None, self.exit_click))
        menu_bar.Items.Add(menu_file)
        
        # Events menu
        menu_events = ToolStripMenuItem("Events")
        menu_events.DropDownItems.Add(ToolStripMenuItem("Event Details", None, self.show_event_details_click))
        menu_events.DropDownItems.Add(ToolStripMenuItem("Edit Settings", None, self.edit_exposure_click))
        menu_events.DropDownItems.Add(ToolStripSeparator())
        menu_events.DropDownItems.Add(ToolStripMenuItem("Generate Report", None, self.generate_report_click))
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
        #menu_bar.Items.Add(menu_sequences)
        
        # Tools menu
        menu_tools = ToolStripMenuItem("Tools")
        menu_tools.DropDownItems.Add(ToolStripMenuItem("Configuration", None, self.show_configuration_click))
        menu_tools.DropDownItems.Add(ToolStripSeparator())
        menu_tools.DropDownItems.Add(ToolStripMenuItem("Manage Telescopes", None, self.show_telescope_manager_click))
        menu_tools.DropDownItems.Add(ToolStripMenuItem("Manage Cameras", None, self.show_camera_manager_click))
        menu_tools.DropDownItems.Add(ToolStripSeparator())
        menu_tools.DropDownItems.Add(ToolStripMenuItem("Template Manager", None, self.show_template_manager_click))
        menu_bar.Items.Add(menu_tools)
        
        # Help menu - MODIFIED
        menu_help = ToolStripMenuItem("Help")
        menu_help.DropDownItems.Add(ToolStripMenuItem("User Guide", None, self.show_help_click))
        menu_help.DropDownItems.Add(ToolStripSeparator())
        menu_help.DropDownItems.Add(ToolStripMenuItem("About", None, self.show_about_click))
        menu_bar.Items.Add(menu_help)
        
        return menu_bar
        
    
    def create_enhanced_bottom_panel(self):
        """Create the enhanced bottom control panel with Observation Preparation"""
        panel = Panel()
        # Height derived from central constants (DPI-aware). Reduce by half the
        # form font height so the bottom panel is a bit less tall at high DPI.
        try:
            base_h = int(self.size_constants.get('bottom_reserved_height', 90))
            reduce_by = int(round((self.Font.Height or 16) / 2.0))
            panel.Height = max(32, base_h - reduce_by)
        except Exception:
            panel.Height = 90
        panel.Dock = DockStyle.Top
        panel.BackColor = SystemColors.Control
        sf = getattr(self, '_scale_factor', 1.0)
        gap = int(self.size_constants.get('gap', 4))
        start_x = int(self.size_constants.get('start_x', 10))

        # Observation Preparation Group (create it, but size/height will be aligned
        # to the Quick Filters group below)
        obs_prep_group = self.create_observation_preparation_group()
        panel.Controls.Add(obs_prep_group)

        # Quick Filter Actions group
        actions_group = GroupBox()
        actions_group.Text = "Quick Filters"
        actions_group.Location = Point(start_x, 5)
        try:
            actions_group.Size = Size(int(self.size_constants.get('quick_group_width', 310)), int(max(66, panel.Height - 24)))
        except Exception:
            actions_group.Size = Size(310, 66)
        panel.Controls.Add(actions_group)

        # Make Observation Preparation group the same height as Quick Filters
        # Calculate width based on event grid width minus Quick Filters width
        try:
            # Calculate total event grid width
            total_grid_width = 0
            for col in self.events_grid.Columns:
                total_grid_width += col.Width
            
            # Obs prep width should be: grid width - quick filters width - gap
            # This makes Quick Filters + gap + Obs Prep = grid width
            obs_w = total_grid_width - actions_group.Size.Width - gap
            
            # Ensure it's wide enough for the event details label inside (640px base + margins)
            min_content_width = int(round(660 * sf))
            obs_w = max(min_content_width, obs_w)
            
            obs_h = actions_group.Size.Height
            # Place to the right of quick filters
            obs_x = start_x + actions_group.Size.Width + gap
            obs_prep_group.Location = Point(obs_x, actions_group.Location.Y)
            obs_prep_group.Size = Size(obs_w, obs_h)
        except Exception:
            # fallback to previous placement
            try:
                obs_prep_group.Location = Point(270, 5)
                obs_prep_group.Size = Size(600, 66)
            except Exception:
                pass
        
        btn_filter_today = Button()
        btn_filter_today.Text = "Today"
        btn_filter_today.Click += self.filter_today_click
        actions_group.Controls.Add(btn_filter_today)
        
        btn_filter_upcoming = Button()
        btn_filter_upcoming.Text = "Future"
        btn_filter_upcoming.Click += self.filter_upcoming_click
        actions_group.Controls.Add(btn_filter_upcoming)
        
        btn_show_all = Button()
        btn_show_all.Text = "All"
        btn_show_all.Click += self.show_all_click
        actions_group.Controls.Add(btn_show_all)

        btn_select_toggle = Button()
        btn_select_toggle.Text = "On/Off"
        btn_select_toggle .Click += self.select_toggle_click
        actions_group.Controls.Add(btn_select_toggle)

        # Give filter buttons scaled height
        try:
            btn_h = int(self.size_constants.get('button_height', int(round(25 * sf))))
        except Exception:
            btn_h = int(round(25 * sf))

        try:
            # Nudge quick-filter row down by 1 pixel for visual spacing
            self._layout_row(actions_group, [btn_filter_today, btn_filter_upcoming, btn_show_all, btn_select_toggle], start_x=10, y=int(round(15 * sf)) + 1, gap=gap)
            for b in (btn_filter_today, btn_filter_upcoming, btn_show_all, btn_select_toggle):
                try:
                    self._autosize_button(b, height=btn_h)
                except Exception:
                    pass
        except Exception:
            pass

        self.lbl_selection_summary = Label()
        self.lbl_selection_summary.Text = "No events selected"
        try:
            self.lbl_selection_summary.Location = Point(10, int(round(panel.Height * 0.50)))
            self.lbl_selection_summary.Size = Size(int(round(self.size_constants.get('quick_group_width', 310) * 0.65)), int(round(18 * sf)))
        except Exception:
            self.lbl_selection_summary.Location = Point(10, 45)
            self.lbl_selection_summary.Size = Size(200, 18)
        actions_group.Controls.Add(self.lbl_selection_summary)

        self.events_grid.SelectionChanged += self.grid_selection_changed

        return panel
    
    def create_observation_preparation_group(self):
        """Create the observation preparation control group"""
        sf = getattr(self, '_scale_factor', 1.0)
        
        obs_group = GroupBox()
        obs_group.Text = "Observation Preparation - Interactive Setup + Testing"
        # Size will be set dynamically by parent panel
        
        # Load Event button
        btn_load_event = Button()
        btn_load_event.Text = "Load Event"
        btn_load_event.Click += self.load_event_for_prep_click
        btn_load_event.BackColor = Color.LightYellow
        obs_group.Controls.Add(btn_load_event)
        
        # Row 1: Setup and Navigation
        
        btn_goto_target = Button()
        btn_goto_target.Text = "GOTO"
        btn_goto_target.Click += self.goto_and_center_click
        btn_goto_target.BackColor = Color.LightBlue
        obs_group.Controls.Add(btn_goto_target)
        
        btn_plate_solve = Button()
        btn_plate_solve.Text = "Plate Solve"
        btn_plate_solve.Click += self.plate_solve_label_click
        btn_plate_solve.BackColor = Color.LightCyan
        obs_group.Controls.Add(btn_plate_solve)
        
        btn_setup_event = Button()
        btn_setup_event.Text = "Setup"
        btn_setup_event.Click += self.setup_for_event_click
        btn_setup_event.BackColor = Color.LightGreen
        obs_group.Controls.Add(btn_setup_event)
        
        btn_test_recording = Button()
        btn_test_recording.Text = "Test Recording"
        btn_test_recording.Click += self.test_recording_click
        btn_test_recording.BackColor = Color.LightSalmon
        obs_group.Controls.Add(btn_test_recording)
        
        # Layout observation-prep row with buttons using 4px gap
        try:
            # Use the same Y offset as quick filters so rows align; apply scale
            sf = getattr(self, '_scale_factor', 1.0)
            self._layout_row(obs_group, [btn_load_event, btn_goto_target, btn_plate_solve, btn_setup_event, btn_test_recording], start_x=10, y=int(round(15 * sf)) + 1, gap=4)
        except Exception:
            pass
        
        # Combined event display - positioned below buttons
        self.lbl_current_event = Label()
        self.lbl_current_event.Text = "No event loaded for preparation"
        self.lbl_current_event.Location = Point(10, int(42 * sf))
        self.lbl_current_event.Size = Size(640, int(18 * sf))
        self.lbl_current_event.Font = Font("Microsoft Sans Serif", 8, FontStyle.Bold)
        obs_group.Controls.Add(self.lbl_current_event)
        
        # Initialize preparation event to None
        self._preparation_event = None
        
        return obs_group
    
    def create_status_bar(self):
        """Create the status bar"""
        status_bar = Panel()
        # Use DPI-aware status height when available and ensure a sensible
        # minimum so label text does not get vertically clipped at high DPI.
        try:
            status_h = int(self.size_constants.get('status_height', 25))
        except Exception:
            status_h = 25
        status_bar.Height = max(status_h, 28)
        status_bar.Dock = DockStyle.Bottom
        status_bar.BackColor = SystemColors.ControlDark
        
        self.lbl_status = Label()
        self.lbl_status.Text = "Ready"
        try:
            # Try to vertically center the label based on the form font height
            lbl_h = int(round(self.Font.Height or 15))
        except Exception:
            lbl_h = 15
        lbl_y = max(2, int((status_bar.Height - lbl_h) / 2))
        self.lbl_status.Location = Point(10, lbl_y)
        self.lbl_status.Size = Size(400, lbl_h)
        status_bar.Controls.Add(self.lbl_status)
        
        self.lbl_event_count = Label()
        self.lbl_event_count.Text = "0 events"
        try:
            lbl_h2 = int(round(self.Font.Height or 15))
        except Exception:
            lbl_h2 = 15
        lbl_y2 = max(2, int((status_bar.Height - lbl_h2) / 2))
        self.lbl_event_count.Location = Point(500, lbl_y2)
        self.lbl_event_count.Size = Size(100, lbl_h2)
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

    def select_toggle_click(self, sender, e):
        """Handle toggle button click"""
        status = self.manager.toggle_event_selection()
        self.events_grid.toggle_all_events(status=status)
        self.update_selection_summary()


    # "Download & Run Tonight" flow removed per user request.
    # The UI and handlers for downloading and auto-running tonight's events
    # have been intentionally removed to simplify the menu and flows.

    def create_and_run_sequences(self, events):
        """Create sequences and run them for the given events"""
        if not events:
            return
        # First create sequences
        # Show the template selection dialog once. The dialog contains a checkbox
        # 'Apply to All Events' which controls whether the chosen template should
        # be applied to every selected event or only to the first (and prompt for
        # each subsequent event).
        template_dialog = TemplateSelectionDialog(self.config, self.theme_manager)
        if template_dialog.ShowDialog() != DialogResult.OK:
            return

        template_path = template_dialog.get_selected_template_path()
        apply_all = getattr(template_dialog, 'apply_for_all', False)
        create_combined = getattr(template_dialog, 'create_combined', False)

        # If the user requested a single combined sequence file
        if create_combined:
            if apply_all:
                # Create combined for all events using selected template
                combined_path = self.create_combined_sequence_file(events, template_path)
                if combined_path:
                    MessageBox.Show(f"Combined sequence file created: {os.path.basename(combined_path)}", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information)
                else:
                    MessageBox.Show("Failed to create combined sequence file.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
                return
            else:
                # Per-event templates for combined file: collect a map of per-event templates
                templates_map = {}
                for idx, ev in enumerate(events):
                    if idx == 0:
                        templates_map[ev.event_id] = template_path
                    else:
                        per_dialog = TemplateSelectionDialog(self.config, self.theme_manager)
                        per_dialog.Text = f"Select Template for {ev.get_asteroid_display_name()}"
                        if per_dialog.ShowDialog() != DialogResult.OK:
                            # User cancelled; abort combined creation
                            templates_map = None
                            break
                        templates_map[ev.event_id] = per_dialog.get_selected_template_path()

                if not templates_map:
                    return

                combined_path = self.create_combined_sequence_file(events, templates_map)
                if combined_path:
                    MessageBox.Show(f"Combined sequence file created: {os.path.basename(combined_path)}", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information)
                else:
                    MessageBox.Show("Failed to create combined sequence file.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
                return

        # Not creating combined: fall back to existing create-per-event/create-all logic
        if apply_all:
            # Create sequences for all events using the selected template
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
        else:
            # Apply the initially chosen template to the first event, then
            # prompt for each subsequent event individually.
            success_events = []
            for idx, ev in enumerate(events):
                if idx == 0:
                    # Use the template chosen in the initial dialog for the first event
                    per_template = template_path
                else:
                    per_dialog = TemplateSelectionDialog(self.config, self.theme_manager)
                    per_dialog.Text = f"Select Template for {ev.get_asteroid_display_name()}"
                    if per_dialog.ShowDialog() != DialogResult.OK:
                        # User cancelled per-event selection; stop processing further
                        break
                    per_template = per_dialog.get_selected_template_path()

                # Attempt to save sequence for this single event
                try:
                    ok = save_occultation_sequence(ev, per_template or "", self.config.get_sequence_path(), self.config)
                    if ok:
                        success_events.append(ev)
                except Exception as ex:
                    print(f"Error creating sequence for {ev.event_name}: {ex}")

            if success_events:
                # Run only the sequences that were created successfully
                self.update_status("Per-event sequences created, starting execution...")
                def run_in_background():
                    self.sequence_runner.run_sequences(success_events, self.update_status_safe)

                thread = threading.Thread(target=run_in_background)
                thread.IsBackground = True
                thread.start()
    
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
        """Handle edit settings button click"""
        selected_rows = []
        for row in self.events_grid.SelectedRows:
            selected_rows.append(row)
        
        if len(selected_rows) == 0:
            MessageBox.Show("Please select an event to edit settings.", "No Event Selected", 
                          MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        elif len(selected_rows) > 1:
            MessageBox.Show("Please select only one event to edit settings.", "Multiple Events Selected", 
                          MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        
        event = selected_rows[0].Tag
        if event:
            self.edit_event_exposure(event)
    
    def edit_event_exposure(self, event):
        """Edit exposure, gain, and recording duration for a specific event"""
        exposure_dialog = ExposureEditDialog(event, self.theme_manager)
        if exposure_dialog.ShowDialog() == DialogResult.OK:
            new_exposure = exposure_dialog.get_new_exposure()
            new_gain = exposure_dialog.get_new_gain()
            new_duration = exposure_dialog.get_new_recording_duration()
            
            # Check if values match calculated defaults to avoid unnecessary custom flags
            # Calculate what the default values would be
            original_custom_exp = event.custom_exposure
            original_custom_dur = event.custom_recording_duration
            
            event.custom_exposure = None
            event.custom_recording_duration = None
            event._calculate_derived_values()
            calculated_exposure = event.exposure_ms
            calculated_duration = event.recording_duration
            default_gain = self.config.get_default_gain()
            
            # Restore originals before setting new values
            event.custom_exposure = original_custom_exp
            event.custom_recording_duration = original_custom_dur
            event._calculate_derived_values()
            
            # Only set custom if different from calculated/default
            if new_exposure != calculated_exposure:
                event.set_custom_exposure(new_exposure)
            else:
                event.custom_exposure = None
                event._calculate_derived_values()
            
            if new_gain != default_gain:
                event.set_custom_gain(new_gain)
            else:
                event.custom_gain = None
                event._calculate_derived_values()
            
            if new_duration != calculated_duration:
                event.set_custom_recording_duration(new_duration)
            else:
                event.custom_recording_duration = None
                event._calculate_derived_values()
            
            # Refresh the grid to show updated values
            self.refresh_display()
            
            # Ask if user wants to regenerate sequence
            result = MessageBox.Show(
                f"Settings updated:\n- Exposure: {new_exposure}ms\n- Gain: {new_gain}\n- Recording Duration: {new_duration}s\n\nWould you like to regenerate the sequence file for this event?",
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
        """Execute the actual GOTO command and wait for completion"""
        coordinates = self.CoordinateParser.Parse(f"{event.ra:.6f};{event.dec:.6f}", True)

        try:
            # Check if mount control is available
            if hasattr(self.sharpcap, 'Mounts') and self.sharpcap.Mounts.SelectedMount:
                mount = self.sharpcap.Mounts.SelectedMount
                
                # Use the async method with SafeGetAsyncResult to properly wait for completion
                # SafeGetAsyncResult blocks until the async operation completes
                print(f"Starting GOTO to: RA {event.ra:.6f}h, Dec {event.dec:.6f}°")
                result = self.sharpcap.SafeGetAsyncResult(mount.StartSlewToAsync(coordinates, CancellationToken()))
                
                # Wait a moment for mount to settle after slew completes
                time.sleep(2)
                if not mount.IsSettled:
                    print("Waiting for mount to settle...")
                    # Wait up to 30 seconds for mount to settle
                    wait_start = time.time()
                    while not mount.IsSettled and (time.time() - wait_start) < 30:
                        time.sleep(1)
                
                # Optionally sync mount after GOTO
                if self.config.get_sync_mount():
                    print("Performing Solve And Sync...")
                    mount.SolveAndSync() 

                print(f"GOTO completed: RA {event.ra:.4f}h, Dec {event.dec:.4f}°")
                return True
            else:
                # Show coordinates for manual GOTO
                print(f"Manual GOTO required: RA {event.ra:.6f}h, Dec {event.dec:.6f}°")
                result = MessageBox.Show(f"No mount control available.\n\nPlease manually GOTO:\n\nYou can use the SharpCap Push To Assistant" +
                                    f"RA: {event.ra:.6f} hours\nDec: {event.dec:.6f}°\n\n" +
                                    f"These coordinates have been copied to the clipboard.",
                                    "Manual GOTO Required", MessageBoxButtons.OKCancel, MessageBoxIcon.Information)
                System.Windows.Forms.Clipboard.SetText(f"{event.ra:.6f}, {event.dec:.6f}")
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
    
    def generate_report_click(self, sender, e):
        """Generate North American Occultation Report Forms for selected past events"""
        selected_events = self.get_displayed_selected_events()
        if not selected_events:
            MessageBox.Show("Please select an event to generate a report for.", "No Event Selected", 
                        MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        
        # Only allow one event to be selected
        if len(selected_events) > 1:
            MessageBox.Show("Please select only one event to generate a report for.", "Multiple Events Selected", 
                        MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        
        event = selected_events[0]
        
        # Check if event has already occurred
        if not event.event_datetime or event.event_datetime >= datetime.utcnow():
            MessageBox.Show("Reports can only be generated for events that have already occurred.\n\nPlease select a past event.", 
                        "Event Not Yet Occurred", MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        
        # Show warning about report generation being under development
        warning_result = MessageBox.Show(
            "Report generation is still under development and has not been approved by the NA or TT reporting coordinators. Use with caution.\n\nDo you want to continue?",
            "Report Generation Warning",
            MessageBoxButtons.YesNo,
            MessageBoxIcon.Warning)
        
        if warning_result != DialogResult.Yes:
            self.update_status("Report generation cancelled")
            return
        
        # Generate report
        try:
            print(f"\n=== Generating report for {event.get_asteroid_display_name()} ===")
            
            # Show location confirmation dialog FIRST (before comprehensive dialog)
            from gui_dialogs import LocationConfirmDialog
            location_dialog = LocationConfirmDialog(event, self.theme_manager)
            if location_dialog.ShowDialog() != DialogResult.OK:
                print("User cancelled location confirmation")
                self.update_status("Report generation cancelled")
                return
            
            # Get the confirmed location from the dialog
            location = location_dialog.get_location()
            
            # Update event with user-confirmed/edited location
            event.latitude = location['latitude']
            event.longitude = location['longitude']
            event.elevation = location['elevation']
            event.obs_location = location['obs_location']
            
            # Show COMPREHENSIVE REPORT DIALOG - combines everything!
            from comprehensive_report_dialog import ComprehensiveReportDialog
            comprehensive_dialog = ComprehensiveReportDialog(self.config, self.theme_manager, event)
            
            if comprehensive_dialog.ShowDialog() != DialogResult.OK:
                print("User cancelled report generation")
                self.update_status("Report generation cancelled")
                return
            
            # Get all selections from comprehensive dialog
            report_type = comprehensive_dialog.get_report_type()
            telescope_id = comprehensive_dialog.get_telescope_id()
            camera_id = comprehensive_dialog.get_camera_id()
            observation_type = comprehensive_dialog.get_observation_type()
            aota_file_path = comprehensive_dialog.get_selected_aota_path()
            tangra_csv_path = comprehensive_dialog.get_selected_tangra_path()
            aota_report_path = comprehensive_dialog.get_selected_aota_report_path()
            
            print(f"Report type: {report_type}")
            print(f"Telescope ID: {telescope_id}")
            print(f"Camera ID: {camera_id}")
            print(f"Observation type: {observation_type}")
            print(f"AOTA file: {aota_file_path if aota_file_path else 'None'}")
            print(f"Tangra CSV: {tangra_csv_path if tangra_csv_path else 'None'}")
            print(f"AOTA Report: {aota_report_path if aota_report_path else 'None'}")
            
            # Create appropriate report generator
            if report_type == 'north_america':
                from na_report import NAReportGenerator
                report_generator = NAReportGenerator(self.config)
            elif report_type == 'trans_tasman':
                import sys
                if 'tt_report' in sys.modules:
                    del sys.modules['tt_report']
                from tt_report import TTReportGenerator
                report_generator = TTReportGenerator(self.config)
            else:
                MessageBox.Show(f"Report type '{report_type}' is not yet implemented.", 
                              "Not Implemented", MessageBoxButtons.OK, MessageBoxIcon.Information)
                self.update_status("Report generation cancelled")
                return
            
            # Check template exists
            template_ok, message = report_generator.check_template_exists()
            if not template_ok:
                MessageBox.Show(message, "Template Not Found", 
                              MessageBoxButtons.OK, MessageBoxIcon.Error)
                self.update_status("Report generation failed: template not found")
                return
            
            # Process AOTA file if selected
            aota_event = None
            if aota_file_path:
                try:
                    print(f"Processing AOTA file: {aota_file_path}")
                    from aota_parser import parse_aota_file
                    aota_result = parse_aota_file(aota_file_path)
                    
                    if aota_result:
                        # Check if multiple valid events exist
                        if aota_result.has_multiple_valid_events():
                            from aota_dialogs import AOTAEventSelectionDialog
                            event_selector = AOTAEventSelectionDialog(
                                self.theme_manager, 
                                aota_result, 
                                event.get_asteroid_display_name()
                            )
                            if event_selector.ShowDialog() == DialogResult.OK:
                                aota_event = event_selector.get_selected_event()
                                print(f"Selected AOTA event: {aota_event}")
                            else:
                                print("AOTA event selection cancelled")
                                if observation_type in ["Positive", "Unsure"]:
                                    MessageBox.Show(
                                        "AOTA event selection is required for Positive/Unsure observations.",
                                        "AOTA Required",
                                        MessageBoxButtons.OK,
                                        MessageBoxIcon.Warning
                                    )
                                    self.update_status("Report generation cancelled")
                                    return
                        else:
                            aota_event = aota_result.get_single_valid_event()
                            if aota_event:
                                print(f"Using single AOTA event: {aota_event}")
                            else:
                                MessageBox.Show(
                                    "No valid events found in AOTA file.",
                                    "No Valid Events",
                                    MessageBoxButtons.OK,
                                    MessageBoxIcon.Warning
                                )
                    else:
                        MessageBox.Show(
                            "Failed to parse AOTA file.",
                            "Parse Error",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Error
                        )
                except Exception as ex:
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"Error importing AOTA data: {ex}")
                    print(error_details)
                    MessageBox.Show(
                        f"Error importing AOTA data:\n\n{str(ex)}",
                        "Import Error",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    )
            
            # Process Tangra CSV file
            tangra_data = None
            if tangra_csv_path:
                try:
                    print(f"Processing Tangra CSV: {tangra_csv_path}")
                    import light_curves_iron as lc
                    tangra_data = lc.get_observation_summary(tangra_csv_path, percentiles=[1, 99])
                    print(f"Tangra data extracted successfully")
                    print(f"  Start time: {tangra_data['start_time']}")
                    print(f"  End time: {tangra_data['end_time']}")
                    print(f"  Exposure (ms): {tangra_data['tdelta_median']:.3f}")
                    if 'video_format' in tangra_data:
                        print(f"  Video format: {tangra_data['video_format']}")
                    if 'acquisition_delay' in tangra_data:
                        print(f"  Camera acquisition delay (ms): {tangra_data['acquisition_delay']:.3f}")
                except Exception as ex:
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"Error processing Tangra CSV: {ex}")
                    print(error_details)
                    MessageBox.Show(
                        f"Error processing Tangra CSV:\n\n{str(ex)}",
                        "Tangra Processing Error",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    )
                    tangra_data = None
            
            # Process AOTA Report file if selected
            aota_report_data = None
            if aota_report_path:
                try:
                    print(f"Processing AOTA Report: {aota_report_path}")
                    import aota_report_parser as arp
                    parsed_report = arp.parse_aota_report(aota_report_path)
                    
                    # Bug fix #8: Check if parsed_report is None (file read error)
                    if parsed_report is None:
                        print("Failed to parse AOTA Report file")
                        MessageBox.Show(
                            "Failed to read or parse AOTA Report file.",
                            "Parse Error",
                            MessageBoxButtons.OK,
                            MessageBoxIcon.Error
                        )
                    elif parsed_report and parsed_report['events']:
                        # Check if multiple events exist
                        if len(parsed_report['events']) > 1:
                            from System.Windows.Forms import Form, Label, ListBox, Button, FormStartPosition
                            from System.Drawing import Point, Size
                            
                            # Create event selection dialog
                            event_dialog = Form()
                            event_dialog.Text = "Select AOTA Report Event"
                            event_dialog.Size = Size(500, 300)
                            event_dialog.StartPosition = FormStartPosition.CenterParent
                            event_dialog.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
                            event_dialog.MaximizeBox = False
                            event_dialog.MinimizeBox = False
                            
                            lbl = Label()
                            lbl.Text = "Multiple events found in AOTA Report. Please select one:"
                            lbl.Location = Point(20, 20)
                            lbl.Size = Size(450, 40)
                            event_dialog.Controls.Add(lbl)
                            
                            listbox = ListBox()
                            listbox.Location = Point(20, 70)
                            listbox.Size = Size(450, 120)
                            
                            for evt in parsed_report['events']:
                                d_time = evt.get('d_time_utc', 'N/A')
                                r_time = evt.get('r_time_utc', 'N/A')
                                display = f"Event #{evt['event_number']}  D: {d_time}  R: {r_time} UTC"
                                listbox.Items.Add(display)
                            
                            listbox.SelectedIndex = 0
                            event_dialog.Controls.Add(listbox)
                            
                            btn_ok = Button()
                            btn_ok.Text = "OK"
                            btn_ok.Location = Point(300, 210)
                            btn_ok.Size = Size(80, 30)
                            btn_ok.DialogResult = DialogResult.OK
                            event_dialog.Controls.Add(btn_ok)
                            event_dialog.AcceptButton = btn_ok
                            
                            btn_cancel = Button()
                            btn_cancel.Text = "Cancel"
                            btn_cancel.Location = Point(390, 210)
                            btn_cancel.Size = Size(80, 30)
                            btn_cancel.DialogResult = DialogResult.Cancel
                            event_dialog.Controls.Add(btn_cancel)
                            event_dialog.CancelButton = btn_cancel
                            
                            if event_dialog.ShowDialog() == DialogResult.OK:
                                selected_index = listbox.SelectedIndex
                                aota_report_data = arp.get_event_summary(parsed_report, selected_index)
                                print(f"Selected AOTA Report event #{selected_index + 1}")
                            else:
                                print("AOTA Report event selection cancelled")
                        else:
                            # Single event, use it automatically
                            aota_report_data = arp.get_event_summary(parsed_report, 0)
                            print(f"Using AOTA Report event data")
                        
                        if aota_report_data:
                            print(f"  D time: {aota_report_data['d_hours']}:{aota_report_data['d_minutes']}:{aota_report_data['d_seconds']}")
                            print(f"  R time: {aota_report_data['r_hours']}:{aota_report_data['r_minutes']}:{aota_report_data['r_seconds']}")
                            print(f"  SNR: {aota_report_data['snr']}")
                    else:
                        print("No valid events found in AOTA Report")
                        
                except Exception as ex:
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"Error processing AOTA Report: {ex}")
                    print(error_details)
                    MessageBox.Show(
                        f"Error processing AOTA Report:\n\n{str(ex)}",
                        "AOTA Report Processing Error",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Error
                    )
                    aota_report_data = None
            
            # Compare AOTA.xml and AOTA Report times if both are available
            if aota_event and aota_report_data:
                self._compare_aota_sources(aota_event, aota_report_data)
            
            # Use AOTA Report data if AOTA.xml is not available
            if aota_report_data and not aota_event:
                print("Using AOTA Report data (no AOTA.xml file provided)")
            
            # Determine if AOTA XML was used (for OTE determination)
            aota_xml_used = bool(aota_event and not aota_report_data)
            
            self.update_status(f"Generating report for {event.get_asteroid_display_name()}...")
            output_path = report_generator.generate_report(event, telescope_id, camera_id, observation_type, tangra_data, aota_report_data, aota_xml_used)
            
            # If AOTA.xml data exists but AOTA Report wasn't used, add AOTA.xml data to the report
            # (AOTA Report data is already included in generate_report if it was provided)
            if output_path and aota_event and not aota_report_data:
                try:
                    print("Adding AOTA.xml data to report...")
                    self._add_aota_to_existing_report(output_path, report_generator, aota_event)
                    print("AOTA.xml data successfully added to report")
                except Exception as ex:
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"Warning: Could not add AOTA.xml data to report: {ex}")
                    print(error_details)
                    # Don't fail the whole report generation, just warn
                    MessageBox.Show(
                        f"Report generated but AOTA.xml data could not be added:\n\n{str(ex)}",
                        "Warning",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Warning
                    )
            
            if output_path:
                # Generate Occult4 XML export with the same filename as the report
                xml_output_path = None
                try:
                    print("Generating Occult4 XML export...")
                    from occult4_export import Occult4Exporter
                    occult4_exporter = Occult4Exporter(self.config)
                    
                    # Generate XML filename from report filename
                    report_dir = os.path.dirname(output_path)
                    report_basename = os.path.splitext(os.path.basename(output_path))[0]
                    xml_filename = report_basename + '.xml'
                    xml_path = os.path.join(report_dir, xml_filename)
                    
                    # Export observation data using the proper public API
                    xml_output_path = occult4_exporter.export_observation_to_path(
                        xml_path, event, telescope_id, camera_id, 
                        observation_type, tangra_data, aota_report_data, None
                    )
                except Exception as ex:
                    import traceback
                    error_details = traceback.format_exc()
                    print(f"Warning: Failed to export Occult4 XML - {str(ex)}")
                    print(error_details)
                    # Show warning to user
                    MessageBox.Show(
                        f"Occult4 XML export failed:\n\n{str(ex)}\n\nReport was generated successfully, but XML export failed.",
                        "XML Export Warning",
                        MessageBoxButtons.OK,
                        MessageBoxIcon.Warning
                    )
                    xml_output_path = None
                
                print(f"SUCCESS: Report generated: {output_path}")
                
                # Update status and message based on whether XML was also generated
                if xml_output_path:
                    self.update_status("Report and XML generated successfully")
                    MessageBox.Show(f"Report and Occult4 XML generated successfully.\n\nFiles saved to:\n{output_path}\n{xml_output_path}", 
                                "Success", MessageBoxButtons.OK, MessageBoxIcon.Information)
                else:
                    self.update_status("Report generated successfully")
                    MessageBox.Show(f"Report generated successfully.\n\nFile saved to:\n{output_path}", 
                                "Success", MessageBoxButtons.OK, MessageBoxIcon.Information)
            else:
                print(f"ERROR: Report generation failed (check log)")
                self.update_status("Report generation failed")
                MessageBox.Show("Report generation failed. Tip: Close the Excel file if it's already open.\n\nCheck report_debug.log for details.", 
                            "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
        except Exception as ex:
            import traceback
            error_details = traceback.format_exc()
            error_msg = str(ex)
            print(f"EXCEPTION generating report: {error_msg}")
            print(f"Full traceback:\n{error_details}")
            self.update_status("Report generation failed")
            MessageBox.Show(f"Error generating report:\n\n{error_msg}", 
                        "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def _compare_aota_sources(self, aota_event, aota_report_data):
        """Compare D/R times from AOTA.xml and AOTA Report and warn if different
        
        Args:
            aota_event: AOTAEvent object from AOTA.xml
            aota_report_data: Dictionary from AOTA Report parser
        """
        def time_to_seconds(hours, minutes, seconds):
            """Convert time components to total seconds for comparison"""
            try:
                h = int(hours) if hours else 0
                m = int(minutes) if minutes else 0
                s = float(seconds) if seconds else 0.0
                return h * 3600 + m * 60 + s
            except:
                return None
        
        # Compare D times
        aota_d_seconds = time_to_seconds(aota_event.d_hours, aota_event.d_minutes, aota_event.d_seconds)
        report_d_seconds = time_to_seconds(
            aota_report_data.get('d_hours'),
            aota_report_data.get('d_minutes'),
            aota_report_data.get('d_seconds')
        )
        
        # Compare R times
        aota_r_seconds = time_to_seconds(aota_event.r_hours, aota_event.r_minutes, aota_event.r_seconds)
        report_r_seconds = time_to_seconds(
            aota_report_data.get('r_hours'),
            aota_report_data.get('r_minutes'),
            aota_report_data.get('r_seconds')
        )
        
        # Check for differences (allow 0.1 second tolerance for rounding)
        tolerance = 0.1
        d_differs = False
        r_differs = False
        
        if aota_d_seconds is not None and report_d_seconds is not None:
            if abs(aota_d_seconds - report_d_seconds) > tolerance:
                d_differs = True
        
        if aota_r_seconds is not None and report_r_seconds is not None:
            if abs(aota_r_seconds - report_r_seconds) > tolerance:
                r_differs = True
        
        if d_differs or r_differs:
            from System.Windows.Forms import MessageBox, MessageBoxButtons, MessageBoxIcon
            
            warning_msg = "Warning: AOTA.xml and AOTA Report times differ!\n\n"
            
            if d_differs:
                warning_msg += f"Disappearance (D):\n"
                aota_d_str = f"{aota_event.d_hours or 0:02d}:{aota_event.d_minutes or 0:02d}:{aota_event.d_seconds or 0:05.2f}"
                report_d_str = f"{aota_report_data.get('d_hours', '?')}:{aota_report_data.get('d_minutes', '?')}:{aota_report_data.get('d_seconds', '?')}"
                warning_msg += f"  AOTA.xml:    {aota_d_str}\n"
                warning_msg += f"  AOTA Report: {report_d_str}\n\n"
            
            if r_differs:
                warning_msg += f"Reappearance (R):\n"
                aota_r_str = f"{aota_event.r_hours or 0:02d}:{aota_event.r_minutes or 0:02d}:{aota_event.r_seconds or 0:05.2f}"
                report_r_str = f"{aota_report_data.get('r_hours', '?')}:{aota_report_data.get('r_minutes', '?')}:{aota_report_data.get('r_seconds', '?')}"
                warning_msg += f"  AOTA.xml:    {aota_r_str}\n"
                warning_msg += f"  AOTA Report: {report_r_str}\n\n"
            
            warning_msg += "AOTA Report times will be used in the Excel report.\n"
            warning_msg += "Please verify which times are correct."
            
            print(f"WARNING: {warning_msg}")
            MessageBox.Show(warning_msg, "Time Difference Detected", 
                          MessageBoxButtons.OK, MessageBoxIcon.Warning)
    
    def _add_aota_to_existing_report(self, output_path, report_generator, aota_event):
        """Add AOTA data to an existing report by re-processing it
        
        Args:
            output_path: Path to the generated report file
            report_generator: The report generator instance used
            aota_event: AOTAEvent object with timing data
        """
        import os
        import zipfile
        import xml.etree.ElementTree as ET
        from tempfile import NamedTemporaryFile
        import shutil
        
        # Build AOTA replacements
        from aota_parser import format_aota_time_component, format_aota_error
        aota_replacements = {}
        
        # D (disappearance) times - use string representations to preserve precision
        if aota_event.d_hours is not None:
            aota_replacements['{{AOTA_D_HOURS}}'] = format_aota_time_component(hours=aota_event.d_hours)
            aota_replacements['{{AOTA_D_MINUTES}}'] = format_aota_time_component(minutes=aota_event.d_minutes)
            aota_replacements['{{AOTA_D_SECONDS}}'] = format_aota_time_component(seconds=aota_event.d_seconds, seconds_str=aota_event.d_seconds_str)
            aota_replacements['{{AOTA_D_ERROR}}'] = format_aota_error(aota_event.d_error, aota_event.d_error_str)
        
        # R (reappearance) times - use string representations to preserve precision
        if aota_event.r_hours is not None:
            aota_replacements['{{AOTA_R_HOURS}}'] = format_aota_time_component(hours=aota_event.r_hours)
            aota_replacements['{{AOTA_R_MINUTES}}'] = format_aota_time_component(minutes=aota_event.r_minutes)
            aota_replacements['{{AOTA_R_SECONDS}}'] = format_aota_time_component(seconds=aota_event.r_seconds, seconds_str=aota_event.r_seconds_str)
            aota_replacements['{{AOTA_R_ERROR}}'] = format_aota_error(aota_event.r_error, aota_event.r_error_str)
        
        # Create temporary file
        temp_file = NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name
        temp_file.close()
        
        try:
            # Process the existing report file
            with zipfile.ZipFile(output_path, 'r') as zf_in:
                with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as zf_out:
                    for item in zf_in.infolist():
                        data = zf_in.read(item.filename)
                        
                        # Process sheet XML files
                        if item.filename.startswith('xl/worksheets/') and item.filename.endswith('.xml'):
                            try:
                                xml_content = data.decode('utf-8')
                                # Replace AOTA placeholders
                                for placeholder, value in aota_replacements.items():
                                    if placeholder in xml_content:
                                        print(f"Replacing {placeholder} with {value} in {item.filename}")
                                    xml_content = xml_content.replace(placeholder, str(value))
                                data = xml_content.encode('utf-8')
                            except Exception as ex:
                                print(f"Error processing {item.filename}: {ex}")
                                pass  # Leave as-is if decoding fails
                        
                        # Process shared strings if present
                        elif item.filename == 'xl/sharedStrings.xml':
                            try:
                                xml_content = data.decode('utf-8')
                                for placeholder, value in aota_replacements.items():
                                    xml_content = xml_content.replace(placeholder, str(value))
                                data = xml_content.encode('utf-8')
                            except:
                                pass
                        
                        zf_out.writestr(item, data)
            
            # Replace original file with updated file
            shutil.move(temp_path, output_path)
            print(f"Successfully added AOTA data to report: {output_path}")
            
        except Exception as ex:
            # Clean up temp file on error
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
            raise ex
        
    def create_sequences_click(self, sender, e):
        """Handle create sequences button click"""
        selected_events = self.get_displayed_selected_events()
        if not selected_events:
            MessageBox.Show("Please select events to create sequences for.", "No Events Selected", 
                          MessageBoxButtons.OK, MessageBoxIcon.Information)
            return
        
        self.manager.selected_events = set(selected_events)
        
        # Show the template selection dialog once. The dialog contains a
        # checkbox 'Apply to All Events' which controls whether the chosen
        # template should be applied to every selected event or only to the
        # first (and prompt for each subsequent event).
        template_dialog = TemplateSelectionDialog(self.config, self.theme_manager)
        if template_dialog.ShowDialog() != DialogResult.OK:
            return

        template_path = template_dialog.get_selected_template_path()
        apply_all = getattr(template_dialog, 'apply_for_all', False)
        create_combined = getattr(template_dialog, 'create_combined', False)

        # If user requested a single combined file
        if create_combined:
            if apply_all:
                # Create combined for all selected events using the chosen template
                combined_path = self.create_combined_sequence_file(selected_events, template_path)
                if combined_path:
                    MessageBox.Show(f"Combined sequence file created: {os.path.basename(combined_path)}", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information)
                else:
                    MessageBox.Show("Failed to create combined sequence file.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
                return
            else:
                # Per-event templates for combined file: collect a map of per-event templates
                templates_map = {}
                for idx, ev in enumerate(selected_events):
                    if idx == 0:
                        templates_map[ev.event_id] = template_path
                    else:
                        per_dialog = TemplateSelectionDialog(self.config, self.theme_manager)
                        per_dialog.Text = f"Select Template for {ev.get_asteroid_display_name()}"
                        if per_dialog.ShowDialog() != DialogResult.OK:
                            # User cancelled; abort combined creation
                            templates_map = None
                            break
                        templates_map[ev.event_id] = per_dialog.get_selected_template_path()

                if not templates_map:
                    return

                combined_path = self.create_combined_sequence_file(selected_events, templates_map)
                if combined_path:
                    MessageBox.Show(f"Combined sequence file created: {os.path.basename(combined_path)}", "Success", MessageBoxButtons.OK, MessageBoxIcon.Information)
                else:
                    MessageBox.Show("Failed to create combined sequence file.", "Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
                return

        # Not creating combined: fall back to existing behaviour
        if apply_all:
            # Create sequences for all events using the selected template
            self.create_sequences_for_events(template_path)
        else:
            # Apply the initially chosen template to the first event, then prompt for each subsequent event individually.
            success = 0
            errors = 0
            for idx, ev in enumerate(selected_events):
                if idx == 0:
                    per_template = template_path
                else:
                    per_dialog = TemplateSelectionDialog(self.config, self.theme_manager)
                    per_dialog.Text = f"Select Template for {ev.get_asteroid_display_name()}"
                    if per_dialog.ShowDialog() != DialogResult.OK:
                        # User cancelled per-event selection; abort remaining events
                        break
                    per_template = per_dialog.get_selected_template_path()

                try:
                    ok = save_occultation_sequence(ev, per_template or "", self.config.get_sequence_path(), self.config)
                    if ok:
                        success += 1
                    else:
                        errors += 1
                except Exception as ex:
                    errors += 1
                    print(f"Error creating sequence for {ev.event_name}: {ex}")

            MessageBox.Show(f"Successfully created {success} of {success + errors} sequence files.", 
                           "Sequence Creation Complete", MessageBoxButtons.OK, MessageBoxIcon.Information)
    
    def create_sequences_for_events(self, template_path):
        """Create sequence files for selected events"""
        # `txt_sequence_path` is created by the configuration UI; guard in case
        # the main form doesn't have that control (fixes attribute errors).
        if hasattr(self, 'txt_sequence_path') and self.txt_sequence_path is not None:
            sequence_path = self.txt_sequence_path.Text
            # Persist the chosen path to config
            try:
                self.config.set_sequence_path(sequence_path)
            except Exception:
                pass
        else:
            sequence_path = self.config.get_sequence_path()
        
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
        combined_path = self.create_combined_sequence_file(selected_events, template_path)

        if combined_path:
            MessageBox.Show(f"Combined sequence file generated: {os.path.basename(combined_path)}", "Success", 
                        MessageBoxButtons.OK, MessageBoxIcon.Information)
        else:
            MessageBox.Show("Failed to generate combined sequence file.", "Error", 
                        MessageBoxButtons.OK, MessageBoxIcon.Error)

    def create_combined_sequence_file(self, events, template_path_or_map):
        """Create a single sequence file with all events in time order.

        template_path_or_map may be either:
        - a single template path (string) to use for all events, or
        - a dict mapping event identifiers (event.event_id) to template paths to
          allow per-event templates within the single combined file.
        """
        if not events:
            return False

        try:
            # Sort events by event time (preferred) and fall back to GOTO time if event time unavailable
            # This ensures the combined sequence lists events in chronological event-time order.
            sorted_events = sorted(
                events,
                key=lambda x: (
                    x.event_datetime if getattr(x, 'event_datetime', None) else (
                        x.goto_time if getattr(x, 'goto_time', None) else datetime.max
                    )
                )
            )

            # Generate filename
            date_str = datetime.utcnow().strftime('%Y%m%d')
            stations = set(event.station_name for event in events)
            station_name = list(stations)[0] if len(stations) == 1 else "MultiStation"
            combined_filename = f"{date_str}_{station_name}_Combined_Sequences.scs"
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
            combined_content.append("#" + "=" * 70)
            combined_content.append("")

            # Process each event and add its sequence content
            for i, event in enumerate(sorted_events, 1):
                self.update_status(f"Processing event {i}/{len(sorted_events)}: {event.event_name}")

                # Add event separator
                combined_content.append(f"# Event {i}: {event.get_asteroid_display_name()}")
                combined_content.append(f"# Time: {event.event_time} UTC")
                combined_content.append(f"# GOTO: {event.goto_time_str} UTC")
                combined_content.append(f"# Duration: {event.recording_duration}s")
                combined_content.append("#" + "-" * 50)

                # Determine the template to use for this event
                if isinstance(template_path_or_map, dict):
                    tpl_path = template_path_or_map.get(event.event_id) or template_path_or_map.get(event.event_name) or ""
                else:
                    tpl_path = template_path_or_map or ""

                # Load template content for this event
                template_content = TemplateManager.load_template(tpl_path, self.config) if tpl_path else None
                if not template_content:
                    # If no template available for this event, add a comment and continue
                    combined_content.append(f"# WARNING: Template not found for {event.get_asteroid_display_name()} (path: {tpl_path})")
                else:
                    try:
                        event_sequence = self.format_template(template_content, event)
                        combined_content.append(event_sequence)
                    except Exception as e:
                        combined_content.append(f"# ERROR: Could not generate sequence for {event.event_name}: {e}")
                        print(f"Error generating sequence for {event.event_name}: {e}")

                # Add spacing between events (except for last one)
                if i < len(sorted_events):
                    combined_content.append("")
                    combined_content.append("#" + "=" * 70)
                    combined_content.append("")

            # Write combined file
            with open(combined_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(combined_content))

            self.update_status(f"Combined sequence saved: {combined_filename}")
            # Return the path to the generated combined file for callers
            return combined_path

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
                goto_time_local=event.goto_time_local,
                pre_goto_time_local =   event.pre_goto_time_local
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
        from datetime import timezone
        today = datetime.utcnow().date()
        filtered_events = []
        for event in self.manager.all_events:
            if event.event_datetime and (event.event_datetime.replace(tzinfo=timezone.utc).astimezone() - timedelta(hours = 12)).date() == today:
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
        # Pass self as owner so the configuration dialog can refresh the
        # main UI immediately when settings (like display_utc) are changed.
        config_dialog.ShowDialog(self)
    
    def show_telescope_manager_click(self, sender, e):
        """Show telescope manager dialog"""
        from equipment_dialogs import TelescopeManagerDialog
        telescope_dialog = TelescopeManagerDialog(self.config, self.theme_manager)
        telescope_dialog.ShowDialog(self)
    
    def show_camera_manager_click(self, sender, e):
        """Show camera manager dialog"""
        from equipment_dialogs import CameraManagerDialog
        camera_dialog = CameraManagerDialog(self.config, self.theme_manager)
        camera_dialog.ShowDialog(self)
    
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

    def load_event_for_prep_click(self, sender, e):
        """Load the first selected event for preparation"""
        selected_events = self.get_displayed_selected_events()
        if len(selected_events) != 1:
            MessageBox.Show("Please select exactly one event from the grid", "Invalid Selection", 
                        MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        event = selected_events[0]
        
        # Load event for preparation
        self._preparation_event = event
        self.update_status(f"Loaded event for preparation: {event.get_asteroid_display_name()}")

        """Update the observation preparation display with current event info"""
        event = self._preparation_event
        # Combined display with all event info
        self.lbl_current_event.Text = (f"{event.get_asteroid_display_name()} at {event.event_time} UTC | "
                                       f"{event.star_alt:.0f}@{event.star_az:.0f} | "
                                       f"Exp: {event.exposure_ms}ms | Max Dur: {event.event_duration:.1f}s | "
                                       f"Star Mag: {event.star_mag:.1f}")

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
                            f"Exposure Set to : {event.exposure_ms}ms\n" +
                            f"Coords copied to clipboard: RA {event.ra:.4f}h, Dec {event.dec:.4f}°\n\n" +
                            f"Continue with testing or use SharpCap interface if you want to record manually.",
                            "Setup Complete", MessageBoxButtons.OK, MessageBoxIcon.Information)
            else:
                self.update_status("Failed to configure SharpCap")
                
                
        except Exception as ex:
            self.update_status(f"Error during setup: {ex}")
            MessageBox.Show(f"Error setting up event: {ex}", "Setup Error", 
                        MessageBoxButtons.OK, MessageBoxIcon.Error)

    def test_recording_click(self, sender, e):
        """Test recording using a temporary sequence for the selected event"""
        # Get selected events from grid
        selected_events = self.get_displayed_selected_events()
        
        if len(selected_events) != 1:
            MessageBox.Show("Please select exactly one event from the grid", "Invalid Selection", 
                        MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        event = selected_events[0]
        
        try:
            # Check for template file
            template_name = "SharpCap Test Recording Template.txt"
            template_folder = self.config.get_file_folder()
            template_path = os.path.join(template_folder, template_name)
            
            if not os.path.exists(template_path):
                MessageBox.Show(f"Template file not found: {template_name}\n\nPlease ensure the template exists in:\n{template_folder}", 
                            "Template Missing", MessageBoxButtons.OK, MessageBoxIcon.Warning)
                return
            
            # Create temporary sequence file
            temp_sequence_name = "temp_test_record.scs"
            sequence_path = self.config.get_sequence_path()
            temp_sequence_path = os.path.join(sequence_path, temp_sequence_name)
            
            self.update_status(f"Creating test recording sequence for {event.event_name}...")
            
            # Load template and generate sequence content manually to control filename
            from templates import TemplateManager
            template_content = TemplateManager.load_template(template_path, self.config)
            if not template_content:
                MessageBox.Show("Failed to load template file", "Error", 
                            MessageBoxButtons.OK, MessageBoxIcon.Error)
                return
            
            # Prepare event data for template substitution
            try:
                report_content = template_content.format(
                    object_name=event.object_name,
                    event_time=event.event_time,
                    start_time=event.start_time_str,
                    goto_time=event.goto_time_str,
                    recording_duration=format(event.recording_duration, '.0f'),
                    star_mag=format(event.star_mag, '.1f'),
                    comb_mag=format(event.comb_mag, '.1f'),
                    mag_drop=format(event.mag_drop, '.1f'),
                    time_error=format(event.event_uncertainty, '.1f'),
                    ra=format(event.ra, '.6f'),
                    dec=format(event.dec, '.6f'),
                    asteroid_name=event.object_name,
                    exposure=format(event.get_exposure_seconds(), '.3f'),
                    gain=event.gain_value,
                    event_time_local=event.event_time_local,
                    start_time_local=event.start_time_local,
                    goto_time_local=event.goto_time_local,
                    pre_goto_time_local=event.pre_goto_time_local
                )
                
                # Ensure directory exists
                if not os.path.exists(sequence_path):
                    os.makedirs(sequence_path, exist_ok=True)
                
                # Write the temporary sequence file
                with open(temp_sequence_path, 'w') as f:
                    f.write(report_content)
                    
            except Exception as write_error:
                MessageBox.Show(f"Failed to create test recording sequence:\n{write_error}", "Error", 
                            MessageBoxButtons.OK, MessageBoxIcon.Error)
                return
            
            # Save current camera settings before test recording
            saved_settings = {}
            try:
                if self.sharpcap.SelectedCamera:
                    camera = self.sharpcap.SelectedCamera
                    if hasattr(camera.Controls, 'Binning'):
                        saved_settings['binning'] = camera.Controls.Binning.Value
                        print(f"Saved Binning: {saved_settings['binning']}")
                    if hasattr(camera.Controls, 'Exposure'):
                        saved_settings['exposure'] = camera.Controls.Exposure.ExposureMs
                        print(f"Saved Exposure (ms): {saved_settings['exposure']}")
                    if hasattr(camera.Controls, 'Gain'):
                        saved_settings['gain'] = camera.Controls.Gain.Value
                        print(f"Saved Gain: {saved_settings['gain']}")
                    if hasattr(camera.Controls, 'Resolution'):
                        saved_settings['resolution'] = camera.Controls.Resolution.Value
                        print(f"Saved Resolution: {saved_settings['resolution']}")
                    if hasattr(camera.Controls, 'DisplayBlackLevel'):
                        saved_settings['display_black'] = camera.Controls.DisplayBlackLevel.Value
                        print(f"Saved DisplayBlackLevel: {saved_settings['display_black']}")
                    if hasattr(camera.Controls, 'DisplayMidLevel'):
                        saved_settings['display_mid'] = camera.Controls.DisplayMidLevel.Value
                        print(f"Saved DisplayMidLevel: {saved_settings['display_mid']}")
                    if hasattr(camera.Controls, 'DisplayWhiteLevel'):
                        saved_settings['display_white'] = camera.Controls.DisplayWhiteLevel.Value
                        print(f"Saved DisplayWhiteLevel: {saved_settings['display_white']}")
                    self.update_status(f"Camera settings saved (Exp: {saved_settings.get('exposure', 'N/A')}ms, Gain: {saved_settings.get('gain', 'N/A')})")
            except Exception as save_error:
                print(f"Warning: Could not save camera settings: {save_error}")
            
            # Run the sequence immediately
            self.update_status(f"Running test recording sequence...")
            
            try:
                self.sharpcap.Sequencer.RunSequenceFile(temp_sequence_path)
                self.update_status(f"Test recording completed for {event.event_name}")
                
                # Restore camera settings after test recording
                try:
                    if self.sharpcap.SelectedCamera and saved_settings:
                        camera = self.sharpcap.SelectedCamera
                        self.update_status("Restoring camera settings...")
                        
                        if 'binning' in saved_settings and hasattr(camera.Controls, 'Binning'):
                            print(f"Restoring Binning to: {saved_settings['binning']}")
                            camera.Controls.Binning.Value = saved_settings['binning']
                            print(f"Binning after restore: {camera.Controls.Binning.Value}")
                        
                        if 'exposure' in saved_settings and hasattr(camera.Controls, 'Exposure'):
                            print(f"Restoring Exposure to: {saved_settings['exposure']} ms")
                            camera.Controls.Exposure.ExposureMs = saved_settings['exposure']
                            print(f"Exposure after restore: {camera.Controls.Exposure.ExposureMs} ms")
                            exposure_to_wait = saved_settings['exposure']
                        else:
                            exposure_to_wait = 100  # Default if exposure not saved
                        
                        if 'gain' in saved_settings and hasattr(camera.Controls, 'Gain'):
                            print(f"Restoring Gain to: {saved_settings['gain']}")
                            camera.Controls.Gain.Value = saved_settings['gain']
                            print(f"Gain after restore: {camera.Controls.Gain.Value}")
                        
                        if 'resolution' in saved_settings and hasattr(camera.Controls, 'Resolution'):
                            print(f"Restoring Resolution to: {saved_settings['resolution']}")
                            camera.Controls.Resolution.Value = saved_settings['resolution']
                            print(f"Resolution after restore: {camera.Controls.Resolution.Value}")
                        
                        # Wait 2x the restored exposure time
                        import time
                        wait_time = (exposure_to_wait * 2) / 1000.0  # Convert ms to seconds
                        self.update_status(f"Waiting {wait_time:.1f}s for camera to stabilize...")
                        time.sleep(wait_time)
                        
                        # Restore display levels
                        try:
                            if 'display_black' in saved_settings and hasattr(camera.Controls, 'DisplayBlackLevel'):
                                print(f"Restoring DisplayBlackLevel to: {saved_settings['display_black']}")
                                camera.Controls.DisplayBlackLevel.Value = saved_settings['display_black']
                            if 'display_mid' in saved_settings and hasattr(camera.Controls, 'DisplayMidLevel'):
                                print(f"Restoring DisplayMidLevel to: {saved_settings['display_mid']}")
                                camera.Controls.DisplayMidLevel.Value = saved_settings['display_mid']
                            if 'display_white' in saved_settings and hasattr(camera.Controls, 'DisplayWhiteLevel'):
                                print(f"Restoring DisplayWhiteLevel to: {saved_settings['display_white']}")
                                camera.Controls.DisplayWhiteLevel.Value = saved_settings['display_white']
                            self.update_status("Display levels restored")
                        except Exception as display_error:
                            print(f"Warning: Could not restore display levels: {display_error}")
                        
                        self.update_status("Camera settings restored")
                        
                except Exception as restore_error:
                    print(f"Warning: Could not restore camera settings: {restore_error}")
                    self.update_status(f"Warning: Settings restoration incomplete")
                
                MessageBox.Show(f"Test recording sequence completed for:\n\n{event.get_asteroid_display_name()}\n\nCamera settings have been restored.", 
                            "Test Recording Completed", MessageBoxButtons.OK, MessageBoxIcon.Information)
            except Exception as seq_error:
                MessageBox.Show(f"Failed to run test recording sequence:\n{seq_error}", "Sequence Error", 
                            MessageBoxButtons.OK, MessageBoxIcon.Error)
                self.update_status(f"Failed to start test recording: {seq_error}")
                
        except Exception as ex:
            self.update_status(f"Error during test recording: {ex}")
            MessageBox.Show(f"Error creating test recording: {ex}", "Error", 
                        MessageBoxButtons.OK, MessageBoxIcon.Error)

    def apply_event_parameters_to_sharpcap(self, event):
        """Apply event parameters to SharpCap interface"""
        try:
                       
            # Set exposure time
            if self.sharpcap.SelectedCamera:
                camera = self.sharpcap.SelectedCamera
                if hasattr(camera.Controls, 'Exposure'):
                    camera.Controls.Exposure.ExposureMs = event.exposure_ms
                    print(f"Set exposure to {event.exposure_ms:.0f} ms")
            
            # Set target name/coordinates in SharpCap (if supported)
            try:
                target_name = f"{event.get_asteroid_display_name()}_{event.station_name}"
                self.sharpcap.TargetName = target_name
                print(f"Target: {target_name} at RA {event.ra:.6f}h, Dec {event.dec:.6f}°")
            except:
                pass
            print(f"Target coords copied to clipboard: {target_name} at RA {event.ra:.6f}h, Dec {event.dec:.6f}°")
            System.Windows.Forms.Clipboard.SetText(f"{event.ra:.6f}, {event.dec:.6f}")

            return True
            
        except Exception as e:
            print(f"Error applying parameters to SharpCap: {e}")
            return False

    def goto_and_center_click(self, sender, e):
        """Execute GOTO and wait for mount to settle"""
        if not self._preparation_event:
            MessageBox.Show("Please load an event first using 'Load Event' button", "No Event Loaded", 
                        MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        event = self._preparation_event
        
        try:
            self.update_status(f"Executing GOTO: {event.get_asteroid_display_name()}...")
            
            # Execute GOTO sequence
            success = self.execute_complete_goto_sequence(event)
            
            if success:
                MessageBox.Show(f"GOTO completed!\n\n" +
                            f"Target: {event.get_asteroid_display_name()}\n" +
                            f"RA: {event.ra:.4f}h, Dec: {event.dec:.4f}°\n\n" +
                            f"Next: Click 'Plate Solve' to verify position",
                            "GOTO Complete", MessageBoxButtons.OK, MessageBoxIcon.Information)
            else:
                self.update_status("GOTO failed")
                MessageBox.Show("GOTO failed. Please check mount connection and try again.",
                              "GOTO Failed", MessageBoxButtons.OK, MessageBoxIcon.Error)
                
        except Exception as ex:
            self.update_status(f"GOTO error: {ex}")
            MessageBox.Show(f"GOTO error: {ex}", "Error", 
                        MessageBoxButtons.OK, MessageBoxIcon.Error)
            MessageBox.Show(f"GOTO & center error: {ex}", "Error", 
                        MessageBoxButtons.OK, MessageBoxIcon.Error)

    def execute_complete_goto_sequence(self, event):
        """Execute the complete GOTO sequence with error handling"""
        try:
            # Step 1: GOTO (this will block until GOTO completes)
            self.update_status("Step 1: Executing GOTO...")
            goto_success = self.execute_goto_command(event)
            
            if not goto_success:
                return False

            
            # GOTO complete - user can now manually verify position with Plate Solve button
            self.update_status("GOTO complete. Now use 'Plate Solve' to verify position and label the target.")
            return True
            
        except Exception as e:
            print(f"GOTO sequence error: {e}")
            return False

    def verify_goto_position(self, event):
        """Verify mount position after GOTO by plate solving and checking distance from target.
        Returns: 'success' if within tolerance, 'retry' if user wants to retry, 'failed' if plate solve failed"""
        import math
        
        try:
            # Capture and plate solve
            if not self.sharpcap.SelectedCamera:
                print("Camera not selected for position verification")
                return "failed"
            
            # Perform plate solve to get current mount position
            result = self.sharpcap.SafeGetAsyncResult(
                self.sharpcap.BlindSolver.SolveAsync(self.plate_solve_purpose.Annotation, CancellationToken())
            )
            
            if not result or str(type(result)) != "<class 'RADecPosition'>":
                print(f"Plate solve failed during position verification: {result}")
                return "failed"
            
            # Get current mount position from plate solve result
            current_ra = result.RightAscension  # in hours
            current_dec = result.Declination    # in degrees
            
            # Target position
            target_ra = event.ra    # in hours
            target_dec = event.dec  # in degrees
            
            # Calculate angular separation in degrees
            # Convert RA from hours to degrees for calculation
            ra1_deg = current_ra * 15.0
            ra2_deg = target_ra * 15.0
            
            # Use spherical trigonometry to calculate angular separation
            # d = arccos(sin(dec1)*sin(dec2) + cos(dec1)*cos(dec2)*cos(ra1-ra2))
            dec1_rad = math.radians(current_dec)
            dec2_rad = math.radians(target_dec)
            ra_diff_rad = math.radians(ra1_deg - ra2_deg)
            
            cos_distance = (math.sin(dec1_rad) * math.sin(dec2_rad) + 
                          math.cos(dec1_rad) * math.cos(dec2_rad) * math.cos(ra_diff_rad))
            
            # Clamp to [-1, 1] to avoid domain errors from floating point precision
            cos_distance = max(-1.0, min(1.0, cos_distance))
            distance_deg = math.degrees(math.acos(cos_distance))
            
            print(f"Position check - Current: RA {current_ra:.4f}h, Dec {current_dec:.4f}°")
            print(f"Position check - Target: RA {target_ra:.4f}h, Dec {target_dec:.4f}°")
            print(f"Position check - Distance: {distance_deg:.4f}°")
            
            # Check if within tolerance (0.05 degrees)
            tolerance = 0.05
            if distance_deg <= tolerance:
                self.update_status(f"Position verified: {distance_deg:.2f}° from target (within {tolerance:.2f}° tolerance)")
                return "success"
            else:
                # Position is off - prompt user
                message = (f"Mount position is off target!\n\n"
                          f"Current position:\n"
                          f"  RA: {current_ra:.4f}h, Dec: {current_dec:.4f}°\n\n"
                          f"Target position:\n"
                          f"  RA: {target_ra:.4f}h, Dec: {target_dec:.4f}°\n\n"
                          f"Distance from target: {distance_deg:.2f}° (tolerance: {tolerance:.2f}°)\n\n"
                          f"Redo the GOTO and Plate Solve to get closer.\n"
                          f"You might need to plate solve and sync manually")
                
                result = MessageBox.Show(message, "Position Check Failed", 
                                       MessageBoxButtons.OKCancel, MessageBoxIcon.Information)
                
                if result == DialogResult.OK:
                    self.update_status("User requested retry of GOTO sequence")
                    return "retry"
                else:
                    self.update_status(f"User accepted position error of {distance_deg:.4f}°")
                    return "success"
                    
        except Exception as e:
            print(f"Error verifying GOTO position: {e}")
            return "failed"

    def plate_solve_label_click(self, sender, e):
        """Plate solve, verify position, and label the target star"""
        if not self._preparation_event:
            MessageBox.Show("Please load an event first using 'Load Event' button", "No Event Loaded", 
                        MessageBoxButtons.OK, MessageBoxIcon.Warning)
            return
        
        event = self._preparation_event
        
        try:
            self.update_status("Plate solving and verifying position...")
            
            # First, verify the GOTO position
            position_check = self.verify_goto_position(event)
            
            if position_check == "retry":
                # User wants to retry GOTO
                self.update_status("Please click 'GOTO & Center' to reposition mount")
                return
            elif position_check == "failed":
                self.update_status("Plate solve failed during position verification")
                MessageBox.Show("Plate solve failed. Please check camera settings and try again.",
                              "Plate Solve Failed", MessageBoxButtons.OK, MessageBoxIcon.Error)
                return
            
            # Position is good, now mark the target star
            self.update_status("Position verified, labeling target...")
            success = self.plate_solve_and_mark_star(event, checkStarInFOV=True)
            
            if success == True:
                self.update_status(f"Target labeled: {event.get_asteroid_display_name()}")
                MessageBox.Show(f"Position verified and target labeled!\n\n" +
                            f"Object: {event.get_asteroid_display_name()}\n" +
                            f"Coordinates: RA {event.ra:.4f}h, Dec {event.dec:.4f}°\n" +
                            f"Star Magnitude: {event.star_mag:.1f}\n\n" +
                            f"Ready for observation",
                            "Target Labeled", MessageBoxButtons.OK, MessageBoxIcon.Information)
            elif isinstance(success, str):
                self.update_status(f"Target labeling failed: {success}")
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