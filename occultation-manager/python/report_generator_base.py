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
        
        star_name = star_name.upper().strip()

        # Gaia DR3 format: "Gaia DR3 4691443935057297792"
        if star_name.startswith('GAIA DR3') or star_name.startswith('GAIA') or star_name.startswith('J'):
            star_catalog = '1G    Gaia - DR3'
            # Extract star number based on prefix
            if star_name.startswith('GAIA DR3 '):
                star_number = star_name.replace('GAIA DR3 ', '').strip()
            elif star_name.startswith('GAIA '):
                star_number = star_name.replace('GAIA ', '').strip()
            elif star_name.startswith('J'):
                # Handle raw GAIA ID that starts with 'J' (e.g., "J1234567890123456789")
                star_number = star_name.strip()
            else:
                # Fallback - just use the name
                star_number = star_name.strip()
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

        # Hipparcos format: "HIP 80400" (4–6 digit number)
        if star_name.upper().startswith('HIP ') or star_name.upper().startswith('HIP\t'):
            import re as _re
            m = _re.match(r'HIP\s+(\d{4,6})\b', star_name, _re.IGNORECASE)
            if m:
                star_catalog = '1H    Hipparcos'
                star_number = m.group(1)
                return star_catalog, star_number

        # HD format: "HD 12345"
        if star_name.upper().startswith('HD ') or star_name.upper().startswith('HD\t'):
            import re as _re
            m = _re.match(r'HD\s+(\d+)', star_name, _re.IGNORECASE)
            if m:
                star_catalog = '1D    HD'
                star_number = m.group(1)
                return star_catalog, star_number

        # PPM format: "PPM 12345"
        if star_name.upper().startswith('PPM ') or star_name.upper().startswith('PPM\t'):
            import re as _re
            m = _re.match(r'PPM\s+(\d+)', star_name, _re.IGNORECASE)
            if m:
                star_catalog = '1P    PPM'
                star_number = m.group(1)
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

    @staticmethod
    def build_timing_note(timing_data):
        """Return a human-readable summary of timing corrections for report comments.

        Returns an empty string when there is nothing meaningful to record.
        """
        if not timing_data:
            return ''
        method = timing_data.get('timing_method', '')
        if method == 'GPS_dumb':
            return 'GPS timing (reference only); no OM timing correction applied'
        if method != 'NTP':
            return ''
        cam_ms = timing_data.get('camera_delay_ms') or 0.0
        ntp_ms = timing_data.get('ntp_offset_ms') or 0.0
        net_s = timing_data.get('net_correction_s')
        lc_corrected = timing_data.get('lc_timestamps_corrected')
        confirmed = timing_data.get('corrections_confirmed', False)
        cam_applied = timing_data.get('camera_delay_applied')
        ntp_applied = timing_data.get('ntp_applied')
        if lc_corrected is True:
            net_ms = cam_ms + ntp_ms
            note = ('NTP timing corrections applied in Tangra: '
                    'camera acq. delay {0:.1f} ms, NTP offset {1:+.1f} ms (net {2:+.1f} ms)'.format(
                        cam_ms, ntp_ms, net_ms))
            if confirmed:
                note += ' \u2014 confirmed by observer'
            return note
        if cam_applied is None and ntp_applied is True:
            return 'NTP system used; timing corrections not applicable'
        return 'NTP timing: corrections not applied in this session'
