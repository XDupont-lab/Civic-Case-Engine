@echo off
setlocal EnableDelayedExpansion
chcp 65001 >nul
title Civic Case Engine - Volledige Zelf-Inrichting (Setup All)
cd /d "%~dp0"

echo =======================================================================
echo          CIVIC CASE ENGINE — COMPLETE WERKOMGEVING SETUP
echo =======================================================================
echo.
echo Dit script richt de volledige autonome werkomgeving voor je in:
echo   1. Controle en installatie van Python 3 ^& Git (via Winget indien nodig)
echo   2. Aanmaken van de virtuele AI-omgeving (.venv_bu)
echo   3. Installatie van AI Browser Agent (Chromium + browser-use)
echo   4. Mappenstructuur, sjablonen en bureaublad-starters
echo   5. Juridische Onboarding Wizard (bootstrap.py)
echo.

:: 1. Controleer of Python aanwezig is
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [*] Python is nog niet geinstalleerd op dit systeem.
    echo [*] Bezig met automatische installatie via Windows Package Manager (winget)...
    winget install --id Python.Python.3.12 -e --accept-source-agreements --accept-package-agreements
    if %ERRORLEVEL% neq 0 (
        echo [!] Automatische installatie via winget mislukt.
        echo [!] Download en installeer Python 3 handmatig van https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo [+] Python succesvol geinstalleerd! Herstart dit venster indien nodig.
)

:: 2. Controleer of Git aanwezig is
where git >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [*] Git is nog niet geinstalleerd.
    echo [*] Bezig met automatische installatie via winget...
    winget install --id Git.Git -e --accept-source-agreements --accept-package-agreements
)

:: 3. Voer het Python setup script uit
echo.
echo [*] Starten van de autonome omgevingsinrichter (setup_environment.py)...
python setup_environment.py

echo.
pause
