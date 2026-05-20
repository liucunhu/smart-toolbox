#!/usr/bin/env python3
"""
清理 Git 历史中的敏感信息
使用 git filter-repo 或 git filter-branch
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """执行命令并返回结果"""
    print(f"\n{'='*60}")
    print(f"执行: {description}")
    print(f"命令: {cmd}")
    print('='*60)
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=600
        )
        
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            if result.stdout:
                print(result.stdout[:1000])
            return True
        else:
            print(f"❌ {description} 失败")
            print(f"错误输出:\n{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"⏱️  {description} 超时")
        return False
    except Exception as e:
        print(f"❌ {description} 异常: {e}")
        return False

def main():
    print("🔧 Smart-Toolbox Git 历史敏感信息清理工具")
    print("="*60)
    
    # 定义需要替换的敏感信息
    replacements = {
        'sk-e28ba64c17ae4321a7d00620264e0a68': 'REMOVED_DASHSCOPE_KEY',
        'sk-fqwnoraqwzkwoppbvtrgyyvbpiserarsxyrsdvrwixjzfafx': 'REMOVED_SILICONFLOW_KEY',
        'ToolboxPass123': 'REMOVED_DB_PASSWORD',
        'RedisPass123': 'REMOVED_REDIS_PASSWORD',
        'Hspc@2024': 'REMOVED_TOUTIAO_PASSWORD'
    }
    
    print("\n将清理以下敏感信息:")
    for old, new in replacements.items():
        print(f"  {old[:20]}... → {new}")
    
    confirm = input("\n是否继续？(yes/no): ")
    if confirm.lower() != 'yes':
        print("操作已取消")
        return 1
    
    # 步骤1: 备份
    print("\n[步骤 1/5] 创建备份分支...")
    if not run_command("git branch backup-before-cleanup", "创建备份分支"):
        print("警告: 备份分支可能已存在")
    
    # 步骤2: 尝试使用 git-filter-repo（如果可用）
    print("\n[步骤 2/5] 检查 git-filter-repo...")
    has_filter_repo = run_command("git filter-repo --version", "检查 git-filter-repo")
    
    if has_filter_repo:
        print("✅ 找到 git-filter-repo，使用此工具")
        # 创建替换文件
        with open('replacement-map.txt', 'w', encoding='utf-8') as f:
            for old, new in replacements.items():
                f.write(f"{old}==>{new}\n")
        
        cmd = "git filter-repo --replace-text replacement-map.txt --force"
        if run_command(cmd, "使用 git-filter-repo 清理"):
            os.remove('replacement-map.txt')
        else:
            print("回退到 git filter-branch 方法")
            has_filter_repo = False
    
    if not has_filter_repo:
        print("⚠️  使用 git filter-branch 方法（较慢）")
        print("注意: 这将重写所有提交，可能需要几分钟...")
        
        # 为每个敏感词执行 filter-branch
        for i, (old, new) in enumerate(replacements.items(), 1):
            print(f"\n[步骤 3/{len(replacements)+2}] 替换 {i}/{len(replacements)}: {old[:20]}...")
            
            # 创建临时脚本
            script_content = f'''#!/bin/bash
# 替换文件内容
for file in $(find . -type f -name "*.md" -o -name "*.py" -o -name "*.txt" -o -name "*.json" -o -name "*.yaml" -o -name "*.yml"); do
    if grep -q "{old}" "$file" 2>/dev/null; then
        sed -i 's/{old}/{new}/g' "$file"
    fi
done
'''
            with open('temp_cleanup.sh', 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            cmd = f'git filter-branch --force --tree-filter "bash temp_cleanup.sh" --tag-name-filter cat -- --all'
            run_command(cmd, f"替换 {old[:20]}...")
            
            if os.path.exists('temp_cleanup.sh'):
                os.remove('temp_cleanup.sh')
    
    # 步骤3: 清理引用
    print(f"\n[步骤 {len(replacements)+3}/5] 清理 Git 引用...")
    run_command("git for-each-ref --format='delete %(refname)' refs/original/ | git update-ref --stdin", "清理原始引用")
    
    # 步骤4: 清理 reflog 和垃圾回收
    print(f"\n[步骤 {len(replacements)+4}/5] 垃圾回收...")
    run_command("git reflog expire --expire=now --all", "过期 reflog")
    run_command("git gc --prune=now --aggressive", "垃圾回收")
    
    # 步骤5: 验证
    print(f"\n[步骤 {len(replacements)+5}/5] 验证清理结果...")
    verification_cmd = 'git log -p --all'
    for old in replacements.keys():
        verification_cmd += f' | Select-String "{old}"'
    
    result = subprocess.run(verification_cmd, shell=True, capture_output=True, text=True)
    if result.stdout.strip():
        print(f"⚠️  警告: 仍发现 {len(result.stdout.splitlines())} 处包含敏感信息")
        print("建议手动检查或使用 BFG Repo-Cleaner")
    else:
        print("✅ 验证通过！未发现敏感信息")
    
    print("\n" + "="*60)
    print("🎉 清理完成！")
    print("="*60)
    print("\n下一步:")
    print("1. 检查当前代码是否正常: git status")
    print("2. 如果确认无误，强制推送到远程:")
    print("   git push origin --force --all")
    print("   git push origin --force --tags")
    print("3. 通知所有团队成员重新克隆仓库")
    print("\n⚠️  重要: 立即轮换所有泄露的密钥！")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
