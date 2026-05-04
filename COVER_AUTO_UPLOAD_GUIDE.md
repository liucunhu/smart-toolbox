# 头条发布封面图自动上传功能说明

## 📋 功能概述

系统现已支持在单图模式下**自动生成并上传LLM智能封面图**，实现完全自动化的封面图处理流程。

## ✨ 核心特性

### 1. LLM智能封面生成
- ✅ **内容分析**：基于文章标题和内容进行深度分析
- ✅ **智能设计**：自动生成视觉风格、配色方案、设计元素
- ✅ **关键词提取**：提取文章核心关键词用于封面设计
- ✅ **多提供商支持**：支持SiliconFlow、ModelScope、DeepSeek、OpenAI等

### 2. 降级保障机制
```
LLM智能生成 (优先)
    ↓ 失败
传统AI生成 (PIL图形)
    ↓ 失败
保持单图模式但不上传图片
```

### 3. 自动上传流程
1. **选择单图模式** → 确保使用单图布局
2. **生成封面图** → LLM分析文章内容生成
3. **压缩优化** → 自动压缩至最佳尺寸和质量
4. **自动上传** → 通过file input自动上传
5. **验证状态** → 确认上传成功

## 🔧 技术实现

### 主服务层 - toutiao_publisher.py

#### 执行流程
```python
# 1. 生成封面图（如果启用auto_generate_cover）
if auto_generate_cover and not cover_image_path:
    # LLM智能生成
    result = llm_generator.generate_cover_with_llm_analysis(
        title=title,
        content=content,
        category=category,
        style_override=cover_style
    )
    
    if result["status"] == "success":
        cover_image_path = result["file_path"]

# 2. 压缩优化封面图
if cover_image_path:
    compress_result = processor.compress_image(
        input_path=cover_image_path,
        quality=85,
        max_width=1920,
        max_height=1080,
        output_format='jpg'
    )
    cover_image_path = compress_result["output_path"]

# 3. 选择单图模式
await self._select_single_image_mode()

# 4. 上传封面图
if cover_image_path:
    await self._upload_cover_with_cdp_optimization(cover_image_path)
```

#### 关键方法

**`_select_single_image_mode()`** - 选择单图模式
- 方案0：检查当前状态，避免重复操作
- 方案1：Playwright text选择器
- 方案2：JavaScript radio button点击
- 方案3：查找文本元素点击
- 验证：确认选择成功

**`_upload_cover_with_cdp_optimization(cover_image_path)`** - CDP优化上传
- 滚动到封面区域
- 再次确认单图模式
- 查找file input元素
- 使用set_input_files上传
- 等待上传完成

### 测试脚本 - test_cdp_auto_publish.py

#### 智能生成与上传
```python
# 找到 file input，生成并上传封面图
if upload_result['fileInputs']:
    try:
        # LLM智能生成
        from app.services.content.llm_cover_generator import get_llm_cover_generator
        llm_generator = get_llm_cover_generator()
        
        result = llm_generator.generate_cover_with_llm_analysis(
            title=title,
            content=content,
            category="科技",
            style_override=None
        )
        
        if result["status"] == "success":
            cover_image_path = result["file_path"]
            
            # 上传图片
            await page.locator('input[type="file"]').first.set_input_files(cover_image_path)
            
    except Exception as e:
        # 降级：传统AI生成
        from app.services.content.ai_cover_generator import AICoverGenerator
        generator = AICoverGenerator()
        
        ai_result = generator.generate_cover(
            title=title,
            subtitle="",
            category="科技",
            style="modern"
        )
        
        if ai_result["status"] == "success":
            cover_image_path = ai_result["file_path"]
            await page.locator('input[type="file"]').first.set_input_files(cover_image_path)
```

## 📊 使用示例

### 方式1：使用ToutiaoPublisher类

```python
from app.services.publish.toutiao_publisher import ToutiaoPublisher

publisher = ToutiaoPublisher(account_id=1)
await publisher.initialize_browser()

# 登录
login_result = await publisher.login_with_manual_input(
    username="your_account",
    password="your_password"
)

# 发布文章（自动生成并上传LLM封面）
result = await publisher.publish_article(
    title="人工智能技术发展趋势分析",
    content="这是一篇关于人工智能的深度分析文章...",
    category="科技",
    auto_generate_cover=True,  # 启用自动生成
    cover_style="modern",       # 指定风格（可选）
    declaration_type="personal_opinion"  # 作品声明类型
)

print(f"发布结果: {result}")
```

### 方式2：运行测试脚本

```bash
# 完整的CDP自动发布测试（包含LLM封面生成和上传）
python test_cdp_auto_publish.py

# 单独测试单图模式选择
python test_single_image_mode.py
```

### 方式3：使用API接口

```bash
curl -X POST http://localhost:8000/api/v1/content/toutiao/publish \
  -d "account_id=1" \
  -d "title=人工智能技术发展趋势" \
  -d "content=文章内容..." \
  -d "category=科技" \
  -d "auto_generate_cover=true" \
  -d "cover_style=modern" \
  -d "declaration_type=personal_opinion"
```

## 🎯 工作流程详解

### 完整流程图
```
开始发布
    ↓
[步骤1] 生成封面图
    ├─→ LLM智能分析文章内容
    ├─→ 生成设计计划（风格、配色、关键词）
    ├─→ 创建封面图片
    └─→ 保存到 uploads/llm_covers/
    ↓
[步骤2] 压缩优化
    ├─→ 调整尺寸（最大1920x1080）
    ├─→ 压缩质量（85%）
    └─→ 转换为JPG格式
    ↓
[步骤3] 选择单图模式 ⭐
    ├─→ 检查当前状态
    ├─→ 尝试3种方案选择"单图"
    └─→ 验证选择成功
    ↓
[步骤4] 上传封面图
    ├─→ 滚动到封面区域
    ├─→ 查找file input元素
    ├─→ 使用set_input_files上传
    └─→ 等待上传完成（3秒）
    ↓
[步骤5] 设置作品声明
    ├─→ 滚动到页面底部
    ├─→ 查找声明选项
    └─→ 勾选"仅个人观点"
    ↓
[步骤6] 点击发布
    ├─→ 点击"预览并发布"
    ├─→ 点击"确认发布"
    └─→ 验证发布成功
    ↓
完成
```

## 🔍 日志输出示例

```
正在检查封面图...
🤖 开始AI生成封面图...
✅ LLM智能封面生成成功!
   视觉风格: modern
   配色方案: blue
   关键词: ['人工智能', '技术发展', '深度学习']
📦 优化封面图...
✅ 封面图压缩完成: 65% 压缩率
📸 开始设置封面图模式...
   步骤1：选择'单图'模式...
   当前状态: 单图未选中
   尝试方案1：text 选择器...
   ✅ 已通过 text 选择器选择'单图'
   验证状态: 已选中
   ✅ '单图'模式选择成功！
📸 开始设置封面图（CDP优化模式）...
   步骤1：选择'单图'模式...
   ✅ 已通过 text 选择器选择'单图'
   步骤2：上传封面图片...
   ✅ 图片已上传
✅ 封面图设置完成
📝 设置作品声明（类型: personal_opinion）...
   ✅ 已滚动到底部
   正在查找'仅个人观点，仅供参考'选项...
   ✅ 已勾选仅个人观点声明
```

## 💡 优势特点

### 1. 智能化
- LLM深度分析文章内容
- 自动生成匹配的视觉设计
- 智能选择风格和配色

### 2. 可靠性
- 多重降级保障机制
- 三种方案确保单图选择
- 详细的验证和日志

### 3. 自动化
- 无需手动上传图片
- 自动压缩优化
- 一键完成全流程

### 4. 灵活性
- 支持自定义风格
- 可切换声明类型
- 兼容多种LLM提供商

## 📁 相关文件

### 核心文件
- `app/services/publish/toutiao_publisher.py` - 主发布服务
- `app/services/content/llm_cover_generator.py` - LLM封面生成器
- `app/services/content/ai_cover_generator.py` - 传统AI封面生成器
- `app/utils/image_processor.py` - 图片压缩处理器

### 测试文件
- `test_cdp_auto_publish.py` - 完整CDP自动发布测试
- `test_single_image_mode.py` - 单图模式选择测试
- `test_llm_cover_generation.py` - LLM封面生成测试

### 配置文件
- `.env` - LLM API密钥配置
- `templates/covers/templates_config.json` - 封面模板配置

## 🚀 快速开始

### 1. 配置LLM API密钥
```bash
# .env文件
SILICONFLOW_API_KEY=your_api_key
SILICONFLOW_MODEL=Qwen/Qwen2.5-Coder-32B-Instruct
```

### 2. 安装依赖
```bash
pip install pillow openai playwright
playwright install
```

### 3. 运行测试
```bash
python test_cdp_auto_publish.py
```

### 4. 查看生成的封面图
```bash
# LLM生成的封面图保存在
ls uploads/llm_covers/

# 传统AI生成的封面图保存在
ls uploads/ai_covers/
```

## ❓ 常见问题

### Q1: LLM生成失败怎么办？
A: 系统会自动降级到传统AI生成（PIL图形），确保总有封面图可用。

### Q2: 找不到file input元素怎么办？
A: 系统会保持"单图"模式但不上传图片，您可以后续手动上传。

### Q3: 如何自定义封面风格？
A: 在调用时传入`cover_style`参数：
```python
cover_style="modern"  # 现代风格
cover_style="minimal" # 极简风格
cover_style="bold"    # 大胆风格
```

### Q4: 封面图太大怎么办？
A: 系统会自动压缩优化，最大尺寸1920x1080，质量85%，通常可减少50-70%文件大小。

## 📝 总结

现在系统已经完全实现了：
- ✅ **单图模式选择** - 确保使用单图布局
- ✅ **LLM智能封面生成** - 基于文章内容自动生成
- ✅ **自动压缩优化** - 调整尺寸和质量
- ✅ **自动上传** - 通过file input自动上传
- ✅ **作品声明设置** - 支持"仅个人观点"声明
- ✅ **完整自动化** - 从生成到发布全流程自动化

所有功能已就绪，可以立即使用！🎉
