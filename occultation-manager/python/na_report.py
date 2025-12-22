"""
North American Occultation Report Form Generator
Based on astrid's fillinnareport.py implementation

Uses simple_xlsx: A minimal pure-Python Excel reader/writer for IronPython
No C extensions, no external dependencies beyond Python stdlib
"""

import os
from datetime import datetime
from simple_xlsx import load_workbook


class NAReportGenerator:
    """Generates North American Occultation Report Forms using the official template"""
    
    # Local template file (now bundled with the project)
    TEMPLATE_FILENAME = 'NorthAmerica_AstReportForm_V5.6.12r.xlsx'
    
    # Month names for report
    MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 
              'July', 'August', 'September', 'October', 'November', 'December']
    
    def __init__(self, config):
        """Initialize with configuration manager"""
        self.config = config
    
    def get_template_path(self):
        """Get path to local template file bundled with the project"""
        # Template is in the same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, self.TEMPLATE_FILENAME)
    
    def check_template_exists(self):
        """Check if template file exists. Returns (success, message)"""
        template_path = self.get_template_path()
        
        if os.path.exists(template_path):
            return True, template_path
        else:
            error_msg = f"Template file not found:\n{template_path}\n\n" + \
                       f"Please ensure {self.TEMPLATE_FILENAME} is in the same folder as na_report.py"
            return False, error_msg
    
    def parse_star_catalog(self, star_name):
        """Parse star name to determine catalog and number"""
        if not star_name:
            return None, None
        
        star = star_name.strip()
        star_catalog = None
        star_number = None
        
        if star.startswith('TYC'):
            star_catalog = 'TYC       xxxx-xxxxx-x'
            star_number = star.replace('TYC ', '')
        elif star.startswith('HIP'):
            star_catalog = 'HIP  xxxxxx'
            star_number = star.replace('HIP ', '')
        elif star.startswith('UCAC2'):
            star_catalog = 'UCAC2        xxxxxxxx'
            star_number = star.replace('UCAC2 ', '')
        elif star.startswith('UCAC3'):
            star_catalog = 'UCAC3     xxx - xxxxxx'
            star_number = star.replace('UCAC3 ', '')
        elif star.startswith('UCAC4'):
            star_catalog = 'UCAC4     xxx - xxxxxx'
            star_number = star.replace('UCAC4 ', '')
        elif star.startswith('G'):
            star_catalog = 'G-coords hhmmss.s?ddmmss'
            star_number = star.replace('G', '')
        elif star.startswith('URAT1'):
            star_catalog = 'URAT1    xxx - xxxxxxx'
            star_number = star.replace('URAT1 ', '')
        elif star.startswith('1B'):
            star_catalog = '1B    xxx - xxxxxxx'
            star_number = star.replace('1B ', '')
        elif star.startswith('1N'):
            star_catalog = '1N    xxx - xxxxxxx'
            star_number = star.replace('1N ', '')
        
        return star_catalog, star_number
    
    def get_cell_mapping(self):
        """Get the cell mapping dict (from astrid's fillinnareport.py)"""
        return {
            'AstNum': 'E7',
            'AstName': 'K7',
            'EventYear': 'D5',
            'EventMonth': 'K5',
            'EventDay': 'P5',
            'StarCatalog': 'S7',
            'StarNumber': 'X7',
            'PredictedHours': 'Y5',
            'PredictedMinutes': 'AA5',
            'PredictedSeconds': 'AC5',
            'LatitudeFormat': 'E17',
            'LongitudeFormat': 'N17',
            'Latitude': 'E18',
            'LatitudeDir': 'J18',
            'Longitude': 'N18',
            'LongitudeDir': 'R18',
            'Elevation': 'V18',
            'ElevationUnits': 'W18',
            'ElevationDatum': 'AA18',
            'Timing': 'E22',
            'TimingDevice': 'E23',
            'Detector': 'E25',
            'OtherDetectorRelatedInfo': 'V25',
            'ObserverName': 'D9',
            'ObserverEmail': 'S9',
            'Aperture': 'E20',
            'ApertureUnits': 'H20',
            'FocalRatio': 'L20',
            'TelescopeType': 'T20',
            'StartedObservingHours': 'F31',
            'StartedObservingMins': 'H31',
            'StartedObservingSecs': 'J31',
            'StoppedObservingHours': 'F37',
            'StoppedObservingMins': 'H37',
            'StoppedObservingSecs': 'J37',
            'VideoFormat': 'L25',
            'ExposureIntegration': 'P25',
            'CommentLine3': 'D44',
        }
    
    def generate_report(self, event):
        """
        Generate a North American Occultation Report Form for a single event.
        Returns report_path on success, None on error (with error printed)
        """
        # Create debug log
        debug_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'report_debug.log')
        
        def log(msg):
            print(msg)
            try:
                with open(debug_log, 'a') as f:
                    f.write(msg + '\n')
            except:
                pass
        
        try:
            log(f"\n{'='*60}")
            log(f"Starting report generation at {datetime.now()}")
            log(f"Event: {event.get_asteroid_display_name() if hasattr(event, 'get_asteroid_display_name') else 'Unknown'}")
            
            # Determine report folder
            report_folder = os.path.join(self.config.get_file_folder(), 'Reports')
            log(f"Report folder: {report_folder}")
            
            # Check template exists
            log("Checking template exists...")
            success, template_path_or_error = self.check_template_exists()
            if not success:
                log(f"ERROR: {template_path_or_error}")
                return None
            
            template_path = template_path_or_error
            log(f"Template found: {template_path}")
            
            # Load template
            log("Loading template workbook...")
            wb = load_workbook(template_path)
            log("Workbook loaded successfully")
            
            log("Accessing DATA worksheet...")
            ws = wb['DATA']
            log("Worksheet accessed successfully")
            
            # Validate template
            log("Validating template...")
            cell_g1 = ws['G1'].value
            log(f"Cell G1 value: {cell_g1}")
            if cell_g1 != 'Asteroid Occultation Report Form':
                log(f"ERROR: Invalid template file. Expected 'Asteroid Occultation Report Form' at cell G1, got '{cell_g1}'")
                return None
            
            # Get cell mapping
            log("Getting cell mapping...")
            cell_mapping = self.get_cell_mapping()
            
            # Fill in event data
            log("Filling event data...")
            self._fill_event_data(ws, cell_mapping, event)
            log("Filling observer data...")
            self._fill_observer_data(ws, cell_mapping)
            log("Filling telescope data...")
            self._fill_telescope_data(ws, cell_mapping)
            log("Filling recording times...")
            self._fill_recording_times(ws, cell_mapping, event)
            log("Filling metadata...")
            self._fill_metadata(ws, cell_mapping, event)
            
            # Generate filename (IOTA standard format)
            log("Generating filename...")
            filename = self._generate_filename(event)
            report_path = os.path.join(report_folder, filename)
            log(f"Report will be saved to: {report_path}")
            
            # Ensure report folder exists
            if not os.path.exists(report_folder):
                log(f"Creating report folder: {report_folder}")
                os.makedirs(report_folder)
            
            # Save report
            log("Saving report...")
            wb.save(report_path)
            log(f"SUCCESS: Report generated: {report_path}")
            return report_path
            
        except Exception as ex:
            import traceback
            log(f"ERROR generating report: {str(ex)}")
            log(f"Exception type: {type(ex).__name__}")
            log("Full traceback:")
            for line in traceback.format_exc().split('\n'):
                log(line)
            return None
    
    def _fill_event_data(self, ws, cell_mapping, event):
        """Fill in event-specific data"""
        # Asteroid number and name
        if hasattr(event, 'object_no') and event.object_no:
            ws[cell_mapping['AstNum']] = event.object_no
        if hasattr(event, 'object_name') and event.object_name:
            ws[cell_mapping['AstName']] = event.object_name
        
        # Event date/time
        if hasattr(event, 'event_datetime') and event.event_datetime:
            dt = event.event_datetime
            ws[cell_mapping['EventYear']] = dt.year
            ws[cell_mapping['EventMonth']] = self.MONTHS[dt.month - 1]
            ws[cell_mapping['EventDay']] = dt.day
            ws[cell_mapping['PredictedHours']] = dt.hour
            ws[cell_mapping['PredictedMinutes']] = dt.minute
            ws[cell_mapping['PredictedSeconds']] = dt.second
        
        # Star catalog and number
        star_name = getattr(event, 'star_name', None) or getattr(event, 'star_id', None)
        if star_name:
            star_catalog, star_number = self.parse_star_catalog(star_name)
            if star_catalog and star_number:
                ws[cell_mapping['StarCatalog']] = star_catalog
                ws[cell_mapping['StarNumber']] = star_number
    
    def _fill_observer_data(self, ws, cell_mapping):
        """Fill in observer information from config"""
        # Location
        observer_lat = self.config.get_observer_latitude()
        observer_lon = self.config.get_observer_longitude()
        observer_elev = self.config.get_observer_elevation()
        
        if observer_lat != 0.0:
            ws[cell_mapping['LatitudeFormat']] = 'deg.ddddd'
            ws[cell_mapping['Latitude']] = '%0.5f' % abs(observer_lat)
            ws[cell_mapping['LatitudeDir']] = 'S' if observer_lat < 0 else 'N'
        
        if observer_lon != 0.0:
            ws[cell_mapping['LongitudeFormat']] = 'deg.ddddd'
            ws[cell_mapping['Longitude']] = '%0.5f' % abs(observer_lon)
            ws[cell_mapping['LongitudeDir']] = 'W' if observer_lon < 0 else 'E'
        
        if observer_elev != 0.0:
            ws[cell_mapping['Elevation']] = observer_elev
            ws[cell_mapping['ElevationUnits']] = 'm'
            ws[cell_mapping['ElevationDatum']] = 'WGS84'
        
        # Observer name and email
        observer_name = self.config.get_observer_name()
        observer_email = self.config.get_observer_email()
        if observer_name:
            ws[cell_mapping['ObserverName']] = observer_name
        if observer_email:
            ws[cell_mapping['ObserverEmail']] = observer_email
    
    def _fill_telescope_data(self, ws, cell_mapping):
        """Fill in telescope information from config"""
        aperture = self.config.get_telescope_aperture()
        focal_length = self.config.get_telescope_focal_length()
        telescope_type = self.config.get_telescope_type()
        
        if aperture > 0 and focal_length > 0:
            ws[cell_mapping['Aperture']] = aperture / 10.0  # Convert mm to cm
            ws[cell_mapping['ApertureUnits']] = 'cm'
            focal_ratio = focal_length / aperture
            ws[cell_mapping['FocalRatio']] = focal_ratio
        
        if telescope_type:
            ws[cell_mapping['TelescopeType']] = telescope_type
    
    def _fill_recording_times(self, ws, cell_mapping, event):
        """Fill in recording start/stop times"""
        if hasattr(event, 'start_time') and event.start_time:
            ws[cell_mapping['StartedObservingHours']] = event.start_time.hour
            ws[cell_mapping['StartedObservingMins']] = event.start_time.minute
            ws[cell_mapping['StartedObservingSecs']] = event.start_time.second
        
        if hasattr(event, 'end_time') and event.end_time:
            ws[cell_mapping['StoppedObservingHours']] = event.end_time.hour
            ws[cell_mapping['StoppedObservingMins']] = event.end_time.minute
            ws[cell_mapping['StoppedObservingSecs']] = event.end_time.second
    
    def _fill_metadata(self, ws, cell_mapping, event):
        """Fill in metadata fields"""
        # Timing source
        ws[cell_mapping['Timing']] = 'GPS - other linking'
        ws[cell_mapping['TimingDevice']] = 'SharpCap'
        ws[cell_mapping['Detector']] = 'SharpCap'
        
        # Detector info (include exposure if available)
        detector_info = 'SharpCap'
        if hasattr(event, 'exposure_ms'):
            detector_info += f' Exp {event.exposure_ms}ms'
        ws[cell_mapping['OtherDetectorRelatedInfo']] = detector_info
        
        # Video format
        ws[cell_mapping['VideoFormat']] = 'SER'
        ws[cell_mapping['ExposureIntegration']] = 'Other'
        
        # Comment
        ws[cell_mapping['CommentLine3']] = 'This report was pre-filled by Occultation Manager'
    
    def _generate_filename(self, event):
        """Generate IOTA-standard filename"""
        # Get date
        if hasattr(event, 'event_datetime') and event.event_datetime:
            event_date = event.event_datetime.strftime('%Y%m%d')
        else:
            event_date = 'unknown'
        
        # Get asteroid number and name (no parentheses)
        object_no = getattr(event, 'object_no', '')
        object_name = getattr(event, 'object_name', '').replace(' ', '_')
        
        # Get star designation and convert to filename format
        star_name = getattr(event, 'star_name', '') or getattr(event, 'star_id', '')
        if star_name:
            # Extract catalog prefix and number
            star_clean = star_name.strip()
            if ' ' in star_clean:
                catalog = star_clean.split(' ')[0]
                number = star_clean.split(' ', 1)[1]
            else:
                catalog = star_clean
                number = ''
            
            # Convert all separators in star number to underscores
            if number:
                number = number.replace('-', '_').replace(' ', '_')
            
            star_part = f"{catalog}_{number}" if number else f"{catalog}"
        else:
            star_part = ''
        
        # Get observer surname from config
        observer_name = self.config.get_observer_name()
        if observer_name:
            # Get surname (last part)
            name_parts = observer_name.split()
            surname = name_parts[-1] if name_parts else observer_name
            surname = surname.replace(' ', '_')
        else:
            surname = 'Observer'
        
        # Get station name from event and remove surname if it's duplicated
        station = getattr(event, 'station_name', '')
        if station:
            station = station.replace(' ', '_')
            # Remove surname from station name if it appears at the start
            if surname and station.startswith(surname + '_'):
                station = station[len(surname) + 1:]  # Remove surname and underscore
            elif surname and station == surname:
                station = 'Home'  # If station is just the surname, use Home
        else:
            station = 'Home'
        
        # Determine result indicator (+ for positive, - for negative/unsure)
        # For now, default to '-' (unsure/to be determined)
        result_indicator = '-'
        
        # IOTA format: YYYYMMDD_asteroidnumber_asteroidname_starcatalog_starnumber-surname_station.xlsx
        filename = f"{event_date}_{object_no}_{star_part}{result_indicator}{surname}_{station}.xlsx"
        
        return filename
