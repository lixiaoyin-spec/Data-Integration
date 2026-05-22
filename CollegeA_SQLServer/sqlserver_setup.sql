-- ============================================================
-- College A (SQL Server) 教学管理系统 数据库初始化脚本
-- 基于课本P74-P76表结构设计
-- ============================================================

-- 创建数据库
IF NOT EXISTS (SELECT name FROM sys.databases WHERE name = N'CollegeA')
BEGIN
    CREATE DATABASE CollegeA;
END
GO

USE CollegeA;
GO

-- ============================================================
-- 1. 用户表 (Users)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Users' AND xtype='U')
BEGIN
    CREATE TABLE Users (
        account  VARCHAR(10) PRIMARY KEY,
        password VARCHAR(6)  NOT NULL,
        role     CHAR(4)     NOT NULL  -- '学生','教师','管理员'
    );
END
GO

-- ============================================================
-- 2. 学生表 (Students)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Students' AND xtype='U')
BEGIN
    CREATE TABLE Students (
        Sno VARCHAR(12) PRIMARY KEY,
        Snm VARCHAR(10) NOT NULL,
        Sex VARCHAR(2),
        Sde VARCHAR(10),          -- 系别/专业
        Pwd VARCHAR(10)           -- 登录密码
    );
END
GO

-- ============================================================
-- 3. 课程表 (Courses)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Courses' AND xtype='U')
BEGIN
    CREATE TABLE Courses (
        Cno   VARCHAR(8)  PRIMARY KEY,
        Cnm   VARCHAR(10) NOT NULL,
        Ctm   VARCHAR(2),         -- 学分
        Cpt   VARCHAR(10),        -- 学时
        Tec   VARCHAR(20),        -- 授课教师
        Pla   CHAR(1),            -- 上课地点代码
        Share VARCHAR(10) DEFAULT 'A'  -- 共享来源学院: A/B/C
    );
END
GO

-- ============================================================
-- 4. 选课表 (Selections)
-- ============================================================
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='Selections' AND xtype='U')
BEGIN
    -- 注: PDF规定Selections.Sno=VARCHAR(8), Students.Sno=VARCHAR(12),
    -- Selections.Cno=VARCHAR(12), Courses.Cno=VARCHAR(8), 列长度故意不同以
    -- 体现异构数据库结构差异。SQL Server不允许不同长度列间的FK约束，
    -- 故省略FK，由应用层保证引用完整性。
    CREATE TABLE Selections (
        Sno VARCHAR(8),
        Cno VARCHAR(12),
        Grd VARCHAR(3),           -- 成绩
        CONSTRAINT PK_Selections PRIMARY KEY (Sno, Cno)
    );
END
GO
