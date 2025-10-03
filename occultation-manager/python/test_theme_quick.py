# test_theme_quick.py - Quick theme validation test

import os
import sys

def quick_test():
    """Quick theme test"""
    print("Quick Theme Test")
    print("=" * 20)
    
    try:
        # Import GUI libraries
        import clr
        clr.AddReference("System.Windows.Forms")
        clr.AddReference("System.Drawing")
        
        from System.Windows.Forms import *
        from System.Drawing import Color
        
        # Import and test theme module
        from theme import ThemeManager, apply_theme_to_control
        print("✓ Theme module imports")
        
        # Create theme manager
        tm = ThemeManager()
        print("✓ ThemeManager created")
        
        # Test initial state
        assert tm.is_night_mode == False, "Should start in day mode"
        print("✓ Initial state correct")
        
        # Test themes exist
        day_theme = tm.day_theme
        night_theme = tm.night_theme
        assert len(day_theme) > 0, "Day theme should have colors"
        assert len(night_theme) > 0, "Night theme should have colors"
        print("✓ Themes defined")
        
        # Test toggle
        result = tm.toggle_night_mode()
        assert result == True, "Should be in night mode after toggle"
        assert tm.is_night_mode == True, "Night mode flag should be set"
        print("✓ Toggle works")
        
        # Test current theme
        current = tm.get_current_theme()
        assert current == night_theme, "Should return night theme"
        print("✓ Current theme correct")
        
        # Test set method
        tm.set_night_mode(False)
        assert tm.is_night_mode == False, "Should be day mode"
        print("✓ Set method works")
        
        # Test theme application
        test_form = Form()
        test_form.Size = Size(100, 100)
        
        apply_theme_to_control(test_form, day_theme)
        print("✓ Theme application works")
        
        test_form.Dispose()
        
        print("✓ Quick test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)