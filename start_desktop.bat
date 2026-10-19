@echo off
rem start_desktop.bat - open the Tkinter desktop app. The API must be running.
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
if not exist ".venv\Scripts\python.exe" (
    echo Error: .venv not found. Run setup.bat first.
    pause
    exit /b 1
)
start "" "%~dp0.venv\Scripts\pythonw.exe" "%~dp0desktop_apppp.py"
