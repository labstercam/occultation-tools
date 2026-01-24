# Create release ZIP for Occultation Manager v0.2.0-beta.1

$files = @(
    # Python files
    "python\aota_dialogs.py",
    "python\aota_parser.py",
    "python\aota_report_parser.py",
    "python\comprehensive_report_dialog.py",
    "python\config.py",
    "python\equipment_dialogs.py",
    "python\events.py",
    "python\file_selection_dialog.py",
    "python\gui_components.py",
    "python\gui_dialogs.py",
    "python\help.py",
    "python\light_curves_iron.py",
    "python\main.py",
    "python\main_gui.py",
    "python\na_report.py",
    "python\occult4_export.py",
    "python\report_generator_base.py",
    "python\sequence_runner.py",
    "python\tangra_dialogs.py",
    "python\templates.py",
    "python\theme.py",
    "python\tt_report.py",
    "python\utils.py",
    # SharpCap sequence templates
    "python\SharpCap Minimal Local Time template.txt",
    "python\SharpCap Just Record template.txt",
    "python\SharpCap Sequence Local Time template.txt",
    "python\SharpCap Sequence UTC template.txt",
    "python\SharpCap Test Recording template.txt",
    # Countdown reference file
    "python\countdown python for sequencer.scs",
    # Excel report templates
    "python\NorthAmerica_AstReportForm_V5.6.12r_Template.xlsx",
    "python\RASNZ_AstReporttForm_V4.1.2.G_Template.xlsx",
    # Icon
    "python\moon_icon_178489.ico",
    # Documentation
    "python\ReadMe.md",
    "ReadMe.md",
    "RELEASE_NOTES.md",
    # Folder README files
    "README_files_folder.txt",
    "README_sequences_folder.txt",
    "README_reports_folder.txt"
)

$version = "0.2.0-beta.1"
$zipPath = "occultation-manager-v$version.zip"

Write-Host "Creating $zipPath..." -ForegroundColor Green

if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
    Write-Host "Removed existing zip file" -ForegroundColor Yellow
}

# Create a temporary directory for the zip structure
$tempDir = "temp_release"
$targetDir = "$tempDir\occultation-manager"

if (Test-Path $tempDir) {
    Remove-Item $tempDir -Recurse -Force
}
New-Item -ItemType Directory -Path $targetDir -Force | Out-Null

# Create folder structure
Write-Host "Creating folder structure..." -ForegroundColor Cyan
$filesDir = "$targetDir\files"
$sequencesDir = "$targetDir\sequences"
$reportsDir = "$filesDir\Reports"

New-Item -ItemType Directory -Path $filesDir -Force | Out-Null
New-Item -ItemType Directory -Path $sequencesDir -Force | Out-Null
New-Item -ItemType Directory -Path $reportsDir -Force | Out-Null

Write-Host "  Created: files/" -ForegroundColor Gray
Write-Host "  Created: files/Reports/" -ForegroundColor Gray
Write-Host "  Created: sequences/" -ForegroundColor Gray

# Copy README files to appropriate folders
if (Test-Path "README_files_folder.txt") {
    Copy-Item "README_files_folder.txt" "$filesDir\README.txt" -Force
    Write-Host "  Added README to files/" -ForegroundColor Gray
}
if (Test-Path "README_sequences_folder.txt") {
    Copy-Item "README_sequences_folder.txt" "$sequencesDir\README.txt" -Force
    Write-Host "  Added README to sequences/" -ForegroundColor Gray
}
if (Test-Path "README_reports_folder.txt") {
    Copy-Item "README_reports_folder.txt" "$reportsDir\README.txt" -Force
    Write-Host "  Added README to files/Reports/" -ForegroundColor Gray
}

# Copy files to temp directory
Write-Host "`nCopying application files..." -ForegroundColor Cyan
foreach ($file in $files) {
    if (Test-Path $file) {
        $destination = Join-Path $targetDir (Split-Path $file -Leaf)
        Copy-Item $file $destination -Force
        Write-Host "  Copied: $file" -ForegroundColor Gray
    } else {
        Write-Host "  WARNING: File not found: $file" -ForegroundColor Yellow
    }
}

# Copy template files to files folder as well
Write-Host "`nCopying templates to files folder..." -ForegroundColor Cyan
$templateFiles = @(
    "python\SharpCap Minimal Local Time template.txt",
    "python\SharpCap Just Record template.txt",
    "python\SharpCap Sequence Local Time template.txt",
    "python\SharpCap Sequence UTC template.txt",
    "python\SharpCap Test Recording template.txt"
)

foreach ($template in $templateFiles) {
    if (Test-Path $template) {
        $fileName = Split-Path $template -Leaf
        $destination = Join-Path $filesDir $fileName
        Copy-Item $template $destination -Force
        Write-Host "  Copied: $fileName to files/" -ForegroundColor Gray
    }
}

# Create the zip from the temp directory
Compress-Archive -Path "$tempDir\*" -DestinationPath $zipPath -CompressionLevel Optimal

# Clean up temp directory
Remove-Item $tempDir -Recurse -Force

if (Test-Path $zipPath) {
    $size = (Get-Item $zipPath).Length / 1KB
    Write-Host "`nSuccess! Created $zipPath ($([math]::Round($size, 1)) KB)" -ForegroundColor Green
    Write-Host "`nZip contents:" -ForegroundColor Cyan
    Write-Host "  occultation-manager/" -ForegroundColor Cyan
    Write-Host "    files/" -ForegroundColor Cyan
    Write-Host "      Reports/" -ForegroundColor Cyan
    Write-Host "    sequences/" -ForegroundColor Cyan
    foreach ($file in $files) {
        $fileName = Split-Path $file -Leaf
        if ($fileName -notlike "README_*") {
            Write-Host "    $fileName" -ForegroundColor Gray
        }
    }
} else {
    Write-Host "`nERROR: Failed to create zip file" -ForegroundColor Red
}

Write-Host "`n"
Read-Host "Press Enter to exit"
