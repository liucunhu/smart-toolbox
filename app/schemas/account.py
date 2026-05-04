from pydantic import BaseModel, Field
from app.models import PlatformEnum, AccountStatusEnum
from typing import Optional
from datetime import datetime

class AccountCreate(BaseModel):
    platform: PlatformEnum
    proxy_ip: Optional[str] = None
    phone_number: str  # 手机号
    verification_code: Optional[str] = None  # 验证码（可选，若为自动接码则可不传）

class AccountResponse(BaseModel):
    id: int
    platform: PlatformEnum
    username: Optional[str] = None
    status: AccountStatusEnum
    health_score: float = 100.0
    proxy_ip: Optional[str] = None
    cookies: Optional[str] = None  # 登录后的 Cookie（用于自动化发布）
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class AccountLoginRequest(BaseModel):
    """账号登录请求"""
    account_id: int = Field(..., description="账号 ID")
    username: str = Field(..., description="账号/手机号/邮箱")
    password: str = Field(..., description="密码")

class AccountListResponse(BaseModel):
    """账号列表响应"""
    total: int
    accounts: list[AccountResponse]
