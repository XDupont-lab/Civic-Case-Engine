@echo off
cd /d "%~dp0"
call "%~dp0INSTAP_WINDOWS.cmd" %*
exit /b %ERRORLEVEL%
