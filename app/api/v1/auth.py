"""
认证路由
提供用户登录、注册等认证相关接口
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.core.security import create_access_token, authenticate_user
from app.utils.security import hash_password
from app.models.user import User
from app.db.session import get_db
from app.utils.logger import logger
from typing import Optional

router = APIRouter(prefix="/auth", tags=["认证"])


class LoginRequest(BaseModel):
    """登录请求模型"""
    username: str
    password: str


class LoginResponse(BaseModel):
    """登录响应模型"""
    access_token: str
    token_type: str = "bearer"
    user_id: int


class RegisterRequest(BaseModel):
    """注册请求模型"""
    username: str
    password: str
    email: Optional[str] = None


@router.post("/login", response_model=LoginResponse)
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """
    用户登录
    
    - **username**: 用户名
    - **password**: 密码
    
    返回JWT access token
    """
    # 从数据库查询用户
    user = db.query(User).filter(User.username == form_data.username).first()
    
    if not user or not authenticate_user(form_data.username, form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户账号已被禁用"
        )
    
    # 创建access token
    access_token = create_access_token(data={"sub": user.id})
    
    logger.info(f"用户 {user.username} (ID: {user.id}) 登录成功")
    
    return LoginResponse(
        access_token=access_token,
        user_id=user.id
    )


@router.post("/register")
def register(register_data: RegisterRequest, db: Session = Depends(get_db)):
    """
    用户注册
    
    - **username**: 用户名
    - **password**: 密码
    - **email**: 邮箱（可选）
    """
    # 1. 检查用户名是否已存在
    existing_user = db.query(User).filter(User.username == register_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用户名已存在"
        )
    
    # 2. 检查邮箱是否已存在（如果提供了邮箱）
    if register_data.email:
        existing_email = db.query(User).filter(User.email == register_data.email).first()
        if existing_email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="邮箱已被注册"
            )
    
    # 3. 哈希密码并创建用户
    hashed_pw = hash_password(register_data.password)
    new_user = User(
        username=register_data.username,
        email=register_data.email,
        hashed_password=hashed_pw
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    logger.info(f"用户 {new_user.username} (ID: {new_user.id}) 注册成功")
    
    return {
        "message": "注册成功",
        "user_id": new_user.id,
        "username": new_user.username
    }


@router.post("/logout")
def logout():
    """
    用户登出
    
    前端应删除本地存储的token
    """
    return {"message": "登出成功"}
