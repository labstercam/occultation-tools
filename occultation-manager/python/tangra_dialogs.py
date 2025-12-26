"""
Tangra CSV File Selection Dialog
Shows folder browsing and CSV file selection with preview
"""

import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")
clr.AddReference("System")

import os
import System
from System.Drawing import Point, Size, Color, Font, FontStyle
from System.Windows.Forms import (
    Form, Button, Label, ListBox, Panel, TextBox,
    AnchorStyles, DockStyle, Padding, DialogResult,
    FormStartPosition, MessageBox, MessageBoxButtons, MessageBoxIcon,
    FolderBrowserDialog, SelectionMode
)
from theme import apply_theme_to_control


class TangraCSVSelectionDialog(Form):
    """Dialog for selecting a Tangra CSV file from a folder"""
    
    def __init__(self, theme_manager, asteroid_name=""):
        """Initialize the dialog
        
        Args:
            theme_manager: Theme manager for consistent styling
            asteroid_name: Name of the asteroid for display
        """
        Form.__init__(self)
        self.theme_manager = theme_manager
        self.asteroid_name = asteroid_name
        self.selected_file_path = None
        self.csv_files = []
        
        self.setup_ui()
        
        # Apply theme using the correct method
        theme_colors = self.theme_manager.get_current_theme()
        apply_theme_to_control(self, theme_colors)
    
    def setup_ui(self):
        """Setup user interface"""
        self.Text = "Select Tangra Light Curve CSV"
        self.Size = Size(650, 450)
        self.StartPosition = FormStartPosition.CenterParent
        self.FormBorderStyle = System.Windows.Forms.FormBorderStyle.FixedDialog
        self.MaximizeBox = False
        self.MinimizeBox = False
        
        # Header label
        header = Label()
        header.Text = "Select Tangra Light Curve CSV File"
        if self.asteroid_name:
            header.Text += f" for {self.asteroid_name}"
        header.Font = Font(header.Font.FontFamily, 10, FontStyle.Bold)
        header.Location = Point(20, 20)
        header.Size = Size(600, 25)
        self.Controls.Add(header)
        
        # Instructions label
        instructions = Label()
        instructions.Text = "1. Select folder containing AOTA, Tangra CSV, and other observation files\n" + \
                           "2. Choose the Tangra CSV file from the list below"
        instructions.Location = Point(20, 55)
        instructions.Size = Size(600, 40)
        self.Controls.Add(instructions)
        
        # Folder selection panel
        folder_panel = Panel()
        folder_panel.Location = Point(20, 105)
        folder_panel.Size = Size(600, 30)
        self.Controls.Add(folder_panel)
        
        # Folder path textbox
        self.folder_textbox = TextBox()
        self.folder_textbox.Location = Point(0, 0)
        self.folder_textbox.Size = Size(470, 25)
        self.folder_textbox.ReadOnly = True
        folder_panel.Controls.Add(self.folder_textbox)
        
        # Browse button
        browse_button = Button()
        browse_button.Text = "Browse Folder..."
        browse_button.Location = Point(480, 0)
        browse_button.Size = Size(120, 25)
        browse_button.Click += self.browse_folder_click
        folder_panel.Controls.Add(browse_button)
        
        # CSV files label
        csv_label = Label()
        csv_label.Text = "Tangra CSV Files Found:"
        csv_label.Location = Point(20, 145)
        csv_label.Size = Size(400, 20)
        self.Controls.Add(csv_label)
        
        # CSV files count label
        self.count_label = Label()
        self.count_label.Text = "No folder selected"
        self.count_label.Location = Point(420, 145)
        self.count_label.Size = Size(200, 20)
        self.count_label.TextAlign = System.Drawing.ContentAlignment.MiddleRight
        self.Controls.Add(self.count_label)
        
        # CSV files listbox
        self.csv_listbox = ListBox()
        self.csv_listbox.Location = Point(20, 170)
        self.csv_listbox.Size = Size(600, 180)
        self.csv_listbox.SelectionMode = SelectionMode.One
        self.csv_listbox.DoubleClick += self.ok_button_click
        self.Controls.Add(self.csv_listbox)
        
        # Buttons panel
        button_panel = Panel()
        button_panel.Location = Point(20, 365)
        button_panel.Size = Size(600, 35)
        self.Controls.Add(button_panel)
        
        # OK button
        self.ok_button = Button()
        self.ok_button.Text = "OK"
        self.ok_button.Location = Point(380, 5)
        self.ok_button.Size = Size(100, 30)
        self.ok_button.Enabled = False
        self.ok_button.Click += self.ok_button_click
        button_panel.Controls.Add(self.ok_button)
        self.AcceptButton = self.ok_button
        
        # Cancel button
        cancel_button = Button()
        cancel_button.Text = "Cancel"
        cancel_button.Location = Point(490, 5)
        cancel_button.Size = Size(100, 30)
        cancel_button.Click += self.cancel_button_click
        button_panel.Controls.Add(cancel_button)
        self.CancelButton = cancel_button
    
    def browse_folder_click(self, sender, e):
        """Handle browse folder button click"""
        dialog = FolderBrowserDialog()
        dialog.Description = "Select folder containing Tangra CSV and AOTA files"
        
        # Start in Reports folder if it exists
        reports_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Reports')
        if os.path.exists(reports_folder):
            dialog.SelectedPath = reports_folder
        
        if dialog.ShowDialog() == DialogResult.OK:
            folder_path = dialog.SelectedPath
            self.folder_textbox.Text = folder_path
            self.scan_folder_for_csv(folder_path)
    
    def scan_folder_for_csv(self, folder_path):
        """Scan folder for CSV files
        
        Args:
            folder_path: Path to folder to scan
        """
        self.csv_files = []
        self.csv_listbox.Items.Clear()
        
        if not os.path.exists(folder_path):
            self.count_label.Text = "Folder not found"
            return
        
        try:
            # Find all CSV files in the folder
            for filename in os.listdir(folder_path):
                if filename.lower().endswith('.csv'):
                    full_path = os.path.join(folder_path, filename)
                    self.csv_files.append(full_path)
                    self.csv_listbox.Items.Add(filename)
            
            # Update count label
            count = len(self.csv_files)
            if count == 0:
                self.count_label.Text = "No CSV files found"
                self.ok_button.Enabled = False
            elif count == 1:
                self.count_label.Text = "1 CSV file found"
                # Auto-select if only one file
                self.csv_listbox.SelectedIndex = 0
                self.ok_button.Enabled = True
            else:
                self.count_label.Text = f"{count} CSV files found"
                self.ok_button.Enabled = False
            
            # Enable OK button when selection changes
            self.csv_listbox.SelectedIndexChanged += self.selection_changed
            
        except Exception as ex:
            MessageBox.Show(
                f"Error scanning folder:\n\n{str(ex)}",
                "Scan Error",
                MessageBoxButtons.OK,
                MessageBoxIcon.Error
            )
            self.count_label.Text = "Error scanning folder"
    
    def selection_changed(self, sender, e):
        """Handle selection changed in listbox"""
        self.ok_button.Enabled = self.csv_listbox.SelectedIndex >= 0
    
    def ok_button_click(self, sender, e):
        """Handle OK button click"""
        if self.csv_listbox.SelectedIndex >= 0:
            self.selected_file_path = self.csv_files[self.csv_listbox.SelectedIndex]
            print(f"Selected Tangra CSV: {self.selected_file_path}")
            self.DialogResult = DialogResult.OK
            self.Close()
        else:
            MessageBox.Show(
                "Please select a Tangra CSV file from the list.",
                "No File Selected",
                MessageBoxButtons.OK,
                MessageBoxIcon.Information
            )
    
    def cancel_button_click(self, sender, e):
        """Handle Cancel button click"""
        self.DialogResult = DialogResult.Cancel
        self.Close()
    
    def get_selected_file_path(self):
        """Get the selected file path
        
        Returns:
            Path to selected CSV file, or None if cancelled
        """
        return self.selected_file_path
    
    def get_selected_folder_path(self):
        """Get the selected folder path
        
        Returns:
            Path to selected folder, or None if not selected
        """
        return self.folder_textbox.Text if self.folder_textbox.Text else None
