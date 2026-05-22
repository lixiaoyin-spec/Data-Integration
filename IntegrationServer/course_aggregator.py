"""
集成服务器 — 课程聚合模块
负责从A(SQL Server)、B(Oracle)、C(MySQL)三学院拉取课程数据，
进行格式统一、去重合并、共享筛选，输出统一XML。

功能:
  1. 从所有在线学院拉取课程
  2. 字段名统一化（处理三学院异构schema差异）
  3. 课程去重（基于课程名称相似度识别重叠课程）
  4. 共享课程筛选
  5. 统一XML输出
  6. XSLT格式转换
"""
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from difflib import SequenceMatcher

from config import COLLEGES

# XSLT 脚本目录
XSLT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xslt")


class CourseAggregator:
    """课程聚合器 — 统一管理跨学院课程数据"""

    # 课程名相似度阈值，超过此值视为同一门课
    SIMILARITY_THRESHOLD = 0.75

    def __init__(self, registry):
        """
        registry: CollegeRegistry 实例，用于与各学院通信
        """
        self._registry = registry
        self._raw_courses = {}    # college_id -> [dict] 原始课程列表
        self._unified = []        # 统一格式后的课程列表
        self._merged = []         # 去重合并后的课程列表
        self._shared = []         # 仅共享课程

    # ================================================================
    # 数据拉取
    # ================================================================

    def fetch_all(self, colleges=None):
        """从指定学院（默认全部）拉取全部课程"""
        if colleges is None:
            colleges = list(COLLEGES.keys())

        self._raw_courses = {}
        for cid in colleges:
            client = self._registry.get(cid)
            if not client:
                continue
            status = client.check_status()
            if not status.get("online"):
                print(f"[Aggregator] 学院{cid}离线，跳过")
                continue
            xml_data = client.get_courses()
            if xml_data:
                courses = self._parse_courses(xml_data, cid)
                self._raw_courses[cid] = courses
                print(f"[Aggregator] 学院{cid}: 拉取到 {len(courses)} 门课程")
            else:
                self._raw_courses[cid] = []
        return self

    def fetch_shared(self, colleges=None):
        """从指定学院拉取仅共享课程"""
        if colleges is None:
            colleges = list(COLLEGES.keys())

        self._raw_courses = {}
        for cid in colleges:
            client = self._registry.get(cid)
            if not client:
                continue
            status = client.check_status()
            if not status.get("online"):
                continue
            xml_data = client.get_shared_courses()
            if xml_data:
                courses = self._parse_courses(xml_data, cid)
                self._raw_courses[cid] = courses
            else:
                self._raw_courses[cid] = []
        return self

    # ================================================================
    # 格式统一
    # ================================================================

    def normalize(self):
        """将所有学院的课程统一为标准字段名"""
        self._unified = []
        for cid, courses in self._raw_courses.items():
            for c in courses:
                norm = {
                    "cno": c.get("cno", ""),
                    "cnm": c.get("cnm", ""),
                    "credit": c.get("credit", ""),
                    "hours": c.get("hours", ""),
                    "teacher": c.get("teacher", ""),
                    "location": c.get("location", ""),
                    "share_flag": c.get("share_flag", "N"),
                    "share_college": cid,
                    "college_name": COLLEGES.get(cid, {}).get("name", ""),
                }
                self._unified.append(norm)
        print(f"[Aggregator] 统一格式完成，共 {len(self._unified)} 门课程")
        return self

    # ================================================================
    # 去重合并
    # ================================================================

    def deduplicate(self):
        """
        基于课程名相似度去重。
        多学院开设的同一门课会被识别并合并，记录所有开课学院。
        """
        if not self._unified:
            self._merged = []
            return self

        merged = []
        used = [False] * len(self._unified)

        for i, course in enumerate(self._unified):
            if used[i]:
                continue
            used[i] = True

            # 聚合同名/相似课程
            cluster = [course]
            for j in range(i + 1, len(self._unified)):
                if used[j]:
                    continue
                similarity = self._name_similarity(
                    course.get("cnm", ""),
                    self._unified[j].get("cnm", "")
                )
                if similarity >= self.SIMILARITY_THRESHOLD:
                    used[j] = True
                    cluster.append(self._unified[j])

            merged_course = self._merge_cluster(cluster)
            merged.append(merged_course)

        self._merged = merged
        duplicate_count = len(self._unified) - len(merged)
        print(f"[Aggregator] 去重完成: {len(self._unified)} → {len(merged)} 门"
              f"（合并 {duplicate_count} 门重复课程）")
        return self

    def _merge_cluster(self, cluster):
        """合并一组同名课程"""
        if len(cluster) == 1:
            return dict(cluster[0])

        base = dict(cluster[0])
        # 收集所有开课学院
        colleges_set = set()
        share_flags = []
        for c in cluster:
            colleges_set.add(c.get("share_college", ""))
            share_flags.append(c.get("share_flag", "N"))

        base["share_college"] = ",".join(sorted(colleges_set))
        base["share_flag"] = "Y" if "Y" in share_flags else "N"
        base["cross_college"] = True
        base["offered_by_count"] = len(colleges_set)
        base["offered_by"] = list(colleges_set)
        return base

    @staticmethod
    def _name_similarity(name1, name2):
        """计算两个课程名的相似度"""
        if not name1 or not name2:
            return 0.0
        # 去除括号内容后比较
        import re
        n1 = re.sub(r'[（(][^)）]*[)）]', '', name1).strip().lower()
        n2 = re.sub(r'[（(][^)）]*[)）]', '', name2).strip().lower()
        if n1 == n2:
            return 1.0
        return SequenceMatcher(None, n1, n2).ratio()

    # ================================================================
    # 筛选
    # ================================================================

    def filter_shared(self):
        """筛选仅共享课程"""
        source = self._merged if self._merged else self._unified
        self._shared = [c for c in source if c.get("share_flag") == "Y"]
        return self

    def filter_college(self, college_id):
        """筛选指定学院的课程"""
        source = self._merged if self._merged else self._unified
        return [c for c in source if c.get("share_college") == college_id]

    # ================================================================
    # 统计
    # ================================================================

    def statistics(self):
        """返回聚合统计信息"""
        courses = self._merged if self._merged else self._unified
        shared = [c for c in courses if c.get("share_flag") == "Y"]
        cross = [c for c in courses if c.get("cross_college")]

        college_counts = {}
        for cid in COLLEGES:
            college_counts[cid] = len([
                x for x in courses
                if cid in str(x.get("share_college", ""))
            ])

        return {
            "total_courses": len(courses),
            "shared_courses": len(shared),
            "cross_college_courses": len(cross),
            "by_college": college_counts,
        }

    # ================================================================
    # XML 输出
    # ================================================================

    def to_xml(self, courses=None):
        """将课程列表导出为统一XML"""
        if courses is None:
            courses = self._merged if self._merged else self._unified

        root = ET.Element("Classes")
        for c in courses:
            cls = ET.SubElement(root, "class")
            ET.SubElement(cls, "id").text = str(c.get("cno", ""))
            ET.SubElement(cls, "name").text = str(c.get("cnm", ""))
            ET.SubElement(cls, "credit").text = str(c.get("credit", ""))
            ET.SubElement(cls, "hours").text = str(c.get("hours", ""))
            ET.SubElement(cls, "teacher").text = str(c.get("teacher", ""))
            ET.SubElement(cls, "location").text = str(c.get("location", ""))
            ET.SubElement(cls, "share_flag").text = str(c.get("share_flag", "N"))
            ET.SubElement(cls, "share_college").text = str(c.get("share_college", ""))
            if c.get("cross_college"):
                ET.SubElement(cls, "cross_college").text = "true"
                ET.SubElement(cls, "offered_by").text = ",".join(c.get("offered_by", []))
        return self._pretty(root)

    def to_dict_list(self, courses=None):
        """将课程列表导出为dict列表（供JSON API使用）"""
        if courses is None:
            courses = self._merged if self._merged else self._unified
        return list(courses)

    # ================================================================
    # 内部解析
    # ================================================================

    @staticmethod
    def _parse_courses(xml_str, college_id):
        """
        解析学院返回的课程XML，处理异构字段名。
        A(SQL Server): Cno, Cnm, Ctm, Cpt, Tec, Pla, Share
        B(Oracle):     id, name, time(学时), score(学分), teacher, location, shareFlag
        C(MySQL):      Cno, Cnm, Ctm(学时), Cpt(学分), Tec, Pla, Share
        """
        courses = []
        try:
            root = ET.fromstring(xml_str)
            # 探测XML格式
            for elem in root.findall(".//class") or root.findall(".//course") or root.findall(".//Course"):
                c = {
                    "cno": (CourseAggregator._text(elem, "id")
                            or CourseAggregator._text(elem, "Cno")
                            or CourseAggregator._text(elem, "cno")
                            or CourseAggregator._text(elem, "cid")),
                    "cnm": (CourseAggregator._text(elem, "name")
                            or CourseAggregator._text(elem, "Cnm")
                            or CourseAggregator._text(elem, "cname")),
                    "credit": (CourseAggregator._text(elem, "credit")
                               or CourseAggregator._text(elem, "score")
                               or CourseAggregator._text(elem, "Cpt")),
                    "hours": (CourseAggregator._text(elem, "hours")
                              or CourseAggregator._text(elem, "time")
                              or CourseAggregator._text(elem, "Ctm")),
                    "teacher": (CourseAggregator._text(elem, "teacher")
                                or CourseAggregator._text(elem, "Tec")),
                    "location": (CourseAggregator._text(elem, "location")
                                 or CourseAggregator._text(elem, "Pla")),
                    "share_flag": (CourseAggregator._text(elem, "share")
                                   or CourseAggregator._text(elem, "Share")
                                   or CourseAggregator._text(elem, "shareFlag")
                                   or "N"),
                    "share_college": college_id,
                }
                if c["cno"]:
                    courses.append(c)
        except ET.ParseError as e:
            print(f"[Aggregator] XML解析失败 ({college_id}): {e}")
        return courses

    @staticmethod
    def _text(elem, tag):
        child = elem.find(tag)
        if child is not None and child.text:
            return child.text.strip()
        return ""

    @staticmethod
    def _pretty(root):
        rough = ET.tostring(root, encoding="unicode")
        try:
            parsed = minidom.parseString(rough)
            return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
        except Exception:
            return rough


# ================================================================
# 便捷函数 — 供外部直接调用
# ================================================================

def aggregate_shared_courses(registry):
    """快速聚合所有在线学院的共享课程"""
    aggr = CourseAggregator(registry)
    aggr.fetch_shared().normalize().deduplicate()
    return aggr


def aggregate_all_courses(registry):
    """快速聚合所有在线学院的全部课程"""
    aggr = CourseAggregator(registry)
    aggr.fetch_all().normalize().deduplicate()
    return aggr
