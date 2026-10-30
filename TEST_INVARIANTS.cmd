@echo off
setlocal enabledelayedexpansion
title Civic Helper - Een poort, alle invarianten
cd /d "%~dp0"

set PY=python
if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" set PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe

echo =======================================================================
echo     CIVIC HELPER - POORT: ALLE INVARIANTEN IN EEN RUN
echo =======================================================================
echo.

set FAILED=0
set RAN=0

for %%F in (_engine\test_*.py Ketengrootboek\test_*.py) do (
    set /a RAN+=1
    echo [test] %%F
    "%PY%" "%%F"
    if errorlevel 1 (
        echo   ^>^>^> FAALT: %%F
        set FAILED=1
    ) else (
        echo   ok
    )
    echo.
)

echo =======================================================================
if "%FAILED%"=="1" (
    echo   POORT GESLOTEN - minstens een invariant is geschonden.
    echo =======================================================================
    endlocal & exit /b 1
)
echo   POORT OPEN - %RAN% testbestanden, alle groen.
echo =======================================================================
endlocal & exit /b 0
