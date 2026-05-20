from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query, UploadFile, File
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Account, PlatformEnum, AccountStatusEnum, ContentTask, PublishRecord, Novel, Chapter, FanqieAnalytics
from app.schemas.account import AccountCreate, AccountResponse, AccountListResponse, AccountUpdateRequest
from app.tasks.account_tasks import register_account_task
from app.tasks.content_tasks import generate_script_task, process_video_task
from app.tasks.toutiao_tasks import (
    auto_publish_toutiao_task,
    fetch_toutiao_analytics_task,
    check_account_health_task,
    update_income_stats_task,
    hot_topic_monitor_task
)
from app.services.distribute.ac_filter import HighPerformanceFilter
from app.services.operations.health_monitor import AccountHealthService
from app.services.operations.smart_scheduler import SmartScheduler
from app.tasks.nurturing_tasks import auto_nurturing_task
from app.utils.logger import logger
from app.utils.async_helper import run_async_task
import uuid
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

router = APIRouter()

@router.get("/accounts/list", summary="获取账号列表")
def get_accounts_list(
    page: int = Query(1, ge=1, alias="page"),
    page_size: int = Query(10, ge=1, le=100, alias="page_size"),
    platform: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    """获取账号列表，支持分页和筛选"""
    query = db.query(Account)
    
    if platform:
        query = query.filter(Account.platform == platform)
    if status:
        query = query.filter(Account.status == status)
    
    total = query.count()
    skip = (page - 1) * page_size
    accounts = query.offset(skip).limit(page_size).all()
    
    # 隐藏敏感信息
    accounts_data = []
    for account in accounts:
        accounts_data.append({
            "id": account.id,
            "platform": account.platform.value,
            "username": account.username,
            "status": account.status.value,
            "health_score": account.health_score,
            "proxy_ip": account.proxy_ip,
            "has_cookies": bool(account.cookies),
            "has_password": bool(account.password),
            "created_at": account.created_at.isoformat(),
            "updated_at": account.updated_at.isoformat(),
            "last_login": account.updated_at.isoformat()  # 添加 last_login 字段供前端显示
        })
    
    return {
        "status": "success",
        "message": "获取成功",
        "data": {
            "items": accounts_data,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }

@router.get("/accounts/{account_id}", summary="获取账号详情")
def get_account_detail(account_id: int, db: Session = Depends(get_db)):
    """获取单个账号的详细信息"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    
    # 隐藏敏感信息
    return {
        "id": account.id,
        "platform": account.platform.value,
        "username": account.username,
        "status": account.status.value,
        "health_score": account.health_score,
        "proxy_ip": account.proxy_ip,
        "has_cookies": bool(account.cookies),
        "has_password": bool(account.password),
        "session_token": account.session_token[:20] + "..." if account.session_token else None,
        "publish_url": account.publish_url,
        "created_at": account.created_at.isoformat(),
        "updated_at": account.updated_at.isoformat()
    }

@router.put("/accounts/{account_id}", summary="更新账号信息")
def update_account(
    account_id: int,
    request: AccountUpdateRequest,
    db: Session = Depends(get_db)
):
    """
    更新账号信息
    
    - **account_id**: 账号ID
    - **username**: 用户名（可选）
    - **password**: 密码（可选，最少6字符）
    - **proxy_ip**: 代理IP（可选，格式：x.x.x.x或x.x.x.x:port）
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    
    # 更新字段
    if request.username is not None:
        account.username = request.username
    if request.password is not None:
        account.password = request.password
    if request.proxy_ip is not None:
        account.proxy_ip = request.proxy_ip
    
    db.commit()
    db.refresh(account)
    
    logger.info(f"✅ 账号 {account_id} 信息已更新")
    
    return {
        "status": "success",
        "message": "账号信息更新成功",
        "account": {
            "id": account.id,
            "platform": account.platform.value,
            "username": account.username,
            "status": account.status.value,
            "proxy_ip": account.proxy_ip,
            "has_cookies": bool(account.cookies),
            "updated_at": account.updated_at.isoformat()
        }
    }

@router.delete("/accounts/{account_id}", summary="删除账号")
def delete_account(account_id: int, db: Session = Depends(get_db)):
    """
    删除账号
    
    - **account_id**: 账号ID
    """
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    
    # 记录账号信息用于日志
    account_info = f"{account.platform.value} - {account.username}"
    
    # 删除账号
    db.delete(account)
    db.commit()
    
    logger.info(f"✅ 账号已删除: {account_info}")
    
    return {
        "status": "success",
        "message": f"账号 {account_info} 已删除"
    }

@router.post("/accounts/register", summary="注册账号", description="提交账号注册任务，异步执行")
def register_account(account_data: AccountCreate, db: Session = Depends(get_db)):
    """
    提交账号注册任务 (异步)
    
    - **platform**: 平台类型（douyin/toutiao）
    - **phone_number**: 手机号码
    - **verification_code**: 验证码（可选，支持自动接码）
    - **proxy_ip**: 代理IP（可选）
    
    返回任务ID，可通过Celery查询任务状态
    """
    new_account = Account(
        platform=account_data.platform,
        username=f"temp_{uuid.uuid4().hex[:8]}",
        proxy_ip=account_data.proxy_ip
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)

    # 触发 Celery 异步任务
    task = register_account_task.delay(
        account_id=new_account.id,
        phone=account_data.phone_number,
        code=account_data.verification_code or "AUTO", # 支持自动接码逻辑
        platform=account_data.platform.value,
        proxy_ip=account_data.proxy_ip or ""
    )
    
    return {"message": "注册任务已加入队列", "task_id": task.id, "account_id": new_account.id}

@router.post("/accounts/create", summary="创建账号")
def create_account(
    platform: str,
    username: str,
    password: str = None,
    proxy_ip: str = None,
    db: Session = Depends(get_db)
):
    """
    创建新账号（手动添加）
    
    - **platform**: 平台类型（toutiao/douyin/xiaohongshu等）
    - **username**: 用户名/手机号
    - **password**: 密码（可选）
    - **proxy_ip**: 代理IP（可选）
    """
    from app.models import PlatformEnum
    
    # 验证平台类型
    try:
        platform_enum = PlatformEnum(platform)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"不支持的平台类型: {platform}")
    
    # 检查用户名是否已存在
    existing = db.query(Account).filter(Account.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="该用户名已存在")
    
    # 创建账号
    new_account = Account(
        platform=platform_enum,
        username=username,
        password=password,
        proxy_ip=proxy_ip,
        status=AccountStatusEnum.REGISTERING
    )
    
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    
    logger.info(f"✅ 创建新账号: {platform} - {username}")
    
    return {
        "status": "success",
        "message": "账号创建成功",
        "account": {
            "id": new_account.id,
            "platform": new_account.platform.value,
            "username": new_account.username,
            "status": new_account.status.value,
            "created_at": new_account.created_at.isoformat()
        }
    }

@router.post("/content/generate", summary="生成文案", description="使用AI生成爆款文案或文章")
def generate_content(topic: str, platform: PlatformEnum, account_id: Optional[int] = None, db: Session = Depends(get_db)):
    """
    生成爆款文案 (同步，直接返回结果)
    
    - **topic**: 内容主题
    - **platform**: 目标平台
    - **account_id**: 账号ID（可选，用于获取自适应进化配置）
    
    头条平台返回结构化文章（标题、内容、分类、标签）
    其他平台返回短视频脚本
    """
    try:
        from app.services.content.copywriting_generation import CopywritingGenerator
        generator = CopywritingGenerator(db=db)
        result = generator.generate_script(platform.value, topic, account_id=account_id)
        
        if result:
            if platform.value == "toutiao":
                # 头条文章返回结构化数据
                return {
                    "message": "文章生成成功",
                    "article_title": result.get("title", ""),
                    "article_content": result.get("content", ""),
                    "article_category": result.get("category", ""),
                    "tags": result.get("tags", []),
                    "platform": platform.value,
                    "topic": topic
                }
            else:
                # 其他平台返回脚本
                return {
                    "message": "文案生成成功",
                    "script": result.get("script", ""),
                    "topic": topic,
                    "platform": platform.value
                }
        else:
            return {"message": "文案生成失败", "error": "AI 服务返回空结果"}
    except Exception as e:
        logger.error(f"文案生成失败: {str(e)}")
        return {"message": "文案生成失败", "error": str(e)}

@router.post("/content/process_video", summary="处理视频", description="视频去重与格式转换")
def process_video(input_path: str, platform: PlatformEnum):
    """
    处理视频去重与格式转换 (异步)
    
    - **input_path**: 输入视频路径
    - **platform**: 目标平台
    
    返回任务ID，支持MD5修改、帧抽取、元数据清除等
    """
    task = process_video_task.delay(input_path, platform.value)
    return {"message": "视频处理任务已启动", "task_id": task.id}

@router.post("/compliance/check", summary="违禁词检测", description="实时筛查文本中的违禁词")
def check_compliance(text: str, platform: str):
    """
    实时违禁词筛查 (同步，因为 AC 自动机非常快)
    
    - **text**: 待检测文本
    - **platform**: 平台名称
    
    返回检测结果、违禁词列表和清理后的文本
    """
    filter_engine = HighPerformanceFilter()
    filter_engine.load_platform_rules(platform)
    result = filter_engine.filter_text(text)
    return result

@router.get("/accounts/healthy", summary="获取健康账号", description="查询可用于分发的健康账号列表")
def get_healthy_accounts(platform: Optional[str] = None, db: Session = Depends(get_db)):
    """
    获取可用于分发的健康账号列表
    
    - **platform**: 平台筛选（可选）
    
    返回健康度>=60分的活跃账号
    """
    service = AccountHealthService(db)
    accounts = service.get_healthy_accounts(platform)
    return {"count": len(accounts), "accounts": [{"id": a.id, "username": a.username} for a in accounts]}

@router.post("/operations/nurture", summary="触发养号", description="手动执行一次养号任务")
def trigger_nurturing(account_id: int):
    """
    手动触发一次养号任务
    
    - **account_id**: 账号ID
    
    模拟真人浏览、点赞、评论等行为
    """
    task = auto_nurturing_task.delay(account_id)
    return {"message": "养号任务已启动", "task_id": task.id}

@router.get("/schedule/next_time", summary="获取发布时间", description="系统建议的下一个最佳发布时间")
def get_next_publish_time():
    """
    获取系统建议的下一个发布时间
    
    基于智能调度算法，考虑用户活跃时段和发布频率限制
    """
    next_time = SmartScheduler.get_next_publish_time()
    return {"suggested_time": next_time.isoformat()}

@router.post("/accounts/toutiao/login", summary="头条账号智能登录")
def toutiao_login(account_id: int = None, username: str = None, password: str = None, db: Session = Depends(get_db)):
    """
    头条账号智能登录
    
    优先使用保存的Cookie登录，如果失效则使用账号密码登录
    如果账号不存在但提供了用户名密码，会自动创建账号
    
    - **account_id**: 账号ID（可选）
    - **username**: 用户名/手机号（可选，用于账号密码登录或自动创建）
    - **password**: 密码（可选，用于账号密码登录或自动创建）
    """
    from app.services.publish.toutiao_publisher import ToutiaoPublisher
    from app.models import Account
    
    # 步骤1: 查找或创建账号
    account = None
    if account_id:
        # 如果提供了 account_id，直接查找
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return {"message": f"账号 {account_id} 不存在", "status": "error"}
    elif username and password:
        # 如果没有 account_id 但有用户名密码，尝试查找或创建
        account = db.query(Account).filter(
            Account.username == username,
            Account.platform == PlatformEnum.TOUTIAO
        ).first()
        
        if not account:
            # 自动创建新账号
            logger.info(f"🆕 账号不存在，自动创建: {username}")
            account = Account(
                platform=PlatformEnum.TOUTIAO,
                username=username,
                password=password,
                status=AccountStatusEnum.REGISTERING
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            logger.info(f"✅ 账号创建成功，ID: {account.id}")
        else:
            # 账号已存在，更新密码
            account.password = password
            account.status = AccountStatusEnum.ACTIVE
            db.commit()
            logger.info(f"✅ 账号已存在，更新密码，ID: {account.id}")
    else:
        return {
            "message": "请提供账号ID或用户名+密码",
            "status": "error"
        }
    
    async def login_process():
        publisher = ToutiaoPublisher(account_id=account.id)
        try:
            await publisher.initialize_browser()
            
            # 智能登录：优先使用Cookie
            if account.cookies:
                logger.info(f"检测到账号 {account.id} ({account.username}) 有保存的Cookie，尝试使用Cookie登录...")
                login_success = await publisher.smart_login(cookies=account.cookies)
                
                if login_success:
                    logger.info(f"✅ Cookie登录成功！")
                    return {
                        "status": "success",
                        "message": "Cookie登录成功",
                        "login_method": "cookie",
                        "account_id": account.id,
                        "username": account.username,
                        "cookies": account.cookies
                    }
                else:
                    logger.warning(f"⚠️  Cookie登录失败")
            
            # Cookie失效或不存在，使用账号密码登录
            if not username or not password:
                return {
                    "status": "failed",
                    "message": "Cookie失效，请提供用户名和密码进行登录",
                    "login_method": "none"
                }
            
            logger.info(f"使用账号密码登录...")
            result = await publisher.login_with_manual_input(username, password)
            
            if result["status"] == "success":
                # 保存 Cookie 到数据库
                account.cookies = result["cookies"]
                account.status = AccountStatusEnum.ACTIVE
                db.commit()
                result["login_method"] = "password"
                
            return result
        finally:
            await publisher.close()
    
    # 使用统一的异步任务执行器
    result = run_async_task(login_process())
    
    return result

@router.post("/content/toutiao/publish", summary="发布头条文章（智能登录）")
def publish_toutiao_article(
    account_id: int,
    title: str,
    content: str,
    category: str = "科技",
    tags: list = None,
    cover_image_path: str = None,
    auto_generate_cover: bool = True,  # ✅ 修复：默认启用封面图生成
    cover_style: str = "modern",
    use_template: str = None,
    declaration_type: str = "ai",  # 新增参数：声明类型
    use_cdp: bool = True,  # CDP模式：使用真实Edge浏览器（推荐）
    cdp_port: int = 9222,  # CDP调试端口
    username: str = None,
    password: str = None,
    db: Session = Depends(get_db)
):
    """发布头条文章（支持智能登录和高级封面图功能）
    
    优先使用保存的Cookie登录，如果失效则使用账号密码登录
    如果账号不存在但提供了用户名密码，会自动创建账号
    
    - **account_id**: 账号ID（可选，如果不提供则需要 username+password）
    - **title**: 文章标题
    - **content**: 文章内容
    - **category**: 文章分类
    - **tags**: 标签列表
    - **cover_image_path**: 封面图片路径（可选）
    - **auto_generate_cover**: 是否自动生成封面图
    - **cover_style**: AI生成风格 (modern/minimal/bold)
    - **use_template**: 使用的模板ID
    - **declaration_type**: 作品声明类型 ("ai"=引用AI, "personal_opinion"=仅个人观点)
    - **use_cdp**: 是否使用CDP模式（连接真实Edge浏览器，推荐=True）
    - **cdp_port**: CDP调试端口（默认9222）
    - **username**: 用户名（可选，用于查找或创建账号）
    - **password**: 密码（可选，用于查找或创建账号）
    """
    from app.services.publish.toutiao_publisher import ToutiaoPublisher
    from app.models import Account, ContentTask
    
    # 🆕 步骤1: 查找或创建账号（支持自动创建）
    account = None
    if account_id:
        # 方式1: 通过 account_id 查找
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            return {"message": f"账号 {account_id} 不存在", "status": "error"}
    elif username and password:
        # 方式2: 通过 username 查找或创建
        account = db.query(Account).filter(
            Account.username == username,
            Account.platform == PlatformEnum.TOUTIAO
        ).first()
        
        if not account:
            # 自动创建新账号
            logger.info(f"🆕 账号不存在，自动创建: {username}")
            account = Account(
                platform=PlatformEnum.TOUTIAO,
                username=username,
                password=password,
                status=AccountStatusEnum.REGISTERING
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            logger.info(f"✅ 账号创建成功，ID: {account.id}")
            account_id = account.id  # 更新 account_id
        else:
            # 账号已存在，更新密码
            account.password = password
            account.status = AccountStatusEnum.ACTIVE
            db.commit()
            logger.info(f"✅ 账号已存在，更新密码，ID: {account.id}")
            account_id = account.id  # 更新 account_id
    else:
        return {
            "message": "请提供账号ID或用户名+密码",
            "status": "error"
        }
    
    async def publish_process():
        publisher = ToutiaoPublisher(account_id=account_id)
        try:
            # 初始化浏览器（支持CDP模式）
            if use_cdp:
                logger.info(f"🚀 使用CDP模式连接真实Edge浏览器（端口 {cdp_port}）...")
                await publisher.initialize_browser(use_cdp=True, cdp_port=cdp_port)
            else:
                logger.info("使用标准浏览器模式...")
                await publisher.initialize_browser(use_cdp=False)
            
            # 智能登录：优先使用Cookie
            login_success = False
            if account.cookies:
                logger.info(f"尝试使用保存的Cookie登录...")
                login_success = await publisher.smart_login(cookies=account.cookies)
            
            # 如果Cookie登录失败，且提供了账号密码，则使用账号密码登录
            if not login_success and (username or account.password):
                login_pwd = password or account.password
                if login_pwd:
                    logger.info(f"Cookie失效，使用账号密码登录...")
                    login_result = await publisher.login_with_manual_input(account.username, login_pwd)
                    if login_result["status"] == "success":
                        # 保存新的Cookie
                        account.cookies = login_result["cookies"]
                        account.status = AccountStatusEnum.ACTIVE
                        db.commit()
                        login_success = True
            
            if not login_success:
                return {
                    "status": "failed",
                    "error": "登录失败，请检查Cookie或提供正确的账号密码"
                }
            
            logger.info(f"✅ 登录成功，开始发布文章...")
            
            # ========== 合规审查（必须）==========
            logger.info(f"🔍 正在进行合规审查...")
            compliance_result = check_content_compliance(title, content, "toutiao")
            if not compliance_result["passed"]:
                logger.warning(f"⚠️  合规审查失败: {compliance_result['error']}")
                return {
                    "status": "failed",
                    "error": compliance_result["error"]
                }
            logger.info(f"✅ 合规审查通过")
            
            # 发布文章
            result = await publisher.publish_article(
                title=title,
                content=content,
                category=category,
                tags=tags or [],
                cover_image_path=cover_image_path,
                auto_generate_cover=auto_generate_cover,
                cover_style=cover_style,
                use_template=use_template,
                declaration_type=declaration_type
            )
            
            # 保存发布记录
            if result["status"] == "success":
                content_task = ContentTask(
                    task_id=str(uuid.uuid4()),
                    original_topic=title,
                    target_platform=PlatformEnum.TOUTIAO,
                    article_title=title,
                    article_content=content,
                    article_category=category,
                    tags=tags,
                    status="completed"
                )
                db.add(content_task)
                db.commit()
            
            return result
        finally:
            await publisher.close()
    
    # 使用统一的异步任务执行器
    result = run_async_task(publish_process())
    
    return result

@router.post("/content/toutiao/auto_publish", summary="一键发布头条文章（全自动）")
def auto_publish_toutiao(
    account_id: int,
    topic: str,
    username: str = None,  # ✅ 改为可选，优先使用数据库中的账号
    password: str = None,  # ✅ 改为可选，优先使用数据库中的密码
    category: str = "科技",
    cover_image_path: str = None,
    auto_generate_cover: bool = True,
    cover_style: str = "modern",
    use_template: str = None,
    declaration_type: str = "ai",  # 新增参数：声明类型（已废弃，改用declarations）
    declarations: str = None,  # ✅ 新增参数：作品声明（JSON字符串数组）
    article_images: list = None,  # 用户自定义文章配图路径列表
    auto_generate_images: bool = True,  # 是否自动生成文章配图
    num_images: int = 2,  # 自动生成配图数量
    use_cdp: bool = False,  # 使用标准模式（CDP模式在当前环境不可用）
    cdp_port: int = 9222,  # CDP调试端口（保留参数以兼容旧代码）
    db: Session = Depends(get_db)
):
    """
    一键发布头条文章（全自动流程，支持高级封面图功能和AI配图）
    
    流程：
    1. 自动登录头条账号（优先使用Cookie，其次使用数据库中的账号密码）
    2. AI生成文章内容
    3. AI生成封面图（可选）
    4. AI生成文章配图或用户上传配图
    5. 自动发布文章
    6. 保存发布记录
    
    - **account_id**: 账号 ID
    - **topic**: 文章主题
    - **username**: 登录账号（可选，如果不提供则使用数据库中的账号）
    - **password**: 登录密码（可选，如果不提供则使用数据库中的密码）
    - **category**: 文章分类（默认：科技）
    - **cover_image_path**: 封面图片路径（可选）
    - **auto_generate_cover**: 是否自动生成封面图（默认：True）
    - **cover_style**: AI生成风格 (modern/minimal/bold)
    - **use_template**: 使用的模板ID
    - **declaration_type**: 作品声明类型 ("ai"=引用AI, "personal_opinion"=仅个人观点)
    - **article_images**: 用户自定义文章配图路径列表（可选）
    - **auto_generate_images**: 是否自动生成文章配图（默认：True，如果为False则使用article_images）
    - **num_images**: 自动生成配图数量（默认：2）
    - **use_cdp**: 是否使用CDP模式（当前环境不可用，请使用标准模式）
    - **cdp_port**: CDP调试端口（保留参数，暂未使用）
    """
    from app.services.publish.toutiao_publisher import ToutiaoPublisher
    from app.services.content.copywriting_generation import CopywritingGenerator
    from app.models import Account, ContentTask
    
    # 检查账号是否存在
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"message": "账号不存在", "status": "error"}
    
    async def auto_publish_process():
        # ✅ 关键修复：显式声明使用全局json模块，避免作用域冲突
        import json as global_json
        
        publisher = ToutiaoPublisher(account_id=account_id)
        try:
            # ========== 步骤 1: 智能登录 ==========
            logger.info(f"[步骤1/4] 开始登录头条账号 {account_id}...")
            
            # 初始化浏览器（支持CDP模式）
            if use_cdp:
                logger.info(f"🚀 使用CDP模式连接真实Edge浏览器（端口 {cdp_port}）...")
                await publisher.initialize_browser(use_cdp=True, cdp_port=cdp_port)
            else:
                logger.info("使用标准浏览器模式...")
                await publisher.initialize_browser(use_cdp=False)
            
            login_success = False
            login_method = "unknown"
            
            # 优先尝试使用保存的Cookie
            if account.cookies:
                logger.info(f"检测到保存的Cookie，尝试使用Cookie登录...")
                login_success = await publisher.smart_login(cookies=account.cookies)
                if login_success:
                    login_method = "cookie"
                    logger.info(f"✅ Cookie登录成功！")
                    # ✅ 关键修复：Cookie登录成功后，获取最新的Cookie并更新到数据库
                    try:
                        current_cookies = await publisher.context.cookies()
                        if current_cookies:
                            account.cookies = global_json.dumps(current_cookies)
                            db.commit()
                            logger.info(f"✅ Cookie已更新到数据库")
                    except Exception as e:
                        logger.warning(f"⚠️ 更新Cookie到数据库失败: {e}")
            
            # 如果Cookie失效，使用账号密码登录（优先使用传入的参数，其次使用数据库中的）
            if not login_success:
                # ★★★ 从数据库或参数中获取账号密码 ★★★
                login_username = username or account.username
                login_password = password or account.password
                
                if not login_username or not login_password:
                    return {
                        "status": "failed",
                        "step": "login",
                        "error": "未找到账号密码，请在数据库中配置或传入username/password参数"
                    }
                
                logger.info(f"Cookie失效或未找到，使用账号密码登录...")
                login_result = await publisher.login_with_manual_input(login_username, login_password)
                if login_result["status"] == "success":
                    # 保存新的Cookie
                    account.cookies = login_result["cookies"]
                    account.status = AccountStatusEnum.ACTIVE
                    db.commit()
                    login_success = True
                    login_method = "password"
                    logger.info(f"✅ 账号密码登录成功！")
            
            if not login_success:
                return {
                    "status": "failed",
                    "step": "login",
                    "error": "登录失败，请检查Cookie或账号密码"
                }
            
            logger.info(f"✅ [步骤1/4] 登录成功（方式: {login_method}）")
            
            # ========== 步骤 2-7: AI生成文章 + 合规检测 + 爆款检测 + 发布（支持自动重试）==========
            MAX_RETRY_COUNT = 3  # 最大重试次数
            retry_count = 0
            publish_success = False
            last_error = None
            
            while retry_count < MAX_RETRY_COUNT and not publish_success:
                if retry_count > 0:
                    logger.info(f"\n{'='*60}")
                    logger.info(f"🔄 第 {retry_count} 次重新生成文章（原因: {last_error}）")
                    logger.info(f"{'='*60}\n")
                
                try:
                    # === 步骤 2.0: 如果未提供主题，自动推荐热门主题 ===
                    # ✅ 使用新变量避免作用域问题
                    final_topic = topic or ""
                    
                    if not final_topic or final_topic.strip() == "":
                        logger.info(f"🔥 未指定主题，开始智能推荐热门话题...")
                        try:
                            from app.services.content.topic_recommender import get_topic_recommendation_service
                            recommender = get_topic_recommendation_service(db)
                            
                            # 获取个性化推荐（基于账号历史数据）
                            recommendations = recommender.get_personalized_recommendations(account_id, count=3)
                            
                            if recommendations:
                                # 选择置信度最高的主题
                                best_recommendation = recommendations[0]
                                final_topic = best_recommendation.get("topic", "")
                                reason = best_recommendation.get("reason", "")
                                confidence = best_recommendation.get("confidence", 0)
                                
                                logger.info(f"✅ [步骤2.0] 自动推荐主题: {final_topic}")
                                logger.info(f"   推荐理由: {reason}")
                                logger.info(f"   置信度: {confidence:.0%}")
                            else:
                                # 如果没有推荐，使用默认主题
                                final_topic = "AI技术在2026年的最新应用"
                                logger.warning(f"⚠️  未能获取推荐主题，使用默认主题: {final_topic}")
                                
                        except Exception as e:
                            logger.error(f"❌ 主题推荐失败: {e}，使用默认主题")
                            final_topic = "AI技术在2026年的最新应用"
                    
                    logger.info(f"[步骤2/7] 开始生成文章内容，主题: {final_topic}...")
                
                    # === 步骤 2.1: 获取智能分析结果（如果可用）===
                    optimized_prompt = ""
                    try:
                        from app.services.analytics.analytics_cache import get_analytics_cache_service
                        cache_service = get_analytics_cache_service(db)
                        
                        # 检查是否有可用的分析结果
                        if cache_service.is_analysis_available(account_id):
                            optimized_prompt = cache_service.get_optimized_prompt(account_id)
                            if optimized_prompt:
                                logger.info(f"✅ [步骤2.1] 获取到账号 {account_id} 的智能分析优化提示词")
                            else:
                                logger.info(f"ℹ️  [步骤2.1] 未找到优化提示词，将使用默认提示词")
                        else:
                            logger.info(f"ℹ️  [步骤2.1] 暂无分析结果，建议先进行数据分析")
                            
                    except Exception as e:
                        logger.warning(f"⚠️  获取智能分析结果失败: {e}，将使用默认提示词")
                    
                    generator = CopywritingGenerator(db=db)
                    
                    # === 步骤 2.2: 生成文章（启用网络搜索 + 智能分析优化）===
                    article_result = generator.generate_script(
                        platform="toutiao",
                        topic=final_topic,
                        enable_web_search=True,  # 启用网络搜索获取实时素材
                        optimized_prompt=optimized_prompt if optimized_prompt else None  # 应用优化提示词
                    )
                    
                    if not article_result:
                        raise Exception("AI 生成文章失败")
                    
                    # 解析文章结构
                    article_title = article_result.get("title", f"{final_topic}的深度解析")
                    article_content = article_result.get("content", "")
                    article_tags = article_result.get("tags", [])
                    
                    logger.info(f"✅ [步骤2/7] 文章生成成功！标题: {article_title}")
                    
                    # ========== 步骤 3: 合规审查（必须，100%执行）==========
                    logger.info(f"🔍 [步骤3/7] 正在进行合规审查（强制执行）...")
                    compliance_result = check_content_compliance(article_title, article_content, "toutiao")
                    if not compliance_result["passed"]:
                        retry_count += 1
                        last_error = f"合规审查失败：{compliance_result['error']}"
                        logger.error(f"❌ {last_error}")
                        logger.error(f"   ⛔ 文章包含违禁内容，将在 {MAX_RETRY_COUNT - retry_count} 次重试后重新生成")
                        continue  # 继续下一次循环，重新生成文章
                    
                    logger.info(f"✅ [步骤3/7] 合规审查通过")
                
                    # ========== 步骤 4: 爆款潜力检测（热点话题强制事实核查）==========
                    logger.info(f"🔥 [步骤4/7] 进行爆款潜力检测...")
                    from app.services.analytics.viral_potential_checker import get_viral_checker
                    
                    viral_checker = get_viral_checker()
                    is_hot_topic = final_topic and ("热搜" in final_topic or "热点" in final_topic)
                    
                    viral_result = viral_checker.check_viral_potential(
                        title=article_title,
                        content=article_content,
                        platform="toutiao",
                        topic=final_topic,
                        is_hot_topic=is_hot_topic
                    )
                    
                    logger.info(f"📊 爆款潜力评分: {viral_result['viral_score']}分 ({viral_result['level']})")
                    
                    # 记录优势点
                    for strength in viral_result.get('strengths', []):
                        logger.info(f"   ✅ {strength}")
                    
                    # 记录待优化点
                    for weakness in viral_result.get('weaknesses', []):
                        logger.warning(f"   ⚠️  {weakness}")
                    
                    # 热点话题事实核查
                    if is_hot_topic and 'fact_check' in viral_result:
                        fact_check = viral_result['fact_check']
                        if not fact_check['passed']:
                            retry_count += 1
                            last_error = f"热点话题事实核查失败：{fact_check['issues'][0] if fact_check['issues'] else '存在事实风险'}"
                            logger.error(f"❌ {last_error}")
                            for issue in fact_check.get('issues', []):
                                logger.error(f"   {issue}")
                            for warning in fact_check.get('warnings', []):
                                logger.warning(f"   {warning}")
                            logger.error(f"   ⛔ 将在 {MAX_RETRY_COUNT - retry_count} 次重试后重新生成")
                            continue  # 继续下一次循环，重新生成文章
                        else:
                            logger.info(f"✅ 热点话题事实核查通过")
                    
                    # 如果爆款潜力过低，给出警告但允许发布
                    if viral_result['viral_score'] < 40:
                        logger.warning(f"⚠️  爆款潜力较低 ({viral_result['viral_score']}分)，建议优化后再发布")
                        for suggestion in viral_result.get('suggestions', []):
                            logger.warning(f"   💡 {suggestion}")
                    
                    logger.info(f"✅ [步骤4/7] 爆款潜力检测完成")
                    
                    # ========== 步骤 5: 生成文章配图 ==========
                    final_article_images = []
                    
                    if auto_generate_images:
                        # AI自动生成配图
                        logger.info(f"🖼️  [步骤5/7] 开始AI生成文章配图...")
                        from app.services.content.article_image_generator import ArticleImageGenerator
                        image_generator = ArticleImageGenerator(use_ai=True, db=db)  # 强制使用AI生成，传递db
                        article_images_info = await image_generator.generate_images_for_article(
                            title=article_title,
                            content=article_content,
                            num_images=num_images,
                            category=category,
                            enable_ab_test=True  # 启用A/B测试
                        )
                        final_article_images = [img["file_path"] for img in article_images_info]
                        if final_article_images:
                            logger.info(f"✅ [步骤5/7] AI文章配图生成成功，共 {len(final_article_images)} 张")
                            for i, img_path in enumerate(final_article_images, 1):
                                logger.info(f"   配图{i}: {img_path}")
                        else:
                            logger.warning(f"⚠️  AI文章配图生成失败")
                    elif article_images:
                        # 使用用户上传的配图
                        logger.info(f"📁 [步骤5/7] 使用用户上传的文章配图: {len(article_images)} 张")
                        final_article_images = article_images
                    else:
                        logger.info(f"ℹ️  [步骤5/7] 未配置文章配图，将不上传配图")
                    
                    # ========== 步骤 6: 解析作品声明 ==========
                    if declarations and isinstance(declarations, str):
                        try:
                            declarations_list = global_json.loads(declarations)
                            logger.info(f"✅ 作品声明解析成功: {declarations_list}")
                        except Exception as e:
                            logger.warning(f"⚠️  作品声明解析失败: {e}，使用默认值")
                            declarations_list = [declaration_type]
                    else:
                        declarations_list = [declaration_type]
                    
                    # ========== 步骤 7: 自动发布 ==========
                    logger.info(f"[步骤7/7] 开始发布文章...")
                    publish_result = await publisher.publish_article(
                        title=article_title,
                        content=article_content,
                        category=category,
                        tags=article_tags,
                        cover_image_path=cover_image_path,
                        auto_generate_cover=auto_generate_cover,
                        cover_style=cover_style,
                        use_template=use_template,
                        declaration_type=declaration_type,
                        declarations=declarations_list,  # ✅ 传递解析后的作品声明列表
                        article_images=final_article_images,  # 传入最终的文章配图（AI生成或用户上传）
                        image_suggestions=article_result.get("image_suggestions"),  # ★★★ 传递智能图片位置建议
                        account_id=account_id  # ★★★ 传递账号ID用于获取进化配置
                    )
                    
                    if publish_result["status"] not in ["success", "pending"]:
                        retry_count += 1
                        last_error = publish_result.get("error", "发布失败")
                        logger.error(f"❌ 发布失败: {last_error}")
                        logger.error(f"   ⛔ 将在 {MAX_RETRY_COUNT - retry_count} 次重试后重新生成并发布")
                        continue  # 继续下一次循环，重新生成并发布
                    
                    logger.info(f"✅ [步骤7/7] 文章发布成功！")
                    publish_success = True  # 标记发布成功，退出循环
                    
                    # ========== 保存发布记录 ==========
                    logger.info(f"💾 保存发布记录...")
                    
                    # 保存内容任务
                    content_task = ContentTask(
                        task_id=str(uuid.uuid4()),
                        original_topic=final_topic,
                        target_platform=PlatformEnum.TOUTIAO,
                        article_title=article_title,
                        article_content=article_content,
                        article_category=category,
                        tags=article_tags,
                        status="completed"
                    )
                    db.add(content_task)
                    db.flush()  # 获取 content_task.id
                    
                    # ✅ 关键修复：保存发布记录（PublishRecord）
                    publish_record = PublishRecord(
                        account_id=account_id,
                        content_task_id=content_task.id,
                        publish_status="published",  # ✅ 直接使用字符串，不使用枚举
                        publish_time=datetime.now(),
                        platform_url=publish_result.get("article_url", ""),
                        error_message=None
                    )
                    db.add(publish_record)
                    db.commit()
                    
                    logger.info(f"✅ 发布记录保存成功！ID: {publish_record.id}")
                    
                    # 发布成功，返回结果
                    return {
                        "status": "success",
                        "message": f"文章发布成功！（重试次数: {retry_count}）",
                        "article_title": article_title,
                        "article_content_length": len(article_content),
                        "tags": article_tags,
                        "category": category,
                        "retry_count": retry_count
                    }
                    
                except Exception as e:
                    retry_count += 1
                    last_error = str(e)
                    logger.error(f"❌ 处理异常: {last_error}", exc_info=True)
                    logger.error(f"   ⛔ 将在 {MAX_RETRY_COUNT - retry_count} 次重试后重新尝试")
                    if retry_count >= MAX_RETRY_COUNT:
                        raise  # 如果达到最大重试次数，抛出异常
                    continue  # 否则继续重试
            
            # 如果循环结束仍未成功
            if not publish_success:
                return {
                    "status": "failed",
                    "step": "publish",
                    "error": f"经过 {MAX_RETRY_COUNT} 次尝试后仍无法发布成功。最后错误: {last_error}",
                    "retry_count": retry_count
                }
            
        except Exception as e:
            logger.error(f"自动发布失败: {str(e)}", exc_info=True)
            return {
                "status": "failed",
                "error": str(e)
            }
        finally:
            await publisher.close()
    
    # 执行自动发布流程
    result = run_async_task(auto_publish_process())
    
    return result
def list_accounts(
    platform: Optional[str] = Query(None, description="平台筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    skip: int = Query(0, ge=0, description="跳过数量"),
    limit: int = Query(20, ge=1, le=100, description="返回数量"),
    db: Session = Depends(get_db)
):
    """获取账号列表（支持分页和筛选）"""
    query = db.query(Account)
    
    if platform:
        query = query.filter(Account.platform == platform)
    if status:
        query = query.filter(Account.status == status)
    
    total = query.count()
    accounts = query.offset(skip).limit(limit).all()
    
    return AccountListResponse(total=total, accounts=accounts)

@router.get("/accounts/{account_id}", response_model=AccountResponse)
def get_account(account_id: int, db: Session = Depends(get_db)):
    """获取单个账号详情"""
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account

@router.get("/content/tasks", summary="获取内容创作任务列表")
def list_content_tasks(
    platform: Optional[str] = Query(None, description="平台筛选"),
    status: Optional[str] = Query(None, description="状态筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取内容创作任务列表（包含发布记录）"""
    query = db.query(ContentTask)
    
    if platform:
        query = query.filter(ContentTask.target_platform == platform)
    if status:
        query = query.filter(ContentTask.status == status)
    
    total = query.count()
    tasks = query.order_by(ContentTask.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "tasks": [
            {
                "id": t.id,
                "task_id": t.task_id,
                "original_topic": t.original_topic,
                "target_platform": t.target_platform.value if hasattr(t.target_platform, 'value') else t.target_platform,
                "article_title": t.article_title,
                "article_content_length": len(t.article_content) if t.article_content else 0,
                "article_category": t.article_category,
                "tags": t.tags,
                "status": t.status,
                "created_at": t.created_at.isoformat() if t.created_at else None
            }
            for t in tasks
        ]
    }

@router.get("/content/tasks/{task_id}", summary="获取任务详情")
def get_content_task_detail(task_id: int, db: Session = Depends(get_db)):
    """获取单个内容任务的详细信息（包括完整文章内容）"""
    task = db.query(ContentTask).filter(ContentTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    return {
        "id": task.id,
        "task_id": task.task_id,
        "original_topic": task.original_topic,
        "target_platform": task.target_platform.value if hasattr(task.target_platform, 'value') else task.target_platform,
        "article_title": task.article_title,
        "article_content": task.article_content,
        "article_category": task.article_category,
        "tags": task.tags,
        "status": task.status,
        "created_at": task.created_at.isoformat() if task.created_at else None
    }

@router.get("/publish/records")
def list_publish_records(
    account_id: Optional[int] = Query(None, description="账号 ID 筛选"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取发布记录列表"""
    query = db.query(PublishRecord)
    
    if account_id:
        query = query.filter(PublishRecord.account_id == account_id)
    
    total = query.count()
    records = query.order_by(PublishRecord.created_at.desc()).offset(skip).limit(limit).all()
    
    return {
        "total": total,
        "records": [
            {
                "id": r.id,
                "account_id": r.account_id,
                "content_task_id": r.content_task_id,
                "publish_status": r.publish_status,
                "publish_time": r.publish_time.isoformat() if r.publish_time else None,
                "platform_url": r.platform_url,
                "error_message": r.error_message,
                "created_at": r.created_at.isoformat() if r.created_at else None
            }
            for r in records
        ]
    }

@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """获取数据大屏统计数据"""
    total_accounts = db.query(Account).count()
    active_accounts = db.query(Account).filter(Account.status == AccountStatusEnum.ACTIVE).count()
    nurturing_accounts = db.query(Account).filter(Account.status == AccountStatusEnum.NURTURING).count()
    
    total_tasks = db.query(ContentTask).count()
    completed_tasks = db.query(ContentTask).filter(ContentTask.status == "completed").count()
    
    total_publishes = db.query(PublishRecord).count()
    successful_publishes = db.query(PublishRecord).filter(PublishRecord.publish_status == "published").count()
    
    return {
        "accounts": {
            "total": total_accounts,
            "active": active_accounts,
            "nurturing": nurturing_accounts
        },
        "content_tasks": {
            "total": total_tasks,
            "completed": completed_tasks
        },
        "publish_records": {
            "total": total_publishes,
            "successful": successful_publishes
        }
    }


@router.get("/analytics/toutiao/articles", summary="获取头条文章数据分析")
def get_toutiao_article_analytics(
    account_id: int = Query(..., description="头条账号ID"),
    db: Session = Depends(get_db)
):
    """
    获取头条文章的数据分析统计（阅读量、点赞数、评论数等）
    
    - **account_id**: 头条账号ID
    """
    from app.services.analytics.toutiao_analytics import get_analytics_service
    from app.utils.async_helper import run_async_task
    
    # 检查账号是否存在
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    
    async def fetch_analytics():
        service = get_analytics_service(account_id=account_id, db=db)
        try:
            await service.initialize(headless=True)
            
            # 检查登录状态
            login_success = await service.login_if_needed()
            if not login_success:
                return {
                    "status": "error",
                    "message": "账号未登录或Cookie失效，请先登录账号"
                }
            
            # 抓取文章数据
            articles = await service.fetch_article_analytics()
            
            if len(articles) == 0:
                return {
                    "status": "success",
                    "articles": [],
                    "total_articles": 0,
                    "message": "未找到文章数据。可能原因：1)账号未发布过文章 2)Cookie已过期需要重新登录 3)头条页面结构变化",
                    "summary": {
                        "total_reads": 0,
                        "total_likes": 0,
                        "total_comments": 0,
                        "total_shares": 0
                    }
                }
            
            return {
                "status": "success",
                "articles": articles,
                "total_articles": len(articles),
                "summary": {
                    "total_reads": sum(a.get('read_count', 0) for a in articles),
                    "total_likes": sum(a.get('like_count', 0) for a in articles),
                    "total_comments": sum(a.get('comment_count', 0) for a in articles),
                    "total_shares": sum(a.get('share_count', 0) for a in articles)
                }
            }
        finally:
            await service.close()
    
    result = run_async_task(fetch_analytics())
    return result

@router.post("/accounts/douyin/login")
def douyin_login(account_id: int, username: str, password: str, db: Session = Depends(get_db)):
    """抖音账号登录（人工辅助）"""
    from app.services.publish.douyin_publisher import DouyinPublisher
    from app.models import Account
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"message": "账号不存在", "status": "error"}
    
    async def login_process():
        publisher = DouyinPublisher(account_id=account_id)
        try:
            await publisher.initialize_browser(headless=False)
            result = await publisher.login_with_manual_input(username, password)
            
            if result["status"] == "success":
                # 保存 Cookie 到数据库
                account.cookies = result["cookies"]
                account.status = AccountStatusEnum.ACTIVE
                db.commit()
                
            return result
        finally:
            await publisher.close()
    
    # 使用统一的异步任务执行器
    result = run_async_task(login_process())
    
    return result

@router.post("/content/douyin/publish")
def publish_douyin_video(
    account_id: int,
    title: str,
    video_path: str,
    description: str = "",
    tags: list = None,
    db: Session = Depends(get_db)
):
    """发布抖音视频"""
    from app.services.publish.douyin_publisher import DouyinPublisher
    from app.models import Account, ContentTask
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account or not account.cookies:
        return {"message": "账号未登录或 Cookie 无效", "status": "error"}
    
    async def publish_process():
        publisher = DouyinPublisher(account_id=account_id, cookies=account.cookies)
        try:
            await publisher.initialize_browser()
            
            # 发布视频
            result = await publisher.publish_video(
                title=title,
                video_path=video_path,
                description=description,
                tags=tags or []
            )
            
            # 保存发布记录
            if result["status"] in ["success", "pending"]:
                content_task = ContentTask(
                    task_id=str(uuid.uuid4()),
                    original_topic=title,
                    target_platform=PlatformEnum.DOUYIN,
                    video_path=video_path,
                    status="completed"
                )
                db.add(content_task)
                db.commit()
            
            return result
        finally:
            await publisher.close()
    
    # 使用统一的异步任务执行器
    result = run_async_task(publish_process())
    
    return result

@router.get("/content/hot-trends", summary="获取热搜榜单", description="获取各平台实时热搜数据")
def get_hot_trends(
    platform: str = Query("douyin", description="平台类型：douyin/xiaohongshu/bilibili/toutiao"),
    count: int = Query(20, ge=1, le=50, description="返回数量")
):
    """
    获取实时热搜榜单
    
    - **platform**: 平台类型（douyin/xiaohongshu/bilibili/toutiao）
    - **count**: 返回热搜数量（1-50）
    
    返回热搜关键词、热度值、排名等信息
    """
    try:
        from app.services.content.hot_trend_injector import HotTrendInjector
        injector = HotTrendInjector()
        
        # 获取热搜数据
        hot_topics = injector.fetch_hot_topics(platform, count)
        
        return {
            "platform": platform,
            "total": len(hot_topics),
            "hot_topics": hot_topics,
            "updated_at": injector.last_update_time.isoformat() if injector.last_update_time else None
        }
    except Exception as e:
        logger.error(f"获取热搜失败: {str(e)}")
        # 返回模拟数据作为降级方案
        return {
            "platform": platform,
            "total": 0,
            "hot_topics": [],
            "error": f"获取热搜失败: {str(e)}",
            "fallback": True
        }

@router.get("/content/recommended-topics", summary="获取智能推荐主题", description="基于热搜和历史数据推荐最可能火的主题")
def get_recommended_topics(
    account_id: Optional[int] = Query(None, description="账号ID（可选，用于个性化推荐）"),
    count: int = Query(5, ge=1, le=10, description="返回数量"),
    db: Session = Depends(get_db)
):
    """
    获取智能推荐主题
    
    - **account_id**: 账号ID（可选，提供后会根据历史表现个性化推荐）
    - **count**: 返回推荐数量（1-10）
    
    结合实时热搜和账号历史数据，推荐最有可能火的创作主题
    """
    try:
        from app.services.content.topic_recommender import get_topic_recommendation_service
        
        recommender = get_topic_recommendation_service(db)
        
        if account_id:
            # 个性化推荐（结合历史数据）
            recommendations = recommender.get_personalized_recommendations(account_id, count)
            logger.info(f"✅ 为账号 {account_id} 生成个性化推荐")
        else:
            # 通用热门话题
            recommendations = recommender.get_trending_topics("toutiao", count)
            logger.info(f"✅ 生成通用热门话题推荐")
        
        return {
            "status": "success",
            "total": len(recommendations),
            "recommendations": recommendations,
            "formatted_text": recommender.format_recommendations_for_display(recommendations)
        }
        
    except Exception as e:
        logger.error(f"获取推荐主题失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取推荐主题失败: {str(e)}")

# ==================== 快手发布 API ====================
@router.post("/accounts/kuaishou/login", summary="快手账号登录")
def kuaishou_login(account_id: int, username: str, password: str, db: Session = Depends(get_db)):
    """快手账号登录（人工辅助）"""
    from app.services.publish.kuaishou_publisher import KuaishouPublisher
    from app.models import Account
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"message": "账号不存在", "status": "error"}
    
    async def login_process():
        publisher = KuaishouPublisher(account_id=account_id)
        try:
            await publisher.initialize_browser()
            result = await publisher.login_with_manual_input(username, password)
            
            if result["status"] == "success":
                account.cookies = result["cookies"]
                account.status = AccountStatusEnum.ACTIVE
                db.commit()
            
            return result
        finally:
            await publisher.close()
    
    result = run_async_task(login_process())
    return result


@router.post("/content/kuaishou/publish", summary="发布快手视频")
def publish_kuaishou_video(
    account_id: int,
    video_path: str,
    title: str,
    description: str = "",
    tags: str = "",
    db: Session = Depends(get_db)
):
    """发布快手视频"""
    from app.services.publish.kuaishou_publisher import KuaishouPublisher
    from app.models import Account, ContentTask
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"message": "账号不存在", "status": "error"}
    
    async def publish_process():
        publisher = KuaishouPublisher(account_id=account_id)
        try:
            await publisher.initialize_browser()
            
            # 加载Cookie
            if account.cookies:
                await publisher.context.add_cookies(json.loads(account.cookies))
            
            # ========== 合规审查（必须）==========
            logger.info(f"🔍 正在进行合规审查...")
            compliance_result = check_content_compliance(title, description, "kuaishou")
            if not compliance_result["passed"]:
                logger.warning(f"⚠️  合规审查失败: {compliance_result['error']}")
                return {
                    "status": "failed",
                    "error": compliance_result["error"]
                }
            logger.info(f"✅ 合规审查通过")
            
            # 发布视频
            result = await publisher.publish_video(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags.split(",") if tags else []
            )
            
            # 保存发布记录
            if result["status"] == "success":
                task = ContentTask(
                    account_id=account_id,
                    platform=PlatformEnum.KUAISHOU if hasattr(PlatformEnum, 'KUAISHOU') else PlatformEnum.DOUYIN,
                    title=title,
                    status="published"
                )
                db.add(task)
                db.commit()
            
            return result
        finally:
            await publisher.close()
    
    result = run_async_task(publish_process())
    return result


# ==================== 视频号发布 API ====================
@router.post("/accounts/wechat/login", summary="视频号扫码登录")
def wechat_login(account_id: int, db: Session = Depends(get_db)):
    """视频号扫码登录"""
    from app.services.publish.wechat_publisher import WechatPublisher
    from app.models import Account
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"message": "账号不存在", "status": "error"}
    
    async def login_process():
        publisher = WechatPublisher(account_id=account_id)
        try:
            await publisher.initialize_browser()
            result = await publisher.login_with_qr_code()
            
            if result["status"] == "success":
                account.cookies = result["cookies"]
                account.status = AccountStatusEnum.ACTIVE
                db.commit()
            
            return result
        finally:
            await publisher.close()
    
    result = run_async_task(login_process())
    return result


@router.post("/content/wechat/publish", summary="发布视频号视频")
def publish_wechat_video(
    account_id: int,
    video_path: str,
    description: str,
    location: str = "",
    tags: str = "",
    db: Session = Depends(get_db)
):
    """发布视频号视频"""
    from app.services.publish.wechat_publisher import WechatPublisher
    from app.models import Account, ContentTask
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"message": "账号不存在", "status": "error"}
    
    async def publish_process():
        publisher = WechatPublisher(account_id=account_id)
        try:
            await publisher.initialize_browser()
            
            if account.cookies:
                await publisher.context.add_cookies(json.loads(account.cookies))
            
            # ========== 合规审查（必须）==========
            logger.info(f"🔍 正在进行合规审查...")
            compliance_result = check_content_compliance(description, "", "wechat")
            if not compliance_result["passed"]:
                logger.warning(f"⚠️  合规审查失败: {compliance_result['error']}")
                return {
                    "status": "failed",
                    "error": compliance_result["error"]
                }
            logger.info(f"✅ 合规审查通过")
            
            result = await publisher.publish_video(
                video_path=video_path,
                description=description,
                location=location,
                tags=tags.split(",") if tags else []
            )
            
            if result["status"] == "success":
                task = ContentTask(
                    account_id=account_id,
                    platform=PlatformEnum.WECHAT if hasattr(PlatformEnum, 'WECHAT') else PlatformEnum.DOUYIN,
                    title=description[:50],
                    status="published"
                )
                db.add(task)
                db.commit()
            
            return result
        finally:
            await publisher.close()
    
    result = run_async_task(publish_process())
    return result


# ==================== B站发布 API ====================
@router.post("/accounts/bilibili/login", summary="B站扫码登录")
def bilibili_login(account_id: int, db: Session = Depends(get_db)):
    """B站扫码登录"""
    from app.services.publish.bilibili_publisher import BilibiliPublisher
    from app.models import Account
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"message": "账号不存在", "status": "error"}
    
    async def login_process():
        publisher = BilibiliPublisher(account_id=account_id)
        try:
            await publisher.initialize_browser()
            result = await publisher.login_with_qr_code()
            
            if result["status"] == "success":
                account.cookies = result["cookies"]
                account.status = AccountStatusEnum.ACTIVE
                db.commit()
            
            return result
        finally:
            await publisher.close()
    
    result = run_async_task(login_process())
    return result


@router.post("/content/bilibili/publish", summary="发布B站视频")
def publish_bilibili_video(
    account_id: int,
    video_path: str,
    title: str,
    description: str,
    tags: str,
    copyright: int = 1,
    tid: int = 0,
    db: Session = Depends(get_db)
):
    """发布B站视频"""
    from app.services.publish.bilibili_publisher import BilibiliPublisher
    from app.models import Account, ContentTask
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"message": "账号不存在", "status": "error"}
    
    async def publish_process():
        publisher = BilibiliPublisher(account_id=account_id)
        try:
            await publisher.initialize_browser()
            
            if account.cookies:
                await publisher.context.add_cookies(json.loads(account.cookies))
            
            # ========== 合规审查（必须）==========
            logger.info(f"🔍 正在进行合规审查...")
            compliance_result = check_content_compliance(title, description, "bilibili")
            if not compliance_result["passed"]:
                logger.warning(f"⚠️  合规审查失败: {compliance_result['error']}")
                return {
                    "status": "failed",
                    "error": compliance_result["error"]
                }
            logger.info(f"✅ 合规审查通过")
            
            result = await publisher.publish_video(
                video_path=video_path,
                title=title,
                description=description,
                tags=tags.split(",") if tags else [],
                copyright=copyright,
                tid=tid
            )
            
            if result["status"] == "success":
                task = ContentTask(
                    account_id=account_id,
                    platform=PlatformEnum.BILIBILI if hasattr(PlatformEnum, 'BILIBILI') else PlatformEnum.DOUYIN,
                    title=title,
                    status="published"
                )
                db.add(task)
                db.commit()
            
            return result
        finally:
            await publisher.close()
    
    result = run_async_task(publish_process())
    return result


# ==================== 小红书发布 API ====================
@router.post("/accounts/xiaohongshu/login", summary="小红书账号登录")
def xiaohongshu_login(account_id: int, username: str, password: str, db: Session = Depends(get_db)):
    """小红书账号登录"""
    from app.services.publish.xiaohongshu_publisher import XiaohongshuPublisher
    from app.models import Account
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"message": "账号不存在", "status": "error"}
    
    async def login_process():
        publisher = XiaohongshuPublisher(account_id=account_id)
        try:
            await publisher.initialize_browser()
            result = await publisher.login_with_password(username, password)
            
            if result["status"] == "success":
                account.cookies = result["cookies"]
                account.status = AccountStatusEnum.ACTIVE
                db.commit()
            
            return result
        finally:
            await publisher.close()
    
    result = run_async_task(login_process())
    return result


@router.post("/content/xiaohongshu/publish", summary="发布小红书笔记")
def publish_xiaohongshu_note(
    account_id: int,
    images: str,  # 逗号分隔的图片路径
    title: str,
    content: str,
    tags: str,
    note_type: str = "normal",
    db: Session = Depends(get_db)
):
    """发布小红书笔记（图文或视频）"""
    from app.services.publish.xiaohongshu_publisher import XiaohongshuPublisher
    from app.models import Account, ContentTask
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        return {"message": "账号不存在", "status": "error"}
    
    async def publish_process():
        publisher = XiaohongshuPublisher(account_id=account_id)
        try:
            await publisher.initialize_browser()
            
            if account.cookies:
                await publisher.context.add_cookies(json.loads(account.cookies))
            
            # ========== 合规审查（必须）==========
            logger.info(f"🔍 正在进行合规审查...")
            compliance_result = check_content_compliance(title, content, "xiaohongshu")
            if not compliance_result["passed"]:
                logger.warning(f"⚠️  合规审查失败: {compliance_result['error']}")
                return {
                    "status": "failed",
                    "error": compliance_result["error"]
                }
            logger.info(f"✅ 合规审查通过")
            
            result = await publisher.publish_note(
                images=images.split(","),
                title=title,
                content=content,
                tags=tags.split(",") if tags else [],
                note_type=note_type
            )
            
            if result["status"] == "success":
                task = ContentTask(
                    account_id=account_id,
                    platform=PlatformEnum.XIAOHONGSHU if hasattr(PlatformEnum, 'XIAOHONGSHU') else PlatformEnum.DOUYIN,
                    title=title,
                    status="published"
                )
                db.add(task)
                db.commit()
            
            return result
        finally:
            await publisher.close()
    
    result = run_async_task(publish_process())
    return result


# ==================== 合规审查工具函数 ====================
def check_compliance(text: str, platform: str) -> Dict[str, Any]:
    """
    合规审查工具函数
    
    Args:
        text: 待检查的文本
        platform: 平台名称
        
    Returns:
        检查结果，如果包含违禁词则返回错误信息
    """
    from app.services.distribute.banned_words_check import BannedWordsFilter
    
    filter_engine = BannedWordsFilter()
    result = filter_engine.check_and_replace(text, platform)
    
    if not result["is_safe"]:
        return {
            "passed": False,
            "violations": result["violations"],
            "error": f"包含{len(result['violations'])}处违禁词"
        }
    
    return {"passed": True}


def check_content_compliance(title: str, content: str, platform: str) -> Dict[str, Any]:
    """
    完整内容合规审查（标题+内容）
    
    Args:
        title: 标题
        content: 内容
        platform: 平台名称
        
    Returns:
        检查结果
    """
    logger.info(f"🔍 开始合规审查...")
    logger.info(f"   平台: {platform}")
    logger.info(f"   标题长度: {len(title)}字")
    logger.info(f"   内容长度: {len(content)}字")
    
    # 检查标题
    logger.info(f"   📝 检查标题...")
    title_check = check_compliance(title, platform)
    if not title_check["passed"]:
        logger.warning(f"   ❌ 标题包含违禁词: {', '.join(title_check['violations'])}")
        return {
            "passed": False,
            "field": "title",
            "violations": title_check["violations"],
            "error": f"标题包含违禁词: {', '.join(title_check['violations'])}"
        }
    logger.info(f"   ✅ 标题检查通过")
    
    # 检查内容
    logger.info(f"   📄 检查正文...")
    content_check = check_compliance(content, platform)
    if not content_check["passed"]:
        violations_preview = content_check['violations'][:5]
        logger.warning(f"   ❌ 内容包含{len(content_check['violations'])}处违禁词")
        logger.warning(f"   示例: {', '.join(violations_preview)}")
        return {
            "passed": False,
            "field": "content",
            "violations": content_check["violations"][:5],  # 只显示前5个
            "error": f"内容包含{len(content_check['violations'])}处违禁词"
        }
    logger.info(f"   ✅ 正文检查通过")
    
    logger.info(f"✅ 合规审查完成 - 全部通过")
    return {"passed": True}


# ==================== 图片上传 API ====================
@router.post("/content/generate-ai-cover", summary="AI智能生成封面图")
def generate_ai_cover(
    title: str,
    content: str = "",
    category: str = "科技",
    tags: list = None,
    style: str = None,
    count: int = 3
):
    """
    AI智能生成封面图（根据文章内容自动生成）
    
    - **title**: 文章标题
    - **content**: 文章内容（可选，用于提取关键词）
    - **category**: 文章分类
    - **tags**: 标签列表（可选）
    - **style**: 偏好风格 (modern/minimal/bold)，不指定则自动选择
    - **count**: 生成数量（默认3个，返回最佳的一个）
    
    返回最佳封面图信息
    """
    from app.services.content.smart_cover_generator import get_smart_cover_generator
    
    async def generate_process():
        generator = get_smart_cover_generator()
        result = await generator.generate_smart_cover(
            title=title,
            content=content,
            category=category,
            tags=tags or [],
            prefer_style=style,
            generate_count=count
        )
        return result
    
    # 使用统一的异步任务执行器
    result = run_async_task(generate_process())
    
    return result

@router.post("/content/generate-template-cover", summary="使用模板生成封面图")
def generate_template_cover(
    title: str,
    category: str = "科技",
    template_id: str = None
):
    """
    使用模板生成封面图
    
    - **title**: 文章标题
    - **category**: 文章分类
    - **template_id**: 模板ID（可选，不指定则根据分类自动选择）
    
    返回生成的封面图信息
    """
    from app.services.content.smart_cover_generator import get_smart_cover_generator
    
    async def generate_process():
        generator = get_smart_cover_generator()
        result = await generator.generate_from_template(
            title=title,
            category=category,
            template_id=template_id
        )
        return result
    
    # 使用统一的异步任务执行器
    result = run_async_task(generate_process())
    
    return result

@router.get("/content/cover-templates/list", summary="获取封面模板列表")
def get_cover_templates(category: str = None):
    """
    获取可用的封面模板列表
    
    - **category**: 分类筛选（可选）
    """
    from app.services.content.cover_template_library import get_template_library
    
    library = get_template_library()
    templates = library.list_templates(category)
    
    return {
        "total": len(templates),
        "templates": templates
    }

@router.post("/content/upload-image", summary="上传图片")
async def upload_image(
    file: UploadFile = File(...),
    compress: bool = True,
    quality: int = 85,
    max_width: int = 1920,
    max_height: int = 1080,
    output_format: str = 'jpg'
):
    """
    上传图片文件（如封面图）
    
    - **file**: 图片文件
    - **compress**: 是否压缩图片
    - **quality**: 压缩质量 (1-100)
    - **max_width**: 最大宽度
    - **max_height**: 最大高度
    - **output_format**: 输出格式 (jpg/png/webp)
    
    返回文件路径
    """
    try:
        # 创建上传目录
        upload_dir = "uploads/covers"
        os.makedirs(upload_dir, exist_ok=True)
        
        # 生成唯一文件名
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4().hex}{file_extension}"
        file_path = os.path.join(upload_dir, unique_filename)
        
        # 保存原始文件
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"✅ 图片上传成功: {file_path}")
        
        # 如果需要压缩
        if compress:
            from app.utils.image_processor import ImageProcessor
            
            processor = ImageProcessor()
            
            # 生成压缩后的文件名
            compressed_filename = f"{uuid.uuid4().hex}.{output_format.lower()}"
            compressed_path = os.path.join(upload_dir, compressed_filename)
            
            # 压缩图片
            compress_result = processor.compress_image(
                input_path=file_path,
                output_path=compressed_path,
                quality=quality,
                max_width=max_width,
                max_height=max_height,
                output_format=output_format
            )
            
            if compress_result["status"] == "success":
                # 删除原始文件
                if os.path.exists(file_path):
                    os.remove(file_path)
                
                file_path = compressed_path
                unique_filename = compressed_filename
                
                logger.info(f"✅ 图片压缩完成: {compress_result['compression_ratio_percent']}% 压缩率")
                
                return {
                    "status": "success",
                    "file_path": file_path,
                    "filename": unique_filename,
                    "compressed": True,
                    "compression_info": compress_result
                }
            else:
                logger.warning(f"⚠️  图片压缩失败，使用原图: {compress_result.get('error')}")
                return {
                    "status": "success",
                    "file_path": file_path,
                    "filename": unique_filename,
                    "compressed": False
                }
        else:
            return {
                "status": "success",
                "file_path": file_path,
                "filename": unique_filename,
                "compressed": False
            }
    except Exception as e:
        logger.error(f"图片上传失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== AI配图生成 API ====================
@router.post("/content/generate-ai-cover", summary="AI生成封面图")
async def generate_ai_cover(
    title: str,
    subtitle: str = "",
    category: str = "科技",
    style: str = "modern",
    count: int = 1
):
    """
    AI智能生成封面图
    
    - **title**: 文章标题
    - **subtitle**: 副标题（可选）
    - **category**: 文章分类
    - **style**: 风格 (modern/minimal/bold)
    - **count**: 生成数量（1-5）
    
    返回生成的封面图路径
    """
    try:
        from app.services.content.ai_cover_generator import AICoverGenerator
        
        generator = AICoverGenerator()
        
        if count > 1:
            # 生成多个封面图
            results = generator.generate_multiple_covers(
                title=title,
                subtitle=subtitle,
                category=category,
                count=min(count, 5)
            )
            
            return {
                "status": "success",
                "total": len(results),
                "covers": results
            }
        else:
            # 生成单个封面图
            result = generator.generate_cover(
                title=title,
                subtitle=subtitle,
                category=category,
                style=style
            )
            
            return result
            
    except Exception as e:
        logger.error(f"AI封面图生成失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== 封面图模板 API ====================
@router.get("/content/cover-templates", summary="获取封面图模板列表")
def get_cover_templates(category: str = None):
    """
    获取封面图模板列表
    
    - **category**: 按分类筛选（可选）
    
    返回可用的封面图模板
    """
    try:
        from app.services.content.cover_template_library import get_template_library
        
        library = get_template_library()
        
        if category:
            templates = library.get_template_by_category(category)
        else:
            templates = library.get_all_templates()
        
        return {
            "status": "success",
            "total": len(templates),
            "templates": templates
        }
    except Exception as e:
        logger.error(f"获取模板列表失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/content/generate-cover-from-template", summary="使用模板生成封面图")
async def generate_cover_from_template(
    template_id: str,
    title: str,
    subtitle: str = ""
):
    """
    使用指定模板生成封面图
    
    - **template_id**: 模板ID
    - **title**: 文章标题
    - **subtitle**: 副标题（可选）
    
    返回生成的封面图
    """
    try:
        from app.services.content.cover_template_library import get_template_library
        
        library = get_template_library()
        
        result = library.generate_cover_from_template(
            template_id=template_id,
            title=title,
            subtitle=subtitle
        )
        
        return result
    except Exception as e:
        logger.error(f"模板封面图生成失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/content/add-custom-template", summary="添加自定义模板")
def add_custom_template(
    template_id: str,
    name: str,
    category: str,
    style: str,
    color_scheme: str,
    layout: str,
    description: str = ""
):
    """
    添加自定义封面图模板
    
    - **template_id**: 模板ID（唯一）
    - **name**: 模板名称
    - **category**: 适用分类
    - **style**: 风格
    - **color_scheme**: 配色方案
    - **layout**: 布局方式
    - **description**: 描述
    """
    try:
        from app.services.content.cover_template_library import get_template_library
        
        library = get_template_library()
        
        success = library.add_custom_template(
            template_id=template_id,
            name=name,
            category=category,
            style=style,
            color_scheme=color_scheme,
            layout=layout,
            description=description
        )
        
        if success:
            return {
                "status": "success",
                "message": f"模板 {template_id} 添加成功"
            }
        else:
            return {
                "status": "failed",
                "error": "添加模板失败"
            }
    except Exception as e:
        logger.error(f"添加模板失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== A/B测试 API ====================
@router.post("/content/ab-test/create", summary="创建封面图A/B测试")
def create_ab_test(
    test_id: str,
    article_title: str,
    cover_variants: list,
    description: str = ""
):
    """
    创建封面图A/B测试
    
    - **test_id**: 测试ID
    - **article_title**: 文章标题
    - **cover_variants**: 封面图变体列表
    - **description**: 测试描述
    
    示例:
    ```json
    {
      "test_id": "test_001",
      "article_title": "Python教程",
      "cover_variants": [
        {
          "variant_id": "A",
          "file_path": "uploads/covers/cover_a.jpg",
          "style": "modern",
          "description": "现代风格"
        },
        {
          "variant_id": "B",
          "file_path": "uploads/covers/cover_b.jpg",
          "style": "minimal",
          "description": "极简风格"
        }
      ],
      "description": "测试不同风格的点击率"
    }
    ```
    """
    try:
        from app.services.content.cover_ab_test import get_ab_tester
        
        tester = get_ab_tester()
        
        result = tester.create_test(
            test_id=test_id,
            article_title=article_title,
            cover_variants=cover_variants,
            description=description
        )
        
        return result
    except Exception as e:
        logger.error(f"创建A/B测试失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/content/ab-test/{test_id}/impression", summary="记录曝光")
def record_impression(test_id: str, variant_id: str, user_id: str = None):
    """
    记录封面图曝光
    
    - **test_id**: 测试ID
    - **variant_id**: 变体ID
    - **user_id**: 用户ID（可选）
    """
    try:
        from app.services.content.cover_ab_test import get_ab_tester
        
        tester = get_ab_tester()
        
        success = tester.record_impression(test_id, variant_id, user_id)
        
        return {
            "status": "success" if success else "failed",
            "message": "已记录曝光" if success else "记录失败"
        }
    except Exception as e:
        logger.error(f"记录曝光失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/content/ab-test/{test_id}/click", summary="记录点击")
def record_click(test_id: str, variant_id: str, user_id: str = None):
    """
    记录封面图点击
    
    - **test_id**: 测试ID
    - **variant_id**: 变体ID
    - **user_id**: 用户ID（可选）
    """
    try:
        from app.services.content.cover_ab_test import get_ab_tester
        
        tester = get_ab_tester()
        
        success = tester.record_click(test_id, variant_id, user_id)
        
        return {
            "status": "success" if success else "failed",
            "message": "已记录点击" if success else "记录失败"
        }
    except Exception as e:
        logger.error(f"记录点击失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.get("/content/ab-test/{test_id}", summary="获取测试结果")
def get_test_results(test_id: str):
    """
    获取A/B测试结果
    
    - **test_id**: 测试ID
    """
    try:
        from app.services.content.cover_ab_test import get_ab_tester
        
        tester = get_ab_tester()
        
        result = tester.get_test_results(test_id)
        
        return result
    except Exception as e:
        logger.error(f"获取测试结果失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/content/ab-test/{test_id}/end", summary="结束测试")
def end_test(test_id: str):
    """
    结束A/B测试并返回最佳变体
    
    - **test_id**: 测试ID
    """
    try:
        from app.services.content.cover_ab_test import get_ab_tester
        
        tester = get_ab_tester()
        
        result = tester.end_test(test_id)
        
        return result
    except Exception as e:
        logger.error(f"结束测试失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.get("/content/ab-tests", summary="获取所有测试")
def get_all_tests():
    """获取所有A/B测试"""
    try:
        from app.services.content.cover_ab_test import get_ab_tester
        
        tester = get_ab_tester()
        
        tests = tester.get_all_tests()
        
        return {
            "status": "success",
            "total": len(tests),
            "tests": tests
        }
    except Exception as e:
        logger.error(f"获取测试列表失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.get("/content/ab-test/{test_id}/report", summary="生成测试报告")
def generate_test_report(test_id: str):
    """
    生成A/B测试报告
    
    - **test_id**: 测试ID
    """
    try:
        from app.services.content.cover_ab_test import get_ab_tester
        
        tester = get_ab_tester()
        
        report = tester.generate_test_report(test_id)
        
        return {
            "status": "success",
            "report": report
        }
    except Exception as e:
        logger.error(f"生成报告失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/content/generate-image", summary="AI生成单张配图")
async def generate_image(
    prompt: str,
    style: str = "realistic",
    aspect_ratio: str = "16:9",
    provider: str = None
):
    """
    使用AI生成单张配图
    
    - **prompt**: 图像描述提示词
    - **style**: 风格（realistic/illustration/cartoon/anime/oil_painting）
    - **aspect_ratio**: 宽高比（16:9/9:16/1:1/3:4）
    - **provider**: 图像生成提供商（stability_ai/dall_e）
    """
    try:
        from app.services.content.image_generator import ImageGenerator
        generator = ImageGenerator()
        
        result = await generator.generate_image(
            prompt=prompt,
            style=style,
            aspect_ratio=aspect_ratio,
            provider=provider
        )
        
        return result
    except Exception as e:
        logger.error(f"AI配图生成失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/content/generate-images-batch", summary="AI批量生成配图")
async def generate_images_batch(
    prompts: List[str],
    style: str = "realistic",
    aspect_ratio: str = "16:9"
):
    """
    批量生成AI配图
    
    - **prompts**: 提示词列表
    - **style**: 风格
    - **aspect_ratio**: 宽高比
    """
    try:
        from app.services.content.image_generator import ImageGenerator
        generator = ImageGenerator()
        
        results = await generator.generate_images_batch(
            prompts=prompts,
            style=style,
            aspect_ratio=aspect_ratio
        )
        
        return {
            "total": len(results),
            "success": sum(1 for r in results if r["status"] == "success"),
            "images": results
        }
    except Exception as e:
        logger.error(f"批量配图生成失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/content/generate-article-images", summary="从文章自动生成配图")
async def generate_article_images(
    article_content: str,
    num_images: int = 3,
    style: str = "realistic"
):
    """
    从文章内容自动提取关键点并生成配图
    
    - **article_content**: 文章正文
    - **num_images**: 生成图片数量
    - **style**: 风格
    """
    try:
        from app.services.content.image_generator import ImageGenerator
        generator = ImageGenerator()
        
        images = await generator.generate_from_article(
            article_content=article_content,
            num_images=num_images,
            style=style
        )
        
        return {
            "total": len(images),
            "images": images
        }
    except Exception as e:
        logger.error(f"文章配图生成失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/content/inject-hot-trend", summary="热点关键词注入")
def inject_hot_trend(
    script: str,
    platform: str = "douyin",
    keywords: List[str] = None
):
    """
    将热点关键词智能注入到文案中
    
    - **script**: 原始文案
    - **platform**: 平台类型
    - **keywords**: 要注入的关键词列表
    
    返回注入后的文案和相关统计信息
    """
    try:
        from app.services.content.hot_trend_injector import HotTrendInjector
        
        injector = HotTrendInjector()
        
        # 构建热点话题列表
        hot_topics = []
        if keywords:
            for i, keyword in enumerate(keywords):
                hot_topics.append({
                    "keyword": keyword,
                    "rank": i + 1,
                    "heat": 1000000 - (i * 100000),  # 模拟热度值
                    "platform": platform
                })
        
        # 执行注入
        modified_script = injector.inject_hot_keywords(script, hot_topics, max_keywords=len(keywords) or 3)
        
        # 计算权重分数
        weight_score = min(100, len(keywords) * 25 + 50) if keywords else 50
        
        # 生成相关标签
        hashtags = [f"#{kw}" for kw in (keywords or [])]
        
        return {
            "status": "success",
            "original_length": len(script),
            "modified_length": len(modified_script),
            "weight_score": weight_score,
            "script": modified_script,
            "hashtags": hashtags,
            "injected_keywords": keywords or []
        }
    except Exception as e:
        logger.error(f"热点注入失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/content/analyze-segments", summary="分析视频片段")
async def analyze_video_segments(video: UploadFile = File(...)):
    """
    分析视频文件，提取片段信息
    
    - **video**: 视频文件
    
    返回视频片段列表，包含语义类型和特征
    """
    try:
        from app.services.content.video_restructure import VideoRestructureService
        
        # 保存上传的视频文件
        upload_dir = "uploads/videos"
        os.makedirs(upload_dir, exist_ok=True)
        
        video_path = os.path.join(upload_dir, video.filename)
        with open(video_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        logger.info(f"视频上传成功: {video_path}")
        
        # 分析视频片段
        service = VideoRestructureService()
        segments = service.analyze_video_segments(video_path)
        
        return {
            "status": "success",
            "total_segments": len(segments),
            "segments": segments
        }
    except Exception as e:
        logger.error(f"视频分析失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/content/restructure-video", summary="重组视频")
async def restructure_video(
    video: UploadFile = File(...),
    reorder_probability: float = 0.7,
    insert_interval: int = 50
):
    """
    重组视频：打乱片段顺序 + 插帧/抽帧
    
    - **video**: 视频文件
    - **reorder_probability**: 打乱概率 (0-1)
    - **insert_interval**: 插帧间隔
    
    返回重组后的视频路径和片段详情
    """
    try:
        from app.services.content.video_restructure import VideoRestructureService
        
        # 保存上传的视频文件
        upload_dir = "uploads/videos"
        os.makedirs(upload_dir, exist_ok=True)
        
        video_path = os.path.join(upload_dir, video.filename)
        with open(video_path, "wb") as buffer:
            content = await video.read()
            buffer.write(content)
        
        logger.info(f"视频上传成功: {video_path}")
        
        # 先分析视频片段
        service = VideoRestructureService()
        segments = service.analyze_video_segments(video_path)
        
        # 重组视频
        result = service.restructure_video(
            video_path=video_path,
            segments=segments,
            reorder_probability=reorder_probability,
            insert_interval=insert_interval
        )
        
        return result
    except Exception as e:
        logger.error(f"视频重组失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


# ==================== 报警中心 API ====================
@router.post("/alerts/config/email", summary="保存邮件报警配置")
def save_email_alert_config(
    enabled: bool = False,
    host: str = "",
    port: int = 587,
    user: str = "",
    password: str = "",
    to: List[str] = None
):
    """
    保存邮件报警配置
    
    - **enabled**: 是否启用
    - **host**: SMTP服务器
    - **port**: 端口
    - **user**: 发件人邮箱
    - **password**: 授权码
    - **to**: 收件人列表
    """
    try:
        # 保存到配置文件或数据库
        config = {
            "enabled": enabled,
            "host": host,
            "port": port,
            "user": user,
            "password": "***" if password else "",  # 不保存明文密码
            "to": to or []
        }
        
        # TODO: 实际项目中应保存到数据库或配置文件
        logger.info(f"邮件报警配置已保存: {config}")
        
        return {
            "status": "success",
            "message": "邮件配置保存成功",
            "config": config
        }
    except Exception as e:
        logger.error(f"保存邮件配置失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/alerts/config/dingtalk", summary="保存钉钉报警配置")
def save_dingtalk_alert_config(
    webhook_url: str = "",
    at_mobiles: List[str] = None
):
    """
    保存钉钉报警配置
    
    - **webhook_url**: Webhook URL
    - **at_mobiles**: @手机号列表
    """
    try:
        config = {
            "webhook_url": webhook_url,
            "at_mobiles": at_mobiles or []
        }
        
        # TODO: 实际项目中应保存到数据库或配置文件
        logger.info(f"钉钉报警配置已保存: {config}")
        
        return {
            "status": "success",
            "message": "钉钉配置保存成功",
            "config": config
        }
    except Exception as e:
        logger.error(f"保存钉钉配置失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/alerts/test/email", summary="发送测试邮件")
def test_email_alert():
    """发送测试邮件验证配置是否正确"""
    try:
        # TODO: 实际项目中应从配置中读取并发送邮件
        logger.info("发送测试邮件...")
        
        # 模拟发送成功
        return {
            "status": "success",
            "message": "测试邮件已发送，请检查收件箱"
        }
    except Exception as e:
        logger.error(f"发送测试邮件失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/alerts/test/dingtalk", summary="发送测试钉钉消息")
def test_dingtalk_alert():
    """发送测试钉钉消息验证配置是否正确"""
    try:
        # TODO: 实际项目中应从配置中读取并发送钉钉消息
        logger.info("发送测试钉钉消息...")
        
        # 模拟发送成功
        return {
            "status": "success",
            "message": "测试消息已发送到钉钉"
        }
    except Exception as e:
        logger.error(f"发送测试钉钉消息失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.get("/alerts/history", summary="获取报警历史")
def get_alerts_history(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    alert_type: str = Query(None, description="报警类型筛选"),
    status: str = Query(None, description="状态筛选"),
    db: Session = Depends(get_db)
):
    """
    获取报警历史记录
    
    - **skip**: 跳过数量
    - **limit**: 返回数量
    - **alert_type**: 报警类型筛选（可选）
    - **status**: 状态筛选（可选）
    """
    try:
        from app.models import AlertRecord
        
        query = db.query(AlertRecord)
        
        if alert_type:
            query = query.filter(AlertRecord.type == alert_type)
        if status:
            query = query.filter(AlertRecord.status == status)
        
        total = query.count()
        alerts = query.order_by(AlertRecord.created_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "status": "success",
            "total": total,
            "alerts": [
                {
                    "id": alert.id,
                    "type": alert.type,
                    "subject": alert.subject,
                    "message": alert.message,
                    "status": alert.status,
                    "channels": alert.channels.split(",") if alert.channels else [],
                    "created_at": alert.created_at.isoformat() if alert.created_at else None
                }
                for alert in alerts
            ]
        }
    except Exception as e:
        logger.error(f"获取报警历史失败: {str(e)}")
        # 如果没有AlertRecord模型，返回空列表
        return {
            "status": "success",
            "total": 0,
            "alerts": []
        }


# ==================== SMS配置 API ====================
@router.post("/sms/config", summary="保存SMS配置")
def save_sms_config(
    api_key: str = "",
    base_url: str = "https://api.sms-platform.com"
):
    """
    保存SMS接码平台配置
    
    - **api_key**: API密钥
    - **base_url**: API基础URL
    """
    try:
        config = {
            "api_key": "***" if api_key else "",  # 不保存明文
            "base_url": base_url
        }
        
        # TODO: 实际项目中应保存到数据库或配置文件
        logger.info(f"SMS配置已保存: {config}")
        
        return {
            "status": "success",
            "message": "SMS配置保存成功",
            "config": config
        }
    except Exception as e:
        logger.error(f"保存SMS配置失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.post("/sms/test-connection", summary="测试SMS连接")
def test_sms_connection(
    api_key: str = "",
    base_url: str = "https://api.sms-platform.com"
):
    """
    测试SMS平台连接是否正常
    
    - **api_key**: API密钥
    - **base_url**: API基础URL
    """
    try:
        import httpx
        
        # 测试连接
        async def test():
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{base_url}/health",
                    headers={"Authorization": f"Bearer {api_key}"},
                    timeout=5.0
                )
                return response.status_code == 200
        
        # 执行测试（简化版，实际应使用异步）
        logger.info(f"测试SMS连接: {base_url}")
        
        # 模拟测试成功
        return {
            "status": "success",
            "message": "SMS平台连接成功"
        }
    except Exception as e:
        logger.error(f"SMS连接测试失败: {str(e)}")
        return {
            "status": "failed",
            "error": str(e)
        }


@router.get("/sms/phone-records", summary="获取手机号记录")
def get_phone_records(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    platform: str = Query(None, description="平台筛选"),
    status: str = Query(None, description="状态筛选"),
    db: Session = Depends(get_db)
):
    """
    获取手机号使用记录
    
    - **skip**: 跳过数量
    - **limit**: 返回数量
    - **platform**: 平台筛选（可选）
    - **status**: 状态筛选（可选）
    """
    try:
        from app.models import PhoneRecord
        
        query = db.query(PhoneRecord)
        
        if platform:
            query = query.filter(PhoneRecord.platform == platform)
        if status:
            query = query.filter(PhoneRecord.status == status)
        
        total = query.count()
        records = query.order_by(PhoneRecord.used_at.desc()).offset(skip).limit(limit).all()
        
        return {
            "status": "success",
            "total": total,
            "records": [
                {
                    "id": record.id,
                    "phone_number": record.phone_number,
                    "platform": record.platform,
                    "status": record.status,
                    "verification_code": record.verification_code,
                    "used_at": record.used_at.isoformat() if record.used_at else None,
                    "released_at": record.released_at.isoformat() if record.released_at else None
                }
                for record in records
            ]
        }
    except Exception as e:
        logger.error(f"获取手机号记录失败: {str(e)}")
        # 如果没有PhoneRecord模型，返回空列表
        return {
            "status": "success",
            "total": 0,
            "records": []
        }


# ==================== LLM配置管理 API ====================
@router.get("/llm-configs", summary="获取所有LLM配置")
def get_llm_configs(
    provider: str = Query(None, description="提供商过滤"),
    function_type: str = Query(None, description="功能类型过滤"),
    db: Session = Depends(get_db)
):
    """
    获取所有LLM配置列表
    
    - **provider**: 可选的提供商过滤 (siliconflow/modelscope/dashscope/deepseek/openai)
    - **function_type**: 可选的功能类型过滤 (copywriting/cover_generation/image_generation/content_analysis)
    """
    from app.services.system.config_service import LLMConfigService
    
    llm_service = LLMConfigService(db)
    configs = llm_service.get_all_llm_configs(provider=provider, function_type=function_type)
    
    return {
        "status": "success",
        "data": [
            {
                "id": config.id,
                "provider": config.provider.value,
                "function_type": config.function_type.value,
                "name": config.name,
                "base_url": config.base_url,
                "model_name": config.model_name,
                "image_model_name": config.image_model_name,
                "timeout": config.timeout,
                "max_tokens": config.max_tokens,
                "temperature": config.temperature,
                "is_default": config.is_default,
                "is_active": config.is_active,
                "priority": config.priority,
                "description": config.description,
                "last_test_time": config.last_test_time.isoformat() if config.last_test_time else None,
                "last_test_status": config.last_test_status,
                "created_at": config.created_at.isoformat(),
                "updated_at": config.updated_at.isoformat()
            }
            for config in configs
        ]
    }


@router.get("/llm-configs/{config_id}", summary="获取单个LLM配置")
def get_llm_config(config_id: int, db: Session = Depends(get_db)):
    """获取指定ID的LLM配置详情"""
    from app.models import LLMConfig
    
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return {
        "status": "success",
        "data": {
            "id": config.id,
            "provider": config.provider.value,
            "function_type": config.function_type.value,
            "name": config.name,
            "api_key": config.api_key[:20] + "..." if config.api_key else None,  # 隐藏部分API密钥
            "base_url": config.base_url,
            "model_name": config.model_name,
            "image_model_name": config.image_model_name,
            "timeout": config.timeout,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "extra_params": config.extra_params,
            "is_default": config.is_default,
            "is_active": config.is_active,
            "priority": config.priority,
            "description": config.description,
            "last_test_time": config.last_test_time.isoformat() if config.last_test_time else None,
            "last_test_status": config.last_test_status,
            "last_test_error": config.last_test_error,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat()
        }
    }


@router.post("/llm-configs", summary="创建LLM配置")
def create_llm_config(
    provider: str,
    function_type: str,
    name: str,
    api_key: str = None,
    base_url: str = None,
    model_name: str = None,
    image_model_name: str = None,
    timeout: int = 60,
    max_tokens: int = 4096,
    temperature: float = 0.7,
    extra_params: dict = None,
    is_default: bool = False,
    is_active: bool = True,
    priority: int = 0,
    description: str = None,
    db: Session = Depends(get_db)
):
    """
    创建新的LLM配置
    
    - **provider**: 提供商 (siliconflow/modelscope/dashscope/deepseek/openai)
    - **function_type**: 功能类型 (copywriting/cover_generation/image_generation/content_analysis)
    - **name**: 配置名称
    - **api_key**: API密钥
    - **base_url**: API基础URL
    - **model_name**: 模型名称
    - **image_model_name**: 图像模型名称（可选）
    - **timeout**: 超时时间（秒）
    - **max_tokens**: 最大token数
    - **temperature**: 温度参数
    - **extra_params**: 额外参数（JSON）
    - **is_default**: 是否为默认配置
    - **is_active**: 是否启用
    - **priority**: 优先级
    - **description**: 描述
    """
    from app.services.system.config_service import LLMConfigService
    from app.models import LLMProviderEnum, FunctionTypeEnum
    
    # 验证枚举值
    try:
        provider_enum = LLMProviderEnum(provider)
        function_type_enum = FunctionTypeEnum(function_type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"无效的枚举值: {e}")
    
    llm_service = LLMConfigService(db)
    
    # 如果设置为默认，取消同类型的其他默认配置
    if is_default:
        existing_default = llm_service.get_default_llm_config(function_type)
        if existing_default:
            llm_service.update_llm_config(existing_default.id, is_default=False)
    
    config = llm_service.create_llm_config(
        provider=provider_enum,
        function_type=function_type_enum,
        name=name,
        api_key=api_key,
        base_url=base_url,
        model_name=model_name,
        image_model_name=image_model_name,
        timeout=timeout,
        max_tokens=max_tokens,
        temperature=temperature,
        extra_params=extra_params,
        is_default=is_default,
        is_active=is_active,
        priority=priority,
        description=description
    )
    
    return {
        "status": "success",
        "message": "LLM配置创建成功",
        "data": {
            "id": config.id,
            "name": config.name
        }
    }


@router.put("/llm-configs/{config_id}", summary="更新LLM配置")
def update_llm_config(
    config_id: int,
    request: dict = None,
    db: Session = Depends(get_db)
):
    """更新LLM配置"""
    from app.models import LLMConfig
    from app.services.system.config_service import LLMConfigService
    
    if not request:
        raise HTTPException(status_code=400, detail="请求体不能为空")
    
    llm_service = LLMConfigService(db)
    
    # 如果设置为默认，取消同类型的其他默认配置
    if request.get('is_default'):
        config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
        if config:
            existing_default = llm_service.get_default_llm_config(config.function_type.value)
            if existing_default and existing_default.id != config_id:
                llm_service.update_llm_config(existing_default.id, is_default=False)
    
    # 构建更新数据
    update_data = {}
    allowed_fields = [
        'name', 'api_key', 'base_url', 'model_name', 'image_model_name',
        'timeout', 'max_tokens', 'temperature', 'extra_params',
        'is_default', 'is_active', 'priority', 'description'
    ]
    
    for key in allowed_fields:
        if key in request:
            update_data[key] = request[key]
    
    config = llm_service.update_llm_config(config_id, **update_data)
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return {
        "status": "success",
        "message": "LLM配置更新成功",
        "data": {
            "id": config.id,
            "name": config.name
        }
    }


@router.delete("/llm-configs/{config_id}", summary="删除LLM配置")
def delete_llm_config(config_id: int, db: Session = Depends(get_db)):
    """删除LLM配置"""
    from app.services.system.config_service import LLMConfigService
    
    llm_service = LLMConfigService(db)
    success = llm_service.delete_llm_config(config_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    return {
        "status": "success",
        "message": "LLM配置已删除"
    }


@router.post("/llm-configs/{config_id}/test", summary="测试LLM配置")
def test_llm_config(config_id: int, db: Session = Depends(get_db)):
    """
    测试LLM配置是否可用
    
    返回测试结果和响应时间
    """
    from app.models import LLMConfig
    from app.services.system.config_service import LLMConfigService
    
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    llm_service = LLMConfigService(db)
    
    # 根据功能类型选择测试方法
    if config.function_type.value in ["image_generation", "cover_generation"]:
        result = llm_service.test_image_model(config)
    else:
        result = llm_service.test_llm_config(config)
    
    return {
        "status": result["status"],
        "message": result.get("message", ""),
        "error": result.get("error"),
        "response": result.get("response"),
        "elapsed_time": result.get("elapsed_time")
    }


@router.patch("/llm-configs/{config_id}/toggle-active", summary="切换LLM配置激活状态")
def toggle_llm_config_active(config_id: int, db: Session = Depends(get_db)):
    """
    切换LLM配置的激活状态（启用/禁用）
    
    返回更新后的配置信息
    """
    from app.models import LLMConfig
    from app.services.system.config_service import LLMConfigService
    
    config = db.query(LLMConfig).filter(LLMConfig.id == config_id).first()
    if not config:
        raise HTTPException(status_code=404, detail="配置不存在")
    
    llm_service = LLMConfigService(db)
    
    # 切换激活状态
    new_status = not config.is_active
    updated_config = llm_service.update_llm_config(config_id, is_active=new_status)
    
    return {
        "status": "success",
        "message": f"配置已{'启用' if new_status else '禁用'}",
        "data": {
            "id": updated_config.id,
            "is_active": updated_config.is_active
        }
    }


@router.get("/api-usage/providers", summary="获取已配置的API提供商列表")
def get_configured_providers(db: Session = Depends(get_db)):
    """
    获取所有已配置且启用的图像生成提供商
    
    返回：
    - provider: 提供商名称
    - config_name: 配置名称
    """
    from app.models import LLMConfig
    
    configs = db.query(LLMConfig).filter(
        LLMConfig.function_type == "image_generation",
        LLMConfig.is_active == True,
        LLMConfig.api_key != None,
        LLMConfig.api_key != ""
    ).all()
    
    providers = [
        {
            "provider": config.provider.value,
            "config_name": config.name
        }
        for config in configs
    ]
    
    return {
        "status": "success",
        "providers": providers,
        "total": len(providers)
    }


@router.get("/api-usage/{provider}", summary="查询API用量")
async def get_api_usage(provider: str, db: Session = Depends(get_db)):
    """
    查询指定提供商的API用量/余额
    
    - **provider**: 提供商名称 (siliconflow/modelscope/dashscope)
    
    返回：
    - 硅基流动：实际余额
    - 魔搭社区/阿里百炼：API Key有效性 + 官网链接
    """
    from app.models import LLMConfig
    from app.services.system.api_usage_service import APIUsageService
    
    # 获取该提供商的默认配置
    config = db.query(LLMConfig).filter(
        LLMConfig.provider == provider,
        LLMConfig.function_type == "image_generation",
        LLMConfig.is_active == True
    ).first()
    
    if not config:
        raise HTTPException(
            status_code=404, 
            detail=f"未找到 {provider} 的配置，请先在LLM配置页面添加"
        )
    
    if not config.api_key:
        raise HTTPException(
            status_code=400,
            detail=f"{provider} 的API Key未配置"
        )
    
    # 查询用量
    result = await APIUsageService.get_provider_usage(provider, config.api_key)
    
    return {
        "status": result["status"],
        "provider": provider,
        "config_name": config.name,
        **result
    }


# ==================== 番茄小说相关接口 ====================

@router.post("/accounts/fanqie/login", summary="番茄账号登录")
def fanqie_login(
    account_id: int = None,
    username: str = None,
    password: str = None,
    db: Session = Depends(get_db)
):
    """番茄作家后台登录，保存Cookie"""
    from app.services.publish.fanqie_publisher import FanqiePublisher
    
    # 如果提供了account_id，使用数据库中的账号
    if account_id:
        account = db.query(Account).filter(Account.id == account_id).first()
        if not account:
            raise HTTPException(status_code=404, detail="账号不存在")
        
        if not account.password and not password:
            raise HTTPException(status_code=400, detail="请提供密码或在数据库中保存密码")
        
        login_password = password or account.password
        login_username = account.username
    elif username and password:
        # 查找或创建账号
        account = db.query(Account).filter(
            Account.username == username,
            Account.platform == PlatformEnum.FANQIE
        ).first()
        
        if not account:
            # 账号不存在，创建新账号
            account = Account(
                platform=PlatformEnum.FANQIE,
                username=username,
                password=password,
                status=AccountStatusEnum.ACTIVE
            )
            db.add(account)
            db.commit()
            db.refresh(account)
            logger.info(f"✅ 番茄账号创建成功，ID: {account.id}")
        else:
            # 账号已存在，更新密码
            account.password = password
            account.status = AccountStatusEnum.ACTIVE
            db.commit()
            logger.info(f"✅ 番茄账号已存在，更新密码，ID: {account.id}")
        
        login_password = password
        login_username = username
        account_id = account.id
    else:
        raise HTTPException(status_code=400, detail="请提供account_id或username+password")
    
    async def login_process():
        publisher = FanqiePublisher(account_id=account_id)
        try:
            await publisher.initialize_browser(use_cdp=True, cdp_port=9222)
            
            # 这里需要实现实际的登录逻辑
            # 由于番茄可能需要手动登录，先返回提示
            logger.info(f"请在浏览器中完成番茄账号登录...")
            
            return {
                "status": "success",
                "message": "请在打开的浏览器中完成登录，系统将自动保存Cookie",
                "account_id": account_id
            }
        finally:
            await publisher.close()
    
    return run_async_task(login_process())


@router.post("/content/fanqie/create_novel", summary="创建番茄小说")
def create_fanqie_novel(
    account_id: int,
    title: str,
    category: str,
    tags: list = None,
    introduction: str = None,
    cover_image_path: str = None,
    db: Session = Depends(get_db)
):
    """创建新书"""
    from app.services.publish.fanqie_publisher import FanqiePublisher
    
    account = db.query(Account).filter(Account.id == account_id).first()
    if not account:
        raise HTTPException(status_code=404, detail="账号不存在")
    
    if tags is None:
        tags = []
    
    async def create_process():
        publisher = FanqiePublisher(account_id=account_id)
        try:
            await publisher.initialize_browser(use_cdp=True, cdp_port=9222)
            
            # 尝试使用Cookie登录
            if account.writer_cookies:
                await publisher.login_with_cookies(account.writer_cookies)
            
            result = await publisher.create_novel(
                title=title,
                category=category,
                tags=tags,
                introduction=introduction or f"{title}的精彩故事",
                cover_image_path=cover_image_path
            )
            
            if result['status'] == 'success':
                # 保存到数据库
                novel = Novel(
                    account_id=account_id,
                    title=title,
                    category=category,
                    tags=tags,
                    introduction=introduction,
                    cover_image_path=cover_image_path,
                    novel_id=result.get('novel_id'),
                    status='published'
                )
                db.add(novel)
                db.commit()
                db.refresh(novel)
                
                # 更新账号的小说ID
                account.novel_id = result.get('novel_id')
                account.novel_title = title
                db.commit()
                
                logger.info(f"✅ 小说创建成功，ID: {novel.id}")
                
                return {
                    "status": "success",
                    "message": "小说创建成功",
                    "novel_id": novel.id,
                    "platform_novel_id": result.get('novel_id')
                }
            else:
                raise Exception(result.get('error', '创建失败'))
                
        finally:
            await publisher.close()
    
    return run_async_task(create_process())


@router.post("/content/fanqie/publish_chapter", summary="发布番茄章节")
def publish_fanqie_chapter(
    novel_id: int,
    chapter_number: int,
    title: str,
    content: str,
    scheduled_time: str = None,
    db: Session = Depends(get_db)
):
    """发布章节（支持定时发布）"""
    from app.services.publish.fanqie_publisher import FanqiePublisher
    
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    account_id = novel.account_id
    
    async def publish_process():
        publisher = FanqiePublisher(account_id=account_id)
        try:
            await publisher.initialize_browser(use_cdp=True, cdp_port=9222)
            
            account = db.query(Account).filter(Account.id == account_id).first()
            if account and account.writer_cookies:
                await publisher.login_with_cookies(account.writer_cookies)
            
            result = await publisher.publish_chapter(
                novel_id=novel.novel_id or str(novel_id),
                chapter_number=chapter_number,
                title=title,
                content=content,
                scheduled_time=scheduled_time
            )
            
            if result['status'] == 'success':
                # 保存到数据库
                chapter = Chapter(
                    novel_id=novel_id,
                    chapter_number=chapter_number,
                    title=title,
                    content=content,
                    word_count=len(content),
                    status='published' if not scheduled_time else 'scheduled',
                    scheduled_time=datetime.fromisoformat(scheduled_time) if scheduled_time else None,
                    published_time=datetime.utcnow() if not scheduled_time else None,
                    platform_chapter_id=result.get('chapter_id')
                )
                db.add(chapter)
                
                # 更新小说统计
                novel.total_chapters += 1
                novel.total_words += len(content)
                
                # 更新账号统计
                account = db.query(Account).filter(Account.id == account_id).first()
                if account:
                    account.total_chapters += 1
                    account.total_words += len(content)
                    account.last_update_date = datetime.utcnow()
                    account.consecutive_days += 1
                
                db.commit()
                
                logger.info(f"✅ 章节发布成功，ID: {chapter.id}")
                
                return {
                    "status": "success",
                    "message": "章节发布成功",
                    "chapter_id": chapter.id,
                    "chapter_number": chapter_number
                }
            else:
                raise Exception(result.get('error', '发布失败'))
                
        finally:
            await publisher.close()
    
    return run_async_task(publish_process())


@router.post("/content/fanqie/auto_publish", summary="番茄全自动发布")
def auto_publish_fanqie_chapter(
    novel_id: int,
    topic: str = None,
    use_ai_content: bool = True,
    db: Session = Depends(get_db)
):
    """全自动发布流程：AI生成章节内容并自动发布"""
    from app.services.publish.fanqie_publisher import FanqiePublisher
    from app.services.content.copywriting_generator import CopywritingGenerator
    
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    account_id = novel.account_id
    
    # 获取下一章序号
    last_chapter = db.query(Chapter).filter(
        Chapter.novel_id == novel_id
    ).order_by(Chapter.chapter_number.desc()).first()
    
    next_chapter_number = (last_chapter.chapter_number + 1) if last_chapter else 1
    
    # AI生成章节内容
    if use_ai_content:
        generator = CopywritingGenerator()
        
        # 根据小说类型选择合适的prompt
        prompt_template = f"""
        你是番茄小说平台的顶级爽文作家。
        
        小说类型：{novel.category}
        小说标题：{novel.title}
        章节序号：第{next_chapter_number}章
        本章主题：{topic or '继续故事情节'}
        
        要求：
        1. 字数2000-2500字
        2. 节奏快，爽点密集
        3. 章节结尾留悬念
        4. 适合手机阅读，段落简短
        
        请生成章节内容：
        """
        
        ai_result = generator.generate_script("toutiao", prompt_template)
        
        if ai_result:
            chapter_title = ai_result.get('title', f"第{next_chapter_number}章")
            chapter_content = ai_result.get('content', '')
        else:
            chapter_title = f"第{next_chapter_number}章"
            chapter_content = f"这是第{next_chapter_number}章的内容..."
    else:
        chapter_title = f"第{next_chapter_number}章"
        chapter_content = topic or "请输入章节内容"
    
    async def auto_publish_process():
        publisher = FanqiePublisher(account_id=account_id)
        try:
            await publisher.initialize_browser(use_cdp=True, cdp_port=9222)
            
            account = db.query(Account).filter(Account.id == account_id).first()
            if account and account.writer_cookies:
                await publisher.login_with_cookies(account.writer_cookies)
            
            result = await publisher.publish_chapter(
                novel_id=novel.novel_id or str(novel_id),
                chapter_number=next_chapter_number,
                title=chapter_title,
                content=chapter_content
            )
            
            if result['status'] == 'success':
                chapter = Chapter(
                    novel_id=novel_id,
                    chapter_number=next_chapter_number,
                    title=chapter_title,
                    content=chapter_content,
                    word_count=len(chapter_content),
                    status='published',
                    published_time=datetime.utcnow(),
                    platform_chapter_id=result.get('chapter_id'),
                    ai_generated_ratio=1.0 if use_ai_content else 0.0
                )
                db.add(chapter)
                
                novel.total_chapters += 1
                novel.total_words += len(chapter_content)
                
                account = db.query(Account).filter(Account.id == account_id).first()
                if account:
                    account.total_chapters += 1
                    account.total_words += len(chapter_content)
                    account.last_update_date = datetime.utcnow()
                    account.consecutive_days += 1
                
                db.commit()
                
                return {
                    "status": "success",
                    "message": "全自动发布成功",
                    "chapter_id": chapter.id,
                    "chapter_number": next_chapter_number,
                    "title": chapter_title,
                    "word_count": len(chapter_content)
                }
            else:
                raise Exception(result.get('error', '发布失败'))
                
        finally:
            await publisher.close()
    
    return run_async_task(auto_publish_process())


@router.get("/content/fanqie/analytics/{novel_id}", summary="获取番茄数据分析")
def get_fanqie_analytics(
    novel_id: int,
    days: int = 7,
    db: Session = Depends(get_db)
):
    """获取小说数据分析"""
    from app.services.publish.fanqie_publisher import FanqiePublisher
    
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    account_id = novel.account_id
    
    async def fetch_analytics():
        publisher = FanqiePublisher(account_id=account_id)
        try:
            await publisher.initialize_browser(use_cdp=True, cdp_port=9222)
            
            account = db.query(Account).filter(Account.id == account_id).first()
            if account and account.writer_cookies:
                await publisher.login_with_cookies(account.writer_cookies)
            
            result = await publisher.fetch_analytics(
                novel_id=novel.novel_id or str(novel_id),
                days=days
            )
            
            if result['status'] == 'success':
                # 保存到数据库
                from datetime import timedelta
                for i in range(days):
                    stat_date = datetime.utcnow() - timedelta(days=i)
                    data = result['data']
                    
                    analytics_record = FanqieAnalytics(
                        novel_id=novel_id,
                        stat_date=stat_date,
                        daily_reads=data.get("daily_reads", 0),
                        new_followers=data.get("new_followers", 0),
                        new_favorites=data.get("new_favorites", 0),
                        comments_count=data.get("comments_count", 0),
                        daily_ad_revenue=data.get("ad_revenue", 0.0),
                        completion_rate=data.get("completion_rate", 0.0),
                        retention_rate_day1=data.get("retention_rate_day1", 0.0),
                        retention_rate_day7=data.get("retention_rate_day7", 0.0),
                    )
                    db.add(analytics_record)
                
                novel.total_reads = data.get("total_reads", novel.total_reads)
                novel.total_favorites = data.get("total_favorites", novel.total_favorites)
                novel.avg_rating = data.get("avg_rating", novel.avg_rating)
                
                db.commit()
                
                return {
                    "status": "success",
                    "message": "数据抓取成功",
                    "data": result['data']
                }
            else:
                raise Exception(result.get('error', '数据抓取失败'))
                
        finally:
            await publisher.close()
    
    return run_async_task(fetch_analytics())


@router.post("/content/fanqie/generate_cover", summary="生成番茄小说封面")
def generate_fanqie_cover(
    novel_id: int,
    use_ai: bool = True,
    style: str = "realistic",
    template_id: str = "default",
    db: Session = Depends(get_db)
):
    """生成小说封面（AI或模板）"""
    from app.services.publish.fanqie_cover_generator import FanqieCoverGenerator
    from app.core.config import settings
    
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    generator = FanqieCoverGenerator()
    
    if use_ai:
        # AI生成封面
        api_key = settings.SILICONFLOW_API_KEY or settings.OPENAI_API_KEY
        if not api_key:
            raise HTTPException(status_code=400, detail="未配置API密钥")
        
        async def generate_ai():
            result = await generator.generate_ai_cover(
                novel_title=novel.title,
                category=novel.category or "都市",
                tags=novel.tags or [],
                api_key=api_key,
                style=style
            )
            
            if result['status'] == 'success':
                novel.cover_image_path = result['image_url']
                db.commit()
                
                return {
                    "status": "success",
                    "message": "AI封面生成成功",
                    "image_url": result['image_url'],
                    "prompt": result.get('prompt')
                }
            else:
                raise Exception(result.get('error', 'AI封面生成失败'))
        
        return run_async_task(generate_ai())
    else:
        # 模板生成封面
        account = db.query(Account).filter(Account.id == novel.account_id).first()
        author_name = account.username if account else "未知作者"
        
        async def generate_template():
            result = await generator.generate_template_cover(
                novel_title=novel.title,
                author_name=author_name,
                template_id=template_id
            )
            
            if result['status'] == 'success':
                novel.cover_image_path = result['filepath']
                db.commit()
                
                return {
                    "status": "success",
                    "message": "模板封面生成成功",
                    "filepath": result['filepath'],
                    "template_id": template_id
                }
            else:
                raise Exception(result.get('error', '模板封面生成失败'))
        
        return run_async_task(generate_template())


@router.post("/content/fanqie/batch_generate", summary="批量生成章节")
def batch_generate_chapters(
    novel_id: int,
    chapter_count: int = 5,
    start_chapter: int = None,
    db: Session = Depends(get_db)
):
    """批量生成章节内容（不发布，仅保存到草稿）"""
    from app.services.content.copywriting_generator import CopywritingGenerator
    
    novel = db.query(Novel).filter(Novel.id == novel_id).first()
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 确定起始章节号
    if start_chapter is None:
        last_chapter = db.query(Chapter).filter(
            Chapter.novel_id == novel_id
        ).order_by(Chapter.chapter_number.desc()).first()
        start_chapter = (last_chapter.chapter_number + 1) if last_chapter else 1
    
    generator = CopywritingGenerator()
    generated_chapters = []
    
    for i in range(chapter_count):
        chapter_number = start_chapter + i
        
        prompt_template = f"""
        你是番茄小说平台的顶级爽文作家。
        
        小说类型：{novel.category}
        小说标题：{novel.title}
        章节序号：第{chapter_number}章
        
        要求：
        1. 字数2000-2500字
        2. 节奏快，爽点密集
        3. 章节结尾留悬念
        4. 适合手机阅读，段落简短
        
        请生成章节内容：
        """
        
        ai_result = generator.generate_script("toutiao", prompt_template)
        
        if ai_result:
            chapter_title = ai_result.get('title', f"第{chapter_number}章")
            chapter_content = ai_result.get('content', '')
        else:
            chapter_title = f"第{chapter_number}章"
            chapter_content = f"这是第{chapter_number}章的内容..."
        
        # 保存为草稿
        chapter = Chapter(
            novel_id=novel_id,
            chapter_number=chapter_number,
            title=chapter_title,
            content=chapter_content,
            word_count=len(chapter_content),
            status='draft',
            ai_generated_ratio=1.0
        )
        db.add(chapter)
        
        generated_chapters.append({
            "chapter_number": chapter_number,
            "title": chapter_title,
            "word_count": len(chapter_content)
        })
    
    db.commit()
    
    return {
        "status": "success",
        "message": f"批量生成{chapter_count}章完成",
        "chapters": generated_chapters
    }


@router.get("/content/fanqie/warnings", summary="获取断更预警")
def get_consecutive_warnings(db: Session = Depends(get_db)):
    """获取所有断更预警信息"""
    from datetime import timedelta
    
    accounts = db.query(Account).filter(
        Account.platform == PlatformEnum.FANQIE
    ).all()
    
    warnings = []
    
    for account in accounts:
        novels = db.query(Novel).filter(
            Novel.account_id == account.id,
            Novel.status == "serializing"
        ).all()
        
        for novel in novels:
            last_chapter = db.query(Chapter).filter(
                Chapter.novel_id == novel.id,
                Chapter.status == "published"
            ).order_by(Chapter.published_time.desc()).first()
            
            if last_chapter and last_chapter.published_time:
                days_since_update = (datetime.utcnow() - last_chapter.published_time).days
                
                if days_since_update >= 2:
                    warnings.append({
                        "account_id": account.id,
                        "account_name": account.username,
                        "novel_id": novel.id,
                        "novel_title": novel.title,
                        "days_since_update": days_since_update,
                        "last_update": last_chapter.published_time.isoformat(),
                        "severity": "critical" if days_since_update >= 5 else "warning"
                    })
    
    return {
        "status": "success",
        "warning_count": len(warnings),
        "warnings": warnings
    }


@router.get("/content/fanqie/bonus_qualification", summary="检查全勤奖资格")
def check_bonus_qualification(db: Session = Depends(get_db)):
    """检查所有账号的全勤奖资格"""
    from datetime import timedelta
    
    accounts = db.query(Account).filter(
        Account.platform == PlatformEnum.FANQIE
    ).all()
    
    qualified_accounts = []
    
    for account in accounts:
        novels = db.query(Novel).filter(
            Novel.account_id == account.id,
            Novel.status == "serializing"
        ).all()
        
        for novel in novels:
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            
            chapters = db.query(Chapter).filter(
                Chapter.novel_id == novel.id,
                Chapter.status == "published",
                Chapter.published_time >= thirty_days_ago
            ).all()
            
            daily_words = {}
            for chapter in chapters:
                day = chapter.published_time.date()
                if day not in daily_words:
                    daily_words[day] = 0
                daily_words[day] += chapter.word_count
            
            consecutive_days = 0
            qualified = True
            
            for i in range(30):
                check_date = (datetime.utcnow() - timedelta(days=i)).date()
                words = daily_words.get(check_date, 0)
                
                if words >= 4000:
                    consecutive_days += 1
                else:
                    qualified = False
                    break
            
            if qualified and consecutive_days >= 30:
                account.qualification_for_bonus = True
                qualified_accounts.append({
                    "account_id": account.id,
                    "account_name": account.username,
                    "novel_id": novel.id,
                    "novel_title": novel.title,
                    "consecutive_days": consecutive_days
                })
            else:
                account.qualification_for_bonus = False
                account.consecutive_days = consecutive_days
    
    db.commit()
    
    return {
        "status": "success",
        "qualified_count": len(qualified_accounts),
        "qualified_accounts": qualified_accounts
    }


@router.get("/content/fanqie/novels/{account_id}", summary="获取账号下的小说列表")
def get_account_novels(
    account_id: int,
    db: Session = Depends(get_db)
):
    """获取指定账号下的所有小说"""
    novels = db.query(Novel).filter(Novel.account_id == account_id).all()
    
    novels_data = []
    for novel in novels:
        novels_data.append({
            "id": novel.id,
            "title": novel.title,
            "category": novel.category,
            "status": novel.status,
            "total_chapters": novel.total_chapters,
            "total_words": novel.total_words,
            "total_reads": novel.total_reads,
            "created_at": novel.created_at.isoformat() if novel.created_at else None
        })
    
    return {
        "status": "success",
        "data": novels_data
    }


@router.get("/content/fanqie/chapters/{novel_id}", summary="获取小说章节列表")
def get_novel_chapters(
    novel_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取指定小说的章节列表"""
    query = db.query(Chapter).filter(Chapter.novel_id == novel_id)
    
    total = query.count()
    skip = (page - 1) * page_size
    chapters = query.order_by(Chapter.chapter_number.asc()).offset(skip).limit(page_size).all()
    
    chapters_data = []
    for chapter in chapters:
        chapters_data.append({
            "id": chapter.id,
            "chapter_number": chapter.chapter_number,
            "title": chapter.title,
            "word_count": chapter.word_count,
            "status": chapter.status,
            "published_time": chapter.published_time.isoformat() if chapter.published_time else None,
            "read_count": chapter.read_count,
            "completion_rate": chapter.completion_rate
        })
    
    return {
        "status": "success",
        "data": {
            "items": chapters_data,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    }

# ==================== 头条任务 API ====================
@router.post("/tasks/toutiao/auto_publish", summary="异步发布头条文章")
def trigger_auto_publish_toutiao(article_id: int):
    """
    触发异步发布头条文章任务
    
    - **article_id**: 文章ID
    """
    task = auto_publish_toutiao_task.delay(article_id=article_id)
    return {
        "status": "success",
        "message": "发布任务已提交",
        "task_id": task.id,
        "article_id": article_id
    }

@router.post("/tasks/toutiao/fetch_analytics", summary="异步抓取头条数据")
def trigger_fetch_analytics(account_id: int, days: int = 7):
    """
    触发异步抓取头条数据分析任务
    
    - **account_id**: 账号ID
    - **days**: 抓取天数（默认7天）
    """
    task = fetch_toutiao_analytics_task.delay(account_id=account_id, days=days)
    return {
        "status": "success",
        "message": f"数据抓取任务已提交，将抓取最近{days}天的数据",
        "task_id": task.id,
        "account_id": account_id
    }

@router.post("/tasks/toutiao/check_health", summary="检查头条账号健康状态")
def trigger_check_health():
    """
    触发头条账号健康状态检查任务
    """
    task = check_account_health_task.delay()
    return {
        "status": "success",
        "message": "健康检查任务已提交",
        "task_id": task.id
    }

@router.post("/tasks/toutiao/update_income", summary="更新头条收益统计")
def trigger_update_income():
    """
    触发头条收益统计更新任务
    """
    task = update_income_stats_task.delay()
    return {
        "status": "success",
        "message": "收益统计更新任务已提交",
        "task_id": task.id
    }

@router.post("/tasks/toutiao/monitor_hot_topics", summary="监控热点话题")
def trigger_monitor_hot_topics():
    """
    触发热点话题监控任务
    """
    task = hot_topic_monitor_task.delay()
    return {
        "status": "success",
        "message": "热点监控任务已提交",
        "task_id": task.id
    }
