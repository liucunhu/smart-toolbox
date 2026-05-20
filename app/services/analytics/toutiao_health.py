"""
今日头条账号健康度评估服务
"""
from datetime import datetime, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models import Account, Article, PlatformEnum
from app.utils.logger import logger


class ToutiaoHealthService:
    """头条账号健康度评估服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_health_score(self, account_id: int) -> Dict[str, Any]:
        """
        计算账号健康度评分
        
        :param account_id: 账号ID
        :return: 健康度评分详情
        """
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"账号 {account_id} 不存在")
        
        # 获取最近7天的文章数据
        seven_days_ago = datetime.now() - timedelta(days=7)
        
        recent_articles = self.db.query(Article).filter(
            Article.account_id == account_id,
            Article.published_time >= seven_days_ago,
            Article.status == "published"
        ).all()
        
        # 1. 活跃度评分（25%）
        activity_score = self._calculate_activity_score(recent_articles, seven_days_ago)
        
        # 2. 内容质量评分（30%）
        quality_score = self._calculate_quality_score(recent_articles)
        
        # 3. 用户粘性评分（20%）
        engagement_score = self._calculate_engagement_score(recent_articles)
        
        # 4. 合规安全评分（25%）
        compliance_score = self._calculate_compliance_score(account)
        
        # 综合评分
        overall_score = (
            activity_score * 0.25 +
            quality_score * 0.30 +
            engagement_score * 0.20 +
            compliance_score * 0.25
        )
        
        # 确定风险等级
        risk_level = self._determine_risk_level(overall_score, recent_articles)
        
        return {
            "account_id": account_id,
            "overall_score": round(overall_score, 2),
            "activity_score": round(activity_score, 2),
            "quality_score": round(quality_score, 2),
            "engagement_score": round(engagement_score, 2),
            "compliance_score": round(compliance_score, 2),
            "risk_level": risk_level,
            "articles_count": len(recent_articles),
            "recommendations": self._generate_recommendations(
                activity_score, quality_score, engagement_score, compliance_score
            )
        }
    
    def _calculate_activity_score(self, articles: List[Article], since: datetime) -> float:
        """计算活跃度评分"""
        if not articles:
            return 0.0
        
        # 发文频率（理想：每天1-3篇）
        days_span = max((datetime.now() - since).days, 1)
        daily_avg = len(articles) / days_span
        
        if 1 <= daily_avg <= 3:
            frequency_score = 100
        elif 0.5 <= daily_avg < 1:
            frequency_score = 80
        elif 3 < daily_avg <= 5:
            frequency_score = 70
        else:
            frequency_score = max(0, 100 - abs(daily_avg - 2) * 30)
        
        # 连续性（是否断更）
        if articles:
            last_article = max(articles, key=lambda a: a.published_time)
            days_since_last = (datetime.now() - last_article.published_time).days
            
            if days_since_last == 0:
                continuity_score = 100
            elif days_since_last <= 1:
                continuity_score = 90
            elif days_since_last <= 3:
                continuity_score = 70
            else:
                continuity_score = max(0, 100 - days_since_last * 20)
        else:
            continuity_score = 0
        
        return (frequency_score + continuity_score) / 2
    
    def _calculate_quality_score(self, articles: List[Article]) -> float:
        """计算内容质量评分"""
        if not articles:
            return 50.0  # 默认中等分数
        
        # 平均阅读量
        avg_views = sum(a.views or 0 for a in articles) / len(articles)
        
        # 阅读质量分（基于阅读量分布）
        if avg_views > 10000:
            views_score = 100
        elif avg_views > 5000:
            views_score = 90
        elif avg_views > 1000:
            views_score = 80
        elif avg_views > 500:
            views_score = 70
        else:
            views_score = max(30, avg_views / 500 * 70)
        
        # 完成率（如果有数据）
        completion_rates = [a.completion_rate for a in articles if a.completion_rate]
        if completion_rates:
            avg_completion = sum(completion_rates) / len(completion_rates)
            completion_score = min(100, avg_completion * 100)
        else:
            completion_score = 70  # 无数据时给中等分数
        
        return views_score * 0.6 + completion_score * 0.4
    
    def _calculate_engagement_score(self, articles: List[Article]) -> float:
        """计算用户粘性评分"""
        if not articles:
            return 50.0
        
        total_likes = sum(a.likes or 0 for a in articles)
        total_comments = sum(a.comments or 0 for a in articles)
        total_views = sum(a.views or 0 for a in articles)
        
        if total_views == 0:
            return 30.0
        
        # 互动率
        interaction_rate = (total_likes + total_comments) / total_views
        
        # 互动率评分
        if interaction_rate > 0.05:  # >5%
            interaction_score = 100
        elif interaction_rate > 0.02:  # >2%
            interaction_score = 85
        elif interaction_rate > 0.01:  # >1%
            interaction_score = 70
        else:
            interaction_score = max(30, interaction_rate * 1000)
        
        return interaction_score
    
    def _calculate_compliance_score(self, account: Account) -> float:
        """计算合规安全评分"""
        score = 100.0
        
        # 检查是否有违规记录（这里简化处理，实际应从违规记录表查询）
        # TODO: 集成违规记录查询
        
        return score
    
    def _determine_risk_level(self, score: float, articles: List[Article]) -> str:
        """确定风险等级"""
        if score >= 80:
            return "low"
        elif score >= 60:
            return "medium"
        elif score >= 40:
            return "high"
        else:
            return "critical"
    
    def _generate_recommendations(
        self,
        activity: float,
        quality: float,
        engagement: float,
        compliance: float
    ) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if activity < 70:
            recommendations.append("建议提高发文频率，保持每日1-3篇的稳定更新")
        
        if quality < 70:
            recommendations.append("建议优化内容质量，提升标题吸引力和内容深度")
        
        if engagement < 70:
            recommendations.append("建议增加互动引导，如提问、投票等方式提升用户参与度")
        
        if compliance < 80:
            recommendations.append("注意遵守平台规范，避免敏感内容和违规行为")
        
        if not recommendations:
            recommendations.append("账号状态良好，继续保持当前运营策略")
        
        return recommendations
