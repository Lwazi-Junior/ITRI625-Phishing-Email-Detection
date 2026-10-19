@echo off
rem setup.bat - create the virtual environment and install the requirements.
rem Run once after cloning. Needs Python 3.10 to 3.13 on the PATH.
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1

if exist ".venv\Scripts\python.exe" (
    echo Virtual environment: already present
) else (
    echo Creating virtual environment in .venv
    where py >nul 2>nul && (py -3 -m venv .venv) || (python -m venv .venv)
    if not exist ".venv\Scripts\python.exe" (
        echo Error: could not create .venv. Install Python 3.10 to 3.13 from python.org and tick "Add to PATH".
        pause
        exit /b 1
    )
)

echo Installing requirements: this downloads TensorFlow and takes a few minutes
".venv\Scripts\python.exe" -m pip install --upgrade pip
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error: pip could not install requirements.txt. Check the internet connection and run setup.bat again.
    pause
    exit /b 1
)
echo.
echo Setup complete. Next: start_all.bat
pause
