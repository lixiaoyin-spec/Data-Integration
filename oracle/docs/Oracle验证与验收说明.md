# Oracle 验证与验收说明

## 1. 初始化数据库

执行 `db/oracle_b_schema.sql`。

## 2. 启动本地服务

编译并运行 `service/BLocalServer.java`。

## 3. 运行验证脚本

安装 `python-oracledb` 后执行：

```bash
python scripts/verify_oracle.py --user BUSER --password BPASS --dsn localhost:1521/orcl
```

## 4. 验收标准

- 学生数量不少于 50
- 课程数量不少于 10
- 每个学生至少 5 条选课记录
- 共享课程不为空
- 选课记录无孤立引用
- 退课功能可将状态改为 `DROPPED`

## 5. XML 交换样例

- `data/shared_course_exchange_sample.xml`
- `data/enrollment_exchange_sample.xml`
