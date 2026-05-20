"""
头条文章内容抓取服务
使用 Playwright 模拟浏览器访问，绕过反爬机制，抓取真实文章内容
"""
import asyncio
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from app.utils.logger import logger


class ToutiaoArticleFetcher:
    """头条文章内容抓取器"""
    
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    async def initialize(self, headless: bool = True):
        """初始化浏览器"""
        try:
            logger.info("🌐 初始化头条文章抓取浏览器...")
            
            # Windows 事件循环修复
            import sys
            if sys.platform == 'win32':
                asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
            
            playwright = await async_playwright().start()
            
            # 启动 Edge 浏览器（与头条发布使用相同的配置）
            edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
            import os
            if not os.path.exists(edge_path):
                edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
            
            if not os.path.exists(edge_path):
                raise FileNotFoundError("未找到 Edge 浏览器")
            
            self.browser = await playwright.chromium.launch(
                executable_path=edge_path,
                headless=headless,
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--no-sandbox',
                    '--disable-setuid-sandbox'
                ]
            )
            
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                locale="zh-CN",
                timezone_id="Asia/Shanghai"
            )
            
            self.page = await self.context.new_page()
            logger.info("✅ 浏览器初始化完成")
            
        except Exception as e:
            logger.error(f"❌ 浏览器初始化失败: {e}")
            raise
    
    async def search_and_fetch_article(
        self, 
        keyword: str,
        max_results: int = 3
    ) -> Optional[Dict]:
        """
        搜索关键词并抓取第一篇文章内容
        
        Args:
            keyword: 搜索关键词
            max_results: 最大尝试的文章数量
            
        Returns:
            {
                "title": "文章标题",
                "content": "文章内容",
                "author": "作者",
                "publish_date": "发布日期",
                "url": "文章URL"
            }
        """
        try:
            logger.info(f"🔍 开始搜索并抓取文章: {keyword}")
            
            # 步骤1: 访问头条搜索页面
            search_url = f"https://www.toutiao.com/search/?keyword={keyword}"
            logger.info(f"   访问搜索页面: {search_url}")
            
            await self.page.goto(search_url, timeout=30000, wait_until='domcontentloaded')
            await asyncio.sleep(3)  # 等待页面加载
            
            # 步骤2: 提取搜索结果中的文章链接
            article_urls = await self._extract_article_urls(max_results)
            
            if not article_urls:
                logger.warning(f"⚠️  未找到相关文章")
                return None
            
            logger.info(f"✅ 找到 {len(article_urls)} 篇文章，开始逐个尝试抓取...")
            
            # 步骤3: 逐个尝试抓取文章内容
            for idx, article_url in enumerate(article_urls, 1):
                logger.info(f"\n   [{idx}/{len(article_urls)}] 尝试抓取: {article_url[:80]}...")
                
                try:
                    article_data = await self._fetch_single_article(article_url)
                    
                    if article_data and len(article_data.get("content", "")) > 500:
                        logger.info(f"✅ 成功抓取文章（长度: {len(article_data['content'])}字）")
                        return article_data
                    else:
                        logger.warning(f"⚠️  文章内容过短或为空，尝试下一篇...")
                        
                except Exception as e:
                    logger.warning(f"⚠️  抓取第{idx}篇失败: {e}，继续尝试...")
                    continue
            
            logger.warning(f"❌ 所有文章都抓取失败")
            return None
            
        except Exception as e:
            logger.error(f"❌ 搜索和抓取过程失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _extract_article_urls(self, max_count: int) -> List[str]:
        """从搜索结果中提取文章URL"""
        try:
            urls = await self.page.evaluate("""
                (maxCount) => {
                    const urls = [];
                    const seen = new Set();
                    
                    // 策略1: 查找文章卡片链接
                    const selectors = [
                        'a[href*="/article/"]',
                        'a[href*="/wenda/"]',
                        '.article-link a',
                        '[class*="article"] a',
                        '.result-item a'
                    ];
                    
                    for (const selector of selectors) {
                        const links = document.querySelectorAll(selector);
                        for (const link of links) {
                            const href = link.href;
                            if (href && !seen.has(href) && href.includes('toutiao.com')) {
                                seen.add(href);
                                urls.push(href);
                                if (urls.length >= maxCount) {
                                    return urls;
                                }
                            }
                        }
                    }
                    
                    return urls;
                }
            """, max_count)
            
            logger.info(f"   📊 提取到 {len(urls)} 个文章链接")
            return urls
            
        except Exception as e:
            logger.error(f"❌ 提取文章链接失败: {e}")
            return []
    
    async def _fetch_single_article(self, url: str) -> Optional[Dict]:
        """抓取单篇文章的完整内容"""
        try:
            # 访问文章页面
            await self.page.goto(url, timeout=30000, wait_until='domcontentloaded')
            await asyncio.sleep(3)  # 等待内容加载
            
            # 滚动页面以触发懒加载
            await self.page.evaluate("""
                () => {
                    window.scrollTo(0, document.body.scrollHeight / 2);
                }
            """)
            await asyncio.sleep(2)
            
            await self.page.evaluate("""
                () => {
                    window.scrollTo(0, document.body.scrollHeight);
                }
            """)
            await asyncio.sleep(2)
            
            # 提取文章内容
            article_data = await self.page.evaluate("""
                () => {
                    // 提取标题
                    let title = '';
                    const titleSelectors = [
                        'h1.article-title',
                        'h1.title',
                        '[class*="title"]',
                        'meta[property="og:title"]'
                    ];
                    
                    for (const selector of titleSelectors) {
                        const el = document.querySelector(selector);
                        if (el) {
                            title = el.content || el.textContent || '';
                            title = title.trim();
                            if (title.length > 5) break;
                        }
                    }
                    
                    // 提取正文内容
                    let content = '';
                    const contentSelectors = [
                        '.article-content',
                        '.article-body',
                        '[class*="article-content"]',
                        '#article-content',
                        'article',
                        '.post-content'
                    ];
                    
                    for (const selector of contentSelectors) {
                        const container = document.querySelector(selector);
                        if (container) {
                            // 移除脚本、样式等无关元素
                            const clone = container.cloneNode(true);
                            const scripts = clone.querySelectorAll('script, style, nav, header, footer, .ad, .advertisement');
                            scripts.forEach(el => el.remove());
                            
                            // 提取段落文本
                            const paragraphs = clone.querySelectorAll('p');
                            const texts = [];
                            paragraphs.forEach(p => {
                                const text = p.textContent.trim();
                                if (text.length > 20) {  // 过滤短段落
                                    texts.push(text);
                                }
                            });
                            
                            if (texts.length > 0) {
                                content = texts.join('\\n\\n');
                                break;
                            }
                        }
                    }
                    
                    // 提取作者
                    let author = '';
                    const authorSelectors = [
                        '.author-name',
                        '[class*="author"]',
                        'meta[name="author"]'
                    ];
                    
                    for (const selector of authorSelectors) {
                        const el = document.querySelector(selector);
                        if (el) {
                            author = el.content || el.textContent || '';
                            author = author.trim();
                            if (author.length > 0) break;
                        }
                    }
                    
                    // 提取发布时间
                    let publishDate = '';
                    const timeSelectors = [
                        '.publish-time',
                        'time',
                        '[class*="time"]',
                        'meta[property="article:published_time"]'
                    ];
                    
                    for (const selector of timeSelectors) {
                        const el = document.querySelector(selector);
                        if (el) {
                            publishDate = el.content || el.textContent || el.datetime || '';
                            publishDate = publishDate.trim();
                            if (publishDate.length > 0) break;
                        }
                    }
                    
                    return {
                        title: title.substring(0, 100),
                        content: content,
                        author: author.substring(0, 50),
                        publishDate: publishDate.substring(0, 50)
                    };
                }
            """)
            
            if not article_data or not article_data.get("title") or not article_data.get("content"):
                logger.warning(f"   ⚠️  未能提取到有效的标题或内容")
                return None
            
            # 清理内容
            content = article_data["content"].replace('\\n\\n', '\n\n')
            
            return {
                "title": article_data["title"],
                "content": content,
                "author": article_data.get("author", ""),
                "publish_date": article_data.get("publishDate", ""),
                "url": url
            }
            
        except Exception as e:
            logger.error(f"❌ 抓取单篇文章失败: {e}")
            return None
    
    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            logger.info("✅ 浏览器已关闭")
        except Exception as e:
            logger.warning(f"⚠️  关闭浏览器时出错: {e}")


async def fetch_toutiao_article(keyword: str, max_results: int = 3) -> Optional[Dict]:
    """
    便捷函数：搜索并抓取头条文章
    
    Args:
        keyword: 搜索关键词
        max_results: 最大尝试的文章数量
        
    Returns:
        文章数据字典，失败返回 None
    """
    fetcher = ToutiaoArticleFetcher()
    
    try:
        await fetcher.initialize(headless=True)
        result = await fetcher.search_and_fetch_article(keyword, max_results)
        return result
    finally:
        await fetcher.close()
