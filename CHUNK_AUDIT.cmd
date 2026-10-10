@echo off
title Civic Case Engine — Chunk-Audit v0.3
cd /d "%~dp0"

echo =======================================================================
echo     CIVIC CASE ENGINE — CHUNK-AUDIT v0.3 (WERKGEHEUGENTOETS)
echo =======================================================================
echo Toetst conceptbrieven en processtukken op cognitieve dichtheid (<= 4 chunks).
echo Voorkomt dat teksten dichtslibben na zware multi-LLM audits.
echo.

if not exist "Outgoing_Drafts" mkdir Outgoing_Drafts

echo Beschikbare concepten in Outgoing_Drafts/:
dir /b Outgoing_Drafts\*.md 2>nul
echo.

set /p doc="Voer bestandsnaam in (bijv. Outgoing_Drafts\Concept_Sonde_Gemeente.md) of druk op Enter voor de nieuwste: "

if "%doc%"=="" (
    for /f "delims=" %%F in ('dir /b /o:-d Outgoing_Drafts\*.md 2^>nul') do (
        set "doc=Outgoing_Drafts\%%F"
        goto :run_audit
    )
)

:run_audit
if not exist "%doc%" (
    echo [!] Bestand niet gevonden: %doc%
    pause
    exit /b 1
)

echo.
echo [*] Chunk-Audit v0.3 uitvoeren op: %doc%
echo -----------------------------------------------------------------------
python _engine\chunk_audit.py "%doc%"
echo -----------------------------------------------------------------------
echo.
pause
