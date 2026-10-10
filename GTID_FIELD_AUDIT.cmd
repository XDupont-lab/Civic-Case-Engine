@echo off
title Civic Case Engine — G-TID Institutional Field Audit
cd /d "%~dp0"
echo =======================================================================
echo     CIVIC CASE ENGINE — G-TID INSTITUTIONAL FIELD DIAGNOSTICS
echo =======================================================================
echo.
python _engine\gtid_engine.py
echo.
pause
