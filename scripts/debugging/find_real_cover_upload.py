"""
直接找到并点击真正的封面上传区域
"""
import asyncio
from playwright.async_api import async_playwright

async def find_and_click_cover_upload():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            print("跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        print("=" * 80)
        print("查找并点击真正的封面上传区域")
        print("=" * 80)
        
        # 详细分析页面上所有包含"+"号的元素
        print("\n【步骤1】查找所有可能的'+'号元素...")
        plus_elements = await page.evaluate("""
            () => {
                const results = [];
                
                // 查找所有元素
                const allElements = document.querySelectorAll('*');
                
                for (const el of allElements) {
                    const text = (el.textContent || '').trim();
                    const rect = el.getBoundingClientRect();
                    
                    // 条件1：文本只包含"+"
                    if (text === '+' && rect.width > 20 && rect.height > 20 && rect.top > 400) {
                        results.push({
                            type: 'plus_text',
                            tagName: el.tagName,
                            className: el.className.substring(0, 100),
                            text: text,
                            position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                            size: { width: Math.round(rect.width), height: Math.round(rect.height) },
                            parentClass: el.parentElement ? el.parentElement.className.substring(0, 100) : ''
                        });
                    }
                    
                    // 条件2：类名包含cover或upload
                    const className = typeof el.className === 'string' ? el.className : (el.className.baseVal || '');
                    if ((className.includes('cover') || className.includes('upload')) && 
                        rect.width > 50 && rect.height > 50 && rect.top > 400) {
                        results.push({
                            type: 'cover_class',
                            tagName: el.tagName,
                            className: el.className.substring(0, 100),
                            text: text.substring(0, 30),
                            position: { top: Math.round(rect.top), left: Math.round(rect.left) },
                            size: { width: Math.round(rect.width), height: Math.round(rect.height) }
                        });
                    }
                }
                
                return results;
            }
        """)
        
        print(f"   找到 {len(plus_elements)} 个相关元素:")
        for i, el in enumerate(plus_elements[:20]):
            print(f"      [{i}] [{el['type']}] <{el['tagName']}> @ ({el['position']['top']}, {el['position']['left']}) {el['size']['width']}x{el['size']['height']}")
            print(f"          class: {el['className'][:80]}")
            if 'parentClass' in el:
                print(f"          parent: {el['parentClass'][:80]}")
        
        # 方法：直接点击第一个找到的"+"号
        if plus_elements:
            print(f"\n【步骤2】点击第一个'+'号元素...")
            
            first_plus = plus_elements[0]
            click_x = first_plus['position']['left'] + first_plus['size']['width'] / 2
            click_y = first_plus['position']['top'] + first_plus['size']['height'] / 2
            
            print(f"   点击位置: ({click_x}, {click_y})")
            
            # 先截图
            await page.screenshot(path='logs/before_click_plus.png', full_page=True)
            
            # 使用鼠标点击
            await page.mouse.click(click_x, click_y)
            
            await asyncio.sleep(3)
            
            # 截图查看结果
            await page.screenshot(path='logs/after_click_plus.png', full_page=True)
            print("   [OK] 已点击，截图保存")
            
            # 检查是否有对话框
            dialog_check = await page.evaluate("""
                () => {
                    // 查找所有可能的对话框
                    const selectors = [
                        '[class*="dialog"]',
                        '[class*="modal"]',
                        '[role="dialog"]',
                        '.byte-modal',
                        '.byted-modal',
                        '[class*="popup"]',
                        '[class*="popover"]'
                    ];
                    
                    let count = 0;
                    for (const selector of selectors) {
                        const els = document.querySelectorAll(selector);
                        count += els.length;
                    }
                    
                    return count;
                }
            """)
            
            print(f"   检测到 {dialog_check} 个对话框元素")
            
            if dialog_check > 0:
                print("   [OK] 对话框已打开！")
                
                # 分析对话框内容
                print("\n【步骤3】分析对话框内容...")
                dialog_content = await page.evaluate("""
                    () => {
                        const content = {
                            buttons: [],
                            inputs: [],
                            texts: []
                        };
                        
                        // 获取所有可见的按钮
                        const buttons = document.querySelectorAll('button, [role="button"], [onclick]');
                        for (const btn of buttons) {
                            const rect = btn.getBoundingClientRect();
                            const text = (btn.textContent || '').trim();
                            
                            if (rect.width > 0 && rect.height > 0 && rect.top > 0 && text.length > 0) {
                                content.buttons.push({
                                    text: text.substring(0, 50),
                                    tagName: btn.tagName,
                                    className: btn.className.substring(0, 80)
                                });
                            }
                        }
                        
                        // 获取所有输入框
                        const inputs = document.querySelectorAll('input');
                        for (const inp of inputs) {
                            const rect = inp.getBoundingClientRect();
                            if (rect.width > 0 && rect.height > 0) {
                                content.inputs.push({
                                    type: inp.type,
                                    accept: inp.accept,
                                    id: inp.id
                                });
                            }
                        }
                        
                        // 获取所有文本（可能包含"上传"、"本地"等关键词）
                        const allDivs = document.querySelectorAll('div, span');
                        for (const div of allDivs) {
                            const text = (div.textContent || '').trim();
                            if (text.includes('上传') || text.includes('本地') || text.includes('选择') || text.includes('图片')) {
                                const rect = div.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0 && rect.top > 0) {
                                    content.texts.push({
                                        text: text.substring(0, 50),
                                        tagName: div.tagName,
                                        className: div.className.substring(0, 80)
                                    });
                                }
                            }
                        }
                        
                        return content;
                    }
                """)
                
                print(f"   对话框中找到:")
                print(f"      - {len(dialog_content['buttons'])} 个按钮")
                print(f"      - {len(dialog_content['inputs'])} 个输入框")
                print(f"      - {len(dialog_content['texts'])} 个相关文本")
                
                if dialog_content['buttons']:
                    print(f"\n   按钮列表:")
                    for btn in dialog_content['buttons']:
                        print(f"      - [{btn['tagName']}] '{btn['text']}'")
                
                if dialog_content['inputs']:
                    print(f"\n   输入框列表:")
                    for inp in dialog_content['inputs']:
                        print(f"      - type={inp['type']}, accept={inp['accept']}")
                
                if dialog_content['texts']:
                    print(f"\n   相关文本:")
                    for txt in dialog_content['texts'][:10]:
                        print(f"      - '{txt['text']}'")
                
                # 如果有file input，直接使用它
                file_inputs = await page.evaluate("""
                    () => {
                        const inputs = document.querySelectorAll('input[type="file"]');
                        return inputs.length;
                    }
                """)
                
                if file_inputs > 0:
                    print(f"\n   [OK] 找到 {file_inputs} 个file input！")
                    print("   可以直接使用set_input_files上传文件")
                else:
                    print(f"\n   [FAIL] 未找到file input")
                    print("   说明：对话框可能使用了自定义上传机制")
            else:
                print("   [FAIL] 对话框未打开")
        else:
            print("   [FAIL] 未找到'+'号元素")
        
        print("\n" + "=" * 80)
        print("测试完成！")
        print("=" * 80)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_and_click_cover_upload())
