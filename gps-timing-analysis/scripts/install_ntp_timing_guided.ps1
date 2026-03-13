[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-WarnMsg([string]$Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Ok([string]$Message) { Write-Host "[ OK ] $Message" -ForegroundColor Green }
function Write-Step([string]$Message) { Write-Host "`n=== $Message ===" -ForegroundColor Green }

function Wait-BeforeCloseIfNeeded {
    # Keep standalone ConsoleHost windows open so users can read output/errors.
    if ($Host.Name -ne 'ConsoleHost') {
        return
    }

    # VS Code integrated terminals should not be blocked.
    if ($env:TERM_PROGRAM -eq 'vscode') {
        return
    }

    try {
        [void](Read-Host "Press Enter to close")
    }
    catch {
        # Ignore prompt failures during shutdown.
    }
}

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
        $choice = Read-Host "Action for '$Title' (Enter = Install): [I]nstall / [S]kip / E[x]it"
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

    $startArgs = @{
        FilePath = $InstallerPath
        PassThru = $true
        Wait     = $true
    }

    if ([string]::IsNullOrWhiteSpace($Arguments)) {
        Write-WarnMsg "$Label silent arguments are empty; starting installer without arguments (interactive mode)."
    }
    else {
        $startArgs.ArgumentList = $Arguments
    }

    Write-Info "Starting installer: $Label"
    $proc = Start-Process @startArgs
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

function Load-CountryConfigResource {
    param([string]$ResourcePath)
    return Get-JsonResourceWithFallback -LocalPath $ResourcePath -RemoteUrl $script:CountryConfigRemoteUrl -ResourceLabel "Country server config"
}

function Load-NtpPoolZonesResource {
    param([string]$ResourcePath)
    return Get-JsonResourceWithFallback -LocalPath $ResourcePath -RemoteUrl $script:PoolZonesRemoteUrl -ResourceLabel "NTP pool zones resource"
}

function Load-NationalUtcInventoryResource {
    param([string]$ResourcePath)
    return Get-JsonResourceWithFallback -LocalPath $ResourcePath -RemoteUrl $script:NationalUtcRemoteUrl -ResourceLabel "National UTC/NTP inventory resource"
}

function Get-CountryConfigEntry {
    param([string]$CountryCode, [string]$ConfigPath)

    $json = Load-CountryConfigResource -ResourcePath $ConfigPath
    $prop = @($json.PSObject.Properties | Where-Object { $_.Name -ieq $CountryCode } | Select-Object -First 1)
    if ($prop.Count -eq 0) {
        return $null
    }

    return $prop[0].Value
}

function Get-CountryServers {
    param([string]$CountryCode, [string]$ConfigPath)

    $entry = Get-CountryConfigEntry -CountryCode $CountryCode -ConfigPath $ConfigPath
    if ($null -eq $entry) {
        throw "Country '$CountryCode' not found in $ConfigPath"
    }

    return @($entry.servers)
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

function Get-ServerHostFromEntry {
    param([string]$Entry)

    if ([string]::IsNullOrWhiteSpace($Entry)) {
        return ""
    }

    return ($Entry.Trim() -split '\s+')[0].ToLowerInvariant()
}

function Select-ServersFromListInteractive {
    param(
        [string]$Header,
        [string]$Prompt,
        [string[]]$Servers,
        [int]$MaxCount
    )

    $choices = @($Servers | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
    if ($choices.Count -eq 0) {
        return @()
    }

    while ($true) {
        Write-Host $Header -ForegroundColor Cyan
        for ($i = 0; $i -lt $choices.Count; $i++) {
            Write-Host ("  {0}) {1}" -f ($i + 1), $choices[$i])
        }

        $raw = Read-Host ($Prompt + " Enter numbers separated by comma, or press Enter for 0")
        if ([string]::IsNullOrWhiteSpace($raw)) {
            return @()
        }

        $parts = @($raw -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" })
        if ($parts.Count -gt $MaxCount) {
            Write-WarnMsg ("Please select up to {0} servers." -f $MaxCount)
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

function Convert-PrefixLengthToSubnetMask {
    param([int]$PrefixLength)

    if ($PrefixLength -lt 0 -or $PrefixLength -gt 32) {
        return ""
    }

    $remaining = $PrefixLength
    $octets = @()
    for ($i = 0; $i -lt 4; $i++) {
        if ($remaining -ge 8) {
            $octets += 255
            $remaining -= 8
            continue
        }

        if ($remaining -le 0) {
            $octets += 0
            continue
        }

        $octets += (256 - [math]::Pow(2, (8 - $remaining)))
        $remaining = 0
    }

    return (($octets | ForEach-Object { [int]$_ }) -join '.')
}

function Get-ActiveIpv4Configuration {
    $configs = @()
    try {
        $configs = @(
            Get-NetIPConfiguration -ErrorAction Stop |
                Where-Object { $null -ne $_.IPv4Address -and $null -ne $_.IPv4DefaultGateway }
        )
    }
    catch {
        return $null
    }

    if ($configs.Count -eq 0) {
        return $null
    }

    $selected = @($configs | Where-Object { $null -ne $_.NetAdapter -and $_.NetAdapter.Status -eq 'Up' } | Select-Object -First 1)
    if ($selected.Count -eq 0) {
        $selected = @($configs | Select-Object -First 1)
    }

    $cfg = $selected[0]
    $ipObj = @($cfg.IPv4Address | Select-Object -First 1)
    $ip = if ($ipObj.Count -gt 0) { [string]$ipObj[0].IPAddress } else { "" }
    $prefix = if ($ipObj.Count -gt 0) { [int]$ipObj[0].PrefixLength } else { 24 }
    $gateway = ""
    if ($null -ne $cfg.IPv4DefaultGateway) {
        $gateway = [string]$cfg.IPv4DefaultGateway.NextHop
    }

    $dns = @()
    if ($null -ne $cfg.DNSServer -and $null -ne $cfg.DNSServer.ServerAddresses) {
        $dns = @($cfg.DNSServer.ServerAddresses | Where-Object { $_ -match '^\d+\.\d+\.\d+\.\d+$' })
    }

    $dhcpState = "Unknown"
    try {
        $iface = Get-NetIPInterface -InterfaceIndex $cfg.InterfaceIndex -AddressFamily IPv4 -ErrorAction Stop
        if ($iface.Dhcp -eq 'Enabled') { $dhcpState = "Enabled" }
        elseif ($iface.Dhcp -eq 'Disabled') { $dhcpState = "Disabled" }
    }
    catch {
        $dhcpState = "Unknown"
    }

    return [pscustomobject]@{
        AdapterAlias = [string]$cfg.InterfaceAlias
        IPAddress    = $ip
        PrefixLength = $prefix
        SubnetMask   = Convert-PrefixLengthToSubnetMask -PrefixLength $prefix
        Gateway      = $gateway
        DnsServers   = $dns
        DhcpState    = $dhcpState
    }
}

function Get-SuggestedStaticIpAddress {
    param(
        [string]$CurrentIp,
        [string]$Gateway
    )

    if ([string]::IsNullOrWhiteSpace($CurrentIp)) {
        return ""
    }

    $parts = @($CurrentIp -split '\.')
    if ($parts.Count -ne 4) {
        return $CurrentIp
    }

    $octet = 0
    if (-not [int]::TryParse($parts[3], [ref]$octet)) {
        return $CurrentIp
    }

    $candidates = @($octet + 20, $octet + 30, $octet + 10)
    foreach ($cand in $candidates) {
        if ($cand -lt 2 -or $cand -gt 254) {
            continue
        }

        $testIp = "{0}.{1}.{2}.{3}" -f $parts[0], $parts[1], $parts[2], $cand
        if ($testIp -ne $Gateway -and $testIp -ne $CurrentIp) {
            return $testIp
        }
    }

    return $CurrentIp
}

function Show-StaticIpGuidance {
    Write-Host "Brief static IP guide for Windows 10/11:" -ForegroundColor Cyan

    $net = Get-ActiveIpv4Configuration
    if ($null -ne $net -and -not [string]::IsNullOrWhiteSpace($net.IPAddress)) {
        $suggestedIp = Get-SuggestedStaticIpAddress -CurrentIp $net.IPAddress -Gateway $net.Gateway

        Write-Host ""
        Write-Host "Detected current active network settings:" -ForegroundColor Cyan
        Write-Host ("  Adapter: {0}" -f $net.AdapterAlias)
        Write-Host ("  Current IPv4: {0}" -f $net.IPAddress)
        Write-Host ("  Subnet mask: {0}" -f $net.SubnetMask)
        Write-Host ("  Gateway: {0}" -f $net.Gateway)
        if ($net.DnsServers.Count -gt 0) {
            Write-Host ("  DNS: {0}" -f ($net.DnsServers -join ', '))
        }
        Write-Host ("  DHCP: {0}" -f $net.DhcpState)

        Write-Host ""
        Write-Host "Suggested static IPv4 values to enter:" -ForegroundColor Cyan
        Write-Host ("  IP address: {0}" -f $suggestedIp)
        Write-Host ("  Subnet mask: {0}" -f $net.SubnetMask)
        Write-Host ("  Gateway: {0}" -f $net.Gateway)
        if ($net.DnsServers.Count -gt 0) {
            Write-Host ("  Preferred DNS: {0}" -f $net.DnsServers[0])
            if ($net.DnsServers.Count -gt 1) {
                Write-Host ("  Alternate DNS: {0}" -f $net.DnsServers[1])
            }
        }

        Write-WarnMsg "Important: use an IP address outside your router DHCP range (or reserve this IP in the router) to avoid conflicts."
    }
    else {
        Write-WarnMsg "Could not auto-detect current IPv4 settings."
        Write-Host "Use your current IPv4, subnet mask, gateway, and DNS as a starting point, then choose a nearby unused IP." -ForegroundColor Yellow
    }

    Write-Host ""
    Write-Host "How to enter on Windows 10/11:" -ForegroundColor Cyan
    Write-Host "  1) Open Settings > Network and Internet > Advanced network settings."
    Write-Host "  2) Open your active adapter (Ethernet/Wi-Fi) and choose View additional properties."
    Write-Host "  3) Under IP assignment, click Edit."
    Write-Host "  4) Select Manual, enable IPv4, and enter the suggested values."
    Write-Host "  5) Save and confirm internet access still works."
    Write-Host ""
    Write-Host "Simple step-by-step guide: https://support.microsoft.com/windows/change-tcp-ip-settings"
}

function Resolve-AuServersInteractive {
    param([string]$ConfigPath)

    $entry = Get-CountryConfigEntry -CountryCode "AU" -ConfigPath $ConfigPath
    if ($null -eq $entry) {
        throw "Country 'AU' not found in $ConfigPath"
    }

    $all = @($entry.servers)
    $nmiAll = @($all | Where-Object {
            $h = Get-ServerHostFromEntry -Entry $_
            $h -match '(^|\.)nmi\.gov\.au$'
        })

    $eduAll = @($all | Where-Object {
            $h = Get-ServerHostFromEntry -Entry $_
            $h -match '\.edu\.au$'
        })

    $poolNumbered = @($all | Where-Object {
            $h = Get-ServerHostFromEntry -Entry $_
            $h -match '^[0-3]\.au\.pool\.ntp\.org$'
        } | Select-Object -Unique)

    if ($poolNumbered.Count -lt 4) {
        $poolNumbered = @("0.au.pool.ntp.org iburst", "1.au.pool.ntp.org iburst", "2.au.pool.ntp.org iburst", "3.au.pool.ntp.org iburst")
    }

    $selected = @()
    $nmiUsed = $false

    Write-Info "Select the NTP servers to use."
    Write-Host "Where possible, choose servers that are near to you." -ForegroundColor Cyan
    Write-Host "Prefer servers in the same or neighbouring city/state/territory." -ForegroundColor Cyan

    Write-Host "" 
    Write-Host "Do you want to use NTP servers from the National Measurement Institute (NMI)?" -ForegroundColor Cyan
    Write-Host "These are the best servers and are traceable to UTC." -ForegroundColor Cyan
    Write-Host "However, you must register your computer and use a static IP address." -ForegroundColor Cyan
    Write-Host "Details will be provided." -ForegroundColor Cyan
    $useNmi = Read-YesNo -Prompt "Use NMI servers?" -DefaultYes $true
    if ($useNmi) {
        $primaryNmi = @($nmiAll | Where-Object { (Get-ServerHostFromEntry -Entry $_) -eq 'ntp.nmi.gov.au' } | Select-Object -First 1)
        if ($primaryNmi.Count -eq 0) {
            $primaryNmi = @("ntp.nmi.gov.au iburst")
        }

        $selected = Add-UniqueServers -Base $selected -ToAdd $primaryNmi
        $nmiUsed = $true

        $remainingNmi = @($nmiAll | Where-Object { (Get-ServerHostFromEntry -Entry $_) -ne 'ntp.nmi.gov.au' } | Select-Object -Unique)
        $chosenNmi = Select-ServersFromListInteractive -Header "Select 0, 1 or 2 NMI servers:`nChoose ones nearest to your city/state/territory.`nIf you choose 0 or 1, additional servers will be added in the next steps." -Prompt "Select NMI servers." -Servers $remainingNmi -MaxCount 2
        $selected = Add-UniqueServers -Base $selected -ToAdd $chosenNmi
    }

    $chosenEdu = Select-ServersFromListInteractive -Header "Select 0, 1 or 2 University servers:`nChoose ones nearest to your city/state/territory.`nIf you choose 0 or 1, additional servers will be added in the next steps." -Prompt "Select University servers." -Servers $eduAll -MaxCount 2
    $selected = Add-UniqueServers -Base $selected -ToAdd $chosenEdu

    foreach ($pool in $poolNumbered) {
        if ($selected.Count -ge 5) {
            break
        }
        $selected = Add-UniqueServers -Base $selected -ToAdd @($pool)
    }

    if ($selected.Count -lt 5) {
        Write-WarnMsg "Not enough numbered AU pool servers were available to reach 5 unique entries."
    }

    Write-Step "AU server selection summary"
    for ($i = 0; $i -lt $selected.Count; $i++) {
        Write-Host ("  {0}) {1}" -f ($i + 1), $selected[$i])
    }

    if ($nmiUsed) {
        Write-WarnMsg "You must register to use NMI servers, and have a static IP address."
        Write-Host "To register, email time@measurement.gov.au" -ForegroundColor Yellow
        Write-Host "More details:" -ForegroundColor Yellow
        Write-Host "https://www.industry.gov.au/national-measurement-institute/nmi-services/physical-measurement-services/time-and-frequency-services" -ForegroundColor Yellow

        if (Read-YesNo -Prompt "Do you want more information about using a static IP address for your PC?" -DefaultYes $false) {
            Show-StaticIpGuidance
        }
    }

    return @($selected)
}

function Select-NationalServersInteractive {
    param([string[]]$Servers)

    $choices = @($Servers | Where-Object { -not [string]::IsNullOrWhiteSpace($_) } | Select-Object -Unique)
    if ($choices.Count -le 1) {
        return $choices
    }

    while ($true) {
        Write-Host "National servers found. Select up to TWO servers:" -ForegroundColor Cyan
        for ($i = 0; $i -lt $choices.Count; $i++) {
            Write-Host ("  {0}) {1}" -f ($i + 1), $choices[$i])
        }

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
            if ($p -notmatch '^\d+$') { $valid = $false; break }
            $idx = [int]$p
            if ($idx -lt 1 -or $idx -gt $choices.Count) { $valid = $false; break }
            $selected += $choices[$idx - 1]
        }

        if (-not $valid) {
            Write-WarnMsg "One or more selections were invalid."
            continue
        }

        return @($selected | Select-Object -Unique)
    }
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
        try { $listedActive = [int]$countryEntry[0].counts.listed_active } catch { $listedActive = $null }
    }

    $countryIndexed = Get-IndexedPoolServers -PoolHostnames $countryPoolHostnames -MaxCount 3
    if ($countryIndexed.Count -lt 3) {
        $countryIndexed = @("0.$cc.pool.ntp.org", "1.$cc.pool.ntp.org", "2.$cc.pool.ntp.org")
    }

    $servers = @($countryIndexed | ForEach-Object { "$_ iburst" })

    $region = $null
    if ($null -ne $poolData.country_to_region) { $region = $poolData.country_to_region.$cc }
    if ([string]::IsNullOrWhiteSpace([string]$region) -and $countryEntry.Count -gt 0) { $region = $countryEntry[0].region }
    if ([string]::IsNullOrWhiteSpace([string]$region)) { $region = Get-RegionPoolZoneForCountryCode -CountryCode $cc }

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
            $regionIndexed = @("0.$region.pool.ntp.org", "1.$region.pool.ntp.org")
        }

        $servers += @($regionIndexed | ForEach-Object { "$_ iburst" })
    }
    elseif ($includeRegionServers) {
        Write-WarnMsg "Could not determine continental region for '$cc'. Using global pool fallback for regional entries."
        $servers += @("0.pool.ntp.org iburst", "1.pool.ntp.org iburst")
    }

    return @($servers | Select-Object -Unique)
}

function Resolve-ServersForCountryViaNationalInventory {
    param(
        [string]$CountryCode,
        [string]$NationalUtcPath,
        [string]$PoolZonesPath
    )

    $selectedServers = @()
    $resource = Load-NationalUtcInventoryResource -ResourcePath $NationalUtcPath
    $entryResult = @($resource.entries | Where-Object { $_.country_code -ieq $CountryCode } | Select-Object -First 1)
    $entry = if ($entryResult.Count -gt 0) { $entryResult[0] } else { $null }

    if ($null -ne $entry) {
        Write-Info ("National UTC/NTP entry for '{0}': {1}" -f $CountryCode.ToUpperInvariant(), $entry.country_name)
        Write-Host ("Authority: {0}" -f $entry.authority)
        Write-Host ("Status: {0}" -f $entry.status)
        if (-not [string]::IsNullOrWhiteSpace([string]$entry.usage_note)) {
            Write-Host ("Note: {0}" -f $entry.usage_note)
        }

        $urls = @($entry.source_urls)
        if ($urls.Count -gt 0) {
            Write-Host "Source URLs:"
            foreach ($u in $urls) { Write-Host ("  - {0}" -f $u) }
        }

        $nationalHosts = @($entry.ntp_servers | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
        if ($nationalHosts.Count -gt 0) {
            $chosenNational = Select-NationalServersInteractive -Servers $nationalHosts
            $selectedServers = Add-UniqueServers -Base $selectedServers -ToAdd (@($chosenNational | ForEach-Object { "$_ iburst" }))
        }
        else {
            Write-WarnMsg "No national server hostnames listed for '$CountryCode'."
        }
    }
    else {
        Write-WarnMsg "No national UTC/NTP inventory entry found for '$CountryCode'."
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
        [string]$OtherCc
    )

    if ($CountryCode -eq "Other") {
        $resolvedCode = $OtherCc.ToUpperInvariant()
        $configEntry = Get-CountryConfigEntry -CountryCode $resolvedCode -ConfigPath $ConfigPath
        if ($null -ne $configEntry) {
            Write-Info "Country '$resolvedCode' is defined in config; using configured server list."
            return @($configEntry.servers)
        }

        Write-Info "Country '$resolvedCode' is not defined in config; using national UTC/NTP inventory plus pool fallback."
        return Resolve-ServersForCountryViaNationalInventory -CountryCode $resolvedCode -NationalUtcPath $NationalUtcPath -PoolZonesPath $PoolZonesPath
    }

    if ($CountryCode -eq "AU") {
        return Resolve-AuServersInteractive -ConfigPath $ConfigPath
    }

    return Get-CountryServers -CountryCode $CountryCode -ConfigPath $ConfigPath
}

function Update-NtpManagedSectionsFromTemplate {
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
        New-Item -ItemType Directory -Path $outDir -Force | Out-Null
    }

    $contentToWrite = $rendered
    if (Test-Path -LiteralPath $OutputPath) {
        $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
        $backup = "$OutputPath.bak_$stamp"
        Copy-Item -LiteralPath $OutputPath -Destination $backup -Force
        Write-Info "Backup created: $backup"

        $existing = Get-Content -Raw -LiteralPath $OutputPath
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

    Set-Content -LiteralPath $OutputPath -Value $contentToWrite -Encoding ASCII
    Write-Ok "Updated ntp.conf managed sections: $OutputPath"
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

function Get-ComOptionalPropertyValue {
    param(
        [object]$Object,
        [string]$Name,
        [object]$Default = ""
    )

    if ($null -eq $Object) {
        return $Default
    }

    $prop = $Object.PSObject.Properties[$Name]
    if ($null -eq $prop) {
        return $Default
    }

    return $prop.Value
}

function Get-ComPortSnapshot {
    $hasGetPnpDevice = $null -ne (Get-Command -Name Get-PnpDevice -ErrorAction SilentlyContinue)
    $hasGetPnpDeviceProperty = $null -ne (Get-Command -Name Get-PnpDeviceProperty -ErrorAction SilentlyContinue)

    $ports = @()
    if ($hasGetPnpDevice) {
        try {
            $ports = @(Get-PnpDevice -Class Ports -PresentOnly -ErrorAction Stop)
        }
        catch {
            Write-WarnMsg ("Get-PnpDevice failed; falling back to Win32_SerialPort. {0}" -f $_.Exception.Message)
            $ports = @()
        }
    }

    $serialByInstanceId = @{}
    $serialRecords = @(Get-CimInstance Win32_SerialPort -ErrorAction SilentlyContinue)

    foreach ($serial in $serialRecords) {
        if (-not [string]::IsNullOrWhiteSpace($serial.PNPDeviceID)) {
            $serialByInstanceId[$serial.PNPDeviceID] = $serial
        }
    }

    if ($ports.Count -eq 0) {
        foreach ($serial in $serialRecords) {
            $friendly = [string](Get-ComOptionalPropertyValue -Object $serial -Name "Name")
            $comPort = [string](Get-ComOptionalPropertyValue -Object $serial -Name "DeviceID")
            if ([string]::IsNullOrWhiteSpace($comPort) -and $friendly -match '\((COM\d+)\)') {
                $comPort = $matches[1]
            }

            $ports += [pscustomobject]@{
                InstanceId   = [string](Get-ComOptionalPropertyValue -Object $serial -Name "PNPDeviceID")
                FriendlyName = $friendly
                Status       = [string](Get-ComOptionalPropertyValue -Object $serial -Name "Status")
                Manufacturer = [string](Get-ComOptionalPropertyValue -Object $serial -Name "Manufacturer")
                Description  = [string](Get-ComOptionalPropertyValue -Object $serial -Name "Description")
                Service      = [string](Get-ComOptionalPropertyValue -Object $serial -Name "Service")
                COMPort      = $comPort
                HardwareIds  = @()
            }
        }

        return @($ports | Sort-Object COMPort, FriendlyName)
    }

    $result = @()
    foreach ($port in $ports) {
        $friendly = [string]$port.FriendlyName
        $comPort = ""
        if ($friendly -match '\((COM\d+)\)') {
            $comPort = $matches[1]
        }

        $manufacturer = ""
        $hardwareIds = @()

        if ($hasGetPnpDeviceProperty) {
            try {
                $manufacturer = [string](Get-PnpDeviceProperty -InstanceId $port.InstanceId -KeyName 'DEVPKEY_Device_Manufacturer' -ErrorAction SilentlyContinue).Data
            }
            catch {
                $manufacturer = ""
            }

            try {
                $hardwareIds = @((Get-PnpDeviceProperty -InstanceId $port.InstanceId -KeyName 'DEVPKEY_Device_HardwareIds' -ErrorAction SilentlyContinue).Data)
            }
            catch {
                $hardwareIds = @()
            }
        }

        $serial = $null
        if ($serialByInstanceId.ContainsKey($port.InstanceId)) {
            $serial = $serialByInstanceId[$port.InstanceId]
        }

        $result += [pscustomobject]@{
            InstanceId   = [string]$port.InstanceId
            COMPort      = $comPort
            FriendlyName = $friendly
            Status       = [string]$port.Status
            Manufacturer = if ([string]::IsNullOrWhiteSpace($manufacturer)) { [string](Get-ComOptionalPropertyValue -Object $serial -Name "Manufacturer") } else { $manufacturer }
            Description  = if ($null -ne $serial) { [string](Get-ComOptionalPropertyValue -Object $serial -Name "Description") } else { "" }
            Service      = if ($null -ne $serial) { [string](Get-ComOptionalPropertyValue -Object $serial -Name "Service") } else { "" }
            HardwareIds  = $hardwareIds
        }
    }

    return @($result | Sort-Object COMPort, FriendlyName)
}

function Show-ComPorts {
    param(
        [array]$Snapshot,
        [string]$Title
    )

    Write-Info $Title
    $snapshotItems = @($Snapshot)
    if ($snapshotItems.Count -eq 0) {
        Write-Host "  (No active COM/Ports devices found.)"
        return
    }

    foreach ($d in $snapshotItems) {
        $comValue = [string](Get-ComOptionalPropertyValue -Object $d -Name "COMPort")
        $comText = "(none)"
        if (-not [string]::IsNullOrWhiteSpace($comValue)) {
            $comText = $comValue
        }

        Write-Host "------------------------------------------------------------"
        Write-Host ("COM Port      : {0}" -f $comText)
        Write-Host ("Friendly Name : {0}" -f [string](Get-ComOptionalPropertyValue -Object $d -Name "FriendlyName"))
        Write-Host ("Status        : {0}" -f [string](Get-ComOptionalPropertyValue -Object $d -Name "Status"))
        $manufacturerValue = [string](Get-ComOptionalPropertyValue -Object $d -Name "Manufacturer")
        if (-not [string]::IsNullOrWhiteSpace($manufacturerValue)) {
            Write-Host ("Manufacturer  : {0}" -f $manufacturerValue)
        }
        $descriptionValue = [string](Get-ComOptionalPropertyValue -Object $d -Name "Description")
        if (-not [string]::IsNullOrWhiteSpace($descriptionValue)) {
            Write-Host ("Description   : {0}" -f $descriptionValue)
        }
        $serviceValue = [string](Get-ComOptionalPropertyValue -Object $d -Name "Service")
        if (-not [string]::IsNullOrWhiteSpace($serviceValue)) {
            Write-Host ("Service       : {0}" -f $serviceValue)
        }
        Write-Host ("Instance ID   : {0}" -f [string](Get-ComOptionalPropertyValue -Object $d -Name "InstanceId"))
        $hardwareIds = @(Get-ComOptionalPropertyValue -Object $d -Name "HardwareIds" -Default @())
        if ($hardwareIds.Count -gt 0) {
            Write-Host ("Hardware IDs  : {0}" -f ($hardwareIds -join '; '))
        }
    }
    Write-Host "------------------------------------------------------------"
}

function Select-DetectedComDevice {
    param([array]$Candidates)

    $candidateItems = @($Candidates)
    if ($candidateItems.Count -eq 1) {
        return $candidateItems[0]
    }

    while ($true) {
        Write-Info "Multiple candidate COM devices found. Select the GPS/PPS device:"
        for ($i = 0; $i -lt $candidateItems.Count; $i++) {
            $c = $candidateItems[$i]
            $comValue = [string](Get-ComOptionalPropertyValue -Object $c -Name "COMPort")
            $comText = if ([string]::IsNullOrWhiteSpace($comValue)) { "(no COM tag)" } else { $comValue }
            Write-Host ("  {0}) {1}  [{2}]" -f ($i + 1), $c.FriendlyName, $comText)
        }

        $raw = Read-Host "Enter a number"
        if ($raw -match '^\d+$') {
            $n = [int]$raw
            if ($n -ge 1 -and $n -le $candidateItems.Count) {
                return $candidateItems[$n - 1]
            }
        }

        Write-WarnMsg "Invalid selection."
    }
}

function Find-GpsComPortInteractive {
    Write-Step "COM detection"
    Write-Host "Disconnect the GPS receiver/GPS PPS device before starting." -ForegroundColor Yellow

    while (-not (Read-YesNo -Prompt "Is the GPS/PPS device currently disconnected?" -DefaultYes $true)) {
        Write-WarnMsg "Please disconnect the device before continuing."
    }

    $baseline = Get-ComPortSnapshot
    Show-ComPorts -Snapshot $baseline -Title "Baseline active COM/Ports devices (device disconnected):"

    Write-Host ""
    Write-Host "Now plug in the GPS receiver or GPS PPS device." -ForegroundColor Yellow
    while (-not (Read-YesNo -Prompt "Has the GPS/PPS device been connected now?" -DefaultYes $true)) {
        Write-WarnMsg "Connect the device, then answer 'y' to continue."
    }

    Start-Sleep -Seconds 2
    $after = Get-ComPortSnapshot
    Show-ComPorts -Snapshot $after -Title "Active COM/Ports devices after connecting GPS/PPS device:"

    $newDevices = @()
    $baselineIds = @($baseline | ForEach-Object { $_.InstanceId })
    foreach ($d in $after) {
        if ($baselineIds -notcontains $d.InstanceId) {
            $newDevices += $d
        }
    }

    if ($newDevices.Count -eq 0) {
        Write-WarnMsg "No newly detected COM/Ports device found."
        Write-WarnMsg "Select the GPS/PPS device manually from current list."
        if ($after.Count -eq 0) {
            throw "No active COM/Ports devices available to select."
        }
        $newDevices = $after
    }

    $selected = Select-DetectedComDevice -Candidates $newDevices
    $selectedComText = "(not detected)"
    if (-not [string]::IsNullOrWhiteSpace($selected.COMPort)) {
        $selectedComText = $selected.COMPort
    }

    Write-Host ""
    Write-Info "Selected device candidate:"
    Write-Host ("  Friendly Name: {0}" -f $selected.FriendlyName)
    Write-Host ("  COM Port     : {0}" -f $selectedComText)
    Write-Host ("  Instance ID  : {0}" -f $selected.InstanceId)

    if (-not (Read-YesNo -Prompt "Is this the GPS/PPS device?" -DefaultYes $true)) {
        throw "User did not confirm selected device."
    }

    if ([string]::IsNullOrWhiteSpace($selected.COMPort)) {
        throw "Selected device does not expose a COMx name."
    }

    if ($selected.COMPort -notmatch '^COM(\d+)$') {
        throw "Unexpected COM port format: $($selected.COMPort)"
    }

    $comNumber = [int]$matches[1]
    Write-Ok ("Detected GPS/PPS COM port: {0} (number {1})" -f $selected.COMPort, $comNumber)
    return $comNumber
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
$templatePath = Join-Path $projectRoot "config\ntp.conf.template"

$countryConfigPath = Join-Path $projectRoot "config\ntp-country-servers.json"
$nationalUtcPath = Join-Path $projectRoot "resources\national_utc_ntp_servers.json"
$poolZonesPath = Join-Path $projectRoot "resources\ntp_pool_zones.json"

$CountryConfigRemoteUrl = "https://raw.githubusercontent.com/labstercam/occultation-tools/main/gps-timing-analysis/config/ntp-country-servers.json"
$PoolZonesRemoteUrl = "https://raw.githubusercontent.com/labstercam/occultation-tools/main/gps-timing-analysis/resources/ntp_pool_zones.json"
$NationalUtcRemoteUrl = "https://raw.githubusercontent.com/labstercam/occultation-tools/main/gps-timing-analysis/resources/national_utc_ntp_servers.json"

$script:CountryConfigRemoteUrl = $CountryConfigRemoteUrl
$script:PoolZonesRemoteUrl = $PoolZonesRemoteUrl
$script:NationalUtcRemoteUrl = $NationalUtcRemoteUrl

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

    Write-Step "Welcome to the NTP Installer"
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

    if (Confirm-Step -Title "Step 1: Install Meinberg NTP and prepare logging" -Details @(
            "Downloads and installs Meinberg NTP.",
            "NTP internet server selection is done in a later step.",
            "Install using default. Do not add any predefined servers. They will be added later in Step 4.",
            ("Installer URL: {0}" -f $meinbergInstallerUrl),
            ("Install root: {0}" -f $installRoot),
            ("Config file: {0}" -f $ntpConfPath),
            ("Log folder: {0}" -f $statsDir),
            ("Advanced (automatic if PPS is enabled): registry value {0}\\PPSProviders" -f $ppsRegistryPath)
        )) {

        Write-WarnMsg "Install using default. Do not add any predefined servers. They will be added later in Step 4."

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

    if (Confirm-Step -Title "Step 2: Install NTP Time Server Monitor" -Details @(
            "Downloads and installs NTP Time Server Monitor.",
            "Use this tool later to verify lock, offsets, and source selection.",
            ("Installer URL: {0}" -f $ntpMonitorInstallerUrl),
            "No official checksum URL is currently configured in this script."
        )) {

        $monitorInstallerPath = Join-Path $downloadDir "ntp_monitor_installer.exe"
        Invoke-InstallerDownload -Url $ntpMonitorInstallerUrl -OutputPath $monitorInstallerPath -Label "NTP Time Server Monitor"
        Install-Exe -InstallerPath $monitorInstallerPath -Arguments $ntpMonitorInstallerArgs -Label "NTP Time Server Monitor"
    }

    if (Confirm-Step -Title "Step 3: Optional GPS/PPS source setup" -Details @(
            "Optionally auto-detect COM port with built-in detection.",
            "Can configure either PPS+NMEA (GPS PPS) or NMEA-only receiver mode.",
            "Writes GPS server/fudge lines to ntp.conf.",
            ("ntp.conf target: {0}" -f $ntpConfPath),
            ("PPS provider DLL path (automatic if PPS mode is selected): {0}" -f $ppsDllPath),
            "No manual registry editing is required for normal setup.",
            ("Advanced detail: PPS mode updates {0}\\PPSProviders automatically" -f $ppsRegistryPath)
        )) {

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

        if (Read-YesNo -Prompt "Run built-in COM port detection now?" -DefaultYes $true) {
            $selectedComPort = Find-GpsComPortInteractive
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
            Write-WarnMsg "ntp.conf not found yet. GPS lines will be applied after Step 4 completes."
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
        Write-Step "GPS reminder"
        Write-WarnMsg "GPS parameters may still require tuning for your hardware and serial settings."
        Write-Info "Test behavior in NTP Time Server Monitor and refer to project documentation when available."
    }

    if (Confirm-Step -Title "Step 4: Configure internet NTP servers by country" -Details @(
            "Uses guided installer built-in country logic.",
            "Country profiles in ntp-country-servers.json are curated.",
            "Other countries use pool logic and may include national UTC inventory data.",
            ("Template: {0}" -f $templatePath),
            ("Country config: {0}" -f $countryConfigPath),
            ("National UTC metadata: {0}" -f $nationalUtcPath),
            ("Pool zones metadata: {0}" -f $poolZonesPath),
            ("Target config file: {0}" -f $ntpConfPath)
        )) {

        $countryChoice = Read-CountrySelection
        $selectedCountry = [string]$countryChoice.Country
        $selectedOtherCode = [string]$countryChoice.OtherCode

        $servers = Resolve-ServersForCountry -CountryCode $selectedCountry -ConfigPath $countryConfigPath -NationalUtcPath $nationalUtcPath -PoolZonesPath $poolZonesPath -OtherCc $selectedOtherCode
        Update-NtpManagedSectionsFromTemplate -TemplatePath $templatePath -Servers $servers -Port $selectedComPort -Mode $selectedGpsMode -StatsFolder $statsDir -OutputPath $ntpConfPath
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

    Wait-BeforeCloseIfNeeded
}
