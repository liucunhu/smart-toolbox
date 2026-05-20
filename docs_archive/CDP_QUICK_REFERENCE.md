# CDP发布功能 - 快速参考

## 🚀 一键使用

### Python脚本
```powershell
# 简化版（推荐）
python scripts\quick_cdp_publish.py

# 完整版
python scripts\test_cdp_auto_publish.py
```

### API调用
```bash
curl -X POST http://localhost:8000/api/v1/content/toutiao/publish \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": 1,
    "title": "文章标题",
    "content": "文章内容...",
    "use_cdp": true,
    "cdp_port": 9222
  }'
```

---

## 📁 核心文件

| 文件 | 路径 | 说明 |
|------|------|------|
| **Publisher类** | `app/services/publish/toutiao_publisher.py` | CDP实现核心 |
| **API接口** | `app/api/v1/endpoints.py` | 后端API（第453、604行） |
| **前端页面** | `frontend/src/views/ContentCreation.vue` | 前端调用 |
| **简化脚本** | `scripts/quick_cdp_publish.py` | 快速测试 |
| **完整脚本** | `scripts/test_cdp_auto_publish.py` | 完整功能 |
| **验证脚本** | `scripts/verify_toutiao_publish.py` | 结果验证 |
| **文档** | `docs_archive/CDP_PUBLISH_INTEGRATION.md` | 详细文档 |

---

## 🔑 关键参数

### API参数
```python
use_cdp: bool = True      # 是否使用CDP模式（默认True，推荐）
cdp_port: int = 9222      # CDP调试端口（默认9222）
```

### 方法签名
```python
# ToutiaoPublisher类
await publisher.initialize_browser(use_cdp=True, cdp_port=9222)

# API接口
POST /api/v1/content/toutiao/publish
POST /api/v1/content/toutiao/auto_publish
```

---

## ✅ 优势对比

| 特性 | CDP模式 | 标准模式 |
|------|---------|---------|
| 真实性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 稳定性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 兼容性 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 推荐度 | ✅ **强烈推荐** | 备选 |

---

## 🔧 配置项

### Edge浏览器路径
```python
# 默认路径（自动检测）
C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe
C:\Program Files\Microsoft\Edge\Application\msedge.exe
```

### 用户数据目录
```
CDP模式:   ./edge_profile_toutiao_cdp
标准模式:  ./edge_profile_toutiao
```

### CDP端口
```
默认: 9222
自定义: 在API调用时指定 cdp_port 参数
```

---

## 📊 工作流程

```
[1] 启动Edge浏览器 → taskkill关闭旧进程 → 启动带调试端口的Edge
[2] 连接浏览器 → Playwright connect_over_cdp → 获取context/page
[3] 检查登录 → URL检测 → 未登录则等待手动登录（120秒）
[4] 访问发布页 → 智能跳转 → 等待10秒 → 验证元素
[5] 填写发布 → 标题 → 正文 → 分类 → 点击发布 → 等待结果
```

---

## 💡 最佳实践

### 1. 始终使用CDP
```python
✅ use_cdp = True
❌ use_cdp = False  # 除非特殊情况
```

### 2. 前端超时设置
```typescript
// frontend/src/utils/api.ts
const REQUEST_TIMEOUT = 120000  // 120秒（头条登录需要30-60秒）
```

### 3. 复用浏览器
CDP会自动保存Cookie到配置文件，下次启动自动登录。

### 4. 查看日志和截图
```powershell
# 日志
Get-Content logs\*.log -Tail 50

# 截图
Get-ChildItem logs\cdp_*.png | Sort-Object LastWriteTime -Descending | Select-Object -First 1 | Invoke-Item
```

---

## ❓ 常见问题

### Q: CDP连接失败？
```powershell
taskkill /F /IM msedge.exe
Start-Sleep -Seconds 2
python scripts\quick_cdp_publish.py
```

### Q: 页面加载不完整？
- 增加等待时间：`await asyncio.sleep(10)` → `20`
- 检查网络
- 手动刷新后按回车

### Q: 找不到发布的文章？
```powershell
python scripts\verify_toutiao_publish.py
# 或手动访问：https://mp.toutiao.com/profile_v4/graphic/articles
```

---

## 🎯 快速测试流程

```powershell
# 1. 确保服务运行
python main.py

# 2. 运行CDP脚本
python scripts\quick_cdp_publish.py

# 3. 验证结果
python scripts\verify_toutiao_publish.py
```

---

## 📝 代码示例

### Python调用
```python
import requests

response = requests.post(
    "http://localhost:8000/api/v1/content/toutiao/publish",
    json={
        "account_id": 1,
        "title": "测试文章",
        "content": "测试内容...",
        "use_cdp": True,
        "cdp_port": 9222
    }
)
print(response.json())
```

### JavaScript调用
```javascript
const response = await fetch('/api/v1/content/toutiao/publish', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    account_id: 1,
    title: '测试文章',
    content: '测试内容...',
    use_cdp: true,
    cdp_port: 9222
  })
})
const result = await response.json()
```

---

## 🔗 相关链接

- [详细文档](./CDP_PUBLISH_INTEGRATION.md)
- [ToutiaoPublisher源码](../app/services/publish/toutiao_publisher.py)
- [API定义](../app/api/v1/endpoints.py#L453)
- [测试脚本](../scripts/test_cdp_auto_publish.py)

---

**记住：CDP模式是头条发布的最佳方案，强烈推荐使用！** 🎉
