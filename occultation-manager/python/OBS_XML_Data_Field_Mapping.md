# OBS.XML Data Field Mapping

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

### 4. Tangra Light Curve Data
Structure not yet fully defined, but likely includes:
- Light curve data points
- Event detection parameters
- Additional SNR metrics

### 5. OWC Downloaded Events (from owc_downloaded_events.json)
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

### 6. User Input / Observation Type
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
| 1. Catalogue | Event | Parse from `event.star_id` | - | e.g., "UCAC4" from "UCAC4 570-020044" |
| 2. Number | Event | Parse from `event.star_id` | - | e.g., "570-020044" |
| 3. Gaia version | **NOT AVAILABLE** | - | - | Use -1 (not specified) unless catalog is "Gaia DR3" etc. |
| 4. Gaia id | **NOT AVAILABLE** | - | - | Use "0" unless Gaia catalog identified |
| 5. RA J2000 | Event | `event.ra_hours` (from OWC `RAJ2000Hours`) | 10 decimals | hh.hhhhhhhhhh format |
| 6. Dec J2000 | Event | `event.dec_degrees` (from OWC `DEJ2000Deg`) | 9 decimals | ±dd.ddddddddd format with sign |
| 7. RA uncertainty | **NOT AVAILABLE** | - | - | Use "0" |
| 8. Dec uncertainty | **NOT AVAILABLE** | - | - | Use "0" |
| 9. Stellar diameter | OWC Raw | `StellarDiaMas` from OWC | - | Often null, use "0" if not available |
| 10. Issues flag | **NOT AVAILABLE** | - | - | Use "0" (no issues) |
| 11. RA Apparent | **NOT AVAILABLE** | - | 8 decimals | Use "0.00000000" - not provided by OWC |
| 12. Dec Apparent | **NOT AVAILABLE** | - | 7 decimals | Use "+0.0000000" - not provided by OWC |
| 13. Mb | **NOT AVAILABLE** | - | 2 decimals | Use star_mag or "0" |
| 14. Mg | Event | `event.star_mag` | 2 decimals | Gaia G or V magnitude |
| 15. Mr | **NOT AVAILABLE** | - | 2 decimals | Use star_mag or "0" |
| 16. EPIC ID | **NOT AVAILABLE** | - | - | Leave blank |

#### StarIssues Line (11 fields)
**XML Format:** `<StarIssues>Reliability|Dup flag|No PM|UCAC4 PM|Brightness ratio|Ratio unc%|RA offset|Dec offset|RA sdev|Dec sdev|Component ID</StarIssues>`

| Field | Source | Value | Notes |
|-------|--------|-------|-------|
| 1. Reliability | **NOT AVAILABLE** | "0" | RUWE not available |
| 2. Duplicated Source flag | **NOT AVAILABLE** | "-1" | Not specified |
| 3. No Proper Motion | **NOT AVAILABLE** | "-1" | Not specified |
| 4. UCAC4 Proper Motion | **NOT AVAILABLE** | "0" | Not applicable |
| 5. Brightness ratio | Default | "1.2" | Default value |
| 6. Ratio uncertainty % | Default | "10" | Default value |
| 7. RA offset mas | Default | "0" | No double star solution |
| 8. Dec offset mas | Default | "0" | No double star solution |
| 9. RA sdev mas | Default | "0" | No double star solution |
| 10. Dec sdev mas | Default | "0" | No double star solution |
| 11. Component ID | **NOT AVAILABLE** | "" | Blank |

#### Asteroid Line (12 fields)
**XML Format:** `<Asteroid>Number|Name|dX|dY|d2X|d2Y|d3X|d3Y|Parallax|dParallax|Diameter|Diameter unc|Mv</Asteroid>`

| Field | Source | Data Path | Notes |
|-------|--------|-----------|-------|
| 1. Number | Event | Parse from `event.object_name` | Extract number from "(119355) 2001 SU232" |
| 2. Name | Event | Parse from `event.object_name` | Extract name, remove number |
| 3. dX | **NOT AVAILABLE** | "0" | Motion coefficient - need ephemeris |
| 4. dY | **NOT AVAILABLE** | "0" | Motion coefficient - need ephemeris |
| 5. d2X | **NOT AVAILABLE** | "0" | Motion coefficient - need ephemeris |
| 6. d2Y | **NOT AVAILABLE** | "0" | Motion coefficient - need ephemeris |
| 7. d3X | **NOT AVAILABLE** | "0" | Motion coefficient - need ephemeris |
| 8. d3Y | **NOT AVAILABLE** | "0" | Motion coefficient - need ephemeris |
| 9. Parallax | **NOT AVAILABLE** | "0" | Need ephemeris calculation |
| 10. dParallax | **NOT AVAILABLE** | "0" | Need ephemeris calculation |
| 11. Diameter | OWC Raw | `AstDiaKm` | From OWC, use "0" if not available |
| 12. Diameter unc | **NOT AVAILABLE** | "0" | Not provided by OWC |
| 13. Mv | OWC Raw | `AstMag` | From OWC, use "0" if not available |

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

### ✅ Available from Current Sources
- Event date/time (PREDICTION from OWC)
- Star catalog and coordinates (RA/Dec J2000 from OWC `RAJ2000Hours` and `DEJ2000Deg`)
- Star magnitude
- Asteroid number and name
- Observer location (lat/lon/elevation)
- Observer name and contact info
- Telescope aperture and type
- Camera information
- **D and R OBSERVED times** (from AOTA Report)
- D and R uncertainties (from AOTA Report)
- Signal-to-noise ratio (from AOTA Report)

### ❌ NOT Available (Use Defaults)
- Gaia version and ID (unless parsed from catalog)
- Star position uncertainties (RA/Dec)
- Gaia quality flags (RUWE, duplicate source, proper motion)
- Gaia photometry (Mb, Mr magnitudes)
- **RA/Dec Apparent coordinates** (different from J2000, not provided by OWC)
- Stellar diameter (sometimes available, often null)
- Asteroid motion coefficients (dX, dY, d2X, d2Y, d3X, d3Y)
- Parallax data
- Asteroid diameter uncertainty
- Second observer names
- Observing conditions (stability, transparency)
- Time adjustment value
- Personal equation (PEqn)
- Plot codes

### ⚠️ Needs Calculation/Mapping
- Hour as decimal (from datetime)
- DMS format coordinates (from decimal degrees)
- Telescope type code (from telescope type string)
- Observing method code (from camera data)
- Time source code (from camera timing)
- Event code (from observation_type)
- Weight (could calculate from SNR)

### 🔑 Key Distinction
- **PREDICTION data** (from OWC): Event time, location → goes in `<Prediction>` line
- **OBSERVED data** (from AOTA Report): D/R times, uncertainties, SNR → goes in `<D>` and `<R>` lines

---

## Implementation Notes

1. **Parser functions needed:**
   - Parse star catalog name from star_id string
   - Parse asteroid number from object_name string
   - Convert decimal degrees to DMS format
   - Map telescope type string to code
   - Map camera data to observing method code
   - Map timing info to time source code
   - Map observation_type to event code

2. **Data validation:**
   - Check for missing AOTA report data (D/R times)
   - Check for missing telescope/camera selection
   - Validate coordinate ranges
   - Validate time formats

3. **Default values:**
   - Use "0" for unavailable numeric fields
   - Use blank string "" for unavailable text fields
   - Use "_" for unstated observing conditions
   - Use "-1" for not-specified flags

4. **Precision requirements:**
   - RA J2000: 10 decimal places
   - Dec J2000: 9 decimal places
   - RA Apparent: 8 decimal places
   - Dec Apparent: 7 decimal places
   - Magnitudes: 2 decimal places
   - Times: Typically 1-2 decimal places on seconds
