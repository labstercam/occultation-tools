# SODIS vs Current NA/TT Reporting: Verified Comparison Matrix

## Status note (March 2026)

This matrix captures the pre-implementation comparison baseline. SODIS is now implemented in the active workflow.

Implemented deltas relative to this baseline:
- SODIS report format option added in `comprehensive_report_dialog.py`
- Main report flow now routes `report_type == 'sodis'` in `main_gui.py`
- New text generator added: `sodis_report_text.py` (`SODISReportGeneratorText`)
- Shared camera profile support includes `SODIS`

Open items intentionally still outside MVP scope remain as documented in this matrix (for example full enum-code coverage for all optional SODIS fields and additional non-core weather/observer fields).

## Scope of comparison (exact files reviewed)
SODIS source files:
- `occultation-manager/python/IOTA-ES_report.txt`
- `occultation-manager/python/IOTA-ES_Sample-report-positiv.txt`
- `occultation-manager/python/IOTA-ES_Sample-report-negativ.txt`

Current reporting implementation files:
- `occultation-manager/python/comprehensive_report_dialog.py`
- `occultation-manager/python/main_gui.py` (report generation flow)
- `occultation-manager/python/na_report_openize.py`
- `occultation-manager/python/tt_report_openize.py`
- `occultation-manager/python/report_generator_base.py`

## Method
- This matrix is based only on observed code paths and observed SODIS text fields.
- If a mapping is not explicit in reviewed files, it is marked `Not explicit` or `Not mapped`.
- No inferred or speculative field transformations are asserted as facts.

---

## Report interface capability (current)

Observed in `comprehensive_report_dialog.py`:
- Report format options: `IOTA North America` and `Trans-Tasman / RASNZ` only.
- No SODIS/IOTA-ES option currently present in the dialog.
- User-selectable inputs include:
  - telescope
  - camera
  - observation type (Positive/Negative/Unsure)
  - Tangra CSV file
  - AOTA XML file (optional depending on observation type)
  - AOTA Report TXT file (optional depending on observation type)
  - clouds, stability, other_conditions

Observed in `main_gui.py` report flow:
- Tangra CSV is parsed to `tangra_data`.
- AOTA Report TXT is parsed to `aota_report_data`.
- If only AOTA XML is selected, selected AOTA event is converted into `aota_report_data`-like dictionary for Openize generation.

---

## Field-by-field matrix

Legend:
- `Mapped` = explicit write exists in reviewed NA/TT generator code.
- `Partial` = some part exists, but not equivalent to SODIS field semantics/format.
- `Not mapped` = no explicit corresponding write found in reviewed NA/TT generator code.
- `Not explicit` = code path exists but exact SODIS-equivalent transform is not defined.

| SODIS field | SODIS expectation (from text files) | Current NA/TT source in code | Interface/input source | Status |
|---|---|---|---|---|
| `Occultation` | POSITIVE/NEGATIVE text | NA/TT write observation type to cell `A2` (`self._observation_type`) | Observation Result radio buttons | Mapped (value family equivalent) |
| `DATE` | Date text | NA/TT write event date/time components to date/time cells (`D5`,`K5`,`P5`,`Y5`,`AA5`,`AC5`) | Event selected in main grid | Partial (different cell/form representation) |
| `PREDICTTIME` | Free text with UT in samples | NA/TT write event datetime components as above; no explicit SODIS-style combined text field | Event selected in main grid | Partial |
| `STAR` | Star identifier string | NA/TT parse and write star catalog/number (`S7`,`X7`) | Event star fields | Mapped (split representation) |
| `ASTEROID` | Asteroid name | NA/TT write asteroid name (`K7`) | Event object | Mapped |
| `Nr` | Asteroid number | NA/TT write asteroid number (`E7`) | Event object | Mapped |
| `Observer1` | Observer name | NA/TT write observer name (`D9`) | Config observer fields | Mapped |
| `Observer2` | Optional second observer | No explicit NA/TT write found for a second observer | Not collected in report dialog | Not mapped |
| `moreObs` | Additional observers | No explicit NA/TT write found | Not collected in report dialog | Not mapped |
| `E-mail` | Email | NA/TT write observer email (`S9`) | Config observer fields | Mapped |
| `Address` | Address | NA/TT write observer address (`D11`) | Config observer fields | Mapped |
| `NearestCity` | City text | NA/TT write combined city/state/country at `D13`; no dedicated nearest-city field | Config observer city/state/country | Partial |
| `Countrycode` | 2-letter code in samples (e.g. DE) | NA/TT write country as part of combined text at `D13`; no dedicated countrycode field write | Config observer country | Partial |
| `Latitude` | Signed DMS text (`+DD MM SS.S`) | NA/TT write decimal degrees abs + hemisphere (`E18` + `J18`) | Event location dialog result | Partial (different format) |
| `Longitude` | Signed DMS text (`+DDD MM SS.S`) | NA/TT write decimal degrees abs + hemisphere (`N18` + `R18`) | Event location dialog result | Partial (different format) |
| `Altitude` | Numeric text | NA/TT write elevation (`V18`) + unit (`W18`) | Event location dialog result | Mapped |
| `Datum` | code/blank convention | NA/TT write `WGS84` into `AA18` (when elevation present) | Not user-selectable in report dialog | Partial |
| `Telescope` | coded enum in SODIS template | NA/TT write telescope type string (`T20`) and not a SODIS numeric code | Telescope profile | Partial |
| `Aperture` | cm | NA/TT convert aperture mm->cm and write (`E20`) | Telescope profile | Mapped |
| `FocalLength` | cm | NA/TT write focal ratio (`L20`), not focal length cm | Telescope profile | Partial |
| `ObservingMethod` | coded enum (`a..g`) | TT writes `O22` = `Video Recording`; NA writes timing-related fields (`E22`, etc.), not SODIS enum code | Camera profile + fixed strings | Partial |
| `StartObs` | hh:mm:ss.s... | NA/TT write from Tangra start time (`F31`,`H31`,`J31`) | Tangra CSV parsed in main flow | Mapped |
| `D` | event code + time or `M` | NA writes D components from `aota_report_data` to (`F32`,`H32`,`J32`); TT writes to (`F33`,`H33`,`J33`) | AOTA Report or converted AOTA XML | Partial (time components mapped; SODIS code prefix semantics not represented) |
| `Acc_D` | uncertainty | NA `M33`; TT `M33` from `d_uncertainty` | AOTA Report or converted AOTA XML | Mapped |
| `R` | event code + time or `M` | NA writes R components to (`F36`,`H36`,`J36`); TT to (`F35`,`H35`,`J35`) | AOTA Report or converted AOTA XML | Partial (time components mapped; SODIS code prefix semantics not represented) |
| `Acc_R` | uncertainty | NA `M35`; TT `M35` from `r_uncertainty` | AOTA Report or converted AOTA XML | Mapped |
| `EndObs` | hh:mm:ss.s... | NA/TT write from Tangra end time (`F37`,`H37`,`J37`) | Tangra CSV parsed in main flow | Mapped |
| `Duration` | numeric or blank | No explicit duration write found in reviewed NA/TT openize code | Not directly collected in dialog | Not mapped |
| `Exp_Time` | numeric | NA derives integration info into comment area (`V25`) and sets method (`P25=Other`); TT writes exposure seconds to `P25` and units `S25` | Tangra CSV parsed | Partial |
| `Timesource` | coded enum (`a..g`) | NA writes camera timing strings (`E22`, `E23`); TT writes timing and `O22=Video Recording` | Camera profile fields | Partial |
| `Camera` | camera name/model text | NA comments include `Camera: <name>` in `D43`; TT writes detector field `E25` and camera other_info comments | Camera profile | Partial |
| `Signal/Noise` | value/blank | NA/TT write SNR from AOTA data to `W40` when available | AOTA Report parser | Mapped |
| `Wind` | value/blank | No explicit wind write in reviewed NA/TT code | Not collected in report dialog | Not mapped |
| `Temperature` | value/blank | No explicit temperature write in reviewed NA/TT code | Not collected in report dialog | Not mapped |
| `Transparency` | coded enum 1..7 | NA/TT write selected cloud text to `H27` | Dialog clouds combo | Partial (text labels, not numeric code) |
| `Stability` | coded enum 1..3 | NA/TT write selected stability text to `P27` | Dialog stability combo | Partial (text labels, not numeric code) |
| `Comments` | free text | NA/TT write `other_conditions` to `X27`; plus camera/telescope comments in `D42/D43` | Dialog `Other Conditions` + equipment data | Partial |

---

## Verified equivalence and gap summary

### Explicitly present in current flows
- Observation outcome selection (Positive/Negative/Unsure).
- Tangra start/end observing times.
- AOTA D/R timing components and uncertainties.
- SNR (if present in AOTA Report data).
- Basic observer/equipment/location fields (with NA/TT-specific layouts).

### Explicitly not present in current report interface (reviewed dialog)
- SODIS report format option.
- Dedicated fields for `Observer2`, `moreObs`, `Countrycode`, `Wind`, `Temperature`.
- Direct SODIS enum-code entry for `Timesource`, `ObservingMethod`, `Transparency`, `Stability`, `Telescope`.

### Format mismatches (explicit)
- SODIS coordinates are shown as signed DMS text in samples/template comments.
- Current NA/TT writes use decimal-degree value + separate hemisphere cells.

---

## Ambiguities / constraints
- This comparison is limited to reviewed files listed at top.
- No claim is made here about additional hidden/reporting paths outside those files.
- Where a field is marked `Not mapped`, it means no explicit write was found in the reviewed NA/TT Openize generator code and report dialog flow.
