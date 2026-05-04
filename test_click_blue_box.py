"""
根据截图坐标直接点击蓝色方框
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def click_cover_by_coords():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            print("跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        print("=" * 80)
        print("根据截图坐标点击蓝色方框")
        print("=" * 80)
        
        # 先截图查看当前页面
        await page.screenshot(path='logs/page_before_click.png', full_page=True)
        print("\n已保存截图: logs/page_before_click.png")
        
        # 根据您提供的截图，蓝色方框大概在：
        # - 左侧有"* 展示封面"文字
        # - 右侧有"单图"、"三图"、"无封面"单选按钮
        # - 蓝色方框在"单图"下方
        
        print("\n【步骤1】尝试多种方式找到蓝色方框...")
        
        # 方法1：查找包含"单图"的元素，然后找它下方的方框
        box_coords = await page.evaluate("""
            () => {
                // 查找所有元素
                const allElements = document.querySelectorAll('*');
                
                for (const el of allElements) {
                    const text = (el.textContent || '').trim();
                    const rect = el.getBoundingClientRect();
                    
                    // 查找"单图"文字
                    if (text === '单图' && rect.width > 20 && rect.height > 20) {
                        console.log('找到"单图":', rect);
                        
                        // 在"单图"下方查找方形区域
                        // 向下偏移50-200像素
                        const searchTop = rect.top + 30;
                        const searchBottom = rect.top + 250;
                        const searchLeft = rect.left - 50;
                        const searchRight = rect.left + 250;
                        
                        // 查找在这个区域内的方形div
                        const allDivs = document.querySelectorAll('div');
                        for (const div of allDivs) {
                            const divRect = div.getBoundingClientRect();
                            
                            // 方形区域，宽度150-250，高度150-250
                            if (divRect.top >= searchTop && divRect.bottom <= searchBottom &&
                                divRect.left >= searchLeft && divRect.right <= searchRight &&
                                divRect.width >= 150 && divRect.width <= 300 &&
                                divRect.height >= 100 && divRect.height <= 250) {
                                
                                // 检查是否是蓝色边框或有特定样式
                                const style = window.getComputedStyle(div);
                                if (style.borderColor.includes('rgb(22, 119, 255)') || // 蓝色
                                    style.borderColor.includes('rgb(64, 158, 255)') ||  // 另一种蓝色
                                    div.className.includes('cover') ||
                                    div.className.includes('upload')) {
                                    
                                    return {
                                        method: 'below_dantu',
                                        x: divRect.left + divRect.width / 2,
                                        y: divRect.top + divRect.height / 2,
                                        width: divRect.width,
                                        height: divRect.height,
                                        className: div.className.substring(0, 100)
                                    };
                                }
                            }
                        }
                    }
                }
                
                // 方法2：直接查找所有方形区域
                const allDivs = document.querySelectorAll('div');
                for (const div of allDivs) {
                    const rect = div.getBoundingClientRect();
                    const text = (div.textContent || '').trim();
                    
                    // 方形，宽度150-300，高度100-250，位置在页面中上部
                    if (rect.width >= 150 && rect.width <= 300 &&
                        rect.height >= 100 && rect.height <= 250 &&
                        rect.top > 300 && rect.top < 800 &&
                        rect.left > 200) {
                        
                        const style = window.getComputedStyle(div);
                        
                        // 检查是否有蓝色边框、虚线边框、或包含"+"号
                        if ((style.borderStyle === 'dashed' || 
                             style.borderColor.includes('22, 119, 255') ||
                             style.borderColor.includes('64, 158, 255') ||
                             text.includes('+')) &&
                            !text.includes('展示封面')) { // 排除标签文字
                            
                            return {
                                method: 'square_box',
                                x: rect.left + rect.width / 2,
                                y: rect.top + rect.height / 2,
                                width: rect.width,
                                height: rect.height,
                                className: div.className.substring(0, 100),
                                hasPlus: text.includes('+')
                            };
                        }
                    }
                }
                
                return null;
            }
        """)
        
        if box_coords:
            print(f"   [OK] 找到蓝色方框！")
            print(f"   方法: {box_coords['method']}")
            print(f"   位置: ({box_coords['x']}, {box_coords['y']})")
            print(f"   尺寸: {box_coords['width']}x{box_coords['height']}")
            print(f"   类名: {box_coords['className']}")
            
            # 点击蓝色方框
            print(f"\n【步骤2】点击蓝色方框...")
            await page.mouse.click(box_coords['x'], box_coords['y'])
            
            await asyncio.sleep(3)
            
            # 截图
            await page.screenshot(path='logs/after_click_blue_box.png', full_page=True)
            print("   [OK] 截图已保存: logs/after_click_blue_box.png")
            
            # 检查对话框
            print(f"\n【步骤3】检查对话框...")
            dialog_found = await page.evaluate("""
                () => {
                    const dialogs = document.querySelectorAll('[class*="dialog"], [class*="modal"], [role="dialog"]');
                    for (const dialog of dialogs) {
                        const rect = dialog.getBoundingClientRect();
                        if (rect.width > 200 && rect.height > 200) {
                            return true;
                        }
                    }
                    return false;
                }
            """)
            
            if dialog_found:
                print("   [OK] 对话框已打开！")
                
                # 查找"本地上传"按钮
                print(f"\n【步骤4】查找'本地上传'按钮...")
                upload_btn = await page.evaluate("""
                    () => {
                        const allElements = document.querySelectorAll('button, [role="button"], span, div');
                        
                        for (const el of allElements) {
                            const text = (el.textContent || '').trim();
                            const rect = el.getBoundingClientRect();
                            
                            if ((text.includes('本地上传') || text.includes('上传图片') || 
                                 text === '上传' || text.includes('选择图片')) &&
                                rect.width > 50 && rect.height > 20 && rect.top > 0) {
                                
                                return {
                                    text: text,
                                    x: rect.left + rect.width / 2,
                                    y: rect.top + rect.height / 2,
                                    tagName: el.tagName
                                };
                            }
                        }
                        
                        return null;
                    }
                """)
                
                if upload_btn:
                    print(f"   [OK] 找到上传按钮: '{upload_btn['text']}'")
                    print(f"   位置: ({upload_btn['x']}, {upload_btn['y']})")
                    
                    # 点击上传按钮
                    print(f"\n【步骤5】点击上传按钮...")
                    await page.mouse.click(upload_btn['x'], upload_btn['y'])
                    
                    await asyncio.sleep(2)
                    await page.screenshot(path='logs/after_click_upload.png', full_page=True)
                    print("   [OK] 截图已保存")
                    
                    # 检查file input
                    print(f"\n【步骤6】检查file input...")
                    file_inputs = await page.evaluate("""
                        () => document.querySelectorAll('input[type="file"]').length
                    """)
                    
                    if file_inputs > 0:
                        print(f"   [OK] 找到 {file_inputs} 个file input！")
                        
                        # 上传文件
                        test_image = os.path.abspath('logs/test_cover.jpg')
                        if not os.path.exists(test_image):
                            from PIL import Image
                            img = Image.new('RGB', (800, 600), color='green')
                            img.save(test_image)
                        
                        print(f"\n【步骤7】上传文件...")
                        try:
                            await page.locator('input[type="file"]').first.set_input_files(test_image)
                            print("   [OK] 文件已上传！")
                            
                            await asyncio.sleep(3)
                            await page.screenshot(path='logs/after_file_upload.png', full_page=True)
                            
                            # 验证
                            cover_shown = await page.evaluate("""
                                () => {
                                    const imgs = document.querySelectorAll('img');
                                    for (const img of imgs) {
                                        const rect = img.getBoundingClientRect();
                                        if (rect.width > 100 && rect.height > 100 && rect.top > 400) {
                                            if (img.src && !img.src.includes('data:')) {
                                                return true;
                                            }
                                        }
                                    }
                                    return false;
                                }
                            """)
                            
                            if cover_shown:
                                print("   [SUCCESS] 封面图上传成功！")
                            else:
                                print("   [FAIL] 封面图未显示")
                        
                        except Exception as e:
                            print(f"   [ERROR] {e}")
                    else:
                        print("   [FAIL] 未找到file input")
                else:
                    print("   [FAIL] 未找到上传按钮")
                    print("   请查看截图: logs/after_click_blue_box.png")
            else:
                print("   [FAIL] 对话框未打开")
                print("   请查看截图: logs/after_click_blue_box.png")
        else:
            print("   [FAIL] 未找到蓝色方框")
            print("   建议：手动查看截图 logs/page_before_click.png，确定坐标后告诉我")
        
        print("\n" + "=" * 80)
        print("测试完成！")
        print("=" * 80)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(click_cover_by_coords())
