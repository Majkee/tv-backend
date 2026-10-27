@echo off
rem Starts the backend and the TV simulator. Usage: run_server.bat [--port 8765] [--reset]
setlocal
cd /d "%~dp0"
call tools\find_python.bat
if not defined PY exit /b 1
%PY% -m backend %*
