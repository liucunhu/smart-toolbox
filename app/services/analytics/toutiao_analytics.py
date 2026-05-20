"""
头条文章数据分析服务
通过Playwright抓取头条后台的文章统计数据（阅读量、点赞数、评论数等）
"""
import asyncio
from playwright.async_api import async_playwright, Browser, Page
from typing import List, Dict, Optional
from app.utils.logger import logger
from sqlalchemy.orm import Session
from app.models import Account


class ToutiaoAnalyticsService:
    """头条文章数据分析服务"""
    
    def __init__(self, account_id: int, db: Session):
        self.account_id = account_id
        self.db = db
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.context = None
        
    async def initialize(self, headless: bool = True, use_cdp: bool = True, cdp_port: int = 9222):
        """初始化浏览器"""
        try:
            logger.info(f"🌐 初始化头条数据分析浏览器...")
            
            # === Windows 事件循环修复 ===
            # Playwright 需要创建子进程，Windows 默认 SelectorEventLoop 不支持 subprocess
            # 必须在 async_playwright().start() 之前设置 ProactorEventLoop
            import sys
            if sys.platform == 'win32':
                import asyncio
                current_policy = asyncio.get_event_loop_policy()
                if not isinstance(current_policy, asyncio.WindowsProactorEventLoopPolicy):
                    logger.warning("⚠️  当前事件循环策略不是 ProactorEventLoop，尝试切换...")
                    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
                    
                    # 注意：uvicorn 已经创建并运行了事件循环，策略设置不会改变已运行的循环
                    # 这里记录警告，但 Playwright 内部可能会使用自己的子进程处理
                    logger.warning("   提示：uvicorn worker 已使用 SelectorEventLoop 运行")
                    logger.warning("   建议：重启服务并使用 python start_server.py 启动")
            
            self.playwright = await async_playwright().start()
            
            if use_cdp:
                # 使用CDP连接已运行的Edge浏览器（推荐）
                import subprocess
                import os
                import socket
                
                logger.info(f" 正在连接Edge浏览器 (CDP端口: {cdp_port})...")
                
                # 检查CDP端口是否可用
                cdp_available = False
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('127.0.0.1', cdp_port))
                    if result == 0:
                        cdp_available = True
                        logger.info(f"   ⚠️  CDP端口 {cdp_port} 已被占用，尝试复用现有浏览器")
                    sock.close()
                except:
                    pass
                
                if not cdp_available:
                    # 启动带远程调试的Edge
                    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
                    if not os.path.exists(edge_path):
                        edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
                    
                    if not os.path.exists(edge_path):
                        raise FileNotFoundError("未找到 Edge 浏览器")
                    
                    logger.info(f"   启动新的Edge浏览器实例...")
                    user_data_dir = "./edge_profile_toutiao_analytics"
                    cmd = [
                        edge_path,
                        f'--remote-debugging-port={cdp_port}',
                        f'--user-data-dir={user_data_dir}',
                        'https://mp.toutiao.com/'
                    ]
                    
                    process = subprocess.Popen(cmd)
                    logger.info("✅ Edge浏览器已启动")
                    logger.info("   等待浏览器完全启动...")
                    await asyncio.sleep(5)
                else:
                    logger.info("   ✅ 使用现有的Edge浏览器实例")
                
                # 连接到Edge浏览器
                self.browser = await self.playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
                
                # 获取第一个context
                contexts = self.browser.contexts
                if not contexts:
                    self.context = await self.browser.new_context(
                        viewport={"width": 1920, "height": 1080},
                        locale="zh-CN",
                        timezone_id="Asia/Shanghai"
                    )
                else:
                    self.context = contexts[0]
                
                # 创建新标签页
                logger.info("   📑 创建新的标签页...")
                self.page = await self.context.new_page()
                logger.info(f"✅ 通过CDP连接到Edge浏览器成功")
                return
            
            # 降级方案：使用Edge浏览器的用户目录
            edge_profile = "C:\\Users\\hspcadmin\\AppData\\Local\\Microsoft\\Edge\\User Data"
            
            try:
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=edge_profile,
                    headless=headless,
                    args=[
                        '--no-sandbox',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled',
                        '--excludeSwitches=enable-automation',
                    ]
                )
                self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
            except Exception as e:
                logger.warning(f"无法使用Edge用户目录，使用无头模式: {e}")
                browser = await self.playwright.chromium.launch(
                    headless=headless,
                    args=['--no-sandbox', '--disable-blink-features=AutomationControlled']
                )
                self.page = await browser.new_page()
                self.browser = browser
            
            logger.info("✅ 浏览器初始化成功")
            
        except Exception as e:
            logger.error(f"❌ 浏览器初始化失败: {e}")
            raise
    
    async def login_if_needed(self, use_cdp: bool = True):
        """
        检查是否需要登录
        - 如果使用CDP连接，Edge浏览器已有登录状态，直接跳过
        - 如果数据库有Cookie，尝试使用Cookie自动登录
        - 只有在Cookie不存在或过期时才返回False（需要重新登录）
        """
        try:
            # 策略1: 如果使用CDP连接，Edge浏览器已经有登录状态，直接跳过
            if use_cdp:
                logger.info("🔌 使用CDP连接，Edge浏览器已有登录状态，跳过登录...")
                return True
            
            # 策略2: 从数据库获取账号Cookie
            account = self.db.query(Account).filter(Account.id == self.account_id).first()
            if not account or not account.cookies:
                logger.warning("⚠️  数据库中无Cookie，需要手动登录")
                return False
            
            logger.info("🔑 检测到已保存的Cookie，尝试自动登录...")
            
            # 解析并设置Cookie
            import json
            try:
                cookie_list = json.loads(account.cookies)
                await self.context.add_cookies(cookie_list)
                logger.info(f"✅ 已加载 {len(cookie_list)} 个 Cookie")
            except Exception as e:
                logger.error(f"❌ Cookie解析失败: {e}")
                return False
            
            # 访问头条后台页面验证Cookie是否有效
            logger.info("🌐 正在验证Cookie有效性...")
            await self.page.goto("https://mp.toutiao.com/profile_v4/graphic/articles", timeout=30000, wait_until='domcontentloaded')
            await asyncio.sleep(5)
            
            # 检查是否登录成功
            current_url = self.page.url
            page_title = await self.page.title()
            
            logger.info(f"📄 当前URL: {current_url}")
            logger.info(f"📄 页面标题: {page_title}")
            
            # 检测策略1: URL包含 profile 且不包含 login/sso
            if "profile" in current_url and "login" not in current_url and "sso" not in current_url:
                logger.info("✅ Cookie有效，登录成功（URL匹配）")
                return True
            
            # 检测策略2: 页面标题包含头条号相关关键词
            if any(keyword in page_title for keyword in ['头条号', '工作台', '文章管理']):
                logger.info("✅ Cookie有效，登录成功（页面标题匹配）")
                return True
            
            # 检测策略3: 检查是否有用户信息元素
            try:
                user_avatar = await self.page.query_selector('img[alt*="头像"], div[class*="avatar"]')
                if user_avatar and await user_avatar.is_visible():
                    logger.info("✅ Cookie有效，登录成功（检测到用户头像）")
                    return True
            except:
                pass
            
            # 如果以上都不满足，Cookie已过期
            logger.warning("⚠️  Cookie已过期，需要重新登录")
            logger.warning(f"   当前URL: {current_url}")
            logger.warning(f"   页面标题: {page_title}")
            return False
            
        except Exception as e:
            logger.error(f"❌ 登录检查失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def fetch_article_analytics(self, use_cdp: bool = True) -> List[Dict]:
        """
        抓取文章数据分析
            
        Args:
            use_cdp: 是否使用CDP连接（默认True）
                
        Returns:
            文章统计数据列表
        """
        try:
            logger.info("📊 开始抓取文章数据分析...")
                
            # 确保在文章列表页面
            await self.page.goto("https://mp.toutiao.com/profile_v4/graphic/articles", timeout=30000, wait_until='domcontentloaded')
            await asyncio.sleep(5)  # 等待页面基本加载
                
            # 截图调试
            try:
                debug_screenshot = "logs/analytics_debug.png"
                await self.page.screenshot(path=debug_screenshot, full_page=True)
                logger.info(f"📸 页面调试截图: {debug_screenshot}")
            except Exception as e:
                logger.warning(f"截图失败: {e}")
                
            # 获取页面标题
            page_title = await self.page.title()
            logger.info(f"📄 页面标题: {page_title}")
                
            # 使用更宽松的等待策略（不使用 networkidle，因为头条页面可能有持续的网络请求）
            try:
                await self.page.wait_for_load_state('domcontentloaded', timeout=15000)
                logger.info("✅ 页面 DOM 已加载")
            except Exception as e:
                logger.warning(f"⚠️  等待 DOM 加载超时，继续尝试提取数据: {e}")
            
            await asyncio.sleep(3)  # 额外等待让动态内容渲染
                
            # 使用JavaScript获取文章列表（使用正确的选择器）
            logger.info("🔍 开始提取文章数据...")
                        
            articles_data = await self.page.evaluate("""
                () => {
                    const articles = [];
                                
                    // 使用正确的选择器：.article-card（根据调试结果）
                    const articleCards = document.querySelectorAll('.article-card');
                    console.log(`找到 ${articleCards.length} 个文章卡片`);
                                
                    articleCards.forEach((card, index) => {
                        if (index >= 50) return; // 最多50篇
                                    
                        try {
                            const text = card.innerText || '';
                            const lines = text.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                                        
                            // 提取标题（第一行较长的文本）
                            let title = '';
                            for (const line of lines) {
                                if (line.length > 5 && 
                                    !line.match(/^\\d{2}-\\d{2}/) && // 不是日期
                                    !line.includes('已发布') &&
                                    !line.includes('展现') &&
                                    !line.includes('阅读')) {
                                    title = line;
                                    break;
                                }
                            }
                                        
                            if (!title || title.length < 5) return;
                                        
                            // 从文本中提取各个统计数据
                            const showMatch = text.match(/展现\\s*(\\d+)/);
                            const readMatch = text.match(/阅读\\s*(\\d+)/);
                            const likeMatch = text.match(/点赞\\s*(\\d+)/);
                            const commentMatch = text.match(/评论\\s*(\\d+)/);
                            
                            // 提取发布时间（尝试多种格式）
                            let publishTime = null;
                            
                            // 格式1: YYYY-MM-DD HH:mm
                            const dateTimeMatch = text.match(/(\\d{4}-\\d{2}-\\d{2})\\s+(\\d{2}:\\d{2})/);
                            if (dateTimeMatch) {
                                publishTime = `${dateTimeMatch[1]} ${dateTimeMatch[2]}:00`;
                            } else {
                                // 格式2: MM-DD HH:mm （今年）
                                const shortDateMatch = text.match(/(\\d{2}-\\d{2})\\s+(\\d{2}:\\d{2})/);
                                if (shortDateMatch) {
                                    const currentYear = new Date().getFullYear();
                                    publishTime = `${currentYear}-${shortDateMatch[1]} ${shortDateMatch[2]}:00`;
                                } else {
                                    // 格式3: 相对时间（如 "2小时前"、"昨天"）
                                    const relativeMatch = text.match(/(\\d+)\\s*小时前/);
                                    if (relativeMatch) {
                                        const hoursAgo = parseInt(relativeMatch[1]);
                                        const publishDate = new Date(Date.now() - hoursAgo * 60 * 60 * 1000);
                                        publishTime = publishDate.toISOString().replace('T', ' ').substring(0, 19);
                                    } else if (text.includes('昨天')) {
                                        const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000);
                                        publishTime = yesterday.toISOString().replace('T', ' ').substring(0, 19);
                                    } else {
                                        // 默认使用当前时间
                                        publishTime = new Date().toISOString().replace('T', ' ').substring(0, 19);
                                    }
                                }
                            }
                                        
                            const showCount = showMatch ? parseInt(showMatch[1]) : 0;
                            const readCount = readMatch ? parseInt(readMatch[1]) : 0;
                            const likeCount = likeMatch ? parseInt(likeMatch[1]) : 0;
                            const commentCount = commentMatch ? parseInt(commentMatch[1]) : 0;
                                                        
                            articles.push({
                                title: title.substring(0, 100),
                                show_count: showCount,
                                read_count: readCount,
                                like_count: likeCount,
                                comment_count: commentCount,
                                share_count: 0,
                                publish_time: publishTime
                            });
                        } catch (e) {
                            console.error(`处理文章 ${index} 失败:`, e);
                        }
                    });
                                
                    console.log(`成功提取 ${articles.length} 篇文章`);
                    return articles;
                }
            """)
                
            logger.info(f"✅ 成功抓取 {len(articles_data)} 篇文章的数据")
                
            if len(articles_data) == 0:
                logger.warning("⚠️  未抓取到文章数据")
                logger.warning("可能原因：")
                logger.warning("  1. 账号没有发布过文章")
                logger.warning("  2. 页面仍在登录状态")
                logger.warning("  3. 头条页面结构已更新")
                
            return articles_data if isinstance(articles_data, list) else []
                
        except Exception as e:
            logger.error(f"❌ 抓取文章数据失败: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    async def get_article_detail_analytics(self, article_id: str = None) -> Dict:
        """
        获取单篇文章的详细数据分析
        
        Args:
            article_id: 文章ID（可选）
            
        Returns:
            文章详细统计数据
        """
        try:
            logger.info(f"📊 获取文章详细数据分析...")
            
            # 这里需要根据头条后台的实际URL结构调整
            # 暂时返回模拟数据，后续可以根据实际需求完善
            analytics_data = {
                "title": "示例文章",
                "read_count": 1250,
                "like_count": 85,
                "comment_count": 23,
                "share_count": 12,
                "collect_count": 45,  # 收藏数
                "fans_read_count": 890,  # 粉丝阅读
                "recommend_read_count": 360,  # 推荐阅读
                "publish_time": "2024-01-01 12:00:00"
            }
            
            return analytics_data
            
        except Exception as e:
            logger.error(f"❌ 获取文章详细数据失败: {e}")
            return {}
    
    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if hasattr(self, 'playwright'):
                await self.playwright.stop()
            logger.info("✅ 浏览器已关闭")
        except Exception as e:
            logger.warning(f"关闭浏览器时出错: {e}")


def get_analytics_service(account_id: int, db: Session) -> ToutiaoAnalyticsService:
    """获取数据分析服务实例"""
    return ToutiaoAnalyticsService(account_id=account_id, db=db)
