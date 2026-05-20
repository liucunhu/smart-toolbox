# 数据库迁移执行脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  执行数据库迁移" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 检查alembic是否安装
Write-Host "[1/3] 检查Alembic..." -ForegroundColor Yellow
alembic --version

if ($LASTEXITCODE -ne 0) {
    Write-Host "Alembic未安装，正在安装..." -ForegroundColor Red
    pip install alembic
}

# 显示当前版本
Write-Host ""
Write-Host "[2/3] 当前数据库版本:" -ForegroundColor Yellow
alembic current

# 执行升级
Write-Host ""
Write-Host "[3/3] 执行数据库迁移..." -ForegroundColor Yellow
alembic upgrade head

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  数据库迁移成功！" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    
    # 显示最新版本
    Write-Host ""
    Write-Host "最新版本:" -ForegroundColor Cyan
    alembic current
} else {
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Red
    Write-Host "  数据库迁移失败！" -ForegroundColor Red
    Write-Host "========================================" -ForegroundColor Red
    exit 1
}
