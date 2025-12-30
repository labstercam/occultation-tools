# OWC Data vs OBS.XML Field Mapping Analysis

## Summary
This document compares fields available from OccultWatcher Cloud (OWC) API downloads with the fields required for Occult4 OBS.XML format (version 2.15).

## OWC Data Fields Available

From `owc_downloaded_events.json`, the following fields are available:

### Event-level fields:
- `Id` - Event UUID
- `Object` - Asteroid name/designation (e.g., "(119355) 2001 SU232")
- `StarName` - Star catalogue designation (e.g., "UCAC4 570-020044")
- `OtherStarNames` - Alternative star names
- `RAJ2000Hours` - RA J2000 in hours
- `DEJ2000Deg` - Dec J2000 in degrees
- `RAHours` - RA apparent in hours
- `DEDeg` - Dec apparent in degrees
- `StarMag` - Star magnitude
- `AstMag` - Asteroid magnitude
- `CombMag` - Combined magnitude
- `MagDrop` - Magnitude drop
- `BV` - B-V color index
- `StellarDiaMas` - Stellar diameter in mas (often null)
- `EventTimeUtc` - Event time UTC
- `MaxDurSec` - Maximum duration in seconds
- `ErrorInTimeSec` - Time error in seconds
- `AstDiaKm` - Asteroid diameter in km
- `AstDistUA` - Asteroid distance in AU
- `AstRotationHrs` - Asteroid rotation period (often null)
- `AstRotationAmplitude` - Asteroid rotation amplitude (often null)
- `OneSigmaErrorWidthKm` - 1-sigma error width in km
- `PredictionUpdated` - Timestamp of prediction update
- `Rank` - Event rank
- `AstClass` - Asteroid class
- `Feed` - Data feed ("OWC")

### Station-level fields (under Stations array):
- `StationId` - Station ID
- `StationName` - Station name
- `Latitude` - Station latitude
- `Longitude` - Station longitude
- `IsOwnStation` - Boolean
- `IsPrimaryStation` - Boolean
- `EventTimeUtc` - Event time at station
- `ChordOffsetKm` - Chord offset in km
- `OccultDistanceKm` - Occultation distance in km
- `StarAlt` - Star altitude
- `StarAz` - Star azimuth
- `SunAlt` - Sun altitude
- `MoonAlt` - Moon altitude
- `MoonAz` - Moon azimuth
- `MoonDist` - Moon distance
- `MoonPhase` - Moon phase
- `StarColour` - Star color code
- `CombMag` - Combined magnitude at station
- `ErrorInTimeSec` - Time error at station
- `Report` - Report code
- `ReportComment` - Report comment
- `ReportedDuration` - Reported duration
- Weather-related fields (WeatherInfoAvailable, TempDegC, Wind, CloudCover, HighCloud)

## OBS.XML Required Fields

### Date Line:
- ✅ Year - derivable from EventTimeUtc
- ✅ Month - derivable from EventTimeUtc
- ✅ Day - derivable from EventTimeUtc
- ✅ Hour - derivable from EventTimeUtc

### Star Line (16 fields):
1. ✅ Catalogue - parseable from StarName (e.g., "UCAC4")
2. ✅ Number - parseable from StarName (e.g., "570-020044")
3. ❌ **Gaia version** - NOT available (0=Hipparcos2, 1=DR1, 2=DR2, 3=EDR3, 9=UBSC, -1=not specified)
4. ❌ **Gaia id** - NOT available (18-digit Gaia id)
5. ✅ RA2000 (hh.hhhhhhhhhh) - available as RAJ2000Hours (10 decimal places required)
6. ✅ Dec2000 (±dd.ddddddddd) - available as DEJ2000Deg (9 decimal places required)
7. ❌ **RA uncertainty (mas)** - NOT available
8. ❌ **Dec uncertainty (mas)** - NOT available
9. ⚠️ Stellar diameter (mas) - available as StellarDiaMas but often null
10. ❌ **IssuesFlag** - NOT available (0=no issues, 1=high RUWE, 2=duplicate source, 3=both)
11. ✅ RA Apparent (hh.hhhhhhhh) - available as RAHours (8 decimal places required)
12. ✅ Dec Apparent (±dd.ddddddd) - available as DEDeg (7 decimal places required)
13. ❌ **Mb** - NOT available (Gaia blue magnitude)
14. ⚠️ Mg - available as StarMag (Gaia G magnitude or V magnitude) (2 decimal places required)
15. ❌ **Mr** - NOT available (Gaia red magnitude)
16. ❌ **EPIC ID** - NOT available (Kepler2 mission ID)

### StarIssues Line (11 fields):
1. ❌ **Reliability** - NOT available (RUWE for Gaia stars)
2. ❌ **Gaia Duplicated Source flag** - NOT available (0/1/-1)
3. ❌ **No Proper Motion flag** - NOT available (0/1/-1)
4. ❌ **Proper motion using UCAC4** - NOT available (0/1/-1)
5. ❌ **Double star solution - star brightness ratio** - NOT available
6. ❌ **Uncertainty in star brightness ratio (%)** - NOT available
7. ❌ **Double star solution RA offset (mas)** - NOT available
8. ❌ **Double star solution Dec offset (mas)** - NOT available
9. ❌ **Standard Deviation RA offset (mas)** - NOT available
10. ❌ **Standard Deviation Dec offset (mas)** - NOT available
11. ❌ **Known double star component ID** - NOT available

### Asteroid Line (12 fields):
1. ✅ Number - parseable from Object field
2. ✅ Name - parseable from Object field
3. ❌ **dX** - NOT available (coefficient 'a' in X, Earth radii/hr)
4. ❌ **dY** - NOT available (coefficient 'a' in Y, Earth radii/hr)
5. ❌ **d2X** - NOT available (coefficient 'b' in X, Earth radii/hr²)
6. ❌ **d2Y** - NOT available (coefficient 'b' in Y, Earth radii/hr²)
7. ❌ **d3X** - NOT available (coefficient 'c' in X, Earth radii/hr³)
8. ❌ **d3Y** - NOT available (coefficient 'c' in Y, Earth radii/hr³)
9. ❌ **Parallax** - NOT available (arcsec at event hour)
10. ❌ **dParallax** - NOT available (hourly rate of change in parallax)
11. ⚠️ Nominal mean diameter (km) - available as AstDiaKm
12. ❌ **Uncertainty in mean diameter (km)** - NOT available
13. ⚠️ Mv - available as AstMag (2 decimal places required)

### EventFits Section:
- ❌ **SolveFlags** - NOT available (9 flags for automatic fitting)
- ❌ **EllipticFit** - NOT available (10 fields: X, Y, axes, PA, quality, etc.)
- ❌ **EllipseUncertainty** - NOT available (5 standard deviation fields)
- ❌ **ShapeModelFit** - NOT available (optional, 8 fields per fit)
- ❌ **SatelliteFit** - NOT available (optional, 13 fields per satellite)
- ❌ **DoubleStar** - NOT available (optional, JDSO and solution data)

### Astrometry Section:
- ❌ **ReferenceTime** - NOT available (6 fields: year, month, day, hour, uncertainty, across-path uncertainty)
- ❌ **MainBody** - NOT available (17 fields: designation, geocentric X/Y, rates, uncertainties, etc.)
- ❌ **MainAtConjunction** - NOT available (4 fields)
- ❌ **SatelliteBodies** - NOT available (optional)
- ❌ **MPC** - NOT available (3 fields: publication date, circular number, submission ID)

### Observations Section:

#### Prediction Line (7 fields):
1. ✅ Seq Num - can be assigned
2. ✅ Longitude - available from Stations[].Longitude
3. ✅ Latitude - available from Stations[].Latitude
4. ✅ hr - derivable from EventTimeUtc
5. ✅ min - derivable from EventTimeUtc
6. ✅ sec - derivable from EventTimeUtc
7. ⚠️ Event comments - NOT directly available from OWC (could use blank or synthesize from available data)

#### Observer ID Line (14 fields):
1. ✅ Seq Num - can be assigned
2. ✅ Observer1 - available from StationName
3. ⚠️ Observer2 - NOT available (could use blank)
4. ⚠️ MoreThan2Observers - NOT available (could use blank)
5. ⚠️ NearLocation - NOT available (could use blank)
6. ❌ **State/country** - NOT available (2-3 letter code from OWC, CountryCode is null in sample)
7. ✅ Longitude - available from Stations[].Longitude
8. ✅ Latitude - available from Stations[].Latitude
9. ❌ **Alt (m)** - NOT available (elevation in sample is unlabeled)
10. ⚠️ Datum - NOT available (could default to "_" for WGS84)
11. ❌ **TelescopeAperture (cm)** - NOT available
12. ⚠️ TelescopeType - NOT available (could default to "_" for unstated)
13. ⚠️ Observing method - NOT available (could default to blank for unspecified)
14. ⚠️ Time Source - NOT available (could default to blank for unspecified)

#### Conditions Line (5 fields):
1. ⚠️ Stability - NOT available (could default to "_" for unstated)
2. ⚠️ Transparency - NOT available (could default to "_" for unstated)
3. ❌ **SN** - NOT available (signal-to-noise ratio)
4. ❌ **Time Adjustment** - NOT available
5. ⚠️ Comment - available from ReportComment (often null)

#### D Line (Disappearance, 6 fields):
1. ❌ **hh mm ss.ss** - NOT available (actual observed time from observation)
2. ❌ **eventCode** - NOT available (P/p/N/n/M/m/etc.)
3. ❌ **Accuracy** - NOT available
4. ❌ **PEqn** - NOT available
5. ❌ **Weight** - NOT available
6. ❌ **PlotCode** - NOT available

#### R Line (Reappearance, 6 fields):
1. ❌ **hh mm ss.ss** - NOT available (actual observed time from observation)
2. ❌ **eventCode** - NOT available (P/p/N/n/M/m/etc.)
3. ❌ **Accuracy** - NOT available
4. ❌ **PEqn** - NOT available
5. ❌ **Weight** - NOT available
6. ❌ **PlotCode** - NOT available

### Added/LastEdited Lines:
- ⚠️ Added date - NOT available (could use current date or PredictionUpdated)
- ⚠️ LastEdited date - NOT available (could use current date)

## Summary Statistics

### Available from OWC: ~35 fields (including derived/parseable)
- Basic star coordinates (RA/Dec J2000 and apparent)
- Basic asteroid data (number, name, diameter, magnitude)
- Station location (lat/lon)
- Event timing (UTC timestamp)
- Star magnitude, combined magnitude, magnitude drop
- Prediction metadata

### Missing from OWC: ~120+ fields
- **All Gaia quality metrics** (version, ID, RUWE, duplicated source flag, proper motion flags)
- **All star uncertainties** (RA/Dec uncertainties in mas)
- **All Gaia photometry** (Mb, Mr magnitudes)
- **All double star data** (brightness ratios, offsets, component IDs)
- **All asteroid motion coefficients** (dX, dY, d2X, d2Y, d3X, d3Y)
- **All parallax data** (parallax, dParallax)
- **All EventFits data** (elliptic fit, uncertainties, shape models, satellites, double stars)
- **All Astrometry data** (reference time, geocentric positions, rates, uncertainties, MPC info)
- **All actual observation data** (D/R times, event codes, accuracy, weights, plot codes)
- **All telescope/equipment data** (aperture, type, observing method, time source)
- **All observing conditions** (stability, transparency, S/N)
- **State/country codes** (CountryCode is null in samples)

### Partially Available: ~10 fields
- Stellar diameter (StellarDiaMas often null)
- Observer names (only StationName available)
- Event comments (not directly available)
- Datum (can default)
- Telescope type (can default)
- Observing method (can default)
- Time source (can default)
- Conditions (can default)

## Conclusion

**OWC data contains only basic prediction data (~25% of OBS.XML requirements).** It is fundamentally **NOT suitable** for generating complete OBS.XML files because:

1. **Missing critical observation data**: D/R times, event codes, accuracy - these are the actual observation results
2. **Missing all astrometric solution data**: The entire purpose of OBS.XML is to report astrometric solutions
3. **Missing all fit data**: Elliptic fits, shape model fits, uncertainties
4. **Missing all Gaia quality metrics**: Required for assessing star position reliability
5. **Missing telescope/equipment data**: Required for observation validation

## Recommendation

OWC data should **NOT** be used as the source for generating Occult4 XML exports. The XML export should only be generated from:

1. **NA (North American) reports** - which contain actual observation data
2. **TT (Tangra/AOTA) reports** - which contain actual observation data
3. **Occult4 software output** - which contains the complete astrometric solution

The current implementation in `occult4_export.py` that sources data from AOTA/NA reports is the correct approach. The tool should never attempt to generate XML from OWC downloads alone.
