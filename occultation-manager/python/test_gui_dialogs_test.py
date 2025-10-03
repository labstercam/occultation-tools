# test_gui_dialogs_quick.py - Quick GUI dialogs validation test

import os
import sys
import tempfile
import shutil

def quick_test():
    """Quick GUI dialogs test"""
    print("Quick GUI Dialogs Test")
    print("=" * 25)
    
    try:
        # Import GUI libraries
        import clr
        clr.AddReference("System.Windows.Forms")
        clr.AddReference("System.Drawing")
        
        from System.Windows.Forms import *
        from System.Drawing import *
        
        # Mock dependencies
        class MockTheme:
            def get_current_theme(self):
                return {'background': SystemColors.Control, 'text_foreground': SystemColors.ControlText}
        
        class MockConfig:
            def __init__(self):
                self.temp_dir = tempfile.mkdtemp()
            def get_owc_email(self):
                return "test@example.com"
            def get_file_folder(self):
                return self.temp_dir
            def validate_config(self):
                return []
            def save_config(self):
                return True
            def cleanup(self):
                if os.path.exists(self.temp_dir):
                    shutil.rmtree(self.temp_dir)
        
        class MockEvent:
            def __init__(self):
                self.event_name = "Test Event"
                self.star_name = "Test Star"
                self.star_mag = 11.5
                self.exposure_ms = 80
                self.custom_exposure = None
                self.object_name = "Test Asteroid"
            def has_custom_exposure(self):
                return self.custom_exposure is not None
            def set_custom_exposure(self, ms):
                self.custom_exposure = ms / 1000.0
            def get_asteroid_display_name(self):
                return self.object_name
            def _calculate_derived_values(self):
                pass
        
        # Mock theme application
        def mock_apply_theme(control, theme):
            pass
        
        sys.modules['theme'] = type('MockModule', (), {
            'apply_theme_to_control': mock_apply_theme
        })()
        
        # Mock templates
        class MockTemplateManager:
            @staticmethod
            def find_template_files(folder):
                return ['test_template.txt'], folder
            @staticmethod
            def get_template_info(path):
                from datetime import datetime
                return 100, datetime.now()
            @staticmethod
            def load_template(path, config=None):
                return "# Test template"
        
        sys.modules['templates'] = type('MockModule', (), {
            'TemplateManager': MockTemplateManager
        })()
        
        # Import and test dialogs
        from gui_dialogs import ExposureEditDialog, EventDetailsDialog, ConfigurationDialog, TemplateSelectionDialog
        print("✓ GUI Dialogs module imports")
        
        theme_manager = MockTheme()
        config = MockConfig()
        event = MockEvent()
        
        # Test ExposureEditDialog
        exposure_dialog = ExposureEditDialog(event, theme_manager)
        assert exposure_dialog.new_exposure_ms == 80, "Initial exposure should be 80"
        exposure_dialog.Dispose()
        print("✓ ExposureEditDialog creates")
        
        # Test EventDetailsDialog
        details_dialog = EventDetailsDialog(event, theme_manager)
        assert "Test Event" in details_dialog.Text, "Dialog title should contain event name"
        details_dialog.Dispose()
        print("✓ EventDetailsDialog creates")
        
        # Test ConfigurationDialog
        config_dialog = ConfigurationDialog(config, theme_manager)
        assert "Configuration" in config_dialog.Text, "Dialog should be configuration dialog"
        config_dialog.Dispose()
        print("✓ ConfigurationDialog creates")
        
        # Test TemplateSelectionDialog
        template_dialog = TemplateSelectionDialog(config, theme_manager)
        assert "Template" in template_dialog.Text, "Dialog should be template dialog"
        template_dialog.Dispose()
        print("✓ TemplateSelectionDialog creates")
        
        # Cleanup
        config.cleanup()
        
        print("✓ Quick test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)