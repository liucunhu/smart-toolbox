"""
测试直接在编辑器中插入图片HTML
"""
import asyncio
from playwright.async_api import async_playwright
import os


async def test_insert_image_html():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            print("跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(5)
        
        # 先填写一些文本
        print("填写测试文本...")
        test_content = """这是第一段测试内容。

这是第二段内容，下面要插入图片。

这是第三段内容。"""
        
        await page.fill('div[contenteditable="true"]', test_content)
        await asyncio.sleep(2)
        
        print("=" * 80)
        print("测试直接插入图片HTML")
        print("=" * 80)
        
        # 准备测试图片（必须是可访问的URL或base64）
        test_image_path = os.path.abspath('uploads/article_images/article_img_e8c61185.jpg')
        
        if os.path.exists(test_image_path):
            # 读取图片并转换为base64
            import base64
            with open(test_image_path, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
                base64_url = f"data:image/jpeg;base64,{image_data}"
            
            print(f"图片大小: {len(image_data)} bytes")
            print("在第二段后插入图片...")
            
            # 方法：通过JavaScript在编辑器中插入img标签
            result = await page.evaluate("""
                (base64Url) => {
                    const editor = document.querySelector('div[contenteditable="true"]');
                    if (!editor) return false;
                    
                    // 获取所有段落
                    const paragraphs = editor.querySelectorAll('p');
                    if (paragraphs.length < 2) return false;
                    
                    // 在第2段后插入图片
                    const img = document.createElement('img');
                    img.src = base64Url;
                    img.style.maxWidth = '100%';
                    img.style.height = 'auto';
                    img.style.display = 'block';
                    img.style.margin = '20px 0';
                    
                    // 在第2段后插入
                    if (paragraphs[1].nextSibling) {
                        editor.insertBefore(img, paragraphs[1].nextSibling);
                    } else {
                        editor.appendChild(img);
                    }
                    
                    // 触发input事件
                    editor.dispatchEvent(new Event('input', { bubbles: true }));
                    
                    return true;
                }
            """, base64_url)
            
            if result:
                print("✅ 图片已插入到编辑器")
                await asyncio.sleep(2)
                
                # 验证
                has_image = await page.evaluate("""
                    () => {
                        const editor = document.querySelector('div[contenteditable="true"]');
                        if (!editor) return false;
                        const imgs = editor.querySelectorAll('img');
                        return imgs.length > 0;
                    }
                """)
                
                if has_image:
                    print("✅ 编辑器中包含图片")
                else:
                    print("❌ 编辑器中没有图片")
                
                # 截图
                await page.screenshot(path='logs/insert_image_html_test.png', full_page=True)
                print("✅ 截图已保存: logs/insert_image_html_test.png")
            else:
                print("❌ 插入失败")
        else:
            print(f"⚠️  图片不存在: {test_image_path}")
        
        await browser.close()


if __name__ == "__main__":
    asyncio.run(test_insert_image_html())
