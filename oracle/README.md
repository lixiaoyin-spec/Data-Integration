# Oracle 侧项目结构

本目录是实验三中 B 学院（Oracle）部分的实现，按分层方式组织：

## 目录说明

- `db/`：数据库建表、约束、存储过程、初始化数据
- `service/`：Oracle 本地服务（HTTP 接口、XML 输出/输入）
- `xml/`：XML 协议定义（XSD）
- `integration/`：跨库集成约定与交换协议
- `data/`：示例交换 XML 数据
- `scripts/`：验证脚本
- `docs/`：启动说明、测试流程与验收说明

## 当前能力

- 登录验证
- 课程查询、共享课程查询
- 学生列表查询
- 选课、退课、成绩单查询
- 共享课程 XML 导出
- XML 选课导入
- 批量初始化数据与验证脚本

## 验证建议

1. 执行 `db/oracle_b_schema.sql` 初始化数据库
2. 启动 `service/BLocalServer.java`
3. 使用 `scripts/verify_oracle.py` 检查数据与业务状态
4. 访问 `http://localhost:8082/b/shared-courses/xml` 验证 XML 导出
5. POST `data/enrollment_exchange_sample.xml` 到 `/b/enroll/xml` 验证 XML 导入
