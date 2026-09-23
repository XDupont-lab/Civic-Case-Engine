@echo off
setlocal
echo ========================================================
echo   CIVIC CASE ENGINE -- REALTIME LANDSCAPE SYNCHRONIZER
echo ========================================================
echo.

if exist "%~dp0.venv_bu\Scripts\python.exe" (
    set "PY_BIN=%~dp0.venv_bu\Scripts\python.exe"
) else (
    set "PY_BIN=python"
)

echo [1/2] Scannen van actieve dossiers op actoren, functies en detacheerders...
"%PY_BIN%" "%~dp0_engine\sync_landscape.py" --scan

echo.
echo [2/2] Synchronisatie gereed. Voor specifieke scans:
echo   - Beroepsscan genereren:   %PY_BIN% _engine\sync_landscape.py --enrich "Naam"
echo   - Raadsinformatie pollen:  %PY_BIN% _engine\sync_landscape.py --poll-ris "<RSS_URL>"
echo.
pause
