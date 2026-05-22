package com.edu.client;

import java.awt.BorderLayout;
import java.awt.FlowLayout;
import java.awt.GridLayout;
import java.io.IOException;

import javax.swing.JButton;
import javax.swing.JFrame;
import javax.swing.JLabel;
import javax.swing.JOptionPane;
import javax.swing.JPanel;
import javax.swing.JPasswordField;
import javax.swing.JTextField;
import javax.swing.SwingUtilities;
import javax.swing.UIManager;
import javax.swing.UnsupportedLookAndFeelException;
import javax.swing.WindowConstants;

/**
 * 登录窗口：用户名、密码，以及学生 / 管理员登录入口。
 */
public class LoginFrame extends JFrame {

    private static final long serialVersionUID = 1L;

    private final JTextField usernameField;
    private final JPasswordField passwordField;

    public LoginFrame() {
        super("教务管理系统 - 登录");
        setDefaultCloseOperation(WindowConstants.EXIT_ON_CLOSE);
        setSize(400, 180);
        setLocationRelativeTo(null);

        usernameField = new JTextField(16);
        passwordField = new JPasswordField(16);

        JPanel form = new JPanel(new GridLayout(2, 2, 6, 6));
        form.add(new JLabel("用户名："));
        form.add(usernameField);
        form.add(new JLabel("密码："));
        form.add(passwordField);

        JButton studentBtn = new JButton("学生登录");
        JButton adminBtn = new JButton("管理员登录");
        studentBtn.addActionListener(e -> doLogin("student"));
        adminBtn.addActionListener(e -> doLogin("admin"));

        JPanel buttons = new JPanel(new FlowLayout(FlowLayout.CENTER, 12, 0));
        buttons.add(studentBtn);
        buttons.add(adminBtn);

        JPanel center = new JPanel(new BorderLayout(8, 8));
        center.add(form, BorderLayout.CENTER);
        center.add(buttons, BorderLayout.SOUTH);

        getContentPane().add(center, BorderLayout.CENTER);
    }

    /**
     * 执行登录：发送 {@code LOGIN|用户名|密码|角色}，根据返回跳转主界面。
     *
     * @param role {@code student} 或 {@code admin}
     */
    private void doLogin(String role) {
        String username = usernameField.getText().trim();
        String password = new String(passwordField.getPassword());

        if (username.isEmpty()) {
            JOptionPane.showMessageDialog(this, "请输入用户名。", "提示", JOptionPane.WARNING_MESSAGE);
            return;
        }

        SocketClient client = new SocketClient();
        try {
            client.connect();
            String cmd = "LOGIN|" + username + "|" + password + "|" + role;
            client.sendMessage(cmd);
            String resp = client.receiveMessage();
            client.disconnect();

            if (resp == null) {
                JOptionPane.showMessageDialog(this, "服务器无响应。", "错误", JOptionPane.ERROR_MESSAGE);
                return;
            }

            String r = resp.trim();
            if ("SUCCESS".equalsIgnoreCase(r)) {
                dispose();
                if ("student".equalsIgnoreCase(role)) {
                    // 学生端协议使用学号；此处约定登录用户名为学号
                    new StudentFrame(username).setVisible(true);
                } else {
                    new AdminFrame().setVisible(true);
                }
            } else if ("FAIL".equalsIgnoreCase(r)) {
                JOptionPane.showMessageDialog(this, "登录失败，用户名或密码错误。", "登录失败",
                        JOptionPane.ERROR_MESSAGE);
            } else {
                JOptionPane.showMessageDialog(this, "未知响应：" + r, "提示", JOptionPane.INFORMATION_MESSAGE);
            }
        } catch (IOException ex) {
            JOptionPane.showMessageDialog(this, "连接服务器失败：" + ex.getMessage(), "错误",
                    JOptionPane.ERROR_MESSAGE);
        } finally {
            client.disconnect();
        }
    }


    //[本地测试时候用的死数据可以忽略，后续联调时会删除]
    // private void doLogin(String role) {

    //     String username = usernameField.getText().trim();
    //     String password = new String(passwordField.getPassword());

    //     if (username.isEmpty()) {
    //         JOptionPane.showMessageDialog(this,
    //                 "请输入用户名。",
    //                 "提示",
    //                 JOptionPane.WARNING_MESSAGE);
    //         return;
    //     }

    //     // ====== 假数据登录 ======

    //     // 学生账号
    //     if (role.equals("student")) {

    //         // 假设：
    //         // 用户名：1001
    //         // 密码：123456

    //         if (username.equals("1001")
    //                 && password.equals("123456")) {

    //             JOptionPane.showMessageDialog(this,
    //                     "学生登录成功！");

    //             dispose();

    //             new StudentFrame(username).setVisible(true);

    //         } else {

    //             JOptionPane.showMessageDialog(this,
    //                     "学生账号或密码错误！");
    //         }
    //     }

    //     // 管理员账号
    //     else if (role.equals("admin")) {

    //         // 假设：
    //         // 管理员：admin
    //         // 密码：admin

    //         if (username.equals("admin")
    //                 && password.equals("admin")) {

    //             JOptionPane.showMessageDialog(this,
    //                     "管理员登录成功！");

    //             dispose();

    //             new AdminFrame().setVisible(true);

    //         } else {

    //             JOptionPane.showMessageDialog(this,
    //                     "管理员账号或密码错误！");
    //         }
    //     }
    // }

    /**
     * 程序入口：启动登录界面。
     *
     * @param args 命令行参数（未使用）
     */
    public static void main(String[] args) {
        try {
            UIManager.setLookAndFeel(UIManager.getSystemLookAndFeelClassName());
        } catch (ClassNotFoundException e) {
            // 使用默认外观
        } catch (InstantiationException e) {
            // 使用默认外观
        } catch (IllegalAccessException e) {
            // 使用默认外观
        } catch (UnsupportedLookAndFeelException e) {
            // 使用默认外观
        }

        SwingUtilities.invokeLater(new Runnable() {
            @Override
            public void run() {
                new LoginFrame().setVisible(true);
            }
        });
    }
}
