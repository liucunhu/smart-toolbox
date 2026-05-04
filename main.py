from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.endpoints import router as api_router
from app.api.v1.health import router as health_router
from app.api.v1.auth import router as auth_router
from app.models import Base
from app.db.session import engine
from app.utils.logger import logger
import sys

# 启动时检查数据库连接
try:
    Base.metadata.create_all(bind=engine)
    logger.info("✅ 数据库连接成功并已完成表结构同步")
except Exception as e:
    logger.error(f"❌ 数据库连接失败：{e}")
    sys.exit(1)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc"
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

@app.get("/")
def read_root():
    return {"message": "Welcome to Smart-Toolbox API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
