from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "smart_toolbox",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.account_tasks", "app.tasks.content_tasks"]
)

# Celery 配置优化
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 单个任务最大运行时间 1 小时
)
