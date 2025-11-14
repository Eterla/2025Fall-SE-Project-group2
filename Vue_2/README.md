# 校内二手物品交易平台

这是一个基于Flask和Vue的校内二手物品交易平台，实现了前后端分离的架构。

## 项目结构

```
project/
├── backend/                  # Flask后端
│   ├── app/                  # 核心逻辑
│   │   ├── __init__.py       # 应用初始化
│   │   ├── models.py         # 数据模型
│   │   ├── auth.py           # 认证相关
│   │   ├── main.py           # 主要业务逻辑
│   │   └── schema.sql        # 数据库表结构
│   ├── run.py                # 后端启动文件
│   ├── requirements.txt      # 后端依赖
│   └── test_api.py           # API测试脚本
├── frontend/                 # Vue前端
│   ├── public/               # 静态文件
│   ├── src/
│   │   ├── assets/           # 前端资源
│   │   ├── components/       # 组件
│   │   ├── views/            # 页面
│   │   ├── router/           # 路由
│   │   ├── axios/            # 请求封装
│   │   ├── App.vue           # 根组件
│   │   └── main.js           # 入口文件
│   ├── package.json          # 前端依赖
│   └── vue.config.js         # Vue配置
├── api.md                    # API文档
└── README.md                 # 项目说明
```

## 功能特点

### 后端功能
- 用户认证（注册、登录、JWT认证）
- 商品管理（发布、查看、搜索、状态更新）
- 收藏功能
- 消息聊天系统

### 前端功能
- 响应式界面设计
- 用户认证（登录、注册）
- 商品浏览与搜索
- 商品发布与管理
- 个人中心
- 收藏管理
- 消息聊天

## 技术栈

### 后端
- Flask：Python Web框架
- Flask-CORS：解决跨域问题
- PyJWT：JWT认证
- SQLite：轻量级数据库

### 前端
- Vue 3：前端框架
- Vue Router：路由管理
- Axios：HTTP请求
- Bootstrap：UI框架

## 如何运行

### 后端

1. 进入backend目录：
```bash
cd project/backend
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

3. 启动后端服务器：
```bash
python run.py
```
服务器将在 http://localhost:5001 运行。

### 前端

1. 进入frontend目录：
```bash
cd project/frontend
```

2. 安装依赖：
```bash
npm install
```

3. 启动前端开发服务器：
```bash
npm run serve
```
服务器将在 http://localhost:8080 运行。

## API文档

API文档位于 `api.md` 文件中，包含了所有API接口的详细说明。

## 注意事项

1. 确保后端服务器先启动，然后再启动前端服务器。
2. 前端通过代理访问后端API，配置在 `vue.config.js` 中。
3. 数据库文件位于 `backend/instance/market.db`。
4. 图片上传路径为 `backend/static/images/`。

## 未来计划

1. 添加商品分类功能
2. 实现更完善的搜索功能
3. 添加支付功能
4. 优化用户界面
5. 添加移动端适配
