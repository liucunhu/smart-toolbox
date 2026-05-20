# 阿里百炼图像生成 - 快速开始指南

## 📌 概述

已成功集成阿里百炼（DashScope）图像生成API，替代暂时不可用的硅基流动。

### 优势

✅ **稳定可用** - 阿里云服务，稳定性高  
✅ **中文友好** - 对中文内容理解优秀  
✅ **新账号福利** - 开通即送500张免费额度（180天有效期）  
✅ **性价比高** - wanx2.1-t2i-turbo仅0.14元/张  
✅ **异步API** - 支持批量生成，不阻塞主流程  

---

##  快速开始

### 步骤1: 获取API密钥

1. 访问 [阿里云百炼控制台](https://bailian.console.aliyun.com/)
2. 注册/登录阿里云账号
3. 搜索"通义万相"并开通服务
4. 创建API密钥（AccessKey）

### 步骤2: 配置项目

编辑 `.env` 文件：

```bash
# 填写你的阿里百炼API密钥
DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx

# 选择模型（默认推荐wanx2.1-t2i-turbo）
DASHSCOPE_IMAGE_MODEL=wanx2.1-t2i-turbo
```

### 步骤3: 测试运行

```bash
# 运行测试脚本
python scripts/test_dashscope_image.py
```

---

## 🎨 可用模型

### 通义万相（推荐）

| 模型 | 价格 | 特点 | 适用场景 |
|------|------|------|----------|
| **wanx2.1-t2i-turbo** | 0.14元/张 |  速度快，性价比高 | 日常配图、封面图 |
| wanx2.1-t2i-plus | 0.20元/张 | 🎯 细节丰富，质量高 | 专业设计、海报 |
| wanx2.0-t2i-turbo | 0.04元/张 | 💰 成本最低 | 批量生成、测试 |

### 通义千问

| 模型 | 价格 | 特点 | 适用场景 |
|------|------|------|----------|
| qwen-image-plus | 0.20元/张 | 📝 文字渲染强 | 海报、PPT、图表 |
| qwen-image | 0.25元/张 |  综合能力强 | 电商、广告 |

---

## 💻 代码使用示例

### 基础用法

```python
from app.services.content.image_generator import ImageGenerator

# 初始化生成器
generator = ImageGenerator()

# 生成单张图像
result = await generator.generate_image(
    prompt="AI technology, machine learning, professional",
    style="realistic",
    aspect_ratio="16:9",
    provider="dashscope"  # 使用阿里百炼
)

if result["status"] == "success":
    print(f"图像已保存: {result['image_path']}")
```

### 批量生成

```python
# 批量生成3张配图
prompts = [
    "人工智能改变生活，智能家居场景",
    "机器学习算法可视化",
    "深度学习神经网络结构"
]

results = await generator.generate_images_batch(
    prompts=prompts,
    style="realistic",
    aspect_ratio="16:9"
)

# 统计成功数量
success_count = sum(1 for r in results if r["status"] == "success")
print(f"成功生成 {success_count}/{len(prompts)} 张")
```

### 文章配图生成

```python
# 从文章内容自动生成配图
images = await generator.generate_from_article(
    article_content="人工智能正在改变我们的生活...",
    num_images=3,
    style="realistic"
)
```

---

##  API工作流程

阿里百炼使用**异步API**，流程如下：

```
1. 创建任务 (POST /services/aigc/text2image/image-synthesis)
   ↓
2. 获取task_id
   ↓
3. 轮询任务状态 (GET /tasks/{task_id})
   ↓
4. 状态变为SUCCEEDED
   ↓
5. 下载图像并保存
```

**轮询策略：**
- 最多轮询30次
- 每次间隔5秒
- 总超时时间：150秒（2.5分钟）

---

## 📊 与硅基流动对比

| 特性 | 硅基流动 | 阿里百炼 |
|------|---------|---------|
| 当前状态 | ❌ 暂时不可用 | ✅ **稳定可用** |
| API类型 | 同步 | 异步（需轮询） |
| 生成速度 | 10-30秒 | 30-60秒 |
| 图像质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 中文支持 | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 价格 | ~0.02-0.1元 | 0.04-0.25元 |
| 免费额度 | 无 | **500张** |
| 新账号 | 需审核 | **立即可用** |

---

## ⚙️ 配置说明

### 环境变量

```bash
# 必填
DASHSCOPE_API_KEY=sk-xxx  # 你的API密钥

# 可选（有默认值）
DASHSCOPE_BASE_URL=https://dashscope.aliyuncs.com/api/v1
DASHSCOPE_IMAGE_MODEL=wanx2.1-t2i-turbo
```

### 默认提供商

已修改默认提供商为`dashscope`：

```python
# image_generator.py
self.default_provider = "dashscope"  # 默认使用阿里百炼
```

如果需要使用硅基流动（恢复后）：

```python
self.default_provider = "siliconflow"
```

---

## 🐛 故障排查

### 问题1: "未配置阿里百炼API密钥"

**原因：** `.env`文件中未配置`DASHSCOPE_API_KEY`

**解决：**
```bash
# 编辑.env文件
DASHSCOPE_API_KEY=sk-你的真实密钥
```

### 问题2: "生成超时"

**原因：** 网络问题或模型繁忙

**解决：**
- 检查网络连接
- 稍后重试
- 考虑使用更快的模型（turbo版本）

### 问题3: "任务失败: xxx"

**原因：** 提示词违规或账户问题

**解决：**
- 检查prompt是否包含违规内容
- 确认账户余额充足
- 查看日志获取详细错误信息

---

## 📝 最佳实践

### 1. 优化提示词

```python
# ✅ 好的提示词
prompt = "AI technology, machine learning, neural network visualization, professional, high quality, clean background"

#  避免的提示词
prompt = "图片"  # 太简单
```

### 2. 选择合适的尺寸

```python
# 文章配图推荐
aspect_ratio="16:9"  # 1024x576

# 社交媒体推荐
aspect_ratio="1:1"   # 1024x1024

# 手机竖屏推荐
aspect_ratio="9:16"  # 576x1024
```

### 3. 批量生成时控制并发

```python
# 使用generate_images_batch会自动顺序生成
# 避免同时发起过多请求
results = await generator.generate_images_batch(
    prompts=prompts,
    style="realistic"
)
```

---

## 💰 成本估算

### 日常使用（头条发布）

假设每天发布10篇文章，每篇2张配图：

```
10篇/天 × 2张/篇 × 0.14元/张 = 2.8元/天
2.8元/天 × 30天 = 84元/月
```

### 免费额度使用

新账号500张免费额度：
```
500张 ÷ 2张/篇 = 250篇文章
```

足够测试和小规模使用！

---

## 🔗 相关资源

- [阿里百炼官方文档](https://help.aliyun.com/zh/model-studio/)
- [通义万相模型介绍](https://help.aliyun.com/zh/model-studio/user-guide/text-to-image)
- [模型价格列表](https://help.aliyun.com/zh/model-studio/model-pricing)
- [API参考](https://help.aliyun.com/zh/model-studio/text-to-image-api-reference)

---

## ✅ 集成完成清单

- [x] 添加`DASHSCOPE_API_KEY`配置项
- [x] 实现`_generate_with_dashscope()`方法
- [x] 更新默认提供商为`dashscope`
- [x] 添加异步任务轮询机制
- [x] 创建测试脚本`test_dashscope_image.py`
- [x] 更新`.env`配置示例
- [x] 编写使用文档

---

**下一步：** 填写你的API密钥，运行测试脚本，开始使用AI图像生成！
