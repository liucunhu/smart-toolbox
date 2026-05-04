"""
智能调度分发服务
遵循 ISP (Interface Segregation Principle) 和 DIP (Dependency Inversion Principle)
"""
from datetime import datetime, timedelta
import random
from app.core.constants import (
    PUBLISH_TIME_WINDOW_START,
    PUBLISH_TIME_WINDOW_END,
    MAX_DAILY_PUBLISH_PER_ACCOUNT
)
from app.utils.logger import logger

class SmartScheduler:
    """智能发布调度器"""

    @staticmethod
    def get_next_publish_time(current_time: datetime = None) -> datetime:
        """
        计算下一个最佳发布时间点（在活跃时间段内随机分布）
        :param current_time: 当前时间
        :return: 建议的发布时间
        """
        now = current_time or datetime.now()
        
        # 如果当前不在活跃窗口，则设定为下一个窗口的开始时间
        if now.hour < PUBLISH_TIME_WINDOW_START:
            target_hour = PUBLISH_TIME_WINDOW_START
        elif now.hour >= PUBLISH_TIME_WINDOW_END:
            # 推迟到明天
            now += timedelta(days=1)
            target_hour = PUBLISH_TIME_WINDOW_START
        else:
            target_hour = now.hour

        # 在目标小时内随机选择一个分钟数，模拟人类行为
        random_minute = random.randint(0, 59)
        random_second = random.randint(0, 59)
        
        publish_time = now.replace(hour=target_hour, minute=random_minute, second=random_second)
        
        # 确保时间在未来
        if publish_time <= now:
            publish_time += timedelta(hours=1)
            
        logger.info(f"计算得到建议发布时间: {publish_time}")
        return publish_time

    @staticmethod
    def is_account_available(daily_count: int) -> bool:
        """
        检查账号是否达到每日发布上限
        :param daily_count: 今日已发布数量
        :return: 是否可用
        """
        return daily_count < MAX_DAILY_PUBLISH_PER_ACCOUNT
