# Smart Toolbox 一键启动脚本
# 此脚本会启动所有必要的服务

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Smart Toolbox 服务启动脚本" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查 Docker 是否运行
Write-Host "[1/5] 检查 Docker 服务..." -ForegroundColor Yellow
try {
    $dockerStatus = docker info 2>&1
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Docker 未运行，请先启动 Docker Desktop" -ForegroundColor Red
        exit 1
    }
    Write-Host "✅ Docker 服务正常" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker 检查失败" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. 启动中间件（MySQL + Redis）
Write-Host "[2/5] 启动中间件服务（MySQL + Redis）..." -ForegroundColor Yellow
docker-compose -f docker-compose-infra.yml up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "✅ 中间件服务启动成功" -ForegroundColor Green
} else {
    Write-Host "❌ 中间件服务启动失败" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 3. 等待中间件就绪
Write-Host "[3/5] 等待中间件就绪..." -ForegroundColor Yellow
Write-Host "   等待 MySQL 和 Redis 健康检查通过..." -ForegroundColor Gray
Start-Sleep -Seconds 10

# 检查 MySQL
Write-Host "   检查 MySQL 连接..." -ForegroundColor Gray
$mysqlReady = $false
for ($i = 1; $i -le 10; $i++) {
    try {
        $result = docker exec smart-toolbox-mysql mysqladmin ping -h localhost 2>&1
        if ($result -match "mysqld is alive") {
            $mysqlReady = $true
            break
        }
    } catch {}
    Write-Host "   尝试 $i/10..." -ForegroundColor Gray
    Start-Sleep -Seconds 2
}

if ($mysqlReady) {
    Write-Host "   ✅ MySQL 已就绪" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  MySQL 可能还未完全就绪，继续启动其他服务..." -ForegroundColor Yellow
}

# 检查 Redis
Write-Host "   检查 Redis 连接..." -ForegroundColor Gray
try {
    $redisResult = docker exec smart-toolbox-redis redis-cli -a RedisPass123 ping 2>&1
    if ($redisResult -match "PONG") {
        Write-Host "   ✅ Redis 已就绪" -ForegroundColor Green
    } else {
        Write-Host "   ⚠️  Redis 响应异常" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ⚠️  Redis 检查失败" -ForegroundColor Yellow
}
Write-Host ""

# 4. 提示启动后端和前端
Write-Host "[4/5] 后端和前端服务需要手动启动：" -ForegroundColor Yellow
Write-Host ""
Write-Host "   请在新的 PowerShell 窗口中执行以下命令：" -ForegroundColor Cyan
Write-Host ""
Write-Host "   终端 1 - 后端服务:" -ForegroundColor White
Write-Host "   python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "   终端 2 - Celery Worker:" -ForegroundColor White
Write-Host "   celery -A app.tasks.celery_app worker --loglevel=info --pool=solo" -ForegroundColor Gray
Write-Host ""
Write-Host "   终端 3 - 前端服务:" -ForegroundColor White
Write-Host "   cd frontend" -ForegroundColor Gray
Write-Host "   npm run dev" -ForegroundColor Gray
Write-Host ""

# 5. 显示访问地址
Write-Host "[5/5] 服务访问地址：" -ForegroundColor Yellow
Write-Host ""
Write-Host "   🌐 前端应用: http://localhost:3000" -ForegroundColor Cyan
Write-Host "   🔧 后端 API:  http://localhost:8000" -ForegroundColor Cyan
Write-Host "   📚 API 文档:  http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "   💾 MySQL:      localhost:3306" -ForegroundColor Gray
Write-Host "   🔴 Redis:      localhost:6379" -ForegroundColor Gray
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  启动完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "💡 提示: 查看 SERVICES_RUNNING_REPORT.md 获取详细信息" -ForegroundColor Yellow
Write-Host ""
