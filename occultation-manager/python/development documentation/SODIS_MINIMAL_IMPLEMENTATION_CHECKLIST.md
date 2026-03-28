# SODIS Minimal Implementation Checklist

This checklist is intentionally minimal and based only on verified gaps in `SODIS_COMPARISON.md`.

## Goal (MVP)
Generate an `IOTA-ES` text report file from existing report workflow with required core fields populated, reusing current NA/TT data sources where possible.

---

## 1) Add SODIS report type to UI
- [x] Add a third report format option in `ComprehensiveReportDialog`:
  - Label: `IOTA-ES / SODIS (Form 2.03)`
  - Internal key: `sodis`
- [x] Ensure selection is returned by `get_report_type()` and accepted in `main_gui.generate_report_click`.

## 2) Add SODIS report generator class
- [x] Create `sodis_report_text.py` with class (example) `SODISReportGeneratorText`.
- [x] Input signature should match current generator call pattern:
  - `generate_report(event, telescope_id, camera_id, observation_type, tangra_data, aota_report_data, aota_xml_used, clouds, stability, other_conditions)`
- [x] Write plain-text output file (not XLSX) with line order matching `IOTA-ES_report.txt`.

## 3) Wire generator selection in main flow
- [x] In `main_gui.generate_report_click`, add branch for `report_type == 'sodis'`.
- [x] Instantiate SODIS generator and call `.generate_report(...)` with existing collected inputs.

## 4) Populate required MVP fields (must-have)
- [x] Header line exactly:
  - `#IOTA-ES ASTEROIDAL OCCULTATION - REPORT FORM 2.03`
- [x] Event core fields:
  - `Occultation`, `DATE`, `PREDICTTIME`, `STAR`, `ASTEROID`, `Nr`
- [x] Observer core fields:
  - `Observer1`, `E-mail`, `Address`
- [x] Station core fields:
  - `NearestCity`, `Countrycode`, `Latitude`, `Longitude`, `Altitude`, `Datum`
- [x] Observation timing fields:
  - `StartObs`, `EndObs`, `D`, `Acc_D`, `R`, `Acc_R`, `Exp_Time`
- [x] Conditions fields:
  - `Transparency`, `Stability`, `Comments`

## 5) Outcome rules (minimal, explicit)
- [x] Positive/Unsure:
  - Write `D` and `R` using available AOTA timing values.
  - Write `Acc_D` / `Acc_R` if uncertainty exists.
- [x] Negative:
  - Write `D: M`
  - Write `R: M`
  - Leave `Acc_D` and `Acc_R` blank.

## 6) Use current sources only (no new dialogs for MVP)
- [x] Use existing `event` object for event/asteroid/star/location data.
- [x] Use existing config for observer details.
- [x] Use existing Tangra summary for `StartObs`, `EndObs`, and exposure-derived value if used for `Exp_Time`.
- [x] Use existing AOTA Report / converted AOTA XML summary for `D/R/Acc`.
- [x] Use existing `clouds`, `stability`, `other_conditions` dialog values.

## 7) Required formatting constraints for MVP
- [x] Preserve SODIS key names exactly (including capitalization and punctuation).
- [x] Keep file line order consistent with template.
- [x] Prefix all lines with `#` as in template.
- [x] Do not invent values when source is missing; leave blank unless a rule above requires a default (e.g., negative D/R = `M`).

## 8) Explicitly defer (out of MVP)
- [x] Full codebook mapping for all SODIS enum fields not currently captured as codes (Timesource, ObservingMethod, Telescope code).
- [x] Strict conversion to signed DMS text if current source is decimal (unless implemented without new UI impact).
- [x] Additional observer fields (`Observer2`, `moreObs`) and weather details (`Wind`, `Temperature`) if not available.

## 9) Validation checklist before merge
- [x] Generate one positive SODIS file and compare line-by-line against `IOTA-ES_report.txt` structure.
- [x] Generate one negative SODIS file and verify `D: M` / `R: M` behavior.
- [x] Confirm no regressions in existing NA/TT report generation paths.
- [x] Confirm output file is created in reports folder and status messaging remains clean.
