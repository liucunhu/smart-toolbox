"""
验证头条文章是否真的发布成功
检查多个指标来确认
"""
import asyncio
from playwright.async_api import async_playwright
from app.utils.logger import logger


async def verify_publish():
    """验证发布状态"""
    
    print("="*80)
    print("🔍 验证头条文章发布状态")
    print("="*80)
    print()
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page = await context.new_page()
    
    try:
        # 步骤 1: 登录
        print("\n[步骤 1] 请登录头条创作者平台...")
        await page.goto("https://mp.toutiao.com/", timeout=30000)
        
        if "login" in page.url or "sso" in page.url:
            print("⚠️  请在浏览器中完成登录，然后按回车继续...")
            input()
        else:
            print("✅ 已登录")
        
        # 步骤 2: 进入内容管理页面
        print("\n[步骤 2] 进入内容管理页面...")
        await page.goto("https://mp.toutiao.com/profile_v4/graphic/articles", timeout=30000)
        await asyncio.sleep(3)
        
        screenshot_path = "logs/verify_content_list.png"
        await page.screenshot(path=screenshot_path, full_page=True)
        print(f"📸 截图已保存: {screenshot_path}")
        
        # 步骤 3: 查找测试文章
        print("\n[步骤 3] 查找测试文章...")
        test_title = "【测试】修复后的发布功能"
        
        # 尝试多种选择器查找文章
        search_selectors = [
            f'a:has-text("{test_title}")',
            f'div:has-text("{test_title}")',
            f'span:has-text("{test_title}")',
            f'td:has-text("{test_title}")'
        ]
        
        article_found = False
        for selector in search_selectors:
            try:
                elem = await page.query_selector(selector)
                if elem:
                    article_found = True
                    print(f"✅ 找到文章！选择器: {selector}")
                    
                    # 获取文章详情
                    text = await elem.text_content()
                    print(f"   文章内容: {text[:100]}...")
                    
                    # 查找状态标签
                    parent = await elem.evaluate_handle("el => el.closest('tr') || el.closest('div[class*=\"item\"]')")
                    if parent:
                        status_elem = await parent.query_selector('[class*="status"], [class*="tag"]')
                        if status_elem:
                            status_text = await status_elem.text_content()
                            print(f"   文章状态: {status_text}")
                    break
            except Exception as e:
                continue
        
        if not article_found:
            print(f"❌ 未找到标题包含 '{test_title}' 的文章")
            
            # 列出最近的文章
            print("\n📋 最近的文章列表:")
            try:
                articles = await page.query_selector_all('a[href*="/graphic/"], div[class*="article"]')
                for i, article in enumerate(articles[:5]):
                    title = await article.text_content()
                    if title and len(title.strip()) > 5:
                        print(f"   [{i+1}] {title.strip()[:50]}")
            except Exception as e:
                print(f"   无法获取文章列表: {e}")
        
        # 步骤 4: 检查草稿箱
        print("\n[步骤 4] 检查草稿箱...")
        draft_link = await page.query_selector('a:has-text("草稿"), a:has-text("draft")')
        if draft_link:
            await draft_link.click()
            await asyncio.sleep(2)
            
            draft_screenshot = "logs/verify_draft_box.png"
            await page.screenshot(path=draft_screenshot, full_page=True)
            print(f"📸 草稿箱截图: {draft_screenshot}")
            
            # 在草稿箱中查找
            draft_found = False
            for selector in search_selectors:
                try:
                    elem = await page.query_selector(selector)
                    if elem:
                        draft_found = True
                        print(f"✅ 在草稿箱中找到文章！")
                        break
                except:
                    continue
            
            if not draft_found:
                print("❌ 草稿箱中也没有找到文章")
        else:
            print("⚠️  未找到草稿箱链接")
        
        # 步骤 5: 总结
        print("\n" + "="*80)
        print("📊 验证总结")
        print("="*80)
        
        if article_found:
            print("✅ 文章已成功发布！")
            print("   可以在头条App中看到这篇文章")
        else:
            print("❌ 文章未找到")
            print("\n可能的原因:")
            print("   1. 发布失败（虽然显示成功）")
            print("   2. 文章还在审核中")
            print("   3. 发布到了错误的账号")
            print("   4. 头条页面结构变化，选择器失效")
            print("\n建议:")
            print("   1. 查看截图文件分析页面内容")
            print("   2. 手动在头条后台搜索文章标题")
            print("   3. 检查是否有审核通知")
            print("   4. 等待几分钟后再次检查")
        
        print("="*80)
        
        print("\n⏸️  浏览器将保持打开，请手动检查")
        print("   确认无误后，在此终端按回车关闭浏览器...")
        input()
        
    except Exception as e:
        print(f"\n❌ 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n⏸️  按回车关闭浏览器...")
        input()
    finally:
        await browser.close()
        await playwright.stop()
        print("\n✅ 验证完成")


if __name__ == "__main__":
    asyncio.run(verify_publish())
