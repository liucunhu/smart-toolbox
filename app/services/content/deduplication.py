import cv2
import ffmpeg
import random
import os
import numpy as np
from pathlib import Path
from app.utils.logger import logger
# from paddleocr import PaddleOCR # 引入 OCR 引擎

class VideoDeduplicationEngine:
    """智能视频去重与伪原创引擎"""

    def __init__(self, input_path: str, output_dir: str = "output/videos"):
        self.input_path = input_path
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)
        
        # 生成唯一的输出文件名
        self.output_path = os.path.join(output_dir, f"dedup_{os.path.basename(input_path)}")

    def _apply_visual_noise(self, cap: cv2.VideoCapture, writer: cv2.VideoWriter):
        """应用视觉层去重：镜像、缩放、色彩扰动及随机帧抽取"""
        frame_count = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # 1. 随机帧抽取 (每 30 帧跳过 1 帧，打破指纹连续性)
            if frame_count % 30 == 0 and frame_count != 0:
                continue
            frame_count += 1

            # 2. 随机镜像 (50% 概率)
            if random.random() > 0.5:
                frame = cv2.flip(frame, 1)

            # 3. 微缩放 (1.0 - 1.1 倍)
            scale_factor = 1 + random.uniform(0, 0.1)
            h, w = frame.shape[:2]
            new_h, new_w = int(h * scale_factor), int(w * scale_factor)
            frame = cv2.resize(frame, (new_w, new_h))
            
            # 裁剪回原始尺寸（保持中心）
            start_y = (new_h - h) // 2
            start_x = (new_w - w) // 2
            frame = frame[start_y:start_y+h, start_x:start_x+w]

            # 4. 色彩微调 (亮度/对比度)
            alpha = random.uniform(0.95, 1.05)  # 对比度
            beta = random.uniform(-5, 5)        # 亮度
            frame = cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

            # 5. 叠加极淡的随机噪点 (肉眼难辨但能改变哈希值)
            noise = np.random.normal(0, 1, frame.shape).astype(np.float32)
            frame = cv2.addWeighted(frame.astype(np.float32), 0.98, noise, 0.02, 0).astype(np.uint8)

            writer.write(frame)

    def _apply_audio_shift(self):
        """应用音频层去重：变速变调"""
        # 使用 ffmpeg-python 进行音频微调
        # atempo: 速度 (0.95-1.05), asetrate: 采样率调整以改变音调
        try:
            speed = random.uniform(0.98, 1.02)
            stream = ffmpeg.input(self.output_path)
            audio = stream.audio.filter('atempo', speed)
            video = stream.video
            
            temp_path = self.output_path.replace(".mp4", "_temp.mp4")
            out = ffmpeg.output(video, audio, temp_path)
            ffmpeg.run(out, overwrite_output=True, quiet=True)
            
            # 替换原文件
            os.remove(self.output_path)
            os.rename(temp_path, self.output_path)
            logger.info(f"音频变速处理完成: {speed:.2f}x")
        except Exception as e:
            logger.warning(f"音频处理跳过或失败: {str(e)}")

    def process(self) -> str:
        """执行完整的去重流程"""
        logger.info(f"开始对视频进行去重处理: {self.input_path}")
        
        cap = cv2.VideoCapture(self.input_path)
        if not cap.isOpened():
            raise Exception(f"无法打开视频文件: {self.input_path}")

        # 获取视频属性
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        writer = cv2.VideoWriter(self.output_path, fourcc, fps, (width, height))

        # 1. 执行视觉处理
        self._apply_visual_noise(cap, writer)

        cap.release()
        writer.release()

        # 2. 执行音频处理
        self._apply_audio_shift()

        # 3. 元数据清洗 (通过 FFmpeg 重新封装)
        final_path = self.output_path.replace(".mp4", "_final.mp4")
        try:
            stream = ffmpeg.input(self.output_path)
            out = ffmpeg.output(stream, final_path, map_metadata="-1", c="copy")
            ffmpeg.run(out, overwrite_output=True, quiet=True)
            os.remove(self.output_path)
            logger.info(f"去重完成，最终文件路径: {final_path}")
        except Exception as e:
            logger.error(f"元数据清洗失败: {str(e)}")
            return self.output_path

        return final_path
