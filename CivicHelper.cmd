@echo off
cd /d "%~dp0"
where pythonw >nul 2>&1 && start "" pythonw "%~dp0hulp\venster.py" && exit /b 0
where py >nul 2>&1 && start "" py -3 "%~dp0hulp\venster.py" && exit /b 0
echo Python ontbreekt. Installeer Python 3 en start hulp\venster.py opnieuw.
exit /b 1
