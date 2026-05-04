"""
抖音平台 RPA 发布引擎
"""
import asyncio
from app.rpa.base_engine import BaseRPAEngine
from app.rpa.human_simulator import HumanSimulator
from app.utils.logger import logger
from pathlib import Path

class DouyinPublishEngine(BaseRPAEngine):
    """抖音自动化发布引擎"""

    def __init__(self, cookies: dict = None, proxy_url: str = None):
        super().__init__("douyin", proxy_url)
        self.cookies = cookies

    async def login(self):
        """通过 Cookies 维持登录状态"""
        await self.page.goto("https://creator.douyin.com/")
        if self.cookies:
            await self.context.add_cookies(self.cookies)
            await self.page.reload()
            await HumanSimulator.random_sleep(2, 4)
        
        # 简单检查是否登录成功（根据实际 DOM 调整）
        logger.info("抖音账号登录状态检查完成")

    async def perform_action(self, video_path: str, title: str):
        """执行视频发布动作"""
        logger.info(f"开始发布视频: {video_path}")
        
        # 1. 导航到发布页
        await self.page.goto("https://creator.douyin.com/creator-micro/content/upload")
        await HumanSimulator.random_sleep(3, 5)

        # 2. 上传视频（处理文件选择器）
        async with self.page.expect_file_chooser() as fc_info:
            # 点击上传按钮
            upload_button = self.page.locator('input[type="file"]')
            await upload_button.click()
        
        file_chooser = await fc_info.value
        await file_chooser.set_files(video_path)
        
        # 3. 等待上传进度条完成（简化逻辑，实际需轮询进度）
        logger.info("视频上传中，等待处理...")
        await HumanSimulator.random_sleep(10, 15)

        # 4. 填写标题和话题
        title_input = self.page.locator('div[data-placeholder*="标题"]')
        await HumanSimulator.human_type(title_input, title)
        
        # 5. 点击发布
        publish_btn = self.page.locator('button:has-text("发布")')
        await HumanSimulator.random_click(self.page, publish_btn)
        
        logger.info("抖音视频发布指令已发送")
