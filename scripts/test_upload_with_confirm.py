"""
完整流程 + 等待处理 + 点击确认
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def full_upload_with_confirm():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            print("跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        print("=" * 80)
        print("完整上传流程（带确认）")
        print("=" * 80)
        
        # 步骤1：点击蓝色方框
        print("\n【步骤1】点击蓝色方框...")
        box_info = await page.evaluate("""
            () => {
                const coverBox = document.querySelector('.article-cover-images');
                if (coverBox) {
                    const rect = coverBox.getBoundingClientRect();
                    return {
                        center_x: rect.left + rect.width / 2,
                        center_y: rect.top + rect.height / 2
                    };
                }
                return null;
            }
        """)
        
        await page.mouse.click(box_info['center_x'], box_info['center_y'])
        await asyncio.sleep(3)
        print("[OK] 对话框已打开")
        
        # 步骤2：点击"上传图片"
        print("\n【步骤2】点击'上传图片'...")
        await page.evaluate("""
            () => {
                const allElements = document.querySelectorAll('button, [role="button"], span, div');
                for (const el of allElements) {
                    const text = (el.textContent || '').trim();
                    const rect = el.getBoundingClientRect();
                    if (text.includes('上传图片') && rect.width > 50 && rect.top > 0) {
                        el.click();
                        return true;
                    }
                }
                return false;
            }
        """)
        await asyncio.sleep(2)
        print("[OK] 已点击")
        
        # 步骤3：上传文件
        print("\n【步骤3】上传文件...")
        test_image = os.path.abspath('logs/test_cover.jpg')
        
        file_input = page.locator('input[type="file"]').first
        await file_input.set_input_files(test_image)
        print("[OK] 文件已设置")
        
        # 步骤4：等待上传处理
        print("\n【步骤4】等待上传处理...")
        await asyncio.sleep(10)  # 增加等待时间
        
        # 截图查看状态
        await page.screenshot(path='logs/after_upload_wait.png', full_page=True)
        print("[OK] 截图已保存")
        
        # 步骤5：查找并点击确认按钮
        print("\n【步骤5】查找确认按钮...")
        confirm_clicked = await page.evaluate("""
            () => {
                const allButtons = document.querySelectorAll('button, [role="button"]');
                for (const btn of allButtons) {
                    const text = (btn.textContent || '').trim();
                    const rect = btn.getBoundingClientRect();
                    if ((text === '确定' || text === '确认' || text === '完成') && 
                        rect.width > 50 && rect.top > 0) {
                        btn.click();
                        console.log('点击确认按钮:', text);
                        return true;
                    }
                }
                return false;
            }
        """)
        
        if confirm_clicked:
            print("[OK] 已点击确认按钮")
            await asyncio.sleep(3)
        else:
            print("[INFO] 未找到确认按钮（可能自动处理）")
        
        # 步骤6：验证封面
        print("\n【步骤6】验证封面...")
        await asyncio.sleep(5)
        
        # 截图
        await page.screenshot(path='logs/final_verification.png', full_page=True)
        
        cover_ok = await page.evaluate("""
            () => {
                const imgs = document.querySelectorAll('img');
                for (const img of imgs) {
                    const rect = img.getBoundingClientRect();
                    if (rect.width > 100 && rect.height > 100 && rect.top > 200) {
                        if (img.src && !img.src.includes('data:')) {
                            console.log('找到封面:', img.src.substring(0, 80));
                            return true;
                        }
                    }
                }
                return false;
            }
        """)
        
        if cover_ok:
            print("\n" + "=" * 80)
            print("[SUCCESS] 封面图上传成功！")
            print("=" * 80)
        else:
            print("\n[FAIL] 封面图未显示")
            print("请查看截图: logs/final_verification.png")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(full_upload_with_confirm())
