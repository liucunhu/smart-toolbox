"""
视觉合成服务（增强版）
实现三格拼接封面、高饱和度人物特写封面、Ins风格滤镜
"""
import os
import random
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)


class CoverStyle:
    """封面风格"""
    DOUYIN_THREE_GRID = "douyin_three_grid"  # 抖音三格拼接
    DOUYIN_PORTRAIT = "douyin_portrait"  # 抖音高饱和度人物特写
    XIAOHONGSHU_INS = "xiaohongshu_ins"  # 小红书Ins风格


class VisualSynthesisEngine:
    """视觉合成引擎"""
    
    def __init__(self):
        pass
    
    def generate_three_grid_cover(
        self,
        input_path: str,
        output_path: str,
        title: str = ""
    ) -> Dict[str, Any]:
        """
        生成三格拼接封面（抖音风格）
        
        Args:
            input_path: 输入图片路径
            output_path: 输出路径
            title: 标题文字（可选）
            
        Returns:
            Dict: 生成结果
        """
        try:
            # 加载图片
            img = Image.open(input_path)
            
            # 三格布局：左中右
            w, h = img.size
            
            # 计算每格的宽度
            grid_width = w // 3
            
            # 创建三格封面
            cover = Image.new('RGB', (w, h), color=(255, 255, 255))
            
            # 左格：原图裁剪
            left = img.crop((0, 0, grid_width, h))
            left = left.resize((grid_width, h), Image.Resampling.LANCZOS)
            cover.paste(left, (0, 0))
            
            # 中格：原图裁剪（带小偏移）
            middle = img.crop((grid_width, 0, grid_width * 2, h))
            middle = middle.resize((grid_width, h), Image.Resampling.LANCZOS)
            cover.paste(middle, (grid_width, 0))
            
            # 右格：原图裁剪
            right = img.crop((grid_width * 2, 0, w, h))
            right = right.resize((grid_width, h), Image.Resampling.LANCZOS)
            cover.paste(right, (grid_width * 2, 0))
            
            # 添加分隔线
            draw = ImageDraw.Draw(cover)
            for i in range(1, 3):
                x = i * grid_width
                draw.line([(x, 0), (x, h)], fill=(0, 0, 0), width=2)
            
            # 添加标题
            if title:
                self._add_title_to_cover(cover, title, style="bottom")
            
            # 保存
            cover.save(output_path, quality=95)
            
            logger.info(f"✅ 三格拼接封面生成成功: {output_path}")
            return {
                "success": True,
                "output_path": output_path,
                "style": CoverStyle.DOUYIN_THREE_GRID,
                "dimensions": cover.size
            }
            
        except Exception as e:
            logger.error(f"生成三格拼接封面失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_portrait_cover(
        self,
        input_path: str,
        output_path: str,
        title: str = ""
    ) -> Dict[str, Any]:
        """
        生成高饱和度人物特写封面（抖音风格）
        
        Args:
            input_path: 输入图片路径
            output_path: 输出路径
            title: 标题文字
            
        Returns:
            Dict: 生成结果
        """
        try:
            # 加载图片
            img = Image.open(input_path)
            
            # 调整为竖屏9:16
            cover = self._adjust_aspect_ratio(img, 9, 16)
            
            # 提高饱和度
            cover = self._enhance_saturation(cover, factor=1.5)
            
            # 提高对比度
            cover = self._enhance_contrast(cover, factor=1.2)
            
            # 人物特写裁剪（中心裁剪）
            cover = self._crop_center_portrait(cover)
            
            # 添加标题
            if title:
                self._add_title_to_cover(cover, title, style="center")
            
            # 保存
            cover.save(output_path, quality=95)
            
            logger.info(f"✅ 人物特写封面生成成功: {output_path}")
            return {
                "success": True,
                "output_path": output_path,
                "style": CoverStyle.DOUYIN_PORTRAIT,
                "dimensions": cover.size
            }
            
        except Exception as e:
            logger.error(f"生成人物特写封面失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_ins_style_cover(
        self,
        input_path: str,
        output_path: str,
        title: str = ""
    ) -> Dict[str, Any]:
        """
        生成Ins风格封面（小红书风格）
        
        Args:
            input_path: 输入图片路径
            output_path: 输出路径
            title: 标题文字
            
        Returns:
            Dict: 生成结果
        """
        try:
            # 加载图片
            img = Image.open(input_path)
            
            # 调整为3:4竖屏
            cover = self._adjust_aspect_ratio(img, 3, 4)
            
            # 应用Ins风格滤镜
            cover = self._apply_ins_filter(cover)
            
            # 添加标题
            if title:
                self._add_title_to_cover(cover, title, style="ins")
            
            # 保存
            cover.save(output_path, quality=95)
            
            logger.info(f"✅ Ins风格封面生成成功: {output_path}")
            return {
                "success": True,
                "output_path": output_path,
                "style": CoverStyle.XIAOHONGSHU_INS,
                "dimensions": cover.size
            }
            
        except Exception as e:
            logger.error(f"生成Ins风格封面失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _adjust_aspect_ratio(
        self,
        img: Image.Image,
        target_ratio_w: int,
        target_ratio_h: int
    ) -> Image.Image:
        """
        调整宽高比
        
        Args:
            img: 图片对象
            target_ratio_w: 目标宽高比分子
            target_ratio_h: 目标宽高比分母
            
        Returns:
            Image.Image: 调整后的图片
        """
        w, h = img.size
        current_ratio = w / h
        target_ratio = target_ratio_w / target_ratio_h
        
        if current_ratio > target_ratio:
            # 太宽，裁剪宽度
            new_w = int(h * target_ratio)
            x_offset = (w - new_w) // 2
            img = img.crop((x_offset, 0, x_offset + new_w, h))
        else:
            # 太高，裁剪高度
            new_h = int(w / target_ratio)
            y_offset = (h - new_h) // 2
            img = img.crop((0, y_offset, w, y_offset + new_h))
        
        return img
    
    def _enhance_saturation(
        self,
        img: Image.Image,
        factor: float = 1.3
    ) -> Image.Image:
        """
        增强饱和度
        
        Args:
            img: 图片对象
            factor: 饱和度因子
            
        Returns:
            Image.Image: 增强后的图片
        """
        from PIL import ImageEnhance
        
        enhancer = ImageEnhance.Color(img)
        return enhancer.enhance(factor)
    
    def _enhance_contrast(
        self,
        img: Image.Image,
        factor: float = 1.2
    ) -> Image.Image:
        """
        增强对比度
        
        Args:
            img: 图片对象
            factor: 对比度因子
            
        Returns:
            Image.Image: 增强后的图片
        """
        from PIL import ImageEnhance
        
        enhancer = ImageEnhance.Contrast(img)
        return enhancer.enhance(factor)
    
    def _crop_center_portrait(
        self,
        img: Image.Image
    ) -> Image.Image:
        """
        中心裁剪为人物特写
        
        Args:
            img: 图片对象
            
        Returns:
            Image.Image: 裁剪后的图片
        """
        w, h = img.size
        
        # 人物特写：裁剪中心60%区域
        crop_width = int(w * 0.6)
        crop_height = int(h * 0.6)
        
        x_offset = (w - crop_width) // 2
        y_offset = (h - crop_height) // 2
        
        return img.crop((x_offset, y_offset, x_offset + crop_width, y_offset + crop_height))
    
    def _apply_ins_filter(
        self,
        img: Image.Image
    ) -> Image.Image:
        """
        应用Ins风格滤镜
        
        Args:
            img: 图片对象
            
        Returns:
            Image.Image: 滤镜后的图片
        """
        # 转换为OpenCV格式
        cv_img = np.array(img)
        cv_img = cv2.cvtColor(cv_img, cv2.COLOR_RGB2BGR)
        
        # 1. 轻微降低饱和度
        hsv = cv2.cvtColor(cv_img, cv2.COLOR_BGR2HSV)
        hsv[:, :, 1] = hsv[:, :, 1] * 0.9  # 降低饱和度
        cv_img = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
        
        # 2. 添加轻微暖色调
        cv_img[:, :, 0] = cv_img[:, :, 0] * 1.05  # 红色通道增强
        cv_img[:, :, 2] = cv_img[:, :, 2] * 0.95  # 蓝色通道降低
        
        # 3. 轻微锐化
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        cv_img = cv2.filter2D(cv_img, -1, kernel)
        
        # 4. 转回PIL格式
        img = Image.fromarray(cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB))
        
        return img
    
    def _add_title_to_cover(
        self,
        img: Image.Image,
        title: str,
        style: str = "center"
    ):
        """
        添加标题到封面
        
        Args:
            img: 图片对象
            title: 标题文字
            style: 风格（center/bottom/ins）
        """
        draw = ImageDraw.Draw(img)
        w, h = img.size
        
        # 字体大小
        font_size = max(20, int(w * 0.08))
        
        try:
            font = ImageFont.truetype("arialbd.ttf", font_size)
        except:
            font = ImageFont.load_default()
        
        # 计算文本位置
        text_bbox = draw.textbbox((0, 0), title, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        
        if style == "center":
            # 居中显示
            x = (w - text_w) // 2
            y = (h - text_h) // 2
            
            # 绘制文字阴影
            shadow_offset = 2
            draw.text((x + shadow_offset, y + shadow_offset), title, 
                   font=font, fill=(0, 0, 0))
            
            # 绘制主文字
            draw.text((x, y), title, font=font, fill=(255, 255, 255))
            
        elif style == "bottom":
            # 底部显示
            x = (w - text_w) // 2
            y = h - text_h - 20
            
            # 绘制背景框
            padding = 10
            draw.rectangle([x - padding, y - padding,
                          x + text_w + padding, y + text_h + padding],
                         fill=(0, 0, 0, 180))
            
            # 绘制文字
            draw.text((x, y), title, font=font, fill=(255, 255, 255))
            
        elif style == "ins":
            # Ins风格：顶部显示，使用大字
            font_size = int(w * 0.12)
            try:
                font = ImageFont.truetype("arialbd.ttf", font_size)
            except:
                font = ImageFont.load_default()
            
            x = 20
            y = 20
            
            # 绘制半透明背景
            padding = 15
            bg_img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
            bg_draw = ImageDraw.Draw(bg_img)
            bg_draw.rectangle([x, y, x + text_w + padding * 2, y + text_h + padding * 2],
                          fill=(0, 0, 0, 100))
            
            # 合成背景
            img = Image.alpha_composite(img.convert('RGBA'), bg_img).convert('RGB')
            draw = ImageDraw.Draw(img)
            
            # 绘制文字
            draw.text((x + padding, y + padding), title, font=font, fill=(255, 255, 255))
    
    def batch_generate_covers(
        self,
        input_paths: List[str],
        output_dir: str,
        style: CoverStyle = CoverStyle.DOUYIN_PORTRAIT,
        titles: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量生成封面
        
        Args:
            input_paths: 输入图片路径列表
            output_dir: 输出目录
            style: 封面风格
            titles: 标题列表
            
        Returns:
            List[Dict]: 生成结果列表
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i, input_path in enumerate(input_paths):
            try:
                # 生成输出路径
                input_path_obj = Path(input_path)
                output_filename = f"{input_path_obj.stem}_{style.value}{input_path_obj.suffix}"
                output_path = os.path.join(output_dir, output_filename)
                
                # 选择标题
                title = titles[i] if titles and i < len(titles) else ""
                
                # 根据风格生成封面
                if style == CoverStyle.DOUYIN_THREE_GRID:
                    result = self.generate_three_grid_cover(input_path, output_path, title)
                elif style == CoverStyle.DOUYIN_PORTRAIT:
                    result = self.generate_portrait_cover(input_path, output_path, title)
                elif style == CoverStyle.XIAOHONGSHU_INS:
                    result = self.generate_ins_style_cover(input_path, output_path, title)
                else:
                    result = {
                        "success": False,
                        "error": f"不支持的风格: {style}"
                    }
                
                results.append(result)
                
            except Exception as e:
                logger.error(f"处理 {input_path} 失败: {e}")
                results.append({
                    "success": False,
                    "input_path": input_path,
                    "error": str(e)
                })
        
        success_count = sum(1 for r in results if r.get("success"))
        logger.info(f"✅ 批量生成封面完成: {success_count}/{len(input_paths)} 成功")
        
        return results


# 创建全局视觉合成引擎实例
_visual_synthesis_engine = None


def get_visual_synthesis_engine() -> VisualSynthesisEngine:
    """
    获取视觉合成引擎实例（单例模式）
    
    Returns:
        VisualSynthesisEngine: 视觉合成引擎实例
    """
    global _visual_synthesis_engine
    if _visual_synthesis_engine is None:
        _visual_synthesis_engine = VisualSynthesisEngine()
    return _visual_synthesis_engine
