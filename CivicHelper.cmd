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

echo Python ontbreekt of PyQt6 is niet geinstalleerd.
pause
exit /b 1
