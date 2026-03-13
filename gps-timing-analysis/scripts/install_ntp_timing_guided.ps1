[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-WarnMsg([string]$Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Ok([string]$Message) { Write-Host "[ OK ] $Message" -ForegroundColor Green }
function Write-Step([string]$Message) { Write-Host "`n=== $Message ===" -ForegroundColor Green }

function Read-YesNo {
    param(
        [string]$Prompt,
        [bool]$DefaultYes = $true
    )

    while ($true) {
        $suffix = if ($DefaultYes) { "[Y/n]" } else { "[y/N]" }
        $reply = Read-Host "$Prompt $suffix"
        if ([string]::IsNullOrWhiteSpace($reply)) {
            return $DefaultYes
        }

        switch -Regex ($reply.Trim()) {
            '^(y|yes)$' { return $true }
            '^(n|no)$' { return $false }
            default { Write-WarnMsg "Please answer y or n." }
        }
    }
}

function Read-StepAction {
    param([string]$Title)

    while ($true) {
        $choice = Read-Host "Action for '$Title': [I]nstall / [S]kip / E[x]it"
        if ([string]::IsNullOrWhiteSpace($choice)) {
            return "Install"
        }

        switch -Regex ($choice.Trim().ToLowerInvariant()) {
            '^(i|install)$' { return "Install" }
            '^(s|skip)$' { return "Skip" }
            '^(x|e|exit|quit)$' { return "Exit" }
            default { Write-WarnMsg "Enter I, S, or X." }
        }
    }
}

function Confirm-Step {
    param(
        [string]$Title,
        [string[]]$Details
    )

    Write-Step $Title
    foreach ($line in $Details) {
        Write-Host (" - {0}" -f $line)
    }

    $action = Read-StepAction -Title $Title
    if ($action -eq "Exit") {
        throw "Installer exited by user at step: $Title"
    }

    if ($action -eq "Skip") {
        Write-WarnMsg "Step skipped: $Title"
        return $false
    }

    return $true
}

function Assert-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($id)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "This installer needs Administrator rights. Close this window, then right-click PowerShell and select 'Run as administrator', and run the installer again."
    }
}

function Resolve-DefaultInstallRoot {
    $pf86 = ${env:ProgramFiles(x86)}
    $pf64 = $env:ProgramFiles

    $candidates = @()
    if (-not [string]::IsNullOrWhiteSpace($pf86)) { $candidates += (Join-Path $pf86 "NTP") }
    if (-not [string]::IsNullOrWhiteSpace($pf64)) { $candidates += (Join-Path $pf64 "NTP") }

    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) {
            return (Resolve-Path -LiteralPath $c).Path
        }
    }

    if ($candidates.Count -gt 0) {
        return $candidates[0]
    }

    throw "Could not determine Program Files directory on this system."
}

function Convert-ToTextFromResponseContent {
    param([object]$Content)

    if ($Content -is [string]) {
        return $Content
    }

    if ($Content -is [System.Array]) {
        return (($Content | ForEach-Object { [char]$_ }) -join '')
    }

    return [string]$Content
}

function Get-ExpectedSha256FromUrl {
    param([string]$ShaUrl)

    if ([string]::IsNullOrWhiteSpace($ShaUrl)) {
        return ""
    }

    $resp = Invoke-WebRequest -Uri $ShaUrl -UseBasicParsing
    $text = Convert-ToTextFromResponseContent -Content $resp.Content
    $line = ($text -split "`n" | Select-Object -First 1).Trim()
    if ($line -match '^(?<hash>[A-Fa-f0-9]{64})\s+\*?.+$') {
        return $matches['hash'].ToLowerInvariant()
    }

    throw "Could not parse SHA256 checksum from $ShaUrl"
}

function Assert-FileSha256 {
    param(
        [string]$Path,
        [string]$ExpectedSha256,
        [string]$Label
    )

    if ([string]::IsNullOrWhiteSpace($ExpectedSha256)) {
        Write-WarnMsg "No expected SHA256 provided for $Label. Skipping checksum validation."
        return
    }

    $actual = (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
    $expected = $ExpectedSha256.ToLowerInvariant()

    if ($actual -ne $expected) {
        throw "$Label checksum mismatch. Expected $expected but got $actual"
    }

    Write-Ok "$Label checksum validated (SHA256)"
}

function Invoke-InstallerDownload {
    param(
        [string]$Url,
        [string]$OutputPath,
        [string]$Label
    )

    if ([string]::IsNullOrWhiteSpace($Url)) {
        throw "$Label URL is empty."
    }

    Write-Info "Downloading $Label from $Url"
    Invoke-WebRequest -Uri $Url -OutFile $OutputPath -UseBasicParsing
    Write-Ok "Downloaded $Label to $OutputPath"
}

function Install-Exe {
    param(
        [string]$InstallerPath,
        [string]$Arguments,
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $InstallerPath)) {
        throw "$Label installer not found: $InstallerPath"
    }

    if ([string]::IsNullOrWhiteSpace($Arguments)) {
        Write-WarnMsg "$Label silent arguments are empty; installer may be interactive."
    }

    Write-Info "Starting installer: $Label"
    $proc = Start-Process -FilePath $InstallerPath -ArgumentList $Arguments -PassThru -Wait
    if ($proc.ExitCode -ne 0) {
        throw "$Label installer exited with code $($proc.ExitCode)"
    }

    Write-Ok "$Label installation completed"
}

function Set-LoggingConfig {
    param(
        [string]$NtpConfPath,
        [string]$StatsDir
    )

    if (-not (Test-Path -LiteralPath (Split-Path -Parent $NtpConfPath))) {
        New-Item -ItemType Directory -Path (Split-Path -Parent $NtpConfPath) -Force | Out-Null
    }

    if (-not (Test-Path -LiteralPath $StatsDir)) {
        New-Item -ItemType Directory -Path $StatsDir -Force | Out-Null
    }

    $content = ""
    if (Test-Path -LiteralPath $NtpConfPath) {
        $content = Get-Content -Raw -LiteralPath $NtpConfPath
    }

    if ([string]::IsNullOrWhiteSpace($content)) {
        $content = @(
            "# Placeholder ntp.conf created by guided installer.",
            "# Server selection is configured in the country setup step.",
            ""
        ) -join [Environment]::NewLine
    }

    $required = @(
        "enable stats",
        "statsdir `"$StatsDir`"",
        "statistics loopstats",
        "statistics peerstats"
    )

    foreach ($line in $required) {
        if ($content -notmatch [regex]::Escape($line)) {
            $content += [Environment]::NewLine + $line
        }
    }

    Set-Content -LiteralPath $NtpConfPath -Value $content -Encoding ASCII
    Write-Ok "Logging directives prepared in $NtpConfPath"
}

function Read-CountrySelection {
    while ($true) {
        Write-Host "Select country profile for NTP servers:" -ForegroundColor Cyan
        Write-Host "  1) NZ"
        Write-Host "  2) AU"
        Write-Host "  3) US"
        Write-Host "  4) Other (enter 2-letter country code, for example FR, DE, JP)"

        $choice = Read-Host "Enter 1-4"
        if ($choice -eq "1") { return @{ Country = "NZ"; OtherCode = "" } }
        if ($choice -eq "2") { return @{ Country = "AU"; OtherCode = "" } }
        if ($choice -eq "3") { return @{ Country = "US"; OtherCode = "" } }
        if ($choice -eq "4") {
            $raw = Read-Host "Enter 2-letter country code (e.g. fr, de, jp)"
            if (-not [string]::IsNullOrWhiteSpace($raw)) {
                $cc = $raw.Trim().ToLowerInvariant()
                if ($cc -match '^[a-z]{2}$') {
                    return @{ Country = "Other"; OtherCode = $cc }
                }
            }
            Write-WarnMsg "Please enter exactly two letters for the country code."
            continue
        }

        Write-WarnMsg "Invalid selection."
    }
}

function Read-GpsModeInteractive {
    param([int]$CurrentMode = 18)

    Write-Info "GPS mode controls how serial GPS data is interpreted."
    if (Read-YesNo -Prompt "Use recommended GPS mode (18)?" -DefaultYes $true) {
        return 18
    }

    Write-Host "Advanced mode values: 2, 18, 34, 50, 66, 82" -ForegroundColor Yellow
    Write-Host "If unsure, use 18." -ForegroundColor Yellow

    while ($true) {
        $modeRaw = Read-Host "Enter GPS mode value"
        if ($modeRaw -match '^(2|18|34|50|66|82)$') {
            return [int]$modeRaw
        }

        Write-WarnMsg "Unsupported GPS mode. Allowed values: 2, 18, 34, 50, 66, 82."
    }
}

function Show-CountryInstallSummary {
    param(
        [string]$Country,
        [string]$OtherCode,
        [string]$CountryConfigPath,
        [string]$NationalUtcPath
    )

    if (-not (Test-Path -LiteralPath $CountryConfigPath)) {
        Write-WarnMsg "Country config file not found: $CountryConfigPath"
        return
    }

    $countryConfig = Get-Content -Raw -LiteralPath $CountryConfigPath | ConvertFrom-Json

    if ($Country -ne "Other") {
        Write-Ok "Country profile '$Country' is curated in ntp-country-servers.json and expected to work well."
        return
    }

    $cc = $OtherCode.ToUpperInvariant()
    $prop = @($countryConfig.PSObject.Properties | Where-Object { $_.Name -ieq $cc } | Select-Object -First 1)
    if ($prop.Count -gt 0) {
        Write-Ok "Country profile '$cc' is curated in ntp-country-servers.json and expected to work well."
        return
    }

    Write-WarnMsg "Country '$cc' is not curated in ntp-country-servers.json. Pool-based servers should generally work."
    Write-Info "Country pool is usually preferred over region pool where available."

    if (-not (Test-Path -LiteralPath $NationalUtcPath)) {
        Write-WarnMsg "National UTC inventory file not found: $NationalUtcPath"
        return
    }

    $national = Get-Content -Raw -LiteralPath $NationalUtcPath | ConvertFrom-Json
    $entry = @($national.entries | Where-Object { $_.country_code -ieq $cc } | Select-Object -First 1)
    if ($entry.Count -eq 0) {
        Write-WarnMsg "No national UTC/NTP metadata found for '$cc'."
        return
    }

    $item = $entry[0]
    Write-WarnMsg "National standards servers have not been fully tested by this installer."
    Write-WarnMsg "These servers may be inaccessible, restricted, or require registration with the authority."
    Write-Host ("Country     : {0}" -f $item.country_name)
    Write-Host ("Status      : {0}" -f $item.status)
    Write-Host ("Authority   : {0}" -f $item.authority)
    if (-not [string]::IsNullOrWhiteSpace([string]$item.usage_note)) {
        Write-Host ("Usage Note  : {0}" -f $item.usage_note)
    }

    $urls = @($item.source_urls)
    if ($urls.Count -gt 0) {
        Write-Host "Authority / Source URL(s):"
        foreach ($u in $urls) {
            Write-Host (" - {0}" -f $u)
        }
    }
}

function Remove-GpsClockLines {
    param([string[]]$Lines)

    $cleaned = @()
    foreach ($line in @($Lines)) {
        if ($line -match '^\s*#\s*GPS serial source configured by install_ntp_timing_guided\.ps1\s*$') { continue }
        if ($line -match '^\s*#?\s*server\s+127\.127\.20\.') { continue }
        if ($line -match '^\s*#?\s*fudge\s+127\.127\.20\.') { continue }
        $cleaned += $line
    }

    return @($cleaned)
}

function Update-GpsLines {
    param(
        [string]$NtpConfPath,
        [int]$ComPort,
        [int]$GpsMode,
        [bool]$NmeaOnly
    )

    if (-not (Test-Path -LiteralPath $NtpConfPath)) {
        throw "ntp.conf not found at $NtpConfPath. Complete the NTP setup step first."
    }

    $lines = @(Get-Content -LiteralPath $NtpConfPath)
    $filtered = Remove-GpsClockLines -Lines $lines

    $gpsBlock = @(
        "",
        "# GPS serial source configured by install_ntp_timing_guided.ps1"
    )

    if ($NmeaOnly) {
        $gpsBlock += "server 127.127.20.$ComPort mode $GpsMode minpoll 4 maxpoll 4 iburst"
        $gpsBlock += "fudge 127.127.20.$ComPort flag1 0 flag2 0 refid GPS"
    }
    else {
        $gpsBlock += "server 127.127.20.$ComPort mode $GpsMode minpoll 4 maxpoll 4 prefer"
        $gpsBlock += "fudge 127.127.20.$ComPort flag1 1 flag2 1 refid GPS"
    }

    $updated = @($filtered + $gpsBlock)
    Set-Content -LiteralPath $NtpConfPath -Value $updated -Encoding ASCII

    if ($NmeaOnly) {
        Write-Ok "Configured NMEA-only GPS lines for COM$ComPort in $NtpConfPath"
    }
    else {
        Write-Ok "Configured PPS+NMEA GPS lines for COM$ComPort in $NtpConfPath"
    }
}

function Disable-GpsLines {
    param([string]$NtpConfPath)

    if (-not (Test-Path -LiteralPath $NtpConfPath)) {
        return
    }

    $lines = @(Get-Content -LiteralPath $NtpConfPath)
    $updated = Remove-GpsClockLines -Lines $lines

    Set-Content -LiteralPath $NtpConfPath -Value $updated -Encoding ASCII
    Write-Info "GPS local-clock lines were removed because GPS was not selected in this run."
}

function Set-PpsProviderRegistryValue {
    param([string]$DllPath)

    $regPath = "HKLM:\SYSTEM\CurrentControlSet\Services\NTP"
    if (-not (Test-Path -LiteralPath $regPath)) {
        Write-WarnMsg "Registry path not found: $regPath"
        Write-WarnMsg "Install Meinberg NTP before enabling PPS provider."
        return $false
    }

    if (-not (Test-Path -LiteralPath $DllPath)) {
        Write-WarnMsg "PPS provider DLL not found: $DllPath"
        Write-WarnMsg "Install Meinberg NTP (or provide DLL path) before enabling PPS provider."
        return $false
    }

    New-ItemProperty -Path $regPath -Name "PPSProviders" -PropertyType MultiString -Value $DllPath -Force | Out-Null
    Write-Ok ("Set registry PPSProviders = {0}" -f $DllPath)
    return $true
}

function Try-RestartNtpService {
    try {
        $svc = Get-Service -Name "NTP" -ErrorAction Stop
    }
    catch {
        Write-WarnMsg "NTP service is not installed or not registered. Restart skipped."
        return $false
    }

    try {
        Write-Info "Restarting NTP service..."
        Restart-Service -Name "NTP" -ErrorAction Stop
        Start-Sleep -Seconds 2
        $svc = Get-Service -Name "NTP" -ErrorAction Stop
        if ($svc.Status -ne "Running") {
            Write-WarnMsg ("NTP service status after restart: {0}" -f $svc.Status)
            return $false
        }

        Write-Ok "NTP service restarted successfully."
        return $true
    }
    catch {
        Write-WarnMsg ("NTP service restart failed: {0}" -f $_.Exception.Message)
        return $false
    }
}

function Prompt-RestartIfNeeded {
    param([bool]$RestartNeeded)

    if (-not $RestartNeeded) {
        return $false
    }

    Write-WarnMsg "NTP configuration changed in this run."
    $doRestart = Read-YesNo -Prompt "Restart NTP service now to apply changes?" -DefaultYes $true
    if (-not $doRestart) {
        Write-WarnMsg "Please restart the NTP service manually before relying on this configuration."
        return $false
    }

    return (Try-RestartNtpService)
}

$scriptRoot = Split-Path -Parent $PSCommandPath
$projectRoot = Split-Path -Parent $scriptRoot
$setupScript = Join-Path $scriptRoot "setup_ntp_timing.ps1"
$findComScript = Join-Path $scriptRoot "find_gps_com_port.ps1"

$countryConfigPath = Join-Path $projectRoot "config\ntp-country-servers.json"
$nationalUtcPath = Join-Path $projectRoot "resources\national_utc_ntp_servers.json"

$meinbergInstallerUrl = "https://www.meinbergglobal.com/download/ntp/windows/ntp-4.2.8p18a2-win32-setup.exe"
$meinbergInstallerSha256 = "f933bc66ed987eb436f8345f6331de4ffad24e6ce5e5a6f5ce98109b7b29f164"
$meinbergInstallerSha256Url = "https://www.meinbergglobal.com/download/ntp/windows/ntp-4.2.8p18a2-win32-setup.exe.sha256sum"
$meinbergInstallerArgs = ""

$ntpMonitorInstallerUrl = "https://www.meinbergglobal.com/download/ntp/windows/time-server-monitor/ntp-time-server-monitor-104.exe"
$ntpMonitorInstallerArgs = ""

$installRoot = Resolve-DefaultInstallRoot
$statsDir = Join-Path $installRoot "etc\"
$ntpConfPath = Join-Path $installRoot "etc\ntp.conf"
$ppsRegistryPath = "HKLM:\SYSTEM\CurrentControlSet\Services\NTP"
$ppsDllPath = Join-Path $installRoot "bin\loopback-ppsapi-provider.dll"
$downloadDir = Join-Path $env:TEMP "gps-timing-analysis-installer"

if (-not (Test-Path -LiteralPath $downloadDir)) {
    New-Item -ItemType Directory -Path $downloadDir -Force | Out-Null
}

$logDir = Join-Path $projectRoot "logs"
if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}
$logPath = Join-Path $logDir ("guided_ntp_installer_{0}.log" -f (Get-Date -Format "yyyyMMdd_HHmmss"))

$gpsConfigured = $false
$gpsNmeaOnly = $false
$selectedComPort = 1
$selectedGpsMode = 18
$selectedCountry = "NZ"
$selectedOtherCode = ""
$transcriptStarted = $false
$restartRecommended = $false
$restartCompleted = $false

try {
    Start-Transcript -Path $logPath -Force | Out-Null
    $transcriptStarted = $true
}
catch {
    Write-WarnMsg ("Could not start transcript log at {0}: {1}" -f $logPath, $_.Exception.Message)
    Write-WarnMsg "Continuing without transcript logging for this run."
}

try {
    Assert-Admin

    Write-Step "Welcome"
    Write-Host "This guided installer can perform any or all of the following:" -ForegroundColor Cyan
    Write-Host " 1) Install Meinberg NTP and prepare logging"
    Write-Host " 2) Install NTP Time Server Monitor"
    Write-Host " 3) Configure optional GPS/PPS serial source"
    Write-Host " 4) Configure internet NTP servers by country"
    Write-Host ""
    Write-Host "Estimated time: 10-20 minutes (depends on internet speed and installer prompts)." -ForegroundColor Cyan
    Write-Host "Internet access is needed for optional downloads." -ForegroundColor Cyan
    Write-Host "You can safely skip any step and run this installer again later." -ForegroundColor Cyan
    Write-Host "If Windows shows security/UAC prompts for trusted installers, choose Allow/Yes to continue." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Each step is optional. At every step you can choose: Install, Skip, or Exit." -ForegroundColor Cyan
    Write-Host "You can also do all steps manually and follow project documentation when available." -ForegroundColor Yellow
    Write-Host ("Installer log: {0}" -f $logPath) -ForegroundColor DarkGray

    if (-not (Read-YesNo -Prompt "Proceed with guided installer?" -DefaultYes $true)) {
        throw "Installer canceled by user at launch page."
    }

    if (Confirm-Step -Title "Step 2: Install Meinberg NTP and prepare logging" -Details @(
            "Downloads and installs Meinberg NTP.",
            "NTP internet server selection is done in a later step.",
            ("Installer URL: {0}" -f $meinbergInstallerUrl),
            ("Install root: {0}" -f $installRoot),
            ("Config file: {0}" -f $ntpConfPath),
            ("Log folder: {0}" -f $statsDir),
            ("Advanced (automatic if PPS is enabled): registry value {0}\\PPSProviders" -f $ppsRegistryPath)
        )) {

        $meinbergInstallerPath = Join-Path $downloadDir "meinberg_installer.exe"
        Invoke-InstallerDownload -Url $meinbergInstallerUrl -OutputPath $meinbergInstallerPath -Label "Meinberg NTP"

        $effectiveMeinbergSha = $meinbergInstallerSha256
        if ([string]::IsNullOrWhiteSpace($effectiveMeinbergSha) -and -not [string]::IsNullOrWhiteSpace($meinbergInstallerSha256Url)) {
            $effectiveMeinbergSha = Get-ExpectedSha256FromUrl -ShaUrl $meinbergInstallerSha256Url
        }
        Assert-FileSha256 -Path $meinbergInstallerPath -ExpectedSha256 $effectiveMeinbergSha -Label "Meinberg NTP installer"

        Install-Exe -InstallerPath $meinbergInstallerPath -Arguments $meinbergInstallerArgs -Label "Meinberg NTP"
        Set-LoggingConfig -NtpConfPath $ntpConfPath -StatsDir $statsDir
        $restartRecommended = $true
    }

    if (Confirm-Step -Title "Step 3: Install NTP Time Server Monitor" -Details @(
            "Downloads and installs NTP Time Server Monitor.",
            "Use this tool later to verify lock, offsets, and source selection.",
            ("Installer URL: {0}" -f $ntpMonitorInstallerUrl),
            "No official checksum URL is currently configured in this script."
        )) {

        $monitorInstallerPath = Join-Path $downloadDir "ntp_monitor_installer.exe"
        Invoke-InstallerDownload -Url $ntpMonitorInstallerUrl -OutputPath $monitorInstallerPath -Label "NTP Time Server Monitor"
        Install-Exe -InstallerPath $monitorInstallerPath -Arguments $ntpMonitorInstallerArgs -Label "NTP Time Server Monitor"
    }

    if (Confirm-Step -Title "Step 4: Optional GPS/PPS source setup" -Details @(
            "Optionally detect COM port using find_gps_com_port.ps1.",
            "Can configure either PPS+NMEA (GPS PPS) or NMEA-only receiver mode.",
            "Writes GPS server/fudge lines to ntp.conf.",
            ("COM helper script: {0}" -f $findComScript),
            ("ntp.conf target: {0}" -f $ntpConfPath),
            ("PPS provider DLL path (automatic if PPS mode is selected): {0}" -f $ppsDllPath),
            ("Advanced: registry value set for PPS mode at {0}\\PPSProviders" -f $ppsRegistryPath)
        )) {

        if (-not (Test-Path -LiteralPath $findComScript)) {
            throw "COM helper script not found: $findComScript"
        }

        Write-Host "Select GPS mode:" -ForegroundColor Cyan
        Write-Host "  1) GPS PPS + NMEA (recommended when PPS available)"
        Write-Host "  2) GPS NMEA only (no PPS signal)"

        $gpsChoice = Read-Host "Enter 1 or 2 (default 1)"
        if ($gpsChoice -eq "2") {
            $gpsNmeaOnly = $true
            Write-Info "Selected mode: NMEA only"
        }
        else {
            $gpsNmeaOnly = $false
            Write-Info "Selected mode: PPS + NMEA"
        }

        if (Read-YesNo -Prompt "Run COM port discovery helper now?" -DefaultYes $true) {
            $comOutput = @(& $findComScript)
            $numericLines = @($comOutput | ForEach-Object { [string]$_ } | Where-Object { $_ -match '^\d+$' })
            if ($numericLines.Count -eq 0) {
                throw "COM helper did not return a COM port number."
            }

            $selectedComPort = [int]$numericLines[$numericLines.Count - 1]
            Write-Ok ("Using detected COM port: COM{0}" -f $selectedComPort)
        }
        else {
            while ($true) {
                $manualCom = Read-Host "Enter COM port number (example: 3 for COM3)"
                if ($manualCom -match '^\d+$') {
                    $comValue = [int]$manualCom
                    if ($comValue -ge 1 -and $comValue -le 256) {
                        $selectedComPort = $comValue
                        break
                    }
                }
                Write-WarnMsg "Enter a numeric COM port value between 1 and 256."
            }
        }

        $selectedGpsMode = Read-GpsModeInteractive -CurrentMode $selectedGpsMode

        if (-not (Test-Path -LiteralPath $ntpConfPath)) {
            Write-WarnMsg "ntp.conf not found yet. GPS lines will be applied after step 6 completes."
        }
        else {
            Update-GpsLines -NtpConfPath $ntpConfPath -ComPort $selectedComPort -GpsMode $selectedGpsMode -NmeaOnly:$gpsNmeaOnly
            $restartRecommended = $true
        }

        if (-not $gpsNmeaOnly) {
            Write-Info "PPS mode selected: configuring PPSProviders registry value."
            $ppsConfigured = Set-PpsProviderRegistryValue -DllPath $ppsDllPath
            if (-not $ppsConfigured) {
                Write-WarnMsg "PPSProviders registry value was not set in this run."
            }
            else {
                $restartRecommended = $true
            }
        }

        $gpsConfigured = $true
    }

    if ($gpsConfigured) {
        Write-Step "Step 5: GPS reminder"
        Write-WarnMsg "GPS parameters may still require tuning for your hardware and serial settings."
        Write-Info "Test behavior in NTP Time Server Monitor and refer to project documentation when available."
    }

    if (Confirm-Step -Title "Step 6: Configure internet NTP servers by country" -Details @(
            "Uses existing logic from setup_ntp_timing.ps1.",
            "Country profiles in ntp-country-servers.json are curated.",
            "Other countries use pool logic and may include national UTC inventory data.",
            ("Setup script: {0}" -f $setupScript),
            ("Country config: {0}" -f $countryConfigPath),
            ("National UTC metadata: {0}" -f $nationalUtcPath),
            ("Target config file: {0}" -f $ntpConfPath)
        )) {

        if (-not (Test-Path -LiteralPath $setupScript)) {
            throw "Setup script not found: $setupScript"
        }

        $countryChoice = Read-CountrySelection
        $selectedCountry = [string]$countryChoice.Country
        $selectedOtherCode = [string]$countryChoice.OtherCode

        $setupArgs = @(
            "-Country", $selectedCountry,
            "-ComPort", [string]$selectedComPort,
            "-GpsMode", [string]$selectedGpsMode,
            "-SkipInstall",
            "-SkipRegistry",
            "-SkipServiceRestart"
        )

        if (-not [string]::IsNullOrWhiteSpace($selectedOtherCode)) {
            $setupArgs += @("-OtherCountryCode", $selectedOtherCode)
        }

        Write-Info "Invoking setup_ntp_timing.ps1 for country server configuration..."
        & $setupScript @setupArgs
        $restartRecommended = $true

        if (-not $gpsConfigured) {
            Disable-GpsLines -NtpConfPath $ntpConfPath
            $restartRecommended = $true
        }
        elseif ($gpsNmeaOnly) {
            Update-GpsLines -NtpConfPath $ntpConfPath -ComPort $selectedComPort -GpsMode $selectedGpsMode -NmeaOnly:$true
            $restartRecommended = $true
        }

        Show-CountryInstallSummary -Country $selectedCountry -OtherCode $selectedOtherCode -CountryConfigPath $countryConfigPath -NationalUtcPath $nationalUtcPath
    }

    if ($restartRecommended -and -not $restartCompleted) {
        $restartCompleted = Prompt-RestartIfNeeded -RestartNeeded $restartRecommended
    }

    Write-Step "Completed"
    Write-Ok "Guided installer finished."
    Write-Host "You can run this installer again and complete any skipped steps later." -ForegroundColor Cyan
    Write-Host "You can also install all components manually and use project documentation." -ForegroundColor Cyan
    Write-Host ("Log written to: {0}" -f $logPath) -ForegroundColor Cyan
}
catch {
    if ($_.Exception.Message -like "Installer exited by user at step:*") {
        Write-WarnMsg $_.Exception.Message
        if ($restartRecommended -and -not $restartCompleted) {
            Write-WarnMsg "You exited before final restart check."
            $restartCompleted = Prompt-RestartIfNeeded -RestartNeeded $restartRecommended
        }
        Write-Host ("Log written to: {0}" -f $logPath) -ForegroundColor Cyan
        return
    }

    if ($_.Exception.Message -eq "Installer canceled by user at launch page.") {
        Write-WarnMsg "Installer canceled by user at launch page."
        if ($restartRecommended -and -not $restartCompleted) {
            Write-WarnMsg "Configuration changed earlier in this run; restart may still be required."
            $restartCompleted = Prompt-RestartIfNeeded -RestartNeeded $restartRecommended
        }
        Write-Host ("Log written to: {0}" -f $logPath) -ForegroundColor Cyan
        return
    }

    Write-Host "" 
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "See installer log for full details:" -ForegroundColor Yellow
    Write-Host ("  {0}" -f $logPath) -ForegroundColor Yellow
    throw
}
finally {
    if ($transcriptStarted) {
        try { Stop-Transcript | Out-Null } catch {}
    }
}
