package com.edu.server;

import org.dom4j.Document;
import org.dom4j.Element;
import org.dom4j.io.SAXReader;

import java.io.File;
import java.sql.Connection;
import java.sql.PreparedStatement;
import java.util.Iterator;

/**
 * XML 数据导入工具 (数据集成流入端)
 * 负责解析集成服务器发来的统一格式 XML，并同步到本地 MySQL
 */
public class XmlImporter {

    private static final String INPUT_XML = "../xml/C_System/choice_from_center.xml";

    public static void main(String[] args) {
        System.out.println("========== 开始从集成服务器导入数据 ==========");
        importChoicesFromXml(INPUT_XML);
        System.out.println("===============================================");
    }

    /**
     * 解析选课 XML 并写入数据库
     */
    public static void importChoicesFromXml(String filePath) {
        File xmlFile = new File(filePath);
        if (!xmlFile.exists()) {
            System.err.println("❌ 错误：未找到集成服务器发来的文件: " + filePath);
            return;
        }

        try (Connection conn = DBUtil.getConnection()) {
            // 1. 使用 dom4j 读取并解析 XML
            SAXReader reader = new SAXReader();
            Document document = reader.read(xmlFile);
            Element root = document.getRootElement();

            // 2. 准备 SQL 语句 (使用 INSERT IGNORE 避免重复导入报错)
            String sql = "INSERT IGNORE INTO choice (Sno, Cno, Grd) VALUES (?, ?, ?)";
            PreparedStatement ps = conn.prepareStatement(sql);

            int count = 0;
            // 3. 遍历 XML 中的每个 <choice> 节点
            for (Iterator<Element> it = root.elementIterator("choice"); it.hasNext(); ) {
                Element choice = it.next();

                // 统一格式中：sid 代表学号，cid 代表课程号
                String sid = choice.elementText("sid");
                String cid = choice.elementText("cid");
                String score = choice.elementText("score");

                ps.setString(1, sid);
                ps.setString(2, cid);
                // 如果 XML 中没有成绩，默认为 NULL
                if (score == null || score.isEmpty()) {
                    ps.setObject(3, null);
                } else {
                    ps.setInt(3, Integer.parseInt(score));
                }

                ps.executeUpdate();
                count++;
                System.out.println("  -> 已导入选课记录：学生[" + sid + "] 选修了课程[" + cid + "]");
            }

            System.out.println("✅ 导入成功！共计同步了 " + count + " 条跨系选课记录。");

        } catch (Exception e) {
            System.err.println("❌ 导入失败：解析 XML 或写入数据库时发生错误。");
            e.printStackTrace();
        }
    }
}