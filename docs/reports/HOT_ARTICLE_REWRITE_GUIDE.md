# 🔥 热点文章二次创作功能使用指南

## 📋 功能概述

当网络搜索无法获取热点内容时，系统会自动启动**热点文章二次创作引擎**，直接基于热点文章的原始内容进行深度分析，然后进行智能改写生成原创内容。

---

## ✨ 核心功能

### 1️⃣ **智能降级策略**

系统的素材获取采用5级降级策略：

```
优先级1: Bing搜索 API
    ↓ 失败
优先级2: SerpAPI 搜索
    ↓ 失败
优先级3: 头条热搜数据
    ↓ 失败
优先级4: AI生成内容框架 ← 新增
    ↓ 失败
优先级5: 纯LLM知识生成
```

### 2️⃣ **二次创作流程**

```
输入：热点文章（标题 + 内容）
    ↓
步骤1: 深度分析原文
  - 提取核心观点
  - 识别关键案例
  - 分析文章结构
  - 提取关键词
    ↓
步骤2: 制定改写策略
  - 结构重组
  - 视角转换
  - 案例替换
  - 语言润色
  - 深度扩展
  - 观点补充
    ↓
步骤3: 执行二次创作
  - 重新组织段落
  - 同义词替换
  - 添加新案例
  - 补充个人观点
    ↓
步骤4: 生成新标题
  - 基于原标题优化
  - 符合头条规范（≤30字）
  - 增强吸引力
    ↓
步骤5: 原创度评估
  - 句子相似度检测
  - 段落改写率计算
  - 输出原创度分数
    ↓
输出：原创文章（含智能优化建议）
```

---

## 🚀 使用方法

### 方法1：自动触发（推荐）

在网络搜索失败时，系统会**自动启动**二次创作引擎：

```python
from app.services.content.copywriting_generation import CopywritingGenerator

generator = CopywritingGenerator(db=db)

# 正常调用，无需额外参数
result = generator.generate_script(
    platform="toutiao",
    topic="AI技术在2026年的应用",
    enable_web_search=True  # 启用网络搜索
)

# 如果网络搜索失败，会自动尝试二次创作
```

**日志示例**：
```
🔍 开始搜索素材: AI技术在2026年的应用
❌ Bing搜索失败: API Key未配置
❌ SerpAPI搜索失败: API Key未配置
⚠️  所有搜索引擎失败，尝试使用头条热搜数据...
⚠️  头条热搜获取也失败: 连接超时
🔄 网络搜索完全失败，启动热点文章二次创作引擎...
✅ 已为话题 'AI技术在2026年的应用' 生成原创内容框架
✅ 二次创作引擎已生成内容建议
```

---

### 方法2：手动提供热点文章

如果你已经有热点文章的原始内容，可以直接传入进行二次创作：

```python
from app.services.content.copywriting_generation import CopywritingGenerator

generator = CopywritingGenerator(db=db)

# 热点文章原始内容
hot_article_title = "2026年AI技术将如何改变我们的生活"
hot_article_content = """
人工智能正在快速发展，深刻影响着我们的日常生活...
（这里是完整的文章内容）
"""

# 传入热点文章内容进行二次创作
result = generator.generate_script(
    platform="toutiao",
    topic="AI技术在2026年的应用",
    hot_article_title=hot_article_title,      # 新增参数
    hot_article_content=hot_article_content   # 新增参数
)

# 系统会自动进行深度分析和二次原创
```

**日志示例**：
```
🔄 检测到热点文章，启动二次创作模式
   原标题: 2026年AI技术将如何改变我们的生活
   原长度: 2500字
📊 开始分析文章，共 12 个段落，计划插入 3 张图片
✅ 原文分析完成
   核心观点: 5个
   关键案例: 3个
   文章结构: structured_with_headings
✅ 核心信息提取完成
✅ 改写策略制定完成: ['language_polish', 'structure_reorg', ...]
✅ 二次创作成功
   新标题: AI技术2026：这5个变化将颠覆你的生活
   原创度: 85%
   使用策略: 语言润色, 结构重组, 视角转换, 案例替换, 深度扩展, 观点补充
✅ 已将二次创作内容整合到提示词
```

---

### 方法3：直接使用二次创作引擎

可以独立调用二次创作引擎：

```python
from app.services.content.hot_article_rewriter import rewrite_hot_article

# 异步调用
result = await rewrite_hot_article(
    content=hot_article_content,
    title=hot_article_title,
    platform="toutiao",
    depth="deep"  # light/medium/deep
)

if result["status"] == "success":
    print(f"新标题: {result['new_title']}")
    print(f"原创度: {result['originality_score']:.0%}")
    print(f"改写策略: {result['rewrite_strategies_used']}")
    print(f"新内容: {result['content']}")
```

---

## 📊 返回结果格式

### 二次创作结果

```python
{
    "status": "success",
    "original_title": "2026年AI技术将如何改变我们的生活",
    "new_title": "AI技术2026：这5个变化将颠覆你的生活",
    "original_content_length": 2500,
    "new_content_length": 2800,
    "rewrite_strategies_used": [
        "语言润色",
        "结构重组",
        "视角转换",
        "案例替换",
        "深度扩展",
        "观点补充"
    ],
    "originality_score": 0.85,  # 原创度85%
    "content": "（二次创作后的完整文章内容）",
    "analysis": {
        "core_points": ["观点1", "观点2", ...],
        "key_examples": ["案例1", "案例2", ...],
        "data_points": ["数据1", "数据2", ...],
        "structure_type": "structured_with_headings",
        "paragraphs": [...],
        "keywords": ["AI", "技术", "生活", ...]
    }
}
```

### 文章生成结果（包含智能优化）

```python
{
    "title": "AI技术2026：这5个变化将颠覆你的生活",
    "content": "（完整文章内容）",
    "category": "科技",
    "tags": ["AI", "2026", "未来"],
    "platform": "toutiao",
    "topic": "AI技术在2026年的应用",
    
    # ★★★ 新增字段 ★★★
    "image_suggestions": [
        {
            "position": 3,
            "theme": "AI应用场景",
            "prompt": "展示AI在日常生活中的应用场景...",
            "keywords": ["AI", "应用", "生活"],
            "location_type": "正文中间",
            "rationale": "缓解阅读疲劳，增强理解",
            "preview_text": "人工智能正在改变我们的生活方式..."
        },
        ...
    ],
    
    "smart_optimization": {
        "title_optimization": {
            "current_length": 25,
            "optimal_range": [20, 30],
            "patterns_detected": [{"name": "数字型", "weight": 0.9}],
            "suggestions": [
                {"type": "length", "recommendation": "✅ 标题长度适中"}
            ]
        },
        "content_structure": {
            "paragraph_count": 10,
            "total_length": 2800,
            "avg_paragraph_length": 280,
            "structure_score": 85,
            "issues": [],
            "recommendations": ["✅ 结构清晰，小标题使用得当"]
        },
        "image_suggestions": [...],
        "engagement_tips": [
            "💬 在文中设置2-3个思考问题，引导读者评论",
            "📊 文末添加投票或征集观点，提升参与度"
        ],
        "publishing_tips": {
            "best_times": [
                {"time": "08:00-09:00", "reason": "早高峰通勤时间"},
                {"time": "19:00-21:00", "reason": "晚间休闲时间"}
            ],
            "recommendation": "💡 建议在工作日晚7-9点发布，获得最大曝光"
        }
    }
}
```

---

## 🎯 改写策略详解

### 1. 结构重组 (structure_reorg)
- **作用**：调整段落顺序，避免与原文结构雷同
- **实现**：保持开头和结尾，重新排列中间段落
- **适用场景**：原文结构清晰但需要差异化

### 2. 视角转换 (perspective_shift)
- **作用**：改变叙述角度（第三人称→第一人称等）
- **实现**：添加个人观点引导词（"笔者认为"、"在我看来"等）
- **适用场景**：增加文章的个人色彩和观点性

### 3. 案例替换 (example_replace)
- **作用**：用新案例替换原文案例
- **实现**：保留案例位置，替换具体内容
- **适用场景**：原文案例过时或缺乏新意

### 4. 语言润色 (language_polish)
- **作用**：同义词替换、句式变换
- **实现**：内置同义词库（非常重要→至关重要等）
- **适用场景**：所有文章的基础改写

### 5. 深度扩展 (depth_expand)
- **作用**：添加深度分析和趋势展望
- **实现**：在关键位置插入分析段落
- **适用场景**：原文深度不足，需要加强专业性

### 6. 观点补充 (opinion_add)
- **作用**：加入新的个人观点和建议
- **实现**：在适当位置插入观点段落
- **适用场景**：提升文章的独特性和价值

---

## ⚙️ 配置选项

### 改写深度 (rewrite_depth)

```python
# 轻度改写（适合快速生成）
depth = "light"
# 使用策略：语言润色 + 结构重组

# 中度改写（推荐）
depth = "medium"
# 使用策略：语言润色 + 结构重组 + 视角转换 + 案例替换

# 深度改写（最高原创度）
depth = "deep"
# 使用策略：全部6种策略
```

### 图片数量 (num_images)

```python
# 默认3张配图
num_images = 3

# 可根据文章长度调整
if len(content) > 3000:
    num_images = 5
elif len(content) < 1000:
    num_images = 2
```

---

## 📈 原创度评估

系统会自动评估二次创作的原创度：

```python
originality_score = result["originality_score"]

if originality_score >= 0.8:
    print("✅ 高原创度，可直接发布")
elif originality_score >= 0.6:
    print("⚠️  中等原创度，建议进一步修改")
else:
    print("❌ 原创度较低，需要深度改写")
```

**评估标准**：
- **0.8-1.0**: 高原创度，句子重叠率低，结构差异大
- **0.6-0.8**: 中等原创度，有部分相似但整体差异明显
- **0.4-0.6**: 低原创度，需要进一步优化
- **<0.4**: 极低原创度，不建议使用

---

## 🔧 故障排查

### 问题1：二次创作未触发

**症状**：网络搜索失败后，没有看到二次创作日志

**检查**：
```python
# 确认传入了热点文章内容
print(f"hot_article_content: {hot_article_content is not None}")
print(f"hot_article_title: {hot_article_title is not None}")

# 检查日志中是否有以下信息
# "🔄 检测到热点文章，启动二次创作模式"
```

**解决**：确保 `hot_article_content` 和 `hot_article_title` 都不为空

---

### 问题2：原创度过低

**症状**：`originality_score < 0.6`

**原因**：
- 改写深度不够
- 原文本身质量不高
- 缺乏足够的案例和观点补充

**解决**：
```python
# 使用深度改写模式
result = await rewrite_hot_article(
    content=hot_article_content,
    title=hot_article_title,
    depth="deep"  # 改为deep
)

# 或者手动添加更多内容
rewritten_content += "\n\n【个人观点】..."
```

---

### 问题3：图片位置不合理

**症状**：图片插入位置不符合预期

**检查**：
```python
# 查看图片位置建议
for suggestion in result["image_suggestions"]:
    print(f"位置: {suggestion['position'] + 1}段落后")
    print(f"主题: {suggestion['theme']}")
    print(f"理由: {suggestion['rationale']}")
```

**解决**：
- 调整 `num_images` 参数
- 手动修改 `image_suggestions` 列表
- 或在发布时使用均匀分布模式（不传 `image_suggestions`）

---

## 💡 最佳实践

### 1. 选择合适的改写深度

```python
# 新闻资讯类 → 轻度改写（时效性强，不需要太多个人观点）
depth = "light"

# 分析评论类 → 中度改写（需要加入观点）
depth = "medium"

# 深度解读类 → 深度改写（需要大量原创内容）
depth = "deep"
```

### 2. 结合多种数据源

```python
# 优先尝试网络搜索
result = generator.generate_script(
    platform="toutiao",
    topic="AI技术",
    enable_web_search=True  # 先尝试搜索
)

# 如果搜索结果不理想，再使用热点文章二次创作
if not result or len(result["content"]) < 1000:
    result = generator.generate_script(
        platform="toutiao",
        topic="AI技术",
        hot_article_content=hot_content,
        hot_article_title=hot_title
    )
```

### 3. 人工审核和优化

```python
# 二次创作后，建议人工检查
print(f"原创度: {result['originality_score']:.0%}")
print(f"新标题: {result['new_title']}")
print(f"内容长度: {result['new_content_length']}字")

# 检查关键点
assert result['originality_score'] >= 0.7, "原创度过低"
assert len(result['new_title']) <= 30, "标题超长"
assert result['new_content_length'] >= 1500, "内容过短"
```

### 4. 利用智能优化建议

```python
# 查看并使用优化建议
optimization = result["smart_optimization"]

# 标题优化
if optimization["title_optimization"]["suggestions"]:
    for suggestion in optimization["title_optimization"]["suggestions"]:
        print(f"标题建议: {suggestion['recommendation']}")

# 发布时间
best_time = optimization["publishing_tips"]["best_times"][0]
print(f"最佳发布时间: {best_time['time']} ({best_time['reason']})")
```

---

## 📝 示例完整流程

```python
import asyncio
from app.services.content.copywriting_generation import CopywritingGenerator
from app.db.session import SessionLocal

async def main():
    db = SessionLocal()
    generator = CopywritingGenerator(db=db)
    
    # 热点文章原始内容
    hot_title = "2026年AI技术将如何改变我们的生活"
    hot_content = """
    人工智能正在快速发展，深刻影响着我们的日常生活。从智能手机到自动驾驶，
    AI技术已经渗透到我们生活的方方面面...
    （完整文章内容）
    """
    
    # 方式1：自动触发（网络搜索失败时）
    result = generator.generate_script(
        platform="toutiao",
        topic="AI技术在2026年的应用",
        enable_web_search=True
    )
    
    # 方式2：手动提供热点文章
    result = generator.generate_script(
        platform="toutiao",
        topic="AI技术在2026年的应用",
        hot_article_title=hot_title,
        hot_article_content=hot_content
    )
    
    if result:
        print(f"✅ 文章生成成功")
        print(f"标题: {result['title']}")
        print(f"长度: {len(result['content'])}字")
        print(f"原创度: {result.get('smart_optimization', {}).get('originality_score', 'N/A')}")
        
        # 查看图片位置建议
        if result.get("image_suggestions"):
            print(f"\n📸 建议插入 {len(result['image_suggestions'])} 张图片:")
            for i, sug in enumerate(result["image_suggestions"], 1):
                print(f"  {i}. 第{sug['position'] + 1}段后 - {sug['theme']}")
        
        # 查看优化建议
        if result.get("smart_optimization"):
            opt = result["smart_optimization"]
            print(f"\n💡 优化建议:")
            if opt.get("title_optimization"):
                for sug in opt["title_optimization"]["suggestions"]:
                    print(f"  - {sug['recommendation']}")
    else:
        print("❌ 文章生成失败")
    
    db.close()

if __name__ == "__main__":
    asyncio.run(main())
```

---

## 🎉 总结

**热点文章二次创作功能**的核心优势：

✅ **智能降级**：网络搜索失败时自动启用  
✅ **深度分析**：多维度分析原文结构和内容  
✅ **高原创度**：6种改写策略组合使用  
✅ **智能配图**：基于内容分析推荐图片位置  
✅ **优化建议**：提供标题、结构、互动等多维度建议  
✅ **灵活可控**：支持3种改写深度，可自定义参数  

**适用场景**：
- 🔥 突发热点事件，需要快速出稿
- 📰 网络搜索受限，但有原文素材
- ✍️ 需要高原创度的深度解读文章
- 🎯 希望提升文章质量和互动率

---

**版本**: v1.0  
**更新日期**: 2026-05-12  
**作者**: Smart-Toolbox Team
