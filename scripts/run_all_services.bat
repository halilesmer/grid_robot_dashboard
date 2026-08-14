:: Dosya: scripts/run_all_services.bat
@echo off
set ROBOT_ENV=LIVE
set STREAMLIT_PORT=8502
cd /d "%~dp0\.."
python scripts\launcher.py --open-browser