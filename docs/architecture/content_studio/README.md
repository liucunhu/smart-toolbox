# 爆款内容智造局 (Content Studio) 架构设计

## 1. 模块概述
本模块是 Smart-Toolbox 的核心创作引擎，负责将原始素材转化为符合各平台算法偏好的“爆款”作品。

## 2. 子功能架构文档

### 2.1 平台差异化文案生成
*   **文档路径**: `docs/architecture/content_studio/copywriting_generation.md`
*   **核心技术**: LLM Prompt Engineering, 风格迁移模型。
*   **架构要点**:
    *   **模板化提示词**: 针对抖音（悬念）、小红书（种草）、视频号（共鸣）预设不同的 System Prompt。
    *   **热点注入**: 实时抓取全网热搜关键词，强制植入生成的文案中。

### 2.2 视觉爆款合成
*   **文档路径**: `docs/architecture/content_studio/visual_synthesis.md`
*   **核心技术**: OpenCV, FFmpeg, Stable Diffusion (封面生成)。
*   **架构要点**:
    *   **智能封面工厂**: 自动截取视频高潮帧，叠加平台专属风格的文字与滤镜。
    *   **情绪字幕系统**: 结合语音识别 (ASR) 与情感分析，动态调整字幕颜色与大小。

### 2.3 智能去重与伪原创
*   **文档路径**: `docs/architecture/content_studio/deduplication.md`
*   **核心技术**: 随机扰动算法, 帧序列重组, MD5 混淆。
*   **架构要点**:
    *   **多维去重**: 从画面（镜像、缩放）、音频（变速、变调）、数据（元数据修改）三个维度进行深度加工。
    *   **结构重组**: AI 识别视频片段语义，自动打乱非逻辑依赖的片段顺序。

---

## 3. 接口定义 (API Contract)
*   `POST /api/v1/content/generate`: 提交原始素材与目标平台，获取成品视频链接。
*   `GET /api/v1/content/templates`: 获取当前可用的爆款文案与视觉模板列表。
