"""
拟人化操作工具类
用于模拟真实人类行为，规避自动化检测
"""
import asyncio
import random
from playwright.async_api import Page, Locator
from app.utils.logger import logger

class HumanSimulator:
    """人类行为模拟器"""

    @staticmethod
    async def random_sleep(min_seconds: float = 1.0, max_seconds: float = 3.0):
        """随机休眠，模拟思考或阅读时间"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.debug(f"模拟人类休眠: {delay:.2f}秒")
        await asyncio.sleep(delay)

    @staticmethod
    async def human_type(locator: Locator, text: str):
        """
        模拟人类打字：逐字输入并带有随机间隔
        :param locator: Playwright 定位器
        :param text: 输入内容
        """
        await locator.click()
        for char in text:
            await locator.press_sequentially(char)
            # 每次按键间隔 50ms - 200ms
            await asyncio.sleep(random.uniform(0.05, 0.2))

    @staticmethod
    async def smooth_scroll(page: Page, distance: int = 500):
        """平滑滚动页面"""
        steps = 10
        step_distance = distance // steps
        for _ in range(steps):
            await page.mouse.wheel(0, step_distance)
            await asyncio.sleep(random.uniform(0.1, 0.3))

    @staticmethod
    async def random_click(page: Page, locator: Locator):
        """
        随机位置点击：在元素范围内随机选择一个坐标点击，模拟非精准点击
        """
        box = await locator.bounding_box()
        if box:
            x = box['x'] + random.uniform(5, box['width'] - 5)
            y = box['y'] + random.uniform(5, box['height'] - 5)
            await page.mouse.click(x, y)
            await HumanSimulator.random_sleep(0.5, 1.5)
        else:
            await locator.click()
