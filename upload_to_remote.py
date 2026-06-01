"""
将 A(SQLite)、B(SQLite Mock)、C(MySQL) 三学院数据上传到远程 MySQL hw4 数据库
组号: 27  院系编号: A, B, C
"""
import sqlite3
import pymysql
import os

GROUP_NO = "27"
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 远程 MySQL 连接
REMOTE = {
    "host": "10.60.254.44",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "hw4",
    "charset": "utf8",
}


def connect_remote():
    return pymysql.connect(**REMOTE)


def clear_existing(cur, dept):
    """删除该院系已有数据"""
    cur.execute("DELETE FROM sc WHERE group_no=%s AND dept_no=%s", (GROUP_NO, dept))
    cur.execute("DELETE FROM course WHERE group_no=%s AND dept_no=%s", (GROUP_NO, dept))
    cur.execute("DELETE FROM student WHERE group_no=%s AND dept_no=%s", (GROUP_NO, dept))


def upload_dept(conn, cur, dept, students, courses, selections):
    """上传一个学院的全部数据"""
    clear_existing(cur, dept)

    # 学生
    for sno, snm, sex, sde, pwd in students:
        cur.execute(
            "INSERT INTO student (student_id, student_name, gender, department, account, password, group_no, dept_no) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            (sno, snm, sex, sde, sno, pwd, GROUP_NO, dept),
        )
    print(f"  [{dept}] 学生: {len(students)} 条")

    # 课程（加上院系前缀避免不同学院课程号冲突）
    for cno, cnm, credit, hours, tec, pla, share in courses:
        remote_cno = f"{dept}_{cno}"
        cur.execute(
            "INSERT INTO course (course_id, course_name, credit, teacher_name, location, share_flag, class_hours, practice_hours, group_no, dept_no) "
            "VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
            (remote_cno, cnm, credit, tec, pla, share, hours, "", GROUP_NO, dept),
        )
    print(f"  [{dept}] 课程: {len(courses)} 条")

    # 选课
    for sno, cno, grd in selections:
        remote_cno = f"{dept}_{cno}"
        score = str(grd) if grd else ""
        cur.execute(
            "INSERT INTO sc (course_id, student_id, score, group_no, dept_no) "
            "VALUES (%s,%s,%s,%s,%s)",
            (remote_cno, sno, score, GROUP_NO, dept),
        )
    print(f"  [{dept}] 选课: {len(selections)} 条")


def read_a():
    """从 A 系统的 SQLite 读取数据"""
    db_path = os.path.join(BASE_DIR, "CollegeA_SQLServer", "college_a.db")
    if not os.path.exists(db_path):
        print("  [A] 数据库不存在，请先运行 init_database.py")
        return None, None, None

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT Sno, Snm, Sex, Sde, Pwd FROM Students ORDER BY Sno")
    students = cur.fetchall()
    cur.execute("SELECT Cno, Cnm, Ctm, Cpt, Tec, Pla, Share FROM Courses ORDER BY Cno")
    courses = cur.fetchall()
    cur.execute("SELECT Sno, Cno, Grd FROM Selections ORDER BY Sno, Cno")
    selections = cur.fetchall()
    conn.close()
    return students, courses, selections


def read_b():
    """从 Mock B 系统的 SQLite 读取数据"""
    db_path = os.path.join(BASE_DIR, "oracle", "mock_b.db")
    if not os.path.exists(db_path):
        print("  [B] Mock数据库不存在，请先运行一次 mock_b_server.py")
        return None, None, None

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT SID, SNAME, SEX, MAJOR, PASSWORD FROM b_student ORDER BY SID")
    students = cur.fetchall()
    cur.execute("SELECT CID, CNAME, CREDIT, HOURS, TEACHER, LOCATION, SHARE_FLAG FROM b_course ORDER BY CID")
    courses = cur.fetchall()
    cur.execute("SELECT SID, CID, SCORE FROM b_enrollment ORDER BY SID, CID")
    selections = cur.fetchall()
    conn.close()
    return students, courses, selections


def read_c():
    """从 C 系统的 MySQL 读取数据"""
    conn = pymysql.connect(
        host="localhost", port=3306, user="root",
        password="123456", database="teaching_c", charset="utf8",
    )
    cur = conn.cursor()
    cur.execute("SELECT Sno, Snm, Sex, Sde, Pwd FROM student ORDER BY Sno")
    students_raw = cur.fetchall()
    # 性别转换: M→男, F→女
    students = []
    for sno, snm, sex, sde, pwd in students_raw:
        sex_cn = "男" if sex in ("M", "m") else "女"
        students.append((sno, snm, sex_cn, sde, pwd))

    cur.execute("SELECT Cno, Cnm, Cpt, Ctm, Tec, Pla, Share FROM course ORDER BY Cno")
    courses_raw = cur.fetchall()
    # C 系统的 Cpt=学分, Ctm=学时，与 A 的 Ctm/Cpt 相反
    courses = [(r[0], r[1], str(r[2]), str(r[3]), r[4], r[5], r[6]) for r in courses_raw]

    cur.execute("SELECT Sno, Cno, Grd FROM choice ORDER BY Sno, Cno")
    selections = cur.fetchall()
    conn.close()
    return students, courses, selections


def main():
    print("=" * 55)
    print("  上传三学院数据到远程 MySQL (组号: 27)")
    print(f"  目标: {REMOTE['host']}:{REMOTE['port']}/{REMOTE['database']}")
    print("=" * 55)

    conn = connect_remote()
    cur = conn.cursor()

    for dept, reader in [("A", read_a), ("B", read_b), ("C", read_c)]:
        print(f"\n处理学院 {dept}...")
        students, courses, selections = reader()
        if not students:
            print(f"  跳过学院 {dept}（数据不可用）")
            continue
        upload_dept(conn, cur, dept, students, courses, selections)

    conn.commit()

    # 验证
    print("\n" + "=" * 55)
    print("上传完成，验证数据:")
    cur.execute("SELECT dept_no, COUNT(*) FROM student WHERE group_no=%s GROUP BY dept_no", (GROUP_NO,))
    for dept, cnt in cur.fetchall():
        print(f"  student[{dept}]: {cnt}")
    cur.execute("SELECT dept_no, COUNT(*) FROM course WHERE group_no=%s GROUP BY dept_no", (GROUP_NO,))
    for dept, cnt in cur.fetchall():
        print(f"  course[{dept}]: {cnt}")
    cur.execute("SELECT dept_no, COUNT(*) FROM sc WHERE group_no=%s GROUP BY dept_no", (GROUP_NO,))
    for dept, cnt in cur.fetchall():
        print(f"  sc[{dept}]: {cnt}")
    print("=" * 55)

    conn.close()


if __name__ == "__main__":
    main()
