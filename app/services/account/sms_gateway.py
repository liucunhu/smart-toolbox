"""
SMS接码平台对接服务
支持多个接码平台API
"""
import httpx
import asyncio
from app.utils.logger import logger
from typing import Dict, Optional


class SMSGateway:
    """SMS接码平台网关"""
    
    def __init__(self, platform: str = "sms_activate", api_key: str = ""):
        self.platform = platform
        self.api_key = api_key
        self.base_url = self._get_base_url(platform)
    
    def _get_base_url(self, platform: str) -> str:
        """获取平台API地址"""
        platforms = {
            "sms_activate": "https://sms-activate.org/stubs/handler_api.php",
            "5sim": "https://api.5sim.net/v1",
            "smshub": "https://smshub.org/stubs/handler_api.php"
        }
        return platforms.get(platform, "")
    
    async def get_phone_number(self, service: str, country: str = "0") -> Dict:
        """
        获取手机号码
        
        Args:
            service: 服务名称 (tiktok, instagram, wechat, etc.)
            country: 国家代码 (0=俄罗斯, 1=乌克兰, etc.)
        
        Returns:
            {
                "status": "success",
                "access_id": "订单ID",
                "phone_number": "+79999999999"
            }
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "api_key": self.api_key,
                    "action": "getNumber",
                    "service": service,
                    "country": country
                }
                
                response = await client.get(self.base_url, params=params)
                result = response.text
                
                if ":" in result:
                    status, data = result.split(":", 1)
                    if status == "ACCESS_NUMBER":
                        access_id, phone = data.split(":")
                        logger.info(f"成功获取号码: +{phone}")
                        return {
                            "status": "success",
                            "access_id": access_id,
                            "phone_number": f"+{phone}"
                        }
                    else:
                        logger.error(f"获取号码失败: {result}")
                        return {
                            "status": "failed",
                            "error": f"获取号码失败: {result}"
                        }
                
                return {
                    "status": "failed",
                    "error": f"响应格式错误: {result}"
                }
        
        except Exception as e:
            logger.error(f"SMS网关错误: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def get_sms_code(self, access_id: str, max_wait: int = 120) -> Dict:
        """
        获取短信验证码
        
        Args:
            access_id: 订单ID
            max_wait: 最大等待时间（秒）
        
        Returns:
            {
                "status": "success",
                "code": "123456"
            }
        """
        try:
            start_time = asyncio.get_event_loop().time()
            
            while (asyncio.get_event_loop().time() - start_time) < max_wait:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    params = {
                        "api_key": self.api_key,
                        "action": "getStatus",
                        "id": access_id
                    }
                    
                    response = await client.get(self.base_url, params=params)
                    result = response.text
                    
                    if "STATUS_OK" in result:
                        code = result.split(":")[1]
                        logger.info(f"成功获取验证码: {code}")
                        return {
                            "status": "success",
                            "code": code
                        }
                    elif "STATUS_WAIT_CODE" in result:
                        logger.debug("等待验证码...")
                        await asyncio.sleep(5)
                    else:
                        logger.error(f"获取验证码失败: {result}")
                        return {
                            "status": "failed",
                            "error": f"状态异常: {result}"
                        }
            
            return {
                "status": "timeout",
                "error": f"等待验证码超时（{max_wait}秒）"
            }
        
        except Exception as e:
            logger.error(f"获取验证码失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def set_status(self, access_id: str, status: int) -> Dict:
        """
        设置订单状态
        
        Args:
            access_id: 订单ID
            status: 状态码 (1=验证码已发送, 3=取消订单, 6=完成, 8=举报)
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "api_key": self.api_key,
                    "action": "setStatus",
                    "id": access_id,
                    "status": status
                }
                
                response = await client.get(self.base_url, params=params)
                
                if "ACCESS_" in response.text:
                    logger.info(f"订单状态更新成功: {status}")
                    return {
                        "status": "success",
                        "message": response.text
                    }
                else:
                    logger.error(f"状态更新失败: {response.text}")
                    return {
                        "status": "failed",
                        "error": response.text
                    }
        
        except Exception as e:
            logger.error(f"设置状态失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }
    
    async def get_balance(self) -> Dict:
        """查询账户余额"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {
                    "api_key": self.api_key,
                    "action": "getBalance"
                }
                
                response = await client.get(self.base_url, params=params)
                result = response.text
                
                if ":" in result:
                    status, balance = result.split(":")
                    if status == "ACCESS_BALANCE":
                        return {
                            "status": "success",
                            "balance": float(balance)
                        }
                
                return {
                    "status": "failed",
                    "error": f"查询余额失败: {result}"
                }
        
        except Exception as e:
            logger.error(f"查询余额失败: {str(e)}")
            return {
                "status": "failed",
                "error": str(e)
            }


# 使用示例
if __name__ == "__main__":
    async def test_sms():
        gateway = SMSGateway(
            platform="sms_activate",
            api_key="YOUR_API_KEY"
        )
        
        # 1. 查询余额
        balance = await gateway.get_balance()
        print(f"余额: {balance}")
        
        # 2. 获取号码
        result = await gateway.get_phone_number(service="vk")
        print(f"号码: {result}")
        
        if result["status"] == "success":
            # 3. 等待验证码
            code_result = await gateway.get_sms_code(result["access_id"])
            print(f"验证码: {code_result}")
            
            # 4. 设置状态为完成
            if code_result["status"] == "success":
                await gateway.set_status(result["access_id"], 6)
    
    asyncio.run(test_sms())
