package com.edu.client;

import java.util.ArrayList;
import java.util.List;

import javax.swing.table.DefaultTableModel;

/**
 * 将服务器返回的文本解析为 {@link DefaultTableModel}，供 {@link javax.swing.JTable} 使用。
 * 约定：多行数据，每行以竖线 {@code |} 分隔各列（与客户端请求协议风格一致）。
 */
public final class ServerResponseTableHelper {

    private ServerResponseTableHelper() {
    }

    /**
     * 把服务器返回的字符串转成表格模型。
     *
     * @param response 服务器原始返回（可为 null）
     * @return 非 null 的表格模型
     */
    public static DefaultTableModel parseToTableModel(String response) {
        if (response == null || response.trim().isEmpty()) {
            return emptyModel("(无数据)");
        }

        String text = response.trim();
        String[] lines = text.split("\\r?\\n");
        List<String[]> rows = new ArrayList<String[]>();
        int maxCols = 1;

        for (String line : lines) {
            if (line == null) {
                continue;
            }
            String trimmed = line.trim();
            if (trimmed.isEmpty()) {
                continue;
            }
            String[] cells = trimmed.split("\\|", -1);
            rows.add(cells);
            if (cells.length > maxCols) {
                maxCols = cells.length;
            }
        }

        if (rows.isEmpty()) {
            return emptyModel("(无数据)");
        }

        String[] columnNames = new String[maxCols];
        for (int i = 0; i < maxCols; i++) {
            columnNames[i] = "列" + (i + 1);
        }

        Object[][] data = new Object[rows.size()][maxCols];
        for (int r = 0; r < rows.size(); r++) {
            String[] cells = rows.get(r);
            for (int c = 0; c < maxCols; c++) {
                if (c < cells.length) {
                    data[r][c] = cells[c];
                } else {
                    data[r][c] = "";
                }
            }
        }

        return new DefaultTableModel(data, columnNames);
    }

    private static DefaultTableModel emptyModel(String message) {
        return new DefaultTableModel(new Object[][] { { message } }, new Object[] { "消息" });
    }
}
