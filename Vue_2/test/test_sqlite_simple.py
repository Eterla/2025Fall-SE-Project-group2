import sqlite3
import os

def test_sqlite_simple():
    """简单SQLite数据库模式的简单测试"""
    
    # 创建临时内存数据库进行测试
    conn = sqlite3.connect(':memory:')
    cursor = conn.cursor()
    
    # 读取schema.sql文件内容
    schema_path = os.path.join(os.path.dirname(__file__), '../backend/app/schema.sql')
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            sql_script = f.read()
        
        print("正在测试SQLite数据库模式...")
        
        # 执行SQL脚本
        try:
            cursor.executescript(sql_script)
            conn.commit()
            print("✅ SQL脚本执行成功！")
        except sqlite3.Error as e:
            print(f"❌ SQL执行失败：{e}")
            import traceback
            traceback.print_exc()
            return
        
        # 检查表是否创建成功
        cursor.execute("SELECT name from sqlite_master where type='table' order by name;")
        tables = cursor.fetchall()
        
        print(f"\n成功创建了 {len(tables)} 个表：")
        for table in tables:
            print(f"- {table[0]}")
        
        # 验证是否表都被创建了
        expected_tables = {'users', 'items', 'favorites', 'messages'}
        created_tables = {table[0] for table in tables}
        
        missing_tables = expected_tables - created_tables
        if missing_tables:
            print(f"\n❌ 缺少表：{missing_tables}")
        else:
            print("\n✅ 所有预期表都已创建")
        
        print("\n✅ 数据库模式测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试过程中出错：{e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()

if __name__ == "__main__":
    print("=== SQLite数据库模式测试 ===")
    test_sqlite_simple()
