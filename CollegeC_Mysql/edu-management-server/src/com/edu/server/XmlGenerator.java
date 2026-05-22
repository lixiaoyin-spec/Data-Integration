package com.edu.server;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStreamWriter;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.ResultSetMetaData;

import org.dom4j.Document;
import org.dom4j.DocumentHelper;
import org.dom4j.Element;
import org.dom4j.io.OutputFormat;
import org.dom4j.io.XMLWriter;

/**
 * 院系C 的 XML 生成工具类
 * 负责将 MySQL 中的数据导出为本地格式的 XML 文件
 */
public class XmlGenerator {

    // 定义 XML 文件的保存路径（保存在项目根目录的 xml 文件夹下）
    private static final String XML_OUTPUT_DIR = "../xml/C_System/";

    public static void main(String[] args) {
        // 先确保输出文件夹存在
        File dir = new File(XML_OUTPUT_DIR);
        if (!dir.exists()) {
            dir.mkdirs();
        }

        System.out.println("⏳ 开始生成 C院系 的 XML 数据文件...");

        // 依次导出三张表的数据
        exportTableToXml("student", "Students", "student", "studentC.xml");
        exportTableToXml("course", "Courses", "course", "classC.xml");
        exportTableToXml("choice", "Choices", "choice", "choiceC.xml");

        System.out.println("✅ XML 文件生成完毕！请去项目根目录的 xml/C_System 文件夹查看！");
    }

    /**
     * 通用的数据库表转 XML 方法
     *
     * @param tableName  数据库表名 (如 student)
     * @param rootName   XML 根节点名称 (如 Students)
     * @param rowName    XML 行节点名称 (如 student)
     * @param outputName 输出的文件名 (如 studentC.xml)
     */
    public static void exportTableToXml(String tableName, String rootName, String rowName, String outputName) {
        try (Connection conn = DBUtil.getConnection()) {
            String sql = "SELECT * FROM " + tableName;
            PreparedStatement ps = conn.prepareStatement(sql);
            ResultSet rs = ps.executeQuery();

            // 1. 获取表的元数据（为了拿到列名）
            ResultSetMetaData rsmd = rs.getMetaData();
            int columnCount = rsmd.getColumnCount();

            // 2. 创建 XML 文档对象和根节点
            Document doc = DocumentHelper.createDocument();
            Element root = doc.addElement(rootName);

            // 3. 遍历数据库结果集，生成 XML 节点
            while (rs.next()) {
                Element rowElement = root.addElement(rowName); // 创建如 <student> 节点
                for (int i = 1; i <= columnCount; i++) {
                    String columnName = rsmd.getColumnName(i);
                    Element columnElement = rowElement.addElement(columnName); // 创建如 <Sno> 节点
                    Object value = rs.getObject(i);
                    // 将数据库的值写入 XML 节点
                    if (value != null) {
                        columnElement.setText(value.toString());
                    } else {
                        columnElement.setText("");
                    }
                }
            }

            // 4. 将生成的 XML 写入到文件
            String filePath = XML_OUTPUT_DIR + outputName;

            // 设置 XML 格式（带缩进和换行，采用 GB2312 编码，匹配 PDF 要求）
            OutputFormat format = OutputFormat.createPrettyPrint();
            format.setEncoding("GB2312");

            // 使用 OutputStreamWriter 确保编码正确写入
            OutputStreamWriter osw = new OutputStreamWriter(new FileOutputStream(filePath), "GB2312");
            XMLWriter writer = new XMLWriter(osw, format);
            writer.write(doc);

            writer.close();
            osw.close();

            System.out.println("  -> 成功生成: " + filePath);

        } catch (Exception e) {
            System.err.println("❌ 生成 " + outputName + " 时发生错误！");
            e.printStackTrace();
        }
    }
}