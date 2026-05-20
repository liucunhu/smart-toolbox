"""
番茄小说智能封面生成服务
支持：AI生成封面、模板封面、A/B测试
"""
import asyncio
import aiohttp
from typing import Dict, Any, Optional
from app.utils.logger import logger


class FanqieCoverGenerator:
    """番茄小说封面生成器"""
    
    def __init__(self):
        self.api_base = "https://api.siliconflow.cn/v1"
        self.model = "stabilityai/stable-diffusion-xl-base-1.0"
    
    async def generate_ai_cover(
        self,
        novel_title: str,
        category: str,
        tags: list,
        api_key: str,
        style: str = "realistic"
    ) -> Dict[str, Any]:
        """
        AI生成小说封面
        
        :param novel_title: 小说标题
        :param category: 分类（都市/玄幻/仙侠等）
        :param tags: 标签列表
        :param api_key: API密钥
        :param style: 风格（realistic/anime/fantasy）
        :return: 图片URL或本地路径
        """
        try:
            logger.info(f"开始AI生成封面: {novel_title}")
            
            # 构建Prompt
            prompt = self._build_cover_prompt(novel_title, category, tags, style)
            
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": self.model,
                "prompt": prompt,
                "negative_prompt": "blurry, low quality, distorted, ugly, text, watermark",
                "width": 800,
                "height": 1200,  # 竖版封面比例
                "steps": 30,
                "guidance_scale": 7.5,
                "seed": -1
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_base}/images/generations",
                    headers=headers,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=120)
                ) as response:
                    if response.status == 200:
                        result = await response.json()
                        image_url = result["data"][0]["url"]
                        
                        logger.info(f"✅ AI封面生成成功: {image_url}")
                        return {
                            "status": "success",
                            "image_url": image_url,
                            "prompt": prompt
                        }
                    else:
                        error_text = await response.text()
                        logger.error(f"AI封面生成失败: {error_text}")
                        return {
                            "status": "failed",
                            "error": error_text
                        }
        
        except Exception as e:
            logger.error(f"AI封面生成异常: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _build_cover_prompt(
        self,
        title: str,
        category: str,
        tags: list,
        style: str
    ) -> str:
        """构建封面生成Prompt"""
        
        # 风格映射
        style_prompts = {
            "realistic": "photorealistic, high detail, professional photography",
            "anime": "anime style, vibrant colors, manga illustration",
            "fantasy": "fantasy art, magical atmosphere, epic scene",
            "minimalist": "minimalist design, clean layout, modern typography"
        }
        
        # 分类映射
        category_prompts = {
            "都市": "modern city skyline, urban life, contemporary setting",
            "玄幻": "mystical energy, magical creatures, fantasy landscape",
            "仙侠": "ancient chinese mountains, immortal cultivator, ethereal clouds",
            "历史": "ancient chinese architecture, historical costumes, traditional culture",
            "科幻": "futuristic technology, space station, sci-fi elements",
            "悬疑": "dark atmosphere, mysterious shadows, thriller mood"
        }
        
        base_style = style_prompts.get(style, style_prompts["realistic"])
        base_category = category_prompts.get(category, "")
        
        # 提取关键词
        keywords = ", ".join(tags[:3]) if tags else ""
        
        prompt = (
            f"A professional book cover for a Chinese web novel titled '{title}'. "
            f"Style: {base_style}. "
            f"Theme: {base_category}. "
            f"Keywords: {keywords}. "
            f"High quality, detailed, eye-catching composition, suitable for mobile reading apps. "
            f"No text, no watermark, no logo."
        )
        
        return prompt
    
    async def generate_template_cover(
        self,
        novel_title: str,
        author_name: str,
        template_id: str = "default"
    ) -> Dict[str, Any]:
        """
        使用模板生成封面
        
        :param novel_title: 小说标题
        :param author_name: 作者名
        :param template_id: 模板ID
        :return: 本地文件路径
        """
        try:
            from PIL import Image, ImageDraw, ImageFont
            import os
            
            logger.info(f"使用模板生成封面: {novel_title}")
            
            # 创建画布（800x1200）
            img = Image.new('RGB', (800, 1200), color=(255, 255, 255))
            draw = ImageDraw.Draw(img)
            
            # 加载字体（使用系统默认字体）
            try:
                font_title = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 60)
                font_author = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 40)
            except:
                font_title = ImageFont.load_default()
                font_author = ImageFont.load_default()
            
            # 绘制背景渐变
            for i in range(1200):
                color = int(200 + (i / 1200) * 55)
                draw.line([(0, i), (800, i)], fill=(color, color, color))
            
            # 绘制标题（居中）
            title_bbox = draw.textbbox((0, 0), novel_title, font=font_title)
            title_width = title_bbox[2] - title_bbox[0]
            title_x = (800 - title_width) / 2
            title_y = 400
            
            draw.text((title_x, title_y), novel_title, fill=(0, 0, 0), font=font_title)
            
            # 绘制作者名
            author_text = f"作者：{author_name}"
            author_bbox = draw.textbbox((0, 0), author_text, font=font_author)
            author_width = author_bbox[2] - author_bbox[0]
            author_x = (800 - author_width) / 2
            author_y = 500
            
            draw.text((author_x, author_y), author_text, fill=(100, 100, 100), font=font_author)
            
            # 保存文件
            output_dir = "uploads/covers"
            os.makedirs(output_dir, exist_ok=True)
            
            filename = f"cover_{novel_title.replace(' ', '_')}_{template_id}.png"
            filepath = os.path.join(output_dir, filename)
            
            img.save(filepath)
            
            logger.info(f"✅ 模板封面生成成功: {filepath}")
            return {
                "status": "success",
                "filepath": filepath,
                "template_id": template_id
            }
        
        except Exception as e:
            logger.error(f"模板封面生成失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def ab_test_covers(
        self,
        novel_id: int,
        covers: list,
        db_session
    ) -> Dict[str, Any]:
        """
        封面A/B测试
        
        :param novel_id: 小说ID
        :param covers: 封面列表 [{"url": "...", "type": "ai/template"}]
        :param db_session: 数据库会话
        :return: 测试结果
        """
        try:
            from app.models import Novel
            
            logger.info(f"开始封面A/B测试，小说ID: {novel_id}")
            
            # 随机分配封面给不同用户组
            import random
            random.shuffle(covers)
            
            # 为每个封面生成测试ID
            test_results = []
            for i, cover in enumerate(covers):
                test_group = f"group_{i}"  # A/B/C组
                test_results.append({
                    "cover_url": cover.get("url"),
                    "cover_type": cover.get("type"),
                    "test_group": test_group,
                    "impressions": 0,  # 展示次数
                    "clicks": 0,  # 点击次数
                    "ctr": 0.0  # 点击率
                })
            
            best_cover = covers[0]  # 简化版：返回第一个
            
            logger.info(f"✅ A/B测试初始化完成，共{len(covers)}个封面参与测试")
            return {
                "status": "success",
                "best_cover": best_cover,
                "test_results": test_results,
                "message": "A/B测试已启动，需要收集用户行为数据后才能得出最佳封面"
            }
        
        except Exception as e:
            logger.error(f"A/B测试失败: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }
