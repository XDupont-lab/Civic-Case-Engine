@echo off
title Civic Case Engine (Civic Exoskeleton)
cd /d "%~dp0"

:menu
cls
echo =======================================================================
echo              CIVIC CASE ENGINE — CIVIC EXOSKELETON HUB
echo =======================================================================
echo.
echo [0] Inrichtings- & Onboarding Wizard (bootstrap.py)
echo [1] Multi-Model Dialectic Audit (AUDIT_DRAFT.cmd)
echo [2] Forensische Tijdlijn & Hashes (WEAVE_TIMELINE.cmd)
echo [3] Termijnen & Dwangsommen Tracker (CHECK_TERMIJNEN.cmd)
echo [4] Bank CSV Auditen op bronheffingen & huur (AUDIT_BANK_CSV.cmd)
echo [5] Procesbundel Exporteren met SHA-256 (EXPORT_BUNDEL.cmd)
echo [6] Rechtsdomein / Doctrine Wisselen (SWITCH_DOMAIN.cmd)
echo [7] Chunk-Audit v0.3 — Cognitieve Werkgeheugentoets (CHUNK_AUDIT.cmd)
echo [8] Mappen openen in Verkenner
echo [9] Afsluiten
echo.
set /p opt="Kies een optie (0-9): "

if "%opt%"=="0" python bootstrap.py
if "%opt%"=="1" call AUDIT_DRAFT.cmd
if "%opt%"=="2" call WEAVE_TIMELINE.cmd
if "%opt%"=="3" call CHECK_TERMIJNEN.cmd
if "%opt%"=="4" call AUDIT_BANK_CSV.cmd
if "%opt%"=="5" call EXPORT_BUNDEL.cmd
if "%opt%"=="6" call SWITCH_DOMAIN.cmd
if "%opt%"=="7" call CHUNK_AUDIT.cmd
if "%opt%"=="8" explorer .
if "%opt%"=="9" exit /b

echo.
pause
goto menu
