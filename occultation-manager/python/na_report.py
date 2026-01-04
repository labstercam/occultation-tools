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
    
    def generate_report(self, event, telescope_id=None, camera_id=None, observation_type=None, tangra_data=None, aota_report_data=None):
        """Generate a North American report using placeholder replacement
        
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
    
    def _build_replacements(self, event):
        """Build dictionary of placeholder -> value replacements"""
        replacements = {}
        
        # OBSERVATION TYPE
        replacements['{{OBSERVATION_TYPE}}'] = self._observation_type
        
        # EVENT INFORMATION
        # Asteroid number and name
        if hasattr(event, 'object_no') and event.object_no:
            replacements['{{ASTEROID_NUMBER}}'] = str(event.object_no)
        else:
            replacements['{{ASTEROID_NUMBER}}'] = ''
        
        if hasattr(event, 'object_name') and event.object_name:
            name = event.object_name
            name = re.sub(r'^\(\d+\)\s*', '', name)
            replacements['{{ASTEROID_NAME}}'] = name
        else:
            replacements['{{ASTEROID_NAME}}'] = ''
        
        # Event date/time
        if hasattr(event, 'event_datetime') and event.event_datetime:
            dt = event.event_datetime
            replacements['{{EVENT_YEAR}}'] = str(dt.year)
            replacements['{{EVENT_MONTH}}'] = self.MONTHS[dt.month - 1]
            replacements['{{EVENT_DAY}}'] = str(dt.day)
            replacements['{{PREDICTED_HOURS}}'] = str(dt.hour)
            replacements['{{PREDICTED_MINUTES}}'] = str(dt.minute)
            replacements['{{PREDICTED_SECONDS}}'] = str(dt.second)
        else:
            replacements['{{EVENT_YEAR}}'] = ''
            replacements['{{EVENT_MONTH}}'] = ''
            replacements['{{EVENT_DAY}}'] = ''
            replacements['{{PREDICTED_HOURS}}'] = ''
            replacements['{{PREDICTED_MINUTES}}'] = ''
            replacements['{{PREDICTED_SECONDS}}'] = ''
        
        # Star catalog and number
        star_name = getattr(event, 'star_name', None) or getattr(event, 'star_id', None)
        if star_name:
            star_catalog, star_number = self.parse_star_catalog(star_name)
            if star_catalog:
                # Strip the '1X    ' prefix (e.g., '1U    UCAC4' -> 'UCAC4')
                star_catalog = re.sub(r'^1[A-Z]\s+', '', star_catalog).strip()
            replacements['{{STAR_CATALOG}}'] = star_catalog if star_catalog else ''
            replacements['{{STAR_NUMBER}}'] = star_number if star_number else ''
        else:
            replacements['{{STAR_CATALOG}}'] = ''
            replacements['{{STAR_NUMBER}}'] = ''
        
        # OBSERVER INFORMATION
        # Observing location
        obs_location = getattr(event, 'obs_location', '')
        replacements['{{OBSERVING_LOCATION}}'] = obs_location if obs_location else ''
        
        # Observer name and email
        observer_name = self.config.get_observer_name()
        observer_email = self.config.get_observer_email()
        replacements['{{OBSERVER_NAME}}'] = observer_name if observer_name else ''
        replacements['{{OBSERVER_EMAIL}}'] = observer_email if observer_email else ''
        
        # Observer mailing address
        observer_address = self.config.get_observer_address()
        observer_phone = self.config.get_observer_phone()
        observer_fax = self.config.get_observer_fax()
        replacements['{{OBSERVER_ADDRESS}}'] = observer_address if observer_address else ''
        replacements['{{OBSERVER_PHONE}}'] = observer_phone if observer_phone else ''
        replacements['{{OBSERVER_FAX}}'] = observer_fax if observer_fax else ''
        
        # City, state, country
        observer_city = self.config.get_observer_city()
        observer_state = self.config.get_observer_state()
        observer_country = self.config.get_observer_country()
        city_state_country_parts = []
        if observer_city:
            city_state_country_parts.append(observer_city)
        if observer_state:
            city_state_country_parts.append(observer_state)
        if observer_country:
            city_state_country_parts.append(observer_country)
        replacements['{{OBSERVER_CITY_STATE_COUNTRY}}'] = ', '.join(city_state_country_parts) if city_state_country_parts else ''
        
        # LOCATION COORDINATES
        station_lat = getattr(event, 'latitude', 0.0)
        station_lon = getattr(event, 'longitude', 0.0)
        station_elev = getattr(event, 'elevation', 0.0)
        
        replacements['{{LATITUDE_FORMAT}}'] = 'deg.ddddd' if station_lat != 0.0 else ''
        replacements['{{LONGITUDE_FORMAT}}'] = 'deg.ddddd' if station_lon != 0.0 else ''
        
        if station_lat != 0.0:
            replacements['{{LATITUDE}}'] = '{:.5f}'.format(abs(station_lat))
            replacements['{{LATITUDE_DIR}}'] = 'S' if station_lat < 0 else 'N'
        else:
            replacements['{{LATITUDE}}'] = ''
            replacements['{{LATITUDE_DIR}}'] = ''
        
        if station_lon != 0.0:
            replacements['{{LONGITUDE}}'] = '{:.5f}'.format(abs(station_lon))
            replacements['{{LONGITUDE_DIR}}'] = 'W' if station_lon < 0 else 'E'
        else:
            replacements['{{LONGITUDE}}'] = ''
            replacements['{{LONGITUDE_DIR}}'] = ''
        
        if station_elev != 0.0:
            replacements['{{ELEVATION}}'] = str(station_elev)
            replacements['{{ELEVATION_UNITS}}'] = 'm'
            replacements['{{ELEVATION_DATUM}}'] = 'WGS84'
        else:
            replacements['{{ELEVATION}}'] = ''
            replacements['{{ELEVATION_UNITS}}'] = ''
            replacements['{{ELEVATION_DATUM}}'] = ''
        
        # TELESCOPE INFORMATION
        telescope_data = self.get_telescope_data(self._report_telescope_id)
        if telescope_data:
            aperture = telescope_data.get('aperture', 0)
            focal_ratio = telescope_data.get('focal_ratio', 0)
            telescope_type = telescope_data.get('type', '')
            telescope_name = telescope_data.get('name', '')
            
            if aperture > 0:
                replacements['{{APERTURE}}'] = '{:.1f}'.format(aperture / 10.0)  # Convert mm to cm
                replacements['{{APERTURE_UNITS}}'] = 'cm'
            else:
                replacements['{{APERTURE}}'] = ''
                replacements['{{APERTURE_UNITS}}'] = ''
            
            if focal_ratio > 0:
                replacements['{{FOCAL_RATIO}}'] = '{:.1f}'.format(focal_ratio)
            else:
                replacements['{{FOCAL_RATIO}}'] = ''
            
            replacements['{{TELESCOPE_TYPE}}'] = telescope_type if telescope_type else ''
            self._telescope_name = telescope_name
        else:
            replacements['{{APERTURE}}'] = ''
            replacements['{{APERTURE_UNITS}}'] = ''
            replacements['{{FOCAL_RATIO}}'] = ''
            replacements['{{TELESCOPE_TYPE}}'] = ''
            self._telescope_name = ''
        
        # RECORDING TIMES - use Tangra data if available
        if self._tangra_data:
            # Parse start time from Tangra data (format: "HH:MM:SS.ffffff")
            start_time_str = self._tangra_data.get('start_time', '')
            if start_time_str:
                try:
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
                    replacements['{{STARTED_OBSERVING_HOURS}}'] = ''
                    replacements['{{STARTED_OBSERVING_MINUTES}}'] = ''
                    replacements['{{STARTED_OBSERVING_SECONDS}}'] = ''
            
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
                    replacements['{{STOPPED_OBSERVING_HOURS}}'] = ''
                    replacements['{{STOPPED_OBSERVING_MINUTES}}'] = ''
                    replacements['{{STOPPED_OBSERVING_SECONDS}}'] = ''
        elif hasattr(event, 'start_time') and event.start_time:
            # Fallback to event start_time if no Tangra data
            replacements['{{STARTED_OBSERVING_HOURS}}'] = str(event.start_time.hour)
            replacements['{{STARTED_OBSERVING_MINUTES}}'] = str(event.start_time.minute)
            replacements['{{STARTED_OBSERVING_SECONDS}}'] = str(event.start_time.second)
        else:
            replacements['{{STARTED_OBSERVING_HOURS}}'] = ''
            replacements['{{STARTED_OBSERVING_MINUTES}}'] = ''
            replacements['{{STARTED_OBSERVING_SECONDS}}'] = ''
        
        if hasattr(event, 'end_time') and event.end_time and not self._tangra_data:
            # Fallback to event end_time if no Tangra data
            replacements['{{STOPPED_OBSERVING_HOURS}}'] = str(event.end_time.hour)
            replacements['{{STOPPED_OBSERVING_MINUTES}}'] = str(event.end_time.minute)
            replacements['{{STOPPED_OBSERVING_SECONDS}}'] = str(event.end_time.second)
        elif not self._tangra_data:
            replacements['{{STOPPED_OBSERVING_HOURS}}'] = ''
            replacements['{{STOPPED_OBSERVING_MINUTES}}'] = ''
            replacements['{{STOPPED_OBSERVING_SECONDS}}'] = ''
        
        # CAMERA/DETECTOR INFORMATION
        camera_data = self.get_camera_data(self._report_camera_id)
        if camera_data:
            timing = camera_data.get('timing', 'GPS - other linking')
            timing_device = camera_data.get('timing_device', 'SharpCap')
            detector = camera_data.get('detector', 'SharpCap')
            other_info = camera_data.get('other_info', '')
            video_format = camera_data.get('video_format', 'SER')
            exposure_integration = camera_data.get('exposure_integration', 'Other')
            camera_name = camera_data.get('name', '')
        else:
            timing = 'GPS - other linking'
            timing_device = 'SharpCap'
            detector = 'SharpCap'
            other_info = 'SharpCap'
            video_format = 'SER'
            exposure_integration = 'Other'
            camera_name = ''
        
        replacements['{{TIMING}}'] = timing
        replacements['{{TIMING_DEVICE}}'] = timing_device
        replacements['{{DETECTOR}}'] = detector
        
        # Other detector info (include exposure if available)
        detector_info = other_info
        
        # Use Tangra data for exposure if available
        if self._tangra_data and 'tdelta_median' in self._tangra_data:
            exposure_ms = self._tangra_data['tdelta_median']
            if detector_info:
                detector_info += f' | Exp {exposure_ms:.3f}ms'
            else:
                detector_info = f'Exp {exposure_ms:.3f}ms'
        elif hasattr(event, 'exposure_ms') and event.exposure_ms:
            if detector_info:
                detector_info += f' | Exp {event.exposure_ms}ms'
            else:
                detector_info = f'Exp {event.exposure_ms}ms'
        
        replacements['{{OTHER_DETECTOR_INFO}}'] = detector_info if detector_info else ''
        
        replacements['{{VIDEO_FORMAT}}'] = video_format
        replacements['{{EXPOSURE_INTEGRATION}}'] = exposure_integration
        
        # ADDITIONAL FIELDS
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
        
        # COMMENTS
        comment_parts = []
        if self._telescope_name:
            comment_parts.append(f"Telescope: {self._telescope_name}")
        if camera_name:
            comment_parts.append(f"Camera: {camera_name}")
        
        replacements['{{COMMENT_LINE1}}'] = ' | '.join(comment_parts) if comment_parts else ''
        replacements['{{COMMENT_LINE2}}'] = ''
        replacements['{{COMMENT_LINE3}}'] = 'This report was pre-filled by Occultation Manager'
        
        # AOTA TIMING DATA - NOT initialized here
        # These placeholders remain in the template so post-processing can replace them
        # when AOTA data is imported via _add_aota_to_existing_report()
        
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
        """Create report by replacing placeholders in template"""
        # Create temporary file
        temp_fd, temp_path = NamedTemporaryFile(delete=False, suffix='.xlsx').name, NamedTemporaryFile(delete=False, suffix='.xlsx').name
        
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
                        data = template_zip.read(item)
                        
                        # Process sharedStrings.xml (where cell text is stored)
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
        """Generate NA report filename: YYYYMMDD_###_Asteroid name_Last name_POS/NEG.xlsx"""
        # Get asteroid number
        asteroid_number = str(event.object_no) if hasattr(event, 'object_no') and event.object_no else 'Unknown'
        
        # Get asteroid name
        if hasattr(event, 'object_name') and event.object_name:
            asteroid_name = event.object_name
            asteroid_name = re.sub(r'^\(\d+\)\s*', '', asteroid_name).strip()
            asteroid_name = asteroid_name.replace(' ', '_')
        else:
            asteroid_name = 'Unknown'
        
        # Get observer surname
        observer_surname = self.config.get_observer_name().split()[-1] if self.config.get_observer_name() else 'Observer'
        
        # Result indicator based on observation type
        if self._observation_type == 'Positive':
            result_indicator = 'POS'
        else:
            result_indicator = 'NEG'  # Negative or Unsure
        
        # NA format: YYYYMMDD_###_Asteroid_name_Surname_POS/NEG.xlsx
        filename = f"{event_date_str}_{asteroid_number}_{asteroid_name}_{observer_surname}_{result_indicator}.xlsx"
        
        return filename
