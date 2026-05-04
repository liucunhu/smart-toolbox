# Smart-Toolbox 服务启动指南

## 🚀 快速启动（不含数据库和Redis）

### 前提条件

1. **Python 3.10+** 已安装
2. **Node.js 16+** 已安装
3. **远程数据库和Redis** 已配置在 `.env` 文件中

---

## 📋 启动步骤

### 方式一：使用启动脚本（推荐）

```powershell
# 在项目根目录执行
.\start_services.ps1
```

脚本会自动：
- ✅ 检查Python环境
- ✅ 安装依赖包
- ✅ 启动后端API (端口8000)
- ✅ 启动Celery Worker
- ✅ 启动前端服务 (端口3000)

---

### 方式二：手动分步启动

#### 1️⃣ 安装依赖

```powershell
# 后端依赖
pip install fastapi uvicorn sqlalchemy pymysql pydantic celery redis playwright openai python-dotenv loguru passlib bcrypt python-jose tenacity nest-asyncio opencv-python ffmpeg-python

# 前端依赖
cd frontend
npm install
cd ..
```

#### 2️⃣ 配置环境变量

编辑 `.env` 文件，配置远程数据库和Redis：

```env
# 数据库配置（使用远程服务）
DATABASE_URL=mysql+pymysql://username:password@remote-host:3306/smart_toolbox?charset=utf8mb4

# Redis配置（使用远程服务）
REDIS_URL=redis://:password@remote-host:6379/0
CELERY_BROKER_URL=redis://:password@remote-host:6379/1
CELERY_RESULT_BACKEND=redis://:password@remote-host:6379/2

# JWT配置
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
```

#### 3️⃣ 启动后端API

```powershell
# 在项目根目录
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

访问：
- API服务: http://localhost:8000
- API文档: http://localhost:8000/docs

#### 4️⃣ 启动Celery Worker（新终端窗口）

```powershell
# 在项目根目录
celery -A app.tasks.celery_app.celery_app worker --loglevel=info --pool=solo
```

#### 5️⃣ 启动前端服务（新终端窗口）

```powershell
# 进入前端目录
cd frontend

# 启动开发服务器
npm run dev
```

访问：
- 前端界面: http://localhost:3000

---

## 🔍 验证服务状态

### 检查后端API

```powershell
curl http://localhost:8000/api/v1/health
```

预期响应：
```json
{
  "status": "healthy",
  "components": {
    "database": "healthy",
    "redis": "healthy",
    "celery": "healthy"
  },
  "version": "1.0.2"
}
```

### 检查前端

浏览器访问 http://localhost:3000，应该看到登录页面。

---

## ⚠️ 常见问题

### 1. 端口被占用

**问题**: 端口8000或3000已被占用

**解决**:
```powershell
# 查找占用端口的进程
netstat -ano | findstr :8000
netstat -ano | findstr :3000

# 终止进程（替换PID为实际进程ID）
taskkill /F /PID <PID>
```

### 2. 依赖安装失败

**问题**: `paddlepaddle` 或 `paddleocr` 安装失败

**解决**: 这些是可选依赖，可以跳过：
```powershell
# 只安装核心依赖
pip install fastapi uvicorn sqlalchemy pymysql pydantic celery redis openai python-dotenv loguru passlib bcrypt python-jose tenacity nest-asyncio
```

### 3. 数据库连接失败

**问题**: 无法连接到远程数据库

**解决**:
1. 检查 `.env` 中的 `DATABASE_URL` 配置
2. 确认远程数据库允许外部访问
3. 检查防火墙设置

### 4. Redis连接失败

**问题**: 无法连接到远程Redis

**解决**:
1. 检查 `.env` 中的 `REDIS_URL` 配置
2. 确认Redis密码正确
3. 检查Redis是否允许外部访问

---

## 🛑 停止服务

### 方式一：使用Ctrl+C

在每个运行服务的终端窗口按 `Ctrl+C`

### 方式二：强制停止所有服务

```powershell
# 停止所有Python进程
Get-Process | Where-Object {$_.ProcessName -like "*python*"} | Stop-Process -Force

# 停止所有Node进程
Get-Process | Where-Object {$_.ProcessName -like "*node*"} | Stop-Process -Force
```

---

## 📊 服务清单

| 服务 | 端口 | 说明 | 必需 |
|------|------|------|------|
| **后端API** | 8000 | FastAPI应用 | ✅ |
| **Celery Worker** | - | 异步任务处理 | ✅ |
| **前端服务** | 3000 | Vue3开发服务器 | ✅ |
| **数据库** | 远程 | MySQL 8.0 | ✅ (远程) |
| **Redis** | 远程 | Redis 7.0 | ✅ (远程) |

---

## 🔗 相关链接

- **前端界面**: http://localhost:3000
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/api/v1/health

---

## 💡 提示

1. **首次启动**可能需要较长时间安装依赖
2. **开发模式**下代码修改会自动重载
3. **查看日志**可以排查问题
4. **确保**.env文件配置正确**

---

**祝使用愉快！** 🎉
