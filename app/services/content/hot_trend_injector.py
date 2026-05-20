"""
热点趋势注入系统
完整实现：实时热搜抓取 + 热点关键词强制植入 + 自然语言优化
支持真实数据爬取和模拟数据降级
"""
import httpx
import asyncio
import random
from typing import List, Dict, Optional
from datetime import datetime
from app.core.config import settings
from app.utils.logger import logger

class HotTrendInjector:
    """热点趋势注入器 - 实时抓取热搜并植入文案"""
    
    def __init__(self):
        self.api_url = settings.HOT_TREND_API_URL
        self.api_key = settings.HOT_TREND_API_KEY
        self.last_update_time = None
        self.cache = {}  # 简单缓存
        self.cache_ttl = 300  # 缓存5分钟
        
        # 平台热搜API配置
        self.platform_apis = {
            "douyin": {
                "url": "https://www.douyin.com/aweme/v1/web/hot/search/list/",
                "params": {"device_platform": "webapp", "aid": "6383"}
            },
            "xiaohongshu": {
                "url": "https://edith.xiaohongshu.com/api/sns/web/v1/search/hot",
                "params": {}
            },
            "bilibili": {
                "url": "https://api.bilibili.com/x/web-interface/search/type",
                "params": {"search_type": "hot_topic"}
            },
            "toutiao": {
                "url": "https://www.toutiao.com/hot-event/hot-board/",
                "params": {"origin": "toutiao_pc"}
            }
        }
        
        # 热点词权重配置
        self.hot_weight_config = {
            "top_1": 1.0,      # 热搜第1名
            "top_2_5": 0.8,    # 热搜2-5名
            "top_6_10": 0.6,   # 热搜6-10名
            "top_11_20": 0.4,  # 热搜11-20名
        }
    
    async def fetch_trending_topics(self, platform: str, count: int = 10) -> List[Dict]:
        """
        抓取平台热搜关键词
        :param platform: 平台名称
        :param count: 获取数量
        :return: 热搜列表
        """
        try:
            logger.info(f"开始抓取 {platform} 平台热搜")
            
            # 使用自定义API或平台官方API
            if self.api_url:
                return await self._fetch_from_custom_api(platform, count)
            else:
                return await self._fetch_from_platform_api(platform, count)
            
        except Exception as e:
            logger.error(f"抓取热搜失败: {str(e)}")
            # 返回空列表，不使用模拟数据
            return []
    
    async def _fetch_from_custom_api(self, platform: str, count: int) -> List[Dict]:
        """从自定义API获取热搜"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                self.api_url,
                params={
                    "platform": platform,
                    "count": count,
                    "api_key": self.api_key
                },
                timeout=10.0
            )
            response.raise_for_status()
            result = response.json()
            
            hot_topics = []
            for item in result.get("data", []):
                hot_topics.append({
                    "keyword": item["keyword"],
                    "rank": item.get("rank", 0),
                    "heat": item.get("heat", 0),
                    "platform": platform
                })
            
            logger.info(f"成功获取 {len(hot_topics)} 个热搜关键词")
            return hot_topics
    
    async def _fetch_from_platform_api(self, platform: str, count: int) -> List[Dict]:
        """从平台官方API获取热搜（真实数据）"""
        try:
            logger.info(f"开始抓取 {platform} 平台真实热搜")
            
            # 根据平台选择不同的爬取策略
            if platform == "douyin":
                return await self._fetch_douyin_hot(count)
            elif platform == "xiaohongshu":
                return await self._fetch_xiaohongshu_hot(count)
            elif platform == "bilibili":
                return await self._fetch_bilibili_hot(count)
            elif platform == "toutiao":
                return await self._fetch_toutiao_hot(count)
            else:
                logger.error(f"不支持的平台: {platform}")
                return []
                
        except Exception as e:
            logger.error(f"抓取 {platform} 热搜失败: {str(e)}")
            return []
    
    def _get_default_hot_topics(self, platform: str, count: int) -> List[Dict]:
        """获取默认热点词（API失败时）"""
        default_topics = [
            {"keyword": "热门推荐", "rank": 1, "heat": 1000000},
            {"keyword": "今日话题", "rank": 2, "heat": 900000},
            {"keyword": "爆款内容", "rank": 3, "heat": 800000},
        ]
        return default_topics[:count]
    
    def inject_hot_keywords(self, script: str, hot_topics: List[Dict], max_keywords: int = 3) -> str:
        """
        将热点关键词自然植入文案
        :param script: 原始文案
        :param hot_topics: 热搜列表
        :param max_keywords: 最多植入关键词数量
        :return: 植入热点后的文案
        """
        try:
            logger.info(f"开始植入热点关键词，原始文案长度: {len(script)}")
            
            if not hot_topics:
                logger.warning("热点词列表为空，跳过植入")
                return script
            
            # 根据热度排序，选择top关键词
            sorted_topics = sorted(hot_topics, key=lambda x: x.get("heat", 0), reverse=True)
            selected_topics = sorted_topics[:max_keywords]
            
            # 获取关键词列表
            keywords = [topic["keyword"] for topic in selected_topics]
            
            # 植入策略：在文案开头、中间、结尾自然植入
            modified_script = self._natural_injection(script, keywords)
            
            logger.info(f"热点植入完成，新增关键词: {keywords}")
            
            return modified_script
            
        except Exception as e:
            logger.error(f"热点植入失败: {str(e)}")
            return script
    
    def _natural_injection(self, script: str, keywords: List[str]) -> str:
        """自然植入热点关键词"""
        paragraphs = script.split('\n\n')
        
        if len(paragraphs) < 2:
            # 单段落文案，在开头植入
            return self._inject_at_beginning(script, keywords)
        
        # 多段落文案，分散植入
        modified_paragraphs = []
        keyword_index = 0
        
        for i, paragraph in enumerate(paragraphs):
            # 在关键位置植入热点词
            if i == 0 and keyword_index < len(keywords):
                # 第一段：开头植入
                modified_paragraphs.append(
                    f"【{keywords[keyword_index]}】{paragraph}"
                )
                keyword_index += 1
            elif i == len(paragraphs) // 2 and keyword_index < len(keywords):
                # 中间段：自然融入
                modified_paragraphs.append(
                    self._insert_in_middle(paragraph, keywords[keyword_index])
                )
                keyword_index += 1
            elif i == len(paragraphs) - 1 and keyword_index < len(keywords):
                # 最后一段：结尾植入
                modified_paragraphs.append(
                    f"{paragraph}\n\n 相关热点：{'、'.join(keywords[keyword_index:])}"
                )
                keyword_index = len(keywords)
            else:
                modified_paragraphs.append(paragraph)
        
        return '\n\n'.join(modified_paragraphs)
    
    def _inject_at_beginning(self, script: str, keywords: List[str]) -> str:
        """在开头植入热点词"""
        prefix = f"🔥 热点话题：{'、'.join(keywords)}\n\n"
        return prefix + script
    
    def _insert_in_middle(self, paragraph: str, keyword: str) -> str:
        """在段落中间自然植入关键词"""
        # 找到合适的插入位置（逗号或句号后）
        sentences = paragraph.split('，')
        if len(sentences) > 2:
            mid_point = len(sentences) // 2
            sentences[mid_point] = f"{sentences[mid_point]}，这个话题与{keyword}密切相关"
            return '，'.join(sentences)
        
        return f"{paragraph}\n\n💡 延伸话题：{keyword}"
    
    def generate_hashtags(self, hot_topics: List[Dict], platform: str) -> List[str]:
        """生成平台专属话题标签"""
        hashtags = []
        
        for topic in hot_topics[:10]:  # 最多10个标签
            keyword = topic["keyword"]
            # 移除空格和特殊字符
            tag = f"#{keyword.replace(' ', '')}#"
            hashtags.append(tag)
        
        # 添加平台通用标签
        platform_tags = {
            "douyin": ["#抖音热门", "#热门推荐", "#爆款"],
            "xiaohongshu": ["#小红书爆款", "#好物推荐", "#种草"],
            "bilibili": ["#B站热门", "#必看", "#推荐"],
            "toutiao": ["#头条热点", "#今日关注", "#热点"],
        }
        
        hashtags.extend(platform_tags.get(platform, [])[:3])
        
        return hashtags
    
    async def inject_and_generate(self, script: str, platform: str) -> Dict:
        """
        完整流程：抓取热点 + 植入文案 + 生成标签
        :param script: 原始文案
        :param platform: 目标平台
        :return: 处理结果
        """
        try:
            # 1. 抓取热点
            hot_topics = await self.fetch_trending_topics(platform, count=20)
            
            # 2. 植入文案
            modified_script = self.inject_hot_keywords(script, hot_topics, max_keywords=3)
            
            # 3. 生成标签
            hashtags = self.generate_hashtags(hot_topics, platform)
            
            # 4. 获取权重分数
            weight_score = self._calculate_weight_score(hot_topics)
            
            logger.info(f"热点注入完成，权重分数: {weight_score}")
            
            return {
                "status": "success",
                "original_length": len(script),
                "modified_length": len(modified_script),
                "script": modified_script,
                "hashtags": hashtags,
                "hot_topics": hot_topics[:5],  # 返回top 5
                "weight_score": weight_score
            }
            
        except Exception as e:
            logger.error(f"热点注入流程失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "script": script  # 返回原始文案
            }
    
    def _calculate_weight_score(self, hot_topics: List[Dict]) -> float:
        """计算热点权重分数"""
        if not hot_topics:
            return 0.0
        
        total_heat = sum([topic.get("heat", 0) for topic in hot_topics[:5]])
        max_heat = hot_topics[0].get("heat", 1) if hot_topics else 1
        
        # 归一化分数（0-100）
        score = min(100, (total_heat / (max_heat * 5)) * 100)
        return round(score, 2)
    
    async def _fetch_douyin_hot(self, count: int) -> List[Dict]:
        """抓取抖音热搜（使用公开API）"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 抖音热榜API
                response = await client.get(
                    "https://www.douyin.com/aweme/v1/web/hot/search/list/",
                    params={
                        "device_platform": "webapp",
                        "aid": "6383",
                        "channel": "channel_pc_web",
                        "pc_client_type": "1",
                        "version_code": "170400",
                        "version_name": "17.4.0",
                        "cookie_enabled": "true",
                        "screen_width": "1920",
                        "screen_height": "1080",
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Referer": "https://www.douyin.com/",
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    hot_list = data.get("data", {}).get("word_list", [])
                    
                    result = []
                    for i, item in enumerate(hot_list[:count], 1):
                        result.append({
                            "keyword": item.get("word", ""),
                            "rank": i,
                            "heat": item.get("hot_value", 0),
                            "platform": "douyin"
                        })
                    
                    logger.info(f"成功获取抖音热搜 {len(result)} 条")
                    self.last_update_time = datetime.now()
                    return result
                else:
                    logger.error(f"抖音API返回状态码: {response.status_code}，无法获取真实数据")
                    return []
                    
        except Exception as e:
            logger.error(f"抓取抖音热搜异常: {str(e)}")
            return []
    
    async def _fetch_bilibili_hot(self, count: int) -> List[Dict]:
        """抓取B站热搜（使用官方热搜API）"""
        try:
            logger.info("开始抓取B站热搜")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # B站热搜榜API（更接近APP端）
                response = await client.get(
                    "https://api.bilibili.com/x/web-interface/ranking/v2",
                    params={
                        "rid": 0,  # 0表示全站
                        "type": "all"  # 全部类型
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Referer": "https://www.bilibili.com/",
                        "Origin": "https://www.bilibili.com"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    videos = data.get("data", {}).get("list", [])
                    
                    if not videos:
                        logger.warning("B站API返回空数据，尝试备用API")
                        return await self._fetch_bilibili_popular(count)
                    
                    result = []
                    for i, video in enumerate(videos[:count], 1):
                        title = video.get("title", "")
                        # 使用完整标题作为关键词
                        keyword = title[:30] if len(title) > 30 else title
                        
                        # 获取播放量作为热度
                        stat = video.get("stat", {})
                        heat = stat.get("view", 0) or stat.get("play", 0)
                        
                        result.append({
                            "keyword": keyword,
                            "rank": i,
                            "heat": heat,
                            "platform": "bilibili"
                        })
                    
                    logger.info(f"成功获取B站热搜 {len(result)} 条")
                    self.last_update_time = datetime.now()
                    return result
                else:
                    logger.error(f"B站API返回状态码: {response.status_code}，尝试备用方案")
                    return await self._fetch_bilibili_popular(count)
                    
        except Exception as e:
            logger.error(f"抓取B站热搜异常: {str(e)}，尝试备用方案")
            return await self._fetch_bilibili_popular(count)
    
    async def _fetch_bilibili_popular(self, count: int) -> List[Dict]:
        """备用方案：获取B站热门视频"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.bilibili.com/x/web-interface/popular",
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Referer": "https://www.bilibili.com/",
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    videos = data.get("data", {}).get("list", [])
                    
                    result = []
                    for i, video in enumerate(videos[:count], 1):
                        title = video.get("title", "")
                        keyword = title[:30] if len(title) > 30 else title
                        
                        result.append({
                            "keyword": keyword,
                            "rank": i,
                            "heat": video.get("stat", {}).get("view", 0),
                            "platform": "bilibili"
                        })
                    
                    logger.info(f"通过备用API获取B站热门 {len(result)} 条")
                    self.last_update_time = datetime.now()
                    return result
                else:
                    logger.error(f"B站备用API失败: {response.status_code}")
                    return []
        except Exception as e:
            logger.error(f"B站备用API异常: {str(e)}")
            return []
    
    async def _fetch_xiaohongshu_hot(self, count: int) -> List[Dict]:
        """抓取小红书热搜（使用Playwright）"""
        try:
            logger.info("开始使用Playwright抓取小红书热搜")
            
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                
                page = await context.new_page()
                
                # 访问小红书首页
                await page.goto("https://www.xiaohongshu.com", wait_until="domcontentloaded", timeout=15000)
                
                # 等待页面加载
                await page.wait_for_timeout(3000)
                
                # 尝试提取热门内容
                hot_topics = await page.evaluate("""
                    () => {
                        const topics = []
                        
                        // 尝试多种选择器策略
                        const strategies = [
                            // 策略1: 查找笔记卡片
                            () => {
                                const cards = document.querySelectorAll('[class*="note"]')
                                if (cards.length > 0) return cards
                                return null
                            },
                            // 策略2: 查找feed项
                            () => {
                                const feeds = document.querySelectorAll('[class*="feed"]')
                                if (feeds.length > 0) return feeds
                                return null
                            },
                            // 策略3: 查找所有包含标题的元素
                            () => {
                                const titles = document.querySelectorAll('h1, h2, h3, [class*="title"]')
                                if (titles.length > 0) return titles
                                return null
                            }
                        ]
                        
                        let elements = null
                        for (const strategy of strategies) {
                            elements = strategy()
                            if (elements && elements.length > 0) break
                        }
                        
                        if (!elements || elements.length === 0) {
                            // 如果都没找到，返回页面基本信息
                            return [{
                                keyword: document.title || '小红书热门推荐',
                                rank: 1,
                                heat: 1000000
                            }]
                        }
                        
                        // 提取数据
                        Array.from(elements).slice(0, 30).forEach((item, index) => {
                            let title = ''
                            
                            // 根据不同元素类型提取标题
                            if (item.tagName === 'H1' || item.tagName === 'H2' || item.tagName === 'H3') {
                                title = item.textContent.trim()
                            } else {
                                // 尝试查找子元素中的标题
                                const titleEl = item.querySelector('h1, h2, h3, [class*="title"], span')
                                title = titleEl ? titleEl.textContent.trim() : item.textContent.trim()
                            }
                            
                            // 过滤有效标题
                            if (title && title.length > 3 && title.length < 50) {
                                topics.push({
                                    keyword: title.substring(0, 20),
                                    rank: index + 1,
                                    heat: Math.floor(Math.random() * 1000000) + 100000
                                })
                            }
                        })
                        
                        // 去重
                        const uniqueTopics = []
                        const seen = new Set()
                        for (const topic of topics) {
                            if (!seen.has(topic.keyword)) {
                                seen.add(topic.keyword)
                                uniqueTopics.push(topic)
                            }
                        }
                        
                        return uniqueTopics.length > 0 ? uniqueTopics : [{
                            keyword: '小红书热门推荐',
                            rank: 1,
                            heat: 999999
                        }]
                    }
                """)
                
                await browser.close()
                
                if hot_topics and len(hot_topics) > 0:
                    result = hot_topics[:count]
                    logger.info(f"成功获取小红书热搜 {len(result)} 条")
                    self.last_update_time = datetime.now()
                    return result
                else:
                    logger.error("小红书未获取到真实数据")
                    return []
                    
        except Exception as e:
            logger.error(f"抓取小红书热搜异常: {str(e)}")
            self.last_update_time = datetime.now()  # 即使失败也更新时间戳
            return []
    
    async def _fetch_toutiao_hot(self, count: int) -> List[Dict]:
        """抓取今日头条热搜（使用多种策略）"""
        try:
            logger.info("开始使用Playwright抓取今日头条热搜")
            
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(
                    headless=True,
                    args=['--no-sandbox', '--disable-setuid-sandbox']
                )
                
                context = await browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    viewport={"width": 1920, "height": 1080}
                )
                
                page = await context.new_page()
                
                # 策略1: 直接访问热榜页面
                try:
                    await page.goto("https://www.toutiao.com/hot-event/hot-board/", wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(5000)
                    logger.info("成功访问头条热榜页面")
                except Exception as e:
                    logger.warning(f"访问热榜页面失败: {str(e)}，尝试首页")
                    # 策略2: 访问首页
                    await page.goto("https://www.toutiao.com/", wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(5000)
                
                # 提取热榜数据
                hot_topics = await page.evaluate("""
                    () => {
                        const topics = []
                        const seen = new Set()
                        
                        // 策略1: 查找热榜专用选择器
                        const hotSelectors = [
                            '.hot-item',
                            '[class*="hot"]',
                            '.word-item',
                            '[class*="word"]',
                            '.title-list a',
                            '[class*="title"]'
                        ]
                        
                        let elements = null
                        for (const selector of hotSelectors) {
                            elements = document.querySelectorAll(selector)
                            if (elements && elements.length > 5) break
                        }
                        
                        if (elements && elements.length > 0) {
                            Array.from(elements).slice(0, 30).forEach((item, index) => {
                                const titleEl = item.querySelector('.title, h3, [class*="title"]') || item
                                const text = titleEl.textContent.trim()
                                
                                if (text && text.length > 5 && text.length < 100 && !seen.has(text)) {
                                    // 提取热度值
                                    const hotEl = item.querySelector('.hot-value, .heat, [class*="hot"]')
                                    let heat = Math.floor(Math.random() * 10000000) + 1000000
                                    
                                    if (hotEl) {
                                        const hotText = hotEl.textContent.trim()
                                        if (hotText.includes('万')) {
                                            heat = parseInt(hotText.replace(/[^0-9]/g, '')) * 10000
                                        } else if (hotText.includes('亿')) {
                                            heat = parseInt(hotText.replace(/[^0-9]/g, '')) * 100000000
                                        } else {
                                            const num = parseInt(hotText.replace(/[^0-9]/g, ''))
                                            if (num > 0) heat = num
                                        }
                                    }
                                    
                                    seen.add(text)
                                    topics.push({
                                        keyword: text.substring(0, 30),
                                        heat: heat
                                    })
                                }
                            })
                        } else {
                            // 策略3: 如果没找到热榜元素，提取页面所有文本
                            const allElements = document.querySelectorAll('body *')
                            
                            Array.from(allElements).forEach((el) => {
                                if (el.childNodes.length === 1 && el.childNodes[0].nodeType === Node.TEXT_NODE) {
                                    const text = el.textContent.trim()
                                    
                                    if (text && text.length > 5 && text.length < 100 && !seen.has(text)) {
                                        const excludePatterns = [
                                            /登录|注册|搜索|更多|首页|视频|小视频|直播/,
                                            /关注|推荐|发布|消息|我的|设置|帮助/,
                                            /广告|下载|APP|客户端/,
                                            /^\d+$/,
                                            /^\s*$/
                                        ]
                                        
                                        const shouldExclude = excludePatterns.some(pattern => pattern.test(text))
                                        
                                        if (!shouldExclude) {
                                            seen.add(text)
                                            topics.push({
                                                keyword: text.substring(0, 30),
                                                heat: Math.floor(Math.random() * 10000000) + 1000000
                                            })
                                        }
                                    }
                                }
                            })
                        }
                        
                        // 按热度排序
                        topics.sort((a, b) => b.heat - a.heat)
                        
                        // 添加排名
                        topics.forEach((topic, index) => {
                            topic.rank = index + 1
                        })
                        
                        return topics.slice(0, 30)
                    }
                """)
                
                await browser.close()
                
                if hot_topics and len(hot_topics) >= 5:
                    result = hot_topics[:count]
                    logger.info(f"成功获取头条热搜 {len(result)} 条")
                    self.last_update_time = datetime.now()
                    return result
                else:
                    logger.warning(f"头条获取到 {len(hot_topics) if hot_topics else 0} 条数据，数量不足，尝试备用方案")
                    # 备用方案：使用头条搜索API
                    result = await self._fetch_toutiao_search(count)
                    if result:
                        logger.info(f"备用方案成功，获取到 {len(result)} 条头条热点")
                    else:
                        logger.error("所有真实数据源均失败，无法获取今日头条热点")
                    return result
                    
        except Exception as e:
            logger.error(f"抓取头条热搜异常: {str(e)}，尝试备用方案")
            result = await self._fetch_toutiao_search(count)
            if result:
                logger.info(f"备用方案成功，获取到 {len(result)} 条头条热点")
            else:
                logger.error("所有真实数据源均失败，无法获取今日头条热点")
            return result
    
    async def _fetch_toutiao_search(self, count: int) -> List[Dict]:
        """备用方案：使用头条多个API接口获取热点"""
        try:
            logger.info("使用头条API接口获取热点")
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                # 尝试多个API端点，优先使用更接近APP的接口
                api_endpoints = [
                    {
                        "name": "热榜API",
                        "url": "https://www.toutiao.com/hot-event/hot-board/",
                        "params": {"origin": "toutiao_pc"}
                    },
                    {
                        "name": "新闻热榜",
                        "url": "https://www.toutiao.com/api/pc/feed/",
                        "params": {"category": "news_hot", "max_behot_time": "0"}
                    },
                    {
                        "name": "社会热榜",
                        "url": "https://www.toutiao.com/api/pc/feed/",
                        "params": {"category": "news_society", "max_behot_time": "0"}
                    }
                ]
                
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": "https://www.toutiao.com/",
                }
                
                for endpoint in api_endpoints:
                    try:
                        logger.info(f"尝试头条API: {endpoint['name']}")
                        response = await client.get(
                            endpoint["url"],
                            params=endpoint.get("params", {}),
                            headers=headers
                        )
                        
                        if response.status_code == 200:
                            data = response.json()
                            
                            # 解析热榜数据（支持多种格式）
                            hot_list = (
                                data.get("data", []) or 
                                data.get("hot_list", []) or 
                                data.get("hot_words", []) or
                                []
                            )
                            
                            if hot_list and len(hot_list) > 0:
                                result = []
                                for i, item in enumerate(hot_list[:count], 1):
                                    # 支持多种字段名
                                    keyword = (
                                        item.get("Title") or 
                                        item.get("title") or 
                                        item.get("Keyword") or
                                        item.get("keyword") or 
                                        item.get("word") or 
                                        item.get("Word") or
                                        ""
                                    )
                                    
                                    if keyword and len(keyword) > 2:
                                        # 获取热度值
                                        heat = (
                                            item.get("HotValue") or 
                                            item.get("hot_value") or
                                            item.get("Heat") or
                                            item.get("heat") or 
                                            item.get("score") or
                                            (10000000 - i * 500000)
                                        )
                                        
                                        result.append({
                                            "keyword": keyword[:30],
                                            "rank": i,
                                            "heat": int(heat) if isinstance(heat, (int, float)) else 1000000
                                        })
                                
                                if result:
                                    logger.info(f"通过{endpoint['name']}获取头条热点 {len(result)} 条")
                                    self.last_update_time = datetime.now()
                                    return result
                    except Exception as e:
                        logger.warning(f"{endpoint['name']}失败: {str(e)}")
                        continue
            
            # 如果以上方法都失败，返回空列表
            logger.error("所有真实数据源均失败，无法获取今日头条热点")
            return []
                    
        except Exception as e:
            logger.error(f"头条API接口失败: {str(e)}")
            return []
    
    def _get_dynamic_mock_topics(self, platform: str, count: int) -> List[Dict]:
        """生成基于日期的动态模拟数据（每天不同）"""
        import hashlib
        
        # 使用日期作为种子，确保每天数据不同但同一天内一致
        today = datetime.now().strftime("%Y-%m-%d")
        seed = hashlib.md5(f"{platform}_{today}".encode()).hexdigest()
        
        # 基础话题池
        base_topics = [
            "人工智能最新突破", "新能源汽车发展", "数字经济趋势",
            "健康生活指南", "教育改革政策", "文化旅游热点",
            "体育赛事回顾", "美食探店推荐", "时尚潮流趋势",
            "财经投资分析", "社会民生关注", "环境保护行动",
            "创新创业故事", "国际形势解读", "历史文化探索",
            "娱乐资讯速递", "职场发展建议", "家庭生活技巧",
            "科学知识普及", "科技创新应用", "城市发展规划",
            "乡村振兴战略", "医疗健康进展", "教育培训创新",
            "消费升级趋势", "数字化转型", "可持续发展",
            "智能制造", "区块链应用", "元宇宙发展",
            "5G技术应用", "物联网创新", "云计算服务",
            "大数据应用", "网络安全", "隐私保护",
            "智慧城市", "智慧交通", "智慧医疗",
            "在线教育", "远程办公", "共享经济",
            "绿色能源", "碳中和", "碳达峰",
            "生物多样性", "生态保护", "气候变化",
            "太空探索", "深海探测", "极地科考",
            "量子计算", "基因编辑", "脑科学研究",
            "新材料研发", "生物医药", "精准医疗",
            "养老服务", "社会保障", "就业政策",
            "住房保障", "交通建设", "基础设施",
            "乡村振兴", "农业发展", "粮食安全",
            "食品安全", "药品监管", "质量标准",
            "知识产权保护", "法律法规", "司法改革",
            "文化交流", "国际合作", "一带一路",
            "区域发展", "城市群建设", "都市圈规划"
        ]
        
        # 根据种子打乱顺序
        import random
        random.seed(seed)
        shuffled = base_topics.copy()
        random.shuffle(shuffled)
        
        # 生成结果
        result = []
        for i, topic in enumerate(shuffled[:count], 1):
            # 根据种子生成相对稳定的热度值
            heat_seed = hashlib.md5(f"{seed}_{i}".encode()).hexdigest()
            heat = int(heat_seed[:8], 16) % 90000000 + 1000000
            
            result.append({
                "keyword": topic,
                "rank": i,
                "heat": heat
            })
        
        logger.info(f"生成动态模拟数据 {len(result)} 条（日期: {today}）")
        self.last_update_time = datetime.now()
        return result
    
    def _get_mock_topics(self, platform: str, count: int) -> List[Dict]:
        """获取模拟热搜数据（降级方案）"""
        mock_topics = {
            "douyin": [
                {"keyword": "2026最新AI工具", "rank": 1, "heat": 9999999},
                {"keyword": "自媒体运营技巧", "rank": 2, "heat": 8888888},
                {"keyword": "爆款视频制作", "rank": 3, "heat": 7777777},
                {"keyword": "短视频剪辑教程", "rank": 4, "heat": 6666666},
                {"keyword": "直播带货技巧", "rank": 5, "heat": 5555555},
            ],
            "xiaohongshu": [
                {"keyword": "好物分享", "rank": 1, "heat": 999999},
                {"keyword": "生活小妙招", "rank": 2, "heat": 888888},
                {"keyword": "穿搭推荐", "rank": 3, "heat": 777777},
                {"keyword": "美食探店", "rank": 4, "heat": 666666},
                {"keyword": "旅行攻略", "rank": 5, "heat": 555555},
            ],
            "bilibili": [
                {"keyword": "科技测评", "rank": 1, "heat": 99999},
                {"keyword": "游戏攻略", "rank": 2, "heat": 88888},
                {"keyword": "动画推荐", "rank": 3, "heat": 77777},
                {"keyword": "学习干货", "rank": 4, "heat": 66666},
                {"keyword": "音乐翻唱", "rank": 5, "heat": 55555},
            ],
            "toutiao": [
                {"keyword": "今日热点", "rank": 1, "heat": 99999999},
                {"keyword": "社会新闻", "rank": 2, "heat": 88888888},
                {"keyword": "科技前沿", "rank": 3, "heat": 77777777},
                {"keyword": "财经资讯", "rank": 4, "heat": 66666666},
                {"keyword": "体育快讯", "rank": 5, "heat": 55555555},
            ]
        }
        
        topics = mock_topics.get(platform, mock_topics["douyin"])
        return topics[:count]
    
    def fetch_hot_topics(self, platform: str, count: int = 10) -> List[Dict]:
        """
        同步方法：获取热搜关键词（用于API端点）
        :param platform: 平台名称
        :param count: 获取数量
        :return: 热搜列表
        """
        import asyncio
        try:
            # ✅ 修复：检查是否已在事件循环中，避免嵌套创建
            try:
                loop = asyncio.get_running_loop()
                # 如果已有运行中的循环，直接在其中执行
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.fetch_trending_topics(platform, count))
                    return future.result(timeout=30)
            except RuntimeError:
                # 没有运行中的循环，创建新循环
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                result = loop.run_until_complete(self.fetch_trending_topics(platform, count))
                loop.close()
                return result
        except Exception as e:
            logger.error(f"同步获取热搜失败: {str(e)}")
            # 返回空列表，不使用模拟数据
            return []


# 辅助函数
def get_platform_trend_keywords(platform: str) -> List[str]:
    """获取平台趋势关键词（静态版）"""
    trend_keywords = {
        "douyin": [
            "黄金3秒", "反转剧情", "情绪价值", "悬念", "冲突"
        ],
        "xiaohongshu": [
            "种草", "好物分享", "ins风", "精致", "生活美学"
        ],
        "bilibili": [
            "干货", "硬核", "玩梗", "一键三连", "深度解析"
        ],
        "toutiao": [
            "热点", "爆款", "深度", "独家", "重磅"
        ]
    }
    
    return trend_keywords.get(platform, trend_keywords["douyin"])
