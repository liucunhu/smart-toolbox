from app.tasks.celery_app import celery_app
from app.services.account.auto_registration import AutoRegistrationEngine
from app.db.session import SessionLocal
from app.models import Account, AccountStatusEnum
from app.utils.logger import logger

@celery_app.task(bind=True, max_retries=3)
def register_account_task(self, account_id: int, phone: str, code: str, platform: str, proxy_ip: str):
    """异步执行账号注册流程"""
    import asyncio
    from app.services.account.auto_registration import AutoRegistrationEngine
    
    db = SessionLocal()
    try:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return {"status": "error", "message": "Account not found"}

        account.status = AccountStatusEnum.REGISTERING
        db.commit()

        logger.info(f"开始异步注册账号 ID: {account_id}")
        engine = AutoRegistrationEngine(platform=platform, proxy_url=proxy_ip)
        
        # 使用 asyncio.run() 执行异步方法
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            engine.register_account(phone_number=phone, verification_code=code)
        )

        if result["status"] == "success":
            account.status = AccountStatusEnum.NURTURING
            # 此处应保存 cookies 到数据库
            db.commit()  # ✅ 提交事务
            logger.info(f"账号 ID: {account_id} 注册成功，进入养号阶段")
        else:
            raise Exception(result.get("error", "Unknown error"))

        return {"status": "success", "account_id": account_id}

    except Exception as exc:
        db.rollback()  # ✅ 异常时回滚
        logger.error(f"注册任务失败: {str(exc)}")
        # 指数退避重试：60s, 120s, 240s
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
    finally:
        db.close()
