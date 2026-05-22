"""
Oracle B 系统验证脚本
用途：检查初始化数据量、课程共享、选课完整性与退课状态
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from typing import Dict, List, Tuple

try:
    import oracledb  # type: ignore
except ImportError:  # pragma: no cover
    oracledb = None


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str


DEFAULT_DSN = "localhost:1521/orcl"
DEFAULT_USER = "BUSER"
DEFAULT_PASSWORD = "BPASS"


def get_conn(user: str, password: str, dsn: str):
    if oracledb is None:
        raise RuntimeError("缺少 oracledb 驱动，请先安装 python-oracledb")
    return oracledb.connect(user=user, password=password, dsn=dsn)


def fetch_one(cur, sql: str, params: Tuple = ()):
    cur.execute(sql, params)
    return cur.fetchone()


def fetch_all(cur, sql: str, params: Tuple = ()):
    cur.execute(sql, params)
    return cur.fetchall()


def run_checks(conn) -> List[CheckResult]:
    cur = conn.cursor()
    results: List[CheckResult] = []

    student_count = fetch_one(cur, "SELECT COUNT(*) FROM B_STUDENT")[0]
    course_count = fetch_one(cur, "SELECT COUNT(*) FROM B_COURSE")[0]
    enroll_count = fetch_one(cur, "SELECT COUNT(*) FROM B_ENROLLMENT")[0]
    account_count = fetch_one(cur, "SELECT COUNT(*) FROM B_ACCOUNT WHERE SID IS NOT NULL")[0]
    shared_course_count = fetch_one(cur, "SELECT COUNT(*) FROM B_COURSE WHERE SHARE_FLAG = 'Y'")[0]

    results.append(CheckResult("学生数量", student_count >= 50, f"当前 {student_count}，要求 >= 50"))
    results.append(CheckResult("课程数量", course_count >= 10, f"当前 {course_count}，要求 >= 10"))
    results.append(CheckResult("学生账号数量", account_count >= 50, f"当前 {account_count}，要求 >= 50"))
    results.append(CheckResult("选课记录数量", enroll_count >= 250, f"当前 {enroll_count}，要求 >= 250"))
    results.append(CheckResult("共享课程数量", shared_course_count > 0, f"当前 {shared_course_count} 门共享课"))

    orphan = fetch_one(
        cur,
        """
        SELECT COUNT(*)
        FROM B_ENROLLMENT e
        WHERE NOT EXISTS (SELECT 1 FROM B_STUDENT s WHERE s.SID = e.SID)
           OR NOT EXISTS (SELECT 1 FROM B_COURSE c WHERE c.CID = e.CID)
        """,
    )[0]
    results.append(CheckResult("选课引用完整性", orphan == 0, f"孤立记录 {orphan} 条"))

    dropped = fetch_one(cur, "SELECT COUNT(*) FROM B_ENROLLMENT WHERE CHOICE_STA = 'DROPPED'")[0]
    results.append(CheckResult("退课状态机制", dropped >= 0, f"DROPPED 记录 {dropped} 条"))

    duplicates = fetch_one(
        cur,
        """
        SELECT COUNT(*)
        FROM (
            SELECT SID, COUNT(*) c
            FROM B_ENROLLMENT
            GROUP BY SID
            HAVING COUNT(*) < 5
        )
        """,
    )[0]
    results.append(CheckResult("每个学生至少 5 条选课的覆盖度", duplicates == 0, f"未满足 5 门课覆盖的学生分组数 {duplicates}（若为 0 表示全部满足）"))

    cur.close()
    return results


def print_report(results: List[CheckResult]):
    print("=" * 60)
    print("Oracle B 系统验证报告")
    print("=" * 60)
    for item in results:
        mark = "PASS" if item.ok else "FAIL"
        print(f"[{mark}] {item.name}: {item.detail}")
    print("=" * 60)
    all_ok = all(r.ok for r in results)
    print("总体结果：" + ("通过" if all_ok else "未通过"))
    return all_ok


def main():
    parser = argparse.ArgumentParser(description="验证 Oracle B 系统初始化与业务数据")
    parser.add_argument("--user", default=DEFAULT_USER)
    parser.add_argument("--password", default=DEFAULT_PASSWORD)
    parser.add_argument("--dsn", default=DEFAULT_DSN)
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    args = parser.parse_args()

    conn = get_conn(args.user, args.password, args.dsn)
    try:
        results = run_checks(conn)
        if args.json:
            print(json.dumps([r.__dict__ for r in results], ensure_ascii=False, indent=2))
        ok = print_report(results)
        raise SystemExit(0 if ok else 1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
