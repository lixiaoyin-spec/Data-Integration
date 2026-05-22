@echo off
echo ======================================================
echo   院系 C 教务系统 - XML 数据生成工具 (正式版)
echo ======================================================
chcp 65001 >nul
:: 1. 进入源码目录
cd /d "%~dp0src"

:: 2. 编译 XmlGenerator.java
echo [1/2] 正在编译 XML 生成模块...
javac -encoding UTF-8 -cp ".;..\lib\*" com\edu\server\XmlGenerator.java
if %errorlevel% neq 0 (
    echo.
    echo ❌ [错误] 编译失败，请检查代码或 lib 目录下的 jar 包。
    pause
    exit /b 1
)

:: 3. 运行程序
echo [2/2] 正在从数据库导出数据并生成 XML 文件...
java -cp ".;..\lib\*" com.edu.server.XmlGenerator

if %errorlevel% neq 0 (
    echo.
    echo ❌ [错误] 运行失败，请检查 MySQL 数据库是否启动。
) else (
    echo.
    echo ✅ [成功] 所有 XML 文件已生成完毕！
    echo 📂 文件路径: 项目根目录\xml\C_System\
)

echo ======================================================
pause