@echo off
rem run_tests.bat - run the test suite against the saved model.
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
set TF_CPP_MIN_LOG_LEVEL=2
".venv\Scripts\python.exe" -m pytest -q
pause
