"""
College A - 数据库初始化与示例数据生成
生成50名学生、10门课程、250条选课记录（每名学生选5门课）
"""
import sqlite3
import random
import os
from config import SQLITE_DB_PATH, COLLEGE_ID

# ============================================================
# 中文示例数据
# ============================================================

# 50个中文姓名
SURNAMES = [
    "李", "王", "张", "刘", "陈", "杨", "赵", "黄", "周", "吴",
    "徐", "孙", "胡", "朱", "高", "林", "何", "郭", "马", "罗",
    "梁", "宋", "郑", "谢", "韩", "唐", "冯", "于", "董", "萧",
    "程", "曹", "袁", "邓", "许", "傅", "沈", "曾", "彭", "吕",
    "苏", "卢", "蒋", "蔡", "贾", "丁", "魏", "薛", "叶", "阎"
]

GIVEN_NAMES_MALE = [
    "伟", "强", "磊", "军", "勇", "杰", "涛", "明", "辉", "鹏",
    "浩", "峰", "毅", "俊", "宁", "建", "志", "文", "华", "飞",
    "斌", "宇", "鑫", "超", "平", "健", "刚", "龙", "博", "旭",
    "亮", "威", "震", "恒", "瑞", "岩", "翔", "松", "波", "翰"
]

GIVEN_NAMES_FEMALE = [
    "芳", "敏", "静", "丽", "婷", "雪", "琳", "玲", "艳", "娟",
    "霞", "秀兰", "慧", "莉", "娜", "小红", "洁", "燕", "萍", "倩",
    "丹", "佳", "瑶", "蓉", "悦", "思", "怡", "颖", "文", "晶",
    "琪", "萱", "婉", "月", "晴", "菲", "芸", "馨", "彤", "昕"
]

MAJORS = [
    "计算机科学", "软件工程", "信息管理", "数据科学",
    "人工智能", "网络工程", "信息安全", "电子信息"
]

# 10门课程
COURSES_DATA = [
    ("C001", "数据库原理",   "3", "48",  "李明远教授", "A", COLLEGE_ID),
    ("C002", "操作系统",     "4", "64",  "王建华教授", "B", COLLEGE_ID),
    ("C003", "数据结构",     "3", "48",  "张伟民教授", "C", COLLEGE_ID),
    ("C004", "计算机网络",   "3", "48",  "陈志强教授", "A", COLLEGE_ID),
    ("C005", "软件工程",     "2", "32",  "刘国栋教授", "B", COLLEGE_ID),
    ("C006", "人工智能",     "3", "48",  "杨海波教授", "C", COLLEGE_ID),
    ("C007", "编译原理",     "3", "48",  "赵永强教授", "A", COLLEGE_ID),
    ("C008", "计算机组成",   "4", "64",  "黄晓明教授", "B", COLLEGE_ID),
    ("C009", "算法设计",     "3", "48",  "周文博教授", "C", COLLEGE_ID),
    ("C010", "信息安全",     "2", "32",  "吴志远教授", "A", COLLEGE_ID),
]


def generate_students(count=50):
    """生成指定数量的学生数据，男女均衡"""
    students = []
    used_names = set()
    idx = 1
    while len(students) < count:
        sno = f"S{idx:03d}"
        surname = random.choice(SURNAMES)
        # 均衡性别
        if len(students) % 2 == 0:
            sex = "男"
            given = random.choice(GIVEN_NAMES_MALE)
        else:
            sex = "女"
            given = random.choice(GIVEN_NAMES_FEMALE)
        full_name = surname + given
        if full_name in used_names:
            continue
        used_names.add(full_name)
        major = random.choice(MAJORS)
        pwd = f"stu{idx:03d}"
        students.append((sno, full_name, sex, major, pwd))
        idx += 1
    return students


def generate_selections(students, courses, courses_per_student=5):
    """为每个学生随机选择指定数量的课程"""
    selections = []
    course_cnos = [c[0] for c in courses]
    for sno, *_ in students:
        chosen = random.sample(course_cnos, min(courses_per_student, len(course_cnos)))
        for cno in chosen:
            # 部分有成绩，部分没有（新选的课无成绩）
            if random.random() < 0.4:
                grd = str(random.randint(60, 98))
            else:
                grd = ""
            selections.append((sno, cno, grd))
    return selections


def init_database():
    """初始化数据库：建表 + 插入示例数据"""
    # 删除旧数据库文件
    if os.path.exists(SQLITE_DB_PATH):
        os.remove(SQLITE_DB_PATH)

    conn = sqlite3.connect(SQLITE_DB_PATH)
    cursor = conn.cursor()

    # ---- 建表 (SQLite语法，字段类型兼容) ----
    cursor.execute("""
        CREATE TABLE Users (
            account  VARCHAR(10) PRIMARY KEY,
            password VARCHAR(6)  NOT NULL,
            role     CHAR(4)     NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE Students (
            Sno VARCHAR(12) PRIMARY KEY,
            Snm VARCHAR(10) NOT NULL,
            Sex VARCHAR(2),
            Sde VARCHAR(10),
            Pwd VARCHAR(10)
        )
    """)

    cursor.execute("""
        CREATE TABLE Courses (
            Cno   VARCHAR(8)  PRIMARY KEY,
            Cnm   VARCHAR(10) NOT NULL,
            Ctm   VARCHAR(2),
            Cpt   VARCHAR(10),
            Tec   VARCHAR(20),
            Pla   CHAR(1),
            Share VARCHAR(10) DEFAULT 'A'
        )
    """)

    cursor.execute("""
        CREATE TABLE Selections (
            Sno VARCHAR(8),
            Cno VARCHAR(12),
            Grd VARCHAR(3),
            PRIMARY KEY (Sno, Cno),
            FOREIGN KEY (Sno) REFERENCES Students(Sno),
            FOREIGN KEY (Cno) REFERENCES Courses(Cno)
        )
    """)

    # ---- 插入用户数据 ----
    users = [
        ("admin", "admin", "管理员"),
        ("teacher1", "123456", "教师"),
    ]
    # 为学生创建登录账号
    students = generate_students(50)
    for sno, snm, sex, sde, pwd in students:
        users.append((sno, pwd, "学生"))

    cursor.executemany(
        "INSERT INTO Users (account, password, role) VALUES (?, ?, ?)", users
    )

    # ---- 插入学生数据 ----
    cursor.executemany(
        "INSERT INTO Students (Sno, Snm, Sex, Sde, Pwd) VALUES (?, ?, ?, ?, ?)",
        students
    )

    # ---- 插入课程数据 ----
    cursor.executemany(
        "INSERT INTO Courses (Cno, Cnm, Ctm, Cpt, Tec, Pla, Share) VALUES (?, ?, ?, ?, ?, ?, ?)",
        COURSES_DATA
    )

    # ---- 插入选课数据 ----
    selections = generate_selections(students, COURSES_DATA, 5)
    cursor.executemany(
        "INSERT INTO Selections (Sno, Cno, Grd) VALUES (?, ?, ?)",
        selections
    )

    conn.commit()
    conn.close()

    print(f"[完成] 数据库初始化成功: {SQLITE_DB_PATH}")
    print(f"  - 用户: {len(users)} 条 (含{len(students)}名学生)")
    print(f"  - 学生: {len(students)} 条")
    print(f"  - 课程: {len(COURSES_DATA)} 条")
    print(f"  - 选课: {len(selections)} 条 (每名学生选5门)")

    # 打印统计
    print(f"\n统计信息:")
    print(f"  男生: {sum(1 for s in students if s[2]=='男')} 人")
    print(f"  女生: {sum(1 for s in students if s[2]=='女')} 人")
    print(f"  专业数: {len(set(s[3] for s in students))} 个")


if __name__ == "__main__":
    init_database()
