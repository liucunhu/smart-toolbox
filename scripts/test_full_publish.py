"""
完整测试一键发布功能（包含文章生成、封面图、配图）
"""
import requests
import json
import os

# API配置
BASE_URL = "http://localhost:8000/api/v1"

def test_auto_publish():
    """测试一键全自动发布（推荐）"""
    print("="*80)
    print("🧪 测试：一键全自动发布")
    print("="*80)
    
    # 准备测试数据
    payload = {
        "account_id": 9,
        "topic": "如何使用DeepSeek生成爆款文章",
        "username": "17739848781",
        "password": "Lch@12345",
        "category": "科技",
        
        # ✅ 关键参数：启用封面图生成
        "auto_generate_cover": True,
        "cover_style": "modern",
        
        # ✅ CDP模式
        "use_cdp": True,
        "cdp_port": 9222,
        
        # ✅ 作品声明
        "declaration_type": "ai"
    }
    
    print(f"\n📤 发送请求到: {BASE_URL}/content/toutiao/auto_publish")
    print(f"📝 主题: {payload['topic']}")
    print(f"🎨 封面生成: {payload['auto_generate_cover']}")
    print(f"🌐 CDP模式: {payload['use_cdp']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/content/toutiao/auto_publish",
            params=payload,  # ✅ 使用 params 而不是 json
            timeout=300  # 5分钟超时
        )
        
        print(f"\n📥 响应状态码: {response.status_code}")
        print(f"📄 响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("\n✅ 测试成功！")
                print(f"   标题: {result.get('article_title', 'N/A')}")
                print(f"   内容长度: {result.get('article_content_length', 0)} 字")
                print(f"   分类: {result.get('category', 'N/A')}")
                print(f"   标签: {', '.join(result.get('tags', []))}")
            else:
                print(f"\n❌ 发布失败: {result.get('error', '未知错误')}")
        else:
            print(f"\n❌ HTTP错误: {response.status_code}")
            print(response.text)
            
    except requests.exceptions.Timeout:
        print("\n⏱️  请求超时（超过5分钟）")
        print("💡 提示：头条发布可能需要较长时间，请耐心等待")
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def test_manual_publish_with_cover():
    """测试手动发布（带封面图生成）"""
    print("\n" + "="*80)
    print("🧪 测试：手动发布（带封面图生成）")
    print("="*80)
    
    # 先调用AI生成接口
    print("\n步骤1: 生成文章内容...")
    generate_payload = {
        "platform": "toutiao",
        "topic": "如何使用DeepSeek生成爆款文章"
    }
    
    try:
        gen_response = requests.post(
            f"{BASE_URL}/content/generate",
            json=generate_payload,
            timeout=60
        )
        
        if gen_response.status_code != 200:
            print(f"❌ 生成失败: {gen_response.status_code}")
            return
        
        gen_result = gen_response.json()
        article_title = gen_result.get("article_title", "测试标题")
        article_content = gen_result.get("article_content", "测试内容")
        
        print(f"✅ 文章生成成功")
        print(f"   标题: {article_title}")
        print(f"   内容长度: {len(article_content)} 字")
        
    except Exception as e:
        print(f"❌ 生成失败: {e}")
        print("💡 使用默认测试内容")
        article_title = "测试文章标题"
        article_content = "这是测试文章内容，用于验证发布功能。" * 10
    
    # 然后调用发布接口
    print("\n步骤2: 发布文章（带封面图生成）...")
    publish_payload = {
        "account_id": 9,
        "title": article_title,
        "content": article_content,
        "category": "科技",
        "tags": ["DeepSeek", "AI", "爆款文章"],
        
        # ✅ 关键参数：启用封面图生成
        "auto_generate_cover": True,
        "cover_style": "modern",
        
        # ✅ CDP模式
        "use_cdp": True,
        "cdp_port": 9222,
        
        # ✅ 作品声明
        "declaration_type": "ai"
    }
    
    print(f"📤 发送请求到: {BASE_URL}/content/toutiao/publish")
    print(f"🎨 封面生成: {publish_payload['auto_generate_cover']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/content/toutiao/publish",
            params=publish_payload,  # ✅ 使用 params 而不是 json
            timeout=300
        )
        
        print(f"\n📥 响应状态码: {response.status_code}")
        print(f"📄 响应内容:")
        print(json.dumps(response.json(), indent=2, ensure_ascii=False))
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "success":
                print("\n✅ 测试成功！")
            else:
                print(f"\n❌ 发布失败: {result.get('error', '未知错误')}")
                
    except Exception as e:
        print(f"\n❌ 请求失败: {e}")


def check_logs():
    """检查最新日志"""
    print("\n" + "="*80)
    print("📋 检查最新日志")
    print("="*80)
    
    log_dir = "logs"
    if not os.path.exists(log_dir):
        print("❌ 日志目录不存在")
        return
    
    # 获取最新的日志文件
    log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
    if not log_files:
        print("❌ 没有找到日志文件")
        return
    
    latest_log = sorted(log_files)[-1]
    log_path = os.path.join(log_dir, latest_log)
    
    print(f"📄 最新日志: {latest_log}")
    print("\n🔍 查找关键信息...")
    
    keywords = [
        "auto_generate_cover",
        "LLM智能封面生成",
        "封面图已生成",
        "文章配图",
        "AI生成封面图"
    ]
    
    found = False
    with open(log_path, 'r', encoding='utf-8') as f:
        for line in f:
            for keyword in keywords:
                if keyword in line:
                    print(f"   {line.strip()}")
                    found = True
    
    if not found:
        print("   ⚠️  未找到相关日志，可能参数未传递")


if __name__ == "__main__":
    print("\n🚀 开始测试一键发布功能\n")
    
    # 测试1：一键全自动发布（推荐）
    test_auto_publish()
    
    # 测试2：手动发布（带封面图）
    # test_manual_publish_with_cover()
    
    # 检查日志
    check_logs()
    
    print("\n" + "="*80)
    print("✅ 测试完成！")
    print("="*80)
    print("\n💡 提示：")
    print("   1. 如果看到'未提供封面图'，说明 auto_generate_cover 参数未传递")
    print("   2. 请强制刷新浏览器（Ctrl+Shift+R）以获取最新前端代码")
    print("   3. 或直接使用本脚本测试API功能")
    print("="*80)
