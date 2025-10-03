# test_config_quick.py - Quick config validation test

import os
import sys
import tempfile
import shutil

def quick_test():
    """Quick configuration test"""
    print("Quick Configuration Test")
    print("=" * 30)
    
    try:
        # Import the module
        from config import ConfigManager
        print("✓ Config module imports")
        
        # Create in temp directory
        temp_dir = tempfile.mkdtemp()
        config = ConfigManager(config_folder=temp_dir)
        print("✓ ConfigManager created")
        
        # Test basic functionality
        config.set_owc_email('test@example.com')
        email = config.get_owc_email()
        assert email == 'test@example.com', f"Email mismatch: {email}"
        print("✓ Email get/set works")
        
        # Test save/load
        success = config.save_config()
        assert success, "Save failed"
        print("✓ Config saves")
        
        # Test validation
        errors = config.validate_config()
        print(f"✓ Validation returns {len(errors)} errors")
        
        # Test URL generation
        config.set_api_key('746573745f6b6579')  # 'test_key' in hex
        url = config.get_full_url()
        assert 'apikey=' in url, "API key missing from URL"
        print("✓ URL generation works")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        print("✓ All quick tests passed!")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except AssertionError as e:
        print(f"❌ Assertion failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = quick_test()
    sys.exit(0 if success else 1)