# 📊 查看发布记录完整指南

**更新时间**: 2026-05-03  
**当前状态**: ✅ 已有 2 条成功发布记录

---

## 🎯 快速查看方式

### 方式一：使用命令行脚本（推荐）⭐

```powershell
python view_publish_records.py
```

**优点**:
- ✅ 直接查询数据库，数据最准确
- ✅ 显示详细信息（标题、内容长度、创建时间等）
- ✅ 无需启动前端服务

**示例输出**:
```
================================================================================
📊 Smart Toolbox - 发布记录查询
================================================================================

✅ 找到 2 条发布记录

ID    平台           状态           标题                                       创建时间                
------------------------------------------------------------------------------------------
2     toutiao      completed    无标题                                      2026-05-03 07:30:23 
1     toutiao      completed    90%的人都不知道！用DeepSeek写网络小说...     2026-05-03 07:08:35 

================================================================================

📝 详细记录信息:

[1] 记录 ID: 2
    任务ID: fa5d765c-e4ac-48f1-a5cc-781254f2116c
    主题: 如何用deepseek生成网络小说
    标题: N/A
    平台: toutiao
    分类: 科技
    状态: completed
    内容长度: 5056 字符
    创建时间: 2026-05-03 07:30:23

[2] 记录 ID: 1
    任务ID: 34ebcd3f-0f60-4ac5-8de5-b85191d54941
    主题: 如何用deepseek生成网络小说
    标题: 90%的人都不知道！用DeepSeek写网络小说，3天爆更10万字，月入过万不是梦！
    平台: toutiao
    分类: 科技
    状态: completed
    内容长度: 7138 字符
    创建时间: 2026-05-03 07:08:35
```

---

### 方式二：前端页面查看

访问发布记录页面：
```
http://localhost:3000/publish-records
```

**注意**: 当前前端页面查询的是 `publish_records` 表，该表目前为空。需要更新前端代码以查询 `content_tasks` 表。

---

### 方式三：直接查询数据库

#### 使用 Docker 命令

```powershell
# 查看所有发布记录
docker exec smart-toolbox-mysql mysql -u toolbox_user -pToolboxPass123 smart_toolbox -e "SELECT id, task_id, original_topic, article_title, target_platform, status, created_at FROM content_tasks ORDER BY created_at DESC;"

# 查看最近的 5 条记录
docker exec smart-toolbox-mysql mysql -u toolbox_user -pToolboxPass123 smart_toolbox -e "SELECT * FROM content_tasks ORDER BY created_at DESC LIMIT 5\G"
```

#### 使用 MySQL 客户端

```powershell
# 连接到数据库
docker exec -it smart-toolbox-mysql mysql -u toolbox_user -pToolboxPass123 smart_toolbox

# 执行查询
mysql> SELECT id, task_id, original_topic AS '主题', article_title AS '标题', target_platform AS '平台', status AS '状态', created_at AS '创建时间' FROM content_tasks ORDER BY created_at DESC;
```

---

### 方式四：后端 API 查询

#### 查看 Swagger UI

访问：http://localhost:8000/docs

但目前没有查询 `content_tasks` 的 API 端点，需要添加。

---

## 📋 当前发布记录详情

根据最新查询结果，系统中有 **2 条** 成功的头条文章发布记录：

### 记录 #1（最新）

| 字段 | 值 |
|------|-----|
| **记录 ID** | 2 |
| **任务 ID** | fa5d765c-e4ac-48f1-a5cc-781254f2116c |
| **主题** | 如何用deepseek生成网络小说 |
| **标题** | (未保存) |
| **平台** | 今日头条 (toutiao) |
| **分类** | 科技 |
| **状态** | ✅ completed (已完成) |
| **内容长度** | 5,056 字符 |
| **创建时间** | 2026-05-03 07:30:23 |

---

### 记录 #2

| 字段 | 值 |
|------|-----|
| **记录 ID** | 1 |
| **任务 ID** | 34ebcd3f-0f60-4ac5-8de5-b85191d54941 |
| **主题** | 如何用deepseek生成网络小说 |
| **标题** | 90%的人都不知道！用DeepSeek写网络小说，3天爆更10万字，月入过万不是梦！ |
| **平台** | 今日头条 (toutiao) |
| **分类** | 科技 |
| **状态** | ✅ completed (已完成) |
| **内容长度** | 7,138 字符 |
| **创建时间** | 2026-05-03 07:08:35 |

---

## 🔍 如何验证文章是否真的发布成功？

### 方法一：检查后端日志

在运行 `python main.py` 的终端中查找类似日志：

```
2026-05-03 15:30:23 | INFO | [步骤3/4] 开始发布文章...
2026-05-03 15:30:23 | INFO | ✅ [步骤3/4] 文章发布成功！
2026-05-03 15:30:23 | INFO | [步骤4/4] 保存发布记录...
2026-05-03 15:30:23 | INFO | ✅ [步骤4/4] 记录保存成功！
```

### 方法二：登录头条平台查看

1. 访问：https://mp.toutiao.com/
2. 登录你的头条账号（17739848781）
3. 进入"内容管理" → "图文"
4. 查看最近发布的文章

### 方法三：检查数据库中的文章内容

```powershell
docker exec smart-toolbox-mysql mysql -u toolbox_user -pToolboxPass123 smart_toolbox -e "SELECT id, article_title, LEFT(article_content, 100) AS '内容预览' FROM content_tasks WHERE id=1\G"
```

---

## 💡 常见问题

### Q1: 为什么前端页面显示没有记录？

**原因**: 前端页面查询的是 `publish_records` 表，但自动发布功能保存的是 `content_tasks` 表。这是两个不同的表：

- **content_tasks**: 内容创作任务表（存储生成的内容和发布状态）
- **publish_records**: 分发记录表（存储每个账号的发布详情）

**解决方案**: 
1. 使用命令行脚本查看（推荐）
2. 或直接查询数据库
3. 或等待前端页面更新以查询正确的表

---

### Q2: 如何查看文章的完整内容？

```powershell
# 查看指定记录的完整内容
docker exec smart-toolbox-mysql mysql -u toolbox_user -pToolboxPass123 smart_toolbox -e "SELECT article_content FROM content_tasks WHERE id=1\G"
```

或者使用 Python 脚本：

```python
from app.db.session import SessionLocal
from app.models import ContentTask

db = SessionLocal()
task = db.query(ContentTask).filter(ContentTask.id == 1).first()
print(f"标题: {task.article_title}")
print(f"内容:\n{task.article_content}")
db.close()
```

---

### Q3: 如何删除测试记录？

```powershell
# 删除指定记录
docker exec smart-toolbox-mysql mysql -u toolbox_user -pToolboxPass123 smart_toolbox -e "DELETE FROM content_tasks WHERE id IN (1, 2);"

# 清空所有记录
docker exec smart-toolbox-mysql mysql -u toolbox_user -pToolboxPass123 smart_toolbox -e "TRUNCATE TABLE content_tasks;"
```

⚠️ **警告**: 删除操作不可恢复，请谨慎操作！

---

### Q4: 发布记录保存在哪里？

**数据库表**: `content_tasks`

**表结构**:
```sql
CREATE TABLE content_tasks (
    id INTEGER PRIMARY KEY AUTO_INCREMENT,
    task_id VARCHAR(64) UNIQUE,          -- UUID
    original_topic TEXT,                  -- 原始主题
    target_platform VARCHAR(20),          -- 目标平台
    article_title VARCHAR(500),           -- 文章标题
    article_content TEXT,                 -- 文章内容
    article_category VARCHAR(100),        -- 文章分类
    tags JSON,                            -- 标签列表
    status VARCHAR(20),                   -- 状态: pending/processing/completed/failed
    created_at DATETIME                   -- 创建时间
);
```

---

## 🚀 后续优化建议

### 1. 添加 content_tasks 查询 API

在后端添加以下 API 端点：

```python
@router.get("/content/tasks")
def list_content_tasks(
    platform: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0),
    limit: int = Query(20),
    db: Session = Depends(get_db)
):
    """获取内容创作任务列表"""
    query = db.query(ContentTask)
    
    if platform:
        query = query.filter(ContentTask.target_platform == platform)
    if status:
        query = query.filter(ContentTask.status == status)
    
    total = query.count()
    tasks = query.order_by(ContentTask.created_at.desc()).offset(skip).limit(limit).all()
    
    return {"total": total, "tasks": tasks}
```

### 2. 更新前端页面

修改 `frontend/src/views/PublishRecords.vue`，使其查询 `content_tasks` 表而不是 `publish_records` 表。

### 3. 关联两个表

在自动发布成功后，同时创建 `publish_records` 记录：

```python
# 保存 content_task
content_task = ContentTask(...)
db.add(content_task)
db.commit()

# 创建 publish_record
publish_record = PublishRecord(
    account_id=account_id,
    content_task_id=content_task.id,
    publish_status="published",
    publish_time=datetime.utcnow(),
    platform_url=f"https://www.toutiao.com/article/{article_id}"
)
db.add(publish_record)
db.commit()
```

---

## 📌 总结

### ✅ 推荐的查看方式

1. **快速查看**: 使用 `python view_publish_records.py` 脚本
2. **详细查看**: 直接查询数据库
3. **可视化查看**: 等待前端页面更新

### 📊 当前状态

- ✅ 共有 **2 条** 发布记录
- ✅ 平台：**今日头条**
- ✅ 状态：**全部成功** (completed)
- ✅ 总内容量：**12,194 字符**

### 🎯 下一步

1. 登录头条平台验证文章是否可见
2. 检查文章的实际浏览量和互动数据
3. 考虑添加更多平台的发布记录查询

---

**文档版本**: 1.0  
**最后更新**: 2026-05-03  
**维护者**: AI Assistant
