"""
North American Occultation Report Form Generator (Openize SDK)
Uses Openize.OpenXML-SDK for direct Excel manipulation

This version directly populates Excel cells using the .NET Openize SDK via IronPython,
avoiding manual XML manipulation and preserving all Excel formatting, formulas, and data validation.
"""

import clr
import os
import sys
import re
from datetime import datetime

# Add reference to Openize DLL
lib_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'lib')
if os.path.exists(lib_path):
    sys.path.append(lib_path)

try:
    # Load the required .NET assemblies
    clr.AddReference('Openize.OpenXMLSDK')
    clr.AddReference('DocumentFormat.OpenXml')
    
    # Import Openize namespaces
    from Openize.Cells import Workbook, Worksheet
    
    OPENIZE_AVAILABLE = True
except Exception as ex:
    print(f"Warning: Openize SDK not available: {ex}")
    print(f"DLL search path: {lib_path}")
    OPENIZE_AVAILABLE = False

from report_generator_base import ReportGeneratorBase


class NAReportGeneratorOpenize(ReportGeneratorBase):
    """
    Generates North American Occultation Report Forms using Openize SDK
    
    This implementation uses direct Excel cell manipulation via the Openize.OpenXML-SDK .NET library.
    
    Benefits:
    - Preserves Excel data validation
    - Preserves formulas and formatting
    - More reliable than XML string replacement
    - Cleaner code with direct cell access
    """
    
    # Use original template with data validation enabled
    TEMPLATE_FILENAME = 'NorthAmerica_AstReportForm_V5.6.12r.xlsx'
    
    def __init__(self, config):
        """Initialize with configuration manager"""
        super(NAReportGeneratorOpenize, self).__init__(config)
        
        print("\n" + "="*70)
        print("*** OPENIZE VERSION LOADED - Using na_report_openize.py ***")
        print("Template: NorthAmerica_AstReportForm_V5.6.12r.xlsx")
        print("="*70 + "\n")
        
        if not OPENIZE_AVAILABLE:
            raise RuntimeError("Openize SDK is not available. Please install the DLL to lib folder.")
    
    def get_template_path(self):
        """Get path to original template file with data validation"""
        return os.path.join(self.config.get_templates_master_reports_folder(), self.TEMPLATE_FILENAME)
    
    def generate_report(self, event, telescope_id=None, camera_id=None, observation_type=None, 
                       tangra_data=None, aota_report_data=None, aota_xml_used=False,
                       clouds=None, stability=None, other_conditions=None):
        """Generate a North American report using Openize SDK
        
        Args:
            event: Event object with observation details
            telescope_id: ID of telescope to use
            camera_id: ID of camera to use
            observation_type: Type of observation ("Positive", "Negative", "Unsure")
            tangra_data: Optional dictionary with Tangra light curve analysis data
            aota_report_data: Optional dictionary with AOTA Report timing/SNR data
            aota_xml_used: Boolean indicating if AOTA XML file was used (for OTE determination)
            clouds: Cloud conditions (e.g., "Clear", "Fog", etc.)
            stability: Atmospheric stability (e.g., "Steady", "Slight flickering", etc.)
            other_conditions: Free text for other observing conditions
        
        Returns:
            Path to generated report file, or None on error
        """
        # Store equipment IDs and observation type
        self._report_telescope_id = telescope_id
        self._report_camera_id = camera_id
        self._observation_type = observation_type or "Positive"
        self._tangra_data = tangra_data
        self._aota_report_data = aota_report_data
        self._aota_xml_used = aota_xml_used
        self._clouds = clouds
        self._stability = stability
        self._other_conditions = other_conditions
        
        print("\n" + "="*60)
        print("USING OPENIZE VERSION - NA Report Generator")
        print("Template: NorthAmerica_AstReportForm_V5.6.12r.xlsx")
        print("="*60 + "\n")
        
        try:
            # Get report folder
            report_folder = self.config.get_reports_folder()
            if not os.path.exists(report_folder):
                os.makedirs(report_folder)
            
            # Check template exists
            template_path = self.get_template_path()
            if not os.path.exists(template_path):
                print(f"ERROR: Template not found: {template_path}")
                return None
            
            # Generate filename
            event_date_str = event.event_datetime.strftime('%Y%m%d') if hasattr(event, 'event_datetime') else 'unknown'
            filename = self._generate_filename(event, event_date_str)
            output_path = os.path.join(report_folder, filename)
            
            # Load workbook using Openize
            print(f"Opening template: {template_path}")
            workbook = Workbook(template_path)
            
            # Get the DATA worksheet (3rd sheet, index 2, same as TT report)
            worksheet = workbook.Worksheets[2]
            print(f"Working with worksheet: {worksheet.Name if hasattr(worksheet, 'Name') else 'Sheet1'}")
            
            # Populate all cells with event data
            self._populate_worksheet(worksheet, event)
            
            # Save the workbook
            print(f"Saving report to: {output_path}")
            workbook.Save(output_path)
            
            print(f"Report successfully generated: {output_path}")
            return output_path
            
        except Exception as ex:
            print(f"ERROR: Failed to generate report - {str(ex)}")
            import traceback
            traceback.print_exc()
            return None
    
    def _populate_worksheet(self, worksheet, event):
        """Populate worksheet cells with event data using Openize SDK
        
        This method directly sets cell values using the Openize Cell API,
        which preserves Excel formatting and data validation.
        
        Cell mapping is based on NA_PLACEHOLDERS.txt documentation.
        """
        
        # OBSERVATION TYPE
        self._set_cell(worksheet, "A2", self._observation_type)
        
        # EVENT INFORMATION
        if hasattr(event, 'event_datetime') and event.event_datetime:
            dt = event.event_datetime
            self._set_cell(worksheet, "D5", dt.year)
            self._set_cell(worksheet, "K5", self.MONTHS[dt.month - 1])
            self._set_cell(worksheet, "P5", dt.day)
            self._set_cell(worksheet, "Y5", dt.hour)
            self._set_cell(worksheet, "AA5", dt.minute)
            self._set_cell(worksheet, "AC5", dt.second)
        
        # ASTEROID INFO
        if hasattr(event, 'object_no') and event.object_no:
            self._set_cell(worksheet, "E7", event.object_no)
        
        if hasattr(event, 'object_name') and event.object_name:
            name = re.sub(r'^\(\d+\)\s*', '', event.object_name).strip()
            self._set_cell(worksheet, "K7", name)
        
        # STAR CATALOG AND NUMBER
        star_name = getattr(event, 'star_name', None) or getattr(event, 'star_id', None)
        if star_name:
            star_catalog, star_number = self.parse_star_catalog(star_name)
            if star_catalog and star_number:
                # Clean star catalog format (remove prefix like "1U    ")
                mapped_catalog = re.sub(r'^1[A-Z]\s+', '', star_catalog).strip()
                self._set_cell(worksheet, "S7", mapped_catalog)
                self._set_cell(worksheet, "X7", star_number)
        
        # OBSERVER INFORMATION
        observer_name = self.config.get_observer_name()
        if observer_name:
            self._set_cell(worksheet, "D9", observer_name)
        
        observer_email = self.config.get_observer_email()
        if observer_email:
            self._set_cell(worksheet, "S9", observer_email)
        
        observer_address = self.config.get_observer_address()
        if observer_address:
            self._set_cell(worksheet, "D11", observer_address)
        
        if hasattr(self.config, 'get_observer_phone'):
            observer_phone = self.config.get_observer_phone()
            if observer_phone:
                self._set_cell(worksheet, "S11", observer_phone)
        
        if hasattr(self.config, 'get_observer_fax'):
            observer_fax = self.config.get_observer_fax()
            if observer_fax:
                self._set_cell(worksheet, "S13", observer_fax)
        
        # City, State, Country combined
        observer_city = self.config.get_observer_city()
        observer_state = self.config.get_observer_state()  
        observer_country = self.config.get_observer_country()
        if observer_city or observer_state or observer_country:
            parts = [p for p in [observer_city, observer_state, observer_country] if p]
            city_state_country = ", ".join(parts)
            self._set_cell(worksheet, "D13", city_state_country)
        
        # OBSERVING LOCATION
        obs_location = getattr(event, 'obs_location', None)
        if obs_location:
            self._set_cell(worksheet, "E15", obs_location)
        
        # LOCATION COORDINATES
        station_lat = getattr(event, 'latitude', 0.0)
        station_lon = getattr(event, 'longitude', 0.0)
        station_elev = getattr(event, 'elevation', 0.0)
        
        if station_lat != 0.0:
            self._set_cell(worksheet, "E17", "deg.ddddd")
            self._set_cell(worksheet, "E18", abs(station_lat))
            self._set_cell(worksheet, "J18", 'S' if station_lat < 0 else 'N')
        
        if station_lon != 0.0:
            self._set_cell(worksheet, "N17", "deg.ddddd")
            self._set_cell(worksheet, "N18", abs(station_lon))
            self._set_cell(worksheet, "R18", 'W' if station_lon < 0 else 'E')
        
        if station_elev != 0.0:
            self._set_cell(worksheet, "V18", station_elev)
            self._set_cell(worksheet, "W18", "m")
            self._set_cell(worksheet, "AA18", "WGS84")
        
        # TELESCOPE
        telescope = self.get_telescope_data(self._report_telescope_id)
        if telescope:
            aperture = telescope.get('aperture', 0)
            if aperture:
                self._set_cell(worksheet, "E20", aperture / 10.0)  # Convert mm to cm
                self._set_cell(worksheet, "H20", "cm")
            
            focal_ratio = telescope.get('focal_ratio', 0)
            if focal_ratio > 0:
                self._set_cell(worksheet, "L20", focal_ratio)
            
            telescope_type = telescope.get('type', '')
            if telescope_type:
                self._set_cell(worksheet, "T20", telescope_type)
        
        # TIMING & RECORDING
        camera = self.get_camera_data(self._report_camera_id)
        if camera:
            timing = camera.get('timing', 'GPS - other linking')
            if timing:
                self._set_cell(worksheet, "E22", timing)
            
            timing_device = camera.get('timing_device', 'SharpCap')
            if timing_device:
                self._set_cell(worksheet, "E23", timing_device)
        
        # OTE (Occultation Timing Extraction)
        ote_value = self._determine_ote_value()
        self._set_cell(worksheet, "E24", ote_value)
        
        # DETECTOR/CAMERA
        if camera:
            detector = camera.get('detector', 'SharpCap')
            if detector:
                self._set_cell(worksheet, "E25", detector)
            
            # Video format from Tangra data if available
            if self._tangra_data and 'video_format' in self._tangra_data:
                video_format_value = self._tangra_data['video_format']
                if video_format_value:
                    self._set_cell(worksheet, "L25", video_format_value)
            
            # Integration time info - add to other detector info
            other_info_parts = []
            if camera.get('other_info'):
                other_info_parts.append(camera['other_info'])
            
            if self._tangra_data and 'tdelta_median' in self._tangra_data:
                exposure_ms = self._tangra_data['tdelta_median']
                exposure_sec = exposure_ms / 1000.0
                other_info_parts.append(f"Integration: {exposure_sec:.3f}s")
            
            if other_info_parts:
                self._set_cell(worksheet, "V25", " | ".join(other_info_parts))
            
            # Exposure/Integration method
            self._set_cell(worksheet, "P25", "Other")
        
        # CONDITIONS (Same cells as TT report: H27, P27, X27)
        if self._clouds:
            self._set_cell(worksheet, "H27", self._clouds)
        if self._stability:
            self._set_cell(worksheet, "P27", self._stability)
        if self._other_conditions:
            self._set_cell(worksheet, "X27", self._other_conditions)
        
        # TIMING OBSERVATIONS - use Tangra data if available
        if self._tangra_data:
            # Start time
            start_time_str = self._tangra_data.get('start_time', '')
            if start_time_str:
                hours, minutes, seconds = self._parse_time_string(start_time_str)
                if hours is not None:
                    self._set_cell(worksheet, "F31", hours)
                    self._set_cell(worksheet, "H31", minutes)
                    self._set_cell(worksheet, "J31", seconds)
            
            # End time
            end_time_str = self._tangra_data.get('end_time', '')
            if end_time_str:
                hours, minutes, seconds = self._parse_time_string(end_time_str)
                if hours is not None:
                    self._set_cell(worksheet, "F37", hours)
                    self._set_cell(worksheet, "H37", minutes)
                    self._set_cell(worksheet, "J37", seconds)
        
        # COMMENTS
        comments = []
        if telescope:
            tel_name = telescope.get('name', 'Unknown Telescope')
            comments.append(f"Telescope: {tel_name}")
        if camera:
            cam_name = camera.get('name', 'Unknown Camera')
            comments.append(f"Camera: {cam_name}")
        
        if comments:
            self._set_cell(worksheet, "D42", comments[0] if len(comments) > 0 else "")
            if len(comments) > 1:
                self._set_cell(worksheet, "D43", comments[1])
        
        self._set_cell(worksheet, "D44", "This report was pre-filled by Occultation Manager")
        
        # AOTA TIMING DATA - populate if available from AOTA Report
        if self._aota_report_data:
            self._populate_aota_data(worksheet, self._aota_report_data)
        
        print("Worksheet population complete")
    
    def _set_cell(self, worksheet, cell_ref, value):
        """Set cell value using Openize SDK
        
        Args:
            worksheet: Openize Worksheet object
            cell_ref: Cell reference in A1 notation (e.g., "A2", "D5")
            value: Value to set (int, float, or string - passed directly to PutValue)
        """
        try:
            if value is None or value == '':
                print(f"  Skipping cell {cell_ref}: value is None or empty")
                return  # Don't set empty values
            
            # Pass value directly without converting to string
            # PutValue handles int, float, string automatically
            print(f"  Setting cell {cell_ref} = {value} (type: {type(value).__name__})")
            worksheet.Cells[cell_ref].PutValue(value)
        except Exception as ex:
            print(f"  ERROR: Could not set cell {cell_ref} to {value}: {ex}")
    
    def _parse_time_string(self, time_str):
        """Parse time string from Tangra format (HH:MM:SS.ffffff)
        
        Returns:
            Tuple of (hours, minutes, seconds) or (None, None, None) on error
        """
        try:
            time_parts = time_str.split(':')
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
                
                return hours, minutes, seconds_decimal
        except Exception as ex:
            print(f"Warning: Could not parse time string '{time_str}': {ex}")
        
        return None, None, None
    
    def _determine_ote_value(self):
        """Determine the OTE (Occultation Timing Extraction) value
        
        Returns the appropriate OTE string based on the data source loaded.
        """
        # Check if AOTA Report data is available
        if self._aota_report_data:
            return "AOTA (part of OCCULT4)"
        
        # Check if AOTA XML was used
        if self._aota_xml_used:
            return "AOTA (part of OCCULT4)"
        
        # Default
        return "PYOTE"
    
    def _populate_aota_data(self, worksheet, aota_report_summary):
        """Populate AOTA timing data from AOTA Report
        
        Args:
            worksheet: Openize Worksheet object
            aota_report_summary: Dictionary with AOTA timing data
        """
        if not aota_report_summary:
            return
        
        # Disappearance (D) times - N, P, R, T columns:
        # Cell N31: AOTA_D_HOURS
        # Cell P31: AOTA_D_MINUTES
        # Cell R31: AOTA_D_SECONDS
        # Cell T31: AOTA_D_ERROR
        d_hours = aota_report_summary.get('d_hours')
        d_minutes = aota_report_summary.get('d_minutes')
        d_seconds = aota_report_summary.get('d_seconds')
        
        if d_hours and d_minutes and d_seconds:
            self._set_cell(worksheet, "N31", d_hours)
            self._set_cell(worksheet, "P31", d_minutes)
            self._set_cell(worksheet, "R31", d_seconds)
            
            d_uncertainty = aota_report_summary.get('d_uncertainty')
            if d_uncertainty is not None:
                try:
                    self._set_cell(worksheet, "T31", float(d_uncertainty))
                except (ValueError, TypeError):
                    print(f"Warning: Could not format d_uncertainty: {d_uncertainty}")
        
        # Reappearance (R) times - N, P, R, T columns:
        # Cell N37: AOTA_R_HOURS
        # Cell P37: AOTA_R_MINUTES
        # Cell R37: AOTA_R_SECONDS
        # Cell T37: AOTA_R_ERROR
        r_hours = aota_report_summary.get('r_hours')
        r_minutes = aota_report_summary.get('r_minutes')
        r_seconds = aota_report_summary.get('r_seconds')
        
        if r_hours and r_minutes and r_seconds:
            self._set_cell(worksheet, "N37", r_hours)
            self._set_cell(worksheet, "P37", r_minutes)
            self._set_cell(worksheet, "R37", r_seconds)
            
            r_uncertainty = aota_report_summary.get('r_uncertainty')
            if r_uncertainty is not None:
                try:
                    self._set_cell(worksheet, "T37", float(r_uncertainty))
                except (ValueError, TypeError):
                    print(f"Warning: Could not format r_uncertainty: {r_uncertainty}")
        
        # SNR - Cell W40 (same as TT report)
        snr = aota_report_summary.get('snr')
        if snr is not None:
            try:
                self._set_cell(worksheet, "W40", float(snr))
            except (ValueError, TypeError):
                print(f"Warning: Could not format snr: {snr}")
        
        print(f"AOTA Report data populated: D={d_hours}:{d_minutes}:{d_seconds}, R={r_hours}:{r_minutes}:{r_seconds}")
    
    def _generate_filename(self, event, event_date_str):
        """Generate NA report filename
        
        Args:
            event: Event object
            event_date_str: Event date as string (YYYYMMDD)
        
        Returns:
            Generated filename string
        """
        # Get object number and name
        object_no = getattr(event, 'object_no', 'unknown')
        object_name = getattr(event, 'object_name', 'unknown')
        
        # Clean object name (remove number prefix)
        clean_name = re.sub(r'^\(\d+\)\s*', '', object_name).strip()
        clean_name = re.sub(r'[^\w\s-]', '', clean_name).strip()
        clean_name = re.sub(r'\s+', '_', clean_name)
        
        # Get observer from config
        observer_name = self.config.get_observer_name()
        if observer_name:
            # Use last name only
            name_parts = observer_name.split()
            observer_short = name_parts[-1] if name_parts else 'Observer'
        else:
            observer_short = 'Observer'
        
        # Get observation type
        obs_type_short = self._observation_type[:3].upper() if self._observation_type else 'POS'
        
        # Format: YYYYMMDD_objectno_objectname_observer_TYPE.xlsx
        filename = f"{event_date_str}_{object_no}_{clean_name}_{observer_short}_{obs_type_short}.xlsx"
        
        return filename
