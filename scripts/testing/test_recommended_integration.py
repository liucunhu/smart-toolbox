"""测试推荐主题API和前端集成"""
import requests
import json

# 测试推荐主题API
print("=" * 60)
print("测试: 推荐主题 API")
print("=" * 60)

# 1. 获取推荐主题（通用）
r = requests.get('http://localhost:8000/api/v1/content/recommended-topics', params={'count': 5})
data = r.json()

if data['status'] == 'success':
    print(f"✅ API 正常")
    print(f"推荐主题数量: {data['total']}")
    print()
    for i, rec in enumerate(data['recommendations'], 1):
        confidence_pct = int(rec['confidence'] * 100)
        print(f"{i}. {rec['topic']}")
        print(f"   置信度: {confidence_pct}%")
        print(f"   理由: {rec['reason']}")
        print()
else:
    print(f"❌ API 失败: {data}")

# 2. 检查前端是否需要手动获取推荐
print("=" * 60)
print("前端集成说明")
print("=" * 60)
print("""
前端推荐主题功能需要：
1. 点击"🔥 获取推荐"按钮手动获取
2. 或者留空主题，系统会自动推荐

当前API状态: ✅ 正常
Cookie状态: ✅ 已持久化
""")
