# test_templates.py - Standalone test for templates.py module

import sys
import os
import tempfile
import shutil
from datetime import datetime

# Add the module directory to Python path if needed
module_dir = os.path.dirname(os.path.abspath(__file__))
if module_dir not in sys.path:
    sys.path.insert(0, module_dir)

# Mock dependencies
class MockConfigManager:
    """Mock config manager for testing templates module"""
    
    def __init__(self, custom_folder=None):
        if custom_folder:
            self.test_folder = custom_folder
        else:
            self.test_folder = tempfile.mkdtemp(prefix='templates_test_')
        
    def get_file_folder(self):
        return self.test_folder
    
    def get_full_file_path(self, filename):
        return os.path.join(self.test_folder, filename)
    
    def cleanup(self):
        if os.path.exists(self.test_folder):
            shutil.rmtree(self.test_folder)

def create_test_template_files(test_folder):
    """Create various test template files"""
    templates = {
        'basic_template.txt': """# Basic Template for {object_name}
GOTO {ra} {dec}
SET EXPOSURE {exposure}
START RECORDING
WAIT {recording_duration}
STOP RECORDING
""",
        
        'detailed_template.txt': """# Detailed Occultation Template
# Event: {object_name} occultation
# Time: {event_time} UTC
# Station: {station_name}
# 
# Target coordinates: RA={ra}h, Dec={dec}°
# Star magnitude: {star_mag}
# Combined magnitude: {comb_mag}
# Expected drop: {mag_drop}
# Time uncertainty: {time_error}s
#
# Sequence begins:

COMMENT "Starting occultation sequence for {object_name}"
GOTO {ra} {dec}
COMMENT "Waiting for GOTO time: {goto_time}"
WAIT UNTIL {goto_time_local}
SET EXPOSURE {exposure}
COMMENT "Starting recording at {start_time_local} local time"
START RECORDING
WAIT {recording_duration}
STOP RECORDING
COMMENT "Sequence completed"
""",
        
        'minimal_template.txt': """GOTO {ra} {dec}
EXPOSE {exposure}
RECORD {recording_duration}
""",
        
        'sharpcap_template.txt': """# SharpCap Sequence Template
# Generated for {object_name}

# GOTO target
GOTO {ra} {dec}
PLATESOLVE
CENTER

# Wait for event time
WAIT UNTIL {goto_time_local}

# Configure camera
SET EXPOSURE {exposure}
SET GAIN AUTO

# Start recording
FILENAME "{object_name}_%timestamp%"
START RECORDING
WAIT {recording_duration}
STOP RECORDING

# Finalize
COMMENT "Sequence completed for {object_name}"
""",
        
        'invalid_template.txt': """# Template with syntax issues
GOTO {ra} {dec
MISSING BRACE {exposure
{invalid_variable}
NORMAL LINE
""",
        
        'empty_template.txt': "",
        
        'comments_only_template.txt': """# This template has only comments
# No actual sequence commands
# Used for testing
""",
        
        'non_template_file.txt': """This is not a template file.
It doesn't contain the word 'template' in the filename properly.
Should not be detected by find_template_files.
""",
        
        'my_custom_sequence_template.txt': """# Custom template
# This should be found because it contains 'template'
CUSTOM_COMMAND {object_name}
""",
        
        'not_a_template.txt': """# This file doesn't have template in name
# Should not be found by find_template_files
SOME_COMMAND
"""
    }
    
    created_files = []
    for filename, content in templates.items():
        file_path = os.path.join(test_folder, filename)
        with open(file_path, 'w') as f:
            f.write(content)
        created_files.append(filename)
    
    return created_files

def test_template_manager_creation():
    """Test TemplateManager creation"""
    print("\n=== Testing TemplateManager Creation ===")
    
    try:
        from templates import TemplateManager
        
        config = MockConfigManager()
        template_manager = TemplateManager(config)
        
        print("✓ TemplateManager created successfully")
        print(f"✓ Config reference stored: {template_manager.config is not None}")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ TemplateManager creation failed: {e}")
        import traceback
        traceback.print_exc()

def test_find_template_files():
    """Test finding template files in folder"""
    print("\n=== Testing find_template_files ===")
    
    try:
        from templates import TemplateManager
        
        config = MockConfigManager()
        
        # Create test template files
        created_files = create_test_template_files(config.get_file_folder())
        print(f"✓ Created {len(created_files)} test files")
        
        # Test finding templates
        template_files, template_folder = TemplateManager.find_template_files(config.get_file_folder())
        
        print(f"✓ Found {len(template_files)} template files")
        print(f"✓ Template folder: {template_folder}")
        
        # Check which files were found (should contain 'template' in name)
        expected_templates = [f for f in created_files if 'template' in f.lower()]
        print(f"✓ Expected {len(expected_templates)} template files")
        
        print("✓ Found template files:")
        for template_file in sorted(template_files):
            print(f"  - {template_file}")
        
        print("✓ Expected template files:")
        for expected_file in sorted(expected_templates):
            print(f"  - {expected_file}")
        
        # Verify correct files were found
        found_set = set(template_files)
        expected_set = set(expected_templates)
        
        if found_set == expected_set:
            print("✓ Template file detection works correctly")
        else:
            missing = expected_set - found_set
            extra = found_set - expected_set
            if missing:
                print(f"❌ Missing templates: {missing}")
            if extra:
                print(f"❌ Extra templates: {extra}")
        
        # Test with non-existent folder
        empty_files, empty_folder = TemplateManager.find_template_files("/nonexistent/path")
        print(f"✓ Non-existent folder handled: {len(empty_files)} files found")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ find_template_files test failed: {e}")
        import traceback
        traceback.print_exc()

def test_get_template_info():
    """Test getting template file information"""
    print("\n=== Testing get_template_info ===")
    
    try:
        from templates import TemplateManager
        
        config = MockConfigManager()
        created_files = create_test_template_files(config.get_file_folder())
        
        # Test getting info for existing files
        for filename in created_files[:3]:  # Test first 3 files
            file_path = os.path.join(config.get_file_folder(), filename)
            size, mtime = TemplateManager.get_template_info(file_path)
            
            print(f"✓ {filename}:")
            print(f"  - Size: {size} bytes")
            print(f"  - Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # Verify size is reasonable
            if size > 0:
                print(f"  - ✓ File has content")
            else:
                print(f"  - ⚠ File is empty (may be expected)")
            
            # Verify modification time is recent
            time_diff = datetime.now() - mtime
            if time_diff.total_seconds() < 60:  # Modified within last minute
                print(f"  - ✓ Recent modification time")
            else:
                print(f"  - ⚠ Old modification time: {time_diff}")
        
        # Test with non-existent file
        size, mtime = TemplateManager.get_template_info("/nonexistent/file.txt")
        print(f"✓ Non-existent file handled: size={size}, mtime={mtime}")
        
        if size == 0 and mtime == datetime.min:
            print("✓ Non-existent file returns expected defaults")
        else:
            print("❌ Non-existent file handling incorrect")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ get_template_info test failed: {e}")
        import traceback
        traceback.print_exc()

def test_load_template():
    """Test loading template content"""
    print("\n=== Testing load_template ===")
    
    try:
        from templates import TemplateManager
        
        config = MockConfigManager()
        created_files = create_test_template_files(config.get_file_folder())
        
        # Test loading existing templates
        test_templates = ['basic_template.txt', 'detailed_template.txt', 'minimal_template.txt']
        
        for template_name in test_templates:
            template_path = os.path.join(config.get_file_folder(), template_name)
            content = TemplateManager.load_template(template_path, config)
            
            if content:
                print(f"✓ Loaded {template_name}: {len(content)} characters")
                
                # Check for template variables
                variables = ['{object_name}', '{ra}', '{dec}', '{exposure}']
                found_vars = [var for var in variables if var in content]
                print(f"  - Template variables found: {len(found_vars)}/{len(variables)}")
                
                # Show first few lines
                lines = content.split('\n')[:3]
                for i, line in enumerate(lines):
                    if line.strip():
                        print(f"  - Line {i+1}: {line.strip()[:50]}...")
                        break
            else:
                print(f"❌ Failed to load {template_name}")
        
        # Test loading non-existent file
        content = TemplateManager.load_template("/nonexistent/template.txt", config)
        print(f"✓ Non-existent file handled: {'Content loaded' if content else 'None returned'}")
        
        # Test loading with None path
        content = TemplateManager.load_template(None, config)
        print(f"✓ None path handled: {'Content loaded' if content else 'None returned'}")
        
        # Test loading empty file
        empty_path = os.path.join(config.get_file_folder(), 'empty_template.txt')
        content = TemplateManager.load_template(empty_path, config)
        print(f"✓ Empty file handled: {len(content) if content else 0} characters")
        
        # Test default template fallback
        default_template_path = config.get_full_file_path('SharpCap Owcloud template.txt')
        with open(default_template_path, 'w') as f:
            f.write("# Default SharpCap Template\nGOTO {ra} {dec}\n")
        
        content = TemplateManager.load_template("", config)  # Empty path should try default
        if content and "Default SharpCap Template" in content:
            print("✓ Default template fallback works")
        else:
            print("⚠ Default template fallback may not be working")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ load_template test failed: {e}")
        import traceback
        traceback.print_exc()

def test_template_content_validation():
    """Test template content validation and variable detection"""
    print("\n=== Testing Template Content Validation ===")
    
    try:
        from templates import TemplateManager
        
        config = MockConfigManager()
        create_test_template_files(config.get_file_folder())
        
        # Define expected template variables
        standard_variables = [
            '{object_name}', '{event_time}', '{start_time}', '{goto_time}',
            '{recording_duration}', '{star_mag}', '{comb_mag}', '{mag_drop}',
            '{time_error}', '{ra}', '{dec}', '{asteroid_name}', '{exposure}',
            '{event_time_local}', '{start_time_local}', '{goto_time_local}',
            '{station_name}'
        ]
        
        # Test each template file
        template_files, _ = TemplateManager.find_template_files(config.get_file_folder())
        
        for template_file in template_files:
            template_path = os.path.join(config.get_file_folder(), template_file)
            content = TemplateManager.load_template(template_path, config)
            
            if content:
                print(f"\n✓ Analyzing {template_file}:")
                
                # Count variables
                found_variables = []
                for var in standard_variables:
                    if var in content:
                        found_variables.append(var)
                
                print(f"  - Standard variables used: {len(found_variables)}/{len(standard_variables)}")
                
                # Show found variables
                if found_variables:
                    print(f"  - Variables: {', '.join(found_variables[:5])}" + 
                          (f" + {len(found_variables)-5} more" if len(found_variables) > 5 else ""))
                
                # Check for potential issues
                issues = []
                
                # Check for unmatched braces
                open_braces = content.count('{')
                close_braces = content.count('}')
                if open_braces != close_braces:
                    issues.append(f"Unmatched braces: {open_braces} open, {close_braces} close")
                
                # Check for unknown variables
                import re
                all_variables = re.findall(r'\{[^}]+\}', content)
                unknown_vars = [var for var in set(all_variables) if var not in standard_variables]
                if unknown_vars:
                    issues.append(f"Unknown variables: {', '.join(unknown_vars[:3])}")
                
                # Check for basic SharpCap commands
                sharpcap_commands = ['GOTO', 'WAIT', 'START', 'STOP', 'SET', 'COMMENT']
                found_commands = [cmd for cmd in sharpcap_commands if cmd in content.upper()]
                if found_commands:
                    print(f"  - SharpCap commands: {', '.join(found_commands[:3])}" + 
                          (f" + {len(found_commands)-3} more" if len(found_commands) > 3 else ""))
                
                # Report issues
                if issues:
                    print(f"  - ⚠ Issues: {'; '.join(issues)}")
                else:
                    print(f"  - ✓ No obvious issues detected")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Template content validation failed: {e}")
        import traceback
        traceback.print_exc()

def test_template_file_sorting():
    """Test template file sorting behavior"""
    print("\n=== Testing Template File Sorting ===")
    
    try:
        from templates import TemplateManager
        
        config = MockConfigManager()
        
        # Create templates with specific names to test sorting
        sorting_templates = {
            'z_last_template.txt': "# Last template alphabetically",
            'a_first_template.txt': "# First template alphabetically", 
            'basic_template.txt': "# Basic template",
            'advanced_template.txt': "# Advanced template",
            'simple_template.txt': "# Simple template"
        }
        
        for filename, content in sorting_templates.items():
            file_path = os.path.join(config.get_file_folder(), filename)
            with open(file_path, 'w') as f:
                f.write(content)
        
        print(f"✓ Created {len(sorting_templates)} templates for sorting test")
        
        # Get template files (should be sorted)
        template_files, _ = TemplateManager.find_template_files(config.get_file_folder())
        
        print("✓ Templates found in order:")
        for i, template_file in enumerate(template_files):
            print(f"  {i+1}. {template_file}")
        
        # Verify sorting
        expected_order = sorted(sorting_templates.keys())
        if template_files == expected_order:
            print("✓ Template files are correctly sorted alphabetically")
        else:
            print("❌ Template file sorting may be incorrect")
            print(f"Expected: {expected_order}")
            print(f"Actual:   {template_files}")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Template file sorting test failed: {e}")
        import traceback
        traceback.print_exc()

def test_template_error_handling():
    """Test template error handling scenarios"""
    print("\n=== Testing Template Error Handling ===")
    
    try:
        from templates import TemplateManager
        
        config = MockConfigManager()
        
        # Test 1: Folder that doesn't exist
        print("✓ Testing non-existent folder:")
        templates, folder = TemplateManager.find_template_files("/this/path/does/not/exist")
        print(f"  - Templates found: {len(templates)}")
        print(f"  - Folder returned: {folder}")
        
        # Test 2: Folder with no permissions (simulate)
        print("✓ Testing folder access:")
        try:
            # Create folder and try to make it inaccessible (Unix-like systems)
            test_folder = tempfile.mkdtemp()
            os.chmod(test_folder, 0o000)  # No permissions
            
            templates, folder = TemplateManager.find_template_files(test_folder)
            print(f"  - No-permission folder handled gracefully: {len(templates)} templates")
            
            # Restore permissions for cleanup
            os.chmod(test_folder, 0o755)
            shutil.rmtree(test_folder)
            
        except (OSError, PermissionError):
            print("  - Permission test skipped (not applicable on this system)")
        
        # Test 3: File that can't be read
        create_test_template_files(config.get_file_folder())
        
        # Try to make a file unreadable
        test_file = os.path.join(config.get_file_folder(), 'basic_template.txt')
        try:
            os.chmod(test_file, 0o000)  # No read permission
            
            content = TemplateManager.load_template(test_file, config)
            print(f"✓ Unreadable file handled: {'Content loaded' if content else 'None returned'}")
            
            # Restore permissions
            os.chmod(test_file, 0o644)
            
        except (OSError, PermissionError):
            print("✓ File permission test skipped (not applicable on this system)")
        
        # Test 4: Corrupted file (binary data)
        corrupted_file = os.path.join(config.get_file_folder(), 'corrupted_template.txt')
        with open(corrupted_file, 'wb') as f:
            f.write(b'\x00\x01\x02\x03\xFF\xFE\xFD')  # Binary data
        
        content = TemplateManager.load_template(corrupted_file, config)
        print(f"✓ Binary file handled: {'Content loaded' if content else 'Error handled gracefully'}")
        
        # Test 5: Very large file
        large_file = os.path.join(config.get_file_folder(), 'large_template.txt')
        with open(large_file, 'w') as f:
            f.write("# Large template\n" + "COMMENT 'Large file test'\n" * 10000)
        
        content = TemplateManager.load_template(large_file, config)
        if content:
            print(f"✓ Large file handled: {len(content)} characters loaded")
        else:
            print("❌ Large file failed to load")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Template error handling test failed: {e}")
        import traceback
        traceback.print_exc()

def test_integration_with_config():
    """Test integration with config manager"""
    print("\n=== Testing Config Integration ===")
    
    try:
        from templates import TemplateManager
        
        # Test with different config scenarios
        
        # Scenario 1: Normal config with standard folder
        config1 = MockConfigManager()
        create_test_template_files(config1.get_file_folder())
        
        tm1 = TemplateManager(config1)
        templates1, folder1 = TemplateManager.find_template_files(config1.get_file_folder())
        
        print(f"✓ Standard config: {len(templates1)} templates in {os.path.basename(folder1)}")
        
        # Scenario 2: Config with custom folder
        custom_folder = tempfile.mkdtemp(prefix='custom_templates_')
        config2 = MockConfigManager(custom_folder)
        
        # Create different templates in custom folder
        custom_templates = {
            'custom_template_1.txt': "# Custom template 1",
            'custom_template_2.txt': "# Custom template 2"
        }
        
        for filename, content in custom_templates.items():
            with open(os.path.join(custom_folder, filename), 'w') as f:
                f.write(content)
        
        tm2 = TemplateManager(config2)
        templates2, folder2 = TemplateManager.find_template_files(config2.get_file_folder())
        
        print(f"✓ Custom config: {len(templates2)} templates in {os.path.basename(folder2)}")
        
        # Test loading with different configs
        if templates1:
            template_path1 = os.path.join(folder1, templates1[0])
            content1 = TemplateManager.load_template(template_path1, config1)
            print(f"✓ Load with config1: {'Success' if content1 else 'Failed'}")
        
        if templates2:
            template_path2 = os.path.join(folder2, templates2[0])
            content2 = TemplateManager.load_template(template_path2, config2)
            print(f"✓ Load with config2: {'Success' if content2 else 'Failed'}")
        
        # Test default template with different configs
        default_path1 = config1.get_full_file_path('SharpCap Owcloud template.txt')
        with open(default_path1, 'w') as f:
            f.write("# Default template for config1")
        
        content_default1 = TemplateManager.load_template("", config1)
        print(f"✓ Default template config1: {'Found' if content_default1 else 'Not found'}")
        
        # Cleanup
        config1.cleanup()
        config2.cleanup()
        shutil.rmtree(custom_folder)
        
    except Exception as e:
        print(f"❌ Config integration test failed: {e}")
        import traceback
        traceback.print_exc()

def test_template_performance():
    """Test template operations performance"""
    print("\n=== Testing Template Performance ===")
    
    try:
        import time
        from templates import TemplateManager
        
        config = MockConfigManager()
        
        # Create many template files
        num_templates = 50
        print(f"✓ Creating {num_templates} template files for performance test...")
        
        for i in range(num_templates):
            template_content = f"""# Performance Test Template {i+1}
# Generated template for performance testing
GOTO {{ra}} {{dec}}
SET EXPOSURE {{exposure}}
COMMENT "Template {i+1} for {{object_name}}"
START RECORDING
WAIT {{recording_duration}}
STOP RECORDING
"""
            filename = f'perf_template_{i+1:02d}.txt'
            filepath = os.path.join(config.get_file_folder(), filename)
            with open(filepath, 'w') as f:
                f.write(template_content)
        
        # Test find_template_files performance
        start_time = time.time()
        templates, folder = TemplateManager.find_template_files(config.get_file_folder())
        find_time = time.time() - start_time
        
        print(f"✓ Find templates: {len(templates)} files in {find_time:.3f}s")
        
        # Test load_template performance
        if templates:
            template_path = os.path.join(folder, templates[0])
            
            # Load same template multiple times
            start_time = time.time()
            for _ in range(100):
                content = TemplateManager.load_template(template_path, config)
            load_time = (time.time() - start_time) / 100
            
            print(f"✓ Load template: average {load_time:.4f}s per load")
        
        # Test get_template_info performance
        if templates:
            start_time = time.time()
            for template in templates[:10]:  # Test first 10
                template_path = os.path.join(folder, template)
                size, mtime = TemplateManager.get_template_info(template_path)
            info_time = (time.time() - start_time) / min(10, len(templates))
            
            print(f"✓ Get template info: average {info_time:.4f}s per file")
        
        # Overall performance summary
        total_files = len(templates)
        if total_files == num_templates:
            print(f"✓ Performance test completed successfully with {total_files} templates")
        else:
            print(f"⚠ Expected {num_templates} templates, found {total_files}")
        
        config.cleanup()
        
    except Exception as e:
        print(f"❌ Template performance test failed: {e}")
        import traceback
        traceback.print_exc()

def main():
    """Main test function"""
    print("Templates Module Standalone Test")
    print("=" * 50)
    
    try:
        # Test module import
        from templates import TemplateManager
        print("✓ TemplateManager module imported successfully")
        
        # Run all tests
        test_template_manager_creation()
        test_find_template_files()
        test_get_template_info()
        test_load_template()
        test_template_content_validation()
        test_template_file_sorting()
        test_template_error_handling()
        test_integration_with_config()
        test_template_performance()
        
        print("\n" + "=" * 50)
        print("✓ All template tests completed!")
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure templates.py is in the same directory")
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