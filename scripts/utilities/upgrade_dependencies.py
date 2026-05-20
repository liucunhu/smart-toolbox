#!/usr/bin/env python3
"""
依赖升级验证脚本
检查依赖更新后的兼容性
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: str, description: str) -> bool:
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
            timeout=300
        )
        
        if result.returncode == 0:
            print(f"✅ {description} 成功")
            if result.stdout:
                print(result.stdout[:500])  # 只显示前500字符
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
    print("🔧 Smart-Toolbox 依赖升级验证")
    print("="*60)
    
    steps = [
        ("pip install --upgrade pip", "升级 pip"),
        ("pip install -r requirements.txt", "安装更新的依赖"),
        ("python -c \"import fastapi; print(f'FastAPI: {fastapi.__version__}')\"", "验证 FastAPI"),
        ("python -c \"import pydantic; print(f'Pydantic: {pydantic.__version__}')\"", "验证 Pydantic"),
        ("python -c \"import sqlalchemy; print(f'SQLAlchemy: {sqlalchemy.__version__}')\"", "验证 SQLAlchemy"),
        ("python -c \"import celery; print(f'Celery: {celery.__version__}')\"", "验证 Celery"),
        ("python -c \"import playwright; print('Playwright installed')\"", "验证 Playwright"),
        ("python -c \"import openai; print(f'OpenAI: {openai.__version__}')\"", "验证 OpenAI"),
        ("python -c \"import requests; print(f'Requests: {requests.__version__}')\"", "验证 Requests"),
        ("python -c \"import PIL; print(f'Pillow: {PIL.__version__}')\"", "验证 Pillow"),
        ("python -c \"import numpy; print(f'NumPy: {numpy.__version__}')\"", "验证 NumPy"),
    ]
    
    results = []
    for cmd, desc in steps:
        success = run_command(cmd, desc)
        results.append((desc, success))
    
    # 打印总结
    print("\n" + "="*60)
    print("📊 验证总结")
    print("="*60)
    
    all_success = True
    for desc, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {desc}")
        if not success:
            all_success = False
    
    print("="*60)
    if all_success:
        print("🎉 所有依赖升级成功！")
        print("\n下一步:")
        print("1. 运行测试: pytest tests/")
        print("2. 启动服务验证功能")
        print("3. 提交更改到 Git")
        return 0
    else:
        print("⚠️  部分依赖升级失败，请检查错误信息")
        print("\n建议:")
        print("1. 查看上述错误输出")
        print("2. 可能需要调整某些依赖版本")
        print("3. 参考 docs/SECURITY_FIX_PLAN.md")
        return 1


if __name__ == "__main__":
    sys.exit(main())
