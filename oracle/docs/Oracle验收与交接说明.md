# Oracle 侧验收与交接说明

本文档用于说明当前 Oracle（B 学院）部分已经完成了什么、尚未完成什么，以及后续同学应如何继续推进。

---

## 一、当前 Oracle 侧已完成内容

### 1. 数据层
- 已建立核心表：`B_STUDENT`、`B_ACCOUNT`、`B_COURSE`、`B_ENROLLMENT`
- 已建立常用索引、视图、触发器、存储过程
- 已补充批量初始化数据逻辑，目标满足 50 名学生、10 门课程、每人 5 门课

### 2. 服务层
- 已实现本地 HTTP 服务 `BLocalServer.java`
- 已支持登录、课程列表、共享课程、学生列表、选课、退课、成绩单查询
- 已增加 XML 导出/导入入口

### 3. XML 与协议层
- 已补充共享课程 XSD：`oracle/xml/shared_courses.xsd`
- 已补充选课交换 XSD：`oracle/xml/enrollment_exchange.xsd`
- 已补充集成契约：`oracle/integration/b_exchange_contract.xml`

### 4. 验证层
- 已补充 Python 验证脚本：`oracle/scripts/verify_oracle.py`
- 已补充 Oracle SQL 验收脚本：`oracle/scripts/verify_oracle.sql`
- 已补充示例 XML：`oracle/data/enrollment_exchange_sample.xml`

---

## 二、当前 Oracle 侧尚未完全完成内容

### 1. 严格的跨库联动闭环
目前 Oracle 侧已经具备 XML 交换能力，但还没有完成：
- 与 SQLServer 侧的统一集成调度
- 与 MySQL 侧的统一集成调度
- 三库之间的统一数据回流与统计汇总

### 2. 更完整的业务管理界面
当前主要完成的是：
- 登录
- 查询
- 选课
- 退课
- 成绩单

仍可继续补充：
- 学生增删改
- 课程增删改
- 更完整的账号管理
- 更严格的选课规则展示

### 3. 更严格的 XML 解析与校验
当前 XML 交换已能使用，但后续仍可进一步完善：
- 更标准的 XML 架构校验
- 更明确的批量交换协议
- 更稳健的错误处理与回滚机制

---

## 三、当前验收建议

建议按以下顺序验证 Oracle 侧：

1. 执行 `oracle/db/oracle_b_schema.sql`
2. 运行 `oracle/scripts/verify_oracle.sql`
3. 运行 `oracle/scripts/verify_oracle.py`
4. 启动 `oracle/service/BLocalServer.java`
5. 访问本地页面测试登录、选课、退课、成绩单
6. 测试 XML 导出接口：`/b/shared-courses/xml`
7. 测试 XML 导入接口：`/b/enroll/xml`、`/b/enroll/batch`、`/b/drop/xml`

---

## 四、交接说明

后续接手 Oracle 部分的同学，建议优先完成以下任务：

1. 检查初始化脚本是否在当前 Oracle 环境中可直接执行
2. 验证 50 学生 / 10 课程 / 每人 5 课的数据是否真正落库
3. 继续补齐跨库联动逻辑
4. 如有需要，补一个更完整的集成服务器层
5. 为实验报告补充流程图和截图

---

## 五、项目结构说明

Oracle 目录当前建议结构如下：

- `oracle/db/`：数据库脚本
- `oracle/service/`：本地服务
- `oracle/xml/`：XSD 定义
- `oracle/integration/`：集成契约
- `oracle/data/`：示例 XML
- `oracle/scripts/`：验证脚本
- `oracle/docs/`：说明文档

---

## 六、结论

当前 Oracle 侧已经具备“可运行、可验证、可继续扩展”的基础，但还未完全达到跨库集成的最终状态。后续工作应围绕“联动闭环”和“实验验收”继续推进。
