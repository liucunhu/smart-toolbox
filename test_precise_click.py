"""
精确定位并点击蓝色方框的中心
"""
import asyncio
from playwright.async_api import async_playwright

async def precise_click():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        print("精确定位蓝色方框...")
        
        # 获取蓝色方框的精确位置
        box_info = await page.evaluate("""
            () => {
                // 查找 article-cover-images 类
                const coverBox = document.querySelector('.article-cover-images');
                if (coverBox) {
                    const rect = coverBox.getBoundingClientRect();
                    return {
                        left: rect.left,
                        top: rect.top,
                        width: rect.width,
                        height: rect.height,
                        center_x: rect.left + rect.width / 2,
                        center_y: rect.top + rect.height / 2
                    };
                }
                return null;
            }
        """)
        
        if box_info:
            print(f"蓝色方框位置:")
            print(f"  左上角: ({box_info['left']}, {box_info['top']})")
            print(f"  尺寸: {box_info['width']}x{box_info['height']}")
            print(f"  中心点: ({box_info['center_x']}, {box_info['center_y']})")
            
            # 截图前
            await page.screenshot(path='logs/before_precise_click.png')
            
            # 点击中心点
            print(f"\n点击中心点 ({box_info['center_x']}, {box_info['center_y']})...")
            await page.mouse.click(box_info['center_x'], box_info['center_y'])
            
            await asyncio.sleep(3)
            
            # 截图后
            await page.screenshot(path='logs/after_precise_click.png')
            
            # 检查对话框
            dialog_exists = await page.evaluate("""
                () => {
                    const allDivs = document.querySelectorAll('div');
                    for (const div of allDivs) {
                        const text = (div.textContent || '').trim();
                        if (text.includes('上传图片') || text.includes('本地上传') || text.includes('免费正版')) {
                            return true;
                        }
                    }
                    return false;
                }
            """)
            
            if dialog_exists:
                print("[OK] 对话框已打开！")
            else:
                print("[FAIL] 对话框未打开")
                print("请查看截图对比:")
                print("  - logs/before_precise_click.png")
                print("  - logs/after_precise_click.png")
        else:
            print("[FAIL] 未找到蓝色方框")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(precise_click())
