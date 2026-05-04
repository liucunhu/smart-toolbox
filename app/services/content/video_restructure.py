"""
视频结构重组服务
完整实现：视频片段分析 + 智能重组 + 插帧/抽帧处理
"""
import os
import cv2
import numpy as np
import random
from typing import List, Dict, Tuple
from pathlib import Path
from app.utils.logger import logger


class VideoRestructureService:
    """视频结构重组服务"""
    
    def __init__(self):
        self.output_dir = "output/restructured_videos"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def analyze_video_segments(self, video_path: str) -> List[Dict]:
        """
        分析视频片段，提取语义类型和特征
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            片段列表，每个片段包含索引、时长、起始时间、语义类型和特征
        """
        try:
            logger.info(f"开始分析视频: {video_path}")
            
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise Exception(f"无法打开视频文件: {video_path}")
            
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps if fps > 0 else 0
            
            logger.info(f"视频信息: FPS={fps}, 总帧数={total_frames}, 时长={duration:.2f}秒")
            
            # 检测场景切换点
            scene_changes = self._detect_scene_changes(cap, total_frames)
            
            # 分割片段并分析
            segments = []
            for i, (start_frame, end_frame) in enumerate(scene_changes):
                start_time = start_frame / fps
                end_time = end_frame / fps
                segment_duration = end_time - start_time
                
                # 提取片段特征
                features = self._extract_segment_features(cap, start_frame, end_frame)
                
                # 判断语义类型
                semantic_type = self._classify_segment(features)
                
                segments.append({
                    "index": i,
                    "start_time": round(start_time, 2),
                    "end_time": round(end_time, 2),
                    "duration": round(segment_duration, 2),
                    "semantic_type": semantic_type,
                    "features": features
                })
            
            cap.release()
            
            logger.info(f"视频分析完成，共{len(segments)}个片段")
            return segments
            
        except Exception as e:
            logger.error(f"视频分析失败: {str(e)}", exc_info=True)
            raise
    
    def _detect_scene_changes(self, cap: cv2.VideoCapture, total_frames: int, 
                              threshold: float = 30.0) -> List[Tuple[int, int]]:
        """
        检测场景切换点
        
        Args:
            cap: 视频捕获对象
            total_frames: 总帧数
            threshold: 场景切换阈值
            
        Returns:
            场景边界列表 [(start_frame, end_frame), ...]
        """
        scene_boundaries = [(0, 0)]  # 起始帧
        
        prev_frame = None
        step = max(1, total_frames // 100)  # 每1%采样一次
        
        for frame_idx in range(0, total_frames, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            if prev_frame is not None:
                # 计算帧间差异
                diff = cv2.absdiff(prev_frame, gray)
                mean_diff = np.mean(diff)
                
                # 如果差异超过阈值，认为是场景切换
                if mean_diff > threshold:
                    scene_boundaries[-1] = (scene_boundaries[-1][0], frame_idx)
                    scene_boundaries.append((frame_idx, frame_idx))
            
            prev_frame = gray
        
        # 设置最后一个片段的结束帧
        if scene_boundaries:
            scene_boundaries[-1] = (scene_boundaries[-1][0], total_frames)
        
        return scene_boundaries
    
    def _extract_segment_features(self, cap: cv2.VideoCapture, 
                                  start_frame: int, end_frame: int) -> Dict:
        """
        提取片段特征
        
        Args:
            cap: 视频捕获对象
            start_frame: 起始帧
            end_frame: 结束帧
            
        Returns:
            特征字典
        """
        brightness_values = []
        contrast_values = []
        motion_values = []
        
        sample_count = min(10, end_frame - start_frame)
        step = max(1, (end_frame - start_frame) // sample_count)
        
        prev_frame = None
        
        for frame_idx in range(start_frame, end_frame, step):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            # 转换为灰度图
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # 计算亮度
            brightness = np.mean(gray)
            brightness_values.append(brightness)
            
            # 计算对比度
            contrast = np.std(gray)
            contrast_values.append(contrast)
            
            # 计算运动强度
            if prev_frame is not None:
                motion = cv2.absdiff(prev_frame, gray)
                motion_intensity = np.mean(motion)
                motion_values.append(motion_intensity)
            
            prev_frame = gray
        
        return {
            "brightness": float(np.mean(brightness_values)) if brightness_values else 0,
            "contrast": float(np.mean(contrast_values)) if contrast_values else 0,
            "motion": float(np.mean(motion_values)) if motion_values else 0
        }
    
    def _classify_segment(self, features: Dict) -> str:
        """
        根据特征分类片段语义类型
        
        Args:
            features: 特征字典
            
        Returns:
            语义类型字符串
        """
        brightness = features["brightness"]
        contrast = features["contrast"]
        motion = features["motion"]
        
        # 分类规则
        if motion < 5 and brightness > 128:
            return "static_bright"  # 静态明亮
        elif motion < 5 and brightness <= 128:
            return "static_dark"   # 静态暗
        elif motion > 20:
            return "action"        # 动作场景
        else:
            return "normal"        # 普通场景
    
    def restructure_video(self, video_path: str, segments: List[Dict],
                         reorder_probability: float = 0.7,
                         insert_interval: int = 50) -> Dict:
        """
        重组视频：打乱片段顺序 + 插帧/抽帧
        
        Args:
            video_path: 原始视频路径
            segments: 片段列表
            reorder_probability: 打乱概率 (0-1)
            insert_interval: 插帧间隔
            
        Returns:
            重组结果字典
        """
        try:
            logger.info(f"开始重组视频: {video_path}")
            
            # 打开视频
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                raise Exception(f"无法打开视频文件: {video_path}")
            
            # 获取视频属性
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 生成输出文件名
            output_filename = f"restructured_{os.path.basename(video_path)}"
            output_path = os.path.join(self.output_dir, output_filename)
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            # 打乱片段顺序（非逻辑依赖片段）
            reordered_segments = self._reorder_segments(segments, reorder_probability)
            
            # 按新顺序写入视频帧
            total_written_frames = 0
            for segment in reordered_segments:
                start_frame = int(segment["start_time"] * fps)
                end_frame = int(segment["end_time"] * fps)
                
                for frame_idx in range(start_frame, end_frame):
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    
                    if not ret:
                        break
                    
                    # 写入原帧
                    out.write(frame)
                    total_written_frames += 1
                    
                    # 插帧：每隔insert_interval帧插入一帧重复帧
                    if insert_interval > 0 and total_written_frames % insert_interval == 0:
                        out.write(frame)
                        total_written_frames += 1
                    
                    # 抽帧：5%概率跳过某些帧
                    if random.random() < 0.05:
                        continue
            
            # 释放资源
            cap.release()
            out.release()
            
            logger.info(f"视频重组完成: {output_path}")
            
            # 构建片段详情
            segments_detail = []
            for new_idx, segment in enumerate(reordered_segments):
                segments_detail.append({
                    "index": segment["index"],
                    "new_index": new_idx,
                    "duration": segment["duration"],
                    "semantic_type": segment["semantic_type"]
                })
            
            return {
                "status": "success",
                "original_segments": len(segments),
                "reordered_segments": len(reordered_segments),
                "output_path": output_path,
                "segments_detail": segments_detail
            }
            
        except Exception as e:
            logger.error(f"视频重组失败: {str(e)}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _reorder_segments(self, segments: List[Dict], probability: float) -> List[Dict]:
        """
        打乱片段顺序
        
        Args:
            segments: 原始片段列表
            probability: 打乱概率
            
        Returns:
            打乱后的片段列表
        """
        if not segments or probability <= 0:
            return segments
        
        # 复制片段列表
        reordered = segments.copy()
        
        # 按语义类型分组
        type_groups = {}
        for segment in reordered:
            seg_type = segment["semantic_type"]
            if seg_type not in type_groups:
                type_groups[seg_type] = []
            type_groups[seg_type].append(segment)
        
        # 在同类片段内部随机打乱
        for seg_type in type_groups:
            if random.random() < probability:
                random.shuffle(type_groups[seg_type])
        
        # 重新组合
        result = []
        for segment in reordered:
            seg_type = segment["semantic_type"]
            if type_groups[seg_type]:
                result.append(type_groups[seg_type].pop(0))
        
        return result
