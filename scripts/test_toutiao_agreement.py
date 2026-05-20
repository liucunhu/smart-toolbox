"""
今日头条自动勾选用户协议测试
验证登录时是否能自动勾选用户协议
"""
import asyncio
from app.services.publish.toutiao_publisher import ToutiaoPublisher
from app.utils.logger import logger


async def test_agreement_checkbox():
    """测试头条登录时自动勾选用户协议"""
    publisher = ToutiaoPublisher(account_id=1)
    
    try:
        # 1. 初始化浏览器
        await publisher.initialize_browser()
        logger.info("✅ 浏览器初始化完成")
        
        # 2. 打开登录页面
        await publisher.page.goto("https://mp.toutiao.com/", timeout=30000)
        await asyncio.sleep(3)
        logger.info(f"当前URL: {publisher.page.url}")
        
        # 3. 切换到密码登录模式
        logger.info("正在切换到密码登录模式...")
        try:
            password_login_btn = await publisher.page.query_selector('text=密码登录')
            if password_login_btn:
                await password_login_btn.click()
                await asyncio.sleep(2)
                logger.info("✅ 已切换到密码登录模式")
        except Exception as e:
            logger.warning(f"切换失败: {e}")
        
        # 4. 测试自动勾选用户协议
        logger.info("\n" + "="*60)
        logger.info("开始测试自动勾选用户协议功能")
        logger.info("="*60)
        
        agreement_selectors = [
            'input[type="checkbox"]',
            'label:has-text("用户协议")',
            'label:has-text("我已阅读并同意")',
            'label:has-text("隐私政策")',
            '[class*="agree"] input[type="checkbox"]',
            '[class*="protocol"] input[type="checkbox"]',
            'input[name*="agree"]',
            'input[name*="protocol"]',
            '.agreement-checkbox input[type="checkbox"]'
        ]
        
        agreement_checked = False
        for selector in agreement_selectors:
            try:
                agreement_checkbox = await publisher.page.query_selector(selector)
                if agreement_checkbox:
                    logger.info(f"✅ 找到用户协议复选框，选择器: {selector}")
                    is_checked = await agreement_checkbox.is_checked()
                    logger.info(f"当前状态: {'已勾选' if is_checked else '未勾选'}")
                    
                    if not is_checked:
                        await agreement_checkbox.check()
                        await asyncio.sleep(1)
                        is_checked_after = await agreement_checkbox.is_checked()
                        logger.info(f"勾选后状态: {'已勾选' if is_checked_after else '未勾选'}")
                        
                        if is_checked_after:
                            logger.info("✅ 自动勾选成功！")
                            agreement_checked = True
                            break
                        else:
                            logger.warning("⚠️  勾选操作失败")
                    else:
                        logger.info("✅ 用户协议已经勾选")
                        agreement_checked = True
                        break
            except Exception as e:
                logger.debug(f"尝试选择器 {selector} 失败: {e}")
                continue
        
        if not agreement_checked:
            logger.warning("⚠️  未找到用户协议复选框")
        
        # 5. 截图保存（用于调试）
        screenshot_path = "logs/toutiao_agreement_test.png"
        await publisher.page.screenshot(path=screenshot_path)
        logger.info(f"📸 截图已保存到: {screenshot_path}")
        
        logger.info("\n" + "="*60)
        logger.info("测试完成！请检查日志和截图")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"测试失败: {str(e)}", exc_info=True)
    finally:
        await publisher.close()


if __name__ == "__main__":
    asyncio.run(test_agreement_checkbox())
