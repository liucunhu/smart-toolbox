"""简单测试Tongyi-MAI/Z-Image-Turbo模型"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

import httpx
from app.core.config import settings


async def test_zimage():
    print("测试 Tongyi-MAI/Z-Image-Turbo 模型")
    print("=" * 80)
    
    api_key = settings.SILICONFLOW_API_KEY
    if not api_key:
        print("❌ 未配置API密钥")
        return
    
    try:
        print("发送请求...")
        async with httpx.AsyncClient(timeout=180.0) as client:
            response = await client.post(
                f"{settings.SILICONFLOW_BASE_URL}/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "Tongyi-MAI/Z-Image-Turbo",
                    "prompt": "AI technology, machine learning, professional illustration, high quality",
                    "image_size": "1024*576",
                    "batch_size": 1,
                    "num_inference_steps": 8
                }
            )
            
            print(f"状态码: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print("✅ 图像生成成功!")
                print(f"返回数据: {data}")
                
                if "data" in data and len(data["data"]) > 0:
                    image_url = data["data"][0].get("url")
                    print(f"图片URL: {image_url}")
                    return True
            else:
                print(f"❌ 失败: {response.text}")
                
    except Exception as e:
        print(f"❌ 异常: {e}")
        import traceback
        traceback.print_exc()
    
    return False


if __name__ == "__main__":
    result = asyncio.run(test_zimage())
    print("\n" + "=" * 80)
    if result:
        print("✅ 测试通过！Tongyi-MAI/Z-Image-Turbo 模型可用")
    else:
        print("❌ 测试失败")
    print("=" * 80)
