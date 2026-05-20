"""
增强的页面加载策略 - 解决头条页面加载不完整问题
"""
import asyncio
from playwright.async_api import async_playwright


async def advanced_page_load(page, url, timeout=60000):
    """
    高级页面加载策略
    1. 等待DOM加载
    2. 等待关键元素
    3. 滚动页面触发懒加载
    4. 等待网络空闲
    5. 执行页面初始化
    """
    
    print(f"\n📄 正在加载页面: {url}")
    
    # 策略 1: 基本加载
    print("  [1/5] 等待DOM加载...")
    await page.goto(url, timeout=timeout, wait_until='domcontentloaded')
    
    # 策略 2: 等待关键元素
    print("  [2/5] 等待关键元素...")
    key_selectors = [
        'input[placeholder*="标题"]',
        'div[contenteditable="true"]',
        'button:has-text("预览并发布")'
    ]
    
    for selector in key_selectors:
        try:
            await page.wait_for_selector(selector, timeout=10000)
            print(f"    ✅ 找到: {selector[:40]}")
        except:
            print(f"    ⚠️  未找到: {selector[:40]}")
    
    # 策略 3: 滚动页面触发懒加载
    print("  [3/5] 滚动页面触发懒加载...")
    await page.evaluate("""
        () => {
            return new Promise((resolve) => {
                let totalHeight = 0;
                const distance = 100;
                const timer = setInterval(() => {
                    const scrollHeight = document.body.scrollHeight;
                    window.scrollBy(0, distance);
                    totalHeight += distance;
                    
                    if(totalHeight >= scrollHeight){
                        clearInterval(timer);
                        resolve();
                    }
                }, 100);
            });
        }
    """)
    await asyncio.sleep(2)
    print("    ✅ 滚动完成")
    
    # 策略 4: 等待网络空闲
    print("  [4/5] 等待网络请求完成...")
    try:
        await page.wait_for_load_state('networkidle', timeout=15000)
        print("    ✅ 网络空闲")
    except:
        print("    ⚠️  网络请求持续中，继续执行")
    
    # 策略 5: 额外等待让JavaScript执行
    print("  [5/5] 等待JavaScript执行...")
    await asyncio.sleep(5)
    
    # 验证页面完整性
    print("\n🔍 验证页面完整性:")
    
    checks = {
        '标题输入框': 'input[placeholder*="标题"], textarea[placeholder*="标题"]',
        '正文编辑器': 'div[contenteditable="true"]',
        '发布按钮': 'button:has-text("预览并发布")',
        '封面图区域': 'div:has-text("封面"), div:has-text("无封面")',
        '发文设置': 'text=发文设置',
    }
    
    all_passed = True
    for name, selector in checks.items():
        try:
            elem = await page.query_selector(selector)
            if elem and await elem.is_visible():
                print(f"  ✅ {name}")
            else:
                print(f"  ❌ {name} (不可见)")
                all_passed = False
        except:
            print(f"  ❌ {name} (未找到)")
            all_passed = False
    
    if all_passed:
        print("\n✅ 页面加载完整！")
    else:
        print("\n⚠️  页面可能未完全加载")
    
    return all_passed


async def test_advanced_load():
    """测试高级加载策略"""
    
    print("="*80)
    print("🧪 测试高级页面加载策略")
    print("="*80)
    
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context(
        viewport={"width": 1920, "height": 1080}
    )
    page = await context.new_page()
    
    try:
        # 登录
        print("\n[步骤 1] 登录...")
        await page.goto("https://mp.toutiao.com/", timeout=30000)
        
        if "login" in page.url:
            print("⚠️  请手动完成登录，然后按回车...")
            input()
        else:
            print("✅ 已登录")
        
        # 使用高级加载策略打开发布页面
        print("\n[步骤 2] 使用高级策略加载发布页面...")
        publish_url = "https://mp.toutiao.com/profile_v4/graphic/publish?from=toutiao_pc"
        
        is_complete = await advanced_page_load(page, publish_url)
        
        if is_complete:
            print("\n✅ 页面完整，可以开始填写表单")
            
            # 尝试填写标题
            print("\n[步骤 3] 测试填写标题...")
            title_input = await page.query_selector('input[placeholder*="标题"]')
            if title_input:
                await title_input.fill("测试标题12345")
                print("✅ 标题填写成功")
                
                # 验证
                value = await title_input.input_value()
                print(f"验证: {value}")
            else:
                print("❌ 未找到标题输入框")
        else:
            print("\n⚠️  页面不完整，建议手动检查")
        
        print("\n⏸️  浏览器保持打开，按回车关闭...")
        input()
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        
        print("\n⏸️  按回车关闭...")
        input()
    finally:
        await browser.close()
        await playwright.stop()
        print("\n✅ 测试完成")


if __name__ == "__main__":
    asyncio.run(test_advanced_load())
