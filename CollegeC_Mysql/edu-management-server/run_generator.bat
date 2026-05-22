@echo off
chcp 65001 >nul
cd /d "%~dp0src"
echo 正在生成数据库表数据...
java -cp ".;..\lib\mysql-connector-j-8.0.33.jar" com.edu.server.DataGenerator
pause