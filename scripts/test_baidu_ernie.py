"""测试百度ERNIE-Image-Turbo模型"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.core.config import settings


async def test_baidu_ernie():
    print("测试 baidu/ERNIE-Image-Turbo 模型")
    print("=" * 80)
    
    api_key = settings.SILICONFLOW_API_KEY
    if not api_key:
        print("❌ 未配置API密钥")
        return
    
    try:
        print("发送请求...")
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{settings.SILICONFLOW_BASE_URL}/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "baidu/ERNIE-Image-Turbo",
                    "prompt": "AI technology, professional illustration, high quality",
                    "image_size": "1024x576",  # 使用x而不是*
                    "batch_size": 1
                }
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 图像生成成功!")
                
                if "data" in data and len(data["data"]) > 0:
                    image_url = data["data"][0].get("url")
                    print(f"图片URL: {image_url}")
                    return True
                else:
                    print(f"返回数据: {data}")
            else:
                print(f"❌ 失败: {response.text}")
                
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
    
    return False


if __name__ == "__main__":
    result = asyncio.run(test_baidu_ernie())
    print("\n" + "=" * 80)
    if result:
        print("✅ 测试通过！baidu/ERNIE-Image-Turbo 模型可用")
    else:
        print("❌ 测试失败")
    print("=" * 80)
