import os
import json
import binascii
import base64
import urllib.request
import math
from datetime import datetime, timedelta

class EventProcessor:
    """Handles event processing operations"""
    
    def __init__(self, config):
        self.config = config
    
    @staticmethod
    def load_occultations(filename, config):
        """Load occultations from JSON file"""
        try:
            full_path = config.get_full_file_path(filename)
            if os.path.exists(full_path):
                with open(full_path, 'r') as f:
                    return json.load(f)
        except Exception as ex:
            print(f"Error loading occultations: {ex}")
        return []
    
    @staticmethod
    def save_occultations(events_data, filename, config):
        """Save occultations to JSON file"""
        try:
            full_path = config.get_full_file_path(filename)
            with open(full_path, 'w') as f:
                json.dump(events_data, f, indent=2)
            return True
        except Exception as ex:
            print(f"Error saving occultations: {ex}")
            return False
    
    @staticmethod
    def merge_occultation_lists(existing, new, id_key='unique_id', retention_days=14):
        """Merge two lists of occultation dictionaries"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        merged_dict = {}
        
        # Add existing occultations
        for occ in existing:
            if occ is None:
                continue
            if datetime.strptime(occ['event_time'].split('T')[0], '%Y-%m-%d') > cutoff_date: 
                merged_dict[occ[id_key]] = occ
        
        # Add/update with new occultations
        added = 0
        updated = 0
        for occ in new:
            if occ is None:
                continue
            if occ[id_key] in merged_dict and datetime.strptime(occ['event_time'].split('T')[0], '%Y-%m-%d') > cutoff_date:
                updated += 1
                merged_dict[occ[id_key]] = occ
            if occ[id_key] not in merged_dict and datetime.strptime(occ['event_time'].split('T')[0], '%Y-%m-%d') > cutoff_date: 
                added += 1
                merged_dict[occ[id_key]] = occ
        
        result = list(merged_dict.values())
        print("Merge completed: {} existing + {} new = {} total ({} added, {} updated)".format(
            len(existing), len(new), len(result), added, updated))
        
        return result
    
    @staticmethod    
    def get_owc_events(url, username, password, data=None):
        """Get events from OW Cloud API"""
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Basic {encoded_credentials}")
        request.add_header("Content-Type", "application/json")
        
        if data:
            request.data = json.dumps(data).encode('utf-8')
        
        response = urllib.request.urlopen(request)
        return json.loads(response.read().decode('utf-8'))

    def update_ow_cloud_events(self):
        """Get all your OWC announced events using configuration"""
        try:
            result = EventProcessor.get_owc_events(
                self.config.get_full_url(), 
                self.config.get_owc_email(), 
                self.config.get_owc_password()
            )
        except urllib.error.HTTPError as e:
            print(f"HTTP Error: {e.code} - {e.reason}")
            return []

        result = EventProcessor.process_owc_events(result, sitefilter='', config=self.config)
        EventProcessor.save_occultations(result, self.config.get_latest_occultations_file(), self.config)
        latest_occultations = EventProcessor.load_occultations(self.config.get_latest_occultations_file(), self.config)

        # Create new master if doesn't exist
        master_file = self.config.get_full_file_path(self.config.get_occultations_file())
        if not os.path.exists(master_file):
            print("File {} not found - creating new master occultations file".format(self.config.get_occultations_file()))
            EventProcessor.save_occultations(result, self.config.get_occultations_file(), self.config)
        existing_occultations = EventProcessor.load_occultations(self.config.get_occultations_file(), self.config)

        merged_occultations = EventProcessor.merge_occultation_lists(existing_occultations, latest_occultations, id_key='id', retention_days=14)
        EventProcessor.save_occultations(merged_occultations, self.config.get_occultations_file(), self.config)
        return latest_occultations
    
    @staticmethod    
    def process_owc_events(owevents, sitefilter, config):
        """Process OWC events to extract the parameters"""
        # DEBUG: Log raw OWC data at the start
        import os
        module_dir = os.path.dirname(os.path.abspath(__file__))
        debug_log = os.path.join(module_dir, "owc_raw_download.log")
        try:
            with open(debug_log, 'w') as f:  # 'w' to overwrite each time
                f.write("="*80 + "\n")
                f.write("RAW OWC DOWNLOAD DATA - COMPLETE DUMP\n")
                f.write("="*80 + "\n")
                f.write("Number of events: " + str(len(owevents)) + "\n\n")
            print("DEBUG: Writing raw OWC data to: " + debug_log)
        except Exception as e:
            print("DEBUG: Error creating log file: " + str(e))
        
        occultations = []
        for owevent in owevents:
            name = owevent['Object']
            eventDuration = float(owevent['MaxDurSec'])
            eventId = owevent['Id']
            star_id = owevent['StarName']
            ra = float(owevent['RAJ2000Hours'])
            dec = float(owevent['DEJ2000Deg'])

            for station in owevent['Stations']:
                if station['IsOwnStation']:
                    # DEBUG: Log raw OWC station data
                    try:
                        with open(debug_log, 'a') as f:
                            f.write("\n" + "-"*80 + "\n")
                            f.write("Event: " + str(name) + "\n")
                            f.write("Station: " + str(station.get('StationName', 'Unknown')) + "\n")
                            f.write("\nAll station keys: " + str(sorted(station.keys())) + "\n")
                            f.write("\nAll station data:\n")
                            for key in sorted(station.keys()):
                                f.write("  " + str(key) + " = " + str(station[key]) + "\n")
                            f.write("\nELEVATION FIELD CHECK:\n")
                            if 'Elevation' in station:
                                f.write("  >>> FOUND 'Elevation': " + str(station['Elevation']) + " <<<\n")
                            else:
                                f.write("  'Elevation' field NOT FOUND\n")
                            if 'Altitude' in station:
                                f.write("  >>> FOUND 'Altitude': " + str(station['Altitude']) + " <<<\n")
                            else:
                                f.write("  'Altitude' field NOT FOUND\n")
                            if 'Height' in station:
                                f.write("  >>> FOUND 'Height': " + str(station['Height']) + " <<<\n")
                            else:
                                f.write("  'Height' field NOT FOUND\n")
                        print("DEBUG: Logged station data for: " + str(station.get('StationName', 'Unknown')))
                    except Exception as e:
                        print("DEBUG: Error writing station data: " + str(e))
                    
                    eventTime = station['EventTimeUtc']
                    eventUncertainty = station['ErrorInTimeSec']
                    stationName = station['StationName']
                    latitude = station['Latitude']
                    longitude = station['Longitude']
                    starAz = station['StarAz']
                    starAlt = station['StarAlt']
                    starMag = owevent['StarMag']
                    combMag = station['CombMag']
                    magDrop = owevent['MagDrop']

                    if sitefilter != '' and not stationName.startswith(sitefilter):
                        print('Ignoring: %s due to site filter: %s' % (stationName, sitefilter))
                        continue

                    # Recording duration using config values
                    base_dur = config.get_base_duration()
                    recording_duration = round(base_dur + (eventDuration if eventDuration > 5 else 0) + 6*(eventUncertainty if eventUncertainty > 2 else 0))

                    # Calculate the Start/End Times
                    eventCenterTime = datetime.strptime(eventTime.split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    startTime = eventCenterTime - timedelta(seconds=recording_duration/2.0)
                    endTime = eventCenterTime + timedelta(seconds=recording_duration/2.0)
                    gotoTime = eventCenterTime - timedelta(seconds=recording_duration/2.0 + config.get_goto_lead_time())
                    
                    eventCenterTime = eventCenterTime.strftime("%Y-%m-%dT%H:%M:%S")
                    startTime = startTime.strftime("%Y-%m-%dT%H:%M:%S")
                    endTime = endTime.strftime("%Y-%m-%dT%H:%M:%S")
                    gotoTime = gotoTime.strftime("%Y-%m-%dT%H:%M:%S")

                    # Get the occelmnt
                    occelmntUrl = config.get_occelmnt_url() % eventId
                    try:
                        eventOccelmnt = EventProcessor.get_owc_events(
                            occelmntUrl, 
                            config.get_owc_email(), 
                            config.get_owc_password()
                        )
                    except urllib.error.HTTPError as e:
                        print(f"HTTP Error: {e.code} - {e.reason}")
                        eventOccelmnt = None

                    if eventOccelmnt:
                        elements = eventOccelmnt['Occultations']['Event']['Elements'].split(',')
                        star = eventOccelmnt['Occultations']['Event']['Star'].split(',')
                        object_data = eventOccelmnt['Occultations']['Event']['Object'].split(',')
                        owcloudurl = 'https://cloud.occultwatcher.net' + eventOccelmnt['Occultations']['Event']['OWC']
                        object_no = object_data[0]
                    else:
                        object_no = ""
                        owcloudurl = ""

                    # Calculate exposure using config values
                    mag_ref = config.get_mag_for_40ms_exposure()
                    extinction_mag = min(2, -0.5 + 0.5/math.cos((90-starAlt)*2*math.pi/360))
                    exposure = round(max(40, 40 * pow(2, round(combMag + extinction_mag - mag_ref + 0.5, 0)))/20)*20/1000.0

                    # Create dictionary of occultation events
                    occultation = {
                        'name': name + ' - ' + stationName, 
                        'station_name': stationName,
                        'ow_eventid': eventId, 
                        'id': name + ' : ' + star_id + ' : ' + stationName,
                        'ra': ra, 'dec': dec,
                        'star_mag': starMag, 'mag_drop': magDrop, 'comb_mag': combMag,
                        'event_time': eventCenterTime, 'start_time': startTime, 'end_time': endTime, 'goto_time': gotoTime,
                        'event_duration': eventDuration, 'event_uncertainty': eventUncertainty, 'recording_duration': recording_duration,
                        'occelmnt': eventOccelmnt, 'source': 'OWCloud',
                        'latitude': latitude, 'longitude': longitude, 'star_az': starAz, 'star_alt': starAlt,
                        'star_id': star_id, 'object_no': object_no, 'object_name': name, 'exposure': exposure
                    }
                    if owcloudurl:
                        occultation['owcloudurl'] = owcloudurl

                    occultations.append(occultation)

        return occultations

class OccultationEvent:
    """Represents a single occultation event with all calculations"""
    
    def __init__(self, event_data, config):
        self.config = config
        self.original_data = event_data
        self.selected = True
        self.custom_exposure = None  # Track custom exposure settings
        self._parse_event_data(event_data)
        self._calculate_derived_values()
    
    def _parse_event_data(self, data):
        """Parse event data from OW Cloud JSON format"""
        # DEBUG: Log all OWC data fields to check for elevation
        import os
        module_dir = os.path.dirname(os.path.abspath(__file__))
        debug_log = os.path.join(module_dir, "owc_data_debug.log")
        try:
            with open(debug_log, 'a') as f:
                f.write("\n" + "="*80 + "\n")
                f.write("OWC Event Data Debug\n")
                f.write("Available keys: " + str(sorted(data.keys())) + "\n")
                f.write("\nAll data items:\n")
                for key in sorted(data.keys()):
                    f.write("  " + str(key) + " = " + str(data[key]) + "\n")
                f.write("\nChecking for elevation fields:\n")
                if 'elevation' in data:
                    f.write("  FOUND 'elevation': " + str(data['elevation']) + "\n")
                if 'altitude' in data:
                    f.write("  FOUND 'altitude': " + str(data['altitude']) + "\n")
                if 'height' in data:
                    f.write("  FOUND 'height': " + str(data['height']) + "\n")
                if 'station_elevation' in data:
                    f.write("  FOUND 'station_elevation': " + str(data['station_elevation']) + "\n")
                if 'observer_elevation' in data:
                    f.write("  FOUND 'observer_elevation': " + str(data['observer_elevation']) + "\n")
                f.write("="*80 + "\n")
        except Exception as e:
            pass  # Silently ignore debug logging errors
        
        self.name = data.get('name', '')
        self.station_name = data.get('station_name', '')
        self.ow_eventid = data.get('ow_eventid', '')
        self.event_id = data.get('id', '')
        self.object_name = data.get('object_name', '')
        
        self.ra = float(data.get('ra', 0))
        self.dec = float(data.get('dec', 0))
        self.ra_hours = self.ra
        self.dec_degrees = self.dec
        
        self.star_mag = float(data.get('star_mag', 0))
        self.mag_drop = float(data.get('mag_drop', 0))
        self.comb_mag = float(data.get('comb_mag', 0))
        self.magnitude = self.star_mag
        
        self.event_time = data.get('event_time', '')
        self.start_time_str = data.get('start_time', '')
        self.end_time_str = data.get('end_time', '')
        self.goto_time_str = data.get('goto_time', '')
        
        self.event_duration = float(data.get('event_duration', 0))
        self.event_uncertainty = float(data.get('event_uncertainty', 0))
        self.recording_duration = int(data.get('recording_duration', 0))
        
        self.star_id = data.get('star_id', '')
        self.star_az = float(data.get('star_az', 0))
        self.star_alt = float(data.get('star_alt', 0))
        
        self.object_no = data.get('object_no', '')
        self.asteroid_name = self.object_name
        self.star_name = self.star_id
        self.event_name = self.name
        
        self.latitude = float(data.get('latitude', 0))
        self.longitude = float(data.get('longitude', 0))
        self.precalc_exposure = float(data.get('exposure', 0))
        
        self.source = data.get('source', '')
        self.owcloudurl = data.get('owcloudurl', '')
        
        self.event_date = self._extract_date_from_iso(self.event_time)
        self.event_time_utc = self._extract_time_from_iso(self.event_time)
        
        self.duration_seconds = self.event_duration
        self.max_duration_seconds = self.event_duration
        self.uncertainty_seconds = self.event_uncertainty
    
    def _extract_date_from_iso(self, iso_string):
        """Extract date part from ISO datetime string"""
        if iso_string:
            return iso_string.split('T')[0]
        return ''
    
    def _extract_time_from_iso(self, iso_string):
        """Extract time part from ISO datetime string"""
        if iso_string:
            time_part = iso_string.split('T')[1] if 'T' in iso_string else iso_string
            return time_part.replace('Z', '')
        return ''
    


    def _calculate_derived_values(self):
            """Calculate exposure time and recording parameters"""
            if self.custom_exposure is not None:
                # Use custom exposure if set
                self.exposure_ms = int(self.custom_exposure * 1000)
            elif self.precalc_exposure > 0:
                self.exposure_ms = int(self.precalc_exposure * 1000)
            else:
                if self.star_mag > 0:
                    mag_ref = self.config.get_mag_for_40ms_exposure()
                    extinction_mag = min(2, -0.5 + 0.5/math.cos((90-self.star_alt)*2*math.pi/360))
                    self.exposure_ms = round(max(40, 40 * pow(2, round(self.comb_mag + extinction_mag - mag_ref + 0.5, 0)))/20)*20

                else:
                    self.exposure_ms = 40
            # Parse the main event datetime from the stored ISO string
            self.event_datetime = self._parse_iso_datetime(self.event_time)

            # Recompute recording duration and timing windows using current config
            # Read base duration from config; be defensive about types so
            # that strings or None don't cause the value to fall back to 0.
            try:
                base_dur = self.config.get_base_duration()
                if base_dur is None:
                    base_dur = 0
                else:
                    try:
                        base_dur = float(base_dur)
                    except Exception:
                        # If conversion fails, fall back to 0 but don't
                        # crash the whole recalculation.
                        base_dur = 0
            except Exception:
                base_dur = 0

            # Use the stored event_duration and uncertainty to compute recording duration
            try:
                rec_dur = round(base_dur + (self.event_duration if self.event_duration > 5 else 0) + 6 * (self.event_uncertainty if self.event_uncertainty > 2 else 0))
                self.recording_duration = int(rec_dur)
            except Exception:
                # Fallback: keep existing recording_duration if present
                pass

            # Compute start/end/goto times (datetimes and ISO strings) and
            # prepare local-time display strings used by templates/UI.
            try:
                if self.event_datetime:
                    eventCenterTime = self.event_datetime
                    startTime = eventCenterTime - timedelta(seconds=self.recording_duration / 2.0)
                    endTime = eventCenterTime + timedelta(seconds=self.recording_duration / 2.0)
                    try:
                        goto_lead = self.config.get_goto_lead_time()
                        if goto_lead is None:
                            goto_lead = 0
                        else:
                            try:
                                goto_lead = float(goto_lead)
                            except Exception:
                                goto_lead = 0
                    except Exception:
                        goto_lead = 0

                    gotoTime = eventCenterTime - timedelta(seconds=self.recording_duration / 2.0 + goto_lead)

                    # Store ISO strings and parsed datetimes
                    self.start_time_str = startTime.strftime("%Y-%m-%dT%H:%M:%S")
                    self.end_time_str = endTime.strftime("%Y-%m-%dT%H:%M:%S")
                    self.goto_time_str = gotoTime.strftime("%Y-%m-%dT%H:%M:%S")

                    self.start_time = startTime
                    self.end_time = endTime
                    self.goto_time = gotoTime
                else:
                    # If event datetime is not available, parse any existing strings
                    self.start_time = self._parse_iso_datetime(self.start_time_str)
                    self.end_time = self._parse_iso_datetime(self.end_time_str)
                    self.goto_time = self._parse_iso_datetime(self.goto_time_str)
            except Exception:
                # Ensure attributes exist even on failure
                self.start_time = getattr(self, 'start_time', None)
                self.end_time = getattr(self, 'end_time', None)
                self.goto_time = getattr(self, 'goto_time', None)

            # Add local time strings for use in UI/sequence templates
            try:
                from datetime import timezone

                if self.event_datetime:
                    self.event_time_local = (self.event_datetime.replace(tzinfo=timezone.utc).astimezone()).strftime("%I:%M:%S %p") or ""
                else:
                    self.event_time_local = ""

                if self.start_time:
                    self.start_time_local = (self.start_time.replace(tzinfo=timezone.utc).astimezone()).strftime("%I:%M:%S %p") or ""
                else:
                    self.start_time_local = ""

                if self.goto_time:
                    self.goto_time_local = (self.goto_time.replace(tzinfo=timezone.utc).astimezone()).strftime("%I:%M:%S %p") or ""
                    # Pre-goto display (90s before goto) for some templates
                    try:
                        pre_goto = (self.goto_time.replace(tzinfo=timezone.utc).astimezone() - timedelta(seconds=90))
                        self.pre_goto_time_local = pre_goto.strftime("%I:%M:%S %p") or ""
                    except Exception:
                        self.pre_goto_time_local = ""
                else:
                    self.goto_time_local = ""
                    self.pre_goto_time_local = ""
            except Exception:
                # ignore localization failures but ensure attributes exist
                self.event_time_local = getattr(self, 'event_time_local', "")
                self.start_time_local = getattr(self, 'start_time_local', "")
                self.goto_time_local = getattr(self, 'goto_time_local', "")
                self.pre_goto_time_local = getattr(self, 'pre_goto_time_local', "")

    def recompute_timing(self):
        """Public helper to force recalculation of timing and exposure using
        the current configuration. Preserves user custom exposure but clears
        any stored precalc_exposure so recalculation uses live config values.
        """
        try:
            # Clear any precalculated exposure so exposure calculation uses
            # the current config (but keep custom_exposure intact).
            try:
                self.precalc_exposure = 0
            except Exception:
                pass

            # Force recording duration recomputation
            try:
                self.recording_duration = 0
            except Exception:
                pass

            # Recompute derived values (exposure, times, local strings)
            self._calculate_derived_values()
        except Exception as ex:
            print(f"Error recomputing timing for {getattr(self, 'event_name', '')}: {ex}")

            # Compute start/end/goto times from event_datetime and updated recording_duration/goto lead
            if self.event_datetime:
                try:
                    eventCenterTime = self.event_datetime
                    startTime = eventCenterTime - timedelta(seconds=self.recording_duration / 2.0)
                    endTime = eventCenterTime + timedelta(seconds=self.recording_duration / 2.0)
                    try:
                        goto_lead = self.config.get_goto_lead_time()
                        if goto_lead is None:
                            goto_lead = 0
                        else:
                            try:
                                goto_lead = float(goto_lead)
                            except Exception:
                                goto_lead = 0
                    except Exception:
                        goto_lead = 0
                    gotoTime = eventCenterTime - timedelta(seconds=self.recording_duration / 2.0 + goto_lead)

                    # Store ISO strings and parsed datetimes
                    self.start_time_str = startTime.strftime("%Y-%m-%dT%H:%M:%S")
                    self.end_time_str = endTime.strftime("%Y-%m-%dT%H:%M:%S")
                    self.goto_time_str = gotoTime.strftime("%Y-%m-%dT%H:%M:%S")

                    self.start_time = startTime
                    self.end_time = endTime
                    self.goto_time = gotoTime
                except Exception:
                    # If anything fails, try to parse existing strings
                    self.start_time = self._parse_iso_datetime(self.start_time_str)
                    self.end_time = self._parse_iso_datetime(self.end_time_str)
                    self.goto_time = self._parse_iso_datetime(self.goto_time_str)
            else:
                # Event datetime missing: fall back to parsing stored strings
                self.start_time = self._parse_iso_datetime(self.start_time_str)
                self.end_time = self._parse_iso_datetime(self.end_time_str)
                self.goto_time = self._parse_iso_datetime(self.goto_time_str)

            # Add local time strings for use in UI/sequence templates
            try:
                import time
                from datetime import timezone

                if self.event_datetime:
                    self.event_time_local = (self.event_datetime.replace(tzinfo=timezone.utc).astimezone()).strftime("%I:%M:%S %p") or ""
                else:
                    self.event_time_local = ""

                if self.start_time:
                    self.start_time_local = (self.start_time.replace(tzinfo=timezone.utc).astimezone()).strftime("%I:%M:%S %p") or ""
                else:
                    self.start_time_local = ""

                if self.goto_time:
                    self.goto_time_local = (self.goto_time.replace(tzinfo=timezone.utc).astimezone()).strftime("%I:%M:%S %p") or ""
                    self.pre_goto_time_local = (self.goto_time.replace(tzinfo=timezone.utc).astimezone() - timedelta(seconds=90)).strftime("%I:%M:%S %p") or ""
                else:
                    self.goto_time_local = ""
                    self.pre_goto_time_local = ""
            except Exception:
                # ignore localization failures
                pass
        
    def set_custom_exposure(self, exposure_ms):
        """Set custom exposure in milliseconds"""
        self.custom_exposure = exposure_ms / 1000.0
        self.exposure_ms = exposure_ms
        
    def get_exposure_seconds(self):
        """Get exposure in seconds for template substitution"""
        return self.exposure_ms / 1000.0
    
    def has_custom_exposure(self):
        """Check if event has custom exposure setting"""
        return self.custom_exposure is not None
    
    def _parse_iso_datetime(self, iso_string):
        """Parse ISO format datetime string"""
        if not iso_string:
            return None
            
        try:
            formats = [
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ",
                "%Y-%m-%d %H:%M:%S",
            ]
            
            clean_string = iso_string.replace('Z', '')
            
            for fmt in formats:
                try:
                    return datetime.strptime(clean_string, fmt)
                except ValueError:
                    continue
            
            print(f"Could not parse datetime: {iso_string}")
            return None
            
        except Exception as ex:
            print(f"Error parsing datetime '{iso_string}': {ex}")
            return None
    
    def get_coordinates_string(self):
        """Get formatted coordinate string"""
        return f"{self.ra:.4f}h, {self.dec:.4f}°"
    
    def get_status_info(self):
        """Get event status information"""
        if not self.event_datetime:
            return "Invalid"
        
        now = datetime.utcnow()
        if self.event_datetime < now:
            return "Past"
                
        time_to_event = self.event_datetime - now
        if time_to_event.total_seconds() < self.config.get_goto_lead_time():
            return "Now..."
        
        days = time_to_event.days
        hours = time_to_event.seconds // 3600
        return f"{days}d {hours}h"
    
    def get_asteroid_display_name(self):
        """Get proper asteroid name, preferring named asteroids over designations"""
        name = self.object_name
        
        # Common asteroid name mappings (expandable)
        asteroid_names = {
            "2002 WY15": "Asteroid 2002 WY15",
            "4 Vesta": "4 Vesta",
            "1 Ceres": "1 Ceres",
            "2 Pallas": "2 Pallas",
            "3 Juno": "3 Juno",
            # Add more mappings as discovered
        }
        
        # Try to find a better name
        if name in asteroid_names:
            return asteroid_names[name]
        
        # If it looks like a designation, format it nicely
        if name and len(name) > 4 and name[:4].isdigit():
            return f"Asteroid {name}"
        
        # Try to extract numbered asteroid names
        if name and name.split():
            parts = name.split()
            try:
                # Check if first part is a number (numbered asteroid)
                num = int(parts[0])
                if len(parts) > 1:
                    return f"{num} {' '.join(parts[1:])}"
            except ValueError:
                pass
        
        return name or "Unknown Object"

class OccultationManager:
    """Core manager class for GUI"""
    
    def __init__(self, config):
        self.config = config
        self.events = []
        self.all_events = []
        self.selected_events = set()
        self.station_filter = ""
        self.running = False
        
        self.event_processor = EventProcessor(config)
    
    def load_events_from_files(self):
        """Load events from saved JSON files"""
        events_data = EventProcessor.load_occultations(self.config.get_latest_occultations_file(), self.config)
        if not events_data:
            events_data = EventProcessor.load_occultations(self.config.get_occultations_file(), self.config)
        
        if events_data:
            self.all_events = [OccultationEvent(event, self.config) for event in events_data]
            self.events = self.all_events[:]
            self.sort_events()
            return True
        return False
    
    def download_events_from_cloud(self):
        """Download events from OW Cloud"""
        try:
            events_data = self.event_processor.update_ow_cloud_events()
            if events_data:
                self.all_events = [OccultationEvent(event, self.config) for event in events_data]
                self.events = self.all_events[:]
                self.sort_events()
                return len(self.events)
            return 0
        except Exception as e:
            print(f"Error downloading events: {e}")
            return -1
    
    def sort_events(self):
        """Sort events by event time"""
        self.events.sort(key=lambda x: x.event_datetime if x.event_datetime else datetime.min)
    
    def get_filtered_events(self):
        """Get events filtered by station"""
        if self.station_filter:
            return [e for e in self.events if self.station_filter.lower() in e.station_name.lower()]
        return self.events
    
    def set_station_filter(self, filter_text):
        """Set station filter"""
        self.station_filter = filter_text
    
    def clear_station_filter(self):
        """Clear station filter"""
        self.station_filter = ""
        self.events = self.all_events[:]
        #self.refresh_display()
    
    def select_all_events(self):
        """Select all filtered events"""
        filtered_events = self.get_filtered_events()
        self.selected_events.update(filtered_events)
        return len(filtered_events)
    
    def select_no_events(self):
        """Deselect all events"""
        self.selected_events.clear()
    
    def toggle_event_selection(self):
        """Toggle selection of specific events by index. Toggle all On/Off based on first event."""

        filtered_events = self.get_filtered_events()
        if len(filtered_events) >0:
            status = filtered_events[0] in self.selected_events
        else:
            return False
        
        for event in filtered_events:
            if status :
                self.selected_events.remove(event)
            else:
                self.selected_events.add(event)
        return not status

    def get_all_stations(self):
        """Get list of all station names"""
        stations = set()
        for event in self.all_events:
            if event.station_name:
                stations.add(event.station_name)
        return sorted(list(stations))    