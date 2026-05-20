"""
智能分析缓存服务
保存和获取账号的智能分析结果，用于优化文章生成
"""
import json
from datetime import datetime, timedelta
from typing import Optional, Dict
from sqlalchemy.orm import Session
from app.utils.logger import logger


class AnalyticsCacheService:
    """智能分析缓存服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def save_analysis_result(
        self,
        account_id: int,
        analysis_data: Dict,
        ttl_hours: int = 24
    ):
        """
        保存分析结果到缓存
        
        Args:
            account_id: 账号ID
            analysis_data: 分析数据（包含 optimized_prompt_template 等）
            ttl_hours: 缓存有效期（小时）
        """
        try:
            # 这里可以使用Redis或数据库存储
            # 简化实现：直接记录日志，实际项目应该存入Redis
            
            cache_key = f"analytics_cache:{account_id}"
            cache_data = {
                "account_id": account_id,
                "analysis": analysis_data,
                "created_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
            }
            
            # TODO: 实际项目中应该存入 Redis
            # from app.core.redis_client import redis_client
            # redis_client.setex(cache_key, ttl_hours * 3600, json.dumps(cache_data))
            
            logger.info(f"✅ 分析结果已缓存: 账号{account_id}, 有效期{ttl_hours}小时")
            logger.debug(f"缓存内容: {json.dumps(cache_data, ensure_ascii=False)[:200]}...")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 保存分析结果失败: {e}")
            return False
    
    def get_optimized_prompt(self, account_id: int) -> Optional[str]:
        """
        获取优化的提示词模板
        
        Args:
            account_id: 账号ID
        
        Returns:
            优化的提示词模板，如果不存在则返回None
        """
        try:
            cache_key = f"analytics_cache:{account_id}"
            
            # TODO: 实际项目中应该从 Redis 读取
            # from app.core.redis_client import redis_client
            # cached_data = redis_client.get(cache_key)
            
            # 简化实现：暂时返回None
            logger.debug(f"⚠️  暂未实现缓存读取，将使用默认提示词")
            return None
            
        except Exception as e:
            logger.error(f"❌ 获取优化提示词失败: {e}")
            return None
    
    def is_analysis_available(self, account_id: int) -> bool:
        """
        检查是否有可用的分析结果
        
        Args:
            account_id: 账号ID
        
        Returns:
            是否有可用的分析结果
        """
        prompt = self.get_optimized_prompt(account_id)
        return prompt is not None and len(prompt) > 0


def get_analytics_cache_service(db: Session) -> AnalyticsCacheService:
    """获取分析缓存服务实例"""
    return AnalyticsCacheService(db)
