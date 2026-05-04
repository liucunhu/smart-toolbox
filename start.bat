@echo off
chcp 65001 >nul
echo ==========================================
echo   Smart-Toolbox 全栈启动脚本
echo ==========================================

REM 检查 .env 文件
if not exist .env (
    echo [警告] 未检测到 .env 文件，正在从 .env.example 复制...
    copy .env.example .env
    echo [提示] 请编辑 .env 文件填入运维提供的数据库和 Redis 地址！
    pause
)

REM 启动后端 API
echo [1/2] 正在启动 FastAPI 后端服务...
start "Smart-Toolbox-API" cmd /k "uvicorn main:app --reload --host 0.0.0.0 --port 8000"

REM 启动 Celery Worker
echo [2/2] 正在启动 Celery 异步任务队列...
start "Smart-Toolbox-Celery" cmd /k "celery -A app.tasks.celery_app worker --loglevel=info -P eventlet"

echo.
echo ✅ 所有服务已启动！
echo 🌐 前端请访问: http://localhost:3000
echo 🔧 后端文档请访问: http://localhost:8000/docs
echo.
pause
