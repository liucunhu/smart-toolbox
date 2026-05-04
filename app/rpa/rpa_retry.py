"""
RPA 重试机制工具
使用 tenacity 库实现稳定的元素定位和操作重试
"""
import asyncio
from typing import Optional
from playwright.async_api import Page, Locator
from tenacity import (
    retry,
    stop_after_attempt,
    wait_fixed,
    retry_if_exception_type,
    before_sleep_log
)
from app.utils.logger import logger


class RPARetryHelper:
    """RPA 重试助手"""

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=True
    )
    async def find_element_with_retry(page: Page, selector: str, timeout: int = 5000) -> Locator:
        """
        带重试机制的元素查找
        :param page: Playwright页面对象
        :param selector: CSS选择器
        :param timeout: 超时时间（毫秒）
        :return: 元素定位器
        """
        logger.debug(f"尝试查找元素: {selector}")
        element = await page.wait_for_selector(selector, timeout=timeout)
        if not element:
            raise Exception(f"未找到元素: {selector}")
        return element

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=True
    )
    async def click_with_retry(page: Page, selector: str, timeout: int = 5000):
        """
        带重试机制的点击操作
        :param page: Playwright页面对象
        :param selector: CSS选择器
        :param timeout: 超时时间（毫秒）
        """
        logger.debug(f"尝试点击元素: {selector}")
        element = await page.wait_for_selector(selector, timeout=timeout)
        if element:
            await element.click()
        else:
            raise Exception(f"无法点击元素: {selector}")

    @staticmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(2),
        retry=retry_if_exception_type(Exception),
        before_sleep=before_sleep_log(logger, "WARNING"),
        reraise=True
    )
    async def fill_with_retry(page: Page, selector: str, value: str, timeout: int = 5000):
        """
        带重试机制的填充操作
        :param page: Playwright页面对象
        :param selector: CSS选择器
        :param value: 填充值
        :param timeout: 超时时间（毫秒）
        """
        logger.debug(f"尝试填充元素: {selector}")
        element = await page.wait_for_selector(selector, timeout=timeout)
        if element:
            await element.fill(value)
        else:
            raise Exception(f"无法填充元素: {selector}")

    @staticmethod
    async def safe_get_text(locator: Locator, default: str = "") -> str:
        """
        安全获取元素文本
        :param locator: 元素定位器
        :param default: 默认值
        :return: 元素文本
        """
        try:
            text = await locator.text_content()
            return text or default
        except Exception as e:
            logger.warning(f"获取元素文本失败: {str(e)}")
            return default

    @staticmethod
    async def is_element_visible(page: Page, selector: str) -> bool:
        """
        检查元素是否可见
        :param page: Playwright页面对象
        :param selector: CSS选择器
        :return: 是否可见
        """
        try:
            element = await page.query_selector(selector)
            if element:
                return await element.is_visible()
            return False
        except Exception as e:
            logger.warning(f"检查元素可见性失败: {str(e)}")
            return False
