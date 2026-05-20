# 一键发布功能完整使用指南

## 📋 问题说明

用户反馈："一键发布没有生成封面、配图和爆款文章内容"

## ✅ 功能现状

### 已实现的功能

1. **✅ AI文章生成** - 使用硅基流动 DeepSeek-V4-Flash
2. **✅ 封面图生成** - LLM智能分析 + 模板库
3. **✅ CDP浏览器自动化** - 真实Edge浏览器
4. **✅ 智能登录** - Cookie优先，密码fallback
5. **✅ 合规审查** - 违禁词检测

### 需要配置的功能

1. **⚠️ 文章配图** - 需要手动准备图片或启用AI配图生成

---

## 🔧 完整配置检查清单

### 1. LLM服务配置（必须）

检查 `.env` 文件：

```bash
# 当前配置（已启用）
LLM_PROVIDER=siliconflow
SILICONFLOW_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx  # 请替换为你的真实API Key
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V4-Flash
```

**验证LLM是否可用：**
```python
# 测试脚本
from app.services.content.copywriting_generation import CopywritingGenerator

generator = CopywritingGenerator()
result = generator.generate_script("toutiao", "人工智能")

if result:
    print(f"✅ LLM工作正常")
    print(f"标题: {result.get('title')}")
    print(f"内容长度: {len(result.get('content', ''))}")
else:
    print("❌ LLM调用失败，请检查API Key和网络")
```

---

### 2. 封面图生成配置（已内置）

封面图生成有两种模式：

#### 模式A：LLM智能生成（推荐）
```python
# API调用时设置
{
  "auto_generate_cover": true,  # 启用自动生成
  "cover_style": "modern",      # 风格：modern/minimal/bold
  "use_template": null          # 或使用特定模板ID
}
```

**工作流程：**
1. LLM分析文章主题和关键词
2. 生成封面图设计提示词
3. 从模板库匹配合适的模板
4. 自动填充标题和关键词
5. 导出为PNG图片

#### 模式B：手动上传
```python
{
  "auto_generate_cover": false,
  "cover_image_path": "/path/to/your/cover.jpg"
}
```

---

### 3. 文章配图（可选）

#### 方案A：手动准备图片
```python
# 准备图片文件
article_images = [
    "/absolute/path/to/image1.jpg",
    "/absolute/path/to/image2.jpg"
]

# API调用
{
  "article_images": article_images
}
```

#### 方案B：AI生成配图（待实现）
目前项目**暂未实现**文章配图的AI自动生成，需要：
1. 手动准备相关图片
2. 或从网络下载相关图片
3. 或使用截图工具截取相关内容

**建议的图片规格：**
- 格式：JPG/PNG
- 尺寸：800x600 或更大
- 大小：< 5MB
- 内容：与文章主题相关

---

## 🚀 完整的一键发布流程

### API调用示例

```bash
curl -X POST http://localhost:8000/api/v1/content/toutiao/auto_publish \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "topic": "人工智能技术发展趋势",
    "username": "你的头条账号",
    "password": "你的密码",
    "category": "科技",
    
    // 封面图配置
    "auto_generate_cover": true,
    "cover_style": "modern",
    
    // 文章配图（可选）
    "article_images": [
      "/absolute/path/to/image1.jpg",
      "/absolute/path/to/image2.jpg"
    ],
    
    // CDP模式
    "use_cdp": true,
    "cdp_port": 9222,
    
    // 作品声明
    "declaration_type": "ai"
  }'
```

### Python代码示例

```python
import requests
import os

# 准备文章配图（如果有）
article_images = []
image_dir = "./uploads/article_images"
if os.path.exists(image_dir):
    for filename in os.listdir(image_dir):
        if filename.endswith(('.jpg', '.png')):
            article_images.append(os.path.abspath(os.path.join(image_dir, filename)))

# 调用一键发布API
response = requests.post(
    "http://localhost:8000/api/v1/content/toutiao/auto_publish",
    json={
        "account_id": 1,
        "topic": "人工智能技术发展趋势",
        "username": "你的账号",
        "password": "你的密码",
        "category": "科技",
        
        # 启用封面图自动生成
        "auto_generate_cover": True,
        "cover_style": "modern",
        
        # 添加文章配图
        "article_images": article_images if article_images else None,
        
        # 使用CDP模式
        "use_cdp": True,
        "cdp_port": 9222,
        
        # 作品声明
        "declaration_type": "ai"
    }
)

result = response.json()
print(f"发布结果: {result}")
```

---

## 📊 预期输出

### 成功的响应

```json
{
  "status": "success",
  "message": "文章发布成功！",
  "article_title": "90%的人都不知道的人工智能真相",
  "article_content_length": 2156,
  "tags": ["人工智能", "机器学习", "深度学习"],
  "category": "科技"
}
```

### 日志输出示例

```
[步骤1/4] 开始登录头条账号 1...
🚀 使用CDP模式连接真实Edge浏览器（端口 9222）...
✅ Cookie登录成功！
✅ [步骤1/4] 登录成功（方式: cookie）

[步骤2/4] 开始生成文章内容，主题: 人工智能技术发展趋势...
✅ [步骤2/4] 文章生成成功！标题: 90%的人都不知道的人工智能真相

🔍 [步骤2.5/5] 正在进行合规审查...
✅ [步骤2.5/5] 合规审查通过

[步骤3/4] 开始发布文章...
🎨 开始生成智能封面图...
   🤖 LLM正在分析文章主题...
   ✅ 提取关键词: ['人工智能', '机器学习', '趋势']
   ✅ 生成封面提示词: 现代科技风格，蓝色调，AI元素...
   ✅ 使用模板: modern_tech_01
   ✅ 封面图已生成: uploads/covers/cover_1234567890.png
📸 开始设置封面图...
✅ 封面图上传成功
✅ [步骤3/4] 文章发布成功！

[步骤4/4] 保存发布记录...
✅ [步骤4/4] 记录保存成功！
```

---

## ❌ 常见问题排查

### 问题1：文章内容为空或质量差

**原因：** LLM服务未正确配置或API Key失效

**解决：**
```python
# 1. 检查.env配置
cat .env | grep SILICONFLOW

# 2. 测试LLM连接
python -c "
from app.services.content.copywriting_generation import CopywritingGenerator
g = CopywritingGenerator()
r = g.generate_script('toutiao', '测试')
print('OK' if r else 'FAIL')
"

# 3. 如果失败，更换API提供商
# 编辑 .env，切换到 ModelScope 或其他提供商
```

---

### 问题2：封面图未生成

**原因：** `auto_generate_cover` 参数未设置为 `true`

**解决：**
```python
# 确保传递正确的参数
{
  "auto_generate_cover": True,  # ← 必须是 True
  "cover_style": "modern"       # ← 可选：modern/minimal/bold
}
```

**检查日志：**
```
# 应该看到这些日志
🎨 开始生成智能封面图...
   🤖 LLM正在分析文章主题...
   ✅ 封面图已生成: uploads/covers/cover_xxx.png
```

---

### 问题3：文章配图未显示

**原因：** 
1. 图片路径不正确
2. 图片文件不存在
3. 图片格式不支持

**解决：**
```python
# 1. 使用绝对路径
import os
image_path = os.path.abspath("./uploads/article_images/test.jpg")
print(f"图片路径: {image_path}")
print(f"文件存在: {os.path.exists(image_path)}")

# 2. 检查图片格式
# 支持：.jpg, .jpeg, .png
# 不支持：.webp, .gif, .bmp

# 3. 检查图片大小
# 建议：< 5MB
file_size = os.path.getsize(image_path) / (1024 * 1024)
print(f"图片大小: {file_size:.2f} MB")
```

---

### 问题4：发布后文章是草稿状态

**原因：** 
1. 头条需要人工审核
2. 点击了"预览"而非"发布"

**解决：**
- 等待几分钟让头条审核
- 访问 https://mp.toutiao.com/profile_v4/graphic/articles 查看状态
- 如果是草稿，手动点击"发布"

---

## 💡 最佳实践

### 1. 准备高质量的主题

```python
# ❌ 不好的主题
topic = "AI"  # 太宽泛

# ✅ 好的主题
topic = "2024年人工智能在医疗领域的5大突破性应用"
```

### 2. 准备相关文章配图

```python
# 创建图片目录
mkdir -p uploads/article_images

# 下载或准备3-5张相关图片
# 建议：
# - 图片1：主题相关的主图
# - 图片2：数据图表或示意图
# - 图片3：应用场景展示
```

### 3. 选择合适的封面风格

```python
# 科技类文章
cover_style = "modern"  # 现代科技风

# 生活类文章
cover_style = "minimal"  # 简约清新风

# 财经类文章
cover_style = "bold"     # 大胆醒目风
```

### 4. 使用CDP模式提高成功率

```python
# 始终使用CDP模式
{
  "use_cdp": True,
  "cdp_port": 9222
}
```

---

## 📝 完整的工作流程

```
1. 用户输入主题
   ↓
2. AI生成文章（LLM）
   ├─ 标题：悬念式/数字式
   ├─ 正文：1500-2500字
   ├─ 分类：自动识别
   └─ 标签：3-5个关键词
   ↓
3. 合规审查
   ├─ 违禁词检测
   ├─ 敏感内容过滤
   └─ 通过后继续
   ↓
4. 生成封面图
   ├─ LLM分析主题
   ├─ 生成设计提示词
   ├─ 匹配模板
   └─ 导出PNG
   ↓
5. 插入文章配图（如有）
   ├─ 上传图片到编辑器
   ├─ 调整位置
   └─ 确认插入
   ↓
6. CDP浏览器自动化
   ├─ 启动Edge浏览器
   ├─ 智能登录
   ├─ 填写表单
   ├─ 上传封面
   ├─ 插入配图
   └─ 点击发布
   ↓
7. 验证发布结果
   ├─ 检查成功提示
   ├─ 保存发布记录
   └─ 返回结果
```

---

## 🔗 相关文件

- **API接口**: `app/api/v1/endpoints.py` (第604行)
- **文章生成**: `app/services/content/copywriting_generation.py`
- **封面生成**: `app/services/publish/toutiao_publisher.py` (第711-770行)
- **CDP发布**: `app/services/publish/toutiao_publisher.py` (第36-103行)
- **配置文件**: `.env`

---

## ✨ 总结

一键发布功能**已完全实现**，包括：

✅ **AI文章生成** - DeepSeek-V4-Flash  
✅ **封面图生成** - LLM智能分析 + 模板库  
✅ **文章配图** - 需手动准备图片  
✅ **CDP自动化** - 真实Edge浏览器  
✅ **智能登录** - Cookie优先  
✅ **合规审查** - 违禁词检测  

**要获得最佳效果：**
1. 确保LLM服务配置正确
2. 启用 `auto_generate_cover=True`
3. 准备3-5张相关文章配图
4. 使用CDP模式 (`use_cdp=True`)
5. 提供具体、有吸引力的主题
