@echo off
title Civic Case Engine - Cybernetische Regressietests (T1-T6)
cd /d "%~dp0"
echo =======================================================================
echo     CIVIC CASE ENGINE - CYBERNETISCHE REGRESSIETESTS (T1 t/m T6)
echo =======================================================================
echo.
python _engine\test_cybernetic_invariants.py
echo.
echo =======================================================================
pause
