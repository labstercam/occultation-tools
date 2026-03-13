# Meinberg NTP Setup for Timing Validation

This guide describes a practical baseline setup for Windows systems using Meinberg NTP when preparing camera timing validation workflows.

## Scope

Use this workflow when you need to:
- synchronize a Windows acquisition PC to stable NTP sources,
- collect NTP timing logs for quality checks,
- feed offset data into `gps-timing-analysis/python/ntp_analysis.py`.

## Prerequisites

- Windows machine used for camera control or analysis
- Meinberg NTP package installed
- Internet access to at least 3 reliable upstream NTP servers
- Administrative permissions to edit NTP config and restart the service

## Install and Verify Meinberg NTP

1. Install Meinberg NTP using default paths unless your organization requires otherwise.
2. Confirm service status in Services (`Network Time Protocol`).
3. Verify command-line tools are available (for example `ntpq`, `ntpdc` if installed).

Recommended download references:
- Stable page: `https://www.meinbergglobal.com/english/sw/ntp.htm#ntp_stable`
- Win32 installer: `https://www.meinbergglobal.com/download/ntp/windows/ntp-4.2.8p18a2-win32-setup.exe`
- SHA256 file: `https://www.meinbergglobal.com/download/ntp/windows/ntp-4.2.8p18a2-win32-setup.exe.sha256sum`

If using the automation script in this repository, these URLs are already preconfigured and the installer SHA256 is validated during download/install.

## Recommended Baseline Configuration

Edit `ntp.conf` and include:
- multiple upstream `server` entries (3 to 5 sources),
- drift file path,
- loopstats and peerstats logging.

Example baseline (adapt to your environment):

```conf
# Upstream servers
server 0.pool.ntp.org iburst
server 1.pool.ntp.org iburst
server 2.pool.ntp.org iburst

# Drift and logging
statsdir "C:\\Program Files (x86)\\NTP\\var\\"
driftfile "C:\\Program Files (x86)\\NTP\\etc\\ntp.drift"

filegen loopstats file loopstats type day enable
filegen peerstats file peerstats type day enable

# Access defaults
restrict default kod nomodify notrap nopeer noquery
restrict 127.0.0.1
restrict ::1
```

Notes:
- Keep at least one low-latency regional server in your source list when possible.
- Use `iburst` on startup to reduce initial convergence time.

## Restart and Warm-Up

1. Restart the `Network Time Protocol` service.
2. Allow warm-up time before trusting offsets (typically 15 to 30 minutes).
3. During warm-up, avoid calibration runs intended for publication-quality timing.

## Quick Health Checks

Run checks after warm-up:
- `ntpq -pn` to verify selected source (`*`) and reachable peers
- `ntpq -c rv` to inspect overall synchronization status

Healthy indicators:
- one selected source with stable low offset,
- jitter and dispersion values stable over time,
- no repeated source flapping.

## Data Capture for Analysis

When running camera timing tests:
1. Keep Meinberg NTP running continuously.
2. Record start and end times of each camera session.
3. Keep loopstats and peerstats files for the full session window.
4. Archive logs alongside Tangra or calibration outputs.

## Related Documents

- `gps-timing-analysis/docs/ntp-offset-monitoring.md`
- `gps-timing-analysis/docs/camera-acquisition-delay-estimation.md`
- `gps-timing-analysis/docs/ntp-country-server-requirements.md`
- `gps-timing-analysis/python/ntp_analysis.py`
