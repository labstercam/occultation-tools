# SODIS / IOTA-ES Text Files: Verified Content Analysis

## Implementation status (March 2026)

SODIS support based on these source files is now implemented in the report workflow:
- Report format option: `IOTA-ES / SODIS (Form 2.03)` in `comprehensive_report_dialog.py`
- Generator: `SODISReportGeneratorText` in `sodis_report_text.py`
- Main flow wiring: `main_gui.py` report-type branch (`report_type == 'sodis'`)
- Camera/report profile filtering includes `SODIS`
- Output file generation uses the installed resources template and writes plain-text reports

This document remains the verified source-content analysis for the `IOTA-ES_*` files used by the implementation.

## Sources reviewed (exact)
- `occultation-manager/python/IOTA-ES_report.txt`
- `occultation-manager/python/IOTA-ES_Sample-report-positiv.txt`
- `occultation-manager/python/IOTA-ES_Sample-report-negativ.txt`

## Important naming note
The files present in the repository are named `IOTA-ES*`.
No `IOTA-EA*` files were found during this review.

## Header/version (exact text)
All three files start with:

`#IOTA-ES ASTEROIDAL OCCULTATION - REPORT FORM 2.03`

## File shape and syntax (observed)
- Every line in all three files begins with `#`.
- Data-bearing lines follow `#FieldName: value`.
- Section lines also begin with `#` (for example `#Event`, `#OBSERVER`, `#OBSERVING_STATION`, `#Observation`, `#Weatherconditions`).
- The template includes explanatory lines that are not key-value pairs (for example code legends).

## Field order (observed in all three)
The same overall order appears in template and both samples:
1. Event block
2. Observer block
3. Observing station block
4. Equipment/method lines
5. Observation lines
6. Timesource/camera lines
7. Weatherconditions lines

## Event block fields (exact keys)
- `Occultation`
- `DATE`
- `PREDICTTIME`
- `STAR`
- `ASTEROID`
- `Nr`

Observed values in samples:
- Positive sample: `Occultation: POSITIVE`
- Negative sample: `Occultation: NEGATIVE`
- Template placeholder: `Occultation: xxxxTIVE`

## Observer block fields (exact keys)
- `Observer1`
- `Observer2`
- `moreObs`
- `E-mail`
- `Address`

## Observing station block fields (exact keys)
- `NearestCity`
- `Countrycode`
- `Latitude`
- `Longitude`
- `Altitude`
- `Datum`

Template guidance lines (exactly present):
- `#Coordinates LAT +/-DD MM SS.S  LON +/-DDD MM SS.S`
- `#Datum _blank=WGS84 N=NAD1927 E=ED1950 T=Tokyo G=GB1936 *=unspecified, or other`

Observed coordinate formatting in samples:
- Latitude example: `+52 58 48.5` and `+52 01 02.5`
- Longitude example: `+013 22 13.7` and `+013 45 58.7`

## Equipment/method fields (exact keys)
- `Telescope`
- `Aperture`
- `FocalLength`
- `ObservingMethod`

Template guidance lines (exactly present):
- `#Teleskop _=unstated 1=Refractor 2=Newtonian 3=SCT 4=Dobsonian 5=Binoculars 6=Other 7=None 8=eVscope`
- `#Aperture in cm`
- `#FocalLength in cm`
- `#ObservingMethod   _=unspecified a=Analogue & digital video b=Digital SLR-camera video c=Photometer d=Sequential images e=Drift scan f=Visual g=Other`

Observed in both samples:
- `Telescope: 3`
- `Aperture: 36`
- `FocalLength: 277`
- `ObservingMethod: a`

## Observation fields (exact keys)
- `StartObs`
- `D`
- `Acc_D`
- `R`
- `Acc_R`
- `EndObs`
- `Duration`
- `Exp_Time`

Template guidance lines (exactly present):
- `#D D=Main Star d=second Star G=satellite main star g=satellite 2nd star N=ring  M=non detection +time hh:mm:ss.s`
- `#R R=Main Star r=second Star B=satellite main star b=satellite 2nd star N=ring  M=non detection +time hh:mm:ss.s`

Observed positive sample values:
- `D: D20:02:30.0`
- `Acc_D: 0.5`
- `R: R20:02:34.0`
- `Acc_R: 0.5`

Observed negative sample values:
- `D: M`
- `Acc_D:` (empty)
- `R: M`
- `Acc_R:` (empty)

## Timesource/camera fields (exact keys)
- `Timesource`
- `Camera`
- `Signal/Noise`

Template guidance line (exactly present):
- `#Timesource  _=unspecified a=GPS b=NTP c=Telephone (fixed or mobile) d=Radio time signal e=Internal clock of recorder f=Stopwatch g=Other`

Observed in samples:
- `Timesource: a`
- `Camera: QHY174M GPS`
- `Signal/Noise:` (empty)

## Weatherconditions fields (exact keys)
- `Wind`
- `Temperature`
- `Transparency`
- `Stability`
- `Comments`

Template guidance lines (exactly present):
- `#Transparency 1=Clear 2=Fog 3=Thin cloud <2 [mag loss <2 mag.] 4=Thick cloud >2 [mag loss >2 mag. 5=Broken opaque cloud [that is, observed thru gaps in the cloud] 6=Star faint 7=By averted vision`
- `#Stability _=unstated 1=Steady 2=Slight flickering 3=Strong flickering`

Observed in samples:
- Positive sample: `Transparency: 1`, `Stability: 1`
- Negative sample: `Transparency: 3`, `Stability: 1`

## Precision and formatting observations (only what is visible)
- `StartObs` / `EndObs` in samples show two decimal places in seconds (for example `20:01:34.99`).
- Positive sample `D` / `R` embedded times show one decimal place (`...30.0`, `...34.0`).
- `Exp_Time` values shown as `1.0` and `1.5` in samples.
- `Duration` shown as `4.0` in positive sample and empty in negative sample.

## Explicit ambiguities / not derivable from these files alone
- No machine-readable schema file is included; cardinality/requiredness beyond visible examples is not formally declared.
- The exact rule for `PREDICTTIME` formatting is not defined in the template beyond free text examples.
- The exact required format for `D`/`R` (for example separator between code and time) is not explicitly constrained beyond template comment text; sample uses concatenated form like `D20:02:30.0`.
- The semantic definition of `Signal/Noise` units/format is not provided in these files.
- The meaning/units for `Wind` and `Temperature` are not specified in the template comments.

## Accuracy statement
This document intentionally records only content that is directly observable in the three `IOTA-ES*.txt` files above, plus explicit ambiguity where those files do not define a rule.
