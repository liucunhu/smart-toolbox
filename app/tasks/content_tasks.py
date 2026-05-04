from app.tasks.celery_app import celery_app
from app.services.content.copywriting_generation import CopywritingGenerator
from app.services.content.deduplication import VideoDeduplicationEngine
from app.services.distribute.format_conversion import FormatConverter
from app.utils.logger import logger

@celery_app.task
def generate_script_task(topic: str, platform: str):
    """异步生成爆款脚本"""
    generator = CopywritingGenerator()
    script = generator.generate_script(platform, topic)
    return {"topic": topic, "script": script}

@celery_app.task
def process_video_task(input_path: str, platform: str):
    """异步执行视频去重与格式转换"""
    try:
        # 1. 智能去重
        dedup_engine = VideoDeduplicationEngine(input_path=input_path)
        deduped_path = dedup_engine.process()

        # 2. 格式转换
        converter = FormatConverter()
        final_path = converter.convert_video(deduped_path, platform)

        logger.info(f"视频处理完成: {final_path}")
        return {"status": "success", "path": final_path}
    except Exception as e:
        logger.error(f"视频处理失败: {str(e)}")
        return {"status": "failed", "error": str(e)}
