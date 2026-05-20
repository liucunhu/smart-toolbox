"""
完整流程：点击蓝色方框 → 打开对话框 → 点击本地上传 → 上传文件
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def full_upload_flow():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            print("跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        print("=" * 80)
        print("完整上传流程")
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
        
        if not box_info:
            print("[FAIL] 未找到蓝色方框")
            return
        
        await page.mouse.click(box_info['center_x'], box_info['center_y'])
        await asyncio.sleep(3)
        print("[OK] 已点击蓝色方框")
        
        # 步骤2：查找并点击"本地上传"按钮
        print("\n【步骤2】查找'本地上传'按钮...")
        
        upload_btn_info = await page.evaluate("""
            () => {
                const allElements = document.querySelectorAll('button, [role="button"], span, div');
                
                for (const el of allElements) {
                    const text = (el.textContent || '').trim();
                    const rect = el.getBoundingClientRect();
                    
                    // 查找"本地上传"或"上传图片"
                    if ((text.includes('本地上传') || text.includes('上传图片')) &&
                        rect.width > 50 && rect.height > 20 && rect.top > 0) {
                        
                        return {
                            text: text,
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2
                        };
                    }
                }
                
                return null;
            }
        """)
        
        if upload_btn_info:
            print(f"[OK] 找到按钮: '{upload_btn_info['text']}'")
            print(f"位置: ({upload_btn_info['x']}, {upload_btn_info['y']})")
            
            await page.mouse.click(upload_btn_info['x'], upload_btn_info['y'])
            await asyncio.sleep(2)
            print("[OK] 已点击上传按钮")
        else:
            print("[FAIL] 未找到'本地上传'按钮")
            return
        
        # 步骤3：查找file input并上传文件
        print("\n【步骤3】上传文件...")
        
        # 准备测试图片
        test_image = os.path.abspath('logs/test_cover.jpg')
        if not os.path.exists(test_image):
            from PIL import Image
            img = Image.new('RGB', (800, 600), color='blue')
            img.save(test_image)
            print(f"创建测试图片: {test_image}")
        
        try:
            # 查找file input
            file_inputs = await page.evaluate("""
                () => document.querySelectorAll('input[type="file"]').length
            """)
            
            if file_inputs > 0:
                print(f"[OK] 找到 {file_inputs} 个file input")
                
                # 上传文件
                await page.locator('input[type="file"]').first.set_input_files(test_image)
                print("[OK] 文件已设置")
                
                await asyncio.sleep(5)
                
                # 检查封面是否显示
                cover_displayed = await page.evaluate("""
                    () => {
                        const imgs = document.querySelectorAll('img');
                        for (const img of imgs) {
                            const rect = img.getBoundingClientRect();
                            if (rect.width > 100 && rect.height > 100 && rect.top > 200) {
                                if (img.src && !img.src.includes('data:')) {
                                    console.log('封面图:', img.src.substring(0, 100));
                                    return true;
                                }
                            }
                        }
                        return false;
                    }
                """)
                
                if cover_displayed:
                    print("\n" + "=" * 80)
                    print("[SUCCESS] 封面图上传成功！")
                    print("=" * 80)
                else:
                    print("[FAIL] 封面图未显示")
                    await page.screenshot(path='logs/final_result.png', full_page=True)
            else:
                print("[FAIL] 未找到file input")
        
        except Exception as e:
            print(f"[ERROR] {e}")
            import traceback
            traceback.print_exc()
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(full_upload_flow())
