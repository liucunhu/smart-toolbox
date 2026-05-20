"""
API用量查询服务
支持查询各提供商的API余额和用量
"""
import httpx
import asyncio
from typing import Dict, Optional
from app.utils.logger import logger


class APIUsageService:
    """API用量查询服务"""
    
    @staticmethod
    async def get_siliconflow_balance(api_key: str) -> Dict:
        """
        查询硅基流动账户余额（包含代金券）
        
        Note: 硅基流动没有公开的余额查询API，需要通过官网查看
        此方法验证API Key有效性并引导用户到官网查看
        
        Args:
            api_key: 硅基流动API Key
            
        Returns:
            {
                "status": "info",
                "provider": "siliconflow",
                "api_key_valid": true,
                "message": "API Key有效，请前往官网查看详细余额和代金券",
                "dashboard_url": "https://cloud.siliconflow.cn/account/balance"
            }
        """
        try:
            # 验证API Key是否有效（通过一次简单的请求）
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.siliconflow.cn/v1/user/info",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    # 尝试提取用户信息（虽然可能没有余额字段）
                    user_info = data.get("data", {})
                    balance = user_info.get("balance", None)
                    
                    # 构建返回结果
                    if balance is not None:
                        logger.info(f"✅ 硅基流动余额查询成功: {balance} 元")
                        return {
                            "status": "success",
                            "provider": "siliconflow",
                            "balance": float(balance),
                            "currency": "CNY",
                            "message": f"账户余额: {balance} 元",
                            "note": "硅基流动新用户注册赠送16元代金券，余额已包含代金券",
                            "dashboard_url": "https://cloud.siliconflow.cn/account/balance"
                        }
                    else:
                        # API Key有效但没有返回余额信息
                        logger.info("✅ 硅基流动API Key有效（无余额信息返回）")
                        return {
                            "status": "info",
                            "provider": "siliconflow",
                            "api_key_valid": True,
                            "message": "API Key有效，请前往官网查看详细余额和代金券",
                            "note": "新用户注册赠送16元代金券，可在官网查看：剩余额度、有效期等详细信息",
                            "dashboard_url": "https://cloud.siliconflow.cn/account/balance"
                        }
                else:
                    error_msg = f"查询失败 (状态码: {response.status_code}): {response.text[:200]}"
                    logger.error(f"❌ 硅基流动余额查询失败: {error_msg}")
                    
                    return {
                        "status": "failed",
                        "provider": "siliconflow",
                        "error": error_msg
                    }
        
        except Exception as e:
            logger.error(f"❌ 硅基流动余额查询异常: {e}")
            return {
                "status": "failed",
                "provider": "siliconflow",
                "error": str(e)
            }
    
    @staticmethod
    async def get_modelscope_usage(api_key: str) -> Dict:
        """
        查询魔搭社区使用情况
        
        Note: 魔搭社区没有公开的余额查询API，返回提示信息
        
        Args:
            api_key: 魔搭社区API Key
            
        Returns:
            {
                "status": "info",
                "provider": "modelscope",
                "message": "请前往官网查看: https://modelscope.cn/my/myaccesstoken"
            }
        """
        try:
            # 验证API Key是否有效（通过一次简单的请求）
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api-inference.modelscope.cn/v1/models",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    logger.info("✅ 魔搭社区API Key有效")
                    return {
                        "status": "info",
                        "provider": "modelscope",
                        "api_key_valid": True,
                        "message": "API Key有效，请前往官网查看详细用量: https://modelscope.cn/my/myaccesstoken",
                        "dashboard_url": "https://modelscope.cn/my/myaccesstoken"
                    }
                else:
                    logger.warning(f"⚠️  魔搭社区API Key可能无效: {response.status_code}")
                    return {
                        "status": "warning",
                        "provider": "modelscope",
                        "api_key_valid": False,
                        "message": "API Key可能无效，请检查配置"
                    }
        
        except Exception as e:
            logger.error(f"❌ 魔搭社区API验证异常: {e}")
            return {
                "status": "failed",
                "provider": "modelscope",
                "error": str(e)
            }
    
    @staticmethod
    async def get_dashscope_usage(api_key: str) -> Dict:
        """
        查询阿里百炼使用情况
        
        Note: 阿里百炼没有公开的余额查询API，返回提示信息
        
        Args:
            api_key: 阿里百炼API Key
            
        Returns:
            {
                "status": "info",
                "provider": "dashscope",
                "message": "请前往控制台查看: https://dashscope.console.aliyun.com/overview"
            }
        """
        try:
            # 验证API Key是否有效
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://dashscope.aliyuncs.com/api/v1/services/aigc/text-generation/generation",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": "qwen-turbo",
                        "input": {"messages": [{"role": "user", "content": "hi"}]},
                        "parameters": {}
                    }
                )
                
                # 401表示认证失败，其他状态码表示Key有效
                if response.status_code != 401:
                    logger.info("✅ 阿里百炼API Key有效")
                    return {
                        "status": "info",
                        "provider": "dashscope",
                        "api_key_valid": True,
                        "message": "API Key有效，请前往控制台查看详细用量: https://dashscope.console.aliyun.com/overview",
                        "dashboard_url": "https://dashscope.console.aliyun.com/overview"
                    }
                else:
                    logger.warning("⚠️  阿里百炼API Key无效")
                    return {
                        "status": "warning",
                        "provider": "dashscope",
                        "api_key_valid": False,
                        "message": "API Key无效，请检查配置"
                    }
        
        except Exception as e:
            logger.error(f"❌ 阿里百炼API验证异常: {e}")
            return {
                "status": "failed",
                "provider": "dashscope",
                "error": str(e)
            }
    
    @staticmethod
    async def get_moonshot_balance(api_key: str) -> Dict:
        """
        查询月之暗面（Moonshot/Kimi）账户余额和代金券
        
        Args:
            api_key: 月之暗面API Key
            
        Returns:
            {
                "status": "success",
                "provider": "moonshot",
                "balance": 100.50,
                "voucher_balance": 16.00,
                "cash_balance": 84.50,
                "currency": "CNY",
                "message": "总余额: 100.50元 (代金券: 16.00元, 现金: 84.50元)"
            }
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.moonshot.cn/v1/users/me/balance",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    available_balance = data.get("available_balance", 0)
                    voucher_balance = data.get("voucher_balance", 0)
                    cash_balance = data.get("cash_balance", 0)
                    
                    logger.info(f"✅ 月之暗面余额查询成功: 总计{available_balance}元 (代金券:{voucher_balance}元, 现金:{cash_balance}元)")
                    
                    return {
                        "status": "success",
                        "provider": "moonshot",
                        "balance": float(available_balance),
                        "voucher_balance": float(voucher_balance),
                        "cash_balance": float(cash_balance),
                        "currency": "CNY",
                        "message": f"总余额: {available_balance}元 (代金券: {voucher_balance}元, 现金: {cash_balance}元)"
                    }
                else:
                    error_msg = f"查询失败 (状态码: {response.status_code}): {response.text[:200]}"
                    logger.error(f"❌ 月之暗面余额查询失败: {error_msg}")
                    
                    return {
                        "status": "failed",
                        "provider": "moonshot",
                        "error": error_msg
                    }
        
        except Exception as e:
            logger.error(f"❌ 月之暗面余额查询异常: {e}")
            return {
                "status": "failed",
                "provider": "moonshot",
                "error": str(e)
            }
    
    @staticmethod
    async def get_provider_usage(provider: str, api_key: str) -> Dict:
        """
        根据提供商查询API用量
        
        Args:
            provider: 提供商名称 (siliconflow/modelscope/dashscope/moonshot)
            api_key: API Key
            
        Returns:
            用量信息字典
        """
        if provider == "siliconflow":
            return await APIUsageService.get_siliconflow_balance(api_key)
        elif provider == "modelscope":
            return await APIUsageService.get_modelscope_usage(api_key)
        elif provider == "dashscope":
            return await APIUsageService.get_dashscope_usage(api_key)
        elif provider == "moonshot":
            return await APIUsageService.get_moonshot_balance(api_key)
        else:
            return {
                "status": "failed",
                "provider": provider,
                "error": f"不支持的提供商: {provider}"
            }


# 测试代码
if __name__ == "__main__":
    async def test():
        print("=" * 80)
        print("🔍 测试API用量查询")
        print("=" * 80)
        
        # 测试硅基流动
        print("\n[1] 测试硅基流动...")
        result = await APIUsageService.get_siliconflow_balance("sk-your-api-key")
        print(f"结果: {result}")
        
        # 测试魔搭社区
        print("\n[2] 测试魔搭社区...")
        result = await APIUsageService.get_modelscope_usage("ms-your-api-key")
        print(f"结果: {result}")
        
        # 测试阿里百炼
        print("\n[3] 测试阿里百炼...")
        result = await APIUsageService.get_dashscope_usage("sk-your-api-key")
        print(f"结果: {result}")
    
    asyncio.run(test())
