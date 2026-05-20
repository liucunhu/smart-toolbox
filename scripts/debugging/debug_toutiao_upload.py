"""
调试头条封面上传机制
目的：找出正确的上传按钮和触发方式
"""
import asyncio
from playwright.async_api import async_playwright

async def debug_toutiao_upload():
    print("=" * 80)
    print("🔍 调试头条封面上传机制")
    print("=" * 80)
    
    async with async_playwright() as p:
        # 连接到已运行的Edge浏览器
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        
        # 导航到发布页面
        print("\n[1] 导航到发布页面...")
        await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
        await asyncio.sleep(3)
        
        # 确保页面加载完成
        print("[2] 等待页面加载...")
        await page.wait_for_selector('[contenteditable="true"]', timeout=10000)
        print("   ✅ 编辑器已加载")
        await asyncio.sleep(2)
        
        # 分析封面上传区域
        print("\n[3] 分析封面上传区域...")
        upload_analysis = await page.evaluate("""
            () => {
                const results = {
                    coverLabels: [],
                    uploadAreas: [],
                    plusSigns: [],
                    allButtons: []
                };
                
                // 1. 查找"展示封面"标签
                const allDivs = document.querySelectorAll('div');
                for (const div of allDivs) {
                    const text = (div.textContent || '').trim();
                    if (text.includes('展示封面') || text.includes('封面')) {
                        const rect = div.getBoundingClientRect();
                        results.coverLabels.push({
                            text: text.substring(0, 50),
                            position: { top: rect.top, left: rect.left },
                            tagName: div.tagName,
                            className: div.className
                        });
                    }
                }
                
                // 2. 查找上传区域（通常在封面标签后面）
                for (const label of results.coverLabels) {
                    // 使用XPath风格的查找
                    const elements = document.querySelectorAll('div, span, button, label');
                    for (const el of elements) {
                        const rect = el.getBoundingClientRect();
                        // 查找在封面标签下方，且包含"+"或"上传"的元素
                        if (rect.top > label.position.top && rect.top < label.position.top + 200) {
                            const text = (el.textContent || '').trim();
                            if (text.includes('+') || text.includes('上传') || text.includes('选择')) {
                                results.uploadAreas.push({
                                    text: text.substring(0, 50),
                                    position: { top: rect.top, left: rect.left, width: rect.width, height: rect.height },
                                    tagName: el.tagName,
                                    className: el.className,
                                    id: el.id,
                                    hasClickHandler: el.onclick !== null
                                });
                            }
                        }
                    }
                }
                
                // 3. 查找所有包含"+"的元素
                const allElements = document.querySelectorAll('*');
                for (const el of allElements) {
                    const text = (el.textContent || '').trim();
                    const rect = el.getBoundingClientRect();
                    if (text === '+' && rect.width > 10 && rect.height > 10 && rect.top > 400) {
                        results.plusSigns.push({
                            tagName: el.tagName,
                            className: el.className,
                            position: { top: rect.top, left: rect.left },
                            parentClass: el.parentElement ? el.parentElement.className : ''
                        });
                    }
                }
                
                // 4. 查找所有按钮（用于对比）
                const buttons = document.querySelectorAll('button, [role="button"], [class*="btn"]');
                for (const btn of buttons) {
                    const text = (btn.textContent || '').trim();
                    if (text.length > 0 && text.length < 30) {
                        results.allButtons.push({
                            text: text,
                            tagName: btn.tagName,
                            className: btn.className
                        });
                    }
                }
                
                return results;
            }
        """)
        
        print(f"\n   📊 找到 {len(upload_analysis['coverLabels'])} 个封面标签:")
        for i, label in enumerate(upload_analysis['coverLabels'][:3]):
            print(f"      {i+1}. '{label['text']}' (位置: {label['position']['top']}, 类名: {label['className'][:50]})")
        
        print(f"\n   📊 找到 {len(upload_analysis['uploadAreas'])} 个上传区域:")
        for i, area in enumerate(upload_analysis['uploadAreas'][:5]):
            print(f"      {i+1}. '{area['text']}' (位置: {area['position']['top']}, 大小: {area['position']['width']}x{area['position']['height']})")
            print(f"         类名: {area['className'][:60]}")
            print(f"         有点击事件: {area['hasClickHandler']}")
        
        print(f"\n   📊 找到 {len(upload_analysis['plusSigns'])} 个'+'号:")
        for i, plus in enumerate(upload_analysis['plusSigns'][:5]):
            print(f"      {i+1}. 标签: {plus['tagName']}, 类名: {plus['className'][:50]}")
            print(f"         位置: {plus['position']['top']}, 父类: {plus['parentClass'][:50]}")
        
        # 尝试直接点击第一个上传区域
        if upload_analysis['uploadAreas']:
            print("\n[4] 尝试点击第一个上传区域...")
            first_area = upload_analysis['uploadAreas'][0]
            
            clicked = await page.evaluate("""
                (areaInfo) => {
                    // 通过位置查找元素
                    const elements = document.querySelectorAll('div, span, button');
                    for (const el of elements) {
                        const rect = el.getBoundingClientRect();
                        if (Math.abs(rect.top - areaInfo.position.top) < 5 && 
                            Math.abs(rect.left - areaInfo.position.left) < 5) {
                            console.log('找到目标元素:', el);
                            // 尝试多种点击方式
                            el.click();
                            el.dispatchEvent(new MouseEvent('mousedown', { bubbles: true }));
                            el.dispatchEvent(new MouseEvent('mouseup', { bubbles: true }));
                            el.dispatchEvent(new MouseEvent('click', { bubbles: true }));
                            return true;
                        }
                    }
                    return false;
                }
            """, first_area)
            
            print(f"   点击结果: {'✅ 成功' if clicked else '❌ 失败'}")
            await asyncio.sleep(3)
            
            # 保存截图
            await page.screenshot(path='logs/upload_debug_after_click.png', full_page=True)
            print("   📸 已保存截图: logs/upload_debug_after_click.png")
        
        # 检查是否有对话框打开
        print("\n[5] 检查对话框状态...")
        dialog_info = await page.evaluate("""
            () => {
                const dialogs = [];
                const allDivs = document.querySelectorAll('div');
                for (const div of allDivs) {
                    const text = (div.textContent || '').trim();
                    const style = window.getComputedStyle(div);
                    // 查找对话框特征
                    if ((text.includes('上传图片') || text.includes('本地上传')) && 
                        style.display !== 'none' && 
                        style.visibility !== 'hidden') {
                        const rect = div.getBoundingClientRect();
                        dialogs.push({
                            text: text.substring(0, 100),
                            position: { top: rect.top, left: rect.left },
                            zIndex: style.zIndex
                        });
                    }
                }
                return dialogs;
            }
        """)
        
        if dialog_info:
            print(f"   ✅ 找到 {len(dialog_info)} 个对话框:")
            for i, dialog in enumerate(dialog_info[:3]):
                print(f"      {i+1}. '{dialog['text'][:50]}...' (位置: {dialog['position']['top']})")
        else:
            print("   ❌ 未找到对话框")
        
        # 尝试通过JavaScript直接触发上传
        print("\n[6] 尝试直接触发文件上传...")
        trigger_result = await page.evaluate("""
            () => {
                // 查找input[type="file"]
                const fileInputs = document.querySelectorAll('input[type="file"]');
                console.log(`找到 ${fileInputs.length} 个文件输入框`);
                
                for (const input of fileInputs) {
                    console.log('文件输入框:', input);
                    // 尝试触发点击
                    input.click();
                    return true;
                }
                
                // 如果没有找到，尝试创建一个新的
                const newInput = document.createElement('input');
                newInput.type = 'file';
                newInput.accept = 'image/*';
                newInput.style.display = 'none';
                document.body.appendChild(newInput);
                newInput.click();
                
                console.log('已创建并触发新的文件输入框');
                return true;
            }
        """)
        
        print(f"   触发结果: {'✅ 成功' if trigger_result else '❌ 失败'}")
        await asyncio.sleep(2)
        
        # 最终截图
        await page.screenshot(path='logs/upload_debug_final.png', full_page=True)
        print("\n📸 已保存最终截图: logs/upload_debug_final.png")
        
        print("\n" + "=" * 80)
        print("✅ 调试完成！请检查截图和日志")
        print("=" * 80)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(debug_toutiao_upload())
