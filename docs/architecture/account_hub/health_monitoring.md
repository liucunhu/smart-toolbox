# 账号健康监控 (Account Health Monitoring)

## 1. 功能描述
实时监控矩阵内所有账号的运行状态，通过数据分析识别限流、违规风险，并提供自动熔断保护。

## 2. 技术实现方案

### 2.1 数据采集与清洗
*   **多源数据同步**: 
    *   通过 RPA 定时抓取各平台创作者后台的核心指标（播放量、点赞、评论、转发）。
    *   对接部分平台的开放 API（如 B站、视频号助手）获取结构化数据。
*   **异常值过滤**: 剔除因平台统计延迟或系统波动产生的脏数据。

### 2.2 健康度评分模型
*   **评分维度**:
    *   **流量稳定性** (40%): 近 7 天播放量方差。
    *   **互动转化率** (30%): (点赞+评论)/播放量。
    *   **合规记录** (30%): 是否存在站内信警告或作品被下架。
*   **等级划分**: 
    *   **健康 (80-100)**: 正常分发。
    *   **观察 (60-79)**: 降低发布频率，增加养号时长。
    *   **高危 (<60)**: 触发熔断，停止发布并报警。

### 2.3 预警与熔断机制
*   **实时报警**: 当账号健康分骤降或收到违规通知时，通过邮件/钉钉 webhook 推送告警。
*   **自动熔断**: 
    *   一旦触发高危阈值，系统自动将该账号从分发队列中移除。
    *   启动“静默期”逻辑，连续 3 天仅执行浏览操作，不发布任何内容。

## 3. 数据库设计 (MySQL)
```sql
CREATE TABLE account_health (
    account_id VARCHAR(64) PRIMARY KEY,
    health_score INT DEFAULT 100,
    last_publish_time DATETIME,
    status ENUM('active', 'nurturing', 'banned') DEFAULT 'active',
    warning_count INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```
