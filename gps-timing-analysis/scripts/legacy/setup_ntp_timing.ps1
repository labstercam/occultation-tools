[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseApprovedVerbs', 'Download-FileIfUrlProvided', Justification = 'Legacy identifier in analyzer diagnostics; non-functional.')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseApprovedVerbs', 'Load-CountryServers', Justification = 'Legacy identifier in analyzer diagnostics; non-functional.')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseApprovedVerbs', 'Render-NtpConf', Justification = 'Legacy identifier in analyzer diagnostics; non-functional.')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseApprovedVerbs', 'Run-Validation', Justification = 'Legacy identifier in analyzer diagnostics; non-functional.')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', 'Download-FileIfUrlProvided', Justification = 'Legacy identifier in analyzer diagnostics; non-functional.')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', 'Install-FromFile', Justification = 'Function already supports ShouldProcess; diagnostic noise only.')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', 'Set-PpsRegistryProvider', Justification = 'Function already supports ShouldProcess; diagnostic noise only.')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', 'Render-NtpConf', Justification = 'Legacy identifier in analyzer diagnostics; non-functional.')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', 'Restart-NtpService', Justification = 'Function already supports ShouldProcess; diagnostic noise only.')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseApprovedVerbs', '', Justification = 'Legacy helper naming retained for readability and script compatibility; no runtime impact.')]
[Diagnostics.CodeAnalysis.SuppressMessageAttribute('PSUseShouldProcessForStateChangingFunctions', '', Justification = 'Top-level script uses ShouldProcess; helper-level warnings are non-functional noise in this workflow.')]

# LEGACY SCRIPT: retained for legacy/testing workflows only.
# For normal installs, use scripts/install_ntp_timing_guided.ps1 (or root bootstrap launchers).
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Mandatory = $false)]
    [ValidateSet("NZ", "AU", "US", "Other")]
    [string]$Country = "NZ",

    [Parameter(Mandatory = $false)]
    [string]$OtherCountryCode = "",

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 256)]
    [int]$ComPort = 1,

    [Parameter(Mandatory = $false)]
    [ValidateSet(2, 18, 34, 50, 66, 82)]
    [int]$GpsMode = 18,

    [Parameter(Mandatory = $false)]
    [string]$NtpInstallRoot = "",

    [Parameter(Mandatory = $false)]
    [string]$StatsDir = "",

    [Parameter(Mandatory = $false)]
    [string]$PpsDllPath,

    [Parameter(Mandatory = $false)]
    [string]$MeinbergInstallerUrl = "https://www.meinbergglobal.com/download/ntp/windows/ntp-4.2.8p18a2-win32-setup.exe",

    [Parameter(Mandatory = $false)]
    [string]$MeinbergInstallerSha256 = "f933bc66ed987eb436f8345f6331de4ffad24e6ce5e5a6f5ce98109b7b29f164",

    [Parameter(Mandatory = $false)]
    [string]$MeinbergInstallerSha256Url = "https://www.meinbergglobal.com/download/ntp/windows/ntp-4.2.8p18a2-win32-setup.exe.sha256sum",

    [Parameter(Mandatory = $false)]
    [string]$MeinbergInstallerSilentArgs = "",

    [Parameter(Mandatory = $false)]
    [string]$NtpMonitorInstallerUrl = "https://www.meinbergglobal.com/download/ntp/windows/time-server-monitor/ntp-time-server-monitor-104.exe",

    [Parameter(Mandatory = $false)]
    [string]$NtpMonitorInstallerSilentArgs = "",

    [Parameter(Mandatory = $false)]
    [switch]$SkipInstall,

    [Parameter(Mandatory = $false)]
    [switch]$SkipRegistry,

    [Parameter(Mandatory = $false)]
    [switch]$SkipServiceRestart,

    [Parameter(Mandatory = $false)]
    [switch]$SkipPermissions,

    [Parameter(Mandatory = $false)]
    [switch]$NonInteractive,

    [Parameter(Mandatory = $false)]
    [string]$CountryConfigRemoteUrl = "https://raw.githubusercontent.com/labstercam/occultation-tools/main/gps-timing-analysis/config/ntp-country-servers.json",

    [Parameter(Mandatory = $false)]
    [string]$PoolZonesRemoteUrl = "https://raw.githubusercontent.com/labstercam/occultation-tools/main/gps-timing-analysis/resources/ntp_pool_zones.json",

    [Parameter(Mandatory = $false)]
    [string]$NationalUtcRemoteUrl = "https://raw.githubusercontent.com/labstercam/occultation-tools/main/gps-timing-analysis/resources/national_utc_ntp_servers.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$msg) { Write-Host "[INFO] $msg" -ForegroundColor Cyan }
function Write-WarnMsg([string]$msg) { Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Ok([string]$msg) { Write-Host "[ OK ] $msg" -ForegroundColor Green }

$script:CountryConfigRemoteUrl = $CountryConfigRemoteUrl
$script:PoolZonesRemoteUrl = $PoolZonesRemoteUrl
$script:NationalUtcRemoteUrl = $NationalUtcRemoteUrl

function Get-JsonResourceWithFallback {
    param(
        [string]$LocalPath,
        [string]$RemoteUrl,
        [string]$ResourceLabel
    )

    if (-not [string]::IsNullOrWhiteSpace($RemoteUrl)) {
        try {
            Write-Info ("Loading {0} from GitHub: {1}" -f $ResourceLabel, $RemoteUrl)
            $resp = Invoke-WebRequest -Uri $RemoteUrl -UseBasicParsing -TimeoutSec 20
            return ($resp.Content | ConvertFrom-Json)
        }
        catch {
            Write-WarnMsg ("Failed to load {0} from GitHub: {1}" -f $ResourceLabel, $_.Exception.Message)
            Write-WarnMsg ("Falling back to local file: {0}" -f $LocalPath)
        }
    }

    if (-not (Test-Path -LiteralPath $LocalPath)) {
        throw ("{0} not found remotely or locally. Local path: {1}" -f $ResourceLabel, $LocalPath)
    }

    return (Get-Content -Raw -LiteralPath $LocalPath | ConvertFrom-Json)
}

function Select-CountryInteractive {
    while ($true) {
        Write-Host "Select region for NTP setup:" -ForegroundColor Cyan
        Write-Host "  1) NZ"
        Write-Host "  2) AU"
        Write-Host "  3) US"
        Write-Host "  4) Other"
        $choice = Read-Host "Enter 1-4 (default 1)"
        if ([string]::IsNullOrWhiteSpace($choice) -or $choice -eq "1") { return "NZ" }
        if ($choice -eq "2") { return "AU" }
        if ($choice -eq "3") { return "US" }
        if ($choice -eq "4") { return "Other" }
        Write-WarnMsg "Invalid selection."
    }
}

function Read-OtherCountryCodeInteractive {
    while ($true) {
        $raw = Read-Host "Enter 2-letter country code top-level domain (ccTLD), e.g. fr, de, jp"
        if ([string]::IsNullOrWhiteSpace($raw)) {
            Write-WarnMsg "Country code cannot be empty."
            continue
        }

        $cc = $raw.Trim().ToLowerInvariant()
        if ($cc -match '^[a-z]{2}$') {
            return $cc
        }

        Write-WarnMsg "Please enter exactly two letters (ISO country code / ccTLD format)."
    }
}

function Get-RegionPoolZoneForCountryCode {
    param([string]$CountryCode)

    $cc = $CountryCode.ToLowerInvariant()

    $europe = @('ad','al','am','at','ax','az','ba','be','bg','by','ch','cy','cz','de','dk','ee','es','fi','fo','fr','gb','ge','gg','gi','gr','hr','hu','ie','im','is','it','je','kg','kz','li','lt','lu','lv','mc','md','me','mk','mt','nl','no','pl','pt','ro','rs','ru','se','si','sj','sk','sm','tj','tm','tr','ua','uz','va')
    $northAmerica = @('ag','ai','aw','bb','bm','bs','bz','ca','cr','cu','dm','do','gd','gl','gt','hn','ht','jm','kn','ky','lc','mq','ms','mx','ni','pa','pm','pr','sv','sx','tc','tt','us','vc','vg','vi')
    $southAmerica = @('ar','bo','br','cl','co','ec','fk','gf','gy','pe','py','sr','uy','ve')
    $asia = @('ae','af','bd','bh','bn','bt','cn','hk','id','il','in','iq','ir','jo','jp','kh','kp','kr','kw','la','lb','lk','mm','mn','mo','mv','my','np','om','ph','pk','ps','qa','sa','sg','sy','th','tl','tw','vn','ye')
    $oceania = @('as','au','ck','fj','fm','gu','ki','mh','mp','nc','nf','nr','nu','nz','pg','pn','pw','sb','tk','to','tv','um','vu','wf','ws')
    $africa = @('ao','bf','bi','bj','bw','cd','cf','cg','ci','cm','cv','dj','dz','eg','eh','er','et','ga','gh','gm','gn','gq','gw','ke','km','lr','ls','ly','ma','mg','ml','mr','mu','mw','mz','na','ne','ng','re','rw','sc','sd','sh','sl','sn','so','ss','st','sz','td','tg','tn','tz','ug','yt','za','zm','zw')

    if ($europe -contains $cc) { return 'europe' }
    if ($northAmerica -contains $cc) { return 'north-america' }
    if ($southAmerica -contains $cc) { return 'south-america' }
    if ($asia -contains $cc) { return 'asia' }
    if ($oceania -contains $cc) { return 'oceania' }
    if ($africa -contains $cc) { return 'africa' }

    return ''
}

function Load-NtpPoolZonesResource {
    param([string]$ResourcePath)

    return Get-JsonResourceWithFallback -LocalPath $ResourcePath -RemoteUrl $script:PoolZonesRemoteUrl -ResourceLabel "NTP pool zones resource"
}

function Load-NationalUtcInventoryResource {
    param([string]$ResourcePath)

    return Get-JsonResourceWithFallback -LocalPath $ResourcePath -RemoteUrl $script:NationalUtcRemoteUrl -ResourceLabel "National UTC/NTP inventory resource"
}

function Get-IndexedPoolServers {
    param(
        [string[]]$PoolHostnames,
        [int]$MaxCount
    )

    $indexed = @(
        $PoolHostnames |
            Where-Object { $_ -match '^([0-9]+)\..+\.pool\.ntp\.org$' } |
            Sort-Object { [int](($_ -split '\.')[0]) }
    )

    return @($indexed | Select-Object -First $MaxCount)
}

function Resolve-ServersForOtherCountry {
    param(
        [string]$CountryCode,
        [string]$PoolZonesPath,
        [switch]$UseRegionWhenCountryPoolSmallOnly
    )

    $cc = $CountryCode.ToLowerInvariant()
    $poolData = Load-NtpPoolZonesResource -ResourcePath $PoolZonesPath

    $countryEntry = @($poolData.countries | Where-Object { $_.zone -eq $cc } | Select-Object -First 1)
    $countryPoolHostnames = if ($countryEntry.Count -gt 0) { @($countryEntry[0].pool_hostnames) } else { @() }

    $listedActive = $null
    if ($countryEntry.Count -gt 0 -and $null -ne $countryEntry[0].counts -and $null -ne $countryEntry[0].counts.listed_active) {
        try {
            $listedActive = [int]$countryEntry[0].counts.listed_active
        }
        catch {
            $listedActive = $null
        }
    }

    $countryIndexed = Get-IndexedPoolServers -PoolHostnames $countryPoolHostnames -MaxCount 3
    if ($countryIndexed.Count -lt 3) {
        $countryIndexed = @(
            "0.$cc.pool.ntp.org",
            "1.$cc.pool.ntp.org",
            "2.$cc.pool.ntp.org"
        )
    }

    $servers = @($countryIndexed | ForEach-Object { "$_ iburst" })

    $region = $null
    if ($null -ne $poolData.country_to_region) {
        $region = $poolData.country_to_region.$cc
    }
    if ([string]::IsNullOrWhiteSpace([string]$region) -and $countryEntry.Count -gt 0) {
        $region = $countryEntry[0].region
    }
    if ([string]::IsNullOrWhiteSpace([string]$region)) {
        $region = Get-RegionPoolZoneForCountryCode -CountryCode $cc
    }

    $includeRegionServers = $true
    if ($UseRegionWhenCountryPoolSmallOnly -and $null -ne $listedActive -and $listedActive -ge 30) {
        $includeRegionServers = $false
        Write-Info "Country pool for '$cc' has $listedActive listed active servers; skipping regional pool fallback."
    }

    if ($includeRegionServers -and -not [string]::IsNullOrWhiteSpace([string]$region)) {
        $regionEntry = @($poolData.regions | Where-Object { $_.zone -eq $region } | Select-Object -First 1)
        $regionPoolHostnames = if ($regionEntry.Count -gt 0) { @($regionEntry[0].pool_hostnames) } else { @() }

        $regionIndexed = Get-IndexedPoolServers -PoolHostnames $regionPoolHostnames -MaxCount 2
        if ($regionIndexed.Count -lt 2) {
            $regionIndexed = @(
                "0.$region.pool.ntp.org",
                "1.$region.pool.ntp.org"
            )
        }

        $servers += @($regionIndexed | ForEach-Object { "$_ iburst" })
    }
    elseif ($includeRegionServers) {
        Write-WarnMsg "Could not determine continental region for '$cc'. Using global pool fallback for regional entries."
        $servers += @(
            "0.pool.ntp.org iburst",
            "1.pool.ntp.org iburst"
        )
    }

    return @($servers | Select-Object -Unique)
}

function Read-YesNo {
    param(
        [string]$Prompt,
        [bool]$DefaultYes
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

function Add-UniqueServers {
    param(
        [string[]]$Base,
        [string[]]$ToAdd
    )

    $result = @($Base)
    foreach ($item in $ToAdd) {
        if ($result -notcontains $item) {
            $result += $item
        }
    }
    return $result
}

function Select-AuCityServersInteractive {
    $cityMap = [ordered]@{
        "1" = "ntp.melbourne.nmi.gov.au iburst"
        "2" = "ntp.sydney.nmi.gov.au iburst"
        "3" = "ntp.sydney2.nmi.gov.au iburst"
        "4" = "ntp.perth.nmi.gov.au iburst"
        "5" = "ntp.adelaide.nmi.gov.au iburst"
        "6" = "ntp.brisbane.nmi.gov.au iburst"
    }

    while ($true) {
        Write-Host "Select up to TWO city-specific NMI servers (nearest cities recommended):" -ForegroundColor Cyan
        Write-Host "  1) Melbourne"
        Write-Host "  2) Sydney"
        Write-Host "  3) Sydney2"
        Write-Host "  4) Perth"
        Write-Host "  5) Adelaide"
        Write-Host "  6) Brisbane"
        $raw = Read-Host "Enter one or two numbers separated by comma (example: 2,3)"
        $parts = @($raw -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
        if ($parts.Count -eq 0 -or $parts.Count -gt 2) {
            Write-WarnMsg "Please select one or two cities."
            continue
        }

        $valid = $true
        $selected = @()
        foreach ($p in $parts) {
            if (-not $cityMap.Contains($p)) {
                $valid = $false
                break
            }
            $selected += $cityMap[$p]
        }

        if (-not $valid) {
            Write-WarnMsg "One or more selections were invalid."
            continue
        }

        return ($selected | Select-Object -Unique)
    }
}

function Select-NationalServersInteractive {
    param(
        [string[]]$Servers,
        [switch]$NoPrompt
    )

    $choices = @($Servers | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
    if ($choices.Count -le 1) {
        return $choices
    }

    if ($NoPrompt) {
        Write-WarnMsg "Non-interactive mode: selecting first two national servers."
        return @($choices | Select-Object -First 2)
    }

    while ($true) {
        Write-Host "National servers found. Select up to TWO servers:" -ForegroundColor Cyan
        for ($i = 0; $i -lt $choices.Count; $i++) {
            Write-Host ("  {0}) {1}" -f ($i + 1), $choices[$i])
        }
        Write-Host "Hint: numbered pairs (for example ntp1/ntp2) can provide redundancy." -ForegroundColor DarkGray

        $raw = Read-Host "Enter one or two numbers separated by comma (default: 1,2)"
        if ([string]::IsNullOrWhiteSpace($raw)) {
            return @($choices | Select-Object -First 2)
        }

        $parts = @($raw -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
        if ($parts.Count -eq 0 -or $parts.Count -gt 2) {
            Write-WarnMsg "Please select one or two server numbers."
            continue
        }

        $selected = @()
        $valid = $true
        foreach ($p in $parts) {
            if ($p -notmatch '^\d+$') {
                $valid = $false
                break
            }

            $idx = [int]$p
            if ($idx -lt 1 -or $idx -gt $choices.Count) {
                $valid = $false
                break
            }

            $selected += $choices[$idx - 1]
        }

        if (-not $valid) {
            Write-WarnMsg "One or more selections were invalid."
            continue
        }

        return @($selected | Select-Object -Unique)
    }
}

function Get-CountryConfigEntry {
    param([string]$CountryCode, [string]$ConfigPath)

    $json = Get-JsonResourceWithFallback -LocalPath $ConfigPath -RemoteUrl $script:CountryConfigRemoteUrl -ResourceLabel "Country server config"
    $prop = @($json.PSObject.Properties | Where-Object { $_.Name -ieq $CountryCode } | Select-Object -First 1)
    if ($prop.Count -eq 0) {
        return $null
    }

    return $prop[0].Value
}

function Get-NationalUtcInventoryEntry {
    param([string]$CountryCode, [string]$NationalUtcPath)

    $resource = Load-NationalUtcInventoryResource -ResourcePath $NationalUtcPath
    return @($resource.entries | Where-Object { $_.country_code -ieq $CountryCode } | Select-Object -First 1)
}

function Show-NationalUtcInventoryInfo {
    param([object]$Entry, [string]$CountryCode)

    if ($null -eq $Entry) {
        Write-WarnMsg "No national UTC/NTP inventory entry found for '$CountryCode'."
        return
    }

    Write-Info ("National UTC/NTP entry for '{0}': {1}" -f $CountryCode.ToUpperInvariant(), $Entry.country_name)
    Write-Host ("Authority: {0}" -f $Entry.authority)
    Write-Host ("Status: {0}" -f $Entry.status)

    $urls = @($Entry.source_urls)
    if ($urls.Count -gt 0) {
        Write-Host "Source URLs:"
        foreach ($u in $urls) {
            Write-Host ("  - {0}" -f $u)
        }
    }
    else {
        Write-Host "Source URLs: (none listed)"
    }

    if (-not [string]::IsNullOrWhiteSpace([string]$Entry.usage_note)) {
        Write-Host ("Note: {0}" -f $Entry.usage_note)
    }
    else {
        Write-Host "Note: (none)"
    }
}

function Resolve-ServersForCountryViaNationalInventory {
    param(
        [string]$CountryCode,
        [string]$NationalUtcPath,
        [string]$PoolZonesPath,
        [switch]$NoPrompt
    )

    $selectedServers = @()
    $entryResult = Get-NationalUtcInventoryEntry -CountryCode $CountryCode -NationalUtcPath $NationalUtcPath
    $entry = if ($entryResult.Count -gt 0) { $entryResult[0] } else { $null }

    Show-NationalUtcInventoryInfo -Entry $entry -CountryCode $CountryCode

    if ($null -ne $entry) {
        $nationalHosts = @($entry.ntp_servers | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        if ($nationalHosts.Count -gt 0) {
            $chosenNational = Select-NationalServersInteractive -Servers $nationalHosts -NoPrompt:$NoPrompt
            $selectedServers = Add-UniqueServers -Base $selectedServers -ToAdd (@($chosenNational | ForEach-Object { "$_ iburst" }))
        }
        else {
            Write-WarnMsg "No national server hostnames listed for '$CountryCode'."
        }
    }

    $poolFallback = Resolve-ServersForOtherCountry -CountryCode $CountryCode -PoolZonesPath $PoolZonesPath -UseRegionWhenCountryPoolSmallOnly
    $selectedServers = Add-UniqueServers -Base $selectedServers -ToAdd $poolFallback

    return $selectedServers
}

function Resolve-ServersForCountry {
    param(
        [string]$CountryCode,
        [string]$ConfigPath,
        [string]$NationalUtcPath,
        [string]$PoolZonesPath,
        [string]$OtherCc,
        [switch]$NoPrompt
    )

    if ($CountryCode -eq "Other") {
        $resolvedCode = $OtherCc.ToUpperInvariant()
        $configEntry = Get-CountryConfigEntry -CountryCode $resolvedCode -ConfigPath $ConfigPath
        if ($null -ne $configEntry) {
            Write-Info "Country '$resolvedCode' is defined in config; using configured server list."
            return @($configEntry.servers)
        }

        Write-Info "Country '$resolvedCode' is not defined in config; using national UTC/NTP inventory plus pool fallback."
        return Resolve-ServersForCountryViaNationalInventory -CountryCode $resolvedCode -NationalUtcPath $NationalUtcPath -PoolZonesPath $PoolZonesPath -NoPrompt:$NoPrompt
    }

    $servers = Get-CountryServers -CountryCode $CountryCode -ConfigPath $ConfigPath
    if ($CountryCode -ne "AU" -or $NoPrompt) {
        return $servers
    }

    $selectedServers = @()
    $includeNational = Read-YesNo -Prompt "Include National Standards (NMI) servers? Recommended" -DefaultYes $true
    if ($includeNational) {
        Write-Host "Choose NMI source:" -ForegroundColor Cyan
        Write-Host "  1) Public NMI endpoint (ntp.nmi.gov.au)"
        Write-Host "  2) City-specific NMI servers (requires registration + static IP)"
        $mode = Read-Host "Enter 1 or 2 (default 1)"

        if ([string]::IsNullOrWhiteSpace($mode) -or $mode -eq "1") {
            $selectedServers += "ntp.nmi.gov.au iburst"
        }
        elseif ($mode -eq "2") {
            Write-WarnMsg "City-specific NMI servers require registration and static IP address, and may not work until set up."
            $confirmed = Read-YesNo -Prompt "Do you have (or plan to) register and set up static IP?" -DefaultYes $false
            if ($confirmed) {
                $selectedServers = Add-UniqueServers -Base $selectedServers -ToAdd (Select-AuCityServersInteractive)
            }
            else {
                Write-WarnMsg "Using public NMI endpoint instead."
                $selectedServers += "ntp.nmi.gov.au iburst"
            }
        }
        else {
            Write-WarnMsg "Invalid choice; using public NMI endpoint."
            $selectedServers += "ntp.nmi.gov.au iburst"
        }
    }

    # University public servers are next tier.
    $uniServers = @($servers | Where-Object { $_ -match 'ntp\..+\.edu\.au\s+iburst$' })
    $selectedServers = Add-UniqueServers -Base $selectedServers -ToAdd $uniServers

    # AU pool fallback tier.
    $poolServers = @($servers | Where-Object { $_ -match '(^|\s)(au\.pool\.ntp\.org|[0-3]\.au\.pool\.ntp\.org)\s+iburst$' })
    $selectedServers = Add-UniqueServers -Base $selectedServers -ToAdd $poolServers

    return $selectedServers
}

function Test-PathPrefix {
    param([string]$Path, [string]$Prefix)

    $p = [System.IO.Path]::GetFullPath($Path).TrimEnd('\\')
    $x = [System.IO.Path]::GetFullPath($Prefix).TrimEnd('\\')
    return $p.StartsWith($x, [System.StringComparison]::OrdinalIgnoreCase)
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

function Show-NtpPoolZoneInfo {
    param([string]$CountryCode)

    if ([string]::IsNullOrWhiteSpace($CountryCode)) {
        return
    }

    $cc = $CountryCode.ToLowerInvariant()
    $zoneUrl = "https://www.ntppool.org/zone/$cc"

    Write-Info "NTP Pool zone check for '$cc'"

    $hostnames = 0..3 | ForEach-Object { "$_.$cc.pool.ntp.org" }
    $resolvable = @()
    foreach ($h in $hostnames) {
        try {
            $null = Resolve-DnsName -Name $h -Type A -ErrorAction Stop
            $resolvable += $h
        }
        catch {
            # Best-effort check; unresolved names are reported below.
        }
    }

    if ($resolvable.Count -gt 0) {
        Write-Host ("Resolvable pool hostnames: {0}" -f ($resolvable -join ", "))
    }
    else {
        Write-WarnMsg "No 0..3 country-pool hostnames resolved (may indicate no zone, DNS issue, or network filtering)."
    }

    try {
        $resp = Invoke-WebRequest -Uri $zoneUrl -UseBasicParsing
        $html = [string]$resp.Content

        $ipv4 = $null
        $ipv6 = $null

        $m4 = [regex]::Match($html, 'IPv4[\s\S]*?There are\s+(\d+)\s+active servers', 'IgnoreCase')
        if ($m4.Success) { $ipv4 = [int]$m4.Groups[1].Value }

        $m6 = [regex]::Match($html, 'IPv6[\s\S]*?There are\s+(\d+)\s+active servers', 'IgnoreCase')
        if ($m6.Success) { $ipv6 = [int]$m6.Groups[1].Value }

        if ($null -ne $ipv4 -or $null -ne $ipv6) {
            $ipv4Text = if ($null -ne $ipv4) { [string]$ipv4 } else { "n/a" }
            $ipv6Text = if ($null -ne $ipv6) { [string]$ipv6 } else { "n/a" }
            Write-Host ("Zone stats ($zoneUrl): IPv4 active={0}, IPv6 active={1}" -f $ipv4Text, $ipv6Text)
        }
        else {
            Write-WarnMsg "Could not parse active server counts from zone page: $zoneUrl"
        }
    }
    catch {
        Write-WarnMsg "Could not query NTP Pool zone page ($zoneUrl): $($_.Exception.Message)"
    }
}

function Test-ValidInstallPath {
    param([string]$Path)

    if ([string]::IsNullOrWhiteSpace($Path)) {
        throw "Path cannot be empty."
    }

    $full = [System.IO.Path]::GetFullPath($Path)
    $allowedRoots = @($env:ProgramFiles, ${env:ProgramFiles(x86)}) |
        Where-Object { -not [string]::IsNullOrWhiteSpace($_) }

    $isUnderProgramDir = $false
    foreach ($root in $allowedRoots) {
        if (Test-PathPrefix -Path $full -Prefix $root) {
            $isUnderProgramDir = $true
            break
        }
    }

    if (-not $isUnderProgramDir) {
        throw "Path '$full' must be under Program Files (PROGRAMDIR\\NTP)."
    }

    return $full
}

function Assert-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($id)
    if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
        throw "Run this script as Administrator."
    }
}

function Invoke-FileDownloadIfUrlProvided {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$Url,
        [string]$OutPath
    )

    if ([string]::IsNullOrWhiteSpace($Url)) {
        return $false
    }

    if ($PSCmdlet.ShouldProcess($Url, "Download installer")) {
        Write-Info "Downloading: $Url"
        Invoke-WebRequest -Uri $Url -OutFile $OutPath
        Write-Ok "Downloaded: $OutPath"
    }

    return $true
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

function Install-FromFile {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$InstallerPath,
        [string]$Arguments,
        [string]$Label
    )

    if (-not (Test-Path -LiteralPath $InstallerPath)) {
        throw "$Label installer not found at: $InstallerPath"
    }

    if ([string]::IsNullOrWhiteSpace($Arguments)) {
        Write-WarnMsg "$Label silent args are empty. Launching installer interactively."
    }

    if ($PSCmdlet.ShouldProcess($InstallerPath, "Install $Label")) {
        Write-Info "Installing $Label"
        $proc = Start-Process -FilePath $InstallerPath -ArgumentList $Arguments -PassThru -Wait
        if ($proc.ExitCode -ne 0) {
            throw "$Label installer exited with code $($proc.ExitCode)"
        }
        Write-Ok "$Label install completed"
    }
}

function Resolve-PpsDllPath {
    param([string]$PreferredPath, [string]$InstallRoot)

    $candidates = @()
    if (-not [string]::IsNullOrWhiteSpace($PreferredPath)) { $candidates += $PreferredPath }
    $candidates += (Join-Path $InstallRoot "bin\loopback-ppsapi-provider.dll")
    $candidates += "C:\Program Files (x86)\NTP\bin\loopback-ppsapi-provider.dll"
    $candidates += "C:\NTP\bin\loopback-ppsapi-provider.dll"

    foreach ($c in $candidates) {
        if (Test-Path -LiteralPath $c) {
            return (Resolve-Path -LiteralPath $c).Path
        }
    }

    throw "Could not find loopback-ppsapi-provider.dll. Provide -PpsDllPath explicitly."
}

function Set-PpsRegistryProvider {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param([string]$DllPath)

    $regPath = "HKLM:\SYSTEM\CurrentControlSet\Services\NTP"
    if (-not (Test-Path -LiteralPath $regPath)) {
        throw "Registry path not found: $regPath. Is Meinberg NTP installed?"
    }

    if ($PSCmdlet.ShouldProcess($regPath, "Set PPSProviders registry value")) {
        # Use MultiString to match the documented reg add REG_MULTI_SZ method.
        New-ItemProperty -Path $regPath -Name "PPSProviders" -PropertyType MultiString -Value $DllPath -Force | Out-Null
        Write-Ok "Set registry PPSProviders = $DllPath"
    }
}

function Grant-AclWithIcacls {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$Path,
        [string]$GrantSpec
    )

    if (-not (Test-Path -LiteralPath $Path)) {
        Write-WarnMsg "Skipping ACL update (path not found): $Path"
        return
    }

    if ($PSCmdlet.ShouldProcess($Path, "Grant ACL $GrantSpec")) {
        $output = & icacls.exe $Path /grant $GrantSpec 2>&1
        $exitCode = $LASTEXITCODE
        if ($exitCode -ne 0) {
            throw "icacls failed for '$Path' with exit code $exitCode. Output: $output"
        }
        Write-Ok "ACL updated: $Path ($GrantSpec)"
    }
}

function Set-RequiredPermissions {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$InstallRoot,
        [string]$NtpConfPath,
        [string]$StatsFolder
    )

    # Batch scripts should be runnable by normal users.
    $binDir = Join-Path $InstallRoot "bin"
    if (Test-Path -LiteralPath $binDir) {
        $batchFiles = Get-ChildItem -LiteralPath $binDir -Filter "*.bat" -File -ErrorAction SilentlyContinue
        foreach ($bat in $batchFiles) {
            Grant-AclWithIcacls -Path $bat.FullName -GrantSpec "Users:(RX)"
        }
    }
    else {
        Write-WarnMsg "bin folder not found: $binDir"
    }

    # etc folder needs create/write permissions for logs.
    $etcDir = Split-Path -Parent $NtpConfPath
    if (-not (Test-Path -LiteralPath $etcDir)) {
        if ($PSCmdlet.ShouldProcess($etcDir, "Create etc folder")) {
            New-Item -ItemType Directory -Path $etcDir -Force | Out-Null
        }
    }
    Grant-AclWithIcacls -Path $etcDir -GrantSpec "Users:(OI)(CI)M"

    # ntp.conf needs write/edit/delete for users.
    Grant-AclWithIcacls -Path $NtpConfPath -GrantSpec "Users:(M)"

    # statsdir should be writable/create-capable.
    $statsDirResolved = $StatsFolder.TrimEnd('\\')
    if (-not (Test-Path -LiteralPath $statsDirResolved)) {
        if ($PSCmdlet.ShouldProcess($statsDirResolved, "Create statsdir")) {
            New-Item -ItemType Directory -Path $statsDirResolved -Force | Out-Null
        }
    }
    Grant-AclWithIcacls -Path $statsDirResolved -GrantSpec "Users:(OI)(CI)M"
}

function Get-CountryServers {
    param([string]$CountryCode, [string]$ConfigPath)

    $entry = Get-CountryConfigEntry -CountryCode $CountryCode -ConfigPath $ConfigPath
    if ($null -eq $entry) {
        throw "Country '$CountryCode' not found in $ConfigPath"
    }

    return @($entry.servers)
}

function New-NtpConfFromTemplate {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param(
        [string]$TemplatePath,
        [string[]]$Servers,
        [int]$Port,
        [int]$Mode,
        [string]$StatsFolder,
        [string]$OutputPath
    )

    if (-not (Test-Path -LiteralPath $TemplatePath)) {
        throw "Template not found: $TemplatePath"
    }

    $template = Get-Content -Raw -LiteralPath $TemplatePath
    $serverLines = ($Servers | ForEach-Object { "server $_" }) -join [Environment]::NewLine
    $rendered = $template.Replace("{{SERVER_LINES}}", $serverLines)
    $rendered = $rendered.Replace("{{COM_PORT}}", [string]$Port)
    $rendered = $rendered.Replace("{{MODE}}", [string]$Mode)
    $rendered = $rendered.Replace("{{STATSDIR}}", $StatsFolder)

    $serverStart = "# >>> NTP_GUIDED_MANAGED_SERVERS_START"
    $serverEnd = "# <<< NTP_GUIDED_MANAGED_SERVERS_END"
    $loggingStart = "# >>> NTP_GUIDED_MANAGED_LOGGING_START"
    $loggingEnd = "# <<< NTP_GUIDED_MANAGED_LOGGING_END"

    $serverBlockPattern = "(?ms)^\s*" + [regex]::Escape($serverStart) + ".*?^\s*" + [regex]::Escape($serverEnd) + "\s*$"
    $loggingBlockPattern = "(?ms)^\s*" + [regex]::Escape($loggingStart) + ".*?^\s*" + [regex]::Escape($loggingEnd) + "\s*$"

    $serverMatch = [regex]::Match($rendered, $serverBlockPattern)
    $loggingMatch = [regex]::Match($rendered, $loggingBlockPattern)
    if (-not $serverMatch.Success -or -not $loggingMatch.Success) {
        throw "Template must include managed section markers for SERVERS and LOGGING."
    }

    $managedServersBlock = $serverMatch.Value.TrimEnd()
    $managedLoggingBlock = $loggingMatch.Value.TrimEnd()

    $outDir = Split-Path -Parent $OutputPath
    if (-not (Test-Path -LiteralPath $outDir)) {
        if ($PSCmdlet.ShouldProcess($outDir, "Create output directory")) {
            New-Item -ItemType Directory -Path $outDir | Out-Null
        }
    }

    $contentToWrite = $rendered
    if (Test-Path -LiteralPath $OutputPath) {
        $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backup = "$OutputPath.bak_$stamp"
        if ($PSCmdlet.ShouldProcess($OutputPath, "Backup existing ntp.conf")) {
            Copy-Item -LiteralPath $OutputPath -Destination $backup -Force
            Write-Info "Backup created: $backup"
        }

        $existing = Get-Content -Raw -LiteralPath $OutputPath

        # Remove previous managed sections (marker-based) and legacy generated sections.
        $preserved = [regex]::Replace($existing, $serverBlockPattern + "\r?\n?", "")
        $preserved = [regex]::Replace($preserved, $loggingBlockPattern + "\r?\n?", "")
        $preserved = [regex]::Replace($preserved, '(?ms)^\s*# Internet NTP servers \(country-specific\)\r?\n(?:.*\r?\n)*?(?=^\s*# GPS PPS / NMEA source from serial COM port)', '')
        $preserved = [regex]::Replace($preserved, '(?ms)^\s*# Enable monitoring logs\r?\nenable stats\r?\nstatsdir "[^"]*"\r?\nstatistics loopstats\r?\nstatistics peerstats\r?\n?', '')

        $preserved = $preserved.TrimEnd()
        if ([string]::IsNullOrWhiteSpace($preserved)) {
            $contentToWrite = ($managedServersBlock + [Environment]::NewLine + [Environment]::NewLine + $managedLoggingBlock)
        }
        else {
            $contentToWrite = ($preserved + [Environment]::NewLine + [Environment]::NewLine + $managedServersBlock + [Environment]::NewLine + [Environment]::NewLine + $managedLoggingBlock)
        }

        Write-Info "Preserved existing ntp.conf settings outside managed SERVERS and LOGGING sections."
    }

    if ($PSCmdlet.ShouldProcess($OutputPath, "Write ntp.conf")) {
        Set-Content -LiteralPath $OutputPath -Value $contentToWrite -Encoding ASCII
        Write-Ok "Wrote ntp.conf: $OutputPath"
    }
}

function Restart-NtpService {
    [CmdletBinding(SupportsShouldProcess = $true)]
    param()

    Write-Info "Restarting NTP service"
    if ($PSCmdlet.ShouldProcess("NTP service", "Restart")) {
        Restart-Service -Name "NTP" -ErrorAction Stop
        Start-Sleep -Seconds 2
        $svc = Get-Service -Name "NTP"
        if ($svc.Status -ne "Running") {
            throw "NTP service status is $($svc.Status)"
        }
        Write-Ok "NTP service is running"
    }
}

function Test-NtpValidation {
    param(
        [string]$InstallRoot,
        [string]$NtpConfPath
    )

    Write-Info "Validation checks"

    if (Test-Path -LiteralPath $NtpConfPath) {
        Write-Host "Config: $NtpConfPath"
    }
    else {
        Write-WarnMsg "ntp.conf not found at expected path: $NtpConfPath"
    }

    try {
        $svc = Get-Service -Name "NTP" -ErrorAction Stop
        Write-Host "Service: $($svc.Name)  Status: $($svc.Status)"
    }
    catch {
        Write-WarnMsg "NTP service lookup failed: $($_.Exception.Message)"
    }

    $ntpq = Join-Path $InstallRoot "bin\ntpq.exe"
    if (Test-Path -LiteralPath $ntpq) {
        Write-Info "Running: ntpq -pn"
        & $ntpq -pn

        Write-Info "Running: ntpq -c rv"
        & $ntpq -c rv
    }
    else {
        Write-WarnMsg "ntpq.exe not found at expected path: $ntpq"
    }
}

Assert-Admin

$scriptRoot = Split-Path -Parent $PSCommandPath
$projectRoot = Split-Path -Parent (Split-Path -Parent $scriptRoot)
$configPath = Join-Path $projectRoot "config\ntp-country-servers.json"
$nationalUtcPath = Join-Path $projectRoot "resources\national_utc_ntp_servers.json"
$poolZonesPath = Join-Path $projectRoot "resources\ntp_pool_zones.json"
$templatePath = Join-Path $projectRoot "config\ntp.conf.template"

if (-not $NonInteractive -and -not $PSBoundParameters.ContainsKey("Country")) {
    $Country = Select-CountryInteractive
}

if ($Country -eq "Other") {
    if ([string]::IsNullOrWhiteSpace($OtherCountryCode)) {
        if ($NonInteractive) {
            throw "When -Country Other is used with -NonInteractive, provide -OtherCountryCode (2-letter ccTLD, e.g. fr, de, jp)."
        }

        $OtherCountryCode = Read-OtherCountryCodeInteractive
    }
    else {
        $OtherCountryCode = $OtherCountryCode.Trim().ToLowerInvariant()
        if ($OtherCountryCode -notmatch '^[a-z]{2}$') {
            throw "-OtherCountryCode must be exactly two letters (ISO country code / ccTLD format)."
        }
    }

    Show-NtpPoolZoneInfo -CountryCode $OtherCountryCode
}
else {
    Show-NtpPoolZoneInfo -CountryCode $Country
}

if ([string]::IsNullOrWhiteSpace($NtpInstallRoot)) {
    $NtpInstallRoot = Resolve-DefaultInstallRoot
}
else {
    $NtpInstallRoot = Test-ValidInstallPath -Path $NtpInstallRoot
}

if ([string]::IsNullOrWhiteSpace($StatsDir)) {
    $StatsDir = Join-Path $NtpInstallRoot "etc\\"
}

$ntpConfPath = Join-Path $NtpInstallRoot "etc\ntp.conf"

Write-Info "Country: $Country"
if ($Country -eq "Other") {
    Write-Info "Other country code (ccTLD): $OtherCountryCode"
}
Write-Info "COM port: COM$ComPort"
Write-Info "NTP install root: $NtpInstallRoot"
Write-Info "NTP stats directory: $StatsDir"

if (-not $SkipInstall) {
    $downloadDir = Join-Path $env:TEMP "gps-timing-analysis-installer"
    if (-not (Test-Path -LiteralPath $downloadDir)) {
        if ($PSCmdlet.ShouldProcess($downloadDir, "Create temp download folder")) {
            New-Item -ItemType Directory -Path $downloadDir | Out-Null
        }
    }

    $meinbergInstaller = Join-Path $downloadDir "meinberg_installer.exe"
    $monitorInstaller = Join-Path $downloadDir "ntp_monitor_installer.exe"

    if (Invoke-FileDownloadIfUrlProvided -Url $MeinbergInstallerUrl -OutPath $meinbergInstaller) {
        $effectiveMeinbergSha = $MeinbergInstallerSha256
        if ([string]::IsNullOrWhiteSpace($effectiveMeinbergSha) -and -not [string]::IsNullOrWhiteSpace($MeinbergInstallerSha256Url)) {
            Write-Info "Fetching expected SHA256 from: $MeinbergInstallerSha256Url"
            $effectiveMeinbergSha = Get-ExpectedSha256FromUrl -ShaUrl $MeinbergInstallerSha256Url
        }
        Assert-FileSha256 -Path $meinbergInstaller -ExpectedSha256 $effectiveMeinbergSha -Label "Meinberg NTP installer"
        Install-FromFile -InstallerPath $meinbergInstaller -Arguments $MeinbergInstallerSilentArgs -Label "Meinberg NTP"
    }
    else {
        Write-WarnMsg "Meinberg installer URL not supplied. Skipping installer download/install."
    }

    if (Invoke-FileDownloadIfUrlProvided -Url $NtpMonitorInstallerUrl -OutPath $monitorInstaller) {
        Write-WarnMsg "No official checksum URL configured for NTP Time Server Monitor. Consider validating source manually."
        Install-FromFile -InstallerPath $monitorInstaller -Arguments $NtpMonitorInstallerSilentArgs -Label "NTP Server Monitor"
    }
    else {
        Write-WarnMsg "NTP monitor installer URL not supplied. Skipping monitor install."
    }
}

$resolvedDll = Resolve-PpsDllPath -PreferredPath $PpsDllPath -InstallRoot $NtpInstallRoot
Write-Info "PPS DLL path: $resolvedDll"

if (-not $SkipRegistry) {
    Set-PpsRegistryProvider -DllPath $resolvedDll
}
else {
    Write-WarnMsg "Skipping registry configuration by request"
}

$servers = Resolve-ServersForCountry -CountryCode $Country -ConfigPath $configPath -NationalUtcPath $nationalUtcPath -PoolZonesPath $poolZonesPath -OtherCc $OtherCountryCode -NoPrompt:$NonInteractive
New-NtpConfFromTemplate -TemplatePath $templatePath -Servers $servers -Port $ComPort -Mode $GpsMode -StatsFolder $StatsDir -OutputPath $ntpConfPath

if (-not $SkipPermissions) {
    Set-RequiredPermissions -InstallRoot $NtpInstallRoot -NtpConfPath $ntpConfPath -StatsFolder $StatsDir
}
else {
    Write-WarnMsg "Skipping ACL permission updates by request"
}

if (-not $SkipServiceRestart) {
    Restart-NtpService
}
else {
    Write-WarnMsg "Skipping service restart by request"
}

Test-NtpValidation -InstallRoot $NtpInstallRoot -NtpConfPath $ntpConfPath

Write-Ok "Setup workflow completed."
Write-Host "Next: confirm PPS lock in monitor (expect 'o' marker for PPS), and confirm offsets are stable." -ForegroundColor Cyan
