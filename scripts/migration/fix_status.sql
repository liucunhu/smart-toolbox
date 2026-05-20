-- 修复status字段的大小写问题
UPDATE accounts SET status = 'registering' WHERE status = 'REGISTERING';
UPDATE accounts SET status = 'nurturing' WHERE status = 'NURTURING';
UPDATE accounts SET status = 'active' WHERE status = 'ACTIVE';
UPDATE accounts SET status = 'banned' WHERE status = 'BANNED';

-- 验证修复结果
SELECT id, platform, status FROM accounts;
