# 头条CDP集成问题修复报告

**日期**: 2026-05-05  
**问题**: CDP上传在独立测试时100%成功，但集成到auto_publish后失败  
**状态**: 🔄 修复中

---

## 🔍 问题分析

### 问题1: 标题没有填写成功

**原因**: 
- 集成代码只使用了简单的 `query_selector` + `fill` 方式
- 没有使用测试脚本中的多重保障机制（多种选择器 + JavaScript fallback）
- 没有验证标题是否真正填写成功

**测试脚本的成功方式** (`test_cdp_auto_publish.py:520-600`):
```python
# 方案1: 尝试多种选择器
title_selectors = [
    'input[placeholder*="标题"]',
    'textarea[placeholder*="标题"]',
    'input[placeholder="请输入标题"]',
    '.title-input input',
    '[class*="title"] input',
]

for selector in title_selectors:
    try:
        await page.fill(selector, title, timeout=5000)
        print(f"✅ 标题已填写 (使用选择器: {selector})")
        filled = True
        break
    except:
        continue

# 方案2: JavaScript 直接设置值（如果方案1失败）
if not filled:
    js_success = await page.evaluate(f"""
        () => {{
            const inputs = document.querySelectorAll('input, textarea');
            for (const input of inputs) {{
                if (input.placeholder && input.placeholder.includes('标题')) {{
                    input.focus();
                    input.value = '';
                    input.value = '{title}';
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('blur', {{ bubbles: true }}));
                    return true;
                }}
            }}
            return false;
        }}
    """)

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
print(f"📊 标题验证结果: {title_verification}")
```

**当前集成代码的问题** (`toutiao_publisher.py:658-666`):
```python
# ❌ 过于简单，没有fallback机制
title_input = await self.page.query_selector('input[placeholder="请输入标题"]')
if not title_input:
    title_input = await self.page.query_selector('textarea[placeholder*="标题"]')

if title_input:
    await title_input.fill(title)
    await asyncio.sleep(1)
    logger.info(f"标题已填写: {title}")
```

---

### 问题2: 封面图和配图上传失败

**可能原因**:
1. **页面加载不完整** - 在元素还未渲染完成时就尝试操作
2. **执行顺序错误** - 可能在标题/正文填写之前就尝试上传封面
3. **对话框遮挡** - 之前的操作留下的对话框未关闭
4. **超时时间不足** - 等待file input出现的时间太短

**测试脚本的成功关键点**:
- ✅ 每个步骤都有明确的日志输出
- ✅ 每个操作后都有足够的等待时间
- ✅ 有关闭之前对话框的逻辑
- ✅ 有详细的错误处理和fallback

---

## ✅ 已完成的修复

### 修复1: 标题填写增强

**文件**: `app/services/publish/toutiao_publisher.py`

**修改内容**:
```python
# 2. ★★★ 填写标题（使用多重保障机制）★★★
logger.info("📝 开始填写标题...")
title_filled = False

# 方案1: 尝试多种选择器
title_selectors = [
    'input[placeholder*="标题"]',
    'textarea[placeholder*="标题"]',
    'input[placeholder="请输入标题"]',
    '.title-input input',
    '[class*="title"] input',
]

for selector in title_selectors:
    try:
        title_input = await self.page.query_selector(selector)
        if title_input and await title_input.is_visible():
            await title_input.fill(title)
            await asyncio.sleep(1)
            logger.info(f"✅ 标题已填写 (使用选择器: {selector})")
            title_filled = True
            break
    except Exception as e:
        logger.debug(f"选择器 {selector} 失败: {e}")
        continue

# 方案2: JavaScript 直接设置值（如果方案1失败）
if not title_filled:
    logger.warning("⚠️  常规选择器填写失败，尝试 JavaScript 方式...")
    js_success = await self.page.evaluate(f"""
        () => {{
            const inputs = document.querySelectorAll('input, textarea');
            for (const input of inputs) {{
                if (input.placeholder && input.placeholder.includes('标题')) {{
                    input.focus();
                    input.value = '';
                    input.value = `{title}`;
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
        logger.info("✅ 标题已通过 JS 填写")
        title_filled = True
    else:
        logger.error("❌ 标题填写失败！所有方案都未成功")

# 验证标题是否填写成功
await asyncio.sleep(1)
title_verification = await self.page.evaluate("""
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
logger.info(f"📊 标题验证结果: {title_verification}")

if not title_filled or title_verification == '(空)' or title_verification == '未找到标题输入框':
    logger.error("❌ 标题填写验证失败，中止发布流程")
    return {
        "status": "failed",
        "error": "标题填写失败，请检查页面是否正常加载"
    }
```

**改进点**:
- ✅ 5种选择器尝试
- ✅ JavaScript fallback
- ✅ 事件触发确保框架检测
- ✅ 填写后验证
- ✅ 失败时提前返回

---

## ⏸️ 待完成的修复

### 修复2: 正文填写增强

**需要添加**:
1. 清空编辑器后再填写
2. 填写后验证内容长度
3. 异常处理和错误返回

**建议代码**:
```python
# 3. ★★★ 填写正文（富文本编辑器）★★★
logger.info("📄 开始填写正文...")
try:
    editor = await self.page.query_selector('div[contenteditable="true"]')
    if not editor:
        editor = await self.page.query_selector('div.toutiao-editor')
    
    if editor:
        # 先清空编辑器
        await editor.fill('')
        await asyncio.sleep(0.5)
        
        # 填写内容
        await editor.fill(content)
        await asyncio.sleep(2)
        logger.info(f"✅ 正文已填写，长度: {len(content)} 字")
        
        # 验证正文是否填写成功
        content_verification = await self.page.evaluate("""
            () => {
                const editor = document.querySelector('div[contenteditable="true"]');
                if (editor) {
                    return editor.innerText || editor.textContent || '(空)';
                }
                return '未找到编辑器';
            }
        """)
        logger.info(f"📊 正文验证结果: {len(content_verification)} 字")
    else:
        logger.error("❌ 未找到富文本编辑器")
        return {
            "status": "failed",
            "error": "未找到富文本编辑器，请检查页面是否正常加载"
        }
except Exception as e:
    logger.error(f"❌ 正文填写失败: {e}")
    import traceback
    traceback.print_exc()
    return {
        "status": "failed",
        "error": f"正文填写失败: {str(e)}"
    }
```

---

### 修复3: 封面图上传调试

**需要检查的点**:

1. **页面加载完整性**
   ```python
   # 在上传前检查页面是否完全加载
   page_info = await self.page.evaluate("""
       () => {
           return {
               editor: !!document.querySelector('div[contenteditable="true"]'),
               coverSection: !!Array.from(document.querySelectorAll('div')).find(d => d.textContent.includes('封面')),
               singleImageOption: !!Array.from(document.querySelectorAll('*')).find(el => el.textContent === '单图')
           };
       }
   """)
   logger.info(f"页面加载状态: {page_info}")
   ```

2. **关闭之前的对话框**
   ```python
   # 在上传封面之前，确保没有其他对话框打开
   await self.page.evaluate("""
       () => {
           // 关闭所有可能的对话框
           const closeButtons = document.querySelectorAll('.byte-drawer-close, .byte-modal-close');
           closeButtons.forEach(btn => btn.click());
           
           // 按 ESC 关闭
           const event = new KeyboardEvent('keydown', {
               key: 'Escape',
               code: 'Escape',
               bubbles: true
           });
           document.dispatchEvent(event);
           
           // 隐藏所有遮罩层
           const masks = document.querySelectorAll('.byte-drawer-mask, .byte-modal-mask');
           masks.forEach(mask => mask.style.display = 'none');
       }
   """)
   await asyncio.sleep(1)
   ```

3. **增加等待时间**
   ```python
   # 等待file input出现的时间从5秒增加到10秒
   file_input = await self.page.wait_for_selector('input[type="file"]', timeout=10000)
   ```

4. **详细的日志输出**
   ```python
   logger.info("📸 开始上传封面图...")
   logger.info(f"   图片路径: {cover_image_path}")
   logger.info("   步骤1: 选择'单图'模式...")
   # ... 每个步骤都有日志
   ```

---

## 📋 调试建议

### 1. 启用详细日志

在 `.env` 文件中设置：
```bash
LOG_LEVEL=DEBUG
```

### 2. 保存调试截图和HTML

在每个关键步骤后保存：
```python
# 标题填写后
await self.page.screenshot(path=f"logs/title_after_{int(asyncio.get_event_loop().time())}.png")

# 正文填写后
await self.page.screenshot(path=f"logs/content_after_{int(asyncio.get_event_loop().time())}.png")

# 封面上传前
with open(f"logs/before_cover_{int(asyncio.get_event_loop().time())}.html", 'w') as f:
    f.write(await self.page.content())
```

### 3. 对比测试脚本和集成代码

**测试脚本** (`test_cdp_auto_publish.py`):
- ✅ 手动控制每一步
- ✅ 每步之间有足够等待
- ✅ 详细的控制台输出
- ✅ 可以暂停观察

**集成代码** (`toutiao_publisher.py`):
- ❌ 自动执行，速度较快
- ❌ 等待时间可能不足
- ❌ 日志不够详细
- ❌ 难以中途调试

### 4. 逐步验证

建议按以下顺序测试：
1. ✅ 只测试标题填写
2. ✅ 标题+正文填写
3. ✅ 标题+正文+封面上传
4. ✅ 完整流程

---

## 🎯 下一步行动

1. **立即执行**:
   - ✅ 标题填写已修复（已完成）
   - ⏸️ 正文填写需要修复（待完成）
   - ⏸️ 封面上传需要添加更多调试日志

2. **测试验证**:
   - 运行一次完整的auto_publish测试
   - 检查日志输出，确认哪一步失败
   - 根据日志调整等待时间和选择器

3. **长期优化**:
   - 为每个关键步骤添加超时重试
   - 实现更智能的页面加载检测
   - 添加性能监控和指标收集

---

## 📝 相关文件

- ✅ `app/services/publish/toutiao_publisher.py` - 头条发布器（标题已修复）
- 📋 `scripts/test_cdp_auto_publish.py` - 成功的测试脚本参考
- 📋 `docs_archive/TOUTIAO_AUTO_PUBLISH_OPTIMIZATION.md` - 之前的优化报告

---

**修复进度**: 33% (1/3 完成)  
**预计完成时间**: 需要进一步调试和测试
