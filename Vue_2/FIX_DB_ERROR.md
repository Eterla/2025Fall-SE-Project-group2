# 修复数据库初始化错误

## 问题描述

在执行 `flask init-db` 命令时遇到以下错误：

```
sqlite3.OperationalError: near "DATABASE": syntax error
```

## 问题原因

原 `schema.sql` 文件使用了MySQL特有的语法，而我们的项目使用的是SQLite数据库。SQLite不支持以下MySQL命令：

- `DROP DATABASE IF EXISTS market;`
- `CREATE DATABASE IF NOT EXISTS market;`
- `USE market;`

## 解决方案

我已经修复了 `backend/app/schema.sql` 文件，使用SQLite兼容的语法：

```sql
-- 清除现有表（如果存在）
DROP TABLE IF EXISTS messages;
DROP TABLE IF EXISTS favorites;
DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS users;

-- 用户表
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
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
```

## 如何修复

1. **替换 `schema.sql` 文件**：
   将上面的SQL代码复制到你的 `backend/app/schema.sql` 文件中，覆盖原有内容。

2. **重新初始化数据库**：
   ```bash
   flask init-db
   ```

3. **验证修复**：
   可以运行测试脚本来验证数据库初始化是否正常工作：
   ```bash
   python test_sql_schema.py
   ```

## 额外建议

- 确保你的项目使用的是SQLite数据库（默认配置）
- 如果你需要使用MySQL，需要修改数据库连接配置
- 定期备份你的数据库文件

## 联系方式

如果问题仍然存在，请提供完整的错误日志以便进一步排查。
