"""
测试完整页面加载
"""
import asyncio
from playwright.async_api import async_playwright


async def test_full_page_load():
    """测试页面完全加载"""
    
    print("="*80)
    print("🧪 测试页面完整加载")
    print("="*80)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page = await context.new_page()
    
    try:
        # 步骤 1: 登录
        print("\n[步骤 1] 登录...")
        await page.goto("https://mp.toutiao.com/", timeout=30000)
        
        if "login" in page.url:
            print("⚠️  请手动完成登录，然后按回车...")
            input()
        else:
            print("✅ 已登录")
        
        # 步骤 2: 打开发布页面
        print("\n[步骤 2] 打开发布页面...")
        publish_url = "https://mp.toutiao.com/profile_v4/graphic/publish?from=toutiao_pc"
        
        # ★★★ 使用更宽松的加载策略 ★★★
        print("⏳ 正在加载页面...")
        await page.goto(publish_url, timeout=60000, wait_until='domcontentloaded')
        
        # 等待关键元素出现
        print("⏳ 等待关键元素加载...")
        
        # 等待标题输入框
        try:
            await page.wait_for_selector('input[placeholder*="标题"], textarea[placeholder*="标题"]', timeout=15000)
            print("✅ 标题输入框已加载")
        except:
            print("⚠️  标题输入框未找到")
        
        # 等待正文编辑器
        try:
            await page.wait_for_selector('div[contenteditable="true"]', timeout=15000)
            print("✅ 正文编辑器已加载")
        except:
            print("⚠️  正文编辑器未找到")
        
        # 等待发布按钮
        try:
            await page.wait_for_selector('button:has-text("预览并发布")', timeout=15000)
            print("✅ 发布按钮已加载")
        except:
            print("⚠️  发布按钮未找到")
        
        # 额外等待让JavaScript完全执行
        print("⏳ 等待JavaScript执行...")
        await asyncio.sleep(8)
        
        print(f"\n✅ 页面已加载，URL: {page.url}")
        
        # 保存完整HTML
        html_file = f"logs/full_page_{int(asyncio.get_event_loop().time())}.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(await page.content())
        print(f"📄 HTML已保存: {html_file}")
        
        # 截图
        screenshot = f"logs/full_page_{int(asyncio.get_event_loop().time())}.png"
        await page.screenshot(path=screenshot, full_page=True)
        print(f"📸 截图已保存: {screenshot}")
        
        # 列出所有按钮
        print("\n[按钮列表]")
        buttons = await page.query_selector_all('button')
        print(f"共找到 {len(buttons)} 个按钮:")
        for i, btn in enumerate(buttons):
            text = await btn.text_content()
            if text.strip():
                print(f"  [{i}] {text.strip()[:50]}")
        
        print("\n⏸️  浏览器保持打开，请检查页面是否完整")
        print("   按回车关闭...")
        input()
        
    except Exception as e:
        print(f"\n 错误: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n️  按回车关闭...")
        input()
    finally:
        await browser.close()
        await playwright.stop()
        print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(test_full_page_load())
