import sqlite3
import os

# 测试数据库初始化
def test_db_init():
    # 测试SQL语句是否有效
    sql_script = '''
-- 清除现有表（如果存在）
DROP TABLE TABLE IF EXISTS messages;
DROP TABLE TABLE IF EXISTS favorites;
DROP TABLE TABLE IF EXISTS items;
DROP TABLE TABLE IF EXISTS users;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT CURRENT CURRENT_TIMESTAMP
);

-- 商品表
CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    seller_id INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL DEFAULT 0.0,
    tags TEXT,
    image_path TEXT,
    status TEXT NOT NULL DEFAULT 'available', -- available, sold, reserved
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (seller_id) REFERENCES users (id)
);

-- 收藏表
CREATE TABLE IF NOT EXISTS favorites (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id),
    FOREIGN KEY (item_id) REFERENCES items (id),
    UNIQUE(user_id, item_id)
);

-- 消息表
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    from_user_id INTEGER NOT NULL,
    to_user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (from_user_id) REFERENCES users (id),
    FOREIGN KEY (to_user_id) REFERENCES users (id),
    FOREIGN KEY (item_id) REFERENCES items (id)
);
'''
    
    try:
        # 创建临时数据库文件进行测试
        conn = sqlite3.connect(':memory:')
        cursor = conn.cursor()
        
        # 执行SQL脚本
        cursor.executescript(sql_script)
        conn.commit()
        
        print("✅ SQL脚本执行成功！")
        
        # 检查表是否创建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print("\n创建的表：")
        for table in tables:
            print(f"- {table[0]}")
        
        # 测试插入数据
        print("\n测试插入数据...")
        cursor.execute(
            "INSERT INTO users (username, password, email) VALUES (?, ?, ?)",
            ("testuser", "testhash", "test@example.com")
        )
        conn.commit()
        
        print("✅ 数据插入成功！")
        
        # 测试查询
        cursor.execute("SELECT * FROM users")
        user = cursor.fetchone()
        print(f"\n查询结果：{user}")
        
        conn.close()
        print("\n✅ 数据库初始化测试通过！")
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== 测试数据库初始化 ===")
    test_db_init()
