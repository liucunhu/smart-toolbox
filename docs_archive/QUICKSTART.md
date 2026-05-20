# Smart-Toolbox 快速启动指南（修复后版本）

## 🚀 快速开始

### 1. 环境准备

#### 前置要求
- Python 3.10+
- Node.js 16+
- Docker & Docker Compose（可选，推荐）

### 2. 后端启动

#### 方式一：Docker Compose（推荐）

```bash
# 1. 复制环境变量配置
cp .env.example .env

# 2. 编辑 .env 文件，修改以下必填项：
# - DATABASE_URL
# - REDIS_URL
# - CELERY_BROKER_URL
# - SECRET_KEY（生产环境必须修改）
# - SILICONFLOW_API_KEY（或其他AI提供商密钥）

# 3. 启动所有服务
docker-compose up -d

# 4. 查看日志
docker-compose logs -f web

# 5. 访问应用
# API文档: http://localhost:8000/docs
# 健康检查: http://localhost:8000/api/v1/health
# 前端界面: http://localhost:3000
```

#### 方式二：本地开发

```bash
# 1. 安装Python依赖
pip install -r requirements.txt

# 2. 安装Playwright浏览器
playwright install chromium

# 3. 复制并配置环境变量
cp .env.example .env
# 编辑 .env 文件

# 4. 启动MySQL和Redis（如果未使用Docker）
# 建议使用Docker单独启动基础设施
docker-compose -f docker-compose-infra.yml up -d

# 5. 启动FastAPI服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 6. 启动Celery Worker（新终端）
celery -A app.tasks.celery_app worker --loglevel=info

# 7. 访问API文档
# http://localhost:8000/docs
```

### 3. 前端启动

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 配置环境变量（可选）
# 已创建 .env 文件，默认指向 http://localhost:8000/api/v1
# 如需修改，编辑 frontend/.env 文件

# 4. 启动开发服务器
npm run dev

# 5. 访问前端界面
# http://localhost:3000
```

### 4. 验证安装

#### 检查后端健康状态
```bash
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
  "version": "1.0.0"
}
```

#### 测试API端点
```bash
# 访问Swagger文档
open http://localhost:8000/docs

# 测试文案生成
curl -X POST "http://localhost:8000/api/v1/content/generate?topic=Python自动化&platform=douyin"
```

---

## ⚙️ 配置说明

### 环境变量详解

#### 必需配置
```env
# 数据库连接
DATABASE_URL=mysql+pymysql://root:password@localhost:3306/smart_toolbox?charset=utf8mb4

# Redis连接
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2

# JWT密钥（生产环境必须修改为随机字符串）
SECRET_KEY=your-super-secret-key-change-in-production-min-32-chars
```

#### AI提供商配置（至少选择一个）
```env
# 硅基流动（推荐）
LLM_PROVIDER=siliconflow
SILICONFLOW_API_KEY=sk-xxx

# 或魔搭社区
# LLM_PROVIDER=modelscope
# MODELSCOPE_API_KEY=xxx

# 或DeepSeek
# LLM_PROVIDER=deepseek
# DEEPSEEK_API_KEY=sk-xxx

# 或OpenAI
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-xxx
```

#### 可选配置
```env
# CORS允许的域名（多个用逗号分隔）
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]

# 代理池（用于RPA）
PROXY_POOL_URL=http://your-proxy-service
```

---

## 🔧 常见问题

### 1. 数据库连接失败

**问题**: `Can't connect to MySQL server`

**解决**:
```bash
# 检查MySQL是否运行
docker ps | grep mysql

# 查看MySQL日志
docker logs smart-toolbox-db

# 重启MySQL容器
docker-compose restart db
```

### 2. Redis连接失败

**问题**: `Error connecting to Redis`

**解决**:
```bash
# 检查Redis是否运行
docker ps | grep redis

# 测试Redis连接
docker exec -it smart-toolbox-redis redis-cli ping
# 应返回 PONG
```

### 3. Celery Worker未启动

**问题**: 任务一直处于pending状态

**解决**:
```bash
# 检查Worker是否运行
docker ps | grep worker

# 查看Worker日志
docker logs smart-toolbox-worker

# 重启Worker
docker-compose restart worker
```

### 4. 前端无法连接后端

**问题**: `Network Error` 或 `CORS error`

**解决**:
```bash
# 1. 检查后端是否运行
curl http://localhost:8000/api/v1/health

# 2. 检查CORS配置
# 确保 .env 中 BACKEND_CORS_ORIGINS 包含前端地址

# 3. 清除浏览器缓存并刷新
```

### 5. RPA浏览器启动失败

**问题**: `Browser executable not found`

**解决**:
```bash
# 重新安装Playwright浏览器
playwright install chromium
playwright install-deps
```

---

## 📊 监控和维护

### 健康检查

```bash
# 综合健康检查
curl http://localhost:8000/api/v1/health

# 单独检查组件
curl http://localhost:8000/api/v1/health/db
curl http://localhost:8000/api/v1/health/redis
curl http://localhost:8000/api/v1/health/celery
```

### 日志查看

```bash
# 后端日志
docker logs -f smart-toolbox-web

# Worker日志
docker logs -f smart-toolbox-worker

# 前端日志
docker logs -f smart-toolbox-frontend

# 查看所有日志
docker-compose logs -f
```

### 数据备份

```bash
# 备份MySQL数据
docker exec smart-toolbox-db mysqldump -u root -p smart_toolbox > backup.sql

# 恢复数据
docker exec -i smart-toolbox-db mysql -u root -p smart_toolbox < backup.sql
```

---

## 🛠️ 开发工具

### API测试

使用Swagger UI:
```
http://localhost:8000/docs
```

或使用ReDoc:
```
http://localhost:8000/redoc
```

### 数据库管理

推荐使用以下工具连接MySQL:
- **DBeaver** (免费)
- **Navicat** (付费)
- **MySQL Workbench** (官方)

连接信息:
```
Host: localhost
Port: 3306
Database: smart_toolbox
Username: root
Password: (从.env中的DATABASE_URL获取)
```

### Redis管理

```bash
# 命令行客户端
docker exec -it smart-toolbox-redis redis-cli

# GUI工具: Redis Insight (免费)
```

---

## 📝 下一步

1. **阅读文档**
   - [产品需求文档](docs/Smart-Toolbox_产品需求文档_PRD.md)
   - [技术架构文档](docs/Smart-Toolbox_技术架构设计文档.md)
   - [修复报告](FIXES_REPORT.md)

2. **配置AI提供商**
   - 注册硅基流动账号: https://siliconflow.cn
   - 获取API Key并配置到.env

3. **创建第一个账号**
   - 访问 http://localhost:3000/accounts
   - 选择平台，输入手机号，开始注册

4. **生成第一条内容**
   - 访问 http://localhost:3000/content
   - 输入主题，选择平台，点击生成

---

## 🆘 获取帮助

### 文档资源
- 项目文档: `docs/` 目录
- API文档: http://localhost:8000/docs
- 修复报告: `FIXES_REPORT.md`

### 社区支持
- GitHub Issues: （待添加）
- 技术交流群: （待添加）

---

**最后更新**: 2026年4月30日  
**版本**: V1.0.1 (修复版)
