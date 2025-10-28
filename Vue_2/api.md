# 校内二手物品交易平台 API 文档

## 基础信息

- 基础URL: `/api`
- 所有响应格式: JSON
- 认证方式: JWT Bearer Token

## 响应格式

### 成功响应
```json
{
  "ok": true,
  "data": {
    // 响应数据
  }
}
```

### 错误响应
```json
{
  "ok": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "错误描述"
  }
}
```

## 认证相关 API

### 注册
- URL: `/auth/register`
- 方法: `POST`
- 请求体:
  ```json
  {
    "username": "string",
    "password": "string",
    "email": "string (可选)",
    "phone": "string (可选)"
  }
  ```
- 成功响应 (201 Created):
  ```json
  {
    "ok": true,
    "data": {
      "id": "integer",
      "username": "string",
      "email": "string",
      "created_at": "string"
    }
  }
  ```
- 错误响应:
  - 400 Bad Request: 请求参数错误
  - 409 Conflict: 用户名已存在

### 登录
- URL: `/auth/login`
- 方法: `POST`
- 请求体:
  ```json
  {
    "username": "string",
    "password": "string"
  }
  ```
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data": {
      "access_token": "string",
      "token_type": "bearer",
      "expires_in": 86400,
      "user": {
        "id": "integer",
        "username": "string"
      }
    }
  }
  ```
- 错误响应:
  - 400 Bad Request: 请求参数错误
  - 401 Unauthorized: 用户名或密码错误

### 登出
- URL: `/auth/logout`
- 方法: `POST`
- 认证: 需要
- 成功响应 (200 OK):
  ```json
  {
    "ok": true
  }
  ```

### 获取当前用户信息
- URL: `/auth/me`
- 方法: `GET`
- 认证: 需要
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data": {
      "id": "integer",
      "username": "string",
      "email": "string",
      "phone": "string",
      "created_at": "string"
    }
  }
  ```
- 错误响应:
  - 401 Unauthorized: 未认证
  - 404 Not Found: 用户不存在

## 商品相关 API

### 获取商品列表
- URL: `/items`
- 方法: `GET`
- 查询参数:
  - `search`: 搜索关键词 (可选)
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data": [
      {
        "id": "integer",
        "seller_id": "integer",
        "seller_name": "string",
        "title": "string",
        "description": "string",
        "price": "number",
        "tags": "string",
        "image_path": "string",
        "status": "string",
        "created_at": "string",
        "updated_at": "string"
      }
    ]
  }
  ```

### 获取商品详情
- URL: `/items/{item_id}`
- 方法: `GET`
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data": {
      "id": "integer",
      "seller_id": "integer",
      "seller_name": "string",
      "title": "string",
      "description": "string",
      "price": "number",
      "tags": "string",
      "image_path": "string",
      "status": "string",
      "created_at": "string",
      "updated_at": "string",
      "is_favorite": "boolean"
    }
  }
  ```
- 错误响应:
  - 404 Not Found: 商品不存在

### 发布商品
- URL: `/items`
- 方法: `POST`
- 认证: 需要
- 请求体 (multipart/form-data):
  - `title`: 商品标题
  - `description`: 商品描述
  - `price`: 价格
  - `tags`: 标签 (空格分隔)
  - `image`: 商品图片 (可选)
- 成功响应 (201 Created):
  ```json
  {
    "ok": true,
    "data": {
      "id": "integer",
      "seller_id": "integer",
      "title": "string"
    }
  }
  ```
- 错误响应:
  - 400 Bad Request: 请求参数错误
  - 401 Unauthorized: 未认证

### 获取用户发布的商品
- URL: `/user/items`
- 方法: `GET`
- 认证: 需要
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data": [
      {
        "id": "integer",
        "seller_id": "integer",
        "seller_name": "string",
        "title": "string",
        "description": "string",
        "price": "number",
        "tags": "string",
        "image_path": "string",
        "status": "string",
        "created_at": "string",
        "updated_at": "string"
      }
    ]
  }
  ```
- 错误响应:
  - 401 Unauthorized: 未认证

### 更新商品状态
- URL: `/items/{item_id}/status`
- 方法: `PUT`
- 认证: 需要
- 请求体:
  ```json
  {
    "status": "string" // available, sold, reserved
  }
  ```
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data": {
      "id": "integer",
      "status": "string"
    }
  }
  ```
- 错误响应:
  - 400 Bad Request: 请求参数错误
  - 401 Unauthorized: 未认证
  - 403 Forbidden: 无权操作
  - 404 Not Found: 商品不存在

## 收藏相关 API

### 添加收藏
- URL: `/favorites`
- 方法: `POST`
- 认证: 需要
- 请求体:
  ```json
  {
    "item_id": "integer"
  }
  ```
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data": {
      "is_favorite": "boolean",
      "item_id": "integer"
    }
  }
  ```
- 错误响应:
  - 400 Bad Request: 请求参数错误
  - 401 Unauthorized: 未认证
  - 404 Not Found: 商品不存在

### 取消收藏
- URL: `/favorites/{item_id}`
- 方法: `DELETE`
- 认证: 需要
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data": {
      "is_favorite": false,
      "item_id": "integer"
    }
  }
  ```
- 错误响应:
  - 401 Unauthorized: 未认证
  - 404 Not Found: 收藏不存在

### 获取收藏列表
- URL: `/favorites`
- 方法: `GET`
- 认证: 需要
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data": [
      {
        "id": "integer",
        "seller_id": "integer",
        "seller_name": "string",
        "title": "string",
        "description": "string",
        "price": "number",
        "tags": "string",
        "image_path": "string",
        "status": "string",
        "created_at": "string",
        "updated_at": "string"
      }
    ]
  }
  ```
- 错误响应:
  - 401 Unauthorized: 未认证

## 消息相关 API

### 发送消息
- URL: `/messages`
- 方法: `POST`
- 认证: 需要
- 请求体:
  ```json
  {
    "to_user_id": "integer",
    "item_id": "integer",
    "content": "string"
  }
  ```
- 成功响应 (201 Created):
  ```json
  {
    "ok": true,
    "data": {
      "id": "integer",
      "from_user_id": "integer",
      "to_user_id": "integer",
      "item_id": "integer",
      "content": "string",
      "created_at": "string"
    }
  }
  ```
- 错误响应:
  - 400 Bad Request: 请求参数错误
  - 401 Unauthorized: 未认证
  - 404 Not Found: 用户或商品不存在

### 获取消息列表
- URL: `/messages/conversations`
- 方法: `GET`
- 认证: 需要
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data": [
      {
        "other_user_id": "integer",
        "other_username": "string",
        "item_id": "integer",
        "item_title": "string",
        "item_image": "string",
        "last_message_time": "string",
        "unread_count": "integer"
      }
    ]
  }
  ```
- 错误响应:
  - 401 Unauthorized: 未认证

### 获取聊天记录
- URL: `/messages/conversations/{other_user_id}/{item_id}`
- 方法: `GET`
- 认证: 需要
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data": [
      {
        "id": "integer",
        "from_user_id": "integer",
        "to_user_id": "integer",
        "item_id": "integer",
        "content": "string",
        "is_read": "boolean",
        "created_at": "string",
        "from_username": "string",
        "to_username": "string"
      }
    ]
  }
  ```
- 错误响应:
  - 401 Unauthorized: 未认证
  - 404 Not Found: 商品不存在
