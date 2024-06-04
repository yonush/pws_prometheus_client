@echo off
:: https://gregoryszorc.com/docs/python-build-standalone/main/index.html
::setlocal
cd /D "%~dp0"
set BASE="%~dp0"
%BASE%\python\scripts\pyinstaller.exe --onefile --windowed  --icon favicon.ico --name PWSclient --paths %BASE% main.py 
pause