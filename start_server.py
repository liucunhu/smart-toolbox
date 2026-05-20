"""
Smart-Toolbox 启动脚本
确保 Windows 上使用 ProactorEventLoop（支持 Playwright 子进程）
"""
import sys
import asyncio

# === Windows 事件循环修复 ===
# Playwright 需要创建子进程，Windows 默认 SelectorEventLoop 不支持 subprocess
# 必须在 uvicorn 启动前设置 ProactorEventLoop
if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    print("✅ 已设置 Windows ProactorEventLoop（支持 Playwright）")
    print(f"   当前策略: {asyncio.get_event_loop_policy().__class__.__name__}")

# 启动 uvicorn
if __name__ == "__main__":
    import uvicorn
    
    # 使用 uvicorn 的 loop_factory 参数确保 worker 使用 ProactorEventLoop
    if sys.platform == 'win32':
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            loop="asyncio",  # 使用 asyncio 默认循环（已被策略设置为 ProactorEventLoop）
        )
    else:
        uvicorn.run(
            "main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
