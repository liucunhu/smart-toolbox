# 批量替换硬编码API地址为apiClient
# 此脚本将所有Vue文件中的axios调用替换为apiClient

$files = @(
    "frontend\src\views\ABTestManagement.vue",
    "frontend\src\views\AccountNurturing.vue",
    "frontend\src\views\AlertCenter.vue",
    "frontend\src\views\BatchRegister.vue",
    "frontend\src\views\BilibiliPublish.vue",
    "frontend\src\views\ContentTasks.vue",
    "frontend\src\views\Dashboard.vue",
    "frontend\src\views\DouyinAccount.vue",
    "frontend\src\views\HotTrendMonitor.vue",
    "frontend\src\views\ImageGeneration.vue",
    "frontend\src\views\KuaishouAccount.vue",
    "frontend\src\views\SmsConfig.vue",
    "frontend\src\views\ToutiaoAccount.vue",
    "frontend\src\views\VideoRestructure.vue",
    "frontend\src\views\VisualSynthesis.vue",
    "frontend\src\views\WechatAccount.vue",
    "frontend\src\views\XiaohongshuPublish.vue"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "Processing: $file"
        
        # 读取文件内容
        $content = Get-Content $file -Raw -Encoding UTF8
        
        # 替换import语句
        $content = $content -replace "import axios from 'axios'", "import apiClient from '../utils/api'"
        
        # 替换硬编码URL (http://localhost:8000/api/v1/xxx -> /xxx)
        $content = $content -replace "http://localhost:8000/api/v1/", "/"
        
        # 替换axios.为apiClient.
        $content = $content -replace "\baxios\.", "apiClient."
        
        # 写回文件
        Set-Content $file -Value $content -Encoding UTF8 -NoNewline
        
        Write-Host "  ✓ Updated" -ForegroundColor Green
    } else {
        Write-Host "  ✗ File not found" -ForegroundColor Red
    }
}

Write-Host "`nAll files processed!" -ForegroundColor Cyan
