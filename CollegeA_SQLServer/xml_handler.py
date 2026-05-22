"""
College A - XML 数据处理模块
用于异构数据集成的XML导入/导出、格式转换和验证
支持：
  - 数据库 → XML 导出（学院A原生格式 + 标准集成格式）
  - XML → 数据库 导入
  - XSD Schema 验证（使用 lxml）
  - XSLT 格式转换（使用 lxml）
"""
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from config import COLLEGE_ID

# lxml 用于 XSD 验证和 XSLT 转换
from lxml import etree


class XMLHandler:
    """XML 处理器"""

    # ================================================================
    # 导出：数据库 → XML（标准集成格式，用于跨学院数据交换）
    # ================================================================

    @staticmethod
    def export_students_to_xml(students_data, filepath):
        """
        导出学生数据为标准集成XML格式
        students_data: [(Sno, Snm, Sex, Sde, Pwd), ...]
        XML标签: <Students><student><id><name><sex><major>
        """
        root = ET.Element("Students")
        for sno, snm, sex, sde, pwd in students_data:
            student = ET.SubElement(root, "student")
            ET.SubElement(student, "id").text = sno
            ET.SubElement(student, "name").text = snm
            ET.SubElement(student, "sex").text = sex
            ET.SubElement(student, "major").text = sde
        XMLHandler._write_xml(root, filepath)
        return filepath

    @staticmethod
    def export_courses_to_xml(courses_data, filepath):
        """
        导出课程数据为标准集成XML格式
        courses_data: [(Cno, Cnm, Ctm, Cpt, Tec, Pla, Share), ...]
        XML标签: <Classes><class><id><name><score><teacher><location><share>
        """
        root = ET.Element("Classes")
        for row in courses_data:
            cno, cnm, ctm, cpt, tec, pla, share = row
            cls = ET.SubElement(root, "class")
            ET.SubElement(cls, "id").text = cno
            ET.SubElement(cls, "name").text = cnm
            ET.SubElement(cls, "score").text = str(ctm) if ctm else ""
            ET.SubElement(cls, "teacher").text = tec
            ET.SubElement(cls, "location").text = pla
            ET.SubElement(cls, "share").text = share if share else ""
        XMLHandler._write_xml(root, filepath)
        return filepath

    @staticmethod
    def export_selections_to_xml(selections_data, filepath):
        """
        导出选课数据为标准集成XML格式
        selections_data: [(Sno, Snm, Cno, Cnm, Grd, Share), ...]
        XML标签: <Choices><choice><sid><cid><score>
        """
        root = ET.Element("Choices")
        for row in selections_data:
            sno, snm, cno, cnm, grd, share = row
            choice = ET.SubElement(root, "choice")
            ET.SubElement(choice, "sid").text = sno
            ET.SubElement(choice, "cid").text = cno
            ET.SubElement(choice, "score").text = grd if grd else ""
        XMLHandler._write_xml(root, filepath)
        return filepath

    # ================================================================
    # 导出：原生格式（保留学院A原始字段名，用于本地备份）
    # ================================================================

    @staticmethod
    def export_students_native(students_data, filepath):
        """导出学生数据为学院A原生XML格式"""
        root = ET.Element("Students")
        for sno, snm, sex, sde, pwd in students_data:
            student = ET.SubElement(root, "student")
            ET.SubElement(student, "Sno").text = sno
            ET.SubElement(student, "Snm").text = snm
            ET.SubElement(student, "Sex").text = sex
            ET.SubElement(student, "Sde").text = sde
            ET.SubElement(student, "Pwd").text = pwd
        XMLHandler._write_xml(root, filepath)
        return filepath

    @staticmethod
    def export_courses_native(courses_data, filepath):
        """导出课程数据为学院A原生XML格式"""
        root = ET.Element("Classes")
        for row in courses_data:
            cno, cnm, ctm, cpt, tec, pla, share = row
            cls = ET.SubElement(root, "class")
            ET.SubElement(cls, "Cno").text = cno
            ET.SubElement(cls, "Cnm").text = cnm
            ET.SubElement(cls, "Ctm").text = str(ctm) if ctm else ""
            ET.SubElement(cls, "Cpt").text = str(cpt) if cpt else ""
            ET.SubElement(cls, "Tec").text = tec
            ET.SubElement(cls, "Pla").text = pla
            ET.SubElement(cls, "Share").text = share if share else ""
        XMLHandler._write_xml(root, filepath)
        return filepath

    @staticmethod
    def export_selections_native(selections_data, filepath):
        """导出选课数据为学院A原生XML格式"""
        root = ET.Element("Choices")
        for row in selections_data:
            sno, snm, cno, cnm, grd, share = row
            choice = ET.SubElement(root, "choice")
            ET.SubElement(choice, "Sno").text = sno
            ET.SubElement(choice, "Cno").text = cno
            ET.SubElement(choice, "Grd").text = grd if grd else ""
        XMLHandler._write_xml(root, filepath)
        return filepath

    # ================================================================
    # 导入：标准集成XML格式 → 数据库记录
    # ================================================================

    @staticmethod
    def import_students_from_xml(filepath):
        """
        从标准集成XML导入学生数据
        返回: [(sno, snm, sex, sde, pwd), ...]
        """
        tree = ET.parse(filepath)
        root = tree.getroot()
        students = []
        for stu_elem in root.findall("student"):
            sno = XMLHandler._get_text(stu_elem, "id")
            snm = XMLHandler._get_text(stu_elem, "name")
            sex = XMLHandler._get_text(stu_elem, "sex")
            sde = XMLHandler._get_text(stu_elem, "major")
            pwd = sno  # 默认密码为学号
            if sno:
                students.append((sno, snm, sex, sde, pwd))
        return students

    @staticmethod
    def import_courses_from_xml(filepath):
        """
        从标准集成XML导入课程数据
        返回: [(cno, cnm, ctm, cpt, tec, pla, share), ...]
        """
        tree = ET.parse(filepath)
        root = tree.getroot()
        courses = []
        for cls_elem in root.findall("class"):
            cno = XMLHandler._get_text(cls_elem, "id")
            cnm = XMLHandler._get_text(cls_elem, "name")
            ctm = XMLHandler._get_text(cls_elem, "score")
            tec = XMLHandler._get_text(cls_elem, "teacher")
            pla = XMLHandler._get_text(cls_elem, "location")
            share = XMLHandler._get_text(cls_elem, "share")
            if cno:
                courses.append((cno, cnm, ctm, "", tec, pla, share))
        return courses

    @staticmethod
    def import_selections_from_xml(filepath):
        """
        从标准集成XML导入选课数据
        返回: [(sno, cno, grd), ...]
        """
        tree = ET.parse(filepath)
        root = tree.getroot()
        selections = []
        for ch_elem in root.findall("choice"):
            sno = XMLHandler._get_text(ch_elem, "sid")
            cno = XMLHandler._get_text(ch_elem, "cid")
            grd = XMLHandler._get_text(ch_elem, "score")
            if sno and cno:
                selections.append((sno, cno, grd))
        return selections

    # ================================================================
    # XSD Schema 验证
    # ================================================================
    @staticmethod
    def get_xsd_dir():
        base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, "xsd")

    @staticmethod
    def get_xslt_dir():
        base = os.path.dirname(os.path.abspath(__file__))
        return os.path.join(base, "xslt")

    @staticmethod
    def validate_xml(xml_path, xsd_path):
        """使用 XSD Schema 验证 XML 文件，返回 (is_valid, errors)"""
        errors = []
        try:
            xsd_doc = etree.parse(xsd_path)
            xsd_schema = etree.XMLSchema(xsd_doc)
            xml_doc = etree.parse(xml_path)
            xsd_schema.assertValid(xml_doc)
            return True, []
        except etree.DocumentInvalid:
            for err in xsd_schema.error_log:
                errors.append(f"行{err.line}: {err.message}")
            return False, errors
        except Exception as e:
            errors.append(f"验证异常: {e}")
            return False, errors

    @staticmethod
    def validate_students_xml(xml_path, is_native=True):
        xsd_file = os.path.join(XMLHandler.get_xsd_dir(),
                                "studentA.xsd" if is_native else "formatStudent.xsd")
        return XMLHandler.validate_xml(xml_path, xsd_file)

    @staticmethod
    def validate_courses_xml(xml_path, is_native=True):
        xsd_file = os.path.join(XMLHandler.get_xsd_dir(),
                                "classA.xsd" if is_native else "formatClass.xsd")
        return XMLHandler.validate_xml(xml_path, xsd_file)

    @staticmethod
    def validate_selections_xml(xml_path, is_native=True):
        xsd_file = os.path.join(XMLHandler.get_xsd_dir(),
                                "choiceA.xsd" if is_native else "formatClassChoice.xsd")
        return XMLHandler.validate_xml(xml_path, xsd_file)

    # ================================================================
    # XSLT 格式转换
    # ================================================================
    @staticmethod
    def transform_xml(xml_path, xslt_path, output_path=None):
        """使用 XSLT 转换 XML，返回结果字符串或输出文件路径"""
        try:
            xml_doc = etree.parse(xml_path)
            xslt_doc = etree.parse(xslt_path)
            transform = etree.XSLT(xslt_doc)
            result_tree = transform(xml_doc)
            result_str = str(result_tree)
            if output_path:
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result_str)
                return output_path
            return result_str
        except Exception as e:
            raise RuntimeError(f"XSLT转换失败: {e}")

    @staticmethod
    def native_to_standard(xml_path, data_type, output_path):
        """学院原生XML → 标准集成格式"""
        xslt_map = {
            "students": "formatStudent.xsl",
            "courses": "formatClass.xsl",
            "selections": "formatClassChoice.xsl",
        }
        xslt_file = os.path.join(XMLHandler.get_xslt_dir(), xslt_map[data_type])
        return XMLHandler.transform_xml(xml_path, xslt_file, output_path)

    @staticmethod
    def standard_to_native(xml_path, data_type, target_college, output_path):
        """标准集成XML → 学院原生格式"""
        xslt_map = {
            "students": f"studentTo{target_college}.xsl",
            "courses": f"classTo{target_college}.xsl",
            "selections": f"choiceTo{target_college}.xsl",
        }
        xslt_file = os.path.join(XMLHandler.get_xslt_dir(), xslt_map[data_type])
        return XMLHandler.transform_xml(xml_path, xslt_file, output_path)

    # ================================================================
    # 辅助方法
    # ================================================================

    @staticmethod
    def _get_text(parent, tag):
        elem = parent.find(tag)
        return elem.text.strip() if elem is not None and elem.text else ""

    @staticmethod
    def _write_xml(root, filepath):
        """美化XML并写入文件"""
        rough = ET.tostring(root, encoding="utf-8")
        parsed = minidom.parseString(rough)
        pretty = parsed.toprettyxml(indent="  ", encoding="utf-8")
        with open(filepath, "wb") as f:
            f.write(pretty)

    @staticmethod
    def pretty_print_xml(filepath):
        """读取并美化打印XML文件内容"""
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
