# OBS.XML Data Field Mapping

## Status Note (2026-03)

This mapping is maintained as an active reference for current `occult4_export.py` behavior.

## Purpose
This document maps available data sources to OBS.XML format fields for single observation reporting.

## Data Sources Available

### 1. OccultationEvent Object (from events.py)
Parsed from `occultations.json` (downloaded from OWC):

**Prediction Data (from OWC):**
- `event_datetime` - Event date/time as datetime object
- `event_time` - Event time ISO string "YYYY-MM-DDTHH:MM:SS"
- `event_date` - Event date "YYYY-MM-DD"
- `event_time_utc` - Event time "HH:MM:SS"
- `event_duration` - Event duration in seconds
- `event_uncertainty` - Time uncertainty in seconds
- `recording_duration` - Calculated recording duration

**Star Data (from OWC):**
- `star_id` / `star_name` - Star catalog designation (e.g., "UCAC4 570-020044")
- `ra` / `ra_hours` - RA J2000 in hours (float) - from OWC `RAJ2000Hours`
- `dec` / `dec_degrees` - Dec J2000 in degrees (float) - from OWC `DEJ2000Deg`
- `star_mag` / `magnitude` - Star magnitude
- `comb_mag` - Combined magnitude (star + asteroid)
- `mag_drop` - Magnitude drop during occultation
- `star_az` - Star azimuth (degrees)
- `star_alt` - Star altitude (degrees)
- **NOTE:** RA/Dec apparent coordinates are NOT available in OWC data

**Asteroid Data (from OWC):**
- `object_name` / `asteroid_name` - Full name e.g., "(119355) 2001 SU232"
- `object_no` - Asteroid number e.g., "119355"

**Observer Location (from OWC station + geocoding):**
- `station_name` - Station name
- `latitude` - Latitude (decimal degrees)
- `longitude` - Longitude (decimal degrees)
- `elevation` - Elevation in meters (from geocoding API)
- `obs_location` - City/town name (from geocoding API)

**Other:**
- `ow_eventid` - OWC event UUID
- `owcloudurl` - URL to OWC event page
- `source` - Always "OWCloud"
- `exposure_ms` - Calculated exposure in milliseconds

### 2. Configuration (from config.py)
Observer/equipment configuration stored in `occultation_config.json`:

**Observer Information:**
- `config.get_observer_name()` - Observer's full name
- `config.get_observer_email()` - Observer's email
- `config.get_observer_address()` - Mailing address
- `config.get_observer_city()` - City
- `config.get_observer_state()` - State/region code
- `config.get_observer_country()` - Country
- `config.get_observer_phone()` - Phone number
- `config.get_observer_fax()` - Fax number

**Telescope Configuration:**
- `config.get_telescope_by_id(telescope_id)` returns:
  - `id` - Unique telescope ID
  - `name` - Telescope name
  - `aperture` - Aperture in cm
  - `focal_ratio` - Focal ratio (f/number)
  - `type` - Telescope type (e.g., "SCT including Cass and Mak", "Newtonian", "Refractor")

**Camera Configuration:**
- `config.get_camera_by_id(camera_id)` returns:
  - `id` - Unique camera ID
  - `name` - Camera name
  - `detector` - Detector type
  - `timing` - Timing method
  - `timing_device` - Timing device description
  - `other_info` - Additional camera information
  - `video_format` - Video format (e.g., "SER", "AVI")
  - `exposure_integration` - Exposure integration method

### 3. AOTA Report Data (from aota_report_parser.py)
Parsed from `AOTA_Report.txt` (Tangra output):

**Observed Timing Data:**
- `d_hours` - Disappearance hour (observed)
- `d_minutes` - Disappearance minute (observed)
- `d_seconds` - Disappearance second with decimal (observed)
- `d_uncertainty` - Disappearance uncertainty in seconds
- `r_hours` - Reappearance hour (observed)
- `r_minutes` - Reappearance minute (observed)
- `r_seconds` - Reappearance second with decimal (observed)
- `r_uncertainty` - Reappearance uncertainty in seconds
- `snr` / `snr_ave` - Signal-to-noise ratio

**Metadata:**
- `camera` - Camera name from report
- `frames_integrated` - Number of frames integrated
- `video_system` - Video system type
- `measurement_tool` - Measurement tool used (e.g., "Tangra")

### 4. Occelmnt Data (from OWC API)
**Downloaded via `get_owc_events()` and stored in event's `occelmnt` field.**

The Occelmnt structure contains detailed prediction data from Occult4 calculations. This is the **PREFERRED SOURCE** for star, asteroid, and motion data when available.

**From `<Elements>` tag (comma-separated):**
- Index 0: Source (orbit source and prediction date)
- Index 1: Duration (maximum duration in seconds)
- Index 2-4: Year, Month, Day of event
- Index 5: UT at closest approach (decimal hours)
- Index 6-7: **X, Y** - Shadow coordinates at closest approach (Earth radii)
- Index 8-9: **dX, dY** - Hourly rate of change in X, Y (Earth radii/hr) ✓
- Index 10-11: **d2X, d2Y** - 2nd order rate of change (Earth radii/hr²) ✓
- Index 12-13: **d3X, d3Y** - 3rd order rate of change (Earth radii/hr³) ✓

**From `<Star>` tag (comma-separated, 14 fields total):**
- Index 0: Identifier (catalog designation)
- Index 1: **RA** - BCRS J2000 position (decimal hours) ✓
- Index 2: **Dec** - BCRS J2000 position (decimal degrees) ✓
- Index 3: **Mb** - Blue magnitude ✓
- Index 4: **Mv** - Visual magnitude ✓
- Index 5: **Mr** - Red magnitude ✓
- Index 6: **dia** - Stellar diameter in mas ✓
- Index 7: Double star code (0=none, 1=WDS, 2=other, 4=variable, cumulative)
- Index 8: K2 flag ("K" if Kepler2 target, blank otherwise)
- Index 9: **RA Apparent** - Apparent RA of date (decimal hours) ✓
- Index 10: **Dec Apparent** - Apparent Dec of date (decimal degrees) ✓
- Index 11: MagDropsAdjusted_NearbyStars - Flag: 0=not adjusted, 1=adjusted
- Index 12: BrightNearbyCount - Bright nearby stars count (or -1 if not checked)
- Index 13: TotalNearbyCount - All nearby stars count (or -1 if not checked)

**From `<Object>` tag (comma-separated):**
- Index 0: Number (asteroid number or PxMyy for planet moons)
- Index 1: Name
- Index 2: **Magnitude** - Asteroid magnitude ✓
- Index 3: **Diameter** (km) - augmented by star diameter ✓
- Index 4: Distance (AU)
- Index 5: Number of rings
- Index 6: Number of moons
- Index 7: dRA - Hourly rate of change in RA (s/hr)
- Index 8: dDec - Hourly rate of change in Dec (arcsec/hr)
- Index 9: Taxonomic class
- Index 10: **Diameter uncertainty** (km) ✓
- Index 11: Planet moon in shadow flag
- Index 12: **MagV_Asteroid** - V magnitude ✓
- Index 13: **MagR_Asteroid** - R magnitude ✓

**From `<Earth>` tag (comma-separated):**
- Index 0: Substellar longitude (deg)
- Index 1: Substellar latitude (deg)
- Index 2: Subsolar longitude (deg)
- Index 3: Subsolar latitude (deg)
- Index 4: JWST flag (1=true, 0=false)

**From `<Errors>` tag (comma-separated):**
- Index 0: Path width uncertainty (fraction of path width)
- Index 1: **Major axis** of error ellipse (arcsec) ✓
- Index 2: **Minor axis** of error ellipse (arcsec) ✓
- Index 3: **PA** of major axis (degrees) ✓
- Index 4: **1-sigma** star/asteroid position error (arcsec) ✓
- Index 5: Error basis description string
- Index 6: **Reliability** (RUWE value, or -1/-2/-3/-4 for special cases) ✓
- Index 7: **Duplicate Source** flag (0/1/-1) ✓
- Index 8: **Non-GAIA proper motion** flag (0/1/-1) ✓
- Index 9: **Proper motion using UCAC4** flag (0/1/-1) ✓

**From `<Orbit>` tag (comma-separated):**
- Orbital elements for plotting (not needed for observation reporting)

**From `<Moons>` tag (if present):**
- Moon data (not needed for single observation reporting)

**Access in code:**
```python
if event.original_data.get('occelmnt'):
    occelmnt = event.original_data['occelmnt']
    elements = occelmnt['Occultations']['Event']['Elements'].split(',')
    star = occelmnt['Occultations']['Event']['Star'].split(',')
    obj = occelmnt['Occultations']['Event']['Object'].split(',')
    errors = occelmnt['Occultations']['Event']['Errors'].split(',')
```

### 5. Tangra Light Curve Data
Structure not yet fully defined, but likely includes:
- Light curve data points
- Event detection parameters
- Additional SNR metrics

### 7. OWC Downloaded Events (from owc_downloaded_events.json)
Additional fields available in raw OWC data (not all parsed into OccultationEvent):

**Extended Star Data:**
- `OtherStarNames` - Alternative star designations
- `BV` - B-V color index
- `StellarDiaMas` - Stellar diameter in milliarcseconds (often null)
- `StarColour` - Star color code

**Extended Asteroid Data:**
- `AstMag` - Asteroid magnitude
- `AstDiaKm` - Asteroid diameter in km
- `AstDistUA` - Asteroid distance in AU
- `AstRotationHrs` - Rotation period (often null)
- `AstRotationAmplitude` - Rotation amplitude (often null)
- `AstClass` - Asteroid class
- `OneSigmaErrorWidthKm` - 1-sigma error width

**Extended Prediction Data:**
- `MaxDurSec` - Maximum duration in seconds
- `ErrorInTimeSec` - Time error in seconds
- `ChordOffsetKm` - Chord offset in km (per station)
- `OccultDistanceKm` - Occultation distance in km
- `PredictionUpdated` - Timestamp of prediction update
- `Rank` - Event rank

**Observing Conditions (at prediction time):**
- `SunAlt` - Sun altitude
- `MoonAlt` - Moon altitude
- `MoonAz` - Moon azimuth
- `MoonDist` - Moon distance in degrees
- `MoonPhase` - Moon phase percentage

**Weather (often not available):**
- `WeatherInfoAvailable` - Boolean
- `TempDegC` - Temperature
- `Wind` - Wind speed
- `CloudCover` - Cloud cover percentage
- `HighCloud` - High cloud boolean

### 8. User Input / Observation Type
- `observation_type` - "Positive", "Negative", or "Unsure"

---

## OBS.XML Field Mapping

### FileVersion
**XML Field:** `<FileVersion>`  
**Source:** Hardcoded constant  
**Value:** `"2.15"`

---

### Date Section

#### Date Line (4 fields)
**XML Format:** `<Date>year|month|day|hour</Date>`

| Field | Source | Data Path | Notes |
|-------|--------|-----------|-------|
| Year | Event | `event.event_datetime.year` | From OWC prediction |
| Month | Event | `event.event_datetime.month` | From OWC prediction |
| Day | Event | `event.event_datetime.day` | From OWC prediction |
| Hour | Event | `event.event_datetime.hour + minute/60 + second/3600` | Decimal hours, from OWC prediction |

---

### Details Section

#### Star Line (16 fields)
**XML Format:** `<Star>Catalogue|number|Gaia version|Gaia id|RA2000|Dec2000|RA unc|Dec unc|Stellar dia|Issues|RA Apparent|Dec Apparent|Mb|Mg|Mr|EPIC ID</Star>`

| Field | Source | Data Path | Precision | Notes |
|-------|--------|-----------|-----------|-------|
| 1. Catalogue | Occelmnt/Event | `star[0]` from Occelmnt, or parse `event.star_id` | - | e.g., "UCAC4" from "UCAC4 570-020044" |
| 2. Number | Occelmnt/Event | `star[0]` from Occelmnt, or parse `event.star_id` | - | e.g., "570-020044" |
| 3. Gaia version | **NOT AVAILABLE** | - | - | Use -1 (not specified) unless catalog is "Gaia DR3" etc. |
| 4. Gaia id | **NOT AVAILABLE** | - | - | Use "0" unless Gaia catalog identified |
| 5. RA J2000 | **Occelmnt** | `star[1]` (decimal hours) | 10 decimals | **PREFERRED:** hh.hhhhhhhhhh format |
| 5. RA J2000 (alt) | Event | `event.ra_hours` (from OWC `RAJ2000Hours`) | 10 decimals | Use if Occelmnt not available |
| 6. Dec J2000 | **Occelmnt** | `star[2]` (decimal degrees) | 9 decimals | **PREFERRED:** ±dd.ddddddddd format with sign |
| 6. Dec J2000 (alt) | Event | `event.dec_degrees` (from OWC `DEJ2000Deg`) | 9 decimals | Use if Occelmnt not available |
| 7. RA uncertainty | **Occelmnt** | Calculate from `errors[4]` (1-sigma in arcsec) | mas | Convert arcsec to mas (*1000), apportion to RA |
| 8. Dec uncertainty | **Occelmnt** | Calculate from `errors[4]` (1-sigma in arcsec) | mas | Convert arcsec to mas (*1000), apportion to Dec |
| 9. Stellar diameter | **Occelmnt** | `star[6]` (mas) | mas | Stellar diameter in milliarcseconds |
| 9. Stellar diameter (alt) | OWC Raw | `StellarDiaMas` from OWC | mas | Use if Occelmnt not available, often null |
| 10. Issues flag | **NOT AVAILABLE** | - | - | Use "0" (no issues) - could derive from star[7] double star code |
| 11. RA Apparent | **Occelmnt** | `star[9]` (decimal hours) | 8 decimals | **PREFERRED:** hh.hhhhhhhh format |
| 12. Dec Apparent | **Occelmnt** | `star[10]` (decimal degrees) | 7 decimals | **PREFERRED:** ±dd.ddddddd format |
| 13. Mb | **Occelmnt** | `star[3]` | 2 decimals | Gaia blue magnitude |
| 14. Mg | **Occelmnt** | `star[4]` | 2 decimals | **PREFERRED:** Gaia G or V magnitude |
| 14. Mg (alt) | Event | `event.star_mag` | 2 decimals | Use if Occelmnt not available |
| 15. Mr | **Occelmnt** | `star[5]` | 2 decimals | Gaia red magnitude |
| 16. EPIC ID | **NOT AVAILABLE** | - | - | Leave blank (or use star[8] K2 flag) |

#### StarIssues Line (11 fields)
**XML Format:** `<StarIssues>Reliability|Dup flag|No PM|UCAC4 PM|Brightness ratio|Ratio unc%|RA offset|Dec offset|RA sdev|Dec sdev|Component ID</StarIssues>`

| Field | Source | Data Path | Notes |
|-------|--------|-----------|-------|
| 1. Reliability | **Occelmnt** | `errors[6]` | RUWE or special codes: -1=not set, -2=unreliable Hip, -3=in UBSC, -4=Hip2 duplicate |
| 2. Duplicated Source flag | **Occelmnt** | `errors[7]` | 0=no, 1=yes, -1=not set |
| 3. No Proper Motion | **Occelmnt** | `errors[8]` | 0=has PM, 1=no PM, -1=not set |
| 4. UCAC4 Proper Motion | **Occelmnt** | `errors[9]` | 0=no, 1=UCAC4 PM added, -1=not set |
| 5. Brightness ratio | Default | "1.2" | Default value (no double star data in Occelmnt) |
| 6. Ratio uncertainty % | Default | "10" | Default value |
| 7. RA offset mas | Default | "0" | No double star solution yet |
| 8. Dec offset mas | Default | "0" | No double star solution yet |
| 9. RA sdev mas | Default | "0" | No double star solution yet |
| 10. Dec sdev mas | Default | "0" | No double star solution yet |
| 11. Component ID | **NOT AVAILABLE** | "" | Blank |

#### Asteroid Line (12 fields)
**XML Format:** `<Asteroid>Number|Name|dX|dY|d2X|d2Y|d3X|d3Y|Parallax|dParallax|Diameter|Diameter unc|Mv</Asteroid>`

| Field | Source | Data Path | Notes |
|-------|--------|-----------|-------|
| 1. Number | **Occelmnt** | `object[0]` | **PREFERRED:** Asteroid number or PxMyy format |
| 1. Number (alt) | Event | Parse from `event.object_name` | Extract number from "(119355) 2001 SU232" |
| 2. Name | **Occelmnt** | `object[1]` | **PREFERRED:** Asteroid name |
| 2. Name (alt) | Event | Parse from `event.object_name` | Extract name, remove number |
| 3. dX | **Occelmnt** | `elements[8]` | **AVAILABLE!** Motion coefficient in Earth radii/hr |
| 4. dY | **Occelmnt** | `elements[9]` | **AVAILABLE!** Motion coefficient in Earth radii/hr |
| 5. d2X | **Occelmnt** | `elements[10]` | **AVAILABLE!** 2nd order coefficient in Earth radii/hr² |
| 6. d2Y | **Occelmnt** | `elements[11]` | **AVAILABLE!** 2nd order coefficient in Earth radii/hr² |
| 7. d3X | **Occelmnt** | `elements[12]` | **AVAILABLE!** 3rd order coefficient in Earth radii/hr³ |
| 8. d3Y | **Occelmnt** | `elements[13]` | **AVAILABLE!** 3rd order coefficient in Earth radii/hr³ |
| 9. Parallax | **NOT AVAILABLE** | "0" | Not in Occelmnt - would need ephemeris calculation |
| 10. dParallax | **NOT AVAILABLE** | "0" | Not in Occelmnt - would need ephemeris calculation |
| 11. Diameter | **Occelmnt** | `object[3]` (km) | **PREFERRED:** Augmented by star diameter |
| 11. Diameter (alt) | OWC Raw | `AstDiaKm` | Use if Occelmnt not available |
| 12. Diameter unc | **Occelmnt** | `object[10]` (km) | **AVAILABLE!** Diameter uncertainty |
| 13. Mv | **Occelmnt** | `object[12]` | **PREFERRED:** V magnitude of asteroid |
| 13. Mv (alt) | OWC Raw | `AstMag` | Use if Occelmnt not available |

---

### Observations Section

#### Prediction Line (7 fields)
**XML Format:** `<Prediction>Seq|Longitude|Latitude|hr|min|sec|Comments</Prediction>`

**NOTE:** This is the PREDICTED event location/time from OWC, NOT observed times

| Field | Source | Data Path | Format | Notes |
|-------|--------|-----------|--------|-------|
| 1. Seq Num | Auto | - | - | Sequential number, use "1" |
| 2. Longitude | Event | `event.longitude` | ±ddd mm ss.s | DMS format with sign |
| 3. Latitude | Event | `event.latitude` | ±dd mm ss.s | DMS format with sign |
| 4. Hour | Event | `event.event_datetime.hour` | hh | From OWC PREDICTION |
| 5. Minute | Event | `event.event_datetime.minute` | mm | From OWC PREDICTION |
| 6. Second | Event | `event.event_datetime.second + microsecond/1e6` | ss.s | From OWC PREDICTION, 1 decimal |
| 7. Comments | Optional | - | - | Free text or blank |

#### Observer ID Line (14 fields)
**XML Format:** `<ID>Seq|Observer1|Observer2|More|Near|State|Lon|Lat|Alt|Datum|Aperture|Type|Method|TimeSource</ID>`

| Field | Source | Data Path | Format | Notes |
|-------|--------|-----------|--------|-------|
| 1. Seq Num | Auto | - | - | Sequential number, use "1" |
| 2. Observer1 | Config | `config.get_observer_name()` | - | Primary observer name |
| 3. Observer2 | **NOT AVAILABLE** | - | - | Use blank |
| 4. MoreThan2Observers | **NOT AVAILABLE** | - | - | Use blank |
| 5. NearLocation | Event | `event.obs_location` | - | City/town from geocoding |
| 6. State/Country | Config | `config.get_observer_state()` | 2-3 letter | State or country code |
| 7. Longitude | Event | `event.longitude` | ±ddd mm ss.s | DMS format |
| 8. Latitude | Event | `event.latitude` | ±dd mm ss.ss | DMS format (2 decimal seconds) |
| 9. Altitude | Event | `event.elevation` | m | Meters from geocoding |
| 10. Datum | Default | "_" | - | WGS84 (underscore) |
| 11. Telescope Aperture | Telescope Config | `telescope['aperture']` | cm | From telescope configuration |
| 12. Telescope Type | Telescope Config | Map from `telescope['type']` | 0-8 | Map to OBS.XML codes |
| 13. Observing Method | Camera Config | Map from camera data | a-g | Map to OBS.XML codes |
| 14. Time Source | Camera Config | Map from `camera['timing']` | a-g | Map to OBS.XML codes |

**Telescope Type Mapping:**
- "Refractor" → "1"
- "Newtonian" → "2"
- "SCT including Cass and Mak" → "3"
- "Dobsonian" → "4"
- "Binoculars" → "5"
- "Other" → "6"
- "None" / Visual → "7"
- "Electronic" → "8"
- Unknown → "_"

**Observing Method Mapping:**
- "Analogue & digital video" → "a"
- "Digital SLR-camera video" → "b"
- "Photometer" → "c"
- "Sequential images" → "d"
- "Drift scan" → "e"
- "Visual" → "f"
- "Other" → "g"
- Unknown → blank

**Time Source Mapping:**
- "GPS" / Contains "GPS" → "a"
- "NTP" / Contains "NTP" → "b"
- "Telephone" → "c"
- "Radio time signal" → "d"
- "Internal clock" / "Internal" → "e"
- "Stopwatch" → "f"
- "Other" → "g"
- Unknown → blank

#### Conditions Line (5 fields)
**XML Format:** `<Conditions>Stability|Transparency|SN|TimeAdj|Comment</Conditions>`

| Field | Source | Data Path | Notes |
|-------|--------|-----------|-------|
| 1. Stability | **USER INPUT NEEDED** | - | Use "_" for unstated, or user input (1-3) |
| 2. Transparency | **USER INPUT NEEDED** | - | Use "_" for unstated, or user input (1-7) |
| 3. S/N Ratio | AOTA Report | `aota_report_data['snr']` | From Tangra AOTA Report |
| 4. Time Adjustment | **NOT AVAILABLE** | - | Use blank |
| 5. Comment | **USER INPUT NEEDED** | - | Free text or blank |

#### D Line - Disappearance (6 fields)
**XML Format:** `<D>hh mm ss.ss|eventCode|Accuracy|PEqn|Weight|PlotCode</D>`

**NOTE:** This is the OBSERVED disappearance time from AOTA Report, NOT prediction

| Field | Source | Data Path | Format | Notes |
|-------|--------|-----------|--------|-------|
| 1. Time | AOTA Report | `aota_report_data['d_hours']` `['d_minutes']` `['d_seconds']` | hh mm ss.ss | OBSERVED time from Tangra |
| 2. Event Code | observation_type | Map from observation_type | P/p/M/m/U/Z | See mapping below |
| 3. Accuracy | AOTA Report | `aota_report_data['d_uncertainty']` | seconds | From Tangra uncertainty |
| 4. PEqn | **NOT AVAILABLE** | - | - | Use blank (timing equation) |
| 5. Weight | **USER INPUT or CALC** | - | 0-10 | Could base on SNR, or user input |
| 6. Plot Code | **NOT AVAILABLE** | - | - | Use blank |

#### R Line - Reappearance (6 fields)
**XML Format:** `<R>hh mm ss.ss|eventCode|Accuracy|PEqn|Weight|PlotCode</R>`

**NOTE:** This is the OBSERVED reappearance time from AOTA Report, NOT prediction

| Field | Source | Data Path | Format | Notes |
|-------|--------|-----------|--------|-------|
| 1. Time | AOTA Report | `aota_report_data['r_hours']` `['r_minutes']` `['r_seconds']` | hh mm ss.ss | OBSERVED time from Tangra |
| 2. Event Code | observation_type | Map from observation_type | P/p/M/m/U/Z | See mapping below |
| 3. Accuracy | AOTA Report | `aota_report_data['r_uncertainty']` | seconds | From Tangra uncertainty |
| 4. PEqn | **NOT AVAILABLE** | - | - | Use blank (timing equation) |
| 5. Weight | **USER INPUT or CALC** | - | 0-10 | Could base on SNR, or user input |
| 6. Plot Code | **NOT AVAILABLE** | - | - | Use blank |

**Event Code Mapping:**
- observation_type = "Positive" → "P" (Positive)
- observation_type = "Negative" → "M" (Miss/non-detection)
- observation_type = "Unsure" → "U" (Uncertain)
- If D or R time missing → "Z" (Clouded out) for that event

---

### Metadata Section

#### Added Date
**XML Format:** `<Added>yyyy|m|d</Added>`  
**Source:** Current date at export time  
**Value:** `datetime.now()` formatted as `year|month|day`

#### LastEdited Date
**XML Format:** `<LastEdited>yyyy|m|d</LastEdited>`  
**Source:** Current date at export time  
**Value:** `datetime.now()` formatted as `year|month|day`

---

## Summary of Data Availability

### ✓ Available from Current Sources
- Event date/time (PREDICTION from OWC)
- **Star coordinates:** RA/Dec J2000 from Occelmnt `<Star>` (preferred) or OWC `RAJ2000Hours`/`DEJ2000Deg`
- **Star coordinates:** RA/Dec Apparent from Occelmnt `<Star>` indices 9-10 ✨ NEW!
- **Star magnitudes:** Mb, Mv (Mg), Mr from Occelmnt `<Star>` indices 3-5 ✨ NEW!
- **Star diameter:** From Occelmnt `<Star>` index 6 (mas) ✨ NEW!
- **Star quality flags:** RUWE/Reliability, Duplicate Source, No PM, UCAC4 PM from Occelmnt `<Errors>` ✨ NEW!
- **Star position uncertainty:** From Occelmnt `<Errors>` index 4 (1-sigma in arcsec) ✨ NEW!
- **Asteroid motion coefficients:** dX, dY, d2X, d2Y, d3X, d3Y from Occelmnt `<Elements>` ✨ NEW!
- **Asteroid diameter & uncertainty:** From Occelmnt `<Object>` indices 3, 10 ✨ NEW!
- **Asteroid magnitude:** From Occelmnt `<Object>` index 12 (MagV) ✨ NEW!
- Asteroid number and name (from Occelmnt or event data)
- Observer location (lat/lon/elevation)
- Observer name and contact info
- Telescope aperture and type
- Camera information
- **D and R OBSERVED times** (from AOTA Report)
- D and R uncertainties (from AOTA Report)
- Signal-to-noise ratio (from AOTA Report)

### ✗ NOT Available (Use Defaults)
- Gaia version and ID (unless parsed from catalog name)
- **RA/Dec Apparent coordinates** - ~~NOT available~~ **NOW AVAILABLE from Occelmnt!** ✓
- **Stellar diameter** - ~~Often null~~ **NOW AVAILABLE from Occelmnt!** ✓
- **Asteroid motion coefficients** - ~~Need ephemeris~~ **NOW AVAILABLE from Occelmnt!** ✓
- Parallax and dParallax (still not available - would need separate calculation)
- **Asteroid diameter uncertainty** - ~~Not available~~ **NOW AVAILABLE from Occelmnt!** ✓
- Second observer names
- Observing conditions (stability, transparency) - need user input
- Time adjustment value
- Personal equation (PEqn)
- Plot codes

### ⚠ Needs Calculation/Mapping
- Hour as decimal (from datetime)
- DMS format coordinates (from decimal degrees)
- Telescope type code (from telescope type string)
- Observing method code (from camera data)
- Time source code (from camera timing)
- Event code (from observation_type)
- Weight (could calculate from SNR)
- **RA/Dec uncertainty apportionment** (convert 1-sigma position error to separate RA/Dec uncertainties)

### 🔑 Key Distinction
- **PREDICTION data** (from OWC/Occelmnt): Event time, location → goes in `<Prediction>` line
- **OBSERVED data** (from AOTA Report): D/R times, uncertainties, SNR → goes in `<D>` and `<R>` lines

### ⭐ Occelmnt Data Priority
When both OWC and Occelmnt have the same data, **prefer Occelmnt** as it contains the authoritative Occult4 calculation results with higher precision and more complete information.

**Occelmnt provides:**
- More precise star coordinates (J2000 and Apparent)
- Complete star photometry (Mb, Mv, Mr)
- Star quality metrics (RUWE, duplicate flags, proper motion flags)
- Asteroid motion coefficients (all orders)
- Asteroid diameter with uncertainty
- Position uncertainties

**OWC provides:**
- Event logistics (station names, times, locations)
- Observing conditions at prediction time
- Quick reference magnitudes
- Event ranking and metadata

---

## Implementation Notes

1. **Occelmnt access pattern:**
   ```python
   if event.original_data.get('occelmnt'):
       occelmnt = event.original_data['occelmnt']
       try:
           elements = occelmnt['Occultations']['Event']['Elements'].split(',')
           star = occelmnt['Occultations']['Event']['Star'].split(',')
           obj = occelmnt['Occultations']['Event']['Object'].split(',')
           errors = occelmnt['Occultations']['Event']['Errors'].split(',')
           # Extract data with proper error handling
       except (KeyError, IndexError) as e:
           # Fall back to OWC data
   ```

2. **Parser functions needed:**
   - Parse star catalog name from star_id or star[0] string
   - Parse asteroid number from object_name or object[0] string
   - Convert decimal degrees/hours to DMS format
   - Convert 1-sigma position error to RA/Dec uncertainties
   - Map telescope type string to code
   - Map camera data to observing method code
   - Map timing info to time source code
   - Map observation_type to event code

3. **Data validation:**
   - Check for missing Occelmnt data (fall back to OWC data)
   - Check for missing AOTA report data (D/R times)
   - Check for missing telescope/camera selection
   - Validate coordinate ranges
   - Validate time formats
   - Handle empty/null fields in Occelmnt CSV data

4. **Default values:**
   - Use "0" for unavailable numeric fields
   - Use blank string "" for unavailable text fields
   - Use "_" for unstated observing conditions
   - Use "-1" for not-specified flags

5. **Precision requirements:**
   - RA J2000: 10 decimal places (from Occelmnt star[1])
   - Dec J2000: 9 decimal places (from Occelmnt star[2])
   - RA Apparent: 8 decimal places (from Occelmnt star[9])
   - Dec Apparent: 7 decimal places (from Occelmnt star[10])
   - Magnitudes: 2 decimal places
   - Times: Typically 1-2 decimal places on seconds
   - Motion coefficients: Use full precision from Occelmnt
