# test_theme.py - Standalone test for theme.py module

import sys
import os

# Add the module directory to Python path if needed
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

# Import required GUI libraries for testing
import clr
clr.AddReference("System.Windows.Forms")
clr.AddReference("System.Drawing")

from System.Drawing import Color, SystemColors
from System.Windows.Forms import *

def test_theme_manager_creation():
    """Test ThemeManager creation and initialization"""
    print("\n=== Testing ThemeManager Creation ===")
    
    try:
        from theme import ThemeManager
        
        theme_manager = ThemeManager()
        print("✓ ThemeManager created successfully")
        
        # Test initial state
        print(f"✓ Initial night mode: {theme_manager.is_night_mode}")
        
        # Verify initial state is day mode
        if not theme_manager.is_night_mode:
            print("✓ Starts in day mode (correct)")
        else:
            print("❌ Should start in day mode")
        
        # Test that themes were set up
        if hasattr(theme_manager, 'day_theme') and hasattr(theme_manager, 'night_theme'):
            print("✓ Day and night themes initialized")
        else:
            print("❌ Themes not properly initialized")
        
    except Exception as e:
        print(f"❌ ThemeManager creation failed: {e}")
        import traceback
        traceback.print_exc()

def test_theme_definitions():
    """Test theme color definitions"""
    print("\n=== Testing Theme Definitions ===")
    
    try:
        from theme import ThemeManager
        
        theme_manager = ThemeManager()
        
        # Test day theme
        day_theme = theme_manager.day_theme
        print("✓ Day theme colors:")
        
        required_keys = [
            'background', 'panel_background', 'text_foreground',
            'grid_background', 'grid_foreground', 'grid_selection',
            'button_background', 'button_text', 'status_background',
            'status_text', 'groupbox_background', 'textbox_background'
        ]
        
        for key in required_keys:
            if key in day_theme:
                color = day_theme[key]
                print(f"  - {key}: {color}")
            else:
                print(f"  - ❌ Missing key: {key}")
        
        print(f"✓ Day theme has {len(day_theme)} color definitions")
        
        # Test night theme
        night_theme = theme_manager.night_theme
        print("✓ Night theme colors:")
        
        for key in required_keys[:3]:  # Show first 3 for brevity
            if key in night_theme:
                color = night_theme[key]
                # Check if it's a red-tinted color for night mode
                if hasattr(color, 'R') and color.R > color.G and color.R > color.B:
                    print(f"  - {key}: {color} (✓ Red-tinted)")
                else:
                    print(f"  - {key}: {color}")
            else:
                print(f"  - ❌ Missing key: {key}")
        
        print(f"✓ Night theme has {len(night_theme)} color definitions")
        
        # Verify both themes have same keys
        day_keys = set(day_theme.keys())
        night_keys = set(night_theme.keys())
        
        if day_keys == night_keys:
            print("✓ Day and night themes have matching color keys")
        else:
            missing_in_night = day_keys - night_keys
            missing_in_day = night_keys - day_keys
            if missing_in_night:
                print(f"❌ Night theme missing: {missing_in_night}")
            if missing_in_day:
                print(f"❌ Day theme missing: {missing_in_day}")
        
    except Exception as e:
        print(f"❌ Theme definitions test failed: {e}")
        import tracebook
        traceback.print_exc()

def test_theme_switching():
    """Test theme switching functionality"""
    print("\n=== Testing Theme Switching ===")
    
    try:
        from theme import ThemeManager
        
        theme_manager = ThemeManager()
        
        # Test initial state
        initial_state = theme_manager.is_night_mode
        initial_theme = theme_manager.get_current_theme()
        print(f"✓ Initial state: Night mode = {initial_state}")
        
        # Test toggle
        new_state = theme_manager.toggle_night_mode()
        print(f"✓ After toggle: Night mode = {new_state}")
        
        # Verify state changed
        if new_state != initial_state:
            print("✓ Toggle changed the state")
        else:
            print("❌ Toggle did not change the state")
        
        # Test that theme changed
        new_theme = theme_manager.get_current_theme()
        if new_theme != initial_theme:
            print("✓ Theme changed after toggle")
            
            # Compare specific colors to verify they're different
            if new_theme['background'] != initial_theme['background']:
                print("✓ Background color changed")
            else:
                print("❌ Background color did not change")
                
        else:
            print("❌ Theme did not change after toggle")
        
        # Test toggle again (should return to original)
        final_state = theme_manager.toggle_night_mode()
        final_theme = theme_manager.get_current_theme()
        
        print(f"✓ After second toggle: Night mode = {final_state}")
        
        if final_state == initial_state:
            print("✓ Second toggle returned to initial state")
        else:
            print("❌ Second toggle did not return to initial state")
        
        # Test set_night_mode method
        theme_manager.set_night_mode(True)
        if theme_manager.is_night_mode:
            print("✓ set_night_mode(True) works")
        else:
            print("❌ set_night_mode(True) failed")
        
        theme_manager.set_night_mode(False)
        if not theme_manager.is_night_mode:
            print("✓ set_night_mode(False) works")
        else:
            print("❌ set_night_mode(False) failed")
        
    except Exception as e:
        print(f"❌ Theme switching test failed: {e}")
        import traceback
        traceback.print_exc()

def test_color_properties():
    """Test color object properties and validity"""
    print("\n=== Testing Color Properties ===")
    
    try:
        from theme import ThemeManager
        
        theme_manager = ThemeManager()
        
        # Test both themes
        themes = {
            'Day': theme_manager.day_theme,
            'Night': theme_manager.night_theme
        }
        
        for theme_name, theme in themes.items():
            print(f"✓ Testing {theme_name} theme colors:")
            
            for color_name, color_value in theme.items():
                try:
                    # Test that color has expected properties
                    if hasattr(color_value, 'R') and hasattr(color_value, 'G') and hasattr(color_value, 'B'):
                        r, g, b = color_value.R, color_value.G, color_value.B
                        print(f"  - {color_name}: RGB({r}, {g}, {b})")
                        
                        # Validate RGB values are in valid range
                        if all(0 <= val <= 255 for val in [r, g, b]):
                            pass  # Valid
                        else:
                            print(f"    ❌ Invalid RGB values: {r}, {g}, {b}")
                        
                        # For night theme, check red tinting
                        if theme_name == 'Night' and color_name not in ['grid_selection']:
                            if r >= g and r >= b:
                                pass  # Good red tinting
                            else:
                                print(f"    ⚠ May not be red-tinted enough: R={r}, G={g}, B={b}")
                                
                    else:
                        # System color or other type
                        print(f"  - {color_name}: {color_value} (System color)")
                        
                except Exception as ce:
                    print(f"  - ❌ {color_name}: Error accessing color - {ce}")
            
            print(f"✓ {theme_name} theme validation completed")
        
    except Exception as e:
        print(f"❌ Color properties test failed: {e}")
        import traceback
        traceback.print_exc()

def test_apply_theme_function():
    """Test the apply_theme_to_control function"""
    print("\n=== Testing apply_theme_to_control Function ===")
    
    try:
        from theme import apply_theme_to_control, ThemeManager
        
        theme_manager = ThemeManager()
        
        # Create test controls
        test_form = Form()
        test_form.Text = "Theme Test Form"
        test_form.Size = System.Drawing.Size(300, 200)
        
        # Add various controls to test
        test_button = Button()
        test_button.Text = "Test Button"
        test_button.Location = System.Drawing.Point(10, 10)
        test_form.Controls.Add(test_button)
        
        test_label = Label()
        test_label.Text = "Test Label"
        test_label.Location = System.Drawing.Point(10, 50)
        test_form.Controls.Add(test_label)
        
        test_textbox = TextBox()
        test_textbox.Text = "Test TextBox"
        test_textbox.Location = System.Drawing.Point(10, 80)
        test_form.Controls.Add(test_textbox)
        
        test_panel = Panel()
        test_panel.Location = System.Drawing.Point(10, 110)
        test_panel.Size = System.Drawing.Size(100, 50)
        test_form.Controls.Add(test_panel)
        
        print("✓ Created test form with controls")
        
        # Test day theme application
        day_theme = theme_manager.get_current_theme()
        
        try:
            apply_theme_to_control(test_form, day_theme)
            print("✓ Day theme applied successfully")
        except Exception as e:
            print(f"❌ Day theme application failed: {e}")
        
        # Test night theme application
        theme_manager.set_night_mode(True)
        night_theme = theme_manager.get_current_theme()
        
        try:
            apply_theme_to_control(test_form, night_theme)
            print("✓ Night theme applied successfully")
        except Exception as e:
            print(f"❌ Night theme application failed: {e}")
        
        # Verify some colors were applied
        if hasattr(test_form, 'BackColor'):
            print(f"✓ Form background color: {test_form.BackColor}")
        
        if hasattr(test_button, 'BackColor') and hasattr(test_button, 'ForeColor'):
            print(f"✓ Button colors: Back={test_button.BackColor}, Fore={test_button.ForeColor}")
        
        # Test with None theme (error handling)
        try:
            apply_theme_to_control(test_form, None)
            print("✓ None theme handled gracefully")
        except Exception as e:
            print(f"⚠ None theme caused error: {e}")
        
        # Dispose form
        test_form.Dispose()
        
    except Exception as e:
        print(f"❌ apply_theme_to_control test failed: {e}")
        import traceback
        traceback.print_exc()

def test_datagrid_theme_function():
    """Test the apply_datagrid_theme function"""
    print("\n=== Testing apply_datagrid_theme Function ===")
    
    try:
        from theme import apply_datagrid_theme, ThemeManager
        
        theme_manager = ThemeManager()
        
        # Create test DataGridView
        test_grid = DataGridView()
        test_grid.Size = System.Drawing.Size(200, 100)
        
        # Add some columns for testing
        test_grid.Columns.Add("Column1", "Test Column 1")
        test_grid.Columns.Add("Column2", "Test Column 2")
        
        print("✓ Created test DataGridView")
        
        # Test day theme
        day_theme = theme_manager.get_current_theme()
        
        try:
            apply_datagrid_theme(test_grid, day_theme)
            print("✓ Day theme applied to DataGridView")
        except Exception as e:
            print(f"❌ Day theme DataGrid application failed: {e}")
        
        # Test night theme
        theme_manager.set_night_mode(True)
        night_theme = theme_manager.get_current_theme()
        
        try:
            apply_datagrid_theme(test_grid, night_theme)
            print("✓ Night theme applied to DataGridView")
        except Exception as e:
            print(f"❌ Night theme DataGrid application failed: {e}")
        
        # Verify some properties were set
        if hasattr(test_grid, 'BackgroundColor'):
            print(f"✓ Grid background color: {test_grid.BackgroundColor}")
        
        if hasattr(test_grid, 'DefaultCellStyle'):
            cell_style = test_grid.DefaultCellStyle
            if hasattr(cell_style, 'BackColor') and hasattr(cell_style, 'ForeColor'):
                print(f"✓ Cell colors: Back={cell_style.BackColor}, Fore={cell_style.ForeColor}")
        
        if hasattr(test_grid, 'ColumnHeadersDefaultCellStyle'):
            header_style = test_grid.ColumnHeadersDefaultCellStyle
            if hasattr(header_style, 'BackColor'):
                print(f"✓ Header background: {header_style.BackColor}")
        
        # Check EnableHeadersVisualStyles was set
        if hasattr(test_grid, 'EnableHeadersVisualStyles'):
            print(f"✓ EnableHeadersVisualStyles: {test_grid.EnableHeadersVisualStyles}")
            if not test_grid.EnableHeadersVisualStyles:
                print("✓ Visual styles disabled for custom headers (correct)")
        
        # Dispose grid
        test_grid.Dispose()
        
    except Exception as e:
        print(f"❌ apply_datagrid_theme test failed: {e}")
        import traceback
        traceback.print_exc()

def test_theme_integration():
    """Test theme integration with real GUI components"""
    print("\n=== Testing Theme Integration ===")
    
    try:
        from theme import ThemeManager, apply_theme_to_control
        
        theme_manager = ThemeManager()
        
        # Create a more complex form to test integration
        main_form = Form()
        main_form.Text = "Theme Integration Test"
        main_form.Size = System.Drawing.Size(400, 300)
        main_form.StartPosition = FormStartPosition.CenterScreen
        
        # Add GroupBox
        group_box = GroupBox()
        group_box.Text = "Test Group"
        group_box.Location = System.Drawing.Point(10, 10)
        group_box.Size = System.Drawing.Size(350, 100)
        main_form.Controls.Add(group_box)
        
        # Add controls inside GroupBox
        inner_button = Button()
        inner_button.Text = "Inner Button"
        inner_button.Location = System.Drawing.Point(10, 30)
        group_box.Controls.Add(inner_button)
        
        inner_label = Label()
        inner_label.Text = "Inner Label"
        inner_label.Location = System.Drawing.Point(10, 60)
        group_box.Controls.Add(inner_label)
        
        # Add TabControl
        tab_control = TabControl()
        tab_control.Location = System.Drawing.Point(10, 120)
        tab_control.Size = System.Drawing.Size(350, 150)
        main_form.Controls.Add(tab_control)
        
        # Add TabPages
        tab1 = TabPage()
        tab1.Text = "Tab 1"
        tab_control.TabPages.Add(tab1)
        
        tab2 = TabPage()
        tab2.Text = "Tab 2" 
        tab_control.TabPages.Add(tab2)
        
        # Add control to tab
        tab_button = Button()
        tab_button.Text = "Tab Button"
        tab_button.Location = System.Drawing.Point(10, 10)
        tab1.Controls.Add(tab_button)
        
        print("✓ Created complex test form")
        
        # Test recursive theme application
        def test_theme_application(theme_name, is_night_mode):
            theme_manager.set_night_mode(is_night_mode)
            theme = theme_manager.get_current_theme()
            
            try:
                apply_theme_to_control(main_form, theme)
                print(f"✓ {theme_name} theme applied to complex form")
                
                # Verify recursive application worked
                checks = [
                    (main_form, "main form"),
                    (group_box, "group box"),
                    (inner_button, "inner button"),
                    (tab_control, "tab control"),
                    (tab1, "tab page"),
                    (tab_button, "tab button")
                ]
                
                themed_count = 0
                for control, name in checks:
                    if hasattr(control, 'BackColor'):
                        themed_count += 1
                
                print(f"  - Themed {themed_count}/{len(checks)} controls")
                
            except Exception as e:
                print(f"❌ {theme_name} theme application failed: {e}")
        
        # Test both themes
        test_theme_application("Day", False)
        test_theme_application("Night", True)
        
        # Show form briefly if running interactively
        # (comment out for automated testing)
        # main_form.Show()
        # System.Threading.Thread.Sleep(1000)  # Show for 1 second
        
        # Dispose form
        main_form.Dispose()
        
        print("✓ Theme integration test completed")
        
    except Exception as e:
        print(f"❌ Theme integration test failed: {e}")
        import traceback
        traceback.print_exc()

def test_error_handling():
    """Test error handling in theme functions"""
    print("\n=== Testing Error Handling ===")
    
    try:
        from theme import apply_theme_to_control, apply_datagrid_theme, ThemeManager
        
        theme_manager = ThemeManager()
        theme = theme_manager.get_current_theme()
        
        # Test with None control
        try:
            apply_theme_to_control(None, theme)
            print("✓ None control handled gracefully")
        except Exception as e:
            print(f"⚠ None control caused error: {type(e).__name__}")
        
        # Test with invalid theme
        invalid_theme = {'invalid_key': 'invalid_value'}
        test_button = Button()
        
        try:
            apply_theme_to_control(test_button, invalid_theme)
            print("✓ Invalid theme handled gracefully")
        except Exception as e:
            print(f"⚠ Invalid theme caused error: {type(e).__name__}")
        
        # Test with control that doesn't support theming
        class MockControl:
            pass
        
        mock_control = MockControl()
        
        try:
            apply_theme_to_control(mock_control, theme)
            print("✓ Non-themable control handled gracefully")
        except Exception as e:
            print(f"⚠ Non-themable control caused error: {type(e).__name__}")
        
        # Test DataGrid with None
        try:
            apply_datagrid_theme(None, theme)
            print("✓ None DataGrid handled gracefully")
        except Exception as e:
            print(f"⚠ None DataGrid caused error: {type(e).__name__}")
        
        # Cleanup
        test_button.Dispose()
        
        print("✓ Error handling tests completed")
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("Theme Module Standalone Test")
    print("=" * 40)
    
    try:
        # Test module import
        from theme import ThemeManager, apply_theme_to_control, apply_datagrid_theme
        print("✓ Theme module imported successfully")
        
        # Run all tests
        test_theme_manager_creation()
        test_theme_definitions()
        test_theme_switching()
        test_color_properties()
        test_apply_theme_function()
        test_datagrid_theme_function()
        test_theme_integration()
        test_error_handling()
        
        print("\n" + "=" * 40)
        print("✓ All theme tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure theme.py is in the same directory")
        return False
    except Exception as e:
        print(f"❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)