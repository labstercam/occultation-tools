import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

import webbrowser
from System.Drawing import Font, FontStyle, SystemColors
from datetime import timezone
from System.Windows.Forms import (
    DataGridView, DataGridViewSelectionMode, DataGridViewCheckBoxColumn,
    DataGridViewLinkColumn, DataGridViewTextBoxColumn, MessageBox,
    MessageBoxButtons, MessageBoxIcon
)

class EventsDataGrid(DataGridView):
    """Enhanced DataGridView for displaying occultation events with all requested columns"""
    
    def __init__(self):
        DataGridView.__init__(self)
        self.events = []
        self.setup_grid()
    
    def setup_grid(self):
        """Setup the enhanced data grid columns and properties"""
        self.AutoGenerateColumns = False
        self.AllowUserToAddRows = False
        self.AllowUserToDeleteRows = False
        self.SelectionMode = DataGridViewSelectionMode.FullRowSelect
        self.MultiSelect = True
        # Hide the row header column (left-most header) to remove the small
        # index/selector column and make the grid cleaner.
        try:
            self.RowHeadersVisible = False
            # some environments may still show a thin border; set width to 0
            self.RowHeadersWidth = 0
        except Exception:
            pass
        
        # Enhanced column layout with all requested fields
        columns = [
            ("", "Selected", 35, True),
            ("Event Name", "EventName", 130, False),
            ("Station", "StationName", 110, False),  # Added station name column
            ("Date/Time UTC", "DateTime", 140, False),
            ("Mag", "StarMag", 45, False),
            ("Comb", "CombMag", 45, False),
            ("Drop", "MagDrop", 45, False),
            ("Exp (ms)", "ExposureMs", 70, False),
            ("Record (s)", "RecordingTime", 70, False),  # Changed name as requested
            ("Max Dur (s)", "MaxDuration", 70, False),      # Added as requested
#            ("Error (s)", "TimeError", 60, False),           # Added as requested
            ("Alt-Az", "Altitude", 60, False),                       # Added as requested
#            ("Az", "Azimuth", 55, False),                         # Added as requested
#            ("Coordinates", "Coordinates", 120, False),
            ("OWC", "OWCLink", 50, False),                        # Added as requested
            ("Status", "Status", 55, False)
        ]
        
        for name, data_name, width, editable in columns:
            if data_name == "Selected":
                col = DataGridViewCheckBoxColumn()
            elif name == "OWC":
                col = DataGridViewLinkColumn()
                # Ensure the link remains visible when the row is selected by
                # using the system highlight text color for selection foreground
                try:
                    col.LinkColor = SystemColors.MenuHighlight
                    col.ActiveLinkColor = SystemColors.Highlight
                    col.VisitedLinkColor = SystemColors.GrayText
                    # Use the system highlight text color so the link text contrasts
                    # with the selection background set by the OS/theme.
                    col.DefaultCellStyle.SelectionForeColor = SystemColors.HighlightText
                except Exception:
                    # Defensive: ignore if any of these properties are unavailable
                    pass
            else:
                col = DataGridViewTextBoxColumn()
            
            col.Name = data_name
            col.HeaderText = name
            col.Width = width
            col.ReadOnly = not editable
            self.Columns.Add(col)
        
        # Handle cell events
        self.CellDoubleClick += self.cell_double_click
        self.CellContentClick += self.cell_content_click
        
    
    def cell_double_click(self, sender, e):
        """Handle cell double click for exposure editing"""
        if e.RowIndex >= 0 and e.ColumnIndex >= 0:
            if self.Columns[e.ColumnIndex].Name == "ExposureMs":
                event = self.Rows[e.RowIndex].Tag
                if event:
                    parent_form = self.FindForm()
                    if hasattr(parent_form, 'edit_event_exposure'):
                        parent_form.edit_event_exposure(event)
    
    def cell_content_click(self, sender, e):
        """Handle cell content click for OWC links"""
        if e.RowIndex >= 0 and e.ColumnIndex >= 0:
            if self.Columns[e.ColumnIndex].Name == "OWCLink":
                event = self.Rows[e.RowIndex].Tag
                if event and hasattr(event, 'owcloudurl') and event.owcloudurl:
                    try:
                        webbrowser.open(event.owcloudurl)
                    except Exception as ex:
                        MessageBox.Show(f"Cannot open URL: {event.owcloudurl}\nError: {ex}", "Error", 
                                      MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def update_events(self, events):
        """Update the grid with enhanced events data"""
        self.events = events
        self.Rows.Clear()
        # Determine display preference (UTC vs Local) from parent form config if available
        display_utc = True
        parent_form = self.FindForm()
        if parent_form and hasattr(parent_form, 'config'):
            try:
                display_utc = parent_form.config.get_display_utc()
            except Exception:
                display_utc = True

        # Update column header to reflect whether UTC or Local is shown
        try:
            if display_utc:
                self.Columns["DateTime"].HeaderText = "Date/Time UTC"
            else:
                self.Columns["DateTime"].HeaderText = "Date/Time Local"
        except Exception:
            pass

        for event in events:
            row = self.Rows[self.Rows.Add()]
            row.Cells["Selected"].Value = event.selected
            row.Cells["EventName"].Value = event.get_asteroid_display_name()  # Using enhanced name resolution
            row.Cells["StationName"].Value = event.station_name  # Added station name data
            # Show UTC or Local time according to config
            if not event.event_date:
                row.Cells["DateTime"].Value = "N/A"
            else:
                time_error = f"±{event.uncertainty_seconds:.0f}s"
                try:
                    if display_utc:
                        row.Cells["DateTime"].Value = f"{event.event_date} {event.event_time_utc}{time_error}" 
                    else:
                        # Compute local date from stored event_datetime (assumed UTC)
                        if getattr(event, 'event_datetime', None):
                            local_dt = event.event_datetime.replace(tzinfo=timezone.utc).astimezone()
                            local_date = local_dt.strftime('%Y-%m-%d')
                        else:
                            local_date = event.event_date
                        # event.event_time_local is prepared in OccultationEvent
                        local_time = getattr(event, 'event_time_local', '')
#                        row.Cells["DateTime"].Value = f"{local_date} {local_time}"
                        row.Cells["DateTime"].Value = local_dt.strftime('%Y-%m-%d %H:%M:%S') + time_error
                except Exception:
                    row.Cells["DateTime"].Value = f"{event.event_date} {event.event_time_utc}{time_error}"
            row.Cells["StarMag"].Value = f"{event.star_mag:.1f}" if event.star_mag > 0 else "N/A"
            row.Cells["CombMag"].Value = f"{event.comb_mag:.1f}" if event.comb_mag > 0 else "N/A"
            row.Cells["MagDrop"].Value = f"{event.mag_drop:.1f}" if event.mag_drop > 0 else "N/A"
            
            # Show custom exposure indicator
            exposure_text = str(event.exposure_ms)
            if event.has_custom_exposure():
                exposure_text += "*"
            row.Cells["ExposureMs"].Value = exposure_text
            
            row.Cells["RecordingTime"].Value = str(event.recording_duration)
            row.Cells["MaxDuration"].Value = f"{event.max_duration_seconds:.1f}" if event.max_duration_seconds > 0 else "N/A"
#            row.Cells["TimeError"].Value = f"{event.uncertainty_seconds:.1f}" if event.uncertainty_seconds > 0 else "N/A"
            row.Cells["Altitude"].Value = f"{event.star_alt:.0f}@{event.star_az:.0f}"
            
            #row.Cells["Altitude"].Value = f"{event.star_alt:.1f}°" if event.star_alt > 0 else "N/A"
            #row.Cells["Azimuth"].Value = f"{event.star_az:.1f}°" if event.star_az > 0 else "N/A"
#            row.Cells["Coordinates"].Value = event.get_coordinates_string()
            row.Cells["OWCLink"].Value = "OWC" if hasattr(event, 'owcloudurl') and event.owcloudurl else ""
            row.Cells["Status"].Value = event.get_status_info()
            row.Tag = event
    
    def get_selected_events(self):
        """Get list of selected events"""
        selected = []
        for row in self.Rows:
            if row.Cells["Selected"].Value:
                selected.append(row.Tag)
        return selected
    
    def select_all_events(self, select=True):
        """Select or deselect all events"""
        for row in self.Rows:
            row.Cells["Selected"].Value = select
            if row.Tag:
                row.Tag.selected = select

    def toggle_all_events(self,status=False):
        """Select or deselect all events based on status"""
        print(
            f"Toggling all events to {'selected' if status else 'deselected'}"
        )
        for row in self.Rows:
            row.Cells["Selected"].Value = status
            if row.Tag:
                row.Tag.selected = status