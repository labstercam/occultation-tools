# NTP and Camera Timing End-to-End Workflow

This short workflow links Meinberg NTP setup, offset monitoring, and camera acquisition delay estimation.

## End-to-End Steps

1. Configure and validate Meinberg NTP
- Follow `gps-timing-analysis/docs/ntp-meinberg-setup.md`.

2. Warm up and monitor offsets
- Collect baseline loopstats and peerstats.
- Check stability thresholds before calibration.

3. Capture camera timing calibration data
- Record GPS flash light curves (and LED line-delay run if needed).

4. Analyze timing data
- Run NTP offset analysis for the same session window.
- Run Tangra/flash analysis and estimate acquisition delay.

5. Publish timing profile
- Store camera delay estimate with uncertainty and NTP summary.
- Save configuration, data files, and analysis scripts used.

## Deliverables Per Camera/Setup

- camera timing profile (delay plus uncertainty)
- NTP offset summary for calibration window
- calibration artifacts (CSV, plots, scripts/notebooks)
- notes on software versions and settings

## Related Documents

- `gps-timing-analysis/docs/ntp-meinberg-setup.md`
- `gps-timing-analysis/docs/ntp-offset-monitoring.md`
- `gps-timing-analysis/docs/camera-acquisition-delay-estimation.md`
