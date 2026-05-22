"""
将SQLite数据迁移到SQL Server 2022 (Docker)
1. 在SQL Server上创建CollegeA数据库和表
2. 从SQLite读取数据，写入SQL Server
"""
import sqlite3
import pyodbc
from config import SQLITE_DB_PATH

# SQL Server 连接
SQLSERVER_CONN = (
    "DRIVER={SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=master;"
    "UID=sa;"
    "PWD=CollegeA_2024!;"
)


def create_database_and_tables():
    """在SQL Server上创建数据库和表"""
    conn = pyodbc.connect(SQLSERVER_CONN, timeout=10)
    conn.autocommit = True
    cur = conn.cursor()

    # 创建数据库
    db_name = "CollegeA"
    cur.execute(f"IF DB_ID('{db_name}') IS NULL CREATE DATABASE [{db_name}]")
    print(f"[OK] 数据库 {db_name} 已就绪")

    # 切换到 CollegeA
    conn.close()
    conn2 = pyodbc.connect(
        "DRIVER={SQL Server};SERVER=localhost,1433;DATABASE=CollegeA;UID=sa;PWD=CollegeA_2024!;",
        timeout=10
    )
    cur2 = conn2.cursor()

    # 建表
    tables_sql = [
        """IF OBJECT_ID('Selections', 'U') IS NOT NULL DROP TABLE Selections""",
        """IF OBJECT_ID('Courses', 'U') IS NOT NULL DROP TABLE Courses""",
        """IF OBJECT_ID('Students', 'U') IS NOT NULL DROP TABLE Students""",
        """IF OBJECT_ID('Users', 'U') IS NOT NULL DROP TABLE Users""",

        # 注: 中文字段使用NVARCHAR以正确存储Unicode，
        # 符合SQL Server最佳实践（VARCHAR仅支持ASCII）
        """CREATE TABLE Users (
            account  VARCHAR(10) PRIMARY KEY,
            password VARCHAR(6)  NOT NULL,
            role     NVARCHAR(4) NOT NULL
        )""",

        """CREATE TABLE Students (
            Sno VARCHAR(12) PRIMARY KEY,
            Snm NVARCHAR(10) NOT NULL,
            Sex NVARCHAR(2),
            Sde NVARCHAR(10),
            Pwd VARCHAR(10)
        )""",

        """CREATE TABLE Courses (
            Cno   VARCHAR(8)  PRIMARY KEY,
            Cnm   NVARCHAR(10) NOT NULL,
            Ctm   VARCHAR(2),
            Cpt   VARCHAR(10),
            Tec   NVARCHAR(20),
            Pla   CHAR(1),
            Share VARCHAR(10) DEFAULT 'A'
        )""",

        # 注: PDF规范中Selections.Sno(VARCHAR(8))与Students.Sno(VARCHAR(12))、
        # Selections.Cno(VARCHAR(12))与Courses.Cno(VARCHAR(8))长度故意不同，
        # 体现异构数据库结构差异。SQL Server不允许不同长度的外键，故省略FK约束，
        # 由应用层保证引用完整性。
        """CREATE TABLE Selections (
            Sno VARCHAR(8),
            Cno VARCHAR(12),
            Grd VARCHAR(3),
            CONSTRAINT PK_Selections PRIMARY KEY (Sno, Cno)
        )""",
    ]

    for sql in tables_sql:
        try:
            cur2.execute(sql)
            conn2.commit()
        except Exception as e:
            print(f"[WARN] {e}")

    print("[OK] 所有表已创建")
    conn2.close()


def migrate_data():
    """从SQLite迁移数据到SQL Server"""
    # 连接源(SQLite)和目标(SQL Server)
    src = sqlite3.connect(SQLITE_DB_PATH)
    dst = pyodbc.connect(
        "DRIVER={SQL Server};SERVER=localhost,1433;DATABASE=CollegeA;UID=sa;PWD=CollegeA_2024!;",
        timeout=10
    )
    scur = src.cursor()
    dcur = dst.cursor()

    # 清空现有数据（按外键依赖顺序）
    dcur.execute("DELETE FROM Selections")
    dcur.execute("DELETE FROM Courses")
    dcur.execute("DELETE FROM Students")
    dcur.execute("DELETE FROM Users")
    dst.commit()

    # 迁移 Users
    scur.execute("SELECT account, password, role FROM Users")
    users = scur.fetchall()
    for row in users:
        dcur.execute(
            "INSERT INTO Users (account, password, role) VALUES (?, ?, ?)", row
        )
    dst.commit()
    print(f"[OK] Users: {len(users)} 条")

    # 迁移 Students
    scur.execute("SELECT Sno, Snm, Sex, Sde, Pwd FROM Students")
    students = scur.fetchall()
    for row in students:
        dcur.execute(
            "INSERT INTO Students (Sno, Snm, Sex, Sde, Pwd) VALUES (?, ?, ?, ?, ?)", row
        )
    dst.commit()
    print(f"[OK] Students: {len(students)} 条")

    # 迁移 Courses
    scur.execute("SELECT Cno, Cnm, Ctm, Cpt, Tec, Pla, Share FROM Courses")
    courses = scur.fetchall()
    for row in courses:
        dcur.execute(
            "INSERT INTO Courses (Cno, Cnm, Ctm, Cpt, Tec, Pla, Share) VALUES (?, ?, ?, ?, ?, ?, ?)", row
        )
    dst.commit()
    print(f"[OK] Courses: {len(courses)} 条")

    # 迁移 Selections
    scur.execute("SELECT Sno, Cno, Grd FROM Selections")
    selections = scur.fetchall()
    for row in selections:
        dcur.execute(
            "INSERT INTO Selections (Sno, Cno, Grd) VALUES (?, ?, ?)", row
        )
    dst.commit()
    print(f"[OK] Selections: {len(selections)} 条")

    scur.close()
    dcur.close()
    src.close()
    dst.close()

    print(f"\n[完成] 数据迁移成功！")


def verify():
    """验证SQL Server数据"""
    conn = pyodbc.connect(
        "DRIVER={SQL Server};SERVER=localhost,1433;DATABASE=CollegeA;UID=sa;PWD=CollegeA_2024!;",
        timeout=10
    )
    cur = conn.cursor()

    tables = {
        "Users": "SELECT COUNT(*) FROM Users",
        "Students": "SELECT COUNT(*) FROM Students",
        "Courses": "SELECT COUNT(*) FROM Courses",
        "Selections": "SELECT COUNT(*) FROM Selections",
    }

    for name, sql in tables.items():
        cur.execute(sql)
        cnt = cur.fetchone()[0]
        print(f"  {name}: {cnt} 条")

    # 验证关系完整性
    cur.execute("""
        SELECT COUNT(*) FROM Selections s
        WHERE NOT EXISTS (SELECT 1 FROM Students WHERE Sno = s.Sno)
           OR NOT EXISTS (SELECT 1 FROM Courses WHERE Cno = s.Cno)
    """)
    orphan = cur.fetchone()[0]
    print(f"  孤立选课记录: {orphan} 条" + (" (良好)" if orphan == 0 else " (有问题!)"))

    conn.close()
    print("[验证完成]")


if __name__ == "__main__":
    print("=" * 50)
    print("SQLite → SQL Server 2022 数据迁移")
    print("=" * 50)
    create_database_and_tables()
    migrate_data()
    print()
    print("=" * 50)
    print("数据验证")
    print("=" * 50)
    verify()
