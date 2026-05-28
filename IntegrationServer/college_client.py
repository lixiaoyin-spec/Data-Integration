"""
集成服务器 — 学院客户端模块
负责与各学院的本地HTTP服务器通信
"""
import json
import requests
from config import COLLEGES, HTTP_TIMEOUT


class CollegeClient:
    """与单个学院服务器通信的客户端"""

    def __init__(self, college_id):
        info = COLLEGES.get(college_id)
        if not info:
            raise ValueError(f"未知的学院: {college_id}")
        self.college_id = college_id
        self.name = info["name"]
        self.dbms = info["dbms"]
        self.base_url = info["base_url"].rstrip("/")
        self.endpoints = info["endpoints"]

    def _url(self, key):
        ep = self.endpoints.get(key)
        if not ep:
            return None
        return f"{self.base_url}{ep}"

    def _get(self, key, params=None):
        url = self._url(key)
        if not url:
            return None
        try:
            r = requests.get(url, params=params, timeout=HTTP_TIMEOUT)
            return r
        except requests.RequestException as e:
            print(f"[Client] GET {url} 失败: {e}")
            return None

    def _post(self, key, data=None, json_data=None):
        url = self._url(key)
        if not url:
            return None
        try:
            if json_data:
                r = requests.post(url, json=json_data, timeout=HTTP_TIMEOUT)
            else:
                r = requests.post(url, data=data, timeout=HTTP_TIMEOUT)
            return r
        except requests.RequestException as e:
            print(f"[Client] POST {url} 失败: {e}")
            return None

    def _post_xml(self, key, xml_str):
        """POST XML 到指定端点并解析 JSON 响应"""
        url = self._url(key)
        if not url:
            return {"status": "fail", "message": "端点未配置"}
        if not xml_str or not str(xml_str).strip():
            return {"status": "fail", "message": "XML 内容为空"}
        try:
            r = requests.post(
                url,
                data=xml_str.encode("utf-8"),
                headers={"Content-Type": "application/xml; charset=utf-8"},
                timeout=HTTP_TIMEOUT,
            )
            try:
                return r.json()
            except ValueError:
                return {"status": "fail", "message": "响应格式错误"}
        except requests.RequestException as e:
            print(f"[Client] POST {url} 失败: {e}")
            return {"status": "fail", "message": f"请求失败: {e}"}

    # ---- 状态 ----

    def check_status(self):
        """检查学院服务器是否在线"""
        r = self._get("status")
        if r and r.status_code == 200:
            try:
                data = r.json()
                data["online"] = True
                return data
            except ValueError:
                return {"online": True, "status": "running"}
        return {
            "online": False,
            "college_id": self.college_id,
            "college_name": self.name,
            "error": "无法连接",
        }

    # ---- 登录 ----

    def login(self, acc, pwd):
        r = self._post("login", data={"acc": acc, "pwd": pwd})
        if r and r.status_code == 200:
            try:
                return r.json()
            except ValueError:
                return {"status": "fail", "message": "响应格式错误"}
        return {"status": "fail", "message": "服务器不可用"}

    # ---- 课程 ----

    def get_courses(self):
        """获取全部课程"""
        r = self._get("courses")
        if r and r.status_code == 200:
            return r.text
        return None

    def get_shared_courses(self):
        """获取共享课程"""
        r = self._get("shared")
        if r and r.status_code == 200:
            return r.text
        return None

    # ---- 学生 ----

    def get_students(self):
        """获取学生列表"""
        r = self._get("students")
        if r and r.status_code == 200:
            return r.text
        return None

    def get_students_xml(self):
        """获取标准集成格式的学生XML"""
        r = self._get("students_xml")
        if r:
            return r.text
        # 降级到普通学生接口
        return self.get_students()

    def get_courses_xml(self):
        """获取标准集成格式的课程XML"""
        r = self._get("courses_xml")
        if r:
            return r.text
        return self.get_courses()

    def get_selections_xml(self):
        """获取标准集成格式的选课XML"""
        r = self._get("selections_xml")
        if r:
            return r.text
        return None

    def get_enrollments(self):
        """获取选课记录（XML）"""
        r = self._get("selections_xml")
        if r and r.status_code == 200:
            return r.text
        return None

    # ---- 选课/退课 ----

    def enroll(self, sid, cid):
        """选课"""
        r = self._post("enroll", data={"sid": sid, "cid": cid})
        if r:
            try:
                return r.json()
            except ValueError:
                return {"status": "fail", "message": "响应格式错误"}
        return {"status": "fail", "message": "服务器不可用"}

    def enroll_course(self, enroll_data):
        """在目标学院创建选课记录（字典参数）"""
        url = self._url("enroll")
        if not url:
            return {"status": "fail", "message": "端点未配置"}
        if not isinstance(enroll_data, dict):
            return {"status": "fail", "message": "参数格式错误，需要字典类型"}
        sno = enroll_data.get("sno", "")
        cno = enroll_data.get("cno", "")
        if not sno or not cno:
            return {"status": "fail", "message": "缺少学号或课程号"}
        try:
            r = requests.post(
                url,
                data={"sid": sno, "cid": cno},
                timeout=HTTP_TIMEOUT,
            )
            try:
                return r.json()
            except ValueError:
                return {"status": "fail", "message": "响应格式错误"}
        except requests.RequestException as e:
            print(f"[Client] POST {url} 失败: {e}")
            return {"status": "fail", "message": f"请求失败: {e}"}

    def drop(self, sid, cid):
        """退课"""
        r = self._post("drop", data={"sid": sid, "cid": cid})
        if r:
            try:
                return r.json()
            except ValueError:
                return {"status": "fail", "message": "响应格式错误"}
        return {"status": "fail", "message": "服务器不可用"}

    # ---- 成绩单 ----

    def get_transcript(self, sno):
        """获取学生成绩单"""
        r = self._get("transcript", params={"sno": sno})
        if r and r.status_code == 200:
            return r.text
        return None

    # ---- 统计 ----

    def get_statistics(self):
        """获取学院统计信息"""
        r = self._get("statistics")
        if r and r.status_code == 200:
            try:
                return r.json()
            except ValueError:
                return None
        return None

    # ---- 跨院数据导入 ----

    def import_student(self, student_data, snm=None, sex=None, sde=None, pwd=None):
        """将学生信息导入到目标学院（跨院选课前调用）

        支持两种调用方式:
          import_student({"sno": "S001", "snm": "张三", "sex": "男", "sde": "计算机科学"})
          import_student("S001", "张三", "男", "计算机科学")
        """
        if isinstance(student_data, dict):
            payload = dict(student_data)
            if "pwd" not in payload and payload.get("sno"):
                payload.setdefault("pwd", payload["sno"])
            return self._post_import_student(payload)

        sno = student_data
        data = {"sno": sno, "snm": snm, "sex": sex, "sde": sde, "pwd": pwd or sno}
        r = self._post("import_student", json_data=data)
        if r:
            try:
                return r.json()
            except ValueError:
                return {"status": "fail"}
        return {"status": "fail", "message": "服务器不可用"}

    def _post_import_student(self, student_data):
        """POST /students/import 并返回 JSON 响应（字典参数）"""
        url = self._url("import_student")
        if not url:
            return {"status": "fail", "message": "端点未配置"}
        if not student_data.get("sno") or not student_data.get("snm"):
            return {"status": "fail", "message": "缺少学号或姓名"}
        try:
            r = requests.post(url, json=student_data, timeout=HTTP_TIMEOUT)
            try:
                return r.json()
            except ValueError:
                return {"status": "fail", "message": "响应格式错误"}
        except requests.RequestException as e:
            print(f"[Client] POST {url} 失败: {e}")
            return {"status": "fail", "message": f"请求失败: {e}"}

    def import_enrollment(self, sno, cno, grd=""):
        """将选课记录导入到目标学院"""
        r = self._post("import_enrollment", json_data={"sno": sno, "cno": cno, "grd": grd})
        if r:
            try:
                return r.json()
            except ValueError:
                return {"status": "fail"}
        return {"status": "fail", "message": "服务器不可用"}

    def import_student_xml(self, xml_str):
        """通过 XML 将学生信息导入目标学院（跨院选课 XML 写回）"""
        return self._post_xml("import_student", xml_str)

    def import_enrollment_xml(self, xml_str):
        """通过 XML 将选课记录导入目标学院（跨院选课 XML 写回）"""
        return self._post_xml("import_enrollment", xml_str)


class CollegeRegistry:
    """学院注册中心，管理所有学院客户端"""

    def __init__(self):
        self._clients = {}
        for cid in COLLEGES:
            self._clients[cid] = CollegeClient(cid)

    def get(self, college_id):
        return self._clients.get(college_id)

    def get_client(self, college_id):
        """获取指定学院的客户端（get 的别名）"""
        return self.get(college_id)

    def all(self):
        return list(self._clients.values())

    def all_ids(self):
        return list(self._clients.keys())

    def check_all_status(self):
        """检查所有学院服务器状态"""
        results = {}
        for cid, client in self._clients.items():
            results[cid] = client.check_status()
        return results

    def get_online_clients(self):
        """获取所有在线的学院客户端"""
        online = []
        for cid, client in self._clients.items():
            status = client.check_status()
            if status.get("online"):
                online.append(client)
        return online
