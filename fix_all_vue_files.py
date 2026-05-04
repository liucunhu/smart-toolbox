#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
批量修复所有损坏的Vue文件编码
使用GBK解码原始字节，然后转为UTF-8
"""
import os

files_to_fix = [
    'frontend/src/views/KuaishouAccount.vue',
    'frontend/src/views/WechatAccount.vue',
    'frontend/src/views/BilibiliPublish.vue',
    'frontend/src/views/XiaohongshuPublish.vue',
    'frontend/src/views/AccountManagement.vue',
]

print('=' * 60)
print('开始批量修复Vue文件编码...')
print('=' * 60)

for file_path in files_to_fix:
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    
    if not os.path.exists(full_path):
        print(f'\n✗ 文件不存在: {file_path}')
        continue
    
    print(f'\n处理文件: {file_path}')
    
    # 读取原始字节
    with open(full_path, 'rb') as f:
        raw_bytes = f.read()
    
    print(f'  文件大小: {len(raw_bytes)} bytes')
    
    # 尝试用GBK解码
    try:
        content = raw_bytes.decode('gbk')
        
        # 检查中文字符数量
        chinese_chars = [c for c in content if '\u4e00' <= c <= '\u9fff']
        print(f'  ✓ GBK解码成功 (中文字符: {len(chinese_chars)})')
        
        # 写回UTF-8
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f'  ✓ 已转换为UTF-8并保存')
        
    except Exception as e:
        print(f'  ✗ 修复失败: {e}')

print('\n' + '=' * 60)
print('修复完成！')
print('=' * 60)
