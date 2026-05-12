"""
AI配图自动生成引擎
支持多个AI图像生成API，根据文案自动生成相关插图
"""
import httpx
import base64
import os
from typing import Dict, List, Optional
from pathlib import Path
from app.utils.logger import logger
from app.core.config import settings
from sqlalchemy.orm import Session


class ImageGenerator:
    """AI图像生成器"""
    
    def __init__(self, db: Session = None):
        """
        初始化图像生成器
        
        Args:
            db: 数据库会话（可选）。如果不提供，将尝试从数据库获取默认配置；
                如果数据库配置不可用，则回退到配置文件。
        """
        self.db = db
        self.output_dir = "output/images"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 支持的图像生成提供商
        self.providers = {
            "modelscope": self._generate_with_modelscope,
            "siliconflow": self._generate_with_siliconflow,
            "dashscope": self._generate_with_dashscope
        }
        
        # ✅ 优先使用数据库配置的提供商，如果没有则使用modelscope
        self.default_provider = self._get_default_provider()
    
    def _get_default_provider(self) -> str:
        """获取默认图像生成提供商"""
        if not self.db:
            return "modelscope"
        
        try:
            from app.services.system.config_service import LLMConfigService
            llm_service = LLMConfigService(self.db)
            config = llm_service.get_default_llm_config("image_generation")
            
            if config:
                logger.info(f"✅ 使用数据库配置的图像提供商: {config.provider.value}")
                return config.provider.value
        except Exception as e:
            logger.warning(f"从数据库获取图像配置失败: {e}")
        
        return "modelscope"
    
    def _get_image_config(self, provider: str):
        """
        从数据库或配置文件获取图像生成配置
        
        Returns:
            (api_key, base_url, image_model)
        """
        # 尝试从数据库获取
        if self.db:
            try:
                from app.services.system.config_service import LLMConfigService
                llm_service = LLMConfigService(self.db)
                config = llm_service.get_llm_config(provider, "image_generation", is_default=True)
                
                if config:
                    return config.api_key, config.base_url, config.image_model_name or config.model_name
            except Exception as e:
                logger.warning(f"从数据库获取{provider}配置失败: {e}")
        
        # 回退到配置文件
        if provider == "siliconflow":
            return (
                getattr(settings, 'SILICONFLOW_API_KEY', ''),
                settings.SILICONFLOW_BASE_URL,
                'Tongyi-MAI/Z-Image-Turbo'
            )
        elif provider == "dashscope":
            return (
                getattr(settings, 'DASHSCOPE_API_KEY', ''),
                settings.DASHSCOPE_BASE_URL,
                'wanx2.1-t2i-turbo'
            )
        elif provider == "modelscope":
            return (
                getattr(settings, 'MODELSCOPE_API_KEY', ''),
                settings.MODELSCOPE_BASE_URL,
                'black-forest-labs/FLUX.1-schnell'
            )
        
        return '', '', ''
    
    async def generate_image(
        self,
        prompt: str,
        style: str = "realistic",
        aspect_ratio: str = "16:9",
        provider: str = None
    ) -> Dict:
        """
        生成AI图像
        
        Args:
            prompt: 图像描述提示词
            style: 风格（realistic/illustration/cartoon/anime/oil_painting）
            aspect_ratio: 宽高比（16:9/9:16/1:1/3:4）
            provider: 图像生成提供商
        
        Returns:
            {
                "status": "success",
                "image_path": "output/images/xxx.png",
                "image_url": "http://localhost:8000/images/xxx.png",
                "prompt_used": "...",
                "style": "..."
            }
        """
        try:
            if not provider:
                provider = self.default_provider
            
            logger.info(f"开始生成图像，提示词: {prompt[:50]}...")
            
            # 优化提示词
            optimized_prompt = self._optimize_prompt(prompt, style)
            
            # 调用对应的生成器
            if provider in self.providers:
                result = await self.providers[provider](optimized_prompt, aspect_ratio)
                
                if result["status"] == "success":
                    logger.info(f"图像生成成功: {result['image_path']}")
                    return result
                else:
                    logger.error(f"图像生成失败: {result.get('error')}")
                    return result
            else:
                return {
                    "status": "failed",
                    "error": f"不支持的提供商: {provider}"
                }
        
        except Exception as e:
            logger.error(f"图像生成异常: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def generate_images_batch(
        self,
        prompts: List[str],
        style: str = "realistic",
        aspect_ratio: str = "16:9"
    ) -> List[Dict]:
        """批量生成图像"""
        results = []
        
        for i, prompt in enumerate(prompts):
            logger.info(f"生成第{i+1}/{len(prompts)}张图像...")
            result = await self.generate_image(prompt, style, aspect_ratio)
            results.append(result)
        
        return results
    
    async def generate_from_article(
        self,
        article_content: str,
        num_images: int = 3,
        style: str = "realistic"
    ) -> List[Dict]:
        """
        从文章内容提取关键点并生成配图
        
        Args:
            article_content: 文章正文
            num_images: 生成图片数量
            style: 风格
        
        Returns:
            生成的图像列表
        """
        try:
            # 提取关键段落
            key_points = self._extract_key_points(article_content, num_images)
            
            # 为每个关键点生成图像
            images = []
            for point in key_points:
                prompt = f"Illustration about: {point}, professional, high quality"
                result = await self.generate_image(prompt, style)
                
                if result["status"] == "success":
                    images.append({
                        **result,
                        "related_text": point
                    })
            
            logger.info(f"从文章生成了{len(images)}张配图")
            return images
        
        except Exception as e:
            logger.error(f"文章配图生成失败: {str(e)}")
            return []
    
    def _optimize_prompt(self, prompt: str, style: str) -> str:
        """优化提示词，添加风格描述"""
        style_descriptions = {
            "realistic": "photorealistic, high detail, 8k, professional photography",
            "illustration": "digital illustration, clean lines, modern design, vector art",
            "cartoon": "cartoon style, colorful, playful, friendly",
            "anime": "anime style, vibrant colors, detailed eyes, Japanese animation",
            "oil_painting": "oil painting style, artistic, textured, classical art",
            "watercolor": "watercolor painting, soft colors, artistic, flowing",
            "minimalist": "minimalist design, clean, simple, modern, white background"
        }
        
        style_desc = style_descriptions.get(style, style_descriptions["realistic"])
        optimized = f"{prompt}, {style_desc}, best quality, masterpiece"
        
        return optimized
    
    def _extract_key_points(self, content: str, num_points: int) -> List[str]:
        """从文章内容提取关键点"""
        # 简单实现：按段落分割，选择前N个非空段落
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        
        # 过滤掉太短的段落
        meaningful_paragraphs = [p for p in paragraphs if len(p) > 50]
        
        # 返回前N个关键点
        return meaningful_paragraphs[:num_points]
    
    async def _generate_with_stability(self, prompt: str, aspect_ratio: str) -> Dict:
        """使用Stability AI生成图像"""
        try:
            api_key = getattr(settings, 'STABILITY_AI_API_KEY', '')
            if not api_key:
                return {
                    "status": "failed",
                    "error": "未配置Stability AI API密钥"
                }
            
            # 解析宽高比
            width, height = self._parse_aspect_ratio(aspect_ratio)
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    },
                    json={
                        "text_prompts": [{"text": prompt}],
                        "cfg_scale": 7,
                        "height": height,
                        "width": width,
                        "steps": 30,
                        "samples": 1
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "status": "failed",
                        "error": f"API请求失败: {response.text}"
                    }
                
                data = response.json()
                
                # 保存图像
                image_data = base64.b64decode(data["artifacts"][0]["base64"])
                image_path = self._save_image(image_data, "stability")
                
                return {
                    "status": "success",
                    "image_path": image_path,
                    "image_url": f"/images/{os.path.basename(image_path)}",
                    "prompt_used": prompt,
                    "provider": "stability_ai"
                }
        
        except Exception as e:
            logger.error(f"Stability AI生成失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _generate_with_dalle(self, prompt: str, aspect_ratio: str) -> Dict:
        """使用DALL-E 3生成图像"""
        try:
            api_key = getattr(settings, 'OPENAI_API_KEY', '')
            if not api_key:
                return {
                    "status": "failed",
                    "error": "未配置OpenAI API密钥"
                }
            
            # DALL-E 3只支持特定尺寸
            size_map = {
                "16:9": "1792x1024",
                "9:16": "1024x1792",
                "1:1": "1024x1024"
            }
            size = size_map.get(aspect_ratio, "1024x1024")
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "dall-e-3",
                        "prompt": prompt,
                        "n": 1,
                        "size": size,
                        "quality": "standard"
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "status": "failed",
                        "error": f"API请求失败: {response.text}"
                    }
                
                data = response.json()
                image_url = data["data"][0]["url"]
                
                # 下载并保存图像
                image_response = await client.get(image_url)
                image_path = self._save_image(image_response.content, "dalle")
                
                return {
                    "status": "success",
                    "image_path": image_path,
                    "image_url": f"/images/{os.path.basename(image_path)}",
                    "prompt_used": prompt,
                    "provider": "dall_e"
                }
        
        except Exception as e:
            logger.error(f"DALL-E生成失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _generate_with_midjourney(self, prompt: str, aspect_ratio: str) -> Dict:
        """使用Midjourney生成图像（需要第三方API代理）"""
        # TODO: 实现Midjourney API集成
        return {
            "status": "failed",
            "error": "Midjourney API暂未实现"
        }
    
    async def _generate_with_siliconflow(self, prompt: str, aspect_ratio: str) -> Dict:
        """使用硅基流动生成图像（Tongyi-MAI/Z-Image-Turbo等模型）"""
        try:
            # 尝试从数据库获取配置
            api_key, base_url, image_model = self._get_image_config("siliconflow")
            
            if not api_key:
                return {
                    "status": "failed",
                    "error": "未配置硅基流动API密钥"
                }
            
            # 解析宽高比
            width, height = self._parse_aspect_ratio(aspect_ratio)
            
            logger.info(f"使用硅基流动图像模型: {image_model}")
            logger.info(f"图像尺寸: {width}x{height}")
            
            async with httpx.AsyncClient(timeout=120.0) as client:  # 图像生成需要更长时间
                response = await client.post(
                    f"{base_url}/images/generations",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": image_model,
                        "prompt": prompt,
                        "image_size": f"{width}x{height}",  # 使用x而不是*
                        "batch_size": 1,
                        "num_inference_steps": 8  # Z-Image-Turbo只需8步
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"硅基流动图像生成失败: {response.text}")
                    return {
                        "status": "failed",
                        "error": f"API请求失败: {response.text}"
                    }
                
                data = response.json()
                
                # 硅基流动返回格式: {"data": [{"url": "..."}]}
                if "data" in data and len(data["data"]) > 0:
                    image_url = data["data"][0]["url"]
                    
                    # 下载并保存图像
                    image_response = await client.get(image_url)
                    image_path = self._save_image(image_response.content, "siliconflow")
                    
                    return {
                        "status": "success",
                        "image_path": image_path,
                        "image_url": f"/images/{os.path.basename(image_path)}",
                        "prompt_used": prompt,
                        "provider": "siliconflow",
                        "model": image_model
                    }
                else:
                    return {
                        "status": "failed",
                        "error": "API返回数据格式异常"
                    }
        
        except Exception as e:
            logger.error(f"硅基流动图像生成失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _generate_with_dashscope(self, prompt: str, aspect_ratio: str) -> Dict:
        """使用阿里百炼（DashScope）生成图像（通义万相）"""
        try:
            # 尝试从数据库获取配置
            api_key, base_url, image_model = self._get_image_config("dashscope")
            
            if not api_key:
                return {
                    "status": "failed",
                    "error": "未配置阿里百炼API密钥"
                }
            
            # 解析宽高比
            width, height = self._parse_aspect_ratio(aspect_ratio)
            
            logger.info(f"使用阿里百炼图像模型: {image_model}")
            logger.info(f"图像尺寸: {width}x{height}")
            
            # 阿里百炼使用异步API，需要先创建任务，再查询结果
            async with httpx.AsyncClient(timeout=180.0) as client:
                # 步骤1: 创建图像生成任务
                # 正确的URL: https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis
                response = await client.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "X-DashScope-Async": "enable"  # 必须设置为enable
                    },
                    json={
                        "model": image_model,
                        "input": {
                            "prompt": prompt
                        },
                        "parameters": {
                            "size": f"{width}*{height}",  # 阿里百炼使用*分隔
                            "n": 1  # 生成1张
                        }
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"阿里百炼图像任务创建失败: {response.text}")
                    return {
                        "status": "failed",
                        "error": f"API请求失败: {response.text}"
                    }
                
                task_data = response.json()
                
                # 检查是否成功创建任务
                if task_data.get("output", {}).get("task_id"):
                    task_id = task_data["output"]["task_id"]
                    logger.info(f"图像生成任务已创建: {task_id}")
                    
                    # 步骤2: 轮询任务状态
                    import asyncio
                    max_retries = 30  # 最多轮询30次
                    retry_interval = 5  # 每次间隔5秒
                    
                    for i in range(max_retries):
                        await asyncio.sleep(retry_interval)
                        
                        # 查询任务状态
                        status_response = await client.get(
                            f"{base_url}/tasks/{task_id}",
                            headers={
                                "Authorization": f"Bearer {api_key}"
                            }
                        )
                        
                        if status_response.status_code != 200:
                            logger.error(f"查询任务状态失败: {status_response.text}")
                            continue
                        
                        status_data = status_response.json()
                        task_status = status_data.get("output", {}).get("task_status", "")
                        
                        logger.info(f"任务状态: {task_status} (第{i+1}次轮询)")
                        
                        if task_status == "SUCCEEDED":
                            # 任务成功，获取图像URL
                            results = status_data.get("output", {}).get("results", [])
                            if results and len(results) > 0:
                                image_url = results[0].get("url")
                                
                                if image_url:
                                    # 下载并保存图像
                                    image_response = await client.get(image_url)
                                    image_path = self._save_image(image_response.content, "dashscope")
                                    
                                    logger.info(f"✅ 阿里百炼图像生成成功: {image_path}")
                                    
                                    return {
                                        "status": "success",
                                        "image_path": image_path,
                                        "image_url": f"/images/{os.path.basename(image_path)}",
                                        "prompt_used": prompt,
                                        "provider": "dashscope",
                                        "model": image_model
                                    }
                            
                            return {
                                "status": "failed",
                                "error": "任务成功但未获取到图像URL"
                            }
                        
                        elif task_status == "FAILED":
                            error_msg = status_data.get("output", {}).get("message", "未知错误")
                            logger.error(f"❌ 图像生成任务失败: {error_msg}")
                            return {
                                "status": "failed",
                                "error": f"任务失败: {error_msg}"
                            }
                        
                        # 其他状态（PENDING/RUNNING）继续轮询
                        
                    # 超时
                    logger.error(f"❌ 图像生成超时（{max_retries * retry_interval}秒）")
                    return {
                        "status": "failed",
                        "error": f"生成超时，请稍后重试"
                    }
                
                else:
                    return {
                        "status": "failed",
                        "error": "API返回数据格式异常"
                    }
        
        except Exception as e:
            logger.error(f"阿里百炼图像生成失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def _generate_with_local_sd(self, prompt: str, aspect_ratio: str) -> Dict:
        """使用本地Stable Diffusion生成"""
        # TODO: 实现本地SD集成
        return {
            "status": "failed",
            "error": "本地Stable Diffusion暂未配置"
        }
    
    async def _generate_with_modelscope(self, prompt: str, aspect_ratio: str) -> Dict:
        """使用魔搭社区（ModelScope）生成图像（FLUX.1-schnell等模型）"""
        try:
            # 尝试从数据库获取配置
            api_key, base_url, image_model = self._get_image_config("modelscope")
            
            if not api_key:
                return {
                    "status": "failed",
                    "error": "未配置魔搭社区API密钥"
                }
            
            # 解析宽高比
            width, height = self._parse_aspect_ratio(aspect_ratio)
            
            logger.info(f"使用魔搭社区图像模型: {image_model}")
            logger.info(f"图像尺寸: {width}x{height}")
            
            # ✅ 魔搭社区使用异步调用模式
            async with httpx.AsyncClient(timeout=180.0) as client:
                # 步骤1: 创建异步任务
                response = await client.post(
                    f"{base_url}/images/generations",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json",
                        "X-ModelScope-Async-Mode": "true"  # ✅ 魔搭社区要求使用 "true"
                    },
                    json={
                        "model": image_model,
                        "prompt": prompt,
                        "n": 1,
                        "size": f"{width}x{height}"
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"魔搭社区图像任务创建失败: {response.text}")
                    return {
                        "status": "failed",
                        "error": f"API请求失败: {response.text}"
                    }
                
                task_data = response.json()
                task_id = task_data.get("task_id")
                
                if not task_id:
                    return {
                        "status": "failed",
                        "error": f"未获取到Task ID: {task_data}"
                    }
                
                logger.info(f"图像生成任务已创建: {task_id}")
                
                # 步骤2: 轮询任务状态
                import asyncio
                max_retries = 30
                retry_interval = 5
                
                for i in range(max_retries):
                    await asyncio.sleep(retry_interval)
                    
                    # 查询任务状态
                    status_response = await client.get(
                        f"{base_url}/tasks/{task_id}",
                        headers={
                            "Authorization": f"Bearer {api_key}"
                        }
                    )
                    
                    if status_response.status_code != 200:
                        logger.error(f"查询任务状态失败: {status_response.text}")
                        continue
                    
                    status_data = status_response.json()
                    task_status = status_data.get("task_status", "")
                    
                    logger.info(f"任务状态: {task_status} (第{i+1}次轮询)")
                    
                    if task_status == "SUCCEEDED":
                        # 任务成功，获取图像URL
                        results = status_data.get("results", [])
                        if results and len(results) > 0:
                            image_url = results[0].get("url")
                            
                            if image_url:
                                # 下载并保存图像
                                image_response = await client.get(image_url)
                                image_path = self._save_image(image_response.content, "modelscope")
                                
                                logger.info(f"✅ 魔搭社区图像生成成功: {image_path}")
                                
                                return {
                                    "status": "success",
                                    "image_path": image_path,
                                    "image_url": f"/images/{os.path.basename(image_path)}",
                                    "prompt_used": prompt,
                                    "provider": "modelscope",
                                    "model": image_model
                                }
                        
                        return {
                            "status": "failed",
                            "error": "任务成功但未获取到图像URL"
                        }
                    
                    elif task_status == "FAILED":
                        error_msg = status_data.get("message", "未知错误")
                        logger.error(f"❌ 图像生成任务失败: {error_msg}")
                        return {
                            "status": "failed",
                            "error": f"任务失败: {error_msg}"
                        }
                
                # 超时
                logger.error(f"❌ 图像生成超时（{max_retries * retry_interval}秒）")
                return {
                    "status": "failed",
                    "error": f"生成超时，请稍后重试"
                }
        
        except Exception as e:
            logger.error(f"魔搭社区图像生成失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _parse_aspect_ratio(self, ratio: str) -> tuple:
        """解析宽高比"""
        ratios = {
            "16:9": (1024, 576),
            "9:16": (576, 1024),
            "1:1": (1024, 1024),
            "3:4": (768, 1024),
            "4:3": (1024, 768)
        }
        return ratios.get(ratio, (1024, 576))
    
    def _save_image(self, image_data: bytes, prefix: str) -> str:
        """保存图像到本地"""
        import uuid
        filename = f"{prefix}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(self.output_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(image_data)
        
        return filepath


# 使用示例
if __name__ == "__main__":
    import asyncio
    
    async def test_image_gen():
        generator = ImageGenerator()
        
        # 生成单张图像
        result = await generator.generate_image(
            prompt="A beautiful sunset over mountains",
            style="realistic",
            aspect_ratio="16:9"
        )
        print(f"生成结果: {result}")
        
        # 从文章生成配图
        article = """
        人工智能正在改变我们的生活。从智能家居到自动驾驶，AI技术无处不在。
        
        机器学习是人工智能的核心。通过大量数据训练，模型可以做出准确预测。
        
        深度学习是机器学习的子集。神经网络模拟人脑工作方式，处理复杂任务。
        """
        
        images = await generator.generate_from_article(article, num_images=3)
        print(f"生成了{len(images)}张配图")
    
    asyncio.run(test_image_gen())
