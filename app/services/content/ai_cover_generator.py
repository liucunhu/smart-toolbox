"""
AI智能封面图生成器
根据文章标题和内容自动生成吸引人的封面图
"""
import os
from typing import Optional, Dict, Any
from PIL import Image, ImageDraw, ImageFont
import random
from app.utils.logger import logger


class AICoverGenerator:
    """AI智能封面图生成器"""
    
    def __init__(self, output_dir: str = "uploads/ai_covers"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 头条封面规格 (16:9)
        self.cover_width = 1280
        self.cover_height = 720
        
        # 配色方案
        self.color_schemes = [
            {
                "name": "科技蓝",
                "background": (15, 32, 39),
                "primary": (32, 156, 238),
                "secondary": (0, 212, 255),
                "text": (255, 255, 255)
            },
            {
                "name": "活力橙",
                "background": (255, 107, 53),
                "primary": (255, 159, 67),
                "secondary": (255, 202, 40),
                "text": (255, 255, 255)
            },
            {
                "name": "清新绿",
                "background": (0, 184, 148),
                "primary": (85, 239, 196),
                "secondary": (253, 203, 110),
                "text": (255, 255, 255)
            },
            {
                "name": "优雅紫",
                "background": (108, 92, 231),
                "primary": (162, 155, 254),
                "secondary": (253, 121, 168),
                "text": (255, 255, 255)
            },
            {
                "name": "简约黑",
                "background": (45, 52, 54),
                "primary": (99, 110, 114),
                "secondary": (223, 230, 233),
                "text": (255, 255, 255)
            }
        ]
        
        # 字体路径（使用系统默认字体）
        self.font_paths = {
            "title": self._get_font_path(),
            "subtitle": self._get_font_path(size=36)
        }
    
    def _get_font_path(self, size: int = 48) -> str:
        """获取字体路径"""
        # Windows系统字体路径
        font_candidates = [
            f"C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
            f"C:/Windows/Fonts/simhei.ttf",  # 黑体
            f"C:/Windows/Fonts/simsun.ttc",  # 宋体
        ]
        
        for font_path in font_candidates:
            if os.path.exists(font_path):
                try:
                    return ImageFont.truetype(font_path, size)
                except:
                    continue
        
        # 如果都失败，使用默认字体
        return ImageFont.load_default()
    
    def generate_cover(
        self,
        title: str,
        subtitle: str = "",
        category: str = "科技",
        style: str = "modern",
        color_scheme: str = None
    ) -> Dict[str, Any]:
        """
        生成封面图
        
        Args:
            title: 文章标题
            subtitle: 副标题（可选）
            category: 文章分类
            style: 风格 (modern/minimal/bold)
            color_scheme: 配色方案名称（可选，随机选择）
            
        Returns:
            生成结果
        """
        try:
            logger.info(f"开始生成AI封面图: {title}")
            
            # 选择配色方案
            if color_scheme:
                scheme = next(
                    (s for s in self.color_schemes if s["name"] == color_scheme),
                    self.color_schemes[0]
                )
            else:
                scheme = random.choice(self.color_schemes)
            
            logger.info(f"使用配色方案: {scheme['name']}")
            
            # 创建画布
            img = Image.new('RGB', (self.cover_width, self.cover_height), scheme["background"])
            draw = ImageDraw.Draw(img)
            
            # 根据风格绘制
            if style == "modern":
                self._draw_modern_style(draw, scheme, title, subtitle, category)
            elif style == "minimal":
                self._draw_minimal_style(draw, scheme, title, subtitle, category)
            elif style == "bold":
                self._draw_bold_style(draw, scheme, title, subtitle, category)
            else:
                self._draw_modern_style(draw, scheme, title, subtitle, category)
            
            # 保存文件
            filename = f"ai_cover_{title[:20].replace(' ', '_')}_{random.randint(1000, 9999)}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            
            img.save(filepath, 'JPEG', quality=90, optimize=True)
            
            result = {
                "status": "success",
                "file_path": filepath,
                "filename": filename,
                "title": title,
                "style": style,
                "color_scheme": scheme["name"],
                "dimensions": (self.cover_width, self.cover_height),
                "size_kb": round(os.path.getsize(filepath) / 1024, 2)
            }
            
            logger.info(f"✅ AI封面图生成成功: {filepath}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ AI封面图生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _draw_modern_style(
        self,
        draw: ImageDraw.ImageDraw,
        scheme: dict,
        title: str,
        subtitle: str,
        category: str
    ):
        """现代风格"""
        # 绘制渐变背景效果（简化版：添加色块）
        draw.rectangle(
            [0, 0, self.cover_width, self.cover_height],
            fill=scheme["background"]
        )
        
        # 添加装饰性图形
        draw.rectangle(
            [50, 50, 200, 200],
            fill=scheme["primary"],
            outline=None
        )
        
        draw.ellipse(
            [self.cover_width - 250, 50, self.cover_width - 50, 250],
            fill=scheme["secondary"],
            outline=None
        )
        
        # 绘制标题
        title_font = self.font_paths["title"]
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        
        # 居中显示标题
        title_x = (self.cover_width - title_width) // 2
        title_y = 280
        
        # 添加文字阴影效果
        shadow_offset = 3
        draw.text(
            (title_x + shadow_offset, title_y + shadow_offset),
            title,
            font=title_font,
            fill=(0, 0, 0, 128)
        )
        
        # 绘制主标题
        draw.text(
            (title_x, title_y),
            title,
            font=title_font,
            fill=scheme["text"]
        )
        
        # 绘制副标题
        if subtitle:
            subtitle_font = self.font_paths["subtitle"]
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (self.cover_width - subtitle_width) // 2
            subtitle_y = title_y + 80
            
            draw.text(
                (subtitle_x, subtitle_y),
                subtitle,
                font=subtitle_font,
                fill=scheme["secondary"]
            )
        
        # 绘制分类标签
        tag_text = f"# {category}"
        tag_font = ImageFont.load_default()
        tag_bbox = draw.textbbox((0, 0), tag_text, font=tag_font)
        tag_width = tag_bbox[2] - tag_bbox[0]
        tag_height = tag_bbox[3] - tag_bbox[1]
        
        tag_x = 50
        tag_y = self.cover_height - 80
        
        # 标签背景
        draw.rounded_rectangle(
            [tag_x - 10, tag_y - 10, tag_x + tag_width + 10, tag_y + tag_height + 10],
            radius=10,
            fill=scheme["primary"]
        )
        
        # 标签文字
        draw.text(
            (tag_x, tag_y),
            tag_text,
            font=tag_font,
            fill=scheme["text"]
        )
    
    def _draw_minimal_style(
        self,
        draw: ImageDraw.ImageDraw,
        scheme: dict,
        title: str,
        subtitle: str,
        category: str
    ):
        """极简风格"""
        # 纯色背景
        draw.rectangle(
            [0, 0, self.cover_width, self.cover_height],
            fill=scheme["background"]
        )
        
        # 绘制标题（大号字体，居中）
        title_font = self.font_paths["title"]
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        
        title_x = (self.cover_width - title_width) // 2
        title_y = (self.cover_height - 100) // 2
        
        draw.text(
            (title_x, title_y),
            title,
            font=title_font,
            fill=scheme["text"]
        )
        
        # 底部细线装饰
        line_y = title_y + 120
        draw.line(
            [(self.cover_width // 2 - 100, line_y), (self.cover_width // 2 + 100, line_y)],
            fill=scheme["primary"],
            width=3
        )
        
        # 分类文字
        if category:
            cat_font = ImageFont.load_default()
            cat_text = category.upper()
            cat_bbox = draw.textbbox((0, 0), cat_text, font=cat_font)
            cat_width = cat_bbox[2] - cat_bbox[0]
            
            draw.text(
                ((self.cover_width - cat_width) // 2, line_y + 20),
                cat_text,
                font=cat_font,
                fill=scheme["secondary"]
            )
    
    def _draw_bold_style(
        self,
        draw: ImageDraw.ImageDraw,
        scheme: dict,
        title: str,
        subtitle: str,
        category: str
    ):
        """大胆风格"""
        # 渐变背景（简化为对角线分割）
        draw.rectangle(
            [0, 0, self.cover_width, self.cover_height],
            fill=scheme["background"]
        )
        
        # 对角线色块
        points = [
            (0, 0),
            (self.cover_width, 0),
            (0, self.cover_height)
        ]
        draw.polygon(points, fill=scheme["primary"])
        
        # 绘制标题（左对齐，超大字体）
        title_font = self.font_paths["title"]
        title_x = 80
        title_y = 250
        
        # 文字描边效果
        for offset_x in [-2, -1, 0, 1, 2]:
            for offset_y in [-2, -1, 0, 1, 2]:
                if offset_x != 0 or offset_y != 0:
                    draw.text(
                        (title_x + offset_x, title_y + offset_y),
                        title,
                        font=title_font,
                        fill=(0, 0, 0, 100)
                    )
        
        # 主标题
        draw.text(
            (title_x, title_y),
            title,
            font=title_font,
            fill=scheme["text"]
        )
        
        # 副标题
        if subtitle:
            subtitle_font = self.font_paths["subtitle"]
            draw.text(
                (title_x, title_y + 90),
                subtitle,
                font=subtitle_font,
                fill=scheme["secondary"]
            )
        
        # 右下角分类标签
        if category:
            tag_font = ImageFont.load_default()
            tag_text = category
            tag_bbox = draw.textbbox((0, 0), tag_text, font=tag_font)
            tag_width = tag_bbox[2] - tag_bbox[0]
            
            tag_x = self.cover_width - tag_width - 50
            tag_y = self.cover_height - 60
            
            draw.text(
                (tag_x, tag_y),
                tag_text,
                font=tag_font,
                fill=scheme["text"]
            )
    
    def generate_multiple_covers(
        self,
        title: str,
        subtitle: str = "",
        category: str = "科技",
        count: int = 3
    ) -> list:
        """
        生成多个不同风格的封面图
        
        Args:
            title: 标题
            subtitle: 副标题
            category: 分类
            count: 生成数量
            
        Returns:
            封面图列表
        """
        styles = ["modern", "minimal", "bold"]
        results = []
        
        for i in range(count):
            style = styles[i % len(styles)]
            result = self.generate_cover(
                title=title,
                subtitle=subtitle,
                category=category,
                style=style
            )
            
            if result["status"] == "success":
                results.append(result)
        
        return results


# 便捷函数
def generate_ai_cover(
    title: str,
    subtitle: str = "",
    category: str = "科技",
    style: str = "modern"
) -> Dict[str, Any]:
    """快速生成AI封面图"""
    generator = AICoverGenerator()
    return generator.generate_cover(title, subtitle, category, style)
