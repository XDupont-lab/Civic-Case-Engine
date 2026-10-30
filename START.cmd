@echo off
title Civic Helper — Bouwersmenu
cd /d "%~dp0"

:menu
cls
echo =======================================================================
echo              CIVIC HELPER — WERKOMGEVING & BOUWERSMENU
echo =======================================================================
echo.
echo  [I] 2-Stages Instap & Omgeving Inrichten (INSTAP_WINDOWS.cmd)
echo  [C] Civic Helper Navigatievenster (hulp\venster.py)
echo  [T] De Tafel — Multi-Agent Beraadslaging (gui\tafel_gui.py)
echo  [0] Ontkiemen en Zelftest Startvoorwaarden (ontkiem.py --check)
echo.
echo  --- Gereedschap en Toetsen ---
echo  [1] Briefketen en Dialectische Audit (AUDIT_DRAFT.cmd)
echo  [2] Forensische Tijdlijn en Hashes (WEAVE_TIMELINE.cmd)
echo  [3] Termijnklokken & Keten-Klok nakijken (CHECK_TERMIJNEN.cmd / sluiting.py --klok)
echo  [4] Ketengrootboek & 3-Boeken Integriteitsrapport (Ketengrootboek\sluiting.py --integriteit)
echo  [5] Bank-CSV / CAMT.053 Auditen & Beancount (AUDIT_BANK_CSV.cmd)
echo  [6] Procesbundel Exporteren met SHA-256 (EXPORT_BUNDEL.cmd)
echo  [7] Alle Unit- en Invariantentests draaien (TEST_INVARIANTS.cmd)
echo  [A] Awb Besluit-, Bezwaarclausule- & Dwangsom-Scanner (_engine\awb_besluit_scanner.py)
echo  [8] Werkmap openen in Verkenner
echo  [9] Afsluiten
echo.
set /p opt="Kies een optie (I, C, T, A, 0-9): "

if /i "%opt%"=="I" call INSTAP_WINDOWS.cmd
if /i "%opt%"=="C" call CivicHelper.cmd
if /i "%opt%"=="T" call CivicHelper.cmd --tafel
if /i "%opt%"=="A" python _engine\awb_besluit_scanner.py
if "%opt%"=="0" python ontkiem.py --check
if "%opt%"=="1" call AUDIT_DRAFT.cmd
if "%opt%"=="2" call WEAVE_TIMELINE.cmd
if "%opt%"=="3" (
    call CHECK_TERMIJNEN.cmd
    python Ketengrootboek\sluiting.py --klok
)
if "%opt%"=="4" python Ketengrootboek\sluiting.py --integriteit
if "%opt%"=="5" call AUDIT_BANK_CSV.cmd
if "%opt%"=="6" call EXPORT_BUNDEL.cmd
if "%opt%"=="7" call TEST_INVARIANTS.cmd
if "%opt%"=="8" explorer .
if "%opt%"=="9" exit /b

echo.
pause
goto menu
