"""
头条文章配图上传独立测试脚本
只测试图片上传功能,跳过封面、标题、正文等其他步骤
"""
import asyncio
import os
from playwright.async_api import async_playwright

async def test_article_image_upload():
    """测试文章配图上传功能"""
    async with async_playwright() as p:
        # 连接到已启动的 Edge 浏览器
        browser = await p.chromium.connect_over_cdp("http://localhost:9222")
        page = browser.contexts[0].pages[0]
        
        print("=" * 80)
        print(" 头条文章配图上传独立测试")
        print("=" * 80)
        
        # 确保在发布页面
        print("\n[1/6] 确保在发布页面...")
        current_url = page.url
        if "publish" not in current_url:
            print(f"   当前URL: {current_url}")
            print("   正在跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
            await page.wait_for_selector('[contenteditable="true"]', timeout=10000)
            print("   ✅ 已进入发布页面")
        else:
            print(f"   ✅ 已在发布页面: {current_url}")
        
        # 填写一些基本内容(头条要求必须有标题和正文才能上传图片)
        print("\n[2/6] 填写基本内容...")
        await page.evaluate("""
            () => {
                const titleInput = document.querySelector('textarea[placeholder*="标题"]');
                if (titleInput) {
                    titleInput.value = '测试文章配图上传';
                    titleInput.dispatchEvent(new Event('input', { bubbles: true }));
                    titleInput.dispatchEvent(new Event('change', { bubbles: true }));
                }
                
                const editor = document.querySelector('div[contenteditable="true"]');
                if (editor) {
                    editor.innerHTML = '<p>这是一段测试文本,用于测试配图上传功能。</p>';
                    editor.dispatchEvent(new Event('input', { bubbles: true }));
                }
            }
        """)
        await asyncio.sleep(2)
        print("   ✅ 已填写标题和正文")
        
        # 准备测试图片
        print("\n[3/6] 准备测试图片...")
        test_image_path = os.path.abspath("uploads/article_images/article_img_7546d99b.jpg")
        if not os.path.exists(test_image_path):
            # 如果测试图片不存在,使用封面图
            test_image_path = os.path.abspath("uploads/llm_covers/llm_cover_1777874449_3677.jpg")
        
        if not os.path.exists(test_image_path):
            print(f"   ⚠️  测试图片不存在: {test_image_path}")
            print("   请先运行完整测试生成图片,或手动准备一张测试图片")
            return
        
        print(f"   📄 测试图片路径: {test_image_path}")
        print(f"    图片大小: {os.path.getsize(test_image_path) / 1024:.2f} KB")
        
        # 点击图片按钮
        print("\n[4/6] 点击工具栏图片按钮...")
        button_info = await page.evaluate("""
            () => {
                const buttons = document.querySelectorAll('.syl-toolbar-button');
                console.log('找到工具栏按钮数量:', buttons.length);
                
                // 图片按钮通常在第12个位置
                if (buttons.length >= 12) {
                    const imageButton = buttons[11]; // 索引从0开始
                    const rect = imageButton.getBoundingClientRect();
                    imageButton.click();
                    return {
                        found: true,
                        position: 12,
                        rect: { x: rect.left, y: rect.top, width: rect.width, height: rect.height }
                    };
                }
                return { found: false };
            }
        """)
        
        if button_info.get('found'):
            print(f"   ✅ 已点击第 {button_info['position']} 个按钮(图片按钮)")
            print(f"      按钮位置: x={button_info['rect']['x']}, y={button_info['rect']['y']}")
        else:
            print("   ❌ 未找到图片按钮")
            return
        
        await asyncio.sleep(2)
        
        # 点击"本地上传"按钮
        print("\n[5/6] 点击'本地上传'按钮...")
        upload_clicked = await page.evaluate("""
            () => {
                const allElements = document.querySelectorAll('button, [role="button"], span, div');
                for (const el of allElements) {
                    const text = (el.textContent || '').trim();
                    const rect = el.getBoundingClientRect();
                    if (text.includes('本地上传') && rect.width > 50 && rect.top > 0) {
                        el.click();
                        console.log('点击了本地上传按钮');
                        return true;
                    }
                }
                return false;
            }
        """)
        
        if upload_clicked:
            print("   ✅ 已点击'本地上传'按钮")
        else:
            print("   ️  未找到'本地上传'按钮")
        
        await asyncio.sleep(2)
        
        # 上传文件
        print("\n[6/6] 上传文件...")
        file_input = page.locator('input[type="file"]').first
        try:
            await file_input.set_input_files(test_image_path, timeout=5000)
            print("   ✅ 文件已上传")
        except Exception as e:
            print(f"   ❌ 文件上传失败: {e}")
            return
        
        # ★★★ 调试:等待图片上传完成 ★★★
        print("\n   ⏳ 等待图片上传和处理(15秒)...")
        await asyncio.sleep(15)
        
        # 保存对话框截图
        print("   📸 保存对话框截图...")
        await page.screenshot(path='logs/article_image_upload_dialog.png', full_page=False)
        print("   ✅ 截图已保存: logs/article_image_upload_dialog.png")
        
        # 查看对话框HTML
        print("\n    分析对话框结构...")
        dialog_info = await page.evaluate("""
            () => {
                const result = {
                    dialogs: [],
                    buttons: [],
                    images: []
                };
                
                // 查找对话框
                const dialogs = document.querySelectorAll('.byte-modal, .byte-dialog, [role="dialog"], .upload-image-panel, .byted-drawer');
                dialogs.forEach((dialog, index) => {
                    const rect = dialog.getBoundingClientRect();
                    result.dialogs.push({
                        index,
                        className: dialog.className,
                        visible: rect.width > 0 && rect.top > 0,
                        width: rect.width,
                        height: rect.height
                    });
                });
                
                // 查找所有按钮
                const allButtons = document.querySelectorAll('button, [role="button"], div[role="button"]');
                allButtons.forEach((btn, index) => {
                    const text = (btn.textContent || '').trim();
                    const rect = btn.getBoundingClientRect();
                    if (text && rect.width > 0 && rect.top > 0) {
                        result.buttons.push({
                            index,
                            text: text.substring(0, 20), // 限制长度
                            fullText: text,
                            tagName: btn.tagName,
                            className: btn.className,
                            width: Math.round(rect.width),
                            height: Math.round(rect.height),
                            top: Math.round(rect.top),
                            left: Math.round(rect.left)
                        });
                    }
                });
                
                // 查找图片预览
                const images = document.querySelectorAll('.upload-image-panel img, .image-preview img, [role="dialog"] img');
                images.forEach((img, index) => {
                    const rect = img.getBoundingClientRect();
                    result.images.push({
                        index,
                        src: img.src.substring(0, 80),
                        width: Math.round(rect.width),
                        height: Math.round(rect.height)
                    });
                });
                
                return result;
            }
        """)
        
        print(f"\n   📊 对话框信息:")
        for dialog in dialog_info['dialogs']:
            print(f"      对话框 {dialog['index']}: class='{dialog['className'][:50]}', visible={dialog['visible']}, size={dialog['width']}x{dialog['height']}")
        
        print(f"\n   📊 找到 {len(dialog_info['buttons'])} 个可见按钮:")
        for btn in dialog_info['buttons'][:15]:  # 只显示前15个
            print(f"      [{btn['index']}] <{btn['tagName']}> '{btn['text']}' ({btn['width']}x{btn['height']}) at ({btn['left']},{btn['top']})")
        
        print(f"\n    找到 {len(dialog_info['images'])} 个图片预览:")
        for img in dialog_info['images']:
            print(f"      图片 {img['index']}: {img['src']}... ({img['width']}x{img['height']})")
        
        # ★★★ 尝试点击"确定"按钮 ★★★
        print("\n   🔍 尝试点击'确定'按钮...")
        
        # 策略1: 直接查找"确定"按钮
        confirm_clicked = await page.evaluate("""
            () => {
                const allButtons = document.querySelectorAll('button, [role="button"], div[role="button"]');
                for (const btn of allButtons) {
                    const text = (btn.textContent || '').trim();
                    const rect = btn.getBoundingClientRect();
                    if ((text === '确定' || text === '确认' || text === '完成') && 
                        rect.width > 50 && rect.top > 0) {
                        console.log('找到确定按钮:', text, rect);
                        btn.click();
                        return { success: true, method: 'direct', text: text };
                    }
                }
                return { success: false, method: null };
            }
        """)
        
        if confirm_clicked.get('success'):
            print(f"   ✅ 已点击'确定'按钮 (方法: {confirm_clicked['method']})")
            await asyncio.sleep(3)
        else:
            print("   ⚠️  未找到'确定'按钮")
            
            # 策略2: 尝试滚动对话框后再查找
            print("\n   🔄 尝试滚动对话框...")
            await page.evaluate("""
                () => {
                    const dialogs = document.querySelectorAll('.byte-modal-content, .byte-dialog-body, .upload-image-panel, [role="dialog"]');
                    dialogs.forEach(dialog => {
                        dialog.scrollTop = dialog.scrollHeight;
                        console.log('滚动对话框:', dialog.className);
                    });
                }
            """)
            await asyncio.sleep(2)
            
            # 再次尝试点击
            confirm_clicked = await page.evaluate("""
                () => {
                    const allButtons = document.querySelectorAll('button, [role="button"], div[role="button"]');
                    for (const btn of allButtons) {
                        const text = (btn.textContent || '').trim();
                        const rect = btn.getBoundingClientRect();
                        if ((text === '确定' || text === '确认' || text === '完成') && 
                            rect.width > 50 && rect.top > 0) {
                            btn.click();
                            return { success: true, method: 'after_scroll' };
                        }
                    }
                    return { success: false };
                }
            """)
            
            if confirm_clicked.get('success'):
                print(f"   ✅ 滚动后已点击'确定'按钮 (方法: {confirm_clicked['method']})")
                await asyncio.sleep(3)
            else:
                print("   ❌ 滚动后仍未找到'确定'按钮")
        
        # 检查编辑器中的图片
        print("\n   📊 验证编辑器中的图片...")
        img_count = await page.evaluate("""
            () => {
                const editor = document.querySelector('div[contenteditable="true"]');
                if (!editor) return 0;
                return editor.querySelectorAll('img').length;
            }
        """)
        
        print(f"   📊 编辑器中图片数量: {img_count}")
        
        if img_count > 0:
            print("   ✅✅✅ 图片已成功插入编辑器! ✅✅✅")
        else:
            print("   ❌ 图片未插入编辑器")
            print("   💡 请检查截图: logs/article_image_upload_dialog.png")
            print("   💡 根据按钮信息调整代码中的查找逻辑")
        
        print("\n" + "=" * 80)
        print("测试完成!")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_article_image_upload())
