# Smart Toolbox 前端页面完整列表

## 📋 概述
前端已完成所有页面的路由配置和侧边栏菜单，共 **24个页面**。

---

## 🎯 页面分类

### 1️⃣ 数据大屏（1个）
- **路径**: `/dashboard`
- **组件**: `Dashboard.vue`
- **功能**: 展示系统整体数据统计、图表分析

---

### 2️⃣ 账号管理（8个）
| 页面名称 | 路径 | 组件 | 功能 |
|---------|------|------|------|
| 全部账号 | `/accounts` | AccountManagement.vue | 查看所有平台账号列表 |
| 头条账号 | `/toutiao` | ToutiaoAccount.vue | 今日头条账号管理 |
| 抖音账号 | `/douyin` | DouyinAccount.vue | 抖音账号管理 |
| 快手账号 | `/kuaishou` | KuaishouAccount.vue | 快手账号管理 |
| 视频号 | `/wechat` | WechatAccount.vue | 微信视频号管理 |
| B站账号 | `/bilibili` | BilibiliPublish.vue | B站账号发布 |
| 小红书 | `/xiaohongshu` | XiaohongshuPublish.vue | 小红书账号发布 |
| 批量注册 | `/batch-register` | BatchRegister.vue | 批量注册新账号 |

---

### 3️⃣ 内容创作（4个）
| 页面名称 | 路径 | 组件 | 功能 |
|---------|------|------|------|
| AI文案生成 | `/content` | ContentCreation.vue | AI自动生成文案 |
| AI配图生成 | `/image-generation` | ImageGeneration.vue | AI生成配图 |
| 视觉合成 | `/visual-synthesis` | VisualSynthesis.vue | 视频/图片合成 |
| 视频重组 | `/video-restructure` | VideoRestructure.vue | 视频内容重组 |

---

### 4️⃣ 发布管理（3个）
| 页面名称 | 路径 | 组件 | 功能 |
|---------|------|------|------|
| 发布记录 | `/publish-records` | PublishRecords.vue | 查看历史发布记录 |
| 智能调度 | `/schedule` | ScheduleCenter.vue | 定时发布调度 |
| A/B测试 | `/ab-test` | ABTestManagement.vue | A/B测试管理 |

---

### 5️⃣ 运营监控（3个）
| 页面名称 | 路径 | 组件 | 功能 |
|---------|------|------|------|
| 热点监控 | `/hot-trend` | HotTrendMonitor.vue | 多平台热点监控 |
| 养号中心 | `/account-nurturing` | AccountNurturing.vue | 账号养号管理 |
| 报警中心 | `/alert-center` | AlertCenter.vue | 系统报警通知 |

---

### 6️⃣ 系统配置（1个）
| 页面名称 | 路径 | 组件 | 功能 |
|---------|------|------|------|
| SMS配置 | `/sms-config` | SmsConfig.vue | 短信接码平台配置 |

---

### 7️⃣ 认证页面（2个，无侧边栏）
| 页面名称 | 路径 | 组件 | 说明 |
|---------|------|------|------|
| 登录 | `/login` | Login.vue | 用户登录（不需要认证） |
| 注册 | `/register` | Register.vue | 用户注册（不需要认证） |

---

## 🎨 UI布局

### 主布局组件
- **文件**: `frontend/src/components/MainLayout.vue`
- **包含**:
  - ✅ 左侧可折叠侧边栏菜单
  - ✅ 顶部导航栏（显示用户信息、退出登录）
  - ✅ 主要内容区域（路由视图）

### 侧边栏菜单分组
```
📊 数据大屏
👤 账号管理 (子菜单: 全部账号、头条、抖音、快手、视频号、B站、小红书、批量注册)
✏️ 内容创作 (子菜单: AI文案、AI配图、视觉合成、视频重组)
📤 发布管理 (子菜单: 发布记录、智能调度、A/B测试)
📈 运营监控 (子菜单: 热点监控、养号中心、报警中心)
⚙️ 系统配置 (子菜单: SMS配置)
```

---

## 🔧 技术细节

### 路由配置
- **文件**: `frontend/src/router/index.ts`
- **模式**: Vue Router 嵌套路由
- **认证**: 使用路由守卫检查 JWT Token
- **懒加载**: 所有页面在主布局中作为子路由加载

### API客户端
- **文件**: `frontend/src/utils/api.ts`
- **基础URL**: `http://localhost:8000/api/v1`
- **超时**: 10秒
- **自动添加**: JWT Token到请求头

---

## 🚀 访问方式

1. **启动后端**: `uvicorn main:app --host 0.0.0.0 --port 8000 --reload`
2. **启动前端**: `cd frontend && npm run dev`
3. **访问地址**: http://localhost:3002
4. **默认账号**: 需要先注册或使用已有账号登录

---

## 📝 注意事项

1. **首次访问**: 会重定向到 `/login` 页面
2. **登录后**: 自动跳转到 `/dashboard`
3. **Token过期**: 自动跳转回登录页
4. **刷新页面**: 保持登录状态（Token存储在localStorage）

---

## ✅ 完成状态

- ✅ 所有24个页面已创建
- ✅ 路由配置完整
- ✅ 侧边栏菜单完整
- ✅ 认证守卫已实现
- ✅ API客户端统一
- ✅ CORS配置正确
- ✅ 响应式布局

---

**最后更新**: 2026-05-04
