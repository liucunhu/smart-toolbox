"""
新功能API端点 - 包含所有新实现的服务接口
"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Account
from app.utils.logger import logger
from app.utils.async_helper import run_async_task
import json
import os
from typing import Optional, List, Dict, Any

router = APIRouter()


# ==================== 智能养号系统 API ====================
@router.post("/nurturing/config", summary="设置养号配置")
def set_nurturing_config(
    min_videos: int = 10,
    max_videos: int = 30,
    min_watch_duration: int = 5,
    max_watch_duration: int = 60,
    like_probability: int = 5,
    comment_probability: int = 1,
    forward_probability: int = 1,
    follow_probability: int = 2,
    collect_probability: int = 3,
    active_start_hour: int = 20,
    active_end_hour: int = 22,
    scroll_behavior: str = "normal",
    category_focused: bool = True
):
    """
    设置养号配置参数
    
    - **min_videos**: 每次会话最少观看视频数
    - **max_videos**: 每次会话最多观看视频数
    - **min_watch_duration**: 最小观看时长（秒）
    - **max_watch_duration**: 最大观看时长（秒）
    - **like_probability**: 点赞概率（0-100）
    - **comment_probability**: 评论概率（0-100）
    - **forward_probability**: 转发概率（0-100）
    - **follow_probability**: 关注概率（0-100）
    - **collect_probability**: 收藏概率（0-100）
    - **active_start_hour**: 活跃时段开始时间（小时）
    - **active_end_hour**: 活跃时段结束时间（小时）
    - **scroll_behavior**: 滚动行为（normal/aggressive/conservative）
    - **category_focused**: 是否专注同类内容
    """
    try:
        from app.services.operations.intelligent_nurturing import NurturingConfig
        
        config = NurturingConfig(
            min_videos_per_session=min_videos,
            max_videos_per_session=max_videos,
            min_watch_duration=min_watch_duration,
            max_watch_duration=max_watch_duration,
            like_probability=like_probability,
            comment_probability=comment_probability,
            forward_probability=forward_probability,
            follow_probability=follow_probability,
            collect_probability=collect_probability,
            active_start_hour=active_start_hour,
            active_end_hour=active_end_hour,
            scroll_behavior=scroll_behavior,
            category_focused=category_focused
        )
        
        # 保存配置（实际项目中应保存到数据库）
        import sys
        if not hasattr(sys.modules[__name__], '_nurturing_config'):
            setattr(sys.modules[__name__], '_nurturing_config', {})
        getattr(sys.modules[__name__], '_nurturing_config')['default'] = config
        
        logger.info(f"✅ 养号配置已更新")
        
        return {
            "status": "success",
            "message": "养号配置设置成功",
            "config": {
                "min_videos": config.min_videos_per_session,
                "max_videos": config.max_videos_per_session,
                "min_watch_duration": config.min_watch_duration,
                "max_watch_duration": config.max_watch_duration,
                "like_probability": config.like_probability,
                "comment_probability": config.comment_probability,
                "forward_probability": config.forward_probability,
                "follow_probability": config.follow_probability,
                "collect_probability": config.collect_probability,
                "active_time": f"{config.active_start_hour}:00-{config.active_end_hour}:00",
                "scroll_behavior": config.scroll_behavior,
                "category_focused": config.category_focused
            }
        }
    except Exception as e:
        logger.error(f"设置养号配置失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/nurturing/session/start", summary="开始养号会话")
def start_nurturing_session(
    account_id: int,
    platform: str,
    db: Session = Depends(get_db)
):
    """
    开始智能养号会话（异步）
    
    - **account_id**: 账号ID
    - **platform**: 平台类型（douyin/kuaishou/xiaohongshu/toutiao/bilibili/wechat）
    
    模拟真人浏览、点赞、评论等行为
    """
    try:
        from app.services.operations.intelligent_nurturing import IntelligentNurturingEngine, PlatformType
        
        # 验证平台类型
        try:
            platform_enum = PlatformType(platform.lower())
        except ValueError:
            return {
                "status": "failed",
                "error": f"不支持的平台类型: {platform}"
            }
        
        # 获取账号信息
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return {
                "status": "failed",
                "error": "账号不存在"
            }
        
        # 异步执行养号任务
        async def run_nurturing():
            from playwright.async_api import async_playwright
            
            async with async_playwright() as p:
                # 获取或创建配置
                import sys
                config = getattr(sys.modules[__name__], '_nurturing_config', {}).get('default', None)
                
                # 创建养号引擎
                engine = IntelligentNurturingEngine(config)
                
                # 启动浏览器
                browser = await p.chromium.launch(headless=True)
                
                try:
                    # 执行养号会话
                    cookies = json.loads(account.cookies) if account.cookies else None
                    result = await engine.execute_nurturing_session(
                        browser=browser,
                        platform=platform_enum,
                        cookies=cookies
                    )
                    
                    # 保存会话记录到数据库
                    if result["status"] == "completed":
                        from app.models.nurturing import NurturingSession
                        
                        session = NurturingSession(
                            account_id=account_id,
                            platform=account.platform,
                            session_start=result["start_time"],
                            session_end=result["end_time"],
                            videos_watched=result["videos_watched"],
                            watch_duration=result["total_watch_duration"],
                            likes_count=result["interactions"]["like"],
                            comments_count=result["interactions"]["comment"],
                            forwards_count=result["interactions"]["forward"],
                            follows_count=result["interactions"]["follow"],
                            collects_count=result["interactions"]["collect"],
                            status="completed"
                        )
                        db.add(session)
                        db.commit()
                        
                        # 更新账号健康度
                        account.health_score = min(100, account.health_score + 1)
                        db.commit()
                    
                    return result
                finally:
                    await browser.close()
        
        # 使用异步任务执行器
        result = run_async_task(run_nurturing())
        
        return result
    
    except Exception as e:
        logger.error(f"养号会话失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.get("/nurturing/statistics", summary="获取养号统计")
def get_nurturing_statistics(
    account_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """
    获取养号统计信息
    
    - **account_id**: 账号ID（可选，不指定则获取所有账号的统计）
    """
    try:
        from app.models.nurturing import NurturingSession
        
        query = db.query(NurturingSession)
        
        if account_id:
            query = query.filter(NurturingSession.account_id == account_id)
        
        # 总体统计
        total_sessions = query.count()
        all_sessions = query.all()
        total_videos = sum(s.videos_watched for s in all_sessions)
        total_duration = sum(s.watch_duration for s in all_sessions)
        
        # 互动统计
        total_likes = sum(s.likes_count for s in all_sessions)
        total_comments = sum(s.comments_count for s in all_sessions)
        total_forwards = sum(s.forwards_count for s in all_sessions)
        total_follows = sum(s.follows_count for s in all_sessions)
        total_collects = sum(s.collects_count for s in all_sessions)
        
        # 按平台统计
        platform_stats = {}
        for session in all_sessions:
            platform = session.platform.value if hasattr(session.platform, 'value') else str(session.platform)
            if platform not in platform_stats:
                platform_stats[platform] = {
                    "sessions": 0,
                    "videos": 0,
                    "duration": 0,
                    "likes": 0,
                    "comments": 0,
                    "forwards": 0,
                    "follows": 0,
                    "collects": 0
                }
            stats = platform_stats[platform]
            stats["sessions"] += 1
            stats["videos"] += session.videos_watched
            stats["duration"] += session.watch_duration
            stats["likes"] += session.likes_count
            stats["comments"] += session.comments_count
            stats["forwards"] += session.forwards_count
            stats["follows"] += session.follows_count
            stats["collects"] += session.collects_count
        
        return {
            "status": "success",
            "summary": {
                "total_sessions": total_sessions,
                "total_videos": total_videos,
                "total_duration": total_duration,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "total_forwards": total_forwards,
                "total_follows": total_follows,
                "total_collects": total_collects
            },
            "platform_stats": platform_stats
        }
    except Exception as e:
        logger.error(f"获取养号统计失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.get("/nurturing/sessions", summary="获取养号会话记录")
def get_nurturing_sessions(
    account_id: Optional[int] = None,
    platform: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    获取养号会话记录列表
    
    - **account_id**: 账号ID筛选
    - **platform**: 平台筛选
    - **status**: 状态筛选
    - **skip**: 跳过数量
    - **limit**: 返回数量
    """
    try:
        from app.models.nurturing import NurturingSession
        
        query = db.query(NurturingSession)
        
        if account_id:
            query = query.filter(NurturingSession.account_id == account_id)
        if platform:
            query = query.filter(NurturingSession.platform == platform)
        if status:
            query = query.filter(NurturingSession.status == status)
        
        total = query.count()
        sessions = query.order_by(NurturingSession.session_start.desc()).offset(skip).limit(limit).all()
        
        return {
            "status": "success",
            "total": total,
            "sessions": [
                {
                    "id": s.id,
                    "account_id": s.account_id,
                    "platform": s.platform.value if hasattr(s.platform, 'value') else str(s.platform),
                    "session_start": s.session_start.isoformat() if s.session_start else None,
                    "session_end": s.session_end.isoformat() if s.session_end else None,
                    "videos_watched": s.videos_watched,
                    "watch_duration": s.watch_duration,
                    "likes": s.likes_count,
                    "comments": s.comments_count,
                    "forwards": s.forwards_count,
                    "follows": s.follows_count,
                    "collects": s.collects_count,
                    "status": s.status
                }
                for s in sessions
            ]
        }
    except Exception as e:
        logger.error(f"获取养号会话记录失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/nurturing/history/export", summary="导出养号历史")
def export_nurturing_history(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    导出账号的养号历史记录
    
    - **account_id**: 账号ID
    """
    try:
        from app.models.nurturing import NurturingSession
        
        # 查询该账号的所有会话
        sessions = db.query(NurturingSession).filter(
            NurturingSession.account_id == account_id
        ).order_by(NurturingSession.session_start.desc()).all()
        
        # 构建导出数据
        history_data = []
        for session in sessions:
            history_data.append({
                "session_id": session.id,
                "platform": session.platform.value if hasattr(session.platform, 'value') else str(session.platform),
                "start_time": session.session_start.isoformat() if session.session_start else None,
                "end_time": session.session_end.isoformat() if session.session_end else None,
                "videos_watched": session.videos_watched,
                "watch_duration": session.watch_duration,
                "interactions": {
                    "like": session.likes_count,
                    "comment": session.comments_count,
                    "forward": session.forwards_count,
                    "follow": session.follows_count,
                    "collect": session.collects_count
                },
                "status": session.status
            })
        
        # 创建导出目录
        export_dir = "exports/nurturing"
        os.makedirs(export_dir, exist_ok=True)
        
        # 生成文件名
        filename = f"account_{account_id}_nurturing_history.json"
        filepath = os.path.join(export_dir, filename)
        
        # 保存到文件
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(history_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 养号历史已导出: {filepath}")
        
        return {
            "status": "success",
            "message": "养号历史导出成功",
            "file_path": filepath,
            "total_sessions": len(history_data)
        }
    except Exception as e:
        logger.error(f"导出养号历史失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== 设备指纹隔离 API ====================
@router.post("/fingerprint/generate", summary="生成设备指纹配置")
def generate_fingerprint_profile(
    platform: str = "douyin",
    device_type: str = "desktop"
):
    """
    生成设备指纹配置
    
    - **platform**: 目标平台
    - **device_type**: 设备类型（desktop/mobile）
    """
    try:
        from app.services.security.fingerprint_isolation import FingerprintIsolator
        
        isolator = FingerprintIsolator()
        profile = isolator.generate_device_profile(platform, device_type)
        
        return {
            "status": "success",
            "message": "设备指纹配置生成成功",
            "profile": {
                "user_agent": profile.user_agent,
                "screen_resolution": profile.screen_resolution,
                "canvas_noise": profile.canvas_noise,
                "webgl_vendor": profile.webgl_vendor,
                "webgl_renderer": profile.webgl_renderer,
                "fonts": profile.fonts[:5],  # 只返回前5个字体
                "timezone": profile.timezone,
                "language": profile.language
            }
        }
    except Exception as e:
        logger.error(f"生成设备指纹配置失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/fingerprint/isolate", summary="应用设备指纹隔离")
async def apply_fingerprint_isolation(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    为账号应用设备指纹隔离
    
    - **account_id**: 账号ID
    """
    try:
        from app.services.security.fingerprint_isolation import FingerprintIsolator
        from playwright.async_api import async_playwright
        
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return {
                "status": "failed",
                "error": "账号不存在"
            }
        
        async def isolate():
            async with async_playwright() as p:
                isolator = FingerprintIsolator()
                
                # 生成设备配置
                profile = isolator.generate_device_profile(account.platform.value)
                
                # 启动浏览器并应用隔离
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                
                try:
                    # 应用指纹隔离
                    await isolator.apply_fingerprint_isolation(context, profile)
                    
                    # 创建测试页面验证
                    page = await context.new_page()
                    await page.goto("https://bot.sannysoft.com")
                    await page.wait_for_load_state("networkidle")
                    
                    # 截图保存
                    screenshot_path = f"uploads/fingerprints/account_{account_id}.png"
                    os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
                    await page.screenshot(path=screenshot_path)
                    
                    return {
                        "status": "success",
                        "message": "设备指纹隔离应用成功",
                        "screenshot": screenshot_path,
                        "profile_summary": {
                            "user_agent": profile.user_agent[:50] + "...",
                            "webgl_vendor": profile.webgl_vendor,
                            "canvas_noise": profile.canvas_noise
                        }
                    }
                finally:
                    await browser.close()
        
        result = run_async_task(isolate())
        return result
    
    except Exception as e:
        logger.error(f"应用设备指纹隔离失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== 人机验证突破 API ====================
@router.post("/captcha/ocr", summary="OCR识别验证码")
async def ocr_captcha(image: UploadFile = File(...)):
    """
    OCR识别文本验证码
    
    - **image**: 验证码图片
    """
    try:
        from app.services.security.captcha_breaker import CaptchaBreaker
        
        # 保存图片
        image_path = f"uploads/captchas/{image.filename}"
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        
        with open(image_path, "wb") as buffer:
            content = await image.read()
            buffer.write(content)
        
        # 执行OCR识别
        breaker = CaptchaBreaker()
        result = await breaker.ocr_engine.recognize_text(image_path)
        
        return {
            "status": "success",
            "message": "OCR识别完成",
            "result": result
        }
    except Exception as e:
        logger.error(f"OCR识别失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/captcha/slider", summary="滑块验证码求解")
async def solve_slider_captcha(
    background_image: UploadFile = File(...),
    slider_image: UploadFile = File(...)
):
    """
    滑块验证码求解
    
    - **background_image**: 背景图
    - **slider_image**: 滑块图
    """
    try:
        from app.services.security.captcha_breaker import CaptchaBreaker
        
        # 保存图片
        bg_path = f"uploads/captchas/bg_{background_image.filename}"
        slider_path = f"uploads/captchas/slider_{slider_image.filename}"
        os.makedirs(os.path.dirname(bg_path), exist_ok=True)
        
        with open(bg_path, "wb") as buffer:
            buffer.write(await background_image.read())
        
        with open(slider_path, "wb") as buffer:
            buffer.write(await slider_image.read())
        
        # 求解滑块
        breaker = CaptchaBreaker()
        result = await breaker.slider_solver.solve(bg_path, slider_path)
        
        return {
            "status": "success",
            "message": "滑块求解完成",
            "result": result
        }
    except Exception as e:
        logger.error(f"滑块求解失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== 视频去重 API ====================
@router.post("/video/deduplicate", summary="视频去重处理")
async def deduplicate_video(
    video: UploadFile = File(...),
    layers: List[str] = ["visual", "data", "structural"]
):
    """
    视频去重处理
    
    - **video**: 输入视频
    - **layers**: 去重层级（visual/data/structural）
    """
    try:
        from app.services.content.video_deduplication import VideoDeduplicationEngine, VideoLayer
        
        # 保存视频
        video_path = f"uploads/videos/{video.filename}"
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        
        with open(video_path, "wb") as buffer:
            buffer.write(await video.read())
        
        # 转换层级枚举
        layer_enums = []
        for layer in layers:
            try:
                layer_enums.append(VideoLayer(layer))
            except ValueError:
                pass
        
        if not layer_enums:
            layer_enums = [VideoLayer.VISUAL, VideoLayer.DATA, VideoLayer.STRUCTURAL]
        
        # 执行去重
        engine = VideoDeduplicationEngine()
        output_path = video_path.replace(".mp4", "_deduplicated.mp4")
        
        result = engine.deduplicate(
            input_path=video_path,
            output_path=output_path,
            layers=layer_enums
        )
        
        return {
            "status": "success",
            "message": "视频去重完成",
            "input_path": video_path,
            "output_path": result["output_path"],
            "processing_time": result["processing_time"],
            "layers_applied": result["layers_applied"]
        }
    except Exception as e:
        logger.error(f"视频去重失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== 增强版合规审查 API ====================
@router.post("/compliance/enhanced-check", summary="增强版合规检查")
def enhanced_compliance_check(
    text: str,
    platform: str
):
    """
    增强版合规检查（标红显示+替换建议）
    
    - **text**: 待检查文本
    - **platform**: 平台名称
    """
    try:
        from app.services.distribute.enhanced_compliance_checker import EnhancedComplianceChecker
        
        checker = EnhancedComplianceChecker()
        result = checker.check_compliance(text, platform)
        
        return {
            "status": "success",
            "passed": result.passed,
            "highlighted_text": result.highlighted_text,
            "violations": [
                {
                    "word": v["word"],
                    "position": v["position"],
                    "severity": v["severity"],
                    "category": v["category"]
                }
                for v in result.violations
            ],
            "suggestions": result.suggestions,
            "statistics": result.statistics
        }
    except Exception as e:
        logger.error(f"增强版合规检查失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== 格式自适应转换 API ====================
@router.post("/video/format-adapt", summary="视频格式自适应转换")
async def adapt_video_format(
    video: UploadFile = File(...),
    target_platform: str = "douyin"
):
    """
    视频格式自适应转换
    
    - **video**: 输入视频
    - **target_platform**: 目标平台（douyin/kuaishou/xiaohongshu/bilibili）
    """
    try:
        from app.services.content.format_adapter import FormatAdapter
        
        # 保存视频
        video_path = f"uploads/videos/{video.filename}"
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        
        with open(video_path, "wb") as buffer:
            buffer.write(await video.read())
        
        # 执行格式转换
        adapter = FormatAdapter()
        output_path = video_path.replace(".mp4", f"_{target_platform}.mp4")
        
        result = adapter.adapt_format(video_path, output_path, target_platform)
        
        return {
            "status": "success",
            "message": "格式转换完成",
            "input_path": video_path,
            "output_path": result["output_path"],
            "original_specs": result["original_specs"],
            "adapted_specs": result["adapted_specs"]
        }
    except Exception as e:
        logger.error(f"格式转换失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== 增强版智能调度 API ====================
@router.get("/schedule/analyze-active-time", summary="分析粉丝活跃时段")
def analyze_active_time(
    account_id: int,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """
    分析账号粉丝活跃时段
    
    - **account_id**: 账号ID
    - **days**: 分析天数
    """
    try:
        from app.services.operations.smart_scheduler_v2 import SmartSchedulerV2
        
        scheduler = SmartSchedulerV2(db)
        result = scheduler.analyze_follower_activity(account_id, days)
        
        return {
            "status": "success",
            "message": "活跃时段分析完成",
            "analysis": result
        }
    except Exception as e:
        logger.error(f"活跃时段分析失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.get("/schedule/optimal-time", summary="获取最佳发布时间")
def get_optimal_publish_time(
    account_id: int,
    db: Session = Depends(get_db)
):
    """
    获取最佳发布时间（考虑活跃时段和错峰机制）
    
    - **account_id**: 账号ID
    """
    try:
        from app.services.operations.smart_scheduler_v2 import SmartSchedulerV2
        
        scheduler = SmartSchedulerV2(db)
        result = scheduler.get_optimal_publish_time(account_id)
        
        return {
            "status": "success",
            "suggested_time": result["suggested_time"],
            "reason": result["reason"],
            "peak_hours": result["peak_hours"],
            "avoid_hours": result["avoid_hours"]
        }
    except Exception as e:
        logger.error(f"获取最佳发布时间失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== SMS接码平台 API ====================
@router.post("/sms/register-phone", summary="注册手机号")
def register_sms_phone(
    platform: str,
    api_key: str,
    target_platform: str = "douyin"
):
    """
    通过SMS平台注册手机号
    
    - **platform**: SMS平台（sms_activate/5sim/smshub）
    - **api_key**: API密钥
    - **target_platform**: 目标平台
    """
    try:
        from app.services.network.sms_platform import SMSPlatformManager, SMSPlatform
        
        manager = SMSPlatformManager()
        
        # 映射平台枚举
        platform_enum_map = {
            "sms_activate": SMSPlatform.SMS_ACTIVATE,
            "5sim": SMSPlatform.FIVE_SIM,
            "smshub": SMSPlatform.SMS_HUB
        }
        
        platform_enum = platform_enum_map.get(platform.lower())
        if not platform_enum:
            return {
                "status": "failed",
                "error": f"不支持的SMS平台: {platform}"
            }
        
        # 注册手机号
        async def register():
            result = await manager.register_account(
                platform=platform_enum,
                api_key=api_key,
                target_platform=target_platform
            )
            return result
        
        result = run_async_task(register())
        
        return result
    except Exception as e:
        logger.error(f"注册手机号失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.get("/sms/balance", summary="查询SMS平台余额")
def get_sms_balance(
    platform: str,
    api_key: str
):
    """
    查询SMS平台余额
    
    - **platform**: SMS平台
    - **api_key**: API密钥
    """
    try:
        from app.services.network.sms_platform import SMSPlatformManager, SMSPlatform
        
        manager = SMSPlatformManager()
        
        platform_enum_map = {
            "sms_activate": SMSPlatform.SMS_ACTIVATE,
            "5sim": SMSPlatform.FIVE_SIM,
            "smshub": SMSPlatform.SMS_HUB
        }
        
        platform_enum = platform_enum_map.get(platform.lower())
        if not platform_enum:
            return {
                "status": "failed",
                "error": f"不支持的SMS平台: {platform}"
            }
        
        # 查询余额
        async def check_balance():
            client = manager.get_client(platform_enum, api_key)
            balance = await client.get_balance()
            return balance
        
        balance = run_async_task(check_balance())
        
        return {
            "status": "success",
            "balance": balance
        }
    except Exception as e:
        logger.error(f"查询余额失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== 多平台热搜 API ====================
@router.get("/hot-trends/xiaohongshu", summary="小红书热搜")
def get_xiaohongshu_hot_trends(count: int = 20):
    """
    获取小红书热搜榜单
    
    - **count**: 返回数量
    """
    try:
        from app.services.analytics.hot_trend_fetcher_v2 import HotTrendFetcherV2
        
        fetcher = HotTrendFetcherV2()
        trends = fetcher.fetch_xiaohongshu_trends(count)
        
        return {
            "status": "success",
            "platform": "xiaohongshu",
            "total": len(trends),
            "trends": trends
        }
    except Exception as e:
        logger.error(f"获取小红书热搜失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.get("/hot-trends/bilibili", summary="B站热搜")
def get_bilibili_hot_trends(count: int = 20):
    """
    获取B站热搜榜单
    
    - **count**: 返回数量
    """
    try:
        from app.services.analytics.hot_trend_fetcher_v2 import HotTrendFetcherV2
        
        fetcher = HotTrendFetcherV2()
        trends = fetcher.fetch_bilibili_trends(count)
        
        return {
            "status": "success",
            "platform": "bilibili",
            "total": len(trends),
            "trends": trends
        }
    except Exception as e:
        logger.error(f"获取B站热搜失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.get("/hot-trends/toutiao", summary="今日头条热搜")
def get_toutiao_hot_trends(count: int = 20):
    """
    获取今日头条热搜榜单
    
    - **count**: 返回数量
    """
    try:
        from app.services.analytics.hot_trend_fetcher_v2 import HotTrendFetcherV2
        
        fetcher = HotTrendFetcherV2()
        trends = fetcher.fetch_toutiao_trends(count)
        
        return {
            "status": "success",
            "platform": "toutiao",
            "total": len(trends),
            "trends": trends
        }
    except Exception as e:
        logger.error(f"获取今日头条热搜失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== 视觉合成 API ====================
@router.post("/visual/three-grid-cover", summary="三格拼接封面")
async def generate_three_grid_cover(
    images: List[UploadFile] = File(...),
    title: str = ""
):
    """
    生成三格拼接封面
    
    - **images**: 3张图片
    - **title**: 标题文字
    """
    try:
        from app.services.content.visual_synthesis import VisualSynthesisEngine
        
        # 保存图片
        image_paths = []
        for i, img in enumerate(images):
            img_path = f"uploads/covers/temp_{i}_{img.filename}"
            os.makedirs(os.path.dirname(img_path), exist_ok=True)
            
            with open(img_path, "wb") as buffer:
                buffer.write(await img.read())
            
            image_paths.append(img_path)
        
        # 生成三格封面
        engine = VisualSynthesisEngine()
        output_path = f"uploads/covers/three_grid_{images[0].filename}"
        
        result = engine.create_three_grid_cover(image_paths, output_path, title)
        
        return {
            "status": "success",
            "message": "三格封面生成成功",
            "output_path": result["output_path"],
            "dimensions": result["dimensions"]
        }
    except Exception as e:
        logger.error(f"三格封面生成失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/visual/saturated-portrait", summary="高饱和度人物特写封面")
async def generate_saturated_portrait(
    image: UploadFile = File(...),
    saturation: float = 1.5
):
    """
    生成高饱和度人物特写封面
    
    - **image**: 人物图片
    - **saturation**: 饱和度倍数
    """
    try:
        from app.services.content.visual_synthesis import VisualSynthesisEngine
        
        # 保存图片
        img_path = f"uploads/covers/portrait_{image.filename}"
        os.makedirs(os.path.dirname(img_path), exist_ok=True)
        
        with open(img_path, "wb") as buffer:
            buffer.write(await image.read())
        
        # 生成高饱和度封面
        engine = VisualSynthesisEngine()
        output_path = img_path.replace(".jpg", "_saturated.jpg").replace(".png", "_saturated.png")
        
        result = engine.create_saturated_portrait(img_path, output_path, saturation)
        
        return {
            "status": "success",
            "message": "高饱和度封面生成成功",
            "output_path": result["output_path"],
            "saturation_applied": result["saturation"]
        }
    except Exception as e:
        logger.error(f"高饱和度封面生成失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/visual/ins-style-filter", summary="Ins风格滤镜")
async def apply_ins_style_filter(
    image: UploadFile = File(...),
    filter_type: str = "warm"
):
    """
    应用Ins风格滤镜
    
    - **image**: 输入图片
    - **filter_type**: 滤镜类型（warm/cool/vintage）
    """
    try:
        from app.services.content.visual_synthesis import VisualSynthesisEngine
        
        # 保存图片
        img_path = f"uploads/covers/ins_{image.filename}"
        os.makedirs(os.path.dirname(img_path), exist_ok=True)
        
        with open(img_path, "wb") as buffer:
            buffer.write(await image.read())
        
        # 应用Ins滤镜
        engine = VisualSynthesisEngine()
        output_path = img_path.replace(".jpg", "_ins.jpg").replace(".png", "_ins.png")
        
        result = engine.apply_ins_style_filter(img_path, output_path, filter_type)
        
        return {
            "status": "success",
            "message": "Ins滤镜应用成功",
            "output_path": result["output_path"],
            "filter_type": result["filter_type"]
        }
    except Exception as e:
        logger.error(f"Ins滤镜应用失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== 动态字幕 API ====================
@router.post("/subtitle/generate", summary="生成动态字幕")
async def generate_dynamic_subtitle(
    video: UploadFile = File(...),
    language: str = "zh",
    style: str = "modern"
):
    """
    生成动态字幕
    
    - **video**: 输入视频
    - **language**: 语言（zh/en）
    - **style**: 字幕样式（modern/classic/minimal）
    """
    try:
        from app.services.content.dynamic_subtitle import DynamicSubtitleGenerator
        
        # 保存视频
        video_path = f"uploads/videos/subtitle_{video.filename}"
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        
        with open(video_path, "wb") as buffer:
            buffer.write(await video.read())
        
        # 生成字幕
        generator = DynamicSubtitleGenerator()
        output_path = video_path.replace(".mp4", "_subtitled.mp4")
        
        result = await generator.generate_subtitles(video_path, output_path, language, style)
        
        return {
            "status": "success",
            "message": "动态字幕生成成功",
            "output_path": result["output_path"],
            "subtitle_count": result["subtitle_count"],
            "duration": result["duration"]
        }
    except Exception as e:
        logger.error(f"动态字幕生成失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/subtitle/add-sound-effect", summary="添加热门音效")
async def add_sound_effect(
    video: UploadFile = File(...),
    effect_type: str = "popular"
):
    """
    添加热门音效
    
    - **video**: 输入视频
    - **effect_type**: 音效类型（popular/funny/emotional）
    """
    try:
        from app.services.content.dynamic_subtitle import DynamicSubtitleGenerator
        
        # 保存视频
        video_path = f"uploads/videos/effect_{video.filename}"
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        
        with open(video_path, "wb") as buffer:
            buffer.write(await video.read())
        
        # 添加音效
        generator = DynamicSubtitleGenerator()
        output_path = video_path.replace(".mp4", "_effect.mp4")
        
        result = await generator.add_sound_effects(video_path, output_path, effect_type)
        
        return {
            "status": "success",
            "message": "音效添加成功",
            "output_path": result["output_path"],
            "effects_added": result["effects_count"]
        }
    except Exception as e:
        logger.error(f"音效添加失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/subtitle/match-bgm", summary="匹配热门BGM")
async def match_bgm(
    video: UploadFile = File(...),
    mood: str = "energetic"
):
    """
    匹配热门BGM
    
    - **video**: 输入视频
    - **mood**: 情绪类型（energetic/relaxing/emotional）
    """
    try:
        from app.services.content.dynamic_subtitle import DynamicSubtitleGenerator
        
        # 保存视频
        video_path = f"uploads/videos/bgm_{video.filename}"
        os.makedirs(os.path.dirname(video_path), exist_ok=True)
        
        with open(video_path, "wb") as buffer:
            buffer.write(await video.read())
        
        # 匹配BGM
        generator = DynamicSubtitleGenerator()
        output_path = video_path.replace(".mp4", "_bgm.mp4")
        
        result = await generator.match_bgm(video_path, output_path, mood)
        
        return {
            "status": "success",
            "message": "BGM匹配成功",
            "output_path": result["output_path"],
            "bgm_name": result["bgm_name"],
            "volume_adjustment": result["volume_adjustment"]
        }
    except Exception as e:
        logger.error(f"BGM匹配失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== 行为拟人化 API ====================
@router.post("/behavior/mouse-jitter", summary="模拟鼠标抖动")
async def simulate_mouse_jitter(
    duration: int = 10,
    intensity: str = "normal"
):
    """
    模拟鼠标抖动（用于自动化脚本）
    
    - **duration**: 持续时间（秒）
    - **intensity**: 抖动强度（low/normal/high）
    """
    try:
        from app.services.security.human_behavior import HumanBehaviorController
        
        controller = HumanBehaviorController()
        
        # 执行鼠标抖动
        result = await controller.simulate_mouse_jitter(duration, intensity)
        
        return {
            "status": "success",
            "message": "鼠标抖动模拟完成",
            "duration": result["duration"],
            "movements": result["movements"],
            "intensity": result["intensity"]
        }
    except Exception as e:
        logger.error(f"鼠标抖动模拟失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/behavior/random-delay", summary="添加随机延迟")
def add_random_delay(
    min_delay: float = 1.0,
    max_delay: float = 5.0,
    distribution: str = "uniform"
):
    """
    添加随机延迟（用于自动化脚本）
    
    - **min_delay**: 最小延迟（秒）
    - **max_delay**: 最大延迟（秒）
    - **distribution**: 分布类型（uniform/normal）
    """
    try:
        from app.services.security.human_behavior import HumanBehaviorController
        
        controller = HumanBehaviorController()
        delay = controller.add_random_delay(min_delay, max_delay, distribution)
        
        return {
            "status": "success",
            "message": "随机延迟已添加",
            "delay_seconds": delay,
            "min_delay": min_delay,
            "max_delay": max_delay,
            "distribution": distribution
        }
    except Exception as e:
        logger.error(f"随机延迟失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== IP代理池 API ====================
@router.get("/proxy/list", summary="获取代理列表")
def get_proxy_list(
    proxy_type: Optional[str] = None,
    country: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    获取可用代理列表
    
    - **proxy_type**: 代理类型（residential/datacenter/mobile）
    - **country**: 国家代码
    """
    try:
        from app.services.security.human_behavior import ProxyPoolManager
        
        manager = ProxyPoolManager(db)
        proxies = manager.get_available_proxies(proxy_type, country)
        
        return {
            "status": "success",
            "total": len(proxies),
            "proxies": [
                {
                    "id": p.id,
                    "ip": p.ip,
                    "port": p.port,
                    "type": p.type,
                    "country": p.country,
                    "health_score": p.health_score,
                    "last_checked": p.last_checked.isoformat() if p.last_checked else None
                }
                for p in proxies
            ]
        }
    except Exception as e:
        logger.error(f"获取代理列表失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/proxy/check-health", summary="检查代理健康度")
def check_proxy_health(
    proxy_id: int,
    db: Session = Depends(get_db)
):
    """
    检查代理健康度
    
    - **proxy_id**: 代理ID
    """
    try:
        from app.services.security.human_behavior import ProxyPoolManager
        
        manager = ProxyPoolManager(db)
        result = manager.check_proxy_health(proxy_id)
        
        return {
            "status": "success",
            "message": "健康度检查完成",
            "proxy_id": proxy_id,
            "is_healthy": result["is_healthy"],
            "response_time": result["response_time"],
            "health_score": result["health_score"]
        }
    except Exception as e:
        logger.error(f"代理健康度检查失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/proxy/add", summary="添加代理")
def add_proxy(
    ip: str,
    port: int,
    proxy_type: str = "residential",
    country: str = "CN",
    username: Optional[str] = None,
    password: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    添加代理到代理池
    
    - **ip**: 代理IP
    - **port**: 端口
    - **proxy_type**: 代理类型
    - **country**: 国家代码
    - **username**: 用户名（可选）
    - **password**: 密码（可选）
    """
    try:
        from app.services.security.human_behavior import ProxyPoolManager
        
        manager = ProxyPoolManager(db)
        result = manager.add_proxy(ip, port, proxy_type, country, username, password)
        
        return {
            "status": "success",
            "message": "代理添加成功",
            "proxy_id": result["proxy_id"]
        }
    except Exception as e:
        logger.error(f"添加代理失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.delete("/proxy/remove", summary="移除代理")
def remove_proxy(
    proxy_id: int,
    db: Session = Depends(get_db)
):
    """
    从代理池移除代理
    
    - **proxy_id**: 代理ID
    """
    try:
        from app.services.security.human_behavior import ProxyPoolManager
        
        manager = ProxyPoolManager(db)
        success = manager.remove_proxy(proxy_id)
        
        return {
            "status": "success" if success else "failed",
            "message": "代理移除成功" if success else "代理移除失败"
        }
    except Exception as e:
        logger.error(f"移除代理失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }
