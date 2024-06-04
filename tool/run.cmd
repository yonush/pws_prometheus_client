@echo off
:: https://gregoryszorc.com/docs/python-build-standalone/main/index.html
setlocal
cd /D "%~dp0"
"%~dp0"python\python -s "%~dp0\main.py"
