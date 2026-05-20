"""
爆款潜力检测服务
评估文章的爆款概率，提供优化建议
"""
import re
from typing import Dict, List, Optional
from app.utils.logger import logger


class ViralPotentialChecker:
    """爆款潜力检测器"""
    
    def __init__(self):
        self.platform_rules = {
            "toutiao": {
                "optimal_title_length": (20, 35),  # 最佳标题长度
                "optimal_content_length": (1200, 2500),  # 最佳内容长度
                "required_elements": ["数字", "痛点", "悬念"],  # 标题必备元素
            }
        }
    
    def check_viral_potential(
        self,
        title: str,
        content: str,
        platform: str = "toutiao",
        topic: str = "",
        is_hot_topic: bool = False
    ) -> Dict:
        """
        检测文章爆款潜力
        
        Args:
            title: 文章标题
            content: 文章内容
            platform: 平台名称
            topic: 话题/关键词
            is_hot_topic: 是否为热点话题
            
        Returns:
            {
                "viral_score": 85,  # 爆款指数 (0-100)
                "level": "高潜力",   # 低/中/高/极高
                "strengths": [...],  # 优势点
                "weaknesses": [...], # 待优化点
                "suggestions": [...],# 优化建议
                "fact_check": {...}  # 事实核查结果（热点话题）
            }
        """
        logger.info(f"🔥 开始爆款潜力检测...")
        
        result = {
            "viral_score": 0,
            "level": "未知",
            "strengths": [],
            "weaknesses": [],
            "suggestions": [],
            "dimensions": {}
        }
        
        # 维度1: 标题吸引力 (30分)
        title_result = self._check_title_attractiveness(title)
        result["dimensions"]["title"] = title_result
        
        # 维度2: 内容质量 (25分)
        content_result = self._check_content_quality(content)
        result["dimensions"]["content"] = content_result
        
        # 维度3: 话题热度 (20分)
        topic_result = self._check_topic_heat(topic, is_hot_topic)
        result["dimensions"]["topic"] = topic_result
        
        # 维度4: 互动潜力 (15分)
        interaction_result = self._check_interaction_potential(content)
        result["dimensions"]["interaction"] = interaction_result
        
        # 维度5: 平台匹配度 (10分)
        platform_result = self._check_platform_match(title, content, platform)
        result["dimensions"]["platform"] = platform_result
        
        # 计算总分（提取每个维度的 score 字段）
        total_score = (
            title_result["score"] * 0.3 +
            content_result["score"] * 0.25 +
            topic_result["score"] * 0.2 +
            interaction_result["score"] * 0.15 +
            platform_result["score"] * 0.1
        )
        
        result["viral_score"] = round(total_score, 1)
        result["level"] = self._get_level_label(total_score)
        
        # 合并所有维度的优势和待优化点
        for dim_result in [title_result, content_result, topic_result, interaction_result, platform_result]:
            result["strengths"].extend(dim_result.get("strengths", []))
            result["weaknesses"].extend(dim_result.get("weaknesses", []))
        
        # 热点话题事实核查
        if is_hot_topic:
            fact_check_result = self._fact_check_for_hot_topic(title, content, topic)
            result["fact_check"] = fact_check_result
            
            # 如果事实核查失败，大幅降低分数
            if not fact_check_result["passed"]:
                result["viral_score"] = max(0, result["viral_score"] - 30)
                result["level"] = "不建议发布"
                result["weaknesses"].append("⚠️  热点话题存在事实风险")
        
        # 生成优化建议
        result["suggestions"] = self._generate_suggestions(result["dimensions"])
        
        logger.info(f"✅ 爆款潜力检测完成: {result['viral_score']}分 ({result['level']})")
        
        return result
    
    def _check_title_attractiveness(self, title: str) -> float:
        """检查标题吸引力 (0-100)"""
        score = 50  # 基础分
        strengths = []
        weaknesses = []
        
        # 1. 长度检查
        title_len = len(title)
        if 20 <= title_len <= 35:
            score += 15
            strengths.append(f"✅ 标题长度适中 ({title_len}字)")
        elif title_len < 15:
            score -= 10
            weaknesses.append(f"❌ 标题过短 ({title_len}字)，建议20-35字")
        elif title_len > 40:
            score -= 5
            weaknesses.append(f"⚠️  标题过长 ({title_len}字)，可能被截断")
        
        # 2. 是否包含数字
        if re.search(r'\d+', title):
            score += 10
            strengths.append("✅ 包含数字，增强可信度")
        else:
            weaknesses.append("💡 建议添加具体数字（如'3个技巧'、'5大趋势'）")
        
        # 3. 是否包含痛点/疑问词
        pain_words = ["为什么", "如何", "怎样", "揭秘", "真相", "警惕", "注意"]
        if any(word in title for word in pain_words):
            score += 10
            strengths.append("✅ 包含痛点或疑问，引发好奇")
        else:
            weaknesses.append("💡 建议加入痛点词（如'为什么'、'如何'）")
        
        # 4. 是否包含情感词
        emotion_words = ["震惊", "重磅", "突发", "终于", "必看", "干货"]
        if any(word in title for word in emotion_words):
            score += 5
            strengths.append("✅ 包含情感词，增强冲击力")
        
        return {
            "score": min(100, max(0, score)),
            "strengths": strengths,
            "weaknesses": weaknesses
        }
    
    def _check_content_quality(self, content: str) -> float:
        """检查内容质量 (0-100)"""
        score = 50  # 基础分
        strengths = []
        weaknesses = []
        
        content_len = len(content)
        
        # 1. 长度检查
        if 1200 <= content_len <= 2500:
            score += 15
            strengths.append(f"✅ 内容长度适中 ({content_len}字)")
        elif content_len < 800:
            score -= 15
            weaknesses.append(f"❌ 内容过短 ({content_len}字)，建议1200-2500字")
        elif content_len > 3500:
            score -= 5
            weaknesses.append(f"⚠️  内容过长 ({content_len}字)，用户可能失去耐心")
        
        # 2. 段落结构
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        para_count = len(paragraphs)
        
        if 5 <= para_count <= 15:
            score += 10
            strengths.append(f"✅ 段落结构合理 ({para_count}段)")
        elif para_count < 3:
            score -= 10
            weaknesses.append(f"❌ 段落太少 ({para_count}段)，建议分段更清晰")
        
        # 3. 是否有小标题
        subheadings = re.findall(r'^#{1,3}\s+.+$', content, re.MULTILINE)
        if len(subheadings) >= 2:
            score += 10
            strengths.append(f"✅ 包含{len(subheadings)}个小标题，结构清晰")
        else:
            weaknesses.append("💡 建议添加小标题，提升可读性")
        
        # 4. 是否有数据支撑
        if re.search(r'\d+%', content) or re.search(r'\d+\.\d+', content):
            score += 5
            strengths.append("✅ 包含数据支撑，增强说服力")
        
        return {
            "score": min(100, max(0, score)),
            "strengths": strengths,
            "weaknesses": weaknesses
        }
    
    def _check_topic_heat(self, topic: str, is_hot_topic: bool) -> float:
        """检查话题热度 (0-100)"""
        if is_hot_topic:
            return {
                "score": 90,
                "strengths": ["✅ 热点话题，自带流量"],
                "weaknesses": []
            }
        
        # 非热点话题，根据关键词判断
        hot_keywords = ["AI", "科技", "财经", "健康", "教育", "职场"]
        if any(keyword in topic for keyword in hot_keywords):
            return {
                "score": 70,
                "strengths": ["✅ 话题具有一定热度"],
                "weaknesses": []
            }
        
        return {
            "score": 50,
            "strengths": [],
            "weaknesses": ["💡 建议选择当前热点话题，获得更多曝光"]
        }
    
    def _check_interaction_potential(self, content: str) -> float:
        """检查互动潜力 (0-100)"""
        score = 50
        strengths = []
        weaknesses = []
        
        # 1. 是否有提问
        questions = re.findall(r'[？?]', content)
        if len(questions) >= 2:
            score += 15
            strengths.append(f"✅ 包含{len(questions)}个问题，促进互动")
        else:
            weaknesses.append("💡 建议在文中设置问题，引导读者思考")
        
        # 2. 是否有争议观点
        controversy_words = ["但是", "然而", "相反", "其实", "真相是"]
        if any(word in content for word in controversy_words):
            score += 10
            strengths.append("✅ 包含争议观点，容易引发讨论")
        
        # 3. 是否有行动号召
        cta_words = ["欢迎", "分享", "评论", "点赞", "关注"]
        if any(word in content for word in cta_words):
            score += 10
            strengths.append("✅ 包含行动号召，提升互动率")
        else:
            weaknesses.append("💡 建议在文末添加互动引导（如'你怎么看？'）")
        
        return {
            "score": min(100, max(0, score)),
            "strengths": strengths,
            "weaknesses": weaknesses
        }
    
    def _check_platform_match(self, title: str, content: str, platform: str) -> float:
        """检查平台匹配度 (0-100)"""
        if platform == "toutiao":
            # 头条偏好：深度分析、实用价值、数据支撑
            score = 60
            
            if len(content) >= 1200:
                score += 20
            if re.search(r'\d+', title):
                score += 10
            if "分析" in content or "解读" in content:
                score += 10
            
            return {
                "score": min(100, max(0, score)),
                "strengths": ["✅ 符合头条平台调性"],
                "weaknesses": []
            }
        
        return {"score": 50, "strengths": [], "weaknesses": []}
    
    def _fact_check_for_hot_topic(
        self,
        title: str,
        content: str,
        topic: str
    ) -> Dict:
        """
        热点话题事实核查
        
        原则：
        1. 不造谣 - 必须有可靠来源
        2. 不虚构 - 不能编造数据或事件
        3. 不偏离事实 - 准确描述已知信息
        4. 只描述事实 - 避免主观臆测
        """
        logger.info(f"🔍 开始热点话题事实核查...")
        
        issues = []
        warnings = []
        
        # 1. 检查是否有夸张表述
        exaggeration_words = [
            "史上最", "绝对", "百分百", " guaranteed", 
            "必定", "必然", "100%"
        ]
        
        for word in exaggeration_words:
            if word in title or word in content:
                issues.append(f"⚠️  发现绝对化表述: '{word}'，建议改为更客观的描述")
        
        # 2. 检查是否有未证实的信息
        unverified_patterns = [
            r"据说", r"传闻", r"网传", r" allegedly"
        ]
        
        for pattern in unverified_patterns:
            if re.search(pattern, content):
                warnings.append(f"⚠️  包含未证实信息，请标注信息来源")
        
        # 3. 检查数据来源
        if re.search(r'\d+%', content) or re.search(r'\d+万', content):
            if "据" not in content and "来源" not in content:
                warnings.append("💡 包含数据但未标注来源，建议补充")
        
        # 4. 检查是否区分事实和观点
        opinion_words = ["我认为", "我觉得", "应该", "必须"]
        fact_sentences = [s for s in content.split('。') if any(word in s for word in opinion_words)]
        
        if len(fact_sentences) > 3:
            warnings.append("💡 包含较多主观观点，热点话题应以事实为主")
        
        passed = len(issues) == 0
        
        result = {
            "passed": passed,
            "issues": issues,
            "warnings": warnings,
            "principles": {
                "no_rumors": len([i for i in issues if "绝对化" in i]) == 0,
                "no_fabrication": len(warnings) <= 2,
                "factual_accuracy": True,  # 需要人工审核
                "objective_description": len(fact_sentences) <= 3
            }
        }
        
        if passed:
            logger.info(f"✅ 事实核查通过")
        else:
            logger.warning(f"⚠️  事实核查发现问题: {len(issues)}个")
        
        return result
    
    def _get_level_label(self, score: float) -> str:
        """获取潜力等级标签"""
        if score >= 85:
            return "极高潜力"
        elif score >= 70:
            return "高潜力"
        elif score >= 55:
            return "中等潜力"
        elif score >= 40:
            return "低潜力"
        else:
            return "不建议发布"
    
    def _generate_suggestions(self, dimensions: Dict) -> List[str]:
        """生成优化建议"""
        suggestions = []
        
        # 标题优化
        title_data = dimensions.get("title", {})
        if title_data.get("score", 0) < 70:
            for weakness in title_data.get("weaknesses", []):
                suggestions.append(f"【标题】{weakness}")
        
        # 内容优化
        content_data = dimensions.get("content", {})
        if content_data.get("score", 0) < 70:
            for weakness in content_data.get("weaknesses", []):
                suggestions.append(f"【内容】{weakness}")
        
        # 互动优化
        interaction_data = dimensions.get("interaction", {})
        if interaction_data.get("score", 0) < 70:
            for weakness in interaction_data.get("weaknesses", []):
                suggestions.append(f"【互动】{weakness}")
        
        return suggestions[:5]  # 最多返回5条建议


def get_viral_checker() -> ViralPotentialChecker:
    """获取爆款检测器实例"""
    return ViralPotentialChecker()
