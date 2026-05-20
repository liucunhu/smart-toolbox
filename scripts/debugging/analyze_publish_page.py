"""
分析头条发布页面的HTML，找出缺失的必填字段
"""
from bs4 import BeautifulSoup
import os


def analyze_publish_page():
    """分析发布页面HTML"""
    
    # 找到最新的发布前HTML文件
    html_files = [f for f in os.listdir('logs') if f.startswith('toutiao_pre_publish_') and f.endswith('.html')]
    
    if not html_files:
        print("❌ 未找到发布页面HTML文件")
        return
    
    # 使用最新的文件
    latest_file = sorted(html_files)[-1]
    file_path = f"logs/{latest_file}"
    
    print(f"📄 分析文件: {file_path}")
    print("="*80)
    
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. 查找所有按钮
    print("\n[1] 页面上的按钮:")
    buttons = soup.find_all(['button', 'a'], class_=lambda x: x and ('btn' in str(x).lower() or 'button' in str(x).lower()))
    for i, btn in enumerate(buttons[:20]):
        text = btn.get_text(strip=True)
        btn_class = btn.get('class', [])
        disabled = btn.get('disabled')
        style = btn.get('style', '')
        
        status = "✅" if text else "⚪"
        disabled_mark = "🔒" if disabled else ""
        
        print(f"  {status} [{i}] {text[:30]:30} class={btn_class} {disabled_mark}")
    
    # 2. 查找包含"发布"的元素
    print("\n[2] 包含'发布'关键词的元素:")
    publish_elements = soup.find_all(string=lambda text: text and '发布' in text)
    for elem in publish_elements[:10]:
        parent = elem.parent
        tag = parent.name
        btn_class = parent.get('class', [])
        disabled = parent.get('disabled')
        print(f"  - <{tag}> {elem.strip()[:50]} class={btn_class} disabled={disabled}")
    
    # 3. 查找错误提示
    print("\n[3] 错误提示:")
    error_selectors = [
        {'class': lambda x: x and 'error' in str(x).lower()},
        {'role': 'alert'},
        {'class': lambda x: x and 'message' in str(x).lower() and 'error' in str(x).lower()}
    ]
    
    errors_found = False
    for selector in error_selectors:
        errors = soup.find_all(**selector)
        for error in errors[:5]:
            text = error.get_text(strip=True)
            if text and len(text) > 5:
                print(f"  ❌ {text[:100]}")
                errors_found = True
    
    if not errors_found:
        print("  ✅ 未发现明显错误提示")
    
    # 4. 查找必填字段标记
    print("\n[4] 必填字段（带 * 号）:")
    required_fields = soup.find_all(string=lambda text: text and '*' in text)
    for field in required_fields[:20]:
        parent = field.parent
        # 向上查找标签
        label = parent.find_parent(['label', 'div', 'span'])
        if label:
            label_text = label.get_text(strip=True)
            print(f"  📋 {label_text[:50]}")
    
    # 5. 查找封面图相关元素
    print("\n[5] 封面图相关:")
    cover_elements = soup.find_all(string=lambda text: text and any(kw in text for kw in ['封面', '图片', '上传']))
    for elem in cover_elements[:10]:
        parent = elem.parent
        print(f"  🖼️  {elem.strip()[:50]} - 父元素: <{parent.name}>")
    
    # 6. 查找原创声明
    print("\n[6] 原创声明:")
    original_elements = soup.find_all(string=lambda text: text and '原创' in text)
    for elem in original_elements[:10]:
        parent = elem.parent
        print(f"  ©️  {elem.strip()[:50]} - 父元素: <{parent.name}>")
    
    # 7. 查找禁用的按钮
    print("\n[7] 禁用/不可点击的按钮:")
    disabled_buttons = soup.find_all(['button', 'a'], disabled=True)
    for btn in disabled_buttons[:10]:
        text = btn.get_text(strip=True)
        btn_class = btn.get('class', [])
        print(f"  🔒 {text[:30]:30} class={btn_class}")
    
    # 8. 检查表单状态
    print("\n[8] 表单输入框状态:")
    inputs = soup.find_all(['input', 'textarea', 'div'], attrs={'contenteditable': 'true'})
    for i, inp in enumerate(inputs[:10]):
        placeholder = inp.get('placeholder', '')
        value = inp.get('value', inp.get_text(strip=True))
        input_type = inp.get('type', inp.name)
        
        has_value = "✅" if value and len(value) > 0 else "❌"
        print(f"  {has_value} [{i}] type={input_type:15} placeholder={placeholder[:20]:20} value_len={len(value)}")
    
    print("\n" + "="*80)
    print("💡 建议:")
    print("  1. 检查是否有必填字段未填写")
    print("  2. 检查是否需要上传封面图")
    print("  3. 检查是否需要勾选原创声明")
    print("  4. 查看截图 logs/toutiao_pre_publish_*.png")
    print("="*80)


if __name__ == "__main__":
    try:
        from bs4 import BeautifulSoup
        analyze_publish_page()
    except ImportError:
        print("❌ 需要安装 beautifulsoup4")
        print("   运行: pip install beautifulsoup4")
