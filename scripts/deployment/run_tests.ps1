# 全链路测试执行脚本
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Smart-Toolbox 全链路测试验证" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 检查依赖
Write-Host "[1/6] 检查并安装测试依赖..." -ForegroundColor Yellow
pip install pytest httpx pytest-asyncio -q

# 2. 运行单元测试
Write-Host ""
Write-Host "[2/6] 运行核心Service层单元测试..." -ForegroundColor Yellow
python -m pytest tests/test_services.py -v --tb=short

# 3. 运行AC过滤器测试
Write-Host ""
Write-Host "[3/6] 运行违禁词过滤器测试..." -ForegroundColor Yellow
python -m pytest tests/test_ac_filter.py -v --tb=short

# 4. 运行调度器测试
Write-Host ""
Write-Host "[4/6] 运行智能调度器测试..." -ForegroundColor Yellow
python -m pytest tests/test_operations.py -v --tb=short

# 5. 运行RPA测试
Write-Host ""
Write-Host "[5/6] 运行RPA引擎测试..." -ForegroundColor Yellow
python -m pytest tests/test_rpa.py -v --tb=short

# 6. 运行分发策略测试
Write-Host ""
Write-Host "[6/6] 运行分发策略测试..." -ForegroundColor Yellow
python -m pytest tests/test_distribution.py -v --tb=short

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  测试执行完成！" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
