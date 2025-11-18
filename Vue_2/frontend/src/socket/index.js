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