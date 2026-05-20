"""
配置迁移脚本 - 将.env配置文件中的配置迁移到数据库
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.config import settings
from app.db.session import SessionLocal
from app.services.system.config_service import ConfigService, LLMConfigService
from app.utils.logger import logger


def migrate_system_configs():
    """迁移系统配置到数据库"""
    db = SessionLocal()
    try:
        config_service = ConfigService(db)
        
        logger.info("开始迁移系统配置...")
        
        # 数据库配置
        config_service.set_config(
            category="database",
            key="DATABASE_URL",
            value=settings.DATABASE_URL,
            value_type="string",
            description="数据库连接URL",
            is_required=True
        )
        
        # Redis配置
        config_service.set_config(
            category="redis",
            key="REDIS_URL",
            value=settings.REDIS_URL,
            value_type="string",
            description="Redis连接URL",
            is_required=True
        )
        
        # Celery配置
        config_service.set_config(
            category="celery",
            key="CELERY_BROKER_URL",
            value=settings.CELERY_BROKER_URL,
            value_type="string",
            description="Celery消息代理URL"
        )
        
        config_service.set_config(
            category="celery",
            key="CELERY_RESULT_BACKEND",
            value=settings.CELERY_RESULT_BACKEND,
            value_type="string",
            description="Celery结果后端URL"
        )
        
        # JWT配置
        config_service.set_config(
            category="jwt",
            key="SECRET_KEY",
            value=settings.SECRET_KEY,
            value_type="string",
            description="JWT密钥",
            is_encrypted=True,
            is_required=True
        )
        
        config_service.set_config(
            category="jwt",
            key="ALGORITHM",
            value=settings.ALGORITHM,
            value_type="string",
            description="JWT算法"
        )
        
        config_service.set_config(
            category="jwt",
            key="ACCESS_TOKEN_EXPIRE_MINUTES",
            value=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
            value_type="int",
            description="访问令牌过期时间（分钟）"
        )
        
        # 养号配置
        config_service.set_config(
            category="nurturing",
            key="NURTURING_DURATION_DAYS",
            value=settings.NURTURING_DURATION_DAYS,
            value_type="int",
            description="养号持续天数"
        )
        
        config_service.set_config(
            category="nurturing",
            key="NURTURING_DAILY_BROWSE_COUNT",
            value=settings.NURTURING_DAILY_BROWSE_COUNT,
            value_type="int",
            description="每日浏览数量"
        )
        
        config_service.set_config(
            category="nurturing",
            key="NURTURING_LIKE_PROBABILITY",
            value=settings.NURTURING_LIKE_PROBABILITY,
            value_type="float",
            description="点赞概率"
        )
        
        config_service.set_config(
            category="nurturing",
            key="NURTURING_COMMENT_PROBABILITY",
            value=settings.NURTURING_COMMENT_PROBABILITY,
            value_type="float",
            description="评论概率"
        )
        
        config_service.set_config(
            category="nurturing",
            key="NURTURING_SHARE_PROBABILITY",
            value=settings.NURTURING_SHARE_PROBABILITY,
            value_type="float",
            description="分享概率"
        )
        
        config_service.set_config(
            category="nurturing",
            key="NURTURING_ACTIVE_HOURS",
            value=settings.NURTURING_ACTIVE_HOURS,
            value_type="json",
            description="活跃时间段"
        )
        
        config_service.set_config(
            category="nurturing",
            key="NURTURING_SLEEP_HOURS",
            value=settings.NURTURING_SLEEP_HOURS,
            value_type="int",
            description="睡眠小时数"
        )
        
        # Playwright配置
        config_service.set_config(
            category="playwright",
            key="PLAYWRIGHT_HEADLESS",
            value=settings.PLAYWRIGHT_HEADLESS,
            value_type="bool",
            description="Playwright无头模式"
        )
        
        # CORS配置
        config_service.set_config(
            category="cors",
            key="BACKEND_CORS_ORIGINS",
            value=settings.BACKEND_CORS_ORIGINS,
            value_type="json",
            description="CORS允许的源"
        )
        
        logger.info("✅ 系统配置迁移完成")
        
    except Exception as e:
        logger.error(f"❌ 系统配置迁移失败: {e}")
        raise
    finally:
        db.close()


def migrate_llm_configs():
    """迁移LLM配置到数据库"""
    db = SessionLocal()
    try:
        llm_service = LLMConfigService(db)
        
        logger.info("开始迁移LLM配置...")
        
        # 硅基流动 - 文案生成
        if settings.SILICONFLOW_API_KEY:
            llm_service.create_llm_config(
                provider="siliconflow",
                function_type="copywriting",
                name="硅基流动-文案生成",
                api_key=settings.SILICONFLOW_API_KEY,
                base_url=settings.SILICONFLOW_BASE_URL,
                model_name=settings.SILICONFLOW_MODEL,
                timeout=60,
                is_default=True,
                is_active=True,
                priority=10,
                description="硅基流动DeepSeek模型用于文案生成"
            )
            
            # 硅基流动 - 封面图分析
            llm_service.create_llm_config(
                provider="siliconflow",
                function_type="content_analysis",
                name="硅基流动-封面分析",
                api_key=settings.SILICONFLOW_API_KEY,
                base_url=settings.SILICONFLOW_BASE_URL,
                model_name=settings.SILICONFLOW_MODEL,
                timeout=60,
                is_default=True,
                is_active=True,
                priority=10,
                description="硅基流动模型用于封面图内容分析"
            )
            
            # 硅基流动 - 图像生成
            llm_service.create_llm_config(
                provider="siliconflow",
                function_type="image_generation",
                name="硅基流动-图像生成",
                api_key=settings.SILICONFLOW_API_KEY,
                base_url=settings.SILICONFLOW_BASE_URL,
                model_name=settings.SILICONFLOW_MODEL,
                image_model_name=settings.SILICONFLOW_IMAGE_MODEL,
                timeout=120,
                is_default=True,
                is_active=True,
                priority=10,
                description="硅基流动通义千问加速版用于图像生成"
            )
        
        # 魔搭社区 - 备用配置
        if settings.MODELSCOPE_API_KEY:
            llm_service.create_llm_config(
                provider="modelscope",
                function_type="copywriting",
                name="魔搭社区-文案生成",
                api_key=settings.MODELSCOPE_API_KEY,
                base_url=settings.MODELSCOPE_BASE_URL,
                model_name=settings.MODELSCOPE_MODEL,
                timeout=60,
                is_default=False,
                is_active=True,
                priority=5,
                description="魔搭社区Qwen模型用于文案生成（备用）"
            )
            
            llm_service.create_llm_config(
                provider="modelscope",
                function_type="image_generation",
                name="魔搭社区-图像生成",
                api_key=settings.MODELSCOPE_API_KEY,
                base_url=settings.MODELSCOPE_BASE_URL,
                model_name=settings.MODELSCOPE_MODEL,
                image_model_name=settings.MODELSCOPE_IMAGE_MODEL,
                timeout=120,
                is_default=False,
                is_active=True,
                priority=5,
                description="魔搭社区FLUX模型用于图像生成（备用）"
            )
        
        # 阿里百炼 - 图像生成
        if settings.DASHSCOPE_API_KEY:
            llm_service.create_llm_config(
                provider="dashscope",
                function_type="image_generation",
                name="阿里百炼-图像生成",
                api_key=settings.DASHSCOPE_API_KEY,
                base_url=settings.DASHSCOPE_BASE_URL,
                model_name="qwen-turbo",
                image_model_name=settings.DASHSCOPE_IMAGE_MODEL,
                timeout=120,
                is_default=False,
                is_active=True,
                priority=8,
                description="阿里百炼通义万相用于图像生成"
            )
        
        # DeepSeek - 备用配置
        if settings.DEEPSEEK_API_KEY:
            llm_service.create_llm_config(
                provider="deepseek",
                function_type="copywriting",
                name="DeepSeek-文案生成",
                api_key=settings.DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com/v1",
                model_name="deepseek-chat",
                timeout=60,
                is_default=False,
                is_active=True,
                priority=7,
                description="DeepSeek官方API用于文案生成"
            )
        
        # OpenAI - 备用配置
        if settings.OPENAI_API_KEY:
            llm_service.create_llm_config(
                provider="openai",
                function_type="copywriting",
                name="OpenAI-文案生成",
                api_key=settings.OPENAI_API_KEY,
                base_url="https://api.openai.com/v1",
                model_name="gpt-3.5-turbo",
                timeout=60,
                is_default=False,
                is_active=True,
                priority=6,
                description="OpenAI GPT-3.5用于文案生成"
            )
        
        logger.info("✅ LLM配置迁移完成")
        
    except Exception as e:
        logger.error(f"❌ LLM配置迁移失败: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    logger.info("=" * 80)
    logger.info("开始迁移配置到数据库")
    logger.info("=" * 80)
    
    try:
        # 迁移系统配置
        migrate_system_configs()
        
        # 迁移LLM配置
        migrate_llm_configs()
        
        logger.info("=" * 80)
        logger.info("✅ 所有配置迁移完成！")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"❌ 配置迁移失败: {e}")
        sys.exit(1)
