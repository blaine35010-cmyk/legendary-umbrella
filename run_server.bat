@echo off
REM Activate venv and run uvicorn on Windows cmd
pushd %~dp0
call .venv\Scripts\activate.bat
python -m uvicorn web.app:app --host 127.0.0.1 --port 8000
popd