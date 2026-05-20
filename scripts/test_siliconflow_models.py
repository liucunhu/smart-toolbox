"""测试硅基流动图像生成模型名称"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.core.config import settings


async def test_model(model_name: str):
    """测试单个模型"""
    print(f"\n测试模型: {model_name}")
    
    api_key = settings.SILICONFLOW_API_KEY
    if not api_key:
        print("❌ 未配置API密钥")
        return
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{settings.SILICONFLOW_BASE_URL}/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "prompt": "test",
                    "image_size": "1024x576",
                    "batch_size": 1
                }
            )
            
            if response.status_code == 200:
                print(f"✅ 模型 {model_name} 可用!")
                return True
            else:
                error = response.json()
                print(f"❌ 模型 {model_name} 失败: {error.get('message', 'Unknown')}")
                return False
                
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


async def main():
    """测试所有候选模型"""
    print("=" * 80)
    print("硅基流动图像生成模型测试")
    print("=" * 80)
    
    # 候选模型列表（根据用户提供的截图）
    models = [
        "Z-Image-Turbo",
        "black-forest-labs/Z-Image-Turbo",
        "Z-Image",
        "black-forest-labs/Z-Image",
        "ERNIE-Image-Turbo",
        "baidu/ERNIE-Image-Turbo",
        "Qwen-Image",
        "Qwen/Qwen-Image",
        "Kolors",
        "Kwai-Kolors/Kolors",
    ]
    
    results = {}
    for model in models:
        success = await test_model(model)
        results[model] = success
        await asyncio.sleep(1)  # 避免请求过快
    
    print("\n" + "=" * 80)
    print("测试结果汇总")
    print("=" * 80)
    
    available = [m for m, s in results.items() if s]
    if available:
        print(f"\n✅ 可用模型 ({len(available)}个):")
        for m in available:
            print(f"  - {m}")
    else:
        print("\n❌ 所有模型都不可用")
    
    print("\n建议:")
    if available:
        print(f"  使用第一个可用模型: {available[0]}")
    else:
        print("  1. 检查API密钥是否有图像生成权限")
        print("  2. 登录 https://cloud.siliconflow.cn/models 查看实际模型列表")
        print("  3. 联系硅基流动客服确认")


if __name__ == "__main__":
    asyncio.run(main())
