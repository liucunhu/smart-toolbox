"""
基于大模型的智能封面图生成服务
根据文章标题和内容，调用LLM分析并生成封面图提示词，然后生成封面图
"""
import os
import json
from typing import Dict, Any, Optional
from openai import OpenAI
from app.core.config import settings
from app.utils.logger import logger
from PIL import Image, ImageDraw, ImageFont
import random


class LLMCoverGenerator:
    """基于大模型的智能封面图生成器"""
    
    def __init__(self):
        # 初始化LLM客户端
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "siliconflow":
            self.client = OpenAI(
                api_key=settings.SILICONFLOW_API_KEY,
                base_url=settings.SILICONFLOW_BASE_URL,
                timeout=30.0  # ★★★ 客户端级别超时 ★★★
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
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
            self.model = "gpt-3.5-turbo"
        
        logger.info(f"🤖 LLM封面图生成器已初始化，使用提供商: {provider}")
        
        # 封面规格 (头条推荐 16:9)
        self.cover_width = 1280
        self.cover_height = 720
        
        # 输出目录
        self.output_dir = "uploads/llm_covers"
        os.makedirs(self.output_dir, exist_ok=True)
    
    def analyze_content_for_cover(self, title: str, content: str = "", category: str = "科技") -> Dict[str, Any]:
        """
        使用LLM分析文章内容，提取封面设计要素
        
        Returns:
            {
                "keywords": ["关键词1", "关键词2"],
                "emotion": "positive/negative/neutral",
                "visual_style": "modern/minimal/bold/tech/warm",
                "color_scheme": "blue/orange/green/purple/red",
                "design_elements": ["元素1", "元素2"],
                "cover_prompt": "封面设计提示词"
            }
        """
        try:
            logger.info(f"🔍 开始分析文章内容: {title[:50]}...")
            logger.info(f"   📡 正在调用 LLM API (可能需要3-10秒)...")
            
            import time
            start_time = time.time()
            
            prompt = f"""
你是一位专业的内容视觉设计师。请分析以下文章，为它设计一个吸引人的封面图。

文章标题: {title}
文章分类: {category}
文章内容摘要: {content[:500] if content else ""}

请返回JSON格式的设计方案，包含以下字段：
1. keywords: 3-5个核心关键词（用于封面文字）
2. emotion: 情感基调（positive/neutral/professional/energetic）
3. visual_style: 视觉风格（modern简约现代/tech科技感/warm温暖清新/bold大胆醒目/professional专业稳重）
4. color_scheme: 配色方案（blue科技蓝/orange活力橙/green清新绿/purple优雅紫/red热情红/dark深邃黑）
5. design_elements: 3-5个视觉元素建议（如图标、图形、背景纹理等）
6. cover_prompt: 一段详细的封面设计提示词（英文，用于指导设计）

只返回JSON，不要其他说明文字。示例：
{{
  "keywords": ["人工智能", "技术趋势", "未来发展"],
  "emotion": "professional",
  "visual_style": "tech",
  "color_scheme": "blue",
  "design_elements": ["渐变背景", "科技线条", "数据图表图标"],
  "cover_prompt": "A modern tech-themed cover with gradient blue background, featuring abstract data visualization elements and clean typography"
}}
"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的内容视觉设计师"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                timeout=30,  # ★★★ 添加30秒超时 ★★★
                max_tokens=500  # ★★★ 限制返回长度，加快响应 ★★★
            )
            
            elapsed = time.time() - start_time
            logger.info(f"   ✅ LLM API 响应完成 (耗时: {elapsed:.2f}秒)")
            
            result_text = response.choices[0].message.content
            
            # 解析JSON
            try:
                # 尝试直接解析
                design_plan = json.loads(result_text)
            except json.JSONDecodeError:
                # 如果失败，尝试提取JSON部分
                import re
                json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
                if json_match:
                    design_plan = json.loads(json_match.group())
                else:
                    raise ValueError("无法解析LLM返回的JSON")
            
            logger.info(f"✅ LLM分析完成 (总耗时: {elapsed:.2f}秒)")
            logger.info(f"   关键词: {design_plan.get('keywords', [])}")
            logger.info(f"   视觉风格: {design_plan.get('visual_style', '')}")
            logger.info(f"   配色方案: {design_plan.get('color_scheme', '')}")
            
            return design_plan
            
        except Exception as e:
            logger.error(f"❌ LLM内容分析失败: {e}")
            logger.warning("🔄 降级使用默认设计方案（快速模式）...")
            # 返回默认方案
            return {
                "keywords": [title[:20]],
                "emotion": "neutral",
                "visual_style": "modern",
                "color_scheme": "blue",
                "design_elements": ["简洁背景", "居中标题"],
                "cover_prompt": "A clean modern cover with centered title text"
            }
    
    def generate_cover_with_llm_analysis(
        self,
        title: str,
        content: str = "",
        category: str = "科技",
        style_override: str = None
    ) -> Dict[str, Any]:
        """
        基于LLM分析生成封面图
        
        Args:
            title: 文章标题
            content: 文章内容
            category: 文章分类
            style_override: 强制指定风格（可选）
            
        Returns:
            生成结果
        """
        try:
            import time
            total_start = time.time()
            
            logger.info(f"🎨 开始生成LLM智能封面图: {title[:50]}...")
            logger.info(f" 提示: LLM 分析需要 3-10 秒，请耐心等待")
            
            # 步骤1: LLM分析内容
            logger.info(f"📊 步骤 1/2: 调用 LLM 分析文章内容...")
            design_plan = self.analyze_content_for_cover(title, content, category)
            
            # 步骤2: 如果指定了风格覆盖，使用指定的
            if style_override:
                design_plan["visual_style"] = style_override
            
            # 步骤3: 根据设计方案生成封面图
            logger.info(f"️ 步骤 2/2: 绘制封面图...")
            cover_result = self._create_cover_from_design(title, design_plan, category)
            
            # 添加分析信息到结果
            cover_result["design_plan"] = design_plan
            cover_result["llm_analyzed"] = True
            
            total_elapsed = time.time() - total_start
            logger.info(f"✅ LLM封面图生成成功 (总耗时: {total_elapsed:.2f}秒): {cover_result.get('file_path')}")
            
            return cover_result
            
        except Exception as e:
            logger.error(f"❌ LLM封面图生成失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def _create_cover_from_design(
        self,
        title: str,
        design_plan: Dict[str, Any],
        category: str
    ) -> Dict[str, Any]:
        """
        根据设计方案创建封面图（使用PIL实现基础版本）
        未来可以集成Stable Diffusion或DALL-E等真正的图像生成模型
        """
        try:
            import time
            start_time = time.time()
            logger.info(f"   🎨 开始绘制封面图...")
            
            # 获取配色方案
            color_map = {
                "blue": ((15, 32, 39), (32, 156, 238), (0, 212, 255)),
                "orange": ((255, 107, 53), (255, 159, 67), (255, 202, 40)),
                "green": ((0, 184, 148), (85, 239, 196), (253, 203, 110)),
                "purple": ((108, 92, 231), (162, 155, 254), (253, 121, 168)),
                "red": ((214, 48, 49), (255, 118, 117), (255, 159, 67)),
                "dark": ((45, 52, 54), (99, 110, 114), (178, 190, 195))
            }
            
            color_name = design_plan.get("color_scheme", "blue")
            colors = color_map.get(color_name, color_map["blue"])
            bg_color, primary_color, secondary_color = colors
            
            # 创建画布
            img = Image.new('RGB', (self.cover_width, self.cover_height), bg_color)
            draw = ImageDraw.Draw(img)
            
            # 根据视觉风格绘制
            visual_style = design_plan.get("visual_style", "modern")
            
            if visual_style == "tech":
                self._draw_tech_style(draw, primary_color, secondary_color, design_plan)
            elif visual_style == "warm":
                self._draw_warm_style(draw, primary_color, secondary_color, design_plan)
            elif visual_style == "bold":
                self._draw_bold_style(draw, primary_color, secondary_color, design_plan)
            elif visual_style == "professional":
                self._draw_professional_style(draw, primary_color, secondary_color, design_plan)
            else:  # modern
                self._draw_modern_style(draw, primary_color, secondary_color, design_plan)
            
            # 添加标题文字
            self._add_title_text(draw, title, design_plan)
            
            # 添加分类标签
            self._add_category_tag(draw, category, primary_color)
            
            # 保存文件
            filename = f"llm_cover_{int(time.time())}_{hash(title) % 10000}.jpg"
            file_path = os.path.join(self.output_dir, filename)
            
            img.save(file_path, 'JPEG', quality=90)
            
            # 获取文件大小
            file_size_kb = os.path.getsize(file_path) / 1024
            
            elapsed = time.time() - start_time
            logger.info(f"   ✅ 封面图绘制完成 (耗时: {elapsed:.2f}秒)")
            logger.info(f"✅ 封面图已保存: {file_path} ({file_size_kb:.2f} KB)")
            
            return {
                "status": "success",
                "file_path": file_path,
                "filename": filename,
                "title": title,
                "style": visual_style,
                "color_scheme": color_name,
                "dimensions": [self.cover_width, self.cover_height],
                "size_kb": round(file_size_kb, 2),
                "llm_analyzed": True
            }
            
        except Exception as e:
            logger.error(f"❌ 封面图创建失败: {e}")
            raise
    
    def _draw_modern_style(self, draw, primary_color, secondary_color, design_plan):
        """现代风格"""
        # 渐变背景效果（简化版）
        for y in range(self.cover_height):
            ratio = y / self.cover_height
            r = int(primary_color[0] * (1 - ratio) + secondary_color[0] * ratio)
            g = int(primary_color[1] * (1 - ratio) + secondary_color[1] * ratio)
            b = int(primary_color[2] * (1 - ratio) + secondary_color[2] * ratio)
            draw.line([(0, y), (self.cover_width, y)], fill=(r, g, b))
        
        # 装饰性圆形
        draw.ellipse([100, 100, 300, 300], fill=secondary_color + (100,), outline=None)
        draw.ellipse([self.cover_width - 250, self.cover_height - 250, 
                     self.cover_width - 50, self.cover_height - 50], 
                    fill=secondary_color + (80,))
    
    def _draw_tech_style(self, draw, primary_color, secondary_color, design_plan):
        """科技风格"""
        # 深色背景
        draw.rectangle([0, 0, self.cover_width, self.cover_height], fill=(10, 15, 30))
        
        # 网格线
        for x in range(0, self.cover_width, 50):
            draw.line([(x, 0), (x, self.cover_height)], fill=primary_color + (30,))
        for y in range(0, self.cover_height, 50):
            draw.line([(0, y), (self.cover_width, y)], fill=primary_color + (30,))
        
        # 科技线条
        draw.line([(0, 100), (self.cover_width, 200)], fill=secondary_color, width=2)
        draw.line([(0, self.cover_height - 100), (self.cover_width, self.cover_height - 200)], 
                 fill=secondary_color, width=2)
    
    def _draw_warm_style(self, draw, primary_color, secondary_color, design_plan):
        """温暖风格"""
        # 柔和渐变
        for y in range(self.cover_height):
            ratio = y / self.cover_height
            r = int(primary_color[0] * (1 - ratio * 0.5) + 255 * ratio * 0.5)
            g = int(primary_color[1] * (1 - ratio * 0.5) + 255 * ratio * 0.5)
            b = int(primary_color[2] * (1 - ratio * 0.5) + 255 * ratio * 0.5)
            draw.line([(0, y), (self.cover_width, y)], fill=(r, g, b))
        
        # 圆角装饰
        draw.rounded_rectangle([50, 50, 200, 200], radius=20, fill=secondary_color + (100,))
    
    def _draw_bold_style(self, draw, primary_color, secondary_color, design_plan):
        """大胆风格"""
        # 对角线分割
        draw.polygon([(0, 0), (self.cover_width, 0), (0, self.cover_height)], fill=primary_color)
        draw.polygon([(self.cover_width, 0), (self.cover_width, self.cover_height), 
                     (0, self.cover_height)], fill=secondary_color)
    
    def _draw_professional_style(self, draw, primary_color, secondary_color, design_plan):
        """专业风格"""
        # 简洁纯色背景
        draw.rectangle([0, 0, self.cover_width, self.cover_height], fill=primary_color)
        
        # 底部色块
        draw.rectangle([0, self.cover_height - 150, self.cover_width, self.cover_height], 
                      fill=secondary_color)
    
    def _add_title_text(self, draw, title, design_plan):
        """添加标题文字"""
        try:
            # 尝试使用中文字体
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",  # 微软雅黑
                "C:/Windows/Fonts/simhei.ttf",  # 黑体
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",  # Linux文泉驿
            ]
            
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, 60)
                        break
                    except:
                        continue
            
            if not font:
                font = ImageFont.load_default()
            
            # 计算文字位置（居中）
            bbox = draw.textbbox((0, 0), title, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (self.cover_width - text_width) // 2
            y = (self.cover_height - text_height) // 2
            
            # 添加文字阴影效果
            shadow_offset = 3
            draw.text((x + shadow_offset, y + shadow_offset), title, fill=(0, 0, 0), font=font)
            draw.text((x, y), title, fill=(255, 255, 255), font=font)
            
        except Exception as e:
            logger.warning(f"添加标题文字失败: {e}")
    
    def _add_category_tag(self, draw, category, primary_color):
        """添加分类标签"""
        try:
            font_paths = [
                "C:/Windows/Fonts/msyh.ttc",
                "C:/Windows/Fonts/simhei.ttf",
            ]
            
            font = None
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        font = ImageFont.truetype(font_path, 30)
                        break
                    except:
                        continue
            
            if not font:
                font = ImageFont.load_default()
            
            # 在左上角添加分类标签
            tag_text = category
            bbox = draw.textbbox((0, 0), tag_text, font=font)
            tag_width = bbox[2] - bbox[0] + 40
            tag_height = bbox[3] - bbox[1] + 20
            
            # 绘制标签背景
            draw.rounded_rectangle([20, 20, 20 + tag_width, 20 + tag_height], 
                                  radius=10, fill=primary_color)
            
            # 绘制标签文字
            draw.text((40, 30), tag_text, fill=(255, 255, 255), font=font)
            
        except Exception as e:
            logger.warning(f"添加分类标签失败: {e}")


# 全局单例
_llm_cover_generator = None

def get_llm_cover_generator() -> LLMCoverGenerator:
    """获取LLM封面图生成器单例"""
    global _llm_cover_generator
    if _llm_cover_generator is None:
        _llm_cover_generator = LLMCoverGenerator()
    return _llm_cover_generator
