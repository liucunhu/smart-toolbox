# 魔搭社区API配置指南

## ⚠️ 问题说明

如果你看到以下错误日志：

```
ERROR | app.services.content.image_generator:_generate_with_modelscope:622 - 
魔搭社区图像任务创建失败: {"errors":{"message":"submit failed with code: 40212"}}
```

这是因为**没有配置魔搭社区的API Key**，但系统默认启用了AI封面图生成功能。

---

## 🎯 解决方案（3选1）

### 方案1：关闭自动封面生成（推荐，最简单）⭐

**适用场景**：不需要AI生成封面图，使用头条默认封面或手动上传

**已完成**：前端代码已修改为 `auto_generate_cover: false`

**效果**：
- ✅ 不再调用魔搭社区API
- ✅ 发布速度更快
- ✅ 避免API配置问题

---

### 方案2：配置魔搭社区API Key

**适用场景**：需要使用AI自动生成高质量封面图

#### 步骤1：获取API Key

1. 访问 [魔搭社区](https://modelscope.cn/)
2. 注册/登录账号
3. 进入"个人中心" → "API密钥"
4. 复制你的API Key（格式：`ms-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`）

#### 步骤2：在数据库中配置

**方法A：通过前端界面配置（推荐）**

1. 访问：http://localhost:3003/llm-configs
2. 点击"新增配置"
3. 填写表单：
   ```
   提供商: 魔搭社区 (modelscope)
   功能类型: 图像生成 (image_generation)
   配置名称: 魔搭社区-图像生成
   API密钥: ms-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
   基础URL: https://api-inference.modelscope.cn/v1
   模型名称: black-forest-labs/FLUX.1-schnell
   图像模型名称: black-forest-labs/FLUX.1-schnell
   超时时间: 180
   是否默认: ✅ 是
   是否启用: ✅ 是
   优先级: 10
   描述: 魔搭社区FLUX.1-schnell用于生成头条封面图
   ```
4. 点击"确定"保存

**方法B：通过SQL直接插入**

```sql
INSERT INTO llm_configs (
    provider,
    function_type,
    name,
    api_key,
    base_url,
    model_name,
    image_model_name,
    timeout,
    is_default,
    is_active,
    priority,
    description
) VALUES (
    'modelscope',
    'image_generation',
    '魔搭社区-图像生成',
    'ms-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx',  -- 替换为你的API Key
    'https://api-inference.modelscope.cn/v1',
    'Qwen/Qwen2.5-72B-Instruct',
    'black-forest-labs/FLUX.1-schnell',
    180,
    TRUE,
    TRUE,
    10,
    '魔搭社区FLUX.1-schnell用于生成头条封面图'
);
```

#### 步骤3：重启后端服务

```bash
# 停止服务
Ctrl+C

# 重新启动
python main.py
```

#### 步骤4：测试配置

```bash
python scripts/simple_test_modelscope.py
```

如果看到类似输出，说明配置成功：

```
✅ 任务创建成功! Task ID: xxxxx
⏳ 等待任务完成...
✅ 图像生成成功!
📸 图片路径: output/images/modelscope_xxx.png
```

---

### 方案3：修改后端默认行为

**适用场景**：希望默认不生成封面图，但可以手动开启

修改 `app/api/v1/endpoints.py`：

```python
# 修改前
auto_generate_cover: bool = True

# 修改后
auto_generate_cover: bool = False  # 默认关闭
```

然后前端可以根据需要显式传递 `auto_generate_cover: true`。

---

## 🔍 错误码说明

| 错误码 | 含义 | 解决方法 |
|--------|------|----------|
| 40212 | API认证失败 | 检查API Key是否正确配置 |
| 400 | 请求参数错误 | 检查模型名称和参数格式 |
| 429 | API限流 | 降低调用频率 |
| 500 | 服务器内部错误 | 稍后重试 |

---

## 📝 注意事项

1. **魔搭社区使用异步API**：
   - 必须设置 `X-ModelScope-Async-Mode: true` 头
   - 先创建任务，然后轮询获取结果
   - 参考：`docs_archive/MODELSCOPE_ASYNC_API_GUIDE.md`

2. **支持的图像模型**：
   - ✅ `black-forest-labs/FLUX.1-schnell`（推荐，快速）
   - ✅ `Qwen/Qwen-Image`（通义千问图像生成）
   - ❌ 不是所有模型都支持API-Inference

3. **费用说明**：
   - 魔搭社区提供免费额度
   - 超出后按调用次数收费
   - 建议在个人中心查看使用情况

4. **网络要求**：
   - 需要能够访问 `https://api-inference.modelscope.cn`
   - 国内访问速度较快
   - 无需代理

---

## 🆘 常见问题

### Q1: 为什么默认使用魔搭社区？

**A**: 因为魔搭社区是国内服务，访问速度快，且提供中文支持。

### Q2: 可以切换到其他提供商吗？

**A**: 可以！支持的提供商：
- 硅基流动 (siliconflow)
- 阿里百炼 (dashscope)
- 魔搭社区 (modelscope)

在前端LLM配置页面切换默认提供商即可。

### Q3: 不生成封面图会影响发布吗？

**A**: 不会！头条会使用默认封面，或者你可以手动上传封面图。

### Q4: 如何验证配置是否生效？

**A**: 
1. 查看日志：应该看到 `✅ 使用数据库配置的图像提供商: modelscope`
2. 测试脚本：运行 `python scripts/simple_test_modelscope.py`
3. 实际发布：发布文章时观察是否成功生成封面图

---

## 📚 相关文档

- [魔搭社区异步API指南](../docs_archive/MODELSCOPE_ASYNC_API_GUIDE.md)
- [头条发布完整流程](../docs_archive/TOUTIAO_PUBLISH_WORKFLOW.md)
- [LLM配置管理](../frontend/src/views/LLMConfig.vue)
