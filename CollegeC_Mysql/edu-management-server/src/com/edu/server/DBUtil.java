package com.edu.server;

import java.sql.Connection;
import java.sql.DriverManager;

public class DBUtil {
    private static final String URL = "jdbc:mysql://localhost:3306/teaching_c?useSSL=false&characterEncoding=UTF-8";
    private static final String USER = "root";      // 注意：改成你的MySQL账号
    private static final String PASS = "123456";    // 注意：改成你的MySQL密码

    static {
        try {
            Class.forName("com.mysql.cj.jdbc.Driver");
        } catch (ClassNotFoundException e) {
            e.printStackTrace();
        }
    }

    public static Connection getConnection() throws Exception {
        return DriverManager.getConnection(URL, USER, PASS);
    }
}