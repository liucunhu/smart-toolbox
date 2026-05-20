"""
账号管理功能测试脚本
测试创建、查询、更新、删除和登录功能
"""
import requests
import json


def test_account_management():
    """测试账号管理功能"""
    print("\n" + "="*80)
    print("👤 测试账号管理功能")
    print("="*80)
    
    base_url = "http://localhost:8000/api/v1"
    
    # 测试1: 创建账号
    print("\n1️⃣  测试1: 创建账号")
    print("-" * 80)
    
    response = requests.post(
        f"{base_url}/accounts/create",
        data={
            "platform": "toutiao",
            "username": "test_user_001",
            "password": "test_password",
            "proxy_ip": None
        }
    )
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("status") == "success":
        account_id = result["account"]["id"]
        print(f"✅ 账号创建成功，ID: {account_id}")
    else:
        print(f"❌ 账号创建失败: {result.get('detail')}")
        return False
    
    # 测试2: 获取账号列表
    print("\n2️⃣  测试2: 获取账号列表")
    print("-" * 80)
    
    response = requests.get(
        f"{base_url}/accounts/list",
        params={"platform": "toutiao"}
    )
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"总数: {result.get('total')}")
    print(f"账号数: {len(result.get('accounts', []))}")
    
    if result.get("accounts"):
        print("\n账号列表:")
        for acc in result["accounts"]:
            print(f"  - ID: {acc['id']}, 用户名: {acc['username']}, "
                  f"状态: {acc['status']}, 有Cookie: {acc['has_cookies']}")
        
        # 检查敏感信息是否隐藏
        first_account = result["accounts"][0]
        if "password" not in first_account and "cookies" not in first_account:
            print("\n✅ 敏感信息已正确隐藏")
        else:
            print("\n❌ 敏感信息未隐藏")
    else:
        print("⚠️  没有找到账号")
    
    # 测试3: 获取账号详情
    print("\n3️⃣  测试3: 获取账号详情")
    print("-" * 80)
    
    response = requests.get(f"{base_url}/accounts/{account_id}")
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if "id" in result:
        print(f"\n✅ 获取详情成功")
        # 检查敏感信息
        if "password" not in result or result.get("password") is None:
            print("✅ 密码已隐藏")
        if "cookies" not in result or result.get("cookies") is None:
            print("✅ Cookie已隐藏")
    else:
        print(f"❌ 获取详情失败")
    
    # 测试4: 更新账号信息
    print("\n4️⃣  测试4: 更新账号信息")
    print("-" * 80)
    
    response = requests.put(
        f"{base_url}/accounts/{account_id}",
        data={
            "username": "test_user_001_updated",
            "password": "new_password",
            "proxy_ip": "192.168.1.100"
        }
    )
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("status") == "success":
        print("✅ 账号更新成功")
        print(f"   新用户名: {result['account']['username']}")
        print(f"   代理IP: {result['account']['proxy_ip']}")
    else:
        print(f"❌ 账号更新失败")
    
    # 测试5: 智能登录（首次，应该使用账号密码）
    print("\n5️⃣  测试5: 智能登录（首次）")
    print("-" * 80)
    
    response = requests.post(
        f"{base_url}/accounts/toutiao/login",
        data={
            "account_id": account_id,
            "username": "test_user_001_updated",
            "password": "new_password"
        }
    )
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
    
    if result.get("status") == "success":
        print(f"✅ 登录成功")
        print(f"   登录方式: {result.get('login_method', 'unknown')}")
    else:
        print(f"⚠️  登录状态: {result.get('status')}")
        print(f"   消息: {result.get('message')}")
    
    # 测试6: 再次登录（应该使用Cookie）
    print("\n6️⃣  测试6: 再次登录（应使用Cookie）")
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
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)[:500]}...")
    
    if result.get("status") == "success":
        print(f"✅ 登录成功")
        print(f"   登录方式: {result.get('login_method', 'unknown')}")
        
        if result.get("login_method") == "cookie":
            print("✅ 正确使用了Cookie登录")
        else:
            print(f"⚠️  登录方式为: {result.get('login_method')}")
    else:
        print(f"⚠️  登录状态: {result.get('status')}")
    
    # 测试7: 删除账号
    print("\n7️⃣  测试7: 删除账号")
    print("-" * 80)
    
    response = requests.delete(f"{base_url}/accounts/{account_id}")
    
    result = response.json()
    print(f"状态码: {response.status_code}")
    print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
    
    if result.get("status") == "success":
        print("✅ 账号删除成功")
    else:
        print(f"❌ 账号删除失败")
    
    # 验证删除
    response = requests.get(f"{base_url}/accounts/{account_id}")
    if response.status_code == 404:
        print("✅ 验证删除成功（账号不存在）")
    else:
        print("⚠️  账号仍然存在")
    
    print("\n" + "="*80)
    print("📊 测试完成")
    print("="*80)
    
    return True


if __name__ == "__main__":
    print("\n" + "="*80)
    print("🚀 账号管理功能测试")
    print("="*80)
    
    try:
        test_account_management()
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
