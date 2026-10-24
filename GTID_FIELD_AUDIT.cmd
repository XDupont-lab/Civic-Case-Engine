@echo off
title Civic Helper — G-TID Institutional Field Audit
cd /d "%~dp0"
echo =======================================================================
echo     CIVIC HELPER — G-TID INSTITUTIONAL FIELD DIAGNOSTICS
echo =======================================================================
echo.
python _engine\gtid_engine.py
echo.
pause
