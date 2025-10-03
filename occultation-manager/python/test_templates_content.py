# test_templates_content.py - Test template content handling

import os
import tempfile
import shutil

def test_template_variables():
    """Test template variable handling"""
    print("Template Variables Test")
    print("=" * 25)
    
    try:
        from templates import TemplateManager
        
        # Create test folder
        test_dir = tempfile.mkdtemp()
        
        # Template with all standard variables
        full_template = """# Complete Template for {object_name}
# Event details:
# Time: {event_time} UTC (Local: {event_time_local})
# GOTO: {goto_time} UTC (Local: {goto_time_local}) 
# Start: {start_time} UTC (Local: {start_time_local})
# Duration: {recording_duration} seconds
# Station: {station_name}
#
# Target: {asteroid_name}
# Coordinates: RA={ra}h, Dec={dec}°
# Star magnitude: {star_mag}
# Combined magnitude: {comb_mag}
# Magnitude drop: {mag_drop}
# Time