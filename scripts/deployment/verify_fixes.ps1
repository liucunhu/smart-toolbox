# 验证所有修复是否正确应用

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Smart-Toolbox 代码修复验证" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. 验证前端API客户端
Write-Host "1. 检查API客户端文件..." -ForegroundColor Yellow
if (Test-Path "frontend\src\utils\api.ts") {
    Write-Host "   ✅ api.ts 已创建" -ForegroundColor Green
} else {
    Write-Host "   ❌ api.ts 不存在" -ForegroundColor Red
}

# 2. 验证axios导入是否已替换
Write-Host "`n2. 检查axios导入..." -ForegroundColor Yellow
$axiosImports = Select-String -Path "frontend\src\**\*.vue" -Pattern "from 'axios'" -List
if ($axiosImports.Count -eq 0) {
    Write-Host "   ✅ 所有Vue文件已移除axios导入" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  发现 $($axiosImports.Count) 个文件仍使用axios" -ForegroundColor Yellow
}

# 3. 验证硬编码URL
Write-Host "`n3. 检查硬编码API地址..." -ForegroundColor Yellow
$hardcodedUrls = Select-String -Path "frontend\src\views\*.vue" -Pattern "http://localhost:8000/api/v1" | 
    Where-Object { $_.Line -notmatch "import.meta.env" }
if ($hardcodedUrls.Count -eq 0) {
    Write-Host "   ✅ 无硬编码API地址" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  发现 $($hardcodedUrls.Count) 处硬编码URL" -ForegroundColor Yellow
    $hardcodedUrls | ForEach-Object { Write-Host "      - $($_.Path)" -ForegroundColor Gray }
}

# 4. 验证后端Pydantic模型
Write-Host "`n4. 检查Pydantic验证模型..." -ForegroundColor Yellow
if (Test-Path "app\schemas\account.py") {
    Write-Host "   ✅ account.py 已创建" -ForegroundColor Green
    
    # 检查关键类是否存在
    $content = Get-Content "app\schemas\account.py" -Raw
    if ($content -match "class AccountUpdateRequest") {
        Write-Host "   ✅ AccountUpdateRequest 已定义" -ForegroundColor Green
    }
    if ($content -match "class AccountLoginRequest") {
        Write-Host "   ✅ AccountLoginRequest 已定义" -ForegroundColor Green
    }
    if ($content -match "@validator") {
        Write-Host "   ✅ 自定义验证器已添加" -ForegroundColor Green
    }
} else {
    Write-Host "   ❌ account.py 不存在" -ForegroundColor Red
}

# 5. 验证Celery任务修复
Write-Host "`n5. 检查Celery任务会话管理..." -ForegroundColor Yellow
$taskContent = Get-Content "app\tasks\account_tasks.py" -Raw
if ($taskContent -match "db\.commit\(\)") {
    Write-Host "   ✅ db.commit() 已添加" -ForegroundColor Green
} else {
    Write-Host "   ❌ 缺少 db.commit()" -ForegroundColor Red
}

if ($taskContent -match "db\.rollback\(\)") {
    Write-Host "   ✅ db.rollback() 已添加" -ForegroundColor Green
} else {
    Write-Host "   ⚠️  缺少 db.rollback()" -ForegroundColor Yellow
}

# 6. Python语法检查
Write-Host "`n6. Python语法检查..." -ForegroundColor Yellow
$pythonFiles = @(
    "app\schemas\account.py",
    "app\tasks\account_tasks.py",
    "app\api\v1\endpoints.py"
)

foreach ($file in $pythonFiles) {
    if (Test-Path $file) {
        $result = python -m py_compile $file 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ $file 语法正确" -ForegroundColor Green
        } else {
            Write-Host "   ❌ $file 语法错误" -ForegroundColor Red
        }
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "验证完成！" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
