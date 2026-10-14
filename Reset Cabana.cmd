@echo off
rem Double-click between demo runs: clears work/social/cut and restores working copies from _master.
powershell -ExecutionPolicy Bypass -File "%~dp0tools\reset-cabana.ps1"
pause
