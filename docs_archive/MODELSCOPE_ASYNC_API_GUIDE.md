# 魔搭社区图像生成 API 使用说明

## ⚠️ 重要提示

**魔搭社区（ModelScope）的图像生成 API 不支持同步调用，必须使用异步模式！**

---

## 错误示例

### ❌ 错误调用（会导致400错误）

```python
# 错误：没有设置异步模式头
response = await client.post(
    "https://api-inference.modelscope.cn/v1/images/generations",
    headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
        # ❌ 缺少 X-ModelScope-Async-Mode 头
    },
    json={
        "model": "black-forest-labs/FLUX.1-schnell",
        "prompt": "科技未来感背景",
        "n": 1,
        "size": "1024x576"
    }
)

# 错误响应：
# {"errors":{"message":"image-gen task currently does not support synchronous calls. 
# Please refer to the documentation and set header X-ModelScope-Async-Mode=true to 
# switch to asynchronous calling mode"},"request_id":"..."}
```

---

## 正确示例

### ✅ 正确调用（异步模式）

```python
import httpx
import asyncio

async def generate_image_with_modelscope(api_key: str, prompt: str):
    """使用魔搭社区异步API生成图像"""
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        # 步骤1: 创建异步任务
        response = await client.post(
            "https://api-inference.modelscope.cn/v1/images/generations",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "X-ModelScope-Async-Mode": "enable"  # ✅ 必须设置！
            },
            json={
                "model": "black-forest-labs/FLUX.1-schnell",
                "prompt": prompt,
                "n": 1,
                "size": "1024x576"
            }
        )
        
        if response.status_code != 200:
            raise Exception(f"任务创建失败: {response.text}")
        
        task_data = response.json()
        task_id = task_data.get("task_id")
        
        if not task_id:
            raise Exception(f"未获取到Task ID: {task_data}")
        
        print(f"✅ 任务创建成功! Task ID: {task_id}")
        
        # 步骤2: 轮询任务状态
        max_retries = 30
        retry_interval = 5
        
        for i in range(max_retries):
            await asyncio.sleep(retry_interval)
            
            # 查询任务状态
            status_response = await client.get(
                f"https://api-inference.modelscope.cn/v1/tasks/{task_id}",
                headers={
                    "Authorization": f"Bearer {api_key}"
                }
            )
            
            if status_response.status_code != 200:
                print(f" 查询任务状态失败")
                continue
            
            status_data = status_response.json()
            task_status = status_data.get("task_status", "")
            
            print(f"   任务状态: {task_status} (第{i+1}次轮询)")
            
            if task_status == "SUCCEEDED":
                # 任务成功，获取图像URL
                results = status_data.get("results", [])
                if results and len(results) > 0:
                    image_url = results[0].get("url")
                    print(f"✅ 图像生成成功! URL: {image_url}")
                    return image_url
            
            elif task_status == "FAILED":
                error_msg = status_data.get("message", "未知错误")
                raise Exception(f"任务失败: {error_msg}")
        
        raise Exception("任务超时")
```

---

## API 调用流程

```
1. 创建异步任务
   POST /images/generations
   Headers: X-ModelScope-Async-Mode: enable
   
2. 获取 Task ID
   Response: {"task_id": "xxx"}
   
3. 轮询任务状态
   GET /tasks/{task_id}
   
4. 检查任务状态
   - PENDING: 等待中
   - RUNNING: 运行中
   - SUCCEEDED: 成功
   - FAILED: 失败
   
5. 获取图像 URL
   Response: {"results": [{"url": "..."}]}
   
6. 下载图像
   GET {image_url}
```

---

## 关键要点

### 1. 必须设置异步模式头

```python
headers={
    "X-ModelScope-Async-Mode": "enable"  # ✅ 或者 "true"
}
```

### 2. 使用正确的模型

魔搭社区支持的图像生成模型：
- `black-forest-labs/FLUX.1-schnell` (快速，质量高，推荐)
- `stabilityai/stable-diffusion-3.5-large` (SD3.5，专业级)
- `Kwai-Kolors/Kolors` (可图，适合中文内容)

### 3. 尺寸格式

使用 `x` 分隔符，不是 `*`：
```python
"size": "1024x576"  # ✅ 正确
# "size": "1024*576"  # ❌ 错误
```

### 4. 超时设置

图像生成需要较长时间，建议设置：
```python
async with httpx.AsyncClient(timeout=180.0) as client:
```

### 5. 轮询间隔

建议每5秒轮询一次，最多30次（150秒）：
```python
max_retries = 30
retry_interval = 5
```

---

## 完整示例代码

项目中已实现的完整代码：

**文件**: `app/services/content/image_generator.py`

```python
async def _generate_with_modelscope(self, prompt: str, aspect_ratio: str) -> Dict:
    """使用魔搭社区（ModelScope）生成图像"""
    try:
        api_key = settings.MODELSCOPE_API_KEY
        image_model = 'black-forest-labs/FLUX.1-schnell'
        
        width, height = self._parse_aspect_ratio(aspect_ratio)
        
        async with httpx.AsyncClient(timeout=180.0) as client:
            # 步骤1: 创建异步任务
            response = await client.post(
                f"{settings.MODELSCOPE_BASE_URL}/images/generations",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "X-ModelScope-Async-Mode": "enable"  # ✅ 关键！
                },
                json={
                    "model": image_model,
                    "prompt": prompt,
                    "n": 1,
                    "size": f"{width}x{height}"
                }
            )
            
            # 步骤2: 获取 Task ID
            task_data = response.json()
            task_id = task_data.get("task_id")
            
            # 步骤3: 轮询任务状态
            for i in range(30):
                await asyncio.sleep(5)
                
                status_response = await client.get(
                    f"{settings.MODELSCOPE_BASE_URL}/tasks/{task_id}",
                    headers={"Authorization": f"Bearer {api_key}"}
                )
                
                status_data = status_response.json()
                task_status = status_data.get("task_status", "")
                
                if task_status == "SUCCEEDED":
                    # 获取图像并下载
                    results = status_data.get("results", [])
                    image_url = results[0].get("url")
                    # ... 下载保存图像
                    return {"status": "success", "image_path": "..."}
                
                elif task_status == "FAILED":
                    return {"status": "failed", "error": "..."}
            
            return {"status": "failed", "error": "超时"}
    
    except Exception as e:
        return {"status": "failed", "error": str(e)}
```

---

## 测试脚本

使用测试脚本验证魔搭社区API：

```bash
python scripts\simple_test_modelscope.py
```

测试脚本已包含完整的异步调用逻辑。

---

## 常见问题

### Q1: 为什么会返回400错误？

**A**: 没有设置 `X-ModelScope-Async-Mode` 头，魔搭社区不支持同步调用。

### Q2: 异步模式和同步模式有什么区别？

**A**: 
- **同步模式**: 请求后直接返回结果（魔搭社区不支持）
- **异步模式**: 先创建任务，然后轮询获取结果

### Q3: 轮询频率应该是多少？

**A**: 建议每5秒轮询一次，不要太频繁，避免API限流。

### Q4: 如果任务一直不完成怎么办？

**A**: 设置最大轮询次数（30次）和超时时间（150秒），超时后返回错误。

### Q5: 可以使用哪些图像生成模型？

**A**: 魔搭社区支持多个模型：
- FLUX.1-schnell（推荐，快速）
- SD3.5-large（专业级）
- Kolors（适合中文）

---

## 配置文件

确保 `.env` 文件中配置正确：

```env
# 魔搭社区配置
LLM_PROVIDER=modelscope
MODELSCOPE_API_KEY=ms-bc3203bc-5b62-40e8-9fa0-fd0bcbd1c2a3
MODELSCOPE_BASE_URL=https://api-inference.modelscope.cn/v1
MODELSCOPE_MODEL=Qwen/Qwen2.5-72B-Instruct
MODELSCOPE_IMAGE_MODEL=black-forest-labs/FLUX.1-schnell
```

---

## 已修复的问题

1. ✅ 添加了 `X-ModelScope-Async-Mode: enable` 头
2. ✅ 实现了异步任务创建和轮询逻辑
3. ✅ 更新了头条发布服务，使用默认提供商（modelscope）
4. ✅ 修复了测试脚本，使用正确的异步模式

现在魔搭社区图像生成应该可以正常工作了！
