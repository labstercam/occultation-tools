"""
Base class for occultation report generators
Provides common functionality shared across different regional report formats
"""

import os
from datetime import datetime


class ReportGeneratorBase:
    """Base class for all report generators"""
    
    # Month names for reports
    MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    
    def __init__(self, config):
        """Initialize with configuration manager"""
        self.config = config
        self._report_telescope_id = None
        self._report_camera_id = None
    
    def get_template_path(self):
        """Get path to template file - must be implemented by subclass"""
        raise NotImplementedError("Subclass must implement get_template_path()")
    
    def check_template_exists(self):
        """Check if template file exists. Returns (success, message)"""
        template_path = self.get_template_path()
        
        if os.path.exists(template_path):
            return True, template_path
        else:
            template_filename = os.path.basename(template_path)
            error_msg = f"Template file not found:\n{template_path}\n\n" + \
                       f"Please ensure {template_filename} is in the python folder"
            return False, error_msg
    
    def parse_star_catalog(self, star_name):
        """Parse star name to determine catalog and number"""
        if not star_name:
            return None, None
        
        # Gaia DR3 format: "Gaia DR3 4691443935057297792"
        if star_name.startswith('Gaia DR3'):
            star_catalog = '1G    Gaia - DR3'
            star_number = star_name.replace('Gaia DR3 ', '')
            return star_catalog, star_number
        
        # UCAC4 format: "UCAC4 123-456789" 
        if star_name.startswith('UCAC4'):
            star_catalog = '1U    UCAC4'
            star_number = star_name.replace('UCAC4 ', '')
            return star_catalog, star_number
        
        # Tycho format: "TYC 1234-5678-1"
        if star_name.startswith('TYC'):
            star_catalog = '1T    Tycho2'
            star_number = star_name.replace('TYC ', '')
            return star_catalog, star_number
        
        # Nomad format: "NOMAD 0123-4567890"
        if star_name.upper().startswith('NOMAD'):
            star_catalog = '1N    NOMAD1'
            star_number = star_name.replace('NOMAD ', '').replace('nomad ', '')
            return star_catalog, star_number
        
        # Default fallback
        star_catalog = '1N    xxx - xxxxxxx'
        star_number = star_name.replace('1N ', '')
        
        return star_catalog, star_number
    
    def generate_report(self, event, telescope_id=None, camera_id=None):
        """Generate a report - must be implemented by subclass"""
        raise NotImplementedError("Subclass must implement generate_report()")
    
    def get_telescope_data(self, telescope_id=None):
        """Get telescope data by ID or active telescope"""
        if telescope_id:
            telescopes = self.config.get_telescopes()
            for t in telescopes:
                if t.get('id') == telescope_id:
                    return t
        return self.config.get_active_telescope()
    
    def get_camera_data(self, camera_id=None):
        """Get camera data by ID or active camera"""
        if camera_id:
            cameras = self.config.get_cameras()
            for c in cameras:
                if c.get('id') == camera_id:
                    return c
        return self.config.get_active_camera()
