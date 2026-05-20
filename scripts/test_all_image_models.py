"""测试所有可用的图像生成模型"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.core.config import settings


async def test_model(model_name: str, timeout: int = 120):
    """测试单个模型"""
    print(f"\n{'='*80}")
    print(f"测试模型: {model_name}")
    print(f"{'='*80}")
    
    api_key = settings.SILICONFLOW_API_KEY
    if not api_key:
        print("❌ 未配置API密钥")
        return False
    
    try:
        print("发送请求...")
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                f"{settings.SILICONFLOW_BASE_URL}/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "prompt": "AI technology, professional illustration",
                    "image_size": "1024*576",
                    "batch_size": 1,
                    "num_inference_steps": 8
                }
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                if "data" in data and len(data["data"]) > 0:
                    image_url = data["data"][0].get("url", "N/A")
                    print(f"✅ 成功! 图片URL: {image_url[:80]}...")
                    return True
                else:
                    print(f"❌ 返回数据异常: {data}")
                    return False
            else:
                error_msg = response.text[:200]
                print(f"❌ 失败: {error_msg}")
                return False
                
    except asyncio.TimeoutError:
        print(f"⏱️  超时({timeout}秒)")
        return False
    except Exception as e:
        print(f"❌ 异常: {e}")
        return False


async def main():
    print("="*80)
    print("硅基流动图像生成模型测试")
    print("="*80)
    
    # 根据你提供的截图，这些是可用的模型
    models = [
        "Tongyi-MAI/Z-Image-Turbo",  # 通义千问加速版（推荐）
        "Tongyi-MAI/Z-Image",        # 通义千问标准版
        "baidu/ERNIE-Image-Turbo",   # 百度文心加速版
    ]
    
    results = {}
    for model in models:
        success = await test_model(model)
        results[model] = success
        await asyncio.sleep(2)  # 避免请求过快
    
    print("\n" + "="*80)
    print("测试结果汇总")
    print("="*80)
    
    available = [m for m, s in results.items() if s]
    
    if available:
        print(f"\n✅ 可用模型 ({len(available)}个):")
        for i, m in enumerate(available, 1):
            print(f"  {i}. {m}")
        
        print(f"\n 建议:")
        print(f"  使用第一个可用模型: {available[0]}")
        print(f"  已更新到配置文件")
    else:
        print("\n❌ 所有模型都不可用")
        print("\n可能原因:")
        print("  1. API密钥没有图像生成权限")
        print("  2. 账户余额不足")
        print("  3. 需要实名认证")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    asyncio.run(main())
