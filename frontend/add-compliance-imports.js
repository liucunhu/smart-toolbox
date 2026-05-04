const fs = require('fs');
const path = require('path');

// 需要修复的文件列表
const filesToFix = [
    'src/views/ToutiaoAccount.vue',
    'src/views/KuaishouAccount.vue', 
    'src/views/WechatAccount.vue',
    'src/views/BilibiliPublish.vue',
    'src/views/XiaohongshuPublish.vue'
];

filesToFix.forEach(file => {
    const fullPath = path.join(__dirname, file);
    
    if (!fs.existsSync(fullPath)) {
        console.log(`✗ Not found: ${file}`);
        return;
    }
    
    let content = fs.readFileSync(fullPath, 'utf-8');
    
    // 检查是否已包含合规审查代码
    if (content.includes('ComplianceCheckDialog')) {
        console.log(`✓ Already fixed: ${file}`);
        return;
    }
    
    // 添加导入语句（在<script setup lang="ts">之后）
    const importScript = `import ComplianceCheckDialog from '@/components/ComplianceCheckDialog.vue'
import { checkContentCompliance } from '@/api/compliance'`;
    
    content = content.replace(
        /(<script setup lang="ts">)/,
        `$1\n${importScript}`
    );
    
    // 添加组件引用和待发布数据
    const refCode = `
const complianceDialog = ref<InstanceType<typeof ComplianceCheckDialog> | null>(null)
const pendingPublishData = ref<any>(null)
`;
    
    // 在第一个ref声明后添加
    content = content.replace(
        /(const \w+ = ref\([^)]+\))/,
        `$1${refCode}`
    );
    
    // 写入文件
    fs.writeFileSync(fullPath, content, 'utf-8');
    console.log(`✓ Fixed: ${file}`);
});

console.log('\nAll files processed!');
