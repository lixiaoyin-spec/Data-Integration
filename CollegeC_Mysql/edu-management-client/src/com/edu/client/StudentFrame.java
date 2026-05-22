package com.edu.client;

import java.awt.BorderLayout;
import java.awt.Dimension;
import java.awt.FlowLayout;
import java.io.IOException;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.JToolBar;
import javax.swing.ListSelectionModel;
import javax.swing.SwingUtilities;
import javax.swing.WindowConstants;
import javax.swing.table.DefaultTableModel;

/**
 * 学生主界面：左侧功能菜单，右侧 {@link JTable} 展示服务器返回数据。
 */
public class StudentFrame extends JFrame {

    private static final long serialVersionUID = 1L;

    /** 当前登录学生学号（与登录用户名一致） */
    private final String studentId;

    private final JTable table;
    private final DefaultTableModel emptyModel;

    public StudentFrame(String studentId) {
        super("教务管理系统 - 学生端");
        this.studentId = studentId;

        setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
        setSize(800, 480);
        setLocationRelativeTo(null);

        emptyModel = new DefaultTableModel(new Object[][] { { "请选择左侧功能" } },
                new Object[] { "提示" });
        table = new JTable(emptyModel);
        table.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        table.setFillsViewportHeight(true);

        JScrollPane scroll = new JScrollPane(table);

        JPanel left = buildMenuPanel();

        getContentPane().add(left, BorderLayout.WEST);
        getContentPane().add(scroll, BorderLayout.CENTER);
    }

    private JPanel buildMenuPanel() {
        JPanel panel = new JPanel(new FlowLayout(FlowLayout.CENTER, 0, 8));
        panel.setPreferredSize(new Dimension(160, 0));

        JToolBar bar = new JToolBar(JToolBar.VERTICAL);
        bar.setFloatable(false);

        bar.add(makeMenuButton("查看课程", new Runnable() {
            @Override
            public void run() {
                sendAndShowTable("GET_ALL_COURSES");
            }
        }));
        bar.add(makeMenuButton("查看已选课程", new Runnable() {
            @Override
            public void run() {
                sendAndShowTable("GET_MY_COURSES|" + studentId);
            }
        }));
        bar.add(makeMenuButton("选课", new Runnable() {
            @Override
            public void run() {
                String courseId = JOptionPane.showInputDialog(StudentFrame.this, "请输入课程号：", "选课",
                        JOptionPane.PLAIN_MESSAGE);
                if (courseId == null) {
                    return;
                }
                courseId = courseId.trim();
                if (courseId.isEmpty()) {
                    JOptionPane.showMessageDialog(StudentFrame.this, "课程号不能为空。", "提示",
                            JOptionPane.WARNING_MESSAGE);
                    return;
                }
                sendAndShowTable("SELECT_COURSE|" + studentId + "|" + courseId);
            }
        }));
        bar.add(makeMenuButton("退课", new Runnable() {
            @Override
            public void run() {
                String courseId = JOptionPane.showInputDialog(StudentFrame.this, "请输入课程号：", "退课",
                        JOptionPane.PLAIN_MESSAGE);
                if (courseId == null) {
                    return;
                }
                courseId = courseId.trim();
                if (courseId.isEmpty()) {
                    JOptionPane.showMessageDialog(StudentFrame.this, "课程号不能为空。", "提示",
                            JOptionPane.WARNING_MESSAGE);
                    return;
                }
                sendAndShowTable("DROP_COURSE|" + studentId + "|" + courseId);
            }
        }));
        bar.add(makeMenuButton("退出登录", new Runnable() {
            @Override
            public void run() {
                dispose();
                SwingUtilities.invokeLater(new Runnable() {
                    @Override
                    public void run() {
                        new LoginFrame().setVisible(true);
                    }
                });
            }
        }));

        panel.add(bar);
        return panel;
    }

    private JButton makeMenuButton(String text, final Runnable action) {
        JButton b = new JButton(text);
        b.setAlignmentX(JButton.CENTER_ALIGNMENT);
        b.addActionListener(e -> action.run());
        return b;
    }

    /**
     * 发送一条命令，将服务器返回内容显示在表格中。
     *
     * @param command 协议字符串
     */
    private void sendAndShowTable(String command) {
        SocketClient client = new SocketClient();
        try {
            client.connect();
            client.sendMessage(command);
            String resp = client.receiveMessage();
            client.disconnect();

            DefaultTableModel model = ServerResponseTableHelper.parseToTableModel(resp);
            table.setModel(model);
        } catch (IOException ex) {
            JOptionPane.showMessageDialog(this, "通信失败：" + ex.getMessage(), "错误",
                    JOptionPane.ERROR_MESSAGE);
            table.setModel(emptyModel);
        } finally {
            client.disconnect();
        }
    }
    
    //[本地测试时候用的死数据可以忽略，后续联调时会删除]
    // private void sendAndShowTable(String command) {

    //     String resp = "";

    //     // 查看所有课程
    //     if (command.equals("GET_ALL_COURSES")) {

    //         resp =
    //                 "课程号|课程名|学分\n" +
    //                 "C001|数据库|3\n" +
    //                 "C002|操作系统|4\n" +
    //                 "C003|计算机网络|3";

    //     }

    //     // 查看已选课程
    //     else if (command.startsWith("GET_MY_COURSES")) {

    //         resp =
    //                 "课程号|课程名|学分\n" +
    //                 "C001|数据库|3\n" +
    //                 "C003|计算机网络|3";

    //     }

    //     // 选课
    //     else if (command.startsWith("SELECT_COURSE")) {

    //         resp =
    //                 "结果\n" +
    //                 "选课成功";

    //     }

    //     // 退课
    //     else if (command.startsWith("DROP_COURSE")) {

    //         resp =
    //                 "结果\n" +
    //                 "退课成功";

    //     }

    //     // 转换成 JTable
    //     DefaultTableModel model =
    //             ServerResponseTableHelper.parseToTableModel(resp);

    //     table.setModel(model);
    // }
}
