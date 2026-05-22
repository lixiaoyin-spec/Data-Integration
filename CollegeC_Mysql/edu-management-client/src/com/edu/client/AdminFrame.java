package com.edu.client;

import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.io.IOException;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JScrollPane;
import javax.swing.JTable;
import javax.swing.ListSelectionModel;
import javax.swing.SwingUtilities;
import javax.swing.WindowConstants;
import javax.swing.table.DefaultTableModel;

/**
 * 管理员主界面：功能按钮 + {@link JTable} 展示查询结果。
 */
public class AdminFrame extends JFrame {

    private static final long serialVersionUID = 1L;

    private final JTable table;
    private final DefaultTableModel emptyModel;

    public AdminFrame() {
        super("教务管理系统 - 管理员端");
        setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
        setSize(800, 480);
        setLocationRelativeTo(null);

        emptyModel = new DefaultTableModel(new Object[][] { { "请点击上方功能按钮" } },
                new Object[] { "提示" });
        table = new JTable(emptyModel);
        table.setSelectionMode(ListSelectionModel.SINGLE_SELECTION);
        table.setFillsViewportHeight(true);

        JPanel top = new JPanel(new FlowLayout(FlowLayout.LEFT, 8, 8));
        top.add(makeActionButton("查看所有学生", "GET_ALL_STUDENTS"));
        top.add(makeActionButton("查看所有课程", "GET_ALL_COURSES"));
        top.add(makeActionButton("查看选课统计", "GET_STATISTICS"));
        top.add(makeActionButton("退出登录", null));

        getContentPane().add(top, BorderLayout.NORTH);
        getContentPane().add(new JScrollPane(table), BorderLayout.CENTER);
    }

    private JButton makeActionButton(String text, final String commandOrNull) {
        JButton b = new JButton(text);
        b.addActionListener(e -> {
            if (commandOrNull == null) {
                doLogout();
            } else {
                sendAndShowTable(commandOrNull);
            }
        });
        return b;
    }

    private void doLogout() {
        dispose();
        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                new LoginFrame().setVisible(true);
            }
        });
    }

    /**
     * 发送管理员查询命令并刷新表格。
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

    //     // 查看所有学生
    //     if (command.equals("GET_ALL_STUDENTS")) {

    //         resp =
    //                 "学号|姓名|专业\n" +
    //                 "1001|张三|软件工程\n" +
    //                 "1002|李四|计算机科学\n" +
    //                 "1003|王五|人工智能";
    //     }

    //     // 查看所有课程
    //     else if (command.equals("GET_ALL_COURSES")) {

    //         resp =
    //                 "课程号|课程名|学分\n" +
    //                 "C001|数据库|3\n" +
    //                 "C002|操作系统|4\n" +
    //                 "C003|计算机网络|3";
    //     }

    //     // 查看统计
    //     else if (command.equals("GET_STATISTICS")) {

    //         resp =
    //                 "课程名|选课人数\n" +
    //                 "数据库|35\n" +
    //                 "操作系统|42\n" +
    //                 "计算机网络|28";
    //     }

    //     DefaultTableModel model =
    //             ServerResponseTableHelper.parseToTableModel(resp);

    //     table.setModel(model);
    // }
}
