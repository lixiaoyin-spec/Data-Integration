"""
集成服务器 — 主程序
基于 XML 技术实现 A(SQL Server)、B(Oracle)、C(MySQL) 三学院异构数据集成

功能:
  1. 汇聚所有学院的共享课程
  2. 跨院选课（学生信息+选课记录写回课程所属学院）
  3. 跨院退选
  4. 全局统计

启动方式: python main.py [--port 8000]
"""
import sys
import os
import json
import argparse
import xml.etree.ElementTree as ET
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote_plus

from config import INTEGRATION_SERVER, COLLEGES, MAX_COURSES_PER_STUDENT
from college_client import CollegeRegistry
from xml_utils import (
    parse_courses_xml, parse_students_xml, count_enrollments_xml,
    build_student_xml, build_enrollment_xml,
)
from course_aggregator import CourseAggregator


class IntegrationHandler(BaseHTTPRequestHandler):
    """集成服务器 HTTP 请求处理器"""

    # ---- 基础通信 ----

    def _send_json(self, data, code=200):
        body = json.dumps(data, ensure_ascii=False)
        self._send(body, "application/json; charset=utf-8", code)

    def _send_xml(self, xml_str, code=200):
        self._send(xml_str, "application/xml; charset=utf-8", code)

    def _send_html(self, html, code=200):
        self._send(html, "text/html; charset=utf-8", code)

    def _send_text(self, text, code=200):
        self._send(text, "text/plain; charset=utf-8", code)

    def _send(self, body, content_type, code):
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

    def _parse_json(self, body):
        try:
            return json.loads(body)
        except (json.JSONDecodeError, ValueError):
            return {}

    def log_message(self, fmt, *args):
        print(f"[Integration] {args[0]}")

    # ---- 路由分发 ----

    def do_GET(self):
        path = urlparse(self.path).path.rstrip("/")

        routes = {
            "/":                  self._handle_dashboard,
            "/api/status":        self._handle_status,
            "/api/colleges":      self._handle_colleges,
            "/api/courses/shared":  self._handle_shared_courses,
            "/api/courses/all":     self._handle_all_courses,
            "/api/courses/college": self._handle_college_courses,
            "/api/courses/aggregated": self._handle_aggregated_courses,
            "/api/students":        self._handle_all_students,
            "/api/students/college": self._handle_college_students,
            "/api/statistics":      self._handle_statistics,
            "/api/transcript":      self._handle_transcript,
        }

        handler = routes.get(path, self._handle_not_found)
        handler()

    def do_POST(self):
        path = urlparse(self.path).path.rstrip("/")

        if path == "/api/login":
            return self._handle_login()
        elif path == "/api/enroll":
            return self._handle_enroll()
        elif path == "/api/drop":
            return self._handle_drop()
        else:
            self._send_json({"error": "Not Found"}, 404)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def _handle_not_found(self):
        self._send_json({"error": "Not Found"}, 404)

    # ================================================================
    # GET / — 集成服务器仪表盘
    # ================================================================
    def _handle_dashboard(self):
        self._send_html(DASHBOARD_HTML)

    # ================================================================
    # GET /api/status — 全局状态
    # ================================================================
    def _handle_status(self):
        statuses = registry.check_all_status()
        online = sum(1 for s in statuses.values() if s.get("online"))
        self._send_json({
            "server": INTEGRATION_SERVER["name"],
            "version": INTEGRATION_SERVER["version"],
            "colleges_total": len(COLLEGES),
            "colleges_online": online,
            "details": statuses,
        })

    # ================================================================
    # GET /api/colleges — 学院列表
    # ================================================================
    def _handle_colleges(self):
        result = []
        for cid, info in COLLEGES.items():
            client = registry.get(cid)
            status = client.check_status()
            result.append({
                "id": cid,
                "name": info["name"],
                "dbms": info["dbms"],
                "base_url": info["base_url"],
                "online": status.get("online", False),
                "students": status.get("students", "?"),
                "courses": status.get("courses", "?"),
                "selections": status.get("selections", "?"),
            })
        self._send_json(result)

    # ================================================================
    # GET /api/courses/shared — 共享课程聚合
    # ================================================================
    def _handle_shared_courses(self):
        """从所有在线学院拉取共享课程并统一展示"""
        params = parse_qs(urlparse(self.path).query)
        filter_college = params.get("college", [None])[0]

        all_courses = []
        for cid, info in COLLEGES.items():
            if filter_college and filter_college.upper() != cid:
                continue
            client = registry.get(cid)
            xml_data = client.get_shared_courses()
            if xml_data:
                courses = parse_courses_xml(xml_data, cid)
                all_courses.extend(courses)

        xml_output = self._courses_to_xml(all_courses)
        if "application/json" in (self.headers.get("Accept") or ""):
            self._send_json({"total": len(all_courses), "courses": all_courses})
        else:
            self._send_xml(xml_output)

    # ================================================================
    # GET /api/courses/all — 全部课程（含非共享）
    # ================================================================
    def _handle_all_courses(self):
        params = parse_qs(urlparse(self.path).query)
        filter_college = params.get("college", [None])[0]

        all_courses = []
        for cid, info in COLLEGES.items():
            if filter_college and filter_college.upper() != cid:
                continue
            client = registry.get(cid)
            status = client.check_status()
            if not status.get("online"):
                continue
            xml_data = client.get_courses()
            if xml_data:
                courses = parse_courses_xml(xml_data, cid)
                all_courses.extend(courses)

        xml_output = self._courses_to_xml(all_courses)
        self._send_xml(xml_output)

    # ================================================================
    # GET /api/courses/college — 特定学院课程
    #     ?college=A
    # ================================================================
    def _handle_college_courses(self):
        params = parse_qs(urlparse(self.path).query)
        cid = params.get("college", [""])[0].upper()

        if not cid or cid not in COLLEGES:
            self._send_json({"error": "请指定有效的学院: A, B, C"}, 400)
            return

        client = registry.get(cid)
        xml_data = client.get_courses()
        if xml_data:
            self._send_xml(xml_data)
        else:
            self._send_json({"error": f"学院{cid}服务器不可用"}, 503)

    # ================================================================
    # GET /api/courses/aggregated — 去重聚合课程（新增）
    #     ?shared_only=1  仅共享课程
    #     ?college=A      筛选指定学院
    # ================================================================
    def _handle_aggregated_courses(self):
        """使用CourseAggregator进行智能去重聚合"""
        params = parse_qs(urlparse(self.path).query)
        shared_only = params.get("shared_only", ["0"])[0] == "1"
        filter_college = params.get("college", [None])[0]

        aggr = CourseAggregator(registry)

        if shared_only:
            aggr.fetch_shared()
        else:
            aggr.fetch_all()

        aggr.normalize().deduplicate()

        stats = aggr.statistics()
        courses = aggr.to_dict_list()

        if filter_college and filter_college.upper() in COLLEGES:
            cid = filter_college.upper()
            courses = [c for c in courses
                       if cid in str(c.get("share_college", ""))]

        xml_output = aggr.to_xml(
            [c for c in aggr._merged
             if not filter_college
             or filter_college.upper() in str(c.get("share_college", ""))]
        )

        if "application/json" in (self.headers.get("Accept") or ""):
            self._send_json({
                "statistics": stats,
                "total": len(courses),
                "courses": courses,
            })
        else:
            self._send_xml(xml_output)

    # ================================================================
    # GET /api/students — 全体学生
    # ================================================================
    def _handle_all_students(self):
        params = parse_qs(urlparse(self.path).query)
        filter_college = params.get("college", [None])[0]

        all_students = []
        for cid, info in COLLEGES.items():
            if filter_college and filter_college.upper() != cid:
                continue
            client = registry.get(cid)
            status = client.check_status()
            if not status.get("online"):
                continue
            xml_data = client.get_students_xml()
            if xml_data:
                students = parse_students_xml(xml_data, cid)
                all_students.extend(students)

        # 构建XML输出
        root = ET.Element("Students")
        for s in all_students:
            stu = ET.SubElement(root, "student")
            ET.SubElement(stu, "id").text = s.get("sno", "")
            ET.SubElement(stu, "name").text = s.get("snm", "")
            ET.SubElement(stu, "sex").text = s.get("sex", "")
            ET.SubElement(stu, "major").text = s.get("major", "")
            ET.SubElement(stu, "college").text = s.get("source_college", "")

        self._send_xml(ET.tostring(root, encoding="unicode"))

    # ================================================================
    # GET /api/students/college — 特定学院学生
    #     ?college=A
    # ================================================================
    def _handle_college_students(self):
        params = parse_qs(urlparse(self.path).query)
        cid = params.get("college", [""])[0].upper()

        if not cid or cid not in COLLEGES:
            self._send_json({"error": "请指定有效的学院: A, B, C"}, 400)
            return

        client = registry.get(cid)
        xml_data = client.get_students_xml()
        if xml_data:
            self._send_xml(xml_data)
        else:
            self._send_json({"error": f"学院{cid}服务器不可用"}, 503)

    # ================================================================
    # POST /api/login — 统一登录
    #     body: acc=xxx&pwd=xxx&college=A
    # ================================================================
    def _handle_login(self):
        body = self._read_body()
        content_type = self.headers.get("Content-Type", "")
        if "application/json" in content_type:
            data = self._parse_json(body)
            acc = data.get("acc", "")
            pwd = data.get("pwd", "")
            college = data.get("college", "").upper()
        else:
            form = self._parse_form(body)
            acc = form.get("acc", "")
            pwd = form.get("pwd", "")
            college = form.get("college", "").upper()

        if not acc or not pwd or not college:
            self._send_json({"status": "fail", "message": "请提供账号、密码和所属学院"}, 400)
            return

        if college not in COLLEGES:
            self._send_json({"status": "fail", "message": f"无效的学院: {college}"}, 400)
            return

        client = registry.get(college)
        result = client.login(acc, pwd)
        result["source_college"] = college
        self._send_json(result, 200 if result.get("status") == "success" else 401)

    # ================================================================
    # POST /api/enroll — 跨院选课（核心功能）
    #     body: {sno, snm, sex, sde, source_college, cno, cnm, target_college}
    #
    # 流程:
    #  1. 检查 source_college 和 target_college 是否在线
    #  2. 若 source != target，构建学生 XML 并写回目标学院 /students/import
    #  3. 构建选课 XML 并写回目标学院 /enrollments/import（跨院）
    #     或调用目标学院 /enroll（本院）
    #  4. 返回统一 JSON { status, message, steps }
    # ================================================================
    def _handle_enroll(self):
        body = self._read_body()
        content_type = self.headers.get("Content-Type", "")
        if "application/json" in content_type:
            data = self._parse_json(body)
        else:
            form = self._parse_form(body)
            data = {
                "sno": form.get("sno", ""),
                "snm": form.get("snm", ""),
                "sex": form.get("sex", ""),
                "sde": form.get("sde", ""),
                "source_college": form.get("source_college", ""),
                "cno": form.get("cno", ""),
                "cnm": form.get("cnm", ""),
                "target_college": form.get("target_college", ""),
            }

        sno = data.get("sno", "")
        snm = data.get("snm", "")
        sex = data.get("sex", "")
        sde = data.get("sde", "")
        source = data.get("source_college", "").upper()
        cno = data.get("cno", "")
        cnm = data.get("cnm", "")
        target = data.get("target_college", "").upper()

        if not all([sno, snm, source, cno, target]):
            self._send_json({
                "status": "fail",
                "message": "缺少必要参数: sno, snm, source_college, cno, target_college",
            }, 400)
            return

        if source not in COLLEGES or target not in COLLEGES:
            self._send_json({"status": "fail", "message": "无效的学院"}, 400)
            return

        steps = []
        is_cross = source != target

        try:
            source_client = registry.get(source)
            target_client = registry.get(target)
            if not source_client or not target_client:
                self._send_json({"status": "fail", "message": "无效的学院"}, 400)
                return

            print(f"[Integration] {'跨院' if is_cross else '本院'}选课: "
                  f"学生 {sno}({source}) -> 课程 {cno}({target})")

            # Step 1: 检查源学院与目标学院是否在线
            source_status = source_client.check_status()
            steps.append({"step": "check_source_college", "result": source_status})
            if not source_status.get("online"):
                self._send_json({
                    "status": "fail",
                    "message": f"源学院{source}服务器不可用",
                    "steps": steps,
                }, 503)
                return

            target_status = target_client.check_status()
            steps.append({"step": "check_target_college", "result": target_status})
            if not target_status.get("online"):
                self._send_json({
                    "status": "fail",
                    "message": f"目标学院{target}服务器不可用",
                    "steps": steps,
                }, 503)
                return

            # Step 2: 跨院时构建学生 XML 并写回目标学院
            if is_cross:
                student_xml = build_student_xml({
                    "sno": sno, "snm": snm, "sex": sex, "sde": sde,
                })
                print(f"[Integration] 学生 XML 写回:\n{student_xml}")
                import_result = target_client.import_student_xml(student_xml)
                steps.append({
                    "step": "import_student",
                    "format": "xml",
                    "result": import_result,
                })
                print(f"[Integration] 学生导入结果: {import_result}")
                if import_result.get("status") != "success":
                    self._send_json({
                        "status": "fail",
                        "message": f"学生导入失败: {import_result.get('message', '未知错误')}",
                        "steps": steps,
                    }, 400)
                    return

            # Step 3: 在目标学院创建选课记录
            if is_cross:
                enroll_xml = build_enrollment_xml({"sno": sno, "cno": cno})
                print(f"[Integration] 选课 XML 写回:\n{enroll_xml}")
                enroll_result = target_client.import_enrollment_xml(enroll_xml)
                steps.append({
                    "step": "import_enrollment",
                    "format": "xml",
                    "result": enroll_result,
                })
            else:
                enroll_result = target_client.enroll(sno, cno)
                steps.append({"step": "enroll", "result": enroll_result})
            print(f"[Integration] 选课结果: {enroll_result}")

            if enroll_result.get("status") == "success":
                if is_cross:
                    message = "跨院选课成功"
                    if cnm or cno:
                        message = f"跨院选课成功: 学生{sno}已选修学院{target}的课程{cnm or cno}"
                else:
                    message = enroll_result.get("message", "选课成功")
                resp = {
                    "status": "success",
                    "message": message,
                    "steps": steps,
                }
                if is_cross:
                    resp["source_college"] = source
                    resp["target_college"] = target
                self._send_json(resp)
            else:
                self._send_json({
                    "status": "fail",
                    "message": f"选课失败: {enroll_result.get('message', '未知错误')}",
                    "steps": steps,
                }, 400)

        except Exception as e:
            print(f"[Integration] 选课异常: {e}")
            self._send_json({
                "status": "fail",
                "message": f"选课失败: {e}",
                "steps": steps,
            }, 500)

    # ================================================================
    # POST /api/drop — 跨院退选
    #     body: {sno, cno, target_college}
    # ================================================================
    def _handle_drop(self):
        body = self._read_body()
        content_type = self.headers.get("Content-Type", "")
        if "application/json" in content_type:
            data = self._parse_json(body)
        else:
            form = self._parse_form(body)
            data = {
                "sno": form.get("sno", ""),
                "cno": form.get("cno", ""),
                "target_college": form.get("target_college", "").upper(),
            }

        sno = data.get("sno", "")
        cno = data.get("cno", "")
        target = data.get("target_college", "").upper()

        if not all([sno, cno, target]):
            self._send_json({
                "status": "fail",
                "message": "缺少必要参数: sno, cno, target_college",
            }, 400)
            return

        if target not in COLLEGES:
            self._send_json({"status": "fail", "message": "无效的学院"}, 400)
            return

        try:
            client = registry.get_client(target)
            if not client:
                self._send_json({"status": "fail", "message": f"无效的学院: {target}"}, 400)
                return

            status = client.check_status()
            if not status.get("online"):
                self._send_json({"status": "fail", "message": f"学院{target}服务器不可用"}, 503)
                return

            print(f"[Integration] 跨院退选: 学生 {sno} -> 课程 {cno}({target})")

            result = client.drop(sno, cno)
            if result.get("status") == "success":
                self._send_json({
                    "status": "success",
                    "message": "退课成功",
                })
            else:
                self._send_json({
                    "status": "fail",
                    "message": f"退课失败: {result.get('message', '未知错误')}",
                }, 400)
        except Exception as e:
            print(f"[Integration] 退课异常: {e}")
            self._send_json({
                "status": "fail",
                "message": f"退课失败: {e}",
            }, 500)

    # ================================================================
    # GET /api/statistics — 全局统计
    # ================================================================
    def _handle_statistics(self):
        """聚合所有学院的统计数据"""
        students_total = 0
        courses_total = 0
        enrollments_total = 0
        details = {}

        try:
            for client in registry.all():
                cid = client.college_id
                info = COLLEGES.get(cid, {})
                detail = {
                    "college_id": cid,
                    "college_name": info.get("name", client.name),
                    "dbms": info.get("dbms", client.dbms),
                    "online": False,
                    "students": 0,
                    "courses": 0,
                    "enrollments": 0,
                }

                try:
                    status = client.check_status()
                    detail["online"] = status.get("online", False)

                    if not detail["online"]:
                        detail["error"] = status.get("error", "服务器不可用")
                        details[cid] = detail
                        continue

                    students_xml = client.get_students()
                    courses_xml = client.get_courses()
                    enrollments_xml = client.get_enrollments()

                    errors = []
                    if students_xml:
                        detail["students"] = len(parse_students_xml(students_xml, cid))
                    else:
                        errors.append("获取学生数据失败")

                    if courses_xml:
                        detail["courses"] = len(parse_courses_xml(courses_xml, cid))
                    else:
                        errors.append("获取课程数据失败")

                    if enrollments_xml:
                        detail["enrollments"] = count_enrollments_xml(enrollments_xml)
                    else:
                        errors.append("获取选课数据失败")

                    if errors:
                        detail["error"] = "；".join(errors)

                    students_total += detail["students"]
                    courses_total += detail["courses"]
                    enrollments_total += detail["enrollments"]

                except Exception as e:
                    print(f"[Integration] 统计学院{cid}异常: {e}")
                    detail["error"] = str(e)

                details[cid] = detail

            self._send_json({
                "students_total": students_total,
                "courses_total": courses_total,
                "enrollments_total": enrollments_total,
                "details": details,
            })
        except Exception as e:
            print(f"[Integration] 全局统计异常: {e}")
            self._send_json({
                "students_total": students_total,
                "courses_total": courses_total,
                "enrollments_total": enrollments_total,
                "details": details,
                "error": str(e),
            }, 500)

    # ================================================================
    # GET /api/transcript — 成绩单
    #     ?sno=xxx&college=A
    # ================================================================
    def _handle_transcript(self):
        params = parse_qs(urlparse(self.path).query)
        sno = params.get("sno", [""])[0]
        college = params.get("college", [""])[0].upper()

        if not sno or not college:
            self._send_json({"error": "请提供 sno 和 college 参数"}, 400)
            return

        if college not in COLLEGES:
            self._send_json({"error": "无效的学院"}, 400)
            return

        client = registry.get(college)
        xml_data = client.get_transcript(sno)
        if xml_data:
            self._send_xml(xml_data)
        else:
            self._send_json({"error": "获取成绩单失败"}, 503)

    # ================================================================
    # 辅助方法
    # ================================================================
    def _courses_to_xml(self, courses):
        root = ET.Element("Classes")
        for c in courses:
            cls = ET.SubElement(root, "class")
            ET.SubElement(cls, "id").text = c.get("cno", "")
            ET.SubElement(cls, "name").text = c.get("cnm", "")
            ET.SubElement(cls, "credit").text = str(c.get("credit", ""))
            ET.SubElement(cls, "hours").text = str(c.get("hours", ""))
            ET.SubElement(cls, "teacher").text = c.get("teacher", "")
            ET.SubElement(cls, "location").text = c.get("location", "")
            ET.SubElement(cls, "share_college").text = c.get("share_college", "")
            ET.SubElement(cls, "share_flag").text = c.get("share_flag", "N")
        return ET.tostring(root, encoding="unicode")


# ================================================================
# 仪表盘 HTML（内嵌前端）
# ================================================================

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>集成教务服务器</title>
<style>
:root{--bg:#0b1120;--panel:#111827;--card:#1e293b;--line:#334155;--text:#e2e8f0;--muted:#94a3b8;--brand:#38bdf8;--brand2:#a78bfa;--good:#22c55e;--warn:#f59e0b;--bad:#ef4444}
*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,system-ui,sans-serif;background:var(--bg);color:var(--text);min-height:100vh}
.wrap{max-width:1280px;margin:0 auto;padding:28px 20px}
header{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;margin-bottom:24px}
h1{margin:0;font-size:26px;background:linear-gradient(135deg,var(--brand),var(--brand2));-webkit-background-clip:text;-webkit-text-fill-color:transparent}
.subtitle{color:var(--muted);font-size:14px;margin-top:4px}
.status-badge{padding:8px 16px;border-radius:999px;border:1px solid rgba(56,189,248,.3);background:rgba(15,23,42,.6);color:#bae6fd;font-size:13px}
.status-badge.online{border-color:rgba(34,197,94,.4);color:#86efac}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:18px;margin-bottom:24px}
.card{background:var(--card);border:1px solid rgba(148,163,184,.12);border-radius:16px;padding:18px}
.card h3{margin:0 0 12px;font-size:15px;color:var(--brand)}
.colleges-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:18px;margin-bottom:24px}
.college-card{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:20px}
.college-card h3{margin:0 0 8px;font-size:17px}
.college-card .dbms{color:var(--muted);font-size:13px}
.college-card .dot{display:inline-block;width:9px;height:9px;border-radius:50%;margin-right:6px}
.dot.on{background:var(--good)}.dot.off{background:var(--bad)}
.college-stats{display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:12px}
.stat-item{text-align:center;padding:8px;background:rgba(15,23,42,.5);border-radius:10px}
.stat-item .val{font-size:20px;font-weight:700;color:var(--brand)}.stat-item .lbl{font-size:11px;color:var(--muted)}
.toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:16px}
.btn{padding:10px 18px;border:none;border-radius:10px;font-weight:600;color:#fff;cursor:pointer;font-size:13px;background:linear-gradient(135deg,var(--brand),var(--brand2))}
.btn:hover{filter:brightness(1.08)}.btn.alt{background:#334155}
.result-area{background:var(--card);border:1px solid var(--line);border-radius:16px;padding:16px;min-height:200px;max-height:500px;overflow:auto}
.result-area pre{margin:0;font-family:Consolas,monospace;font-size:12px;white-space:pre-wrap;word-break:break-all}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:9px 8px;border-bottom:1px solid var(--line);text-align:left}
th{color:#bfdbfe;position:sticky;top:0;background:var(--card)}
.tag{display:inline-block;padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600}
.tag.a{background:rgba(56,189,248,.15);color:#7dd3fc}.tag.b{background:rgba(167,139,250,.15);color:#c4b5fd}
.tag.c{background:rgba(34,197,94,.15);color:#86efac}.tag.y{background:rgba(34,197,94,.12);color:#86efac}
.tag.n{background:rgba(148,163,184,.12);color:#94a3b8}
.form-group{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
.form-group label{font-size:13px;color:var(--muted);min-width:60px}
.form-group input,.form-group select{padding:8px 10px;border-radius:8px;border:1px solid var(--line);background:#0f172a;color:var(--text);font-size:13px}
.loading{color:var(--warn);font-style:italic}
</style>
</head>
<body>
<div class="wrap">
<header>
<div><h1>集成教务服务器</h1><div class="subtitle">A(SQL Server) · B(Oracle) · C(MySQL) 跨院数据集成</div></div>
<div class="status-badge" id="serverStatus">检查中...</div>
</header>

<div class="grid">
<div class="card"><h3>在线学院</h3><div style="font-size:32px;font-weight:700" id="onlineCount">—</div></div>
<div class="card"><h3>学生总数</h3><div style="font-size:32px;font-weight:700" id="totalStudents">—</div></div>
<div class="card"><h3>课程总数</h3><div style="font-size:32px;font-weight:700" id="totalCourses">—</div></div>
<div class="card"><h3>选课总数</h3><div style="font-size:32px;font-weight:700" id="totalSelections">—</div></div>
</div>

<h2 style="margin-bottom:12px">各学院状态</h2>
<div class="colleges-grid" id="collegesGrid">加载中...</div>

<h2 style="margin:20px 0 12px">操作面板</h2>
<div class="toolbar">
<button class="btn" onclick="loadSharedCourses()">共享课程</button>
<button class="btn alt" onclick="loadAllCourses()">全部课程</button>
<button class="btn alt" onclick="loadAllStudents()">全体学生</button>
<button class="btn alt" onclick="loadStatistics()">全局统计</button>
</div>
<div class="result-area" id="resultArea"><pre>点击上方按钮加载数据...</pre></div>

<h2 style="margin:20px 0 12px">跨院选课</h2>
<div class="card">
<div class="form-group">
<label>学号:</label><input id="eSno" placeholder="如 S001" style="width:110px"/>
<label>姓名:</label><input id="eSnm" placeholder="张三" style="width:100px"/>
<label>性别:</label><select id="eSex"><option value="男">男</option><option value="女">女</option></select>
<label>专业:</label><input id="eSde" placeholder="计算机科学" style="width:130px"/>
<label>所属学院:</label><select id="eSource"><option value="A">学院A</option><option value="B">学院B</option><option value="C">学院C</option></select>
</div>
<div class="form-group">
<label>课程号:</label><input id="eCno" placeholder="如 C001" style="width:110px"/>
<label>课程名:</label><input id="eCnm" placeholder="数据库原理" style="width:130px"/>
<label>目标学院:</label><select id="eTarget"><option value="A">学院A</option><option value="B" selected>学院B</option><option value="C">学院C</option></select>
<button class="btn" onclick="doEnroll()">执行跨院选课</button>
</div>
<div class="result-area" id="enrollResult" style="margin-top:10px;min-height:60px;max-height:200px"><pre>选课结果将显示在这里...</pre></div>
</div>

<h2 style="margin:20px 0 12px">跨院退选</h2>
<div class="card">
<div class="form-group">
<label>学号:</label><input id="dSno" placeholder="如 S001" style="width:110px"/>
<label>课程号:</label><input id="dCno" placeholder="如 C001" style="width:110px"/>
<label>所属学院:</label><select id="dCollege"><option value="A">学院A</option><option value="B" selected>学院B</option><option value="C">学院C</option></select>
<button class="btn" onclick="doDrop()" style="background:linear-gradient(135deg,#f87171,#ef4444)">执行退选</button>
</div>
<div class="result-area" id="dropResult" style="margin-top:10px;min-height:60px;max-height:200px"><pre>退选结果将显示在这里...</pre></div>
</div>
</div>

<script>
const API = '';
async function api(url, opts) {const r = await fetch(API + url, opts); return {ok: r.ok, status: r.status, text: await r.text()};}
function $(id) {return document.getElementById(id);}

async function init() {
  const r = await api('/api/status');
  if (r.ok) {
    const d = JSON.parse(r.text);
    $('serverStatus').textContent = '在线学院: ' + d.colleges_online + '/' + d.colleges_total;
    $('serverStatus').className = 'status-badge ' + (d.colleges_online > 0 ? 'online' : '');
  }
  loadColleges();
  loadStatistics();
}
async function loadColleges() {
  const r = await api('/api/colleges');
  if (!r.ok) return;
  const list = JSON.parse(r.text);
  let html = '';
  for (const c of list) {
    html += '<div class="college-card"><h3><span class="dot ' + (c.online ? 'on' : 'off') + '"></span>' + c.name + ' <span class="tag ' + c.id.toLowerCase() + '">' + c.id + '</span></h3>';
    html += '<div class="dbms">' + c.dbms + ' | ' + c.base_url + ' | ' + (c.online ? '在线' : '离线') + '</div>';
    html += '<div class="college-stats"><div class="stat-item"><div class="val">' + c.students + '</div><div class="lbl">学生</div></div>';
    html += '<div class="stat-item"><div class="val">' + c.courses + '</div><div class="lbl">课程</div></div>';
    html += '<div class="stat-item"><div class="val">' + c.selections + '</div><div class="lbl">选课</div></div></div></div>';
  }
  $('collegesGrid').innerHTML = html;
}
async function loadStatistics() {
  const r = await api('/api/statistics');
  if (!r.ok) return;
  const d = JSON.parse(r.text);
  const colleges = Object.values(d.details || {});
  const onlineCount = colleges.filter(c => c.online).length;
  $('onlineCount').textContent = onlineCount + '/' + colleges.length;
  $('totalStudents').textContent = d.students_total;
  $('totalCourses').textContent = d.courses_total;
  $('totalSelections').textContent = d.enrollments_total;
}
async function loadSharedCourses() {
  const r = await api('/api/courses/shared');
  $('resultArea').innerHTML = r.ok ? xmlToTable(r.text, '共享课程') : '<pre>加载失败</pre>';
}
async function loadAllCourses() {
  const r = await api('/api/courses/all');
  $('resultArea').innerHTML = r.ok ? xmlToTable(r.text, '全部课程') : '<pre>加载失败</pre>';
}
async function loadAllStudents() {
  const r = await api('/api/students');
  $('resultArea').innerHTML = r.ok ? xmlToTable(r.text, '全体学生') : '<pre>加载失败</pre>';
}
async function doEnroll() {
  const body = JSON.stringify({
    sno: $('eSno').value.trim(), snm: $('eSnm').value.trim(), sex: $('eSex').value,
    sde: $('eSde').value.trim(), source_college: $('eSource').value,
    cno: $('eCno').value.trim(), cnm: $('eCnm').value.trim(), target_college: $('eTarget').value
  });
  const r = await api('/api/enroll', {method: 'POST', headers: {'Content-Type': 'application/json'}, body});
  $('enrollResult').innerHTML = '<pre>' + JSON.stringify(JSON.parse(r.text), null, 2) + '</pre>';
}
async function doDrop() {
  const body = JSON.stringify({
    sno: $('dSno').value.trim(), cno: $('dCno').value.trim(), target_college: $('dCollege').value
  });
  const r = await api('/api/drop', {method: 'POST', headers: {'Content-Type': 'application/json'}, body});
  $('dropResult').innerHTML = '<pre>' + JSON.stringify(JSON.parse(r.text), null, 2) + '</pre>';
}
function xmlToTable(xml, title) {
  try {
    const d = new DOMParser().parseFromString(xml, 'application/xml');
    if (d.querySelector('parsererror')) return '<pre>' + escapeHtml(xml) + '</pre>';
    let out = '<h3 style="margin:0 0 10px">' + title + ' (' + d.querySelectorAll('class,student').length + ' 条)</h3><table><thead><tr>';
    if (d.querySelector('class')) {
      out += '<th>课程号</th><th>课程名</th><th>学分</th><th>学时</th><th>教师</th><th>地点</th><th>来源学院</th><th>共享</th></tr></thead><tbody>';
      d.querySelectorAll('class').forEach(n => {
        const shareCollege = text(n, 'share_college') || text(n, 'share') || '-';
        const shareFlag = text(n, 'share_flag') || text(n, 'shareFlag') || 'N';
        out += '<tr><td>' + text(n, 'id') + '</td><td>' + text(n, 'name') + '</td><td>' + text(n, 'credit') + '</td><td>' + text(n, 'hours') + '</td><td>' + text(n, 'teacher') + '</td><td>' + text(n, 'location') + '</td><td><span class="tag ' + shareCollege.toLowerCase() + '">' + shareCollege + '</span></td><td><span class="tag ' + (shareFlag === 'Y' ? 'y' : 'n') + '">' + shareFlag + '</span></td></tr>';
      });
    } else if (d.querySelector('student')) {
      out += '<th>学号</th><th>姓名</th><th>性别</th><th>专业</th><th>学院</th></tr></thead><tbody>';
      d.querySelectorAll('student').forEach(n => {
        const college = text(n, 'college') || '-';
        out += '<tr><td>' + text(n, 'id') + '</td><td>' + text(n, 'name') + '</td><td>' + text(n, 'sex') + '</td><td>' + text(n, 'major') + '</td><td><span class="tag ' + college.toLowerCase() + '">' + college + '</span></td></tr>';
      });
    }
    out += '</tbody></table>'; return out;
  } catch(e) {return '<pre>' + escapeHtml(xml) + '</pre>';}
}
function text(p, s) {const e = p.querySelector(s); return e ? e.textContent : '';}
function escapeHtml(s) {return s.replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));}
init();
</script>
</body>
</html>"""


# ================================================================
# 全局对象
# ================================================================
registry = CollegeRegistry()


# ================================================================
# 启动入口
# ================================================================
def main():
    parser = argparse.ArgumentParser(description="集成教务服务器")
    parser.add_argument("--port", type=int, default=INTEGRATION_SERVER["port"],
                        help=f"Server port (default: {INTEGRATION_SERVER['port']})")
    args = parser.parse_args()

    host = INTEGRATION_SERVER["host"]
    port = args.port

    server = HTTPServer((host, port), IntegrationHandler)
    print("=" * 55)
    print(f"  {INTEGRATION_SERVER['name']} v{INTEGRATION_SERVER['version']}")
    print(f"  地址: http://localhost:{port}")
    print(f"  仪表盘: http://localhost:{port}/")
    print(f"  状态: http://localhost:{port}/api/status")
    print(f"  文档: http://localhost:{port}/api/colleges")
    print("=" * 55)
    print(f"  注册学院:")
    for cid, info in COLLEGES.items():
        print(f"    [{cid}] {info['name']} ({info['dbms']}) -> {info['base_url']}")
    print("=" * 55)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[Integration] 服务器已停止")
        server.server_close()


if __name__ == "__main__":
    main()
