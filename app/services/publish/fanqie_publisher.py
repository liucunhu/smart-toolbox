"""
番茄小说自动化发布服务
支持：创建新书、发布章节、定时发布、数据抓取
"""
import asyncio
import json
import time
from playwright.async_api import async_playwright, BrowserContext, Page
from app.utils.logger import logger
from typing import Dict, Any, Optional, List


class FanqiePublisher:
    """番茄小说自动化发布引擎"""
    
    def __init__(self, account_id: int):
        self.account_id = account_id
        self.playwright = None
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self._is_cdp_mode = False
        self._cdp_user_data_dir = None
    
    async def initialize_browser(self, use_cdp: bool = True, cdp_port: int = 9222):
        """初始化浏览器"""
        if use_cdp:
            await self.initialize_with_cdp(cdp_port)
        else:
            await self.initialize_standard_browser()
    
    async def initialize_with_cdp(self, cdp_port: int = 9222):
        """使用CDP连接真实Edge浏览器"""
        import subprocess
        import os
        import socket
        import tempfile
        
        self._is_cdp_mode = True
        
        logger.info("🚀 使用CDP模式连接真实Edge浏览器...")
        
        edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
        if not os.path.exists(edge_path):
            edge_path = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        
        if not os.path.exists(edge_path):
            raise FileNotFoundError("未找到 Edge 浏览器")
        
        # 检查CDP端口是否可用
        cdp_available = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', cdp_port))
            if result == 0:
                cdp_available = True
                logger.info(f"⚠️  CDP端口 {cdp_port} 已被占用，尝试复用现有浏览器")
            sock.close()
        except:
            pass
        
        if not cdp_available:
            logger.info(f"[1/3] 启动Edge浏览器（远程调试端口 {cdp_port}）...")
            
            temp_dir = tempfile.gettempdir()
            user_data_dir = os.path.join(temp_dir, f"smart-toolbox-fanqie-cdp-{int(time.time())}")
            self._cdp_user_data_dir = user_data_dir
            
            logger.info(f"   使用独立用户数据目录: {user_data_dir}")
            
            abs_user_data_dir = os.path.abspath(user_data_dir)
            
            cmd = [
                edge_path,
                f'--remote-debugging-port={cdp_port}',
                f'--user-data-dir="{abs_user_data_dir}"',
                '--no-first-run',
                '--no-default-browser-check',
                '--start-maximized',
                '--window-size=1920,1080',
                'about:blank',
            ]
            
            logger.info(f"   执行命令: {' '.join(cmd)}")
            
            creation_flags = 0
            if os.name == 'nt':
                import subprocess as sp
                creation_flags = sp.CREATE_NEW_CONSOLE
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=creation_flags
            )
            logger.info(f"✅ Edge浏览器进程已启动 (PID: {process.pid})")
            
            # 等待CDP端口就绪
            logger.info(f"   等待 CDP 端口 {cdp_port} 就绪...")
            max_retries = 40
            retry_count = 0
            cdp_ready = False
            
            while retry_count < max_retries:
                await asyncio.sleep(1)
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
                raise TimeoutError(f"Edge 浏览器启动超时，CDP 端口 {cdp_port} 无法连接")
        else:
            logger.info("   ✅ 使用现有的Edge浏览器实例")
        
        # 连接到Edge浏览器
        logger.info(f"[2/3] 连接到Edge浏览器（CDP端口 {cdp_port}）...")
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.connect_over_cdp(f"http://127.0.0.1:{cdp_port}")
        
        contexts = self.browser.contexts
        if not contexts:
            self.context = await self.browser.new_context(
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai"
            )
        else:
            self.context = contexts[0]
        
        logger.info("   📑 创建新的标签页...")
        self.page = await self.context.new_page()
        logger.info(f"   ✅ 新标签页已创建")
        
        # 注入反检测脚本
        logger.info("   🛡️  注入反检测脚本...")
        await self.page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            window.chrome = {
                runtime: {},
            };
            
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
        """)
        
        logger.info("[3/3] 浏览器初始化完成")
    
    async def initialize_standard_browser(self):
        """标准浏览器模式"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            locale="zh-CN",
            timezone_id="Asia/Shanghai"
        )
        self.page = await self.context.new_page()
    
    async def login_with_cookies(self, cookies: str) -> bool:
        """使用Cookie登录番茄作家后台"""
        try:
            logger.info("尝试使用Cookie登录番茄作家后台...")
            
            await self.page.goto("https://fanqienovel.com/writer/")
            await asyncio.sleep(3)
            
            cookies_list = json.loads(cookies)
            await self.context.add_cookies(cookies_list)
            
            await self.page.reload()
            await asyncio.sleep(5)
            
            is_logged = await self.check_login_status()
            
            if is_logged:
                logger.info("✅ Cookie登录成功")
            else:
                logger.warning("⚠️  Cookie登录失败，可能需要重新登录")
            
            return is_logged
            
        except Exception as e:
            logger.error(f"登录失败: {e}")
            return False
    
    async def check_login_status(self) -> bool:
        """检查是否已登录"""
        try:
            current_url = self.page.url
            if "login" in current_url.lower():
                return False
            
            user_info = await self.page.query_selector('.writer-user-info, .user-avatar, .account-name')
            return user_info is not None
        except:
            return False
    
    async def create_novel(
        self,
        title: str,
        category: str,
        tags: List[str],
        introduction: str,
        cover_image_path: str = None
    ) -> Dict[str, Any]:
        """创建新书"""
        try:
            logger.info(f"开始创建新书: {title}")
            
            await self.page.goto("https://fanqienovel.com/writer/create")
            await asyncio.sleep(3)
            
            # 填写标题
            title_input = await self.page.query_selector('input[placeholder*="标题"], input[name="title"]')
            if title_input:
                await title_input.fill(title)
                await asyncio.sleep(1)
            
            # 选择分类
            category_select = await self.page.query_selector('select[name="category"], select.category-select')
            if category_select:
                await category_select.select_option(category)
                await asyncio.sleep(1)
            
            # 填写简介
            intro_textarea = await self.page.query_selector('textarea[name="introduction"], textarea.intro')
            if intro_textarea:
                await intro_textarea.fill(introduction)
                await asyncio.sleep(1)
            
            # 添加标签
            for tag in tags[:5]:  # 最多5个标签
                tag_input = await self.page.query_selector('input[placeholder*="标签"], input.tag-input')
                if tag_input:
                    await tag_input.fill(tag)
                    await self.page.press('input[placeholder*="标签"], input.tag-input', 'Enter')
                    await asyncio.sleep(0.5)
            
            # 上传封面
            if cover_image_path:
                await self.upload_cover(cover_image_path)
            
            # 提交创建
            submit_btn = await self.page.query_selector('button[type="submit"], button.create-btn')
            if submit_btn:
                await submit_btn.click()
                await asyncio.sleep(5)
            
            # 获取新书ID
            novel_id = await self.extract_novel_id()
            
            if novel_id:
                logger.info(f"✅ 新书创建成功，ID: {novel_id}")
                return {
                    "status": "success",
                    "novel_id": novel_id,
                    "message": "新书创建成功"
                }
            else:
                logger.warning("⚠️  未获取到小说ID，但可能创建成功")
                return {
                    "status": "success",
                    "novel_id": None,
                    "message": "新书可能创建成功，但未获取到ID"
                }
            
        except Exception as e:
            logger.error(f"创建新书失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def publish_chapter(
        self,
        novel_id: str,
        chapter_number: int,
        title: str,
        content: str,
        scheduled_time: str = None
    ) -> Dict[str, Any]:
        """发布章节"""
        try:
            logger.info(f"发布第{chapter_number}章: {title}")
            
            await self.page.goto(f"https://fanqienovel.com/writer/novel/{novel_id}/chapter/new")
            await asyncio.sleep(3)
            
            # 填写章节标题
            title_input = await self.page.query_selector('input[name="chapter_title"], input.chapter-title')
            if title_input:
                await title_input.fill(title)
                await asyncio.sleep(1)
            
            # 填写章节内容
            content_editor = await self.page.query_selector('textarea[name="content"], div.editor-content, div.ProseMirror')
            if content_editor:
                if content_editor.tag_name() == 'textarea':
                    await content_editor.fill(content)
                else:
                    await self.page.evaluate(f'''
                        () => {{
                            const editor = document.querySelector('div.ProseMirror, div.editor-content');
                            if (editor) {{
                                editor.innerHTML = `{content.replace(chr(10), '<br>')}`;
                            }}
                        }}
                    ''')
                await asyncio.sleep(2)
            
            # 设置定时发布
            if scheduled_time:
                await self.enable_scheduled_publish(scheduled_time)
            
            # 点击发布按钮
            publish_btn = await self.page.query_selector('button.publish-btn, button:has-text("发布"), button:has-text("立即发布")')
            if publish_btn:
                await publish_btn.click()
                await asyncio.sleep(5)
            
            # 验证发布结果
            success = await self.verify_chapter_published(novel_id, chapter_number)
            
            if success:
                chapter_id = await self.extract_chapter_id()
                logger.info(f"✅ 章节发布成功，ID: {chapter_id}")
                return {
                    "status": "success",
                    "chapter_id": chapter_id,
                    "message": f"第{chapter_number}章发布成功"
                }
            else:
                return {
                    "status": "failed",
                    "error": "发布验证失败"
                }
            
        except Exception as e:
            logger.error(f"发布章节失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def upload_cover(self, image_path: str):
        """上传封面图"""
        try:
            file_input = await self.page.query_selector('input[type="file"][accept*="image"]')
            if file_input:
                await file_input.set_input_files(image_path)
                await asyncio.sleep(3)
                logger.info(f"✅ 封面图上传成功: {image_path}")
        except Exception as e:
            logger.warning(f"封面图上传失败: {e}")
    
    async def enable_scheduled_publish(self, scheduled_time: str):
        """启用定时发布"""
        try:
            schedule_checkbox = await self.page.query_selector('input[type="checkbox"].schedule-publish')
            if schedule_checkbox:
                await schedule_checkbox.check()
                await asyncio.sleep(1)
                
                time_input = await self.page.query_selector('input[type="datetime-local"], input.schedule-time')
                if time_input:
                    await time_input.fill(scheduled_time)
                    await asyncio.sleep(1)
                    logger.info(f"✅ 定时发布已设置: {scheduled_time}")
        except Exception as e:
            logger.warning(f"设置定时发布失败: {e}")
    
    async def verify_chapter_published(self, novel_id: str, chapter_number: int) -> bool:
        """验证章节是否发布成功"""
        try:
            await asyncio.sleep(3)
            
            # 检查是否有成功提示
            success_msg = await self.page.query_selector('text=发布成功, text=操作成功, .success-message')
            if success_msg:
                return True
            
            # 检查当前URL是否还在编辑页
            current_url = self.page.url
            if "chapter/new" not in current_url and "edit" not in current_url:
                return True
            
            return False
        except:
            return False
    
    async def extract_novel_id(self) -> Optional[str]:
        """从页面提取小说ID"""
        try:
            current_url = self.page.url
            if "novel/" in current_url:
                novel_id = current_url.split("novel/")[1].split("/")[0]
                return novel_id
            return None
        except:
            return None
    
    async def extract_chapter_id(self) -> Optional[str]:
        """从页面提取章节ID"""
        try:
            current_url = self.page.url
            if "chapter/" in current_url:
                chapter_id = current_url.split("chapter/")[1].split("/")[0]
                return chapter_id
            return None
        except:
            return None
    
    async def fetch_analytics(self, novel_id: str, days: int = 7) -> Dict[str, Any]:
        """抓取数据分析"""
        try:
            logger.info(f"抓取小说 {novel_id} 的数据分析")
            
            await self.page.goto(f"https://fanqienovel.com/writer/novel/{novel_id}/analytics")
            await asyncio.sleep(5)
            
            analytics_data = {}
            
            # 抓取各项数据（需要根据实际页面结构调整选择器）
            metrics_selectors = {
                "daily_reads": ".metric-daily-reads, [data-metric='reads']",
                "new_followers": ".metric-new-followers, [data-metric='followers']",
                "completion_rate": ".metric-completion-rate, [data-metric='completion']",
                "ad_revenue": ".metric-revenue, [data-metric='revenue']",
            }
            
            for metric_name, selector in metrics_selectors.items():
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        text = await element.text_content()
                        analytics_data[metric_name] = float(''.join(filter(str.isdigit, text)) or 0)
                except:
                    analytics_data[metric_name] = 0
            
            logger.info(f"✅ 数据抓取成功")
            return {
                "status": "success",
                "data": analytics_data
            }
            
        except Exception as e:
            logger.error(f"数据抓取失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def close(self):
        """关闭浏览器"""
        try:
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("✅ 浏览器已关闭")
        except Exception as e:
            logger.error(f"关闭浏览器失败: {e}")
