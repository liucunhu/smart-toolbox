"""
测试魔搭社区图像生成 - 尝试同步调用
"""
import httpx
import asyncio

# 魔搭社区配置
MODELSCOPE_API_KEY = "ms-bc3203bc-5b62-40e8-9fa0-fd0bcbd1c2a3"
MODELSCOPE_BASE_URL = "https://api-inference.modelscope.cn/v1"

# 尝试不同的模型
MODELS_TO_TEST = [
    "Qwen/Qwen-Image",
    "black-forest-labs/FLUX.1-schnell",
]

async def test_sync_call(model_name: str):
    """测试同步调用"""
    print(f"\n{'='*80}")
    print(f"🧪 测试模型: {model_name}")
    print('='*80)
    
    prompt = "科技未来感背景，蓝色光效，AI元素"
    width, height = 1024, 576
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            # 尝试1: 不使用异步模式（同步调用）
            print("\n[尝试1] 同步调用（无异步头）...")
            response = await client.post(
                f"{MODELSCOPE_BASE_URL}/images/generations",
                headers={
                    "Authorization": f"Bearer {MODELSCOPE_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "n": 1,
                    "size": f"{width}x{height}"
                }
            )
            
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ 成功! 响应: {data}")
                return True
            else:
                print(f"   ❌ 失败: {response.text[:200]}")
            
            # 尝试2: 使用异步模式
            print("\n[尝试2] 异步调用（X-ModelScope-Async-Mode: true）...")
            response = await client.post(
                f"{MODELSCOPE_BASE_URL}/images/generations",
                headers={
                    "Authorization": f"Bearer {MODELSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                    "X-ModelScope-Async-Mode": "true"
                },
                json={
                    "model": model_name,
                    "prompt": prompt,
                    "n": 1,
                    "size": f"{width}x{height}"
                }
            )
            
            print(f"   状态码: {response.status_code}")
            if response.status_code == 200:
                task_data = response.json()
                print(f"   ✅ 响应数据: {task_data}")
                
                # ✅ 尝试直接从响应中获取图像（同步模式）
                if "data" in task_data or "images" in task_data:
                    images = task_data.get("data") or task_data.get("images")
                    if images and len(images) > 0:
                        image_url = images[0].get("url")
                        print(f"   🖼️  直接获取到图像URL: {image_url}")
                        return True
                
                # 如果是异步模式，获取task_id
                task_id = task_data.get("task_id")
                if task_id:
                    print(f"   ℹ️  任务ID: {task_id}（异步模式）")
                    
                    # ✅ 轮询任务状态直到完成
                    max_retries = 30
                    retry_interval = 5
                    
                    for i in range(max_retries):
                        await asyncio.sleep(retry_interval)
                        
                        # 查询任务状态
                        status_response = await client.get(
                            f"{MODELSCOPE_BASE_URL}/tasks/{task_id}",
                            headers={
                                "Authorization": f"Bearer {MODELSCOPE_API_KEY}",
                                "X-ModelScope-Task-Type": "image_generation"
                            }
                        )
                        
                        if status_response.status_code != 200:
                            print(f"   ❌ 查询失败: {status_response.text[:200]}")
                            continue
                        
                        status_data = status_response.json()
                        task_status = status_data.get("task_status", "")
                        
                        print(f"   [{i+1}/{max_retries}] 任务状态: {task_status}")
                        
                        if task_status in ["SUCCEED", "SUCCEEDED"]:
                            # 任务成功，获取图像URL
                            outputs = status_data.get("outputs", {})
                            print(f"   ✅ 任务完成! 输出数据: {outputs}")
                            
                            # 尝试从不同字段获取图像URL
                            image_url = None
                            if "images" in outputs:
                                image_url = outputs["images"][0].get("url")
                            elif "results" in outputs:
                                image_url = outputs["results"][0].get("url")
                            elif "output_images" in status_data:
                                image_url = status_data["output_images"][0]
                            
                            if image_url:
                                print(f"   🖼️  图像URL: {image_url}")
                                print("\n✅ 测试成功！魔搭社区图像生成模型工作正常！")
                                return True
                            else:
                                print(f"   ❌ 未找到图像URL，完整响应: {status_data}")
                                return False
                        
                        elif task_status == "FAILED":
                            error_msg = status_data.get("error", "未知错误")
                            print(f"   ❌ 任务失败: {error_msg}")
                            print(f"   完整响应: {status_data}")
                            return False
                    
                    print(f"   ❌ 任务超时（{max_retries * retry_interval}秒）")
                    return False
            else:
                print(f"   ❌ 失败: {response.text[:200]}")
                
        except Exception as e:
            print(f"   ❌ 异常: {str(e)}")
            import traceback
            traceback.print_exc()
    
    return False

async def main():
    print("=" * 80)
    print("🎨 魔搭社区图像生成 API 测试")
    print("=" * 80)
    
    for model in MODELS_TO_TEST:
        success = await test_sync_call(model)
        if success:
            print(f"\n✅ 模型 {model} 测试通过!")
            break
        else:
            print(f"\n⚠️  模型 {model} 测试失败，继续下一个...")
    
    print("\n" + "=" * 80)
    print("测试完成")
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
