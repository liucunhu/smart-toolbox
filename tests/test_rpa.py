import pytest
from app.rpa.douyin_engine import DouyinPublishEngine
from app.rpa.human_simulator import HumanSimulator

class TestRPAEngines:
    """RPA 引擎逻辑测试"""

    def test_douyin_engine_initialization(self):
        """测试抖音引擎初始化参数"""
        engine = DouyinPublishEngine(cookies={"name": "test"}, proxy_url="http://127.0.0.1:8080")
        assert engine.platform == "douyin"
        assert engine.proxy_url == "http://127.0.0.1:8080"

    def test_human_simulator_logic(self):
        """测试拟人化工具类的静态方法是否存在"""
        assert hasattr(HumanSimulator, 'random_sleep')
        assert hasattr(HumanSimulator, 'human_type')
        assert hasattr(HumanSimulator, 'smooth_scroll')
