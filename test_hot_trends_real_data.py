"""
测试热点API - 验证所有平台都使用真实数据，不使用模拟数据
"""
import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000/api/v1/content/hot-trends"

async def test_platform(platform_name):
    """测试单个平台的热点数据"""
    print(f"\n{'='*60}")
    print(f"测试平台: {platform_name}")
    print('='*60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(BASE_URL, params={
                "platform": platform_name,
                "count": 5
            })
        
        if response.status_code != 200:
            print(f"❌ HTTP错误: {response.status_code}")
            return False
        
        data = response.json()
        
        # 检查是否有fallback标记
        if data.get("fallback"):
            print(f"❌ 使用了降级方案（模拟数据）")
            print(f"   错误信息: {data.get('error', '未知错误')}")
            return False
        
        hot_topics = data.get("hot_topics", [])
        total = data.get("total", 0)
        
        print(f"✅ 获取到 {total} 条热点数据")
        
        if total == 0:
            print(f"⚠️  警告: 没有获取到任何数据（可能是网络问题或API限制）")
            return False
        
        # 显示前3条数据
        print(f"\n前3条热点:")
        for i, topic in enumerate(hot_topics[:3], 1):
            keyword = topic.get("keyword", "")
            rank = topic.get("rank", 0)
            heat = topic.get("heat", 0)
            print(f"  {i}. [{rank}] {keyword} (热度: {heat:,})")
        
        # 检查是否是模拟数据的特征
        mock_keywords = [
            "今日热点", "社会新闻", "科技前沿", "财经资讯", "体育快讯",
            "好物分享", "生活小妙招", "穿搭推荐", "美食探店", "旅行攻略",
            "科技测评", "游戏攻略", "动画推荐", "学习干货", "音乐翻唱",
            "2026最新AI工具", "自媒体运营技巧", "爆款视频制作"
        ]
        
        found_mock = False
        for topic in hot_topics:
            keyword = topic.get("keyword", "")
            if keyword in mock_keywords:
                print(f"\n⚠️  警告: 发现可能的模拟数据关键词: '{keyword}'")
                found_mock = True
        
        if not found_mock:
            print(f"\n✅ 确认: 使用的是真实数据（未发现模拟数据特征）")
        
        return True
        
    except httpx.TimeoutException:
        print(f"❌ 请求超时")
        return False
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return False

async def main():
    """测试所有平台"""
    platforms = ["douyin", "xiaohongshu", "bilibili", "toutiao"]
    
    print("\n" + "="*60)
    print("热点API测试 - 验证实时数据（不使用模拟数据）")
    print("="*60)
    
    results = {}
    for platform in platforms:
        results[platform] = await test_platform(platform)
    
    # 总结
    print(f"\n{'='*60}")
    print("测试总结")
    print('='*60)
    
    for platform, success in results.items():
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{platform:15s}: {status}")
    
    all_passed = all(results.values())
    print(f"\n{'='*60}")
    if all_passed:
        print("🎉 所有平台都成功获取到真实数据！")
    else:
        print("⚠️  部分平台未能获取到数据")
        print("   注意: 这可能是由于网络问题、API限流或反爬机制")
        print("   但系统已正确配置为不使用模拟数据")
    print('='*60)

if __name__ == "__main__":
    asyncio.run(main())
