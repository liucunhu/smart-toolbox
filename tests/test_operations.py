import pytest
from datetime import datetime
from app.services.operations.smart_scheduler import SmartScheduler
from app.core.constants import PUBLISH_TIME_WINDOW_START, PUBLISH_TIME_WINDOW_END

class TestSmartScheduler:
    """智能调度器测试"""

    def test_publish_time_within_window(self):
        """测试在活跃窗口内生成时间"""
        # 设定当前时间为上午 10 点
        current = datetime(2026, 4, 29, 10, 0, 0)
        result = SmartScheduler.get_next_publish_time(current)
        
        assert result >= current
        assert PUBLISH_TIME_WINDOW_START <= result.hour < PUBLISH_TIME_WINDOW_END

    def test_publish_time_before_window(self):
        """测试在非活跃窗口（凌晨）生成时间"""
        current = datetime(2026, 4, 29, 3, 0, 0)
        result = SmartScheduler.get_next_publish_time(current)
        
        # 应该跳转到当天的 8 点以后
        assert result.day == current.day
        assert result.hour >= PUBLISH_TIME_WINDOW_START

    def test_account_availability(self):
        """测试账号发布上限检查"""
        assert SmartScheduler.is_account_available(4) is True
        assert SmartScheduler.is_account_available(5) is False
        assert SmartScheduler.is_account_available(6) is False
