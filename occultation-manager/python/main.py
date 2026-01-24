# Sharpcap Occultation Manager
# #SharpCap_Scripts/
# └── occultation_manager/
#     ├── config.py
#     ├── theme.py
#     ├── events.py
#     ├── templates.py
#     ├── gui_dialogs.py
#     ├── gui_components.py
#     ├── sequence_runner.py
#     ├── main_gui.py
#     ├── utils.py
#     └── main.py

# Main entry point for the Occultation Manager
import os
import sys

# Add the module directory to Python path
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

import clr
clr.AddReference("System.Windows.Forms")
from System.Windows.Forms import *

clr.AddReference("System.Drawing")
import System.Drawing
from System.Drawing import Image

# Import our modules
from config import ConfigManager
from theme import ThemeManager
from main_gui import OccultationManagerGUI
from SharpCap.Interfaces import PlateSolvePurpose   
from  SharpCap.Base import CoordinateParser, RADecPosition, Epoch



################################
# Various Global Setup
#################################
# Check Version of SharpCap
SharpCapVersion = SharpCap.AppName.Split("v")[1].Split(",")[0]
# Prepare Icon Path for custom button
Occultation_script_path  = os.path.dirname(__file__)
default_icon = Occultation_script_path + "\moon_icon_178489.ico"






############################

# Global variable to track if form is already open
_app_instance = None

def main():
    """Main entry point"""
    global _app_instance
    
    # Single instance check - prevent multiple windows
    if _app_instance is not None:
        try:
            # Try to bring existing window to front
            if not _app_instance.IsDisposed:
                _app_instance.Activate()
                _app_instance.BringToFront()
                MessageBox.Show(
                    "Occultation Manager is already running.\n\nThe existing window has been brought to the front.",
                    "Already Running",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information
                )
                return
            else:
                # Form was disposed, allow creating new one
                _app_instance = None
        except:
            # Form no longer valid, allow creating new one
            _app_instance = None
    
    # Create global instances
    config = ConfigManager()
    theme_manager = ThemeManager()

    if (SharpCapVersion.CompareTo("4.1.13") <= 0):
        MessageBox.Show("SharpCap Version too old - use 4.1.13 or later", "Version Error", MessageBoxButtons.OK, MessageBoxIcon.Error)
        return

    print(f"Configuration loaded from: {config.get_config_path()}")
    print(f"Working directory: {config.get_file_folder()}")


    # Validate configuration
    errors = config.validate_config()
    if errors:
        print("Configuration validation errors:")
        for error in errors:
            print(f"  - {error}")
        print("Please check your configuration settings.")


    try:
        print("Starting Enhanced GUI mode...")
        app = OccultationManagerGUI(config, theme_manager,SharpCap,PlateSolvePurpose,CoordinateParser)
        _app_instance = app  # Store the instance globally
        Application.EnableVisualStyles()
        app.Show()  # Use Show() instead of ShowDialog() to keep SharpCap interface responsive
    except Exception as ex:
        print(f"GUI failed to start: {ex}")
        MessageBox.Show(f"Failed to start application: {ex}", "Startup Error", 
                       MessageBoxButtons.OK, MessageBoxIcon.Error)

# Add custom button to SharpCap UI
SharpCap.AddCustomButton(" Occultations ", Image.FromFile(default_icon), "Occultation Manager", main)
#if __name__ == "__main__":
    # main()