"""
多平台分发策略引擎
遵循 Strategy Pattern 和 LSP (Liskov Substitution Principle)
"""
from abc import ABC, abstractmethod
from app.core.constants import PLATFORM_LIMITS
from app.utils.logger import logger
from typing import Dict

class BasePublishStrategy(ABC):
    """发布策略基类"""
    
    @abstractmethod
    def prepare_payload(self, content: str, media_path: str, account_id: int) -> Dict:
        """准备发布所需的数据负载"""
        pass

    @abstractmethod
    def validate_content(self, content: str) -> bool:
        """验证内容是否符合平台规范"""
        pass

class DouyinStrategy(BasePublishStrategy):
    """抖音发布策略"""
    
    def prepare_payload(self, content: str, media_path: str, account_id: int) -> Dict:
        logger.info("正在为抖音平台准备发布负载...")
        # 抖音通常需要标题和话题
        return {
            "title": content[:50], 
            "video_path": media_path,
            "privacy_level": 0  # 0: 公开, 1: 好友可见, 2: 私密
        }

    def validate_content(self, content: str) -> bool:
        limits = PLATFORM_LIMITS["douyin"]
        if len(content) > 300:
            logger.warning("抖音文案超出长度限制")
            return False
        return True

class XiaohongshuStrategy(BasePublishStrategy):
    """小红书发布策略"""
    
    def prepare_payload(self, content: str, media_path: str, account_id: int) -> Dict:
        logger.info("正在为小红书平台准备发布负载...")
        return {
            "note_body": content,
            "image_paths": [media_path] if media_path.endswith(('.jpg', '.png')) else [],
            "video_path": media_path if media_path.endswith('.mp4') else None
        }

    def validate_content(self, content: str) -> bool:
        # 小红书对广告法词汇非常敏感，此处可集成更复杂的检查
        return len(content) > 10

class StrategyFactory:
    """策略工厂，遵循 DIP (Dependency Inversion Principle)"""
    
    _strategies = {
        "douyin": DouyinStrategy(),
        "xiaohongshu": XiaohongshuStrategy(),
        # "bilibili": BilibiliStrategy()
    }

    @classmethod
    def get_strategy(cls, platform: str) -> BasePublishStrategy:
        strategy = cls._strategies.get(platform.lower())
        if not strategy:
            raise ValueError(f"Unsupported platform: {platform}")
        return strategy
