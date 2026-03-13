# Automated NTP + PPS Setup (Windows)

This guide describes automation options for NTP timing setup in this project.

Recommended entrypoint for most users:
- `install_ntp_timing_bootstrap.cmd`

Official GitHub-first run command (PowerShell, recommended when you want the latest code from GitHub every time):

```powershell
[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; $u="https://raw.githubusercontent.com/labstercam/occultation-tools/main/gps-timing-analysis/install_ntp_timing_bootstrap.ps1"; $p=Join-Path $env:TEMP "install_ntp_timing_bootstrap.ps1"; Invoke-WebRequest -UseBasicParsing -Uri $u -OutFile $p; powershell.exe -NoProfile -ExecutionPolicy Bypass -File $p
```

This command downloads the latest bootstrap from GitHub and then runs it.

Equivalent two-step PowerShell command sequence (easier to troubleshoot):

```powershell
$bootstrap = Join-Path $env:TEMP 'install_ntp_timing_bootstrap.ps1'
Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/labstercam/occultation-tools/main/gps-timing-analysis/install_ntp_timing_bootstrap.ps1' -OutFile $bootstrap
powershell.exe -NoProfile -ExecutionPolicy Bypass -File $bootstrap
```

Beginner one-file option (recommended):
- Download `install_ntp_timing_bootstrap.cmd`
- Double-click it
- Accept the UAC prompt
- Follow the guided installer prompts

If your Windows policy blocks `.cmd` launchers or they flash-close before showing a prompt, use the PowerShell bootstrap instead:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install_ntp_timing_bootstrap.ps1
```

Important:
- Do not run `& $bootstrap` directly in a session with restrictive execution policy.
- Run with `powershell.exe -ExecutionPolicy Bypass -File ...` as shown above.

The bootstrap launcher creates/updates a fixed install location at:
- `C:\OccultationTools\gps-timing-analysis`
and then starts the guided installer automatically.

The guided installer walks through optional steps with `Install / Skip / Exit` choices and logs all actions.

## Guided installer (recommended)

Preferred for low-skill users (no unzip/path setup needed):

```cmd
install_ntp_timing_bootstrap.cmd
```

Advanced/manual entrypoint:

Run as Administrator:

```powershell
Set-Location C:\Users\AstroPC\Git\occultation-tools\gps-timing-analysis
.\scripts\install_ntp_timing_guided.ps1
```

If PowerShell windows flash open/close on your system, use the CMD launcher:

```cmd
scripts\install_ntp_timing_guided.cmd
```

The CMD launcher will prompt for Administrator rights automatically (UAC).

What the guided installer covers:
- launch page explaining the workflow and optional/manual install path
- optional Meinberg NTP install and logging setup
- optional NTP Time Server Monitor install
- optional GPS/PPS setup using built-in COM auto-detection (or manual COM entry)
- GPS reminder note for hardware-specific tuning/testing
- country-based NTP server setup using built-in guided-installer logic
- country install summary, including national UTC metadata warnings for non-curated `Other` countries
- prompts to restart NTP service when configuration changes are detected
- if the installer exits early after making changes, warns and prompts for restart before exit
- full transcript logging to `gps-timing-analysis/logs/`

## Advanced script (legacy/testing)

`scripts/setup_ntp_timing.ps1` is retained for legacy/testing workflows.
For normal installs, use `scripts/install_ntp_timing_guided.ps1`.

## What the guided installer can automate

- optional download and install of Meinberg NTP
- optional download and install of NTP server monitor
- detect the appropriate Program Files install root for `PROGRAMDIR\NTP`
- prompt for region (`NZ`, `AU`, `US`, `Other`) when not provided
- set `PPSProviders` registry value for `loopback-ppsapi-provider.dll`
- generate and deploy `ntp.conf` from a template and country server list
- set ACL permissions so standard users can run batch scripts and edit config/log files
- restart NTP service and run validation checks
- verify downloaded Meinberg NTP installer using SHA256

For `AU`, interactive setup now prompts for:
- whether to include National Standards (NMI) servers,
- auto-add of `ntp.nmi.gov.au` when NMI is selected,
- up to 0-2 additional NMI servers,
- up to 0-2 university `.edu.au` servers,
- automatic fill from numbered `0..3.au.pool.ntp.org` servers to reach 5 total,
- static-IP guidance (including detected local IPv4/gateway/DNS suggestions) when NMI is selected.

## Upstream download sources

- Meinberg NTP stable page:
  - `https://www.meinbergglobal.com/english/sw/ntp.htm#ntp_stable`
- NTP installer URL (current pinned default in script):
  - `https://www.meinbergglobal.com/download/ntp/windows/ntp-4.2.8p18a2-win32-setup.exe`
- NTP installer SHA256 source:
  - `https://www.meinbergglobal.com/download/ntp/windows/ntp-4.2.8p18a2-win32-setup.exe.sha256sum`
- Pinned SHA256 value:
  - `f933bc66ed987eb436f8345f6331de4ffad24e6ce5e5a6f5ce98109b7b29f164`
- NTP Time Server Monitor page:
  - `https://www.meinbergglobal.com/english/sw/ntp-server-monitor.htm`
- NTP Time Server Monitor URL (current pinned default in script):
  - `https://www.meinbergglobal.com/download/ntp/windows/time-server-monitor/ntp-time-server-monitor-104.exe`

## What still requires operator checks

- verify GPS receiver COM port and keep GPS mode at recommended default unless advised otherwise
- confirm PPS lock and `o` marker in NTP Time Server Monitor
- review validation output from the script:
  - config path presence check (`ntp.conf`)
  - service status check (`NTP`)
  - optional advanced checks: peer table (`ntpq -pn`) and runtime variables (`ntpq -c rv`)
- verify leap-second convergence and warm-up timing
- verify installer silent switches for your specific installer versions

## Files used

- Guided installer: `gps-timing-analysis/scripts/install_ntp_timing_guided.ps1`
- Legacy/testing script: `gps-timing-analysis/scripts/setup_ntp_timing.ps1`
- Country servers: `gps-timing-analysis/config/ntp-country-servers.json`
- NTP Pool zones resource: `gps-timing-analysis/resources/ntp_pool_zones.json`
- National UTC/NTP inventory resource: `gps-timing-analysis/resources/national_utc_ntp_servers.json`
- Country requirements: `gps-timing-analysis/docs/ntp-country-server-requirements.md`
- Template: `gps-timing-analysis/config/ntp.conf.template`
- Existing NZ reference: `gps-timing-analysis/config/NTP Server Config for NZ.txt`

Resource notes:
- `ntp-country-servers.json` drives generated `ntp.conf` server lines in the guided installer.
- `ntp.conf` updates are marker-based for managed sections:
  - `# >>> NTP_GUIDED_MANAGED_SERVERS_START` ... `# <<< NTP_GUIDED_MANAGED_SERVERS_END`
  - `# >>> NTP_GUIDED_MANAGED_LOGGING_START` ... `# <<< NTP_GUIDED_MANAGED_LOGGING_END`
  The guided installer updates these managed server/logging blocks while preserving other existing `ntp.conf` settings.
- `ntp_pool_zones.json` is used for `-Country Other` 2-letter country-code/region mapping.
- `national_utc_ntp_servers.json` is consulted for `-Country Other` when the country code is not defined in `ntp-country-servers.json`.
  The script displays authority/status/source/note fields, offers up to two national servers, then adds NTP Pool country servers and conditionally regional pool fallback.
- By default, the script tries to load these JSON resources from GitHub raw URLs first, and automatically falls back to local files if remote loading fails.

## Typical run

Guided installer (recommended):

```powershell
Set-Location C:\Users\AstroPC\Git\occultation-tools\gps-timing-analysis
.\scripts\install_ntp_timing_guided.ps1
```

Direct setup script (legacy/testing):

Open PowerShell as Administrator, then run:

```powershell
Set-Location C:\Users\AstroPC\Git\occultation-tools\gps-timing-analysis

# First identify the GPS/PPS COM port interactively.
$com = .\scripts\find_gps_com_port.ps1

.\scripts\setup_ntp_timing.ps1 \
  -Country NZ \
  -ComPort $com \
  -GpsMode 18 \
  -MeinbergInstallerSilentArgs "<SILENT_ARGS>" \
  -NtpMonitorInstallerSilentArgs "<SILENT_ARGS>"
```

## Dry run (legacy/testing script)

Use `-WhatIf` first to preview all changes:

```powershell
.\scripts\setup_ntp_timing.ps1 -Country NZ -ComPort 1 -WhatIf
```

## Region prompt behavior

- If `-Country` is omitted and `-NonInteractive` is not set, the script prompts for region.
- If `-Country` is provided, that value is used directly.
- Use `-NonInteractive` to disable all prompts and use config defaults.
- If `-Country Other` is selected:
  - interactive mode prompts for a 2-letter country code (for example `fr`, `de`, `jp`),
  - non-interactive mode requires `-OtherCountryCode`.

After country selection, the script also performs a best-effort NTP Pool zone check for the selected country code:
- resolves `0..3.<cc>.pool.ntp.org` hostnames,
- queries `https://www.ntppool.org/zone/<cc>` and attempts to parse IPv4/IPv6 active server counts,
- prints warnings when DNS resolution or zone-page parsing cannot be completed.

## Other country server generation

For `-Country Other`, the script generates:
- 3 country-zone pool servers:
  - `0.<cc>.pool.ntp.org`
  - `1.<cc>.pool.ntp.org`
  - `2.<cc>.pool.ntp.org`
- 2 continental-region pool servers (when region mapping is known):
  - `0.<region>.pool.ntp.org`
  - `1.<region>.pool.ntp.org`

If the country code cannot be mapped to a known region, the script falls back to:
- `0.pool.ntp.org`
- `1.pool.ntp.org`

## Install folder logic

When `-NtpInstallRoot` is not provided, the script selects `PROGRAMDIR\NTP` based on system paths in this order:
- `%ProgramFiles(x86)%\NTP` (if available)
- `%ProgramFiles%\NTP`

If one of those folders already exists, it is preferred.

You can force a specific Program Files path with:

```powershell
.\scripts\setup_ntp_timing.ps1 -Country NZ -ComPort 1 -NtpInstallRoot "C:\Program Files (x86)\NTP"
```

The script validates that `-NtpInstallRoot` is under Program Files.

## Permission updates applied

Unless `-SkipPermissions` is provided, the script applies:
- `Users:(RX)` to `bin\*.bat` so start/stop/restart batch scripts can run
- `Users:(M)` to `etc\ntp.conf` so it can be edited/deleted
- `Users:(OI)(CI)M` to `etc\` so logs and supporting files can be created/updated
- `Users:(OI)(CI)M` to `statsdir` path from config/template

## Safety behavior

- Requires Administrator privileges.
- Backs up existing `ntp.conf` before applying managed section updates.
- Writes generated config as ASCII.
- Supports skip switches for incremental use:
  - `-SkipInstall`
  - `-SkipRegistry`
  - `-SkipServiceRestart`
  - `-SkipPermissions`

## Important note on registry type

The script writes `PPSProviders` as `REG_MULTI_SZ` to match command-line guidance in your source workflow. If your validated setup requires another type for your Meinberg build, adjust `Set-PpsRegistryProvider` in the script.

## GPS/PPS restart and reboot guidance

When GPS PPS is enabled and `PPSProviders` is set, a full Windows reboot is usually **not** required.

Recommended sequence:
- restart the `NTP` service to apply provider changes,
- verify operation in NTP Time Server Monitor and with `ntpq` checks,
- only reboot Windows if the service fails to stabilize, the PPS provider does not load, or the system indicates a pending reboot state.

In the guided installer, restart is prompted when configuration changes are detected (including early-exit cases after changes).

## Integrity note

- Meinberg NTP installer hash is verified automatically by default.
- If Meinberg updates the installer, update either:
  - `-MeinbergInstallerSha256` directly, or
  - `-MeinbergInstallerSha256Url` to a current checksum file.
- NTP Time Server Monitor currently has no checksum URL configured in this project, so source validation remains a manual check.

## Next hardening steps

- Pin installer checksums and verify after download.
- Add more country profiles to `ntp-country-servers.json`.
- Add CI lint checks for script syntax and template placeholders.
