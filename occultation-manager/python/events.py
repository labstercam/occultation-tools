import os
import json
import binascii
import base64
import urllib.request
import urllib.parse
import math
from datetime import datetime, timedelta

# Import location lookup function for use during event download
try:
    from utils import get_location_name_from_coordinates
except ImportError:
    # Fallback if utils not available
    def get_location_name_from_coordinates(lat, lon):
        return None

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
                with open(full_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as ex:
            print(f"Error loading occultations: {ex}")
        return []
    
    @staticmethod
    def save_occultations(events_data, filename, config):
        """Save occultations to JSON file"""
        try:
            full_path = config.get_full_file_path(filename)
            with open(full_path, 'w', encoding='utf-8') as f:
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
        status_fields = ('owc_report_status', 'status')
        
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
                # Preserve locally persisted OWC status fields unless the new
                # payload explicitly provides replacements.
                existing_entry = merged_dict[occ[id_key]]
                for field_name in status_fields:
                    existing_value = existing_entry.get(field_name)
                    incoming_value = occ.get(field_name)
                    if existing_value and not incoming_value:
                        occ[field_name] = existing_value
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
        """Get events from OW Cloud API using Basic Auth + apikey URL parameter.

        This is the original v1 method.  It is preserved unchanged.
        New code should prefer get_owc_events_v2() which uses the OW-ApiKey header.
        """
        credentials = '{0}:{1}'.format(username, password)
        encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        
        request = urllib.request.Request(url)
        request.add_header("Authorization", "Basic {0}".format(encoded_credentials))
        request.add_header("Content-Type", "application/json")
        
        if data:
            request.data = json.dumps(data).encode('utf-8')
        
        response = urllib.request.urlopen(request, timeout=20)
        return json.loads(response.read().decode('utf-8'))

    @staticmethod
    def get_owc_events_v2(url, api_key, data=None, method='GET'):
        """Call an OWC API endpoint using the OW-ApiKey HTTP header (v2 auth).

        This is the new preferred authentication method.  No credentials or
        apikey parameter are included in the URL — the key is sent as a header.
        The old get_owc_events() method is preserved and continues to work.

        Args:
            url:     Full endpoint URL (no ?apikey= suffix needed)
            api_key: OWC API key string (from config.get_api_key())
            data:    Optional dict to send as a JSON body
            method:  HTTP method string.  Defaults to 'GET'; set to 'POST' for
                     write operations such as report-observation.

        Returns:
            Parsed JSON response (dict or list)
        """
        req = urllib.request.Request(url)
        req.get_method = lambda: method   # IronPython-safe; avoids method= kwarg
        req.add_header('OW-ApiKey', api_key)
        req.add_header('Content-Type', 'application/json')
        if data is not None:
            req.data = json.dumps(data).encode('utf-8')
        response = urllib.request.urlopen(req, timeout=20)
        body = response.read().decode('utf-8')
        if not body.strip():
            return None   # empty body (e.g. HTTP 204) — not an error
        return json.loads(body)

    @staticmethod
    def _extract_owc_event_token_from_url(value):
        """Extract OWC event token from URL path /event/<token>/... if present."""
        if not value:
            return None
        try:
            s = str(value).strip()
            if '/event/' not in s:
                return None
            part = s.split('/event/', 1)[1]
            token = part.split('/', 1)[0].strip()
            return token or None
        except Exception:
            return None

    @staticmethod
    def _is_uuid_like(value):
        """True if value looks like a canonical UUID string."""
        if not value:
            return False
        s = str(value).strip().lower()
        if len(s) != 36:
            return False
        try:
            parts = s.split('-')
            if len(parts) != 5:
                return False
            sizes = [8, 4, 4, 4, 12]
            for p, sz in zip(parts, sizes):
                if len(p) != sz:
                    return False
                int(p, 16)
            return True
        except Exception:
            return False

    @staticmethod
    def _extract_owc_style_event_id(value):
        """Return OWC-style EventID token (e.g. 1970-...-U081512) when detectable."""
        if value is None:
            return None
        s = str(value).strip()
        if not s:
            return None

        from_url = EventProcessor._extract_owc_event_token_from_url(s)
        if from_url:
            s = from_url

        # OWC-style IDs are dash-separated, typically include a 'U...' suffix,
        # and are not UUID hex strings.
        if '-' in s and not EventProcessor._is_uuid_like(s):
            return s
        return None

    @staticmethod
    def _find_owc_style_event_id_in_json(data):
        """Search a JSON-like object recursively for an OWC-style EventID token."""
        if data is None:
            return None

        if isinstance(data, dict):
            preferred_keys = (
                'EventID', 'eventID', 'eventId', 'EventId',
                'owApiEventId', 'ow_api_eventid', 'OWC', 'Owc', 'owc'
            )
            for k in preferred_keys:
                if k in data:
                    candidate = EventProcessor._extract_owc_style_event_id(data.get(k))
                    if candidate:
                        return candidate
            for v in data.values():
                candidate = EventProcessor._find_owc_style_event_id_in_json(v)
                if candidate:
                    return candidate
            return None

        if isinstance(data, list):
            for item in data:
                candidate = EventProcessor._find_owc_style_event_id_in_json(item)
                if candidate:
                    return candidate
            return None

        return EventProcessor._extract_owc_style_event_id(data)

    @staticmethod
    def _resolve_ow_api_eventid(config, event_id, ow_api_eventid=None, owcloudurl=None):
        """Resolve OWC-style EventID for report-observation API-key POST.

        Resolution order:
          1) event JSON field (ow_api_eventid)
          2) token parsed from owcloudurl
          3) GET /api2/v1/events/{ow_eventid} lookup and recursive parse
          4) fallback to original ow_eventid
        """
        candidate = EventProcessor._extract_owc_style_event_id(ow_api_eventid)
        if candidate:
            return candidate, 'event_json'

        candidate = EventProcessor._extract_owc_style_event_id(owcloudurl)
        if candidate:
            return candidate, 'owcloudurl'

        try:
            lookup_url = config.get_event_by_id_url(event_id)
            lookup = EventProcessor.get_owc_events_v2(lookup_url, config.get_api_key(), method='GET')
            candidate = EventProcessor._find_owc_style_event_id_in_json(lookup)
            if candidate:
                return candidate, 'event_by_id_lookup'
        except Exception:
            pass

        return str(event_id), 'fallback_ow_eventid'

    @staticmethod
    def submit_owc_report(config, event, observation_type,
                          comment='', duration_s=None, update_location=False):
        """Submit an observation result to OWC via the report-observation endpoint.

        Args:
            config:           ConfigManager instance
            event:            OccultationEvent or dict — must have 'ow_eventid' and
                              'owc_station_id' (populated by process_owc_events)
            observation_type: One of 'Positive', 'Negative', 'Clouded', 'Failed',
                              'NotObserved', 'NotReduced'
            comment:          Optional free-text comment string
            duration_s:       Optional float duration in seconds (Positive detections only)
            update_location:  If True, include observer lat/lng/elevation in the payload

        Returns:
            dict with keys:
                'success':  bool
                'response': raw response dict/list from OWC, or None
                'error':    error message string, or None
        """
        REPORT_CODES = {
            'NotReported':  0,
            'Miss':         1,
            'Negative':     1,
            'Clouded':      2,
            'Failed':       3,
            'Positive':     4,
            'NotObserved':  5,
            'NotReduced':   6,
        }

        # Accept both OccultationEvent objects and plain dicts
        if isinstance(event, dict):
            event_id   = event.get('ow_eventid')
            ow_api_eventid = event.get('ow_api_eventid')
            station_id = event.get('owc_station_id')
            latitude   = event.get('latitude')
            longitude  = event.get('longitude')
            elevation  = event.get('elevation')
            owcloudurl = event.get('owcloudurl')
        else:
            event_id   = getattr(event, 'ow_eventid',   None)
            ow_api_eventid = getattr(event, 'ow_api_eventid', None)
            station_id = getattr(event, 'owc_station_id', None)
            latitude   = getattr(event, 'latitude',     None)
            longitude  = getattr(event, 'longitude',    None)
            elevation  = getattr(event, 'elevation',    None)
            owcloudurl = getattr(event, 'owcloudurl',   None)

        if not event_id:
            return {'success': False, 'response': None,
                    'error': 'No ow_eventid on event',
                    'auth_method': None,
                    'endpoint_used': None}
        if station_id is None:
            return {'success': False, 'response': None,
                    'error': 'No owc_station_id on event — ensure events were downloaded with the current version',
                    'auth_method': None,
                    'endpoint_used': None}

        report_code = REPORT_CODES.get(observation_type)
        if report_code is None:
            return {'success': False, 'response': None,
                    'error': 'Unknown observation_type: ' + str(observation_type),
                    'auth_method': None,
                    'endpoint_used': None,
                    'attempted_calls': []}

        resolved_event_id, resolved_event_id_source = EventProcessor._resolve_ow_api_eventid(
            config,
            event_id,
            ow_api_eventid=ow_api_eventid,
            owcloudurl=owcloudurl,
        )
        if isinstance(event, dict):
            event['ow_api_eventid'] = resolved_event_id

        payload = {
            'eventId':   str(resolved_event_id),
            'stationId': int(station_id),
            'report':    report_code,
            'comment':   comment or '',
        }

        if observation_type == 'Positive' and duration_s is not None:
            payload['duration'] = float(duration_s)

        if update_location and latitude is not None and longitude is not None:
            payload['updateLocation'] = True
            payload['latDeg']         = round(float(latitude), 5)   # ~1 m accuracy
            payload['lngDeg']         = round(float(longitude), 5)
            if elevation is not None:
                payload['altMslMeters'] = int(round(float(elevation)))  # nearest metre

        attempted_calls = []
        url = config.get_report_observation_url()
        attempted_calls.append({
            'auth_method': 'api_key',
            'endpoint_used': url,
            'event_id_source': resolved_event_id_source,
            'headers': {
                'OW-ApiKey': str(config.get_api_key() or '')[:8] + '...',
                'Content-Type': 'application/json',
            },
            'body': payload,
            'outcome': 'pending',
        })
        try:
            response = EventProcessor.get_owc_events_v2(
                url, config.get_api_key(), data=payload, method='POST'
            )
            attempted_calls[-1]['outcome'] = 'success'
            return {
                'success': True,
                'response': response,
                'error': None,
                'auth_method': 'api_key',
                'endpoint_used': url,
                'attempted_calls': attempted_calls,
            }
        except urllib.error.HTTPError as ex:
            # Read the response body — OWC often returns a JSON error description
            try:
                error_body = ex.read().decode('utf-8')
            except Exception:
                error_body = ''
            attempted_calls[-1]['outcome'] = 'http_error'
            attempted_calls[-1]['status'] = ex.code
            attempted_calls[-1]['reason'] = ex.reason
            attempted_calls[-1]['response_body'] = error_body

            # Fallback: OWC planning endpoint expects the encoded event token and
            # Basic auth, and is currently the server-side route that accepts report posts.
            if ex.code in (404, 405) and ('Cannot locate event' in error_body or ex.code == 405):
                token = None
                if owcloudurl:
                    try:
                        parts = str(owcloudurl).split('/event/', 1)
                        if len(parts) == 2:
                            token = parts[1].split('/', 1)[0]
                    except Exception:
                        token = None

                if token:
                    try:
                        report_duration = float(duration_s) if duration_s is not None else 0.0
                        planning_query = {
                            'stationId': int(station_id),
                            'report': int(report_code),
                            'duration': report_duration,
                            'comment': comment or '',
                        }
                        planning_url = (
                            config.get_host()
                            + '/api2/v1/planning/' + str(token)
                            + '/report-obs?'
                            + urllib.parse.urlencode(planning_query)
                        )

                        credentials = '{0}:{1}'.format(
                            config.get_owc_email(), config.get_owc_password())
                        encoded_credentials = base64.b64encode(
                            credentials.encode('utf-8')).decode('utf-8')

                        attempted_calls.append({
                            'auth_method': 'basic_auth_fallback',
                            'endpoint_used': planning_url,
                            'headers': {
                                'Authorization': 'Basic ' + encoded_credentials[:8] + '...',
                                'Content-Type': 'application/json',
                            },
                            'body': None,
                            'outcome': 'pending',
                        })

                        req = urllib.request.Request(planning_url, data=b'')
                        req.get_method = lambda: 'POST'
                        req.add_header('Authorization', 'Basic {0}'.format(encoded_credentials))
                        req.add_header('Content-Type', 'application/json')

                        fallback_resp = urllib.request.urlopen(req, timeout=20)
                        fallback_body = fallback_resp.read().decode('utf-8')
                        attempted_calls[-1]['outcome'] = 'success'
                        attempted_calls[-1]['status'] = getattr(fallback_resp, 'status', 200)
                        attempted_calls[-1]['response_body'] = fallback_body
                        try:
                            parsed_fallback = json.loads(fallback_body) if fallback_body.strip() else None
                        except Exception:
                            parsed_fallback = fallback_body
                        return {
                            'success': True,
                            'response': parsed_fallback,
                            'error': None,
                            'auth_method': 'basic_auth_fallback',
                            'endpoint_used': planning_url,
                            'attempted_calls': attempted_calls,
                        }
                    except urllib.error.HTTPError as ex2:
                        try:
                            error_body2 = ex2.read().decode('utf-8')
                        except Exception:
                            error_body2 = ''
                        attempted_calls[-1]['outcome'] = 'http_error'
                        attempted_calls[-1]['status'] = ex2.code
                        attempted_calls[-1]['reason'] = ex2.reason
                        attempted_calls[-1]['response_body'] = error_body2
                        msg2 = 'HTTP {0}: {1}'.format(ex2.code, ex2.reason)
                        if error_body2.strip():
                            msg2 = msg2 + ' — ' + error_body2.strip()
                        return {
                            'success': False,
                            'response': None,
                            'error': (
                                'Primary report-observation failed; fallback planning endpoint also failed. '
                                + msg2
                            ),
                            'auth_method': 'basic_auth_fallback',
                            'endpoint_used': planning_url,
                            'attempted_calls': attempted_calls,
                        }
                    except Exception as ex2:
                        attempted_calls[-1]['outcome'] = 'exception'
                        attempted_calls[-1]['reason'] = str(ex2)
                        return {
                            'success': False,
                            'response': None,
                            'error': (
                                'Primary report-observation failed; fallback planning endpoint error: '
                                + str(ex2)
                            ),
                            'auth_method': 'basic_auth_fallback',
                            'endpoint_used': planning_url,
                            'attempted_calls': attempted_calls,
                        }

            msg = 'HTTP {0}: {1}'.format(ex.code, ex.reason)
            if error_body.strip():
                msg = msg + ' — ' + error_body.strip()
            return {
                'success': False,
                'response': None,
                'error': msg,
                'auth_method': 'api_key',
                'endpoint_used': url,
                'attempted_calls': attempted_calls,
            }
        except Exception as ex:
            attempted_calls[-1]['outcome'] = 'exception'
            attempted_calls[-1]['reason'] = str(ex)
            return {
                'success': False,
                'response': None,
                'error': str(ex),
                'auth_method': 'api_key',
                'endpoint_used': url,
                'attempted_calls': attempted_calls,
            }

    def update_ow_cloud_events(self, progress_callback=None):
        """Get all your OWC announced events using configuration"""
        try:
            result = EventProcessor.get_owc_events_v2(
                self.config.get_base_url(),
                self.config.get_api_key()
            )
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"OW Cloud HTTP Error: {e.code} - {e.reason}")
        except urllib.error.URLError as e:
            reason = getattr(e, 'reason', e)
            raise RuntimeError(f"OW Cloud Connection Error: {reason}")
        except Exception as e:
            raise RuntimeError(f"OW Cloud Connection Error: {e}")

        # Build geocode cache from existing saved events so repeated downloads
        # can reuse elevation/location by coordinates instead of API calls.
        geocode_cache = {}
        existing_occultations = EventProcessor.load_occultations(self.config.get_occultations_file(), self.config)
        if existing_occultations:
            for existing in existing_occultations:
                try:
                    latitude = existing.get('latitude')
                    longitude = existing.get('longitude')
                    if latitude is None or longitude is None:
                        continue
                    cache_key = (round(float(latitude), 6), round(float(longitude), 6))
                    elevation = existing.get('elevation', 0.0)
                    obs_location = existing.get('obs_location', '')
                    if elevation is not None or obs_location:
                        geocode_cache[cache_key] = {
                            'elevation': float(elevation) if elevation is not None else 0.0,
                            'obs_location': str(obs_location) if obs_location else ''
                        }
                except Exception:
                    pass

        result = EventProcessor.process_owc_events(
            result,
            sitefilter='',
            config=self.config,
            progress_callback=progress_callback,
            geocode_cache=geocode_cache
        )
        EventProcessor.save_occultations(result, self.config.get_latest_occultations_file(), self.config)
        latest_occultations = EventProcessor.load_occultations(self.config.get_latest_occultations_file(), self.config)

        # Create new master if doesn't exist
        master_file = self.config.get_full_file_path(self.config.get_occultations_file())
        if not os.path.exists(master_file):
            print("File {} not found - creating new master occultations file".format(self.config.get_occultations_file()))
            EventProcessor.save_occultations(result, self.config.get_occultations_file(), self.config)
        existing_occultations = EventProcessor.load_occultations(self.config.get_occultations_file(), self.config)

        retention_days = self.config.get_days_to_retain_events()
        merged_occultations = EventProcessor.merge_occultation_lists(existing_occultations, latest_occultations, id_key='id', retention_days=retention_days)
        EventProcessor.save_occultations(merged_occultations, self.config.get_occultations_file(), self.config)
        return latest_occultations
    
    @staticmethod    
    def process_owc_events(owevents, sitefilter, config, progress_callback=None, geocode_cache=None):
        """Process OWC events to extract the parameters"""
        # Optional debug logging (controlled by config)
        import os
        debug_enabled = False
        try:
            debug_enabled = bool(config.get_output_debug_logs())
        except Exception:
            debug_enabled = False

        module_dir = os.path.dirname(os.path.abspath(__file__))
        debug_log = os.path.join(module_dir, "owc_raw_download.log")
        if debug_enabled:
            try:
                with open(debug_log, 'w', encoding='utf-8') as f:  # 'w' to overwrite each time
                    f.write("="*80 + "\n")
                    f.write("RAW OWC DOWNLOAD DATA - COMPLETE DUMP\n")
                    f.write("="*80 + "\n")
                    f.write("Number of events: " + str(len(owevents)) + "\n\n")
                print("DEBUG: Writing raw OWC data to: " + debug_log)
            except Exception as e:
                print("DEBUG: Error creating log file: " + str(e))
        
        occultations = []
        geocode_cache = geocode_cache or {}

        total_events = 0
        for owevent in owevents:
            stations = owevent.get('Stations', [])
            for station in stations:
                if station.get('IsOwnStation'):
                    total_events += 1

        processed_events = 0
        if progress_callback:
            try:
                progress_callback(0, total_events, "")
            except Exception:
                pass

        for owevent in owevents:
            name = owevent['Object']
            eventDuration = float(owevent['MaxDurSec'])
            eventId = owevent['Id']
            star_id = owevent['StarName']
            ra = float(owevent['RAJ2000Hours'])
            dec = float(owevent['DEJ2000Deg'])

            for station in owevent['Stations']:
                if station['IsOwnStation']:
                    processed_events += 1
                    if progress_callback:
                        try:
                            progress_callback(processed_events, total_events, owevent.get('Object', 'Unknown Object'))
                        except Exception:
                            pass

                    if debug_enabled:
                        try:
                            with open(debug_log, 'a', encoding='utf-8') as f:
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
                    # StationId arrives as a string (e.g. '1'); guard against 'None' sentinel
                    _raw_sid = station.get('StationId')
                    owc_station_id = int(_raw_sid) if _raw_sid not in (None, 'None', '') else None
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
                    occelmntUrl = config.get_occelmnt_base_url() % eventId
                    try:
                        eventOccelmnt = EventProcessor.get_owc_events_v2(
                            occelmntUrl,
                            config.get_api_key()
                        )
                    except urllib.error.HTTPError as e:
                        print(f"HTTP Error: {e.code} - {e.reason}")
                        eventOccelmnt = None
                    except urllib.error.URLError:
                        eventOccelmnt = None
                    except Exception:
                        eventOccelmnt = None

                    # Extract Occelmnt data with error handling
                    object_no = ""
                    owcloudurl = ""
                    
                    # Initialize Occelmnt data fields for OBS.XML export
                    occelmnt_data = {}
                    
                    if eventOccelmnt:
                        try:
                            elements = eventOccelmnt['Occultations']['Event']['Elements'].split(',')
                            star = eventOccelmnt['Occultations']['Event']['Star'].split(',')
                            object_data = eventOccelmnt['Occultations']['Event']['Object'].split(',')
                            owcloudurl = 'https://cloud.occultwatcher.net' + eventOccelmnt['Occultations']['Event']['OWC']
                            object_no = object_data[0] if len(object_data) > 0 else ""
                            
                            # Extract additional Occelmnt fields for OBS.XML
                            # Star data (16 fields)
                            if len(star) >= 16:
                                occelmnt_data['star_identifier'] = star[0]
                                occelmnt_data['star_ra_j2000'] = star[1]  # decimal hours
                                occelmnt_data['star_dec_j2000'] = star[2]  # decimal degrees
                                occelmnt_data['star_mag_b'] = star[3]
                                occelmnt_data['star_mag_v'] = star[4]
                                occelmnt_data['star_mag_r'] = star[5]
                                occelmnt_data['star_diameter_mas'] = star[6]
                                occelmnt_data['star_double_flag'] = star[7]
                                occelmnt_data['star_k2_flag'] = star[8]
                                occelmnt_data['star_ra_apparent'] = star[9]  # decimal hours
                                occelmnt_data['star_dec_apparent'] = star[10]  # decimal degrees
                                occelmnt_data['star_mag_drops_adjusted'] = star[11]
                                occelmnt_data['star_bright_nearby_count'] = star[12]
                                occelmnt_data['star_total_nearby_count'] = star[13]
                                occelmnt_data['star_unknown_14'] = star[14]
                                occelmnt_data['star_unknown_15'] = star[15]
                            
                            # Object data (15 fields)
                            if len(object_data) >= 15:
                                occelmnt_data['object_number'] = object_data[0]
                                occelmnt_data['object_name'] = object_data[1]
                                occelmnt_data['object_magnitude'] = object_data[2]  # Asteroid magnitude
                                occelmnt_data['object_diameter_km'] = object_data[3]
                                occelmnt_data['object_distance_au'] = object_data[4]
                                occelmnt_data['object_rings'] = object_data[5]
                                occelmnt_data['object_moons'] = object_data[6]
                                occelmnt_data['object_dra'] = object_data[7]  # s/hr
                                occelmnt_data['object_ddec'] = object_data[8]  # arcsec/hr
                                occelmnt_data['object_taxonomic_class'] = object_data[9]
                                occelmnt_data['object_diameter_uncertainty'] = object_data[10]
                                occelmnt_data['object_moon_shadow_flag'] = object_data[11]
                                occelmnt_data['object_mag_v'] = object_data[12]  # V magnitude
                                occelmnt_data['object_mag_r'] = object_data[13]  # R magnitude
                                occelmnt_data['object_unknown_14'] = object_data[14]
                            
                            # Elements data (14 fields) - ACTUAL FORMAT from real data
                            # Index 0: Source/ephemeris string (e.g., "JPL#29:2025-02-13@2025-12-30[OWC]")
                            # Index 1: Duration in seconds
                            # Indices 2-5: Event date/time (year, month, day, hours)
                            # Indices 6-7: Shadow X, Y coordinates at closest approach (Earth radii)
                            # Indices 8-9: First-order motion coefficients dX, dY (Earth radii/hr)
                            # Indices 10-11: Second-order coefficients d2X, d2Y (Earth radii/hr²)
                            # Indices 12-13: Third-order coefficients d3X, d3Y (Earth radii/hr³)
                            if len(elements) >= 14:
                                occelmnt_data['event_ephemeris_source'] = elements[0]
                                occelmnt_data['event_duration_sec'] = elements[1]
                                occelmnt_data['event_year'] = elements[2]
                                occelmnt_data['event_month'] = elements[3]
                                occelmnt_data['event_day'] = elements[4]
                                occelmnt_data['event_hours'] = elements[5]
                                occelmnt_data['motion_x'] = elements[6]
                                occelmnt_data['motion_y'] = elements[7]
                                occelmnt_data['motion_dx'] = elements[8]
                                occelmnt_data['motion_dy'] = elements[9]
                                occelmnt_data['motion_d2x'] = elements[10]
                                occelmnt_data['motion_d2y'] = elements[11]
                                occelmnt_data['motion_d3x'] = elements[12]
                                occelmnt_data['motion_d3y'] = elements[13]
                            
                            # Errors data (10 fields) - optional quality flags
                            try:
                                errors = eventOccelmnt['Occultations']['Event']['Errors'].split(',')
                                if len(errors) >= 10:
                                    occelmnt_data['error_path_width_unc'] = errors[0]  # Fraction of path width
                                    occelmnt_data['error_ellipse_major'] = errors[1]  # arcsec
                                    occelmnt_data['error_ellipse_minor'] = errors[2]  # arcsec
                                    occelmnt_data['error_ellipse_pa'] = errors[3]  # degrees
                                    occelmnt_data['error_position_1sigma'] = errors[4]  # arcsec
                                    occelmnt_data['error_basis_description'] = errors[5]  # String
                                    occelmnt_data['quality_ruwe'] = errors[6]
                                    occelmnt_data['quality_duplicate_source'] = errors[7]
                                    occelmnt_data['quality_no_pm'] = errors[8]
                                    occelmnt_data['quality_ucac4_pm'] = errors[9]
                            except (KeyError, IndexError):
                                pass  # Errors section is optional
                            
                            # Earth data (5 fields) - optional observer geocentric position
                            try:
                                earth = eventOccelmnt['Occultations']['Event']['Earth'].split(',')
                                if len(earth) >= 5:
                                    occelmnt_data['earth_x'] = earth[0]
                                    occelmnt_data['earth_y'] = earth[1]
                                    occelmnt_data['earth_z'] = earth[2]
                                    occelmnt_data['earth_vx'] = earth[3]
                                    occelmnt_data['earth_vy'] = earth[4]
                            except (KeyError, IndexError):
                                pass  # Earth section is optional
                            
                            # Orbit data (6 fields) - optional orbital elements
                            try:
                                orbit = eventOccelmnt['Occultations']['Event']['Orbit'].split(',')
                                if len(orbit) >= 6:
                                    occelmnt_data['orbit_a'] = orbit[0]
                                    occelmnt_data['orbit_e'] = orbit[1]
                                    occelmnt_data['orbit_i'] = orbit[2]
                                    occelmnt_data['orbit_node'] = orbit[3]
                                    occelmnt_data['orbit_peri'] = orbit[4]
                                    occelmnt_data['orbit_m'] = orbit[5]
                            except (KeyError, IndexError):
                                pass  # Orbit section is optional
                            
                        except (KeyError, IndexError, AttributeError) as e:
                            print(f"Warning: Error parsing Occelmnt data for event {eventId}: {e}")
                            # Keep default values (empty strings and dict)

                    # Prefer star identifier from occelmnt over OWC StarName (fallback)
                    if occelmnt_data.get('star_identifier'):
                        star_id = occelmnt_data['star_identifier']

                    # Calculate exposure using config values
                    mag_ref = config.get_mag_for_40ms_exposure()
                    extinction_mag = min(2, -0.5 + 0.5/math.cos((90-starAlt)*2*math.pi/360))
                    exposure = round(max(40, 40 * pow(2, round(combMag + extinction_mag - mag_ref + 0.5, 0)))/20)*20/1000.0

                    # Use elevation from OW Cloud station fields.
                    # Preferred order: Elevation, Altitude, Height.
                    # Use None when not found so callers can trigger a lookup.
                    elevation = None
                    raw_elevation = station.get('Elevation')
                    if raw_elevation in (None, ""):
                        raw_elevation = station.get('Altitude')
                    if raw_elevation in (None, ""):
                        raw_elevation = station.get('Height')

                    try:
                        if raw_elevation not in (None, ""):
                            elevation = float(raw_elevation)
                    except Exception:
                        elevation = None

                    # Use cached geocoded location name (by lat/lon) or lookup if needed.
                    # Also use cached elevation as fallback when OWCloud returns none.
                    obs_location = ""
                    try:
                        cache_key = (round(float(latitude), 6), round(float(longitude), 6))
                        if cache_key in geocode_cache:
                            cached_geo = geocode_cache.get(cache_key, {})
                            obs_location = str(cached_geo.get('obs_location', '') or '')
                            # Use cached elevation if OWCloud did not supply one.
                            if elevation is None:
                                cached_elev = cached_geo.get('elevation')
                                if cached_elev:
                                    elevation = float(cached_elev)
                        else:
                            if debug_enabled:
                                print("Performing location lookup for station: {}".format(stationName))

                            # Lookup observing location (city/town)
                            loc_result = get_location_name_from_coordinates(
                                latitude,
                                longitude,
                                verbose=debug_enabled
                            )
                            if loc_result is not None:
                                obs_location = str(loc_result)
                                if debug_enabled:
                                    print("  Observing location: {}".format(obs_location))
                            else:
                                if debug_enabled:
                                    print("  Location lookup failed, using empty string")

                            geocode_cache[cache_key] = {
                                'obs_location': obs_location,
                                'elevation': elevation,  # may be None
                            }
                    except Exception as ex:
                        if debug_enabled:
                            print("  Error during location lookup: {}".format(ex))
                        # Keep default values (0.0 and empty string)

                    # Create dictionary of occultation events
                    occultation = {
                        'name': name + ' - ' + stationName, 
                        'station_name': stationName,
                        'owc_station_id': owc_station_id,
                        'ow_eventid': eventId, 
                        'id': name + ' : ' + star_id + ' : ' + stationName,
                        'ra': ra, 'dec': dec,
                        'star_mag': starMag, 'mag_drop': magDrop, 'comb_mag': combMag,
                        'event_time': eventCenterTime, 'start_time': startTime, 'end_time': endTime, 'goto_time': gotoTime,
                        'event_duration': eventDuration, 'event_uncertainty': eventUncertainty, 'recording_duration': recording_duration,
                        'occelmnt': eventOccelmnt, 'source': 'OWCloud',
                        'latitude': latitude, 'longitude': longitude, 'star_az': starAz, 'star_alt': starAlt,
                        'star_id': star_id, 'object_no': object_no, 'object_name': name, 'exposure': exposure,
                        'elevation': elevation, 'obs_location': obs_location
                    }
                    
                    # Add Occelmnt data fields if available
                    if occelmnt_data:
                        occultation['occelmnt_data'] = occelmnt_data
                    
                    if owcloudurl:
                        occultation['owcloudurl'] = owcloudurl
                        token = EventProcessor._extract_owc_event_token_from_url(owcloudurl)
                        if token:
                            occultation['ow_api_eventid'] = token

                    occultations.append(occultation)

        return occultations

class OccultationEvent:
    """Represents a single occultation event with all calculations"""
    
    def __init__(self, event_data, config):
        self.config = config
        self.original_data = event_data
        self.selected = True
        self.custom_exposure = None  # Track custom exposure settings
        self.custom_gain = None  # Track custom gain settings
        self.custom_recording_duration = None  # Track custom recording duration override
        self._parse_event_data(event_data)
        self._calculate_derived_values()
    
    def _parse_event_data(self, data):
        """Parse event data from OW Cloud JSON format"""
        debug_enabled = False
        try:
            debug_enabled = bool(self.config.get_output_debug_logs())
        except Exception:
            debug_enabled = False

        if debug_enabled:
            import os
            module_dir = os.path.dirname(os.path.abspath(__file__))
            debug_log = os.path.join(module_dir, "owc_data_debug.log")
            try:
                with open(debug_log, 'a', encoding='utf-8') as f:
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
            except Exception:
                pass  # Silently ignore debug logging errors
        
        self.name = data.get('name', '')
        self.station_name = data.get('station_name', '')
        self.owc_station_id = data.get('owc_station_id', None)
        self.ow_eventid = data.get('ow_eventid', '')
        self.ow_api_eventid = data.get('ow_api_eventid', '')
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
        
        # Load geocoded data (elevation and observing location)
        # Use get with defaults for backwards compatibility with old event files.
        # None means elevation was never retrieved and a lookup should be triggered.
        raw_elev = data.get('elevation')
        if raw_elev is None:
            self.elevation = None
        else:
            try:
                self.elevation = float(raw_elev)
            except (ValueError, TypeError):
                self.elevation = None
        
        self.obs_location = str(data.get('obs_location', '')) if data.get('obs_location') else ''
        
        self.source = data.get('source', '')
        self.owcloudurl = data.get('owcloudurl', '')
        self.owc_report_status = data.get('owc_report_status', '')
        self.status = data.get('status', '')
        
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
            
            # Calculate gain value
            if self.custom_gain is not None:
                # Use custom gain if set
                self.gain_value = int(self.custom_gain)
            else:
                # Use default gain from config
                self.gain_value = int(self.config.get_default_gain())
            
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

            # Calculate recording duration
            if self.custom_recording_duration is not None:
                # Use custom recording duration if set
                self.recording_duration = int(self.custom_recording_duration)
            else:
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
    
    def get_gain(self):
        """Get gain value for template substitution"""
        return self.gain_value
    
    def has_custom_exposure(self):
        """Check if event has custom exposure setting"""
        return self.custom_exposure is not None
    
    def set_custom_gain(self, gain_value):
        """Set a custom gain override for this event"""
        self.custom_gain = int(gain_value)
        self.gain_value = int(gain_value)
    
    def has_custom_gain(self):
        """Check if this event has a custom gain override"""
        return self.custom_gain is not None
    
    def set_custom_recording_duration(self, duration_seconds):
        """Set a custom recording duration override for this event"""
        self.custom_recording_duration = int(duration_seconds)
        # Recalculate times based on new duration
        self._calculate_derived_values()
    
    def has_custom_recording_duration(self):
        """Check if this event has a custom recording duration override"""
        return self.custom_recording_duration is not None
    
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
        # If this event has been reported to OWC, show the reported result in the grid.
        status_value = str(getattr(self, 'owc_report_status', '') or '').strip()
        if status_value:
            status_map = {
                'Positive': 'Positive',
                'Miss': 'Miss',
                'Negative': 'Miss',
                'NotObserved': 'No Obs',
                'Failed': 'Failed',
                'Clouded': 'Clouded',
                'CloudedOut': 'Clouded',
            }
            return status_map.get(status_value, status_value)

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
    
    def set_elevation(self, elevation):
        """Set elevation value for the event"""
        try:
            self.elevation = float(elevation) if elevation is not None else 0.0
        except (ValueError, TypeError):
            self.elevation = 0.0
    
    def get_elevation(self):
        """Get elevation value for the event"""
        return getattr(self, 'elevation', 0.0)
    
    def set_obs_location(self, obs_location):
        """Set observing location (city/town) for the event"""
        self.obs_location = str(obs_location) if obs_location else ''
    
    def get_obs_location(self):
        """Get observing location (city/town) for the event"""
        return getattr(self, 'obs_location', '')
    
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
        """Load events from saved JSON files - uses occultations.json (merged history)"""
        # Load from occultations.json which contains the full merged history
        events_data = EventProcessor.load_occultations(self.config.get_occultations_file(), self.config)
        
        if events_data:
            self.all_events = [OccultationEvent(event, self.config) for event in events_data]
            self.events = self.all_events[:]
            self.sort_events()
            return True
        return False
    
    def download_events_from_cloud(self, progress_callback=None):
        """Download events from OW Cloud"""
        try:
            # This downloads, merges with existing, and saves to occultations.json
            events_data = self.event_processor.update_ow_cloud_events(progress_callback=progress_callback)
            if events_data:
                # Load the merged file (occultations.json) instead of just the latest
                # This ensures retention policy has been applied
                merged_events = EventProcessor.load_occultations(self.config.get_occultations_file(), self.config)
                if merged_events:
                    self.all_events = [OccultationEvent(event, self.config) for event in merged_events]
                    self.events = self.all_events[:]
                    self.sort_events()
                    return len(events_data)
            return 0
        except Exception as e:
            print(f"Error downloading events: {e}")
            raise
    
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

    def save_event_location(self, event):
        """Persist updated latitude/longitude/elevation/obs_location back to occultations.json."""
        try:
            events_data = EventProcessor.load_occultations(
                self.config.get_occultations_file(), self.config)
            if not events_data:
                return False
            for entry in events_data:
                if entry.get('id') == event.event_id:
                    entry['latitude'] = event.latitude
                    entry['longitude'] = event.longitude
                    entry['elevation'] = event.elevation
                    entry['obs_location'] = event.obs_location
                    break
            EventProcessor.save_occultations(
                events_data, self.config.get_occultations_file(), self.config)
            return True
        except Exception as ex:
            print('Warning: could not save event location: {0}'.format(ex))
            return False

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
                self.selected_events.discard(event)
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
    
    def delete_events(self, events_to_delete):
        """
        Delete events from both JSON files and internal lists
        
        Args:
            events_to_delete: List of OccultationEvent objects to delete
        
        Returns:
            Number of events deleted
        """
        if not events_to_delete:
            return 0
        
        try:
            # Get unique_ids of events to delete
            # Use original_data to get the exact unique_id from the JSON
            delete_ids = set()
            for event in events_to_delete:
                # Try to get unique_id from original_data, fallback to event_id
                # Handle None or empty string properly
                unique_id = event.original_data.get('unique_id') or event.event_id
                if unique_id:
                    delete_ids.add(unique_id)
            
            if not delete_ids:
                return 0
            
            # Helper function to extract event ID (unique_id or id, handling None/empty)
            def get_event_id(event_dict):
                """Extract unique_id or id from event dictionary, handling None/empty strings"""
                return event_dict.get('unique_id') or event_dict.get('id') or ''
            
            # Delete from occultations.json (main file)
            occultations_file = self.config.get_occultations_file()
            occultations_data = EventProcessor.load_occultations(occultations_file, self.config)
            if occultations_data:
                occultations_data = [e for e in occultations_data if get_event_id(e) not in delete_ids]
                EventProcessor.save_occultations(occultations_data, occultations_file, self.config)
            
            # Delete from occultations_latest.json
            latest_file = self.config.get_latest_occultations_file()
            latest_data = EventProcessor.load_occultations(latest_file, self.config)
            if latest_data:
                latest_data = [e for e in latest_data if get_event_id(e) not in delete_ids]
                EventProcessor.save_occultations(latest_data, latest_file, self.config)
            
            # Update internal lists and count actual removals
            original_count = len(self.all_events)
            self.all_events = [e for e in self.all_events if e not in events_to_delete]
            self.events = [e for e in self.events if e not in events_to_delete]
            deleted_count = original_count - len(self.all_events)
            
            # Clear deleted events from selected_events
            for event in events_to_delete:
                self.selected_events.discard(event)
            
            return deleted_count
            
        except Exception as e:
            print("Error deleting events: {}".format(e))
            return 0