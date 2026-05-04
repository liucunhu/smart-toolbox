"""
抖音自动化发布引擎
使用 Playwright 实现抖音创作者平台的自动化发布
"""
import asyncio
import json
import time
from playwright.async_api import async_playwright, BrowserContext
from app.utils.logger import logger
from app.rpa.rpa_retry import RPARetryHelper
from typing import Dict, Any, Optional


class DouyinPublisher:
    """抖音自动化发布引擎"""

    def __init__(self, account_id: int, cookies: Optional[str] = None):
        self.account_id = account_id
        self.cookies = cookies
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page = None

    async def initialize_browser(self, headless: bool = True):
        """初始化浏览器"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=headless)
        
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        
        self.context = await self.browser.new_context(**context_options)
        
        # 如果提供了 cookies，则加载
        if self.cookies:
            try:
                cookies_list = json.loads(self.cookies)
                await self.context.add_cookies(cookies_list)
                logger.info(f"已加载账号 {self.account_id} 的 Cookie")
            except Exception as e:
                logger.warning(f"加载 Cookie 失败：{str(e)}")
        
        self.page = await self.context.new_page()

    async def login_with_manual_input(self, username: str, password: str) -> Dict[str, Any]:
        """
        人工辅助登录（自动填充账号密码，手动完成验证码）
        """
        logger.info(f"开始登录抖音账号: {username}")
        
        try:
            # 访问抖音登录页
            await self.page.goto("https://creator.douyin.com/", timeout=30000)
            await self.page.wait_for_load_state("networkidle")
            
            # 等待登录按钮并点击
            await self.page.wait_for_selector('text=登录', timeout=10000)
            await self.page.click('text=登录')
            await asyncio.sleep(2)
            
            # 切换到手机号登录
            try:
                await self.page.click('text=手机号登录')
                await asyncio.sleep(1)
            except:
                pass  # 可能已经在手机号登录页面
            
            # 填充手机号
            try:
                await RPARetryHelper.fill_with_retry(
                    self.page, 
                    'input[placeholder*="手机号"]', 
                    username
                )
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"填充手机号失败: {str(e)}")
            
            # 填充密码
            try:
                await RPARetryHelper.fill_with_retry(
                    self.page, 
                    'input[type="password"]', 
                    password
                )
                await asyncio.sleep(1)
            except Exception as e:
                logger.warning(f"填充密码失败: {str(e)}")
            
            # 点击登录按钮
            try:
                await RPARetryHelper.click_with_retry(
                    self.page, 
                    'text=登录'
                )
            except Exception as e:
                logger.warning(f"点击登录按钮失败: {str(e)}")
            
            logger.info("已自动填充账号密码，请在浏览器中手动完成验证码...")
            
            # 等待登录成功（最多等待 120 秒）
            try:
                await self.page.wait_for_url("**/creator.douyin.com/**", timeout=120000)
                logger.info("登录成功！")
            except:
                logger.warning("等待超时，请检查是否登录成功")
            
            # 保存 Cookie
            cookies = await self.context.cookies()
            
            return {
                "status": "success",
                "cookies": json.dumps(cookies),
                "message": "登录成功，请在浏览器中确认"
            }
            
        except Exception as e:
            logger.error(f"登录失败：{str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def publish_video(
        self,
        title: str,
        video_path: str,
        description: str = "",
        tags: list = None
    ) -> Dict[str, Any]:
        """
        发布视频到抖音
        """
        logger.info(f"开始发布视频：{title}")
        
        try:
            # 访问发布页面
            await self.page.goto("https://creator.douyin.com/creator-micro/content/upload", timeout=30000)
            await self.page.wait_for_load_state("networkidle")
            await asyncio.sleep(3)
            
            # 上传视频文件
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(video_path)
                logger.info("视频文件已上传")
                await asyncio.sleep(5)  # 等待上传完成
            
            # 填写标题
            title_input = await self.page.query_selector('textarea[placeholder*="标题"]')
            if title_input:
                await title_input.fill(title)
                await asyncio.sleep(1)
            
            # 填写描述
            if description:
                desc_input = await self.page.query_selector('textarea[placeholder*="描述"]')
                if desc_input:
                    await desc_input.fill(description)
                    await asyncio.sleep(1)
            
            # 添加标签
            if tags:
                for tag in tags[:5]:  # 最多 5 个标签
                    try:
                        tag_input = await self.page.query_selector('input[placeholder*="添加标签"]')
                        if tag_input:
                            await tag_input.fill(tag)
                            await self.page.keyboard.press('Enter')
                            await asyncio.sleep(1)
                    except:
                        break
            
            # 点击发布按钮
            publish_button = await self.page.query_selector('text=发布')
            if publish_button:
                await publish_button.click()
                logger.info("已点击发布按钮")
                await asyncio.sleep(5)
            
            # 等待发布完成
            try:
                await self.page.wait_for_selector('text=发布成功', timeout=30000)
                logger.info("视频发布成功！")
                return {
                    "status": "success",
                    "message": "视频发布成功"
                }
            except:
                logger.warning("未检测到发布成功提示，请手动确认")
                return {
                    "status": "pending",
                    "message": "发布任务已提交，请手动确认"
                }
            
        except Exception as e:
            logger.error(f"发布失败：{str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def close(self):
        """关闭浏览器"""
        if self.browser:
            await self.browser.close()
            logger.info("浏览器已关闭")
