"""
RPA元素监控器
监控页面元素健康状态，自动报警
"""
from playwright.async_api import Page
from app.utils.logger import logger
from typing import Dict, List


class ElementMonitor:
    """RPA元素监控器"""
    
    def __init__(self):
        self.monitored_elements = {}
    
    async def add_element(self, name: str, selector: str, platform: str):
        """添加需要监控的元素"""
        self.monitored_elements[name] = {
            "selector": selector,
            "platform": platform,
            "status": "unknown",
            "last_check": None
        }
        logger.info(f"已添加监控元素: {name}")
    
    async def check_element(self, page: Page, name: str) -> Dict:
        """检查单个元素状态"""
        if name not in self.monitored_elements:
            return {"error": "元素不存在"}
        
        element_info = self.monitored_elements[name]
        
        try:
            element = await page.query_selector(element_info["selector"])
            
            if element:
                element_info["status"] = "healthy"
                logger.info(f"元素 {name} 状态正常")
                return {
                    "name": name,
                    "status": "healthy",
                    "visible": await element.is_visible()
                }
            else:
                element_info["status"] = "missing"
                logger.warning(f"元素 {name} 未找到")
                
                # 发送告警
                await self.send_alert(name, "元素未找到")
                
                return {
                    "name": name,
                    "status": "missing",
                    "selector": element_info["selector"]
                }
        
        except Exception as e:
            element_info["status"] = "error"
            logger.error(f"元素 {name} 检查失败: {str(e)}")
            
            await self.send_alert(name, f"检查失败: {str(e)}")
            
            return {
                "name": name,
                "status": "error",
                "error": str(e)
            }
    
    async def check_all_elements(self, page: Page) -> Dict:
        """检查所有监控元素"""
        results = {}
        
        for name in self.monitored_elements:
            results[name] = await self.check_element(page, name)
        
        # 统计健康状态
        healthy_count = sum(1 for r in results.values() if r.get("status") == "healthy")
        total_count = len(results)
        
        health_rate = (healthy_count / total_count * 100) if total_count > 0 else 0
        
        return {
            "total": total_count,
            "healthy": healthy_count,
            "health_rate": health_rate,
            "details": results
        }
    
    async def send_alert(self, element_name: str, message: str):
        """发送告警通知"""
        alert_message = f"⚠️ RPA元素告警\n元素: {element_name}\n问题: {message}"
        logger.warning(alert_message)
        
        # TODO: 集成实际的通知渠道（邮件、钉钉、企业微信等）
        # await notification_service.send(alert_message)
    
    async def get_health_report(self) -> Dict:
        """生成健康报告"""
        report = {
            "total_elements": len(self.monitored_elements),
            "elements": {}
        }
        
        for name, info in self.monitored_elements.items():
            report["elements"][name] = {
                "selector": info["selector"],
                "platform": info["platform"],
                "status": info["status"]
            }
        
        return report


# 使用示例
if __name__ == "__main__":
    import asyncio
    from playwright.async_api import async_playwright
    
    async def test_monitor():
        monitor = ElementMonitor()
        
        # 添加监控元素
        await monitor.add_element("login_button", "#login-btn", "douyin")
        await monitor.add_element("upload_button", ".upload-btn", "douyin")
        
        # 启动浏览器测试
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch()
        page = await browser.new_page()
        await page.goto("https://example.com")
        
        # 检查元素
        report = await monitor.check_all_elements(page)
        print(f"健康报告: {report}")
        
        await browser.close()
        await playwright.stop()
    
    asyncio.run(test_monitor())
