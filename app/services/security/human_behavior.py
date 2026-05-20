"""
行为拟人化和IP代理池服务
实现鼠标抖动、随机延迟、代理IP池管理
"""
import asyncio
import random
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from playwright.async_api import Page

logger = logging.getLogger(__name__)


class HumanLikeBehavior:
    """拟人化行为控制器"""
    
    @staticmethod
    def calculate_mouse_jitter() -> Tuple[float, float]:
        """
        计算鼠标抖动偏移量
        
        Returns:
            Tuple[float, float]: (x偏移, y偏移）
        """
        # 使用高斯分布生成更自然的抖动
        x_jitter = random.gauss(0, 1.5)  # 均值0，标准差1.5
        y_jitter = random.gauss(0, 1.5)
        
        return (x_jitter, y_jitter)
    
    @staticmethod
    def calculate_random_delay(
        base_delay: float,
        min_delay: float = 0.5,
        max_delay: float = 3.0
    ) -> float:
        """
        计算随机延迟
        
        Args:
            base_delay: 基础延迟（秒）
            min_delay: 最小延迟
            max_delay: 最大延迟
            
        Returns:
            float: 实际延迟时间（秒）
        """
        # 在基础延迟附近随机波动
        jitter = random.uniform(-0.3, 0.3)
        actual_delay = base_delay + jitter
        
        # 确保在范围内
        actual_delay = max(min_delay, min(max_delay, actual_delay))
        
        return actual_delay
    
    @staticmethod
    async def simulate_human_click(
        page: Page,
        x: float,
        y: float,
        jitter_std: float = 1.0
    ) -> Tuple[float, float]:
        """
        模拟人类点击（包含鼠标移动和抖动）
        
        Args:
            page: Playwright页面对象
            x: 目标X坐标
            y: 目标Y坐标
            jitter_std: 抖动标准差
            
        Returns:
            Tuple[float, float]: 实际点击坐标
        """
        # 计算抖动
        x_jitter, y_jitter = HumanLikeBehavior.calculate_mouse_jitter()
        
        # 生成移动路径（贝塞尔曲线，更自然）
        current_x, current_y = await page.evaluate("""
            return [window.mouseX, window.mouseY];
        """)
        
        # 贝塞尔曲线控制点（3点曲线：起点 -> 控制点1 -> 控制点2 -> 终点）
        control_points = [
            (current_x, current_y),
            (current_x + (x - current_x) * 0.3, current_y + (y - current_y) * 0.3),
            (current_x + (x - current_x) * 0.7, current_y + (y - current_y) * 0.7),
            (x + x_jitter, y + y_jitter)
        ]
        
        # 分段移动到目标点
        segments = 10
        for i in range(segments):
            t = (i + 1) / segments
            
            # 贝塞尔曲线插值
            cx = 0
            cy = 0
            for j in range(4):
                if j == 0:
                    continue
                # 贝塞尔基函数
                n = 3
                for k in range(n + 1):
                    if k == j:
                        continue
                    # 计算组合数
                    coef = 1
                    for m in range(j, n + 1):
                        coef *= (n - m)
                        coef //= (n - m)
                    
                    cx += coef * control_points[j][0] * (t ** j) * ((1 - t) ** (n - j))
                    cy += coef * control_points[j][1] * (t ** j) * ((1 - t) ** (n - j))
            
            # 添加随机抖动到移动路径
            move_jitter_x = random.gauss(0, 0.5)
            move_jitter_y = random.gauss(0, 0.5)
            cx += move_jitter_x
            cy += move_jitter_y
            
            # 移动鼠标
            await page.mouse.move(cx, cy)
            
            # 随机延迟
            delay = HumanLikeBehavior.calculate_random_delay(0.02, 0.01, 0.05)
            await asyncio.sleep(delay)
        
        # 在目标点添加额外的抖动
        final_jitter_x = random.gauss(0, 1.0)
        final_jitter_y = random.gauss(0, 1.0)
        final_x = x + final_jitter_x
        final_y = y + final_jitter_y
        
        await page.mouse.move(final_x, final_y)
        await asyncio.sleep(random.uniform(0.05, 0.15))
        
        # 点击
        await page.mouse.click(x=final_x, y=final_y)
        
        return (final_x, final_y)
    
    @staticmethod
    async def simulate_human_type(
        page: Page,
        text: str,
        element,
        base_delay: float = 0.1
    ):
        """
        模拟人类输入文字
        
        Args:
            page: 页面对象
            text: 要输入的文本
            element: 输入元素
            base_delay: 基础字符间延迟
        """
        # 点击输入框
        await element.click()
        await asyncio.sleep(random.uniform(0.1, 0.3))
        
        # 逐字输入
        for i, char in enumerate(text):
            # 随机延迟（模拟真实打字速度）
            delay = HumanLikeBehavior.calculate_random_delay(base_delay)
            
            # 输入字符
            await element.type(char)
            
            # 偶尔添加删除和重新输入（模拟打错）
            if random.random() < 0.05:  # 5%概率模拟打错
                await asyncio.sleep(delay)
                await element.press('Backspace')
                await asyncio.sleep(random.uniform(0.2, 0.5))
                await element.type(char)
            
            await asyncio.sleep(delay)
        
        await asyncio.sleep(random.uniform(0.2, 0.5))
    
    @staticmethod
    async def simulate_human_scroll(
        page: Page,
        direction: str = "down",
        amount: int = 300
    ):
        """
        模拟人类滚动
        
        Args:
            page: 页面对象
            direction: 滚动方向（up/down）
            amount: 滚动量（像素）
        """
        # 分多次滚动
        steps = random.randint(3, 5)
        scroll_per_step = amount / steps
        
        for i in range(steps):
            if direction == "down":
                delta = scroll_per_step
            else:
                delta = -scroll_per_step
            
            # 添加随机抖动
            jitter = random.uniform(-20, 20)
            await page.mouse.wheel(delta + jitter)
            
            # 随机延迟
            await asyncio.sleep(random.uniform(0.3, 0.8))
    
    @staticmethod
    async def simulate_human_hover(
        page: Page,
        element,
        hover_duration: float = 2.0
    ):
        """
        模拟人类悬停
        
        Args:
            page: 页面对象
            element: 元素
            hover_duration: 悬停时长（秒）
        """
        # 获取元素位置
        box = await element.bounding_box()
        
        if not box:
            return
        
        # 移动到元素中心
        center_x = box["x"] + box["width"] / 2
        center_y = box["y"] + box["height"] / 2
        
        await HumanLikeBehavior.simulate_human_click(
            page, center_x, center_y
        )
        
        # 悬停
        await asyncio.sleep(hover_duration)
        
        # 偶尔移动鼠标（模拟观察）
        for _ in range(random.randint(1, 3)):
            move_x = center_x + random.uniform(-10, 10)
            move_y = center_y + random.uniform(-10, 10)
            await page.mouse.move(move_x, move_y)
            await asyncio.sleep(random.uniform(0.2, 0.5))


@dataclass
class ProxyConfig:
    """代理配置"""
    protocol: str  # http/https/socks5
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    proxy_type: str = "residential"  # residential/datacenter/mobile
    country: str = "cn"
    response_time: Optional[float] = None
    success_rate: float = 1.0
    last_used: Optional[str] = None


class ProxyPool:
    """IP代理池"""
    
    def __init__(self):
        self.proxies: Dict[str, ProxyConfig] = {}
        self.proxy_queue: List[str] = []
        self.proxy_stats: Dict[str, Dict[str, Any]] = {}
    
    def load_proxies(self, proxy_list: List[ProxyConfig]):
        """
        加载代理列表
        
        Args:
            proxy_list: 代理配置列表
        """
        for i, proxy in enumerate(proxy_list):
            proxy_id = f"proxy_{i}"
            self.proxies[proxy_id] = proxy
            self.proxy_queue.append(proxy_id)
            self.proxy_stats[proxy_id] = {
                "use_count": 0,
                "success_count": 0,
                "last_used": None,
                "response_times": []
            }
        
        logger.info(f"✅ 加载代理池: {len(proxy_list)} 个代理")
    
    def get_proxy(
        self,
        country: Optional[str] = None,
        proxy_type: Optional[str] = None
    ) -> Optional[ProxyConfig]:
        """
        获取代理（考虑轮换和健康度）
        
        Args:
            country: 国家代码（可选）
            proxy_type: 代理类型（可选）
            
        Returns:
            Optional[ProxyConfig]: 代理配置
        """
        if not self.proxy_queue:
            logger.warning("代理池为空")
            return None
        
        # 过滤符合要求的代理
        available_proxies = []
        for proxy_id in self.proxy_queue:
            proxy = self.proxies[proxy_id]
            stats = self.proxy_stats[proxy_id]
            
            # 检查健康度
            if stats["use_count"] > 0:
                success_rate = stats["success_count"] / stats["use_count"]
                if success_rate < 0.5:  # 成功率低于50%则跳过
                    continue
            
            # 检查国家和类型
            if country and proxy.country != country:
                continue
            if proxy_type and proxy.proxy_type != proxy_type:
                continue
            
            available_proxies.append((proxy_id, proxy))
        
        if not available_proxies:
            # 如果没有符合要求的代理，返回任意一个
            if self.proxy_queue:
                proxy_id = self.proxy_queue[0]
                proxy = self.proxies[proxy_id]
                self._update_queue(proxy_id)
                return proxy
            return None
        
        # 优先使用成功率高的代理
        available_proxies.sort(
            key=lambda x: self.proxy_stats[x[0]]["success_count"] / 
                               max(self.proxy_stats[x[0]]["use_count"], 1),
            reverse=True
        )
        
        proxy_id, proxy = available_proxies[0]
        self._update_queue(proxy_id)
        
        return proxy
    
    def _update_queue(self, used_proxy_id: str):
        """
        更新代理队列（将使用的代理移到队尾）
        
        Args:
            used_proxy_id: 使用的代理ID
        """
        if used_proxy_id in self.proxy_queue:
            self.proxy_queue.remove(used_proxy_id)
            self.proxy_queue.append(used_proxy_id)
    
    def record_proxy_result(
        self,
        proxy_id: str,
        success: bool,
        response_time: Optional[float] = None
    ):
        """
        记录代理使用结果
        
        Args:
            proxy_id: 代理ID
            success: 是否成功
            response_time: 响应时间（毫秒）
        """
        if proxy_id not in self.proxy_stats:
            return
        
        stats = self.proxy_stats[proxy_id]
        stats["use_count"] += 1
        
        if success:
            stats["success_count"] += 1
        
        if response_time:
            stats["response_times"].append(response_time)
            # 只保留最近10次响应时间
            if len(stats["response_times"]) > 10:
                stats["response_times"] = stats["response_times"][-10:]
            
            # 更新平均响应时间
            stats["avg_response_time"] = sum(stats["response_times"]) / len(stats["response_times"])
        
        stats["last_used"] = asyncio.get_event_loop().time()
        
        logger.debug(f"代理 {proxy_id} 使用记录: 成功={success}, 次数={stats['use_count']}")
    
    def mark_proxy_failed(self, proxy_id: str):
        """
        标记代理为失败
        
        Args:
            proxy_id: 代理ID
        """
        if proxy_id in self.proxies:
            # 暂时移除使用
            if proxy_id in self.proxy_queue:
                self.proxy_queue.remove(proxy_id)
            
            logger.warning(f"代理 {proxy_id} 标记为失败，暂时移除")
    
    def rotate_proxy(self, max_retries: int = 3) -> Optional[str]:
        """
        轮换代理
        
        Args:
            max_retries: 最大重试次数
            
        Returns:
            Optional[str]: 可用的代理ID
        """
        for _ in range(max_retries):
            proxy = self.get_proxy()
            if proxy:
                return f"{proxy.protocol}://{proxy.host}:{proxy.port}"
        
        logger.error("代理池中没有可用的代理")
        return None
    
    def get_proxy_stats(self) -> Dict[str, Any]:
        """
        获取代理池统计信息
        
        Returns:
            Dict: 统计信息
        """
        total_proxies = len(self.proxies)
        total_usage = sum(s["use_count"] for s in self.proxy_stats.values())
        total_success = sum(s["success_count"] for s in self.proxy_stats.values())
        
        avg_success_rate = total_success / total_usage if total_usage > 0 else 0.0
        
        return {
            "total_proxies": total_proxies,
            "total_usage": total_usage,
            "total_success": total_success,
            "avg_success_rate": avg_success_rate,
            "proxy_details": [
                {
                    "id": proxy_id,
                    "host": proxy.host,
                    "port": proxy.port,
                    "type": proxy.proxy_type,
                    "country": proxy.country,
                    "use_count": self.proxy_stats[proxy_id]["use_count"],
                    "success_rate": self.proxy_stats[proxy_id]["success_count"] / 
                                 max(self.proxy_stats[proxy_id]["use_count"], 1),
                    "avg_response_time": self.proxy_stats[proxy_id].get("avg_response_time", 0)
                }
                for proxy_id, proxy in self.proxies.items()
            ]
        }
    
    def load_from_file(self, filepath: str):
        """
        从文件加载代理列表
        
        Args:
            filepath: 文件路径
        """
        import json
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            proxies = []
            for proxy_data in data.get("proxies", []):
                proxy = ProxyConfig(
                    protocol=proxy_data.get("protocol", "http"),
                    host=proxy_data.get("host", ""),
                    port=proxy_data.get("port", 8080),
                    username=proxy_data.get("username"),
                    password=proxy_data.get("password"),
                    proxy_type=proxy_data.get("type", "residential"),
                    country=proxy_data.get("country", "cn")
                )
                proxies.append(proxy)
            
            self.load_proxies(proxies)
            logger.info(f"✅ 从文件加载代理: {len(proxies)}个")
            
        except Exception as e:
            logger.error(f"从文件加载代理失败: {e}")


# 创建全局代理池实例
_proxy_pool = None
_human_behavior = None


def get_proxy_pool() -> ProxyPool:
    """获取代理池实例（单例模式）"""
    global _proxy_pool
    if _proxy_pool is None:
        _proxy_pool = ProxyPool()
    return _proxy_pool


def get_human_behavior() -> HumanLikeBehavior:
    """获取拟人化行为控制器实例（单例模式）"""
    global _human_behavior
    if _human_behavior is None:
        _human_behavior = HumanLikeBehavior()
    return _human_behavior
