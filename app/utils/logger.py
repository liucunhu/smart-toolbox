from loguru import logger
import sys

# 配置 Loguru 日志输出
logger.remove()  # 移除默认的 handler
logger.add(
    sys.stderr,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
    level="INFO"
)
logger.add(
    "logs/smart_toolbox_{time}.log",
    rotation="500 MB",
    retention="10 days",
    level="DEBUG"
)

__all__ = ["logger"]
