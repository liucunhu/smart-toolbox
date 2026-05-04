"""
内容去重检测服务
遵循 OCP (Open/Closed Principle)，支持扩展不同的去重算法
"""
import hashlib
from pathlib import Path
from app.utils.logger import logger
from typing import Optional

class ContentDeduplicationService:
    """内容唯一性校验服务"""

    @staticmethod
    def calculate_md5(file_path: str) -> str:
        """计算文件的 MD5 值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    @staticmethod
    def is_duplicate(file_path: str, existing_hashes: list) -> bool:
        """
        检查文件是否已存在
        :param file_path: 待检查文件路径
        :param existing_hashes: 数据库中已存在的哈希列表
        :return: 是否重复
        """
        current_hash = ContentDeduplicationService.calculate_md5(file_path)
        if current_hash in existing_hashes:
            logger.warning(f"检测到重复文件: {file_path}")
            return True
        return False

    @staticmethod
    def generate_unique_filename(original_path: str, account_id: int) -> str:
        """
        为不同账号生成唯一的文件名，避免平台内部查重
        :param original_path: 原始路径
        :param account_id: 账号ID
        :return: 新的文件路径
        """
        path = Path(original_path)
        unique_suffix = f"_acc{account_id}_{hashlib.md5(str(account_id).encode()).hexdigest()[:6]}"
        new_name = f"{path.stem}{unique_suffix}{path.suffix}"
        return str(path.parent / new_name)
