"""
智能主题推荐服务
结合热搜趋势和历史数据分析，推荐最有可能火的主题
"""
import random
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from app.utils.logger import logger


class TopicRecommendationService:
    """智能主题推荐服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_trending_topics(self, platform: str = "toutiao", count: int = 5) -> List[Dict]:
        """
        获取当前热门话题
        
        Args:
            platform: 平台名称
            count: 返回数量
        
        Returns:
            热门话题列表
        """
        try:
            from app.services.content.hot_trend_injector import HotTrendInjector
            
            injector = HotTrendInjector()
            hot_topics = injector.fetch_hot_topics(platform, count * 2)  # 获取更多用于筛选
            
            if not hot_topics:
                logger.warning("⚠️  未能获取热搜数据，使用备选方案")
                return self._get_fallback_topics(count)
            
            # 转换为推荐格式
            recommendations = []
            for topic in hot_topics[:count]:
                keyword = topic.get("keyword", "")
                rank = topic.get("rank", 0)
                heat = topic.get("heat", 0)
                
                if keyword and len(keyword) > 0:
                    recommendations.append({
                        "topic": keyword,
                        "source": "hot_trend",
                        "rank": rank,
                        "heat_score": heat,
                        "reason": f"当前热搜第{rank}名，热度 {heat:,}",
                        "confidence": self._calculate_confidence(rank, heat)
                    })
            
            logger.info(f"✅ 获取到 {len(recommendations)} 个热门话题")
            return recommendations[:count]
            
        except Exception as e:
            logger.error(f"❌ 获取热门话题失败: {e}")
            return self._get_fallback_topics(count)
    
    def get_personalized_recommendations(
        self, 
        account_id: int, 
        count: int = 5
    ) -> List[Dict]:
        """
        获取个性化推荐（结合历史表现和热点）
        
        Args:
            account_id: 账号ID
            count: 返回数量
        
        Returns:
            个性化推荐列表
        """
        try:
            # 1. 获取热门话题
            trending = self.get_trending_topics("toutiao", count * 2)
            
            # 2. 分析账号历史数据（如果有）
            from app.models import Account, PublishRecord, ContentTask
            
            account = self.db.query(Account).filter(Account.id == account_id).first()
            if not account:
                logger.warning(f"⚠️  账号 {account_id} 不存在")
                return trending[:count]
            
            # 获取该账号的历史文章主题
            publish_records = (
                self.db.query(PublishRecord, ContentTask)
                .join(ContentTask, PublishRecord.content_task_id == ContentTask.id)
                .filter(PublishRecord.account_id == account_id)
                .order_by(PublishRecord.publish_time.desc())
                .limit(20)
                .all()
            )
            
            if not publish_records:
                logger.info("ℹ️  暂无历史数据，返回通用热门话题")
                return trending[:count]
            
            # 3. 分析历史表现最好的主题类型
            best_performing_keywords = []
            for record, content_task in publish_records:
                if content_task and content_task.article_title:
                    title = content_task.article_title
                    # 简单提取关键词（可以优化为NLP分析）
                    if len(title) > 10:  # 只考虑较长的标题
                        best_performing_keywords.append(title[:20])
            
            # 4. 结合热点和历史偏好生成推荐
            recommendations = []
            
            # 4.1 直接推荐热门话题
            for trend in trending[:count // 2]:
                recommendations.append(trend)
            
            # 4.2 基于历史表现的扩展推荐
            if best_performing_keywords:
                from app.services.content.web_search import get_web_search_service
                import asyncio
                
                search_service = get_web_search_service()
                
                # 选择一个历史表现好的关键词进行扩展搜索
                base_keyword = random.choice(best_performing_keywords[:3])
                logger.info(f"🔍 基于历史表现扩展搜索: {base_keyword}")
                
                try:
                    # 异步搜索相关话题
                    loop = asyncio.new_event_loop()
                    related_topics = loop.run_until_complete(
                        search_service.search_materials(f"{base_keyword} 最新", num_results=3)
                    )
                    loop.close()
                    
                    if related_topics:
                        for result in related_topics:
                            title = result.get("title", "")
                            if title and len(title) > 5:
                                recommendations.append({
                                    "topic": title[:30],
                                    "source": "historical_expansion",
                                    "rank": 0,
                                    "heat_score": 0,
                                    "reason": f"基于您历史表现优秀的主题扩展",
                                    "confidence": 0.7
                                })
                except Exception as e:
                    logger.warning(f"⚠️  扩展搜索失败: {e}")
            
            # 5. 按置信度排序
            recommendations.sort(key=lambda x: x.get("confidence", 0), reverse=True)
            
            logger.info(f"✅ 生成 {len(recommendations)} 个个性化推荐")
            return recommendations[:count]
            
        except Exception as e:
            logger.error(f"❌ 生成个性化推荐失败: {e}")
            return self.get_trending_topics("toutiao", count)
    
    def _calculate_confidence(self, rank: int, heat: int) -> float:
        """
        计算推荐置信度
        
        Args:
            rank: 热搜排名
            heat: 热度值
        
        Returns:
            置信度 (0-1)
        """
        # 排名权重（前10名置信度高）
        rank_score = max(0, 1 - (rank - 1) / 20)
        
        # 热度权重（归一化到0-1）
        heat_score = min(1, heat / 10000000) if heat > 0 else 0.5
        
        # 综合评分
        confidence = rank_score * 0.6 + heat_score * 0.4
        
        return round(confidence, 2)
    
    def _get_fallback_topics(self, count: int) -> List[Dict]:
        """
        获取备选话题（当无法获取实时热点时）
        
        Args:
            count: 返回数量
        
        Returns:
            备选话题列表
        """
        fallback_topics = [
            {
                "topic": "AI技术在2026年的最新应用",
                "source": "fallback",
                "rank": 0,
                "heat_score": 0,
                "reason": "持续热门的科技话题",
                "confidence": 0.8
            },
            {
                "topic": "自媒体运营实战技巧分享",
                "source": "fallback",
                "rank": 0,
                "heat_score": 0,
                "reason": "实用性强，受众广泛",
                "confidence": 0.75
            },
            {
                "topic": "职场晋升的关键能力培养",
                "source": "fallback",
                "rank": 0,
                "heat_score": 0,
                "reason": "职场人群刚需话题",
                "confidence": 0.7
            },
            {
                "topic": "健康生活方式的科学指南",
                "source": "fallback",
                "rank": 0,
                "heat_score": 0,
                "reason": "健康生活永恒话题",
                "confidence": 0.7
            },
            {
                "topic": "投资理财的实用策略分析",
                "source": "fallback",
                "rank": 0,
                "heat_score": 0,
                "reason": "财经类高关注度话题",
                "confidence": 0.65
            }
        ]
        
        return fallback_topics[:count]
    
    def format_recommendations_for_display(
        self, 
        recommendations: List[Dict]
    ) -> str:
        """
        格式化推荐结果为展示文本
        
        Args:
            recommendations: 推荐列表
        
        Returns:
            格式化后的文本
        """
        if not recommendations:
            return "暂无推荐话题"
        
        formatted = "🔥 今日推荐创作主题\n\n"
        
        for i, rec in enumerate(recommendations, 1):
            topic = rec.get("topic", "")
            reason = rec.get("reason", "")
            confidence = rec.get("confidence", 0)
            source = rec.get("source", "")
            
            # 置信度图标
            if confidence >= 0.8:
                conf_icon = "🟢"
            elif confidence >= 0.6:
                conf_icon = "🟡"
            else:
                conf_icon = "🔴"
            
            formatted += f"{i}. {topic}\n"
            formatted += f"   {conf_icon} 推荐理由: {reason}\n"
            formatted += f"   置信度: {confidence:.0%}\n\n"
        
        formatted += "💡 提示: 点击任一主题可快速开始创作"
        
        return formatted


def get_topic_recommendation_service(db: Session) -> TopicRecommendationService:
    """获取主题推荐服务实例"""
    return TopicRecommendationService(db)
