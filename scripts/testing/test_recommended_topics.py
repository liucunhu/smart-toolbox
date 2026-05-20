"""测试推荐主题API"""
import requests
import json

# 测试1：获取推荐主题
print("=" * 60)
print("测试: 获取推荐主题")
print("=" * 60)

r = requests.get('http://localhost:8000/api/v1/content/recommended-topics', params={'count': 3})
data = r.json()

print(f"Status: {data['status']}")
print(f"Total: {data['total']}")
print()
for i, rec in enumerate(data['recommendations'], 1):
    confidence_pct = int(rec['confidence'] * 100)
    print(f"{i}. {rec['topic']}")
    print(f"   置信度: {confidence_pct}%")
    print(f"   理由: {rec['reason']}")
    print()
