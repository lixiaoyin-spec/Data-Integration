"""
集成服务器 — 配置文件
定义各学院本地服务器注册信息
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ================================================================
# 集成服务器自身配置
# ================================================================
INTEGRATION_SERVER = {
    "host": "0.0.0.0",
    "port": 8000,
    "name": "集成教务服务器",
    "version": "1.0.0",
}

# ================================================================
# 各学院本地服务器注册
# ================================================================
COLLEGES = {
    "A": {
        "id": "A",
        "name": "学院A",
        "dbms": "SQL Server",
        "base_url": "http://localhost:8081",
        "endpoints": {
            "status":      "/a/api/status",
            "login":       "/a/login",
            "courses":     "/a/courses",
            "shared":      "/a/shared-courses",
            "students":    "/a/students",
            "students_xml":    "/a/students/xml",
            "courses_xml":     "/a/courses/xml",
            "selections_xml":  "/a/selections/xml",
            "enroll":      "/a/enroll",
            "drop":        "/a/drop",
            "transcript":  "/a/transcript",
            "statistics":  "/a/statistics",
            "import_student":   "/a/students/import",
            "import_enrollment": "/a/enrollments/import",
        },
    },
    "B": {
        "id": "B",
        "name": "学院B",
        "dbms": "Oracle",
        "base_url": "http://localhost:8082",
        "endpoints": {
            "status":      "/b/api/status",
            "login":       "/b/login",
            "courses":     "/b/courses",
            "shared":      "/b/shared-courses",
            "students":    "/b/students",
            "students_xml":    "/b/students/xml",
            "courses_xml":     "/b/courses/xml",
            "selections_xml":  "/b/selections/xml",
            "enroll":      "/b/enroll",
            "drop":        "/b/drop",
            "transcript":  "/b/transcript",
            "statistics":  "/b/statistics",
            "import_student":   "/b/students/import",
            "import_enrollment": "/b/enrollments/import",
        },
    },
    "C": {
        "id": "C",
        "name": "学院C",
        "dbms": "MySQL",
        "base_url": "http://localhost:8083",
        "endpoints": {
            "status":      "/c/api/status",
            "login":       "/c/login",
            "courses":     "/c/courses",
            "shared":      "/c/shared-courses",
            "students":    "/c/students",
            "students_xml":    "/c/students/xml",
            "courses_xml":     "/c/courses/xml",
            "selections_xml":  "/c/selections/xml",
            "enroll":      "/c/enroll",
            "drop":        "/c/drop",
            "transcript":  "/c/transcript",
            "statistics":  "/c/statistics",
            "import_student":   "/c/students/import",
            "import_enrollment": "/c/enrollments/import",
        },
    },
}

# 选课限制
MAX_COURSES_PER_STUDENT = 5

# 超时设置（秒）
HTTP_TIMEOUT = 10
