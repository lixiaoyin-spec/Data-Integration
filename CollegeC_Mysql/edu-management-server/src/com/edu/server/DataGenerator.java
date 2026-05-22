package com.edu.server;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Random;

public class DataGenerator {

    public static void main(String[] args) {
        System.out.println("⏳ 开始初始化教学数据库...");

        try (Connection conn = DBUtil.getConnection()) {
            conn.createStatement().execute("DELETE FROM choice");
            conn.createStatement().execute("DELETE FROM course");
            conn.createStatement().execute("DELETE FROM student");
            conn.createStatement().execute("DELETE FROM account");
            System.out.println("清理旧数据完成...");

            PreparedStatement psAcc = conn.prepareStatement("INSERT INTO account (acc, passwd) VALUES (?, ?)");
            psAcc.setString(1, "admin");
            psAcc.setString(2, "admin");
            psAcc.executeUpdate();

            String[][] courses = {
                    {"C001", "数据库原理", "64", "4", "王建国", "A101", "Y"},
                    {"C002", "操作系统", "72", "4", "李明", "B202", "N"},
                    {"C003", "计算机网络", "64", "3", "赵强", "C303", "Y"},
                    {"C004", "数据结构", "80", "5", "刘洋", "A102", "Y"},
                    {"C005", "Java编程", "48", "3", "陈飞", "B201", "N"},
                    {"C006", "软件工程", "48", "3", "张伟", "C301", "Y"},
                    {"C007", "人工智能", "64", "4", "周杰", "A103", "Y"},
                    {"C008", "编译原理", "72", "4", "吴昊", "B203", "N"},
                    {"C009", "离散数学", "64", "4", "郑爽", "C302", "N"},
                    {"C010", "算法设计", "48", "3", "孙涛", "A104", "Y"}
            };

            PreparedStatement psCourse = conn.prepareStatement(
                    "INSERT INTO course (Cno, Cnm, Ctm, Cpt, Tec, Pla, Share) VALUES (?, ?, ?, ?, ?, ?, ?)");

            List<String> courseIds = new ArrayList<>();
            for (String[] c : courses) {
                psCourse.setString(1, c[0]);
                psCourse.setString(2, c[1]);
                psCourse.setInt(3, Integer.parseInt(c[2]));
                psCourse.setInt(4, Integer.parseInt(c[3]));
                psCourse.setString(5, c[4]);
                psCourse.setString(6, c[5]);
                psCourse.setString(7, c[6]);
                psCourse.executeUpdate();
                courseIds.add(c[0]);
            }
            System.out.println("✅ 10 门课程插入完成！");

            String[] majors = {"软件工程", "计算机科学", "人工智能", "信息安全"};
            String[] surnames = {"赵", "钱", "孙", "李", "周", "吴", "郑", "王", "冯", "陈", "褚", "卫", "蒋", "沈", "韩", "杨"};
            String[] names = {"伟", "芳", "娜", "敏", "静", "强", "磊", "洋", "艳", "勇", "军", "杰", "娟", "涛", "明", "超", "秀英", "霞", "平", "刚"};
            Random random = new Random();

            PreparedStatement psStudent = conn.prepareStatement(
                    "INSERT INTO student (Sno, Snm, Sex, Sde, Pwd) VALUES (?, ?, ?, ?, ?)");
            PreparedStatement psChoice = conn.prepareStatement(
                    "INSERT INTO choice (Cno, Sno, Grd) VALUES (?, ?, ?)");

            for (int i = 1; i <= 50; i++) {
                String sno = String.format("10%02d", i);
                String pwd = "123456";
                String name = surnames[random.nextInt(surnames.length)] + names[random.nextInt(names.length)];
                String sex = random.nextBoolean() ? "M" : "F";
                String major = majors[random.nextInt(majors.length)];

                psAcc.setString(1, sno);
                psAcc.setString(2, pwd);
                psAcc.executeUpdate();

                psStudent.setString(1, sno);
                psStudent.setString(2, name);
                psStudent.setString(3, sex);
                psStudent.setString(4, major);
                psStudent.setString(5, pwd);
                psStudent.executeUpdate();

                Collections.shuffle(courseIds);
                for (int j = 0; j < 5; j++) {
                    String chosenCno = courseIds.get(j);
                    int grade = 60 + random.nextInt(41);

                    psChoice.setString(1, chosenCno);
                    psChoice.setString(2, sno);
                    psChoice.setInt(3, grade);
                    psChoice.executeUpdate();
                }
            }
            System.out.println("✅ 50 名学生及其登录账户插入完成！");
            System.out.println("✅ 每人 5 门课，共计 250 条选课记录生成完毕！");

        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}