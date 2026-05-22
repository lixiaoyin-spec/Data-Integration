# 教务管理系统客户端 README

## 一、项目概述

本项目为《基于 XML 的异构数据集成教务系统》中的 C 学院客户端部分。

当前项目负责：

- Java Swing 图形化客户端
- 学生端 GUI
- 管理员端 GUI
- Socket 通信接口封装
- JTable 数据展示
- 与服务端进行协议通信

当前阶段已经完成：

- 登录界面
- 学生主界面
- 管理员主界面
- JTable 数据展示
- 假数据(Mock Data)测试
- 协议字符串发送结构
- Socket 通信框架

目前系统中的部分数据为本地假数据，用于前端界面开发与功能验证。
后续与服务端联调时，将切换为真实 Socket 通信。

---

# 二、项目结构

```text
edu-management-client/
├── compile.bat
├── run.bat
└── src/
    └── com/edu/client/
        ├── SocketClient.java
        ├── ServerResponseTableHelper.java
        ├── LoginFrame.java
        ├── StudentFrame.java
        └── AdminFrame.java
```

---

# 三、各模块说明

## 1. LoginFrame.java

登录界面。

功能：

- 输入用户名
- 输入密码
- 学生登录
- 管理员登录
- 登录成功后跳转不同界面

当前阶段：

使用本地假账号测试。

测试账号：

学生：

```text
用户名：1001
密码：123456
```

管理员：

```text
用户名：admin
密码：admin
```

后续联调时：

将恢复 Socket 通信版本：

```java
SocketClient client = new SocketClient();
client.connect();
client.sendMessage(...);
```

由服务端负责登录验证。

---

## 2. StudentFrame.java

学生主界面。

功能：

- 查看课程
- 查看已选课程
- 选课
- 退课
- 退出登录

界面结构：

- 左侧：功能菜单
- 右侧：JTable 数据展示

当前阶段：

使用假数据模拟：

- 所有课程
- 已选课程
- 选课成功
- 退课成功

后续联调时：

需要切换为真实 Socket 通信。

核心通信方法：

```java
private void sendAndShowTable(String command)
```

当前版本：

本地 mock 数据。

后续版本：

恢复为：

```java
client.sendMessage(command);
String resp = client.receiveMessage();
```

由服务端返回真实数据。

---

## 3. AdminFrame.java

管理员主界面。

功能：

- 查看所有学生
- 查看所有课程
- 查看选课统计
- 退出登录

当前阶段：

使用本地假数据。

后续联调：

恢复 Socket 通信。

---

## 4. SocketClient.java

Socket 通信封装类。

负责：

- connect()
- sendMessage()
- receiveMessage()
- disconnect()

默认：

```text
localhost:9999
```

后续服务端启动后：

客户端通过此类与服务端通信。

---

## 5. ServerResponseTableHelper.java

服务器响应解析工具类。

功能：

将服务端返回的字符串转换为 JTable 可显示的 DefaultTableModel。

当前约定格式：

```text
课程号|课程名|学分
C001|数据库|3
C002|操作系统|4
```

说明：

- 每行代表一条记录
- 使用 \n 分隔行
- 使用 | 分隔列

---

# 四、当前开发阶段

目前属于：

```text
客户端 GUI 与 Mock 数据验证阶段
```

已经验证：

- Swing GUI 正常
- JTable 正常
- 界面跳转正常
- 按钮事件正常
- 表格刷新正常
- Socket 结构正常

当前未接入真实数据库。

---

# 五、后续联调说明（给服务端同学）

## 1. 当前客户端协议

### 登录

客户端发送：

```text
LOGIN|用户名|密码|角色
```

例如：

```text
LOGIN|1001|123456|student
```

服务端返回：

```text
SUCCESS
```

或者：

```text
FAIL
```

---

## 2. 查看所有课程

客户端发送：

```text
GET_ALL_COURSES
```

服务端返回格式：

```text
课程号|课程名|学分
C001|数据库|3
C002|操作系统|4
```

---

## 3. 查看已选课程

客户端发送：

```text
GET_MY_COURSES|学号
```

例如：

```text
GET_MY_COURSES|1001
```

---

## 4. 选课

客户端发送：

```text
SELECT_COURSE|学号|课程号
```

例如：

```text
SELECT_COURSE|1001|C002
```

服务端建议返回：

```text
SUCCESS
```

或者：

```text
ALREADY_SELECTED
```

---

## 5. 退课

客户端发送：

```text
DROP_COURSE|学号|课程号
```

例如：

```text
DROP_COURSE|1001|C002
```

---

## 6. 查看所有学生

客户端发送：

```text
GET_ALL_STUDENTS
```

返回格式：

```text
学号|姓名|专业
1001|张三|软件工程
1002|李四|计算机科学
```

---

## 7. 查看选课统计

客户端发送：

```text
GET_STATISTICS
```

返回格式：

```text
课程名|选课人数
数据库|35
操作系统|42
```

---

# 六、重要联调注意事项

## 1. 服务端必须使用 UTF-8

避免中文乱码。

---

## 2. 服务端必须换行输出

客户端 receiveMessage() 使用按行读取。

服务端必须：

```java
writer.println(resp);
```

否则客户端会阻塞。

---

## 3. 服务端返回格式必须统一

当前客户端 JTable 默认：

- 使用 \n 分割行
- 使用 | 分割列

服务端必须保持一致。

---

## 4. 当前客户端 studentId

约定：

```text
登录用户名 = 学号
```

例如：

```text
1001
```

避免额外用户映射。

---

# 七、后续待完成内容

当前客户端已基本完成。

后续需要：

- 与真实服务端联调
- 恢复 Socket 通信
- 替换假数据
- 增加真实数据库结果展示
- 增加 XML 集成结果展示（可选）

---

# 八、当前运行方式

## 编译（在文件夹页面直接点击对应的文件）

```text
compile.bat
```

## 运行（在文件夹页面直接点击对应的文件）

```text
run.bat
```

或者：

```bash
java com.edu.client.LoginFrame
```

---

# 九、当前完成情况总结

当前客户端已经完成：

- GUI 框架
- 登录逻辑
- 学生端
- 管理员端
- JTable 数据展示
- Mock 数据测试
- Socket 通信框架
- 协议定义

目前已经具备联调条件。
