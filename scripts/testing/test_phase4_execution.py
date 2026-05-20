"""
Phase 4 任务执行引擎测试脚本
测试智能体任务执行功能
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


async def test_execution_engine():
    """测试任务执行引擎"""
    print("=" * 60)
    print("Phase 4 任务执行引擎测试")
    print("=" * 60)
    
    # 初始化执行器
    print("\n1. 初始化任务执行器...")
    from app.services.agents.executor_initializer import initialize_executors
    initialize_executors()
    print("✅ 执行器初始化成功")
    
    # 获取已注册的执行器
    from app.services.agents.task_execution_engine import execution_engine
    print(f"\n2. 已注册的智能体类型: {list(execution_engine.executors.keys())}")
    
    # 测试研究智能体
    print("\n3. 测试研究智能体...")
    result = await execution_engine.execute_task(
        agent_type="research",
        task_params={
            "task_type": "topic_research",
            "platform": "toutiao",
            "category": "科技",
            "keyword": "AI"
        },
        task_id="test_001"
    )
    print(f"   状态: {result['status']}")
    print(f"   耗时: {result['duration']:.2f}秒")
    if result['status'] == 'success':
        print(f"   找到话题数: {result['data'].get('total_found', 0)}")
    
    # 测试内容生成智能体
    print("\n4. 测试内容生成智能体...")
    result = await execution_engine.execute_task(
        agent_type="content_generation",
        task_params={
            "topic": "人工智能",
            "style": "professional",
            "length": "medium"
        },
        task_id="test_002"
    )
    print(f"   状态: {result['status']}")
    print(f"   耗时: {result['duration']:.2f}秒")
    if result['status'] == 'success':
        print(f"   生成字数: {result['data'].get('word_count', 0)}")
    
    # 测试合规检查智能体
    print("\n5. 测试合规检查智能体...")
    result = await execution_engine.execute_task(
        agent_type="compliance_check",
        task_params={
            "content": "这是一篇测试文章的内容",
            "platform": "toutiao"
        },
        task_id="test_003"
    )
    print(f"   状态: {result['status']}")
    print(f"   耗时: {result['duration']:.2f}秒")
    if result['status'] == 'success':
        print(f"   是否合规: {result['data'].get('is_compliant', False)}")
    
    # 查看执行历史
    print("\n6. 查看执行历史...")
    history = execution_engine.get_task_history(limit=5)
    print(f"   历史记录数: {len(history)}")
    for record in history:
        print(f"   - 任务ID: {record['task_id']}, 类型: {record['agent_type']}, 状态: {record['status']}")
    
    # 查看执行统计
    print("\n7. 查看执行统计...")
    stats = execution_engine.get_executor_stats()
    for agent_type, stat in stats.items():
        print(f"   {agent_type}: 总任务={stat['total_tasks']}, 成功={stat['success_count']}, 失败={stat['failed_count']}")
    
    print("\n" + "=" * 60)
    print("✅ 所有测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        asyncio.run(test_execution_engine())
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
