# 智能图像生成配置指南

## 🎯 核心设计理念

**系统会根据后台配置的默认提供商自动生成图像**，实现真正的智能化运营。

---

## ✅ 已完成的关键修复

### 1. **ImageGenerator 传入数据库会话**

**修复前**：
```python
image_gen = ImageGenerator()  # ❌ 没有数据库会话，无法读取配置
```

**修复后**：
```python
from app.db.session import SessionLocal
db = SessionLocal()
image_gen = ImageGenerator(db=db)  # ✅ 传入数据库会话，能读取配置
```

**效果**：
- ✅ 自动读取数据库中配置的默认提供商
- ✅ 支持动态切换提供商（硅基流动/魔搭社区/阿里百炼）
- ✅ 无需修改代码，只需在后台配置即可

---

### 2. **设置魔搭社区为默认提供商**

**数据库配置状态**：
```
ID=5, Provider=modelscope, Name=魔搭社区-图像生成, Default=True, API Key=ms-bc3203b...
ID=3, Provider=siliconflow, Name=硅基流动-图像生成, Default=False, API Key=sk-fqwnora...
```

**当前默认**：魔搭社区 (modelscope)

---

### 3. **前端启用AI封面图生成**

**修复前**：
```javascript
auto_generate_cover: false  // ❌ 关闭AI生成
```

**修复后**：
```javascript
auto_generate_cover: true  // ✅ 启用AI生成（使用数据库配置的默认提供商）
```

---

## 🔧 如何切换图像生成提供商

### 方法1：通过前端界面（推荐）⭐

1. 访问：http://localhost:3003/llm-configs
2. 找到"图像生成"类型的配置
3. 点击编辑按钮
4. 将想要的提供商设置为"默认配置"
5. 保存

**支持的提供商**：
- ✅ 魔搭社区 (modelscope) - 当前默认
- ✅ 硅基流动 (siliconflow)
- ✅ 阿里百炼 (dashscope)

---

### 方法2：通过SQL直接修改

```sql
-- 将魔搭社区设置为默认
UPDATE llm_configs SET is_default = TRUE WHERE id = 5;

-- 将其他提供商设置为非默认
UPDATE llm_configs SET is_default = FALSE WHERE function_type = 'image_generation' AND id != 5;
```

---

## 📊 工作流程

```
用户发起发布请求 (auto_generate_cover=true)
    ↓
ToutiaoPublisher.publish_article()
    ↓
创建 ImageGenerator(db=db)  ← ★★★ 关键：传入数据库会话
    ↓
ImageGenerator._get_default_provider()
    ↓
查询数据库：SELECT * FROM llm_configs 
             WHERE function_type='image_generation' 
             AND is_default=True
    ↓
获取默认提供商（例如：modelscope）
    ↓
调用对应的生成器：_generate_with_modelscope()
    ↓
从数据库读取API配置：api_key, base_url, model_name
    ↓
调用第三方API生成图像
    ↓
返回图像路径
    ↓
上传到头条
```

---

## 🎨 不同提供商的特点

| 提供商 | 模型 | 速度 | 质量 | 费用 | 适用场景 |
|--------|------|------|------|------|----------|
| **魔搭社区** | FLUX.1-schnell | ⚡⚡⚡ 快 | ⭐⭐⭐⭐ 高 | 💰 免费额度+付费 | 快速生成，中文支持好 |
| **硅基流动** | Z-Image-Turbo | ⚡⚡⚡⚡ 很快 | ⭐⭐⭐ 中 | 💰💰 按量付费 | 高速生成，成本低 |
| **阿里百炼** | wanx2.1-t2i-turbo | ⚡⚡ 中等 | ⭐⭐⭐⭐⭐ 很高 | 💰💰💰 较贵 | 高质量封面图 |

---

## 🔍 验证配置是否生效

### 1. 查看日志

发布文章时，日志应该显示：

```
INFO | app.services.content.image_generator:_get_default_provider:51 - 
✅ 使用数据库配置的图像提供商: modelscope

INFO | app.services.publish.toutiao_publisher:publish_article:674 - 
   开始AI生成封面图...
   提示词: xxx, 科技, 高质量专业摄影...
   默认提供商: modelscope

INFO | app.services.content.image_generator:_generate_with_modelscope:600 - 
使用魔搭社区图像模型: black-forest-labs/FLUX.1-schnell
```

### 2. 测试脚本

```bash
python scripts/simple_test_modelscope.py
```

### 3. 实际发布

在前端发布一篇文章，观察：
- ✅ 是否成功生成封面图
- ✅ 日志中显示的提供商是否正确
- ✅ 头条后台是否显示了自定义封面

---

## 🆘 常见问题

### Q1: 为什么日志显示使用的是硅基流动，但我配置的是魔搭社区？

**A**: 检查数据库中是否有多个 `is_default=True` 的配置。应该只有一个默认配置。

```sql
-- 检查默认配置数量
SELECT COUNT(*) FROM llm_configs 
WHERE function_type = 'image_generation' AND is_default = TRUE;

-- 应该返回 1，如果大于1，需要修正
```

### Q2: 如何临时切换到其他提供商测试？

**A**: 有两种方式：

**方式1**：修改数据库配置
```sql
UPDATE llm_configs SET is_default = TRUE WHERE id = 3;  -- 切换到硅基流动
UPDATE llm_configs SET is_default = FALSE WHERE id = 5;
```

**方式2**：代码中显式指定提供商
```python
result = await image_gen.generate_image(
    prompt=prompt,
    aspect_ratio="16:9",
    provider="siliconflow"  # 显式指定
)
```

### Q3: API Key 失效了怎么办？

**A**: 
1. 登录对应提供商的官网
2. 重新生成API Key
3. 在前端LLM配置页面更新API Key
4. 或者通过SQL更新：
```sql
UPDATE llm_configs 
SET api_key = '新的API Key' 
WHERE id = 5;
```

### Q4: 生成的图像质量不满意怎么办？

**A**: 可以调整：
1. **更换提供商**：尝试不同的提供商（魔搭/硅基/阿里）
2. **优化提示词**：修改 `toutiao_publisher.py` 中的 prompt
3. **调整模型**：在LLM配置页面更换图像模型

---

## 📝 最佳实践

### 1. **定期检查API余额**

- 魔搭社区：https://modelscope.cn/my/myaccesstoken
- 硅基流动：https://cloud.siliconflow.cn/account/billing
- 阿里百炼：https://dashscope.console.aliyun.com/overview

### 2. **监控生成成功率**

在数据库中查看最后测试结果：

```sql
SELECT 
    name,
    provider,
    last_test_status,
    last_test_time,
    last_test_error
FROM llm_configs
WHERE function_type = 'image_generation';
```

### 3. **配置多个提供商作为备份**

建议配置2-3个提供商，当主提供商出现问题时可以快速切换。

---

## 🚀 智能化运营的意义

通过这套配置系统，你可以实现：

1. **全自动内容生产**：
   - AI自动生成标题
   - AI自动生成正文
   - AI自动生成封面图
   - AI自动生成配图

2. **灵活的内容策略**：
   - 根据成本选择提供商
   - 根据质量需求选择模型
   - A/B测试不同提供商的效果

3. **降低运营成本**：
   - 无需设计师制作封面
   - 无需手动上传图片
   - 24小时不间断运行

4. **规模化内容矩阵**：
   - 同时管理多个账号
   - 批量生成和发布内容
   - 快速试错和优化

---

## 📚 相关文档

- [魔搭社区异步API指南](./MODELSCOPE_ASYNC_API_GUIDE.md)
- [头条发布完整流程](./TOUTIAO_PUBLISH_WORKFLOW.md)
- [LLM配置管理界面](../frontend/src/views/LLMConfig.vue)
