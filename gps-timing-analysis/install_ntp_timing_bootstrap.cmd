@echo off
setlocal

set "REPO_OWNER=labstercam"
set "REPO_NAME=occultation-tools"
set "REPO_BRANCH=main"
set "SUBDIR=gps-timing-analysis"
set "INSTALL_ROOT=%SystemDrive%\OccultationTools\gps-timing-analysis"
set "ELEVATED_FLAG=%~1"

set "BASE_URL=https://raw.githubusercontent.com/%REPO_OWNER%/%REPO_NAME%/%REPO_BRANCH%/%SUBDIR%"

echo.
echo Occultation Tools - NTP Guided Setup Bootstrap
echo ----------------------------------------------
echo This will download/update installer files to:
echo   %INSTALL_ROOT%
echo.

choice /C YN /N /M "Continue? [Y/N]: "
if errorlevel 2 (
	echo Cancelled.
	exit /b 0
)

rem Ensure admin context; if not elevated, relaunch this CMD via UAC once.
powershell.exe -NoProfile -Command "$p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent()); if ($p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { exit 0 } else { exit 1 }"
if not "%ERRORLEVEL%"=="0" (
	if /I "%ELEVATED_FLAG%"=="--elevated" (
		echo [ERROR] Could not obtain Administrator rights.
		echo Please right-click this file and choose "Run as administrator".
		pause
		exit /b 1
	)

	echo Requesting Administrator rights...
	powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -Verb RunAs -FilePath '%ComSpec%' -ArgumentList '/c """%~f0"" --elevated'"
	exit /b %ERRORLEVEL%
)

call :EnsureDir "%INSTALL_ROOT%"
call :EnsureDir "%INSTALL_ROOT%\scripts"
call :EnsureDir "%INSTALL_ROOT%\config"
call :EnsureDir "%INSTALL_ROOT%\resources"
call :EnsureDir "%INSTALL_ROOT%\logs"

echo.
echo Downloading setup files...
call :Download "scripts/install_ntp_timing_guided.ps1"
if errorlevel 1 goto :download_fail
call :Download "scripts/install_ntp_timing_guided.cmd"
if errorlevel 1 goto :download_fail
call :Download "config/ntp.conf.template"
if errorlevel 1 goto :download_fail
call :Download "config/ntp-country-servers.json"
if errorlevel 1 goto :download_fail
call :Download "resources/ntp_pool_zones.json"
if errorlevel 1 goto :download_fail
call :Download "resources/national_utc_ntp_servers.json"
if errorlevel 1 goto :download_fail

echo.
echo Starting guided installer...
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%INSTALL_ROOT%\scripts\install_ntp_timing_guided.ps1"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
	echo.
	echo [ERROR] Guided installer exited with code %EXIT_CODE%.
	echo Logs are under:
	echo   %INSTALL_ROOT%\logs
	pause
)

exit /b %EXIT_CODE%

:download_fail
echo.
echo [ERROR] Download failed. Check internet access and try again.
echo If GitHub is blocked on your network, download the full project ZIP instead.
pause
exit /b 1

:EnsureDir
if not exist "%~1" mkdir "%~1"
exit /b 0

:Download
set "REL=%~1"
set "REL_WIN=%REL:/=\%"
set "SRC=%BASE_URL%/%REL%"
set "DST=%INSTALL_ROOT%\%REL_WIN%"

echo   %REL%
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri '%SRC%' -OutFile '%DST%'"
if not "%ERRORLEVEL%"=="0" exit /b 1

exit /b 0
