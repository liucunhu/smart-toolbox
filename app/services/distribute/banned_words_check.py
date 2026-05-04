from typing import List, Dict
from app.utils.logger import logger

class BannedWordsFilter:
    """多平台违禁词实时筛查引擎"""

    def __init__(self):
        # 模拟从数据库或配置文件加载的敏感词库
        self.banned_words = {
            "douyin": ["第一", "顶级", "绝对", "微信", "私信", "赚钱"],
            "xiaohongshu": ["微信", "购买", "下单", "链接", "淘宝"],
            "bilibili": ["广告", "引流", "加群"]
        }
        # 替换建议映射
        self.replacements = {
            "微信": "V信",
            "赚钱": "搞米",
            "第一": "No.1",
            "顶级": "天花板"
        }

    def check_and_replace(self, text: str, platform: str) -> Dict[str, any]:
        """
        检查文本并返回处理结果
        :return: {"cleaned_text": str, "violations": List[str]}
        """
        violations = []
        words_to_check = self.banned_words.get(platform, [])
        
        for word in words_to_check:
            if word in text:
                violations.append(word)
                # 执行智能替换
                if word in self.replacements:
                    text = text.replace(word, self.replacements[word])
                else:
                    text = text.replace(word, "*" * len(word))

        if violations:
            logger.warning(f"检测到平台 {platform} 违禁词: {violations}")
        
        return {
            "cleaned_text": text,
            "violations": violations,
            "is_safe": len(violations) == 0
        }

# 示例调用
if __name__ == "__main__":
    filter_engine = BannedWordsFilter()
    result = filter_engine.check_and_replace("这个产品绝对是全网第一，想赚钱的加微信！", "douyin")
    print(result)
