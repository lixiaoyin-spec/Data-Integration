"""
College A - SQL Server / SQLite Configuration
使用SQLite作为开发数据库，可通过切换连接字符串使用SQL Server
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 当前使用 SQL Server 2022 (Docker)，设置 False 可切换回 SQLite
USE_SQLITE = False
SQLITE_DB_PATH = os.path.join(BASE_DIR, "college_a.db")

# SQL Server 连接配置（当USE_SQLITE=False时使用）
SQLSERVER_CONFIG = {
    "driver": "{SQL Server}",
    "server": "localhost,1433",
    "database": "CollegeA",
    "uid": "sa",
    "pwd": "CollegeA_2024!",
}

# 学院标识
COLLEGE_ID = "A"
COLLEGE_NAME = "学院A (SQL Server)"
