# 🎬 Phase 4 功能演示指南

## 📋 目录
- [快速体验](#快速体验)
- [详细操作步骤](#详细操作步骤)
- [API 测试示例](#api-测试示例)
- [常见问题](#常见问题)

---

## 🚀 快速体验

### 前提条件
✅ 后端服务运行中（端口 8000）  
✅ 前端服务运行中（端口 3002）  

### 5分钟快速上手

1. **打开浏览器**
   ```
   http://localhost:3002/autonomous-agent-monitor
   ```

2. **注册智能体**（如果还没有）
   - 点击"注册智能体"按钮
   - 选择智能体类型（建议至少注册 research 和 content_generation）
   - 点击"注册"

3. **分解任务**
   - 在"任务规划"面板输入：`创作一篇关于AI的文章`
   - 设置优先级：7
   - 点击"分解目标"

4. **执行任务**
   - 点击"🚀 执行所有任务"
   - 观察每个任务的执行状态变化

5. **查看结果**
   - 滚动到页面底部
   - 查看"任务执行历史"表格
   - 查看"执行统计"面板

---

## 📖 详细操作步骤

### 场景 1: 完整的内容创作工作流

#### 步骤 1: 准备智能体
确保已注册以下智能体：
- ✅ research（研究智能体）
- ✅ planning（规划智能体）
- ✅ content_generation（内容生成智能体）
- ✅ compliance_check（合规检查智能体）

#### 步骤 2: 输入目标
在"任务规划"面板中：
```
目标描述: 创作一篇关于人工智能在自媒体运营中应用的文章并发布到头条
优先级: 8
```

#### 步骤 3: 分解目标
点击"分解目标"按钮

系统会分解为：
```
步骤 1: topic_research (research)
步骤 2: outline_generation (planning)
步骤 3: content_writing (content_generation)
步骤 4: compliance_check (compliance_check)
步骤 5: image_generation (image_generation)
步骤 6: publish (distribution)
```

#### 步骤 4: 执行任务

**方式 A: 批量执行**
- 点击"🚀 执行所有任务"
- 系统会按顺序执行所有任务
- 每个任务之间间隔 0.5 秒

**方式 B: 单个执行**
- 点击每个任务的"执行"按钮
- 可以控制执行顺序
- 适合调试和测试

#### 步骤 5: 监控进度

观察每个任务卡片的状态变化：
```
待执行 → 执行中... → 已完成
```

执行完成后：
- 显示"查看结果"按钮
- 结果以 JSON 格式展示在卡片中

#### 步骤 6: 查看统计

滚动到页面底部：

**左侧：执行历史**
- 查看所有任务的执行记录
- 包括任务ID、类型、状态、耗时、时间

**右侧：执行统计**
- 每种智能体的成功率
- 总任务数、成功数、失败数
- 彩色进度条直观展示

---

### 场景 2: 单独测试某个智能体

#### 测试研究智能体

1. **分解一个简单目标**
   ```
   目标: 研究AI相关热点话题
   ```

2. **只执行第一个任务**
   - 找到 research 类型的任务
   - 点击"执行"按钮

3. **查看结果**
   ```json
   {
     "task_type": "topic_research",
     "topics": [
       {
         "title": "AI在科技领域的最新应用",
         "heat_score": 95,
         "source": "toutiao",
         "trend": "rising"
       }
     ],
     "total_found": 3
   }
   ```

#### 测试内容生成智能体

1. **分解目标**
   ```
   目标: 写一篇关于自媒体的文章
   ```

2. **执行 content_generation 任务**

3. **查看生成的内容**
   ```json
   {
     "title": "自媒体运营完全指南",
     "content": "这是一篇关于自媒体的文章...\n\n## 引言...",
     "word_count": 1200,
     "style": "professional"
   }
   ```

---

### 场景 3: 监控和分析

#### 查看执行历史

1. 滚动到"任务执行历史"面板
2. 点击"刷新"获取最新数据
3. 分析执行情况：
   - 哪些任务执行最快？
   - 是否有失败的任务？
   - 平均耗时是多少？

#### 查看执行统计

1. 查看右侧"执行统计"面板
2. 观察各智能体的成功率：
   - 🟢 绿色（≥90%）：优秀
   - 🟡 橙色（≥70%）：良好
   - 🔴 红色（<70%）：需要优化

3. 根据统计数据：
   - 识别性能瓶颈
   - 优化低成功率的智能体
   - 调整任务参数

---

## 🔧 API 测试示例

### 1. 执行研究任务

```bash
curl -X POST http://localhost:8000/api/v1/agents/autonomous/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "research",
    "task_params": {
      "task_type": "topic_research",
      "platform": "toutiao",
      "category": "科技",
      "keyword": "AI"
    },
    "task_id": "demo_001"
  }'
```

**预期响应：**
```json
{
  "status": "success",
  "agent_type": "research",
  "task_id": "demo_001",
  "duration": 0.001,
  "data": {
    "task_type": "topic_research",
    "topics": [...],
    "total_found": 3
  }
}
```

### 2. 执行内容生成任务

```bash
curl -X POST http://localhost:8000/api/v1/agents/autonomous/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "content_generation",
    "task_params": {
      "topic": "人工智能",
      "style": "professional",
      "length": "medium"
    }
  }'
```

### 3. 执行合规检查任务

```bash
curl -X POST http://localhost:8000/api/v1/agents/autonomous/execute \
  -H "Content-Type: application/json" \
  -d '{
    "agent_type": "compliance_check",
    "task_params": {
      "content": "这是一篇测试文章的内容",
      "platform": "toutiao"
    }
  }'
```

### 4. 查看执行历史

```bash
curl http://localhost:8000/api/v1/agents/autonomous/execution/history?limit=10
```

**预期响应：**
```json
{
  "status": "success",
  "count": 3,
  "history": [
    {
      "task_id": "demo_001",
      "agent_type": "research",
      "status": "success",
      "duration": 0.001,
      "start_time": "2026-05-18T15:30:00",
      "end_time": "2026-05-18T15:30:00"
    }
  ]
}
```

### 5. 查看执行统计

```bash
curl http://localhost:8000/api/v1/agents/autonomous/execution/stats
```

**预期响应：**
```json
{
  "status": "success",
  "stats": {
    "research": {
      "total_tasks": 5,
      "success_count": 5,
      "failed_count": 0,
      "success_rate": 1.0
    },
    "content_generation": {
      "total_tasks": 3,
      "success_count": 3,
      "failed_count": 0,
      "success_rate": 1.0
    }
  }
}
```

### 6. 查看已注册的执行器

```bash
curl http://localhost:8000/api/v1/agents/autonomous/execution/executors
```

**预期响应：**
```json
{
  "status": "success",
  "count": 7,
  "executors": {
    "research": {"agent_type": "research", "registered": true},
    "content_generation": {"agent_type": "content_generation", "registered": true},
    "compliance_check": {"agent_type": "compliance_check", "registered": true},
    "image_generation": {"agent_type": "image_generation", "registered": true},
    "distribution": {"agent_type": "distribution", "registered": true},
    "planning": {"agent_type": "planning", "registered": true},
    "nurturing": {"agent_type": "nurturing", "registered": true}
  }
}
```

---

## 💻 Python 代码示例

### 基础用法

```python
import asyncio
from app.services.agents.task_execution_engine import execution_engine

async def demo():
    # 执行研究任务
    result = await execution_engine.execute_task(
        agent_type="research",
        task_params={
            "task_type": "topic_research",
            "platform": "toutiao",
            "keyword": "AI"
        }
    )
    
    print(f"状态: {result['status']}")
    print(f"耗时: {result['duration']}秒")
    print(f"结果: {result['data']}")

asyncio.run(demo())
```

### 批量执行

```python
async def batch_demo():
    tasks = [
        ("research", {"task_type": "topic_research", "keyword": "AI"}),
        ("content_generation", {"topic": "AI", "style": "professional"}),
        ("compliance_check", {"content": "测试内容"})
    ]
    
    results = []
    for agent_type, params in tasks:
        result = await execution_engine.execute_task(
            agent_type=agent_type,
            task_params=params
        )
        results.append(result)
        print(f"{agent_type}: {result['status']}")
    
    return results

results = asyncio.run(batch_demo())
```

### 查看统计

```python
from app.services.agents.task_execution_engine import execution_engine

# 获取执行历史
history = execution_engine.get_task_history(limit=10)
print(f"最近 {len(history)} 条执行记录:")
for record in history:
    print(f"  - {record['task_id']}: {record['status']}")

# 获取统计信息
stats = execution_engine.get_executor_stats()
print("\n执行统计:")
for agent_type, stat in stats.items():
    print(f"  {agent_type}: 成功率 {stat['success_rate']*100:.1f}%")
```

---

## ❓ 常见问题

### Q1: 为什么返回的是模拟数据？

**A**: 当前版本使用模拟数据进行演示。要获取真实数据，需要：
1. 集成真实的热点 API
2. 接入 LLM 服务（如 GPT、Claude）
3. 连接图片生成服务
4. 对接现有的发布模块

### Q2: 任务执行失败怎么办？

**A**: 
1. 检查错误消息
2. 查看后端日志（`logs/` 目录）
3. 确认智能体已注册
4. 验证任务参数是否正确

### Q3: 如何添加新的智能体类型？

**A**: 
1. 创建新的执行器类，继承 `TaskExecutor`
2. 实现 `execute()` 方法
3. 在 `executor_initializer.py` 中注册
4. 重启后端服务

### Q4: 前端界面不显示执行历史？

**A**: 
1. 确认后端服务正常运行
2. 检查浏览器控制台是否有错误
3. 点击"刷新"按钮
4. 先执行一些任务再查看历史

### Q5: 如何调整任务执行速度？

**A**: 修改前端代码中的延迟时间：
```javascript
// 在 executeAllTasks 函数中
await new Promise(resolve => setTimeout(resolve, 500)) // 改为其他值
```

### Q6: 执行统计不准确？

**A**: 
1. 点击"刷新"按钮更新数据
2. 统计数据基于内存，重启后会清空
3. 确保任务已成功执行

---

## 🎯 最佳实践

### 1. 任务分解技巧
- 目标描述要具体明确
- 优先级根据紧急程度设置
- 复杂目标可以分多次分解

### 2. 执行策略
- 首次使用建议单个执行，观察效果
- 熟悉后可以批量执行提高效率
- 重要任务建议单独执行并检查结果

### 3. 监控建议
- 定期查看执行历史
- 关注成功率低的智能体
- 分析耗时较长的任务

### 4. 性能优化
- 避免同时执行过多任务
- 合理设置任务间隔时间
- 定期清理执行历史（未来版本支持）

---

## 📊 演示检查清单

使用此清单确保所有功能正常：

- [ ] 能够访问监控系统页面
- [ ] 能够注册智能体
- [ ] 能够分解目标
- [ ] 能够执行单个任务
- [ ] 能够批量执行任务
- [ ] 能够查看执行状态变化
- [ ] 能够查看执行结果
- [ ] 能够查看执行历史
- [ ] 能够查看执行统计
- [ ] 能够通过 API 调用
- [ ] 所有智能体类型都能正常工作

---

## 🎉 开始体验吧！

现在你已经了解了 Phase 4 的所有功能，开始体验智能体任务执行的魅力吧！

**访问地址**: http://localhost:3002/autonomous-agent-monitor

祝你使用愉快！🚀
