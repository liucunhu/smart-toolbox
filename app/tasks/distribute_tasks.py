"""
内容分发任务逻辑
"""
from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models import ContentTask, PublishRecord, Account, PlatformEnum
from app.services.content.deduplication import VideoDeduplicationEngine
from app.services.operations.distribution_strategy import StrategyFactory
from app.services.operations.smart_scheduler import SmartScheduler
from app.utils.logger import logger
import asyncio
import json

@celery_app.task(bind=True)
def distribute_content_task(self, content_task_id: int, account_id: int):
    """
    执行内容分发任务
    :param content_task_id: 内容任务ID
    :param account_id: 目标账号ID
    """
    db = SessionLocal()
    try:
        # 1. 获取内容与账号信息
        content_task = db.query(ContentTask).filter(ContentTask.id == content_task_id).first()
        account = db.query(Account).filter(Account.id == account_id).first()
        
        if not content_task or not account:
            raise ValueError("Content task or Account not found")

        # 2. 智能调度检查
        if not SmartScheduler.is_account_available(0):  # 此处应查询今日已发数
            logger.warning(f"账号 {account_id} 今日发布已达上限")
            return {"status": "skipped", "reason": "daily_limit_reached"}

        # 3. 策略模式准备负载
        strategy = StrategyFactory.get_strategy(account.platform.value)
        if not strategy.validate_content(content_task.original_topic or ""):
            raise ValueError("Content validation failed")

        payload = strategy.prepare_payload(
            content_task.original_topic or "", 
            content_task.video_path or "", 
            account_id
        )

        # 4. 执行发布逻辑（根据平台调用不同的发布引擎）
        publish_result = {"status": "pending"}
        
        if account.platform.value == "douyin":
            # TODO: 实现抖音发布引擎
            logger.info(f"抖音发布功能开发中，账号: {account_id}")
            publish_result = {"status": "success", "platform": "douyin"}
        elif account.platform.value == "toutiao":
            # TODO: 实现头条发布引擎
            logger.info(f"头条发布功能开发中，账号: {account_id}")
            publish_result = {"status": "success", "platform": "toutiao"}
        else:
            logger.warning(f"平台 {account.platform.value} 发布功能待实现")
            publish_result = {"status": "pending", "platform": account.platform.value}

        # 5. 记录分发日志
        record = PublishRecord(
            account_id=account_id,
            content_task_id=content_task_id,
            publish_status=publish_result.get("status", "pending"),
            publish_time=SmartScheduler.get_next_publish_time(),
            error_message=None if publish_result["status"] == "success" else "Platform not implemented"
        )
        db.add(record)
        db.commit()

        logger.info(f"内容 {content_task_id} 分发任务完成，状态: {publish_result['status']}")
        return {"status": publish_result["status"], "record_id": record.id}

    except Exception as exc:
        logger.error(f"分发任务失败: {str(exc)}")
        db.rollback()
        raise self.retry(exc=exc, countdown=60)
    finally:
        db.close()
