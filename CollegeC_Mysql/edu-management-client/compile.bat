@echo off
chcp 65001 >nul
cd /d "%~dp0src"
javac -encoding UTF-8 com\edu\client\*.java
if errorlevel 1 exit /b 1
echo 编译成功。
exit /b 0