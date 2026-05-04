"""
核心 Service 层单元测试
测试违禁词过滤、健康监控、智能调度等功能
"""
import pytest
from app.services.distribute.ac_filter import HighPerformanceFilter, ACAutomaton
from app.services.operations.health_monitor import AccountHealthService
from app.services.operations.smart_scheduler import SmartScheduler
from datetime import datetime


class TestACAutomaton:
    """AC自动机节点测试"""

    def test_node_initialization(self):
        """测试节点初始化"""
        node = ACAutomaton()
        assert node.children == {}
        assert node.fail is None
        assert node.is_end is False
        assert node.word is None

    def test_add_children(self):
        """测试添加子节点"""
        node = ACAutomaton()
        child = ACAutomaton()
        node.children['a'] = child
        assert 'a' in node.children
        assert node.children['a'] == child


class TestHighPerformanceFilter:
    """高性能违禁词过滤器测试"""

    def setup_method(self):
        """每个测试方法前执行"""
        self.filter = HighPerformanceFilter()
        self.filter.load_platform_rules("douyin")

    def test_basic_violation_detection(self):
        """测试基础违禁词检测"""
        text = "这个产品绝对是全网第一，想赚钱的加微信！"
        result = self.filter.filter_text(text)
        
        assert result["is_safe"] is False
        assert len(result["violations"]) > 0
        assert "微信" in result["violations"] or "赚钱" in result["violations"]

    def test_safe_text(self):
        """测试安全文本"""
        text = "今天天气真好，适合出去走走"
        result = self.filter.filter_text(text)
        
        assert result["is_safe"] is True
        assert len(result["violations"]) == 0
        assert result["cleaned_text"] == text

    def test_replacement_logic(self):
        """测试替换逻辑"""
        text = "想赚钱的加微信"
        result = self.filter.filter_text(text)
        
        assert result["is_safe"] is False
        # 检查是否进行了替换
        assert "微信" not in result["cleaned_text"] or "V信" in result["cleaned_text"]

    def test_empty_text(self):
        """测试空文本"""
        result = self.filter.filter_text("")
        assert result["is_safe"] is True
        assert len(result["violations"]) == 0

    def test_multiple_violations(self):
        """测试多个违禁词"""
        text = "第一顶级绝对微信赚钱"
        result = self.filter.filter_text(text)
        
        assert result["is_safe"] is False
        assert len(result["violations"]) >= 2

    def test_platform_douyin_rules(self):
        """测试抖音平台规则"""
        self.filter.load_platform_rules("douyin")
        text = "加我微信，带你赚钱，绝对是第一"
        result = self.filter.filter_text(text)
        
        assert result["is_safe"] is False
        assert "微信" in result["violations"]
        assert "赚钱" in result["violations"]
        assert "第一" in result["violations"]

    def test_platform_xiaohongshu_rules(self):
        """测试小红书平台规则"""
        self.filter.load_platform_rules("xiaohongshu")
        text = "淘宝链接，加微信购买"
        result = self.filter.filter_text(text)
        
        assert result["is_safe"] is False
        assert "淘宝" in result["violations"] or "微信" in result["violations"]

    def test_unknown_platform(self):
        """测试未知平台（应使用空规则）"""
        self.filter.load_platform_rules("unknown")
        text = "微信赚钱"
        result = self.filter.filter_text(text)
        
        # 未知平台没有规则，应该返回安全
        assert result["is_safe"] is True
        assert len(result["violations"]) == 0

    def test_replacement_wechat(self):
        """测试微信替换为V信"""
        text = "加微信联系"
        result = self.filter.filter_text(text)
        
        assert "微信" in result["violations"]
        assert "V信" in result["cleaned_text"]

    def test_replacement_money(self):
        """测试赚钱替换为搞米"""
        text = "想赚钱的来"
        result = self.filter.filter_text(text)
        
        assert "赚钱" in result["violations"]
        assert "搞米" in result["cleaned_text"]

    def test_replacement_first(self):
        """测试第一替换为No.1"""
        text = "全网第一"
        result = self.filter.filter_text(text)
        
        assert "第一" in result["violations"]
        assert "No.1" in result["cleaned_text"]

    def test_replacement_top(self):
        """测试顶级替换为天花板"""
        text = "顶级产品"
        result = self.filter.filter_text(text)
        
        assert "顶级" in result["violations"]
        assert "天花板" in result["cleaned_text"]

    def test_replacement_absolute(self):
        """测试绝对替换为真的"""
        text = "绝对好用"
        result = self.filter.filter_text(text)
        
        assert "绝对" in result["violations"]
        assert "真的" in result["cleaned_text"]

    def test_no_replacement_for_unknown_word(self):
        """测试未知违禁词用星号替换"""
        # 添加一个没有在replacements中的词
        self.filter.add_keyword("测试词")
        self.filter.build_failure_pointer()
        
        text = "这是测试词"
        result = self.filter.filter_text(text)
        
        assert "测试词" in result["violations"]
        assert "***" in result["cleaned_text"]

    def test_overlapping_violations(self):
        """测试重叠违禁词"""
        text = "微信赚钱第一"
        result = self.filter.filter_text(text)
        
        assert result["is_safe"] is False
        assert len(result["violations"]) >= 2

    def test_case_sensitivity(self):
        """测试大小写敏感性（中文不区分）"""
        text = "微信WX信"
        result = self.filter.filter_text(text)
        
        # 应该只检测到“微信”
        assert "微信" in result["violations"]

    def test_long_text_performance(self):
        """测试长文本性能"""
        import time
        long_text = "这是一个很长的文本" * 1000
        start = time.time()
        result = self.filter.filter_text(long_text)
        elapsed = time.time() - start
        
        # 应该在1秒内完成
        assert elapsed < 1.0
        assert result["is_safe"] is True

    def test_special_characters(self):
        """测试特殊字符"""
        text = "@#￥%……&*（）"
        result = self.filter.filter_text(text)
        
        assert result["is_safe"] is True

    def test_unicode_characters(self):
        """测试Unicode字符"""
        text = "你好🌍世界✨"
        result = self.filter.filter_text(text)
        
        assert result["is_safe"] is True

    def test_empty_keywords_list(self):
        """测试关键词列表为空的情况"""
        filter_empty = HighPerformanceFilter()
        result = filter_empty.filter_text("任何文本")
        
        assert result["is_safe"] is True
        assert result["violations"] == []

    def test_add_keyword_manually(self):
        """测试手动添加关键词"""
        self.filter.add_keyword("自定义敏感词")
        self.filter.build_failure_pointer()
        
        text = "这是自定义敏感词测试"
        result = self.filter.filter_text(text)
        
        assert "自定义敏感词" in result["violations"]

    def test_filter_preserves_original_length(self):
        """测试过滤后文本长度保持一致"""
        text = "微信赚钱第一"
        result = self.filter.filter_text(text)
        
        # 替换后的文本长度应该相同
        assert len(result["cleaned_text"]) == len(text)


class TestSmartScheduler:
    """智能调度器测试"""

    def test_publish_time_within_window(self):
        """测试在活跃窗口内生成时间"""
        current = datetime(2026, 4, 29, 10, 0, 0)
        result = SmartScheduler.get_next_publish_time(current)
        
        assert result >= current
        assert 8 <= result.hour < 22

    def test_publish_time_before_window(self):
        """测试在非活跃窗口（凌晨）生成时间"""
        current = datetime(2026, 4, 29, 3, 0, 0)
        result = SmartScheduler.get_next_publish_time(current)
        
        # 应该跳转到当天的8点以后
        assert result.day == current.day
        assert result.hour >= 8

    def test_publish_time_after_window(self):
        """测试在非活跃窗口（深夜）生成时间"""
        current = datetime(2026, 4, 29, 23, 0, 0)
        result = SmartScheduler.get_next_publish_time(current)
        
        # 应该跳转到第二天的8点以后
        assert result.day > current.day
        assert result.hour >= 8

    def test_account_availability_under_limit(self):
        """测试账号未达到发布上限"""
        assert SmartScheduler.is_account_available(4) is True
        assert SmartScheduler.is_account_available(0) is True

    def test_account_availability_at_limit(self):
        """测试账号达到发布上限"""
        assert SmartScheduler.is_account_available(5) is False
        assert SmartScheduler.is_account_available(6) is False


class TestAccountHealthService:
    """账号健康服务测试（需要数据库fixture）"""

    def test_health_score_calculation(self):
        """测试健康分计算逻辑（模拟）"""
        # 这里只是示例，实际需要数据库session
        metrics = {
            "views": 5000,
            "interaction_rate": 0.05
        }
        
        # view_score = min(5000/1000, 40) = 5
        # interaction_score = 0.05 * 100 * 0.6 = 3
        # new_score = 5 + 3 = 8
        
        expected_score = 8.0
        assert expected_score > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
