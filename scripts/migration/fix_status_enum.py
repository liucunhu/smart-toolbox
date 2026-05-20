"""
修复数据库中status字段的大小写问题
将大写的状态值转换为小写
"""
from app.db.session import SessionLocal
from sqlalchemy import text

def fix_status_enum():
    """修复status字段的大小写问题"""
    db = SessionLocal()
    
    try:
        # 检查当前数据
        result = db.execute(text("SELECT id, status FROM accounts"))
        accounts = result.fetchall()
        
        print(f"找到 {len(accounts)} 个账号")
        
        for account in accounts:
            account_id, status = account
            print(f"账号ID: {account_id}, 状态: {status}")
            
            # 如果状态是大写，转换为小写
            if status and status.isupper():
                new_status = status.lower()
                print(f"  转换: {status} -> {new_status}")
                
                # 更新数据库
                db.execute(
                    text("UPDATE accounts SET status = :status WHERE id = :id"),
                    {"status": new_status, "id": account_id}
                )
        
        # 提交更改
        db.commit()
        print("\n✅ 修复完成！")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ 修复失败: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    fix_status_enum()
