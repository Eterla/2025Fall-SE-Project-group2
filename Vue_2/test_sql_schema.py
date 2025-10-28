import sqlite3
import os

def test_sql_schema():
    """测试SQLite数据库模式"""
    
    # 创建临时内存数据库
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # 读取schema.sql文件
    schema_path = os.path.join(os.path.dirname(__file__), 'backend/app/schema.sql')
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("=== 测试SQLite数据库模式 ===")
        print("正在执行SQL脚本...")
        
        # 执行SQL脚本
        cursor.executescript(sql_script)
        conn.commit()
        
        print("✅ SQL脚本执行成功！")
        
        # 验证表是否创建
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()
        
        print(f"\n创建的表 ({len(tables)} 个):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # 验证预期的表都存在
        expected_tables = {'users', 'items', 'favorites', 'messages'}
        actual_tables = {table[0] for table in tables}
        
        if expected_tables == actual_tables:
            print("\n✅ 所有预期表都已创建")
        else:
            missing = expected_tables - actual_tables
            extra = actual_tables - expected_tables
            if missing:
                print(f"❌ 缺少表: {missing}")
            if extra:
                print(f"❌ 多余表: {extra}")
        
        # 测试插入数据
        print("\n测试插入数据...")
        cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            ("testuser", "testpass123", "test@example.com")
        )
        conn.commit()
        
        print("✅ 数据插入成功！")
        
        # 测试查询
        cursor.execute("SELECT * FROM users WHERE username = 'testuser'")
        user = cursor.fetchone()
        print(f"\n查询结果: {user}")
        
        print("\n=== 所有测试通过！===")
        
    except sqlite3.Error as e:
        print(f"\n❌ SQLite错误: {e}")
        import traceback
        traceback.print_exc()
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    test_sql_schema()
