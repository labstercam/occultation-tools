# OBS.XML Requirements for Single Observation Reporting

## Overview
This document identifies which sections of the OBS.XML format (v2.15+) are required for single observation reporting versus multi-chord analysis.

## Core Structure (Always Required)

```xml
<AsteroidOccultations>
   <FileVersion>2.15</FileVersion>
   <Event>
        <Date>year|month|day|hour</Date>
        <Details>
           <Star>...</Star>
           <StarIssues>...</StarIssues>
           <Asteroid>...</Asteroid>
        </Details>
        <Observations>
           <Prediction>...</Prediction>
           <Observer>
               <ID>...</ID> 
               <Conditions>...</Conditions>
               <D>...</D>
               <R>...</R> 
           </Observer>
        </Observations>
        <Added>yyyy|m|d</Added>
        <LastEdited>yyyy|m|d</LastEdited>
   </Event>
</AsteroidOccultations>
```

## Required Sections for Single Observations

### 1. File-level (Always Required)
- **`<FileVersion>`** - Format version (2.15)

### 2. Event-level (Always Required)
- **`<Date>`** - Event date and hour (4 fields: year|month|day|hour)

### 3. Details Section (Always Required)

#### `<Star>` (16 fields) - Star information
All fields required, though some may have default/unknown values:
1. Catalogue identifier (HIP, Tycho2, UCAC4, USNO-B1, NOMAD, G-coords, etc.)
2. Catalogue number
3. Gaia version (0-3, 9, or -1 for not specified)
4. Gaia ID (18-digit, or "0" if not available)
5. RA J2000 (hh.hhhhhhhhhh - 10 decimal places)
6. Dec J2000 (±dd.ddddddddd - 9 decimal places)
7. RA uncertainty (mas, or "0" if unknown)
8. Dec uncertainty (mas, or "0" if unknown)
9. Stellar diameter (mas, or "0" if unknown)
10. Issues flag (0=no issues, 1=high RUWE, 2=duplicate source, 3=both)
11. RA Apparent (hh.hhhhhhhh - 8 decimal places)
12. Dec Apparent (±dd.ddddddd - 7 decimal places)
13. Mb - Gaia blue magnitude (or use V mag)
14. Mg - Gaia G magnitude (or V magnitude)
15. Mr - Gaia red magnitude
16. EPIC ID (or blank)

#### `<StarIssues>` (11 fields) - Star quality metrics
All fields required, though most may have default values for single observations:
1. Reliability (RUWE for Gaia, or "0")
2. Gaia Duplicated Source flag (0/1/-1)
3. No Proper Motion flag (0/1/-1)
4. Proper motion using UCAC4 (0/1/-1)
5. Double star brightness ratio (default "1.2")
6. Brightness ratio uncertainty % (default "10")
7. Double star RA offset mas (default "0")
8. Double star Dec offset mas (default "0")
9. Std Dev RA offset mas (default "0")
10. Std Dev Dec offset mas (default "0")
11. Known double star component ID (or blank)

#### `<Asteroid>` (12 fields) - Asteroid information
All fields required, though motion coefficients may be zeros:
1. Asteroid number
2. Asteroid name
3. dX - motion coefficient (Earth radii/hr) - can be "0" for single obs
4. dY - motion coefficient (Earth radii/hr) - can be "0" for single obs
5. d2X - 2nd order coefficient (Earth radii/hr²) - can be "0" for single obs
6. d2Y - 2nd order coefficient (Earth radii/hr²) - can be "0" for single obs
7. d3X - 3rd order coefficient (Earth radii/hr³) - can be "0" for single obs
8. d3Y - 3rd order coefficient (Earth radii/hr³) - can be "0" for single obs
9. Parallax (arcsec) - can be "0" for single obs
10. dParallax (arcsec/hr) - can be "0" for single obs
11. Nominal mean diameter (km) - can be "0" if unknown
12. Uncertainty in diameter (km) - can be "0" if unknown
13. Mv - Visual magnitude - can be "0" if unknown

### 4. Observations Section (Always Required)

#### `<Prediction>` (7 fields) - Predicted event location
1. Sequential number
2. Longitude (±ddd mm ss.s format)
3. Latitude (±dd mm ss.s format)
4. Hour (hh)
5. Minute (mm)
6. Second (ss.s)
7. Event comments (free text, or blank)

#### `<Observer>` section - Repeated for each observer

##### `<ID>` (14 fields) - Observer and equipment details
1. Sequential number
2. Observer1 name
3. Observer2 name (or blank)
4. More than 2 observers (or blank)
5. Located near (location reference, or blank)
6. State/country (2-3 letter code)
7. Longitude (±ddd mm ss.s)
8. Latitude (±dd mm ss.ss)
9. Altitude (m)
10. Datum (_=WGS84, N=NAD1927, E=ED1950, T=Tokyo, G=GB1936, *=other)
11. Telescope aperture (cm)
12. Telescope type (0-8: _=unstated, 1=Refractor, 2=Newtonian, 3=SCT, 4=Dobsonian, 5=Binoculars, 6=Other, 7=None, 8=Electronic)
13. Observing method (blank=unspecified, a=Analogue/digital video, b=Digital SLR video, c=Photometer, d=Sequential images, e=Drift scan, f=Visual, g=Other)
14. Time source (blank=unspecified, a=GPS, b=NTP, c=Telephone, d=Radio, e=Internal clock, f=Stopwatch, g=Other)

##### `<Conditions>` (5 fields) - Observing conditions
1. Stability (_=unstated, 1=Steady, 2=Slight flickering, 3=Strong flickering)
2. Transparency (_=unstated, 1=Clear, 2=Fog, 3=Thin cloud <2 mag, 4=Thick cloud >2 mag, 5=Broken cloud, 6=Star faint, 7=Averted vision)
3. S/N ratio (signal-to-noise, or blank)
4. Time adjustment (or blank)
5. Comment (free text, or blank)

##### `<D>` (6 fields) - Disappearance event
1. Time (hh mm ss.ss)
2. Event code (P=Positive, p=probable positive, M=Miss/non-detection, m=probable miss, N=ring detection, n=ring non-detection, U=uncertain, Z=clouded out)
3. Accuracy (seconds, or blank)
4. PEqn (timing equation correction, or blank)
5. Weight (0-10, or blank)
6. Plot code (or blank)

##### `<R>` (6 fields) - Reappearance event
Same structure as `<D>` line

### 5. Metadata (Always Required)
- **`<Added>`** - Date added (yyyy|m|d)
- **`<LastEdited>`** - Date last edited (yyyy|m|d)

## Sections NOT Required for Single Observations

According to the obs.md specification, these sections are **OPTIONAL** and only appear under specific conditions:

### 1. `<EventFits>` - NOT REQUIRED for initial single observation reports
**When it appears:** Only after IOTA processes multiple observations and performs fitting
**Contains:**
- `<SolveFlags>` - Automatic fitting parameters (9 fields)
- `<EllipticFit>` - Ellipse fit to observations (10 fields)
- `<EllipseUncertainty>` - Standard deviations (5 fields)
- `<ShapeModelFit>` - Shape model fitting (optional, multiple entries)
- `<SatelliteFit>` - Satellite fitting (optional, multiple entries)
- `<DoubleStar>` - Double star solution (optional, 1-4 entries)

**Reason:** This section contains the results of fitting an ellipse or shape model to multiple chords. Single observations don't have this analysis yet.

### 2. `<Astrometry>` - NOT REQUIRED for single observations
**When it appears:** Per specification: "This group only appears if the quality setting under EllipticFit is greater than 0."

**Contains:**
- `<ReferenceTime>` - Astrometric reference time (6 fields)
- `<MainBody>` - Geocentric position and uncertainties (17 fields)
- `<MainAtConjunction>` - Position at conjunction (4 fields)
- `<SatelliteBodies>` - Satellite astrometry (optional, multiple entries)
- `<MPC>` - Minor Planet Center publication info (3 fields)

**Reason:** Astrometry section contains the astrometric solution derived from fitting multiple observations. This requires:
- Multiple chords to determine asteroid position
- Uncertainty analysis across observations
- Geocentric coordinate calculations
- This is computed by IOTA after collecting observations from multiple sites

### 3. Optional subsections that may appear in special cases:
- `<ShapeModelFit>` - Only if shape model fitting was performed
- `<SatelliteFit>` - Only if satellite detected
- `<DoubleStar>` - Only if double star detected
- `<SatelliteBodies>` under Astrometry - Only if satellite astrometry computed

## Summary for Implementation

**For single observation reporting, export:**
✅ FileVersion
✅ Date
✅ Star (with available data, defaults for unknowns)
✅ StarIssues (with available data, defaults for unknowns)
✅ Asteroid (with available data, zeros for motion coefficients if unknown)
✅ Prediction
✅ Observer section (ID, Conditions, D, R)
✅ Added/LastEdited dates

**Do NOT export:**
❌ EventFits section - Added by IOTA after multi-chord analysis
❌ Astrometry section - Added by IOTA after computing astrometric solution

## Data Availability for Single Observations

From our AOTA/NA reports we have:
- ✅ Basic event data (date, time, location)
- ✅ Observer information (name, location, equipment)
- ✅ Star identification and coordinates (from event data)
- ✅ Asteroid identification (from event data)
- ✅ Observation timing (D and R times from Tangra/AOTA)
- ✅ Observing conditions (from observer notes)
- ✅ Event code (Positive/Negative from observation type)
- ✅ S/N ratio (from Tangra analysis)
- ✅ Timing accuracy (from Tangra analysis)

From OWC downloads we could get additional prediction data, but this is optional for the basic report.

The asteroid motion coefficients (dX, dY, d2X, etc.) and parallax would need to come from ephemeris calculations, but can be set to "0" for initial reporting if not available.
