package com.edu.server;

import java.sql.Connection;
import java.sql.PreparedStatement;
import java.sql.ResultSet;

public class EduService {

    public String handleCommand(String command) {
        System.out.println("收到客户端请求: " + command);
        String[] parts = command.split("\\|");
        String cmdType = parts[0];

        try {
            switch (cmdType) {
                case "LOGIN":
                    return login(parts[1], parts[2], parts[3]);
                case "GET_ALL_COURSES":
                    return getAllCourses();
                case "GET_MY_COURSES":
                    return getMyCourses(parts[1]);
                case "SELECT_COURSE":
                    return selectCourse(parts[1], parts[2]);
                case "DROP_COURSE":
                    return dropCourse(parts[1], parts[2]);
                case "GET_ALL_STUDENTS":
                    return getAllStudents();
                case "GET_STATISTICS":
                    return getStatistics();
                default:
                    return "UNKNOWN_COMMAND";
            }
        } catch (Exception e) {
            e.printStackTrace();
            return "ERROR|" + e.getMessage();
        }
    }

    private String login(String username, String password, String role) throws Exception {
        try (Connection conn = DBUtil.getConnection()) {
            String sql;
            if ("student".equals(role)) {
                sql = "SELECT Sno FROM student WHERE Sno=? AND Pwd=?";
            } else {
                sql = "SELECT acc FROM account WHERE acc=? AND passwd=?";
            }
            PreparedStatement ps = conn.prepareStatement(sql);
            ps.setString(1, username);
            ps.setString(2, password);
            ResultSet rs = ps.executeQuery();
            if (rs.next()) {
                return "SUCCESS";
            }
            return "FAIL";
        }
    }

    private String getAllCourses() throws Exception {
        StringBuilder sb = new StringBuilder("课程号|课程名|学分\n");
        try (Connection conn = DBUtil.getConnection()) {
            PreparedStatement ps = conn.prepareStatement("SELECT Cno, Cnm, Cpt FROM course");
            ResultSet rs = ps.executeQuery();
            while (rs.next()) {
                sb.append(rs.getString("Cno")).append("|")
                        .append(rs.getString("Cnm")).append("|")
                        .append(rs.getInt("Cpt")).append("\n");
            }
        }
        return sb.toString().trim();
    }

    private String getMyCourses(String sno) throws Exception {
        StringBuilder sb = new StringBuilder("课程号|课程名|学分\n");
        try (Connection conn = DBUtil.getConnection()) {
            String sql = "SELECT c.Cno, c.Cnm, c.Cpt FROM course c JOIN choice ch ON c.Cno = ch.Cno WHERE ch.Sno = ?";
            PreparedStatement ps = conn.prepareStatement(sql);
            ps.setString(1, sno);
            ResultSet rs = ps.executeQuery();
            while (rs.next()) {
                sb.append(rs.getString("Cno")).append("|")
                        .append(rs.getString("Cnm")).append("|")
                        .append(rs.getInt("Cpt")).append("\n");
            }
        }
        return sb.toString().trim();
    }

    private String selectCourse(String sno, String cno) throws Exception {
        try (Connection conn = DBUtil.getConnection()) {
            PreparedStatement checkPs = conn.prepareStatement("SELECT * FROM choice WHERE Sno=? AND Cno=?");
            checkPs.setString(1, sno);
            checkPs.setString(2, cno);
            if (checkPs.executeQuery().next()) return "提示\n该课程已经选过啦";

            PreparedStatement insertPs = conn.prepareStatement("INSERT INTO choice (Sno, Cno) VALUES (?, ?)");
            insertPs.setString(1, sno);
            insertPs.setString(2, cno);
            insertPs.executeUpdate();
            return "结果\n选课成功";
        }
    }

    private String dropCourse(String sno, String cno) throws Exception {
        try (Connection conn = DBUtil.getConnection()) {
            PreparedStatement ps = conn.prepareStatement("DELETE FROM choice WHERE Sno=? AND Cno=?");
            ps.setString(1, sno);
            ps.setString(2, cno);
            int rows = ps.executeUpdate();
            return rows > 0 ? "结果\n退课成功" : "提示\n你没有选这门课";
        }
    }

    private String getAllStudents() throws Exception {
        StringBuilder sb = new StringBuilder("学号|姓名|专业\n");
        try (Connection conn = DBUtil.getConnection()) {
            PreparedStatement ps = conn.prepareStatement("SELECT Sno, Snm, Sde FROM student");
            ResultSet rs = ps.executeQuery();
            while (rs.next()) {
                sb.append(rs.getString("Sno")).append("|")
                        .append(rs.getString("Snm")).append("|")
                        .append(rs.getString("Sde")).append("\n");
            }
        }
        return sb.toString().trim();
    }

    private String getStatistics() throws Exception {
        StringBuilder sb = new StringBuilder("课程名|选课人数\n");
        try (Connection conn = DBUtil.getConnection()) {
            String sql = "SELECT c.Cnm, COUNT(ch.Sno) as cnt FROM course c LEFT JOIN choice ch ON c.Cno = ch.Cno GROUP BY c.Cno, c.Cnm";
            PreparedStatement ps = conn.prepareStatement(sql);
            ResultSet rs = ps.executeQuery();
            while (rs.next()) {
                sb.append(rs.getString("Cnm")).append("|")
                        .append(rs.getInt("cnt")).append("\n");
            }
        }
        return sb.toString().trim();
    }
}