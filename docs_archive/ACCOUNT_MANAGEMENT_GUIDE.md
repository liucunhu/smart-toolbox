# 头条账号管理功能使用指南

## 🎯 功能概述

提供完整的头条账号管理功能，包括：
- ✅ 创建账号
- ✅ 查看账号列表（隐藏敏感信息）
- ✅ 查看账号详情
- ✅ 编辑账号信息
- ✅ 删除账号
- ✅ 登录账号（智能登录）

**重要**: 前端页面不直接展示登录表单，所有操作通过API进行。

---

## 📋 API接口清单

### 1. 创建账号

**URL**: `POST /api/v1/accounts/create`

**参数**:
- `platform` (必填): 平台类型（toutiao/douyin/xiaohongshu等）
- `username` (必填): 用户名/手机号
- `password` (可选): 密码
- `proxy_ip` (可选): 代理IP

**示例**:
```bash
curl -X POST http://localhost:8000/api/v1/accounts/create \
  -d "platform=toutiao" \
  -d "username=13800138000" \
  -d "password=your_password"
```

**响应**:
```json
{
  "status": "success",
  "message": "账号创建成功",
  "account": {
    "id": 1,
    "platform": "toutiao",
    "username": "13800138000",
    "status": "registering",
    "created_at": "2026-05-03T21:30:00"
  }
}
```

---

### 2. 获取账号列表

**URL**: `GET /api/v1/accounts/list`

**参数**:
- `skip` (可选): 跳过数量，默认0
- `limit` (可选): 每页数量，默认10
- `platform` (可选): 平台筛选
- `status` (可选): 状态筛选

**示例**:
```bash
# 获取所有头条账号
curl "http://localhost:8000/api/v1/accounts/list?platform=toutiao&limit=20"

# 获取活跃账号
curl "http://localhost:8000/api/v1/accounts/list?status=active"
```

**响应**:
```json
{
  "accounts": [
    {
      "id": 1,
      "platform": "toutiao",
      "username": "13800138000",
      "status": "active",
      "health_score": 95.5,
      "proxy_ip": null,
      "has_cookies": true,
      "has_password": true,
      "created_at": "2026-05-03T21:30:00",
      "updated_at": "2026-05-03T21:35:00"
    }
  ],
  "total": 1
}
```

**注意**: 
- ❌ 不返回密码
- ❌ 不返回完整Cookie
- ✅ 只返回是否有密码/Cookie的标识

---

### 3. 获取账号详情

**URL**: `GET /api/v1/accounts/{account_id}`

**示例**:
```bash
curl http://localhost:8000/api/v1/accounts/1
```

**响应**:
```json
{
  "id": 1,
  "platform": "toutiao",
  "username": "13800138000",
  "status": "active",
  "health_score": 95.5,
  "proxy_ip": null,
  "has_cookies": true,
  "has_password": true,
  "session_token": "abc123def456...",
  "publish_url": "https://mp.toutiao.com/profile_v4/graphic/publish",
  "created_at": "2026-05-03T21:30:00",
  "updated_at": "2026-05-03T21:35:00"
}
```

---

### 4. 更新账号信息

**URL**: `PUT /api/v1/accounts/{account_id}`

**参数** (全部可选):
- `username`: 新用户名
- `password`: 新密码
- `proxy_ip`: 新代理IP

**示例**:
```bash
# 只更新密码
curl -X PUT http://localhost:8000/api/v1/accounts/1 \
  -d "password=new_password"

# 更新多个字段
curl -X PUT http://localhost:8000/api/v1/accounts/1 \
  -d "username=new_username" \
  -d "password=new_password" \
  -d "proxy_ip=192.168.1.100"
```

**响应**:
```json
{
  "status": "success",
  "message": "账号信息更新成功",
  "account": {
    "id": 1,
    "platform": "toutiao",
    "username": "new_username",
    "status": "active",
    "proxy_ip": "192.168.1.100",
    "has_cookies": true,
    "updated_at": "2026-05-03T21:40:00"
  }
}
```

---

### 5. 删除账号

**URL**: `DELETE /api/v1/accounts/{account_id}`

**示例**:
```bash
curl -X DELETE http://localhost:8000/api/v1/accounts/1
```

**响应**:
```json
{
  "status": "success",
  "message": "账号 toutiao - 13800138000 已删除"
}
```

---

### 6. 登录账号（智能登录）

**URL**: `POST /api/v1/accounts/toutiao/login`

**参数**:
- `account_id` (必填): 账号ID
- `username` (可选): 用户名，仅在Cookie失效时需要
- `password` (可选): 密码，仅在Cookie失效时需要

**示例**:
```bash
# 方式1: 使用Cookie登录（推荐）
curl -X POST http://localhost:8000/api/v1/accounts/toutiao/login \
  -d "account_id=1"

# 方式2: 提供账号密码作为备用
curl -X POST http://localhost:8000/api/v1/accounts/toutiao/login \
  -d "account_id=1" \
  -d "username=13800138000" \
  -d "password=your_password"
```

**响应** (Cookie登录成功):
```json
{
  "status": "success",
  "message": "Cookie登录成功",
  "login_method": "cookie",
  "cookies": "{...}"
}
```

**响应** (账号密码登录成功):
```json
{
  "status": "success",
  "message": "登录成功，已保存会话状态",
  "login_method": "password",
  "cookies": "{...}"
}
```

---

## 💡 使用场景

### 场景1: 添加新头条账号

```bash
# 1. 创建账号记录
curl -X POST http://localhost:8000/api/v1/accounts/create \
  -d "platform=toutiao" \
  -d "username=13800138000" \
  -d "password=your_password"

# 响应: {"account": {"id": 1, ...}}

# 2. 登录账号（会自动保存Cookie）
curl -X POST http://localhost:8000/api/v1/accounts/toutiao/login \
  -d "account_id=1" \
  -d "username=13800138000" \
  -d "password=your_password"
```

### 场景2: 查看所有头条账号

```bash
curl "http://localhost:8000/api/v1/accounts/list?platform=toutiao"
```

### 场景3: 修改账号密码

```bash
curl -X PUT http://localhost:8000/api/v1/accounts/1 \
  -d "password=new_password"
```

### 场景4: 删除不再使用的账号

```bash
curl -X DELETE http://localhost:8000/api/v1/accounts/1
```

### 场景5: 登录并发布文章

```bash
# 1. 智能登录（自动选择最佳方式）
curl -X POST http://localhost:8000/api/v1/accounts/toutiao/login \
  -d "account_id=1"

# 2. 发布文章（系统会自动使用保存的Cookie）
curl -X POST http://localhost:8000/api/v1/content/toutiao/publish \
  -d "account_id=1" \
  -d "title=Python教程" \
  -d "content=文章内容..."
```

---

## 🔒 安全特性

### 1. 敏感信息保护

| 字段 | 列表接口 | 详情接口 | 说明 |
|------|---------|---------|------|
| password | ❌ 不返回 | ❌ 不返回 | 完全隐藏 |
| cookies | ❌ 不返回 | ❌ 不返回 | 完全隐藏 |
| has_password | ✅ 返回布尔值 | ✅ 返回布尔值 | 仅标识是否存在 |
| has_cookies | ✅ 返回布尔值 | ✅ 返回布尔值 | 仅标识是否存在 |
| session_token | ❌ 不返回 | ⚠️ 部分显示 | 只显示前20字符 |

### 2. 数据加密建议

**当前状态**: 
- ⚠️  密码明文存储（待优化）
- ⚠️  Cookie明文存储（待优化）

**建议改进**:
```python
# 使用bcrypt加密密码
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed_password = pwd_context.hash(password)

# 验证密码
pwd_context.verify(plain_password, hashed_password)
```

---

## 📊 前端集成示例

### Vue 3 + Element Plus

```vue
<template>
  <div class="account-management">
    <!-- 账号列表 -->
    <el-table :data="accounts" style="width: 100%">
      <el-table-column prop="id" label="ID" width="80" />
      <el-table-column prop="platform" label="平台" width="100" />
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="status" label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="getStatusType(row.status)">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="Cookie" width="100">
        <template #default="{ row }">
          <el-tag v-if="row.has_cookies" type="success">已登录</el-tag>
          <el-tag v-else type="info">未登录</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="250">
        <template #default="{ row }">
          <el-button size="small" @click="handleLogin(row)">
            登录
          </el-button>
          <el-button size="small" @click="handleEdit(row)">
            编辑
          </el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">
            删除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    
    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialogVisible" title="编辑账号">
      <el-form :model="editForm" label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="editForm.password" type="password" placeholder="留空则不修改" />
        </el-form-item>
        <el-form-item label="代理IP">
          <el-input v-model="editForm.proxy_ip" placeholder="可选" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitEdit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'

const accounts = ref([])
const editDialogVisible = ref(false)
const editForm = ref({})

// 加载账号列表
const loadAccounts = async () => {
  const response = await axios.get('/api/v1/accounts/list', {
    params: { platform: 'toutiao' }
  })
  accounts.value = response.data.accounts
}

// 登录账号
const handleLogin = async (account) => {
  try {
    const response = await axios.post('/api/v1/accounts/toutiao/login', {
      account_id: account.id
    })
    
    if (response.data.status === 'success') {
      ElMessage.success(`登录成功（方式: ${response.data.login_method}）`)
      loadAccounts() // 刷新列表
    } else {
      ElMessage.error(response.data.message)
    }
  } catch (error) {
    ElMessage.error('登录失败')
  }
}

// 编辑账号
const handleEdit = (account) => {
  editForm.value = {
    id: account.id,
    username: account.username,
    password: '',
    proxy_ip: account.proxy_ip
  }
  editDialogVisible.value = true
}

// 提交编辑
const submitEdit = async () => {
  try {
    const data = {
      username: editForm.value.username,
      proxy_ip: editForm.value.proxy_ip
    }
    
    // 只有填写了密码才更新
    if (editForm.value.password) {
      data.password = editForm.value.password
    }
    
    await axios.put(`/api/v1/accounts/${editForm.value.id}`, data)
    
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    loadAccounts()
  } catch (error) {
    ElMessage.error('更新失败')
  }
}

// 删除账号
const handleDelete = async (account) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除账号 ${account.username} 吗？`,
      '警告',
      { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
    )
    
    await axios.delete(`/api/v1/accounts/${account.id}`)
    
    ElMessage.success('删除成功')
    loadAccounts()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 获取状态标签类型
const getStatusType = (status) => {
  const types = {
    active: 'success',
    registering: 'warning',
    banned: 'danger'
  }
  return types[status] || 'info'
}

onMounted(() => {
  loadAccounts()
})
</script>
```

---

## 🔍 调试技巧

### 1. 查看所有账号

```bash
curl "http://localhost:8000/api/v1/accounts/list?limit=100" | python -m json.tool
```

### 2. 检查Cookie状态

```bash
curl http://localhost:8000/api/v1/accounts/1 | grep has_cookies
```

### 3. 测试登录

```bash
# 第一次登录（保存Cookie）
curl -X POST http://localhost:8000/api/v1/accounts/toutiao/login \
  -d "account_id=1" \
  -d "username=xxx" \
  -d "password=xxx"

# 第二次登录（应该使用Cookie）
curl -X POST http://localhost:8000/api/v1/accounts/toutiao/login \
  -d "account_id=1"
```

### 4. 查看日志

```bash
tail -f logs/app.log | grep -E "账号|登录|Cookie"
```

---

## ❓ 常见问题

### Q1: 如何批量导入账号？

**A**: 可以使用循环调用创建接口：

```python
import requests

accounts = [
    {"username": "user1", "password": "pass1"},
    {"username": "user2", "password": "pass2"},
]

for acc in accounts:
    requests.post("http://localhost:8000/api/v1/accounts/create", data={
        "platform": "toutiao",
        "username": acc["username"],
        "password": acc["password"]
    })
```

### Q2: Cookie多久会过期？

**A**: 通常7-30天，取决于头条平台策略。可以通过`has_cookies`字段检查。

### Q3: 如何强制重新登录？

**A**: 先清除数据库中的Cookie，然后重新登录：

```sql
UPDATE accounts SET cookies = NULL WHERE id = 1;
```

### Q4: 可以修改账号的平台类型吗？

**A**: 不建议。如果需要更改，请删除旧账号并创建新账号。

---

## 📝 总结

### 核心功能
- ✅ 创建账号
- ✅ 查看列表（隐藏敏感信息）
- ✅ 查看详情（隐藏敏感信息）
- ✅ 编辑账号
- ✅ 删除账号
- ✅ 智能登录

### 安全特性
- ✅ 密码不返回
- ✅ Cookie不返回
- ✅ 只返回存在性标识
- ⚠️  建议加密存储（待实现）

### 使用建议
1. 首次使用时创建账号并登录
2. 后续使用智能登录（自动使用Cookie）
3. 定期检查`has_cookies`状态
4. Cookie失效时重新登录

---

**开发完成时间**: 2026年5月3日  
**功能状态**: ✅ 已完成  
**测试状态**: ⏳ 待测试
