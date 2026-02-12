# Clear Python bytecode cache files
# Run this if changes to .py files aren't being picked up

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Clearing Python cache files..." -ForegroundColor Cyan

# Remove __pycache__ directories
Get-ChildItem -Path $scriptDir -Recurse -Directory -Filter "__pycache__" | ForEach-Object {
    Write-Host "  Removing: $($_.FullName)" -ForegroundColor Yellow
    Remove-Item $_.FullName -Recurse -Force
}

# Remove .pyc files
Get-ChildItem -Path $scriptDir -Recurse -Filter "*.pyc" | ForEach-Object {
    Write-Host "  Removing: $($_.FullName)" -ForegroundColor Yellow
    Remove-Item $_.FullName -Force
}

Write-Host "`nDone! Python cache cleared." -ForegroundColor Green
Write-Host "Please restart SharpCap for changes to take effect." -ForegroundColor Cyan
