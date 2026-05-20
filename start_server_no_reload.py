"""
Smart-Toolbox 启动脚本（生产模式，无 reload）
确保 Windows 上使用 ProactorEventLoop（支持 Playwright 子进程）
"""
import sys
import asyncio

# === Windows 事件循环修复 ===
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("✅ 已设置 Windows ProactorEventLoop（支持 Playwright）")
    print(f"   当前策略: {asyncio.get_event_loop_policy().__class__.__name__}")

if __name__ == "__main__":
    import uvicorn
    
    # 不使用 reload 模式，确保事件循环策略生效
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # 禁用 reload 模式
        log_level="info",
        workers=1  # 单 worker 模式
    )
