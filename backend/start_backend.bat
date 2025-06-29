@echo off
echo Starting Video Splitter Pro Backend...
cd /d "%~dp0"
call venv\Scripts\activate
uvicorn server:app --host 127.0.0.1 --port 8001 --reload
pause