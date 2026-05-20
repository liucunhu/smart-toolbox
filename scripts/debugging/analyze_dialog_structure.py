"""
分析打开的对话框结构
"""
import asyncio
from playwright.async_api import async_playwright

async def analyze_dialog():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            print("跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        print("=" * 80)
        print("分析对话框结构")
        print("=" * 80)
        
        # 先点击封面区域打开对话框
        print("\n打开对话框...")
        await page.evaluate("""
            () => {
                const divs = document.querySelectorAll('div');
                for (const div of divs) {
                    const text = (div.textContent || '').trim();
                    if (text.includes('展示封面') && text.length < 50) {
                        div.click();
                        return true;
                    }
                }
                return false;
            }
        """)
        
        await asyncio.sleep(3)
        
        # 分析对话框的所有元素
        print("\n【步骤1】分析对话框中的所有元素...")
        dialog_structure = await page.evaluate("""
            () => {
                const results = {
                    allElements: [],
                    clickableElements: [],
                    images: [],
                    buttons: [],
                    inputs: []
                };
                
                // 查找所有对话框相关的元素
                const dialogs = document.querySelectorAll('[class*="dialog"], [class*="modal"], [role="dialog"], .byte-modal, .byted-modal');
                
                if (dialogs.length === 0) {
                    // 如果没有找到标准对话框，尝试找覆盖层
                    const overlays = document.querySelectorAll('[class*="overlay"], [class*="mask"], [class*="wrapper"]');
                    for (const overlay of overlays) {
                        const rect = overlay.getBoundingClientRect();
                        if (rect.width > window.innerWidth * 0.5 && rect.height > window.innerHeight * 0.5) {
                            dialogs.push(overlay);
                        }
                    }
                }
                
                for (const dialog of dialogs) {
                    // 获取对话框内所有元素
                    const allEls = dialog.querySelectorAll('*');
                    
                    for (const el of allEls) {
                        const rect = el.getBoundingClientRect();
                        const text = (el.textContent || '').trim();
                        
                        // 只记录可见的元素
                        if (rect.width > 0 && rect.height > 0 && rect.top >= 0) {
                            const elementInfo = {
                                tagName: el.tagName,
                                className: el.className.substring(0, 100),
                                text: text.substring(0, 50),
                                position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                                size: { width: Math.round(rect.width), height: Math.round(rect.height) }
                            };
                            
                            results.allElements.push(elementInfo);
                            
                            // 检查是否可点击
                            if (el.tagName === 'BUTTON' || 
                                el.getAttribute('role') === 'button' ||
                                el.onclick ||
                                el.style.cursor === 'pointer') {
                                results.clickableElements.push(elementInfo);
                            }
                            
                            // 检查是否是图片
                            if (el.tagName === 'IMG') {
                                results.images.push({
                                    ...elementInfo,
                                    src: el.src ? el.src.substring(0, 100) : ''
                                });
                            }
                            
                            // 检查是否是输入框
                            if (el.tagName === 'INPUT') {
                                results.inputs.push({
                                    ...elementInfo,
                                    type: el.type,
                                    accept: el.accept
                                });
                            }
                        }
                    }
                }
                
                return results;
            }
        """)
        
        print(f"\n   对话框中找到:")
        print(f"      - {len(dialog_structure['allElements'])} 个元素")
        print(f"      - {len(dialog_structure['clickableElements'])} 个可点击元素")
        print(f"      - {len(dialog_structure['images'])} 个图片")
        print(f"      - {len(dialog_structure['buttons'])} 个按钮")
        print(f"      - {len(dialog_structure['inputs'])} 个输入框")
        
        # 显示所有可点击元素
        if dialog_structure['clickableElements']:
            print(f"\n   【可点击元素列表】")
            for i, el in enumerate(dialog_structure['clickableElements'][:20]):
                print(f"      [{i}] <{el['tagName']}> '{el['text']}' @ ({el['position']['top']}, {el['position']['left']}) {el['size']['width']}x{el['size']['height']}")
                print(f"          class: {el['className'][:80]}")
        
        # 显示所有图片
        if dialog_structure['images']:
            print(f"\n   【图片列表】")
            for i, img in enumerate(dialog_structure['images']):
                print(f"      [{i}] '{img['text']}' src: {img['src'][:80]}")
        
        # 显示所有输入框
        if dialog_structure['inputs']:
            print(f"\n   【输入框列表】")
            for i, inp in enumerate(dialog_structure['inputs']):
                print(f"      [{i}] type={inp['type']}, accept={inp['accept']}")
        
        # 尝试点击第一个可点击元素
        if dialog_structure['clickableElements']:
            print(f"\n【步骤2】尝试点击第一个可点击元素...")
            
            first_clickable = dialog_structure['clickableElements'][0]
            print(f"   点击: <{first_clickable['tagName']}> '{first_clickable['text']}'")
            
            click_result = await page.evaluate("""
                (elementInfo) => {
                    const dialogs = document.querySelectorAll('[class*="dialog"], [class*="modal"], [role="dialog"], .byte-modal, .byted-modal');
                    
                    for (const dialog of dialogs) {
                        const allEls = dialog.querySelectorAll('*');
                        let count = 0;
                        
                        for (const el of allEls) {
                            const rect = el.getBoundingClientRect();
                            const text = (el.textContent || '').trim();
                            
                            if (rect.width > 0 && rect.height > 0 && rect.top >= 0) {
                                if (count === 0) {  // 第一个可点击元素
                                    console.log('点击元素:', el.tagName, text);
                                    
                                    // 多种方式触发
                                    el.click();
                                    
                                    const event = new MouseEvent('click', {
                                        view: window,
                                        bubbles: true,
                                        cancelable: true
                                    });
                                    el.dispatchEvent(event);
                                    
                                    return true;
                                }
                                count++;
                            }
                        }
                    }
                    return false;
                }
            """, first_clickable)
            
            await asyncio.sleep(2)
            await page.screenshot(path='logs/after_click_first_element.png', full_page=True)
            print("   [OK] 已点击，截图保存")
        
        # 保存完整的对话框HTML
        print(f"\n【步骤3】保存对话框HTML...")
        dialog_html = await page.evaluate("""
            () => {
                const dialogs = document.querySelectorAll('[class*="dialog"], [class*="modal"], [role="dialog"], .byte-modal, .byted-modal');
                if (dialogs.length > 0) {
                    return dialogs[0].outerHTML;
                }
                return '';
            }
        """)
        
        if dialog_html:
            with open('logs/dialog_structure.html', 'w', encoding='utf-8') as f:
                f.write(dialog_html)
            print("   [OK] 对话框HTML已保存到 logs/dialog_structure.html")
        else:
            print("   [FAIL] 未找到对话框HTML")
        
        print("\n" + "=" * 80)
        print("分析完成！")
        print("=" * 80)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(analyze_dialog())
