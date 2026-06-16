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
from datetime import datetime, timedelta
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
        
        import re
        filename = f"{event_date_str}_{asteroid}_{star}_Occult4.xml"
        # Clean up filename — allow space for provisional designations (e.g. "2002 PR155")
        filename = ''.join(c for c in filename if c.isalnum() or c in ['_', '-', '.', ' '])
        # Restore space in provisional designations (e.g. 2002_PR155 -> 2002 PR155) in case
        # spaces were collapsed by earlier char-filtering passes
        filename = re.sub(r'(\d{4})_([A-Z]{1,2}\d)', r'\1 \2', filename)
        
        return filename
    
    def _build_xml(self, event, telescope_id, camera_id, observation_type, 
                   tangra_data, aota_report_data, observer_data):
        """Build the complete Occult 4 XML structure"""
        
        lines = []
        lines.append('<AsteroidOccultations>')
        lines.append('   <Event>')
        
        # Date line
        lines.append(self._build_date_line(event))
        
        # Details section
        lines.append('       <Details>')
        lines.append(self._build_star_line(event))
        lines.append(self._build_asteroid_line(event))
        
        # EventFits section omitted - will be added by IOTA after report processing
        
        lines.append('       </Details>')
        
        # Observations section
        lines.append('       <Observations>')
        # Observer comes FIRST, then Prediction (order matters for Occult 4 parser!)
        lines.append(self._build_observer_section(event, telescope_id, camera_id, 
                                                   observation_type, tangra_data, 
                                                   aota_report_data, observer_data))
        lines.append('       </Observations>')
        
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
        
        # Get occelmnt_data if available (preferred source)
        occelmnt_data = event.original_data.get('occelmnt_data', {}) if hasattr(event, 'original_data') else {}
        
        # Get RA and Dec in required format - prefer occelmnt_data
        # J2000 coordinates: RA has 10 decimals, Dec has 9 decimals
        if 'star_ra_j2000' in occelmnt_data and occelmnt_data['star_ra_j2000']:
            try:
                ra_hours = float(occelmnt_data['star_ra_j2000'])
            except (ValueError, TypeError):
                ra_hours = event.ra_hours if hasattr(event, 'ra_hours') else 0.0
        else:
            ra_hours = event.ra_hours if hasattr(event, 'ra_hours') else 0.0
            
        if 'star_dec_j2000' in occelmnt_data and occelmnt_data['star_dec_j2000']:
            try:
                dec_degrees = float(occelmnt_data['star_dec_j2000'])
            except (ValueError, TypeError):
                dec_degrees = event.dec_degrees if hasattr(event, 'dec_degrees') else 0.0
        else:
            dec_degrees = event.dec_degrees if hasattr(event, 'dec_degrees') else 0.0
        
        ra_j2000 = f'{ra_hours:.10f}'
        dec_j2000 = f'{dec_degrees:+.9f}'  # Include sign
        
        # Uncertainties from occelmnt_data if available
        # Use 1-sigma position error for both RA and Dec (isotropic uncertainty)
        ra_uncertainty = '0'  # mas
        dec_uncertainty = '0'  # mas
        if 'error_position_1sigma' in occelmnt_data and occelmnt_data['error_position_1sigma']:
            try:
                # Convert from arcsec to mas - use same value for both RA and Dec
                pos_unc = float(occelmnt_data['error_position_1sigma']) * 1000
                ra_uncertainty = f'{pos_unc:.1f}'
                dec_uncertainty = f'{pos_unc:.1f}'
            except (ValueError, TypeError):
                pass
        
        # Star diameter from occelmnt_data (preferred) or default
        star_diameter = '0'  # mas
        if 'star_diameter_mas' in occelmnt_data and occelmnt_data['star_diameter_mas']:
            try:
                diam = float(occelmnt_data['star_diameter_mas'])
                star_diameter = f'{diam:.2f}'
            except (ValueError, TypeError):
                pass
        
        # Issues flag from occelmnt quality indicators
        issues_flag = '0'  # 0=no issues, 1=high RUWE, 2=duplicate source, 3=both
        try:
            if 'quality_ruwe' in occelmnt_data and occelmnt_data['quality_ruwe']:
                ruwe = float(occelmnt_data['quality_ruwe'])
                if ruwe > 1.4:
                    issues_flag = '1'
            if 'quality_duplicate_source' in occelmnt_data and occelmnt_data['quality_duplicate_source']:
                dup = int(float(occelmnt_data['quality_duplicate_source']))
                if dup == 1:
                    issues_flag = '3' if issues_flag == '1' else '2'
        except (ValueError, TypeError):
            pass
        
        # Apparent RA/Dec from occelmnt_data (different from J2000!)
        # Apparent coordinates: RA has 8 decimals, Dec has 7 decimals
        ra_apparent = None
        dec_apparent = None
        
        if 'star_ra_apparent' in occelmnt_data:
            ra_app_str = str(occelmnt_data['star_ra_apparent']).strip()
            if ra_app_str and ra_app_str != '':
                try:
                    ra_app = float(ra_app_str)
                    ra_apparent = f'{ra_app:.8f}'
                except (ValueError, TypeError):
                    pass
            
        if 'star_dec_apparent' in occelmnt_data:
            dec_app_str = str(occelmnt_data['star_dec_apparent']).strip()
            if dec_app_str and dec_app_str != '':
                try:
                    dec_app = float(dec_app_str)
                    dec_apparent = f'{dec_app:+.7f}'
                except (ValueError, TypeError):
                    pass
        
        # If apparent coordinates not available, fall back to J2000
        if ra_apparent is None:
            ra_apparent = f'{ra_hours:.8f}'  # Fallback to J2000
        if dec_apparent is None:
            dec_apparent = f'{dec_degrees:+.7f}'  # Fallback to J2000
        
        # Magnitudes from occelmnt_data (Mb, Mv, Mr) - format with 2 decimal places
        # Use occelmnt color-specific magnitudes if available
        if 'star_mag_b' in occelmnt_data and occelmnt_data['star_mag_b']:
            try:
                mag_b_val = float(occelmnt_data['star_mag_b'])
                mag_b = f'{mag_b_val:.2f}'
            except (ValueError, TypeError):
                star_mag = event.star_mag if hasattr(event, 'star_mag') else 0.0
                mag_b = f'{star_mag:.2f}'
        else:
            star_mag = event.star_mag if hasattr(event, 'star_mag') else 0.0
            mag_b = f'{star_mag:.2f}'
            
        if 'star_mag_v' in occelmnt_data and occelmnt_data['star_mag_v']:
            try:
                mag_v_val = float(occelmnt_data['star_mag_v'])
                mag_g = f'{mag_v_val:.2f}'  # Mg field uses V magnitude
            except (ValueError, TypeError):
                star_mag = event.star_mag if hasattr(event, 'star_mag') else 0.0
                mag_g = f'{star_mag:.2f}'
        else:
            star_mag = event.star_mag if hasattr(event, 'star_mag') else 0.0
            mag_g = f'{star_mag:.2f}'
            
        if 'star_mag_r' in occelmnt_data and occelmnt_data['star_mag_r']:
            try:
                mag_r_val = float(occelmnt_data['star_mag_r'])
                mag_r = f'{mag_r_val:.2f}'
            except (ValueError, TypeError):
                star_mag = event.star_mag if hasattr(event, 'star_mag') else 0.0
                mag_r = f'{star_mag:.2f}'
        else:
            star_mag = event.star_mag if hasattr(event, 'star_mag') else 0.0
            mag_r = f'{star_mag:.2f}'
        
        # All detail fields left empty — coordinators populate from their data
        star_line = (
            f'           <Star>{star_catalog}|{star_number}||||||||||||||</Star>'
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
        # Get occelmnt_data if available
        occelmnt_data = event.original_data.get('occelmnt_data', {}) if hasattr(event, 'original_data') else {}
        
        # Reliability (RUWE) from occelmnt_data
        reliability = '0'
        if 'quality_ruwe' in occelmnt_data and occelmnt_data['quality_ruwe']:
            try:
                ruwe = float(occelmnt_data['quality_ruwe'])
                reliability = f'{ruwe:.2f}'
            except (ValueError, TypeError):
                pass
        
        # Duplicated source flag from occelmnt_data
        duplicated_flag = '-1'  # -1 = not specified
        if 'quality_duplicate_source' in occelmnt_data and occelmnt_data['quality_duplicate_source']:
            try:
                duplicated_flag = str(int(float(occelmnt_data['quality_duplicate_source'])))
            except (ValueError, TypeError):
                pass
        
        # No proper motion flag from occelmnt_data
        no_proper_motion = '-1'  # -1 = not specified
        if 'quality_no_pm' in occelmnt_data and occelmnt_data['quality_no_pm']:
            try:
                no_proper_motion = str(int(float(occelmnt_data['quality_no_pm'])))
            except (ValueError, TypeError):
                pass
        
        # UCAC4 proper motion flag from occelmnt_data
        ucac4_proper_motion = '0'  # 0 = not applicable
        if 'quality_ucac4_pm' in occelmnt_data and occelmnt_data['quality_ucac4_pm']:
            try:
                ucac4_proper_motion = str(int(float(occelmnt_data['quality_ucac4_pm'])))
            except (ValueError, TypeError):
                pass
        
        # Double star data (defaults if not available)
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
        # Get occelmnt_data if available (preferred source)
        occelmnt_data = event.original_data.get('occelmnt_data', {}) if hasattr(event, 'original_data') else {}
        
        # Asteroid identification - prefer occelmnt_data
        if 'object_number' in occelmnt_data and occelmnt_data['object_number']:
            asteroid_number = str(occelmnt_data['object_number'])
        else:
            asteroid_number = event.object_no if hasattr(event, 'object_no') and event.object_no else ''
            
        if 'object_name' in occelmnt_data and occelmnt_data['object_name']:
            asteroid_name = str(occelmnt_data['object_name'])
        else:
            asteroid_name = event.object_name if hasattr(event, 'object_name') and event.object_name else ''
        
        # Clean asteroid name (remove number if present)
        if asteroid_name:
            import re
            asteroid_name = re.sub(r'^\(\d+\)\s*', '', asteroid_name)
        
        # Motion coefficients from occelmnt_data (Earth radii/hr)
        # These are PREDICTION data from Occult4/Occelmnt
        dx = '0'
        dy = '0'
        d2x = '0'
        d2y = '0'
        d3x = '0'
        d3y = '0'
        
        if 'motion_dx' in occelmnt_data and occelmnt_data['motion_dx']:
            try:
                dx_val = float(occelmnt_data['motion_dx'])
                dx = f'{dx_val:.7f}'  # 7 decimal precision to preserve small coefficients
            except (ValueError, TypeError):
                pass
        if 'motion_dy' in occelmnt_data and occelmnt_data['motion_dy']:
            try:
                dy_val = float(occelmnt_data['motion_dy'])
                dy = f'{dy_val:.7f}'
            except (ValueError, TypeError):
                pass
        if 'motion_d2x' in occelmnt_data and occelmnt_data['motion_d2x']:
            try:
                d2x_val = float(occelmnt_data['motion_d2x'])
                d2x = f'{d2x_val:.7f}'
            except (ValueError, TypeError):
                pass
        if 'motion_d2y' in occelmnt_data and occelmnt_data['motion_d2y']:
            try:
                d2y_val = float(occelmnt_data['motion_d2y'])
                d2y = f'{d2y_val:.7f}'
            except (ValueError, TypeError):
                pass
        if 'motion_d3x' in occelmnt_data and occelmnt_data['motion_d3x']:
            try:
                d3x_val = float(occelmnt_data['motion_d3x'])
                d3x = f'{d3x_val:.7f}'
            except (ValueError, TypeError):
                pass
        if 'motion_d3y' in occelmnt_data and occelmnt_data['motion_d3y']:
            try:
                d3y_val = float(occelmnt_data['motion_d3y'])
                d3y = f'{d3y_val:.7f}'
            except (ValueError, TypeError):
                pass
        
        # Parallax (not available in occelmnt_data)
        parallax = '0'  # arcsec
        d_parallax = '0'  # arcsec/hr
        
        # Diameter from occelmnt_data (preferred)
        diameter = '0'  # km (nominal mean diameter)
        diameter_uncertainty = '0'  # km
        
        if 'object_diameter_km' in occelmnt_data and occelmnt_data['object_diameter_km']:
            try:
                diam = float(occelmnt_data['object_diameter_km'])
                diameter = f'{diam:.1f}'
            except (ValueError, TypeError):
                pass
        if 'object_diameter_uncertainty' in occelmnt_data and occelmnt_data['object_diameter_uncertainty']:
            try:
                diam_unc = float(occelmnt_data['object_diameter_uncertainty'])
                diameter_uncertainty = f'{diam_unc:.1f}'
            except (ValueError, TypeError):
                pass
        
        # Visual magnitude from occelmnt_data: use object_magnitude (object[2] = asteroid apparent V mag).
        # object_mag_v (object[12]) is the negative magnitude drop, not the asteroid magnitude.
        mv = '0'
        if 'object_magnitude' in occelmnt_data and occelmnt_data['object_magnitude']:
            try:
                mv_val = float(occelmnt_data['object_magnitude'])
                if mv_val > 0:  # Asteroid apparent magnitudes are always positive
                    mv = f'{mv_val:.2f}'
            except (ValueError, TypeError):
                pass
        
        # All detail fields left empty — coordinators populate from their data
        asteroid_line = (
            f'           <Asteroid>{asteroid_number}|{asteroid_name}||||||||||</Asteroid>'
        )
        
        return asteroid_line
    
    def _build_prediction_line(self, event):
        """Build the Prediction line with predicted event details"""
        # Sequential reference number
        seq_num = '1'
        
        # Longitude and latitude in DMS format
        longitude = self._format_dms(event.longitude if hasattr(event, 'longitude') else 0, is_longitude=True)
        latitude = self._format_dms(event.latitude if hasattr(event, 'latitude') else 0, is_longitude=False)
        
        # Time - format as single field with Occult 4 spacing: " h  m ss.ss" or " hh  m ss.ss"
        # Example: " 8  2  7.88" (note leading space, double space between parts)
        if hasattr(event, 'event_datetime') and event.event_datetime:
            dt = event.event_datetime
            hour = dt.hour
            minute = dt.minute
            second = dt.second + dt.microsecond/1000000.0
            # Format: H M SS.S - no leading space, single space between parts
            seconds_str = f'{second:.2f}'.rstrip('0').rstrip('.')
            # Ensure at least one decimal place, handle 0 case
            if '.' not in seconds_str or seconds_str == '':
                if seconds_str == '':
                    seconds_str = '0.0'
                else:
                    seconds_str += '.0'
            time_str = f'{hour:d} {minute:d} {seconds_str}'
        else:
            time_str = '0 0 0.0'
        
        # Event comments - use occelmnt ephemeris source if available
        occelmnt_data = event.original_data.get('occelmnt_data', {}) if hasattr(event, 'original_data') else {}
        comments = ''
        if 'event_ephemeris_source' in occelmnt_data and occelmnt_data['event_ephemeris_source']:
            comments = str(occelmnt_data['event_ephemeris_source'])
        
        # Build prediction line - time is single field, then comments
        prediction_line = (
            f'           <Prediction>{seq_num}|{longitude}|{latitude}|{time_str}|{comments}</Prediction>'
        )
        
        return prediction_line
    
    def _format_dms(self, decimal_degrees, is_longitude=True):
        """Convert decimal degrees to DMS format: ±ddd mm ss.s (1 decimal place for seconds)"""
        is_negative = decimal_degrees < 0
        abs_degrees = abs(decimal_degrees)
        
        degrees = int(abs_degrees)
        minutes_decimal = (abs_degrees - degrees) * 60
        minutes = int(minutes_decimal)
        seconds = (minutes_decimal - minutes) * 60
        
        sign = '-' if is_negative else '+'
        
        # Occult 4 format: seconds with 3 decimal places, no fixed width
        # Example: "+174 39 28.440" or "-36 50 7.476"
        if is_longitude:
            return f'{sign}{degrees:03d} {minutes:02d} {seconds:.3f}'
        else:
            return f'{sign}{degrees:02d} {minutes:02d} {seconds:.3f}'
    
    def _build_observer_section(self, event, telescope_id, camera_id, 
                               observation_type, tangra_data, aota_report_data, 
                               observer_data):
        """Build the complete Observer section"""
        lines = []
        lines.append('           <Observer>')
        lines.append(self._build_observer_id_line(event, telescope_id, camera_id, observer_data))
        lines.append(self._build_conditions_line(aota_report_data, observer_data))
        lines.append(self._build_d_event_line(event, observation_type, tangra_data, aota_report_data))
        lines.append(self._build_r_event_line(event, observation_type, tangra_data, aota_report_data))
        lines.append('           </Observer>')
        
        return '\n'.join(lines)
    
    def _build_observer_id_line(self, event, telescope_id, camera_id, observer_data):
        """Build the Observer ID line with equipment and location details"""
        # Sequential reference number
        seq_num = '1'
        
        # Observer names
        observer1 = self._format_observer_name(self.config.get_observer_name() if self.config else '')
        observer2 = ''
        more_than_2 = '0'  # Default to 0, not empty
        
        # Override with observer_data if provided
        if observer_data:
            observer1 = self._format_observer_name(observer_data.get('observer1', observer1))
            observer2 = self._format_observer_name(observer_data.get('observer2', observer2))
            more_than_2_override = observer_data.get('more_than_2', '')
            if more_than_2_override:  # Only use if provided
                more_than_2 = more_than_2_override
        
        # Near location - parse from obs_location, remove country code
        near_location = ''
        if hasattr(event, 'obs_location') and event.obs_location:
            # Remove common country codes like ", NZ" or ", USA"
            loc = event.obs_location
            if ',' in loc:
                near_location = loc.split(',')[0].strip()
            else:
                near_location = loc.strip()
        
        # Override with observer_data if provided and not empty
        if observer_data and observer_data.get('near_location'):
            near_location = observer_data.get('near_location')
        
        # State/country - try to get from obs_location or config
        state_country = ''
        if hasattr(event, 'obs_location') and event.obs_location:
            # Try to extract country from obs_location (e.g., "Auckland, NZ" -> "NZ")
            if ',' in event.obs_location:
                parts = event.obs_location.split(',')
                if len(parts) > 1:
                    state_country = parts[-1].strip()
        
        # Fall back to config
        if not state_country:
            state_country = self.config.get_observer_state() if self.config else ''
        
        # Override with observer_data if provided and not empty
        if observer_data and observer_data.get('state_country'):
            state_country = observer_data.get('state_country')
        
        # Coordinates
        longitude = self._format_dms(event.longitude if hasattr(event, 'longitude') else 0, is_longitude=True)
        latitude = self._format_dms(event.latitude if hasattr(event, 'latitude') else 0, is_longitude=False)
        
        # Altitude
        altitude = int(event.elevation) if hasattr(event, 'elevation') else 0
        
        # Datum
        datum = ' '  # Space for WGS84 (default)
        
        # Telescope aperture and type
        telescope_aperture = ''
        telescope_type = '_'  # unstated
        
        telescope_data = self._get_telescope_data(telescope_id)
        
        if telescope_data:
            aperture = telescope_data.get('aperture', '')
            if aperture:
                try:
                    # Convert from mm to cm and round to integer
                    aperture_cm = int(round(float(aperture) / 10.0))
                    telescope_aperture = str(aperture_cm)
                except Exception as e:
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
        
        # Observing method - read from camera configuration
        camera_data = self._get_camera_data(camera_id)
        observing_method = 'b'  # Digital SLR-camera video (default)
        if camera_data:
            observing_method = camera_data.get('occult4_method', 'b')
        
        # Time source - read from camera configuration
        time_source = 'a'  # GPS (default)
        if camera_data:
            time_source = camera_data.get('occult4_time', 'a')
        # Allow override from observer_data if provided
        if observer_data:
            time_source = observer_data.get('time_source', time_source)
        
        id_line = (
            f'               <ID>{seq_num}|{observer1}|{observer2}|{more_than_2}|{near_location}|'
            f'{state_country}|{longitude}|{latitude}|{altitude}|{datum}|{telescope_aperture}|'
            f'{telescope_type}|{observing_method}|{time_source}</ID>'
        )
        
        return id_line
    
    def _format_observer_name(self, name):
        """Format observer name to OBS.XML 'Initial Surname' format (e.g. 'J Smith')."""
        if not name or not name.strip():
            return name
        parts = name.strip().split()
        if len(parts) == 1:
            return name.strip()
        initial = parts[0][0].upper()
        surname = parts[-1]
        return initial + ' ' + surname

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
    
    def _build_conditions_line(self, aota_report_data, observer_data):
        """Build the Conditions line with observing conditions"""
        # Default values
        stability = '_'  # unstated
        transparency = '_'  # unstated
        sn = ''  # Signal-to-noise ratio
        time_adjustment = ''  # ±s.ss - leave blank; not applicable
        comment = ''
        
        # Get SNR from AOTA report data if available
        if aota_report_data and 'snr' in aota_report_data:
            snr_value = aota_report_data.get('snr')
            if snr_value is not None and float(snr_value) > 0:
                # Cap SNR at maximum value of 20.0 per Occult 4 specification
                snr_value = min(float(snr_value), 20.0)
                # Format to 1 decimal place
                sn = f"{snr_value:.1f}"
        
        # Override with observer_data if provided (observer_data takes precedence)
        if observer_data:
            stability = observer_data.get('stability', stability)
            transparency = observer_data.get('transparency', transparency)
            # Only override SNR if explicitly provided in observer_data
            if 'sn' in observer_data:
                sn = observer_data.get('sn', sn)
            time_adjustment = observer_data.get('time_adjustment', time_adjustment)
            comment = observer_data.get('comment', comment)
            # timing_comment: camera name + timing correction note
            timing_comment = observer_data.get('timing_comment', '')
            if timing_comment:
                comment = timing_comment if not comment else comment + ' ' + timing_comment
        
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
        
        # PEqn (personal equation) - blank; not applicable for GPS/NTP timing
        peqn = ''
        
        # Weight (blank for default)
        weight = ''
        
        # Plot code (blank to include)
        plot_code = ' ' if event_code in ['D', 'd', 'G', 'g'] else 'x'
        
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
        
        # PEqn - blank; not applicable for GPS/NTP timing
        peqn = ''
        
        # Weight
        weight = ''
        
        # Plot code
        plot_code = ' ' if event_code in ['R', 'r', 'B', 'b'] else 'x'
        
        r_line = f'               <R>{time_str}|{event_code}|{accuracy}|{peqn}|{weight}|{plot_code}</R>'
        
        return r_line
    
    def _get_d_time(self, tangra_data, aota_report_data, event):
        """Get disappearance time from available data sources"""
        def _format_hms(hours, minutes, seconds):
            # OBS format: hour is space-padded (right-justified in 2 chars), minutes zero-padded
            return f'{int(hours):2d} {int(minutes):02d} {float(seconds):05.2f}'

        # Try AOTA report data first (has d_hours, d_minutes, d_seconds)
        if aota_report_data and 'd_hours' in aota_report_data:
            hours = int(aota_report_data.get('d_hours', 0))
            minutes = int(aota_report_data.get('d_minutes', 0))
            seconds = float(aota_report_data.get('d_seconds', 0.0))
            return _format_hms(hours, minutes, seconds)
        
        # Tangra data doesn't have d_time - skip it
        # Note: Tangra CSV only has observation start/end times, not event times
        
        # Fall back to event predicted time
        if hasattr(event, 'event_datetime') and event.event_datetime:
            dt = event.event_datetime
            seconds_with_fraction = dt.second + dt.microsecond / 1000000.0
            return _format_hms(dt.hour, dt.minute, seconds_with_fraction)
        
        return ' 0 00 00.00'
    
    def _get_r_time(self, tangra_data, aota_report_data, event):
        """Get reappearance time from available data sources"""
        def _format_hms(hours, minutes, seconds):
            # OBS format: hour is space-padded (right-justified in 2 chars), minutes zero-padded
            return f'{int(hours):2d} {int(minutes):02d} {float(seconds):05.2f}'

        # Try AOTA report data first (has r_hours, r_minutes, r_seconds)
        if aota_report_data and 'r_hours' in aota_report_data:
            hours = int(aota_report_data.get('r_hours', 0))
            minutes = int(aota_report_data.get('r_minutes', 0))
            seconds = float(aota_report_data.get('r_seconds', 0.0))
            return _format_hms(hours, minutes, seconds)
        
        # Tangra data doesn't have r_time - skip it
        # Note: Tangra CSV only has observation start/end times, not event times
        
        # If we have a D time and duration, calculate R time
        if hasattr(event, 'event_datetime') and event.event_datetime and hasattr(event, 'event_duration'):
            dt = event.event_datetime + timedelta(seconds=event.event_duration)
            seconds_with_fraction = dt.second + dt.microsecond / 1000000.0
            return _format_hms(dt.hour, dt.minute, seconds_with_fraction)
        
        return ' 0 00 00.00'
    
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
            except (ValueError, TypeError, KeyError):
                pass
        
        # Try Tangra data
        if tangra_data and 'd_uncertainty' in tangra_data:
            try:
                return f"{float(tangra_data['d_uncertainty']):.2f}"
            except (ValueError, TypeError, KeyError):
                pass
        
        # Default accuracy for video observations
        return '0.5'
