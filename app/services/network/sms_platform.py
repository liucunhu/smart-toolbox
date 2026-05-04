"""
SMS接码平台API对接服务
支持SMS Activate、5SIM、SMSHub等平台
"""
import logging
import random
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class SMSPlatform(Enum):
    """SMS平台"""
    SMS_ACTIVATE = "sms_activate"
    FIVE_SIM = "5sim"
    SMS_HUB = "smshub"


@dataclass
class PhoneNumber:
    """手机号信息"""
    phone_number: str
    platform: SMSPlatform
    country_code: str
    service_id: str
    activation_id: str
    status: str = "pending"  # pending/sent/received/used/expired
    verification_code: Optional[str] = None
    received_at: Optional[str] = None
    expires_at: Optional[str] = None


class SMSActivateClient:
    """SMS Activate API客户端"""
    
    BASE_URL = "https://sms-activate.org/stubs/handler_api.php"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_balance(self) -> Dict[str, Any]:
        """获取余额"""
        params = {
            "api_key": self.api_key,
            "action": "getBalance"
        }
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            data = response.json()
            
            if "ACCESS_BALANCE" in data:
                return {
                    "success": True,
                    "balance": data["ACCESS_BALANCE"],
                    "currency": "RUB"
                }
            else:
                return {
                    "success": False,
                    "error": data.get("ACTION_ERROR", "未知错误")
                }
                
        except Exception as e:
            logger.error(f"获取余额失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_phone_number(
        self,
        service_id: str = "ot_0",  # 其他服务（通用）
        country: str = "0",  # 0 = 俄罗斯, 6 = 中国
        operator: str = "any"  # 运营商
    ) -> Dict[str, Any]:
        """
        获取手机号
        
        Args:
            service_id: 服务ID（ot_0 = 通用）
            country: 国家代码
            operator: 运营商
            
        Returns:
            Dict: 结果
        """
        params = {
            "api_key": self.api_key,
            "action": "getNumber",
            "service": service_id,
            "country": country,
            "operator": operator
        }
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            data = response.text  # SMS-Activate 返回文本格式
            
            if ":" in data:
                # 格式: ACTIVATION_ID:PHONE_NUMBER
                activation_id, phone_number = data.split(":")
                
                return {
                    "success": True,
                    "activation_id": activation_id,
                    "phone_number": phone_number,
                    "country": country,
                    "service_id": service_id
                }
            else:
                return {
                    "success": False,
                    "error": data  # 错误信息直接在返回值中
                }
                
        except Exception as e:
            logger.error(f"获取手机号失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_sms_code(
        self,
        activation_id: str
    ) -> Dict[str, Any]:
        """
        获取验证码
        
        Args:
            activation_id: 激活ID
            
        Returns:
            Dict: 结果
        """
        params = {
            "api_key": self.api_key,
            "action": "getStatus",
            "id": activation_id
        }
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            data = response.text
            
            # SMS-Activate 状态码
            # STATUS_OK:8 = 等待验证码
            # STATUS_OK:CODE:1234 = 收到验证码
            
            if "STATUS_OK:CODE:" in data:
                # 提取验证码
                code = data.split(":")[-1]
                return {
                    "success": True,
                    "code": code,
                    "status": "received"
                }
            elif "STATUS_OK" in data:
                return {
                    "success": False,
                    "status": "waiting",
                    "message": "等待验证码"
                }
            elif "STATUS_CANCEL" in data:
                return {
                    "success": False,
                    "status": "cancelled",
                    "message": "激活已取消"
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "message": data
                }
                
        except Exception as e:
            logger.error(f"获取验证码失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cancel_activation(self, activation_id: str) -> Dict[str, Any]:
        """取消激活"""
        params = {
            "api_key": self.api_key,
            "action": "setStatus",
            "id": activation_id,
            "status": "8"  # 取消激活
        }
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            data = response.text
            
            if "ACCESS_CANCEL" in data:
                return {
                    "success": True,
                    "message": "激活已取消"
                }
            else:
                return {
                    "success": False,
                    "error": data
                }
                
        except Exception as e:
            logger.error(f"取消激活失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


class FiveSimClient:
    """5SIM API客户端"""
    
    BASE_URL = "https://5sim.net/v1"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_balance(self) -> Dict[str, Any]:
        """获取余额"""
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/user/profile",
                headers=self.headers
            )
            data = response.json()
            
            if "balance" in data:
                return {
                    "success": True,
                    "balance": data["balance"],
                    "currency": data.get("currency", "RUB")
                }
            else:
                return {
                    "success": False,
                    "error": data.get("error", "未知错误")
                }
                
        except Exception as e:
            logger.error(f"获取余额失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_phone_number(
        self,
        product: str = "other",  # 产品
        country: str = "cn",  # 国家
        operator: str = "any"  # 运营商
    ) -> Dict[str, Any]:
        """
        获取手机号
        
        Args:
            product: 产品类型
            country: 国家代码
            operator: 运营商
            
        Returns:
            Dict: 结果
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/user/buy/activation/{country}/{operator}/{product}",
                headers=self.headers
            )
            data = response.json()
            
            if "id" in data and "phone" in data:
                return {
                    "success": True,
                    "activation_id": str(data["id"]),
                    "phone_number": data["phone"],
                    "country": country,
                    "product": product
                }
            else:
                return {
                    "success": False,
                    "error": data.get("error", "未知错误")
                }
                
        except Exception as e:
            logger.error(f"获取手机号失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_sms_code(
        self,
        activation_id: str
    ) -> Dict[str, Any]:
        """
        获取验证码
        
        Args:
            activation_id: 激活ID
            
        Returns:
            Dict: 结果
        """
        try:
            response = await self.client.get(
                f"{self.BASE_URL}/user/check/{activation_id}",
                headers=self.headers
            )
            data = response.json()
            
            if "sms" in data and data["sms"]:
                return {
                    "success": True,
                    "code": data["sms"],
                    "status": "received"
                }
            elif "status" in data:
                status = data["status"]
                if status == "PENDING":
                    return {
                        "success": False,
                        "status": "waiting",
                        "message": "等待验证码"
                    }
                elif status == "CANCELED":
                    return {
                        "success": False,
                        "status": "cancelled",
                        "message": "激活已取消"
                    }
                else:
                    return {
                        "success": False,
                        "status": status.lower(),
                        "message": data
                    }
            else:
                return {
                    "success": False,
                    "error": "未知错误"
                }
                
        except Exception as e:
            logger.error(f"获取验证码失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cancel_activation(self, activation_id: str) -> Dict[str, Any]:
        """取消激活"""
        try:
            response = await self.client.post(
                f"{self.BASE_URL}/user/cancel/{activation_id}",
                headers=self.headers
            )
            data = response.json()
            
            return {
                "success": True,
                "message": "取消请求已发送"
            }
                
        except Exception as e:
            logger.error(f"取消激活失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


class SMSHubClient:
    """SMSHub API客户端"""
    
    BASE_URL = "http://smshub.org/stubs/handler_api.php"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def get_balance(self) -> Dict[str, Any]:
        """获取余额"""
        params = {
            "api_key": self.api_key,
            "action": "getBalance"
        }
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            data = response.json()
            
            if "ACCESS_BALANCE" in data:
                return {
                    "success": True,
                    "balance": data["ACCESS_BALANCE"],
                    "currency": "RUB"
                }
            else:
                return {
                    "success": False,
                    "error": data.get("ACTION_ERROR", "未知错误")
                }
                
        except Exception as e:
            logger.error(f"获取余额失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_phone_number(
        self,
        service_id: str = "ot",
        country: str = "0"
    ) -> Dict[str, Any]:
        """获取手机号"""
        params = {
            "api_key": self.api_key,
            "action": "getNumber",
            "service": service_id,
            "country": country,
            "operator": "any"
        }
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            data = response.text
            
            if ":" in data:
                activation_id, phone_number = data.split(":")
                
                return {
                    "success": True,
                    "activation_id": activation_id,
                    "phone_number": phone_number,
                    "country": country,
                    "service_id": service_id
                }
            else:
                return {
                    "success": False,
                    "error": data
                }
                
        except Exception as e:
            logger.error(f"获取手机号失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def get_sms_code(
        self,
        activation_id: str
    ) -> Dict[str, Any]:
        """获取验证码"""
        params = {
            "api_key": self.api_key,
            "action": "getStatus",
            "id": activation_id
        }
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            data = response.text
            
            if "STATUS_OK:CODE:" in data:
                code = data.split(":")[-1]
                return {
                    "success": True,
                    "code": code,
                    "status": "received"
                }
            elif "STATUS_OK" in data:
                return {
                    "success": False,
                    "status": "waiting",
                    "message": "等待验证码"
                }
            else:
                return {
                    "success": False,
                    "status": "error",
                    "message": data
                }
                
        except Exception as e:
            logger.error(f"获取验证码失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def cancel_activation(self, activation_id: str) -> Dict[str, Any]:
        """取消激活"""
        params = {
            "api_key": self.api_key,
            "action": "setStatus",
            "id": activation_id,
            "status": "8"
        }
        
        try:
            response = await self.client.get(self.BASE_URL, params=params)
            data = response.text
            
            if "ACCESS_CANCEL" in data:
                return {
                    "success": True,
                    "message": "激活已取消"
                }
            else:
                return {
                    "success": False,
                    "error": data
                }
                
        except Exception as e:
            logger.error(f"取消激活失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


class SMSPlatformManager:
    """SMS平台管理器"""
    
    def __init__(self):
        self.clients = {}
    
    def get_client(
        self,
        platform: SMSPlatform,
        api_key: str
    ):
        """
        获取平台客户端
        
        Args:
            platform: 平台类型
            api_key: API密钥
            
        Returns:
            平台客户端实例
        """
        cache_key = f"{platform.value}_{api_key}"
        
        if cache_key not in self.clients:
            if platform == SMSPlatform.SMS_ACTIVATE:
                self.clients[cache_key] = SMSActivateClient(api_key)
            elif platform == SMSPlatform.FIVE_SIM:
                self.clients[cache_key] = FiveSimClient(api_key)
            elif platform == SMSPlatform.SMS_HUB:
                self.clients[cache_key] = SMSHubClient(api_key)
            else:
                raise ValueError(f"不支持的平台: {platform}")
        
        return self.clients[cache_key]
    
    async def register_account(
        self,
        platform: SMSPlatform,
        api_key: str,
        target_platform: str = "douyin"
    ) -> Dict[str, Any]:
        """
        注册账号（获取手机号）
        
        Args:
            platform: SMS平台
            api_key: API密钥
            target_platform: 目标平台（用于选择服务ID）
            
        Returns:
            Dict: 注册结果
        """
        try:
            # 获取客户端
            client = self.get_client(platform, api_key)
            
            # 映射目标平台到服务ID
            service_mapping = {
                "douyin": "ot",  # 通用服务
                "kuaishou": "ot",
                "xiaohongshu": "ot",
                "toutiao": "ot",
                "bilibili": "ot",
                "wechat": "ot"
            }
            
            service_id = service_mapping.get(target_platform, "ot")
            
            # 获取手机号
            result = await client.get_phone_number(service_id=service_id)
            
            if result["success"]:
                logger.info(f"✅ 成功获取手机号: {result['phone_number']}")
            else:
                logger.error(f"获取手机号失败: {result['error']}")
            
            return result
            
        except Exception as e:
            logger.error(f"注册账号失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def poll_verification_code(
        self,
        platform: SMSPlatform,
        api_key: str,
        activation_id: str,
        max_attempts: int = 30,
        interval: int = 5
    ) -> Dict[str, Any]:
        """
        轮询获取验证码
        
        Args:
            platform: SMS平台
            api_key: API密钥
            activation_id: 激活ID
            max_attempts: 最大尝试次数
            interval: 轮询间隔（秒）
            
        Returns:
            Dict: 结果
        """
        try:
            client = self.get_client(platform, api_key)
            
            for attempt in range(max_attempts):
                logger.info(f"尝试获取验证码 ({attempt+1}/{max_attempts})...")
                
                result = await client.get_sms_code(activation_id)
                
                if result["success"]:
                    logger.info(f"✅ 成功获取验证码: {result['code']}")
                    return result
                elif result["status"] == "cancelled":
                    logger.warning("激活已取消")
                    return result
                elif result["status"] == "error":
                    logger.error(f"获取验证码失败: {result.get('message', '未知错误')}")
                    return result
                
                # 等待后重试
                if attempt < max_attempts - 1:
                    await asyncio.sleep(interval)
            
            return {
                "success": False,
                "error": f"在 {max_attempts * interval} 秒内未收到验证码"
            }
            
        except Exception as e:
            logger.error(f"轮询验证码失败: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def test_connection(
        self,
        platform: SMSPlatform,
        api_key: str
    ) -> Dict[str, Any]:
        """
        测试平台连接
        
        Args:
            platform: SMS平台
            api_key: API密钥
            
        Returns:
            Dict: 测试结果
        """
        try:
            client = self.get_client(platform, api_key)
            balance_result = await client.get_balance()
            
            if balance_result["success"]:
                return {
                    "success": True,
                    "platform": platform.value,
                    "balance": balance_result["balance"],
                    "message": "连接成功"
                }
            else:
                return {
                    "success": False,
                    "platform": platform.value,
                    "error": balance_result.get("error", "连接失败")
                }
                
        except Exception as e:
            logger.error(f"测试连接失败: {e}")
            return {
                "success": False,
                "platform": platform.value,
                "error": str(e)
            }


# 创建全局SMS管理器实例
_sms_manager = None


def get_sms_manager() -> SMSPlatformManager:
    """
    获取SMS管理器实例（单例模式）
    
    Returns:
        SMSPlatformManager: SMS管理器实例
    """
    global _sms_manager
    if _sms_manager is None:
        _sms_manager = SMSPlatformManager()
    return _sms_manager
