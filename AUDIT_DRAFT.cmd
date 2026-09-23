@echo off
chcp 65001 >nul
title Civic Case Engine — Constructieve Multi-Model Audit
cd /d "%~dp0"

echo =======================================================================
echo     CIVIC CASE ENGINE — CONSTRUCTIEVE MULTI-MODEL AUDIT ENGINE v2.0
echo =======================================================================
echo.
echo Methodologie: "Bekijk kritisch, verrijk, verfijn en vul aan"
echo Co-pilots: DeepSeek (Logica & Wetgeving) + Grok (Strategie & Velvet Glove)
echo.

if "%1"=="" (
    echo Kies het gewenste audit-niveau:
    echo   [1] Standaard Multi-Model Audit (Parallel getoetst)
    echo   [2] Diepe Kruislingse Audit (--critical, Niveau 3 Falsificatie)
    echo.
    set /p opt="Keuze (1-2, default 1): "
)

if "%opt%"=="2" (
    python "_engine\audit_engine.py" --critical
) else (
    python "_engine\audit_engine.py" %*
)

echo.
pause
