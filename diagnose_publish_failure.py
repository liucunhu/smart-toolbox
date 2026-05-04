"""
诊断头条发布失败的原因
分析截图和 HTML 快照
"""
import os
from pathlib import Path

def diagnose_publish_failure():
    """诊断发布失败的原因"""
    
    print("="*80)
    print("🔍 头条发布失败诊断工具")
    print("="*80)
    
    # 查找最新的截图和 HTML
    logs_dir = Path("logs")
    
    # 查找最新的截图
    screenshots = list(logs_dir.glob("toutiao_after_publish_*.png"))
    htmls = list(logs_dir.glob("toutiao_after_publish_*.html"))
    
    if not screenshots:
        print("❌ 未找到发布后的截图")
        return
    
    latest_screenshot = max(screenshots, key=lambda x: x.stat().st_mtime)
    latest_html = max(htmls, key=lambda x: x.stat().st_mtime) if htmls else None
    
    print(f"\n📸 最新截图: {latest_screenshot}")
    print(f" 最新 HTML: {latest_html}")
    
    print("\n" + "="*80)
    print("请手动检查以下内容：")
    print("="*80)
    
    print("\n1. 打开截图文件，查看页面上显示了什么：")
    print(f"   文件路径: {latest_screenshot.absolute()}")
    
    if latest_html:
        print(f"\n2. 用浏览器打开 HTML 文件，查看页面完整内容：")
        print(f"   文件路径: {latest_html.absolute()}")
    
    print("\n3. 请告诉我页面上显示了什么：")
    print("   □ 是否有错误提示？（红色文字）")
    print("   □ 是否仍在编辑页面？（有标题框、正文编辑器）")
    print("   □ 是否跳转到了其他页面？")
    print("   □ 是否有成功提示？")
    print("   □ 页面底部有什么按钮？")
    
    print("\n" + "="*80)
    print("常见失败原因：")
    print("="*80)
    print("1. ❌ 标题长度不符合要求（2-30 个字）")
    print("2. ❌ 内容长度不足（至少需要一定字数）")
    print("3. ❌ 封面图未选择或上传失败")
    print("4. ❌ 作品声明未勾选（某些类型文章必需）")
    print("5. ❌ 网络连接问题")
    print("6. ❌ 头条服务器维护或限制")
    
    print("\n" + "="*80)
    print("下一步操作建议：")
    print("="*80)
    print("1. 查看截图和 HTML，确认页面状态")
    print("2. 告诉我页面上显示了什么")
    print("3. 我会根据具体情况调整代码")
    
    print("\n现在请打开截图文件查看！")
    print("="*80)

if __name__ == "__main__":
    diagnose_publish_failure()
