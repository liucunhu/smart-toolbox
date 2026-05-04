"""
密码加密工具类
使用 bcrypt 算法进行密码哈希和验证
"""
from passlib.context import CryptContext

# 配置密码加密上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    对密码进行哈希加密
    :param password: 明文密码
    :return: 哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码是否与哈希密码匹配
    :param plain_password: 明文密码
    :param hashed_password: 哈希后的密码
    :return: 是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)
