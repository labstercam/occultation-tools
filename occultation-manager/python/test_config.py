# test_config.py - Standalone test for config.py module

import sys
import os
import json
import tempfile
import shutil
from datetime import datetime

# Add the module directory to Python path if needed
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

def test_config_creation():
    """Test ConfigManager creation and defaults"""
    print("\n=== Testing ConfigManager Creation ===")
    
    try:
        from config import ConfigManager
        
        # Test with default folder
        config = ConfigManager()
        print("✓ ConfigManager created with default settings")
        
        # Test default values
        expected_defaults = {
            'owc_user_email': 'your_owc_email',
            'base_duration': 60,
            'goto_lead_time': 240,
            'mag_for_40ms_exposure': 12.0,
            'night_mode': False
        }
        
        for key, expected_value in expected_defaults.items():
            actual_value = getattr(config, f'get_{key}')()
            if actual_value == expected_value:
                print(f"✓ Default {key}: {actual_value}")
            else:
                print(f"❌ Default {key}: Expected {expected_value}, got {actual_value}")
        
        # Test path normalization
        folder = config.get_file_folder()
        print(f"✓ File folder: {folder}")
        print(f"✓ Config path: {config.get_config_path()}")
        
    except Exception as e:
        print(f"❌ ConfigManager creation failed: {e}")
        import traceback
        traceback.print_exc()

def test_config_with_custom_folder():
    """Test ConfigManager with custom folder"""
    print("\n=== Testing Custom Folder Configuration ===")
    
    try:
        from config import ConfigManager
        
        # Create temporary directory for testing
        temp_dir = tempfile.mkdtemp(prefix='config_test_')
        print(f"✓ Created test directory: {temp_dir}")
        
        # Test with custom folder
        config = ConfigManager(config_folder=temp_dir)
        print("✓ ConfigManager created with custom folder")
        
        # Verify paths
        assert config.config_folder == os.path.normpath(temp_dir)
        assert config.get_config_path() == os.path.join(temp_dir, config.CONFIG_FILENAME)
        print(f"✓ Custom folder set correctly: {config.config_folder}")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        print("✓ Test directory cleaned up")
        
    except Exception as e:
        print(f"❌ Custom folder test failed: {e}")
        import traceback
        traceback.print_exc()

def test_config_save_load():
    """Test configuration save and load operations"""
    print("\n=== Testing Save/Load Operations ===")
    
    try:
        from config import ConfigManager
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix='config_save_test_')
        
        # Create config manager
        config = ConfigManager(config_folder=temp_dir)
        
        # Test initial save (defaults)
        success = config.save_config()
        print(f"✓ Initial save: {'Success' if success else 'Failed'}")
        
        # Verify file was created
        config_file = config.get_config_path()
        if os.path.exists(config_file):
            print(f"✓ Config file created: {config_file}")
            
            # Check file contents
            with open(config_file, 'r') as f:
                saved_data = json.load(f)
            print(f"✓ Config file contains {len(saved_data)} settings")
        else:
            print(f"❌ Config file not found: {config_file}")
        
        # Modify some settings
        config.set_owc_email('test@example.com')
        config.set_base_duration(90)
        config.set_night_mode(True)
        
        # Save modified config
        success = config.save_config()
        print(f"✓ Modified save: {'Success' if success else 'Failed'}")
        
        # Create new config manager to test loading
        config2 = ConfigManager(config_folder=temp_dir)
        
        # Verify loaded values
        if config2.get_owc_email() == 'test@example.com':
            print("✓ Email setting loaded correctly")
        else:
            print(f"❌ Email setting: Expected 'test@example.com', got '{config2.get_owc_email()}'")
        
        if config2.get_base_duration() == 90:
            print("✓ Base duration loaded correctly")
        else:
            print(f"❌ Base duration: Expected 90, got {config2.get_base_duration()}")
        
        if config2.get_night_mode() == True:
            print("✓ Night mode loaded correctly")
        else:
            print(f"❌ Night mode: Expected True, got {config2.get_night_mode()}")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        print("✓ Test directory cleaned up")
        
    except Exception as e:
        print(f"❌ Save/Load test failed: {e}")
        import traceback
        traceback.print_exc()

def test_all_getters_setters():
    """Test all getter and setter methods"""
    print("\n=== Testing All Getters/Setters ===")
    
    try:
        from config import ConfigManager
        
        temp_dir = tempfile.mkdtemp(prefix='config_getset_test_')
        config = ConfigManager(config_folder=temp_dir)
        
        # Test cases: (method_base, test_value, expected_type)
        test_cases = [
            ('owc_email', 'test@domain.com', str),
            ('owc_password', 'secret123', str),
            ('file_folder', '/tmp/test', str),
            ('occultations_file', 'test_occ.json', str),
            ('latest_occultations_file', 'test_latest.json', str),
            ('sequence_path', '/tmp/sequences', str),
            ('base_duration', 120, int),
            ('goto_lead_time', 300, int),
            ('mag_for_40ms_exposure', 11.5, float),
            ('host', 'https://test.example.com', str),
            ('api_key', 'test_api_key_123', str),
            ('night_mode', True, bool)
        ]
        
        for method_base, test_value, expected_type in test_cases:
            try:
                # Get setter and getter methods
                setter = getattr(config, f'set_{method_base}')
                getter = getattr(config, f'get_{method_base}')
                
                # Test setter
                setter(test_value)
                
                # Test getter
                retrieved_value = getter()
                
                # Verify type and value
                if isinstance(retrieved_value, expected_type) and retrieved_value == test_value:
                    print(f"✓ {method_base}: {test_value} ({expected_type.__name__})")
                else:
                    print(f"❌ {method_base}: Expected {test_value} ({expected_type.__name__}), got {retrieved_value} ({type(retrieved_value).__name__})")
                    
            except AttributeError as e:
                print(f"❌ {method_base}: Method not found - {e}")
            except Exception as e:
                print(f"❌ {method_base}: Error - {e}")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"❌ Getters/Setters test failed: {e}")
        import traceback
        traceback.print_exc()

def test_url_generation():
    """Test URL generation methods"""
    print("\n=== Testing URL Generation ===")
    
    try:
        from config import ConfigManager
        
        temp_dir = tempfile.mkdtemp(prefix='config_url_test_')
        config = ConfigManager(config_folder=temp_dir)
        
        # Set test API key (hex encoded)
        test_api_key = '746573745f6170695f6b6579'  # 'test_api_key' in hex
        config.set_api_key(test_api_key)
        
        # Test full URL generation
        try:
            full_url = config.get_full_url()
            print(f"✓ Full URL generated: {full_url[:50]}...")
            
            # Check that API key is included
            if 'apikey=' in full_url:
                print("✓ API key parameter included in URL")
            else:
                print("❌ API key parameter missing from URL")
                
        except Exception as e:
            print(f"❌ Full URL generation failed: {e}")
        
        # Test occelmnt URL generation
        try:
            occelmnt_url = config.get_occelmnt_url()
            print(f"✓ Occelmnt URL generated: {occelmnt_url[:50]}...")
            
            # Test with event ID
            test_event_id = '12345'
            formatted_url = occelmnt_url % test_event_id
            print(f"✓ Formatted occelmnt URL: {formatted_url[:50]}...")
            
        except Exception as e:
            print(f"❌ Occelmnt URL generation failed: {e}")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"❌ URL generation test failed: {e}")
        import traceback
        traceback.print_exc()

def test_validation():
    """Test configuration validation"""
    print("\n=== Testing Configuration Validation ===")
    
    try:
        from config import ConfigManager
        
        temp_dir = tempfile.mkdtemp(prefix='config_validation_test_')
        config = ConfigManager(config_folder=temp_dir)
        
        # Test with default (invalid) configuration
        errors = config.validate_config()
        print(f"✓ Default validation found {len(errors)} errors:")
        for error in errors[:3]:  # Show first 3 errors
            print(f"  - {error}")
        if len(errors) > 3:
            print(f"  ... and {len(errors) - 3} more")
        
        # Set valid configuration
        config.set_owc_email('valid@example.com')
        config.set_owc_password('validpassword')
        config.set_base_duration(60)
        config.set_goto_lead_time(240)
        config.set_mag_for_40ms_exposure(12.0)
        
        # Test validation with valid config
        errors = config.validate_config()
        print(f"✓ Valid configuration: {len(errors)} errors")
        if errors:
            for error in errors:
                print(f"  - {error}")
        
        # Test with invalid numeric values
        config.set_base_duration(0)  # Invalid
        config.set_goto_lead_time(-10)  # Invalid
        
        errors = config.validate_config()
        print(f"✓ Invalid numeric validation: {len(errors)} errors")
        for error in errors:
            if 'duration' in error.lower() or 'time' in error.lower():
                print(f"  - {error}")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"❌ Validation test failed: {e}")
        import traceback
        traceback.print_exc()

def test_reset_to_defaults():
    """Test reset to defaults functionality"""
    print("\n=== Testing Reset to Defaults ===")
    
    try:
        from config import ConfigManager
        
        temp_dir = tempfile.mkdtemp(prefix='config_reset_test_')
        config = ConfigManager(config_folder=temp_dir)
        
        # Modify settings
        config.set_owc_email('modified@example.com')
        config.set_base_duration(999)
        config.set_night_mode(True)
        
        print(f"✓ Modified email: {config.get_owc_email()}")
        print(f"✓ Modified duration: {config.get_base_duration()}")
        print(f"✓ Modified night mode: {config.get_night_mode()}")
        
        # Reset to defaults
        success = config.reset_to_defaults()
        print(f"✓ Reset to defaults: {'Success' if success else 'Failed'}")
        
        # Verify reset values
        if config.get_owc_email() == 'your_owc_email':
            print("✓ Email reset to default")
        else:
            print(f"❌ Email not reset: {config.get_owc_email()}")
        
        if config.get_base_duration() == 60:
            print("✓ Duration reset to default")
        else:
            print(f"❌ Duration not reset: {config.get_base_duration()}")
        
        if config.get_night_mode() == False:
            print("✓ Night mode reset to default")
        else:
            print(f"❌ Night mode not reset: {config.get_night_mode()}")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"❌ Reset test failed: {e}")
        import traceback
        traceback.print_exc()

def test_path_operations():
    """Test path-related operations"""
    print("\n=== Testing Path Operations ===")
    
    try:
        from config import ConfigManager
        
        temp_dir = tempfile.mkdtemp(prefix='config_path_test_')
        config = ConfigManager(config_folder=temp_dir)
        
        # Test get_full_file_path
        test_filename = 'test_file.json'
        full_path = config.get_full_file_path(test_filename)
        expected_path = os.path.join(config.get_file_folder(), test_filename)
        
        if full_path == expected_path:
            print(f"✓ Full file path: {full_path}")
        else:
            print(f"❌ Full file path: Expected {expected_path}, got {full_path}")
        
        # Test path normalization
        test_paths = [
            r'C:\Users\Test\Documents',
            '/home/user/documents',
            'relative/path/test',
            r'C:\Users\Test\..\Other\Path'
        ]
        
        for test_path in test_paths:
            config.set_file_folder(test_path)
            normalized = config.get_file_folder()
            print(f"✓ Path '{test_path}' → '{normalized}'")
        
        # Test sequence path defaults
        config.set_file_folder('/test/folder')
        config.config['sequence_path'] = ''  # Reset to empty
        config._normalize_paths()
        
        if config.get_sequence_path() == config.get_file_folder():
            print("✓ Sequence path defaults to file folder when empty")
        else:
            print(f"❌ Sequence path default failed: {config.get_sequence_path()}")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"❌ Path operations test failed: {e}")
        import traceback
        traceback.print_exc()

def test_error_handling():
    """Test error handling scenarios"""
    print("\n=== Testing Error Handling ===")
    
    try:
        from config import ConfigManager
        
        # Test with invalid directory
        invalid_dir = '/this/path/should/not/exist/12345'
        try:
            config = ConfigManager(config_folder=invalid_dir)
            print("✓ Invalid directory handled gracefully")
        except Exception as e:
            print(f"✓ Invalid directory properly rejected: {type(e).__name__}")
        
        # Test save to read-only location (if possible)
        temp_dir = tempfile.mkdtemp(prefix='config_readonly_test_')
        config = ConfigManager(config_folder=temp_dir)
        
        # Try to make directory read-only (Unix-like systems)
        try:
            os.chmod(temp_dir, 0o444)  # Read-only
            success = config.save_config()
            print(f"✓ Read-only directory save: {'Failed as expected' if not success else 'Unexpectedly succeeded'}")
            os.chmod(temp_dir, 0o755)  # Restore permissions
        except (OSError, PermissionError):
            print("✓ Permission test skipped (not applicable on this system)")
        
        # Test loading corrupted config file
        config_file = config.get_config_path()
        try:
            with open(config_file, 'w') as f:
                f.write('invalid json content {')
            
            # Create new config manager to trigger load
            config2 = ConfigManager(config_folder=temp_dir)
            print("✓ Corrupted config file handled gracefully")
            
        except Exception as e:
            print(f"✓ Corrupted file properly handled: {type(e).__name__}")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        
    except Exception as e:
        print(f"❌ Error handling test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("Configuration Module Standalone Test")
    print("=" * 50)
    
    try:
        # Test module import
        from config import ConfigManager
        print("✓ Config module imported successfully")
        
        # Run all tests
        test_config_creation()
        test_config_with_custom_folder()
        test_config_save_load()
        test_all_getters_setters()
        test_url_generation()
        test_validation()
        test_reset_to_defaults()
        test_path_operations()
        test_error_handling()
        
        print("\n" + "=" * 50)
        print("✓ All configuration tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure config.py is in the same directory")
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