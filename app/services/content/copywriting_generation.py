from openai import OpenAI
from app.core.config import settings
from app.utils.logger import logger
from typing import Optional
import re
from sqlalchemy.orm import Session
from app.db.session import SessionLocal

class CopywritingGenerator:
    """平台差异化文案生成器"""

    def __init__(self, db: Session = None):
        """
        初始化文案生成器
        
        Args:
            db: 数据库会话（可选）。如果不提供，将尝试从数据库获取默认配置；
                如果数据库配置不可用，则回退到配置文件。
        """
        self.db = db
        self._initialize_client()
    
    def _initialize_client(self):
        """初始化OpenAI客户端，优先使用数据库配置"""
        # 尝试从数据库获取配置
        config = self._get_llm_config_from_db()
        
        if config:
            # 使用数据库配置
            self.client = OpenAI(
                api_key=config.api_key,
                base_url=config.base_url,
                timeout=float(config.timeout or 60)
            )
            self.model = config.model_name
            logger.info(f"✅ AI 文案生成器已初始化，使用数据库配置: {config.provider.value} - {config.name}")
        else:
            # 回退到配置文件
            self._initialize_from_settings()
    
    def _get_llm_config_from_db(self):
        """从数据库获取LLM配置(必须)"""
        if not self.db:
            raise ValueError("数据库会话未提供,无法获取LLM配置。请先在数据库中配置大模型。")
        
        try:
            from app.services.system.config_service import LLMConfigService
            llm_service = LLMConfigService(self.db)
            config = llm_service.get_default_llm_config("copywriting")
            
            if not config:
                raise ValueError(
                    "数据库中未找到文案生成的默认LLM配置。\n"
                    "请前往【系统管理】→【LLM配置管理】添加配置:\n"
                    "1. 选择提供商(siliconflow/modelscope/dashscope等)\n"
                    "2. 功能类型选择【文案生成】\n"
                    "3. 填写API密钥、Base URL和模型名称\n"
                    "4. 勾选【设为默认】\n"
                    "5. 保存并测试"
                )
            
            return config
        except ValueError:
            raise
        except Exception as e:
            logger.error(f"从数据库获取LLM配置失败: {e}")
            raise ValueError(f"数据库查询失败: {str(e)}")
    
    def _initialize_from_settings(self):
        """从配置文件初始化（回退方案）"""
        provider = settings.LLM_PROVIDER.lower()
        
        if provider == "siliconflow":
            self.client = OpenAI(
                api_key=settings.SILICONFLOW_API_KEY,
                base_url=settings.SILICONFLOW_BASE_URL,
                timeout=60.0  # ✅ 增加到60秒超时，适应硅基流动API响应速度
            )
            self.model = settings.SILICONFLOW_MODEL
        elif provider == "modelscope":
            self.client = OpenAI(
                api_key=settings.MODELSCOPE_API_KEY,
                base_url=settings.MODELSCOPE_BASE_URL,
                timeout=30.0  # ✅ 添加30秒超时
            )
            self.model = settings.MODELSCOPE_MODEL
        elif provider == "deepseek":
            self.client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url="https://api.deepseek.com/v1",
                timeout=30.0  # ✅ 添加30秒超时
            )
            self.model = "deepseek-chat"
        else:  # openai
            self.client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=30.0  # ✅ 添加30秒超时
            )
            self.model = "gpt-3.5-turbo"
        
        logger.info(f"⚠️ AI 文案生成器已初始化（使用配置文件），提供商: {provider}")

    def _clean_markdown(self, text: str) -> str:
        """清理 Markdown 标签和写作提示词"""
        if not text:
            return text
        
        # 1. 移除 Markdown 标题标记 (##, ###, #### 等)
        text = re.sub(r'^#{1,6}\s+', '', text, flags=re.MULTILINE)
        
        # 2. 移除加粗标记 (**text** 或 __text__)
        text = re.sub(r'\*\*(.+?)\*\*', r'\1', text)
        text = re.sub(r'__(.+?)__', r'\1', text)
        
        # 3. 移除斜体标记 (*text* 或 _text_)
        text = re.sub(r'\*(.+?)\*', r'\1', text)
        text = re.sub(r'_(.+?)_', r'\1', text)
        
        # 4. 移除列表标记 (- item 或 * item 或 1. item)
        text = re.sub(r'^\s*[-*]\s+', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*\d+\.\s+', '', text, flags=re.MULTILINE)
        
        # 5. 移除引用标记 (> text)
        text = re.sub(r'^\s*>\s+', '', text, flags=re.MULTILINE)
        
        # 6. 移除代码块标记 (```code```)
        text = re.sub(r'```[\s\S]*?```', '', text)
        text = re.sub(r'`(.+?)`', r'\1', text)
        
        # 7. 移除写作提示词（这些不应该出现在最终文章中）
        prompt_words = [
            r'【开头】', r'【起势】', r'【金句】', r'【爆点】',
            r'开头：', r'起势：', r'金句：', r'爆点：',
            r'开头\s*[:：]', r'起势\s*[:：]', r'金句\s*[:：]', r'爆点\s*[:：]',
            r'信息爆点', r'情绪高点',
        ]
        for pattern in prompt_words:
            text = re.sub(pattern, '', text)
        
        # 8. 清理多余的空行（超过2个连续空行改为2个）
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 9. 清理每行首尾的多余空格
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        return text

    def _get_platform_prompt(self, platform: str, topic: str) -> str:
        """根据平台获取特定的 System Prompt（优化为今日头条爆款黄金规则）"""
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
            你是一位今日头条爆款文章写手，精通头条算法推荐机制和用户阅读偏好。
                                    
            请为话题 '{topic}' 创作一篇符合"头条爆款黄金规则"的深度文章。
                                    
            【头条爆款黄金规则】
            1. **标题设计**（决定80%的点击率）：
               - 采用"悬念式"、"数字式"或"反差式"标题
               - 示例：《90%的人都不知道...》《这3个技巧，让你效率提升10倍》
               - ⚠️ 标题长度严格控制在20-30个字符以内（头条限制30字）
               - 包含核心关键词
               - 避免标题党，但要足够吸引人
                                    
            2. **内容结构**（提升完读率）：
               - 开头100字必须抓住读者注意力（痛点/悬念/热点）
               - 全文1500-2500字，分段清晰，每段有小标题
               - 使用通俗易懂的语言，避免学术化表达
               - 在关键位置自然融入观点和案例，不要标注"金句"、"爆点"等提示词
                                    
            3. **互动引导**（提升推荐权重）：
               - 文中适当提出开放式问题，引导评论
               - 结尾设置投票或讨论话题
               - 鼓励读者分享自己的经历
                                    
            4. **SEO优化**：
               - 融入3-5个热点关键词
               - 标题和首段必须包含核心关键词
               - 标签选择高搜索量的垂直领域词
                                    
            5. **输出格式**（严格遵守，不要使用任何Markdown标记）：
               - 标题：[具有吸引力的爆款标题]
               - 分类：[科技/生活/财经/娱乐/体育等]
               - 正文：[完整文章内容，包含小标题和段落，不要使用##等Markdown标记]
               - 标签：[关键词1,关键词2,关键词3]
                                    
            ⚠️ 重要提示：
            - 正文中不要使用 #、##、### 等 Markdown 标记
            - 小标题直接使用文字，不要加任何符号
            - 保持纯文本格式，方便直接复制到头条编辑器
            - 不要在正文中出现"开头"、"起势"、"金句"、"爆点"等写作提示词
            - 所有内容都应该是文章的正式部分，直接呈现给读者
                                    
            现在请开始创作，确保文章既有深度又易读，能够引发读者共鸣和讨论。
            """
        }
        return prompts.get(platform, prompts["douyin"])

    def generate_script(self, platform: str, topic: str, max_retries: int = 2, enable_web_search: bool = True, optimized_prompt: Optional[str] = None, hot_article_content: Optional[str] = None, hot_article_title: Optional[str] = None, account_id: Optional[int] = None) -> Optional[dict]:
        """
        生成脚本内容
        
        Args:
            platform: 目标平台
            topic: 创作主题
            max_retries: 最大重试次数
            enable_web_search: 是否启用网络搜索获取素材（默认True）
            optimized_prompt: 优化的提示词模板（来自智能分析结果）
            hot_article_content: 热点文章原始内容（用于二次创作）
            hot_article_title: 热点文章标题（用于二次创作）
            account_id: 账号ID（用于获取自适应进化配置）
        """
        for attempt in range(max_retries + 1):
            try:
                # === 步骤1: 网络搜索获取实时素材 ===
                web_materials = ""
                if enable_web_search and platform == "toutiao":
                    logger.info(f"🌐 开始搜索网络素材: {topic}")
                    try:
                        from app.services.content.web_search import get_web_search_service
                        search_service = get_web_search_service(self.db)
                        
                        # 异步搜索（在同步函数中需要特殊处理）
                        import asyncio
                        try:
                            loop = asyncio.get_running_loop()
                            # 如果已经有事件循环，创建任务
                            results = asyncio.run_coroutine_threadsafe(
                                search_service.search_materials(topic, num_results=5),
                                loop
                            ).result(timeout=15)
                        except RuntimeError:
                            # 没有事件循环，直接运行
                            results = asyncio.run(
                                search_service.search_materials(topic, num_results=5)
                            )
                        
                        if results:
                            web_materials = search_service.format_search_results_for_prompt(results)
                            logger.info(f"✅ 获取到 {len(results)} 条网络素材")
                            
                            # ★★★ 检查是否有二次创作内容 ★★★
                            ai_rewrite_result = None
                            for result in results:
                                if result.get("is_generated") and result.get("source") == "ai_rewrite":
                                    ai_rewrite_result = result
                                    break
                            
                            if ai_rewrite_result:
                                logger.info(f"🔄 检测到AI二次创作内容，将用于生成文章")
                                # 这里可以使用 ai_rewrite_result['snippet'] 作为参考
                        else:
                            logger.warning("⚠️  未获取到网络素材，将仅使用LLM知识")
                    except Exception as e:
                        logger.warning(f"⚠️  网络搜索失败: {e}，将仅使用LLM知识")
                
                # === 步骤2: 构建增强Prompt ===
                system_prompt = self._get_platform_prompt(platform, topic)
                
                # ★★★ 获取账号的自适应进化配置（如果有）★★★
                evolution_config = None
                if account_id:
                    try:
                        from app.models import Account
                        from app.db.session import SessionLocal
                        
                        db = SessionLocal()
                        account = db.query(Account).filter(Account.id == account_id).first()
                        
                        if account and account.evolution_config:
                            import json
                            evolution_config = json.loads(account.evolution_config)
                            logger.info(f"✅ 检测到账号 {account_id} 的自适应进化配置")
                            logger.info(f"   标题模式: {evolution_config.get('title_optimization', {}).get('recommended_pattern', 'N/A')}")
                            logger.info(f"   封面风格: {len(evolution_config.get('cover_optimization', {}).get('style_recommendations', {}))}个分类")
                        
                        db.close()
                    except Exception as e:
                        logger.warning(f"⚠️  获取进化配置失败: {e}")
                
                # 如果有进化配置，将其整合到提示词中
                if evolution_config:
                    title_optimization = evolution_config.get("title_optimization", {})
                    content_optimization = evolution_config.get("content_optimization", {})
                    
                    evolution_guidance = f"""

【🧬 自适应进化优化建议】
基于您最近的历史数据分析，系统自动为您生成以下优化建议：

📝 标题优化：
- 推荐模式：{title_optimization.get('recommended_pattern', '')}
- 成功案例：
"""
                    for i, example in enumerate(title_optimization.get('pattern_examples', [])[:3], 1):
                        evolution_guidance += f"  {i}. {example}\n"
                    
                    evolution_guidance += f"""
- 最佳长度：{int(title_optimization.get('optimal_length', 25))}字左右

📖 内容结构优化：
- 建议文章长度：{int(content_optimization.get('optimal_length', 2000))}字
- 建议段落数量：{int(content_optimization.get('optimal_paragraphs', 8))}个
- 结构建议：{content_optimization.get('structure_recommendation', '')}

💡 请遵循以上优化建议进行创作，以提高文章的阅读量和互动率！
"""
                    
                    system_prompt += evolution_guidance
                    logger.info(f"✅ 已将自适应进化建议整合到提示词")
                
                # ★★★ 如果有热点文章内容，先进行二次创作 ★★★
                if hot_article_content and hot_article_title:
                    logger.info(f"🔄 检测到热点文章，启动二次创作模式")
                    logger.info(f"   原标题: {hot_article_title}")
                    logger.info(f"   原长度: {len(hot_article_content)}字")
                    
                    try:
                        import asyncio
                        from app.services.content.hot_article_rewriter import rewrite_hot_article
                        
                        # 异步执行二次创作
                        try:
                            loop = asyncio.get_running_loop()
                            rewrite_result = asyncio.run_coroutine_threadsafe(
                                rewrite_hot_article(
                                    content=hot_article_content,
                                    title=hot_article_title,
                                    platform=platform,
                                    depth="deep"
                                ),
                                loop
                            ).result(timeout=30)
                        except RuntimeError:
                            rewrite_result = asyncio.run(
                                rewrite_hot_article(
                                    content=hot_article_content,
                                    title=hot_article_title,
                                    platform=platform,
                                    depth="deep"
                                )
                            )
                        
                        if rewrite_result.get("status") == "success":
                            logger.info(f"✅ 二次创作成功")
                            logger.info(f"   新标题: {rewrite_result['new_title']}")
                            logger.info(f"   原创度: {rewrite_result['originality_score']:.0%}")
                            logger.info(f"   使用策略: {', '.join(rewrite_result['rewrite_strategies_used'])}")
                            
                            # 使用二次创作后的内容作为基础
                            rewritten_content = rewrite_result['content']
                            new_title = rewrite_result['new_title']
                            
                            # 将二次创作结果整合到提示词中
                            user_message = f"""
【二次创作参考】
已对热点文章进行深度分析和二次原创：
- 原标题: {hot_article_title}
- 新标题建议: {new_title}
- 原创度: {rewrite_result['originality_score']:.0%}
- 改写策略: {', '.join(rewrite_result['rewrite_strategies_used'])}

【二次创作后的内容框架】
{rewritten_content[:1500]}

【创作要求】
请基于以上二次创作的内容框架，进一步完善和优化，生成最终的头条文章。
注意：
1. 保持高原创度，避免与原文雷同
2. 加入更多个人观点和深度分析
3. 确保内容结构清晰，段落分明
4. 符合头条爆款文章的黄金规则
5. 标题控制在30字以内

主题：{topic}
"""
                            logger.info(f"✅ 已将二次创作内容整合到提示词")
                        else:
                            logger.warning(f"⚠️  二次创作失败: {rewrite_result.get('error')}")
                            # 降级：使用普通流程
                            user_message = f"请开始创作关于 {topic} 的内容"
                            
                    except Exception as e:
                        logger.error(f"❌ 二次创作过程异常: {e}")
                        import traceback
                        traceback.print_exc()
                        # 降级：使用普通流程
                        user_message = f"请开始创作关于 {topic} 的内容"
                
                # 如果有优化的提示词，添加到system prompt中
                elif optimized_prompt:
                    logger.info("🎯 应用智能分析优化后的提示词")
                    system_prompt = f"{system_prompt}\n\n{optimized_prompt}"
                    
                    # 如果有网络素材，添加到用户消息中
                    user_message = f"请开始创作关于 {topic} 的内容"
                    if web_materials:
                        user_message = f"""
{web_materials}

【创作要求】
请基于以上网络素材进行二次原创，注意：
1. 不要直接复制素材内容，要进行深度加工和重新组织
2. 结合素材中的最新信息和数据
3. 加入你自己的观点和分析
4. 保持原创性，避免抄袭嫌疑
5. 确保内容准确性和时效性

主题：{topic}
"""
                else:
                    # 普通流程
                    user_message = f"请开始创作关于 {topic} 的内容"
                    if web_materials:
                        user_message = f"""
{web_materials}

【创作要求】
请基于以上网络素材进行二次原创，注意：
1. 不要直接复制素材内容，要进行深度加工和重新组织
2. 结合素材中的最新信息和数据
3. 加入你自己的观点和分析
4. 保持原创性，避免抄袭嫌疑
5. 确保内容准确性和时效性

主题：{topic}
"""
                
                logger.info(f"开始生成 {platform} 平台内容（尝试 {attempt + 1}/{max_retries + 1}）...")
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    temperature=0.8,  # 提高创造性
                    timeout=60.0  # ✅ 请求级别也设置60秒超时
                )
                
                content = response.choices[0].message.content
                logger.info(f"成功为平台 {platform} 生成内容，长度: {len(content)}")
                
                # ✅ 清理 Markdown 标签和写作提示词
                content = self._clean_markdown(content)
                logger.info(f"✅ 已清理 Markdown 标签和提示词，清理后长度: {len(content)}")
                
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
                            # 移除所有 Markdown 标记（#, ##, ### 等）
                            title = line.replace('#', '').replace('标题：', '').strip()
                            # ✅ 头条标题限制30个字符，超出则截断
                            if len(title) > 30:
                                logger.warning(f"️  标题超长 ({len(title)}字)，截断为30字")
                                title = title[:27] + "..."
                            result["title"] = title
                            logger.info(f"✅ 标题已提取: {title} ({len(title)}字)")
                        elif '分类：' in line:
                            # 移除 Markdown 标记
                            result["category"] = line.replace('#', '').replace('分类：', '').strip()
                            logger.info(f"✅ 分类已提取: {result['category']}")
                        elif '标签：' in line:
                            # 移除 Markdown 标记
                            tags_str = line.replace('#', '').replace('标签：', '').strip()
                            result["tags"] = [tag.strip() for tag in tags_str.split(',')]
                            logger.info(f"✅ 标签已提取: {result['tags']}")
                    
                    # ★★★ 新增：分析图片插入位置 ★★★
                    image_suggestions = []
                    try:
                        from app.services.content.article_image_position_analyzer import suggest_image_positions
                        image_suggestions = suggest_image_positions(
                            content=content,
                            title=result.get("title", topic),
                            num_images=3
                        )
                        logger.info(f"✅ 图片位置分析完成，建议 {len(image_suggestions)} 个位置")
                    except Exception as e:
                        logger.warning(f"⚠️  图片位置分析失败: {e}，将使用默认均匀分布")
                    
                    # ★★★ 新增：智能内容优化建议 ★★★
                    smart_optimization = {}
                    try:
                        from app.services.analytics.smart_content_optimizer import get_smart_optimization_suggestions
                        
                        historical_data = None  # TODO: 从数据库获取该账号的历史文章数据
                        
                        smart_optimization = get_smart_optimization_suggestions(
                            content=content,
                            title=result.get("title", topic),
                            category=result.get("category", "科技"),
                            historical_analytics=historical_data
                        )
                        
                        logger.info(f"✅ 智能优化建议生成完成")
                        if smart_optimization.get("title_optimization"):
                            logger.info(f"   标题优化建议: {len(smart_optimization['title_optimization'].get('suggestions', []))}条")
                        if smart_optimization.get("image_suggestions"):
                            logger.info(f"   图片位置建议: {len(smart_optimization['image_suggestions'])}个")
                            
                    except Exception as e:
                        logger.warning(f"⚠️  智能优化建议生成失败: {e}")
                    
                    # 添加智能优化字段到返回结果
                    result["image_suggestions"] = image_suggestions
                    result["smart_optimization"] = smart_optimization
                    
                    return result
                else:
                    return {
                        "script": content,
                        "platform": platform,
                        "topic": topic
                    }

            except Exception as e:
                error_msg = str(e)
                logger.warning(f"AI 内容生成失败（尝试 {attempt + 1}/{max_retries + 1}）: {error_msg}")
                
                # 如果是最后一次尝试，返回 None
                if attempt == max_retries:
                    logger.error(f"AI 内容生成最终失败，已重试 {max_retries} 次: {error_msg}")
                    return None
                
                # 否则继续重试
                import time
                wait_time = 2 * (attempt + 1)  # 递增等待时间：2s, 4s
                logger.info(f"{wait_time} 秒后重试...")
                time.sleep(wait_time)
