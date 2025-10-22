# 博雅市集 - 二手交易平台

一个基于Flask开发的在线二手商品交易平台，支持用户注册、商品发布、收藏、私信聊天等功能。

## 📋 项目概述

博雅市集是一个面向校园的二手交易平台，用户可以：
- 注册账户并登录
- 发布二手商品（支持图片上传）
- 浏览和搜索商品
- 收藏感兴趣的商品
- 与卖家私信沟通
- 管理个人发布的商品

## 🏗️ 项目结构

```
project/
├── run.py              # 应用启动文件
├── requirements.txt    # Python依赖包
├── README.md          # 项目说明文档
├── instance/          # 实例文件（运行时生成）
│   └── db.sqlite3     # SQLite数据库文件
├── app/               # 应用核心代码
│   ├── __init__.py    # Flask应用工厂，注册蓝图并初始化Database
│   ├── db.py          # Database类（连接、初始化、Schema）
│   ├── models.py      # 数据模型（User, Item, Favorite, Chat）
│   ├── auth.py        # 用户认证蓝图（注册/登录/登出）
│   ├── main.py        # 主要功能蓝图（首页、发布、商品详情、收藏）
│   └── messages.py    # 消息功能蓝图（聊天列表、发送消息、聊天详情）
├── templates/         # HTML模板文件
│   ├── base.html      # 基础模板
│   ├── index.html     # 首页
│   ├── login.html     # 登录页面
│   ├── register.html  # 注册页面
│   ├── publish.html   # 发布商品页面
│   ├── item_detail.html # 商品详情页面
│   ├── user_center.html # 用户中心
│   ├── favorites.html   # 收藏列表
│   ├── messages.html    # 消息列表
│   └── chat_detail.html # 聊天详情页面
└── static/            # 静态资源
    └── images/        # 上传的商品图片（运行时写入）
```

## 🚀 快速开始

### 环境要求
- Python 3.8+
- SQLite3（通常已预装）

### 1. 进入项目目录
```bash
cd 博雅市集/project
```

### 2. 激活虚拟环境
```bash
source .venv/bin/activate  # macOS/Linux
# 或者 Windows: .venv\Scripts\activate
```

### 3. 安装依赖（如果需要）
```bash
pip install flask
```

### 4. 运行应用
```bash
python3 run.py
```

### 5. 访问应用
打开浏览器访问：http://localhost:5000

## 🗄️ 数据库设计

项目使用SQLite数据库，包含以下表：

### users 表（用户信息）
- `id`: 用户ID（主键）
- `username`: 用户名（唯一）
- `password`: 密码（SHA256加密）
- `email`: 邮箱
- `phone`: 手机号
- `created_at`: 注册时间

### items 表（商品信息）
- `id`: 商品ID（主键）
- `seller_id`: 卖家ID（外键）
- `title`: 商品标题
- `description`: 商品描述
- `price`: 价格
- `tags`: 标签
- `image_path`: 图片路径
- `status`: 状态（available/removed）
- `created_at`: 发布时间

### favorites 表（收藏关系）
- `id`: 收藏ID（主键）
- `user_id`: 用户ID（外键）
- `item_id`: 商品ID（外键）
- `created_at`: 收藏时间

### chats 表（聊天消息）
- `id`: 消息ID（主键）
- `sender_id`: 发送者ID（外键）
- `receiver_id`: 接收者ID（外键）
- `item_id`: 关联商品ID（外键）
- `content`: 消息内容
- `created_at`: 发送时间

## 🔧 开发指南

### 蓝图（Blueprint）结构
- **auth_bp**: 用户认证相关功能
- **main_bp**: 主要业务功能（商品、收藏等）
- **messages_bp**: 消息和聊天功能

### 添加新功能
1. **路由**: 在相应的蓝图文件中添加路由
2. **模板**: 在 `templates/` 目录下创建HTML模板
3. **模型**: 在 `models.py` 中添加数据模型
4. **数据库**: 如需新表，在 `db.py` 中添加建表语句

### 常用开发命令
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate 

# 安装以来
pip install -r requirements.txt

# 运行应用（开发模式）
python run.py

# 查看数据库内容
sqlite3 instance/db.sqlite3
.tables  # 查看所有表
.schema users  # 查看用户表结构
SELECT * FROM users;  # 查看用户数据
```

## 📝 功能清单

- [x] 用户注册/登录/登出
- [x] 商品发布（支持图片上传）
- [x] 商品浏览和搜索
- [x] 商品详情页面
- [x] 收藏功能
- [x] 用户中心（管理个人商品）
- [x] 私信聊天功能
- [x] 商品下架功能
- [ ] 用户头像上传
- [ ] 商品分类
- [ ] 评价系统

---

**开发愉快! 🎉**