"""
查看发布记录脚本
直接从数据库查询 content_tasks 表
"""
import sys
from sqlalchemy import create_engine, text
from app.core.config import settings

def view_publish_records():
    """查看发布记录"""
    
    print("="*80)
    print("📊 Smart Toolbox - 发布记录查询")
    print("="*80)
    print()
    
    try:
        # 连接数据库
        engine = create_engine(settings.DATABASE_URL)
        
        with engine.connect() as conn:
            # 查询所有发布记录
            query = text("""
                SELECT 
                    id,
                    task_id,
                    original_topic AS '主题',
                    article_title AS '标题',
                    target_platform AS '平台',
                    article_category AS '分类',
                    status AS '状态',
                    LENGTH(article_content) AS '内容长度',
                    created_at AS '创建时间'
                FROM content_tasks 
                ORDER BY created_at DESC
                LIMIT 20
            """)
            
            result = conn.execute(query)
            rows = result.fetchall()
            
            if not rows:
                print("❌ 暂无发布记录")
                return
            
            print(f"✅ 找到 {len(rows)} 条发布记录\n")
            
            # 打印表头
            print(f"{'ID':<5} {'平台':<12} {'状态':<12} {'标题':<40} {'创建时间':<20}")
            print("-" * 90)
            
            # 打印每条记录
            for row in rows:
                id_, task_id, topic, title, platform, category, status, content_len, created_at = row
                
                # 截断标题
                display_title = (title[:37] + '...') if title and len(title) > 40 else (title or '无标题')
                
                # 格式化时间
                time_str = created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else 'N/A'
                
                print(f"{id_:<5} {platform:<12} {status:<12} {display_title:<40} {time_str:<20}")
            
            print()
            print("="*80)
            
            # 显示详细信息
            print("\n📝 详细记录信息:\n")
            
            for idx, row in enumerate(rows, 1):
                id_, task_id, topic, title, platform, category, status, content_len, created_at = row
                
                print(f"[{idx}] 记录 ID: {id_}")
                print(f"    任务ID: {task_id}")
                print(f"    主题: {topic or 'N/A'}")
                print(f"    标题: {title or 'N/A'}")
                print(f"    平台: {platform}")
                print(f"    分类: {category or 'N/A'}")
                print(f"    状态: {status}")
                print(f"    内容长度: {content_len or 0} 字符")
                print(f"    创建时间: {created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else 'N/A'}")
                print()
            
            print("="*80)
            print("\n💡 提示:")
            print("   - 这些是内容创作任务的记录")
            print("   - 要查看实际的发布结果，请检查日志或访问对应平台")
            print("   - 前端页面开发中: http://localhost:3000/publish-records")
            print()
            
    except Exception as e:
        print(f"❌ 查询失败: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    view_publish_records()
