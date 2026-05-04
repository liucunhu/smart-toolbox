"""
健康检查端点
提供系统各组件的健康状态检查
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db, engine
from app.core.config import settings
from app.utils.logger import logger
import redis
from celery.result import AsyncResult
from app.tasks.celery_app import celery_app

router = APIRouter()


def check_database() -> bool:
    """检查数据库连接"""
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception as e:
        logger.error(f"数据库检查失败: {str(e)}")
        return False


def check_redis() -> bool:
    """检查Redis连接"""
    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
        return True
    except Exception as e:
        logger.error(f"Redis检查失败: {str(e)}")
        return False


def check_celery() -> bool:
    """检查Celery Worker状态"""
    try:
        # 发送一个简单的ping任务
        result = celery_app.control.ping(timeout=2)
        return len(result) > 0
    except Exception as e:
        logger.error(f"Celery检查失败: {str(e)}")
        return False


@router.get("/health")
def health_check():
    """
    健康检查端点
    返回各组件的健康状态
    """
    db_status = check_database()
    redis_status = check_redis()
    celery_status = check_celery()
    
    overall_status = all([db_status, redis_status, celery_status])
    
    return {
        "status": "healthy" if overall_status else "unhealthy",
        "components": {
            "database": "healthy" if db_status else "unhealthy",
            "redis": "healthy" if redis_status else "unhealthy",
            "celery": "healthy" if celery_status else "unhealthy"
        },
        "version": settings.VERSION
    }


@router.get("/health/db")
def check_db_health():
    """单独检查数据库健康状态"""
    status = check_database()
    return {
        "component": "database",
        "status": "healthy" if status else "unhealthy"
    }


@router.get("/health/redis")
def check_redis_health():
    """单独检查Redis健康状态"""
    status = check_redis()
    return {
        "component": "redis",
        "status": "healthy" if status else "unhealthy"
    }


@router.get("/health/celery")
def check_celery_health():
    """单独检查Celery健康状态"""
    status = check_celery()
    return {
        "component": "celery",
        "status": "healthy" if status else "unhealthy"
    }
