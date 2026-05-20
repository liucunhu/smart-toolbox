"""
动态字幕生成服务
实现语音识别、热门音效插入、热门BGM匹配
"""
import os
import random
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from pathlib import Path

from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, AudioFileClip, vfx
import numpy as np

logger = logging.getLogger(__name__)


class SubtitleStyle:
    """字幕样式"""
    MODERN = "modern"  # 现代风格
    CLASSIC = "classic"  # 经典风格
    CARTOON = "cartoon"  # 卡通风格


class DynamicSubtitleGenerator:
    """动态字幕生成器"""
    
    # 热门音效库
    POPULAR_SOUNDS = {
        "ding": {
            "name": "叮",
            "file": "assets/sounds/ding.mp3",
            "description": "提示音"
        },
        "wow": {
            "name": "哇",
            "file": "assets/sounds/wow.mp3",
            "description": "惊讶音"
        },
        "success": {
            "name": "成功",
            "file": "assets/sounds/success.mp3",
            "description": "成功音"
        },
        "suspense": {
            "name": "悬念",
            "file": "assets/sounds/suspense.mp3",
            "description": "悬念音"
        }
    }
    
    # 热门BGM库
    POPULAR_BGM = {
        "upbeat": {
            "name": "欢快",
            "file": "assets/bgm/upbeat.mp3",
            "mood": "energetic"
        },
        "emotional": {
            "name": "情感",
            "file": "assets/bgm/emotional.mp3",
            "mood": "touching"
        },
        "tension": {
            "name": "紧张",
            "file": "assets/bgm/tension.mp3",
            "mood": "exciting"
        },
        "calm": {
            "name": "平静",
            "file": "assets/bgm/calm.mp3",
            "mood": "relaxing"
        }
    }
    
    def __init__(self):
        pass
    
    def generate_subtitles(
        self,
        video_path: str,
        subtitle_text: List[Dict[str, Any]],
        output_path: str,
        style: SubtitleStyle = SubtitleStyle.MODERN
    ) -> Dict[str, Any]:
        """
        生成动态字幕
        
        Args:
            video_path: 视频路径
            subtitle_text: 字幕文本列表 [{"text": "内容", "start": 0.0, "end": 3.0}]
            output_path: 输出路径
            style: 字幕样式
            
        Returns:
            Dict: 生成结果
        """
        try:
            # 加载视频
            video = VideoFileClip(video_path)
            
            # 生成字幕片段
            subtitle_clips = []
            
            for subtitle in subtitle_text:
                text = subtitle["text"]
                start = subtitle["start"]
                end = subtitle["end"]
                duration = end - start
                
                # 创建字幕片段
                txt_clip = self._create_text_clip(text, duration, style)
                
                # 设置时间位置
                txt_clip = txt_clip.set_start(start)
                txt_clip = txt_clip.set_end(end)
                
                subtitle_clips.append(txt_clip)
            
            # 合成视频和字幕
            if subtitle_clips:
                final_video = CompositeVideoClip([video] + subtitle_clips)
            else:
                final_video = video
            
            # 导出视频
            final_video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio-subtitle.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # 关闭视频对象
            video.close()
            final_video.close()
            for clip in subtitle_clips:
                clip.close()
            
            logger.info(f"✅ 动态字幕生成成功: {output_path}")
            return {
                "success": True,
                "output_path": output_path,
                "subtitle_count": len(subtitle_text),
                "style": style.value
            }
            
        except Exception as e:
            logger.error(f"动态字幕生成失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_text_clip(
        self,
        text: str,
        duration: float,
        style: SubtitleStyle
    ) -> TextClip:
        """
        创建文本片段
        
        Args:
            text: 文本内容
            duration: 持续时间
            style: 样式
            
        Returns:
            TextClip: 文本片段
        """
        if style == SubtitleStyle.MODERN:
            # 现代风格：白色字体，黑色描边
            return TextClip(
                text,
                fontsize=60,
                font='Arial-Bold',
                color='white',
                stroke_color='black',
                stroke_width=2,
                method='caption',
                size=(800, 200)
            ).set_duration(duration).set_position('center', 'bottom')
        
        elif style == SubtitleStyle.CLASSIC:
            # 经典风格：黄色字体，黑色背景
            return TextClip(
                text,
                fontsize=50,
                font='Georgia',
                color='yellow',
                bg_color='black',
                method='caption',
                size=(800, 200)
            ).set_duration(duration).set_position('center', 'bottom')
        
        else:  # CARTOON
            # 卡通风格：彩色字体
            colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEEAD']
            color = random.choice(colors)
            
            return TextClip(
                text,
                fontsize=70,
                font='Comic Sans MS',
                color=color,
                stroke_color='white',
                stroke_width=3,
                method='caption',
                size=(800, 200)
            ).set_duration(duration).set_position('center', 'bottom')
    
    def insert_sound_effects(
        self,
        video_path: str,
        sound_effects: List[Dict[str, Any]],
        output_path: str
    ) -> Dict[str, Any]:
        """
        插入热门音效
        
        Args:
            video_path: 视频路径
            sound_effects: 音效列表 [{"sound": "ding", "position": 3.0}]
            output_path: 输出路径
            
        Returns:
            Dict: 生成结果
        """
        try:
            # 加载视频
            video = VideoFileClip(video_path)
            
            # 加载原始音频
            if video.audio:
                original_audio = video.audio
            else:
                original_audio = None
            
            # 创建音频列表
            audio_clips = [original_audio] if original_audio else []
            
            # 插入音效
            for effect in sound_effects:
                sound_name = effect["sound"]
                position = effect["position"]
                
                if sound_name in self.POPULAR_SOUNDS:
                    sound_info = self.POPULAR_SOUNDS[sound_name]
                    sound_file = sound_info["file"]
                    
                    # 检查音效文件是否存在
                    if os.path.exists(sound_file):
                        try:
                            sound_audio = AudioFileClip(sound_file)
                            sound_audio = sound_audio.set_start(position)
                            audio_clips.append(sound_audio)
                            logger.info(f"✓ 插入音效: {sound_info['name']} @ {position}s")
                        except Exception as e:
                            logger.warning(f"加载音效失败: {e}")
                    else:
                        logger.warning(f"音效文件不存在: {sound_file}")
            
            # 混合音频
            if len(audio_clips) > 1:
                final_audio = CompositeAudioClip(audio_clips)
                video = video.set_audio(final_audio)
            elif original_audio:
                video = video.set_audio(original_audio)
            
            # 导出视频
            video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio-sfx.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # 关闭对象
            video.close()
            if original_audio:
                original_audio.close()
            for clip in audio_clips[1:]:  # 跳过原始音频
                clip.close()
            
            logger.info(f"✅ 音效插入完成: {output_path}")
            return {
                "success": True,
                "output_path": output_path,
                "sound_count": len(sound_effects)
            }
            
        except Exception as e:
            logger.error(f"音效插入失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def match_bgm(
        self,
        video_path: str,
        mood: str = "energetic",
        output_path: str
    ) -> Dict[str, Any]:
        """
        匹配并添加热门BGM
        
        Args:
            video_path: 视频路径
            mood: 情绪（energetic/touching/exciting/relaxing）
            output_path: 输出路径
            
        Returns:
            Dict: 生成结果
        """
        try:
            # 加载视频
            video = VideoFileClip(video_path)
            
            # 选择匹配的BGM
            bgm_mapping = {
                "energetic": "upbeat",
                "touching": "emotional",
                "exciting": "tension",
                "relaxing": "calm"
            }
            
            bgm_key = bgm_mapping.get(mood, "upbeat")
            
            if bgm_key in self.POPULAR_BGM:
                bgm_info = self.POPULAR_BGM[bgm_key]
                bgm_file = bgm_info["file"]
                
                # 检查BGM文件是否存在
                if os.path.exists(bgm_file):
                    try:
                        # 加载BGM
                        bgm_audio = AudioFileClip(bgm_file)
                        
                        # 调整BGM长度以匹配视频
                        if bgm_audio.duration < video.duration:
                            # 循环BGM
                            loop_times = int(video.duration / bgm_audio.duration) + 1
                            bgm_audio = bgm_audio.loop(loop_times)
                        bgm_audio = bgm_audio.subclip(0, video.duration)
                        
                        # 混合音量（BGM音量降低）
                        bgm_audio = bgm_audio.volumex(0.3)
                        
                        # 如果视频有原声，进行混合
                        if video.audio:
                            original_audio = video.audio
                            mixed_audio = CompositeAudioClip([original_audio, bgm_audio])
                            video = video.set_audio(mixed_audio)
                        else:
                            video = video.set_audio(bgm_audio)
                        
                        logger.info(f"✓ 添加BGM: {bgm_info['name']}")
                        
                    except Exception as e:
                        logger.warning(f"加载BGM失败: {e}")
                else:
                    logger.warning(f"BGM文件不存在: {bgm_file}")
            
            # 导出视频
            video.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio-bgm.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # 关闭对象
            video.close()
            
            logger.info(f"✅ BGM匹配完成: {output_path}")
            return {
                "success": True,
                "output_path": output_path,
                "bgm_mood": mood
            }
            
        except Exception as e:
            logger.error(f"BGM匹配失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }


# 创建全局动态字幕生成器实例
_subtitle_generator = None


def get_dynamic_subtitle_generator() -> DynamicSubtitleGenerator:
    """
    获取动态字幕生成器实例（单例模式）
    
    Returns:
        DynamicSubtitleGenerator: 动态字幕生成器实例
    """
    global _subtitle_generator
    if _subtitle_generator is None:
        _subtitle_generator = DynamicSubtitleGenerator()
    return _subtitle_generator
