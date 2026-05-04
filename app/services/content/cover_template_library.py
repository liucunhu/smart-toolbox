"""
封面图模板库
提供多种预设的封面图模板
"""
import os
from typing import Dict, List, Any
from PIL import Image, ImageDraw, ImageFont
import json
from app.utils.logger import logger


class CoverTemplateLibrary:
    """封面图模板库"""
    
    def __init__(self, template_dir: str = "templates/covers"):
        self.template_dir = template_dir
        os.makedirs(template_dir, exist_ok=True)
        
        # 初始化默认模板
        self._init_default_templates()
    
    def _init_default_templates(self):
        """初始化默认模板配置"""
        default_templates = {
            "tech_news": {
                "name": "科技资讯",
                "category": "科技",
                "style": "modern",
                "color_scheme": "科技蓝",
                "layout": "title_center",
                "description": "适合科技类文章，现代风格"
            },
            "finance_report": {
                "name": "财经报道",
                "category": "财经",
                "style": "minimal",
                "color_scheme": "简约黑",
                "layout": "title_left",
                "description": "适合财经类文章，极简风格"
            },
            "entertainment_hot": {
                "name": "娱乐热点",
                "category": "娱乐",
                "style": "bold",
                "color_scheme": "活力橙",
                "layout": "title_bottom",
                "description": "适合娱乐类文章，大胆风格"
            },
            "lifestyle_tips": {
                "name": "生活技巧",
                "category": "生活",
                "style": "modern",
                "color_scheme": "清新绿",
                "layout": "title_center",
                "description": "适合生活类文章，清新风格"
            },
            "education_guide": {
                "name": "教育指南",
                "category": "教育",
                "style": "minimal",
                "color_scheme": "优雅紫",
                "layout": "title_top",
                "description": "适合教育类文章，优雅风格"
            }
        }
        
        # 保存模板配置
        config_path = os.path.join(self.template_dir, "templates_config.json")
        if not os.path.exists(config_path):
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(default_templates, f, ensure_ascii=False, indent=2)
            logger.info(f"✅ 已初始化 {len(default_templates)} 个默认模板")
    
    def get_all_templates(self) -> List[Dict[str, Any]]:
        """获取所有模板"""
        config_path = os.path.join(self.template_dir, "templates_config.json")
        
        if not os.path.exists(config_path):
            return []
        
        with open(config_path, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        result = []
        for template_id, template_info in templates.items():
            result.append({
                "id": template_id,
                **template_info
            })
        
        return result
    
    def get_template_by_category(self, category: str) -> List[Dict[str, Any]]:
        """根据分类获取模板"""
        all_templates = self.get_all_templates()
        return [t for t in all_templates if t.get("category") == category]
    
    def get_template_by_id(self, template_id: str) -> Dict[str, Any]:
        """根据ID获取模板"""
        config_path = os.path.join(self.template_dir, "templates_config.json")
        
        if not os.path.exists(config_path):
            return None
        
        with open(config_path, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        template_info = templates.get(template_id)
        if template_info:
            return {
                "id": template_id,
                **template_info
            }
        return None
    
    def add_custom_template(
        self,
        template_id: str,
        name: str,
        category: str,
        style: str,
        color_scheme: str,
        layout: str,
        description: str = ""
    ) -> bool:
        """添加自定义模板"""
        config_path = os.path.join(self.template_dir, "templates_config.json")
        
        # 读取现有配置
        templates = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                templates = json.load(f)
        
        # 添加新模板
        templates[template_id] = {
            "name": name,
            "category": category,
            "style": style,
            "color_scheme": color_scheme,
            "layout": layout,
            "description": description
        }
        
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(templates, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 已添加自定义模板: {template_id}")
        return True
    
    def delete_template(self, template_id: str) -> bool:
        """删除模板"""
        config_path = os.path.join(self.template_dir, "templates_config.json")
        
        if not os.path.exists(config_path):
            return False
        
        with open(config_path, 'r', encoding='utf-8') as f:
            templates = json.load(f)
        
        if template_id in templates:
            del templates[template_id]
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(templates, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 已删除模板: {template_id}")
            return True
        
        return False
    
    def generate_cover_from_template(
        self,
        template_id: str,
        title: str,
        subtitle: str = "",
        output_dir: str = "uploads/template_covers"
    ) -> Dict[str, Any]:
        """
        使用模板生成封面图
        
        Args:
            template_id: 模板ID
            title: 标题
            subtitle: 副标题
            output_dir: 输出目录
            
        Returns:
            生成结果
        """
        try:
            # 获取模板信息
            template = self.get_template_by_id(template_id)
            if not template:
                return {
                    "status": "failed",
                    "error": f"模板不存在: {template_id}"
                }
            
            # 导入AI封面生成器
            from app.services.content.ai_cover_generator import AICoverGenerator
            
            generator = AICoverGenerator(output_dir=output_dir)
            
            # 使用模板配置生成
            result = generator.generate_cover(
                title=title,
                subtitle=subtitle,
                category=template["category"],
                style=template["style"],
                color_scheme=template["color_scheme"]
            )
            
            if result["status"] == "success":
                result["template_id"] = template_id
                result["template_name"] = template["name"]
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 模板封面图生成失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def batch_generate_covers(
        self,
        articles: List[Dict[str, str]],
        auto_select_template: bool = True
    ) -> List[Dict[str, Any]]:
        """
        批量为文章生成封面图
        
        Args:
            articles: 文章列表，每个包含 title, category
            auto_select_template: 是否自动选择模板
            
        Returns:
            生成结果列表
        """
        results = []
        
        for article in articles:
            title = article.get("title", "")
            category = article.get("category", "科技")
            subtitle = article.get("subtitle", "")
            
            if auto_select_template:
                # 根据分类自动选择模板
                templates = self.get_template_by_category(category)
                if templates:
                    template_id = templates[0]["id"]
                else:
                    # 如果没有匹配的分类，使用第一个模板
                    all_templates = self.get_all_templates()
                    template_id = all_templates[0]["id"] if all_templates else None
            else:
                template_id = article.get("template_id")
            
            if template_id:
                result = self.generate_cover_from_template(
                    template_id=template_id,
                    title=title,
                    subtitle=subtitle
                )
                results.append(result)
        
        return results


# 单例模式
_template_library = None

def get_template_library() -> CoverTemplateLibrary:
    """获取模板库单例"""
    global _template_library
    if _template_library is None:
        _template_library = CoverTemplateLibrary()
    return _template_library
