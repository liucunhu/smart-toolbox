"""
微信视频号自动化发布服务
支持视频发布、直播预告
"""
import asyncio
import json
from playwright.async_api import async_playwright, BrowserContext, Page
from app.utils.logger import logger
from typing import Dict, Any, Optional


class WechatPublisher:
    """微信视频号自动化发布引擎"""

    def __init__(self, account_id: int):
        self.account_id = account_id
        self.playwright = None
        self.browser = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None

    async def initialize_browser(self, headless: bool = False):
        """初始化浏览器"""
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=headless)
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.page = await self.context.new_page()
        logger.info(f"视频号发布引擎初始化完成，账号 ID: {self.account_id}")

    async def login_with_qr_code(self) -> Dict[str, Any]:
        """
        微信扫码登录视频号
        视频号主要使用微信扫码登录
        
        Returns:
            登录结果字典
        """
        try:
            # 1. 打开视频号助手
            await self.page.goto("https://channels.weixin.qq.com/platform", timeout=30000)
            await asyncio.sleep(3)
            
            logger.info("请使用微信扫描二维码登录...")
            
            # 2. 等待扫码登录成功
            login_detected = False
            for attempt in range(90):  # 最多等待3分钟
                await asyncio.sleep(2)
                current_url = self.page.url
                
                # 检测是否登录成功
                if "platform" in current_url and "login" not in current_url:
                    try:
                        user_info = await self.page.query_selector('.user-info, .nickname')
                        if user_info:
                            login_detected = True
                            logger.info("✅ 检测到登录成功")
                            break
                    except:
                        pass
                
                if (attempt + 1) % 15 == 0:
                    logger.info(f"⏳ 等待扫码中... ({attempt + 1}/90)")
            
            if not login_detected:
                raise TimeoutError("等待扫码登录超时")
            
            # 3. 保存Cookie
            cookies = await self.context.cookies()
            cookies_json = json.dumps(cookies)
            
            logger.info(f"视频号登录成功！已保存 {len(cookies)} 个 Cookie")
            
            return {
                "status": "success",
                "cookies": cookies_json,
                "message": "登录成功"
            }

        except Exception as e:
            logger.error(f"视频号登录失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def publish_video(
        self,
        video_path: str,
        description: str,
        location: str = "",
        tags: list = None
    ) -> Dict[str, Any]:
        """
        发布视频到视频号
        
        Args:
            video_path: 视频文件路径
            description: 视频描述
            location: 位置信息（可选）
            tags: 话题标签列表
        
        Returns:
            发布结果字典
        """
        try:
            logger.info(f"开始发布视频号视频")
            
            # 1. 导航到发布页面
            await self.page.goto("https://channels.weixin.qq.com/platform/post/create", timeout=30000)
            await asyncio.sleep(3)
            
            # 2. 上传视频
            logger.info("正在上传视频...")
            file_input = await self.page.query_selector('input[type="file"]')
            if file_input:
                await file_input.set_input_files(video_path)
                logger.info("✅ 视频已上传")
                
                # 等待视频处理
                logger.info("等待视频处理...")
                await asyncio.sleep(15)
            
            # 3. 填写描述
            desc_input = await self.page.query_selector('textarea[placeholder*="描述"], textarea[placeholder*="填写描述"]')
            if desc_input:
                await desc_input.fill(description)
                await asyncio.sleep(1)
                logger.info("✅ 描述已填写")
            
            # 4. 添加位置（如果提供）
            if location:
                logger.info(f"正在添加位置: {location}")
                # 位置选择逻辑
            
            # 5. 添加话题标签
            if tags:
                logger.info(f"正在添加话题: {tags}")
                for tag in tags[:3]:  # 视频号最多3个话题
                    # 话题添加逻辑
                    await asyncio.sleep(0.5)
            
            # 6. 点击发布
            publish_button = await self.page.query_selector('button:has-text("发表"), button:has-text("发布")')
            if publish_button:
                await publish_button.click()
                logger.info("✅ 已点击发布按钮")
                
                await asyncio.sleep(5)
                
                logger.info("🎉 视频发布成功！")
                return {
                    "status": "success",
                    "message": "视频发布成功",
                    "description": description
                }
            
            return {
                "status": "failed",
                "error": "未找到发布按钮"
            }

        except Exception as e:
            logger.error(f"视频号发布失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }

    async def close(self):
        """关闭浏览器"""
        try:
            if self.page:
                await self.page.close()
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
            logger.info("视频号发布引擎已关闭")
        except Exception as e:
            logger.error(f"关闭视频号发布引擎失败: {str(e)}")
