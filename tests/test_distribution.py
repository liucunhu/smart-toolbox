import pytest
from app.services.operations.content_dedup import ContentDeduplicationService
from app.services.operations.distribution_strategy import StrategyFactory, DouyinStrategy

class TestContentDedup:
    """内容去重服务测试"""

    def test_unique_filename_generation(self):
        """测试为不同账号生成唯一文件名"""
        path = "output/video.mp4"
        name1 = ContentDeduplicationService.generate_unique_filename(path, 1)
        name2 = ContentDeduplicationService.generate_unique_filename(path, 2)
        
        assert name1 != name2
        assert "acc1" in name1
        assert "acc2" in name2

class TestDistributionStrategy:
    """分发策略引擎测试"""

    def test_get_douyin_strategy(self):
        """测试获取抖音策略"""
        strategy = StrategyFactory.get_strategy("douyin")
        assert isinstance(strategy, DouyinStrategy)

    def test_invalid_platform(self):
        """测试不支持的平台"""
        with pytest.raises(ValueError):
            StrategyFactory.get_strategy("unknown_platform")

    def test_douyin_content_validation(self):
        """测试抖音内容长度校验"""
        strategy = StrategyFactory.get_strategy("douyin")
        long_content = "a" * 301
        assert strategy.validate_content(long_content) is False
        assert strategy.validate_content("Short content") is True
