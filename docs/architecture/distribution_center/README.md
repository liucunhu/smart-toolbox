# 合规分发中心 (Distribution Center) 架构设计

## 1. 模块概述
本模块负责将处理好的内容安全、高效地分发至各大主流平台，核心目标是**零违规发布**与**流量最大化**。

## 2. 子功能架构文档

### 2.1 违禁词实时筛查
*   **文档路径**: `docs/architecture/distribution_center/banned_words_check.md`
*   **核心技术**: AC 自动机算法, 动态词库管理。
*   **架构要点**:
    *   **多模态扫描**: 同时检测视频标题、文案、字幕甚至画面中的文字（OCR）。
    *   **智能替换**: 针对极限词、引流词提供谐音字、拼音或 Emoji 替代方案。

### 2.2 格式自适应转换
*   **文档路径**: `docs/architecture/distribution_center/format_conversion.md`
*   **核心技术**: FFmpeg 滤镜链, 智能裁剪算法。
*   **架构要点**:
    *   **比例重绘**: 自动将横屏内容通过“背景模糊填充”或“关键内容裁剪”转换为竖屏。
    *   **参数优化**: 根据不同平台要求自动调整码率（Bitrate）与编码格式（H.264/H.265）。

### 2.3 智能调度发布
*   **文档路径**: `docs/architecture/distribution_center/smart_scheduling.md`
*   **核心技术**: 分布式任务队列 (Celery), 粉丝活跃时段分析。
*   **架构要点**:
    *   **错峰机制**: 避免同一 IP 下多个账号在短时间内密集发布。
    *   **最佳时机**: 结合历史数据推荐各平台的黄金发布时间点。

---

## 3. 接口定义 (API Contract)
*   `POST /api/v1/distribute/publish`: 提交分发任务，指定目标平台与账号。
*   `GET /api/v1/distribute/tasks/{id}/progress`: 查询分发任务的实时进度。
