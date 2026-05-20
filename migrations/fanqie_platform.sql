-- 番茄小说平台支持 - 数据库迁移脚本
-- 适用于SQLite和MySQL

-- 1. 添加FANQIE到platform枚举（仅MySQL需要，SQLite自动支持）
-- MySQL: ALTER TYPE platformenum ADD VALUE IF NOT EXISTS 'fanqie';

-- 2. 为accounts表添加番茄小说特有字段
ALTER TABLE accounts ADD COLUMN novel_id VARCHAR(100);
ALTER TABLE accounts ADD COLUMN novel_title VARCHAR(500);
ALTER TABLE accounts ADD COLUMN novel_status VARCHAR(20);
ALTER TABLE accounts ADD COLUMN writer_cookies TEXT;
ALTER TABLE accounts ADD COLUMN writer_token VARCHAR(500);
ALTER TABLE accounts ADD COLUMN total_chapters INTEGER DEFAULT 0;
ALTER TABLE accounts ADD COLUMN total_words INTEGER DEFAULT 0;
ALTER TABLE accounts ADD COLUMN total_readers INTEGER DEFAULT 0;
ALTER TABLE accounts ADD COLUMN avg_completion_rate FLOAT DEFAULT 0.0;
ALTER TABLE accounts ADD COLUMN daily_income FLOAT DEFAULT 0.0;
ALTER TABLE accounts ADD COLUMN monthly_income FLOAT DEFAULT 0.0;
ALTER TABLE accounts ADD COLUMN total_income FLOAT DEFAULT 0.0;
ALTER TABLE accounts ADD COLUMN consecutive_days INTEGER DEFAULT 0;
ALTER TABLE accounts ADD COLUMN last_update_date DATETIME;
ALTER TABLE accounts ADD COLUMN qualification_for_bonus BOOLEAN DEFAULT FALSE;

-- 3. 创建novels表
CREATE TABLE novels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    account_id INTEGER,
    title VARCHAR(500) NOT NULL,
    subtitle VARCHAR(500),
    category VARCHAR(50),
    tags JSON,
    cover_image_path VARCHAR(500),
    introduction TEXT,
    golden_three_chapters TEXT,
    status VARCHAR(20) DEFAULT 'draft',
    publish_schedule JSON,
    total_chapters INTEGER DEFAULT 0,
    total_words INTEGER DEFAULT 0,
    total_reads INTEGER DEFAULT 0,
    total_favorites INTEGER DEFAULT 0,
    avg_rating FLOAT DEFAULT 0.0,
    evolution_config JSON,
    last_evolution_time DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (account_id) REFERENCES accounts(id)
);

CREATE INDEX idx_novels_account_id ON novels(account_id);

-- 4. 创建chapters表
CREATE TABLE chapters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id INTEGER,
    chapter_number INTEGER NOT NULL,
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    word_count INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'draft',
    scheduled_time DATETIME,
    published_time DATETIME,
    platform_chapter_id VARCHAR(100),
    read_count INTEGER DEFAULT 0,
    completion_rate FLOAT DEFAULT 0.0,
    retention_rate FLOAT DEFAULT 0.0,
    ai_generated_ratio FLOAT DEFAULT 0.0,
    manual_revision_notes TEXT,
    error_message TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (novel_id) REFERENCES novels(id)
);

CREATE INDEX idx_chapters_novel_id ON chapters(novel_id);

-- 5. 创建fanqie_analytics表
CREATE TABLE fanqie_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    novel_id INTEGER,
    chapter_id INTEGER,
    stat_date DATETIME NOT NULL,
    daily_reads INTEGER DEFAULT 0,
    new_followers INTEGER DEFAULT 0,
    new_favorites INTEGER DEFAULT 0,
    comments_count INTEGER DEFAULT 0,
    daily_ad_revenue FLOAT DEFAULT 0.0,
    reading_minutes INTEGER DEFAULT 0,
    avg_reading_time FLOAT DEFAULT 0.0,
    completion_rate FLOAT DEFAULT 0.0,
    retention_rate_day1 FLOAT DEFAULT 0.0,
    retention_rate_day7 FLOAT DEFAULT 0.0,
    category_rank INTEGER,
    overall_rank INTEGER,
    rising_rank INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (novel_id) REFERENCES novels(id),
    FOREIGN KEY (chapter_id) REFERENCES chapters(id)
);

CREATE INDEX idx_fanqie_analytics_novel_id ON fanqie_analytics(novel_id);
CREATE INDEX idx_fanqie_analytics_chapter_id ON fanqie_analytics(chapter_id);
CREATE INDEX idx_fanqie_analytics_stat_date ON fanqie_analytics(stat_date);

-- 完成
-- 注意：如果使用MySQL，需要将AUTOINCREMENT改为AUTO_INCREMENT，BOOLEAN改为TINYINT(1)
