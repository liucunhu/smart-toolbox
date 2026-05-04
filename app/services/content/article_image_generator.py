"""
文章配图生成器
根据文章内容自动生成相关配图
"""
import os
import uuid
from PIL import Image, ImageDraw, ImageFont
from typing import List, Dict, Optional
import random


class ArticleImageGenerator:
    """文章配图生成器"""
    
    def __init__(self, output_dir: str = "uploads/article_images"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
    def generate_images_for_article(
        self, 
        title: str, 
        content: str, 
        num_images: int = 2,
        category: str = "科技"
    ) -> List[Dict]:
        """
        为文章生成配图
        
        Args:
            title: 文章标题
            content: 文章内容
            num_images: 生成图片数量
            category: 文章分类
            
        Returns:
            生成的图片信息列表
        """
        images = []
        
        # 根据文章主题生成不同风格的配图
        themes = self._extract_themes(title, content, category)
        
        for i in range(min(num_images, len(themes))):
            theme = themes[i]
            image_info = self._generate_single_image(
                theme=theme,
                index=i + 1,
                total=num_images
            )
            if image_info:
                images.append(image_info)
        
        return images
    
    def _extract_themes(self, title: str, content: str, category: str) -> List[str]:
        """从文章内容中提取主题"""
        themes = []
        
        # 根据分类和标题生成主题
        if "人工智能" in title or "AI" in title:
            themes = [
                "AI技术",
                "机器学习",
                "深度学习应用",
                "未来科技"
            ]
        elif "科技" in category:
            themes = [
                "科技创新",
                "数字化时代",
                "智能未来",
                "技术趋势"
            ]
        else:
            themes = [
                "热门话题",
                "深度分析",
                "行业洞察",
                "趋势展望"
            ]
        
        return themes
    
    def _generate_single_image(
        self, 
        theme: str, 
        index: int, 
        total: int
    ) -> Optional[Dict]:
        """生成单张配图"""
        try:
            # 图片尺寸（头条推荐比例）
            width = 800
            height = 450
            
            # 创建图片
            img = Image.new('RGB', (width, height), color=self._get_background_color(theme))
            draw = ImageDraw.Draw(img)
            
            # 绘制装饰元素
            self._draw_decorations(draw, width, height, theme)
            
            # 添加文字
            self._add_text(draw, theme, width, height)
            
            # 保存图片
            filename = f"article_img_{uuid.uuid4().hex[:8]}.jpg"
            filepath = os.path.join(self.output_dir, filename)
            
            img.save(filepath, 'JPEG', quality=90)
            
            return {
                "file_path": filepath,
                "theme": theme,
                "index": index,
                "size": (width, height)
            }
            
        except Exception as e:
            print(f"   ⚠️  生成配图失败: {e}")
            return None
    
    def _get_background_color(self, theme: str) -> tuple:
        """根据主题获取背景色"""
        colors = {
            "AI技术": (70, 130, 180),      # 钢蓝色
            "机器学习": (100, 149, 237),    # 矢车菊蓝
            "深度学习应用": (65, 105, 225), # 皇家蓝
            "未来科技": (0, 191, 255),      # 深天蓝
            "科技创新": (0, 206, 209),      # 暗青绿色
            "数字化时代": (72, 61, 139),    # 暗蓝紫色
            "智能未来": (25, 25, 112),      # 午夜蓝
            "技术趋势": (0, 128, 128),      # 青色
        }
        return colors.get(theme, (70, 130, 180))
    
    def _draw_decorations(self, draw: ImageDraw, width: int, height: int, theme: str):
        """绘制装饰元素"""
        # 绘制圆形装饰
        for _ in range(5):
            x = random.randint(50, width - 50)
            y = random.randint(50, height - 50)
            radius = random.randint(20, 60)
            color = (255, 255, 255, 50)
            draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color)
        
        # 绘制线条装饰
        for _ in range(3):
            x1 = random.randint(0, width)
            y1 = random.randint(0, height)
            x2 = random.randint(0, width)
            y2 = random.randint(0, height)
            draw.line([(x1, y1), (x2, y2)], fill=(255, 255, 255, 30), width=2)
    
    def _add_text(self, draw: ImageDraw, theme: str, width: int, height: int):
        """添加文字"""
        try:
            # 尝试使用系统字体
            font_size = 48
            try:
                font = ImageFont.truetype("simhei.ttf", font_size)
            except:
                try:
                    font = ImageFont.truetype("msyh.ttc", font_size)
                except:
                    font = ImageFont.load_default()
            
            # 计算文字位置（居中）
            text_bbox = draw.textbbox((0, 0), theme, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            
            # 绘制文字阴影
            shadow_offset = 3
            draw.text((x + shadow_offset, y + shadow_offset), theme, fill=(0, 0, 0, 128), font=font)
            
            # 绘制文字
            draw.text((x, y), theme, fill=(255, 255, 255), font=font)
            
        except Exception as e:
            print(f"   ⚠️  添加文字失败: {e}")
    
    def insert_images_to_content(
        self, 
        content: str, 
        images: List[Dict],
        positions: List[int] = None
    ) -> str:
        """
        将图片插入到文章内容中
        
        Args:
            content: 原始内容
            images: 图片信息列表
            positions: 插入位置（段落索引），None表示均匀分布
            
        Returns:
            包含图片标记的内容
        """
        paragraphs = content.strip().split('\n\n')
        
        if positions is None:
            # 均匀分布插入
            if len(paragraphs) > 1 and len(images) > 0:
                positions = [len(paragraphs) // (len(images) + 1) * (i + 1) 
                            for i in range(len(images))]
                positions = [min(p, len(paragraphs) - 1) for p in positions]
            else:
                positions = []
        
        # 插入图片标记
        new_paragraphs = []
        image_idx = 0
        
        for i, para in enumerate(paragraphs):
            new_paragraphs.append(para)
            
            if i in positions and image_idx < len(images):
                image_path = images[image_idx]['file_path']
                # 使用HTML img标签或Markdown格式
                img_tag = f'\n\n![{images[image_idx]["theme"]}]({image_path})\n\n'
                new_paragraphs.append(img_tag)
                image_idx += 1
        
        return '\n\n'.join(new_paragraphs)


def get_article_image_generator() -> ArticleImageGenerator:
    """获取文章配图生成器实例"""
    return ArticleImageGenerator()
