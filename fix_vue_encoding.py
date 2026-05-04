#!/usr/bin/env python3
"""
修复Vue文件的编码问题
尝试多种编码方式读取并转换为UTF-8
"""
import os
import chardet

files_to_fix = [
    'frontend/src/views/ToutiaoAccount.vue',
    'frontend/src/views/KuaishouAccount.vue',
    'frontend/src/views/WechatAccount.vue',
    'frontend/src/views/BilibiliPublish.vue',
    'frontend/src/views/XiaohongshuPublish.vue',
    'frontend/src/views/AccountManagement.vue',
]

def fix_encoding(file_path):
    """检测并修复文件编码"""
    if not os.path.exists(file_path):
        print(f"✗ 文件不存在: {file_path}")
        return False
    
    # 读取原始字节
    with open(file_path, 'rb') as f:
        raw_data = f.read()
    
    # 检测编码
    result = chardet.detect(raw_data)
    detected_encoding = result['encoding']
    confidence = result['confidence']
    
    print(f"\n处理文件: {file_path}")
    print(f"  检测到编码: {detected_encoding} (置信度: {confidence:.2f})")
    
    # 尝试用检测到的编码读取
    try:
        if detected_encoding:
            content = raw_data.decode(detected_encoding, errors='ignore')
        else:
            content = raw_data.decode('utf-8', errors='ignore')
        
        # 写回UTF-8（无BOM）
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"  ✓ 修复成功")
        return True
        
    except Exception as e:
        print(f"  ✗ 修复失败: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("开始修复Vue文件编码...")
    print("=" * 60)
    
    success_count = 0
    for file_path in files_to_fix:
        if fix_encoding(file_path):
            success_count += 1
    
    print("\n" + "=" * 60)
    print(f"修复完成: {success_count}/{len(files_to_fix)} 个文件")
    print("=" * 60)
