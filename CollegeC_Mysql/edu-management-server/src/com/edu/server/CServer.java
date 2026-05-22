package com.edu.server;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

public class CServer {
    private static final int PORT = 9999;

    public static void main(String[] args) {
        System.out.println("院系 C 教务系统服务器已启动，监听端口: " + PORT);
        try (ServerSocket serverSocket = new ServerSocket(PORT)) {
            EduService service = new EduService();

            while (true) {
                Socket clientSocket = serverSocket.accept();
                System.out.println("客户端已连接: " + clientSocket.getInetAddress());

                new Thread(() -> {
                    try (BufferedReader reader = new BufferedReader(new InputStreamReader(clientSocket.getInputStream(), StandardCharsets.UTF_8));
                         PrintWriter writer = new PrintWriter(new OutputStreamWriter(clientSocket.getOutputStream(), StandardCharsets.UTF_8), true)) {

                        String command = reader.readLine();
                        if (command != null) {
                            String response = service.handleCommand(command);
                            writer.println(response);
                        }
                    } catch (Exception e) {
                        e.printStackTrace();
                    }
                }).start();
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}