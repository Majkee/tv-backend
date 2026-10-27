@echo off
rem Runs the whole test suite. Extra arguments go to unittest, e.g. -v or -k ota.
setlocal
cd /d "%~dp0"
call tools\find_python.bat
if not defined PY exit /b 1
%PY% -m unittest discover -s tests -t . %*
