"""
Occult 4 XML Export Module
Exports occultation observation data in the Occult 4 XML format (Version 2.15+)

This module generates XML files compatible with the Occult 4 software for 
asteroid occultation analysis. It uses data already collected for NA and TT reports.

Note: EventFits section is omitted from the exported XML. This section (containing
elliptic fits, uncertainties, shape model fits, etc.) will be added by IOTA after
the observation reports are processed.
"""

import os
from datetime import datetime
from xml.sax.saxutils import escape as xml_escape


class Occult4Exporter:
    """Generates Occult 4 XML format files from observation data"""
    
    FILE_VERSION = "2.15"
    
    def __init__(self, config):
        """Initialize with configuration manager"""
        self.config = config
    
    def export_observation(self, event, telescope_id=None, camera_id=None, 
                          observation_type=None, tangra_data=None, aota_report_data=None,
                          observer_data=None):
        """
        Export observation data to Occult 4 XML format
        
        Args:
            event: OccultationEvent object with event details
            telescope_id: ID of telescope used
            camera_id: ID of camera used
            observation_type: Type of observation ("Positive", "Negative", "Unsure")
            tangra_data: Optional dictionary with Tangra light curve analysis data
            aota_report_data: Optional dictionary with AOTA Report timing/SNR data
            observer_data: Optional dictionary with additional observer information
        
        Returns:
            Path to the generated XML file, or None if generation failed
        """
        try:
            # Get report folder
            report_folder = os.path.join(self.config.get_file_folder(), 'Reports')
            if not os.path.exists(report_folder):
                os.makedirs(report_folder)
            
            # Generate filename
            filename = self._generate_filename(event)
            output_path = os.path.join(report_folder, filename)
            
            # Generate XML content
            xml_content = self._build_xml(event, telescope_id, camera_id, 
                                         observation_type, tangra_data, 
                                         aota_report_data, observer_data)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            print(f"Occult 4 XML exported to: {output_path}")
            return output_path
            
        except Exception as ex:
            print(f"ERROR: Failed to export Occult 4 XML - {str(ex)}")
            import traceback
            traceback.print_exc()
            return None
    
    def export_observation_to_path(self, output_path, event, telescope_id=None, camera_id=None, 
                                   observation_type=None, tangra_data=None, aota_report_data=None,
                                   observer_data=None):
        """
        Export observation data to Occult 4 XML format with a specified output path
        
        Args:
            output_path: Full path where the XML file should be saved
            event: OccultationEvent object with event details
            telescope_id: ID of telescope used
            camera_id: ID of camera used
            observation_type: Type of observation ("Positive", "Negative", "Unsure")
            tangra_data: Optional dictionary with Tangra light curve analysis data
            aota_report_data: Optional dictionary with AOTA Report timing/SNR data
            observer_data: Optional dictionary with additional observer information
        
        Returns:
            Path to the generated XML file, or None if generation failed
        """
        try:
            # Generate XML content
            xml_content = self._build_xml(event, telescope_id, camera_id, 
                                         observation_type, tangra_data, 
                                         aota_report_data, observer_data)
            
            # Write to file
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(xml_content)
            
            print(f"Occult 4 XML exported to: {output_path}")
            return output_path
            
        except Exception as ex:
            print(f"ERROR: Failed to export Occult 4 XML - {str(ex)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _generate_filename(self, event):
        """Generate output filename based on event details"""
        event_date_str = event.event_datetime.strftime('%Y%m%d') if hasattr(event, 'event_datetime') and event.event_datetime else 'unknown'
        
        # Extract asteroid number and name
        asteroid = ''
        if hasattr(event, 'object_no') and event.object_no:
            asteroid = str(event.object_no)
        if hasattr(event, 'object_name') and event.object_name:
            name = event.object_name.replace('(', '').replace(')', '')
            name = ''.join(c for c in name if c.isalnum() or c in [' ', '_', '-'])
            if asteroid:
                asteroid += '_' + name
            else:
                asteroid = name
        
        if not asteroid:
            asteroid = 'Unknown'
        
        # Extract star identifier
        star = ''
        if hasattr(event, 'star_id') and event.star_id:
            star = event.star_id.replace(' ', '_')[:20]
        else:
            star = 'Unknown'
        
        filename = f"{event_date_str}_{asteroid}_{star}_Occult4.xml"
        # Clean up filename
        filename = ''.join(c for c in filename if c.isalnum() or c in ['_', '-', '.'])
        
        return filename
    
    def _build_xml(self, event, telescope_id, camera_id, observation_type, 
                   tangra_data, aota_report_data, observer_data):
        """Build the complete Occult 4 XML structure"""
        
        lines = []
        lines.append('<?xml version="1.0" encoding="UTF-8"?>')
        lines.append('<AsteroidOccultations>')
        lines.append(f'   <FileVersion>{self.FILE_VERSION}</FileVersion>')
        lines.append('   <Event>')
        
        # Date line
        lines.append(self._build_date_line(event))
        
        # Details section
        lines.append('       <Details>')
        lines.append(self._build_star_line(event))
        lines.append(self._build_star_issues_line(event))
        lines.append(self._build_asteroid_line(event))
        
        # EventFits section omitted - will be added by IOTA after report processing
        
        lines.append('       </Details>')
        
        # Observations section
        lines.append('       <Observations>')
        lines.append(self._build_prediction_line(event))
        lines.append(self._build_observer_section(event, telescope_id, camera_id, 
                                                   observation_type, tangra_data, 
                                                   aota_report_data, observer_data))
        lines.append('       </Observations>')
        
        # Added and LastEdited dates
        today = datetime.now()
        date_str = f'{today.year}|{today.month}|{today.day}'
        lines.append(f'        <Added>{date_str}</Added>')
        lines.append(f'        <LastEdited>{date_str}</LastEdited>')
        
        lines.append('   </Event>')
        lines.append('</AsteroidOccultations>')
        
        return '\n'.join(lines)
    
    def _build_date_line(self, event):
        """Build the Date line: year|month|day|hour"""
        if hasattr(event, 'event_datetime') and event.event_datetime:
            dt = event.event_datetime
            hour_decimal = dt.hour + dt.minute / 60.0 + dt.second / 3600.0
            return f'        <Date>{dt.year}|{dt.month}|{dt.day}|{hour_decimal:.1f}</Date>'
        else:
            return '        <Date>0|0|0|0.0</Date>'
    
    def _build_star_line(self, event):
        """Build the Star line with catalog, position, and magnitude data"""
        # Parse star catalog and number
        star_catalog, star_number = self._parse_star_catalog(event.star_id if hasattr(event, 'star_id') else '')
        
        # Determine Gaia version based on catalog
        gaia_version = -1  # -1 = not specified
        gaia_id = '0'
        if 'Gaia DR3' in str(star_catalog):
            gaia_version = 3
            gaia_id = star_number
        elif 'Gaia DR2' in str(star_catalog):
            gaia_version = 2
            gaia_id = star_number
        elif 'Gaia DR1' in str(star_catalog):
            gaia_version = 1
            gaia_id = star_number
        
        # Get RA and Dec in required format
        ra_hours = event.ra_hours if hasattr(event, 'ra_hours') else 0.0
        dec_degrees = event.dec_degrees if hasattr(event, 'dec_degrees') else 0.0
        
        # Format RA and Dec with proper precision per OBS.XML format specs
        # J2000 coordinates: RA has 10 decimals, Dec has 9 decimals
        ra_j2000 = f'{ra_hours:.10f}'
        dec_j2000 = f'{dec_degrees:+.9f}'  # Include sign
        
        # Uncertainties (defaults if not available)
        ra_uncertainty = '0'  # mas
        dec_uncertainty = '0'  # mas
        
        # Star diameter (default)
        star_diameter = '0'  # mas
        
        # Issues flag (0 = no issues)
        issues_flag = '0'
        
        # Apparent RA/Dec (same as J2000 for simplicity, but with reduced precision)
        # Apparent coordinates: RA has 8 decimals, Dec has 7 decimals
        ra_apparent = f'{ra_hours:.8f}'
        dec_apparent = f'{dec_degrees:+.7f}'
        
        # Magnitudes - format with 2 decimal places
        star_mag = event.star_mag if hasattr(event, 'star_mag') else 0.0
        mag_b = f'{star_mag:.2f}'
        mag_g = f'{star_mag:.2f}'
        mag_r = f'{star_mag:.2f}'
        
        # EPIC ID (not typically used)
        epic_id = ''
        
        star_line = (
            f'           <Star>{star_catalog}|{star_number}|{gaia_version}|{gaia_id}|'
            f'{ra_j2000}|{dec_j2000}|{ra_uncertainty}|{dec_uncertainty}|'
            f'{star_diameter}|{issues_flag}|{ra_apparent}|{dec_apparent}|'
            f'{mag_b}|{mag_g}|{mag_r}|{epic_id}</Star>'
        )
        
        return star_line
    
    def _parse_star_catalog(self, star_name):
        """Parse star name to determine catalog and number"""
        if not star_name:
            return 'Unknown', '0'
        
        # Gaia DR3 format
        if 'Gaia DR3' in star_name:
            return 'Gaia DR3', star_name.replace('Gaia DR3 ', '').strip()
        
        # Gaia DR2 format
        if 'Gaia DR2' in star_name:
            return 'Gaia DR2', star_name.replace('Gaia DR2 ', '').strip()
        
        # UCAC4 format
        if star_name.startswith('UCAC4'):
            return 'UCAC4', star_name.replace('UCAC4 ', '').strip()
        
        # Tycho format
        if star_name.startswith('TYC'):
            return 'Tycho2', star_name.replace('TYC ', '').strip()
        
        # NOMAD format
        if star_name.upper().startswith('NOMAD'):
            return 'NOMAD', star_name.replace('NOMAD ', '').replace('nomad ', '').strip()
        
        # Default fallback
        return 'Unknown', star_name
    
    def _build_star_issues_line(self, event):
        """Build the StarIssues line with reliability and quality indicators"""
        # Default values for all fields
        reliability = '0'  # RUWE or equivalent
        duplicated_flag = '-1'  # -1 = not specified
        no_proper_motion = '-1'  # -1 = not specified
        ucac4_proper_motion = '0'  # 0 = not applicable
        brightness_ratio = '1.2'  # Default ratio
        brightness_ratio_uncertainty = '10'  # Default 10%
        ra_offset = '0'  # mas
        dec_offset = '0'  # mas
        ra_offset_sdev = '0'  # mas
        dec_offset_sdev = '0'  # mas
        component_id = ''  # Known double star component
        
        star_issues_line = (
            f'               <StarIssues>{reliability}|{duplicated_flag}|{no_proper_motion}|'
            f'{ucac4_proper_motion}|{brightness_ratio}|{brightness_ratio_uncertainty}|'
            f'{ra_offset}|{dec_offset}|{ra_offset_sdev}|{dec_offset_sdev}|{component_id}</StarIssues>'
        )
        
        return star_issues_line
    
    def _build_asteroid_line(self, event):
        """Build the Asteroid line with motion coefficients and physical data"""
        # Asteroid identification
        asteroid_number = event.object_no if hasattr(event, 'object_no') and event.object_no else ''
        asteroid_name = event.object_name if hasattr(event, 'object_name') and event.object_name else ''
        
        # Clean asteroid name (remove number if present)
        if asteroid_name:
            import re
            asteroid_name = re.sub(r'^\(\d+\)\s*', '', asteroid_name)
        
        # Motion coefficients (all zeros if not available - would need ephemeris data)
        dx = '0'  # Earth radii/hr
        dy = '0'
        d2x = '0'  # Earth radii/hr²
        d2y = '0'
        d3x = '0'  # Earth radii/hr³
        d3y = '0'
        
        # Parallax
        parallax = '0'  # arcsec
        d_parallax = '0'  # arcsec/hr
        
        # Diameter
        diameter = '0'  # km (nominal mean diameter)
        diameter_uncertainty = '0'  # km
        
        # Visual magnitude
        mv = '0'
        
        asteroid_line = (
            f'           <Asteroid>{asteroid_number}|{asteroid_name}|{dx}|{dy}|{d2x}|{d2y}|'
            f'{d3x}|{d3y}|{parallax}|{d_parallax}|{diameter}|{diameter_uncertainty}|{mv}</Asteroid>'
        )
        
        return asteroid_line
    
    def _build_prediction_line(self, event):
        """Build the Prediction line with predicted event details"""
        # Sequential reference number
        seq_num = '1'
        
        # Longitude and latitude in DMS format
        longitude = self._format_dms(event.longitude if hasattr(event, 'longitude') else 0, is_longitude=True)
        latitude = self._format_dms(event.latitude if hasattr(event, 'latitude') else 0, is_longitude=False)
        
        # Time - separate fields for hr, min, sec
        if hasattr(event, 'event_datetime') and event.event_datetime:
            dt = event.event_datetime
            hour = str(dt.hour)
            minute = str(dt.minute)
            # Format seconds with one decimal place: s.s
            second = f'{dt.second + dt.microsecond/1000000.0:.1f}'
        else:
            hour = '0'
            minute = '0'
            second = '0.0'
        
        # Event comments
        comments = ''
        
        prediction_line = (
            f'           <Prediction>{seq_num}|{longitude}|{latitude}|{hour}|{minute}|{second}|{comments}</Prediction>'
        )
        
        return prediction_line
    
    def _format_dms(self, decimal_degrees, is_longitude=True):
        """Convert decimal degrees to DMS format: ±ddd mm ss.s"""
        is_negative = decimal_degrees < 0
        abs_degrees = abs(decimal_degrees)
        
        degrees = int(abs_degrees)
        minutes_decimal = (abs_degrees - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        
        sign = '-' if is_negative else '+'
        
        # Both longitude and latitude use ss.s format (one decimal place)
        if is_longitude:
            return f'{sign}{degrees:03d} {minutes:02d} {seconds:04.1f}'
        else:
            return f'{sign}{degrees:02d} {minutes:02d} {seconds:04.1f}'
    
    def _build_observer_section(self, event, telescope_id, camera_id, 
                               observation_type, tangra_data, aota_report_data, 
                               observer_data):
        """Build the complete Observer section"""
        lines = []
        lines.append('           <Observer>')
        lines.append(self._build_observer_id_line(event, telescope_id, camera_id, observer_data))
        lines.append(self._build_conditions_line(observer_data))
        lines.append(self._build_d_event_line(event, observation_type, tangra_data, aota_report_data))
        lines.append(self._build_r_event_line(event, observation_type, tangra_data, aota_report_data))
        lines.append('           </Observer>')
        
        return '\n'.join(lines)
    
    def _build_observer_id_line(self, event, telescope_id, camera_id, observer_data):
        """Build the Observer ID line with equipment and location details"""
        # Sequential reference number
        seq_num = '1'
        
        # Observer names
        observer1 = self.config.get_observer_name() if self.config else ''
        observer2 = ''
        more_than_2 = ''
        
        # Override with observer_data if provided
        if observer_data:
            observer1 = observer_data.get('observer1', observer1)
            observer2 = observer_data.get('observer2', observer2)
            more_than_2 = observer_data.get('more_than_2', more_than_2)
        
        # Near location
        near_location = event.obs_location if hasattr(event, 'obs_location') and event.obs_location else ''
        
        # State/country
        state_country = self.config.get_observer_state() if self.config else ''
        if observer_data:
            state_country = observer_data.get('state_country', state_country)
        
        # Coordinates
        longitude = self._format_dms(event.longitude if hasattr(event, 'longitude') else 0, is_longitude=True)
        latitude = self._format_dms(event.latitude if hasattr(event, 'latitude') else 0, is_longitude=False)
        
        # Altitude
        altitude = int(event.elevation) if hasattr(event, 'elevation') else 0
        
        # Datum
        datum = '_'  # WGS84
        
        # Telescope aperture and type
        telescope_aperture = ''
        telescope_type = '_'  # unstated
        
        telescope_data = self._get_telescope_data(telescope_id)
        if telescope_data:
            aperture = telescope_data.get('aperture', '')
            if aperture:
                try:
                    telescope_aperture = str(float(aperture))
                except:
                    pass
            
            tel_type = telescope_data.get('type', '').lower()
            if 'refractor' in tel_type:
                telescope_type = '1'
            elif 'newtonian' in tel_type:
                telescope_type = '2'
            elif 'sct' in tel_type or 'schmidt' in tel_type:
                telescope_type = '3'
            elif 'dob' in tel_type:
                telescope_type = '4'
        
        # Observing method
        observing_method = 'b'  # Digital SLR-camera video (default)
        camera_data = self._get_camera_data(camera_id)
        if camera_data:
            # Try to determine method from camera type
            camera_type = camera_data.get('type', '').lower()
            if 'video' in camera_type:
                observing_method = 'b'
            elif 'photometer' in camera_type:
                observing_method = 'c'
            elif 'dslr' in camera_type or 'sequential' in camera_type:
                observing_method = 'd'
        
        # Time source
        time_source = 'a'  # GPS (default)
        if observer_data:
            time_source = observer_data.get('time_source', time_source)
        
        id_line = (
            f'               <ID>{seq_num}|{observer1}|{observer2}|{more_than_2}|{near_location}|'
            f'{state_country}|{longitude}|{latitude}|{altitude}|{datum}|{telescope_aperture}|'
            f'{telescope_type}|{observing_method}|{time_source}</ID>'
        )
        
        return id_line
    
    def _get_telescope_data(self, telescope_id):
        """Get telescope data from configuration"""
        if not telescope_id or not self.config:
            return None
        
        telescopes = self.config.get_telescopes()
        for t in telescopes:
            if t.get('id') == telescope_id:
                return t
        return None
    
    def _get_camera_data(self, camera_id):
        """Get camera data from configuration"""
        if not camera_id or not self.config:
            return None
        
        cameras = self.config.get_cameras()
        for c in cameras:
            if c.get('id') == camera_id:
                return c
        return None
    
    def _build_conditions_line(self, observer_data):
        """Build the Conditions line with observing conditions"""
        # Default values
        stability = '_'  # unstated
        transparency = '_'  # unstated
        sn = ''  # Signal-to-noise ratio
        time_adjustment = '0'  # ±s.ss
        comment = ''
        
        # Override with observer_data if provided
        if observer_data:
            stability = observer_data.get('stability', stability)
            transparency = observer_data.get('transparency', transparency)
            sn = observer_data.get('sn', sn)
            time_adjustment = observer_data.get('time_adjustment', time_adjustment)
            comment = observer_data.get('comment', comment)
        
        conditions_line = (
            f'               <Conditions>{stability}|{transparency}|{sn}|'
            f'{time_adjustment}|{comment}</Conditions>'
        )
        
        return conditions_line
    
    def _build_d_event_line(self, event, observation_type, tangra_data, aota_report_data):
        """Build the D (disappearance) event line"""
        # Time
        time_str = self._get_d_time(tangra_data, aota_report_data, event)
        
        # Event code
        event_code = self._get_event_code(observation_type, is_d=True)
        
        # Accuracy
        accuracy = self._get_timing_accuracy(tangra_data, aota_report_data)
        
        # PEqn (personal equation)
        peqn = '0'
        
        # Weight (blank for default)
        weight = ''
        
        # Plot code (blank to include)
        plot_code = '_' if event_code in ['D', 'd', 'G', 'g'] else 'x'
        
        d_line = f'               <D>{time_str}|{event_code}|{accuracy}|{peqn}|{weight}|{plot_code}</D>'
        
        return d_line
    
    def _build_r_event_line(self, event, observation_type, tangra_data, aota_report_data):
        """Build the R (reappearance) event line"""
        # Time
        time_str = self._get_r_time(tangra_data, aota_report_data, event)
        
        # Event code
        event_code = self._get_event_code(observation_type, is_d=False)
        
        # Accuracy
        accuracy = self._get_timing_accuracy(tangra_data, aota_report_data)
        
        # PEqn
        peqn = '0'
        
        # Weight
        weight = ''
        
        # Plot code
        plot_code = '_' if event_code in ['R', 'r', 'B', 'b'] else 'x'
        
        r_line = f'               <R>{time_str}|{event_code}|{accuracy}|{peqn}|{weight}|{plot_code}</R>'
        
        return r_line
    
    def _get_d_time(self, tangra_data, aota_report_data, event):
        """Get disappearance time from available data sources"""
        # Try AOTA report data first (has d_hours, d_minutes, d_seconds)
        if aota_report_data and 'd_hours' in aota_report_data:
            hours = str(aota_report_data.get('d_hours', '0')).zfill(2)
            minutes = str(aota_report_data.get('d_minutes', '0')).zfill(2)
            seconds = str(aota_report_data.get('d_seconds', '0.0'))
            # Ensure seconds has proper format (at least .xx)
            if '.' not in seconds:
                seconds = seconds.zfill(2) + '.00'
            else:
                parts = seconds.split('.')
                seconds = parts[0].zfill(2) + '.' + parts[1].ljust(2, '0')[:2]
            return f'{hours} {minutes} {seconds}'
        
        # Tangra data doesn't have d_time - skip it
        # Note: Tangra CSV only has observation start/end times, not event times
        
        # Fall back to event predicted time
        if hasattr(event, 'event_datetime') and event.event_datetime:
            dt = event.event_datetime
            seconds_with_fraction = dt.second + dt.microsecond / 1000000.0
            return f'{dt.hour:02d} {dt.minute:02d} {seconds_with_fraction:05.2f}'
        
        return '00 00 00.00'
    
    def _get_r_time(self, tangra_data, aota_report_data, event):
        """Get reappearance time from available data sources"""
        # Try AOTA report data first (has r_hours, r_minutes, r_seconds)
        if aota_report_data and 'r_hours' in aota_report_data:
            hours = str(aota_report_data.get('r_hours', '0')).zfill(2)
            minutes = str(aota_report_data.get('r_minutes', '0')).zfill(2)
            seconds = str(aota_report_data.get('r_seconds', '0.0'))
            # Ensure seconds has proper format (at least .xx)
            if '.' not in seconds:
                seconds = seconds.zfill(2) + '.00'
            else:
                parts = seconds.split('.')
                seconds = parts[0].zfill(2) + '.' + parts[1].ljust(2, '0')[:2]
            return f'{hours} {minutes} {seconds}'
        
        # Tangra data doesn't have r_time - skip it
        # Note: Tangra CSV only has observation start/end times, not event times
        
        # If we have a D time and duration, calculate R time
        if hasattr(event, 'event_datetime') and event.event_datetime and hasattr(event, 'event_duration'):
            from datetime import timedelta
            dt = event.event_datetime + timedelta(seconds=event.event_duration)
            seconds_with_fraction = dt.second + dt.microsecond / 1000000.0
            return f'{dt.hour:02d} {dt.minute:02d} {seconds_with_fraction:05.2f}'
        
        return '00 00 00.00'
    
    def _format_time_hms(self, time_value):
        """Format time value to hh mm ss.ss format"""
        if isinstance(time_value, str):
            # Parse time string (could be HH:MM:SS.SS or other formats)
            # Expected format from AOTA/Tangra: "HH:MM:SS.SS" or similar
            time_str = time_value.strip()
            
            # Try to parse different formats
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) >= 3:
                    hh = parts[0].strip().zfill(2)
                    mm = parts[1].strip().zfill(2)
                    ss = parts[2].strip()
                    # Ensure seconds has .xx format
                    if '.' not in ss:
                        ss = ss.zfill(2) + '.00'
                    else:
                        ss_parts = ss.split('.')
                        ss = ss_parts[0].zfill(2) + '.' + ss_parts[1].ljust(2, '0')[:2]
                    return f'{hh} {mm} {ss}'
        
        # If it's a datetime object
        if hasattr(time_value, 'hour'):
            seconds_with_fraction = time_value.second + time_value.microsecond / 1000000.0
            return f'{time_value.hour:02d} {time_value.minute:02d} {seconds_with_fraction:05.2f}'
        
        return '00 00 00.00'
    
    def _get_event_code(self, observation_type, is_d=True):
        """Get event code based on observation type"""
        if observation_type == "Positive":
            return 'D' if is_d else 'R'
        elif observation_type == "Negative":
            # For negative observations, both D and R use 'M' code
            return 'M'  # Miss/non-detection (applies to both D and R lines)
        else:
            # For "Unsure" or other types, use Miss code
            return 'M'
    
    def _get_timing_accuracy(self, tangra_data, aota_report_data):
        """Get timing accuracy from available data"""
        # Try to get from AOTA report
        if aota_report_data and 'd_uncertainty' in aota_report_data:
            try:
                return f"{float(aota_report_data['d_uncertainty']):.2f}"
            except:
                pass
        
        # Try Tangra data
        if tangra_data and 'd_uncertainty' in tangra_data:
            try:
                return f"{float(tangra_data['d_uncertainty']):.2f}"
            except:
                pass
        
        # Default accuracy for video observations
        return '0.5'
