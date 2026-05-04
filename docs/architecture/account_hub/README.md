# 智能账号工厂 (Account Hub) 架构设计

## 1. 模块概述
本模块负责主流短视频平台（抖音、小红书、B站等）的账号全生命周期管理，核心目标是实现**高成功率注册**与**高权重养号**。

## 2. 子功能架构文档

### 2.1 自动化注册引擎
*   **文档路径**: `docs/architecture/account_hub/auto_registration.md`
*   **核心技术**: Playwright RPA, PaddleOCR, 虚拟手机号 API 集成。
*   **架构要点**:
    *   **指纹隔离容器**: 为每个注册任务启动独立的浏览器上下文，注入随机化的 WebGL、Canvas 及 User-Agent。
    *   **验证码突破**: 采用 CNN 模型识别滑块缺口，结合模拟人类拖拽轨迹（贝塞尔曲线）通过验证。

### 2.2 智能养号系统
*   **文档路径**: `docs/architecture/account_hub/smart_nurturing.md`
*   **核心技术**: 行为决策树, 随机延迟算法, 领域关键词匹配。
*   **架构要点**:
    *   **拟人化调度器**: 基于正态分布生成浏览停留时长，避免机械式固定间隔。
    *   **互动概率模型**: 根据账号阶段动态调整点赞、评论的概率权重。

### 2.3 账号健康监控
*   **文档路径**: `docs/architecture/account_hub/health_monitoring.md`
*   **核心技术**: 实时数据流处理, 异常检测算法。
*   **架构要点**:
    *   **多维度评分**: 综合播放量、互动率、违规记录计算账号健康分。
    *   **自动熔断**: 当检测到限流信号时，自动暂停该账号的分发任务并触发预警。

---

## 3. 接口定义 (API Contract)
*   `POST /api/v1/accounts/register`: 提交注册任务。
*   `GET /api/v1/accounts/{id}/status`: 查询账号当前状态与健康分。
