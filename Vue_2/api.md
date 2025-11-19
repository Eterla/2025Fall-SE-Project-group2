# 校内二手物品交易平台 API 文档
> [!tip]
>
> 目前的api文档是根据已经实现的frontend和backend响应接口来描述，而后端实际上尚未实现的内容则特殊标注为BNC(Backend Not Completed)
>
> **前后端的同学都一定要看api文档!!! **
>
> 1. 前端同学在完成前端需求时如果需要修改已有的api，需要向相关的后端同学提出由后端同学进行修改!
> 2. 前端同学在完成前端需求时，如果是自己新添加的api，则尽量确保新增api的稳定性，避免频繁提出api更改需求，同时应当遵循下述规定的响应基本格式，保证api的统一性.
> 3. 后端同学应尽量及时处理前端同学对api的修改需求和新增需求; 
> 4. **关于api开发的Git合作:目前设想的逻辑有两种:**
>    - 前端同学完成自己的开发之前，如果已经有了对api的需求，可以先跟后端同步，后端即可并行开始; 后面各自pull request到`dev`分支上.
>    - 前端同学如果开发过程对api的需求不太确定，也可以先等自己把前端逻辑完全开发完了，再通知后端开始修改或新增.
> 5. 最后所有开发完成之后可以删除掉api文档中多余的注释，publish一个尽量简洁清爽的version
> 6. (前端同学可以忽略本条)后端同学还需要注意一个事情，目前的后端架构中，只有User, Item...等类，同时这些类并不是个体类，而都是用来封装这些大类中与数据库交互的方法，相当于跳过了更细粒度层的个体item, user这些类的实现, 这是否已经与OOA和OOD模型产生了矛盾?
> 7. **By the end **目前还有一个问题，img在项目中应该怎么管理?  之前后端的数据库中有一个str类型的img_path, 但是previous version中的实现都是把该项置为Null， 所以可能需要在组会的时候讨论清楚这一个内容以便后续开发

[TOC]

## 基础信息

- 基础URL: `/api`
- 所有响应格式: JSON
- 认证方式: JWT Bearer Token
- 同时规约好200, 201, 401, 404等状态码

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
  - 500: 服务器内部错误，如数据库bug等

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
  - 400 Bad Request: 请求参数错误(如没填密码等, 前端如果有提交验证的话，则一般不会出现该错误)
  - 401 Unauthorized: 用户名或密码错误

### 登出

> BCN: 严格来说, 后端有一个demo已经实现在了/auth/logout中，但是时间原因暂时没有检查前端中对logout的api是怎么要求的，同时由于对session机制的陌生, 所以整条环路不确定是否通畅，故而标记为BCN，等待后续同学check完成，为了便利后续检查，下面仍然给出后端demo版本对该api的实现 ----Author: weizhiyuan

- URL: `/auth/logout`
- 方法: `POST`
- 认证: 需要
- 成功响应 (200 OK):
  ```json
  {
    "ok": true
  }
  ```

- 暂无错误响应实现, 默认都返回ok

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
  
    > 便于一些不了解的同学理解: 关键词的写法为路径后添加?search=xxx的格式
  
- 成功响应 (200 OK):
  
  - > Notice: 现在的data json object的内容即为目前数据库中items表的所有列，即如果还需要添加这里的返回值的话，可能会涉及对sqlite数据库的items表的结构性改动，对于后端来说会有大量的work，所以除非万不得已, 尽量使用已有的内容----(:by weizhiyuan)
  
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
- URL: `/items/{item_id:int}`
- > 对{item_id:int}的说明: for example: /items/2 表示向后端提出查找item_id为2的物品, 另外同/items方法, 这里也已经给出了所有的items项...
  >
  > 此外data.is_favorite的含义和功能我暂时不是很明确，所以后端目前都是返回False, 前端如果有需求请联系(weizhiyuan)
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

### 获取用户自己发布的商品

> 返回user_id对应拥有的items, 所以response.data是一个list[item], 内部的单个item还是用json格式来保证一致性

- URL: `/items/my`
- 方法: `GET`
- 认证: 需要
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data":list[item:json] [
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

> **BCN! wait for implement**

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

> **BCN! 同样的，所有的favorite相关的api, 后端里其实有一些demo实现(可能是之前ai生成的) 然而由于时间和精力问题, 都没有被检查和测试, 所以有些api可能是work的，有些则可能是没必要的，这一部分如果需求确实存在的话，可能就是接下来前后端工作的一个主要方面了** -----(weizhiyuan)

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

### 检查收藏状态
- URL: `/favorites/check?item_id={integer}`
- Method: `GET`
- 认证: 需要
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data":{
      // TODO: the frontend students should finish it and sync info to backend
      
    }
  }
  ```

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

> 使用SocketIO实现实时通信，下面描述SocketIO的接口和HTTP的api

### SocketIO
==**Important!!! 因为添加了SocketIO, 因此其实有一套另外的"api"系统, 而api文档中其他的api其实都是REST api; 所以后面可能会把SocketIO有关的内容单独封装到一个新的api文档中?**==

- 为了实现实时消息, 添加了这一项, 不过其使用方法略微与其他api有区别，故而专门在此处标注出来;

- 前端重新运行一次`npm install`即可, 因为需要装一个socket.io-client的包依赖

- 主要的两个方法:

  - Socket.emit(): 主动向socket的对面推送内容，可以类比socket编程中send的作用
  - Socket.on(): route一个监听对象, 
#### 逻辑简述:

  - 前端在login的时候需要添加一个websocket的连接请求，表示登陆成功之后就利用得到的token向后端发起一个websocket的连接:(这条通道)

  - 一个供前端参考的从零开始的socketService类的封装(由ai生成), 同时便于理解emit和on的功能(其实前端也可以直接copy，经过测试，是完全跑通的)

    ```js
    import { io } from 'socket.io-client';
    
    class SocketService {
      constructor() {
        this.socket = null;
        this.connected = false;
      }
    
      // 连接到服务器
      connect(token) {
        if (this.socket && this.connected) {
          console.log('Already connected');
          return;
        }
    
        // 建立连接（携带JWT token）
        this.socket = io('http://127.0.0.1:5001', {
          auth: {
            token: token
          },
          transports: ['websocket', 'polling']
        });
    
        // 连接成功
        this.socket.on('connected', (data) => {
          console.log('SocketIO connected:', data);
          this.connected = true;
        });
    
        // 连接错误
        this.socket.on('connect_error', (error) => {
          console.error('SocketIO connection error:', error);
          this.connected = false;
        });
    
        // 断开连接
        this.socket.on('disconnect', (reason) => {
          console.log('SocketIO disconnected:', reason);
          this.connected = false;
        });
    
        return this.socket;
      }
    
      // 断开连接
      disconnect() {
        if (this.socket) {
          this.socket.disconnect();
          this.socket = null;
          this.connected = false;
        }
      }
    
      // 监听新消息
      onNewMessage(callback) {
        if (this.socket) {
          this.socket.on('new_message', callback);
        }
      }
    
      // 加入会话房间
      joinConversation(conversationId) {
        if (this.socket && this.connected) {
          this.socket.emit('join_conversation', { conversation_id: conversationId });
        }
      }
    
      // 离开会话房间
      leaveConversation(conversationId) {
        if (this.socket && this.connected) {
          this.socket.emit('leave_conversation', { conversation_id: conversationId });
        }
      }
    
      // 发送正在输入状态
      sendTyping(conversationId, userId, isTyping = true) {
        if (this.socket && this.connected) {
          this.socket.emit('typing', {
            conversation_id: conversationId,
            user_id: userId,
            is_typing: isTyping
          });
        }
      }
    
      // 监听对方正在输入
      onUserTyping(callback) {
        if (this.socket) {
          this.socket.on('user_typing', callback);
        }
      }
    }
    
    // 导出单例
    export default new SocketService();
    ```

    
  ```js
  // Notice: 这是封装后的版本，推荐也采用这样的封装方式，为整个前端维护一个全局的socketService类的对象，后续所有的Vue中只调用该对象中的服务，这样能够确保单例化socket;
  // 同时
  
  import socketService from xxx	//伪代码
  export default {
    methods: {
      async handleLogin() {
        // ... 登录逻辑 ... 
        // 登陆成功后应该会获得一个response，内含access_token, [可以参考api的login part]
        if (response.data.ok) {
          const token = response.data.access_token;
          localStorage.setItem('access_token', token);
          // 连接 WebSocket
          socketService.connect(token);
          this.$router.push('/');
        }
      }
    }
  }
  ```
  - 同样的logout的时候也要调用`socket.disconnect()`

#### 实际目前socketio的api

##### Typing: #####

- type: 后端监听

- Event: "typing"

- Data:
	```json
  {
  	'user_id':'integer',
	  'to_user_id':'integer',
		'item_id':'integer',
		'is_typing':'bool',
	}
	```
	
- 作用: 向后端推送"我正在输入中“的event



##### User_typing: #####

- type: 后端emit, 前端监听
- Event: "user_typing"
- Data:

    	 ```json
     {
       	'user_id': 'integer',		// 输入中的那一方的user_id
         'item_id': 'integer', 
         'is_typing': 'bool'
     }
      ```

- 作用: 向另一方的前端推送，"对方正在输入中"的event

##### new_message: #####

- Type: 后端emit, 前端监听
- Event: "new_message"
- Data:

   ```json
   {
      "id": "integer",
      "conversation_id":"integer",
      "from_user_id": "integer",
      "to_user_id": "integer",
      "item_id": "integer",
      "content": "string",
      "created_at": "string"
   }
   ```



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
      "conversation_id": "integer",
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

### 获取会话列表
- URL: `/messages/conversations`
- 方法: `GET`
- 认证: 需要
- 成功响应 (200 OK):
  ```json
  {
    "ok": true,
    "data": [
      {
        "conversation_id": "integer",
        "other_user_id": "integer",
        "other_username": "string",
        "item_id": "integer",
        "item_title": "string",
        "item_image": "string",
        "last_message_time": "string",    // 最新一条消息的时间
        "last_message_content": "string", // 最新一条消息的内容
        "unread_count": "integer"
      }
    ]
  }
  ```
- 错误响应:
  - 401 Unauthorized: 未认证
  - 500 Server's internal error: 服务器内部错误

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
        "conversation_id": "integer",
        "from_user_id": "integer",    //发送方id
        "to_user_id": "integer",      //接受方id
        "item_id": "integer",
        "content": "string",
        "is_read": "boolean",
        "created_at": "string",
        "from_username": "string",    //发送方name
        "to_username": "string"       //接收方name
      }
    ]
  }
  ```
- 错误响应:
  - 401 Unauthorized: 未认证
  - 404 Not Found: 商品不存在, 用户不存在
  - 500 服务器内部错误
