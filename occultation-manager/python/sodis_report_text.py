"""
SODIS / IOTA-ES text report generator.

Generates plain-text reports based on IOTA-ES_report.txt template.
"""

import os
import re
from datetime import datetime

from report_generator_base import ReportGeneratorBase


class SODISReportGeneratorText(ReportGeneratorBase):
    """Generates SODIS text reports from the IOTA-ES template."""

    TEMPLATE_FILENAME = 'IOTA-ES_report.txt'

    def __init__(self, config):
        super(SODISReportGeneratorText, self).__init__(config)
        self._observation_type = None
        self._tangra_data = None
        self._aota_report_data = None
        self._clouds = None
        self._stability = None
        self._other_conditions = None

    def get_template_path(self):
        return os.path.join(self.config.get_templates_master_reports_folder(), self.TEMPLATE_FILENAME)

    def generate_report(self, event, telescope_id=None, camera_id=None, observation_type=None,
                       tangra_data=None, aota_report_data=None, aota_xml_used=False,
                       clouds=None, stability=None, other_conditions=None, timing_data=None,
                       ntp_comment=None, observation_comment=None, include_station_name=True):
        """Generate SODIS text report.

        Args mirror existing Openize generator call pattern.
        """
        self._report_telescope_id = telescope_id
        self._report_camera_id = camera_id
        self._observation_type = observation_type or "Positive"
        self._tangra_data = tangra_data
        self._aota_report_data = aota_report_data
        self._clouds = clouds
        self._stability = stability
        self._other_conditions = other_conditions
        self._timing_data = timing_data
        self._observation_comment = observation_comment

        template_path = self.get_template_path()
        if not os.path.exists(template_path):
            print("ERROR: SODIS template not found: {0}".format(template_path))
            return None

        reports_folder = self.config.get_reports_folder()
        if not os.path.exists(reports_folder):
            os.makedirs(reports_folder)

        filename = self._generate_filename(event)
        output_path = os.path.join(reports_folder, filename)

        try:
            with open(template_path, 'r', encoding='utf-8') as src:
                template_lines = src.readlines()

            field_values = self._build_field_values(event)
            output_lines = self._render_lines(template_lines, field_values)

            with open(output_path, 'w', encoding='utf-8') as dst:
                dst.writelines(output_lines)

            print("SODIS report generated: {0}".format(output_path))
            return output_path
        except Exception as ex:
            print("ERROR: Failed to generate SODIS report - {0}".format(str(ex)))
            import traceback
            traceback.print_exc()
            return None

    def _render_lines(self, template_lines, field_values):
        """Render output lines by replacing known #Key: lines only."""
        output_lines = []
        for line in template_lines:
            stripped = line.rstrip('\n')
            if stripped.startswith('#') and ':' in stripped:
                key = stripped[1:].split(':', 1)[0].strip()
                if key in field_values:
                    value = field_values[key]
                    output_lines.append("#{0}: {1}\n".format(key, value if value is not None else ''))
                    continue
            output_lines.append(line)
        return output_lines

    def _build_field_values(self, event):
        """Build SODIS field dictionary from available event/config/report data."""
        dt = getattr(event, 'event_datetime', None)

        # Event identifiers
        object_name = getattr(event, 'object_name', '') or ''
        object_no = getattr(event, 'object_no', '') or ''
        star_name = getattr(event, 'star_name', None) or getattr(event, 'star_id', None) or ''

        # Observer
        observer_name = self.config.get_observer_name() or ''
        observer_email = self.config.get_observer_email() or ''
        observer_address = self.config.get_observer_address() or ''

        # Station/location
        nearest_city = getattr(event, 'obs_location', None) or self.config.get_observer_city() or ''
        country_code = self._country_to_code(self.config.get_observer_country() if hasattr(self.config, 'get_observer_country') else '')
        latitude = self._decimal_to_signed_dms(getattr(event, 'latitude', None), is_longitude=False)
        longitude = self._decimal_to_signed_dms(getattr(event, 'longitude', None), is_longitude=True)
        altitude = self._format_number(getattr(event, 'elevation', None), decimals=1)

        # Equipment
        telescope = self.get_telescope_data(self._report_telescope_id) or {}
        camera = self.get_camera_data(self._report_camera_id) or {}

        telescope_code = self._map_telescope_code(telescope.get('type', ''))
        aperture_cm = self._format_number(self._mm_to_cm(telescope.get('aperture', None)), decimals=0)
        focal_length_cm = self._format_number(self._focal_length_cm_from_telescope(telescope), decimals=0)
        observing_method_code = self._map_observing_method_code(camera)

        # Timing from Tangra
        start_obs = self._value_or_blank(self._tangra_data, 'start_time')
        end_obs = self._value_or_blank(self._tangra_data, 'end_time')
        exp_time = self._format_number(self._exposure_seconds(self._tangra_data), decimals=3)

        # AOTA D/R data
        d_text, acc_d, r_text, acc_r, duration = self._build_event_times()

        # Misc
        timesource_code = self._map_timesource_code(camera)
        camera_text = self._camera_text_from_camera(camera)
        snr = self._format_number(self._value_or_blank(self._aota_report_data, 'snr'), decimals=2)

        transparency_code = self._map_transparency_code(self._clouds)
        stability_code = self._map_stability_code(self._stability)

        timing_note = self.build_timing_note(self._timing_data)
        comments_value = self._other_conditions or ''
        if timing_note:
            comments_value = (comments_value + '  ' + timing_note).strip() if comments_value else timing_note
        if self._observation_comment:
            comments_value = (comments_value + '  ' + self._observation_comment).strip() if comments_value else self._observation_comment

        values = {
            'Occultation': (self._observation_type or '').upper(),
            'DATE': dt.strftime('%d %B %Y') if dt else '',
            'PREDICTTIME': dt.strftime('%d %b; %Y %H:%M:%S UT') if dt else '',
            'STAR': star_name,
            'ASTEROID': self._clean_asteroid_name(object_name),
            'Nr': str(object_no) if object_no != '' else '',
            'Observer1': observer_name,
            'Observer2': '',
            'moreObs': '',
            'E-mail': observer_email,
            'Address': observer_address,
            'NearestCity': nearest_city,
            'Countrycode': country_code,
            'Latitude': latitude,
            'Longitude': longitude,
            'Altitude': altitude,
            'Datum': '',
            'Telescope': telescope_code,
            'Aperture': aperture_cm,
            'FocalLength': focal_length_cm,
            'ObservingMethod': observing_method_code,
            'StartObs': start_obs,
            'D': d_text,
            'Acc_D': acc_d,
            'R': r_text,
            'Acc_R': acc_r,
            'EndObs': end_obs,
            'Duration': duration,
            'Exp_Time': exp_time,
            'Timesource': timesource_code,
            'Camera': camera_text,
            'Signal/Noise': snr,
            'Wind': '',
            'Temperature': '',
            'Transparency': transparency_code,
            'Stability': stability_code,
            'Comments': comments_value
        }

        return values

    def _build_event_times(self):
        """Build D/R text and uncertainty fields per observation type and AOTA values."""
        if (self._observation_type or '').lower() == 'negative':
            return 'M', '', 'M', '', ''

        d_h = self._value_or_blank(self._aota_report_data, 'd_hours')
        d_m = self._value_or_blank(self._aota_report_data, 'd_minutes')
        d_s = self._value_or_blank(self._aota_report_data, 'd_seconds')
        r_h = self._value_or_blank(self._aota_report_data, 'r_hours')
        r_m = self._value_or_blank(self._aota_report_data, 'r_minutes')
        r_s = self._value_or_blank(self._aota_report_data, 'r_seconds')

        d_time = self._format_hms(d_h, d_m, d_s)
        r_time = self._format_hms(r_h, r_m, r_s)

        d_text = ('D' + d_time) if d_time else ''
        r_text = ('R' + r_time) if r_time else ''

        acc_d = self._format_number(self._value_or_blank(self._aota_report_data, 'd_uncertainty'), decimals=3)
        acc_r = self._format_number(self._value_or_blank(self._aota_report_data, 'r_uncertainty'), decimals=3)

        duration = ''
        d_total = self._hms_to_seconds(d_h, d_m, d_s)
        r_total = self._hms_to_seconds(r_h, r_m, r_s)
        if d_total is not None and r_total is not None and r_total >= d_total:
            duration = self._format_number(r_total - d_total, decimals=3)

        return d_text, acc_d, r_text, acc_r, duration

    def _generate_filename(self, event):
        dt = getattr(event, 'event_datetime', None)
        date_part = dt.strftime('%Y%m%d') if dt else datetime.utcnow().strftime('%Y%m%d')

        object_no = str(getattr(event, 'object_no', 'unknown'))

        star_name = getattr(event, 'star_name', None) or getattr(event, 'star_id', None)
        star_catalog = 'UNKNOWN'
        star_number = 'UNKNOWN'
        if star_name:
            parsed_catalog, parsed_number = self.parse_star_catalog(star_name)
            if parsed_catalog:
                catalog_mapping = {
                    '1U    UCAC4': 'UCAC4',
                    '1U    UCAC2': 'UCAC2',
                    '1G    Gaia - DR3': 'GAIA_DR3',
                    '1G    Gaia - DR2': 'GAIA_DR2',
                    '1G    Gaia - DR1': 'GAIA_DR1',
                    '1T    Tycho2': 'TYC',
                    '1H    Hipparcos': 'HIP',
                    '1P    PPM': 'PPM',
                    '1D    HD': 'HD'
                }
                star_catalog = catalog_mapping.get(parsed_catalog, re.sub(r'^1[A-Z]\s+', '', str(parsed_catalog)).strip())
            if parsed_number:
                star_number = str(parsed_number)

        # Normalize separators to underscores as requested
        object_no = re.sub(r'[^0-9A-Za-z]+', '_', object_no).strip('_') or 'unknown'
        # Restore space in provisional designations (e.g. 2002_PR155 -> 2002 PR155)
        object_no = re.sub(r'(\d{4})_([A-Z]{1,2}\d)', r'\1 \2', object_no)
        star_catalog = re.sub(r'[^0-9A-Za-z]+', '_', str(star_catalog)).strip('_') or 'UNKNOWN'
        star_number = re.sub(r'[^0-9A-Za-z]+', '_', str(star_number)).strip('_') or 'UNKNOWN'

        return "{0}_{1}_{2}_{3}.txt".format(date_part, object_no, star_catalog, star_number)

    def _clean_asteroid_name(self, name):
        if not name:
            return ''
        return re.sub(r'^\(\d+\)\s*', '', str(name)).strip()

    def _mm_to_cm(self, value):
        try:
            if value is None:
                return None
            return float(value) / 10.0
        except Exception:
            return None

    def _focal_length_cm_from_telescope(self, telescope):
        """Calculate focal length in cm from aperture(mm) * focal_ratio."""
        try:
            if not telescope:
                return None

            aperture_mm = telescope.get('aperture', None)
            focal_ratio = telescope.get('focal_ratio', None)

            if aperture_mm is None or focal_ratio is None:
                return None

            focal_length_mm = float(aperture_mm) * float(focal_ratio)
            return focal_length_mm / 10.0
        except Exception:
            return None

    def _format_hms(self, h, m, s):
        try:
            if h is None or m is None or s is None or h == '' or m == '' or s == '':
                return ''
            h_int = int(float(h))
            m_int = int(float(m))
            s_float = float(s)
            return "{0:02d}:{1:02d}:{2:06.3f}".format(h_int, m_int, s_float).rstrip('0').rstrip('.')
        except Exception:
            return ''

    def _hms_to_seconds(self, h, m, s):
        try:
            if h is None or m is None or s is None or h == '' or m == '' or s == '':
                return None
            return int(float(h)) * 3600 + int(float(m)) * 60 + float(s)
        except Exception:
            return None

    def _decimal_to_signed_dms(self, value, is_longitude):
        try:
            if value is None:
                return ''
            decimal = float(value)
            sign = '+' if decimal >= 0 else '-'
            abs_value = abs(decimal)

            degrees = int(abs_value)
            minutes_full = (abs_value - degrees) * 60.0
            minutes = int(minutes_full)
            seconds = (minutes_full - minutes) * 60.0

            if is_longitude:
                return "{0}{1:03d} {2:02d} {3:04.1f}".format(sign, degrees, minutes, seconds)
            return "{0}{1:02d} {2:02d} {3:04.1f}".format(sign, degrees, minutes, seconds)
        except Exception:
            return ''

    def _exposure_seconds(self, tangra_data):
        try:
            if not tangra_data:
                return None
            if 'tdelta_median' not in tangra_data or tangra_data['tdelta_median'] is None:
                return None
            return float(tangra_data['tdelta_median']) / 1000.0
        except Exception:
            return None

    def _map_timesource_code(self, camera):
        # Prefer explicit Occult/SODIS code if present
        code = (camera.get('occult4_time', '') or '').strip()
        if code in ['a', 'b', 'c', 'd', 'e', 'f', 'g']:
            return code

        timing_text = camera.get('timing', '')
        text = (timing_text or '').lower()
        if 'gps' in text:
            return 'a'
        if 'ntp' in text:
            return 'b'
        return ''

    def _map_observing_method_code(self, camera):
        # Prefer explicit Occult/SODIS code if present
        code = (camera.get('occult4_method', '') or '').strip()
        if code in ['a', 'b', 'c', 'd', 'e', 'f', 'g']:
            return code
        return 'a'

    def _map_telescope_code(self, telescope_type):
        text = (telescope_type or '').lower()
        if 'refractor' in text:
            return '1'
        if 'newton' in text:
            return '2'
        if 'sct' in text or 'schmidt' in text:
            return '3'
        if 'dob' in text:
            return '4'
        if 'binoc' in text:
            return '5'
        if 'evscope' in text:
            return '8'
        if text:
            return '6'
        return ''

    def _map_transparency_code(self, clouds_text):
        text = (clouds_text or '').lower()
        if text == 'clear':
            return '1'
        if text == 'fog':
            return '2'
        if 'thin cloud' in text:
            return '3'
        if 'thick cloud' in text:
            return '4'
        if 'broken cloud' in text:
            return '5'
        if 'star faint' in text:
            return '6'
        if 'averted vision' in text:
            return '7'
        return ''

    def _map_stability_code(self, stability_text):
        text = (stability_text or '').lower()
        if text == 'steady':
            return '1'
        if 'slight flickering' in text:
            return '2'
        if 'strong flickering' in text:
            return '3'
        return ''

    def _camera_text_from_camera(self, camera):
        detector = (camera.get('detector', '') or '').strip()
        if detector == 'Other - List in Comments':
            return (camera.get('other_info', '') or '').strip()
        return detector

    def _country_to_code(self, country):
        if not country:
            return ''
        text = str(country).strip()
        if len(text) == 2 and text.isalpha():
            return text.upper()
        return text

    def _format_number(self, value, decimals=3):
        if value is None or value == '':
            return ''
        try:
            num = float(value)
            if decimals <= 0:
                return str(int(round(num)))
            fmt = "{0:0." + str(decimals) + "f}"
            return fmt.format(num).rstrip('0').rstrip('.')
        except Exception:
            return str(value)

    def _value_or_blank(self, data, key):
        if not data:
            return ''
        return data.get(key, '')
