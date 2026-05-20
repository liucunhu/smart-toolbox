"""
测试智能主题推荐功能
"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_get_recommended_topics():
    """测试获取推荐主题API"""
    print("=" * 60)
    print("测试1: 获取推荐主题（个性化）")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/content/recommended-topics",
            params={
                "account_id": 9,
                "count": 5
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态: {data.get('status')}")
            print(f"📊 推荐数量: {data.get('total')}")
            print(f"\n🔥 推荐主题列表:")
            
            for i, rec in enumerate(data.get('recommendations', []), 1):
                topic = rec.get('topic', '')
                confidence = rec.get('confidence', 0)
                reason = rec.get('reason', '')
                
                # 置信度图标
                if confidence >= 0.8:
                    icon = "🟢"
                elif confidence >= 0.6:
                    icon = "🟡"
                else:
                    icon = "🔴"
                
                print(f"\n{i}. {icon} {topic}")
                print(f"   置信度: {confidence:.0%}")
                print(f"   理由: {reason}")
            
            print(f"\n📝 格式化文本:")
            print(data.get('formatted_text', ''))
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 错误: {e}")


def test_get_recommended_topics_generic():
    """测试获取通用推荐主题（不提供账号ID）"""
    print("\n" + "=" * 60)
    print("测试2: 获取通用推荐主题（无账号ID）")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/content/recommended-topics",
            params={
                "count": 3
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态: {data.get('status')}")
            print(f"📊 推荐数量: {data.get('total')}")
            
            for i, rec in enumerate(data.get('recommendations', []), 1):
                print(f"{i}. {rec.get('topic', '')} (置信度: {rec.get('confidence', 0):.0%})")
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 错误: {e}")


def test_auto_publish_with_recommendation():
    """测试一键发布时自动推荐主题"""
    print("\n" + "=" * 60)
    print("测试3: 一键发布（留空主题，测试自动推荐）")
    print("=" * 60)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/content/toutiao/auto_publish",
            params={
                "account_id": 9,
                "topic": "",  # 留空，触发自动推荐
                "category": "科技",
                "auto_generate_cover": True,
                "use_cdp": False
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 状态: {data.get('status')}")
            print(f"📝 文章标题: {data.get('article_title', 'N/A')}")
            print(f"📄 内容长度: {data.get('article_content_length', 0)}")
            
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ 错误: {e}")


if __name__ == "__main__":
    print("🚀 开始测试智能主题推荐功能\n")
    
    # 测试1: 获取个性化推荐
    test_get_recommended_topics()
    
    # 测试2: 获取通用推荐
    test_get_recommended_topics_generic()
    
    # 测试3: 一键发布自动推荐（可选，会实际发布文章）
    # test_auto_publish_with_recommendation()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成")
    print("=" * 60)
