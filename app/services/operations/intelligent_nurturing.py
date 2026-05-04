"""
智能养号系统
实现模拟真人行为的养号策略，包括浏览轨迹、互动模拟、活跃时段控制
"""
import asyncio
import random
import logging
from datetime import datetime, time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json

from playwright.async_api import async_playwright, Page, Browser, BrowserContext

logger = logging.getLogger(__name__)


class PlatformType(Enum):
    """支持的平台类型"""
    DOUYIN = "douyin"
    KUAISHOU = "kuaishou"
    XIAOHONGSHU = "xiaohongshu"
    TOUTIAO = "toutiao"
    BILIBILI = "bilibili"
    WECHAT = "wechat"


class InteractionType(Enum):
    """互动类型"""
    LIKE = "like"
    COMMENT = "comment"
    FORWARD = "forward"
    FOLLOW = "follow"
    COLLECT = "collect"


@dataclass
class NurturingConfig:
    """养号配置"""
    # 浏览配置
    min_videos_per_session: int = 10  # 每次会话最少观看视频数
    max_videos_per_session: int = 30  # 每次会话最多观看视频数
    min_watch_duration: int = 5  # 最小观看时长（秒）
    max_watch_duration: int = 60  # 最大观看时长（秒）
    
    # 互动概率（0-100）
    like_probability: int = 5  # 点赞概率 5%
    comment_probability: int = 1  # 评论概率 1%
    forward_probability: int = 0.5  # 转发概率 0.5%
    follow_probability: int = 2  # 关注概率 2%
    collect_probability: int = 3  # 收藏概率 3%
    
    # 活跃时段
    active_start_hour: int = 20  # 开始时间（小时）
    active_end_hour: int = 22  # 结束时间（小时）
    
    # 浏览轨迹配置
    scroll_behavior: str = "normal"  # normal/aggressive/conservative
    category_focused: bool = True  # 是否专注同类内容


class IntelligentNurturingEngine:
    """智能养号引擎"""
    
    # 各平台的热门分类标签
    PLATFORM_CATEGORIES = {
        PlatformType.DOUYIN: ["科技", "数码", "美食", "旅行", "娱乐", "教育", "游戏"],
        PlatformType.KUAISHOU: ["科技", "美食", "生活", "娱乐", "游戏", "汽车"],
        PlatformType.XIAOHONGSHU: ["科技数码", "美食", "旅行", "穿搭", "美妆", "家居"],
        PlatformType.TOUTIAO: ["科技", "教育", "娱乐", "体育", "财经", "健康"],
        PlatformType.BILIBILI: ["科技", "游戏", "生活", "美食", "音乐", "舞蹈"],
        PlatformType.WECHAT: ["科技", "教育", "生活", "美食", "旅行"]
    }
    
    # 各平台的URL模板
    PLATFORM_URLS = {
        PlatformType.DOUYIN: "https://www.douyin.com",
        PlatformType.KUAISHOU: "https://www.kuaishou.com",
        PlatformType.XIAOHONGSHU: "https://www.xiaohongshu.com",
        PlatformType.TOUTIAO: "https://www.toutiao.com",
        PlatformType.BILIBILI: "https://www.bilibili.com",
        PlatformType.WECHAT: "https://weixin.qq.com"
    }
    
    # 各平台的搜索页面
    SEARCH_URLS = {
        PlatformType.DOUYIN: "https://www.douyin.com/search",
        PlatformType.KUAISHOU: "https://www.kuaishou.com/search",
        PlatformType.XIAOHONGSHU: "https://www.xiaohongshu.com/search_result",
        PlatformType.TOUTIAO: "https://www.toutiao.com/search",
        PlatformType.BILIBILI: "https://search.bilibili.com/all",
        PlatformType.WECHAT: "https://weixin.sogou.com"
    }
    
    # 各平台的选择器（需要根据实际页面调整）
    PLATFORM_SELECTORS = {
        PlatformType.DOUYIN: {
            "video_item": '[data-e2e="feed-video"]',
            "like_button": '[data-e2e="like-icon"]',
            "comment_button": '[data-e2e="comment-icon"]',
            "forward_button": '[data-e2e="share-icon"]',
            "follow_button": '[data-e2e="follow-button"]',
            "video_title": '[data-e2e="video-desc"]',
            "video_author": '[data-e2e="author-name"]',
            "scroll_container": "body"
        },
        PlatformType.KUAISHOU: {
            "video_item": ".video-item",
            "like_button": ".like-btn",
            "comment_button": ".comment-btn",
            "forward_button": ".share-btn",
            "follow_button": ".follow-btn",
            "video_title": ".video-title",
            "video_author": ".author-name",
            "scroll_container": "body"
        },
        PlatformType.XIAOHONGSHU: {
            "video_item": ".note-item",
            "like_button": ".like-btn",
            "comment_button": ".comment-btn",
            "forward_button": ".share-btn",
            "follow_button": ".follow-btn",
            "video_title": ".note-title",
            "video_author": ".author-name",
            "scroll_container": "body"
        },
        PlatformType.TOUTIAO: {
            "video_item": ".video-item",
            "like_button": ".like-btn",
            "comment_button": ".comment-btn",
            "forward_button": ".share-btn",
            "follow_button": ".follow-btn",
            "video_title": ".article-title",
            "video_author": ".author-name",
            "scroll_container": "body"
        },
        PlatformType.BILIBILI: {
            "video_item": ".video-item",
            "like_button": ".like-btn",
            "comment_button": ".comment-btn",
            "forward_button": ".share-btn",
            "follow_button": ".follow-btn",
            "video_title": ".video-title",
            "video_author": ".author-name",
            "scroll_container": "body"
        },
        PlatformType.WECHAT: {
            "video_item": ".video-item",
            "like_button": ".like-btn",
            "comment_button": ".comment-btn",
            "forward_button": ".share-btn",
            "follow_button": ".follow-btn",
            "video_title": ".video-title",
            "video_author": ".author-name",
            "scroll_container": "body"
        }
    }
    
    def __init__(self, config: Optional[NurturingConfig] = None):
        self.config = config or NurturingConfig()
        self.current_category = None
        self.nurturing_history = []
        
    def _is_active_time(self) -> bool:
        """
        检查当前是否为活跃时段
        
        Returns:
            bool: 是否在活跃时段内
        """
        now = datetime.now()
        current_hour = now.hour
        return self.config.active_start_hour <= current_hour < self.config.active_end_hour
    
    def _generate_watch_duration(self) -> int:
        """
        生成符合正态分布的观看时长
        
        Returns:
            int: 观看时长（秒）
        """
        # 使用正态分布生成观看时长
        mean = (self.config.max_watch_duration + self.config.min_watch_duration) / 2
        std = (self.config.max_watch_duration - self.config.min_watch_duration) / 4
        duration = int(random.gauss(mean, std))
        
        # 确保在范围内
        duration = max(self.config.min_watch_duration, min(self.config.max_watch_duration, duration))
        return duration
    
    def _should_interact(self, interaction_type: InteractionType) -> bool:
        """
        判断是否应该执行互动
        
        Args:
            interaction_type: 互动类型
            
        Returns:
            bool: 是否执行互动
        """
        probabilities = {
            InteractionType.LIKE: self.config.like_probability,
            InteractionType.COMMENT: self.config.comment_probability,
            InteractionType.FORWARD: self.config.forward_probability,
            InteractionType.FOLLOW: self.config.follow_probability,
            InteractionType.COLLECT: self.config.collect_probability
        }
        
        probability = probabilities.get(interaction_type, 0)
        return random.randint(1, 100) <= probability
    
    def _select_category(self, platform: PlatformType) -> str:
        """
        选择浏览分类
        
        Args:
            platform: 平台类型
            
        Returns:
            str: 分类名称
        """
        categories = self.PLATFORM_CATEGORIES.get(platform, [])
        if not categories:
            return ""
        
        # 如果专注同类内容，使用当前分类
        if self.config.category_focused and self.current_category:
            if random.random() < 0.8:  # 80%概率继续浏览同类
                return self.current_category
        
        # 随机选择新分类
        self.current_category = random.choice(categories)
        return self.current_category
    
    def _generate_scroll_behavior(self) -> Dict[str, Any]:
        """
        生成滚动行为参数
        
        Returns:
            Dict: 滚动参数
        """
        if self.config.scroll_behavior == "aggressive":
            scroll_steps = random.randint(3, 5)
            scroll_distance = random.randint(300, 500)
        elif self.config.scroll_behavior == "conservative":
            scroll_steps = random.randint(1, 2)
            scroll_distance = random.randint(100, 200)
        else:  # normal
            scroll_steps = random.randint(2, 3)
            scroll_distance = random.randint(200, 400)
        
        return {
            "steps": scroll_steps,
            "distance": scroll_distance,
            "delay": random.uniform(0.5, 2.0)
        }
    
    async def _simulate_human_scroll(self, page: Page, container_selector: str = "body"):
        """
        模拟人类滚动行为
        
        Args:
            page: Playwright页面对象
            container_selector: 滚动容器选择器
        """
        scroll_params = self._generate_scroll_behavior()
        
        for i in range(scroll_params["steps"]):
            # 随机滚动距离
            scroll_y = random.randint(scroll_params["distance"] - 50, scroll_params["distance"] + 50)
            
            # 执行滚动
            await page.evaluate(f"""
                const container = document.querySelector('{container_selector}');
                if (container) {{
                    container.scrollBy({{ top: {scroll_y}, behavior: 'smooth' }});
                }}
            """)
            
            # 随机延迟
            delay = random.uniform(scroll_params["delay"] * 0.8, scroll_params["delay"] * 1.2)
            await asyncio.sleep(delay)
            
            # 模拟人类的不确定性：偶尔向上滚动
            if random.random() < 0.1:  # 10%概率向上滚动
                scroll_up = random.randint(50, 150)
                await page.evaluate(f"""
                    const container = document.querySelector('{container_selector}');
                    if (container) {{
                        container.scrollBy({{ top: -{scroll_up}, behavior: 'smooth' }});
                    }}
                """)
                await asyncio.sleep(random.uniform(0.3, 1.0))
    
    async def _wait_for_page_load(self, page: Page, timeout: int = 30000):
        """
        等待页面加载完成
        
        Args:
            page: Playwright页面对象
            timeout: 超时时间（毫秒）
        """
        try:
            # 等待页面网络空闲
            await page.wait_for_load_state("networkidle", timeout=timeout)
            # 额外等待确保动态内容加载
            await asyncio.sleep(random.uniform(1, 2))
        except Exception as e:
            logger.warning(f"等待页面加载超时: {e}")
    
    async def _perform_interaction(
        self,
        page: Page,
        interaction_type: InteractionType,
        selectors: Dict[str, str]
    ) -> bool:
        """
        执行互动操作
        
        Args:
            page: Playwright页面对象
            interaction_type: 互动类型
            selectors: 平台选择器
            
        Returns:
            bool: 是否成功
        """
        try:
            # 获取对应按钮选择器
            button_selector = selectors.get(f"{interaction_type.value}_button")
            if not button_selector:
                logger.warning(f"未找到{interaction_type.value}按钮选择器")
                return False
            
            # 等待按钮可见
            await page.wait_for_selector(button_selector, timeout=5000)
            
            # 模拟人类鼠标移动
            button = await page.query_selector(button_selector)
            if button:
                box = await button.bounding_box()
                if box:
                    # 随机偏移
                    offset_x = random.uniform(-5, 5)
                    offset_y = random.uniform(-5, 5)
                    target_x = box["x"] + box["width"] / 2 + offset_x
                    target_y = box["y"] + box["height"] / 2 + offset_y
                    
                    # 鼠标移动并点击
                    await page.mouse.move(target_x, target_y)
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    await button.click()
                    
                    logger.info(f"✅ 成功执行{interaction_type.value}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"执行{interaction_type.value}失败: {e}")
            return False
    
    async def _perform_comment(self, page: Page, selectors: Dict[str, str]) -> bool:
        """
        执行评论操作（特殊处理）
        
        Args:
            page: Playwright页面对象
            selectors: 平台选择器
            
        Returns:
            bool: 是否成功
        """
        try:
            # 评论模板
            comment_templates = [
                "内容很棒！",
                "学到了，感谢分享",
                "这个观点很有意思",
                "支持一下",
                "期待更多内容"
            ]
            
            # 点击评论按钮
            await self._perform_interaction(page, InteractionType.COMMENT, selectors)
            await asyncio.sleep(random.uniform(1, 2))
            
            # 等待评论框出现
            comment_input_selector = selectors.get("comment_input", "textarea, input[type='text']")
            await page.wait_for_selector(comment_input_selector, timeout=5000)
            
            # 输入评论（模拟人类打字）
            comment_text = random.choice(comment_templates)
            input_field = await page.query_selector(comment_input_selector)
            if input_field:
                await input_field.click()
                await asyncio.sleep(random.uniform(0.3, 0.5))
                
                # 逐字输入，模拟人类打字速度
                for char in comment_text:
                    await input_field.type(char, delay=random.uniform(50, 150))
                
                await asyncio.sleep(random.uniform(0.5, 1))
                
                # 提交评论
                submit_button_selector = selectors.get("comment_submit", "button[type='submit'], .submit-btn")
                submit_button = await page.query_selector(submit_button_selector)
                if submit_button:
                    await submit_button.click()
                    logger.info(f"✅ 成功评论: {comment_text}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"评论失败: {e}")
            return False
    
    async def browse_videos(
        self,
        page: Page,
        platform: PlatformType,
        num_videos: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        浏览视频（模拟真人浏览轨迹）
        
        Args:
            page: Playwright页面对象
            platform: 平台类型
            num_videos: 浏览视频数量（不指定则使用配置范围）
            
        Returns:
            List[Dict]: 浏览记录
        """
        if num_videos is None:
            num_videos = random.randint(
                self.config.min_videos_per_session,
                self.config.max_videos_per_session
            )
        
        selectors = self.PLATFORM_SELECTORS.get(platform, {})
        if not selectors:
            logger.error(f"不支持的平台: {platform.value}")
            return []
        
        browse_records = []
        
        # 选择浏览分类
        category = self._select_category(platform)
        logger.info(f"📱 开始浏览 {platform.value} 平台，分类: {category}，目标视频数: {num_videos}")
        
        try:
            # 导航到平台首页
            await page.goto(self.PLATFORM_URLS[platform], wait_until="domcontentloaded")
            await self._wait_for_page_load(page)
            
            # 如果有分类，搜索分类内容
            if category:
                search_url = f"{self.SEARCH_URLS[platform]}?keyword={category}"
                await page.goto(search_url, wait_until="domcontentloaded")
                await self._wait_for_page_load(page)
            
            # 浏览视频
            for i in range(num_videos):
                try:
                    # 模拟滚动查找视频
                    await self._simulate_human_scroll(page, selectors["scroll_container"])
                    await asyncio.sleep(random.uniform(0.5, 1.5))
                    
                    # 查找视频元素
                    video_items = await page.query_selector_all(selectors["video_item"])
                    if not video_items:
                        logger.warning(f"未找到视频元素，继续滚动")
                        await self._simulate_human_scroll(page, selectors["scroll_container"])
                        continue
                    
                    # 随机选择一个视频
                    video_item = random.choice(video_items)
                    
                    # 获取视频信息
                    video_title = ""
                    video_author = ""
                    
                    try:
                        title_element = await video_item.query_selector(selectors["video_title"])
                        if title_element:
                            video_title = await title_element.inner_text()
                        
                        author_element = await video_item.query_selector(selectors["video_author"])
                        if author_element:
                            video_author = await author_element.inner_text()
                    except:
                        pass
                    
                    # 点击视频
                    await video_item.click()
                    await asyncio.sleep(random.uniform(1, 2))
                    
                    # 观看视频（模拟真人观看时长）
                    watch_duration = self._generate_watch_duration()
                    logger.info(f"🎬 观看视频 {i+1}/{num_videos}: {video_title}，时长: {watch_duration}秒")
                    
                    # 分段观看，模拟暂停和回放
                    segments = random.randint(2, 4)
                    segment_duration = watch_duration // segments
                    
                    for seg in range(segments):
                        await asyncio.sleep(segment_duration)
                        
                        # 随机暂停
                        if random.random() < 0.2:  # 20%概率暂停
                            await asyncio.sleep(random.uniform(2, 5))
                    
                    # 执行互动
                    interactions = []
                    
                    # 点赞
                    if self._should_interact(InteractionType.LIKE):
                        success = await self._perform_interaction(page, InteractionType.LIKE, selectors)
                        if success:
                            interactions.append("like")
                            await asyncio.sleep(random.uniform(1, 2))
                    
                    # 评论
                    if self._should_interact(InteractionType.COMMENT):
                        success = await self._perform_comment(page, selectors)
                        if success:
                            interactions.append("comment")
                            await asyncio.sleep(random.uniform(1, 2))
                    
                    # 转发
                    if self._should_interact(InteractionType.FORWARD):
                        success = await self._perform_interaction(page, InteractionType.FORWARD, selectors)
                        if success:
                            interactions.append("forward")
                            await asyncio.sleep(random.uniform(1, 2))
                    
                    # 关注
                    if self._should_interact(InteractionType.FOLLOW):
                        success = await self._perform_interaction(page, InteractionType.FOLLOW, selectors)
                        if success:
                            interactions.append("follow")
                            await asyncio.sleep(random.uniform(1, 2))
                    
                    # 收藏
                    if self._should_interact(InteractionType.COLLECT):
                        success = await self._perform_interaction(page, InteractionType.COLLECT, selectors)
                        if success:
                            interactions.append("collect")
                            await asyncio.sleep(random.uniform(1, 2))
                    
                    # 记录浏览信息
                    record = {
                        "platform": platform.value,
                        "category": category,
                        "video_title": video_title,
                        "video_author": video_author,
                        "watch_duration": watch_duration,
                        "interactions": interactions,
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    browse_records.append(record)
                    self.nurturing_history.append(record)
                    
                    # 返回上一页
                    await page.go_back()
                    await asyncio.sleep(random.uniform(1, 2))
                    
                except Exception as e:
                    logger.error(f"浏览视频 {i+1} 时出错: {e}")
                    continue
            
            logger.info(f"✅ 浏览完成，共观看 {len(browse_records)} 个视频")
            return browse_records
            
        except Exception as e:
            logger.error(f"浏览视频失败: {e}")
            return browse_records
    
    async def execute_nurturing_session(
        self,
        browser: Browser,
        platform: PlatformType,
        cookies: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        执行完整的养号会话
        
        Args:
            browser: Playwright浏览器实例
            platform: 平台类型
            cookies: 登录Cookie
            
        Returns:
            Dict: 养号会话结果
        """
        # 检查是否为活跃时段
        if not self._is_active_time():
            logger.warning(f"⚠️ 当前不在活跃时段（{self.config.active_start_hour}:00-{self.config.active_end_hour}:00）")
        
        result = {
            "platform": platform.value,
            "start_time": datetime.now().isoformat(),
            "is_active_time": self._is_active_time(),
            "category": None,
            "videos_watched": 0,
            "total_watch_duration": 0,
            "interactions": {
                "like": 0,
                "comment": 0,
                "forward": 0,
                "follow": 0,
                "collect": 0
            },
            "browse_records": [],
            "status": "in_progress"
        }
        
        try:
            # 创建浏览器上下文
            context = await browser.new_context()
            
            # 如果有Cookie，加载Cookie
            if cookies:
                await context.add_cookies(cookies)
            
            # 创建页面
            page = await context.new_page()
            
            # 设置视口大小（模拟移动端）
            await page.set_viewport_size({"width": 375, "height": 667})
            
            # 执行浏览
            browse_records = await self.browse_videos(page, platform)
            
            # 统计结果
            result["browse_records"] = browse_records
            result["videos_watched"] = len(browse_records)
            result["total_watch_duration"] = sum(r["watch_duration"] for r in browse_records)
            result["category"] = self.current_category
            
            # 统计互动次数
            for record in browse_records:
                for interaction in record["interactions"]:
                    if interaction in result["interactions"]:
                        result["interactions"][interaction] += 1
            
            result["status"] = "completed"
            result["end_time"] = datetime.now().isoformat()
            
            # 关闭页面和上下文
            await page.close()
            await context.close()
            
            logger.info(f"✅ 养号会话完成: {result}")
            return result
            
        except Exception as e:
            logger.error(f"养号会话失败: {e}")
            result["status"] = "failed"
            result["error"] = str(e)
            result["end_time"] = datetime.now().isoformat()
            return result
    
    def get_nurturing_statistics(self) -> Dict[str, Any]:
        """
        获取养号统计信息
        
        Returns:
            Dict: 统计信息
        """
        if not self.nurturing_history:
            return {
                "total_sessions": 0,
                "total_videos_watched": 0,
                "total_watch_duration": 0,
                "interaction_stats": {}
            }
        
        total_videos = len(self.nurturing_history)
        total_duration = sum(r["watch_duration"] for r in self.nurturing_history)
        
        # 统计各平台浏览情况
        platform_stats = {}
        for record in self.nurturing_history:
            platform = record["platform"]
            if platform not in platform_stats:
                platform_stats[platform] = {
                    "videos": 0,
                    "duration": 0,
                    "interactions": []
                }
            platform_stats[platform]["videos"] += 1
            platform_stats[platform]["duration"] += record["watch_duration"]
            platform_stats[platform]["interactions"].extend(record["interactions"])
        
        # 统计互动类型
        interaction_stats = {}
        for record in self.nurturing_history:
            for interaction in record["interactions"]:
                interaction_stats[interaction] = interaction_stats.get(interaction, 0) + 1
        
        return {
            "total_sessions": len(set(r["timestamp"][:10] for r in self.nurturing_history)),
            "total_videos_watched": total_videos,
            "total_watch_duration": total_duration,
            "platform_stats": platform_stats,
            "interaction_stats": interaction_stats
        }
    
    def export_history(self, filepath: str):
        """
        导出养号历史记录
        
        Args:
            filepath: 导出文件路径
        """
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.nurturing_history, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ 养号历史已导出到: {filepath}")


# 创建全局养号引擎实例
_nurturing_engine = None


def get_nurturing_engine(config: Optional[NurturingConfig] = None) -> IntelligentNurturingEngine:
    """
    获取养号引擎实例（单例模式）
    
    Args:
        config: 养号配置
        
    Returns:
        IntelligentNurturingEngine: 养号引擎实例
    """
    global _nurturing_engine
    if _nurturing_engine is None:
        _nurturing_engine = IntelligentNurturingEngine(config)
    return _nurturing_engine
