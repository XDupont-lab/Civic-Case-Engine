@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ===============================================================================
echo      CIVIC HELPER -- BANK LEDGER AUDITOR EN KETENGROOTBOEK BRIDGE
echo ===============================================================================
echo.
echo Ondersteunt:
echo   - Bank CSV exports (ING, Rabobank, ABN AMRO, SNS, ASN, Triodos)
echo   - ISO 20022 CAMT.053 / CAMT.052 XML dagafschriften
echo.
echo Plaats een bestand in 'Incoming_Letters' of sleep een .csv / .xml op dit bestand.
echo.
if "%~1"=="" goto auto_detect
python _engine\bank_audit.py "%~1"
goto klaar

:auto_detect
python _engine\bank_audit.py

:klaar
echo.
echo ===============================================================================
echo Analyse voltooid. Beancount-ledger opgeslagen in 'Ketengrootboek\'.
echo Druk op een toets om af te sluiten.
pause >nul
