@echo off
cd /d "%~dp0"
set PY="C:\Users\Dell Demo\Desktop\Demo\Loop Agency\tools\.venv\Scripts\python.exe"
%PY% -u driver.py beat1 --reset || exit /b 1
%PY% -u driver.py beat2 || exit /b 2
%PY% -u driver.py beat3 || exit /b 3
echo ALL BEATS 1-3 DONE
