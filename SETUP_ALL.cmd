@echo off
cd /d "%~dp0"
rem SETUP_ALL.cmd — Doorverwijzing naar de volledige 2-Stages Instap
call "%~dp0INSTAP_WINDOWS.cmd" %*
exit /b %ERRORLEVEL%
