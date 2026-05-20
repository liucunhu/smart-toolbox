"""检查智能分析缓存"""
from app.db.session import SessionLocal
from app.services.analytics.analytics_cache import get_analytics_cache_service

db = SessionLocal()
cache_service = get_analytics_cache_service(db)

account_id = 9

print(f"检查账号 {account_id} 的智能分析缓存:")
print()

# 检查是否有可用分析
is_available = cache_service.is_analysis_available(account_id)
print(f"分析是否可用: {is_available}")

if is_available:
    # 获取优化提示词
    optimized_prompt = cache_service.get_optimized_prompt(account_id)
    if optimized_prompt:
        print(f"\n优化提示词长度: {len(optimized_prompt)} 字符")
        print(f"\n优化提示词内容:")
        print(optimized_prompt[:500])
        print("...")
    else:
        print("️  分析可用但没有优化提示词")
else:
    print("⚠️  暂无分析结果，建议先进行数据分析")

db.close()
