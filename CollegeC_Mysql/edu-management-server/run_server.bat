@echo off
chcp 65001 >nul
cd /d "%~dp0src"
echo 正在启动 C 院系后端服务器...
java -cp ".;..\lib\mysql-connector-j-8.0.33.jar" com.edu.server.CServer
pause