# 修复所有Vue和TS文件的编码为UTF-8无BOM
$files = @(
    'src\components\ComplianceCheckDialog.vue',
    'src\components\EditAccountDialog.vue',
    'src\components\DeleteAccountDialog.vue',
    'src\api\compliance.ts',
    'src\views\ToutiaoAccount.vue',
    'src\views\KuaishouAccount.vue',
    'src\views\WechatAccount.vue',
    'src\views\BilibiliPublish.vue',
    'src\views\XiaohongshuPublish.vue',
    'src\views\AccountManagement.vue'
)

foreach ($file in $files) {
    $fullPath = Join-Path $PSScriptRoot $file
    if (Test-Path $fullPath) {
        # 读取内容
        $content = Get-Content $fullPath -Raw -Encoding UTF8
        # 写入UTF-8无BOM
        $utf8NoBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllText($fullPath, $content, $utf8NoBom)
        Write-Host "✓ Fixed: $file"
    } else {
        Write-Host "✗ Not found: $file"
    }
}

Write-Host "`n所有文件编码修复完成！" -ForegroundColor Green
