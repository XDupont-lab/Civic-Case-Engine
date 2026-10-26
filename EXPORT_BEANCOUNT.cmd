@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

echo ===============================================================================
echo       CIVIC HELPER -- BEANCOUNT EXPORTER EN KETENGROOTBOEK BRIDGE
echo ===============================================================================
echo.
echo 1. Exporteert institutionele overdrachten (Ketengrootboek) naar Beancount
echo 2. Parseert bankbestanden (CSV / CAMT.053 XML) naar sluitende Beancount-posten
echo.

python -c "import sys; sys.path.append('_engine'); from beancount_exporter import export_ketengrootboek_to_beancount; p = export_ketengrootboek_to_beancount(); print('[*] Ketengrootboek Beancount gegenereerd: ' + p)"

echo.
echo Controleer of er een bankbestand in 'Incoming_Letters' staat...
python _engine\bank_audit.py %*

echo.
echo ===============================================================================
echo Export voltooid. Ledgers staan in 'Ketengrootboek\'.
echo.
echo Tip: Installeer eventueel Fava voor een webdashboard:
echo      pip install fava beancount
echo      fava Ketengrootboek\ketengrootboek_audit.beancount
echo ===============================================================================
pause >nul
