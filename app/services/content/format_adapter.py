"""
格式自适应转换服务
实现多平台视频格式自动转换
"""
import os
import subprocess
import logging
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from moviepy.editor import VideoFileClip

logger = logging.getLogger(__name__)


class PlatformFormat(Enum):
    """平台格式规范"""
    
    # 抖音/快手/视频号 - 9:16 竖屏
    DOUYIN = {
        "aspect_ratio": "9:16",
        "resolution": (1080, 1920),
        "fps": 30,
        "codec": "libx264",
        "bitrate": "6000k",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
        "max_duration": 15 * 60,  # 15分钟
        "min_duration": 3,
        "format": "mp4"
    }
    
    KUAISHOU = {
        "aspect_ratio": "9:16",
        "resolution": (1080, 1920),
        "fps": 30,
        "codec": "libx264",
        "bitrate": "6000k",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
        "max_duration": 10 * 60,
        "min_duration": 3,
        "format": "mp4"
    }
    
    WECHAT = {
        "aspect_ratio": "9:16",
        "resolution": (1080, 1920),
        "fps": 30,
        "codec": "libx264",
        "bitrate": "6000k",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
        "max_duration": 30 * 60,
        "min_duration": 5,
        "format": "mp4"
    }
    
    # B站/西瓜视频 - 16:9 横屏
    BILIBILI = {
        "aspect_ratio": "16:9",
        "resolution": (1920, 1080),
        "fps": 60,
        "codec": "libx264",
        "bitrate": "8000k",
        "audio_codec": "aac",
        "audio_bitrate": "192k",
        "max_duration": 4 * 60 * 60,  # 4小时
        "min_duration": 10,
        "format": "mp4",
        "support_4k": True
    }
    
    XIGUA = {
        "aspect_ratio": "16:9",
        "resolution": (1920, 1080),
        "fps": 60,
        "codec": "libx264",
        "bitrate": "8000k",
        "audio_codec": "aac",
        "audio_bitrate": "192k",
        "max_duration": 4 * 60 * 60,
        "min_duration": 10,
        "format": "mp4",
        "support_4k": True
    }
    
    # 小红书 - 3:4 图文或 9:16 视频
    XIAOHONGSHU_IMAGE = {
        "aspect_ratio": "3:4",
        "resolution": (1080, 1440),
        "format": "jpg",
        "max_size": 20 * 1024 * 1024,  # 20MB
        "min_size": 10 * 1024  # 10KB
    }
    
    XIAOHONGSHU_VIDEO = {
        "aspect_ratio": "9:16",
        "resolution": (1080, 1920),
        "fps": 30,
        "codec": "libx264",
        "bitrate": "5000k",
        "audio_codec": "aac",
        "audio_bitrate": "128k",
        "max_duration": 15 * 60,
        "min_duration": 3,
        "format": "mp4"
    }


@dataclass
class ConversionResult:
    """转换结果"""
    success: bool
    input_path: str
    output_path: str
    platform: str
    format_type: str
    duration: float
    resolution: Tuple[int, int]
    file_size: int
    operations: list
    error: Optional[str] = None


class FormatAdapter:
    """格式适配器"""
    
    def __init__(self):
        pass
    
    def get_platform_format(self, platform: str, content_type: str = "video") -> Dict[str, Any]:
        """
        获取平台格式规范
        
        Args:
            platform: 平台名称
            content_type: 内容类型（video/image）
            
        Returns:
            Dict: 格式规范
        """
        platform_upper = platform.upper()
        
        if platform_upper == "XIAOHONGSHU":
            if content_type == "image":
                return PlatformFormat.XIAOHONGSHU_IMAGE.value
            else:
                return PlatformFormat.XIAOHONGSHU_VIDEO.value
        else:
            format_enum = getattr(PlatformFormat, platform_upper, None)
            if format_enum:
                return format_enum.value
        
        # 默认返回抖音格式
        return PlatformFormat.DOUYIN.value
    
    def adapt_video_format(
        self,
        input_path: str,
        platform: str,
        output_path: Optional[str] = None
    ) -> ConversionResult:
        """
        适配视频格式到目标平台
        
        Args:
            input_path: 输入视频路径
            platform: 目标平台
            output_path: 输出路径（可选）
            
        Returns:
            ConversionResult: 转换结果
        """
        try:
            # 获取目标格式
            target_format = self.get_platform_format(platform, "video")
            
            # 生成输出路径
            if output_path is None:
                input_path_obj = Path(input_path)
                output_path = str(input_path_obj.parent / f"{input_path_obj.stem}_{platform}{input_path_obj.suffix}")
            
            # 加载视频信息
            video = VideoFileClip(input_path)
            original_duration = video.duration
            original_resolution = video.size
            original_fps = video.fps
            
            logger.info(f"原始视频: 时长={original_duration:.2f}s, 分辨率={original_resolution}, 帧率={original_fps:.2f}")
            
            operations = []
            
            # 检查时长是否符合要求
            if original_duration < target_format["min_duration"]:
                video.close()
                return ConversionResult(
                    success=False,
                    input_path=input_path,
                    output_path="",
                    platform=platform,
                    format_type="video",
                    duration=original_duration,
                    resolution=original_resolution,
                    file_size=0,
                    operations=[],
                    error=f"视频时长({original_duration:.2f}s)小于平台要求的{target_format['min_duration']}秒"
                )
            
            if original_duration > target_format["max_duration"]:
                # 裁剪视频
                max_duration = target_format["max_duration"]
                video = video.subclip(0, max_duration)
                operations.append({
                    "type": "trim",
                    "original_duration": original_duration,
                    "new_duration": max_duration
                })
                logger.info(f"✓ 裁剪视频: {original_duration:.2f}s → {max_duration:.2f}s")
            
            # 检查分辨率和宽高比
            target_resolution = target_format["resolution"]
            target_aspect = target_format["aspect_ratio"]
            
            current_aspect = original_resolution[0] / original_resolution[1]
            target_aspect_ratio = self._parse_aspect_ratio(target_aspect)
            
            if abs(current_aspect - target_aspect_ratio) > 0.1:
                # 需要调整宽高比
                video = self._adjust_aspect_ratio(video, target_aspect_ratio)
                operations.append({
                    "type": "aspect_ratio_adjust",
                    "from": f"{original_resolution[0]}x{original_resolution[1]}",
                    "to": target_aspect
                })
                logger.info(f"✓ 调整宽高比: {target_aspect}")
            
            # 调整分辨率
            if video.size != target_resolution:
                video = video.resize(target_resolution)
                operations.append({
                    "type": "resize",
                    "from": f"{video.w}x{video.h}",
                    "to": f"{target_resolution[0]}x{target_resolution[1]}"
                })
                logger.info(f"✓ 调整分辨率: {target_resolution[0]}x{target_resolution[1]}")
            
            # 调整帧率
            target_fps = target_format["fps"]
            if abs(video.fps - target_fps) > 1:
                video = video.set_fps(target_fps)
                operations.append({
                    "type": "fps_adjust",
                    "from": f"{original_fps:.2f}",
                    "to": f"{target_fps}"
                })
                logger.info(f"✓ 调整帧率: {original_fps:.2f} → {target_fps}")
            
            # 导出视频
            video.write_videofile(
                output_path,
                codec=target_format["codec"],
                bitrate=target_format["bitrate"],
                audio_codec=target_format["audio_codec"],
                audio_bitrate=target_format["audio_bitrate"],
                temp_audiofile='temp-audio-format.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            video.close()
            
            # 获取输出文件信息
            output_size = os.path.getsize(output_path)
            output_video = VideoFileClip(output_path)
            final_duration = output_video.duration
            final_resolution = output_video.size
            output_video.close()
            
            result = ConversionResult(
                success=True,
                input_path=input_path,
                output_path=output_path,
                platform=platform,
                format_type="video",
                duration=final_duration,
                resolution=final_resolution,
                file_size=output_size,
                operations=operations
            )
            
            logger.info(f"✅ 视频格式适配完成: {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"视频格式适配失败: {e}")
            return ConversionResult(
                success=False,
                input_path=input_path,
                output_path="",
                platform=platform,
                format_type="video",
                duration=0,
                resolution=(0, 0),
                file_size=0,
                operations=[],
                error=str(e)
            )
    
    def adapt_image_format(
        self,
        input_path: str,
        platform: str,
        output_path: Optional[str] = None
    ) -> ConversionResult:
        """
        适配图片格式到目标平台
        
        Args:
            input_path: 输入图片路径
            platform: 目标平台
            output_path: 输出路径（可选）
            
        Returns:
            ConversionResult: 转换结果
        """
        try:
            # 获取目标格式
            target_format = self.get_platform_format(platform, "image")
            
            # 生成输出路径
            if output_path is None:
                input_path_obj = Path(input_path)
                output_path = str(input_path_obj.parent / f"{input_path_obj.stem}_{platform}.{target_format['format']}")
            
            # 使用FFmpeg处理图片
            target_resolution = target_format["resolution"]
            
            cmd = [
                'ffmpeg', '-y',
                '-i', input_path,
                '-vf', f'scale={target_resolution[0]}:{target_resolution[1]}:force_original_aspect_ratio=decrease,pad={target_resolution[0]}:{target_resolution[1]}:(ow-iw)/2:(oh-ih)/2',
                '-q:v', '2',  # 高质量
                output_path
            ]
            
            subprocess.run(cmd, check=True, capture_output=True)
            
            # 获取输出文件信息
            output_size = os.path.getsize(output_path)
            
            # 检查文件大小
            if output_size > target_format["max_size"]:
                # 压缩图片
                self._compress_image(output_path, output_path, target_format["max_size"])
                output_size = os.path.getsize(output_path)
            
            result = ConversionResult(
                success=True,
                input_path=input_path,
                output_path=output_path,
                platform=platform,
                format_type="image",
                duration=0,
                resolution=target_resolution,
                file_size=output_size,
                operations=[
                    {"type": "resize", "to": f"{target_resolution[0]}x{target_resolution[1]}"},
                    {"type": "format", "to": target_format["format"]}
                ]
            )
            
            logger.info(f"✅ 图片格式适配完成: {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"图片格式适配失败: {e}")
            return ConversionResult(
                success=False,
                input_path=input_path,
                output_path="",
                platform=platform,
                format_type="image",
                duration=0,
                resolution=(0, 0),
                file_size=0,
                operations=[],
                error=str(e)
            )
    
    def _parse_aspect_ratio(self, aspect_str: str) -> float:
        """
        解析宽高比字符串
        
        Args:
            aspect_str: 宽高比字符串（如 "9:16"）
            
        Returns:
            float: 宽高比值
        """
        parts = aspect_str.split(":")
        if len(parts) == 2:
            width = float(parts[0])
            height = float(parts[1])
            return width / height
        return 16.0 / 9.0  # 默认16:9
    
    def _adjust_aspect_ratio(self, video: VideoFileClip, target_ratio: float) -> VideoFileClip:
        """
        调整视频宽高比
        
        Args:
            video: 视频对象
            target_ratio: 目标宽高比
            
        Returns:
            VideoFileClip: 调整后的视频
        """
        w, h = video.size
        current_ratio = w / h
        
        if current_ratio > target_ratio:
            # 视频太宽，裁剪宽度
            new_width = int(h * target_ratio)
            x_offset = (w - new_width) // 2
            video = video.crop(x1=x_offset, y1=0, x2=x_offset+new_width, y2=h)
        else:
            # 视频太高，裁剪高度
            new_height = int(w / target_ratio)
            y_offset = (h - new_height) // 2
            video = video.crop(x1=0, y1=y_offset, x2=w, y2=y_offset+new_height)
        
        return video
    
    def _compress_image(self, input_path: str, output_path: str, max_size: int):
        """
        压缩图片到指定大小
        
        Args:
            input_path: 输入路径
            output_path: 输出路径
            max_size: 最大文件大小（字节）
        """
        quality = 95
        while quality > 50:
            cmd = [
                'ffmpeg', '-y',
                '-i', input_path,
                '-q:v', str(quality),
                output_path
            ]
            subprocess.run(cmd, check=True, capture_output=True)
            
            if os.path.getsize(output_path) <= max_size:
                break
            
            quality -= 5
    
    def batch_adapt(
        self,
        input_paths: list,
        platform: str,
        output_dir: Optional[str] = None
    ) -> list:
        """
        批量适配格式
        
        Args:
            input_paths: 输入文件路径列表
            platform: 目标平台
            output_dir: 输出目录
            
        Returns:
            list: 转换结果列表
        """
        if output_dir is None:
            output_dir = str(Path(input_paths[0]).parent / f"adapted_{platform}")
        
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i, input_path in enumerate(input_paths):
            logger.info(f"📦 处理 {i+1}/{len(input_paths)}: {input_path}")
            
            # 判断文件类型
            if input_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                result = self.adapt_video_format(input_path, platform)
            elif input_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                result = self.adapt_image_format(input_path, platform)
            else:
                logger.warning(f"不支持的文件格式: {input_path}")
                continue
            
            results.append(result)
        
        success_count = sum(1 for r in results if r.success)
        logger.info(f"✅ 批量适配完成: {success_count}/{len(input_paths)} 成功")
        
        return results
    
    def get_format_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件格式信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            Dict: 格式信息
        """
        try:
            if file_path.lower().endswith(('.mp4', '.mov', '.avi', '.mkv')):
                video = VideoFileClip(file_path)
                info = {
                    "type": "video",
                    "duration": video.duration,
                    "resolution": video.size,
                    "fps": video.fps,
                    "has_audio": video.audio is not None
                }
                video.close()
            elif file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                from PIL import Image
                img = Image.open(file_path)
                info = {
                    "type": "image",
                    "resolution": img.size,
                    "format": img.format,
                    "mode": img.mode
                }
            else:
                info = {"type": "unknown"}
            
            info["file_size"] = os.path.getsize(file_path)
            info["file_path"] = file_path
            
            return info
            
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            return {"type": "error", "error": str(e)}


# 创建全局格式适配器实例
_format_adapter = None


def get_format_adapter() -> FormatAdapter:
    """
    获取格式适配器实例（单例模式）
    
    Returns:
        FormatAdapter: 格式适配器实例
    """
    global _format_adapter
    if _format_adapter is None:
        _format_adapter = FormatAdapter()
    return _format_adapter
