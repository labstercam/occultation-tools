# NTP Offset Monitoring and Analysis

Use this guide to continuously monitor NTP quality and analyze offset behavior before and during camera timing work.

## Objectives

- verify that host clock offsets are small and stable,
- detect drift episodes before camera calibration,
- summarize offset quality in timing reports.

## Data Sources

Primary sources from Meinberg NTP logging:
- `loopstats` for local loop offset/frequency/jitter trends,
- `peerstats` for per-peer offset and delay behavior.

## Recommended Monitoring Process

1. Start Meinberg NTP and allow warm-up.
2. Collect at least 30 to 60 minutes of loopstats before critical runs.
3. Continue logging throughout acquisition and analysis sessions.
4. Annotate significant events (network changes, GPS lock changes, restarts).

## Suggested Quality Thresholds

Tune for your environment, but use explicit thresholds:
- median absolute offset <= 2.0 ms (target),
- short excursions above 5.0 ms should be rare and explained,
- jitter trend should not show sustained growth.

If thresholds are exceeded, flag data as timing-risk and repeat when stable.

## Analysis with Existing Python Tools

Use existing helper code:
- `gps-timing-analysis/python/ntp_analysis.py`
- `gps-timing-analysis/examples/process loopstats.ipynb`

Typical workflow:
1. Parse loopstats into timestamped data.
2. Plot offset versus time and inspect excursions.
3. Resample to regular intervals for summary reporting.
4. Export session statistics (median, percentiles, max absolute offset).

Example metrics table for reports:
- `session_start_utc`
- `session_end_utc`
- `median_offset_ms`
- `p95_abs_offset_ms`
- `max_abs_offset_ms`
- `median_jitter_ms`
- `notes`

## Event Correlation

When possible, align NTP monitoring windows with:
- camera calibration start/stop times,
- Tangra extraction times,
- GPS LED line-delay runs.

This allows post-hoc confidence scoring per camera dataset.

## Escalation Rules

Define clear stop/go rules:
- proceed if offsets are stable and under threshold,
- pause and investigate if repeated spikes occur,
- restart NTP service only when necessary, then repeat warm-up.

## Related Documents

- `gps-timing-analysis/docs/ntp-meinberg-setup.md`
- `gps-timing-analysis/docs/camera-acquisition-delay-estimation.md`
