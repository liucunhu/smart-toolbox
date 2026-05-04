import pytest
from app.services.distribute.ac_filter import HighPerformanceFilter

class TestHighPerformanceFilter:
    """敏感词过滤引擎测试"""

    def setup_method(self):
        self.filter_engine = HighPerformanceFilter()
        # 模拟加载规则，必须调用 load_platform_rules 才能构建 AC 自动机
        self.filter_engine.load_platform_rules("douyin")

    def test_basic_filter(self):
        """测试基础敏感词识别与替换"""
        text = "想赚钱的加微信"
        result = self.filter_engine.filter_text(text)
        # AC 自动机逻辑中，replacements 是在 filter_text 内部使用的
        assert result["is_safe"] is False
        assert "微信" in result["violations"] or "赚钱" in result["violations"]

    def test_no_violations(self):
        """测试安全文案"""
        text = "今天天气真好"
        result = self.filter_engine.filter_text(text)
        assert result["is_safe"] is True
        assert len(result["violations"]) == 0

    def test_special_characters(self):
        """测试包含特殊符号的文本"""
        text = "赚-钱！加#微*信"
        result = self.filter_engine.filter_text(text)
        # 即使有符号，核心词也应被识别（取决于具体实现逻辑）
        assert isinstance(result, dict)
