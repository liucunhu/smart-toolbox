"""
其他智能体任务处理器
包括：内容生成、合规检查、图片生成、分发智能体
"""
import logging
from typing import Dict, Any
from datetime import datetime

from app.services.agents.task_execution_engine import TaskExecutor
from app.utils.logger import logger

logger = logging.getLogger(__name__)


class ContentGenerationExecutor(TaskExecutor):
    """内容生成智能体执行器"""
    
    @property
    def agent_type(self) -> str:
        return "content_generation"
    
    async def execute(self, task_params: Dict[str, Any]) -> Dict[str, Any]:
        """执行内容生成任务 - 使用真实LLM服务"""
        topic = task_params.get("topic", "")
        style = task_params.get("style", "professional")
        length = task_params.get("length", "medium")  # short/medium/long
        platform = task_params.get("platform", "toutiao")
        
        logger.info(f"开始生成内容: 主题={topic}, 风格={style}, 平台={platform}")
        
        try:
            # ✅ 使用真实的文案生成服务
            from app.services.content.copywriting_generation import CopywritingGenerator
            from app.db.session import SessionLocal
            
            db = SessionLocal()
            generator = CopywritingGenerator(db=db)
            
            result = generator.generate_script(
                platform=platform,
                topic=topic,
                enable_web_search=True  # 启用网络搜索获取实时素材
            )
            
            db.close()
            
            if not result:
                logger.error(f"❌ LLM生成失败")
                return {
                    "task_type": "content_writing",
                    "title": "",
                    "content": "",
                    "word_count": 0,
                    "style": style,
                    "timestamp": datetime.now().isoformat(),
                    "error": "LLM生成失败，请检查API配置"
                }
            
            # 解析文章结构
            title = result.get("title", f"{topic}的深度解析与实践指南")
            content = result.get("content", "")
            word_count = len(content)
            
            logger.info(f"✅ 内容生成成功！标题: {title}, 字数: {word_count}")
            
            return {
                "task_type": "content_writing",
                "title": title,
                "content": content,
                "word_count": word_count,
                "style": style,
                "category": result.get("category", ""),
                "tags": result.get("tags", []),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 内容生成失败: {e}")
            return {
                "task_type": "content_writing",
                "title": "",
                "content": "",
                "word_count": 0,
                "style": style,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }


class ComplianceCheckExecutor(TaskExecutor):
    """合规检查智能体执行器"""
    
    @property
    def agent_type(self) -> str:
        return "compliance_check"
    
    async def execute(self, task_params: Dict[str, Any]) -> Dict[str, Any]:
        """执行合规检查任务 - 使用真实违禁词检测服务"""
        content = task_params.get("content", "")
        title = task_params.get("title", "")
        platform = task_params.get("platform", "toutiao")
        
        logger.info(f"开始合规检查: 平台={platform}, 内容长度={len(content)}")
        
        try:
            # ✅ 使用真实的违禁词检测服务
            from app.api.v1.endpoints import check_content_compliance
            
            # 检查标题和内容
            compliance_result = check_content_compliance(
                title=title or "测试标题",
                content=content,
                platform=platform
            )
            
            is_compliant = compliance_result.get("passed", False)
            violations = compliance_result.get("violations", [])
            
            # 转换为统一格式
            violation_list = []
            if violations:
                for v in violations:
                    violation_list.append({
                        "type": "sensitive_word",
                        "word": v if isinstance(v, str) else v.get("word", ""),
                        "severity": "high"
                    })
            
            logger.info(f"✅ 合规检查完成: {'通过' if is_compliant else '未通过'}, 违规数={len(violation_list)}")
            
            return {
                "task_type": "compliance_check",
                "is_compliant": is_compliant,
                "violations": violation_list,
                "violation_count": len(violation_list),
                "platform": platform,
                "checked_at": datetime.now().isoformat(),
                "recommendation": "内容合规，可以发布" if is_compliant else "需要修改后再发布"
            }
            
        except Exception as e:
            logger.error(f"❌ 合规检查失败: {e}")
            return {
                "task_type": "compliance_check",
                "is_compliant": False,
                "violations": [],
                "violation_count": 0,
                "platform": platform,
                "checked_at": datetime.now().isoformat(),
                "error": str(e)
            }


class ImageGenerationExecutor(TaskExecutor):
    """图片生成智能体执行器"""
    
    @property
    def agent_type(self) -> str:
        return "image_generation"
    
    async def execute(self, task_params: Dict[str, Any]) -> Dict[str, Any]:
        """执行图片生成任务 - 使用真实图像生成API"""
        prompt = task_params.get("prompt", "")
        style = task_params.get("style", "modern")
        size = task_params.get("size", "1200x630")
        
        logger.info(f"开始生成图片: 提示词={prompt}, 风格={style}")
        
        try:
            # ✅ 使用真实的图像生成服务
            from app.services.content.image_generator import ImageGenerator
            
            generator = ImageGenerator()
            
            # 解析尺寸
            aspect_ratio = "16:9"  # 默认
            if "1200x630" in size:
                aspect_ratio = "16:9"
            elif "1080x1080" in size:
                aspect_ratio = "1:1"
            elif "1080x1920" in size:
                aspect_ratio = "9:16"
            
            result = await generator.generate_image(
                prompt=prompt,
                style="realistic" if style == "modern" else style,
                aspect_ratio=aspect_ratio,
                provider="dashscope"  # 使用阿里百炼（已配置）
            )
            
            if result.get("status") != "success":
                logger.error(f"❌ 图片生成失败: {result.get('error')}")
                return {
                    "task_type": "image_generation",
                    "image_url": "",
                    "prompt": prompt,
                    "style": style,
                    "size": size,
                    "generated_at": datetime.now().isoformat(),
                    "error": result.get("error", "未知错误")
                }
            
            image_path = result.get("image_path", "")
            image_url = result.get("image_url", "")
            
            logger.info(f"✅ 图片生成成功: {image_path}")
            
            return {
                "task_type": "image_generation",
                "image_url": image_url,
                "image_path": image_path,
                "prompt": prompt,
                "style": style,
                "size": size,
                "generated_at": datetime.now().isoformat(),
                "provider": result.get("provider", "dashscope")
            }
            
        except Exception as e:
            logger.error(f"❌ 图片生成失败: {e}")
            return {
                "task_type": "image_generation",
                "image_url": "",
                "prompt": prompt,
                "style": style,
                "size": size,
                "generated_at": datetime.now().isoformat(),
                "error": str(e)
            }


class DistributionExecutor(TaskExecutor):
    """分发智能体执行器"""
    
    @property
    def agent_type(self) -> str:
        return "distribution"
    
    async def execute(self, task_params: Dict[str, Any]) -> Dict[str, Any]:
        """执行分发任务 - 使用真实发布服务"""
        platform = task_params.get("platform", "toutiao")
        title = task_params.get("title", "")
        content = task_params.get("content", "")
        account_id = task_params.get("account_id")
        category = task_params.get("category", "科技")
        tags = task_params.get("tags", [])
        cover_image_path = task_params.get("cover_image_path")
        
        logger.info(f"开始分发内容: 平台={platform}, 标题={title}")
        
        try:
            # ✅ 使用真实的头条发布服务
            if platform == "toutiao":
                from app.services.publish.toutiao_publisher import ToutiaoPublisher
                from app.db.session import SessionLocal
                
                db = SessionLocal()
                publisher = ToutiaoPublisher(account_id=account_id)
                
                try:
                    # 初始化浏览器（CDP模式）
                    await publisher.initialize_browser(use_cdp=True, cdp_port=9222)
                    
                    # 智能登录
                    login_success = await publisher.smart_login()
                    if not login_success:
                        raise Exception("登录失败")
                    
                    # 发布文章
                    publish_result = await publisher.publish_article(
                        title=title,
                        content=content,
                        category=category,
                        tags=tags or [],
                        cover_image_path=cover_image_path,
                        auto_generate_cover=False,  # 不自动生成封面
                        account_id=account_id
                    )
                    
                    db.close()
                    
                    if publish_result.get("status") == "success":
                        logger.info(f"✅ 文章发布成功！")
                        return {
                            "task_type": "publish",
                            "platform": platform,
                            "title": title,
                            "status": "published",
                            "article_id": publish_result.get("article_id", ""),
                            "url": publish_result.get("url", ""),
                            "published_at": datetime.now().isoformat(),
                            "account_id": account_id
                        }
                    else:
                        raise Exception(publish_result.get("error", "发布失败"))
                        
                finally:
                    await publisher.close()
            else:
                logger.warning(f"⚠️ 暂不支持平台: {platform}")
                return {
                    "task_type": "publish",
                    "platform": platform,
                    "title": title,
                    "status": "failed",
                    "error": f"暂不支持平台: {platform}",
                    "published_at": datetime.now().isoformat(),
                    "account_id": account_id
                }
            
        except Exception as e:
            logger.error(f"❌ 分发失败: {e}")
            return {
                "task_type": "publish",
                "platform": platform,
                "title": title,
                "status": "failed",
                "error": str(e),
                "published_at": datetime.now().isoformat(),
                "account_id": account_id
            }


class PlanningExecutor(TaskExecutor):
    """规划智能体执行器"""
    
    @property
    def agent_type(self) -> str:
        return "planning"
    
    async def execute(self, task_params: Dict[str, Any]) -> Dict[str, Any]:
        """执行规划任务 - 使用真实LLM生成大纲"""
        topic = task_params.get("topic", "")
        platform = task_params.get("platform", "toutiao")
        
        logger.info(f"开始内容规划: 主题={topic}, 平台={platform}")
        
        try:
            # ✅ 使用真实的LLM服务生成文章大纲
            from app.services.content.copywriting_generation import CopywritingGenerator
            from app.db.session import SessionLocal
            
            db = SessionLocal()
            generator = CopywritingGenerator(db=db)
            
            # 调用LLM生成文章大纲
            result = generator.generate_script(
                platform=platform,
                topic=topic,
                enable_web_search=False  # 只需要大纲,不需要全文
            )
            
            db.close()
            
            if not result:
                logger.error(f"❌ 大纲生成失败")
                return {
                    "task_type": "outline_generation",
                    "topic": topic,
                    "outline": {},
                    "estimated_word_count": 0,
                    "timestamp": datetime.now().isoformat(),
                    "error": "LLM生成失败"
                }
            
            # 从生成结果中提取大纲结构
            title = result.get("title", f"{topic}完全指南")
            content = result.get("content", "")
            tags = result.get("tags", [])
            category = result.get("category", "")
            
            # 解析内容结构(简单按段落划分)
            sections = []
            paragraphs = content.split('\n\n')
            
            for i, para in enumerate(paragraphs[:6], 1):  # 取前6个段落
                if para.strip():
                    # 提取关键观点(前100字)
                    key_points = [para.strip()[:100]]
                    sections.append({
                        "heading": f"第{i}部分",
                        "key_points": key_points
                    })
            
            word_count = len(content)
            
            logger.info(f"✅ 内容规划完成！标题: {title}, 预计字数: {word_count}")
            
            return {
                "task_type": "outline_generation",
                "topic": topic,
                "outline": {
                    "title": title,
                    "sections": sections,
                    "category": category,
                    "tags": tags
                },
                "estimated_word_count": word_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ 内容规划失败: {e}")
            return {
                "task_type": "outline_generation",
                "topic": topic,
                "outline": {},
                "estimated_word_count": 0,
                "timestamp": datetime.now().isoformat(),
                "error": str(e)
            }


class NurturingExecutor(TaskExecutor):
    """养号智能体执行器"""
    
    @property
    def agent_type(self) -> str:
        return "nurturing"
    
    async def execute(self, task_params: Dict[str, Any]) -> Dict[str, Any]:
        """执行养号任务 - 使用真实浏览器自动化"""
        platform = task_params.get("platform", "douyin")
        action_type = task_params.get("action_type", "browse")  # browse/like/comment/follow
        account_id = task_params.get("account_id")
        duration_minutes = task_params.get("duration_minutes", 10)  # 养号时长(分钟)
        
        logger.info(f"开始养号操作: 平台={platform}, 动作={action_type}, 时长={duration_minutes}分钟")
        
        try:
            # ✅ 使用真实的智能养号引擎
            from app.services.operations.intelligent_nurturing import IntelligentNurturingEngine, PlatformType
            from playwright.async_api import async_playwright
            from app.db.session import SessionLocal
            from app.models import Account
            
            db = SessionLocal()
            
            # 获取账号信息
            account = db.query(Account).filter(Account.id == account_id).first()
            if not account:
                raise Exception(f"账号{account_id}不存在")
            
            if not account.cookies:
                raise Exception(f"账号{account_id}未登录,无法养号")
            
            # 转换平台类型
            try:
                platform_enum = PlatformType(platform.lower())
            except ValueError:
                raise Exception(f"不支持的平台: {platform}")
            
            # 初始化养号引擎
            engine = IntelligentNurturingEngine(
                account_id=account_id,
                platform=platform,
                proxy_url=account.proxy_ip
            )
            
            # 执行养号会话
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                
                result = await engine.execute_nurturing_session(
                    browser=browser,
                    platform=platform_enum,
                    cookies=account.cookies
                )
                
                await browser.close()
            
            db.close()
            
            logger.info(f"✅ 养号完成！浏览{result.get('videos_watched', 0)}个视频, 点赞{result.get('like_count', 0)}次")
            
            return {
                "task_type": f"nurturing_{action_type}",
                "platform": platform,
                "action_type": action_type,
                "videos_watched": result.get("videos_watched", 0),
                "like_count": result.get("like_count", 0),
                "comment_count": result.get("comment_count", 0),
                "follow_count": result.get("follow_count", 0),
                "duration_seconds": result.get("duration", 0),
                "account_id": account_id,
                "completed_at": datetime.now().isoformat(),
                "status": result.get("status", "completed")
            }
            
        except Exception as e:
            logger.error(f"❌ 养号失败: {e}")
            return {
                "task_type": f"nurturing_{action_type}",
                "platform": platform,
                "action_type": action_type,
                "actions_performed": 0,
                "duration_seconds": 0,
                "account_id": account_id,
                "completed_at": datetime.now().isoformat(),
                "status": "failed",
                "error": str(e)
            }


# 创建全局实例
content_executor = ContentGenerationExecutor()
compliance_executor = ComplianceCheckExecutor()
image_executor = ImageGenerationExecutor()
distribution_executor = DistributionExecutor()
planning_executor = PlanningExecutor()
nurturing_executor = NurturingExecutor()


class GeneralExecutor(TaskExecutor):
    """通用智能体执行器 - 处理未专门定义的任务类型"""
    
    @property
    def agent_type(self) -> str:
        return "general"
    
    async def execute(self, task_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行通用任务
        根据task_type分发到相应的处理逻辑
        """
        task_type = task_params.get("task_type", "unknown")
        description = task_params.get("description", "")
        
        logger.info(f"开始执行通用任务: {task_type}, 描述={description}")
        
        try:
            # ✅ 根据任务类型智能分发
            if "research" in task_type.lower() or "研究" in description:
                # 转发到研究智能体
                from app.services.agents.executors.research_executor import research_executor
                result = await research_executor.execute({
                    "task_type": "topic_research",
                    "platform": task_params.get("platform", "toutiao"),
                    "category": task_params.get("category", "科技"),
                    "keyword": task_params.get("keyword", "")
                })
            elif "content" in task_type.lower() or "生成" in description or "创作" in description:
                # 转发到内容生成智能体
                result = await content_executor.execute({
                    "topic": task_params.get("topic", ""),
                    "platform": task_params.get("platform", "toutiao"),
                    "style": task_params.get("style", "professional")
                })
            elif "compliance" in task_type.lower() or "合规" in description or "检查" in description:
                # 转发到合规检查智能体
                result = await compliance_executor.execute({
                    "content": task_params.get("content", ""),
                    "title": task_params.get("title", ""),
                    "platform": task_params.get("platform", "toutiao")
                })
            elif "image" in task_type.lower() or "图片" in description or "封面" in description:
                # 转发到图片生成智能体
                result = await image_executor.execute({
                    "prompt": task_params.get("prompt", description),
                    "style": task_params.get("style", "modern"),
                    "size": task_params.get("size", "1200x630")
                })
            elif "publish" in task_type.lower() or "发布" in description or "分发" in description:
                # 转发到分发智能体
                result = await distribution_executor.execute({
                    "platform": task_params.get("platform", "toutiao"),
                    "title": task_params.get("title", ""),
                    "content": task_params.get("content", ""),
                    "account_id": task_params.get("account_id"),
                    "category": task_params.get("category", "科技"),
                    "tags": task_params.get("tags", [])
                })
            elif "plan" in task_type.lower() or "规划" in description or "大纲" in description:
                # 转发到规划智能体
                result = await planning_executor.execute({
                    "topic": task_params.get("topic", ""),
                    "platform": task_params.get("platform", "toutiao")
                })
            elif "nurture" in task_type.lower() or "养号" in description:
                # 转发到养号智能体
                result = await nurturing_executor.execute({
                    "platform": task_params.get("platform", "douyin"),
                    "action_type": task_params.get("action_type", "browse"),
                    "account_id": task_params.get("account_id")
                })
            else:
                # 未知任务类型，使用LLM直接处理
                from app.services.content.copywriting_generation import CopywritingGenerator
                from app.db.session import SessionLocal
                
                db = SessionLocal()
                generator = CopywritingGenerator(db=db)
                
                result_text = generator.generate_script(
                    platform=task_params.get("platform", "toutiao"),
                    topic=description or task_type,
                    enable_web_search=True
                )
                
                db.close()
                
                result = {
                    "task_type": "general_processing",
                    "description": description,
                    "result": result_text.get("content", "") if result_text else "",
                    "timestamp": datetime.now().isoformat()
                }
            
            logger.info(f"✅ 通用任务执行完成: {task_type}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ 通用任务执行失败: {e}")
            return {
                "task_type": task_type,
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }


# 创建通用执行器实例
general_executor = GeneralExecutor()
