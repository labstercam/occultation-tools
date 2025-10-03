# test_templates_quick.py - Quick templates validation test

import os
import sys
import tempfile
import shutil

def quick_test():
    """Quick templates test"""
    print("Quick Templates Test")
    print("=" * 25)
    
    try:
        # Mock config
        class MockConfig:
            def __init__(self):
                self.temp_dir = tempfile.mkdtemp()
            def get_file_folder(self):
                return self.temp_dir
            def get_full_file_path(self, filename):
                return os.path.join(self.temp_dir, filename)
        
        # Import and test
        from templates import TemplateManager
        print("✓ TemplateManager module imports")
        
        config = MockConfig()
        tm = TemplateManager(config)
        print("✓ TemplateManager creates successfully")
        
        # Create test template
        template_content = """# Test Template
GOTO {ra} {dec}
EXPOSE {exposure}
RECORD {recording_duration}
"""
        template_path = os.path.join(config.temp_dir, 'test_template.txt')
        with open(template_path, 'w') as f:
            f.write(template_content)
        
        print("✓ Test template created")
        
        # Test finding templates
        templates, folder = TemplateManager.find_template_files(config.temp_dir)
        assert len(templates) == 1, f"Expected 1 template, found {len(templates)}"
        assert templates[0] == 'test_template.txt', f"Wrong template name: {templates[0]}"
        print("✓ Template finding works")
        
        # Test loading template
        content = TemplateManager.load_template(template_path, config)
        assert content is not None, "Template content is None"
        assert '{ra}' in content, "Template variables not found"
        print("✓ Template loading works")
        
        # Test template info
        size, mtime = TemplateManager.get_template_info(template_path)
        assert size > 0, f"Template size is {size}"
        print("✓ Template info works")
        
        # Cleanup
        shutil.rmtree(config.temp_dir)
        
        print("✓ Quick test passed!")
        return True
        
    except Exception as e:
        print(f"❌ Quick test failed: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)