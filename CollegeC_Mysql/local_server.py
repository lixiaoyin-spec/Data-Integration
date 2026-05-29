"""
College C (MySQL) - 本地 HTTP API 服务器
为集成服务器提供 REST 接口，端口 8083

启动方式: python local_server.py [--port 8083]
依赖: pip install pymysql
"""
import sys
import os
import json
import argparse
import xml.etree.ElementTree as ET
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote_plus

import pymysql

# ---- 数据库配置 ----
MYSQL_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "123456",
    "database": "teaching_c",
    "charset": "utf8",
}

COLLEGE_ID = "C"
COLLEGE_NAME = "学院C (MySQL)"

PORT = 8083


class CollegeCHandler(BaseHTTPRequestHandler):
    """College C HTTP API 请求处理器"""

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False)
        self._send_response(body, "application/json; charset=utf-8", code)

    def _send_xml(self, xml_str, code=200):
        self._send_response(xml_str, "application/xml; charset=utf-8", code)

    def _send_html(self, html, code=200):
        self._send_response(html, "text/html; charset=utf-8", code)

    def _send_response(self, body, content_type, code):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            return ""
        return self.rfile.read(length).decode("utf-8")

    def _parse_form(self, body):
        result = {}
        if not body:
            return result
        for pair in body.split("&"):
            kv = pair.split("=", 1)
            if len(kv) == 2:
                result[unquote_plus(kv[0])] = unquote_plus(kv[1])
        return result

    def _get_db(self):
        return pymysql.connect(**MYSQL_CONFIG)

    def log_message(self, fmt, *args):
        print(f"[C-Server] {args[0]}")

    # ---- 路由分发 ----

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")

        if path == "/" or path == "/c":
            return self._handle_root()
        elif path == "/c/api/status":
            return self._handle_status()
        elif path == "/c/courses":
            return self._handle_list_courses()
        elif path == "/c/shared-courses":
            return self._handle_list_shared_courses()
        elif path == "/c/students":
            return self._handle_list_students()
        elif path == "/c/students/xml":
            return self._handle_students_xml()
        elif path == "/c/courses/xml":
            return self._handle_courses_xml()
        elif path == "/c/selections/xml":
            return self._handle_selections_xml()
        elif path == "/c/transcript":
            return self._handle_transcript()
        elif path == "/c/statistics":
            return self._handle_statistics()
        else:
            self._send_json({"error": "Not Found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")

        if path == "/c/login":
            return self._handle_login()
        elif path == "/c/enroll":
            return self._handle_enroll()
        elif path == "/c/drop":
            return self._handle_drop()
        elif path == "/c/students/import":
            return self._handle_import_student()
        elif path == "/c/enrollments/import":
            return self._handle_import_enrollment()
        else:
            self._send_json({"error": "Not Found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ---- API 实现 ----

    def _handle_root(self):
        html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"/><title>{COLLEGE_NAME} - API Server</title>
<style>body{{font-family:Segoe UI,sans-serif;max-width:800px;margin:40px auto;padding:20px;background:#0f172a;color:#e5e7eb}}
h1{{color:#38bdf8}}h2{{color:#a78bfa;margin-top:30px}}ul{{line-height:2}}
.method{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:bold;margin-right:8px;min-width:36px;text-align:center}}
.g{{background:rgba(34,197,94,.2);color:#86efac}}.p{{background:rgba(56,189,248,.2);color:#7dd3fc}}
.endpoint{{font-family:Consolas,monospace}}</style></head><body>
<h1>{COLLEGE_NAME} - 本地API服务器</h1><p>状态: 运行中 | 端口: {PORT}</p>
<h2>API 端点</h2><ul>
<li><span class="method g">GET</span><span class="endpoint">/c/api/status</span> — 服务器状态</li>
<li><span class="method p">POST</span><span class="endpoint">/c/login</span> — 用户登录</li>
<li><span class="method g">GET</span><span class="endpoint">/c/courses</span> — 全部课程</li>
<li><span class="method g">GET</span><span class="endpoint">/c/shared-courses</span> — 共享课程</li>
<li><span class="method g">GET</span><span class="endpoint">/c/students</span> — 学生列表</li>
<li><span class="method g">GET</span><span class="endpoint">/c/students/xml</span> — 学生XML导出(标准格式)</li>
<li><span class="method g">GET</span><span class="endpoint">/c/courses/xml</span> — 课程XML导出(标准格式)</li>
<li><span class="method g">GET</span><span class="endpoint">/c/selections/xml</span> — 选课XML导出(标准格式)</li>
<li><span class="method p">POST</span><span class="endpoint">/c/enroll</span> — 选课</li>
<li><span class="method p">POST</span><span class="endpoint">/c/drop</span> — 退课</li>
<li><span class="method p">POST</span><span class="endpoint">/c/students/import</span> — 导入学生(跨院)</li>
<li><span class="method p">POST</span><span class="endpoint">/c/enrollments/import</span> — 导入选课(跨院)</li>
<li><span class="method g">GET</span><span class="endpoint">/c/transcript?sno=</span> — 成绩单</li>
<li><span class="method g">GET</span><span class="endpoint">/c/statistics</span> — 统计信息</li>
</ul></body></html>"""
        self._send_html(html)

    def _handle_status(self):
        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM student")
                sc = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM course")
                cc = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM choice")
                ec = cur.fetchone()[0]
        finally:
            db.close()

        self._send_json({
            "status": "running",
            "college_id": COLLEGE_ID,
            "college_name": COLLEGE_NAME,
            "students": sc,
            "courses": cc,
            "selections": ec,
        })

    def _handle_login(self):
        body = self._read_body()
        form = self._parse_form(body)
        acc = form.get("acc", "")
        pwd = form.get("pwd", "")

        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    "SELECT acc FROM account WHERE acc=%s AND passwd=%s",
                    (acc, pwd)
                )
                row = cur.fetchone()
        finally:
            db.close()

        if row:
            role = "管理员" if acc == "admin" else "学生"
            self._send_json({"status": "success", "role": role, "sno": acc})
        else:
            self._send_json({"status": "fail", "message": "账号或密码错误"}, 401)

    def _handle_list_courses(self):
        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT Cno, Cnm, Ctm, Cpt, Tec, Pla, Share FROM course ORDER BY Cno")
                rows = cur.fetchall()
        finally:
            db.close()

        xml = _build_courses_xml(rows)
        self._send_xml(xml)

    def _handle_list_shared_courses(self):
        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute(
                    "SELECT Cno, Cnm, Ctm, Cpt, Tec, Pla, Share FROM course WHERE Share='Y' ORDER BY Cno"
                )
                rows = cur.fetchall()
        finally:
            db.close()

        xml = _build_courses_xml(rows)
        self._send_xml(xml)

    def _handle_list_students(self):
        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT Sno, Snm, Sex, Sde, Pwd FROM student ORDER BY Sno")
                rows = cur.fetchall()
        finally:
            db.close()

        xml = _build_students_xml(rows)
        self._send_xml(xml)

    def _handle_students_xml(self):
        """标准集成格式XML导出"""
        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT Sno, Snm, Sex, Sde FROM student ORDER BY Sno")
                rows = cur.fetchall()
        finally:
            db.close()

        root = ET.Element("Students")
        for sno, snm, sex, sde in rows:
            stu = ET.SubElement(root, "student")
            ET.SubElement(stu, "id").text = sno
            ET.SubElement(stu, "name").text = snm
            ET.SubElement(stu, "sex").text = "男" if sex in ("M", "m") else "女"
            ET.SubElement(stu, "major").text = sde

        self._send_xml(ET.tostring(root, encoding="unicode"))

    def _handle_courses_xml(self):
        """标准集成格式XML导出"""
        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT Cno, Cnm, Ctm, Cpt, Tec, Pla, Share FROM course ORDER BY Cno")
                rows = cur.fetchall()
        finally:
            db.close()

        root = ET.Element("Classes")
        for cno, cnm, ctm, cpt, tec, pla, share in rows:
            cls = ET.SubElement(root, "class")
            ET.SubElement(cls, "id").text = cno
            ET.SubElement(cls, "name").text = cnm
            ET.SubElement(cls, "credit").text = str(cpt) if cpt else ""
            ET.SubElement(cls, "hours").text = str(ctm) if ctm else ""
            ET.SubElement(cls, "teacher").text = tec
            ET.SubElement(cls, "location").text = pla
            ET.SubElement(cls, "share").text = share if share else ""

        self._send_xml(ET.tostring(root, encoding="unicode"))

    def _handle_selections_xml(self):
        """标准集成格式XML导出"""
        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute("""
                    SELECT ch.Sno, st.Snm, ch.Cno, co.Cnm, ch.Grd, co.Share
                    FROM choice ch
                    JOIN student st ON ch.Sno = st.Sno
                    JOIN course co ON ch.Cno = co.Cno
                    ORDER BY ch.Sno, ch.Cno
                """)
                rows = cur.fetchall()
        finally:
            db.close()

        root = ET.Element("Choices")
        for sno, snm, cno, cnm, grd, share in rows:
            choice = ET.SubElement(root, "choice")
            ET.SubElement(choice, "sid").text = sno
            ET.SubElement(choice, "cid").text = cno
            ET.SubElement(choice, "score").text = str(grd) if grd else ""

        self._send_xml(ET.tostring(root, encoding="unicode"))

    def _handle_transcript(self):
        qs = parse_qs(urlparse(self.path).query)
        sno = qs.get("sno", [""])[0]
        if not sno:
            self._send_json({"error": "缺少sno参数"}, 400)
            return

        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT Sno, Snm, Sde FROM student WHERE Sno=%s", (sno,))
                student = cur.fetchone()
                if not student:
                    self._send_json({"error": "学生不存在"}, 404)
                    return

                cur.execute("""
                    SELECT ch.Cno, co.Cnm, co.Cpt, co.Tec, ch.Grd, co.Share
                    FROM choice ch
                    JOIN course co ON ch.Cno = co.Cno
                    WHERE ch.Sno = %s
                    ORDER BY ch.Cno
                """, (sno,))
                selections = cur.fetchall()
        finally:
            db.close()

        root = ET.Element("Transcript")
        root.set("sid", student[0])
        root.set("name", student[1])
        root.set("major", student[2])
        for cno, cnm, cpt, tec, grd, share in selections:
            course = ET.SubElement(root, "Course")
            ET.SubElement(course, "cid").text = cno
            ET.SubElement(course, "cname").text = cnm
            ET.SubElement(course, "credit").text = str(cpt) if cpt else ""
            ET.SubElement(course, "score").text = str(grd) if grd else ""
            ET.SubElement(course, "share").text = share if share else ""

        self._send_xml(ET.tostring(root, encoding="unicode"))

    def _handle_statistics(self):
        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM student")
                sc = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM course")
                cc = cur.fetchone()[0]
                cur.execute("SELECT COUNT(*) FROM choice")
                ec = cur.fetchone()[0]
                cur.execute("SELECT Sex, COUNT(*) FROM student GROUP BY Sex")
                sex_stats = cur.fetchall()
                cur.execute("SELECT Sde, COUNT(*) FROM student GROUP BY Sde ORDER BY COUNT(*) DESC")
                major_stats = cur.fetchall()
                cur.execute("SELECT Share, COUNT(*) FROM course GROUP BY Share")
                share_stats = cur.fetchall()
                cur.execute("""
                    SELECT co.Cnm, COUNT(ch.Sno)
                    FROM course co
                    LEFT JOIN choice ch ON co.Cno = ch.Cno
                    GROUP BY co.Cno, co.Cnm
                    ORDER BY COUNT(ch.Sno) DESC
                """)
                course_pop = cur.fetchall()
        finally:
            db.close()

        self._send_json({
            "student_count": sc,
            "course_count": cc,
            "selection_count": ec,
            "sex_stats": [[s, c] for s, c in sex_stats],
            "major_stats": [[m, c] for m, c in major_stats],
            "share_stats": [[s, c] for s, c in share_stats],
            "course_popularity": [[n, c] for n, c in course_pop],
        })

    # ---- 选课/退课 ----

    def _handle_enroll(self):
        body = self._read_body()
        form = self._parse_form(body)
        sno = form.get("sid", "")
        cno = form.get("cid", "")

        if not sno or not cno:
            self._send_json({"status": "fail", "message": "缺少学号或课程号"}, 400)
            return

        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM choice WHERE Sno=%s", (sno,))
                count = cur.fetchone()[0]
                if count >= 5:
                    self._send_json({"status": "fail", "message": "选课数量已达上限（5门）"}, 400)
                    return
                cur.execute(
                    "INSERT IGNORE INTO choice (Sno, Cno, Grd) VALUES (%s, %s, NULL)",
                    (sno, cno)
                )
                db.commit()
                self._send_json({"status": "success", "message": "选课成功"})
        except Exception as e:
            self._send_json({"status": "fail", "message": str(e)}, 500)
        finally:
            db.close()

    def _handle_drop(self):
        body = self._read_body()
        form = self._parse_form(body)
        sno = form.get("sid", "")
        cno = form.get("cid", "")

        if not sno or not cno:
            self._send_json({"status": "fail", "message": "缺少学号或课程号"}, 400)
            return

        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute("DELETE FROM choice WHERE Sno=%s AND Cno=%s", (sno, cno))
                db.commit()
                self._send_json({"status": "success", "message": "退课成功"})
        except Exception as e:
            self._send_json({"status": "fail", "message": str(e)}, 500)
        finally:
            db.close()

    # ---- 跨院导入 ----

    def _handle_import_student(self):
        """导入学生信息（用于跨院选课时将学生信息写入课程所属学院）"""
        body = self._read_body()
        content_type = self.headers.get("Content-Type", "")

        if "application/json" in content_type:
            data = json.loads(body)
            sno = data.get("sno", "")
            snm = data.get("snm", "")
            sex = data.get("sex", "")
            sde = data.get("sde", "")
            pwd = data.get("pwd", sno)
        elif "application/xml" in content_type or "text/xml" in content_type:
            # 解析 XML 格式的学生数据
            try:
                root = ET.fromstring(body)
                stu = root if root.tag == "student" else root.find("student")
                if stu is not None:
                    sno = (_xml_text(stu, "id") or _xml_text(stu, "sno"))
                    snm = (_xml_text(stu, "name") or _xml_text(stu, "snm"))
                    sex = (_xml_text(stu, "sex"))
                    sde = (_xml_text(stu, "major") or _xml_text(stu, "sde"))
                    pwd = sno
                else:
                    sno = ""; snm = ""; sex = ""; sde = ""; pwd = ""
            except ET.ParseError:
                self._send_json({"status": "fail", "message": "XML解析失败"}, 400)
                return
        else:
            form = self._parse_form(body)
            sno = form.get("sno", "")
            snm = form.get("snm", "")
            sex = form.get("sex", "")
            sde = form.get("sde", "")
            pwd = form.get("pwd", sno)

        if not sno or not snm:
            self._send_json({"status": "fail", "message": "缺少学号或姓名"}, 400)
            return

        # C系统性别字段用 M/F
        sex_code = "M" if sex == "男" else "F"

        db = self._get_db()
        try:
            with db.cursor() as cur:
                cur.execute("SELECT Sno FROM student WHERE Sno=%s", (sno,))
                if cur.fetchone():
                    self._send_json({"status": "success", "message": "学生已存在,跳过导入", "existed": True})
                else:
                    cur.execute(
                        "INSERT INTO student (Sno, Snm, Sex, Sde, Pwd) VALUES (%s, %s, %s, %s, %s)",
                        (sno, snm, sex_code, sde, pwd)
                    )
                    cur.execute(
                        "INSERT IGNORE INTO account (acc, passwd) VALUES (%s, %s)",
                        (sno, pwd)
                    )
                    db.commit()
                    self._send_json({"status": "success", "message": "学生导入成功", "existed": False})
        except Exception as e:
            self._send_json({"status": "fail", "message": str(e)}, 500)
        finally:
            db.close()

    def _handle_import_enrollment(self):
        """导入选课记录（跨院选课写回）"""
        body = self._read_body()
        content_type = self.headers.get("Content-Type", "")

        if "application/json" in content_type:
            data = json.loads(body)
            sno = data.get("sno", "")
            cno = data.get("cno", "")
            grd = data.get("grd", "")
        elif "application/xml" in content_type or "text/xml" in content_type:
            try:
                root = ET.fromstring(body)
                ch = root if root.tag == "choice" else root.find("choice")
                if ch is not None:
                    sno = (_xml_text(ch, "sid") or _xml_text(ch, "sno"))
                    cno = (_xml_text(ch, "cid") or _xml_text(ch, "cno"))
                    grd = (_xml_text(ch, "score") or _xml_text(ch, "grd"))
                else:
                    sno = ""; cno = ""; grd = ""
            except ET.ParseError:
                self._send_json({"status": "fail", "message": "XML解析失败"}, 400)
                return
        else:
            form = self._parse_form(body)
            sno = form.get("sno", "")
            cno = form.get("cno", "")
            grd = form.get("grd", "")

        if not sno or not cno:
            self._send_json({"status": "fail", "message": "缺少学号或课程号"}, 400)
            return

        db = self._get_db()
        try:
            with db.cursor() as cur:
                grd_val = int(grd) if grd else None
                cur.execute(
                    "INSERT IGNORE INTO choice (Sno, Cno, Grd) VALUES (%s, %s, %s)",
                    (sno, cno, grd_val)
                )
                db.commit()
                self._send_json({"status": "success", "message": "选课记录导入成功"})
        except Exception as e:
            self._send_json({"status": "fail", "message": str(e)}, 500)
        finally:
            db.close()


# ================================================================
# XML 构建辅助
# ================================================================

def _xml_text(elem, tag):
    child = elem.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return ""


def _build_courses_xml(rows):
    root = ET.Element("Classes")
    for cno, cnm, ctm, cpt, tec, pla, share in rows:
        cls = ET.SubElement(root, "class")
        ET.SubElement(cls, "id").text = cno
        ET.SubElement(cls, "name").text = cnm
        ET.SubElement(cls, "credit").text = str(cpt) if cpt else ""
        ET.SubElement(cls, "hours").text = str(ctm) if ctm else ""
        ET.SubElement(cls, "teacher").text = tec
        ET.SubElement(cls, "location").text = pla
        ET.SubElement(cls, "share").text = share if share else ""
    return ET.tostring(root, encoding="unicode")


def _build_students_xml(rows):
    root = ET.Element("Students")
    for sno, snm, sex, sde, pwd in rows:
        stu = ET.SubElement(root, "student")
        ET.SubElement(stu, "id").text = sno
        ET.SubElement(stu, "name").text = snm
        ET.SubElement(stu, "sex").text = "男" if sex in ("M", "m") else "女"
        ET.SubElement(stu, "major").text = sde
    return ET.tostring(root, encoding="unicode")


# ================================================================
# 启动入口
# ================================================================

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="College C Local API Server")
    parser.add_argument("--port", type=int, default=8083, help="Server port (default: 8083)")
    args = parser.parse_args()
    PORT = args.port

    server = HTTPServer(("0.0.0.0", PORT), CollegeCHandler)
    print(f"[C-Server] {COLLEGE_NAME} 本地API服务器已启动")
    print(f"[C-Server] 地址: http://localhost:{PORT}")
    print(f"[C-Server] 状态: http://localhost:{PORT}/c/api/status")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[C-Server] 服务器已停止")
        server.server_close()
