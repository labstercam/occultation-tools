# test_main_gui_quick.py - Quick main GUI validation test

import os
import sys
import tempfile

def quick_test():
    """Quick main GUI test"""
    print("Quick Main GUI Test")
    print("=" * 20)
    
    try:
        # Import GUI libraries
        import clr
        clr.AddReference("System.Windows.Forms")
        clr.AddReference("System.Drawing")
        
        from System.Windows.Forms import *
        
        # Quick mocks
        class MockConfig:
            def __init__(self):
                self.temp_dir = tempfile.mkdtemp()
            def get_sequence_path(self):
                return self.temp_dir
            def get_night_mode(self):
                return False
            def set_night_mode(self, mode):
                pass
            def save_config(self):
                return True
        
        class MockTheme:
            def get_current_theme(self):
                return {'background': SystemColors.Control}
            def toggle_night_mode(self):
                return False
        
        class MockManager:
            def __init__(self, config):
                self.all_events = []
                self.selected_events = set()
            def load_events_from_files(self):
                return True
            def get_filtered_events(self):
                return []
            def get_all_stations(self):
                return []
        
        class MockGrid:
            def __init__(self):
                self.SelectionChanged = None
            def update_events(self, events):
                pass
        
        class MockRunner:
            def __init__(self, config):
                self.running = False
        
        # Setup mocks
        def mock_apply_theme(control, theme):
            pass
        
        sys.modules['theme'] = type('MockModule', (), {
            'apply_theme_to_control': mock_apply_theme
        })()
        
        sys.modules['events'] = type('MockModule', (), {
            'OccultationManager': MockManager
        })()
        
        sys.modules['sequence_runner'] = type('MockModule', (), {
            'SequenceRunner': MockRunner
        })()
        
        sys.modules['gui_components'] = type('MockModule', (), {
            'EventsDataGrid': MockGrid
        })()
        
        # Mock other modules with minimal functionality
        mock_dialog = type('MockDialog', (), {
            '__init__': lambda self, *args: None,
            'ShowDialog': lambda self: DialogResult.OK,
            'Dispose': lambda self: None
        })
        
        sys.modules['gui_dialogs'] = type('MockModule', (), {
            'ExposureEditDialog': mock_dialog,
            'EventDetailsDialog': mock_dialog,
            'ConfigurationDialog': mock_dialog,
            'TemplateSelectionDialog': mock_dialog
        })()
        
        sys.modules['templates'] = type('MockModule', (), {
            'TemplateManager': type('MockTM', (), {'__init__': lambda self, config: None})
        })()
        
        sys.modules['utils'] = type('MockModule', (), {
            'save_occultation_sequence': lambda *args: True,
            'simple_goto_event': lambda event: True
        })()
        
        # Import and test
        from main_gui import OccultationManagerGUI
        print("✓ Main GUI module imports")
        
        config = MockConfig()
        theme_manager = MockTheme()
        
        # Test creation
        gui = OccultationManagerGUI(config, theme_manager)
        print("✓ Main GUI created successfully")
        
        # Test basic properties
        assert "Occultation Manager" in gui.Text, "Title should contain 'Occultation Manager'"
        assert gui.Size.Width > 1000, "Window should be wide enough"
        assert gui.Size.Height > 600, "Window should be tall enough"
        print("✓ Basic properties correct")
        
        # Test that key components exist
        components = ['manager', 'sequence_runner', 'events_grid']
        for component in components:
            if hasattr(gui, component):
                print(f"✓ {component} exists")
            else:
                print(f"❌ {component} missing")
        
        # Test simple method
        gui.update_status("Quick test")
        print("✓ Basic method works")
        
        gui.Dispose()
        
        import shutil
        shutil.rmtree(config.temp_dir)
        
        print("✓ Quick test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)