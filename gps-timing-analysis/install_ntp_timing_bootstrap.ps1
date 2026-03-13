[CmdletBinding()]
param(
    [switch]$Elevated,
    [switch]$NoPause
)

$ErrorActionPreference = 'Stop'

function Wait-BeforeCloseIfNeeded {
    if (-not $NoPause) {
        Write-Host ""
        Write-Host "Press Enter to close..."
        [void](Read-Host)
    }
}

function Write-BootstrapLog {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    try {
        if ([string]::IsNullOrWhiteSpace($script:bootstrapLog)) {
            return
        }
        Add-Content -Path $script:bootstrapLog -Value "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message"
    }
    catch {
        # Intentionally ignore logging failures so setup can continue.
    }
}

$repoOwner = 'labstercam'
$repoName = 'occultation-tools'
$repoBranch = 'main'
$subdir = 'gps-timing-analysis'
$systemDrive = $env:SystemDrive
if ([string]::IsNullOrWhiteSpace($systemDrive)) {
    $systemDrive = 'C:'
}

$installRoot = Join-Path $systemDrive 'OccultationTools\gps-timing-analysis'
$baseUrl = "https://raw.githubusercontent.com/$repoOwner/$repoName/$repoBranch/$subdir"

$tempRoot = $env:TEMP
if ([string]::IsNullOrWhiteSpace($tempRoot)) {
    $tempRoot = [System.IO.Path]::GetTempPath()
}
if ([string]::IsNullOrWhiteSpace($tempRoot)) {
    $tempRoot = $installRoot
}

$bootstrapLog = Join-Path $tempRoot 'occultation_bootstrap_ps.log'

try {
    Write-BootstrapLog -Message "bootstrap launch: $PSCommandPath"

    $principal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
    $isAdmin = $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

    if (-not $isAdmin) {
        if ($Elevated) {
            throw 'Could not obtain Administrator rights.'
        }

        Write-Host 'Requesting Administrator rights (UAC)...'
        $launchArgs = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', ('"{0}"' -f $PSCommandPath), '-Elevated')
        if ($NoPause) { $launchArgs += '-NoPause' }
        Start-Process -Verb RunAs -FilePath 'powershell.exe' -ArgumentList ($launchArgs -join ' ')
        exit 0
    }

    Write-Host ''
    Write-Host 'Occultation Tools - NTP Guided Setup Bootstrap (PowerShell)'
    Write-Host '-----------------------------------------------------------'
    Write-Host "This will download/update installer files to:"
    Write-Host "  $installRoot"
    Write-Host ''

    $reply = Read-Host 'Continue setup now? [Y/N]'
    if ($reply -notin @('Y', 'y', 'N', 'n')) {
        throw 'Invalid choice. Enter Y or N.'
    }
    if ($reply -in @('N', 'n')) {
        Write-Host 'Cancelled.'
        exit 0
    }

    foreach ($dir in @(
        $installRoot,
        (Join-Path $installRoot 'scripts'),
        (Join-Path $installRoot 'config'),
        (Join-Path $installRoot 'resources'),
        (Join-Path $installRoot 'logs')
    )) {
        if (-not (Test-Path $dir)) {
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
        }
    }

    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

    $files = @(
        'scripts/install_ntp_timing_guided.ps1',
        'scripts/install_ntp_timing_guided.cmd',
        'config/ntp.conf.template',
        'config/ntp-country-servers.json',
        'resources/ntp_pool_zones.json',
        'resources/national_utc_ntp_servers.json'
    )

    Write-Host ''
    Write-Host 'Downloading setup files...'
    foreach ($rel in $files) {
        $src = "$baseUrl/$rel"
        $dst = Join-Path $installRoot ($rel -replace '/', '\\')
        Write-Host "  $rel"
        Invoke-WebRequest -UseBasicParsing -Uri $src -OutFile $dst
        Write-BootstrapLog -Message "downloaded $rel"
    }

    $guided = Join-Path $installRoot 'scripts\install_ntp_timing_guided.ps1'
    Write-Host ''
    Write-Host 'Starting guided installer...'
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $guided
    $exitCode = $LASTEXITCODE
    if ($exitCode -ne 0) {
        throw "Guided installer exited with code $exitCode"
    }

    Write-Host ''
    Write-Host 'Setup launcher completed.'
    Wait-BeforeCloseIfNeeded
    exit 0
}
catch {
    Write-Host ''
    Write-Host ('[ERROR] ' + $_.Exception.Message)
    Write-Host ('Diagnostic log: ' + $bootstrapLog)
    Write-BootstrapLog -Message ("error: " + $_.Exception.Message)
    Wait-BeforeCloseIfNeeded
    exit 1
}
