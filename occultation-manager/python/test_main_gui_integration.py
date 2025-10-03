# test_main_gui_integration.py - Test integration between main GUI and components

import sys
import os

def integration_test():
    """Test integration between main GUI and its components"""
    print("Main GUI Integration Test")
    print("=" * 30)
    
    try:
        # Import and setup
        import clr
        clr.AddReference("System.Windows.Forms") 
        clr.AddReference("System.Drawing")
        
        from System.Windows.Forms import *
        
        # Create realistic mocks that interact properly
        component_interactions = []
        
        class TrackedConfig:
            def __init__(self):
                import tempfile
                self.temp_dir = tempfile.mkdtemp()
            
            def get_sequence_path(self):
                component_interactions.append("config.get_sequence_path()")
                return self.temp_dir