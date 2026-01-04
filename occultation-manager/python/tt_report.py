"""
Trans-Tasman / RASNZ Occultation Report Form Generator (String-based)
Uses simple string replacement in XML to avoid namespace issues

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


class TTReportGenerator(ReportGeneratorBase):
    """Generates Trans-Tasman / RASNZ Occultation Report Forms using placeholder replacement"""
    
    # Use the template version with placeholders (no validation)
    TEMPLATE_FILENAME = 'RASNZ_AstReporttForm_V4.1.2.G_Template.xlsx'
    
    def __init__(self, config):
        """Initialize with configuration manager"""
        super(TTReportGenerator, self).__init__(config)
    
    def get_template_path(self):
        """Get path to local template file bundled with the project"""
        script_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(script_dir, self.TEMPLATE_FILENAME)
    
    def generate_report(self, event, telescope_id=None, camera_id=None, observation_type=None, tangra_data=None, aota_report_data=None):
        """Generate a Trans-Tasman report using string replacement
        
        Args:
            event: Event object with observation details
            telescope_id: ID of telescope to use
            camera_id: ID of camera to use
            observation_type: Type of observation ("Positive", "Negative", "Unsure")
            tangra_data: Optional dictionary with Tangra light curve analysis data
            aota_report_data: Optional dictionary with AOTA Report timing/SNR data
        """
        # Store equipment IDs and observation type
        self._report_telescope_id = telescope_id
        self._report_camera_id = camera_id
        self._observation_type = observation_type or "Positive"
        self._tangra_data = tangra_data
        self._aota_report_data = aota_report_data
        
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
            
            # Build replacements dictionary
            replacements = self._build_replacements(event)
            
            # Generate filename
            event_date_str = event.event_datetime.strftime('%Y%m%d') if hasattr(event, 'event_datetime') else 'unknown'
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
    
    def _build_replacements(self, event):
        """Build dictionary of placeholder -> value replacements"""
        replacements = {}
        
        # Event information
        replacements['{{OBSERVATION_TYPE}}'] = self._observation_type
        
        if hasattr(event, 'event_datetime') and event.event_datetime:
            dt = event.event_datetime
            replacements['{{EVENT_YEAR}}'] = str(dt.year)
            replacements['{{EVENT_MONTH}}'] = self.MONTHS[dt.month - 1]
            replacements['{{EVENT_DAY}}'] = str(dt.day)
            replacements['{{PREDICTED_HOURS}}'] = str(dt.hour)
            replacements['{{PREDICTED_MINUTES}}'] = str(dt.minute)
            replacements['{{PREDICTED_SECONDS}}'] = str(dt.second)
        
        # Asteroid info
        if hasattr(event, 'object_no') and event.object_no:
            replacements['{{ASTEROID_NUMBER}}'] = str(event.object_no)
        
        if hasattr(event, 'object_name') and event.object_name:
            name = event.object_name
            name = re.sub(r'^\(\d+\)\s*', '', name)
            replacements['{{ASTEROID_NAME}}'] = name
        
        # Star catalog and number
        star_name = getattr(event, 'star_name', None) or getattr(event, 'star_id', None)
        if star_name:
            star_catalog, star_number = self.parse_star_catalog(star_name)
            if star_catalog and star_number:
                # Map to TT format
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
                mapped_catalog = catalog_mapping.get(star_catalog, star_catalog)
                mapped_catalog = re.sub(r'^1[A-Z]\s+', '', mapped_catalog).strip()
                replacements['{{STAR_CATALOG}}'] = mapped_catalog
                replacements['{{STAR_NUMBER}}'] = star_number
        
        replacements['{{RIO_TNO_PREDICTION}}'] = 'No'
        
        # Observer information
        observer_name = self.config.get_observer_name()
        if observer_name:
            replacements['{{OBSERVER_NAME}}'] = observer_name
        
        observer_email = self.config.get_observer_email()
        if observer_email:
            replacements['{{OBSERVER_EMAIL}}'] = observer_email
        
        observer_address = self.config.get_observer_address()
        if observer_address:
            replacements['{{OBSERVER_ADDRESS}}'] = observer_address
        
        if hasattr(self.config, 'get_observer_phone'):
            observer_phone = self.config.get_observer_phone()
            if observer_phone:
                replacements['{{OBSERVER_PHONE}}'] = observer_phone
        
        if hasattr(self.config, 'get_observer_fax'):
            observer_fax = self.config.get_observer_fax()
            if observer_fax:
                replacements['{{OBSERVER_FAX}}'] = observer_fax
        
        # City, State, Country
        city = self.config.get_observer_city()
        state = self.config.get_observer_state()
        country = self.config.get_observer_country() if hasattr(self.config, 'get_observer_country') else ''
        
        parts = []
        if city:
            parts.append(city)
        if state:
            parts.append(state)
        if country:
            parts.append(country)
        
        if parts:
            replacements['{{OBSERVER_CITY_STATE_COUNTRY}}'] = ', '.join(parts)
        
        # Observing location
        obs_location = getattr(event, 'obs_location', None)
        if obs_location:
            replacements['{{OBSERVING_LOCATION}}'] = obs_location
        
        # Location coordinates
        station_lat = getattr(event, 'latitude', 0.0)
        station_lon = getattr(event, 'longitude', 0.0)
        station_elev = getattr(event, 'elevation', 0.0)
        
        if station_lat != 0.0:
            lat_str = '{:.5f}'.format(abs(station_lat))
            replacements['{{LATITUDE_FORMAT}}'] = 'deg.ddddd'
            replacements['{{LATITUDE}}'] = lat_str
            replacements['{{LATITUDE_DIR}}'] = 'S' if station_lat < 0 else 'N'
        
        if station_lon != 0.0:
            lon_str = '{:.5f}'.format(abs(station_lon))
            replacements['{{LONGITUDE_FORMAT}}'] = 'deg.ddddd'
            replacements['{{LONGITUDE}}'] = lon_str
            replacements['{{LONGITUDE_DIR}}'] = 'W' if station_lon < 0 else 'E'
        
        if station_elev != 0.0:
            replacements['{{ELEVATION}}'] = str(station_elev)
            replacements['{{ELEVATION_UNITS}}'] = 'm'
            replacements['{{ELEVATION_DATUM}}'] = 'WGS84'
        
        # Telescope
        telescope = self.get_telescope_data(self._report_telescope_id)
        if telescope:
            aperture = telescope.get('aperture', 0)
            if aperture:
                replacements['{{APERTURE}}'] = str(aperture / 10.0)
                replacements['{{APERTURE_UNITS}}'] = 'cm'
            
            focal_ratio = telescope.get('focal_ratio', 0)
            if focal_ratio == 0 and telescope.get('focal_length', 0) > 0 and aperture > 0:
                focal_ratio = telescope.get('focal_length') / aperture
            if focal_ratio > 0:
                fr_str = '{:.1f}'.format(focal_ratio)
                replacements['{{FOCAL_RATIO}}'] = fr_str
            
            telescope_type = telescope.get('type', '')
            if telescope_type:
                replacements['{{TELESCOPE_TYPE}}'] = telescope_type
        
        # Timing observations - use Tangra data if available
        if self._tangra_data:
            # Parse start time from Tangra data (format: "HH:MM:SS.ffffff")
            start_time_str = self._tangra_data.get('start_time', '')
            if start_time_str:
                try:
                    from datetime import datetime
                    # Parse the time string
                    time_parts = start_time_str.split(':')
                    if len(time_parts) >= 3:
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        seconds_parts = time_parts[2].split('.')
                        seconds = int(seconds_parts[0])
                        # Get fractional seconds
                        if len(seconds_parts) > 1:
                            frac = float('0.' + seconds_parts[1])
                            seconds_decimal = seconds + frac
                        else:
                            seconds_decimal = float(seconds)
                        
                        replacements['{{STARTED_OBSERVING_HOURS}}'] = str(hours)
                        replacements['{{STARTED_OBSERVING_MINUTES}}'] = str(minutes)
                        replacements['{{STARTED_OBSERVING_SECONDS}}'] = '{:.2f}'.format(seconds_decimal)
                except Exception as ex:
                    print(f"Warning: Could not parse Tangra start time: {ex}")
            
            # Parse end time from Tangra data
            end_time_str = self._tangra_data.get('end_time', '')
            if end_time_str:
                try:
                    time_parts = end_time_str.split(':')
                    if len(time_parts) >= 3:
                        hours = int(time_parts[0])
                        minutes = int(time_parts[1])
                        seconds_parts = time_parts[2].split('.')
                        seconds = int(seconds_parts[0])
                        # Get fractional seconds
                        if len(seconds_parts) > 1:
                            frac = float('0.' + seconds_parts[1])
                            seconds_decimal = seconds + frac
                        else:
                            seconds_decimal = float(seconds)
                        
                        replacements['{{STOPPED_OBSERVING_HOURS}}'] = str(hours)
                        replacements['{{STOPPED_OBSERVING_MINUTES}}'] = str(minutes)
                        replacements['{{STOPPED_OBSERVING_SECONDS}}'] = '{:.2f}'.format(seconds_decimal)
                except Exception as ex:
                    print(f"Warning: Could not parse Tangra end time: {ex}")
        elif hasattr(event, 'start_time') and event.start_time:
            # Fallback to event start_time if no Tangra data
            replacements['{{STARTED_OBSERVING_HOURS}}'] = str(event.start_time.hour)
        
        if hasattr(event, 'end_time') and event.end_time and not self._tangra_data:
            # Fallback to event end_time if no Tangra data
            replacements['{{STOPPED_OBSERVING_HOURS}}'] = str(event.end_time.hour)
        
        # Camera/detector info
        camera = self.get_camera_data(self._report_camera_id)
        if camera:
            timing = camera.get('timing_tt', camera.get('timing', 'GPS - other linking'))
            if timing:
                replacements['{{TIMING}}'] = timing
            
            timing_device = camera.get('timing_device_tt', camera.get('timing_device', 'SharpCap'))
            if timing_device:
                replacements['{{TIMING_DEVICE}}'] = timing_device
            
            detector = camera.get('detector', 'SharpCap')
            if detector:
                replacements['{{DETECTOR}}'] = detector
            
            video_format = camera.get('video_format', 'SER')
            if video_format:
                replacements['{{VIDEO_FORMAT}}'] = video_format
            
            # Integration time from Tangra data if available
            if self._tangra_data and 'tdelta_median' in self._tangra_data:
                # Convert ms to seconds with 3 decimal places
                exposure_ms = self._tangra_data['tdelta_median']
                exposure_sec = exposure_ms / 1000.0
                replacements['{{INTEGRATION}}'] = '{:.3f}'.format(exposure_sec)
                replacements['{{INTEGRATION_UNITS}}'] = 'Seconds'
            else:
                # Fallback to camera settings
                exposure_integration = camera.get('exposure_integration', 'Other')
                if exposure_integration:
                    replacements['{{INTEGRATION}}'] = exposure_integration
                    replacements['{{INTEGRATION_UNITS}}'] = 'Frames'
            
            other_info = camera.get('other_info', '')
            if other_info:
                replacements['{{COMMENTS}}'] = other_info
                # Also populate detector-related info with the same data
                replacements['{{OTHER_DETECTOR_RELATED_INFO}}'] = other_info
        
        # Camera delay correction from Tangra data
        if self._tangra_data and 'acquisition_delay' in self._tangra_data:
            # Use acquisition delay from Tangra (in ms, convert to seconds)
            delay_ms = self._tangra_data['acquisition_delay']
            delay_sec = delay_ms / 1000.0
            replacements['{{CAMERA_DELAY_CORRECTION}}'] = '{:.3f}'.format(delay_sec)
            replacements['{{CORRECTIONS_APPLIED}}'] = 'yes'
        else:
            replacements['{{CORRECTIONS_APPLIED}}'] = 'No'
        
        # Default values
        replacements['{{TIMING_METHOD}}'] = 'Video Recording'
        replacements['{{ASTEROID_VISIBLE}}'] = 'Yes'
        
        # Set WAS_MISS based on observation type (inverse relationship)
        # Positive = saw occultation = NOT a miss
        # Negative = didn't see occultation = WAS a miss
        if self._observation_type == 'Positive':
            replacements['{{WAS_MISS}}'] = 'no'
        elif self._observation_type == 'Negative':
            replacements['{{WAS_MISS}}'] = 'yes'
        elif self._observation_type == 'Unsure':
            replacements['{{WAS_MISS}}'] = 'maybe'
        else:
            replacements['{{WAS_MISS}}'] = 'maybe'  # Default fallback
        
        replacements['{{SECOND_STAR}}'] = 'No'
        
        # NOTE: AOTA TIMING DATA placeholders are NOT initialized here.
        # They remain in the template as {{AOTA_D_HOURS}} etc. so that
        # _add_aota_to_existing_report() can find and replace them later.
        
        # Ensure all placeholders have values (empty string if no data)
        all_placeholders = [
            '{{OBSERVATION_TYPE}}', '{{EVENT_YEAR}}', '{{EVENT_MONTH}}', '{{EVENT_DAY}}',
            '{{PREDICTED_HOURS}}', '{{PREDICTED_MINUTES}}', '{{PREDICTED_SECONDS}}',
            '{{ASTEROID_NUMBER}}', '{{ASTEROID_NAME}}', '{{STAR_CATALOG}}', '{{STAR_NUMBER}}',
            '{{RIO_TNO_PREDICTION}}', '{{OBSERVER_NAME}}', '{{OBSERVER_EMAIL}}',
            '{{OBSERVER_ADDRESS}}', '{{OBSERVER_PHONE}}', '{{OBSERVER_FAX}}',
            '{{OBSERVER_CITY_STATE_COUNTRY}}', '{{OBSERVING_LOCATION}}',
            '{{LATITUDE_FORMAT}}', '{{LATITUDE}}', '{{LATITUDE_DIR}}',
            '{{LONGITUDE_FORMAT}}', '{{LONGITUDE}}', '{{LONGITUDE_DIR}}',
            '{{ELEVATION}}', '{{ELEVATION_UNITS}}', '{{ELEVATION_DATUM}}',
            '{{APERTURE}}', '{{APERTURE_UNITS}}', '{{FOCAL_RATIO}}', '{{TELESCOPE_TYPE}}',
            '{{STARTED_OBSERVING_HOURS}}', '{{STARTED_OBSERVING_MINUTES}}', '{{STARTED_OBSERVING_SECONDS}}',
            '{{STOPPED_OBSERVING_HOURS}}', '{{STOPPED_OBSERVING_MINUTES}}', '{{STOPPED_OBSERVING_SECONDS}}',
            '{{TIMING}}', '{{TIMING_DEVICE}}', '{{DETECTOR}}', '{{VIDEO_FORMAT}}',
            '{{INTEGRATION}}', '{{INTEGRATION_UNITS}}', '{{COMMENTS}}',
            '{{TIMING_METHOD}}', '{{ASTEROID_VISIBLE}}', '{{WAS_MISS}}',
            '{{SECOND_STAR}}', '{{CORRECTIONS_APPLIED}}',
            '{{CAMERA_DELAY_CORRECTION}}', '{{VTI_CORRECTION}}',
            '{{SNR}}', '{{OTHER_DETECTOR_RELATED_INFO}}'
            # AOTA placeholders excluded - handled by post-processing
        ]
        for placeholder in all_placeholders:
            if placeholder not in replacements:
                replacements[placeholder] = ''
        
        # AOTA REPORT TIMING DATA - populate if available
        if self._aota_report_data:
            self.import_aota_report_data(self._aota_report_data, replacements)
        
        return replacements
    
    def import_aota_data(self, aota_event, replacements):
        """Import timing data from AOTA event into replacements dictionary
        
        Args:
            aota_event: AOTAEvent object from aota_parser
            replacements: Dictionary of placeholders to update
        """
        if not aota_event:
            return
        
        # Import formatting functions
        from aota_parser import format_aota_time_component, format_aota_error
        
        # Update D (disappearance) times - use string representations to preserve precision
        if aota_event.d_hours is not None:
            replacements['{{AOTA_D_HOURS}}'] = format_aota_time_component(hours=aota_event.d_hours)
            replacements['{{AOTA_D_MINUTES}}'] = format_aota_time_component(minutes=aota_event.d_minutes)
            replacements['{{AOTA_D_SECONDS}}'] = format_aota_time_component(seconds=aota_event.d_seconds, seconds_str=aota_event.d_seconds_str)
            replacements['{{AOTA_D_ERROR}}'] = format_aota_error(aota_event.d_error, aota_event.d_error_str)
        
        # Update R (reappearance) times - use string representations to preserve precision
        if aota_event.r_hours is not None:
            replacements['{{AOTA_R_HOURS}}'] = format_aota_time_component(hours=aota_event.r_hours)
            replacements['{{AOTA_R_MINUTES}}'] = format_aota_time_component(minutes=aota_event.r_minutes)
            replacements['{{AOTA_R_SECONDS}}'] = format_aota_time_component(seconds=aota_event.r_seconds, seconds_str=aota_event.r_seconds_str)
            replacements['{{AOTA_R_ERROR}}'] = format_aota_error(aota_event.r_error, aota_event.r_error_str)
        
        print(f"AOTA data imported: D={aota_event.d_hours}:{aota_event.d_minutes}:{aota_event.d_seconds_str}, R={aota_event.r_hours}:{aota_event.r_minutes}:{aota_event.r_seconds_str}")
    
    def import_aota_report_data(self, aota_report_summary, replacements):
        """Import timing and SNR data from AOTA Report into replacements dictionary
        
        Args:
            aota_report_summary: Dictionary from aota_report_parser.get_event_summary()
            replacements: Dictionary of placeholders to update
        """
        if not aota_report_summary:
            return
        
        # Update D (disappearance) times - check all components exist and are non-empty
        d_hours = aota_report_summary.get('d_hours')
        d_minutes = aota_report_summary.get('d_minutes')
        d_seconds = aota_report_summary.get('d_seconds')
        
        if d_hours and d_minutes and d_seconds:
            replacements['{{AOTA_D_HOURS}}'] = str(d_hours)
            replacements['{{AOTA_D_MINUTES}}'] = str(d_minutes)
            replacements['{{AOTA_D_SECONDS}}'] = str(d_seconds)
            # Populate error/uncertainty if available
            d_uncertainty = aota_report_summary.get('d_uncertainty')
            if d_uncertainty is not None:
                try:
                    replacements['{{AOTA_D_ERROR}}'] = f"{float(d_uncertainty):.1f}"
                except (ValueError, TypeError):
                    print(f"Warning: Could not format d_uncertainty: {d_uncertainty}")
        
        # Update R (reappearance) times - check all components exist and are non-empty
        r_hours = aota_report_summary.get('r_hours')
        r_minutes = aota_report_summary.get('r_minutes')
        r_seconds = aota_report_summary.get('r_seconds')
        
        if r_hours and r_minutes and r_seconds:
            replacements['{{AOTA_R_HOURS}}'] = str(r_hours)
            replacements['{{AOTA_R_MINUTES}}'] = str(r_minutes)
            replacements['{{AOTA_R_SECONDS}}'] = str(r_seconds)
            # Populate error/uncertainty if available
            r_uncertainty = aota_report_summary.get('r_uncertainty')
            if r_uncertainty is not None:
                try:
                    replacements['{{AOTA_R_ERROR}}'] = f"{float(r_uncertainty):.1f}"
                except (ValueError, TypeError):
                    print(f"Warning: Could not format r_uncertainty: {r_uncertainty}")
        
        # Update SNR if available and placeholder exists
        snr = aota_report_summary.get('snr')
        if snr is not None:
            # Format SNR to 1 decimal place
            replacements['{{SNR}}'] = f"{snr:.1f}"
        
        print(f"AOTA Report data imported: D={d_hours}:{d_minutes}:{d_seconds}, R={r_hours}:{r_minutes}:{r_seconds}, SNR={snr}")

    
    def _create_report_with_replacements(self, template_path, output_path, replacements):
        """Create report by replacing placeholders in the template"""
        # Create temporary file
        temp_file = NamedTemporaryFile(delete=False, suffix='.xlsx')
        temp_path = temp_file.name
        temp_file.close()
        
        # Find which XML file corresponds to the DATA sheet
        data_sheet_path = None
        try:
            with zipfile.ZipFile(template_path, 'r') as zf:
                # Read workbook.xml to find sheet relationships
                wb_xml = zf.read('xl/workbook.xml').decode('utf-8')
                wb_root = ET.fromstring(wb_xml)
                
                # Read workbook.xml.rels to map relationship IDs to file paths
                rels_xml = zf.read('xl/_rels/workbook.xml.rels').decode('utf-8')
                rels_root = ET.fromstring(rels_xml)
                
                # Find the sheet named "DATA"
                for sheet_elem in wb_root.iter():
                    if sheet_elem.tag.endswith('sheet') and sheet_elem.get('name') == 'DATA':
                        rid = sheet_elem.get('{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id')
                        
                        # Find the corresponding file path from relationships
                        for rel in rels_root.iter():
                            if rel.tag.endswith('Relationship') and rel.get('Id') == rid:
                                target = rel.get('Target')
                                data_sheet_path = f'xl/{target}'
                                break
                        break
                
                if not data_sheet_path:
                    # Fallback to sheet1.xml if DATA sheet not found
                    data_sheet_path = 'xl/worksheets/sheet1.xml'
        except Exception as ex:
            data_sheet_path = 'xl/worksheets/sheet1.xml'
        
        try:
            # Open template and create new workbook
            with zipfile.ZipFile(template_path, 'r') as template_zip:
                with zipfile.ZipFile(temp_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                    # Process each file in the template
                    for item in template_zip.namelist():
                        # Skip calcChain to avoid issues
                        if item == 'xl/calcChain.xml':
                            continue
                        
                        data = template_zip.read(item)
                        
                        # Process SHARED STRINGS (where Excel stores text)
                        if item == 'xl/sharedStrings.xml':
                            # Parse the XML properly instead of string replacement
                            try:
                                root = ET.fromstring(data)
                                
                                # Find all <t> elements (text nodes in shared strings)
                                for t_elem in root.iter():
                                    if t_elem.tag.endswith('}t') or t_elem.tag == 't':
                                        if t_elem.text:
                                            original_text = t_elem.text
                                            modified_text = original_text
                                            
                                            # Replace all placeholders in this text node
                                            for placeholder, value in replacements.items():
                                                if placeholder in modified_text:
                                                    safe_value = str(value) if value else ''
                                                    modified_text = modified_text.replace(placeholder, safe_value)
                                            
                                            # Update the text if it changed
                                            if modified_text != original_text:
                                                t_elem.text = modified_text
                                
                                # Serialize back to XML with proper formatting
                                xml_bytes = ET.tostring(root, encoding='utf-8')
                                xml_str = xml_bytes.decode('utf-8')
                                
                                # Write with XML declaration
                                final_xml = '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n' + xml_str
                                new_zip.writestr(item, final_xml.encode('utf-8'))
                                
                            except Exception as ex:
                                # If parsing fails, fall back to copying original
                                print(f"Warning: Could not process sharedStrings.xml: {str(ex)}")
                                new_zip.writestr(item, data)
                        
                        # Process DATA sheet XML (find by name, not hardcoded sheet1.xml)
                        elif item == data_sheet_path:
                            # Convert to string
                            xml_str = data.decode('utf-8')
                            
                            # Replace all placeholders
                            for placeholder, value in replacements.items():
                                # Replace even if empty (to clear placeholder)
                                # Escape XML special characters in the value
                                safe_value = xml_escape(str(value)) if value else ''
                                xml_str = xml_str.replace(placeholder, safe_value)
                            
                            # Write modified data
                            new_zip.writestr(item, xml_str.encode('utf-8'))
                        else:
                            # Copy other files as-is
                            new_zip.writestr(item, data)
            
            # Move to final location
            if os.path.exists(output_path):
                os.remove(output_path)
            shutil.move(temp_path, output_path)
            
        except Exception as ex:
            # Clean up temp file on any error
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except:
                pass  # Ignore cleanup errors
            raise
    

    def _generate_filename(self, event, event_date_str):
        """Generate TT report filename"""
        # Get observer last name
        observer_surname = self.config.get_observer_name().split()[-1] if self.config.get_observer_name() else 'Observer'
        
        # Get asteroid number
        asteroid_number = str(event.object_no) if hasattr(event, 'object_no') and event.object_no else 'Unknown'
        
        # Get asteroid name
        if hasattr(event, 'object_name') and event.object_name:
            asteroid_name = event.object_name
            asteroid_name = re.sub(r'^\(\d+\)\s*', '', asteroid_name).strip()
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
                    star_catalog = re.sub(r'^1[A-Z]\s+', '', parsed_catalog).strip()
                
                star_number = parsed_number.replace('-', '_')
        
        # Result sign based on observation type
        if self._observation_type == 'Positive':
            result_sign = '+'
        else:
            result_sign = '-'  # Negative or Unsure
        
        # Station name
        station_name = ''
        if hasattr(event, 'station_name') and event.station_name:
            station_name_raw = event.station_name
            # Remove observer surname prefix if present
            if station_name_raw.startswith(observer_surname + ' '):
                station_name_raw = station_name_raw[len(observer_surname)+1:]
            # Remove PC/machine name suffix
            if '-' in station_name_raw:
                parts = station_name_raw.split('-')
                station_name_raw = parts[0].strip()
            # Format for filename
            station_name = '_' + station_name_raw.replace(' ', '_').replace(',', '_')
        
        # Build filename
        filename = f"{event_date_str}_{asteroid_number}_{asteroid_name}_{star_catalog}_{star_number}{result_sign}{observer_surname}{station_name}.xlsx"
        return filename
    
    def check_template_exists(self):
        """Check if template file exists"""
        template_path = self.get_template_path()
        if os.path.exists(template_path):
            return True, "Template found"
        else:
            return False, f"Template not found: {template_path}\n\nPlease ensure the template file exists in the same folder as this script."
