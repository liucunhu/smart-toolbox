"""
SMS接码平台服务
支持多平台自动获取验证码，替代硬编码
"""
import httpx
import asyncio
from typing import Optional, Dict
from app.core.config import settings
from app.utils.logger import logger

class SMSVerificationService:
    """SMS接码平台服务 - 支持多平台自动获取验证码"""
    
    def __init__(self):
        self.api_key = settings.SMS_PLATFORM_API_KEY
        self.base_url = settings.SMS_PLATFORM_BASE_URL
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
    
    async def get_phone_number(self, platform: str) -> Dict:
        """从接码平台获取手机号"""
        try:
            response = await self.client.post("/api/get_number", json={
                "platform": platform,
                "country": "CN"
            })
            response.raise_for_status()
            result = response.json()
            
            logger.info(f"成功获取手机号: {result.get('phone_number')}")
            return result
            
        except Exception as e:
            logger.error(f"获取手机号失败: {str(e)}")
            raise
    
    async def get_verification_code(self, phone_number: str, platform: str, timeout: int = 60) -> str:
        """
        从接码平台获取验证码
        :param phone_number: 手机号
        :param platform: 平台名称
        :param timeout: 超时时间（秒）
        :return: 验证码
        """
        try:
            logger.info(f"开始获取验证码，手机号: {phone_number}, 平台: {platform}")
            
            # 请求发送验证码
            await self.client.post("/api/request_code", json={
                "phone_number": phone_number,
                "platform": platform
            })
            
            # 轮询获取验证码
            for attempt in range(timeout // 5):
                await asyncio.sleep(5)
                
                response = await self.client.get("/api/get_code", params={
                    "phone_number": phone_number
                })
                response.raise_for_status()
                result = response.json()
                
                if result.get("code"):
                    verification_code = result["code"]
                    logger.info(f"成功获取验证码: {verification_code}")
                    return verification_code
                
                logger.debug(f"等待验证码... 尝试 {attempt + 1}/{timeout // 5}")
            
            raise TimeoutError(f"获取验证码超时 ({timeout}秒)")
            
        except Exception as e:
            logger.error(f"获取验证码失败: {str(e)}")
            raise
    
    async def release_phone_number(self, phone_number: str, status: str = "success"):
        """释放手机号"""
        try:
            await self.client.post("/api/release_number", json={
                "phone_number": phone_number,
                "status": status
            })
            logger.info(f"手机号已释放: {phone_number}")
        except Exception as e:
            logger.error(f"释放手机号失败: {str(e)}")
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
