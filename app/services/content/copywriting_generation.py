from openai import OpenAI
from app.core.config import settings
from app.utils.logger import logger
from typing import Optional

class CopywritingGenerator:
    """平台差异化文案生成器"""

    def __init__(self):
        # 根据配置选择 AI 提供商
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "siliconflow":
            self.client = OpenAI(
                api_key=settings.SILICONFLOW_API_KEY,
                base_url=settings.SILICONFLOW_BASE_URL
            )
            self.model = settings.SILICONFLOW_MODEL
        elif provider == "modelscope":
            self.client = OpenAI(
                api_key=settings.MODELSCOPE_API_KEY,
                base_url=settings.MODELSCOPE_BASE_URL
            )
            self.model = settings.MODELSCOPE_MODEL
        elif provider == "deepseek":
            self.client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com/v1"
            )
            self.model = "deepseek-chat"
        else:  # openai
            self.client = OpenAI(
                api_key=settings.OPENAI_API_KEY
            )
            self.model = "gpt-3.5-turbo"
        
        logger.info(f"AI 文案生成器已初始化，使用提供商: {provider}")

    def _get_platform_prompt(self, platform: str, topic: str) -> str:
        """根据平台获取特定的 System Prompt"""
        prompts = {
            "douyin": f"""
            你是一位抖音爆款脚本大师。请为话题 '{topic}' 创作一个短视频脚本。
            要求：
            1. 开头前3秒必须有强烈的悬念或冲突（黄金3秒）。
            2. 语言口语化，节奏快，每200字设置一个情绪高点。
            3. 结尾必须引导用户评论和点赞。
            """,
            "xiaohongshu": f"""
            你是一位小红书种草达人。请为话题 '{topic}' 创作一篇笔记文案。
            要求：
            1. 标题采用"二段式"，包含吸引人的关键词。
            2. 正文大量使用 Emoji 表情，语气亲切真实。
            3. 文末添加 10 个相关的垂直领域标签（Hashtags）。
            """,
            "bilibili": f"""
            你是一位 B站资深 UP 主。请为话题 '{topic}' 创作一个深度解析视频大纲。
            要求：
            1. 融入 B站流行梗，语气幽默且有干货密度。
            2. 结构清晰，适合中长视频（3-10分钟）。
            3. 结尾引导"一键三连"。
            """,
            "toutiao": f"""
            你是一位今日头条爆款文章写手。请为话题 '{topic}' 创作一篇深度文章。
            要求：
            1. 标题采用"悬念式"或"数字式"，吸引点击（如：90%的人都不知道...）
            2. 正文 1500-2500 字，分段清晰，每段有小标题
            3. 融入热点关键词，提升推荐权重
            4. 语言通俗易懂，避免学术化表达
            5. 结尾引导评论互动，提出开放式问题
            6. 输出格式：
               - 标题：[文章标题]
               - 分类：[适合的分类，如科技/生活/财经]
               - 正文：[完整文章内容]
               - 标签：[3-5个关键词]
            """
        }
        return prompts.get(platform, prompts["douyin"])

    def generate_script(self, platform: str, topic: str) -> Optional[dict]:
        """生成脚本内容"""
        try:
            system_prompt = self._get_platform_prompt(platform, topic)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"请开始创作关于 {topic} 的内容"}
                ],
                temperature=0.8  # 提高创造性
            )
            
            content = response.choices[0].message.content
            logger.info(f"成功为平台 {platform} 生成内容，长度: {len(content)}")
            
            # 针对头条文章进行结构化解析
            if platform == "toutiao":
                result = {
                    "title": "",
                    "category": "",
                    "content": content,
                    "tags": [],
                    "platform": platform,
                    "topic": topic
                }
                
                # 简单的标题提取逻辑
                for line in content.split('\n'):
                    if '标题：' in line:
                        result["title"] = line.replace('标题：', '').strip()
                    elif '分类：' in line:
                        result["category"] = line.replace('分类：', '').strip()
                    elif '标签：' in line:
                        tags_str = line.replace('标签：', '').strip()
                        result["tags"] = [tag.strip() for tag in tags_str.split(',')]
                
                return result
            else:
                return {
                    "script": content,
                    "platform": platform,
                    "topic": topic
                }

        except Exception as e:
            logger.error(f"AI 内容生成失败: {str(e)}")
            return None
