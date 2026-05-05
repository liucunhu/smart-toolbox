"""
账号相关的Pydantic模型
用于API请求参数验证
"""
from pydantic import BaseModel, Field, validator
from app.models import PlatformEnum, AccountStatusEnum
from typing import Optional
from datetime import datetime
import re


# ==================== 原有模型（保持向后兼容）====================

class AccountCreate(BaseModel):
    """创建账号请求（旧版）"""
    platform: PlatformEnum
    proxy_ip: Optional[str] = None
    phone_number: str  # 手机号
    verification_code: Optional[str] = None  # 验证码（可选，若为自动接码则可不传）


class AccountResponse(BaseModel):
    """账号响应模型"""
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


class AccountListResponse(BaseModel):
    """账号列表响应"""
    total: int
    accounts: list[AccountResponse]


# ==================== 新增验证模型 ====================


class AccountCreateRequest(BaseModel):
    """创建账号请求模型"""
    platform: str = Field(..., min_length=1, max_length=50, description="平台名称")
    username: str = Field(..., min_length=3, max_length=100, description="用户名")
    password: Optional[str] = Field(None, min_length=6, max_length=255, description="密码")
    proxy_ip: Optional[str] = Field(None, description="代理IP")
    
    @validator('proxy_ip')
    def validate_proxy_ip(cls, v):
        """验证代理IP格式"""
        if v is None:
            return v
        
        # IP地址格式: xxx.xxx.xxx.xxx 或 xxx.xxx.xxx.xxx:port
        pattern = r'^(\d{1,3}\.){3}\d{1,3}(:\d+)?$'
        if not re.match(pattern, v):
            raise ValueError('Invalid proxy IP format. Expected: x.x.x.x or x.x.x.x:port')
        
        # 验证IP范围
        ip_part = v.split(':')[0]
        octets = ip_part.split('.')
        for octet in octets:
            if not (0 <= int(octet) <= 255):
                raise ValueError('IP octets must be between 0 and 255')
        
        return v


class AccountUpdateRequest(BaseModel):
    """更新账号请求模型"""
    username: Optional[str] = Field(None, min_length=3, max_length=100, description="用户名")
    password: Optional[str] = Field(None, min_length=6, max_length=255, description="密码")
    proxy_ip: Optional[str] = Field(None, description="代理IP")
    
    @validator('proxy_ip')
    def validate_proxy_ip(cls, v):
        """验证代理IP格式"""
        if v is None:
            return v
        
        pattern = r'^(\d{1,3}\.){3}\d{1,3}(:\d+)?$'
        if not re.match(pattern, v):
            raise ValueError('Invalid proxy IP format. Expected: x.x.x.x or x.x.x.x:port')
        
        ip_part = v.split(':')[0]
        octets = ip_part.split('.')
        for octet in octets:
            if not (0 <= int(octet) <= 255):
                raise ValueError('IP octets must be between 0 and 255')
        
        return v


class AccountLoginRequest(BaseModel):
    """账号登录请求模型"""
    account_id: int = Field(..., gt=0, description="账号ID")
    username: str = Field(..., min_length=1, max_length=100, description="登录用户名/手机号")
    password: str = Field(..., min_length=1, max_length=255, description="登录密码")


class ContentPublishRequest(BaseModel):
    """内容发布请求模型"""
    account_id: int = Field(..., gt=0, description="账号ID")
    title: str = Field(..., min_length=1, max_length=500, description="标题")
    content: str = Field(..., min_length=1, description="内容")
    category: Optional[str] = Field(None, max_length=100, description="分类")
    tags: Optional[list] = Field(None, description="标签列表")


class ComplianceCheckRequest(BaseModel):
    """合规检查请求模型"""
    text: str = Field(..., min_length=1, max_length=50000, description="待检查文本")
    platform: str = Field(..., min_length=1, max_length=50, description="目标平台")


class BatchRegisterRequest(BaseModel):
    """批量注册请求模型"""
    platform: str = Field(..., min_length=1, max_length=50, description="平台名称")
    count: int = Field(..., ge=1, le=10, description="注册数量（1-10）")
    sms_platform: str = Field(..., min_length=1, max_length=50, description="短信平台")
    sms_api_key: str = Field(..., min_length=1, description="短信API密钥")
    captcha_api_key: Optional[str] = Field(None, description="验证码API密钥")
