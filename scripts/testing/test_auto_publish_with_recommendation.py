"""测试一键发布功能（留空主题自动推荐）"""
import requests
import json

BASE_URL = "http://localhost:8000"

print("=" * 70)
print("测试: 一键发布（留空主题触发自动推荐）")
print("=" * 70)
print()

# 测试参数
test_params = {
    "account_id": 9,
    "topic": "",  # 留空，触发自动推荐
    "category": "科技",
    "auto_generate_cover": True,
    "auto_generate_images": True,
    "num_images": 2,
    "use_cdp": False,
    "cdp_port": 9222,
    "declarations": json.dumps(["个人观点"])
}

print("请求参数:")
print(f"  account_id: {test_params['account_id']}")
print(f"  topic: '{test_params['topic']}' (留空)")
print(f"  category: {test_params['category']}")
print()

print("预期行为:")
print("  1. 后端检测到主题为空")
print("  2. 调用推荐服务获取热门话题")
print("  3. 自动选择置信度最高的主题")
print("  4. 使用该主题生成文章并发布")
print()

print("=" * 70)
print("ℹ️  请在浏览器中测试:")
print("=" * 70)
print("""
1. 刷新前端页面（Ctrl+F5 强制刷新）
2. 选择账号 (ID: 9)
3. 留空"文章主题"输入框
4. 点击"一键发布"按钮
5. 应该会弹出确认对话框："您未输入主题，系统将自动..."
6. 点击"✅ 使用智能推荐"
7. 观察后端日志，应该看到:
   - ✅ [步骤2.0] 自动推荐主题: XXX
   - ✅ Cookie已更新到数据库
   - ✅ 文章生成成功
""")
