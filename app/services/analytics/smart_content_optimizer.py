"""
智能内容优化器
基于账号历史文章分析结果，为新文章提供智能优化建议
包括：图片位置建议、内容结构优化、标题优化等
"""
import re
from typing import List, Dict, Optional
from app.utils.logger import logger


class SmartContentOptimizer:
    """智能内容优化器"""
    
    def __init__(self):
        self.title_patterns = {
            "数字型": {
                "pattern": r"\d+[个种项条]",
                "examples": ["3个技巧", "5种方法", "10个案例"],
                "weight": 0.9
            },
            "疑问型": {
                "pattern": r"(为什么|如何|怎么|什么)",
                "examples": ["为什么...", "如何实现...", "怎么选择..."],
                "weight": 0.85
            },
            "对比型": {
                "pattern": r"(VS|对比|区别|差异)",
                "examples": ["A VS B", "两者的区别", "对比分析"],
                "weight": 0.8
            },
            "痛点型": {
                "pattern": r"(总是|经常|困扰|难题)",
                "examples": ["总是失败？", "经常困扰你的问题"],
                "weight": 0.88
            }
        }
    
    def generate_optimization_suggestions(
        self,
        article_content: str,
        title: str,
        category: str,
        historical_analytics: Optional[List[Dict]] = None
    ) -> Dict:
        """
        生成智能优化建议
        
        Args:
            article_content: 文章内容
            title: 文章标题
            category: 文章分类
            historical_analytics: 历史文章分析数据
            
        Returns:
            优化建议字典
        """
        logger.info("🎯 开始生成智能优化建议...")
        
        suggestions = {
            "title_optimization": self._optimize_title(title, historical_analytics),
            "content_structure": self._analyze_content_structure(article_content),
            "image_suggestions": self._suggest_image_positions(article_content, title),
            "engagement_tips": self._generate_engagement_tips(historical_analytics),
            "publishing_tips": self._suggest_publishing_time()
        }
        
        logger.info(f"✅ 优化建议生成完成")
        return suggestions
    
    def _optimize_title(self, title: str, historical_data: Optional[List[Dict]]) -> Dict:
        """优化标题"""
        analysis = {
            "current_length": len(title),
            "optimal_range": (20, 30),
            "patterns_detected": [],
            "suggestions": []
        }
        
        for pattern_name, pattern_info in self.title_patterns.items():
            if re.search(pattern_info["pattern"], title):
                analysis["patterns_detected"].append({
                    "name": pattern_name,
                    "weight": pattern_info["weight"]
                })
        
        if len(title) < 20:
            analysis["suggestions"].append({
                "type": "length",
                "issue": "标题过短，信息量不足",
                "recommendation": "建议增加到20-30字，添加更多关键词和吸引力元素"
            })
        elif len(title) > 35:
            analysis["suggestions"].append({
                "type": "length",
                "issue": "标题过长，可能被截断",
                "recommendation": "建议精简到30字以内，突出核心卖点"
            })
        else:
            analysis["suggestions"].append({
                "type": "length",
                "issue": None,
                "recommendation": "✅ 标题长度适中"
            })
        
        if historical_data and len(historical_data) > 0:
            best_performing = max(historical_data, key=lambda x: x.get("read_count", 0))
            best_title = best_performing.get("title", "")
            
            for pattern_name in self.title_patterns.keys():
                if re.search(self.title_patterns[pattern_name]["pattern"], best_title):
                    analysis["suggestions"].append({
                        "type": "pattern",
                        "recommendation": f"💡 您的高阅读文章常使用「{pattern_name}」标题，建议继续使用"
                    })
                    break
        
        if not analysis["patterns_detected"]:
            analysis["suggestions"].append({
                "type": "pattern",
                "recommendation": "⚠️  建议添加数字、疑问词或痛点词，增强吸引力"
            })
        
        return analysis
    
    def _analyze_content_structure(self, content: str) -> Dict:
        """分析内容结构"""
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        total_length = len(content)
        
        analysis = {
            "paragraph_count": len(paragraphs),
            "total_length": total_length,
            "avg_paragraph_length": total_length / max(len(paragraphs), 1),
            "structure_score": 0,
            "issues": [],
            "recommendations": []
        }
        
        if len(paragraphs) < 5:
            analysis["issues"].append("段落数量较少，建议增加内容深度")
            analysis["recommendations"].append("💡 建议将文章扩展到5-10个段落，每段200-400字")
        elif len(paragraphs) > 15:
            analysis["issues"].append("段落数量较多，可能影响阅读体验")
            analysis["recommendations"].append("💡 考虑合并相关段落，保持7-12个段落为宜")
        else:
            analysis["structure_score"] += 30
        
        avg_len = analysis["avg_paragraph_length"]
        if avg_len < 100:
            analysis["issues"].append("段落过短，缺乏深度")
            analysis["recommendations"].append("💡 每个段落建议200-400字，提供更详细的信息")
        elif avg_len > 600:
            analysis["issues"].append("段落过长，阅读疲劳")
            analysis["recommendations"].append("💡 建议拆分长段落，每段控制在300-500字")
        else:
            analysis["structure_score"] += 30
        
        has_subheadings = bool(re.search(r'#{1,3}\s+.+', content)) or \
                         bool(re.search(r'[一二三四五六七八九十]、\s*\S{2,10}', content))
        
        if has_subheadings:
            analysis["structure_score"] += 20
            analysis["recommendations"].append("✅ 检测到小标题，结构清晰")
        else:
            analysis["issues"].append("缺少小标题，建议添加结构化标记")
            analysis["recommendations"].append("💡 建议添加3-5个小标题，提升可读性")
        
        has_lists = bool(re.search(r'[-*•]\s+', content)) or \
                   bool(re.search(r'\d+\.\s+', content))
        
        if has_lists:
            analysis["structure_score"] += 20
            analysis["recommendations"].append("✅ 使用了列表形式，易于阅读")
        else:
            analysis["recommendations"].append("💡 适当使用列表呈现要点，提升阅读体验")
        
        return analysis
    
    def _suggest_image_positions(
        self, 
        content: str, 
        title: str,
        num_images: int = 3
    ) -> List[Dict]:
        """基于内容和历史数据建议图片位置"""
        from app.services.content.article_image_position_analyzer import suggest_image_positions
        
        base_suggestions = suggest_image_positions(content, title, num_images)
        
        enhanced_suggestions = []
        paragraphs = content.split('\n\n')
        
        for suggestion in base_suggestions:
            position = suggestion["position"]
            theme = suggestion.get("theme", "")
            prompt = suggestion.get("prompt", "")
            
            if position < len(paragraphs):
                para_text = paragraphs[position][:100]
                
                if position == 0:
                    location_type = "开头引言后"
                    rationale = "吸引读者注意力，建立第一印象"
                elif position == len(paragraphs) - 1:
                    location_type = "结尾总结前"
                    rationale = "强化结论，留下深刻印象"
                else:
                    location_type = "正文中间"
                    rationale = "缓解阅读疲劳，增强理解"
                
                enhanced_suggestion = {
                    "position": position,
                    "theme": theme,
                    "prompt": prompt,
                    "location_type": location_type,
                    "rationale": rationale,
                    "preview_text": para_text + "..." if len(para_text) >= 100 else para_text
                }
                
                enhanced_suggestions.append(enhanced_suggestion)
        
        return enhanced_suggestions
    
    def _generate_engagement_tips(self, historical_data: Optional[List[Dict]]) -> List[str]:
        """生成互动优化建议"""
        tips = []
        
        tips.append("💬 在文中设置2-3个思考问题，引导读者评论")
        tips.append("📊 文末添加投票或征集观点，提升参与度")
        tips.append("🔄 鼓励读者分享自己的经历和看法")
        
        if historical_data and len(historical_data) > 0:
            avg_comments = sum(d.get("comment_count", 0) for d in historical_data) / len(historical_data)
            
            if avg_comments < 10:
                tips.append("⚠️  历史文章评论数偏低，建议在文末明确提出互动邀请")
            else:
                tips.append("✅ 您的文章互动良好，继续保持问答式写作风格")
        
        return tips
    
    def _suggest_publishing_time(self) -> Dict:
        """建议发布时间"""
        return {
            "best_times": [
                {"time": "08:00-09:00", "reason": "早高峰通勤时间"},
                {"time": "12:00-13:00", "reason": "午休时间"},
                {"time": "19:00-21:00", "reason": "晚间休闲时间"}
            ],
            "weekend_times": [
                {"time": "14:00-16:00", "reason": "周末下午休闲时段"}
            ],
            "recommendation": "💡 建议在工作日晚7-9点发布，获得最大曝光"
        }


def get_smart_optimization_suggestions(
    content: str,
    title: str,
    category: str,
    historical_analytics: Optional[List[Dict]] = None
) -> Dict:
    """
    获取智能优化建议（便捷函数）
    
    Usage:
        suggestions = get_smart_optimization_suggestions(article_content, title, category, history_data)
    """
    optimizer = SmartContentOptimizer()
    return optimizer.generate_optimization_suggestions(content, title, category, historical_analytics)
