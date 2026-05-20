"""
服务健康检查脚本
验证后端和前端服务是否正常运行
"""
import requests
import sys


def check_backend():
    """检查后端服务"""
    print("\n" + "="*80)
    print("🔍 检查后端服务 (http://localhost:8000)")
    print("="*80)
    
    try:
        # 测试首页
        response = requests.get("http://localhost:8000/", timeout=5)
        if response.status_code == 200:
            print("✅ 后端服务运行正常")
            print(f"   响应: {response.json()}")
        else:
            print(f"❌ 后端服务异常: HTTP {response.status_code}")
            return False
        
        # 测试API文档
        response = requests.get("http://localhost:8000/docs", timeout=5)
        if response.status_code == 200:
            print("✅ API文档可访问")
            print(f"   URL: http://localhost:8000/docs")
        else:
            print(f"⚠️  API文档访问异常: HTTP {response.status_code}")
        
        # 测试高级功能API
        endpoints = [
            "/api/v1/content/cover-templates",
            "/api/v1/content/generate-ai-cover",
        ]
        
        print("\n📋 高级封面图功能API:")
        for endpoint in endpoints:
            try:
                url = f"http://localhost:8000{endpoint}"
                if "generate" in endpoint:
                    # POST请求
                    response = requests.post(url, data={
                        "title": "测试",
                        "category": "科技"
                    }, timeout=5)
                else:
                    # GET请求
                    response = requests.get(url, timeout=5)
                
                if response.status_code == 200:
                    print(f"   ✅ {endpoint}")
                else:
                    print(f"   ⚠️  {endpoint} - HTTP {response.status_code}")
            except Exception as e:
                print(f"   ❌ {endpoint} - {str(e)}")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 后端服务未启动或无法连接")
        print("   请运行: python main.py")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        return False


def check_frontend():
    """检查前端服务"""
    print("\n" + "="*80)
    print("🔍 检查前端服务 (http://localhost:3001)")
    print("="*80)
    
    try:
        response = requests.get("http://localhost:3001/", timeout=5)
        if response.status_code == 200:
            print("✅ 前端服务运行正常")
            print(f"   URL: http://localhost:3001")
            return True
        else:
            print(f"❌ 前端服务异常: HTTP {response.status_code}")
            return False
        
    except requests.exceptions.ConnectionError:
        print("❌ 前端服务未启动或无法连接")
        print("   请运行: cd frontend && npm run dev")
        return False
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        return False


def check_port_conflict():
    """检查端口冲突"""
    print("\n" + "="*80)
    print("🔍 检查端口占用情况")
    print("="*80)
    
    import subprocess
    
    # 检查8000端口
    result = subprocess.run(
        ["netstat", "-ano"],
        capture_output=True,
        text=True
    )
    
    lines = result.stdout.split('\n')
    
    port_8000 = any(':8000' in line and 'LISTENING' in line for line in lines)
    port_3001 = any(':3001' in line and 'LISTENING' in line for line in lines)
    port_3000 = any(':3000' in line and 'LISTENING' in line for line in lines)
    
    print(f"\n端口状态:")
    print(f"   8000 (后端): {'✅ 已使用' if port_8000 else '❌ 未使用'}")
    print(f"   3001 (前端): {'✅ 已使用' if port_3001 else '❌ 未使用'}")
    print(f"   3000 (VMware): {'⚠️  被占用' if port_3000 else '✅ 空闲'}")
    
    if port_3000:
        print("\n⚠️  注意: 3000端口被VMware占用，前端已切换到3001端口")


def main():
    """主函数"""
    print("\n" + "="*80)
    print("🚀 Smart-Toolbox 服务健康检查")
    print("="*80)
    
    # 检查端口
    check_port_conflict()
    
    # 检查后端
    backend_ok = check_backend()
    
    # 检查前端
    frontend_ok = check_frontend()
    
    # 总结
    print("\n" + "="*80)
    print("📊 检查总结")
    print("="*80)
    
    if backend_ok and frontend_ok:
        print("\n🎉 所有服务运行正常!")
        print("\n访问地址:")
        print("   🌐 前端界面: http://localhost:3001")
        print("   📚 API文档: http://localhost:8000/docs")
        print("\n可以开始使用高级封面图功能了！")
        return True
    else:
        print("\n⚠️  部分服务未正常运行")
        if not backend_ok:
            print("   ❌ 后端服务未启动")
        if not frontend_ok:
            print("   ❌ 前端服务未启动")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
