"""
图片处理工具
支持图片压缩、格式转换、尺寸调整等功能
"""
import os
from PIL import Image
from typing import Optional, Tuple
from app.utils.logger import logger


class ImageProcessor:
    """图片处理器"""
    
    def __init__(self):
        # 支持的输出格式
        self.supported_formats = {
            'jpg': 'JPEG',
            'jpeg': 'JPEG',
            'png': 'PNG',
            'webp': 'WEBP'
        }
        
    def compress_image(
        self,
        input_path: str,
        output_path: str = None,
        quality: int = 85,
        max_width: int = 1920,
        max_height: int = 1080,
        output_format: str = 'jpg'
    ) -> dict:
        """
        压缩图片
        
        Args:
            input_path: 输入图片路径
            output_path: 输出图片路径（可选，默认在原文件名后加_compressed）
            quality: 压缩质量 (1-100)，默认85
            max_width: 最大宽度，默认1920
            max_height: 最大高度，默认1080
            output_format: 输出格式 (jpg/png/webp)，默认jpg
            
        Returns:
            包含处理结果的字典
        """
        try:
            logger.info(f"开始压缩图片: {input_path}")
            
            # 打开图片
            img = Image.open(input_path)
            
            # 获取原始信息
            original_size = os.path.getsize(input_path)
            original_format = img.format
            original_size_px = img.size
            
            logger.info(f"原始图片: {original_size_px}, 格式: {original_format}, 大小: {original_size/1024:.2f}KB")
            
            # 转换颜色模式（如果需要）
            if output_format.lower() in ['jpg', 'jpeg']:
                # JPEG不支持透明度，需要转换为RGB
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                    logger.info("已转换为RGB模式")
            elif output_format.lower() == 'png':
                # PNG支持透明度
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
            elif output_format.lower() == 'webp':
                # WebP支持透明度和RGB
                if img.mode not in ('RGB', 'RGBA'):
                    img = img.convert('RGB')
            
            # 计算新尺寸（保持宽高比）
            new_size = self._calculate_new_size(
                img.size, 
                max_width, 
                max_height
            )
            
            if new_size != img.size:
                img = img.resize(new_size, Image.LANCZOS)
                logger.info(f"调整尺寸: {img.size}")
            
            # 生成输出路径
            if output_path is None:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}_compressed.{output_format.lower()}"
            
            # 保存压缩后的图片
            save_kwargs = {}
            if output_format.lower() in ['jpg', 'jpeg']:
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            elif output_format.lower() == 'png':
                save_kwargs['optimize'] = True
            elif output_format.lower() == 'webp':
                save_kwargs['quality'] = quality
                save_kwargs['method'] = 6  # 最高压缩率
            
            img.save(output_path, format=self.supported_formats[output_format.lower()], **save_kwargs)
            
            # 获取压缩后信息
            compressed_size = os.path.getsize(output_path)
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            result = {
                "status": "success",
                "input_path": input_path,
                "output_path": output_path,
                "original_size_kb": round(original_size / 1024, 2),
                "compressed_size_kb": round(compressed_size / 1024, 2),
                "compression_ratio_percent": round(compression_ratio, 2),
                "original_dimensions": original_size_px,
                "new_dimensions": img.size,
                "output_format": output_format.lower(),
                "quality": quality
            }
            
            logger.info(f"✅ 图片压缩成功: {result['compression_ratio_percent']}% 压缩率")
            logger.info(f"   原始大小: {result['original_size_kb']}KB -> 压缩后: {result['compressed_size_kb']}KB")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 图片压缩失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def convert_format(
        self,
        input_path: str,
        output_format: str = 'webp',
        output_path: str = None,
        quality: int = 85
    ) -> dict:
        """
        转换图片格式
        
        Args:
            input_path: 输入图片路径
            output_format: 目标格式 (jpg/png/webp)
            output_path: 输出路径（可选）
            quality: 质量 (1-100)
            
        Returns:
            处理结果
        """
        try:
            logger.info(f"开始转换图片格式: {input_path} -> {output_format}")
            
            # 打开图片
            img = Image.open(input_path)
            
            # 生成输出路径
            if output_path is None:
                base_name = os.path.splitext(input_path)[0]
                output_path = f"{base_name}.{output_format.lower()}"
            
            # 转换颜色模式
            if output_format.lower() in ['jpg', 'jpeg']:
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
            elif output_format.lower() == 'png':
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
            
            # 保存
            save_kwargs = {}
            if output_format.lower() in ['jpg', 'jpeg']:
                save_kwargs['quality'] = quality
                save_kwargs['optimize'] = True
            elif output_format.lower() == 'webp':
                save_kwargs['quality'] = quality
            
            img.save(output_path, format=self.supported_formats[output_format.lower()], **save_kwargs)
            
            original_size = os.path.getsize(input_path)
            new_size = os.path.getsize(output_path)
            
            result = {
                "status": "success",
                "input_path": input_path,
                "output_path": output_path,
                "original_format": os.path.splitext(input_path)[1][1:],
                "new_format": output_format.lower(),
                "original_size_kb": round(original_size / 1024, 2),
                "new_size_kb": round(new_size / 1024, 2),
                "size_change_percent": round((1 - new_size / original_size) * 100, 2)
            }
            
            logger.info(f"✅ 格式转换成功: {result['original_format']} -> {result['new_format']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 格式转换失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def resize_image(
        self,
        input_path: str,
        width: int,
        height: int,
        output_path: str = None,
        maintain_aspect_ratio: bool = True
    ) -> dict:
        """
        调整图片尺寸
        
        Args:
            input_path: 输入图片路径
            width: 目标宽度
            height: 目标高度
            output_path: 输出路径（可选）
            maintain_aspect_ratio: 是否保持宽高比
            
        Returns:
            处理结果
        """
        try:
            logger.info(f"开始调整图片尺寸: {input_path} -> {width}x{height}")
            
            img = Image.open(input_path)
            
            if maintain_aspect_ratio:
                # 保持宽高比，使用thumbnail
                img.thumbnail((width, height), Image.LANCZOS)
            else:
                # 不保持宽高比，直接resize
                img = img.resize((width, height), Image.LANCZOS)
            
            # 生成输出路径
            if output_path is None:
                base_name = os.path.splitext(input_path)[0]
                ext = os.path.splitext(input_path)[1]
                output_path = f"{base_name}_{width}x{height}{ext}"
            
            # 保存
            img.save(output_path)
            
            result = {
                "status": "success",
                "input_path": input_path,
                "output_path": output_path,
                "original_dimensions": img.size,
                "new_dimensions": (width, height) if not maintain_aspect_ratio else img.size,
                "maintain_aspect_ratio": maintain_aspect_ratio
            }
            
            logger.info(f"✅ 尺寸调整成功: {result['new_dimensions']}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 尺寸调整失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _calculate_new_size(
        self,
        current_size: Tuple[int, int],
        max_width: int,
        max_height: int
    ) -> Tuple[int, int]:
        """
        计算新的图片尺寸（保持宽高比）
        
        Args:
            current_size: 当前尺寸 (width, height)
            max_width: 最大宽度
            max_height: 最大高度
            
        Returns:
            新尺寸 (width, height)
        """
        width, height = current_size
        
        # 如果已经小于最大尺寸，不需要调整
        if width <= max_width and height <= max_height:
            return current_size
        
        # 计算缩放比例
        ratio_w = max_width / width
        ratio_h = max_height / height
        ratio = min(ratio_w, ratio_h)
        
        new_width = int(width * ratio)
        new_height = int(height * ratio)
        
        return (new_width, new_height)
    
    def get_image_info(self, image_path: str) -> dict:
        """
        获取图片信息
        
        Args:
            image_path: 图片路径
            
        Returns:
            图片信息字典
        """
        try:
            img = Image.open(image_path)
            file_size = os.path.getsize(image_path)
            
            return {
                "status": "success",
                "path": image_path,
                "format": img.format,
                "mode": img.mode,
                "size_kb": round(file_size / 1024, 2),
                "dimensions": img.size,
                "width": img.size[0],
                "height": img.size[1],
                "aspect_ratio": round(img.size[0] / img.size[1], 2)
            }
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e)
            }


# 便捷函数
def compress_and_optimize(
    input_path: str,
    output_path: str = None,
    target_format: str = 'webp',
    quality: int = 85,
    max_width: int = 1920,
    max_height: int = 1080
) -> dict:
    """
    一键压缩和优化图片
    
    Args:
        input_path: 输入路径
        output_path: 输出路径
        target_format: 目标格式
        quality: 质量
        max_width: 最大宽度
        max_height: 最大高度
        
    Returns:
        处理结果
    """
    processor = ImageProcessor()
    
    # 先调整尺寸
    resize_result = processor.resize_image(
        input_path,
        max_width,
        max_height,
        maintain_aspect_ratio=True
    )
    
    if resize_result["status"] != "success":
        return resize_result
    
    # 再压缩和转换格式
    temp_path = resize_result["output_path"]
    compress_result = processor.compress_image(
        temp_path,
        output_path=output_path,
        quality=quality,
        output_format=target_format
    )
    
    # 清理临时文件
    if temp_path != input_path and os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except:
            pass
    
    return compress_result
