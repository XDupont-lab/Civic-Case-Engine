@echo off
setlocal
chcp 65001 >nul
title Civic Helper - Schone-Machine Reconstructietest
cd /d "%~dp0"

set PY=python
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe

echo =======================================================================
echo     CIVIC HELPER — SCHONE-MACHINE RECONSTRUCTIE- ^& HERSTELTEST
echo       (7 Harde Eisen voor Installatieveiligheid en Rampenherstel)
echo =======================================================================
echo.

"%PY%" _engine\test_reconstructie_schone_machine.py
set RET=%ERRORLEVEL%

echo.
if %RET% equ 0 (
    echo [+] RECONSTRUCTIE-POORT OPEN: De volledige installatie- en herstelketen is veilig.
) else (
    echo [!] RECONSTRUCTIE-POORT GESLOTEN: Minstens een scenario faalt.
)

endlocal & exit /b %RET%
