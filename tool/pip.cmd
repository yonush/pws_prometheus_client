@echo off
setlocal
cd /D %~dp0

"%~dp0"python\python.exe -m pip %1 %2 %3 %4 %5 %6
