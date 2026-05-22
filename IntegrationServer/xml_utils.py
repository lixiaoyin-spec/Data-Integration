"""
集成服务器 — XML 工具模块
负责 XML 解析、构建与格式转换
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom


def parse_courses_xml(xml_str, college_id):
    """
    解析学院返回的课程XML, 统一为标准格式
    返回: [{cno, cnm, credit, hours, teacher, location, share_college, share_flag}]
    """
    courses = []
    try:
        root = ET.fromstring(xml_str)
        for elem in root.findall("class"):
            c = {
                "cno": _text(elem, "id"),
                "cnm": _text(elem, "name"),
                "credit": _text(elem, "credit") or _text(elem, "score"),
                "hours": _text(elem, "hours") or _text(elem, "time"),
                "teacher": _text(elem, "teacher"),
                "location": _text(elem, "location"),
                "share_college": college_id,
                "share_flag": _text(elem, "share") or _text(elem, "shareFlag") or "N",
            }
            if c["cno"]:
                courses.append(c)
    except ET.ParseError as e:
        print(f"[XML] 解析课程数据失败 ({college_id}): {e}")
    return courses


def parse_students_xml(xml_str, college_id):
    """
    解析学院返回的学生XML, 统一为标准格式
    返回: [{sno, snm, sex, major, source_college}]
    """
    students = []
    try:
        root = ET.fromstring(xml_str)
        for elem in root.findall("student"):
            s = {
                "sno": _text(elem, "id"),
                "snm": _text(elem, "name"),
                "sex": _text(elem, "sex"),
                "major": _text(elem, "major"),
                "source_college": college_id,
            }
            if s["sno"]:
                students.append(s)
    except ET.ParseError as e:
        print(f"[XML] 解析学生数据失败 ({college_id}): {e}")
    return students


def parse_transcript_xml(xml_str):
    """
    解析成绩单XML
    返回: {sid, name, major, courses: [{cid, cname, credit, score, status}]}
    """
    try:
        root = ET.fromstring(xml_str)
        result = {
            "sid": root.get("sid", ""),
            "name": root.get("name", ""),
            "major": root.get("major", ""),
            "courses": [],
        }
        for elem in root.findall("Course"):
            result["courses"].append({
                "cid": _text(elem, "cid"),
                "cname": _text(elem, "cname"),
                "credit": _text(elem, "credit"),
                "score": _text(elem, "score"),
                "status": _text(elem, "status"),
            })
        return result
    except ET.ParseError as e:
        print(f"[XML] 解析成绩单失败: {e}")
        return None


def build_unified_courses_xml(courses_list):
    """
    构建集成服务器的统一课程XML
    courses_list: [{cno, cnm, credit, hours, teacher, location, share_college, share_flag}]
    """
    root = ET.Element("Classes")
    for c in courses_list:
        cls = ET.SubElement(root, "class")
        ET.SubElement(cls, "id").text = c.get("cno", "")
        ET.SubElement(cls, "name").text = c.get("cnm", "")
        ET.SubElement(cls, "credit").text = str(c.get("credit", ""))
        ET.SubElement(cls, "hours").text = str(c.get("hours", ""))
        ET.SubElement(cls, "teacher").text = c.get("teacher", "")
        ET.SubElement(cls, "location").text = c.get("location", "")
        ET.SubElement(cls, "share_college").text = c.get("share_college", "")
        ET.SubElement(cls, "share_flag").text = c.get("share_flag", "N")
    return _pretty_xml(root)


def build_unified_students_xml(students_list):
    """
    构建集成服务器的统一学生XML
    """
    root = ET.Element("Students")
    for s in students_list:
        stu = ET.SubElement(root, "student")
        ET.SubElement(stu, "id").text = s.get("sno", "")
        ET.SubElement(stu, "name").text = s.get("snm", "")
        ET.SubElement(stu, "sex").text = s.get("sex", "")
        ET.SubElement(stu, "major").text = s.get("major", "")
        ET.SubElement(stu, "college").text = s.get("source_college", "")
    return _pretty_xml(root)


def build_enrollment_import_xml(sno, cno, grd=""):
    """构建选课导入XML"""
    root = ET.Element("Enrollment")
    ET.SubElement(root, "sno").text = sno
    ET.SubElement(root, "cno").text = cno
    ET.SubElement(root, "grd").text = grd
    return _pretty_xml(root)


def build_student_import_xml(sno, snm, sex, sde):
    """构建学生导入XML"""
    root = ET.Element("student")
    ET.SubElement(root, "id").text = sno
    ET.SubElement(root, "name").text = snm
    ET.SubElement(root, "sex").text = sex
    ET.SubElement(root, "major").text = sde
    return _pretty_xml(root)


# ---- 内部辅助 ----

def _text(elem, tag):
    child = elem.find(tag)
    if child is not None and child.text:
        return child.text.strip()
    return ""


def _pretty_xml(root):
    rough = ET.tostring(root, encoding="unicode")
    try:
        parsed = minidom.parseString(rough)
        return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")
    except Exception:
        return rough
