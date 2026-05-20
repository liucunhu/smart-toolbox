"""
今日头条登录状态检测优化测试
验证多种登录成功检测策略
"""
import asyncio
from app.services.publish.toutiao_publisher import ToutiaoPublisher
from app.utils.logger import logger


async def test_login_detection():
    """测试头条登录检测逻辑"""
    publisher = ToutiaoPublisher(account_id=1)
    
    try:
        # 1. 初始化浏览器
        await publisher.initialize_browser()
        logger.info("✅ 浏览器初始化完成")
        
        # 2. 执行登录（支持扫码）
        logger.info("=" * 60)
        logger.info("请在弹出的浏览器中完成扫码登录")
        logger.info("系统将自动检测登录状态并保存Cookie")
        logger.info("=" * 60)
        
        login_result = await publisher.login_with_manual_input(
            username="test_user",  # 用户名仅用于日志
            password=""  # 扫码登录不需要密码
        )
        
        # 3. 检查登录结果
        if login_result["status"] == "success":
            logger.info("🎉 登录成功！")
            logger.info(f"当前URL: {publisher.page.url}")
            logger.info(f"Cookie数量: {len(login_result.get('cookies', ''))}")
            
            # 4. 验证是否可以访问发布页面
            logger.info("\n测试访问发布页面...")
            await publisher.page.goto("https://mp.toutiao.com/profile/v4/graphic/publish", timeout=30000)
            await asyncio.sleep(3)
            
            current_url = publisher.page.url
            if "login" not in current_url and "sso" not in current_url:
                logger.info("✅ 可以正常访问发布页面，登录状态有效！")
            else:
                logger.warning("⚠️  访问发布页面被重定向到登录页，Cookie可能无效")
                
        else:
            logger.error(f"❌ 登录失败: {login_result.get('error')}")
    
    except Exception as e:
        logger.error(f"测试异常: {e}", exc_info=True)
    
    finally:
        await publisher.close()
        logger.info("测试完成")


if __name__ == "__main__":
    asyncio.run(test_login_detection())
