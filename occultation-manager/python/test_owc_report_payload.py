"""
test_owc_report_payload.py
==========================
T4 — Report payload dry-run.

Verifies that submit_owc_report() builds the correct JSON payload for each
observation type WITHOUT making any HTTP request to OWC.

Run from the SharpCap IronPython console:

    exec(open(r'C:\<path-to>\occultation-manager\python\test_owc_report_payload.py').read())

Or import and call:

    import test_owc_report_payload; test_owc_report_payload.run()

Output goes to the console AND to:
    owc_report_payload_test.log  (same folder as this script)

Compatibility: IronPython 3.4 — no f-strings, no pathlib, no typing, no numpy.
"""

import os
import sys
import json
import datetime
import traceback

try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _script_dir = os.getcwd()

from config import ConfigManager
from events import EventProcessor


# ---------------------------------------------------------------------------
# Tee writer
# ---------------------------------------------------------------------------
class _Tee(object):
    def __init__(self, filepath):
        self._file = open(filepath, 'w', encoding='utf-8')

    def write(self, text):
        print(text)
        self._file.write(text + '\n')

    def close(self):
        try:
            self._file.close()
        except Exception:
            pass


def _section(tee, title):
    tee.write('')
    tee.write('=' * 70)
    tee.write('  ' + title)
    tee.write('=' * 70)


def _subsection(tee, title):
    tee.write('')
    tee.write('-' * 60)
    tee.write('  ' + title)
    tee.write('-' * 60)


# ---------------------------------------------------------------------------
# Mirrors submit_owc_report payload construction — no HTTP call made
# ---------------------------------------------------------------------------
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


def _build_payload(event, observation_type, comment='',
                   duration_s=None, update_location=False):
    """Replicate submit_owc_report payload logic without the HTTP call.

    Returns (payload_dict, error_string).  error_string is None on success.
    """
    if isinstance(event, dict):
        event_id   = event.get('ow_eventid')
        station_id = event.get('owc_station_id')
        latitude   = event.get('latitude')
        longitude  = event.get('longitude')
        elevation  = event.get('elevation')
    else:
        event_id   = getattr(event, 'ow_eventid',    None)
        station_id = getattr(event, 'owc_station_id', None)
        latitude   = getattr(event, 'latitude',      None)
        longitude  = getattr(event, 'longitude',     None)
        elevation  = getattr(event, 'elevation',     None)

    if not event_id:
        return None, 'No ow_eventid on event'
    if station_id is None:
        return None, 'No owc_station_id — event needs re-downloading with current version'

    report_code = REPORT_CODES.get(observation_type)
    if report_code is None:
        return None, 'Unknown observation_type: ' + str(observation_type)

    payload = {
        'eventId':   str(event_id),
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

    return payload, None


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------

def run():
    config = ConfigManager()

    log_path = os.path.join(_script_dir, 'owc_report_payload_test.log')
    tee = _Tee(log_path)

    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    _section(tee, 'T4 — OWC Report Payload Dry-Run')
    tee.write('  Run at:    ' + timestamp)
    tee.write('  Log file:  ' + log_path)
    tee.write('  POST URL:  ' + config.get_report_observation_url())
    tee.write('')
    tee.write('  NOTE: No HTTP requests are made in this test.')

    # -----------------------------------------------------------------------
    # STEP 1 — Load a saved event
    # -----------------------------------------------------------------------
    _section(tee, 'STEP 1 — Load saved event from occultations file')

    events_path = config.get_full_file_path(config.get_occultations_file())
    tee.write('  File: ' + events_path)

    saved_events = []
    try:
        with open(events_path, 'r', encoding='utf-8') as f:
            saved_events = json.load(f)
        tee.write('  Total saved events: ' + str(len(saved_events)))
    except Exception as ex:
        tee.write('  FAILED to load: ' + str(ex))
        tee.write(traceback.format_exc())
        tee.write('')
        tee.write('  Cannot continue without saved events.')
        tee.close()
        return

    # Prefer an event that already has owc_station_id set (Task 2 data)
    sample = None
    for ev in saved_events:
        if ev.get('owc_station_id') is not None:
            sample = ev
            break

    placeholder_used = False
    if sample is None:
        tee.write('')
        tee.write('  WARNING: No event with owc_station_id found.')
        tee.write('  This means events were saved before Task 2 was implemented.')
        tee.write('  Re-download events from OWC to populate owc_station_id.')
        tee.write('  Using first event with a placeholder station_id of 1 for dry-run.')
        if saved_events:
            sample = dict(saved_events[0])   # copy so we don't mutate
            sample['owc_station_id'] = 1
            placeholder_used = True
        else:
            tee.write('  No saved events at all — cannot continue.')
            tee.close()
            return

    tee.write('')
    tee.write('  Selected event:')
    tee.write('    object_name:   ' + str(sample.get('object_name', '')))
    tee.write('    ow_eventid:    ' + str(sample.get('ow_eventid', '')))
    tee.write('    station_name:  ' + str(sample.get('station_name', '')))
    tee.write('    owc_station_id:' + str(sample.get('owc_station_id', '')) +
              ('  (PLACEHOLDER)' if placeholder_used else ''))
    tee.write('    event_time:    ' + str(sample.get('event_time', '')))
    tee.write('    latitude:      ' + str(sample.get('latitude', '')))
    tee.write('    longitude:     ' + str(sample.get('longitude', '')))
    tee.write('    elevation:     ' + str(sample.get('elevation', '')))

    # -----------------------------------------------------------------------
    # STEP 2 — Payload for each observation type
    # -----------------------------------------------------------------------
    _section(tee, 'STEP 2 — Payload for each observation_type')

    test_cases = [
        ('Negative',    {},                           'Standard negative report'),
        ('Positive',    {'duration_s': 1.5,
                         'comment': 'Clean D and R'},  'Positive with duration and comment'),
        ('Clouded',     {},                           'Clouded out'),
        ('Failed',      {'comment': 'Equipment failure'}, 'Failed with comment'),
        ('NotObserved', {},                           'Not observed'),
        ('NotReduced',  {},                           'Not yet reduced'),
    ]

    all_ok = True
    for obs_type, kwargs, label in test_cases:
        _subsection(tee, '{0} ({1})'.format(obs_type, label))
        payload, err = _build_payload(sample, obs_type, **kwargs)
        if err:
            tee.write('  ERROR: ' + err)
            all_ok = False
        else:
            tee.write(json.dumps(payload, indent=4))

    # -----------------------------------------------------------------------
    # STEP 3 — Payload with update_location=True
    # -----------------------------------------------------------------------
    _section(tee, 'STEP 3 — Payload with update_location=True (Negative)')

    payload, err = _build_payload(
        sample, 'Negative',
        comment='Test with location update',
        update_location=True
    )
    if err:
        tee.write('  ERROR: ' + err)
        all_ok = False
    else:
        tee.write(json.dumps(payload, indent=4))
        tee.write('')
        if 'updateLocation' not in payload:
            tee.write('  NOTE: updateLocation not in payload — latitude/longitude may be missing on this event.')
        else:
            tee.write('  latDeg:       ' + str(payload.get('latDeg')))
            tee.write('  lngDeg:       ' + str(payload.get('lngDeg')))
            if 'altMslMeters' in payload:
                tee.write('  altMslMeters: ' + str(payload['altMslMeters']) + '  (elevation present)')
            else:
                tee.write('  altMslMeters: MISSING — elevation not set on this event (check saved occultation dict)')

    # -----------------------------------------------------------------------
    # STEP 4 — Validate REPORT_CODES matches submit_owc_report
    # -----------------------------------------------------------------------
    _section(tee, 'STEP 4 — Validate REPORT_CODES match between test and implementation')

    impl_source = None
    try:
        import inspect
        impl_source = inspect.getsource(EventProcessor.submit_owc_report)
    except Exception:
        pass

    if impl_source is None:
        tee.write('  SKIPPED — could not read submit_owc_report source (inspect unavailable)')
    else:
        mismatches = []
        for k, v in REPORT_CODES.items():
            expected_line = "'{0}':".format(k)
            if expected_line not in impl_source:
                mismatches.append(k)
            else:
                # Check value too — find the line and extract the number
                for line in impl_source.splitlines():
                    if expected_line in line:
                        try:
                            impl_val = int(line.split(':')[1].strip().rstrip(','))
                            if impl_val != v:
                                mismatches.append(
                                    '{0} (test={1}, impl={2})'.format(k, v, impl_val)
                                )
                        except Exception:
                            pass
                        break

        if mismatches:
            tee.write('  MISMATCHES FOUND: ' + str(mismatches))
            all_ok = False
        else:
            tee.write('  All {0} report codes match submit_owc_report implementation.'.format(
                len(REPORT_CODES)))

    # -----------------------------------------------------------------------
    # Done
    # -----------------------------------------------------------------------
    _section(tee, 'T4 DRY-RUN ' + ('PASSED' if all_ok else 'COMPLETED WITH ISSUES'))
    tee.write('  Target URL (no request sent): ' + config.get_report_observation_url())
    tee.write('  Log written to: ' + log_path)
    tee.write('')
    tee.close()


run()
