const fs = require('fs');
const path = require('path');
const iconv = require('iconv-lite');

// 需要修复的文件
const filesToFix = [
    'src/views/ToutiaoAccount.vue',
];

console.log('=' .repeat(60));
console.log('开始修复Vue文件编码...');
console.log('=' .repeat(60));

filesToFix.forEach(file => {
    const fullPath = path.join(__dirname, file);
    
    if (!fs.existsSync(fullPath)) {
        console.log(`\n✗ 文件不存在: ${file}`);
        return;
    }
    
    console.log(`\n处理文件: ${file}`);
    
    // 读取原始字节
    const rawBuffer = fs.readFileSync(fullPath);
    console.log(`  文件大小: ${rawBuffer.length} bytes`);
    
    // 尝试多种编码
    const encodings = ['gbk', 'gb2312', 'cp936', 'utf-8'];
    let success = false;
    
    for (const encoding of encodings) {
        try {
            const decoded = iconv.decode(rawBuffer, encoding);
            
            // 检查是否包含合理的中文
            const chineseChars = decoded.match(/[\u4e00-\u9fa5]/g);
            if (chineseChars && chineseChars.length > 50) {
                console.log(`  ✓ 检测到正确编码: ${encoding} (中文字符: ${chineseChars.length})`);
                
                // 写回UTF-8
                fs.writeFileSync(fullPath, decoded, 'utf-8');
                console.log(`  ✓ 已转换为UTF-8并保存`);
                success = true;
                break;
            }
        } catch (e) {
            console.log(`  ✗ ${encoding} 解码失败`);
        }
    }
    
    if (!success) {
        console.log(`  ✗ 无法找到正确的编码`);
    }
});

console.log('\n' + '='.repeat(60));
console.log('修复完成！');
console.log('='.repeat(60));
