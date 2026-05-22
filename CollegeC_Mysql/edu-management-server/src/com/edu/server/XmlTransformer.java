package com.edu.server;

import javax.xml.transform.Transformer;
import javax.xml.transform.TransformerFactory;
import javax.xml.transform.stream.StreamResult;
import javax.xml.transform.stream.StreamSource;
import java.io.File;

/**
 * XML 格式转换工具类 (XSLT 引擎)
 * 负责将 C 院系的本地 XML 转换为 全校统一格式的 XML
 */
public class XmlTransformer {

    private static final String XML_DIR = "../xml/C_System/";

    public static void main(String[] args) {
        System.out.println("========== 开始 XML 格式转换 (XSLT) ==========");

        // 1. 转换学生数据
        transformXml(XML_DIR + "studentC.xml",
                XML_DIR + "studentCToUniform.xsl",
                XML_DIR + "uniform_student.xml");

        // 2. 转换课程数据
        transformXml(XML_DIR + "classC.xml",
                XML_DIR + "courseCToUniform.xsl",
                XML_DIR + "uniform_course.xml");

        // 3. 转换选课数据
        transformXml(XML_DIR + "choiceC.xml",
                XML_DIR + "choiceCToUniform.xsl",
                XML_DIR + "uniform_choice.xml");

        System.out.println("==============================================");
        System.out.println("✅ 转换大功告成！所有统一格式的文件已生成。");
    }

    /**
     * 核心转换逻辑
     * @param sourcePath 原 XML 文件路径
     * @param xsltPath   XSL 转换规则文件路径
     * @param outputPath 转换后生成的新 XML 文件路径
     */
    public static void transformXml(String sourcePath, String xsltPath, String outputPath) {
        try {
            // 创建转换工厂
            TransformerFactory factory = TransformerFactory.newInstance();
            // 加载 XSL 规则文件
            StreamSource xslStream = new StreamSource(new File(xsltPath));
            Transformer transformer = factory.newTransformer(xslStream);

            // 加载原 XML 数据
            StreamSource in = new StreamSource(new File(sourcePath));
            // 设置输出路径
            StreamResult out = new StreamResult(new File(outputPath));

            // 执行转换！
            transformer.transform(in, out);

            System.out.println("  -> 成功生成统一格式: " + outputPath);
        } catch (Exception e) {
            System.err.println("❌ 转换失败: " + sourcePath);
            e.printStackTrace();
        }
    }
}