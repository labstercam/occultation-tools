# Camera Acquisition Delay Estimation Process

This document defines a repeatable process for estimating camera acquisition delay and documenting uncertainty.

## Purpose

Acquisition delay is the timing offset between the true event time and the timestamp embedded or inferred from camera data products. This delay must be estimated and recorded for high-quality occultation timing.

## Inputs

- Tangra CSV output from calibration or event recordings
- exposure setting metadata (camera and software)
- optional GPS LED line-delay calibration results
- NTP quality summary for the same time window

## Recommended Process

1. Prepare timing environment
- Confirm Meinberg NTP is synchronized and stable.
- Record NTP summary for the upcoming session.

2. Acquire calibration data
- Capture a dedicated run with visible GPS timing flashes.
- Prefer multiple runs rather than one long run when checking repeatability.

3. Analyze light curve timing
- Parse Tangra CSV with `read_tangra_csv`.
- Run timestamp analysis and GPS flash offset analysis.
- Extract or compute acquisition-delay estimate per run.

4. Correct for rolling shutter effects
- If available, apply line-delay correction from LED calibration.
- Track aperture Y-position assumptions used in correction.

5. Estimate final delay and uncertainty
- Combine runs and compute robust center (median preferred).
- Report spread (for example MAD or standard deviation).
- Record final value as `acquisition_delay_ms +/- uncertainty_ms`.

## Minimum Reporting Fields

For each camera profile, capture:
- `camera_model`
- `capture_software_version`
- `video_format`
- `exposure_ms`
- `estimated_acquisition_delay_ms`
- `uncertainty_ms`
- `sample_count`
- `analysis_date_utc`
- `ntp_quality_summary`
- `notes`

## Repeatability Guidance

- Perform at least 3 independent calibration runs.
- Compare run-to-run variation before accepting a final value.
- Re-estimate whenever firmware, driver, or capture settings change.

## Acceptance Criteria (Example)

- NTP monitoring indicates stable offsets during calibration window.
- Delay estimates across runs agree within predefined tolerance.
- No unresolved dropped-frame or timestamp anomalies.

## Integration Notes

- `gps-timing-analysis/python/light_curves.py` supports CSV-based GPS flash analysis.
- `occultation-manager/python/light_curves_iron.py` can consume timing values for report generation.

## Related Documents

- `gps-timing-analysis/docs/ntp-meinberg-setup.md`
- `gps-timing-analysis/docs/ntp-offset-monitoring.md`
- `gps-timing-analysis/ReadMe.md`
