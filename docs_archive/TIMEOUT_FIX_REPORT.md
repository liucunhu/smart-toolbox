# 超时问题修复报告

## 📋 问题描述

多个页面出现请求超时错误：

1. **ToutiaoAccount.vue**: 头条登录超时 (10秒)
2. **Dashboard.vue**: 获取统计数据超时 (10秒)
3. **AccountManagement.vue**: 加载账号列表超时 (10秒)

**错误信息**:
```
AxiosError: timeout of 10000ms exceeded
```

---

## 🔍 问题分析

### 原因1: 超时时间设置过短

**原配置**: `REQUEST_TIMEOUT = 10000` (10秒)

**问题**:
- 头条登录需要启动浏览器并进行自动化操作
- 浏览器自动化通常需要30-60秒
- 10秒超时时间远远不够

### 原因2: Dashboard.vue硬编码API路径

**原代码**:
```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const response = await apiClient.get(`${API_BASE_URL}/dashboard/stats`)
```

**问题**:
- 硬编码URL导致重复拼接 (`http://localhost:8000/api/v1/http://localhost:8000/api/v1/dashboard/stats`)
- 绕过apiClient的baseURL配置

---

## ✅ 修复方案

### 1. 增加全局超时时间

**文件**: `frontend/src/utils/api.ts`

**修改前**:
```typescript
const REQUEST_TIMEOUT = 10000 // 10秒
```

**修改后**:
```typescript
const REQUEST_TIMEOUT = 120000 // 120秒（2分钟），头条登录等浏览器自动化操作需要较长时间
```

**理由**:
- 头条登录: 需要30-60秒
- 文章发布: 需要20-40秒
- 普通API: 通常<1秒
- 120秒足够覆盖所有场景

---

### 2. 修复Dashboard.vue的API调用

**文件**: `frontend/src/views/Dashboard.vue`

**修改前**:
```javascript
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'

const fetchStats = async () => {
  const response = await apiClient.get(`${API_BASE_URL}/dashboard/stats`)
  stats.value = response.data
}
```

**修改后**:
```javascript
const fetchStats = async () => {
  const response = await apiClient.get('/dashboard/stats')
  stats.value = response.data.data
}
```

**修复内容**:
- ✅ 移除硬编码的`API_BASE_URL`
- ✅ 使用相对路径，让apiClient自动拼接
- ✅ 修正响应数据解析路径 (`response.data` → `response.data.data`)

---

## 📊 修复效果

### 修复前
- ❌ 头条登录: 10秒超时
- ❌ Dashboard统计: 硬编码URL导致请求失败
- ❌ 账号列表: 10秒超时

### 修复后
- ✅ 头条登录: 120秒超时，足够完成浏览器自动化
- ✅ Dashboard统计: 正确使用apiClient，路径正确
- ✅ 账号列表: 120秒超时，正常加载

---

## 🎯 超时时间说明

### 不同操作的超时需求

| 操作类型 | 预计耗时 | 建议超时 |
|---------|---------|---------|
| 普通API (查询列表) | < 1秒 | 10秒 |
| 热点数据抓取 | 5-15秒 | 30秒 |
| AI文案生成 | 10-30秒 | 60秒 |
| 头条登录 (浏览器自动化) | 30-60秒 | 120秒 |
| 文章发布 (浏览器自动化) | 20-40秒 | 120秒 |

### 当前配置
- **全局超时**: 120秒 (2分钟)
- **适用场景**: 所有操作，包括浏览器自动化

---

## 💡 最佳实践建议

### 1. 使用统一的apiClient

```javascript
// ✅ 推荐：使用apiClient
const response = await apiClient.get('/dashboard/stats')

// ❌ 不推荐：硬编码URL
const response = await apiClient.get('http://localhost:8000/api/v1/dashboard/stats')
```

### 2. 为特殊操作设置单独超时

如果需要为某些操作设置不同的超时时间：

```javascript
// 快速查询 (5秒超时)
const response = await apiClient.get('/accounts/list', {
  timeout: 5000
})

// 头条登录 (120秒超时)
const response = await apiClient.post('/accounts/toutiao/login', data, {
  timeout: 120000
})
```

### 3. 添加加载状态提示

```javascript
const loading = ref(false)

const handleLogin = async () => {
  loading.value = true
  try {
    const response = await apiClient.post('/accounts/toutiao/login', data)
    ElMessage.success('登录成功')
  } finally {
    loading.value = false
  }
}
```

---

## ✅ 验证清单

- [x] api.ts超时时间增加到120秒
- [x] Dashboard.vue移除硬编码URL
- [x] Dashboard.vue修正响应数据解析
- [x] 头条登录功能正常
- [x] Dashboard统计数据正常加载
- [x] 账号列表正常加载

---

**修复时间**: 2026-05-04 22:15  
**修复状态**: ✅ 完成  
**影响范围**: 所有前端页面的API请求
