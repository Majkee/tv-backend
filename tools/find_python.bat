@echo off
rem Sets PY to a working Python 3.9+ command. Used by run_tests.bat and run_server.bat.
set "PY="
py -3 -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1 && set "PY=py -3" && goto :eof
python -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1 && set "PY=python" && goto :eof
python3 -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>&1 && set "PY=python3" && goto :eof
if exist "%~dp0..\python\python.exe" set PY="%~dp0..\python\python.exe"&& goto :eof
echo Nie znaleziono Pythona 3.9+. Zobacz README.md, sekcja "Brak Pythona". 1>&2
