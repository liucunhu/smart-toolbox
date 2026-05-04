"""
智能封面图自动生成服务
根据文章标题、内容和分类自动生成多种风格的封面图
"""
import os
import asyncio
from typing import List, Dict, Any, Optional
from app.services.content.ai_cover_generator import AICoverGenerator
from app.services.content.cover_template_library import get_template_library
from app.utils.image_processor import ImageProcessor
from app.utils.logger import logger


class SmartCoverGenerator:
    """智能封面图生成服务"""
    
    def __init__(self):
        self.ai_generator = AICoverGenerator()
        self.template_library = get_template_library()
        self.image_processor = ImageProcessor()
    
    async def generate_smart_cover(
        self,
        title: str,
        content: str = "",
        category: str = "科技",
        tags: List[str] = None,
        prefer_style: str = None,
        generate_count: int = 3
    ) -> Dict[str, Any]:
        """
        智能生成封面图
        
        Args:
            title: 文章标题
            content: 文章内容（用于提取关键词）
            category: 文章分类
            tags: 标签列表
            prefer_style: 偏好风格 (modern/minimal/bold)
            generate_count: 生成数量（默认3个）
            
        Returns:
            最佳封面图信息
        """
        logger.info(f"🎨 开始智能生成封面图: {title}")
        
        try:
            # 步骤1: 分析文章内容，提取关键词
            keywords = self._extract_keywords(title, content, tags)
            logger.info(f"   提取关键词: {keywords}")
            
            # 步骤2: 确定最佳配色方案
            color_scheme = self._select_color_scheme(category, keywords)
            logger.info(f"   选择配色: {color_scheme}")
            
            # 步骤3: 确定最佳风格
            style = prefer_style or self._select_style(category, keywords)
            logger.info(f"   选择风格: {style}")
            
            # 步骤4: 生成多个版本的封面图
            covers = []
            styles_to_try = [style]
            
            # 添加备选风格
            all_styles = ["modern", "minimal", "bold"]
            for s in all_styles:
                if s != style and len(styles_to_try) < generate_count:
                    styles_to_try.append(s)
            
            for i, cover_style in enumerate(styles_to_try[:generate_count]):
                logger.info(f"   生成第 {i+1} 个版本 ({cover_style} 风格)...")
                
                result = self.ai_generator.generate_cover(
                    title=title,
                    subtitle=self._generate_subtitle(content),
                    category=category,
                    style=cover_style,
                    color_scheme=color_scheme if i == 0 else None  # 第一个使用选定配色，其他随机
                )
                
                if result["status"] == "success":
                    # 压缩优化图片
                    optimized = self._optimize_image(result["file_path"])
                    if optimized:
                        result["file_path"] = optimized
                        result["optimized"] = True
                    
                    result["version"] = i + 1
                    result["score"] = self._calculate_score(result, category, style)
                    covers.append(result)
            
            if not covers:
                return {
                    "status": "failed",
                    "error": "所有封面图生成都失败了"
                }
            
            # 步骤5: 选择最佳封面
            best_cover = max(covers, key=lambda x: x.get("score", 0))
            
            logger.info(f"✅ 智能封面生成完成！")
            logger.info(f"   生成了 {len(covers)} 个版本")
            logger.info(f"   最佳评分: {best_cover['score']}")
            logger.info(f"   最佳风格: {best_cover['style']}")
            logger.info(f"   文件路径: {best_cover['file_path']}")
            
            return {
                "status": "success",
                "best_cover": best_cover,
                "all_covers": covers,
                "total_generated": len(covers)
            }
            
        except Exception as e:
            logger.error(f"❌ 智能封面生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _extract_keywords(self, title: str, content: str, tags: List[str] = None) -> List[str]:
        """从标题和内容中提取关键词"""
        keywords = []
        
        # 从标题提取
        if title:
            # 简单分词（按空格和常见标点）
            words = title.replace(',', ' ').replace('，', ' ').replace('、', ' ').split()
            keywords.extend([w for w in words if len(w) > 1])
        
        # 从标签提取
        if tags:
            keywords.extend(tags[:5])  # 最多5个标签
        
        # 去重
        keywords = list(dict.fromkeys(keywords))
        
        return keywords[:10]  # 最多10个关键词
    
    def _select_color_scheme(self, category: str, keywords: List[str]) -> str:
        """根据分类和关键词选择配色方案"""
        # 分类到配色的映射
        category_colors = {
            "科技": "科技蓝",
            "财经": "简约黑",
            "娱乐": "活力橙",
            "生活": "清新绿",
            "教育": "优雅紫",
            "健康": "清新绿",
            "体育": "活力橙",
            "汽车": "科技蓝",
            "房产": "简约黑",
            "美食": "活力橙"
        }
        
        # 优先使用分类对应的配色
        if category in category_colors:
            return category_colors[category]
        
        # 根据关键词选择
        keyword_colors = {
            "AI": "科技蓝",
            "人工智能": "科技蓝",
            "技术": "科技蓝",
            "互联网": "科技蓝",
            "投资": "简约黑",
            "股票": "简约黑",
            "电影": "活力橙",
            "音乐": "活力橙",
            "旅游": "清新绿",
            "健身": "清新绿"
        }
        
        for keyword in keywords:
            if keyword in keyword_colors:
                return keyword_colors[keyword]
        
        # 默认返回科技蓝
        return "科技蓝"
    
    def _select_style(self, category: str, keywords: List[str]) -> str:
        """根据分类和关键词选择风格"""
        # 分类到风格的映射
        category_styles = {
            "科技": "modern",
            "财经": "minimal",
            "娱乐": "bold",
            "生活": "modern",
            "教育": "minimal",
            "健康": "modern",
            "体育": "bold",
            "汽车": "modern",
            "房产": "minimal",
            "美食": "bold"
        }
        
        if category in category_styles:
            return category_styles[category]
        
        # 默认现代风格
        return "modern"
    
    def _generate_subtitle(self, content: str, max_length: int = 50) -> str:
        """从内容中生成副标题"""
        if not content:
            return ""
        
        # 取第一段的前50个字符
        first_paragraph = content.split('\n')[0]
        if len(first_paragraph) <= max_length:
            return first_paragraph
        
        # 截取并添加省略号
        return first_paragraph[:max_length-3] + "..."
    
    def _optimize_image(self, image_path: str) -> Optional[str]:
        """优化图片（压缩和格式转换）"""
        try:
            result = self.image_processor.compress_image(
                input_path=image_path,
                quality=85,
                max_width=1280,
                max_height=720,
                output_format='jpg'
            )
            
            if result["status"] == "success":
                logger.info(f"   ✅ 图片优化完成: {result['compression_ratio_percent']}% 压缩率")
                return result["output_path"]
            else:
                logger.warning(f"   ⚠️  图片优化失败: {result.get('error')}")
                return image_path
                
        except Exception as e:
            logger.warning(f"   ⚠️  图片优化异常: {e}")
            return image_path
    
    def _calculate_score(
        self,
        cover: Dict[str, Any],
        category: str,
        preferred_style: str
    ) -> float:
        """计算封面图评分"""
        score = 0.0
        
        # 风格匹配度（40分）
        if cover["style"] == preferred_style:
            score += 40
        else:
            score += 20
        
        # 文件大小合理性（30分）
        size_kb = cover.get("size_kb", 0)
        if 100 <= size_kb <= 500:  # 理想大小
            score += 30
        elif 50 <= size_kb <= 1000:  # 可接受范围
            score += 20
        else:
            score += 10
        
        # 配色方案（20分）
        expected_color = self._select_color_scheme(category, [])
        if cover.get("color_scheme") == expected_color:
            score += 20
        else:
            score += 10
        
        # 是否优化过（10分）
        if cover.get("optimized"):
            score += 10
        
        return score
    
    async def generate_from_template(
        self,
        title: str,
        category: str = "科技",
        template_id: str = None
    ) -> Dict[str, Any]:
        """
        使用模板生成封面图
        
        Args:
            title: 文章标题
            category: 文章分类
            template_id: 模板ID（可选，自动选择）
            
        Returns:
            生成的封面图信息
        """
        logger.info(f"📋 使用模板生成封面图: {title}")
        
        try:
            # 如果没有指定模板，根据分类自动选择
            if not template_id:
                template_id = self._select_template_by_category(category)
                logger.info(f"   自动选择模板: {template_id}")
            
            # 使用模板库生成
            result = self.template_library.generate_cover_from_template(
                template_id=template_id,
                title=title,
                subtitle=""
            )
            
            if result["status"] == "success":
                # 优化图片
                optimized = self._optimize_image(result["file_path"])
                if optimized:
                    result["file_path"] = optimized
                    result["optimized"] = True
                
                logger.info(f"✅ 模板封面生成成功: {result['template_name']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 模板封面生成失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _select_template_by_category(self, category: str) -> str:
        """根据分类选择模板"""
        # 分类到模板的映射
        category_templates = {
            "科技": "tech_news",
            "财经": "finance_report",
            "娱乐": "entertainment",
            "生活": "lifestyle",
            "教育": "education",
            "健康": "health",
            "体育": "sports",
            "汽车": "automotive",
            "房产": "realestate",
            "美食": "food"
        }
        
        return category_templates.get(category, "tech_news")
    
    async def batch_generate(
        self,
        articles: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        批量生成封面图
        
        Args:
            articles: 文章列表，每个文章包含 title, content, category, tags
            
        Returns:
            生成结果列表
        """
        logger.info(f"🚀 开始批量生成 {len(articles)} 个封面图...")
        
        results = []
        
        for i, article in enumerate(articles, 1):
            logger.info(f"\n[{i}/{len(articles)}] 处理: {article['title']}")
            
            result = await self.generate_smart_cover(
                title=article["title"],
                content=article.get("content", ""),
                category=article.get("category", "科技"),
                tags=article.get("tags", [])
            )
            
            results.append({
                "article_title": article["title"],
                "cover_result": result
            })
        
        success_count = sum(1 for r in results if r["cover_result"]["status"] == "success")
        logger.info(f"\n✅ 批量生成完成！成功: {success_count}/{len(articles)}")
        
        return results


# 全局单例
_smart_cover_generator = None

def get_smart_cover_generator() -> SmartCoverGenerator:
    """获取智能封面生成器单例"""
    global _smart_cover_generator
    if _smart_cover_generator is None:
        _smart_cover_generator = SmartCoverGenerator()
    return _smart_cover_generator
