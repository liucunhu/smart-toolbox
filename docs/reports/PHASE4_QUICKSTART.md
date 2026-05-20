# Phase 4 快速开始指南

## 🚀 5分钟上手任务执行引擎

### 前置条件
- ✅ 后端服务已启动 (`python start_server.py`)
- ✅ 数据库连接正常

---

## 步骤 1: 验证执行器已注册

访问 API 查看已注册的智能体类型：

```bash
curl http://localhost:8000/api/v1/agents/autonomous/execution/executors
```

你应该看到：
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

## 步骤 2: 执行第一个任务

### 示例 1: 研究智能体 - 选题研究

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
    }
  }'
```

响应示例：
```json
{
  "status": "success",
  "agent_type": "research",
  "task_id": "test_001",
  "duration": 0.001,
  "data": {
    "task_type": "topic_research",
    "topics": [
      {
        "title": "AI在科技领域的最新应用",
        "heat_score": 95,
        "source": "toutiao",
        "trend": "rising"
      },
      ...
    ],
    "total_found": 3
  }
}
```

### 示例 2: 内容生成智能体

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

### 示例 3: 合规检查智能体

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

---

## 步骤 3: 查看执行历史

```bash
curl http://localhost:8000/api/v1/agents/autonomous/execution/history?limit=5
```

响应：
```json
{
  "status": "success",
  "count": 3,
  "history": [
    {
      "task_id": "test_001",
      "agent_type": "research",
      "status": "success",
      "duration": 0.001,
      "start_time": "2026-05-18T15:30:00",
      "end_time": "2026-05-18T15:30:00"
    },
    ...
  ]
}
```

---

## 步骤 4: 查看执行统计

```bash
curl http://localhost:8000/api/v1/agents/autonomous/execution/stats
```

响应：
```json
{
  "status": "success",
  "stats": {
    "research": {
      "total_tasks": 1,
      "success_count": 1,
      "failed_count": 0,
      "success_rate": 1.0
    },
    "content_generation": {
      "total_tasks": 1,
      "success_count": 1,
      "failed_count": 0,
      "success_rate": 1.0
    },
    ...
  }
}
```

---

## 🐍 Python 代码调用示例

### 基础用法

```python
import asyncio
from app.services.agents.task_execution_engine import execution_engine

async def main():
    # 执行研究任务
    result = await execution_engine.execute_task(
        agent_type="research",
        task_params={
            "task_type": "topic_research",
            "platform": "toutiao",
            "category": "科技"
        }
    )
    
    print(f"状态: {result['status']}")
    print(f"耗时: {result['duration']}秒")
    print(f"结果: {result['data']}")

asyncio.run(main())
```

### 批量执行

```python
async def batch_execute():
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
    
    return results

results = asyncio.run(batch_execute())
for r in results:
    print(f"{r['agent_type']}: {r['status']}")
```

---

## 📊 所有可用的任务类型

### 1. Research (研究智能体)

```json
{
  "agent_type": "research",
  "task_params": {
    "task_type": "topic_research",  // 或 "trend_analysis", "competitor_analysis"
    "platform": "toutiao",
    "category": "科技",
    "keyword": "AI"
  }
}
```

### 2. Content Generation (内容生成)

```json
{
  "agent_type": "content_generation",
  "task_params": {
    "topic": "人工智能",
    "style": "professional",  // 或 "casual", "technical"
    "length": "medium"  // 或 "short", "long"
  }
}
```

### 3. Compliance Check (合规检查)

```json
{
  "agent_type": "compliance_check",
  "task_params": {
    "content": "文章内容...",
    "platform": "toutiao"
  }
}
```

### 4. Image Generation (图片生成)

```json
{
  "agent_type": "image_generation",
  "task_params": {
    "prompt": "AI科技风格封面图",
    "style": "modern",
    "size": "1200x630"
  }
}
```

### 5. Distribution (分发)

```json
{
  "agent_type": "distribution",
  "task_params": {
    "platform": "toutiao",
    "title": "文章标题",
    "content": "文章内容...",
    "account_id": 123
  }
}
```

### 6. Planning (规划)

```json
{
  "agent_type": "planning",
  "task_params": {
    "topic": "人工智能发展趋势"
  }
}
```

### 7. Nurturing (养号)

```json
{
  "agent_type": "nurturing",
  "task_params": {
    "platform": "douyin",
    "action_type": "browse",  // 或 "like", "comment", "follow"
    "account_id": 123
  }
}
```

---

## 🔧 故障排查

### 问题 1: 执行器未注册

**症状**: 返回错误 `"未找到智能体类型 'xxx' 的执行器"`

**解决**: 
1. 检查后端服务是否正常启动
2. 查看启动日志中是否有 `"✅ 智能体任务执行器初始化成功"`
3. 重启后端服务

### 问题 2: 任务执行失败

**症状**: 返回 `"status": "failed"`

**解决**:
1. 检查 `task_params` 参数是否正确
2. 查看详细错误信息 `result['error']`
3. 查看后端日志获取更多信息

### 问题 3: 返回的是模拟数据

**说明**: 这是预期行为！当前版本使用模拟数据进行演示。

**后续**: 需要集成真实服务（LLM、热点API等）才能获取真实数据。

---

## 📖 更多资源

- 📄 [完整实现报告](PHASE4_COMPLETION_REPORT.md)
- 📚 [详细实现总结](PHASE4_IMPLEMENTATION_SUMMARY.md)
- 🎯 [用户使用指南](AUTONOMOUS_AGENT_USER_GUIDE.md)
- 🧪 [测试脚本](test_phase4_execution.py)

---

## 💡 提示

1. **所有任务都是异步的** - 使用 `await` 调用
2. **任务ID可选** - 如果不提供，系统会自动生成
3. **执行历史有限制** - 默认保留最近50条记录
4. **模拟数据** - 当前返回的是模拟数据，用于演示功能

---

**祝你使用愉快！** 🎉

如有问题，请查看日志文件：`logs/` 目录
