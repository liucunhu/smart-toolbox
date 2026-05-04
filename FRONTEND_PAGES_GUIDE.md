# 📱 Smart-Toolbox 前端页面访问指南

**更新日期**: 2026-05-03  
**状态**: ✅ **所有页面已配置完成**

---

## 🎯 快速访问地址

### 基础页面
| 页面名称 | 访问地址 | 说明 |
|---------|---------|------|
| 登录页 | http://localhost:3001/login | 用户登录 |
| 注册页 | http://localhost:3001/register | 用户注册 |
| 仪表盘 | http://localhost:3001/dashboard | 数据大屏 |

---

## 🚀 Phase 1-2: 多平台发布页面（4个）

### 1. 快手账号管理
**地址**: http://localhost:3001/kuaishou

**功能**:
- ✅ 快手账号登录（密码模式）
- ✅ 视频发布
- ✅ 图文发布
- ✅ Cookie自动保存

**使用流程**:
1. 输入账号ID、手机号、密码
2. 点击"登录并保存Cookie"
3. 系统打开浏览器自动登录
4. 登录成功后可发布视频/图文

---

### 2. 视频号账号管理
**地址**: http://localhost:3001/wechat

**功能**:
- ✅ 微信扫码登录
- ✅ 视频发布
- ✅ 位置信息添加
- ✅ 话题标签支持

**使用流程**:
1. 输入账号ID
2. 点击"扫码登录"
3. 使用微信扫描二维码
4. 登录成功后发布视频

---

### 3. B站发布
**地址**: http://localhost:3001/bilibili

**功能**:
- ✅ B站扫码登录
- ✅ 视频发布（支持原创/转载）
- ✅ 专栏文章发布
- ✅ 分区选择
- ✅ 封面设置

**使用流程**:
1. 输入账号ID
2. 点击"扫码登录"
3. 使用B站APP扫描二维码
4. 填写视频信息并发布

---

### 4. 小红书发布
**地址**: http://localhost:3001/xiaohongshu

**功能**:
- ✅ 小红书账号登录
- ✅ 图文笔记发布（最多9张图）
- ✅ 视频笔记发布
- ✅ 智能Emoji增强
- ✅ 话题标签（最多10个）

**使用流程**:
1. 输入账号ID、手机号、密码
2. 点击"登录并保存Cookie"
3. 选择笔记类型（图文/视频）
4. 上传内容并发布

---

## 🔧 Phase 3: 批量注册（1个）

### 5. 批量注册
**地址**: http://localhost:3001/batch-register

**功能**:
- ✅ SMS接码平台集成
- ✅ OCR验证码识别
- ✅ 批量账号注册
- ✅ 账号列表管理

**配置要求**:
```bash
# 需要在.env中配置（可选）
SMS_ACTIVATE_API_KEY=your_key_here
CAPTCHA_SOLVER_API_KEY=your_key_here
```

**使用流程**:
1. 选择目标平台（抖音/快手/小红书/B站）
2. 设置注册数量（1-50个）
3. 选择SMS平台（SMS Activate/5SIM/SMSHub）
4. 输入SMS API密钥
5. 点击"开始批量注册"
6. 查看注册结果和账号列表

---

## 🎨 Phase 6: AI配图生成（1个）

### 6. AI配图生成 ⭐NEW
**地址**: http://localhost:3001/image-generation

**功能**:
- ✅ 单张图像生成
- ✅ 批量图像生成
- ✅ 文章自动配图
- ✅ 7种艺术风格
- ✅ 5种宽高比

**配置要求**:
```bash
# 必须在.env中配置至少一个API密钥
STABILITY_AI_API_KEY=your_stability_key_here
OPENAI_API_KEY=your_openai_key_here
```

**获取API密钥**:

**Stability AI**（推荐，性价比高）:
1. 访问 https://platform.stability.ai/
2. 注册账号
3. 获取API密钥
4. 免费额度：每月25次生成

**OpenAI DALL-E 3**:
1. 访问 https://platform.openai.com/
2. 注册账号
3. 创建API密钥
4. 费用：$0.04/张（1024x1024）

**使用流程 - 单张生成**:
1. 输入图像描述（英文效果更好）
   - 例如："A beautiful sunset over mountains with clouds"
2. 选择风格（写实/插画/卡通/动漫/油画/水彩/极简）
3. 选择宽高比（16:9/9:16/1:1/3:4）
4. 点击"生成图像"
5. 等待10-30秒，查看预览

**使用流程 - 文章配图**:
1. 粘贴文章内容到文本框
2. 设置配图数量（1-10张）
3. 选择风格
4. 点击"自动生成配图"
5. 系统自动提取关键点并生成配图
6. 查看生成的所有配图

---

## 📊 其他核心页面

### 已有页面清单

| 页面名称 | 访问地址 | 功能说明 |
|---------|---------|---------|
| 账号管理 | http://localhost:3001/accounts | 统一管理所有平台账号 |
| 内容创作 | http://localhost:3001/content | AI文案生成 |
| 头条账号 | http://localhost:3001/toutiao | 头条文章发布 |
| 抖音账号 | http://localhost:3001/douyin | 抖音视频发布 |
| 热点监控 | http://localhost:3001/hot-trend | 4平台热点实时监控 |
| 视觉合成 | http://localhost:3001/visual-synthesis | 封面生成+字幕+BGM |
| 视频重组 | http://localhost:3001/video-restructure | AI视频结构重组 |
| 发布记录 | http://localhost:3001/publish-records | 查看所有发布记录 |
| 报警中心 | http://localhost:3001/alert-center | 系统告警管理 |
| SMS配置 | http://localhost:3001/sms-config | SMS接码平台配置 |
| 智能调度 | http://localhost:3001/schedule | 定时发布任务 |

---

## 🗺️ 完整路由地图

```
Smart-Toolbox 前端路由结构
│
├── 认证相关
│   ├── /login - 登录页
│   └── /register - 注册页
│
├── 核心功能
│   ├── /dashboard - 仪表盘
│   ├── /accounts - 账号管理
│   ├── /content - 内容创作
│   └── /schedule - 智能调度
│
├── 平台专属（Phase 1-2）
│   ├── /toutiao - 头条账号
│   ├── /douyin - 抖音账号
│   ├── /kuaishou - 快手账号 ⭐NEW
│   ├── /wechat - 视频号账号 ⭐NEW
│   ├── /bilibili - B站发布 ⭐NEW
│   └── /xiaohongshu - 小红书发布 ⭐NEW
│
├── 批量操作（Phase 3）
│   └── /batch-register - 批量注册 ⭐NEW
│
├── AI功能（Phase 6）
│   └── /image-generation - AI配图生成 ⭐NEW
│
├── 内容处理
│   ├── /visual-synthesis - 视觉合成
│   └── /video-restructure - 视频重组
│
├── 数据监控
│   ├── /hot-trend - 热点监控
│   ├── /publish-records - 发布记录
│   └── /alert-center - 报警中心
│
└── 系统配置
    └── /sms-config - SMS配置
```

---

## 🔍 页面功能对比

### 多平台发布能力

| 平台 | 登录方式 | 视频发布 | 图文发布 | 特色功能 |
|------|---------|---------|---------|---------|
| 头条 | 密码 | ❌ | ✅ | 文章自动发布 |
| 抖音 | 扫码 | ✅ | ❌ | 短视频发布 |
| 快手 | 密码 | ✅ | ✅ | 双模式支持 |
| 视频号 | 扫码 | ✅ | ❌ | 位置+话题 |
| B站 | 扫码 | ✅ | ✅ | 原创/转载 |
| 小红书 | 密码 | ✅ | ✅ | Emoji增强 |

---

## 💡 使用建议

### 新手入门流程

1. **第一步：注册登录**
   - 访问 http://localhost:3001/register
   - 创建账号并登录

2. **第二步：体验AI配图**
   - 访问 http://localhost:3001/image-generation
   - 配置API密钥
   - 尝试生成第一张AI图片

3. **第三步：绑定账号**
   - 选择要运营的平台
   - 访问对应平台页面（如/kuaishou）
   - 登录并保存Cookie

4. **第四步：创作内容**
   - 访问 http://localhost:3001/content
   - 输入主题，AI生成文案
   - 使用AI配图生成插图

5. **第五步：发布内容**
   - 回到平台页面
   - 填写发布信息
   - 一键发布

### 高级用户技巧

**批量注册账号**:
- 访问 /batch-register
- 配置SMS API
- 一次性注册多个账号

**文章自动配图**:
- 在 /image-generation 粘贴文章
- 自动生成3-5张配图
- 下载后用于发布

**多平台同步发布**:
- 准备一份内容
- 依次访问各平台页面
- 快速发布到所有平台

---

## ⚙️ 环境配置检查

### 必需配置

**后端环境变量** (`.env`):
```bash
# AI配图生成（至少配置一个）
STABILITY_AI_API_KEY=sk-xxx
OPENAI_API_KEY=sk-xxx

# SMS接码（批量注册需要）
SMS_ACTIVATE_API_KEY=xxx

# 其他已有配置
DATABASE_URL=mysql://...
REDIS_URL=redis://...
```

**前端启动**:
```bash
cd frontend
npm install
npm run dev
```

**后端启动**:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Celery Worker**（异步任务需要）:
```bash
celery -A app.tasks.celery_app worker --loglevel=info
```

---

## 🎊 总结

### 已完成页面统计

| 类别 | 数量 | 页面列表 |
|------|------|---------|
| **认证页面** | 2 | 登录、注册 |
| **核心页面** | 4 | 仪表盘、账号管理、内容创作、智能调度 |
| **平台页面** | 6 | 头条、抖音、快手、视频号、B站、小红书 |
| **批量操作** | 1 | 批量注册 |
| **AI功能** | 1 | AI配图生成 ⭐NEW |
| **内容处理** | 2 | 视觉合成、视频重组 |
| **数据监控** | 3 | 热点监控、发布记录、报警中心 |
| **系统配置** | 1 | SMS配置 |
| **总计** | **20个** | - |

### 新增页面（本次完成）

✅ `/kuaishou` - 快手账号管理  
✅ `/wechat` - 视频号账号管理  
✅ `/bilibili` - B站发布  
✅ `/xiaohongshu` - 小红书发布  
✅ `/batch-register` - 批量注册  
✅ `/image-generation` - AI配图生成  

**共6个新页面已全部配置完成！**

---

**🎉 所有前端页面已配置完成，可以立即访问使用！**

**访问 http://localhost:3001 开始体验完整的自媒体智能工具平台！** 🚀
