# 集成教务服务器 API 文档

## 概述

集成服务器（Integration Server）是连接 A(SQL Server)、B(Oracle)、C(MySQL) 三个异构学院教务系统的中枢。所有数据交换使用 **标准 XML 格式**。

- **默认端口**: `8000`
- **Content-Type**: JSON 或 XML（根据请求头 Accept 决定）
- **CORS**: 全部开放

---

## 一、系统管理

### GET /api/status — 全局状态

检查集成服务器及所有学院的状态。

**响应示例:**
```json
{
  "server": "集成教务服务器",
  "version": "1.0.0",
  "colleges_total": 3,
  "colleges_online": 2,
  "details": {
    "A": { "online": true, "college_id": "A", "students": 50, "courses": 10, "selections": 250 },
    "B": { "online": true, "college_id": "B", "students": 50, "courses": 10, "selections": 250 },
    "C": { "online": false, "error": "无法连接" }
  }
}
```

### GET /api/colleges — 学院列表

获取所有注册学院的详细信息和在线状态。

**响应**: JSON 数组

---

## 二、认证

### POST /api/login — 统一登录

学生在集成端登录，验证请求转发到所属学院。

**请求体** (form-urlencoded 或 JSON):
```json
{
  "acc": "S001",
  "pwd": "student123",
  "college": "A"
}
```

**响应:**
```json
{
  "status": "success",
  "role": "学生",
  "sno": "S001",
  "source_college": "A"
}
```

---

## 三、课程聚合

### GET /api/courses/shared — 共享课程

从所有在线学院拉取标记为"共享"的课程，统一格式返回。

**查询参数**: `?college=B` — 筛选特定学院

**响应**: XML 或 JSON

```xml
<Classes>
  <class>
    <id>C001</id>
    <name>数据库原理</name>
    <credit>3.0</credit>
    <hours>48</hours>
    <teacher>王教授</teacher>
    <location>教学楼301</location>
    <share_college>B</share_college>
    <share_flag>Y</share_flag>
  </class>
</Classes>
```

### GET /api/courses/all — 全部课程

聚合所有学院的课程（含非共享）。

**查询参数**: `?college=A`

### GET /api/courses/college?college=A — 特定学院课程

---

## 四、学生聚合

### GET /api/students — 全体学生

从所有在线学院拉取学生数据。

**查询参数**: `?college=B`

**响应**: XML

```xml
<Students>
  <student>
    <id>S001</id>
    <name>张三</name>
    <sex>男</sex>
    <major>计算机科学</major>
    <college>A</college>
  </student>
</Students>
```

### GET /api/students/college?college=A — 特定学院学生

---

## 五、跨院选课（核心功能）

### POST /api/enroll — 跨院选课

**这是作业的核心功能**。学生从所属学院选其他学院的共享课程，选课记录写回课程所属学院。

**流程:**
1. 验证源学院和目标学院均在线
2. 将学生信息（学号、姓名、性别、专业）导入目标学院数据库
3. 在目标学院创建选课记录

**请求体** (JSON):
```json
{
  "sno": "S001",
  "snm": "张三",
  "sex": "男",
  "sde": "计算机科学",
  "source_college": "A",
  "cno": "C001",
  "cnm": "数据库原理",
  "target_college": "B"
}
```

**成功响应:**
```json
{
  "status": "success",
  "message": "跨院选课成功: 学生S001已选修学院B的课程数据库原理",
  "source_college": "A",
  "target_college": "B",
  "steps": [
    {"step": "import_student", "result": {"status": "success", "existed": false}},
    {"step": "enroll", "result": {"status": "success", "message": "选课成功"}}
  ]
}
```

---

## 六、跨院退选

### POST /api/drop — 跨院退选

退选其他学院的课程，同步删除目标学院的选课记录。

**请求体** (JSON):
```json
{
  "sno": "S001",
  "cno": "C001",
  "target_college": "B"
}
```

**响应:**
```json
{
  "status": "success",
  "message": "退选成功: 学生S001已退选学院B的课程C001"
}
```

---

## 七、统计

### GET /api/statistics — 全局统计

聚合所有学院的统计数据。

**响应:**
```json
{
  "summary": {
    "total_students": 150,
    "total_courses": 30,
    "total_selections": 750,
    "colleges_online": 3,
    "colleges_total": 3
  },
  "details": [
    { "college_id": "A", "college_name": "学院A", "dbms": "SQL Server", "online": true, "students": 50, "courses": 10, "selections": 250 }
  ]
}
```

---

## 八、成绩单

### GET /api/transcript?sno=S001&college=A

获取学生在特定学院的成绩单。

**响应**: XML（Transcript 格式）

---

## 集成服务器与各学院的通信架构

```
┌─────────────────────────────────────────────────────────┐
│                    集成服务器 :8000                       │
│  ┌──────────────────────────────────────────────────┐  │
│  │            CollegeClient (HTTP)                   │  │
│  └──────────────────────────────────────────────────┘  │
└──────┬──────────────────┬──────────────────┬───────────┘
       │                  │                  │
       ▼                  ▼                  ▼
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ A学院 :8081   │  │ B学院 :8082   │  │ C学院 :8083   │
│ (SQL Server) │  │ (Oracle)     │  │ (MySQL)      │
└──────────────┘  └──────────────┘  └──────────────┘
```

各学院需要实现以下 API 接口供集成服务器调用：

| 端点 | 方法 | 说明 |
|------|------|------|
| `/x/api/status` | GET | 服务器状态 |
| `/x/login` | POST | 用户登录 |
| `/x/courses` | GET | 全部课程（XML） |
| `/x/shared-courses` | GET | 共享课程（XML） |
| `/x/students` | GET | 学生列表（XML） |
| `/x/students/xml` | GET | 学生数据（标准集成格式） |
| `/x/enroll` | POST | 选课 |
| `/x/drop` | POST | 退课 |
| `/x/transcript` | GET | 成绩单 |
| `/x/students/import` | POST | 导入外部学生 |
| `/x/enrollments/import` | POST | 导入选课记录 |
