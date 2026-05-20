"""
测试新的文章数据抓取方法
"""
import asyncio
import sys
import json
from playwright.async_api import async_playwright

async def test_new_method():
    """测试新的抓取方法"""
    print("=" * 80)
    print("测试新的文章数据抓取方法")
    print("=" * 80)
    
    async with async_playwright() as p:
        # 使用CDP连接已运行的Edge浏览器
        print("\n[0] 使用CDP连接Edge浏览器...")
        try:
            browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
            context = browser.contexts[0]
            page = context.pages[0] if context.pages else await context.new_page()
            print("✅ CDP连接成功")
        except Exception as e:
            print(f"❌ CDP连接失败: {e}")
            print("请先启动Edge浏览器，并确保启用了远程调试端口9222")
            return
        
        try:
            # 访问头条文章列表
            print("\n[1] 访问头条文章列表...")
            await page.goto("https://mp.toutiao.com/profile_v4/graphic/articles", timeout=30000)
            await asyncio.sleep(8)
            
            # 截图
            await page.screenshot(path="logs/test_new_method.png", full_page=True)
            print("✅ 已截图: logs/test_new_method.png")
            
            # 获取页面标题
            title = await page.title()
            print(f"\n[2] 页面标题: {title}")
            
            # 尝试查找文章列表
            print("\n[3] 查找文章列表元素...")
            
            # 尝试多种选择器
            selectors = [
                '[class*="article"]',
                '[class*="content"]',
                'tbody tr',
                'div[class*="item"]',
                '[class*="semi-table"]',
            ]
            
            for selector in selectors:
                elements = await page.query_selector_all(selector)
                print(f"  选择器 '{selector}': 找到 {len(elements)} 个元素")
                
                if len(elements) > 2:
                    print(f"\n[4] 分析前3个元素...")
                    for i, elem in enumerate(elements[:3]):
                        try:
                            text = await elem.inner_text()
                            text = text.strip()
                            if len(text) > 0:
                                print(f"\n  元素 {i+1}:")
                                print(f"  文本长度: {len(text)}")
                                print(f"  前200字符: {text[:200]}")
                                
                                # 检查是否包含文章特征
                                if '展现' in text or '阅读' in text:
                                    print(f"  ✅ 包含文章特征（展现/阅读）")
                                    
                                    # 提取标题
                                    lines = text.split('\n')
                                    for line in lines:
                                        line = line.strip()
                                        if len(line) > 10 and '展现' not in line and '阅读' not in line and '点赞' not in line and '评论' not in line:
                                            print(f"  📝 标题: {line}")
                                            break
                                    
                                    # 提取数字
                                    import re
                                    numbers = re.findall(r'\d+', text)
                                    if len(numbers) >= 4:
                                        print(f"  📊 数据: 展现={numbers[0]}, 阅读={numbers[1]}, 点赞={numbers[2]}, 评论={numbers[3]}")
                        except Exception as e:
                            print(f"  元素 {i+1} 获取失败: {e}")
                    
                    break
            
            # 保存HTML用于分析
            print("\n[5] 保存页面HTML...")
            html = await page.content()
            with open("logs/test_new_method.html", "w", encoding="utf-8") as f:
                f.write(html)
            print(f"✅ HTML已保存，大小: {len(html)} 字符")
            
            print("\n" + "=" * 80)
            print("测试完成！")
            print("=" * 80)
            
        except Exception as e:
            print(f"\n❌ 错误: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await context.close()

if __name__ == "__main__":
    asyncio.run(test_new_method())
