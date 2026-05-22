package com.edu.client;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.io.OutputStreamWriter;
import java.io.PrintWriter;
import java.net.Socket;
import java.nio.charset.StandardCharsets;

/**
 * 封装与服务器的 Socket 通信。
 * 默认连接 localhost:9999。
 */
public class SocketClient {

    /** 默认服务器主机 */
    public static final String DEFAULT_HOST = "localhost";

    /** 默认服务器端口 */
    public static final int DEFAULT_PORT = 9999;

    private final String host;
    private final int port;

    private Socket socket;
    private BufferedReader reader;
    private PrintWriter writer;

    public SocketClient() {
        this(DEFAULT_HOST, DEFAULT_PORT);
    }

    public SocketClient(String host, int port) {
        this.host = host;
        this.port = port;
    }

    /**
     * 建立到服务器的连接。
     *
     * @throws IOException 连接失败时抛出
     */
    public void connect() throws IOException {
        disconnect();
        socket = new Socket(host, port);
        reader = new BufferedReader(
                new InputStreamReader(socket.getInputStream(), StandardCharsets.UTF_8));
        writer = new PrintWriter(new OutputStreamWriter(
                socket.getOutputStream(), StandardCharsets.UTF_8), true);
    }

    /**
     * 向服务器发送一行文本（自动追加换行，便于服务器按行读取）。
     *
     * @param msg 要发送的消息
     * @throws IllegalStateException 未连接时调用
     */
    public void sendMessage(String msg) {
        if (writer == null) {
            throw new IllegalStateException("请先调用 connect() 建立连接");
        }
        writer.println(msg);
    }

    /**
     * 从服务器读取完整的响应文本（支持多行读取）。
     *
     * @return 服务器返回的完整文本
     * @throws IOException 读取失败时抛出
     */
    public String receiveMessage() throws IOException {
        if (reader == null) {
            throw new IllegalStateException("请先调用 connect() 建立连接");
        }
        StringBuilder sb = new StringBuilder();
        String line;
        // 循环读取，直到服务器端发送完毕并关闭连接（此时返回 null）
        while ((line = reader.readLine()) != null) {
            sb.append(line).append("\n");
        }
        return sb.toString();
    }

    /**
     * 关闭连接并释放资源。
     */
    public void disconnect() {
        try {
            if (socket != null && !socket.isClosed()) {
                socket.close();
            }
        } catch (IOException ignored) {
            // 忽略关闭异常
        }
        reader = null;
        writer = null;
        socket = null;
    }
}
