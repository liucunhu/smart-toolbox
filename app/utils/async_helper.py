"""
异步工具函数
提供通用的异步任务执行辅助方法
"""
import asyncio
from typing import Callable, Any


def run_async_task(coro):
    """
    运行异步任务的通用封装
    避免在同步代码中重复创建事件循环
    
    :param coro: 协程对象
    :return: 协程执行结果
    """
    try:
        # 尝试获取当前事件循环
        loop = asyncio.get_running_loop()
        # 如果已经在事件循环中，创建新任务
        if loop.is_running():
            # 注意：这种情况应该避免，最好直接使用 await
            import nest_asyncio
            nest_asyncio.apply()
            return loop.run_until_complete(coro)
    except RuntimeError:
        # 没有运行中的事件循环，创建新的
        pass
    
    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(coro)
        return result
    finally:
        loop.close()
