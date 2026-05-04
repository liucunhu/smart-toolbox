"""
智能登录功能测试脚本
测试Cookie优先登录和账号密码回退机制
"""
import requests
import json


def test_smart_login():
    """测试智能登录功能"""
    print("\n" + "="*80)
    print("🔐 测试智能登录功能")
    print("="*80)
    
    base_url = "http://localhost:8000/api/v1"
    account_id = 1
    
    # 测试1: 首次登录（使用账号密码）
    print("\n1️⃣  测试1: 首次登录（使用账号密码）")
    print("-" * 80)
    
    response = requests.post(
        f"{base_url}/accounts/toutiao/login",
        data={
            "account_id": account_id,
            "username": "your_username",  # 替换为实际账号
            "password": "your_password"   # 替换为实际密码
        }
    )
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("status") == "success":
        print("✅ 首次登录成功")
        print(f"   登录方式: {result.get('login_method', 'unknown')}")
    else:
        print(f"❌ 首次登录失败: {result.get('message')}")
        return False
    
    # 测试2: 再次登录（应该使用Cookie）
    print("\n2️⃣  测试2: 再次登录（应使用Cookie）")
    print("-" * 80)
    
    response = requests.post(
        f"{base_url}/accounts/toutiao/login",
        data={
            "account_id": account_id
            # 不提供username和password
        }
    )
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("status") == "success":
        print("✅ Cookie登录成功")
        print(f"   登录方式: {result.get('login_method', 'unknown')}")
        
        if result.get("login_method") == "cookie":
            print("✅ 正确使用了Cookie登录")
        else:
            print(f"⚠️  登录方式为: {result.get('login_method')}")
    else:
        print(f"❌ Cookie登录失败: {result.get('message')}")
    
    # 测试3: 发布文章（使用智能登录）
    print("\n3️⃣  测试3: 发布文章（智能登录）")
    print("-" * 80)
    
    response = requests.post(
        f"{base_url}/content/toutiao/publish",
        data={
            "account_id": account_id,
            "title": "智能登录功能测试",
            "content": "这是一篇测试文章，用于验证智能登录功能。",
            "category": "科技"
            # 不提供username和password，系统会自动使用Cookie
        }
    )
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
    
    if result.get("status") in ["success", "pending"]:
        print("✅ 发布成功（使用了智能登录）")
    else:
        print(f"⚠️  发布状态: {result.get('status')}")
        print(f"   错误: {result.get('error')}")
    
    # 测试4: 全自动发布（内置智能登录）
    print("\n4️⃣  测试4: 全自动发布（内置智能登录）")
    print("-" * 80)
    
    response = requests.post(
        f"{base_url}/content/toutiao/auto_publish",
        data={
            "account_id": account_id,
            "topic": "人工智能发展趋势",
            "username": "your_username",  # 提供作为备用
            "password": "your_password",  # 提供作为备用
            "auto_generate_cover": "true"
        }
    )
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
    
    if result.get("status") == "success":
        print("✅ 全自动发布成功")
    else:
        print(f"⚠️  发布状态: {result.get('status')}")
    
    print("\n" + "="*80)
    print("📊 测试完成")
    print("="*80)
    print("\n💡 提示:")
    print("   - 如果Cookie有效，登录会非常快（~3秒）")
    print("   - 如果Cookie失效，系统会自动使用账号密码登录")
    print("   - 查看日志可以了解具体使用了哪种登录方式")
    
    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 智能登录功能测试")
    print("="*80)
    print("\n⚠️  注意: 请将测试脚本中的账号密码替换为实际值")
    print("="*80)
    
    try:
        test_smart_login()
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
