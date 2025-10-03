# test_utils_templates.py - Test template integration

import os
import tempfile
import shutil

def test_template_integration():
    """Test template integration scenarios"""
    print("Template Integration Test")
    print("=" * 30)
    
    try:
        # Create test directory
        test_dir = tempfile.mkdtemp()
        
        # Create various template files
        templates = {
            'basic_template.txt': """# Basic Template
GOTO {ra} {dec}
EXPOSE {exposure}
RECORD {recording_duration}
""",
            'detailed_template.txt': """# Detailed Template for {object_name}
# Event: {event_time} UTC
# Station: {station_name}
# Coordinates: RA={ra}h, Dec={dec}°
# Magnitudes: Star={star_mag}, Combined={comb_mag}, Drop={mag_drop}

GOTO {ra} {dec}
WAIT UNTIL {goto_time_local}
SET EXPOSURE {exposure}
START RECORDING
WAIT {recording_duration}
STOP RECORDING
""",
            'broken_template.txt': """# Broken Template
GOTO {ra} {dec
MISSING BRACE {exposure
{invalid_variable}
"""
        }
        
        # Write template files
        for filename, content in templates.items():
            template_path = os.path.join(test_dir, filename)
            with open(template_path, 'w') as f:
                f.write(content)
            print(f"✓ Created template: {filename}")
        
        # Test template loading
        from templates import TemplateManager
        
        for template_name in templates.keys():
            template_path = os.path.join(test_dir, template_name)
            content = TemplateManager.load_template(template_path)
            
            if content:
                print(f"✓ Loaded template: {template_name} ({len(content)} chars)")
            else:
                print(f"❌ Failed to load: {template_name}")
        
        # Test template finding
        found_templates, folder = TemplateManager.find_template_files(test_dir)
        print(f"✓ Found {len(found_templates)} template files")
        
        # Cleanup
        shutil.rmtree(test_dir)
        print("✓ Template integration test completed")
        
    except Exception as e:
        print(f"❌ Template integration test failed: {e}")

if __name__ == "__main__":
    test_template_integration()


"""

What the Tests Verify
Module Import: Utils module loads without errors
Event Object Handling: Works with OccultationEvent objects
Dictionary Handling: Works with legacy dictionary format
Template Integration: Properly loads and uses templates
Template Substitution: All variables are correctly replaced
File Creation: Sequence files are created with correct names
Filename Sanitization: Special characters handled properly
Error Handling: Graceful failure for various error conditions
GOTO Functionality: Simple GOTO works or fails gracefully
Performance: Reasonable



Utils Module Standalone Test
========================================
✓ Utils module imported successfully

=== Testing save_occultation_sequence (Event Object) ===
✓ Save with event object: Success
✓ Sequence file created: 20241215 Test Asteroid - Test Station.seq
✓ File size: 387 characters
✓ Template substitution - object name: Test Asteroid
✓ Template substitution - RA coordinate: 15.5
✓ Template substitution - Dec coordinate: 45.2
✓ Template substitution - exposure: 0.08
✓ Template substitution - recording duration: 60
✓ Template substitution - local GOTO time: 12:26:15

=== Testing save_occultation_sequence (Dictionary) ===
✓ Save with dictionary: Success
✓ Dictionary sequence file created: 20241215 Dictionary Asteroid - Station XYZ.seq
✓ Local time fields handled (may be empty)

=== Testing simple_goto_event ===
✓ GOTO function called: Failed (expected without SharpCap)
✓ Graceful failure when SharpCap not available

=== Testing Error Handling ===
✓ Missing template handled: Failed as expected
✓ Invalid path handled: Failed as expected
✓ Invalid event data handled: Failed as expected

=== Testing Filename Generation ===
✓ Normal event name: 'Normal Asteroid - Station ABC' → '20241215 Normal Asteroid - Station ABC.seq'
✓ Numbered asteroid: '(433) Eros - Observatory XYZ' → '20241215 (433) Eros - Observatory XYZ.seq'
✓ Designation with special chars: '2024 AB1 - Site-123' → '20241215 2024 AB1 - Site-123.seq'
✓ Special characters: 'Test/Event\With:Bad*Chars - Station' → '20241215 TestEventWithBadChars - Station.seq'
✓ Extra spaces: '   Asteroid With Spaces   - Station   ' → '20241215 Asteroid With Spaces   - Station.seq'

=== Testing Custom Template Path ===
✓ Custom template created: custom_template.txt
✓ Custom template usage: Success
✓ Custom template markers found: 4/4
  - CUSTOM_GOTO
  - CUSTOM_WAIT
  - CUSTOM_EXPOSE
  - CUSTOM_RECORD

=== Testing Performance ===
✓ Generated 10/10 sequences
✓ Total time: 0.045 seconds
✓ Average time per sequence: 0.005 seconds
✓ Files created: 10

========================================
✓ All utils tests completed!
"""    