# 合规审查系统 - 完整实施指南

## 🎯 核心要求

**所有平台的内容发布前必须经过合规审查，包括：**
- ✅ 头条文章
- ✅ 快手视频
- ✅ 视频号
- ✅ B站视频  
- ✅ 小红书笔记
- ✅ 抖音视频

**标准：**
1. **100%覆盖** - 所有发布接口都必须有合规审查
2. **强制执行** - 审查失败立即终止，无法绕过
3. **详细反馈** - 明确指出违禁词位置和內容
4. **完整日志** - 记录每次审查结果

---

## ✅ 已完成的工作

### 1. 统一合规审查工具函数

**文件**: `app/api/v1/endpoints.py`

**新增函数**:

```python
def check_compliance(text: str, platform: str) -> Dict[str, Any]:
    """单文本合规检查"""
    
def check_content_compliance(title: str, content: str, platform: str) -> Dict[str, Any]:
    """完整内容合规审查（标题+正文）"""
```

**特性**:
- ✅ 自动加载平台规则
- ✅ 检测违禁词
- ✅ 返回详细错误信息
- ✅ 统一错误格式

---

### 2. 头条发布接口（✅ 100%完成）

#### A. 手动发布
**接口**: `POST /content/toutiao/publish`  
**状态**: ✅ 已集成合规审查

**代码位置**: Line ~507

```python
# 合规审查（必须）
logger.info(f"🔍 正在进行合规审查...")
compliance_result = check_content_compliance(title, content, "toutiao")
if not compliance_result["passed"]:
    logger.warning(f"⚠️  合规审查失败: {compliance_result['error']}")
    return {
        "status": "failed",
        "error": compliance_result["error"]
    }
logger.info(f"✅ 合规审查通过")
```

---

#### B. 全自动发布
**接口**: `POST /content/toutiao/auto_publish`  
**状态**: ✅ 已集成合规审查

**代码位置**: Line ~648

```python
# 步骤 2.5: 合规审查（必须）
logger.info(f"🔍 [步骤2.5/5] 正在进行合规审查...")
compliance_result = check_content_compliance(article_title, article_content, "toutiao")
if not compliance_result["passed"]:
    logger.warning(f"⚠️  合规审查失败: {compliance_result['error']}")
    return {
        "status": "failed",
        "step": "compliance",
        "error": compliance_result["error"]
    }
logger.info(f"✅ [步骤2.5/5] 合规审查通过")
```

---

## ⏳ 待完成的工作

### 需要添加合规审查的接口清单

#### 1. 快手发布 ⏳
**接口**: `POST /content/kuaishou/publish`  
**文件**: `app/api/v1/endpoints.py`  
**行号**: ~1060

**需要添加的代码**:
```python
async def publish_process():
    publisher = KuaishouPublisher(account_id=account_id)
    try:
        await publisher.initialize_browser()
        
        if account.cookies:
            await publisher.context.add_cookies(json.loads(account.cookies))
        
        # ========== 合规审查（必须）==========
        logger.info(f"🔍 正在进行合规审查...")
        compliance_result = check_content_compliance(description, "", "kuaishou")
        if not compliance_result["passed"]:
            logger.warning(f"⚠️  合规审查失败: {compliance_result['error']}")
            return {
                "status": "failed",
                "error": compliance_result["error"]
            }
        logger.info(f"✅ 合规审查通过")
        
        result = await publisher.publish_video(...)
        return result
    finally:
        await publisher.close()
```

---

#### 2. 视频号发布 ⏳
**接口**: `POST /content/wechat/publish`  
**文件**: `app/api/v1/endpoints.py`  
**行号**: ~1109

**需要添加的代码**:
```python
async def publish_process():
    publisher = WechatPublisher(account_id=account_id)
    try:
        await publisher.initialize_browser()
        
        if account.cookies:
            await publisher.context.add_cookies(json.loads(account.cookies))
        
        # ========== 合规审查（必须）==========
        logger.info(f"🔍 正在进行合规审查...")
        compliance_result = check_content_compliance(description, "", "wechat")
        if not compliance_result["passed"]:
            logger.warning(f"⚠️  合规审查失败: {compliance_result['error']}")
            return {
                "status": "failed",
                "error": compliance_result["error"]
            }
        logger.info(f"✅ 合规审查通过")
        
        result = await publisher.publish_video(...)
        return result
    finally:
        await publisher.close()
```

---

#### 3. B站发布 ⏳
**接口**: `POST /content/bilibili/publish`  
**文件**: `app/api/v1/endpoints.py`  
**行号**: ~1191

**需要添加的代码**:
```python
async def publish_process():
    publisher = BilibiliPublisher(account_id=account_id)
    try:
        await publisher.initialize_browser()
        
        if account.cookies:
            await publisher.context.add_cookies(json.loads(account.cookies))
        
        # ========== 合规审查（必须）==========
        logger.info(f"🔍 正在进行合规审查...")
        compliance_result = check_content_compliance(title, description, "bilibili")
        if not compliance_result["passed"]:
            logger.warning(f"⚠️  合规审查失败: {compliance_result['error']}")
            return {
                "status": "failed",
                "error": compliance_result["error"]
            }
        logger.info(f"✅ 合规审查通过")
        
        result = await publisher.publish_video(...)
        return result
    finally:
        await publisher.close()
```

---

#### 4. 小红书发布 ⏳
**接口**: `POST /content/xiaohongshu/publish`  
**文件**: `app/api/v1/endpoints.py`  
**行号**: ~1274

**需要添加的代码**:
```python
async def publish_process():
    publisher = XiaohongshuPublisher(account_id=account_id)
    try:
        await publisher.initialize_browser()
        
        if account.cookies:
            await publisher.context.add_cookies(json.loads(account.cookies))
        
        # ========== 合规审查（必须）==========
        logger.info(f"🔍 正在进行合规审查...")
        compliance_result = check_content_compliance(title, content, "xiaohongshu")
        if not compliance_result["passed"]:
            logger.warning(f"⚠️  合规审查失败: {compliance_result['error']}")
            return {
                "status": "failed",
                "error": compliance_result["error"]
            }
        logger.info(f"✅ 合规审查通过")
        
        result = await publisher.publish_note(...)
        return result
    finally:
        await publisher.close()
```

---

## 📊 实施进度统计

| 平台 | 手动发布 | 自动发布 | 完成度 |
|------|---------|---------|--------|
| 头条 | ✅ 100% | ✅ 100% | ✅ 100% |
| 快手 | ❌ 0% | N/A | ❌ 0% |
| 视频号 | ❌ 0% | N/A | ❌ 0% |
| B站 | ❌ 0% | N/A | ❌ 0% |
| 小红书 | ❌ 0% | N/A | ❌ 0% |
| 抖音 | ❌ 0% | N/A | ❌ 0% |

**总体进度**: **16.7%** (1/6平台完成)

---

## 🔧 快速实施脚本

### Python脚本自动添加合规审查

创建一个脚本来批量修改：

```python
# add_compliance_check.py
import re

def add_compliance_to_publish_interface(file_path, platform, title_var, content_var):
    """为发布接口添加合规审查"""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 查找发布函数的位置
    pattern = rf'async def publish_process\(\):.*?publisher = \w+Publisher\(account_id=account_id\)'
    
    # 在找到位置后插入合规审查代码
    compliance_code = f'''
        # ========== 合规审查（必须）==========
        logger.info(f"🔍 正在进行合规审查...")
        compliance_result = check_content_compliance({title_var}, {content_var}, "{platform}")
        if not compliance_result["passed"]:
            logger.warning(f"⚠️  合规审查失败: {{compliance_result['error']}}")
            return {{
                "status": "failed",
                "error": compliance_result["error"]
            }}
        logger.info(f"✅ 合规审查通过")
'''
    
    # 替换逻辑...
    # (具体实现需要根据实际代码结构调整)
    
    print(f"✅ 已为 {platform} 添加合规审查")
```

---

## 📝 测试用例

### 1. 正常内容测试

```bash
# 应该成功发布
curl -X POST http://localhost:8000/api/v1/content/toutiao/publish \
  -d "account_id=1" \
  -d "title=人工智能技术发展趋势" \
  -d "content=这是一篇关于AI技术的文章..."
```

**预期响应**:
```json
{
  "status": "success",
  "message": "文章发布成功"
}
```

---

### 2. 包含违禁词测试

```bash
# 应该被拦截
curl -X POST http://localhost:8000/api/v1/content/toutiao/publish \
  -d "account_id=1" \
  -d "title=这是最牛的技术" \
  -d "content=第一名的产品..."
```

**预期响应**:
```json
{
  "status": "failed",
  "error": "标题包含违禁词: 最牛"
}
```

---

### 3. 内容包含违禁词测试

```bash
# 应该被拦截
curl -X POST http://localhost:8000/api/v1/content/toutiao/publish \
  -d "account_id=1" \
  -d "title=技术分享" \
  -d "content=这个产品绝对是最好的，排名第一..."
```

**预期响应**:
```json
{
  "status": "failed",
  "error": "内容包含2处违禁词"
}
```

---

## 🎯 验收标准

### 必须满足的条件

- [ ] **所有6个平台**的发布接口都有合规审查
- [ ] 审查**失败时立即终止**，不会继续发布
- [ ] 返回**清晰的错误信息**，指出具体问题
- [ ] 记录**完整的日志**，便于审计
- [ ] **无法绕过**审查机制
- [ ] 支持**多平台规则**差异化
- [ ] 性能影响**小于100ms**

---

### 测试清单

- [ ] 正常内容能成功发布
- [ ] 标题包含违禁词被拦截
- [ ] 内容包含违禁词被拦截
- [ ] 多个违禁词都能检测
- [ ] 不同平台规则不同
- [ ] 日志记录完整
- [ ] 错误信息清晰
- [ ] 性能符合要求

---

## 💡 最佳实践

### 1. 统一的错误处理

```python
# 所有平台使用相同的错误格式
{
    "status": "failed",
    "error": "详细描述错误信息"
}
```

### 2. 详细的日志记录

```python
logger.info(f"🔍 正在进行合规审查...")
logger.warning(f"⚠️  合规审查失败: {error}")
logger.info(f"✅ 合规审查通过")
```

### 3. 平台差异化规则

```python
# 不同平台加载不同的规则
filter_engine.load_platform_rules(platform)  # toutiao/kuaishou/wechat等
```

---

## 📋 实施计划

### P0 - 今天完成（最高优先级）
- [x] 创建统一合规审查工具函数
- [x] 头条发布接口集成
- [ ] 快手发布接口集成
- [ ] 视频号发布接口集成
- [ ] B站发布接口集成
- [ ] 小红书发布接口集成

### P1 - 本周完成
- [ ] 前端添加合规审查提示UI
- [ ] 添加合规审查统计API
- [ ] 完善各平台违禁词库
- [ ] 编写完整测试用例

### P2 - 本月完成
- [ ] 实时违禁词更新机制
- [ ] 自定义违禁词功能
- [ ] 合规审查报告生成
- [ ] 性能优化

---

## 🔒 安全保障

### 1. 强制性强
- ✅ 代码层面强制，无法绕过
- ✅ 审查失败立即return，不执行后续代码
- ✅ 没有配置开关，始终启用

### 2. 透明度高
- ✅ 明确的日志记录
- ✅ 清晰的错误提示
- ✅ 完整的审计追踪

### 3. 可扩展性
- ✅ 易于添加新平台
- ✅ 易于更新违禁词库
- ✅ 支持自定义规则

---

## 📞 联系方式

如有问题，请参考：
- 违禁词引擎: `app/services/distribute/banned_words_check.py`
- 工具函数: `app/api/v1/endpoints.py` (Line ~1045)
- 实施文档: `COMPLIANCE_CHECK_INTEGRATION.md`

---

**最后更新**: 2026年5月3日  
**当前进度**: 16.7% (1/6平台)  
**目标进度**: 100%  
**优先级**: P0 - 最高优先级  
**预计完成时间**: 今天内
