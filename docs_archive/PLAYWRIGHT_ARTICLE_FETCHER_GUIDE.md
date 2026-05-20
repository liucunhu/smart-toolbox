# Playwright 头条文章抓取功能说明

## 📋 功能概述

使用 Playwright 模拟真实浏览器访问今日头条，绕过反爬机制，抓取真实文章内容用于深度二次创作。

## 🎯 核心优势

### 1. 真实浏览器环境
- ✅ 使用 Edge 浏览器（与头条发布相同配置）
- ✅ 完整的 JavaScript 执行环境
- ✅ 自动处理动态加载内容
- ✅ 模拟真实用户行为（滚动、等待）

### 2. 智能内容提取
- ✅ 多策略标题提取（h1标签、meta标签等）
- ✅ 智能正文识别（article-content、article-body等）
- ✅ 自动过滤广告和无关元素
- ✅ 段落级文本提取（过滤短段落）

### 3. 容错机制
- ✅ 尝试多篇文章（默认3篇）
- ✅ 内容长度验证（>500字）
- ✅ 异常捕获和降级方案
- ✅ 详细的日志记录

## 🔧 技术实现

### 核心组件

#### ToutiaoArticleFetcher（头条文章抓取器）
**文件**: `app/services/content/toutiao_article_fetcher.py`

**主要方法**:
```python
async def search_and_fetch_article(
    keyword: str,
    max_results: int = 3
) -> Optional[Dict]:
    """搜索关键词并抓取第一篇文章内容"""
    
async def _extract_article_urls(max_count: int) -> List[str]:
    """从搜索结果中提取文章URL"""
    
async def _fetch_single_article(url: str) -> Optional[Dict]:
    """抓取单篇文章的完整内容"""
```

**返回数据结构**:
```python
{
    "title": "文章标题",
    "content": "文章完整内容（段落用\\n\\n分隔）",
    "author": "作者名",
    "publish_date": "发布日期",
    "url": "文章URL"
}
```

### 工作流程

```
输入热点关键词
    ↓
初始化 Playwright 浏览器（Edge）
    ↓
访问头条搜索页面
https://www.toutiao.com/search/?keyword={关键词}
    ↓
等待页面加载（3秒）
    ↓
提取搜索结果中的文章链接
（多选择器策略，最多3个）
    ↓
逐个尝试抓取文章内容
    ├─ 访问文章页面
    ├─ 等待加载（3秒）
    ├─ 滚动页面触发懒加载
    ├─ 提取标题、正文、作者、时间
    └─ 验证内容长度（>500字）
    ↓
返回第一篇成功抓取的文章
    ↓
关闭浏览器
```

### 内容提取策略

#### 标题提取（优先级从高到低）
1. `h1.article-title`
2. `h1.title`
3. `[class*="title"]`
4. `meta[property="og:title"]`

#### 正文提取（优先级从高到低）
1. `.article-content`
2. `.article-body`
3. `[class*="article-content"]`
4. `#article-content`
5. `article` 标签
6. `.post-content`

**清理步骤**:
- 移除 `<script>`、`<style>` 标签
- 移除导航、页眉、页脚
- 移除广告元素（`.ad`、`.advertisement`）
- 只保留长度>20字的段落

#### 作者提取
1. `.author-name`
2. `[class*="author"]`
3. `meta[name="author"]`

#### 发布时间提取
1. `.publish-time`
2. `time` 标签
3. `[class*="time"]`
4. `meta[property="article:published_time"]`

## 📊 集成到工作流

### WebSearchService 增强

**文件**: `app/services/content/web_search.py`

**修改位置**: 策略4 - 头条热搜获取后

**新增流程**:
```python
# 1. 获取头条热搜
hot_topics = injector.fetch_hot_topics("toutiao", num_results)

# 2. 选择热度最高的话题
best_topic = max(hot_topics, key=lambda x: x.get("heat", 0))

# 3. 使用 Playwright 抓取真实文章
hot_article_data = await fetch_toutiao_article(topic_keyword, max_results=3)

# 4. 如果抓取成功，进行深度二次创作
if hot_article_data:
    rewrite_result = await rewriter.rewrite_from_hot_article(
        hot_article_content=hot_article_data["content"],
        hot_article_title=hot_article_data["title"],
        target_platform="toutiao",
        rewrite_depth="deep"
    )
    
    # 5. 将二次创作结果优先使用
    results.insert(0, {
        "title": rewrite_result["new_title"],
        "snippet": rewrite_result["content"],
        "source": "hot_article_deep_rewrite",
        "originality_score": rewrite_result["originality_score"]
    })
```

### 三级降级机制

```
级别1: Playwright 抓取真实文章 + HotArticleRewriter 深度二创
  ↓ 失败
级别2: 直接使用抓取的原文（不二次创作）
  ↓ 失败
级别3: LLM 基于热点话题生成原创内容
```

## 🚀 使用示例

### 独立使用

```python
from app.services.content.toutiao_article_fetcher import fetch_toutiao_article

# 抓取文章
article = await fetch_toutiao_article("4月汽车销量", max_results=3)

if article:
    print(f"标题: {article['title']}")
    print(f"作者: {article['author']}")
    print(f"长度: {len(article['content'])}字")
    print(f"URL: {article['url']}")
else:
    print("抓取失败")
```

### 在自动发布中使用

```python
# 自动发布流程中会自动调用
# 无需手动干预，系统会在网络搜索失败时自动触发

# 日志示例：
# 2026-05-13 10:34:13 | INFO | 🔄 检测到头条热搜，尝试深度二次创作...
# 2026-05-13 10:34:13 | INFO |    📰 选择热搜话题进行二次创作: 4月汽车销量前十名仅剩一款油车
# 2026-05-13 10:34:13 | INFO |    🔍 正在使用 Playwright 抓取真实文章...
# 2026-05-13 10:34:25 | INFO | ✅ 成功抓取真实文章
# 2026-05-13 10:34:25 | INFO |    标题: 4月销量榜大洗牌...
# 2026-05-13 10:34:25 | INFO |    长度: 2345字
# 2026-05-13 10:34:25 | INFO |    🔄 开始深度二次创作...
# 2026-05-13 10:34:30 | INFO | ✅ 热点文章二次创作成功
# 2026-05-13 10:34:30 | INFO |    原创度: 87%
# 2026-05-13 10:34:30 | INFO |    新标题: 燃油车时代终结？...
```

## ⚙️ 配置说明

### 浏览器配置

```python
# 使用 Edge 浏览器（与头条发布一致）
edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"

# 启动参数
args=[
    '--disable-blink-features=AutomationControlled',  # 隐藏自动化特征
    '--no-sandbox',
    '--disable-setuid-sandbox'
]

# 浏览器上下文
viewport={"width": 1920, "height": 1080}
user_agent="Mozilla/5.0 ..."
locale="zh-CN"
timezone_id="Asia/Shanghai"
```

### 超时设置

- 页面加载超时: 30秒
- 初始等待: 3秒
- 滚动后等待: 2秒 × 2次

### 内容验证

- 最小内容长度: 500字
- 最小段落长度: 20字
- 最大标题长度: 100字

## 🐛 常见问题

### Q1: 抓取失败怎么办？

**A**: 系统有三级降级机制：
1. 尝试多篇不同文章（默认3篇）
2. 降级为直接使用原文
3. 最终降级为LLM生成

### Q2: 为什么有时抓取不到内容？

**可能原因**:
- 头条更新了页面结构
- 需要登录才能查看完整内容
- 反爬机制升级

**解决方案**:
- 检查日志中的错误信息
- 更新选择器策略
- 考虑添加 Cookie 支持

### Q3: 如何调试抓取过程？

**A**: 
1. 设置 `headless=False` 查看浏览器操作
2. 检查日志中的详细步骤
3. 使用截图功能保存页面状态

```python
# 调试模式
await self.page.screenshot(path="debug_search.png")
await self.page.screenshot(path="debug_article.png")
```

### Q4: 性能如何？

**耗时分析**:
- 浏览器初始化: ~2秒
- 搜索页面加载: ~5秒
- 文章页面加载: ~5秒 × 3篇 = 15秒
- 内容提取: ~1秒
- **总计**: ~23秒（最坏情况）

**优化建议**:
- 复用浏览器实例（当前每次新建）
- 并行抓取多篇文章
- 缓存已抓取的文章

## 🔮 后续优化方向

### 短期（1-2周）
1. **浏览器复用**: 创建浏览器池，避免重复初始化
2. **Cookie 支持**: 使用已登录的 Cookie 获取更多内容
3. **并发抓取**: 同时抓取多篇文章，提升速度

### 中期（1个月）
4. **智能重试**: 根据失败原因自动调整策略
5. **内容去重**: 避免抓取相似内容
6. **质量评分**: 评估文章质量，优先抓取高质量文章

### 长期（3个月）
7. **多平台支持**: 扩展至微信公众号、知乎等平台
8. **AI 辅助**: 使用 AI 判断文章相关性和质量
9. **分布式抓取**: 支持大规模文章抓取任务

## 📝 相关文件清单

### 新增文件
- `app/services/content/toutiao_article_fetcher.py` - 头条文章抓取器
- `docs_archive/PLAYWRIGHT_ARTICLE_FETCHER_GUIDE.md` - 本文档

### 修改文件
- `app/services/content/web_search.py` - 集成文章抓取功能

### 依赖文件（已存在）
- `app/services/content/hot_article_rewriter.py` - 热点文章二次创作引擎
- `app/services/content/hot_trend_injector.py` - 头条热搜获取

## ✅ 测试建议

### 单元测试
```python
import pytest
from app.services.content.toutiao_article_fetcher import fetch_toutiao_article

@pytest.mark.asyncio
async def test_fetch_article():
    """测试文章抓取"""
    article = await fetch_toutiao_article("AI技术", max_results=1)
    
    assert article is not None
    assert len(article["title"]) > 0
    assert len(article["content"]) > 500
    assert "url" in article
```

### 集成测试
1. 运行自动发布流程
2. 观察日志中的抓取步骤
3. 验证生成的文章质量
4. 检查原创度评分

### 性能测试
1. 测量单次抓取耗时
2. 测试连续多次抓取的稳定性
3. 监控内存使用情况

---

**最后更新**: 2026-05-13  
**版本**: v1.0  
**作者**: Smart-Toolbox Team
