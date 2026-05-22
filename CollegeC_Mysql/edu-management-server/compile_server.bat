@echo off
chcp 65001 >nul
cd /d "%~dp0src"
echo 正在编译服务器端代码...
javac -encoding UTF-8 -cp ".;..\lib\mysql-connector-j-8.0.33.jar" com\edu\server\*.java
if errorlevel 1 (
    echo ❌ 编译失败！
    pause
    exit /b 1
)
echo ✅ 编译成功！
pause