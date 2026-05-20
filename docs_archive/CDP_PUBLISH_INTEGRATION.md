# 头条CDP发布功能集成文档

## 📋 概述

CDP (Chrome DevTools Protocol) 模式是头条发布的**最可靠方案**，通过连接真实的Edge浏览器实现100%还原真实用户环境。

### ✅ 优势

- **100%真实浏览器环境**：无任何自动化特征
- **绕过所有检测**：头条无法检测到自动化工具
- **完整页面加载**：微前端架构完美支持
- **Cookie持久化**：登录状态自动保存
- **稳定可靠**：经过多次测试验证

---

## 🚀 快速开始

### 方式1：使用API接口（推荐）

#### 1. 普通发布接口

```bash
curl -X POST http://localhost:8000/api/v1/content/toutiao/publish \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "title": "人工智能技术发展趋势分析",
    "content": "这是一篇关于人工智能的深度分析文章...",
    "category": "科技",
    "tags": ["AI", "机器学习"],
    "use_cdp": true,
    "cdp_port": 9222
  }'
```

#### 2. 一键全自动发布

```bash
curl -X POST http://localhost:8000/api/v1/content/toutiao/auto_publish \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "topic": "人工智能",
    "username": "你的账号",
    "password": "你的密码",
    "category": "科技",
    "auto_generate_cover": true,
    "use_cdp": true,
    "cdp_port": 9222
  }'
```

---

### 方式2：使用Python脚本

项目提供了两个CDP测试脚本：

#### 简化版（推荐新手）

```powershell
python scripts\quick_cdp_publish.py
```

**特点：**
- ✅ 代码简洁（369行）
- ✅ 中文提示详细
- ✅ 适合快速测试
- ❌ 不支持封面图上传

#### 完整版（功能齐全）

```powershell
python scripts\test_cdp_auto_publish.py
```

**特点：**
- ✅ 功能完整（1106行）
- ✅ 支持封面图上传
- ✅ 支持文章配图
- ✅ 支持A/B测试
- ⚠️ 代码较复杂

---

## 🔧 技术实现

### 后端集成

#### 1. ToutiaoPublisher 类

位置：`app/services/publish/toutiao_publisher.py`

```python
class ToutiaoPublisher:
    """今日头条自动化发布引擎"""
    
    async def initialize_browser(self, use_cdp: bool = False, cdp_port: int = 9222):
        """
        初始化浏览器
        
        :param use_cdp: 是否使用CDP连接真实Edge浏览器
        :param cdp_port: CDP调试端口，默认9222
        """
        if use_cdp:
            await self.initialize_with_cdp(cdp_port)
        else:
            await self.initialize_standard_browser()
    
    async def initialize_with_cdp(self, cdp_port: int = 9222):
        """使用CDP连接真实Edge浏览器"""
        # 1. 启动Edge浏览器（带远程调试）
        # 2. 连接到Edge浏览器
        # 3. 获取context和page
```

#### 2. API接口

位置：`app/api/v1/endpoints.py`

**接口1：普通发布**
```python
@router.post("/content/toutiao/publish")
def publish_toutiao_article(
    account_id: int,
    title: str,
    content: str,
    use_cdp: bool = True,  # CDP模式开关
    cdp_port: int = 9222,  # CDP端口
    ...
):
```

**接口2：一键发布**
```python
@router.post("/content/toutiao/auto_publish")
def auto_publish_toutiao(
    account_id: int,
    topic: str,
    username: str,
    password: str,
    use_cdp: bool = True,  # CDP模式开关
    cdp_port: int = 9222,  # CDP端口
    ...
):
```

---

## 📊 工作流程

### CDP模式完整流程

```
[1/5] 启动Edge浏览器
  ├─ 关闭已有Edge进程
  ├─ 启动带远程调试的Edge
  └─ 等待5秒完全启动

[2/5] 连接浏览器
  ├─ Playwright连接CDP端口
  ├─ 获取context和page
  └─ 验证连接成功

[3/5] 检查登录状态
  ├─ 如果已登录 → 继续
  └─ 如果未登录 → 等待手动登录（最多120秒）

[4/5] 访问发布页面
  ├─ 智能跳转（避免导航冲突）
  ├─ 等待10秒页面加载
  └─ 验证页面元素（编辑器、标题框、发布按钮）

[5/5] 填写并发布
  ├─ 填写标题
  ├─ 填写正文
  ├─ 选择分类
  ├─ 点击发布按钮
  └─ 等待发布结果
```

---

## ⚙️ 配置说明

### CDP端口配置

默认端口：`9222`

如果需要修改端口：

```python
# API调用时指定
{
  "use_cdp": true,
  "cdp_port": 9223  # 自定义端口
}
```

### Edge浏览器路径

默认路径：
- `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`
- `C:\Program Files\Microsoft\Edge\Application\msedge.exe`

如果Edge安装在其他位置，需要修改 `toutiao_publisher.py` 第47-49行。

### 用户数据目录

CDP模式使用：`./edge_profile_toutiao_cdp`

标准模式使用：`./edge_profile_toutiao`

---

## 🎯 使用场景

### 场景1：日常发布（推荐CDP）

```python
# Python代码示例
import requests

response = requests.post(
    "http://localhost:8000/api/v1/content/toutiao/publish",
    json={
        "account_id": 1,
        "title": "我的文章标题",
        "content": "文章内容...",
        "category": "科技",
        "use_cdp": True  # 使用CDP模式
    }
)

print(response.json())
```

### 场景2：批量发布

```python
articles = [
    {"title": "文章1", "content": "内容1"},
    {"title": "文章2", "content": "内容2"},
    {"title": "文章3", "content": "内容3"},
]

for article in articles:
    response = requests.post(
        "http://localhost:8000/api/v1/content/toutiao/publish",
        json={
            "account_id": 1,
            "title": article["title"],
            "content": article["content"],
            "use_cdp": True
        }
    )
    print(f"发布结果: {response.json()}")
```

### 场景3：定时发布

结合Celery任务调度：

```python
from app.tasks.content_tasks import publish_toutiao_task

# 延迟执行
publish_toutiao_task.apply_async(
    kwargs={
        "account_id": 1,
        "title": "定时文章",
        "content": "内容...",
        "use_cdp": True
    },
    countdown=3600  # 1小时后执行
)
```

---

## 🔍 调试技巧

### 1. 查看日志

日志文件位置：`logs/`

```powershell
# 查看最新日志
Get-Content logs\*.log -Tail 50
```

### 2. 查看截图

每次发布都会保存截图：

```powershell
# 查看最新截图
Get-ChildItem logs\cdp_publish_*.png | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Invoke-Item
```

### 3. 浏览器保持打开

CDP脚本会在发布后保持浏览器打开，方便检查结果。

在终端按回车才会关闭浏览器。

### 4. 验证发布结果

```powershell
python scripts\verify_toutiao_publish.py
```

---

## ❓ 常见问题

### Q1: CDP连接失败

**错误：** `Connection refused`

**解决：**
```powershell
# 1. 关闭所有Edge进程
taskkill /F /IM msedge.exe

# 2. 等待2秒
Start-Sleep -Seconds 2

# 3. 重新运行
python scripts\quick_cdp_publish.py
```

### Q2: 页面加载不完整

**现象：** 编辑器或发布按钮找不到

**解决：**
- 增加等待时间（修改脚本中的 `await asyncio.sleep(10)` 为更长时间）
- 检查网络连接
- 手动刷新页面后按回车继续

### Q3: 发布后找不到文章

**解决：**
1. 访问头条后台：https://mp.toutiao.com/profile_v4/graphic/articles
2. 查看"全部"或"审核中"标签
3. 运行验证脚本：`python scripts\verify_toutiao_publish.py`

### Q4: Cookie失效

**解决：**
CDP模式会自动保存Cookie到浏览器配置文件，下次启动会自动登录。

如果仍然需要重新登录，在浏览器中手动登录即可。

---

## 📈 性能对比

| 特性 | CDP模式 | 标准模式 |
|------|---------|---------|
| 真实性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 速度 | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| 兼容性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 推荐度 | ✅ 强烈推荐 | 备选方案 |

---

## 🎓 最佳实践

### 1. 始终使用CDP模式

```python
# ✅ 推荐
use_cdp = True

# ❌ 不推荐（除非特殊情况）
use_cdp = False
```

### 2. 复用浏览器实例

CDP模式会复用浏览器配置文件，登录状态自动保存。

### 3. 合理设置超时

头条发布可能需要30-60秒，确保前端超时设置足够长（建议120秒）。

### 4. 定期检查日志

```powershell
# 每天检查一次日志
Get-Content logs\*.log | Select-String "ERROR" | Measure-Object
```

### 5. 备份浏览器配置

定期备份 `edge_profile_toutiao_cdp` 目录，防止Cookie丢失。

---

## 📝 更新日志

### v1.0 (2026-05-04)
- ✅ 集成CDP模式到API接口
- ✅ 添加 `use_cdp` 和 `cdp_port` 参数
- ✅ 创建简化版CDP脚本 `quick_cdp_publish.py`
- ✅ 完善文档和示例

---

## 🔗 相关资源

- [ToutiaoPublisher源码](../app/services/publish/toutiao_publisher.py)
- [API接口定义](../app/api/v1/endpoints.py)
- [CDP测试脚本](../scripts/test_cdp_auto_publish.py)
- [简化版脚本](../scripts/quick_cdp_publish.py)
- [验证脚本](../scripts/verify_toutiao_publish.py)

---

## 💡 总结

CDP模式是头条发布的**最佳方案**，具有以下优势：

1. ✅ **100%真实浏览器**：无任何自动化特征
2. ✅ **稳定可靠**：经过多次测试验证
3. ✅ **易于使用**：一行代码即可启用
4. ✅ **功能完整**：支持所有高级功能

**强烈建议在生产和测试环境中都使用CDP模式！**
