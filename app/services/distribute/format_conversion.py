import ffmpeg
import os
from app.utils.logger import logger

class FormatConverter:
    """多平台格式自适应转换器"""

    PLATFORM_SPECS = {
        "douyin": {"width": 1080, "height": 1920, "crf": 23, "fps": 30},
        "xiaohongshu": {"width": 1080, "height": 1440, "crf": 22, "fps": 30}, # 3:4
        "bilibili": {"width": 1920, "height": 1080, "crf": 20, "fps": 60},
    }

    @staticmethod
    def convert_video(input_path: str, platform: str) -> str:
        """根据平台要求转换视频格式"""
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"视频文件不存在: {input_path}")

        spec = FormatConverter.PLATFORM_SPECS.get(platform)
        if not spec:
            logger.warning(f"未找到平台 {platform} 的规格配置，使用默认抖音配置")
            spec = FormatConverter.PLATFORM_SPECS["douyin"]

        output_path = input_path.replace(".mp4", f"_{platform}.mp4")
        
        try:
            logger.info(f"正在将视频转换为 {platform} 格式: {spec['width']}x{spec['height']}")
            
            # 使用 FFmpeg 进行缩放和编码
            # scale: 强制分辨率, crf: 质量控制 (越小质量越高), preset: 编码速度
            stream = ffmpeg.input(input_path)
            stream = ffmpeg.filter(stream, 'scale', spec['width'], spec['height'], force_original_aspect_ratio='decrease')
            stream = ffmpeg.filter(stream, 'pad', spec['width'], spec['height'], '(ow-iw)/2', '(oh-ih)/2') # 居中填充
            
            out = ffmpeg.output(
                stream, 
                output_path,
                vcodec='libx264',
                acodec='aac',
                r=spec['fps'],
                crf=spec['crf'],
                preset='fast'
            )
            
            ffmpeg.run(out, overwrite_output=True, quiet=False) # quiet=False 以便在控制台看到进度
            logger.info(f"格式转换成功: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"视频格式转换失败: {str(e)}")
            raise e
