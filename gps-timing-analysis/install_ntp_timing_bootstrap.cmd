@echo off
setlocal

set "NO_PAUSE=0"
set "BOOTSTRAP_LOG=%TEMP%\occultation_bootstrap.log"
set "REPO_OWNER=labstercam"
set "REPO_NAME=occultation-tools"
set "REPO_BRANCH=main"
set "SUBDIR=gps-timing-analysis"
set "INSTALL_ROOT=%SystemDrive%\OccultationTools\gps-timing-analysis"
set "ELEVATED_FLAG="

if /I "%~1"=="--elevated" set "ELEVATED_FLAG=--elevated"
if /I "%~1"=="--no-pause" set "NO_PAUSE=1"
if /I "%~2"=="--no-pause" set "NO_PAUSE=1"

set "BASE_URL=https://raw.githubusercontent.com/%REPO_OWNER%/%REPO_NAME%/%REPO_BRANCH%/%SUBDIR%"

echo [%DATE% %TIME%] bootstrap launch >> "%BOOTSTRAP_LOG%"
echo [%DATE% %TIME%] script path: %~f0 >> "%BOOTSTRAP_LOG%"

echo.
echo Occultation Tools - NTP Guided Setup Bootstrap
echo ----------------------------------------------
echo This will download/update installer files to:
echo   %INSTALL_ROOT%
echo.
echo Press Y to continue or N to cancel.

set "USER_REPLY="
set /P "USER_REPLY=Continue setup now? [Y/N]: "
if /I "%USER_REPLY%"=="N" (
	echo Cancelled.
	echo [%DATE% %TIME%] user cancelled at prompt >> "%BOOTSTRAP_LOG%"
	set "EXIT_CODE=0"
	goto :finish
)
if /I not "%USER_REPLY%"=="Y" (
	echo Invalid choice. Please run again and enter Y or N.
	echo [%DATE% %TIME%] invalid user reply: %USER_REPLY% >> "%BOOTSTRAP_LOG%"
	set "EXIT_CODE=1"
	goto :finish
)

echo [%DATE% %TIME%] continuing after prompt >> "%BOOTSTRAP_LOG%"


rem Ensure admin context; if not elevated, relaunch this CMD via UAC once.
powershell.exe -NoProfile -Command "$p = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent()); if ($p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { exit 0 } else { exit 1 }"
if not "%ERRORLEVEL%"=="0" (
	if /I "%ELEVATED_FLAG%"=="--elevated" (
		echo [ERROR] Could not obtain Administrator rights.
		echo Please right-click this file and choose "Run as administrator".
		echo [%DATE% %TIME%] elevation failed in elevated rerun >> "%BOOTSTRAP_LOG%"
		set "EXIT_CODE=1"
		goto :finish
	)

	echo Requesting Administrator rights...
	echo [%DATE% %TIME%] requesting elevation >> "%BOOTSTRAP_LOG%"
	powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -Verb RunAs -FilePath '%~f0' -ArgumentList '--elevated'"
	set "EXIT_CODE=%ERRORLEVEL%"
	goto :finish
)

echo [%DATE% %TIME%] already elevated or elevation successful >> "%BOOTSTRAP_LOG%"

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
echo [%DATE% %TIME%] launching guided installer >> "%BOOTSTRAP_LOG%"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%INSTALL_ROOT%\scripts\install_ntp_timing_guided.ps1"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
	echo.
	echo [ERROR] Guided installer exited with code %EXIT_CODE%.
	echo Logs are under:
	echo   %INSTALL_ROOT%\logs
)

goto :finish

:download_fail
echo.
echo [ERROR] Download failed. Check internet access and try again.
echo If GitHub is blocked on your network, download the full project ZIP instead.
echo [%DATE% %TIME%] download failed >> "%BOOTSTRAP_LOG%"
set "EXIT_CODE=1"
goto :finish

:EnsureDir
if not exist "%~1" mkdir "%~1"
exit /b 0

:Download
set "REL=%~1"
set "REL_WIN=%REL:/=\%"
set "SRC=%BASE_URL%/%REL%?ts=%RANDOM%%RANDOM%"
set "DST=%INSTALL_ROOT%\%REL_WIN%"

echo   %REL%
powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop'; [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing -Uri '%SRC%' -OutFile '%DST%'"
if not "%ERRORLEVEL%"=="0" exit /b 1

echo [%DATE% %TIME%] downloaded %REL% >> "%BOOTSTRAP_LOG%"

exit /b 0

:finish
if "%EXIT_CODE%"=="" set "EXIT_CODE=0"
echo [%DATE% %TIME%] exit code %EXIT_CODE% >> "%BOOTSTRAP_LOG%"
echo Diagnostic log: %BOOTSTRAP_LOG%
if not "%NO_PAUSE%"=="1" (
	echo.
	echo Press any key to close this window...
	pause >nul
)
exit /b %EXIT_CODE%
