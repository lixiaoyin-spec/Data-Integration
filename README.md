# 数据集成作业三 — 基于 XML 的异构数据集成系统

**组号**: 27 
**成员**: 6人 
**技术**: Python · Java · SQL Server · Oracle · MySQL · XML/XSD/XSLT
**GitHub仓库链接：**[lixiaoyin-spec/Data-Integration: Data Integration Course Project, Grade 3, School of Software, Nanjing University](https://github.com/lixiaoyin-spec/Data-Integration)

---

## 一、项目概述

本系统实现了三个异构学院教务系统（A、B、C）的数据集成。三个学院分别使用不同的数据库管理系统（SQL Server、Oracle、MySQL），表结构、字段名称各不相同。通过新增**集成服务器（Integration Server）**，基于 **XML 标准格式**实现跨学院课程共享、跨院选课、全局统计等功能。

---

## 二、系统架构

```
┌──────────────────────────────────────────────────────────┐
│                   集成教务服务器 (:8000)                    │
│  课程聚合 · 学生聚合 · 统计汇总 · 跨院选课 · 跨院退选       │
│  CollegeClient → HTTP → A/B/C 各学院本地服务器              │
└──────┬──────────────────┬──────────────────┬─────────────┘
       │ HTTP + XML       │ HTTP + XML       │ HTTP + XML
       ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ 学院 A :8081  │  │ 学院 B :8082  │  │ 学院 C :8083  │
│ SQL Server   │  │ Oracle       │  │ MySQL        │
│ Python+tkinter│  │ Java+Web前端  │  │ Java+Swing   │
│ GUI + 登录    │  │ GUI + 登录    │  │ GUI + 登录    │
└──────────────┘  └──────────────┘  └──────────────┘
```

---

## 三、各学院异构数据库设计

三个学院的**表结构、字段名、数据类型存在差异**，体现了异构数据集成场景：

| 对比维度 | A (SQL Server) | B (Oracle) | C (MySQL) |
|---------|---------------|-----------|----------|
| 学生表 | `Students(Sno, Snm, Sex, Sde, Pwd)` | `B_STUDENT(SID, SNAME, SEX, MAJOR, PASSWORD, GRADE, PHONE, STATUS)` | `student(Sno, Snm, Sex, Sde, Pwd)` |
| 课程表 | `Courses(Cno, Cnm, Ctm, Cpt, Tec, Pla, Share)` | `B_COURSE(CID, CNAME, HOURS, CREDIT, TEACHER, LOCATION, SHARE_FLAG, CAPACITY, STATUS)` | `course(Cno, Cnm, Ctm, Cpt, Tec, Pla, Share)` |
| 选课表 | `Selections(Sno, Cno, Grd)` | `B_ENROLLMENT(SID, CID, SCORE, CHOICE_STA)` | `choice(Sno, Cno, Grd)` |
| 学分字段 | `Ctm` | `CREDIT` | `Cpt` |
| 学时字段 | `Cpt` | `HOURS` | `Ctm` |
| 共享标记 | `Share` 自由文本 | `SHARE_FLAG` Y/N | `Share` Y/N |
| 学号前缀 | `S001-S050` | `B2023001-B2023050` | `1001-1050` |

> 注：B系统Oracle建表脚本（`oracle/db/oracle_b_schema.sql`）和Java API服务器（`oracle/service/BLocalServer.java`）代码完整。演示环境下可使用 `oracle/mock_b_server.py` 替代。

---

## 四、作业要求对应表

| # | 作业要求 | 实现情况 | 关键文件 |
|---|---------|---------|---------|
| 1 | 三学院基于不同DBMS | A=SQL Server, B=Oracle, C=MySQL | `CollegeA_SQLServer/`, `oracle/`, `CollegeC_Mysql/` |
| 2 | 各系统 50学生/10课程/每人5门 | 三系统各 50+10+250条 | `init_database.py`, `oracle_b_schema.sql`, `DataGenerator.java` |
| 3 | GUI + 登录 | A=tkinter, B=Web嵌入式, C=Java Swing, 集成=tkinter | `gui_app.py`, `BLocalServer.java`, `LoginFrame.java`, `integration_gui.py` |
| 4 | XML 技术 | XSD验证, XSLT转换, 标准XML交换 | `xml_handler.py`, `xsd/`, `xslt/`, `xml_utils.py` |
| 5 | 集成服务器 → 课程共享 | 聚合三学院共享课程（share_flag=Y），XML统一格式 | `main.py → /api/courses/shared` |
| 6 | 跨院选课 → 数据写回 | 学生信息导入目标学院 + 选课记录写入目标学院数据库 | `main.py → /api/enroll` |
| 7 | 全局统计 | 汇总三学院学生/课程/选课总数 | `main.py → /api/statistics` |
| 8 | 跨院退选 | 同步删除目标学院选课记录 | `main.py → /api/drop` |

---

## 五、项目目录结构

```
├── CollegeA_SQLServer/          # 学院A (SQL Server + Python)
│   ├── init_database.py         #   数据库初始化（50学生+10课程+250选课）
│   ├── gui_app.py               #   tkinter 桌面GUI（含登录）
│   ├── local_server.py          #   HTTP API服务器 (:8081)
│   ├── db_manager.py            #   数据库CRUD操作
│   ├── xml_handler.py           #   XML导入/导出/XSD验证/XSLT转换
│   ├── sqlserver_setup.sql      #   SQL Server 建表脚本
│   ├── xslt/                    #   XSLT 格式转换样式表（6个）
│   └── xsd/                     #   XSD Schema 验证文件（6个）
│
├── oracle/                      # 学院B (Oracle + Java)
│   ├── db/oracle_b_schema.sql   #   Oracle建表+数据+触发器+存储过程
│   ├── service/BLocalServer.java #  HTTP API服务器 (:8082)，含20个端点
│   ├── mock_b_server.py         #   Mock B服务器 (不依赖Oracle，用于演示)
│   ├── xslt/                    #   XSLT 转换（6个）
│   └── docs/                    #   B系统说明文档
│
├── CollegeC_Mysql/              # 学院C (MySQL + Java)
│   ├── local_server.py          #   HTTP API服务器 (:8083)
│   ├── edu-management-server/   #   Java Socket服务器 + XML生成/导入/转换
│   └── edu-management-client/   #   Java Swing 桌面GUI（含登录）
│
├── IntegrationServer/           # 集成服务器 (:8000)
│   ├── main.py                  #   主程序（多线程HTTP + 内嵌Web仪表盘）
│   ├── config.py                #   学院注册配置（A/B/C的URL和端点）
│   ├── college_client.py        #   HTTP客户端（绕过代理直连各学院）
│   ├── course_aggregator.py     #   课程聚合器（拉取+统一+去重）
│   ├── xml_utils.py             #   XML解析/构建/格式转换工具
│   ├── integration_gui.py       #   tkinter 集成桌面GUI
│   ├── xslt/                    #   XSLT 转换表
│   ├── api_docs.md              #   API 文档
│   └── 成员*_交付说明.md         #   各成员交付文档
│
├── upload_to_remote.py          # 远程数据库上传脚本（组号27）
├── 现场演示指南.md               # 演示流程指导
├── 数据集成作业三作业要求.md      # 作业要求
└── README.md                    # 本文件
```

---

## 六、快速启动（5终端演示）

```powershell
# 准备工作（首次运行）
cd CollegeA_SQLServer && python init_database.py

# 终端1: A学院 (SQL Server)
python CollegeA_SQLServer/local_server.py --port 8081

# 终端2: B学院 (Oracle/Mock)
python oracle/mock_b_server.py --port 8082

# 终端3: C学院 (MySQL)
python CollegeC_Mysql/local_server.py --port 8083

# 终端4: 集成服务器
python IntegrationServer/main.py --port 8000

# 终端5: 集成GUI（可选）
python IntegrationServer/integration_gui.py
```

浏览器打开 `http://localhost:8000` 即可看到集成仪表盘。

---

## 七、跨院选课核心流程

```
学生 S001 (学院A) 要选 学院B 的课程 C001

  集成服务器 POST /api/enroll
       │
       ├── Step 1: 验证学院A和学院B均在线
       │
       ├── Step 2: POST /b/students/import
       │     → XML: <Students><student><id>S001</id><name>张三</name>...</student></Students>
       │     → 学生信息写入学院B数据库（如已存在则跳过）
       │
       ├── Step 3: POST /b/enroll
       │     → XML: <Choices><choice><sid>S001</sid><cid>C001</cid></choice></Choices>
       │     → 选课记录写入学院B数据库
       │
       └── 返回: { "status": "success", "message": "跨院选课成功" }
```

---

## 八、关键技术点

| 技术 | 应用位置 | 说明 |
|------|---------|------|
| **XML 标准格式** | `xml_utils.py`, `xml_handler.py` | 统一数据交换格式，屏蔽异构DB差异 |
| **XSD Schema** | `xsd/*.xsd` | 验证XML格式合法性（学生/课程/选课） |
| **XSLT 转换** | `xslt/*.xsl` | 原生格式 ↔ 标准格式双向转换 |
| **HTTP REST API** | 各 `local_server.py`, `main.py` | 松耦合通信，各学院独立部署 |
| **多线程HTTP** | `main.py` (ThreadingHTTPServer) | 并发处理请求，避免单请求阻塞 |
| **异构字段映射** | `course_aggregator.py`, `xml_utils.py` | 自动识别不同学院的字段名差异 |

---

## 九、依赖

| 模块 | 依赖 |
|------|------|
| A系统 | Python 3.x（标准库 + pyodbc 可选） |
| B系统 (Mock) | Python 3.x（标准库，无需Oracle） |
| B系统 (真实) | JDK 8+, Oracle Database, Oracle JDBC |
| C系统 (Python HTTP) | Python 3.x + pymysql |
| C系统 (Java) | JDK 8+, MySQL Connector/J, dom4j |
| 集成服务器 | Python 3.x + requests |
| 集成GUI | Python 3.x + tkinter（标准库） |

```powershell
pip install requests pymysql
```
