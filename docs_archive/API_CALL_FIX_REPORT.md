# 前端API调用修复报告

## 📋 问题描述

前端页面在获取账号列表时出现404错误和数据结构不匹配错误：

1. **BatchRegister.vue**: 使用不存在的API `/accounts/batch/list`
2. **ContentCreation.vue**: API参数错误（`skip/limit` vs `page/page_size`）
3. **两个文件**: 响应数据结构解析错误

---

## 🔍 问题分析

### 后端API实际结构

**端点**: `GET /api/v1/accounts/list`

**请求参数**:
- `page`: 页码（默认1）
- `page_size`: 每页数量（默认10）
- `platform`: 平台筛选（可选）
- `status`: 状态筛选（可选）

**响应结构**:
```json
{
  "status": "success",
  "message": "获取成功",
  "data": {
    "items": [
      {
        "id": 1,
        "platform": "toutiao",
        "username": "test",
        "status": "active",
        "health_score": 100.0,
        ...
      }
    ],
    "total": 10,
    "page": 1,
    "page_size": 10
  }
}
```

### 前端错误调用

**BatchRegister.vue** (错误):
```javascript
const response = await apiClient.get('/accounts/batch/list', {
  params: {
    limit: pagination.value.pageSize  // ❌ 参数名错误
  }
})
accounts.value = response.data.accounts      // ❌ 路径错误
pagination.value.total = response.data.total // ❌ 路径错误
```

**ContentCreation.vue** (错误):
```javascript
const response = await apiClient.get('/accounts/list', {
  params: {
    platform: 'toutiao',
    skip: 0,      // ❌ 参数名错误
    limit: 100    // ❌ 参数名错误
  }
})
toutiaoAccounts.value = response.data.accounts // ❌ 路径错误
```

---

## ✅ 修复方案

### 1. BatchRegister.vue 修复

**修改前**:
```javascript
const response = await apiClient.get('/accounts/batch/list', {
  params: {
    limit: pagination.value.pageSize
  }
})
accounts.value = response.data.accounts
pagination.value.total = response.data.total
```

**修改后**:
```javascript
const response = await apiClient.get('/accounts/list', {
  params: {
    page: pagination.value.page,
    page_size: pagination.value.pageSize
  }
})
accounts.value = response.data.data.items
pagination.value.total = response.data.data.total
```

**修复内容**:
- ✅ API路径: `/accounts/batch/list` → `/accounts/list`
- ✅ 参数名: `limit` → `page` + `page_size`
- ✅ 数据路径: `response.data.accounts` → `response.data.data.items`
- ✅ 总数路径: `response.data.total` → `response.data.data.total`

---

### 2. ContentCreation.vue 修复

**修改前**:
```javascript
const response = await apiClient.get('/accounts/list', {
  params: {
    platform: 'toutiao',
    skip: 0,
    limit: 100
  }
})
toutiaoAccounts.value = response.data.accounts
```

**修改后**:
```javascript
const response = await apiClient.get('/accounts/list', {
  params: {
    platform: 'toutiao',
    page: 1,
    page_size: 100
  }
})
toutiaoAccounts.value = response.data.data.items
```

**修复内容**:
- ✅ 参数名: `skip/limit` → `page/page_size`
- ✅ 数据路径: `response.data.accounts` → `response.data.data.items`

---

## 📊 修复效果

### 修复前
- ❌ BatchRegister页面: 404 Not Found
- ❌ ContentCreation页面: TypeError (无法读取undefined的length)
- ❌ 账号列表无法加载

### 修复后
- ✅ BatchRegister页面: 正常加载账号列表
- ✅ ContentCreation页面: 正常加载头条账号
- ✅ 下拉选择框正确显示账号
- ✅ 分页功能正常工作

---

## 🎯 最佳实践建议

### 1. 统一API响应处理

建议在 `utils/api.ts` 中添加响应拦截器，自动提取数据：

```typescript
// utils/api.ts
apiClient.interceptors.response.use(
  (response) => {
    // 自动提取data字段
    if (response.data && response.data.data) {
      response.data = response.data.data
    }
    return response
  },
  (error) => { ... }
)
```

### 2. 定义API响应类型

```typescript
// types/api.ts
export interface PaginatedResponse<T> {
  status: string
  message: string
  data: {
    items: T[]
    total: number
    page: number
    page_size: number
  }
}

export interface Account {
  id: number
  platform: string
  username: string
  status: string
  health_score: number
  // ...
}
```

### 3. 封装API调用

```typescript
// api/accounts.ts
export const accountsApi = {
  getList(params: { page?: number; page_size?: number; platform?: string }) {
    return apiClient.get<PaginatedResponse<Account>>('/accounts/list', { params })
  }
}

// 使用
const response = await accountsApi.getList({
  page: 1,
  page_size: 10,
  platform: 'toutiao'
})
accounts.value = response.data.items
```

---

## ✅ 验证清单

- [x] BatchRegister.vue API调用修复
- [x] ContentCreation.vue API调用修复
- [x] API路径正确
- [x] 请求参数正确
- [x] 响应数据解析正确
- [x] 分页功能正常
- [x] 平台筛选功能正常

---

**修复时间**: 2026-05-04 22:10  
**修复状态**: ✅ 完成  
**影响范围**: 批量注册页面、内容创作页面
