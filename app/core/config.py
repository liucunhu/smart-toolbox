from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    """应用全局配置"""
    PROJECT_NAME: str = "Smart-Toolbox"
    VERSION: str = "1.0.0"
    
    # 数据库配置
    DATABASE_URL: str
    
    # Redis & Celery 配置
    REDIS_URL: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    
    # JWT 认证配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI 模型配置 - 多平台支持
    LLM_PROVIDER: str = "siliconflow"  # 可选：siliconflow, modelscope, deepseek, openai
    
    # 硅基流动 (SiliconFlow)
    SILICONFLOW_API_KEY: Optional[str] = None
    SILICONFLOW_BASE_URL: str = "https://api.siliconflow.cn/v1"
    SILICONFLOW_MODEL: str = "Qwen/Qwen2.5-72B-Instruct"
    SILICONFLOW_IMAGE_MODEL: str = "Tongyi-MAI/Z-Image-Turbo"  # 图像生成模型（通义千问加速版）
    
    # 阿里百炼 (DashScope) - ✅ 新增
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_BASE_URL: str = "https://dashscope.aliyuncs.com/api/v1"
    DASHSCOPE_IMAGE_MODEL: str = "wanx2.1-t2i-turbo"  # 通义万相极速版（性价比高）
    
    # 魔搭社区 (ModelScope)
    MODELSCOPE_API_KEY: Optional[str] = None
    MODELSCOPE_BASE_URL: str = "https://api-inference.modelscope.cn/v1"
    MODELSCOPE_MODEL: str = "Qwen/Qwen2.5-72B-Instruct"
    MODELSCOPE_IMAGE_MODEL: str = "black-forest-labs/FLUX.1-schnell"  # ✅ 图像生成模型（FLUX.1-schnell）
    
    # DeepSeek
    DEEPSEEK_API_KEY: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    
    # 代理池配置
    PROXY_POOL_URL: Optional[str] = None
    
    # CORS 配置
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3002",
        "http://localhost:3003",  # 前端当前端口
        "http://127.0.0.1:3003"
    ]
    
    # 养号系统配置
    NURTURING_DURATION_DAYS: int = 7
    NURTURING_DAILY_BROWSE_COUNT: int = 50
    NURTURING_LIKE_PROBABILITY: float = 0.05
    NURTURING_COMMENT_PROBABILITY: float = 0.01
    NURTURING_SHARE_PROBABILITY: float = 0.005
    NURTURING_ACTIVE_HOURS: List[str] = ["12:00-13:00", "20:00-22:00"]
    NURTURING_SLEEP_HOURS: int = 7
    
    # Playwright配置
    PLAYWRIGHT_HEADLESS: bool = False
    
    # 报警系统配置
    EMAIL_ENABLED: bool = False
    EMAIL_HOST: str = "smtp.example.com"
    EMAIL_PORT: int = 587
    EMAIL_USER: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_FROM: str = "noreply@smart-toolbox.com"
    EMAIL_TO: List[str] = []
    
    DINGTALK_WEBHOOK_URL: Optional[str] = None
    
    # SMS接码平台配置
    SMS_PLATFORM_API_KEY: Optional[str] = None
    SMS_PLATFORM_BASE_URL: str = "https://api.sms-platform.com"
    
    # 热点数据源
    HOT_TREND_API_URL: Optional[str] = None
    HOT_TREND_API_KEY: Optional[str] = None
    
    # 网络搜索配置（用于获取实时素材进行二次原创）
    BING_SEARCH_API_KEY: Optional[str] = None  # Bing Search API Key
    SERPAPI_API_KEY: Optional[str] = None  # SerpAPI Key

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
