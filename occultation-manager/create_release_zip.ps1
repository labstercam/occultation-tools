# Create release ZIP for Occultation Manager v0.2.0

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
    # Excel report templates
    "python\NorthAmerica_AstReportForm_V5.6.12r_Template.xlsx",
    "python\RASNZ_AstReporttForm_V4.1.2.G_Template.xlsx",
    # Icon
    "python\moon_icon_178489.ico",
    # Documentation
    "python\ReadMe.md",
    "ReadMe.md",
    "RELEASE_NOTES.md"
)

$version = "0.2.0"
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

# Copy files to temp directory
foreach ($file in $files) {
    if (Test-Path $file) {
        $destination = Join-Path $targetDir (Split-Path $file -Leaf)
        Copy-Item $file $destination -Force
        Write-Host "  Copied: $file" -ForegroundColor Gray
    } else {
        Write-Host "  WARNING: File not found: $file" -ForegroundColor Yellow
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
    foreach ($file in $files) {
        $fileName = Split-Path $file -Leaf
        Write-Host "    $fileName" -ForegroundColor Gray
    }
} else {
    Write-Host "`nERROR: Failed to create zip file" -ForegroundColor Red
}
