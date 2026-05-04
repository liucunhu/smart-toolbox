const fs = require('fs');
const path = require('path');

const files = [
    'src/components/ComplianceCheckDialog.vue',
    'src/components/EditAccountDialog.vue',
    'src/components/DeleteAccountDialog.vue',
    'src/api/compliance.ts',
    'src/views/ToutiaoAccount.vue',
    'src/views/KuaishouAccount.vue',
    'src/views/WechatAccount.vue',
    'src/views/BilibiliPublish.vue',
    'src/views/XiaohongshuPublish.vue',
    'src/views/AccountManagement.vue'
];

files.forEach(file => {
    const fullPath = path.join(__dirname, file);
    if (fs.existsSync(fullPath)) {
        // 读取为Buffer，然后以utf-8写入（无BOM）
        const content = fs.readFileSync(fullPath, 'utf-8');
        fs.writeFileSync(fullPath, content, 'utf-8');
        console.log(`✓ Fixed: ${file}`);
    } else {
        console.log(`✗ Not found: ${file}`);
    }
});

console.log('\n所有文件编码修复完成！');
