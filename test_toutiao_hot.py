"""测试今日头条热点获取"""
import asyncio
from app.services.content.hot_trend_injector import HotTrendInjector

async def test():
    injector = HotTrendInjector()
    result = await injector.fetch_trending_topics('toutiao', 5)
    print(f'获取到 {len(result)} 条数据')
    for i, r in enumerate(result[:5], 1):
        print(f'{i}. {r["keyword"]} (热度: {r.get("heat", 0):,})')

if __name__ == "__main__":
    asyncio.run(test())
