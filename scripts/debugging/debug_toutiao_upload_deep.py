"""
深度调试头条封面上传机制
目标：找出为什么文件设置后封面不显示
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_upload_mechanism():
    async with async_playwright() as p:
        # 连接真实浏览器
        browser = await p.chromium.connect_over_cdp(
            "http://127.0.0.1:9222"
        )
        
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        print("=" * 80)
        print("深度调试头条封面上传机制")
        print("=" * 80)
        
        # 确保在发布页面
        if "publish" not in page.url:
            print("\n跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        print(f"\n当前URL: {page.url}")
        
        # 步骤1：分析头条的所有input[type=file]元素
        print("\n【步骤1】查找所有文件输入框...")
        file_inputs = await page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input[type="file"]');
                return Array.from(inputs).map((input, index) => ({
                    index,
                    id: input.id,
                    className: input.className,
                    style: input.style.cssText,
                    visible: input.offsetParent !== null,
                    rect: input.getBoundingClientRect(),
                    attributes: {
                        accept: input.accept,
                        multiple: input.multiple,
                        required: input.required
                    },
                    parentTag: input.parentElement ? input.parentElement.tagName : '',
                    parentClass: input.parentElement ? input.parentElement.className : ''
                }));
            }
        """)
        
        print(f"   找到 {len(file_inputs)} 个file input")
        for inp in file_inputs:
            print(f"   [{inp['index']}] id={inp['id']}, class={inp['className'][:50]}, visible={inp['visible']}")
        
        # 步骤2：监听网络请求（图片上传）
        print("\n【步骤2】设置网络请求监听...")
        upload_requests = []
        
        def handle_request(request):
            if any(keyword in request.url.lower() for keyword in ['upload', 'image', 'cover']):
                upload_requests.append({
                    'url': request.url,
                    'method': request.method,
                    'resource_type': request.resource_type
                })
                print(f"   📡 捕获到相关请求: {request.method} {request.url[:100]}")
        
        page.on("request", handle_request)
        
        # 步骤3：尝试点击工具栏的图片按钮
        print("\n【步骤3】尝试点击工具栏图片按钮...")
        toolbar_clicked = await page.evaluate("""
            () => {
                // 查找所有可能的图片按钮
                const buttons = document.querySelectorAll('button, [role="button"], span[onclick], div[onclick]');
                let clicked = false;
                
                for (const btn of buttons) {
                    const text = (btn.textContent || '').trim();
                    const title = btn.getAttribute('title') || '';
                    const ariaLabel = btn.getAttribute('aria-label') || '';
                    
                    // 查找包含"图片"、"插入图片"等关键词的按钮
                    if (text.includes('图片') || title.includes('图片') || ariaLabel.includes('图片')) {
                        if (text.length < 20) {  // 避免匹配到长文本
                            console.log('找到图片按钮:', text || title || ariaLabel);
                            btn.click();
                            clicked = true;
                            break;
                        }
                    }
                }
                
                return clicked;
            }
        """)
        
        await asyncio.sleep(3)
        
        if toolbar_clicked:
            print("   [OK] 已点击图片按钮")
            
            # 检查是否出现对话框
            dialog_found = await page.evaluate("""
                () => {
                    const dialogs = document.querySelectorAll('[class*="dialog"], [class*="modal"], [role="dialog"]');
                    return dialogs.length > 0;
                }
            """)
            
            if dialog_found:
                print("   [OK] 对话框已打开")
                
                # 查找对话框中的上传按钮
                upload_buttons = await page.evaluate("""
                    () => {
                        const buttons = [];
                        const allButtons = document.querySelectorAll('button, [role="button"]');
                        
                        for (const btn of allButtons) {
                            const text = (btn.textContent || '').trim();
                            if (text.includes('上传') || text.includes('本地') || text.includes('选择')) {
                                const rect = btn.getBoundingClientRect();
                                buttons.push({
                                    text: text.substring(0, 30),
                                    visible: rect.width > 0 && rect.height > 0 && rect.top > 0,
                                    rect: { top: rect.top, left: rect.left }
                                });
                            }
                        }
                        
                        return buttons;
                    }
                """)
                
                print(f"   找到 {len(upload_buttons)} 个上传相关按钮:")
                for btn in upload_buttons:
                    print(f"      - {btn['text']} (visible={btn['visible']})")
            else:
                print("   [FAIL] 对话框未打开")
        else:
            print("   [FAIL] 未找到图片按钮")
        
        # 步骤4：分析封面区域的点击事件
        print("\n【步骤4】分析封面区域的事件处理...")
        cover_events = await page.evaluate("""
            () => {
                const results = [];
                
                // 查找封面相关的容器
                const containers = document.querySelectorAll('div');
                for (const div of containers) {
                    const text = (div.textContent || '').trim();
                    if (text.includes('展示封面') && text.length < 50) {
                        const rect = div.getBoundingClientRect();
                        
                        // 获取该元素的所有事件监听器信息
                        results.push({
                            text: text,
                            rect: { top: rect.top, left: rect.left, width: rect.width, height: rect.height },
                            tagName: div.tagName,
                            className: div.className,
                            hasClickHandler: div.onclick !== null,
                            children: div.children.length
                        });
                    }
                }
                
                return results;
            }
        """)
        
        print(f"   找到 {len(cover_events)} 个封面容器:")
        for i, cover in enumerate(cover_events):
            print(f"   [{i}] {cover['text']}")
            print(f"       位置: top={cover['rect']['top']}, left={cover['rect']['left']}")
            print(f"       尺寸: {cover['rect']['width']}x{cover['rect']['height']}")
            print(f"       类名: {cover['className'][:80]}")
            print(f"       有click处理器: {cover['hasClickHandler']}")
        
        # 步骤5：尝试直接触发封面容器的点击事件
        if cover_events:
            print("\n【步骤5】尝试点击第一个封面容器...")
            click_result = await page.evaluate("""
                () => {
                    const containers = document.querySelectorAll('div');
                    for (const div of containers) {
                        const text = (div.textContent || '').trim();
                        if (text.includes('展示封面') && text.length < 50) {
                            // 尝试多种事件类型
                            const events = ['click', 'mousedown', 'mouseup'];
                            
                            for (const eventType of events) {
                                const event = new MouseEvent(eventType, {
                                    view: window,
                                    bubbles: true,
                                    cancelable: true,
                                    clientX: 100,
                                    clientY: 100
                                });
                                
                                div.dispatchEvent(event);
                            }
                            
                            // 也尝试调用onclick
                            if (div.onclick) {
                                div.onclick();
                            }
                            
                            return true;
                        }
                    }
                    return false;
                }
            """)
            
            await asyncio.sleep(3)
            
            if click_result:
                print("   [OK] 已触发封面容器点击事件")
            else:
                print("   [FAIL] 未找到封面容器")
        
        # 步骤6：保存页面HTML用于分析
        print("\n【步骤6】保存页面快照...")
        html_content = await page.content()
        with open('logs/toutiao_cover_debug.html', 'w', encoding='utf-8') as f:
            f.write(html_content)
        print("   [OK] HTML已保存到 logs/toutiao_cover_debug.html")
        
        # 步骤7：截图
        print("\n【步骤7】截图...")
        await page.screenshot(path='logs/toutiao_cover_debug.png', full_page=True)
        print("   [OK] 截图已保存到 logs/toutiao_cover_debug.png")
        
        # 步骤8：分析网络请求
        print("\n【步骤8】网络请求统计...")
        if upload_requests:
            print(f"   捕获到 {len(upload_requests)} 个上传相关请求:")
            for req in upload_requests:
                print(f"      - {req['method']} {req['url'][:80]}")
        else:
            print("   未捕获到上传请求")
        
        print("\n" + "=" * 80)
        print("调试完成！请查看以下文件：")
        print("  1. logs/toutiao_cover_debug.html - 页面HTML快照")
        print("  2. logs/toutiao_cover_debug.png - 页面截图")
        print("=" * 80)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_upload_mechanism())
