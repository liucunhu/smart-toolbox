"""检查账号9的发布记录"""
from app.db.session import SessionLocal
from app.models import Account, PublishRecord, ContentTask

db = SessionLocal()

# 检查账号9的发布记录
account_id = 9
records = db.query(PublishRecord).filter(PublishRecord.account_id == account_id).all()
print(f'账号 {account_id} 的发布记录数量: {len(records)}')

for r in records[-3:]:
    task = db.query(ContentTask).filter(ContentTask.id == r.content_task_id).first()
    if task:
        print(f'  - 文章: {task.article_title[:30] if task.article_title else "N/A"}...')
        print(f'    状态: {r.publish_status}')
        print(f'    发布时间: {r.publish_time}')

db.close()
