@echo off
title Civic Case Engine -- Procesdossier Bundler
cd /d "%~dp0"

echo =======================================================================
echo          CIVIC LEGAL KERNEL — PROCESDOSSIER BUNDLER & EXPORTER
echo =======================================================================
echo.
echo Deze module bundelt alle dossierstukken, de forensische chronologie,
echo de actieve doctrine en genummerde producties (met SHA-256 integriteits-
echo controle) tot een complete, verifieerbare procesbundel (.md en .html).
echo.
echo [1] Standaardbundel genereren (Wmo Maatwerk & Zorgcontinuiteit)
echo [2] Aangepaste bundel genereren (Zelf zaakstitel en partijen invoeren)
echo [3] Annuleren
echo.
set /p choice="Selecteer een optie (1-3): "

if "%choice%"=="1" (
    echo.
    echo [*] Genereren van standaard procesbundel...
    python _engine\case_bundler.py --title "Wmo Maatwerk & Zorgcontinuiteit Voorbeeldzaak" --author "Voorbeeld Burger" --respondent "College van B&W Voorbeeldgemeente"
    goto klaar
)

if "%choice%"=="2" (
    echo.
    set /p ztitel="Voer zaakstitel in: "
    set /p zindiener="Voer naam indiener in: "
    set /p zweder="Voer naam wederpartij in: "
    echo.
    echo [*] Genereren van aangepaste procesbundel...
    python _engine\case_bundler.py --title "%ztitel%" --author "%zindiener%" --respondent "%zweder%"
    goto klaar
)

if "%choice%"=="3" (
    goto einde
)

:klaar
echo.
echo [✓] Procesbundel gereed in de map Dossier/.
echo Wil je de map openen in Verkenner?
set /p open_exp="Open map (j/n)? "
if /i "%open_exp%"=="j" explorer Dossier

:einde
pause
