"""
JWT 认证模块
提供 Token 生成、验证和用户认证功能
"""
from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from app.core.config import settings
from app.utils.logger import logger

# OAuth2 password bearer scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建 JWT Access Token
    
    :param data: 要编码的数据（通常包含用户ID）
    :param expires_delta: 过期时间增量
    :return: JWT token字符串
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def verify_token(token: str) -> dict:
    """
    验证 JWT Token
    
    :param token: JWT token字符串
    :return: 解码后的payload
    :raises HTTPException: Token无效或过期
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token验证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的认证凭证",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(token: str = Depends(oauth2_scheme)) -> dict:
    """
    获取当前认证用户（FastAPI依赖注入）
    
    :param token: 从请求头提取的token
    :return: 用户信息字典
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(token)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        
        return {"user_id": user_id}
    except JWTError:
        raise credentials_exception


def authenticate_user(username: str, password: str, hashed_password: str) -> bool:
    """
    验证用户凭据
    
    :param username: 用户名
    :param password: 明文密码
    :param hashed_password: 哈希后的密码
    :return: 是否认证成功
    """
    from app.utils.security import verify_password
    return verify_password(password, hashed_password)
