
"""
今日头条自动化发布服务
支持人工账号登录 + 自动化发布文章
"""
import asyncio
import json
import time
from playwright.async_api import async_playwright, BrowserContext, Page
from app.utils.logger import logger
from typing import Dict, Any, Optional


class ToutiaoPublisher:
    """今日头条自动化发布引擎"""

    def __init__(self, account_id: int):
        self.account_id = account_id
        self.playwright = None  # 保存 playwright 实例引用
        self.browser = None     # 保存 browser 实例引用
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def initialize_browser(self, use_cdp: bool = False, cdp_port: int = 9222):
        """
        初始化浏览器
        
        :param use_cdp: 是否使用CDP连接真实Edge浏览器
        :param cdp_port: CDP调试端口，默认9222
        """
        if use_cdp:
            await self.initialize_with_cdp(cdp_port)
        else:
            await self.initialize_standard_browser()
    
    async def initialize_with_cdp(self, cdp_port: int = 9222):
        """
        使用CDP连接真实Edge浏览器（100%还原真实浏览器环境）
        
        :param cdp_port: Edge浏览器的远程调试端口
        """
        import subprocess
        import os
        
        logger.info("🚀 使用CDP模式连接真实Edge浏览器...")
        
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        if not os.path.exists(edge_path):
            edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        
        if not os.path.exists(edge_path):
            raise FileNotFoundError("未找到 Edge 浏览器")
        
        # 步骤1：启动Edge浏览器（带远程调试）
        logger.info(f"[1/3] 启动Edge浏览器（远程调试端口 {cdp_port}）...")
        
        # 先关闭已有的Edge
        try:
            subprocess.run("taskkill /F /IM msedge.exe", shell=True, capture_output=True, timeout=5)
            await asyncio.sleep(2)
        except:
            pass
        
        # 启动带远程调试的Edge
        user_data_dir = "./edge_profile_toutiao_cdp"
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
        
        # 步骤2：连接到Edge浏览器
        logger.info(f"[2/3] 连接到Edge浏览器（CDP端口 {cdp_port}）...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
        
        # 获取第一个context和page
        contexts = self.browser.contexts
        if not contexts:
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai"
            )
        else:
            self.context = contexts[0]
        
        pages = self.context.pages
        if pages:
            self.page = pages[0]
        else:
            self.page = await self.context.new_page()
        
        logger.info("✅ 已连接到真实Edge浏览器")
        logger.info(f"   当前URL: {self.page.url}")
        logger.info("[3/3] CDP连接完成！")
    
    async def initialize_standard_browser(self):
        """初始化标准浏览器（原有逻辑）"""
        self.playwright = await async_playwright().start()
        
        # ★★★ 头条发布页面使用微前端架构，必须使用 Edge 浏览器才能完整加载
        # ★★★ 使用系统默认Edge用户配置文件，而非新建
        
        import os
        # Edge浏览器的默认路径
        edge_executable = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        
        if not os.path.exists(edge_executable):
            edge_executable = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        
        if not os.path.exists(edge_executable):
            raise FileNotFoundError(
                f"未找到 Edge 浏览器！\n"
                f"请安装 Microsoft Edge 浏览器。\n"
                f"头条发布页面在 Playwright Chromium 中无法完整加载。"
            )
        
        # ★★★ 使用独立的配置文件，避免与系统Edge冲突 ★★★
        user_data_dir = "./edge_profile_toutiao"
        
        logger.info(f"使用 Edge 浏览器: {edge_executable}")
        logger.info(f"使用用户配置文件: {user_data_dir}")
        
        # ★★★ 100% 模拟真实浏览器 ★★★
        self.context = await self.playwright.chromium.launch_persistent_context(
            user_data_dir=user_data_dir,
            headless=False,
            executable_path=edge_executable,
            viewport={"width": 1920, "height": 1080},
            device_scale_factor=1.0,
            locale="zh-CN",
            timezone_id="Asia/Shanghai",
            # ★★★ 真实浏览器的 user-agent ★★★
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
            # ★★★ 真实浏览器的启动参数 ★★★
            args=[
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--window-size=1920,1080',
                '--start-maximized',
                '--disable-blink-features=AutomationControlled',  # 隐藏自动化特征
                '--disable-extensions',  # 禁用扩展避免干扰
                '--disable-plugins',  # 禁用插件
                # ★★★ 关键：不添加任何自动化相关参数 ★★★
            ],
            # ★★★ 忽略自动化参数 ★★★
            ignore_default_args=['--enable-automation'],
        )
        
        # launch_persistent_context 返回的就是 context
        self.browser = self.context
        
        # ★★★ 超强反检测 JavaScript 注入 ★★★
        await self.context.add_init_script("""
            // 1. 隐藏 webdriver（最重要！）
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // 2. 模拟真实的 permissions API
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // 3. 模拟真实的 Chrome 对象
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // 4. 隐藏 Playwright 特征
            delete window.__playwright;
            delete window.__pw_manual;
            delete window.__pw_inspect;
            
            // 5. 模拟真实的插件
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Viewer', filename: 'internal-pdf-viewer' },
                    { name: 'Microsoft Edge PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                ],
            });
            
            // 6. 模拟真实的语言
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en'],
            });
        """)
        
        # 创建新页面
        self.page = await self.context.new_page()
        
        # ★★★ 设置额外的页面属性 ★★★
        await self.page.add_init_script("""
            // 隐藏 Playwright 特征
            delete window.__playwright;
            delete window.__pw_manual;
            delete window.__pw_inspect;
            
            // 模拟真实的屏幕属性
            Object.defineProperty(window.screen, 'availWidth', { get: () => 1920 });
            Object.defineProperty(window.screen, 'availHeight', { get: () => 1040 });
            Object.defineProperty(window.screen, 'width', { get: () => 1920 });
            Object.defineProperty(window.screen, 'height', { get: () => 1080 });
            Object.defineProperty(window.screen, 'colorDepth', { get: () => 24 });
            Object.defineProperty(window.screen, 'pixelDepth', { get: () => 24 });
        """)
        
        logger.info("✅ Edge 浏览器初始化成功（100% 模拟真实浏览器）")
        logger.info(f"头条发布引擎初始化完成，账号 ID: {self.account_id}")

    async def smart_login(self, cookies: str = None) -> bool:
        """
        智能登录：先尝试Cookie，失败后等待用户手动登录
        :param cookies: Cookie字符串（可选）
        :return: 是否登录成功
        """
        logger.info("开始智能登录流程...")
        
        # 步骤 1: 尝试使用 Cookie 登录
        if cookies:
            logger.info("尝试使用保存的 Cookie 登录...")
            try:
                cookie_list = json.loads(cookies)
                await self.context.add_cookies(cookie_list)
                logger.info(f"已加载 {len(cookie_list)} 个 Cookie")
                
                # 访问头条首页检查是否已登录
                await self.page.goto("https://mp.toutiao.com/", timeout=15000, wait_until='domcontentloaded')
                await asyncio.sleep(3)
                
                current_url = self.page.url
                if "profile" in current_url and "login" not in current_url:
                    logger.info("✅ Cookie 登录成功！")
                    return True
                else:
                    logger.warning(f"⚠️  Cookie 失效，当前URL: {current_url}")
            except Exception as e:
                logger.warning(f"Cookie 登录失败: {e}")
        
        # 步顤2: Cookie 失效，需要手动登录
        logger.info("\n👤 Cookie 失效，请手动完成登录...")
        logger.info("💡 提示：可以使用扫码登录或手机号+验证码登录")
        
        # 打开头条首页
        await self.page.goto("https://mp.toutiao.com/", timeout=30000)
        await asyncio.sleep(2)
        
        # 等待用户登录
        login_success = await self.wait_for_user_login(timeout=120)
        
        if login_success:
            logger.info("✅ 手动登录成功！")
            return True
        else:
            logger.error("❌ 登录超时或失败")
            return False
    
    async def wait_for_user_login(self, timeout=120) -> bool:
        """
        等待用户完成登录
        :param timeout: 超时时间（秒）
        :return: 是否登录成功
        """
        start_time = asyncio.get_event_loop().time()
        check_count = 0
        
        while asyncio.get_event_loop().time() - start_time < timeout:
            await asyncio.sleep(2)
            check_count += 1
            
            current_url = self.page.url
            
            # 每10次检查输出一次提示
            if check_count % 10 == 0:
                remaining = int(timeout - (asyncio.get_event_loop().time() - start_time))
                logger.info(f"⏳ 等待登录中... 剩余 {remaining} 秒")
                logger.info(f"   当前URL: {current_url}")
            
            # 检测策略1: URL包含 profile 且不包含 login
            if "profile" in current_url and "login" not in current_url and "sso" not in current_url:
                logger.info(f"✅ 检测到登录成功（URL匹配）")
                return True
            
            # 检测策略2: 检查是否有用户信息元素
            try:
                user_avatar = await self.page.query_selector('img[alt*="头像"], div[class*="avatar"]')
                if user_avatar and await user_avatar.is_visible():
                    if "login" not in current_url:
                        logger.info("✅ 检测到登录成功（用户头像）")
                        return True
            except:
                pass
            
            # 检测策略3: 页面标题变化
            try:
                title = await self.page.title()
                if any(keyword in title for keyword in ['头条号', '工作台', '首页']):
                    if "login" not in current_url:
                        logger.info(f"✅ 检测到登录成功（页面标题: {title}）")
                        return True
            except:
                pass
        
        logger.error(f"❌ 等待登录超时（{timeout}秒）")
        return False

    async def login_with_manual_input(self, username: str, password: str) -> Dict[str, Any]:
        """
        人工辅助登录头条
        流程：
        1. 打开头条登录页
        2. 自动填充账号密码
        3. 等待用户完成验证码/二次验证
        4. 保存登录状态（Cookies）
        """
        try:
            # 1. 打开头条创作者平台（首页会自动重定向到登录页）
            await self.page.goto("https://mp.toutiao.com/", timeout=30000)
            await asyncio.sleep(2)

            # 2. 尝试自动登录
            try:
                # 2.1 先尝试切换到密码登录模式（头条默认是验证码登录）
                logger.info("正在切换到密码登录模式...")
                try:
                    # 点击“密码登录”按钮
                    password_login_btn = await self.page.query_selector('text=密码登录')
                    if password_login_btn:
                        await password_login_btn.click()
                        await asyncio.sleep(2)
                        logger.info("✅ 已切换到密码登录模式")
                    else:
                        logger.info("ℹ️ 未找到密码登录按钮，尝试直接填充")
                except Exception as e:
                    logger.debug(f"切换密码登录模式失败: {e}")
                
                # 2.2 尝试自动填充账号密码
                # ★★★ 关键：自动勾选用户协议 ★★★
                logger.info("正在查找并勾选用户协议...")
                agreement_selectors = [
                    'input[type="checkbox"]',
                    'label:has-text("用户协议")',
                    'label:has-text("我已阅读并同意")',
                    'label:has-text("隐私政策")',
                    '[class*="agree"] input[type="checkbox"]',
                    '[class*="protocol"] input[type="checkbox"]',
                    'input[name*="agree"]',
                    'input[name*="protocol"]',
                    '.agreement-checkbox input[type="checkbox"]'
                ]
                
                agreement_checked = False
                for selector in agreement_selectors:
                    try:
                        agreement_checkbox = await self.page.query_selector(selector)
                        if agreement_checkbox:
                            is_checked = await agreement_checkbox.is_checked()
                            if not is_checked:
                                await agreement_checkbox.check()
                                logger.info("✅ 已自动勾选用户协议")
                            else:
                                logger.info("用户协议已勾选")
                            agreement_checked = True
                            break
                    except Exception as e:
                        logger.debug(f"尝试选择器 {selector} 失败: {e}")
                        continue
                
                if not agreement_checked:
                    logger.warning("⚠️  未找到用户协议复选框，可能需要手动勾选")
                
                # 查找账号输入框（可能是手机号/邮箱）
                username_input = await self.page.query_selector('input[placeholder*="手机号"], input[placeholder*="邮箱"], input[name="account"]')
                if username_input:
                    await username_input.fill(username)
                    await asyncio.sleep(1)
                    logger.info(f"✅ 已填充账号: {username}")
                else:
                    logger.warning("⚠️  未找到账号输入框")
                
                # 查找密码输入框
                password_input = await self.page.query_selector('input[type="password"], input[placeholder*="密码"]')
                if password_input:
                    await password_input.fill(password)
                    await asyncio.sleep(1)
                    logger.info("✅ 已填充密码")
                else:
                    logger.warning("⚠️  未找到密码输入框")

                # 点击登录按钮
                login_button = await self.page.query_selector('button:has-text("登录"), button[type="submit"]')
                if login_button:
                    await login_button.click()
                    logger.info("✅ 已点击登录按钮，等待登录成功...")
                else:
                    logger.warning("⚠️  未找到登录按钮")
                
                # 等待登录成功（检测 URL 变化或特定元素）
                # 头条URL可能是 profile_v4 或 profile/v4
                await self.page.wait_for_url("**/profile*", timeout=60000)
                
            except Exception as e:
                logger.warning(f"自动填充失败，请手动完成登录: {e}")
                # 等待用户手动登录完成
                logger.info("请在浏览器窗口中手动完成登录（扫码或输入账号密码），系统将自动检测登录状态...")
                logger.info("💡 提示：如果需要勾选用户协议，请手动勾选")
                
                # 多种登录成功检测策略
                login_detected = False
                for attempt in range(60):  # 最多等待60次 * 2秒 = 120秒
                    await asyncio.sleep(2)
                    current_url = self.page.url
                    
                    # 🔍 详细调试日志
                    if attempt == 0:
                        logger.info(f"开始检测登录状态...")
                        logger.info(f"初始URL: {current_url}")
                    
                    # 检测策略1: URL包含 profile（支持 profile_v4, profile/v4, profile 等格式）
                    if "profile" in current_url or "profile_v" in current_url:
                        login_detected = True
                        logger.info(f"✅ 检测到登录成功（策略1-URL匹配）: {current_url}")
                        break
                    
                    # 检测策略2: URL不包含 login/sso/register
                    if "login" not in current_url and "sso" not in current_url and "register" not in current_url:
                        # 进一步检查是否有用户信息元素
                        try:
                            user_avatar = await self.page.query_selector('img[alt*="头像"], div[class*="avatar"], .user-avatar')
                            if user_avatar:
                                login_detected = True
                                logger.info(f"✅ 检测到登录成功（策略2-用户头像）: {current_url}")
                                break
                        except Exception as e:
                            logger.debug(f"头像检测异常: {e}")
                    
                    # 检测策略3: 检查Cookie中是否有登录态
                    try:
                        cookies = await self.context.cookies()
                        login_cookies = [c for c in cookies if 'session' in c.get('name', '').lower() or 'token' in c.get('name', '').lower()]
                        if login_cookies and "login" not in current_url:
                            login_detected = True
                            logger.info(f"✅ 检测到登录成功（策略3-Cookie存在）: {len(login_cookies)} 个登录Cookie")
                            break
                    except Exception as e:
                        logger.debug(f"Cookie检测异常: {e}")
                    
                    # 检测策略4: 页面标题包含“头条号”或“工作台”等关键词
                    try:
                        page_title = await self.page.title()
                        if any(keyword in page_title for keyword in ['头条号', '工作台', '首页', '管理']):
                            if "login" not in current_url and "sso" not in current_url:
                                login_detected = True
                                logger.info(f"✅ 检测到登录成功（策略4-页面标题）: {page_title}")
                                break
                    except Exception as e:
                        logger.debug(f"标题检测异常: {e}")
                    
                    # 每10次输出一次提示
                    if (attempt + 1) % 10 == 0:
                        logger.info(f"⏳ 等待登录中... ({attempt + 1}/60)，当前URL: {current_url}")
                        logger.info(f"   页面标题: {await self.page.title()}")
                
                if not login_detected:
                    # 输出详细调试信息
                    logger.error("❌ 等待登录超时！")
                    logger.error(f"最终URL: {self.page.url}")
                    logger.error(f"页面标题: {await self.page.title()}")
                    
                    try:
                        cookies = await self.context.cookies()
                        logger.error(f"Cookie数量: {len(cookies)}")
                        if cookies:
                            logger.error("Cookie列表:")
                            for cookie in cookies[:5]:  # 只显示前5个
                                logger.error(f"  - {cookie.get('name')}: {cookie.get('value', '')[:50]}...")
                    except Exception as e:
                        logger.error(f"获取Cookie失败: {e}")
                    
                    raise TimeoutError("等待登录超时，请确认是否已完成扫码/登录操作")

            # 3. 保存登录状态
            cookies = await self.context.cookies()
            cookies_json = json.dumps(cookies)
            
            logger.info(f"头条账号 {username} 登录成功！")
            logger.info(f"当前URL: {self.page.url}")
            logger.info(f"已保存 {len(cookies)} 个 Cookie")
            
            return {
                "status": "success",
                "cookies": cookies_json,
                "message": "登录成功，已保存会话状态"
            }

        except Exception as e:
            logger.error(f"头条登录失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def publish_article(
        self,
        title: str,
        content: str,
        category: str = "科技",
        tags: list = None,
        cover_image_path: str = None,
        auto_generate_cover: bool = False,
        cover_style: str = "modern",
        use_template: str = None,
        enable_ab_test: bool = False,
        declaration_type: str = "ai",  # 新增参数：声明类型，"ai"=引用AI, "personal_opinion"=仅个人观点
        article_images: list = None  # 新增参数：文章配图路径列表
    ) -> Dict[str, Any]:
        """
        发布头条文章（支持高级封面图功能）
        
        :param title: 文章标题
        :param content: 文章内容
        :param category: 文章分类
        :param tags: 标签列表
        :param cover_image_path: 封面图片路径（可选）
        :param auto_generate_cover: 是否自动生成封面图
        :param cover_style: AI生成风格 (modern/minimal/bold)
        :param use_template: 使用的模板ID
        :param enable_ab_test: 是否启用A/B测试
        :param declaration_type: 声明类型
        :param article_images: 文章配图路径列表（可选）
        """
        try:
            if not self.page:
                await self.initialize_browser()

            # 1. 进入文章发布页
            # ★★★ 尝试不同的URL ★★★
            publish_url = "https://mp.toutiao.com/profile_v4/graphic/publish"
            logger.info(f"正在打开发布页面: {publish_url}")
            
            # ★★★ 智能跳转逻辑：先检查当前页面，避免导航冲突（参考 test_cdp_auto_publish.py）★★★
            current_url = self.page.url
            logger.info(f"   当前URL: {current_url}")
            
            if "profile_v4/graphic/publish" not in current_url:
                logger.info("   正在跳转到发布页面...")
                try:
                    await self.page.goto(publish_url, timeout=60000, wait_until='domcontentloaded')
                except Exception as e:
                    # 如果跳转被中断（例如重定向），通常意味着已经在目标页面或正在跳转
                    if "interrupted" in str(e) or "navigation" in str(e).lower():
                        logger.warning("   ⚠️  导航冲突（可能正在自动跳转），等待页面稳定...")
                    else:
                        raise e
            else:
                logger.info("   ✅ 已在发布页面")
            
            # 等待页面完全稳定
            logger.info("   等待页面完全加载...")
            await asyncio.sleep(10)
            
            # 再次检查URL
            final_url = self.page.url
            logger.info(f"   最终URL: {final_url}")
            
            # 验证页面加载状态（参考 test_cdp_auto_publish.py）
            logger.info("   验证页面加载状态...")
            page_info = await self.page.evaluate("""
                () => {
                    const editor = document.querySelector('div[contenteditable="true"]');
                    const titleInput = document.querySelector('input[placeholder*="标题"]');
                    
                    let publishBtn = null;
                    document.querySelectorAll('button').forEach(btn => {
                        if (btn.textContent.includes('预览并发布')) publishBtn = btn;
                    });
                    
                    return {
                        editor: !!editor,
                        title: !!titleInput,
                        button: !!publishBtn,
                        url: window.location.href
                    };
                }
            """)
            
            logger.info(f"   编辑器: {'✅' if page_info['editor'] else '❌'}")
            logger.info(f"   标题框: {'✅' if page_info['title'] else '❌'}")
            logger.info(f"   发布按钮: {'✅' if page_info['button'] else '❌'}")
            
            if not page_info['editor'] or not page_info['button']:
                logger.warning("⚠️  页面未完整加载，可能需要手动检查")
                # 保存调试信息
                try:
                    debug_html = f"logs/toutiao_page_load_{int(asyncio.get_event_loop().time())}.html"
                    with open(debug_html, 'w', encoding='utf-8') as f:
                        f.write(await self.page.content())
                    logger.info(f"📄 页面HTML已保存: {debug_html}")
                except:
                    pass
            
            # ★★★ 滚动到编辑器位置 ★★★
            logger.info("  滚动到编辑器位置...")
            await self.page.evaluate("""
                () => {
                    const editor = document.querySelector('div[contenteditable="true"]');
                    if (editor) {
                        editor.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            """)
            await asyncio.sleep(2)
            logger.info("  ✅ 已滚动到编辑器")
            
            # 检查是否需要登录
            current_url = self.page.url
            if "login" in current_url or "sso" in current_url:
                logger.warning("检测到未登录状态，请先执行登录")
                return {
                    "status": "failed",
                    "error": "未登录，请先调用 login_with_manual_input 方法"
                }
            
            logger.info(f"发布页面已加载，当前URL: {current_url}")

            # 2. 填写标题
            title_input = await self.page.query_selector('input[placeholder="请输入标题"]')
            if not title_input:
                title_input = await self.page.query_selector('textarea[placeholder*="标题"]')
            
            if title_input:
                await title_input.fill(title)
                await asyncio.sleep(1)
                logger.info(f"标题已填写: {title}")

            # 3. 填写正文（富文本编辑器）
            # 头条使用富文本编辑器，需要定位编辑器区域
            editor = await self.page.query_selector('div[contenteditable="true"]')
            if not editor:
                editor = await self.page.query_selector('div.toutiao-editor')
            
            if editor:
                await editor.fill(content)
                await asyncio.sleep(2)
                logger.info(f"正文已填写，长度: {len(content)} 字")

            # 4. 选择分类
            if category:
                try:
                    category_select = await self.page.query_selector('select, div[class*="category"]')
                    if category_select:
                        await category_select.click()
                        await asyncio.sleep(1)
                        # 选择对应分类
                        await self.page.click(f'text={category}', timeout=5000)
                        await asyncio.sleep(1)
                        logger.info(f"分类已选择: {category}")
                except Exception as e:
                    logger.warning(f"分类选择失败，使用默认分类: {e}")

            # 5. 添加标签
            if tags:
                try:
                    tag_input = await self.page.query_selector('input[placeholder*="标签"]')
                    if tag_input:
                        for tag in tags[:5]:  # 最多 5 个标签
                            await tag_input.fill(tag)
                            await self.page.keyboard.press('Enter')
                            await asyncio.sleep(0.5)
                        logger.info(f"标签已添加: {tags}")
                except Exception as e:
                    logger.warning(f"标签添加失败: {e}")

            # 5.5 ★★★ 插入文章配图（在填写正文后、处理封面图前）★★★
            if article_images:
                logger.info("\n=== 开始插入文章配图 ===")
                await self._insert_article_images(article_images)
                logger.info("=== 文章配图插入完成 ===\n")
            
            # 6. ★★★ 处理封面图（关键！）★★★
            logger.info("正在检查封面图...")
            try:
                # 如果需要自动生成封面图
                if auto_generate_cover and not cover_image_path:
                    logger.info("🤖 开始AI生成封面图...")
                                            
                    # ★★★ 使用LLM智能分析文章内容生成封面图（优先）★★★
                    try:
                        from app.services.content.llm_cover_generator import get_llm_cover_generator
                        llm_generator = get_llm_cover_generator()
                                                
                        result = llm_generator.generate_cover_with_llm_analysis(
                            title=title,
                            content=content,  # 传入文章内容用于LLM分析
                            category=category,
                            style_override=cover_style if cover_style else None
                        )
                                                
                        if result["status"] == "success":
                            cover_image_path = result["file_path"]
                            design_plan = result.get("design_plan", {})
                            logger.info(f"✅ LLM智能封面生成成功!")
                            logger.info(f"   视觉风格: {design_plan.get('visual_style', 'N/A')}")
                            logger.info(f"   配色方案: {design_plan.get('color_scheme', 'N/A')}")
                            logger.info(f"   关键词: {design_plan.get('keywords', [])}")
                        else:
                            logger.warning(f"⚠️  LLM封面生成失败: {result.get('error')}")
                            logger.info("   降级使用传统模板生成...")
                            raise Exception("LLM封面生成失败")
                    except Exception as e:
                        logger.warning(f"LLM封面生成异常: {e}，尝试其他方法...")
                                    
                        # 降级方案1: 如果使用模板
                        if use_template:
                            from app.services.content.cover_template_library import get_template_library
                            library = get_template_library()
                                                    
                            result = library.generate_cover_from_template(
                                template_id=use_template,
                                title=title,
                                subtitle=""
                            )
                                                    
                            if result["status"] == "success":
                                cover_image_path = result["file_path"]
                                logger.info(f"✅ 使用模板生成封面: {result['template_name']}")
                            else:
                                logger.warning(f"⚠️  模板生成失败: {result.get('error')}")
                        else:
                            # 降级方案2: 使用传统AI生成（PIL图形）
                            from app.services.content.ai_cover_generator import AICoverGenerator
                            generator = AICoverGenerator()
                                                    
                            result = generator.generate_cover(
                                title=title,
                                subtitle="",
                                category=category,
                                style=cover_style
                            )
                                                    
                            if result["status"] == "success":
                                cover_image_path = result["file_path"]
                                logger.info(f"✅ 传统AI生成封面成功: {result['style']} 风格")
                            else:
                                logger.warning(f"⚠️  AI生成失败: {result.get('error')}")
                                        
                # 如果提供了封面图路径，先压缩优化
                if cover_image_path:
                    logger.info("📦 优化封面图...")
                    from app.utils.image_processor import ImageProcessor
                    processor = ImageProcessor()
                                            
                    # 压缩图片
                    compress_result = processor.compress_image(
                        input_path=cover_image_path,
                        quality=85,
                        max_width=1920,
                        max_height=1080,
                        output_format='jpg'
                    )
                                            
                    if compress_result["status"] == "success":
                        cover_image_path = compress_result["output_path"]
                        logger.info(f"✅ 封面图压缩完成: {compress_result['compression_ratio_percent']}% 压缩率")
                    else:
                        logger.warning(f"⚠️  压缩失败，使用原图: {compress_result.get('error')}")
                            
                # ★★★ 无论是否提供封面图，都先选择“单图”模式 ★★★
                logger.info("📸 开始设置封面图模式...")
                await self._select_single_image_mode()
                            
                # ★★★ CDP模式优化：参考 test_cdp_auto_publish.py ★★★
                if cover_image_path:
                    await self._upload_cover_with_cdp_optimization(cover_image_path)
                else:
                    logger.info("ℹ️  未提供封面图，将使用默认或无封面模式")
                                
            except Exception as e:
                logger.warning(f"处理封面图时出错: {e}")
                import traceback
                traceback.print_exc()
                            
                # 查找“无封面”或“上传封面”按钮
                cover_selectors = [
                    'div:has-text("无封面")',
                    'span:has-text("无封面")',
                    'div:has-text("上传封面")',
                    'button:has-text("上传")',
                    '[class*="cover"] button'
                ]
                                        
                cover_btn = None
                for selector in cover_selectors:
                    try:
                        cover_btn = await self.page.query_selector(selector)
                        if cover_btn and await cover_btn.is_visible():
                            logger.info(f"✅ 找到封面图按钮: {selector}")
                            break
                    except:
                        continue
                                        
                if cover_btn:
                    # 点击封面图按钮
                    await cover_btn.click()
                    await asyncio.sleep(2)
                    logger.info("✅ 已点击封面图按钮")
                                            
                    # 如果提供了自定义封面图路径，则上传
                    if cover_image_path:
                        logger.info(f"正在上传自定义封面图: {cover_image_path}")
                                                
                        # 等待上传对话框出现
                        await asyncio.sleep(2)
                                                
                        # 查找文件上传input元素
                        file_input_selectors = [
                            'input[type="file"]',
                            'input[accept*="image"]',
                            '[class*="upload"] input[type="file"]'
                        ]
                                                
                        file_input = None
                        for selector in file_input_selectors:
                            try:
                                file_input = await self.page.query_selector(selector)
                                if file_input:
                                    logger.info(f"✅ 找到文件上传元素: {selector}")
                                    break
                            except:
                                continue
                                                
                        if file_input:
                            # 上传封面图
                            await file_input.set_input_files(cover_image_path)
                            logger.info("✅ 封面图文件已选择")
                                                    
                            # 等待上传完成
                            await asyncio.sleep(5)
                            logger.info("✅ 封面图上传完成")
                                                    
                            # 尝试点击确认按钮
                            try:
                                confirm_selectors = [
                                    'button:has-text("确定")',
                                    'button:has-text("确认")',
                                    'button:has-text("完成")'
                                ]
                                                        
                                for confirm_selector in confirm_selectors:
                                    confirm_btn = await self.page.query_selector(confirm_selector)
                                    if confirm_btn and await confirm_btn.is_visible():
                                        await confirm_btn.click()
                                        await asyncio.sleep(2)
                                        logger.info(f"✅ 已点击确认按钮: {confirm_selector}")
                                        break
                            except Exception as e:
                                logger.warning(f"未找到确认按钮或已自动确认: {e}")
                        else:
                            logger.warning("⚠️  未找到文件上传元素，使用默认封面")
                    else:
                        # 没有提供自定义封面，尝试选择第一张图片或使用默认
                        logger.info("ℹ️  未提供自定义封面图，使用默认封面")
                        try:
                            first_image = await self.page.query_selector('img:first-of-type, .image-item:first-child')
                            if first_image:
                                await first_image.click()
                                await asyncio.sleep(1)
                                logger.info("✅ 已选择默认封面图")
                            else:
                                # 如果没有图片，尝试点击“确定”或“关闭”
                                confirm_btn = await self.page.query_selector('button:has-text("确定"), button:has-text("关闭")')
                                if confirm_btn:
                                    await confirm_btn.click()
                                    await asyncio.sleep(1)
                                    logger.info("⚠️  使用默认封面或跳过封面选择")
                        except Exception as e:
                            logger.warning(f"选择封面图失败: {e}")
                else:
                    logger.info("ℹ️  未找到封面图按钮，可能已有封面或非必填")
            except Exception as e:
                logger.warning(f"处理封面图时出错: {e}")

            # 6. ★★★ 设置作品声明（根据declaration_type参数）★★★
            await self._set_declaration(declaration_type)
            await asyncio.sleep(2)
            
            # 7. 点击发布按钮
            logger.info("正在查找发布按钮...")
            publish_selectors = [
                'button:has-text("预览并发布")',  # ★★★ 头条实际按钮文字 ★★★
                'button:has-text("发布")',
                'button.publish-btn',
                'button[type="submit"]',
                'button[class*="publish"]',
                'button[class*="btn"]:has-text("发布")',
                '.byte-btn:has-text("发布")',
                '.byte-btn:has-text("预览并发布")',  # ★★★ 头条样式 ★★★
                'a:has-text("发布")'
            ]
            
            publish_button = None
            for selector in publish_selectors:
                try:
                    publish_button = await self.page.query_selector(selector)
                    if publish_button and await publish_button.is_visible():
                        logger.info(f"✅ 找到发布按钮: {selector}")
                        break
                    else:
                        logger.debug(f"选择器 {selector} 找到元素但不可见")
                except Exception as e:
                    logger.debug(f"选择器 {selector} 失败: {e}")
            
            if not publish_button:
                logger.error("❌ 未找到发布按钮！")
                logger.error("页面URL:", self.page.url)
                
                # 保存当前页面HTML用于调试
                try:
                    debug_html = f"logs/toutiao_no_button_{int(asyncio.get_event_loop().time())}.html"
                    with open(debug_html, 'w', encoding='utf-8') as f:
                        f.write(await self.page.content())
                    logger.info(f"📄 页面HTML已保存: {debug_html}")
                except Exception as e:
                    logger.warning(f"保存HTML失败: {e}")
                
                # 列出页面上所有的button
                try:
                    all_buttons = await self.page.query_selector_all('button, a[class*="btn"]')
                    logger.info(f"页面上找到 {len(all_buttons)} 个按钮/链接")
                    for i, btn in enumerate(all_buttons[:10]):
                        text = await btn.text_content()
                        class_name = await btn.get_attribute('class')
                        logger.info(f"  [{i}] text='{text.strip()[:30]}', class={class_name}")
                except Exception as e:
                    logger.warning(f"无法获取按钮列表: {e}")
                
                return {
                    "status": "failed",
                    "error": "未找到发布按钮，请检查页面是否正常加载"
                }
            
            logger.info("✅ 发布按钮已找到，准备点击")
            
            # ★★★ 发布前保存HTML和截图 ★★★
            try:
                pre_publish_html = f"logs/toutiao_pre_publish_{int(asyncio.get_event_loop().time())}.html"
                with open(pre_publish_html, 'w', encoding='utf-8') as f:
                    f.write(await self.page.content())
                logger.info(f"📄 发布前HTML已保存: {pre_publish_html}")
                
                pre_publish_screenshot = f"logs/toutiao_pre_publish_{int(asyncio.get_event_loop().time())}.png"
                await self.page.screenshot(path=pre_publish_screenshot, full_page=True)
                logger.info(f"📸 发布前截图: {pre_publish_screenshot}")
            except Exception as e:
                logger.warning(f"保存发布前状态失败: {e}")
            
            # ★★★ 监听网络请求 ★★★
            publish_request_detected = False
            response_status = None
            
            def handle_response(response):
                nonlocal publish_request_detected, response_status
                url = response.url
                if any(keyword in url.lower() for keyword in ['publish', 'save', 'submit', 'article']):
                    publish_request_detected = True
                    response_status = response.status
                    logger.info(f"🌐 检测到发布请求: {url} (状态码: {response_status})")
            
            self.page.on("response", handle_response)
            
            # 记录当前URL
            before_url = self.page.url
            logger.info(f"点击发布前URL: {before_url}")
            
            # 点击发布按钮
            await publish_button.click()
            logger.info("✅ 已点击发布按钮，等待响应...")
            
            # 等待网络请求和页面变化
            await asyncio.sleep(5)
            
            # 检查是否有网络请求
            if publish_request_detected:
                logger.info(f"✅ 检测到发布网络请求，响应状态: {response_status}")
            else:
                logger.warning("⚠️  未检测到发布相关的网络请求！")
            
            # 检查URL是否变化
            after_url = self.page.url
            logger.info(f"点击发布后URL: {after_url}")
            url_changed = before_url != after_url
            
            if url_changed:
                logger.info(f"✅ URL发生变化: {before_url} -> {after_url}")
            else:
                logger.warning("⚠️  URL未变化，可能发布失败")

            # ★★★ 检查是否有确认弹窗（从页面底部查找）★★★
            try:
                logger.info("   查找'确认发布'按钮...")
                confirm_clicked = await self.page.evaluate("""
                    () => {
                        // 从截图看，确认发布按钮在页面底部，不在模态框中
                        // 直接查找所有包含"确认发布"文本的按钮
                        const allButtons = document.querySelectorAll('button, [role="button"], .byte-btn');
                        
                        for (const btn of allButtons) {
                            const text = btn.textContent?.trim();
                            console.log('检查按钮:', text);
                            
                            if (text === '确认发布') {
                                btn.click();
                                console.log('已点击确认发布按钮');
                                return true;
                            }
                        }
                        
                        // 如果没找到，尝试查找包含"确认"的按钮
                        for (const btn of allButtons) {
                            const text = btn.textContent?.trim();
                            if (text.includes('确认')) {
                                btn.click();
                                console.log('已点击包含确认的按钮:', text);
                                return true;
                            }
                        }
                        
                        // 最后尝试：查找模态框中的按钮
                        const modals = document.querySelectorAll('.byte-modal, .modal, [role="dialog"], .confirm-dialog');
                        for (const modal of modals) {
                            const buttons = modal.querySelectorAll('button, [role="button"], .byte-btn');
                            for (const btn of buttons) {
                                const text = btn.textContent?.trim();
                                if (text && (text.includes('确认') || text.includes('确定') || text === '发布')) {
                                    btn.click();
                                    return true;
                                }
                            }
                            if (buttons.length > 0) {
                                buttons[buttons.length - 1].click();
                                return true;
                            }
                        }
                        
                        return false;
                    }
                """)
                
                if confirm_clicked:
                    logger.info("✅ 已点击'确认发布'按钮")
                    await asyncio.sleep(2)
                else:
                    logger.info("⚠️  未找到确认按钮，可能不需要二次确认")
            except Exception as e:
                logger.debug(f"未找到确认弹窗或已自动确认: {e}")
            
            # ★★★ 发布后截图 ★★★
            try:
                post_publish_screenshot = f"logs/toutiao_post_publish_{int(asyncio.get_event_loop().time())}.png"
                await self.page.screenshot(path=post_publish_screenshot, full_page=True)
                logger.info(f"📸 发布后截图: {post_publish_screenshot}")
            except Exception as e:
                logger.warning(f"截图失败: {e}")

            # 等待发布成功提示（更严格的检测）
            success_detected = False
            success_message = ""
            try:
                # 只检测明确的发布成功提示，避免误判
                success_selectors = [
                    'text=发布成功',
                    'text=发表成功',
                    '.ant-message-success:has-text("发布")',
                    '[class*="message"][class*="success"]:has-text("发布")',
                    'div[role="alert"]:has-text("发布成功")'
                ]
                
                for selector in success_selectors:
                    try:
                        elem = await self.page.wait_for_selector(selector, timeout=8000)
                        if elem:
                            success_message = await elem.text_content()
                            # 验证确实包含“发布”相关关键词
                            if any(keyword in success_message for keyword in ['发布', '发表', '文章']):
                                success_detected = True
                                logger.info(f"✅ 检测到发布成功提示: {selector}")
                                logger.info(f"   提示内容: {success_message}")
                                break
                    except:
                        continue
            except Exception as e:
                logger.warning(f"等待成功提示超时: {e}")
            
            # 检查是否有错误提示
            error_detected = False
            error_message = ""
            try:
                # 更精确的错误选择器，避免误判
                error_selectors = [
                    '.ant-message-error',  # Ant Design 错误消息
                    '.error-toast',
                    '[class*="message"][class*="error"]',
                    'div[role="alert"][class*="error"]'
                ]
                
                for selector in error_selectors:
                    error_elem = await self.page.query_selector(selector)
                    if error_elem and await error_elem.is_visible():
                        error_message = await error_elem.text_content()
                        error_detected = True
                        logger.warning(f"⚠️  检测到错误提示: {error_message}")
                        break
            except Exception as e:
                logger.debug(f"检查错误提示时出错: {e}")
            
            # 综合判断发布状态
            if success_detected:
                logger.info(f"✅ 头条文章发布成功！标题: {title}")
                return {
                    "status": "success",
                    "title": title,
                    "message": "文章发布成功"
                }
            elif error_detected:
                logger.error(f"❌ 发布失败: {error_message}")
                return {
                    "status": "failed",
                    "error": f"发布失败: {error_message}"
                }
            else:
                # 没有明确的成功/失败提示，根据其他指标判断
                current_url = self.page.url
                logger.info(f"当前URL: {current_url}")
                
                # 指标1: 是否有网络请求
                # 指标2: URL是否变化
                # 指标3: 是否仍在发布页面
                
                if "draft" in current_url or "edit" in current_url:
                    logger.warning("⚠️  仍在编辑页面，文章可能被保存为草稿")
                    return {
                        "status": "draft",
                        "title": title,
                        "message": "文章已保存为草稿，请在头条后台手动发布"
                    }
                elif "publish" in current_url and not url_changed:
                    logger.error("❌ 仍停留在发布页面且URL未变化，发布可能失败")
                    return {
                        "status": "failed",
                        "error": "发布操作未完成，仍停留在发布页面。请检查表单是否填写完整"
                    }
                elif publish_request_detected and response_status == 200:
                    logger.info("✅ 检测到成功的网络请求，但无明确提示，可能发布成功")
                    return {
                        "status": "pending",
                        "title": title,
                        "message": "发布请求已发送，请检查头条后台确认状态"
                    }
                else:
                    logger.warning("⚠️  无法确定发布状态")
                    logger.warning(f"   - 网络请求: {'有' if publish_request_detected else '无'}")
                    logger.warning(f"   - URL变化: {'是' if url_changed else '否'}")
                    logger.warning(f"   - 响应状态: {response_status}")
                    return {
                        "status": "failed",
                        "error": "发布状态不明确，请查看日志和截图分析原因"
                    }

        except Exception as e:
            logger.error(f"头条文章发布失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def _select_single_image_mode(self):
        """
        选择“单图”模式（无论是否提供封面图）
        """
        logger.info("   步骤1：选择'单图'模式...")
            
        single_image_selected = False
            
        # ★★★ 方案0：先检查当前是否已经选择了“单图” ★★★
        try:
            current_mode = await self.page.evaluate("""
                () => {
                    const radios = document.querySelectorAll('input[type="radio"]');
                    for (const radio of radios) {
                        const parent = radio.parentElement;
                        if (parent && parent.textContent.includes('单图')) {
                            return radio.checked ? '单图已选中' : '单图未选中';
                        }
                    }
                    return '未找到单图选项';
                }
            """)
            logger.info(f"   当前状态: {current_mode}")
            if current_mode == '单图已选中':
                logger.info("   ✅ '单图'模式已经选中，无需操作")
                return True
        except Exception as e:
            logger.debug(f"   检查当前状态失败: {e}")
            
        # 方案1：使用 Playwright 的 text 选择器点击“单图”（最可靠）
        try:
            logger.info("   尝试方案1：text 选择器...")
            await self.page.click('text="单图"', timeout=5000)
            logger.info("   ✅ 已通过 text 选择器选择'单图'")
            single_image_selected = True
            await asyncio.sleep(2)
        except Exception as e:
            logger.debug(f"   ⚠️  text 选择器失败: {e}")
            
        # 方案2：使用 JavaScript 查找并点击 radio button
        if not single_image_selected:
            logger.info("   尝试方案2：JavaScript radio button...")
            js_result = await self.page.evaluate("""
                () => {
                    // 查找所有 radio button
                    const radios = document.querySelectorAll('input[type="radio"]');
                    console.log(`找到 ${radios.length} 个 radio button`);
                        
                    for (const radio of radios) {
                        const parent = radio.parentElement;
                        if (parent) {
                            const text = parent.textContent || '';
                            console.log(`检查 radio: ${text.substring(0, 50)}`);
                                
                            if (text.includes('单图')) {
                                console.log('找到单图 radio');
                                // 检查是否已经选中
                                if (!radio.checked) {
                                    // 触发完整的鼠标事件序列
                                    const mouseDown = new MouseEvent('mousedown', { bubbles: true });
                                    radio.dispatchEvent(mouseDown);
                                        
                                    const click = new MouseEvent('click', { bubbles: true });
                                    radio.dispatchEvent(click);
                                        
                                    const mouseUp = new MouseEvent('mouseup', { bubbles: true });
                                    radio.dispatchEvent(mouseUp);
                                        
                                    // 触发 change 事件
                                    const change = new Event('change', { bubbles: true });
                                    radio.dispatchEvent(change);
                                        
                                    console.log('已点击单图 radio');
                                } else {
                                    console.log('单图 radio 已经选中');
                                }
                                return 'clicked_radio';
                            }
                        }
                    }
                    console.log('未找到单图 radio');
                    return 'not_found';
                }
            """)
                
            if js_result == 'clicked_radio':
                logger.info("   ✅ 已通过 JavaScript 选择'单图' (radio button)")
                single_image_selected = True
                await asyncio.sleep(2)
            
        # 方案3：查找包含“单图”文本的元素并点击
        if not single_image_selected:
            logger.info("   尝试方案3：查找元素并点击...")
            js_result = await self.page.evaluate("""
                () => {
                    // 查找所有包含“单图”文本的元素
                    const allElements = document.querySelectorAll('*');
                    for (const el of allElements) {
                        const text = el.textContent?.trim();
                        if (text === '单图') {
                            console.log('找到单图文本元素');
                            // 直接点击元素
                            el.click();
                            return 'clicked_element';
                        }
                    }
                    console.log('未找到单图文本元素');
                    return 'not_found';
                }
            """)
                
            if js_result == 'clicked_element':
                logger.info("   ✅ 已通过 JavaScript 选择'单图' (element)")
                single_image_selected = True
                await asyncio.sleep(2)
            else:
                logger.warning("   ❌ 无法选择'单图'模式")
            
        # 验证是否成功选择
        if single_image_selected:
            verification = await self.page.evaluate("""
                () => {
                    const radios = document.querySelectorAll('input[type="radio"]');
                    for (const radio of radios) {
                        const parent = radio.parentElement;
                        if (parent && parent.textContent.includes('单图')) {
                            return radio.checked ? '已选中' : '未选中';
                        }
                    }
                    return '未找到';
                }
            """)
            logger.info(f"   验证状态: {verification}")
            if verification == '已选中':
                logger.info("   ✅ '单图'模式选择成功！")
            else:
                logger.warning(f"   ⚠️  '单图'模式可能未正确选择: {verification}")
            
        return single_image_selected
    
    async def _upload_cover_with_cdp_optimization(self, cover_image_path: str):
        """
        CDP优化的封面图上传（参考 test_cdp_auto_publish.py）
            
        :param cover_image_path: 封面图片路径
        """
        logger.info("📸 开始设置封面图（CDP优化模式）...")
            
        try:
            # 步骤1：滚动到封面图区域
            await self.page.evaluate("""
                () => {
                    const coverSection = document.querySelector('[class*="封面"]') || 
                                        Array.from(document.querySelectorAll('div')).find(d => d.textContent.includes('展示封面'));
                    if (coverSection) {
                        coverSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            """)
            await asyncio.sleep(2)
                
            # 步骤2：选择"单图"模式
            logger.info("   步骤1：选择'单图'模式...")
                
            single_image_selected = False
                
            # 方案1：使用 Playwright 的 text 选择器
            try:
                await self.page.click('text="单图"', timeout=5000)
                logger.info("   ✅ 已通过 text 选择器选择'单图'")
                single_image_selected = True
                await asyncio.sleep(2)
            except Exception as e:
                logger.debug(f"   text 选择器失败: {e}")
                
            # 方案2：使用 JavaScript 查找并点击 radio button
            if not single_image_selected:
                js_result = await self.page.evaluate("""
                    () => {
                        const radios = document.querySelectorAll('input[type="radio"]');
                        for (const radio of radios) {
                            const parent = radio.parentElement;
                            if (parent && parent.textContent.includes('单图')) {
                                if (!radio.checked) {
                                    radio.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                                    radio.dispatchEvent(new Event('change', { bubbles: true }));
                                }
                                return 'clicked';
                            }
                        }
                        return 'not_found';
                    }
                """)
                    
                if js_result == 'clicked':
                    logger.info("   ✅ 已通过 JavaScript 选择'单图'")
                    single_image_selected = True
                    await asyncio.sleep(2)
                
            # 步骤3：点击"+"区域触发上传对话框
            if single_image_selected:
                logger.info("   步骤2：点击封面上传区域...")
                    
                try:
                    # 点击包含"+"和"预览"的区域
                    click_result = await self.page.evaluate("""
                        () => {
                            const allDivs = Array.from(document.querySelectorAll('div'));
                            for (const div of allDivs) {
                                const text = div.textContent || '';
                                // 查找包含"+"和"预览"文字的区域
                                if (text.includes('+') && text.includes('预览') && div.children.length < 10) {
                                    div.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                        
                    if click_result:
                        logger.info("   ✅ 已点击封面上传区域，等待对话框打开...")
                        await asyncio.sleep(3)
                            
                        # 步骤4：在对话框中查找file input并上传
                        logger.info("   步骤3：上传封面图文件...")
                            
                        # 等待对话框出现
                        try:
                            file_input = await self.page.wait_for_selector('input[type="file"]', timeout=5000)
                                
                            if file_input:
                                await self.page.locator('input[type="file"]').first.set_input_files(cover_image_path)
                                logger.info("   ✅ 封面图已上传")
                                await asyncio.sleep(3)
                                    
                                # 等待上传完成，可能需要点击确认按钮
                                try:
                                    confirm_selectors = ['text="确定"', 'text="确认"', 'text="完成"']
                                    for selector in confirm_selectors:
                                        try:
                                            confirm_btn = await self.page.query_selector(selector)
                                            if confirm_btn and await confirm_btn.is_visible():
                                                await confirm_btn.click()
                                                logger.info("   ✅ 已点击确认按钮")
                                                await asyncio.sleep(2)
                                                break
                                        except:
                                            continue
                                except Exception as e:
                                    logger.info("   ℹ️  未找到确认按钮，可能已自动关闭")
                            else:
                                logger.warning("   ⚠️  未找到文件上传元素")
                        except Exception as e:
                            logger.warning(f"   ⚠️  等待file input超时: {e}")
                    else:
                        logger.warning("   ⚠️  未找到封面上传区域")
                            
                except Exception as e:
                    logger.warning(f"   ⚠️  上传过程出错: {e}")
            else:
                logger.warning("   ⚠️  未能选择单图模式")
                
            logger.info("✅ 封面图设置完成")
                
        except Exception as e:
            logger.warning(f"⚠️  封面图设置失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def _insert_article_images(self, image_paths: list):
        """
        插入文章配图到富文本编辑器（完全复用成功测试脚本的逻辑）
        
        :param image_paths: 图片路径列表
        """
        if not image_paths:
            logger.info("ℹ️  未提供文章配图")
            return
        
        logger.info(f"📸 开始插入文章配图，共 {len(image_paths)} 张...")
        
        try:
            # 滚动到编辑器位置
            await self.page.evaluate("""
                () => {
                    const editor = document.querySelector('div[contenteditable="true"]');
                    if (editor) {
                        editor.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            """)
            await asyncio.sleep(2)
            
            for idx, img_path in enumerate(image_paths, 1):
                logger.info(f"   步骤{idx}/{len(image_paths)}：上传配图 '{img_path}'...")
                
                # 转换为绝对路径
                import os
                abs_img_path = os.path.abspath(img_path)
                
                # ★★★ 第一步：点击编辑器的图片按钮（第12个工具栏按钮）★★★
                logger.info(f"      步骤 1：点击编辑器图片按钮...")
                
                # 先关闭可能存在的对话框
                await self.page.evaluate("""
                    () => {
                        // 发送Escape键关闭可能的弹窗
                        const event = new KeyboardEvent('keydown', {
                            key: 'Escape',
                            code: 'Escape',
                            bubbles: true
                        });
                        document.dispatchEvent(event);
                    }
                """)
                await asyncio.sleep(1)
                
                # 关闭可能存在的图片选择抽屉
                await self.page.evaluate("""
                    () => {
                        const drawers = document.querySelectorAll('.byte-drawer-wrapper, .upload-image-panel');
                        drawers.forEach(drawer => {
                            drawer.style.display = 'none';
                            drawer.style.visibility = 'hidden';
                            drawer.style.pointerEvents = 'none';
                        });
                    }
                """)
                await asyncio.sleep(1)
                
                # 查找并点击第12个工具栏按钮（图片按钮）
                toolbar_buttons = await self.page.query_selector_all('.syl-toolbar-button')
                logger.info(f"      找到 {len(toolbar_buttons)} 个工具栏按钮")
                
                if len(toolbar_buttons) > 11:
                    await toolbar_buttons[11].click()
                    logger.info(f"      ✅ 已点击第 12 个按钮（图片按钮）")
                    
                    # ★★★ 等待对话框完全加载 ★★★
                    logger.info(f"      等待对话框加载...")
                    await asyncio.sleep(5)
                    
                    # ★★★ 调试：检查对话框状态 ★★★
                    dialog_info = await self.page.evaluate("""
                        () => {
                            const dialogs = document.querySelectorAll('.upload-image-panel, .byte-modal, .byte-dialog, [role="dialog"]');
                            const buttons = document.querySelectorAll('button, [role="button"], div[role="button"]');
                            return {
                                dialogCount: dialogs.length,
                                buttonTexts: Array.from(buttons).slice(0, 15).map(b => (b.textContent || '').trim()).filter(t => t)
                            };
                        }
                    """)
                    logger.info(f"      📊 对话框数量: {dialog_info['dialogCount']}")
                    logger.info(f"      📊 前15个按钮文本: {dialog_info['buttonTexts']}")
                    
                    # ★★★ 完全复用封面上传的成功逻辑 ★★★
                    
                    # 步骤1：点击"本地上传"按钮
                    logger.info(f"      步骤 2：点击'本地上传'按钮...")
                    await self.page.evaluate("""
                        () => {
                            const allElements = document.querySelectorAll('button, [role="button"], span, div');
                            for (const el of allElements) {
                                const text = (el.textContent || '').trim();
                                const rect = el.getBoundingClientRect();
                                if (text.includes('本地上传') && rect.width > 50 && rect.top > 0) {
                                    el.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    await asyncio.sleep(2)
                    logger.info(f"      ✅ 已点击'本地上传'按钮")
                    
                    # 步骤2：等待文件选择器出现并上传
                    logger.info(f"      步骤 3：等待文件选择器...")
                    await asyncio.sleep(2)
                    
                    # 使用 .first（与封面上传一致）
                    file_input = self.page.locator('input[type="file"]').first
                    try:
                        await file_input.set_input_files(abs_img_path, timeout=5000)
                        logger.info(f"      ✅ 文件已上传")
                    except Exception as e:
                        logger.warning(f"      ⚠️  文件上传失败：{e}")
                        raise
                    
                    # 步骤3：等待头条处理上传
                    logger.info(f"       等待图片上传和处理(15秒)...")
                    await asyncio.sleep(15)  # 关键：必须是15秒
                    
                    # 步骤4：点击确认按钮
                    logger.info(f"      步骤 4：点击'确定'按钮...")
                    confirm_clicked = await self.page.evaluate("""
                        () => {
                            const allButtons = document.querySelectorAll('button, [role="button"]');
                            for (const btn of allButtons) {
                                const text = (btn.textContent || '').trim();
                                const rect = btn.getBoundingClientRect();
                                if ((text === '确定' || text === '确认' || text === '完成') && 
                                    rect.width > 50 && rect.top > 0) {
                                    btn.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    
                    if confirm_clicked:
                        logger.info(f"      ✅ 已点击确认按钮")
                        await asyncio.sleep(3)
                    else:
                        logger.info(f"      ⚠️  未找到'确定'按钮")
                        
                        # 策略2: 尝试滚动对话框后再查找
                        logger.info(f"      🔄 尝试滚动对话框...")
                        await self.page.evaluate("""
                            () => {
                                const dialogs = document.querySelectorAll('.byte-modal-content, .byte-dialog-body, .upload-image-panel, [role="dialog"]');
                                dialogs.forEach(dialog => {
                                    dialog.scrollTop = dialog.scrollHeight;
                                });
                            }
                        """)
                        await asyncio.sleep(2)
                        
                        # 再次尝试点击
                        confirm_clicked = await self.page.evaluate("""
                            () => {
                                const allButtons = document.querySelectorAll('button, [role="button"], div[role="button"]');
                                for (const btn of allButtons) {
                                    const text = (btn.textContent || '').trim();
                                    const rect = btn.getBoundingClientRect();
                                    if ((text === '确定' || text === '确认' || text === '完成') && 
                                        rect.width > 50 && rect.top > 0) {
                                        btn.click();
                                        return true;
                                    }
                                }
                                return false;
                            }
                        """)
                        
                        if confirm_clicked:
                            logger.info(f"      ✅ 滚动后已点击'确定'按钮")
                            await asyncio.sleep(3)
                        else:
                            logger.info(f"      ℹ️  未找到确认按钮（可能自动处理）")
                    
                    # 步骤5：验证图片是否插入编辑器
                    logger.info(f"      步骤 5：验证图片...")
                    await asyncio.sleep(3)
                    
                    img_count = await self.page.evaluate("""
                        () => {
                            const editor = document.querySelector('div[contenteditable="true"]');
                            if (!editor) return 0;
                            return editor.querySelectorAll('img').length;
                        }
                    """)
                    logger.info(f"      📊 编辑器中图片数量: {img_count}")
                    
                    if img_count > 0:
                        logger.info(f"      ✅ 图片已成功插入编辑器")
                    else:
                        logger.warning(f"      ⚠️  图片未插入")
                else:
                    logger.warning(f"      ⚠️  未找到足够的工具栏按钮（需要至少12个，实际{len(toolbar_buttons)}个）")
            
            logger.info(f"   ✅ 所有配图已处理")
        
        except Exception as e:
            logger.warning(f"   ⚠️  插入配图失败：{e}")
            import traceback
            traceback.print_exc()
    
    async def _set_declaration(self, declaration_type: str = "ai"):
        """
        设置作品声明
        :param declaration_type: 声明类型
            - "ai": 引用AI
            - "personal_opinion": 仅个人观点，仅供参考
        """
        logger.info(f"📝 设置作品声明（类型: {declaration_type}）...")
            
        try:
            # 滚动到页面底部，加载"作品声明"区域
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            logger.info("   ✅ 已滚动到底部")
                
            # 根据声明类型查找并勾选对应的选项
            if declaration_type == "personal_opinion":
                # 查找"仅个人观点，仅供参考"选项
                declaration_texts = [
                    '仅个人观点',
                    '个人观点',
                    '仅供参考',
                    '仅个人观点，仅供参考'
                ]
                logger.info("   正在查找'仅个人观点，仅供参考'选项...")
            else:
                # 默认查找"引用AI"选项
                declaration_texts = ['引用AI']
                logger.info("   正在查找'引用AI'选项...")
                
            declaration_checked = await self.page.evaluate(f"""
                () => {{
                    const targetTexts = {json.dumps(declaration_texts)};
                        
                    // 查找所有 checkbox
                    const allCheckboxes = document.querySelectorAll('input[type="checkbox"]');
                    for (const cb of allCheckboxes) {{
                        const label = cb.closest('label') || cb.parentElement;
                        if (label) {{
                            const labelText = label.textContent || '';
                            for (const targetText of targetTexts) {{
                                if (labelText.includes(targetText)) {{
                                    if (!cb.checked) {{
                                        cb.click();
                                    }}
                                    return true;
                                }}
                            }}
                        }}
                    }}
                    return false;
                }}
            """)
                
            if declaration_checked:
                logger.info(f"   ✅ 已勾选{declaration_texts[0]}声明")
            else:
                logger.warning(f"   ⚠️  未找到{declaration_texts[0]}选项")
                    
                # 备用方案：直接通过文本查找
                await self.page.evaluate(f"""
                    () => {{
                        const targetTexts = {json.dumps(declaration_texts)};
                        const allElements = document.querySelectorAll('*');
                        for (const el of allElements) {{
                            const text = el.textContent || '';
                            for (const targetText of targetTexts) {{
                                if (text.includes(targetText) && (el.tagName === 'LABEL' || el.tagName === 'SPAN')) {{
                                    const checkbox = el.querySelector('input[type="checkbox"]') || 
                                                   el.parentElement?.querySelector('input[type="checkbox"]') ||
                                                   el.previousElementSibling;
                                    if (checkbox && checkbox.type === 'checkbox' && !checkbox.checked) {{
                                        checkbox.click();
                                        return true;
                                    }}
                                    el.click();
                                    return true;
                                }}
                            }}
                        }}
                        return false;
                    }}
                """)
                logger.info(f"   ✅ 已通过备用方案勾选{declaration_texts[0]}")
                    
        except Exception as e:
            logger.warning(f"⚠️  设置声明失败: {e}")
        
    async def _set_ai_declaration(self):
        """
        设置作品声明：引用AI（已废弃，使用 _set_declaration 代替）
        """
        await self._set_declaration("ai")
    
    async def close(self):
        """关闭浏览器并清理资源"""
        try:
            if self.page:
                await self.page.close()
                self.page = None
            
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
            
            logger.info(f"头条发布引擎已关闭，账号 ID: {self.account_id}")
        except Exception as e:
            logger.warning(f"关闭浏览器时出现警告（可忽略）: {e}")


# 示例用法
if __name__ == "__main__":
    async def test_publish():
        publisher = ToutiaoPublisher(account_id=1)
        
        try:
            # 1. 初始化浏览器
            await publisher.initialize_browser()
            
            # 2. 登录（人工辅助）
            login_result = await publisher.login_with_manual_input(
                username="your_phone_or_email",
                password="your_password"
            )
            print(f"登录结果: {login_result}")
            
            if login_result["status"] == "success":
                # 3. 发布文章
                publish_result = await publisher.publish_article(
                    title="Python 自动化办公的 10 个实用技巧",
                    content="这里是文章内容...",
                    category="科技",
                    tags=["Python", "自动化", "办公技巧"]
                )
                print(f"发布结果: {publish_result}")
        
        finally:
            await publisher.close()

    asyncio.run(test_publish())
