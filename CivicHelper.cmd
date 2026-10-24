@echo off
cd /d "%~dp0"

rem 1. Probeer de moderne Multi-Agent Tafelvenster (Civic Helper 0.3)
if exist "%~dp0gui\tafel_gui.py" (
    where pythonw >nul 2>&1 && start "" pythonw "%~dp0gui\tafel_gui.py" && exit /b 0
    where py >nul 2>&1 && start "" py -3 "%~dp0gui\tafel_gui.py" && exit /b 0
    where python >nul 2>&1 && start "" python "%~dp0gui\tafel_gui.py" && exit /b 0
)

rem 2. Terugvaloptie: Klassiek navigatievenster
if exist "%~dp0hulp\venster.py" (
    where pythonw >nul 2>&1 && start "" pythonw "%~dp0hulp\venster.py" && exit /b 0
    where py >nul 2>&1 && start "" py -3 "%~dp0hulp\venster.py" && exit /b 0
    where python >nul 2>&1 && start "" python "%~dp0hulp\venster.py" && exit /b 0
)

echo Python ontbreekt of PyQt6 is niet geinstalleerd.
echo Installeer Python 3 en PyQt6 ('pip install PyQt6') en start opnieuw.
pause
exit /b 1
