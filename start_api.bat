@echo off
rem start_api.bat - run the FastAPI service on http://127.0.0.1:8000
rem The browser UI is at /ui/ and the interactive API docs at /docs.
setlocal
cd /d "%~dp0"
rem UTF-8 mode: the saved model's vocabulary file is UTF-8, which Windows
rem would otherwise read with its legacy code page and fail to load.
set PYTHONUTF8=1
set TF_CPP_MIN_LOG_LEVEL=2
if not exist ".venv\Scripts\python.exe" (
    echo Error: .venv not found. Run setup.bat first.
    pause
    exit /b 1
)
echo Starting the PhishGuard API on http://127.0.0.1:8000 (close this window to stop it)
".venv\Scripts\python.exe" -m uvicorn api.main:app --host 127.0.0.1 --port 8000
pause
