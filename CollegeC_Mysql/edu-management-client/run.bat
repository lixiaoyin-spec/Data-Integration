@echo off
chcp 65001 >nul
cd /d "%~dp0src"
java com.edu.client.LoginFrame
