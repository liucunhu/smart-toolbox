import pytest
from app.services.distribute.banned_words_check import BannedWordsFilter

class TestBannedWordsFilter:
    """违禁词筛查引擎测试"""

    def setup_method(self):
        self.filter = BannedWordsFilter()

    def test_douyin_banned_words(self):
        """测试抖音平台违禁词"""
        text = "这个产品绝对是全网第一"
        result = self.filter.check_and_replace(text, "douyin")
        assert "No.1" in result["cleaned_text"] or "*" in result["cleaned_text"]
        assert result["is_safe"] is False

    def test_xiaohongshu_banned_words(self):
        """测试小红书平台违禁词"""
        text = "点击链接购买淘宝商品"
        result = self.filter.check_and_replace(text, "xiaohongshu")
        assert result["is_safe"] is False
        assert "链接" in result["violations"]

    def test_empty_text(self):
        """测试空文本"""
        result = self.filter.check_and_replace("", "douyin")
        assert result["is_safe"] is True
        assert len(result["violations"]) == 0
