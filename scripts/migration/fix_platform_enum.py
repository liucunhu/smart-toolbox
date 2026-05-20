"""
修复数据库中枚举值大小写问题
将小写的平台名称转换为大写
"""
from app.db.session import SessionLocal, engine
from sqlalchemy import text

def fix_platform_enum():
    """修复platform字段的大小写问题"""
    db = SessionLocal()
    
    try:
        # 检查当前数据
        result = db.execute(text("SELECT id, platform FROM accounts"))
        accounts = result.fetchall()
        
        print(f"找到 {len(accounts)} 个账号")
        
        for account in accounts:
            account_id, platform = account
            print(f"账号ID: {account_id}, 平台: {platform}")
            
            # 如果平台是小写，转换为大写
            if platform and platform.islower():
                new_platform = platform.upper()
                print(f"  转换: {platform} -> {new_platform}")
                
                # 更新数据库
                db.execute(
                    text("UPDATE accounts SET platform = :platform WHERE id = :id"),
                    {"platform": new_platform, "id": account_id}
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
    fix_platform_enum()
