@echo off
cd /d "%~dp0"
py -3.12 launch.py
if errorlevel 1 (
  echo.
  echo If Python was not found, install Python 3.12 from https://www.python.org/downloads/
  pause
)
