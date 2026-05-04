"""
批量账号注册API
支持多平台批量注册
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models import Account, PlatformEnum
from app.services.account.sms_gateway import SMSGateway
from app.services.account.captcha_solver import CaptchaSolver
from app.utils.logger import logger
from typing import List, Dict
import uuid

router = APIRouter()


@router.post("/batch/register", summary="批量注册账号")
async def batch_register_accounts(
    platform: str,
    count: int = 1,
    sms_platform: str = "sms_activate",
    sms_api_key: str = "",
    captcha_api_key: str = "",
    db: Session = Depends(get_db)
):
    """
    批量注册账号
    
    - **platform**: 平台类型（douyin/kuaishou/wechat/bilibili/xiaohongshu）
    - **count**: 注册数量
    - **sms_platform**: SMS接码平台
    - **sms_api_key**: SMS API密钥
    - **captcha_api_key**: 验证码识别API密钥
    
    返回任务ID列表
    """
    try:
        # 初始化服务
        sms_gateway = SMSGateway(platform=sms_platform, api_key=sms_api_key)
        captcha_solver = CaptchaSolver(api_key=captcha_api_key)
        
        task_ids = []
        
        for i in range(count):
            # 1. 获取手机号
            phone_result = await sms_gateway.get_phone_number(service=platform)
            
            if phone_result["status"] != "success":
                logger.error(f"第{i+1}个账号获取号码失败: {phone_result['error']}")
                continue
            
            phone_number = phone_result["phone_number"]
            access_id = phone_result["access_id"]
            
            # 2. 创建账号记录
            new_account = Account(
                platform=getattr(PlatformEnum, platform.upper(), PlatformEnum.DOUYIN),
                username=f"temp_{uuid.uuid4().hex[:8]}",
                phone=phone_number
            )
            db.add(new_account)
            db.commit()
            db.refresh(new_account)
            
            # 3. 等待验证码
            code_result = await sms_gateway.get_sms_code(access_id)
            
            if code_result["status"] == "success":
                verification_code = code_result["code"]
                
                # 4. 触发注册任务（这里简化处理，实际需要调用RPA引擎）
                task_id = f"register_{new_account.id}_{uuid.uuid4().hex[:8]}"
                task_ids.append({
                    "account_id": new_account.id,
                    "task_id": task_id,
                    "phone": phone_number,
                    "status": "pending"
                })
                
                # 标记订单完成
                await sms_gateway.set_status(access_id, 6)
                
                logger.info(f"账号 {new_account.id} 注册任务已创建")
            else:
                logger.error(f"第{i+1}个账号获取验证码失败")
                # 取消订单
                await sms_gateway.set_status(access_id, 3)
        
        return {
            "message": f"批量注册任务已创建",
            "total": count,
            "success": len(task_ids),
            "tasks": task_ids
        }
    
    except Exception as e:
        logger.error(f"批量注册失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/batch/status/{task_id}", summary="查询批量注册状态")
def get_batch_register_status(task_id: str, db: Session = Depends(get_db)):
    """查询批量注册任务状态"""
    # TODO: 实现任务状态查询
    return {
        "task_id": task_id,
        "status": "completed",
        "message": "任务已完成"
    }


@router.get("/accounts/batch/list", summary="批量账号列表")
def get_batch_accounts(
    platform: str = None,
    status: str = None,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取批量注册的账号列表"""
    query = db.query(Account)
    
    if platform:
        query = query.filter(Account.platform == getattr(PlatformEnum, platform.upper()))
    
    if status:
        query = query.filter(Account.status == status)
    
    accounts = query.order_by(Account.created_at.desc()).limit(limit).all()
    
    return {
        "total": len(accounts),
        "accounts": [
            {
                "id": acc.id,
                "username": acc.username,
                "platform": acc.platform.value,
                "status": acc.status.value if acc.status else None,
                "created_at": acc.created_at.isoformat() if acc.created_at else None
            }
            for acc in accounts
        ]
    }
