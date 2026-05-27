# OWC API v2 — Development Plan

**Date:** 2026-05-26  
**Source:** Emails from Hristo (see `owc_new_endpoints.md`)  
**Scope:** Three changes — header-based auth, submit report, retrieve event by EventID  
**Constraint:** All existing methods must be preserved intact; new code added alongside.

---

## 1. Current State

### Authentication
`config.get_full_url()` and `config.get_occelmnt_url()` append `?apikey=<key>` as a URL
query parameter. `EventProcessor.get_owc_events()` sends HTTP Basic Auth credentials as a
header in addition to the API key in the URL.

```python
# config.py — current
return base_url + sep + 'apikey=%s' % self.config['apiKey']

# events.py — current
credentials = f"{username}:{password}"
encoded_credentials = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
request.add_header("Authorization", f"Basic {encoded_credentials}")
```

### Event download
- `EventProcessor.get_owc_events(url, username, password, data=None)` — fetches any endpoint
- `EventProcessor.update_ow_cloud_events()` — downloads details-list, calls `process_owc_events`
- `process_owc_events()` iterates stations with `IsOwnStation == True`; calls the occelmnt
  endpoint per event; builds the `occultation` dict

### Station ID
The current station dict fields inspected in `process_owc_events` do **not** include a
numeric station ID. The `occultation` dict stores:
- `ow_eventid` — the OWC event ID string (used as key for occelmnt URL)
- `station_name` — the text station name
- **No `owc_station_id`** field

### Endpoints in use
| Purpose | Endpoint |
|---|---|
| Download events | `GET /api2/v1/events/details-list?apikey=…` |
| Download occelmnt | `GET /api2/v1/owc/event/my/{eventId}/occelmnts?apikey=…` |

---

## 2. New Capabilities (from Hristo)

### 2.1 Header-based authentication
Pass `OW-ApiKey: <key>` as an HTTP header. The URL `?apikey=` parameter no longer required.
Old method continues to work — no breaking change on the server side.

### 2.2 Submit observation report
```
POST https://www.occultwatcher.net/api2/v1/owc/report-observation
Content-Type: application/json
OW-ApiKey: <key>

{
    "eventId":  "<string>",
    "stationId": 0,
    "report":   4,
    "comment":  "optional text"
}
```

Report values:
| Value | Meaning |
|---|---|
| 0 | Not reported |
| 1 | Miss |
| 2 | Clouded out |
| 3 | Failed |
| 4 | Positive |
| 5 | Not observed |
| 6 | Not reduced |

Optional extra fields:
```json
{
    "duration": 0.0
}
```
(positive events only — duration in seconds)

```json
{
    "updateLocation": true,
    "latDeg":      0.0,
    "lngDeg":      0.0,
    "altMslMeters": 0.0
}
```
(all fields optional; `altMslMeters` may be omitted)

### 2.3 Retrieve event by EventID
```
GET https://www.occultwatcher.net/api2/v1/events/{EventID}
OW-ApiKey: <key>
```
Returns event details including station IDs. This is the mechanism to discover the integer
`stationId` needed for the report submission endpoint.

**Unknown at time of writing:** the exact JSON structure of the response, and whether
`stationId` is a zero-based integer index, a database row ID, or another format. Hristo
said it has been implemented. Inspection test (Task T3) will expose the raw response.

---

## 3. Implementation Plan

### Task 1 — Add header-based API call method (preserve old method)

**File:** `events.py`  
**Existing method:** `EventProcessor.get_owc_events(url, username, password, data=None)`  
**Action:** Add a new static method alongside it. Do **not** modify the existing method.

```python
@staticmethod
def get_owc_events_v2(url, api_key, data=None, method='GET'):
    """Call an OWC API endpoint using the OW-ApiKey header.

    This is the new preferred authentication method (header, not URL param).
    The old get_owc_events() method is preserved and still works.

    Args:
        url:     Full URL (without ?apikey= suffix)
        api_key: OWC API key string
        data:    Optional dict to send as JSON body (triggers POST if method not set)
        method:  HTTP method string ('GET' or 'POST'). Default 'GET'.

    Returns:
        Parsed JSON response (dict or list)
    """
    import urllib.request, json
    req = urllib.request.Request(url, method=method)
    req.add_header('OW-ApiKey', api_key)
    req.add_header('Content-Type', 'application/json')
    if data is not None:
        req.data = json.dumps(data).encode('utf-8')
    response = urllib.request.urlopen(req, timeout=20)
    return json.loads(response.read().decode('utf-8'))
```

**Config changes required:**  
`config.get_full_url()` and `config.get_occelmnt_url()` currently append the API key as a
URL parameter. Add two new methods that return the base URL **without** the key appended:

```python
# config.py — new methods (alongside existing)
def get_base_url(self):
    """Return the events list URL without apikey parameter."""
    return self.config['host'] + self.config['url_path']

def get_occelmnt_base_url(self):
    """Return the occelmnt URL template without apikey parameter."""
    return self.config['host'] + self.config['URL_OCCELMNT_ENDPOINT_PATH']

def get_report_observation_url(self):
    """Return the POST endpoint for reporting an observation."""
    return self.config['host'] + '/api2/v1/owc/report-observation'

def get_event_by_id_url(self, event_id):
    """Return the GET endpoint for fetching a single event by its OWC ID."""
    return self.config['host'] + '/api2/v1/events/' + str(event_id)
```

---

### Task 2 — Retrieve event by EventID and extract station ID

**File:** `events.py`  
**Action:** New static method. Does not replace anything.

```python
@staticmethod
def get_owc_event_by_id(event_id, api_key, host='https://www.occultwatcher.net'):
    """Fetch a single event record by its OWC Event ID.

    Used to discover the numeric stationId values for the report-observation
    endpoint. The response structure is unknown until first inspection — see
    test T3 in the test plan which dumps the raw response.

    Args:
        event_id: OWC event ID string (stored as 'ow_eventid' in occultation dict)
        api_key:  OWC API key string
        host:     Base host URL

    Returns:
        Parsed JSON response dict (raw — caller inspects structure)
    """
    url = host + '/api2/v1/events/' + str(event_id)
    return EventProcessor.get_owc_events_v2(url, api_key)
```

**Station ID extraction:** Once the response structure is known from inspection (test T3),
add a helper:

```python
@staticmethod
def extract_station_id(event_by_id_response, station_name):
    """Extract the integer stationId for a named station from the event-by-id response.

    NOTE: The field name and structure are TBD pending inspection of the response.
    This is a placeholder — update after running test T3.

    Args:
        event_by_id_response: JSON dict from get_owc_event_by_id()
        station_name:         Station name string to match

    Returns:
        int station ID, or None if not found
    """
    # TODO: Update path once response structure is known from test T3
    stations = event_by_id_response.get('Stations', [])
    for s in stations:
        if s.get('StationName') == station_name:
            return s.get('Id') or s.get('StationId') or s.get('id')
    return None
```

**Store station ID in event dict:**  
In `process_owc_events()`, after the occultation dict is built (around the existing
`occultations.append(occultation)` call), add a deferred lookup step. This is a separate
pass so that the existing per-event flow is unchanged.

```python
# In process_owc_events() — new block appended AFTER existing occultation dict is built
# (inside the station loop, after occultation dict creation):

# Attempt to resolve the numeric OWC stationId using the new endpoint.
# Falls back gracefully — does not break the existing flow if unavailable.
owc_station_id = None
try:
    event_detail = EventProcessor.get_owc_event_by_id(
        eventId, config.get_api_key()
    )
    owc_station_id = EventProcessor.extract_station_id(event_detail, stationName)
except Exception:
    pass   # Non-critical — report submission will surface the error later
occultation['owc_station_id'] = owc_station_id   # None until resolved
```

> **Note on extra API call per event:** The `get_owc_event_by_id` call adds one HTTP
> request per event during download. If this is too slow, move it to a lazy-resolve step
> triggered only when the user initiates report submission.

---

### Task 3 — Submit observation report

**File:** `events.py` (or new `owc_report.py` — see note below)  
**Action:** New static method. No existing methods modified.

```python
@staticmethod
def submit_owc_report(config, event, observation_type,
                      comment='', duration_s=None, update_location=False):
    """Submit an observation result to OWC via the report-observation endpoint.

    Args:
        config:          AppConfig instance
        event:           OccultationEvent (must have 'ow_eventid' and 'owc_station_id')
        observation_type: String — 'Positive', 'Negative', 'Clouded', 'Failed',
                          'NotObserved', 'NotReduced'
        comment:         Optional free text comment
        duration_s:      Optional float duration in seconds (Positive only)
        update_location: If True, include observer lat/lng/alt from config

    Returns:
        dict with keys:
            'success':  bool
            'response': raw response dict or None
            'error':    error message string or None
    """
    REPORT_CODES = {
        'NotReported':   0,
        'Miss':          1,
        'Negative':      1,
        'Clouded':       2,
        'Failed':        3,
        'Positive':      4,
        'NotObserved':   5,
        'NotReduced':    6,
    }

    event_id  = event.get('ow_eventid') if isinstance(event, dict) else getattr(event, 'ow_eventid', None)
    station_id = event.get('owc_station_id') if isinstance(event, dict) else getattr(event, 'owc_station_id', None)

    if not event_id:
        return {'success': False, 'response': None, 'error': 'No ow_eventid on event'}
    if station_id is None:
        return {'success': False, 'response': None, 'error': 'No owc_station_id resolved — run get_owc_event_by_id first'}

    report_code = REPORT_CODES.get(observation_type)
    if report_code is None:
        return {'success': False, 'response': None, 'error': 'Unknown observation_type: ' + observation_type}

    payload = {
        'eventId':   str(event_id),
        'stationId': int(station_id),
        'report':    report_code,
        'comment':   comment or '',
    }

    if observation_type == 'Positive' and duration_s is not None:
        payload['duration'] = float(duration_s)

    if update_location:
        lat = event.get('latitude') if isinstance(event, dict) else getattr(event, 'latitude', None)
        lng = event.get('longitude') if isinstance(event, dict) else getattr(event, 'longitude', None)
        alt = event.get('elevation') if isinstance(event, dict) else getattr(event, 'elevation', None)
        if lat is not None and lng is not None:
            payload['updateLocation'] = True
            payload['latDeg']         = float(lat)
            payload['lngDeg']         = float(lng)
            if alt is not None:
                payload['altMslMeters'] = float(alt)

    url = config.get_report_observation_url()
    try:
        response = EventProcessor.get_owc_events_v2(
            url, config.get_api_key(), data=payload, method='POST'
        )
        return {'success': True, 'response': response, 'error': None}
    except Exception as ex:
        return {'success': False, 'response': None, 'error': str(ex)}
```

---

## 4. Config changes — `config.py`

| New method | Returns |
|---|---|
| `get_base_url()` | `host + url_path` (no API key) |
| `get_occelmnt_base_url()` | `host + URL_OCCELMNT_ENDPOINT_PATH` (no API key) |
| `get_report_observation_url()` | `host + '/api2/v1/owc/report-observation'` |
| `get_event_by_id_url(event_id)` | `host + '/api2/v1/events/' + str(event_id)` |

**Existing `get_full_url()` and `get_occelmnt_url()` are unchanged.**

---

## 5. Test Plan

### T1 — Compare old vs new authentication responses

Verify that the v2 header-based call returns identical data to the existing v1 URL-param call.

```python
# test_owc_auth_comparison.py
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import AppConfig
from events import EventProcessor

config = AppConfig()
api_key = config.get_api_key()

print("=== T1: Auth comparison — old (URL param) vs new (header) ===\n")

# --- Old method (unchanged) ---
url_v1 = config.get_full_url()   # includes ?apikey=...
print("V1 URL:", url_v1)
try:
    result_v1 = EventProcessor.get_owc_events(
        url_v1, config.get_owc_email(), config.get_owc_password()
    )
    print("V1 event count:", len(result_v1))
    v1_ids = sorted(e['Id'] for e in result_v1)
except Exception as ex:
    print("V1 FAILED:", ex)
    v1_ids = []

# --- New method (header) ---
url_v2 = config.get_base_url()   # no ?apikey=
print("V2 URL:", url_v2)
try:
    result_v2 = EventProcessor.get_owc_events_v2(url_v2, api_key)
    print("V2 event count:", len(result_v2))
    v2_ids = sorted(e['Id'] for e in result_v2)
except Exception as ex:
    print("V2 FAILED:", ex)
    v2_ids = []

# Compare
if v1_ids == v2_ids:
    print("\n✓ MATCH — both methods return identical event IDs")
else:
    print("\n✗ MISMATCH")
    print("  In V1 only:", [i for i in v1_ids if i not in v2_ids])
    print("  In V2 only:", [i for i in v2_ids if i not in v1_ids])
```

---

### T2 — Inspect raw station data for `Id` / `StationId` field

Before implementing `extract_station_id()`, dump all keys from a station object to
discover whether the new endpoint or the details-list already returns a station ID.

```python
# test_owc_station_fields.py
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import AppConfig
from events import EventProcessor

config = AppConfig()
api_key = config.get_api_key()

url = config.get_base_url()
events = EventProcessor.get_owc_events_v2(url, api_key)

print("=== T2: Station field inspection from details-list ===\n")
for ev in events[:3]:   # inspect first 3 events
    print("Event:", ev.get('Object'), "| Id:", ev.get('Id'))
    print("  Event-level keys:", sorted(ev.keys()))
    for station in ev.get('Stations', []):
        if station.get('IsOwnStation'):
            print("  Own station fields:")
            for k in sorted(station.keys()):
                print("    {0!s:30s} = {1!r}".format(k, station[k]))
            print()
    print()
```

**Expected:** Look for `Id`, `StationId`, `station_id`, or similar integer field. If no
station ID is present here, it must come from the new `/api2/v1/events/{EventID}` endpoint
(see T3).

---

### T3 — Inspect raw response from `/api2/v1/events/{EventID}`

This is the key inspection test for the unknown station ID format.

```python
# test_owc_event_by_id.py
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import AppConfig
from events import EventProcessor

config = AppConfig()
api_key = config.get_api_key()

# First, get a real event ID from the current event list
url = config.get_base_url()
all_events = EventProcessor.get_owc_events_v2(url, api_key)
own_events = [e for e in all_events if any(s.get('IsOwnStation') for s in e.get('Stations', []))]

if not own_events:
    print("No own-station events found — cannot test")
    sys.exit(1)

sample = own_events[0]
event_id = sample['Id']
print("=== T3: Event-by-ID response inspection ===")
print("Using event:", sample.get('Object'), "| ID:", event_id)
print()

try:
    detail = EventProcessor.get_owc_event_by_id(event_id, api_key)
    print("--- Full response (pretty-printed) ---")
    print(json.dumps(detail, indent=2))
    print()
    print("--- Top-level keys ---")
    print(sorted(detail.keys()) if isinstance(detail, dict) else type(detail))
    if isinstance(detail, dict):
        stations = detail.get('Stations', [])
        print("\n--- Stations ({0}) ---".format(len(stations)))
        for s in stations:
            print("  Keys:", sorted(s.keys()))
            for k in sorted(s.keys()):
                print("    {0!s:30s} = {1!r}".format(k, s[k]))
            print()
except Exception as ex:
    print("FAILED:", ex)
```

**What to look for:**
- A `StationId`, `Id`, `id`, or similar integer field on each station object
- Whether the station name matches the `StationName` field from the details-list
- Whether the event ID is a string (GUID/UUID) or integer

---

### T4 — Dry-run of report payload (no actual submission)

Verify payload construction without sending to OWC.

```python
# test_owc_report_payload.py
import json, sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import AppConfig
from events import EventProcessor

config = AppConfig()
api_key = config.get_api_key()

# Load a saved event (with owc_station_id if T3 succeeded and station ID was stored)
from events import EventProcessor
import json

events_file = config.get_occultations_file()
full_path = config.get_full_file_path(events_file)
with open(full_path, 'r') as f:
    saved_events = json.load(f)

# Find one with owc_station_id set (will be None until Task 2 is implemented)
sample = None
for ev in saved_events:
    if ev.get('owc_station_id') is not None:
        sample = ev
        break

if sample is None:
    print("No event with owc_station_id found — simulating with placeholder")
    sample = saved_events[0]
    sample['owc_station_id'] = 99   # placeholder for dry-run

print("=== T4: Report payload dry-run ===")
print("Event:", sample.get('object_name'), "| ow_eventid:", sample.get('ow_eventid'))
print("Station:", sample.get('station_name'), "| owc_station_id:", sample.get('owc_station_id'))
print()

# Build payload manually (mirrors submit_owc_report logic)
payload = {
    'eventId':   str(sample['ow_eventid']),
    'stationId': int(sample['owc_station_id']),
    'report':    4,   # Positive
    'comment':   'Test dry-run from OM',
    'duration':  1.5,
}
print("Payload to POST:")
print(json.dumps(payload, indent=2))
print()
print("Target URL:", config.get_report_observation_url())
print()
print("NOTE: No HTTP request made — inspection only")
```

---

### T5 — Live report submission test (use with caution)

Only run against a real past event where you know the outcome. Use a known negative event
to avoid polluting positive detection data.

```python
# test_owc_report_submit_live.py  — USE WITH CAUTION
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from config import AppConfig
from events import EventProcessor

config = AppConfig()

# Use a known past event ID — fill in manually after T3 inspection
TEST_EVENT_ID   = 'PASTE-KNOWN-EVENT-ID-HERE'
TEST_STATION_ID = 0   # Fill in after T3 inspection

test_event = {
    'ow_eventid':      TEST_EVENT_ID,
    'owc_station_id':  TEST_STATION_ID,
    'station_name':    config.get_observer_name(),
    'latitude':        None,
    'longitude':       None,
    'elevation':       None,
}

result = EventProcessor.submit_owc_report(
    config,
    test_event,
    observation_type='Negative',
    comment='Automated test from OM — please ignore'
)

print("=== T5: Live report submission ===")
print("Success:", result['success'])
print("Error:  ", result['error'])
print("Response:")
import json
print(json.dumps(result['response'], indent=2) if result['response'] else "(none)")
```

---

## 6. Implementation Order

```
T2 → inspect station fields in details-list (may already have station ID)
T3 → inspect /api2/v1/events/{EventID} response structure
      ↓
     Update extract_station_id() with correct field name
      ↓
Task 1 → add get_owc_events_v2() + new config URL methods
Task 2 → add get_owc_event_by_id() + extract_station_id() + store owc_station_id
Task 3 → add submit_owc_report()
      ↓
T1 → verify V1/V2 auth parity
T4 → verify payload construction
T5 → live submission against known past event
```

---

## 7. Rollback Notes

- All existing methods (`get_owc_events`, `get_full_url`, `get_occelmnt_url`,
  `update_ow_cloud_events`, `process_owc_events`) are **not modified** — they remain
  callable and functional.
- The new `owc_station_id` key is added to the event dict with value `None` as default.
  Existing code that doesn't reference this key is unaffected.
- New config methods are additive — no existing config keys or methods change.
- To roll back entirely: remove the four new config methods and the two new `EventProcessor`
  static methods. No data files are altered by any of the above.

---

## 8. Open Questions

| # | Question | How to resolve |
|---|---|---|
| OQ1 | Is `stationId` a zero-based index, a DB row ID, or a GUID? | Run T3 |
| OQ2 | Does the details-list response already carry a station ID? | Run T2 |
| OQ3 | What does the `/api2/v1/events/{ID}` response look like? | Run T3 |
| OQ4 | Does the POST report endpoint return a body, or just HTTP 200? | Run T5 |
| OQ5 | Is `eventId` a string UUID or a numeric integer? | Run T3 / check `ev['Id']` type in T1 |
| OQ6 | Can a station ID be retrieved without the new endpoint (i.e., already in details-list)? | Run T2 |
