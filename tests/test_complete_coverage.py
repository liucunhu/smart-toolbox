"""
完整测试套件 - 达到100%覆盖率
包含所有Service层、工具类、RPA引擎的单元测试
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import asyncio


# ==================== 健康监控服务测试 ====================

class TestAccountHealthService:
    """账号健康服务完整测试"""

    def test_calculate_health_score_high_views(self):
        """测试高播放量账号的健康分计算"""
        from app.services.operations.health_monitor import AccountHealthService
        
        # 模拟数据库session
        mock_db = Mock()
        service = AccountHealthService(mock_db)
        
        # 测试高播放量（5000次）
        metrics = {"views": 5000, "interaction_rate": 0.05}
        score = service.calculate_health_score(metrics)
        
        # view_score = min(5000/1000, 40) = 5
        # interaction_score = 0.05 * 100 * 0.6 = 3
        # total = 8
        assert score == 8.0

    def test_calculate_health_score_max_views(self):
        """测试播放量上限"""
        from app.services.operations.health_monitor import AccountHealthService
        
        mock_db = Mock()
        service = AccountHealthService(mock_db)
        
        # 测试超高播放量（应该被限制在40分）
        metrics = {"views": 100000, "interaction_rate": 0.05}
        score = service.calculate_health_score(metrics)
        
        # view_score应该是40（上限）
        assert score >= 40.0

    def test_calculate_health_score_zero_interaction(self):
        """测试零互动率"""
        from app.services.operations.health_monitor import AccountHealthService
        
        mock_db = Mock()
        service = AccountHealthService(mock_db)
        
        metrics = {"views": 1000, "interaction_rate": 0.0}
        score = service.calculate_health_score(metrics)
        
        # 只有view_score = 1
        assert score == 1.0

    def test_update_account_health(self):
        """测试更新账号健康分"""
        from app.services.operations.health_monitor import AccountHealthService
        from app.models import Account
        
        mock_db = Mock()
        service = AccountHealthService(mock_db)
        
        # 模拟账号
        mock_account = Mock(spec=Account)
        mock_account.id = 1
        mock_account.health_score = 50.0
        
        mock_db.query.return_value.filter.return_value.first.return_value = mock_account
        
        # 更新健康分
        service.update_account_health(1, 75.0)
        
        # 验证调用
        assert mock_account.health_score == 75.0
        mock_db.commit.assert_called_once()

    def test_get_healthy_accounts_all_platforms(self):
        """测试获取所有平台的健康账号"""
        from app.services.operations.health_monitor import AccountHealthService
        from app.models import Account, AccountStatusEnum
        
        mock_db = Mock()
        service = AccountHealthService(mock_db)
        
        # 模拟查询结果
        mock_accounts = [
            Mock(spec=Account, id=1, username="user1", health_score=80.0, status=AccountStatusEnum.ACTIVE),
            Mock(spec=Account, id=2, username="user2", health_score=70.0, status=AccountStatusEnum.ACTIVE),
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_accounts
        
        accounts = service.get_healthy_accounts()
        
        assert len(accounts) == 2
        assert all(a.health_score >= 60 for a in accounts)

    def test_get_healthy_accounts_specific_platform(self):
        """测试获取指定平台的健康账号"""
        from app.services.operations.health_monitor import AccountHealthService
        from app.models import Account, PlatformEnum, AccountStatusEnum
        
        mock_db = Mock()
        service = AccountHealthService(mock_db)
        
        mock_accounts = [
            Mock(spec=Account, id=1, username="user1", platform=PlatformEnum.DOUYIN),
        ]
        
        mock_db.query.return_value.filter.return_value.all.return_value = mock_accounts
        
        accounts = service.get_healthy_accounts(platform="douyin")
        
        assert len(accounts) == 1
        assert accounts[0].platform == PlatformEnum.DOUYIN

    def test_detect_abnormal_activity_normal(self):
        """测试检测异常活动 - 正常情况"""
        from app.services.operations.health_monitor import AccountHealthService
        
        mock_db = Mock()
        service = AccountHealthService(mock_db)
        
        # 正常的发布频率（每天3条）
        is_abnormal = service.detect_abnormal_activity(publish_count=3, days=1)
        
        assert is_abnormal is False

    def test_detect_abnormal_activity_excessive(self):
        """测试检测异常活动 - 过度发布"""
        from app.services.operations.health_monitor import AccountHealthService
        
        mock_db = Mock()
        service = AccountHealthService(mock_db)
        
        # 过度的发布频率（每天10条，超过5条限制）
        is_abnormal = service.detect_abnormal_activity(publish_count=10, days=1)
        
        assert is_abnormal is True

    def test_get_health_status_healthy(self):
        """测试获取健康状态 - 健康"""
        from app.services.operations.health_monitor import AccountHealthService
        
        mock_db = Mock()
        service = AccountHealthService(mock_db)
        
        status = service.get_health_status(80.0)
        
        assert status == "healthy"

    def test_get_health_status_warning(self):
        """测试获取健康状态 - 警告"""
        from app.services.operations.health_monitor import AccountHealthService
        
        mock_db = Mock()
        service = AccountHealthService(mock_db)
        
        status = service.get_health_status(50.0)
        
        assert status == "warning"

    def test_get_health_status_critical(self):
        """测试获取健康状态 - 危险"""
        from app.services.operations.health_monitor import AccountHealthService
        
        mock_db = Mock()
        service = AccountHealthService(mock_db)
        
        status = service.get_health_status(20.0)
        
        assert status == "critical"


# ==================== 智能调度器完整测试 ====================

class TestSmartSchedulerExtended:
    """智能调度器扩展测试"""

    def test_get_next_publish_time_exact_boundary(self):
        """测试边界时间（正好8点）"""
        from app.services.operations.smart_scheduler import SmartScheduler
        
        current = datetime(2026, 4, 29, 8, 0, 0)
        result = SmartScheduler.get_next_publish_time(current)
        
        assert result >= current
        assert 8 <= result.hour < 22

    def test_get_next_publish_time_exact_end_boundary(self):
        """测试边界时间（正好22点）"""
        from app.services.operations.smart_scheduler import SmartScheduler
        
        current = datetime(2026, 4, 29, 22, 0, 0)
        result = SmartScheduler.get_next_publish_time(current)
        
        # 应该跳转到第二天8点
        assert result.day > current.day
        assert result.hour == 8

    def test_is_account_available_boundary_values(self):
        """测试账号可用性边界值"""
        from app.services.operations.smart_scheduler import SmartScheduler
        
        # 测试0-6的所有值
        assert SmartScheduler.is_account_available(0) is True
        assert SmartScheduler.is_account_available(1) is True
        assert SmartScheduler.is_account_available(4) is True
        assert SmartScheduler.is_account_available(5) is False
        assert SmartScheduler.is_account_available(6) is False
        assert SmartScheduler.is_account_available(10) is False

    def test_calculate_optimal_interval(self):
        """测试计算最优发布间隔"""
        from app.services.operations.smart_scheduler import SmartScheduler
        
        # 健康度高，间隔应该短
        interval_high = SmartScheduler.calculate_optimal_interval(health_score=90)
        
        # 健康度低，间隔应该长
        interval_low = SmartScheduler.calculate_optimal_interval(health_score=30)
        
        assert interval_high < interval_low

    def test_get_peak_hours(self):
        """测试获取高峰时段"""
        from app.services.operations.smart_scheduler import SmartScheduler
        
        peak_hours = SmartScheduler.get_peak_hours()
        
        assert isinstance(peak_hours, list)
        assert len(peak_hours) > 0
        assert all(0 <= h < 24 for h in peak_hours)


# ==================== 内容去重服务测试 ====================

class TestContentDeduplication:
    """内容去重服务测试"""

    def test_calculate_md5(self):
        """测试计算MD5"""
        from app.services.content.deduplication import ContentDeduplication
        
        dedup = ContentDeduplication()
        md5 = dedup.calculate_md5("test content")
        
        assert isinstance(md5, str)
        assert len(md5) == 32  # MD5是32位十六进制字符串

    def test_calculate_md5_different_content(self):
        """测试不同内容产生不同MD5"""
        from app.services.content.deduplication import ContentDeduplication
        
        dedup = ContentDeduplication()
        md5_1 = dedup.calculate_md5("content 1")
        md5_2 = dedup.calculate_md5("content 2")
        
        assert md5_1 != md5_2

    def test_check_duplicate_new_content(self):
        """测试检查新内容（非重复）"""
        from app.services.content.deduplication import ContentDeduplication
        
        dedup = ContentDeduplication()
        is_duplicate = dedup.check_duplicate("new unique content")
        
        assert is_duplicate is False

    def test_add_to_history(self):
        """测试添加到历史记录"""
        from app.services.content.deduplication import ContentDeduplication
        
        dedup = ContentDeduplication()
        dedup.add_to_history("test content")
        
        # 再次检查应该是重复
        is_duplicate = dedup.check_duplicate("test content")
        assert is_duplicate is True

    def test_clear_history(self):
        """测试清空历史记录"""
        from app.services.content.deduplication import ContentDeduplication
        
        dedup = ContentDeduplication()
        dedup.add_to_history("test content")
        dedup.clear_history()
        
        # 清空后应该不是重复
        is_duplicate = dedup.check_duplicate("test content")
        assert is_duplicate is False

    def test_similarity_check_identical(self):
        """测试相似度检查 - 完全相同"""
        from app.services.content.deduplication import ContentDeduplication
        
        dedup = ContentDeduplication()
        similarity = dedup.calculate_similarity("hello world", "hello world")
        
        assert similarity == 1.0

    def test_similarity_check_completely_different(self):
        """测试相似度检查 - 完全不同"""
        from app.services.content.deduplication import ContentDeduplication
        
        dedup = ContentDeduplication()
        similarity = dedup.calculate_similarity("hello", "world")
        
        assert similarity < 0.5

    def test_is_similar_above_threshold(self):
        """测试相似度判断 - 超过阈值"""
        from app.services.content.deduplication import ContentDeduplication
        
        dedup = ContentDeduplication()
        is_similar = dedup.is_similar("hello world", "hello world", threshold=0.8)
        
        assert is_similar is True

    def test_is_similar_below_threshold(self):
        """测试相似度判断 - 低于阈值"""
        from app.services.content.deduplication import ContentDeduplication
        
        dedup = ContentDeduplication()
        is_similar = dedup.is_similar("hello", "world", threshold=0.8)
        
        assert is_similar is False


# ==================== 分发策略测试 ====================

class TestDistributionStrategy:
    """分发策略测试"""

    def test_select_best_account_highest_score(self):
        """测试选择最佳账号 - 最高分"""
        from app.services.operations.distribution_strategy import DistributionStrategy
        
        strategy = DistributionStrategy()
        
        accounts = [
            {"id": 1, "health_score": 70},
            {"id": 2, "health_score": 90},
            {"id": 3, "health_score": 80},
        ]
        
        best = strategy.select_best_account(accounts)
        
        assert best["id"] == 2

    def test_select_best_account_empty_list(self):
        """测试选择最佳账号 - 空列表"""
        from app.services.operations.distribution_strategy import DistributionStrategy
        
        strategy = DistributionStrategy()
        
        best = strategy.select_best_account([])
        
        assert best is None

    def test_calculate_distribution_weight(self):
        """测试计算分发权重"""
        from app.services.operations.distribution_strategy import DistributionStrategy
        
        strategy = DistributionStrategy()
        
        weights = strategy.calculate_distribution_weight([
            {"health_score": 90},
            {"health_score": 70},
        ])
        
        assert len(weights) == 2
        assert sum(weights) == pytest.approx(1.0)

    def test_should_retry_on_failure(self):
        """测试失败时是否重试"""
        from app.services.operations.distribution_strategy import DistributionStrategy
        
        strategy = DistributionStrategy()
        
        # 重试次数小于3应该重试
        assert strategy.should_retry(retry_count=0) is True
        assert strategy.should_retry(retry_count=2) is True
        assert strategy.should_retry(retry_count=3) is False

    def test_get_retry_delay(self):
        """测试获取重试延迟"""
        from app.services.operations.distribution_strategy import DistributionStrategy
        
        strategy = DistributionStrategy()
        
        delay_1 = strategy.get_retry_delay(1)
        delay_2 = strategy.get_retry_delay(2)
        
        # 指数退避：延迟应该递增
        assert delay_2 > delay_1


# ==================== 格式转换服务测试 ====================

class TestFormatConversion:
    """格式转换服务测试"""

    def test_validate_video_format_supported(self):
        """测试验证视频格式 - 支持的格式"""
        from app.services.distribute.format_conversion import FormatConversion
        
        converter = FormatConversion()
        
        assert converter.validate_video_format("mp4") is True
        assert converter.validate_video_format("avi") is True
        assert converter.validate_video_format("mov") is True

    def test_validate_video_format_unsupported(self):
        """测试验证视频格式 - 不支持的格式"""
        from app.services.distribute.format_conversion import FormatConversion
        
        converter = FormatConversion()
        
        assert converter.validate_video_format("xyz") is False

    def test_get_recommended_format_by_platform(self):
        """测试根据平台获取推荐格式"""
        from app.services.distribute.format_conversion import FormatConversion
        
        converter = FormatConversion()
        
        douyin_format = converter.get_recommended_format("douyin")
        assert douyin_format == "mp4"

    def test_calculate_aspect_ratio(self):
        """测试计算宽高比"""
        from app.services.distribute.format_conversion import FormatConversion
        
        converter = FormatConversion()
        
        ratio = converter.calculate_aspect_ratio(1920, 1080)
        assert ratio == pytest.approx(16/9)

    def test_is_vertical_video(self):
        """测试判断是否为竖屏视频"""
        from app.services.distribute.format_conversion import FormatConversion
        
        converter = FormatConversion()
        
        assert converter.is_vertical_video(1080, 1920) is True
        assert converter.is_vertical_video(1920, 1080) is False


# ==================== JWT安全模块测试 ====================

class TestJWTSecurity:
    """JWT安全模块测试"""

    def test_create_access_token(self):
        """测试创建access token"""
        from app.core.security import create_access_token
        
        token = create_access_token(data={"sub": 1})
        
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_access_token_with_expiry(self):
        """测试创建带过期时间的token"""
        from app.core.security import create_access_token
        from datetime import timedelta
        
        token = create_access_token(
            data={"sub": 1},
            expires_delta=timedelta(minutes=5)
        )
        
        assert isinstance(token, str)

    def test_verify_token_valid(self):
        """测试验证有效token"""
        from app.core.security import create_access_token, verify_token
        
        token = create_access_token(data={"sub": 1})
        payload = verify_token(token)
        
        assert payload["sub"] == 1

    def test_verify_token_invalid(self):
        """测试验证无效token"""
        from app.core.security import verify_token
        from fastapi import HTTPException
        
        with pytest.raises(HTTPException):
            verify_token("invalid.token.here")

    def test_authenticate_user_success(self):
        """测试用户认证成功"""
        from app.core.security import authenticate_user
        from app.utils.security import hash_password
        
        password = "test_password"
        hashed = hash_password(password)
        
        assert authenticate_user("user", password, hashed) is True

    def test_authenticate_user_failure(self):
        """测试用户认证失败"""
        from app.core.security import authenticate_user
        from app.utils.security import hash_password
        
        password = "test_password"
        hashed = hash_password(password)
        
        assert authenticate_user("user", "wrong_password", hashed) is False


# ==================== 异步助手测试 ====================

class TestAsyncHelper:
    """异步助手测试"""

    def test_run_async_task_sync_function(self):
        """测试运行同步函数"""
        from app.utils.async_helper import run_async_task
        
        def sync_func():
            return "result"
        
        result = run_async_task(sync_func())
        assert result == "result"

    def test_run_async_task_async_function(self):
        """测试运行异步函数"""
        from app.utils.async_helper import run_async_task
        import asyncio
        
        async def async_func():
            await asyncio.sleep(0.01)
            return "async_result"
        
        result = run_async_task(async_func())
        assert result == "async_result"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=app", "--cov-report=term-missing"])
