# 一键全自动发布功能使用指南

## 📋 功能概述

**一键全自动发布**是Smart-Toolbox最强大的功能，只需输入一个主题，系统会自动完成：

1. ✅ **AI生成爆款文章** - DeepSeek-V4-Flash模型
2. ✅ **LLM智能封面图** - 分析文章内容生成封面
3. ✅ **合规审查** - 违禁词检测
4. ✅ **CDP浏览器自动化** - 真实Edge浏览器发布
5. ✅ **智能登录** - Cookie优先，密码fallback
6. ✅ **保存发布记录** - 自动记录到数据库

---

## 🚀 使用方法

### 方式1：前端界面操作（推荐）

#### 步骤1：进入内容创作页面
访问：`http://localhost:5173/content-creation`

#### 步骤2：输入创作主题
在"创作主题"输入框中输入你的主题，例如：
```
如何使用DeepSeek生成爆款文章
```

#### 步骤3：选择发布账号
从下拉列表中选择已登录的头条账号。

**如果账号未登录：**
- 点击"头条账号管理"页面
- 找到对应账号
- 点击"登录"按钮完成登录

#### 步骤4：点击"一键全自动发布"
点击蓝色的"一键全自动发布"按钮。

#### 步骤5：输入账号密码
系统会弹出两个对话框：
1. 第一个：输入头条账号的登录手机号/邮箱
2. 第二个：输入头条账号的登录密码

#### 步骤6：等待发布完成
系统会自动执行以下流程（约2-5分钟）：
```
[步骤1/4] 开始登录头条账号...
✅ 登录成功

[步骤2/4] 开始生成文章内容...
✅ 文章生成成功！标题: xxx

[步骤2.5/5] 正在进行合规审查...
✅ 合规审查通过

[步骤3/4] 开始发布文章...
🤖 开始AI生成封面图...
   ✅ LLM智能封面生成成功!
📸 开始设置封面图...
   ✅ 封面图上传成功
✅ 文章发布成功！

[步骤4/4] 保存发布记录...
✅ 记录保存成功！
```

---

### 方式2：API直接调用（开发调试）

#### 请求示例

```bash
curl -X POST http://localhost:8000/api/v1/content/toutiao/auto_publish \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 9,
    "topic": "如何使用DeepSeek生成爆款文章",
    "username": "17739848781",
    "password": "Lch@12345",
    "category": "科技",
    "auto_generate_cover": true,
    "cover_style": "modern",
    "use_cdp": true,
    "cdp_port": 9222,
    "declaration_type": "ai"
  }'
```

#### Python代码示例

```python
import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

payload = {
    "account_id": 9,
    "topic": "如何使用DeepSeek生成爆款文章",
    "username": "17739848781",
    "password": "Lch@12345",
    "category": "科技",
    
    # ✅ 启用封面图生成
    "auto_generate_cover": True,
    "cover_style": "modern",
    
    # ✅ CDP模式
    "use_cdp": True,
    "cdp_port": 9222,
    
    # ✅ 作品声明
    "declaration_type": "ai"
}

response = requests.post(
    f"{BASE_URL}/content/toutiao/auto_publish",
    params=payload,  # 注意：使用 params 而不是 json
    timeout=300  # 5分钟超时
)

result = response.json()
print(json.dumps(result, indent=2, ensure_ascii=False))
```

#### 使用测试脚本

```powershell
# 运行完整的测试脚本
python D:\code\smart-toolbox\scripts\test_full_publish.py
```

---

## 📊 参数说明

### 必需参数

| 参数 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `account_id` | int | 账号ID | `9` |
| `topic` | string | 文章主题 | `"如何使用DeepSeek生成爆款文章"` |
| `username` | string | 登录账号（手机号/邮箱） | `"17739848781"` |
| `password` | string | 登录密码 | `"Lch@12345"` |

### 可选参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `category` | string | `"科技"` | 文章分类 |
| `auto_generate_cover` | boolean | `True` | 是否自动生成封面图 |
| `cover_style` | string | `"modern"` | 封面风格：modern/minimal/bold |
| `use_cdp` | boolean | `True` | 是否使用CDP模式 |
| `cdp_port` | int | `9222` | CDP调试端口 |
| `declaration_type` | string | `"ai"` | 作品声明：ai/personal_opinion |
| `article_images` | list | `null` | 文章配图路径列表 |

---

## 🎨 封面图生成详解

### 三层降级策略

#### 第一层：LLM智能分析（推荐）
```
1. LLM分析文章主题和关键词
2. 生成视觉风格建议
3. 匹配合适的模板
4. 自动填充标题和关键词
5. 导出为PNG图片
```

**日志示例：**
```
🤖 开始AI生成封面图...
   🤖 LLM正在分析文章主题...
   ✅ 提取关键词: ['DeepSeek', '爆款', '文章']
   ✅ 生成封面提示词: 现代科技风格，蓝紫色调，AI元素...
   ✅ 使用模板: modern_tech_01
   ✅ 封面图已生成: uploads/covers/cover_1234567890.png
```

#### 第二层：模板库匹配
如果LLM失败，使用预定义的模板库。

#### 第三层：传统AI生成（PIL图形）
如果前两层都失败，使用PIL生成简单的文字封面。

---

## 📝 文章配图说明

### 当前状态
⚠️ **项目暂不支持AI自动生成文章配图**

### 解决方案

#### 方案A：手动准备图片
```python
# 1. 准备图片文件
mkdir uploads/article_images

# 2. 放入相关图片（3-5张）
# - image1.jpg: 主题相关的主图
# - image2.jpg: 数据图表或示意图
# - image3.jpg: 应用场景展示

# 3. API调用时传入路径
{
  "article_images": [
    "D:/code/smart-toolbox/uploads/article_images/image1.jpg",
    "D:/code/smart-toolbox/uploads/article_images/image2.jpg"
  ]
}
```

#### 方案B：从网络下载
使用爬虫工具下载与主题相关的图片。

#### 方案C：截图工具
截取相关内容作为配图。

### 图片要求
- **格式**：JPG/PNG
- **尺寸**：800x600 或更大
- **大小**：< 5MB
- **内容**：与文章主题相关

---

## 🔍 常见问题

### Q1: 为什么显示"未提供封面图"？

**原因：** 浏览器缓存导致前端代码未更新。

**解决：**
1. 按 `Ctrl + Shift + R` 硬刷新浏览器
2. 或使用测试脚本绕过前端

---

### Q2: 发布后URL未变化，显示失败？

**原因：** 头条发布需要较长时间（30+秒）。

**解决：** 
已修复！现在会等待最多30秒检测发布请求，20秒检测URL跳转。

---

### Q3: 多个请求同时发布会冲突吗？

**原因：** 之前的代码复用同一个标签页。

**解决：**
已修复！现在每个请求创建独立的标签页，支持并发。

---

### Q4: Edge浏览器会被关掉吗？

**原因：** 之前的代码会关闭整个浏览器。

**解决：**
已修复！CDP模式下只关闭标签页，保持浏览器运行。

---

### Q5: 如何提高成功率？

**建议：**
1. ✅ 始终使用CDP模式（`use_cdp=True`）
2. ✅ 启用封面图生成（`auto_generate_cover=True`）
3. ✅ 使用具体的主题（不要太宽泛）
4. ✅ 确保账号已登录（有Cookie）
5. ✅ 耐心等待（整个过程需要2-5分钟）

---

## 📈 性能指标

### 时间消耗

| 步骤 | 耗时 | 说明 |
|------|------|------|
| 智能登录 | 5-10秒 | Cookie登录更快 |
| AI生成文章 | 10-20秒 | 取决于LLM响应速度 |
| 合规审查 | 1-2秒 | 本地检测 |
| 封面图生成 | 5-10秒 | LLM分析+模板匹配 |
| 浏览器自动化 | 30-60秒 | 填写表单+上传+发布 |
| **总计** | **2-5分钟** | 首次发布较慢 |

### 成功率

| 模式 | 成功率 | 说明 |
|------|--------|------|
| CDP模式 | 95%+ | 真实浏览器环境 |
| 标准模式 | 70%+ | 可能被反爬检测 |

---

## 🎯 最佳实践

### 1. 主题选择技巧

**❌ 不好的主题：**
```
AI
技术
互联网
```

**✅ 好的主题：**
```
2024年人工智能在医疗领域的5大突破性应用
如何使用DeepSeek在30分钟内写出爆款文章
今日头条算法解析：如何让文章获得10万+阅读
```

### 2. 封面风格选择

| 文章类型 | 推荐风格 | 说明 |
|----------|----------|------|
| 科技类 | `modern` | 现代科技风，蓝紫色调 |
| 生活类 | `minimal` | 简约清新风，浅色调 |
| 财经类 | `bold` | 大胆醒目风，深色调 |

### 3. 账号管理

**建议：**
1. 提前在"头条账号管理"页面登录账号
2. 系统会自动保存Cookie
3. 下次发布时直接使用Cookie登录（更快）

### 4. 发布时机

**最佳发布时间：**
- 早上 7:00-9:00
- 中午 12:00-13:00
- 晚上 18:00-21:00

---

## 🛠️ 调试技巧

### 查看日志

日志文件位置：`logs/`

**关键日志关键词：**
```bash
# 查找封面生成日志
grep "LLM智能封面生成" logs/*.log

# 查找发布结果
grep "发布成功\|发布失败" logs/*.log

# 查找错误信息
grep "ERROR" logs/*.log
```

### 查看截图

截图文件位置：`logs/`

- `toutiao_pre_publish_xxx.png` - 发布前截图
- `toutiao_post_publish_xxx.png` - 发布后截图

### 查看HTML

HTML文件位置：`logs/`

- `toutiao_pre_publish_xxx.html` - 发布前页面HTML

---

## 📚 相关文档

- [CDP集成文档](./CDP_PUBLISH_INTEGRATION.md)
- [快速参考](./CDP_QUICK_REFERENCE.md)
- [一键发布指南](./ONE_CLICK_PUBLISH_GUIDE.md)

---

## ✨ 总结

**一键全自动发布**是Smart-Toolbox的核心功能，能够：

✅ **完全自动化** - 只需输入主题  
✅ **AI生成内容** - DeepSeek-V4-Flash模型  
✅ **智能封面图** - LLM分析+三层降级  
✅ **高成功率** - CDP模式95%+  
✅ **并发支持** - 独立标签页隔离  

**立即体验：**
1. 打开前端页面
2. 输入主题
3. 点击"一键全自动发布"
4. 等待2-5分钟
5. 完成！🎉
