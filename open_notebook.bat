@echo off
rem open_notebook.bat - open the experiment notebook in Jupyter.
rem Outputs are saved in the notebook, so it can be read without re-running it.
setlocal
cd /d "%~dp0"
set PYTHONUTF8=1
".venv\Scripts\python.exe" -m jupyter notebook notebooks\phishing_detection.ipynb
