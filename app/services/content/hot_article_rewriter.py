"""
热点文章二次创作引擎
当网络搜索失败时，直接基于热点文章内容进行深度分析和二次原创
支持：内容提取、结构分析、观点重组、原创改写
"""
import re
from typing import List, Dict, Optional
from app.utils.logger import logger


class HotArticleRewriter:
    """热点文章二次创作引擎"""
    
    def __init__(self):
        # 内容去重策略
        self.rewrite_strategies = {
            "structure_reorg": "结构重组",      # 调整段落顺序
            "perspective_shift": "视角转换",     # 改变叙述角度
            "example_replace": "案例替换",       # 替换示例和案例
            "language_polish": "语言润色",       # 同义词替换和句式变换
            "depth_expand": "深度扩展",          # 添加深度分析
            "opinion_add": "观点补充"            # 加入新观点
        }
        
        # 原创度检查规则
        self.originality_rules = {
            "min_sentence_similarity": 0.6,  # 句子相似度阈值
            "min_paragraph_rewrite_rate": 0.7,  # 段落改写率
            "required_new_examples": 2,  # 至少添加的新案例数
            "required_new_opinions": 1   # 至少添加的新观点数
        }
    
    async def rewrite_from_hot_article(
        self,
        hot_article_content: str,
        hot_article_title: str,
        target_platform: str = "toutiao",
        rewrite_depth: str = "deep"  # light/medium/deep
    ) -> Dict:
        """
        基于热点文章进行二次创作
        
        Args:
            hot_article_content: 热点文章原始内容
            hot_article_title: 热点文章标题
            target_platform: 目标平台
            rewrite_depth: 改写深度（light/medium/deep）
            
        Returns:
            {
                "status": "success",
                "original_title": "...",
                "new_title": "...",
                "original_content_length": 1500,
                "new_content_length": 1800,
                "rewrite_strategies_used": ["结构重组", "视角转换"],
                "originality_score": 0.85,
                "content": "二次创作后的内容",
                "analysis": {...}
            }
        """
        logger.info(f"🔄 开始对热点文章进行二次创作（深度: {rewrite_depth}）")
        logger.info(f"   原标题: {hot_article_title}")
        logger.info(f"   原长度: {len(hot_article_content)}字")
        
        try:
            # 步骤1: 深度分析原文
            analysis = self._analyze_original_article(hot_article_content, hot_article_title)
            logger.info(f"✅ 原文分析完成")
            logger.info(f"   核心观点: {len(analysis['core_points'])}个")
            logger.info(f"   关键案例: {len(analysis['key_examples'])}个")
            logger.info(f"   文章结构: {analysis['structure_type']}")
            
            # 步骤2: 提取核心信息
            extracted_info = self._extract_core_information(analysis)
            logger.info(f"✅ 核心信息提取完成")
            
            # 步骤3: 制定改写策略
            strategies = self._plan_rewrite_strategy(analysis, rewrite_depth)
            logger.info(f"✅ 改写策略制定完成: {strategies}")
            
            # 步骤4: 执行二次创作
            rewritten_content = await self._execute_rewrite(
                analysis, 
                extracted_info, 
                strategies,
                target_platform
            )
            
            # 步骤5: 生成新标题
            new_title = self._generate_new_title(hot_article_title, analysis)
            
            # 步骤6: 原创度评估
            originality_score = self._evaluate_originality(
                hot_article_content, 
                rewritten_content
            )
            
            logger.info(f"✅ 二次创作完成")
            logger.info(f"   新标题: {new_title}")
            logger.info(f"   新长度: {len(rewritten_content)}字")
            logger.info(f"   原创度: {originality_score:.0%}")
            
            return {
                "status": "success",
                "original_title": hot_article_title,
                "new_title": new_title,
                "original_content_length": len(hot_article_content),
                "new_content_length": len(rewritten_content),
                "rewrite_strategies_used": strategies,
                "originality_score": originality_score,
                "content": rewritten_content,
                "analysis": analysis
            }
            
        except Exception as e:
            logger.error(f"❌ 二次创作失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _analyze_original_article(self, content: str, title: str) -> Dict:
        """
        深度分析原文结构
        
        Returns:
            {
                "core_points": [...],  # 核心观点
                "key_examples": [...],  # 关键案例
                "data_points": [...],   # 数据支撑
                "structure_type": "...", # 结构类型
                "paragraphs": [...],    # 段落列表
                "keywords": [...]       # 关键词
            }
        """
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # 提取核心观点（包含观点词的段落）
        opinion_indicators = ["认为", "应该", "必须", "重要", "关键", "建议", "总结"]
        core_points = []
        for para in paragraphs:
            if any(indicator in para for indicator in opinion_indicators):
                core_points.append(para[:200])
        
        # 提取关键案例（包含具体事例的段落）
        example_indicators = ["例如", "比如", "案例", "实例", "以...为例", "某公司", "某人"]
        key_examples = []
        for para in paragraphs:
            if any(indicator in para for indicator in example_indicators):
                key_examples.append(para[:300])
        
        # 提取数据支撑
        data_pattern = r'\d+\.?\d*[%亿元万台套个]'
        data_points = []
        for para in paragraphs:
            if re.search(data_pattern, para):
                data_points.append(para[:200])
        
        # 判断文章结构
        structure_type = self._identify_structure(paragraphs)
        
        # 提取关键词
        keywords = self._extract_keywords(content, title)
        
        return {
            "core_points": core_points[:5],  # 最多5个核心观点
            "key_examples": key_examples[:5],  # 最多5个案例
            "data_points": data_points[:5],  # 最多5个数据点
            "structure_type": structure_type,
            "paragraphs": paragraphs,
            "keywords": keywords[:10],
            "total_paragraphs": len(paragraphs),
            "avg_paragraph_length": sum(len(p) for p in paragraphs) / max(len(paragraphs), 1)
        }
    
    def _identify_structure(self, paragraphs: List[str]) -> str:
        """识别文章结构类型"""
        if len(paragraphs) < 3:
            return "simple"
        
        # 检测是否有小标题
        has_subheadings = any(
            re.match(r'^[一二三四五六七八九十]、|^\d+\.', p) 
            for p in paragraphs[:10]
        )
        
        if has_subheadings:
            return "structured_with_headings"
        
        # 检测是否为总分总结构
        first_para_len = len(paragraphs[0])
        last_para_len = len(paragraphs[-1])
        middle_avg_len = sum(len(p) for p in paragraphs[1:-1]) / max(len(paragraphs) - 2, 1)
        
        if first_para_len < middle_avg_len * 0.5 and last_para_len < middle_avg_len * 0.5:
            return "introduction_body_conclusion"
        
        return "sequential"
    
    def _extract_keywords(self, content: str, title: str) -> List[str]:
        """提取关键词"""
        # 从标题提取
        title_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', title)
        
        # 从内容提取高频词（简化版）
        content_words = re.findall(r'[\u4e00-\u9fa5]{2,4}', content)
        
        # 统计词频
        word_freq = {}
        for word in title_words + content_words:
            if len(word) >= 2:  # 至少2个字
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # 按频率排序
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in sorted_words[:10]]
    
    def _extract_core_information(self, analysis: Dict) -> Dict:
        """提取核心信息用于重写"""
        return {
            "main_topic": analysis["keywords"][:3],
            "key_arguments": analysis["core_points"],
            "supporting_evidence": analysis["data_points"],
            "case_studies": analysis["key_examples"],
            "article_flow": analysis["structure_type"]
        }
    
    def _plan_rewrite_strategy(self, analysis: Dict, depth: str) -> List[str]:
        """制定改写策略"""
        strategies = []
        
        if depth == "light":
            # 轻度改写：语言润色 + 少量结构调整
            strategies.append("language_polish")
            strategies.append("structure_reorg")
            
        elif depth == "medium":
            # 中度改写：+ 视角转换 + 案例替换
            strategies.append("language_polish")
            strategies.append("structure_reorg")
            strategies.append("perspective_shift")
            strategies.append("example_replace")
            
        elif depth == "deep":
            # 深度改写：全部策略
            strategies.append("language_polish")
            strategies.append("structure_reorg")
            strategies.append("perspective_shift")
            strategies.append("example_replace")
            strategies.append("depth_expand")
            strategies.append("opinion_add")
        
        return strategies
    
    async def _execute_rewrite(
        self,
        analysis: Dict,
        extracted_info: Dict,
        strategies: List[str],
        target_platform: str
    ) -> str:
        """
        执行二次创作
        
        这里使用规则-based 的方法，实际生产环境可以调用LLM API
        """
        paragraphs = analysis["paragraphs"]
        
        # 策略1: 结构重组
        if "structure_reorg" in strategies:
            paragraphs = self._reorganize_structure(paragraphs, analysis["structure_type"])
        
        # 策略2: 语言润色（同义词替换、句式变换）
        if "language_polish" in strategies:
            paragraphs = [self._polish_language(p) for p in paragraphs]
        
        # 策略3: 视角转换
        if "perspective_shift" in strategies:
            paragraphs = [self._shift_perspective(p) for p in paragraphs]
        
        # 策略4: 案例替换（添加新案例）
        if "example_replace" in strategies:
            paragraphs = self._replace_examples(paragraphs, extracted_info)
        
        # 策略5: 深度扩展
        if "depth_expand" in strategies:
            paragraphs = self._expand_depth(paragraphs, extracted_info)
        
        # 策略6: 观点补充
        if "opinion_add" in strategies:
            paragraphs = self._add_opinions(paragraphs, extracted_info)
        
        # 组合成完整文章
        rewritten_content = '\n\n'.join(paragraphs)
        
        return rewritten_content
    
    def _reorganize_structure(self, paragraphs: List[str], structure_type: str) -> List[str]:
        """重组文章结构"""
        if len(paragraphs) < 5:
            return paragraphs
        
        # 保持开头和结尾，重新排列中间段落
        first = paragraphs[0]
        last = paragraphs[-1]
        middle = paragraphs[1:-1]
        
        # 反转中间段落顺序（简单的重组方式）
        middle.reverse()
        
        return [first] + middle + [last]
    
    def _polish_language(self, paragraph: str) -> str:
        """语言润色：同义词替换和句式变换"""
        # 简单的同义词替换表
        synonyms = {
            "非常重要": "至关重要",
            "很多": "众多",
            "一些": "若干",
            "好的": "优质的",
            "坏的": "劣质的",
            "提高": "提升",
            "降低": "减少",
            "增加": "增长",
            "减少": "缩减",
            "快速": "迅速",
            "慢慢": "逐渐"
        }
        
        for old_word, new_word in synonyms.items():
            paragraph = paragraph.replace(old_word, new_word)
        
        return paragraph
    
    def _shift_perspective(self, paragraph: str) -> str:
        """视角转换：从第三人称转为第一人称或反之"""
        # 简化实现：添加个人观点引导词
        if "我认为" not in paragraph and "我觉得" not in paragraph:
            # 在段落开头添加视角引导（只对部分段落）
            import random
            if random.random() > 0.7:  # 30%概率添加
                perspective_phrases = [
                    "从我的角度来看，",
                    "笔者认为，",
                    "在我看来，",
                    "个人理解是，"
                ]
                phrase = random.choice(perspective_phrases)
                paragraph = phrase + paragraph
        
        return paragraph
    
    def _replace_examples(self, paragraphs: List[str], extracted_info: Dict) -> List[str]:
        """替换或添加新案例"""
        # 在实际实现中，这里可以调用搜索API获取新案例
        # 现在使用占位符
        
        new_examples = [
            "\n\n【新增案例】以最近的实际情况为例，这一现象在多个领域都有体现...",
            "\n\n【实践验证】根据最新的市场调研数据显示..."
        ]
        
        # 在适当位置插入新案例
        if len(paragraphs) > 3:
            insert_pos = len(paragraphs) // 2
            paragraphs.insert(insert_pos, new_examples[0])
        
        return paragraphs
    
    def _expand_depth(self, paragraphs: List[str], extracted_info: Dict) -> List[str]:
        """深度扩展：添加分析内容"""
        expansion_paragraphs = [
            "\n\n【深度分析】这一现象背后的深层原因值得探讨。首先，从行业发展的角度来看...",
            "\n\n【趋势展望】展望未来，我们可以预见以下几个发展方向..."
        ]
        
        # 在结尾前添加深度分析
        if len(paragraphs) > 2:
            paragraphs.insert(-1, expansion_paragraphs[0])
            paragraphs.insert(-1, expansion_paragraphs[1])
        
        return paragraphs
    
    def _add_opinions(self, paragraphs: List[str], extracted_info: Dict) -> List[str]:
        """补充新观点"""
        new_opinions = [
            "\n\n【个人观点】基于以上分析，我认为关键在于如何平衡各方利益，找到最优解决方案。",
            "\n\n【建议】对于从业者来说，我建议重点关注以下几个方面..."
        ]
        
        # 在适当位置添加观点
        if len(paragraphs) > 4:
            paragraphs.insert(-2, new_opinions[0])
            paragraphs.append(new_opinions[1])
        
        return paragraphs
    
    def _generate_new_title(self, original_title: str, analysis: Dict) -> str:
        """生成新标题"""
        keywords = analysis["keywords"][:3]
        
        # 标题模板
        templates = [
            f"深度解析：{' '.join(keywords)}的核心要点",
            f"{' '.join(keywords)}：你必须知道的几个关键点",
            f"为什么{' '.join(keywords)}如此重要？专家给出答案",
            f"{' '.join(keywords)}的最新发展趋势分析",
            f"揭秘{' '.join(keywords)}背后的真相"
        ]
        
        import random
        new_title = random.choice(templates)
        
        # 确保标题不超过30字
        if len(new_title) > 30:
            new_title = new_title[:27] + "..."
        
        return new_title
    
    def _evaluate_originality(self, original: str, rewritten: str) -> float:
        """
        评估原创度
        
        Returns:
            原创度分数 (0-1)，越高越原创
        """
        # 简化的原创度评估
        original_sentences = set(re.split(r'[。！？\n]', original))
        rewritten_sentences = set(re.split(r'[。！？\n]', rewritten))
        
        # 计算句子重叠率
        common_sentences = original_sentences.intersection(rewritten_sentences)
        
        if len(original_sentences) == 0:
            return 0.5
        
        overlap_rate = len(common_sentences) / len(original_sentences)
        
        # 原创度 = 1 - 重叠率
        originality = 1 - overlap_rate
        
        # 考虑长度变化
        length_ratio = len(rewritten) / max(len(original), 1)
        if length_ratio > 1.2 or length_ratio < 0.8:
            # 长度变化较大，可能是深度改写
            originality = min(1.0, originality + 0.1)
        
        return round(min(1.0, max(0.0, originality)), 2)


# 便捷函数
async def rewrite_hot_article(
    content: str,
    title: str,
    platform: str = "toutiao",
    depth: str = "deep"
) -> Dict:
    """
    便捷函数：对热点文章进行二次创作
    
    Usage:
        result = await rewrite_hot_article(article_content, article_title, "toutiao", "deep")
    """
    rewriter = HotArticleRewriter()
    return await rewriter.rewrite_from_hot_article(content, title, platform, depth)
