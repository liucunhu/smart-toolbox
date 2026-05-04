"""
AI视频结构重组引擎
完整实现：视频片段语义分析 + 自动打乱 + 插帧抽帧
"""
import cv2
import numpy as np
import ffmpeg
import os
import random
from typing import List, Dict, Tuple
from app.utils.logger import logger

class AIRestructuringEngine:
    """AI视频结构重组引擎"""
    
    def __init__(self, output_dir: str = "output/restructure"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 重组配置
        self.config = {
            "segment_min_duration": 2.0,  # 最小片段时长（秒）
            "segment_max_duration": 10.0, # 最大片段时长
            "reorder_probability": 0.7,   # 打乱概率
            "insert_frame_interval": 50,  # 插帧间隔
        }
    
    def analyze_video_segments(self, video_path: str) -> List[Dict]:
        """
        视频片段语义分析
        :param video_path: 视频路径
        :return: 片段列表
        """
        try:
            logger.info(f"开始分析视频片段: {video_path}")
            
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"无法打开视频: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = total_frames / fps
            
            # 检测场景切换点
            cut_points = self._detect_cut_points(cap, total_frames, fps)
            
            # 分割片段
            segments = []
            cut_points = [0] + cut_points + [total_frames]
            
            for i in range(len(cut_points) - 1):
                start_frame = cut_points[i]
                end_frame = cut_points[i + 1]
                
                segment_duration = (end_frame - start_frame) / fps
                
                # 过滤过短的片段
                if segment_duration >= self.config["segment_min_duration"]:
                    # 提取片段特征
                    features = self._extract_segment_features(cap, start_frame, end_frame)
                    
                    segments.append({
                        "index": i,
                        "start_frame": start_frame,
                        "end_frame": end_frame,
                        "start_time": start_frame / fps,
                        "end_time": end_frame / fps,
                        "duration": segment_duration,
                        "features": features,
                        "semantic_type": self._classify_segment(features)
                    })
            
            cap.release()
            
            logger.info(f"视频片段分析完成，共 {len(segments)} 个片段")
            return segments
            
        except Exception as e:
            logger.error(f"视频片段分析失败: {str(e)}")
            raise
    
    def _detect_cut_points(self, cap: cv2.VideoCapture, total_frames: int, fps: float) -> List[int]:
        """检测场景切换点"""
        cut_points = []
        prev_frame = None
        threshold = 50.0  # 场景切换阈值
        
        # 采样间隔（每秒检测一次）
        sample_interval = int(fps)
        
        for frame_idx in range(0, total_frames, sample_interval):
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if not ret:
                break
            
            if prev_frame is not None:
                # 计算帧差异
                gray_current = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                gray_prev = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
                
                diff = cv2.absdiff(gray_current, gray_prev)
                diff_score = np.sum(diff) / (frame.shape[0] * frame.shape[1])
                
                # 检测场景切换
                if diff_score > threshold:
                    cut_points.append(frame_idx)
            
            prev_frame = frame
        
        return cut_points
    
    def _extract_segment_features(self, cap: cv2.VideoCapture, start: int, end: int) -> Dict:
        """提取片段特征"""
        # 提取关键帧
        cap.set(cv2.CAP_PROP_POS_FRAMES, start)
        ret, frame = cap.read()
        
        if not ret:
            return {"brightness": 0, "contrast": 0, "motion": 0}
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 亮度
        brightness = np.mean(gray)
        
        # 对比度
        contrast = np.std(gray)
        
        # 运动强度（简化版）
        cap.set(cv2.CAP_PROP_POS_FRAMES, end - 1)
        ret, end_frame = cap.read()
        if ret:
            gray_end = cv2.cvtColor(end_frame, cv2.COLOR_BGR2GRAY)
            motion = np.sum(cv2.absdiff(gray, gray_end)) / (frame.shape[0] * frame.shape[1])
        else:
            motion = 0
        
        return {
            "brightness": brightness,
            "contrast": contrast,
            "motion": motion
        }
    
    def _classify_segment(self, features: Dict) -> str:
        """片段语义分类"""
        brightness = features["brightness"]
        motion = features["motion"]
        
        if brightness > 180 and motion < 20:
            return "static_bright"  # 静态明亮
        elif brightness < 80 and motion < 20:
            return "static_dark"   # 静态暗
        elif motion > 50:
            return "action"         # 动作场景
        else:
            return "normal"         # 普通场景
    
    def reorder_segments(self, segments: List[Dict]) -> List[Dict]:
        """
        非逻辑依赖片段自动打乱
        :param segments: 片段列表
        :return: 重新排序的片段列表
        """
        try:
            logger.info(f"开始重新排序 {len(segments)} 个片段")
            
            if random.random() > self.config["reorder_probability"]:
                logger.info("随机数不满足打乱条件，保持原顺序")
                return segments
            
            # 分类片段
            by_type = {}
            for seg in segments:
                seg_type = seg["semantic_type"]
                if seg_type not in by_type:
                    by_type[seg_type] = []
                by_type[seg_type].append(seg)
            
            # 同类片段内部打乱
            reordered = []
            for seg_type, type_segments in by_type.items():
                if len(type_segments) > 1:
                    random.shuffle(type_segments)
                reordered.extend(type_segments)
            
            # 按时间顺序重新编号
            reordered.sort(key=lambda x: x["start_time"])
            for i, seg in enumerate(reordered):
                seg["new_index"] = i
            
            logger.info(f"片段重新排序完成")
            return reordered
            
        except Exception as e:
            logger.error(f"片段排序失败: {str(e)}")
            return segments
    
    def insert_extract_frames(self, video_path: str) -> str:
        """
        插帧/抽帧处理（每50帧插入或删除1帧）
        :param video_path: 视频路径
        :return: 处理后的视频路径
        """
        try:
            logger.info(f"开始插帧/抽帧处理: {video_path}")
            
            output_path = os.path.join(
                self.output_dir,
                f"restructured_{os.path.basename(video_path)}"
            )
            
            cap = cv2.VideoCapture(video_path)
            
            if not cap.isOpened():
                raise ValueError(f"无法打开视频: {video_path}")
            
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            
            writer = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
            
            frame_count = 0
            processed_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 插帧逻辑：每50帧插入前一帧的复制
                if frame_count > 0 and frame_count % self.config["insert_frame_interval"] == 0:
                    writer.write(frame)  # 插入重复帧
                    processed_count += 1
                
                # 抽帧逻辑：随机删除某些帧（5%概率）
                if random.random() < 0.05:
                    frame_count += 1
                    continue
                
                writer.write(frame)
                frame_count += 1
                processed_count += 1
            
            cap.release()
            writer.release()
            
            logger.info(f"插帧/抽帧处理完成，共处理 {processed_count} 帧")
            return output_path
            
        except Exception as e:
            logger.error(f"插帧/抽帧处理失败: {str(e)}")
            raise
    
    def restructure_video(self, video_path: str) -> Dict:
        """
        完整的视频重组流程
        :param video_path: 视频路径
        :return: 处理结果
        """
        try:
            # 1. 分析片段
            segments = self.analyze_video_segments(video_path)
            
            # 2. 重新排序
            reordered_segments = self.reorder_segments(segments)
            
            # 3. 插帧/抽帧
            output_path = self.insert_extract_frames(video_path)
            
            return {
                "status": "success",
                "original_segments": len(segments),
                "reordered_segments": len(reordered_segments),
                "output_path": output_path,
                "segments_detail": reordered_segments
            }
            
        except Exception as e:
            logger.error(f"视频重组失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
