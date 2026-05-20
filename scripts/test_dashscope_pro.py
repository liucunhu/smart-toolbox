"""
测试阿里百炼（DashScope）图像生成 - 专业版
使用 qwen-image-2.0-pro-2026-04-22 模型（100张免费额度）
"""
import httpx
import asyncio
from pathlib import Path

# 阿里百炼配置
DASHSCOPE_API_KEY = "sk-e28ba64c17ae4321a7d00620264e0a68"
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/api/v1"
# ✅ 使用文生图模型（不是图生图）
IMAGE_MODEL = "wanx2.1-t2i-turbo"  # 通义万相文生图

async def test_dashscope_pro():
    """测试阿里百炼专业版图像生成"""
    print("=" * 80)
    print("🎨 测试阿里百炼图像生成（wanx2.1-t2i-turbo 文生图）")
    print("=" * 80)
    
    prompt = "科技未来感背景，蓝色光效，AI元素，4K超高清，专业摄影"
    
    print(f"\n📝 提示词: {prompt}")
    print(f"🔑 模型: {IMAGE_MODEL}")
    print(f"💰 费用: 0.14元/张\n")
    
    output_dir = Path("output/test_dashscope")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            # 步骤1: 创建任务
            print("[1/3] 创建图像生成任务...")
            print(f"   API端点: {DASHSCOPE_BASE_URL}/services/aigc/text2image/image-synthesis")
            response = await client.post(
                f"{DASHSCOPE_BASE_URL}/services/aigc/text2image/image-synthesis",
                headers={
                    "Authorization": f"Bearer {DASHSCOPE_API_KEY}",
                    "Content-Type": "application/json",
                    "X-DashScope-Async": "enable"
                },
                json={
                    "model": IMAGE_MODEL,
                    "input": {"prompt": prompt},
                    "parameters": {
                        "size": "1024*576",
                        "n": 1
                    }
                }
            )
            
            if response.status_code != 200:
                print(f"❌ 创建失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                return False
            
            task_data = response.json()
            task_id = task_data.get("output", {}).get("task_id")
            print(f"✅ 任务创建成功! Task ID: {task_id}\n")
            
            # 步骤2: 轮询状态
            print("[2/3] 等待图像生成...")
            for i in range(30):
                await asyncio.sleep(5)
                
                status_resp = await client.get(
                    f"{DASHSCOPE_BASE_URL}/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {DASHSCOPE_API_KEY}"}
                )
                
                status = status_resp.json().get("output", {}).get("task_status", "")
                print(f"  状态: {status} (第{i+1}次查询)")
                
                if status == "SUCCEEDED":
                    # 获取图像URL
                    results = status_resp.json().get("output", {}).get("results", [])
                    if results:
                        image_url = results[0].get("url")
                        print(f"\n✅ 图像生成成功!")
                        print(f"🖼️  URL: {image_url}\n")
                        
                        # 步骤3: 下载图像
                        print("[3/3] 下载图像...")
                        img_resp = await client.get(image_url)
                        
                        filename = f"dashscope_pro_{task_id[:8]}.png"
                        filepath = output_dir / filename
                        
                        with open(filepath, 'wb') as f:
                            f.write(img_resp.content)
                        
                        print(f"✅ 图像已保存: {filepath}")
                        print(f"📦 文件大小: {len(img_resp.content) / 1024:.2f} KB")
                        
                        # Windows自动打开
                        import os
                        os.startfile(filepath)
                        
                        print("\n" + "=" * 80)
                        print("🎉 测试成功！专业版图像已生成并保存")
                        print("=" * 80)
                        return True
                
                elif status == "FAILED":
                    print(f"❌ 任务失败: {status_resp.json()}")
                    return False
            
            print("❌ 超时")
            return False
            
        except Exception as e:
            print(f"❌ 异常: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    asyncio.run(test_dashscope_pro())
