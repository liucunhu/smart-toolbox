# Smart-Toolbox 服务启动脚本（不含数据库和Redis）
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Smart-Toolbox 服务启动" -ForegroundColor Cyan
Write-Host "  (排除数据库和Redis)" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查Python环境
Write-Host "[1/5] 检查Python环境..." -ForegroundColor Yellow
python --version
if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Python未找到，请先安装Python 3.10+" -ForegroundColor Red
    exit 1
}

# 安装依赖
Write-Host ""
Write-Host "[2/5] 安装依赖包..." -ForegroundColor Yellow
pip install fastapi uvicorn sqlalchemy pymysql pydantic celery redis playwright openai python-dotenv loguru passlib bcrypt python-jose tenacity nest-asyncio opencv-python ffmpeg-python -q

if ($LASTEXITCODE -ne 0) {
    Write-Host "⚠️  部分依赖安装失败，但将继续尝试启动" -ForegroundColor Yellow
}

# 启动后端API
Write-Host ""
Write-Host "[3/5] 启动后端API服务 (端口8000)..." -ForegroundColor Yellow
Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload" -WindowStyle Normal
Start-Sleep -Seconds 3
Write-Host "✅ 后端API已启动: http://localhost:8000" -ForegroundColor Green
Write-Host "   API文档: http://localhost:8000/docs" -ForegroundColor Green

# 启动Celery Worker
Write-Host ""
Write-Host "[4/5] 启动Celery Worker..." -ForegroundColor Yellow
Start-Process -FilePath "celery" -ArgumentList "-A", "app.tasks.celery_app.celery_app", "worker", "--loglevel=info", "--pool=solo" -WindowStyle Normal
Start-Sleep -Seconds 2
Write-Host "✅ Celery Worker已启动" -ForegroundColor Green

# 启动前端开发服务器
Write-Host ""
Write-Host "[5/5] 启动前端开发服务器 (端口3000)..." -ForegroundColor Yellow
Set-Location frontend
npm install --silent
Start-Process -FilePath "npm" -ArgumentList "run", "dev" -WindowStyle Normal
Set-Location ..
Start-Sleep -Seconds 3
Write-Host "✅ 前端服务已启动: http://localhost:3000" -ForegroundColor Green

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  所有服务启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "📍 服务地址:" -ForegroundColor Cyan
Write-Host "  • 前端界面: http://localhost:3000" -ForegroundColor White
Write-Host "  • 后端API:  http://localhost:8000" -ForegroundColor White
Write-Host "  • API文档:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "⚠️  注意: 数据库和Redis需要单独启动或使用远程服务" -ForegroundColor Yellow
Write-Host ""
Write-Host "按任意键停止所有服务..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# 停止所有服务
Write-Host ""
Write-Host "正在停止服务..." -ForegroundColor Yellow
Get-Process | Where-Object {$_.ProcessName -like "*python*" -or $_.ProcessName -like "*node*"} | Stop-Process -Force
Write-Host "所有服务已停止" -ForegroundColor Green
