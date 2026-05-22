"""
College A - 数据库管理器
提供所有数据库CRUD操作，支持SQLite（开发）和SQL Server（生产）
"""
import sqlite3
from config import SQLITE_DB_PATH, USE_SQLITE, SQLSERVER_CONFIG, COLLEGE_ID


class DatabaseManager:
    def __init__(self):
        self.conn = None

    def connect(self):
        if USE_SQLITE:
            self.conn = sqlite3.connect(SQLITE_DB_PATH)
            self.conn.execute("PRAGMA foreign_keys = ON")
        else:
            import pyodbc
            cfg = SQLSERVER_CONFIG
            if "uid" in cfg:
                conn_str = (
                    f"DRIVER={cfg['driver']};"
                    f"SERVER={cfg['server']};"
                    f"DATABASE={cfg['database']};"
                    f"UID={cfg['uid']};"
                    f"PWD={cfg['pwd']};"
                )
            else:
                conn_str = (
                    f"DRIVER={cfg['driver']};"
                    f"SERVER={cfg['server']};"
                    f"DATABASE={cfg['database']};"
                    f"TRUSTED_CONNECTION={cfg['trusted_connection']};"
                )
            self.conn = pyodbc.connect(conn_str)

    def close(self):
        if self.conn:
            self.conn.close()

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, *args):
        self.close()

    # ============================================================
    # 用户认证
    # ============================================================
    def authenticate(self, account, password):
        """验证用户登录，返回(成功, 角色, 学号或None)"""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT account, role FROM Users WHERE account=? AND password=?",
            (account, password)
        )
        row = cur.fetchone()
        if row:
            role = row[1]
            sno = None
            if role == "学生":
                sno = account  # 学生账号即学号
            return True, role, sno
        return False, None, None

    # ============================================================
    # 学生管理
    # ============================================================
    def get_all_students(self):
        cur = self.conn.cursor()
        cur.execute("SELECT Sno, Snm, Sex, Sde, Pwd FROM Students ORDER BY Sno")
        return cur.fetchall()

    def get_student(self, sno):
        cur = self.conn.cursor()
        cur.execute("SELECT Sno, Snm, Sex, Sde, Pwd FROM Students WHERE Sno=?", (sno,))
        return cur.fetchone()

    def add_student(self, sno, snm, sex, sde, pwd):
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO Students (Sno, Snm, Sex, Sde, Pwd) VALUES (?, ?, ?, ?, ?)",
            (sno, snm, sex, sde, pwd)
        )
        cur.execute(
            "INSERT INTO Users (account, password, role) VALUES (?, ?, '学生')",
            (sno, pwd)
        )
        self.conn.commit()

    def update_student(self, sno, snm, sex, sde, pwd):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE Students SET Snm=?, Sex=?, Sde=?, Pwd=? WHERE Sno=?",
            (snm, sex, sde, pwd, sno)
        )
        cur.execute(
            "UPDATE Users SET password=? WHERE account=?",
            (pwd, sno)
        )
        self.conn.commit()

    def delete_student(self, sno):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM Selections WHERE Sno=?", (sno,))
        cur.execute("DELETE FROM Users WHERE account=?", (sno,))
        cur.execute("DELETE FROM Students WHERE Sno=?", (sno,))
        self.conn.commit()

    def get_student_count(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Students")
        return cur.fetchone()[0]

    # ============================================================
    # 课程管理
    # ============================================================
    def get_all_courses(self):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT Cno, Cnm, Ctm, Cpt, Tec, Pla, Share FROM Courses ORDER BY Cno"
        )
        return cur.fetchall()

    def get_course(self, cno):
        cur = self.conn.cursor()
        cur.execute(
            "SELECT Cno, Cnm, Ctm, Cpt, Tec, Pla, Share FROM Courses WHERE Cno=?",
            (cno,)
        )
        return cur.fetchone()

    def add_course(self, cno, cnm, ctm, cpt, tec, pla, share=None):
        if share is None:
            share = COLLEGE_ID
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO Courses (Cno, Cnm, Ctm, Cpt, Tec, Pla, Share) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (cno, cnm, ctm, cpt, tec, pla, share)
        )
        self.conn.commit()

    def update_course(self, cno, cnm, ctm, cpt, tec, pla, share):
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE Courses SET Cnm=?, Ctm=?, Cpt=?, Tec=?, Pla=?, Share=? WHERE Cno=?",
            (cnm, ctm, cpt, tec, pla, share, cno)
        )
        self.conn.commit()

    def delete_course(self, cno):
        cur = self.conn.cursor()
        cur.execute("DELETE FROM Selections WHERE Cno=?", (cno,))
        cur.execute("DELETE FROM Courses WHERE Cno=?", (cno,))
        self.conn.commit()

    def get_course_count(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Courses")
        return cur.fetchone()[0]

    # ============================================================
    # 选课管理
    # ============================================================
    def get_all_selections(self):
        """获取所有选课记录，含学生姓名和课程名"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT s.Sno, st.Snm, s.Cno, c.Cnm, s.Grd, c.Share
            FROM Selections s
            JOIN Students st ON s.Sno = st.Sno
            JOIN Courses c ON s.Cno = c.Cno
            ORDER BY s.Sno, s.Cno
        """)
        return cur.fetchall()

    def get_student_selections(self, sno):
        """获取某学生的选课记录"""
        cur = self.conn.cursor()
        cur.execute("""
            SELECT s.Cno, c.Cnm, c.Ctm, c.Tec, s.Grd, c.Share
            FROM Selections s
            JOIN Courses c ON s.Cno = c.Cno
            WHERE s.Sno = ?
            ORDER BY s.Cno
        """, (sno,))
        return cur.fetchall()

    def get_student_selection_count(self, sno):
        """获取某学生的选课数量"""
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Selections WHERE Sno=?", (sno,))
        return cur.fetchone()[0]

    def add_selection(self, sno, cno):
        """添加选课（不带成绩）"""
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO Selections (Sno, Cno, Grd) VALUES (?, ?, '')",
            (sno, cno)
        )
        self.conn.commit()

    def remove_selection(self, sno, cno):
        """退选课程"""
        cur = self.conn.cursor()
        cur.execute(
            "DELETE FROM Selections WHERE Sno=? AND Cno=?",
            (sno, cno)
        )
        self.conn.commit()

    def update_grade(self, sno, cno, grd):
        """更新成绩"""
        cur = self.conn.cursor()
        cur.execute(
            "UPDATE Selections SET Grd=? WHERE Sno=? AND Cno=?",
            (grd, sno, cno)
        )
        self.conn.commit()

    def get_selection_count(self):
        cur = self.conn.cursor()
        cur.execute("SELECT COUNT(*) FROM Selections")
        return cur.fetchone()[0]

    # ============================================================
    # 跨学院课程查询（用于课程共享）
    # ============================================================
    def get_shared_courses(self):
        """获取本学院共享给其他学院的课程"""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT Cno, Cnm, Ctm, Cpt, Tec, Pla, Share FROM Courses WHERE Share=?",
            (COLLEGE_ID,)
        )
        return cur.fetchall()

    def get_external_courses(self):
        """获取来自其他学院的课程（Share != A）"""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT Cno, Cnm, Ctm, Cpt, Tec, Pla, Share FROM Courses WHERE Share != ?",
            (COLLEGE_ID,)
        )
        return cur.fetchall()

    # ============================================================
    # 统计
    # ============================================================
    def get_statistics(self):
        """获取统计数据"""
        student_count = self.get_student_count()
        course_count = self.get_course_count()
        selection_count = self.get_selection_count()

        # 各专业人数
        cur = self.conn.cursor()
        cur.execute("SELECT Sde, COUNT(*) FROM Students GROUP BY Sde ORDER BY COUNT(*) DESC")
        major_stats = cur.fetchall()

        # 性别分布
        cur.execute("SELECT Sex, COUNT(*) FROM Students GROUP BY Sex")
        sex_stats = cur.fetchall()

        # 各课程选课人数
        cur.execute("""
            SELECT c.Cnm, COUNT(s.Sno)
            FROM Courses c
            LEFT JOIN Selections s ON c.Cno = s.Cno
            GROUP BY c.Cno, c.Cnm
            ORDER BY COUNT(s.Sno) DESC
        """)
        course_popularity = cur.fetchall()

        # 跨学院课程数量
        cur.execute("SELECT Share, COUNT(*) FROM Courses GROUP BY Share")
        share_stats = cur.fetchall()

        return {
            "student_count": student_count,
            "course_count": course_count,
            "selection_count": selection_count,
            "major_stats": major_stats,
            "sex_stats": sex_stats,
            "course_popularity": course_popularity,
            "share_stats": share_stats,
        }
