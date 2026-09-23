@echo off
setlocal
cd /d "%~dp0"
echo ========================================================
echo    CIVIC CASE ENGINE -- AI BROWSER AGENT (PORTAL PILOT)
echo ========================================================
echo.
set /p TARGET_URL="Voer de URL van het burgerportaal in: "
set /p TARGET_TASK="Voer de taakomschrijving in (bijv. 'Download alle brieven van 2026'): "

if "%TARGET_URL%"=="" (
    echo [!] Geen URL opgegeven.
    pause
    exit /b 1
)

python "_engine\browser_agent.py" --url "%TARGET_URL%" --task "%TARGET_TASK%"
echo.
echo ========================================================
pause
