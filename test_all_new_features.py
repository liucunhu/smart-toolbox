"""
完整功能测试脚本
验证所有新增API是否正常工作
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"

def test_hot_trend_injection():
    """测试热点关键词注入"""
    print("\n🧪 测试1: 热点关键词注入")
    print("-" * 50)
    
    response = requests.post(
        f"{BASE_URL}/content/inject-hot-trend",
        json={
            "script": "这是一段测试文案，用于演示热点注入功能。今天我们来聊聊Python编程。",
            "platform": "douyin",
            "keywords": ["热门推荐", "今日话题", "爆款内容"]
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 状态: {data['status']}")
        print(f"✅ 原文长度: {data['original_length']}")
        print(f"✅ 新文长度: {data['modified_length']}")
        print(f"✅ 权重分数: {data['weight_score']}")
        print(f"✅ 标签: {data['hashtags']}")
        print(f"✅ 注入关键词: {data['injected_keywords']}")
        print(f"✅ 注入后文案:\n{data['script'][:200]}...")
    else:
        print(f"❌ 失败: {response.status_code}")
        print(response.text)


def test_alert_config():
    """测试报警配置"""
    print("\n🧪 测试2: 报警配置")
    print("-" * 50)
    
    # 测试邮件配置
    print("\n📧 保存邮件配置...")
    response = requests.post(
        f"{BASE_URL}/alerts/config/email",
        json={
            "enabled": True,
            "host": "smtp.example.com",
            "port": 587,
            "user": "noreply@example.com",
            "password": "test_password",
            "to": ["admin@example.com", "ops@example.com"]
        }
    )
    
    if response.status_code == 200:
        print(f"✅ 邮件配置保存成功")
    else:
        print(f"❌ 邮件配置失败: {response.status_code}")
    
    # 测试钉钉配置
    print("\n💬 保存钉钉配置...")
    response = requests.post(
        f"{BASE_URL}/alerts/config/dingtalk",
        json={
            "webhook_url": "https://oapi.dingtalk.com/robot/send?access_token=test",
            "at_mobiles": ["13800138000"]
        }
    )
    
    if response.status_code == 200:
        print(f"✅ 钉钉配置保存成功")
    else:
        print(f"❌ 钉钉配置失败: {response.status_code}")


def test_alert_test():
    """测试报警发送"""
    print("\n🧪 测试3: 报警测试")
    print("-" * 50)
    
    # 测试邮件
    print("\n📧 发送测试邮件...")
    response = requests.post(f"{BASE_URL}/alerts/test/email")
    
    if response.status_code == 200:
        print(f"✅ {response.json()['message']}")
    else:
        print(f"❌ 测试邮件失败: {response.status_code}")
    
    # 测试钉钉
    print("\n💬 发送测试钉钉消息...")
    response = requests.post(f"{BASE_URL}/alerts/test/dingtalk")
    
    if response.status_code == 200:
        print(f"✅ {response.json()['message']}")
    else:
        print(f"❌ 测试钉钉失败: {response.status_code}")


def test_sms_config():
    """测试SMS配置"""
    print("\n🧪 测试4: SMS配置")
    print("-" * 50)
    
    # 保存配置
    print("\n📱 保存SMS配置...")
    response = requests.post(
        f"{BASE_URL}/sms/config",
        json={
            "api_key": "test_api_key_123456",
            "base_url": "https://api.sms-platform.com"
        }
    )
    
    if response.status_code == 200:
        print(f"✅ SMS配置保存成功")
    else:
        print(f"❌ SMS配置失败: {response.status_code}")
    
    # 测试连接
    print("\n🔗 测试SMS连接...")
    response = requests.post(
        f"{BASE_URL}/sms/test-connection",
        json={
            "api_key": "test_api_key_123456",
            "base_url": "https://api.sms-platform.com"
        }
    )
    
    if response.status_code == 200:
        print(f"✅ {response.json()['message']}")
    else:
        print(f"❌ SMS连接测试失败: {response.status_code}")


def test_alert_history():
    """测试报警历史查询"""
    print("\n🧪 测试5: 报警历史查询")
    print("-" * 50)
    
    response = requests.get(
        f"{BASE_URL}/alerts/history",
        params={"skip": 0, "limit": 10}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 查询成功")
        print(f"✅ 总数: {data['total']}")
        print(f"✅ 返回记录数: {len(data['alerts'])}")
    else:
        print(f"❌ 查询失败: {response.status_code}")


def test_phone_records():
    """测试手机号记录查询"""
    print("\n🧪 测试6: 手机号记录查询")
    print("-" * 50)
    
    response = requests.get(
        f"{BASE_URL}/sms/phone-records",
        params={"skip": 0, "limit": 10}
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 查询成功")
        print(f"✅ 总数: {data['total']}")
        print(f"✅ 返回记录数: {len(data['records'])}")
    else:
        print(f"❌ 查询失败: {response.status_code}")


def test_ab_test_create():
    """测试A/B测试创建"""
    print("\n🧪 测试7: A/B测试创建")
    print("-" * 50)
    
    test_id = f"test_{int(time.time())}"
    
    response = requests.post(
        f"{BASE_URL}/content/ab-test/create",
        json={
            "test_id": test_id,
            "article_title": "Python入门教程",
            "cover_variants": [
                {
                    "variant_id": "A",
                    "file_path": "uploads/covers/cover_a.jpg",
                    "description": "现代风格"
                },
                {
                    "variant_id": "B",
                    "file_path": "uploads/covers/cover_b.jpg",
                    "description": "极简风格"
                }
            ],
            "description": "测试不同封面风格的点击率"
        }
    )
    
    if response.status_code == 200:
        print(f"✅ A/B测试创建成功: {test_id}")
        return test_id
    else:
        print(f"❌ 创建失败: {response.status_code}")
        print(response.text)
        return None


def test_ab_test_results(test_id):
    """测试A/B测试结果查询"""
    if not test_id:
        return
    
    print("\n🧪 测试8: A/B测试结果查询")
    print("-" * 50)
    
    response = requests.get(f"{BASE_URL}/content/ab-test/{test_id}")
    
    if response.status_code == 200:
        print(f"✅ 查询成功")
        print(f"✅ 测试ID: {response.json().get('test_id')}")
        print(f"✅ 状态: {response.json().get('status')}")
    else:
        print(f"❌ 查询失败: {response.status_code}")


def test_schedule():
    """测试智能调度"""
    print("\n🧪 测试9: 智能调度")
    print("-" * 50)
    
    response = requests.get(f"{BASE_URL}/schedule/next_time")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 下一个发布时间: {data['suggested_time']}")
    else:
        print(f"❌ 查询失败: {response.status_code}")


def test_healthy_accounts():
    """测试健康账号查询"""
    print("\n🧪 测试10: 健康账号查询")
    print("-" * 50)
    
    response = requests.get(f"{BASE_URL}/accounts/healthy")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 健康账号数量: {data['count']}")
        print(f"✅ 账号列表:")
        for account in data['accounts']:
            print(f"   - ID: {account['id']}, 用户名: {account['username']}")
    else:
        print(f"❌ 查询失败: {response.status_code}")


def main():
    """运行所有测试"""
    print("=" * 60)
    print("Smart-Toolbox 完整功能测试")
    print("=" * 60)
    
    try:
        test_hot_trend_injection()
        test_alert_config()
        test_alert_test()
        test_sms_config()
        test_alert_history()
        test_phone_records()
        
        # A/B测试需要先创建再查询
        test_id = test_ab_test_create()
        time.sleep(1)
        test_ab_test_results(test_id)
        
        test_schedule()
        test_healthy_accounts()
        
        print("\n" + "=" * 60)
        print("✅ 所有测试完成！")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
