@echo off
chcp 65001 >nul
set PYTHONUTF8=1
set PYTHONIOENCODING=utf-8
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_autoplay_utf8.ps1" %*
exit /b %ERRORLEVEL%
