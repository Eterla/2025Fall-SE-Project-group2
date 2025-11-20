import { io } from 'socket.io-client'
import { useChatStore } from '@/stores/chat'

class SocketService {
    constructor() {
        this.socket = null
        this.connected = false
        this._pendingOn = [] // 在 connect 之前注册的事件，会在连接后绑定
    }

  // 连接到服务器
    connect(token) {
        if (this.socket && this.connected) {
            console.log('SocketService: already connected')
            return this.socket
        }

        this.socket = io('http://127.0.0.1:5001', {
            auth: { 
                token: token 
            },
                transports: ['websocket', 'polling'],
                autoConnect: true,
        })
        
        
        this.socket.on('connect', () => {
            console.log('SocketService: connect id=', this.socket.id)
            this.connected = true

            // 绑定核心事件到 store（这里直接在 handler 中拿 store）
            const chatStore = useChatStore()
            // new_message -> 写入 store
            this.socket.on('new_message', (payload) => {
                console.log('socket new_message', payload)
                try {
                    chatStore.addMessage(payload)
                } catch (e) {
                    console.error('chatStore.addMessage error', e)
                }
            })

            // user_typing -> 更新 typing 状态
            this.socket.on('user_typing', (payload) => {
                // payload: { user_id, item_id, is_typing } （后端目前约定如此）
                const convId = payload.conversation_id || `${Math.min(payload.user_id, payload.other_user_id)}_${Math.max(payload.user_id, payload.other_user_id)}`
                chatStore.setTyping(convId, payload.user_id, !!payload.is_typing)
            })

            // 绑定此前 pending 注册的事件
            for (const [evt, cb] of this._pendingOn) {
                this.socket.on(evt, cb)
            }
            this._pendingOn = []
        })

        // 连接错误
        this.socket.on('connect_error', (err) => {
            console.error('SocketService: connect_error', err)
            this.connected = false
        })

        // 断开连接
        this.socket.on('disconnect', (reason) => {
            console.log('SocketService: disconnect', reason)
            this.connected = false
        })

        return this.socket
    }

    // 断开连接
    disconnect() {
        if (this.socket) {
            try {
                this.socket.disconnect()
            } catch (e) {
                console.error('SocketService.disconnect error:', e)
            }
            this.socket = null
            this.connected = false
            this._pendingOn = []
        }
    }

    // 通用 emit 方法（安全检查）
    emit(event, data, ack) {
        if (!this.socket) {
            console.warn('SocketService.emit: socket not connected yet')
            return
        }
        this.socket.emit(event, data, ack)
    }

    // 通用 on 方法（若尚未连接，先缓存）
    on(event, callback) {
        if (this.socket && this.connected) {
            this.socket.on(event, callback)
        } else {
            this._pendingOn.push([event, callback])
        }
    }

    off(event, callback) {
        if (this.socket) {
            this.socket.off(event, callback)
        } else {
            // 从 pending 中移除
            this._pendingOn = this._pendingOn.filter(([e, cb]) => !(e === event && cb === callback))
        }
    }

    // 新消息监听
    onNewMessage(callback) { 
        console.log("Registering onNewMessage callback", callback);
        this.on('new_message', callback) 
    }
    // 取消新消息监听
    offNewMessage(callback) { 
        this.off('new_message', callback) 
    }

    // 发送正在输入状态
    sendTyping(payload) { 
        this.emit('typing', payload) 
    }

    // 监听用户正在输入状态
    onUserTyping(callback) { 
        this.on('user_typing', callback) 
    }

    // 取消监听用户正在输入状态
    offUserTyping(callback) { 
        this.off('user_typing', callback) 
    }

    // 加入会话房间
    joinConversation(conversationId) {
        this.emit('join_conversation', { conversation_id: conversationId })
    }

    // 离开会话房间
    leaveConversation(conversationId) {
        this.emit('leave_conversation', { conversation_id: conversationId })
    }
}

// 导出单例
export default new SocketService()