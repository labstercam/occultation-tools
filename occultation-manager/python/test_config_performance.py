# test_config_performance.py - Test config performance

import time
import tempfile
import shutil

def performance_test():
    """Test configuration performance"""
    print("Configuration Performance Test")
    print("=" * 35)
    
    try:
        from config import ConfigManager
        
        temp_dir = tempfile.mkdtemp()
        
        # Test creation time
        start_time = time.time()
        config = ConfigManager(config_folder=temp_dir)
        creation_time = time.time() - start_time
        print(f"✓ Creation time: {creation_time:.3f} seconds")
        
        # Test save performance
        start_time = time.time()
        for i in range(100):
            config.save_config()
        save_time = (time.time() - start_time) / 100
        print(f"✓ Average save time: {save_time:.4f} seconds")
        
        # Test load performance
        start_time = time.time()
        for i in range(100):
            config2 = ConfigManager(config_folder=temp_dir)
        load_time = (time.time() - start_time) / 100
        print(f"✓ Average load time: {load_time:.4f} seconds")
        
        # Test getter/setter performance
        start_time = time.time()
        for i in range(1000):
            config.set_base_duration(60 + i % 10)
            duration = config.get_base_duration()
        getset_time = (time.time() - start_time) / 1000
        print(f"✓ Average get/set time: {getset_time:.6f} seconds")
        
        # Cleanup
        shutil.rmtree(temp_dir)
        print("✓ Performance test completed")
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")

if __name__ == "__main__":
    performance_test()

"""
Configuration Module Standalone Test
==================================================
✓ Config module imported successfully

=== Testing ConfigManager Creation ===
✓ ConfigManager created with default settings
✓ Default owc_user_email: your_owc_email
✓ Default base_duration: 60
✓ Default goto_lead_time: 240
✓ Default mag_for_40ms_exposure: 12.0
✓ Default night_mode: False
✓ File folder: C:\Users\...\Documents\SharpCap
✓ Config path: C:\Users\...\Documents\SharpCap\occultation_config.json

=== Testing Custom Folder Configuration ===
✓ Created test directory: C:\Users\...\Temp\config_test_abc123
✓ ConfigManager created with custom folder
✓ Custom folder set correctly: C:\Users\...\Temp\config_test_abc123
✓ Test directory cleaned up

=== Testing Save/Load Operations ===
✓ Initial save: Success
✓ Config file created: C:\Users\...\Temp\config_save_test_def456\occultation_config.json
✓ Config file contains 12 settings
✓ Modified save: Success
✓ Email setting loaded correctly
✓ Base duration loaded correctly
✓ Night mode loaded correctly
✓ Test directory cleaned up

... (additional test sections)

==================================================
✓ All configuration tests completed!
"""    