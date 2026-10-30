@echo off
cd /d "%~dp0"

rem Start Civic Helper 0.3 — Tafelvenster (primair vanuit gui\tafel_gui.py)
if exist "%~dp0gui\tafel_gui.py" (
    where pythonw >nul 2>&1 && start "" pythonw "%~dp0gui\tafel_gui.py" %* && exit /b 0
    where py >nul 2>&1 && start "" py -3 "%~dp0gui\tafel_gui.py" %* && exit /b 0
    where python >nul 2>&1 && start "" python "%~dp0gui\tafel_gui.py" %* && exit /b 0
)

if exist "%~dp0..\Shared_Tools\tafel_gui.py" (
    where pythonw >nul 2>&1 && start "" pythonw "%~dp0..\Shared_Tools\tafel_gui.py" %* && exit /b 0
    where python >nul 2>&1 && start "" python "%~dp0..\Shared_Tools\tafel_gui.py" %* && exit /b 0
)

echo.
echo =======================================================================
echo  [!] Python of PyQt6 is nog niet aangetroffen op deze computer.
echo  [*] Wil je de 2-Stages Instap starten om alles automatisch in te richten?
echo =======================================================================
echo.
choice /C JN /M "Druk op J voor de Automatische Instap, of N om af te sluiten"
if errorlevel 2 exit /b 1

if exist "%~dp0INSTAP_WINDOWS.cmd" (
    call "%~dp0INSTAP_WINDOWS.cmd" %*
    exit /b %ERRORLEVEL%
)

echo Kon INSTAP_WINDOWS.cmd niet vinden.
pause
exit /b 1
