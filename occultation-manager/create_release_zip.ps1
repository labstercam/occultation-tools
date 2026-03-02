# Create release ZIP for Occultation Manager (folder-based layout)

$version = "0.2.0-beta.3"
$zipPath = "occultation-manager-v$version.zip"

Write-Host "Creating $zipPath..." -ForegroundColor Green

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
    Write-Host "Removed existing zip file" -ForegroundColor Yellow
}

# Temporary packaging root
$tempDir = "temp_release"
$targetDir = "$tempDir\occultation-manager"
$targetPrefix = $targetDir + "\"

if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null

# New release structure
$appDir = "$targetDir\app"
$appLibDir = "$appDir\lib"
$resourcesDir = "$targetDir\resources"
$masterRoot = "$resourcesDir\templates_master"
$masterSequencerDir = "$masterRoot\sequencer"
$masterReportsDir = "$masterRoot\reports"
$dataDir = "$targetDir\data"
$dataConfigDir = "$dataDir\config"
$dataEventsDir = "$dataDir\events"
$dataTemplatesDir = "$dataDir\templates"
$dataSequencesDir = "$dataDir\sequences"
$dataReportsDir = "$dataDir\reports"

Write-Host "Creating folder structure..." -ForegroundColor Cyan
@(
    $appDir,
    $appLibDir,
    $masterSequencerDir,
    $masterReportsDir,
    $dataConfigDir,
    $dataEventsDir,
    $dataTemplatesDir,
    $dataSequencesDir,
    $dataReportsDir
) | ForEach-Object {
    New-Item -ItemType Directory -Path $_ -Force | Out-Null
    Write-Host ("  Created: " + $_.Replace($targetPrefix, '')) -ForegroundColor Gray
}

# Files to package into app/
$pythonFiles = @(
    "python\aota_dialogs.py",
    "python\aota_parser.py",
    "python\aota_report_parser.py",
    "python\comprehensive_report_dialog.py",
    "python\config.py",
    "python\dummy_event_generator.py",
    "python\equipment_dialogs.py",
    "python\events.py",
    "python\file_selection_dialog.py",
    "python\gui_components.py",
    "python\gui_dialogs.py",
    "python\help.py",
    "python\light_curves_iron.py",
    "python\main.py",
    "python\main_gui.py",
    "python\na_report_openize.py",
    "python\occult4_export.py",
    "python\report_generator_base.py",
    "python\sequence_runner.py",
    "python\tangra_dialogs.py",
    "python\templates.py",
    "python\theme.py",
    "python\tt_report_openize.py",
    "python\utils.py"
)

# Sequencer template masters
$sequencerMasterFiles = @(
    "python\SharpCap Minimal Local Time template.txt",
    "python\SharpCap Just Record template.txt",
    "python\SharpCap Sequence Local Time template.txt",
    "python\SharpCap Sequence UTC template.txt",
    "python\SharpCap Test Recording template.txt",
    "python\countdown python for sequencer.scs"
)

# Report template masters
$reportMasterFiles = @(
    "python\NorthAmerica_AstReportForm_V5.6.12r.xlsx",
    "python\RASNZ_AstReporttForm_V4.1.2.G.xlsx"
)

# App support files
$appSupportFiles = @(
    "python\moon_icon_178489.ico",
    "python\ReadMe.md"
)

# App lib files
$appLibFiles = @(
    "python\lib\Openize.OpenXMLSDK.dll",
    "python\lib\DocumentFormat.OpenXml.dll",
    "python\lib\DocumentFormat.OpenXml.Framework.dll",
    "python\lib\README.md"
)

function Copy-ExistingFile {
    param(
        [string]$Source,
        [string]$Destination
    )
    if (Test-Path $Source) {
        $destParent = Split-Path $Destination -Parent
        if (-not (Test-Path $destParent)) {
            New-Item -ItemType Directory -Path $destParent -Force | Out-Null
        }
        Copy-Item $Source $Destination -Force
        Write-Host ("  Copied: " + $Source + " -> " + $Destination.Replace($targetPrefix, '')) -ForegroundColor Gray
    } else {
        Write-Host "  WARNING: File not found: $Source" -ForegroundColor Yellow
    }
}

Write-Host "`nCopying application files to app/..." -ForegroundColor Cyan
foreach ($file in $pythonFiles) {
    $dest = Join-Path $appDir (Split-Path $file -Leaf)
    Copy-ExistingFile -Source $file -Destination $dest
}

foreach ($file in $appSupportFiles) {
    $dest = Join-Path $appDir (Split-Path $file -Leaf)
    Copy-ExistingFile -Source $file -Destination $dest
}

Write-Host "`nCopying app lib files to app/lib/..." -ForegroundColor Cyan
foreach ($file in $appLibFiles) {
    $dest = Join-Path $appLibDir (Split-Path $file -Leaf)
    Copy-ExistingFile -Source $file -Destination $dest
}

Write-Host "`nCopying template masters to resources/templates_master/sequencer/..." -ForegroundColor Cyan
foreach ($file in $sequencerMasterFiles) {
    $dest = Join-Path $masterSequencerDir (Split-Path $file -Leaf)
    Copy-ExistingFile -Source $file -Destination $dest
}

Write-Host "`nCopying report template masters to resources/templates_master/reports/..." -ForegroundColor Cyan
foreach ($file in $reportMasterFiles) {
    $dest = Join-Path $masterReportsDir (Split-Path $file -Leaf)
    Copy-ExistingFile -Source $file -Destination $dest
}

# Root docs
Write-Host "`nCopying top-level docs..." -ForegroundColor Cyan
@("ReadMe.md", "RELEASE_NOTES.md", "RELEASE_INSTRUCTIONS.md") | ForEach-Object {
    $dest = Join-Path $targetDir (Split-Path $_ -Leaf)
    Copy-ExistingFile -Source $_ -Destination $dest
}

# Seed data README files for user guidance
if (Test-Path "README_events_folder.txt") {
    Copy-Item "README_events_folder.txt" "$dataEventsDir\README.txt" -Force
}
if (Test-Path "README_sequences_folder.txt") {
    Copy-Item "README_sequences_folder.txt" "$dataSequencesDir\README.txt" -Force
}
if (Test-Path "README_reports_folder.txt") {
    Copy-Item "README_reports_folder.txt" "$dataReportsDir\README.txt" -Force
}

Set-Content -Path "$dataConfigDir\README.txt" -Value "Configuration storage (occultation_config.json)" -Encoding UTF8
Set-Content -Path "$dataTemplatesDir\README.txt" -Value "User-editable working template copies" -Encoding UTF8

# Create zip
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -CompressionLevel Optimal

# Cleanup
Remove-Item $tempDir -Recurse -Force

if (Test-Path $zipPath) {
    $size = (Get-Item $zipPath).Length / 1KB
    Write-Host "`nSuccess! Created $zipPath ($([math]::Round($size, 1)) KB)" -ForegroundColor Green
    Write-Host "`nZip structure:" -ForegroundColor Cyan
    Write-Host "  occultation-manager/app" -ForegroundColor Gray
    Write-Host "  occultation-manager/resources/templates_master/sequencer" -ForegroundColor Gray
    Write-Host "  occultation-manager/resources/templates_master/reports" -ForegroundColor Gray
    Write-Host "  occultation-manager/data/{config,events,templates,sequences,reports}" -ForegroundColor Gray
} else {
    Write-Host "`nERROR: Failed to create zip file" -ForegroundColor Red
}

Write-Host "`n"
Read-Host "Press Enter to exit"
