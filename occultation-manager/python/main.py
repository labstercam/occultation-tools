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








############################

def main():
    """Main entry point"""
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
        Application.EnableVisualStyles()
        #Application.Run(app)
        app.ShowDialog()  # Changed from Application.Run(app) so shouldn't lock the main SharpCap interface.
    except Exception as ex:
        print(f"GUI failed to start: {ex}")
        MessageBox.Show(f"Failed to start application: {ex}", "Startup Error", 
                       MessageBoxButtons.OK, MessageBoxIcon.Error)

if __name__ == "__main__":
    main()