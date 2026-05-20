from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "smart_toolbox",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.account_tasks", "app.tasks.content_tasks", "app.tasks.fanqie_tasks", "app.tasks.toutiao_tasks"]
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

# 定时任务调度配置
celery_app.conf.beat_schedule = {
    "check-toutiao-health-every-hour": {
        "task": "app.tasks.toutiao_tasks.check_account_health_task",
        "schedule": 3600.0,  # 每小时检查一次
    },
    "update-toutiao-income-daily": {
        "task": "app.tasks.toutiao_tasks.update_income_stats_task",
        "schedule": 86400.0,  # 每天更新一次收益
    },
    "monitor-hot-topics-every-2-hours": {
        "task": "app.tasks.toutiao_tasks.hot_topic_monitor_task",
        "schedule": 7200.0,  # 每2小时监控一次热点
    },
}
