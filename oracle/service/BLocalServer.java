import com.sun.net.httpserver.HttpExchange;
import com.sun.net.httpserver.HttpServer;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.OutputStream;
import java.net.InetSocketAddress;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.PreparedStatement;
import java.sql.ResultSet;
import java.sql.SQLException;
import java.sql.Statement;
import java.util.HashMap;
import java.util.Map;

/**
 * B系统本地服务器（Oracle）
 *
 * 作用：
 * 1. 接收客户端请求
 * 2. 调用Oracle本地过程/查询
 * 3. 返回JSON/XML文本结果
 * 4. 为后续集成服务器转发提供统一入口
 */
public class BLocalServer {

    private static final int DEFAULT_PORT = 8082;
    private final OracleBRepository repository;

    public BLocalServer(OracleBRepository repository) {
        this.repository = repository;
    }

    public static void main(String[] args) throws Exception {
        OracleBRepository repository = new OracleBRepository(
                "jdbc:oracle:thin:@localhost:1521/orcl",
                "BUSER",
                "BPASS"
        );
        BLocalServer server = new BLocalServer(repository);
        server.start(DEFAULT_PORT);
    }

    public void start(int port) throws IOException {
        HttpServer httpServer = HttpServer.create(new InetSocketAddress(port), 0);
        httpServer.createContext("/", this::handleHome);
        httpServer.createContext("/b/login", this::handleLogin);
        httpServer.createContext("/b/courses", this::handleListCourses);
        httpServer.createContext("/b/shared-courses", this::handleListSharedCourses);
        httpServer.createContext("/b/shared-courses/xml", this::handleExportSharedCoursesXml);
        httpServer.createContext("/b/shared-courses/feed", this::handleSharedCoursesFeed);
        httpServer.createContext("/b/students", this::handleListStudents);
        httpServer.createContext("/b/enroll", this::handleEnroll);
        httpServer.createContext("/b/enroll/xml", this::handleEnrollFromXml);
        httpServer.createContext("/b/enroll/batch", this::handleBatchEnrollFromXml);
        httpServer.createContext("/b/drop", this::handleDrop);
        httpServer.createContext("/b/drop/xml", this::handleDropFromXml);
        httpServer.createContext("/b/transcript", this::handleTranscript);
        httpServer.createContext("/b/transcript/xml", this::handleTranscriptXml);
        httpServer.createContext("/b/api/status", this::handleStatus);
        httpServer.createContext("/b/students/xml", this::handleStudentsXml);
        httpServer.createContext("/b/courses/xml", this::handleCoursesXml);
        httpServer.createContext("/b/selections/xml", this::handleSelectionsXml);
        httpServer.createContext("/b/students/import", this::handleImportStudent);
        httpServer.createContext("/b/enrollments/import", this::handleImportEnrollment);
        httpServer.createContext("/b/statistics", this::handleStatistics);
        httpServer.setExecutor(null);
        httpServer.start();
        System.out.println("B Local Server started on port " + port);
    }

    private void handleHome(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        sendText(exchange, 200, FrontendPage.HTML, "text/html; charset=UTF-8");
    }

    private void handleStatus(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        try {
            sendText(exchange, 200, repository.getCounts(), "application/json; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 200, "{\"status\":\"running\",\"system\":\"B-Oracle\"}", "application/json; charset=UTF-8");
        }
    }

    private void handleLogin(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        Map<String, String> form = parseForm(readBody(exchange.getRequestBody()));
        String acc = form.getOrDefault("acc", "");
        String pwd = form.getOrDefault("pwd", "");
        try {
            boolean ok = repository.login(acc, pwd);
            sendText(exchange, 200, ok ? "{\"status\":\"success\"}" : "{\"status\":\"fail\"}", "application/json; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleListCourses(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        try {
            sendText(exchange, 200, repository.listCoursesAsXml(false), "application/xml; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleListSharedCourses(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        try {
            sendText(exchange, 200, repository.listCoursesAsXml(true), "application/xml; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleExportSharedCoursesXml(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        try {
            sendText(exchange, 200, repository.exportSharedCoursesXml(), "application/xml; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleSharedCoursesFeed(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        try {
            sendText(exchange, 200, repository.exportSharedCoursesXml(), "application/xml; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleListStudents(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        try {
            sendText(exchange, 200, repository.listStudentsAsXml(), "application/xml; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleEnroll(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        Map<String, String> form = parseForm(readBody(exchange.getRequestBody()));
        String sid = form.getOrDefault("sid", "");
        String cid = form.getOrDefault("cid", "");
        try {
            repository.enrollCourse(sid, cid);
            sendText(exchange, 200, "{\"status\":\"success\",\"message\":\"选课成功\"}", "application/json; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleEnrollFromXml(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        String xml = readBody(exchange.getRequestBody());
        try {
            repository.importEnrollmentsFromXml(xml);
            sendText(exchange, 200, "{\"status\":\"success\",\"message\":\"XML导入成功\"}", "application/json; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleBatchEnrollFromXml(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        String xml = readBody(exchange.getRequestBody());
        try {
            repository.importBatchEnrollments(xml);
            sendText(exchange, 200, "{\"status\":\"success\",\"message\":\"批量XML导入成功\"}", "application/json; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleDrop(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        Map<String, String> form = parseForm(readBody(exchange.getRequestBody()));
        String sid = form.getOrDefault("sid", "");
        String cid = form.getOrDefault("cid", "");
        try {
            repository.dropCourse(sid, cid);
            sendText(exchange, 200, "{\"status\":\"success\",\"message\":\"退课成功\"}", "application/json; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleDropFromXml(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        String xml = readBody(exchange.getRequestBody());
        try {
            repository.importDropFromXml(xml);
            sendText(exchange, 200, "{\"status\":\"success\",\"message\":\"XML退课成功\"}", "application/json; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleTranscript(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        String query = exchange.getRequestURI().getQuery();
        Map<String, String> params = parseForm(query == null ? "" : query);
        String sid = params.getOrDefault("sid", "");
        try {
            sendText(exchange, 200, repository.getTranscriptAsXml(sid), "application/xml; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleTranscriptXml(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        String query = exchange.getRequestURI().getQuery();
        Map<String, String> params = parseForm(query == null ? "" : query);
        String sid = params.getOrDefault("sid", "");
        try {
            sendText(exchange, 200, repository.getTranscriptAsXml(sid), "application/xml; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleStudentsXml(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        try {
            sendText(exchange, 200, repository.getStudentsStandardXml(), "application/xml; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleCoursesXml(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        try {
            sendText(exchange, 200, repository.getCoursesStandardXml(), "application/xml; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleSelectionsXml(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        try {
            sendText(exchange, 200, repository.getSelectionsXml(), "application/xml; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleImportStudent(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        String body = readBody(exchange.getRequestBody());
        String contentType = exchange.getRequestHeaders().getFirst("Content-Type");
        if (contentType == null) {
            contentType = "";
        }

        Map<String, String> data;
        try {
            if (contentType.contains("xml") || body.trim().startsWith("<")) {
                data = parseStudentXml(body);
            } else if (contentType.contains("json") || body.trim().startsWith("{")) {
                data = parseJson(body);
            } else {
                data = parseForm(body);
            }
        } catch (Exception e) {
            sendText(exchange, 400, jsonError("请求体解析失败: " + e.getMessage()), "application/json; charset=UTF-8");
            return;
        }

        String sno = firstNonEmpty(data, "sno", "id", "sid");
        String snm = firstNonEmpty(data, "snm", "name", "sname");
        String sex = data.getOrDefault("sex", "");
        String sde = firstNonEmpty(data, "sde", "major");
        String pwd = firstNonEmpty(data, "pwd", "password");
        if (pwd.isEmpty()) {
            pwd = sno;
        }

        if (sno.isEmpty() || snm.isEmpty()) {
            sendText(exchange, 400, "{\"status\":\"fail\",\"message\":\"缺少必要参数: sno, snm\"}", "application/json; charset=UTF-8");
            return;
        }

        try {
            repository.importStudent(sno, snm, sex, sde, pwd);
            sendText(exchange, 200, "{\"status\":\"success\"}", "application/json; charset=UTF-8");
        } catch (SQLException e) {
            String msg = e.getMessage();
            if (msg != null && (msg.contains("ORA-00001") || msg.contains("unique constraint"))) {
                sendText(exchange, 200, "{\"status\":\"success\"}", "application/json; charset=UTF-8");
            } else {
                sendText(exchange, 500, jsonError(msg), "application/json; charset=UTF-8");
            }
        } catch (Exception e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleImportEnrollment(HttpExchange exchange) throws IOException {
        if (!"POST".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        String body = readBody(exchange.getRequestBody());
        String contentType = exchange.getRequestHeaders().getFirst("Content-Type");
        if (contentType == null) {
            contentType = "";
        }

        Map<String, String> data;
        try {
            if (contentType.contains("xml") || body.trim().startsWith("<")) {
                data = parseEnrollmentXml(body);
            } else if (contentType.contains("json") || body.trim().startsWith("{")) {
                data = parseJson(body);
            } else {
                data = parseForm(body);
            }
        } catch (Exception e) {
            sendText(exchange, 400, jsonError("请求体解析失败: " + e.getMessage()), "application/json; charset=UTF-8");
            return;
        }

        String sno = firstNonEmpty(data, "sno", "sid");
        String cno = firstNonEmpty(data, "cno", "cid");
        if (sno.isEmpty() || cno.isEmpty()) {
            sendText(exchange, 400, "{\"status\":\"fail\",\"message\":\"缺少必要参数: sno, cno\"}", "application/json; charset=UTF-8");
            return;
        }

        try {
            repository.importEnrollmentSkipExisting(sno, cno);
            sendText(exchange, 200, "{\"status\":\"success\"}", "application/json; charset=UTF-8");
        } catch (SQLException e) {
            String msg = e.getMessage();
            if (msg != null && (msg.contains("ORA-00001") || msg.contains("unique constraint"))) {
                sendText(exchange, 200, "{\"status\":\"success\"}", "application/json; charset=UTF-8");
            } else {
                sendText(exchange, 500, jsonError(msg), "application/json; charset=UTF-8");
            }
        } catch (Exception e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private void handleStatistics(HttpExchange exchange) throws IOException {
        if (!"GET".equalsIgnoreCase(exchange.getRequestMethod())) {
            sendText(exchange, 405, "Method Not Allowed", "text/plain; charset=UTF-8");
            return;
        }
        try {
            sendText(exchange, 200, repository.getStatistics(), "application/json; charset=UTF-8");
        } catch (SQLException e) {
            sendText(exchange, 500, jsonError(e.getMessage()), "application/json; charset=UTF-8");
        }
    }

    private static String readBody(InputStream inputStream) throws IOException {
        try (BufferedReader reader = new BufferedReader(new InputStreamReader(inputStream, StandardCharsets.UTF_8))) {
            StringBuilder sb = new StringBuilder();
            String line;
            while ((line = reader.readLine()) != null) {
                sb.append(line);
            }
            return sb.toString();
        }
    }

    private static Map<String, String> parseForm(String body) {
        Map<String, String> map = new HashMap<>();
        if (body == null || body.isEmpty()) {
            return map;
        }
        String[] pairs = body.split("&");
        for (String pair : pairs) {
            String[] kv = pair.split("=", 2);
            if (kv.length == 2) {
                map.put(urlDecode(kv[0]), urlDecode(kv[1]));
            }
        }
        return map;
    }

    private static Map<String, String> parseJson(String body) {
        Map<String, String> map = new HashMap<>();
        if (body == null || body.isEmpty()) {
            return map;
        }
        java.util.regex.Matcher m = java.util.regex.Pattern.compile("\"(\\w+)\"\\s*:\\s*\"([^\"]*)\"").matcher(body);
        while (m.find()) {
            map.put(m.group(1), m.group(2));
        }
        return map;
    }

    private static Map<String, String> parseStudentXml(String body) {
        Map<String, String> map = new HashMap<>();
        if (body == null || body.isEmpty()) {
            return map;
        }
        map.put("sno", extractXmlTag(body, "sno", "id", "sid"));
        map.put("snm", extractXmlTag(body, "snm", "name", "sname"));
        map.put("sex", extractXmlTag(body, "sex"));
        map.put("sde", extractXmlTag(body, "sde", "major"));
        map.put("pwd", extractXmlTag(body, "pwd", "password"));
        return map;
    }

    private static Map<String, String> parseEnrollmentXml(String body) {
        Map<String, String> map = new HashMap<>();
        if (body == null || body.isEmpty()) {
            return map;
        }
        map.put("sno", extractXmlTag(body, "sno", "sid"));
        map.put("cno", extractXmlTag(body, "cno", "cid"));
        return map;
    }

    private static String extractXmlTag(String xml, String... tags) {
        for (String tag : tags) {
            java.util.regex.Matcher matcher = java.util.regex.Pattern.compile(
                    "<" + tag + ">\\s*([^<]*)\\s*</" + tag + ">",
                    java.util.regex.Pattern.CASE_INSENSITIVE | java.util.regex.Pattern.DOTALL
            ).matcher(xml);
            if (matcher.find()) {
                return unescapeXml(matcher.group(1).trim());
            }
        }
        return "";
    }

    private static String firstNonEmpty(Map<String, String> map, String... keys) {
        for (String key : keys) {
            String value = map.get(key);
            if (value != null && !value.isEmpty()) {
                return value;
            }
        }
        return "";
    }

    private static String unescapeXml(String value) {
        if (value == null) {
            return "";
        }
        return value.replace("&apos;", "'")
                .replace("&quot;", "\"")
                .replace("&gt;", ">")
                .replace("&lt;", "<")
                .replace("&amp;", "&");
    }

    private static String urlDecode(String value) {
        return java.net.URLDecoder.decode(value.replace('+', ' '), StandardCharsets.UTF_8);
    }

    private static void sendText(HttpExchange exchange, int code, String body, String contentType) throws IOException {
        byte[] bytes = body.getBytes(StandardCharsets.UTF_8);
        exchange.getResponseHeaders().set("Content-Type", contentType);
        exchange.getResponseHeaders().set("Access-Control-Allow-Origin", "*");
        exchange.sendResponseHeaders(code, bytes.length);
        try (OutputStream os = exchange.getResponseBody()) {
            os.write(bytes);
        }
    }

    private static String jsonError(String message) {
        return "{\"status\":\"fail\",\"message\":\"" + escapeJson(message) + "\"}";
    }

    private static String escapeJson(String value) {
        return value == null ? "" : value.replace("\\", "\\\\").replace("\"", "\\\"").replace("\n", " ");
    }

    public static class FrontendPage {
        private static final String HTML = "<!doctype html>"
                + "<html lang='zh-CN'><head><meta charset='UTF-8'/>"
                + "<meta name='viewport' content='width=device-width, initial-scale=1'/>"
                + "<title>B系统 | Oracle 教务系统</title>"
                + "<style>"
                + ":root{--bg:#0f172a;--panel:#111827;--card:#1f2937;--line:#334155;--text:#e5e7eb;--muted:#94a3b8;--brand:#38bdf8;--brand2:#a78bfa;--good:#22c55e;--bad:#ef4444;}"
                + "*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,Arial,sans-serif;background:radial-gradient(circle at top,#1e293b 0,#0f172a 45%,#020617 100%);color:var(--text);}"
                + ".wrap{max-width:1180px;margin:0 auto;padding:32px 20px 40px;}"
                + ".hero{display:flex;justify-content:space-between;gap:20px;align-items:end;margin-bottom:24px;}"
                + ".title h1{margin:0;font-size:32px;letter-spacing:.5px}.title p{margin:8px 0 0;color:var(--muted)}"
                + ".badge{padding:10px 14px;border:1px solid rgba(56,189,248,.35);background:rgba(15,23,42,.65);border-radius:999px;color:#c7f9ff;backdrop-filter:blur(8px)}"
                + ".grid{display:grid;grid-template-columns:320px 1fr;gap:20px}.panel{background:rgba(17,24,39,.78);border:1px solid rgba(148,163,184,.18);border-radius:20px;padding:20px;box-shadow:0 20px 60px rgba(0,0,0,.35)}"
                + ".panel h2{margin:0 0 14px;font-size:18px}.form{display:grid;gap:10px}.input{width:100%;padding:12px 14px;border-radius:12px;border:1px solid var(--line);background:#0b1220;color:var(--text);outline:none}.btn{border:none;border-radius:12px;padding:12px 14px;font-weight:600;color:#fff;background:linear-gradient(135deg,var(--brand),var(--brand2));cursor:pointer}.btn.alt{background:#334155}.btn:hover{filter:brightness(1.06)}"
                + ".toolbar{display:flex;gap:10px;flex-wrap:wrap;margin-bottom:14px}.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px}.card{background:linear-gradient(180deg,rgba(31,41,55,.92),rgba(15,23,42,.92));border:1px solid rgba(148,163,184,.15);border-radius:18px;padding:16px}.card h3{margin:0 0 8px;font-size:16px}.muted{color:var(--muted)}.status{margin-top:10px;padding:10px 12px;border-radius:12px;background:rgba(15,23,42,.8);border:1px solid rgba(148,163,184,.14);min-height:42px;white-space:pre-wrap}"
                + "table{width:100%;border-collapse:collapse;margin-top:10px}th,td{padding:10px 8px;border-bottom:1px solid rgba(148,163,184,.14);text-align:left;font-size:14px}th{color:#bfdbfe;font-weight:600}.tag{display:inline-block;padding:3px 8px;border-radius:999px;font-size:12px}.tag.y{background:rgba(34,197,94,.14);color:#86efac}.tag.n{background:rgba(239,68,68,.14);color:#fca5a5}"
                + "</style></head><body><div class='wrap'>"
                + "<div class='hero'><div class='title'><h1>B系统 · Oracle教务</h1><p>最小可运行版本：登录、课程查询、共享课程、选课、退课、成绩单</p></div><div class='badge' id='serverStatus'>服务器状态：检查中</div></div>"
                + "<div class='grid'><section class='panel'><h2>登录</h2><div class='form'><input id='acc' class='input' placeholder='账户名，例如 b2023001'/><input id='pwd' class='input' type='password' placeholder='密码，例如 123456'/><button class='btn' onclick='login()'>登录验证</button></div><div class='status' id='loginResult'>等待登录...</div><hr style='border:none;border-top:1px solid rgba(148,163,184,.12);margin:18px 0'/><h2>操作</h2><div class='form'><input id='sid' class='input' placeholder='学号，例如 B2023001'/><input id='cid' class='input' placeholder='课程号，例如 C001'/><button class='btn' onclick='enroll()'>选课</button><button class='btn alt' onclick='dropCourse()'>退课</button><button class='btn alt' onclick='loadTranscript()'>查成绩单</button></div></section>"
                + "<section class='panel'><h2>课程信息</h2><div class='toolbar'><button class='btn' onclick='loadCourses()'>全部课程</button><button class='btn alt' onclick='loadSharedCourses()'>共享课程</button><button class='btn alt' onclick='loadStudents()'>学生列表</button></div><div class='status' id='coursesBox'>点击按钮加载课程列表</div><div style='margin-top:16px'><h2>成绩单</h2><div class='status' id='transcriptBox'>暂无成绩单</div></div></section></div></div>"
                + "<script>"
                + "async function api(url,opts){const r=await fetch(url,opts);return {ok:r.ok,text:await r.text()};}"
                + "function set(id,t){document.getElementById(id).innerHTML=t;}"
                + "async function login(){const form=new URLSearchParams({acc:acc.value,pwd:pwd.value});const r=await api('/b/login',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:form});set('loginResult',r.text);}" 
                + "async function enroll(){const form=new URLSearchParams({sid:sid.value,cid:cid.value});const r=await api('/b/enroll',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:form});set('loginResult',r.text);}" 
                + "async function dropCourse(){const form=new URLSearchParams({sid:sid.value,cid:cid.value});const r=await api('/b/drop',{method:'POST',headers:{'Content-Type':'application/x-www-form-urlencoded'},body:form});set('loginResult',r.text);}" 
                + "async function loadCourses(){const r=await api('/b/courses');set('coursesBox',xmlToHtml(r.text));}" 
                + "async function loadSharedCourses(){const r=await api('/b/shared-courses');set('coursesBox',xmlToHtml(r.text));}" 
                + "async function loadStudents(){const r=await api('/b/students');set('coursesBox',xmlToHtml(r.text));}" 
                + "async function loadTranscript(){const r=await api('/b/transcript?sid='+encodeURIComponent(sid.value));set('transcriptBox',xmlToHtml(r.text));}" 
                + "function xmlToHtml(xml){try{const d=new DOMParser().parseFromString(xml,'application/xml');if(d.querySelector('parsererror')) return '<pre>'+escapeHtml(xml)+'</pre>';let out='<table><thead><tr><th>编号</th><th>名称</th><th>学分</th><th>教师</th><th>地点</th><th>共享</th><th>容量</th><th>状态</th></tr></thead><tbody>';d.querySelectorAll('class').forEach(n=>{out+='<tr><td>'+text(n,'id')+'</td><td>'+text(n,'name')+'</td><td>'+text(n,'score')+'</td><td>'+text(n,'teacher')+'</td><td>'+text(n,'location')+'</td><td><span class=\'tag '+(text(n,'shareFlag')==='Y'?'y':'n')+'\'>'+text(n,'shareFlag')+'</span></td><td>'+text(n,'capacity')+'</td><td>'+text(n,'status')+'</td></tr>';});d.querySelectorAll('Course').forEach(n=>{out+='<tr><td>'+text(n,'cid')+'</td><td>'+text(n,'cname')+'</td><td>'+text(n,'credit')+'</td><td>-</td><td>-</td><td colspan=2>-</td><td>'+text(n,'status')+'</td></tr>';});out+='</tbody></table>';return out;}catch(e){return '<pre>'+escapeHtml(xml)+'</pre>';}}"
                + "function text(p,s){const e=p.querySelector(s);return e?e.textContent:'';}function escapeHtml(s){return s.replace(/[&<>'\"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','\'':'&#39;','\"':'&quot;'}[m]));}"
                + "fetch('/b/api/status').then(r=>r.json()).then(j=>serverStatus.textContent='服务器状态：'+j.system+' / '+j.status).catch(()=>serverStatus.textContent='服务器状态：不可用');"
                + "</script></body></html>";
    }

    public static class OracleBRepository {
        private final String url;
        private final String user;
        private final String password;

        public OracleBRepository(String url, String user, String password) {
            this.url = url;
            this.user = user;
            this.password = password;
        }

        private Connection getConnection() throws SQLException {
            return DriverManager.getConnection(url, user, password);
        }

        public boolean login(String acc, String pwd) throws SQLException {
            String sql = "SELECT COUNT(*) FROM B_ACCOUNT WHERE ACC_NAME = ? AND ACC_PWD = ?";
            try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql)) {
                ps.setString(1, acc);
                ps.setString(2, pwd);
                try (ResultSet rs = ps.executeQuery()) {
                    return rs.next() && rs.getInt(1) > 0;
                }
            }
        }

        public void enrollCourse(String sid, String cid) throws SQLException {
            try (Connection conn = getConnection(); Statement stmt = conn.createStatement()) {
                conn.setAutoCommit(false);
                try {
                    try (PreparedStatement ps = conn.prepareStatement("BEGIN P_B_ENROLL_COURSE(?, ?); END;")) {
                        ps.setString(1, sid);
                        ps.setString(2, cid);
                        ps.execute();
                    }
                    conn.commit();
                } catch (SQLException e) {
                    conn.rollback();
                    throw e;
                } finally {
                    conn.setAutoCommit(true);
                }
            }
        }

        public void dropCourse(String sid, String cid) throws SQLException {
            try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement("BEGIN P_B_DROP_COURSE(?, ?); END;")) {
                ps.setString(1, sid);
                ps.setString(2, cid);
                ps.execute();
            }
        }

        public String listCoursesAsXml(boolean sharedOnly) throws SQLException {
            String sql = sharedOnly
                    ? "SELECT CID, CNAME, HOURS, CREDIT, TEACHER, LOCATION, SHARE_FLAG, CAPACITY, STATUS FROM B_COURSE WHERE SHARE_FLAG = 'Y' ORDER BY CID"
                    : "SELECT CID, CNAME, HOURS, CREDIT, TEACHER, LOCATION, SHARE_FLAG, CAPACITY, STATUS FROM B_COURSE ORDER BY CID";
            try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql); ResultSet rs = ps.executeQuery()) {
                StringBuilder xml = new StringBuilder();
                xml.append("<Classes>");
                while (rs.next()) {
                    xml.append("<class>")
                       .append(tag("id", rs.getString("CID")))
                       .append(tag("name", rs.getString("CNAME")))
                       .append(tag("time", String.valueOf(rs.getInt("HOURS"))))
                       .append(tag("score", String.valueOf(rs.getDouble("CREDIT"))))
                       .append(tag("teacher", rs.getString("TEACHER")))
                       .append(tag("location", rs.getString("LOCATION")))
                       .append(tag("shareFlag", rs.getString("SHARE_FLAG")))
                       .append(tag("capacity", String.valueOf(rs.getInt("CAPACITY"))))
                       .append(tag("status", rs.getString("STATUS")))
                       .append("</class>");
                }
                xml.append("</Classes>");
                return xml.toString();
            }
        }

        public String exportSharedCoursesXml() throws SQLException {
            String sql = "SELECT CID, CNAME, HOURS, CREDIT, TEACHER, LOCATION, SHARE_FLAG, CAPACITY, STATUS FROM B_COURSE WHERE SHARE_FLAG = 'Y' ORDER BY CID";
            try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql); ResultSet rs = ps.executeQuery()) {
                StringBuilder xml = new StringBuilder();
                xml.append("<SharedCourses college=\"B\">");
                while (rs.next()) {
                    xml.append("<Course>")
                       .append(tag("cid", rs.getString("CID")))
                       .append(tag("cname", rs.getString("CNAME")))
                       .append(tag("hours", rs.getString("HOURS")))
                       .append(tag("credit", rs.getString("CREDIT")))
                       .append(tag("teacher", rs.getString("TEACHER")))
                       .append(tag("location", rs.getString("LOCATION")))
                       .append(tag("shareFlag", rs.getString("SHARE_FLAG")))
                       .append(tag("capacity", rs.getString("CAPACITY")))
                       .append(tag("status", rs.getString("STATUS")))
                       .append("</Course>");
                }
                xml.append("</SharedCourses>");
                return xml.toString();
            }
        }

        public void importEnrollmentsFromXml(String xml) throws SQLException {
            java.util.regex.Matcher matcher = java.util.regex.Pattern.compile("<enrollment>\\s*<sid>(.*?)</sid>\\s*<cid>(.*?)</cid>\\s*</enrollment>", java.util.regex.Pattern.DOTALL).matcher(xml);
            while (matcher.find()) {
                String sid = unescapeXml(matcher.group(1).trim());
                String cid = unescapeXml(matcher.group(2).trim());
                enrollCourse(sid, cid);
            }
        }

        public void importBatchEnrollments(String xml) throws SQLException {
            java.util.regex.Matcher matcher = java.util.regex.Pattern.compile("<batch>.*?<enrollment>\\s*<sid>(.*?)</sid>\\s*<cid>(.*?)</cid>\\s*</enrollment>.*?</batch>", java.util.regex.Pattern.DOTALL).matcher(xml);
            if (matcher.find()) {
                // 兼容包装型 batch，回退到通用解析
                importEnrollmentsFromXml(xml);
                return;
            }
            importEnrollmentsFromXml(xml);
        }

        public void importDropFromXml(String xml) throws SQLException {
            java.util.regex.Matcher matcher = java.util.regex.Pattern.compile("<drop>\\s*<sid>(.*?)</sid>\\s*<cid>(.*?)</cid>\\s*</drop>", java.util.regex.Pattern.DOTALL).matcher(xml);
            while (matcher.find()) {
                String sid = unescapeXml(matcher.group(1).trim());
                String cid = unescapeXml(matcher.group(2).trim());
                dropCourse(sid, cid);
            }
        }

        public String listStudentsAsXml() throws SQLException {
            String sql = "SELECT SID, SNAME, SEX, MAJOR, GRADE, PHONE, STATUS FROM B_STUDENT ORDER BY SID";
            try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql); ResultSet rs = ps.executeQuery()) {
                StringBuilder xml = new StringBuilder();
                xml.append("<Students>");
                while (rs.next()) {
                    xml.append("<student>")
                       .append(tag("id", rs.getString("SID")))
                       .append(tag("name", rs.getString("SNAME")))
                       .append(tag("sex", rs.getString("SEX")))
                       .append(tag("major", rs.getString("MAJOR")))
                       .append(tag("grade", String.valueOf(rs.getInt("GRADE"))))
                       .append(tag("phone", rs.getString("PHONE")))
                       .append(tag("status", rs.getString("STATUS")))
                       .append("</student>");
                }
                xml.append("</Students>");
                return xml.toString();
            }
        }

        public String getTranscriptAsXml(String sid) throws SQLException {
            String sql = "SELECT s.SID, s.SNAME, s.MAJOR, c.CID, c.CNAME, c.CREDIT, e.SCORE, e.CHOICE_STA " +
                         "FROM B_STUDENT s LEFT JOIN B_ENROLLMENT e ON s.SID = e.SID " +
                         "LEFT JOIN B_COURSE c ON e.CID = c.CID WHERE s.SID = ? ORDER BY c.CID";
            try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql)) {
                ps.setString(1, sid);
                try (ResultSet rs = ps.executeQuery()) {
                    StringBuilder xml = new StringBuilder();
                    xml.append("<Transcript sid=\"").append(escapeXml(sid)).append("\">");
                    while (rs.next()) {
                        xml.append("<Course>")
                           .append(tag("cid", rs.getString("CID")))
                           .append(tag("cname", rs.getString("CNAME")))
                           .append(tag("credit", rs.getString("CREDIT")))
                           .append(tag("score", rs.getString("SCORE")))
                           .append(tag("status", rs.getString("CHOICE_STA")))
                           .append("</Course>");
                    }
                    xml.append("</Transcript>");
                    return xml.toString();
                }
            }
        }

        public String getStudentsStandardXml() throws SQLException {
            String sql = "SELECT SID, SNAME, SEX, MAJOR, GRADE, PHONE, STATUS FROM B_STUDENT ORDER BY SID";
            try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql); ResultSet rs = ps.executeQuery()) {
                StringBuilder xml = new StringBuilder();
                xml.append("<Students>");
                while (rs.next()) {
                    xml.append("<student>")
                       .append(tag("id", rs.getString("SID")))
                       .append(tag("name", rs.getString("SNAME")))
                       .append(tag("sex", rs.getString("SEX")))
                       .append(tag("major", rs.getString("MAJOR")))
                       .append(tag("grade", String.valueOf(rs.getInt("GRADE"))))
                       .append(tag("phone", rs.getString("PHONE")))
                       .append(tag("status", rs.getString("STATUS")))
                       .append("</student>");
                }
                xml.append("</Students>");
                return xml.toString();
            }
        }

        public String getCoursesStandardXml() throws SQLException {
            String sql = "SELECT CID, CNAME, HOURS, CREDIT, TEACHER, LOCATION, SHARE_FLAG, CAPACITY, STATUS FROM B_COURSE ORDER BY CID";
            try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql); ResultSet rs = ps.executeQuery()) {
                StringBuilder xml = new StringBuilder();
                xml.append("<Classes>");
                while (rs.next()) {
                    xml.append("<class>")
                       .append(tag("id", rs.getString("CID")))
                       .append(tag("name", rs.getString("CNAME")))
                       .append(tag("hours", String.valueOf(rs.getInt("HOURS"))))
                       .append(tag("credit", String.valueOf(rs.getDouble("CREDIT"))))
                       .append(tag("teacher", rs.getString("TEACHER")))
                       .append(tag("location", rs.getString("LOCATION")))
                       .append(tag("shareFlag", rs.getString("SHARE_FLAG")))
                       .append(tag("capacity", String.valueOf(rs.getInt("CAPACITY"))))
                       .append(tag("status", rs.getString("STATUS")))
                       .append("</class>");
                }
                xml.append("</Classes>");
                return xml.toString();
            }
        }

        public String getSelectionsXml() throws SQLException {
            String sql = "SELECT e.SID, e.CID, c.CNAME, e.SCORE, e.CHOICE_STA, TO_CHAR(e.ENROLL_DT, 'YYYY-MM-DD') AS ENROLL_DATE FROM B_ENROLLMENT e JOIN B_COURSE c ON e.CID = c.CID ORDER BY e.SID, e.CID";
            try (Connection conn = getConnection(); PreparedStatement ps = conn.prepareStatement(sql); ResultSet rs = ps.executeQuery()) {
                StringBuilder xml = new StringBuilder();
                xml.append("<Selections>");
                while (rs.next()) {
                    xml.append("<selection>")
                       .append(tag("sid", rs.getString("SID")))
                       .append(tag("cid", rs.getString("CID")))
                       .append(tag("cname", rs.getString("CNAME")))
                       .append(tag("score", rs.getString("SCORE")))
                       .append(tag("status", rs.getString("CHOICE_STA")))
                       .append(tag("date", rs.getString("ENROLL_DATE")))
                       .append("</selection>");
                }
                xml.append("</Selections>");
                return xml.toString();
            }
        }

        public void importStudent(String sno, String snm, String sex, String sde, String pwd) throws SQLException {
            try (Connection conn = getConnection()) {
                String checkSql = "SELECT COUNT(*) FROM B_STUDENT WHERE SID = ?";
                try (PreparedStatement ps = conn.prepareStatement(checkSql)) {
                    ps.setString(1, sno);
                    try (ResultSet rs = ps.executeQuery()) {
                        if (rs.next() && rs.getInt(1) > 0) {
                            return;
                        }
                    }
                }
                String insertStudent = "INSERT INTO B_STUDENT(SID, SNAME, SEX, MAJOR, PASSWORD, GRADE, PHONE, STATUS) VALUES (?, ?, ?, ?, ?, 2024, ?, 'NORMAL')";
                try (PreparedStatement ps = conn.prepareStatement(insertStudent)) {
                    ps.setString(1, sno);
                    ps.setString(2, snm);
                    ps.setString(3, sex != null ? sex : "男");
                    ps.setString(4, sde != null ? sde : "未知专业");
                    ps.setString(5, pwd != null ? pwd : sno);
                    ps.setString(6, "-");
                    ps.executeUpdate();
                }
                String insertAccount = "INSERT INTO B_ACCOUNT(ACC_NAME, ACC_PWD, LEVEL_NO, SID) VALUES (?, ?, 1, ?)";
                try (PreparedStatement ps = conn.prepareStatement(insertAccount)) {
                    ps.setString(1, sno.toLowerCase());
                    ps.setString(2, pwd != null ? pwd : sno);
                    ps.setString(3, sno);
                    ps.executeUpdate();
                }
            }
        }

        public void importEnrollment(String sno, String cno) throws SQLException {
            enrollCourse(sno, cno);
        }

        public void importEnrollmentSkipExisting(String sno, String cno) throws SQLException {
            try (Connection conn = getConnection()) {
                String checkSql = "SELECT COUNT(*) FROM B_ENROLLMENT WHERE SID = ? AND CID = ?";
                try (PreparedStatement ps = conn.prepareStatement(checkSql)) {
                    ps.setString(1, sno);
                    ps.setString(2, cno);
                    try (ResultSet rs = ps.executeQuery()) {
                        if (rs.next() && rs.getInt(1) > 0) {
                            return;
                        }
                    }
                }
                enrollCourse(sno, cno);
            }
        }

        public String getCounts() throws SQLException {
            try (Connection conn = getConnection(); Statement stmt = conn.createStatement()) {
                int students = 0, courses = 0, selections = 0;
                try (ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM B_STUDENT")) {
                    if (rs.next()) students = rs.getInt(1);
                }
                try (ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM B_COURSE")) {
                    if (rs.next()) courses = rs.getInt(1);
                }
                try (ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM B_ENROLLMENT WHERE CHOICE_STA = 'ENROLLED'")) {
                    if (rs.next()) selections = rs.getInt(1);
                }
                return "{\"status\":\"running\",\"system\":\"B-Oracle\",\"online\":true,\"students\":" + students + ",\"courses\":" + courses + ",\"selections\":" + selections + "}";
            }
        }

        public String getStatistics() throws SQLException {
            try (Connection conn = getConnection(); Statement stmt = conn.createStatement()) {
                int students = 0, courses = 0, selections = 0, sharedCourses = 0, dropped = 0;
                try (ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM B_STUDENT")) {
                    if (rs.next()) students = rs.getInt(1);
                }
                try (ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM B_COURSE")) {
                    if (rs.next()) courses = rs.getInt(1);
                }
                try (ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM B_ENROLLMENT")) {
                    if (rs.next()) selections = rs.getInt(1);
                }
                try (ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM B_COURSE WHERE SHARE_FLAG = 'Y'")) {
                    if (rs.next()) sharedCourses = rs.getInt(1);
                }
                try (ResultSet rs = stmt.executeQuery("SELECT COUNT(*) FROM B_ENROLLMENT WHERE CHOICE_STA = 'DROPPED'")) {
                    if (rs.next()) dropped = rs.getInt(1);
                }
                return "{\"college_id\":\"B\",\"college_name\":\"学院B\",\"dbms\":\"Oracle\",\"students\":" + students + ",\"courses\":" + courses + ",\"selections\":" + selections + ",\"shared_courses\":" + sharedCourses + ",\"dropped\":" + dropped + "}";
            }
        }

        private static String tag(String name, String value) {
            return "<" + name + ">" + escapeXml(value) + "</" + name + ">";
        }

        private static String escapeXml(String value) {
            if (value == null) return "";
            return value.replace("&", "&amp;")
                        .replace("<", "&lt;")
                        .replace(">", "&gt;")
                        .replace("\"", "&quot;")
                        .replace("'", "&apos;");
        }

        private static String unescapeXml(String value) {
            if (value == null) return "";
            return value.replace("&apos;", "'")
                        .replace("&quot;", "\"")
                        .replace("&gt;", ">")
                        .replace("&lt;", "<")
                        .replace("&amp;", "&");
        }
    }
}
