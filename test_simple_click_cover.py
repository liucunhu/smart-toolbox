"""
简单直接地测试点击封面"+"号
"""
import asyncio
from playwright.async_api import async_playwright

async def test_click_plus():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            print("跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        print("=" * 80)
        print("测试点击封面'+'号")
        print("=" * 80)
        
        # 方法1：直接使用Playwright点击包含"展示封面"的区域
        print("\n【方法1】点击封面区域...")
        
        try:
            # 等待页面加载完成
            await page.wait_for_selector('[contenteditable="true"]', timeout=10000)
            
            # 滚动到封面区域
            await page.evaluate("""
                () => {
                    const divs = document.querySelectorAll('div');
                    for (const div of divs) {
                        const text = (div.textContent || '').trim();
                        if (text.includes('展示封面') && text.length < 50) {
                            div.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            return true;
                        }
                    }
                    return false;
                }
            """)
            
            await asyncio.sleep(2)
            
            # 截图查看当前位置
            await page.screenshot(path='logs/before_click_cover.png', full_page=True)
            print("   [OK] 已滚动到封面区域")
            
            # 尝试点击第一个包含"展示封面"的div
            click_result = await page.evaluate("""
                () => {
                    const divs = document.querySelectorAll('div');
                    let clicked = false;
                    
                    for (const div of divs) {
                        const text = (div.textContent || '').trim();
                        if (text.includes('展示封面') && text.length < 50) {
                            console.log('找到封面区域:', text);
                            
                            // 获取该div的位置和尺寸
                            const rect = div.getBoundingClientRect();
                            console.log('位置:', rect);
                            
                            // 尝试多种方式触发点击
                            
                            // 方式1：直接click
                            div.click();
                            console.log('已执行div.click()');
                            
                            // 方式2：dispatchEvent
                            const event = new MouseEvent('click', {
                                view: window,
                                bubbles: true,
                                cancelable: true,
                                clientX: rect.left + rect.width / 2,
                                clientY: rect.top + rect.height / 2
                            });
                            div.dispatchEvent(event);
                            console.log('已dispatch click事件');
                            
                            // 方式3：mousedown + mouseup
                            const mousedown = new MouseEvent('mousedown', {
                                view: window,
                                bubbles: true,
                                cancelable: true
                            });
                            div.dispatchEvent(mousedown);
                            
                            const mouseup = new MouseEvent('mouseup', {
                                view: window,
                                bubbles: true,
                                cancelable: true
                            });
                            div.dispatchEvent(mouseup);
                            console.log('已dispatch mousedown/mouseup');
                            
                            clicked = true;
                            break;
                        }
                    }
                    
                    return clicked;
                }
            """)
            
            if click_result:
                print("   [OK] 已触发点击事件")
            else:
                print("   [FAIL] 未找到封面区域")
            
            # 等待可能的对话框出现
            await asyncio.sleep(3)
            
            # 截图查看点击后的状态
            await page.screenshot(path='logs/after_click_cover.png', full_page=True)
            print("   [OK] 截图已保存")
            
            # 检查是否有对话框出现
            dialog_exists = await page.evaluate("""
                () => {
                    // 查找常见的对话框元素
                    const dialogs = document.querySelectorAll('[class*="dialog"], [class*="modal"], [role="dialog"], .byte-modal');
                    return dialogs.length > 0;
                }
            """)
            
            if dialog_exists:
                print("   [OK] 检测到对话框！")
                
                # 查找对话框中的上传按钮
                upload_buttons = await page.evaluate("""
                    () => {
                        const buttons = [];
                        const allButtons = document.querySelectorAll('button, [role="button"], span');
                        
                        for (const btn of allButtons) {
                            const text = (btn.textContent || '').trim();
                            if (text.includes('上传') || text.includes('本地') || text.includes('选择图片')) {
                                const rect = btn.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    buttons.push({
                                        text: text.substring(0, 30),
                                        tagName: btn.tagName,
                                        className: btn.className.substring(0, 50)
                                    });
                                }
                            }
                        }
                        
                        return buttons;
                    }
                """)
                
                print(f"   找到 {len(upload_buttons)} 个上传按钮:")
                for btn in upload_buttons:
                    print(f"      - [{btn['tagName']}] {btn['text']} ({btn['className']})")
                
                # 如果有"本地上传"或类似按钮，点击它
                if upload_buttons:
                    print("\n   尝试点击第一个上传按钮...")
                    await page.evaluate("""
                        () => {
                            const buttons = document.querySelectorAll('button, [role="button"], span');
                            for (const btn of buttons) {
                                const text = (btn.textContent || '').trim();
                                if (text.includes('上传') || text.includes('本地') || text.includes('选择')) {
                                    const rect = btn.getBoundingClientRect();
                                    if (rect.width > 0 && rect.height > 0) {
                                        btn.click();
                                        console.log('已点击:', text);
                                        return true;
                                    }
                                }
                            }
                            return false;
                        }
                    """)
                    
                    await asyncio.sleep(2)
                    await page.screenshot(path='logs/after_click_upload_btn.png', full_page=True)
                    print("   [OK] 已点击上传按钮")
            else:
                print("   [FAIL] 未检测到对话框")
                print("   说明：点击封面区域没有触发任何反应")
        
        except Exception as e:
            print(f"   [ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        print("\n" + "=" * 80)
        print("测试完成！请查看以下截图：")
        print("  1. logs/before_click_cover.png - 点击前")
        print("  2. logs/after_click_cover.png - 点击后")
        if dialog_exists:
            print("  3. logs/after_click_upload_btn.png - 点击上传按钮后")
        print("=" * 80)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_click_plus())
