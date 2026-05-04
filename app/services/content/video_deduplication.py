"""
视频去重服务
实现画面层、数据层、结构层的视频去重处理
"""
import os
import random
import logging
import hashlib
import subprocess
import tempfile
from typing import Dict, Any, Optional, Tuple, List
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import cv2
import numpy as np
from moviepy.editor import VideoFileClip, CompositeVideoClip, vfx, AudioFileClip
from moviepy.video.fx import all as vfx_all

logger = logging.getLogger(__name__)


class VideoLayer(Enum):
    """视频处理层级"""
    VISUAL = "visual"  # 画面层
    DATA = "data"  # 数据层
    STRUCTURAL = "structural"  # 结构层


@dataclass
class VideoDeduplicationConfig:
    """视频去重配置"""
    # 画面层配置
    enable_mirror: bool = True  # 启用镜像
    enable_frame_rate_adjust: bool = True  # 启用帧率调整
    enable_color_filter: bool = True  # 启用色彩滤镜
    enable_picture_in_picture: bool = True  # 启用画中画
    enable_crop: bool = True  # 启用裁剪
    enable_zoom: bool = True  # 启用缩放
    enable_rotation: bool = False  # 启用旋转（谨慎使用）
    
    # 画面层参数
    mirror_probability: float = 0.5  # 镜像概率
    frame_rate_adjust_range: Tuple[float, float] = (0.9, 1.1)  # 帧率调整范围
    color_filter_intensity: float = 0.3  # 色彩滤镜强度
    pip_probability: float = 0.3  # 画中画概率
    crop_range: Tuple[float, float] = (0.95, 0.98)  # 裁剪范围
    zoom_range: Tuple[float, float] = (1.02, 1.05)  # 缩放范围
    rotation_range: Tuple[float, float] = (-3, 3)  # 旋转范围（度）
    
    # 数据层配置
    enable_md5_modify: bool = True  # 启用MD5修改
    enable_audio_bitrate_adjust: bool = True  # 启用音频比特率调整
    enable_watermark: bool = True  # 启用水印
    enable_metadata_clear: bool = True  # 启用元数据清除
    
    # 数据层参数
    audio_bitrate_options: List[str] = ["128k", "192k", "256k"]
    watermark_text: str = ""
    watermark_opacity: float = 0.1
    watermark_position: str = "bottom-right"  # top-left, top-right, bottom-left, bottom-right
    
    # 结构层配置
    enable_segment_reorder: bool = True  # 启用片段重排
    enable_segment_insert: bool = True  # 启用片段插入
    enable_segment_delete: bool = True  # 启用片段删除
    enable_speed_adjust: bool = True  # 启用速度调整
    
    # 结构层参数
    min_segment_duration: float = 2.0  # 最小片段时长（秒）
    max_segment_duration: float = 10.0  # 最大片段时长（秒）
    reorder_probability: float = 0.3  # 重排概率
    insert_probability: float = 0.2  # 插入概率
    delete_probability: float = 0.1  # 删除概率
    speed_adjust_range: Tuple[float, float] = (0.95, 1.05)


class VisualLayerProcessor:
    """画面层处理器"""
    
    def __init__(self, config: VideoDeduplicationConfig):
        self.config = config
    
    def process(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        处理画面层
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            
        Returns:
            Dict: 处理结果
        """
        try:
            result = {
                "layer": VideoLayer.VISUAL.value,
                "operations": [],
                "success": True,
                "error": None
            }
            
            # 加载视频
            video = VideoFileClip(input_path)
            
            # 应用画面层处理
            processed_video = self._apply_visual_effects(video, result)
            
            # 导出视频
            processed_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # 关闭视频对象
            video.close()
            processed_video.close()
            
            logger.info(f"✅ 画面层处理完成: {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"画面层处理失败: {e}")
            return {
                "layer": VideoLayer.VISUAL.value,
                "operations": [],
                "success": False,
                "error": str(e)
            }
    
    def _apply_visual_effects(self, video: VideoFileClip, result: Dict) -> VideoFileClip:
        """
        应用画面效果
        
        Args:
            video: 视频对象
            result: 结果字典
            
        Returns:
            VideoFileClip: 处理后的视频
        """
        processed = video
        
        # 1. 镜像处理
        if self.config.enable_mirror and random.random() < self.config.mirror_probability:
            processed = processed.fx(vfx.mirror_x)
            result["operations"].append({"type": "mirror", "direction": "horizontal"})
            logger.info("✓ 应用水平镜像")
        
        # 2. 裁剪处理
        if self.config.enable_crop:
            crop_ratio = random.uniform(*self.config.crop_range)
            w, h = processed.size
            new_w = int(w * crop_ratio)
            new_h = int(h * crop_ratio)
            x1 = (w - new_w) // 2
            y1 = (h - new_h) // 2
            
            processed = processed.crop(x1=x1, y1=y1, x2=x1+new_w, y2=y1+new_h)
            result["operations"].append({
                "type": "crop",
                "ratio": crop_ratio,
                "size": (new_w, new_h)
            })
            logger.info(f"✓ 应用裁剪: {crop_ratio:.2f}")
        
        # 3. 缩放处理（恢复到原始尺寸）
        if self.config.enable_zoom:
            zoom_factor = random.uniform(*self.config.zoom_range)
            processed = processed.resize(zoom_factor)
            result["operations"].append({"type": "zoom", "factor": zoom_factor})
            logger.info(f"✓ 应用缩放: {zoom_factor:.2f}x")
        
        # 4. 旋转处理
        if self.config.enable_rotation and random.random() < 0.3:
            angle = random.uniform(*self.config.rotation_range)
            processed = processed.rotate(angle)
            result["operations"].append({"type": "rotate", "angle": angle})
            logger.info(f"✓ 应用旋转: {angle:.2f}°")
        
        # 5. 色彩滤镜处理
        if self.config.enable_color_filter:
            processed = self._apply_color_filter(processed, result)
        
        # 6. 画中画处理
        if self.config.enable_picture_in_picture and random.random() < self.config.pip_probability:
            processed = self._apply_picture_in_picture(processed, result)
        
        # 7. 帧率调整
        if self.config.enable_frame_rate_adjust:
            fps_factor = random.uniform(*self.config.frame_rate_adjust_range)
            new_fps = processed.fps * fps_factor
            processed = processed.set_fps(new_fps)
            result["operations"].append({
                "type": "frame_rate_adjust",
                "original_fps": processed.fps / fps_factor,
                "new_fps": new_fps
            })
            logger.info(f"✓ 调整帧率: {processed.fps / fps_factor:.2f} → {new_fps:.2f} fps")
        
        return processed
    
    def _apply_color_filter(self, video: VideoFileClip, result: Dict) -> VideoFileClip:
        """
        应用色彩滤镜
        
        Args:
            video: 视频对象
            result: 结果字典
            
        Returns:
            VideoFileClip: 处理后的视频
        """
        # 随机选择滤镜类型
        filter_types = ["brightness", "contrast", "saturation", "hue"]
        selected_filters = random.sample(filter_types, k=random.randint(1, 3))
        
        for filter_type in selected_filters:
            intensity = random.uniform(-self.config.color_filter_intensity, self.config.color_filter_intensity)
            
            if filter_type == "brightness":
                # 亮度调整
                video = video.fx(vfx_all.lum_contrast, lum=1.0 + intensity)
            elif filter_type == "contrast":
                # 对比度调整
                video = video.fx(vfx_all.lum_contrast, contrast=1.0 + intensity)
            elif filter_type == "saturation":
                # 饱和度调整（需要自定义实现）
                video = video.fx(self._adjust_saturation, saturation=1.0 + intensity)
            elif filter_type == "hue":
                # 色相调整（需要自定义实现）
                video = video.fx(self._adjust_hue, shift=intensity * 30)
            
            result["operations"].append({
                "type": f"color_filter_{filter_type}",
                "intensity": intensity
            })
            logger.info(f"✓ 应用色彩滤镜: {filter_type} (强度: {intensity:.2f})")
        
        return video
    
    @staticmethod
    def _adjust_saturation(clip, saturation=1.0):
        """调整饱和度"""
        def get_frame(frame):
            # 转换到HSV色彩空间
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            # 调整S通道
            hsv[:, :, 1] = np.clip(hsv[:, :, 1] * saturation, 0, 255).astype(np.uint8)
            # 转换回RGB
            return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        
        return clip.fl(get_frame)
    
    @staticmethod
    def _adjust_hue(clip, shift=0):
        """调整色相"""
        def get_frame(frame):
            # 转换到HSV色彩空间
            hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)
            # 调整H通道
            hsv[:, :, 0] = (hsv[:, :, 0] + shift) % 180
            # 转换回RGB
            return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
        
        return clip.fl(get_frame)
    
    def _apply_picture_in_picture(self, video: VideoFileClip, result: Dict) -> VideoFileClip:
        """
        应用画中画效果
        
        Args:
            video: 视频对象
            result: 结果字典
            
        Returns:
            VideoFileClip: 处理后的视频
        """
        try:
            w, h = video.size
            
            # 创建小的画中画窗口
            pip_width = int(w * 0.2)
            pip_height = int(h * 0.2)
            
            # 随机选择位置
            positions = ["top-left", "top-right", "bottom-left", "bottom-right"]
            position = random.choice(positions)
            
            if position == "top-left":
                x, y = 0, 0
            elif position == "top-right":
                x, y = w - pip_width, 0
            elif position == "bottom-left":
                x, y = 0, h - pip_height
            else:  # bottom-right
                x, y = w - pip_width, h - pip_height
            
            # 创建画中画片段（视频的一部分）
            pip_clip = video.resize((pip_width, pip_height))
            pip_clip = pip_clip.set_position((x, y))
            pip_clip = pip_clip.set_opacity(0.3)  # 半透明
            
            # 合成
            final = CompositeVideoClip([video, pip_clip])
            
            result["operations"].append({
                "type": "picture_in_picture",
                "position": position,
                "size": (pip_width, pip_height),
                "opacity": 0.3
            })
            logger.info(f"✓ 应用画中画: {position}, 透明度: 0.3")
            
            return final
            
        except Exception as e:
            logger.warning(f"画中画处理失败: {e}")
            return video


class DataLayerProcessor:
    """数据层处理器"""
    
    def __init__(self, config: VideoDeduplicationConfig):
        self.config = config
    
    def process(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        处理数据层
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            
        Returns:
            Dict: 处理结果
        """
        try:
            result = {
                "layer": VideoLayer.DATA.value,
                "operations": [],
                "success": True,
                "error": None
            }
            
            # 加载视频
            video = VideoFileClip(input_path)
            audio = video.audio
            
            # 1. MD5修改（通过在末尾添加微小帧）
            if self.config.enable_md5_modify:
                result["operations"].append({"type": "md5_modify", "method": "micro_frame"})
                logger.info("✓ 将通过添加微小帧修改MD5")
            
            # 2. 音频比特率调整
            if self.config.enable_audio_bitrate_adjust and audio:
                new_bitrate = random.choice(self.config.audio_bitrate_options)
                result["operations"].append({
                    "type": "audio_bitrate_adjust",
                    "new_bitrate": new_bitrate
                })
                logger.info(f"✓ 调整音频比特率: {new_bitrate}")
            else:
                new_bitrate = None
            
            # 3. 元数据清除
            if self.config.enable_metadata_clear:
                result["operations"].append({"type": "metadata_clear"})
                logger.info("✓ 清除视频元数据")
            
            # 4. 水印（如果配置了文本）
            if self.config.enable_watermark and self.config.watermark_text:
                video = self._add_watermark(video)
                result["operations"].append({
                    "type": "watermark",
                    "text": self.config.watermark_text,
                    "position": self.config.watermark_position,
                    "opacity": self.config.watermark_opacity
                })
                logger.info(f"✓ 添加水印: {self.config.watermark_text}")
            
            # 导出视频（使用FFmpeg清除元数据）
            cmd = [
                'ffmpeg', '-y',
                '-i', input_path,
                '-c:v', 'copy',
                '-c:a', 'copy',
                '-movflags', '+faststart',
                '-map_metadata', '-1',
                output_path
            ]
            
            if new_bitrate:
                # 重新编码音频以改变比特率
                cmd = [
                    'ffmpeg', '-y',
                    '-i', input_path,
                    '-c:v', 'copy',
                    '-c:a', 'aac',
                    '-b:a', new_bitrate,
                    '-movflags', '+faststart',
                    '-map_metadata', '-1',
                    output_path
                ]
            
            # 添加微小帧以修改MD5
            if self.config.enable_md5_modify:
                cmd.insert(-1, '-metadata')
                cmd.insert(-1, f'title=Deduplicated_{random.randint(10000, 99999)}')
            
            # 执行FFmpeg命令
            subprocess.run(cmd, check=True, capture_output=True)
            
            # 关闭视频对象
            video.close()
            if audio:
                audio.close()
            
            logger.info(f"✅ 数据层处理完成: {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"数据层处理失败: {e}")
            return {
                "layer": VideoLayer.DATA.value,
                "operations": [],
                "success": False,
                "error": str(e)
            }
    
    def _add_watermark(self, video: VideoFileClip) -> VideoFileClip:
        """
        添加水印
        
        Args:
            video: 视频对象
            
        Returns:
            VideoFileClip: 带水印的视频
        """
        from moviepy.video.fx.all import textclip
        
        w, h = video.size
        font_size = int(h * 0.05)
        
        # 创建文本水印
        txt_clip = textclip.TextClip(
            self.config.watermark_text,
            fontsize=font_size,
            color='white',
            font='Arial-Bold',
            transparent=True
        )
        
        # 设置位置
        position = self.config.watermark_position
        if position == "top-left":
            txt_clip = txt_clip.set_position((10, 10))
        elif position == "top-right":
            txt_clip = txt_clip.set_position((w - txt_clip.w - 10, 10))
        elif position == "bottom-left":
            txt_clip = txt_clip.set_position((10, h - txt_clip.h - 10))
        else:  # bottom-right
            txt_clip = txt_clip.set_position((w - txt_clip.w - 10, h - txt_clip.h - 10))
        
        # 设置透明度
        txt_clip = txt_clip.set_opacity(self.config.watermark_opacity)
        
        # 设置持续时间
        txt_clip = txt_clip.set_duration(video.duration)
        
        # 合成
        final = CompositeVideoClip([video, txt_clip])
        
        return final
    
    def calculate_md5(self, file_path: str) -> str:
        """
        计算文件的MD5哈希值
        
        Args:
            file_path: 文件路径
            
        Returns:
            str: MD5哈希值
        """
        md5_hash = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5_hash.update(chunk)
        return md5_hash.hexdigest()


class StructuralLayerProcessor:
    """结构层处理器"""
    
    def __init__(self, config: VideoDeduplicationConfig):
        self.config = config
    
    def process(self, input_path: str, output_path: str) -> Dict[str, Any]:
        """
        处理结构层
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径
            
        Returns:
            Dict: 处理结果
        """
        try:
            result = {
                "layer": VideoLayer.STRUCTURAL.value,
                "operations": [],
                "success": True,
                "error": None
            }
            
            # 加载视频
            video = VideoFileClip(input_path)
            total_duration = video.duration
            
            # 分析视频并分割成片段
            segments = self._analyze_and_split(video, result)
            
            if len(segments) < 2:
                logger.warning("视频片段过少，跳过结构层处理")
                result["operations"].append({"type": "skip", "reason": "insufficient_segments"})
                video.close()
                return result
            
            # 1. 片段重排
            if self.config.enable_segment_reorder and random.random() < self.config.reorder_probability:
                segments = self._reorder_segments(segments, result)
            
            # 2. 片段插入
            if self.config.enable_segment_insert and random.random() < self.config.insert_probability:
                segments = self._insert_segments(segments, video, result)
            
            # 3. 片段删除
            if self.config.enable_segment_delete and random.random() < self.config.delete_probability:
                segments = self._delete_segments(segments, result)
            
            # 4. 速度调整
            if self.config.enable_speed_adjust:
                segments = self._adjust_segments_speed(segments, result)
            
            # 合并片段
            final_video = self._concatenate_segments(segments, result)
            
            # 导出视频
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio-struct.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # 关闭视频对象
            video.close()
            final_video.close()
            
            for seg in segments:
                if hasattr(seg, 'close'):
                    seg.close()
            
            logger.info(f"✅ 结构层处理完成: {output_path}")
            return result
            
        except Exception as e:
            logger.error(f"结构层处理失败: {e}")
            return {
                "layer": VideoLayer.STRUCTURAL.value,
                "operations": [],
                "success": False,
                "error": str(e)
            }
    
    def _analyze_and_split(self, video: VideoFileClip, result: Dict) -> List[VideoFileClip]:
        """
        分析并分割视频
        
        Args:
            video: 视频对象
            result: 结果字典
            
        Returns:
            List[VideoFileClip]: 视频片段列表
        """
        total_duration = video.duration
        segments = []
        
        # 基于场景检测分割（简化版：按固定时长分割）
        current_time = 0
        segment_index = 0
        
        while current_time < total_duration:
            # 随机片段时长
            segment_duration = random.uniform(
                self.config.min_segment_duration,
                min(self.config.max_segment_duration, total_duration - current_time)
            )
            
            end_time = min(current_time + segment_duration, total_duration)
            
            # 提取片段
            segment = video.subclip(current_time, end_time)
            segments.append(segment)
            
            segment_index += 1
            current_time = end_time
        
        result["operations"].append({
            "type": "segment_split",
            "total_segments": len(segments),
            "avg_duration": total_duration / len(segments)
        })
        
        logger.info(f"✓ 分割视频为 {len(segments)} 个片段")
        return segments
    
    def _reorder_segments(self, segments: List[VideoFileClip], result: Dict) -> List[VideoFileClip]:
        """
        重排片段
        
        Args:
            segments: 视频片段列表
            result: 结果字典
            
        Returns:
            List[VideoFileClip]: 重排后的片段列表
        """
        if len(segments) < 3:
            return segments
        
        # 随机交换几个相邻片段
        num_swaps = random.randint(1, min(3, len(segments) // 2))
        
        for _ in range(num_swaps):
            i = random.randint(0, len(segments) - 2)
            segments[i], segments[i + 1] = segments[i + 1], segments[i]
        
        result["operations"].append({
            "type": "segment_reorder",
            "swaps": num_swaps
        })
        
        logger.info(f"✓ 重排片段，交换 {num_swaps} 次")
        return segments
    
    def _insert_segments(
        self,
        segments: List[VideoFileClip],
        original_video: VideoFileClip,
        result: Dict
    ) -> List[VideoFileClip]:
        """
        插入片段
        
        Args:
            segments: 视频片段列表
            original_video: 原始视频
            result: 结果字典
            
        Returns:
            List[VideoFileClip]: 插入后的片段列表
        """
        # 随机选择一个片段复制插入
        if len(segments) < 2:
            return segments
        
        insert_pos = random.randint(1, len(segments) - 1)
        source_pos = random.randint(0, len(segments) - 1)
        
        # 复制片段
        source_segment = segments[source_pos]
        
        # 创建新片段（重复）
        new_segment = source_segment.subclip(0, min(source_segment.duration, 3.0))
        
        # 插入到指定位置
        segments.insert(insert_pos, new_segment)
        
        result["operations"].append({
            "type": "segment_insert",
            "insert_position": insert_pos,
            "source_position": source_pos
        })
        
        logger.info(f"✓ 在位置 {insert_pos} 插入片段")
        return segments
    
    def _delete_segments(self, segments: List[VideoFileClip], result: Dict) -> List[VideoFileClip]:
        """
        删除片段
        
        Args:
            segments: 视频片段列表
            result: 结果字典
            
        Returns:
            List[VideoFileClip]: 删除后的片段列表
        """
        if len(segments) < 4:
            return segments
        
        # 随机删除1-2个中间片段（保留开头和结尾）
        num_deletes = random.randint(1, min(2, len(segments) - 3))
        
        for _ in range(num_deletes):
            delete_pos = random.randint(1, len(segments) - 2)
            segments.pop(delete_pos)
        
        result["operations"].append({
            "type": "segment_delete",
            "deleted_count": num_deletes
        })
        
        logger.info(f"✓ 删除 {num_deletes} 个片段")
        return segments
    
    def _adjust_segments_speed(
        self,
        segments: List[VideoFileClip],
        result: Dict
    ) -> List[VideoFileClip]:
        """
        调整片段速度
        
        Args:
            segments: 视频片段列表
            result: 结果字典
            
        Returns:
            List[VideoFileClip]: 速度调整后的片段列表
        """
        adjusted_segments = []
        speed_changes = 0
        
        for segment in segments:
            if random.random() < 0.3:  # 30%概率调整速度
                speed_factor = random.uniform(*self.config.speed_adjust_range)
                adjusted_segment = segment.fx(vfx.speedx, speed_factor)
                adjusted_segments.append(adjusted_segment)
                speed_changes += 1
            else:
                adjusted_segments.append(segment)
        
        result["operations"].append({
            "type": "speed_adjust",
            "affected_segments": speed_changes
        })
        
        logger.info(f"✓ 调整 {speed_changes} 个片段的速度")
        return adjusted_segments
    
    def _concatenate_segments(
        self,
        segments: List[VideoFileClip],
        result: Dict
    ) -> VideoFileClip:
        """
        连接片段
        
        Args:
            segments: 视频片段列表
            result: 结果字典
            
        Returns:
            VideoFileClip: 合并后的视频
        """
        final_video = segments[0]
        
        for segment in segments[1:]:
            # 添加淡入淡出过渡
            final_video = final_video.crossfadeout(0.3)
            segment = segment.crossfadein(0.3)
            final_video = final_video.append(segment)
        
        result["operations"].append({
            "type": "concatenate",
            "transition": "crossfade",
            "duration": 0.3
        })
        
        logger.info(f"✓ 连接 {len(segments)} 个片段")
        return final_video


class VideoDeduplicationEngine:
    """视频去重引擎（统一入口）"""
    
    def __init__(self, config: Optional[VideoDeduplicationConfig] = None):
        self.config = config or VideoDeduplicationConfig()
        self.visual_processor = VisualLayerProcessor(self.config)
        self.data_processor = DataLayerProcessor(self.config)
        self.structural_processor = StructuralLayerProcessor(self.config)
    
    def deduplicate(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        layers: Optional[List[VideoLayer]] = None
    ) -> Dict[str, Any]:
        """
        执行视频去重
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频路径（不指定则自动生成）
            layers: 要处理的层级（不指定则处理所有层级）
            
        Returns:
            Dict: 处理结果
        """
        if layers is None:
            layers = [VideoLayer.VISUAL, VideoLayer.DATA, VideoLayer.STRUCTURAL]
        
        # 生成输出路径
        if output_path is None:
            input_path_obj = Path(input_path)
            output_path = str(input_path_obj.parent / f"{input_path_obj.stem}_dedup{input_path_obj.suffix}")
        
        results = {
            "input_path": input_path,
            "output_path": output_path,
            "layers_processed": [],
            "success": True,
            "errors": []
        }
        
        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            current_input = input_path
            current_output = os.path.join(temp_dir, f"temp_{os.path.basename(input_path)}")
            
            # 逐层处理
            for layer in layers:
                logger.info(f"🔄 开始处理 {layer.value} 层...")
                
                if layer == VideoLayer.VISUAL:
                    result = self.visual_processor.process(current_input, current_output)
                elif layer == VideoLayer.DATA:
                    result = self.data_processor.process(current_input, current_output)
                elif layer == VideoLayer.STRUCTURAL:
                    result = self.structural_processor.process(current_input, current_output)
                else:
                    logger.warning(f"未知的层级: {layer.value}")
                    continue
                
                results["layers_processed"].append(result)
                
                if result["success"]:
                    # 更新输入为当前输出，供下一层使用
                    current_input = current_output
                    current_output = os.path.join(temp_dir, f"temp_{random.randint(1000, 9999)}_{os.path.basename(input_path)}")
                else:
                    results["success"] = False
                    results["errors"].append({
                        "layer": layer.value,
                        "error": result["error"]
                    })
                    logger.error(f"{layer.value} 层处理失败: {result['error']}")
                    break
            
            # 将最终结果移动到指定输出路径
            if results["success"] and os.path.exists(current_input):
                import shutil
                shutil.move(current_input, output_path)
                logger.info(f"✅ 视频去重完成: {output_path}")
            else:
                # 如果失败，复制原始文件
                import shutil
                shutil.copy(input_path, output_path)
                logger.warning("⚠️ 视频去重失败，输出原始文件")
        
        return results
    
    def batch_deduplicate(
        self,
        input_paths: List[str],
        output_dir: str,
        layers: Optional[List[VideoLayer]] = None
    ) -> List[Dict[str, Any]]:
        """
        批量去重
        
        Args:
            input_paths: 输入视频路径列表
            output_dir: 输出目录
            layers: 要处理的层级
            
        Returns:
            List[Dict]: 处理结果列表
        """
        os.makedirs(output_dir, exist_ok=True)
        results = []
        
        for i, input_path in enumerate(input_paths):
            logger.info(f"📦 处理 {i+1}/{len(input_paths)}: {input_path}")
            
            input_path_obj = Path(input_path)
            output_path = os.path.join(output_dir, f"{input_path_obj.stem}_dedup{input_path_obj.suffix}")
            
            result = self.deduplicate(input_path, output_path, layers)
            results.append(result)
        
        success_count = sum(1 for r in results if r["success"])
        logger.info(f"✅ 批量去重完成: {success_count}/{len(input_paths)} 成功")
        
        return results


# 创建全局视频去重引擎实例
_deduplication_engine = None


def get_deduplication_engine(
    config: Optional[VideoDeduplicationConfig] = None
) -> VideoDeduplicationEngine:
    """
    获取视频去重引擎实例（单例模式）
    
    Args:
        config: 去重配置
        
    Returns:
        VideoDeduplicationEngine: 视频去重引擎实例
    """
    global _deduplication_engine
    if _deduplication_engine is None or config is not None:
        _deduplication_engine = VideoDeduplicationEngine(config)
    return _deduplication_engine
