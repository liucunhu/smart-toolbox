# API用量监控功能说明

## 📊 功能概述

新增了API用量监控功能，可以实时查看各AI提供商的API使用情况和余额信息。

---

## ✨ 核心特性

### 1. **多提供商支持**
- ✅ **硅基流动 (SiliconFlow)**: 实时查询账户余额
- ✅ **魔搭社区 (ModelScope)**: 验证API Key有效性 + 官网链接
- ✅ **阿里百炼 (DashScope)**: 验证API Key有效性 + 官网链接

### 2. **实时监控**
- 一键刷新所有提供商用量
- 单独刷新指定提供商
- 状态可视化（成功/警告/失败）

### 3. **快速访问**
- 直接跳转到各提供商官网
- 查看详细用量统计
- 管理API密钥

---

## 🔧 技术实现

### 后端API

**文件**: `app/services/system/api_usage_service.py`

```python
class APIUsageService:
    # 硅基流动 - 查询真实余额
    async def get_siliconflow_balance(api_key: str) -> Dict
    
    # 魔搭社区 - 验证Key有效性
    async def get_modelscope_usage(api_key: str) -> Dict
    
    # 阿里百炼 - 验证Key有效性
    async def get_dashscope_usage(api_key: str) -> Dict
```

**API端点**: `GET /api/v1/api-usage/{provider}`

```python
@router.get("/api-usage/{provider}", summary="查询API用量")
async def get_api_usage(provider: str, db: Session = Depends(get_db))
```

### 前端页面

**文件**: `frontend/src/views/APIUsage.vue`

**功能**:
- 表格展示所有提供商状态
- 实时刷新按钮
- 官网跳转链接
- 状态标签（成功/警告/失败）

---

## 📱 使用方式

### 1. 访问页面

启动服务后，访问：
```
http://localhost:3003/api-usage
```

或在左侧菜单：**系统配置 → API用量监控**

### 2. 查看用量

页面会自动加载所有已配置的提供商：

| 提供商 | 状态 | 余额/信息 | 操作 |
|--------|------|-----------|------|
| 硅基流动 | ✅ 成功 | 账户余额: 50.00元 | [刷新] [官网] |
| 魔搭社区 | ℹ️ 信息 | API Key有效，请前往官网查看 | [刷新] [官网] |
| 阿里百炼 | ℹ️ 信息 | API Key有效，请前往官网查看 | [刷新] [官网] |

### 3. 刷新数据

- **刷新全部**: 点击顶部"刷新全部"按钮
- **单个刷新**: 点击每行的"刷新"按钮

### 4. 访问官网

点击"官网"按钮，在新窗口打开对应提供商的管理控制台：
- 硅基流动: https://cloud.siliconflow.cn/account/billing
- 魔搭社区: https://modelscope.cn/my/myaccesstoken
- 阿里百炼: https://dashscope.console.aliyun.com/overview

---

## 🔍 各提供商详情

### 硅基流动 (SiliconFlow)

**功能**: 
- ✅ 实时查询账户余额
- ✅ 显示具体金额（元）

**API响应示例**:
```json
{
  "status": "success",
  "provider": "siliconflow",
  "config_name": "硅基流动-图像生成",
  "balance": 50.00,
  "currency": "CNY",
  "message": "账户余额: 50.00 元"
}
```

**特点**:
- 唯一支持实时余额查询的提供商
- 数据准确可靠
- 建议定期检查余额，避免欠费

---

### 魔搭社区 (ModelScope)

**功能**: 
- ✅ 验证API Key是否有效
- ✅ 提供官网链接跳转
- ❌ 无法通过API查询具体用量

**API响应示例**:
```json
{
  "status": "info",
  "provider": "modelscope",
  "config_name": "魔搭社区-图像生成",
  "api_key_valid": true,
  "message": "API Key有效，请前往官网查看详细用量",
  "dashboard_url": "https://modelscope.cn/my/myaccesstoken"
}
```

**查看用量步骤**:
1. 点击"官网"按钮
2. 登录魔搭社区
3. 进入"个人中心" → "我的令牌"
4. 查看使用统计和配额

---

### 阿里百炼 (DashScope)

**功能**: 
- ✅ 验证API Key是否有效
- ✅ 提供官网链接跳转
- ❌ 无法通过API查询具体用量

**API响应示例**:
```json
{
  "status": "info",
  "provider": "dashscope",
  "config_name": "阿里百炼-图像生成",
  "api_key_valid": true,
  "message": "API Key有效，请前往控制台查看详细用量",
  "dashboard_url": "https://dashscope.console.aliyun.com/overview"
}
```

**查看用量步骤**:
1. 点击"官网"按钮
2. 登录阿里云控制台
3. 进入"百炼"控制台
4. 查看"用量统计"和"费用中心"

---

## 💡 最佳实践

### 1. 日常监控

**建议频率**: 每天检查一次

**检查要点**:
- 硅基流动余额是否充足
- 其他提供商API Key是否有效
- 是否有异常使用量

### 2. 余额预警

**硅基流动**: 
- 建议设置余额提醒（官网支持）
- 当余额低于10元时及时充值
- 避免因余额不足导致服务中断

**魔搭社区/阿里百炼**:
- 每周登录官网查看用量
- 关注配额使用情况
- 注意免费额度到期时间

### 3. 故障排查

**问题1**: 显示"API Key无效"

**解决**:
1. 检查API Key是否正确复制
2. 确认API Key未过期
3. 在LLM配置页面重新配置
4. 联系提供商客服

**问题2**: 查询超时

**解决**:
1. 检查网络连接
2. 确认提供商服务正常
3. 稍后重试
4. 检查防火墙设置

**问题3**: 余额显示为0

**解决**:
1. 确认是否刚充值（可能有延迟）
2. 刷新页面重新查询
3. 登录官网确认实际余额
4. 联系提供商客服

---

## 🎯 集成到发布流程

### 自动检查机制（未来优化）

可以在发布前自动检查API余额：

```python
# 伪代码示例
async def check_api_balance_before_publish():
    """发布前检查API余额"""
    usage = await APIUsageService.get_siliconflow_balance(api_key)
    
    if usage['balance'] < 5.0:  # 余额低于5元
        raise Exception("硅基流动余额不足，请先充值")
    
    return True
```

### 成本估算

根据历史数据估算每次发布的成本：
- 封面图生成: ~0.01元/次
- 配图生成（3张）: ~0.03元/次
- 文案生成: ~0.005元/次
- **总计**: ~0.045元/篇文章

---

## 📈 未来扩展

### 计划功能

1. **用量统计图表**
   - 每日/每周/每月用量趋势
   - 各提供商用量占比
   - 成本分析报表

2. **自动告警**
   - 余额低于阈值时邮件通知
   - API Key失效时立即告警
   - 异常用量检测

3. **预算管理**
   - 设置月度预算上限
   - 自动暂停超出预算的服务
   - 多账号预算分配

4. **用量预测**
   - 基于历史数据预测消耗
   - 预估余额可用天数
   - 智能充值建议

---

## 🔗 相关文档

- [LLM配置管理](./LLM_CONFIG_GUIDE.md)
- [头条发布完整流程](./TOUTIAO_PUBLISH_WORKFLOW.md)
- [图像生成配置指南](./IMAGE_GENERATION_CONFIG_GUIDE.md)

---

## ❓ 常见问题

### Q1: 为什么只有硅基流动能查余额？

**A**: 目前只有硅基流动提供了公开的余额查询API。魔搭社区和阿里百炼需要通过官网控制台查看。

### Q2: 如何确保API Key安全？

**A**: 
- API Key存储在数据库中，加密保存
- 前端不直接显示完整Key
- 仅在后端服务器使用
- 定期轮换API Key

### Q3: 能否设置余额自动充值？

**A**: 目前需要手动充值。未来可以考虑集成支付API实现自动充值。

### Q4: 多个配置会重复计费吗？

**A**: 不会。每个API Key独立计费，系统只是提供了多个选项，实际使用时只调用一个提供商。

---

## 📞 技术支持

如有问题，请：
1. 查看日志文件: `logs/smart_toolbox_*.log`
2. 检查API Key配置: 系统配置 → 大模型配置
3. 访问提供商官网查看帮助文档
4. 提交Issue到项目仓库
