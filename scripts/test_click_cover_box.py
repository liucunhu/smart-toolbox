"""
直接点击蓝色方框（封面上传区域）
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def click_cover_box():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            print("跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        print("=" * 80)
        print("点击蓝色方框（封面上传区域）")
        print("=" * 80)
        
        # 步骤1：找到蓝色方框的位置
        print("\n【步骤1】定位蓝色方框...")
        
        box_position = await page.evaluate("""
            () => {
                // 查找所有div，找到包含"展示封面"且尺寸合适的
                const allDivs = document.querySelectorAll('div');
                
                for (const div of allDivs) {
                    const text = (div.textContent || '').trim();
                    const rect = div.getBoundingClientRect();
                    
                    // 条件：包含"展示封面"，宽度在200-300之间，高度在150-250之间
                    if (text.includes('展示封面') && 
                        rect.width > 150 && rect.width < 350 &&
                        rect.height > 100 && rect.height < 300 &&
                        rect.top > 400) {
                        
                        return {
                            x: rect.left + rect.width / 2,
                            y: rect.top + rect.height / 2,
                            width: rect.width,
                            height: rect.height,
                            top: rect.top,
                            left: rect.left,
                            className: div.className.substring(0, 100)
                        };
                    }
                }
                
                return null;
            }
        """)
        
        if box_position:
            print(f"   找到蓝色方框！")
            print(f"   位置: ({box_position['left']}, {box_position['top']})")
            print(f"   尺寸: {box_position['width']}x{box_position['height']}")
            print(f"   中心点: ({box_position['x']}, {box_position['y']})")
            print(f"   类名: {box_position['className']}")
            
            # 先截图
            await page.screenshot(path='logs/before_click_box.png', full_page=True)
            
            # 步骤2：点击蓝色方框
            print(f"\n【步骤2】点击蓝色方框中心...")
            await page.mouse.click(box_position['x'], box_position['y'])
            
            await asyncio.sleep(3)
            
            # 截图查看结果
            await page.screenshot(path='logs/after_click_box.png', full_page=True)
            print("   [OK] 已点击，截图保存")
            
            # 步骤3：检查对话框是否打开
            print(f"\n【步骤3】检查对话框...")
            
            # 查找对话框
            dialog_check = await page.evaluate("""
                () => {
                    // 查找所有可能的对话框元素
                    const selectors = [
                        '.byte-modal',
                        '.byted-modal',
                        '[class*="dialog"]',
                        '[class*="modal"]',
                        '[role="dialog"]'
                    ];
                    
                    for (const selector of selectors) {
                        const els = document.querySelectorAll(selector);
                        if (els.length > 0) {
                            // 找到第一个可见的对话框
                            for (const el of els) {
                                const rect = el.getBoundingClientRect();
                                if (rect.width > 100 && rect.height > 100) {
                                    return {
                                        found: true,
                                        selector: selector,
                                        className: el.className.substring(0, 100),
                                        position: {
                                            top: Math.round(rect.top),
                                            left: Math.round(rect.left),
                                            width: Math.round(rect.width),
                                            height: Math.round(rect.height)
                                        }
                                    };
                                }
                            }
                        }
                    }
                    
                    return { found: false };
                }
            """)
            
            if dialog_check['found']:
                print(f"   [OK] 对话框已打开！")
                print(f"   选择器: {dialog_check['selector']}")
                print(f"   位置: ({dialog_check['position']['left']}, {dialog_check['position']['top']})")
                print(f"   尺寸: {dialog_check['position']['width']}x{dialog_check['position']['height']}")
                
                # 步骤4：在对话框中查找"本地上传"按钮
                print(f"\n【步骤4】查找'本地上传'按钮...")
                
                upload_buttons = await page.evaluate("""
                    () => {
                        const buttons = [];
                        
                        // 查找所有按钮和可点击元素
                        const allElements = document.querySelectorAll('button, [role="button"], span, div');
                        
                        for (const el of allElements) {
                            const text = (el.textContent || '').trim();
                            const rect = el.getBoundingClientRect();
                            
                            // 查找包含"上传"、"本地"、"选择"的元素
                            if ((text.includes('上传') || text.includes('本地') || text.includes('选择图片')) &&
                                rect.width > 50 && rect.height > 20 &&
                                rect.top > 0) {
                                
                                buttons.push({
                                    text: text.substring(0, 50),
                                    tagName: el.tagName,
                                    className: typeof el.className === 'string' ? el.className.substring(0, 100) : '',
                                    position: {
                                        x: rect.left + rect.width / 2,
                                        y: rect.top + rect.height / 2
                                    }
                                });
                            }
                        }
                        
                        return buttons;
                    }
                """)
                
                print(f"   找到 {len(upload_buttons)} 个相关按钮:")
                for i, btn in enumerate(upload_buttons):
                    print(f"      [{i}] '{btn['text']}' @ ({btn['position']['x']}, {btn['position']['y']})")
                    print(f"          <{btn['tagName']}> class={btn['className'][:80]}")
                
                # 如果有"本地上传"按钮，点击它
                if upload_buttons:
                    print(f"\n【步骤5】点击'本地上传'按钮...")
                    
                    # 优先查找包含"本地"的按钮
                    local_upload_btn = None
                    for btn in upload_buttons:
                        if '本地' in btn['text']:
                            local_upload_btn = btn
                            break
                    
                    # 如果没有，使用第一个
                    if not local_upload_btn:
                        local_upload_btn = upload_buttons[0]
                    
                    print(f"   点击: '{local_upload_btn['text']}'")
                    await page.mouse.click(local_upload_btn['position']['x'], local_upload_btn['position']['y'])
                    
                    await asyncio.sleep(2)
                    
                    # 截图
                    await page.screenshot(path='logs/after_click_upload_btn.png', full_page=True)
                    print("   [OK] 已点击，截图保存")
                    
                    # 检查是否出现文件选择器
                    print(f"\n【步骤6】检查文件选择器...")
                    
                    file_input_exists = await page.evaluate("""
                        () => {
                            const inputs = document.querySelectorAll('input[type="file"]');
                            return inputs.length;
                        }
                    """)
                    
                    if file_input_exists > 0:
                        print(f"   [OK] 找到 {file_input_exists} 个file input！")
                        print("   现在可以直接使用set_input_files上传文件了")
                        
                        # 准备测试图片
                        test_image = os.path.abspath('logs/test_cover.jpg')
                        if not os.path.exists(test_image):
                            from PIL import Image
                            img = Image.new('RGB', (800, 600), color='green')
                            img.save(test_image)
                            print(f"   创建测试图片: {test_image}")
                        
                        # 上传文件
                        print(f"\n【步骤7】上传测试图片...")
                        try:
                            file_input = page.locator('input[type="file"]').first
                            await file_input.set_input_files(test_image)
                            print("   [OK] 文件已设置！")
                            
                            await asyncio.sleep(3)
                            await page.screenshot(path='logs/after_upload_file.png', full_page=True)
                            print("   [OK] 截图保存")
                            
                            # 检查封面是否显示
                            cover_displayed = await page.evaluate("""
                                () => {
                                    const imgs = document.querySelectorAll('img');
                                    for (const img of imgs) {
                                        const rect = img.getBoundingClientRect();
                                        if (rect.width > 100 && rect.height > 100 && rect.top > 400) {
                                            if (img.src && !img.src.includes('data:')) {
                                                console.log('找到封面图:', img.src.substring(0, 100));
                                                return true;
                                            }
                                        }
                                    }
                                    return false;
                                }
                            """)
                            
                            if cover_displayed:
                                print("   [SUCCESS] 封面图已成功上传并显示！")
                            else:
                                print("   [FAIL] 封面图未显示")
                        
                        except Exception as e:
                            print(f"   [ERROR] {e}")
                    else:
                        print(f"   [FAIL] 未找到file input")
                        print("   说明：对话框可能使用了其他方式")
                else:
                    print("   [FAIL] 未找到'本地上传'按钮")
                    print("   请查看截图: logs/after_click_box.png")
            else:
                print("   [FAIL] 对话框未打开")
                print("   请查看截图: logs/after_click_box.png")
        else:
            print("   [FAIL] 未找到蓝色方框")
        
        print("\n" + "=" * 80)
        print("测试完成！")
        print("=" * 80)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(click_cover_box())
