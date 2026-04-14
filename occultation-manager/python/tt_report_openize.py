"""
Trans-Tasman / RASNZ Occultation Report Form Generator (Openize SDK)
Proof-of-concept using Openize.OpenXML-SDK for direct Excel manipulation

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


class TTReportGeneratorOpenize(ReportGeneratorBase):
    """
    Generates Trans-Tasman / RASNZ Occultation Report Forms using Openize SDK
    
    This is a proof-of-concept that demonstrates direct Excel cell manipulation
    using the Openize.OpenXML-SDK .NET library via IronPython.
    
    Benefits:
    - Preserves Excel data validation
    - Preserves formulas and formatting
    - More reliable than XML string replacement
    - Cleaner code with direct cell access
    """
    
    # Use original template with data validation enabled
    TEMPLATE_FILENAME = 'RASNZ_AstReporttForm_V4.1.2.G.xlsx'
    
    def __init__(self, config):
        """Initialize with configuration manager"""
        super(TTReportGeneratorOpenize, self).__init__(config)
        
        print("\n" + "="*70)
        print("*** OPENIZE VERSION LOADED - Using tt_report_openize.py ***")
        print("Template: RASNZ_AstReporttForm_V4.1.2.G.xlsx")
        print("="*70 + "\n")
        
        if not OPENIZE_AVAILABLE:
            raise RuntimeError("Openize SDK is not available. Please install the DLL to lib folder.")
    
    def get_template_path(self):
        """Get path to original template file with data validation"""
        return os.path.join(self.config.get_templates_master_reports_folder(), self.TEMPLATE_FILENAME)
    
    def generate_report(self, event, telescope_id=None, camera_id=None, observation_type=None, 
                       tangra_data=None, aota_report_data=None, aota_xml_used=False,
                       clouds=None, stability=None, other_conditions=None, timing_data=None):
        """Generate a Trans-Tasman report using Openize SDK
        
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
            timing_data: Optional dict from ComprehensiveReportDialog.get_timing_data()
        
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
        self._timing_data = timing_data
        
        print("\n" + "="*60)
        print("USING OPENIZE VERSION - TT Report Generator")
        print("Template: RASNZ_AstReporttForm_V4.1.2.G.xlsx")
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
            
            # Get the DATA worksheet (3rd sheet in TT template, index 2)
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
        
        Cell mapping is based on TT_PLACEHOLDERS.txt documentation.
        """
        
        # EVENT INFORMATION
        self._set_cell(worksheet, "A2", self._observation_type)
        
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
                self._set_cell(worksheet, "S7", mapped_catalog)
                self._set_cell(worksheet, "X7", star_number)
        
        self._set_cell(worksheet, "P8", "No")  # RIO_TNO_PREDICTION
        
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
            self._set_cell(worksheet, "D13", ', '.join(parts))
        
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
            if focal_ratio == 0 and telescope.get('focal_length', 0) > 0 and aperture > 0:
                focal_ratio = telescope.get('focal_length') / aperture
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
                self._set_cell(worksheet, "C22", timing)
            
            timing_device = camera.get('timing_device', 'SharpCap')
            if timing_device:
                self._set_cell(worksheet, "E23", timing_device)
        
        self._set_cell(worksheet, "O22", "Video Recording")  # TIMING_METHOD
        self._set_cell(worksheet, "AA22", "No")  # ASTEROID_VISIBLE
        
        # OTE (Occultation Timing Extraction)
        ote_value = self._determine_ote_value()
        print(f"\nSetting OTE value: {ote_value}")
        self._set_cell(worksheet, "O23", ote_value)
        
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
            
            # Integration time from Tangra data if available
            if self._tangra_data and 'tdelta_median' in self._tangra_data:
                exposure_ms = self._tangra_data['tdelta_median']
                exposure_sec = exposure_ms / 1000.0
                print(f"\nSetting integration time: {exposure_ms}ms = {exposure_sec}s")
                self._set_cell(worksheet, "P25", exposure_sec)
                self._set_cell(worksheet, "S25", "Seconds")
        
        # Camera delay / timing correction cell (P26)
        # Prefer net_correction_s from timing_data when available; fall back to tangra acquisition_delay
        if self._timing_data and self._timing_data.get('net_correction_s') is not None:
            net_s = self._timing_data['net_correction_s']
            print(f"\nSetting timing correction (net): {net_s}s")
            self._set_cell(worksheet, "P26", net_s)
            self._set_cell(worksheet, "O26", "yes")
        elif self._tangra_data and 'acquisition_delay' in self._tangra_data:
            delay_ms = self._tangra_data['acquisition_delay']
            delay_sec = delay_ms / 1000.0
            print(f"\nSetting camera delay: {delay_ms}ms = {delay_sec}s")
            self._set_cell(worksheet, "P26", delay_sec)
            self._set_cell(worksheet, "O26", "yes")
        else:
            self._set_cell(worksheet, "O26", "No")
        
        # CONDITIONS (Row 27)
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
            print(f"\nProcessing start time: {start_time_str}")
            if start_time_str:
                hours, minutes, seconds = self._parse_time_string(start_time_str)
                print(f"  Parsed: hours={hours}, minutes={minutes}, seconds={seconds}")
                if hours is not None:
                    self._set_cell(worksheet, "F31", hours)
                    self._set_cell(worksheet, "H31", minutes)
                    self._set_cell(worksheet, "J31", seconds)
            
            # End time
            end_time_str = self._tangra_data.get('end_time', '')
            print(f"\nProcessing end time: {end_time_str}")
            if end_time_str:
                hours, minutes, seconds = self._parse_time_string(end_time_str)
                print(f"  Parsed: hours={hours}, minutes={minutes}, seconds={seconds}")
                if hours is not None:
                    self._set_cell(worksheet, "F37", hours)
                    self._set_cell(worksheet, "H37", minutes)
                    self._set_cell(worksheet, "J37", seconds)
        
        # EVENT OUTCOME
        # Set WAS_MISS based on observation type
        if self._observation_type == 'Positive':
            self._set_cell(worksheet, "W38", "no")
        elif self._observation_type == 'Negative':
            self._set_cell(worksheet, "W38", "yes")
        else:  # Unsure
            self._set_cell(worksheet, "W38", "maybe")
        
        self._set_cell(worksheet, "D40", "No")  # SECOND_STAR
        
        # COMMENTS
        if camera:
            other_info = camera.get('other_info', '')
            if other_info:
                self._set_cell(worksheet, "D42", other_info)
        
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
        
        For TT report, valid values are:
        - Manual
        - AOTA (part of OCCULT4)
        - Occular
        - R-OTE
        - Other - Specify in Comments
        """
        # Check if AOTA Report data is available
        if self._aota_report_data:
            return "AOTA (part of OCCULT4)"
        
        # Check if AOTA XML was used
        if self._aota_xml_used:
            return "AOTA (part of OCCULT4)"
        
        # Default to AOTA (part of OCCULT4)
        return "AOTA (part of OCCULT4)"
    
    def _populate_aota_data(self, worksheet, aota_report_summary):
        """Populate AOTA timing data from AOTA Report
        
        Args:
            worksheet: Openize Worksheet object
            aota_report_summary: Dictionary from aota_report_parser.get_event_summary()
        """
        if not aota_report_summary:
            return

        def _is_blank(value):
            return value is None or (isinstance(value, str) and value.strip() == "")

        def _normalize_hms(hours, minutes, seconds):
            # Handle accidental combined format in seconds slot: "HH MM SS.s"
            if _is_blank(hours) and _is_blank(minutes) and isinstance(seconds, str):
                sec_text = seconds.strip()
                parts = sec_text.split()
                if len(parts) == 3:
                    return parts[0], parts[1], parts[2]

            # Handle accidental combined format in hours slot: "HH MM SS.s"
            if isinstance(hours, str):
                hour_text = hours.strip()
                parts = hour_text.split()
                if len(parts) == 3 and _is_blank(minutes) and _is_blank(seconds):
                    return parts[0], parts[1], parts[2]

            return hours, minutes, seconds

        def _to_int_or_none(value):
            if _is_blank(value):
                return None
            try:
                # Excel text prefixes like '\'' should not flow into numeric fields.
                text = str(value).strip().lstrip("'")
                return int(text)
            except Exception:
                return None

        def _to_seconds_float_or_none(value):
            if _is_blank(value):
                return None
            try:
                # Excel text prefixes like '\'' should not flow into numeric fields.
                text = str(value).strip().lstrip("'")
                return round(float(text), 3)
            except Exception:
                return None
        
        # Disappearance (D) times - F, H, J columns for hours, minutes, seconds:
        # Cell F33: AOTA_D_HOURS
        # Cell H33: AOTA_D_MINUTES
        # Cell J33: AOTA_D_SECONDS
        # Cell M33: AOTA_D_ERROR
        d_hours = aota_report_summary.get('d_hours')
        d_minutes = aota_report_summary.get('d_minutes')
        d_seconds = aota_report_summary.get('d_seconds')
        d_hours, d_minutes, d_seconds = _normalize_hms(d_hours, d_minutes, d_seconds)

        d_hours_num = _to_int_or_none(d_hours)
        d_minutes_num = _to_int_or_none(d_minutes)
        d_seconds_num = _to_seconds_float_or_none(d_seconds)

        r_hours = aota_report_summary.get('r_hours')
        r_minutes = aota_report_summary.get('r_minutes')
        r_seconds = aota_report_summary.get('r_seconds')
        r_hours, r_minutes, r_seconds = _normalize_hms(r_hours, r_minutes, r_seconds)

        r_hours_num = _to_int_or_none(r_hours)
        r_minutes_num = _to_int_or_none(r_minutes)
        r_seconds_num = _to_seconds_float_or_none(r_seconds)

        # Write D cells: F33=hours, H33=minutes, J33=seconds, M33=uncertainty
        if d_hours_num is not None or d_minutes_num is not None or d_seconds_num is not None:
            if d_hours_num is not None:
                self._set_cell(worksheet, "F33", d_hours_num)
            if d_minutes_num is not None:
                self._set_cell(worksheet, "H33", d_minutes_num)
            if d_seconds_num is not None:
                self._set_cell(worksheet, "J33", d_seconds_num)
            d_uncertainty = aota_report_summary.get('d_uncertainty')
            if d_uncertainty is not None:
                try:
                    self._set_cell(worksheet, "M33", float(d_uncertainty))
                except (ValueError, TypeError):
                    print(f"Warning: Could not format d_uncertainty: {d_uncertainty}")

        # Write R cells: F35=hours, H35=minutes, J35=seconds, M35=uncertainty
        if r_hours_num is not None or r_minutes_num is not None or r_seconds_num is not None:
            if r_hours_num is not None:
                self._set_cell(worksheet, "F35", r_hours_num)
            if r_minutes_num is not None:
                self._set_cell(worksheet, "H35", r_minutes_num)
            if r_seconds_num is not None:
                self._set_cell(worksheet, "J35", r_seconds_num)
            r_uncertainty = aota_report_summary.get('r_uncertainty')
            if r_uncertainty is not None:
                try:
                    self._set_cell(worksheet, "M35", float(r_uncertainty))
                except (ValueError, TypeError):
                    print(f"Warning: Could not format r_uncertainty: {r_uncertainty}")
        snr = aota_report_summary.get('snr')
        if snr is not None:
            try:
                self._set_cell(worksheet, "W40", float(snr))
            except (ValueError, TypeError):
                print(f"Warning: Could not format snr: {snr}")
        
        print(f"AOTA Report data populated: D={d_hours}:{d_minutes}:{d_seconds}, R={r_hours}:{r_minutes}:{r_seconds}")
    
    def _generate_filename(self, event, event_date_str):
        """Generate TT report filename
        
        Format: YYYYMMDD_###_Asteroid_name_Catalog_Number+/-Surname_Station.xlsx
        """
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


# Convenience function to check if Openize is available
def is_openize_available():
    """Check if Openize SDK is available and loaded"""
    return OPENIZE_AVAILABLE


# Example usage (for testing)
if __name__ == "__main__":
    print("TT Report Generator - Openize SDK Proof of Concept")
    print("=" * 60)
    
    if not OPENIZE_AVAILABLE:
        print("\nERROR: Openize SDK is not available.")
        print("Please ensure the following DLLs are in the 'lib' folder:")
        print("  - Openize.OpenXML-SDK.dll")
        print("  - DocumentFormat.OpenXml.dll")
        print("\nDownload from: https://www.nuget.org/packages/Openize.OpenXML-SDK/")
    else:
        print("\nSUCCESS: Openize SDK loaded successfully!")
        print("\nTo use this generator:")
        print("  from tt_report_openize import TTReportGeneratorOpenize")
        print("  generator = TTReportGeneratorOpenize(config)")
        print("  generator.generate_report(event, telescope_id, camera_id, ...)")
