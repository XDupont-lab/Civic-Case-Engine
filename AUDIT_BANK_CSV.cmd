@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ===============================================================================
echo                CIVIC CASE ENGINE -- BANK LEDGER AUDITOR
echo ===============================================================================
echo.
echo Plaats een geanonimiseerde bank-export (.csv) in Incoming_Letters van DEZE engine.
echo Persoonlijke bank-exports uit externe mappen hierheen kopieren om te auditen.
echo.
echo Druk op een toets om de analyse te starten...
pause >nul

python _engine\bank_audit.py

echo.
echo ===============================================================================
echo Analyse voltooid. Druk op een toets om af te sluiten.
pause >nul
