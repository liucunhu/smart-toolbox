"""
简单测试魔搭社区图像生成模型（Qwen/Qwen-Image-2512）
"""
import httpx
import asyncio

# 搭社区配置
MODELSCOPE_API_KEY = "ms-bc3203bc-5b62-40e8-9fa0-fd0bcbd1c2a3"  # 修复：添加完整的API密钥
MODELSCOPE_BASE_URL = "https://api-inference.modelscope.cn/v1"
# ✅ 使用魔搭社区可用的图像生成模型
# 注意：不是所有模型都支持API-Inference，需要选择已启用API的模型
IMAGE_MODEL = "Qwen/Qwen-Image"  # Qwen图像生成模型
# 其他可选模型：
# - Qwen/Qwen-Image (通义千问图像生成)
# - black-forest-labs/FLUX.1-schnell (需要确认是否启用API)
# - stabilityai/stable-diffusion-3.5-large (需要确认是否启用API)

async def test_modelscope():
    """测试魔搭社区图像生成"""
    print("=" * 80)
    print("🎨 测试魔搭社区图像生成模型（Qwen/Qwen-Image-2512）")
    print("=" * 80)
    
    prompt = "科技未来感背景，蓝色光效，AI元素，4K超高清"
    width, height = 1024, 576
    
    print(f"\n📝 提示词: {prompt}")
    print(f" 尺寸: {width}x{height}")
    print(f"🔑 模型: {IMAGE_MODEL}")
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            # ✅ 步骤1: 创建异步任务
            response = await client.post(
                f"{MODELSCOPE_BASE_URL}/images/generations",
                headers={
                    "Authorization": f"Bearer {MODELSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                    "X-ModelScope-Async-Mode": "true"  # ✅ 魔搭社区要求使用 "true"
                },
                json={
                    "model": IMAGE_MODEL,
                    "prompt": prompt,
                    "n": 1,
                    "size": f"{width}x{height}"
                }
            )
            
            print(f"\n📊 响应状态码: {response.status_code}")
            
            if response.status_code == 200:
                task_data = response.json()
                task_id = task_data.get("task_id")
                
                if task_id:
                    print(f"✅ 任务创建成功! Task ID: {task_id}")
                    
                    # ✅ 步骤2: 轮询任务状态
                    import asyncio
                    max_retries = 30
                    retry_interval = 5
                    
                    for i in range(max_retries):
                        await asyncio.sleep(retry_interval)
                        
                        # 查询任务状态
                        # ✅ 尝试不同的端点格式
                        task_status_url = f"{MODELSCOPE_BASE_URL}/tasks/{task_id}"
                        print(f"   查询URL: {task_status_url}")  # ✅ 调试信息
                        
                        status_response = await client.get(
                            task_status_url,
                            headers={
                                "Authorization": f"Bearer {MODELSCOPE_API_KEY}"
                            }
                        )
                        
                        if status_response.status_code != 200:
                            print(f" 查询任务状态失败: {status_response.text}")
                            continue
                        
                        status_data = status_response.json()
                        task_status = status_data.get("task_status", "")
                        
                        print(f"   任务状态: {task_status} (第{i+1}次轮询)")
                        
                        if task_status == "SUCCEEDED":
                            # 任务成功，获取图像URL
                            results = status_data.get("results", [])
                            if results and len(results) > 0:
                                image_url = results[0].get("url")
                                
                                if image_url:
                                    print(f"\n🖼️ 图像URL: {image_url}")
                                    print("\n✅ 测试成功！魔搭社区图像生成模型工作正常！")
                                    return True
                            
                            print(f"❌ 任务成功但未获取到图像URL: {status_data}")
                            return False
                        
                        elif task_status == "FAILED":
                            error_msg = status_data.get("message", "未知错误")
                            print(f"❌ 任务失败: {error_msg}")
                            print(f"   完整响应: {status_data}")  # ✅ 输出完整错误信息
                            return False
                    
                    print(f"❌ 任务超时（{max_retries * retry_interval}秒）")
                    return False
                else:
                    print(f"❌ 未获取到Task ID: {task_data}")
                    return False
            else:
                print(f"❌ API请求失败: {response.text}")
                return False
                
        except Exception as e:
            print(f" 测试异常: {str(e)}")
            return False

if __name__ == "__main__":
    asyncio.run(test_modelscope())
