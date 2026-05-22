-- Oracle B 系统验收脚本
-- 用途：在 Oracle 客户端中直接执行，检查数据规模、共享课程、选课与退课状态。

SET SERVEROUTPUT ON;

PROMPT ==============================================
PROMPT 1) 基础数据规模
PROMPT ==============================================
SELECT 'B_STUDENT' AS TABLE_NAME, COUNT(*) AS CNT FROM B_STUDENT
UNION ALL
SELECT 'B_COURSE', COUNT(*) FROM B_COURSE
UNION ALL
SELECT 'B_ACCOUNT', COUNT(*) FROM B_ACCOUNT
UNION ALL
SELECT 'B_ENROLLMENT', COUNT(*) FROM B_ENROLLMENT;

PROMPT ==============================================
PROMPT 2) 共享课程检查
PROMPT ==============================================
SELECT COUNT(*) AS SHARED_COURSE_COUNT FROM B_COURSE WHERE SHARE_FLAG = 'Y';
SELECT * FROM V_B_SHARED_COURSE ORDER BY CID;

PROMPT ==============================================
PROMPT 3) 选课完整性检查
PROMPT ==============================================
SELECT COUNT(*) AS ORPHAN_ENROLLMENTS
FROM B_ENROLLMENT e
WHERE NOT EXISTS (SELECT 1 FROM B_STUDENT s WHERE s.SID = e.SID)
   OR NOT EXISTS (SELECT 1 FROM B_COURSE c WHERE c.CID = e.CID);

PROMPT ==============================================
PROMPT 4) 每个学生至少 5 门课的抽查
PROMPT ==============================================
SELECT SID, COUNT(*) AS ENROLL_CNT
FROM B_ENROLLMENT
GROUP BY SID
ORDER BY COUNT(*) DESC, SID;

PROMPT ==============================================
PROMPT 5) 成绩单与课程统计视图
PROMPT ==============================================
SELECT * FROM V_B_STUDENT_SCORE WHERE ROWNUM <= 20;
SELECT * FROM V_B_COURSE_ENROLL_COUNT ORDER BY ENROLL_COUNT DESC, CID;

PROMPT ==============================================
PROMPT 6) 退课状态检查
PROMPT ==============================================
SELECT COUNT(*) AS DROPPED_COUNT FROM B_ENROLLMENT WHERE CHOICE_STA = 'DROPPED';

PROMPT ==============================================
PROMPT 验收脚本执行完毕
PROMPT ==============================================
