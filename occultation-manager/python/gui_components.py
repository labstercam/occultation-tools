import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

import webbrowser
from datetime import datetime, timezone
from System.Drawing import Color, Font, FontStyle, SystemColors
from System.Windows.Forms import (
    DataGridView, DataGridViewSelectionMode, DataGridViewCheckBoxColumn,
    DataGridViewLinkColumn, DataGridViewTextBoxColumn, MessageBox,
    MessageBoxButtons, MessageBoxIcon, DataGridViewDataErrorContexts, SortOrder,
    DataGridViewAutoSizeColumnsMode
)
from System.Windows.Forms import DataGridViewAutoSizeColumnMode

class EventsDataGrid(DataGridView):
    """Enhanced DataGridView for displaying occultation events with all requested columns"""
    
    def __init__(self):
        DataGridView.__init__(self)
        self.events = []
        # Sort state: default is datetime ascending (oldest first)
        self._sort_col_name = 'DateTime'
        self._sort_ascending = True
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
            ("Gain", "Gain", 50, False),
            ("Record (s)", "RecordingTime", 70, False),  # Changed name as requested
            ("Max Dur (s)", "MaxDuration", 70, False),      # Added as requested
#            ("Error (s)", "TimeError", 60, False),           # Added as requested
            ("Alt-Az", "Altitude", 60, False),                       # Added as requested
#            ("Az", "Azimuth", 55, False),                         # Added as requested
#            ("Coordinates", "Coordinates", 120, False),
      #      ("OWC", "OWCLink", 50, False),                        # Added as requested
            ("Status", "Status", 55, False)
        ]
        
        for name, data_name, width, editable in columns:
            if data_name == "Selected":
                col = DataGridViewCheckBoxColumn()
            elif name in ("Event Name","OWC"):
                col = DataGridViewLinkColumn()
                # Ensure the link remains visible when the row is selected by
                # using the system highlight text color for selection foreground
                try:
                    col.LinkColor = SystemColors.MenuHighlight
                    col.ActiveLinkColor = SystemColors.Highlight
                    col.VisitedLinkColor = SystemColors.GrayText
                    # Use white so the link text contrasts with the selection
                    # background (blue in light mode, dark orange in dark/night mode).
                    col.DefaultCellStyle.SelectionForeColor = Color.White
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
        # Set sensible per-column autosize modes so columns grow to fit their
        # content (headers + cell text) and respect DPI/font scaling.
        # Note: AllCells mode causes a spinning wait cursor on hover because the
        # grid continuously remeasures content during paint/mouse-move events.
        # Instead we fix column widths in update_events() via AutoResizeColumns().
        try:
            for col in self.Columns:
                try:
                    # Keep the selection checkbox a fixed small column
                    if col.Name == "Selected":
                        # 'None' is a reserved Python name; fetch the enum member by name
                        try:
                            none_mode = getattr(DataGridViewAutoSizeColumnMode, 'None')
                        except Exception:
                            none_mode = None
                        if none_mode is not None:
                            col.AutoSizeMode = none_mode
                        # Keep the specified fixed width
                        col.Width = max(24, col.Width)
                    else:
                        # NotSet — let update_events() do a one-shot resize via AutoResizeColumns()
                        col.AutoSizeMode = DataGridViewAutoSizeColumnMode.NotSet
                except Exception:
                    pass
        except Exception:
            pass
        # Handle cell events
        self.CellDoubleClick += self.cell_double_click
        self.CellContentClick += self.cell_content_click
        # Handle checkbox changes immediately
        self.CurrentCellDirtyStateChanged += self.current_cell_dirty_state_changed
        self.CellValueChanged += self.cell_value_changed
        # Column-header click for user-driven sorting
        self.ColumnHeaderMouseClick += self._on_column_header_click
        # Update EventName link color when row selection changes so the link
        # text stays visible against the selection highlight background.
        self.SelectionChanged += self._on_selection_changed
        
    
    def _on_selection_changed(self, sender, e):
        """Update EventName link color: white when row is selected, default otherwise."""
        try:
            default_color = SystemColors.MenuHighlight
            for row in self.Rows:
                try:
                    cell = row.Cells["EventName"]
                    color = Color.White if row.Selected else default_color
                    cell.LinkColor = color
                    cell.VisitedLinkColor = color
                except Exception:
                    pass
        except Exception:
            pass

    def cell_double_click(self, sender, e):
        """Handle cell double click for settings editing (exposure, gain, recording duration)"""
        if e.RowIndex >= 0 and e.ColumnIndex >= 0:
            column_name = self.Columns[e.ColumnIndex].Name
            if column_name in ("ExposureMs", "Gain", "RecordingTime"):
                event = self.Rows[e.RowIndex].Tag
                if event:
                    parent_form = self.FindForm()
                    if hasattr(parent_form, 'edit_event_exposure'):
                        parent_form.edit_event_exposure(event)
    
    def cell_content_click(self, sender, e):
        """Handle cell content click for OWC links"""
        if e.RowIndex >= 0 and e.ColumnIndex >= 0:
            if self.Columns[e.ColumnIndex].Name in ("EventName", "OWCLink"):
                event = self.Rows[e.RowIndex].Tag
                if event and hasattr(event, 'owcloudurl') and event.owcloudurl:
                    try:
                        # 1. Station-specific event page (original URL)
                        webbrowser.open(event.owcloudurl)
                        # 2. General event page (remove station ID suffix)
                        parent_url = event.owcloudurl.rsplit('/', 1)[0]
                        if parent_url != event.owcloudurl:
                            webbrowser.open_new_tab(parent_url)
                        # 3. Aladin 0.5° FOV chart
                        if event.ra and event.dec is not None:
                            from gui_dialogs import _build_aladin_url
                            aladin_url = _build_aladin_url(event.ra, event.dec, fov=0.5)
                            webbrowser.open_new_tab(aladin_url)
                    except Exception as ex:
                        MessageBox.Show(f"Cannot open URL: {event.owcloudurl}\nError: {ex}", "Error", 
                                      MessageBoxButtons.OK, MessageBoxIcon.Error)
    
    def current_cell_dirty_state_changed(self, sender, e):
        """Handle checkbox state change immediately to update selection count"""
        # When a checkbox is clicked, commit the edit immediately so the SelectionChanged event
        # sees the updated value
        if self.IsCurrentCellDirty:
            self.CommitEdit(DataGridViewDataErrorContexts.Commit)
    
    def cell_value_changed(self, sender, e):
        """Handle cell value changed - update summary when checkbox is toggled"""
        if e.RowIndex >= 0 and e.ColumnIndex >= 0:
            if self.Columns[e.ColumnIndex].Name == "Selected":
                # Update the selection summary immediately when checkbox changes
                parent_form = self.FindForm()
                if parent_form and hasattr(parent_form, 'update_selection_summary'):
                    parent_form.update_selection_summary()
    
    def _on_column_header_click(self, sender, e):
        """Sort by the clicked column; toggle direction if already sorted by that column."""
        col = self.Columns[e.ColumnIndex]
        if col.Name == 'Selected':
            return  # checkbox column — not sortable
        if self._sort_col_name == col.Name:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_col_name = col.Name
            self._sort_ascending = True
        self.update_events(self.events)

    def _sort_key(self, ev):
        """Return a sort key for the given event based on the current sort column."""
        name = self._sort_col_name
        if name == 'DateTime':
            return ev.event_datetime if ev.event_datetime else datetime.min
        if name == 'EventName':
            return (ev.get_asteroid_display_name() or '').lower()
        if name == 'StationName':
            return (ev.station_name or '').lower()
        if name == 'StarMag':
            return ev.star_mag or 0
        if name == 'CombMag':
            return ev.comb_mag or 0
        if name == 'MagDrop':
            return ev.mag_drop or 0
        if name == 'ExposureMs':
            return ev.exposure_ms or 0
        if name == 'Gain':
            return ev.gain_value or 0
        if name == 'RecordingTime':
            return ev.recording_duration or 0
        if name == 'MaxDuration':
            return ev.max_duration_seconds or 0
        if name == 'Altitude':
            return ev.star_alt or 0
        if name == 'Status':
            return (ev.get_status_info() or '').lower()
        return ''

    def _apply_sort_glyphs(self):
        """Update column header sort glyph arrows to match the current sort state."""
        try:
            none_sort = getattr(SortOrder, 'None')
            for col in self.Columns:
                try:
                    if col.Name == self._sort_col_name:
                        col.HeaderCell.SortGlyphDirection = (
                            SortOrder.Ascending if self._sort_ascending else SortOrder.Descending)
                    else:
                        col.HeaderCell.SortGlyphDirection = none_sort
                except Exception:
                    pass
        except Exception:
            pass

    def update_events(self, events):
        """Update the grid with enhanced events data"""
        self.events = events
        # Apply current sort order before populating
        try:
            sorted_events = sorted(events, key=self._sort_key, reverse=not self._sort_ascending)
        except Exception:
            sorted_events = list(events)
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

        for event in sorted_events:
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
            
            # Show gain with custom indicator
            gain_text = str(event.gain_value)
            if event.has_custom_gain():
                gain_text += "*"
            row.Cells["Gain"].Value = gain_text
            
            duration_text = str(event.recording_duration)
            if event.has_custom_recording_duration():
                duration_text += "*"
            row.Cells["RecordingTime"].Value = duration_text
            row.Cells["MaxDuration"].Value = f"{event.max_duration_seconds:.1f}" if event.max_duration_seconds > 0 else "N/A"
#            row.Cells["TimeError"].Value = f"{event.uncertainty_seconds:.1f}" if event.uncertainty_seconds > 0 else "N/A"
            row.Cells["Altitude"].Value = f"{event.star_alt:.0f}@{event.star_az:.0f}"
            
            #row.Cells["Altitude"].Value = f"{event.star_alt:.1f}°" if event.star_alt > 0 else "N/A"
            #row.Cells["Azimuth"].Value = f"{event.star_az:.1f}°" if event.star_az > 0 else "N/A"
#            row.Cells["Coordinates"].Value = event.get_coordinates_string()
#            row.Cells["OWCLink"].Value = "OWC" if hasattr(event, 'owcloudurl') and event.owcloudurl else ""
            row.Cells["Status"].Value = event.get_status_info()
            row.Tag = event

        # After populating rows, perform an autosize pass so column widths are
        # adjusted based on the actual rendered text and current font (DPI-aware).
        try:
            # Auto-resize columns based on content for displayed cells, then fix widths
            # so the grid doesn't continuously remeasure (which causes a wait cursor).
            self.AutoResizeColumns(DataGridViewAutoSizeColumnsMode.AllCells)
            # Freeze widths at their current measured size
            try:
                not_set = DataGridViewAutoSizeColumnMode.NotSet
                none_mode = getattr(DataGridViewAutoSizeColumnMode, 'None')
            except Exception:
                not_set = None
                none_mode = None
            for col in self.Columns:
                try:
                    if col.Name == 'Selected':
                        if none_mode is not None:
                            col.AutoSizeMode = none_mode
                    elif not_set is not None:
                        col.AutoSizeMode = not_set
                except Exception:
                    pass
            # Some columns (like DateTime or EventName) may benefit from keeping
            # a little extra space; ensure a minimum width scaled by font height
            try:
                min_extra = int(round((self.Font.Height or 12) * 1.5))
            except Exception:
                min_extra = 18
            for col in self.Columns:
                try:
                    if col.Name != 'Selected':
                        col.Width = col.Width + min_extra
                except Exception:
                    pass
        except Exception:
            # Non-fatal if autosize fails in some environments
            pass
        # Update sort indicator arrows on column headers
        self._apply_sort_glyphs()

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