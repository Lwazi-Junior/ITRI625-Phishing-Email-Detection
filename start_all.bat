@echo off
rem start_all.bat - start the API in its own window, wait until it answers,
rem then open the browser UI and the desktop app.
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo Error: .venv not found. Run setup.bat first.
    pause
    exit /b 1
)
start "PhishGuard API" cmd /c "%~dp0start_api.bat"
echo Waiting for the API to load the model...
for /l %%i in (1,1,90) do (
    powershell -NoProfile -Command "try { Invoke-WebRequest -UseBasicParsing http://127.0.0.1:8000/health -TimeoutSec 2 | Out-Null; exit 0 } catch { exit 1 }" && goto ready
    timeout /t 2 /nobreak >nul
)
echo Error: the API did not answer within 3 minutes. Check the "PhishGuard API" window for the reason.
pause
exit /b 1
:ready
echo API: online
call "%~dp0start_web.bat"
call "%~dp0start_desktop.bat"
