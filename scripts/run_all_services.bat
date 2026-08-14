:: Dosya: scripts/run_all_services.bat
@echo off
set ROBOT_ENV=TEST
set STREAMLIT_PORT=8501
cd /d "%~dp0\.."
python scripts\launcher.py --open-browser