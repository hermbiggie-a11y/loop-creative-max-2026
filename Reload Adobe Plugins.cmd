@echo off
rem Double-click after restarting Photoshop or Premiere: reloads both MCP plugins (they auto-connect).
powershell -ExecutionPolicy Bypass -File "%~dp0tools\start-loop.ps1" -ReloadOnly
pause
