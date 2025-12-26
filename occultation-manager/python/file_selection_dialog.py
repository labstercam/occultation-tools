"""
Combined AOTA and Tangra CSV File Selection Dialog
Allows selection of both files from a single folder in one dialog
"""

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("System")

import os
import System
from System.Drawing import Point, Size, Color, Font, FontStyle
from System.Windows.Forms import (
    Form, Button, Label, ListBox, Panel, TextBox, GroupBox,
    AnchorStyles, DockStyle, Padding, DialogResult,
    FormStartPosition, MessageBox, MessageBoxButtons, MessageBoxIcon,
    FolderBrowserDialog, SelectionMode
)
from theme import apply_theme_to_control


class CombinedFileSelectionDialog(Form):
    """Dialog for selecting both AOTA and Tangra CSV files from a single folder"""
    
    def __init__(self, theme_manager, asteroid_name="", observation_type="Positive"):
        """Initialize the dialog
        
        Args:
            theme_manager: Theme manager for consistent styling
            asteroid_name: Name of the asteroid for display
            observation_type: Type of observation (determines if AOTA is required)
        """
        Form.__init__(self)
        self.theme_manager = theme_manager
        self.asteroid_name = asteroid_name
        self.observation_type = observation_type
        self.selected_aota_path = None
        self.selected_tangra_path = None
        self.aota_files = []
        self.csv_files = []
        
        self.setup_ui()
        
        # Apply theme using the correct method
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup user interface"""
        self.Text = "Select Observation Files"
        self.Size = Size(900, 600)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        # Header label
        header = Label()
        header.Text = f"Select AOTA and Tangra CSV Files"
        if self.asteroid_name:
            header.Text += f" for {self.asteroid_name}"
        header.Font = Font(header.Font.FontFamily, 10, FontStyle.Bold)
        header.Location = Point(20, 20)
        header.Size = Size(850, 25)
        self.Controls.Add(header)
        
        # Instructions label
        instructions = Label()
        instructions.Text = "1. Select folder containing observation files (AOTA and Tangra CSV)\n" + \
                           "2. Choose files from the lists below"
        instructions.Location = Point(20, 55)
        instructions.Size = Size(850, 40)
        self.Controls.Add(instructions)
        
        # Folder selection panel
        folder_panel = Panel()
        folder_panel.Location = Point(20, 105)
        folder_panel.Size = Size(850, 30)
        self.Controls.Add(folder_panel)
        
        # Folder path textbox
        self.folder_textbox = TextBox()
        self.folder_textbox.Location = Point(0, 0)
        self.folder_textbox.Size = Size(720, 25)
        self.folder_textbox.ReadOnly = True
        folder_panel.Controls.Add(self.folder_textbox)
        
        # Browse button
        browse_button = Button()
        browse_button.Text = "Browse Folder..."
        browse_button.Location = Point(730, 0)
        browse_button.Size = Size(120, 25)
        browse_button.Click += self.browse_folder_click
        folder_panel.Controls.Add(browse_button)
        
        # AOTA files group (left side)
        aota_group = GroupBox()
        aota_group.Text = "AOTA Files (.aota.xml)"
        aota_group.Location = Point(20, 145)
        aota_group.Size = Size(420, 340)
        self.Controls.Add(aota_group)
        
        # AOTA count label
        self.aota_count_label = Label()
        self.aota_count_label.Text = "No folder selected"
        self.aota_count_label.Location = Point(10, 20)
        self.aota_count_label.Size = Size(400, 20)
        aota_group.Controls.Add(self.aota_count_label)
        
        # AOTA files listbox
        self.aota_listbox = ListBox()
        self.aota_listbox.Location = Point(10, 45)
        self.aota_listbox.Size = Size(400, 280)
        self.aota_listbox.SelectionMode = SelectionMode.One
        self.aota_listbox.DoubleClick += self.ok_button_click
        aota_group.Controls.Add(self.aota_listbox)
        
        # Tangra CSV files group (right side)
        csv_group = GroupBox()
        csv_group.Text = "Tangra Light Curve Files (.csv)"
        csv_group.Location = Point(450, 145)
        csv_group.Size = Size(420, 340)
        self.Controls.Add(csv_group)
        
        # CSV count label
        self.csv_count_label = Label()
        self.csv_count_label.Text = "No folder selected"
        self.csv_count_label.Location = Point(10, 20)
        self.csv_count_label.Size = Size(400, 20)
        csv_group.Controls.Add(self.csv_count_label)
        
        # CSV files listbox
        self.csv_listbox = ListBox()
        self.csv_listbox.Location = Point(10, 45)
        self.csv_listbox.Size = Size(400, 280)
        self.csv_listbox.SelectionMode = SelectionMode.One
        self.csv_listbox.DoubleClick += self.ok_button_click
        csv_group.Controls.Add(self.csv_listbox)
        
        # Buttons panel
        button_panel = Panel()
        button_panel.Location = Point(20, 500)
        button_panel.Size = Size(850, 35)
        self.Controls.Add(button_panel)
        
        # Status label
        self.status_label = Label()
        self.status_label.Text = ""
        self.status_label.Location = Point(0, 10)
        self.status_label.Size = Size(600, 20)
        button_panel.Controls.Add(self.status_label)
        
        # OK button
        self.ok_button = Button()
        self.ok_button.Text = "OK"
        self.ok_button.Location = Point(630, 5)
        self.ok_button.Size = Size(100, 30)
        self.ok_button.Enabled = False
        self.ok_button.Click += self.ok_button_click
        button_panel.Controls.Add(self.ok_button)
        self.AcceptButton = self.ok_button
        
        # Cancel button
        cancel_button = Button()
        cancel_button.Text = "Cancel"
        cancel_button.Location = Point(740, 5)
        cancel_button.Size = Size(100, 30)
        cancel_button.Click += self.cancel_button_click
        button_panel.Controls.Add(cancel_button)
        self.CancelButton = cancel_button
    
    def browse_folder_click(self, sender, e):
        """Handle browse folder button click"""
        dialog = FolderBrowserDialog()
        dialog.Description = "Select folder containing AOTA and Tangra CSV files"
        
        # Start in Reports folder if it exists
        reports_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Reports')
        if os.path.exists(reports_folder):
            dialog.SelectedPath = reports_folder
        
        if dialog.ShowDialog() == DialogResult.OK:
            folder_path = dialog.SelectedPath
            self.folder_textbox.Text = folder_path
            self.scan_folder(folder_path)
    
    def scan_folder(self, folder_path):
        """Scan folder for AOTA and CSV files
        
        Args:
            folder_path: Path to folder to scan
        """
        self.aota_files = []
        self.csv_files = []
        self.aota_listbox.Items.Clear()
        self.csv_listbox.Items.Clear()
        
        if not os.path.exists(folder_path):
            self.aota_count_label.Text = "Folder not found"
            self.csv_count_label.Text = "Folder not found"
            return
        
        try:
            # Find all AOTA and CSV files in the folder
            for filename in os.listdir(folder_path):
                full_path = os.path.join(folder_path, filename)
                
                if filename.lower().endswith('.aota.xml'):
                    self.aota_files.append(full_path)
                    self.aota_listbox.Items.Add(filename)
                elif filename.lower().endswith('.csv'):
                    self.csv_files.append(full_path)
                    self.csv_listbox.Items.Add(filename)
            
            # Update count labels
            aota_count = len(self.aota_files)
            csv_count = len(self.csv_files)
            
            if aota_count == 0:
                self.aota_count_label.Text = "No AOTA files found"
            elif aota_count == 1:
                self.aota_count_label.Text = "1 AOTA file found"
                self.aota_listbox.SelectedIndex = 0
            else:
                self.aota_count_label.Text = f"{aota_count} AOTA files found"
            
            if csv_count == 0:
                self.csv_count_label.Text = "No CSV files found"
            elif csv_count == 1:
                self.csv_count_label.Text = "1 CSV file found"
                self.csv_listbox.SelectedIndex = 0
            else:
                self.csv_count_label.Text = f"{csv_count} CSV files found"
            
            # Enable OK button when selections change
            self.aota_listbox.SelectedIndexChanged += self.selection_changed
            self.csv_listbox.SelectedIndexChanged += self.selection_changed
            
            # Update button state
            self.update_button_state()
            
        except Exception as ex:
            MessageBox.Show(
                f"Error scanning folder:\n\n{str(ex)}",
                "Scan Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            self.aota_count_label.Text = "Error scanning folder"
            self.csv_count_label.Text = "Error scanning folder"
    
    def selection_changed(self, sender, e):
        """Handle selection changed in listboxes"""
        self.update_button_state()
    
    def update_button_state(self):
        """Update OK button state and status message"""
        aota_selected = self.aota_listbox.SelectedIndex >= 0
        csv_selected = self.csv_listbox.SelectedIndex >= 0
        
        # For Negative observations, AOTA is optional
        if self.observation_type == "Negative":
            # Only CSV is required
            self.ok_button.Enabled = csv_selected
            if csv_selected and not aota_selected:
                self.status_label.Text = "Ready (AOTA file optional for negative observations)"
            elif csv_selected and aota_selected:
                self.status_label.Text = "Ready"
            else:
                self.status_label.Text = "Please select a Tangra CSV file"
        else:
            # Both AOTA and CSV required for Positive/Unsure
            self.ok_button.Enabled = aota_selected and csv_selected
            if aota_selected and csv_selected:
                self.status_label.Text = "Ready"
            elif not aota_selected and not csv_selected:
                self.status_label.Text = "Please select both AOTA and Tangra CSV files"
            elif not aota_selected:
                self.status_label.Text = "Please select an AOTA file"
            else:
                self.status_label.Text = "Please select a Tangra CSV file"
    
    def ok_button_click(self, sender, e):
        """Handle OK button click"""
        # Get CSV selection (required for all observation types)
        if self.csv_listbox.SelectedIndex >= 0:
            self.selected_tangra_path = self.csv_files[self.csv_listbox.SelectedIndex]
        else:
            MessageBox.Show(
                "Please select a Tangra CSV file.",
                "No CSV File Selected",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            return
        
        # Get AOTA selection (optional for Negative observations)
        if self.aota_listbox.SelectedIndex >= 0:
            self.selected_aota_path = self.aota_files[self.aota_listbox.SelectedIndex]
        elif self.observation_type != "Negative":
            MessageBox.Show(
                "Please select an AOTA file.",
                "No AOTA File Selected",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
            return
        
        print(f"Selected AOTA: {self.selected_aota_path if self.selected_aota_path else 'None'}")
        print(f"Selected Tangra CSV: {self.selected_tangra_path}")
        
        self.DialogResult = DialogResult.OK
        self.Close()
    
    def cancel_button_click(self, sender, e):
        """Handle Cancel button click"""
        self.DialogResult = DialogResult.Cancel
        self.Close()
    
    def get_selected_aota_path(self):
        """Get the selected AOTA file path
        
        Returns:
            Path to selected AOTA file, or None if not selected/cancelled
        """
        return self.selected_aota_path
    
    def get_selected_tangra_path(self):
        """Get the selected Tangra CSV file path
        
        Returns:
            Path to selected CSV file, or None if cancelled
        """
        return self.selected_tangra_path
