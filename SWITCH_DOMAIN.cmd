@echo off
title Civic Case Engine -- Switch Domain Doctrine
cd /d "%~dp0"

echo =======================================================================
echo          CIVIC CASE ENGINE — RECHTSDOMEIN SELECTIE (DOMAIN PACKS)
echo =======================================================================
echo.
echo Kies welk juridisch domeinprofiel je wilt activeren:
echo.
echo [1] NL Wmo ^& Sociaal Domein (Compensatieplicht, Socrates, Zorg)
echo [2] UK Housing ^& Equality Act (Housing Act 1996, Equality Act 2010)
echo [3] NL Toeslagen ^& Bestaanszekerheid (Awir, Hardheidsclausule, Beslagvrije voet)
echo [4] NL UWV ^& Arbeidsongeschiktheid (Wet WIA, Ziektewet, FML-weerlegging)
echo [5] NL BRP ^& Briefadres (Wet BRP, VOW-bestrijding, Dakloosheid)
echo [6] NL Schulden ^& Feitelijke Oninbaarheid (Beslagvrije voet, Beslagverbod, WIK)
echo.
set /p choice="Selecteer profiel (1-6): "

if "%choice%"=="1" (
    copy /y "_engine\domain_packs\nl_wmo\DOCTRINE.md" "DOCTRINE.md" >nul
    echo [+] Geactiveerd: NL Wmo ^& Sociaal Domein
)
if "%choice%"=="2" (
    copy /y "_engine\domain_packs\uk_housing\DOCTRINE.md" "DOCTRINE.md" >nul
    echo [+] Geactiveerd: UK Housing ^& Equality Act
)
if "%choice%"=="3" (
    copy /y "_engine\domain_packs\nl_toeslagen\DOCTRINE.md" "DOCTRINE.md" >nul
    echo [+] Geactiveerd: NL Toeslagen ^& Bestaanszekerheid
)
if "%choice%"=="4" (
    copy /y "_engine\domain_packs\nl_uwv\DOCTRINE.md" "DOCTRINE.md" >nul
    echo [+] Geactiveerd: NL UWV ^& Arbeidsongeschiktheid
)
if "%choice%"=="5" (
    copy /y "_engine\domain_packs\nl_brp_adres\DOCTRINE.md" "DOCTRINE.md" >nul
    echo [+] Geactiveerd: NL BRP ^& Briefadres
)
if "%choice%"=="6" (
    copy /y "_engine\domain_packs\nl_schulden_oninbaar\DOCTRINE.md" "DOCTRINE.md" >nul
    echo [+] Geactiveerd: NL Schulden ^& Feitelijke Oninbaarheid
)

echo.
echo Actieve doctrine is bijgewerkt in DOCTRINE.md.
pause
