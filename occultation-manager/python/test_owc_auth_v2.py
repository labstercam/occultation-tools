"""
test_owc_auth_v2.py
===================
OWC API v2 authentication comparison test.

Run directly from the SharpCap IronPython console:

    exec(open(r'C:\<path-to>\occultation-manager\python\test_owc_auth_v2.py').read())

Or import and call:

    import test_owc_auth_v2; test_owc_auth_v2.run()

Output goes to the console AND to:
    owc_auth_v2_test.log  (same folder as this script)

Compatibility: IronPython 3.4 — no f-strings, no pathlib, no typing, no numpy.
"""

import os
import sys
import json
import datetime
import traceback

# ---------------------------------------------------------------------------
# Locate this script's directory so the log file lands beside the other
# debug logs (owc_raw_download.log, owc_data_debug.log).
# __file__ is available on import and script-run; under exec() it falls back
# to os.getcwd(), which SharpCap sets to the python/ folder at startup.
# ---------------------------------------------------------------------------
try:
    _script_dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _script_dir = os.getcwd()  # exec() fallback — relies on SharpCap cwd

from config import ConfigManager
from events import EventProcessor


# ---------------------------------------------------------------------------
# Tee writer — all output goes to console AND to the log file
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
# Helpers
# ---------------------------------------------------------------------------

def _safe_json_excerpt(obj, max_chars=400):
    """Return a truncated JSON string safe for console display."""
    try:
        s = json.dumps(obj, indent=2)
        if len(s) > max_chars:
            return s[:max_chars] + '\n  ... (truncated)'
        return s
    except Exception as ex:
        return '(could not serialise: {0})'.format(ex)


def _event_ids(raw_list):
    """Return sorted list of event IDs from a raw OWC response list."""
    ids = []
    for ev in raw_list:
        if isinstance(ev, dict):
            eid = ev.get('Id') or ev.get('id') or ev.get('EventId')
            if eid is not None:
                ids.append(str(eid))
    return sorted(ids)


def _own_station_events(raw_list):
    """Return only events that have at least one own-station entry."""
    result = []
    for ev in raw_list:
        if isinstance(ev, dict):
            stations = ev.get('Stations', [])
            if any(s.get('IsOwnStation') for s in stations):
                result.append(ev)
    return result


def _compare_event_dicts(tee, dict_v1, dict_v2, label_v1='V1', label_v2='V2'):
    """Compare two processed event dicts and report differences."""
    all_keys = sorted(set(list(dict_v1.keys()) + list(dict_v2.keys())))
    missing_in_v2 = []
    missing_in_v1 = []
    differ = []
    match = []

    for k in all_keys:
        in_v1 = k in dict_v1
        in_v2 = k in dict_v2
        if in_v1 and not in_v2:
            missing_in_v2.append(k)
        elif in_v2 and not in_v1:
            missing_in_v1.append(k)
        else:
            # Both present — compare values (skip heavy nested objects)
            v1 = dict_v1[k]
            v2 = dict_v2[k]
            if k in ('occelmnt', 'occelmnt_data'):
                tee.write('  {0!s:35s}  (skipped — complex nested object)'.format(k))
                continue
            try:
                same = (v1 == v2)
            except Exception:
                same = False
            if same:
                match.append(k)
            else:
                differ.append((k, v1, v2))

    tee.write('')
    tee.write('  Fields identical in both:  {0}'.format(len(match)))
    tee.write('  Fields with differences:   {0}'.format(len(differ)))
    tee.write('  In {0} only:               {1}'.format(label_v1, len(missing_in_v2)))
    tee.write('  In {0} only:               {1}'.format(label_v2, len(missing_in_v1)))

    if missing_in_v2:
        tee.write('')
        tee.write('  Keys present in {0} but MISSING in {1}:'.format(label_v1, label_v2))
        for k in missing_in_v2:
            tee.write('    - {0}'.format(k))

    if missing_in_v1:
        tee.write('')
        tee.write('  Keys present in {0} but MISSING in {1}:'.format(label_v2, label_v1))
        for k in missing_in_v1:
            tee.write('    + {0}'.format(k))

    if differ:
        tee.write('')
        tee.write('  Differing field values:')
        for k, v1, v2 in differ:
            tee.write('    {0!s:35s}'.format(k))
            tee.write('      {0}: {1!r}'.format(label_v1, str(v1)[:120]))
            tee.write('      {0}: {1!r}'.format(label_v2, str(v2)[:120]))


def _show_processed_event(tee, ev_dict, label):
    """Pretty-print the key fields of a processed event dict."""
    tee.write('')
    tee.write('  [{0}]'.format(label))
    skip = ('occelmnt', 'occelmnt_data')
    for k in sorted(ev_dict.keys()):
        if k in skip:
            tee.write('    {0!s:35s}  <complex object — omitted>'.format(k))
        else:
            tee.write('    {0!s:35s}  {1!r}'.format(k, str(ev_dict.get(k, ''))[:120]))


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------

def run():
    config = ConfigManager()
    api_key  = config.get_api_key()
    email    = config.get_owc_email()
    password = config.get_owc_password()

    log_path = os.path.join(_script_dir, 'owc_auth_v2_test.log')
    tee = _Tee(log_path)

    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')
    _section(tee, 'OWC API v2 Authentication Comparison Test')
    tee.write('  Run at: ' + timestamp)
    tee.write('  Log file: ' + log_path)
    tee.write('  Config host: ' + config.get_host())
    tee.write('  API key present: ' + ('YES' if api_key and len(api_key) > 10 else 'NO — check config'))
    tee.write('  Email: ' + email)

    # -----------------------------------------------------------------------
    # STEP 1 — Download using OLD method (URL param + Basic Auth)
    # -----------------------------------------------------------------------
    _section(tee, 'STEP 1 — Old method: URL apikey= param + Basic Auth')

    url_v1 = config.get_full_url()
    tee.write('  URL: ' + url_v1)
    raw_v1 = None
    try:
        raw_v1 = EventProcessor.get_owc_events(url_v1, email, password)
        tee.write('  Status: OK')
        tee.write('  Total events returned: ' + str(len(raw_v1)))
        own_v1 = _own_station_events(raw_v1)
        tee.write('  Own-station events: ' + str(len(own_v1)))
    except Exception as ex:
        tee.write('  Status: FAILED')
        tee.write('  Error: ' + str(ex))
        tee.write(traceback.format_exc())

    # -----------------------------------------------------------------------
    # STEP 2 — Download using NEW method (OW-ApiKey header only)
    # -----------------------------------------------------------------------
    _section(tee, 'STEP 2 — New method: OW-ApiKey header')

    url_v2 = config.get_base_url()
    tee.write('  URL: ' + url_v2)
    tee.write('  (no apikey= in URL — key sent as OW-ApiKey header)')
    raw_v2 = None
    try:
        raw_v2 = EventProcessor.get_owc_events_v2(url_v2, api_key)
        tee.write('  Status: OK')
        tee.write('  Total events returned: ' + str(len(raw_v2)))
        own_v2 = _own_station_events(raw_v2)
        tee.write('  Own-station events: ' + str(len(own_v2)))
    except Exception as ex:
        tee.write('  Status: FAILED')
        tee.write('  Error: ' + str(ex))
        tee.write(traceback.format_exc())

    # -----------------------------------------------------------------------
    # STEP 3 — Raw response comparison
    # -----------------------------------------------------------------------
    _section(tee, 'STEP 3 — Raw response comparison (event IDs)')

    if raw_v1 is None or raw_v2 is None:
        tee.write('  SKIPPED — one or both downloads failed')
    else:
        ids_v1 = _event_ids(raw_v1)
        ids_v2 = _event_ids(raw_v2)
        tee.write('  V1 event IDs ({0}): {1}'.format(len(ids_v1), ids_v1[:10]))
        tee.write('  V2 event IDs ({0}): {1}'.format(len(ids_v2), ids_v2[:10]))
        if len(ids_v1) > 10:
            tee.write('  (showing first 10 of {0})'.format(len(ids_v1)))

        only_v1 = [i for i in ids_v1 if i not in ids_v2]
        only_v2 = [i for i in ids_v2 if i not in ids_v1]

        if not only_v1 and not only_v2:
            tee.write('')
            tee.write('  RESULT: MATCH — both methods returned identical event IDs')
        else:
            tee.write('')
            tee.write('  RESULT: MISMATCH')
            if only_v1:
                tee.write('  In V1 only: ' + str(only_v1))
            if only_v2:
                tee.write('  In V2 only: ' + str(only_v2))

        if raw_v1 and raw_v2:
            _subsection(tee, 'First raw event — V1 (excerpt)')
            tee.write(_safe_json_excerpt(raw_v1[0]))
            _subsection(tee, 'First raw event — V2 (excerpt)')
            tee.write(_safe_json_excerpt(raw_v2[0]))

    # -----------------------------------------------------------------------
    # STEP 4 — Process both raw lists through process_owc_events()
    # -----------------------------------------------------------------------
    _section(tee, 'STEP 4 — process_owc_events() on both raw results')

    processed_v1 = []
    processed_v2 = []

    if raw_v1 is not None:
        _subsection(tee, 'Processing V1 result')
        try:
            processed_v1 = EventProcessor.process_owc_events(
                raw_v1, sitefilter='', config=config
            )
            tee.write('  Processed events: ' + str(len(processed_v1)))
        except Exception as ex:
            tee.write('  FAILED: ' + str(ex))
            tee.write(traceback.format_exc())

    if raw_v2 is not None:
        _subsection(tee, 'Processing V2 result')
        try:
            processed_v2 = EventProcessor.process_owc_events(
                raw_v2, sitefilter='', config=config
            )
            tee.write('  Processed events: ' + str(len(processed_v2)))
        except Exception as ex:
            tee.write('  FAILED: ' + str(ex))
            tee.write(traceback.format_exc())

    # -----------------------------------------------------------------------
    # STEP 5 — Show processed event dicts
    # -----------------------------------------------------------------------
    _section(tee, 'STEP 5 — Processed event dict inspection')

    if processed_v1:
        _subsection(tee, 'First processed event — V1 (all fields)')
        _show_processed_event(tee, processed_v1[0], 'V1 event[0]')
    else:
        tee.write('  No V1 processed events to show')

    if processed_v2:
        _subsection(tee, 'First processed event — V2 (all fields)')
        _show_processed_event(tee, processed_v2[0], 'V2 event[0]')
    else:
        tee.write('  No V2 processed events to show')

    # -----------------------------------------------------------------------
    # STEP 6 — Field-by-field diff of the first matching processed event
    # -----------------------------------------------------------------------
    _section(tee, 'STEP 6 — Processed event dict diff (V1 vs V2)')

    if not processed_v1 or not processed_v2:
        tee.write('  SKIPPED — one or both processed lists are empty')
    else:
        def _by_eid(lst):
            return {str(ev.get('ow_eventid', '')): ev for ev in lst}

        map_v1 = _by_eid(processed_v1)
        map_v2 = _by_eid(processed_v2)
        common = sorted(set(map_v1.keys()) & set(map_v2.keys()))
        only_in_v1 = sorted(set(map_v1.keys()) - set(map_v2.keys()))
        only_in_v2 = sorted(set(map_v2.keys()) - set(map_v1.keys()))

        tee.write('  Events in both:    ' + str(len(common)))
        tee.write('  Events in V1 only: ' + str(len(only_in_v1)))
        tee.write('  Events in V2 only: ' + str(len(only_in_v2)))

        if only_in_v1:
            tee.write('  V1-only event IDs: ' + str(only_in_v1))
        if only_in_v2:
            tee.write('  V2-only event IDs: ' + str(only_in_v2))

        if common:
            first_eid = common[0]
            _subsection(tee, 'Field diff for event ID: ' + first_eid)
            _compare_event_dicts(tee, map_v1[first_eid], map_v2[first_eid], 'V1', 'V2')

            if len(common) > 1:
                _subsection(tee, 'Summary diff for all {0} common events'.format(len(common)))
                total_diffs = 0
                for eid in common:
                    ev1 = map_v1[eid]
                    ev2 = map_v2[eid]
                    diff_keys = []
                    for k in set(list(ev1.keys()) + list(ev2.keys())):
                        if k in ('occelmnt', 'occelmnt_data'):
                            continue
                        try:
                            if ev1.get(k) != ev2.get(k):
                                diff_keys.append(k)
                        except Exception:
                            diff_keys.append(k)
                    if diff_keys:
                        total_diffs += 1
                        tee.write('  Event {0} ({1}):  {2} field(s) differ: {3}'.format(
                            eid,
                            str(ev1.get('object_name', ''))[:40],
                            len(diff_keys),
                            diff_keys,
                        ))
                if total_diffs == 0:
                    tee.write('  All {0} events: no differences found'.format(len(common)))

    # -----------------------------------------------------------------------
    # STEP 7 — Station field listing (useful for Task 2 planning)
    # -----------------------------------------------------------------------
    _section(tee, 'STEP 7 — Raw station field listing (V2 first own-station)')

    if raw_v2 is not None:
        found = False
        for ev in raw_v2:
            for st in ev.get('Stations', []):
                if st.get('IsOwnStation'):
                    tee.write('  Event: ' + str(ev.get('Object', '')) + '  Id=' + str(ev.get('Id', '')))
                    tee.write('  All station keys ({0}):'.format(len(st)))
                    for k in sorted(st.keys()):
                        tee.write('    {0!s:35s}  {1!r}'.format(k, str(st[k])[:80]))
                    found = True
                    break
            if found:
                break
        if not found:
            tee.write('  No own-station found in V2 response')
    else:
        tee.write('  SKIPPED — V2 download failed')

    # -----------------------------------------------------------------------
    # Done
    # -----------------------------------------------------------------------
    _section(tee, 'TEST COMPLETE')
    tee.write('  Log written to: ' + log_path)
    tee.write('')
    tee.close()


run()
