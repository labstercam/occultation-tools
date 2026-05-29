"""
T5 -- Live report submission test
==================================
Submits a REAL report to OWC for a known past event.
**This makes a live HTTP POST to cloud.occultwatcher.net.**

Event:  (112765) 2002 PR155  [2026-05-25]
        ow_eventid = 0c05b60f-79dd-43fe-b155-5bef78617301

Run from SharpCap console:
    exec(open(r'C:\\path\\to\\test_owc_report_submit_live.py').read())
Or directly from the python/ folder:
    exec(open('test_owc_report_submit_live.py').read())
"""

import os
import sys
import json
import datetime

# ---------------------------------------------------------------------------
# Locate script directory for relative imports and log output
# ---------------------------------------------------------------------------
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _script_dir = os.getcwd()

if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)

from config import ConfigManager
from events import EventProcessor

# ---------------------------------------------------------------------------
# Test constants  -- edit TEST_EVENT_ID if you want a different event
# ---------------------------------------------------------------------------
TEST_EVENT_ID   = '0c05b60f-79dd-43fe-b155-5bef78617301'
TEST_STATION_ID = 1
TEST_OBS_TYPE   = 'Negative'
TEST_COMMENT    = 'Automated test from OM'

# Live OM events data (lat/lon/elev source)
LIVE_EVENTS_FILE = r'C:\Users\AstroPC\Documents\SharpCap\occultation-manager\data\events\occultations.json'

# Fallback location if event data file is missing or event is not found.
TEST_LATITUDE   = -36.83541
TEST_LONGITUDE  = 174.65790
TEST_ELEVATION  = None
# update_location is False -- location fields are included in the dict
# but will NOT be sent to the server unless update_location=True
UPDATE_LOCATION = False

LOG_FILE = os.path.join(_script_dir, 'owc_report_submit_live_test.log')

# ---------------------------------------------------------------------------
# Logging helper
# ---------------------------------------------------------------------------
_log_lines = []

def _log(msg):
    ts = datetime.datetime.now().strftime('%H:%M:%S')
    line = '[{0}] {1}'.format(ts, msg)
    print(line)
    _log_lines.append(line)

def _save_log():
    with open(LOG_FILE, 'w') as fh:
        fh.write('\n'.join(_log_lines) + '\n')
    print('Log saved: {0}'.format(LOG_FILE))


def _load_live_event_location(event_id):
    """Load latitude/longitude/elevation for event_id from live OM events file."""
    if not os.path.exists(LIVE_EVENTS_FILE):
        return None
    try:
        with open(LIVE_EVENTS_FILE, 'r') as fh:
            data = json.load(fh)
    except Exception:
        return None
    if not isinstance(data, list):
        return None

    for row in data:
        if not isinstance(row, dict):
            continue
        if str(row.get('ow_eventid', '')) != str(event_id):
            continue
        return {
            'latitude': row.get('latitude', None),
            'longitude': row.get('longitude', None),
            'elevation': row.get('elevation', None),
            'owcloudurl': row.get('owcloudurl', None),
        }
    return None

# ---------------------------------------------------------------------------
# Main test function
# ---------------------------------------------------------------------------
def run():
    _log('=== T5: Live OWC Report Submission ===')
    _log('')
    _log('*** WARNING: This script makes a REAL HTTP POST to OWC. ***')
    _log('*** The observation will be recorded against your account. ***')
    _log('')

    # ------------------------------------------------------------------
    # Step 1 -- Load config and confirm API key is present
    # ------------------------------------------------------------------
    _log('Step 1: Loading config...')
    try:
        LIVE_CONFIG_FOLDER = r'C:\Users\AstroPC\Documents\SharpCap\occultation-manager\data\config'
        config = ConfigManager(config_folder=LIVE_CONFIG_FOLDER)
        api_key = config.get_api_key()
        report_url = config.get_report_observation_url()
        if not api_key:
            _log('  FAIL: No API key configured. Aborting.')
            _save_log()
            return
        _log('  Config folder:  {0}'.format(LIVE_CONFIG_FOLDER))
        _log('  API key present: {0}...'.format(str(api_key)[:8]))
        _log('  Report URL: {0}'.format(report_url))
    except Exception as ex:
        _log('  FAIL loading config: {0}'.format(ex))
        _save_log()
        return

    # ------------------------------------------------------------------
    # Step 2 -- Build the event dict (mirrors what process_owc_events
    #           would produce for a v2-downloaded event)
    # ------------------------------------------------------------------
    _log('')
    _log('Step 2: Building event dict...')
    live_loc = _load_live_event_location(TEST_EVENT_ID)
    if live_loc:
        lat = live_loc.get('latitude', TEST_LATITUDE)
        lon = live_loc.get('longitude', TEST_LONGITUDE)
        elev = live_loc.get('elevation', TEST_ELEVATION)
        live_owc_url = live_loc.get('owcloudurl', None)
        _log('  Loaded lat/lon/elev from live events file')
    else:
        lat = TEST_LATITUDE
        lon = TEST_LONGITUDE
        elev = TEST_ELEVATION
        live_owc_url = None
        _log('  Live events file lookup failed; using fallback lat/lon/elev')

    if not live_owc_url:
        live_owc_url = 'https://cloud.occultwatcher.net/event/1970-112765-227447-646540-U081512/3635675'

    event = {
        'ow_eventid':     TEST_EVENT_ID,
        'owc_station_id': TEST_STATION_ID,
        'latitude':       lat,
        'longitude':      lon,
        'elevation':      elev,
        'owcloudurl':     live_owc_url,
    }
    _log('  ow_eventid:     {0}'.format(event['ow_eventid']))
    _log('  owc_station_id: {0}'.format(event['owc_station_id']))
    _log('  latitude:       {0}'.format(event['latitude']))
    _log('  longitude:      {0}'.format(event['longitude']))
    _log('  elevation:      {0}'.format(event['elevation']))
    _log('  observation:    {0}'.format(TEST_OBS_TYPE))
    _log('  comment:        {0}'.format(TEST_COMMENT))
    _log('  update_location:{0}'.format(UPDATE_LOCATION))

    # ------------------------------------------------------------------
    # Step 3 -- Log the outgoing request, then submit
    # ------------------------------------------------------------------
    _log('')
    _log('Step 3: Submitting report to OWC...')
    REPORT_CODES = {'NotReported':0,'Miss':1,'Negative':1,'Clouded':2,
                    'Failed':3,'Positive':4,'NotObserved':5,'NotReduced':6}
    _payload = {
        'eventId':   TEST_EVENT_ID,
        'stationId': TEST_STATION_ID,
        'report':    REPORT_CODES[TEST_OBS_TYPE],
        'comment':   TEST_COMMENT,
    }
    _log('  POST {0}'.format(config.get_report_observation_url()))
    _log('  Headers: OW-ApiKey: {0}...'.format(str(config.get_api_key())[:8]))
    _log('  Body: {0}'.format(json.dumps(_payload)))
    try:
        result = EventProcessor.submit_owc_report(
            config,
            event,
            observation_type=TEST_OBS_TYPE,
            comment=TEST_COMMENT,
            duration_s=None,
            update_location=UPDATE_LOCATION
        )
    except Exception as ex:
        _log('  EXCEPTION during submit: {0}'.format(ex))
        _save_log()
        return

    # ------------------------------------------------------------------
    # Step 4 -- Display result
    # ------------------------------------------------------------------
    _log('')
    _log('Step 4: Result:')
    _log('  success: {0}'.format(result.get('success')))
    _log('  auth_method:   {0}'.format(result.get('auth_method')))
    _log('  endpoint_used: {0}'.format(result.get('endpoint_used')))
    attempted_calls = result.get('attempted_calls') or []
    if attempted_calls:
        _log('  attempted_calls:')
        for idx, call in enumerate(attempted_calls):
            _log('    [{0}] auth_method:   {1}'.format(idx + 1, call.get('auth_method')))
            _log('    [{0}] endpoint_used: {1}'.format(idx + 1, call.get('endpoint_used')))
            _log('    [{0}] outcome:       {1}'.format(idx + 1, call.get('outcome')))
            if call.get('status') is not None:
                _log('    [{0}] status:        {1}'.format(idx + 1, call.get('status')))
            if call.get('reason'):
                _log('    [{0}] reason:        {1}'.format(idx + 1, call.get('reason')))
            if call.get('headers') is not None:
                _log('    [{0}] headers:       {1}'.format(idx + 1, json.dumps(call.get('headers'))))
            if call.get('body') is not None:
                _log('    [{0}] body:          {1}'.format(idx + 1, json.dumps(call.get('body'))))
            if call.get('response_body'):
                _log('    [{0}] response_body: {1}'.format(idx + 1, call.get('response_body')))
    if result.get('error'):
        _log('  error:   {0}'.format(result['error']))
    response = result.get('response')
    if response is None:
        _log('  response: (empty / HTTP 204)')
    else:
        try:
            pretty = json.dumps(response, indent=2)
            for line in pretty.splitlines():
                _log('  ' + line)
        except Exception:
            _log('  response: {0}'.format(response))

    _log('')
    if result.get('success'):
        _log('T5 PASS -- report submitted successfully.')
    else:
        _log('T5 FAIL -- see error above.')

    _save_log()


run()
