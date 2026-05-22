"""
College A (SQL Server) - 本地 HTTP API 服务器
为集成服务器提供 REST 接口，封装 db_manager 和 xml_handler
启动方式: python local_server.py [--port 8081]
"""
import sys
import os
import json
import argparse
import xml.etree.ElementTree as ET
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from db_manager import DatabaseManager
from config import COLLEGE_ID, COLLEGE_NAME


class CollegeAHandler(BaseHTTPRequestHandler):
    """College A HTTP API 请求处理器"""

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False)
        self._send_response(body, "application/json; charset=utf-8", code)

    def _send_xml(self, xml_str, code=200):
        self._send_response(xml_str, "application/xml; charset=utf-8", code)

    def _send_html(self, html, code=200):
        self._send_response(html, "text/html; charset=utf-8", code)

    def _send_text(self, text, code=200):
        self._send_response(text, "text/plain; charset=utf-8", code)

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
                from urllib.parse import unquote_plus
                result[unquote_plus(kv[0])] = unquote_plus(kv[1])
        return result

    def _get_db(self):
        db = DatabaseManager()
        db.connect()
        return db

    def log_message(self, fmt, *args):
        print(f"[A-Server] {args[0]}")

    # ---- 路由分发 ----

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")

        if path == "/" or path == "/a":
            return self._handle_root()
        elif path == "/a/api/status":
            return self._handle_status()
        elif path == "/a/courses":
            return self._handle_list_courses()
        elif path == "/a/shared-courses":
            return self._handle_list_shared_courses()
        elif path == "/a/students":
            return self._handle_list_students()
        elif path == "/a/students/xml":
            return self._handle_students_xml()
        elif path == "/a/courses/xml":
            return self._handle_courses_xml()
        elif path == "/a/selections/xml":
            return self._handle_selections_xml()
        elif path == "/a/transcript":
            return self._handle_transcript()
        elif path == "/a/statistics":
            return self._handle_statistics()
        else:
            self._send_json({"error": "Not Found"}, 404)

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")

        if path == "/a/login":
            return self._handle_login()
        elif path == "/a/enroll":
            return self._handle_enroll()
        elif path == "/a/drop":
            return self._handle_drop()
        elif path == "/a/students/import":
            return self._handle_import_student()
        elif path == "/a/enrollments/import":
            return self._handle_import_enrollment()
        else:
            self._send_json({"error": "Not Found"}, 404)

    def do_OPTIONS(self):
        """CORS preflight"""
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
h1{{color:#38bdf8}}h2{{color:#a78bfa;margin-top:30px}}ul{{line-height:2}}.method{{display:inline-block;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:bold;margin-right:8px;min-width:36px;text-align:center}}
.g{{background:rgba(34,197,94,.2);color:#86efac}}.p{{background:rgba(56,189,248,.2);color:#7dd3fc}}
.endpoint{{font-family:Consolas,monospace}}</style></head><body>
<h1>{COLLEGE_NAME} - 本地API服务器</h1><p>状态: 运行中 | 端口: {PORT}</p>
<h2>API 端点</h2><ul>
<li><span class="method g">GET</span><span class="endpoint">/a/api/status</span> — 服务器状态</li>
<li><span class="method p">POST</span><span class="endpoint">/a/login</span> — 用户登录</li>
<li><span class="method g">GET</span><span class="endpoint">/a/courses</span> — 全部课程</li>
<li><span class="method g">GET</span><span class="endpoint">/a/shared-courses</span> — 共享课程</li>
<li><span class="method g">GET</span><span class="endpoint">/a/students</span> — 学生列表</li>
<li><span class="method g">GET</span><span class="endpoint">/a/students/xml</span> — 学生XML导出</li>
<li><span class="method g">GET</span><span class="endpoint">/a/courses/xml</span> — 课程XML导出</li>
<li><span class="method g">GET</span><span class="endpoint">/a/selections/xml</span> — 选课XML导出</li>
<li><span class="method p">POST</span><span class="endpoint">/a/enroll</span> — 选课</li>
<li><span class="method p">POST</span><span class="endpoint">/a/drop</span> — 退课</li>
<li><span class="method p">POST</span><span class="endpoint">/a/students/import</span> — 导入学生（跨院）</li>
<li><span class="method p">POST</span><span class="endpoint">/a/enrollments/import</span> — 导入选课（跨院）</li>
<li><span class="method g">GET</span><span class="endpoint">/a/transcript?sno=</span> — 成绩单</li>
<li><span class="method g">GET</span><span class="endpoint">/a/statistics</span> — 统计信息</li>
</ul></body></html>"""
        self._send_html(html)

    def _handle_status(self):
        db = self._get_db()
        try:
            student_count = db.get_student_count()
            course_count = db.get_course_count()
            selection_count = db.get_selection_count()
        finally:
            db.close()
        self._send_json({
            "status": "running",
            "college_id": COLLEGE_ID,
            "college_name": COLLEGE_NAME,
            "students": student_count,
            "courses": course_count,
            "selections": selection_count
        })

    def _handle_login(self):
        body = self._read_body()
        form = self._parse_form(body)
        acc = form.get("acc", "")
        pwd = form.get("pwd", "")

        db = self._get_db()
        try:
            ok, role, sno = db.authenticate(acc, pwd)
        finally:
            db.close()

        if ok:
            self._send_json({"status": "success", "role": role, "sno": sno})
        else:
            self._send_json({"status": "fail", "message": "账号或密码错误"}, 401)

    def _handle_list_courses(self):
        db = self._get_db()
        try:
            rows = db.get_all_courses()
        finally:
            db.close()

        xml = _build_courses_xml(rows)
        self._send_xml(xml)

    def _handle_list_shared_courses(self):
        db = self._get_db()
        try:
            rows = db.get_shared_courses()
        finally:
            db.close()

        xml = _build_courses_xml(rows)
        self._send_xml(xml)

    def _handle_list_students(self):
        db = self._get_db()
        try:
            rows = db.get_all_students()
        finally:
            db.close()

        xml = _build_students_xml(rows)
        self._send_xml(xml)

    def _handle_students_xml(self):
        """标准集成格式XML导出（用于集成服务器拉取）"""
        db = self._get_db()
        try:
            rows = db.get_all_students()
        finally:
            db.close()

        root = ET.Element("Students")
        for sno, snm, sex, sde, pwd in rows:
            student = ET.SubElement(root, "student")
            ET.SubElement(student, "id").text = sno
            ET.SubElement(student, "name").text = snm
            ET.SubElement(student, "sex").text = sex
            ET.SubElement(student, "major").text = sde

        self._send_xml(ET.tostring(root, encoding="unicode"))

    def _handle_courses_xml(self):
        """标准集成格式XML导出"""
        db = self._get_db()
        try:
            rows = db.get_all_courses()
        finally:
            db.close()

        root = ET.Element("Classes")
        for cno, cnm, ctm, cpt, tec, pla, share in rows:
            cls = ET.SubElement(root, "class")
            ET.SubElement(cls, "id").text = cno
            ET.SubElement(cls, "name").text = cnm
            ET.SubElement(cls, "credit").text = str(ctm) if ctm else ""
            ET.SubElement(cls, "hours").text = str(cpt) if cpt else ""
            ET.SubElement(cls, "teacher").text = tec
            ET.SubElement(cls, "location").text = pla
            ET.SubElement(cls, "share").text = share if share else ""

        self._send_xml(ET.tostring(root, encoding="unicode"))

    def _handle_selections_xml(self):
        """标准集成格式XML导出"""
        db = self._get_db()
        try:
            rows = db.get_all_selections()
        finally:
            db.close()

        root = ET.Element("Choices")
        for sno, snm, cno, cnm, grd, share in rows:
            choice = ET.SubElement(root, "choice")
            ET.SubElement(choice, "sid").text = sno
            ET.SubElement(choice, "cid").text = cno
            ET.SubElement(choice, "score").text = grd if grd else ""

        self._send_xml(ET.tostring(root, encoding="unicode"))

    def _handle_transcript(self):
        qs = parse_qs(urlparse(self.path).query)
        sno = qs.get("sno", [""])[0]
        if not sno:
            self._send_json({"error": "缺少sno参数"}, 400)
            return

        db = self._get_db()
        try:
            student = db.get_student(sno)
            selections = db.get_student_selections(sno)
        finally:
            db.close()

        if not student:
            self._send_json({"error": "学生不存在"}, 404)
            return

        root = ET.Element("Transcript")
        root.set("sid", sno)
        root.set("name", student[1])
        root.set("major", student[3])
        for cno, cnm, ctm, tec, grd, share in selections:
            course = ET.SubElement(root, "Course")
            ET.SubElement(course, "cid").text = cno
            ET.SubElement(course, "cname").text = cnm
            ET.SubElement(course, "credit").text = str(ctm) if ctm else ""
            ET.SubElement(course, "score").text = grd if grd else ""
            ET.SubElement(course, "share").text = share if share else ""

        self._send_xml(ET.tostring(root, encoding="unicode"))

    def _handle_statistics(self):
        db = self._get_db()
        try:
            stats = db.get_statistics()
        finally:
            db.close()
        self._send_json(stats)

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
            existing = db.get_student_selection_count(sno)
            if existing >= 5:
                self._send_json({"status": "fail", "message": "选课数量已达上限（5门）"}, 400)
                return
            db.add_selection(sno, cno)
        except Exception as e:
            self._send_json({"status": "fail", "message": str(e)}, 500)
        finally:
            db.close()

        self._send_json({"status": "success", "message": "选课成功"})

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
            db.remove_selection(sno, cno)
        except Exception as e:
            self._send_json({"status": "fail", "message": str(e)}, 500)
        finally:
            db.close()

        self._send_json({"status": "success", "message": "退课成功"})

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

        db = self._get_db()
        try:
            existing = db.get_student(sno)
            if existing:
                self._send_json({"status": "success", "message": "学生已存在,跳过导入", "existed": True})
            else:
                db.add_student(sno, snm, sex, sde, pwd)
                self._send_json({"status": "success", "message": "学生导入成功", "existed": False})
        except Exception as e:
            self._send_json({"status": "fail", "message": str(e)}, 500)
        finally:
            db.close()

    def _handle_import_enrollment(self):
        """导入选课记录（用于跨院选课时将选课记录写入课程所属学院）"""
        body = self._read_body()
        content_type = self.headers.get("Content-Type", "")

        if "application/json" in content_type:
            data = json.loads(body)
            sno = data.get("sno", "")
            cno = data.get("cno", "")
            grd = data.get("grd", "")
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
            db.add_selection(sno, cno)
            if grd:
                db.update_grade(sno, cno, grd)
        except Exception as e:
            self._send_json({"status": "fail", "message": str(e)}, 500)
        finally:
            db.close()

        self._send_json({"status": "success", "message": "选课记录导入成功"})


def _build_courses_xml(rows):
    root = ET.Element("Classes")
    for cno, cnm, ctm, cpt, tec, pla, share in rows:
        cls = ET.SubElement(root, "class")
        ET.SubElement(cls, "id").text = cno
        ET.SubElement(cls, "name").text = cnm
        ET.SubElement(cls, "credit").text = str(ctm) if ctm else ""
        ET.SubElement(cls, "hours").text = str(cpt) if cpt else ""
        ET.SubElement(cls, "teacher").text = tec
        ET.SubElement(cls, "location").text = pla
        ET.SubElement(cls, "share").text = share if share else ""
    return ET.tostring(root, encoding="unicode")


def _build_students_xml(rows):
    root = ET.Element("Students")
    for sno, snm, sex, sde, pwd in rows:
        student = ET.SubElement(root, "student")
        ET.SubElement(student, "id").text = sno
        ET.SubElement(student, "name").text = snm
        ET.SubElement(student, "sex").text = sex
        ET.SubElement(student, "major").text = sde
    return ET.tostring(root, encoding="unicode")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="College A Local API Server")
    parser.add_argument("--port", type=int, default=8081, help="Server port (default: 8081)")
    args = parser.parse_args()
    PORT = args.port

    server = HTTPServer(("0.0.0.0", PORT), CollegeAHandler)
    print(f"[A-Server] {COLLEGE_NAME} 本地API服务器已启动")
    print(f"[A-Server] 地址: http://localhost:{PORT}")
    print(f"[A-Server] 状态: http://localhost:{PORT}/a/api/status")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[A-Server] 服务器已停止")
        server.server_close()
