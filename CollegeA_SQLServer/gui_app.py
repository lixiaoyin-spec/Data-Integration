"""
College A (SQL Server) - 教学管理系统 GUI
功能：登录、学生管理、课程管理、选课管理、退选课程、XML集成、统计
"""
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
from db_manager import DatabaseManager
from xml_handler import XMLHandler
from config import COLLEGE_ID, COLLEGE_NAME


class LoginWindow:
    """登录窗口"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title(f"{COLLEGE_NAME} - 教学管理系统 登录")
        self.root.geometry("420x320")
        self.root.resizable(False, False)

        # 居中
        self.root.update_idletasks()
        w = self.root.winfo_width()
        h = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() - w) // 2
        y = (self.root.winfo_screenheight() - h) // 2
        self.root.geometry(f"+{x}+{y}")

        self._build_ui()

    def _build_ui(self):
        # 标题
        title_frame = ttk.Frame(self.root)
        title_frame.pack(pady=20)
        ttk.Label(title_frame, text=f"学院A 教学管理系统",
                  font=("Microsoft YaHei", 16, "bold")).pack()
        ttk.Label(title_frame, text="基于 SQL Server",
                  font=("Microsoft YaHei", 10)).pack()

        # 登录表单
        form_frame = ttk.Frame(self.root)
        form_frame.pack(pady=20)

        ttk.Label(form_frame, text="账  号：", font=("Microsoft YaHei", 11)).grid(
            row=0, column=0, sticky="e", pady=8)
        self.account_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.account_var,
                  font=("Microsoft YaHei", 11), width=18).grid(row=0, column=1, padx=8)

        ttk.Label(form_frame, text="密  码：", font=("Microsoft YaHei", 11)).grid(
            row=1, column=0, sticky="e", pady=8)
        self.pwd_var = tk.StringVar()
        ttk.Entry(form_frame, textvariable=self.pwd_var, show="*",
                  font=("Microsoft YaHei", 11), width=18).grid(row=1, column=1, padx=8)

        # 按钮
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=15)
        ttk.Button(btn_frame, text="登  录", command=self._login,
                   width=12).pack(side="left", padx=8)
        ttk.Button(btn_frame, text="退  出", command=self.root.quit,
                   width=12).pack(side="left", padx=8)

        # 提示
        ttk.Label(self.root, text="默认管理员: admin / admin",
                  font=("Microsoft YaHei", 8), foreground="gray").pack()
        ttk.Label(self.root, text="学生账号: S001~S050 / stu001~stu050",
                  font=("Microsoft YaHei", 8), foreground="gray").pack()

    def _login(self):
        acc = self.account_var.get().strip()
        pwd = self.pwd_var.get().strip()
        if not acc or not pwd:
            messagebox.showwarning("提示", "请输入账号和密码")
            return

        db = DatabaseManager()
        db.connect()
        ok, role, sno = db.authenticate(acc, pwd)
        db.close()

        if ok:
            self.root.destroy()
            MainWindow(role, sno).run()
        else:
            messagebox.showerror("登录失败", "账号或密码错误")

    def run(self):
        self.root.mainloop()


class MainWindow:
    """主窗口（含多标签页）"""

    def __init__(self, role, sno):
        self.role = role
        self.current_sno = sno  # 当前登录学生的学号
        self.root = tk.Tk()
        self.root.title(f"{COLLEGE_NAME} - 教学管理系统 [角色: {role}]")
        self.root.geometry("1000x620")
        self.root.minsize(900, 550)

        self.db = DatabaseManager()
        self.db.connect()

        self._build_menu()
        self._build_notebook()
        self._refresh_all()

    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="刷新全部数据", command=self._refresh_all)
        file_menu.add_separator()
        file_menu.add_command(label="退出系统", command=self._on_exit)
        menubar.add_cascade(label="文件", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="关于", command=lambda: messagebox.showinfo(
            "关于", f"{COLLEGE_NAME}\n教学管理系统 v1.0\n基于SQL Server + XML数据集成"))
        menubar.add_cascade(label="帮助", menu=help_menu)

        self.root.config(menu=menubar)
        self.root.protocol("WM_DELETE_WINDOW", self._on_exit)

    def _build_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)

        # 标签页1: 学生管理
        self.tab_student = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_student, text="学生管理")
        self._build_student_tab()

        # 标签页2: 课程管理
        self.tab_course = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_course, text="课程管理")
        self._build_course_tab()

        # 标签页3: 选课管理
        self.tab_selection = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_selection, text="选课管理")
        self._build_selection_tab()

        # 标签页4: 退选课程
        self.tab_withdraw = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_withdraw, text="退选课程")
        self._build_withdraw_tab()

        # 标签页5: XML集成
        self.tab_xml = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_xml, text="XML数据集成")
        self._build_xml_tab()

        # 标签页6: 统计信息
        self.tab_stats = ttk.Frame(self.notebook)
        self.notebook.add(self.tab_stats, text="统计信息")
        self._build_stats_tab()

    # ================================================================
    # 标签页1: 学生管理
    # ================================================================
    def _build_student_tab(self):
        # 工具栏
        toolbar = ttk.Frame(self.tab_student)
        toolbar.pack(fill="x", padx=5, pady=5)

        ttk.Button(toolbar, text="新增学生", command=self._add_student_dialog).pack(
            side="left", padx=3)
        ttk.Button(toolbar, text="编辑选中", command=self._edit_student_dialog).pack(
            side="left", padx=3)
        ttk.Button(toolbar, text="删除选中", command=self._delete_student).pack(
            side="left", padx=3)
        ttk.Button(toolbar, text="刷新", command=self._refresh_student_tab).pack(
            side="left", padx=20)

        # 搜索框
        ttk.Label(toolbar, text="搜索：").pack(side="left", padx=(20, 2))
        self.student_search_var = tk.StringVar()
        ttk.Entry(toolbar, textvariable=self.student_search_var, width=12).pack(
            side="left", padx=2)
        ttk.Button(toolbar, text="查找", command=self._search_student).pack(
            side="left", padx=3)

        # Treeview
        columns = ("Sno", "Snm", "Sex", "Sde", "Pwd")
        self.student_tree = ttk.Treeview(self.tab_student, columns=columns,
                                          show="headings", height=18)
        self.student_tree.heading("Sno", text="学号")
        self.student_tree.heading("Snm", text="姓名")
        self.student_tree.heading("Sex", text="性别")
        self.student_tree.heading("Sde", text="专业")
        self.student_tree.heading("Pwd", text="密码")

        self.student_tree.column("Sno", width=100)
        self.student_tree.column("Snm", width=120)
        self.student_tree.column("Sex", width=60)
        self.student_tree.column("Sde", width=150)
        self.student_tree.column("Pwd", width=100)

        scrollbar = ttk.Scrollbar(self.tab_student, orient="vertical",
                                   command=self.student_tree.yview)
        self.student_tree.configure(yscrollcommand=scrollbar.set)

        self.student_tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

    def _refresh_student_tab(self):
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)
        for row in self.db.get_all_students():
            self.student_tree.insert("", "end", values=row)

    def _add_student_dialog(self):
        dialog = StudentDialog(self.root, "新增学生")
        self.root.wait_window(dialog)
        if dialog.result:
            try:
                self.db.add_student(*dialog.result)
                self._refresh_student_tab()
                messagebox.showinfo("成功", "学生添加成功")
            except Exception as e:
                messagebox.showerror("错误", f"添加失败: {e}")

    def _edit_student_dialog(self):
        sel = self.student_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选中一个学生")
            return
        values = self.student_tree.item(sel[0])["values"]
        dialog = StudentDialog(self.root, "编辑学生", values)
        self.root.wait_window(dialog)
        if dialog.result:
            try:
                sno = values[0]
                self.db.update_student(sno, *dialog.result[1:])
                self._refresh_student_tab()
                messagebox.showinfo("成功", "学生信息更新成功")
            except Exception as e:
                messagebox.showerror("错误", f"更新失败: {e}")

    def _delete_student(self):
        sel = self.student_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选中一个学生")
            return
        values = self.student_tree.item(sel[0])["values"]
        if messagebox.askyesno("确认删除", f"确定要删除学生 {values[1]}({values[0]}) 吗？\n将同时删除其选课记录和登录账号。"):
            self.db.delete_student(values[0])
            self._refresh_student_tab()
            messagebox.showinfo("成功", "学生已删除")

    def _search_student(self):
        keyword = self.student_search_var.get().strip()
        if not keyword:
            self._refresh_student_tab()
            return
        for item in self.student_tree.get_children():
            self.student_tree.delete(item)
        for row in self.db.get_all_students():
            if (keyword.lower() in str(row[0]).lower() or
                keyword in str(row[1]) or
                keyword in str(row[3])):
                self.student_tree.insert("", "end", values=row)

    # ================================================================
    # 标签页2: 课程管理
    # ================================================================
    def _build_course_tab(self):
        toolbar = ttk.Frame(self.tab_course)
        toolbar.pack(fill="x", padx=5, pady=5)

        ttk.Button(toolbar, text="新增课程", command=self._add_course_dialog).pack(
            side="left", padx=3)
        ttk.Button(toolbar, text="编辑选中", command=self._edit_course_dialog).pack(
            side="left", padx=3)
        ttk.Button(toolbar, text="删除选中", command=self._delete_course).pack(
            side="left", padx=3)
        ttk.Button(toolbar, text="刷新", command=self._refresh_course_tab).pack(
            side="left", padx=20)

        ttk.Label(toolbar, text="学院筛选：").pack(side="left", padx=(20, 2))
        self.course_filter_var = tk.StringVar(value="全部")
        filter_combo = ttk.Combobox(toolbar, textvariable=self.course_filter_var,
                                     values=["全部", "A", "B", "C"],
                                     state="readonly", width=6)
        filter_combo.pack(side="left", padx=2)
        filter_combo.bind("<<ComboboxSelected>>", lambda e: self._refresh_course_tab())

        columns = ("Cno", "Cnm", "Ctm", "Cpt", "Tec", "Pla", "Share")
        self.course_tree = ttk.Treeview(self.tab_course, columns=columns,
                                         show="headings", height=18)
        self.course_tree.heading("Cno", text="课程号")
        self.course_tree.heading("Cnm", text="课程名")
        self.course_tree.heading("Ctm", text="学分")
        self.course_tree.heading("Cpt", text="学时")
        self.course_tree.heading("Tec", text="授课教师")
        self.course_tree.heading("Pla", text="地点")
        self.course_tree.heading("Share", text="共享来源")

        widths = [80, 140, 50, 50, 140, 50, 80]
        for col, w in zip(columns, widths):
            self.course_tree.column(col, width=w)

        scrollbar = ttk.Scrollbar(self.tab_course, orient="vertical",
                                   command=self.course_tree.yview)
        self.course_tree.configure(yscrollcommand=scrollbar.set)

        self.course_tree.pack(side="left", fill="both", expand=True, padx=(5, 0), pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

    def _refresh_course_tab(self):
        for item in self.course_tree.get_children():
            self.course_tree.delete(item)
        flt = self.course_filter_var.get()
        for row in self.db.get_all_courses():
            if flt == "全部" or row[6] == flt:
                self.course_tree.insert("", "end", values=row)

    def _add_course_dialog(self):
        dialog = CourseDialog(self.root, "新增课程")
        self.root.wait_window(dialog)
        if dialog.result:
            try:
                self.db.add_course(*dialog.result)
                self._refresh_course_tab()
                messagebox.showinfo("成功", "课程添加成功")
            except Exception as e:
                messagebox.showerror("错误", f"添加失败: {e}")

    def _edit_course_dialog(self):
        sel = self.course_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选中一门课程")
            return
        values = self.course_tree.item(sel[0])["values"]
        dialog = CourseDialog(self.root, "编辑课程", values)
        self.root.wait_window(dialog)
        if dialog.result:
            try:
                cno = values[0]
                self.db.update_course(cno, *dialog.result[1:])
                self._refresh_course_tab()
                messagebox.showinfo("成功", "课程信息更新成功")
            except Exception as e:
                messagebox.showerror("错误", f"更新失败: {e}")

    def _delete_course(self):
        sel = self.course_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选中一门课程")
            return
        values = self.course_tree.item(sel[0])["values"]
        if messagebox.askyesno("确认删除", f"确定要删除课程 {values[1]}({values[0]}) 吗？"):
            self.db.delete_course(values[0])
            self._refresh_course_tab()
            messagebox.showinfo("成功", "课程已删除")

    # ================================================================
    # 标签页3: 选课管理
    # ================================================================
    def _build_selection_tab(self):
        # 上方：选课操作区
        top_frame = ttk.Frame(self.tab_selection)
        top_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(top_frame, text="选择学生：", font=("Microsoft YaHei", 10)).pack(
            side="left", padx=(0, 5))
        self.sel_student_var = tk.StringVar()
        self.sel_student_combo = ttk.Combobox(top_frame,
                                               textvariable=self.sel_student_var,
                                               state="readonly", width=15)
        self.sel_student_combo.pack(side="left", padx=3)

        # 仅管理员和教师可以替任意学生选课；学生只能自己选
        if self.role == "学生":
            self.sel_student_combo["values"] = [self.current_sno]
            self.sel_student_var.set(self.current_sno)
            self.sel_student_combo.config(state="disabled")
        else:
            students = self.db.get_all_students()
            self.sel_student_combo["values"] = [s[0] for s in students]

        ttk.Button(top_frame, text="加载可选课程", command=self._load_available_courses).pack(
            side="left", padx=15)

        ttk.Separator(top_frame, orient="vertical").pack(side="left", fill="y", padx=10)

        self.sel_info_label = ttk.Label(top_frame, text="", font=("Microsoft YaHei", 9))
        self.sel_info_label.pack(side="left", padx=5)

        # 中间：选课/已选双列表
        mid_frame = ttk.Frame(self.tab_selection)
        mid_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # 可选课程列表
        avail_frame = ttk.LabelFrame(mid_frame, text="可选课程")
        avail_frame.pack(side="left", fill="both", expand=True, padx=3)

        columns = ("Cno", "Cnm", "Ctm", "Tec", "Share")
        self.avail_tree = ttk.Treeview(avail_frame, columns=columns,
                                        show="headings", height=14)
        self.avail_tree.heading("Cno", text="课程号")
        self.avail_tree.heading("Cnm", text="课程名")
        self.avail_tree.heading("Ctm", text="学分")
        self.avail_tree.heading("Tec", text="授课教师")
        self.avail_tree.heading("Share", text="来源学院")
        for col, w in zip(columns, [80, 140, 50, 120, 70]):
            self.avail_tree.column(col, width=w)
        self.avail_tree.pack(fill="both", expand=True)

        # 中间按钮
        btn_mid = ttk.Frame(mid_frame)
        btn_mid.pack(side="left", padx=8)
        ttk.Button(btn_mid, text=">> 选课 >>", command=self._do_select_course,
                   width=14).pack(pady=10)

        # 已选课程列表
        sel_frame = ttk.LabelFrame(mid_frame, text="已选课程")
        sel_frame.pack(side="right", fill="both", expand=True, padx=3)

        columns2 = ("Cno", "Cnm", "Ctm", "Tec", "Grd", "Share")
        self.sel_tree = ttk.Treeview(sel_frame, columns=columns2,
                                      show="headings", height=14)
        self.sel_tree.heading("Cno", text="课程号")
        self.sel_tree.heading("Cnm", text="课程名")
        self.sel_tree.heading("Ctm", text="学分")
        self.sel_tree.heading("Tec", text="授课教师")
        self.sel_tree.heading("Grd", text="成绩")
        self.sel_tree.heading("Share", text="来源学院")
        for col, w in zip(columns2, [80, 140, 50, 120, 60, 70]):
            self.sel_tree.column(col, width=w)
        self.sel_tree.pack(fill="both", expand=True)

        # 下方提示
        ttk.Label(self.tab_selection,
                  text="提示：在左侧选择课程后点击「选课」按钮即可完成选课。每名学生最多选5门课。",
                  font=("Microsoft YaHei", 8), foreground="gray").pack(pady=3)

    def _load_available_courses(self):
        sno = self.sel_student_var.get()
        if not sno:
            messagebox.showwarning("提示", "请先选择一名学生")
            return

        # 显示学生信息
        student = self.db.get_student(sno)
        if student:
            self.sel_info_label.config(
                text=f"当前学生: {student[1]} | 专业: {student[3]} | 已选: {self.db.get_student_selection_count(sno)}/5 门")

        # 可选课程 = 所有课程 - 已选课程
        all_courses = self.db.get_all_courses()
        selected = self.db.get_student_selections(sno)
        selected_cnos = {s[0] for s in selected}

        self.avail_tree.delete(*self.avail_tree.get_children())
        for row in all_courses:
            if row[0] not in selected_cnos:
                self.avail_tree.insert("", "end", values=(
                    row[0], row[1], row[2], row[4], row[6]))

        # 已选课程
        self.sel_tree.delete(*self.sel_tree.get_children())
        for row in selected:
            self.sel_tree.insert("", "end", values=(
                row[0], row[1], row[2], row[3], row[4] if row[4] else "-", row[5]))

    def _do_select_course(self):
        sno = self.sel_student_var.get()
        if not sno:
            messagebox.showwarning("提示", "请先选择一名学生")
            return

        sel = self.avail_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请在左侧可选课程中选择一门课程")
            return

        # 检查选课数量上限
        if self.db.get_student_selection_count(sno) >= 5:
            messagebox.showwarning("提示", "选课数量已达上限（5门），请先退选其他课程")
            return

        values = self.avail_tree.item(sel[0])["values"]
        cno = values[0]
        try:
            self.db.add_selection(sno, cno)
            self._load_available_courses()
        except Exception as e:
            messagebox.showerror("错误", f"选课失败: {e}")

    # ================================================================
    # 标签页4: 退选课程
    # ================================================================
    def _build_withdraw_tab(self):
        top_frame = ttk.Frame(self.tab_withdraw)
        top_frame.pack(fill="x", padx=5, pady=5)

        ttk.Label(top_frame, text="选择学生：", font=("Microsoft YaHei", 10)).pack(
            side="left", padx=(0, 5))
        self.wd_student_var = tk.StringVar()
        self.wd_student_combo = ttk.Combobox(top_frame,
                                              textvariable=self.wd_student_var,
                                              state="readonly", width=15)
        self.wd_student_combo.pack(side="left", padx=3)

        if self.role == "学生":
            self.wd_student_combo["values"] = [self.current_sno]
            self.wd_student_var.set(self.current_sno)
            self.wd_student_combo.config(state="disabled")
        else:
            students = self.db.get_all_students()
            self.wd_student_combo["values"] = [s[0] for s in students]

        ttk.Button(top_frame, text="加载已选课程", command=self._load_withdraw_courses).pack(
            side="left", padx=15)

        self.wd_info_label = ttk.Label(top_frame, text="", font=("Microsoft YaHei", 9))
        self.wd_info_label.pack(side="left", padx=5)

        # 已选课程列表
        list_frame = ttk.Frame(self.tab_withdraw)
        list_frame.pack(fill="both", expand=True, padx=5, pady=5)

        columns = ("Cno", "Cnm", "Ctm", "Tec", "Grd", "Share")
        self.wd_tree = ttk.Treeview(list_frame, columns=columns,
                                     show="headings", height=16)
        self.wd_tree.heading("Cno", text="课程号")
        self.wd_tree.heading("Cnm", text="课程名")
        self.wd_tree.heading("Ctm", text="学分")
        self.wd_tree.heading("Tec", text="授课教师")
        self.wd_tree.heading("Grd", text="成绩")
        self.wd_tree.heading("Share", text="来源学院")
        for col, w in zip(columns, [80, 140, 50, 120, 60, 70]):
            self.wd_tree.column(col, width=w)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical",
                                   command=self.wd_tree.yview)
        self.wd_tree.configure(yscrollcommand=scrollbar.set)
        self.wd_tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # 退选按钮
        btn_frame = ttk.Frame(self.tab_withdraw)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="退选选中课程", command=self._do_withdraw_course,
                   width=16).pack(side="left", padx=5)
        ttk.Button(btn_frame, text="退选全部课程", command=self._do_withdraw_all,
                   width=16).pack(side="left", padx=5)

        ttk.Label(self.tab_withdraw,
                  text="提示：退选课程会同时删除对应的选课记录。已有成绩的课程建议谨慎退选。",
                  font=("Microsoft YaHei", 8), foreground="gray").pack(pady=3)

    def _load_withdraw_courses(self):
        sno = self.wd_student_var.get()
        if not sno:
            messagebox.showwarning("提示", "请先选择一名学生")
            return

        student = self.db.get_student(sno)
        if student:
            self.wd_info_label.config(
                text=f"当前学生: {student[1]} | 已选: {self.db.get_student_selection_count(sno)} 门")

        self.wd_tree.delete(*self.wd_tree.get_children())
        for row in self.db.get_student_selections(sno):
            self.wd_tree.insert("", "end", values=(
                row[0], row[1], row[2], row[3],
                row[4] if row[4] else "-", row[5]))

    def _do_withdraw_course(self):
        sno = self.wd_student_var.get()
        if not sno:
            messagebox.showwarning("提示", "请先选择一名学生")
            return

        sel = self.wd_tree.selection()
        if not sel:
            messagebox.showwarning("提示", "请先选中要退选的课程")
            return

        values = self.wd_tree.item(sel[0])["values"]
        cno = values[0]
        cnm = values[1]

        if messagebox.askyesno("确认退选", f"确定要退选课程「{cnm}」({cno})吗？"):
            self.db.remove_selection(sno, cno)
            self._load_withdraw_courses()
            messagebox.showinfo("成功", f"已退选课程「{cnm}」")

    def _do_withdraw_all(self):
        sno = self.wd_student_var.get()
        if not sno:
            messagebox.showwarning("提示", "请先选择一名学生")
            return

        count = self.db.get_student_selection_count(sno)
        if count == 0:
            messagebox.showinfo("提示", "该学生当前没有选课")
            return

        if messagebox.askyesno("确认全部退选",
                                f"确定要退选该学生的全部 {count} 门课程吗？"):
            for row in self.db.get_student_selections(sno):
                self.db.remove_selection(sno, row[0])
            self._load_withdraw_courses()
            messagebox.showinfo("成功", f"已退选全部 {count} 门课程")

    # ================================================================
    # 标签页5: XML数据集成
    # ================================================================
    def _build_xml_tab(self):
        # 使用Notebook嵌套子标签页
        sub_nb = ttk.Notebook(self.tab_xml)
        sub_nb.pack(fill="both", expand=True, padx=5, pady=5)

        # --- 子标签5-1: XML导出 ---
        export_frame = ttk.Frame(sub_nb)
        sub_nb.add(export_frame, text="XML导出")

        exp_top = ttk.LabelFrame(export_frame, text="导出选项")
        exp_top.pack(fill="x", padx=8, pady=8)

        self.export_type_var = tk.StringVar(value="standard")
        ttk.Radiobutton(exp_top, text="标准集成格式（用于跨学院数据交换）",
                        variable=self.export_type_var, value="standard").pack(
            anchor="w", padx=10, pady=3)
        ttk.Radiobutton(exp_top, text="学院A原生格式（保留原始字段名）",
                        variable=self.export_type_var, value="native").pack(
            anchor="w", padx=10, pady=3)

        data_sel_frame = ttk.Frame(exp_top)
        data_sel_frame.pack(fill="x", padx=10, pady=5)
        self.export_students_var = tk.BooleanVar(value=True)
        self.export_courses_var = tk.BooleanVar(value=True)
        self.export_selections_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(data_sel_frame, text="学生数据",
                        variable=self.export_students_var).pack(side="left", padx=5)
        ttk.Checkbutton(data_sel_frame, text="课程数据",
                        variable=self.export_courses_var).pack(side="left", padx=5)
        ttk.Checkbutton(data_sel_frame, text="选课数据",
                        variable=self.export_selections_var).pack(side="left", padx=5)

        btn_frame = ttk.Frame(export_frame)
        btn_frame.pack(pady=8)
        ttk.Button(btn_frame, text="执行导出", command=self._do_xml_export,
                   width=14).pack(side="left", padx=5)

        self.export_status = ttk.Label(export_frame, text="",
                                        font=("Microsoft YaHei", 9))
        self.export_status.pack()

        # 预览框
        preview_frame = ttk.LabelFrame(export_frame, text="XML导出预览")
        preview_frame.pack(fill="both", expand=True, padx=8, pady=8)
        self.export_preview = scrolledtext.ScrolledText(
            preview_frame, font=("Consolas", 9), height=14)
        self.export_preview.pack(fill="both", expand=True, padx=5, pady=5)

        # --- 子标签5-2: XML导入 ---
        import_frame = ttk.Frame(sub_nb)
        sub_nb.add(import_frame, text="XML导入")

        imp_top = ttk.LabelFrame(import_frame, text="导入选项")
        imp_top.pack(fill="x", padx=8, pady=8)

        self.import_type_var = tk.StringVar(value="students")
        ttk.Radiobutton(imp_top, text="导入学生数据",
                        variable=self.import_type_var, value="students").pack(
            anchor="w", padx=10, pady=2)
        ttk.Radiobutton(imp_top, text="导入课程数据",
                        variable=self.import_type_var, value="courses").pack(
            anchor="w", padx=10, pady=2)
        ttk.Radiobutton(imp_top, text="导入选课数据",
                        variable=self.import_type_var, value="selections").pack(
            anchor="w", padx=10, pady=2)

        file_frame = ttk.Frame(imp_top)
        file_frame.pack(fill="x", padx=10, pady=5)
        self.import_file_var = tk.StringVar()
        ttk.Entry(file_frame, textvariable=self.import_file_var,
                  width=50).pack(side="left", padx=2)
        ttk.Button(file_frame, text="浏览...", command=self._browse_import_file).pack(
            side="left", padx=3)

        btn_frame2 = ttk.Frame(import_frame)
        btn_frame2.pack(pady=8)
        ttk.Button(btn_frame2, text="预览XML", command=self._preview_import_xml,
                   width=14).pack(side="left", padx=5)
        ttk.Button(btn_frame2, text="执行导入", command=self._do_xml_import,
                   width=14).pack(side="left", padx=5)

        self.import_status = ttk.Label(import_frame, text="",
                                        font=("Microsoft YaHei", 9))
        self.import_status.pack()

        self.import_preview = scrolledtext.ScrolledText(
            import_frame, font=("Consolas", 9), height=16)
        self.import_preview.pack(fill="both", expand=True, padx=8, pady=5)

        # --- 子标签5-3: XSLT格式转换 ---
        xslt_frame = ttk.Frame(sub_nb)
        sub_nb.add(xslt_frame, text="XSLT转换")

        xslt_top = ttk.LabelFrame(xslt_frame, text="XSLT 格式转换")
        xslt_top.pack(fill="x", padx=8, pady=8)

        # 源XML文件
        row1 = ttk.Frame(xslt_top)
        row1.pack(fill="x", padx=10, pady=5)
        ttk.Label(row1, text="源XML:", width=10).pack(side="left")
        self.xslt_src_var = tk.StringVar()
        ttk.Entry(row1, textvariable=self.xslt_src_var, width=45).pack(side="left", padx=3)
        ttk.Button(row1, text="浏览", command=self._browse_xslt_src).pack(side="left", padx=3)

        # XSLT样式表
        row2 = ttk.Frame(xslt_top)
        row2.pack(fill="x", padx=10, pady=5)
        ttk.Label(row2, text="XSLT文件:", width=10).pack(side="left")
        self.xslt_file_var = tk.StringVar()
        ttk.Entry(row2, textvariable=self.xslt_file_var, width=45).pack(side="left", padx=3)
        ttk.Button(row2, text="浏览", command=self._browse_xslt_file).pack(side="left", padx=3)

        # 预置XSLT快速选择
        row3 = ttk.Frame(xslt_top)
        row3.pack(fill="x", padx=10, pady=5)
        ttk.Label(row3, text="快速选择:", width=10).pack(side="left")
        self.xslt_preset_var = tk.StringVar(value="")
        preset_combo = ttk.Combobox(row3, textvariable=self.xslt_preset_var,
                                     values=[
                                         "原生→标准: 学生 (formatStudent.xsl)",
                                         "原生→标准: 课程 (formatClass.xsl)",
                                         "原生→标准: 选课 (formatClassChoice.xsl)",
                                         "标准→A: 学生 (studentToA.xsl)",
                                         "标准→A: 课程 (classToA.xsl)",
                                         "标准→A: 选课 (choiceToA.xsl)",
                                     ], state="readonly", width=40)
        preset_combo.pack(side="left", padx=3)
        preset_combo.bind("<<ComboboxSelected>>", self._on_xslt_preset)

        # 转换按钮
        row4 = ttk.Frame(xslt_top)
        row4.pack(fill="x", padx=10, pady=5)
        ttk.Button(row4, text="执行XSLT转换", command=self._do_xslt_transform,
                   width=16).pack(side="left", padx=5)
        ttk.Button(row4, text="保存转换结果", command=self._save_xslt_result,
                   width=16).pack(side="left", padx=5)

        self.xslt_status = ttk.Label(xslt_top, text="", font=("Microsoft YaHei", 9))
        self.xslt_status.pack(padx=10, pady=3)

        # 转换结果预览
        self.xslt_result_var = ""
        xslt_preview_frame = ttk.LabelFrame(xslt_frame, text="转换结果")
        xslt_preview_frame.pack(fill="both", expand=True, padx=8, pady=5)
        self.xslt_preview = scrolledtext.ScrolledText(
            xslt_preview_frame, font=("Consolas", 9), height=14)
        self.xslt_preview.pack(fill="both", expand=True, padx=5, pady=5)

        # --- 子标签5-4: XSD验证 ---
        valid_frame = ttk.Frame(sub_nb)
        sub_nb.add(valid_frame, text="XSD验证")

        valid_top = ttk.LabelFrame(valid_frame, text="XSD Schema 验证")
        valid_top.pack(fill="x", padx=8, pady=8)

        r1 = ttk.Frame(valid_top)
        r1.pack(fill="x", padx=10, pady=5)
        ttk.Label(r1, text="XML文件:", width=10).pack(side="left")
        self.valid_xml_var = tk.StringVar()
        ttk.Entry(r1, textvariable=self.valid_xml_var, width=45).pack(side="left", padx=3)
        ttk.Button(r1, text="浏览", command=self._browse_valid_xml).pack(side="left", padx=3)

        r2 = ttk.Frame(valid_top)
        r2.pack(fill="x", padx=10, pady=5)
        ttk.Label(r2, text="XSD文件:", width=10).pack(side="left")
        self.valid_xsd_var = tk.StringVar()
        ttk.Entry(r2, textvariable=self.valid_xsd_var, width=45).pack(side="left", padx=3)
        ttk.Button(r2, text="浏览", command=self._browse_valid_xsd).pack(side="left", padx=3)

        # 预置XSD快速选择
        r3 = ttk.Frame(valid_top)
        r3.pack(fill="x", padx=10, pady=5)
        ttk.Label(r3, text="快速选择:", width=10).pack(side="left")
        self.valid_preset_var = tk.StringVar(value="")
        combo2 = ttk.Combobox(r3, textvariable=self.valid_preset_var,
                               values=[
                                   "学生 (studentA.xsd)", "学生 (formatStudent.xsd)",
                                   "课程 (classA.xsd)", "课程 (formatClass.xsd)",
                                   "选课 (choiceA.xsd)", "选课 (formatClassChoice.xsd)",
                               ], state="readonly", width=40)
        combo2.pack(side="left", padx=3)
        combo2.bind("<<ComboboxSelected>>", self._on_valid_preset)

        r4 = ttk.Frame(valid_top)
        r4.pack(fill="x", padx=10, pady=5)
        ttk.Button(r4, text="执行验证", command=self._do_xsd_validate,
                   width=16).pack(side="left", padx=5)

        self.valid_status = ttk.Label(valid_top, text="",
                                       font=("Microsoft YaHei", 10, "bold"))
        self.valid_status.pack(padx=10, pady=3)

        # 验证详情
        valid_detail_frame = ttk.LabelFrame(valid_frame, text="验证详情")
        valid_detail_frame.pack(fill="both", expand=True, padx=8, pady=5)
        self.valid_detail = scrolledtext.ScrolledText(
            valid_detail_frame, font=("Microsoft YaHei", 9), height=16)
        self.valid_detail.pack(fill="both", expand=True, padx=5, pady=5)

    def _do_xml_export(self):
        export_dir = filedialog.askdirectory(title="选择导出目录")
        if not export_dir:
            return

        fmt = self.export_type_var.get()
        prefix = "integration" if fmt == "standard" else "native"
        files_created = []

        try:
            if self.export_students_var.get():
                students = self.db.get_all_students()
                fp = os.path.join(export_dir, f"{prefix}_students_{COLLEGE_ID}.xml")
                if fmt == "standard":
                    XMLHandler.export_students_to_xml(students, fp)
                else:
                    XMLHandler.export_students_native(students, fp)
                files_created.append(fp)

            if self.export_courses_var.get():
                courses = self.db.get_all_courses()
                fp = os.path.join(export_dir, f"{prefix}_courses_{COLLEGE_ID}.xml")
                if fmt == "standard":
                    XMLHandler.export_courses_to_xml(courses, fp)
                else:
                    XMLHandler.export_courses_native(courses, fp)
                files_created.append(fp)

            if self.export_selections_var.get():
                selections = self.db.get_all_selections()
                fp = os.path.join(export_dir, f"{prefix}_selections_{COLLEGE_ID}.xml")
                if fmt == "standard":
                    XMLHandler.export_selections_to_xml(selections, fp)
                else:
                    XMLHandler.export_selections_native(selections, fp)
                files_created.append(fp)

            self.export_status.config(
                text=f"导出成功！共 {len(files_created)} 个文件 → {export_dir}",
                foreground="green")

            # 预览第一个文件
            if files_created:
                preview = XMLHandler.pretty_print_xml(files_created[0])
                self.export_preview.delete("1.0", "end")
                self.export_preview.insert("1.0", preview)

        except Exception as e:
            self.export_status.config(text=f"导出失败: {e}", foreground="red")

    def _browse_import_file(self):
        fp = filedialog.askopenfilename(
            title="选择XML文件",
            filetypes=[("XML files", "*.xml"), ("All files", "*.*")])
        if fp:
            self.import_file_var.set(fp)

    def _preview_import_xml(self):
        fp = self.import_file_var.get()
        if not fp:
            messagebox.showwarning("提示", "请先选择XML文件")
            return
        try:
            with open(fp, "r", encoding="utf-8") as f:
                content = f.read()
            self.import_preview.delete("1.0", "end")
            self.import_preview.insert("1.0", content)
        except Exception as e:
            messagebox.showerror("错误", f"读取文件失败: {e}")

    def _do_xml_import(self):
        fp = self.import_file_var.get()
        if not fp:
            messagebox.showwarning("提示", "请先选择XML文件")
            return

        import_type = self.import_type_var.get()
        try:
            if import_type == "students":
                students = XMLHandler.import_students_from_xml(fp)
                count = 0
                for sno, snm, sex, sde, pwd in students:
                    existing = self.db.get_student(sno)
                    if existing:
                        self.db.update_student(sno, snm, sex, sde, pwd)
                    else:
                        try:
                            self.db.add_student(sno, snm, sex, sde, pwd)
                        except Exception:
                            pass  # 跳过重复
                    count += 1
                self.import_status.config(
                    text=f"学生数据导入成功！共处理 {count} 条记录", foreground="green")

            elif import_type == "courses":
                courses = XMLHandler.import_courses_from_xml(fp)
                count = 0
                for cno, cnm, ctm, cpt, tec, pla, share in courses:
                    existing = self.db.get_course(cno)
                    if existing:
                        self.db.update_course(cno, cnm, ctm, cpt, tec, pla, share)
                    else:
                        try:
                            self.db.add_course(cno, cnm, ctm, cpt, tec, pla, share)
                        except Exception:
                            pass
                    count += 1
                self.import_status.config(
                    text=f"课程数据导入成功！共处理 {count} 条记录", foreground="green")

            elif import_type == "selections":
                selections = XMLHandler.import_selections_from_xml(fp)
                count = 0
                for sno, cno, grd in selections:
                    try:
                        self.db.add_selection(sno, cno)
                        if grd:
                            self.db.update_grade(sno, cno, grd)
                        count += 1
                    except Exception:
                        pass
                self.import_status.config(
                    text=f"选课数据导入成功！共处理 {count} 条记录", foreground="green")

            self._refresh_all()
        except Exception as e:
            self.import_status.config(text=f"导入失败: {e}", foreground="red")

    # ---- XML: XSLT转换 ----
    def _browse_xslt_src(self):
        fp = filedialog.askopenfilename(filetypes=[("XML files", "*.xml"), ("All", "*.*")])
        if fp:
            self.xslt_src_var.set(fp)

    def _browse_xslt_file(self):
        fp = filedialog.askopenfilename(filetypes=[("XSL files", "*.xsl"), ("All", "*.*")])
        if fp:
            self.xslt_file_var.set(fp)

    def _on_xslt_preset(self, event=None):
        preset = self.xslt_preset_var.get()
        xslt_dir = XMLHandler.get_xslt_dir()
        mapping = {
            "原生→标准: 学生": "formatStudent.xsl",
            "原生→标准: 课程": "formatClass.xsl",
            "原生→标准: 选课": "formatClassChoice.xsl",
            "标准→A: 学生": "studentToA.xsl",
            "标准→A: 课程": "classToA.xsl",
            "标准→A: 选课": "choiceToA.xsl",
        }
        for key, filename in mapping.items():
            if key in preset:
                self.xslt_file_var.set(os.path.join(xslt_dir, filename))
                break

    def _do_xslt_transform(self):
        src = self.xslt_src_var.get()
        xslt_f = self.xslt_file_var.get()
        if not src or not xslt_f:
            messagebox.showwarning("提示", "请选择源XML文件和XSLT文件")
            return
        try:
            result = XMLHandler.transform_xml(src, xslt_f)
            self.xslt_result_var = result
            self.xslt_preview.delete("1.0", "end")
            self.xslt_preview.insert("1.0", result)
            self.xslt_status.config(text="XSLT转换成功！", foreground="green")
        except Exception as e:
            self.xslt_status.config(text=f"转换失败: {e}", foreground="red")

    def _save_xslt_result(self):
        if not self.xslt_result_var:
            messagebox.showwarning("提示", "请先执行XSLT转换")
            return
        fp = filedialog.asksaveasfilename(
            defaultextension=".xml",
            filetypes=[("XML files", "*.xml"), ("All", "*.*")])
        if fp:
            with open(fp, "w", encoding="utf-8") as f:
                f.write(self.xslt_result_var)
            messagebox.showinfo("成功", f"已保存到: {fp}")

    # ---- XML: XSD验证 ----
    def _browse_valid_xml(self):
        fp = filedialog.askopenfilename(filetypes=[("XML files", "*.xml"), ("All", "*.*")])
        if fp:
            self.valid_xml_var.set(fp)

    def _browse_valid_xsd(self):
        fp = filedialog.askopenfilename(filetypes=[("XSD files", "*.xsd"), ("All", "*.*")])
        if fp:
            self.valid_xsd_var.set(fp)

    def _on_valid_preset(self, event=None):
        preset = self.valid_preset_var.get()
        xsd_dir = XMLHandler.get_xsd_dir()
        mapping = {
            "学生 (studentA.xsd)": "studentA.xsd",
            "学生 (formatStudent.xsd)": "formatStudent.xsd",
            "课程 (classA.xsd)": "classA.xsd",
            "课程 (formatClass.xsd)": "formatClass.xsd",
            "选课 (choiceA.xsd)": "choiceA.xsd",
            "选课 (formatClassChoice.xsd)": "formatClassChoice.xsd",
        }
        for key, filename in mapping.items():
            if key == preset:
                self.valid_xsd_var.set(os.path.join(xsd_dir, filename))
                break

    def _do_xsd_validate(self):
        xml_f = self.valid_xml_var.get()
        xsd_f = self.valid_xsd_var.get()
        if not xml_f or not xsd_f:
            messagebox.showwarning("提示", "请选择XML文件和XSD文件")
            return
        try:
            ok, errors = XMLHandler.validate_xml(xml_f, xsd_f)
            self.valid_detail.delete("1.0", "end")
            if ok:
                self.valid_status.config(text="XML验证通过!", foreground="green")
                self.valid_detail.insert("1.0", "XML文档符合XSD Schema定义，验证通过。")
            else:
                self.valid_status.config(
                    text=f"验证失败 — 发现 {len(errors)} 个错误", foreground="red")
                for i, err in enumerate(errors, 1):
                    self.valid_detail.insert("end", f"[错误 {i}] {err}\n")
        except Exception as e:
            self.valid_status.config(text=f"验证异常: {e}", foreground="red")

    # ================================================================
    # 标签页6: 统计信息
    # ================================================================
    def _build_stats_tab(self):
        ttk.Button(self.tab_stats, text="刷新统计数据",
                   command=self._refresh_stats_tab).pack(pady=8)

        self.stats_text = scrolledtext.ScrolledText(
            self.tab_stats, font=("Microsoft YaHei", 10), height=22, width=80)
        self.stats_text.pack(fill="both", expand=True, padx=10, pady=5)

    def _refresh_stats_tab(self):
        stats = self.db.get_statistics()
        self.stats_text.delete("1.0", "end")

        line = "=" * 55 + "\n"
        self.stats_text.insert("end", line)
        self.stats_text.insert("end", f"  {COLLEGE_NAME} - 教学管理系统 统计报表\n")
        self.stats_text.insert("end", line)
        self.stats_text.insert("end", f"\n  ▶ 学生总数: {stats['student_count']} 人\n")
        self.stats_text.insert("end", f"  ▶ 课程总数: {stats['course_count']} 门\n")
        self.stats_text.insert("end", f"  ▶ 选课总数: {stats['selection_count']} 条\n")

        self.stats_text.insert("end", f"\n  {'─' * 45}\n")
        self.stats_text.insert("end", "  ▶ 性别分布:\n")
        for sex, cnt in stats["sex_stats"]:
            self.stats_text.insert("end", f"      {sex}: {cnt} 人\n")

        self.stats_text.insert("end", f"\n  {'─' * 45}\n")
        self.stats_text.insert("end", "  ▶ 各专业人数:\n")
        for sde, cnt in stats["major_stats"]:
            self.stats_text.insert("end", f"      {sde}: {cnt} 人\n")

        self.stats_text.insert("end", f"\n  {'─' * 45}\n")
        self.stats_text.insert("end", "  ▶ 课程选课人数排行:\n")
        for cnm, cnt in stats["course_popularity"]:
            bar = "█" * min(cnt, 25)
            self.stats_text.insert("end", f"      {cnm}: {cnt} 人 {bar}\n")

        self.stats_text.insert("end", f"\n  {'─' * 45}\n")
        self.stats_text.insert("end", "  ▶ 课程来源分布:\n")
        for share, cnt in stats["share_stats"]:
            label = f"学院{share}" if share else "未知"
            self.stats_text.insert("end", f"      {label}: {cnt} 门\n")

        self.stats_text.insert("end", f"\n{line}")

    # ================================================================
    # 全局
    # ================================================================
    def _refresh_all(self):
        try:
            self._refresh_student_tab()
            self._refresh_course_tab()
            self._refresh_stats_tab()
        except Exception:
            pass

    def _on_exit(self):
        self.db.close()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


# ================================================================
# 对话框：学生信息编辑
# ================================================================
class StudentDialog(tk.Toplevel):
    def __init__(self, parent, title, initial=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("350x280")
        self.resizable(False, False)
        self.result = None

        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self)
        frame.pack(padx=20, pady=20)

        labels = ["学号(Sno):", "姓名(Snm):", "性别(Sex):", "专业(Sde):", "密码(Pwd):"]
        self.vars = []
        for i, label in enumerate(labels):
            ttk.Label(frame, text=label, font=("Microsoft YaHei", 10)).grid(
                row=i, column=0, sticky="e", pady=6)
            var = tk.StringVar()
            if initial:
                var.set(str(initial[i]) if initial[i] else "")
            self.vars.append(var)
            entry = ttk.Entry(frame, textvariable=var, width=22,
                              font=("Microsoft YaHei", 10))
            if i == 2:  # 性别下拉
                combo = ttk.Combobox(frame, textvariable=var, values=["男", "女"],
                                      state="readonly", width=20)
                combo.grid(row=i, column=1, padx=8)
            else:
                entry.grid(row=i, column=1, padx=8)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="确定", command=self._on_ok, width=10).pack(
            side="left", padx=8)
        ttk.Button(btn_frame, text="取消", command=self.destroy, width=10).pack(
            side="left", padx=8)

    def _on_ok(self):
        values = [v.get().strip() for v in self.vars]
        if not values[0] or not values[1]:
            messagebox.showwarning("提示", "学号和姓名不能为空")
            return
        self.result = values
        self.destroy()


# ================================================================
# 对话框：课程信息编辑
# ================================================================
class CourseDialog(tk.Toplevel):
    def __init__(self, parent, title, initial=None):
        super().__init__(parent)
        self.title(title)
        self.geometry("380x320")
        self.resizable(False, False)
        self.result = None

        self.transient(parent)
        self.grab_set()

        frame = ttk.Frame(self)
        frame.pack(padx=20, pady=20)

        labels = [
            "课程号(Cno):", "课程名(Cnm):", "学分(Ctm):",
            "学时(Cpt):", "授课教师(Tec):", "地点(Pla):", "共享来源(Share):"
        ]
        self.vars = []
        for i, label in enumerate(labels):
            ttk.Label(frame, text=label, font=("Microsoft YaHei", 10)).grid(
                row=i, column=0, sticky="e", pady=5)
            var = tk.StringVar()
            if initial:
                var.set(str(initial[i]) if initial[i] else "")
            self.vars.append(var)
            if i == 6:  # 共享来源下拉
                combo = ttk.Combobox(frame, textvariable=var,
                                      values=["A", "B", "C"],
                                      state="readonly", width=20)
                combo.grid(row=i, column=1, padx=8)
            else:
                ttk.Entry(frame, textvariable=var, width=22,
                          font=("Microsoft YaHei", 10)).grid(row=i, column=1, padx=8)

        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="确定", command=self._on_ok, width=10).pack(
            side="left", padx=8)
        ttk.Button(btn_frame, text="取消", command=self.destroy, width=10).pack(
            side="left", padx=8)

    def _on_ok(self):
        values = [v.get().strip() for v in self.vars]
        if not values[0] or not values[1]:
            messagebox.showwarning("提示", "课程号和课程名不能为空")
            return
        self.result = values
        self.destroy()


# ================================================================
# 启动入口
# ================================================================
if __name__ == "__main__":
    # 首次运行自动初始化数据库
    from config import SQLITE_DB_PATH
    if not os.path.exists(SQLITE_DB_PATH):
        print("数据库不存在，正在初始化...")
        import init_database
        init_database.init_database()

    LoginWindow().run()
