@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PS_SCRIPT=%SCRIPT_DIR%install_ntp_timing_guided.ps1"

if not exist "%PS_SCRIPT%" (
  echo [ERROR] Could not find PowerShell script:
  echo   %PS_SCRIPT%
  echo.
  pause
  exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%PS_SCRIPT%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
  echo.
  echo [ERROR] Guided installer exited with code %EXIT_CODE%.
  echo If it failed before opening, try running this CMD launcher as Administrator.
  pause
)

exit /b %EXIT_CODE%
