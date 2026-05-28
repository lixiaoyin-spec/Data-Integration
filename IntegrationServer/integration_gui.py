"""
集成教务系统 — 集成端GUI
基于 Tkinter，连接集成服务器 (端口 8000) 的 REST API
功能：登录、系统状态、课程管理、学生管理、跨院选课、跨院退选、统计、成绩单查询
"""
import os
import sys
import json
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from urllib.request import urlopen, Request
from urllib.error import URLError
from urllib.parse import urlencode
import xml.dom.minidom as minidom

INTEGRATION_URL = "http://localhost:8000"


def api_get(path, params=None):
    """调用集成服务器 GET API"""
    url = f"{INTEGRATION_URL}{path}"
    if params:
        qs = urlencode(params)
        url = f"{url}?{qs}"
    req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except URLError as e:
        return None, str(e)


def api_post(path, data=None, json_data=None):
    """调用集成服务器 POST API"""
    url = f"{INTEGRATION_URL}{path}"
    if json_data:
        body = json.dumps(json_data, ensure_ascii=False).encode("utf-8")
        req = Request(url, data=body, headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
        })
    elif data:
        body = urlencode(data).encode("utf-8")
        req = Request(url, data=body, headers={
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        })
    else:
        req = Request(url, headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=10) as resp:
            return resp.status, resp.read().decode("utf-8")
    except URLError as e:
        return None, str(e)


def fmt_json(text):
    """尝试格式化JSON，失败则返回原文"""
    try:
        obj = json.loads(text)
        return json.dumps(obj, ensure_ascii=False, indent=2)
    except (json.JSONDecodeError, ValueError):
        return text


def fmt_xml(text):
    """尝试格式化XML，失败则返回原文"""
    try:
        dom = minidom.parseString(text)
        return dom.toprettyxml(indent="  ")
    except Exception:
        return text


def parse_statistics_response(data):
    """解析 GET /api/statistics 响应"""
    details_raw = data.get("details", {})
    if isinstance(details_raw, dict):
        details = sorted(details_raw.values(), key=lambda d: d.get("college_id", ""))
    else:
        details = list(details_raw or [])

    online_count = sum(1 for d in details if d.get("online"))
    return {
        "students_total": data.get("students_total", 0),
        "courses_total": data.get("courses_total", 0),
        "enrollments_total": data.get("enrollments_total", 0),
        "online_count": online_count,
        "colleges_total": len(details),
        "details": details,
    }


class LoginWindow:
    """登录窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("集成教务系统 - 登录")
        self.root.geometry("440x380")
        self.root.resizable(False, False)
        self._center()
        self._build_ui()

    def _center(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build_ui(self):
        style = ttk.Style()
        style.configure("Title.TLabel", font=("Microsoft YaHei", 18, "bold"))
        style.configure("Form.TLabel", font=("Microsoft YaHei", 11))

        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=24)
        ttk.Label(title_frame, text="集成教务系统",
                  style="Title.TLabel").pack()
        ttk.Label(title_frame, text="A(SQL Server) · B(Oracle) · C(MySQL) 跨院数据集成",
                  font=("Microsoft YaHei", 9), foreground="gray").pack()

        form_frame = ttk.Frame(self.root)
        form_frame.pack(pady=16)

        ttk.Label(form_frame, text="账  号：", style="Form.TLabel").grid(
            row=0, column=0, sticky="e", pady=8, padx=(0, 8))
        self.acc_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.acc_var,
                  font=("Microsoft YaHei", 11), width=20).grid(row=0, column=1)

        ttk.Label(form_frame, text="密  码：", style="Form.TLabel").grid(
            row=1, column=0, sticky="e", pady=8, padx=(0, 8))
        self.pwd_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.pwd_var, show="*",
                  font=("Microsoft YaHei", 11), width=20).grid(row=1, column=1)

        ttk.Label(form_frame, text="所属学院：", style="Form.TLabel").grid(
            row=2, column=0, sticky="e", pady=8, padx=(0, 8))
        self.college_var = tk.StringVar(value="A")
        college_combo = ttk.Combobox(form_frame, textvariable=self.college_var,
                                     values=["A", "B", "C"], state="readonly",
                                     font=("Microsoft YaHei", 11), width=18)
        college_combo.grid(row=2, column=1)

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=18)
        ttk.Button(btn_frame, text="登  录", command=self._login,
                   width=14).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="退  出", command=self.root.quit,
                   width=14).pack(side="left", padx=8)

        ttk.Label(self.root, text="默认管理员: admin / admin (任意学院)",
                  font=("Microsoft YaHei", 8), foreground="gray").pack()
        ttk.Label(self.root, text="学生账号: S001~S050 (对应学院存在即可)",
                  font=("Microsoft YaHei", 8), foreground="gray").pack()

    def _login(self):
        acc = self.acc_var.get().strip()
        pwd = self.pwd_var.get().strip()
        college = self.college_var.get().strip()

        if not acc or not pwd:
            messagebox.showwarning("提示", "请输入账号和密码")
            return

        status, body = api_post("/api/login", json_data={
            "acc": acc, "pwd": pwd, "college": college,
        })

        if status == 200:
            try:
                result = json.loads(body)
                if result.get("status") == "success":
                    self.root.destroy()
                    role = result.get("role", "student")
                    MainWindow(role, acc, college).run()
                else:
                    messagebox.showerror("登录失败",
                                         result.get("message", "账号或密码错误"))
            except ValueError:
                messagebox.showerror("错误", "服务器响应格式异常")
        else:
            messagebox.showerror("连接失败",
                                 f"集成服务器不可用\n请先启动: python IntegrationServer/main.py")

    def run(self):
        self.root.mainloop()


class MainWindow:
    """主窗口（含多标签页）"""

    def __init__(self, role, acc, college):
        self.role = role
        self.current_acc = acc
        self.current_college = college
        self.root = tk.Tk()
        self.root.title(f"集成教务系统 [角色: {role}] [学院: {college}] [账号: {acc}]")
        self.root.geometry("1100x720")
        self._center()
        self._build_ui()
        self._refresh_status()

    def _center(self):
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"+{x}+{y}")

    def _build_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=6, pady=6)

        self._build_status_tab()
        self._build_course_tab()
        self._build_student_tab()
        self._build_enroll_tab()
        self._build_drop_tab()
        self._build_statistics_tab()
        self._build_transcript_tab()

    # ================================================================
    # Tab 1: 系统状态
    # ================================================================
    def _build_status_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  系统状态  ")

        top_bar = ttk.Frame(tab)
        top_bar.pack(fill="x", padx=12, pady=8)

        self.status_label = ttk.Label(top_bar, text="集成服务器: 检查中...",
                                      font=("Microsoft YaHei", 12, "bold"))
        self.status_label.pack(side="left")

        ttk.Button(top_bar, text="刷新状态", command=self._refresh_status).pack(side="right")

        # 全局统计卡片
        self.stats_frame = ttk.Frame(tab)
        self.stats_frame.pack(fill="x", padx=12, pady=4)

        self.stat_cards = {}
        for i, (key, title) in enumerate([
            ("online", "在线学院"), ("total_students", "学生总数"),
            ("total_courses", "课程总数"), ("total_selections", "选课总数"),
        ]):
            card = ttk.LabelFrame(self.stats_frame, text=title)
            card.grid(row=0, column=i, padx=6, pady=4, sticky="nsew")
            self.stats_frame.grid_columnconfigure(i, weight=1)
            val_label = ttk.Label(card, text="—",
                                  font=("Microsoft YaHei", 22, "bold"),
                                  foreground="#2563eb")
            val_label.pack(pady=12, padx=20)
            self.stat_cards[key] = val_label

        # 学院详情卡片
        self.colleges_frame = ttk.Frame(tab)
        self.colleges_frame.pack(fill="both", expand=True, padx=12, pady=4)

    # ================================================================
    # Tab 2: 课程管理
    # ================================================================
    def _build_course_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  课程管理  ")

        # 操作栏
        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", padx=12, pady=8)

        ttk.Label(toolbar, text="课程类型:", font=("Microsoft YaHei", 10)).pack(side="left")
        self.course_type_var = tk.StringVar(value="shared")
        ttk.Radiobutton(toolbar, text="共享课程", variable=self.course_type_var,
                        value="shared").pack(side="left", padx=4)
        ttk.Radiobutton(toolbar, text="全部课程", variable=self.course_type_var,
                        value="all").pack(side="left", padx=4)
        ttk.Radiobutton(toolbar, text="聚合去重", variable=self.course_type_var,
                        value="aggregated").pack(side="left", padx=4)

        ttk.Label(toolbar, text="  学院筛选:").pack(side="left", padx=(20, 0))
        self.course_college_var = tk.StringVar(value="")
        ttk.Combobox(toolbar, textvariable=self.course_college_var,
                     values=["", "A", "B", "C"], state="readonly",
                     width=6).pack(side="left")

        ttk.Button(toolbar, text="查询课程",
                   command=self._load_courses).pack(side="left", padx=10)

        self.course_shared_only_var = tk.IntVar(value=0)
        ttk.Checkbutton(toolbar, text="仅共享课程(聚合)",
                        variable=self.course_shared_only_var).pack(side="left", padx=4)

        # 视图切换
        self.course_view_var = tk.StringVar(value="table")
        ttk.Radiobutton(toolbar, text="表格视图", variable=self.course_view_var,
                        value="table").pack(side="right", padx=2)
        ttk.Radiobutton(toolbar, text="XML视图", variable=self.course_view_var,
                        value="xml").pack(side="right", padx=2)
        ttk.Label(toolbar, text="视图:").pack(side="right")

        # 结果区域
        self.course_tree_frame = ttk.Frame(tab)
        self.course_tree_frame.pack(fill="both", expand=True, padx=12, pady=4)

        self.course_text = scrolledtext.ScrolledText(
            tab, font=("Consolas", 11), wrap="none")
        self.course_text.pack(fill="both", expand=True, padx=12, pady=4)

    def _load_courses(self):
        course_type = self.course_type_var.get()
        college = self.course_college_var.get()

        for w in self.course_tree_frame.winfo_children():
            w.destroy()

        if course_type == "shared":
            params = {}
            if college:
                params["college"] = college
            status, body = api_get("/api/courses/shared", params or None)
            title = "共享课程"
        elif course_type == "aggregated":
            params = {}
            if self.course_shared_only_var.get():
                params["shared_only"] = "1"
            if college:
                params["college"] = college
            status, body = api_get("/api/courses/aggregated", params or None)
            title = "聚合去重课程"
        elif college:
            status, body = api_get("/api/courses/college", {"college": college})
            title = f"学院{college}课程"
        else:
            status, body = api_get("/api/courses/all")
            title = "全部课程"

        if status != 200 or not body:
            self.course_text.delete("1.0", tk.END)
            self.course_text.insert("1.0", f"[错误] 无法获取课程数据: {body}")
            return

        if self.course_view_var.get() == "xml":
            self.course_text.delete("1.0", tk.END)
            self.course_text.insert("1.0", fmt_xml(body))
            return

        self.course_text.delete("1.0", tk.END)
        self._render_course_tree(body, title)

    def _render_course_tree(self, xml_str, title):
        try:
            dom = minidom.parseString(xml_str)
            classes = dom.getElementsByTagName("class")
            if not classes:
                self.course_text.insert("1.0", f"{title}: 无课程数据\n\n{fmt_xml(xml_str)}")
                return
        except Exception:
            self.course_text.insert("1.0", fmt_xml(xml_str))
            return

        columns = ("课程号", "课程名", "学分", "学时", "教师", "地点", "来源学院", "共享")
        tree = ttk.Treeview(self.course_tree_frame, columns=columns, show="headings",
                            height=18)
        widths = [80, 180, 60, 60, 100, 100, 90, 60]
        for col, w in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(self.course_tree_frame, orient="vertical", command=tree.yview)
        hsb = ttk.Scrollbar(self.course_tree_frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        self.course_tree_frame.grid_rowconfigure(0, weight=1)
        self.course_tree_frame.grid_columnconfigure(0, weight=1)

        for cls in classes:
            def tn(tag):
                el = cls.getElementsByTagName(tag)
                return el[0].firstChild.data if el and el[0].firstChild else ""
            vals = (tn("id"), tn("name"), tn("credit"), tn("hours"),
                    tn("teacher"), tn("location"),
                    tn("share_college") or "-",
                    tn("share_flag") or "N")
            tree.insert("", "end", values=vals)

        count = len(classes)
        ttk.Label(self.course_tree_frame, text=f"{title}: 共 {count} 条",
                  font=("Microsoft YaHei", 9), foreground="gray").grid(
            row=2, column=0, sticky="w")

    # ================================================================
    # Tab 3: 学生管理
    # ================================================================
    def _build_student_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  学生管理  ")

        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", padx=12, pady=8)

        ttk.Label(toolbar, text="学院筛选:").pack(side="left")
        self.student_college_var = tk.StringVar(value="")
        ttk.Combobox(toolbar, textvariable=self.student_college_var,
                     values=["", "A", "B", "C"], state="readonly",
                     width=6).pack(side="left", padx=4)

        ttk.Button(toolbar, text="查询学生",
                   command=self._load_students).pack(side="left", padx=10)

        self.student_view_var = tk.StringVar(value="table")
        ttk.Radiobutton(toolbar, text="表格视图", variable=self.student_view_var,
                        value="table").pack(side="right", padx=2)
        ttk.Radiobutton(toolbar, text="XML视图", variable=self.student_view_var,
                        value="xml").pack(side="right", padx=2)
        ttk.Label(toolbar, text="视图:").pack(side="right")

        self.student_tree_frame = ttk.Frame(tab)
        self.student_tree_frame.pack(fill="both", expand=True, padx=12, pady=4)

        self.student_text = scrolledtext.ScrolledText(
            tab, font=("Consolas", 11), wrap="none")
        self.student_text.pack(fill="both", expand=True, padx=12, pady=4)

    def _load_students(self):
        college = self.student_college_var.get()
        for w in self.student_tree_frame.winfo_children():
            w.destroy()

        if college:
            status, body = api_get("/api/students/college", {"college": college})
            title = f"学院{college}学生"
        else:
            status, body = api_get("/api/students")
            title = "全体学生"

        if status != 200 or not body:
            self.student_text.delete("1.0", tk.END)
            self.student_text.insert("1.0", f"[错误] 无法获取学生数据: {body}")
            return

        if self.student_view_var.get() == "xml":
            self.student_text.delete("1.0", tk.END)
            self.student_text.insert("1.0", fmt_xml(body))
            return

        self.student_text.delete("1.0", tk.END)
        self._render_student_tree(body, title)

    def _render_student_tree(self, xml_str, title):
        try:
            dom = minidom.parseString(xml_str)
            students = dom.getElementsByTagName("student")
            if not students:
                self.student_text.insert("1.0", f"{title}: 无学生数据\n\n{fmt_xml(xml_str)}")
                return
        except Exception:
            self.student_text.insert("1.0", fmt_xml(xml_str))
            return

        columns = ("学号", "姓名", "性别", "专业", "学院")
        tree = ttk.Treeview(self.student_tree_frame, columns=columns, show="headings",
                            height=18)
        widths = [100, 120, 60, 180, 80]
        for col, w in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(self.student_tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.student_tree_frame.grid_rowconfigure(0, weight=1)
        self.student_tree_frame.grid_columnconfigure(0, weight=1)

        for stu in students:
            def tn(tag):
                el = stu.getElementsByTagName(tag)
                return el[0].firstChild.data if el and el[0].firstChild else ""
            vals = (tn("id"), tn("name"), tn("sex"), tn("major"),
                    tn("college") or "-")
            tree.insert("", "end", values=vals)

        ttk.Label(self.student_tree_frame, text=f"{title}: 共 {len(students)} 条",
                  font=("Microsoft YaHei", 9), foreground="gray").grid(
            row=2, column=0, sticky="w")

    # ================================================================
    # Tab 4: 跨院选课
    # ================================================================
    def _build_enroll_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  跨院选课  ")

        form = ttk.LabelFrame(tab, text="选课信息")
        form.pack(fill="x", padx=12, pady=8)

        fields = [
            ("学号 *", "e_sno", 14),
            ("姓名 *", "e_snm", 14),
            ("性别", "e_sex", 8),
            ("专业", "e_sde", 16),
            ("课程号 *", "e_cno", 14),
            ("课程名", "e_cnm", 16),
            ("所属学院 *", "e_source", 6),
            ("目标学院 *", "e_target", 6),
        ]

        row_frame = None
        for i, (label, attr, width) in enumerate(fields):
            if i % 4 == 0:
                row_frame = ttk.Frame(form)
                row_frame.pack(fill="x", padx=10, pady=3)
            ttk.Label(row_frame, text=label, font=("Microsoft YaHei", 9)).pack(
                side="left", padx=(0, 2))
            if label.startswith("性别"):
                var = tk.StringVar(value="男")
                setattr(self, attr, var)
                ttk.Combobox(row_frame, textvariable=var, values=["男", "女"],
                             state="readonly", width=width,
                             font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 10))
            elif label.endswith("学院 *"):
                default = "A" if "source" in attr else "B"
                var = tk.StringVar(value=default)
                setattr(self, attr, var)
                ttk.Combobox(row_frame, textvariable=var, values=["A", "B", "C"],
                             state="readonly", width=width,
                             font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 10))
            else:
                var = tk.StringVar()
                setattr(self, attr, var)
                ttk.Entry(row_frame, textvariable=var, width=width,
                          font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 10))

        btn_frame = ttk.Frame(form)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="执行跨院选课", command=self._do_enroll).pack(side="left", padx=6)
        ttk.Button(btn_frame, text="清空表单", command=self._clear_enroll).pack(side="left", padx=6)

        self.enroll_result = scrolledtext.ScrolledText(
            tab, font=("Consolas", 11), height=12)
        self.enroll_result.pack(fill="both", expand=True, padx=12, pady=4)
        self.enroll_result.insert("1.0", "选课结果将显示在这里...\n\n"
                                  "提示: 跨院选课会自动将学生信息导入目标学院，再创建选课记录。")

    def _do_enroll(self):
        sno = self.e_sno.get().strip()
        snm = self.e_snm.get().strip()
        cno = self.e_cno.get().strip()
        source = self.e_source.get().strip()
        target = self.e_target.get().strip()

        if not all([sno, snm, cno, source, target]):
            messagebox.showwarning("提示", "请填写所有带 * 的必填项")
            return

        if source == target:
            if not messagebox.askyesno("确认", "源学院与目标学院相同，将直接在本院选课。确认继续?"):
                return

        data = {
            "sno": sno,
            "snm": snm,
            "sex": self.e_sex.get(),
            "sde": self.e_sde.get().strip(),
            "source_college": source,
            "cno": cno,
            "cnm": self.e_cnm.get().strip(),
            "target_college": target,
        }

        status, body = api_post("/api/enroll", json_data=data)
        self.enroll_result.delete("1.0", tk.END)
        self.enroll_result.insert("1.0", fmt_json(body))

    def _clear_enroll(self):
        for attr in ["e_sno", "e_snm", "e_sde", "e_cno", "e_cnm"]:
            getattr(self, attr).set("")
        self.e_sex.set("男")
        self.e_source.set("A")
        self.e_target.set("B")

    # ================================================================
    # Tab 5: 跨院退选
    # ================================================================
    def _build_drop_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  跨院退选  ")

        form = ttk.LabelFrame(tab, text="退选信息")
        form.pack(fill="x", padx=12, pady=8)

        row = ttk.Frame(form)
        row.pack(fill="x", padx=10, pady=8)
        ttk.Label(row, text="学号 *", font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 2))
        self.d_sno = tk.StringVar()
        ttk.Entry(row, textvariable=self.d_sno, width=16,
                  font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 20))

        ttk.Label(row, text="课程号 *", font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 2))
        self.d_cno = tk.StringVar()
        ttk.Entry(row, textvariable=self.d_cno, width=16,
                  font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 20))

        ttk.Label(row, text="目标学院 *", font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 2))
        self.d_college = tk.StringVar(value="B")
        ttk.Combobox(row, textvariable=self.d_college, values=["A", "B", "C"],
                     state="readonly", width=6,
                     font=("Microsoft YaHei", 10)).pack(side="left", padx=(0, 10))

        ttk.Button(row, text="执行退选", command=self._do_drop).pack(side="left", padx=10)
        ttk.Button(row, text="清空", command=lambda: (
            self.d_sno.set(""), self.d_cno.set(""), self.d_college.set("B")
        )).pack(side="left")

        self.drop_result = scrolledtext.ScrolledText(
            tab, font=("Consolas", 11), height=12)
        self.drop_result.pack(fill="both", expand=True, padx=12, pady=4)
        self.drop_result.insert("1.0", "退选结果将显示在这里...")

    def _do_drop(self):
        sno = self.d_sno.get().strip()
        cno = self.d_cno.get().strip()
        college = self.d_college.get().strip()

        if not all([sno, cno, college]):
            messagebox.showwarning("提示", "请填写所有带 * 的必填项")
            return

        if not messagebox.askyesno("确认退选",
                                   f"确认退选?\n学号: {sno}\n课程号: {cno}\n学院: {college}"):
            return

        status, body = api_post("/api/drop", json_data={
            "sno": sno, "cno": cno, "target_college": college,
        })
        self.drop_result.delete("1.0", tk.END)
        self.drop_result.insert("1.0", fmt_json(body))

    # ================================================================
    # Tab 6: 统计查询
    # ================================================================
    def _build_statistics_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  统计查询  ")

        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", padx=12, pady=8)
        ttk.Button(toolbar, text="刷新统计",
                   command=self._load_statistics).pack(side="left")
        self.stat_view_var = tk.StringVar(value="formatted")
        ttk.Radiobutton(toolbar, text="格式化视图", variable=self.stat_view_var,
                        value="formatted").pack(side="right", padx=2)
        ttk.Radiobutton(toolbar, text="JSON原始", variable=self.stat_view_var,
                        value="json").pack(side="right", padx=2)
        ttk.Label(toolbar, text="视图:").pack(side="right")

        self.stat_tree_frame = ttk.Frame(tab)
        self.stat_tree_frame.pack(fill="both", expand=True, padx=12, pady=4)

        self.stat_text = scrolledtext.ScrolledText(
            tab, font=("Consolas", 11))
        self.stat_text.pack(fill="both", expand=True, padx=12, pady=4)

    def _load_statistics(self):
        status, body = api_get("/api/statistics")

        if status != 200 or not body:
            self.stat_text.delete("1.0", tk.END)
            self.stat_text.insert("1.0", f"[错误] 无法获取统计: {body}")
            return

        for w in self.stat_tree_frame.winfo_children():
            w.destroy()

        try:
            data = json.loads(body)
        except ValueError:
            self.stat_text.delete("1.0", tk.END)
            self.stat_text.insert("1.0", body)
            return

        if self.stat_view_var.get() == "json":
            self.stat_text.delete("1.0", tk.END)
            self.stat_text.insert("1.0", fmt_json(body))
            return

        self.stat_text.delete("1.0", tk.END)

        stats = parse_statistics_response(data)
        details = stats["details"]

        columns = ("学院", "DBMS", "状态", "学生数", "课程数", "选课数")
        tree = ttk.Treeview(self.stat_tree_frame, columns=columns, show="headings",
                            height=8)
        widths = [100, 100, 120, 100, 100, 100]
        for col, w in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(self.stat_tree_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.stat_tree_frame.grid_rowconfigure(0, weight=1)
        self.stat_tree_frame.grid_columnconfigure(0, weight=1)

        for d in details:
            status_text = "在线" if d.get("online") else "离线"
            if d.get("error"):
                status_text = f"{status_text} ({d['error']})"
            tree.insert("", "end", values=(
                d.get("college_name", ""),
                d.get("dbms", ""),
                status_text,
                d.get("students", 0),
                d.get("courses", 0),
                d.get("enrollments", 0),
            ))

        summary_text = (
            f"===== 全局统计汇总 =====\n\n"
            f"在线学院:  {stats['online_count']} / {stats['colleges_total']}\n"
            f"学生总数:  {stats['students_total']}\n"
            f"课程总数:  {stats['courses_total']}\n"
            f"选课总数:  {stats['enrollments_total']}\n"
        )
        ttk.Label(self.stat_tree_frame, text=summary_text,
                  font=("Microsoft YaHei", 10), foreground="#2563eb",
                  justify="left").grid(row=1, column=0, sticky="w", pady=10)

    # ================================================================
    # Tab 7: 成绩单查询
    # ================================================================
    def _build_transcript_tab(self):
        tab = ttk.Frame(self.notebook)
        self.notebook.add(tab, text="  成绩单查询  ")

        toolbar = ttk.Frame(tab)
        toolbar.pack(fill="x", padx=12, pady=8)

        ttk.Label(toolbar, text="学号:", font=("Microsoft YaHei", 10)).pack(side="left")
        self.t_sno = tk.StringVar()
        ttk.Entry(toolbar, textvariable=self.t_sno, width=14,
                  font=("Microsoft YaHei", 10)).pack(side="left", padx=(2, 12))

        ttk.Label(toolbar, text="学院:", font=("Microsoft YaHei", 10)).pack(side="left")
        self.t_college = tk.StringVar(value="A")
        ttk.Combobox(toolbar, textvariable=self.t_college, values=["A", "B", "C"],
                     state="readonly", width=6,
                     font=("Microsoft YaHei", 10)).pack(side="left", padx=(2, 10))

        ttk.Button(toolbar, text="查询成绩单",
                   command=self._load_transcript).pack(side="left")

        self.transcript_view_var = tk.StringVar(value="xml")
        ttk.Radiobutton(toolbar, text="XML视图", variable=self.transcript_view_var,
                        value="xml").pack(side="right", padx=2)
        ttk.Radiobutton(toolbar, text="表格视图", variable=self.transcript_view_var,
                        value="table").pack(side="right", padx=2)
        ttk.Label(toolbar, text="视图:").pack(side="right")

        self.transcript_tree_frame = ttk.Frame(tab)
        self.transcript_tree_frame.pack(fill="both", expand=True, padx=12, pady=4)

        self.transcript_text = scrolledtext.ScrolledText(
            tab, font=("Consolas", 11))
        self.transcript_text.pack(fill="both", expand=True, padx=12, pady=4)

    def _load_transcript(self):
        sno = self.t_sno.get().strip()
        college = self.t_college.get().strip()

        if not sno:
            messagebox.showwarning("提示", "请输入学号")
            return

        status, body = api_get("/api/transcript", {"sno": sno, "college": college})

        for w in self.transcript_tree_frame.winfo_children():
            w.destroy()

        if status != 200 or not body:
            self.transcript_text.delete("1.0", tk.END)
            self.transcript_text.insert("1.0", f"[错误] 无法获取成绩单: {body}")
            return

        if self.transcript_view_var.get() == "xml":
            self.transcript_text.delete("1.0", tk.END)
            self.transcript_text.insert("1.0", fmt_xml(body))
            return

        self.transcript_text.delete("1.0", tk.END)
        try:
            dom = minidom.parseString(body)
            items = (dom.getElementsByTagName("transcript") or
                     dom.getElementsByTagName("enrollment") or
                     dom.getElementsByTagName("choice") or [])
            if not items:
                items = dom.getElementsByTagName("Transcript")
            if not items:
                self.transcript_text.insert("1.0", fmt_xml(body))
                return
        except Exception:
            self.transcript_text.insert("1.0", fmt_xml(body))
            return

        columns = ("课程号", "课程名", "成绩", "学分")
        tree = ttk.Treeview(self.transcript_tree_frame, columns=columns,
                            show="headings", height=14)
        widths = [100, 200, 80, 80]
        for col, w in zip(columns, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")

        vsb = ttk.Scrollbar(self.transcript_tree_frame, orient="vertical",
                            command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.transcript_tree_frame.grid_rowconfigure(0, weight=1)
        self.transcript_tree_frame.grid_columnconfigure(0, weight=1)

        def tn(el, tag):
            nodes = el.getElementsByTagName(tag)
            return nodes[0].firstChild.data if nodes and nodes[0].firstChild else ""

        for item in items:
            if item.tagName in ("Transcript", "transcript"):
                for child in item.childNodes:
                    if child.nodeType == child.ELEMENT_NODE:
                        vals = (tn(child, "cid") or tn(child, "cno") or tn(child, "id"),
                                tn(child, "cnm") or tn(child, "name") or "",
                                tn(child, "score") or tn(child, "grd") or "",
                                tn(child, "credit") or tn(child, "cpt") or "")
                        tree.insert("", "end", values=vals)
            elif item.tagName in ("enrollment", "choice"):
                vals = (tn(item, "cid") or tn(item, "cno") or tn(item, "id"),
                        tn(item, "cnm") or tn(item, "name") or "",
                        tn(item, "score") or tn(item, "grd") or "",
                        tn(item, "credit") or tn(item, "cpt") or "")
                tree.insert("", "end", values=vals)

        ttk.Label(self.transcript_tree_frame,
                  text=f"学生 {sno} 在学院{college}的成绩单",
                  font=("Microsoft YaHei", 9), foreground="gray").grid(
            row=1, column=0, sticky="w")

    # ================================================================
    # 系统状态刷新
    # ================================================================
    def _refresh_status(self):
        status, body = api_get("/api/status")
        if status == 200:
            try:
                data = json.loads(body)
                online = data.get("colleges_online", 0)
                total = data.get("colleges_total", 0)
                self.status_label.config(
                    text=f"集成服务器: 在线 | {online}/{total} 学院在线",
                    foreground="#16a34a")
            except ValueError:
                self.status_label.config(text="集成服务器: 响应异常", foreground="#dc2626")
        else:
            self.status_label.config(
                text="集成服务器: 离线 — 请先启动 main.py", foreground="#dc2626")

        self._refresh_college_cards()
        self._load_statistics_summary()

    def _refresh_college_cards(self):
        for w in self.colleges_frame.winfo_children():
            w.destroy()

        status, body = api_get("/api/colleges")
        if status != 200:
            ttk.Label(self.colleges_frame,
                      text="无法获取学院信息，请确认集成服务器已启动",
                      font=("Microsoft YaHei", 10), foreground="#dc2626").pack(pady=20)
            return

        try:
            colleges = json.loads(body)
        except ValueError:
            return

        for c in colleges:
            cid = c.get("id", "?")
            online = c.get("online", False)
            dot_color = "#16a34a" if online else "#dc2626"
            status_text = "在线" if online else "离线"

            card = ttk.LabelFrame(self.colleges_frame,
                                  text=f"学院{cid} — {c.get('name', '')}")
            card.pack(side="left", padx=8, pady=6, fill="both", expand=True)

            header = ttk.Frame(card)
            header.pack(fill="x", padx=10, pady=4)
            ttk.Label(header, text=f"● {status_text}",
                      foreground=dot_color,
                      font=("Microsoft YaHei", 10, "bold")).pack(side="left")
            ttk.Label(header, text=f"  {c.get('dbms', '')}",
                      foreground="gray", font=("Microsoft YaHei", 9)).pack(side="right")

            ttk.Label(card, text=f"地址: {c.get('base_url', '')}",
                      font=("Microsoft YaHei", 8), foreground="gray").pack(padx=10)

            stats_inner = ttk.Frame(card)
            stats_inner.pack(padx=10, pady=6)
            for key, label in [("students", "学生"), ("courses", "课程"),
                               ("selections", "选课")]:
                sf = ttk.Frame(stats_inner)
                sf.pack(side="left", padx=10)
                ttk.Label(sf, text=str(c.get(key, "?")),
                          font=("Microsoft YaHei", 16, "bold"),
                          foreground="#2563eb").pack()
                ttk.Label(sf, text=label,
                          font=("Microsoft YaHei", 8), foreground="gray").pack()

    def _load_statistics_summary(self):
        status, body = api_get("/api/statistics")
        if status != 200:
            return
        try:
            data = json.loads(body)
            stats = parse_statistics_response(data)
            self.stat_cards["online"].config(
                text=f"{stats['online_count']}/{stats['colleges_total']}")
            self.stat_cards["total_students"].config(
                text=str(stats["students_total"]))
            self.stat_cards["total_courses"].config(
                text=str(stats["courses_total"]))
            self.stat_cards["total_selections"].config(
                text=str(stats["enrollments_total"]))
        except ValueError:
            pass

    def run(self):
        self.root.mainloop()


def main():
    """启动集成端GUI"""
    print("=" * 55)
    print("  集成教务系统 — 集成端GUI")
    print("  连接集成服务器: http://localhost:8000")
    print("  请确保集成服务器已启动: python IntegrationServer/main.py")
    print("=" * 55)
    LoginWindow().run()


if __name__ == "__main__":
    main()
