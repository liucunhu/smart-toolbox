"""
智能图片位置分析器
根据文章内容分析最适合插入图片的位置，并生成相关的图片提示词
"""
import re
from typing import List, Dict
from app.utils.logger import logger


class ImagePositionAnalyzer:
    """智能图片位置分析器"""
    
    def __init__(self):
        # 关键词到主题的映射
        self.keyword_to_theme = {
            "AI": {
                "keywords": ["人工智能", "AI", "机器学习", "深度学习", "神经网络"],
                "theme_template": "{keyword}应用场景",
                "prompt_template": "展示{keyword}在现代生活中的实际应用场景，科技感强，未来感十足"
            },
            "数据": {
                "keywords": ["数据", "分析", "统计", "图表", "可视化"],
                "theme_template": "{keyword}分析与可视化",
                "prompt_template": "专业的{keyword}可视化展示，商业风格，清晰直观"
            },
            "技术": {
                "keywords": ["技术", "创新", "研发", "突破", "前沿"],
                "theme_template": "{keyword}创新与发展",
                "prompt_template": "{keyword}领域的最新发展，高科技感，专业质感"
            },
            "应用": {
                "keywords": ["应用", "实践", "案例", "场景", "落地"],
                "theme_template": "{keyword}实践案例",
                "prompt_template": "{keyword}的实际应用案例，生动形象，易于理解"
            },
            "趋势": {
                "keywords": ["趋势", "未来", "展望", "预测", "发展"],
                "theme_template": "{keyword}展望",
                "prompt_template": "{keyword}的未来发展趋势，前瞻性，启发性"
            }
        }
    
    def analyze_and_suggest(
        self, 
        content: str, 
        title: str,
        num_images: int = 3
    ) -> List[Dict]:
        """
        分析文章内容，建议图片插入位置
        
        Args:
            content: 文章内容
            title: 文章标题
            num_images: 需要生成的图片数量
            
        Returns:
            图片位置建议列表
        """
        # 分割段落
        paragraphs = self._split_paragraphs(content)
        total_paragraphs = len(paragraphs)
        
        if total_paragraphs == 0:
            logger.warning("⚠️  文章内容为空，无法分析图片位置")
            return []
        
        logger.info(f"📊 开始分析文章，共 {total_paragraphs} 个段落，计划插入 {num_images} 张图片")
        
        # 为每个段落计算重要性分数
        paragraph_scores = []
        for idx, para in enumerate(paragraphs):
            score = self._calculate_paragraph_score(para, idx, total_paragraphs, title)
            paragraph_scores.append({
                "index": idx,
                "text": para[:50],
                "score": score,
                "length": len(para)
            })
        
        # 选择最佳的插入位置
        suggestions = self._select_best_positions(paragraph_scores, num_images, total_paragraphs)
        
        # 为每个位置生成图片提示词
        for suggestion in suggestions:
            para_text = paragraphs[suggestion["position"]]
            theme_info = self._generate_image_prompt(para_text, title)
            suggestion.update(theme_info)
        
        logger.info(f"✅ 图片位置分析完成，建议 {len(suggestions)} 个位置")
        for i, sug in enumerate(suggestions, 1):
            logger.info(f"   位置{i}: 第{sug['position'] + 1}段后 - {sug.get('theme', '通用主题')}")
        
        return suggestions
    
    def _split_paragraphs(self, content: str) -> List[str]:
        """分割段落（支持多种分隔符）"""
        # 按换行符分割
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # 如果只有一个段落，尝试按句号分割
        if len(paragraphs) <= 1:
            sentences = re.split(r'[。！？\n]', content)
            paragraphs = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        return paragraphs
    
    def _calculate_paragraph_score(
        self, 
        paragraph: str, 
        index: int, 
        total: int,
        title: str
    ) -> float:
        """
        计算段落的重要性分数
        
        考虑因素：
        1. 位置（开头、结尾权重高）
        2. 长度（较长的段落通常更重要）
        3. 关键词密度
        4. 是否包含数字（数据段落）
        """
        score = 0.0
        
        # 1. 位置权重
        position_weight = self._get_position_weight(index, total)
        score += position_weight * 0.3
        
        # 2. 长度权重（适中的长度最好）
        length = len(paragraph)
        if 50 <= length <= 300:
            score += 0.2
        elif length > 300:
            score += 0.1
        
        # 3. 关键词匹配
        keyword_score = self._check_keywords(paragraph, title)
        score += keyword_score * 0.3
        
        # 4. 是否包含数据/案例
        if re.search(r'\d+\.?\d*[%亿元万台套个]', paragraph):
            score += 0.15
        
        # 5. 是否包含示例词汇
        example_words = ["例如", "比如", "案例", "实例", "以...为例"]
        if any(word in paragraph for word in example_words):
            score += 0.1
        
        return min(score, 1.0)
    
    def _get_position_weight(self, index: int, total: int) -> float:
        """获取位置权重"""
        if index == 0:
            return 0.8
        elif index == total - 1:
            return 0.9
        elif index < total * 0.2:
            return 0.6
        elif index > total * 0.8:
            return 0.7
        else:
            return 0.5
    
    def _check_keywords(self, paragraph: str, title: str) -> float:
        """检查段落与标题的关键词匹配度"""
        title_words = re.findall(r'[\u4e00-\u9fa5]{2,}', title)
        
        if not title_words:
            return 0.0
        
        matches = sum(1 for word in title_words if word in paragraph)
        return matches / len(title_words)
    
    def _select_best_positions(
        self, 
        paragraph_scores: List[Dict],
        num_images: int,
        total_paragraphs: int
    ) -> List[Dict]:
        """
        选择最佳的插入位置
        
        策略：
        1. 按分数排序
        2. 确保位置分散（避免集中在某一段）
        3. 保持合理的间距
        """
        sorted_paragraphs = sorted(paragraph_scores, key=lambda x: x["score"], reverse=True)
        
        selected = []
        min_distance = total_paragraphs // (num_images + 1)
        
        for para in sorted_paragraphs:
            if len(selected) >= num_images:
                break
            
            idx = para["index"]
            
            too_close = False
            for selected_idx in selected:
                if abs(idx - selected_idx) < min_distance:
                    too_close = True
                    break
            
            if not too_close:
                selected.append(idx)
        
        selected.sort()
        
        return [{"position": idx} for idx in selected]
    
    def _generate_image_prompt(self, paragraph: str, title: str) -> Dict[str, str]:
        """
        根据段落内容生成图片提示词
        
        Returns:
            {
                "theme": "主题名称",
                "prompt": "图片生成提示词",
                "keywords": ["关键词1", "关键词2"]
            }
        """
        best_match = None
        best_score = 0
        
        for category, info in self.keyword_to_theme.items():
            matches = [kw for kw in info["keywords"] if kw in paragraph or kw in title]
            score = len(matches)
            
            if score > best_score:
                best_score = score
                best_match = {
                    "category": category,
                    "keywords": matches,
                    "info": info
                }
        
        if not best_match or best_score == 0:
            title_keywords = re.findall(r'[\u4e00-\u9fa5]{2,4}', title)[:3]
            theme = " ".join(title_keywords) if title_keywords else "科技前沿"
            prompt = f"{theme}相关的高质量配图，专业质感，现代风格"
            keywords = title_keywords
        else:
            info = best_match["info"]
            keyword = best_match["keywords"][0] if best_match["keywords"] else best_match["category"]
            
            theme = info["theme_template"].format(keyword=keyword)
            prompt = info["prompt_template"].format(keyword=keyword)
            keywords = best_match["keywords"]
        
        return {
            "theme": theme,
            "prompt": prompt,
            "keywords": keywords[:3]
        }


def suggest_image_positions(content: str, title: str, num_images: int = 3) -> List[Dict]:
    """
    便捷函数：分析文章并建议图片位置
    
    Usage:
        suggestions = suggest_image_positions(article_content, article_title, 3)
    """
    analyzer = ImagePositionAnalyzer()
    return analyzer.analyze_and_suggest(content, title, num_images)
