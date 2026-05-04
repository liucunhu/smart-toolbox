"""
账号健康监控服务
遵循 SRP (Single Responsibility Principle) 和 OCP (Open/Closed Principle)
"""
from sqlalchemy.orm import Session
from app.models import Account, AccountStatusEnum
from app.core.constants import (
    HEALTH_SCORE_THRESHOLD_ACTIVE,
    HEALTH_SCORE_THRESHOLD_NURTURING
)
from app.utils.logger import logger
from typing import Dict

class AccountHealthService:
    """账号健康度管理服务"""

    def __init__(self, db_session: Session):
        self.db = db_session

    def update_health_score(self, account_id: int, metrics: Dict[str, float]) -> float:
        """
        根据最新数据指标更新账号健康分
        :param account_id: 账号ID
        :param metrics: 包含播放量、互动率等指标的字典
        :return: 更新后的健康分
        """
        account = self.db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise ValueError(f"Account with id {account_id} not found")

        # 简单的加权评分算法（可根据业务需求扩展）
        view_score = min(metrics.get("views", 0) / 1000, 40)
        interaction_score = metrics.get("interaction_rate", 0) * 100 * 0.6
        new_score = max(0, min(100, view_score + interaction_score))

        old_status = account.status
        account.health_score = new_score
        
        # 自动状态流转逻辑
        if new_score >= HEALTH_SCORE_THRESHOLD_ACTIVE:
            account.status = AccountStatusEnum.ACTIVE
        elif new_score >= HEALTH_SCORE_THRESHOLD_NURTURING:
            account.status = AccountStatusEnum.NURTURING
        else:
            account.status = AccountStatusEnum.BANNED

        self.db.commit()
        
        if old_status != account.status:
            logger.warning(f"账号 {account_id} 状态变更: {old_status} -> {account.status}")
            
        return new_score

    def get_healthy_accounts(self, platform: str = None) -> list:
        """获取所有处于活跃或养号状态的账号"""
        query = self.db.query(Account).filter(
            Account.status.in_([AccountStatusEnum.ACTIVE, AccountStatusEnum.NURTURING])
        )
        if platform:
            query = query.filter(Account.platform == platform)
        return query.all()
