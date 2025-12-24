"""
Trans-Tasman / RASNZ Occultation Report Form Generator
Generates reports using the RASNZ Asteroid Report Form format

Uses simple_xlsx: A minimal pure-Python Excel reader/writer for IronPython
No C extensions, no external dependencies beyond Python stdlib
"""

import os
import re
from datetime import datetime
from simple_xlsx import load_workbook
from report_generator_base import ReportGeneratorBase


class TTReportGenerator(ReportGeneratorBase):
    """Generates Trans-Tasman / RASNZ Occultation Report Forms using the official template"""
    
    # Local template file (must be converted to XLSX format)
    TEMPLATE_FILENAME = 'RASNZ_AstReporttForm_V4.1.2.G.xlsx'
    
    def __init__(self, config):
        """Initialize with configuration manager"""
        super(TTReportGenerator, self).__init__(config)
    
    def get_template_path(self):
        """Get path to local template file bundled with the project"""
        # Template is in the same directory as this script
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, self.TEMPLATE_FILENAME)
    
    def get_cell_mapping(self):
        """Get the cell mapping dict for Trans-Tasman form"""
        return {
            # Event information
            'ObservationType': 'A2',  # Positive/Negative/Unsure/Maybe
            'EventYear': 'D5',
            'EventMonth': 'K5',
            'EventDay': 'P5',
            'PredictedHours': 'Y5',
            'PredictedMinutes': 'AA5',
            'PredictedSeconds': 'AC5',
            'AstNum': 'E7',  # Merged cells E-F7
            'AstName': 'K7',
            'StarCatalog': 'S7',
            'StarNumber': 'X7',
            
            # RIO-TNO
            'RioTnoPrediction': 'P8',  # Yes/No
            
            # Observer information
            'ObserverName': 'D9',
            'ObserverEmail': 'S9',
            'ObserverAddress': 'D11',
            'ObserverPhone': 'S11',
            'ObserverCityStateCountry': 'D13',
            'ObserverFax': 'S13',
            'ObservingLocation': 'E15',
            
            # Location
            'LatitudeFormat': 'E17',
            'Latitude': 'E18',
            'LatitudeDir': 'J18',
            'LongitudeFormat': 'N17',
            'Longitude': 'N18',
            'LongitudeDir': 'R18',
            'Elevation': 'V18',
            'ElevationUnits': 'W18',
            'ElevationDatum': 'AA18',
            
            # Telescope
            'Aperture': 'E20',
            'ApertureUnits': 'H20',
            'FocalRatio': 'L20',
            'Magnification': 'O20',
            'TelescopeType': 'T20',
            
            # Timing and method
            'Timing': 'C22',  # Merged cells C-K22
            'TimingMethod': 'O22',
            'AsteroidVisible': 'Y22',  # Yes/No
            'TimingDevice': 'E23',  # Merged cells E-I23
            'OTAUsed': 'N23',
            
            # Detector/Camera
            'Detector': 'E25',  # Merged cells E-I25
            'DetectorModel': 'E25',
            'VideoFormat': 'L25',
            'Integration': 'O25',
            'IntegrationUnits': 'S25',
            'CameraDelayCorrection': 'N26',
            'VTICorrection': 'S26',
            'VTICorrectionUnits': 'W26',
            'CorrectionsApplied': 'Z26',  # Yes/No
            
            # Conditions
            'Clouds': 'F27',
            'Fog': 'H27',
            'Stability': 'P27',
            'OtherConditions': 'V27',
            
            # Timing observations
            'StartedObservingHours': 'E31',
            'StartedObservingMins': 'G31',
            'StartedObservingSecs': 'I31',
            'MergedHours': 'E32',
            'MergedMins': 'G32',
            'MergedSecs': 'I32',
            'DisappearanceHours': 'E33',
            'DisappearanceMins': 'G33',
            'DisappearanceSecs': 'I33',
            'ClosestApproachHours': 'E34',
            'ClosestApproachMins': 'G34',
            'ClosestApproachSecs': 'I34',
            'ReappearanceHours': 'E35',
            'ReappearanceMins': 'G35',
            'ReappearanceSecs': 'I35',
            'SeparatedHours': 'E36',
            'SeparatedMins': 'G36',
            'SeparatedSecs': 'I36',
            'StoppedObservingHours': 'E37',
            'StoppedObservingMins': 'G37',
            'StoppedObservingSecs': 'I37',
            
            # Miss and comments
            'WasMiss': 'W38',  # Yes/No
            'SecondStar': 'D40',  # Yes/No
            'Comments': 'D42',  # Starting cell for comments
        }
    
    def generate_report(self, event, telescope_id=None, camera_id=None):
        """
        Generate a Trans-Tasman Occultation Report Form for a single event.
        
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
        debug_log = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tt_report_debug.log')
        
        def log(msg):
            print(msg)
            try:
                with open(debug_log, 'a') as f:
                    f.write(msg + '\n')
            except:
                pass
        
        # Log equipment IDs
        log("="*60)
        log("Trans-Tasman Report generation started")
        log("Telescope ID: {}".format(telescope_id if telescope_id else "None"))
        log("Camera ID: {}".format(camera_id if camera_id else "None"))
        
        try:
            # Get event date for filename
            event_date_str = ''
            if hasattr(event, 'event_datetime') and event.event_datetime:
                event_date_str = event.event_datetime.strftime('%Y%m%d')
            if not event_date_str:
                event_date_str = datetime.now().strftime('%Y%m%d')
            
            # Get report folder from config
            report_folder = os.path.join(self.config.get_file_folder(), 'Reports')
            log(f"Event: {event.get_asteroid_display_name() if hasattr(event, 'get_asteroid_display_name') else 'Unknown'}")
            log(f"Report folder: {report_folder}")
            
            # Check template exists
            template_path = self.get_template_path()
            log("Checking template exists...")
            if not os.path.exists(template_path):
                log(f"ERROR: Template not found: {template_path}")
                print(f"ERROR: Template file not found: {template_path}")
                return None
            log(f"Template found: {template_path}")
            
            # Load template workbook
            log("Loading template workbook...")
            wb = load_workbook(template_path)
            log("Workbook loaded successfully")
            
            # Access DATA worksheet
            log("Accessing DATA worksheet...")
            ws = wb['DATA']
            log("Worksheet accessed successfully")
            
            # Validate template
            log("Validating template...")
            # TODO: Add validation based on actual template structure
            
            # Get cell mapping
            log("Getting cell mapping...")
            cell_mapping = self.get_cell_mapping()
            
            # Fill in the report
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
            
            # Generate filename
            log("Generating filename...")
            # Trans-Tasman format: yyyymmdd_MPNumber_MPName_StarCat_StarName<+/->LastName.xlsx
            # Example: 20131003_25_Phocaea_HIP_115725+Timerson.xlsx
            
            # Get observer last name
            observer_surname = self.config.get_observer_name().split()[-1] if self.config.get_observer_name() else 'Observer'
            
            # Get asteroid number - use object_no directly
            asteroid_number = str(event.object_no) if hasattr(event, 'object_no') and event.object_no else 'Unknown'
            
            # Get asteroid name - remove leading parenthetical number: "(46584) 1998 QY42" -> "1998_QY42"
            if hasattr(event, 'object_name') and event.object_name:
                asteroid_name = event.object_name
                # Remove leading number in parentheses: "(46584) 1998 QY42" -> "1998 QY42"
                asteroid_name = re.sub(r'^\(\d+\)\s*', '', asteroid_name).strip()
                # Replace spaces with underscores for filename
                asteroid_name = asteroid_name.replace(' ', '_')
            else:
                asteroid_name = 'Unknown'
            
            # Get star catalog and number
            star_name = getattr(event, 'star_name', None) or getattr(event, 'star_id', None)
            star_catalog = 'Unknown'
            star_number = 'Unknown'
            if star_name:
                parsed_catalog, parsed_number = self.parse_star_catalog(star_name)
                if parsed_catalog and parsed_number:
                    # Map catalog to TT format (strip "1U    " prefix)
                    catalog_mapping = {
                        '1U    UCAC4': 'UCAC4',
                        '1U    UCAC2': 'UCAC2',
                        '1G    Gaia - DR3': 'Gaia_DR3',
                        '1G    Gaia - DR2': 'Gaia_DR2',
                        '1G    Gaia - DR1': 'Gaia_DR1',
                        '1T    Tycho2': 'TYC',
                        '1H    Hipparcos': 'HIP',
                        '1P    PPM': 'PPM',
                        '1D    HD': 'HD'
                    }
                    if parsed_catalog in catalog_mapping:
                        star_catalog = catalog_mapping[parsed_catalog]
                    else:
                        # Strip format prefix as fallback
                        star_catalog = re.sub(r'^1[A-Z]\s+', '', parsed_catalog).strip()
                    
                    # Replace dashes with underscores in star number for filename
                    star_number = parsed_number.replace('-', '_')
            
            # Determine if positive (+) or negative (-) - default to negative
            result_sign = '-'  # User can change in the form, default to miss/negative
            
            # Get station name from event
            station_name = ''
            if hasattr(event, 'station_name') and event.station_name:
                station_name_raw = event.station_name
                # If station name starts with observer surname, remove it to avoid duplication
                if station_name_raw.startswith(observer_surname + ' '):
                    station_name_raw = station_name_raw[len(observer_surname)+1:]
                # Remove PC/machine name suffix if present (e.g., "M Home-AstroPC" -> "M Home")
                if '-' in station_name_raw:
                    parts = station_name_raw.split('-')
                    # Keep only the first part (location name), drop machine identifier
                    station_name_raw = parts[0].strip()
                # Replace spaces and special characters with underscores
                station_name = '_' + station_name_raw.replace(' ', '_').replace(',', '_')
            
            # Build filename: yyyymmdd_MPNumber_MPName_StarCat_StarName+/-LastName_Station.xlsx
            filename = f"{event_date_str}_{asteroid_number}_{asteroid_name}_{star_catalog}_{star_number}{result_sign}{observer_surname}{station_name}.xlsx"
            output_path = os.path.join(report_folder, filename)
            log(f"Report will be saved to: {output_path}")
            
            # Save the workbook
            log("Saving report...")
            wb.save(output_path)
            wb.close()  # Release file handle
            log(f"SUCCESS: Report generated: {output_path}")
            print(f"Report saved to: {output_path}")
            return output_path
            
        except Exception as ex:
            import traceback
            log(f"ERROR generating report: {str(ex)}")
            log(f"Exception type: {type(ex).__name__}")
            log("Full traceback:")
            for line in traceback.format_exc().split('\n'):
                log(line)
            print(f"ERROR: Failed to generate report - {str(ex)}")
            return None
    
    def _fill_event_data(self, ws, cell_mapping, event):
        """Fill in event-specific data"""
        # Observation type - default to Positive (user can change)
        ws[cell_mapping['ObservationType']] = 'Positive'
        
        # Event date/time
        if hasattr(event, 'event_datetime') and event.event_datetime:
            dt = event.event_datetime
            ws[cell_mapping['EventYear']] = dt.year
            ws[cell_mapping['EventMonth']] = self.MONTHS[dt.month - 1]
            ws[cell_mapping['EventDay']] = dt.day
            ws[cell_mapping['PredictedHours']] = dt.hour
            ws[cell_mapping['PredictedMinutes']] = dt.minute
            ws[cell_mapping['PredictedSeconds']] = dt.second
        
        # Asteroid number and name
        if hasattr(event, 'object_no') and event.object_no:
            ws[cell_mapping['AstNum']] = event.object_no
        if hasattr(event, 'object_name') and event.object_name:
            # Remove asteroid number from name
            name = event.object_name
            name = re.sub(r'^\(\d+\)\s*', '', name)
            ws[cell_mapping['AstName']] = name
        
        # Star catalog and number
        star_name = getattr(event, 'star_name', None) or getattr(event, 'star_id', None)
        if star_name:
            star_catalog, star_number = self.parse_star_catalog(star_name)
            if star_catalog and star_number:
                # Map to TT-compatible catalog names (from TABLES sheet A1:A9)
                # Valid values: Gaia DR3, Gaia DR2, Gaia DR1, UCAC4, UCAC2, TYC, HIP, PPM, HD
                # Strip the format prefix like "1U    " from parse_star_catalog output
                catalog_mapping = {
                    '1U    UCAC4': 'UCAC4',
                    '1U    UCAC2': 'UCAC2',
                    '1G    Gaia - DR3': 'Gaia DR3',
                    '1G    Gaia - DR2': 'Gaia DR2',
                    '1G    Gaia - DR1': 'Gaia DR1',
                    '1T    Tycho2': 'TYC',
                    '1H    Hipparcos': 'HIP',
                    '1P    PPM': 'PPM',
                    '1D    HD': 'HD'
                }
                # Use mapping if available, otherwise try to extract just the catalog name
                if star_catalog in catalog_mapping:
                    mapped_catalog = catalog_mapping[star_catalog]
                else:
                    # Try to strip format prefix (e.g., "1X    CatalogName" -> "CatalogName")
                    mapped_catalog = re.sub(r'^1[A-Z]\s+', '', star_catalog).strip()
                
                ws[cell_mapping['StarCatalog']] = mapped_catalog
                ws[cell_mapping['StarNumber']] = star_number
        
        # RIO-TNO prediction - default to No
        ws[cell_mapping['RioTnoPrediction']] = 'No'
    
    def _fill_observer_data(self, ws, cell_mapping, event):
        """Fill in observer information"""
        # Observer name
        observer_name = self.config.get_observer_name()
        if observer_name:
            ws[cell_mapping['ObserverName']] = observer_name
        
        # Email
        observer_email = self.config.get_observer_email()
        if observer_email:
            ws[cell_mapping['ObserverEmail']] = observer_email
        
        # Address
        observer_address = self.config.get_observer_address()
        if observer_address:
            ws[cell_mapping['ObserverAddress']] = observer_address
        
        # Phone
        observer_phone = self.config.get_observer_phone() if hasattr(self.config, 'get_observer_phone') else ''
        if observer_phone:
            ws[cell_mapping['ObserverPhone']] = observer_phone
        
        # Fax (if available)
        observer_fax = self.config.get_observer_fax() if hasattr(self.config, 'get_observer_fax') else ''
        if observer_fax:
            ws[cell_mapping['ObserverFax']] = observer_fax
        
        # City, State, Country - combine into one field
        city = self.config.get_observer_city()
        state = self.config.get_observer_state()
        country = self.config.get_observer_country() if hasattr(self.config, 'get_observer_country') else ''
        
        city_state_country_parts = []
        if city:
            city_state_country_parts.append(city)
        if state:
            city_state_country_parts.append(state)
        if country:
            city_state_country_parts.append(country)
        
        if city_state_country_parts:
            ws[cell_mapping['ObserverCityStateCountry']] = ', '.join(city_state_country_parts)
        
        # Observing Location
        obs_location = getattr(event, 'obs_location', None)
        if obs_location:
            ws[cell_mapping['ObservingLocation']] = obs_location
        
        # Location coordinates
        station_lat = getattr(event, 'latitude', 0.0)
        station_lon = getattr(event, 'longitude', 0.0)
        station_elev = getattr(event, 'elevation', 0.0)
        
        # Latitude
        if station_lat != 0.0:
            ws[cell_mapping['LatitudeFormat']] = 'deg.ddddd'
            # Use decimal degrees format
            ws[cell_mapping['Latitude']] = abs(station_lat)
            ws[cell_mapping['LatitudeDir']] = 'S' if station_lat < 0 else 'N'
        
        # Longitude
        if station_lon != 0.0:
            ws[cell_mapping['LongitudeFormat']] = 'deg.ddddd'
            # Use decimal degrees format
            ws[cell_mapping['Longitude']] = abs(station_lon)
            ws[cell_mapping['LongitudeDir']] = 'W' if station_lon < 0 else 'E'
        
        # Elevation
        if station_elev != 0.0:
            ws[cell_mapping['Elevation']] = station_elev
            ws[cell_mapping['ElevationUnits']] = 'm'
            ws[cell_mapping['ElevationDatum']] = 'WGS84'
    
    def _fill_telescope_data(self, ws, cell_mapping):
        """Fill in telescope information"""
        # Get telescope by ID or active
        telescope = self.get_telescope_data(self._report_telescope_id)
        
        if telescope:
            # Aperture
            aperture = telescope.get('aperture', 0)
            if aperture:
                # Convert mm to cm
                ws[cell_mapping['Aperture']] = aperture / 10.0
                ws[cell_mapping['ApertureUnits']] = 'cm'
            
            # Focal ratio
            focal_ratio = telescope.get('focal_ratio', 0)
            if focal_ratio == 0 and telescope.get('focal_length', 0) > 0 and aperture > 0:
                focal_ratio = telescope.get('focal_length') / aperture
            if focal_ratio > 0:
                ws[cell_mapping['FocalRatio']] = round(focal_ratio, 2)
            
            # Telescope type
            telescope_type = telescope.get('type', '')
            if telescope_type:
                ws[cell_mapping['TelescopeType']] = telescope_type
            
            # Magnification - leave blank for now (not in our config)
            # User can fill manually if needed
    
    def _fill_recording_times(self, ws, cell_mapping, event):
        """Fill in recording start/stop times"""
        # Started observing - only fill hours column to avoid stray values in mins/secs
        if hasattr(event, 'start_time') and event.start_time:
            ws[cell_mapping['StartedObservingHours']] = event.start_time.hour
            # Note: Mins and Secs cells left blank - user fills from video analysis
        
        # Stopped observing - only fill hours column
        if hasattr(event, 'end_time') and event.end_time:
            ws[cell_mapping['StoppedObservingHours']] = event.end_time.hour
            # Note: Mins and Secs cells left blank - user fills from video analysis
        
        # Other timing fields (merged, disappeared, reappeared, separated) 
        # are left blank for user to fill in from their analysis
        # These are event-specific and not in our event data
    
    def _fill_metadata(self, ws, cell_mapping, event):
        """Fill in metadata fields"""
        # Get camera by ID or active
        camera = self.get_camera_data(self._report_camera_id)
        
        if camera:
            # Timing
            timing = camera.get('timing', 'GPS - other linking')
            if timing:
                ws[cell_mapping['Timing']] = timing
            
            # Timing device
            timing_device = camera.get('timing_device', 'SharpCap')
            if timing_device:
                ws[cell_mapping['TimingDevice']] = timing_device
            
            # Detector
            detector = camera.get('detector', 'SharpCap')
            if detector:
                ws[cell_mapping['Detector']] = detector
            
            # Detector model (camera name/model)
            camera_model = camera.get('model', '')
            if camera_model:
                ws[cell_mapping['DetectorModel']] = camera_model
            
            # Video format
            video_format = camera.get('video_format', 'SER')
            if video_format:
                ws[cell_mapping['VideoFormat']] = video_format
            
            # Exposure/Integration
            exposure_integration = camera.get('exposure_integration', 'Other')
            if exposure_integration:
                ws[cell_mapping['Integration']] = exposure_integration
                ws[cell_mapping['IntegrationUnits']] = 'Frames'
            
            # Other info as comments
            other_info = camera.get('other_info', '')
            if other_info:
                ws[cell_mapping['Comments']] = other_info
        
        # Default some fields
        ws[cell_mapping['AsteroidVisible']] = 'Yes'  # User can change
        ws[cell_mapping['WasMiss']] = 'No'  # User can change
        ws[cell_mapping['SecondStar']] = 'No'  # User can change
        ws[cell_mapping['CorrectionsApplied']] = 'No'  # User can change
        
        # Timing method - leave blank or set default
        ws[cell_mapping['TimingMethod']] = 'Video Recording'
        
        # Conditions - leave blank for user to fill
        # Clouds, Fog, Stability, OtherConditions
