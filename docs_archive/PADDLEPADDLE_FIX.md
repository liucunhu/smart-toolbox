# PaddlePaddle 依赖问题解决方案

## ❌ 问题描述

```
ERROR: No matching distribution found for paddlepaddle==3.0.0
ERROR: No matching distribution found for paddlepaddle==2.6.2
```

## 🔍 根本原因

**Python版本不兼容**: 
- 当前使用 Python **3.14.2**
- PaddlePaddle 最高支持到 Python **3.12**
- PaddlePaddle 3.0.0 版本不存在（最新稳定版是 2.x系列）

---

## ✅ 解决方案

### 方案一：降级Python版本（推荐用于生产环境）

使用 Python 3.10-3.12 重新创建虚拟环境：

```powershell
# 1. 删除现有虚拟环境
Remove-Item -Recurse -Force .venv

# 2. 使用Python 3.10/3.11/3.12创建新环境
py -3.10 -m venv .venv

# 3. 激活环境
.\.venv\Scripts\Activate.ps1

# 4. 安装依赖
pip install -r requirements.txt
```

**修改requirements.txt**:
```txt
paddlepaddle==2.6.2  # 改为存在的版本
```

---

### 方案二：跳过PaddlePaddle（推荐用于快速启动）

如果暂时不需要OCR和视频去重功能，可以优雅降级：

#### 已完成的修改

1. **修复requirements.txt**
   ```txt
   paddlepaddle==2.6.2  # 从3.0.0改为2.6.2
   ```

2. **添加依赖检查（deduplication.py）**
   ```python
   try:
       import cv2
       import numpy as np
       CV2_AVAILABLE = True
   except ImportError:
       CV2_AVAILABLE = False
   
   # 在使用时检查
   if not CV2_AVAILABLE:
       logger.warning("⚠️ OpenCV未安装，视频去重功能不可用")
       return self.input_path
   ```

3. **添加依赖检查（format_conversion.py）**
   ```python
   try:
       import ffmpeg
       FFMPEG_AVAILABLE = True
   except ImportError:
       FFMPEG_AVAILABLE = False
   ```

#### 安装核心依赖

```powershell
# 只安装核心功能所需依赖
pip install fastapi uvicorn sqlalchemy pymysql pydantic celery redis openai python-dotenv loguru passlib bcrypt python-jose tenacity nest-asyncio python-multipart pytest httpx alembic greenlet pydantic-settings
```

#### 启动服务

```powershell
# 后端API
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Celery Worker
celery -A app.tasks.celery_app.celery_app worker --loglevel=info --pool=solo

# 前端
cd frontend
npm run dev
```

---

### 方案三：使用Docker（最省心）

使用项目提供的Docker配置，自动处理所有依赖：

```powershell
# 启动所有服务（包括数据库和Redis）
docker-compose up -d

# 或只启动应用服务
docker-compose up -d backend frontend celery-worker
```

---

## 📊 功能影响评估

| 功能模块 | 无PaddlePaddle | 说明 |
|---------|---------------|------|
| **账号管理** | ✅ 正常 | 不受影响 |
| **AI文案生成** | ✅ 正常 | 使用OpenAI API |
| **违禁词检测** | ✅ 正常 | AC自动机实现 |
| **智能调度** | ✅ 正常 | 纯Python逻辑 |
| **健康监控** | ✅ 正常 | 数据库查询 |
| **JWT认证** | ✅ 正常 | python-jose |
| **视频去重** | ⚠️ 降级 | 返回原文件 |
| **格式转换** | ⚠️ 降级 | 返回原文件 |
| **OCR识别** | ❌ 不可用 | 需要PaddleOCR |

---

## 🎯 推荐方案

### 开发环境
✅ **方案二**：跳过PaddlePaddle，快速启动核心功能

### 测试环境  
✅ **方案一**：使用Python 3.10-3.12，安装完整依赖

### 生产环境
✅ **方案三**：使用Docker部署，确保环境一致性

---

## 📝 后续优化建议

1. **更新requirements.txt**
   ```txt
   # 标注可选依赖
   paddlepaddle==2.6.2; python_version<"3.13"  # 条件安装
   paddleocr==2.7.0.3; python_version<"3.13"
   ```

2. **添加依赖分组**
   ```txt
   # requirements_core.txt - 核心依赖
   fastapi
   uvicorn
   ...
   
   # requirements_video.txt - 视频处理（可选）
   paddlepaddle
   paddleocr
   opencv-python
   ffmpeg-python
   ```

3. **改进错误提示**
   ```python
   if not CV2_AVAILABLE:
       raise ImportError(
           "视频处理功能需要安装opencv-python。\n"
           "请运行: pip install opencv-python\n"
           "或使用Docker部署以包含所有依赖。"
       )
   ```

---

## 🔗 相关资源

- [PaddlePaddle官方文档](https://www.paddlepaddle.org.cn/)
- [PaddlePaddle版本支持](https://github.com/PaddlePaddle/Paddle)
- [Python版本兼容性](https://devguide.python.org/versions/)

---

**当前状态**: ✅ 核心功能可正常运行，视频处理功能优雅降级
