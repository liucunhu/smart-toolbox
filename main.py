from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import sys
import asyncio
from app.core.config import settings
from app.api.v1 import api_router
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.api.v1.content_tasks import router as content_tasks_router
from app.api.v1.new_features import router as new_features_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.webpack_hmr_router import router as webpack_hmr_router
from app.models import Base
from app.db.session import engine
from app.utils.logger import logger

# === Windows 事件循环修复 ===
# Playwright 需要创建子进程，Windows 默认 SelectorEventLoop 不支持 subprocess
# 必须在导入任何其他依赖前设置 ProactorEventLoop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 启动时检查数据库连接
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ 数据库连接成功并已完成表结构同步")
except Exception as e:
    logger.error(f"❌ 数据库连接失败：{e}")
    sys.exit(1)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    确保每个 worker 进程启动时都设置正确的事件循环策略
    """
    # Startup: 确保事件循环策略正确
    if sys.platform == 'win32':
        current_policy = asyncio.get_event_loop_policy()
        if not isinstance(current_policy, asyncio.WindowsProactorEventLoopPolicy):
            logger.info("🔧 检测到 worker 进程事件循环策略不正确，正在修复...")
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        
        # 检查当前事件循环类型
        current_loop = asyncio.get_running_loop()
        logger.info(f"🔍 当前事件循环类型: {type(current_loop).__name__}")
        if isinstance(current_loop, asyncio.ProactorEventLoop):
            logger.info("✅ Windows ProactorEventLoop 已确认（支持 Playwright 子进程）")
        else:
            logger.warning(f"⚠️  当前事件循环为 {type(current_loop).__name__}，Playwright 可能需要 ProactorEventLoop")
            logger.warning("   如果遇到 NotImplementedError，请重启服务并使用 python start_server.py")
    
    # 初始化智能体任务执行器 (Phase 4)
    try:
        from app.services.agents.executor_initializer import initialize_executors
        initialize_executors()
        logger.info("✅ 智能体任务执行器初始化成功")
    except Exception as e:
        logger.error(f"❌ 智能体任务执行器初始化失败: {str(e)}")
    
    yield  # 应用运行期间
    
    # Shutdown
    logger.info("👋 Smart-Toolbox 正在关闭...")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 配置 CORS（跨域资源共享）
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(auth_router, prefix="/api/v1")
app.include_router(api_router, prefix="/api/v1")
app.include_router(health_router, prefix="/api/v1")
app.include_router(content_tasks_router, prefix="/api/v1")
app.include_router(new_features_router, prefix="/api/v1")
app.include_router(analytics_router, prefix="/api/v1")
app.include_router(webpack_hmr_router)  # 注册 webpack HMR 路由

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart-Toolbox API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
