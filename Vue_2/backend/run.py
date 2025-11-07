# run.py
import os
import sqlite3  # 新增：导入sqlite3模块
from app import create_app
from utils import make_response_ok, error_response

app = create_app()

@app.route('/')
def home():
    return make_response_ok({"message": "Welcome to the Marketplace API"})


# 初始化数据库表
def init_db():
    # 确保 instance 目录存在
    os.makedirs(app.instance_path, exist_ok=True)
    
    # 连接数据库并创建 users 表
    conn = sqlite3.connect(os.path.join(app.instance_path, 'market.db'))
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT,
            phone TEXT,
            created_at DATETIME NOT NULL
        )
    """)
    conn.commit()
    conn.close()

# 启动时初始化数据库
with app.app_context():
    init_db()

if __name__ == '__main__':
    app.run(debug=True)