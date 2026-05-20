"""修改accounts表的status字段ENUM定义为小写"""
import pymysql

conn = pymysql.connect(
    host='localhost',
    user='toolbox_user',
    password='ToolboxPass123',
    database='smart_toolbox'
)

try:
    cursor = conn.cursor()
    
    # 修改status字段的ENUM定义
    print("修改status字段ENUM定义...")
    cursor.execute("""
        ALTER TABLE accounts 
        MODIFY COLUMN status ENUM('registering', 'nurturing', 'active', 'banned') 
        DEFAULT 'registering'
    """)
    conn.commit()
    print("✅ status字段修改成功")
    
    # 修改platform字段的ENUM定义
    print("\n修改platform字段ENUM定义...")
    cursor.execute("""
        ALTER TABLE accounts 
        MODIFY COLUMN platform ENUM('douyin', 'xiaohongshu', 'bilibili', 'video_account', 'toutiao') 
        NOT NULL
    """)
    conn.commit()
    print("✅ platform字段修改成功")
    
    # 验证修改结果
    print("\n验证修改结果:")
    cursor.execute("SHOW COLUMNS FROM accounts LIKE 'status'")
    result = cursor.fetchone()
    print(f"Status字段定义: {result[1]}")
    
    cursor.execute("SHOW COLUMNS FROM accounts LIKE 'platform'")
    result = cursor.fetchone()
    print(f"Platform字段定义: {result[1]}")
    
    # 检查数据
    cursor.execute("SELECT id, platform, status FROM accounts")
    rows = cursor.fetchall()
    print("\n当前数据:")
    for row in rows:
        print(f"ID: {row[0]}, Platform: {row[1]}, Status: {row[2]}")
        
finally:
    conn.close()
