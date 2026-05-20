"""
使用默认Edge浏览器打开头条发布页面
"""
import asyncio
import subprocess
import time


def open_edge_browser():
    """使用Edge浏览器打开头条发布页面"""
    
    print("="*80)
    print(" 使用Edge浏览器打开头条发布页面")
    print("="*80)
    
    # Edge浏览器路径
    edge_path = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    
    # 头条发布页面URL
    publish_url = "https://mp.toutiao.com/profile_v4/graphic/publish?from=toutiao_pc"
    
    print(f"\n 正在打开: {publish_url}")
    print("💡 请在浏览器中：")
    print("   1. 检查页面是否完整加载（标题输入框、正文编辑器、发布按钮）")
    print("   2. 如果页面不完整，请截图告诉我")
    print("   3. 确认页面完整后，按回车继续\n")
    
    # 打开Edge浏览器
    subprocess.Popen([edge_path, publish_url])
    
    # 等待用户确认
    input("页面加载完成后，按回车继续...")
    
    print("\n✅ 好的！现在我们知道页面结构了")
    print("\n下一步：")
    print("   - 如果页面完整 → 我们可以开始自动化测试")
    print("   - 如果页面不完整 → 请告诉我看到了什么，我来调整方案")


if __name__ == "__main__":
    open_edge_browser()
