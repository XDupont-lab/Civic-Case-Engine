@echo off
chcp 65001 >nul
echo [*] Forensische Tijdlijn- & Bewijs-Weaver draait...
python "%~dp0_engine\timeline_weaver.py" "%~dp0Dossier" "%~dp0Dossier\00_Master_Chronologie.md"
echo.
pause
