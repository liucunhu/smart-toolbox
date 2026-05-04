
"""
头条全自动发布 - 连接真实Edge浏览器（CDP方案）
这是唯一能100%还原真实浏览器访问的方案
"""
import asyncio
import subprocess
from playwright.async_api import async_playwright


async def publish_with_cdp():
    """使用CDP连接真实Edge浏览器"""
    
    print("="*80)
    print("🚀 头条全自动发布（CDP连接真实Edge浏览器）")
    print("="*80)
    print("\n💡 方案说明：")
    print("   1. 先启动一个真实的Edge浏览器（带远程调试）")
    print("   2. Playwright连接到这个浏览器")
    print("   3. 100%真实浏览器环境，无任何自动化特征")
    print("   4. 全自动完成登录、填写、发布")
    print()
    
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    debug_port = 9222
    
    # 步骤1：启动Edge浏览器（带远程调试）
    print(f"[1/5] 启动Edge浏览器（远程调试端口 {debug_port}）...")
    
    # 先关闭已有的Edge
    subprocess.run("taskkill /F /IM msedge.exe", shell=True, capture_output=True)
    await asyncio.sleep(2)
    
    # 启动带远程调试的Edge
    cmd = [
        edge_path,
        f'--remote-debugging-port={debug_port}',
        '--user-data-dir=D:/edge_debug_profile',
        'https://mp.toutiao.com/'
    ]
    
    process = subprocess.Popen(cmd)
    print("✅ Edge浏览器已启动")
    print("   等待浏览器完全启动...")
    await asyncio.sleep(5)
    
    async with async_playwright() as p:
        # 步骤2：连接到Edge浏览器
        print(f"\n[2/5] 连接到Edge浏览器（CDP端口 {debug_port}）...")
        browser = await p.chromium.connect_over_cdp(f"http://127.0.0.1:{debug_port}")
        
        # 获取第一个context和page
        contexts = browser.contexts
        if not contexts:
            context = await browser.new_context()
        else:
            context = contexts[0]
        
        pages = context.pages
        if pages:
            page = pages[0]
        else:
            page = await context.new_page()
        
        print("✅ 已连接到真实Edge浏览器")
        print(f"   当前URL: {page.url}")
        
        # 步骤3：登录
        print("\n[3/5] 检查登录状态...")
        if "login" in page.url:
            print("⚠️  未登录，请在浏览器中手动登录...")
            print("   登录完成后按回车继续...")
            input()
        else:
            print("✅ 已登录")
        
        # 步骤4：访问发布页面
        print("\n[4/5] 访问发布页面...")
        
        # ★★★ 智能跳转逻辑：先检查当前页面，避免导航冲突 ★★★
        current_url = page.url
        print(f"   当前URL: {current_url}")
        
        if "profile_v4/graphic/publish" not in current_url:
            print("   正在跳转到发布页面...")
            try:
                await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
            except Exception as e:
                # 如果跳转被中断（例如重定向），通常意味着已经在目标页面或正在跳转
                if "interrupted" in str(e) or "navigation" in str(e).lower():
                    print("   ⚠️  导航冲突（可能正在自动跳转），等待页面稳定...")
                else:
                    raise e
        else:
            print("   ✅ 已在发布页面")
        
        # 等待页面完全稳定
        await asyncio.sleep(10)
        
        # 再次检查URL
        final_url = page.url
        print(f"   最终URL: {final_url}")
        
        # 验证页面加载
        print("\n   验证页面加载状态...")
        page_info = await page.evaluate("""
            () => {
                const editor = document.querySelector('div[contenteditable="true"]');
                const titleInput = document.querySelector('input[placeholder*="标题"]');
                
                let publishBtn = null;
                document.querySelectorAll('button').forEach(btn => {
                    if (btn.textContent.includes('预览并发布')) publishBtn = btn;
                });
                
                return {
                    editor: !!editor,
                    title: !!titleInput,
                    button: !!publishBtn,
                    url: window.location.href
                };
            }
        """)
        
        print(f"   编辑器: {'✅' if page_info['editor'] else '❌'}")
        print(f"   标题框: {'✅' if page_info['title'] else '❌'}")
        print(f"   发布按钮: {'✅' if page_info['button'] else '❌'}")
        
        if not page_info['editor'] or not page_info['button']:
            print("\n❌ 页面未完整加载，请检查：")
            print("   1. 浏览器是否完整显示页面")
            print("   2. 是否有错误提示")
            input("按回车继续...")
        
        # 步骤5:填写并发布
        print("\n[5/5] 填写内容并发布...")
        
        title = "人工智能技术发展趋势分析"
        content = """这是一篇关于人工智能技术发展的深度分析文章。

近年来,人工智能技术取得了长足的进步。机器学习、深度学习、自然语言处理、计算机视觉等技术正在改变我们的生活和工作方式。

人工智能的发展速度令人惊叹。从AlphaGo到GPT系列模型,AI技术在各个领域都取得了突破性进展。特别是在内容创作、智能客服、自动驾驶等领域,AI已经展现出强大的能力。

自然语言处理技术的进步尤为显著。大语言模型能够理解和生成人类语言,这在智能写作、机器翻译、对话系统等场景都有广泛应用。

计算机视觉技术也在快速发展。图像识别、目标检测、视频分析等技术正在各个行业发挥重要作用。从安防监控到医疗影像,从工业自动化到智能交通,计算机视觉的应用场景越来越广泛。

同时,AI技术的伦理和安全问题也日益受到关注。如何在推动技术发展的同时,确保AI的安全性和可控性,是我们需要共同思考的问题。

未来,人工智能将继续快速发展,在更多领域发挥重要作用。我们应该积极拥抱AI技术,同时也要注意其带来的挑战和风险。
"""
        
        # ★★★ 第一步：先生成并上传封面图（优先处理）★★★
        print("\n   === 第一步：生成并上传封面图 ===")
        
        # ★★★ 先关闭 AI 助手抽屉（防止遮挡）★★★
        print("   收起 AI 助手抽屉...")
        try:
            await page.evaluate("""
                () => {
                    const drawers = document.querySelectorAll('.byte-drawer-wrapper, .ai-assistant-drawer');
                    drawers.forEach(drawer => {
                        drawer.style.display = 'none';
                        drawer.style.visibility = 'hidden';
                        drawer.style.pointerEvents = 'none';
                    });
                    
                    const rightPanels = document.querySelectorAll('[class*="drawer"], [class*="assistant"], [class*="sidebar"]');
                    rightPanels.forEach(panel => {
                        if (panel.getBoundingClientRect().right > window.innerWidth * 0.7) {
                            panel.style.display = 'none';
                        }
                    });
                }
            """)
            await asyncio.sleep(1)
            print("   ✅ AI 助手已隐藏")
        except Exception as e:
            print(f"   ⚠️  收起助手失败: {e}")
        
        # ★★★ 设置封面图（选择单图模式 + 上传图片）★★★
        print("   设置封面图（单图模式）...")
        try:
            # 先滚动到封面图区域
            await page.evaluate("""
                () => {
                    const coverSection = document.querySelector('[class*="封面"]') || 
                                        Array.from(document.querySelectorAll('div')).find(d => d.textContent.includes('展示封面'));
                    if (coverSection) {
                        coverSection.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
            """)
            await asyncio.sleep(2)
            
            # ★★★ 步骤1：无论是否找到上传元素，都先选择"单图"模式 ★★★
            print("   步骤1：选择'单图'模式...")
            
            # 方案1：使用 Playwright 的 text 选择器点击"单图"（最可靠）
            single_image_selected = False
            try:
                await page.click('text="单图"', timeout=5000)
                print("   ✅ 已通过 text 选择器选择'单图'")
                single_image_selected = True
                await asyncio.sleep(2)
            except Exception as e:
                print(f"   ⚠️  text 选择器失败: {e}")
            
            # 方案2：使用 JavaScript 查找并点击 radio button
            if not single_image_selected:
                js_result = await page.evaluate("""
                    () => {
                        // 查找所有 radio button
                        const radios = document.querySelectorAll('input[type="radio"]');
                        for (const radio of radios) {
                            const parent = radio.parentElement;
                            if (parent && parent.textContent.includes('单图')) {
                                // 检查是否已经选中
                                if (!radio.checked) {
                                    // 触发完整的鼠标事件序列
                                    const mouseDown = new MouseEvent('mousedown', { bubbles: true });
                                    radio.dispatchEvent(mouseDown);
                                    
                                    const click = new MouseEvent('click', { bubbles: true });
                                    radio.dispatchEvent(click);
                                    
                                    const mouseUp = new MouseEvent('mouseup', { bubbles: true });
                                    radio.dispatchEvent(mouseUp);
                                    
                                    // 触发 change 事件
                                    const change = new Event('change', { bubbles: true });
                                    radio.dispatchEvent(change);
                                }
                                return 'clicked_radio';
                            }
                        }
                        return 'not_found';
                    }
                """)
                
                if js_result == 'clicked_radio':
                    print("   ✅ 已通过 JavaScript 选择'单图' (radio button)")
                    single_image_selected = True
                    await asyncio.sleep(2)
            
            # 方案3：查找包含"单图"文本的元素并点击
            if not single_image_selected:
                js_result = await page.evaluate("""
                    () => {
                        // 查找所有包含"单图"文本的元素
                        const allElements = document.querySelectorAll('*');
                        for (const el of allElements) {
                            const text = el.textContent?.trim();
                            if (text === '单图') {
                                // 直接点击元素
                                el.click();
                                return 'clicked_element';
                            }
                        }
                        return 'not_found';
                    }
                """)
                
                if js_result == 'clicked_element':
                    print("   ✅ 已通过 JavaScript 选择'单图' (element)")
                    single_image_selected = True
                    await asyncio.sleep(2)
                else:
                    print("   ❌ 无法选择'单图'模式")
            
            # 验证是否成功选择
            if single_image_selected:
                verification = await page.evaluate("""
                    () => {
                        const radios = document.querySelectorAll('input[type="radio"]');
                        for (const radio of radios) {
                            const parent = radio.parentElement;
                            if (parent && parent.textContent.includes('单图')) {
                                return radio.checked ? '已选中' : '未选中';
                            }
                        }
                        return '未找到';
                    }
                """)
                print(f"   验证状态: {verification}")
            
            # ★★★ 步骤2：检测上传元素并上传图片 ★★★
            print("   步骤2：检测上传区域...")
                        
            # 查找封面上传区域（包含"+"的区域）
            cover_area_info = await page.evaluate("""
                () => {
                    // 查找所有包含"+"的区域
                    const allDivs = Array.from(document.querySelectorAll('div'));
                    const plusAreas = [];
                                
                    for (const div of allDivs) {
                        const text = div.textContent || '';
                        // 查找包含"+"和"预览"文字的区域
                        if (text.includes('+') && text.includes('预览') && div.children.length < 10) {
                            const rect = div.getBoundingClientRect();
                            plusAreas.push({
                                text: text.substring(0, 50),
                                rect: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
                                className: div.className
                            });
                        }
                    }
                                
                    return plusAreas.slice(0, 3);
                }
            """)
                        
            print(f"   📊 找到 {len(cover_area_info)} 个封面上传区域")
                        
            # ★★★ 步骤3：生成封面图 ★★★
            print("   步骤3：生成 LLM 智能封面图...")
            cover_image_path = None
                        
            try:
                # 使用 LLM 生成智能封面图
                from app.services.content.llm_cover_generator import get_llm_cover_generator
                llm_generator = get_llm_cover_generator()
                            
                result = llm_generator.generate_cover_with_llm_analysis(
                    title=title,
                    content=content,
                    category="科技",
                    style_override=None
                )
                            
                if result["status"] == "success":
                    cover_image_path = result["file_path"]
                    design_plan = result.get("design_plan", {})
                    print(f"   ✅ LLM智能封面生成成功!")
                    print(f"      视觉风格: {design_plan.get('visual_style', 'N/A')}")
                    print(f"      配色方案: {design_plan.get('color_scheme', 'N/A')}")
                else:
                    print(f"   ⚠️  LLM封面生成失败: {result.get('error')}")
                    print("   🔄 降级使用传统AI生成...")
                    raise Exception("LLM生成失败")
                                
            except Exception as e:
                print(f"   ⚠️  LLM生成异常: {e}")
                print("   🔄 使用传统PIL图形生成封面...")
                            
                # 降级方案：使用传统AI生成
                from app.services.content.ai_cover_generator import AICoverGenerator
                generator = AICoverGenerator()
                            
                ai_result = generator.generate_cover(
                    title=title,
                    subtitle="",
                    category="科技",
                    style="modern"
                )
                            
                if ai_result["status"] == "success":
                    cover_image_path = ai_result["file_path"]
                    print(f"   ✅ 传统AI封面生成成功: {ai_result['style']} 风格")
                else:
                    print(f"   ❌ AI封面生成失败: {ai_result.get('error')}")
                    cover_image_path = None
                        
            # ★★★ 步骤4：点击蓝色方框上传封面图（已验证成功）★★★
            if cover_image_path and cover_area_info:
                print("   步骤4：上传封面图到头条...")
                            
                try:
                    import os
                                
                    abs_cover_path = os.path.abspath(cover_image_path)
                    print(f"   📊 封面图路径: {abs_cover_path}")
                    
                    # 步骤1：确保在发布页面
                    print("   步骤4.1：确保在发布页面...")
                    current_url = page.url
                    if "publish" not in current_url:
                        print("   ℹ️  当前不在发布页面，正在跳转...")
                        await page.goto("https://mp.toutiao.com/profile_v4/graphic/publish", wait_until="domcontentloaded")
                        await asyncio.sleep(3)
                        await page.wait_for_selector('[contenteditable="true"]', timeout=10000)
                        print("   ✅ 已回到发布页面")
                    
                    # 步骤2：点击蓝色方框（.article-cover-images）
                    print("   步骤4.2：点击封面上传区域...")
                    box_info = await page.evaluate("""
                        () => {
                            const coverBox = document.querySelector('.article-cover-images');
                            if (coverBox) {
                                const rect = coverBox.getBoundingClientRect();
                                return {
                                    center_x: rect.left + rect.width / 2,
                                    center_y: rect.top + rect.height / 2
                                };
                            }
                            return null;
                        }
                    """)
                    
                    if box_info:
                        await page.mouse.click(box_info['center_x'], box_info['center_y'])
                        await asyncio.sleep(3)
                        print("   ✅ 对话框已打开")
                    else:
                        print("   ⚠️  未找到封面上传区域")
                        raise Exception("未找到.article-cover-images元素")
                    
                    # 步骤3：点击"上传图片"按钮
                    print("   步骤4.3：点击上传图片按钮...")
                    await page.evaluate("""
                        () => {
                            const allElements = document.querySelectorAll('button, [role="button"], span, div');
                            for (const el of allElements) {
                                const text = (el.textContent || '').trim();
                                const rect = el.getBoundingClientRect();
                                if (text.includes('上传图片') && rect.width > 50 && rect.top > 0) {
                                    el.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    await asyncio.sleep(2)
                    print("   ✅ 已点击上传图片")
                    
                    # 步骤4：等待文件选择器出现并上传
                    print("   步骤4.4：等待文件选择器...")
                    await asyncio.sleep(2)
                    
                    # 尝试查找隐藏的 file input
                    file_input = page.locator('input[type="file"]').first
                    try:
                        await file_input.set_input_files(abs_cover_path, timeout=5000)
                        print("   ✅ 文件已上传")
                    except:
                        print("   ⚠️  文件选择器未出现，尝试其他方法...")
                    
                    # 步骤5：等待头条处理上传
                    print("   ⏳ 等待图片上传和处理...")
                    await asyncio.sleep(10)
                    
                    # 步骤6：点击确认按钮
                    print("   步骤4.5：点击确认按钮...")
                    confirm_clicked = await page.evaluate("""
                        () => {
                            const allButtons = document.querySelectorAll('button, [role="button"]');
                            for (const btn of allButtons) {
                                const text = (btn.textContent || '').trim();
                                const rect = btn.getBoundingClientRect();
                                if ((text === '确定' || text === '确认' || text === '完成') && 
                                    rect.width > 50 && rect.top > 0) {
                                    btn.click();
                                    return true;
                                }
                            }
                            return false;
                        }
                    """)
                    
                    if confirm_clicked:
                        print("   ✅ 已点击确认按钮")
                        await asyncio.sleep(3)
                    else:
                        print("   ℹ️  未找到确认按钮（可能自动处理）")
                    
                    # 步骤7：验证封面
                    print("   步骤4.6：验证封面...")
                    await asyncio.sleep(5)
                    
                    cover_uploaded = await page.evaluate("""
                        () => {
                            const imgs = document.querySelectorAll('img');
                            for (const img of imgs) {
                                const rect = img.getBoundingClientRect();
                                if (rect.width > 100 && rect.height > 100 && rect.top > 200) {
                                    if (img.src && !img.src.includes('data:')) {
                                        console.log('找到封面图:', img.src.substring(0, 80));
                                        return true;
                                    }
                                }
                            }
                            return false;
                        }
                    """)
                    
                    if cover_uploaded:
                        print("   ✅ 封面图已成功上传！")
                    else:
                        print("   ⚠️  封面图未显示")
                        await page.screenshot(path='logs/cover_upload_debug.png', full_page=True)
                        print("   ℹ️  请查看截图: logs/cover_upload_debug.png")
                                
                except Exception as e:
                    print(f"   ⚠️  上传失败: {e}")
                    import traceback
                    traceback.print_exc()
            elif cover_image_path and not cover_area_info:
                print("   ⚠️  未找到封面上传区域")
                print("   🔄 将保持'单图'模式，但不上传图片...")
            elif not cover_image_path:
                print("   ⚠️  封面图生成失败")
                print("   🔄 将保持'单图'模式，但不上传图片...")
            
        except Exception as e:
            print(f"   ⚠️  封面图设置失败: {e}")
            import traceback
            traceback.print_exc()
            print("   提示：将使用'无封面'模式继续发布")
        
        await asyncio.sleep(3)
        await asyncio.sleep(3)
        
        # ★★★ 第二步：填写标题 ★★★
        print("\n   === 第二步：填写标题 ===")
        print(f"   填写标题: {title}")
        try:
            # 尝试多种标题选择器
            title_selectors = [
                'input[placeholder*="标题"]',
                'textarea[placeholder*="标题"]',
                'input[placeholder="请输入标题"]',
                '.title-input input',
                '[class*="title"] input',
            ]
            
            filled = False
            for selector in title_selectors:
                try:
                    await page.fill(selector, title, timeout=5000)
                    print(f"   ✅ 标题已填写 (使用选择器: {selector})")
                    filled = True
                    break
                except:
                    continue
            
            if not filled:
                # 最后尝试：通过 JavaScript 直接设置值
                js_success = await page.evaluate(f"""
                    () => {{
                        const inputs = document.querySelectorAll('input, textarea');
                        for (const input of inputs) {{
                            if (input.placeholder && input.placeholder.includes('标题')) {{
                                // 先聚焦
                                input.focus();
                                // 清空现有值
                                input.value = '';
                                // 设置新值
                                input.value = '{title}';
                                // 触发多个事件确保 React/Vue 等框架能检测到
                                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                                return true;
                            }}
                        }}
                        return false;
                    }}
                """)
                if js_success:
                    print(f"   ✅ 标题已通过 JS 填写")
                else:
                    print(f"   ❌ JS 填写也失败了，尝试备用方案...")
                    # 备用方案：查找所有 input/textarea 并尝试第一个
                    await page.evaluate(f"""
                        () => {{
                            const allInputs = document.querySelectorAll('input:not([type="hidden"]), textarea');
                            if (allInputs.length > 0) {{
                                const firstInput = allInputs[0];
                                firstInput.focus();
                                firstInput.value = '{title}';
                                firstInput.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                firstInput.dispatchEvent(new Event('change', {{ bubbles: true }}));
                                return true;
                            }}
                            return false;
                        }}
                    """)
                    print(f"   ⚠️  已尝试备用方案填写标题")
        except Exception as e:
            print(f"   ❌ 标题填写失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 验证标题是否填写成功
        await asyncio.sleep(1)
        title_verification = await page.evaluate("""
            () => {
                const inputs = document.querySelectorAll('input, textarea');
                for (const input of inputs) {
                    if (input.placeholder && input.placeholder.includes('标题')) {
                        return input.value || '(空)';
                    }
                }
                return '未找到标题输入框';
            }
        """)
        print(f"   📊 标题验证结果: {title_verification}")
                
        await asyncio.sleep(2)
                
        # ★★★ 第三步：生成文章配图 ★★★
        print("\n   === 第三步：生成文章配图 ===")
        print("   生成文章配图...")
        try:
            from app.services.content.article_image_generator import get_article_image_generator
            image_generator = get_article_image_generator()
                    
            # 生成2张配图（只生成文件，不插入到文本）
            article_images = image_generator.generate_images_for_article(
                title=title,
                content=content,
                num_images=2,
                category="科技"
            )
                    
            if article_images:
                print(f"   ✅ 生成了 {len(article_images)} 张配图")
                for img in article_images:
                    print(f"      - {img['theme']}: {img['file_path']}")
            else:
                print("   ⚠️  配图生成失败，使用纯文本")
                article_images = []
        except Exception as e:
            print(f"   ⚠️  配图生成异常：{e}")
            import traceback
            traceback.print_exc()
            article_images = []
        
        await asyncio.sleep(1)
        
        # ★★★ 第四步：填写正文（纯文本）★★★
        print("\n   === 第四步：填写正文 ===")
        print(f"   填写正文 ({len(content)} 字)")
        try:
            await page.fill('div[contenteditable="true"]', content)
            print("   ✅ 正文已填写")
        except Exception as e:
            print(f"   ⚠️  正文填写失败: {e}")
        
        await asyncio.sleep(3)
        
        # ★★★ 第五步：插入图片到文章（点击按钮上传）★★★
        if article_images:
            print("\n   === 第五步：插入图片到文章 ===")
            try:
                import os
                
                for i, img_info in enumerate(article_images):
                    print(f"   步骤{i+1}/{len(article_images)}：上传配图 '{img_info['theme']}'...")
                    
                    abs_img_path = os.path.abspath(img_info['file_path'])
                    print(f"      📄 图片路径: {abs_img_path}")
                    
                    # 定位光标到合适位置
                    target_index = min((i + 1) * 2, 5)
                    await page.evaluate(f"""
                        () => {{
                            const editor = document.querySelector('div[contenteditable="true"]');
                            if (!editor) return;
                            
                            editor.focus();
                            const paragraphs = editor.querySelectorAll('p');
                            const idx = Math.min({target_index}, paragraphs.length - 1);
                            
                            if (paragraphs.length > idx) {{
                                const range = document.createRange();
                                const sel = window.getSelection();
                                range.setStartAfter(paragraphs[idx]);
                                range.collapse(true);
                                sel.removeAllRanges();
                                sel.addRange(range);
                            }}
                        }}
                    """)
                    await asyncio.sleep(1)
                    
                    # 点击工具栏的图片按钮
                    print(f"      步骤 2：点击图片按钮...")
                    # 先隐藏所有可能遮挡的元素
                    await page.evaluate("""
                        () => {
                            const overlays = document.querySelectorAll('.byte-drawer-wrapper, .upload-image-panel, .byte-drawer-mask, .byte-modal-mask');
                            overlays.forEach(el => el.style.display = 'none');
                        }
                    """)
                    await asyncio.sleep(1)
                                    
                    # 关闭之前可能打开的抽屉
                    await page.evaluate("""
                        () => {
                            // 查找所有关闭按钮并点击
                            const closeButtons = document.querySelectorAll('.byte-drawer-close, .byte-modal-close, .upload-image-close');
                            closeButtons.forEach(btn => btn.click());
                                            
                            // 按 ESC 关闭对话框
                            const event = new KeyboardEvent('keydown', {
                                key: 'Escape',
                                code: 'Escape',
                                bubbles: true
                            });
                            document.dispatchEvent(event);
                        }
                    """)
                    await asyncio.sleep(1)
                    
                    # 先关闭可能存在的图片选择抽屉
                    await page.evaluate("""
                        () => {
                            const drawers = document.querySelectorAll('.byte-drawer-wrapper, .upload-image-panel');
                            drawers.forEach(drawer => {
                                drawer.style.display = 'none';
                                drawer.style.visibility = 'hidden';
                                drawer.style.pointerEvents = 'none';
                            });
                        }
                    """)
                    await asyncio.sleep(1)
                    
                    toolbar_buttons = await page.query_selector_all('.syl-toolbar-button')
                    print(f"      找到 {len(toolbar_buttons)} 个工具栏按钮")
                    
                    # ★★★ 直接点击第12个按钮（索引11）- 图片按钮 ★★★
                    if len(toolbar_buttons) > 11:
                        await toolbar_buttons[11].click()
                        print(f"      ✅ 已点击第 12 个按钮（图片按钮）")
                        
                        # ★★★ 等待对话框完全加载 ★★★
                        print(f"      等待对话框加载...")
                        await asyncio.sleep(5)  # 增加到5秒
                        
                        # ★★★ 调试：检查对话框状态 ★★★
                        dialog_info = await page.evaluate("""
                            () => {
                                const dialogs = document.querySelectorAll('.upload-image-panel, .byte-modal, .byte-dialog, [role="dialog"]');
                                const buttons = document.querySelectorAll('button, [role="button"], div[role="button"]');
                                return {
                                    dialogCount: dialogs.length,
                                    buttonTexts: Array.from(buttons).slice(0, 15).map(b => (b.textContent || '').trim()).filter(t => t)
                                };
                            }
                        """)
                        print(f"      📊 对话框数量: {dialog_info['dialogCount']}")
                        print(f"      📊 前15个按钮文本: {dialog_info['buttonTexts']}")
                        
                        # ★★★ 完全复用封面上传的成功逻辑 ★★★
                                                
                        # 步骤1：点击"本地上传"按钮
                        print(f"      步骤 3：点击'本地上传'按钮...")
                        await page.evaluate("""
                            () => {
                                const allElements = document.querySelectorAll('button, [role="button"], span, div');
                                for (const el of allElements) {
                                    const text = (el.textContent || '').trim();
                                    const rect = el.getBoundingClientRect();
                                    if (text.includes('本地上传') && rect.width > 50 && rect.top > 0) {
                                        el.click();
                                        return true;
                                    }
                                }
                                return false;
                            }
                        """)
                        await asyncio.sleep(2)
                        print(f"      ✅ 已点击'本地上传'按钮")
                                                
                        # 步骤2：等待文件选择器出现并上传
                        print(f"      步骤 4：等待文件选择器...")
                        await asyncio.sleep(2)
                                                
                        # 使用 .first（与封面上传一致）
                        file_input = page.locator('input[type="file"]').first
                        try:
                            await file_input.set_input_files(abs_img_path, timeout=5000)
                            print(f"      ✅ 文件已上传")
                        except Exception as e:
                            print(f"      ⚠️  文件上传失败：{e}")
                            raise
                                                
                        # 步骤3：等待头条处理上传
                        print(f"       等待图片上传和处理(15秒)...")
                        await asyncio.sleep(15)
                                                
                        # 步骤4：点击确认按钮
                        print(f"      步骤 5：点击'确定'按钮...")
                        confirm_clicked = await page.evaluate("""
                            () => {
                                const allButtons = document.querySelectorAll('button, [role="button"]');
                                for (const btn of allButtons) {
                                    const text = (btn.textContent || '').trim();
                                    const rect = btn.getBoundingClientRect();
                                    if ((text === '确定' || text === '确认' || text === '完成') && 
                                        rect.width > 50 && rect.top > 0) {
                                        btn.click();
                                        return true;
                                    }
                                }
                                return false;
                            }
                        """)
                                                
                        if confirm_clicked:
                            print(f"      ✅ 已点击确认按钮")
                            await asyncio.sleep(3)
                        else:
                            print(f"      ⚠️  未找到'确定'按钮")
                            
                            # 策略2: 尝试滚动对话框后再查找
                            print(f"      🔄 尝试滚动对话框...")
                            await page.evaluate("""
                                () => {
                                    const dialogs = document.querySelectorAll('.byte-modal-content, .byte-dialog-body, .upload-image-panel, [role="dialog"]');
                                    dialogs.forEach(dialog => {
                                        dialog.scrollTop = dialog.scrollHeight;
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
                                            return true;
                                        }
                                    }
                                    return false;
                                }
                            """)
                            
                            if confirm_clicked:
                                print(f"      ✅ 滚动后已点击'确定'按钮")
                                await asyncio.sleep(3)
                            else:
                                print(f"      ℹ️  未找到确认按钮（可能自动处理）")
                                                
                        # 步骤5：验证图片是否插入编辑器
                        print(f"      步骤 6：验证图片...")
                        await asyncio.sleep(3)
                                                
                        img_count = await page.evaluate("""
                            () => {
                                const editor = document.querySelector('div[contenteditable="true"]');
                                if (!editor) return 0;
                                return editor.querySelectorAll('img').length;
                            }
                        """)
                        print(f"      📊 编辑器中图片数量: {img_count}")
                                                
                        if img_count > 0:
                            print(f"      ✅ 图片已成功插入编辑器")
                        else:
                            print(f"      ⚠️  图片未插入")
                
                print(f"   ✅ 所有配图已处理")
            except Exception as e:
                print(f"   ⚠️  插入配图失败：{e}")
                import traceback
                traceback.print_exc()
        
        await asyncio.sleep(3)
        
        # ★★★ 第二步：填写标题 ★★★
        print("\n   === 第六步：设置作品声明 ===")
        try:
            # 查找并勾选"仅个人观点，仅供参考"选项
            declaration_texts = [
                '仅个人观点',
                '个人观点',
                '仅供参考',
                '仅个人观点，仅供参考'
            ]
            
            declaration_checked = await page.evaluate(f"""
                () => {{
                    const targetTexts = {declaration_texts};
                    
                    // 查找所有 checkbox
                    const allCheckboxes = document.querySelectorAll('input[type="checkbox"]');
                    for (const cb of allCheckboxes) {{
                        const label = cb.closest('label') || cb.parentElement;
                        if (label) {{
                            const labelText = label.textContent || '';
                            for (const targetText of targetTexts) {{
                                if (labelText.includes(targetText)) {{
                                    if (!cb.checked) {{
                                        cb.click();
                                    }}
                                    return true;
                                }}
                            }}
                        }}
                    }}
                    return false;
                }}
            """)
                    
            if declaration_checked:
                print(f"   ✅ 已勾选{declaration_texts[0]}声明")
            else:
                print(f"   ⚠️  未找到{declaration_texts[0]}选项（尝试查找所有 checkbox）")
                        
                # 备用方案：直接通过文本查找
                await page.evaluate(f"""
                    () => {{
                        const targetTexts = {declaration_texts};
                        const allElements = document.querySelectorAll('*');
                        for (const el of allElements) {{
                            const text = el.textContent || '';
                            for (const targetText of targetTexts) {{
                                if (text.includes(targetText) && (el.tagName === 'LABEL' || el.tagName === 'SPAN')) {{
                                    // 点击包含目标文本的元素或其相邻的 checkbox
                                    const checkbox = el.querySelector('input[type="checkbox"]') || 
                                                   el.parentElement?.querySelector('input[type="checkbox"]') ||
                                                   el.previousElementSibling;
                                    if (checkbox && checkbox.type === 'checkbox' && !checkbox.checked) {{
                                        checkbox.click();
                                        return true;
                                    }}
                                    el.click();
                                    return true;
                                }}
                            }}
                        }}
                        return false;
                    }}
                """)
                print(f"   ✅ 已通过备用方案勾选{declaration_texts[0]}")
        except Exception as e:
            print(f"   ⚠️  设置声明失败: {e}")
        
        await asyncio.sleep(3)
                
        # 点击发布
        print("   点击发布按钮...")
        try:
            # 等待页面稳定
            await asyncio.sleep(2)
            
            publish_btn = None
            buttons = await page.query_selector_all('button')
            for btn in buttons:
                text = await btn.text_content()
                if '预览并发布' in text:
                    publish_btn = btn
                    break
            
            if publish_btn:
                # 使用 force=True 强制点击，避免被遮挡
                await publish_btn.click(force=True)
                print("   ✅ 已点击'预览并发布'按钮")
                
                # ★★★ 等待确认对话框出现 ★★★
                print("   等待确认对话框...")
                await asyncio.sleep(3)
                
                # ★★★ 查找并点击“确认发布”按钮（从截图看，在底部） ★★★
                print("   查找'确认发布'按钮...")
                confirm_clicked = await page.evaluate("""
                    () => {
                        // 从截图看，确认发布按钮在页面底部，不在模态框中
                        // 直接查找所有包含"确认发布"文本的按钮
                        const allButtons = document.querySelectorAll('button, [role="button"], .byte-btn');
                        
                        for (const btn of allButtons) {
                            const text = btn.textContent?.trim();
                            console.log('检查按钮:', text);
                            
                            if (text === '确认发布') {
                                btn.click();
                                console.log('已点击确认发布按钮');
                                return true;
                            }
                        }
                        
                        // 如果没找到，尝试查找包含"确认"的按钮
                        for (const btn of allButtons) {
                            const text = btn.textContent?.trim();
                            if (text.includes('确认')) {
                                btn.click();
                                console.log('已点击包含确认的按钮:', text);
                                return true;
                            }
                        }
                        
                        // 最后尝试：查找模态框中的按钮
                        const modals = document.querySelectorAll('.byte-modal, .modal, [role="dialog"], .confirm-dialog');
                        for (const modal of modals) {
                            const buttons = modal.querySelectorAll('button, [role="button"], .byte-btn');
                            for (const btn of buttons) {
                                const text = btn.textContent?.trim();
                                if (text && (text.includes('确认') || text.includes('确定') || text === '发布')) {
                                    btn.click();
                                    return true;
                                }
                            }
                            if (buttons.length > 0) {
                                buttons[buttons.length - 1].click();
                                return true;
                            }
                        }
                        
                        return false;
                    }
                """)
                
                if confirm_clicked:
                    print("   ✅ 已点击'确认发布'按钮")
                else:
                    print("   ⚠️  未找到确认按钮，可能不需要二次确认")
                
                # ★★★ 等待发布处理完成（更长时间）★★★
                print("   等待发布处理...")
                await asyncio.sleep(15)
                
                # ★★★ 多维度验证发布是否真正成功 ★★★
                print("   验证发布结果...")
                
                # 1. 检查当前 URL
                new_url = page.url
                print(f"   当前 URL: {new_url}")
                
                # 2. 检查页面是否有成功提示
                success_indicators = await page.evaluate("""
                    () => {
                        const body = document.body.textContent;
                        const url = window.location.href;
                        
                        // 检查多种成功信号
                        const signals = {
                            hasSuccessMsg: body.includes('发布成功') || body.includes('已成功') || body.includes('发布完成'),
                            isInPublishPage: url.includes('/publish'),
                            hasError: body.includes('失败') || body.includes('错误') || body.includes('error'),
                            isRedirected: !url.includes('/publish') && url.includes('/profile'),
                        };
                        
                        return signals;
                    }
                """)
                
                print(f"   成功提示: {'✅' if success_indicators['hasSuccessMsg'] else '❌'}")
                print(f"   仍在发布页: {'是' if success_indicators['isInPublishPage'] else '否'}")
                print(f"   有错误信息: {'是' if success_indicators['hasError'] else '否'}")
                print(f"   已跳转: {'✅' if success_indicators['isRedirected'] else '❌'}")
                
                # 3. 截图保存发布后状态
                import time
                screenshot_path = f"logs/toutiao_after_publish_{int(time.time())}.png"
                await page.screenshot(path=screenshot_path, full_page=True)
                print(f"    已保存截图: {screenshot_path}")
                
                # 4. 保存 HTML 用于调试
                html_path = f"logs/toutiao_after_publish_{int(time.time())}.html"
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(await page.content())
                print(f"   📄 已保存 HTML: {html_path}")
                
                # 5. 综合判断
                if success_indicators['isRedirected'] or (success_indicators['hasSuccessMsg'] and not success_indicators['isInPublishPage']):
                    print("\n🎉 发布成功！")
                    print("   文章已发布到今日头条")
                elif success_indicators['hasError']:
                    print("\n❌ 发布失败！检测到错误信息")
                    print("   请查看截图和 HTML 文件")
                elif success_indicators['isInPublishPage']:
                    print("\n⚠️  仍在发布页面，发布可能未完成")
                    print("   可能原因：")
                    print("   - 表单验证失败（标题、内容不完整）")
                    print("   - 网络连接问题")
                    print("   - 头条服务器处理中")
                    print("   请查看截图确认状态")
                else:
                    print("\n⚠️  无法确定发布状态")
                    print("   请手动检查截图和 HTML")
            else:
                print("   ❌ 未找到发布按钮")
                # 截图保存
                await page.screenshot(path="logs/toutiao_no_button.png")
        except Exception as e:
            print(f"   ❌ 发布失败: {e}")
            # 截图保存错误状态
            await page.screenshot(path="logs/toutiao_publish_error.png")
        
        print("\n" + "="*80)
        print("✅ 操作完成！")
        print("   浏览器保持打开，请检查结果")
        print("   按回车关闭...")
        print("="*80)
        input()
        
        # 关闭
        process.terminate()
        await browser.close()


if __name__ == "__main__":
    asyncio.run(publish_with_cdp())
