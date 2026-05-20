from typing import List, Dict
from app.utils.logger import logger

class BannedWordsFilter:
    """多平台违禁词实时筛查引擎（含政治敏感词过滤）"""

    def __init__(self):
        # 模拟从数据库或配置文件加载的敏感词库
        self.banned_words = {
            "douyin": ["第一", "顶级", "绝对", "微信", "私信", "赚钱"],
            "xiaohongshu": ["微信", "购买", "下单", "链接", "淘宝"],
            "bilibili": ["广告", "引流", "加群"],
            "toutiao": []  # 头条使用通用规则
        }
        
        # ★★★ 政治敏感词库（所有平台通用）★★★
        self.political_sensitive_words = [
            # 领导人相关
            "习主席", "习近平", "总理", "主席", "总书记",
            "政治局", "常委", "中央领导", "国家领导人",
            
            # 政治事件
            "六四", "天安门", "法轮功", "藏独", "台独",
            "港独", "疆独", "民运", "学潮",
            
            # 政治组织
            "共产党", "国民党", "民主党派", "反动派",
            "恐怖组织", "邪教", "非法组织",
            
            # 敏感话题
            "政变", "革命", "起义", "暴动", "抗议",
            "游行", "示威", "罢工", "罢课",
            
            # 国际关系敏感
            "台湾独立", "西藏独立", "新疆独立",
            "南海仲裁", "钓鱼岛", "中美贸易战",
            
            # 其他敏感词汇
            "腐败", "贪污", "受贿", "行贿",
            "专制", "独裁", "民主运动", "人权问题"
        ]
        
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
        
        # ★★★ 关键修复：先检查政治敏感词（所有平台通用）★★★
        for word in self.political_sensitive_words:
            if word in text:
                violations.append(f"[政治敏感] {word}")
        
        # 如果检测到政治敏感词，直接返回失败（不允许发布）
        if violations:
            logger.error(f"❌ 检测到政治敏感内容: {violations}")
            logger.error("   ⛔ 根据规定，禁止发布政治、领导人、社会敏感话题文章")
            return {
                "cleaned_text": text,
                "violations": violations,
                "is_safe": False
            }
        
        # 然后检查平台特定违禁词
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
