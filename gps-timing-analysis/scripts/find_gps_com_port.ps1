[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Write-Info([string]$Message) { Write-Host "[INFO] $Message" -ForegroundColor Cyan }
function Write-WarnMsg([string]$Message) { Write-Host "[WARN] $Message" -ForegroundColor Yellow }
function Write-Ok([string]$Message) { Write-Host "[ OK ] $Message" -ForegroundColor Green }

function Get-OptionalPropertyValue {
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

    # If PnP cmdlets are unavailable, synthesize port entries from Win32_SerialPort.
    if ($ports.Count -eq 0) {
        foreach ($serial in $serialRecords) {
            $friendly = [string](Get-OptionalPropertyValue -Object $serial -Name "Name")
            $comPort = [string](Get-OptionalPropertyValue -Object $serial -Name "DeviceID")
            if ([string]::IsNullOrWhiteSpace($comPort) -and $friendly -match '\((COM\d+)\)') {
                $comPort = $matches[1]
            }

            $ports += [pscustomobject]@{
                InstanceId   = [string](Get-OptionalPropertyValue -Object $serial -Name "PNPDeviceID")
                FriendlyName = $friendly
                Status       = [string](Get-OptionalPropertyValue -Object $serial -Name "Status")
                Manufacturer = [string](Get-OptionalPropertyValue -Object $serial -Name "Manufacturer")
                Description  = [string](Get-OptionalPropertyValue -Object $serial -Name "Description")
                Service      = [string](Get-OptionalPropertyValue -Object $serial -Name "Service")
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
            Manufacturer = if ([string]::IsNullOrWhiteSpace($manufacturer)) { [string](Get-OptionalPropertyValue -Object $serial -Name "Manufacturer") } else { $manufacturer }
            Description  = if ($null -ne $serial) { [string](Get-OptionalPropertyValue -Object $serial -Name "Description") } else { "" }
            Service      = if ($null -ne $serial) { [string](Get-OptionalPropertyValue -Object $serial -Name "Service") } else { "" }
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
        $comValue = [string](Get-OptionalPropertyValue -Object $d -Name "COMPort")
        $comText = "(none)"
        if (-not [string]::IsNullOrWhiteSpace($comValue)) {
            $comText = $comValue
        }

        Write-Host "------------------------------------------------------------"
        Write-Host ("COM Port      : {0}" -f $comText)
        Write-Host ("Friendly Name : {0}" -f [string](Get-OptionalPropertyValue -Object $d -Name "FriendlyName"))
        Write-Host ("Status        : {0}" -f [string](Get-OptionalPropertyValue -Object $d -Name "Status"))
        $manufacturerValue = [string](Get-OptionalPropertyValue -Object $d -Name "Manufacturer")
        if (-not [string]::IsNullOrWhiteSpace($manufacturerValue)) {
            Write-Host ("Manufacturer  : {0}" -f $manufacturerValue)
        }
        $descriptionValue = [string](Get-OptionalPropertyValue -Object $d -Name "Description")
        if (-not [string]::IsNullOrWhiteSpace($descriptionValue)) {
            Write-Host ("Description   : {0}" -f $descriptionValue)
        }
        $serviceValue = [string](Get-OptionalPropertyValue -Object $d -Name "Service")
        if (-not [string]::IsNullOrWhiteSpace($serviceValue)) {
            Write-Host ("Service       : {0}" -f $serviceValue)
        }
        Write-Host ("Instance ID   : {0}" -f [string](Get-OptionalPropertyValue -Object $d -Name "InstanceId"))
        $hardwareIds = @(Get-OptionalPropertyValue -Object $d -Name "HardwareIds" -Default @())
        if ($hardwareIds.Count -gt 0) {
            Write-Host ("Hardware IDs  : {0}" -f ($hardwareIds -join '; '))
        }
    }
    Write-Host "------------------------------------------------------------"
}

function Select-DetectedDevice {
    param([array]$Candidates)

    $candidateItems = @($Candidates)
    if ($candidateItems.Count -eq 1) {
        return $candidateItems[0]
    }

    while ($true) {
        Write-Info "Multiple candidate COM devices found. Select the GPS/PPS device:"
        for ($i = 0; $i -lt $candidateItems.Count; $i++) {
            $c = $candidateItems[$i]
            $comValue = [string](Get-OptionalPropertyValue -Object $c -Name "COMPort")
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

function Invoke-Main {
    Write-Host "GPS/PPS COM Port Identification Helper" -ForegroundColor Green
    Write-Host ""
    Write-Host "Important: Disconnect the GPS receiver/GPS PPS device before starting." -ForegroundColor Yellow

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

    # Give Windows a moment to enumerate the new device.
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

    $selected = Select-DetectedDevice -Candidates $newDevices
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
        throw "User did not confirm selected device. Re-run and select the correct device."
    }

    if ([string]::IsNullOrWhiteSpace($selected.COMPort)) {
        throw "Selected device does not expose a COMx name. Cannot return COM port number."
    }

    if ($selected.COMPort -notmatch '^COM(\d+)$') {
        throw "Unexpected COM port format: $($selected.COMPort)"
    }

    $comNumber = [int]$matches[1]
    Write-Ok ("Detected GPS/PPS COM port: {0} (number {1})" -f $selected.COMPort, $comNumber)
    Write-Host ("Use this in setup script as: -ComPort {0}" -f $comNumber) -ForegroundColor Cyan

    # Emit machine-friendly output for chaining in scripts.
    Write-Output $comNumber
}

try {
    Invoke-Main
}
catch {
    Write-Host "" 
    Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "" 
    Write-Host "Tip: Run from an existing terminal to keep messages visible:" -ForegroundColor Yellow
    Write-Host "  .\scripts\find_gps_com_port.ps1" -ForegroundColor Yellow

    # Keep a standalone PowerShell window open so the user can read the error.
    if ($Host.Name -eq 'ConsoleHost') {
        try {
            [void](Read-Host "Press Enter to close")
        }
        catch {
            # Ignore secondary prompt errors.
        }
    }

    throw
}
