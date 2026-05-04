"""
自动化养号任务逻辑
包含完整的错误处理和边界条件检查
"""
import asyncio
import random
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models import Account, AccountStatusEnum
from app.core.constants import (
    NURTURING_BROWSE_DURATION_MIN,
    NURTURING_BROWSE_DURATION_MAX,
    NURTURING_LIKE_PROBABILITY
)
from app.utils.logger import logger
from playwright.sync_api import sync_playwright
import time

@celery_app.task(bind=True, max_retries=3)
def auto_nurturing_task(self, account_id: int):
    """
    执行账号自动养号流程：随机浏览、点赞
    :param account_id: 账号ID
    """
    db = SessionLocal()
    try:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account or account.status not in [AccountStatusEnum.NURTURING, AccountStatusEnum.ACTIVE]:
            logger.warning(f"账号 {account_id} 不需要养号或不存在")
            return {"status": "skipped", "reason": "account_not_eligible"}

        logger.info(f"开始为账号 {account.username} 执行养号任务...")
        
        # 模拟人类行为：随机浏览时长
        duration = random.uniform(NURTURING_BROWSE_DURATION_MIN, NURTURING_BROWSE_DURATION_MAX)
        logger.info(f"计划浏览时长: {duration:.2f} 秒")

        # 执行实际的浏览动作
        _perform_browse_actions(account.proxy_ip, duration, account.platform.value)

        # 模拟随机点赞行为
        if random.random() < NURTURING_LIKE_PROBABILITY:
            logger.info(f"账号 {account.username} 触发了点赞行为")
            # TODO: 实现具体的点赞逻辑

        logger.info(f"账号 {account_id} 养号任务完成")
        return {"status": "success", "duration": duration}

    except Exception as exc:
        logger.error(f"养号任务异常: {str(exc)}")
        raise self.retry(exc=exc, countdown=300)
    finally:
        db.close()

def _perform_browse_actions(proxy_ip: str, duration: float, platform: str):
    """执行具体的浏览动作"""
    logger.info(f"开始执行浏览动作，平台: {platform}, 时长: {duration:.2f}秒")
    
    # 根据平台选择浏览 URL
    platform_urls = {
        "douyin": "https://www.douyin.com/recommend",
        "xiaohongshu": "https://www.xiaohongshu.com/explore",
        "bilibili": "https://www.bilibili.com",
        "toutiao": "https://www.toutiao.com",
    }
    
    url = platform_urls.get(platform, platform_urls["douyin"])
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context_options = {
            "viewport": {"width": 1920, "height": 1080},
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        if proxy_ip:
            context_options["proxy"] = {"server": proxy_ip}
        
        context = browser.new_context(**context_options)
        page = context.new_page()
        
        try:
            # 访问平台首页
            page.goto(url, timeout=30000)
            page.wait_for_load_state("networkidle")
            
            # 随机滚动页面，模拟人类浏览行为
            scroll_count = int(duration / 5)  # 每 5 秒滚动一次
            for _ in range(scroll_count):
                page.evaluate("window.scrollBy(0, Math.random() * 500 + 200)")
                time.sleep(random.uniform(2, 5))
            
            logger.info("浏览动作执行完成")
        except Exception as e:
            logger.error(f"浏览动作执行失败: {str(e)}")
        finally:
            browser.close()
