@echo off
chcp 65001 >nul
python "%~dp0_engine\statutory_clock.py" status
echo.
pause
