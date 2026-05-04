"""
指数退避重试机制
完整实现：重试装饰器 + 断点续传支持
"""
import asyncio
import random
import functools
from typing import Callable, Any, Optional
from app.utils.logger import logger

def exponential_backoff_retry(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exponential_base: float = 2.0,
    jitter: bool = True,
    retryable_exceptions: tuple = (Exception,)
):
    """
    指数退避重试装饰器
    :param max_retries: 最大重试次数
    :param base_delay: 基础延迟（秒）
    :param max_delay: 最大延迟（秒）
    :param exponential_base: 指数基数
    :param jitter: 是否添加随机抖动
    :param retryable_exceptions: 可重试的异常类型
    :return: 装饰器
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} 重试 {max_retries} 次后仍然失败: {str(e)}",
                            exc_info=True
                        )
                        raise
                    
                    # 计算延迟时间（指数退避）
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    # 添加随机抖动
                    if jitter:
                        delay *= random.uniform(0.5, 1.5)
                    
                    logger.warning(
                        f"{func.__name__} 第 {attempt + 1} 次失败，{delay:.2f}秒后重试: {str(e)}"
                    )
                    
                    await asyncio.sleep(delay)
                    
                except Exception as e:
                    # 不可重试的异常直接抛出
                    logger.error(f"{func.__name__} 发生不可重试的异常: {str(e)}", exc_info=True)
                    raise
            
            # 理论上不会到达这里
            raise last_exception
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                    
                except retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        logger.error(
                            f"{func.__name__} 重试 {max_retries} 次后仍然失败: {str(e)}",
                            exc_info=True
                        )
                        raise
                    
                    # 计算延迟时间
                    delay = min(
                        base_delay * (exponential_base ** attempt),
                        max_delay
                    )
                    
                    if jitter:
                        delay *= random.uniform(0.5, 1.5)
                    
                    logger.warning(
                        f"{func.__name__} 第 {attempt + 1} 次失败，{delay:.2f}秒后重试: {str(e)}"
                    )
                    
                    import time
                    time.sleep(delay)
                    
                except Exception as e:
                    logger.error(f"{func.__name__} 发生不可重试的异常: {str(e)}", exc_info=True)
                    raise
            
            raise last_exception
        
        # 判断是否为异步函数
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


class RetryManager:
    """重试管理器 - 支持断点续传"""
    
    def __init__(self):
        self.retry_state = {}
    
    def save_checkpoint(self, task_id: str, state: dict):
        """保存检查点（用于断点续传）"""
        self.retry_state[task_id] = {
            "state": state,
            "timestamp": asyncio.get_event_loop().time()
        }
        logger.debug(f"保存检查点: {task_id}")
    
    def load_checkpoint(self, task_id: str) -> Optional[dict]:
        """加载检查点"""
        if task_id in self.retry_state:
            checkpoint = self.retry_state[task_id]
            logger.info(f"加载检查点: {task_id}")
            return checkpoint["state"]
        return None
    
    def clear_checkpoint(self, task_id: str):
        """清除检查点"""
        if task_id in self.retry_state:
            del self.retry_state[task_id]
            logger.debug(f"清除检查点: {task_id}")
    
    async def execute_with_resume(
        self,
        task_id: str,
        func: Callable,
        *args,
        max_retries: int = 3,
        **kwargs
    ) -> Any:
        """
        执行任务并支持断点续传
        :param task_id: 任务ID
        :param func: 任务函数
        :param args: 位置参数
        :param max_retries: 最大重试次数
        :param kwargs: 关键字参数
        :return: 任务结果
        """
        # 加载检查点
        checkpoint = self.load_checkpoint(task_id)
        if checkpoint:
            logger.info(f"从检查点恢复任务: {task_id}")
            kwargs.update(checkpoint)
        
        last_exception = None
        
        for attempt in range(max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                
                # 执行成功，清除检查点
                self.clear_checkpoint(task_id)
                return result
                
            except Exception as e:
                last_exception = e
                
                if attempt == max_retries:
                    logger.error(f"任务 {task_id} 重试 {max_retries} 次后失败: {str(e)}")
                    raise
                
                # 保存检查点
                checkpoint_state = {
                    "attempt": attempt + 1,
                    "error": str(e),
                    "args": args,
                    "kwargs": kwargs
                }
                self.save_checkpoint(task_id, checkpoint_state)
                
                # 计算延迟
                delay = min(1.0 * (2 ** attempt), 60.0) * random.uniform(0.5, 1.5)
                
                logger.warning(f"任务 {task_id} 第 {attempt + 1} 次失败，{delay:.2f}秒后重试")
                await asyncio.sleep(delay)
        
        raise last_exception


# 全局重试管理器
retry_manager = RetryManager()
