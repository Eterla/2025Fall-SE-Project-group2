// src/stores/chat.js
import { defineStore } from 'pinia'

export const useChatStore = defineStore('chat', {
  state: () => ({
    sessions: [],      // 会话列表
    messages: {},      // 每个会话的消息列表
    activeSessionId: null, // 当前打开的会话
    typing: {}         // 正在输入状态
  }),
  // sessions的格式：
  // [
  //  { id, 
  //    other_user_id, 
  //    other_username, 
  //    item_id, 
  //    lastMessage, 
  //    unreadCount }
  // ]

  // messages 的格式：messages: { [conversationId]: Message[] }
  // Message 的格式：
  // {
  //   id,
  //   conversation_id,
  //   from_user_id,
  //   to_user_id,
  //   item_id,
  //   content,
  //   created_at,
  //   sender_name,
  //   is_read
  // }

  // typing: { [item_id]: {[userId]: boolean} } 

  actions: {
    // 打开会话（打开聊天窗口）
    setActiveSession(conversationId) {
      console.log("setActiveSession:", conversationId)
      this.activeSessionId = conversationId
      // this.markSessionRead(conversationId)
    },

    // 清空 store（登出时调用）
    clearAll() {
      this.sessions = []
      this.messages = {}
      this.activeSessionId = null
      this.typing = {}
    },

    // 插入或更新一个会话条目（供列表页面或首次收到消息时使用）
    upsertSession(session) {
      const s = this.sessions.find(x => x.id === session.id)
      console.log("upsertSession:", session, "found existing:", s) // s 不存在时表示新会话
      if (s) {
        Object.assign(s, session) // 更新已有字段
      } else {
        console.log("upsertSession: adding new session", session)
        this.sessions.unshift(Object.assign({}, session)) // 新会话插入到最前面
      }
    },

    // 添加消息（SocketService 或页面发送/获取历史时调用）
    addMessage(raw) {
      const conversationId = raw.conversation_id
      if (!conversationId) return

      const msg = {
        id: raw.id,
        conversation_id: conversationId,
        from_user_id: raw.from_user_id,
        to_user_id: raw.to_user_id,
        item_id: raw.item_id,
        content: raw.content,
        created_at: raw.created_at,
        sender_name: raw.from_username ?? '',
        is_read: raw.is_read ||  (this.activeSessionId === conversationId) 
      }

      // 确保 messages 数组存在
      if (!this.messages[conversationId]) {
        this.messages[conversationId] = []
      }

      // 去重：如果已有相同 id 则替换
      const existIdx = this.messages[conversationId].findIndex(m => String(m.id) === String(msg.id))
      if (existIdx !== -1) {
        this.messages[conversationId].splice(existIdx, 1, msg)
      } else {
        this.messages[conversationId].push(msg)
      }

      // 更新或创建 session 的 lastMessage & unreadCount
      let session = this.sessions.find(s => s.id === conversationId)
      if (session) {
        session.lastMessage = msg.content
        // 如果当前不是正在聊天的会话 → 未读+1（且消息是发给我的并未被标记为已读）
        if (this.activeSessionId !== conversationId && msg.to_user_id == this.getCurrentUserId() && !msg.is_read) {
          session.unreadCount = (session.unreadCount || 0) + 1
        }
      } else {
        // 新会话入口，unshift 到列表
        this.sessions.unshift({
          id: conversationId,
          other_user_id: msg.from_user_id === Number(this.getCurrentUserId()) ? msg.to_user_id : msg.from_user_id,
          other_username: msg.sender_name,
          item_id: msg.item_id,
          lastMessage: msg.content,
          unreadCount: (this.activeSessionId === conversationId || msg.is_read) ? 0 : 1
        })
      }
    },

    // 将会话标记已读（未读置零），并把 messages 标记为 is_read=true
    markSessionRead(conversationId) {
      const s = this.sessions.find(s => s.id === conversationId)
      if (s) {
        console.log("markSessionRead for conversationId:", conversationId)
        s.unreadCount = 0
      } else {
        this.upsertSession({ id: conversationId, unreadCount: 0 })
      }

      const msgs = this.messages[conversationId]
      if (Array.isArray(msgs)) {
        for (const m of msgs) {
          // 只把发给当前用户的消息标为已读
          if (m.to_user_id == this.getCurrentUserId()) {
            m.is_read = true
          }
        }
      }
    },

    // helper: 当前登录用户 id（从 localStorage 或其它存储取）
    getCurrentUserId() {
      try {
        const u = JSON.parse(localStorage.getItem('user_info') || '{}')
        return u.id
      } catch {
        return null
      }
    },

    // 设置 typing 状态
    setTyping(userId, itemId, isTyping) {
      console.log("设置 typing 状态:", userId, itemId, isTyping)
      if (!this.typing[itemId]) {
        this.typing[itemId] = {}
      }
      this.typing[itemId][userId] = isTyping
    }
  },

  getters: {
    // 获取某个会话的消息（如果没有返回空数组）
    getMessages: (state) => {
      return (conversationId) => state.messages[conversationId] || []
    },
    // 会话总未读数
    totalUnread: (state) => {
      return state.sessions.reduce((sum, s) => sum + (s.unreadCount || 0), 0)
    }
  }
})