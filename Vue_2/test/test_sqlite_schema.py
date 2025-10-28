import sqlite3
import os

def test_sqlite_schema():
    """测试SQLite数据库模式是否正确"""
    
    # 创建临时内存数据库进行测试
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # 读取schema.sql文件内容
    schema_path = os.path.join(os.path.dirname(__file__), '../backend/app/schema.sql')
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("读取schema.sql文件内容：")
        print(sql_script)
        print("-" * 50)
        
        # 执行SQL脚本
        print("执行SQL脚本...")
        cursor.executescript(sql_script)
        conn.commit()
        print("✅ SQL脚本执行成功！")
        
        # 检查表是否创建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        
        print("\n创建的表：")
        for table in tables:
            print(f"- {table[0]}")
        
        # 检查每个表的结构
        print("\n各表结构：")
        for table_name in ['users', 'items', 'favorites', 'messages']:
            print(f"\n{table_name}表：")
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns_info = cursor.fetchall()
            for col in column_info:
                print(f"  {col[1]} ({col[2]}) {'PRIMARY KEY' if col[5] else ''}")
        
        # 测试插入数据
        print("\n测试插入数据...")
        cursor = cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            ("testuser", "testhash", "test@example.com")
        )
        conn.commit()
        
        print("✅ 数据插入成功！")
        
        # 测试查询
        cursor.execute("SELECT * FROM users")
        user = cursor.fetchone()
        print(f"\n查询结果：{user}")
        
        # 测试外键约束
        print("\n测试外键约束...")
        try:
            # 尝试插入不存在用户的商品（应该失败）
            cursor.execute(
                "INSERT INTO items (seller_id, title, price) VALUES (999, '测试商品', 99.99)",
            )
            conn.commit()
            print("❌ 外键约束测试失败：允许插入了不存在用户的商品")
        except sqlite3.IntegrityError as e:
            print(f"✅ 外键约束束测试通过：{e}")
            conn.rollback()
        
        print("\n✅ 所有测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== 测试SQLite数据库模式 ===")
    test_sqlite_schema()
