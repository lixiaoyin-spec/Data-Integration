"""
Mock College B (Oracle) - HTTP API 服务器
不依赖 Oracle，基于 SQLite 模拟真实 B 系统的全部端点。
返回的 XML/JSON 格式与 BLocalServer.java 完全一致。

启动: python mock_b_server.py --port 8082
"""
import sys
import os
import json
import sqlite3
import random
import argparse
import xml.etree.ElementTree as ET
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote_plus

PORT = 8082
COLLEGE_ID = "B"
COLLEGE_NAME = "学院B (Oracle)"

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mock_b.db")


# ================================================================
# 数据库初始化
# ================================================================
def init_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""CREATE TABLE b_student (
        SID VARCHAR2(9) PRIMARY KEY, SNAME VARCHAR2(20), SEX VARCHAR2(2),
        MAJOR VARCHAR2(40), PASSWORD VARCHAR2(20), GRADE NUMBER(4),
        PHONE VARCHAR2(20), STATUS VARCHAR2(10) DEFAULT 'NORMAL'
    )""")
    cur.execute("""CREATE TABLE b_account (
        ACC_NAME VARCHAR2(12) PRIMARY KEY, ACC_PWD VARCHAR2(20),
        LEVEL_NO NUMBER(2) DEFAULT 1, SID VARCHAR2(9)
    )""")
    cur.execute("""CREATE TABLE b_course (
        CID VARCHAR2(5) PRIMARY KEY, CNAME VARCHAR2(40), HOURS NUMBER(3),
        CREDIT NUMBER(2,1), TEACHER VARCHAR2(20), LOCATION VARCHAR2(40),
        SHARE_FLAG CHAR(1) DEFAULT 'N', CAPACITY NUMBER(4) DEFAULT 60,
        STATUS VARCHAR2(12) DEFAULT 'OPEN'
    )""")
    cur.execute("""CREATE TABLE b_enrollment (
        SID VARCHAR2(9), CID VARCHAR2(5), SCORE NUMBER(3),
        CHOICE_STA VARCHAR2(12) DEFAULT 'ENROLLED',
        PRIMARY KEY (SID, CID)
    )""")

    # Admin account
    cur.execute("INSERT INTO b_account VALUES ('badmin','123456',9,NULL)")

    # 50 students
    surnames = ['张','李','王','刘','陈','杨','赵','黄','周','吴','徐','孙','胡','朱','高','林','何','郭','马','罗','梁','宋','郑','谢','韩','唐','冯','于','董','萧','程','曹','袁','邓','许','傅','沈','曾','彭','吕','苏','卢','蒋','蔡','贾','丁','魏','薛','叶','阎']
    male_names = ['伟','强','磊','军','勇','杰','涛','明','辉','鹏','浩','峰','毅','俊','宁','建','志','文','华','飞','斌','宇','鑫','超','平','健','刚','龙','博','旭']
    female_names = ['芳','敏','静','丽','婷','雪','琳','玲','艳','娟','霞','慧','莉','娜','红','洁','燕','萍','倩','丹','佳','瑶','蓉','悦','思','怡']
    majors = ['计算机科学','软件工程','网络工程','信息安全','人工智能','数据科学','电子信息','通信工程']

    students = []
    for i in range(1, 51):
        sno = f'B2023{i:03d}'
        name = random.choice(surnames)
        sex = '男' if i % 2 == 1 else '女'
        if sex == '男':
            name += random.choice(male_names)
        else:
            name += random.choice(female_names)
        major = random.choice(majors)
        phone = f'138{random.randint(10000000,99999999)}'
        students.append((sno, name, sex, major))
        cur.execute("INSERT INTO b_student VALUES (?,?,?,?,'123456',2023,?,'NORMAL')",
                    (sno, name, sex, major, phone))
        cur.execute("INSERT INTO b_account VALUES (?,?,1,?)",
                    (f'b{i:04d}', '123456', sno))

    # 10 courses (B-style: C001-C010, different names from A)
    b_courses = [
        ('C001','数据库系统',48,3.0,'赵老师','B-301','Y',60,'OPEN'),
        ('C002','操作系统',54,4.0,'钱老师','B-302','Y',55,'OPEN'),
        ('C003','软件工程',40,2.0,'孙老师','B-303','Y',50,'OPEN'),
        ('C004','Java程序设计',64,4.0,'李老师','B-304','N',60,'OPEN'),
        ('C005','计算机网络',48,3.0,'周老师','B-305','Y',55,'OPEN'),
        ('C006','数据结构',64,4.0,'吴老师','B-306','Y',60,'OPEN'),
        ('C007','编译原理',56,3.5,'郑老师','B-307','N',50,'OPEN'),
        ('C008','人工智能',48,3.0,'王老师','B-308','Y',55,'OPEN'),
        ('C009','信息安全',32,2.0,'冯老师','B-309','N',60,'OPEN'),
        ('C010','算法设计',48,3.0,'陈老师','B-310','Y',50,'OPEN'),
    ]
    for c in b_courses:
        cur.execute("INSERT INTO b_course VALUES (?,?,?,?,?,?,?,?,?)", c)

    # 5 courses per student
    course_ids = [c[0] for c in b_courses]
    for sno, _, _, _ in students:
        chosen = random.sample(course_ids, 5)
        for cno in chosen:
            score = random.randint(60, 98)
            cur.execute("INSERT INTO b_enrollment VALUES (?,?,?,'ENROLLED')",
                       (sno, cno, score))

    conn.commit()
    sc = cur.execute("SELECT COUNT(*) FROM b_student").fetchone()[0]
    cc = cur.execute("SELECT COUNT(*) FROM b_course").fetchone()[0]
    ec = cur.execute("SELECT COUNT(*) FROM b_enrollment").fetchone()[0]
    print(f"[Mock-B] DB init: {sc} students, {cc} courses, {ec} enrollments")
    conn.close()


# ================================================================
# HTTP Handler
# ================================================================
class MockBHandler(BaseHTTPRequestHandler):

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False)
        self._send(body, "application/json; charset=utf-8", code)

    def _send_xml(self, xml_str, code=200):
        self._send(xml_str, "application/xml; charset=utf-8", code)

    def _send_html(self, html, code=200):
        self._send(html, "text/html; charset=utf-8", code)

    def _send(self, body, content_type, code):
        data = body.encode("utf-8")
        try:
            self.send_response(code)
            self.send_header("Content-Type", content_type)
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        return self.rfile.read(length).decode("utf-8") if length > 0 else ""

    def _parse_form(self, body):
        result = {}
        for pair in (body or "").split("&"):
            kv = pair.split("=", 1)
            if len(kv) == 2:
                result[unquote_plus(kv[0])] = unquote_plus(kv[1])
        return result

    def _get_db(self):
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

    def log_message(self, fmt, *args):
        print(f"[Mock-B] {args[0]}")

    # ---- Routing ----

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        routes = {
            "/": self._home, "/b/api/status": self._status,
            "/b/courses": self._courses, "/b/courses/xml": self._courses_xml,
            "/b/shared-courses": self._shared_courses,
            "/b/students": self._students, "/b/students/xml": self._students_xml,
            "/b/selections/xml": self._selections_xml,
            "/b/transcript": self._transcript, "/b/statistics": self._statistics,
        }
        routes.get(path, self._not_found)()

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/") or "/"
        routes = {
            "/b/login": self._login, "/b/enroll": self._enroll,
            "/b/drop": self._drop, "/b/students/import": self._import_student,
            "/b/enrollments/import": self._import_enrollment,
        }
        routes.get(path, self._not_found)()

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _not_found(self):
        self._send_json({"error": "Not Found"}, 404)

    def _home(self):
        self._send_html(f"""<!DOCTYPE html><html lang='zh-CN'><head><meta charset='UTF-8'/>
<title>B系统 Mock</title>
<style>body{{font-family:Segoe UI,sans-serif;max-width:800px;margin:40px auto;padding:20px;background:#0f172a;color:#e5e7eb}}
h1{{color:#38bdf8}}ul{{line-height:2}}.tag{{color:#86efac;font-size:12px}}</style></head><body>
<h1>{COLLEGE_NAME} - Mock API 服务器</h1>
<p class='tag'>(模拟 Oracle B 系统，格式与真实 BLocalServer 完全一致)</p>
<p>状态: 运行中 | 端口: {PORT} | 数据库: SQLite (Mock)</p>
<ul>
<li>GET /b/api/status</li><li>POST /b/login</li>
<li>GET /b/courses | /b/courses/xml | /b/shared-courses</li>
<li>GET /b/students | /b/students/xml | /b/selections/xml</li>
<li>POST /b/enroll | /b/drop</li>
<li>POST /b/students/import | /b/enrollments/import</li>
<li>GET /b/transcript | /b/statistics</li>
</ul></body></html>""")

    def _status(self):
        db = self._get_db()
        sc = db.execute("SELECT COUNT(*) FROM b_student").fetchone()[0]
        cc = db.execute("SELECT COUNT(*) FROM b_course").fetchone()[0]
        ec = db.execute("SELECT COUNT(*) FROM b_enrollment").fetchone()[0]
        db.close()
        self._send_json({"status":"running","college_id":"B","college_name":COLLEGE_NAME,
                         "students":sc,"courses":cc,"selections":ec})

    def _login(self):
        body = self._read_body()
        form = self._parse_form(body)
        acc = form.get("acc", "")
        db = self._get_db()
        row = db.execute("SELECT * FROM b_account WHERE ACC_NAME=? AND ACC_PWD=?",
                         (acc, form.get("pwd",""))).fetchone()
        db.close()
        self._send_json({"status":"success","role":"学生","sno":acc} if row else
                        {"status":"fail","message":"账号或密码错误"}, 200 if row else 401)

    def _courses(self):
        db = self._get_db(); rows = db.execute("SELECT * FROM b_course ORDER BY CID").fetchall(); db.close()
        xml = ["<Classes>"]
        for r in rows:
            xml.append(f"<class><id>{r['CID']}</id><name>{r['CNAME']}</name>"
                       f"<time>{r['HOURS']}</time><score>{r['CREDIT']}</score>"
                       f"<teacher>{r['TEACHER']}</teacher><location>{r['LOCATION']}</location>"
                       f"<shareFlag>{r['SHARE_FLAG']}</shareFlag><capacity>{r['CAPACITY']}</capacity>"
                       f"<status>{r['STATUS']}</status></class>")
        xml.append("</Classes>")
        self._send_xml("".join(xml))

    def _courses_xml(self):
        """Standard integration format"""
        db = self._get_db(); rows = db.execute("SELECT * FROM b_course ORDER BY CID").fetchall(); db.close()
        root = ET.Element("Classes")
        for r in rows:
            c = ET.SubElement(root, "class")
            ET.SubElement(c, "id").text = r["CID"]
            ET.SubElement(c, "name").text = r["CNAME"]
            ET.SubElement(c, "credit").text = str(r["CREDIT"])
            ET.SubElement(c, "hours").text = str(r["HOURS"])
            ET.SubElement(c, "teacher").text = r["TEACHER"]
            ET.SubElement(c, "location").text = r["LOCATION"]
            ET.SubElement(c, "share").text = r["SHARE_FLAG"]
        self._send_xml(ET.tostring(root, encoding="unicode"))

    def _shared_courses(self):
        db = self._get_db()
        rows = db.execute("SELECT * FROM b_course WHERE SHARE_FLAG='Y' ORDER BY CID").fetchall()
        db.close()
        xml = ["<Classes>"]
        for r in rows:
            xml.append(f"<class><id>{r['CID']}</id><name>{r['CNAME']}</name>"
                       f"<time>{r['HOURS']}</time><score>{r['CREDIT']}</score>"
                       f"<teacher>{r['TEACHER']}</teacher><location>{r['LOCATION']}</location>"
                       f"<shareFlag>Y</shareFlag><capacity>{r['CAPACITY']}</capacity>"
                       f"<status>{r['STATUS']}</status></class>")
        xml.append("</Classes>")
        self._send_xml("".join(xml))

    def _students(self):
        db = self._get_db(); rows = db.execute("SELECT * FROM b_student ORDER BY SID").fetchall(); db.close()
        xml = ["<Students>"]
        for r in rows:
            xml.append(f"<student><id>{r['SID']}</id><name>{r['SNAME']}</name>"
                       f"<sex>{r['SEX']}</sex><major>{r['MAJOR']}</major>"
                       f"<grade>{r['GRADE']}</grade><phone>{r['PHONE']}</phone>"
                       f"<status>{r['STATUS']}</status></student>")
        xml.append("</Students>")
        self._send_xml("".join(xml))

    def _students_xml(self):
        """Standard integration format"""
        db = self._get_db(); rows = db.execute("SELECT SID,SNAME,SEX,MAJOR FROM b_student ORDER BY SID").fetchall(); db.close()
        root = ET.Element("Students")
        for r in rows:
            s = ET.SubElement(root, "student")
            ET.SubElement(s, "id").text = r["SID"]
            ET.SubElement(s, "name").text = r["SNAME"]
            ET.SubElement(s, "sex").text = r["SEX"]
            ET.SubElement(s, "major").text = r["MAJOR"]
        self._send_xml(ET.tostring(root, encoding="unicode"))

    def _selections_xml(self):
        """Standard integration format"""
        db = self._get_db()
        rows = db.execute("""SELECT e.SID, s.SNAME, e.CID, c.CNAME, e.SCORE, c.SHARE_FLAG
            FROM b_enrollment e JOIN b_student s ON e.SID=s.SID
            JOIN b_course c ON e.CID=c.CID ORDER BY e.SID, e.CID""").fetchall()
        db.close()
        root = ET.Element("Choices")
        for r in rows:
            ch = ET.SubElement(root, "choice")
            ET.SubElement(ch, "sid").text = r["SID"]
            ET.SubElement(ch, "cid").text = r["CID"]
            ET.SubElement(ch, "score").text = str(r["SCORE"]) if r["SCORE"] else ""
        self._send_xml(ET.tostring(root, encoding="unicode"))

    def _transcript(self):
        qs = parse_qs(urlparse(self.path).query)
        sno = qs.get("sno", [""])[0]
        if not sno:
            self._send_json({"error":"Missing sno"}, 400); return
        db = self._get_db()
        stu = db.execute("SELECT * FROM b_student WHERE SID=?", (sno,)).fetchone()
        if not stu:
            db.close(); self._send_json({"error":"Not found"}, 404); return
        rows = db.execute("""SELECT c.CID,c.CNAME,c.CREDIT,e.SCORE,e.CHOICE_STA
            FROM b_enrollment e JOIN b_course c ON e.CID=c.CID
            WHERE e.SID=? ORDER BY c.CID""", (sno,)).fetchall()
        db.close()
        xml = [f'<Transcript sid="{sno}" name="{stu["SNAME"]}" major="{stu["MAJOR"]}">']
        for r in rows:
            xml.append(f"<Course><cid>{r['CID']}</cid><cname>{r['CNAME']}</cname>"
                       f"<credit>{r['CREDIT']}</credit><score>{r['SCORE'] or ''}</score>"
                       f"<status>{r['CHOICE_STA']}</status></Course>")
        xml.append("</Transcript>")
        self._send_xml("".join(xml))

    def _statistics(self):
        db = self._get_db()
        sc = db.execute("SELECT COUNT(*) FROM b_student").fetchone()[0]
        cc = db.execute("SELECT COUNT(*) FROM b_course").fetchone()[0]
        ec = db.execute("SELECT COUNT(*) FROM b_enrollment").fetchone()[0]
        db.close()
        self._send_json({"student_count":sc,"course_count":cc,"selection_count":ec})

    def _enroll(self):
        body = self._read_body()
        form = self._parse_form(body)
        sno, cno = form.get("sid",""), form.get("cid","")
        if not sno or not cno:
            self._send_json({"status":"fail","message":"缺少学号或课程号"}, 400); return
        db = self._get_db()
        try:
            cnt = db.execute("SELECT COUNT(*) FROM b_enrollment WHERE SID=?",
                            (sno,)).fetchone()[0]
            if cnt >= 5:
                self._send_json({"status":"fail","message":"选课已达上限"})
                return
            db.execute("INSERT INTO b_enrollment (SID,CID,CHOICE_STA) VALUES (?,?,'ENROLLED')",
                      (sno, cno))
            db.commit()
            self._send_json({"status":"success","message":"选课成功"})
        except Exception as e:
            self._send_json({"status":"fail","message":str(e)}, 500)
        finally:
            db.close()

    def _drop(self):
        body = self._read_body()
        form = self._parse_form(body)
        sno, cno = form.get("sid",""), form.get("cid","")
        if not sno or not cno:
            self._send_json({"status":"fail","message":"缺少学号或课程号"}, 400); return
        db = self._get_db()
        try:
            db.execute("DELETE FROM b_enrollment WHERE SID=? AND CID=?", (sno, cno))
            db.commit()
            self._send_json({"status":"success","message":"退课成功"})
        except Exception as e:
            self._send_json({"status":"fail","message":str(e)}, 500)
        finally:
            db.close()

    def _import_student(self):
        body = self._read_body()
        ct = self.headers.get("Content-Type", "")
        if "xml" in ct or body.strip().startswith("<"):
            try:
                root = ET.fromstring(body)
                stu = root if root.tag == "student" else root.find("student")
                sno = (stu.findtext("id") or stu.findtext("sno") or "")
                snm = (stu.findtext("name") or stu.findtext("snm") or "")
                sex = (stu.findtext("sex") or "")
                sde = (stu.findtext("major") or stu.findtext("sde") or "")
            except ET.ParseError:
                self._send_json({"status":"fail","message":"XML解析失败"}, 400); return
        elif "json" in ct:
            data = json.loads(body)
            sno, snm, sex, sde = data.get("sno",""), data.get("snm",""), data.get("sex",""), data.get("sde","")
        else:
            form = self._parse_form(body)
            sno, snm, sex, sde = form.get("sno",""), form.get("snm",""), form.get("sex",""), form.get("sde","")

        if not sno or not snm:
            self._send_json({"status":"fail","message":"缺少学号或姓名"}, 400); return

        db = self._get_db()
        try:
            exist = db.execute("SELECT SID FROM b_student WHERE SID=?", (sno,)).fetchone()
            if exist:
                self._send_json({"status":"success","message":"学生已存在","existed":True})
            else:
                db.execute("INSERT INTO b_student (SID,SNAME,SEX,MAJOR,PASSWORD,GRADE,PHONE,STATUS) VALUES (?,?,?,?,'123456',2024,'','NORMAL')",
                          (sno, snm, sex, sde))
                db.execute("INSERT OR IGNORE INTO b_account (ACC_NAME,ACC_PWD,LEVEL_NO) VALUES (?,?,1)",
                          (sno, '123456'))
                db.commit()
                self._send_json({"status":"success","message":"学生导入成功","existed":False})
        except Exception as e:
            self._send_json({"status":"fail","message":str(e)}, 500)
        finally:
            db.close()

    def _import_enrollment(self):
        body = self._read_body()
        ct = self.headers.get("Content-Type", "")
        if "xml" in ct or body.strip().startswith("<"):
            try:
                root = ET.fromstring(body)
                ch = root if root.tag == "choice" else root.find("choice")
                sno = (ch.findtext("sid") or ch.findtext("sno") or "")
                cno = (ch.findtext("cid") or ch.findtext("cno") or "")
            except ET.ParseError:
                self._send_json({"status":"fail","message":"XML解析失败"}, 400); return
        elif "json" in ct:
            data = json.loads(body)
            sno, cno = data.get("sno",""), data.get("cno","")
        else:
            form = self._parse_form(body)
            sno, cno = form.get("sno",""), form.get("cno","")

        if not sno or not cno:
            self._send_json({"status":"fail","message":"缺少学号或课程号"}, 400); return

        db = self._get_db()
        try:
            db.execute("INSERT OR IGNORE INTO b_enrollment (SID,CID,CHOICE_STA) VALUES (?,?,'ENROLLED')",
                      (sno, cno))
            db.commit()
            self._send_json({"status":"success","message":"选课导入成功"})
        except Exception as e:
            self._send_json({"status":"fail","message":str(e)}, 500)
        finally:
            db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=8082)
    args = parser.parse_args()
    PORT = args.port

    if not os.path.exists(DB_PATH):
        init_db()

    server = HTTPServer(("0.0.0.0", PORT), MockBHandler)
    print(f"[Mock-B] {COLLEGE_NAME} Mock API 服务器 端口 {PORT}")
    print(f"[Mock-B] 模拟 Oracle B 系统，所有端点格式与 BLocalServer 一致")
    for ep in ["/b/api/status","/b/login","/b/courses","/b/shared-courses",
               "/b/students/xml","/b/courses/xml","/b/selections/xml",
               "/b/enroll","/b/drop","/b/students/import","/b/enrollments/import",
               "/b/transcript","/b/statistics"]:
        print(f"[Mock-B]   http://localhost:{PORT}{ep}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        print("\n[Mock-B] 已停止")
