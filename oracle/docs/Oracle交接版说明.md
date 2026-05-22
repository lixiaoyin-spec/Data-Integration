# Oracle 交接版说明

这份说明适合直接发给后续接手 Oracle 部分的同学。

---

## 1. 当前已经完成的内容

### 数据层
- 已建立核心表：`B_STUDENT`、`B_ACCOUNT`、`B_COURSE`、`B_ENROLLMENT`
- 已建立索引、视图、触发器、存储过程
- 已补充批量初始化数据，目标是 50 名学生、10 门课程、每人 5 门课

### 本地服务层
- 已有 `oracle/service/BLocalServer.java`
- 支持登录、课程查询、共享课程查询、学生查询、选课、退课、成绩单查询
- 已有 XML 导出/导入接口

### XML / 协议层
- `oracle/xml/shared_courses.xsd`
- `oracle/xml/enrollment_exchange.xsd`
- `oracle/integration/b_exchange_contract.xml`

### 验证层
- `oracle/scripts/verify_oracle.sql`
- `oracle/scripts/verify_oracle.py`
- `oracle/data/enrollment_exchange_sample.xml`

### 文档层
- `oracle/docs/B系统最小运行版启动说明与测试流程.md`
- `oracle/docs/Oracle验收与交接说明.md`

---

## 2. 当前还没有完全完成的内容

### 跨库联动闭环
Oracle 现在已经能导出/导入 XML，但还没有和 SQLServer、MySQL 形成完整联动闭环。

### 更完整的业务功能
目前已完成登录、查询、选课、退课、成绩单，但还可以继续补：
- 学生增删改
- 课程增删改
- 更完整的账号管理
- 更严格的选课规则

### 更严格的 XML 校验
- 目前 XML 能用，但还可以继续增强校验和错误处理
- 可以进一步统一批量导入/导出格式

---

## 3. 建议你接手后优先做什么

### 第一优先级
1. 执行 `oracle/db/oracle_b_schema.sql`
2. 检查 50 学生 / 10 课程 / 每人 5 课是否真正落库
3. 运行 `oracle/scripts/verify_oracle.sql`
4. 运行 `oracle/scripts/verify_oracle.py`

### 第二优先级
5. 确认 `BLocalServer.java` 能正常启动
6. 测试页面、登录、选课、退课、成绩单
7. 测试 XML 导出和导入接口

### 第三优先级
8. 继续补跨库联动逻辑
9. 如有需要，补集成服务器层
10. 为实验报告补流程图和截图

---

## 4. 目录说明

- `oracle/db/`：数据库脚本
- `oracle/service/`：本地服务代码
- `oracle/xml/`：XML 结构定义
- `oracle/integration/`：集成协议
- `oracle/data/`：示例 XML 数据
- `oracle/scripts/`：验证脚本
- `oracle/docs/`：说明文档

---

## 5. 简短结论

Oracle 部分已经有一个可运行的基础版本，但还没有做到实验要求中的完整跨库集成。后续建议先确认数据是否真正补齐，再继续完善联动逻辑。
