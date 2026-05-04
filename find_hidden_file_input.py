"""
查找页面上所有的file input（包括隐藏的）
"""
import asyncio
from playwright.async_api import async_playwright
import os

async def find_all_file_inputs():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0] if context.pages else await context.new_page()
        
        if "publish" not in page.url:
            print("跳转到发布页面...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            await asyncio.sleep(3)
        
        print("=" * 80)
        print("查找所有file input")
        print("=" * 80)
        
        # 查找所有input元素
        print("\n【步骤1】查找所有input元素...")
        all_inputs = await page.evaluate("""
            () => {
                const inputs = [];
                const allInputs = document.querySelectorAll('input');
                
                for (const inp of allInputs) {
                    inputs.push({
                        type: inp.type,
                        id: inp.id,
                        className: typeof inp.className === 'string' ? inp.className : '',
                        name: inp.name,
                        accept: inp.accept,
                        visible: inp.offsetParent !== null,
                        disabled: inp.disabled,
                        style: inp.style.cssText.substring(0, 100)
                    });
                }
                
                return inputs;
            }
        """)
        
        print(f"   找到 {len(all_inputs)} 个input元素")
        
        # 筛选出file类型的
        file_inputs = [inp for inp in all_inputs if inp['type'] == 'file']
        print(f"\n   其中 {len(file_inputs)} 个是file类型:")
        
        for i, inp in enumerate(file_inputs):
            print(f"      [{i}] id='{inp['id']}', name='{inp['name']}'")
            print(f"          accept={inp['accept']}")
            print(f"          visible={inp['visible']}, disabled={inp['disabled']}")
            print(f"          class={inp['className'][:80]}")
        
        # 如果有file input，尝试使用它
        if file_inputs:
            print(f"\n【步骤2】尝试使用第一个file input...")
            
            test_image = os.path.abspath('logs/test_cover.jpg')
            if not os.path.exists(test_image):
                # 创建测试图片
                from PIL import Image
                img = Image.new('RGB', (800, 600), color='blue')
                img.save(test_image)
                print(f"   创建测试图片: {test_image}")
            
            try:
                # 使用Playwright的set_input_files
                await page.evaluate("""
                    () => {
                        const fileInput = document.querySelector('input[type="file"]');
                        if (fileInput) {
                            console.log('找到file input:', fileInput);
                            return true;
                        }
                        return false;
                    }
                """)
                
                # 直接使用locator设置文件
                first_file_input = page.locator('input[type="file"]').first
                
                print(f"   尝试上传文件: {test_image}")
                await first_file_input.set_input_files(test_image)
                print("   [OK] 文件已设置！")
                
                await asyncio.sleep(3)
                
                # 截图查看结果
                await page.screenshot(path='logs/after_set_file.png', full_page=True)
                print("   [OK] 截图已保存")
                
                # 检查是否有变化
                cover_changed = await page.evaluate("""
                    () => {
                        // 查找封面区域是否有图片
                        const imgs = document.querySelectorAll('img');
                        let found = false;
                        
                        for (const img of imgs) {
                            const rect = img.getBoundingClientRect();
                            if (rect.width > 50 && rect.height > 50 && rect.top > 400) {
                                if (img.src && !img.src.includes('data:')) {
                                    console.log('找到封面图:', img.src.substring(0, 100));
                                    found = true;
                                    break;
                                }
                            }
                        }
                        
                        return found;
                    }
                """)
                
                if cover_changed:
                    print("   [OK] 封面图已显示！")
                else:
                    print("   [FAIL] 封面图未显示")
                    print("   说明：头条可能需要额外的触发操作")
            
            except Exception as e:
                print(f"   [ERROR] {e}")
        else:
            print("\n   [FAIL] 页面上没有file input")
            print("   说明：头条完全使用了自定义上传机制")
        
        print("\n" + "=" * 80)
        print("测试完成！")
        print("=" * 80)
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(find_all_file_inputs())
