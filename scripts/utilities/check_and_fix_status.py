"""检查并修复status字段"""
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='toolbox_user',
    password='ToolboxPass123',
    database='smart_toolbox'
)

try:
    cursor = conn.cursor()
    
    # 检查ENUM定义
    cursor.execute("SHOW COLUMNS FROM accounts LIKE 'status'")
    result = cursor.fetchone()
    print(f"Status字段定义: {result[1]}")
    
    # 直接更新为小写值
    cursor.execute("UPDATE accounts SET status = 'registering'")
    conn.commit()
    print(f"更新了 {cursor.rowcount} 条记录")
    
    # 验证
    cursor.execute("SELECT id, status FROM accounts")
    rows = cursor.fetchall()
    print("\n修复后的数据:")
    for row in rows:
        print(f"ID: {row[0]}, Status: {row[1]}")
        
finally:
    conn.close()
