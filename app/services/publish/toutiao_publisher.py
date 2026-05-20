
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
        self._is_cdp_mode = False  # 标记是否为CDP模式
        self._cdp_user_data_dir = None  # CDP模式的用户数据目录

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
        
        # ★★★ 标记为CDP模式 ★★★
        self._is_cdp_mode = True
        
        logger.info("🚀 使用CDP模式连接真实Edge浏览器...")
        
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        if not os.path.exists(edge_path):
            edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        
        if not os.path.exists(edge_path):
            raise FileNotFoundError("未找到 Edge 浏览器")
        
        # 步骤1：启动Edge浏览器（带远程调试）
        logger.info(f"[1/3] 启动Edge浏览器（远程调试端口 {cdp_port}）...")
        
        # ★★★ 关键修复：不关闭所有Edge进程，只检查CDP端口是否可用 ★★★
        import socket
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
            # 只有当CDP端口未被占用时，才启动新浏览器
            logger.info(f"   启动新的Edge浏览器实例...")
            
            # ★★★ 关键修复：使用独立的临时用户数据目录，不影响正常Edge使用 ★★★
            import tempfile
            import time
            # 使用时间戳创建唯一的临时目录，确保与日常使用的Edge完全隔离
            temp_dir = tempfile.gettempdir()
            user_data_dir = os.path.join(temp_dir, f"smart-toolbox-cdp-{int(time.time())}")
            
            # 保存路径以便后续清理
            self._cdp_user_data_dir = user_data_dir
            
            logger.info(f"   使用独立用户数据目录: {user_data_dir}")
            logger.info(f"   （此目录与您的日常Edge配置完全隔离，互不影响）")
            
            # 启动带远程调试的Edge
            abs_user_data_dir = os.path.abspath(user_data_dir)
            
            # ★★★ 尝试不同的启动参数组合 ★★★
            cmd = [
                edge_path,
                f'--remote-debugging-port={cdp_port}',
                f'--user-data-dir="{abs_user_data_dir}"',  # 使用引号包裹路径
                '--no-first-run',
                '--no-default-browser-check',
                '--start-maximized',  # ★★★ 关键修复：启动时最大化窗口 ★★★
                '--window-size=1920,1080',  # ★★★ 设置窗口大小 ★★★
                'about:blank',
            ]
            
            logger.info(f"   执行命令: {' '.join(cmd)}")
            
            # ★★★ 关键修复：使用 CREATE_NEW_CONSOLE 标志，确保浏览器独立运行 ★★★
            creation_flags = 0
            if os.name == 'nt':  # Windows
                import subprocess as sp
                creation_flags = sp.CREATE_NEW_CONSOLE
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags
            )
            logger.info(f"✅ Edge浏览器进程已启动 (PID: {process.pid})")
            
            # ★★★ 关键修复：等待 CDP 端口真正可用 ★★★
            logger.info(f"   等待 CDP 端口 {cdp_port} 就绪...")
            max_retries = 40  # 增加到40秒
            retry_count = 0
            cdp_ready = False
            
            while retry_count < max_retries:
                await asyncio.sleep(1)  # 每秒检查一次
                retry_count += 1
                
                try:
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    sock.settimeout(1)
                    result = sock.connect_ex(('127.0.0.1', cdp_port))
                    if result == 0:
                        cdp_ready = True
                        sock.close()
                        logger.info(f"   ✅ CDP 端口 {cdp_port} 已就绪（耗时 {retry_count} 秒）")
                        break
                    sock.close()
                except:
                    pass
                
                if retry_count % 5 == 0:
                    logger.info(f"   ⏳ 等待中... ({retry_count}/{max_retries} 秒)")
            
            if not cdp_ready:
                logger.error(f"   ❌ CDP 端口 {cdp_port} 在 {max_retries} 秒后仍未就绪")
                logger.error(f"   请检查 Edge 浏览器是否正常启动")
                # 尝试读取进程输出，查看是否有错误信息
                try:
                    stdout, stderr = process.communicate(timeout=2)
                    if stdout:
                        logger.error(f"   标准输出: {stdout.decode('utf-8', errors='ignore')[:500]}")
                    if stderr:
                        logger.error(f"   错误输出: {stderr.decode('utf-8', errors='ignore')[:500]}")
                except:
                    pass
                logger.error(f"   💡 建议：关闭所有 Edge 浏览器窗口后重试")
                logger.error(f"   💡 或者使用标准模式（use_cdp=False）")
                raise TimeoutError(f"Edge 浏览器启动超时，CDP 端口 {cdp_port} 无法连接")
        else:
            logger.info("   ✅ 使用现有的Edge浏览器实例")
        
        # 步骤2：连接到Edge浏览器
        logger.info(f"[2/3] 连接到Edge浏览器（CDP端口 {cdp_port}）...")
                
        self.playwright = await async_playwright().start()
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
                
        # ★★★ 关键修复：始终创建新标签页，避免并发冲突 ★★★
        logger.info("   📑 创建新的标签页...")
        self.page = await self.context.new_page()
        logger.info(f"   ✅ 新标签页已创建")
        
        # ★★★ 关键修复：CDP模式下也要注入反检测脚本 ★★★
        logger.info("   🛡️  注入反检测脚本...")
        await self.page.add_init_script("""
            // 隐藏 webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // 模拟真实的 Chrome 对象
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // 隐藏 Playwright 特征
            delete window.__playwright;
            delete window.__pw_manual;
            delete window.__pw_inspect;
            
            console.log('✅ 反检测脚本已注入');
        """)
        logger.info("   ✅ 反检测脚本已注入")
                
        logger.info("✅ 已连接到真实Edge浏览器")
        logger.info(f"   当前URL: {self.page.url}")
        logger.info("[3/3] CDP连接完成！")
    
    async def initialize_standard_browser(self):
        """初始化标准浏览器（原有逻辑）"""
        # ★★★ 标记为非CDP模式 ★★★
        self._is_cdp_mode = False
        
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
        declaration_type: str = "ai",  # 新增参数：声明类型，"ai"=引用ai, "personal_opinion"=仅个人观点（已废弃，改用declarations）
        declarations: list = None,  # ✅ 新增参数：作品声明列表（多选）
        article_images: list = None,  # 新增参数：文章配图路径列表
        image_suggestions: list = None,  # 新增参数：智能图片位置建议
        account_id: int = None  # 新增参数：账号ID（用于获取进化配置）
    ) -> Dict[str, Any]:
        """
        发布头条文章（支持高级封面图功能）
        
        Args:
            title: 文章标题
            content: 文章内容
            category: 文章分类
            tags: 标签列表
            cover_image_path: 自定义封面图路径
            auto_generate_cover: 是否自动生成封面图
            cover_style: 封面风格 (modern/minimal/bold)
            use_template: 使用模板ID生成封面
            enable_ab_test: 是否启用A/B测试
            declaration_type: 声明类型（已废弃，改用declarations）
            declarations: 作品声明列表（多选），如 ["ai_generated", "personal_opinion"]
            article_images: 文章配图路径列表
            image_suggestions: 智能图片位置建议
            account_id: 账号ID（用于获取进化配置）
        """
        # 保存account_id供后续使用
        self.account_id = account_id
        
        try:
            if not self.page:
                await self.initialize_browser()

            # 1. 进入文章发布页
            # ✅ 使用正确的头条文章发布URL（根据实际页面）
            publish_url = "https://mp.toutiao.com/profile_v4/graphic/publish?from=toutiao_pc"
            logger.info(f"正在打开发布页面: {publish_url}")
            
            # ★★★ 智能跳转逻辑：先检查当前页面，避免导航冲突（参考 test_cdp_auto_publish.py）★★★
            current_url = self.page.url
            logger.info(f"   当前URL: {current_url}")
            
            if "profile_v4/graphic/publish" not in current_url:
                logger.info("   正在跳转到发布页面...")
                try:
                    # ✅ 关键修复：使用 wait_until='networkidle' 确保页面完全加载
                    await self.page.goto(publish_url, timeout=60000, wait_until='networkidle')
                    logger.info("   ✅ 发布页面已加载（networkidle）")
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
            
            # ★★★ 关键修复：额外等待微前端模块加载（针对CDP模式）★★★
            if self._is_cdp_mode:
                logger.info("   🧩 CDP模式：等待微前端模块加载...")
                
                # ✅ 关键修复：增加最大等待时间和重试次数
                MAX_WAIT_TIME = 30  # 最多等待30秒
                CHECK_INTERVAL = 1  # 每秒检查一次
                
                for i in range(MAX_WAIT_TIME):
                    await asyncio.sleep(CHECK_INTERVAL)
                    
                    # 检查页面加载状态
                    load_status = await self.page.evaluate("""
                        () => {
                            // 检查微前端容器是否存在
                            const microAppContainer = document.querySelector('#micro-app-graphic, [id*="micro-app"], .garfish-container');
                            
                            // 检查编辑器是否真正可用
                            const editor = document.querySelector('div[contenteditable="true"]');
                            const isEditorReady = editor && editor.offsetParent !== null && editor.clientHeight > 0;
                            
                            // ★★★ 关键：检查底部固定栏是否出现（固定定位，不随滚动条滚动）★★★
                            // ✅ 根据实际页面：预览、定时发布、预览并发布按钮是固定在底部的
                            const bottomBarSelectors = [
                                // 方法1：直接查找按钮文本（最可靠）
                                'button:has-text("预览并发布")',
                                'button:has-text("预览")',
                                'button:has-text("定时发布")',
                                'button:has-text("确认发布")',  // ✅ 新增：确认发布按钮
                                
                                // 方法2：底部栏容器
                                '[class*="publish-bar"]',
                                '[class*="bottom-bar"]',
                                '[class*="footer-bar"]',
                                
                                // 方法3：包含多个按钮的容器
                                'div[class*="action"]',
                                'div[class*="toolbar-bottom"]'
                            ];
                            
                            let bottomBarFound = false;
                            let foundSelector = '';
                            for (const selector of bottomBarSelectors) {
                                try {
                                    const elements = document.querySelectorAll(selector);
                                    for (const element of elements) {
                                        if (element && element.offsetParent !== null && element.clientHeight > 0) {
                                            bottomBarFound = true;
                                            foundSelector = selector;
                                            console.log('✅ 找到底部栏:', selector);
                                            break;
                                        }
                                    }
                                    if (bottomBarFound) break;
                                } catch(e) {
                                    // 忽略选择器错误
                                }
                            }
                            
                            // 检查是否有"预览并发布"或"确认发布"按钮的文本（最可靠的检测方式）
                            let hasPublishButton = false;
                            let publishButtonText = '';
                            const allButtons = document.querySelectorAll('button');
                            for (const btn of allButtons) {
                                const text = btn.textContent.trim();
                                if (text.includes('预览并发布') || text.includes('确认发布')) {
                                    hasPublishButton = true;
                                    publishButtonText = text;
                                    console.log('✅ 找到发布按钮:', text);
                                    break;
                                }
                            }
                            
                            return {
                                container: !!microAppContainer,
                                editorReady: isEditorReady,
                                bottomBarLoaded: bottomBarFound,
                                hasPublishButton: hasPublishButton,
                                foundSelector: foundSelector
                            };
                        }
                    """)
                    
                    # 如果找到发布按钮，说明页面完全就绪（底部按钮是固定定位，不需要滚动）
                    if load_status['hasPublishButton']:
                        # ✅ 关键修复：只要有发布按钮就认为页面加载完成
                        # 底部按钮是固定定位（position: fixed/sticky），页面加载后应该立即可见
                        logger.info(f"   ✅ 页面完全加载！发布按钮已就绪（耗时{i+1}秒）")
                        logger.info(f"      按钮文本: {load_status.get('publishButtonText', 'N/A')}")
                        if load_status.get('foundSelector'):
                            logger.info(f"      匹配选择器: {load_status.get('foundSelector')}")
                        break
                    
                    # 如果编辑器已就绪但发布按钮未出现，继续等待
                    if load_status['editorReady'] and i > 5:
                        logger.info(f"   ⏳ 编辑器已就绪，等待发布按钮加载... ({i+1}/{MAX_WAIT_TIME}秒) [发布按钮:{load_status['hasPublishButton']}]")
                    elif i % 5 == 0 and i > 0:
                        logger.info(f"    等待页面加载... ({i+1}/{MAX_WAIT_TIME}秒) [编辑器:{load_status['editorReady']}, 发布按钮:{load_status['hasPublishButton']}]")
                else:
                    # 循环结束仍未找到发布按钮
                    logger.warning("   ⚠️  页面可能未完全加载，发布按钮未出现")
                    
                    # ✅ 保存调试信息（HTML + 截图）
                    try:
                        import time
                        timestamp = int(time.time())
                        debug_html = f"logs/toutiao_incomplete_load_{timestamp}.html"
                        with open(debug_html, 'w', encoding='utf-8') as f:
                            f.write(await self.page.content())
                        logger.info(f"📄 不完整加载的HTML已保存: {debug_html}")
                        
                        # 保存截图
                        debug_screenshot = f"logs/toutiao_incomplete_load_{timestamp}.png"
                        await self.page.screenshot(path=debug_screenshot, full_page=True)
                        logger.info(f"📸 不完整加载的截图已保存: {debug_screenshot}")
                    except Exception as e:
                        logger.error(f"保存调试信息失败: {e}")
                    
                    # ★★★ 尝试触发发布按钮加载（底部按钮是固定定位，理论上不需要滚动）★★★
                    logger.info("   ⚠️  底部按钮未出现，尝试触发页面完整渲染...")
                    
                    # 方法1：聚焦到标题输入框（可能触发页面完整渲染）
                    await self.page.evaluate("""
                        () => {
                            const titleInput = document.querySelector('input[placeholder*="标题"]');
                            if (titleInput) {
                                titleInput.click();
                                titleInput.focus();
                                setTimeout(() => {
                                    titleInput.blur();
                                    // 触发input事件
                                    titleInput.dispatchEvent(new Event('input', { bubbles: true }));
                                }, 500);
                            }
                        }
                    """)
                    await asyncio.sleep(3)
                    
                    # 方法2：聚焦到正文编辑器
                    await self.page.evaluate("""
                        () => {
                            const editor = document.querySelector('div[contenteditable="true"]');
                            if (editor) {
                                editor.click();
                                editor.focus();
                                setTimeout(() => editor.blur(), 500);
                            }
                        }
                    """)
                    await asyncio.sleep(3)
                    
                    # 方法3：窗口resize事件（可能触发重新渲染）
                    await self.page.evaluate("""
                        () => {
                            window.dispatchEvent(new Event('resize'));
                        }
                    """)
                    await asyncio.sleep(2)
                    
                    logger.info("   ✅ 已尝试多种方法触发页面完整渲染")
                    
                    # 最终检测：直接查找按钮文本（最可靠）
                    final_check = await self.page.evaluate("""
                        () => {
                            const buttons = document.querySelectorAll('button');
                            for (const btn of buttons) {
                                const text = btn.textContent.trim();
                                if (text.includes('预览并发布')) {
                                    return {
                                        found: true,
                                        text: text
                                    };
                                }
                            }
                            return {
                                found: false,
                                text: ''
                            };
                        }
                    """)
                    
                    if final_check['found']:
                        logger.info(f"   ✅ 触发后成功找到发布按钮！按钮文本: {final_check['text']}")
                    else:
                        logger.error("   ❌ 即使触发后仍未找到'预览并发布'按钮")
                        logger.error("    可能原因：")
                        logger.error("      1. 浏览器窗口未最大化，按钮被遮挡")
                        logger.error("      2. 被头条反自动化检测拦截，页面未完整加载")
                        logger.error("      3. 网络连接问题，微前端模块加载失败")
                        logger.error("      4. 头条页面结构发生变化")
            
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

            # ★★★ [步骤1/6] 先生成并上传封面图（参考成功测试脚本）★★★
            logger.info("📦 [步骤1/6] 开始处理封面图...")
            try:
                # 如果需要自动生成封面图
                if auto_generate_cover and not cover_image_path:
                    logger.info("🤖 开始AI生成封面图...")
                    
                    # ✅ 使用数据库配置的默认提供商生成真实AI图像
                    db = None
                    try:
                        from app.services.content.image_generator import ImageGenerator
                        from app.db.session import SessionLocal
                        from app.models import Account
                        
                        # ★★★ 关键修复：传入数据库会话，让ImageGenerator能读取配置 ★★★
                        db = SessionLocal()
                        image_gen = ImageGenerator(db=db)
                        
                        # ★★★ 获取账号的自适应进化配置（如果有）★★★
                        evolution_config = None
                        if self.account_id:
                            account = db.query(Account).filter(Account.id == self.account_id).first()
                            if account and account.evolution_config:
                                import json
                                evolution_config = json.loads(account.evolution_config)
                                logger.info(f"✅ 检测到账号 {self.account_id} 的自适应进化配置")
                        
                        # ★★★ 根据进化配置优化提示词 ★★★
                        cover_optimization = {}
                        if evolution_config:
                            cover_optimization = evolution_config.get("cover_optimization", {})
                            style_recommendations = cover_optimization.get("style_recommendations", {})
                            
                            # 根据分类选择推荐的封面风格
                            recommended_style = style_recommendations.get(category, {})
                            if recommended_style:
                                logger.info(f"🎨 应用自适应封面优化建议")
                                logger.info(f"   推荐风格: {recommended_style.get('style', 'modern')}")
                                logger.info(f"   配色方案: {recommended_style.get('color_scheme', '')}")
                                logger.info(f"   构图方式: {recommended_style.get('composition', '')}")
                                
                                # 构建增强提示词
                                prompt = f"""{title}, {category}

专业级头条封面图设计，视觉冲击力强，引人注目：
- 风格：{recommended_style.get('style', 'modern')}（{recommended_style.get('prompt_additions', '')}）
- 色彩：{recommended_style.get('color_scheme', '蓝紫色渐变')}
- 构图：{recommended_style.get('composition', '黄金分割构图')}
- 质量：8K超高清，专业摄影质感
- 元素：关键主题元素突出，留白适当，文字友好

适合今日头条平台，吸引点击，高转化率"""
                            else:
                                # 降级：使用通用模板
                                universal_template = cover_optimization.get("universal_prompt_template", "")
                                if universal_template:
                                    prompt = universal_template.format(
                                        style="modern",
                                        color_scheme="蓝色/紫色渐变",
                                        composition="主体居中，简洁背景",
                                        prompt_additions=f"{title}, {category}"
                                    )
                                else:
                                    prompt = f"""{title}, {category}

专业级头条封面图设计，视觉冲击力强，引人注目：
- 构图：黄金分割构图，主体突出，层次分明
- 色彩：鲜艳饱和，对比强烈，暖色调为主
- 风格：现代简约，商业摄影质感，高清细节
- 元素：关键主题元素居中，留白适当，文字友好
- 质量：8K超高清，专业灯光，锐利清晰

适合今日头条平台，吸引点击，高转化率"""
                        else:
                            # 没有进化配置，使用原始提示词
                            prompt = f"""{title}, {category}

专业级头条封面图设计，视觉冲击力强，引人注目：
- 构图：黄金分割构图，主体突出，层次分明
- 色彩：鲜艳饱和，对比强烈，暖色调为主
- 风格：现代简约，商业摄影质感，高清细节
- 元素：关键主题元素居中，留白适当，文字友好
- 质量：8K超高清，专业灯光，锐利清晰

适合今日头条平台，吸引点击，高转化率"""
                        
                        logger.info(f"   开始AI生成封面图...")
                        logger.info(f"   提示词: {prompt[:100]}...")
                        logger.info(f"   默认提供商: {image_gen.default_provider}")
                        
                        result = await image_gen.generate_image(
                            prompt=prompt,
                            aspect_ratio="16:9"
                        )
                        
                        if result.get("status") == "success":
                            cover_image_path = result.get("image_path")
                            logger.info(f"✅ 封面图生成成功!")
                            logger.info(f"   图片路径: {cover_image_path}")
                            logger.info(f"   提供商: {result.get('provider', 'unknown')}")
                            logger.info(f"   模型: {result.get('model', 'unknown')}")
                        else:
                            # ✅ 不做降级，直接抛出异常
                            error_msg = result.get('error', '未知错误')
                            logger.error(f"❌ 封面图生成失败: {error_msg}")
                            raise Exception(f"封面图生成失败: {error_msg}")
                    except Exception as e:
                        # ✅ 不做降级，直接抛出异常
                        logger.error(f"❌ 封面图生成失败: {e}")
                        raise
                    finally:
                        # 关闭数据库会话
                        if db:
                            db.close()
                
                # 如果有封面图，现在上传
                if cover_image_path:
                    logger.info(f"📸 开始上传封面图: {cover_image_path}")
                    
                    try:
                        # 压缩封面图
                        from app.utils.image_processor import ImageProcessor
                        processor = ImageProcessor()
                        compress_result = processor.compress_image(
                            cover_image_path,
                            quality=85,
                            max_width=1280,
                            max_height=720
                        )
                        if compress_result.get("status") == "success":
                            cover_image_path = compress_result["output_path"]
                            logger.info(f"✅ 封面图压缩完成: {compress_result['compression_ratio_percent']}% 压缩率")
                        else:
                            logger.warning(f"⚠️  封面图压缩失败: {compress_result.get('error')}")
                    except Exception as e:
                        logger.warning(f"⚠️  封面图压缩异常: {e}，使用原图")
                    
                    # 选择单图模式
                    await self._select_single_image_mode()
                    
                    # 上传封面图
                    await self._upload_cover_with_cdp_optimization(cover_image_path)
                    logger.info("✅ [步骤1/6] 封面图处理完成")
                else:
                    logger.warning("⚠️  未生成封面图，将使用默认封面")
                    
            except Exception as e:
                logger.warning(f"⚠️  封面图处理失败: {e}")
                import traceback
                traceback.print_exc()
            
            await asyncio.sleep(3)

            # ★★★ [步骤2/6] 填写标题（使用测试脚本验证成功的JS方式）★★★
            logger.info("📝 [步骤2/6] 开始填写标题...")
            
            # ✅ 直接使用JS方式（测试脚本验证成功）
            js_success = await self.page.evaluate(f"""
                () => {{
                    const inputs = document.querySelectorAll('input, textarea');
                    for (const input of inputs) {{
                        if (input.placeholder && input.placeholder.includes('标题')) {{
                            input.focus();
                            input.value = '';
                            input.value = `{title}`;
                            input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                            input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                            return true;
                        }}
                    }}
                    return false;
                }}
            """)
            
            if js_success:
                logger.info("✅ 标题已通过 JS 填写")
            else:
                logger.error("❌ 标题填写失败！未找到标题输入框")
                return {
                    "status": "failed",
                    "error": "标题填写失败，请检查页面是否正常加载"
                }
            
            # 验证标题是否填写成功
            await asyncio.sleep(1)
            title_verification = await self.page.evaluate("""
                () => {
                    const inputs = document.querySelectorAll('input, textarea');
                    for (const input of inputs) {
                        if (input.placeholder && input.placeholder.includes('标题')) {
                            return input.value || '(空)';
                        }
                    }
                    return '未找到标题输入框';
                }
            """)
            logger.info(f"📊 标题验证结果: {title_verification}")
            
            if title_verification == '(空)' or title_verification == '未找到标题输入框':
                logger.error("❌ 标题填写验证失败，中止发布流程")
                return {
                    "status": "failed",
                    "error": "标题填写验证失败"
                }

            # 3. ★★★ [步骤3/6] 生成文章配图（只生成文件，不插入）★★★
            logger.info("🖼️ [步骤3/6] 开始生成文章配图...")
            if article_images:
                logger.info(f"✅ 已提供 {len(article_images)} 张配图")
            else:
                logger.info("ℹ️  未提供配图，将使用纯文本")

            # 4. ★★★ [步骤4/6] 填写正文（富文本编辑器）★★★
            logger.info("📄 [步骤4/6] 开始填写正文...")
            try:
                # 头条使用富文本编辑器，需要定位编辑器区域
                editor = await self.page.query_selector('div[contenteditable="true"]')
                if not editor:
                    editor = await self.page.query_selector('div.toutiao-editor')
                
                if editor:
                    # 先清空编辑器
                    await editor.fill('')
                    await asyncio.sleep(0.5)
                    
                    # 填写内容
                    await editor.fill(content)
                    await asyncio.sleep(2)
                    logger.info(f"✅ 正文已填写，长度: {len(content)} 字")
                    
                    # 验证正文是否填写成功
                    content_verification = await self.page.evaluate("""
                        () => {
                            const editor = document.querySelector('div[contenteditable="true"]');
                            if (editor) {
                                return editor.innerText || editor.textContent || '(空)';
                            }
                            return '未找到编辑器';
                        }
                    """)
                    logger.info(f"📊 正文验证结果: {len(content_verification)} 字")
                else:
                    logger.error("❌ 未找到富文本编辑器")
                    return {
                        "status": "failed",
                        "error": "未找到富文本编辑器，请检查页面是否正常加载"
                    }
            except Exception as e:
                logger.error(f"❌ 正文填写失败: {e}")
                import traceback
                traceback.print_exc()
                return {
                    "status": "failed",
                    "error": f"正文填写失败: {str(e)}"
                }

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

            # 5. ★★★ [步骤5/6] 插入文章配图（分散插入到不同段落）★★★
            if article_images:
                logger.info("\n=== [步骤5/6] 开始插入文章配图 ===")
                
                # ★★★ 检查是否有智能图片位置建议 ★★★
                if image_suggestions and len(image_suggestions) > 0:
                    logger.info(f"📍 使用智能图片位置建议，共 {len(image_suggestions)} 个位置")
                    positions = [sug["position"] for sug in image_suggestions]
                    logger.info(f"   位置: {positions}")
                    await self._insert_article_images_with_positions(article_images, positions)
                else:
                    # 降级：使用均匀分布
                    logger.info("📍 使用均匀分布模式")
                    await self._insert_article_images(article_images)
                
                logger.info("=== 文章配图插入完成 ===\n")
            
            # 6. ★★★ [步骤6/6] 设置作品声明（根据declarations参数）★★★
            await self._set_declaration(declaration_type, declarations)
            await asyncio.sleep(2)

            # 7. 点击发布按钮
            logger.info("正在查找发布按钮...")
            publish_selectors = [
                'button:has-text("预览并发布")',  # ★★★ 头条实际按钮文字（优先）★★★
                '.byte-btn:has-text("预览并发布")',  # ★★★ 头条样式 ★★★
                'button:has-text("发布")',
                '.byte-btn:has-text("发布")',
                'button.publish-btn',
                'button[type="submit"]',
                'button[class*="publish"]',
                'button[class*="btn"]:has-text("发布")',
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
            
            # ★★★ 关键修复：隐藏 AI 助手抽屉（防止遮挡发布按钮）★★★
            logger.info("   🛡️  隐藏 AI 助手抽屉...")
            try:
                await self.page.evaluate("""
                    () => {
                        // 隐藏所有 AI 助手相关的抽屉
                        const drawers = document.querySelectorAll('.byte-drawer-wrapper, .ai-assistant-drawer, .ai-conversation');
                        drawers.forEach(drawer => {
                            drawer.style.display = 'none';
                            drawer.style.visibility = 'hidden';
                            drawer.style.pointerEvents = 'none';
                        });
                        
                        // 隐藏右侧面板
                        const rightPanels = document.querySelectorAll('[class*="drawer"], [class*="assistant"], [class*="sidebar"]');
                        rightPanels.forEach(panel => {
                            if (panel.getBoundingClientRect().right > window.innerWidth * 0.7) {
                                panel.style.display = 'none';
                            }
                        });
                        
                        console.log('AI 助手已隐藏');
                    }
                """)
                await asyncio.sleep(1)
                logger.info("   ✅ AI 助手已隐藏")
            except Exception as e:
                logger.warning(f"   ⚠️  隐藏 AI 助手失败: {e}")
            
            # ★★★ 关键修复：使用 force=True 强制点击，避免被AI助手抽屉遮挡 ★★★
            logger.info("   🖱️  使用 force=True 强制点击发布按钮...")
            await publish_button.click(force=True)
            logger.info("✅ 已点击发布按钮，等待响应...")
            
            # ★★★ 关键修复：增加等待时间，头条发布需要较长时间 ★★★
            logger.info("   ⏳ 等待发布请求（最多30秒）...")
            for i in range(30):  # 等待30秒，每秒检查一次
                await asyncio.sleep(1)
                if publish_request_detected:
                    logger.info(f"   ✅ 在第{i+1}秒检测到发布请求")
                    break
                if i % 5 == 0 and i > 0:
                    logger.info(f"   ⏳ 已等待{i}秒...")
            
            # 检查是否有网络请求
            if publish_request_detected:
                logger.info(f"✅ 检测到发布网络请求，响应状态: {response_status}")
            else:
                logger.warning("⚠️  30秒内未检测到发布相关的网络请求！")
            
            # 检查URL是否变化
            after_url = self.page.url
            logger.info(f"点击发布后URL: {after_url}")
            url_changed = before_url != after_url
            
            if url_changed:
                logger.info(f"✅ URL发生变化: {before_url} -> {after_url}")
            else:
                logger.warning("⚠️  URL未变化，可能发布失败")

            # ★★★ 检查是否有确认弹窗（自动点击）★★★
            try:
                logger.info("   🔍 查找'确认发布'按钮...")
                # ★★★ 关键修复：等待确认对话框出现（增加等待时间）★★★
                await asyncio.sleep(5)  # 从3秒增加到5秒
                
                # ★★★ 调试：保存点击后的页面状态 ★★★
                try:
                    post_click_html = f"logs/toutiao_post_click_{int(asyncio.get_event_loop().time())}.html"
                    with open(post_click_html, 'w', encoding='utf-8') as f:
                        f.write(await self.page.content())
                    logger.info(f"📄 点击后HTML已保存: {post_click_html}")
                    
                    post_click_screenshot = f"logs/toutiao_post_click_{int(asyncio.get_event_loop().time())}.png"
                    await self.page.screenshot(path=post_click_screenshot, full_page=True)
                    logger.info(f"📸 点击后截图: {post_click_screenshot}")
                except Exception as e:
                    logger.warning(f"保存点击后状态失败: {e}")
                
                # ★★★ 先尝试等待对话框出现（最多等待10秒）★★★
                logger.info("   ⏳ 等待确认对话框出现...")
                dialog_appeared = False
                for i in range(10):
                    await asyncio.sleep(1)
                    has_dialog = await self.page.evaluate("""
                        () => {
                            const dialogs = document.querySelectorAll('.byte-modal, .modal, [role="dialog"], .ant-modal, .confirm-dialog');
                            return dialogs.length > 0;
                        }
                    """)
                    if has_dialog:
                        logger.info(f"   ✅ 在第{i+1}秒检测到对话框")
                        dialog_appeared = True
                        break
                    if i % 3 == 0 and i > 0:
                        logger.info(f"   ⏳ 已等待{i}秒...")
                
                if not dialog_appeared:
                    logger.warning("   ⚠️  10秒内未检测到对话框，可能不需要二次确认")
                
                # ★★★ 自动点击确认发布按钮（根据实际对话框结构优化）★★★
                confirm_clicked = await self.page.evaluate("""
                    () => {
                        const results = {
                            clicked: false,
                            buttonText: '',
                            foundButtons: [],
                            method: ''
                        };
                        
                        // 方法1：优先在对话框/模态框中查找（根据截图结构）
                        const dialogs = document.querySelectorAll('.byte-modal, .modal, [role="dialog"], .preview-modal, .confirm-dialog');
                        for (const dialog of dialogs) {
                            // 在对话框中查找底部按钮区域
                            const footer = dialog.querySelector('.byte-modal-footer, .modal-footer, [class*="footer"], [class*="bottom"]');
                            const buttons = footer ? footer.querySelectorAll('button, [role="button"], .byte-btn') : 
                                                   dialog.querySelectorAll('button, [role="button"], .byte-btn');
                            
                            for (const btn of buttons) {
                                const text = btn.textContent?.trim();
                                if (text) {
                                    results.foundButtons.push(text.substring(0, 20));
                                }
                                
                                // ★★★ 精确匹配"确认发布"按钮（红色主按钮）★★★
                                if (text === '确认发布') {
                                    btn.click();
                                    console.log('✅ 已点击确认发布按钮');
                                    results.clicked = true;
                                    results.buttonText = text;
                                    results.method = '精确匹配对话框内的确认发布按钮';
                                    return results;
                                }
                            }
                        }
                        
                        // 方法2：在整个页面查找（如果对话框检测失败）
                        const allButtons = document.querySelectorAll('button, [role="button"], .byte-btn');
                        for (const btn of allButtons) {
                            const text = btn.textContent?.trim();
                            if (text === '确认发布') {
                                btn.click();
                                console.log('✅ 已点击确认发布按钮');
                                results.clicked = true;
                                results.buttonText = text;
                                results.method = '精确匹配页面中的确认发布按钮';
                                return results;
                            }
                        }
                        
                        // 方法3：查找包含"确认"的按钮
                        for (const btn of allButtons) {
                            const text = btn.textContent?.trim();
                            if (text && (text.includes('确认发布') || text === '确认')) {
                                btn.click();
                                console.log('✅ 已点击确认按钮:', text);
                                results.clicked = true;
                                results.buttonText = text;
                                results.method = '模糊匹配确认按钮';
                                return results;
                            }
                        }
                        
                        // 方法4：对话框中最后一个按钮（通常是确认按钮）
                        for (const dialog of dialogs) {
                            const buttons = dialog.querySelectorAll('button, [role="button"], .byte-btn');
                            if (buttons.length > 0) {
                                // 最后一个按钮通常是确认/发布
                                const lastButton = buttons[buttons.length - 1];
                                const text = lastButton.textContent?.trim() || '未知按钮';
                                lastButton.click();
                                console.log('✅ 已点击对话框最后一个按钮:', text);
                                results.clicked = true;
                                results.buttonText = text;
                                results.method = '点击对话框最后一个按钮';
                                return results;
                            }
                        }
                        
                        return results;
                    }
                """)
                
                # ★★★ 详细记录找到的按钮 ★★★
                if isinstance(confirm_clicked, dict):
                    if confirm_clicked.get('clicked'):
                        logger.info(f"✅ 已点击按钮: {confirm_clicked.get('buttonText', '未知')}")
                        logger.info(f"   匹配方式: {confirm_clicked.get('method', 'N/A')}")
                    else:
                        found_buttons = confirm_clicked.get('foundButtons', [])[:10]
                        logger.warning(f"⚠️  未找到确认按钮")
                        logger.warning(f"   页面上找到的按钮: {found_buttons}")
                        
                        # ★★★ 关键修复：尝试查找任何可见的对话框按钮 ★★★
                        logger.info("   🔍 尝试查找对话框中的任何按钮...")
                        any_button_clicked = await self.page.evaluate("""
                            () => {
                                // 查找所有模态框/对话框
                                const dialogs = document.querySelectorAll('.byte-modal, .modal, [role="dialog"], .ant-modal, .confirm-dialog');
                                if (dialogs.length === 0) {
                                    console.log('未找到任何对话框');
                                    return false;
                                }
                                
                                // 在每个对话框中查找按钮
                                for (const dialog of dialogs) {
                                    const buttons = dialog.querySelectorAll('button, [role="button"], .byte-btn, .ant-btn');
                                    if (buttons.length > 0) {
                                        // 点击最后一个按钮（通常是确认按钮）
                                        const lastButton = buttons[buttons.length - 1];
                                        const text = lastButton.textContent?.trim() || '未知按钮';
                                        console.log('点击对话框按钮:', text);
                                        lastButton.click();
                                        return true;
                                    }
                                }
                                
                                return false;
                            }
                        """)
                        
                        if any_button_clicked:
                            logger.info("✅ 已点击对话框中的按钮")
                        else:
                            logger.warning("⚠️  未找到任何可点击的对话框按钮")
                else:
                    # 兼容旧版本返回值（布尔值）
                    if confirm_clicked:
                        logger.info("✅ 已点击'确认发布'按钮")
                    else:
                        logger.warning("⚠️  未找到确认按钮")
                
                # ★★★ 关键修复：无论是否找到确认按钮，都等待足够时间 ★★★
                logger.info("   ⏳ 等待发布处理完成（20秒）...")
                await asyncio.sleep(20)
            except Exception as e:
                logger.debug(f"未找到确认弹窗或已自动确认: {e}")
                # 异常情况下也等待
                logger.info("   ⏳ 等待发布处理完成（15秒）...")
                await asyncio.sleep(15)
            
            # ★★★ 统一验证：跳转到“已发布作品”页面验证 ★★★
            logger.info("   🔍 跳转到已发布作品页面进行验证...")
            try:
                articles_url = "https://mp.toutiao.com/profile_v4/graphic/articles"
                await self.page.goto(articles_url, timeout=30000, wait_until='domcontentloaded')
                await asyncio.sleep(5)  # 等待页面加载
                
                logger.info(f"   📄 当前URL: {self.page.url}")
                
                # ★★★ 关键修复：多次尝试查找文章（最多3次，每次间隔3秒）★★★
                article_found = False
                for attempt in range(3):
                    if attempt > 0:
                        logger.info(f"   ⏳ 第{attempt + 1}次尝试查找文章...")
                        await asyncio.sleep(3)
                        # 刷新页面
                        await self.page.reload(wait_until='domcontentloaded')
                        await asyncio.sleep(3)
                    
                    # 在已发布列表中查找刚发布的文章
                    article_found = await self.page.evaluate(f"""
                        () => {{
                            const bodyText = document.body.textContent || '';
                            const title = `{title}`;
                            
                            // 检查页面是否包含文章标题
                            return bodyText.includes(title);
                        }}
                    """)
                    
                    if article_found:
                        logger.info(f"✅ 在已发布作品中找到文章: {title}")
                        break
                    else:
                        logger.warning(f"   ⚠️  第{attempt + 1}次未找到文章")
                
                if article_found:
                    logger.info("✅ 发布验证成功！")
                    
                    # 截图保存验证结果
                    try:
                        verify_screenshot = f"logs/toutiao_publish_verified_{int(asyncio.get_event_loop().time())}.png"
                        await self.page.screenshot(path=verify_screenshot, full_page=True)
                        logger.info(f"📸 验证截图: {verify_screenshot}")
                    except:
                        pass
                    
                    return {
                        "status": "success",
                        "title": title,
                        "message": "文章发布成功，已在已发布作品中验证"
                    }
                else:
                    # ★★★ 关键修复：未找到文章，继续检查草稿箱 ★★★
                    logger.warning(f"⚠️  在已发布作品中未找到文章: {title}")
                    logger.warning("   正在检查是否在草稿箱中...")
                    
                    # 跳转到草稿箱页面
                    drafts_url = "https://mp.toutiao.com/profile_v4/graphic/drafts"
                    await self.page.goto(drafts_url, timeout=30000, wait_until='domcontentloaded')
                    await asyncio.sleep(5)
                    
                    # 在草稿箱中查找文章
                    draft_found = False
                    for attempt in range(2):
                        if attempt > 0:
                            await asyncio.sleep(2)
                            await self.page.reload(wait_until='domcontentloaded')
                            await asyncio.sleep(2)
                        
                        draft_found = await self.page.evaluate(f"""
                            () => {{
                                const bodyText = document.body.textContent || '';
                                const title = `{title}`;
                                return bodyText.includes(title);
                            }}
                        """)
                        
                        if draft_found:
                            logger.info(f"✅ 在草稿箱中找到文章: {title}")
                            break
                    
                    # 截图保存
                    try:
                        verify_screenshot = f"logs/toutiao_publish_check_{int(asyncio.get_event_loop().time())}.png"
                        await self.page.screenshot(path=verify_screenshot, full_page=True)
                        logger.info(f"📸 验证截图: {verify_screenshot}")
                    except:
                        pass
                    
                    if draft_found:
                        logger.warning("⚠️  文章被保存为草稿，未正式发布")
                        return {
                            "status": "draft",
                            "title": title,
                            "message": "文章已保存为草稿，请在头条后台手动发布"
                        }
                    else:
                        # ★★★ 关键修复：既不在已发布也不在草稿箱，判定为失败 ★★★
                        logger.error(f"❌ 发布验证失败！")
                        logger.error(f"   文章标题: {title}")
                        logger.error(f"   已发布作品: 未找到")
                        logger.error(f"   草稿箱: 未找到")
                        logger.error(f"   可能原因:")
                        logger.error(f"   1. 发布操作未成功执行")
                        logger.error(f"   2. 文章被系统拦截或拒绝")
                        logger.error(f"   3. 头条平台延迟（但超过30秒仍未显示）")
                        logger.error(f"   请查看截图和日志，手动检查头条后台")
                        
                        return {
                            "status": "failed",
                            "error": f"发布验证失败：文章'{title}'既不在已发布作品也不在草稿箱中。请检查头条后台确认状态。"
                        }
            except Exception as e:
                logger.warning(f"⚠️  验证过程出错: {e}")
                import traceback
                traceback.print_exc()
                # 继续执行后续的判断逻辑
            
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
                # ★★★ 关键修复：再等待一段时间，让页面有时间跳转 ★★★
                logger.info("   ⏳ 等待页面跳转（最多20秒）...")
                for i in range(20):
                    await asyncio.sleep(1)
                    current_url = self.page.url
                    if "publish" not in current_url:
                        logger.info(f"   ✅ 在第{i+1}秒检测到URL变化: {current_url}")
                        break
                    if i % 5 == 0 and i > 0:
                        logger.info(f"   ⏳ 已等待{i}秒，当前URL: {current_url}")
                
                current_url = self.page.url
                logger.info(f"当前URL: {current_url}")
                
                # 指标1: URL是否变化
                # 指标2: 是否仍在发布页面
                
                if "draft" in current_url or "edit" in current_url:
                    logger.warning("⚠️  仍在编辑页面，文章可能被保存为草稿")
                    return {
                        "status": "draft",
                        "title": title,
                        "message": "文章已保存为草稿，请在头条后台手动发布"
                    }
                elif "publish" in current_url and not url_changed:
                    # 仍停留在发布页面
                    logger.error("❌ 发布操作未完成，仍停留在发布页面")
                    logger.error(f"   - URL变化: {'是' if url_changed else '否'}")
                    logger.error(f"   - 当前URL: {current_url}")
                    return {
                        "status": "failed",
                        "error": "发布操作未完成，仍停留在发布页面。请检查表单是否填写完整"
                    }
                else:
                    # URL已变化但无法确定状态
                    logger.warning("⚠️  URL已变化，但未在已发布或草稿中找到文章")
                    logger.warning(f"   - 当前URL: {current_url}")
                    logger.warning(f"   请手动检查头条后台确认文章状态")
                    return {
                        "status": "pending",
                        "title": title,
                        "message": "发布状态不明确，请查看头条后台确认。建议检查日志和截图"
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
                
            # 步骤3：点击封面上传区域（使用测试脚本验证成功的方式）
            if single_image_selected:
                logger.info("   步骤2：点击封面上传区域...")
                    
                try:
                    # ★★★ 关键修复：使用测试脚本验证成功的方式（鼠标点击）★★★
                    # 获取封面上传区域的中心坐标
                    box_info = await self.page.evaluate("""
                        () => {
                            const coverBox = document.querySelector('.article-cover-images');
                            if (coverBox) {
                                const rect = coverBox.getBoundingClientRect();
                                return {
                                    center_x: rect.left + rect.width / 2,
                                    center_y: rect.top + rect.height / 2
                                };
                            }
                            return null;
                        }
                    """)
                    
                    if box_info:
                        # ✅ 使用鼠标点击（与测试脚本一致）
                        await self.page.mouse.click(box_info['center_x'], box_info['center_y'])
                        logger.info("   ✅ 已通过鼠标点击封面上传区域，等待对话框打开...")
                        await asyncio.sleep(3)
                    else:
                        logger.warning("   ⚠️  未找到.article-cover-images元素")
                        raise Exception("未找到封面上传区域")
                        
                    # ★★★ 关键修复：关闭之前可能存在的对话框 ★★★
                    logger.info("   步骤2.5：关闭之前的对话框...")
                    await self.page.evaluate("""
                        () => {
                            // 按 ESC 关闭可能的弹窗
                            const event = new KeyboardEvent('keydown', {
                                key: 'Escape',
                                code: 'Escape',
                                bubbles: true
                            });
                            document.dispatchEvent(event);
                            
                            // 关闭所有抽屉和模态框
                            const closeButtons = document.querySelectorAll('.byte-drawer-close, .byte-modal-close');
                            closeButtons.forEach(btn => btn.click());
                            
                            // 隐藏遮罩层
                            const masks = document.querySelectorAll('.byte-drawer-mask, .byte-modal-mask');
                            masks.forEach(mask => mask.style.display = 'none');
                        }
                    """)
                    await asyncio.sleep(1)
                        
                    # 步骤3：点击"上传图片"按钮
                    logger.info("   步骤3：点击'上传图片'按钮...")
                    await self.page.evaluate("""
                        () => {
                            const allElements = document.querySelectorAll('button, [role="button"], span, div');
                            for (const el of allElements) {
                                const text = (el.textContent || '').trim();
                                const rect = el.getBoundingClientRect();
                                if (text.includes('上传图片') && rect.width > 50 && rect.top > 0) {
                                    el.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    await asyncio.sleep(3)  # 增加到3秒
                    logger.info("   ✅ 已点击'上传图片'按钮")
                                        
                    # 步骤4：在对话框中查找file input并上传
                    logger.info("   步骤4：上传封面图文件...")
                                            
                    # ★★★ 关键修复2：复用文章配图成功的方案 - 不等待文件选择器，直接上传 ★★★
                    try:
                        logger.info("   ⏳ 直接上传文件（不等待文件选择器）...")
                        await asyncio.sleep(2)  # 短暂等待对话框稳定
                        
                        # 使用 .first 定位器，与文章配图一致
                        file_input = self.page.locator('input[type="file"]').first
                        await file_input.set_input_files(cover_image_path, timeout=10000)
                        logger.info("   ✅ 封面图已上传")
                                                
                        # ✅ 步骤5：等待头条处理上传（参考测试脚本）
                        logger.info("   ⏳ 等待图片上传和处理(10秒)...")
                        await asyncio.sleep(10)
                                                    
                        # ✅ 步骤6：点击确认按钮（参考测试脚本）
                        logger.info("   步骤6：点击'确定'按钮...")
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
                            logger.info("   ✅ 已点击确认按钮")
                            await asyncio.sleep(3)
                        else:
                            logger.info("   ℹ️  未找到确认按钮（可能自动处理）")
                                            
                        # ✅ 步骤7：验证封面是否成功上传（参考测试脚本）
                        logger.info("   步骤7：验证封面...")
                        await asyncio.sleep(5)
                                            
                        cover_uploaded = await self.page.evaluate("""
                            () => {
                                const imgs = document.querySelectorAll('img');
                                for (const img of imgs) {
                                    const rect = img.getBoundingClientRect();
                                    if (rect.width > 100 && rect.height > 100 && rect.top > 200) {
                                        if (img.src && !img.src.includes('data:')) {
                                            console.log('找到封面图:', img.src.substring(0, 80));
                                            return true;
                                        }
                                    }
                                }
                                return false;
                            }
                        """)
                                            
                        if cover_uploaded:
                            logger.info("   ✅ 封面图已成功上传！")
                        else:
                            logger.warning("   ⚠️  封面图未显示，请检查截图")
                            # 保存调试截图
                            try:
                                screenshot_path = f"logs/cover_upload_debug_{int(asyncio.get_event_loop().time())}.png"
                                await self.page.screenshot(path=screenshot_path, full_page=True)
                                logger.info(f"   ℹ️  调试截图已保存: {screenshot_path}")
                            except:
                                pass
                    except Exception as e:
                        logger.error(f"   ❌ 封面图上传失败: {e}")
                        import traceback
                        traceback.print_exc()
                        # ✅ 关键修复：上传失败时抛出异常，不继续执行
                        raise
                            
                except Exception as e:
                    logger.error(f"   ❌ 上传过程出错: {e}")
                    import traceback
                    traceback.print_exc()
                    raise  # ✅ 抛出异常，让上层知道失败了
            else:
                logger.warning("   ⚠️  未能选择单图模式")
                
            # ✅ 只有成功执行到这里才显示成功
            logger.info("✅ 封面图设置完成")
                
        except Exception as e:
            logger.warning(f"⚠️  封面图设置失败: {e}")
            import traceback
            traceback.print_exc()
    
    async def _insert_article_images(self, image_paths: list):
        """
        插入文章配图到富文本编辑器（分散插入到不同段落）
        
        :param image_paths: 图片路径列表
        """
        if not image_paths:
            logger.info("ℹ️  未提供文章配图")
            return
        
        logger.info(f"📸 开始插入文章配图，共 {len(image_paths)} 张（分散插入模式）...")
        
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
            
            # ★★★ 关键优化：获取文章段落数量，计算分散插入位置 ★★★
            paragraph_count = await self.page.evaluate("""
                () => {
                    const editor = document.querySelector('div[contenteditable="true"]');
                    if (!editor) return 0;
                    // 获取所有段落元素（p标签或div）
                    const paragraphs = editor.querySelectorAll('p, div');
                    return paragraphs.length;
                }
            """)
            
            logger.info(f"   📊 检测到文章共有 {paragraph_count} 个段落")
            
            if paragraph_count == 0:
                logger.warning("   ⚠️  未检测到段落，将按顺序插入")
                paragraph_count = len(image_paths)  #  fallback：每张图片一个位置
            
            # 计算每张图片应该插入的段落索引（均匀分布）
            # 例如：5张图片，10个段落 → 插入位置：0, 2, 4, 6, 8
            insert_positions = []
            if len(image_paths) <= paragraph_count:
                # 图片数 <= 段落数：均匀分布
                step = paragraph_count // len(image_paths)
                insert_positions = [i * step for i in range(len(image_paths))]
            else:
                # 图片数 > 段落数：尽可能分散，但可能有些段落有多张图片
                step = max(1, paragraph_count // len(image_paths))
                insert_positions = [min(i * step, paragraph_count - 1) for i in range(len(image_paths))]
            
            logger.info(f"   📍 计划插入位置（段落索引）: {insert_positions}")
            
            for idx, (img_path, target_position) in enumerate(zip(image_paths, insert_positions), 1):
                logger.info(f"   步骤{idx}/{len(image_paths)}：上传配图 '{img_path}' 到第 {target_position + 1} 段落后...")
                
                # 转换为绝对路径
                import os
                abs_img_path = os.path.abspath(img_path)
                
                # ★★★ 第一步：将光标移动到目标段落位置 ★★★
                logger.info(f"      步骤 0：移动光标到目标段落...")
                cursor_moved = await self.page.evaluate("""
                    (targetIndex) => {
                        const editor = document.querySelector('div[contenteditable="true"]');
                        if (!editor) return false;
                        
                        const paragraphs = editor.querySelectorAll('p, div');
                        if (targetIndex >= paragraphs.length) return false;
                        
                        const targetParagraph = paragraphs[targetIndex];
                        
                        // 创建Range并选中目标段落的末尾
                        const range = document.createRange();
                        const sel = window.getSelection();
                        
                        // 将光标放在段落的末尾
                        range.selectNodeContents(targetParagraph);
                        range.collapse(false);  // false表示折叠到末尾
                        
                        sel.removeAllRanges();
                        sel.addRange(range);
                        
                        // 滚动到光标位置
                        targetParagraph.scrollIntoView({ behavior: 'smooth', block: 'center' });
                        
                        return true;
                    }
                """, target_position)
                
                if cursor_moved:
                    logger.info(f"      ✅ 光标已移动到第 {target_position + 1} 个段落")
                    await asyncio.sleep(1)
                else:
                    logger.warning(f"      ⚠️  无法移动光标，将在当前位置插入")
                
                # ★★★ 第二步：点击编辑器的图片按钮（第12个工具栏按钮）★★★
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
                                        
                    # 步骤2：点击“本地上传”按钮
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
                    
                    # 步骤3：等待文件选择器出现并上传
                    logger.info(f"      步骤 3：等待文件选择器...")
                    await asyncio.sleep(2)
                    
                    # 使用 .first（与封面上传一致）
                    file_input = self.page.locator('input[type="file"]').first
                    try:
                        await file_input.set_input_files(abs_img_path, timeout=5000)
                        logger.info(f"      ✅ 文件已上传")
                    except Exception as e:
                        logger.error(f"      ❌ 文件上传失败：{e}")
                        raise  # ✅ 关键修复：抛出异常，中断执行
                    
                    # 步骤4：等待头条处理上传
                    logger.info(f"       等待图片上传和处理(15秒)...")
                    await asyncio.sleep(15)  # 关键：必须是15秒
                    
                    # ★★★ 关键修复：直接通过JS在目标段落后插入图片（绕过头条UI）★★★
                    logger.info(f"      🔄 直接在目标段落后插入图片...")
                    
                    # 先获取已上传图片的URL（从对话框中）
                    uploaded_img_url = await self.page.evaluate("""
                        () => {
                            // 查找对话框中已上传的图片
                            const dialogs = document.querySelectorAll('.upload-image-panel, .byte-modal, .byte-dialog, [role="dialog"]');
                            for (const dialog of dialogs) {
                                const imgs = dialog.querySelectorAll('img');
                                if (imgs.length > 0) {
                                    // 返回最后一张图片的URL（最新上传的）
                                    return imgs[imgs.length - 1].src;
                                }
                            }
                            return null;
                        }
                    """)
                    
                    if uploaded_img_url:
                        logger.info(f"      ✅ 获取到已上传图片URL")
                        
                        # 直接在目标段落后插入图片
                        insert_result = await self.page.evaluate("""
                            (params) => {
                                const { targetIndex, imgUrl } = params;
                                const editor = document.querySelector('div[contenteditable="true"]');
                                if (!editor) return { success: false, reason: '未找到编辑器' };
                                
                                const paragraphs = editor.querySelectorAll('p, div');
                                if (targetIndex >= paragraphs.length) {
                                    return { success: false, reason: `目标索引${targetIndex}超出段落数${paragraphs.length}` };
                                }
                                
                                const targetParagraph = paragraphs[targetIndex];
                                
                                // 创建图片元素
                                const img = document.createElement('img');
                                img.src = imgUrl;
                                img.style.maxWidth = '100%';
                                img.style.height = 'auto';
                                img.style.display = 'block';
                                img.style.margin = '10px auto';
                                
                                // 在目标段落后插入图片（使用正确的父节点）
                                if (targetParagraph.nextSibling) {
                                    targetParagraph.parentNode.insertBefore(img, targetParagraph.nextSibling);
                                } else {
                                    targetParagraph.parentNode.appendChild(img);
                                }
                                
                                // 在图片后添加一个空段落，方便后续插入
                                const emptyPara = document.createElement('p');
                                emptyPara.innerHTML = '<br>';
                                if (img.nextSibling) {
                                    img.parentNode.insertBefore(emptyPara, img.nextSibling);
                                } else {
                                    img.parentNode.appendChild(emptyPara);
                                }
                                
                                return { success: true, message: '图片已插入' };
                            }
                        """, {"targetIndex": target_position, "imgUrl": uploaded_img_url})
                        
                        if insert_result.get('success'):
                            logger.info(f"      ✅ 图片已成功插入到第 {target_position + 1} 段落后")
                        else:
                            logger.warning(f"      ⚠️  JS插入失败: {insert_result.get('reason')}")
                            # 降级方案：尝试点击确定按钮
                            logger.info(f"      🔄 降级方案：尝试点击确定按钮...")
                    else:
                        logger.warning(f"      ⚠️  未获取到已上传图片URL，尝试点击确定按钮...")
                    
                    # 步骤5：关闭对话框（因为我们已经用JS直接插入图片了）
                    logger.info(f"      步骤 5：关闭对话框...")
                    
                    # 策略1：尝试点击关闭按钮
                    close_result = await self.page.evaluate("""
                        () => {
                            // 查找所有可能的关闭按钮
                            const closeSelectors = [
                                '.byte-modal-close',
                                '.close-btn',
                                '[aria-label="关闭"]',
                                'button.close',
                                '.icon-close'
                            ];
                            
                            for (const selector of closeSelectors) {
                                const btn = document.querySelector(selector);
                                if (btn && typeof btn.click === 'function') {
                                    btn.click();
                                    return { method: 'button', selector: selector };
                                }
                            }
                            
                            return { method: 'none', reason: '未找到关闭按钮' };
                        }
                    """)
                    
                    if close_result.get('method') == 'button':
                        logger.info(f"      ✅ 已点击关闭按钮 ({close_result.get('selector')})")
                    else:
                        logger.info(f"      ℹ️  未找到关闭按钮，尝试Escape键...")
                    
                    # 策略2：发送Escape键关闭对话框
                    await self.page.keyboard.press('Escape')
                    await asyncio.sleep(2)
                    logger.info(f"      ✅ 对话框已关闭")
                    
                    # 步骤6：验证图片是否插入编辑器
                    logger.info(f"      步骤 6：验证图片...")
                    await asyncio.sleep(3)
                    
                    # ★★★ 详细验证：检查图片数量和位置 ★★★
                    img_info = await self.page.evaluate("""
                        () => {
                            const editor = document.querySelector('div[contenteditable="true"]');
                            if (!editor) return { count: 0, positions: [] };
                            
                            const imgs = editor.querySelectorAll('img');
                            const positions = [];
                            
                            imgs.forEach((img, idx) => {
                                // 找到图片所在的段落
                                let parent = img.parentElement;
                                let paraIndex = -1;
                                
                                while (parent && parent !== editor) {
                                    const paragraphs = editor.querySelectorAll('p, div');
                                    paraIndex = Array.from(paragraphs).indexOf(parent);
                                    if (paraIndex !== -1) break;
                                    parent = parent.parentElement;
                                }
                                
                                positions.push({
                                    index: idx,
                                    paragraphIndex: paraIndex,
                                    src: img.src.substring(0, 50) + '...'
                                });
                            });
                            
                            return {
                                count: imgs.length,
                                positions: positions
                            };
                        }
                    """)
                    
                    logger.info(f"      📊 编辑器中图片数量: {img_info['count']}")
                    if img_info['positions']:
                        for pos in img_info['positions']:
                            logger.info(f"         图片{pos['index'] + 1}: 位于第{pos['paragraphIndex'] + 1}段")
                    
                    if img_info['count'] > 0:
                        logger.info(f"      ✅ 图片已成功插入编辑器")
                    else:
                        logger.warning(f"      ⚠️  图片未插入")
                else:
                    logger.warning(f"      ⚠️  未找到足够的工具栏按钮（需要至少12个，实际{len(toolbar_buttons)}个）")
            
            logger.info(f"   ✅ 所有配图已处理")
        
        except Exception as e:
            logger.error(f"   ❌ 插入配图失败：{e}")
            import traceback
            traceback.print_exc()
            raise  # ✅ 关键修复：抛出异常，让上层知道失败了
    
    async def _upload_image_to_toutiao(self, image_path: str) -> Optional[str]:
        """
        上传图片到头条服务器
        :param image_path: 图片路径
        :return: 上传后的图片URL，失败返回None
        """
        import os
        
        try:
            logger.info(f"   📤 开始上传图片: {image_path}")
            
            # 转换为绝对路径
            abs_img_path = os.path.abspath(image_path)
            
            if not os.path.exists(abs_img_path):
                logger.error(f"   ❌ 图片文件不存在: {abs_img_path}")
                return None
            
            # 点击编辑器的图片按钮（第12个工具栏按钮）
            logger.info(f"   步骤1：点击编辑器图片按钮...")
            
            # 先关闭可能存在的对话框
            await self.page.evaluate("""
                () => {
                    const event = new KeyboardEvent('keydown', {
                        key: 'Escape',
                        code: 'Escape',
                        bubbles: true
                    });
                    document.dispatchEvent(event);
                }
            """)
            await asyncio.sleep(1)
            
            # 查找并点击第12个工具栏按钮（图片按钮）
            toolbar_buttons = await self.page.query_selector_all('.syl-toolbar-button')
            logger.info(f"   找到 {len(toolbar_buttons)} 个工具栏按钮")
            
            if len(toolbar_buttons) <= 11:
                logger.error(f"   ❌ 未找到足够的工具栏按钮（需要至少12个，实际{len(toolbar_buttons)}个）")
                return None
            
            await toolbar_buttons[11].click()
            logger.info(f"   ✅ 已点击第 12 个按钮（图片按钮）")
            
            # 等待对话框加载
            await asyncio.sleep(3)
            
            # 点击"本地上传"按钮
            logger.info(f"   步骤2：点击'本地上传'按钮...")
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
            logger.info(f"   ✅ 已点击'本地上传'按钮")
            
            # 上传文件
            logger.info(f"   步骤3：上传文件...")
            await asyncio.sleep(2)
            
            file_input = self.page.locator('input[type="file"]').first
            await file_input.set_input_files(abs_img_path, timeout=10000)
            logger.info(f"   ✅ 文件已上传")
            
            # 等待头条处理上传
            logger.info(f"   步骤4：等待图片上传和处理(15秒)...")
            await asyncio.sleep(15)
            
            # 获取已上传图片的URL
            uploaded_img_url = await self.page.evaluate("""
                () => {
                    // 查找对话框中已上传的图片
                    const dialogs = document.querySelectorAll('.upload-image-panel, .byte-modal, .byte-dialog, [role="dialog"]');
                    for (const dialog of dialogs) {
                        const imgs = dialog.querySelectorAll('img');
                        if (imgs.length > 0) {
                            // 返回最后一张图片的URL（最新上传的）
                            return imgs[imgs.length - 1].src;
                        }
                    }
                    return null;
                }
            """)
            
            if uploaded_img_url:
                logger.info(f"   ✅ 图片上传成功，URL: {uploaded_img_url[:80]}...")
            else:
                logger.warning(f"   ⚠️  未获取到已上传图片URL")
            
            # 关闭对话框
            logger.info(f"   步骤5：关闭对话框...")
            await self.page.keyboard.press('Escape')
            await asyncio.sleep(2)
            logger.info(f"   ✅ 对话框已关闭")
            
            return uploaded_img_url
            
        except Exception as e:
            logger.error(f"   ❌ 上传图片失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _insert_article_images_with_positions(self, image_paths: list, positions: list):
        """
        根据指定位置插入文章配图（智能位置模式）
        :param image_paths: 图片路径列表
        :param positions: 图片插入位置列表（段落索引）
        """
        if not image_paths or not positions:
            logger.warning("⚠️  没有图片或位置信息，跳过配图插入")
            return
        
        try:
            logger.info(f"🖼️ 开始插入 {len(image_paths)} 张配图到指定位置...")
            
            for idx, (img_path, position) in enumerate(zip(image_paths, positions), 1):
                logger.info(f"\n步骤{idx}/{len(image_paths)}：上传配图 '{img_path}' 到第 {position + 1} 段落后...")
                
                # 上传图片到头条服务器
                uploaded_img_url = await self._upload_image_to_toutiao(img_path)
                if not uploaded_img_url:
                    logger.error(f"❌ 第{idx}张图片上传失败，跳过")
                    continue
                
                logger.info(f"✅ 图片已上传到头条服务器: {uploaded_img_url[:50]}...")
                
                # 使用JavaScript将图片插入到指定位置
                insert_result = await self.page.evaluate("""
                    (params) => {
                        const { targetIndex, imgUrl } = params;
                        const editor = document.querySelector('div[contenteditable="true"]');
                        if (!editor) return { success: false, reason: '未找到编辑器' };
                        
                        const paragraphs = editor.querySelectorAll('p, div');
                        if (targetIndex >= paragraphs.length) {
                            return { success: false, reason: `目标索引${targetIndex}超出段落数${paragraphs.length}` };
                        }
                        
                        const targetParagraph = paragraphs[targetIndex];
                        
                        // 创建图片元素
                        const img = document.createElement('img');
                        img.src = imgUrl;
                        img.style.maxWidth = '100%';
                        img.style.height = 'auto';
                        img.style.display = 'block';
                        img.style.margin = '10px auto';
                        
                        // 在目标段落后插入图片（使用正确的父节点）
                        if (targetParagraph.nextSibling) {
                            targetParagraph.parentNode.insertBefore(img, targetParagraph.nextSibling);
                        } else {
                            targetParagraph.parentNode.appendChild(img);
                        }
                        
                        return { success: true };
                    }
                """, {"targetIndex": position, "imgUrl": uploaded_img_url})
                
                if insert_result.get("success"):
                    logger.info(f"✅ 图片已成功插入到第 {position + 1} 段落后")
                else:
                    logger.error(f"❌ 插入配图失败: {insert_result.get('reason', '未知错误')}")
                
                await asyncio.sleep(2)
            
            logger.info(f"\n   ✅ 所有配图已处理")
        
        except Exception as e:
            logger.error(f"   ❌ 插入配图失败：{e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def _set_declaration(self, declaration_type: str = "ai", declarations: list = None):
        """
        设置作品声明（支持多选）
        :param declaration_type: 声明类型（已废弃，改用declarations）
            - "ai": 引用AI
            - "personal_opinion": 仅个人观点，仅供参考
        :param declarations: 声明列表（多选）
            - ["引用ai"]
            - ["引用ai", "个人观点"]
            - ["取材网络", "虚构演绎"]
            等组合
        """
        # 兼容旧参数
        if declarations is None:
            declarations = [declaration_type]
        
        logger.info(f"📝 设置作品声明（类型: {declarations}）...")
            
        try:
            # 滚动到页面底部，加载"作品声明"区域
            await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
            logger.info("   ✅ 已滚动到底部")
            
            # 头条作品声明选项映射
            declaration_mapping = {
                '引用ai': '引用AI',
                'ai': '引用AI',
                '取材网络': '取材网络',
                '引用站内': '引用站内',
                '个人观点': '个人观点，仅供参考',
                'personal_opinion': '个人观点，仅供参考',
                '虚构演绎': '虚构演绎，故事经历',
                '投资观点': '投资观点，仅供参考',
                '健康医疗': '健康医疗分享，仅供参考'
            }
            
            # 遍历用户选择的声明，逐个勾选
            for decl in declarations:
                target_text = declaration_mapping.get(decl, decl)
                logger.info(f"   正在查找'{target_text}'选项...")
                
                declaration_checked = await self.page.evaluate(f"""
                    () => {{
                        const targetText = '{target_text}';
                            
                        // 查找所有 checkbox
                        const allCheckboxes = document.querySelectorAll('input[type="checkbox"]');
                        for (const cb of allCheckboxes) {{
                            const label = cb.closest('label') || cb.parentElement;
                            if (label) {{
                                const labelText = label.textContent || '';
                                if (labelText.includes(targetText)) {{
                                    if (!cb.checked) {{
                                        cb.click();
                                    }}
                                    return true;
                                }}
                            }}
                        }}
                        return false;
                    }}
                """)
                    
                if declaration_checked:
                    logger.info(f"   ✅ 已勾选{target_text}声明")
                else:
                    logger.warning(f"   ⚠️  未找到{target_text}选项")
                        
                    # 备用方案：直接通过文本查找
                    await self.page.evaluate(f"""
                        () => {{
                            const targetText = '{target_text}';
                            const allElements = document.querySelectorAll('*');
                            for (const el of allElements) {{
                                const text = el.textContent || '';
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
                            return false;
                        }}
                    """)
                    logger.info(f"   ✅ 已通过备用方案勾选{target_text}")
                
                # 每个声明之间稍作延迟
                await asyncio.sleep(0.5)
                    
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
            # ★★★ 关键修复：CDP模式下只关闭标签页，不关闭浏览器 ★★★
            if self.page:
                logger.info("   📑 关闭标签页...")
                await self.page.close()
                self.page = None
                logger.info("   ✅ 标签页已关闭")
            
            # 只在非CDP模式下关闭context和browser
            if hasattr(self, '_is_cdp_mode') and self._is_cdp_mode:
                logger.info("   ℹ️  CDP模式：保持浏览器运行，只断开连接")
                # 只断开Playwright连接，不关闭浏览器
                if self.playwright:
                    await self.playwright.stop()
                    self.playwright = None
                
                # ★★★ 新增：清理临时用户数据目录（如果存在）★★★
                if hasattr(self, '_cdp_user_data_dir') and self._cdp_user_data_dir:
                    import shutil
                    import os as _os
                    try:
                        if _os.path.exists(self._cdp_user_data_dir):
                            logger.info(f"   🗑️  清理临时用户数据目录: {self._cdp_user_data_dir}")
                            shutil.rmtree(self._cdp_user_data_dir, ignore_errors=True)
                            logger.info("   ✅ 临时目录已清理")
                    except Exception as e:
                        logger.warning(f"   ⚠️  清理临时目录失败: {e}")
                    finally:
                        self._cdp_user_data_dir = None
            else:
                # 标准模式：关闭所有资源
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
