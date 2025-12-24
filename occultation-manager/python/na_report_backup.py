"""
North American Occultation Report Form Generator (Placeholder-based)
Uses placeholder replacement in XML to avoid namespace issues with Excel

This version replaces placeholders in the template with actual values
"""

import os
import re
import zipfile
from datetime import datetime
from tempfile import NamedTemporaryFile
import shutil
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape
from report_generator_base import ReportGeneratorBase


class NAReportGenerator(ReportGeneratorBase):
    """Generates North American Occultation Report Forms using placeholder replacement"""
    
    # Use the template version with placeholders (no validation)
    TEMPLATE_FILENAME = 'NorthAmerica_AstReportForm_V5.6.12r_Template.xlsx'
    
    def __init__(self, config):
        """Initialize with configuration manager"""
        super(NAReportGenerator, self).__init__(config)
    
    def get_template_path(self):
        """Get path to local template file bundled with the project"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, self.TEMPLATE_FILENAME)
    
    def generate_report(self, event, telescope_id=None, camera_id=None):
        """Generate a North American report using placeholder replacement"""
        # Store equipment IDs
        self._report_telescope_id = telescope_id
        self._report_camera_id = camera_id
        
        try:
            # Get report folder
            report_folder = os.path.join(self.config.get_file_folder(), 'Reports')
            if not os.path.exists(report_folder):
                os.makedirs(report_folder)
            
            # Check template exists
            template_path = self.get_template_path()
            if not os.path.exists(template_path):
                print(f"ERROR: Template not found: {template_path}")
                return None
            
            # Build placeholder replacements
            replacements = self._build_replacements(event)
            
            # Generate output filename
            event_date_str = event.event_datetime.strftime('%Y%m%d') if hasattr(event, 'event_datetime') and event.event_datetime else 'unknown'
            filename = self._generate_filename(event, event_date_str)
            output_path = os.path.join(report_folder, filename)
            
            # Create modified workbook
            self._create_report_with_replacements(template_path, output_path, replacements)
            
            print(f"Report saved to: {output_path}")
            return output_path
            
        except Exception as ex:
            print(f"ERROR: Failed to generate report - {str(ex)}")
            import traceback
            traceback.print_exc()
            return None
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
            'ObservingLocation': 'E15',
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
            'ObserverAddress': 'D11',
            'ObserverCityStateCountry': 'D13',
            'ObserverPhone': 'S11',
            'ObserverFax': 'S13',
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
            'CommentLine1': 'D42',
            'CommentLine2': 'D43',
            'CommentLine3': 'D44',
        }
    
    def generate_report(self, event, telescope_id=None, camera_id=None):
        """
        Generate a North American Occultation Report Form for a single event.
        
        Args:
            event: The event object to generate the report for
            telescope_id: Optional telescope ID to use (if None, uses active telescope)
            camera_id: Optional camera ID to use (if None, uses active camera)
        
        Returns report_path on success, None on error (with error printed)
        """
        # Store equipment IDs for use in fill methods
        self._report_telescope_id = telescope_id
        self._report_camera_id = camera_id
        
        # Create debug log
        debug_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'report_debug.log')
        
        def log(msg):
            print(msg)
            try:
                with open(debug_log, 'a') as f:
                    f.write(msg + '\n')
            except:
                pass
        
        # Log equipment IDs
        log("="*60)
        log("Report generation started")
        log("Telescope ID: {}".format(telescope_id if telescope_id else "None"))
        log("Camera ID: {}".format(camera_id if camera_id else "None"))
        
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
            self._fill_observer_data(ws, cell_mapping, event)
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
            wb.close()  # Release file handle
            log(f"SUCCESS: Report generated: {report_path}")
            return report_path
            
        except PermissionError as ex:
            import traceback
            error_msg = f"Cannot save report - file is open in another program. Please close the file and try again:\n{report_path}"
            log(f"ERROR generating report: {error_msg}")
            log(f"Exception type: {type(ex).__name__}")
            log("Full traceback:")
            for line in traceback.format_exc().split('\n'):
                log(line)
            # Return a tuple (None, error_message) to provide better feedback
            return None
            
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
            # Remove asteroid number from name (e.g., "(46854) 1998 QY42" -> "1998 QY42")
            name = event.object_name
            # Remove number in parentheses at the start
            name = re.sub(r'^\(\d+\)\s*', '', name)
            ws[cell_mapping['AstName']] = name
        
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
    
    def _fill_observer_data(self, ws, cell_mapping, event):
        """Fill in observer information from event station data"""
        # Observing location (City, State/Country)
        obs_location = getattr(event, 'obs_location', '')
        if obs_location:
            ws[cell_mapping['ObservingLocation']] = obs_location
        
        # Use latitude/longitude from the event (station location)
        station_lat = getattr(event, 'latitude', 0.0)
        station_lon = getattr(event, 'longitude', 0.0)
        
        # Try to get elevation from event data if available
        # Note: elevation may not be in event data, so we'll use 0 as fallback
        station_elev = getattr(event, 'elevation', 0.0)
        
        if station_lat != 0.0:
            ws[cell_mapping['LatitudeFormat']] = 'deg.ddddd'
            ws[cell_mapping['Latitude']] = '%0.5f' % abs(station_lat)
            ws[cell_mapping['LatitudeDir']] = 'S' if station_lat < 0 else 'N'
        
        if station_lon != 0.0:
            ws[cell_mapping['LongitudeFormat']] = 'deg.ddddd'
            ws[cell_mapping['Longitude']] = '%0.5f' % abs(station_lon)
            ws[cell_mapping['LongitudeDir']] = 'W' if station_lon < 0 else 'E'
        
        if station_elev != 0.0:
            ws[cell_mapping['Elevation']] = station_elev
            ws[cell_mapping['ElevationUnits']] = 'm'
            ws[cell_mapping['ElevationDatum']] = 'WGS84'
        
        # Observer name and email still come from config
        observer_name = self.config.get_observer_name()
        observer_email = self.config.get_observer_email()
        if observer_name:
            ws[cell_mapping['ObserverName']] = observer_name
        if observer_email:
            ws[cell_mapping['ObserverEmail']] = observer_email
        
        # Observer mailing address information
        observer_address = self.config.get_observer_address()
        observer_city = self.config.get_observer_city()
        observer_state = self.config.get_observer_state()
        observer_country = self.config.get_observer_country()
        observer_phone = self.config.get_observer_phone()
        observer_fax = self.config.get_observer_fax()
        
        if observer_address:
            ws[cell_mapping['ObserverAddress']] = observer_address
        
        # Combine city, state, country into single cell
        city_state_country_parts = []
        if observer_city:
            city_state_country_parts.append(observer_city)
        if observer_state:
            city_state_country_parts.append(observer_state)
        if observer_country:
            city_state_country_parts.append(observer_country)
        if city_state_country_parts:
            ws[cell_mapping['ObserverCityStateCountry']] = ', '.join(city_state_country_parts)
        
        if observer_phone:
            ws[cell_mapping['ObserverPhone']] = observer_phone
        if observer_fax:
            ws[cell_mapping['ObserverFax']] = observer_fax
    
    def _fill_telescope_data(self, ws, cell_mapping):
        """Fill in telescope information from config (supports multiple telescopes)"""
        # Use specified telescope ID if provided, otherwise use active telescope
        if hasattr(self, '_report_telescope_id') and self._report_telescope_id:
            # Find the specific telescope by ID
            telescopes = self.config.get_telescopes()
            telescope = None
            for t in telescopes:
                if t.get('id') == self._report_telescope_id:
                    telescope = t
                    print("Found telescope by ID: {} - {}".format(t.get('id'), t.get('name')))
                    break
            if not telescope:
                print("ERROR: Telescope ID '{}' not found in list!".format(self._report_telescope_id))
        else:
            # Try to get active telescope
            telescope = self.config.get_active_telescope()
            if telescope:
                print("Using active telescope: {}".format(telescope.get('name', 'Unknown')))
        
        if telescope:
            aperture = telescope.get('aperture', 0)
            focal_ratio = telescope.get('focal_ratio', 0)
            
            # Backward compatibility: if focal_ratio is 0 but focal_length exists, calculate it
            if focal_ratio == 0 and telescope.get('focal_length', 0) > 0 and aperture > 0:
                focal_ratio = telescope.get('focal_length') / aperture
            
            telescope_type = telescope.get('type', '')
            telescope_name = telescope.get('name', '')
        else:
            # Fallback to legacy single telescope config
            aperture = self.config.get_telescope_aperture()
            focal_ratio = 0  # Legacy config doesn't have focal_ratio
            telescope_type = self.config.get_telescope_type()
            telescope_name = ''
        
        if aperture > 0:
            ws[cell_mapping['Aperture']] = aperture / 10.0  # Convert mm to cm
            ws[cell_mapping['ApertureUnits']] = 'cm'
        
        if focal_ratio > 0:
            ws[cell_mapping['FocalRatio']] = round(focal_ratio, 2)
        
        if telescope_type:
            ws[cell_mapping['TelescopeType']] = telescope_type
        
        # Store telescope name for later use in comment
        self._telescope_name = telescope_name
    
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
        """Fill in metadata fields (supports multiple cameras)"""
        # Use specified camera ID if provided, otherwise use active camera
        if hasattr(self, '_report_camera_id') and self._report_camera_id:
            # Find the specific camera by ID
            cameras = self.config.get_cameras()
            camera = None
            for c in cameras:
                if c.get('id') == self._report_camera_id:
                    camera = c
                    print("Found camera by ID: {} - {}".format(c.get('id'), c.get('model')))
                    break
            if not camera:
                print("ERROR: Camera ID '{}' not found in list!".format(self._report_camera_id))
        else:
            # Try to get active camera
            camera = self.config.get_active_camera()
            if camera:
                print("Using active camera: {}".format(camera.get('model', 'Unknown')))
        
        if camera:
            # Use camera configuration
            timing = camera.get('timing', 'GPS - other linking')
            timing_device = camera.get('timing_device', 'SharpCap')
            detector = camera.get('detector', 'SharpCap')
            other_info = camera.get('other_info', '')
            video_format = camera.get('video_format', 'SER')
            exposure_integration = camera.get('exposure_integration', 'Other')
            camera_name = camera.get('name', '')
        else:
            # Default values
            timing = 'GPS - other linking'
            timing_device = 'SharpCap'
            detector = 'SharpCap'
            other_info = 'SharpCap'
            video_format = 'SER'
            exposure_integration = 'Other'
            camera_name = ''
        
        # Fill timing and detector fields
        ws[cell_mapping['Timing']] = timing
        ws[cell_mapping['TimingDevice']] = timing_device
        ws[cell_mapping['Detector']] = detector
        
        # Detector info (include exposure if available)
        detector_info = other_info
        if hasattr(event, 'exposure_ms') and event.exposure_ms:
            if detector_info:
                detector_info += f' | Exp {event.exposure_ms}ms'
            else:
                detector_info = f'Exp {event.exposure_ms}ms'
        ws[cell_mapping['OtherDetectorRelatedInfo']] = detector_info
        
        # Video format
        ws[cell_mapping['VideoFormat']] = video_format
        ws[cell_mapping['ExposureIntegration']] = exposure_integration
        
        # Comment - include telescope and camera names
        comment_parts = []
        if hasattr(self, '_telescope_name') and self._telescope_name:
            comment_parts.append(f"Telescope: {self._telescope_name}")
        if camera_name:
            comment_parts.append(f"Camera: {camera_name}")
        
        comment = ' | '.join(comment_parts)
        if comment:
            ws[cell_mapping['CommentLine1']] = comment
        ws[cell_mapping['CommentLine3']] = 'This report was pre-filled by Occultation Manager'
    
    def _generate_filename(self, event):
        """Generate NA report filename: YYYYMMDD_###_Asteroid name_Last name_POS/NEG.xlsx"""
        # Get date
        if hasattr(event, 'event_datetime') and event.event_datetime:
            event_date = event.event_datetime.strftime('%Y%m%d')
        else:
            event_date = 'unknown'
        
        # Get asteroid number (###) - use object_no directly
        object_no = getattr(event, 'object_no', '')
        
        # Get asteroid name with spaces replaced by underscores
        # Remove the leading number in parentheses: "(46584) 1998 QY42" -> "1998 QY42"
        object_name = getattr(event, 'object_name', '')
        # Remove leading pattern like (46584) from the start
        object_name = re.sub(r'^\(\d+\)\s*', '', object_name).strip().replace(' ', '_')
        
        # Get observer surname from config
        observer_name = self.config.get_observer_name()
        if observer_name:
            # Get surname (last part)
            name_parts = observer_name.split()
            surname = name_parts[-1] if name_parts else observer_name
            surname = surname.replace(' ', '_')
        else:
            surname = 'Observer'
        
        # Determine result indicator (POS for positive, NEG for negative/unsure)
        # For now, default to 'NEG' (negative/no detection)
        result_indicator = 'NEG'
        
        # NA format: YYYYMMDD_###_Asteroid_name_Surname_POS/NEG.xlsx
        filename = f"{event_date}_{object_no}_{object_name}_{surname}_{result_indicator}.xlsx"
        
        return filename
